# SV Pipeline Quick Reference

## 🎯 Which Tool Should I Use?

### Step 1: Detect Link Type

```bash
python Executions/detect_link_type.py <url>
```

The detector automatically tells you which workflow to use.

---

## 📋 Common Workflows

### Single Company Evaluation

**When:** You have ONE company website to evaluate

**Command:**
```bash
python Executions/sv_pipeline.py <company_url>
```

**Example:**
```bash
python Executions/sv_pipeline.py https://chasi.co/
```

**Output:**
- `.tmp/{prospect_id}/` - All artifacts
- Google Doc with SV profile
- Row in Master Prospect List

---

### Batch Processing from Directory

**When:** You have a directory URL with MULTIPLE companies

**Step 1: Scrape**
```bash
# YC Batch
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 10

# CSV Import
python Executions/batch_directory_scrape.py --source csv --file companies.csv
```

**Step 2: Process**
```bash
# Sequential (safe)
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/*/companies.json

# Parallel (faster)
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/*/companies.json --parallel 3

# Skip existing
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/*/companies.json --skip-existing
```

**Output:**
- Individual artifacts for each company
- Batch report with statistics
- All companies in Master Prospect List

---

## 🔗 Link Type Examples

### Directory Links (Use Batch Workflow)

```
✓ https://www.ycombinator.com/companies?batch=Winter%202026
✓ https://www.producthunt.com/topics/ai
✓ https://example-vc.com/portfolio
✓ https://www.crunchbase.com/lists/yc-companies/
```

### Single Company Links (Use Regular SV Pipeline)

```
✓ https://chasi.co/
✓ https://example.com
✓ https://www.ycombinator.com/companies/chasi
✓ https://www.producthunt.com/posts/example
```

---

## 📊 Master Outputs

### Master Prospect List (Google Sheets)
```
https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID/edit
```

### Local Artifacts
```
.tmp/{prospect_id}/
├── canonical_url.json          # URL normalization
├── raw_sources/
│   ├── content.md              # Scraped content
│   └── metadata.json           # Source metadata
├── prospect_profile.json       # Enriched data
├── sv_evaluation_record.json  # SV scores
├── sv_profile.md              # Human-readable profile
└── google_doc_metadata.json   # Google Doc link
```

### Batch Reports
```
.tmp/batch_scrapes/{source}_{timestamp}/
├── companies.json              # Scraped companies
├── batch_report.json          # Processing results
└── batch_progress_*.json      # Resume checkpoint
```

---

## 🛠️ All Available Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `detect_link_type.py` | Detect directory vs single company | `python Executions/detect_link_type.py <url>` |
| `sv_pipeline.py` | Process single company | `python Executions/sv_pipeline.py <url>` |
| `batch_directory_scrape.py` | Scrape company directory | `python Executions/batch_directory_scrape.py --source yc --batch "W26"` |
| `batch_sv_pipeline.py` | Process batch of companies | `python Executions/batch_sv_pipeline.py companies.json` |
| `url_intake.py` | Normalize URL | `python Executions/url_intake.py <url>` |
| `source_capture.py` | Scrape website | `python Executions/source_capture.py <prospect_id>` |
| `data_enrichment.py` | Extract company data | `python Executions/data_enrichment.py <prospect_id>` |
| `sv_evaluation.py` | Score company | `python Executions/sv_evaluation.py <prospect_id>` |
| `canadian_market_research.py` | Deep market research | `python Executions/canadian_market_research.py <prospect_id>` |
| `generate_profile_doc.py` | Create Google Doc | `python Executions/generate_profile_doc.py <prospect_id>` |
| `master_list_update.py` | Add to Master List | `python Executions/master_list_update.py <prospect_id>` |
| `update_with_research.py` | Add research to existing | `python Executions/update_with_research.py <prospect_id>` |

---

## ⚙️ Configuration

### Enable Canadian Market Research
```bash
# In .env file
ENABLE_CANADIAN_RESEARCH=true
```

**Cost:** $0.30-0.50 per company (uses GPT-4.1)

---

## 🚀 Quick Start Examples

### Example 1: Single Company
```bash
# Evaluate one company
python Executions/sv_pipeline.py https://chasi.co/

# Check results
cat .tmp/chasi_co_*/sv_evaluation_record.json | grep "overall_score"
```

### Example 2: YC Batch
```bash
# Scrape YC W26, get first 10
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 10

# Process all in parallel
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_winter_2026_*/companies.json --parallel 3

# Check batch report
cat .tmp/batch_scrapes/yc_winter_2026_*/batch_report.json | grep "top_prospects"
```

### Example 3: CSV Import
```bash
# Create companies.csv
echo "name,website,description" > companies.csv
echo "Acme,https://acme.com,AI widgets" >> companies.csv
echo "Beta,https://beta.io,SaaS platform" >> companies.csv

# Import and process
python Executions/batch_directory_scrape.py --source csv --file companies.csv
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/csv_*/companies.json
```

---

## 📖 Full Documentation

- **[BATCH_WORKFLOW_GUIDE.md](BATCH_WORKFLOW_GUIDE.md)** - Complete batch workflow guide
- **[Directives/umbrella_sv_pipeline.md](../Directives/umbrella_sv_pipeline.md)** - Pipeline overview
- **[Directives/batch_directory_scrape.md](../Directives/batch_directory_scrape.md)** - Directory scraping directive
- **[Directives/batch_sv_pipeline.md](../Directives/batch_sv_pipeline.md)** - Batch processing directive
- **[CLAUDE.md](../CLAUDE.md)** - 3-layer architecture guide

---

## 🆘 Troubleshooting

### "Is this a directory or single company?"
```bash
python Executions/detect_link_type.py <url>
```

### "Company already processed, want to skip?"
```bash
python Executions/batch_sv_pipeline.py companies.json --skip-existing
```

### "Batch processing failed halfway?"
```bash
python Executions/batch_sv_pipeline.py companies.json --resume
```

### "Want faster processing?"
```bash
python Executions/batch_sv_pipeline.py companies.json --parallel 3
```

### "Where are my results?"
```bash
# Local artifacts
ls .tmp/{prospect_id}/

# Batch report
cat .tmp/batch_scrapes/*/batch_report.json

# Master List (Google Sheets)
# https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID/edit
```

---

## 📞 Support

For issues or questions:
- Check error logs in `.tmp/` directories
- Review directive files in `Directives/` for detailed workflows
- Consult [BATCH_WORKFLOW_GUIDE.md](BATCH_WORKFLOW_GUIDE.md) for examples
