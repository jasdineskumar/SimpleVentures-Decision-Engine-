#!/usr/bin/env python3
"""
SV Pipeline - Modal Cloud Function
===================================
Runs the full SV evaluation pipeline on Modal's serverless infrastructure.

Deploy:
    modal deploy Executions/modal_sv_api.py

Run (single company):
    modal run Executions/modal_sv_api.py --url https://example.com

Run (with Canadian market research):
    modal run Executions/modal_sv_api.py --url https://example.com --run-mode deep_canada

Call programmatically from another Modal function:
    from Executions.modal_sv_api import run_pipeline
    result = run_pipeline.remote(url="https://example.com")

Required Modal secret (create with: modal secret create sv-secrets ...):
    ANTHROPIC_API_KEY
    OPENAI_API_KEY          (optional, for Canadian research)
    FIRECRAWL_API_KEY       (optional, improves scraping)
    GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT  (entire JSON as string)
    MASTER_PROSPECT_LIST_SHEET_ID
"""

import modal
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Modal app + image
# ---------------------------------------------------------------------------

app = modal.App("sv-pipeline")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "anthropic",
        "openai",
        "requests",
        "beautifulsoup4",
        "lxml",
        "gspread",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "python-dotenv",
        "firecrawl-py",
        "pydantic",
        "jinja2",
        "markdown2",
        "colorlog",
        "python-dateutil",
    )
)

secrets = modal.Secret.from_name("sv-secrets")
volume  = modal.Volume.from_name("sv-pipeline-tmp", create_if_missing=True)

# Mount the entire local workspace into the container
code_mount = modal.Mount.from_local_dir(".", remote_path="/root/sv_workflow")

# ---------------------------------------------------------------------------
# Core cloud function
# ---------------------------------------------------------------------------

@app.function(
    image=image,
    secrets=[secrets],
    volumes={"/tmp/sv": volume},
    mounts=[code_mount],
    timeout=900,  # 15 minutes - well above the typical 2-10 min pipeline run
)
def run_pipeline(url: str, run_mode: str = "standard") -> dict:
    """
    Evaluate a single company through the full SV pipeline on Modal.

    Args:
        url:      Company website URL to evaluate.
        run_mode: "standard" (default) or "deep_canada" (adds Canadian market research).

    Returns:
        dict with keys:
            success          bool
            prospect_id      str
            company_name     str
            overall_score    float  (0-5)
            suggested_action str    (PASS / WATCH / INVESTIGATE / PRIORITIZE)
            confidence_level str    (HIGH / MEDIUM / LOW)
            google_doc_url   str
            url              str
            error            str    (only on failure)
            failed_step      str    (only on failure)
    """
    sys.path.insert(0, "/root/sv_workflow")
    from Executions.pipeline_runner import run_pipeline as _run_pipeline

    print(f"\n{'='*60}")
    print(f"SV Pipeline  |  Modal Cloud Run")
    print(f"URL:     {url}")
    print(f"Mode:    {run_mode}")
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print(f"{'='*60}\n")

    def log_progress(_step_name: str, step_display: str, progress_pct: int):
        print(f"[{progress_pct:3d}%] {step_display}")

    result = _run_pipeline(
        url=url,
        run_mode=run_mode,
        tmp_dir="/tmp/sv",
        progress_callback=log_progress,
    )

    if result["success"]:
        prospect_id = result["prospect_id"]

        eval_path    = Path(f"/tmp/sv/{prospect_id}/sv_evaluation_record.json")
        profile_path = Path(f"/tmp/sv/{prospect_id}/prospect_profile.json")

        evaluation = json.loads(eval_path.read_text())    if eval_path.exists()    else {}
        profile    = json.loads(profile_path.read_text()) if profile_path.exists() else {}

        doc_url = (
            result.get("results", {})
                  .get("steps", {})
                  .get("generate_profile_doc", {})
                  .get("doc_url", "")
        )

        summary = {
            "success":          True,
            "prospect_id":      prospect_id,
            "company_name":     profile.get("company_name", ""),
            "url":              url,
            "overall_score":    evaluation.get("overall_score"),
            "suggested_action": evaluation.get("suggested_action"),
            "confidence_level": evaluation.get("confidence_level"),
            "google_doc_url":   doc_url,
        }

        print(f"\n{'='*60}")
        print(f"RESULT: {summary['suggested_action']}  ({summary['overall_score']}/5)")
        print(f"Company: {summary['company_name']}")
        if doc_url:
            print(f"Doc:     {doc_url}")
        print(f"{'='*60}\n")

        return summary

    else:
        print(f"\n✗ Pipeline failed at step: {result.get('step')}")
        print(f"  Error: {result.get('error')}")
        traceback.print_exc()
        return {
            "success":     False,
            "url":         url,
            "error":       result.get("error"),
            "failed_step": result.get("step"),
        }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main(url: str, run_mode: str = "standard"):
    """
    Run the SV pipeline from the command line via Modal.

    Usage:
        modal run Executions/modal_sv_api.py --url https://example.com
        modal run Executions/modal_sv_api.py --url https://example.com --run-mode deep_canada
    """
    result = run_pipeline.remote(url=url, run_mode=run_mode)
    print("\n--- Final Result ---")
    print(json.dumps(result, indent=2))
