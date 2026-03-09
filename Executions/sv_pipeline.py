#!/usr/bin/env python3
"""
SV Pipeline - Umbrella Orchestrator

Executes all 6 workflows in sequence for end-to-end company evaluation.
"""

import sys
import subprocess
from pathlib import Path

def run_workflow(script_name, arg, description):
    """Run a workflow script and return exit code."""
    print(f"\n{'='*60}")
    print(f"EXECUTING: {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(
        ['python', f'Executions/{script_name}', arg],
        capture_output=False
    )

    if result.returncode != 0:
        print(f"\n[FAIL] {description} failed with exit code {result.returncode}")
        return False

    print(f"\n[OK] {description} completed successfully")
    return True

def main(raw_url):
    """Execute complete SV pipeline."""
    print("\n" + "="*60)
    print("SV PIPELINE - END-TO-END EXECUTION")
    print("="*60)
    print(f"Input URL: {raw_url}\n")

    # Workflow 1: URL Intake
    if not run_workflow('url_intake.py', raw_url, "Workflow 1: URL Intake"):
        return 1

    # Extract prospect_id from output (simple approach: re-run to get it)
    result = subprocess.run(
        ['python', 'Executions/url_intake.py', raw_url],
        capture_output=True,
        text=True
    )
    prospect_id = None
    for line in result.stdout.split('\n'):
        if 'Prospect ID:' in line:
            prospect_id = line.split(':')[1].strip()
            break

    if not prospect_id:
        print("[FAIL] Could not extract prospect_id")
        return 1

    print(f"\n[INFO] Processing prospect: {prospect_id}")

    # Workflow 2: Source Capture
    if not run_workflow('source_capture.py', prospect_id, "Workflow 2: Source Capture"):
        return 1

    # Workflow 3: Data Enrichment
    if not run_workflow('data_enrichment.py', prospect_id, "Workflow 3: Data Enrichment"):
        return 1

    # Workflow 4: SV Evaluation
    if not run_workflow('sv_evaluation.py', prospect_id, "Workflow 4: SV Evaluation"):
        return 1

    # Workflow 4.5: Canadian Market Research (Optional - controlled by .env)
    import os
    if os.getenv('ENABLE_CANADIAN_RESEARCH', 'false').lower() == 'true':
        print("\n[INFO] Canadian Market Research enabled - running research workflow")
        if not run_workflow('canadian_market_research.py', prospect_id, "Workflow 4.5: Canadian Market Research"):
            return 1
    else:
        print("\n[INFO] Canadian Market Research disabled - skipping (can be run separately later)")

    # Workflow 5: Generate Profile Document (MUST run before Master List Update)
    if not run_workflow('generate_profile_doc.py', prospect_id, "Workflow 5: Generate Profile Document"):
        return 1

    # Workflow 6: Master List Update (includes Google Doc URL from Workflow 5)
    if not run_workflow('master_list_update.py', prospect_id, "Workflow 6: Master List Update"):
        return 1

    # Load Google Doc URL
    import json
    import os
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    doc_url = ''
    try:
        with open(tmp_dir / prospect_id / 'google_doc_metadata.json', 'r') as f:
            doc_metadata = json.load(f)
            doc_url = doc_metadata.get('doc_url', '')
    except:
        pass

    # Summary
    print("\n" + "="*60)
    print("SV PIPELINE COMPLETE - ALL WORKFLOWS SUCCEEDED")
    print("="*60)
    print(f"Prospect ID: {prospect_id}")
    print(f"Artifacts: .tmp/{prospect_id}/")
    print(f"Local Profile: .tmp/{prospect_id}/sv_profile.md")
    if doc_url:
        print(f"Google Doc: {doc_url}")
    print(f"Google Sheet: https://docs.google.com/spreadsheets/d/12J94HQSUY1qVA5QII1wFiABpP7Nd2L-mpvR1i5ABNAo/edit")
    print("="*60 + "\n")

    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sv_pipeline.py <url>")
        print("Example: python sv_pipeline.py https://figured.com")
        sys.exit(1)

    raw_url = sys.argv[1]
    exit_code = main(raw_url)
    sys.exit(exit_code)
