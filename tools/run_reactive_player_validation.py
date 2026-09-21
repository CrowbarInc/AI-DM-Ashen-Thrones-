#!/usr/bin/env python3
"""Run bounded reactive/adversarial players through the existing chat and evaluator seams."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.campaign_reset import apply_new_campaign_hard_reset  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from tests.helpers.reactive_player import (  # noqa: E402
    ReactivePlayerConfig,
    ReactivePlayerState,
    ReactiveScenario,
    decide_reactive_action,
    initial_decision,
)
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _final_emission_meta_from_chat_payload,
    _gm_text_from_chat_payload,
    _make_http_caller,
    _resolution_kind,
    _session_debug_traces,
)

ChatCaller = Callable[[str], dict[str, Any]]
ARTIFACT_VERSION = 1

SCENARIOS: dict[str, ReactiveScenario] = {
    "watch_command": ReactiveScenario(
        scenario_id="watch_command",
        objective="Identify who specifically commands the watch at the gate.",
        initial_action="Who commands the watch here?",
        narrower_follow_up="Who specifically is in command of the watch at this gate?",
        rephrased_follow_up="Give me the name or rank of the person who commands this watch.",
        contradiction_probe="You named the captain, but the serjeant appears to direct the gate. Which one actually commands here?",
        established_fact_probe="Earlier you established that a guard captain is present. What authority does that captain have over this watch?",
        knowledge_boundary_probe="Would the tavern runner actually know who sets the watch roster, or should I ask the serjeant?",
        return_to_topic_probe="Before we move on, return to my unresolved question: who commands this watch?",
        degradation_probe="I will ask once more, plainly: who commands the watch here?",
        acceptance_markers=("captain", "serjeant", "commander", "commands", "officer", "rank"),
    ),
    "notice_observation": ReactiveScenario(
        scenario_id="notice_observation",
        objective="Read the concrete information posted on the gate notice.",
        initial_action="I inspect the notice closely and read what is posted.",
        narrower_follow_up="What exact words or instructions are written on the notice?",
        rephrased_follow_up="Read me the notice itself, not the surrounding gate scene.",
        observation_follow_up="I keep my attention on the notice. What does it actually say?",
        contradiction_probe="You described the notice as both weathered and legible. Which parts can I actually read?",
        established_fact_probe="You established that the notice is structured and posted at the gate. What information does that structure contain?",
        return_to_topic_probe="After that interruption, I return to the notice and finish reading it.",
        degradation_probe="I examine the same notice again and ask for only the readable text.",
        acceptance_markers=("tax", "curfew", "patrol", "warning", "written", "reads"),
    ),
    "patrol_knowledge": ReactiveScenario(
        scenario_id="patrol_knowledge",
        objective="Determine where the missing patrol was last seen without granting an NPC impossible knowledge.",
        initial_action="Runner, where exactly was the missing patrol last seen?",
        narrower_follow_up="What is the most specific location you actually know for their last sighting?",
        rephrased_follow_up="Separate rumor from fact: where were they last seen, and who knows that?",
        contradiction_probe="That conflicts with the earlier east-gate rumor. Which account is supported, and why?",
        established_fact_probe="You previously placed the patrol by the east gate. Is that still established?",
        knowledge_boundary_probe="How would the runner know that detail firsthand rather than as hearsay?",
        return_to_topic_probe="I return to the missing patrol: what reliable last location do we have?",
        degradation_probe="One bounded answer: last reliable location, source, and uncertainty.",
        acceptance_markers=("east gate", "northwest", "mud track", "crates", "wall", "yard"),
    ),
}


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _classification(turn: Mapping[str, Any]) -> str:
    semantic = str(turn.get("semantic_result") or "UNCHECKED")
    if not turn.get("api_ok") or semantic == "INVALID_RUN":
        return "D_INFRASTRUCTURE_INVALID_RUN"
    if semantic == "FAIL":
        return "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    if semantic == "UNCHECKED":
        return "E_AMBIGUOUS_HUMAN_REVIEW_REQUIRED"
    return "E_AMBIGUOUS_HUMAN_REVIEW_REQUIRED"


def run_reactive_scenario(
    scenario: ReactiveScenario,
    *,
    strategy: str,
    seed: int,
    chat_call: ChatCaller,
    apply_reset: bool = True,
) -> dict[str, Any]:
    if apply_reset:
        apply_new_campaign_hard_reset()
    config = ReactivePlayerConfig(
        strategy=strategy,
        seed=seed,
        max_turns=scenario.max_turns,
        max_attempts_per_intent=scenario.max_attempts_per_intent,
    )
    state = ReactivePlayerState(current_intent=scenario.objective)
    decision = initial_decision(scenario)
    prior_player = ""
    prior_gm = ""
    turns: list[dict[str, Any]] = []
    termination_reason = "max_turns"

    for turn_index in range(config.max_turns):
        if decision.stop_requested:
            termination_reason = decision.stop_reason or "policy_stop"
            break
        payload = chat_call(decision.player_text)
        if not isinstance(payload, dict):
            payload = {"ok": False, "error": "chat caller returned non-dict"}
        gm_text = _gm_text_from_chat_payload(payload)
        gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), Mapping) else {}
        evaluation = evaluate_playability(
            _build_eval_payload(
                player_prompt=decision.player_text,
                gm_text=gm_text,
                prior_player=prior_player,
                prior_gm=prior_gm,
                debug_traces=_session_debug_traces(payload),
                gm_output=gm_output,
            )
        )
        semantic = str(evaluation.get("semantic_result") or "UNCHECKED")
        turn = {
            "turn_index": turn_index,
            "player_objective": scenario.objective,
            "current_intent": state.current_intent,
            "selected_player_action": decision.player_text,
            "selection_reason": decision.rationale,
            "relevant_prior_context": {"player": prior_player, "gm": prior_gm},
            "gm_response": gm_text,
            "semantic_result": semantic,
            "mandatory_gates": evaluation.get("mandatory_gates"),
            "diagnostic_quality": evaluation.get("diagnostic_quality"),
            "gameplay_runtime_validity": evaluation.get("gameplay_validation"),
            "playability_eval": evaluation,
            "api_ok": bool(payload.get("ok")),
            "api_error": payload.get("error"),
            "resolution_kind": _resolution_kind(payload),
            "final_emission_meta": _final_emission_meta_from_chat_payload(payload),
        }
        turn["failure_classification"] = _classification(turn)
        turns.append(turn)

        decision = decide_reactive_action(
            scenario=scenario,
            config=config,
            state=state,
            turn_index=turn_index + 1,
            prior_gm_text=gm_text,
            prior_evaluation=evaluation,
        )
        prior_player = turn["selected_player_action"]
        prior_gm = gm_text
        if decision.stop_requested:
            termination_reason = decision.stop_reason or "policy_stop"
            break
    else:
        termination_reason = "max_turns"

    if not turns:
        termination_reason = "no_turns"
    return {
        "artifact_version": ARTIFACT_VERSION,
        "scenario_id": scenario.scenario_id,
        "player_strategy": strategy,
        "seed": seed,
        "configuration": {
            "objective": scenario.objective,
            "max_turns": config.max_turns,
            "max_attempts_per_intent": config.max_attempts_per_intent,
        },
        "termination_reason": termination_reason,
        "turn_count": len(turns),
        "valid_run": bool(turns) and all(t["api_ok"] and t["semantic_result"] != "INVALID_RUN" for t in turns),
        "unresolved_intents": state.unresolved_intents,
        "turns": turns,
    }


def campaign_summary(runs: list[Mapping[str, Any]]) -> dict[str, Any]:
    semantic_counts: Counter[str] = Counter()
    gate_failures: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    diagnostic_warnings = 0
    producing: dict[str, set[str]] = defaultdict(set)
    failure_refs: list[dict[str, Any]] = []
    for run in runs:
        run_key = f"{run.get('scenario_id')}:{run.get('player_strategy')}:seed={run.get('seed')}"
        for turn in run.get("turns") or []:
            semantic = str(turn.get("semantic_result") or "UNCHECKED")
            semantic_counts[semantic] += 1
            classification = str(turn.get("failure_classification") or "")
            classifications[classification] += 1
            diagnostic = turn.get("diagnostic_quality") or {}
            if isinstance(diagnostic, Mapping) and not diagnostic.get("passed", False) and semantic == "PASS":
                diagnostic_warnings += 1
            gates = turn.get("mandatory_gates") or {}
            if isinstance(gates, Mapping):
                for name, gate in gates.items():
                    if isinstance(gate, Mapping) and gate.get("status") == "FAIL":
                        gate_failures[str(name)] += 1
                        producing[str(name)].add(run_key)
            if semantic in {"FAIL", "INVALID_RUN", "UNCHECKED"}:
                failure_refs.append(
                    {
                        "run": run_key,
                        "turn_index": turn.get("turn_index"),
                        "semantic_result": semantic,
                        "classification": classification,
                    }
                )
    return {
        "artifact_version": ARTIFACT_VERSION,
        "total_runs": len(runs),
        "valid_runs": sum(1 for run in runs if run.get("valid_run")),
        "invalid_runs": sum(1 for run in runs if not run.get("valid_run")),
        "total_turns": sum(int(run.get("turn_count") or 0) for run in runs),
        "semantic_result_counts": dict(sorted(semantic_counts.items())),
        "mandatory_gate_failure_counts": dict(sorted(gate_failures.items())),
        "diagnostic_only_warnings": diagnostic_warnings,
        "failure_classification_counts": dict(sorted(classifications.items())),
        "failure_clusters": {key: sorted(value) for key, value in sorted(producing.items())},
        "failure_references": failure_refs,
        "novel_failures_not_in_calibration_corpus": [],
        "human_review_note": (
            "PASS turns remain review candidates; probable evaluator misses and false positives are "
            "not inferred automatically or converted into semantic policy."
        ),
    }


def _transcript_md(run: Mapping[str, Any]) -> str:
    lines = [
        f"# Reactive Simulation: {run['scenario_id']}", "",
        f"Strategy: {run['player_strategy']}",
        f"Seed: {run['seed']}",
        f"Objective: {run['configuration']['objective']}",
        f"Termination: {run['termination_reason']}",
        f"Valid Run: {run['valid_run']}", "",
    ]
    for turn in run.get("turns") or []:
        lines.extend([
            f"## Turn {int(turn['turn_index']) + 1}", "",
            f"Player: {turn['selected_player_action']}", "",
            f"Decision reason: `{turn['selection_reason']}`", "",
            f"GM: {turn['gm_response']}", "",
            f"Semantic result: `{turn['semantic_result']}`", "",
            f"Mandatory gates: `{json.dumps(turn['mandatory_gates'], ensure_ascii=False, sort_keys=True)}`", "",
            f"Diagnostic quality: `{json.dumps(turn['diagnostic_quality'], ensure_ascii=False, sort_keys=True)}`", "",
            f"Classification: `{turn['failure_classification']}`", "",
        ])
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), action="append")
    parser.add_argument("--strategy", choices=("reactive", "adversarial"), action="append")
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts" / "reactive_adversarial_players")
    parser.add_argument("--base-url")
    parser.add_argument("--http-timeout", type=float, default=180.0)
    parser.add_argument("--no-reset", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    scenarios = args.scenario or list(SCENARIOS)
    strategies = args.strategy or ["reactive", "adversarial"]
    seeds = args.seed or [1701]
    stamp = _utc_slug()
    campaign_dir = args.artifact_dir / stamp

    def execute(chat_call: ChatCaller) -> list[dict[str, Any]]:
        runs: list[dict[str, Any]] = []
        for scenario_id in scenarios:
            for strategy in strategies:
                for seed in seeds:
                    run = run_reactive_scenario(
                        SCENARIOS[scenario_id],
                        strategy=strategy,
                        seed=seed,
                        chat_call=chat_call,
                        apply_reset=not args.no_reset,
                    )
                    run_id = f"{scenario_id}_{strategy}_seed{seed}"
                    run_dir = campaign_dir / run_id
                    _write_json(run_dir / "run.json", run)
                    (run_dir / "transcript.md").write_text(_transcript_md(run), encoding="utf-8")
                    runs.append(run)
        return runs

    if args.base_url:
        runs = execute(_make_http_caller(args.base_url, timeout_s=args.http_timeout))
    else:
        from fastapi.testclient import TestClient
        from game.api import app

        with TestClient(app) as client:
            runs = execute(lambda text: client.post("/api/chat", json={"text": text}).json())

    summary = campaign_summary(runs)
    summary["campaign_id"] = stamp
    summary["run_artifact_paths"] = [
        str((campaign_dir / f"{r['scenario_id']}_{r['player_strategy']}_seed{r['seed']}" / "run.json").resolve())
        for r in runs
    ]
    _write_json(campaign_dir / "campaign_summary.json", summary)
    (campaign_dir / "campaign_summary.md").write_text(
        "# Reactive and Adversarial Player Campaign\n\n```json\n"
        + json.dumps(summary, indent=2, ensure_ascii=False)
        + "\n```\n",
        encoding="utf-8",
    )
    print(str(campaign_dir.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
