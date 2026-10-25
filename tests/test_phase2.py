import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

load_dotenv()


class TestPhase2(unittest.TestCase):

    # =========================================================================
    # 1. PYTHON IMPORT CHECKS
    # =========================================================================
    def test_01_imports_with_env(self):
        """[NO NETWORK] Verify src.tools and src.agents import cleanly with active environment."""
        try:
            import src.tools.tools as tools_mod
            import src.agents.agents as agents_mod
            self.assertTrue(hasattr(tools_mod, "web_search"))
            self.assertTrue(hasattr(tools_mod, "scrape_url"))
            self.assertTrue(hasattr(agents_mod, "build_search_agent"))
            self.assertTrue(hasattr(agents_mod, "build_reader_agent"))
            self.assertTrue(hasattr(agents_mod, "writer_chain"))
            self.assertTrue(hasattr(agents_mod, "critic_chain"))
        except Exception as e:
            self.fail(f"Import failed with active env: {e}")

    def test_02_lazy_imports_without_keys(self):
        """[MOCKED / ISOLATED] Verify modules do not crash on import if API keys are missing."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "", "TAVILY_API_KEY": ""}, clear=True):
            try:
                import importlib
                import src.tools.tools as tools_mod
                import src.agents.agents as agents_mod
                importlib.reload(tools_mod)
                importlib.reload(agents_mod)
                self.assertIsNotNone(tools_mod.web_search)
                self.assertIsNotNone(agents_mod.writer_chain)
            except Exception as e:
                self.fail(f"Lazy import failed when keys are missing: {e}")

    # =========================================================================
    # 2. TAVILY TOOL TESTS
    # =========================================================================
    def test_03_tavily_tool_validation(self):
        """[MOCKED / NO NETWORK] Verify Tavily tool handles empty inputs gracefully."""
        from src.tools.tools import web_search
        res = web_search.invoke("")
        self.assertIn("Error: Search query cannot be empty", res)

    def test_04_tavily_tool_missing_key(self):
        """[MOCKED / NO NETWORK] Verify Tavily tool returns error message when key is unset."""
        from src.tools.tools import web_search, get_tavily_client
        with patch.dict(os.environ, {"TAVILY_API_KEY": ""}, clear=True):
            with patch("src.tools.tools._tavily_client", None):
                res = web_search.invoke("test query")
                self.assertIn("Configuration error", res)

    def test_05_tavily_real_search(self):
        """[REAL API CALL] Test Tavily search returns real results using configured key."""
        from src.tools.tools import web_search
        res = web_search.invoke("Python programming language")
        self.assertIsInstance(res, str)
        self.assertIn("Title:", res)
        self.assertIn("URL:", res)
        self.assertNotIn("Configuration error", res)
        self.assertNotIn("Tavily search failed", res)

    # =========================================================================
    # 3. SCRAPING TESTS
    # =========================================================================
    def test_06_scrape_invalid_url(self):
        """[NO NETWORK] Test scrape_url input validation on non-URL inputs."""
        from src.tools.tools import scrape_url
        res = scrape_url.invoke("not-a-valid-url")
        self.assertIn("Error: A valid HTTP or HTTPS URL must be provided", res)

    def test_07_scrape_http_error(self):
        """[REAL HTTP CALL] Test scrape_url handling of a safe 404 test URL."""
        from src.tools.tools import scrape_url
        res = scrape_url.invoke("https://httpbin.org/status/404")
        self.assertIn("Page not found (HTTP 404)", res)

    def test_08_scrape_real_page(self):
        """[REAL HTTP CALL] Test scraping a safe, static public URL."""
        from src.tools.tools import scrape_url
        res = scrape_url.invoke("https://example.com")
        self.assertIsInstance(res, str)
        self.assertIn("Example Domain", res)
        self.assertLessEqual(len(res), 5000)

    def test_09_scrape_fallback_strategies(self):
        """[MOCKED HTML] Test that extraction falls back through strategies if Trafilatura fails."""
        from src.tools.tools import scrape_url
        mock_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <header>Header to remove</header>
                <nav>Nav to remove</nav>
                <article>
                    <p>This is a sufficiently long mock body text designed to test the readability fallback extraction strategy in our multi-strategy scraping pipeline. It contains meaningful information that will be retained while header, nav, and footer tags are stripped away.</p>
                </article>
                <footer>Footer to remove</footer>
            </body>
        </html>
        """
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = mock_html
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            # Force trafilatura to return None to test readability fallback
            with patch("trafilatura.extract", return_value=None):
                res = scrape_url.invoke("https://mock-domain.com/article")
                self.assertIn("sufficiently long mock body text", res)
                self.assertNotIn("Header to remove", res)
                self.assertNotIn("Footer to remove", res)

    # =========================================================================
    # 4. AGENT INITIALIZATION TESTS
    # =========================================================================
    def test_10_agent_initialization(self):
        """[NO NETWORK] Verify build_search_agent and build_reader_agent initialize without error."""
        from src.agents.agents import build_search_agent, build_reader_agent
        search_agent = build_search_agent()
        reader_agent = build_reader_agent()
        self.assertIsNotNone(search_agent)
        self.assertIsNotNone(reader_agent)

    # =========================================================================
    # 5. GEMINI TOOL-CALLING & AGENT EXECUTION
    # =========================================================================
    def test_11_gemini_tool_calling(self):
        """[REAL API CALL] Test Search Agent calling web_search and returning structured answer."""
        from src.agents.agents import build_search_agent
        agent = build_search_agent()
        result = agent.invoke({
            "messages": [("user", "Find recent information on the James Webb Space Telescope and summarize one finding in one sentence.")]
        })
        self.assertIn("messages", result)
        last_msg = result["messages"][-1]
        self.assertIsInstance(last_msg.content, str)
        self.assertGreater(len(last_msg.content), 20)

    # =========================================================================
    # 6. WRITER & CRITIC CHAIN TESTS
    # =========================================================================
    def test_12_writer_and_critic_chains(self):
        """[REAL API CALL] Test writer_chain and critic_chain with sample research input."""
        from src.agents.agents import writer_chain, critic_chain

        sample_topic = "Photosynthesis"
        sample_research = "Photosynthesis is the process used by plants to convert light energy into chemical energy. Key steps include light reactions and Calvin cycle."

        # Test Writer
        report = writer_chain.invoke({
            "topic": sample_topic,
            "research": sample_research
        })
        self.assertIsInstance(report, str)
        self.assertIn("Introduction", report)
        self.assertIn("Conclusion", report)

        # Test Critic
        feedback = critic_chain.invoke({
            "report": report
        })
        self.assertIsInstance(feedback, str)
        self.assertIn("Score:", feedback)
        self.assertIn("Strengths:", feedback)
        self.assertIn("Areas to Improve:", feedback)


if __name__ == "__main__":
    unittest.main(verbosity=2)
