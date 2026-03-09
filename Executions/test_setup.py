#!/usr/bin/env python3
"""
Test setup script to verify all API connections and create necessary resources.
This script should be run before building the workflows.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_variables():
    """Check that all required environment variables are set."""
    print("=" * 60)
    print("1. Testing Environment Variables")
    print("=" * 60)

    required_vars = [
        "OPENAI_API_KEY",
        "GOOGLE_OAUTH_CREDENTIALS",
        "FIRECRAWL_API_KEY",
        "TMP_DIR",
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"[OK] {var}: {display_value}")
        else:
            print(f"[X] {var}: NOT SET")
            missing.append(var)

    if missing:
        print(f"\n[FAIL] Missing environment variables: {', '.join(missing)}")
        return False

    print("\n[PASS] All required environment variables are set\n")
    return True


def test_tmp_directory():
    """Verify .tmp directory exists and is writable."""
    print("=" * 60)
    print("2. Testing Temporary Directory")
    print("=" * 60)

    tmp_dir = Path(os.getenv("TMP_DIR", "./.tmp"))

    if not tmp_dir.exists():
        print(f"[X] Directory does not exist: {tmp_dir}")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created directory: {tmp_dir}")
    else:
        print(f"[OK] Directory exists: {tmp_dir}")

    # Test write permissions
    test_file = tmp_dir / "test_write.txt"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"[OK] Directory is writable: {tmp_dir}")
        print("\n[PASS] Temporary directory is ready\n")
        return True
    except Exception as e:
        print(f"[X] Cannot write to directory: {e}")
        print("\n[FAIL] Temporary directory setup failed\n")
        return False


def test_openai_api():
    """Test OpenAI API connection."""
    print("=" * 60)
    print("3. Testing OpenAI API Connection")
    print("=" * 60)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Simple test completion
        print("Sending test request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API test successful' and nothing else."}],
            max_tokens=10
        )

        result = response.choices[0].message.content.strip()
        print(f"[OK] OpenAI Response: {result}")
        print(f"[OK] Model used: {response.model}")
        print(f"[OK] Tokens used: {response.usage.total_tokens}")
        print("\n[PASS] OpenAI API connection successful\n")
        return True

    except ImportError:
        print("[X] OpenAI library not installed. Run: pip install openai")
        print("\n[FAIL] OpenAI API test failed\n")
        return False
    except Exception as e:
        print(f"[X] OpenAI API error: {e}")
        print("\n[FAIL] OpenAI API test failed\n")
        return False


def test_firecrawl_api():
    """Test Firecrawl API connection."""
    print("=" * 60)
    print("4. Testing Firecrawl API Connection")
    print("=" * 60)

    try:
        import requests

        api_key = os.getenv("FIRECRAWL_API_KEY")

        # Test with a simple scrape request
        print("Sending test request to Firecrawl...")
        response = requests.post(
            "https://api.firecrawl.dev/v0/scrape",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"url": "https://example.com"},
            timeout=10
        )

        if response.status_code == 200:
            print(f"[OK] Firecrawl API responded: {response.status_code}")
            print(f"[OK] Successfully scraped test URL")
            print("\n[PASS] Firecrawl API connection successful\n")
            return True
        else:
            print(f"[X] Firecrawl API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print("\n[FAIL] Firecrawl API test failed\n")
            return False

    except ImportError:
        print("[X] requests library not installed. Run: pip install requests")
        print("\n[FAIL] Firecrawl API test failed\n")
        return False
    except Exception as e:
        print(f"[X] Firecrawl API error: {e}")
        print("\n[FAIL] Firecrawl API test failed\n")
        return False


def test_google_sheets_and_create():
    """Test Google Sheets API and create Master Prospect List."""
    print("=" * 60)
    print("5. Testing Google Sheets API & Creating Master List")
    print("=" * 60)

    try:
        import gspread
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import pickle

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive']

        creds = None
        token_file = Path("./token.json")
        creds_file = os.getenv("GOOGLE_OAUTH_CREDENTIALS")

        # Check if we have a token file
        if token_file.exists():
            try:
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            except:
                pass

        # If no valid credentials, do the OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                print("Starting OAuth flow...")
                print("A browser window will open for authentication.")
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            print("[OK] Credentials saved")

        # Connect to Google Sheets
        gc = gspread.authorize(creds)
        print("[OK] Successfully authenticated with Google Sheets API")

        # Check if sheet exists
        sheet_id = os.getenv("MASTER_PROSPECT_LIST_SHEET_ID")

        if sheet_id:
            # Try to open existing sheet
            try:
                sheet = gc.open_by_key(sheet_id)
                print(f"[OK] Found existing sheet: {sheet.title}")
            except:
                print(f"[X] Could not open sheet with ID: {sheet_id}")
                sheet_id = None

        if not sheet_id:
            # Create new sheet
            print("Creating new Master Prospect List...")
            sheet = gc.create("SV Master Prospect List")
            sheet_id = sheet.id

            # Make it accessible
            sheet.share('', perm_type='anyone', role='writer')

            print(f"[OK] Created new sheet: {sheet.title}")
            print(f"[OK] Sheet ID: {sheet_id}")
            print(f"[OK] Sheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")

            # Update .env file with sheet ID
            env_path = Path(".env")
            env_content = env_path.read_text()

            if "MASTER_PROSPECT_LIST_SHEET_ID=" in env_content:
                # Replace empty value
                env_content = env_content.replace(
                    "MASTER_PROSPECT_LIST_SHEET_ID=",
                    f"MASTER_PROSPECT_LIST_SHEET_ID={sheet_id}"
                )
                env_path.write_text(env_content)
                print(f"[OK] Updated .env with Sheet ID")

        # Set up worksheet
        worksheet_name = os.getenv("MASTER_PROSPECT_LIST_SHEET_NAME", "Prospects")

        try:
            worksheet = sheet.worksheet(worksheet_name)
            print(f"[OK] Found existing worksheet: {worksheet_name}")
        except:
            worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            print(f"[OK] Created new worksheet: {worksheet_name}")

        # Add header row if empty
        if not worksheet.get('A1'):
            headers = [
                "prospect_id",
                "company_name",
                "canonical_url",
                "source_type",
                "date_evaluated",
                "confidence_level",
                "overall_score",
                "problem_buyer_clarity",
                "mvp_speed",
                "defensible_wedge",
                "venture_studio_fit",
                "canada_market_fit",
                "suggested_action",
                "primary_risks",
                "status",
                "notes"
            ]
            worksheet.append_row(headers)
            print(f"[OK] Added header row with {len(headers)} columns")

        print(f"\n[PASS] Google Sheets setup complete!")
        print(f"[INFO] Sheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        print()
        return True

    except ImportError as e:
        print(f"[X] Missing library: {e}")
        print("Run: pip install gspread google-auth google-auth-oauthlib google-auth-httplib2")
        print("\n[FAIL] Google Sheets test failed\n")
        return False
    except Exception as e:
        print(f"[X] Google Sheets error: {e}")
        print("\n[FAIL] Google Sheets test failed\n")
        return False


def main():
    """Run all setup tests."""
    print("\n" + "=" * 60)
    print("SV PIPELINE SETUP TEST")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Environment variables
    results.append(("Environment Variables", test_env_variables()))

    # Test 2: Temporary directory
    results.append(("Temporary Directory", test_tmp_directory()))

    # Test 3: OpenAI API
    results.append(("OpenAI API", test_openai_api()))

    # Test 4: Firecrawl API
    results.append(("Firecrawl API", test_firecrawl_api()))

    # Test 5: Google Sheets
    results.append(("Google Sheets API", test_google_sheets_and_create()))

    # Summary
    print("=" * 60)
    print("SETUP TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED - READY TO BUILD WORKFLOWS!")
        print("=" * 60 + "\n")
        return 0
    else:
        print("\n" + "=" * 60)
        print("SOME TESTS FAILED - PLEASE FIX BEFORE PROCEEDING")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
