# Data Enrichment (Prospect Profile Structuring)

## Directive Layer: What This Workflow Does

This workflow uses LLM to extract structured data from scraped content and create a standardized Prospect Profile.

---

## Goal

Transform unstructured content into a structured JSON profile that can be evaluated against SV criteria.

---

## Inputs

**Required Files:**
1. `.tmp/{prospect_id}/canonical_url.json` - URL metadata
2. `.tmp/{prospect_id}/raw_sources/content.md` - Scraped content
3. `.tmp/{prospect_id}/raw_sources/metadata.json` - Scrape metadata

---

## Processing Steps

1. **Load Inputs**
   - Read canonical URL data
   - Read scraped content
   - Read metadata

2. **Prepare LLM Prompt**
   - Include content (truncate if >10,000 words)
   - Include URL for context
   - Specify exact JSON schema expected

3. **Call LLM (gpt-4o)** (UPGRADED from gpt-4o-mini)
   - Use structured output mode (JSON mode)
   - Extract explicit information first
   - Make reasonable inferences from context when explicit data missing
   - Use UNKNOWN only when truly unclear
   - Include source citations

4. **Validate Output**
   - Check JSON structure
   - Ensure required fields present
   - Validate data types

5. **Save Prospect Profile**
   - Save as `.tmp/{prospect_id}/prospect_profile.json`

---

## Prospect Profile JSON Schema

```json
{
  "prospect_id": "string",
  "company_name": "string",
  "canonical_url": "string",
  "source_type": "string",
  "description_one_sentence": "string",
  "problem_statement": "string | UNKNOWN",
  "primary_customer": "string | UNKNOWN",
  "primary_buyer": "string | UNKNOWN",
  "customer_context": "string | UNKNOWN",
  "key_features": ["string", "string", ...],
  "revenue_model": "string | UNKNOWN",
  "pricing_signals": "string | Not disclosed",
  "who_pays": "string | UNKNOWN",
  "market_signals": {
    "target_market": "string | UNKNOWN",
    "geographic_focus": "string | UNKNOWN",
    "market_size_indicators": "string | UNKNOWN"
  },
  "product_maturity": "string | UNKNOWN",
  "team_signals": {
    "founder_background": "string | UNKNOWN",
    "team_size_indicators": "string | UNKNOWN"
  },
  "traction_signals": {
    "customer_count_indicators": "string | UNKNOWN",
    "revenue_indicators": "string | UNKNOWN",
    "growth_indicators": "string | UNKNOWN"
  },
  "sources_reviewed": ["url1", "url2"],
  "key_excerpts": [
    {
      "claim": "string",
      "quote": "string",
      "source": "url"
    }
  ],
  "enrichment_metadata": {
    "enriched_at": "ISO datetime",
    "model_used": "string",
    "tokens_used": "integer",
    "confidence": "HIGH | MEDIUM | LOW"
  }
}
```

---

## LLM Prompt Guidelines

**Tone:** Neutral, factual, evidence-based

**Key Instructions (UPDATED - addresses "lack of clarity" issue):**
- Extract information explicitly stated first
- Make reasonable inferences from business context when explicit data missing
  - Example: If content mentions "farmers struggling with spreadsheets", infer the problem statement
  - Example: If pricing page mentions "per farm" pricing, infer who pays
- Use "UNKNOWN" only when truly unclear (not when inferable from context)
- Plain English (no marketing jargon)
- Cite sources for non-obvious claims
- Focus on facts that support SV evaluation criteria

**Inference Guidelines:**
- Problem statement: Can be inferred from value prop and customer pain points
- Primary buyer: Can be inferred from pricing structure and sales language
- Revenue model: Can be inferred from pricing page structure (SaaS, marketplace, etc.)
- Product maturity: Can be inferred from feature depth, customer stories, team size

---

## Execution Tool

**Script:** `Executions/data_enrichment.py`

**Usage:**
```bash
python Executions/data_enrichment.py <prospect_id>
```

**Returns:** Exit code 0 on success, 1 on failure

---

## Edge Cases

1. **Already Enriched (Checkpointing)**
   - Check if `.tmp/{prospect_id}/prospect_profile.json` exists
   - If exists and recent (<24h), skip enrichment
   - Otherwise, re-enrich

2. **Content Too Long**
   - Truncate to first 10,000 words for LLM
   - Log truncation in metadata
   - Focus on most relevant sections

3. **LLM Returns Invalid JSON**
   - Retry up to 2 times with explicit JSON schema
   - If still fails, log error and exit
   - Save error state for debugging

4. **Missing Critical Data**
   - If >50% of fields are UNKNOWN, flag as LOW confidence
   - Still save profile (downstream can decide)

5. **Cost Optimization**
   - Use gpt-4o (better inference, addresses "lack of clarity")
   - Cache results for 24h
   - **Updated cost estimate:** ~$0.05-0.08 per enrichment (higher but necessary for quality)

---

## Success Criteria

- Prospect Profile JSON created
- All required fields present
- UNKNOWN used appropriately
- No speculation or fabrication
- Confidence level assigned
- Token usage logged

---

## Self-Annealing Notes

**Common Failures:**
- LLM returns plain text instead of JSON → Add explicit JSON mode
- Speculation in output → Strengthen "UNKNOWN" instruction
- Missing fields → Add JSON schema validation

**Learnings from testing will be added here.**
