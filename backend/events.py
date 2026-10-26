import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional, AsyncGenerator
from src.db.database import get_research_by_id


def format_sse(event: str, data: Any) -> str:
    """Formats an event name and data payload into standard SSE wire format."""
    data_str = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {data_str}\n\n"


class ResearchEventManager:
    """
    In-memory event manager for pub/sub progress streaming of active research runs.
    
    Architecture & Limitations:
    - Local Development: Stores events and subscribers in memory for fast, real-time local SSE delivery.
    - Concurrency: Multiple clients can subscribe to the same research run simultaneously.
    - Late Subscribers: Automatically replays event history for runs that are in-progress.
    - Historical Runs: Falls back to the SQLite database if a client connects to a completed run
      not currently in memory (e.g. after a server restart).
    - Multi-Worker Limitation: Since state is in-memory, multiple Uvicorn workers (e.g. --workers 4)
      or distributed instances would require an external pub/sub message broker like Redis.
      For local development with a single worker process, this in-memory pub/sub is optimal.
    """

    def __init__(self):
        self._runs: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    def register_run(self, run_id: str, topic: str) -> None:
        """Registers a new research run for event tracking."""
        self._runs[run_id] = {
            "id": run_id,
            "topic": topic,
            "status": "running",
            "events": [],
            "subscribers": set(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def emit_event(self, run_id: str, stage: str, data: dict) -> None:
        """
        Emits a progress event to all active subscribers and appends it to run history.
        """
        run = self._runs.get(run_id)
        event_payload = {
            "event": stage,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if run:
            run["events"].append(event_payload)
            if stage in ("completed", "failed"):
                run["status"] = stage

            # Deliver to active subscriber queues
            for queue in list(run["subscribers"]):
                try:
                    queue.put_nowait(event_payload)
                    if stage in ("completed", "failed"):
                        queue.put_nowait(None)  # Sentinel to close stream
                except Exception:
                    pass

    def subscribe(self, run_id: str) -> tuple[list[dict], asyncio.Queue]:
        """
        Subscribes to an in-memory run, returning (history, queue).
        """
        run = self._runs.get(run_id)
        if not run:
            raise KeyError(f"Run {run_id} is not registered in memory.")

        queue = asyncio.Queue()
        run["subscribers"].add(queue)
        history = list(run["events"])
        return history, queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        """Removes a subscriber queue from a run."""
        run = self._runs.get(run_id)
        if run and queue in run["subscribers"]:
            run["subscribers"].discard(queue)

    def is_run_registered(self, run_id: str) -> bool:
        """Checks if a run is currently registered in memory."""
        return run_id in self._runs

    def get_run_status(self, run_id: str) -> Optional[str]:
        """Retrieves status of run if present in memory."""
        run = self._runs.get(run_id)
        return run["status"] if run else None

    def remove_run(self, run_id: str) -> None:
        """Removes a run from in-memory tracking."""
        run = self._runs.pop(run_id, None)
        if run:
            for queue in list(run.get("subscribers", [])):
                try:
                    queue.put_nowait(None)
                except Exception:
                    pass


# Global singleton event manager instance
event_manager = ResearchEventManager()


async def stream_research_events(run_id: str, heartbeat_timeout: float = 15.0) -> AsyncGenerator[str, None]:
    """
    Generates Server-Sent Events (SSE) for a research run.
    Handles active runs, completed runs, and database fallbacks for late-connecting clients.
    """
    # Case 1: In-memory active or recently finished run
    if event_manager.is_run_registered(run_id):
        history, queue = event_manager.subscribe(run_id)
        try:
            # Replay all events recorded so far
            for ev in history:
                yield format_sse(ev["event"], ev["data"])

            # If the run already finished, close stream immediately
            if event_manager.get_run_status(run_id) in ("completed", "failed"):
                return

            # Stream incoming events in real time
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=heartbeat_timeout)
                    if item is None:
                        break  # End of stream sentinel
                    yield format_sse(item["event"], item["data"])
                    if item["event"] in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive comment to keep connection active through proxies/browsers
                    yield ": keepalive\n\n"
        finally:
            event_manager.unsubscribe(run_id, queue)
        return

    # Case 2: Run not in memory; look up in SQLite database
    record = await get_research_by_id(run_id)
    if not record:
        yield format_sse("failed", {"stage": "failed", "id": run_id, "error": f"Research run '{run_id}' not found."})
        return

    # Send initial event and final status from DB record without hanging
    yield format_sse("started", {
        "stage": "started",
        "id": run_id,
        "topic": record.get("topic", ""),
        "message": "Retrieved past research run."
    })

    if record.get("status") == "completed":
        yield format_sse("completed", {
            "stage": "completed",
            "id": run_id,
            "topic": record.get("topic", ""),
            "report": record.get("report", ""),
            "feedback": record.get("feedback", ""),
            "sources": record.get("sources", []),
        })
    else:
        meta = record.get("metadata", {})
        err = meta.get("error", "Research run failed.") if isinstance(meta, dict) else "Research run failed."
        yield format_sse("failed", {
            "stage": "failed",
            "id": run_id,
            "error": err
        })
