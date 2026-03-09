# Simple Ventures — DOE-Compliant Pipeline SOP

## Role of This Document (Directive Layer)

This document operates at the **Directive layer** of the DOE framework.

It defines:
- **What** Simple Ventures (SV) is trying to achieve
- **What artifacts must exist** for decision-making
- **How workflows relate**, without prescribing implementation details

This SOP does **not**:
- Perform orchestration
- Describe execution scripts
- Contain scraping, crawling, or tooling logic

Those responsibilities belong to the **Orchestration** and **Execution** layers respectively.

---

## 1. Purpose

The purpose of this SOP is to define a **repeatable, evidence-grounded pipeline** for evaluating company opportunities surfaced via URLs.

The system exists to:
- Standardize early-stage evaluation
- Enable comparison across opportunities
- Preserve institutional memory
- Reduce low-signal manual research

Final decisions remain **human-owned**.

---

## 2. Scope

This SOP applies to **any company opportunity provided as a URL**, including:
- Company websites
- Accelerator or YC profiles
- Pitch decks (PDF)
- Notion pages
- Articles or third-party descriptions

The pipeline must be source-agnostic.

---

## 3. Core Principles

1. **Separation of Concerns**
   - Directives define intent and required outcomes
   - Orchestration determines control flow
   - Execution performs deterministic work

2. **Evidence First**
   - The system may only reason over captured sources
   - Missing information must be labeled explicitly

3. **Comparability Over Completeness**
   - Outputs must enable side-by-side comparison
   - Exhaustive research is not a default goal

4. **Human Judgment Is Final**
   - The system narrows focus
   - Humans decide next actions

---

## 4. SV Evaluation Philosophy (Decision Criteria)

SV evaluates opportunities by consistently answering:

1. Is there a **clear problem and buyer**?
2. Can an **MVP be built and validated quickly** (≈3–6 months)?
3. Is there a **defensible wedge** (market, distribution, or economics)?
4. Is the opportunity suitable for a **venture studio model**?
5. Would this **type of business model work well in the Canadian market**? (Not whether this specific company should move to Canada, but whether a similar venture addressing the same problem would succeed in Canada)

These criteria guide evaluation but do not mandate outcomes.

---

## 5. Required Artifacts (Authoritative Outputs)

Every processed opportunity must produce the following artifacts.

These artifacts are the **single sources of truth** for SV decisions.

---

### 5.1 Prospect Profile (Structured, Neutral)

A factual representation of what is known about the company, derived solely from captured sources.

Characteristics:
- No scoring
- No evaluation
- Explicit UNKNOWN values where data is missing

**Format:** Structured JSON  
**Produced by:** Enrichment workflow  
**Consumed by:** Evaluation workflow

---

### 5.2 SV Evaluation Record

An application of SV criteria to the Prospect Profile.

Includes:
- Scored dimensions
- Short rationales
- Key risks and unknowns
- Confidence level (HIGH / MEDIUM / LOW)

**Format:** Structured JSON  
**Produced by:** Evaluation workflow  
**Consumed by:** Reporting and tracking

---

### 5.3 SV Profile Document (Human-Readable)

A concise, standardized document rendered from the structured artifacts.

Purpose:
- <2-minute review by partners
- Enable discussion and comparison
- No additional interpretation beyond structured data

**Format:** Markdown or PDF  
**Derived from:** Prospect Profile + SV Evaluation Record

---

### 5.4 Master Prospect List Entry

A single upserted record in SV’s master tracking system (e.g., Excel or Google Sheets).

Purpose:
- Comparison across opportunities
- Status tracking
- Institutional memory

**Keyed by:** Stable prospect identifier  
**Updated by:** Master list workflow

---

## 6. Workflow Composition (Directive-Level View)

This SOP defines **what workflows must exist**, not how they are implemented.

The SV pipeline is composed of the following independent workflows:

1. **URL Intake & Canonicalization**
2. **Source Capture**
3. **Data Enrichment (Profile Structuring)**
4. **SV Evaluation**
5. **Master Prospect List Update**

Each workflow:
- Has a single responsibility
- Produces explicit artifacts
- Can be executed independently or composed

An umbrella pipeline may orchestrate these workflows sequentially but must not duplicate their logic.

---

## 7. Evidence, Confidence, and Integrity Rules

- All non-obvious claims must be traceable to captured sources
- Speculation must be labeled or excluded
- Missing data must be marked UNKNOWN
- Each evaluation must include a confidence indicator
- Confidence reflects data quality, not attractiveness

---

## 8. Definition of “Processed”

An opportunity is considered processed when:
- A Prospect Profile exists
- An SV Evaluation Record exists
- An SV Profile document is generated
- The Master Prospect List is updated

At this point, the opportunity is ready for **human decision-making**.

---

## 9. Explicit Non-Goals

This SOP explicitly excludes:
- Automated investment decisions
- Unbounded or default “deep research”
- Market sizing speculation without data
- Narrative-heavy research reports

Optional deep research may be initiated **only after human interest** and must exist as a separate workflow and artifact.

---

## 10. Guiding Statement

> The SV pipeline exists to reduce noise, preserve judgment, and make tradeoffs visible.
>  
> It is a decision-support system, not a decision-maker.
