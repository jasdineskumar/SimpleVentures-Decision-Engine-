#!/usr/bin/env python3
"""
Jobs Sheet Manager - Permanent job history in Google Sheets
Solves Problem #3: Modal Dict is ephemeral, Sheets is the source of truth
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
import gspread
from google_auth_cloud import get_google_credentials


def get_jobs_worksheet():
    """
    Get or create the Jobs worksheet in the Master Prospect List spreadsheet.
    This is the permanent system of record for all analysis runs.
    """
    creds = get_google_credentials()
    gc = gspread.authorize(creds)

    sheet_id = os.environ.get('MASTER_PROSPECT_LIST_SHEET_ID')
    if not sheet_id:
        raise ValueError("MASTER_PROSPECT_LIST_SHEET_ID not set")

    spreadsheet = gc.open_by_key(sheet_id)

    # Try to get Jobs worksheet, create if doesn't exist
    try:
        worksheet = spreadsheet.worksheet('Jobs')
        print("[INFO] Jobs worksheet found")
    except gspread.exceptions.WorksheetNotFound:
        print("[INFO] Creating Jobs worksheet...")
        worksheet = spreadsheet.add_worksheet(title='Jobs', rows=1000, cols=20)
        setup_jobs_sheet_formatting(worksheet)

    return worksheet, spreadsheet


def setup_jobs_sheet_formatting(worksheet):
    """Set up header row and formatting for the Jobs worksheet."""

    # Define headers
    headers = [
        'Job ID',
        'Status',
        'Prospect ID',
        'Company Name',
        'URL',
        'Run Mode',
        'Overall Score',
        'Suggested Action',
        'Confidence',
        'Google Doc URL',
        'Sheets Row',
        'Created At',
        'Completed At',
        'Duration (min)',
        'Notes',
        'Error Message',
        'Failed Step'
    ]

    # Insert headers
    worksheet.update(range_name='A1:Q1', values=[headers])

    # Format header row (blue background, white bold text)
    worksheet.format('A1:Q1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })

    # Set column widths
    sheet_id = worksheet._properties['sheetId']
    body = {
        'requests': [
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1}, 'properties': {'pixelSize': 180}, 'fields': 'pixelSize'}},  # Job ID
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},  # Status
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3}, 'properties': {'pixelSize': 180}, 'fields': 'pixelSize'}},  # Prospect ID
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 4}, 'properties': {'pixelSize': 200}, 'fields': 'pixelSize'}},  # Company Name
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 5}, 'properties': {'pixelSize': 250}, 'fields': 'pixelSize'}},  # URL
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 5, 'endIndex': 6}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},  # Run Mode
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 7}, 'properties': {'pixelSize': 110}, 'fields': 'pixelSize'}},  # Overall Score
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 7, 'endIndex': 8}, 'properties': {'pixelSize': 130}, 'fields': 'pixelSize'}},  # Suggested Action
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 8, 'endIndex': 9}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},  # Confidence
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 9, 'endIndex': 10}, 'properties': {'pixelSize': 300}, 'fields': 'pixelSize'}},  # Google Doc URL
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 10, 'endIndex': 11}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},  # Sheets Row
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 11, 'endIndex': 12}, 'properties': {'pixelSize': 150}, 'fields': 'pixelSize'}},  # Created At
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 12, 'endIndex': 13}, 'properties': {'pixelSize': 150}, 'fields': 'pixelSize'}},  # Completed At
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 13, 'endIndex': 14}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},  # Duration
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 14, 'endIndex': 15}, 'properties': {'pixelSize': 250}, 'fields': 'pixelSize'}},  # Notes
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 15, 'endIndex': 16}, 'properties': {'pixelSize': 250}, 'fields': 'pixelSize'}},  # Error Message
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 16, 'endIndex': 17}, 'properties': {'pixelSize': 120}, 'fields': 'pixelSize'}},  # Failed Step
        ]
    }
    worksheet.spreadsheet.batch_update(body)

    # Freeze header row
    body = {
        'requests': [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {'frozenRowCount': 1}
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        }]
    }
    worksheet.spreadsheet.batch_update(body)

    print("[OK] Jobs sheet formatting complete")


def write_job_to_sheet(job_data: Dict[str, Any]) -> int:
    """
    Write job record to Jobs worksheet.
    Returns the row number where the job was written.

    This is the PERMANENT record that survives Modal Dict cleanup.
    """
    worksheet, spreadsheet = get_jobs_worksheet()

    # Calculate duration if completed
    duration_min = None
    if job_data.get('status') == 'completed' and job_data.get('created_at') and job_data.get('completed_at'):
        try:
            created = datetime.fromisoformat(job_data['created_at'].replace('Z', '+00:00'))
            completed = datetime.fromisoformat(job_data['completed_at'].replace('Z', '+00:00'))
            duration_min = round((completed - created).total_seconds() / 60, 2)
        except:
            pass

    # Extract results if completed
    results = job_data.get('results', {})

    # Build row data
    row = [
        job_data.get('job_id', ''),
        job_data.get('status', '').upper(),
        job_data.get('prospect_id', ''),
        job_data.get('company_name', ''),
        job_data.get('url', ''),
        job_data.get('run_mode', 'standard'),
        results.get('overall_score', '') if results else '',
        results.get('suggested_action', '') if results else '',
        results.get('confidence_level', '') if results else '',
        results.get('google_doc_url', '') if results else '',
        '',  # Sheets Row (populated by master_list_update)
        job_data.get('created_at', ''),
        job_data.get('completed_at', ''),
        duration_min or '',
        job_data.get('notes', ''),
        job_data.get('error', ''),
        job_data.get('failed_step', '')
    ]

    # Check if job already exists (update instead of insert)
    existing_jobs = worksheet.col_values(1)  # Job ID column
    job_id = job_data.get('job_id')

    if job_id in existing_jobs:
        # Update existing row
        row_num = existing_jobs.index(job_id) + 1
        worksheet.update(range_name=f'A{row_num}:Q{row_num}', values=[row])
        print(f"[OK] Updated job {job_id} in row {row_num}")
    else:
        # Append new row
        worksheet.append_row(row)
        row_num = len(existing_jobs) + 1
        print(f"[OK] Added job {job_id} to row {row_num}")

    # Apply conditional formatting based on status
    apply_status_formatting(worksheet, row_num, job_data.get('status'))

    return row_num


def apply_status_formatting(worksheet, row_num: int, status: str):
    """Apply color coding based on job status."""

    # Status column (B)
    status_range = f'B{row_num}'

    if status == 'completed':
        # Green background
        worksheet.format(status_range, {
            'backgroundColor': {'red': 0.85, 'green': 1, 'blue': 0.85},
            'textFormat': {'bold': True}
        })
    elif status == 'failed':
        # Red background
        worksheet.format(status_range, {
            'backgroundColor': {'red': 1, 'green': 0.85, 'blue': 0.85},
            'textFormat': {'bold': True}
        })
    elif status == 'running':
        # Yellow background
        worksheet.format(status_range, {
            'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.85},
            'textFormat': {'bold': True}
        })
    else:  # queued
        # Gray background
        worksheet.format(status_range, {
            'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
        })


def get_jobs_from_sheet(limit: int = 100, status_filter: Optional[str] = None) -> list:
    """
    Read jobs from Google Sheets (permanent history).
    This is the source of truth for the dashboard.

    Args:
        limit: Maximum number of jobs to return
        status_filter: Filter by status (completed, failed, running, queued)

    Returns:
        List of job dictionaries
    """
    worksheet, _ = get_jobs_worksheet()

    # Get all rows (skip header)
    all_rows = worksheet.get_all_values()[1:]

    jobs = []
    for row in all_rows:
        if len(row) < 12:  # Skip incomplete rows
            continue

        job = {
            'job_id': row[0],
            'status': row[1].lower(),
            'prospect_id': row[2],
            'company_name': row[3],
            'url': row[4],
            'run_mode': row[5],
            'created_at': row[11],
            'completed_at': row[12],
        }

        # Add results if completed
        if row[6]:  # Has overall score
            job['results'] = {
                'overall_score': float(row[6]) if row[6] else None,
                'suggested_action': row[7],
                'confidence_level': row[8],
                'google_doc_url': row[9],
                'sheets_url': f"https://docs.google.com/spreadsheets/d/{os.environ['MASTER_PROSPECT_LIST_SHEET_ID']}/edit"
            }

        # Add error info if failed
        if row[15]:  # Has error message
            job['error'] = row[15]
            job['failed_step'] = row[16]

        # Filter by status if specified
        if status_filter and job['status'] != status_filter.lower():
            continue

        jobs.append(job)

    # Sort by created_at descending (most recent first)
    jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return jobs[:limit]


def update_job_status_in_sheet(job_id: str, status: str, error: Optional[str] = None):
    """
    Quick update of job status in Google Sheets.
    Used when job status changes (queued → running → completed/failed).
    """
    worksheet, _ = get_jobs_worksheet()

    # Find row with this job_id
    existing_jobs = worksheet.col_values(1)

    if job_id not in existing_jobs:
        print(f"[WARN] Job {job_id} not found in Jobs sheet")
        return

    row_num = existing_jobs.index(job_id) + 1

    # Update status column
    worksheet.update(f'B{row_num}', [[status.upper()]])

    # Update completed_at if completed
    if status == 'completed':
        worksheet.update(f'M{row_num}', [[datetime.utcnow().isoformat()]])

    # Update error if failed
    if status == 'failed' and error:
        worksheet.update(f'P{row_num}', [[error]])

    # Apply formatting
    apply_status_formatting(worksheet, row_num, status)

    print(f"[OK] Updated job {job_id} status to {status}")


if __name__ == "__main__":
    # Test the Jobs sheet setup
    print("Testing Jobs sheet manager...")

    worksheet, _ = get_jobs_worksheet()
    print(f"✓ Jobs worksheet ready with {worksheet.row_count} rows")

    # Test write
    test_job = {
        'job_id': 'job_test_123',
        'status': 'completed',
        'prospect_id': 'test_com_abc',
        'company_name': 'Test Company',
        'url': 'https://test.com',
        'run_mode': 'standard',
        'created_at': datetime.utcnow().isoformat(),
        'completed_at': datetime.utcnow().isoformat(),
        'results': {
            'overall_score': 4.2,
            'suggested_action': 'deeper_diligence',
            'confidence_level': 'HIGH',
            'google_doc_url': 'https://docs.google.com/document/d/test'
        }
    }

    row_num = write_job_to_sheet(test_job)
    print(f"✓ Test job written to row {row_num}")

    # Test read
    jobs = get_jobs_from_sheet(limit=5)
    print(f"✓ Retrieved {len(jobs)} jobs from sheet")
