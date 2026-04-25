"""Webhook caller for frontend progress updates."""

from __future__ import annotations

import httpx


async def notify_frontend(
    webhook_url: str | None,
    job_id: str,
    status: str,
    progress: float = 0.0,
    message: str = "",
    data: dict | None = None,
) -> None:
    """POST a progress update to the frontend webhook. Fire-and-forget."""
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
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json=payload)
    except Exception as e:
        print(f"[webhook] Failed to notify {webhook_url}: {e}")
