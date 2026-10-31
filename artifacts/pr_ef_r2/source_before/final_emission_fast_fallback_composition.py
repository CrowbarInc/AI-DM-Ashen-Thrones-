"""Fast-fallback neutral opening prose composition helpers.

Pure applicability checks, malformed-text detection, opening scene-template
authoring, and gate layer apply/default-meta for upstream fast-fallback paths.
Metadata merge timing and final emission route sequencing remain in
:mod:`game.final_emission_gate` / :mod:`game.final_emission_fem_assembly`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.anti_reset_emission_guard import _opening_scene_preference_active
from game.final_emission_scene_state_anchor import (
    _resolve_scene_state_anchor_contract,
    _title_case_anchor_phrase,
)
from game.final_emission_text_formatting import _normalize_text
from game.final_emission_text import _global_narrative_fallback_stock_line


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scene_inner(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, dict):
        return inner
    return scene


def _output_sentence(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def _scene_visible_facts(scene: Dict[str, Any] | None) -> List[str]:
    inner = _scene_inner(scene)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            out.append(clean)
    return _dedupe_preserve_order(out)


_FAST_FALLBACK_NEUTRAL_BAD_JOIN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bholds;\s+beside it\b", flags=re.IGNORECASE),
    re.compile(r"\bholds;\s+beside them\b", flags=re.IGNORECASE),
    re.compile(r"\bholds;\s+beside\b", flags=re.IGNORECASE),
)

_FAST_FALLBACK_NEUTRAL_SUBJECT_VERB_RE = re.compile(
    r"^(?:"
    r"is|was|stands?|keeps?|watches?|glances?|lingers?|waits?|looks?|holds?|moves?|speaks?|says?|"
    r"turns?|steps?|calls?|shouts?|scans?|studies?|gestures?|rests?|leans?|hangs?|offers?|questions?"
    r")\b",
    flags=re.IGNORECASE,
)
def _fast_fallback_neutral_composition_applicable(
    gm_output: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    strict_social_active: bool,
) -> bool:
    if strict_social_active or not _opening_scene_preference_active(session):
        return False
    tags = [str(t) for t in ((gm_output or {}).get("tags") or []) if isinstance(t, str)]
    return any(tag in tags for tag in ("upstream_api_fast_fallback", "forced_retry_fallback", "retry_escape_hatch"))


def _fast_fallback_bare_actor_header_detected(text: str, actor_tokens: List[str]) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    lowered = clean.lower()
    for raw in actor_tokens:
        token = str(raw or "").strip().lower()
        if len(token) < 3:
            continue
        display = _title_case_anchor_phrase(token)
        if not display:
            continue
        prefix = f"{display.lower()} "
        if not lowered.startswith(prefix):
            continue
        remainder = clean[len(display) :].lstrip(" ,;:-")
        if not remainder:
            return True
        if _FAST_FALLBACK_NEUTRAL_SUBJECT_VERB_RE.match(remainder):
            return False
        if remainder[:1].islower():
            return False
        return True
    return False


def _fast_fallback_neutral_composition_failure_reasons(
    text: str,
    *,
    gm_output: Dict[str, Any] | None,
) -> List[str]:
    reasons: List[str] = []
    clean = _normalize_text(text)
    if not clean:
        return reasons
    contract = _resolve_scene_state_anchor_contract(gm_output)
    actor_tokens = [str(tok) for tok in ((contract or {}).get("actor_tokens") or []) if isinstance(tok, str)]
    if actor_tokens and _fast_fallback_bare_actor_header_detected(clean, actor_tokens):
        reasons.append("bare_actor_header")
    if any(pattern.search(clean) for pattern in _FAST_FALLBACK_NEUTRAL_BAD_JOIN_PATTERNS):
        reasons.append("fact_fragment_collision")
    return _dedupe_preserve_order(reasons)


def _fast_fallback_opening_clean_scene_summary(scene: Dict[str, Any] | None) -> str:
    inner = _scene_inner(scene)
    summary = _normalize_text(str(inner.get("summary") or ""))
    if not summary:
        return ""
    first = re.split(r"(?<=[.!?])\s+", summary, maxsplit=1)[0].strip()
    if not first:
        return ""
    if ";" in first:
        first = first.split(";", 1)[0].strip(" ,;:-")
    return _output_sentence(first)


def _fast_fallback_opening_detail_candidates(
    scene: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None,
) -> List[str]:
    contract = _resolve_scene_state_anchor_contract(gm_output)
    actor_tokens = [str(tok) for tok in ((contract or {}).get("actor_tokens") or []) if isinstance(tok, str)]
    details: List[str] = []
    for fact in _scene_visible_facts(scene):
        clean = _output_sentence(fact)
        if not clean:
            continue
        if any(pattern.search(clean) for pattern in _FAST_FALLBACK_NEUTRAL_BAD_JOIN_PATTERNS):
            continue
        if actor_tokens and _fast_fallback_bare_actor_header_detected(clean, actor_tokens):
            continue
        details.append(clean)
    return _dedupe_preserve_order(details)


def _build_fast_fallback_opening_scene_template(
    scene: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None,
    scene_id: str,
) -> str:
    lead = _fast_fallback_opening_clean_scene_summary(scene)
    details = _fast_fallback_opening_detail_candidates(scene, gm_output=gm_output)
    parts: List[str] = []
    if lead:
        parts.append(lead)
    if details:
        for detail in details:
            if lead and _normalize_text(detail).lower() == _normalize_text(lead).lower():
                continue
            parts.append(detail)
            break
    if parts:
        return _normalize_text(" ".join(parts[:2]))
    return _normalize_text(
        _global_narrative_fallback_stock_line(scene if isinstance(scene, dict) else None, scene_id=scene_id)
    )


def default_fast_fallback_neutral_composition_meta() -> Dict[str, Any]:
    return {
        "fast_fallback_neutral_composition_checked": False,
        "fast_fallback_neutral_composition_applicable": False,
        "fast_fallback_neutral_composition_malformed_detected": False,
        "fast_fallback_neutral_composition_failure_reasons": [],
        "fast_fallback_neutral_composition_repaired": False,
        "fast_fallback_neutral_composition_repair_mode": None,
    }


def apply_fast_fallback_neutral_composition_layer(
    text: str,
    *,
    gm_output: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
    strict_social_active: bool,
) -> tuple[str, Dict[str, Any]]:
    meta = default_fast_fallback_neutral_composition_meta()
    if not _fast_fallback_neutral_composition_applicable(
        gm_output,
        session=session,
        strict_social_active=strict_social_active,
    ):
        return text, meta
    meta["fast_fallback_neutral_composition_checked"] = True
    meta["fast_fallback_neutral_composition_applicable"] = True
    reasons = _fast_fallback_neutral_composition_failure_reasons(text, gm_output=gm_output)
    if not reasons:
        return text, meta
    meta["fast_fallback_neutral_composition_malformed_detected"] = True
    meta["fast_fallback_neutral_composition_failure_reasons"] = reasons
    meta["fast_fallback_neutral_composition_boundary_semantic_repair_disabled"] = True
    return text, meta
