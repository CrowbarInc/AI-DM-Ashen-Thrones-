"""Model-facing interpretation schema for PR-DO.

The model may describe an attempt. It may not grant execution.
Closed enums classify the attempt. Free text stays descriptive.
"""

from __future__ import annotations

COMMUNICATION_MODES = frozenset(
    {
        "IN_WORLD_ACTION",
        "OUT_OF_CHARACTER_CORRECTION",
        "RULES_QUESTION",
        "CLARIFICATION",
        "OTHER",
    }
)

INTERPRETATION_STATUSES = frozenset(
    {
        "INTERPRETED",
        "CLARIFICATION_REQUIRED",
        "UNSUPPORTED_REQUEST",
        "ABSTAIN",
    }
)

# Classes the engine may later validate. Eligibility is not execution.
VALIDATION_ALLOWLIST = frozenset(
    {
        "MOVE",
        "ATTACK",
        "INSPECT",
        "ASK",
        "SOCIAL_SIGNAL",
        "PERCEIVE",
        "FOLLOW",
        "USE_VISIBLE_OBJECT",
    }
)

UNSUPPORTED_OPERATION_CLASSES = frozenset(
    {
        "HP_ASSIGNMENT",
        "DICE_OVERRIDE",
        "INVENTORY_GRANT",
        "CANON_DECLARATION",
        "NPC_COMMITMENT",
        "HIDDEN_INFORMATION_REQUEST",
        "RETCON",
        "UNSUPPORTED_MECHANIC",
        "TIME_CONTROL",
        "STEALTH_MODE_TOGGLE",
    }
)

OPERATION_CLASSES = VALIDATION_ALLOWLIST | UNSUPPORTED_OPERATION_CLASSES

CORRECTION_SUBJECTS = frozenset({"NONE", "REFERENT", "INTENTION", "COMMITTED_ACTION"})

DISPOSITIONS = frozenset(
    {
        "ELIGIBLE_FOR_VALIDATION",
        "NEEDS_CLARIFICATION",
        "UNSUPPORTED_OPERATION",
        "OUT_OF_CHARACTER",
        "SAFE_ABSTENTION",
    }
)

# Exact key names only. This is not a prose blacklist.
FORBIDDEN_MODEL_KEYS = frozenset(
    {
        "authoritative_outcome",
        "authoritative_operation",
        "authorized",
        "authorize_execution",
        "execution",
        "execution_authorized",
        "execution_eligibility",
        "execute",
        "execute_action",
        "hp",
        "hit_points",
        "damage",
        "damage_dealt",
        "dice_result",
        "dice_results",
        "roll",
        "rolls",
        "inventory",
        "inventory_mutations",
        "world_flags",
        "state_patch",
        "state_mutation",
        "scene_patch",
        "hidden_facts",
        "hidden_information",
        "hidden_enemies",
        "npc_commitments",
        "canon",
        "canon_status",
        "adjudication_status",
        "discourse_commit_allowed",
        "resolver",
        "proposed_resolver",
        "selected_resolver",
        "advance_time",
        "expects_mutation",
    }
)

MODEL_TOP_LEVEL = frozenset(
    {
        "communication_mode",
        "interpretation_status",
        "player_intent",
        "asserted_premises",
        "requested_outcomes",
        "action_components",
        "references",
        "clarification_question",
        "correction",
    }
)

CANON_STATUS_PLAYER_CLAIM = "PLAYER_CLAIM"
ADJUDICATION_UNADJUDICATED = "UNADJUDICATED"


def schema_document() -> dict:
    """JSON-schema-shaped description. Validation is implemented in the adapter."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "communication_mode": {"enum": sorted(COMMUNICATION_MODES)},
            "interpretation_status": {"enum": sorted(INTERPRETATION_STATUSES)},
            "player_intent": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            },
            "asserted_premises": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            },
            "requested_outcomes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            },
            "action_components": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "order": {"type": "integer"},
                        "description": {"type": "string"},
                        "target_ref": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "operation_class": {"enum": sorted(OPERATION_CLASSES)},
                    },
                    "required": ["order", "description", "target_ref", "operation_class"],
                },
            },
            "references": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "permitted_entity_ids": {"type": "array", "items": {"type": "string"}},
                    "unresolved_references": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["permitted_entity_ids", "unresolved_references"],
            },
            "clarification_question": {"type": "string"},
            "correction": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "subject": {"enum": sorted(CORRECTION_SUBJECTS)},
                    "note": {"type": "string"},
                },
                "required": ["subject", "note"],
            },
        },
        "required": sorted(MODEL_TOP_LEVEL),
        "not_model_writable": [
            "execution_eligibility",
            "execution_authorized",
            "canon_status",
            "adjudication_status",
            "engine_submission",
        ],
    }


def schema_grants_execution(schema: dict) -> bool:
    properties = schema.get("properties") or {}
    return bool(set(properties) & FORBIDDEN_MODEL_KEYS) or "execution_eligibility" in properties
