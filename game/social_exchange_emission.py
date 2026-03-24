"""Route-isolated emission helpers for active social_exchange turns.

Ensures player-facing text is speaker-owned, single-form, and never pulled from
scene/ambient uncertainty pools except as an explicit interruption breakoff.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from game.interaction_context import (
    _world_npc_dicts_for_addressing,
    assert_valid_speaker,
    effective_in_scene_npc_roster,
    inspect as inspect_interaction_context,
    line_opens_with_comma_vocative,
    npc_id_from_explicit_generic_role_address,
    npc_id_from_substring_line,
    npc_id_from_vocative_line,
    npc_roster_for_dialogue_addressing,
)

# Historical name in this module; delegates to canonical roster resolution in interaction_context.
effective_scene_npc_roster = effective_in_scene_npc_roster
from game.storage import get_scene_runtime
from game.utils import slugify

_log = logging.getLogger(__name__)

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
) -> Tuple[str, str]:
    """Pick the NPC for strict-social coercion: ``(npc_id, basis)``.

    ``basis`` is one of: ``vocative``, ``generic_address``, ``active``, ``active_unlisted``,
    ``substring``, ``first_roster``, ``none``.
    Resolution order: vocative address (shared resolver with dialogue binding), then
    explicit generic role address (same scoped roster as dialogue binding), then
    :func:`inspect` ``active_interaction_target_id``, then substring/name overlap, then
    first roster only as a last resort. Vocative wins over active interlocutor so
    ``Runner, …`` targets the runner even if context points elsewhere.
    """
    sid = str(scene_id or "").strip()
    roster = effective_scene_npc_roster(world, sid)
    prompt = str(merged_player_prompt or "").strip()
    if roster and prompt:
        voc = npc_id_from_vocative_line(prompt, roster)
        if voc:
            return voc, "vocative"
        wroster = _world_npc_dicts_for_addressing(world if isinstance(world, dict) else {})
        voc_w = npc_id_from_vocative_line(prompt, wroster)
        if voc_w:
            return voc_w, "vocative"
    w = world if isinstance(world, dict) else {}
    addressable = npc_roster_for_dialogue_addressing(
        w,
        sid,
        scene=None,
        session=session if isinstance(session, dict) else None,
    )
    if addressable and prompt:
        gen = npc_id_from_explicit_generic_role_address(prompt.lower(), addressable)
        if gen:
            return gen, "generic_address"
    if isinstance(session, dict):
        inspected = inspect_interaction_context(session)
        active = str((inspected or {}).get("active_interaction_target_id") or "").strip()
        if active and assert_valid_speaker(active, session):
            for npc in roster:
                if isinstance(npc, dict) and str(npc.get("id") or "").strip() == active:
                    return active, "active"
            return active, "active_unlisted"
    if roster and prompt:
        sub = npc_id_from_substring_line(prompt, roster)
        if sub:
            return sub, "substring"
    if roster:
        first = str(roster[0].get("id") or "").strip()
        if first:
            return first, "first_roster"
    return "", "none"


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
    if looks_like_npc_directed_question(text):
        return True
    sid = str(scene_id or "").strip()
    w = world if isinstance(world, dict) else {}
    roster = effective_scene_npc_roster(w, sid)
    addressable = npc_roster_for_dialogue_addressing(
        w,
        sid,
        scene=None,
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
    target, _basis = resolve_strict_social_npc_target_id(session, world, sid, prompt)
    if not target:
        return None
    npc_name = _npc_display_name_for_emission(world, sid, target)
    return {
        "kind": "question",
        "prompt": prompt,
        "label": prompt[:140],
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": target,
            "npc_name": npc_name,
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
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
    """Resolve a short speaker label; avoids depending on resolution.social.npc_name being present."""
    from game.defaults import default_world
    from game.social import find_npc_by_target

    sid = str(scene_id or "").strip()
    nid = str(npc_id or "").strip()
    if not nid:
        return "The guard"
    npc = find_npc_by_target(world or {}, nid, sid) if world is not None else None
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
    target, basis = resolve_strict_social_npc_target_id(session, world, sid, prompt)
    if not target:
        return None
    if basis in {"active", "active_unlisted"}:
        inspected = inspect_interaction_context(session)
        kind = str((inspected or {}).get("active_interaction_kind") or "").strip().lower()
        mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
        engagement = str((inspected or {}).get("engagement_level") or "").strip().lower()
        if not ((kind == "social" or mode == "social") and engagement in {"engaged", "active", ""}):
            return None
    npc_name = _npc_display_name_for_emission(world, sid, target)
    return {
        "kind": "question",
        "prompt": prompt,
        "label": prompt[:140],
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": target,
            "npc_name": npc_name,
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
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
    """Align ``resolution.social`` NPC fields with :func:`resolve_strict_social_npc_target_id` (merged prompt).

    Prevents deterministic fallbacks from using a stale engine ``npc_id`` or ``first_roster`` ambient NPC
    when vocative / active interlocutor / substring addressing resolves a different target.
    """
    sid = str(scene_id or "").strip()
    if not isinstance(resolution, dict) or not sid:
        return resolution
    merged = merged_player_prompt_for_gate(resolution, session, sid)
    target_id, _basis = resolve_strict_social_npc_target_id(session, world, sid, merged)
    if not target_id:
        return resolution
    out = dict(resolution)
    soc = dict(resolution.get("social") or {}) if isinstance(resolution.get("social"), dict) else {}
    soc["npc_id"] = target_id
    soc["npc_name"] = _npc_display_name_for_emission(world, sid, target_id)
    if not str(soc.get("social_intent_class") or "").strip():
        soc["social_intent_class"] = "social_exchange"
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
    canonical_id, _basis = resolve_strict_social_npc_target_id(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        merged,
    )
    if npc_id and canonical_id and npc_id != canonical_id:
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
        _assert_all_sentences_strict_social_or_interruption(text, res)
        final_emitted_source = (
            "generated_candidate"
            if _normalize_gate_text(candidate_text).strip() == text.strip()
            else "normalized_social_candidate"
        )
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
        }

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
    }
