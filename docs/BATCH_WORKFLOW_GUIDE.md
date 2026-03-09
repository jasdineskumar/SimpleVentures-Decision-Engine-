# Batch Workflow Guide

## Overview

The batch workflow system allows you to scrape and process multiple companies from any directory source (YC batches, accelerator cohorts, VC portfolios, etc.) through the complete SV pipeline automatically.

**Built on the 3-Layer Architecture:**
1. **Directives** - What to do (batch_directory_scrape.md, batch_sv_pipeline.md)
2. **Orchestration** - Decision making (You read directives and coordinate)
3. **Execution** - Deterministic tools (batch_directory_scrape.py, batch_sv_pipeline.py)

---

## 🔍 Directory Link vs. Single Company Link

**IMPORTANT:** Know which tool to use based on the link type!

### **Directory Link** → Use Batch Workflow

A URL that shows a **LIST of MULTIPLE companies**:

| Example URL | Description | Company Count |
|-------------|-------------|---------------|
| `https://www.ycombinator.com/companies?batch=Winter%202026` | YC batch directory | 30+ companies |
| `https://www.producthunt.com/topics/ai` | Product Hunt AI category | 50+ products |
| `https://example-vc.com/portfolio` | VC portfolio page | 20+ companies |
| `https://www.crunchbase.com/lists/yc-companies/` | Crunchbase list | 100+ companies |

**Use this command:**
```bash
python Executions/batch_directory_scrape.py --source custom --config directory_config.json
```

---

### **Single Company Link** → Use Regular SV Pipeline

A URL for **ONE specific company**:

| Example URL | Description | Company Count |
|-------------|-------------|---------------|
| `https://chasi.co/` | Company website | 1 company |
| `https://www.ycombinator.com/companies/chasi` | YC company profile | 1 company |
| `https://example.com` | Any company website | 1 company |

**Use this command:**
```bash
python Executions/sv_pipeline.py https://chasi.co/
```

---

### **Automatic Link Type Detection**

Not sure which tool to use? Run the detector:

```bash
python Executions/detect_link_type.py <url>
```

**Example:**
```bash
# Check YC batch URL
python Executions/detect_link_type.py "https://www.ycombinator.com/companies?batch=Winter%202026"
# Output: DIRECTORY DETECTED → Use batch_directory_scrape.py

# Check company website
python Executions/detect_link_type.py "https://chasi.co/"
# Output: SINGLE COMPANY DETECTED → Use sv_pipeline.py

# Check YC company profile
python Executions/detect_link_type.py "https://www.ycombinator.com/companies/chasi"
# Output: SINGLE COMPANY DETECTED → Use sv_pipeline.py
```

---

### **Manual Decision Guide**

If detector is unavailable, use this flowchart:

```
┌─────────────────────────────────────┐
│   Got a URL? Which tool to use?     │
└─────────────────────────────────────┘
             │
             ▼
      Open URL in browser
             │
             ▼
   ┌─────────────────────┐
   │ How many companies  │
   │   do you see?       │
   └─────────────────────┘
        │            │
        ▼            ▼
    Multiple       Single
    Companies      Company
        │            │
        ▼            ▼
   Use BATCH     Use REGULAR
   Workflow      SV Pipeline
        │            │
        ▼            ▼
batch_directory_  sv_pipeline.py
   scrape.py
```

**Still unsure? Look for these indicators:**

**Directory Link Indicators:**
- ✓ Query parameters in URL (`?batch=`, `?category=`, `?filter=`)
- ✓ Pagination buttons ("Next", "Page 2", "Load More")
- ✓ Multiple company cards/listings on one page
- ✓ Page title: "Companies", "Portfolio", "Directory", "Batch"

**Single Company Indicators:**
- ✓ Root domain (e.g., `https://company.com`)
- ✓ About, Product, Pricing pages
- ✓ One company name in page title
- ✓ No list of other companies

---

## Quick Start

### Process YC Batch (One Command)
```bash
# Scrape and process first 10 companies from YC Winter 2026
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 10 && \
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_winter_2026_*/companies.json
```

### Two-Step Process (More Control)

**Step 1: Scrape Directory**
```bash
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 10
```

**Step 2: Process Companies**
```bash
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_winter_2026_*/companies.json
```

---

## Supported Directory Sources

### 1. Y Combinator Batches
```bash
python Executions/batch_directory_scrape.py \
  --source yc \
  --batch "Winter 2026" \
  --max 20
```

**Supported batch formats:**
- "Winter 2026", "Summer 2025"
- "W26", "S25"
- Any YC batch name

### 2. Product Hunt Topics
```bash
python Executions/batch_directory_scrape.py \
  --source product_hunt \
  --topic AI \
  --max 30
```

**Note:** Product Hunt scraping is planned but not yet implemented.

### 3. CSV Import
```bash
python Executions/batch_directory_scrape.py \
  --source csv \
  --file companies.csv
```

**CSV Format:**
```csv
name,website,description
Acme Corp,https://acme.com,AI-powered widgets
Beta Inc,https://beta.io,SaaS platform for developers
```

### 4. Custom Directory with Config
```bash
python Executions/batch_directory_scrape.py \
  --source custom \
  --config scrape_config.json
```

**Config Example (scrape_config.json):**
```json
{
  "url": "https://example.com/startups",
  "pagination": {
    "type": "button",
    "selector": "button.next",
    "max_pages": 5
  },
  "selectors": {
    "company_card": ".company-item",
    "name": "h2.company-name",
    "website": "a.website-link",
    "description": "p.description"
  }
}
```

---

## Batch Pipeline Options

### Sequential Processing (Default)
Process one company at a time - safer, easier to debug:
```bash
python Executions/batch_sv_pipeline.py companies.json
```

### Parallel Processing
Process multiple companies concurrently (faster, higher resource usage):
```bash
python Executions/batch_sv_pipeline.py companies.json --parallel 3
```

**Recommendations:**
- Use `--parallel 1-2` for small batches (<10 companies)
- Use `--parallel 3` for medium batches (10-50 companies)
- Max 5 workers to avoid API rate limits

### Skip Already Processed
Skip companies already in Master Prospect List:
```bash
python Executions/batch_sv_pipeline.py companies.json --skip-existing
```

### Resume Failed Batch
Continue from last failure point:
```bash
python Executions/batch_sv_pipeline.py companies.json --resume
```

---

## Output Structure

### Directory Layout
```
.tmp/batch_scrapes/
└── yc_winter_2026_20260101_213614/
    ├── companies.json           # Scraped company data
    ├── batch_report.json        # Processing results
    └── batch_progress_*.json    # Progress tracking (for resume)
```

### Individual Company Artifacts
Each processed company gets:
```
.tmp/{prospect_id}/
├── canonical_url.json
├── raw_sources/
│   ├── content.md
│   └── metadata.json
├── prospect_profile.json
├── sv_evaluation_record.json
├── sv_profile.md
└── google_doc_metadata.json
```

### Batch Report Schema
```json
{
  "batch_info": {
    "source": "yc",
    "batch": "Winter 2026",
    "started_at": "2026-01-01T21:00:00Z",
    "completed_at": "2026-01-01T21:45:00Z",
    "duration_seconds": 2700
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
  "failures": [],
  "statistics": {
    "average_duration": 270,
    "score_distribution": {
      "min": 2.8,
      "max": 4.0,
      "average": 3.5,
      "count_4_plus": 1,
      "count_3_to_4": 7,
      "count_below_3": 1
    },
    "top_prospects": [...]
  }
}
```

---

## Real-World Examples

### Example 1: Evaluate YC W26 Batch
```bash
# Scrape all companies (34 total)
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 34

# Process in parallel (3 workers, ~90 minutes total)
python Executions/batch_sv_pipeline.py \
  .tmp/batch_scrapes/yc_winter_2026_*/companies.json \
  --parallel 3

# Check results
cat .tmp/batch_scrapes/yc_winter_2026_*/batch_report.json
```

### Example 2: Import from Spreadsheet
1. Export Google Sheet to CSV
2. Save as `companies.csv`
3. Run:
```bash
python Executions/batch_directory_scrape.py --source csv --file companies.csv
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/csv_*/companies.json
```

### Example 3: Custom VC Portfolio
1. Create `vc_portfolio_config.json` with selectors
2. Run:
```bash
python Executions/batch_directory_scrape.py --source custom --config vc_portfolio_config.json
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/custom_*/companies.json
```

### Example 4: Resume Failed Batch
If processing fails midway:
```bash
# Original run failed at company #15
python Executions/batch_sv_pipeline.py companies.json --resume

# Will skip companies 1-14 and continue from #15
```

---

## Performance & Optimization

### Processing Time
- **Per company:** 2-3 minutes (sequential)
- **Batch of 10:** ~25 minutes (sequential), ~10 minutes (parallel 3x)
- **Batch of 50:** ~2 hours (sequential), ~45 minutes (parallel 3x)

### Resource Usage
- **Memory:** ~500MB per worker (browser instance)
- **API Calls:**
  - Firecrawl: 1-3 requests per company
  - OpenAI/Anthropic: ~20K tokens per company
  - Google APIs: 2 writes per company

### Rate Limits
- **Firecrawl:** 100 requests/hour (monitor usage)
- **OpenAI:** 10K requests/minute (unlikely to hit)
- **Google Sheets:** 300 writes/minute (batch writes help)

### Best Practices
1. Start with small batches (5-10) to test
2. Use `--skip-existing` to avoid reprocessing
3. Run large batches overnight with parallel mode
4. Monitor `.tmp/batch_progress_*.json` for status
5. Check batch report for failures and retry manually

---

## Error Handling

### Common Errors

**1. Invalid Website URL**
```
Error: URL intake failed
Solution: Company skipped, logged in failures array
```

**2. Source Capture Timeout**
```
Error: Firecrawl timeout after 60s
Solution: Retry manually or increase timeout in source_capture.py
```

**3. API Rate Limit**
```
Error: 429 Too Many Requests
Solution: Reduce parallel workers or wait for quota reset
```

**4. Google Sheets API Timeout**
```
Error: Timeout writing to Master List
Solution: Batch pipeline will retry automatically
```

### Recovery Strategies

**Partial Failure:**
```bash
# Check batch report for failures
cat batch_report.json | grep "status.*failed"

# Process failed companies manually
python Executions/sv_pipeline.py <failed_company_url>
```

**Complete Failure:**
```bash
# Resume from progress file
python Executions/batch_sv_pipeline.py companies.json --resume
```

---

## Integration with Existing Workflows

### Add to Existing Pipeline
The batch workflow integrates seamlessly:

```bash
# 1. Scrape directory
python Executions/batch_directory_scrape.py --source yc --batch "W26" --max 10

# 2. Process batch
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_w26_*/companies.json

# 3. Add Canadian Market Research to top prospects
for prospect_id in $(cat batch_report.json | jq -r '.statistics.top_prospects[].prospect_id'); do
  python Executions/update_with_research.py $prospect_id
done
```

### Automation Example
```bash
#!/bin/bash
# Daily YC batch check script

BATCH="Winter 2026"
MAX_COMPANIES=50

# Scrape
python Executions/batch_directory_scrape.py \
  --source yc \
  --batch "$BATCH" \
  --max $MAX_COMPANIES

# Process (skip existing)
python Executions/batch_sv_pipeline.py \
  .tmp/batch_scrapes/yc_*/companies.json \
  --skip-existing \
  --parallel 3

# Email report (if you have email setup)
# python Executions/send_batch_report.py .tmp/batch_scrapes/yc_*/batch_report.json
```

---

## Self-Annealing Notes

### Lessons Learned

**1. YC Page Structure (Jan 2026):**
- Company links: `a[href^="/companies/"]`
- Website selector: `a:has-text("Website")`
- Needs 2-3 second wait for JavaScript rendering

**2. Browser Management:**
- Reusing browser contexts saves 30% time
- Must close tabs to avoid memory leaks
- Headless mode works fine, no need for headed

**3. Rate Limiting:**
- 3 parallel workers is sweet spot
- More than 5 workers triggers rate limits
- 1.5s delay between requests prevents blocks

**4. Error Recovery:**
- Progress tracking essential for large batches
- Skip-existing prevents waste on reruns
- Manual retry for edge cases is acceptable

### Future Improvements
- [ ] Add Product Hunt scraping
- [ ] Implement Crunchbase integration
- [ ] Add email notifications for batch completion
- [ ] Create web dashboard for batch monitoring
- [ ] Optimize Google Sheets bulk writes

---

## Troubleshooting

### Debug Mode
Add verbose logging:
```bash
export DEBUG=1
python Executions/batch_directory_scrape.py --source yc --batch "W26"
```

### Check Progress
```bash
# Monitor real-time progress
tail -f .tmp/batch_progress_*.json

# Count processed
ls -1 .tmp/*/canonical_url.json | wc -l
```

### Verify Outputs
```bash
# Check batch report
cat .tmp/batch_scrapes/*/batch_report.json | jq '.statistics'

# List top prospects
cat batch_report.json | jq '.statistics.top_prospects[].name'

# Check Master List
# Open: https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID/edit
```

---

## Summary

The batch workflow system provides:
- ✅ Automated scraping from any directory source
- ✅ Batch processing through complete SV pipeline
- ✅ Parallel execution for speed
- ✅ Error handling and recovery
- ✅ Comprehensive reporting
- ✅ Integration with existing tools

**Key Files:**
- `Directives/batch_directory_scrape.md` - Scraping directive
- `Directives/batch_sv_pipeline.md` - Batch processing directive
- `../Executions/batch_directory_scrape.py` - Scraping tool
- `../Executions/batch_sv_pipeline.py` - Batch processor
- `Directives/umbrella_sv_pipeline.md` - Updated umbrella directive

**Next Steps:**
1. Try small batch (5-10 companies)
2. Review batch report
3. Adjust parallel workers based on performance
4. Scale to larger batches
5. Integrate into daily workflow
