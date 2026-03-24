"""Authoritative interaction-context mutation API.

This module is the single owner for interaction-context runtime mutations.
Callers may read context elsewhere, but all writes should route through these
functions so behavior remains deterministic and inspectable.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

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
    scene = scene_envelope.get("scene")
    if not isinstance(scene, dict):
        return []
    authored: List[str] = []
    for key in ("active_entities", "entities", "npcs"):
        raw = scene.get(key)
        if not isinstance(raw, list):
            continue
        for item in raw:
            ent_id = ""
            if isinstance(item, str):
                ent_id = item.strip()
            elif isinstance(item, dict):
                ent_id = str(item.get("id") or "").strip()
            if ent_id and ent_id not in authored:
                authored.append(ent_id)
    return authored


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


# Narrow spoken roles for explicit generic addressing (scene-local roster match only).
_GENERIC_ADDRESS_ROLE_ALT = r"(?:guardsman|stranger|refugee|merchant|runner|guard)"
_GENERIC_ADDRESS_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(rf"\byou\s*,\s*({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\bto\s+the\s+({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"\btowards?\s+the\s+({_GENERIC_ADDRESS_ROLE_ALT})\b"),
    re.compile(rf"^\s*({_GENERIC_ADDRESS_ROLE_ALT})\b(?:\s*[,:?!]|\s+)"),
)


def _normalize_spoken_generic_role_slug(raw: str) -> str:
    s = str(raw or "").strip().lower()
    if s == "guardsman":
        return "guard"
    return s


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


def npc_id_from_explicit_generic_role_address(low: str, addressable_npcs: List[Dict[str, Any]]) -> str:
    """Resolve a scene-local NPC from narrow generic address forms (comma ``you, <role>``, ``to the <role>``, etc.).

    Explicit generic redirection must override stale active-target continuity: otherwise ``you`` in
    ``you, stranger, …`` is misread as pronoun continuation to the prior interlocutor.
    """
    line = str(low or "").strip().lower()
    if not line or not addressable_npcs:
        return ""
    role = _last_spoken_generic_role_slug(line)
    if not role:
        return ""
    matches = [
        str(n.get("id") or "").strip()
        for n in addressable_npcs
        if isinstance(n, dict) and _npc_matches_normalized_generic_role(n, role)
    ]
    matches = [m for m in matches if m]
    if not matches:
        return ""
    matches.sort()
    return matches[0]


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

    # Highest priority: comma vocative. Resolve against in-scene location roster first, then any
    # world NPC so ``Runner, …`` overrides a stale interlocutor even when the addressee is off-scene.
    roster_by_location = effective_in_scene_npc_roster(w, scene_id) if scene_id else []
    if roster_by_location:
        v_loc = npc_id_from_vocative_line(p, roster_by_location)
        if v_loc:
            return v_loc
    world_roster = _world_npc_dicts_for_addressing(w)
    v_world = npc_id_from_vocative_line(p, world_roster)
    if v_world:
        return v_world

    # Line-leading / directed address on the full location roster (not active_entities subset).
    if roster_by_location:
        lead = _explicit_addressed_npc_id_leading_or_directed(low, roster_by_location)
        if lead:
            return lead

    scene_npcs = (
        npc_roster_for_dialogue_addressing(w, scene_id, scene=scene, session=session) if scene_id else []
    )
    # Generic role address beats substring overlap and pronoun continuation so lines like
    # ``you, stranger, …`` retarget instead of sticking to the prior interlocutor on ``you``.
    gen_id = npc_id_from_explicit_generic_role_address(low, scene_npcs)
    if gen_id:
        return gen_id

    if not scene_npcs:
        return None
    text_slug = slugify(low)
    interaction = inspect(session)
    active_target_id = str(interaction.get("active_interaction_target_id") or "").strip()

    for npc in scene_npcs:
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
    if len(scene_npcs) == 1 and not _line_blocks_dialogue_addressing(low):
        only_id = str(scene_npcs[0].get("id") or "").strip()
        if world_ref and only_id and world_ref != only_id:
            return None
        if only_id and (_HAILING_RE.search(low) or _information_seeking_dialogue_line(low)):
            return only_id

    return None


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
