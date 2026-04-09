"""Routing classifiers: dialogue vs world-action lanes for API turn handling.

Ownership: ``choose_interaction_route``-adjacent classifiers and lane selection used by
``game.api`` (dialogue lock, cues, OOC/engine question guards). **Not here:** authoritative
target binding (:mod:`game.interaction_context`), vocative helpers
(:mod:`game.dialogue_targeting`), or social **commitment-break** decisions
(:mod:`game.social_continuity_routing`).
"""
from __future__ import annotations

import re

from game.adjudication import classify_adjudication_query
from game.interaction_context import (
    apply_world_action_social_continuity_break,
    assert_valid_speaker,
    build_intent_route_debug_social_exchange,
    evaluate_world_action_social_continuity_break,
    find_addressed_npc_id_for_turn,
    find_world_npc_reference_id_in_text,
    inspect as inspect_interaction_context,
    merge_turn_segments_for_directed_social_entry,
    resolve_dialogue_lock_action_target_id,
    resolve_directed_social_entry,
    scene_npcs_in_active_scene,
    should_route_addressed_question_to_social,
    _looks_like_local_observation_question,
)
from game.utils import slugify


_MECHANICS_OR_PROCEDURAL_TOKENS: tuple[str, ...] = (
    "roll",
    "check",
    "skill check",
    "dc",
    "difficulty",
    "saving throw",
    "need to roll",
    "do i need",
    "does this need",
    "mechanically",
    "rules-wise",
    "rules wise",
    "what actions are available",
    "which actions are available",
    "actions are available",
    "mechanic",
    "rules",
    "procedure",
)
_ENGINE_STATE_QUERY_PATTERNS: tuple[str, ...] = (
    "earshot",
    "who can hear",
    "in range",
    "how far",
    "distance",
    "is anyone else here",
    "who is here",
    "what is my",
    "current hp",
    "spell slots",
    "inventory",
)
_OOC_MARKER_PATTERNS: tuple[str, ...] = (
    r"\booc\b",
    r"\bout of character\b",
    r"\bas a player\b",
    r"^\s*\(\(",
)
_QUESTION_START_TOKENS: tuple[str, ...] = (
    "where",
    "what",
    "who",
    "when",
    "why",
    "how",
    "can",
    "could",
    "would",
    "should",
    "do",
    "does",
    "is",
    "are",
    "will",
)
_IN_CHARACTER_REPLY_PREFIXES: tuple[str, ...] = (
    "yes",
    "no",
    "maybe",
    "i say",
    "i tell",
    "i reply",
    "i answer",
)
_IN_CHARACTER_COMMAND_PREFIXES: tuple[str, ...] = (
    "lead the way",
    "tell me",
    "show me",
    "take me",
    "bring me",
    "let me through",
    "stand aside",
    "step aside",
)
_DIALOGUE_QUESTION_WORDS: tuple[str, ...] = (
    "who",
    "what",
    "where",
    "when",
    "why",
    "how",
    "which",
)
_DIALOGUE_SPEECH_TOKENS: tuple[str, ...] = (
    "ask",
    "asks",
    "asked",
    "question",
    "tell me",
    "do you know",
    "what do you know",
    "say",
    "reply",
    "answer",
    "i ask",
    "we ask",
)
_DIALOGUE_INFO_REQUEST_PHRASES: tuple[str, ...] = (
    "do you know",
    "what do you know",
    "tell me what you know",
    "who attacked",
    "what are they planning",
    "who saw this happen",
    "who saw it",
    "where can i find",
    "where can we find",
    "where do i find",
    "where are they",
)
_AMBIGUOUS_DIALOGUE_FOLLOWUP_PHRASES: tuple[str, ...] = (
    "what should i do next",
    "what's the next step",
    "what is the next step",
    "where does this lead",
    "where does this go",
    "what now",
)
_WORLD_ACTION_STRONG_PATTERNS: tuple[str, ...] = (
    r"\b(?:i|we)\s+(?:search|sneak|attack|follow|track|cast|inspect|examine|check|investigate)\b",
    r"\b(?:i|we)\s+(?:grab|seize|shove|push|pull|pin|restrain|force|coerce|threaten)\b",
    r"\b(?:i|we)\s+(?:pick up|open|unlock|break|climb|jump|hide|steal|manipulate)\b",
)
_WORLD_ACTION_FORCEFUL_PATTERNS: tuple[str, ...] = (
    r"\b(?:i|we)\s+(?:grab|seize|attack|strike|cast|force|coerce|threaten|restrain)\b",
    r"\b(?:i|we)\s+(?:follow|track|sneak|search)\b",
)


def _merged_text_for_dialogue_routing(segmented_turn: dict | None, player_text: str) -> str:
    """Rejoin turn segments so hail + extracted question still read as one line for addressing."""
    if not isinstance(segmented_turn, dict):
        return str(player_text or "").strip()
    ordered_keys = (
        "declared_action_text",
        "spoken_text",
        "adjudication_question_text",
        "observation_intent_text",
    )
    parts: list[str] = []
    seen: set[str] = set()
    for key in ordered_keys:
        raw = segmented_turn.get(key)
        if not isinstance(raw, str):
            continue
        s = raw.strip()
        if not s or s in seen:
            continue
        parts.append(s)
        seen.add(s)
    return " ".join(parts) if parts else str(player_text or "").strip()


def _find_world_npc_reference_id(text: str, world: dict) -> str | None:
    return find_world_npc_reference_id_in_text(text, world)


def _is_information_seeking_clause(text: str) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    if any(phrase in low for phrase in _DIALOGUE_INFO_REQUEST_PHRASES):
        return True
    if any(token in low for token in _DIALOGUE_SPEECH_TOKENS) and any(word in low for word in _DIALOGUE_QUESTION_WORDS):
        return True
    if "?" in low:
        lead = re.sub(r'^[^a-z0-9"]+', "", low)
        lead = lead.replace('"', "")
        first = lead.split(" ", 1)[0] if lead else ""
        if first in _QUESTION_START_TOKENS:
            return True
        if any(word in low for word in _DIALOGUE_QUESTION_WORDS):
            return True
    return False


def _has_dialogue_cue(*, text: str, segmented_turn: dict | None) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    spoken_text = segmented_turn.get("spoken_text") if isinstance(segmented_turn, dict) else None
    if isinstance(spoken_text, str) and spoken_text.strip():
        return True
    if '"' in low:
        return True
    if _is_information_seeking_clause(low):
        return True
    return any(token in low for token in _DIALOGUE_SPEECH_TOKENS)


def is_world_action(text: str, segmented_turn: dict | None = None) -> bool:
    clause = (
        (segmented_turn.get("declared_action_text") if isinstance(segmented_turn, dict) else None)
        or text
    )
    low = str(clause or "").strip().lower()
    if not low:
        return False
    return any(re.search(pattern, low) for pattern in _WORLD_ACTION_STRONG_PATTERNS)


def is_directed_dialogue(
    text: str,
    *,
    scene: dict,
    session: dict,
    world: dict,
    segmented_turn: dict | None = None,
    canonical_social_entry: dict | None = None,
) -> bool:
    ce = canonical_social_entry
    if ce is None:
        ce = resolve_directed_social_entry(
            session=session,
            scene=scene,
            world=world,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=str(text or ""),
        )
    if ce.get("should_route_social"):
        return True
    merged = _merged_text_for_dialogue_routing(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(text or ""),
    )
    primary_clause = merged.strip() or str(text or "").strip()
    clause = str(primary_clause or "").strip()
    if not clause:
        return False
    if _is_explicit_ooc(clause) or _is_explicit_ooc(text):
        return False
    if _contains_mechanics_or_procedural_language(clause):
        return False
    if _is_engine_state_question(clause):
        return False
    # Ambiguity rule: during an active NPC exchange, "next step"-style
    # follow-ups default to that interlocutor unless explicit procedural/OOC
    # markers were present above.
    if _has_active_social_interlocutor(session, scene=scene, world=world) and _is_ambiguous_dialogue_followup(
        clause
    ):
        if evaluate_world_action_social_continuity_break(
            session=session,
            scene=scene,
            world=world,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=str(text or ""),
        ):
            merged_lane = merge_turn_segments_for_directed_social_entry(
                segmented_turn if isinstance(segmented_turn, dict) else None,
                str(text or ""),
            )
            apply_world_action_social_continuity_break(
                session,
                merged_text=merged_lane.strip(),
                scene=scene,
            )
            return False
        return True

    scene_npcs = scene_npcs_in_active_scene(scene, world)
    addressed_npc_id = find_addressed_npc_id_for_turn(clause, session, world, scene)
    has_present_character = bool(scene_npcs)
    has_world_reference = bool(_find_world_npc_reference_id(clause, world))
    has_dialogue_cue = _has_dialogue_cue(text=text, segmented_turn=segmented_turn)
    asks_for_information = _is_information_seeking_clause(clause)

    if addressed_npc_id:
        return True
    if _looks_like_local_observation_question(clause):
        return False
    if has_dialogue_cue and has_world_reference:
        return True
    if has_dialogue_cue and has_present_character:
        return True
    if asks_for_information and has_present_character:
        return True
    return False


def choose_interaction_route(
    text: str,
    *,
    scene: dict,
    session: dict,
    world: dict,
    segmented_turn: dict | None = None,
    canonical_social_entry: dict | None = None,
) -> str:
    """Choose coarse chat lane: dialogue, action, or undecided.

    Canonical social entry is computed in :func:`game.interaction_context.resolve_directed_social_entry`
    (pass *canonical_social_entry* from /api/chat to avoid duplicate work).
    """
    directed_dialogue = is_directed_dialogue(
        text,
        scene=scene,
        session=session,
        world=world,
        segmented_turn=segmented_turn,
        canonical_social_entry=canonical_social_entry,
    )
    world_action = is_world_action(text, segmented_turn=segmented_turn)
    has_dialogue_cue = _has_dialogue_cue(text=text, segmented_turn=segmented_turn)
    low = str(text or "").strip().lower()
    forceful_action = any(re.search(pattern, low) for pattern in _WORLD_ACTION_FORCEFUL_PATTERNS)

    if directed_dialogue:
        # Dialogue lock: keep spoken questioning in social lane unless action intent is forceful.
        if world_action and (forceful_action or not has_dialogue_cue):
            return "action"
        return "dialogue"
    if world_action:
        return "action"
    return "undecided"


def _build_dialogue_first_action(
    *,
    player_text: str,
    scene: dict,
    session: dict,
    world: dict,
    segmented_turn: dict | None,
    canonical_social_entry: dict | None = None,
) -> dict | None:
    ce = canonical_social_entry
    if ce is None:
        ce = resolve_directed_social_entry(
            session=session,
            scene=scene,
            world=world,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=str(player_text or ""),
        )
    merged_address = merge_turn_segments_for_directed_social_entry(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(player_text or ""),
    )
    if not ce.get("should_route_social") and not is_directed_dialogue(
        player_text,
        scene=scene,
        session=session,
        world=world,
        segmented_turn=segmented_turn,
        canonical_social_entry=ce,
    ):
        return None

    target_id = str(ce.get("target_actor_id") or "").strip() or resolve_dialogue_lock_action_target_id(
        merged_address or player_text,
        scene=scene,
        session=session,
        world=world,
    )

    action_kind = (
        "question"
        if _is_information_seeking_clause(merged_address or player_text)
        or "?" in str(merged_address or player_text or "")
        else "social_probe"
    )
    action_label = str(player_text or "").strip()
    if not action_label:
        return None
    _, _route_meta = should_route_addressed_question_to_social(
        merged_address or player_text,
        session=session,
        world=world,
        scene_envelope=scene if isinstance(scene, dict) else None,
    )
    metadata = {
        "routed_via_dialogue_lock": True,
        "route": "dialogue",
        "canonical_entry_path": "social",
        "canonical_entry_reason": ce.get("reason"),
        "canonical_entry_target_actor_id": ce.get("target_actor_id") or target_id,
        "intent_route_debug": build_intent_route_debug_social_exchange(
            should_route_meta=_route_meta if isinstance(_route_meta, dict) else None,
            resolved_target_id=target_id,
        ),
    }
    if ce.get("open_social_solicitation"):
        metadata["open_social_solicitation"] = True
        metadata["broad_address_bid"] = bool(ce.get("broad_address_bid"))
        if ce.get("broadcast_social_open_call"):
            metadata["broadcast_social_open_call"] = True
        cands = ce.get("candidate_addressable_ids")
        if isinstance(cands, list):
            metadata["candidate_addressable_ids"] = list(cands)
        try:
            metadata["candidate_addressable_count"] = int(ce.get("candidate_addressable_count", 0))
        except (TypeError, ValueError):
            metadata["candidate_addressable_count"] = len(metadata.get("candidate_addressable_ids") or [])
        if ce.get("broad_address_reason") is not None:
            metadata["broad_address_reason"] = ce.get("broad_address_reason")
        if ce.get("broad_address_phrase_matched") is not None:
            metadata["broad_address_phrase_matched"] = ce.get("broad_address_phrase_matched")
    if target_id:
        metadata["active_interaction_target_id"] = target_id
    intent_cls = "open_call" if ce.get("open_social_solicitation") else "social_exchange"
    out = {
        "id": slugify(f"{action_kind}-{target_id or 'npc'}") or "social",
        "label": action_label[:140],
        "type": action_kind,
        "social_intent_class": intent_cls,
        "prompt": action_label,
        "metadata": metadata,
    }
    if target_id:
        out["target_id"] = target_id
        out["targetEntityId"] = target_id
    return out


def _is_explicit_ooc(text: str | None) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    return any(re.search(pattern, low) for pattern in _OOC_MARKER_PATTERNS)


def _contains_mechanics_or_procedural_language(text: str | None) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    return any(token in low for token in _MECHANICS_OR_PROCEDURAL_TOKENS)


def _has_active_social_interlocutor(
    session: dict | None,
    *,
    scene: dict | None = None,
    world: dict | None = None,
) -> bool:
    inspected = inspect_interaction_context(session if isinstance(session, dict) else {})
    target_id = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    if not target_id:
        return False
    if not assert_valid_speaker(
        target_id,
        session if isinstance(session, dict) else {},
        scene_envelope=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    ):
        return False
    kind = str((inspected or {}).get("active_interaction_kind") or "").strip().lower()
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    engagement = str((inspected or {}).get("engagement_level") or "").strip().lower()
    return (kind == "social" or mode == "social") and engagement in {"engaged", "active", ""}


def _is_ambiguous_dialogue_followup(text: str | None) -> bool:
    """Return True for short follow-up prompts that can read IC or OOC."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    return any(phrase in low for phrase in _AMBIGUOUS_DIALOGUE_FOLLOWUP_PHRASES)


def _is_engine_state_question(text: str | None) -> bool:
    low = str(text or "").strip().lower()
    if not low or "?" not in low:
        return False
    return any(pattern in low for pattern in _ENGINE_STATE_QUERY_PATTERNS)


def _looks_like_in_character_exchange_clause(text: str | None, spoken_text: str | None) -> bool:
    clause = str(text or "").strip()
    low = clause.lower()
    if not clause:
        return False
    if isinstance(spoken_text, str) and spoken_text.strip():
        return True
    if "?" in clause:
        words = low.replace("?", " ").split()
        if words and words[0] in _QUESTION_START_TOKENS:
            return True
    if any(low.startswith(prefix) for prefix in _IN_CHARACTER_COMMAND_PREFIXES):
        return True
    if " require an audience" in f" {low}" or low.startswith("footman? i require an audience"):
        return True
    return any(low.startswith(prefix) for prefix in _IN_CHARACTER_REPLY_PREFIXES)


def _prefer_dialogue_over_adjudication(
    *,
    player_text: str,
    segmented_turn: dict | None,
    adjudication_text: str | None,
    has_active_interaction: bool = False,
    scene: dict | None = None,
    session: dict | None = None,
    world: dict | None = None,
    canonical_social_entry: dict | None = None,
) -> bool:
    """Bias ambiguous turns toward dialogue instead of procedural adjudication.

    When *has_active_interaction* is True the classifier uses narrowed
    feasibility patterns so that normal in-character social questioning
    during an active NPC conversation is not captured as adjudication.
    """
    if isinstance(scene, dict) and isinstance(session, dict) and isinstance(world, dict):
        ce = canonical_social_entry
        if ce is None:
            ce = resolve_directed_social_entry(
                session=session,
                scene=scene,
                world=world,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                raw_text=str(player_text or ""),
            )
        if ce.get("should_route_social"):
            return True
    spoken_text = segmented_turn.get("spoken_text") if isinstance(segmented_turn, dict) else None
    declared_action_text = segmented_turn.get("declared_action_text") if isinstance(segmented_turn, dict) else None
    primary_clause = _merged_text_for_dialogue_routing(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(player_text or ""),
    ).strip() or str(declared_action_text or spoken_text or player_text or "").strip()
    if not primary_clause:
        return False
    if _is_explicit_ooc(player_text) or _is_explicit_ooc(primary_clause):
        return False
    if _contains_mechanics_or_procedural_language(primary_clause):
        return False
    if _is_engine_state_question(adjudication_text or primary_clause):
        return False
    if has_active_interaction and _is_ambiguous_dialogue_followup(primary_clause):
        return True
    if isinstance(scene, dict) and isinstance(session, dict) and isinstance(world, dict):
        if choose_interaction_route(
            player_text,
            scene=scene,
            session=session,
            world=world,
            segmented_turn=segmented_turn,
        ) == "dialogue":
            return True
    if classify_adjudication_query(
        adjudication_text or primary_clause,
        has_active_interaction=has_active_interaction,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
    ) is not None:
        return False
    return _looks_like_in_character_exchange_clause(primary_clause, spoken_text)
