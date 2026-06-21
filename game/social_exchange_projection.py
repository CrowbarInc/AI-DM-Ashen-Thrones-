"""Strict-social telemetry and FEM/realization projection (BV14A canonical owner)."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, MutableMapping

from game.social_exchange_validation import _looks_like_interruption_breakoff_text

from game.realization_provenance import (
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    attach_realization_fallback_family,
    normalize_realization_fallback_family,
)

_log = logging.getLogger(__name__)

def stamp_strict_social_deterministic_fallback_family(
    meta: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Stamp strict-social deterministic fallback family on emission/debug metadata."""
    return attach_realization_fallback_family(meta, STRICT_SOCIAL_DETERMINISTIC_FALLBACK)

def strict_social_deterministic_fallback_family_token() -> str:
    """Canonical token for strict-social details/FEM literals (known family constant)."""
    return STRICT_SOCIAL_DETERMINISTIC_FALLBACK

def project_strict_social_replace_realization_family(existing: str | None = None) -> str:
    """Normalized family for strict-social terminal replace FEM (details trace optional)."""
    return normalize_realization_fallback_family(
        str(existing if (existing not in (None, "")) else STRICT_SOCIAL_DETERMINISTIC_FALLBACK)
    )

_UNCERTAINTY_TAG_PREFIX = "uncertainty:"

_MOMENTUM_TAG_PREFIX = "scene_momentum:"

def log_final_emission_decision(payload: Dict[str, Any]) -> None:
    """Structured, concise server log line for final handoff debugging."""
    try:
        _log.info("final_emission %s", json.dumps(payload, default=str, ensure_ascii=False))
    except (TypeError, ValueError):
        _log.info("final_emission %s", str(payload))

def log_final_emission_trace(payload: Dict[str, Any]) -> None:
    """Structured terminal record for the last writer before user-visible return."""
    try:
        _log.info("final_emission_trace %s", json.dumps(payload, default=str, ensure_ascii=False))
    except (TypeError, ValueError):
        _log.info("final_emission_trace %s", str(payload))

def _extract_uncertainty_source_from_tags(tags: List[str], text: str) -> str:
    lowered = text.lower()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        t = tag.strip().lower()
        if not t.startswith(_UNCERTAINTY_TAG_PREFIX):
            continue
        if "feasibility" in t:
            return "procedural_insufficiency"
        if any(v in t for v in ("identity", "location", "motive", "method", "quantity")):
            return "npc_ignorance"
    if "do not know" in lowered or "don't know" in lowered or "no names" in lowered:
        return "npc_ignorance"
    return "scene_ambiguity"

def _is_pressure_active(tags: List[str], session: Dict[str, Any] | None, scene_id: str) -> bool:
    low_tags = {str(t).strip().lower() for t in tags if isinstance(t, str)}
    if "topic_pressure_escalation" in low_tags:
        return True
    if any(t.startswith(_MOMENTUM_TAG_PREFIX) for t in low_tags):
        return True
    if not isinstance(session, dict) or not scene_id:
        return False
    runtime = ((session.get("scene_runtime") or {}).get(scene_id) if isinstance(session.get("scene_runtime"), dict) else {})
    if not isinstance(runtime, dict):
        return False
    current = runtime.get("topic_pressure_current") if isinstance(runtime.get("topic_pressure_current"), dict) else {}
    repeat_count = int(current.get("repeat_count", 0) or 0)
    return repeat_count >= 3

def emission_gate_uncertainty_source(tags: List[str], text: str) -> str:
    return _extract_uncertainty_source_from_tags(tags, text)

def emission_gate_pressure_active(tags: List[str], session: Dict[str, Any] | None, scene_id: str) -> bool:
    return _is_pressure_active(tags, session, scene_id)

def interruption_cue_present_in_text(text: str) -> bool:
    """Momentum tags alone must not select interruption fallback without diegetic cue."""
    return _looks_like_interruption_breakoff_text(text)


def emission_gate_interruption_active(tags: List[str], text: str) -> bool:
    _ = tags
    return interruption_cue_present_in_text(text)
