"""Route-isolated emission helpers for active social_exchange turns.

Ensures player-facing text is speaker-owned, single-form, and never pulled from
scene/ambient uncertainty pools except as an explicit interruption breakoff.

Speaker identity for strict emission aligns with
:func:`game.interaction_context.resolve_authoritative_social_target`; do not resolve a competing
NPC id in this module except through that helper (or thin wrappers around it).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from game.prompt_context import canonical_interaction_target_npc_id

from game.interaction_context import (
    assert_valid_speaker,
    canonical_scene_addressable_roster,
    effective_in_scene_npc_roster,
    inspect as inspect_interaction_context,
    line_opens_with_comma_vocative,
    npc_id_from_explicit_generic_role_address,
    npc_id_from_vocative_line,
    resolve_authoritative_social_target,
    scene_addressable_actor_ids,
    session_allows_implicit_social_reply_authority,
)

# Historical name in this module; delegates to canonical roster resolution in interaction_context.
effective_scene_npc_roster = effective_in_scene_npc_roster
from game.storage import get_scene_runtime
from game.social import (
    apply_social_reply_speaker_grounding,
    classify_social_question_dimension,
    finalize_social_target_with_promotion,
    format_structured_fact_social_line,
    neutral_reply_speaker_grounding_bridge_line,
    resolve_grounded_social_speaker,
    select_best_social_answer_candidate,
    topic_pressure_speaker_id_for_social_exchange,
)
from game.exploration import EXPLORATION_KINDS
from game.social import SOCIAL_KINDS
from game.utils import slugify

_log = logging.getLogger(__name__)

_EXPLORATION_RESOLUTION_KINDS = frozenset(str(k).strip().lower() for k in EXPLORATION_KINDS)

_REFLECTIVE_OR_MOVEMENT_NARRATION_OPEN_RE = re.compile(
    r"^\s*(?:"
    r"i\s+(?:"
    r"think|consider|reflect|recall|remember|weigh|mull|ponder|digest|"
    r"take\s+a\s+moment|step\s+back|walk\s+away|move\s+off|head\s+away|turn\s+away|"
    r"glance\s+around|look\s+around|examine\s+the\s+room|study\s+the|"
    r"listen\s+to\s+the\s+(?:ambient|crowd|room)"
    r")"
    r"|we\s+(?:step|walk|move|head)\b"
    r"|looking\s+(?:around|about|over)\b"
    r"|after\s+(?:a\s+moment|stepping\s+away|walking\s+off)\b"
    r"|the\s+scene\s+(?:holds|settles|shifts)\b"
    r")",
    re.IGNORECASE,
)

_IMPERATIVE_SOCIAL_CONTINUATION_RE = re.compile(
    r"^\s*(?:[\w\s']+,\s*)?(?:tell|give|say|spill|explain|share|describe|go\s+on|continue|elaborate)\b",
    re.IGNORECASE,
)


def _session_turn_counter(session: Dict[str, Any] | None) -> int:
    if not isinstance(session, dict):
        return 0
    try:
        return int(session.get("turn_counter") or 0)
    except (TypeError, ValueError):
        return 0


def _auth_after_social_promotion_binding(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    auth: Dict[str, Any],
    scene_envelope: Dict[str, Any] | None,
    *,
    merged_player_prompt: str | None = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Align resolver output with promoted_actor_npc_map and auto-promotion policy (same as engine social)."""
    return finalize_social_target_with_promotion(
        session if isinstance(session, dict) else {},
        world if isinstance(world, dict) else {},
        str(scene_id or "").strip(),
        auth,
        action_type="",
        turn_counter=_session_turn_counter(session),
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
        raw_player_text=merged_player_prompt,
    )


def _scene_envelope_for_strict_social(session: Dict[str, Any] | None, scene_id: str) -> Dict[str, Any] | None:
    """Load persisted scene JSON and overlay live ``session.scene_state`` (active_entities scope)."""
    sid = str(scene_id or "").strip()
    if not sid:
        return None
    from game.storage import load_scene

    env = load_scene(sid)
    if not isinstance(env, dict):
        return None
    out = dict(env)
    if isinstance(session, dict):
        st = session.get("scene_state")
        if isinstance(st, dict):
            out["scene_state"] = st
    return out


def _legacy_strict_basis_from_authoritative(auth: Dict[str, Any], world: Dict[str, Any] | None, scene_id: str) -> str:
    """Map :func:`resolve_authoritative_social_target` ``source`` to historical ``basis`` strings."""
    src = str((auth or {}).get("source") or "").strip()
    if src == "generic_role":
        return "generic_address"
    if src == "spoken_vocative":
        return "vocative"
    if src == "continuity":
        sid = str(scene_id or "").strip()
        roster = effective_scene_npc_roster(world, sid)
        nid = str((auth or {}).get("npc_id") or "").strip()
        if nid and any(isinstance(n, dict) and str(n.get("id") or "").strip() == nid for n in roster):
            return "active"
        return "active_unlisted"
    if src == "none":
        return "none"
    return src


_UNCERTAINTY_TAG_PREFIX = "uncertainty:"
_MOMENTUM_TAG_PREFIX = "scene_momentum:"

_SCENE_CONTAMINATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bfor a breath,?\s+the scene\b", re.IGNORECASE),
    re.compile(r"\bthe scene holds\b", re.IGNORECASE),
    re.compile(r"\bscene stays still\b", re.IGNORECASE),
    re.compile(r"\bvoices shift around you\b", re.IGNORECASE),
    re.compile(r"\bnothing in the scene points\b", re.IGNORECASE),
    re.compile(r"\bnothing visible around\b", re.IGNORECASE),
    re.compile(r"\bnothing around\b.+\bconfirms\b", re.IGNORECASE),
    re.compile(r"\bno certain answer\b", re.IGNORECASE),
    re.compile(r"\bfrom here, no\b", re.IGNORECASE),
    re.compile(r"\bno clear answer\b", re.IGNORECASE),
    re.compile(r"\bthe scene suggests\b", re.IGNORECASE),
    re.compile(r"\bit can be inferred\b", re.IGNORECASE),
    re.compile(r"\bdoes not point to a clear answer\b", re.IGNORECASE),
    re.compile(r"\bnothing resolves into\b", re.IGNORECASE),
    re.compile(r"\baround you, small details sharpen into clues\b", re.IGNORECASE),
    re.compile(r"\btaken together, the marks\b", re.IGNORECASE),
    re.compile(r"\bscuffed mud, broken chalk\b", re.IGNORECASE),
    re.compile(r"\btwo details stand out\b", re.IGNORECASE),
)

_INTERRUPTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bshouting breaks out\b", re.IGNORECASE),
    re.compile(r"\bshout(?:ing)? breaks out\b", re.IGNORECASE),
    re.compile(r"\bshout erupts\b", re.IGNORECASE),
    re.compile(r"\bcommotion\b", re.IGNORECASE),
    re.compile(r"\balarm\b", re.IGNORECASE),
    re.compile(r"\bcrowd .*?(?:erupts|breaks|surges)\b", re.IGNORECASE),
    re.compile(r"\berupts in the crowd\b", re.IGNORECASE),
)

_EXPLICIT_INTERRUPTION_JOIN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bstarts to answer, then\b", re.IGNORECASE),
    re.compile(r"\bbegins to answer, then\b", re.IGNORECASE),
    re.compile(r"\bbreaks off\b", re.IGNORECASE),
    re.compile(r"\bcuts (?:himself|herself|themselves) off\b", re.IGNORECASE),
    re.compile(r"\bbefore .*?(?:can|could) .*?(?:answer|finish)\b", re.IGNORECASE),
    re.compile(r"\bas .*?(?:shouting|commotion|alarm) .*?(?:breaks out|erupts)\b", re.IGNORECASE),
)

_NPC_SETUP_HINTS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:says|said|replies|replied|answers|answered|mutters|whispers|asks)\b", re.IGNORECASE),
    re.compile(r"\bstarts to answer\b", re.IGNORECASE),
    re.compile(r"\bbegins to answer\b", re.IGNORECASE),
    re.compile(r"\"[^\"]{2,}\"", re.IGNORECASE),
)

_SENTENCE_TERMINATORS = ".!?"
_CLOSING_PUNCT_OR_QUOTES = "\"')]}»”’"


def is_social_exchange_resolution(resolution: Dict[str, Any] | None) -> bool:
    if not isinstance(resolution, dict):
        return False
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(social.get("social_intent_class") or "").strip().lower() == "social_exchange"


_SCENE_DIRECTED_WATCH_QUESTION_RE = re.compile(
    r"\bwho\s+should\s+i\s+watch\b.*\bhere\b|\bwho\s+should\s+i\s+watch\s+here\b",
    re.IGNORECASE | re.DOTALL,
)


def is_scene_directed_watch_question(player_text: str | None) -> bool:
    return bool(_SCENE_DIRECTED_WATCH_QUESTION_RE.search(str(player_text or "")))


# Question-shape hint for coercion when resolution.prompt is empty (GPT / unstitched paths).
_DIRECT_QUESTION_WORDS_FOR_EMIT = (
    "who",
    "what",
    "where",
    "when",
    "why",
    "how",
    "which",
    "should",
    "could",
    "would",
    "can",
    "did",
    "do",
    "does",
    "is",
    "are",
    "was",
    "were",
)


def _question_prompt_for_resolution_early(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    return str(
        resolution.get("prompt")
        or resolution.get("label")
        or ((resolution.get("metadata") or {}).get("player_input") if isinstance(resolution.get("metadata"), dict) else "")
        or ""
    ).strip()


def _scene_runtime_player_hint(session: Dict[str, Any] | None, scene_id: str) -> str:
    sid = str(scene_id or "").strip()
    if not sid or not isinstance(session, dict):
        return ""
    rt = get_scene_runtime(session, sid)
    return str(rt.get("last_player_action_text") or "").strip()


def _merge_prompt_for_strict_gate(
    resolution: Dict[str, Any] | None,
    scene_runtime_prompt: str | None,
) -> str:
    base = _question_prompt_for_resolution_early(resolution if isinstance(resolution, dict) else None)
    extra = str(scene_runtime_prompt or "").strip()
    if extra and not base:
        return extra
    if extra and base:
        # Do not always prepend raw scene-runtime text: it can carry a *previous* line
        # (e.g. travel) and poison substring resolution. Prepend ``extra`` only when it
        # opens with comma vocative syntax (this turn's raw line). If only ``base`` has
        # that form, keep vocative at the front with ``base`` first.
        if line_opens_with_comma_vocative(extra):
            return f"{extra} {base}".strip()
        if line_opens_with_comma_vocative(base):
            return f"{base} {extra}".strip()
        return f"{base} {extra}".strip()
    return base


def merged_player_prompt_for_gate(
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> str:
    """Merged player prompt + scene-runtime hint for strict-social / NPC-directed guards."""
    sid = str(scene_id or "").strip()
    hint = _scene_runtime_player_hint(session, sid) if sid else ""
    return _merge_prompt_for_strict_gate(resolution if isinstance(resolution, dict) else None, hint or None)


def resolve_strict_social_npc_target_id(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    merged_player_prompt: str,
    *,
    normalized_action: Dict[str, Any] | None = None,
    scene_envelope: Dict[str, Any] | None = None,
) -> Tuple[str, str]:
    """Pick the NPC for strict-social coercion: ``(npc_id, basis)``.

    Delegates to :func:`game.interaction_context.resolve_authoritative_social_target` with
    ``allow_first_roster_fallback=True``. ``basis`` preserves legacy strings used by tests
    (``generic_address`` for generic role, ``active`` / ``active_unlisted`` for continuity).
    """
    sid = str(scene_id or "").strip()
    prompt = str(merged_player_prompt or "").strip()
    env = scene_envelope if isinstance(scene_envelope, dict) else None
    if env is None and sid:
        env = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    auth = resolve_authoritative_social_target(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        player_text=prompt,
        normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
        scene_envelope=env,
        merged_player_prompt=prompt,
        allow_first_roster_fallback=True,
    )
    auth, _, _ = _auth_after_social_promotion_binding(
        session, world, sid, auth, env, merged_player_prompt=prompt
    )
    basis = _legacy_strict_basis_from_authoritative(auth, world if isinstance(world, dict) else None, sid)
    tid0 = str(auth.get("npc_id") or "").strip()
    if tid0 and auth.get("target_resolved") and not auth.get("offscene_target"):
        _soc_gate = {
            "npc_id": tid0,
            "target_resolved": True,
            "npc_name": str(auth.get("npc_name") or "").strip(),
        }
        apply_social_reply_speaker_grounding(
            _soc_gate,
            session if isinstance(session, dict) else {},
            world if isinstance(world, dict) else {},
            sid,
            env,
            auth,
        )
        tid0 = str(_soc_gate.get("npc_id") or "").strip()
    return tid0, basis


def is_conversational_npc_dialogue_line(text: str | None, session: Dict[str, Any] | None) -> bool:
    """True when the player is in an active social exchange with a valid in-scene interlocutor."""
    if not isinstance(session, dict) or not str(text or "").strip():
        return False
    low = str(text or "").strip().lower()
    # Skill maneuvers are resolved by the engine / check prompts, not strict NPC dialogue emission.
    if re.search(r"\b(persuade|intimidate|deceive|barter|recruit)\b", low):
        return False
    inspected = inspect_interaction_context(session)
    target = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    if not target or not assert_valid_speaker(target, session):
        return False
    kind = str((inspected or {}).get("active_interaction_kind") or "").strip().lower()
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    engagement = str((inspected or {}).get("engagement_level") or "").strip().lower()
    if not (kind == "social" or mode == "social"):
        return False
    return engagement in {"engaged", "active", "", "focused"}


def looks_like_npc_directed_question(text: str | None) -> bool:
    """True when the player line reasonably expects an NPC verbal answer (not pure staging)."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    if "?" in low:
        return True
    return bool(
        re.search(
            r"\b(" + "|".join(_DIRECT_QUESTION_WORDS_FOR_EMIT) + r")\b",
            low,
        )
    )


def player_line_triggers_strict_social_emission(
    text: str | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    """Single predicate for whether the player line is NPC-directed / in-scene social exchange."""
    if is_scene_directed_watch_question(text):
        return False
    # Question-shaped lines alone must not trigger strict-social after explicit non-social activity.
    if looks_like_npc_directed_question(text) and session_allows_implicit_social_reply_authority(
        session if isinstance(session, dict) else None
    ):
        return True
    sid = str(scene_id or "").strip()
    w = world if isinstance(world, dict) else {}
    roster = effective_scene_npc_roster(w, sid)
    env = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    addressable = canonical_scene_addressable_roster(
        w,
        sid,
        scene_envelope=env,
        session=session if isinstance(session, dict) else None,
    )
    p = str(text or "").strip()
    if roster and p and npc_id_from_vocative_line(p, roster):
        return True
    if addressable and p and npc_id_from_explicit_generic_role_address(p.lower(), addressable):
        return True
    if is_conversational_npc_dialogue_line(text, session):
        return True
    return False


def strict_social_emission_will_apply(
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    """True when apply_final_emission_gate will take the strict-social path (incl. npc_directed_guard)."""
    if isinstance(resolution, dict):
        soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        if soc.get("offscene_target"):
            return False
        kind = str(resolution.get("kind") or "").strip().lower()
        if kind in {"adjudication_query", "scene_opening"}:
            return False
        if resolution.get("adjudication") and not isinstance(resolution.get("social"), dict):
            return False
    _eff, social_route, _ = effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    return bool(social_route)


def minimal_social_resolution_for_directed_question_guard(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    merged_player_prompt: str,
    resolution: Dict[str, Any] | None = None,
) -> Optional[Dict[str, Any]]:
    """When strict coercion missed, still avoid global scene fallback on NPC-directed questions."""
    if isinstance(resolution, dict):
        soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        if soc.get("offscene_target"):
            return None
        kind = str(resolution.get("kind") or "").strip().lower()
        if kind in {"adjudication_query", "scene_opening"}:
            return None
        if resolution.get("adjudication") and not isinstance(resolution.get("social"), dict):
            return None
        rk = str(resolution.get("kind") or "").strip().lower()
        if rk in {"persuade", "intimidate", "deceive", "barter", "recruit"}:
            return None
        if resolution.get("requires_check"):
            return None
    prompt = str(merged_player_prompt or "").strip()
    sid = str(scene_id or "").strip()
    if not prompt or not player_line_triggers_strict_social_emission(prompt, session, world, sid):
        return None
    if is_scene_directed_watch_question(prompt):
        return None
    env = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    auth = resolve_authoritative_social_target(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        player_text=prompt,
        merged_player_prompt=prompt,
        scene_envelope=env,
        allow_first_roster_fallback=True,
    )
    auth, tb, tph = _auth_after_social_promotion_binding(
        session, world, sid, auth, env, merged_player_prompt=prompt
    )
    target = str(auth.get("npc_id") or "").strip()
    if not target or not auth.get("target_resolved") or auth.get("offscene_target"):
        return None
    npc_name = _npc_display_name_for_emission(world, sid, target)
    soc = {
        "social_intent_class": "social_exchange",
        "npc_id": target,
        "npc_name": npc_name,
        "npc_reply_expected": True,
        "reply_kind": "answer",
        "target_resolved": True,
        "target_source": auth.get("source"),
        "target_reason": auth.get("reason"),
        "target_candidate_id": None,
        "target_candidate_valid": False,
    }
    if tb:
        soc["target_binding"] = dict(tb)
    if tph:
        soc["target_profile_hints"] = dict(tph)
    grb = auth.get("generic_role_rebind")
    if isinstance(grb, dict):
        soc["generic_role_rebind"] = grb
    apply_social_reply_speaker_grounding(
        soc,
        session if isinstance(session, dict) else {},
        world if isinstance(world, dict) else {},
        sid,
        env,
        auth,
        proposed_reply_speaker_id=str(target or "").strip() or None,
    )
    return {
        "kind": "question",
        "prompt": prompt,
        "label": prompt[:140],
        "social": soc,
    }


def _active_social_target_matches_npc(session: Dict[str, Any] | None, npc_id: str | None) -> bool:
    nid = str(npc_id or "").strip()
    if not nid or not isinstance(session, dict):
        return False
    inspected = inspect_interaction_context(session)
    active = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    if active != nid:
        return False
    kind = str((inspected or {}).get("active_interaction_kind") or "").strip().lower()
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    engagement = str((inspected or {}).get("engagement_level") or "").strip().lower()
    if not ((kind == "social" or mode == "social") and engagement in {"engaged", "active", ""}):
        return False
    return assert_valid_speaker(nid, session)


def should_apply_strict_social_exchange_emission(
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    *,
    scene_runtime_prompt: str | None = None,
    scene_id: str | None = None,
    world: Dict[str, Any] | None = None,
) -> bool:
    """True only for NPC-directed social_exchange turns (exempt scene-wide watch/scan questions)."""
    if not is_social_exchange_resolution(resolution):
        return False
    if not isinstance(resolution, dict):
        return False
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    prompt = _merge_prompt_for_strict_gate(resolution, scene_runtime_prompt)
    sid = str(scene_id or "").strip()
    if not sid and isinstance(session, dict):
        st = session.get("scene_state")
        if isinstance(st, dict):
            sid = str(st.get("active_scene_id") or "").strip()
        if not sid:
            sid = str(session.get("active_scene_id") or "").strip()
    if is_scene_directed_watch_question(prompt):
        return False
    if social.get("npc_reply_expected") is False:
        npc_id = str(social.get("npc_id") or "").strip()
        if not (
            _active_social_target_matches_npc(session, npc_id)
            and player_line_triggers_strict_social_emission(prompt, session, world, sid)
        ):
            return False
    return True


def _npc_display_name_for_emission(world: Dict[str, Any] | None, scene_id: str, npc_id: str) -> str:
    """Resolve a short speaker label; prefers persisted world NPC row (stable across turns)."""
    from game.defaults import default_world
    from game.social import find_npc_by_target
    from game.world import get_world_npc_by_id

    sid = str(scene_id or "").strip()
    nid = str(npc_id or "").strip()
    if not nid:
        return "The guard"
    w = world if isinstance(world, dict) else {}
    row = get_world_npc_by_id(w, nid)
    if isinstance(row, dict):
        nm = str(row.get("name") or "").strip()
        if nm:
            return nm
    npc = find_npc_by_target(w, nid, sid) if w is not None else None
    if npc is None:
        npc = find_npc_by_target(default_world(), nid, sid)
    name = str((npc or {}).get("name") or "").strip()
    if name:
        return name
    return nid.replace("_", " ").replace("-", " ").title()


def synthetic_social_exchange_resolution_for_emission(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    prompt_text: str,
) -> Optional[Dict[str, Any]]:
    """Build minimal resolution so strict social emission can run when engine resolution was not threaded."""
    if not isinstance(session, dict):
        return None
    sid = str(scene_id or "").strip()
    prompt = str(prompt_text or "").strip()
    if not prompt or not player_line_triggers_strict_social_emission(prompt, session, world, sid):
        return None
    if is_scene_directed_watch_question(prompt):
        return None
    env = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    auth = resolve_authoritative_social_target(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        player_text=prompt,
        merged_player_prompt=prompt,
        scene_envelope=env,
        allow_first_roster_fallback=True,
    )
    auth, tb2, tph2 = _auth_after_social_promotion_binding(
        session, world, sid, auth, env, merged_player_prompt=prompt
    )
    target = str(auth.get("npc_id") or "").strip()
    if not target or not auth.get("target_resolved") or auth.get("offscene_target"):
        return None
    src_syn = str(auth.get("source") or "").strip()
    if src_syn in ("continuity", "first_roster") and not session_allows_implicit_social_reply_authority(session):
        return None
    if src_syn == "continuity":
        inspected = inspect_interaction_context(session)
        kind = str((inspected or {}).get("active_interaction_kind") or "").strip().lower()
        mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
        engagement = str((inspected or {}).get("engagement_level") or "").strip().lower()
        if not ((kind == "social" or mode == "social") and engagement in {"engaged", "active", ""}):
            return None
    npc_name = _npc_display_name_for_emission(world, sid, target)
    soc2 = {
        "social_intent_class": "social_exchange",
        "npc_id": target,
        "npc_name": npc_name,
        "npc_reply_expected": True,
        "reply_kind": "answer",
        "target_resolved": True,
        "target_source": auth.get("source"),
        "target_reason": auth.get("reason"),
        "target_candidate_id": None,
        "target_candidate_valid": False,
    }
    if tb2:
        soc2["target_binding"] = dict(tb2)
    if tph2:
        soc2["target_profile_hints"] = dict(tph2)
    grb2 = auth.get("generic_role_rebind")
    if isinstance(grb2, dict):
        soc2["generic_role_rebind"] = grb2
    apply_social_reply_speaker_grounding(
        soc2,
        session if isinstance(session, dict) else {},
        world if isinstance(world, dict) else {},
        sid,
        env,
        auth,
        proposed_reply_speaker_id=str(target or "").strip() or None,
    )
    return {
        "kind": "question",
        "prompt": prompt,
        "label": prompt[:140],
        "social": soc2,
    }


def coerce_resolution_for_strict_social_emission(
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    """Pick the resolution dict used for strict social gate logic; returns (effective, strict_on, trace_reason)."""
    if isinstance(resolution, dict):
        soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        if soc.get("offscene_target"):
            return resolution, False, "offscene_target_engine_response"

    sid = str(scene_id or "").strip()
    w = world if isinstance(world, dict) else None
    if not isinstance(session, dict) or not sid:
        active = bool(
            resolution
            and isinstance(resolution, dict)
            and should_apply_strict_social_exchange_emission(
                resolution, session, scene_id=sid or None, world=w
            )
        )
        return resolution if isinstance(resolution, dict) else None, active, "no_session_or_scene"

    hint = _scene_runtime_player_hint(session, sid)
    merged_for_syn = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session,
        sid,
    )

    if isinstance(resolution, dict) and should_apply_strict_social_exchange_emission(
        resolution,
        session,
        scene_runtime_prompt=hint or None,
        scene_id=sid,
        world=w,
    ):
        return resolution, True, "native_resolution"

    syn = synthetic_social_exchange_resolution_for_emission(
        session, world, sid, prompt_text=merged_for_syn or hint
    )
    if syn and should_apply_strict_social_exchange_emission(syn, session, scene_id=sid, world=w):
        return syn, True, "synthetic_active_interlocutor_question"

    return resolution if isinstance(resolution, dict) else None, False, "strict_social_inactive"


def reconcile_strict_social_resolution_speaker(
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """Align ``resolution.social`` NPC fields with :func:`resolve_authoritative_social_target` (merged prompt).

    Prevents deterministic fallbacks from using a stale engine ``npc_id`` or ``first_roster`` ambient NPC
    when vocative / active interlocutor / substring addressing resolves a different target.
    """
    # Authoritative social target selection happens here. After this point, emission/validation may reject
    # output text, but may not null the selected target unless it is invalidated by scene scope.
    sid = str(scene_id or "").strip()
    if not isinstance(resolution, dict) or not sid:
        return resolution
    merged = merged_player_prompt_for_gate(resolution, session, sid)
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    na = meta.get("normalized_action") if isinstance(meta.get("normalized_action"), dict) else None
    env = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    auth = resolve_authoritative_social_target(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        player_text=merged,
        normalized_action=na,
        merged_player_prompt=merged,
        scene_envelope=env,
        allow_first_roster_fallback=True,
    )
    auth, tb3, tph3 = _auth_after_social_promotion_binding(
        session, world, sid, auth, env, merged_player_prompt=merged
    )
    target_id = str(auth.get("npc_id") or "").strip()
    target_id = canonical_interaction_target_npc_id(session if isinstance(session, dict) else None, target_id)
    if not target_id or not auth.get("target_resolved") or auth.get("offscene_target"):
        return resolution
    out = dict(resolution)
    soc = dict(resolution.get("social") or {}) if isinstance(resolution.get("social"), dict) else {}
    soc["npc_id"] = target_id
    soc["npc_name"] = _npc_display_name_for_emission(world, sid, target_id)
    soc["target_resolved"] = bool(auth.get("target_resolved"))
    soc["offscene_target"] = bool(auth.get("offscene_target"))
    soc["target_source"] = auth.get("source")
    soc["target_reason"] = auth.get("reason")
    cand_raw = (na or {}).get("target_id") or (na or {}).get("targetEntityId")
    cand = str(cand_raw).strip() if cand_raw is not None and str(cand_raw).strip() else None
    addr = scene_addressable_actor_ids(
        world if isinstance(world, dict) else None,
        sid,
        scene_envelope=env,
        session=session if isinstance(session, dict) else None,
    )
    soc["target_candidate_id"] = cand
    soc["target_candidate_valid"] = bool(cand and cand in addr)
    if not str(soc.get("social_intent_class") or "").strip():
        soc["social_intent_class"] = "social_exchange"
    if tb3:
        soc["target_binding"] = dict(tb3)
    if tph3:
        soc["target_profile_hints"] = dict(tph3)
    grb = auth.get("generic_role_rebind")
    if isinstance(grb, dict):
        soc["generic_role_rebind"] = grb
    apply_social_reply_speaker_grounding(
        soc,
        session if isinstance(session, dict) else {},
        world if isinstance(world, dict) else {},
        sid,
        env,
        auth,
        proposed_reply_speaker_id=str(target_id or "").strip() or None,
    )
    out["social"] = soc
    return out


def effective_strict_social_resolution_for_emission(
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    """Effective resolution and strict-social route — matches :func:`apply_final_emission_gate`.

    Coercion plus ``npc_directed_guard`` must stay aligned anywhere upstream emitters
    branch on “strict social” so deterministic fallbacks cannot inject narrator/uncertainty
    blobs while the gate still routes to :func:`build_final_strict_social_response`.
    """
    eff_resolution, social_route, coercion_reason = coerce_resolution_for_strict_social_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    merged_prompt = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        str(scene_id or "").strip(),
    )
    if not social_route:
        guard_res = minimal_social_resolution_for_directed_question_guard(
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            str(scene_id or "").strip(),
            merged_player_prompt=merged_prompt,
            resolution=resolution if isinstance(resolution, dict) else None,
        )
        if isinstance(guard_res, dict):
            eff_resolution = guard_res
            social_route = True
            coercion_reason = f"{coercion_reason}|npc_directed_guard"
    if social_route and isinstance(eff_resolution, dict):
        eff_resolution = reconcile_strict_social_resolution_speaker(
            eff_resolution,
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            str(scene_id or "").strip(),
        )
    preview = merged_prompt[:120] + ("…" if len(merged_prompt) > 120 else "")
    _log.debug(
        "strict_social_route social_route=%s coercion_reason=%s merged_prompt_preview=%r",
        social_route,
        coercion_reason,
        preview,
    )
    return eff_resolution if isinstance(eff_resolution, dict) else None, social_route, coercion_reason


def _normalized_action_from_resolution(resolution: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(resolution, dict):
        return None
    meta = resolution.get("metadata")
    if isinstance(meta, dict):
        na = meta.get("normalized_action")
        if isinstance(na, dict):
            return na
    return None


def _merged_prompt_opens_reflective_or_world_action_beat(merged_player_prompt: str) -> bool:
    p = str(merged_player_prompt or "").strip()
    return bool(p and _REFLECTIVE_OR_MOVEMENT_NARRATION_OPEN_RE.match(p))


def coerced_strict_social_allowed_by_merged_prompt(
    merged_player_prompt: str,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    """Narrow allow-list for synthetic / npc_directed_guard strict-social (not continuity-only)."""
    merged = str(merged_player_prompt or "").strip()
    if not merged:
        return False
    if "?" in merged:
        return True
    if _merged_prompt_opens_reflective_or_world_action_beat(merged):
        return False
    if _IMPERATIVE_SOCIAL_CONTINUATION_RE.search(merged):
        return True
    if looks_like_npc_directed_question(merged):
        return True
    sid = str(scene_id or "").strip()
    w = world if isinstance(world, dict) else {}
    roster = effective_scene_npc_roster(w, sid)
    env = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    addressable = canonical_scene_addressable_roster(
        w,
        sid,
        scene_envelope=env,
        session=session if isinstance(session, dict) else None,
    )
    if roster and npc_id_from_vocative_line(merged, roster):
        return True
    if addressable and npc_id_from_explicit_generic_role_address(merged.lower(), addressable):
        return True
    return False


def strict_social_suppress_non_native_coercion_for_narration_beat(
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    coercion_reason: str,
    merged_player_prompt: str,
) -> tuple[bool, str]:
    """If True, final emission must not use strict-social / NPC-owned writers for this turn.

    Preserves ``native_resolution`` strict-social. Targets synthetic continuity and npc_directed_guard
    when the turn is exploration, reflective framing, or lacks surface NPC-directed form.
    """
    cr = str(coercion_reason or "").strip()
    if cr == "native_resolution":
        return False, ""
    if not cr or "offscene_target" in cr:
        return False, ""

    merged = str(merged_player_prompt or "").strip()
    sid = str(scene_id or "").strip()

    if isinstance(resolution, dict):
        rk = str(resolution.get("kind") or "").strip().lower()
        if rk in _EXPLORATION_RESOLUTION_KINDS:
            return True, "exploration_resolution_kind"
        if rk and rk not in SOCIAL_KINDS and rk not in {"adjudication_query", "scene_opening"}:
            return True, "non_social_engine_resolution_kind"

    na = _normalized_action_from_resolution(resolution if isinstance(resolution, dict) else None)
    if isinstance(na, dict):
        nt = str(na.get("type") or "").strip().lower()
        if nt and nt not in SOCIAL_KINDS:
            return True, "non_social_normalized_action_type"

    if merged and "?" not in merged and _merged_prompt_opens_reflective_or_world_action_beat(merged):
        return True, "reflective_or_world_action_prompt"

    if coerced_strict_social_allowed_by_merged_prompt(merged, session, world, sid):
        return False, ""

    return True, "continuity_only_no_npc_directed_surface_form"


def log_final_emission_decision(payload: Dict[str, Any]) -> None:
    """Structured, concise server log line for final handoff debugging."""
    try:
        _log.info("final_emission %s", json.dumps(payload, default=str, ensure_ascii=False))
    except (TypeError, ValueError):
        _log.info("final_emission %s", str(payload))


def minimal_social_emergency_fallback_line(resolution: Dict[str, Any] | None) -> str:
    """Terminal-safe; deterministic variety; must pass as route-legal social without revalidation loops."""
    social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    speaker = _speaker_label(resolution)
    seed = f"{npc_id}|{speaker}"
    idx = _deterministic_index(seed, 3)
    lines = (
        f'{speaker} shakes their head. "I don\'t know."',
        f'{speaker} frowns. "That\'s all I\'ve got."',
        f"{speaker} starts to answer, then glances past you as shouting breaks out in the crowd.",
    )
    return lines[idx]


def strict_social_ownership_terminal_fallback(resolution: Dict[str, Any] | None) -> str:
    """Hard legal minimum for strict-social ownership: NPC refusal/ignorance lines only.

    Deterministic; intended to bypass further validation loops when no SOCIAL sentences remain.
    """
    social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    speaker = _speaker_label(resolution)
    seed = f"ownership_terminal|{npc_id}|{speaker}"
    idx = _deterministic_index(seed, 3)
    lines = (
        f'{speaker} shakes their head. "I don\'t know."',
        f'{speaker} lowers their voice. "I heard talk, not names."',
        f'{speaker} grimaces. "Hard to say—people whisper, nobody swears."',
    )
    return lines[idx]


def is_route_illegal_global_or_sanitizer_fallback_text(text: str | None) -> bool:
    """True when text matches global scene / empty-sanitizer / procedural sludge families (strict-social guard)."""
    t = _collapse_ws(str(text or ""))
    if not t:
        return True
    low = t.lower()
    if any(p.search(t) for p in _SCENE_CONTAMINATION_PATTERNS):
        return True
    banned = (
        "for a breath",
        "the scene holds",
        "voices shift around you",
        "nothing around the faces",
        "the answer has not formed yet",
        "from here, no certain answer",
        "nothing in the scene points",
        "for a breath, the scene stays still",
    )
    if any(b in low for b in banned):
        return True
    if re.search(r"\b(?:pin down|shadow tavern runner|you should|i'd suggest)\b", low):
        return True
    return False


def log_final_emission_trace(payload: Dict[str, Any]) -> None:
    """Structured terminal record for the last writer before user-visible return."""
    try:
        _log.info("final_emission_trace %s", json.dumps(payload, default=str, ensure_ascii=False))
    except (TypeError, ValueError):
        _log.info("final_emission_trace %s", str(payload))


def replacement_is_route_legal_social(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str = "",
    world: Dict[str, Any] | None = None,
) -> bool:
    """True if text is acceptable final social_exchange output (or intentional interruption path)."""
    return not hard_reject_social_exchange_text(
        text,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=str(scene_id or "").strip(),
        world=world if isinstance(world, dict) else None,
    )


def _collapse_ws(text: str) -> str:
    return " ".join(str(text or "").strip().split())


def _split_sentences(text: str) -> List[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    src = text.replace("\r\n", "\n").replace("\r", "\n")
    sentences: List[str] = []
    buff: List[str] = []
    i = 0
    n = len(src)
    while i < n:
        ch = src[i]
        if ch == "\n":
            if i + 1 < n and src[i + 1] == "\n":
                flushed = _collapse_ws("".join(buff))
                if flushed:
                    sentences.append(flushed)
                buff = []
                while i + 1 < n and src[i + 1] == "\n":
                    i += 1
                i += 1
                continue
            buff.append(" ")
            i += 1
            continue
        buff.append(ch)
        if ch in _SENTENCE_TERMINATORS:
            j = i + 1
            while j < n and src[j] in _CLOSING_PUNCT_OR_QUOTES:
                buff.append(src[j])
                j += 1
            flushed = _collapse_ws("".join(buff))
            if flushed:
                sentences.append(flushed)
            buff = []
            while j < n and src[j].isspace():
                j += 1
            i = j
            continue
        i += 1
    tail = _collapse_ws("".join(buff))
    if tail:
        sentences.append(tail)
    return sentences


def _sentence_is_scene_contaminated(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return True
    low = s.lower()
    if any(p.search(s) for p in _SCENE_CONTAMINATION_PATTERNS):
        return True
    if low.startswith("you notice ") or low.startswith("you can trace"):
        return True
    return False


def _sentence_is_npc_setup(sentence: str) -> bool:
    s = (sentence or "").strip()
    return any(p.search(s) for p in _NPC_SETUP_HINTS)


def _has_explicit_interruption_shape(text: str) -> bool:
    return any(p.search(text) for p in _EXPLICIT_INTERRUPTION_JOIN_PATTERNS)


def _interruption_sentence_index(sentences: List[str]) -> int | None:
    for i, s in enumerate(sentences):
        if any(p.search(s) for p in _INTERRUPTION_PATTERNS):
            return i
        if _has_explicit_interruption_shape(s):
            return i
    return None


# Detached omniscient / analyst prose (not speaker-bounded) — invalid as strict-social NPC lines.
_DETACHED_OMNISCIENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthe plan behind\b", re.IGNORECASE),
    re.compile(r"\bis likely to\b", re.IGNORECASE),
    re.compile(r"\bthe likely motive\b", re.IGNORECASE),
    re.compile(r"\bthis would benefit\b", re.IGNORECASE),
    re.compile(r"\bwould benefit them\b", re.IGNORECASE),
    re.compile(r"\bdisrupt(?:ting)?\s+local\s+order\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+a\s+tactical\b", re.IGNORECASE),
)

# Clue / analytical fragments that must not substitute for an NPC verbal answer.
_CLUE_OR_ANALYTICAL_SUBSTITUTE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:two\s+details|scuffed\s+mud|broken\s+chalk|wet\s+footprints)\b", re.IGNORECASE),
    re.compile(r"\baround\s+you,\s+small\s+details\b", re.IGNORECASE),
    re.compile(r"\btaken\s+together,\s+the\s+marks\b", re.IGNORECASE),
    re.compile(r"\bonly\s+fragments\s+of\b", re.IGNORECASE),
    re.compile(r"\bthe\s+notice\s+board\s+is\b", re.IGNORECASE),
)

_REFUSAL_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bnot\s+nam(?:ing|e)\b", re.IGNORECASE),
    re.compile(r"\bwon'?t\s+say\b", re.IGNORECASE),
    re.compile(r"\bI\s+won'?t\s+name\b", re.IGNORECASE),
    re.compile(r"\bno\s+names\s+here\b", re.IGNORECASE),
)

_IGNORANCE_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bdon'?t\s+know\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\s+know\b", re.IGNORECASE),
    re.compile(r"\bcan'?t\s+swear\b", re.IGNORECASE),
    re.compile(r"\bnot\s+the\s+names\b", re.IGNORECASE),
    re.compile(r"\bheard\s+the\s+talk\b", re.IGNORECASE),
    re.compile(r"\bno\s+one\s+here\s+can\s+swear\b", re.IGNORECASE),
)

_PRESSURE_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\btighten(?:s|ed)?\s+(?:their|his|her)\s+jaw\b", re.IGNORECASE),
    re.compile(r"\bI'?ve\s+told\s+you\s+what\s+I\s+know\b", re.IGNORECASE),
    re.compile(r"\bthat'?s\s+all\s+you'?re\s+getting\b", re.IGNORECASE),
    re.compile(r"\bpress\s+me\s+on\s+this\b", re.IGNORECASE),
    re.compile(r"\bconversation\s+is\s+over\b", re.IGNORECASE),
    re.compile(r"\bstop\s+grind(?:ing)?\s+the\s+same\s+point\b", re.IGNORECASE),
)

# Priority when multiple social forms compete (higher index = wins in tie-break).
_FORM_ORDER: tuple[str, ...] = (
    "interruption_breakoff",
    "pressure_escalation",
    "refusal_evasion",
    "direct_answer",
    "bounded_ignorance",
)


def _sentence_has_speaker_speculation_frame(sentence: str) -> bool:
    """True when speculation is clearly NPC/speaker-bound (not narrator omniscience)."""
    t = (sentence or "").strip()
    if not t:
        return False
    low = t.lower()
    if '"' in t:
        return True
    if any(p.search(t) for p in _NPC_SETUP_HINTS):
        return True
    if re.search(r"\bif i (?:had|have) to guess\b", low):
        return True
    if re.search(r"\b(?:i'?d guess|my guess is)\b", low):
        return True
    if re.search(
        r"\b(?:they|he|she|the\s+(?:guard|runner|merchant|man|woman|captain|soldier|clerk|tender|bartender|sergeant|lieutenant))\s+"
        r"(?:grimaces?|shrugs?|mutters?|lowers?\s+(?:their|his|her)\s+voice|leans?\s+in)\b",
        low,
    ):
        return True
    return False


def _sentence_is_detached_omniscient_analysis(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return True
    if _sentence_has_speaker_speculation_frame(s):
        return False
    return any(p.search(s) for p in _DETACHED_OMNISCIENT_PATTERNS)


def _sentence_is_bounded_social_signal(sentence: str) -> bool:
    """Short ignorance / refusal / pressure lines without explicit dialogue tags."""
    s = (sentence or "").strip()
    if not s:
        return False
    return bool(
        any(p.search(s) for p in _IGNORANCE_SIGNAL_PATTERNS)
        or any(p.search(s) for p in _REFUSAL_SIGNAL_PATTERNS)
        or any(p.search(s) for p in _PRESSURE_SIGNAL_PATTERNS)
    )


def _sentence_is_clue_or_analytical_substitute(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return True
    if _sentence_is_scene_contaminated(sentence):
        return True
    if _sentence_is_detached_omniscient_analysis(sentence):
        return True
    if any(p.search(s) for p in _CLUE_OR_ANALYTICAL_SUBSTITUTE_PATTERNS):
        return True
    return False


def _speaker_display_prefixes(resolution: Dict[str, Any] | None) -> List[str]:
    """npc_name and title-cased npc_id — used to treat '<Name> frowns.' as speaker-owned."""
    if not isinstance(resolution, dict):
        return []
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    out: List[str] = []
    if name:
        out.append(name)
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        tid = npc_id.replace("_", " ").replace("-", " ").title()
        if tid and tid not in out:
            out.append(tid)
    return out


def _sentence_opens_with_resolved_npc_beat(sentence: str, resolution: Dict[str, Any] | None) -> bool:
    """Multi-word display names (e.g. 'Tavern Runner frowns.') must count as speaker-owned."""
    s = (sentence or "").strip()
    if not s or not isinstance(resolution, dict):
        return False
    low = s.lower()
    for pref in _speaker_display_prefixes(resolution):
        p = pref.strip()
        if len(p) < 2:
            continue
        if not low.startswith(p.lower()):
            continue
        tail = s[len(p) :].lstrip(" \t,")
        if re.match(
            r"^(?:frowns|grimaces|shrugs|nods|gestures|leans|mutters|spreads|opens|starts|shakes|lowers|raises)\b",
            tail,
            re.IGNORECASE,
        ):
            return True
    return False


def _sentence_is_speaker_owned_social(sentence: str, resolution: Dict[str, Any] | None = None) -> bool:
    """True when the line is plausibly NPC/speaker social (not pure narrator atmosphere)."""
    t = (sentence or "").strip()
    if not t:
        return False
    low = t.lower()
    if resolution is not None and _sentence_opens_with_resolved_npc_beat(t, resolution):
        return True
    if any(p.search(t) for p in _INTERRUPTION_PATTERNS) or _has_explicit_interruption_shape(t):
        return True
    if _sentence_is_bounded_social_signal(t):
        return True
    if '"' in t:
        return True
    if any(p.search(t) for p in _NPC_SETUP_HINTS):
        return True
    if re.search(
        r"\b(?:they|he|she|the\s+\w+)\s+"
        r"(?:says|replies|asks|mutters|whispers|answers|shakes|shrugs|grimaces|frowns|tightens|glances|opens|starts|breaks|steps|cuts|spreads|lowers|nods|points|avoids)\b",
        low,
    ):
        return True
    if re.search(
        r"\b(?:they|he|she|the\s+(?:guard|runner|merchant|man|woman|captain|soldier|clerk|tender|bartender|sergeant|lieutenant))\s+"
        r"(?:points|gestures|nods|waves|looks?|turns|leans|faces|taps|shrugs?|grimaces?|frowns?)\b",
        low,
    ):
        return True
    return False


def _sentence_form_label(sentence: str) -> str:
    """Single-form label for one sentence (after scene/clue drops)."""
    s = (sentence or "").strip()
    low = s.lower()
    if any(p.search(s) for p in _INTERRUPTION_PATTERNS) or _has_explicit_interruption_shape(s):
        return "interruption_breakoff"
    if any(p.search(s) for p in _PRESSURE_SIGNAL_PATTERNS):
        return "pressure_escalation"
    if any(p.search(s) for p in _REFUSAL_SIGNAL_PATTERNS):
        return "refusal_evasion"
    if any(p.search(s) for p in _IGNORANCE_SIGNAL_PATTERNS):
        return "bounded_ignorance"
    if '"' in s or re.search(r"\b(?:says|replies|asks|answers|mutters|whispers)\b", low):
        return "direct_answer"
    return "direct_answer"


def _is_flat_idk_without_qualifier(sentence: str) -> bool:
    """Flat 'I don't know' / 'no idea' with no in-sentence who/what/which follow-up."""
    low = str(sentence or "").lower()
    m = re.search(r"\b(?:i\s+don'?t\s+know|i\s+do\s+not\s+know|no\s+idea)\b", low)
    if not m:
        return False
    tail = low[m.end() : m.end() + 100]
    if re.search(r"\b(?:who|what|which|whether)\b", tail):
        return False
    return True


def _contradictory_flat_ignorance_and_concrete_lead(sentences: List[str], labels: List[str]) -> bool:
    """True when one line gives a concrete lead and another is flat ignorance (terminal-fallback case)."""
    if len(sentences) != len(labels) or len(sentences) < 2:
        return False
    concrete_pat = re.compile(
        r'(?:\b(?:east|west|north|south)(?:\s+road|\s+lane)?\b|"[^"]{0,120}(?:east|west|road|lane|mill|gate))',
        re.IGNORECASE,
    )
    has_concrete = any(
        lb == "direct_answer" and concrete_pat.search(sentences[i] or "")
        for i, lb in enumerate(labels)
    )
    has_flat = any(
        lb == "bounded_ignorance" and _is_flat_idk_without_qualifier(sentences[i] or "")
        for i, lb in enumerate(labels)
    )
    return bool(has_concrete and has_flat)


def _dominant_form_from_labels(labels: List[str], *, pressure_tag: bool) -> str | None:
    uniq = {lb for lb in labels if lb}
    if not uniq:
        return None
    if len(uniq) == 1:
        return next(iter(uniq))
    if "interruption_breakoff" in uniq:
        return "interruption_breakoff"
    if pressure_tag and ("pressure_escalation" in uniq or "refusal_evasion" in uniq):
        return "pressure_escalation" if "pressure_escalation" in uniq else "refusal_evasion"
    # Conflicting substantive social claims: refuse to synthesize.
    if "bounded_ignorance" in uniq and "direct_answer" in uniq:
        return "mixed_ignorance_and_direct"
    if "refusal_evasion" in uniq and "direct_answer" in uniq:
        return "refusal_evasion"
    if "pressure_escalation" in uniq and "direct_answer" in uniq:
        return "pressure_escalation"
    if "bounded_ignorance" in uniq and "refusal_evasion" in uniq:
        return "refusal_evasion"
    # Pick highest-priority remaining form.
    best = None
    best_rank = -1
    for lb in uniq:
        try:
            r = _FORM_ORDER.index(lb)
        except ValueError:
            r = 0
        if r >= best_rank:
            best_rank = r
            best = lb
    return best


def _strip_ascii_double_quotes_for_scan(sentence: str) -> str:
    """Replace double-quoted spans so advisory heuristics do not match NPC dialogue."""
    return re.sub(r'"[^"]*"', " ", str(sentence or ""))


def _strict_social_advisory_outside_quotes(sentence: str) -> bool:
    """Advisory / player-directive phrasing outside quoted speech — invalid in strict social."""
    outside = _strip_ascii_double_quotes_for_scan(sentence)
    low = outside.lower()
    patterns = (
        r"\byou\s+should\b",
        r"\byou\s+might\s+want\s+to\b",
        r"\bit\s+might\s+be\s+worth\b",
        r"\bit\s+would\s+be\s+wise\b",
        r"\bconsider\s+(?:asking|looking|investigating)\b",
        r"\bi['']d\s+suggest\b",
        r"\bperhaps\s+you\s+should\b",
        r"\bit\s+might\s+help\s+to\b",
    )
    return any(re.search(p, low) for p in patterns)


def _strict_social_sentence_is_invalid(sentence: str, resolution: Dict[str, Any] | None) -> bool:
    """INVALID: narrator uncertainty, scene placeholders, analysis, clue narration, advisory."""
    s = (sentence or "").strip()
    if not s:
        return True
    if _sentence_is_scene_contaminated(s):
        return True
    if _sentence_is_clue_or_analytical_substitute(s):
        return True
    if _sentence_is_detached_omniscient_analysis(s):
        return True
    if _strict_social_advisory_outside_quotes(s):
        return True
    return False


def _classify_strict_social_ownership_sentence(
    sentence: str,
    resolution: Dict[str, Any] | None,
) -> str:
    """Return 'interruption', 'social', or 'invalid' for strict-social final emission."""
    s = (sentence or "").strip()
    if not s:
        return "invalid"
    if any(p.search(s) for p in _INTERRUPTION_PATTERNS) or _has_explicit_interruption_shape(s):
        return "interruption"
    if _strict_social_sentence_is_invalid(s, resolution):
        return "invalid"
    if _sentence_is_speaker_owned_social(s, resolution):
        return "social"
    return "invalid"


def _merge_interruption_chunk(sentences: List[str]) -> str | None:
    intr_idx = _interruption_sentence_index(sentences)
    if intr_idx is None:
        return None
    start = intr_idx
    cur = sentences[intr_idx]
    if intr_idx > 0 and any(p.search(cur) for p in _INTERRUPTION_PATTERNS) and not _has_explicit_interruption_shape(cur):
        if _sentence_is_npc_setup(sentences[intr_idx - 1]):
            start = intr_idx - 1
    chunk = sentences[start : intr_idx + 1]
    merged = _collapse_ws(" ".join(chunk))
    if _sentence_is_scene_contaminated(merged) or _sentence_is_clue_or_analytical_substitute(merged):
        solo = sentences[intr_idx].strip()
        if solo and not _sentence_is_scene_contaminated(solo):
            return _collapse_ws(solo)
        return None
    return merged


def apply_strict_social_sentence_ownership_filter(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
) -> str:
    """Final strict-social emission: only NPC-owned (SOCIAL) sentences or one INTERRUPTION breakoff.

    Classifies each sentence as SOCIAL | INTERRUPTION | INVALID; drops INVALID; resolves
    conflicts; otherwise returns :func:`strict_social_ownership_terminal_fallback`.
    """
    res = resolution if isinstance(resolution, dict) else None
    raw = _collapse_ws(text)
    if not raw:
        return strict_social_ownership_terminal_fallback(res)
    sentences = _split_sentences(raw)
    if not sentences:
        return strict_social_ownership_terminal_fallback(res)

    tag_list = [str(t) for t in tags if isinstance(t, str)] if isinstance(tags, list) else []
    low_tags = {t.strip().lower() for t in tag_list}
    pressure_tag = "topic_pressure_escalation" in low_tags or _is_pressure_active(
        tag_list, session if isinstance(session, dict) else None, str(scene_id or "").strip()
    )

    # 1) Interruption dominates: one coherent breakoff only (trailing sentences ignored).
    intr_merged = _merge_interruption_chunk(sentences)
    if intr_merged:
        return intr_merged.strip()

    # 2) Drop INVALID everywhere; keep only SOCIAL sentences (prefix contamination removed).
    social_sentences: List[str] = []
    labels: List[str] = []
    for s in sentences:
        cat = _classify_strict_social_ownership_sentence(s, res)
        if cat != "social":
            continue
        social_sentences.append(s)
        labels.append(_sentence_form_label(s))

    if not social_sentences:
        return strict_social_ownership_terminal_fallback(res)

    dominant = _dominant_form_from_labels(labels, pressure_tag=pressure_tag)
    if dominant is None:
        return strict_social_ownership_terminal_fallback(res)

    if dominant == "mixed_ignorance_and_direct":
        if _contradictory_flat_ignorance_and_concrete_lead(social_sentences, labels):
            return strict_social_ownership_terminal_fallback(res)
        selected = list(social_sentences)
    else:
        selected = [s for s, lb in zip(social_sentences, labels) if lb == dominant]
    if not selected:
        return strict_social_ownership_terminal_fallback(res)

    out = _collapse_ws(" ".join(selected))
    if _sentence_is_scene_contaminated(out) or _sentence_is_clue_or_analytical_substitute(out):
        return strict_social_ownership_terminal_fallback(res)

    return out


def apply_strict_social_ownership_enforcement(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
) -> str:
    """Alias for :func:`apply_strict_social_sentence_ownership_filter` (final ownership pass)."""
    return apply_strict_social_sentence_ownership_filter(
        text,
        resolution=resolution,
        tags=tags,
        session=session,
        scene_id=scene_id,
    )


def normalize_social_exchange_candidate(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
) -> str:
    """Backward-compatible alias for :func:`apply_strict_social_sentence_ownership_filter`."""
    return apply_strict_social_sentence_ownership_filter(
        text,
        resolution=resolution,
        tags=tags,
        session=session,
        scene_id=scene_id,
    )


def _question_prompt_for_resolution(resolution: Dict[str, Any] | None) -> str:
    return _question_prompt_for_resolution_early(resolution)


def _speaker_label(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "The guard"
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    if name:
        return name
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        return npc_id.replace("_", " ").replace("-", " ").title()
    return "The guard"


def _deterministic_index(seed: str, size: int) -> int:
    if size <= 1:
        return 0
    return sum(ord(ch) for ch in seed) % size


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


def emission_gate_interruption_active(tags: List[str], text: str) -> bool:
    _ = tags
    return interruption_cue_present_in_text(text)


def interruption_cue_present_in_text(text: str) -> bool:
    """Momentum tags alone must not select interruption fallback without diegetic cue."""
    return any(pattern.search(text) for pattern in _INTERRUPTION_PATTERNS)


def deterministic_social_fallback_line(
    *,
    resolution: Dict[str, Any] | None,
    uncertainty_source: str,
    pressure_active: bool,
    interruption_active: bool,
    seed: str,
) -> Tuple[str, str]:
    speaker = _speaker_label(resolution)
    direct_answer = (
        f'{speaker} points down the nearest road. "Old crossroads—that way."',
        f'{speaker} nods once. "Old Millstone. South road."',
    )
    interruption = (
        f"{speaker} starts to answer, then glances past you as shouting breaks out in the crowd.",
        f"{speaker} opens their mouth, then breaks off as a shout cuts across the square.",
    )
    pressure_refusal = (
        f'{speaker} tightens their jaw. "I\'ve told you what I know."',
        f'{speaker} steps back. "That\'s all you\'re getting from me."',
    )
    ignorance = (
        f'{speaker} shakes their head. "I don\'t know."',
        f'{speaker} spreads their hands. "I\'ve heard talk, not names."',
        f'{speaker} lowers their voice. "I have heard the talk, but not the names."',
        f'{speaker} glances away. "I do not know that part for certain."',
        f'{speaker} mutters. "Word is, it was messy—but I won\'t swear to who."',
        f'{speaker} shrugs. "Couldn\'t tell you—only rumors from the road."',
    )
    evasive = (
        f'{speaker} avoids your eyes. "I\'m not naming names."',
        f'{speaker} keeps their voice low. "I won\'t say more here."',
    )
    if interruption_active:
        options, kind = interruption, "interruption"
    elif pressure_active:
        options, kind = pressure_refusal, "pressure_refusal"
    elif uncertainty_source == "procedural_insufficiency":
        options, kind = evasive, "refusal_evasion"
    elif uncertainty_source == "npc_ignorance":
        options, kind = ignorance, "explicit_ignorance"
    else:
        idx = _deterministic_index(seed + "|direct", len(direct_answer))
        return direct_answer[idx], "direct_answer_hint"
    idx = _deterministic_index(seed, len(options))
    return options[idx], kind


def social_fallback_line_for_sanitizer(
    context: Dict[str, Any] | None,
    *,
    source_text: str = "",
    mode: str | None = None,
) -> str:
    """Single-form social line for sanitizer rescue (never scene pools)."""
    resolution = context.get("resolution") if isinstance(context, dict) else None
    session = context.get("session") if isinstance(context, dict) else None
    scene_id = str((context.get("scene_id") or "")).strip()
    if mode == "narration":
        mode = None
    uncertainty = "npc_ignorance"
    if mode == "npc" or mode == "npc_ignorance":
        uncertainty = "npc_ignorance"
    elif mode == "procedural_insufficiency":
        uncertainty = "procedural_insufficiency"
    text = source_text or ""
    tags: List[str] = []
    seed = _collapse_ws(text) or "sanitizer"
    line, _ = deterministic_social_fallback_line(
        resolution=resolution if isinstance(resolution, dict) else None,
        uncertainty_source=uncertainty,
        pressure_active=_is_pressure_active(tags, session if isinstance(session, dict) else None, scene_id),
        interruption_active=False,
        seed=seed,
    )
    return line


def apply_social_exchange_retry_fallback_gm(
    gm: Dict[str, Any],
    *,
    player_text: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """Replace GM text with a compact social fallback (no uncertainty renderer blob)."""
    if not isinstance(gm, dict):
        return gm
    sid_rf = str(scene_id or "").strip()
    if isinstance(resolution, dict) and isinstance(session, dict) and sid_rf:
        soc_r = resolution.get("social") if isinstance(resolution.get("social"), dict) else None
        if isinstance(soc_r, dict) and soc_r.get("target_resolved") is True and not soc_r.get("offscene_target"):
            env_rf = _scene_envelope_for_strict_social(session, sid_rf)
            merged_rf = merged_player_prompt_for_gate(resolution, session, sid_rf)
            meta_rf = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
            na_rf = meta_rf.get("normalized_action") if isinstance(meta_rf.get("normalized_action"), dict) else None
            auth_rf = resolve_authoritative_social_target(
                session,
                world if isinstance(world, dict) else None,
                sid_rf,
                player_text=merged_rf,
                normalized_action=na_rf,
                merged_player_prompt=merged_rf,
                scene_envelope=env_rf,
                allow_first_roster_fallback=True,
            )
            auth_rf, _, _ = _auth_after_social_promotion_binding(
                session,
                world if isinstance(world, dict) else {},
                sid_rf,
                auth_rf,
                env_rf,
                merged_player_prompt=merged_rf,
            )
            apply_social_reply_speaker_grounding(
                soc_r,
                session,
                world if isinstance(world, dict) else {},
                sid_rf,
                env_rf,
                auth_rf,
            )
    out = dict(gm)
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    prior_text = str(out.get("player_facing_text") or "")
    uncertainty_source = _extract_uncertainty_source_from_tags(tag_list, prior_text)
    pressure = _is_pressure_active(tag_list, session, scene_id)
    interrupt = interruption_cue_present_in_text(prior_text)
    seed = f"{scene_id}|retry|{player_text}|{uncertainty_source}|{pressure}|{interrupt}"
    line, kind = deterministic_social_fallback_line(
        resolution=resolution,
        uncertainty_source=uncertainty_source,
        pressure_active=pressure,
        interruption_active=interrupt,
        seed=seed,
    )
    out["player_facing_text"] = line
    out["tags"] = tag_list + ["question_retry_fallback", "social_exchange_retry_fallback", f"social_exchange_fallback:{kind}"]
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (dbg + " | " if dbg else "") + f"retry_fallback:unresolved_question|retry_fallback:social_exchange:{kind}"
    return out


def hard_reject_social_exchange_text(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str = "",
    world: Dict[str, Any] | None = None,
) -> List[str]:
    """Reason codes for illegal final social_exchange emission."""
    from game.gm import question_resolution_rule_check

    reasons: List[str] = []
    t = _collapse_ws(text)
    if not t:
        reasons.append("empty_social_emission")
        return reasons

    res = resolution if isinstance(resolution, dict) else {}
    social = res.get("social") if isinstance(res.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    sid = str(scene_id or "").strip()
    merged = merged_player_prompt_for_gate(resolution if isinstance(resolution, dict) else None, session, sid)
    meta = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
    na = meta.get("normalized_action") if isinstance(meta.get("normalized_action"), dict) else None
    env_hr = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    auth = resolve_authoritative_social_target(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        player_text=merged,
        normalized_action=na,
        merged_player_prompt=merged,
        scene_envelope=env_hr,
        allow_first_roster_fallback=True,
    )
    auth, _, _ = _auth_after_social_promotion_binding(
        session, world, sid, auth, env_hr, merged_player_prompt=merged
    )
    tp_hr = topic_pressure_speaker_id_for_social_exchange(session if isinstance(session, dict) else {}, sid)
    gr_hr = resolve_grounded_social_speaker(
        session if isinstance(session, dict) else {},
        world if isinstance(world, dict) else {},
        sid,
        env_hr,
        auth,
        proposed_reply_speaker_id=npc_id or None,
        topic_pressure_speaker_id=tp_hr,
    )
    if social.get("reply_speaker_grounding_neutral_bridge"):
        pass
    elif npc_id and not gr_hr.get("allowed"):
        reasons.append("reply_speaker_grounding_denied")
    elif npc_id and gr_hr.get("grounded_actor_id") and npc_id != str(gr_hr.get("grounded_actor_id") or "").strip():
        reasons.append("speaker_binding_mismatch")

    player_prompt = merged or _question_prompt_for_resolution(resolution if isinstance(resolution, dict) else None)
    if player_prompt:
        first_sentence_contract = question_resolution_rule_check(
            player_text=player_prompt,
            gm_reply_text=t,
            resolution=resolution if isinstance(resolution, dict) else None,
        )
        if first_sentence_contract.get("applies") and not first_sentence_contract.get("ok"):
            reasons.extend([f"first_sentence_illegal:{r}" for r in list(first_sentence_contract.get("reasons") or [])])

    low = t.lower()
    advisory = (
        r"\bi['’]d suggest you\b",
        r"\byou should\b",
        r"\byou could\b",
        r"\bbest lead\b",
        r"\bconsider\b",
    )
    if any(re.search(p, low) for p in advisory):
        reasons.append("advisory_prose_in_social_exchange")

    if any(p.search(t) for p in _SCENE_CONTAMINATION_PATTERNS):
        reasons.append("scene_or_ambient_contamination")

    banned = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
        "nothing in the scene points to a clear answer yet",
        "the answer has not formed yet",
    )
    if any(b in low for b in banned):
        reasons.append("banned_stock_phrase")

    for seg in _split_sentences(t):
        if _sentence_is_detached_omniscient_analysis(seg):
            reasons.append("detached_omniscient_analysis")
            break

    has_npc_answer = bool(re.search(r"\".+?\"", t, re.DOTALL)) or bool(
        re.search(
            r"\b(?:says|replies|answers|shakes|shrugs|frowns|jaw tightens|starts to answer)\b",
            t,
            re.IGNORECASE,
        )
    )
    has_interrupt = any(p.search(t) for p in _INTERRUPTION_PATTERNS)
    if has_npc_answer and has_interrupt and not _has_explicit_interruption_shape(t):
        reasons.append("mixed_npc_answer_and_scene_interrupt_blob")

    if re.search(r"\bthe scene holds\b", low) or re.search(r"\bscene stays still\b", low):
        reasons.append("scene_hold_placeholder")

    return reasons


def _normalize_gate_text(text: str | None) -> str:
    """Whitespace normalization matching :func:`game.final_emission_gate._normalize_text`."""
    return " ".join(str(text or "").strip().split())


def _speaker_label_for_emission_seed(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "The guard"
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    if name:
        return name
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        return npc_id.replace("_", " ").replace("-", " ").title()
    return "The guard"


def _assert_all_sentences_strict_social_or_interruption(
    text: str,
    resolution: Dict[str, Any] | None,
) -> None:
    """Temporary invariant: final strict-social output must be only SOCIAL or INTERRUPTION sentences."""
    res = resolution if isinstance(resolution, dict) else None
    raw = _collapse_ws(text)
    if not raw:
        return
    for sent in _split_sentences(raw):
        s = (sent or "").strip()
        if not s:
            continue
        cat = _classify_strict_social_ownership_sentence(s, res)
        if cat not in ("social", "interruption"):
            raise AssertionError(
                f"strict_social_final_invariant: sentence not SOCIAL or INTERRUPTION: {cat!r}: {s[:120]!r}"
            )


def _looks_like_strict_social_terminal_placeholder(text: str) -> bool:
    """True for ownership-filter terminal ignorance / tight-lipped lines (not substantive NPC answers)."""
    low = str(text or "").strip().lower()
    if not low:
        return True
    if any(p.search(str(text or "")) for p in _SCENE_CONTAMINATION_PATTERNS):
        return True
    if "hard to say" in low and ("whisper" in low or "nobody" in low or "swear" in low):
        return True
    if re.search(r"\b(don'?t know|do not know|no names here|won'?t name)\b", low) and (
        "shake" in low or "grimace" in low or "mutter" in low or "spread" in low
    ):
        return True
    return False


def _structured_fact_emission_details() -> dict[str, Any]:
    return {
        "used_internal_fallback": False,
        "fallback_kind": "none",
        "rejection_reasons": [],
        "final_emitted_source": "structured_fact_candidate_emission",
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "structured_fact",
        "route_illegal_intercepted": False,
        "intercepted_preview": "",
        "candidate_quality_degraded": False,
        "resolved_answer_preferred": False,
        "resolved_answer_source": None,
        "resolved_answer_preference_reason": None,
    }


def select_best_grounded_social_answer_text(
    *,
    session: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Return the strongest engine-owned social answer snippet (no narration pools / lead salience).

    Delegates to :func:`game.social.select_best_social_answer_candidate` with the same precedence
    as structured strict-social fallbacks: ``topic_revealed``, topic-pressure ``last_answer``,
    reconciled ``clue_knowledge``, then redirect-style ``last_answer`` partials.
    """
    sid = str(scene_id or "").strip()
    sess = session if isinstance(session, dict) else None
    res = resolution if isinstance(resolution, dict) else None
    merged = merged_player_prompt_for_gate(res, sess, sid)
    soc: Dict[str, Any] = {}
    if isinstance(res, dict):
        s = res.get("social")
        if isinstance(s, dict):
            soc = s
    nid = str(soc.get("npc_id") or "").strip() or None
    cand = select_best_social_answer_candidate(
        session=sess if sess is not None else {},
        scene_id=sid,
        npc_id=nid,
        topic_key=None,
        player_text=merged,
        resolution=res,
    )
    kind = str(cand.get("answer_kind") or "").strip()
    txt = str(cand.get("text") or "").strip()
    if kind not in ("structured_fact", "reconciled_fact", "partial_answer") or not txt:
        return {"text": None, "source": str(cand.get("source") or "none"), "answer_kind": kind or "refusal"}
    return {"text": txt, "source": str(cand.get("source") or ""), "answer_kind": kind}


_ACTIONABLE_DETAIL_RE = re.compile(
    r"\b(?:east|west|north|south|road|lane|gate|mill|square|market|crossroad|milestone|patrol)\b",
    re.IGNORECASE,
)


def _actionable_hits(text: str) -> set[str]:
    return {m.group(0).lower() for m in _ACTIONABLE_DETAIL_RE.finditer(str(text or ""))}


def _strict_social_bounded_evasion_or_placeholder_candidate(text: str) -> bool:
    """True for refusal / flat ignorance / pressure-only lines that should not beat substantive facts."""
    t = _collapse_ws(str(text or ""))
    if not t:
        return True
    if _looks_like_strict_social_terminal_placeholder(t):
        return True
    sents = _split_sentences(t)
    if not sents:
        return True
    if len(sents) > 1:
        return False
    s0 = sents[0]
    if any(p.search(s0) for p in _REFUSAL_SIGNAL_PATTERNS):
        return True
    if any(p.search(s0) for p in _PRESSURE_SIGNAL_PATTERNS) and '"' not in s0:
        return True
    if _is_flat_idk_without_qualifier(s0):
        return True
    low = s0.lower()
    if re.search(r"\b(?:can'?t|cannot)\s+help\b", low) and '"' not in s0:
        return True
    return False


def _strict_social_elliptical_fragment_candidate(text: str) -> bool:
    t = _collapse_ws(str(text or "")).strip()
    if not t:
        return True
    core = t.rstrip(".!?…").strip()
    if len(core) <= 6 and core.lower() in {"just", "only", "right", "there", "here", "well"}:
        return True
    if re.match(r"^just\s*\.?$", t, re.IGNORECASE):
        return True
    return False


def _strict_social_fragmentary_trailing_clause(text: str) -> bool:
    t = _collapse_ws(str(text or ""))
    low = t.lower()
    if re.search(r"\b(?:though|because|if|when)\s+the\s+\w+\s*$", low):
        return True
    if re.search(r",\s*though\s*$", low) and len(t) < 48:
        return True
    return False


def _grounded_snippet_is_substantive(snippet: str, *, answer_kind: str) -> bool:
    s = _collapse_ws(str(snippet or ""))
    if len(s) < 14:
        return False
    if answer_kind == "partial_answer":
        return len(s) >= 18
    return True


def _normalized_social_candidate_is_degraded_vs_grounded(
    accepted_text: str,
    grounded_snippet: str,
    *,
    answer_kind: str,
) -> tuple[bool, str]:
    """Conservative: True only when the accepted line is clearly worse than engine-grounded text."""
    c = _collapse_ws(str(accepted_text or ""))
    g = _collapse_ws(str(grounded_snippet or ""))
    if not c or not g:
        return False, ""
    if not _grounded_snippet_is_substantive(g, answer_kind=answer_kind):
        return False, ""
    if c.strip() == g.strip():
        return False, ""

    if _strict_social_bounded_evasion_or_placeholder_candidate(c):
        return True, "evasion_or_placeholder_over_substantive_grounded_answer"

    if _strict_social_elliptical_fragment_candidate(c):
        return True, "elliptical_fragment"

    if _strict_social_fragmentary_trailing_clause(c):
        return True, "fragmentary_trailing_clause"

    gl, cl = g.lower(), c.lower()
    if len(g) >= 52 and len(c) < len(g) * 0.5:
        gh = _actionable_hits(g)
        ch = _actionable_hits(c)
        if gh and gh - ch:
            return True, "lost_actionable_detail_vs_grounded_answer"

    if len(g) >= 40 and len(c) + 35 < len(g):
        toks = [t for t in re.findall(r"[a-z]{5,}", gl) if t not in {"their", "there", "where", "which", "would", "could", "about", "mutters", "runner", "guard", "tavern"}]
        hits = sum(1 for t in toks[:10] if t in cl)
        if len(toks) >= 4 and hits <= 1:
            return True, "much_shorter_less_informative_vs_grounded_answer"

    return False, ""


def _strict_social_resolved_line_passes_legality(
    line: str,
    *,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
) -> bool:
    t = _normalize_gate_text(line)
    low = t.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        return False
    return not hard_reject_social_exchange_text(
        t,
        resolution=resolution,
        session=session if isinstance(session, dict) else None,
        scene_id=str(scene_id or "").strip(),
        world=world if isinstance(world, dict) else None,
    )


def _prefer_resolved_social_answer_over_candidate(
    accepted_text: str,
    *,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    tags: List[str],
) -> tuple[str, Dict[str, Any]]:
    """If accepted text is clearly degraded vs engine-grounded facts, emit formatted grounded line instead.

    The replacement must pass the same strict-social ownership filter and
    :func:`hard_reject_social_exchange_text` checks as normal final emission.
    """
    sid = str(scene_id or "").strip()
    base_meta: Dict[str, Any] = {
        "candidate_quality_degraded": False,
        "resolved_answer_preferred": False,
        "resolved_answer_source": None,
        "resolved_answer_preference_reason": None,
    }
    sess = session if isinstance(session, dict) else None
    if not sid or not isinstance(resolution, dict):
        return accepted_text, base_meta

    grounded = select_best_grounded_social_answer_text(
        session=sess,
        scene_id=sid,
        resolution=resolution,
    )
    snippet = grounded.get("text")
    src = str(grounded.get("source") or "")
    akind = str(grounded.get("answer_kind") or "")
    if not isinstance(snippet, str) or not str(snippet).strip():
        return accepted_text, base_meta

    degraded, deg_reason = _normalized_social_candidate_is_degraded_vs_grounded(
        accepted_text,
        str(snippet).strip(),
        answer_kind=akind,
    )
    if not degraded:
        return accepted_text, base_meta

    base_meta["candidate_quality_degraded"] = True
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    synth = format_structured_fact_social_line(resolution, str(snippet).strip())
    synth_f = apply_strict_social_sentence_ownership_filter(
        synth,
        resolution=resolution,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    synth_n = _normalize_gate_text(synth_f)
    if synth_n.strip() == _normalize_gate_text(accepted_text).strip():
        base_meta["candidate_quality_degraded"] = False
        return accepted_text, base_meta

    if not _strict_social_resolved_line_passes_legality(
        synth_n,
        resolution=resolution,
        session=sess,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
    ):
        base_meta["resolved_answer_preference_reason"] = "stronger_answer_failed_strict_legality"
        return accepted_text, base_meta

    base_meta["resolved_answer_preferred"] = True
    base_meta["resolved_answer_source"] = src or None
    base_meta["resolved_answer_preference_reason"] = deg_reason
    _assert_all_sentences_strict_social_or_interruption(synth_n, resolution)
    return synth_n, base_meta


def _try_emit_structured_fact_strict_line(
    *,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    tag_list: List[str],
) -> str | None:
    """If topic pressure / clues hold a factual answer, return route-legal strict-social text."""
    sid = str(scene_id or "").strip()
    sess = session if isinstance(session, dict) else None
    merged_pt = merged_player_prompt_for_gate(resolution, sess, sid)
    soc_pre = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    nid_pre = str(soc_pre.get("npc_id") or "").strip() or None
    cand = select_best_social_answer_candidate(
        session=sess,
        scene_id=sid,
        npc_id=nid_pre,
        topic_key=None,
        player_text=merged_pt,
        resolution=resolution,
    )
    if cand.get("answer_kind") not in ("structured_fact", "reconciled_fact") or not str(cand.get("text") or "").strip():
        return None
    synth = format_structured_fact_social_line(resolution, str(cand.get("text") or ""))
    synth_f = apply_strict_social_sentence_ownership_filter(
        synth,
        resolution=resolution,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    synth_n = _normalize_gate_text(synth_f)
    low_s = synth_n.lower()
    banned_any_route2 = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    reasons2: List[str] = []
    if any(phrase in low_s for phrase in banned_any_route2):
        reasons2.append("banned_stock_phrase")
    reasons2.extend(
        hard_reject_social_exchange_text(
            synth_n,
            resolution=resolution,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
        )
    )
    if reasons2:
        return None
    if isinstance(resolution.get("social"), dict):
        resolution["social"]["answer_candidate_selected"] = str(cand.get("answer_kind") or "")
        resolution["social"]["answer_candidate_source"] = str(cand.get("source") or "")
        resolution["social"]["answer_candidate_dimension"] = classify_social_question_dimension(merged_pt)
        resolution["social"]["refusal_suppressed_by_structured_fact"] = True
    preview = synth_n[:140] + ("…" if len(synth_n) > 140 else "")
    resolution["hint"] = (
        "Final strict-social emission used stored thread facts as the spoken NPC line "
        f"({preview}). This is not a refusal and not an empty-information turn."
    )
    _assert_all_sentences_strict_social_or_interruption(synth_n, resolution)
    return synth_n


def build_final_strict_social_response(
    candidate_text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
    world: Optional[Dict[str, Any]] = None,
) -> tuple[str, dict[str, Any]]:
    """Single final writer for strict-social turns.

    Runs :func:`apply_strict_social_sentence_ownership_filter` on the candidate, then
    :func:`hard_reject_social_exchange_text` (and the same banned-phrase gate as the emission gate).
    If the result is rejected, selects deterministic / emergency fallback and runs the ownership
    filter again on that fallback candidate so no unfiltered line reaches the player.
    """
    tag_list = [str(t) for t in tags if isinstance(t, str)] if isinstance(tags, list) else []
    res = resolution if isinstance(resolution, dict) else None
    sid = str(scene_id or "").strip()
    sess = session if isinstance(session, dict) else None

    soc0 = res.get("social") if isinstance(res, dict) and isinstance(res.get("social"), dict) else {}
    if soc0.get("reply_speaker_grounding_neutral_bridge"):
        nb = neutral_reply_speaker_grounding_bridge_line(
            seed=f"{sid}|neutral_grounding|{_question_prompt_for_resolution_early(res)}"
        )
        return nb, {
            "used_internal_fallback": True,
            "fallback_kind": "neutral_speaker_grounding_bridge",
            "rejection_reasons": [],
            "final_emitted_source": "neutral_reply_speaker_grounding_bridge",
            "deterministic_attempted": False,
            "deterministic_passed": False,
            "fallback_pool": "neutral_grounding",
            "route_illegal_intercepted": False,
            "intercepted_preview": "",
            "candidate_quality_degraded": False,
            "resolved_answer_preferred": False,
            "resolved_answer_source": None,
            "resolved_answer_preference_reason": None,
        }

    filtered = apply_strict_social_sentence_ownership_filter(
        candidate_text,
        resolution=res,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    text = _normalize_gate_text(filtered)

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    reasons: List[str] = []
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")
    reasons.extend(
        hard_reject_social_exchange_text(
            text,
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
        )
    )

    if not reasons:
        soc_ok = res.get("social") if isinstance(res, dict) and isinstance(res.get("social"), dict) else {}
        prefer_structured = bool(
            isinstance(res, dict)
            and (
                str(soc_ok.get("reply_kind") or "").strip().lower() == "refusal"
                or res.get("success") is not True
                or soc_ok.get("refusal_suppressed_by_structured_fact") is True
            )
        )
        if prefer_structured and isinstance(res, dict) and _looks_like_strict_social_terminal_placeholder(text):
            st = _try_emit_structured_fact_strict_line(
                resolution=res,
                session=sess,
                scene_id=sid,
                world=world if isinstance(world, dict) else None,
                tag_list=tag_list,
            )
            if st:
                return st, _structured_fact_emission_details()
        pref_text, pref_meta = _prefer_resolved_social_answer_over_candidate(
            text,
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tags=tag_list,
        )
        text = pref_text
        _assert_all_sentences_strict_social_or_interruption(text, res)
        final_emitted_source = (
            "generated_candidate"
            if _normalize_gate_text(candidate_text).strip() == text.strip()
            else "normalized_social_candidate"
        )
        if pref_meta.get("resolved_answer_preferred"):
            final_emitted_source = "resolved_grounded_social_answer"
        return text, {
            "used_internal_fallback": False,
            "fallback_kind": "none",
            "rejection_reasons": [],
            "final_emitted_source": final_emitted_source,
            "deterministic_attempted": False,
            "deterministic_passed": False,
            "fallback_pool": "none",
            "route_illegal_intercepted": False,
            "intercepted_preview": "",
            **pref_meta,
        }

    if isinstance(res, dict):
        st2 = _try_emit_structured_fact_strict_line(
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tag_list=tag_list,
        )
        if st2:
            return st2, _structured_fact_emission_details()

    uncertainty_source = emission_gate_uncertainty_source(tag_list, text)
    pressure_active = emission_gate_pressure_active(tag_list, session, sid)
    interruption_active = emission_gate_interruption_active(tag_list, text)
    seed = (
        f"{sid}|{_speaker_label_for_emission_seed(res)}|{_question_prompt_for_resolution_early(res)}|"
        f"{uncertainty_source}|{pressure_active}|{interruption_active}|{'|'.join(sorted(set(tag_list)))}"
    )
    fallback_pool = "social_deterministic"
    deterministic_attempted = True
    fallback_text, fallback_kind = deterministic_social_fallback_line(
        resolution=res,
        uncertainty_source=uncertainty_source,
        pressure_active=pressure_active,
        interruption_active=interruption_active,
        seed=seed,
    )
    deterministic_passed = replacement_is_route_legal_social(
        fallback_text,
        resolution=res,
        session=sess,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
    )
    final_emitted_source = "deterministic_social_fallback"
    if not deterministic_passed:
        fallback_text = minimal_social_emergency_fallback_line(res)
        fallback_kind = "emergency_social_minimal"
        final_emitted_source = "minimal_social_emergency_fallback"
        deterministic_passed = False

    route_illegal_intercepted = False
    intercepted_preview = ""
    if is_route_illegal_global_or_sanitizer_fallback_text(fallback_text):
        intercepted_preview = fallback_text[:80]
        fallback_text = minimal_social_emergency_fallback_line(res)
        fallback_kind = "emergency_social_minimal"
        final_emitted_source = "minimal_social_emergency_fallback"
        deterministic_passed = False
        route_illegal_intercepted = True

    fb_filtered = apply_strict_social_sentence_ownership_filter(
        fallback_text,
        resolution=res,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    out_text = _normalize_gate_text(fb_filtered)
    _assert_all_sentences_strict_social_or_interruption(out_text, res)

    return out_text, {
        "used_internal_fallback": True,
        "fallback_kind": fallback_kind,
        "rejection_reasons": reasons,
        "final_emitted_source": final_emitted_source,
        "deterministic_attempted": deterministic_attempted,
        "deterministic_passed": deterministic_passed,
        "fallback_pool": fallback_pool,
        "route_illegal_intercepted": route_illegal_intercepted,
        "intercepted_preview": intercepted_preview,
        "candidate_quality_degraded": False,
        "resolved_answer_preferred": False,
        "resolved_answer_source": None,
        "resolved_answer_preference_reason": None,
    }
