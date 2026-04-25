"""Registry of Apify data sources.

Each source defines:
- actor_id: the Apify actor to run
- build_input(query, **kwargs): returns the actor run_input dict
- normalize(items): converts raw Apify items to a common schema
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class DataSource:
    name: str
    actor_id: str
    build_input: Callable[..., dict]
    normalize: Callable[[list[dict]], list[dict]]
    text_field: str  # which field contains the review text after normalization


# ── Normalizer helpers ────────────────────────────────────────────────

def _norm_appstore(items: list[dict]) -> list[dict]:
    """Normalize easyapi/app-store-reviews-scraper output."""
    rows = []
    for it in items:
        rows.append({
            "id": it.get("id", ""),
            "source": "appstore",
            "product_name": it.get("app", it.get("appName", "")),
            "rating": it.get("rating", it.get("score")),
            "title": it.get("title"),
            "content": it.get("review", it.get("text", it.get("body", it.get("content", "")))),
            "author": it.get("userName", it.get("author", "")),
            "date_posted": it.get("date", it.get("updated", "")),
            "url": it.get("url", ""),
        })
    return rows


def _norm_playstore(items: list[dict]) -> list[dict]:
    """Normalize easyapi/google-play-reviews-scraper output."""
    rows = []
    for it in items:
        rows.append({
            "id": it.get("reviewId", it.get("id", "")),
            "source": "playstore",
            "product_name": it.get("appName", it.get("app", "")),
            "rating": it.get("stars", it.get("score", it.get("rating"))),
            "title": it.get("title"),
            "content": it.get("text", it.get("review", it.get("body", it.get("content", "")))),
            "author": it.get("userName", it.get("author", "")),
            "date_posted": it.get("date", it.get("at", "")),
            "url": it.get("reviewUrl", it.get("url", "")),
        })
    return rows


def _norm_twitter(items: list[dict]) -> list[dict]:
    """Normalize data-slayer/twitter-search output."""
    rows = []
    for it in items:
        # data-slayer output: tweet_id, screen_name, text, created_at, user_info{}
        user_info = it.get("user_info", {})
        author = it.get("screen_name", user_info.get("screen_name", ""))
        tweet_id = it.get("tweet_id", it.get("id", ""))
        url = f"https://x.com/{author}/status/{tweet_id}" if tweet_id else it.get("url", "")
        rows.append({
            "id": tweet_id,
            "source": "twitter",
            "product_name": "",
            "rating": None,
            "title": None,
            "content": it.get("text", it.get("full_text", it.get("body", ""))),
            "author": author,
            "date_posted": it.get("created_at", it.get("createdAt", it.get("date", ""))),
            "url": url,
        })
    return rows


def _norm_reddit(items: list[dict]) -> list[dict]:
    rows = []
    for it in items:
        body = it.get("body", it.get("text", ""))
        title = it.get("title", "")
        content = f"{title}\n{body}".strip() if title and body else (body or title)
        rows.append({
            "id": it.get("id", it.get("url", "")),
            "source": "reddit",
            "product_name": "",
            "rating": it.get("upVotes", it.get("score")),
            "title": title or None,
            "content": content,
            "author": it.get("username", it.get("author", "")),
            "date_posted": it.get("createdAt", it.get("date", "")),
            "url": it.get("url", ""),
        })
    return rows


def _norm_trustpilot(items: list[dict]) -> list[dict]:
    rows = []
    for it in items:
        rows.append({
            "id": it.get("id", ""),
            "source": "trustpilot",
            "product_name": it.get("companyName", it.get("businessUnit", "")),
            "rating": it.get("rating", it.get("stars")),
            "title": it.get("title"),
            "content": it.get("text", it.get("body", it.get("content", ""))),
            "author": it.get("consumer", {}).get("displayName", it.get("author", "")),
            "date_posted": it.get("dates", {}).get("publishedDate", it.get("date", "")),
            "url": it.get("url", ""),
        })
    return rows


# ── Input builders (matched to real Apify actor schemas) ─────────────

def _input_appstore(query: str, country: str = "us", max_reviews: int = 100, **_) -> dict:
    """easyapi/app-store-reviews-scraper expects: appId, country, limit"""
    return {
        "appId": query,
        "country": country,
        "limit": max_reviews,
    }


def _input_playstore(query: str, country: str = "us", max_reviews: int = 100, lang: str = "en", **_) -> dict:
    """easyapi/google-play-reviews-scraper expects: appId, maxItems, lang, country, sort"""
    return {
        "appId": query,
        "maxItems": max_reviews,
        "lang": lang,
        "country": country,
        "sort": "2",  # newest
    }


def _input_twitter(query: str, max_tweets: int = 100, **_) -> dict:
    """data-slayer/twitter-search expects: query, maxItems"""
    return {
        "query": query,
        "maxItems": max_tweets,
    }


def _input_reddit(query: str, max_posts: int = 500, **_) -> dict:
    return {
        "searches": [{"term": query, "sort": "new"}] if not query.startswith("http") else [],
        "startUrls": [{"url": query}] if query.startswith("http") else [],
        "maxPostCount": max_posts,
        "maxComments": 0,
    }


def _input_trustpilot(query: str, max_reviews: int = 500, **_) -> dict:
    return {
        "startUrls": [{"url": query}] if query.startswith("http") else [],
        "searchTerms": [] if query.startswith("http") else [query],
        "maxReviews": max_reviews,
    }


# ── Registry ──────────────────────────────────────────────────────────

SOURCES: dict[str, DataSource] = {
    "appstore": DataSource(
        name="App Store",
        actor_id="easyapi~app-store-reviews-scraper",
        build_input=_input_appstore,
        normalize=_norm_appstore,
        text_field="content",
    ),
    "playstore": DataSource(
        name="Play Store",
        actor_id="easyapi~google-play-reviews-scraper",
        build_input=_input_playstore,
        normalize=_norm_playstore,
        text_field="content",
    ),
    "twitter": DataSource(
        name="X / Twitter",
        actor_id="data-slayer~twitter-search",
        build_input=_input_twitter,
        normalize=_norm_twitter,
        text_field="content",
    ),
    "reddit": DataSource(
        name="Reddit",
        actor_id="trudax~reddit-scraper-lite",
        build_input=_input_reddit,
        normalize=_norm_reddit,
        text_field="content",
    ),
    "trustpilot": DataSource(
        name="Trustpilot",
        actor_id="epctex~trustpilot-reviews-scraper",
        build_input=_input_trustpilot,
        normalize=_norm_trustpilot,
        text_field="content",
    ),
}


def get_source(name: str) -> DataSource:
    src = SOURCES.get(name.lower())
    if not src:
        available = ", ".join(SOURCES.keys())
        raise ValueError(f"Unknown source '{name}'. Available: {available}")
    return src
