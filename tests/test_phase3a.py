import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage


class TestPhase3A(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory and database for isolated testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_db_path = os.path.join(self.test_dir.name, "test_research.db")
        self.env_patcher = patch.dict(os.environ, {"DATABASE_PATH": self.test_db_path})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()
        try:
            self.test_dir.cleanup()
        except Exception:
            pass

    # =========================================================================
    # 1. DATABASE INITIALIZATION & TABLE CREATION
    # =========================================================================
    def test_01_db_init_and_tables(self):
        """[NO NETWORK] Verify SQLite database and research_history table are created with expected schema."""
        from src.db.database import init_db_sync
        import sqlite3

        init_db_sync(self.test_db_path)
        self.assertTrue(os.path.exists(self.test_db_path))

        conn = sqlite3.connect(self.test_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='research_history'")
            self.assertIsNotNone(cursor.fetchone(), "Table research_history was not created.")

            cursor.execute("PRAGMA table_info(research_history)")
            cols = {row[1] for row in cursor.fetchall()}
            expected_cols = {
                "id", "topic", "status", "search_results",
                "scraped_content", "report", "feedback",
                "metadata", "created_at", "updated_at"
            }
            self.assertTrue(expected_cols.issubset(cols), f"Missing columns in schema: {expected_cols - cols}")
        finally:
            conn.close()

    # =========================================================================
    # 2. SAVING & RETRIEVING A RESEARCH RUN
    # =========================================================================
    def test_02_save_and_retrieve_run(self):
        """[NO NETWORK] Verify saving a research run and retrieving it by unique ID."""
        from src.db.database import save_research_sync, get_research_by_id_sync

        run_data = {
            "topic": "Quantum Computing Milestones",
            "status": "completed",
            "search_results": "Search findings on qubits",
            "scraped_content": "Detailed text from source article",
            "report": "# Quantum Computing Report\nKey findings...",
            "feedback": "Score: 9/10\nStrengths: Thorough",
            "metadata": {"test_key": "test_val"}
        }

        run_id = save_research_sync(run_data, self.test_db_path)
        self.assertIsInstance(run_id, str)

        retrieved = get_research_by_id_sync(run_id, self.test_db_path)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], run_id)
        self.assertEqual(retrieved["topic"], "Quantum Computing Milestones")
        self.assertEqual(retrieved["status"], "completed")
        self.assertEqual(retrieved["report"], "# Quantum Computing Report\nKey findings...")
        self.assertEqual(retrieved["metadata"], {"test_key": "test_val"})

    # =========================================================================
    # 3. LISTING RECENT RUNS IN EXPECTED ORDER
    # =========================================================================
    def test_03_list_recent_runs_order(self):
        """[NO NETWORK] Verify recent runs are listed in created_at descending order."""
        from src.db.database import save_research_sync, list_recent_research_sync

        save_research_sync({
            "id": "run-1",
            "topic": "First Topic",
            "created_at": "2026-01-01T10:00:00+00:00",
            "status": "completed"
        }, self.test_db_path)

        save_research_sync({
            "id": "run-2",
            "topic": "Second Topic",
            "created_at": "2026-01-02T10:00:00+00:00",
            "status": "completed"
        }, self.test_db_path)

        recent = list_recent_research_sync(limit=10, db_path=self.test_db_path)
        self.assertEqual(len(recent), 2)
        # Most recent (run-2) should be first
        self.assertEqual(recent[0]["id"], "run-2")
        self.assertEqual(recent[1]["id"], "run-1")

    # =========================================================================
    # 4. DELETING A RUN
    # =========================================================================
    def test_04_delete_run(self):
        """[NO NETWORK] Verify deleting a research run by ID."""
        from src.db.database import save_research_sync, get_research_by_id_sync, delete_research_sync

        run_id = save_research_sync({
            "topic": "Temporary Topic",
            "status": "completed"
        }, self.test_db_path)

        deleted = delete_research_sync(run_id, self.test_db_path)
        self.assertTrue(deleted)

        retrieved = get_research_by_id_sync(run_id, self.test_db_path)
        self.assertIsNone(retrieved)

        # Deleting nonexistent run returns False
        self.assertFalse(delete_research_sync("non-existent-id", self.test_db_path))

    # =========================================================================
    # 5. INPUT VALIDATION: EMPTY / INVALID TOPICS
    # =========================================================================
    def test_05_invalid_empty_topics(self):
        """[NO NETWORK] Verify pipeline rejects empty or whitespace-only topics."""
        from src.pipelines.pipeline import run_research_pipeline

        for bad_topic in ["", "   ", None]:
            with self.subTest(topic=bad_topic):
                with self.assertRaises(ValueError):
                    run_research_pipeline(bad_topic)

    # =========================================================================
    # 6. PIPELINE EXECUTION WITH MOCKED AGENTS
    # =========================================================================
    def test_06_pipeline_mocked_execution(self):
        """[MOCKED AGENTS] Verify end-to-end pipeline execution and persistence with mocked agents."""
        from src.pipelines.pipeline import run_research_pipeline
        from src.db.database import get_research_by_id_sync

        mock_search_agent = MagicMock()
        mock_search_agent.invoke.return_value = {
            "messages": [AIMessage(content="Mock search: Found top URL https://example.com/ai")]
        }

        mock_reader_agent = MagicMock()
        mock_reader_agent.invoke.return_value = {
            "messages": [AIMessage(content="Mock scraped content from example.com/ai")]
        }

        mock_writer = MagicMock()
        mock_writer.invoke.return_value = "Mock Generated Report: Introduction, Findings, Conclusion"

        mock_critic = MagicMock()
        mock_critic.invoke.return_value = "Score: 8/10\nStrengths: Good summary\nAreas to Improve: Add data"

        with patch("src.pipelines.pipeline.build_search_agent", return_value=mock_search_agent), \
             patch("src.pipelines.pipeline.build_reader_agent", return_value=mock_reader_agent), \
             patch("src.pipelines.pipeline.writer_chain", mock_writer), \
             patch("src.pipelines.pipeline.critic_chain", mock_critic):

            topic = "Next Gen AI Architectures"
            result = run_research_pipeline(topic)

            # Check return structure
            self.assertIn("id", result)
            self.assertEqual(result["topic"], topic)
            self.assertEqual(result["status"], "completed")
            self.assertIn("Mock search", result["search_results"])
            self.assertIn("Mock scraped content", result["scraped_content"])
            self.assertIn("Mock Generated Report", result["report"])
            self.assertIn("Score: 8/10", result["feedback"])

            # Verify persisted in test SQLite database
            db_record = get_research_by_id_sync(result["id"], self.test_db_path)
            self.assertIsNotNone(db_record)
            self.assertEqual(db_record["status"], "completed")
            self.assertEqual(db_record["report"], result["report"])

    # =========================================================================
    # 7. PIPELINE FAILURE HANDLING
    # =========================================================================
    def test_07_pipeline_failure_handling(self):
        """[MOCKED ERROR] Verify failures in the pipeline are caught, recorded as 'failed', and re-raised."""
        from src.pipelines.pipeline import run_research_pipeline
        from src.db.database import list_recent_research_sync

        mock_search_agent = MagicMock()
        mock_search_agent.invoke.side_effect = ConnectionError("Simulated network timeout in search")

        with patch("src.pipelines.pipeline.build_search_agent", return_value=mock_search_agent):
            with self.assertRaises(RuntimeError) as cm:
                run_research_pipeline("Failing Topic")

            self.assertIn("Simulated network timeout", str(cm.exception))

            # Verify the failed run was recorded in SQLite with status='failed'
            recent = list_recent_research_sync(limit=5, db_path=self.test_db_path)
            self.assertEqual(len(recent), 1)
            self.assertEqual(recent[0]["topic"], "Failing Topic")
            self.assertEqual(recent[0]["status"], "failed")

    # =========================================================================
    # 8. EXISTING CLI COMPATIBILITY (main.py)
    # =========================================================================
    def test_08_cli_compatibility(self):
        """[CLI COMPATIBILITY] Verify that main.py can call run_research_pipeline without changes."""
        mock_search_agent = MagicMock()
        mock_search_agent.invoke.return_value = {
            "messages": [AIMessage(content="CLI mock search output")]
        }
        mock_reader_agent = MagicMock()
        mock_reader_agent.invoke.return_value = {
            "messages": [AIMessage(content="CLI mock reader output")]
        }
        mock_writer = MagicMock()
        mock_writer.invoke.return_value = "CLI mock report"
        mock_critic = MagicMock()
        mock_critic.invoke.return_value = "CLI mock feedback"

        with patch("src.pipelines.pipeline.build_search_agent", return_value=mock_search_agent), \
             patch("src.pipelines.pipeline.build_reader_agent", return_value=mock_reader_agent), \
             patch("src.pipelines.pipeline.writer_chain", mock_writer), \
             patch("src.pipelines.pipeline.critic_chain", mock_critic):

            import runpy
            from src.db.database import list_recent_research_sync
            res_dict = runpy.run_path("main.py")
            self.assertIn("topic", res_dict)
            self.assertEqual(res_dict["topic"], "The impact of AI on the job market in 2026")
            recent = list_recent_research_sync(limit=1, db_path=self.test_db_path)
            self.assertEqual(len(recent), 1)
            self.assertEqual(recent[0]["topic"], "The impact of AI on the job market in 2026")


if __name__ == "__main__":
    unittest.main(verbosity=2)
