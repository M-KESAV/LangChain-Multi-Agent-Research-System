"""
Citation mapping, normalization, and validation utilities.

Ensures:
1. Every in-text citation [N] maps consistently to a numbered entry [N] in Sources & References.
2. Shorthand citations (e.g. [Domain], [Title], [URL]) are resolved to their numerical indices.
3. Every cited URL strictly belongs to a source returned by search/Tavily for that research run.
4. Out-of-bounds or fabricated citation indices are eliminated.
5. Zero-source research runs clearly state that no verified sources were found, without fabricated citations.
"""

import re
from urllib.parse import urlparse
from typing import Optional


def extract_domain_from_url(url: str) -> str:
    """Extracts a clean domain name without www or port."""
    try:
        netloc = urlparse(url).netloc
        netloc = netloc.split(":")[0]
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc.lower()
    except Exception:
        return ""


def validate_and_normalize_citations(report: str, sources: Optional[list[dict]] = None) -> tuple[str, dict]:
    """
    Validates and normalizes citations in a markdown research report against verified sources.

    Returns:
        (normalized_report, citation_metadata)
    """
    sources = sources or []
    metadata = {
        "sources_count": len(sources),
        "in_text_citations": [],
        "invalid_citations_removed": 0,
        "shorthand_citations_resolved": 0,
        "missing_sources": len(sources) == 0,
    }

    if not report or not isinstance(report, str):
        return report, metadata

    # Split report into body and existing Sources & References section (if any)
    sources_heading_pattern = re.compile(
        r"(?P<prefix>\n##\s+(?:Sources\s*&\s*References|References|Sources)\b[^\n]*\n)(?P<content>[\s\S]*)$",
        re.IGNORECASE
    )
    match = sources_heading_pattern.search(report)
    if match:
        body = report[:match.start()].rstrip()
    else:
        body = report.rstrip()

    # Case A: Zero sources discovered
    if not sources:
        # Remove any accidental in-text numerical citations [1], [2], etc. from body
        cleaned_body = re.sub(r'\[\d+\]', '', body)
        cleaned_body = re.sub(r'\s+([,\.])', r'\1', cleaned_body)  # Clean up spacing before punctuation

        references_section = (
            "\n\n## Sources & References\n"
            "*No external sources or URLs were discovered for this research topic; "
            "verified citations cannot be provided.*"
        )
        metadata["in_text_citations"] = []
        return cleaned_body + references_section, metadata

    # Case B: Valid sources present
    num_sources = len(sources)

    # Build lookup dictionaries for resolving shorthand in-text citations
    # e.g. [IDTechEx], [xnergy.us], [https://xnergy.us/guide]
    shorthand_to_idx = {}
    for idx, s in enumerate(sources, 1):
        url = s.get("url", "")
        title = s.get("title", "")
        domain = extract_domain_from_url(url)

        if url:
            shorthand_to_idx[url.lower()] = idx
        if domain:
            shorthand_to_idx[domain.lower()] = idx
            # Also without top-level domain e.g. "idtechex" from "idtechex.com"
            domain_name = domain.split(".")[0]
            if len(domain_name) > 2:
                shorthand_to_idx[domain_name.lower()] = idx
        if title:
            # First 1-3 prominent words of title
            words = [w.strip(",.-:()") for w in title.split() if len(w) > 3]
            if words:
                shorthand_to_idx[words[0].lower()] = idx
            if len(words) >= 2:
                shorthand_to_idx[f"{words[0]} {words[1]}".lower()] = idx

    # Resolve shorthand citations in body: e.g. [IDTechEx] -> [2]
    resolved_count = 0
    def replace_shorthand(m):
        nonlocal resolved_count
        inner = m.group(1).strip()
        # If it's already a number, leave it for numerical validation
        if inner.isdigit():
            return m.group(0)
        # Check lookup
        target_idx = shorthand_to_idx.get(inner.lower())
        if target_idx:
            resolved_count += 1
            return f"[{target_idx}]"
        # Check partial match on domain or title
        for key, idx in shorthand_to_idx.items():
            if len(key) >= 4 and (key in inner.lower() or inner.lower() in key):
                resolved_count += 1
                return f"[{idx}]"
        return m.group(0)

    # Match bracketed terms that are not markdown link anchors (e.g. not followed by '(')
    bracket_pattern = re.compile(r'\[([^\]\n]+)\](?!\()')
    body = bracket_pattern.sub(replace_shorthand, body)
    metadata["shorthand_citations_resolved"] = resolved_count

    # Extract all numerical citations in body
    citation_numbers = []
    removed_out_of_bounds = 0

    def validate_number(m):
        nonlocal removed_out_of_bounds
        num = int(m.group(1))
        if 1 <= num <= num_sources:
            citation_numbers.append(num)
            return f"[{num}]"
        else:
            # Out of bounds citation! Remove it to prevent hallucinated references
            removed_out_of_bounds += 1
            return ""

    body = re.sub(r'\[(\d+)\]', validate_number, body)
    metadata["invalid_citations_removed"] = removed_out_of_bounds
    metadata["in_text_citations"] = sorted(list(set(citation_numbers)))

    # Reconstruct canonical Sources & References section
    # Ensuring 1-to-1 consistent mapping with verified sources
    references_lines = ["\n\n## Sources & References\n"]
    for idx, s in enumerate(sources, 1):
        title = s.get("title", f"Source {idx}").strip()
        url = s.get("url", "").strip()
        snippet = s.get("snippet", "").strip()
        status = s.get("status", "discovered")

        ref_entry = f"[{idx}] {title}. URL: {url}"
        references_lines.append(ref_entry)

    references_section = "\n".join(references_lines)

    return body + references_section, metadata
