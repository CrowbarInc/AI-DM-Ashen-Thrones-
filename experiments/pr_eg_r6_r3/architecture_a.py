"""Architecture A adapter. Production planner and host validation, unchanged.

One provider call goes through unified_semantic_planning._invoke_provider.
The parsed payload is then validated by authorize_information_turn without a
second provider call. Nothing here edits production modules.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from experiments.pr_eg_r6_r3.common import empty_normalized, provider_context_for_case, restricted_leak, role_map


def _roles_from_plan(plan: Mapping[str, Any]) -> dict[str, str]:
    proposition = plan.get("request_proposition") or {}
    if isinstance(proposition, Mapping) and proposition.get("roles"):
        return role_map(proposition.get("roles"))
    return {}


def _operation(plan: Mapping[str, Any]) -> str:
    act = str(plan.get("conversational_act") or "")
    if act == "reference_to_prior_speech":
        return "follow_up"
    if act in {"information_question", "correction", "follow_up", "clarification_response"}:
        return "correction" if act == "clarification_response" else act
    if plan.get("response_kind") == "clarification":
        return "clarification"
    return "other" if act == "other" else "malformed"


def run(case: Mapping[str, Any]) -> dict[str, Any]:
    from game.unified_semantic_planning import _invoke_provider, _provider_context, authorize_information_turn

    built = provider_context_for_case(case)
    context = {key: built[key] for key in ("utterance", "participants", "scene_summary", "prior_plan", "recent_dialogue", "candidates", "referents")}
    payload = _provider_context(context)
    leaks = restricted_leak(payload, case)
    try:
        raw, usage = _invoke_provider(payload)
    except Exception as exc:  # noqa: BLE001 - first-pass transport failure is a result
        return {
            "architecture": "A", "calls": 1, "malformed": True, "raw": "", "usage": {},
            "latency_ms": 0, "prompt": payload, "restricted_leaks": leaks,
            "error": type(exc).__name__,
            "normalized": empty_normalized(validation_reason=type(exc).__name__, malformed=True),
        }
    try:
        proposed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "architecture": "A", "calls": 1, "malformed": True, "raw": raw, "usage": usage,
            "latency_ms": usage.get("latency_ms"), "prompt": payload, "restricted_leaks": leaks,
            "normalized": empty_normalized(validation_reason="malformed_json", malformed=True),
        }
    if not isinstance(proposed, dict):
        return {
            "architecture": "A", "calls": 1, "malformed": True, "raw": raw, "usage": usage,
            "latency_ms": usage.get("latency_ms"), "prompt": payload, "restricted_leaks": leaks,
            "normalized": empty_normalized(validation_reason="malformed_plan", malformed=True),
        }
    outcome = authorize_information_turn(
        player_text=case["utterance"], session=built["session"], world=built["world"],
        scene=built["scene"], proposal=proposed,
    )
    plan = outcome.get("plan") or {}
    proposition = plan.get("request_proposition") if isinstance(plan.get("request_proposition"), Mapping) else {}
    operation_row = plan.get("referent_operation") if isinstance(plan.get("referent_operation"), Mapping) else {}
    reason = str(plan.get("validation_failure") or plan.get("reason") or "")
    accepted = not plan.get("validation_failure") and plan.get("response_kind") not in {"unknown", "clarification"}
    # A host rejection is still an interpreted act when the proposal parsed.
    # Acceptance is recorded separately and is required for conversational success.
    if plan.get("response_kind") == "clarification":
        accepted = False
    response = str(plan.get("response_kind") or "unknown")
    if response not in {"clarification", "refusal", "direct", "partial", "unknown"}:
        response = "unknown"
    response_class = {"direct": "answer", "partial": "answer"}.get(response, response)
    normalized = empty_normalized(
        operation=_operation(plan) if not plan.get("validation_failure") or plan.get("conversational_act") else _operation(plan),
        referent_target=str(plan.get("bound_referent_id") or ""),
        relationship=str((proposition or {}).get("predicate") or ""),
        roles=_roles_from_plan(plan),
        requested_role=str((proposition or {}).get("requested_role") or ""),
        temporal=str((proposition or {}).get("temporal") or ""),
        spatial=str((proposition or {}).get("spatial") or ""),
        negated=bool((proposition or {}).get("negated")),
        transformation=str(operation_row.get("operation") or ""),
        follow_up=str(operation_row.get("follow_up_relationship") or ("speech_clarification" if plan.get("conversational_act") == "reference_to_prior_speech" else "")),
        validation="accepted" if accepted else "rejected",
        validation_reason=reason,
        ambiguity=response == "clarification",
        response_class=response_class,
        addressee_id=str(plan.get("addressee_id") or ""),
        authorized_text=str(plan.get("authorized_text") or ""),
        disclosure_granted=False,
        selected_source_ids=list(plan.get("selected_source_ids") or []),
        malformed=False,
    )
    if reason in {"malformed_json", "malformed_plan", "invalid_plan", "not_an_object"} or not plan.get("conversational_act"):
        normalized["operation"] = "malformed"
        normalized["malformed"] = True
        normalized["validation"] = "rejected"
    return {
        "architecture": "A", "calls": 1, "malformed": normalized["malformed"], "raw": raw,
        "proposal": proposed, "usage": usage, "latency_ms": usage.get("latency_ms"),
        "prompt": payload, "restricted_leaks": leaks, "locked_reason": reason,
        "normalized": normalized,
    }
