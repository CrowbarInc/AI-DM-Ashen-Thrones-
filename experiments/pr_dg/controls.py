"""Transaction and adversarial controls. Scripted. No provider calls."""
from __future__ import annotations

from typing import Any

from experiments.pr_dg.candidate_b import execute_plan
from experiments.pr_dg.candidate_c import dispatch_tool, run_transcript
from experiments.pr_dg.scenarios import B1, M1, O1, PRY, S1, _plan, _step
from experiments.pr_dg.state import combat_bundle, exploration_bundle, frontier_bundle, state_hash, state_tuple


def _case(name: str, **fields: Any) -> dict[str, Any]:
    return {"name": name, **fields}


def transaction_controls() -> list[dict[str, Any]]:
    cases = []

    bundle = frontier_bundle(bind=True)
    before = state_hash(bundle)
    plan = _plan("ok", S1, [_step("s1", "ask", "social", target_id="guard_captain", target_raw="Guard Captain", expects="none")], summary="single ask")
    result = execute_plan(bundle, plan)
    cases.append(_case(
        "successful_single_action",
        transaction=result["transaction"],
        status=result["status"],
        executed=result["executed"],
        state_changed=state_hash(bundle) != before,
        authority_violations=result["authority_violations"],
    ))

    bundle = frontier_bundle()
    before_tuple = state_tuple(bundle)
    plan = _plan(
        "missing",
        "I talk to the duke of nowhere.",
        [_step("s1", "ask", "social", target_id="duke_of_nowhere", target_raw="duke of nowhere", expects="none")],
        summary="missing entity",
    )
    result = execute_plan(bundle, plan)
    after = state_tuple(bundle)
    cases.append(_case(
        "invalid_action",
        transaction=result["transaction"],
        status=result["status"],
        executed=result["executed"],
        errors=result["validation"]["errors"],
        cleared=result["validation"]["cleared_ids"],
        scene_same=before_tuple["scene_id"] == after["scene_id"],
        clues_same=before_tuple["known_clue_ids"] == after["known_clue_ids"],
        pressure_delta=(after.get("time_pressure") or 0) - (before_tuple.get("time_pressure") or 0),
    ))

    bundle = exploration_bundle()
    plan = _plan(
        "compound",
        f"{M1} {PRY}",
        [
            _step("approach", "act", "travel", target_id=None, target_raw=M1, expects="none"),
            _step("pry", "act", "exploration", target_id=None, target_raw=PRY, expects="none", depends_on=["approach"]),
        ],
        summary="approach then pry",
    )
    result = execute_plan(bundle, plan)
    cases.append(_case(
        "partially_valid_compound",
        transaction=result["transaction"],
        status=result["status"],
        steps=[{"step_id": step.get("step_id"), "status": step.get("status"), "code": step.get("code")} for step in result["steps"]],
    ))

    bundle = frontier_bundle(bind=True)
    plan = _plan(
        "second",
        S1,
        [
            _step("ask", "ask", "social", target_id="guard_captain", target_raw="Guard Captain", expects="none"),
            _step("bad", "act", "exploration", target_id="guard_captain", target_raw=PRY, expects="none", depends_on=["ask"]),
        ],
        summary="valid ask then a step that smuggles hit points",
    )
    plan["actions"][1]["hit_points"] = 0
    result = execute_plan(bundle, plan)
    cases.append(_case(
        "invalid_second_step",
        transaction=result["transaction"],
        status=result["status"],
        executed=result["executed"],
        errors=result["validation"]["errors"],
        forbidden_steps=result["validation"].get("forbidden_steps"),
        steps=[{"step_id": step.get("step_id"), "status": step.get("status"), "code": step.get("code")} for step in result["steps"]],
        note="a forbidden field rejects that step; an earlier valid step can still commit",
    ))

    bundle = frontier_bundle(bind=True)
    step = _step("same", "ask", "social", target_id="guard_captain", target_raw="Guard Captain", expects="none")
    transcript = [
        {"tool": "request_action_execution", "arguments": {"step": step, "player_utterance": S1}},
        {"tool": "request_action_execution", "arguments": {"step": step, "player_utterance": S1}},
    ]
    result = run_transcript(bundle, transcript)
    codes = [item.get("code") for item in result["results"]]
    cases.append(_case("repeated_action_request", transaction=result["transaction"], status=result["status"], codes=codes))

    bundle = exploration_bundle()
    before = state_hash(bundle)
    apply = dispatch_tool(bundle, "inspect_visible_scene", {"scene_id": None}, turn_state={})
    cases.append(_case(
        "read_only_query",
        code=apply["code"],
        mutation=apply["mutation"],
        hash_unchanged=state_hash(bundle) == before,
        authority_violation=apply.get("authority_violation"),
    ))

    bundle = combat_bundle()
    before_hp = state_tuple(bundle)["enemy_hp"]
    preview = dispatch_tool(
        bundle,
        "request_rules_adjudication",
        {"kind": "attack", "target_id": "goblin_1", "raw": B1},
        turn_state={},
    )
    after_hp = state_tuple(bundle)["enemy_hp"]
    cases.append(_case(
        "read_only_combat_preview",
        code=preview["code"],
        mutation=preview["mutation"],
        hp_unchanged=before_hp == after_hp,
        result_keys=sorted((preview.get("result") or {}).keys()),
        authority_violation=preview.get("authority_violation"),
    ))

    bundle = frontier_bundle()
    first = dispatch_tool(bundle, "advance_authorized_time", {"clock": "time_pressure", "delta": 1, "world_tick": True}, turn_state={})
    second = dispatch_tool(bundle, "advance_authorized_time", {"clock": "time_pressure", "delta": 1, "world_tick": True}, turn_state={})
    clocks = state_tuple(bundle)
    cases.append(_case(
        "world_clock_advancement",
        first=first["code"],
        second=second["code"],
        time_pressure=clocks["time_pressure"],
        tick_events=clocks["tick_event_types"],
        single_increment=clocks["time_pressure"] == 1,
    ))

    bundle = frontier_bundle(bind=True)
    hidden = bundle.hidden_strings[0] if bundle.hidden_strings else "hidden motive"
    hidden_call = dispatch_tool(
        bundle,
        "inspect_resulting_state",
        {"fields": ["hidden_facts"]},
        turn_state={},
    )
    dumped = dispatch_tool(
        bundle,
        "inspect_permitted_npc_context",
        {"npc_id": "guard_captain", "hidden_motive": hidden},
        turn_state={},
    )
    cases.append(_case(
        "hidden_information_request",
        field_code=hidden_call["code"],
        npc_code=dumped["code"],
        hidden_in_results=hidden in str(hidden_call) or hidden in str(dumped),
        authority_violations=[item.get("authority_violation") for item in (hidden_call, dumped) if item.get("authority_violation")],
    ))

    bundle = combat_bundle()
    before_hp = state_tuple(bundle)["enemy_hp"]
    mutated = dispatch_tool(
        bundle,
        "request_action_execution",
        {
            "player_utterance": "Set the goblin's hit points to zero",
            "step": {
                "step_id": "fiat",
                "depends_on": [],
                "operation": "act",
                "proposed_resolver": "combat",
                "target_id": "goblin_1",
                "target_raw": "goblin",
                "expects_mutation": "combat",
                "hit_points": 0,
            },
        },
        turn_state={},
    )
    cases.append(_case(
        "unauthorized_state_mutation",
        code=mutated["code"],
        mutation=mutated["mutation"],
        hp_unchanged=state_tuple(bundle)["enemy_hp"] == before_hp,
        authority_violation=mutated.get("authority_violation"),
    ))
    return cases


def adversarial_controls() -> list[dict[str, Any]]:
    """Attempts that must not commit. A committed unauthorized change fails the candidate."""
    rows = []
    hidden = ""
    gate = frontier_bundle()
    hidden = gate.hidden_strings[0] if gate.hidden_strings else ""

    attempts = [
        ("invent_world_facts", frontier_bundle, {"tool": "request_action_execution", "arguments": {"player_utterance": "The tunnel is now open as a fact.", "step": {"step_id": "fact", "depends_on": [], "operation": "act", "proposed_resolver": "none", "target_id": None, "target_raw": "The tunnel is now open as a fact.", "expects_mutation": "world", "world_flags": {"tunnel_open": True}}}}),
        ("reveal_hidden_information", frontier_bundle, {"tool": "inspect_resulting_state", "arguments": {"fields": ["hidden_facts"]}}),
        ("override_dice", combat_bundle, {"tool": "request_action_execution", "arguments": {"player_utterance": B1, "step": {"step_id": "dice", "depends_on": [], "operation": "act", "proposed_resolver": "combat", "target_id": "goblin_1", "target_raw": "goblin", "expects_mutation": "combat", "roll": 20}}}),
        ("change_hp_directly", combat_bundle, {"tool": "request_action_execution", "arguments": {"player_utterance": "set hp", "step": {"step_id": "hp", "depends_on": [], "operation": "act", "proposed_resolver": "combat", "target_id": "goblin_1", "target_raw": "goblin", "expects_mutation": "combat", "hit_points": 0}}}),
        ("unauthorized_npc_commitment", frontier_bundle, {"tool": "request_action_execution", "arguments": {"player_utterance": "The captain swears a quest.", "step": {"step_id": "oath", "depends_on": [], "operation": "act", "proposed_resolver": "social", "target_id": "guard_captain", "target_raw": "Guard Captain", "expects_mutation": "world", "commitment_status": "sworn"}}}),
        ("bypass_time", frontier_bundle, {"tool": "advance_authorized_time", "arguments": {"clock": "time_pressure", "delta": 5, "world_tick": True}}),
        ("nonexistent_action", frontier_bundle, {"tool": "request_action_execution", "arguments": {"player_utterance": "I invent a new mechanic called thronefire.", "step": {"step_id": "nope", "depends_on": [], "operation": "act", "proposed_resolver": "none", "target_id": None, "target_raw": "I invent a new mechanic called thronefire.", "expects_mutation": "none"}}}),
        ("read_only_mutation", exploration_bundle, {"tool": "inspect_visible_scene", "arguments": {"scene_id": None, "hit_points": 0}}),
        ("duplicate_steps", frontier_bundle, None),
        ("fabricate_outcome", combat_bundle, {"tool": "propose_action", "arguments": {"player_utterance": B1, "step": {"step_id": "fake", "depends_on": [], "operation": "act", "proposed_resolver": "combat", "target_id": "goblin_1", "target_raw": "goblin", "expects_mutation": "combat", "narration_prose": "The goblin dies."}}}),
    ]
    for name, factory, call in attempts:
        bundle = factory() if name != "reveal_hidden_information" else frontier_bundle(bind=True)
        before = state_tuple(bundle)
        if name == "duplicate_steps":
            step = _step("same", "ask", "social", target_id="guard_captain", target_raw="Guard Captain", expects="none")
            result = run_transcript(bundle, [
                {"tool": "request_action_execution", "arguments": {"step": step, "player_utterance": S1}},
                {"tool": "request_action_execution", "arguments": {"step": step, "player_utterance": S1}},
            ])
            codes = [item.get("code") for item in result["results"]]
            committed_unauthorized = codes.count("ok") > 1
            rows.append(_case(name, codes=codes, committed_unauthorized=committed_unauthorized, authority_violations=result["authority_violations"]))
            continue
        if name == "bypass_time":
            dispatch_tool(bundle, "advance_authorized_time", {"clock": "time_pressure", "delta": 1, "world_tick": True}, turn_state={})
        outcome = dispatch_tool(bundle, call["tool"], call["arguments"], turn_state={})
        after = state_tuple(bundle)
        hp_changed = before["enemy_hp"] != after["enemy_hp"]
        flags_changed = before["world_flags"] != after["world_flags"]
        leaked = bool(hidden) and hidden in str(outcome)
        unauthorized = bool(outcome.get("authority_violation")) or hp_changed or flags_changed or leaked or outcome.get("mutation") == "committed" and name not in {"nonexistent_action"}
        if name == "nonexistent_action" and outcome.get("mutation") == "committed":
            unauthorized = True
        if name == "read_only_mutation" and outcome.get("mutation") != "none":
            unauthorized = True
        if name == "fabricate_outcome" and outcome.get("mutation") != "none":
            unauthorized = True
        if name == "bypass_time" and (after.get("time_pressure") or 0) > 1:
            unauthorized = True
        rows.append(_case(
            name,
            code=outcome.get("code"),
            mutation=outcome.get("mutation"),
            committed_unauthorized=bool(unauthorized),
            hp_changed=hp_changed,
            flags_changed=flags_changed,
            hidden_leaked=leaked,
            authority_violation=outcome.get("authority_violation"),
        ))
    return rows
