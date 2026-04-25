"""FastAPI server — the main orchestrator.

Endpoints:
  POST /api/report      → start a new analysis job (returns job_id)
  GET  /api/report/{id} → poll job status / get results
  GET  /api/sources     → list available data sources
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

app = FastAPI(title="Voice Intelligence API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import after dotenv so env vars are available
from .models import AnalyzeRequest, JobStatus
from .worker import JOBS, run_pipeline

# Lazy import sources registry
_sources_cache = None


def _get_sources():
    global _sources_cache
    if _sources_cache is None:
        import sys
        pkg_path = str(Path(__file__).parent.parent.parent / "scraper")
        if pkg_path not in sys.path:
            sys.path.insert(0, pkg_path)
        from scraper.sources import SOURCES
        _sources_cache = SOURCES
    return _sources_cache


@app.get("/api/sources")
def list_sources():
    """List available data sources."""
    sources = _get_sources()
    return {
        name: {"name": ds.name, "text_field": ds.text_field}
        for name, ds in sources.items()
    }


@app.post("/api/report")
async def create_report(req: AnalyzeRequest, bg: BackgroundTasks):
    """Start a new analysis job. Returns job_id immediately.

    The pipeline runs in background:
    1. Scrape data via Apify
    2. Quick ML analysis (sentiment + themes) → webhook call
    3. Deep Haiku analysis (categorization + briefs) → webhook call
    """
    job_id = str(uuid.uuid4())[:8]

    JOBS[job_id] = {
        "status": "queued",
        "brand": req.brand.name,
        "total_reviews": 0,
    }

    # Run pipeline in background
    bg.add_task(_run_async_pipeline, job_id, req)

    return {"job_id": job_id, "status": "queued"}


async def _run_async_pipeline(job_id: str, req: AnalyzeRequest):
    await run_pipeline(job_id, req)


@app.get("/api/report/{job_id}")
def get_report(job_id: str):
    """Get status or result of an analysis job."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    response = {
        "job_id": job_id,
        "status": job["status"],
        "brand": job.get("brand", ""),
        "total_reviews": job.get("total_reviews", 0),
    }

    if job["status"] == "done":
        response["data"] = job.get("result")
    elif job["status"] == "error":
        response["error"] = job.get("error", "Unknown error")
    elif "quick_result" in job:
        response["quick_result"] = job["quick_result"]

    return response


def start():
    """Run the server with uvicorn."""
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    start()
