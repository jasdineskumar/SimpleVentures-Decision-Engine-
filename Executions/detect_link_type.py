#!/usr/bin/env python3
"""
Link Type Detector - Determines if a URL is a directory or single company

Helps users choose between:
- batch_directory_scrape.py (for directories with multiple companies)
- sv_pipeline.py (for single company URLs)
"""

import sys
import re
from urllib.parse import urlparse, parse_qs

# Known directory patterns
DIRECTORY_PATTERNS = {
    'yc_batch': {
        'pattern': r'ycombinator\.com/companies\?batch=',
        'type': 'directory',
        'description': 'Y Combinator batch directory',
        'tool': 'batch_directory_scrape.py --source yc --batch "BATCH_NAME"'
    },
    'yc_all': {
        'pattern': r'ycombinator\.com/companies/?$',
        'type': 'directory',
        'description': 'Y Combinator all companies directory',
        'tool': 'batch_directory_scrape.py (requires custom config)'
    },
    'product_hunt_topic': {
        'pattern': r'producthunt\.com/topics/',
        'type': 'directory',
        'description': 'Product Hunt topic directory',
        'tool': 'batch_directory_scrape.py --source product_hunt --topic "TOPIC"'
    },
    'crunchbase_list': {
        'pattern': r'crunchbase\.com/lists/',
        'type': 'directory',
        'description': 'Crunchbase company list',
        'tool': 'batch_directory_scrape.py --source custom --config crunchbase.json'
    },
    'portfolio': {
        'pattern': r'/(portfolio|companies|startups)',
        'type': 'directory',
        'description': 'Portfolio/companies page (likely directory)',
        'tool': 'batch_directory_scrape.py --source custom --config custom.json'
    }
}

# Single company patterns
SINGLE_COMPANY_PATTERNS = {
    'yc_company': {
        'pattern': r'ycombinator\.com/companies/[^/?]+/?$',
        'type': 'single',
        'description': 'Y Combinator company profile',
        'tool': 'sv_pipeline.py'
    },
    'product_hunt_post': {
        'pattern': r'producthunt\.com/posts/',
        'type': 'single',
        'description': 'Product Hunt product page',
        'tool': 'sv_pipeline.py'
    },
    'root_domain': {
        'pattern': r'^https?://[^/]+/?$',
        'type': 'single',
        'description': 'Company root domain',
        'tool': 'sv_pipeline.py'
    }
}


def detect_link_type(url: str) -> dict:
    """
    Detect if URL is a directory (multiple companies) or single company

    Returns:
        {
            'type': 'directory' | 'single' | 'unknown',
            'confidence': 'high' | 'medium' | 'low',
            'description': str,
            'tool': str,
            'reasoning': str
        }
    """

    # Parse URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    result = {
        'type': 'unknown',
        'confidence': 'low',
        'description': 'Unable to determine',
        'tool': 'Manual inspection required',
        'reasoning': []
    }

    # Check single company patterns FIRST (more specific)
    for pattern_name, pattern_info in SINGLE_COMPANY_PATTERNS.items():
        if re.search(pattern_info['pattern'], url, re.IGNORECASE):
            result['type'] = 'single'
            result['confidence'] = 'high'
            result['description'] = pattern_info['description']
            result['tool'] = pattern_info['tool']
            result['reasoning'].append(f"Matches single company pattern: {pattern_name}")
            return result

    # Then check directory patterns (more general)
    for pattern_name, pattern_info in DIRECTORY_PATTERNS.items():
        if re.search(pattern_info['pattern'], url, re.IGNORECASE):
            result['type'] = 'directory'
            result['confidence'] = 'high'
            result['description'] = pattern_info['description']
            result['tool'] = pattern_info['tool']
            result['reasoning'].append(f"Matches known directory pattern: {pattern_name}")
            return result

    # Heuristic checks

    # Check for query parameters (often indicates filtering/listing)
    if query_params:
        directory_params = ['batch', 'category', 'filter', 'page', 'topic', 'tag']
        if any(param in query_params for param in directory_params):
            result['type'] = 'directory'
            result['confidence'] = 'medium'
            result['description'] = 'URL contains directory-like query parameters'
            result['tool'] = 'batch_directory_scrape.py --source custom --config custom.json'
            result['reasoning'].append(f"Query parameters suggest filtering: {list(query_params.keys())}")
            return result

    # Check path indicators
    path = parsed.path.lower()
    directory_keywords = ['companies', 'portfolio', 'startups', 'directory', 'list', 'batch']
    if any(keyword in path for keyword in directory_keywords):
        result['type'] = 'directory'
        result['confidence'] = 'medium'
        result['description'] = 'Path contains directory keywords'
        result['tool'] = 'batch_directory_scrape.py --source custom --config custom.json'
        result['reasoning'].append(f"Path contains directory keyword: {path}")
        return result

    # Default: assume single company if root domain or simple path
    if parsed.path in ['', '/'] or len(parsed.path.split('/')) <= 2:
        result['type'] = 'single'
        result['confidence'] = 'medium'
        result['description'] = 'Simple URL structure suggests single company'
        result['tool'] = 'sv_pipeline.py'
        result['reasoning'].append("Simple URL structure (root domain or single path)")
        return result

    return result


def print_result(url: str, result: dict):
    """Pretty print detection result"""

    # Color codes for terminal (optional)
    COLORS = {
        'directory': '\033[94m',  # Blue
        'single': '\033[92m',     # Green
        'unknown': '\033[93m',    # Yellow
        'reset': '\033[0m'
    }

    color = COLORS.get(result['type'], '')
    reset = COLORS['reset']

    print("\n" + "="*60)
    print("LINK TYPE DETECTION")
    print("="*60)
    print(f"\nURL: {url}")
    print(f"\nType: {color}{result['type'].upper()}{reset}")
    print(f"Confidence: {result['confidence'].upper()}")
    print(f"Description: {result['description']}")
    print(f"\nRecommended Tool:")
    print(f"  {result['tool']}")

    if result['reasoning']:
        print(f"\nReasoning:")
        for reason in result['reasoning']:
            print(f"  - {reason}")

    # Additional guidance
    print("\n" + "-"*60)
    if result['type'] == 'directory':
        print("[DIRECTORY DETECTED]")
        print("\nThis URL shows MULTIPLE companies.")
        print("Use the BATCH workflow to scrape and process all companies.")
        print("\nNext steps:")
        print("  1. Run batch_directory_scrape.py to extract company list")
        print("  2. Run batch_sv_pipeline.py to process all companies")

    elif result['type'] == 'single':
        print("[SINGLE COMPANY DETECTED]")
        print("\nThis URL is for ONE specific company.")
        print("Use the REGULAR SV pipeline to process this company.")
        print("\nNext step:")
        print("  Run: python Executions/sv_pipeline.py " + url)

    else:
        print("[UNKNOWN TYPE]")
        print("\nCouldn't automatically determine link type.")
        print("Please manually inspect the URL in a browser:")
        print("  - If you see MULTIPLE companies -> Use batch workflow")
        print("  - If you see ONE company -> Use regular sv_pipeline.py")

    print("="*60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python detect_link_type.py <url>")
        print("\nExamples:")
        print("  python detect_link_type.py https://www.ycombinator.com/companies?batch=Winter%202026")
        print("  python detect_link_type.py https://chasi.co/")
        print()
        return 1

    url = sys.argv[1]
    result = detect_link_type(url)
    print_result(url, result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
