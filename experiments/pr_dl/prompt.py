"""Compact non-authoritative interpretation prompt for PR-DL.

The model name, temperature, and Responses JSON-schema call shape follow
PR-DH. The PR-DH planner schema is not reused: it includes proposed_resolver,
advance_time, and expects_mutation, which this comparison forbids.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from experiments.pr_dj.adapter import ALLOWED_ENTITY_TYPES, ALLOWED_OPERATIONS, ALLOWED_STATUSES, FORBIDDEN_KEYS
from experiments.pr_dg.state import state_hash
from game.scene_referent_catalog import build_canonical_referent_catalog

OUTPUT_TOKEN_CAP = 400

_TYPE_MAP = {
    "place": "scene",
    "npc": "interlocutor",
    "character": "interlocutor",
}


def interpretation_schema() -> dict[str, Any]:
    nullable_string = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    entity = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "type": {"type": "string", "enum": sorted(ALLOWED_ENTITY_TYPES)},
        },
        "required": ["id", "type"],
    }
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"type": "string", "enum": sorted(ALLOWED_STATUSES)},
            "interpreted_intent": {"type": "string"},
            "referenced_entities": {"type": "array", "items": entity},
            "unresolved_references": {"type": "array", "items": {"type": "string"}},
            "multiple_action_components": {"type": "array", "items": {"type": "string"}},
            "clarification_required": {"type": "boolean"},
            "clarification_question": {"type": "string"},
            "unsupported_action": {"type": "string"},
            "non_authoritative_explanation": {"type": "string"},
            "primary_operation": {"type": "string", "enum": sorted(ALLOWED_OPERATIONS)},
            "supporting_operations": {
                "type": "array",
                "items": {"type": "string", "enum": sorted(ALLOWED_OPERATIONS)},
            },
            "proposed_target_id": nullable_string,
            "interlocutor_id": nullable_string,
            "ambiguous": {"type": "boolean"},
            },
        "required": [
            "status",
            "interpreted_intent",
            "referenced_entities",
            "unresolved_references",
            "multiple_action_components",
            "clarification_required",
            "clarification_question",
            "unsupported_action",
            "non_authoritative_explanation",
            "primary_operation",
            "supporting_operations",
            "proposed_target_id",
            "interlocutor_id",
            "ambiguous",
        ],
    }
    return schema


def _clean(value: Any, limit: int = 140) -> str:
    return " ".join(str(value or "").split())[:limit]


def _scene_body(scene: Mapping[str, Any]) -> Mapping[str, Any]:
    inner = scene.get("scene")
    return inner if isinstance(inner, Mapping) else scene


def _contains_hidden(text: str, hidden: list[str]) -> bool:
    haystack = text.casefold()
    return any(item and item.casefold() in haystack for item in hidden)


def permitted_entities(bundle: Any) -> list[dict[str, str]]:
    """Public ids and labels only. Hidden facts and mechanical numbers stay out."""
    scene_id = str((_scene_body(bundle.scene).get("id")) or bundle.session.get("active_scene_id") or "")
    catalog = build_canonical_referent_catalog(
        scene=bundle.scene,
        world=bundle.world,
        session=bundle.session,
        scene_id=scene_id,
    )
    hidden = [str(item) for item in bundle.hidden_strings if str(item).strip()]
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in catalog:
        if not isinstance(row, Mapping):
            continue
        entity_id = _clean(row.get("id"), 80)
        label = _clean(row.get("label"), 80)
        raw_type = str(row.get("type") or "")
        entity_type = _TYPE_MAP.get(raw_type, raw_type)
        if entity_type not in ALLOWED_ENTITY_TYPES or not entity_id:
            continue
        blob = f"{entity_id} {label}"
        if _contains_hidden(blob, hidden):
            continue
        if entity_id in seen:
            continue
        seen.add(entity_id)
        rows.append({"id": entity_id, "type": entity_type, "label": label})
    body = _scene_body(bundle.scene)
    for enemy in body.get("enemies") or []:
        if not isinstance(enemy, Mapping):
            continue
        entity_id = _clean(enemy.get("id"), 80)
        label = _clean(enemy.get("name") or enemy.get("label") or entity_id, 80)
        if not entity_id or entity_id in seen:
            continue
        if _contains_hidden(f"{entity_id} {label}", hidden):
            continue
        seen.add(entity_id)
        rows.append({"id": entity_id, "type": "enemy", "label": label})
    return rows


def visible_context(bundle: Any) -> dict[str, Any]:
    body = _scene_body(bundle.scene)
    hidden = [str(item) for item in bundle.hidden_strings if str(item).strip()]
    facts = []
    for item in body.get("visible_facts") or []:
        text = _clean(item, 90)
        if text and not _contains_hidden(text, hidden):
            facts.append(text)
        if len(facts) >= 2:
            break
    from experiments.pr_dg.state import state_tuple

    public = state_tuple(bundle)
    location = _clean(body.get("location") or body.get("name") or "", 80)
    if _contains_hidden(location, hidden):
        location = ""
    return {
        "scene_id": _clean(public.get("scene_id"), 80),
        "location": location,
        "visible_facts": facts,
        "active_interlocutor_id": public.get("interlocutor_id"),
    }


def build_messages(bundle: Any, utterance: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    entities = permitted_entities(bundle)
    context = visible_context(bundle)
    user = {
        "player_input": utterance,
        "visible_context": context,
        "permitted_entities": [{"id": row["id"], "type": row["type"], "label": row["label"]} for row in entities],
        "clarification_rules": [
            "Named people use a permitted id. Ambiguous pronouns need one clarification and no guessed id.",
            "A unique active interlocutor may resolve one singular pronoun.",
            "List each real attempted action. Quoted, negated, and hypothetical lines are not attempts.",
        ],
        "authority_restrictions": "Intent only. No outcomes, dice, HP, inventory, time, canon, NPC commitments, invented entities, or execution.",
    }
    messages = [
        {
            "role": "system",
            "content": (
                "Interpret one player utterance as non-authoritative JSON. "
                "You may identify intent, permitted entities, multiple actions, ambiguity, or unsupported intent, and you may ask one clarification or abstain. "
                "You may not determine outcomes, roll dice, assign HP, change inventory, advance time, establish canon, commit an NPC, invent an entity, or authorize execution."
            ),
        },
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]
    return messages, {
        "permitted_entities": entities,
        "visible_context": context,
        "state_hash": state_hash(bundle),
    }


def estimate_input_tokens(messages: list[dict[str, str]], schema: Mapping[str, Any]) -> int:
    """Conservative preflight. Overestimates relative to a bytes/4 tokenizer."""
    blob = json.dumps({"messages": messages, "schema": schema}, ensure_ascii=False).encode("utf-8")
    return max(1, (len(blob) // 3) + 64)


def hidden_leaks(messages: list[dict[str, str]], hidden: list[str]) -> list[str]:
    blob = json.dumps(messages, ensure_ascii=False).casefold()
    return [item for item in hidden if item and item.casefold() in blob]


def schema_is_non_authoritative(schema: Mapping[str, Any]) -> bool:
    keys = set(schema.get("properties") or {})
    return not (keys & FORBIDDEN_KEYS) and "status" in keys
