#!/usr/bin/env python3
"""Canadian Market Research - Execution Layer"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import openai

load_dotenv()

def load_data(prospect_id):
    """Load prospect profile and evaluation data."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))

    with open(tmp_dir / prospect_id / 'prospect_profile.json', 'r') as f:
        profile = json.load(f)

    with open(tmp_dir / prospect_id / 'sv_evaluation_record.json', 'r') as f:
        evaluation = json.load(f)

    return profile, evaluation

def create_research_prompt(profile, evaluation):
    """Create comprehensive Canadian market research prompt."""

    company_name = profile.get('company_name', 'Unknown')
    description = profile.get('description_one_sentence', 'UNKNOWN')
    problem = profile.get('problem_statement', 'UNKNOWN')
    target_customer = profile.get('primary_customer', 'UNKNOWN')
    revenue_model = profile.get('revenue_model', 'UNKNOWN')
    canada_score = evaluation.get('scores', {}).get('canada_market_fit', {}).get('score', 0)
    canada_rationale = evaluation.get('scores', {}).get('canada_market_fit', {}).get('rationale', '')

    prompt = f"""You are a Canadian market research analyst conducting deep market analysis for a venture capital firm evaluating {company_name}.

## COMPANY OVERVIEW
**Name:** {company_name}
**Description:** {description}
**Problem Addressed:** {problem}
**Target Customer:** {target_customer}
**Revenue Model:** {revenue_model}
**Current Canada Market Fit Score:** {canada_score}/5
**Market Fit Notes:** {canada_rationale}

## YOUR TASK
Conduct comprehensive Canadian market research using the EXACT format below. Match structure, headings, and level of detail. Use clean formatting with NO asterisks or hashtags - only bullet points and lines. Follow the exemplar precisely.

## OUTPUT FORMAT (MANDATORY - FOLLOW THIS EXACT STRUCTURE)

═══════════════════════════════════════════════════════════════

🇨🇦 CANADIAN MARKET RESEARCH

═══════════════════════════════════════════════════════════════

1. MARKET SIZING (CANADA)
________________________________________________________________________

Total Addressable Market (TAM)

Estimated Size: [Insert $ range CAD annually]

What's included
• [List what businesses/sectors are included]
• [Focus areas or verticals]

Key assumptions
• [Number of businesses or market participants]
• [Core sectors or industries]
• [Average annual spend per customer]

________________________________________________________________________

Serviceable Addressable Market (SAM)

Estimated Size: [Insert $ range CAD annually]

What's included
• [Number of businesses with specific needs]
• [Target customer types]

Key assumptions
• [Higher annual spend range]
• [Focus on specific use cases or volume]

________________________________________________________________________

Serviceable Obtainable Market (SOM)

Estimated Size: [Insert $ range CAD annually over 3–5 years]

What's included
• [Early adopter segments]

Key assumptions
• [Realistic market share %]
• [Requirements for success]

═══════════════════════════════════════════════════════════════

2. MARKET SEGMENTATION
________________________________________________________________________

By Industry
• [Industry segment 1]
• [Industry segment 2]
• [Industry segment 3]
• [Continue for key industries]

By Company Size
• Enterprise: [Description]
• Mid-market: [Description]
• SMBs: [Description]

By Geography
• [Province/City 1]: [Why prioritize]
• [Province/City 2]: [Why prioritize]
• [Province/City 3]: [Why prioritize]

═══════════════════════════════════════════════════════════════

3. GROWTH DRIVERS & TRENDS
________________________________________________________________________

Regulatory Catalysts
• [Regulation 1 and impact]
• [Regulation 2 and impact]
• [Regulation 3 and impact]

Technology Trends
• [Tech trend 1]
• [Tech trend 2]
• [Tech trend 3]

Behavioral Shifts
• [Buyer/user behavior change 1]
• [Buyer/user behavior change 2]

Macroeconomic Factors
• [Economic trend 1]
• [Economic trend 2]

═══════════════════════════════════════════════════════════════

4. COMPETITIVE LANDSCAPE
________________________________________________________________________

Direct Competitors

[Competitor 1] — [Brief description]
• [Key strength or market position]

[Competitor 2] — [Brief description]
• [Key strength or market position]

[Competitor 3] — [Brief description]
• [Key strength or market position]

[Continue for 3-5 direct competitors]

________________________________________________________________________

Indirect Competitors
• [Alternative solution category 1]
• [Alternative solution category 2]
• [Alternative solution category 3]

Market Gaps
• [Underserved need 1]
• [Underserved need 2]
• [Underserved need 3]

═══════════════════════════════════════════════════════════════

5. REGULATORY ENVIRONMENT
________________________________________________________________________

Key Regulations
• [Regulation 1: e.g., PIPEDA]
• [Regulation 2: e.g., Provincial laws]
• [Regulation 3: e.g., Industry-specific rules]

Compliance Requirements
• [Requirement 1]
• [Requirement 2]
• [Requirement 3]

Data Residency
• [Data residency implications]
• [Cloud infrastructure requirements]

Certifications
• [Certification 1: e.g., SOC 2]
• [Certification 2: e.g., ISO 27001]
• [Additional certifications]

═══════════════════════════════════════════════════════════════

6. CUSTOMER & BUYER BEHAVIOR
________________________________________________________________________

Procurement Cycles
• Enterprise: [Timeline]
• SMB / Mid-market: [Timeline]
• [Additional context]

Decision Criteria
• [Criterion 1]
• [Criterion 2]
• [Criterion 3]
• [Criterion 4]

Buyer Influencers
• [Role 1: e.g., Compliance/risk]
• [Role 2: e.g., IT leadership]
• [Role 3: e.g., Product]
• [Role 4: e.g., Legal]

Canada-Specific Differences
• [Difference 1: e.g., Bilingual requirements]
• [Difference 2: e.g., Privacy sensitivity]
• [Difference 3: e.g., Local vendor preference]

═══════════════════════════════════════════════════════════════

7. GO-TO-MARKET STRATEGY (CANADA)
________________________________________________________________________

Entry Strategy
• [Strategy 1]
• [Strategy 2]
• [Strategy 3]

Distribution Channels
• [Channel 1]
• [Channel 2]
• [Channel 3]

Partnerships
• [Partner/organization 1]
• [Partner/organization 2]
• [Partner/organization 3]

Government Programs
• [Program 1]
• [Program 2]
• [Program 3]

═══════════════════════════════════════════════════════════════

8. CANADA-SPECIFIC RISKS
________________________________________________________________________

Market Barriers
• [Barrier 1]
• [Barrier 2]
• [Barrier 3]

Competitive Barriers
• [Barrier 1]
• [Barrier 2]
• [Barrier 3]

Operational Challenges
• [Challenge 1]
• [Challenge 2]
• [Challenge 3]

Mitigation
• [Mitigation strategy 1]
• [Mitigation strategy 2]
• [Mitigation strategy 3]

═══════════════════════════════════════════════════════════════

9. GROWTH POTENTIAL (CANADA)
________________________________________________________________________

Revenue Scenarios
• Conservative: [Year 1: $X → Year 3: $Y with brief assumption]
• Moderate: [Year 1: $X → Year 3: $Y with brief assumption]
• Optimistic: [Year 1: $X → Year 3: $Y with brief assumption]

Scaling Opportunities
• [Opportunity 1]
• [Opportunity 2]
• [Opportunity 3]

Geographic Priorities
1. [Province/City 1]
2. [Province/City 2]
3. [Province/City 3]
4. [Province/City 4]

═══════════════════════════════════════════════════════════════

10. FINAL ASSESSMENT (CANADA)
________________________________________________________________________

Overall:
[2-3 sentence synthesis of the Canadian market opportunity]

Win Conditions:
[Critical success factors specific to Canada]

Failure Risks:
[Key failure risks specific to Canada]

Confidence Level: [HIGH, MEDIUM, or LOW]

═══════════════════════════════════════════════════════════════

CRITICAL FORMATTING RULES:
- Use ═ lines for major section breaks (main sections 1-10)
- Use _ underlines for subsection headers
- NO bold asterisks - use plain text for headers and UPPERCASE for main sections
- Use • bullet points for lists
- Use plain text with colons for labels (e.g., "Estimated Size:" not "**Estimated Size:**")
- Keep it clean, scannable, and professional
- Match the structure and style exactly as shown above
"""

    return prompt

def call_openai_research(prompt):
    """Call OpenAI GPT-4.1 for market research."""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are an expert Canadian market research analyst with deep knowledge of Canadian business, regulations, competitive landscape, and market dynamics across industries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )

    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens

    return content, tokens_used

def parse_research_output(markdown_content, profile, tokens_used):
    """Parse the structured research output into JSON."""
    import re

    # Extract confidence level from the structured output
    confidence = "MEDIUM"
    confidence_match = re.search(r'Confidence Level:\s*(HIGH|MEDIUM|LOW)', markdown_content, re.IGNORECASE)
    if confidence_match:
        confidence = confidence_match.group(1).upper()

    # Extract overall assessment
    overall_match = re.search(r'overall_assessment:\s*(.+?)(?=\nwhy_this_wins)', markdown_content, re.DOTALL)
    summary = overall_match.group(1).strip() if overall_match else ""

    research_record = {
        "prospect_id": profile.get('prospect_id', ''),
        "company_name": profile.get('company_name', 'Unknown'),
        "research_date": datetime.utcnow().isoformat() + 'Z',
        "model_used": "gpt-4.1",
        "tokens_used": tokens_used,
        "structured_output": markdown_content,
        "summary": summary,
        "confidence_level": confidence,
        "metadata": {
            "model": "gpt-4.1",
            "temperature": 0.3,
            "max_tokens": 4000,
            "format": "structured_template"
        }
    }

    return research_record

def format_for_google_doc(structured_content):
    """Format the structured research for appending to Google Doc."""

    # The structured content is already in the correct format
    # Just add section header
    formatted = f"\n\n---\n\n# 9. Canadian Market Research\n\n{structured_content}\n"

    return formatted

def main(prospect_id):
    print("="*60)
    print("CANADIAN MARKET RESEARCH")
    print("="*60)
    print(f"Prospect ID: {prospect_id}\n")

    # Load data
    profile, evaluation = load_data(prospect_id)
    print(f"[OK] Loaded data for {profile.get('company_name')}")
    print(f"[INFO] Canada Market Fit Score: {evaluation.get('scores', {}).get('canada_market_fit', {}).get('score', 0)}/5")

    # Create research prompt
    prompt = create_research_prompt(profile, evaluation)
    print(f"[OK] Created research prompt")

    # Call OpenAI GPT-4.1
    print(f"[INFO] Calling OpenAI GPT-4.1 for Canadian market research...")
    try:
        structured_content, tokens_used = call_openai_research(prompt)
        print(f"[OK] Research completed successfully")
        print(f"[INFO] Tokens used: {tokens_used:,}")
    except Exception as e:
        print(f"[FAIL] OpenAI API call failed: {str(e)}")
        # Retry once
        print(f"[INFO] Retrying...")
        try:
            structured_content, tokens_used = call_openai_research(prompt)
            print(f"[OK] Research completed successfully on retry")
            print(f"[INFO] Tokens used: {tokens_used:,}")
        except Exception as e2:
            print(f"[FAIL] Retry failed: {str(e2)}")
            return 1

    # Parse into structured JSON
    research_record = parse_research_output(structured_content, profile, tokens_used)
    print(f"[OK] Parsed research output")
    print(f"[INFO] Confidence level: {research_record['confidence_level']}")

    # Save JSON
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    json_file = tmp_dir / prospect_id / 'canadian_market_research.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(research_record, f, indent=2)
    print(f"[OK] Saved research JSON to: {json_file}")

    # Save structured content for Google Doc
    formatted_md = format_for_google_doc(structured_content)
    md_file = tmp_dir / prospect_id / 'canadian_market_research.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(formatted_md)
    print(f"[OK] Saved formatted content to: {md_file}")

    # Log to annealing log
    annealing_log_path = os.getenv('ANNEALING_LOG_PATH', './.tmp/annealing_log.json')
    if os.getenv('ENABLE_ANNEALING_LOG', 'false').lower() == 'true':
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "workflow": "canadian_market_research",
                "prospect_id": prospect_id,
                "company": profile.get('company_name'),
                "model": "gpt-4.1",
                "tokens": tokens_used,
                "confidence": research_record['confidence_level']
            }

            if os.path.exists(annealing_log_path):
                with open(annealing_log_path, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)

            with open(annealing_log_path, 'w') as f:
                json.dump(logs, f, indent=2)

            print(f"[OK] Logged to annealing log")
        except Exception as e:
            print(f"[WARN] Failed to write annealing log: {str(e)}")

    print("\n" + "="*60)
    print("CANADIAN MARKET RESEARCH COMPLETE")
    print("="*60)
    print(f"Company: {profile.get('company_name')}")
    print(f"Confidence: {research_record['confidence_level']}")
    print(f"Tokens Used: {tokens_used:,}")
    print(f"Output: {md_file}")
    print("="*60 + "\n")

    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python canadian_market_research.py <prospect_id>")
        print("Example: python canadian_market_research.py figured_com_a1b2c3d4")
        sys.exit(1)

    prospect_id = sys.argv[1]
    exit_code = main(prospect_id)
    sys.exit(exit_code)
