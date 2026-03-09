#!/usr/bin/env python3
"""
Batch SV Pipeline - Process multiple companies through the complete SV pipeline

Supports:
- Sequential processing (default)
- Parallel processing (optional)
- Resume capability
- Progress tracking
"""

import sys
import os
import json
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment
from dotenv import load_dotenv
load_dotenv()

TMP_DIR = Path(os.getenv('TMP_DIR', './.tmp'))


class BatchSVPipeline:
    """Batch processor for SV pipeline"""

    def __init__(self, parallel: int = 1, skip_existing: bool = False, resume: bool = False):
        self.parallel = parallel
        self.skip_existing = skip_existing
        self.resume = resume
        self.results = {
            'total_companies': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        self.companies_processed = []
        self.failures = []
        self.start_time = None
        self.progress_file = None

    def load_companies(self, input_file: str) -> List[Dict]:
        """Load companies from JSON file"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different input formats
        if isinstance(data, list):
            # Simple array format
            companies = data
        elif isinstance(data, dict) and 'companies' in data:
            # Batch scrape format
            companies = data['companies']
        else:
            raise ValueError("Invalid JSON format")

        self.results['total_companies'] = len(companies)
        print(f"[INFO] Loaded {len(companies)} companies")
        return companies

    def check_already_processed(self, website: str) -> bool:
        """Check if company already exists in Master Prospect List"""
        # TODO: Query Google Sheets to check for existing URL
        # For now, simple file-based check
        try:
            # Check if any prospect_id directory contains this URL
            for prospect_dir in TMP_DIR.glob('*/canonical_url.json'):
                with open(prospect_dir, 'r') as f:
                    canonical_data = json.load(f)
                    if canonical_data.get('canonical_url', '').lower().strip('/') == website.lower().strip('/'):
                        return True
        except:
            pass
        return False

    def process_single_company(self, company: Dict) -> Dict:
        """Process a single company through SV pipeline"""
        name = company.get('name', 'Unknown')
        website = company.get('website', '')

        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"Website: {website}")
        print(f"{'='*60}\n")

        start_time = time.time()
        result = {
            'name': name,
            'website': website,
            'status': 'pending',
            'prospect_id': None,
            'score': None,
            'action': None,
            'google_doc': None,
            'duration_seconds': 0,
            'error': None,
            'failed_workflow': None
        }

        try:
            # Check if already processed
            if self.skip_existing and self.check_already_processed(website):
                print(f"[SKIP] {name} already processed")
                result['status'] = 'skipped'
                self.results['skipped'] += 1
                return result

            # Run SV pipeline
            process = subprocess.run(
                ['python', 'Executions/sv_pipeline.py', website],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per company
            )

            if process.returncode == 0:
                # Extract results from output
                prospect_id = self._extract_from_output(process.stdout, 'Prospect ID:')
                score = self._extract_from_output(process.stdout, 'Overall Score:')
                action = self._extract_from_output(process.stdout, 'Suggested Action:')
                google_doc = self._extract_from_output(process.stdout, 'Google Doc:')

                result['status'] = 'success'
                result['prospect_id'] = prospect_id
                result['score'] = float(score.split('/')[0]) if score else None
                result['action'] = action
                result['google_doc'] = google_doc
                self.results['successful'] += 1

                print(f"\n[SUCCESS] {name}")
                print(f"  Prospect ID: {prospect_id}")
                print(f"  Score: {score}")
                print(f"  Action: {action}")

            else:
                # Pipeline failed
                result['status'] = 'failed'
                result['error'] = process.stderr or "Unknown error"
                result['failed_workflow'] = self._extract_failed_workflow(process.stderr)
                self.results['failed'] += 1
                self.failures.append(result)

                print(f"\n[FAILED] {name}")
                print(f"  Error: {result['error'][:200]}")

        except subprocess.TimeoutExpired:
            result['status'] = 'failed'
            result['error'] = "Pipeline timeout (>5 minutes)"
            self.results['failed'] += 1
            self.failures.append(result)
            print(f"\n[FAILED] {name} - Timeout")

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.results['failed'] += 1
            self.failures.append(result)
            print(f"\n[FAILED] {name} - {e}")

        result['duration_seconds'] = int(time.time() - start_time)
        return result

    def _extract_from_output(self, output: str, key: str) -> str:
        """Extract value from pipeline output"""
        for line in output.split('\n'):
            if key in line:
                return line.split(key)[1].strip()
        return ""

    def _extract_failed_workflow(self, stderr: str) -> str:
        """Determine which workflow failed from stderr"""
        workflows = ['url_intake', 'source_capture', 'data_enrichment',
                     'sv_evaluation', 'canadian_market_research',
                     'generate_profile_doc', 'master_list_update']
        for workflow in workflows:
            if workflow in stderr.lower():
                return workflow
        return "unknown"

    def save_progress(self, results: List[Dict]):
        """Save progress to file for resume capability"""
        if not self.progress_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.progress_file = TMP_DIR / f"batch_progress_{timestamp}.json"

        progress = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'companies_processed': results
        }

        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def generate_batch_report(self, companies: List[Dict], output_dir: Path, source_info: Dict = None):
        """Generate comprehensive batch report"""
        report = {
            'batch_info': {
                'source': source_info.get('type', 'unknown') if source_info else 'unknown',
                'batch': source_info.get('batch', '') if source_info else '',
                'started_at': self.start_time.isoformat(),
                'completed_at': datetime.now().isoformat(),
                'duration_seconds': int((datetime.now() - self.start_time).total_seconds())
            },
            'results': self.results,
            'companies': companies,
            'failures': self.failures,
            'statistics': {
                'average_duration': sum(c['duration_seconds'] for c in companies) / len(companies) if companies else 0,
                'score_distribution': self._calculate_score_distribution(companies),
                'top_prospects': [c for c in companies if c.get('score') is not None and c.get('score') >= 4.0]
            }
        }

        report_file = output_dir / 'batch_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n[OK] Batch report saved to: {report_file}")
        return report_file

    def _calculate_score_distribution(self, companies: List[Dict]) -> Dict:
        """Calculate score distribution"""
        scores = [c['score'] for c in companies if c.get('score') is not None]
        if not scores:
            return {}

        return {
            'min': min(scores),
            'max': max(scores),
            'average': sum(scores) / len(scores),
            'count_4_plus': len([s for s in scores if s >= 4.0]),
            'count_3_to_4': len([s for s in scores if 3.0 <= s < 4.0]),
            'count_below_3': len([s for s in scores if s < 3.0])
        }

    def process_batch(self, companies: List[Dict], source_info: Dict = None) -> List[Dict]:
        """Process batch of companies"""
        self.start_time = datetime.now()
        results = []

        if self.parallel > 1:
            # Parallel processing
            print(f"\n[INFO] Processing in parallel mode (workers: {self.parallel})")
            with ThreadPoolExecutor(max_workers=self.parallel) as executor:
                futures = {executor.submit(self.process_single_company, company): company
                          for company in companies}

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    self.companies_processed.append(result)

                    # Save progress after each company
                    self.save_progress(results)

        else:
            # Sequential processing
            print(f"\n[INFO] Processing sequentially")
            for i, company in enumerate(companies, 1):
                print(f"\n[{i}/{len(companies)}]")
                result = self.process_single_company(company)
                results.append(result)
                self.companies_processed.append(result)

                # Save progress after each company
                self.save_progress(results)

        return results

    def print_summary(self, report_file: Path):
        """Print batch processing summary"""
        print("\n" + "="*60)
        print("BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"Total Companies: {self.results['total_companies']}")
        print(f"Successful: {self.results['successful']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Skipped: {self.results['skipped']}")
        print(f"\nBatch Report: {report_file}")
        print(f"Master List: https://docs.google.com/spreadsheets/d/12J94HQSUY1qVA5QII1wFiABpP7Nd2L-mpvR1i5ABNAo/edit")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Process multiple companies through SV pipeline in batch'
    )
    parser.add_argument('input_file', help='JSON file with companies to process')
    parser.add_argument('--parallel', type=int, default=1,
                        help='Number of parallel workers (default: 1, max: 5)')
    parser.add_argument('--skip-existing', action='store_true',
                        help='Skip companies already in Master Prospect List')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from previous batch run')

    args = parser.parse_args()

    # Validate parallel workers
    if args.parallel > 5:
        print("[WARN] Limiting parallel workers to 5 to avoid rate limits")
        args.parallel = 5

    print("\n" + "="*60)
    print("BATCH SV PIPELINE")
    print("="*60)

    # Initialize batch processor
    processor = BatchSVPipeline(
        parallel=args.parallel,
        skip_existing=args.skip_existing,
        resume=args.resume
    )

    # Load companies
    companies = processor.load_companies(args.input_file)

    # Load source info if available
    source_info = None
    try:
        with open(args.input_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'source' in data:
                source_info = data['source']
    except:
        pass

    # Process batch
    results = processor.process_batch(companies, source_info)

    # Determine output directory
    input_path = Path(args.input_file)
    output_dir = input_path.parent if input_path.parent != Path('.') else TMP_DIR / 'batch_reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate report
    report_file = processor.generate_batch_report(results, output_dir, source_info)

    # Print summary
    processor.print_summary(report_file)

    # Return exit code based on results
    if processor.results['failed'] > 0:
        return 1  # Some failures
    return 0  # All successful


if __name__ == "__main__":
    sys.exit(main())
