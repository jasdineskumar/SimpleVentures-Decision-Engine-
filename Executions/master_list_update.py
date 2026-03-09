#!/usr/bin/env python3
"""Master Prospect List Update - Execution Layer"""

import sys, json, os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google_auth_cloud import get_google_credentials

load_dotenv()

def load_data(prospect_id):
    """Load profile and evaluation."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))

    with open(tmp_dir / prospect_id / 'prospect_profile.json', 'r') as f:
        profile = json.load(f)

    with open(tmp_dir / prospect_id / 'sv_evaluation_record.json', 'r') as f:
        evaluation = json.load(f)

    return profile, evaluation

def connect_sheets():
    """Connect to Google Sheets (service account for cloud compatibility)."""
    creds = get_google_credentials()

    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(os.getenv('MASTER_PROSPECT_LIST_SHEET_ID'))
    worksheet = sheet.worksheet(os.getenv('MASTER_PROSPECT_LIST_SHEET_NAME', 'Prospects'))
    return worksheet, sheet


def setup_sheet_formatting(worksheet):
    """Set up header row and formatting for the spreadsheet."""
    # Check if header exists
    try:
        first_row = worksheet.row_values(1)
        if first_row and 'Prospect ID' in first_row:
            print("[INFO] Headers already exist, skipping setup")
            return
    except:
        pass

    # Define headers
    headers = [
        'Prospect ID',
        'Company Name',
        'URL',
        'Source Type',
        'Date Evaluated',
        'Confidence',
        'Overall Score',
        'Problem Clarity',
        'MVP Speed',
        'Defensible Wedge',
        'Studio Fit',
        'Canada Fit',
        'Action',
        'Top Risks',
        'Status',
        'Profile Doc'
    ]

    # Insert headers
    worksheet.update(range_name='A1:P1', values=[headers])

    # Format header row
    worksheet.format('A1:P1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })

    # Set column widths using batch update
    sheet_id = worksheet._properties['sheetId']
    body = {
        'requests': [
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1}, 'properties': {'pixelSize': 180}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2}, 'properties': {'pixelSize': 200}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3}, 'properties': {'pixelSize': 250}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 4}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 5}, 'properties': {'pixelSize': 120}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 5, 'endIndex': 6}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 7}, 'properties': {'pixelSize': 110}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 7, 'endIndex': 8}, 'properties': {'pixelSize': 110}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 8, 'endIndex': 9}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 9, 'endIndex': 10}, 'properties': {'pixelSize': 130}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 10, 'endIndex': 11}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 11, 'endIndex': 12}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 12, 'endIndex': 13}, 'properties': {'pixelSize': 120}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 13, 'endIndex': 14}, 'properties': {'pixelSize': 300}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 14, 'endIndex': 15}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
            {'updateDimensionProperties': {'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 15, 'endIndex': 16}, 'properties': {'pixelSize': 300}, 'fields': 'pixelSize'}},
        ]
    }
    worksheet.spreadsheet.batch_update(body)

    # Freeze header row
    worksheet.freeze(rows=1)

    print("[OK] Set up spreadsheet formatting")

def upsert_row(worksheet, profile, evaluation, prospect_id):
    """Upsert row to sheet."""
    # Load Google Doc URL if exists
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    doc_url = ''
    try:
        with open(tmp_dir / prospect_id / 'google_doc_metadata.json', 'r') as f:
            doc_metadata = json.load(f)
            doc_url = doc_metadata.get('doc_url', '')
    except:
        pass

    # Prepare row data
    row_data = [
        prospect_id,
        profile.get('company_name', ''),
        profile.get('canonical_url', ''),
        profile.get('source_type', ''),
        evaluation.get('date_evaluated', '')[:10],
        evaluation.get('confidence_level', ''),
        evaluation.get('overall_score', 0),
        evaluation['scores']['problem_buyer_clarity']['score'],
        evaluation['scores']['mvp_speed']['score'],
        evaluation['scores']['defensible_wedge']['score'],
        evaluation['scores']['venture_studio_fit']['score'],
        evaluation['scores']['canada_market_fit']['score'],
        evaluation.get('suggested_action', ''),
        '; '.join(evaluation.get('primary_risks', [])[:2]),
        'processed',
        doc_url
    ]

    # Find existing row
    try:
        cell = worksheet.find(prospect_id)
        row_num = cell.row
        worksheet.update(values=[row_data], range_name=f'A{row_num}:P{row_num}')
        print(f"[OK] Updated existing row {row_num}")
    except:
        worksheet.append_row(row_data)
        row_num = len(worksheet.col_values(1))
        print(f"[OK] Inserted new row {row_num}")

    # Apply conditional formatting to score columns
    apply_row_formatting(worksheet, row_num, evaluation)


def apply_row_formatting(worksheet, row_num, evaluation):
    """Apply color-coded formatting based on scores and confidence."""
    # Color code overall score (column G)
    overall_score = evaluation.get('overall_score', 0)
    if overall_score >= 4:
        color = {'red': 0.72, 'green': 0.88, 'blue': 0.72}  # Green
    elif overall_score >= 3:
        color = {'red': 1, 'green': 0.95, 'blue': 0.6}  # Yellow
    elif overall_score >= 2:
        color = {'red': 1, 'green': 0.85, 'blue': 0.6}  # Orange
    else:
        color = {'red': 1, 'green': 0.75, 'blue': 0.75}  # Red

    worksheet.format(f'G{row_num}', {
        'backgroundColor': color,
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })

    # Color code confidence (column F)
    confidence = evaluation.get('confidence_level', 'UNKNOWN')
    if confidence == 'HIGH':
        conf_color = {'red': 0.72, 'green': 0.88, 'blue': 0.72}
    elif confidence == 'MEDIUM':
        conf_color = {'red': 1, 'green': 0.95, 'blue': 0.6}
    else:
        conf_color = {'red': 1, 'green': 0.85, 'blue': 0.6}

    worksheet.format(f'F{row_num}', {
        'backgroundColor': conf_color,
        'horizontalAlignment': 'CENTER'
    })

    # Color code suggested action (column M)
    action = evaluation.get('suggested_action', '')
    if action == 'deeper_diligence':
        action_color = {'red': 0.72, 'green': 0.88, 'blue': 0.72}
    elif action == 'outreach':
        action_color = {'red': 0.85, 'green': 0.92, 'blue': 1}
    elif action == 'monitor':
        action_color = {'red': 1, 'green': 0.95, 'blue': 0.6}
    else:  # reject
        action_color = {'red': 1, 'green': 0.75, 'blue': 0.75}

    worksheet.format(f'M{row_num}', {
        'backgroundColor': action_color,
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })


def main(prospect_id):
    print("="*60)
    print("MASTER PROSPECT LIST UPDATE")
    print("="*60)

    profile, evaluation = load_data(prospect_id)
    print(f"[OK] Loaded data for {profile.get('company_name')}")

    worksheet, sheet = connect_sheets()
    print(f"[OK] Connected to Google Sheets")

    # Set up formatting (only runs once)
    setup_sheet_formatting(worksheet)

    upsert_row(worksheet, profile, evaluation, prospect_id)

    print("\n" + "="*60)
    print("MASTER LIST UPDATE COMPLETE")
    print("="*60)
    print(f"Company: {profile.get('company_name')}")
    print(f"Score: {evaluation.get('overall_score')}/5.0")
    print(f"Action: {evaluation.get('suggested_action')}")
    print(f"Sheet: https://docs.google.com/spreadsheets/d/{os.getenv('MASTER_PROSPECT_LIST_SHEET_ID')}/edit")
    print("="*60 + "\n")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python master_list_update.py <prospect_id>")
        sys.exit(1)
    exit_code = main(sys.argv[1])
    sys.exit(exit_code)
