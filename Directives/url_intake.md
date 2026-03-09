# URL Intake & Canonicalization

## Directive Layer: What This Workflow Does

This workflow standardizes and validates input URLs for processing by the SV pipeline.

---

## Goal

Transform a raw URL input into a canonical, validated form with metadata about the source type.

---

## Inputs

- **Raw URL** (string): Any URL provided by the user
  - Examples:
    - `https://example.com`
    - `www.example.com`
    - `example.com`
    - `https://example.com/path?query=value#fragment`

---

## Processing Steps

1. **Normalize URL**
   - Add `https://` if no protocol specified
   - Remove trailing slashes
   - Convert to lowercase (except path/query)
   - Handle redirects (optional, check if needed)

2. **Validate URL**
   - Check URL is well-formed
   - Verify domain exists (DNS lookup optional)
   - Reject invalid URLs with clear error message

3. **Detect Source Type**
   - Classify URL into categories:
     - `website` - Standard company website
     - `yc_profile` - Y Combinator company page
     - `pitch_deck` - PDF pitch deck
     - `notion` - Notion page
     - `article` - News article or blog post
     - `linkedin` - LinkedIn company page
     - `unknown` - Cannot determine

4. **Generate Prospect ID**
   - Create stable identifier from URL
   - Use domain + hash for uniqueness
   - Format: `{domain}_{hash8}` (e.g., `example_com_a1b2c3d4`)

---

## Outputs

**File:** `.tmp/{prospect_id}/canonical_url.json`

**Schema:**
```json
{
  "prospect_id": "string",
  "raw_url": "string",
  "canonical_url": "string",
  "source_type": "website|yc_profile|pitch_deck|notion|article|linkedin|unknown",
  "domain": "string",
  "timestamp": "ISO 8601 datetime",
  "valid": true
}
```

**Example:**
```json
{
  "prospect_id": "example_com_a1b2c3d4",
  "raw_url": "example.com",
  "canonical_url": "https://example.com",
  "source_type": "website",
  "domain": "example.com",
  "timestamp": "2025-12-28T10:30:00Z",
  "valid": true
}
```

---

## Execution Tool

**Script:** `Executions/url_intake.py`

**Usage:**
```bash
python Executions/url_intake.py <raw_url>
```

**Returns:** Exit code 0 on success, 1 on failure

---

## Edge Cases

1. **Invalid URL**
   - Log error with reason
   - Return `valid: false` in output
   - Do not proceed to next workflow

2. **Already Processed**
   - Check if `.tmp/{prospect_id}/canonical_url.json` exists
   - If valid and recent (<24h), skip processing
   - Otherwise, regenerate

3. **URL Redirects**
   - Follow redirects (max 5 hops)
   - Use final destination as canonical URL
   - Log redirect chain for debugging

4. **PDF URLs**
   - Detect `.pdf` extension
   - Classify as `pitch_deck`
   - Validate PDF is accessible

---

## Success Criteria

- URL is validated and normalized
- Source type is detected (or marked `unknown`)
- Prospect ID is generated consistently
- Output JSON exists and is valid
- No crashes or unhandled exceptions

---

## Self-Annealing Notes

**Common Failures:**
- DNS lookup timeout → Add timeout configuration
- Invalid URL format → Improve regex validation
- Redirect loop → Set max redirect limit

**Learnings from testing will be added here.**
