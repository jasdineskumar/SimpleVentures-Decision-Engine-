# Canadian Market Research

## Goal
Conduct deep Canadian market research to assess market fit, competitive landscape, regulatory considerations, and growth potential for the prospect company in the Canadian market.

## Inputs
- `prospect_profile.json` - Company profile with business model, target customer, and product details
- `sv_evaluation_record.json` - SV evaluation with Canada market fit score

## Processing
1. Load prospect profile and evaluation data
2. Create comprehensive research prompt covering:
   - **Market Landscape:** TAM/SAM/SOM sizing for Canada, key market segments, growth trends
   - **Competitive Analysis:** Direct/indirect competitors operating in Canada, market positioning opportunities
   - **Regulatory Environment:** Industry-specific regulations, compliance requirements, licensing needs
   - **Customer Landscape:** Target customer demographics in Canada, regional variations, buyer behavior
   - **Go-to-Market Strategy:** Entry strategies, distribution channels, partnership opportunities
   - **Risk Factors:** Canada-specific challenges, market barriers, cultural considerations
   - **Growth Potential:** Revenue projections, scaling opportunities, geographic expansion priorities
3. Call OpenAI GPT-4.1 for deep analysis (using extended context window)
4. Format research as structured markdown
5. Save as `.tmp/{prospect_id}/canadian_market_research.json` and `.tmp/{prospect_id}/canadian_market_research.md`

## Model Configuration
- **Model:** `gpt-4.1` (OpenAI's latest, 1M token context)
- **Temperature:** 0.3 (balanced creativity with factual accuracy)
- **Max Tokens:** 4000 (comprehensive analysis)

## Output Structure
The research must be formatted using this exact template structure. Populate fields only - no prose outside fields.

```yaml
CANADIAN_MARKET_RESEARCH

MARKET_SIZING
tam:
tam_assumptions:
sam:
sam_assumptions:
som:
som_assumptions:

MARKET_SEGMENTATION
by_industry: []
by_company_size: []
by_geography: []

GROWTH_DRIVERS_AND_TRENDS
regulatory_catalysts: []
technology_trends: []
behavioral_shifts: []
macroeconomic_factors: []

COMPETITIVE_LANDSCAPE
direct_competitors:
  - name:
    position:
    differentiation:
indirect_competitors:
  - category:
    description:
market_gaps: []

REGULATORY_ENVIRONMENT
key_regulations: []
compliance_requirements: []
data_residency_implications:
certifications_required: []

CUSTOMER_AND_BUYER_BEHAVIOR
procurement_cycles:
decision_criteria: []
buyer_influencers: []
canada_specific_differences: []

GO_TO_MARKET_STRATEGY_CANADA
entry_strategies: []
distribution_channels: []
partnership_opportunities: []
government_programs: []

CANADA_SPECIFIC_RISKS
market_barriers: []
competitive_barriers: []
operational_challenges: []
mitigation_strategies: []

GROWTH_POTENTIAL_CANADA
revenue_projection_scenarios:
  conservative:
  moderate:
  optimistic:
scaling_opportunities:
geographic_priorities:

CANADIAN_MARKET_FINAL_ASSESSMENT
overall_assessment:
why_this_wins_or_fails_in_canada:
confidence_level:
research_completion_date:
research_model_used:
```

## Execution
```bash
python Executions/canadian_market_research.py <prospect_id>
```

## Output
- **JSON:** `.tmp/{prospect_id}/canadian_market_research.json`
- **Markdown:** `.tmp/{prospect_id}/canadian_market_research.md` (formatted for Google Doc append)
- **Tokens Used:** ~3000-4000 tokens

## Error Handling
- If API call fails, retry once with exponential backoff
- If prospect_profile.json missing, exit with error
- Log all API usage to annealing log for cost tracking

## Integration
This workflow runs after SV Evaluation (workflow 4) and before Generate Profile Document (workflow 5). The markdown output is automatically appended to the Google Doc as a new section titled "Canadian Market Research."
