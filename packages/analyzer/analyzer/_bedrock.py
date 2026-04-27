"""Shared Bedrock configuration for analyzer modules.

AWS profile/region are read from env at import time. When AWS_PROFILE is unset
the SDK falls back to the default AWS credential provider chain (env vars,
instance profile, SSO cache, etc.).
"""

from __future__ import annotations

import os

AWS_PROFILE = os.environ.get("AWS_PROFILE")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

DEEP_ANALYSIS_MODEL = os.environ.get(
    "BEDROCK_DEEP_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)
BRIEFS_MODEL = os.environ.get(
    "BEDROCK_BRIEFS_MODEL", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
)


def client_kwargs() -> dict:
    kwargs = {"aws_region": AWS_REGION}
    if AWS_PROFILE:
        kwargs["aws_profile"] = AWS_PROFILE
    return kwargs
