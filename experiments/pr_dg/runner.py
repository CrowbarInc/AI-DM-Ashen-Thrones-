"""PR-DG experiment runner. Scripted A, B, and C. No provider calls."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.pr_dg.candidate_b import execute_plan
from experiments.pr_dg.candidate_c import run_transcript
from experiments.pr_dg.controls import adversarial_controls, transaction_controls
from experiments.pr_dg.isolation import ProductionSaveGuard, forbid_provider_calls
from experiments.pr_dg.resolve import execute_authorized, narration_payload_bytes, select_contract, serialized_bytes
from experiments.pr_dg.scenarios import scenario_table
from experiments.pr_dg.state import apply_shared_tick, hidden_hits, state_hash, state_tuple, tuple_diff

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dg_architecture_preflight"


def _ops(record: dict) -> list[str]:
    found = list(record.get("operations") or [])
    for step in record.get("steps") or []:
        found.extend(step.get("operations") or [])
    for item in record.get("results") or []:
        found.extend((item.get("result") or {}).get("operations") or [])
    return found


def _flags(before: dict, after: dict, record: dict, needles: list[str]) -> tuple[list[str], list[str]]:
    """Authority failures are committed leaks or fiat writes. Sheet diffs are separate."""
    authority: list[str] = []
    prohibited: list[str] = []
    player_bits = [record.get("player_visible") or "", record.get("results") or [], record.get("steps") or []]
    if hidden_hits(player_bits, needles) or record.get("hidden_hits"):
        authority.append("hidden_leak")
    if before.get("scene_id") != after.get("scene_id"):
        prohibited.append("scene_change")
    if set(after.get("known_clue_ids") or []) - set(before.get("known_clue_ids") or []):
        prohibited.append("new_clue")
    if before.get("world_flags") != after.get("world_flags"):
        prohibited.append("flag_write")
    if before.get("enemy_hp") != after.get("enemy_hp") and "resolve_attack" not in _ops(record):
        authority.append("hp_write_outside_resolver")
    ledger_before = {row["id"] for row in before.get("ledger") or []}
    for row in after.get("ledger") or []:
        if row["id"] not in ledger_before and row.get("kind") == "consequential":
            authority.append("consequential_ledger")
    pressure_before = before.get("time_pressure") or 0
    pressure_after = after.get("time_pressure") or 0
    if isinstance(pressure_before, int) and isinstance(pressure_after, int) and pressure_after - pressure_before > 1:
        authority.append("second_clock")
    return authority, prohibited


def _run_a(fixture, utterance: str, *, measure: bool) -> dict[str, Any]:
    bundle = fixture.clone()
    initial = state_hash(bundle)
    before = state_tuple(bundle)
    tick = apply_shared_tick(bundle)
    selector = select_contract(bundle, utterance)
    outcome = execute_authorized(bundle, utterance, selector)
    after = state_tuple(bundle)
    narration_input = {"prompt": utterance, "metadata": {}}
    narration_input.update(outcome.get("resolution") or {})
    narration = narration_payload_bytes(bundle, narration_input, utterance) if measure else {"narration_bytes": None, "provider_call": False, "skipped": True}
    authority, prohibited = _flags(before, after, outcome, bundle.hidden_strings)
    authority.extend(outcome.get("authority_violations") or [])
    status = "failed" if authority else "completed"
    return {
        "candidate": "A",
        "initial_state_hash": initial,
        "resulting_state_hash": state_hash(bundle),
        "before": before,
        "after": after,
        "diff": tuple_diff(before, after),
        "tick": tick,
        "selector": selector,
        "resolver": outcome.get("resolver"),
        "kind": outcome.get("kind"),
        "operations": outcome.get("operations") or [],
        "resolution": outcome.get("resolution") or {},
        "mutator": outcome.get("mutator") or {},
        "unsupported": bool(outcome.get("unsupported")),
        "unsupported_reason": outcome.get("unsupported_reason"),
        "elapsed_ms": outcome.get("elapsed_ms"),
        "narration": narration,
        "authority_violations": authority,
        "prohibited_diffs": prohibited,
        "status": status,
        "transaction": "single_resolver_call" if not outcome.get("unsupported") else "no_resolver_commit",
        "player_visible": outcome.get("player_visible") or "",
    }


def _run_b(fixture, plan: dict, *, measure: bool, utterance: str) -> dict[str, Any]:
    bundle = fixture.clone()
    initial = state_hash(bundle)
    before = state_tuple(bundle)
    outcome = execute_plan(bundle, plan)
    after = state_tuple(bundle)
    narration = {"narration_bytes": None, "provider_call": False, "skipped": True}
    if measure and outcome.get("executed"):
        last = next((step.get("resolution") for step in reversed(outcome.get("steps") or []) if step.get("resolution")), {})
        narration_input = {"prompt": utterance, "metadata": {}}
        narration_input.update(last or {})
        narration = narration_payload_bytes(bundle, narration_input, utterance)
    authority, prohibited = _flags(before, after, outcome, bundle.hidden_strings)
    authority.extend(outcome.get("authority_violations") or [])
    return {
        "candidate": "B",
        "initial_state_hash": initial,
        "resulting_state_hash": state_hash(bundle),
        "before": before,
        "after": after,
        "diff": tuple_diff(before, after),
        "tick": outcome.get("tick"),
        "validation": outcome.get("validation"),
        "steps": outcome.get("steps"),
        "resolver": next((step.get("resolver") for step in (outcome.get("steps") or []) if step.get("resolver")), None),
        "operations": _ops(outcome),
        "narration": narration,
        "planner_context_bytes": outcome.get("planner_context_bytes"),
        "authority_violations": authority,
        "prohibited_diffs": prohibited,
        "status": "failed" if authority else outcome.get("status"),
        "transaction": outcome.get("transaction"),
        "unsupported": any(step.get("status") == "unsupported" for step in (outcome.get("steps") or [])),
        "player_visible": outcome.get("player_visible") or "",
        "queries": outcome.get("queries") or [],
    }


def _run_c(fixture, transcript: list[dict], *, measure: bool, utterance: str) -> dict[str, Any]:
    bundle = fixture.clone()
    initial = state_hash(bundle)
    before = state_tuple(bundle)
    outcome = run_transcript(bundle, transcript)
    after = state_tuple(bundle)
    narration = {"narration_bytes": None, "provider_call": False, "skipped": True}
    executed = any(item.get("mutation") == "committed" and item.get("tool") == "request_action_execution" for item in outcome.get("results") or [])
    if measure and executed:
        last = next((item.get("result") for item in reversed(outcome.get("results") or []) if item.get("tool") == "request_action_execution" and item.get("ok")), {})
        narration_input = {"prompt": utterance, "metadata": {}}
        narration_input.update((last or {}).get("public") or {})
        narration = narration_payload_bytes(bundle, narration_input, utterance)
    flags = _flags(before, after, outcome, bundle.hidden_strings)
    authority, prohibited = flags
    authority.extend(outcome.get("authority_violations") or [])
    resolvers = [
        (item.get("result") or {}).get("resolver")
        for item in outcome.get("results") or []
        if (item.get("result") or {}).get("resolver")
    ]
    return {
        "candidate": "C",
        "resolver": resolvers[-1] if resolvers else None,
        "initial_state_hash": initial,
        "resulting_state_hash": state_hash(bundle),
        "before": before,
        "after": after,
        "diff": tuple_diff(before, after),
        "tick": outcome.get("tick"),
        "results": outcome.get("results"),
        "rounds": outcome.get("rounds"),
        "operations": _ops(outcome),
        "narration": narration,
        "tool_context_bytes": outcome.get("tool_context_bytes"),
        "authority_violations": authority,
        "prohibited_diffs": prohibited,
        "status": "failed" if authority else outcome.get("status"),
        "transaction": outcome.get("transaction"),
        "unsupported": any(item.get("code") == "unsupported" for item in (outcome.get("results") or [])),
        "player_visible": "",
    }


def _sheet(scenario: dict, rows: dict[str, dict]) -> dict[str, Any]:
    """Scenario success from the PR-DF sheet. Narrative text is not scored."""
    number = scenario["number"]
    notes = []
    passed = {}
    a, b, c = rows["A"], rows["B"], rows["C"]
    for label, row in rows.items():
        if row["authority_violations"]:
            passed[label] = False
            notes.append(f"{label} authority flags: {row['authority_violations']}")
    if number in {"1", "2", "3", "4", "9"}:
        for label, row in rows.items():
            passed.setdefault(label, "scene_change" not in row.get("prohibited_diffs", []) and "flag_write" not in row.get("prohibited_diffs", []))
        if number == "4":
            for label, row in rows.items():
                passed[label] = passed[label] and "hidden_leak" not in row["authority_violations"] and "new_clue" not in row.get("prohibited_diffs", [])
        if number == "2":
            for label, row in rows.items():
                if row["after"].get("interlocutor_id") not in {None, "guard_captain"} and row["resolver"] == "social":
                    passed[label] = False
    if number == "5":
        for label, row in rows.items():
            passed[label] = row["after"]["scene_id"] == row["before"]["scene_id"]
    if number == "6":
        for label, row in rows.items():
            passed[label] = row["after"]["entity_ids"] == row["before"]["entity_ids"] and row["after"]["scene_id"] == row["before"]["scene_id"]
    if number == "7":
        skill = [((row.get("resolution") or {}).get("skill_check")) for row in (a,)]
        for label, row in rows.items():
            passed[label] = "hp_write_outside_resolver" not in row["authority_violations"]
        notes.append("K1 mechanical equality is compared across candidates in the match table.")
    if number == "8":
        hps = {label: row["after"]["enemy_hp"] for label, row in rows.items()}
        same = len(set(json.dumps(hp, sort_keys=True) for hp in hps.values())) == 1
        for label, row in rows.items():
            attack = "resolve_attack" in (row.get("operations") or [])
            passed[label] = same and (attack or row["after"]["enemy_hp"] == row["before"]["enemy_hp"])
        notes.append(f"enemy hp by candidate: {hps}")
    if number == "10":
        for label, row in rows.items():
            scene_ok = row["after"]["scene_id"] == row["before"]["scene_id"]
            facts_ok = row["after"]["visible_facts"] == row["before"]["visible_facts"]
            passed[label] = scene_ok and facts_ok and "new_clue" not in row.get("prohibited_diffs", [])
        notes.append("A may stop at generation or travel. B and C must not remove the board.")
    if number == "11":
        for label, row in rows.items():
            interlocutor_chosen = row["before"].get("interlocutor_id") != row["after"].get("interlocutor_id") and row["after"].get("interlocutor_id")
            passed[label] = not interlocutor_chosen and "flag_write" not in row.get("prohibited_diffs", []) and "new_clue" not in row.get("prohibited_diffs", [])
    if number == "12":
        locations = {label: row["after"]["npc_locations"].get("df_mobile_courier") for label, row in rows.items()}
        events = {label: row["after"]["tick_event_types"] for label, row in rows.items()}
        same_location = len(set(locations.values())) == 1
        for label in rows:
            passed[label] = same_location
        notes.append(f"courier locations: {locations}; tick events: {events}")
        if locations.get("A") == rows["A"]["before"]["npc_locations"].get("df_mobile_courier"):
            notes.append("engine gap: advance_world_tick did not move df_mobile_courier")
    if number in {"13", "14"}:
        for label, row in rows.items():
            passed[label] = not row["authority_violations"]
        if number == "14":
            for label, row in rows.items():
                passed[label] = passed.get(label, True) and row["after"]["enemy_hp"] == row["before"]["enemy_hp"]
    for label in ("A", "B", "C"):
        passed.setdefault(label, not rows[label]["authority_violations"])
    return {"pass": passed, "notes": notes}


def _match(rows: dict[str, dict]) -> dict[str, Any]:
    fields = ("scene_id", "known_clue_ids", "enemy_hp", "interlocutor_id", "time_pressure", "tick_event_types")
    mismatches = []
    for field in fields:
        values = {label: rows[label]["after"].get(field) for label in ("A", "B", "C")}
        if len({json.dumps(value, sort_keys=True, default=str) for value in values.values()}) != 1:
            mismatches.append({"field": field, "values": values})
    return {"match": not mismatches, "mismatches": mismatches}


def run_preflight(*, measure_narration: bool = True) -> dict[str, Any]:
    provider_hits: list[str] = []
    with ProductionSaveGuard() as guard:
        with forbid_provider_calls() as provider_hits:
            scenarios = []
            for spec in scenario_table():
                fixture = spec["factory"]()
                fixture.lane = spec["lane"]
                gold = {
                    "A": _run_a(fixture, spec["utterance"], measure=measure_narration),
                    "B": _run_b(fixture, spec["plan"], measure=measure_narration, utterance=spec["utterance"]),
                    "C": _run_c(fixture, spec["transcript"], measure=measure_narration, utterance=spec["utterance"]),
                }
                record = {
                    "number": spec["number"],
                    "scenario_id": spec["scenario_id"],
                    "utterance": spec["utterance"],
                    "gold": gold,
                    "sheet": _sheet(spec, gold),
                    "mechanical_match": _match(gold) if spec["number"] in {str(n) for n in range(1, 10)} else None,
                }
                if spec.get("illegal_plan"):
                    illegal_fixture = spec["factory"]()
                    illegal_fixture.lane = spec["lane"]
                    record["illegal"] = {
                        "B": _run_b(illegal_fixture, spec["illegal_plan"], measure=False, utterance=spec["utterance"]),
                        "C": _run_c(illegal_fixture, spec["illegal_transcript"], measure=False, utterance=spec["utterance"]),
                    }
                scenarios.append(record)
            transactions = transaction_controls()
            adversarial = adversarial_controls()
        guard.assert_unchanged()
        isolation = {"verified": guard.verified, "blocked_writes_after_probe": len(guard.attempts)}
    if provider_hits:
        raise RuntimeError(f"provider calls: {provider_hits}")
    from game.config import DEFAULT_MODEL_NAME
    from game.gm_retry import MAX_TARGETED_RETRY_ATTEMPTS

    payload = {
        "live_provider_calls": 0,
        "isolation": isolation,
        "model_configuration": {
            "default_model_name": DEFAULT_MODEL_NAME,
            "narration_temperature": None,
            "narration_max_output_tokens": None,
            "narration_call": "game.gm.call_gpt responses.create(model=route.selected_model, input=messages) has no temperature or max_output_tokens keyword",
            "interpretation_temperature": 0,
            "interpretation_max_output_tokens": 400,
            "experiment_planner_temperature": 0,
            "experiment_tool_temperature": 0,
            "max_narration_retries": MAX_TARGETED_RETRY_ATTEMPTS,
            "max_planner_replans": 1,
            "max_tool_rounds": 4,
            "live_calls_executed": 0,
        },
        "scenarios": scenarios,
        "transactions": transactions,
        "adversarial": adversarial,
    }
    payload["decision"] = _decision(payload)
    return payload


def _decision(payload: dict) -> dict[str, Any]:
    unauthorized = [row["name"] for row in payload["adversarial"] if row.get("committed_unauthorized")]
    authority = []
    for scenario in payload["scenarios"]:
        for label, row in scenario["gold"].items():
            if row["authority_violations"]:
                authority.append(f"{scenario['scenario_id']}:{label}:{row['authority_violations']}")
        for label, row in (scenario.get("illegal") or {}).items():
            if row["authority_violations"]:
                authority.append(f"{scenario['scenario_id']}:illegal:{label}:{row['authority_violations']}")
    if unauthorized or authority:
        code = "D"
        reason = "An experimental interface committed an unauthorized change or a hidden leak."
    else:
        matches = [scenario["mechanical_match"] for scenario in payload["scenarios"] if scenario.get("mechanical_match")]
        matched = sum(1 for item in matches if item["match"])
        if not payload["scenarios"]:
            code = "F"
            reason = "No scenario results were recorded."
        elif matched < len(matches):
            code = "B"
            reason = "The interfaces run inside the authority contract, and the adversarial controls did not commit. Scenarios 1–9 do not all share mechanical fields, so the live comparison is not yet an even baseline."
        else:
            code = "A"
            reason = "Scripted A, B, and C stay inside the shared authority contract on the scored rows, the adversarial controls do not commit, and scenarios 1–9 match on the mechanical tuple."
    return {
        "code": code,
        "reason": reason,
        "unauthorized_controls": unauthorized,
        "authority_rows": authority,
        "mechanical_matches": [
            {"scenario_id": scenario["scenario_id"], "match": scenario["mechanical_match"]["match"]}
            for scenario in payload["scenarios"]
            if scenario.get("mechanical_match")
        ],
    }


def write_results(payload: dict, path: Path | None = None) -> Path:
    path = path or (OUT / "results.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path
