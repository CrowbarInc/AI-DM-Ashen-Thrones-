"""Social-commitment break: when to drop continuity for explicit non-social redirection.

Ownership: ``should_break_social_commitment_for_input`` and the engine hook that records a
break in session metadata. Uses dialogue cue helpers from ``game.interaction_context`` via
lazy imports to avoid cycles; **routing classifiers** live in :mod:`game.interaction_routing`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from game.utils import slugify

# Mirror game.social.SOCIAL_KINDS — avoid importing social (circular).
_ENGINE_SOCIAL_ACTION_TYPES = frozenset(
    {
        "question",
        "social_probe",
        "persuade",
        "intimidate",
        "deceive",
        "barter",
        "recruit",
    }
)

_EXPLICIT_NON_SOCIAL_REDIRECT_RES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(?:stride|striding|strides)\b.*\b(?:toward|towards|to|over\s+to|directly)\b",
            re.IGNORECASE,
        ),
        "stride_toward",
    ),
    (
        re.compile(
            r"\bfollow(?:s|ing|ed)?\s+the\s+(?:path|road|track|route)\b",
            re.IGNORECASE,
        ),
        "follow_path",
    ),
    (
        re.compile(
            r"\b(?:make|making|makes)\s+(?:my|our)\s+way\b",
            re.IGNORECASE,
        ),
        "make_way",
    ),
    (
        re.compile(
            r"\bprioritiz(?:e|es|ing)\b.+\bover\b",
            re.IGNORECASE,
        ),
        "prioritize_over",
    ),
    (
        re.compile(
            r"\bswitch(?:es|ing)?\s+(?:tracks|focus|gears|course)\b",
            re.IGNORECASE,
        ),
        "switch_tracks",
    ),
    (
        re.compile(
            r"\bchange(?:s|ing)?\s+course\b",
            re.IGNORECASE,
        ),
        "change_course",
    ),
)


def _social_commitment_is_active(session: Dict[str, Any]) -> bool:
    """True when a prior turn left an authoritative social interlocutor / target to respect or break."""
    from game.interaction_context import _clean_string, _scene_state, inspect

    if not isinstance(session, dict):
        return False
    ctx = inspect(session)
    mode = str(ctx.get("interaction_mode") or "").strip().lower()
    tid = _clean_string(ctx.get("active_interaction_target_id"))
    st = _scene_state(session)
    cur = _clean_string(st.get("current_interlocutor"))
    return mode == "social" and bool(tid or cur)


def _collect_normalized_target_hints(normalized_action: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    if not isinstance(normalized_action, dict):
        return out
    for key in (
        "target_id",
        "targetEntityId",
        "target_entity_id",
        "targetSceneId",
        "target_scene_id",
        "label",
        "prompt",
    ):
        raw = normalized_action.get(key)
        if isinstance(raw, str) and raw.strip():
            out.append(raw.strip())
    meta = normalized_action.get("metadata")
    if isinstance(meta, dict):
        for key in ("prompt", "target_npc_id", "target_npc_name"):
            raw = meta.get(key)
            if isinstance(raw, str) and raw.strip():
                out.append(raw.strip())
    return list(dict.fromkeys(out))


def _target_hint_refers_to_actor(
    target_hint: Optional[str],
    actor_id: str,
    world: Optional[Dict[str, Any]],
) -> bool:
    """Conservative: *target_hint* names *actor_id* (id, display name, or alias substring)."""
    from game.interaction_context import _clean_string

    if not target_hint or not actor_id:
        return False
    ah = str(actor_id).strip().lower()
    h = str(target_hint).strip().lower()
    if not h:
        return False
    if ah == h or slugify(ah) == slugify(h):
        return True
    if re.search(r"\b(you|your|yourself)\b", h) and len(h) <= 80:
        return True
    w = world if isinstance(world, dict) else {}
    for npc in w.get("npcs") or []:
        if not isinstance(npc, dict):
            continue
        nid = _clean_string(npc.get("id"))
        if nid != actor_id:
            continue
        nm = str(npc.get("name") or "").strip().lower()
        if nm and (nm in h or h in nm):
            return True
        for al in npc.get("aliases") or []:
            if isinstance(al, str) and al.strip():
                als = al.strip().lower()
                if als in h or h in als:
                    return True
        break
    return False


def _explicit_non_social_redirect_in_text(low: str) -> tuple[bool, str]:
    for rx, label in _EXPLICIT_NON_SOCIAL_REDIRECT_RES:
        if rx.search(low):
            return True, label
    return False, ""


def _line_asks_npc_second_person(low: str) -> bool:
    """Match intent_parser second-person adjudication exclusions for dialogue follow-ups."""
    if not low or "?" not in low:
        return False
    if re.search(r"\b(?:can|could|would|will)\s+you\b", low):
        return True
    if re.search(r"\b(?:do|does|did)\s+you\s+know\b", low):
        return True
    if re.search(r"\bhave\s+you\s+seen\b", low):
        return True
    return False


def _text_protected_social_followup(low: str, merged_text: str) -> bool:
    """Direct questions / info-seeking without world-action blockers — keep commitment."""
    from game.interaction_context import _information_seeking_dialogue_line, _line_blocks_dialogue_addressing

    if _information_seeking_dialogue_line(low) and not _line_blocks_dialogue_addressing(low):
        return True
    if "?" in merged_text and _line_asks_npc_second_person(low):
        return True
    return False


def should_break_social_commitment_for_input(
    session: Dict[str, Any],
    raw_text: Optional[str],
    normalized_action: Optional[Dict[str, Any]],
    *,
    world: Optional[Dict[str, Any]] = None,
    scene_envelope: Optional[Dict[str, Any]] = None,
) -> tuple[bool, str]:
    """Return (True, reason_code) when this turn explicitly redirects away from the current interlocutor.

    Conservative: prefers normalized engine actions and explicit phrasing; avoids breaking on
    follow-up questions or quoted-only social lines.
    """
    from game.interaction_context import _clean_string, _line_blocks_dialogue_addressing, _scene_state, inspect

    if not isinstance(session, dict) or not _social_commitment_is_active(session):
        return False, ""
    ctx = inspect(session)
    interlocutor = _clean_string(ctx.get("active_interaction_target_id")) or _clean_string(
        _scene_state(session).get("current_interlocutor")
    )
    if not interlocutor:
        return False, ""

    text = str(raw_text or "").strip()
    low = text.lower()
    if not low:
        return False, ""

    merged_for_protection = text
    if '"' in text:
        inner = " ".join(re.findall(r'"([^"\n]{1,240})"', text))
        if inner.strip():
            merged_for_protection = inner.strip()

    if _text_protected_social_followup(low, merged_for_protection):
        return False, ""

    norm = normalized_action if isinstance(normalized_action, dict) else None
    eff_type = str((norm or {}).get("type") or "").strip().lower()

    from game.scene_actions import infer_action_type_from_label

    if eff_type == "custom" and norm:
        lab = str(norm.get("label") or norm.get("prompt") or "")
        inferred = infer_action_type_from_label(lab).strip().lower()
        if inferred and inferred != "custom":
            eff_type = inferred

    if eff_type in _ENGINE_SOCIAL_ACTION_TYPES:
        return False, ""

    if norm and eff_type in ("scene_opening", "custom"):
        hints = _collect_normalized_target_hints(norm)
        if hints:
            if any(_target_hint_refers_to_actor(h, interlocutor, world) for h in hints):
                return False, ""
            if _explicit_non_social_redirect_in_text(low)[0] or _line_blocks_dialogue_addressing(low):
                return True, "explicit_non_social_redirect"
        elif _explicit_non_social_redirect_in_text(low)[0] or _line_blocks_dialogue_addressing(low):
            return True, "explicit_non_social_redirect"
        return False, ""

    if eff_type in ("travel", "scene_transition", "attack", "combat"):
        return True, "normalized_non_social_travel_or_combat"

    if eff_type in ("observe", "investigate", "interact"):
        hints = _collect_normalized_target_hints(norm) if norm else []
        if hints:
            if any(_target_hint_refers_to_actor(h, interlocutor, world) for h in hints):
                return False, ""
            return True, "normalized_non_social_target_not_interlocutor"
        if _line_blocks_dialogue_addressing(low) or _explicit_non_social_redirect_in_text(low)[0]:
            return True, "explicit_non_social_redirect"
        return False, ""

    if norm and eff_type and eff_type not in ("custom", "scene_opening"):
        return False, ""

    if _line_blocks_dialogue_addressing(low):
        return True, "dialogue_blocker_world_action"

    ex_ok, ex_label = _explicit_non_social_redirect_in_text(low)
    if ex_ok:
        return True, f"explicit_wording:{ex_label}"

    if scene_envelope and isinstance(scene_envelope, dict):
        from game.intent_parser import parse_freeform_to_action

        act = parse_freeform_to_action(text, scene_envelope)
        if isinstance(act, dict):
            ft = str(act.get("type") or "").strip().lower()
            if ft in ("travel", "scene_transition"):
                return True, "freeform_parse_travel"
            if ft in ("observe", "investigate"):
                tid = act.get("target_id") or act.get("targetEntityId")
                if isinstance(tid, str) and tid.strip():
                    if _target_hint_refers_to_actor(tid.strip(), interlocutor, world):
                        return False, ""
                return True, f"freeform_parse:{ft}"
            if ft == "interact":
                tid = act.get("target_id") or act.get("targetEntityId")
                if isinstance(tid, str) and tid.strip():
                    if _target_hint_refers_to_actor(tid.strip(), interlocutor, world):
                        return False, ""
                    return True, "freeform_parse:interact_other"

    return False, ""


def _infer_activity_kind_for_commitment_break(
    normalized_action: Optional[Dict[str, Any]],
    raw_text: Optional[str],
) -> str:
    from game.interaction_context import NON_SOCIAL_ACTIVITY_KINDS

    norm = normalized_action if isinstance(normalized_action, dict) else {}
    t = str(norm.get("type") or "").strip().lower()
    if t in NON_SOCIAL_ACTIVITY_KINDS:
        return t
    from game.scene_actions import infer_action_type_from_label

    lab = str(norm.get("label") or norm.get("prompt") or raw_text or "")
    inferred = infer_action_type_from_label(lab).strip().lower()
    if inferred in NON_SOCIAL_ACTIVITY_KINDS:
        return inferred
    low = str(raw_text or "").lower()
    if any(x in low for x in ("go ", "head ", "travel", "walk ", "enter ", "leave ", "follow the path")):
        return "travel"
    return "investigate"


def apply_explicit_non_social_commitment_break(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    player_text: Optional[str],
    normalized_action: Optional[Dict[str, Any]],
    *,
    scene_envelope: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Clear social continuity when the player explicitly redirects to non-social action. Inspectable metadata only."""
    from game.interaction_context import set_non_social_activity

    sid = str(scene_id or "").strip()
    env = scene_envelope
    if env is None and sid:
        from game.storage import load_scene

        env = load_scene(sid)

    should, reason = should_break_social_commitment_for_input(
        session,
        player_text,
        normalized_action,
        world=world,
        scene_envelope=env if isinstance(env, dict) else None,
    )
    if not should:
        return {}
    kind = _infer_activity_kind_for_commitment_break(normalized_action, player_text)
    set_non_social_activity(session, kind)
    return {
        "commitment_broken": True,
        "break_reason": reason or "explicit_non_social_redirect",
        "commitment_break_activity_kind": kind,
    }
