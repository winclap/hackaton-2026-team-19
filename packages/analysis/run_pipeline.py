"""Run the full analysis pipeline from CLI."""

import asyncio
import json
import time
from pathlib import Path

import nest_asyncio
import pandas as pd
from anthropic import AnthropicBedrock, AsyncAnthropicBedrock
from dotenv import load_dotenv

nest_asyncio.apply()

load_dotenv(Path(__file__).parent.parent.parent / ".env")

CSV_PATH = Path(__file__).parent / "data" / "app store US holafly - dataset_appstore-reviews-scraper_2026-04-23_18-08-17-782.csv"
REVIEW_TEXT_COLUMN = "content"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

BRAND_CONFIG = {
    "name": "Holafly",
    "category": "eSIM internacional para viajeros (datos moviles sin roaming)",
    "audience": "Viajeros internacionales, nomades digitales, turistas que buscan conectividad sin depender de SIM fisicas o roaming",
    "nonnegotiables": [
        "No mencionar competidores por nombre (Airalo, Nomad, SimOptions)",
        "Tono viajero, accesible, no telecom corporativo",
        "Resaltar la simplicidad de activacion y la tranquilidad de estar conectado",
    ],
}

AWS_PROFILE = "sandbox"
AWS_REGION = "us-east-1"
MODEL_TAGGING = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
MODEL_BRIEFS = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
BATCH_SIZE = 10
MAX_CONCURRENT = 8

client_async = AsyncAnthropicBedrock(aws_profile=AWS_PROFILE, aws_region=AWS_REGION)
client_sync = AnthropicBedrock(aws_profile=AWS_PROFILE, aws_region=AWS_REGION)

ANALYSIS_PROMPT = """You are a consumer insights analyst for Winclap, a growth marketing agency. \
You analyze real consumer voice data to extract creative advertising insights.

BRAND CONTEXT:
- Brand: {brand_name}
- Category: {category}
- Target audience: {audience}

Your task: analyze a batch of user reviews and extract structured insights.

Return ONLY a valid JSON array with one object per review, in the same order as the input. \
For each review provide:

{{
  "theme": a 2-3 word theme tag IN ENGLISH, lowercase_with_underscores,
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "emotion": one single dominant emotion as one word,
  "funnel_stage": "awareness" | "consideration" | "purchase" | "activation" | "usage" | "retention",
  "job_to_be_done": one specific sentence,
  "pain_or_delight": the concrete friction or aha moment in their own words,
  "moment": the physical/emotional situation in one short phrase,
  "quotable": true if this review contains a vivid verbatim phrase usable in an ad, else false,
  "verbatim_quote": exact snippet max 25 words if quotable, else null,
  "creative_potential": integer 1-10,
  "strategic_signal": if this review reveals a product/positioning opportunity, one sentence; else null
}}

Reviews to analyze (numbered, keep order in output):
{reviews_block}

Return ONLY the JSON array. No preamble, no markdown fences, no explanation."""

BRIEFS_PROMPT = """You are the Creative Strategy Director at Winclap. \
You just received a Voice Intelligence Report from {brand_name}'s customers. \
Produce 10 creative briefs for paid social ads (Meta, TikTok, YouTube) grounded in REAL consumer voice.

BRAND CONTEXT:
- Brand: {brand_name}
- Category: {category}
- Audience: {audience}
- Non-negotiables: {nonnegotiables}

INPUT DATA -- clustered customer signals:
{cluster_summaries}

TOP VERBATIM QUOTES BY THEME:
{top_quotes}

Generate 10 creative briefs, DIVERSE across angle, format, funnel stage, and segment.

For each brief return JSON:
{{
  "brief_id": 1-10,
  "title": short memorable name,
  "hook": verbatim or tight paraphrase from a real customer,
  "insight": the underlying human truth,
  "customer_quote_source": the literal quote that inspired this,
  "angle": emotional | rational | social_proof | fomo | problem_agitation | transformation,
  "format": UGC_video | static | carousel | reaction_video | testimonial | founder_pov | comparison,
  "funnel_stage": awareness | consideration | conversion,
  "target_segment": who this ad is for,
  "script_concept": 2-3 sentences describing what happens,
  "cta": specific call to action,
  "why_this_wins": one sentence on why this beats typical category ads
}}

Output a valid JSON array of exactly 10 briefs. No text before or after."""


def strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


async def analyze_batch(reviews_batch, semaphore, batch_idx):
    async with semaphore:
        reviews_block = "\n\n".join(
            f"[{i+1}] {r[:900]}" for i, r in enumerate(reviews_batch)
        )
        prompt = ANALYSIS_PROMPT.format(
            brand_name=BRAND_CONFIG["name"],
            category=BRAND_CONFIG["category"],
            audience=BRAND_CONFIG["audience"],
            reviews_block=reviews_block,
        )
        try:
            resp = await client_async.messages.create(
                model=MODEL_TAGGING, max_tokens=4500,
                messages=[{"role": "user", "content": prompt}],
            )
            return json.loads(strip_fences(resp.content[0].text))
        except Exception as e:
            print(f"  batch {batch_idx} error: {e}")
            return [None] * len(reviews_batch)


async def analyze_all(reviews):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    batches = [reviews[i:i+BATCH_SIZE] for i in range(0, len(reviews), BATCH_SIZE)]
    print(f"Analyzing {len(reviews)} reviews in {len(batches)} batches...")
    tasks = [analyze_batch(b, semaphore, i) for i, b in enumerate(batches)]
    results_nested = await asyncio.gather(*tasks)
    results = []
    for br in results_nested:
        results.extend(br)
    return results


def generate_briefs(df_full):
    df_valid = df_full.dropna(subset=["theme"])
    clusters = []
    for theme, group in df_valid.groupby("theme"):
        top_quotes = (
            group[group["quotable"] == True]
            .sort_values("creative_potential", ascending=False)["verbatim_quote"]
            .dropna().head(5).tolist()
        )
        clusters.append({
            "theme": theme,
            "volume": len(group),
            "pct_of_total": round(len(group) / len(df_valid) * 100, 1),
            "top_emotions": group["emotion"].value_counts().head(3).to_dict(),
            "top_moments": group["moment"].dropna().value_counts().head(5).index.tolist(),
            "top_jobs": group["job_to_be_done"].dropna().value_counts().head(3).index.tolist(),
            "top_quotes": top_quotes,
        })
    clusters.sort(key=lambda c: c["volume"], reverse=True)

    top_quotes_global = (
        df_valid[df_valid["quotable"] == True]
        .sort_values("creative_potential", ascending=False)["verbatim_quote"]
        .dropna().head(30).tolist()
    )
    top_quotes_text = "\n".join(f'- "{q}"' for q in top_quotes_global)
    cluster_summaries = json.dumps(
        [{k: v for k, v in c.items() if k != "top_quotes"} for c in clusters[:8]],
        indent=2, ensure_ascii=False,
    )

    prompt = BRIEFS_PROMPT.format(
        brand_name=BRAND_CONFIG["name"],
        category=BRAND_CONFIG["category"],
        audience=BRAND_CONFIG["audience"],
        nonnegotiables="; ".join(BRAND_CONFIG["nonnegotiables"]),
        cluster_summaries=cluster_summaries,
        top_quotes=top_quotes_text,
    )
    resp = client_sync.messages.create(
        model=MODEL_BRIEFS, max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    briefs = json.loads(strip_fences(resp.content[0].text))
    return briefs, clusters


def main():
    start = time.time()

    # 1. Load
    print(f"Loading {CSV_PATH.name}...")
    df_raw = pd.read_csv(CSV_PATH)
    print(f"  {len(df_raw)} rows loaded")

    # 2. Clean
    df = df_raw.dropna(subset=[REVIEW_TEXT_COLUMN]).copy()
    df[REVIEW_TEXT_COLUMN] = df[REVIEW_TEXT_COLUMN].astype(str)
    df = df.drop_duplicates(subset=[REVIEW_TEXT_COLUMN])
    df = df[df[REVIEW_TEXT_COLUMN].str.len() > 30].reset_index(drop=True)
    reviews = df[REVIEW_TEXT_COLUMN].tolist()
    print(f"  {len(reviews)} reviews after cleaning")

    # 3. Analyze
    analyses = asyncio.run(analyze_all(reviews))
    df_analysis = pd.DataFrame([a if a else {} for a in analyses])
    df_full = pd.concat([df.reset_index(drop=True), df_analysis], axis=1)
    ok = df_full["theme"].notna().sum()
    print(f"  {ok}/{len(df_full)} classified successfully")

    # 4. Briefs
    print("Generating briefs...")
    briefs, clusters = generate_briefs(df_full)
    print(f"  {len(briefs)} briefs generated")

    elapsed = time.time() - start

    # 5. Save
    df_full.to_csv(OUTPUT_DIR / "reviews_analyzed.csv", index=False)
    df_full.to_json(OUTPUT_DIR / "analyses.json", orient="records", force_ascii=False, indent=2)

    final_report = {
        "meta": {"brand": BRAND_CONFIG["name"], "total_reviews": len(df_full), "runtime_seconds": round(elapsed, 1)},
        "clusters": clusters,
        "briefs": briefs,
    }
    with open(OUTPUT_DIR / "voice_report.json", "w") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"\nDone in {elapsed:.0f}s. Saved to {OUTPUT_DIR}/")
    print(f"  voice_report.json  ({len(clusters)} clusters, {len(briefs)} briefs)")
    print(f"  analyses.json      ({len(df_full)} reviews)")
    print(f"  reviews_analyzed.csv")


if __name__ == "__main__":
    main()
