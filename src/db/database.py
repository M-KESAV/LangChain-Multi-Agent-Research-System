import os
import json
import uuid
import asyncio
import concurrent.futures
from datetime import datetime, timezone
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

# Project root directory for computing default DB path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "research_history.db")


def get_db_path(custom_path: str = None) -> str:
    """Returns the resolved SQLite database path and ensures its parent directory exists."""
    path = custom_path or os.getenv("DATABASE_PATH") or _DEFAULT_DB_PATH
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    return path


def _run_async(coro):
    """Safely runs an async coroutine from synchronous contexts."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


async def init_db(db_path: str = None) -> None:
    """Initializes the SQLite database and creates the required schema and indexes."""
    path = get_db_path(db_path)
    async with aiosqlite.connect(path, timeout=5.0) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA busy_timeout=5000;")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS research_history (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                status TEXT NOT NULL,
                search_results TEXT,
                scraped_content TEXT,
                report TEXT,
                feedback TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_research_created_at
            ON research_history (created_at DESC)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_research_status
            ON research_history (status)
        """)
        await db.commit()


def init_db_sync(db_path: str = None) -> None:
    """Synchronous wrapper for init_db."""
    return _run_async(init_db(db_path))


async def save_research(run_data: dict, db_path: str = None) -> str:
    """
    Saves or updates a research run in the SQLite database.
    Returns the unique run ID.
    """
    path = get_db_path(db_path)
    await init_db(path)

    run_id = str(run_data.get("id") or uuid.uuid4())
    topic = str(run_data.get("topic", "")).strip()
    status = str(run_data.get("status", "completed")).strip().lower()
    search_results = str(run_data.get("search_results") or "")
    scraped_content = str(run_data.get("scraped_content") or "")
    report = str(run_data.get("report") or "")
    feedback = str(run_data.get("feedback") or "")

    metadata_val = run_data.get("metadata", {})
    if isinstance(metadata_val, dict):
        sanitized_meta = {
            k: v for k, v in metadata_val.items()
            if not any(s in k.lower() for s in ("api_key", "secret", "password", "token", "credential"))
        }
    elif isinstance(metadata_val, str):
        try:
            sanitized_meta = json.loads(metadata_val)
        except Exception:
            sanitized_meta = {}
    else:
        sanitized_meta = {}

    if "sources" in run_data and "sources" not in sanitized_meta:
        sanitized_meta["sources"] = run_data["sources"]

    metadata_str = json.dumps(sanitized_meta)

    now_iso = datetime.now(timezone.utc).isoformat()
    created_at = str(run_data.get("created_at") or now_iso)
    updated_at = now_iso

    query = """
        INSERT INTO research_history (
            id, topic, status, search_results, scraped_content, report, feedback, metadata, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            topic = excluded.topic,
            status = excluded.status,
            search_results = excluded.search_results,
            scraped_content = excluded.scraped_content,
            report = excluded.report,
            feedback = excluded.feedback,
            metadata = excluded.metadata,
            updated_at = excluded.updated_at
    """

    async with aiosqlite.connect(path, timeout=5.0) as db:
        await db.execute("PRAGMA busy_timeout=5000;")
        await db.execute(
            query,
            (run_id, topic, status, search_results, scraped_content, report, feedback, metadata_str, created_at, updated_at)
        )
        await db.commit()

    return run_id


def save_research_sync(run_data: dict, db_path: str = None) -> str:
    """Synchronous wrapper for save_research."""
    return _run_async(save_research(run_data, db_path))


async def get_research_by_id(run_id: str, db_path: str = None) -> dict | None:
    """Retrieves a single research run by its unique ID, or returns None if not found."""
    path = get_db_path(db_path)
    await init_db(path)

    query = "SELECT * FROM research_history WHERE id = ?"
    async with aiosqlite.connect(path, timeout=5.0) as db:
        await db.execute("PRAGMA busy_timeout=5000;")
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (run_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            try:
                data["metadata"] = json.loads(data["metadata"]) if data.get("metadata") else {}
            except Exception:
                data["metadata"] = {}
            data["sources"] = data["metadata"].get("sources", []) if isinstance(data["metadata"], dict) else []
            return data


def get_research_by_id_sync(run_id: str, db_path: str = None) -> dict | None:
    """Synchronous wrapper for get_research_by_id."""
    return _run_async(get_research_by_id(run_id, db_path))


async def list_recent_research(limit: int = 50, db_path: str = None) -> list[dict]:
    """Retrieves a list of recent research runs ordered by created_at DESC."""
    path = get_db_path(db_path)
    await init_db(path)

    query = """
        SELECT id, topic, status, report, feedback, metadata, created_at, updated_at
        FROM research_history
        ORDER BY created_at DESC
        LIMIT ?
    """
    async with aiosqlite.connect(path, timeout=5.0) as db:
        await db.execute("PRAGMA busy_timeout=5000;")
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (limit,)) as cursor:
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["metadata"] = json.loads(item["metadata"]) if item.get("metadata") else {}
                except Exception:
                    item["metadata"] = {}
                item["sources"] = item["metadata"].get("sources", []) if isinstance(item["metadata"], dict) else []
                results.append(item)
            return results


def list_recent_research_sync(limit: int = 50, db_path: str = None) -> list[dict]:
    """Synchronous wrapper for list_recent_research."""
    return _run_async(list_recent_research(limit, db_path))


async def delete_research(run_id: str, db_path: str = None) -> bool:
    """Deletes a research run by its ID. Returns True if deleted, False otherwise."""
    path = get_db_path(db_path)
    await init_db(path)

    query = "DELETE FROM research_history WHERE id = ?"
    async with aiosqlite.connect(path, timeout=5.0) as db:
        await db.execute("PRAGMA busy_timeout=5000;")
        cursor = await db.execute(query, (run_id,))
        await db.commit()
        return cursor.rowcount > 0


def delete_research_sync(run_id: str, db_path: str = None) -> bool:
    """Synchronous wrapper for delete_research."""
    return _run_async(delete_research(run_id, db_path))
