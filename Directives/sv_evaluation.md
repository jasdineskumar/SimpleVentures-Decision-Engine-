# SV Evaluation

## Directive Layer: What This Workflow Does

This workflow applies Simple Ventures' 5 evaluation criteria to a Prospect Profile and generates scored assessments with rationales.

---

## Goal

Evaluate a company opportunity against SV criteria and produce a structured evaluation record with scores, rationales, risks, and recommendations.

---

## Inputs

**Required:** `.tmp/{prospect_id}/prospect_profile.json`

Must contain structured company data from enrichment workflow.

---

## SV Evaluation Criteria (from SV_SOP.md)

1. **Problem & Buyer Clarity** - Is there a clear problem and buyer?
2. **MVP Speed (3-6 months)** - Can an MVP be built and validated quickly?
3. **Defensible Wedge** - Is there a defensible advantage (market, distribution, economics)?
4. **Venture Studio Fit** - Is this suitable for a venture studio model?
5. **Canada Market Fit** - Would this type of business model/idea work well in the Canadian market? (Not whether this specific company should move to Canada, but whether a similar venture addressing the same problem would succeed in Canada)

---

## Processing Steps

1. **Load Prospect Profile**
   - Read enriched profile JSON
   - Validate structure

2. **Prepare LLM Prompt**
   - Include profile data
   - Include SV criteria definitions
   - Request structured scoring (0-5 scale)
   - Request concise rationales

3. **Call LLM (gpt-4o)**
   - Use reasoning model for evaluation
   - Apply SV criteria systematically
   - Generate scores with evidence-based rationales
   - Identify risks and unknowns
   - Suggest next action

4. **Validate Output**
   - Check all 5 scores present (0-5 range)
   - Ensure rationales are concise
   - Validate confidence level

5. **Save Evaluation Record**
   - Save as `.tmp/{prospect_id}/sv_evaluation_record.json`

---

## SV Evaluation Record JSON Schema

```json
{
  "prospect_id": "string",
  "date_evaluated": "ISO 8601 datetime",
  "confidence_level": "HIGH | MEDIUM | LOW",
  "scores": {
    "problem_buyer_clarity": {
      "score": 0-5,
      "rationale": "string (concise, evidence-based)"
    },
    "mvp_speed": {
      "score": 0-5,
      "rationale": "string"
    },
    "defensible_wedge": {
      "score": 0-5,
      "rationale": "string"
    },
    "venture_studio_fit": {
      "score": 0-5,
      "rationale": "string"
    },
    "canada_market_fit": {
      "score": 0-5,
      "rationale": "string"
    }
  },
  "overall_score": "float (balanced composite score, not simple average)",
  "primary_risks": ["string", "string"],
  "unknowns": ["string", "string"],
  "suggested_action": "reject | monitor | outreach | deeper_diligence",
  "action_reasoning": "string (one sentence)",
  "evaluation_metadata": {
    "model_used": "string",
    "tokens_used": "integer"
  }
}
```

## Overall Score Calculation Logic (BALANCED)

**The overall score is NOT a simple average.** It applies balanced evaluation logic:

1. **Critical Failure Check** - If ANY score < 2:
   - Cap overall score at 2.5/5.0
   - Rationale: A critical weakness disqualifies high rankings

2. **Majority Strength Check** - If fewer than 3 scores ≥ 3:
   - Cap overall score at 3.0/5.0
   - Rationale: Need majority of categories to be strong

3. **Variance Penalty** - If variance > 2.0 (highly imbalanced):
   - Apply penalty up to 0.5 points
   - Rationale: Inconsistent excellence is less valuable

**Example Cases:**
- `[5, 5, 1, 1, 5]` → Base avg 3.4, but has critical failures → **2.4/5.0**
- `[3, 3, 2, 2, 2]` → Base avg 2.4, only 2 strong scores → **2.4/5.0**
- `[4, 4, 4, 3, 3]` → Base avg 3.6, balanced → **3.6/5.0**
- `[5, 5, 5, 5, 2]` → Base avg 4.4, but 1 critical failure → **2.5/5.0** (capped)

---

## LLM Prompt Guidelines

**Tone:** Analytical, objective, evidence-based

**Key Instructions:**
- Score based on available evidence only
- Acknowledge data gaps (affect confidence)
- Concise rationales (2-3 sentences max)
- Identify concrete risks, not generic concerns
- Base confidence on data quality from Prospect Profile

**Scoring Scale:**
- 5 = Excellent fit / Strong evidence
- 4 = Good fit / Solid evidence
- 3 = Moderate fit / Some evidence
- 2 = Weak fit / Limited evidence
- 1 = Poor fit / Minimal evidence
- 0 = Does not fit / No evidence

---

## Execution Tool

**Script:** `Executions/sv_evaluation.py`

**Usage:**
```bash
python Executions/sv_evaluation.py <prospect_id>
```

**Returns:** Exit code 0 on success, 1 on failure

---

## Edge Cases

1. **Already Evaluated (Checkpointing)**
   - Check if `.tmp/{prospect_id}/sv_evaluation_record.json` exists
   - If exists and recent (<24h), skip evaluation
   - Otherwise, re-evaluate

2. **Low Confidence Profile**
   - If input profile has LOW confidence, evaluation confidence = LOW
   - Flag that scores are based on limited data

3. **Cost Optimization**
   - Use gpt-4o for reasoning (more expensive but necessary)
   - Cache results for 24h
   - Estimated: ~$0.02-0.05 per evaluation

---

## Success Criteria

- All 5 scores assigned (0-5)
- Rationales are concise and evidence-based
- Risks and unknowns identified
- Action recommended with reasoning
- Confidence level assigned
- Overall score calculated

---

## Self-Annealing Notes

**Common Failures:**
- Generic risks instead of specific ones → Strengthen prompt
- Long rationales → Add word limit instruction
- Scores without evidence → Require citation to profile fields

**Learnings from testing will be added here.**
