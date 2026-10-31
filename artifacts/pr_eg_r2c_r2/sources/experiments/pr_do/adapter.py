"""Non-executable adapter for the PR-DO interpretation contract.

The adapter checks structure and references. It stores claims as claims
and wished outcomes as wished outcomes. It does not mutate a world.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from experiments.pr_do.eligibility import evaluate_eligibility
from experiments.pr_do.schema import (
    ADJUDICATION_UNADJUDICATED,
    CANON_STATUS_PLAYER_CLAIM,
    COMMUNICATION_MODES,
    CORRECTION_SUBJECTS,
    FORBIDDEN_MODEL_KEYS,
    INTERPRETATION_STATUSES,
    MODEL_TOP_LEVEL,
    OPERATION_CLASSES,
)


def _walk_keys(value: Any, found: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in FORBIDDEN_MODEL_KEYS:
                found.append(str(key))
            _walk_keys(item, found)
    elif isinstance(value, list):
        for item in value:
            _walk_keys(item, found)


def _string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return None
    return [item.strip() for item in value if item.strip()]


def _validate(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return ["payload must be an object"]
    unknown = sorted(str(key) for key in payload if str(key) not in MODEL_TOP_LEVEL)
    if unknown:
        errors.append("unknown fields: " + ", ".join(unknown))
    forbidden: list[str] = []
    _walk_keys(payload, forbidden)
    if forbidden:
        errors.append("forbidden fields: " + ", ".join(sorted(set(forbidden))))
    if errors:
        return errors

    mode = payload.get("communication_mode")
    status = payload.get("interpretation_status")
    if mode not in COMMUNICATION_MODES:
        errors.append("communication_mode is not a known mode")
    if status not in INTERPRETATION_STATUSES:
        errors.append("interpretation_status is not a known status")

    intent = payload.get("player_intent")
    if not isinstance(intent, Mapping) or set(intent) != {"summary"} or not isinstance(intent.get("summary"), str):
        errors.append("player_intent.summary must be a string")

    premises = payload.get("asserted_premises")
    if not isinstance(premises, list):
        errors.append("asserted_premises must be an array")
    else:
        for index, row in enumerate(premises):
            if not isinstance(row, Mapping) or set(row) != {"text"} or not isinstance(row.get("text"), str):
                errors.append(f"asserted_premises[{index}] must contain only text")

    outcomes = payload.get("requested_outcomes")
    if not isinstance(outcomes, list):
        errors.append("requested_outcomes must be an array")
    else:
        for index, row in enumerate(outcomes):
            if not isinstance(row, Mapping) or set(row) != {"text"} or not isinstance(row.get("text"), str):
                errors.append(f"requested_outcomes[{index}] must contain only text")

    references = payload.get("references")
    declared: list[str] | None = None
    unresolved: list[str] | None = None
    if not isinstance(references, Mapping) or set(references) != {"permitted_entity_ids", "unresolved_references"}:
        errors.append("references must contain permitted ids and unresolved references")
    else:
        declared = _string_list(references.get("permitted_entity_ids"))
        unresolved = _string_list(references.get("unresolved_references"))
        if declared is None or unresolved is None:
            errors.append("reference lists must contain strings")

    components = payload.get("action_components")
    orders: list[int] = []
    if not isinstance(components, list):
        errors.append("action_components must be an array")
    else:
        for index, row in enumerate(components):
            if not isinstance(row, Mapping) or set(row) != {"order", "description", "target_ref", "operation_class"}:
                errors.append(f"action_components[{index}] has an unexpected shape")
                continue
            order = row.get("order")
            if not isinstance(order, int) or isinstance(order, bool) or order < 1:
                errors.append(f"action_components[{index}].order must be a positive integer")
            else:
                orders.append(order)
            if not isinstance(row.get("description"), str):
                errors.append(f"action_components[{index}].description must be a string")
            target = row.get("target_ref")
            if target is not None and not isinstance(target, str):
                errors.append(f"action_components[{index}].target_ref must be a string or null")
            if row.get("operation_class") not in OPERATION_CLASSES:
                errors.append(f"action_components[{index}].operation_class is unknown")
            if isinstance(target, str) and declared is not None and target.strip() not in declared:
                errors.append(f"action_components[{index}].target_ref is not among declared references")
        if len(orders) != len(set(orders)):
            errors.append("action component orders must be unique")

    if not isinstance(payload.get("clarification_question"), str):
        errors.append("clarification_question must be a string")
    correction = payload.get("correction")
    if not isinstance(correction, Mapping) or set(correction) != {"subject", "note"}:
        errors.append("correction must contain subject and note")
    elif correction.get("subject") not in CORRECTION_SUBJECTS or not isinstance(correction.get("note"), str):
        errors.append("correction subject is unknown or note is not a string")

    if status == "CLARIFICATION_REQUIRED":
        question = str(payload.get("clarification_question") or "").strip()
        unresolved_values = unresolved or []
        if not question and not unresolved_values:
            errors.append("clarification status requires a question or an unresolved reference")
    return errors


def _record(payload: Mapping[str, Any]) -> dict[str, Any]:
    components = sorted(payload["action_components"], key=lambda row: row["order"])
    return {
        "communication_mode": payload["communication_mode"],
        "interpretation_status": payload["interpretation_status"],
        "player_intent": {"summary": payload["player_intent"]["summary"]},
        "asserted_premises": [
            {"text": row["text"], "canon_status": CANON_STATUS_PLAYER_CLAIM}
            for row in payload["asserted_premises"]
        ],
        "requested_outcomes": [
            {"text": row["text"], "adjudication_status": ADJUDICATION_UNADJUDICATED}
            for row in payload["requested_outcomes"]
        ],
        "action_components": [
            {
                "order": row["order"],
                "description": row["description"],
                "target_ref": row["target_ref"],
                "operation_class": row["operation_class"],
            }
            for row in components
        ],
        "references": {
            "permitted_entity_ids": list(payload["references"]["permitted_entity_ids"]),
            "unresolved_references": list(payload["references"]["unresolved_references"]),
        },
        "clarification_question": payload["clarification_question"],
        "correction": {
            "subject": payload["correction"]["subject"],
            "note": payload["correction"]["note"],
        },
    }


def _abstain(errors: list[str]) -> dict[str, Any]:
    eligibility = evaluate_eligibility(
        communication_mode="OTHER",
        interpretation_status="ABSTAIN",
        operation_classes=(),
        target_ids=(),
        component_orders=(),
        unresolved_references=(),
        permitted_ids=set(),
        declared_ids=(),
        correction_subject="NONE",
        engine_channel=None,
    )
    eligibility["disposition"] = "SAFE_ABSTENTION"
    eligibility["reasons"] = ["schema_rejected"]
    eligibility["engine_submission"] = None
    eligibility["execution_authorized"] = False
    return {
        "structurally_valid": False,
        "errors": errors,
        "record": None,
        "eligibility": eligibility,
        "executed": False,
        "mutated_state": False,
        "live_provider_calls": 0,
        "authoritative_effects": [],
    }


def adapt_interpretation(
    payload: Mapping[str, Any] | None,
    *,
    permitted_ids: Sequence[str],
    engine_channel: str | None = None,
) -> dict[str, Any]:
    """Validate one interpretation and attach an engine-owned eligibility result.

    ``payload`` is not written back. No world object is accepted or returned.
    """
    if not isinstance(payload, Mapping):
        return _abstain(["payload must be an object"])
    errors = _validate(payload)
    if errors:
        return _abstain(errors)

    record = _record(payload)
    components = record["action_components"]
    eligibility = evaluate_eligibility(
        communication_mode=record["communication_mode"],
        interpretation_status=record["interpretation_status"],
        operation_classes=[row["operation_class"] for row in components],
        target_ids=[row["target_ref"] for row in components],
        component_orders=[row["order"] for row in components],
        unresolved_references=record["references"]["unresolved_references"],
        permitted_ids=set(permitted_ids),
        declared_ids=record["references"]["permitted_entity_ids"],
        correction_subject=record["correction"]["subject"],
        engine_channel=engine_channel,
    )
    return {
        "structurally_valid": True,
        "errors": [],
        "record": record,
        "eligibility": eligibility,
        "executed": False,
        "mutated_state": False,
        "live_provider_calls": 0,
        "authoritative_effects": [],
    }
