"""Engine-owned execution eligibility.

This function does not read model-authored sentences. Callers pass closed
enums, identifiers, and statuses only. ELIGIBLE_FOR_VALIDATION is not
permission to execute.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from experiments.pr_do.schema import (
    UNSUPPORTED_OPERATION_CLASSES,
    VALIDATION_ALLOWLIST,
)

ELIGIBLE = "ELIGIBLE_FOR_VALIDATION"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
UNSUPPORTED = "UNSUPPORTED_OPERATION"
OUT_OF_CHARACTER = "OUT_OF_CHARACTER"
ABSTAIN = "SAFE_ABSTENTION"

_OOC_MODES = frozenset({"OUT_OF_CHARACTER_CORRECTION", "RULES_QUESTION"})


def _base(**extra: object) -> dict:
    result = {
        "disposition": ABSTAIN,
        "execution_authorized": False,
        "executed": False,
        "mutated_state": False,
        "consumes_action": False,
        "advances_time": False,
        "creates_npc_response": False,
        "history_rewritten": False,
        "history_disposition": "UNCHANGED",
        "rolls_dice": False,
        "reveals_hidden_information": False,
        "engine_submission": None,
        "rejected_identifiers": [],
        "reasons": [],
        "compound_transaction": False,
        "authoritative_effects": [],
    }
    result.update(extra)
    return result


def _submission(classes: Sequence[str], targets: Sequence[str], orders: Sequence[int]) -> dict:
    return {
        "disposition": ELIGIBLE,
        "execution_authorized": False,
        "operation_classes": list(classes),
        "target_ids": list(targets),
        "component_orders": list(orders),
        "compound_transaction": False,
        "includes_model_text": False,
        "includes_asserted_premises": False,
        "includes_requested_outcomes": False,
    }


def evaluate_eligibility(
    *,
    communication_mode: str,
    interpretation_status: str,
    operation_classes: Sequence[str],
    target_ids: Sequence[str | None],
    component_orders: Sequence[int],
    unresolved_references: Sequence[str],
    permitted_ids: set[str],
    declared_ids: Sequence[str],
    correction_subject: str,
    engine_channel: str | None,
) -> dict:
    """Decide whether a structured attempt may be offered to the engine.

    The return value never authorizes execution.
    """
    rejected = [entity_id for entity_id in declared_ids if entity_id not in permitted_ids]
    classes = list(operation_classes)
    targets = [entity_id for entity_id in target_ids if entity_id]
    orders = list(component_orders)
    history = "ADJUDICATION_REQUIRED" if correction_subject == "COMMITTED_ACTION" else "UNCHANGED"
    channel = engine_channel or ""

    if channel == "OUT_OF_CHARACTER_CORRECTION" or communication_mode in _OOC_MODES:
        return _base(
            disposition=OUT_OF_CHARACTER,
            history_disposition=history,
            rejected_identifiers=rejected,
            reasons=["communication_outside_world_action"],
        )

    if any(item in UNSUPPORTED_OPERATION_CLASSES for item in classes) or interpretation_status == "UNSUPPORTED_REQUEST":
        return _base(
            disposition=UNSUPPORTED,
            rejected_identifiers=rejected,
            reasons=["unsupported_or_unauthorized_operation_class"],
        )

    if interpretation_status == "ABSTAIN" or communication_mode == "OTHER":
        return _base(
            disposition=ABSTAIN,
            rejected_identifiers=rejected,
            reasons=["abstain_or_other"],
        )

    needs_clarification = (
        communication_mode == "CLARIFICATION"
        or interpretation_status == "CLARIFICATION_REQUIRED"
        or bool(unresolved_references)
        or bool(rejected)
        or any(entity_id not in permitted_ids for entity_id in targets)
    )
    if needs_clarification:
        return _base(
            disposition=NEEDS_CLARIFICATION,
            rejected_identifiers=rejected,
            reasons=["clarification_or_unresolved_reference"],
        )

    if not classes or any(item not in VALIDATION_ALLOWLIST for item in classes):
        return _base(
            disposition=ABSTAIN,
            rejected_identifiers=rejected,
            reasons=["no_allowlisted_operation_class"],
        )

    if communication_mode != "IN_WORLD_ACTION" or interpretation_status != "INTERPRETED":
        return _base(
            disposition=ABSTAIN,
            rejected_identifiers=rejected,
            reasons=["not_an_interpreted_in_world_action"],
        )

    return _base(
        disposition=ELIGIBLE,
        rejected_identifiers=rejected,
        reasons=["allowlisted_attempt_awaits_engine_validation"],
        engine_submission=_submission(classes, targets, orders),
    )


def submission_strings(submission: Mapping[str, object] | None) -> list[str]:
    found: list[str] = []
    if not isinstance(submission, Mapping):
        return found

    def walk(value: object) -> None:
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, Mapping):
            for key, item in value.items():
                found.append(str(key))
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(dict(submission))
    return found
