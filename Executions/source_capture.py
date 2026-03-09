#!/usr/bin/env python3
"""
Source Capture - Execution Layer

Fetches and stores clean content from URLs using Firecrawl API or fallback methods.
"""

import sys
import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()


def load_canonical_url(prospect_id: str) -> dict:
    """Load canonical URL data from previous workflow."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    canonical_file = tmp_dir / prospect_id / 'canonical_url.json'

    if not canonical_file.exists():
        raise FileNotFoundError(f"Canonical URL file not found: {canonical_file}")

    with open(canonical_file, 'r') as f:
        return json.load(f)


def check_existing_output(prospect_id: str, max_age_days: int = 7) -> tuple[bool, dict]:
    """
    Check if content already scraped (checkpointing).

    Returns: (exists_and_recent, metadata)
    """
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    sources_dir = tmp_dir / prospect_id / 'raw_sources'
    content_file = sources_dir / 'content.md'
    metadata_file = sources_dir / 'metadata.json'

    if not content_file.exists() or not metadata_file.exists():
        return False, {}

    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Check if successful scrape
        if not metadata.get('success', False):
            return False, metadata

        # Check if recent
        scraped_at = datetime.fromisoformat(metadata['scraped_at'])
        age_days = (datetime.now() - scraped_at).total_seconds() / 86400

        if age_days < max_age_days:
            return True, metadata

        return False, metadata

    except Exception:
        return False, {}


def scrape_single_url_with_firecrawl(url: str) -> tuple[bool, str, dict]:
    """
    Scrape a single URL using Firecrawl API.

    Returns: (success, content_markdown, metadata)
    """
    api_key = os.getenv('FIRECRAWL_API_KEY')

    if not api_key:
        return False, "", {"error": "Firecrawl API key not configured"}

    try:
        response = requests.post(
            "https://api.firecrawl.dev/v0/scrape",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "url": url,
                "formats": ["markdown", "html"],
                "onlyMainContent": True
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            # Firecrawl v0 response structure
            if 'data' in data:
                content = data['data'].get('markdown', '')
                metadata = data['data'].get('metadata', {})

                return True, content, {
                    "title": metadata.get('title', 'Untitled'),
                    "description": metadata.get('description'),
                    "scrape_method": "firecrawl"
                }

            return False, "", {"error": "Unexpected Firecrawl response format"}

        elif response.status_code == 429:
            return False, "", {"error": "Rate limit exceeded (Firecrawl)"}

        else:
            return False, "", {"error": f"Firecrawl API error: {response.status_code}"}

    except requests.Timeout:
        return False, "", {"error": "Firecrawl API timeout (30s)"}

    except Exception as e:
        return False, "", {"error": f"Firecrawl error: {str(e)}"}


def discover_key_pages(homepage_url: str, homepage_content: str) -> list[str]:
    """
    Discover key pages to scrape from homepage.

    Returns: list of URLs to scrape (about, team, pricing, product pages)
    """
    from urllib.parse import urljoin, urlparse
    import re

    base_domain = urlparse(homepage_url).netloc.replace('www.', '')
    key_pages = []

    # Common patterns for important pages (more flexible)
    patterns = {
        'about': r'/(about|our-story|company|who-we-are|mission)',
        'pricing': r'/(pricing|plans|subscribe|fees)',
        'product': r'/(product|features|solutions|how-it-works|platform)',
    }

    # Extract all markdown-style links from content
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', homepage_content)

    all_urls = [link[1] for link in markdown_links]

    found_categories = set()

    for url in all_urls:
        # Skip anchors, empty, or javascript
        if not url or url.startswith('#') or url.startswith('javascript:'):
            continue

        # Make absolute URL
        try:
            full_url = urljoin(homepage_url, url)
        except:
            continue

        # Only same domain (normalize www)
        parsed = urlparse(full_url)
        if parsed.netloc and parsed.netloc.replace('www.', '') != base_domain:
            continue

        # Remove query params and fragments for matching
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Check against patterns
        for category, pattern in patterns.items():
            if category not in found_categories and re.search(pattern, clean_url.lower()):
                key_pages.append(clean_url)
                found_categories.add(category)
                print(f"[INFO] Found {category} page: {clean_url}")
                break

        # Limit to 2 additional pages (homepage + 2 = 3 total)
        if len(key_pages) >= 2:
            break

    return key_pages


def scrape_with_firecrawl(url: str) -> tuple[bool, str, dict]:
    """
    Scrape URL using Firecrawl API with multi-page strategy.

    Scrapes homepage + 2-3 key pages (about, pricing, team, product).

    Returns: (success, content_markdown, metadata)
    """
    print("[INFO] Using Firecrawl API with multi-page strategy...")

    # Scrape homepage first
    print(f"[INFO] Scraping homepage: {url}")
    success, homepage_content, homepage_metadata = scrape_single_url_with_firecrawl(url)

    if not success:
        return False, "", homepage_metadata

    # Discover key pages
    key_pages = discover_key_pages(url, homepage_content)
    print(f"[INFO] Discovered {len(key_pages)} key pages to scrape")

    # Combine all content
    combined_content = f"# Homepage\n\n{homepage_content}\n\n"
    pages_scraped = ["homepage"]

    # Scrape additional pages (limit to 2 to control costs)
    for i, page_url in enumerate(key_pages[:2]):
        print(f"[INFO] Scraping additional page {i+1}: {page_url}")
        time.sleep(1)  # Rate limiting

        success, page_content, page_metadata = scrape_single_url_with_firecrawl(page_url)

        if success and page_content:
            page_title = page_metadata.get('title', f'Page {i+1}')
            combined_content += f"# {page_title}\n\n{page_content}\n\n"
            pages_scraped.append(page_url)
        else:
            print(f"[WARN] Failed to scrape {page_url}: {page_metadata.get('error', 'Unknown')}")

    print(f"[OK] Successfully scraped {len(pages_scraped)} pages")

    return True, combined_content, {
        "title": homepage_metadata.get('title', 'Untitled'),
        "description": homepage_metadata.get('description'),
        "scrape_method": "firecrawl_multipage",
        "pages_scraped": pages_scraped
    }


def scrape_with_beautifulsoup(url: str) -> tuple[bool, str, dict]:
    """
    Scrape URL using basic HTTP + BeautifulSoup (fallback).

    Returns: (success, content_text, metadata)
    """
    print("[INFO] Using BeautifulSoup fallback...")

    try:
        from bs4 import BeautifulSoup

        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SVBot/1.0)'
        })

        if response.status_code != 200:
            return False, "", {"error": f"HTTP {response.status_code}"}

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove scripts, styles, etc.
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside']):
            tag.decompose()

        # Extract metadata
        title = soup.find('title')
        title_text = title.get_text().strip() if title else 'Untitled'

        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag.get('content', '') if description_tag else None

        # Extract main content
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.body

        if main_content:
            # Convert to simple text
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        # Basic markdown conversion (paragraphs)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content = '\n\n'.join(lines)

        return True, content, {
            "title": title_text,
            "description": description,
            "scrape_method": "beautifulsoup"
        }

    except ImportError:
        return False, "", {"error": "BeautifulSoup not installed"}

    except Exception as e:
        return False, "", {"error": f"BeautifulSoup error: {str(e)}"}


def scrape_pdf(url: str) -> tuple[bool, str, dict]:
    """
    Download and extract text from PDF.

    Returns: (success, content_text, metadata)
    """
    print("[INFO] Extracting PDF content...")

    try:
        from pypdf import PdfReader
        import io

        # Download PDF
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SVBot/1.0)'
        })

        if response.status_code != 200:
            return False, "", {"error": f"HTTP {response.status_code}"}

        # Extract text from PDF
        pdf_file = io.BytesIO(response.content)
        reader = PdfReader(pdf_file)

        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())

        content = '\n\n'.join(text_parts)

        # Get metadata from PDF
        title = "PDF Document"
        if reader.metadata and reader.metadata.title:
            title = reader.metadata.title

        return True, content, {
            "title": title,
            "description": f"PDF with {len(reader.pages)} pages",
            "scrape_method": "pdf"
        }

    except ImportError:
        return False, "", {"error": "pypdf not installed"}

    except Exception as e:
        return False, "", {"error": f"PDF extraction error: {str(e)}"}


def save_output(prospect_id: str, content: str, metadata: dict):
    """Save scraped content and metadata."""
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    sources_dir = tmp_dir / prospect_id / 'raw_sources'
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Save content
    content_file = sources_dir / 'content.md'
    with open(content_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # Save metadata
    metadata_file = sources_dir / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Saved content to: {content_file}")
    print(f"[OK] Saved metadata to: {metadata_file}")


def main(prospect_id: str) -> int:
    """
    Main workflow: Source capture.

    Returns: 0 on success, 1 on failure
    """
    print("="*60)
    print("SOURCE CAPTURE")
    print("="*60)
    print(f"Prospect ID: {prospect_id}\n")

    # Step 1: Load canonical URL
    try:
        url_data = load_canonical_url(prospect_id)
        canonical_url = url_data['canonical_url']
        source_type = url_data['source_type']

        print(f"[OK] Loaded canonical URL")
        print(f"URL: {canonical_url}")
        print(f"Source Type: {source_type}\n")
    except Exception as e:
        print(f"[FAIL] Could not load canonical URL: {e}")
        return 1

    # Step 2: Check if already scraped (checkpointing)
    exists, existing_metadata = check_existing_output(prospect_id)
    if exists:
        print(f"[INFO] Already scraped (age < 7 days), skipping")
        print(f"[INFO] Using cached content from: .tmp/{prospect_id}/raw_sources/")
        print(f"\n" + "="*60)
        print("SOURCE CAPTURE COMPLETE (FROM CACHE)")
        print("="*60)
        print(f"Title: {existing_metadata.get('title', 'N/A')}")
        print(f"Word Count: {existing_metadata.get('word_count', 'N/A')}")
        print(f"Method: {existing_metadata.get('scrape_method', 'N/A')}")
        print("="*60 + "\n")
        return 0

    # Step 3: Choose scraping method based on source type
    success = False
    content = ""
    scrape_metadata = {}

    if source_type == 'pitch_deck':
        success, content, scrape_metadata = scrape_pdf(canonical_url)
    else:
        # Try Firecrawl first for websites
        success, content, scrape_metadata = scrape_with_firecrawl(canonical_url)

        # Fallback to BeautifulSoup if Firecrawl fails
        if not success and scrape_metadata.get('error') not in ['Rate limit exceeded (Firecrawl)']:
            print("[INFO] Firecrawl failed, trying BeautifulSoup fallback...")
            success, content, scrape_metadata = scrape_with_beautifulsoup(canonical_url)

    # Step 4: Handle scraping result
    if not success:
        print(f"[FAIL] Scraping failed: {scrape_metadata.get('error', 'Unknown error')}")

        # Save failed metadata
        failed_metadata = {
            "title": "Error",
            "description": None,
            "word_count": 0,
            "scraped_at": datetime.now().isoformat(),
            "scrape_method": scrape_metadata.get('scrape_method', 'unknown'),
            "success": False,
            "error": scrape_metadata.get('error', 'Unknown error')
        }
        save_output(prospect_id, "", failed_metadata)
        return 1

    # Step 5: Process content
    word_count = len(content.split())

    # Truncate if too long (>50,000 words)
    if word_count > 50000:
        print(f"[WARN] Content too long ({word_count} words), truncating to 50,000 words")
        words = content.split()
        content = ' '.join(words[:50000])
        word_count = 50000

    print(f"[OK] Content scraped successfully")
    print(f"Title: {scrape_metadata.get('title', 'Untitled')}")
    print(f"Word Count: {word_count}")
    print(f"Method: {scrape_metadata.get('scrape_method', 'unknown')}")

    # Step 6: Create final metadata
    final_metadata = {
        "title": scrape_metadata.get('title', 'Untitled'),
        "description": scrape_metadata.get('description'),
        "word_count": word_count,
        "scraped_at": datetime.now().isoformat(),
        "scrape_method": scrape_metadata.get('scrape_method', 'unknown'),
        "success": True,
        "error": None
    }

    # Step 7: Save output
    save_output(prospect_id, content, final_metadata)

    print("\n" + "="*60)
    print("SOURCE CAPTURE COMPLETE")
    print("="*60)
    print(f"Title: {final_metadata['title']}")
    print(f"Word Count: {final_metadata['word_count']}")
    print(f"Method: {final_metadata['scrape_method']}")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python source_capture.py <prospect_id>")
        print("Example: python source_capture.py example_com_a1b2c3d4")
        sys.exit(1)

    prospect_id = sys.argv[1]
    exit_code = main(prospect_id)
    sys.exit(exit_code)
