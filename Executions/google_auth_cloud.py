#!/usr/bin/env python3
"""
Google Authentication for Cloud Environments
Supports both local development and cloud deployment (Modal)
"""

import json
import os
from pathlib import Path
from google.oauth2 import service_account

# Scopes required for Google APIs
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]


def get_google_credentials():
    """
    Get Google credentials from service account.

    Works in both local and cloud (Modal) environments by checking
    multiple sources in order of preference:

    1. GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT env var (JSON string) - for Modal
    2. GOOGLE_SERVICE_ACCOUNT_JSON env var (file path) - for local
    3. ./service-account.json (default local path)

    Returns:
        google.oauth2.service_account.Credentials

    Raises:
        ValueError: If no valid credentials are found

    Example:
        >>> from google_auth_cloud import get_google_credentials
        >>> import gspread
        >>> creds = get_google_credentials()
        >>> gc = gspread.authorize(creds)
    """

    # Option 1: JSON content in environment variable (for Modal secrets)
    # This is the preferred method for cloud deployment
    sa_json_content = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
    if sa_json_content:
        try:
            sa_info = json.loads(sa_json_content)
            print("[INFO] Using service account from GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
            return service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=SCOPES
            )
        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT: {e}")
            # Fall through to next option

    # Option 2: JSON file path in environment variable
    sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_path:
        sa_path = Path(sa_path)
        if sa_path.exists():
            print(f"[INFO] Using service account from {sa_path}")
            return service_account.Credentials.from_service_account_file(
                str(sa_path),
                scopes=SCOPES
            )
        else:
            print(f"[WARN] GOOGLE_SERVICE_ACCOUNT_JSON points to non-existent file: {sa_path}")
            # Fall through to next option

    # Option 3: Default local path (./service-account.json)
    default_path = Path("./service-account.json")
    if default_path.exists():
        print(f"[INFO] Using service account from {default_path}")
        return service_account.Credentials.from_service_account_file(
            str(default_path),
            scopes=SCOPES
        )

    # No valid credentials found
    raise ValueError(
        "No Google service account credentials found. "
        "Please set one of the following:\n"
        "  1. GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT (JSON string, for Modal)\n"
        "  2. GOOGLE_SERVICE_ACCOUNT_JSON (path to JSON file)\n"
        "  3. Create ./service-account.json in the project root\n\n"
        "To create a service account:\n"
        "  1. Go to https://console.cloud.google.com\n"
        "  2. Create a service account\n"
        "  3. Download the JSON key\n"
        "  4. Share your Google Sheet/Drive with the service account email"
    )


def test_credentials():
    """
    Test that credentials work by attempting to authorize with gspread.

    Returns:
        bool: True if credentials work, False otherwise
    """
    try:
        import gspread
        creds = get_google_credentials()
        gc = gspread.authorize(creds)
        print("[OK] ✓ Google credentials are valid")
        print(f"[OK] ✓ Authorized as: {creds.service_account_email}")
        return True
    except Exception as e:
        print(f"[ERROR] ✗ Failed to authorize with Google: {e}")
        return False


if __name__ == "__main__":
    """
    Test the authentication when run directly.

    Usage:
        python Executions/google_auth_cloud.py
    """
    print("="*60)
    print("GOOGLE AUTHENTICATION TEST")
    print("="*60)

    try:
        creds = get_google_credentials()
        print(f"\n✓ Successfully loaded credentials")
        print(f"✓ Service account email: {creds.service_account_email}")
        print(f"✓ Scopes: {', '.join(SCOPES)}")

        print("\nTesting authorization with gspread...")
        if test_credentials():
            print("\n" + "="*60)
            print("✓ ALL TESTS PASSED - Ready for use!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("✗ Authorization failed - check service account permissions")
            print("="*60)
            exit(1)

    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("\n" + "="*60)
        print("✗ SETUP REQUIRED")
        print("="*60)
        exit(1)
