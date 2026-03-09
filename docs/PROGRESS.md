# SV Pipeline Build Progress

**Date:** 2025-12-28
**Status:** In Progress (Autonomous Build Mode)

---

## ✅ Completed Setup

1. **Environment Configuration**
   - ✅ OpenAI API configured and tested
   - ✅ Firecrawl API configured and tested
   - ✅ Google Sheets API configured with OAuth
   - ✅ Google Drive API enabled
   - ✅ Master Prospect List created: [View Sheet](https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID/edit)
   - ✅ `.env` file configured
   - ✅ `.tmp/` directory created

2. **Infrastructure Files**
   - ✅ `requirements.txt` - Python dependencies
   - ✅ `.gitignore` - Git ignore rules
   - ✅ `.env.template` - Environment template
   - ✅ `SETUP.md` - Setup instructions
   - ✅ `test_setup.py` - Setup validation script
   - ✅ `quick_test.py` - Quick API test script

---

## ✅ Completed Workflows

### Workflow 1: URL Intake & Canonicalization

**Status:** ✅ Complete and Tested

**Files:**
- [Directives/url_intake.md](Directives/url_intake.md)
- [Executions/url_intake.py](Executions/url_intake.py)

**Features:**
- Normalizes raw URLs to canonical form
- Validates URL structure
- Detects source type (website, yc_profile, pitch_deck, etc.)
- Generates stable prospect IDs
- Checkpointing (skips if processed < 24h ago)

**Tested:**
- ✅ Basic URL normalization (example.com → https://example.com)
- ✅ YC profile detection
- ✅ Checkpointing functionality
- ✅ Prospect ID generation

---

### Workflow 2: Source Capture

**Status:** ✅ Complete and Tested

**Files:**
- [Directives/source_capture.md](Directives/source_capture.md)
- [Executions/source_capture.py](Executions/source_capture.py)

**Features:**
- Scrapes content using Firecrawl API (primary)
- BeautifulSoup fallback for simple HTML
- PDF extraction support
- Clean markdown output
- Metadata extraction (title, description, word count)
- Checkpointing (skips if scraped < 7 days ago)
- Handles rate limiting and errors

**Tested:**
- ✅ Firecrawl API scraping (example.com)
- ✅ Checkpointing functionality
- ✅ Metadata extraction
- ✅ Error handling

**Token Cost:** ~$0.04 per scrape (or free with Firecrawl free tier)

---

## ✅ Completed Workflows (Continued)

### Workflow 3: Data Enrichment (Prospect Profile)

**Status:** ✅ Complete and Tested

**Purpose:** Use LLM to structure scraped content into standardized Prospect Profile JSON

**Key Tasks:**
- Create directive file
- Create execution script with OpenAI integration
- Design Prospect Profile JSON schema
- Implement LLM prompt for structured extraction
- Test with minimal tokens
- Add checkpointing

**Files:**
- [Directives/data_enrichment.md](Directives/data_enrichment.md)
- [Executions/data_enrichment.py](Executions/data_enrichment.py)

**Features:**
- LLM-based structured extraction (gpt-4o-mini)
- JSON mode for reliable output
- UNKNOWN marking for missing data
- Confidence scoring (HIGH/MEDIUM/LOW)
- Checkpointing (skips if enriched < 24h ago)
- Token usage tracking

**Tested:**
- ✅ Figured.com enrichment (6,159 tokens ≈ $0.012)
- ✅ Structured JSON output
- ✅ UNKNOWN handling
- ✅ Confidence scoring (LOW due to limited homepage data)

**Actual Token Cost:** ~$0.01-0.02 per enrichment (using gpt-4o-mini)

---

## ⏳ Pending Workflows

### Workflow 4: SV Evaluation

**Purpose:** Apply SV criteria (5 dimensions) to Prospect Profile and generate scores + rationales

**Key Tasks:**
- Create directive file
- Create execution script with OpenAI integration
- Implement SV criteria scoring logic
- Generate confidence levels
- Identify risks and unknowns
- Test with minimal tokens

**Estimated Token Cost:** ~$0.02-0.05 per evaluation (using gpt-4o)

---

### Workflow 5: Master Prospect List Update

**Purpose:** Upsert summary data to Google Sheet for tracking and comparison

**Key Tasks:**
- Create directive file
- Create execution script with gspread integration
- Map JSON artifacts to spreadsheet columns
- Handle upsert logic (update if exists, insert if new)
- Test with sample data

**Token Cost:** $0 (no LLM calls)

---

### Workflow 6: Generate Profile Document

**Purpose:** Render human-readable markdown document from JSON artifacts using template

**Key Tasks:**
- Create directive file
- Create execution script with Jinja2 templating
- Map JSON data to SV_Profile_Template.md
- Handle UNKNOWN values gracefully
- Generate final markdown document

**Token Cost:** $0 (no LLM calls)

---

### Workflow 7: Umbrella Pipeline Orchestrator

**Purpose:** Execute all 6 workflows in sequence with checkpointing and error handling

**Key Tasks:**
- Create umbrella directive
- Create orchestrator script
- Implement sequential workflow execution
- Handle workflow failures gracefully
- Add comprehensive logging
- Test end-to-end with real company URL

**Token Cost:** Sum of individual workflow costs

---

## 📊 Current Test Data

**Prospects Processed:**
1. `example_com_c984d06a` (example.com)
   - ✅ URL intake complete
   - ✅ Source capture complete (20 words)
   - ⏳ Enrichment pending

2. `figured_com_41a904d3` (Figured.com - MAIN TEST CASE)
   - ✅ URL intake complete
   - ✅ Source capture complete (640 words, Firecrawl)
   - ✅ Enrichment complete (6,159 tokens, LOW confidence)
   - ⏳ Evaluation pending

3. `ycombinator_com_02aab67b` (YC Airbnb profile)
   - ✅ URL intake complete
   - ⏳ Source capture pending

---

## 💰 Cost Tracking (Estimated)

**Per Company (End-to-End):**
- URL Intake: $0
- Source Capture: $0.04 (or free)
- Data Enrichment: $0.02
- SV Evaluation: $0.04
- Master List Update: $0
- Generate Profile: $0
- **Total:** ~$0.10 per company

**Monthly Estimates:**
- 10 companies: ~$1
- 100 companies: ~$10
- 500 companies: ~$50

---

## 🎯 Next Steps

1. **Build Workflow 3 (Data Enrichment)** - Use gpt-4o-mini for structured extraction
2. **Test Workflow 3** - With example.com data
3. **Build Workflow 4 (SV Evaluation)** - Use gpt-4o for reasoning
4. **Build Workflows 5-6** - No LLM calls, simpler
5. **Build Umbrella Orchestrator** - Tie everything together
6. **End-to-End Test** - Process a real YC company
7. **Self-Anneal** - Fix any issues discovered during testing

---

## 🔧 Self-Annealing Log

**Issues Fixed:**
1. ✅ Unicode encoding error in test_setup.py (Windows console) → Fixed with ASCII characters
2. ✅ Timestamp parsing issue in checkpointing → Fixed ISO format handling
3. ✅ Unused import warning → Removed unused `re` import
4. ✅ **"Lack of Clarity" Issue (CRITICAL FIX - 2025-12-29)**
   - **Problem:** All evaluations returning "lack of clarity" with scores of 1-2/5
   - **Root Cause:** Shallow data capture (homepage only) + over-conservative enrichment
   - **Solution:** Hybrid Approach (Option 3)
     - Multi-page scraping: Homepage + 2 key pages (about/pricing/product)
     - Upgraded enrichment model: gpt-4o-mini → gpt-4o
     - Relaxed inference constraints: Allow reasonable inference from context
     - Reduced UNKNOWN usage threshold
   - **Results:**
     - Stripe test: 3257 words → 10683 words (3x more content)
     - Confidence: LOW → HIGH
     - Problem clarity score: 1/5 → 5/5
     - All key fields populated with inferred data
   - **Cost Impact:** ~$0.15-0.20 per company (worth it for quality)

5. ✅ **Imbalanced Scoring Issue (CRITICAL FIX - 2025-12-29)**
   - **Problem:** Companies with mixed scores [5,5,1,1,5] getting high overall scores (3.4/5.0)
   - **Root Cause:** Simple average calculation didn't account for critical weaknesses
   - **Solution:** Implemented balanced scoring logic
     - Critical failure check: Cap at 2.5 if ANY score < 2
     - Majority strength check: Cap at 3.0 if fewer than 3 scores ≥ 3
     - Variance penalty: Reduce score up to 0.5 for high imbalance
   - **Results:**
     - Stripe test scores: [5,1,5,1,5] → Overall 2.5 (was 3.4)
     - Action changed: "monitor" → "reject" (more accurate)
     - High variance properly penalized
   - **Example Cases:**
     - `[5,5,1,1,5]` → 2.5 (capped due to critical failures)
     - `[3,3,2,2,2]` → 2.4 (only 2 strong scores)
     - `[4,4,4,3,3]` → 3.6 (balanced, no penalty)
     - `[5,5,5,5,2]` → 2.5 (one critical failure caps score)

6. ✅ **Google Doc Formatting Enhancement (2025-12-29)**
   - **Problem:** Google Docs contained markdown syntax (asterisks, hashtags) instead of clean formatting
   - **Root Cause:** Markdown text was directly inserted without conversion to Google Docs formatting
   - **Solution:** Rewrote `create_google_doc()` function with Google Docs API formatting
     - Title styling (centered, TITLE style)
     - Heading styles (HEADING_1, HEADING_2)
     - Bold labels for metadata fields
     - Clean bullet points (•) instead of markdown dashes
     - Proper paragraph spacing
     - No markdown syntax in final document
   - **Results:**
     - Professional, client-ready documents
     - Clean formatting without asterisks or hashtags
     - Emoji indicators preserved (🟢🟡🟠🔴)
     - Same structure as markdown, but properly formatted
   - **Test:** [Stripe Profile](https://docs.google.com/document/d/1SDSZK-Q1nhfSnjO24cEcblc4_1G7b_0-FdLzGsxBuvU/edit)

7. ✅ **Pipeline Workflow Order Fix (2025-12-29)**
   - **Problem:** Master List Update ran before Google Doc generation, so spreadsheet didn't include doc URL
   - **Root Cause:** Incorrect workflow sequence in pipeline orchestrator
   - **Solution:** Reordered workflows to ensure doc generation happens first
     - OLD order: Evaluation → Master List → Doc Generation
     - NEW order: Evaluation → Doc Generation → Master List
   - **Results:**
     - Google Doc URL now properly included in spreadsheet "Profile Doc" column
     - Single source of truth for all prospect data
     - Complete end-to-end pipeline execution
   - **Test:** [Notion Pipeline Run](https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID/edit) - Row 6 with doc URL

**Learnings:**
- Checkpointing is critical for token efficiency
- Firecrawl API works well for structured content
- Windows requires ASCII-safe console output
- ISO timestamp format needs consistent handling
- **Homepage-only scraping insufficient for B2B SaaS evaluation**
- **gpt-4o-mini too conservative for enrichment - causes data loss**
- **Multi-page strategy essential for SV criteria evaluation**

---

## 📝 Notes

- All workflows follow the Hybrid Approach 3 (Incremental Checkpointing)
- Token efficiency is prioritized throughout
- System is designed for autonomous operation
- Self-annealing is built into the process
