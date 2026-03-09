#!/usr/bin/env python3
"""
Quick test to verify OpenAI and Firecrawl APIs work.
Google Sheets requires OAuth browser flow - run test_setup.py separately for that.
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("QUICK API TEST")
print("="*60)

# Test 1: OpenAI
print("\n1. Testing OpenAI API...")
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'OK' only"}],
        max_tokens=5
    )

    print(f"   [PASS] OpenAI: {response.choices[0].message.content.strip()}")
    print(f"   [INFO] Tokens used: {response.usage.total_tokens}")
except Exception as e:
    print(f"   [FAIL] OpenAI error: {e}")

# Test 2: Firecrawl
print("\n2. Testing Firecrawl API...")
try:
    import requests

    response = requests.post(
        "https://api.firecrawl.dev/v0/scrape",
        headers={"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}"},
        json={"url": "https://example.com"},
        timeout=15
    )

    if response.status_code == 200:
        print(f"   [PASS] Firecrawl working (status {response.status_code})")
    else:
        print(f"   [FAIL] Firecrawl error: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   [FAIL] Firecrawl error: {e}")

print("\n"+"="*60)
print("Quick test complete!")
print("="*60)
print("\nFor Google Sheets setup, you need to:")
print("1. Run: python Executions/test_setup.py")
print("2. Complete OAuth in browser when prompted")
print("3. Script will create the Master Prospect List")
print("="*60+"\n")
