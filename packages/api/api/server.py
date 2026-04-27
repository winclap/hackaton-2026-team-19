"""FastAPI server — the main orchestrator.

Endpoints:
  POST /api/report      → start a new analysis job (returns job_id)
  GET  /api/report/{id} → poll job status / get results
  GET  /api/sources     → list available data sources
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from scraper.sources import SOURCES

from .models import AnalyzeRequest
from .worker import JOBS, run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Voice Intelligence API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/sources")
def list_sources() -> dict:
    return {
        name: {"name": ds.name, "text_field": ds.text_field}
        for name, ds in SOURCES.items()
    }


@app.post("/api/report")
async def create_report(req: AnalyzeRequest, bg: BackgroundTasks) -> dict:
    job_id = uuid.uuid4().hex[:8]

    JOBS[job_id] = {
        "status": "queued",
        "brand": req.brand.name,
        "total_reviews": 0,
    }

    bg.add_task(run_pipeline, job_id, req)

    return {"job_id": job_id, "status": "queued"}


@app.get("/api/report/{job_id}")
def get_report(job_id: str) -> dict:
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


def start() -> None:
    import uvicorn

    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
