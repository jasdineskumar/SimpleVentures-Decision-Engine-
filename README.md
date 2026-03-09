# SV Pipeline

Automated deal flow analysis system for Simple Ventures. Evaluates early-stage companies by scraping their websites, extracting structured data with LLMs, scoring them against venture studio criteria, and generating professional Google Doc profiles and spreadsheet tracking.

**Cost:** ~$0.03–0.11 per company evaluation.

---

## How It Works

The system uses a 3-layer architecture:

```
Layer 1: Directives/     — What to do (SOPs in Markdown)
Layer 2: You (LLM)       — Decision making & orchestration
Layer 3: Executions/     — Deterministic Python scripts that do the work
```

### Pipeline Steps

```
URL Input
  → url_intake.py          Normalize & canonicalize
  → source_capture.py      Scrape website content
  → data_enrichment.py     Extract structured data (Claude)
  → sv_evaluation.py       Score against 5 SV criteria (Claude)
  → canadian_market_research.py  (optional) Deep market analysis
  → generate_profile_doc.py      Create Google Doc profile
  → master_list_update.py        Add row to Master Prospect List
```

### Evaluation Criteria (5 dimensions, scored 0–5)

1. **Problem & Buyer Clarity** — Clear problem with identifiable buyer?
2. **PMF Signal** — Evidence of product-market fit?
3. **MVP Speed** — Can MVP be built in 3–6 months?
4. **Differentiation Vector** — Defensible competitive wedge?
5. **Venture Studio Fit** — Scalable, outsourcable, capital-light?

**Outputs:** `PASS / WATCH / INVESTIGATE / PRIORITIZE`

---

## Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API key
- Google Cloud account (for Sheets + Docs)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your API keys

# Verify everything works
python Executions/test_setup.py
```

See [docs/SETUP.md](docs/SETUP.md) for the full setup guide including Google Sheets API configuration.

### Run the Pipeline

```bash
# Evaluate a single company
python Executions/sv_pipeline.py https://example.com

# Detect whether a URL is a directory or single company
python Executions/detect_link_type.py <url>

# Batch: scrape a YC cohort
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 50

# Batch: process scraped companies
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/*/companies.json --parallel 3
```

See [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for a full command cheat sheet.

---

## Directory Structure

```
sv-workflow/
├── README.md                      # This file
├── CLAUDE.md                      # AI orchestration instructions
├── .env.template                  # Environment variable template
├── requirements.txt               # Python dependencies
│
├── Directives/                    # Layer 1: SOPs & workflow instructions
│   ├── SV_SOP.md                  # Core evaluation philosophy
│   ├── umbrella_sv_pipeline.md    # End-to-end pipeline orchestration
│   ├── url_intake.md
│   ├── source_capture.md
│   ├── data_enrichment.md
│   ├── sv_evaluation.md
│   ├── canadian_market_research.md
│   ├── generate_profile_doc.md
│   ├── master_list_update.md
│   ├── batch_directory_scrape.md
│   ├── batch_sv_pipeline.md
│   └── templates/
│       └── SV_Profile_Template.md
│
├── Executions/                    # Layer 3: Python scripts
│   ├── sv_pipeline.py             # Single-company pipeline
│   ├── batch_sv_pipeline.py       # Batch orchestrator
│   ├── pipeline_runner.py         # Programmatic runner (used by cloud API)
│   ├── url_intake.py
│   ├── source_capture.py
│   ├── data_enrichment.py
│   ├── sv_evaluation.py
│   ├── canadian_market_research.py
│   ├── generate_profile_doc.py
│   ├── master_list_update.py
│   ├── resolve_unknowns.py
│   ├── update_with_research.py
│   ├── batch_directory_scrape.py
│   ├── detect_link_type.py
│   ├── google_auth_cloud.py       # Cloud-compatible Google auth
│   ├── jobs_sheet_manager.py      # Job history in Google Sheets
│   ├── modal_sv_api.py            # Modal serverless backend
│   └── test_setup.py              # Credential & connectivity check
│
├── frontend_api_routes/           # Next.js API proxy routes (security layer)
│   ├── client-api.ts
│   ├── submit.ts
│   ├── list/route.ts
│   └── [id]/
│       ├── route.ts
│       └── status/route.ts
│
├── ui inspiration/                # Reference PDFs for Lovable.ai frontend
│
├── docs/                          # All documentation
│   ├── SETUP.md                   # Initial setup guide
│   ├── QUICK_REFERENCE.md         # Command cheat sheet
│   ├── DEPLOYMENT_GUIDE.md        # Cloud deployment (Modal + Vercel)
│   ├── BATCH_WORKFLOW_GUIDE.md    # Batch processing guide
│   ├── CANADIAN_RESEARCH_SETUP.md # Optional market research setup
│   ├── SECURITY_FIXES.md          # Security architecture notes
│   ├── LOVABLE_INTEGRATION_GUIDE.md # Frontend generation with Lovable.ai
│   ├── IMPLEMENTATION.md          # What was built & why
│   └── PROGRESS.md                # Build log & learnings
│
└── .tmp/                          # Intermediate files (gitignored)
    └── {prospect_id}/
        ├── canonical_url.json
        ├── raw_sources/
        ├── prospect_profile.json
        ├── sv_evaluation_record.json
        ├── sv_profile.md
        └── google_doc_metadata.json
```

---

## Cloud Deployment

The pipeline can run as a serverless API on [Modal](https://modal.com) with a [Next.js](https://nextjs.org) frontend on Vercel.

```
Browser → Next.js API Routes → Modal Backend → Google Sheets
          (no API keys)         (async jobs)    (permanent store)
```

Key design decisions:
- **Async job pattern** — Submit returns immediately; poll for status. Avoids Modal's 150s HTTP timeout.
- **Google Sheets as source of truth** — Jobs tab persists permanently, survives Modal Dict resets.
- **Server-side API keys** — Next.js proxy routes keep credentials off the client.

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for the full step-by-step guide.

---

## Cost Estimates

| Scale | Cost/month |
|-------|-----------|
| 10 companies | ~$0.30–$1 |
| 100 companies | ~$3–$11 |
| 500 companies | ~$15–$55 |

Optional Canadian market research (GPT-4.1) adds ~$0.30–$0.50 per company.

---

## Documentation Index

| Doc | Description |
|-----|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Prerequisites, API keys, Google Sheets setup |
| [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | All commands at a glance |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Modal + Vercel cloud deployment |
| [docs/BATCH_WORKFLOW_GUIDE.md](docs/BATCH_WORKFLOW_GUIDE.md) | Batch processing patterns |
| [docs/CANADIAN_RESEARCH_SETUP.md](docs/CANADIAN_RESEARCH_SETUP.md) | Optional market research |
| [docs/SECURITY_FIXES.md](docs/SECURITY_FIXES.md) | Security architecture |
| [docs/LOVABLE_INTEGRATION_GUIDE.md](docs/LOVABLE_INTEGRATION_GUIDE.md) | Frontend with Lovable.ai |
| [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) | Full implementation summary |
| [CLAUDE.md](CLAUDE.md) | AI orchestration instructions (3-layer architecture) |
| [Directives/SV_SOP.md](Directives/SV_SOP.md) | Core evaluation SOP |

---

## Troubleshooting

**`ModuleNotFoundError`** — Run `pip install -r requirements.txt`

**Google Sheets permission denied** — Share your sheet with the service account email from `credentials.json`

**Scores all returning low (1–2/5)** — Check that `source_capture.py` is scraping multiple pages, not just the homepage.

**Batch processing failed halfway** — Resume with `--resume` flag: `python Executions/batch_sv_pipeline.py companies.json --resume`

**Cloud: Jobs stuck in "queued"** — Check Modal logs: `modal app logs sv-pipeline-api --follow`
