"""Deterministic social action resolution: engine-first before GPT narration.

Supported kinds: question, persuade, intimidate, deceive, barter, recruit, social_probe.

Skill mapping (canonical, conservative):
- question / social_probe: no hard skill check unless explicitly configured
- persuade: Diplomacy
- intimidate: Intimidate
- deceive: Bluff if present; else skip check (fallback cleanly, no crash)
- barter: Diplomacy (canonical; appraise not used—see docstring)
- recruit: Diplomacy with stricter DC (+3)
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from game.models import SocialEngineResult, make_check_request, social_result_to_dict
from game.utils import slugify
from game.storage import get_npc_runtime
from game.interaction_context import (
    apply_turn_input_implied_context,
    canonical_scene_addressable_roster,
    npc_dict_by_id,
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
    scene_addressable_actor_ids,
    set_non_social_activity,
    set_social_target,
)
from game.skill_checks import should_trigger_check

# Skill mapping: action_kind -> (skill_id, dc_modifier)
# dc_modifier: added to base DC 10. recruit uses +3.
SOCIAL_SKILL_MAP = {
    "question": None,  # No check by default
    "social_probe": None,
    "persuade": ("diplomacy", 0),
    "intimidate": ("intimidate", 0),
    "deceive": ("bluff", 0),  # fallback: diplomacy if bluff absent
    "barter": ("diplomacy", 0),  # Canonical: Diplomacy for barter. Appraise not used.
    "recruit": ("diplomacy", 3),  # Stricter threshold
}

SOCIAL_KINDS = tuple(SOCIAL_SKILL_MAP.keys())
SOCIAL_EXCHANGE_KINDS = ("question", "social_probe")
SOCIAL_MANEUVER_KINDS = ("persuade", "intimidate", "deceive", "barter", "recruit")

_DIRECT_QUESTION_WORDS = ("who", "what", "where", "when", "why", "how", "which")
_NAME_REQUEST_TOKENS = ("your name", "their name", "his name", "her name", "called", "who are you")
_DESTINATION_REQUEST_TOKENS = ("where to", "where can i find", "where can we find", "destination", "headed", "going")
_EXPLANATION_REQUEST_TOKENS = ("explain", "why", "how", "what happened", "tell me about", "go on", "continue")
_TERMS_REQUEST_TOKENS = ("terms", "price", "cost", "deal", "conditions", "arrangement")
_LISTENING_INVITE_TOKENS = (
    "i'm listening",
    "im listening",
    "i am listening",
    "go on",
    "continue",
    "tell me more",
    "please continue",
    "what happened next",
    "go ahead",
)


def social_intent_class(kind: str) -> str:
    """Classify social action kind into exchange vs maneuver."""
    k = (kind or "").strip().lower()
    if k in SOCIAL_MANEUVER_KINDS:
        return "social_maneuver"
    return "social_exchange"

# Verb patterns for parse_social_intent: (pattern, action_type, extracts_target)
SOCIAL_PATTERNS = [
    (r"\bpersuade\s+(?:the\s+)?(.+?)(?:\s+to\s+|\s+that\s+)?\.?$", "persuade", True),
    (r"\bpersuade\s+(?:the\s+)?(.+?)\b", "persuade", True),
    (r"\bintimidate\s+(?:the\s+)?(.+?)(?:\s+into\s+|\s+to\s+)?\.?$", "intimidate", True),
    (r"\bintimidate\s+(?:the\s+)?(.+?)\b", "intimidate", True),
    (r"\bdeceive\s+(?:the\s+)?(.+?)(?:\s+into\s+|\s+about\s+)?\.?$", "deceive", True),
    (r"\bdeceive\s+(?:the\s+)?(.+?)\b", "deceive", True),
    (r"\bbarter\s+(?:with\s+)?(?:the\s+)?(.+?)(?:\s+for\s+)?\.?$", "barter", True),
    (r"\bbarter\s+(?:with\s+)?(?:the\s+)?(.+?)\b", "barter", True),
    (r"\brecruit\s+(?:the\s+)?(.+?)(?:\s+to\s+|\s+for\s+)?\.?$", "recruit", True),
    (r"\brecruit\s+(?:the\s+)?(.+?)\b", "recruit", True),
    (r"\b(?:ask|question|query)\s+(?:the\s+)?(.+?)(?:\s+about\s+)?\.?$", "question", True),
    (r"\b(?:talk\s+to|talk\s+with|speak\s+to|speak\s+with|chat\s+with|greet)\s+(?:the\s+)?(.+?)(?:\s+about\s+)?\.?$", "question", True),
    (r"\b(gauge|approach)\s+(?:the\s+)?(.+?)\.?$", "social_probe", True),
]


def parse_social_intent(
    text: str,
    scene_envelope: Optional[Dict[str, Any]] = None,
    world: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Parse freeform player input into a structured social action.

    Returns structured action with id, label, type (question|persuade|intimidate|etc.),
    prompt, target_id. Returns None when no social pattern matches or when world has no npcs.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.strip()
    if not t:
        return None
    low = t.lower()

    npcs = (world or {}).get("npcs") or []
    if not isinstance(npcs, list) or len(npcs) == 0:
        return None

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()

    for pattern, action_type, extracts in SOCIAL_PATTERNS:
        m = re.search(pattern, low, re.IGNORECASE)
        if not m:
            continue
        target = None
        if extracts and m.lastindex and m.lastindex >= 2:
            target = m.group(2).strip()
        elif extracts and m.lastindex:
            target = m.group(1).strip()
        if target and len(target) > 50:
            target = target[:50]
        target_slug = slugify(target) if target else None
        for npc in npcs:
            if not isinstance(npc, dict):
                continue
            nid = str(npc.get("id") or "").strip()
            name = str(npc.get("name") or "").strip()
            loc = npc.get("location") or npc.get("scene_id") or ""
            loc = str(loc).strip() if loc else ""
            if not nid or loc != scene_id:
                continue
            if target_slug and (slugify(nid) == target_slug or slugify(name) == target_slug or target_slug in slugify(nid) or target_slug in slugify(name)):
                return {
                    "id": slugify(f"{action_type}-{nid}") or "social",
                    "label": t,
                    "type": action_type,
                    "social_intent_class": social_intent_class(action_type),
                    "prompt": t,
                    "target_id": nid,
                    "targetEntityId": nid,
                }
        if target:
            return {
                "id": slugify(f"{action_type}-{target}")[:40] or "social",
                "label": t,
                "type": action_type,
                "social_intent_class": social_intent_class(action_type),
                "prompt": t,
                "target_id": target,
                "targetEntityId": target,
            }
    return None


def _get_skill_modifier(character: Dict[str, Any], skill_id: str) -> int:
    """Return character's skill modifier; 0 if skill not present."""
    if not character or not isinstance(character.get("skills"), dict):
        return 0
    v = character["skills"].get(skill_id)
    if v is None:
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _resolve_skill_for_kind(kind: str, character: Dict[str, Any]) -> Optional[str]:
    """Return effective skill_id for social kind. Deceive falls back to diplomacy if bluff absent."""
    entry = SOCIAL_SKILL_MAP.get(kind)
    if entry is None:
        return None
    skill_id, _ = entry
    if skill_id == "bluff":
        skills = character.get("skills") or {}
        if "bluff" in skills and skills.get("bluff") is not None:
            return "bluff"
        return "diplomacy"  # Fallback: no crash
    return skill_id


def find_npc_by_target(
    world: Dict[str, Any],
    target_hint: str,
    scene_id: str,
) -> Optional[Dict[str, Any]]:
    """Find NPC by target id or approximate name. Must be in scene (scene_id or location).

    Returns NPC dict or None if not found/unreachable.
    """
    if not target_hint or not isinstance(target_hint, str):
        return None
    hint = target_hint.strip()
    if not hint:
        return None
    hint_slug = slugify(hint)

    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return None

    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        name = str(npc.get("name") or "").strip()
        loc = npc.get("location") or npc.get("scene_id") or ""
        loc = str(loc).strip() if loc else ""

        if not nid:
            continue
        # Must be in current scene; unknown location does not count as in-scene.
        if loc != scene_id:
            continue

        if nid == hint or nid.lower() == hint.lower():
            return npc
        if slugify(nid) == hint_slug or hint_slug in slugify(nid):
            return npc
        if name and (name.lower() == hint.lower() or slugify(name) == hint_slug or hint_slug in slugify(name)):
            return npc
    return None


def _find_world_npc_by_target(world: Dict[str, Any], target_hint: str) -> Optional[Dict[str, Any]]:
    if not target_hint or not isinstance(target_hint, str):
        return None
    hint = target_hint.strip()
    if not hint:
        return None
    hint_slug = slugify(hint)
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return None
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        name = str(npc.get("name") or "").strip()
        if not nid:
            continue
        if nid == hint or nid.lower() == hint.lower():
            return npc
        if slugify(nid) == hint_slug or hint_slug in slugify(nid):
            return npc
        if name and (name.lower() == hint.lower() or slugify(name) == hint_slug or hint_slug in slugify(name)):
            return npc
    return None


def set_active_interaction_target(
    session: Dict[str, Any],
    npc_id: Optional[str],
    *,
    kind: Optional[str] = "social",
) -> Dict[str, Any]:
    """Compatibility wrapper; owner API now lives in interaction_context."""
    if isinstance(kind, str) and kind.strip().lower() != "social":
        return update_interaction_context_for_non_social(session, kind)
    return set_social_target(session, npc_id)


def update_interaction_context_for_non_social(
    session: Dict[str, Any],
    kind: Optional[str],
) -> Dict[str, Any]:
    """Compatibility wrapper; owner API now lives in interaction_context."""
    return set_non_social_activity(session, kind)


def apply_interaction_implied_heuristics(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    text: Optional[str],
) -> Dict[str, Any]:
    """Compatibility wrapper for interaction-context owned implied-input handling."""
    return apply_turn_input_implied_context(session, world, scene_id, text)


def get_npc_dc_modifier(npc: Dict[str, Any], kind: str) -> int:
    """NPC-specific DC modifier from skill_check_modifier or per-kind override."""
    mod = 0
    m = npc.get("skill_check_modifier")
    if isinstance(m, (int, float)):
        mod += int(m)
    overrides = npc.get("skill_check_overrides") or {}
    if isinstance(overrides, dict) and kind in overrides:
        v = overrides[kind]
        if isinstance(v, (int, float)):
            mod += int(v)
    return mod


def _next_topic_to_reveal(
    npc: Dict[str, Any],
    runtime: Dict[str, Any],
    topic_hint: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return next unrevealed topic that matches hint (if any). Topic: {id, text, clue_id?, clue_text?}."""
    topics = npc.get("topics") or npc.get("knowledge") or []
    if not isinstance(topics, list):
        return None
    revealed = set(runtime.get("revealed_topics") or [])
    hint_slug = slugify(topic_hint) if topic_hint else None

    for t in topics:
        if not isinstance(t, dict):
            rec = {"id": str(t)[:40], "text": str(t)} if t else None
            if not rec:
                continue
        else:
            rec = t
        tid = str(rec.get("id") or "").strip()
        if not tid:
            tid = slugify(rec.get("text", ""))[:40] or "topic"
        if tid in revealed:
            continue
        if hint_slug and hint_slug not in slugify(tid) and hint_slug not in slugify(rec.get("text", "")):
            continue
        return {
            "id": tid,
            "text": str(rec.get("text") or rec.get("label") or "").strip() or "Unknown.",
            "clue_id": rec.get("clue_id") or rec.get("reveals_clue"),
            "clue_text": rec.get("clue_text"),
        }
    return None


def _infer_reply_expectation(
    action_type: str,
    *,
    prompt: str,
    raw_player_text: Optional[str],
    topic_revealed: bool,
    requires_check: bool,
) -> Tuple[bool, str]:
    """Infer whether the active NPC is expected to deliver a substantive reply now."""
    if requires_check:
        return False, "reaction"

    low = f"{raw_player_text or ''} {prompt or ''}".strip().lower()
    has_question_mark = "?" in low
    has_question_word = bool(re.search(r"\b(" + "|".join(_DIRECT_QUESTION_WORDS) + r")\b", low))
    has_direct_question = bool(has_question_mark or has_question_word)
    asks_name = any(tok in low for tok in _NAME_REQUEST_TOKENS)
    asks_destination = any(tok in low for tok in _DESTINATION_REQUEST_TOKENS)
    asks_explanation = any(tok in low for tok in _EXPLANATION_REQUEST_TOKENS)
    asks_terms = any(tok in low for tok in _TERMS_REQUEST_TOKENS)
    invites_continue = any(tok in low for tok in _LISTENING_INVITE_TOKENS)
    explicit_info_request = bool(asks_name or asks_destination or asks_explanation or asks_terms)

    if action_type in SOCIAL_MANEUVER_KINDS:
        return True, "reaction"

    if invites_continue:
        return True, "explanation"

    if action_type == "question" or has_direct_question or explicit_info_request:
        if not topic_revealed and (has_direct_question or explicit_info_request):
            return True, "refusal"
        if asks_explanation:
            return True, "explanation"
        return True, "answer"

    if action_type == "social_probe":
        if has_direct_question or explicit_info_request:
            if not topic_revealed:
                return True, "refusal"
            if asks_explanation:
                return True, "explanation"
            return True, "answer"
        return False, "reaction"

    return False, "reaction"


def _social_payload_with_reply_expectation(
    payload: Dict[str, Any],
    *,
    action_type: str,
    prompt: str,
    raw_player_text: Optional[str],
    topic_revealed: bool,
    requires_check: bool,
    debug_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    expected, reply_kind = _infer_reply_expectation(
        action_type,
        prompt=prompt,
        raw_player_text=raw_player_text,
        topic_revealed=topic_revealed,
        requires_check=requires_check,
    )
    out = dict(payload)
    out["npc_reply_expected"] = bool(expected)
    out["reply_kind"] = reply_kind
    if isinstance(debug_fields, dict) and debug_fields:
        out.update(debug_fields)
    return out


def _social_target_debug_fields(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    scene_envelope: Dict[str, Any],
    normalized_action: Dict[str, Any],
    auth: Dict[str, Any],
) -> Dict[str, Any]:
    na = normalized_action if isinstance(normalized_action, dict) else {}
    cand_raw = na.get("target_id") or na.get("targetEntityId")
    cand = str(cand_raw).strip() if cand_raw is not None and str(cand_raw).strip() else None
    ids = scene_addressable_actor_ids(
        world,
        scene_id,
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    out = {
        "target_source": auth.get("source"),
        "target_reason": auth.get("reason"),
        "target_candidate_id": cand,
        "target_candidate_valid": bool(cand and cand in ids),
    }
    grb = auth.get("generic_role_rebind")
    if isinstance(grb, dict):
        out["generic_role_rebind"] = grb
    return out


def apply_npc_runtime_deltas(
    session: Dict[str, Any],
    npc_id: str,
    kind: str,
    success: Optional[bool],
    turn_counter: int,
    deltas: Optional[Dict[str, int]] = None,
) -> None:
    """Apply attitude/trust/fear/suspicion deltas to NPC runtime. Mutates session."""
    rt = get_npc_runtime(session, npc_id)
    rt["last_interaction_turn"] = turn_counter

    if deltas:
        for key in ("attitude", "trust", "fear", "suspicion"):
            if key in deltas and isinstance(deltas[key], (int, float)):
                current = int(rt.get(key, 0) or 0)
                rt[key] = max(-5, min(5, current + int(deltas[key])))

    if success is True:
        if kind in ("persuade", "question", "social_probe", "barter"):
            rt["trust"] = min(5, int(rt.get("trust", 0) or 0) + 1)
        if kind == "intimidate":
            rt["fear"] = min(5, int(rt.get("fear", 0) or 0) + 1)
        if kind == "deceive":
            rt["suspicion"] = min(5, int(rt.get("suspicion", 0) or 0) + 1)
    elif success is False:
        if kind == "intimidate":
            rt["attitude"] = max(-5, int(rt.get("attitude", 0) or 0) - 1)


def resolve_social_action(
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    normalized_action: Dict[str, Any],
    raw_player_text: Optional[str] = None,
    character: Optional[Dict[str, Any]] = None,
    turn_counter: int = 0,
) -> Dict[str, Any]:
    """Produce a structured SocialEngineResult for the GM prompt. Deterministic, engine-first.

    Mutates session.npc_runtime (deltas, revealed_topics) when an NPC is found and resolved.

    Returns:
        kind, action_id, label, prompt, success, hint, social {npc_id, npc_name, skill_check?, topic_revealed?, ...}
    """
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()

    action_type = (normalized_action.get("type") or "social_probe").strip().lower()
    if action_type not in SOCIAL_KINDS:
        action_type = "social_probe"
    intent_class = social_intent_class(action_type)

    label = str(normalized_action.get("label") or "").strip() or "Social action"
    prompt = str(normalized_action.get("prompt") or raw_player_text or label).strip() or label
    action_id = str(normalized_action.get("id") or "").strip() or "social"
    target_id = normalized_action.get("target_id") or normalized_action.get("targetEntityId") or raw_player_text

    rebuild_active_scene_entities(session, world, scene_id, scene_envelope=scene_envelope)

    # Authoritative social target selection happens here. After this point, emission/validation may reject
    # output text, but may not null the selected target unless it is invalidated by scene scope.
    auth = resolve_authoritative_social_target(
        session,
        world,
        scene_id,
        player_text=raw_player_text,
        normalized_action=normalized_action,
        scene_envelope=scene_envelope,
        allow_first_roster_fallback=False,
    )
    dbg = _social_target_debug_fields(
        session, world, scene_id, scene_envelope, normalized_action, auth
    )

    if auth.get("offscene_target") and auth.get("npc_id"):
        known_target_id = str(auth.get("npc_id") or "").strip()
        known_target_name = str(auth.get("npc_name") or "").strip()
        hint = (
            f"{known_target_name or 'That person'} is no longer here to answer. "
            "Narrate that naturally from the current scene instead of attributing the reply to them."
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=False,
            hint=hint,
            social={
                "social_intent_class": intent_class,
                "npc_id": known_target_id or None,
                "npc_name": known_target_name or None,
                "target_resolved": False,
                "skill_check": None,
                "npc_reply_expected": False,
                "reply_kind": "reaction",
                "offscene_target": True,
                **dbg,
            },
            requires_check=False,
        )
        return result.to_dict()

    if not (auth.get("target_resolved") and auth.get("npc_id")):
        known_target = _find_world_npc_by_target(world, str(target_id or "")) if target_id else None
        known_target_id = str((known_target or {}).get("id") or "").strip()
        known_target_name = str((known_target or {}).get("name") or "").strip()
        known_target_loc = str((known_target or {}).get("location") or (known_target or {}).get("scene_id") or "").strip()
        is_offscene_target = bool(known_target_id and known_target_loc and known_target_loc != scene_id)
        if is_offscene_target:
            hint = (
                f"{known_target_name or 'That person'} is no longer here to answer. "
                "Narrate that naturally from the current scene instead of attributing the reply to them."
            )
        else:
            hint = "No matching NPC found in this scene. Narrate that the player's social attempt has no clear target or the intended person is not present."
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=False,
            hint=hint,
            social={
                "social_intent_class": intent_class,
                "npc_id": known_target_id or None,
                "npc_name": known_target_name or None,
                "target_resolved": False,
                "skill_check": None,
                "npc_reply_expected": False,
                "reply_kind": "reaction",
                "offscene_target": is_offscene_target,
                **dbg,
            },
            requires_check=False,
        )
        return result.to_dict()

    npc_id = str(auth.get("npc_id") or "").strip()
    npc = npc_dict_by_id(world, npc_id)
    if npc is None:
        roster = canonical_scene_addressable_roster(
            world,
            scene_id,
            scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
            session=session if isinstance(session, dict) else None,
        )
        npc = next((x for x in roster if isinstance(x, dict) and str(x.get("id") or "").strip() == npc_id), None)
    if not isinstance(npc, dict):
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=False,
            hint="No matching NPC found in this scene. Narrate that the player's social attempt has no clear target or the intended person is not present.",
            social={
                "social_intent_class": intent_class,
                "npc_id": None,
                "npc_name": None,
                "target_resolved": False,
                "skill_check": None,
                "npc_reply_expected": False,
                "reply_kind": "reaction",
                "offscene_target": False,
                **dbg,
            },
            requires_check=False,
        )
        return result.to_dict()

    npc_name = str(npc.get("name") or auth.get("npc_name") or "the NPC").strip()

    runtime = get_npc_runtime(session, npc_id)
    set_active_interaction_target(session, npc_id, kind="social")

    # Initialize from NPC baseline
    base_attitude = npc.get("disposition") or npc.get("attitude") or "neutral"
    if isinstance(base_attitude, str):
        attitude_map = {"friendly": 2, "helpful": 1, "neutral": 0, "unfriendly": -1, "hostile": -2}
        runtime.setdefault("attitude", attitude_map.get(base_attitude.lower(), 0))
    runtime.setdefault("trust", 0)
    runtime.setdefault("fear", 0)
    runtime.setdefault("suspicion", 0)
    runtime.setdefault("known_topics", [])
    runtime.setdefault("revealed_topics", [])

    # Question/social_probe: no skill check by default; may reveal topic
    if action_type in ("question", "social_probe"):
        # Only use topic hint when explicitly provided; otherwise reveal first available topic
        topic_hint = normalized_action.get("topic") if normalized_action.get("topic") else None
        topic_rec = _next_topic_to_reveal(npc, runtime, topic_hint)

        if topic_rec:
            revealed_ids = runtime.get("revealed_topics") or []
            if topic_rec["id"] not in revealed_ids:
                revealed_ids.append(topic_rec["id"])
                runtime["revealed_topics"] = revealed_ids

            clue_text = topic_rec.get("clue_text") or topic_rec.get("text")
            clue_id = topic_rec.get("clue_id")
            discovered = [clue_text] if clue_text else []

            apply_npc_runtime_deltas(session, npc_id, action_type, True, turn_counter)
            social_payload = _social_payload_with_reply_expectation(
                {
                    "social_intent_class": intent_class,
                    "npc_id": npc_id,
                    "npc_name": npc_name,
                    "target_resolved": True,
                    "topic_revealed": topic_rec,
                    "skill_check": None,
                },
                action_type=action_type,
                prompt=prompt,
                raw_player_text=raw_player_text,
                topic_revealed=True,
                requires_check=False,
                debug_fields=dbg,
            )

            result = SocialEngineResult(
                kind=action_type,
                action_id=action_id,
                label=label,
                prompt=prompt,
                success=True,
                clue_id=clue_id,
                discovered_clues=discovered,
                state_changes={"topic_revealed": True, "npc_id": npc_id},
                hint=f"Player questioned {npc_name} and learned: {topic_rec['text'][:100]}. Narrate the revelation.",
                social=social_payload,
                requires_check=False,
            )
            return result.to_dict()

        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
                "topic_revealed": None,
                "skill_check": None,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=False,
            requires_check=False,
            debug_fields=dbg,
        )
        fallback_hint = (
            f"Player spoke with {npc_name}. No new information was revealed. "
            "Narrate a substantive in-turn response (answer, refusal, evasion, or inability), not dead-air stalling."
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=fallback_hint,
            social=social_payload,
            requires_check=False,
        )
        return result.to_dict()

    # Skill-check kinds: persuade, intimidate, deceive, barter, recruit
    skill_entry = SOCIAL_SKILL_MAP.get(action_type)
    if not skill_entry:
        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=False,
            requires_check=False,
            debug_fields=dbg,
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=f"Player attempted a social action toward {npc_name}. Narrate the outcome.",
            social=social_payload,
            requires_check=False,
        )
        return result.to_dict()

    skill_id, dc_mod = skill_entry
    effective_skill = _resolve_skill_for_kind(action_type, character or {})
    if not effective_skill:
        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=False,
            requires_check=False,
            debug_fields=dbg,
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=f"Player attempted {action_type} toward {npc_name}. Narrate the outcome.",
            social=social_payload,
            requires_check=False,
        )
        return result.to_dict()

    # Skill check authority: engine decides when to roll
    ctx = {
        "engine": "social",
        "action": normalized_action,
        "npc": npc,
        "session": session,
        "turn_counter": turn_counter,
        "scene_id": scene_id,
        "action_id": action_id,
        "character_id": (character or {}).get("id", ""),
        "seed_parts": [turn_counter, scene_id, action_id, npc_id, "social"],
    }
    decision = should_trigger_check(normalized_action, ctx)
    if not decision.get("requires_check") or decision.get("skill") is None or decision.get("difficulty") is None:
        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=False,
            requires_check=False,
            debug_fields=dbg,
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=f"Player attempted {action_type} toward {npc_name}. Narrate the outcome.",
            social=social_payload,
            requires_check=False,
        )
        return result.to_dict()

    effective_skill = _resolve_skill_for_kind(action_type, character or {}) or decision["skill"]
    dc = int(decision["difficulty"])
    roll_prompt = (
        f"Roll {effective_skill.title()} (DC {dc}) to resolve this {action_type} attempt with {npc_name}."
    )
    check_request = make_check_request(
        requires_check=True,
        check_type=effective_skill,
        skill=effective_skill,
        difficulty=dc,
        reason=str(decision.get("reason") or f"{action_type}_attempt"),
        player_prompt=roll_prompt,
    )

    apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
    social_payload = _social_payload_with_reply_expectation(
        {
            "social_intent_class": intent_class,
            "npc_id": npc_id,
            "npc_name": npc_name,
            "target_resolved": True,
            "skill_check": None,
            "check_request": check_request,
        },
        action_type=action_type,
        prompt=prompt,
        raw_player_text=raw_player_text,
        topic_revealed=False,
        requires_check=True,
        debug_fields=dbg,
    )

    result = SocialEngineResult(
        kind=action_type,
        action_id=action_id,
        label=label,
        prompt=prompt,
        success=None,
        clue_id=None,
        discovered_clues=[],
        state_changes={"npc_id": npc_id},
        hint=roll_prompt,
        social=social_payload,
        requires_check=True,
        check_request=check_request,
    )
    return result.to_dict()
