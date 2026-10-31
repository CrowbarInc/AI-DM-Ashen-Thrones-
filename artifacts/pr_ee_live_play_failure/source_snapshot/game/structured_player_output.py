"""Player-facing boundary for model output.

A structured GM response is parsed and reduced to its player-facing text
before sealing. A raw envelope, or an unparseable envelope, is rejected.
Ordinary narration may contain braces, colons, and quotes.
"""
from __future__ import annotations

import json
import re

_ENVELOPE_KEYS = frozenset(
    {
        "declared_claims",
        "narration",
        "player_facing_text",
        "improvisation_proposals",
        "debug_notes",
        "scene_update",
        "activate_scene_id",
        "new_scene_draft",
        "world_updates",
        "suggested_action",
    }
)
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
_KEY_RE = re.compile(
    r'"(?:player_facing_text|improvisation_proposals|debug_notes|scene_update|activate_scene_id|new_scene_draft|world_updates|suggested_action)"\s*:',
)


def is_response_envelope(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    keys = {str(key) for key in value}
    if "declared_claims" in keys and "narration" in keys:
        return True
    if "player_facing_text" in keys:
        return True
    return len(keys & _ENVELOPE_KEYS) >= 2


def _iter_objects(text: str):
    decoder = json.JSONDecoder()
    index = 0
    while True:
        start = text.find("{", index)
        if start < 0:
            return
        try:
            parsed, consumed = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        yield parsed
        index = start + consumed


def text_contains_response_envelope(text: str | None) -> bool:
    raw = str(text or "")
    if not raw.strip():
        return False
    for parsed in _iter_objects(raw):
        if is_response_envelope(parsed):
            return True
    return bool(_KEY_RE.search(raw) and "{" in raw)


def classify_model_output(text: str | None) -> dict:
    """Return form plain, structured, or malformed, plus extracted prose."""
    raw = str(text or "").strip()
    fenced = _FENCE_RE.match(raw)
    if fenced:
        raw = fenced.group(1).strip()
    if not raw:
        return {"form": "malformed", "player_facing_text": "", "fields": {}}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        if is_response_envelope(parsed):
            prose = parsed.get("narration") if "narration" in parsed else parsed.get("player_facing_text")
            if isinstance(prose, str) and prose.strip() and not text_contains_response_envelope(prose):
                return {"form": "structured", "player_facing_text": prose.strip(), "fields": parsed}
            return {"form": "malformed", "player_facing_text": "", "fields": {}}
        return {"form": "malformed", "player_facing_text": "", "fields": {}}
    if parsed is not None:
        return {"form": "malformed", "player_facing_text": "", "fields": {}}
    if text_contains_response_envelope(raw):
        return {"form": "malformed", "player_facing_text": "", "fields": {}}
    return {"form": "plain", "player_facing_text": raw, "fields": {}}
