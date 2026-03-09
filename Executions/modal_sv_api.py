#!/usr/bin/env python3
"""
Modal SV Pipeline API
Serverless backend for SV pipeline with proper timeout handling and CORS
"""

import modal
import os
import json
import time
import traceback
from datetime import datetime
from typing import Optional

# Create Modal app
app = modal.App("sv-pipeline-api")

# Docker image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "openai",
        "requests",
        "beautifulsoup4",
        "gspread",
        "google-auth",
        "google-api-python-client",
        "python-dotenv",
        "firecrawl-py"
    )
)

# Modal resources
secrets = modal.Secret.from_name("sv-secrets")
volume = modal.Volume.from_name("sv-pipeline-tmp", create_if_missing=True)
jobs_dict = modal.Dict.from_name("sv-job-status", create_if_missing=True)

# Mount code directory
code_mount = modal.Mount.from_local_dir(
    ".",
    remote_path="/root/sv_workflow"
)

def verify_api_key(headers: dict):
    """Verify API key from Authorization header."""
    auth = headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.replace("Bearer ", "")
    return token == os.environ.get("SV_API_KEY")

def add_cors_headers(response_dict: dict, status: int = 200):
    """
    Add CORS headers to response.
    Note: In production, restrict Access-Control-Allow-Origin to your Vercel domain.
    """
    return {
        "body": response_dict,
        "status": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # TODO: Change to your Vercel domain
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        }
    }

# ============================================================================
# WEB ENDPOINTS - All return immediately (no long-running HTTP connections)
# ============================================================================

@app.function(image=image, secrets=[secrets])
@modal.web_endpoint(method="POST")
def submit_job(request_dict: dict):
    """
    Submit new analysis job.
    Returns IMMEDIATELY (< 1 second) to avoid Modal's 150s HTTP timeout.
    """
    try:
        # Verify API key
        if not verify_api_key(request_dict.get("headers", {})):
            return add_cors_headers({"error": "Unauthorized"}, 401)

        # Parse request
        body = request_dict.get("body", {})
        url = body.get("url")
        company_name = body.get("company_name", "")
        run_mode = body.get("run_mode", "standard")
        notes = body.get("notes", "")

        if not url:
            return add_cors_headers({"error": "URL is required"}, 400)

        # Generate job ID
        job_id = f"job_{int(time.time())}_{os.urandom(4).hex()}"

        # Store initial status in Modal Dict (fast, ephemeral)
        job_data = {
            "job_id": job_id,
            "status": "queued",
            "url": url,
            "company_name": company_name,
            "run_mode": run_mode,
            "notes": notes,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "progress_pct": 0
        }
        jobs_dict[job_id] = job_data

        # Also write to Google Sheets Jobs tab (permanent source of truth)
        try:
            import sys
            sys.path.insert(0, "/root/sv_workflow")
            from Executions.jobs_sheet_manager import write_job_to_sheet
            write_job_to_sheet(job_data)
        except Exception as e:
            print(f"Warning: Failed to write initial job to Sheets: {e}")
            # Don't fail submission if Sheets write fails

        # Spawn background worker (non-blocking, returns immediately)
        run_pipeline_worker.spawn(job_id, url, company_name, run_mode, notes)

        # Return immediately with job ID
        return add_cors_headers({
            "job_id": job_id,
            "status": "queued",
            "created_at": jobs_dict[job_id]["created_at"]
        })

    except Exception as e:
        print(f"Submit job error: {e}")
        traceback.print_exc()
        return add_cors_headers({"error": "Internal server error"}, 500)

@app.function(image=image, secrets=[secrets])
@modal.web_endpoint(method="GET")
def get_job_status(job_id: str):
    """
    Get job status for polling.
    Returns immediately - reads from Modal Dict (fast in-memory lookup).
    """
    try:
        if job_id not in jobs_dict:
            return add_cors_headers({"error": "Job not found"}, 404)

        # Fast read from Modal Dict
        job_data = dict(jobs_dict[job_id])

        return add_cors_headers(job_data)

    except Exception as e:
        print(f"Get job status error: {e}")
        return add_cors_headers({"error": "Internal server error"}, 500)

@app.function(image=image, secrets=[secrets])
@modal.web_endpoint(method="GET")
def get_job(job_id: str):
    """
    Get full job details including results.
    Returns immediately - reads from Modal Dict.
    """
    try:
        if job_id not in jobs_dict:
            return add_cors_headers({"error": "Job not found"}, 404)

        job_data = dict(jobs_dict[job_id])

        return add_cors_headers(job_data)

    except Exception as e:
        print(f"Get job error: {e}")
        return add_cors_headers({"error": "Internal server error"}, 500)

@app.function(image=image, secrets=[secrets])
@modal.web_endpoint(method="GET")
def list_jobs(limit: int = 50, offset: int = 0, status: str = None):
    """
    List all jobs with pagination.
    Returns immediately - reads from Google Sheets Jobs tab (permanent source of truth).

    Falls back to Modal Dict for very recent jobs not yet written to Sheets.
    """
    try:
        import sys
        sys.path.insert(0, "/root/sv_workflow")
        from Executions.jobs_sheet_manager import get_jobs_from_sheet

        # Primary source: Google Sheets (permanent history)
        all_jobs = get_jobs_from_sheet(limit=limit * 2, status_filter=status)

        # Fallback: Add any jobs from Modal Dict that aren't in Sheets yet
        sheet_job_ids = {job['job_id'] for job in all_jobs}

        for job_id in jobs_dict.keys():
            if job_id not in sheet_job_ids:
                job_data = dict(jobs_dict[job_id])
                job_data["job_id"] = job_id
                all_jobs.append(job_data)

        # Sort by created_at descending (most recent first)
        all_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Paginate
        paginated = all_jobs[offset:offset + limit]

        return add_cors_headers({
            "jobs": paginated,
            "total": len(all_jobs),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        print(f"List jobs error: {e}")
        traceback.print_exc()
        return add_cors_headers({"error": "Internal server error"}, 500)

@app.function()
@modal.web_endpoint(method="GET")
def health():
    """Health check endpoint."""
    return add_cors_headers({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

# ============================================================================
# BACKGROUND WORKER - Long-running, spawned asynchronously
# ============================================================================

@app.function(
    image=image,
    secrets=[secrets],
    volumes={"/tmp/sv": volume},
    mounts=[code_mount],
    timeout=900  # 15 minutes (well within Modal's function timeout)
)
def run_pipeline_worker(job_id: str, url: str, company_name: str,
                        run_mode: str, notes: str):
    """
    Background worker to run pipeline.
    Runs asynchronously - does NOT block HTTP requests.
    Updates job status in Modal Dict after each step.
    """
    import sys
    sys.path.insert(0, "/root/sv_workflow")

    from Executions.pipeline_runner import run_pipeline

    def update_progress(step_name, step_display, progress_pct):
        """Update job progress in Modal Dict."""
        job_data = dict(jobs_dict[job_id])
        job_data.update({
            "status": "running",
            "current_step": step_name,
            "current_step_name": step_display,
            "progress_pct": progress_pct,
            "last_updated": datetime.utcnow().isoformat()
        })
        jobs_dict[job_id] = job_data
        print(f"[{job_id}] {progress_pct}% - {step_display}")

    try:
        # Update to running
        update_progress("starting", "Initializing pipeline...", 5)

        # Run pipeline (this takes 2-10 minutes)
        result = run_pipeline(
            url=url,
            run_mode=run_mode,
            tmp_dir="/tmp/sv",
            progress_callback=update_progress
        )

        if result['success']:
            # Load final results from evaluation
            import json
            from pathlib import Path

            prospect_id = result['prospect_id']
            eval_file = Path(f"/tmp/sv/{prospect_id}/sv_evaluation_record.json")
            profile_file = Path(f"/tmp/sv/{prospect_id}/prospect_profile.json")

            with open(eval_file) as f:
                evaluation = json.load(f)

            with open(profile_file) as f:
                profile = json.load(f)

            # Update with completion data
            job_data = dict(jobs_dict[job_id])
            job_data.update({
                "status": "completed",
                "progress_pct": 100,
                "current_step": "completed",
                "current_step_name": "Analysis complete",
                "prospect_id": prospect_id,
                "company_name": profile.get("company_name", company_name),
                "completed_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "results": {
                    "overall_score": evaluation.get("overall_score"),
                    "suggested_action": evaluation.get("suggested_action"),
                    "confidence_level": evaluation.get("confidence_level"),
                    "scores": evaluation.get("scores"),
                    "google_doc_url": result['results']['steps']['generate_profile_doc'].get('doc_url'),
                    "sheets_url": f"https://docs.google.com/spreadsheets/d/{os.environ['MASTER_PROSPECT_LIST_SHEET_ID']}/edit"
                }
            })
            jobs_dict[job_id] = job_data

            print(f"[{job_id}] ✓ Completed successfully")

            # Write to Google Sheets Jobs tab for permanent history
            try:
                from Executions.jobs_sheet_manager import write_job_to_sheet
                write_job_to_sheet(job_data)
                print(f"[{job_id}] ✓ Written to Jobs sheet")
            except Exception as e:
                print(f"[{job_id}] ⚠ Failed to write to Jobs sheet: {e}")
                # Don't fail the entire job if Sheets write fails

        else:
            # Mark as failed
            job_data = dict(jobs_dict[job_id])
            job_data.update({
                "status": "failed",
                "error": result.get("error", "Unknown error"),
                "failed_step": result.get("step"),
                "last_updated": datetime.utcnow().isoformat()
            })
            jobs_dict[job_id] = job_data

            print(f"[{job_id}] ✗ Failed at step: {result.get('step')}")
            print(f"[{job_id}] Error: {result.get('error')}")

    except Exception as e:
        # Handle unexpected errors
        job_data = dict(jobs_dict[job_id])
        job_data.update({
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "last_updated": datetime.utcnow().isoformat()
        })
        jobs_dict[job_id] = job_data

        print(f"[{job_id}] ✗ Unexpected error:")
        traceback.print_exc()

# ============================================================================
# CORS Pre-flight handler (for browser OPTIONS requests)
# ============================================================================

@app.function()
@modal.web_endpoint(method="OPTIONS")
def handle_cors_preflight():
    """Handle CORS preflight OPTIONS requests."""
    return {
        "status": 204,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # TODO: Change to your Vercel domain
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Max-Age": "86400",  # 24 hours
        }
    }
