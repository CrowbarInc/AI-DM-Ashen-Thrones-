"""Replay helpers. No provider calls and no state writes."""

from __future__ import annotations

import json
from typing import Any

from experiments.pr_do.adapter import adapt_interpretation
from experiments.pr_do.eligibility import submission_strings
from experiments.pr_do.fixtures import adversarial_cases, contract_cases
from experiments.pr_do.schema import FORBIDDEN_MODEL_KEYS, VALIDATION_ALLOWLIST

_EFFECT_KEYS = FORBIDDEN_MODEL_KEYS - {"canon_status", "adjudication_status", "execution_authorized"}
from experiments.pr_do.translate import faithful_translation, load_stored_rows

_SUBMISSION_KEYS = {
    "ELIGIBLE_FOR_VALIDATION",
    "disposition",
    "execution_authorized",
    "operation_classes",
    "target_ids",
    "component_orders",
    "compound_transaction",
    "includes_model_text",
    "includes_asserted_premises",
    "includes_requested_outcomes",
}


def _model_strings(record: dict[str, Any] | None) -> list[str]:
    if not record:
        return []
    found = [record["player_intent"]["summary"]]
    found.extend(row["text"] for row in record["asserted_premises"])
    found.extend(row["text"] for row in record["requested_outcomes"])
    found.extend(row["description"] for row in record["action_components"])
    found.append(record["clarification_question"])
    found.append(record["correction"]["note"])
    return [item for item in found if item]


def _keys(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.append(str(key))
            found.extend(_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_keys(item))
    return found


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = adapt_interpretation(
        case["payload"],
        permitted_ids=case["permitted_ids"],
        engine_channel=case.get("engine_channel"),
    )
    eligibility = result["eligibility"]
    submission = eligibility["engine_submission"]
    strings = submission_strings(submission)
    leaked = [
        text
        for text in _model_strings(result["record"])
        if any(text == item for item in strings)
    ]
    allowed = set(VALIDATION_ALLOWLIST) | set(case["permitted_ids"]) | _SUBMISSION_KEYS
    token_leak = [item for item in strings if item not in allowed]
    return {
        "case_id": case["case_id"],
        "structurally_valid": result["structurally_valid"],
        "disposition": eligibility["disposition"],
        "execution_authorized": eligibility["execution_authorized"],
        "executed": result["executed"],
        "mutated_state": result["mutated_state"],
        "consumes_action": eligibility["consumes_action"],
        "advances_time": eligibility["advances_time"],
        "creates_npc_response": eligibility["creates_npc_response"],
        "history_rewritten": eligibility["history_rewritten"],
        "history_disposition": eligibility["history_disposition"],
        "rolls_dice": eligibility["rolls_dice"],
        "reveals_hidden_information": eligibility["reveals_hidden_information"],
        "compound_transaction": eligibility["compound_transaction"],
        "engine_submission": submission,
        "model_text_in_submission": leaked,
        "unexpected_submission_tokens": token_leak,
        "forbidden_keys_in_result": sorted(set(_keys(result)) & _EFFECT_KEYS),
        "canon_statuses": [row["canon_status"] for row in (result["record"] or {}).get("asserted_premises", [])],
        "adjudication_statuses": [
            row["adjudication_status"] for row in (result["record"] or {}).get("requested_outcomes", [])
        ],
        "component_orders": [row["order"] for row in (result["record"] or {}).get("action_components", [])],
        "operation_classes": [row["operation_class"] for row in (result["record"] or {}).get("action_components", [])],
        "live_provider_calls": result["live_provider_calls"],
        "authoritative_effects": result["authoritative_effects"],
    }


def replay_contract() -> list[dict[str, Any]]:
    return [evaluate_case(case) for case in contract_cases()]


def replay_adversarial() -> list[dict[str, Any]]:
    return [evaluate_case(case) for case in adversarial_cases()]


def replay_translations() -> list[dict[str, Any]]:
    return [faithful_translation(row) for row in load_stored_rows()]


def dump_replay() -> str:
    return json.dumps(
        {
            "contract": replay_contract(),
            "adversarial": replay_adversarial(),
            "translations": [
                {
                    "scenario_id": row["scenario_id"],
                    "validation_outcome": row["validation_outcome"],
                    "submitted": row["submitted"],
                    "lost_information": row["lost_information"],
                }
                for row in replay_translations()
            ],
        },
        indent=2,
    )
