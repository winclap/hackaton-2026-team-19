"""Thin wrapper around the Apify API client."""

from __future__ import annotations

import os
from apify_client import ApifyClient as _ApifyClient


def get_apify_client(token: str | None = None) -> _ApifyClient:
    token = token or os.environ.get("APIFY-API-KEY") or os.environ.get("APIFY_API_TOKEN")
    if not token:
        raise ValueError("APIFY_API_TOKEN not set. Pass it or set the env var.")
    return _ApifyClient(token)


class ApifyClient:
    """High-level client that runs an Apify actor and returns the dataset items."""

    def __init__(self, token: str | None = None):
        self._client = get_apify_client(token)

    def run_actor(self, actor_id: str, run_input: dict, timeout_secs: int = 300) -> list[dict]:
        run = self._client.actor(actor_id).call(run_input=run_input, timeout_secs=timeout_secs)
        dataset_id = run["defaultDatasetId"]
        items = list(self._client.dataset(dataset_id).iterate_items())
        return items
