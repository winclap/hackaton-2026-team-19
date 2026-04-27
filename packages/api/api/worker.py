"""Background worker that runs the full pipeline for a job."""

from __future__ import annotations

import asyncio
import logging
import os
import traceback
from datetime import datetime, timezone

import pandas as pd
from analyzer.briefs import generate_briefs
from analyzer.deep import CHUNK_SIZE, analyze_deep
from analyzer.sentiment import analyze_sentiment
from analyzer.themes import extract_themes
from scraper.collector import collect as scraper_collect
from scraper.resolve import resolve_appstore_id, resolve_playstore_id

from .models import AnalyzeRequest
from .webhook import notify_frontend

logger = logging.getLogger(__name__)

TEXT_COLUMN = "content"
MIN_REVIEW_LEN = 30
MIN_ROWS_FOR_THEMES = 10

# In-memory job store (good enough for hackathon).
JOBS: dict[str, dict] = {}


def _apify_token() -> str:
    return os.environ.get("APIFY_API_TOKEN") or os.environ.get("APIFY_API_KEY", "")


async def _resolve_store_ids(sources: list[dict]) -> None:
    """In-place: replace human-readable app names with bundle IDs the Apify actors expect."""
    loop = asyncio.get_running_loop()
    for cfg in sources:
        src = cfg.get("source", "").lower()
        query = cfg.get("query", "")
        if not query or query.startswith("http"):
            continue
        looks_like_id = "." in query and " " not in query
        if looks_like_id:
            continue
        country = cfg.get("country", "us")
        try:
            if src == "appstore":
                resolved = await loop.run_in_executor(None, resolve_appstore_id, query, country)
            elif src == "playstore":
                resolved = await loop.run_in_executor(None, resolve_playstore_id, query)
            else:
                continue
        except Exception as exc:
            logger.warning("resolver failed for %s '%s': %s", src, query, exc)
            continue

        if resolved:
            logger.info("resolved %s '%s' → '%s'", src, query, resolved)
            cfg["query"] = resolved


def _clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=[TEXT_COLUMN]).copy()
    df[TEXT_COLUMN] = df[TEXT_COLUMN].astype(str)
    df = df.drop_duplicates(subset=[TEXT_COLUMN])
    df = df[df[TEXT_COLUMN].str.len() > MIN_REVIEW_LEN].reset_index(drop=True)
    return df


def _quick_summary(df: pd.DataFrame) -> dict:
    summary = {
        "total_reviews": len(df),
        "sentiment_distribution": df["sentiment"].value_counts().to_dict(),
        "avg_compound": round(df["sentiment_compound"].mean(), 3),
    }
    if "theme_label" in df.columns:
        summary["themes"] = df["theme_label"].value_counts().head(10).to_dict()
    return summary


async def run_pipeline(job_id: str, req: AnalyzeRequest) -> None:
    """Execute the full scrape → quick → deep pipeline."""
    webhook = req.webhook_url
    loop = asyncio.get_running_loop()

    try:
        # 1. Scrape
        JOBS[job_id]["status"] = "scraping"
        await notify_frontend(webhook, job_id, "scraping", 0, "Collecting reviews from sources...")

        sources_input = [s.model_dump() for s in req.sources]
        await _resolve_store_ids(sources_input)

        df = await loop.run_in_executor(
            None, scraper_collect, sources_input, _apify_token()
        )

        if df.empty or TEXT_COLUMN not in df.columns:
            raise RuntimeError(
                "No reviews collected. Check the app name/ID, source, country, or APIFY token."
            )

        JOBS[job_id]["total_reviews"] = len(df)
        await notify_frontend(webhook, job_id, "scraping", 100, f"Collected {len(df)} reviews")

        # 2. Quick analysis
        JOBS[job_id]["status"] = "quick_analysis"
        await notify_frontend(webhook, job_id, "quick_analysis", 0, "Running sentiment analysis...")

        df = _clean_reviews(df)
        df = await loop.run_in_executor(None, analyze_sentiment, df, TEXT_COLUMN)
        await notify_frontend(webhook, job_id, "quick_analysis", 50, "Sentiment done. Clustering themes...")

        if len(df) >= MIN_ROWS_FOR_THEMES:
            df = await loop.run_in_executor(None, extract_themes, df, TEXT_COLUMN)

        quick_summary = _quick_summary(df)
        JOBS[job_id]["quick_result"] = quick_summary
        await notify_frontend(
            webhook, job_id, "quick_analysis", 100, "Quick analysis complete", data=quick_summary,
        )

        # 3. Deep analysis
        JOBS[job_id]["status"] = "deep_analysis"
        await notify_frontend(webhook, job_id, "deep_analysis", 0, "Running deep analysis with AI...")

        brand_dict = req.brand.model_dump()

        async def on_chunk_progress(completed: int, total: int) -> None:
            pct = round(completed / total * 80)  # 80% deep, 20% briefs
            await notify_frontend(
                webhook, job_id, "deep_analysis", pct,
                f"Analyzed {completed}/{total} chunks",
            )

        df = await analyze_deep(
            df, brand_dict,
            text_column=TEXT_COLUMN,
            chunk_size=CHUNK_SIZE,
            on_chunk_done=on_chunk_progress,
        )

        await notify_frontend(webhook, job_id, "deep_analysis", 85, "Generating creative briefs...")
        briefs, clusters = await generate_briefs(df, brand_dict)

        # 4. Final result
        result = {
            "brand_name": req.brand.name,
            "total_reviews": len(df),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": {"clusters": len(clusters), "briefs": len(briefs)},
            "sentiment_summary": quick_summary,
            "clusters": clusters,
            "briefs": briefs,
            "raw_analyses": df.to_dict(orient="records"),
        }

        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = result
        await notify_frontend(webhook, job_id, "done", 100, "Analysis complete", data=result)

    except Exception as exc:
        logger.error("job %s failed: %s\n%s", job_id, exc, traceback.format_exc())
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(exc)
        await notify_frontend(webhook, job_id, "error", 0, f"Error: {exc}")
