"""Pydantic models for request/response."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    source: str = Field(..., description="Data source: appstore, playstore, twitter, reddit, trustpilot")
    query: str = Field(..., description="Search term or URL to scrape")
    country: str = Field(default="us")
    max_reviews: int = Field(default=500)


class BrandConfig(BaseModel):
    name: str
    category: str = ""
    audience: str = ""
    nonnegotiables: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    brand: BrandConfig
    sources: list[SourceConfig]
    webhook_url: str | None = Field(
        default=None,
        description="Frontend webhook URL to call with progress updates",
    )


class JobStatus(BaseModel):
    job_id: str
    status: str  # "scraping" | "quick_analysis" | "deep_analysis" | "done" | "error"
    progress: float = 0.0  # 0-100
    message: str = ""
    data: dict | None = None
