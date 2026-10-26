"""
Phase 5 Comprehensive Regression Test Suite:
Validates research sources, URL extraction, deduplication, scraping error resilience,
writer citations, SQLite persistence, API exposure, zero-source handling,
and live Tavily search and scrape execution.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock

from dotenv import load_dotenv

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from src.tools.tools import (
    validate_url,
    canonicalize_url,
    tavily_search_structured,
    extract_sources_from_text,
    scrape_url_structured,
    scrape_url,
)
from src.agents.agents import writer_prompt, critic_prompt
from src.pipelines.pipeline import (
    _extract_sources_from_agent_result,
    _perform_scraping,
    run_research_pipeline,
)
from src.db.database import (
    init_db,
    save_research,
    get_research_by_id,
    list_recent_research,
    delete_research,
)
from fastapi.testclient import TestClient
from backend.main import app


class TestPhase5Regression(unittest.TestCase):
    """Regression test suite for research sources and citations."""

    @classmethod
    def setUpClass(cls):
        # Initialize test DB
        asyncio.run(init_db())
        cls.client = TestClient(app)

    # 1. Parsing structured Tavily results and extracting URLs
    def test_01_parsing_structured_tavily_results(self):
        """Verify parsing of structured Tavily responses into valid, normalized source objects."""
        mock_tavily_response = {
            "results": [
                {
                    "title": "Quantum Computing Breakthrough 2026",
                    "url": "https://example.com/quantum?utm_source=twitter&utm_medium=social",
                    "content": "Researchers have demonstrated fault-tolerant logical qubits at scale.",
                    "score": 0.98,
                },
                {
                    "title": "MIT Technology Review - Quantum",
                    "url": "https://technologyreview.com/quantum-2026",
                    "content": "Commercial timeline accelerates for quantum chemistry simulations.",
                    "score": 0.92,
                },
                {
                    "title": "Invalid URL Result",
                    "url": "ftp://invalid-protocol.com/file",
                    "content": "Should be filtered out.",
                },
            ]
        }

        with patch("src.tools.tools.get_tavily_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.search.return_value = mock_tavily_response
            mock_get_client.return_value = mock_client

            sources = tavily_search_structured("Quantum Computing 2026", max_results=5)

            self.assertEqual(len(sources), 2)
            self.assertEqual(sources[0]["title"], "Quantum Computing Breakthrough 2026")
            # Verify tracking params stripped
            self.assertEqual(sources[0]["url"], "https://example.com/quantum")
            self.assertIn("fault-tolerant", sources[0]["snippet"])
            self.assertEqual(sources[1]["url"], "https://technologyreview.com/quantum-2026")

    # 2. Deduplicating URLs while preserving useful order
    def test_02_deduplicating_canonical_urls(self):
        """Verify URL canonicalization and deduplication."""
        # Test canonicalization
        url1 = "https://example.com/news/article/?utm_campaign=spring&utm_source=newsletter"
        url2 = "https://example.com/news/article#section-1"
        self.assertEqual(canonicalize_url(url1), "https://example.com/news/article")
        self.assertEqual(canonicalize_url(url2), "https://example.com/news/article")

        # Test deduplication in tavily_search_structured
        duplicate_results = {
            "results": [
                {"title": "First Encounter", "url": "https://example.org/ai-study?utm_medium=rss", "content": "Study 1"},
                {"title": "Second Encounter (Dup)", "url": "https://example.org/ai-study/", "content": "Study 1 dup"},
                {"title": "Unique Study", "url": "https://example.org/ai-study-2", "content": "Study 2"},
            ]
        }
        with patch("src.tools.tools.get_tavily_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.search.return_value = duplicate_results
            mock_get_client.return_value = mock_client

            sources = tavily_search_structured("AI Study", max_results=5)
            self.assertEqual(len(sources), 2)
            self.assertEqual(sources[0]["url"], "https://example.org/ai-study")
            self.assertEqual(sources[1]["url"], "https://example.org/ai-study-2")

    # 3. Passing discovered URLs into the Reader Agent
    def test_03_passing_discovered_urls_to_reader(self):
        """Verify that Reader Agent receives concrete candidate URLs extracted from Search output."""
        mock_tool_message = MagicMock()
        mock_tool_message.type = "tool"
        mock_tool_message.content = (
            "Source: https://nature.com/articles/nature-ai\n"
            "Title: Nature AI Breakthrough\n"
            "Snippet: Foundational model for biology.\n\n"
            "Source: https://arxiv.org/abs/2601.12345\n"
            "Title: Linear Attention at Scale\n"
            "Snippet: Sub-quadratic scaling architecture.\n"
        )

        agent_result = {
            "messages": [
                MagicMock(content="Searching web for topic..."),
                mock_tool_message,
                MagicMock(content="I found two relevant sources: Nature AI and ArXiv."),
            ]
        }

        extracted = _extract_sources_from_agent_result(agent_result, topic="AI Architecture")
        urls = [s["url"] for s in extracted]

        self.assertIn("https://nature.com/articles/nature-ai", urls)
        self.assertIn("https://arxiv.org/abs/2601.12345", urls)

    # 4. Handling a failed scrape while preserving other successful sources
    def test_04_handling_failed_scrape_gracefully(self):
        """Verify that if one URL fails to scrape, other sources succeed and failure is logged."""
        sources = [
            {"title": "Good Source", "url": "https://example.com/good", "snippet": "Snippet 1"},
            {"title": "Broken 404 Source", "url": "https://example.com/missing-404", "snippet": "Snippet 2"},
            {"title": "Another Good Source", "url": "https://example.com/good-2", "snippet": "Snippet 3"},
        ]

        def mock_scrape(url: str, **kwargs):
            if "missing-404" in url:
                return {
                    "url": url,
                    "title": "Broken 404 Source",
                    "text": "",
                    "content": "",
                    "status": "failed",
                    "error": "Page not found (HTTP 404)",
                }
            return {
                "url": url,
                "title": f"Title for {url}",
                "text": f"Rich scraped article body for {url} with deep technical details.",
                "content": f"Rich scraped article body for {url} with deep technical details.",
                "status": "scraped",
                "error": None,
            }

        with patch("src.pipelines.pipeline.scrape_url_structured", side_effect=mock_scrape):
            scraped_text, updated_sources = _perform_scraping(sources, max_urls=3)

            # Both successful sources must be in the scraped content
            self.assertIn("https://example.com/good", scraped_text)
            self.assertIn("https://example.com/good-2", scraped_text)
            self.assertIn("Rich scraped article body", scraped_text)

            # Check per-source status tracking
            status_map = {s["url"]: s["status"] for s in updated_sources}
            self.assertEqual(status_map["https://example.com/good"], "scraped")
            self.assertEqual(status_map["https://example.com/missing-404"], "failed")
            self.assertEqual(status_map["https://example.com/good-2"], "scraped")

    # 5. Passing source metadata to the Writer Chain
    def test_05_passing_source_metadata_to_writer(self):
        """Verify the research input for writer contains topic, sources registry, and scraped text."""
        # Simulated run with mock agents
        mock_sources = [
            {"title": "Clean Energy Report", "url": "https://energy.org/clean-2026", "snippet": "Efficiency 40%"},
        ]
        mock_writer = MagicMock()
        mock_writer.invoke.return_value = (
            "# Clean Energy\n\n## Introduction & Executive Summary\nClean energy is advancing.\n\n"
            "## Key Findings\nSolar efficiency reached 40% [1].\n\n"
            "## In-Depth Analysis & Practical Implications\nImplications are global.\n\n"
            "## Conclusion & Strategic Outlook\nOutlook is positive.\n\n"
            "## Sources & References\n[1] Clean Energy Report - https://energy.org/clean-2026"
        )
        mock_critic = MagicMock()
        mock_critic.invoke.return_value = "Score: 9/10\nStrengths: Good citations\nAreas to Improve: None"

        with patch("src.pipelines.pipeline.build_search_agent") as mock_sa, \
             patch("src.pipelines.pipeline.build_reader_agent") as mock_ra, \
             patch("src.pipelines.pipeline.writer_chain", mock_writer), \
             patch("src.pipelines.pipeline.critic_chain", mock_critic), \
             patch("src.pipelines.pipeline.tavily_search_structured", return_value=mock_sources), \
             patch("src.pipelines.pipeline._perform_scraping", return_value=("Article content", mock_sources)):

            mock_agent = MagicMock()
            mock_agent.invoke.return_value = {"messages": [MagicMock(content="Search completed.")]}
            mock_sa.return_value = mock_agent
            mock_ra.return_value = mock_agent

            result = run_research_pipeline("Clean Energy 2026")

            # Check writer was called with proper payload
            call_args = mock_writer.invoke.call_args[0][0]
            self.assertEqual(call_args["topic"], "Clean Energy 2026")
            self.assertIn("https://energy.org/clean-2026", call_args["research"])
            self.assertIn("Clean Energy Report", call_args["research"])

    # 6. Preventing fabricated citations or source URLs in writer prompt
    def test_06_preventing_fabricated_citations_in_prompt(self):
        """Verify writer and critic prompts enforce strict grounding and cite-checking."""
        # System prompt checks
        sys_message = writer_prompt.messages[0].prompt.template
        self.assertIn("CORE CITATION & GROUNDING RULES", sys_message)
        self.assertIn("NEVER invent, fabricate, or guess URLs", sys_message)
        self.assertIn("In-text citations are MANDATORY", sys_message)
        self.assertIn("Every citation and URL in your report MUST strictly match a source provided", sys_message)

        # Critic prompt checks
        critic_sys = critic_prompt.messages[0].prompt.template
        self.assertIn("source citation coverage", critic_sys)

    # 7. Persisting sources in SQLite and returning them from the API
    def test_07_persisting_and_api_returning_sources(self):
        """Verify research run with structured sources is persisted and returned by GET /api/research/{id}."""
        test_id = "test-phase5-sources-persist"
        test_sources = [
            {
                "title": "Battery Technology Q3 2026",
                "url": "https://battery-tech.org/q3-2026",
                "snippet": "Solid state batteries achieve 500 Wh/kg.",
                "status": "scraped",
            },
            {
                "title": "Automotive News Review",
                "url": "https://autonews.com/battery-ev",
                "snippet": "EV range reaches 1000km in prototype testing.",
                "status": "discovered",
            },
        ]

        # Save to DB
        asyncio.run(
            save_research({
                "id": test_id,
                "topic": "Solid State Batteries 2026",
                "search_results": "Search output summary with https://battery-tech.org/q3-2026",
                "scraped_content": "Detailed battery specifications.",
                "report": "# Solid State Batteries\n\nSolid state density reached 500 Wh/kg [1].",
                "feedback": "Score: 9/10\nCitation Quality: Rigorous.",
                "status": "completed",
                "sources": test_sources,
            })
        )

        # Fetch from DB directly
        db_record = asyncio.run(get_research_by_id(test_id))
        self.assertIsNotNone(db_record)
        self.assertEqual(len(db_record.get("sources", [])), 2)
        self.assertEqual(db_record["sources"][0]["title"], "Battery Technology Q3 2026")
        self.assertEqual(db_record["sources"][0]["url"], "https://battery-tech.org/q3-2026")

        # Fetch via FastAPI endpoint
        response = self.client.get(f"/api/research/{test_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sources", data)
        self.assertEqual(len(data["sources"]), 2)
        self.assertEqual(data["sources"][0]["url"], "https://battery-tech.org/q3-2026")
        self.assertEqual(data["sources"][0]["status"], "scraped")

    # 8. GET /api/research list summary includes sources
    def test_08_sources_in_summary_list(self):
        """Verify GET /api/research summaries include structured sources."""
        response = self.client.get("/api/research?limit=5")
        self.assertEqual(response.status_code, 200)
        runs = response.json()
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)
        # Verify first item has sources field
        first = runs[0]
        self.assertIn("sources", first)
        self.assertIsInstance(first["sources"], list)

    # 9. Handling zero-source research without falsely claiming it is fully sourced
    def test_09_handling_zero_source_research(self):
        """Verify pipeline handles 0 discovered sources gracefully and reports limitation."""
        with patch("src.pipelines.pipeline.build_search_agent") as mock_sa, \
             patch("src.pipelines.pipeline.build_reader_agent") as mock_ra, \
             patch("src.pipelines.pipeline.writer_chain") as mock_writer, \
             patch("src.pipelines.pipeline.critic_chain") as mock_critic, \
             patch("src.pipelines.pipeline.tavily_search_structured", return_value=[]):

            mock_agent = MagicMock()
            mock_agent.invoke.return_value = {"messages": [MagicMock(content="No results found.")]}
            mock_sa.return_value = mock_agent
            mock_ra.return_value = mock_agent

            mock_writer.invoke.return_value = (
                "# Obscure Query\n\n## Introduction & Executive Summary\nNo verified information found.\n\n"
                "## Key Findings\nTopic has 0 verified empirical studies.\n\n"
                "## In-Depth Analysis & Practical Implications\nCannot make recommendations without data.\n\n"
                "## Conclusion & Strategic Outlook\nFurther research needed.\n\n"
                "## Sources & References\nNo external sources available."
            )
            mock_critic.invoke.return_value = (
                "Score: 5/10\n"
                "Strengths: Honestly acknowledges lack of data.\n"
                "Citation & Source Quality: 0 external citations."
            )

            result = run_research_pipeline("Query With Zero Results 999999")

            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(result["sources"]), 0)
            self.assertIn("No external sources", result["report"])

    # 10. Preserving existing CLI, history, and critic functionality
    def test_10_preserving_cli_and_history(self):
        """Verify delete and list functionality work properly with sources data."""
        test_id = "test-phase5-delete-id"
        asyncio.run(
            save_research({
                "id": test_id,
                "topic": "Temporary Delete Test",
                "search_results": "Temp",
                "scraped_content": "Temp",
                "report": "Temp",
                "feedback": "Temp",
                "status": "completed",
                "sources": [{"title": "Temp", "url": "https://temp.org", "snippet": "Temp"}],
            })
        )

        # Confirm it exists
        found = asyncio.run(get_research_by_id(test_id))
        self.assertIsNotNone(found)

        # Delete it via DB function
        deleted = asyncio.run(delete_research(test_id))
        self.assertTrue(deleted)

        # Verify it is gone
        found_after = asyncio.run(get_research_by_id(test_id))
        self.assertIsNone(found_after)

    # 11. Live Tavily search and scrape test (identifying real discovery)
    def test_11_live_tavily_search_and_scrape(self):
        """Live search and scrape test using real Tavily and HTTP client."""
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key or tavily_key.startswith("tvly-placeholder"):
            self.skipTest("Valid TAVILY_API_KEY not configured; skipping live search test.")

        # Real live search
        query = "DeepSeek-R1 open weights reasoning model architecture"
        live_sources = tavily_search_structured(query, max_results=3)

        self.assertIsInstance(live_sources, list)
        self.assertGreater(len(live_sources), 0, "Live Tavily search should return at least 1 result")

        first_source = live_sources[0]
        self.assertIn("url", first_source)
        self.assertTrue(validate_url(first_source["url"]))
        self.assertTrue(len(first_source.get("title", "")) > 0)
        print(f"\n[LIVE SEARCH SUCCESS] Discovered URL: {first_source['url']} | Title: {first_source['title']}")

        # Real live scrape on the first discovered URL
        scrape_result = scrape_url_structured(first_source["url"], timeout=10)
        self.assertIsInstance(scrape_result, dict)
        self.assertEqual(scrape_result["url"], first_source["url"])

        # Check scrape status
        print(f"[LIVE SCRAPE RESULT] Status: {scrape_result['status']} | Content Length: {len(scrape_result['text'])}")
        if scrape_result["status"] == "scraped":
            self.assertGreater(len(scrape_result["text"]), 50)
            self.assertTrue(len(scrape_result.get("title", "")) > 0)
        else:
            # In case site returned 403 or Cloudflare protection, verify structured error recorded
            self.assertIsNotNone(scrape_result["error"])


if __name__ == "__main__":
    unittest.main()
