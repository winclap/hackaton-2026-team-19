"""Creative brief generation using Claude Sonnet 4.5 on AWS Bedrock."""

from __future__ import annotations

import json

import pandas as pd
from anthropic import AsyncAnthropicBedrock

from ._bedrock import BRIEFS_MODEL, client_kwargs
from ._json import parse_json_payload

MAX_TOKENS = 8000
TOP_QUOTES_PER_CLUSTER = 5
TOP_QUOTES_GLOBAL = 30
MAX_CLUSTERS_IN_PROMPT = 8


BRIEFS_PROMPT = """You are the Creative Strategy Director at Winclap. \
Produce 10 creative briefs for paid social ads (Meta, TikTok, YouTube) grounded in REAL consumer voice.

BRAND CONTEXT:
- Brand: {brand_name}
- Category: {category}
- Audience: {audience}
- Non-negotiables: {nonnegotiables}

CLUSTERED CUSTOMER SIGNALS:
{cluster_summaries}

TOP VERBATIM QUOTES:
{top_quotes}

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


def _ensure_theme_column(df: pd.DataFrame) -> pd.DataFrame:
    if "theme" in df.columns and df["theme"].notna().any():
        return df

    df = df.copy()
    if "theme_label" in df.columns:
        df["theme"] = df["theme_label"]
    else:
        df["theme"] = "general"
    return df


def _top_quotes(group: pd.DataFrame, limit: int) -> list[str]:
    if "quotable" not in group.columns or "verbatim_quote" not in group.columns:
        return []

    quotable = group[group["quotable"] == True]  # noqa: E712 — pandas mask
    if quotable.empty:
        return []

    if "creative_potential" in quotable.columns:
        quotable = quotable.sort_values("creative_potential", ascending=False)

    return quotable["verbatim_quote"].dropna().head(limit).tolist()


def _build_clusters(df: pd.DataFrame) -> list[dict]:
    total = max(len(df), 1)
    clusters: list[dict] = []
    for theme, group in df.groupby("theme"):
        clusters.append({
            "theme": theme,
            "volume": len(group),
            "pct_of_total": round(len(group) / total * 100, 1),
            "top_emotions": (
                group["emotion"].value_counts().head(3).to_dict()
                if "emotion" in group.columns else {}
            ),
            "top_quotes": _top_quotes(group, TOP_QUOTES_PER_CLUSTER),
        })
    clusters.sort(key=lambda c: c["volume"], reverse=True)
    return clusters


async def generate_briefs(
    df: pd.DataFrame,
    brand_config: dict,
) -> tuple[list[dict], list[dict]]:
    """Generate creative briefs from analyzed data.

    Returns (briefs, clusters) tuple.
    """
    df = _ensure_theme_column(df)
    df_valid = df.dropna(subset=["theme"])
    if df_valid.empty:
        df_valid = df.assign(theme="general")

    clusters = _build_clusters(df_valid)
    top_quotes_global = _top_quotes(df_valid, TOP_QUOTES_GLOBAL)

    prompt = BRIEFS_PROMPT.format(
        brand_name=brand_config.get("name", ""),
        category=brand_config.get("category", ""),
        audience=brand_config.get("audience", ""),
        nonnegotiables="; ".join(brand_config.get("nonnegotiables", [])),
        cluster_summaries=json.dumps(
            clusters[:MAX_CLUSTERS_IN_PROMPT], indent=2, ensure_ascii=False
        ),
        top_quotes="\n".join(f'- "{q}"' for q in top_quotes_global),
    )

    client = AsyncAnthropicBedrock(**client_kwargs())
    resp = await client.messages.create(
        model=BRIEFS_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    briefs = parse_json_payload(resp.content[0].text)
    if not isinstance(briefs, list):
        raise ValueError(f"expected briefs JSON array, got {type(briefs).__name__}")
    return briefs, clusters
