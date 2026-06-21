"""Strict-social eligibility and resolution policy (BV14A canonical owner)."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple

from game.dialogue_targeting import line_opens_with_comma_vocative, npc_id_from_vocative_line
from game.exploration import EXPLORATION_KINDS
from game.interaction_context import (
    assert_valid_speaker,
    canonical_scene_addressable_roster,
    effective_in_scene_npc_roster,
    inspect as inspect_interaction_context,
    npc_id_from_explicit_generic_role_address,
    resolve_authoritative_social_target,
    scene_addressable_actor_ids,
    session_allows_implicit_social_reply_authority,
)
from game.prompt_context import canonical_interaction_target_npc_id
from game.social import (
    SOCIAL_KINDS,
    apply_social_reply_speaker_grounding,
    finalize_social_target_with_promotion,
)
from game.storage import get_scene_runtime

_log = logging.getLogger(__name__)

effective_scene_npc_roster = effective_in_scene_npc_roster

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
    """Load effective scene state and overlay live ``session.scene_state`` (active_entities scope)."""
    sid = str(scene_id or "").strip()
    if not sid:
        return None
    from game.storage import get_effective_scene

    env = get_effective_scene(session or {}, sid)
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
    npc_name = npc_display_name_for_emission(world, sid, target)
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

def npc_display_name_for_emission(world: Dict[str, Any] | None, scene_id: str, npc_id: str) -> str:
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
    npc_name = npc_display_name_for_emission(world, sid, target)
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
    soc0 = resolution.get("social")
    if isinstance(soc0, dict) and (
        soc0.get("open_social_solicitation")
        or str(soc0.get("social_intent_class") or "").strip().lower() == "open_call"
    ):
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
    soc["npc_name"] = npc_display_name_for_emission(world, sid, target_id)
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

    from game.interaction_context import build_speaker_selection_contract

    speaker_contract = build_speaker_selection_contract(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        resolution=out,
        normalized_action=na,
        scene_envelope=env,
        merged_player_prompt=merged,
        _engine_authoritative_target=dict(auth),
        _engine_grounded_social=dict(soc),
    )
    md = out.setdefault("metadata", {})
    if isinstance(md, dict):
        em_dbg = md.setdefault("emission_debug", {})
        if isinstance(em_dbg, dict):
            # Consumed by :func:`game.final_emission_gate.enforce_emitted_speaker_with_contract` (no re-resolve).
            em_dbg["speaker_selection_contract"] = speaker_contract

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

def _question_prompt_for_resolution(resolution: Dict[str, Any] | None) -> str:
    return _question_prompt_for_resolution_early(resolution)

def speaker_label(resolution: Dict[str, Any] | None) -> str:
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
