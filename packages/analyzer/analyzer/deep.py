"""Deep analysis using Claude Haiku 4.5 on AWS Bedrock, in chunks.

Sends reviews in batches (not row-by-row) to minimize API calls.
"""

from __future__ import annotations

import asyncio
import json
import re as _re
from typing import Any

import pandas as pd
from anthropic import AsyncAnthropicBedrock


AWS_PROFILE = "sandbox"
AWS_REGION = "us-east-1"
MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
CHUNK_SIZE = 15
MAX_CONCURRENT = 10

DEEP_ANALYSIS_PROMPT = """You are a consumer insights analyst. Analyze this batch of user reviews and return structured insights.

BRAND CONTEXT:
- Brand: {brand_name}
- Category: {category}
- Target audience: {audience}

Return ONLY a valid JSON array with one object per review, in the same order as input.
For each review provide:

{{
  "theme": a 2-3 word theme tag in english, lowercase_with_underscores,
  "emotion": one dominant emotion as one word,
  "funnel_stage": "awareness" | "consideration" | "purchase" | "activation" | "usage" | "retention",
  "job_to_be_done": one specific sentence,
  "pain_or_delight": the concrete friction or delight in their own words,
  "moment": the physical/emotional situation in one short phrase,
  "quotable": true if this review contains a vivid verbatim phrase usable in an ad, else false,
  "verbatim_quote": exact snippet max 25 words if quotable, else null,
  "creative_potential": integer 1-10,
  "strategic_signal": if this review reveals a product/positioning opportunity, one sentence; else null
}}

Reviews (numbered, keep order):
{reviews_block}

Return ONLY the JSON array. No preamble, no markdown fences."""


def _parse_json(text: str) -> list | dict:
    """Extract and parse JSON from LLM output, tolerating markdown fences and invalid escapes."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    for pattern in (r'\[.*\]', r'\{.*\}'):
        m = _re.search(pattern, text, _re.DOTALL)
        if m:
            text = m.group(0)
            break
    text = _re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
    return json.loads(text)


async def _analyze_chunk(
    client: AsyncAnthropicBedrock,
    reviews: list[str],
    brand_config: dict,
    semaphore: asyncio.Semaphore,
    chunk_idx: int,
) -> list[dict]:
    async with semaphore:
        reviews_block = "\n\n".join(
            f"[{i+1}] {r[:900]}" for i, r in enumerate(reviews)
        )
        prompt = DEEP_ANALYSIS_PROMPT.format(
            brand_name=brand_config.get("name", ""),
            category=brand_config.get("category", ""),
            audience=brand_config.get("audience", ""),
            reviews_block=reviews_block,
        )
        try:
            resp = await client.messages.create(
                model=MODEL,
                max_tokens=4500,
                messages=[{"role": "user", "content": prompt}],
            )
            return _parse_json(resp.content[0].text)
        except Exception as e:
            print(f"  [analyzer] chunk {chunk_idx} error: {e}")
            return [{}] * len(reviews)


async def _analyze_all_chunks(
    reviews: list[str],
    brand_config: dict,
    chunk_size: int = CHUNK_SIZE,
    max_concurrent: int = MAX_CONCURRENT,
    on_chunk_done: Any = None,
) -> list[dict]:
    client = AsyncAnthropicBedrock(aws_profile=AWS_PROFILE, aws_region=AWS_REGION)
    semaphore = asyncio.Semaphore(max_concurrent)

    chunks = [reviews[i:i + chunk_size] for i in range(0, len(reviews), chunk_size)]
    total_chunks = len(chunks)
    print(f"[analyzer] Deep analysis: {len(reviews)} reviews in {total_chunks} chunks of {chunk_size}")

    results: list[dict] = []
    tasks = [_analyze_chunk(client, c, brand_config, semaphore, i) for i, c in enumerate(chunks)]

    for i, coro in enumerate(asyncio.as_completed(tasks)):
        chunk_result = await coro
        results.extend(chunk_result)
        if on_chunk_done:
            await on_chunk_done(completed=i + 1, total=total_chunks)

    return results


def analyze_deep(
    df: pd.DataFrame,
    brand_config: dict,
    text_column: str = "content",
    chunk_size: int = CHUNK_SIZE,
    max_concurrent: int = MAX_CONCURRENT,
    on_chunk_done: Any = None,
) -> pd.DataFrame:
    """Run deep analysis on reviews using Claude Haiku 4.5 on Bedrock, in chunks."""
    df = df.copy()
    reviews = df[text_column].fillna("").astype(str).tolist()

    coro = _analyze_all_chunks(
        reviews, brand_config,
        chunk_size=chunk_size,
        max_concurrent=max_concurrent,
        on_chunk_done=on_chunk_done,
    )

    try:
        asyncio.get_running_loop()
        import nest_asyncio
        nest_asyncio.apply()
        analyses = asyncio.run(coro)
    except RuntimeError:
        analyses = asyncio.run(coro)

    df_analysis = pd.DataFrame([a if a else {} for a in analyses])

    deep_cols = [c for c in df_analysis.columns if c not in df.columns or c == "theme"]
    for col in deep_cols:
        df[col] = df_analysis[col].values[:len(df)] if col in df_analysis.columns else None

    return df
