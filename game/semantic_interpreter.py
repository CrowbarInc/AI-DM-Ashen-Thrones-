"""Structured model interpretation. Output is a proposal, never a contract.

One semantic attempt per turn. A schema-shaped response is parsed strictly.
Malformed output, transport failure, and rejected proposals do not become targets.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping, Sequence

from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
from game.interpretation_proposal import (
    OP_ACT,
    OP_ASK,
    OP_CONFIRM,
    OP_FOLLOW,
    OP_INSPECT,
    OP_PERCEIVE,
    OP_REPEAT,
    OP_UNRESOLVED,
    SOURCE_MODEL,
    InterpretationProposal,
    proposal_from_mapping,
)

TELEMETRY_KEY = "interpretation_telemetry"
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_ALLOWED_OPERATIONS = (
    OP_PERCEIVE,
    OP_INSPECT,
    OP_ASK,
    OP_REPEAT,
    OP_CONFIRM,
    OP_FOLLOW,
    OP_ACT,
    OP_UNRESOLVED,
)

def _nullable_string() -> dict[str, Any]:
    return {"anyOf": [{"type": "string"}, {"type": "null"}]}


def _nullable_operation() -> dict[str, Any]:
    return {"anyOf": [{"type": "string", "enum": list(_ALLOWED_OPERATIONS)}, {"type": "null"}]}


_PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "primary_operation": _nullable_operation(),
        "supporting_operations": {
            "type": "array",
            "items": {"type": "string", "enum": list(_ALLOWED_OPERATIONS)},
        },
        "raw_target_text": _nullable_string(),
        "proposed_target_id": _nullable_string(),
        "interlocutor_id": _nullable_string(),
        "conversational_subject": _nullable_string(),
        "dimension": _nullable_string(),
        "dimensions": {"type": "array", "items": {"type": "string"}},
        "expected_resolution": _nullable_string(),
        "referenced_claim_id": _nullable_string(),
        "referenced_action_id": _nullable_string(),
        "referenced_inspected_id": _nullable_string(),
        "clarification_required": {"type": "boolean"},
        "ambiguous": {"type": "boolean"},
        "confidence": _nullable_string(),
    },
    "required": [
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
        "clarification_required",
        "ambiguous",
        "confidence",
    ],
}


def live_interpretation_enabled() -> bool:
    return os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION", "").strip().lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }


def empty_telemetry() -> dict[str, int]:
    return {
        "fast_path_success": 0,
        "fast_path_abstention": 0,
        "model_interpreter_invoked": 0,
        "proposal_accepted": 0,
        "proposal_rejected": 0,
        "clarification_after_model": 0,
        "interpretation_api_calls": 0,
    }


def bump_interpretation_telemetry(session: dict[str, Any] | None, **counts: int) -> None:
    if not isinstance(session, dict):
        return
    current = session.get(TELEMETRY_KEY)
    stats = dict(current) if isinstance(current, dict) else empty_telemetry()
    for key, value in empty_telemetry().items():
        stats.setdefault(key, value)
    for key, value in counts.items():
        if not value:
            continue
        stats[key] = int(stats.get(key) or 0) + int(value)
    session[TELEMETRY_KEY] = stats


def player_visible_turns(log: Sequence[Mapping[str, Any]] | None, *, limit: int = 2) -> list[dict[str, str]]:
    """Last player-visible lines only. Resolution metadata stays out."""
    found: list[dict[str, str]] = []
    for entry in reversed(list(log or [])):
        if not isinstance(entry, Mapping):
            continue
        player = " ".join(str(entry.get("player_input") or "").split())[:240]
        gm = " ".join(str(entry.get("player_facing_text") or "").split())[:240]
        if not player and not gm:
            continue
        found.append({"player": player, "gm": gm})
        if len(found) >= limit:
            break
    found.reverse()
    return found


def interpretation_messages(context: Mapping[str, Any]) -> list[dict[str, str]]:
    candidates = []
    for row in context.get("candidates") or []:
        if not isinstance(row, Mapping):
            continue
        candidates.append(
            {
                "id": row.get("id"),
                "type": row.get("type"),
                "label": row.get("label"),
                "aliases": list(row.get("aliases") or []),
            }
        )
    focus = context.get("discourse_focus") if isinstance(context.get("discourse_focus"), Mapping) else {}
    payload = {
        "utterance": str(context.get("raw_input") or ""),
        "abstention_reason": context.get("abstention_reason"),
        "candidates": candidates,
        "discourse": focus,
        "recent_visible": list(context.get("visible_turns") or []),
    }
    return [
        {
            "role": "system",
            "content": (
                "You interpret what the player is immediately trying to ask, do, or reference. "
                "You do not decide what exists, what is true, what becomes canonical, or what happens next. "
                "Use only candidate ids from the supplied list. "
                "Put the player's main goal in primary_operation and any setup action in supporting_operations. "
                "If more than one candidate remains plausible, set ambiguous and clarification_required to true "
                "and leave proposed ids null. Do not invent ids, operations, claims, or previous actions. "
                "Set dimension to content when the player asks what was said, reported, written, or heard. "
                "source is who said it, confidence is how sure, time is when, and use is what something is for."
            ),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def parse_interpretation_output(text: str, *, raw_input: str) -> InterpretationProposal:
    """Strict parse. Fence stripping is mechanical. Invalid JSON is a failure."""
    cleaned = _FENCE_RE.sub("", str(text or "").strip()).strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("interpretation output was not an object")
    if "primary_operation" not in payload and "clarification_required" not in payload:
        raise ValueError("interpretation output missing proposal fields")
    proposal = proposal_from_mapping({**payload, "raw_input": raw_input, "source": SOURCE_MODEL})
    return InterpretationProposal(
        raw_input=raw_input,
        source=SOURCE_MODEL,
        primary_operation=proposal.primary_operation,
        supporting_operations=proposal.supporting_operations,
        raw_target_text=proposal.raw_target_text,
        proposed_target_id=proposal.proposed_target_id,
        target_capture="model",
        has_determiner=proposal.has_determiner,
        interlocutor_id=proposal.interlocutor_id,
        conversational_subject=proposal.conversational_subject,
        dimension=proposal.dimension,
        dimensions=proposal.dimensions,
        expected_resolution=proposal.expected_resolution,
        referenced_claim_id=proposal.referenced_claim_id,
        referenced_action_id=proposal.referenced_action_id,
        referenced_inspected_id=proposal.referenced_inspected_id,
        confidence=proposal.confidence,
        clarification_required=proposal.clarification_required,
        ambiguous=proposal.ambiguous,
        operation_conflict=proposal.operation_conflict,
    )


def _invoke_interpretation_model(messages: list[dict[str, str]]) -> str:
    """One structured completion. Callers do not retry this."""
    from openai import OpenAI

    client = OpenAI(api_key=get_openai_api_key())
    response = client.responses.create(
        model=DEFAULT_MODEL_NAME,
        input=messages,
        temperature=0,
        max_output_tokens=400,
        text={
            "format": {
                "type": "json_schema",
                "name": "interpretation_proposal",
                "strict": True,
                "schema": _PROPOSAL_SCHEMA,
            }
        },
    )
    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("empty interpretation output")
    return str(text)


def interpret_for_contract(context: Mapping[str, Any]) -> dict[str, Any]:
    """Return a proposal mapping, a failure, or a skip. Never raises."""
    if not live_interpretation_enabled():
        return {"status": "skipped", "reason": "live_interpretation_disabled", "api_calls": 0}
    from game.live_chat_interpretation import live_interpretation_consumed

    if live_interpretation_consumed():
        return {
            "status": "skipped",
            "reason": "production_interpretation_already_consumed",
            "api_calls": 0,
        }
    messages = interpretation_messages(context)
    try:
        text = _invoke_interpretation_model(messages)
    except Exception as exc:  # noqa: BLE001 - a transport failure is not a contract
        return {"status": "failed", "reason": type(exc).__name__, "api_calls": 1, "error": str(exc)[:200]}
    try:
        proposal = parse_interpretation_output(text, raw_input=str(context.get("raw_input") or ""))
    except Exception as exc:  # noqa: BLE001 - malformed structure is a failed interpretation
        return {"status": "failed", "reason": "malformed_structured_output", "api_calls": 1, "error": str(exc)[:200]}
    return {"status": "proposed", "proposal": proposal.as_dict(), "api_calls": 1}
