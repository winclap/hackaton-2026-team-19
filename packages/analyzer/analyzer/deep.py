"""Deep analysis using Claude Haiku 4.5 on AWS Bedrock, in chunks.

Sends reviews in batches (not row-by-row) to minimize API calls.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

import pandas as pd
from anthropic import AsyncAnthropicBedrock

from ._bedrock import DEEP_ANALYSIS_MODEL, client_kwargs
from ._json import parse_json_payload

logger = logging.getLogger(__name__)

CHUNK_SIZE = 15
MAX_CONCURRENT = 10
MAX_REVIEW_CHARS = 900
MAX_TOKENS = 4500

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


DEEP_ANALYSIS_COLUMNS = (
    "theme",
    "emotion",
    "funnel_stage",
    "job_to_be_done",
    "pain_or_delight",
    "moment",
    "quotable",
    "verbatim_quote",
    "creative_potential",
    "strategic_signal",
)


ProgressCallback = Callable[[int, int], Awaitable[None]]


def _build_prompt(reviews: list[str], brand_config: dict) -> str:
    reviews_block = "\n\n".join(
        f"[{i + 1}] {r[:MAX_REVIEW_CHARS]}" for i, r in enumerate(reviews)
    )
    return DEEP_ANALYSIS_PROMPT.format(
        brand_name=brand_config.get("name", ""),
        category=brand_config.get("category", ""),
        audience=brand_config.get("audience", ""),
        reviews_block=reviews_block,
    )


async def _analyze_chunk(
    client: AsyncAnthropicBedrock,
    reviews: list[str],
    brand_config: dict,
    semaphore: asyncio.Semaphore,
    chunk_idx: int,
) -> list[dict]:
    async with semaphore:
        try:
            resp = await client.messages.create(
                model=DEEP_ANALYSIS_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": _build_prompt(reviews, brand_config)}],
            )
            parsed = parse_json_payload(resp.content[0].text)
            if not isinstance(parsed, list):
                raise ValueError(f"expected JSON array, got {type(parsed).__name__}")
            return parsed
        except Exception:
            logger.exception("chunk %d failed", chunk_idx)
            return [{} for _ in reviews]


async def _analyze_all_chunks(
    reviews: list[str],
    brand_config: dict,
    chunk_size: int,
    max_concurrent: int,
    on_chunk_done: ProgressCallback | None,
) -> list[dict]:
    client = AsyncAnthropicBedrock(**client_kwargs())
    semaphore = asyncio.Semaphore(max_concurrent)

    chunks = [reviews[i:i + chunk_size] for i in range(0, len(reviews), chunk_size)]
    total_chunks = len(chunks)
    logger.info(
        "deep analysis: %d reviews in %d chunks of %d",
        len(reviews), total_chunks, chunk_size,
    )

    chunk_results: list[list[dict]] = [[] for _ in chunks]

    async def run_chunk(idx: int, chunk: list[str]) -> int:
        chunk_results[idx] = await _analyze_chunk(client, chunk, brand_config, semaphore, idx)
        return idx

    tasks = [asyncio.create_task(run_chunk(i, c)) for i, c in enumerate(chunks)]
    completed = 0
    for finished in asyncio.as_completed(tasks):
        await finished
        completed += 1
        if on_chunk_done is not None:
            await on_chunk_done(completed, total_chunks)

    results: list[dict] = []
    for chunk_data in chunk_results:
        results.extend(chunk_data)
    return results


def _empty_analysis_frame(rows: int) -> pd.DataFrame:
    return pd.DataFrame({col: [None] * rows for col in DEEP_ANALYSIS_COLUMNS})


async def analyze_deep(
    df: pd.DataFrame,
    brand_config: dict,
    text_column: str = "content",
    chunk_size: int = CHUNK_SIZE,
    max_concurrent: int = MAX_CONCURRENT,
    on_chunk_done: ProgressCallback | None = None,
) -> pd.DataFrame:
    """Run deep analysis on reviews using Claude Haiku 4.5 on Bedrock, in chunks."""
    df = df.copy()
    reviews = df[text_column].fillna("").astype(str).tolist()

    if not reviews:
        for col in DEEP_ANALYSIS_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df

    analyses = await _analyze_all_chunks(
        reviews, brand_config,
        chunk_size=chunk_size,
        max_concurrent=max_concurrent,
        on_chunk_done=on_chunk_done,
    )

    df_analysis = pd.DataFrame([a or {} for a in analyses])
    if df_analysis.empty:
        df_analysis = _empty_analysis_frame(len(df))

    for col in DEEP_ANALYSIS_COLUMNS:
        if col not in df_analysis.columns:
            df_analysis[col] = None

    if len(df_analysis) != len(df):
        raise RuntimeError(
            f"deep analysis row mismatch: got {len(df_analysis)} for {len(df)} reviews"
        )

    for col in DEEP_ANALYSIS_COLUMNS:
        df[col] = df_analysis[col].values

    return df
