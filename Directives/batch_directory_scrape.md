# Batch Directory Scrape

## Goal
Scrape company listings from any directory source (YC batches, accelerator cohorts, VC portfolios, etc.) and extract website URLs for batch processing through the SV pipeline.

---

## Link Type Differentiation

### **Directory Link** (Use batch_directory_scrape.py)
A URL that contains a **LIST of multiple companies** to scrape:

**Examples:**
```
✓ https://www.ycombinator.com/companies?batch=Winter%202026
  → Directory: Lists 30+ companies from YC W26 batch

✓ https://www.producthunt.com/topics/ai
  → Directory: Lists AI products/companies

✓ https://www.crunchbase.com/lists/yc-companies/
  → Directory: Database of multiple YC companies

✓ https://example-vc.com/portfolio
  → Directory: VC firm's portfolio page with multiple companies
```

**Key Indicators:**
- URL contains query parameters (`?batch=`, `?category=`, `?page=`)
- Page shows multiple company cards/listings
- Has pagination or "load more" functionality
- Title mentions "companies", "portfolio", "directory", "batch"

---

### **Single Company Link** (Use sv_pipeline.py)
A URL for a **SINGLE specific company** to evaluate:

**Examples:**
```
✓ https://chasi.co/
  → Single company website

✓ https://www.ycombinator.com/companies/chasi
  → Single company profile (NOT the directory listing)

✓ https://www.producthunt.com/posts/example-product
  → Single product page (NOT the topic/category listing)

✓ https://example.com
  → Single company website
```

**Key Indicators:**
- URL is a root domain or specific company subdomain
- Page is about ONE company only
- Contains company-specific information (about, product, pricing)
- No list of other companies on the page

---

## Decision Guide

**Ask yourself:**
1. **Does this URL show MULTIPLE companies?** → Use `batch_directory_scrape.py`
2. **Does this URL show ONE company?** → Use `sv_pipeline.py`

**Quick Test:**
- Open the URL in browser
- Count how many different companies you see
- If > 1 company → It's a directory link
- If = 1 company → It's a single company link

---

## Input
Directory source configuration with one of:
- **YC Batch**: `{"source": "yc", "batch": "Winter 2026", "max_companies": 10}`
- **Product Hunt**: `{"source": "product_hunt", "topic": "AI", "max_companies": 20}`
- **Custom URL List**: `{"source": "csv", "file": "companies.csv"}`
- **Generic Directory**: `{"source": "custom", "url": "https://example.com/companies", "selectors": {...}}`

## Processing Steps

### 1. Source Detection
- Identify the directory source type
- Load appropriate scraping strategy
- Validate input parameters

### 2. Company Extraction
- Use Playwright for JavaScript-rendered pages
- Extract company data: name, website URL, description
- Handle pagination if needed
- Deduplicate entries

### 3. Data Validation
- Verify website URLs are valid
- Check for duplicates against existing prospects
- Filter out companies already processed

### 4. Output Generation
- Save to structured JSON format
- Include metadata (source, scrape date, count)
- Create batch processing queue

## Outputs

**File:** `.tmp/batch_scrapes/{source}_{timestamp}/companies.json`

**Schema:**
```json
{
  "source": {
    "type": "yc|product_hunt|csv|custom",
    "batch": "string (if applicable)",
    "url": "string",
    "scraped_at": "ISO 8601 datetime"
  },
  "companies": [
    {
      "name": "string",
      "website": "string",
      "description": "string (optional)",
      "source_url": "string (profile/listing URL)"
    }
  ],
  "metadata": {
    "total_found": "number",
    "total_valid": "number",
    "duplicates_removed": "number"
  }
}
```

**Example:**
```json
{
  "source": {
    "type": "yc",
    "batch": "Winter 2026",
    "url": "https://www.ycombinator.com/companies?batch=Winter%202026",
    "scraped_at": "2026-01-01T22:00:00Z"
  },
  "companies": [
    {
      "name": "Chasi",
      "website": "https://chasi.co/",
      "description": "AI concierge for equipment sales",
      "source_url": "https://www.ycombinator.com/companies/chasi"
    }
  ],
  "metadata": {
    "total_found": 34,
    "total_valid": 34,
    "duplicates_removed": 0
  }
}
```

## Execution Tool

**Script:** `Executions/batch_directory_scrape.py`

**Usage:**
```bash
# YC batch
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 10

# Product Hunt
python Executions/batch_directory_scrape.py --source product_hunt --topic AI --max 20

# CSV file
python Executions/batch_directory_scrape.py --source csv --file companies.csv

# Custom directory with config
python Executions/batch_directory_scrape.py --source custom --config scrape_config.json
```

**Returns:** Exit code 0 on success, outputs JSON file path

## Supported Sources

### 1. Y Combinator (YC)
- **URL Pattern:** `https://www.ycombinator.com/companies?batch={batch}`
- **Batches:** "Winter 2026", "Summer 2025", "W26", "S25", etc.
- **Strategy:** Navigate to listing → Extract company links → Visit each profile → Get website URL
- **Selectors:**
  - Company links: `a[href^="/companies/"]`
  - Company name: `h1`
  - Website link: `a:has-text("Website")`

### 2. Product Hunt
- **URL Pattern:** `https://www.producthunt.com/topics/{topic}`
- **Topics:** "AI", "SaaS", "Developer Tools", etc.
- **Strategy:** Load topic page → Scroll for lazy loading → Extract product cards
- **Rate Limits:** 100 requests/hour (implement throttling)

### 3. CSV Import
- **Format:** `name,website,description` (headers required)
- **Validation:** Check URL format, skip empty rows
- **No scraping needed:** Direct import

### 4. Custom Directory
- **Config Required:** JSON file with selectors
- **Example Config:**
```json
{
  "url": "https://example.com/startups",
  "pagination": {
    "type": "button|url",
    "selector": "button.next",
    "max_pages": 5
  },
  "selectors": {
    "company_card": ".company-item",
    "name": "h2.company-name",
    "website": "a.website-link",
    "description": "p.description"
  }
}
```

## Edge Cases

### 1. Already Processed Companies
- Check against Master Prospect List
- Skip if URL already exists (optional flag to override)
- Log skipped companies

### 2. Invalid/Missing Website URLs
- Log companies without websites
- Save to separate file for manual review
- Continue processing valid entries

### 3. Rate Limiting
- Implement exponential backoff
- Add delays between requests (1-3 seconds)
- Respect robots.txt

### 4. Dynamic/Infinite Scroll
- Detect lazy loading patterns
- Implement scroll-to-load strategy
- Set maximum scroll depth

### 5. Authentication Required
- Support for login credentials in `.env`
- Cookie-based session management
- API token authentication where available

## Performance Optimization

### 1. Parallel Processing
- Process multiple pages concurrently (max 3 tabs)
- Use connection pooling
- Batch API requests

### 2. Caching
- Cache directory listings for 24 hours
- Store scraped HTML for debugging
- Reuse browser contexts

### 3. Resource Management
- Close browser tabs after use
- Limit memory usage (browser headless mode)
- Clean up temp files after processing

## Success Criteria

- All company websites extracted successfully
- Output JSON is valid and well-formed
- No duplicate entries
- Failed scrapes logged with reasons
- Processing time < 5 seconds per company
- Memory usage < 500MB

## Integration with SV Pipeline

After scraping, use the batch pipeline:

```bash
# Scrape directory
python Executions/batch_directory_scrape.py --source yc --batch "Winter 2026" --max 10

# Process all companies through SV pipeline
python Executions/batch_sv_pipeline.py .tmp/batch_scrapes/yc_winter_2026_*/companies.json
```

## Self-Annealing Notes

**Common Failures:**
- YC page structure changed → Update selectors, version them
- Playwright timeout → Increase wait time, add retry logic
- Memory leak on long runs → Restart browser every N companies
- Invalid URLs → Add URL normalization step

**Optimizations Discovered:**
- Opening multiple tabs causes context issues → Use new context per page
- Some sites block headless browsers → Add user agent spoofing
- Rate limits hit at 50 req/min → Implement 2s delay between requests

**Learnings from testing will be added here.**
