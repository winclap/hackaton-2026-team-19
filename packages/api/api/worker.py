"""Background worker that runs the full pipeline for a job."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Add sibling packages to path so we can import them
_packages_dir = Path(__file__).parent.parent.parent
for pkg in ("scraper", "analyzer"):
    pkg_path = str(_packages_dir / pkg)
    if pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)

from scraper.collector import collect as scraper_collect
from scraper.resolve import resolve_appstore_id, resolve_playstore_id
from analyzer.sentiment import analyze_sentiment
from analyzer.themes import extract_themes
from analyzer.deep import analyze_deep
from analyzer.briefs import generate_briefs

from .webhook import notify_frontend
from .models import AnalyzeRequest


# In-memory job store (good enough for hackathon)
JOBS: dict[str, dict] = {}


async def run_pipeline(job_id: str, req: AnalyzeRequest) -> None:
    """Execute the full scrape → quick → deep pipeline in background."""
    webhook = req.webhook_url

    try:
        # ── 1. Scrape ────────────────────────────────────────────
        JOBS[job_id]["status"] = "scraping"
        await notify_frontend(webhook, job_id, "scraping", 0, "Collecting reviews from sources...")

        apify_token = os.environ.get("APIFY-API-KEY", os.environ.get("APIFY_API_TOKEN", ""))
        sources_input = [s.model_dump() for s in req.sources]

        # Resolve app names → store IDs for appstore/playstore sources.
        # Apify actors expect bundle IDs (e.g. "com.grability.rappi"), not display names.
        loop = asyncio.get_event_loop()
        for cfg in sources_input:
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
                    resolved = await loop.run_in_executor(
                        None, lambda q=query, c=country: resolve_appstore_id(q, c)
                    )
                    if resolved:
                        print(f"[worker] Resolved appstore '{query}' → '{resolved}'")
                        cfg["query"] = resolved
                elif src == "playstore":
                    resolved = await loop.run_in_executor(
                        None, lambda q=query: resolve_playstore_id(q)
                    )
                    if resolved:
                        print(f"[worker] Resolved playstore '{query}' → '{resolved}'")
                        cfg["query"] = resolved
            except Exception as e:
                print(f"[worker] Resolver failed for {src} '{query}': {e}")

        # Run blocking Apify calls in thread pool
        df = await loop.run_in_executor(None, lambda: scraper_collect(sources_input, apify_token=apify_token))

        if df.empty or "content" not in df.columns:
            raise RuntimeError(
                "No reviews collected. Check the app name/ID, source, country, "
                "or APIFY token."
            )

        total = len(df)
        JOBS[job_id]["total_reviews"] = total
        await notify_frontend(webhook, job_id, "scraping", 100, f"Collected {total} reviews")

        # ── 2. Quick Analysis (ML local) ─────────────────────────
        JOBS[job_id]["status"] = "quick_analysis"
        await notify_frontend(webhook, job_id, "quick_analysis", 0, "Running sentiment analysis...")

        # Clean
        text_col = "content"
        df = df.dropna(subset=[text_col]).copy()
        df[text_col] = df[text_col].astype(str)
        df = df.drop_duplicates(subset=[text_col])
        df = df[df[text_col].str.len() > 30].reset_index(drop=True)

        # VADER sentiment
        df = await loop.run_in_executor(None, lambda: analyze_sentiment(df, text_column=text_col))
        await notify_frontend(webhook, job_id, "quick_analysis", 50, "Sentiment done. Clustering themes...")

        # TF-IDF themes
        if len(df) >= 10:
            df = await loop.run_in_executor(None, lambda: extract_themes(df, text_column=text_col))

        # Build quick summary
        quick_summary = {
            "total_reviews": len(df),
            "sentiment_distribution": df["sentiment"].value_counts().to_dict(),
            "avg_compound": round(df["sentiment_compound"].mean(), 3),
        }
        if "theme_label" in df.columns:
            quick_summary["themes"] = df["theme_label"].value_counts().head(10).to_dict()

        JOBS[job_id]["quick_result"] = quick_summary
        await notify_frontend(
            webhook, job_id, "quick_analysis", 100,
            "Quick analysis complete",
            data=quick_summary,
        )

        # ── 3. Deep Analysis (Haiku) ─────────────────────────────
        JOBS[job_id]["status"] = "deep_analysis"
        await notify_frontend(webhook, job_id, "deep_analysis", 0, "Running deep analysis with AI...")

        brand_dict = req.brand.model_dump()
        total_chunks = max(1, (len(df) + 14) // 15)
        chunks_done = 0

        async def on_chunk_progress(completed: int, total: int):
            nonlocal chunks_done
            chunks_done = completed
            pct = round(completed / total * 80)  # 80% for deep, 20% for briefs
            await notify_frontend(
                webhook, job_id, "deep_analysis", pct,
                f"Analyzed {completed}/{total} chunks",
            )

        # Deep analysis needs to run in a way that supports async
        df = analyze_deep(
            df, brand_dict,
            text_column=text_col,
            on_chunk_done=on_chunk_progress,
        )

        await notify_frontend(webhook, job_id, "deep_analysis", 85, "Generating creative briefs...")

        briefs, clusters = await loop.run_in_executor(
            None, lambda: generate_briefs(df, brand_dict)
        )

        # ── 4. Build final result ─────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()
        result = {
            "brand_name": req.brand.name,
            "total_reviews": len(df),
            "timestamp": now,
            "stats": {
                "clusters": len(clusters),
                "briefs": len(briefs),
            },
            "sentiment_summary": quick_summary,
            "clusters": clusters,
            "briefs": briefs,
            "raw_analyses": json.loads(df.to_json(orient="records", force_ascii=False)),
        }

        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = result
        await notify_frontend(webhook, job_id, "done", 100, "Analysis complete", data=result)

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[worker] Job {job_id} failed: {e}\n{tb}")
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)
        await notify_frontend(webhook, job_id, "error", 0, f"Error: {e}")
