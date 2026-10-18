"""Non-authoritative interpretation adapter for PR-DJ.

The adapter validates hand-authored, model-shaped interpretation responses.
It never executes actions, selects outcomes, rolls dice, writes state, or
authorizes a resolver. Its output is an experiment record only.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence

from game.interpretation_proposal import (
    SOURCE_MODEL,
    InterpretationProposal,
    proposal_from_mapping,
    validate_interpretation_proposal,
)

STATUS_INTERPRETED = "INTERPRETED"
STATUS_CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
STATUS_UNSUPPORTED_REQUEST = "UNSUPPORTED_REQUEST"
STATUS_MULTI_ACTION = "MULTI_ACTION"
STATUS_ABSTAIN = "ABSTAIN"

ALLOWED_STATUSES = frozenset(
    {
        STATUS_INTERPRETED,
        STATUS_CLARIFICATION_REQUIRED,
        STATUS_UNSUPPORTED_REQUEST,
        STATUS_MULTI_ACTION,
        STATUS_ABSTAIN,
    }
)
ALLOWED_OPERATIONS = frozenset({"perceive", "inspect", "ask", "repeat", "confirm", "follow", "act", "unresolved"})
ALLOWED_ENTITY_TYPES = frozenset({"interlocutor", "object", "claim", "lead", "action", "enemy", "scene", "resolution_subject"})
ALLOWED_TOP_LEVEL = frozenset(
    {
        "status",
        "interpreted_intent",
        "referenced_entities",
        "unresolved_references",
        "multiple_action_components",
        "clarification_required",
        "clarification_question",
        "unsupported_action",
        "uncertainty",
        "non_authoritative_explanation",
        "primary_operation",
        "supporting_operations",
        "raw_target_text",
        "proposed_target_id",
        "interlocutor_id",
        "conversational_subject",
        "dimension",
        "dimensions",
        "expected_resolution",
        "referenced_claim_id",
        "referenced_action_id",
        "referenced_inspected_id",
        "ambiguous",
        "confidence",
    }
)

FORBIDDEN_KEYS = frozenset(
    {
        "authoritative_outcome",
        "outcome",
        "dice_result",
        "dice_results",
        "roll",
        "rolls",
        "hp",
        "hit_points",
        "damage",
        "damage_dealt",
        "inventory",
        "inventory_mutations",
        "world_flags",
        "hidden_facts",
        "hidden_information",
        "execute",
        "execution",
        "execute_action",
        "authorized",
        "authorize_execution",
        "resolver",
        "proposed_resolver",
        "selected_resolver",
        "state_patch",
        "state_mutation",
        "scene_patch",
        "npc_commitments",
    }
)


@dataclass(frozen=True)
class InterpretationAdapterResult:
    accepted: bool
    status: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    proposal: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    clarification: str | None = None
    unresolved_references: tuple[str, ...] = ()
    multiple_action_components: tuple[str, ...] = ()
    unsupported_action: str | None = None
    non_authoritative: bool = True
    executed: bool = False
    mutated_state: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "status": self.status,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "proposal": deepcopy(self.proposal),
            "validation": deepcopy(self.validation),
            "clarification": self.clarification,
            "unresolved_references": list(self.unresolved_references),
            "multiple_action_components": list(self.multiple_action_components),
            "unsupported_action": self.unsupported_action,
            "non_authoritative": self.non_authoritative,
            "executed": self.executed,
            "mutated_state": self.mutated_state,
        }


def _reject(status: str, *errors: str, warnings: Sequence[str] = ()) -> InterpretationAdapterResult:
    return InterpretationAdapterResult(False, status, tuple(errors), tuple(warnings))


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _walk_forbidden(value: Any, *, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_KEYS:
                found.append(f"{path}.{key_text}")
            found.extend(_walk_forbidden(item, path=f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk_forbidden(item, path=f"{path}[{index}]"))
    return found


def _known_ids(canonical_referents: Sequence[Mapping[str, Any]] | None) -> set[str]:
    ids: set[str] = set()
    for row in canonical_referents or ():
        if isinstance(row, Mapping) and str(row.get("id") or "").strip():
            ids.add(str(row["id"]))
    return ids


def _validate_referenced_entities(payload: Mapping[str, Any], canonical_referents: Sequence[Mapping[str, Any]] | None) -> list[str]:
    errors: list[str] = []
    known = _known_ids(canonical_referents)
    entities = payload.get("referenced_entities")
    if entities is None:
        return errors
    if not isinstance(entities, list):
        return ["referenced_entities must be an array"]
    for index, row in enumerate(entities):
        if not isinstance(row, Mapping):
            errors.append(f"referenced_entities[{index}] must be an object")
            continue
        entity_id = str(row.get("id") or "").strip()
        entity_type = str(row.get("type") or "").strip()
        if entity_type and entity_type not in ALLOWED_ENTITY_TYPES:
            errors.append(f"referenced_entities[{index}].type is unsupported: {entity_type}")
        if entity_id and known and entity_id not in known:
            errors.append(f"referenced_entities[{index}].id is not canonical: {entity_id}")
    return errors


def _proposal_payload(payload: Mapping[str, Any], raw_input: str) -> dict[str, Any]:
    components = _strings(payload.get("multiple_action_components"))
    supporting = payload.get("supporting_operations")
    if supporting is None and len(components) > 1:
        supporting = ["act" for _ in components]
    return {
        "raw_input": raw_input,
        "source": SOURCE_MODEL,
        "primary_operation": payload.get("primary_operation"),
        "supporting_operations": supporting or [],
        "raw_target_text": payload.get("raw_target_text"),
        "proposed_target_id": payload.get("proposed_target_id"),
        "interlocutor_id": payload.get("interlocutor_id"),
        "conversational_subject": payload.get("conversational_subject"),
        "dimension": payload.get("dimension"),
        "dimensions": payload.get("dimensions") or [],
        "expected_resolution": payload.get("expected_resolution"),
        "referenced_claim_id": payload.get("referenced_claim_id"),
        "referenced_action_id": payload.get("referenced_action_id"),
        "referenced_inspected_id": payload.get("referenced_inspected_id"),
        "clarification_required": bool(payload.get("clarification_required")),
        "ambiguous": bool(payload.get("ambiguous")),
        "confidence": payload.get("confidence"),
    }


def _status_consistency_errors(payload: Mapping[str, Any], status: str) -> list[str]:
    errors: list[str] = []
    components = _strings(payload.get("multiple_action_components"))
    question = str(payload.get("clarification_question") or "").strip()
    unsupported = str(payload.get("unsupported_action") or "").strip()
    if status == STATUS_CLARIFICATION_REQUIRED and not question:
        errors.append("clarification status requires clarification_question")
    if status == STATUS_MULTI_ACTION and len(components) < 2:
        errors.append("multi-action status requires at least two action components")
    if status == STATUS_UNSUPPORTED_REQUEST and not unsupported:
        errors.append("unsupported status requires unsupported_action")
    if payload.get("clarification_required") and not question:
        errors.append("clarification_required requires clarification_question")
    intent_surface = " ".join(
        str(payload.get(key) or "")
        for key in ("interpreted_intent", "raw_target_text", "conversational_subject")
    )
    has_silent_guess = bool(
        status == STATUS_INTERPRETED
        and not payload.get("clarification_required")
        and not payload.get("ambiguous")
        and re.search(r"\b(?:him|her|them|it|that|this|other one)\b", intent_surface, re.IGNORECASE)
    )
    if has_silent_guess:
        errors.append("ambiguous references may not be silently resolved")
    return errors


def validate_hand_authored_interpretation(
    payload: Mapping[str, Any],
    *,
    raw_input: str,
    discourse_focus: Mapping[str, Any] | None = None,
    canonical_referents: Sequence[Mapping[str, Any]] | None = None,
) -> InterpretationAdapterResult:
    """Validate a bounded interpretation payload.

    The payload is accepted only as experiment evidence. The returned object
    deliberately contains no execution request or resolver authorization.
    """
    if not isinstance(payload, Mapping):
        return _reject(STATUS_ABSTAIN, "payload must be an object")
    unknown_top = sorted(str(key) for key in payload if str(key) not in ALLOWED_TOP_LEVEL)
    if unknown_top:
        return _reject(STATUS_ABSTAIN, f"unknown fields are not allowed: {', '.join(unknown_top)}")
    forbidden = _walk_forbidden(payload)
    if forbidden:
        return _reject(STATUS_ABSTAIN, f"authoritative fields are forbidden: {', '.join(forbidden)}")

    status = str(payload.get("status") or "").strip()
    if status not in ALLOWED_STATUSES:
        return _reject(STATUS_ABSTAIN, f"status must be one of {sorted(ALLOWED_STATUSES)}")

    consistency = _status_consistency_errors(payload, status)
    entity_errors = _validate_referenced_entities(payload, canonical_referents)
    if consistency or entity_errors:
        return _reject(status, *(consistency + entity_errors))

    operation = payload.get("primary_operation")
    if operation is not None and str(operation) not in ALLOWED_OPERATIONS:
        return _reject(status, f"primary_operation is unsupported: {operation}")
    supporting = payload.get("supporting_operations") or []
    if not isinstance(supporting, list):
        return _reject(status, "supporting_operations must be an array")
    bad_supporting = [str(item) for item in supporting if str(item) not in ALLOWED_OPERATIONS]
    if bad_supporting:
        return _reject(status, f"supporting_operations include unsupported operations: {', '.join(bad_supporting)}")

    try:
        proposal: InterpretationProposal = proposal_from_mapping(_proposal_payload(payload, raw_input))
        validation = validate_interpretation_proposal(
            proposal,
            discourse_focus=discourse_focus,
            canonical_referents=canonical_referents,
        )
    except Exception as exc:  # noqa: BLE001 - malformed hand-authored controls are test data
        return _reject(status, f"malformed structured output: {type(exc).__name__}: {exc}")

    errors: list[str] = []
    if status == STATUS_INTERPRETED and validation.status != "validated":
        errors.append(f"interpreted status did not validate: {validation.reason}")
    if status == STATUS_ABSTAIN and validation.status == "validated" and not payload.get("uncertainty"):
        errors.append("abstain requires uncertainty when the underlying proposal validates")
    if errors:
        return _reject(status, *errors)

    return InterpretationAdapterResult(
        accepted=True,
        status=status,
        proposal=proposal.as_dict(),
        validation=validation.as_dict(),
        clarification=str(payload.get("clarification_question") or "").strip() or None,
        unresolved_references=_strings(payload.get("unresolved_references")),
        multiple_action_components=_strings(payload.get("multiple_action_components")),
        unsupported_action=str(payload.get("unsupported_action") or "").strip() or None,
    )
