"""Creative brief generation using Claude Sonnet 4.5 on AWS Bedrock."""

from __future__ import annotations

import json
import re as _re

import pandas as pd
from anthropic import AnthropicBedrock


AWS_PROFILE = "sandbox"
AWS_REGION = "us-east-1"
MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

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


def generate_briefs(
    df: pd.DataFrame,
    brand_config: dict,
) -> tuple[list[dict], list[dict]]:
    """Generate creative briefs from analyzed data.

    Returns (briefs, clusters) tuple.
    """
    df_valid = df.dropna(subset=["theme"])
    clusters = []
    for theme, group in df_valid.groupby("theme"):
        top_quotes = (
            group[group.get("quotable", pd.Series([False] * len(group))) == True]
            .sort_values("creative_potential", ascending=False)
            .get("verbatim_quote", pd.Series())
            .dropna().head(5).tolist()
        ) if "quotable" in group.columns and "creative_potential" in group.columns else []

        clusters.append({
            "theme": theme,
            "volume": len(group),
            "pct_of_total": round(len(group) / max(len(df_valid), 1) * 100, 1),
            "top_emotions": group["emotion"].value_counts().head(3).to_dict() if "emotion" in group.columns else {},
            "top_quotes": top_quotes,
        })
    clusters.sort(key=lambda c: c["volume"], reverse=True)

    top_quotes_global = []
    if "quotable" in df_valid.columns and "creative_potential" in df_valid.columns:
        top_quotes_global = (
            df_valid[df_valid["quotable"] == True]
            .sort_values("creative_potential", ascending=False)
            .get("verbatim_quote", pd.Series())
            .dropna().head(30).tolist()
        )

    client = AnthropicBedrock(aws_profile=AWS_PROFILE, aws_region=AWS_REGION)
    prompt = BRIEFS_PROMPT.format(
        brand_name=brand_config.get("name", ""),
        category=brand_config.get("category", ""),
        audience=brand_config.get("audience", ""),
        nonnegotiables="; ".join(brand_config.get("nonnegotiables", [])),
        cluster_summaries=json.dumps(clusters[:8], indent=2, ensure_ascii=False),
        top_quotes="\n".join(f'- "{q}"' for q in top_quotes_global),
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    briefs = _parse_json(resp.content[0].text)
    return briefs, clusters
