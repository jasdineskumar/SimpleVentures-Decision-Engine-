# Canadian Market Research - Setup & Usage Guide

## Overview

The SV pipeline now includes **optional** deep Canadian market research powered by OpenAI's GPT-4.1 model. This feature provides comprehensive analysis of market opportunities in Canada for each prospect.

## Features

✓ **Optional Toggle** - Enable/disable research in the main pipeline
✓ **Cost Optimization** - Only run expensive research on promising prospects
✓ **Standalone Updates** - Add research to existing profiles without re-running entire pipeline
✓ **Clean Formatting** - Professional output with underlined headers and section breaks
✓ **Comprehensive Analysis** - 10 sections covering market sizing, competition, regulations, GTM strategy, and more

## Configuration

### Enable/Disable Research in Pipeline

Edit `.env` file:

```bash
# Enable research (runs automatically in pipeline)
ENABLE_CANADIAN_RESEARCH=true

# Disable research (run separately later on promising prospects only)
ENABLE_CANADIAN_RESEARCH=false
```

### Model Configuration

```bash
CANADIAN_RESEARCH_MODEL=gpt-4.1
```

## Usage

### Option 1: Run Research in Pipeline (Automatic)

```bash
# Set in .env
ENABLE_CANADIAN_RESEARCH=true

# Run pipeline normally
python Executions/sv_pipeline.py https://example.com
```

Research runs automatically between SV Evaluation and Profile Document generation.

### Option 2: Run Research Separately (Manual)

```bash
# 1. Initial pipeline run (fast, no research)
ENABLE_CANADIAN_RESEARCH=false
python Executions/sv_pipeline.py https://example.com

# 2. Review initial profile and identify promising prospects

# 3. Add research to specific prospects
python Executions/update_with_research.py example_com_abc123
```

This approach:
- Screens many prospects quickly (no research cost)
- Only runs expensive research ($0.30-0.50 per company) on high-potential candidates
- Updates existing Google Docs with new Section 9: Canadian Market Research

### Option 3: Run Research Only

```bash
# Just generate research (doesn't update Google Doc)
python Executions/canadian_market_research.py <prospect_id>
```

## Research Output Structure

### File Outputs

```
.tmp/{prospect_id}/
├── canadian_market_research.json    # Structured JSON with metadata
└── canadian_market_research.md      # Formatted markdown for Google Doc
```

### Research Sections

1. **Market Sizing (Canada)**
   - TAM, SAM, SOM with assumptions

2. **Market Segmentation**
   - By industry, company size, geography

3. **Growth Drivers & Trends**
   - Regulatory catalysts, technology trends, behavioral shifts, macroeconomic factors

4. **Competitive Landscape**
   - Direct competitors, indirect competitors, market gaps

5. **Regulatory Environment**
   - Key regulations, compliance requirements, data residency, certifications

6. **Customer & Buyer Behavior**
   - Procurement cycles, decision criteria, buyer influencers, Canada-specific differences

7. **Go-To-Market Strategy (Canada)**
   - Entry strategy, distribution channels, partnerships, government programs

8. **Canada-Specific Risks**
   - Market barriers, competitive barriers, operational challenges, mitigation

9. **Growth Potential (Canada)**
   - Revenue scenarios (conservative/moderate/optimistic), scaling opportunities, geographic priorities

10. **Final Assessment (Canada)**
    - Overall assessment, win conditions, failure risks, confidence level

### Formatting

The research uses clean, professional formatting:

```
═══════════════════════════════════════════════════════════════
🇨🇦 CANADIAN MARKET RESEARCH
═══════════════════════════════════════════════════════════════

1. MARKET SIZING (CANADA)
________________________________________________________________________

Total Addressable Market (TAM)

Estimated Size: $800M–$1.2B CAD annually

What's included
• All Canadian businesses requiring digital identity verification
• Financial services, fintech, insurance, telecom...
```

**Key formatting rules:**
- `═` lines for major section breaks
- `_` underlines for subsection headers
- NO bold asterisks - plain text for headers
- UPPERCASE for main sections
- `•` bullet points for lists
- Plain text with colons for labels

## Cost Estimation

**Per Company:**
- Model: GPT-4.1
- Average tokens: 3,500-4,500
- Estimated cost: $0.30-0.50 per company

**Cost Optimization Strategy:**

1. **Fast Initial Screening** (ENABLE_CANADIAN_RESEARCH=false)
   - Run pipeline on 100 prospects
   - Cost: ~$1-2 per prospect (no research)
   - Total: $100-200

2. **Deep Research on Winners** (update_with_research.py)
   - Select 10 promising prospects
   - Run Canadian research only on these 10
   - Cost: $3-5 for research only
   - Total: $30-50

**Total for 100 prospects with 10 deep dives: $130-250**

Compare to running research on all 100: $130-250 + $30-50 = $160-300

## Workflow Integration

### Main Pipeline with Research Enabled

```
1. URL Intake
2. Source Capture
3. Data Enrichment
4. SV Evaluation
5. Canadian Market Research ← OPTIONAL
6. Generate Profile Document (includes research)
7. Master List Update
```

### Separate Research Update

```
1. Run canadian_market_research.py
2. Regenerate profile document
3. Google Doc automatically updated
```

## Examples

### Example 1: Screen Many, Research Few

```bash
# Screen 50 companies quickly
export ENABLE_CANADIAN_RESEARCH=false

for url in $(cat prospect_urls.txt); do
    python Executions/sv_pipeline.py $url
done

# Review all 50 profiles, identify 5 winners
# Add research to winners only
python Executions/update_with_research.py prospect_1_id
python Executions/update_with_research.py prospect_2_id
python Executions/update_with_research.py prospect_3_id
python Executions/update_with_research.py prospect_4_id
python Executions/update_with_research.py prospect_5_id
```

### Example 2: Always Include Research

```bash
# Set once in .env
ENABLE_CANADIAN_RESEARCH=true

# Every pipeline run includes research
python Executions/sv_pipeline.py https://example1.com
python Executions/sv_pipeline.py https://example2.com
```

## Troubleshooting

### Research Not Running

Check `.env`:
```bash
ENABLE_CANADIAN_RESEARCH=true  # Must be 'true', not 'True' or '1'
```

### Research Running Twice

If you run `update_with_research.py` on a prospect that already has research, it will regenerate and replace the existing research.

### Google Doc Not Updating

The `update_with_research.py` script creates a **new** Google Doc with updated research. The old Doc URL is replaced in `google_doc_metadata.json`.

## Files Modified

**New Files:**
- `Executions/canadian_market_research.py` - Research execution script
- `Executions/update_with_research.py` - Standalone update script
- `Directives/canadian_market_research.md` - Research directive
- `Directives/update_with_research.md` - Update directive

**Modified Files:**
- `.env` - Added `ENABLE_CANADIAN_RESEARCH` toggle
- `Executions/sv_pipeline.py` - Added optional research step
- `Executions/generate_profile_doc.py` - Added research section rendering
- `Directives/umbrella_sv_pipeline.md` - Updated workflow documentation

## Summary

The Canadian market research feature is:
- **Optional** - Toggle on/off as needed
- **Cost-effective** - Run only on promising prospects
- **Flexible** - Add to existing profiles anytime
- **Comprehensive** - 10 sections of deep market analysis
- **Professional** - Clean formatting with underlines and section breaks
- **Powered by GPT-4.1** - OpenAI's latest model with 1M token context

Perfect for screening many prospects quickly, then diving deep on winners! 🇨🇦
