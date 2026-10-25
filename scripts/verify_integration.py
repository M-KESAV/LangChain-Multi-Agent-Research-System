import sys
import os
import time
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import uvicorn
from backend.main import app
from src.db.database import save_research_sync, get_research_by_id_sync, delete_research_sync

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


def start_server():
    config = uvicorn.Config(app, host=SERVER_HOST, port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def main():
    print(f"[TEST 1/6] Launching live FastAPI backend on {BASE_URL}...")
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    # Wait for server readiness
    retries = 20
    ready = False
    for _ in range(retries):
        try:
            res = requests.get(f"{BASE_URL}/api/health", timeout=1)
            if res.status_code == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.3)

    if not ready:
        print("ERROR: Server failed to start within timeout.")
        sys.exit(1)

    # 1. Verify Health Endpoint
    print("[TEST 2/6] Verifying GET /api/health against live server...")
    health_res = requests.get(f"{BASE_URL}/api/health")
    assert health_res.status_code == 200, f"Expected 200, got {health_res.status_code}"
    health_data = health_res.json()
    assert health_data["status"] == "ok", f"Expected ok, got {health_data['status']}"
    assert health_data["database"] == "connected", f"Expected connected, got {health_data['database']}"
    print(f" -> PASSED: Health status = {health_data}")

    # 2. Verify Validation & Error States
    print("[TEST 3/6] Verifying Error & Validation Handling (422 and 404)...")
    empty_topic_res = requests.post(f"{BASE_URL}/api/research", json={"topic": "   "})
    assert empty_topic_res.status_code == 422, f"Expected 422 for empty topic, got {empty_topic_res.status_code}"
    print(" -> PASSED: Empty topic rejected with 422.")

    missing_run_res = requests.get(f"{BASE_URL}/api/research/nonexistent-id-999")
    assert missing_run_res.status_code == 404, f"Expected 404 for unknown run, got {missing_run_res.status_code}"
    print(" -> PASSED: Nonexistent run returned 404.")

    # 3. Create a Controlled Test Run & Stream via SSE
    test_run_id = f"e2e-test-{int(time.time())}"
    print(f"[TEST 4/6] Creating controlled test record {test_run_id} and testing SSE stream...")
    save_research_sync({
        "id": test_run_id,
        "topic": "Live Integration Verification Topic",
        "status": "completed",
        "report": "# Live E2E Research Report\n\nVerified integration between FastAPI and React frontend.",
        "feedback": "Score: 10/10 - Excellent integration.",
        "search_results": "Found https://example.com/e2e-source",
        "scraped_content": "Extracted text content for live testing.",
    })

    # Test SSE stream endpoint
    stream_res = requests.get(f"{BASE_URL}/api/research/{test_run_id}/stream", stream=True)
    assert stream_res.status_code == 200, f"Expected 200, got {stream_res.status_code}"
    assert "text/event-stream" in stream_res.headers.get("content-type", "")

    events_received = []
    for line in stream_res.iter_lines(decode_unicode=True):
        if line and line.startswith("event: "):
            events_received.append(line.replace("event: ", "").strip())

    assert "started" in events_received, f"Expected 'started' event, got {events_received}"
    assert "completed" in events_received, f"Expected 'completed' event, got {events_received}"
    print(f" -> PASSED: SSE stream delivered events: {events_received}")

    # 4. Verify Detail Retrieval
    print("[TEST 5/6] Verifying GET /api/research/{id} detail retrieval...")
    detail_res = requests.get(f"{BASE_URL}/api/research/{test_run_id}")
    assert detail_res.status_code == 200, f"Expected 200, got {detail_res.status_code}"
    detail_data = detail_res.json()
    assert detail_data["id"] == test_run_id
    assert detail_data["status"] == "completed"
    assert "Live E2E Research Report" in detail_data["report"]
    print(" -> PASSED: Detail retrieved with complete report and feedback.")

    # 5. Verify History Listing & Run Deletion
    print("[TEST 6/6] Verifying History List and Run Deletion...")
    list_res = requests.get(f"{BASE_URL}/api/research?limit=50")
    assert list_res.status_code == 200
    ids_in_history = [item["id"] for item in list_res.json()]
    assert test_run_id in ids_in_history, "Test run must appear in history list"

    del_res = requests.delete(f"{BASE_URL}/api/research/{test_run_id}")
    assert del_res.status_code == 200, f"Expected 200, got {del_res.status_code}"

    # Confirm deletion
    assert get_research_by_id_sync(test_run_id) is None
    print(f" -> PASSED: Run {test_run_id} deleted successfully from SQLite database.")

    print("\n=======================================================")
    print("ALL 6 LIVE FASTAPI BACKEND INTEGRATION CHECKS PASSED!")
    print("=======================================================")


if __name__ == "__main__":
    main()
