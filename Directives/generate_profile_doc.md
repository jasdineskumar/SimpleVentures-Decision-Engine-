# Generate Profile Document

## Goal
Render human-readable markdown document from JSON artifacts using template.

## Inputs
- `prospect_profile.json`
- `sv_evaluation_record.json`
- `Directives/templates/SV_Profile_Template.md`

## Processing
1. Load both JSON files
2. Load template
3. Map JSON data to template placeholders
4. Render markdown document
5. Save as `.tmp/{prospect_id}/sv_profile.md`

## Output
Human-readable SV Profile Document (<2 min review)

## Execution
```bash
python Executions/generate_profile_doc.py <prospect_id>
```
