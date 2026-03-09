# Umbrella SV Pipeline

## Goal
Execute all workflows for end-to-end company evaluation - supports both single company and batch processing.

## Input Options

### Single Company Mode
Raw URL (e.g., `https://figured.com`)

### Batch Mode
Directory source or company list:
- YC batch (e.g., "Winter 2026")
- Product Hunt topic
- CSV file with companies
- Custom directory with config

## Workflow Sequence
1. URL Intake & Canonicalization
2. Source Capture
3. Data Enrichment
4. SV Evaluation
5. **Canadian Market Research** (OPTIONAL - deep market analysis using GPT-4.1)
6. **Resolve Unknowns** (OPTIONAL - uses OpenAI o1 to fill UNKNOWN values via deep reasoning)
7. Generate Profile Document (creates Google Doc with all research and resolutions appended)
8. Master List Update (includes Google Doc URL from step 7)

**Important:**
- Canadian Market Research is **optional** - controlled by `ENABLE_CANADIAN_RESEARCH` in `.env`
- When enabled, runs automatically in pipeline ($0.30-0.50 per company)
- When disabled, can be run separately later using `update_with_research.py`
- Resolve Unknowns is **optional** - typically run manually after pipeline for companies with many UNKNOWN values
- Uses OpenAI o1-mini for deep reasoning ($0.10-0.50 per company depending on unknowns)
- Profile document generation MUST run after market research and unknown resolution to include all enhancements
- Profile document generation MUST run before master list update so the spreadsheet includes the Google Doc URL

## Canadian Market Research Toggle

**Enable research in pipeline:**
```bash
# In .env file
ENABLE_CANADIAN_RESEARCH=true
```

**Disable research (run separately later):**
```bash
# In .env file
ENABLE_CANADIAN_RESEARCH=false
```

**Add research to existing profile:**
```bash
python Executions/update_with_research.py <prospect_id>
```

## Resolve Unknowns (Post-Pipeline Enhancement)

**When to use:**
- Profile has many UNKNOWN values
- Need deeper insights for high-priority prospects
- Want AI-inferred market data and business model details

**Resolve unknowns for single company:**
```bash
# After running the pipeline
python Executions/resolve_unknowns.py <prospect_id>

# Regenerate profile doc with resolutions
python Executions/generate_profile_doc.py <prospect_id>
```

**How it works:**
- Uses OpenAI o1-mini (deep reasoning model)
- Analyzes company context and infers missing values
- Provides confidence levels (HIGH/MEDIUM/LOW) for each resolution
- Adds reasoning for transparency
- Cost: ~$0.10-0.50 per company depending on number of unknowns

## Checkpointing
Each workflow checks for existing output and skips if recent.

## Error Handling
- If any workflow fails, log error and stop
- Partial results are preserved
- Can resume from last successful step

## Link Type Detection

**Not sure if you have a directory or single company URL?**

Use the automatic detector:
```bash
python Executions/detect_link_type.py <url>
```

The detector will tell you:
- Whether it's a directory (multiple companies) or single company
- Which tool to use
- Recommended command to run

## Execution

### Single Company
```bash
python Executions/sv_pipeline.py <url>
```

### Batch Processing (Two-Step)

**Step 1: Scrape Directory**
```bash
# YC batch
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 10

# Product Hunt topic
python Executions/batch_directory_scrape.py --source product_hunt --topic AI --max 20

# CSV import
python Executions/batch_directory_scrape.py --source csv --file companies.csv

# Custom directory
python Executions/batch_directory_scrape.py --source custom --config scrape_config.json
```

**Step 2: Process Batch**
```bash
# Sequential (default)
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_winter_2026_*/companies.json

# Parallel (3 workers)
python Executions/batch_sv_pipeline.py companies.json --parallel 3

# Skip already processed companies
python Executions/batch_sv_pipeline.py companies.json --skip-existing

# Resume failed batch
python Executions/batch_sv_pipeline.py companies.json --resume
```

### One-Line Batch Example
```bash
# Scrape YC W26 and process first 6 companies
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 6 && \
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_winter_2026_*/companies.json
```

## Output

### Single Company
- All artifacts in `.tmp/{prospect_id}/`
- Row in Master Prospect List
- Human-readable SV Profile document

### Batch Processing
- Individual company artifacts for each prospect
- Batch summary report with statistics
- All companies added to Master Prospect List
- Progress tracking file for resume capability
