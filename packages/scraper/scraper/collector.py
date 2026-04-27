"""High-level collection: run one or more sources, return unified DataFrame."""

from __future__ import annotations

import logging

import pandas as pd

from .client import ApifyClient
from .sources import get_source

logger = logging.getLogger(__name__)


def collect(
    sources: list[dict],
    apify_token: str | None = None,
) -> pd.DataFrame:
    """Collect data from multiple Apify sources and return a unified DataFrame.

    Args:
        sources: list of dicts, each with:
            - "source": one of the registered source names (appstore, playstore, twitter, reddit, trustpilot)
            - "query": the search term or URL to scrape
            - plus any source-specific kwargs (country, max_reviews, etc.)
        apify_token: optional Apify API token (defaults to env var)

    Returns:
        pd.DataFrame with normalized columns: id, source, product_name, rating, title, content, author, date_posted, url
    """
    client = ApifyClient(token=apify_token)
    all_rows: list[dict] = []

    for src_cfg in sources:
        source_name = src_cfg["source"]
        query = src_cfg["query"]
        kwargs = {k: v for k, v in src_cfg.items() if k not in ("source", "query")}

        ds = get_source(source_name)
        run_input = ds.build_input(query, **kwargs)

        logger.info("running %s actor (%s) for '%s'", ds.name, ds.actor_id, query)
        raw_items = client.run_actor(ds.actor_id, run_input)
        logger.info("got %d raw items from %s", len(raw_items), ds.name)

        normalized = ds.normalize(raw_items)
        all_rows.extend(normalized)

    df = pd.DataFrame(all_rows)

    # Drop rows with empty content
    if "content" in df.columns:
        df = df[df["content"].astype(str).str.strip().str.len() > 0]

    return df.reset_index(drop=True)
