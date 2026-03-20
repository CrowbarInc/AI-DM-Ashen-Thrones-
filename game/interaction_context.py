"""Authoritative interaction-context mutation API.

This module is the single owner for interaction-context runtime mutations.
Callers may read context elsewhere, but all writes should route through these
functions so behavior remains deterministic and inspectable.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

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
        if loc and loc != scene_id:
            continue
        out.append(npc)
    return out


def _extract_target_from_text(text: str, world: Dict[str, Any], scene_id: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    text_slug = slugify(text)
    if not text_slug:
        return None
    for npc in _scene_npcs(world, scene_id):
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
