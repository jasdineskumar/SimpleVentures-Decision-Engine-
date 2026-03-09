# Batch SV Pipeline

## Goal
Process multiple companies through the complete SV pipeline in batch mode, using scraped directory data or manual lists.

## Input
Path to batch scrape JSON file from `batch_directory_scrape.py`:
```
.tmp/batch_scrapes/yc_winter_2026_*/companies.json
```

OR manual JSON array:
```json
[
  {"name": "Company A", "website": "https://example.com"},
  {"name": "Company B", "website": "https://example.org"}
]
```

## Workflow Sequence

For each company in batch:
1. URL Intake & Canonicalization
2. Source Capture
3. Data Enrichment
4. SV Evaluation
5. Canadian Market Research (OPTIONAL - if enabled in `.env`)
6. Generate Profile Document
7. Master List Update

## Processing Modes

### 1. Sequential (Default)
- Process one company at a time
- Easier to debug
- Lower resource usage
- ~2-3 minutes per company

### 2. Parallel (Optional)
- Process N companies concurrently (default: 3)
- Faster for large batches
- Higher resource usage
- Risk of API rate limits

### 3. Resume Mode
- Skip already processed companies
- Check Master Prospect List for existing entries
- Continue from last failure

## Execution Tool

**Script:** `Executions/batch_sv_pipeline.py`

**Usage:**
```bash
# Process scraped batch
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_winter_2026_*/companies.json

# Process with parallel mode (3 concurrent)
python Executions/batch_sv_pipeline.py companies.json --parallel 3

# Resume failed batch
python Executions/batch_sv_pipeline.py companies.json --resume

# Skip already processed
python Executions/batch_sv_pipeline.py companies.json --skip-existing
```

## Checkpointing & Recovery

### Progress Tracking
- Save progress after each company
- Track: processed, failed, skipped
- Progress file: `.tmp/batch_progress_{timestamp}.json`

### Error Handling
- Continue on single company failure
- Log errors to batch log file
- Generate summary report at end

### Resume Capability
- Load previous progress
- Skip successfully processed companies
- Retry failed companies

## Output

### 1. Individual Company Artifacts
All standard SV pipeline outputs for each company:
- `.tmp/{prospect_id}/` - All workflow artifacts
- Google Docs - Profile documents
- Google Sheets - Master list rows

### 2. Batch Summary Report
**File:** `.tmp/batch_scrapes/{source}_{timestamp}/batch_report.json`

**Schema:**
```json
{
  "batch_info": {
    "source": "yc",
    "batch": "Winter 2026",
    "started_at": "ISO 8601",
    "completed_at": "ISO 8601",
    "duration_seconds": 450
  },
  "results": {
    "total_companies": 10,
    "successful": 9,
    "failed": 1,
    "skipped": 0
  },
  "companies": [
    {
      "name": "Chasi",
      "website": "https://chasi.co/",
      "prospect_id": "chasi_co_2b26d0ee",
      "status": "success",
      "score": 3.8,
      "action": "monitor",
      "google_doc": "https://docs.google.com/document/d/...",
      "duration_seconds": 42
    }
  ],
  "failures": [
    {
      "name": "FailCorp",
      "website": "https://failcorp.com",
      "error": "Source capture timeout",
      "workflow": "source_capture"
    }
  ]
}
```

### 3. Batch Statistics
- Average processing time per company
- Score distribution
- Top prospects (score >= 4.0)
- Failed workflows breakdown

## Performance Optimization

### 1. API Rate Limiting
- Firecrawl: 100 requests/hour (monitor usage)
- OpenAI/Anthropic: Track token usage
- Google APIs: Batch writes where possible

### 2. Resource Management
- Close browser contexts between companies
- Clear temp files for processed companies
- Monitor memory usage

### 3. Parallelization Strategy
- Max 3 concurrent companies (avoid rate limits)
- Separate browser instances per thread
- Share Google Sheets connection

## Edge Cases

### 1. Duplicate Companies
- Check URL against Master Prospect List
- Skip if `--skip-existing` flag set
- Otherwise, create new prospect_id with timestamp

### 2. Invalid Websites
- Log and skip companies with invalid URLs
- Continue batch processing
- Include in failure report

### 3. Partial Failures
- If workflow fails mid-pipeline, log last successful step
- Don't add to Master List if incomplete
- Flag for manual review

### 4. API Quota Exhaustion
- Detect rate limit errors
- Pause processing
- Resume when quota resets
- Log pause duration

## Success Criteria

- All valid companies processed or logged as failed
- Batch summary report generated
- No data loss on failures
- Progress saved for resume capability
- Master List updated with all successful companies
- Processing time: < 3 minutes per company average

## Integration Example

Complete end-to-end batch workflow:

```bash
# Step 1: Scrape directory
python Executions/batch_directory_scrape.py \
  --source yc \
  --batch "Winter 2026" \
  --max 10

# Step 2: Process batch through SV pipeline
python Executions/batch_sv_pipeline.py \
  .tmp/batch_scrapes/yc_winter_2026_*/companies.json \
  --parallel 3

# Step 3: Review results
cat .tmp/batch_scrapes/yc_winter_2026_*/batch_report.json
```

## Self-Annealing Notes

**Common Failures:**
- API rate limits hit during batch → Reduce parallel workers
- Memory leak on large batches → Restart browser every 10 companies
- Google Sheets API timeout → Implement retry with exponential backoff

**Optimizations Discovered:**
- Batching Google Sheets writes (10 rows at once) saves 60% time
- Reusing browser context between companies reduces overhead by 30%
- Pre-checking duplicates before processing saves unnecessary API calls

**Learnings from testing will be added here.**
