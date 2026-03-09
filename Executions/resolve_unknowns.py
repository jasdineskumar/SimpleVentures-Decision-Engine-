#!/usr/bin/env python3
"""
Resolve Unknowns - Execution Layer

Uses high-intelligence model (OpenAI o1) to fill in UNKNOWN values in prospect profiles
by performing deeper research and inference beyond what was available in scraped pages.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def load_profile_and_evaluation(prospect_id: str) -> tuple[dict, dict]:
    """Load existing prospect profile and evaluation."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    prospect_dir = tmp_dir / prospect_id

    profile_file = prospect_dir / 'prospect_profile.json'
    eval_file = prospect_dir / 'sv_evaluation_record.json'

    if not profile_file.exists():
        raise FileNotFoundError(f"Profile not found: {profile_file}")

    with open(profile_file, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    evaluation = {}
    if eval_file.exists():
        with open(eval_file, 'r', encoding='utf-8') as f:
            evaluation = json.load(f)

    return profile, evaluation


def detect_unknowns(profile: dict, evaluation: dict) -> dict:
    """
    Detect all UNKNOWN values and fields that need resolution.

    Returns: Dict with categories of unknowns found
    """
    unknowns = {
        'profile_fields': [],
        'evaluation_unknowns': evaluation.get('unknowns', []),
        'count': 0
    }

    # Recursively find UNKNOWN values in profile
    def find_unknowns(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if value == "UNKNOWN" or value == "Not disclosed":
                    unknowns['profile_fields'].append({
                        'field': new_path,
                        'value': value
                    })
                    unknowns['count'] += 1
                elif isinstance(value, (dict, list)):
                    find_unknowns(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_unknowns(item, f"{path}[{i}]")

    find_unknowns(profile)

    # Add evaluation unknowns to count
    unknowns['count'] += len(unknowns['evaluation_unknowns'])

    return unknowns


def create_resolution_prompt(profile: dict, evaluation: dict, unknowns: dict) -> str:
    """
    Create a comprehensive prompt for high-intelligence model to resolve unknowns.
    """
    company_name = profile.get('company_name', 'Unknown')
    canonical_url = profile.get('canonical_url', '')
    description = profile.get('description_one_sentence', '')

    # Format unknown fields
    unknown_fields_text = "\n".join([
        f"- {u['field']}: {u['value']}"
        for u in unknowns['profile_fields']
    ])

    # Format evaluation unknowns
    eval_unknowns_text = "\n".join([
        f"- {unknown}"
        for unknown in unknowns['evaluation_unknowns']
    ])

    # Extract key context from profile
    context_summary = {
        "company_name": company_name,
        "url": canonical_url,
        "description": description,
        "problem_statement": profile.get('problem_statement', 'UNKNOWN'),
        "primary_customer": profile.get('primary_customer', 'UNKNOWN'),
        "revenue_model": profile.get('revenue_model', 'UNKNOWN'),
        "market_signals": profile.get('market_signals', {}),
        "key_features": profile.get('key_features', []),
        "sources_reviewed": profile.get('sources_reviewed', [])
    }

    prompt = f"""You are a senior business analyst with deep research capabilities. You're helping complete a company profile that has missing information (marked as UNKNOWN).

**Company Context:**
{json.dumps(context_summary, indent=2)}

**Current Profile Confidence:** {profile.get('enrichment_metadata', {}).get('confidence', 'UNKNOWN')}
**Current Evaluation Confidence:** {evaluation.get('confidence_level', 'UNKNOWN')}

---

**UNKNOWN FIELDS IN PROFILE:**
{unknown_fields_text if unknown_fields_text else "No unknown fields in profile"}

**UNKNOWN FACTORS FROM EVALUATION:**
{eval_unknowns_text if eval_unknowns_text else "No unknown factors identified"}

---

**Your Task:**
Using your knowledge, reasoning, and inference capabilities:

1. **For each UNKNOWN field**, provide:
   - A researched/inferred value based on the company context
   - Your confidence level (HIGH/MEDIUM/LOW)
   - Brief reasoning for your conclusion

2. **For evaluation unknowns**, provide:
   - Research insights that address the unknown
   - Data sources or reasoning used
   - Confidence level

**IMPORTANT GUIDELINES:**
- Use your deep knowledge about business models, industries, and markets
- Make reasonable inferences based on similar companies and industry patterns
- If the company is in a known sector (e.g., "farmers", "healthcare"), leverage domain knowledge
- For market signals, estimate based on company type and target customer
- For pricing/revenue, estimate based on typical models for this business type
- For traction, infer from product maturity and public signals
- Be honest about uncertainty - mark LOW confidence when truly speculative
- Prioritize actionable insights over generic statements

**Return ONLY valid JSON with this structure:**
{{
  "resolved_fields": {{
    "field_path": {{
      "original_value": "UNKNOWN",
      "resolved_value": "Your researched/inferred value",
      "confidence": "HIGH | MEDIUM | LOW",
      "reasoning": "1-2 sentences explaining how you arrived at this"
    }}
  }},
  "resolved_unknowns": [
    {{
      "unknown_factor": "The original unknown",
      "resolution": "Your research insight addressing this",
      "confidence": "HIGH | MEDIUM | LOW",
      "reasoning": "How you arrived at this insight"
    }}
  ],
  "overall_improvement": {{
    "fields_resolved": 0,
    "unknowns_addressed": 0,
    "confidence_level": "HIGH | MEDIUM | LOW",
    "notes": "Any additional context or caveats"
  }}
}}
"""
    return prompt


def call_high_intelligence_model(prompt: str) -> tuple[bool, dict, dict]:
    """
    Call OpenAI o1 (or o1-mini) for deep reasoning and unknown resolution.

    Returns: (success, resolution_data, usage_stats)
    """
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Use o1-preview or o1-mini for deep thinking
    # o1-mini is faster and cheaper, o1-preview for most complex reasoning
    model = os.getenv('UNKNOWN_RESOLUTION_MODEL', 'o1-mini')

    print(f"[INFO] Calling high-intelligence model ({model}) to resolve unknowns...")
    print(f"[INFO] This may take 30-60 seconds for deep reasoning...")

    try:
        # o1 models don't support system messages or response_format
        # They also don't support temperature parameter
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.choices[0].message.content.strip()

        # Extract JSON from response (o1 might include explanation before/after)
        # Look for JSON block
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_text = result_text[json_start:json_end]
            resolution_data = json.loads(json_text)
        else:
            # Try parsing entire response
            resolution_data = json.loads(result_text)

        usage_stats = {
            "model": model,
            "tokens_total": response.usage.total_tokens,
            "reasoning_tokens": getattr(response.usage, 'completion_tokens_details', {}).get('reasoning_tokens', 0) if hasattr(response.usage, 'completion_tokens_details') else 0
        }

        return True, resolution_data, usage_stats

    except json.JSONDecodeError as e:
        print(f"[FAIL] Model returned invalid JSON: {e}")
        print(f"[DEBUG] Response text: {result_text[:500]}...")
        return False, {}, {"error": "Invalid JSON from model"}

    except Exception as e:
        print(f"[FAIL] Model call error: {e}")
        return False, {}, {"error": str(e)}


def apply_resolutions(profile: dict, evaluation: dict, resolution_data: dict) -> tuple[dict, dict]:
    """
    Apply resolved values back to profile and evaluation.

    Returns: (updated_profile, updated_evaluation)
    """
    updated_profile = profile.copy()
    updated_evaluation = evaluation.copy()

    resolved_fields = resolution_data.get('resolved_fields', {})

    # Apply field resolutions
    for field_path, resolution in resolved_fields.items():
        resolved_value = resolution.get('resolved_value')
        confidence = resolution.get('confidence', 'MEDIUM')

        # Navigate to field and update
        # Handle nested paths like "market_signals.target_market"
        parts = field_path.split('.')
        target = updated_profile

        for i, part in enumerate(parts[:-1]):
            if part not in target:
                target[part] = {}
            target = target[part]

        # Update the final field
        final_key = parts[-1]
        if final_key in target and target[final_key] in ['UNKNOWN', 'Not disclosed']:
            target[final_key] = f"{resolved_value} [AI-inferred: {confidence}]"

    # Add resolved unknowns to evaluation
    resolved_unknowns = resolution_data.get('resolved_unknowns', [])
    if resolved_unknowns and 'resolved_unknowns' not in updated_evaluation:
        updated_evaluation['resolved_unknowns'] = []

    for resolution in resolved_unknowns:
        updated_evaluation['resolved_unknowns'].append({
            'original_unknown': resolution.get('unknown_factor'),
            'resolution': resolution.get('resolution'),
            'confidence': resolution.get('confidence'),
            'reasoning': resolution.get('reasoning')
        })

    return updated_profile, updated_evaluation


def save_outputs(prospect_id: str, updated_profile: dict, updated_evaluation: dict,
                 resolution_data: dict, usage_stats: dict):
    """Save updated profile, evaluation, and resolution metadata."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    prospect_dir = tmp_dir / prospect_id

    # Add resolution metadata to profile
    if 'resolution_metadata' not in updated_profile:
        updated_profile['resolution_metadata'] = {}

    updated_profile['resolution_metadata'] = {
        "resolved_at": datetime.now().isoformat(),
        "model_used": usage_stats.get('model', 'unknown'),
        "tokens_used": usage_stats.get('tokens_total', 0),
        "reasoning_tokens": usage_stats.get('reasoning_tokens', 0),
        "fields_resolved": resolution_data.get('overall_improvement', {}).get('fields_resolved', 0),
        "unknowns_addressed": resolution_data.get('overall_improvement', {}).get('unknowns_addressed', 0),
        "resolution_confidence": resolution_data.get('overall_improvement', {}).get('confidence_level', 'MEDIUM')
    }

    # Save updated profile
    profile_file = prospect_dir / 'prospect_profile.json'
    with open(profile_file, 'w', encoding='utf-8') as f:
        json.dump(updated_profile, f, indent=2)
    print(f"[OK] Updated profile saved to: {profile_file}")

    # Save updated evaluation
    if updated_evaluation:
        eval_file = prospect_dir / 'sv_evaluation_record.json'
        with open(eval_file, 'w', encoding='utf-8') as f:
            json.dump(updated_evaluation, f, indent=2)
        print(f"[OK] Updated evaluation saved to: {eval_file}")

    # Save resolution record for audit trail
    resolution_file = prospect_dir / 'unknown_resolution.json'
    resolution_record = {
        "resolved_at": datetime.now().isoformat(),
        "resolution_data": resolution_data,
        "usage_stats": usage_stats
    }
    with open(resolution_file, 'w', encoding='utf-8') as f:
        json.dump(resolution_record, f, indent=2)
    print(f"[OK] Resolution record saved to: {resolution_file}")


def main(prospect_id: str) -> int:
    """Main workflow: Resolve unknowns using high-intelligence model."""
    print("="*60)
    print("RESOLVE UNKNOWNS (HIGH-INTELLIGENCE MODEL)")
    print("="*60)
    print(f"Prospect ID: {prospect_id}\n")

    # Step 1: Load profile and evaluation
    try:
        profile, evaluation = load_profile_and_evaluation(prospect_id)
        print(f"[OK] Loaded profile and evaluation")
        print(f"Company: {profile.get('company_name', 'N/A')}")
    except Exception as e:
        print(f"[FAIL] Could not load data: {e}")
        return 1

    # Step 2: Detect unknowns
    unknowns = detect_unknowns(profile, evaluation)
    print(f"[OK] Detected {unknowns['count']} unknown fields/factors")

    if unknowns['count'] == 0:
        print("[INFO] No unknowns found - profile is complete!")
        return 0

    print(f"  - Profile fields with UNKNOWN: {len(unknowns['profile_fields'])}")
    print(f"  - Evaluation unknowns: {len(unknowns['evaluation_unknowns'])}")

    # Step 3: Create resolution prompt
    prompt = create_resolution_prompt(profile, evaluation, unknowns)
    print(f"[OK] Created resolution prompt")

    # Step 4: Call high-intelligence model
    success, resolution_data, usage_stats = call_high_intelligence_model(prompt)

    if not success:
        print(f"[FAIL] Resolution failed: {usage_stats.get('error', 'Unknown error')}")
        return 1

    print(f"[OK] Resolution complete")
    print(f"Tokens used: {usage_stats.get('tokens_total', 0)}")
    print(f"Reasoning tokens: {usage_stats.get('reasoning_tokens', 0)}")

    # Step 5: Apply resolutions
    updated_profile, updated_evaluation = apply_resolutions(profile, evaluation, resolution_data)
    print(f"[OK] Applied resolutions to profile and evaluation")

    improvement = resolution_data.get('overall_improvement', {})
    print(f"  - Fields resolved: {improvement.get('fields_resolved', 0)}")
    print(f"  - Unknowns addressed: {improvement.get('unknowns_addressed', 0)}")
    print(f"  - Resolution confidence: {improvement.get('confidence_level', 'N/A')}")

    # Step 6: Save outputs
    save_outputs(prospect_id, updated_profile, updated_evaluation, resolution_data, usage_stats)

    # Summary
    print("\n" + "="*60)
    print("UNKNOWN RESOLUTION COMPLETE")
    print("="*60)
    print(f"Company: {profile.get('company_name', 'N/A')}")
    print(f"Original unknowns: {unknowns['count']}")
    print(f"Fields resolved: {improvement.get('fields_resolved', 0)}")
    print(f"Unknowns addressed: {improvement.get('unknowns_addressed', 0)}")
    print(f"Resolution confidence: {improvement.get('confidence_level', 'N/A')}")
    print(f"Model: {usage_stats.get('model', 'N/A')}")
    print(f"Tokens: {usage_stats.get('tokens_total', 0):,}")

    if improvement.get('notes'):
        print(f"\nNotes: {improvement.get('notes')}")

    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resolve_unknowns.py <prospect_id>")
        print("Example: python resolve_unknowns.py example_com_a1b2c3d4")
        sys.exit(1)

    prospect_id = sys.argv[1]
    exit_code = main(prospect_id)
    sys.exit(exit_code)
