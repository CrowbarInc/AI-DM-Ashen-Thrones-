"""Deterministic translation of stored PR-DN outputs.

Old outputs are not treated as instances of the new schema. Missing
separations stay NOT REPRESENTABLE. No model reasoning is invented.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
STORED_RESULTS = ROOT / "artifacts" / "pr_dn_interpretation_robustness" / "raw_results.json"

LOST_INFORMATION = (
    "communication_mode",
    "asserted_premises",
    "requested_outcomes",
    "operation_class",
    "correction_subject",
)


def load_stored_rows() -> list[dict[str, Any]]:
    document = json.loads(STORED_RESULTS.read_text(encoding="utf-8"))
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("stored PR-DN results do not contain rows")
    return rows


def faithful_translation(row: Mapping[str, Any]) -> dict[str, Any]:
    """Copy only fields the old payload actually contains."""
    payload = row.get("live_payload")
    if not isinstance(payload, Mapping):
        return {
            "scenario_id": row.get("scenario_id"),
            "representable": False,
            "validation_outcome": "NOT_REPRESENTABLE",
            "submitted": False,
            "assumptions": [],
            "lost_information": list(LOST_INFORMATION),
            "original_model_output": None,
            "translated_representation": None,
        }
    components = payload.get("multiple_action_components")
    descriptions = [str(item) for item in components] if isinstance(components, list) else []
    entities = payload.get("referenced_entities")
    entity_ids = []
    if isinstance(entities, list):
        for entity in entities:
            if isinstance(entity, Mapping) and entity.get("id"):
                entity_ids.append(str(entity["id"]))
    unresolved = payload.get("unresolved_references")
    translated = {
        "communication_mode": "NOT_REPRESENTABLE",
        "interpretation_status": payload.get("status"),
        "player_intent": {"summary": payload.get("interpreted_intent")},
        "asserted_premises": "NOT_REPRESENTABLE",
        "requested_outcomes": "NOT_REPRESENTABLE",
        "action_components": [
            {
                "order": index + 1,
                "description": description,
                "operation_class": "NOT_REPRESENTABLE",
                "target_ref": "NOT_REPRESENTABLE",
            }
            for index, description in enumerate(descriptions)
        ],
        "references": {
            "entity_ids": entity_ids,
            "unresolved_references": list(unresolved) if isinstance(unresolved, list) else [],
        },
        "old_primary_operation": payload.get("primary_operation"),
        "old_unsupported_action": payload.get("unsupported_action"),
    }
    return {
        "scenario_id": row.get("scenario_id"),
        "representable": False,
        "validation_outcome": "NOT_REPRESENTABLE",
        "submitted": False,
        "executed": False,
        "assumptions": [],
        "lost_information": list(LOST_INFORMATION),
        "reason": "The old schema has no fields for communication mode, premises, requested outcomes, or operation class.",
        "original_model_output": dict(payload),
        "translated_representation": translated,
    }
