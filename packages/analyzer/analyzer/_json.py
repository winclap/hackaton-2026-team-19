"""JSON extraction helper for LLM responses.

The Anthropic SDK returns plain text. When prompts ask for JSON, models
occasionally wrap the payload in ```json fences or include stray prose. This
helper strips those wrappers and parses the result.
"""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)
_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_BAD_ESCAPE_RE = re.compile(r'\\(?!["\\/bfnrtu])')


def parse_json_payload(text: str) -> list | dict:
    """Parse JSON from an LLM response, tolerating fences and bad escapes."""
    text = _FENCE_RE.sub("", text).strip()

    match = _ARRAY_RE.search(text) or _OBJECT_RE.search(text)
    if match:
        text = match.group(0)

    text = _BAD_ESCAPE_RE.sub(r"\\\\", text)
    return json.loads(text)
