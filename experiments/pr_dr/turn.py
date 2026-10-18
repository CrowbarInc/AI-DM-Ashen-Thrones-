"""One live turn: mode, authority, existing resolver, disposable persistence."""

from __future__ import annotations

import copy
from typing import Any

from experiments.pr_do.adapter import adapt_interpretation
from experiments.pr_do.routing import engine_channel_from_utterance
from experiments.pr_do.schema import UNSUPPORTED_OPERATION_CLASSES
from experiments.pr_dp.score import authority_problems
from experiments.pr_dq.envelope import PlayerMessage
from experiments.pr_dq.gameplay import dispatch_message
from experiments.pr_dq.route import execution_permitted, route_message
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dr.bind import connected_action
from experiments.pr_dr.persist import read_state, write_state
from experiments.pr_dr.prompt import visible_catalog
from experiments.pr_dr.scenarios import Scenario
from experiments.pr_dq.world import NOTICE_ID, STREET_ID

_OOC_MODES = frozenset({"OUT_OF_CHARACTER_CORRECTION", "RULES_QUESTION"})
_CLEAR_IC = frozenset({"PERCEIVE", "INSPECT", "ASK", "MOVE"})


def _single(record: dict[str, Any] | None) -> tuple[str, str | None]:
    if not record:
        return "", None
    components = list(record.get("action_components") or [])
    if len(components) != 1:
        return "", None
    return str(components[0].get("operation_class") or ""), components[0].get("target_ref")


def propose_mode(record: dict[str, Any] | None, schema_valid: bool) -> tuple[str, str, str]:
    """Map a model communication mode. Unmarked text is not treated as IC."""
    if not schema_valid or not record:
        return "UNRESOLVED", "AUTO", "schema_invalid"
    mode = str(record.get("communication_mode") or "")
    status = str(record.get("interpretation_status") or "")
    unresolved = list((record.get("references") or {}).get("unresolved_references") or [])
    if mode in _OOC_MODES:
        basis = "model_out_of_character" if mode == "OUT_OF_CHARACTER_CORRECTION" else "model_rules_question"
        return "OOC", "AUTO", basis
    if mode in {"CLARIFICATION", "OTHER"} or status in {"CLARIFICATION_REQUIRED", "ABSTAIN"} or unresolved:
        return "UNRESOLVED", "AUTO", "model_ambiguous_or_unresolved"
    if mode == "IN_WORLD_ACTION" and status == "INTERPRETED":
        return "IC", "AUTO", "model_in_world_action"
    if status == "UNSUPPORTED_REQUEST":
        return "IC", "AUTO", "model_unsupported_request"
    return "UNRESOLVED", "AUTO", "model_mode_not_actionable"


def _intent(mode: str, record: dict[str, Any] | None) -> str:
    if mode == "OOC":
        model_mode = str((record or {}).get("communication_mode") or "")
        subject = str(((record or {}).get("correction") or {}).get("subject") or "NONE")
        if model_mode == "RULES_QUESTION":
            return "RULES_QUERY"
        if model_mode == "OUT_OF_CHARACTER_CORRECTION" or subject != "NONE":
            return "CORRECTION"
        return "QUESTION"
    if mode != "IC":
        return "OTHER"
    operation, _target = _single(record)
    if operation == "ASK":
        return "DIALOGUE"
    if operation in _CLEAR_IC or operation:
        return "ACTION"
    return "OTHER"


def _channel(utterance: str, mode_override: str) -> str | None:
    if mode_override == "OOC":
        return "OUT_OF_CHARACTER_CORRECTION"
    return engine_channel_from_utterance(utterance)


def _classes(parsed: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(parsed, dict):
        return ()
    rows = parsed.get("action_components")
    if not isinstance(rows, list):
        return ()
    ordered = sorted(
        (row for row in rows if isinstance(row, dict)),
        key=lambda row: row.get("order") if isinstance(row.get("order"), int) else 0,
    )
    return tuple(str(row.get("operation_class") or "") for row in ordered)


def _targets(parsed: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(parsed, dict):
        return ()
    rows = parsed.get("action_components")
    if not isinstance(rows, list):
        return ()
    ordered = sorted(
        (row for row in rows if isinstance(row, dict)),
        key=lambda row: row.get("order") if isinstance(row.get("order"), int) else 0,
    )
    found = []
    for row in ordered:
        target = row.get("target_ref")
        if isinstance(target, str) and target.strip():
            found.append(target.strip())
    return tuple(found)


def apply_interpretation(
    harness: Any,
    scenario: Scenario,
    parsed: dict[str, Any] | None,
    *,
    persist_path: Any = None,
) -> dict[str, Any]:
    """Validate one interpretation and maybe call the existing gameplay adapter.

    ``parsed`` is model output or a test fixture. It is not a state patch.
    """
    before = authoritative_snapshot(harness)
    before_scene = harness.session.get("active_scene_id")
    before_clock = (harness.session.get("clocks") or {}).get("time_pressure")
    before_calls = len(harness.resolver_calls)
    permitted = [entity_id for entity_id, _label, _kind in visible_catalog(harness)]
    channel = _channel(scenario.utterance, scenario.mode_override)
    adapter = adapt_interpretation(
        parsed if isinstance(parsed, dict) else {"_unparsed": True},
        permitted_ids=permitted,
        engine_channel=channel,
    )
    unsafe = authority_problems(adapter, parsed if isinstance(parsed, dict) else None)
    record = adapter.get("record") if isinstance(adapter.get("record"), dict) else None
    schema_valid = bool(adapter.get("structurally_valid"))
    if scenario.mode_override in {"IC", "OOC"}:
        mode, source, basis = scenario.mode_override, "USER_OVERRIDE", "user_override"
    else:
        prefixed = engine_channel_from_utterance(scenario.utterance)
        if prefixed == "OUT_OF_CHARACTER_CORRECTION":
            mode, source, basis = "OOC", "AUTO", "explicit_ooc_prefix"
        else:
            mode, source, basis = propose_mode(record, schema_valid)
    intent = _intent(mode, record)
    correction = "NONE"
    if mode == "OOC" and record:
        correction = str((record.get("correction") or {}).get("subject") or "NONE")
    message = PlayerMessage(
        message_id=scenario.scenario_id.lower(),
        text=scenario.utterance,
        mode=mode,
        mode_source=source,
        intent=intent,
        status="CLASSIFIED" if mode in {"IC", "OOC"} else "AWAITING_CLARIFICATION",
        requested_override=scenario.mode_override,
        correction_subject=correction,
        classification_basis=basis,
    )
    route_message(message)
    harness.history.append(message)

    action = None
    bind_reason = "not_offered"
    eligibility = adapter.get("eligibility") if isinstance(adapter.get("eligibility"), dict) else {}
    operation, target = _single(record)
    offer = (
        not unsafe
        and message.mode == "IC"
        and execution_permitted(message)
        and schema_valid
        and str(eligibility.get("disposition") or "") in {"ELIGIBLE_FOR_VALIDATION", "UNSUPPORTED_OPERATION"}
        and operation
        and len(list((record or {}).get("action_components") or [])) == 1
        and not list((record or {}).get("references", {}).get("unresolved_references") or [])
    )
    if offer and operation in _CLEAR_IC and eligibility.get("disposition") == "ELIGIBLE_FOR_VALIDATION":
        action, bind_reason = connected_action(
            harness,
            operation,
            target if isinstance(target, str) else None,
            scenario.utterance,
        )
        if bind_reason:
            action = None
    elif offer and (operation in UNSUPPORTED_OPERATION_CLASSES or operation == "ATTACK"):
        action = {"operation_class": operation}
        bind_reason = "not_connected"
    elif message.mode == "IC" and execution_permitted(message):
        bind_reason = "clarification_or_compound_not_executed"

    if unsafe:
        from experiments.pr_dq.safety import refuse_unexecuted_mutation

        result = {
            "executed": False,
            "resolver_invoked": False,
            "response": "Interpretation blocked before execution. No state was changed.",
            "reason": "unsafe_interpretation",
        }
        message.processing_result = result
        message.status = "REJECTED"
        message.committed = False
        refuse_unexecuted_mutation(before, authoritative_snapshot(harness), message)
    else:
        result = dispatch_message(message, harness, action)

    persisted = False
    reloaded_match = None
    if persist_path is not None:
        write_state(persist_path, harness)
        restored, saved_snapshot = read_state(persist_path)
        reloaded_match = (
            authoritative_snapshot(restored) == authoritative_snapshot(harness) == saved_snapshot
            and restored.history.ids() == harness.history.ids()
        )
        persisted = True

    after = authoritative_snapshot(harness)
    opening = copy.deepcopy(result)
    return {
        "message": message.to_record(),
        "schema_valid": schema_valid,
        "adapter_errors": list(adapter.get("errors") or []),
        "predicted_mode": str((record or parsed or {}).get("communication_mode") or "") if isinstance(parsed, dict) else "",
        "interpretation_status": str((record or {}).get("interpretation_status") or ""),
        "operation_classes": list(_classes(parsed if isinstance(parsed, dict) else None)),
        "target_refs": list(_targets(parsed if isinstance(parsed, dict) else None)),
        "unresolved_references": list((record or {}).get("references", {}).get("unresolved_references") or []) if record else [],
        "disposition": eligibility.get("disposition"),
        "execution_authorized": bool(eligibility.get("execution_authorized")),
        "engine_submission": eligibility.get("engine_submission"),
        "bind_reason": bind_reason,
        "offered_action": action,
        "compatibility": (
            "visible_surface_inspection"
            if isinstance(action, dict) and action.get("visible_surface_inspection") is True
            else ""
        ),
        "unsafe_reasons": unsafe,
        "executed": bool(opening.get("executed")),
        "resolver_invoked": bool(opening.get("resolver_invoked")),
        "new_resolver_calls": harness.resolver_calls[before_calls:],
        "mutated_state": before != after,
        "scene_before": before_scene,
        "scene_after": harness.session.get("active_scene_id"),
        "time_before": before_clock,
        "time_after": (harness.session.get("clocks") or {}).get("time_pressure"),
        "turn_counter": harness.session.get("turn_counter"),
        "response": opening.get("response"),
        "reason": opening.get("reason"),
        "visible_ids": permitted,
        "persisted": persisted,
        "persistence_match": reloaded_match,
        "requested_outcomes_ignored": True,
        "rolls_dice": bool(opening.get("rolls_dice")),
        "hp": harness.character.get("hp"),
        "inventory": list(harness.session.get("inventory") or []),
        "combat_action_used": bool(harness.combat.get("player_turn_used")),
        "notice_resolved": NOTICE_ID
        in (
            ((harness.session.get("scene_runtime") or {}).get(STREET_ID) or {}).get("resolved_interactables")
            or []
        ),
    }
