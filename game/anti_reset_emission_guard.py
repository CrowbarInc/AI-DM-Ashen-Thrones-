"""Anti-reset guard: block scene-opener / intro-style stock fallbacks during established local exchange.

Retry and final-emission replacement paths sometimes pull diegetic lines composed from the same
visible facts and summary sentences as the opening scene paragraph. When the player is already
mid-exchange, those lines read as a spurious scene reset.

This module is intentionally narrow: it does not change routing, only eligibility of opener-like
fallback text when a stricter continuation-safe line is required.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional, Set

from game.interaction_context import inspect as inspect_interaction_context
from game.social_exchange_emission import effective_strict_social_resolution_for_emission, minimal_social_emergency_fallback_line

# Sources that emit broad scene-establishing / first-mention intro shapes (not minimal social beats).
SCENE_INTRO_EMITTER_SOURCES: frozenset[str] = frozenset(
    {
        "composed_visible_scene_intro",
        "explicit_visible_entity_scene_intro",
        "visible_fact_scene_intro",
        "global_scene_fallback",
    }
)

_OBSERVE_OPENER_HINTS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\byou take in the scene\b", re.I),
    re.compile(r"\bwhat surrounds you resolves into focus\b", re.I),
    re.compile(r"\byou widen the sweep\b", re.I),
    re.compile(r"\byou take another pass at the scene\b", re.I),
    re.compile(r"\bthe same impression returns\b", re.I),
    re.compile(r"\bthe moment stays crowded with detail\b", re.I),
)

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "as",
        "with",
        "by",
        "from",
        "into",
        "while",
        "you",
        "your",
        "yours",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "it",
        "its",
        "that",
        "this",
        "these",
        "those",
    }
)


def _inner_scene(scene_or_envelope: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene_or_envelope, Mapping):
        return {}
    raw = scene_or_envelope.get("scene")
    if isinstance(raw, dict):
        return raw
    return dict(scene_or_envelope)  # type: ignore[arg-type]


def _token_set(text: str) -> Set[str]:
    raw = re.findall(r"[a-z0-9']+", str(text or "").lower())
    return {w for w in raw if len(w) > 2 and w not in _STOPWORDS}


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter) / float(union) if union else 0.0


def _first_summary_sentence(scene: Mapping[str, Any] | None) -> str:
    if not isinstance(scene, Mapping):
        return ""
    summary = str(scene.get("summary") or "").strip()
    if not summary:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", summary)
    return parts[0].strip() if parts else ""


def _reference_intro_fragments(scene_envelope: Mapping[str, Any] | None) -> list[str]:
    inner = _inner_scene(scene_envelope)
    out: list[str] = []
    fs = _first_summary_sentence(inner)
    if fs:
        out.append(fs)
    vf = inner.get("visible_facts") if isinstance(inner.get("visible_facts"), list) else []
    for item in vf[:2]:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    jsf = inner.get("journal_seed_facts") if isinstance(inner.get("journal_seed_facts"), list) else []
    for item in jsf[:1]:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def text_overlaps_known_scene_intro_sources(text: str, scene_envelope: Mapping[str, Any] | None) -> bool:
    """High lexical overlap with scene summary / first visible facts (opening paragraph sources)."""
    cand = _token_set(text)
    if len(cand) < 6:
        return False
    for ref in _reference_intro_fragments(scene_envelope):
        rset = _token_set(ref)
        if _jaccard(cand, rset) >= 0.42:
            return True
    return False


def text_matches_observe_opener_templates(text: str) -> bool:
    """Templates from :func:`render_observe_perception_fallback_line` / global anchor."""
    s = str(text or "").strip()
    if not s:
        return False
    return any(p.search(s) for p in _OBSERVE_OPENER_HINTS)


def resolution_allows_scene_intro_framing(resolution: Dict[str, Any] | None, session: Dict[str, Any] | None) -> bool:
    """True when arrival, explicit scene opening, or campaign opening turn should keep intro-shaped lines."""
    if isinstance(resolution, dict):
        if resolution.get("resolved_transition") is True:
            return True
        sc = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
        if sc.get("scene_transition_occurred") is True or sc.get("arrived_at_scene") is True or sc.get("scene_changed") is True:
            return True
        if sc.get("opening_scene_turn") is True:
            return True
        kind = str(resolution.get("kind") or "").strip().lower()
        if kind in {"scene_transition", "travel", "scene_opening"}:
            return True
        aid = str(resolution.get("action_id") or "").strip().lower()
        if "opening_scene" in aid or "campaign_start" in aid:
            return True
    return False


def _opening_scene_preference_active(session: Dict[str, Any] | None) -> bool:
    """Mirrors :func:`game.final_emission_gate._opening_scene_preference_active` without importing the gate."""
    if not isinstance(session, dict):
        return False
    turn_counter = int(session.get("turn_counter", 0) or 0)
    visited_scene_ids = session.get("visited_scene_ids") if isinstance(session.get("visited_scene_ids"), list) else []
    return turn_counter <= 1 or (turn_counter == 0 and len(visited_scene_ids) <= 1)


def session_indicates_established_local_exchange(
    session: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    """Established scene + local/focused interaction or mid-scene continuation signals."""
    if not isinstance(session, dict):
        return False
    turn_counter = int(session.get("turn_counter", 0) or 0)
    ctx = inspect_interaction_context(session)
    mode = str(ctx.get("interaction_mode") or "").strip().lower()
    target = str(ctx.get("active_interaction_target_id") or "").strip()
    engagement = str(ctx.get("engagement_level") or "").strip().lower()

    social_engaged = mode == "social" and bool(target)
    focused = engagement == "focused" and mode in {"social", "activity"}

    mid_scene = turn_counter >= 2 or (turn_counter >= 1 and (social_engaged or focused))

    strict_social = False
    if isinstance(resolution, dict):
        soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        if str(soc.get("social_intent_class") or "").strip().lower() == "social_exchange" and str(
            soc.get("npc_id") or ""
        ).strip():
            strict_social = True

    if not mid_scene:
        return False
    return social_engaged or focused or strict_social


def anti_reset_suppresses_intro_style_fallbacks(
    session: Dict[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    """When True, opener/intro-shaped stock fallbacks must not be used as final player-facing text."""
    if not isinstance(session, dict):
        return False
    sid = str(scene_id or "").strip()
    if resolution_allows_scene_intro_framing(resolution, session):
        return False
    if _opening_scene_preference_active(session):
        return False
    if not session_indicates_established_local_exchange(session, sid, resolution):
        return False
    return True


def local_exchange_continuation_fallback_line(
    *,
    session: Dict[str, Any] | None,
    world: Mapping[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
) -> str:
    """Short, exchange-local beat — not global scene re-establishment."""
    if isinstance(resolution, dict) and isinstance(world, Mapping):
        eff, _, _ = effective_strict_social_resolution_for_emission(
            resolution,
            session if isinstance(session, dict) else None,
            world,
            str(scene_id or "").strip(),
        )
        if isinstance(eff, dict):
            line = minimal_social_emergency_fallback_line(eff)
            if str(line or "").strip():
                return str(line).strip()
    ctx = inspect_interaction_context(session if isinstance(session, dict) else {})
    if str(ctx.get("active_interaction_target_id") or "").strip():
        return "The exchange doesn't resolve cleanly—you hold your ground while the moment stays sharp between you."
    return "Nothing new locks in yet; you keep the scene's weight without stepping backward."


def should_replace_candidate_intro_fallback(
    text: str,
    *,
    scene_envelope: Mapping[str, Any] | None,
    emitter_source: str | None,
    suppress_intro: bool,
) -> bool:
    """True when this candidate should be swapped for a continuation-safe line."""
    if not suppress_intro:
        return False
    src = str(emitter_source or "").strip()
    if src in SCENE_INTRO_EMITTER_SOURCES:
        return True
    if text_matches_observe_opener_templates(text):
        return True
    if text_overlaps_known_scene_intro_sources(text, scene_envelope):
        return True
    return False
