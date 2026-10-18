"""Connect the PR-DO/DR interpretation contract to production chat.

This module does not interpret on its own. It asks the existing contract for a
description, then the existing PR-DU bridge decides whether a resolver may see it.
A rejected, malformed, or ambiguous result never falls through to another parser.
"""

from __future__ import annotations

import json
import os
import re
import time
from contextvars import ContextVar
from typing import Any

from game.player_interpretation_bridge import visible_catalog
from game.provider_budget import (
    accounting_active,
    begin_request,
    finish_request,
    provider_calls_disabled,
)
from game.semantic_interpreter import live_interpretation_enabled, player_visible_turns

_CONSUMED: ContextVar[bool] = ContextVar("live_chat_interpretation_consumed", default=False)
_SECRET_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+", re.IGNORECASE)
_OUTPUT_CAP = 320
_CONTRACT = None

RECIPIENTS = ("GM", "NPC", "CHARACTER", "SESSION", "MIXED", "AMBIGUOUS")
PURPOSES = ("QUESTION", "DESCRIPTION", "EXPLANATION", "RECALL", "RULES", "ACTION", "OBSERVATION", "CORRECTION", "WITHDRAWAL", "CONFIRMATION", "TENTATIVE", "CLARIFICATION")


def production_interpretation_schema() -> dict[str, Any]:
    """Extend the existing interpretation envelope, without granting outcomes."""
    import copy
    schema = copy.deepcopy(_contract()[5]())
    schema["properties"]["communication"] = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "recipient": {"type": "string", "enum": list(RECIPIENTS)},
            "purpose": {"type": "string", "enum": list(PURPOSES)},
            "subject": {"type": "string"},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["recipient", "purpose", "subject", "evidence_refs"],
    }
    schema["required"].append("communication")
    # Structured generation follows property order. Choose the speech act
    # before the operation-shaped legacy fields can bias the recipient.
    schema["properties"] = {"communication": schema["properties"].pop("communication"), **schema["properties"]}
    schema["properties"]["communication"]["properties"]["recipient"]["description"] = (
        "Communicative function of the whole turn, not the person mentioned. GM: asks the facilitator about the world, "
        "including interpreting another person's behavior. NPC: the character actually speaks to that person. "
        "SESSION: mechanics or play procedure. CHARACTER: committed physical attempt. "
        "MIXED: distinct speech/action intentions, including conditional action. AMBIGUOUS: unresolved referent."
    )
    schema["properties"]["communication"]["properties"]["purpose"]["description"] = (
        "Speech act, independent of executable operations: CONFIRMATION accepts pending work; CORRECTION revises "
        "unexecuted intent; WITHDRAWAL cancels it; RULES asks play procedure; EXPLANATION asks cause or meaning. "
        "These control acts are never ACTION, even when mentioning a physical operation."
    )
    return schema


def valid_communication(value: Any, evidence: dict[str, str]) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"recipient", "purpose", "subject", "evidence_refs"}
        and value.get("recipient") in RECIPIENTS
        and value.get("purpose") in PURPOSES
        and isinstance(value.get("subject"), str)
        and isinstance(value.get("evidence_refs"), list)
        and all(isinstance(ref, str) and ref in evidence for ref in value["evidence_refs"])
    )


def redact(text: str) -> str:
    return _SECRET_RE.sub("[REDACTED]", str(text or ""))


def normalize_social_scope(payload: dict, communication: dict | None) -> tuple[dict, list[str]]:
    """Separate nonconsequential posture and question subject from ASK targets.

    This is a conservative compatibility normalization of the existing record,
    not a second interpreter. Unknown gestures remain consequential. A missing
    ASK target, explicit clarification, and independent operations stay intact.
    """
    import copy
    result = copy.deepcopy(payload)
    components = result.get("action_components") or []
    if not isinstance(components, list) or not all(isinstance(c, dict) for c in components):
        return result, []
    if not isinstance(result.get("references"), dict):
        return result, []
    asks = [c for c in components if c.get("operation_class") == "ASK"]
    if not communication or communication.get("recipient") != "NPC" or len(asks) != 1:
        return result, []
    ask = asks[0]
    target = ask.get("target_ref")
    if not target or result.get("interpretation_status") != "INTERPRETED":
        return result, []
    incidental = []
    kept = []
    # Require the whole component to describe only orientation/attention. This
    # cannot swallow drawing weapons, threats, movement, unlocking or sequences.
    posture = re.compile(r"^(?:I\s+)?(?:turn\s+(?:to|toward|towards)|face|(?:nod|incline)\s+(?:(?:my|our|their|the)\s+)?head\s+(?:to|toward|towards)|glance\s+(?:at|toward|towards)|look\s+(?:at|toward|towards))\s+(?P<person>[\w '\-]+?)(?:\s+as a social signal)?[.]?$", re.I)
    for component in components:
        description = str(component.get("description") or "").strip()
        match = posture.fullmatch(description)
        nominal = set(re.findall(r"[a-z]+", match['person'].casefold())) - {'the'} if match else set()
        target_words = set(re.findall(r"[a-z]+", str(target).replace('_', ' ').casefold()))
        if (component.get("operation_class") == "SOCIAL_SIGNAL"
                and component.get("target_ref") == target and nominal and nominal <= target_words
                and not re.search(r"\b(?:and|then|after|before|if|unless|sword|weapon|draw|unlock|threaten)\b", description, re.I)):
            incidental.append(description)
        else:
            kept.append(component)
    result["action_components"] = kept
    return result, incidental


def reset_live_interpretation_consumed() -> None:
    _CONSUMED.set(False)


def mark_live_interpretation_consumed() -> None:
    _CONSUMED.set(True)


def live_interpretation_consumed() -> bool:
    return bool(_CONSUMED.get())


def production_live_interpretation_enabled() -> bool:
    return live_interpretation_enabled() and not provider_calls_disabled()


def _contract():
    """Import the existing contract after its packages force interpretation off."""
    global _CONTRACT
    if _CONTRACT is not None:
        return _CONTRACT
    previous = os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION")
    try:
        from experiments.pr_do.adapter import adapt_interpretation
        from experiments.pr_dp import CONFIGURED_MODEL
        from experiments.pr_dp.prompt import provider_schema
        from experiments.pr_dr.prompt import build_messages_for_catalog, context_leaks, preflight_tokens
    finally:
        if previous is None:
            os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
        else:
            os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = previous
    _CONTRACT = (
        adapt_interpretation,
        build_messages_for_catalog,
        context_leaks,
        preflight_tokens,
        CONFIGURED_MODEL,
        provider_schema,
    )
    return _CONTRACT


def _scene_summary(scene: dict | None) -> str:
    current = scene.get("scene") if isinstance(scene, dict) and isinstance(scene.get("scene"), dict) else scene
    if not isinstance(current, dict):
        return ""
    location = str(current.get("location") or current.get("id") or "")
    summary = str(current.get("summary") or "")
    return f"{location}. {summary}".strip()


def _catalog_rows(scene: dict | None, world: dict | None) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for entity_id, info in sorted(visible_catalog(scene, world).items()):
        row = info.get("row") if isinstance(info.get("row"), dict) else {}
        label = str(row.get("label") or row.get("name") or entity_id)
        aliases = [str(item) for item in (row.get("aliases") or []) if str(item).strip()]
        if aliases:
            label = f"{label} [{' | '.join(aliases)}]"
        rows.append((entity_id, label, str(info.get("kind") or "")))
    return rows


def _blocked(reason: str, player_facing_text: str, *, tags: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "status": "blocked",
        "reason": reason,
        "player_facing_text": player_facing_text,
        "tags": tags,
        "record": None,
        "raw_interpretation": "",
        "provider_requests": [],
    }
    if extra:
        payload.update(extra)
    return payload


def _usage_triplet(resp: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None, None, None
    incoming = getattr(usage, "input_tokens", None)
    outgoing = getattr(usage, "output_tokens", None)
    total = getattr(usage, "total_tokens", None)
    if incoming is None or outgoing is None or total is None:
        return None, None, None
    return int(incoming), int(outgoing), int(total)


def request_interpretation(messages: list[dict[str, str]], *, estimated_input: int) -> dict[str, Any]:
    """One structured completion. No retry and no model switch."""
    _adapt, _build, _leaks, _preflight, model_id, schema_fn = _contract()
    refusal = begin_request(purpose="interpretation", estimated_input=estimated_input, max_output=_OUTPUT_CAP)
    if refusal:
        usage = finish_request(
            {
                "purpose": "interpretation",
                "sent": False,
                "model": model_id,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "refusal": refusal,
            }
        )
        return {"ok": False, "sent": False, "reason": refusal, "error": refusal, "usage": usage}
    from openai import OpenAI

    from game.config import get_openai_api_key

    started = time.perf_counter()
    try:
        from game.gm import provider_timeout_seconds

        client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
        response = client.responses.create(
            model=model_id,
            input=messages,
            temperature=0,
            max_output_tokens=_OUTPUT_CAP,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pr_dr_interpretation",
                    "strict": True,
                    "schema": production_interpretation_schema(),
                }
            },
        )
    except Exception as exc:  # noqa: BLE001 - a failed call is not retried
        finish_request(
            {
                "purpose": "interpretation",
                "sent": True,
                "model": model_id,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "error": redact(str(exc))[:200],
            }
        )
        return {"ok": False, "sent": True, "reason": "provider_failure", "error": type(exc).__name__}
    incoming, outgoing, total = _usage_triplet(response)
    model = str(getattr(response, "model", "") or "")
    record = finish_request(
        {
            "purpose": "interpretation",
            "sent": True,
            "configured_model": model_id,
            "model": model,
            "request_id": getattr(response, "id", None),
            "input_tokens": incoming,
            "output_tokens": outgoing,
            "total_tokens": total,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "estimated_input_tokens": estimated_input,
            "max_output_tokens": _OUTPUT_CAP,
        }
    )
    if model and not model.startswith(model_id):
        return {
            "ok": False,
            "sent": True,
            "reason": "model_mismatch",
            "error": "provider returned a different model",
            "usage": record,
        }
    return {"ok": True, "sent": True, "text": str(getattr(response, "output_text", "") or ""), "usage": record}


def interpret_production_turn(
    *,
    player_text: str,
    mode: str,
    scene: dict | None,
    world: dict | None,
    log: list | None,
    session: dict | None = None,
) -> dict[str, Any]:
    """Return skipped, blocked, or accepted. Accepted carries a bridge record."""
    if not production_live_interpretation_enabled():
        reason = "provider_calls_disabled" if provider_calls_disabled() else "live_interpretation_disabled"
        return {"status": "skipped", "reason": reason, "record": None, "provider_requests": []}

    adapt_interpretation, build_messages_for_catalog, context_leaks, preflight_tokens, _model, _schema = _contract()
    catalog = _catalog_rows(scene, world)
    recent = player_visible_turns(log or [], limit=2)
    messages = build_messages_for_catalog(
        player_text,
        scene_summary=_scene_summary(scene),
        catalog=catalog,
        recent_visible=recent or None,
    )
    from game.conversational_orchestration import public_conversation_evidence
    evidence = public_conversation_evidence(scene, log)
    messages[0]["content"] += (
        " Establish communication.recipient and purpose BEFORE describing operations. "
        "GM is the facilitator, never an NPC. Questions about perception, possibility, prior narration, "
        "third-person NPC appearance, or what an NPC meant address GM; speaking TO an NPC uses NPC. "
        "A short question continuing an active NPC exchange may address NPC; explicit GM address overrides it. "
        "SESSION owns rules and interface questions. CHARACTER owns committed attempts only. "
        "MIXED owns question plus conditional or independent action; preserve all components, never authorize them. "
        "CORRECTION and WITHDRAWAL never undo committed facts. TENTATIVE and capability questions never commit actions. "
        "For GM/session communication leave action_components empty unless a NEW observation is requested; "
        "use existing PERCEIVE/INSPECT for that. Meaningful communication can be INTERPRETED with zero operations. "
        "Select evidence_refs only when the supplied PUBLIC passage actually answers the question. "
        "No evidence means unknown. Subject describes the question, never a new fact. "
        "Do not convert GM communication into SOCIAL_SIGNAL, ASK or an unsupported operation."
        " A declaration of what I/we do is CHARACTER/ACTION, including inspection; "
        "a request to describe already visible information is GM/DESCRIPTION. "
        "NPC clarification or recall of what that NPC just said is NPC/CLARIFICATION with an ASK component; "
        "select its npc:<speaker>:<topic> evidence reference when supplied. "
        "For GM recall of NPC speech, prefer that same established NPC answer passage."
        " For clarification of the most recent NPC statement, npc_latest_reply is the actual latest "
        "utterance, including inability or refusal. Do not substitute an earlier topic for it. "
        " Communication is the primary contract; legacy communication_mode describes the same speech act. "
        "Third-person description of a person does not speak to them. A question about what their expression "
        "implies is GM/EXPLANATION; do not ask the person on the player's behalf. "
        "A request about checks, rolls or adjudication is SESSION/RULES even when phrased hypothetically. "
        "Cancellation, revision and assent describe control of pending intent, never a new world attempt. "
        "Use AMBIGUOUS when a demonstrative has no unique context referent. "
        "For a cause question prefer cause: evidence; if only an outcome is known, do not pretend it explains why. "
        "For mixed observation and speech preserve both components under MIXED; the engine controls their order. "
        "Keep descriptions concise so the complete schema fits the output budget."
        " SESSION does NOT mean every instruction submitted to the engine: describing a character's physical "
        "movement is CHARACTER/ACTION. Assent to proceeding is GM/CONFIRMATION even without a pending proposal "
        "(then the engine will clarify); revising a proposed attempt is GM/CORRECTION. "
        "Conditional commitments are MIXED, even without a question mark. "
        "Ancillary facing, turning toward a speaker, or addressing them is context for ASK, not a separate "
        "SOCIAL_SIGNAL attempt. Dialogue topics need not be entity ids: unresolved_references holds missing "
        "action targets or referents, never merely an unknown subject of a question."
    )
    messages[1]["content"] += "\nPUBLIC answer evidence: " + json.dumps(evidence, ensure_ascii=False)
    interaction = (session or {}).get("interaction_context") or {}
    context = (session or {}).get("conversational_context") or {}
    exchange = context.get("last_gm_exchange") or {}
    messages[1]["content"] += "\nConversation ownership context: " + json.dumps({
        "active_npc_id": interaction.get("active_interaction_target_id"),
        "last_response_category": exchange.get("category"),
        "last_response_owner": exchange.get("owner"),
        "last_subject": exchange.get("subject"),
        "pending_kind": (context.get("pending_clarification") or {}).get("kind"),
        "pending_scene_id": (context.get("pending_clarification") or {}).get("scene_id"),
        "pending_steps": [
            {key: step.get(key) for key in ("operation", "target_id", "text", "supported")}
            for step in (context.get("pending_clarification") or {}).get("steps", [])[:4]
            if isinstance(step, dict)
        ],
        "pending_choices": (context.get("pending_clarification") or {}).get("choices", [])[:4],
    }, ensure_ascii=False)
    leaks = context_leaks(messages, player_text)
    for turn in recent:
        for value in turn.values():
            for leak in list(leaks):
                if leak.casefold() in str(value or "").casefold():
                    leaks = [item for item in leaks if item != leak]
    if leaks:
        return _blocked(
            "context_leak",
            "I can't interpret that from the current scene without using information you have not been shown.",
            tags=["interpretation_rejected", "non_mutating"],
        )

    from experiments.pr_dp.prompt import estimate_input_tokens
    estimated = estimate_input_tokens(messages, production_interpretation_schema())
    if accounting_active() and estimated <= 0:
        return _blocked(
            "token_estimate_unavailable",
            "I can't send that for interpretation because the token estimate is unavailable.",
            tags=["interpretation_rejected", "non_mutating"],
        )
    call = request_interpretation(messages, estimated_input=estimated)
    provider_requests = [call.get("usage")] if isinstance(call.get("usage"), dict) else []
    if not call.get("ok"):
        reason = str(call.get("reason") or "provider_failure")
        return _blocked(
            reason,
            "I couldn't interpret that just now, so no gameplay action was taken.",
            tags=["interpretation_rejected", "non_mutating"],
            extra={"provider_requests": provider_requests, "provider_error": call.get("error")},
        )

    raw = redact(str(call.get("text") or ""))
    try:
        parsed = json.loads(call.get("text") or "")
    except json.JSONDecodeError:
        return _blocked(
            "malformed_interpretation",
            "I couldn't read that as a gameplay action. Please say it again in plain words.",
            tags=["interpretation_rejected", "non_mutating", "malformed_interpretation"],
            extra={"raw_interpretation": raw, "provider_requests": provider_requests},
        )
    if not isinstance(parsed, dict):
        return _blocked(
            "malformed_interpretation",
            "I couldn't read that as a gameplay action. Please say it again in plain words.",
            tags=["interpretation_rejected", "non_mutating", "malformed_interpretation"],
            extra={"raw_interpretation": raw, "provider_requests": provider_requests},
        )

    payload = dict(parsed)
    communication = payload.pop("communication", None)
    # Old recorded records remain replayable; the live provider schema requires ownership.
    if communication is not None and not valid_communication(communication, evidence):
        return _blocked("malformed_communication", "I need you to clarify who you are addressing.",
                        tags=["interpretation_rejected", "non_mutating"],
                        extra={"provider_requests": provider_requests})
    if mode == "IC":
        payload["communication_mode"] = "IN_WORLD_ACTION"
    if communication and payload.get("action_components") and (
        communication["recipient"] in {"CHARACTER", "NPC"}
        or (communication["recipient"] == "GM" and communication["purpose"] == "OBSERVATION")
    ):
        payload["communication_mode"] = "IN_WORLD_ACTION"
    if communication and communication["recipient"] in {"GM", "SESSION"} and communication["purpose"] == "ACTION" and payload.get("communication_mode") == "IN_WORLD_ACTION":
        # Recipient is where the player speaks; ACTION purpose is a declared
        # character attempt. Preserve that commitment rather than swallowing it
        # as a description request when the two model labels disagree.
        components = payload.get("action_components") or []
        if len(components) == 1 and components[0].get("operation_class") in {"MOVE", "INSPECT", "PERCEIVE"}:
            communication["recipient"] = "CHARACTER"
        elif len(components) > 1:
            communication["recipient"] = "MIXED"
    payload, incidental = normalize_social_scope(payload, communication)
    adapted = adapt_interpretation(payload, permitted_ids=[entity_id for entity_id, _label, _kind in catalog])
    reconciliation = None
    if adapted.get("structurally_valid"):
        from game.player_interpretation_bridge import reconcile_reference_annotations
        payload, reconciliation = reconcile_reference_annotations(
            payload, player_text=player_text, scene=scene, world=world, session=session)
        if communication:
            # Reuse the established ownership correction before eligibility can
            # reject a grounded direct address on a stale GM/clarification label.
            from game.conversational_orchestration import _reclassify_direct_npc_address
            prepared = _reclassify_direct_npc_address(
                {**payload, "communication": communication}, player_text,
                scene=scene, world=world, session=session)
            communication = prepared.get("communication", communication)
            payload = {key: prepared[key] for key in payload}
        adapted = adapt_interpretation(payload, permitted_ids=[entity_id for entity_id, _label, _kind in catalog])
    record = adapted.get("record") if isinstance(adapted.get("record"), dict) else None
    if record is not None and communication is not None:
        record["communication"] = communication
        record["incidental_context"] = incidental
        record["reference_reconciliation"] = reconciliation
        # Only passages selected from the engine's public projection can reach emission.
        record["public_evidence"] = {ref: evidence[ref] for ref in communication["evidence_refs"]}
    eligibility = adapted.get("eligibility") if isinstance(adapted.get("eligibility"), dict) else {}
    disposition = str(eligibility.get("disposition") or "")
    common = {
        "raw_interpretation": raw,
        "reference_reconciliation": reconciliation,
        "provider_requests": provider_requests,
        "eligibility_disposition": disposition,
        "model_communication_mode": parsed.get("communication_mode"),
        "interpretation_status": None if record is None else record.get("interpretation_status"),
    }
    if not adapted.get("structurally_valid") or record is None:
        return _blocked(
            "malformed_interpretation",
            "I couldn't read that as a gameplay action. Please say it again in plain words.",
            tags=["interpretation_rejected", "non_mutating", "malformed_interpretation"],
            extra=common,
        )
    if disposition == "OUT_OF_CHARACTER" and mode != "IC":
        return _blocked(
            "automatic_ooc",
            "Understood. I'll treat that as out of character. No gameplay action is executed, "
            "no game time advances, and committed state is unchanged.",
            tags=["ooc_correction", "non_mutating", "automatic_ooc"],
            extra={**common, "record": record},
        )
    if disposition in {"NEEDS_CLARIFICATION", "SAFE_ABSTENTION"}:
        question = str(record.get("clarification_question") or "").strip()
        text = question or "I need a clearer action or target before I change anything in the scene."
        return _blocked(
            "clarification_required",
            text,
            tags=["interpretation_clarification", "non_mutating"],
            extra={**common, "record": record},
        )
    if disposition != "ELIGIBLE_FOR_VALIDATION":
        return _blocked(
            "interpretation_rejected",
            "I can't carry that out from the available interpretation. Tell me the action and who or what it concerns.",
            tags=["interpretation_rejected", "non_mutating"],
            extra={**common, "record": record},
        )
    components = record.get("action_components") if isinstance(record.get("action_components"), list) else []
    if len(components) != 1:
        return _blocked(
            "clarification_required",
            "Which single action should I resolve first?",
            tags=["interpretation_clarification", "non_mutating"],
            extra={**common, "record": record},
        )
    mark_live_interpretation_consumed()
    return {
        "status": "accepted",
        "reason": "eligible_for_bridge",
        "record": record,
        "player_facing_text": "",
        "tags": ["live_interpretation"],
        **common,
    }
