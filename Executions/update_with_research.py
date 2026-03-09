#!/usr/bin/env python3
"""
Update Existing Profile with Canadian Market Research

This script runs Canadian market research on an existing prospect
and updates the Google Doc profile with the new research section.

Usage:
    python Executions/update_with_research.py <prospect_id>
    python Executions/update_with_research.py didit_me_b825e120
"""

import sys
import subprocess

def main(prospect_id):
    """Run Canadian market research and update the profile document."""

    print("\n" + "="*60)
    print("UPDATE PROFILE WITH CANADIAN MARKET RESEARCH")
    print("="*60)
    print(f"Prospect ID: {prospect_id}\n")

    # Step 1: Run Canadian Market Research
    print("[STEP 1/2] Running Canadian Market Research...")
    result = subprocess.run(
        ['python', 'Executions/canadian_market_research.py', prospect_id],
        capture_output=False
    )

    if result.returncode != 0:
        print(f"\n[FAIL] Canadian Market Research failed with exit code {result.returncode}")
        return 1

    print("\n[OK] Canadian Market Research completed successfully")

    # Step 2: Regenerate Profile Document (will include the new research)
    print("\n[STEP 2/2] Regenerating Profile Document with Research...")
    result = subprocess.run(
        ['python', 'Executions/generate_profile_doc.py', prospect_id],
        capture_output=False
    )

    if result.returncode != 0:
        print(f"\n[FAIL] Profile Document generation failed with exit code {result.returncode}")
        return 1

    print("\n[OK] Profile Document updated successfully")

    # Summary
    print("\n" + "="*60)
    print("UPDATE COMPLETE")
    print("="*60)
    print(f"Prospect ID: {prospect_id}")
    print("[OK] Canadian Market Research generated")
    print("[OK] Google Doc updated with research section")
    print("="*60 + "\n")

    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_with_research.py <prospect_id>")
        print("Example: python update_with_research.py didit_me_b825e120")
        print("\nThis script adds Canadian market research to an existing profile.")
        sys.exit(1)

    prospect_id = sys.argv[1]
    exit_code = main(prospect_id)
    sys.exit(exit_code)
