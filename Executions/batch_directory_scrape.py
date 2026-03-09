#!/usr/bin/env python3
"""
Batch Directory Scrape - Extract companies from any directory source

Supports:
- Y Combinator batches
- Product Hunt topics
- CSV imports
- Custom directories with config
"""

import sys
import os
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from playwright.sync_api import sync_playwright
import csv

# Load environment
from dotenv import load_dotenv
load_dotenv()

TMP_DIR = Path(os.getenv('TMP_DIR', './.tmp'))


class BatchDirectoryScraper:
    """Scrapes company directories and extracts website URLs"""

    def __init__(self, max_companies: int = 50):
        self.max_companies = max_companies
        self.companies = []
        self.metadata = {
            'total_found': 0,
            'total_valid': 0,
            'duplicates_removed': 0
        }

    def scrape_yc_batch(self, batch: str) -> List[Dict]:
        """Scrape Y Combinator batch"""
        print(f"[INFO] Scraping YC batch: {batch}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            # Navigate to YC directory
            url = f"https://www.ycombinator.com/companies?batch={batch.replace(' ', '%20')}"
            print(f"[INFO] Loading: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            # Get company links
            company_links = page.query_selector_all('a[href^="/companies/"]')
            unique_paths = list(set([link.get_attribute('href') for link in company_links if link.get_attribute('href')]))

            print(f"[INFO] Found {len(unique_paths)} unique companies")
            self.metadata['total_found'] = len(unique_paths)

            # Extract company data
            companies = []
            for i, company_path in enumerate(unique_paths[:self.max_companies], 1):
                try:
                    company_url = f"https://www.ycombinator.com{company_path}"
                    print(f"[{i}/{min(len(unique_paths), self.max_companies)}] {company_url}")

                    # Open company page
                    company_page = context.new_page()
                    company_page.goto(company_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(1)

                    # Extract name
                    name = "Unknown"
                    try:
                        name_elem = company_page.query_selector('h1')
                        if name_elem:
                            name = name_elem.inner_text().strip()
                    except:
                        pass

                    # Extract website
                    website = None
                    website_selectors = [
                        'a.group.flex:has-text("Website")',
                        'a:has-text("Website")',
                        'a[target="_blank"][rel*="noopener"]',
                    ]

                    for selector in website_selectors:
                        try:
                            links = company_page.query_selector_all(selector)
                            for link in links:
                                href = link.get_attribute('href')
                                if href and href.startswith('http') and 'ycombinator.com' not in href:
                                    website = href
                                    break
                            if website:
                                break
                        except:
                            continue

                    # Extract description
                    description = ""
                    try:
                        desc_elem = company_page.query_selector('.prose, p')
                        if desc_elem:
                            description = desc_elem.inner_text().strip()[:200]
                    except:
                        pass

                    company_page.close()

                    if website:
                        companies.append({
                            'name': name,
                            'website': website,
                            'description': description,
                            'source_url': company_url
                        })
                        print(f"    [OK] {name}: {website}")
                    else:
                        print(f"    [SKIP] {name}: No website found")

                    # Rate limiting
                    time.sleep(1.5)

                except Exception as e:
                    print(f"    [ERROR] {e}")
                    continue

            browser.close()
            self.metadata['total_valid'] = len(companies)
            return companies

    def scrape_product_hunt(self, topic: str) -> List[Dict]:
        """Scrape Product Hunt topic"""
        print(f"[INFO] Scraping Product Hunt topic: {topic}")
        print("[WARN] Product Hunt scraping not yet implemented")
        # TODO: Implement Product Hunt scraping
        return []

    def import_from_csv(self, filepath: str) -> List[Dict]:
        """Import companies from CSV file"""
        print(f"[INFO] Importing from CSV: {filepath}")

        companies = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'website' in row and row['website']:
                    companies.append({
                        'name': row.get('name', 'Unknown'),
                        'website': row['website'].strip(),
                        'description': row.get('description', ''),
                        'source_url': row.get('source_url', '')
                    })

        self.metadata['total_found'] = len(companies)
        self.metadata['total_valid'] = len(companies)
        print(f"[OK] Imported {len(companies)} companies")
        return companies

    def scrape_custom(self, config_file: str) -> List[Dict]:
        """Scrape custom directory using config"""
        print(f"[INFO] Scraping custom directory from config: {config_file}")

        with open(config_file, 'r') as f:
            config = json.load(f)

        url = config['url']
        selectors = config['selectors']

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"[INFO] Loading: {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3)

            # Extract companies using selectors
            companies = []
            company_cards = page.query_selector_all(selectors['company_card'])

            for card in company_cards[:self.max_companies]:
                try:
                    name_elem = card.query_selector(selectors['name'])
                    website_elem = card.query_selector(selectors['website'])

                    name = name_elem.inner_text().strip() if name_elem else "Unknown"
                    website = website_elem.get_attribute('href') if website_elem else None

                    if website:
                        description = ""
                        if 'description' in selectors:
                            desc_elem = card.query_selector(selectors['description'])
                            description = desc_elem.inner_text().strip()[:200] if desc_elem else ""

                        companies.append({
                            'name': name,
                            'website': website,
                            'description': description,
                            'source_url': url
                        })

                except Exception as e:
                    print(f"[WARN] Error extracting company: {e}")
                    continue

            browser.close()
            self.metadata['total_found'] = len(companies)
            self.metadata['total_valid'] = len(companies)
            return companies

    def deduplicate(self, companies: List[Dict]) -> List[Dict]:
        """Remove duplicate companies by website URL"""
        seen_urls = set()
        unique_companies = []

        for company in companies:
            url = company['website'].lower().strip().rstrip('/')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_companies.append(company)
            else:
                self.metadata['duplicates_removed'] += 1

        return unique_companies

    def save_output(self, companies: List[Dict], source_info: Dict) -> str:
        """Save scraped companies to JSON file"""
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_type = source_info['type']
        batch_name = source_info.get('batch', '').replace(' ', '_').lower() or 'custom'

        output_dir = TMP_DIR / 'batch_scrapes' / f"{source_type}_{batch_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare output data
        output = {
            'source': {
                **source_info,
                'scraped_at': datetime.now().isoformat()
            },
            'companies': companies,
            'metadata': self.metadata
        }

        # Save to file
        output_file = output_dir / 'companies.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        print(f"\n[OK] Saved {len(companies)} companies to: {output_file}")
        return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description='Scrape company directories for batch SV pipeline processing'
    )
    parser.add_argument('--source', required=True,
                        choices=['yc', 'product_hunt', 'csv', 'custom'],
                        help='Directory source type')
    parser.add_argument('--batch', help='YC batch name (e.g., "Winter 2026")')
    parser.add_argument('--topic', help='Product Hunt topic')
    parser.add_argument('--file', help='CSV file path')
    parser.add_argument('--config', help='Custom scraper config file')
    parser.add_argument('--max', type=int, default=50,
                        help='Maximum companies to scrape (default: 50)')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("BATCH DIRECTORY SCRAPE")
    print("="*60)

    scraper = BatchDirectoryScraper(max_companies=args.max)
    companies = []
    source_info = {'type': args.source}

    # Execute scraping based on source
    if args.source == 'yc':
        if not args.batch:
            print("[ERROR] --batch required for YC source")
            return 1
        source_info['batch'] = args.batch
        source_info['url'] = f"https://www.ycombinator.com/companies?batch={args.batch.replace(' ', '%20')}"
        companies = scraper.scrape_yc_batch(args.batch)

    elif args.source == 'product_hunt':
        if not args.topic:
            print("[ERROR] --topic required for Product Hunt source")
            return 1
        source_info['topic'] = args.topic
        source_info['url'] = f"https://www.producthunt.com/topics/{args.topic}"
        companies = scraper.scrape_product_hunt(args.topic)

    elif args.source == 'csv':
        if not args.file:
            print("[ERROR] --file required for CSV source")
            return 1
        source_info['file'] = args.file
        companies = scraper.import_from_csv(args.file)

    elif args.source == 'custom':
        if not args.config:
            print("[ERROR] --config required for custom source")
            return 1
        source_info['config'] = args.config
        companies = scraper.scrape_custom(args.config)

    # Deduplicate
    companies = scraper.deduplicate(companies)

    # Save output
    if companies:
        output_file = scraper.save_output(companies, source_info)

        # Summary
        print("\n" + "="*60)
        print("SCRAPE COMPLETE")
        print("="*60)
        print(f"Total Found: {scraper.metadata['total_found']}")
        print(f"Valid Websites: {scraper.metadata['total_valid']}")
        print(f"Duplicates Removed: {scraper.metadata['duplicates_removed']}")
        print(f"Final Count: {len(companies)}")
        print(f"Output: {output_file}")
        print("="*60 + "\n")

        return 0
    else:
        print("\n[ERROR] No companies scraped")
        return 1


if __name__ == "__main__":
    sys.exit(main())
