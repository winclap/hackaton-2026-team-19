import json
import time
from datetime import datetime, timezone
from pathlib import Path

from anthropic import AnthropicBedrock
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent.parent / ".env")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path(__file__).parent / "output"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

AWS_PROFILE = "sandbox"
AWS_REGION = "us-east-1"
MODEL_BRIEFS = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

client = AnthropicBedrock(aws_profile=AWS_PROFILE, aws_region=AWS_REGION)

REFINE_PROMPT = """\
You are preparing a polished Voice Intelligence Report dashboard for {brand_name}, \
an eSIM brand for international travelers.

You have raw analysis of {total_reviews} customer reviews organized into \
{n_clusters} theme clusters and {n_briefs} creative briefs.

TASK 1 — Consolidate into exactly 6 major clusters. Merge related themes. For each return:
{{
  "theme": "Title Case Theme Name (2-4 words)",
  "volume": <sum of merged clusters volumes>,
  "percentage": <round(volume/{total_reviews}*100, 1)>,
  "top_emotions": ["emotion1", "emotion2", "emotion3"],
  "top_moment": "one vivid situational phrase, max 12 words",
  "featured_quote": "the most powerful verbatim quote from the data, max 25 words, from the actual top_quotes provided"
}}

TASK 2 — Polish all 10 briefs to be pitch-deck ready. Make hooks punchier (max 10 words), \
titles catchier, scripts more visual and cinematic. For each return:
{{
  "brief_id": <1-10>,
  "title": "The Catchy Title",
  "hook": "Max 10 words. Punchy. From a real quote.",
  "customer_quote_source": "the real verbatim quote this came from",
  "angle": "<keep or refine>",
  "format": "<specific ad format like 15s vertical UGC, static carousel, etc>",
  "funnel_stage": "awareness|consideration|conversion",
  "target_segment": "<specific segment>",
  "script_concept": "2-3 vivid sentences. Visual. Cinematic.",
  "cta": "short memorable CTA, max 6 words",
  "why_this_wins": "one killer sentence explaining why this creative beats typical category ads"
}}

RAW CLUSTERS:
{clusters_json}

RAW BRIEFS:
{briefs_json}

Return ONLY valid JSON: {{"clusters": [...6 items...], "briefs": [...10 items...]}}
No markdown fences. No preamble. No explanation."""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


class AnalyzeRequest(BaseModel):
    brand: str


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    cache_key = req.brand.lower().replace(" ", "_")
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        return json.loads(cache_file.read_text())

    # Load raw data
    voice_report = json.loads((OUTPUT_DIR / "voice_report.json").read_text())
    raw_analyses = json.loads((OUTPUT_DIR / "analyses.json").read_text())

    total_reviews = voice_report["meta"]["total_reviews"]
    original_runtime = voice_report["meta"]["runtime_seconds"]

    # Call Claude to refine
    start = time.time()

    prompt = REFINE_PROMPT.format(
        brand_name=req.brand,
        total_reviews=total_reviews,
        n_clusters=len(voice_report["clusters"]),
        n_briefs=len(voice_report["briefs"]),
        clusters_json=json.dumps(voice_report["clusters"], indent=2, ensure_ascii=False),
        briefs_json=json.dumps(voice_report["briefs"], indent=2, ensure_ascii=False),
    )

    resp = client.messages.create(
        model=MODEL_BRIEFS,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    refine_time = time.time() - start
    refined = json.loads(_strip_fences(resp.content[0].text))

    # Cost estimation
    usage = resp.usage
    refine_cost = (usage.input_tokens * 3 + usage.output_tokens * 15) / 1_000_000

    # Estimate original analysis cost
    n_batches = (total_reviews + 9) // 10
    orig_cost = (n_batches * 2000 * 3 + n_batches * 3000 * 15) / 1_000_000 + 0.50
    total_cost = orig_cost + refine_cost

    result = {
        "brand_name": req.brand,
        "total_reviews": total_reviews,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "clusters": len(refined["clusters"]),
            "briefs": len(refined["briefs"]),
            "api_cost_usd": round(total_cost, 2),
            "runtime_seconds": round(original_runtime + refine_time),
        },
        "clusters": refined["clusters"],
        "briefs": refined["briefs"],
        "raw_analyses": raw_analyses,
    }

    cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result
