import uuid
import asyncio
import logging
from typing import Optional
import aiosqlite
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError

from src.db.database import (
    get_db_path,
    init_db,
    get_research_by_id,
    list_recent_research,
    delete_research,
)
from src.pipelines.pipeline import run_research_pipeline_async
from backend.models import (
    ResearchCreateRequest,
    ResearchCreateResponse,
    ResearchSummaryResponse,
    ResearchDetailResponse,
    HealthResponse,
    MessageResponse,
)
from backend.events import event_manager, stream_research_events

logger = logging.getLogger("backend")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Multi-Agent AI Research System API",
    description="FastAPI backend providing REST and SSE endpoints for multi-agent research.",
    version="1.0.0",
)

# CORS configuration for frontend clients (Vite / React)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.encoders import jsonable_encoder


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors into clean, consistent JSON responses."""
    errors = exc.errors()
    first_error = errors[0].get("msg", "Invalid request data.") if errors else "Invalid request data."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": first_error, "errors": jsonable_encoder(errors)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Prevents leaking stack traces or credentials on unhandled exceptions."""
    logger.error("Unhandled exception processing %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Reports API and database health status without exposing sensitive credentials.
    """
    db_path = get_db_path()
    try:
        await init_db(db_path)
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")
        return HealthResponse(status="ok", database="connected", version="1.0.0")
    except Exception as e:
        logger.warning("Database health check failed: %s", str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "disconnected", "detail": "Database is unavailable."},
        )


async def _execute_pipeline_task(run_id: str, topic: str):
    """Background task running the async pipeline and routing progress to SSE event manager."""
    def on_progress(stage: str, data: dict):
        event_manager.emit_event(run_id, stage, data)

    try:
        await run_research_pipeline_async(topic=topic, on_progress=on_progress, run_id=run_id)
    except Exception as exc:
        logger.error("Pipeline run %s failed: %s", run_id, str(exc))


@app.post("/api/research", response_model=ResearchCreateResponse, status_code=status.HTTP_201_CREATED, tags=["Research"])
async def create_research(request: ResearchCreateRequest):
    """
    Starts an asynchronous multi-agent research run and returns its unique ID immediately.
    """
    run_id = str(uuid.uuid4())
    event_manager.register_run(run_id, request.topic)

    # Launch background task non-blockingly so the event loop remains free
    asyncio.create_task(_execute_pipeline_task(run_id, request.topic))

    return ResearchCreateResponse(
        id=run_id,
        topic=request.topic,
        status="running",
        message="Research run started successfully.",
    )


@app.get("/api/research", response_model=list[ResearchSummaryResponse], tags=["Research"])
async def list_research(
    limit: int = Query(default=20, ge=1, le=100, description="Max number of runs to return (1-100)")
):
    """
    Lists recent research runs ordered newest first with limit validation.
    """
    runs = await list_recent_research(limit=limit)
    return [ResearchSummaryResponse(**r) for r in runs]


@app.get("/api/research/{research_id}", response_model=ResearchDetailResponse, tags=["Research"])
async def get_research(research_id: str):
    """
    Retrieves full details of a single research run by ID.
    """
    record = await get_research_by_id(research_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{research_id}' was not found.",
        )
    return ResearchDetailResponse(**record)


@app.delete("/api/research/{research_id}", response_model=MessageResponse, tags=["Research"])
async def delete_research_run(research_id: str):
    """
    Deletes a research run by ID. Returns 404 if not found.
    """
    deleted = await delete_research(research_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{research_id}' was not found.",
        )
    event_manager.remove_run(research_id)
    return MessageResponse(message="Research run deleted successfully.", id=research_id)


@app.get("/api/research/{research_id}/stream", tags=["Research"])
async def stream_research(research_id: str):
    """
    Streams Server-Sent Events (SSE) for research run progress.
    Returns 404 if the research ID does not exist in memory or database.
    """
    if not event_manager.is_run_registered(research_id):
        record = await get_research_by_id(research_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research run '{research_id}' was not found.",
            )

    return StreamingResponse(
        stream_research_events(research_id),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
