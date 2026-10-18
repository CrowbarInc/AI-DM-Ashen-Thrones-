"""Compact serialization of the PR-DO contract. The contract enums are unchanged."""

from __future__ import annotations

import json
from typing import Any

from experiments.pr_do.schema import (
    FORBIDDEN_MODEL_KEYS,
    MODEL_TOP_LEVEL,
    schema_document,
    schema_grants_execution,
)
from experiments.pr_dp.scenarios import CONTEXT, VISIBLE_ENTITIES

HIDDEN_PROBES = (
    "secret tunnel",
    "hit points",
    "hidden enemies",
    "patrol route",
    "owes me a favor",
)


def provider_schema() -> dict[str, Any]:
    """JSON Schema for the model-writable PR-DO object.

    ``not_model_writable`` is documentation in schema_document(). It is not a
    model field and not a JSON Schema keyword, so it is omitted here. Property
    names, enums, and required fields are copied unchanged.
    """
    document = schema_document()
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": document["properties"],
        "required": list(document["required"]),
    }


def contract_issues() -> list[str]:
    """Return internal contradictions. An empty list means the contract can be serialized."""
    from experiments.pr_do.eligibility import (
        ABSTAIN,
        ELIGIBLE,
        NEEDS_CLARIFICATION,
        OUT_OF_CHARACTER,
        UNSUPPORTED,
    )
    from experiments.pr_do.schema import (
        COMMUNICATION_MODES,
        CORRECTION_SUBJECTS,
        DISPOSITIONS,
        INTERPRETATION_STATUSES,
        OPERATION_CLASSES,
        UNSUPPORTED_OPERATION_CLASSES,
        VALIDATION_ALLOWLIST,
    )

    issues: list[str] = []
    document = schema_document()
    properties = document.get("properties") or {}
    if set(properties) != set(MODEL_TOP_LEVEL):
        issues.append("schema properties do not match MODEL_TOP_LEVEL")
    if set(document.get("required") or []) != set(MODEL_TOP_LEVEL):
        issues.append("schema required fields do not match MODEL_TOP_LEVEL")
    if schema_grants_execution(document):
        issues.append("schema_document grants execution")
    if set(properties) & FORBIDDEN_MODEL_KEYS:
        issues.append("a forbidden key is a model-writable property")
    if VALIDATION_ALLOWLIST & UNSUPPORTED_OPERATION_CLASSES:
        issues.append("allowlist overlaps unsupported operation classes")
    if OPERATION_CLASSES != (VALIDATION_ALLOWLIST | UNSUPPORTED_OPERATION_CLASSES):
        issues.append("OPERATION_CLASSES is not the union of allowlist and unsupported classes")
    component_enum = set(
        properties["action_components"]["items"]["properties"]["operation_class"]["enum"]
    )
    if component_enum != set(OPERATION_CLASSES):
        issues.append("component operation_class enum does not match OPERATION_CLASSES")
    mode_enum = set(properties["communication_mode"]["enum"])
    if mode_enum != set(COMMUNICATION_MODES):
        issues.append("communication_mode enum drifted")
    status_enum = set(properties["interpretation_status"]["enum"])
    if status_enum != set(INTERPRETATION_STATUSES):
        issues.append("interpretation_status enum drifted")
    correction_enum = set(properties["correction"]["properties"]["subject"]["enum"])
    if correction_enum != set(CORRECTION_SUBJECTS):
        issues.append("correction subject enum drifted")
    expected_dispositions = {ELIGIBLE, NEEDS_CLARIFICATION, UNSUPPORTED, OUT_OF_CHARACTER, ABSTAIN}
    if set(DISPOSITIONS) != expected_dispositions:
        issues.append("disposition enum does not match eligibility constants")
    provider = provider_schema()
    if schema_grants_execution(provider):
        issues.append("provider schema grants execution")
    if set(provider["properties"]) & FORBIDDEN_MODEL_KEYS:
        issues.append("provider schema exposes a forbidden key")
    if "not_model_writable" in provider:
        issues.append("provider schema includes the documentation key")
    return issues


def build_messages(utterance: str) -> list[dict[str, str]]:
    from experiments.pr_do.schema import UNSUPPORTED_OPERATION_CLASSES, VALIDATION_ALLOWLIST

    visible = "; ".join(f"{entity_id}={label}" for entity_id, label in VISIBLE_ENTITIES)
    user = "\n".join(
        [
            f"Utterance: {utterance}",
            f"Visible only: {visible}.",
            CONTEXT,
            "Later validation, not authorization: " + ", ".join(sorted(VALIDATION_ALLOWLIST)) + ".",
            "Ineligible: " + ", ".join(sorted(UNSUPPORTED_OPERATION_CLASSES)) + ".",
            "Ambiguous person or object: unresolved_references, CLARIFICATION_REQUIRED, one question, no guessed id.",
            "Premises and wished results are text. No outcomes, HP, dice, inventory, time, canon, NPC commitments, hidden facts, or execution.",
            "Order attempts. Empty list or string if unused.",
        ]
    )
    return [
        {"role": "system", "content": "Fill the schema. Describe the attempt. Do not authorize execution."},
        {"role": "user", "content": user},
    ]


def estimate_input_tokens(messages: list[dict[str, str]], schema: dict[str, Any]) -> int:
    """Conservative preflight. Overestimates a bytes/4 tokenizer by using bytes/3."""
    blob = json.dumps({"messages": messages, "schema": schema}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return max(1, (len(blob) // 3) + 64)


def hidden_leaks(messages: list[dict[str, str]]) -> list[str]:
    blob = json.dumps(messages, ensure_ascii=False).casefold()
    return [item for item in HIDDEN_PROBES if item.casefold() in blob]
