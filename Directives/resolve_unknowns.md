# Resolve Unknowns

## Goal
Use high-intelligence AI model (OpenAI o1) to resolve UNKNOWN values and missing information in prospect profiles through deep reasoning and inference.

## When to Use
Run this workflow when:
1. Profile document contains UNKNOWN values or "Not disclosed" fields
2. Evaluation record has unknowns that need addressing
3. You want to enhance profile quality with AI-inferred insights
4. Initial scraping couldn't capture certain information

## Input
- **Required:** Prospect ID (folder in `.tmp/` containing profile and evaluation)
- **Files Used:**
  - `prospect_profile.json` - Profile with potential UNKNOWN values
  - `sv_evaluation_record.json` - Evaluation with unknowns list
  - `raw_sources/content.md` - Original scraped content (for context)

## Execution

### Standalone Mode
```bash
python Executions/resolve_unknowns.py <prospect_id>
```

### Integrated in Pipeline
The unknown resolution can be integrated into the main pipeline in two ways:

**Option 1: Automatic (after evaluation, before profile doc)**
Modify `sv_pipeline.py` to include:
```python
# After sv_evaluation.py runs
if has_unknowns(prospect_id):
    run_unknown_resolution(prospect_id)
# Then run generate_profile_doc.py
```

**Option 2: Manual (run separately after pipeline)**
```bash
# Run full pipeline first
python Executions/sv_pipeline.py <url>

# Then resolve unknowns
python Executions/resolve_unknowns.py <prospect_id>

# Regenerate profile doc with resolved data
python Executions/generate_profile_doc.py <prospect_id>
```

## How It Works

### Step 1: Detection
- Recursively scans profile JSON for "UNKNOWN" or "Not disclosed" values
- Collects unknowns list from evaluation record
- Counts total unknowns that need resolution

### Step 2: Context Building
- Extracts company context (name, URL, description, business model)
- Identifies which specific fields need resolution
- Prepares evaluation unknowns for addressing

### Step 3: High-Intelligence Model Call
- Uses OpenAI o1-mini (or o1-preview for complex cases)
- Provides deep reasoning prompt with company context
- Model uses advanced thinking to:
  - Infer values based on business model patterns
  - Apply domain knowledge about industries
  - Make reasonable estimates for market data
  - Address evaluation unknowns with research insights

### Step 4: Resolution Application
- Updates profile fields with resolved values
- Marks each resolution with confidence level (HIGH/MEDIUM/LOW)
- Adds "[AI-inferred: CONFIDENCE]" tag to differentiate from scraped data
- Stores reasoning for each resolution

### Step 5: Output
- Updates `prospect_profile.json` with resolved values
- Updates `sv_evaluation_record.json` with addressed unknowns
- Creates `unknown_resolution.json` for audit trail

## Model Selection

**Default: o1-mini**
- Faster and cheaper ($3-15 per 1M tokens)
- Excellent for most unknown resolution tasks
- Good balance of reasoning depth and cost

**Alternative: o1-preview**
- Most advanced reasoning ($15-60 per 1M tokens)
- Use for highly complex companies
- Better for novel business models

**Configure in `.env`:**
```bash
UNKNOWN_RESOLUTION_MODEL=o1-mini  # or o1-preview
```

## Output Files

### Updated Profile (`prospect_profile.json`)
Contains resolved values marked with confidence:
```json
{
  "revenue_model": "SaaS subscription [AI-inferred: HIGH]",
  "resolution_metadata": {
    "resolved_at": "2024-01-15T10:30:00",
    "model_used": "o1-mini",
    "fields_resolved": 5,
    "unknowns_addressed": 3
  }
}
```

### Resolution Record (`unknown_resolution.json`)
Audit trail with full details:
```json
{
  "resolved_at": "2024-01-15T10:30:00",
  "resolution_data": {
    "resolved_fields": {
      "revenue_model": {
        "original_value": "UNKNOWN",
        "resolved_value": "SaaS subscription",
        "confidence": "HIGH",
        "reasoning": "Company offers software platform with recurring access..."
      }
    },
    "resolved_unknowns": [...],
    "overall_improvement": {
      "fields_resolved": 5,
      "unknowns_addressed": 3,
      "confidence_level": "HIGH"
    }
  }
}
```

### Updated Profile Document
When you regenerate the profile doc (via `generate_profile_doc.py`), it will include:
- Section showing all resolved fields
- Original vs resolved values comparison
- Confidence levels and reasoning
- Addressed evaluation unknowns

## Cost Considerations

**Typical Costs per Company:**
- o1-mini: $0.10 - $0.50 per resolution
- o1-preview: $0.30 - $2.00 per resolution

**Reasoning tokens:**
- o1 models use internal "thinking" tokens (not visible in output)
- These add to total cost but provide better inference
- Typical: 5,000-20,000 reasoning tokens per company

## Quality Guidelines

**High Confidence Resolutions:**
- Based on clear business model patterns
- Standard industry knowledge
- Observable from company type

**Medium Confidence Resolutions:**
- Reasonable inference from context
- Typical for this company category
- Some assumptions made

**Low Confidence Resolutions:**
- Speculative estimates
- Limited context available
- Should be verified if actionable

## Integration with Profile Generation

The profile document generator ([generate_profile_doc.py](../Executions/generate_profile_doc.py)) automatically includes resolution data if available:

1. Checks for `unknown_resolution.json`
2. Adds "AI-Resolved Unknowns" section to both markdown and Google Doc
3. Shows before/after comparison with confidence levels
4. Preserves original UNKNOWN values for transparency

## Error Handling

**If resolution fails:**
- Original profile remains unchanged
- Error logged with details
- Can retry with different model or prompt

**If no unknowns found:**
- Script exits gracefully
- No changes made
- Message: "No unknowns found - profile is complete!"

## Best Practices

1. **Run after initial pipeline**: Let standard enrichment complete first
2. **Review high-stakes fields**: Manually verify LOW confidence resolutions for critical decisions
3. **Cost management**: Use o1-mini by default, o1-preview only for complex cases
4. **Batch processing**: For multiple companies, consider cost vs. value tradeoff
5. **Transparency**: Resolution metadata clearly marks AI-inferred vs. scraped data

## Example Workflow

```bash
# 1. Run standard pipeline
python Executions/sv_pipeline.py https://example.com

# 2. Check for unknowns (inspect profile)
cat .tmp/example_com_*/prospect_profile.json | grep UNKNOWN

# 3. If unknowns exist, resolve them
python Executions/resolve_unknowns.py example_com_a1b2c3d4

# 4. Regenerate profile document with resolutions
python Executions/generate_profile_doc.py example_com_a1b2c3d4
```

## Success Metrics

**Good Resolution:**
- 70%+ of unknowns resolved with MEDIUM+ confidence
- Reasoning is specific and actionable
- Aligns with observable company characteristics

**Poor Resolution:**
- Mostly LOW confidence guesses
- Generic or vague reasoning
- Contradicts known information

## Notes

- **Not a replacement for research**: AI inference complements but doesn't replace manual diligence
- **Use for prioritization**: Helps determine which companies warrant deeper investigation
- **Iterative improvement**: System can be re-run as models improve or new context emerges
- **Audit trail preserved**: Original UNKNOWN values and resolution reasoning always accessible
