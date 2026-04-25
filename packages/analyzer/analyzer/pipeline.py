"""Pipeline orchestration: quick (ML) and deep (Bedrock Claude) analysis steps."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .sentiment import analyze_sentiment
from .themes import extract_themes
from .deep import analyze_deep
from .briefs import generate_briefs


def run_quick_analysis(
    df: pd.DataFrame,
    text_column: str = "content",
    n_clusters: int = 8,
) -> pd.DataFrame:
    """Run fast local ML analysis: VADER sentiment + TF-IDF theme clustering.

    No API calls. Returns DataFrame with sentiment + theme columns.
    """
    df = df.dropna(subset=[text_column]).copy()
    df[text_column] = df[text_column].astype(str)
    df = df.drop_duplicates(subset=[text_column])
    df = df[df[text_column].str.len() > 30].reset_index(drop=True)

    df = analyze_sentiment(df, text_column=text_column)

    if len(df) >= 10:
        df = extract_themes(df, text_column=text_column, n_clusters=n_clusters)

    return df


def run_deep_analysis(
    df: pd.DataFrame,
    brand_config: dict,
    text_column: str = "content",
    chunk_size: int = 15,
    max_concurrent: int = 10,
    on_chunk_done: Any = None,
) -> dict:
    """Run deep Bedrock-Claude analysis + brief generation.

    Returns dict with keys: df, briefs, clusters
    """
    df = analyze_deep(
        df, brand_config,
        text_column=text_column,
        chunk_size=chunk_size,
        max_concurrent=max_concurrent,
        on_chunk_done=on_chunk_done,
    )

    briefs, clusters = generate_briefs(df, brand_config)

    return {
        "df": df,
        "briefs": briefs,
        "clusters": clusters,
    }
