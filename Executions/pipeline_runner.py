#!/usr/bin/env python3
"""
Pipeline Runner - Unified Orchestrator for SV Pipeline
Executes all steps programmatically with error handling and progress tracking.

Design of Experiments (DOE) Framework:
- Error isolation: Each step returns structured results
- Graceful degradation: Failures don't crash entire pipeline
- Progress tracking: Callback system for real-time updates
- Idempotency: Safe to retry failed steps
- Resource efficiency: Parameterized tmp_dir for cloud/local
"""

import os
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any

# Import all pipeline steps
# These will be imported dynamically to handle import errors gracefully
STEP_MODULES = {
    'url_intake': 'Executions.url_intake',
    'source_capture': 'Executions.source_capture',
    'data_enrichment': 'Executions.data_enrichment',
    'sv_evaluation': 'Executions.sv_evaluation',
    'canadian_market_research': 'Executions.canadian_market_research',
    'generate_profile_doc': 'Executions.generate_profile_doc',
    'master_list_update': 'Executions.master_list_update',
}

# Step definitions with progress weights
PIPELINE_STEPS = [
    {'key': 'url_intake', 'display': 'Processing URL', 'progress_start': 5, 'progress_end': 15},
    {'key': 'source_capture', 'display': 'Scraping website', 'progress_start': 15, 'progress_end': 35},
    {'key': 'data_enrichment', 'display': 'Extracting company profile', 'progress_start': 35, 'progress_end': 55},
    {'key': 'sv_evaluation', 'display': 'Scoring company', 'progress_start': 55, 'progress_end': 75},
    {'key': 'canadian_market_research', 'display': 'Researching Canadian market', 'progress_start': 75, 'progress_end': 85},
    {'key': 'generate_profile_doc', 'display': 'Creating Google Doc', 'progress_start': 85, 'progress_end': 95},
    {'key': 'master_list_update', 'display': 'Updating spreadsheet', 'progress_start': 95, 'progress_end': 100},
]


def get_tmp_dir(tmp_dir: Optional[str] = None) -> str:
    """
    Get temp directory with environment detection.

    Priority:
    1. Explicit parameter
    2. MODAL_ENV → /tmp/sv (Modal Volume)
    3. TMP_DIR env var
    4. Default ./.tmp
    """
    if tmp_dir:
        return tmp_dir

    if os.getenv('MODAL_ENV'):
        return '/tmp/sv'

    return os.getenv('TMP_DIR', './.tmp')


def import_step_module(step_key: str):
    """
    Dynamically import a step module with error handling.

    Returns: module or None if import fails
    """
    try:
        import importlib
        module_name = STEP_MODULES.get(step_key)
        if not module_name:
            return None

        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        print(f"[ERROR] Failed to import {step_key}: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error importing {step_key}: {e}")
        return None


def run_url_intake(url: str, tmp_dir: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Step 1: URL Intake & Canonicalization

    Returns:
        {'success': bool, 'prospect_id': str, 'canonical_url': str, 'error': str}
    """
    try:
        # Import module
        module = import_step_module('url_intake')
        if not module:
            return {'success': False, 'error': 'Failed to import url_intake module'}

        # Override TMP_DIR temporarily
        original_tmp = os.environ.get('TMP_DIR')
        os.environ['TMP_DIR'] = tmp_dir

        try:
            # Call main function
            exit_code = module.main(url)

            if exit_code != 0:
                return {'success': False, 'error': 'URL intake returned non-zero exit code'}

            # Extract prospect_id from saved file
            canonical_files = list(Path(tmp_dir).glob('*/canonical_url.json'))
            if not canonical_files:
                return {'success': False, 'error': 'No canonical_url.json file found'}

            with open(canonical_files[-1], 'r') as f:
                data = json.load(f)

            return {
                'success': True,
                'prospect_id': data['prospect_id'],
                'canonical_url': data['canonical_url'],
                'source_type': data['source_type'],
            }

        finally:
            # Restore original TMP_DIR
            if original_tmp:
                os.environ['TMP_DIR'] = original_tmp
            elif 'TMP_DIR' in os.environ:
                del os.environ['TMP_DIR']

    except Exception as e:
        return {
            'success': False,
            'error': f'URL intake exception: {str(e)}',
            'traceback': traceback.format_exc()
        }


def run_pipeline_step(step_key: str, prospect_id: str, tmp_dir: str) -> Dict[str, Any]:
    """
    Run a generic pipeline step (source_capture through master_list_update).

    Args:
        step_key: Step identifier (e.g., 'source_capture')
        prospect_id: Prospect ID from url_intake
        tmp_dir: Temporary directory path

    Returns:
        {'success': bool, 'data': dict, 'error': str}
    """
    try:
        # Import module
        module = import_step_module(step_key)
        if not module:
            return {'success': False, 'error': f'Failed to import {step_key} module'}

        # Override TMP_DIR temporarily
        original_tmp = os.environ.get('TMP_DIR')
        os.environ['TMP_DIR'] = tmp_dir

        try:
            # Call main function
            exit_code = module.main(prospect_id)

            if exit_code != 0:
                return {'success': False, 'error': f'{step_key} returned non-zero exit code'}

            return {'success': True, 'data': {}}

        finally:
            # Restore original TMP_DIR
            if original_tmp:
                os.environ['TMP_DIR'] = original_tmp
            elif 'TMP_DIR' in os.environ:
                del os.environ['TMP_DIR']

    except Exception as e:
        return {
            'success': False,
            'error': f'{step_key} exception: {str(e)}',
            'traceback': traceback.format_exc()
        }


def extract_final_results(prospect_id: str, tmp_dir: str) -> Dict[str, Any]:
    """
    Extract final results from completed pipeline for return.

    Reads evaluation results and doc metadata.
    """
    try:
        tmp_path = Path(tmp_dir)

        # Load evaluation results
        eval_file = tmp_path / prospect_id / 'sv_evaluation_record.json'
        profile_file = tmp_path / prospect_id / 'prospect_profile.json'
        doc_file = tmp_path / prospect_id / 'google_doc_metadata.json'

        results = {}

        if eval_file.exists():
            with open(eval_file, 'r') as f:
                evaluation = json.load(f)
                results['evaluation'] = evaluation
                results['overall_score'] = evaluation.get('overall_score')
                results['suggested_action'] = evaluation.get('suggested_action')
                results['confidence_level'] = evaluation.get('confidence_level')
                results['scores'] = evaluation.get('scores')

        if profile_file.exists():
            with open(profile_file, 'r') as f:
                profile = json.load(f)
                results['company_name'] = profile.get('company_name')
                results['url'] = profile.get('canonical_url')

        if doc_file.exists():
            with open(doc_file, 'r') as f:
                doc_metadata = json.load(f)
                results['doc_url'] = doc_metadata.get('doc_url')
                results['doc_id'] = doc_metadata.get('doc_id')

        return results

    except Exception as e:
        print(f"[WARN] Failed to extract final results: {e}")
        return {}


def run_pipeline(
    url: str,
    run_mode: str = 'standard',
    tmp_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[str, str, int], None]] = None
) -> Dict[str, Any]:
    """
    Run complete SV pipeline with error handling and progress tracking.

    Args:
        url: Company URL to analyze
        run_mode: 'standard' or 'deep_canada'
        tmp_dir: Temporary directory (auto-detected if None)
        progress_callback: Function(step_key, step_display, progress_pct)

    Returns:
        {
            'success': bool,
            'prospect_id': str,
            'results': {
                'steps': {step_key: result_dict, ...},
                'overall_score': float,
                'suggested_action': str,
                'doc_url': str,
                ...
            },
            'error': str,  # if success=False
            'step': str,   # failed step if success=False
        }
    """
    # Initialize
    tmp_dir = get_tmp_dir(tmp_dir)
    results = {'steps': {}}

    print(f"\n{'='*60}")
    print("SV PIPELINE - PROGRAMMATIC EXECUTION")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Run Mode: {run_mode}")
    print(f"Tmp Dir: {tmp_dir}\n")

    try:
        # ====================
        # STEP 1: URL Intake
        # ====================
        step_info = PIPELINE_STEPS[0]  # url_intake
        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_start'])

        print(f"[1/7] {step_info['display']}...")
        result = run_url_intake(url, tmp_dir, progress_callback)
        results['steps']['url_intake'] = result

        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'URL intake failed'),
                'step': 'url_intake',
                'results': results
            }

        prospect_id = result['prospect_id']
        print(f"[OK] Prospect ID: {prospect_id}")

        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_end'])

        # ====================
        # STEP 2: Source Capture
        # ====================
        step_info = PIPELINE_STEPS[1]  # source_capture
        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_start'])

        print(f"\n[2/7] {step_info['display']}...")
        result = run_pipeline_step('source_capture', prospect_id, tmp_dir)
        results['steps']['source_capture'] = result

        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'Source capture failed'),
                'step': 'source_capture',
                'prospect_id': prospect_id,
                'results': results
            }

        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_end'])

        # ====================
        # STEP 3: Data Enrichment
        # ====================
        step_info = PIPELINE_STEPS[2]  # data_enrichment
        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_start'])

        print(f"\n[3/7] {step_info['display']}...")
        result = run_pipeline_step('data_enrichment', prospect_id, tmp_dir)
        results['steps']['data_enrichment'] = result

        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'Data enrichment failed'),
                'step': 'data_enrichment',
                'prospect_id': prospect_id,
                'results': results
            }

        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_end'])

        # ====================
        # STEP 4: SV Evaluation
        # ====================
        step_info = PIPELINE_STEPS[3]  # sv_evaluation
        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_start'])

        print(f"\n[4/7] {step_info['display']}...")
        result = run_pipeline_step('sv_evaluation', prospect_id, tmp_dir)
        results['steps']['sv_evaluation'] = result

        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'SV evaluation failed'),
                'step': 'sv_evaluation',
                'prospect_id': prospect_id,
                'results': results
            }

        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_end'])

        # ====================
        # STEP 4.5: Canadian Market Research (Optional)
        # ====================
        if run_mode == 'deep_canada':
            step_info = PIPELINE_STEPS[4]  # canadian_market_research
            if progress_callback:
                progress_callback(step_info['key'], step_info['display'], step_info['progress_start'])

            print(f"\n[4.5/7] {step_info['display']}...")
            result = run_pipeline_step('canadian_market_research', prospect_id, tmp_dir)
            results['steps']['canadian_market_research'] = result

            if not result['success']:
                # Don't fail entire pipeline for optional step
                print(f"[WARN] Canadian research failed (non-critical): {result.get('error')}")

            if progress_callback:
                progress_callback(step_info['key'], step_info['display'], step_info['progress_end'])
        else:
            print(f"\n[4.5/7] Skipping Canadian market research (run_mode={run_mode})")
            if progress_callback:
                progress_callback('canadian_market_research', 'Skipped Canadian research', 80)

        # ====================
        # STEP 5: Generate Profile Doc
        # ====================
        step_info = PIPELINE_STEPS[5]  # generate_profile_doc
        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_start'])

        print(f"\n[5/7] {step_info['display']}...")
        result = run_pipeline_step('generate_profile_doc', prospect_id, tmp_dir)
        results['steps']['generate_profile_doc'] = result

        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'Profile doc generation failed'),
                'step': 'generate_profile_doc',
                'prospect_id': prospect_id,
                'results': results
            }

        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_end'])

        # ====================
        # STEP 6: Master List Update
        # ====================
        step_info = PIPELINE_STEPS[6]  # master_list_update
        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_start'])

        print(f"\n[6/7] {step_info['display']}...")
        result = run_pipeline_step('master_list_update', prospect_id, tmp_dir)
        results['steps']['master_list_update'] = result

        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'Master list update failed'),
                'step': 'master_list_update',
                'prospect_id': prospect_id,
                'results': results
            }

        if progress_callback:
            progress_callback(step_info['key'], step_info['display'], step_info['progress_end'])

        # ====================
        # Extract Final Results
        # ====================
        print(f"\n[7/7] Extracting final results...")
        final_results = extract_final_results(prospect_id, tmp_dir)
        results.update(final_results)

        print(f"\n{'='*60}")
        print("PIPELINE COMPLETE - SUCCESS")
        print(f"{'='*60}")
        print(f"Prospect ID: {prospect_id}")
        print(f"Company: {results.get('company_name', 'N/A')}")
        print(f"Score: {results.get('overall_score', 'N/A')}")
        print(f"Action: {results.get('suggested_action', 'N/A')}")
        print(f"Google Doc: {results.get('doc_url', 'N/A')}")
        print(f"{'='*60}\n")

        return {
            'success': True,
            'prospect_id': prospect_id,
            'results': results
        }

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Pipeline crashed: {e}")
        traceback.print_exc()

        return {
            'success': False,
            'error': f'Pipeline exception: {str(e)}',
            'traceback': traceback.format_exc(),
            'results': results
        }


if __name__ == "__main__":
    """
    CLI interface for testing pipeline_runner directly.

    Usage:
        python pipeline_runner.py <url> [run_mode]

    Examples:
        python pipeline_runner.py https://figured.com
        python pipeline_runner.py https://figured.com deep_canada
    """
    if len(sys.argv) < 2:
        print("Usage: python pipeline_runner.py <url> [run_mode]")
        print("Example: python pipeline_runner.py https://figured.com")
        print("Example: python pipeline_runner.py https://figured.com deep_canada")
        sys.exit(1)

    url = sys.argv[1]
    run_mode = sys.argv[2] if len(sys.argv) > 2 else 'standard'

    # Simple progress callback for CLI
    def print_progress(step_key, step_display, progress_pct):
        print(f"  → [{progress_pct}%] {step_display}")

    # Run pipeline
    result = run_pipeline(
        url=url,
        run_mode=run_mode,
        progress_callback=print_progress
    )

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)
