"""Pipeline orchestration: quick (ML) and deep (Bedrock Claude) analysis steps."""

from __future__ import annotations

import pandas as pd

from .briefs import generate_briefs
from .deep import CHUNK_SIZE, MAX_CONCURRENT, ProgressCallback, analyze_deep
from .sentiment import analyze_sentiment
from .themes import extract_themes

MIN_ROWS_FOR_THEMES = 10
MIN_REVIEW_LEN = 30


def run_quick_analysis(
    df: pd.DataFrame,
    text_column: str = "content",
    n_clusters: int = 8,
) -> pd.DataFrame:
    """Run fast local ML analysis: VADER sentiment + TF-IDF theme clustering."""
    df = df.dropna(subset=[text_column]).copy()
    df[text_column] = df[text_column].astype(str)
    df = df.drop_duplicates(subset=[text_column])
    df = df[df[text_column].str.len() > MIN_REVIEW_LEN].reset_index(drop=True)

    df = analyze_sentiment(df, text_column=text_column)

    if len(df) >= MIN_ROWS_FOR_THEMES:
        df = extract_themes(df, text_column=text_column, n_clusters=n_clusters)

    return df


async def run_deep_analysis(
    df: pd.DataFrame,
    brand_config: dict,
    text_column: str = "content",
    chunk_size: int = CHUNK_SIZE,
    max_concurrent: int = MAX_CONCURRENT,
    on_chunk_done: ProgressCallback | None = None,
) -> dict:
    """Run deep Bedrock-Claude analysis + brief generation."""
    df = await analyze_deep(
        df, brand_config,
        text_column=text_column,
        chunk_size=chunk_size,
        max_concurrent=max_concurrent,
        on_chunk_done=on_chunk_done,
    )

    briefs, clusters = await generate_briefs(df, brand_config)

    return {"df": df, "briefs": briefs, "clusters": clusters}
