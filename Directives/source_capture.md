# Source Capture (Web Scraping)

## Directive Layer: What This Workflow Does

This workflow captures raw content from URLs and stores it for processing by downstream workflows.

---

## Goal

Fetch and store clean, readable content from a URL (website, PDF, etc.) in a consistent format.

---

## Inputs

**Required:** `.tmp/{prospect_id}/canonical_url.json`

Must contain:
- `canonical_url` - The URL to scrape
- `source_type` - Type of source (website, pitch_deck, etc.)
- `prospect_id` - Stable identifier

---

## Processing Steps

1. **Load Canonical URL**
   - Read from previous workflow output
   - Validate file exists and is valid

2. **Choose Scraping Method**
   - **Firecrawl API** (primary): Best for JavaScript-heavy sites
   - **Basic HTTP + BeautifulSoup** (fallback): For simple HTML
   - **PDF Extraction** (for pitch decks): Use pypdf

3. **Multi-Page Scraping Strategy** (NEW - addresses "lack of clarity" issue)
   - Scrape homepage first
   - Discover key pages from homepage links (about, team, pricing, product)
   - Scrape 2-3 additional key pages (to control costs)
   - Combine all content with section headers
   - Improves data quality for enrichment and evaluation

4. **Fetch Content**
   - Make HTTP request or API call
   - Handle timeouts and errors gracefully
   - Add 1s delay between page requests (rate limiting)
   - Follow redirects (max 5)

5. **Extract Clean Text**
   - Remove scripts, styles, ads
   - Preserve structure (headings, paragraphs)
   - Convert to markdown format
   - Extract metadata (title, description)

6. **Store Raw Content**
   - Save combined markdown text from all pages
   - Save metadata (title, description, word count, pages_scraped)
   - Mark scrape method as "firecrawl_multipage"

---

## Outputs

**Directory:** `.tmp/{prospect_id}/raw_sources/`

**Files:**
1. `content.md` - Clean markdown content
2. `metadata.json` - Extracted metadata
3. `raw.html` (optional) - Original HTML for debugging

**metadata.json Schema:**
```json
{
  "title": "string",
  "description": "string | null",
  "word_count": "integer",
  "scraped_at": "ISO 8601 datetime",
  "scrape_method": "firecrawl|beautifulsoup|pdf",
  "success": true,
  "error": "string | null"
}
```

---

## Execution Tool

**Script:** `Executions/source_capture.py`

**Usage:**
```bash
python Executions/source_capture.py <prospect_id>
```

**Returns:** Exit code 0 on success, 1 on failure

---

## Edge Cases

1. **Already Scraped (Checkpointing)**
   - Check if `.tmp/{prospect_id}/raw_sources/content.md` exists
   - If exists and recent (<7 days), skip scraping
   - Otherwise, re-scrape

2. **JavaScript-Heavy Sites**
   - Try Firecrawl API first
   - If Firecrawl fails, return error (don't waste time on basic scraping)

3. **PDF Documents**
   - Download PDF to temp location
   - Extract text using pypdf
   - Convert to markdown format
   - Clean up temp file

4. **Rate Limiting / 429 Errors**
   - Respect API rate limits
   - Add exponential backoff (1s, 2s, 4s, 8s)
   - Log rate limit errors for debugging

5. **Invalid/Dead URLs**
   - Return error with HTTP status code
   - Save error to metadata.json
   - Mark as failed but don't crash

6. **Large Pages**
   - Limit content to first 50,000 words
   - Truncate if exceeded
   - Log truncation in metadata

---

## Success Criteria

- Content is fetched successfully
- Clean markdown is saved
- Metadata is extracted and saved
- No crashes on common errors
- Checkpointing works (skips re-scraping)

---

## Token/Cost Optimization

- Multi-page strategy: 3 pages per company (homepage + 2 key pages)
- Cache results for 7 days (avoid re-scraping)
- Firecrawl free tier: 500 scrapes/month
- **Updated cost estimate:** $0.12 per company (3 pages × $0.04/page) or free tier

---

## Self-Annealing Notes

**Common Failures:**
- Firecrawl API timeout → Increase timeout to 30s
- Invalid API response → Add better error handling
- PDF extraction failure → Fall back to "PDF could not be read"

**Learnings from testing will be added here.**
