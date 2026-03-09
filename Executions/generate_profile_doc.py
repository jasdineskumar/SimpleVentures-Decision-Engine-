#!/usr/bin/env python3
"""Generate Profile Document - Execution Layer"""

import sys, json, os
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_cloud import get_google_credentials

load_dotenv()

def load_data(prospect_id):
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    with open(tmp_dir / prospect_id / 'prospect_profile.json', 'r') as f:
        profile = json.load(f)
    with open(tmp_dir / prospect_id / 'sv_evaluation_record.json', 'r') as f:
        evaluation = json.load(f)

    # Load Canadian market research if available
    canadian_research = None
    research_file = tmp_dir / prospect_id / 'canadian_market_research.json'
    if research_file.exists():
        with open(research_file, 'r') as f:
            canadian_research = json.load(f)

    # Load unknown resolution if available
    resolution_data = None
    resolution_file = tmp_dir / prospect_id / 'unknown_resolution.json'
    if resolution_file.exists():
        with open(resolution_file, 'r') as f:
            resolution_data = json.load(f)

    return profile, evaluation, canadian_research, resolution_data

def score_indicator(score):
    """Return emoji indicator for score."""
    if score >= 4:
        return "🟢"
    elif score >= 3:
        return "🟡"
    elif score >= 2:
        return "🟠"
    else:
        return "🔴"

def get_decision(evaluation):
    """Determine decision based on score and action."""
    overall_score = evaluation.get('overall_score', 0)
    action = evaluation.get('suggested_action', 'monitor')

    if overall_score >= 4 or action == 'deeper_diligence':
        return "🎯 PRIORITIZE"
    elif overall_score >= 3 or action == 'outreach':
        return "🔍 INVESTIGATE"
    elif action == 'monitor':
        return "👀 WATCH"
    else:
        return "⏸️ PASS"

def render_markdown(profile, evaluation, canadian_research=None, resolution_data=None):
    """Render profile document as markdown for local storage."""
    overall_score = evaluation.get('overall_score', 0)
    decision = get_decision(evaluation)

    doc = f"""# Simple Ventures — Company Profile

**Company Name:** {profile.get('company_name', 'Unknown')}
**Canonical URL:** [{profile.get('canonical_url', '')}]({profile.get('canonical_url', '')})
**Source Type:** {profile.get('source_type', 'website')}
**Date Evaluated:** {evaluation.get('date_evaluated', '')[:10]}
**Confidence Level:** {evaluation.get('confidence_level', 'UNKNOWN')}

---

## 1. What the Company Does

**One-sentence description:**
> {profile.get('description_one_sentence', 'UNKNOWN')}

**Problem being addressed:**
> {profile.get('problem_statement', 'UNKNOWN')}

**Market signals:**
- **Target market:** {profile.get('market_signals', {}).get('target_market', 'UNKNOWN')}
- **Geographic focus:** {profile.get('market_signals', {}).get('geographic_focus', 'UNKNOWN')}
- **Market size indicators:** {profile.get('market_signals', {}).get('market_size_indicators', 'UNKNOWN')}

---

## 2. Target Customer & Buyer

**Primary customer:** {profile.get('primary_customer', 'UNKNOWN')}
**Primary buyer:** {profile.get('primary_buyer', 'UNKNOWN')}

**Customer context / job-to-be-done:**
{profile.get('customer_context', 'UNKNOWN')}

---

## 3. Core Product & Features

**Key features:**
"""

    features = profile.get('key_features', [])
    if features:
        for feature in features:
            doc += f"\n- {feature}"
    else:
        doc += "\n- No features documented"

    doc += f"""

**Product maturity:** {profile.get('product_maturity', 'UNKNOWN')}

**Traction signals:**
- **Customer indicators:** {profile.get('traction_signals', {}).get('customer_count_indicators', 'UNKNOWN')}
- **Revenue indicators:** {profile.get('traction_signals', {}).get('revenue_indicators', 'UNKNOWN')}
- **Growth indicators:** {profile.get('traction_signals', {}).get('growth_indicators', 'UNKNOWN')}

---

## 4. Business Model Signals

**Revenue model:** {profile.get('revenue_model', 'UNKNOWN')}
**Pricing signals:** {profile.get('pricing_signals', 'Not disclosed')}
**Who pays:** {profile.get('who_pays', 'UNKNOWN')}

---

## 5. Simple Ventures Evaluation Snapshot

### 5.1 Scorecard

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| **Problem & Buyer Clarity** | {score_indicator(evaluation['scores']['problem_buyer_clarity']['score'])} **{evaluation['scores']['problem_buyer_clarity']['score']}/5** | {evaluation['scores']['problem_buyer_clarity']['rationale']} |
| **MVP Speed (3–6 mo)** | {score_indicator(evaluation['scores']['mvp_speed']['score'])} **{evaluation['scores']['mvp_speed']['score']}/5** | {evaluation['scores']['mvp_speed']['rationale']} |
| **Defensible Wedge** | {score_indicator(evaluation['scores']['defensible_wedge']['score'])} **{evaluation['scores']['defensible_wedge']['score']}/5** | {evaluation['scores']['defensible_wedge']['rationale']} |
| **Venture Studio Fit** | {score_indicator(evaluation['scores']['venture_studio_fit']['score'])} **{evaluation['scores']['venture_studio_fit']['score']}/5** | {evaluation['scores']['venture_studio_fit']['rationale']} |
| **Canada Market Fit** | {score_indicator(evaluation['scores']['canada_market_fit']['score'])} **{evaluation['scores']['canada_market_fit']['score']}/5** | {evaluation['scores']['canada_market_fit']['rationale']} |

**Composite Score:** {score_indicator(overall_score)} **{overall_score}/5.0**
**Decision:** {decision}

### 5.2 Summary Assessment

{evaluation.get('action_reasoning', 'No summary provided.')}

---

## 6. Key Risks & Unknowns

**Primary risks:**
"""

    risks = evaluation.get('primary_risks', [])
    if risks:
        for i, risk in enumerate(risks, 1):
            doc += f"\n{i}. {risk}"
    else:
        doc += "\n- No specific risks identified"

    doc += "\n\n**Unknowns / missing information:**\n"

    unknowns = evaluation.get('unknowns', [])
    if unknowns:
        for i, unknown in enumerate(unknowns, 1):
            doc += f"\n{i}. {unknown}"
    else:
        doc += "\n- No major unknowns"

    doc += f"""

**Confidence notes:** Data confidence rated as {evaluation.get('confidence_level', 'UNKNOWN')} based on depth and quality of available information.

---

## 7. Suggested Next Action

**Action:** `{evaluation.get('suggested_action', 'UNKNOWN').upper()}`

**Reasoning:**
{evaluation.get('action_reasoning', 'N/A')}

**Recommended next steps:**
"""

    action = evaluation.get('suggested_action', 'monitor')
    if action == 'deeper_diligence':
        doc += """
1. Schedule founder interview to validate market insights
2. Request detailed metrics (CAC, LTV, retention)
3. Conduct competitive landscape analysis"""
    elif action == 'outreach':
        doc += """
1. Request introduction through network
2. Review pitch deck if available
3. Assess founder background and team strength"""
    elif action == 'monitor':
        doc += """
1. Add to monitoring list for quarterly review
2. Track product updates and traction signals
3. Monitor for funding announcements or market changes"""
    else:  # reject
        doc += """
1. Archive with reasoning documented
2. Re-evaluate if market conditions change significantly
3. Consider pivot opportunities if they emerge"""

    doc += """

---

## 8. Evidence & Sources

**Primary sources reviewed:**
"""

    sources = profile.get('sources_reviewed', [])
    if sources:
        for source in sources:
            doc += f"\n- [{source}]({source})"
    else:
        doc += "\n- No sources documented"

    excerpts = profile.get('key_excerpts', [])
    if excerpts:
        doc += "\n\n**Key evidence:**\n"
        for excerpt in excerpts[:3]:
            claim = excerpt.get('claim', '')
            quote = excerpt.get('quote', '')
            doc += f"\n- **{claim}**\n  > \"{quote}\"\n"

    doc += f"""

---

**Evaluation Metadata:**
- Model: {evaluation.get('evaluation_metadata', {}).get('model_used', 'unknown')}
- Tokens: {evaluation.get('evaluation_metadata', {}).get('tokens_used', 0):,}
- Enrichment model: {profile.get('enrichment_metadata', {}).get('model_used', 'unknown')}
- Pages scraped: {len(profile.get('sources_reviewed', []))}

*Generated by SV Pipeline*
"""

    # Append Canadian Market Research if available
    if canadian_research:
        doc += "\n\n---\n\n## 9. Canadian Market Research\n\n"
        doc += canadian_research.get('structured_output', '')

    # Append Unknown Resolution if available
    if resolution_data:
        section_num = 10 if canadian_research else 9
        doc += f"\n\n---\n\n## {section_num}. AI-Resolved Unknowns\n\n"

        resolution_info = resolution_data.get('resolution_data', {})
        improvement = resolution_info.get('overall_improvement', {})

        doc += f"""**Resolution Summary:**
- Fields resolved: {improvement.get('fields_resolved', 0)}
- Unknowns addressed: {improvement.get('unknowns_addressed', 0)}
- Resolution confidence: {improvement.get('resolution_confidence', 'N/A')}
- Model used: {resolution_data.get('usage_stats', {}).get('model', 'unknown')}
- Reasoning tokens: {resolution_data.get('usage_stats', {}).get('reasoning_tokens', 0):,}

"""

        # Show resolved fields
        resolved_fields = resolution_info.get('resolved_fields', {})
        if resolved_fields:
            doc += "**Resolved Profile Fields:**\n\n"
            for field_path, resolution in resolved_fields.items():
                doc += f"**{field_path}:**\n"
                doc += f"- Original: `{resolution.get('original_value', 'UNKNOWN')}`\n"
                doc += f"- Resolved: {resolution.get('resolved_value', 'N/A')}\n"
                doc += f"- Confidence: {resolution.get('confidence', 'N/A')}\n"
                doc += f"- Reasoning: {resolution.get('reasoning', 'N/A')}\n\n"

        # Show resolved unknowns from evaluation
        resolved_unknowns = resolution_info.get('resolved_unknowns', [])
        if resolved_unknowns:
            doc += "**Addressed Evaluation Unknowns:**\n\n"
            for i, resolution in enumerate(resolved_unknowns, 1):
                doc += f"{i}. **{resolution.get('unknown_factor', 'N/A')}**\n"
                doc += f"   - Resolution: {resolution.get('resolution', 'N/A')}\n"
                doc += f"   - Confidence: {resolution.get('confidence', 'N/A')}\n"
                doc += f"   - Reasoning: {resolution.get('reasoning', 'N/A')}\n\n"

        if improvement.get('notes'):
            doc += f"\n**Additional Notes:** {improvement.get('notes')}\n"

        doc += f"\n*AI resolution completed on {resolution_data.get('resolved_at', '')[:10]}*\n"

    return doc


def create_google_doc(profile, evaluation, canadian_research=None, resolution_data=None):
    """Create a professionally formatted Google Doc (clean, no markdown syntax)."""
    # Load credentials (service account for cloud compatibility)
    creds = get_google_credentials()

    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Create document
    company_name = profile.get('company_name', 'Unknown')
    doc_title = f"SV Profile - {company_name}"

    doc = docs_service.documents().create(body={'title': doc_title}).execute()
    doc_id = doc.get('documentId')

    print(f"[OK] Created Google Doc: {doc_title}")
    print(f"[INFO] Doc ID: {doc_id}")

    # Build formatting requests
    requests = []
    index = 1  # Google Docs API index starts at 1

    overall_score = evaluation.get('overall_score', 0)
    decision = get_decision(evaluation)

    # === TITLE ===
    title_text = "Simple Ventures — Company Profile\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': title_text}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(title_text)},
            'paragraphStyle': {'namedStyleType': 'TITLE', 'alignment': 'CENTER'},
            'fields': 'namedStyleType,alignment'
        }
    })
    index += len(title_text)

    # === HEADER INFO ===
    header_lines = [
        f"Company Name: {profile.get('company_name', 'Unknown')}\n",
        f"Canonical URL: {profile.get('canonical_url', '')}\n",
        f"Source Type: {profile.get('source_type', 'website')}\n",
        f"Date Evaluated: {evaluation.get('date_evaluated', '')[:10]}\n",
        f"Confidence Level: {evaluation.get('confidence_level', 'UNKNOWN')}\n\n"
    ]

    for line in header_lines:
        requests.append({'insertText': {'location': {'index': index}, 'text': line}})
        # Bold the label part (before colon)
        if ':' in line:
            label_end = line.index(':') + index + 1
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': index, 'endIndex': label_end},
                    'textStyle': {'bold': True},
                    'fields': 'bold'
                }
            })
        index += len(line)

    # === SECTION 1: What the Company Does ===
    section1_title = "1. What the Company Does\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section1_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section1_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section1_title)

    section1_content = f"""One-sentence description:
{profile.get('description_one_sentence', 'UNKNOWN')}

Problem being addressed:
{profile.get('problem_statement', 'UNKNOWN')}

Market signals:
• Target market: {profile.get('market_signals', {}).get('target_market', 'UNKNOWN')}
• Geographic focus: {profile.get('market_signals', {}).get('geographic_focus', 'UNKNOWN')}
• Market size indicators: {profile.get('market_signals', {}).get('market_size_indicators', 'UNKNOWN')}

"""

    requests.append({'insertText': {'location': {'index': index}, 'text': section1_content}})
    index += len(section1_content)

    # === SECTION 2: Target Customer & Buyer ===
    section2_title = "2. Target Customer & Buyer\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section2_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section2_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section2_title)

    section2_content = f"""Primary customer: {profile.get('primary_customer', 'UNKNOWN')}
Primary buyer: {profile.get('primary_buyer', 'UNKNOWN')}

Customer context / job-to-be-done:
{profile.get('customer_context', 'UNKNOWN')}

"""

    requests.append({'insertText': {'location': {'index': index}, 'text': section2_content}})
    index += len(section2_content)

    # === SECTION 3: Core Product & Features ===
    section3_title = "3. Core Product & Features\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section3_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section3_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section3_title)

    section3_content = "Key features:\n"
    features = profile.get('key_features', [])
    if features:
        for feature in features:
            section3_content += f"• {feature}\n"
    else:
        section3_content += "• No features documented\n"

    section3_content += f"""
Product maturity: {profile.get('product_maturity', 'UNKNOWN')}

Traction signals:
• Customer indicators: {profile.get('traction_signals', {}).get('customer_count_indicators', 'UNKNOWN')}
• Revenue indicators: {profile.get('traction_signals', {}).get('revenue_indicators', 'UNKNOWN')}
• Growth indicators: {profile.get('traction_signals', {}).get('growth_indicators', 'UNKNOWN')}

"""

    requests.append({'insertText': {'location': {'index': index}, 'text': section3_content}})
    index += len(section3_content)

    # === SECTION 4: Business Model ===
    section4_title = "4. Business Model Signals\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section4_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section4_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section4_title)

    section4_content = f"""Revenue model: {profile.get('revenue_model', 'UNKNOWN')}
Pricing signals: {profile.get('pricing_signals', 'Not disclosed')}
Who pays: {profile.get('who_pays', 'UNKNOWN')}

"""

    requests.append({'insertText': {'location': {'index': index}, 'text': section4_content}})
    index += len(section4_content)

    # === SECTION 5: SV Evaluation ===
    section5_title = "5. Simple Ventures Evaluation Snapshot\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section5_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section5_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section5_title)

    # Scorecard (using clean text format instead of complex table)
    scorecard_title = "Scorecard\n\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': scorecard_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(scorecard_title) - 1},
            'paragraphStyle': {'namedStyleType': 'HEADING_2'},
            'fields': 'namedStyleType'
        }
    })
    index += len(scorecard_title)

    # Format scorecard as clean list with clear structure
    scores = evaluation.get('scores', {})

    scorecard_content = f"""Problem & Buyer Clarity: {score_indicator(scores['problem_buyer_clarity']['score'])} {scores['problem_buyer_clarity']['score']}/5
{scores['problem_buyer_clarity']['rationale']}

MVP Speed (3–6 mo): {score_indicator(scores['mvp_speed']['score'])} {scores['mvp_speed']['score']}/5
{scores['mvp_speed']['rationale']}

Defensible Wedge: {score_indicator(scores['defensible_wedge']['score'])} {scores['defensible_wedge']['score']}/5
{scores['defensible_wedge']['rationale']}

Venture Studio Fit: {score_indicator(scores['venture_studio_fit']['score'])} {scores['venture_studio_fit']['score']}/5
{scores['venture_studio_fit']['rationale']}

Canada Market Fit: {score_indicator(scores['canada_market_fit']['score'])} {scores['canada_market_fit']['score']}/5
{scores['canada_market_fit']['rationale']}

"""

    requests.append({'insertText': {'location': {'index': index}, 'text': scorecard_content}})

    # Bold the dimension labels
    current_index = index
    for dimension in ['Problem & Buyer Clarity:', 'MVP Speed (3–6 mo):', 'Defensible Wedge:', 'Venture Studio Fit:', 'Canada Transferability:']:
        dim_start = scorecard_content.find(dimension, current_index - index)
        if dim_start >= 0:
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': index + dim_start, 'endIndex': index + dim_start + len(dimension)},
                    'textStyle': {'bold': True},
                    'fields': 'bold'
                }
            })

    index += len(scorecard_content)

    # Composite score
    composite_text = f"\nComposite Score: {score_indicator(overall_score)} {overall_score}/5.0\nDecision: {decision}\n\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': composite_text}})
    requests.append({
        'updateTextStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(composite_text)},
            'textStyle': {'bold': True, 'fontSize': {'magnitude': 12, 'unit': 'PT'}},
            'fields': 'bold,fontSize'
        }
    })
    index += len(composite_text)

    # Summary assessment
    summary_title = "Summary Assessment\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': summary_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(summary_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_2'},
            'fields': 'namedStyleType'
        }
    })
    index += len(summary_title)

    summary_content = f"{evaluation.get('action_reasoning', 'No summary provided.')}\n\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': summary_content}})
    index += len(summary_content)

    # === SECTION 6: Risks & Unknowns ===
    section6_title = "6. Key Risks & Unknowns\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section6_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section6_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section6_title)

    section6_content = "Primary risks:\n"
    risks = evaluation.get('primary_risks', [])
    if risks:
        for i, risk in enumerate(risks, 1):
            section6_content += f"{i}. {risk}\n"
    else:
        section6_content += "• No specific risks identified\n"

    section6_content += "\nUnknowns / missing information:\n"
    unknowns = evaluation.get('unknowns', [])
    if unknowns:
        for i, unknown in enumerate(unknowns, 1):
            section6_content += f"{i}. {unknown}\n"
    else:
        section6_content += "• No major unknowns\n"

    section6_content += f"\nConfidence notes: Data confidence rated as {evaluation.get('confidence_level', 'UNKNOWN')} based on depth and quality of available information.\n\n"

    requests.append({'insertText': {'location': {'index': index}, 'text': section6_content}})
    index += len(section6_content)

    # === SECTION 7: Next Action ===
    section7_title = "7. Suggested Next Action\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section7_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section7_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section7_title)

    action = evaluation.get('suggested_action', 'UNKNOWN').upper()
    section7_content = f"Action: {action}\n\nReasoning:\n{evaluation.get('action_reasoning', 'N/A')}\n\nRecommended next steps:\n"

    action_type = evaluation.get('suggested_action', 'monitor')
    if action_type == 'deeper_diligence':
        section7_content += "1. Schedule founder interview to validate market insights\n2. Request detailed metrics (CAC, LTV, retention)\n3. Conduct competitive landscape analysis\n\n"
    elif action_type == 'outreach':
        section7_content += "1. Request introduction through network\n2. Review pitch deck if available\n3. Assess founder background and team strength\n\n"
    elif action_type == 'monitor':
        section7_content += "1. Add to monitoring list for quarterly review\n2. Track product updates and traction signals\n3. Monitor for funding announcements or market changes\n\n"
    else:
        section7_content += "1. Archive with reasoning documented\n2. Re-evaluate if market conditions change significantly\n3. Consider pivot opportunities if they emerge\n\n"

    requests.append({'insertText': {'location': {'index': index}, 'text': section7_content}})
    index += len(section7_content)

    # === SECTION 8: Evidence & Sources ===
    section8_title = "8. Evidence & Sources\n"
    requests.append({'insertText': {'location': {'index': index}, 'text': section8_title}})
    requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': index, 'endIndex': index + len(section8_title)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }
    })
    index += len(section8_title)

    section8_content = "Primary sources reviewed:\n"
    sources = profile.get('sources_reviewed', [])
    if sources:
        for source in sources:
            section8_content += f"• {source}\n"
    else:
        section8_content += "• No sources documented\n"

    section8_content += f"\n\nEvaluation Metadata:\n• Model: {evaluation.get('evaluation_metadata', {}).get('model_used', 'unknown')}\n• Tokens: {evaluation.get('evaluation_metadata', {}).get('tokens_used', 0):,}\n• Enrichment model: {profile.get('enrichment_metadata', {}).get('model_used', 'unknown')}\n• Pages scraped: {len(profile.get('sources_reviewed', []))}\n\nGenerated by SV Pipeline\n"

    requests.append({'insertText': {'location': {'index': index}, 'text': section8_content}})
    index += len(section8_content)

    # === SECTION 9: Canadian Market Research (if available) ===
    if canadian_research:
        section9_title = "9. Canadian Market Research\n"
        requests.append({'insertText': {'location': {'index': index}, 'text': section9_title}})
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(section9_title)},
                'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                'fields': 'namedStyleType'
            }
        })
        index += len(section9_title)

        # Add structured research content directly (already in clean format)
        research_content = canadian_research.get('structured_output', '')
        research_content += "\n\n"

        requests.append({'insertText': {'location': {'index': index}, 'text': research_content}})

        # Add metadata footer for research
        research_meta = f"Research completed on {canadian_research.get('research_date', '')[:10]} using {canadian_research.get('model_used', 'gpt-4.1')} ({canadian_research.get('tokens_used', 0):,} tokens)\n"
        research_meta += f"Confidence Level: {canadian_research.get('confidence_level', 'MEDIUM')}\n\n"

        requests.append({'insertText': {'location': {'index': index + len(research_content)}, 'text': research_meta}})
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': index + len(research_content), 'endIndex': index + len(research_content) + len(research_meta)},
                'textStyle': {'italic': True, 'fontSize': {'magnitude': 9, 'unit': 'PT'}},
                'fields': 'italic,fontSize'
            }
        })

        index += len(research_content) + len(research_meta)

    # === SECTION: AI-Resolved Unknowns (if available) ===
    if resolution_data:
        section_num = 10 if canadian_research else 9
        resolution_title = f"{section_num}. AI-Resolved Unknowns\n"
        requests.append({'insertText': {'location': {'index': index}, 'text': resolution_title}})
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(resolution_title)},
                'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                'fields': 'namedStyleType'
            }
        })
        index += len(resolution_title)

        resolution_info = resolution_data.get('resolution_data', {})
        improvement = resolution_info.get('overall_improvement', {})

        # Summary section
        summary_text = "Resolution Summary\n"
        requests.append({'insertText': {'location': {'index': index}, 'text': summary_text}})
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(summary_text)},
                'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                'fields': 'namedStyleType'
            }
        })
        index += len(summary_text)

        summary_content = f"""Fields resolved: {improvement.get('fields_resolved', 0)}
Unknowns addressed: {improvement.get('unknowns_addressed', 0)}
Resolution confidence: {improvement.get('resolution_confidence', 'N/A')}
Model used: {resolution_data.get('usage_stats', {}).get('model', 'unknown')}
Reasoning tokens: {resolution_data.get('usage_stats', {}).get('reasoning_tokens', 0):,}

"""
        requests.append({'insertText': {'location': {'index': index}, 'text': summary_content}})
        index += len(summary_content)

        # Resolved fields
        resolved_fields = resolution_info.get('resolved_fields', {})
        if resolved_fields:
            fields_heading = "Resolved Profile Fields\n"
            requests.append({'insertText': {'location': {'index': index}, 'text': fields_heading}})
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': index, 'endIndex': index + len(fields_heading)},
                    'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                    'fields': 'namedStyleType'
                }
            })
            index += len(fields_heading)

            for field_path, resolution in resolved_fields.items():
                field_content = f"""{field_path}:
• Original: {resolution.get('original_value', 'UNKNOWN')}
• Resolved: {resolution.get('resolved_value', 'N/A')}
• Confidence: {resolution.get('confidence', 'N/A')}
• Reasoning: {resolution.get('reasoning', 'N/A')}

"""
                requests.append({'insertText': {'location': {'index': index}, 'text': field_content}})
                index += len(field_content)

        # Resolved unknowns
        resolved_unknowns = resolution_info.get('resolved_unknowns', [])
        if resolved_unknowns:
            unknowns_heading = "Addressed Evaluation Unknowns\n"
            requests.append({'insertText': {'location': {'index': index}, 'text': unknowns_heading}})
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': index, 'endIndex': index + len(unknowns_heading)},
                    'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                    'fields': 'namedStyleType'
                }
            })
            index += len(unknowns_heading)

            for i, resolution in enumerate(resolved_unknowns, 1):
                unknown_content = f"""{i}. {resolution.get('unknown_factor', 'N/A')}
   • Resolution: {resolution.get('resolution', 'N/A')}
   • Confidence: {resolution.get('confidence', 'N/A')}
   • Reasoning: {resolution.get('reasoning', 'N/A')}

"""
                requests.append({'insertText': {'location': {'index': index}, 'text': unknown_content}})
                index += len(unknown_content)

        # Additional notes
        if improvement.get('notes'):
            notes_text = f"\nAdditional Notes: {improvement.get('notes')}\n\n"
            requests.append({'insertText': {'location': {'index': index}, 'text': notes_text}})
            index += len(notes_text)

        # Footer
        resolution_footer = f"AI resolution completed on {resolution_data.get('resolved_at', '')[:10]}\n\n"
        requests.append({'insertText': {'location': {'index': index}, 'text': resolution_footer}})
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': index, 'endIndex': index + len(resolution_footer)},
                'textStyle': {'italic': True, 'fontSize': {'magnitude': 9, 'unit': 'PT'}},
                'fields': 'italic,fontSize'
            }
        })
        index += len(resolution_footer)

    # Execute all requests
    if requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

    # Make accessible
    drive_service.permissions().create(
        fileId=doc_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"[OK] Document accessible at: {doc_url}")

    return doc_id, doc_url


def main(prospect_id):
    print("="*60)
    print("GENERATE PROFILE DOCUMENT")
    print("="*60)

    profile, evaluation, canadian_research, resolution_data = load_data(prospect_id)
    print(f"[OK] Loaded data for {profile.get('company_name')}")

    if canadian_research:
        print(f"[OK] Canadian market research loaded (Confidence: {canadian_research.get('confidence_level', 'UNKNOWN')})")

    if resolution_data:
        improvement = resolution_data.get('resolution_data', {}).get('overall_improvement', {})
        print(f"[OK] Unknown resolution loaded ({improvement.get('fields_resolved', 0)} fields, {improvement.get('unknowns_addressed', 0)} unknowns)")

    # Render markdown for local storage
    markdown = render_markdown(profile, evaluation, canadian_research, resolution_data)
    print(f"[OK] Rendered profile document")

    # Save local markdown file
    tmp_dir = Path(os.getenv('TMP_DIR', './.tmp'))
    output_file = tmp_dir / prospect_id / 'sv_profile.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"[OK] Saved local copy to: {output_file}")

    # Create professionally formatted Google Doc
    doc_id, doc_url = create_google_doc(profile, evaluation, canadian_research, resolution_data)

    # Save doc URL to metadata
    doc_metadata = {
        'doc_id': doc_id,
        'doc_url': doc_url,
        'created_at': evaluation.get('date_evaluated')
    }
    metadata_file = tmp_dir / prospect_id / 'google_doc_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(doc_metadata, f, indent=2)
    print(f"[OK] Saved doc metadata")

    print("\n" + "="*60)
    print("PROFILE DOCUMENT COMPLETE")
    print("="*60)
    print(f"Company: {profile.get('company_name')}")
    print(f"Local File: {output_file}")
    print(f"Google Doc: {doc_url}")
    print("="*60 + "\n")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_profile_doc.py <prospect_id>")
        sys.exit(1)
    exit_code = main(sys.argv[1])
    sys.exit(exit_code)
