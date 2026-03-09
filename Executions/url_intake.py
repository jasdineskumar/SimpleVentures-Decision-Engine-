#!/usr/bin/env python3
"""
URL Intake & Canonicalization - Execution Layer

Takes a raw URL and produces a canonical, validated form with metadata.
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
import os

load_dotenv()


def normalize_url(raw_url: str) -> str:
    """
    Normalize a raw URL to canonical form.

    - Add https:// if no protocol
    - Remove trailing slashes
    - Handle common URL patterns
    """
    url = raw_url.strip()

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Parse URL
    parsed = urlparse(url)

    # Normalize components
    scheme = parsed.scheme or 'https'
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/')

    # Reconstruct without fragment, preserve query
    canonical = urlunparse((
        scheme,
        netloc,
        path,
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))

    return canonical


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate that URL is well-formed.

    Returns: (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)

        # Check has scheme and netloc
        if not parsed.scheme:
            return False, "Missing URL scheme (http/https)"

        if not parsed.netloc:
            return False, "Missing domain/netloc"

        # Check scheme is http or https
        if parsed.scheme not in ['http', 'https']:
            return False, f"Invalid scheme: {parsed.scheme}"

        # Basic domain validation
        if '.' not in parsed.netloc and parsed.netloc != 'localhost':
            return False, f"Invalid domain: {parsed.netloc}"

        return True, ""

    except Exception as e:
        return False, f"URL parsing error: {str(e)}"


def detect_source_type(url: str) -> str:
    """
    Detect the type of source from URL patterns.
    """
    url_lower = url.lower()

    # Y Combinator
    if 'ycombinator.com/companies/' in url_lower:
        return 'yc_profile'

    # PDF
    if url_lower.endswith('.pdf'):
        return 'pitch_deck'

    # Notion
    if 'notion.site' in url_lower or 'notion.so' in url_lower:
        return 'notion'

    # LinkedIn
    if 'linkedin.com/company/' in url_lower:
        return 'linkedin'

    # News/Articles (common patterns)
    article_domains = ['techcrunch.com', 'medium.com', 'substack.com',
                       'forbes.com', 'bloomberg.com', 'reuters.com']
    if any(domain in url_lower for domain in article_domains):
        return 'article'

    # Default to website
    parsed = urlparse(url)
    if parsed.path in ['', '/'] and not parsed.query:
        return 'website'

    return 'unknown'


def extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc

    # Remove www. prefix
    if domain.startswith('www.'):
        domain = domain[4:]

    return domain


def generate_prospect_id(url: str) -> str:
    """
    Generate stable prospect ID from URL.

    Format: {domain}_{hash8}
    """
    domain = extract_domain(url)

    # Clean domain for ID (replace dots with underscores)
    clean_domain = domain.replace('.', '_')

    # Generate short hash of full URL
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    return f"{clean_domain}_{url_hash}"


def check_existing_output(prospect_id: str) -> tuple[bool, dict]:
    """
    Check if canonical_url.json already exists and is valid.

    Returns: (exists_and_valid, data)
    """
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    output_file = tmp_dir / prospect_id / 'canonical_url.json'

    if not output_file.exists():
        return False, {}

    try:
        with open(output_file, 'r') as f:
            data = json.load(f)

        # Check if valid
        if not data.get('valid', False):
            return False, data

        # Check if recent (within 24 hours)
        timestamp = datetime.fromisoformat(data['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600

        if age_hours < 24:
            return True, data

        return False, data

    except Exception as e:
        # Debug: print error if checkpointing fails
        # print(f"[DEBUG] Checkpoint check failed: {e}")
        return False, {}


def save_output(prospect_id: str, data: dict):
    """Save canonical URL data to JSON file."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    prospect_dir = tmp_dir / prospect_id
    prospect_dir.mkdir(parents=True, exist_ok=True)

    output_file = prospect_dir / 'canonical_url.json'

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"[OK] Saved canonical URL to: {output_file}")


def main(raw_url: str) -> int:
    """
    Main workflow: URL intake and canonicalization.

    Returns: 0 on success, 1 on failure
    """
    print("="*60)
    print("URL INTAKE & CANONICALIZATION")
    print("="*60)
    print(f"Raw URL: {raw_url}\n")

    # Step 1: Normalize URL
    try:
        canonical_url = normalize_url(raw_url)
        print(f"[OK] Normalized URL: {canonical_url}")
    except Exception as e:
        print(f"[FAIL] URL normalization error: {e}")
        return 1

    # Step 2: Validate URL
    is_valid, error_msg = validate_url(canonical_url)
    if not is_valid:
        print(f"[FAIL] Invalid URL: {error_msg}")

        # Save invalid result
        prospect_id = "invalid_" + hashlib.md5(raw_url.encode()).hexdigest()[:8]
        save_output(prospect_id, {
            "prospect_id": prospect_id,
            "raw_url": raw_url,
            "canonical_url": canonical_url,
            "source_type": "unknown",
            "domain": "",
            "timestamp": datetime.now().isoformat(),
            "valid": False,
            "error": error_msg
        })
        return 1

    print(f"[OK] URL is valid")

    # Step 3: Generate Prospect ID
    prospect_id = generate_prospect_id(canonical_url)
    print(f"[OK] Prospect ID: {prospect_id}")

    # Step 4: Check if already processed (checkpointing)
    exists, existing_data = check_existing_output(prospect_id)
    if exists:
        print(f"[INFO] Already processed (age < 24h), skipping")
        print(f"[INFO] Using cached data from: .tmp/{prospect_id}/canonical_url.json")
        print(f"\n" + "="*60)
        print("URL INTAKE COMPLETE (FROM CACHE)")
        print("="*60)
        print(f"Canonical URL: {existing_data['canonical_url']}")
        print(f"Source Type: {existing_data['source_type']}")
        print(f"Prospect ID: {prospect_id}")
        print("="*60 + "\n")
        return 0

    # Step 5: Detect Source Type
    source_type = detect_source_type(canonical_url)
    print(f"[OK] Source Type: {source_type}")

    # Step 6: Extract Domain
    domain = extract_domain(canonical_url)
    print(f"[OK] Domain: {domain}")

    # Step 7: Create output data
    output_data = {
        "prospect_id": prospect_id,
        "raw_url": raw_url,
        "canonical_url": canonical_url,
        "source_type": source_type,
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "valid": True
    }

    # Step 8: Save output
    save_output(prospect_id, output_data)

    print("\n" + "="*60)
    print("URL INTAKE COMPLETE")
    print("="*60)
    print(f"Canonical URL: {canonical_url}")
    print(f"Source Type: {source_type}")
    print(f"Prospect ID: {prospect_id}")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python url_intake.py <url>")
        print("Example: python url_intake.py https://example.com")
        sys.exit(1)

    raw_url = sys.argv[1]
    exit_code = main(raw_url)
    sys.exit(exit_code)
