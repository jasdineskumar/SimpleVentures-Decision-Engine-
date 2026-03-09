#!/usr/bin/env python3
"""
Data Enrichment - Execution Layer

Uses LLM to extract structured Prospect Profile from scraped content.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def load_inputs(prospect_id: str) -> tuple[dict, str, dict]:
    """
    Load all required inputs for enrichment.

    Returns: (canonical_data, content, metadata)
    """
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    prospect_dir = tmp_dir / prospect_id

    # Load canonical URL data
    canonical_file = prospect_dir / 'canonical_url.json'
    if not canonical_file.exists():
        raise FileNotFoundError(f"Canonical URL file not found: {canonical_file}")

    with open(canonical_file, 'r') as f:
        canonical_data = json.load(f)

    # Load scraped content
    content_file = prospect_dir / 'raw_sources' / 'content.md'
    if not content_file.exists():
        raise FileNotFoundError(f"Content file not found: {content_file}")

    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Load metadata
    metadata_file = prospect_dir / 'raw_sources' / 'metadata.json'
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    return canonical_data, content, metadata


def check_existing_output(prospect_id: str, max_age_hours: int = 24) -> tuple[bool, dict]:
    """
    Check if prospect profile already exists (checkpointing).

    Returns: (exists_and_recent, profile_data)
    """
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    profile_file = tmp_dir / prospect_id / 'prospect_profile.json'

    if not profile_file.exists():
        return False, {}

    try:
        with open(profile_file, 'r') as f:
            profile_data = json.load(f)

        # Check if recent
        enriched_at = datetime.fromisoformat(profile_data['enrichment_metadata']['enriched_at'])
        age_hours = (datetime.now() - enriched_at).total_seconds() / 3600

        if age_hours < max_age_hours:
            return True, profile_data

        return False, profile_data

    except Exception:
        return False, {}


def create_enrichment_prompt(canonical_data: dict, content: str, metadata: dict) -> str:
    """
    Create LLM prompt for extracting Prospect Profile.
    """
    # Truncate content if too long (keep first 8,000 words to stay under rate limits)
    words = content.split()
    if len(words) > 8000:
        content = ' '.join(words[:8000])
        truncated = True
    else:
        truncated = False

    prompt = f"""You are a business analyst extracting structured information from a company website.

**Company URL:** {canonical_data['canonical_url']}
**Source Type:** {canonical_data['source_type']}

**Scraped Content:**
{content}

---

**Your Task:**
Extract the following information into a structured JSON format. Follow these rules:

1. **Extract explicit information first** - Use information directly stated in the content
2. **Make reasonable inferences** - When explicit info is missing, infer from context (e.g., if they mention "farmers struggling with complex spreadsheets", infer the problem statement)
3. **Use "UNKNOWN" only when truly unclear** - If you can reasonably infer something from the business model or context, include it
4. **Use plain English** - No marketing jargon or fluff
5. **Be factual but interpretive** - State what the company does based on all available evidence
6. **Cite sources** - For non-obvious claims, include a brief quote from the content

**JSON Schema to Return:**
{{
  "company_name": "string (extract from content or URL)",
  "description_one_sentence": "string (plain English, what does the company do?)",
  "problem_statement": "string | UNKNOWN (what pain point is addressed?)",
  "primary_customer": "string | UNKNOWN (who uses this product?)",
  "primary_buyer": "string | UNKNOWN (who pays for it, if different from user?)",
  "customer_context": "string | UNKNOWN (in what setting/context is it used?)",
  "key_features": ["string", "string", ...] (only features explicitly mentioned),
  "revenue_model": "string | UNKNOWN (SaaS, marketplace, services, etc.)",
  "pricing_signals": "string | Not disclosed (any pricing info found?)",
  "who_pays": "string | UNKNOWN (individual, SMB, enterprise, etc.)",
  "market_signals": {{
    "target_market": "string | UNKNOWN",
    "geographic_focus": "string | UNKNOWN",
    "market_size_indicators": "string | UNKNOWN"
  }},
  "product_maturity": "string | UNKNOWN (MVP, launched, mature, etc.)",
  "team_signals": {{
    "founder_background": "string | UNKNOWN",
    "team_size_indicators": "string | UNKNOWN"
  }},
  "traction_signals": {{
    "customer_count_indicators": "string | UNKNOWN",
    "revenue_indicators": "string | UNKNOWN",
    "growth_indicators": "string | UNKNOWN"
  }},
  "key_excerpts": [
    {{"claim": "string (what you're claiming)", "quote": "string (verbatim quote)", "source": "{canonical_data['canonical_url']}"}}
  ]
}}

**IMPORTANT:**
- Return ONLY valid JSON, no other text
- If information is not in the content, use "UNKNOWN"
- Do not make assumptions or extrapolations
- Focus on facts that would help evaluate this opportunity
"""

    if truncated:
        prompt += "\n\n**Note:** Content was truncated to 10,000 words."

    return prompt


def call_llm_for_enrichment(prompt: str) -> tuple[bool, dict, dict]:
    """
    Call OpenAI LLM to extract structured data.

    Returns: (success, profile_data, usage_stats)
    """
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    model = os.getenv('ENRICHMENT_MODEL', 'gpt-4o')

    print(f"[INFO] Calling LLM ({model}) for enrichment...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a business analyst. Extract structured data as JSON. Never speculate."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for factual extraction
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON
        profile_data = json.loads(result_text)

        usage_stats = {
            "model": model,
            "tokens_input": response.usage.prompt_tokens,
            "tokens_output": response.usage.completion_tokens,
            "tokens_total": response.usage.total_tokens
        }

        return True, profile_data, usage_stats

    except json.JSONDecodeError as e:
        print(f"[FAIL] LLM returned invalid JSON: {e}")
        return False, {}, {"error": "Invalid JSON from LLM"}

    except Exception as e:
        print(f"[FAIL] LLM call error: {e}")
        return False, {}, {"error": str(e)}


def validate_and_enrich_profile(profile_data: dict, canonical_data: dict) -> dict:
    """
    Add metadata and validate profile structure.
    """
    # Add missing top-level fields
    profile_data['prospect_id'] = canonical_data['prospect_id']
    profile_data['canonical_url'] = canonical_data['canonical_url']
    profile_data['source_type'] = canonical_data['source_type']

    # Add sources_reviewed
    if 'sources_reviewed' not in profile_data:
        profile_data['sources_reviewed'] = [canonical_data['canonical_url']]

    # Calculate confidence based on UNKNOWN count
    unknown_count = str(profile_data).count('UNKNOWN')
    total_fields = 20  # Approximate field count

    if unknown_count > total_fields * 0.5:
        confidence = "LOW"
    elif unknown_count > total_fields * 0.2:
        confidence = "MEDIUM"
    else:
        confidence = "HIGH"

    return profile_data, confidence


def save_output(prospect_id: str, profile_data: dict, usage_stats: dict, confidence: str):
    """Save enriched Prospect Profile."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    profile_file = tmp_dir / prospect_id / 'prospect_profile.json'

    # Add enrichment metadata
    profile_data['enrichment_metadata'] = {
        "enriched_at": datetime.now().isoformat(),
        "model_used": usage_stats.get('model', 'unknown'),
        "tokens_used": usage_stats.get('tokens_total', 0),
        "confidence": confidence
    }

    with open(profile_file, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=2)

    print(f"[OK] Saved Prospect Profile to: {profile_file}")


def main(prospect_id: str) -> int:
    """
    Main workflow: Data enrichment.

    Returns: 0 on success, 1 on failure
    """
    print("="*60)
    print("DATA ENRICHMENT (PROSPECT PROFILE)")
    print("="*60)
    print(f"Prospect ID: {prospect_id}\n")

    # Step 1: Check if already enriched (checkpointing)
    exists, existing_profile = check_existing_output(prospect_id)
    if exists:
        print(f"[INFO] Already enriched (age < 24h), skipping")
        print(f"[INFO] Using cached profile from: .tmp/{prospect_id}/prospect_profile.json")
        print(f"\n" + "="*60)
        print("DATA ENRICHMENT COMPLETE (FROM CACHE)")
        print("="*60)
        print(f"Company: {existing_profile.get('company_name', 'N/A')}")
        print(f"Confidence: {existing_profile['enrichment_metadata']['confidence']}")
        print(f"Tokens Used: {existing_profile['enrichment_metadata']['tokens_used']}")
        print("="*60 + "\n")
        return 0

    # Step 2: Load inputs
    try:
        canonical_data, content, metadata = load_inputs(prospect_id)
        print(f"[OK] Loaded inputs")
        print(f"Content length: {len(content.split())} words")
    except Exception as e:
        print(f"[FAIL] Could not load inputs: {e}")
        return 1

    # Step 3: Create enrichment prompt
    prompt = create_enrichment_prompt(canonical_data, content, metadata)
    print(f"[OK] Created enrichment prompt")

    # Step 4: Call LLM
    success, profile_data, usage_stats = call_llm_for_enrichment(prompt)

    if not success:
        print(f"[FAIL] Enrichment failed: {usage_stats.get('error', 'Unknown error')}")
        return 1

    print(f"[OK] LLM enrichment successful")
    print(f"Tokens used: {usage_stats.get('tokens_total', 0)}")

    # Step 5: Validate and add metadata
    profile_data, confidence = validate_and_enrich_profile(profile_data, canonical_data)
    print(f"[OK] Profile validated")
    print(f"Confidence: {confidence}")

    # Step 6: Save output
    save_output(prospect_id, profile_data, usage_stats, confidence)

    print("\n" + "="*60)
    print("DATA ENRICHMENT COMPLETE")
    print("="*60)
    print(f"Company: {profile_data.get('company_name', 'N/A')}")
    print(f"Description: {profile_data.get('description_one_sentence', 'N/A')[:80]}...")
    print(f"Confidence: {confidence}")
    print(f"Tokens Used: {usage_stats.get('tokens_total', 0)}")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python data_enrichment.py <prospect_id>")
        print("Example: python data_enrichment.py example_com_a1b2c3d4")
        sys.exit(1)

    prospect_id = sys.argv[1]
    exit_code = main(prospect_id)
    sys.exit(exit_code)
