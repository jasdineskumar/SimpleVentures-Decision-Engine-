# Master Prospect List Update

## Goal
Upsert summary data to Google Sheet for tracking and comparison.

## Inputs
- `prospect_profile.json`
- `sv_evaluation_record.json`

## Processing
1. Load both JSON files
2. Extract key fields for spreadsheet row
3. Connect to Google Sheets
4. Check if prospect_id exists (update) or new (insert)
5. Upsert row with latest data

## Output
Updated row in Master Prospect List Google Sheet

## Execution
```bash
python Executions/master_list_update.py <prospect_id>
```

## Checkpointing
Compare data hash - only update if changed.
