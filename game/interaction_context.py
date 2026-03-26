"""Authoritative interaction-context mutation API.

This module is the single owner for interaction-context runtime mutations.
Callers may read context elsewhere, but all writes should route through these
functions so behavior remains deterministic and inspectable.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from game.utils import slugify

from game.storage import get_interaction_context


SOCIAL_INTERACTION_KINDS = frozenset(
    {
        "social",
        "question",
        "social_probe",
        "persuade",
        "intimidate",
        "deceive",
        "barter",
        "recruit",
    }
)

NON_SOCIAL_ACTIVITY_KINDS = frozenset(
    {
        "observe",
        "investigate",
        "interact",
        "travel",
        "scene_transition",
        "attack",
        "combat",
    }
)

IMPLIED_HINT_LOWERED_VOICE = "lowered_voice"
IMPLIED_HINT_SEATED_WITH_TARGET = "seated_with_target"

INTERACTION_MODES = frozenset({"none", "social", "activity"})
ENGAGEMENT_LEVELS = frozenset({"none", "engaged", "focused"})
CONVERSATION_PRIVACY_VALUES = frozenset({"public", "lowered_voice", "private"})
FOCUSED_ACTIVITY_KINDS = frozenset({"observe", "investigate", "interact", "travel", "scene_transition"})
_LOWERED_VOICE_TOKENS = (
    "lower my voice",
    "lowered my voice",
    "keep my voice low",
    "speak quietly",
    "say quietly",
    "quietly",
    "whisper",
)
_SIT_WITH_TOKENS = (
    "sit with",
    "sit down with",
    "take a seat with",
    "sit beside",
    "sit next to",
)
_COURTESY_MOVE_TOKENS = ("bring", "carry", "place", "set down", "hand")
_COURTESY_ITEM_TOKENS = ("drink", "ale", "beer", "wine", "mug", "cup", "glass", "item")
_COURTESY_TARGET_PREPOSITIONS = (" to ", " for ", " beside ", " next to ", " in front of ")


def _clean_string(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    clean = value.strip()
    return clean or None


SCENE_ADDRESSABLE_KINDS = frozenset({"npc", "scene_actor", "crowd_actor"})


def _scene_npcs(world: Dict[str, Any], scene_id: str) -> list[Dict[str, Any]]:
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return []
    out: list[Dict[str, Any]] = []
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = _clean_string(npc.get("id"))
        if not nid:
            continue
        loc = _clean_string(npc.get("location")) or _clean_string(npc.get("scene_id"))
        if loc != scene_id:
            continue
        out.append(npc)
    return out


def effective_in_scene_npc_roster(world: Dict[str, Any] | None, scene_id: str) -> list[Dict[str, Any]]:
    """NPC dicts in ``scene_id`` for dialogue binding, active-entity rebuild, and strict-social routing.

    Uses persisted ``world["npcs"]`` when that list is non-empty; otherwise falls back to
    :func:`game.defaults.default_world` for the same location filter. Keeping this roster
    identical across interaction binding and strict-social emission prevents one subsystem
    from seeing an empty scene (no bindable target) while the other still resolves vocative
    lines—``active_interaction_target_id`` and speaker authority must agree.
    """
    sid = _clean_string(scene_id) or ""
    if not sid:
        return []
    w = world if isinstance(world, dict) else {}
    roster = _scene_npcs(w, sid)
    if roster:
        return roster
    # Persisted empty NPC list: do not inject default-world NPCs (scene addressables / active_entities own scope).
    npcs_key = w.get("npcs")
    if isinstance(npcs_key, list) and len(npcs_key) == 0:
        return []
    from game.defaults import default_world

    return _scene_npcs(default_world(), sid)


def _all_world_npc_ids(world: Dict[str, Any]) -> List[str]:
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        npcs = []
    if not npcs:
        from game.defaults import default_world

        npcs = default_world().get("npcs") or []
    if not isinstance(npcs, list):
        return []
    out: List[str] = []
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = _clean_string(npc.get("id"))
        if not nid or nid in out:
            continue
        out.append(nid)
    return out


def _scene_authored_entity_ids(scene_envelope: Dict[str, Any] | None) -> List[str]:
    if not isinstance(scene_envelope, dict):
        return []
    authored: List[str] = []

    def _consume_list(raw: Any) -> None:
        if not isinstance(raw, list):
            return
        for item in raw:
            ent_id = ""
            if isinstance(item, str):
                ent_id = item.strip()
            elif isinstance(item, dict):
                ent_id = str(item.get("id") or "").strip()
            if ent_id and ent_id not in authored:
                authored.append(ent_id)

    scene = scene_envelope.get("scene")
    if isinstance(scene, dict):
        for key in ("active_entities", "entities", "npcs"):
            _consume_list(scene.get(key))

    top_state = scene_envelope.get("scene_state")
    if isinstance(top_state, dict):
        _consume_list(top_state.get("active_entities"))
        _consume_list(top_state.get("entities"))

    return authored


def _normalize_scene_addressable_actor(raw: Dict[str, Any], scene_id: str) -> Optional[Dict[str, Any]]:
    """Normalize scene JSON into the canonical addressable-actor shape (lightweight roster row)."""
    if not isinstance(raw, dict):
        return None
    eid = _clean_string(raw.get("id"))
    if not eid:
        return None
    sid = _clean_string(raw.get("scene_id")) or _clean_string(scene_id) or ""
    name = _clean_string(raw.get("name")) or eid.replace("_", " ").replace("-", " ").title()
    kind = str(raw.get("kind") or "scene_actor").strip().lower()
    if kind not in SCENE_ADDRESSABLE_KINDS:
        kind = "scene_actor"
    roles_in: Any = raw.get("address_roles")
    roles: List[str] = []
    if isinstance(roles_in, list):
        for r in roles_in:
            if isinstance(r, str) and r.strip():
                roles.append(r.strip().lower())
    aliases_in: Any = raw.get("aliases")
    aliases: List[str] = []
    if isinstance(aliases_in, list):
        for a in aliases_in:
            if isinstance(a, str) and a.strip():
                aliases.append(a.strip())
    addressable = raw.get("addressable")
    if addressable is None:
        addressable = True
    priority_raw = raw.get("address_priority")
    try:
        address_priority = int(priority_raw) if priority_raw is not None else 100
    except (TypeError, ValueError):
        address_priority = 100
    row: Dict[str, Any] = {
        "id": eid,
        "name": name,
        "scene_id": sid,
        "address_roles": roles,
        "aliases": aliases,
        "kind": kind,
        "addressable": bool(addressable),
        "address_priority": address_priority,
    }
    if "role" in raw and isinstance(raw.get("role"), str) and raw["role"].strip():
        row["role"] = raw["role"].strip()
    if "topics" in raw:
        row["topics"] = raw["topics"]
    if "disposition" in raw:
        row["disposition"] = raw["disposition"]
    return row


def scene_addressables_from_envelope(scene_envelope: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """Return normalized addressable actors from ``scene.addressables``."""
    if not isinstance(scene_envelope, dict):
        return []
    scene = scene_envelope.get("scene")
    if not isinstance(scene, dict):
        return []
    raw = scene.get("addressables")
    if not isinstance(raw, list):
        return []
    sid = _clean_string(scene.get("id")) or ""
    out: List[Dict[str, Any]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        norm = _normalize_scene_addressable_actor(item, sid)
        if not norm or not norm.get("addressable", True):
            continue
        if norm.get("address_priority", 100) == 100 and "address_priority" not in item:
            norm["address_priority"] = 100 + i
        out.append(norm)
    return out


def _scene_state(session: Dict[str, Any]) -> Dict[str, Any]:
    state = session.get("scene_state")
    if not isinstance(state, dict):
        state = {}
        session["scene_state"] = state
    if not isinstance(state.get("active_entities"), list):
        state["active_entities"] = []
    if not isinstance(state.get("entity_presence"), dict):
        state["entity_presence"] = {}
    if "active_scene_id" not in state:
        state["active_scene_id"] = str(session.get("active_scene_id") or "").strip()
    if "current_interlocutor" not in state:
        state["current_interlocutor"] = None
    return state


def is_entity_active(session: Dict[str, Any], entity_id: Optional[str]) -> bool:
    eid = _clean_string(entity_id)
    if not eid:
        return False
    state = _scene_state(session)
    active_ids = state.get("active_entities")
    if not isinstance(active_ids, list):
        return False
    return eid in {str(x).strip() for x in active_ids if isinstance(x, str)}


def entity_presence_state(session: Dict[str, Any], entity_id: Optional[str]) -> str:
    eid = _clean_string(entity_id)
    if not eid:
        return "unknown"
    state = _scene_state(session)
    presence = state.get("entity_presence")
    if not isinstance(presence, dict):
        return "unknown"
    value = str(presence.get(eid) or "").strip().lower()
    return value if value in {"active", "nearby", "offscene", "unknown"} else "unknown"


def assert_valid_speaker(candidate: Optional[str], session: Dict[str, Any]) -> bool:
    return is_entity_active(session, candidate)


def rebuild_active_scene_entities(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    *,
    scene_envelope: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Rebuild explicit active-scene entity scope and invalidate stale interlocutors."""
    sid = _clean_string(scene_id) or ""
    state = _scene_state(session)
    active_ids: List[str] = []
    for npc in effective_in_scene_npc_roster(world, sid):
        nid = _clean_string(npc.get("id"))
        if nid and nid not in active_ids:
            active_ids.append(nid)

    # Scene-authored entities may be present even when world location is not explicit.
    for ent_id in _scene_authored_entity_ids(scene_envelope):
        if ent_id not in active_ids:
            active_ids.append(ent_id)

    presence: Dict[str, str] = {}
    active_set = set(active_ids)
    for npc_id in _all_world_npc_ids(world):
        if npc_id in active_set:
            presence[npc_id] = "active"
        else:
            presence[npc_id] = "offscene"

    state["active_scene_id"] = sid
    state["active_entities"] = active_ids
    state["entity_presence"] = presence

    ctx = inspect(session)
    current_target = _clean_string(ctx.get("active_interaction_target_id"))
    if current_target and current_target not in active_set:
        # Target left scene scope; clear social continuity so off-scene NPCs cannot answer.
        clear_for_scene_change(session)
        current_target = None

    state["current_interlocutor"] = current_target if current_target in active_set else None
    return state


def _extract_target_from_text(text: str, world: Dict[str, Any], scene_id: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    text_slug = slugify(text)
    if not text_slug:
        return None
    for npc in effective_in_scene_npc_roster(world, scene_id):
        npc_id = _clean_string(npc.get("id")) or ""
        npc_name = _clean_string(npc.get("name")) or ""
        npc_id_slug = slugify(npc_id)
        npc_name_slug = slugify(npc_name)
        if npc_id_slug and npc_id_slug in text_slug:
            return npc_id
        if npc_name_slug and npc_name_slug in text_slug:
            return npc_id
    return None


def _normalize_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize context shape and constrained literals in place."""
    target_id = _clean_string(ctx.get("active_interaction_target_id"))
    kind_raw = _clean_string(ctx.get("active_interaction_kind"))
    kind = kind_raw.lower() if kind_raw else None
    if kind and kind not in SOCIAL_INTERACTION_KINDS and kind not in NON_SOCIAL_ACTIVITY_KINDS:
        kind = None

    privacy_raw = _clean_string(ctx.get("conversation_privacy"))
    privacy = privacy_raw.lower() if privacy_raw else None
    if privacy and privacy not in CONVERSATION_PRIVACY_VALUES:
        privacy = None

    position = _clean_string(ctx.get("player_position_context"))

    mode_raw = _clean_string(ctx.get("interaction_mode"))
    mode = mode_raw.lower() if mode_raw else None
    if mode and mode not in INTERACTION_MODES:
        mode = None

    engagement_raw = _clean_string(ctx.get("engagement_level"))
    engagement = engagement_raw.lower() if engagement_raw else None
    if engagement and engagement not in ENGAGEMENT_LEVELS:
        engagement = None

    # Derive missing mode from kind for backward-compatible sessions.
    if mode is None:
        if kind in SOCIAL_INTERACTION_KINDS:
            mode = "social"
        elif kind in NON_SOCIAL_ACTIVITY_KINDS:
            mode = "activity"
        else:
            mode = "none"

    # Derive missing engagement from mode/kind for backward-compatible sessions.
    if engagement is None:
        if mode == "social":
            engagement = "engaged"
        elif mode == "activity":
            engagement = "focused" if kind in FOCUSED_ACTIVITY_KINDS else "engaged"
        else:
            engagement = "none"

    ctx["active_interaction_target_id"] = target_id
    ctx["active_interaction_kind"] = kind
    ctx["interaction_mode"] = mode
    ctx["engagement_level"] = engagement
    ctx["conversation_privacy"] = privacy
    ctx["player_position_context"] = position
    return ctx


def inspect(session: Dict[str, Any]) -> Dict[str, Any]:
    """Return normalized, mutable interaction context."""
    return _normalize_context(get_interaction_context(session))


def set_interaction_mode(session: Dict[str, Any], mode: Optional[str]) -> Dict[str, Any]:
    """Set interaction mode to one of: none, social, activity."""
    ctx = inspect(session)
    clean_mode = str(mode).strip().lower() if isinstance(mode, str) else "none"
    if clean_mode not in INTERACTION_MODES:
        clean_mode = "none"
    ctx["interaction_mode"] = clean_mode
    if clean_mode == "none" and ctx.get("engagement_level") != "none":
        ctx["engagement_level"] = "none"
    return _normalize_context(ctx)


def set_engagement_level(session: Dict[str, Any], level: Optional[str]) -> Dict[str, Any]:
    """Set engagement level to one of: none, engaged, focused."""
    ctx = inspect(session)
    clean_level = str(level).strip().lower() if isinstance(level, str) else "none"
    if clean_level not in ENGAGEMENT_LEVELS:
        clean_level = "none"
    ctx["engagement_level"] = clean_level
    return _normalize_context(ctx)


def set_social_target(session: Dict[str, Any], target_id: Optional[str]) -> Dict[str, Any]:
    """Set or clear the active social target; marks interaction kind as social."""
    ctx = inspect(session)
    ctx["active_interaction_target_id"] = _clean_string(target_id)
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"
    return _normalize_context(ctx)


def set_privacy(session: Dict[str, Any], privacy: Optional[str]) -> Dict[str, Any]:
    """Set conversation privacy hint; pass None to clear."""
    ctx = inspect(session)
    clean_privacy = str(privacy).strip().lower() if isinstance(privacy, str) else ""
    ctx["conversation_privacy"] = clean_privacy if clean_privacy in CONVERSATION_PRIVACY_VALUES else None
    return _normalize_context(ctx)


def set_position_context(session: Dict[str, Any], position_context: Optional[str]) -> Dict[str, Any]:
    """Set or clear player position context."""
    ctx = inspect(session)
    ctx["player_position_context"] = _clean_string(position_context)
    return _normalize_context(ctx)


def clear_for_scene_change(session: Dict[str, Any]) -> Dict[str, Any]:
    """Clear all interaction continuity fields during scene transitions."""
    ctx = inspect(session)
    ctx["active_interaction_target_id"] = None
    ctx["active_interaction_kind"] = None
    ctx["interaction_mode"] = "none"
    ctx["engagement_level"] = "none"
    ctx["conversation_privacy"] = None
    ctx["player_position_context"] = None
    state = _scene_state(session)
    state["current_interlocutor"] = None
    return _normalize_context(ctx)


def set_non_social_activity(session: Dict[str, Any], kind: Optional[str]) -> Dict[str, Any]:
    """Switch context to a deterministic non-social activity kind.

    Unknown kinds are ignored to avoid speculative state mutation.
    """
    ctx = inspect(session)
    clean_kind = str(kind).strip().lower() if isinstance(kind, str) else ""
    if clean_kind not in NON_SOCIAL_ACTIVITY_KINDS:
        return ctx
    ctx["active_interaction_target_id"] = None
    ctx["active_interaction_kind"] = clean_kind
    ctx["interaction_mode"] = "activity"
    ctx["engagement_level"] = "focused" if clean_kind in FOCUSED_ACTIVITY_KINDS else "engaged"
    ctx["conversation_privacy"] = None
    ctx["player_position_context"] = None
    return _normalize_context(ctx)


def update_after_resolved_action(
    session: Dict[str, Any],
    kind: Optional[str],
    *,
    preserve_continuity: bool = False,
) -> Dict[str, Any]:
    """Apply deterministic continuity changes after engine resolution.

    Rules:
    - social kinds preserve social continuity and mark engagement as active.
    - non-social kinds clear active target unless continuity is explicitly preserved.
    - unknown kinds are ignored.
    """
    clean_kind = str(kind).strip().lower() if isinstance(kind, str) else ""
    ctx = inspect(session)
    if clean_kind in SOCIAL_INTERACTION_KINDS:
        if clean_kind != "social":
            ctx["active_interaction_kind"] = "social"
        ctx["interaction_mode"] = "social"
        if ctx.get("engagement_level") == "none":
            ctx["engagement_level"] = "engaged"
        return _normalize_context(ctx)
    if preserve_continuity:
        return ctx
    return set_non_social_activity(session, clean_kind)


def apply_implied_hint(
    session: Dict[str, Any],
    hint: str,
    *,
    target_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply one supported implied continuity hint.

    Supported hints:
    - lowered_voice
    - seated_with_target
    """
    ctx = inspect(session)
    clean_hint = str(hint).strip().lower()
    clean_target = str(target_id).strip() if isinstance(target_id, str) else ""

    if clean_hint == IMPLIED_HINT_LOWERED_VOICE:
        set_privacy(session, IMPLIED_HINT_LOWERED_VOICE)
        if clean_target:
            set_social_target(session, clean_target)
        return ctx

    if clean_hint == IMPLIED_HINT_SEATED_WITH_TARGET:
        set_position_context(session, IMPLIED_HINT_SEATED_WITH_TARGET)
        if clean_target:
            set_social_target(session, clean_target)
        return ctx

    return ctx


def apply_turn_input_implied_context(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    text: Optional[str],
) -> Dict[str, Any]:
    """Apply narrow implied-action continuity from raw player input.

    Scope is intentionally conservative and deterministic. This helper may only
    adjust interaction continuity fields; it must not invent targets, resolve
    mechanics, or create world outcomes.
    """
    if not isinstance(text, str):
        return {"applied": False, "cases": [], "target_id": None}
    low = text.lower().strip()
    if not low:
        return {"applied": False, "cases": [], "target_id": None}

    ctx = inspect(session)
    target_id = _extract_target_from_text(low, world, scene_id)
    active_target_id = _clean_string(ctx.get("active_interaction_target_id"))
    if target_id is None and active_target_id:
        target_id = active_target_id

    applied_cases: list[str] = []

    if any(token in low for token in _LOWERED_VOICE_TOKENS):
        apply_implied_hint(session, IMPLIED_HINT_LOWERED_VOICE, target_id=target_id)
        applied_cases.append(IMPLIED_HINT_LOWERED_VOICE)

    if target_id and any(token in low for token in _SIT_WITH_TOKENS):
        apply_implied_hint(session, IMPLIED_HINT_SEATED_WITH_TARGET, target_id=target_id)
        applied_cases.append(IMPLIED_HINT_SEATED_WITH_TARGET)

    # Courtesy/object handling remains narrow: explicit carry/place verb, item noun,
    # and target-oriented phrasing to avoid speculative interpretation.
    if (
        target_id
        and any(token in low for token in _COURTESY_MOVE_TOKENS)
        and any(token in low for token in _COURTESY_ITEM_TOKENS)
        and any(token in low for token in _COURTESY_TARGET_PREPOSITIONS)
    ):
        set_social_target(session, target_id)
        applied_cases.append("courtesy_item_to_target")

    return {
        "applied": bool(applied_cases),
        "cases": applied_cases,
        "target_id": target_id,
    }


# --- Dialogue addressing (engine-owned; keeps active_interaction_target_id in sync) ---

_NPC_REFERENCE_TITLES: tuple[str, ...] = (
    "captain",
    "guard",
    "runner",
    "footman",
    "lady",
    "lord",
    "sir",
    "madam",
)

_WORLD_ACTION_DIALOGUE_BLOCKERS: tuple[str, ...] = (
    r"\b(?:i|we)\s+(?:search|sneak|attack|follow|track|cast|inspect|examine|check|investigate)\b",
    r"\b(?:i|we)\s+(?:grab|seize|shove|push|pull|pin|restrain|force|coerce|threaten)\b",
    r"\b(?:i|we)\s+(?:pick up|open|unlock|break|climb|jump|hide|steal|manipulate)\b",
)

_HAILING_RE = re.compile(
    r"\b(?:you\s+there|hey\s+you|hey,?\s*you|excuse me|pardon me|pardon you|oi)\b",
    re.IGNORECASE,
)

_DIALOGUE_INFO_HINTS: tuple[str, ...] = (
    "your name",
    "their name",
    "who are you",
    "what's your name",
    "what is your name",
    "who attacked",
    "what happened",
    "tell me",
)


_VOCATIVE_PREFIX_RE = re.compile(r"^\s*([^,:\n]{1,64})\s*,")


def line_opens_with_comma_vocative(text: str) -> bool:
    """True when the line begins with a ``Name, …`` clause (syntax only; no roster)."""
    return _VOCATIVE_PREFIX_RE.match(str(text or "").strip()) is not None


def npc_id_from_vocative_line(text: str, roster: List[Dict[str, Any]]) -> str:
    """Match leading ``Name, …`` to a roster NPC id (shared with strict-social emission)."""
    m = _VOCATIVE_PREFIX_RE.match(str(text or "").strip())
    if not m:
        return ""
    raw = m.group(1).strip()
    voc_slug = slugify(raw)
    if not voc_slug:
        return ""
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        nm = str(npc.get("name") or "").strip()
        if not nid:
            continue
        if slugify(nid) == voc_slug or (nm and slugify(nm) == voc_slug):
            return nid
        for word in re.split(r"\s+", nm):
            w = slugify(word)
            if w and w == voc_slug:
                return nid
        for part in slugify(nid).split("_"):
            if part and part == voc_slug:
                return nid
        for role in npc.get("address_roles") or []:
            if isinstance(role, str) and slugify(role.strip()) == voc_slug:
                return nid
        for alias in npc.get("aliases") or []:
            if not isinstance(alias, str):
                continue
            if slugify(alias.strip()) == voc_slug:
                return nid
            for word in re.split(r"\s+", alias.strip()):
                w = slugify(word)
                if w and w == voc_slug:
                    return nid
    return ""


def npc_id_from_substring_line(text: str, roster: List[Dict[str, Any]]) -> str:
    """Match full-line slug to NPC id/name (long tokens only; same rules as strict-social)."""
    text_slug = slugify(str(text or ""))
    if not text_slug:
        return ""
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        nm = str(npc.get("name") or "").strip()
        if not nid:
            continue
        ns = slugify(nid)
        if len(ns) >= 5 and ns in text_slug:
            return nid
        if nm:
            ms = slugify(nm)
            if len(ms) >= 5 and ms in text_slug:
                return nid
    return ""


def _world_npc_dicts_for_addressing(world: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    npcs = (world or {}).get("npcs") or []
    if not isinstance(npcs, list):
        npcs = []
    if not npcs:
        from game.defaults import default_world

        npcs = default_world().get("npcs") or []
    if not isinstance(npcs, list):
        return []
    return [n for n in npcs if isinstance(n, dict) and str(n.get("id") or "").strip()]


def _active_entity_scope_ids_from_scene_envelope(scene: Dict[str, Any] | None) -> Optional[Set[str]]:
    """Non-empty active_entities on the envelope narrows addressing; empty/absent means full location roster."""
    if not isinstance(scene, dict):
        return None
    scene_state = scene.get("scene_state")
    if not isinstance(scene_state, dict):
        return None
    raw = scene_state.get("active_entities")
    if not isinstance(raw, list) or not raw:
        return None
    ids = {str(v).strip() for v in raw if isinstance(v, str) and str(v).strip()}
    return ids or None


def _active_entity_scope_ids_from_session(session: Dict[str, Any] | None, scene_id: str) -> Optional[Set[str]]:
    """Mirror of scene envelope scope using synced session.scene_state (strict-social path has no envelope)."""
    if not isinstance(session, dict):
        return None
    state = session.get("scene_state")
    if not isinstance(state, dict):
        return None
    sid = _clean_string(scene_id) or ""
    active_sid = str(state.get("active_scene_id") or "").strip()
    if sid and active_sid and active_sid != sid:
        return None
    raw = state.get("active_entities")
    if not isinstance(raw, list) or not raw:
        return None
    ids = {str(v).strip() for v in raw if isinstance(v, str) and str(v).strip()}
    return ids or None


def npc_roster_for_dialogue_addressing(
    world: Dict[str, Any],
    scene_id: str,
    *,
    scene: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Location roster optionally narrowed by active entity scope (same rules as :func:`scene_npcs_in_active_scene`)."""
    sid = _clean_string(scene_id) or ""
    roster = effective_in_scene_npc_roster(world if isinstance(world, dict) else {}, sid)
    scope: Optional[Set[str]] = None
    if scene is not None:
        scope = _active_entity_scope_ids_from_scene_envelope(scene)
    elif session is not None:
        scope = _active_entity_scope_ids_from_session(session, sid)
    if not scope:
        return list(roster)
    return [n for n in roster if isinstance(n, dict) and str(n.get("id") or "").strip() in scope]


def npc_dict_by_id(world: Dict[str, Any] | None, npc_id: str) -> Optional[Dict[str, Any]]:
    """Return the world NPC dict for ``npc_id`` if present in persisted/default npcs."""
    eid = _clean_string(npc_id)
    if not eid:
        return None
    for n in _world_npc_dicts_for_addressing(world or {}):
        if str(n.get("id") or "").strip() == eid:
            return n if isinstance(n, dict) else None
    return None


def _merge_addressable_spec_onto_row(base: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Merge scene-authored addressable metadata onto a roster row (roles, aliases, priority)."""
    out = dict(base)
    if not isinstance(spec, dict):
        return out
    for k in ("name", "role", "topics", "disposition", "affiliation"):
        if spec.get(k) is not None and (k not in out or out.get(k) in (None, "", [])):
            out[k] = spec[k]
    ar: List[str] = []
    for src in (out.get("address_roles"), spec.get("address_roles")):
        if not isinstance(src, list):
            continue
        for r in src:
            if isinstance(r, str) and r.strip():
                rl = r.strip().lower()
                if rl not in ar:
                    ar.append(rl)
    if ar:
        out["address_roles"] = ar
    al: List[str] = []
    for src in (out.get("aliases"), spec.get("aliases")):
        if not isinstance(src, list):
            continue
        for a in src:
            if isinstance(a, str) and a.strip() and a.strip() not in al:
                al.append(a.strip())
    if al:
        out["aliases"] = al
    try:
        bp = int(out.get("address_priority", 999))
    except (TypeError, ValueError):
        bp = 999
    try:
        sp = int(spec.get("address_priority", 100))
    except (TypeError, ValueError):
        sp = 100
    out["address_priority"] = min(bp, sp)
    if spec.get("kind") in SCENE_ADDRESSABLE_KINDS:
        out["kind"] = spec["kind"]
    return out


def canonical_scene_addressable_roster(
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Addressable actors for dialogue binding: in-scene world NPCs, scene ``addressables``, active scope.

    Scene ``addressables`` need not exist in ``world.npcs``. Rows match the lightweight schema
    (``id``, ``name``, ``address_roles``, ``aliases``, ``kind``, ``address_priority``, …).
    """
    sid = _clean_string(scene_id) or ""
    env = scene_envelope if isinstance(scene_envelope, dict) else None
    specs = scene_addressables_from_envelope(env) if env else []
    spec_by_id: Dict[str, Dict[str, Any]] = {}
    for s in specs:
        if not isinstance(s, dict):
            continue
        eid = str(s.get("id") or "").strip()
        if eid:
            spec_by_id[eid] = s

    base = npc_roster_for_dialogue_addressing(
        world or {},
        sid,
        scene=env,
        session=session if isinstance(session, dict) else None,
    )
    acc: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []

    def _put(row: Dict[str, Any]) -> None:
        nid = str(row.get("id") or "").strip()
        if not nid:
            return
        if nid not in acc:
            acc[nid] = dict(row)
            order.append(nid)
        else:
            acc[nid] = _merge_addressable_spec_onto_row(acc[nid], row)

    for n in base:
        if not isinstance(n, dict):
            continue
        row = dict(n)
        nid = str(row.get("id") or "").strip()
        if nid and nid in spec_by_id:
            row = _merge_addressable_spec_onto_row(row, spec_by_id[nid])
        _put(row)

    for s in specs:
        nid = str(s.get("id") or "").strip()
        if nid and nid not in acc:
            _put(dict(s))

    seen_ids = set(acc.keys())
    if isinstance(session, dict):
        state = session.get("scene_state")
        if isinstance(state, dict):
            active_sid = str(state.get("active_scene_id") or "").strip()
            if (not sid or not active_sid or active_sid == sid) and isinstance(state.get("active_entities"), list):
                for raw in state["active_entities"]:
                    eid = str(raw).strip() if isinstance(raw, str) else ""
                    if not eid or eid in seen_ids:
                        continue
                    npc = npc_dict_by_id(world, eid)
                    spec = spec_by_id.get(eid)
                    if npc:
                        row = dict(npc)
                        if spec:
                            row = _merge_addressable_spec_onto_row(row, spec)
                        _put(row)
                    elif spec:
                        _put(dict(spec))
                    else:
                        _put({"id": eid, "name": eid.replace("_", " ").title()})
                    seen_ids.add(eid)

    return [acc[i] for i in order if i in acc]


def scene_addressable_actor_ids(
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
) -> Set[str]:
    """Set of NPC ids from :func:`canonical_scene_addressable_roster`."""
    return {
        str(n.get("id") or "").strip()
        for n in canonical_scene_addressable_roster(
            world, scene_id, scene_envelope=scene_envelope, session=session
        )
        if isinstance(n, dict) and str(n.get("id") or "").strip()
    }


def _find_world_npc_dict_loose(world: Dict[str, Any] | None, hint: str) -> Optional[Dict[str, Any]]:
    """Match an NPC anywhere in the world by id or name slug (ignores scene)."""
    h = _clean_string(hint)
    if not h:
        return None
    hs = slugify(h)
    for npc in _world_npc_dicts_for_addressing(world or {}):
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        nm = str(npc.get("name") or "").strip()
        if not nid:
            continue
        if nid == h or nid.lower() == h.lower():
            return npc
        if hs and (slugify(nid) == hs or hs in slugify(nid)):
            return npc
        if nm and (nm.lower() == h.lower() or slugify(nm) == hs or hs in slugify(nm)):
            return npc
    return None


def _display_name_for_npc_entry(npc: Dict[str, Any] | None, npc_id: str) -> Optional[str]:
    if isinstance(npc, dict):
        nm = _clean_string(npc.get("name"))
        if nm:
            return nm
    nid = _clean_string(npc_id)
    if not nid:
        return None
    return nid.replace("_", " ").replace("-", " ").title()


AuthoritativeSocialSource = Literal[
    "explicit_target",
    "vocative",
    "generic_role",
    "continuity",
    "substring",
    "first_roster",
    "none",
]


def resolve_authoritative_social_target(
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    *,
    player_text: str | None = None,
    normalized_action: Dict[str, Any] | None = None,
    scene_envelope: Dict[str, Any] | None = None,
    merged_player_prompt: str | None = None,
    allow_first_roster_fallback: bool = False,
) -> Dict[str, Any]:
    """Single precedence-ordered resolver for who the player is addressing in-scene.

    Precedence: explicit normalized target → comma vocative / directed name → generic role
    → active interaction continuity → conservative substring → optional first roster → none.

    Owns: final ``npc_id`` / ``npc_name`` for engine social resolution and strict-social emission
    alignment. Downstream narration may paraphrase; it must not substitute a different NPC id.

    Callers that emit or validate social output should use this result instead of re-deriving
    ``npc_id`` in a different order (prevents wiping a valid engine target on follow-up lines).
    """
    sid = _clean_string(scene_id) or ""
    w = world if isinstance(world, dict) else {}

    def _result(
        npc_id: Optional[str],
        npc_name: Optional[str],
        *,
        target_resolved: bool,
        offscene_target: bool,
        source: AuthoritativeSocialSource,
        reason: str,
        generic_role_rebind: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        nid = _clean_string(npc_id)
        nm = _clean_string(npc_name)
        out: Dict[str, Any] = {
            "npc_id": nid,
            "npc_name": nm,
            "target_resolved": bool(target_resolved),
            "offscene_target": bool(offscene_target),
            "source": source,
            "reason": reason,
        }
        if generic_role_rebind is not None:
            out["generic_role_rebind"] = generic_role_rebind
        return out

    if not sid:
        return _result(
            None,
            None,
            target_resolved=False,
            offscene_target=False,
            source="none",
            reason="empty scene_id",
        )

    roster = canonical_scene_addressable_roster(
        w, sid, scene_envelope=scene_envelope, session=session if isinstance(session, dict) else None
    )
    addr_ids = scene_addressable_actor_ids(
        w, sid, scene_envelope=scene_envelope, session=session if isinstance(session, dict) else None
    )

    na = normalized_action if isinstance(normalized_action, dict) else {}
    explicit = _clean_string(na.get("target_id")) or _clean_string(na.get("targetEntityId"))

    line_raw = _clean_string(merged_player_prompt) or _clean_string(player_text) or ""
    p_voc = str(line_raw).strip()
    low = line_raw.lower()
    prior_interlocutor: Optional[str] = None
    if isinstance(session, dict):
        prior_interlocutor = _clean_string(inspect(session).get("active_interaction_target_id"))

    # --- A. Explicit normalized target_id / targetEntityId ---
    if explicit:
        if explicit in addr_ids:
            npc = npc_dict_by_id(w, explicit) or next(
                (x for x in roster if str(x.get("id") or "").strip() == explicit), None
            )
            return _result(
                explicit,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, explicit),
                target_resolved=True,
                offscene_target=False,
                source="explicit_target",
                reason="normalized target_id matches scene-addressable roster",
            )
        slug_matched_id = ""
        exs = slugify(explicit)
        if exs:
            for npc in roster:
                if not isinstance(npc, dict):
                    continue
                nid = str(npc.get("id") or "").strip()
                nm = str(npc.get("name") or "").strip()
                if not nid:
                    continue
                if exs == slugify(nid) or (nm and exs == slugify(nm)):
                    slug_matched_id = nid
                    break
        if slug_matched_id:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == slug_matched_id), None)
            return _result(
                slug_matched_id,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, slug_matched_id),
                target_resolved=True,
                offscene_target=False,
                source="explicit_target",
                reason="normalized target string slug-matched a scene-addressable NPC",
            )
        known = _find_world_npc_dict_loose(w, explicit)
        if isinstance(known, dict):
            kid = str(known.get("id") or "").strip()
            knm = _display_name_for_npc_entry(known, kid)
            return _result(
                kid or None,
                knm,
                target_resolved=False,
                offscene_target=True,
                source="explicit_target",
                reason="explicit target names a known NPC not in scene-addressable roster",
            )
        # Unrecognized explicit hint: fall through to text-based resolution.

    # --- B. Comma vocative or leading/directed named address (roster then world) ---
    if p_voc:
        voc = npc_id_from_vocative_line(p_voc, roster)
        if voc and voc in addr_ids:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == voc), None)
            return _result(
                voc,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, voc),
                target_resolved=True,
                offscene_target=False,
                source="vocative",
                reason="comma vocative matched scene-addressable roster",
            )
        wroster = _world_npc_dicts_for_addressing(w)
        voc_w = npc_id_from_vocative_line(p_voc, wroster)
        if voc_w:
            if voc_w in addr_ids:
                npc = npc_dict_by_id(w, voc_w)
                return _result(
                    voc_w,
                    _display_name_for_npc_entry(npc, voc_w),
                    target_resolved=True,
                    offscene_target=False,
                    source="vocative",
                    reason="comma vocative matched world NPC present in scene",
                )
            npc_off = npc_dict_by_id(w, voc_w)
            return _result(
                voc_w,
                _display_name_for_npc_entry(npc_off, voc_w),
                target_resolved=False,
                offscene_target=True,
                source="vocative",
                reason="comma vocative matched an NPC not addressable in this scene",
            )
        if roster and low:
            lead = _explicit_addressed_npc_id_leading_or_directed(low, roster)
            if lead and lead in addr_ids:
                npc = next((x for x in roster if str(x.get("id") or "").strip() == lead), None)
                return _result(
                    lead,
                    _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, lead),
                    target_resolved=True,
                    offscene_target=False,
                    source="vocative",
                    reason="leading or directed named address matched roster",
                )

    # --- C. Explicit generic role address ---
    if low and roster:
        gr = match_generic_role_address(low, roster)
        if gr.get("ambiguous"):
            return _result(
                None,
                None,
                target_resolved=False,
                offscene_target=False,
                source="none",
                reason="ambiguous generic role address among scene addressables",
            )
        gen = str(gr.get("npc_id") or "").strip()
        if gen and gen in addr_ids:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == gen), None)
            rebind_meta = {
                "source": "generic_role",
                "matched_role": gr.get("matched_role"),
                "matched_actor_id": gen,
                "continuity_overridden": bool(prior_interlocutor and prior_interlocutor != gen),
            }
            return _result(
                gen,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, gen),
                target_resolved=True,
                offscene_target=False,
                source="generic_role",
                reason="generic role phrase matched a scene-addressable actor",
                generic_role_rebind=rebind_meta,
            )
        role_spoken = _last_spoken_generic_role_slug(low)
        if role_spoken and not gen:
            return _result(
                None,
                None,
                target_resolved=False,
                offscene_target=False,
                source="none",
                reason="generic role address had no matching scene actor",
            )

    # --- D. Active interaction continuity ---
    if isinstance(session, dict):
        ctx = inspect(session)
        active = _clean_string(ctx.get("active_interaction_target_id"))
        if active and active in addr_ids:
            npc = npc_dict_by_id(w, active) or next(
                (x for x in roster if str(x.get("id") or "").strip() == active), None
            )
            return _result(
                active,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, active),
                target_resolved=True,
                offscene_target=False,
                source="continuity",
                reason="active_interaction_target_id is scene-addressable",
            )

    # --- E. Conservative substring / name overlap ---
    if line_raw and roster:
        sub = npc_id_from_substring_line(line_raw, roster)
        if sub and sub in addr_ids:
            npc = next((x for x in roster if str(x.get("id") or "").strip() == sub), None)
            return _result(
                sub,
                _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, sub),
                target_resolved=True,
                offscene_target=False,
                source="substring",
                reason="conservative slug substring matched one roster NPC",
            )

    # --- F. First roster (strict-social emission fallback only) ---
    if allow_first_roster_fallback and roster:
        first = str(roster[0].get("id") or "").strip()
        if first:
            npc = roster[0] if isinstance(roster[0], dict) else None
            return _result(
                first,
                _display_name_for_npc_entry(npc, first),
                target_resolved=True,
                offscene_target=False,
                source="first_roster",
                reason="first scene-addressable roster NPC (strict-social fallback)",
            )

    return _result(
        None,
        None,
        target_resolved=False,
        offscene_target=False,
        source="none",
        reason="no addressable target resolved",
    )


# Narrow spoken roles for explicit generic addressing (scene-local roster match only).
_GENERIC_ADDRESS_ROLE_ALT = r"(?:guardsman|guardswoman|watchman|sentry|stranger|refugee|merchant|runner|guard)"
_GENERIC_ADDRESS_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(rf"\byou\s*,\s*({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\byou\s+there,?\s*({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\bto\s+the\s+({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\btowards?\s+the\s+({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"^\s*({_GENERIC_ADDRESS_ROLE_ALT})\b(?:\s*[,:?!]|\s+)"),
)

_SPOKEN_ROLE_TO_CANONICAL: Dict[str, str] = {
    "guardsman": "guard",
    "guardswoman": "guard",
    "watchman": "guard",
    "sentry": "guard",
}


def _normalize_spoken_generic_role_slug(raw: str) -> str:
    s = str(raw or "").strip().lower()
    return _SPOKEN_ROLE_TO_CANONICAL.get(s, s)


def generic_address_slugs_for_npc(npc: Dict[str, Any]) -> Set[str]:
    """Deterministic role tokens from authored NPC fields (id/name/role) for generic-address matching."""
    out: Set[str] = set()
    if not isinstance(npc, dict):
        return out
    role = npc.get("role")
    if isinstance(role, str) and role.strip():
        rs = slugify(role.strip())
        if rs:
            out.add(rs)
    nid = str(npc.get("id") or "").strip()
    for part in nid.split("_"):
        ps = slugify(part)
        if ps and len(ps) >= 3:
            out.add(ps)
    name = str(npc.get("name") or "").strip()
    for word in re.split(r"\s+", name):
        ws = slugify(word)
        if ws and len(ws) >= 3:
            out.add(ws)
    for r in npc.get("address_roles") or []:
        if isinstance(r, str) and r.strip():
            rs = slugify(r.strip())
            if rs and len(rs) >= 3:
                out.add(rs)
    for a in npc.get("aliases") or []:
        if isinstance(a, str) and a.strip():
            for word in re.split(r"\s+", a.strip()):
                ws = slugify(word)
                if ws and len(ws) >= 3:
                    out.add(ws)
    return out


def _npc_matches_normalized_generic_role(npc: Dict[str, Any], normalized_slug: str) -> bool:
    if not normalized_slug:
        return False
    slugs = generic_address_slugs_for_npc(npc)
    return normalized_slug in slugs


def _last_spoken_generic_role_slug(low: str) -> str:
    """Return the last explicit generic role token in the line (so ``… to the runner`` beats earlier mentions)."""
    best_end = -1
    best_slug = ""
    for pat in _GENERIC_ADDRESS_PATTERNS:
        for m in pat.finditer(low):
            if m.end() > best_end:
                best_end = m.end()
                best_slug = _normalize_spoken_generic_role_slug(m.group(1))
    return best_slug


def match_generic_role_address(low: str, addressable_npcs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolve generic role phrases to a single roster id, or mark ``ambiguous`` when priorities tie."""
    line = str(low or "").strip().lower()
    out: Dict[str, Any] = {}
    if not line or not addressable_npcs:
        return out
    role = _last_spoken_generic_role_slug(line)
    if not role:
        return out
    out["matched_role"] = role
    scored: List[Tuple[str, int]] = []
    for n in addressable_npcs:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or "").strip()
        if not nid or not _npc_matches_normalized_generic_role(n, role):
            continue
        try:
            pri = int(n.get("address_priority", 500))
        except (TypeError, ValueError):
            pri = 500
        scored.append((nid, pri))
    if not scored:
        return {}
    best_pri = min(p for _, p in scored)
    tier = [nid for nid, p in scored if p == best_pri]
    tier.sort()
    if len(tier) > 1:
        out["ambiguous"] = True
        return out
    out["npc_id"] = tier[0]
    out["ambiguous"] = False
    return out


def npc_id_from_explicit_generic_role_address(low: str, addressable_npcs: List[Dict[str, Any]]) -> str:
    """Resolve a scene-local NPC from narrow generic address forms (comma ``you, <role>``, ``to the <role>``, etc.).

    Explicit generic redirection must override stale active-target continuity: otherwise ``you`` in
    ``you, stranger, …`` is misread as pronoun continuation to the prior interlocutor.
    """
    m = match_generic_role_address(low, addressable_npcs)
    if m.get("ambiguous"):
        return ""
    return str(m.get("npc_id") or "").strip()


def _explicit_addressed_npc_id_leading_or_directed(low: str, roster: List[Dict[str, Any]]) -> str:
    """Line-leading name/title or ``to/at <ref>`` against roster (no comma required)."""
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        npc_id = str(npc.get("id") or "").strip()
        if not npc_id:
            continue
        for ref in extract_npc_reference_tokens(npc):
            if not ref:
                continue
            if re.search(rf"^\s*{re.escape(ref)}\b(?:\s*[,:?!-]|\s+)", low):
                return npc_id
            if re.search(rf"\b(?:to|toward|towards|at)\s+{re.escape(ref)}\b", low):
                return npc_id
    return ""


def scene_npcs_in_active_scene(scene: Dict[str, Any] | None, world: Dict[str, Any]) -> List[Dict[str, Any]]:
    """NPCs present in the active scene envelope (matches api routing)."""
    if not isinstance(scene, dict):
        return []
    scene_id = str(((scene or {}).get("scene") or {}).get("id") or "").strip()
    if not scene_id:
        return []
    return npc_roster_for_dialogue_addressing(world or {}, scene_id, scene=scene, session=None)


def extract_npc_reference_tokens(npc: Dict[str, Any]) -> Set[str]:
    refs: Set[str] = set()
    npc_id = str(npc.get("id") or "").strip().lower()
    npc_name = str(npc.get("name") or "").strip().lower()
    if npc_id:
        refs.add(npc_id)
    if npc_name:
        refs.add(npc_name)
    for token in re.split(r"[\s\-_]+", f"{npc_id} {npc_name}"):
        token = token.strip().lower()
        if len(token) >= 3:
            refs.add(token)
    for title in _NPC_REFERENCE_TITLES:
        if title in npc_name:
            refs.add(title)
    for role in npc.get("address_roles") or []:
        if isinstance(role, str) and role.strip() and len(role.strip()) >= 3:
            refs.add(role.strip().lower())
    for alias in npc.get("aliases") or []:
        if isinstance(alias, str) and alias.strip():
            al = alias.strip().lower()
            refs.add(al)
            for token in re.split(r"[\s\-_]+", al):
                t = token.strip().lower()
                if len(t) >= 3:
                    refs.add(t)
    return refs


def _line_blocks_dialogue_addressing(low: str) -> bool:
    if not low.strip():
        return True
    return any(re.search(pattern, low) for pattern in _WORLD_ACTION_DIALOGUE_BLOCKERS)


def _information_seeking_dialogue_line(low: str) -> bool:
    if "?" in low:
        return True
    if any(h in low for h in _DIALOGUE_INFO_HINTS):
        return True
    return bool(re.search(r"\b(who|what|where|when|why|how|which)\b", low))


def find_world_npc_reference_id_in_text(text: str, world: Dict[str, Any]) -> Optional[str]:
    """Match world NPC id/name tokens anywhere in the line (same rules as api dialogue routing)."""
    low = str(text or "").strip().lower()
    if not low:
        return None
    text_slug = slugify(low)
    npcs = (world or {}).get("npcs") or []
    if not isinstance(npcs, list):
        npcs = []
    if not npcs:
        from game.defaults import default_world

        npcs = default_world().get("npcs") or []
    if not isinstance(npcs, list):
        return None
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        npc_id = str(npc.get("id") or "").strip()
        npc_name = str(npc.get("name") or "").strip()
        if not npc_id:
            continue
        npc_slug = slugify(f"{npc_id} {npc_name}")
        if npc_slug and npc_slug in text_slug:
            return npc_id
        for ref in extract_npc_reference_tokens(npc):
            if not ref:
                continue
            if re.search(rf"^\s*{re.escape(ref)}\b(?:\s*[,:?!-]|\s+)", low):
                return npc_id
            if re.search(rf"\b(?:to|toward|towards|at)\s+{re.escape(ref)}\b", low):
                return npc_id
    return None


def find_addressed_npc_id_for_turn(
    text: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene: Dict[str, Any] | None,
) -> Optional[str]:
    """Resolve which scene NPC the player is addressing (vocative, name, proximity, pronouns, hailing)."""
    low = str(text or "").strip().lower()
    if not low or not isinstance(session, dict):
        return None
    scene_id = str(((scene or {}).get("scene") or {}).get("id") or "").strip()
    p = str(text or "").strip()
    w = world if isinstance(world, dict) else {}
    envelope = scene if isinstance(scene, dict) else None
    roster_canon = (
        canonical_scene_addressable_roster(w, scene_id, scene_envelope=envelope, session=session)
        if scene_id else []
    )

    # Highest priority: comma vocative. Canonical roster includes scene addressables; then any world NPC.
    if roster_canon:
        v_loc = npc_id_from_vocative_line(p, roster_canon)
        if v_loc:
            return v_loc
    world_roster = _world_npc_dicts_for_addressing(w)
    v_world = npc_id_from_vocative_line(p, world_roster)
    if v_world:
        return v_world

    # Line-leading / directed address (respects active_entities scope via canonical roster).
    if roster_canon:
        lead = _explicit_addressed_npc_id_leading_or_directed(low, roster_canon)
        if lead:
            return lead

    # Generic role beats substring overlap and pronoun continuation for lines like ``you, stranger, …``.
    gr_match = match_generic_role_address(low, roster_canon)
    if gr_match.get("ambiguous"):
        return None
    gen_id = str(gr_match.get("npc_id") or "").strip()
    if gen_id:
        return gen_id

    if not roster_canon:
        return None
    text_slug = slugify(low)
    interaction = inspect(session)
    active_target_id = str(interaction.get("active_interaction_target_id") or "").strip()

    for npc in roster_canon:
        npc_id = str(npc.get("id") or "").strip()
        npc_name = str(npc.get("name") or "").strip()
        if not npc_id:
            continue
        npc_slug = slugify(f"{npc_id} {npc_name}")
        if npc_slug and npc_slug in text_slug:
            return npc_id
        for ref in extract_npc_reference_tokens(npc):
            if not ref:
                continue
            if re.search(rf"^\s*{re.escape(ref)}\b(?:\s*[,:?!-]|\s+)", low):
                return npc_id
            if re.search(rf"\b(?:to|toward|towards|at)\s+{re.escape(ref)}\b", low):
                return npc_id

    if active_target_id and re.search(r"\b(you|your|him|her|them)\b", low):
        if assert_valid_speaker(active_target_id, session):
            return active_target_id

    world_ref = find_world_npc_reference_id_in_text(str(text or ""), world)
    if len(roster_canon) == 1 and not _line_blocks_dialogue_addressing(low):
        only_id = str(roster_canon[0].get("id") or "").strip()
        if world_ref and only_id and world_ref != only_id:
            return None
        if only_id and (_HAILING_RE.search(low) or _information_seeking_dialogue_line(low)):
            return only_id

    return None


def resolve_dialogue_lock_action_target_id(
    player_text: str,
    *,
    scene: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
) -> Optional[str]:
    """Hint ``target_id`` for dialogue-lane structured actions (see :func:`game.api._build_dialogue_first_action`).

    Precedence matches the historical API behavior: addressed line → world name/id mention → active
    interlocutor (when valid) → sole present NPC. This does **not** replace
    :func:`resolve_authoritative_social_target`, which owns the final NPC at social resolution time;
    emission and validation must not pick a different NPC afterward.
    """
    target_id = find_addressed_npc_id_for_turn(player_text, session, world, scene)
    if not target_id:
        target_id = find_world_npc_reference_id_in_text(player_text, world)
    if not target_id:
        interaction = inspect(session)
        active_target_id = str(interaction.get("active_interaction_target_id") or "").strip()
        if active_target_id and is_entity_active(session, active_target_id):
            target_id = active_target_id
    if not target_id:
        scene_npcs = scene_npcs_in_active_scene(scene, world)
        if len(scene_npcs) == 1:
            target_id = str(scene_npcs[0].get("id") or "").strip() or None
    return target_id


def build_intent_route_debug_social_exchange(
    *,
    should_route_meta: Dict[str, Any] | None,
    resolved_target_id: str | None,
) -> Dict[str, Any]:
    """Assemble ``metadata.intent_route_debug`` for dialogue-lock → social exchange turns."""
    m = should_route_meta if isinstance(should_route_meta, dict) else {}
    route_reason = m.get("route_reason") or "dialogue_lane"
    addressed_id = resolved_target_id or (str(m.get("addressed_actor_id") or "").strip() or None)
    addressed_src = m.get("addressed_actor_source")
    if addressed_src is None:
        addressed_src = "dialogue_target_resolution" if resolved_target_id else None
    return {
        "routed_to": "social_exchange",
        "route_reason": route_reason,
        "addressed_actor_id": addressed_id,
        "addressed_actor_source": addressed_src,
    }


def build_intent_route_debug_adjudication_query(*, category: str | None) -> Dict[str, Any]:
    """Assemble ``metadata.intent_route_debug`` when the turn resolves as procedural adjudication."""
    return {
        "routed_to": "adjudication_query",
        "route_reason": f"procedural_{category or 'unknown'}",
        "addressed_actor_id": None,
        "addressed_actor_source": None,
    }


def is_rules_or_engine_mechanics_question(text: str | None) -> bool:
    """True for roll/skill/procedure questions to the GM (including short parenthetical clauses)."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    if re.search(r"\b(?:does|do)\s+that\s+require\b", low) and re.search(
        r"\b(?:sleight|hand|perception|stealth|roll|check|skill|difficulty)\b",
        low,
    ):
        return True
    if re.search(r"\b(?:skill\s+check|saving\s+throw|\bdc\b|difficulty\s+class)\b", low):
        return True
    if re.search(
        r"\b(?:sleight of hand|perception|stealth|sense motive|diplomacy|intimidate|bluff|thievery)\b",
        low,
    ) and re.search(r"\b(?:need|needed|require|required|roll|check)\b", low):
        return True
    if re.search(r"\bneed(?:ed)?\s+(?:a\s+)?roll\b", low) or re.search(
        r"\brequire(?:s|d)?\s+(?:a\s+)?(?:roll|check)\b",
        low,
    ):
        return True
    return False


def is_gm_or_system_facing_question(text: str | None) -> bool:
    """True for clear player-to-GM feasibility / state questions, not NPC-directed dialogue."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    if re.search(r"\b(?:can|could|would)\s+(?:i|we)\b", low):
        return True
    if re.search(r"\b(?:is there|are there)\s+(?:enough|any)\b", low):
        return True
    if "read the" in low and "board" in low and "?" in low:
        return True
    if re.search(r"\bwould\s+\w+\s+know\s+(?:this|that|already)\b", low):
        return True
    if "?" in low and re.search(
        r"\b(?:reach|climb|jump)\s+(?:the\s+)?(?:roof|wall|ledge|balcony)\b",
        low,
    ):
        return True
    return False


def _looks_like_information_seeking_player_question(text: str) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    if "?" in low:
        return True
    if any(h in low for h in _DIALOGUE_INFO_HINTS):
        return True
    return bool(re.search(r"\b(who|what|where|when|why|how|which|tell me|do you know)\b", low))


def should_route_addressed_question_to_social(
    text: str | None,
    *,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_envelope: Dict[str, Any] | None,
) -> tuple[bool, Dict[str, Any]]:
    """Canonical gate: NPC-directed information-seeking vs GM/rules feasibility (adjudication lane).

    Owns: the decision that a line should **not** be classified as procedural adjudication so chat
    can stay in social exchange (active interlocutor follow-up or directed scene question).
    :func:`game.adjudication.classify_adjudication_query` consults this first; do not reimplement
    the same checks in other layers.

    Returns (decision, debug_meta) with route_reason / addressed_actor_id / addressed_actor_source.
    """
    meta: Dict[str, Any] = {
        "route_reason": None,
        "addressed_actor_id": None,
        "addressed_actor_source": None,
    }
    t = str(text or "").strip()
    if not t:
        return False, meta
    if is_gm_or_system_facing_question(t):
        meta["route_reason"] = "gm_feasibility"
        return False, meta
    if is_rules_or_engine_mechanics_question(t):
        meta["route_reason"] = "rules_or_mechanics_query"
        return False, meta

    if not isinstance(scene_envelope, dict):
        return False, meta
    scene_obj = scene_envelope.get("scene")
    if not isinstance(scene_obj, dict):
        return False, meta
    scene_id = str(scene_obj.get("id") or "").strip()
    if not scene_id:
        return False, meta

    sess = session if isinstance(session, dict) else None
    w = world if isinstance(world, dict) else {}
    if not _looks_like_information_seeking_player_question(t):
        return False, meta

    if sess is not None:
        ctx = inspect(sess)
        active_id = str(ctx.get("active_interaction_target_id") or "").strip()
        mode = str(ctx.get("interaction_mode") or "").strip().lower()
        kind = str(ctx.get("active_interaction_kind") or "").strip().lower()
        social_mode = mode == "social" or kind == "social"
        if active_id and social_mode and is_entity_active(sess, active_id):
            addr_ids = scene_addressable_actor_ids(
                w, scene_id, scene_envelope=scene_envelope, session=sess
            )
            if active_id in addr_ids:
                meta["route_reason"] = "active_interlocutor_followup"
                meta["addressed_actor_id"] = active_id
                meta["addressed_actor_source"] = "active_interlocutor"
                return True, meta

        addressed = find_addressed_npc_id_for_turn(t, sess, w, scene_envelope)
        if addressed:
            meta["route_reason"] = "directed_social_question"
            meta["addressed_actor_id"] = addressed
            meta["addressed_actor_source"] = "scene_address_resolution"
            return True, meta

    return False, meta


def establish_dialogue_interaction_from_input(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene: Dict[str, Any] | None,
    player_text: str | None,
) -> Dict[str, Any]:
    """Set active social target when the player line addresses an NPC in the current scene."""
    if not isinstance(session, dict) or not isinstance(world, dict):
        return {"established": False, "target_id": None}
    low = str(player_text or "").strip().lower()
    if not low:
        return {"established": False, "target_id": None}
    if _line_blocks_dialogue_addressing(low):
        return {"established": False, "target_id": None}

    target_id = find_addressed_npc_id_for_turn(str(player_text or ""), session, world, scene)
    if not target_id:
        return {"established": False, "target_id": None}

    set_social_target(session, target_id)
    return {"established": True, "target_id": target_id}
