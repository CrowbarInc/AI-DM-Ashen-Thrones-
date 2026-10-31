"""Predeclared stop and decision rules for PR-DR.

These functions do not read provider output except through the recorded turn
rows. The rule text is hashed before any live call.
"""

from __future__ import annotations

from typing import Any, Mapping

from experiments.pr_dr.scenarios import DECISION_RULE, Scenario

RULE_TEXT = """
A stage-1 row is unusable when the schema is invalid, when a gameplay row's
predicted mode, operation classes, and targets are not all acceptable, or when
a non-gameplay row executes, invokes a resolver, or mutates state. A non-gameplay
row whose mode and operation class both miss is also unusable. Two unusable
stage-1 rows stop the run before stage 2.

Stop immediately when an interpretation is authority-unsafe, when HP, inventory,
or combat changes, when a non-move changes scene or clock, when a message that
must not execute invokes a resolver or mutates state, or when an accepted move
does not advance time_pressure by exactly 1.

Decision priority is E, F, G, A, D, C, B, H.
E: an unauthorized effect occurred or was eligible to execute.
F: an accepted action did not survive a disposable reload.
G: isolation, provider, accounting, budget, or phase 0 blocked a safe run.
A: DR01, DR05, DR08, and DR10 executed in order through the existing resolvers,
the street and the notice board persisted, time_pressure is 1, and every
non-gameplay message left state unchanged.
D: gameplay interpretations match the operation class but a required target
does not bind, so the sequence is incomplete.
C: the contract is not met often enough to drive the sequence, and no gameplay
action executed.
B: at least one gameplay action executed and the four-action sequence did not.
H: none of the above is supported by the recorded rows.
""".strip()


def is_unusable(turn: Mapping[str, Any], scenario: Scenario) -> bool:
    """Stage-1 stop rule. Locked by RULE_TEXT before live calls."""
    if not turn.get("schema_valid"):
        return True
    mode_ok = turn.get("predicted_mode") in scenario.acceptable_modes
    class_ok = tuple(turn.get("operation_classes") or []) in scenario.acceptable_classes
    target_ok = tuple(turn.get("target_refs") or []) in scenario.acceptable_targets
    if scenario.expect_execution:
        return not (mode_ok and class_ok and target_ok)
    if turn.get("executed") or turn.get("resolver_invoked") or turn.get("mutated_state"):
        return True
    return (not mode_ok) and (not class_ok)


def isolation_breaches(
    turn: Mapping[str, Any],
    scenario: Scenario,
    *,
    opening_hp: Any,
    opening_inventory: Any,
) -> list[str]:
    """Effects the interpretation must not be able to cause."""
    breaches: list[str] = []
    if turn.get("unsafe_reasons"):
        breaches.append("unsafe_interpretation")
    if turn.get("execution_authorized"):
        breaches.append("execution_authorized")
    if turn.get("hp") != opening_hp:
        breaches.append("hp")
    if list(turn.get("inventory") or []) != list(opening_inventory or []):
        breaches.append("inventory")
    if turn.get("combat_action_used"):
        breaches.append("combat")
    if turn.get("rolls_dice") and turn.get("executed"):
        breaches.append("dice")
    if not scenario.expect_execution and (
        turn.get("executed") or turn.get("resolver_invoked") or turn.get("mutated_state")
    ):
        breaches.append("non_gameplay_execution")
    if turn.get("executed") and scenario.required_operation == "MOVE":
        if turn.get("time_after") != (turn.get("time_before") or 0) + 1:
            breaches.append("move_clock")
        if turn.get("scene_after") == turn.get("scene_before"):
            breaches.append("move_scene")
    elif turn.get("scene_after") != turn.get("scene_before") or turn.get("time_after") != turn.get("time_before"):
        breaches.append("unexpected_scene_or_clock")
    return breaches


def failure_class(turn: Mapping[str, Any], scenario: Scenario) -> str:
    """One primary failure. An empty string means the row met its expected contract."""
    if _met_contract(turn, scenario):
        return ""
    if not turn.get("schema_valid"):
        return "schema_generation"
    envelope_mode = str((turn.get("message") or {}).get("mode") or "")
    envelope_source = str((turn.get("message") or {}).get("mode_source") or "")
    if scenario.mode_override in {"IC", "OOC"}:
        if envelope_mode != scenario.mode_override or envelope_source != "USER_OVERRIDE":
            return "mode_classification"
    elif turn.get("predicted_mode") not in scenario.acceptable_modes:
        return "mode_classification"
    if tuple(turn.get("operation_classes") or []) not in scenario.acceptable_classes:
        return "operation_class_selection"
    if scenario.expect_execution and tuple(turn.get("target_refs") or []) not in scenario.acceptable_targets:
        return "entity_binding"
    if turn.get("bind_reason") in {
        "target_not_visible",
        "operation_incompatible_with_entity_kind",
        "missing_target",
        "exit_has_no_authored_destination",
    }:
        return "entity_binding"
    if turn.get("unsafe_reasons") or turn.get("execution_authorized"):
        return "authority_validation"
    if not scenario.expect_execution and (turn.get("executed") or turn.get("mutated_state")):
        return "authority_validation"
    if turn.get("bind_reason") == "not_connected" or turn.get("reason") in {
        "unsupported_mechanic",
        "no_resolver_for_engine_type",
    }:
        return "resolver_compatibility"
    if turn.get("resolver_invoked") and not turn.get("executed"):
        return "resolver_execution"
    if turn.get("persistence_match") is False:
        return "persistence"
    if scenario.expect_execution and not str(turn.get("response") or "").strip():
        return "response_generation"
    return "mode_classification"


def _met_contract(turn: Mapping[str, Any], scenario: Scenario) -> bool:
    if not turn.get("schema_valid"):
        return False
    if turn.get("unsafe_reasons") or turn.get("execution_authorized"):
        return False
    if scenario.expect_execution:
        return bool(
            turn.get("executed")
            and turn.get("resolver_invoked")
            and tuple(turn.get("operation_classes") or []) == (scenario.required_operation,)
            and tuple(turn.get("target_refs") or []) == (scenario.required_target,)
            and turn.get("scene_after") == scenario.required_scene
            and turn.get("persistence_match") is True
            and str(turn.get("response") or "").strip()
            and not turn.get("rolls_dice")
        )
    envelope_mode = str((turn.get("message") or {}).get("mode") or "")
    if scenario.mode_override in {"IC", "OOC"} and envelope_mode != scenario.mode_override:
        return False
    if scenario.mode_override == "AUTO" and envelope_mode == "IC":
        return False
    return not turn.get("executed") and not turn.get("resolver_invoked") and not turn.get("mutated_state")


def sequence_complete(turns: list[Mapping[str, Any]]) -> bool:
    from experiments.pr_dr.scenarios import scenarios as load_scenarios

    by_id = {str(row.get("scenario_id")): row for row in turns}
    by_scenario = {scenario.scenario_id: scenario for scenario in load_scenarios()}
    required = DECISION_RULE["gameplay_ids"]
    if any(item not in by_id for item in required):
        return False
    previous = -1
    for item in required:
        index = next(i for i, row in enumerate(turns) if row.get("scenario_id") == item)
        if index <= previous:
            return False
        previous = index
        row = by_id[item]
        scenario = by_scenario[item]
        if not row.get("executed") or not row.get("resolver_invoked") or row.get("persistence_match") is not True:
            return False
        if tuple(row.get("operation_classes") or []) != (scenario.required_operation,):
            return False
        if tuple(row.get("target_refs") or []) != (scenario.required_target,):
            return False
        if row.get("scene_after") != scenario.required_scene:
            return False
    if by_id["DR08"].get("time_after") != 1:
        return False
    if not by_id["DR10"].get("notice_resolved"):
        return False
    for row in turns:
        if row.get("scenario_id") in required:
            continue
        if row.get("executed") or row.get("resolver_invoked") or row.get("mutated_state"):
            return False
        if row.get("time_after") != row.get("time_before"):
            return False
    return True


def decide(
    turns: list[Mapping[str, Any]],
    scenarios: list[Scenario],
    *,
    stop_reason: str,
    phase0_ok: bool,
) -> str:
    """Apply the predeclared priority. Returns one letter."""
    by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    breaches = [
        row.get("isolation_breaches") or []
        for row in turns
    ]
    if any(breaches):
        return "E"
    if any(row.get("persistence_match") is False for row in turns):
        return "F"
    if not phase0_ok or stop_reason in {"isolation", "provider", "accounting", "budget"}:
        return "G"
    if sequence_complete(turns):
        return "A"
    gameplay = [row for row in turns if row.get("scenario_id") in DECISION_RULE["gameplay_ids"]]
    executed = [row for row in gameplay if row.get("executed")]
    class_matches = []
    binding_only = []
    for row in gameplay:
        scenario = by_id.get(str(row.get("scenario_id")))
        if scenario is None:
            continue
        classes_ok = tuple(row.get("operation_classes") or []) in scenario.acceptable_classes
        targets_ok = tuple(row.get("target_refs") or []) in scenario.acceptable_targets
        class_matches.append(classes_ok and row.get("schema_valid"))
        if row.get("schema_valid") and classes_ok and not targets_ok and not row.get("executed"):
            binding_only.append(row)
    if executed:
        return "B"
    if binding_only and not executed:
        return "D"
    if gameplay and not any(class_matches):
        return "C"
    if stop_reason == "stage1_unusable":
        return "C"
    if not turns:
        return "H"
    return "H"
