"""Webhook caller for frontend progress updates."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 5.0


async def notify_frontend(
    webhook_url: str | None,
    job_id: str,
    status: str,
    progress: float = 0.0,
    message: str = "",
    data: dict | None = None,
) -> None:
    """POST a progress update to the frontend webhook."""
    if not webhook_url:
        return

    payload = {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
    }
    if data is not None:
        payload["data"] = data

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            await client.post(webhook_url, json=payload)
    except httpx.HTTPError as exc:
        logger.warning("webhook %s failed: %s", webhook_url, exc)
