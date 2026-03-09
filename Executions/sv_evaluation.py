#!/usr/bin/env python3
"""
SV Evaluation - Execution Layer

Applies SV criteria to Prospect Profile and generates scored evaluation.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def load_prospect_profile(prospect_id: str) -> dict:
    """Load Prospect Profile from enrichment workflow."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    profile_file = tmp_dir / prospect_id / 'prospect_profile.json'

    if not profile_file.exists():
        raise FileNotFoundError(f"Prospect Profile not found: {profile_file}")

    with open(profile_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_existing_output(prospect_id: str, max_age_hours: int = 24) -> tuple[bool, dict]:
    """Check if evaluation already exists (checkpointing)."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    eval_file = tmp_dir / prospect_id / 'sv_evaluation_record.json'

    if not eval_file.exists():
        return False, {}

    try:
        with open(eval_file, 'r') as f:
            eval_data = json.load(f)

        evaluated_at = datetime.fromisoformat(eval_data['date_evaluated'])
        age_hours = (datetime.now() - evaluated_at).total_seconds() / 3600

        if age_hours < max_age_hours:
            return True, eval_data

        return False, eval_data

    except Exception:
        return False, {}


def create_evaluation_prompt(profile: dict) -> str:
    """Create LLM prompt for SV evaluation."""

    profile_summary = json.dumps({
        "company_name": profile.get('company_name'),
        "description": profile.get('description_one_sentence'),
        "problem_statement": profile.get('problem_statement'),
        "primary_customer": profile.get('primary_customer'),
        "primary_buyer": profile.get('primary_buyer'),
        "key_features": profile.get('key_features'),
        "revenue_model": profile.get('revenue_model'),
        "market_signals": profile.get('market_signals'),
        "product_maturity": profile.get('product_maturity'),
        "traction_signals": profile.get('traction_signals'),
    }, indent=2)

    prompt = f"""You are evaluating a startup opportunity against Simple Ventures' investment criteria.

**Prospect Profile:**
{profile_summary}

**Source Confidence:** {profile.get('enrichment_metadata', {}).get('confidence', 'UNKNOWN')}

---

**Your Task:**
Evaluate this opportunity against SV's 5 criteria. Provide scores (0-5) and concise rationales.

**SV Criteria:**

1. **Problem & Buyer Clarity (0-5)**
   - Is there a clear, specific problem being solved?
   - Is the buyer/customer clearly identified?
   - Rate: 5=Very clear, 0=Unclear

2. **MVP Speed - 3-6 months (0-5)**
   - Can an MVP be built and validated in 3-6 months?
   - Consider product complexity, technical requirements
   - Rate: 5=Very feasible, 0=Not feasible

3. **Defensible Wedge (0-5)**
   - Is there a defensible advantage? (market position, distribution, economics, network effects)
   - Rate: 5=Strong wedge, 0=No wedge

4. **Venture Studio Fit (0-5)**
   - Is this suitable for a venture studio model?
   - Can external team build it? Requires unique founder insight?
   - Rate: 5=Excellent fit, 0=Poor fit

5. **Canada Market Fit (0-5)**
   - Would this type of business model work well in the Canadian market?
   - NOT whether this specific company should move to Canada, but whether a similar venture addressing the same problem would succeed in Canada
   - Consider: market size, regulatory fit, customer demand, competitive landscape
   - Rate: 5=Strong Canadian market fit, 0=Poor Canadian market fit

---

**IMPORTANT RULES:**
- Base scores ONLY on available evidence
- Acknowledge when data is missing (mark as UNKNOWN in rationale)
- Keep rationales to 2-3 sentences
- Identify SPECIFIC risks, not generic ones
- If source confidence is LOW, evaluation confidence should be MEDIUM or LOW

**Return ONLY valid JSON with this exact structure:**
{{
  "confidence_level": "HIGH | MEDIUM | LOW",
  "scores": {{
    "problem_buyer_clarity": {{
      "score": 0-5,
      "rationale": "2-3 sentence evidence-based rationale"
    }},
    "mvp_speed": {{
      "score": 0-5,
      "rationale": "2-3 sentences"
    }},
    "defensible_wedge": {{
      "score": 0-5,
      "rationale": "2-3 sentences"
    }},
    "venture_studio_fit": {{
      "score": 0-5,
      "rationale": "2-3 sentences"
    }},
    "canada_market_fit": {{
      "score": 0-5,
      "rationale": "2-3 sentences"
    }}
  }},
  "primary_risks": [
    "Specific risk 1",
    "Specific risk 2",
    "Specific risk 3"
  ],
  "unknowns": [
    "Unknown factor 1",
    "Unknown factor 2"
  ],
  "suggested_action": "reject | monitor | outreach | deeper_diligence",
  "action_reasoning": "One sentence explaining why this action"
}}
"""
    return prompt


def call_llm_for_evaluation(prompt: str) -> tuple[bool, dict, dict]:
    """Call OpenAI LLM for evaluation."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    model = os.getenv('EVALUATION_MODEL', 'gpt-4o')

    print(f"[INFO] Calling LLM ({model}) for evaluation...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a venture analyst. Evaluate startups objectively against criteria. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()
        eval_data = json.loads(result_text)

        usage_stats = {
            "model": model,
            "tokens_total": response.usage.total_tokens
        }

        return True, eval_data, usage_stats

    except json.JSONDecodeError as e:
        print(f"[FAIL] LLM returned invalid JSON: {e}")
        return False, {}, {"error": "Invalid JSON"}

    except Exception as e:
        print(f"[FAIL] LLM error: {e}")
        return False, {}, {"error": str(e)}


def calculate_overall_score(scores: dict) -> float:
    """
    Calculate overall score with balanced evaluation logic.

    Rules:
    - All scores must be ≥2 (no critical failures)
    - At least 3 out of 5 scores must be ≥3 (majority strength)
    - Apply penalty for high variance (imbalanced scores)
    - Cap at 2.5/5.0 if critical failure exists
    - Cap at 3.0/5.0 if not enough strong categories
    """
    score_values = [
        scores['problem_buyer_clarity']['score'],
        scores['mvp_speed']['score'],
        scores['defensible_wedge']['score'],
        scores['venture_studio_fit']['score'],
        scores['canada_market_fit']['score']
    ]

    # Calculate base average
    avg_score = sum(score_values) / len(score_values)

    # Check for critical failures (any score < 2)
    critical_failures = [s for s in score_values if s < 2]
    if critical_failures:
        # Cap at 2.5 if there are critical weaknesses
        return min(round(avg_score, 2), 2.5)

    # Check for majority strength (at least 3 scores ≥ 3)
    strong_scores = [s for s in score_values if s >= 3]
    if len(strong_scores) < 3:
        # Cap at 3.0 if not enough strong categories
        return min(round(avg_score, 2), 3.0)

    # Calculate variance penalty for imbalanced scores
    mean = sum(score_values) / len(score_values)
    variance = sum((s - mean) ** 2 for s in score_values) / len(score_values)

    # Apply penalty: high variance (>2.0) reduces score by up to 0.5 points
    if variance > 2.0:
        penalty = min(0.5, (variance - 2.0) * 0.2)
        return round(avg_score - penalty, 2)

    return round(avg_score, 2)


def save_output(prospect_id: str, eval_data: dict, usage_stats: dict):
    """Save SV Evaluation Record."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    eval_file = tmp_dir / prospect_id / 'sv_evaluation_record.json'

    # Add metadata
    eval_data['prospect_id'] = prospect_id
    eval_data['date_evaluated'] = datetime.now().isoformat()
    eval_data['overall_score'] = calculate_overall_score(eval_data['scores'])
    eval_data['evaluation_metadata'] = {
        "model_used": usage_stats.get('model', 'unknown'),
        "tokens_used": usage_stats.get('tokens_total', 0)
    }

    with open(eval_file, 'w', encoding='utf-8') as f:
        json.dump(eval_data, f, indent=2)

    print(f"[OK] Saved SV Evaluation Record to: {eval_file}")


def main(prospect_id: str) -> int:
    """Main workflow: SV Evaluation."""
    print("="*60)
    print("SV EVALUATION")
    print("="*60)
    print(f"Prospect ID: {prospect_id}\n")

    # Step 1: Check if already evaluated
    exists, existing_eval = check_existing_output(prospect_id)
    if exists:
        print(f"[INFO] Already evaluated (age < 24h), skipping")
        print(f"\n" + "="*60)
        print("SV EVALUATION COMPLETE (FROM CACHE)")
        print("="*60)
        print(f"Overall Score: {existing_eval.get('overall_score', 'N/A')}/5.0")
        print(f"Confidence: {existing_eval.get('confidence_level', 'N/A')}")
        print(f"Action: {existing_eval.get('suggested_action', 'N/A')}")
        print("="*60 + "\n")
        return 0

    # Step 2: Load Prospect Profile
    try:
        profile = load_prospect_profile(prospect_id)
        print(f"[OK] Loaded Prospect Profile")
        print(f"Company: {profile.get('company_name', 'N/A')}")
        print(f"Profile Confidence: {profile.get('enrichment_metadata', {}).get('confidence', 'N/A')}")
    except Exception as e:
        print(f"[FAIL] Could not load profile: {e}")
        return 1

    # Step 3: Create evaluation prompt
    prompt = create_evaluation_prompt(profile)
    print(f"[OK] Created evaluation prompt")

    # Step 4: Call LLM
    success, eval_data, usage_stats = call_llm_for_evaluation(prompt)

    if not success:
        print(f"[FAIL] Evaluation failed: {usage_stats.get('error', 'Unknown')}")
        return 1

    print(f"[OK] Evaluation successful")
    print(f"Tokens used: {usage_stats.get('tokens_total', 0)}")

    # Step 5: Save output
    save_output(prospect_id, eval_data, usage_stats)

    # Step 6: Display summary
    overall_score = eval_data.get('overall_score', 0)
    print("\n" + "="*60)
    print("SV EVALUATION COMPLETE")
    print("="*60)
    print(f"Overall Score: {overall_score}/5.0")
    print(f"Confidence: {eval_data.get('confidence_level', 'N/A')}")
    print(f"Suggested Action: {eval_data.get('suggested_action', 'N/A')}")
    print(f"Reasoning: {eval_data.get('action_reasoning', 'N/A')}")
    print(f"\nScores:")
    for criterion, data in eval_data.get('scores', {}).items():
        print(f"  {criterion}: {data.get('score', 'N/A')}/5")
    print(f"\nTokens Used: {usage_stats.get('tokens_total', 0)}")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sv_evaluation.py <prospect_id>")
        print("Example: python sv_evaluation.py example_com_a1b2c3d4")
        sys.exit(1)

    prospect_id = sys.argv[1]
    exit_code = main(prospect_id)
    sys.exit(exit_code)
