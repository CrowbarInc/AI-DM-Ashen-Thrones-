"""Replay stored PR-DR interpretations. This module does not call a provider."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from experiments.pr_dg.isolation import IsolationError, ProductionSaveGuard, forbid_provider_calls
from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dq.world import LANTERN_TEXT, NOTICE_ID, NOTICE_TEXT, STREET_ID
from experiments.pr_dr.decide import sequence_complete
from experiments.pr_dr.prompt import build_messages
from experiments.pr_dr.scenarios import scenarios
from experiments.pr_dr.turn import apply_interpretation

ROOT = Path(__file__).resolve().parents[2]
RAW_RESULTS = ROOT / "artifacts" / "pr_dr_live_vertical_slice" / "raw_results.json"
SAVES = ("data/session.json", "data/world.json", "data/combat.json", "data/session_log.jsonl")
GAMEPLAY_IDS = ("DR01", "DR05", "DR08", "DR10")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _refuse_provider(*_args: Any, **_kwargs: Any) -> None:
    raise IsolationError("provider call attempted during PR-DS replay")


def meaningful_state(harness: DisposableHarness) -> dict[str, Any]:
    """World facts. Turn count and empty runtime shells are omitted."""
    session = harness.session
    runtime = session.get("scene_runtime") or {}
    resolved: dict[str, list[Any]] = {}
    discovered: dict[str, list[Any]] = {}
    for scene_id, row in runtime.items():
        if not isinstance(row, dict):
            continue
        resolved_rows = list(row.get("resolved_interactables") or [])
        discovered_rows = list(row.get("discovered_clues") or [])
        if resolved_rows:
            resolved[str(scene_id)] = resolved_rows
        if discovered_rows:
            discovered[str(scene_id)] = discovered_rows
    return {
        "scene": session.get("active_scene_id"),
        "visited": list(session.get("visited_scene_ids") or []),
        "clocks": dict(session.get("clocks") or {}),
        "resolved": resolved,
        "discovered": discovered,
        "inventory": list(session.get("inventory") or []),
        "hp": harness.character.get("hp"),
        "combat_action_used": bool(harness.combat.get("player_turn_used")),
        "flags": session.get("flags") or {},
        "npc_runtime": session.get("npc_runtime") or {},
    }


def load_stored_calls(path: Path = RAW_RESULTS) -> dict[str, Any]:
    state = json.loads(path.read_text(encoding="utf-8"))
    calls = list(state.get("calls") or [])
    problems = authenticate_calls(state, calls)
    if problems:
        raise IsolationError("stored PR-DR outputs failed authentication: " + "; ".join(problems))
    return state


def authenticate_calls(state: dict[str, Any], calls: list[dict[str, Any]]) -> list[str]:
    """Confirm the stored rows are the completed provider responses. Do not rewrite them."""
    problems: list[str] = []
    expected_ids = [row.scenario_id for row in scenarios()]
    found_ids = [str(row.get("scenario_id") or "") for row in calls]
    if found_ids != expected_ids:
        problems.append(f"call order {found_ids}")
    budget = state.get("budget") or {}
    incoming = outgoing = total = 0
    for row in calls:
        usage = row.get("usage") or {}
        parsed = row.get("parsed")
        provider_text = str(row.get("provider_text") or "")
        try:
            decoded = json.loads(provider_text)
        except json.JSONDecodeError:
            problems.append(f"{row.get('scenario_id')} provider text is not JSON")
            continue
        if decoded != parsed:
            problems.append(f"{row.get('scenario_id')} provider text does not match parsed")
        if usage.get("model") != "gpt-4.1-mini-2025-04-14":
            problems.append(f"{row.get('scenario_id')} model {usage.get('model')}")
        request_id = str(usage.get("request_id") or "")
        if not request_id.startswith("resp_") or usage.get("status") != "completed":
            problems.append(f"{row.get('scenario_id')} missing completed request id")
        incoming += int(usage.get("input_tokens") or 0)
        outgoing += int(usage.get("output_tokens") or 0)
        total += int(usage.get("total_tokens") or 0)
    if incoming != 6835 or outgoing != 1934 or total != 8769:
        problems.append(f"token sum {incoming}/{outgoing}/{total}")
    if int(budget.get("requests") or 0) != 10 or int(budget.get("total_tokens") or 0) != 8769:
        problems.append("budget does not record 10 completed requests")
    dr09 = next((row for row in calls if row.get("scenario_id") == "DR09"), None)
    if dr09 is None:
        problems.append("DR09 call missing")
    else:
        usage = dr09.get("usage") or {}
        if int(usage.get("input_tokens") or 0) != 667 or int(usage.get("output_tokens") or 0) != 205:
            problems.append("DR09 usage does not match the stored request")
        blob = json.dumps(dr09.get("messages") or [])
        if "Waystation street" not in blob or "notice_board" not in blob:
            problems.append("DR09 prompt is not the post-transition street prompt")
    return problems


def replay_stored_outputs(persist_path: Path, *, raw_path: Path = RAW_RESULTS) -> dict[str, Any]:
    """Apply the ten stored interpretations on a fresh disposable session."""
    before_saves = {name: _sha(ROOT / name) for name in SAVES}
    raw_hash = _sha(raw_path)
    state = load_stored_calls(raw_path)
    calls = list(state.get("calls") or [])
    by_scenario = {row.scenario_id: row for row in scenarios()}
    harness = DisposableHarness()
    opening_hp = harness.character.get("hp")
    opening_inventory = list(harness.session.get("inventory") or [])
    rows: list[dict[str, Any]] = []
    provider_hits: list[str] = []
    import experiments.pr_dr.runner as runner

    patches = [patch.object(runner, "_call_one", _refuse_provider)]
    try:
        import openai

        patches.append(patch.object(openai, "OpenAI", _refuse_provider))
    except Exception:
        pass
    for item in patches:
        item.start()
    try:
        with ProductionSaveGuard() as guard, forbid_provider_calls() as provider_hits:
            for call in calls:
                scenario = by_scenario[str(call["scenario_id"])]
                rebuilt = build_messages(scenario.utterance, harness)
                stored = call.get("messages") or []
                prompt_match = rebuilt == stored
                meaningful_before = meaningful_state(harness)
                turn = apply_interpretation(
                    harness,
                    scenario,
                    call.get("parsed") if isinstance(call.get("parsed"), dict) else None,
                    persist_path=persist_path,
                )
                turn["scenario_id"] = scenario.scenario_id
                meaningful_after = meaningful_state(harness)
                rows.append(
                    {
                        "scenario_id": scenario.scenario_id,
                        "utterance": scenario.utterance,
                        "mode_override": scenario.mode_override,
                        "stored_model_output": call.get("parsed"),
                        "provider_request_id": (call.get("usage") or {}).get("request_id"),
                        "prompt_match": prompt_match,
                        "predicted_mode": turn.get("predicted_mode"),
                        "operation_classes": turn.get("operation_classes"),
                        "target_refs": turn.get("target_refs"),
                        "envelope_mode": (turn.get("message") or {}).get("mode"),
                        "mode_source": (turn.get("message") or {}).get("mode_source"),
                        "compatibility": turn.get("compatibility"),
                        "bind_reason": turn.get("bind_reason"),
                        "offered_action": turn.get("offered_action"),
                        "executed": turn.get("executed"),
                        "resolver_invoked": turn.get("resolver_invoked"),
                        "new_resolver_calls": turn.get("new_resolver_calls"),
                        "reason": turn.get("reason"),
                        "response": turn.get("response"),
                        "scene_before": turn.get("scene_before"),
                        "scene_after": turn.get("scene_after"),
                        "time_before": turn.get("time_before"),
                        "time_after": turn.get("time_after"),
                        "turn_counter": turn.get("turn_counter"),
                        "mutated_state": turn.get("mutated_state"),
                        "meaningful_change": meaningful_before != meaningful_after,
                        "meaningful_before": meaningful_before,
                        "meaningful_after": meaningful_after,
                        "persistence_match": turn.get("persistence_match"),
                        "notice_resolved": turn.get("notice_resolved"),
                        "rolls_dice": turn.get("rolls_dice"),
                        "hp": turn.get("hp"),
                        "inventory": turn.get("inventory"),
                        "schema_valid": turn.get("schema_valid"),
                        "unsafe_reasons": turn.get("unsafe_reasons"),
                        "execution_authorized": turn.get("execution_authorized"),
                    }
                )
            notice_before = _notice_before_transition(calls, persist_path.parent / "notice_before.json")
            guard.assert_unchanged()
    finally:
        for item in reversed(patches):
            item.stop()
    if provider_hits:
        raise IsolationError("provider call attempted: " + ",".join(provider_hits))
    if _sha(raw_path) != raw_hash:
        raise IsolationError("PR-DR raw_results.json changed during replay")
    after_saves = {name: _sha(ROOT / name) for name in SAVES}
    if after_saves != before_saves:
        raise IsolationError("production saves changed during replay")
    return {
        "rows": rows,
        "history_ids": harness.history.ids(),
        "final_scene": harness.session.get("active_scene_id"),
        "time_pressure": (harness.session.get("clocks") or {}).get("time_pressure"),
        "turn_counter": harness.session.get("turn_counter"),
        "notice_resolved": NOTICE_ID
        in (((harness.session.get("scene_runtime") or {}).get(STREET_ID) or {}).get("resolved_interactables") or []),
        "hp": harness.character.get("hp"),
        "inventory": list(harness.session.get("inventory") or []),
        "opening_hp": opening_hp,
        "opening_inventory": opening_inventory,
        "pr_dr_sequence_complete": sequence_complete(rows),
        "gameplay_executed": [row["scenario_id"] for row in rows if row["scenario_id"] in GAMEPLAY_IDS and row["executed"]],
        "non_gameplay_executed": [
            row["scenario_id"] for row in rows if row["scenario_id"] not in GAMEPLAY_IDS and row["executed"]
        ],
        "prompt_mismatches": [row["scenario_id"] for row in rows if not row["prompt_match"]],
        "persistence_failures": [row["scenario_id"] for row in rows if row["persistence_match"] is not True],
        "provider_hits": list(provider_hits),
        "raw_results_sha256": raw_hash,
        "production_saves_unchanged": after_saves == before_saves,
        "save_fingerprints": after_saves,
        "harness_note": state.get("harness_note"),
        "dr09_usage": next(row.get("usage") for row in calls if row.get("scenario_id") == "DR09"),
        "budget": state.get("budget"),
        "notice_before_transition": notice_before,
        "lantern_text_disclosed": any(LANTERN_TEXT in str(row.get("response") or "") for row in rows if row["scenario_id"] == "DR01"),
        "notice_text_on_dr01": NOTICE_TEXT in str(next(row["response"] for row in rows if row["scenario_id"] == "DR01")),
    }


def _notice_before_transition(calls: list[dict[str, Any]], persist_path: Path) -> dict[str, Any]:
    """Apply the stored DR10 interpretation while the courtyard is still active."""
    harness = DisposableHarness()
    scenario = next(row for row in scenarios() if row.scenario_id == "DR10")
    parsed = next(row.get("parsed") for row in calls if row.get("scenario_id") == "DR10")
    turn = apply_interpretation(harness, scenario, parsed, persist_path=persist_path)
    return {
        "executed": turn.get("executed"),
        "resolver_invoked": turn.get("resolver_invoked"),
        "bind_reason": turn.get("bind_reason"),
        "scene_after": turn.get("scene_after"),
        "time_after": turn.get("time_after"),
        "notice_resolved": turn.get("notice_resolved"),
        "visible_ids": turn.get("visible_ids"),
        "response": turn.get("response"),
        "persistence_match": turn.get("persistence_match"),
        "disposition": turn.get("disposition"),
        "unresolved_references": turn.get("unresolved_references"),
    }
