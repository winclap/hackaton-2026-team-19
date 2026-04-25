"""Resolve app names to store IDs using public APIs."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
import re


def resolve_appstore_id(app_name: str, country: str = "us") -> str | None:
    """Resolve an app name to its iOS bundle ID using the iTunes Search API.

    Returns the bundle ID (e.g. "com.holafly.Customers") or None.
    """
    params = urllib.parse.urlencode({
        "term": app_name,
        "entity": "software",
        "country": country,
        "limit": 1,
    })
    url = f"https://itunes.apple.com/search?{params}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    results = data.get("results", [])
    if results:
        return results[0]["bundleId"]
    return None


def resolve_playstore_id(app_name: str) -> str | None:
    """Resolve an app name to its Play Store package ID by scraping search results.

    Returns the package name (e.g. "com.holafly.holafly") or None.
    """
    params = urllib.parse.urlencode({"q": app_name, "c": "apps"})
    url = f"https://play.google.com/store/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    # Extract first package ID from the search results page
    match = re.search(r'/store/apps/details\?id=([a-zA-Z0-9_.]+)', html)
    if match:
        return match.group(1)
    return None


def resolve_app_ids(app_name: str, country: str = "us") -> dict:
    """Resolve an app name to both App Store and Play Store IDs.

    Returns dict with keys: appstore_id, playstore_id (either can be None).
    """
    appstore_id = None
    playstore_id = None

    try:
        appstore_id = resolve_appstore_id(app_name, country)
    except Exception as e:
        print(f"[resolve] App Store lookup failed: {e}")

    try:
        playstore_id = resolve_playstore_id(app_name)
    except Exception as e:
        print(f"[resolve] Play Store lookup failed: {e}")

    return {
        "appstore_id": appstore_id,
        "playstore_id": playstore_id,
    }
