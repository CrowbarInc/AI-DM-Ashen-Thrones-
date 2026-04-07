from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Literal

from game.exploration import EXPLORATION_KINDS
from game.social import SOCIAL_KINDS


ResponseType = Literal["dialogue", "answer", "action_outcome", "neutral_narration"]
SourceRoute = Literal["social", "adjudication", "exploration", "combat", "mixed"]

_QUESTION_WORD_RE = re.compile(r"\b(?:who|what|where|when|why|how|which|tell me|do you know)\b", re.IGNORECASE)
_COURTEOUS_OR_PASSIVE_RE = re.compile(
    r"\b(?:please|thanks|thank you|sorry|excuse me|wait|hold|watch|observe|look|listen|investigate|inspect|travel|go|move)\b",
    re.IGNORECASE,
)
_EXPLICIT_HOSTILE_TEXT_RE = re.compile(
    r"\b(?:attack|strike|stab|shoot|kill|grab|shove|threaten|intimidate|draw\s+steel|draw\s+my\s+weapon)\b",
    re.IGNORECASE,
)

_COMBAT_KINDS = frozenset({"attack", "combat", "cast_spell", "skill_check", "roll_initiative", "end_turn"})
_ACTION_OUTCOME_KINDS = frozenset(set(EXPLORATION_KINDS) | _COMBAT_KINDS | {"scene_opening"})
_HOSTILE_RESOLUTION_KINDS = frozenset({"attack", "combat", "intimidate"})
_QUESTIONISH_SOCIAL_KINDS = frozenset({"question", "social_probe"})


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _question_like_text(text: str | None, segmented_turn: dict | None) -> bool:
    raw = _clean_str(text)
    if isinstance(segmented_turn, dict):
        if _clean_str(segmented_turn.get("adjudication_question_text")):
            return True
        spoken = _clean_str(segmented_turn.get("spoken_text"))
        if "?" in spoken or _QUESTION_WORD_RE.search(spoken):
            return True
    return bool(raw and ("?" in raw or _QUESTION_WORD_RE.search(raw)))


def _social_payload(resolution: dict | None) -> dict:
    social = (resolution or {}).get("social")
    return social if isinstance(social, dict) else {}


def _resolution_metadata(resolution: dict | None) -> dict:
    metadata = (resolution or {}).get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _strict_target_id(
    *,
    resolution: dict | None,
    interaction_context: dict | None,
    directed_social_entry: dict | None,
) -> str | None:
    social = _social_payload(resolution)
    npc_id = _clean_str(social.get("npc_id"))
    if npc_id:
        return npc_id
    directed_id = _clean_str((directed_social_entry or {}).get("target_actor_id"))
    if directed_id:
        return directed_id
    active_id = _clean_str((interaction_context or {}).get("active_interaction_target_id"))
    return active_id or None


def _resolve_source_route(
    *,
    segmented_turn: dict | None,
    normalized_action: dict | None,
    resolution: dict | None,
    interaction_context: dict | None,
    directed_social_entry: dict | None,
    route_choice: str | None,
) -> SourceRoute:
    resolution_kind = _clean_str((resolution or {}).get("kind")).lower()
    normalized_type = _clean_str((normalized_action or {}).get("type")).lower()
    metadata = _resolution_metadata(resolution)

    if resolution_kind == "adjudication_query":
        return "adjudication"
    if metadata.get("embedded_adjudication") and resolution_kind and resolution_kind != "adjudication_query":
        return "mixed"
    if isinstance(segmented_turn, dict) and _clean_str(segmented_turn.get("adjudication_question_text")) and resolution_kind:
        return "mixed"
    if resolution_kind in _COMBAT_KINDS or normalized_type in _COMBAT_KINDS:
        return "combat"
    if resolution_kind in SOCIAL_KINDS:
        return "social"
    if resolution_kind in _ACTION_OUTCOME_KINDS or normalized_type in _ACTION_OUTCOME_KINDS:
        return "exploration"
    if bool((directed_social_entry or {}).get("should_route_social")):
        return "social"
    if _clean_str(route_choice).lower() == "dialogue":
        return "social"
    if _clean_str(route_choice).lower() == "action":
        return "exploration"
    mode = _clean_str((interaction_context or {}).get("interaction_mode")).lower()
    if mode == "social" and _clean_str((interaction_context or {}).get("active_interaction_target_id")):
        return "social"
    return "exploration"


def _resolution_requires_dialogue(
    *,
    resolution: dict | None,
    directed_social_entry: dict | None,
    route_choice: str | None,
    strict_target_id: str | None,
) -> bool:
    resolution_kind = _clean_str((resolution or {}).get("kind")).lower()
    social = _social_payload(resolution)
    if resolution_kind in SOCIAL_KINDS and strict_target_id and not bool(social.get("offscene_target")):
        if bool((resolution or {}).get("requires_check")):
            return False
        return True
    if strict_target_id and bool((directed_social_entry or {}).get("should_route_social")):
        return True
    return bool(strict_target_id and _clean_str(route_choice).lower() == "dialogue")


def _resolution_requires_answer(
    *,
    segmented_turn: dict | None,
    resolution: dict | None,
    raw_player_text: str | None,
) -> bool:
    resolution_kind = _clean_str((resolution or {}).get("kind")).lower()
    if resolution_kind == "adjudication_query":
        return True
    if resolution_kind in _QUESTIONISH_SOCIAL_KINDS:
        return True
    return _question_like_text(raw_player_text, segmented_turn)


def _authoritative_escalation_required(resolution: dict | None, normalized_action: dict | None) -> bool:
    resolution_kind = _clean_str((resolution or {}).get("kind")).lower()
    normalized_type = _clean_str((normalized_action or {}).get("type")).lower()
    if resolution_kind in _HOSTILE_RESOLUTION_KINDS or normalized_type in _HOSTILE_RESOLUTION_KINDS:
        return True
    combat_payload = (resolution or {}).get("combat")
    if isinstance(combat_payload, dict) and combat_payload:
        return True
    return False


def _non_hostile_guard_applies(
    *,
    segmented_turn: dict | None,
    normalized_action: dict | None,
    resolution: dict | None,
    raw_player_text: str | None,
    required_response_type: ResponseType,
) -> tuple[bool, str | None]:
    if _authoritative_escalation_required(resolution, normalized_action):
        return False, None

    resolution_kind = _clean_str((resolution or {}).get("kind")).lower()
    normalized_type = _clean_str((normalized_action or {}).get("type")).lower()
    raw = _clean_str(raw_player_text)

    if required_response_type == "answer":
        return True, "informational_query_guard"
    if resolution_kind in _QUESTIONISH_SOCIAL_KINDS:
        return True, "social_question_guard"
    if resolution_kind in {"observe", "investigate", "travel", "scene_transition", "scene_opening", "already_searched", "discover_clue"}:
        return True, "non_hostile_world_action_guard"
    if normalized_type in {"observe", "investigate", "travel", "scene_transition"}:
        return True, "non_hostile_world_action_guard"
    if raw and not _EXPLICIT_HOSTILE_TEXT_RE.search(raw):
        if _question_like_text(raw, segmented_turn):
            return True, "question_like_non_hostile_guard"
        if _COURTEOUS_OR_PASSIVE_RE.search(raw):
            return True, "courteous_or_passive_guard"
    return False, None


@dataclass(frozen=True)
class ResponseTypeContract:
    required_response_type: ResponseType
    source_route: SourceRoute
    allow_escalation: bool
    escalation_block_reason: str | None
    strict_target_id: str | None
    strict_answer_expected: bool
    strict_dialogue_expected: bool
    action_must_preserve_agency: bool
    debug_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compact_response_type_contract(contract: ResponseTypeContract | dict | None) -> dict[str, Any] | None:
    src = contract.to_dict() if isinstance(contract, ResponseTypeContract) else contract
    if not isinstance(src, dict):
        return None
    return {
        "required_response_type": src.get("required_response_type"),
        "source_route": src.get("source_route"),
        "allow_escalation": bool(src.get("allow_escalation")),
        "debug_reasons": list(src.get("debug_reasons") or []),
    }


def derive_response_type_contract(
    *,
    segmented_turn: dict | None,
    normalized_action: dict | None,
    resolution: dict | None,
    interaction_context: dict | None,
    directed_social_entry: dict | None = None,
    route_choice: str | None = None,
    raw_player_text: str | None = None,
) -> ResponseTypeContract:
    reasons: list[str] = []
    source_route = _resolve_source_route(
        segmented_turn=segmented_turn,
        normalized_action=normalized_action,
        resolution=resolution,
        interaction_context=interaction_context,
        directed_social_entry=directed_social_entry,
        route_choice=route_choice,
    )
    strict_target_id = _strict_target_id(
        resolution=resolution,
        interaction_context=interaction_context,
        directed_social_entry=directed_social_entry,
    )

    if _clean_str((resolution or {}).get("kind")).lower() == "adjudication_query":
        required_response_type: ResponseType = "answer"
        reasons.append("adjudication_query_requires_answer")
    elif _resolution_requires_dialogue(
        resolution=resolution,
        directed_social_entry=directed_social_entry,
        route_choice=route_choice,
        strict_target_id=strict_target_id,
    ):
        required_response_type = "dialogue"
        reasons.append("authoritative_social_target_requires_dialogue")
    else:
        resolution_kind = _clean_str((resolution or {}).get("kind")).lower()
        normalized_type = _clean_str((normalized_action or {}).get("type")).lower()
        route_choice_clean = _clean_str(route_choice).lower()
        if resolution_kind in _ACTION_OUTCOME_KINDS or normalized_type in _ACTION_OUTCOME_KINDS:
            required_response_type = "action_outcome"
            reasons.append("resolved_world_action_requires_action_outcome")
        elif route_choice_clean == "action":
            required_response_type = "action_outcome"
            reasons.append("action_route_requires_action_outcome")
        else:
            required_response_type = "neutral_narration"
            reasons.append("no_stricter_authoritative_contract")

    strict_answer_expected = _resolution_requires_answer(
        segmented_turn=segmented_turn,
        resolution=resolution,
        raw_player_text=raw_player_text,
    )
    if required_response_type == "dialogue" and strict_answer_expected:
        reasons.append("dialogue_turn_contains_question_expectation")

    guard_applies, block_reason = _non_hostile_guard_applies(
        segmented_turn=segmented_turn,
        normalized_action=normalized_action,
        resolution=resolution,
        raw_player_text=raw_player_text,
        required_response_type=required_response_type,
    )
    allow_escalation = not guard_applies
    if not allow_escalation and block_reason:
        reasons.append(block_reason)
    if allow_escalation:
        reasons.append("authoritative_state_allows_escalation")

    return ResponseTypeContract(
        required_response_type=required_response_type,
        source_route=source_route,
        allow_escalation=allow_escalation,
        escalation_block_reason=block_reason,
        strict_target_id=strict_target_id,
        strict_answer_expected=bool(strict_answer_expected),
        strict_dialogue_expected=required_response_type == "dialogue",
        action_must_preserve_agency=required_response_type == "action_outcome",
        debug_reasons=reasons,
    )
