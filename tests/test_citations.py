"""
Citation Quality & Verification Test Suite:
Validates that:
1. Every in-text citation [N] maps consistently to a numbered entry [N] in Sources & References.
2. Each cited URL belongs to an actual source returned for that research run.
3. Shorthand citations (domain, title) are resolved to canonical numbers.
4. Out-of-bounds or fabricated citation indices are eliminated.
5. Zero-source research runs clearly disclose the absence of external evidence without inventing references.
6. Research pipeline saves citation alignment metadata.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.citations import (
    validate_and_normalize_citations,
    extract_domain_from_url,
)
from src.agents.agents import writer_prompt, critic_prompt
from src.pipelines.pipeline import run_research_pipeline


class TestCitationQuality(unittest.TestCase):
    """Test suite for citation-to-source mapping and grounding integrity."""

    def setUp(self):
        self.mock_sources = [
            {
                "title": "IDTechEx Solid-State Batteries 2026",
                "url": "https://www.idtechex.com/en/research-report/solid-state-batteries/1130",
                "snippet": "Commercialization of solid-state batteries begins in specialized markets in 2026.",
                "status": "scraped"
            },
            {
                "title": "Xnergy Technical Guide 2026",
                "url": "https://xnergy.us/solid-state-batteries-2026-guide",
                "snippet": "Solid electrolyte conductivities exceed 10 mS/cm.",
                "status": "scraped"
            },
            {
                "title": "MDPI Scientific Review on Lithium Anodes",
                "url": "https://www.mdpi.com/2313-0105/11/3/90",
                "snippet": "Dendrite suppression mechanisms analyzed in sulfide interfaces.",
                "status": "discovered"
            }
        ]

    def test_01_consistent_in_text_to_numbered_reference_mapping(self):
        """Verify every in-text citation [N] corresponds 1-to-1 to a numbered entry in Sources & References."""
        sample_report = (
            "# Solid-State Batteries in 2026\n\n"
            "## Introduction & Executive Summary\n"
            "Solid-state technology is scaling rapidly [1]. Commercialization begins in niche sectors [1].\n\n"
            "## Key Findings\n"
            "Solid electrolyte conductivities now exceed 10 mS/cm [2]. Interfacial stability remains crucial [3].\n\n"
            "## Conclusion & Strategic Outlook\n"
            "Future outlook is strong [1][2].\n\n"
            "## Sources & References\n"
            "[1] Old Title https://old.com\n"
            "[2] Another Old Title https://another.com"
        )

        normalized_report, meta = validate_and_normalize_citations(sample_report, self.mock_sources)

        # In-text citations found must be [1], [2], [3]
        self.assertEqual(meta["in_text_citations"], [1, 2, 3])

        # Check references section contains exact numbered entries matching mock sources
        for idx, src in enumerate(self.mock_sources, 1):
            expected_entry = f"[{idx}] {src['title']}. URL: {src['url']}"
            self.assertIn(expected_entry, normalized_report)

    def test_02_each_cited_url_belongs_to_actual_source(self):
        """Ensure all URLs in the final references section strictly belong to retrieved sources."""
        sample_report = (
            "# Quantum Computing\n\n"
            "Breakthrough verified [1].\n\n"
            "## Sources & References\n"
            "[1] Fabricated Article. URL: https://invented-fake-url.com"
        )

        normalized_report, _ = validate_and_normalize_citations(sample_report, self.mock_sources)

        # The fabricated URL must NOT appear in the normalized report
        self.assertNotIn("https://invented-fake-url.com", normalized_report)

        # Verified URLs must be present
        for src in self.mock_sources:
            self.assertIn(src["url"], normalized_report)

    def test_03_resolving_shorthand_citations(self):
        """Verify shorthand citations (e.g. [IDTechEx], [xnergy.us]) resolve to numerical indices."""
        sample_report = (
            "# Solid-State Battery Commercialization\n\n"
            "## Key Findings\n"
            "Market scaling begins this year [IDTechEx]. "
            "High conductivity was demonstrated in lab tests [xnergy.us]. "
            "Sulfide interface mechanics were modeled in detail [MDPI].\n\n"
            "## Conclusion & Strategic Outlook\n"
            "Progress continues [idtechex.com]."
        )

        normalized_report, meta = validate_and_normalize_citations(sample_report, self.mock_sources)

        self.assertGreaterEqual(meta["shorthand_citations_resolved"], 3)
        self.assertIn("[1]", normalized_report)
        self.assertIn("[2]", normalized_report)
        self.assertIn("[3]", normalized_report)
        # Unnumbered bracketed tags should be replaced
        self.assertNotIn("[IDTechEx]", normalized_report)
        self.assertNotIn("[xnergy.us]", normalized_report)

    def test_04_out_of_bounds_fabricated_citations_eliminated(self):
        """Verify that hallucinated citations with invalid indices (e.g. [99]) are removed."""
        sample_report = (
            "# Fusion Energy\n\n"
            "Real finding [1]. Fabricated claim [99]. Another valid claim [2]."
        )

        normalized_report, meta = validate_and_normalize_citations(sample_report, self.mock_sources)

        self.assertEqual(meta["invalid_citations_removed"], 1)
        self.assertIn("[1]", normalized_report)
        self.assertIn("[2]", normalized_report)
        self.assertNotIn("[99]", normalized_report)

    def test_05_missing_source_handling_zero_sources(self):
        """Verify zero-source handling: no fabricated citations, explicit disclosure of limitation."""
        sample_report = (
            "# Obscure Entity Research\n\n"
            "An unsupported claim [1] and another [2].\n\n"
            "## Sources & References\n"
            "[1] Fabricated source: https://fake-news.org"
        )

        normalized_report, meta = validate_and_normalize_citations(sample_report, sources=[])

        self.assertTrue(meta["missing_sources"])
        self.assertEqual(len(meta["in_text_citations"]), 0)
        # Numerical citations must be removed when 0 sources exist
        self.assertNotIn("[1]", normalized_report)
        self.assertNotIn("[2]", normalized_report)
        self.assertNotIn("https://fake-news.org", normalized_report)
        self.assertIn("No external sources or URLs were discovered", normalized_report)

    def test_06_prompt_rules_enforce_evidence_and_consistent_numbering(self):
        """Verify writer and critic prompts specify strict numerical indexing and evidence requirements."""
        sys_writer = writer_prompt.messages[0].prompt.template
        self.assertIn("strictly numbered brackets: [1], [2], [3]", sys_writer)
        self.assertIn("NEVER use author or shorthand names in brackets", sys_writer)
        self.assertIn("map 1-to-1 consistently", sys_writer)
        self.assertIn("NEVER claim that a source supports a statement unless the retrieved snippet or scraped content actually provides evidence", sys_writer)

        sys_critic = critic_prompt.messages[0].prompt.template
        self.assertIn("citation-to-source consistency", sys_critic)
        self.assertIn("every in-text citation [N] corresponds consistently to a numbered entry in Sources & References", sys_critic)

    def test_07_end_to_end_pipeline_citation_validation(self):
        """Verify run_research_pipeline normalizes citations and stores metadata."""
        mock_writer = MagicMock()
        mock_writer.invoke.return_value = (
            "# Battery Research\n\n"
            "## Introduction & Executive Summary\n"
            "Solid state is scaling [IDTechEx].\n\n"
            "## Key Findings\n"
            "Conductivity reached 10 mS/cm [2].\n\n"
            "## In-Depth Analysis & Practical Implications\n"
            "Implications are global.\n\n"
            "## Conclusion & Strategic Outlook\n"
            "Outlook is strong.\n\n"
            "## Sources & References\n"
            "[1] IDTechEx"
        )
        mock_critic = MagicMock()
        mock_critic.invoke.return_value = "Score: 9/10\nStrengths: Solid citations."

        with patch("src.pipelines.pipeline.build_search_agent") as mock_sa, \
             patch("src.pipelines.pipeline.build_reader_agent") as mock_ra, \
             patch("src.pipelines.pipeline.writer_chain", mock_writer), \
             patch("src.pipelines.pipeline.critic_chain", mock_critic), \
             patch("src.pipelines.pipeline.tavily_search_structured", return_value=self.mock_sources[:2]), \
             patch("src.pipelines.pipeline._perform_scraping", return_value=("Scraped text", self.mock_sources[:2])):

            mock_agent = MagicMock()
            mock_agent.invoke.return_value = {"messages": [MagicMock(content="Search done.")]}
            mock_sa.return_value = mock_agent
            mock_ra.return_value = mock_agent

            result = run_research_pipeline("Battery Research 2026")

            # Check that report has [1] instead of [IDTechEx]
            self.assertIn("[1]", result["report"])
            self.assertNotIn("[IDTechEx]", result["report"])
            self.assertIn(self.mock_sources[0]["url"], result["report"])
            self.assertIn(self.mock_sources[1]["url"], result["report"])
            # Check metadata
            self.assertIn("citations", result["metadata"])
            self.assertEqual(result["metadata"]["citations"]["sources_count"], 2)


if __name__ == "__main__":
    unittest.main()
