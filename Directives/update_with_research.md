# Update Profile with Canadian Market Research

## Goal
Add Canadian market research to an existing prospect profile and update the Google Doc.

## Use Case
After initial screening, if a prospect looks promising and warrants deeper Canadian market analysis, run this workflow to add comprehensive research without re-running the entire pipeline.

## Input
- `prospect_id` (e.g., `didit_me_b825e120`)
- Existing prospect data in `.tmp/{prospect_id}/`

## Workflow Steps
1. Run Canadian Market Research workflow
2. Regenerate Profile Document (includes new research section)
3. Update Google Doc with research

## Execution
```bash
python Executions/update_with_research.py <prospect_id>
```

## Example
```bash
# Initial pipeline run (research disabled)
ENABLE_CANADIAN_RESEARCH=false python Executions/sv_pipeline.py https://example.com

# Later, after screening the initial profile
python Executions/update_with_research.py example_com_abc123
```

## Output
- Updated `canadian_market_research.json`
- Updated `canadian_market_research.md`
- Updated `sv_profile.md`
- Updated Google Doc with Section 9: Canadian Market Research
- New Google Doc URL in `google_doc_metadata.json`

## Cost Optimization
This approach allows you to:
1. Run fast initial screening (no research) on many prospects
2. Only run expensive deep research ($0.30-0.50 per company) on promising candidates
3. Update existing profiles without re-running entire pipeline
