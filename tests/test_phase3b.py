import os
import json
import uuid
import tempfile
import unittest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from backend.main import app
from backend.events import event_manager
from src.db.database import (
    get_db_path,
    init_db_sync,
    save_research_sync,
    get_research_by_id_sync,
    delete_research_sync,
)


class TestPhase3B(unittest.TestCase):
    """
    Automated test suite for Phase 3B FastAPI backend and SSE progress streaming.
    Tests operate on an isolated temporary SQLite database and use mocked pipeline
    calls to preserve live API quotas.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_phase3b.db")
        self.orig_db_path = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = self.test_db_path

        # Initialize temporary database schema
        init_db_sync(self.test_db_path)

        # Clear in-memory event manager runs
        event_manager._runs.clear()

        # Initialize FastAPI TestClient
        self.client = TestClient(app)

    def tearDown(self):
        # Clear in-memory event manager runs
        event_manager._runs.clear()

        # Restore original environment
        if self.orig_db_path:
            os.environ["DATABASE_PATH"] = self.orig_db_path
        else:
            os.environ.pop("DATABASE_PATH", None)

        # Clean up temporary test files safely on Windows
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            if os.path.exists(self.test_dir):
                import shutil
                shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_01_health_endpoint_and_db_availability(self):
        """[HEALTH] Verify /api/health reports ok/connected without leaking secrets."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("database"), "connected")
        self.assertIn("version", data)

        # Ensure no sensitive tokens or environment secrets leak
        body_text = response.text.lower()
        for forbidden in ("api_key", "secret", "password", "token", "google_api_key", "tavily_api_key"):
            self.assertNotIn(forbidden, body_text)

    def test_02_empty_and_invalid_research_topics(self):
        """[VALIDATION] Verify empty, whitespace, and missing topics return 422 errors."""
        # 1. Whitespace only
        res_ws = self.client.post("/api/research", json={"topic": "   "})
        self.assertEqual(res_ws.status_code, 422)
        self.assertIn("cannot be empty or whitespace", res_ws.json().get("detail", ""))

        # 2. Empty string
        res_empty = self.client.post("/api/research", json={"topic": ""})
        self.assertEqual(res_empty.status_code, 422)

        # 3. Missing topic field
        res_missing = self.client.post("/api/research", json={})
        self.assertEqual(res_missing.status_code, 422)

        # 4. Invalid data type (integer)
        res_type = self.client.post("/api/research", json={"topic": 98765})
        self.assertEqual(res_type.status_code, 422)

    @patch("backend.main.run_research_pipeline_async", new_callable=AsyncMock)
    def test_03_start_research_run_returns_id(self, mock_pipeline):
        """[RUN CREATION] Verify POST /api/research starts background run and returns research ID."""
        mock_pipeline.return_value = {
            "id": "mock-run-id",
            "topic": "AI advancements in 2026",
            "status": "completed",
            "report": "Mock Report",
            "feedback": "Mock Feedback",
        }

        response = self.client.post(
            "/api/research",
            json={"topic": "AI advancements in 2026"}
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["topic"], "AI advancements in 2026")
        self.assertEqual(data["status"], "running")
        self.assertIn("message", data)

        # Verify run is tracked in event manager
        run_id = data["id"]
        self.assertTrue(event_manager.is_run_registered(run_id))

    def test_04_retrieve_completed_run(self):
        """[RETRIEVAL] Verify GET /api/research/{id} retrieves full details of a saved run."""
        test_id = str(uuid.uuid4())
        run_payload = {
            "id": test_id,
            "topic": "Renewable Energy Grid Integration",
            "status": "completed",
            "search_results": "Search results about smart grids.",
            "scraped_content": "Detailed grid stability data.",
            "report": "Comprehensive Grid Report 2026",
            "feedback": "Score 9/10 - Excellent analysis.",
            "metadata": {"sources_count": 4},
        }
        save_research_sync(run_payload)

        response = self.client.get(f"/api/research/{test_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["id"], test_id)
        self.assertEqual(data["topic"], "Renewable Energy Grid Integration")
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["search_results"], "Search results about smart grids.")
        self.assertEqual(data["scraped_content"], "Detailed grid stability data.")
        self.assertEqual(data["report"], "Comprehensive Grid Report 2026")
        self.assertEqual(data["feedback"], "Score 9/10 - Excellent analysis.")
        self.assertEqual(data["metadata"], {"sources_count": 4})
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_05_list_recent_runs_and_validate_limit(self):
        """[LIST & LIMIT] Verify GET /api/research lists runs in newest-first order with limit validation."""
        # Insert 5 distinct runs
        for i in range(5):
            save_research_sync({
                "id": f"list-test-{i}",
                "topic": f"Topic Number {i}",
                "status": "completed",
                "report": f"Report {i}",
                "feedback": f"Feedback {i}",
            })

        # Test valid limit
        res_limit3 = self.client.get("/api/research?limit=3")
        self.assertEqual(res_limit3.status_code, 200)
        items = res_limit3.json()
        self.assertEqual(len(items), 3)

        # Verify ordering: created_at descending
        timestamps = [item["created_at"] for item in items]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

        # Test limit < 1 (must fail validation with 422)
        res_limit0 = self.client.get("/api/research?limit=0")
        self.assertEqual(res_limit0.status_code, 422)

        # Test limit > 100 (must fail validation with 422)
        res_limit_high = self.client.get("/api/research?limit=150")
        self.assertEqual(res_limit_high.status_code, 422)

        # Test non-integer limit
        res_invalid = self.client.get("/api/research?limit=abc")
        self.assertEqual(res_invalid.status_code, 422)

    def test_06_delete_existing_and_nonexistent_run(self):
        """[DELETE] Verify deleting an existing run returns 200, and deleting nonexistent returns 404."""
        test_id = str(uuid.uuid4())
        save_research_sync({
            "id": test_id,
            "topic": "Run To Be Deleted",
            "status": "completed",
        })
        event_manager.register_run(test_id, "Run To Be Deleted")

        # 1. Delete existing run
        res_del = self.client.delete(f"/api/research/{test_id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertIn("deleted successfully", res_del.json().get("message", ""))
        self.assertFalse(event_manager.is_run_registered(test_id))

        # Verify no longer in database
        self.assertIsNone(get_research_by_id_sync(test_id))

        # 2. Delete same run again -> 404
        res_del_repeat = self.client.delete(f"/api/research/{test_id}")
        self.assertEqual(res_del_repeat.status_code, 404)

        # 3. Delete non-existent ID -> 404
        res_nonexistent = self.client.delete("/api/research/non-existent-id-000")
        self.assertEqual(res_nonexistent.status_code, 404)

    def test_07_unknown_research_ids(self):
        """[NOT FOUND] Verify unknown research IDs return 404 for GET and STREAM endpoints."""
        unknown_id = "00000000-0000-0000-0000-000000000000"

        # GET detail on unknown ID
        res_detail = self.client.get(f"/api/research/{unknown_id}")
        self.assertEqual(res_detail.status_code, 404)
        self.assertIn("detail", res_detail.json())

        # GET stream on unknown ID
        res_stream = self.client.get(f"/api/research/{unknown_id}/stream")
        self.assertEqual(res_stream.status_code, 404)
        self.assertIn("detail", res_stream.json())

    def test_08_sse_headers_and_event_formatting(self):
        """[SSE HEADERS & EVENTS] Verify SSE stream emits correct headers and event wire format."""
        run_id = "sse-format-test-id"
        topic = "SSE Formatting Verification"

        event_manager.register_run(run_id, topic)
        event_manager.emit_event(run_id, "started", {"stage": "started", "id": run_id, "topic": topic})
        event_manager.emit_event(run_id, "searching", {"stage": "searching", "message": "Searching..."})
        event_manager.emit_event(run_id, "reading", {"stage": "reading", "message": "Reading..."})
        event_manager.emit_event(run_id, "writing", {"stage": "writing", "message": "Writing..."})
        event_manager.emit_event(run_id, "reviewing", {"stage": "reviewing", "message": "Reviewing..."})
        event_manager.emit_event(run_id, "completed", {"stage": "completed", "id": run_id, "report": "Final Report"})

        with self.client.stream("GET", f"/api/research/{run_id}/stream") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/event-stream", response.headers.get("content-type", ""))
            self.assertEqual(response.headers.get("cache-control"), "no-cache")

            lines = [line for line in response.iter_lines() if line]

            # Parse event lines and data lines
            events = [line.replace("event: ", "").strip() for line in lines if line.startswith("event: ")]
            self.assertIn("started", events)
            self.assertIn("searching", events)
            self.assertIn("reading", events)
            self.assertIn("writing", events)
            self.assertIn("reviewing", events)
            self.assertIn("completed", events)

            # Verify data JSON payloads
            data_lines = [line.replace("data: ", "").strip() for line in lines if line.startswith("data: ")]
            for d in data_lines:
                parsed = json.loads(d)
                self.assertIn("stage", parsed)

    def test_09_completed_and_failed_sse_runs(self):
        """[SSE EDGE CASES] Test late-connecting client to completed DB run and failed SSE runs."""
        # 1. Connect to an already completed run stored only in SQLite (not in memory)
        completed_id = str(uuid.uuid4())
        save_research_sync({
            "id": completed_id,
            "topic": "Historical Quantum Mechanics",
            "status": "completed",
            "report": "Historical Report Content",
            "feedback": "Historical Feedback",
        })

        with self.client.stream("GET", f"/api/research/{completed_id}/stream") as response:
            self.assertEqual(response.status_code, 200)
            lines = [line for line in response.iter_lines() if line]
            events = [line.replace("event: ", "").strip() for line in lines if line.startswith("event: ")]
            self.assertIn("started", events)
            self.assertIn("completed", events)

        # 2. Connect to an in-memory run that failed
        failed_id = "sse-failed-test-id"
        event_manager.register_run(failed_id, "Failed Topic")
        event_manager.emit_event(failed_id, "started", {"stage": "started", "id": failed_id})
        event_manager.emit_event(failed_id, "failed", {"stage": "failed", "id": failed_id, "error": "API quota exceeded"})

        with self.client.stream("GET", f"/api/research/{failed_id}/stream") as response:
            self.assertEqual(response.status_code, 200)
            lines = [line for line in response.iter_lines() if line]
            events = [line.replace("event: ", "").strip() for line in lines if line.startswith("event: ")]
            self.assertIn("failed", events)

            failed_data = [
                json.loads(line.replace("data: ", "").strip())
                for line in lines if line.startswith("data: ") and "quota" in line
            ]
            self.assertTrue(len(failed_data) > 0)
            self.assertEqual(failed_data[0]["error"], "API quota exceeded")

        # 3. Connect to a failed run stored in SQLite (fallback)
        db_failed_id = str(uuid.uuid4())
        save_research_sync({
            "id": db_failed_id,
            "topic": "Network Failure Run",
            "status": "failed",
            "metadata": {"error": "Connection timed out"},
        })

        with self.client.stream("GET", f"/api/research/{db_failed_id}/stream") as response:
            self.assertEqual(response.status_code, 200)
            lines = [line for line in response.iter_lines() if line]
            events = [line.replace("event: ", "").strip() for line in lines if line.startswith("event: ")]
            self.assertIn("failed", events)

    def test_10_cors_configuration(self):
        """[CORS] Verify CORS headers for configured frontend origins (localhost:5173 and 127.0.0.1:5173)."""
        origins_to_test = ["http://localhost:5173", "http://127.0.0.1:5173"]

        for origin in origins_to_test:
            # Simple GET request with Origin
            res = self.client.get("/api/health", headers={"Origin": origin})
            self.assertEqual(res.headers.get("access-control-allow-origin"), origin)
            self.assertEqual(res.headers.get("access-control-allow-credentials"), "true")

            # Preflight OPTIONS request
            res_opt = self.client.options(
                "/api/research",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                }
            )
            self.assertEqual(res_opt.headers.get("access-control-allow-origin"), origin)
            self.assertIn("POST", res_opt.headers.get("access-control-allow-methods", ""))

    def test_11_database_failure_handling(self):
        """[RESILIENCE] Verify /api/health gracefully reports 503 if the database is inaccessible."""
        with patch("backend.main.init_db", side_effect=RuntimeError("Simulated DB Disk Failure")):
            res = self.client.get("/api/health")
            self.assertEqual(res.status_code, 503)
            data = res.json()
            self.assertEqual(data.get("status"), "error")
            self.assertEqual(data.get("database"), "disconnected")
            self.assertIn("unavailable", data.get("detail", "").lower())

    def test_12_concurrent_requests_and_client_disconnect(self):
        """[CONCURRENCY & DISCONNECT] Verify concurrent operations and graceful client disconnect from stream."""
        # 1. Concurrently insert multiple runs into SQLite and retrieve them
        run_ids = [str(uuid.uuid4()) for _ in range(10)]
        for rid in run_ids:
            save_research_sync({
                "id": rid,
                "topic": f"Concurrent topic {rid}",
                "status": "completed",
            })

        res = self.client.get("/api/research?limit=50")
        self.assertEqual(res.status_code, 200)
        returned_ids = {item["id"] for item in res.json()}
        for rid in run_ids:
            self.assertIn(rid, returned_ids)

        # 2. Client disconnect test: open stream, read one event, and close context immediately
        disc_run_id = "disconnect-test-id"
        event_manager.register_run(disc_run_id, "Disconnect Topic")
        event_manager.emit_event(disc_run_id, "started", {"stage": "started", "id": disc_run_id})

        with self.client.stream("GET", f"/api/research/{disc_run_id}/stream") as response:
            self.assertEqual(response.status_code, 200)
            # Read first line and exit immediately (simulating client closing tab)
            for line in response.iter_lines():
                if line:
                    break

        # Verify that disconnecting does not leave zombie subscribers in event_manager
        run_obj = event_manager._runs.get(disc_run_id)
        if run_obj:
            self.assertEqual(len(run_obj["subscribers"]), 0)


if __name__ == "__main__":
    unittest.main()
