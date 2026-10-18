"""Consumption-time authority guard for non-authoritative interpretations.

Schema acceptance is not authority. A rejected payload is evidence only:
the guard never executes a plan and never writes world state.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

DIRECT_HP = "direct_hp_assignment"
INVENTED_FACT = "invented_world_fact"
CANON_UPDATE = "unauthorized_canon_update"
DICE = "fabricated_dice_outcome"
INVENTED_ID = "invented_entity_identifier"
NPC_COMMITMENT = "unauthorized_npc_commitment"
INVENTORY = "direct_inventory_mutation"
EXECUTION = "unrestricted_execution_request"
HIDDEN = "hidden_information_assertion"
UNSUPPORTED_OP = "unsupported_authoritative_operation"

FORBIDDEN_KEY_CODES = {
    "hp": DIRECT_HP,
    "hit_points": DIRECT_HP,
    "damage": DIRECT_HP,
    "damage_dealt": DIRECT_HP,
    "dice_result": DICE,
    "dice_results": DICE,
    "roll": DICE,
    "rolls": DICE,
    "inventory": INVENTORY,
    "inventory_mutations": INVENTORY,
    "world_flags": CANON_UPDATE,
    "state_patch": CANON_UPDATE,
    "state_mutation": CANON_UPDATE,
    "scene_patch": CANON_UPDATE,
    "hidden_facts": HIDDEN,
    "hidden_information": HIDDEN,
    "execute": EXECUTION,
    "execution": EXECUTION,
    "execute_action": EXECUTION,
    "authorized": EXECUTION,
    "authorize_execution": EXECUTION,
    "npc_commitments": NPC_COMMITMENT,
    "authoritative_outcome": UNSUPPORTED_OP,
    "outcome": UNSUPPORTED_OP,
}

_HP = re.compile(
    r"\bhit\s+points?\b.{0,24}\b(?:to|at|are|is)\s+(?:zero|0|\d+)\b"
    r"|\b(?:set|assign|reduce|drop)\b.{0,40}\bhit\s+points?\b"
    r"|\bhp\s+(?:to|is|are)\s+(?:zero|0|\d+)\b",
    re.IGNORECASE,
)
_DICE = re.compile(
    r"\bnatural\s+20\b|\brolled\s+(?:a\s+)?\d+\b|\b(?:the|your)\s+roll\s+is\b|\bdice\s+result\b",
    re.IGNORECASE,
)
_CANON = re.compile(
    r"\bupdate\s+(?:the\s+)?world\b|\bestablished\s+facts?\b|\bthat\s+is\s+a\s+fact\b"
    r"|\bis\s+now\s+open\b|\bworld\s+state\b",
    re.IGNORECASE,
)
_NPC = re.compile(
    r"\b(?:secretly\s+)?agrees\s+to\b|\bpromises\s+to\b|\bcommits\s+to\b|\bwill\s+betray\b",
    re.IGNORECASE,
)
_INVENTORY = re.compile(
    r"\binventory\b|\bgive\s+(?:me|the\s+player)\s+the\b|\byou\s+(?:now\s+)?(?:receive|have)\s+the\b"
    r"|\badd\b.{0,40}\binventory\b",
    re.IGNORECASE,
)
_EXECUTION = re.compile(
    r"\bexecute(?:\s+the)?\s+action\b|\bauthorize[sd]?\s+execution\b|\bapply\s+the\s+(?:change|outcome)\b",
    re.IGNORECASE,
)
_HIDDEN = re.compile(
    r"\breveal(?:ing|ed)?\s+(?:the\s+)?spy\b|\bhidden\s+motives?\b|\bevery\s+hidden\b",
    re.IGNORECASE,
)
_UNSUPPORTED_OP = re.compile(
    r"\b(?:give|grant)(?:\s+\w+){0,3}\s+advantage\b|\bmark\w*\b.{0,40}\bfound\b",
    re.IGNORECASE,
)
_COMPLETED = re.compile(
    r"\bhit\s+points?\s+(?:are|is)\s+(?:now\s+)?(?:zero|0|\d+)\b|\bhp\s+is\s+now\b"
    r"|\bthe\s+roll\s+is\b|\badvantage\s+(?:is|was)\s+granted\b|\bthe\s+tunnel\s+is\s+now\s+open\b"
    r"|\bpatrol\s+(?:is|was)\s+found\b",
    re.IGNORECASE,
)

_TEXT_FIELDS = (
    "interpreted_intent",
    "clarification_question",
    "unsupported_action",
    "uncertainty",
    "non_authoritative_explanation",
    "raw_target_text",
    "conversational_subject",
)


def _proposing(payload: Mapping[str, Any]) -> bool:
    status = str(payload.get("status") or "")
    if status in {"UNSUPPORTED_REQUEST", "ABSTAIN"}:
        return False
    if str(payload.get("unsupported_action") or "").strip():
        return False
    return True


def _blob(payload: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in _TEXT_FIELDS:
        parts.append(str(payload.get(key) or ""))
    for key in ("multiple_action_components", "unresolved_references"):
        values = payload.get(key) or []
        if isinstance(values, list):
            parts.extend(str(item) for item in values)
    return " ".join(parts)


def _walk_keys(value: Any, found: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            code = FORBIDDEN_KEY_CODES.get(str(key))
            if code:
                found.append(code)
            _walk_keys(item, found)
    elif isinstance(value, list):
        for item in value:
            _walk_keys(item, found)


def _ids(payload: Mapping[str, Any]) -> list[str]:
    found: list[str] = []
    entities = payload.get("referenced_entities") or []
    if isinstance(entities, list):
        for row in entities:
            if isinstance(row, Mapping) and str(row.get("id") or "").strip():
                found.append(str(row["id"]).strip())
    for key in ("proposed_target_id", "interlocutor_id", "referenced_claim_id", "referenced_action_id"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            found.append(str(value).strip())
    return found


def _permitted_ids(permitted_entities: Sequence[Mapping[str, Any]] | None) -> set[str] | None:
    if permitted_entities is None:
        return None
    return {str(row.get("id")).strip() for row in permitted_entities if isinstance(row, Mapping) and str(row.get("id") or "").strip()}


def _visible_text(visible_context: Mapping[str, Any] | None) -> str:
    if not isinstance(visible_context, Mapping):
        return ""
    facts = visible_context.get("visible_facts") or []
    chunks = [str(visible_context.get("location") or "")]
    if isinstance(facts, list):
        chunks.extend(str(item) for item in facts)
    return " ".join(chunks).lower()


def evaluate_authority(
    payload: Mapping[str, Any] | None,
    *,
    permitted_entities: Sequence[Mapping[str, Any]] | None = None,
    visible_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Reject interpretations that claim authority the engine did not grant.

    The result is a consumption decision. ``executed`` and ``mutated_state``
    stay false whether the payload is accepted or rejected.
    """
    if not isinstance(payload, Mapping):
        return {
            "accepted": False,
            "reasons": ["malformed_payload"],
            "executed": False,
            "mutated_state": False,
            "authoritative_outcome": False,
        }
    reasons: list[str] = []
    _walk_keys(payload, reasons)
    known = _permitted_ids(permitted_entities)
    if known is not None:
        for entity_id in _ids(payload):
            if entity_id not in known:
                reasons.append(INVENTED_ID)
                break
    blob = _blob(payload)
    visible = _visible_text(visible_context)
    if _COMPLETED.search(blob):
        if _HP.search(blob) or re.search(r"\bhp\s+is\s+now\b", blob, re.IGNORECASE):
            reasons.append(DIRECT_HP)
        if _DICE.search(blob):
            reasons.append(DICE)
        if re.search(r"\b(?:tunnel\s+is\s+now\s+open|patrol\s+(?:is|was)\s+found|advantage\s+(?:is|was)\s+granted)\b", blob, re.IGNORECASE):
            if not visible or not any(part in visible for part in ("is now open", "patrol found", "advantage")):
                reasons.append(INVENTED_FACT)
        reasons.append(UNSUPPORTED_OP)
    if _proposing(payload):
        if _HP.search(blob):
            reasons.append(DIRECT_HP)
        if _DICE.search(blob):
            reasons.append(DICE)
        if _CANON.search(blob):
            reasons.append(CANON_UPDATE)
            if not visible or "is now open" not in visible:
                reasons.append(INVENTED_FACT)
        if _NPC.search(blob):
            reasons.append(NPC_COMMITMENT)
        if _INVENTORY.search(blob):
            reasons.append(INVENTORY)
        if _EXECUTION.search(blob):
            reasons.append(EXECUTION)
        if _HIDDEN.search(blob):
            reasons.append(HIDDEN)
        if _UNSUPPORTED_OP.search(blob):
            reasons.append(UNSUPPORTED_OP)
    ordered = list(dict.fromkeys(reasons))
    return {
        "accepted": not ordered,
        "reasons": ordered,
        "executed": False,
        "mutated_state": False,
        "authoritative_outcome": False,
    }
