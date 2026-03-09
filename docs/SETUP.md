# SV Pipeline Setup Guide

## Prerequisites

- Python 3.9+ installed
- Git (for version control)
- Google Cloud account (free tier)
- Anthropic API account

---

## Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 2: Get API Keys

### A. Anthropic API Key (Required)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new key
5. Copy the key (starts with `sk-ant-...`)

**Cost:** Pay-as-you-go, ~$0.05 per company evaluation

### B. Google Sheets API Setup (Required)

**Option 1: Service Account (Recommended for Automation)**

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search "Google Sheets API"
   - Click "Enable"
4. Create Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in details, click "Create"
   - Skip optional steps, click "Done"
5. Download JSON key:
   - Click on the service account email
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key" > JSON
   - Save as `credentials.json` in project root
6. Share your Google Sheet:
   - Open your Master Prospect List Google Sheet
   - Click "Share"
   - Add the service account email (found in `credentials.json`)
   - Give "Editor" permissions

**Option 2: OAuth (For Personal Use)**

1. Follow steps 1-3 above
2. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app"
   - Download `credentials.json`
3. First run will prompt browser authentication

**Cost:** $0 (free tier)

### C. Firecrawl API (Optional)

Only needed if basic scraping fails on JavaScript-heavy sites.

1. Go to https://firecrawl.dev/
2. Sign up for free trial or paid plan
3. Get API key from dashboard
4. Add to `.env` file

**Cost:** $20/month for 500 scrapes or $0.04 per scrape

---

## Step 3: Configure Environment Variables

1. Copy the template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` with your actual values:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   GOOGLE_SERVICE_ACCOUNT_JSON=./credentials.json
   MASTER_PROSPECT_LIST_SHEET_ID=your-google-sheet-id
   MASTER_PROSPECT_LIST_SHEET_NAME=Prospects
   ```

3. Get your Google Sheet ID:
   - Open your Google Sheet
   - Look at the URL: `https://docs.google.com/spreadsheets/d/{THIS_IS_THE_ID}/edit`
   - Copy the ID between `/d/` and `/edit`

---

## Step 4: Create Master Prospect List Google Sheet

1. Create a new Google Sheet
2. Name it "SV Master Prospect List" (or your preference)
3. Create a sheet/tab named "Prospects"
4. Add header row (will be auto-populated by pipeline):
   ```
   | prospect_id | company_name | url | status | confidence | score | last_updated | ... |
   ```
5. Share with service account (if using service account method)
6. Copy Sheet ID to `.env`

---

## Step 5: Create Temporary Directory

```bash
mkdir .tmp
```

This directory will store all intermediate files during processing.

---

## Step 6: Verify Setup

Run a test script to verify all credentials work:

```bash
python Executions/test_setup.py
```

This will check:
- ✓ Environment variables loaded
- ✓ Anthropic API key valid
- ✓ Google Sheets API access
- ✓ Temporary directory writable

---

## Cost Summary

**Per Company Evaluation:**
- Data enrichment (LLM): ~$0.01-0.03
- SV evaluation (LLM): ~$0.02-0.05
- Source capture: $0 (or $0.04 if using Firecrawl)
- **Total: ~$0.03-0.12 per company**

**Monthly Estimates:**
- 10 companies: ~$1-2/month
- 100 companies: ~$5-15/month
- 500 companies: ~$30-60/month

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Google Sheets API not enabled"
Go to Google Cloud Console > APIs & Services > Library > Enable "Google Sheets API"

### "Permission denied" on Google Sheet
Make sure you shared the sheet with the service account email from `credentials.json`

### "Invalid API key"
Check that your `.env` file has the correct `ANTHROPIC_API_KEY` without extra spaces

---

## Next Steps

Once setup is complete, you're ready to:
1. Test individual workflows
2. Run the full pipeline on a sample URL
3. Review generated artifacts in `.tmp/`

See `Directives/` folder for workflow documentation.
