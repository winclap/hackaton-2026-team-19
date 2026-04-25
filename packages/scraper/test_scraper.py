"""End-to-end test: given an app name, scrape App Store + Play Store + X."""

import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from scraper.resolve import resolve_app_ids
from scraper.collector import collect

APP_NAME = "Holafly"
MAX_REVIEWS = 20  # keep small for testing

print(f"=== Scraper Test: {APP_NAME} ===\n")

# 1. Resolve IDs
print("1. Resolving app IDs...")
ids = resolve_app_ids(APP_NAME)
print(f"   App Store bundle ID: {ids['appstore_id']}")
print(f"   Play Store package:  {ids['playstore_id']}")

if not ids["appstore_id"] and not ids["playstore_id"]:
    print("ERROR: Could not resolve any app IDs")
    sys.exit(1)

# 2. Build source configs
sources = []

if ids["appstore_id"]:
    sources.append({
        "source": "appstore",
        "query": ids["appstore_id"],
        "country": "us",
        "max_reviews": MAX_REVIEWS,
    })

if ids["playstore_id"]:
    sources.append({
        "source": "playstore",
        "query": ids["playstore_id"],
        "country": "us",
        "max_reviews": MAX_REVIEWS,
    })

# X/Twitter — search mentions
sources.append({
    "source": "twitter",
    "query": f"{APP_NAME} esim",
    "max_tweets": MAX_REVIEWS,
})

print(f"\n2. Scraping {len(sources)} sources...")
for s in sources:
    print(f"   - {s['source']}: {s['query']}")

# 3. Collect
apify_token = os.environ.get("APIFY-API-KEY", "")
df = collect(sources, apify_token=apify_token)

# 4. Results
print(f"\n3. Results: {len(df)} total rows")
print(f"   By source: {df['source'].value_counts().to_dict()}")
print(f"   Columns: {list(df.columns)}")

if len(df) > 0:
    print("\n4. Sample rows:")
    for _, row in df.head(3).iterrows():
        print(f"   [{row['source']}] rating={row.get('rating','-')} | {str(row['content'])[:120]}...")

    # Save for inspection
    out = Path(__file__).parent / "test_output.json"
    df.to_json(out, orient="records", force_ascii=False, indent=2)
    print(f"\n   Full output saved to {out}")
