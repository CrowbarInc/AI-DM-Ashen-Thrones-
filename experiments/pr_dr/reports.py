"""Markdown artifacts for PR-DR. Scenario text is written once, before live calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.pr_dr.decide import RULE_TEXT, sequence_complete
from experiments.pr_dr.scenarios import scenarios

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dr_live_vertical_slice"
HANDOFF = ROOT / "handoff"
INHERITED = ROOT / "artifacts" / "pr_dq_vertical_slice" / "PR-DQ_regression_results.md"

LETTERS = {
    "A": "LIVE VERTICAL SLICE EXECUTED",
    "B": "PARTIAL LIVE SLICE",
    "C": "INTERPRETATION BLOCKED",
    "D": "ENTITY BINDING BLOCKED",
    "E": "AUTHORITY FAILURE",
    "F": "PERSISTENCE FAILURE",
    "G": "BUDGET OR PROVIDER BLOCKED",
    "H": "INCONCLUSIVE",
}

NEXT_STEP = {
    "A": "Keep this slice experimental. A later chapter can decide whether the same four-action path should be repeated on a second disposable scene. Do not add narration, combat, or a production chat path in that chapter.",
    "B": "Read the first gameplay row whose failure class is not empty. Do not send another provider request in this cycle, and do not replace the live interpretation with a fixture.",
    "C": "Do not integrate the interpreter and do not send further calls in this cycle. The recorded rows did not satisfy the interpretation contract often enough to drive the slice.",
    "D": "Do not guess entity ids in the adapter. A later sample should change only the permitted-reference presentation, and only after a separate decision.",
    "E": "Do not run another live call until the recorded breach is closed. The adapter must keep refusing that effect.",
    "F": "The disposable reload disagreed with the in-memory session. Fix that reload before any further live call.",
    "G": "Safe live execution did not finish. Do not switch models and do not retry the in-flight request.",
    "H": "The recorded rows do not support a stronger letter. Do not fill the gap with a hand-authored interpretation.",
}


def scenario_definitions() -> str:
    lines = [
        "# PR-DR Scenario Definitions",
        "",
        "Ten previously unused player messages for the disposable courtyard slice.",
        "These sentences are not the PR-DP prompts and not the PR-DQ fixture lines.",
        "The visible scene changes with the disposable session. The notice board is absent until the gate transition.",
        "No production save is included in the prompt.",
        "",
    ]
    for row in scenarios():
        lines += [
            f"## {row.scenario_id} — {row.category}",
            "",
            f"Stage: {row.stage}",
            "",
            f"Mode override: {row.mode_override}",
            "",
            f"Player utterance: {row.utterance}",
            "",
            "The model receives this utterance, the active scene's visible entities, the PR-DO communication modes, the PR-DO operation classes, and the compact authority restriction.",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def expected_behavior() -> str:
    lines = [
        "# PR-DR Expected Behavior",
        "",
        "These labels were fixed before any live provider call. They are not revised after results.",
        "",
        RULE_TEXT,
        "",
        "An explicit IC or OOC override sets the envelope mode even when the model proposes a different communication mode. The override does not invent an action the interpretation omitted, and it does not execute an OOC envelope.",
        "",
        "Unmarked text is not assumed to be IC. OTHER, CLARIFICATION, an unresolved reference, and a non-interpreted status stay UNRESOLVED and do not execute.",
        "",
        "Connected operations are INSPECT, PERCEIVE, ASK, and MOVE. ATTACK is not connected. Requested outcomes are not commands.",
        "",
    ]
    for row in scenarios():
        lines += [
            f"## {row.scenario_id} — {row.category}",
            "",
            f"Utterance: {row.utterance}",
            "",
            f"- Override: {row.mode_override}",
            f"- Acceptable model modes: {', '.join(row.acceptable_modes)}",
            f"- Acceptable class sequences: {row.acceptable_classes}",
            f"- Acceptable targets: {row.acceptable_targets}",
            f"- Execution expected: {row.expect_execution}",
            f"- Required operation: {row.required_operation or 'none'}",
            f"- Required target: {row.required_target or 'none'}",
            f"- Required scene after success: {row.required_scene or 'unchanged'}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def _turns(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [row["turn"] for row in state.get("calls") or []]


def _budget(state: dict[str, Any]) -> dict[str, Any]:
    budget = state.get("budget") or {}
    return {
        "requests": int(budget.get("requests") or 0),
        "input_tokens": int(budget.get("input_tokens") or 0),
        "output_tokens": int(budget.get("output_tokens") or 0),
        "total_tokens": int(budget.get("total_tokens") or 0),
    }


def _model(state: dict[str, Any]) -> str:
    for row in state.get("calls") or []:
        model = str((row.get("usage") or {}).get("model") or "")
        if model:
            return model
    return str((state.get("provider") or {}).get("pinned_model") or "")


def write_reports(state: dict[str, Any], regression_rows: list[dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    decision = str(state.get("decision") or "H")
    turns = _turns(state)
    (OUT / "execution_trace.json").write_text(
        json.dumps(
            {
                "baseline": state.get("baseline"),
                "turns": turns,
                "stop_reason": state.get("stop_reason") or "",
                "decision": decision,
                "sequence_complete": sequence_complete(turns),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "PR-DR_experiment_report.md").write_text(_experiment(state), encoding="utf-8")
    (OUT / "PR-DR_mode_classification.md").write_text(_modes(state), encoding="utf-8")
    (OUT / "PR-DR_authority_validation.md").write_text(_authority(state), encoding="utf-8")
    (OUT / "PR-DR_engine_execution.md").write_text(_engine(state), encoding="utf-8")
    (OUT / "PR-DR_state_persistence.md").write_text(_persistence(state), encoding="utf-8")
    (OUT / "PR-DR_failure_taxonomy.md").write_text(_taxonomy(state), encoding="utf-8")
    (OUT / "PR-DR_cost_analysis.md").write_text(_cost(state), encoding="utf-8")
    (OUT / "PR-DR_regression_results.md").write_text(_regression(regression_rows), encoding="utf-8")
    (OUT / "PR-DR_recommendation.md").write_text(_recommendation(state), encoding="utf-8")
    (OUT / "PR-DR_remaining_risks.md").write_text(_risks(state), encoding="utf-8")
    focused = next((row for row in regression_rows if row["name"] == "PR-DR"), None)
    (OUT / "focused_tests.txt").write_text(((focused or {}).get("output") or "") + "\n", encoding="utf-8")
    changed = [
        "experiments/pr_dr/__init__.py",
        "experiments/pr_dr/budget.py",
        "experiments/pr_dr/scenarios.py",
        "experiments/pr_dr/prompt.py",
        "experiments/pr_dr/bind.py",
        "experiments/pr_dr/persist.py",
        "experiments/pr_dr/turn.py",
        "experiments/pr_dr/decide.py",
        "experiments/pr_dr/reports.py",
        "experiments/pr_dr/runner.py",
        "tests/test_pr_dr_live_vertical_slice.py",
        "artifacts/pr_dr_live_vertical_slice/",
        "handoff/CURRENT_REVIEW.md",
        "handoff/CURRENT_REVIEW.zip",
        "handoff/REVIEW_MANIFEST.json",
    ]
    (OUT / "changed_files.txt").write_text("\n".join(changed) + "\n", encoding="utf-8")
    review = _current_review(state, regression_rows)
    (HANDOFF / "CURRENT_REVIEW.md").write_text(review, encoding="utf-8")
    manifest = {
        "pr": "PR-DR",
        "mode": "LIVE INTERPRETATION AND GAMEPLAY EXECUTION",
        "decision": decision,
        "live_provider_calls": _budget(state)["requests"],
        "production_ui_changes": False,
        "artifacts": [
            f"artifacts/pr_dr_live_vertical_slice/{path.name}"
            for path in sorted(OUT.iterdir())
            if path.is_file() and path.name != "state.json"
        ],
    }
    (HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _experiment(state: dict[str, Any]) -> str:
    budget = _budget(state)
    baseline = state.get("baseline") or {}
    provider = state.get("provider") or {}
    lines = [
        "# PR-DR Experiment Report",
        "",
        "Bounded live integration. No production integration and no AI narration.",
        "",
        f"Git HEAD: `{state.get('head')}`",
        "",
        f"Dirty worktree lines at prepare: {state.get('status_lines')}. Status sha256: `{state.get('status_sha256')}`. The dirty tree was not reverted.",
        "",
        f"Phase 0 passed: {state.get('phase0_ok')}. Issues: {state.get('issues') or 'none'}.",
        "",
        f"Pinned model: `{provider.get('pinned_model')}`. Returned model: `{_model(state) or 'none'}`.",
        "",
        f"PR-DQ baseline passed: {state.get('baseline_ok')}. Final scene `{baseline.get('final_scene')}`. time_pressure `{baseline.get('time_pressure')}`. Notice resolved: {baseline.get('notice_resolved')}.",
        "",
        f"Live requests: {budget['requests']}. Input tokens: {budget['input_tokens']}. Output tokens: {budget['output_tokens']}. Total tokens: {budget['total_tokens']}.",
        "",
        f"Stop reason: {state.get('stop_reason') or 'none'}.",
        "",
        f"Sequence complete: {sequence_complete(_turns(state))}.",
        "",
        f"Decision: {state.get('decision')} — {LETTERS.get(str(state.get('decision')), '')}.",
        "",
    ]
    if state.get("harness_note"):
        lines += [str(state["harness_note"]), ""]
    if state.get("saves_unchanged_after_live") is not None:
        lines += [f"Production saves unchanged after live calls: {state.get('saves_unchanged_after_live')}.", ""]
    return "\n".join(lines)


def _modes(state: dict[str, Any]) -> str:
    by_id = {row.scenario_id: row for row in scenarios()}
    lines = [
        "# PR-DR Mode Classification",
        "",
        "Explicit overrides win over the model. AUTO messages use the model communication mode. Unmarked text is not defaulted to IC.",
        "",
        "| ID | Override | Predicted mode | Envelope mode | Source | Intent | Destination | Executed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in state.get("calls") or []:
        turn = row["turn"]
        message = turn.get("message") or {}
        lines.append(
            "| {id} | {override} | {predicted} | {mode} | {source} | {intent} | {destination} | {executed} |".format(
                id=row["scenario_id"],
                override=by_id[row["scenario_id"]].mode_override,
                predicted=turn.get("predicted_mode") or "",
                mode=message.get("mode") or "",
                source=message.get("mode_source") or "",
                intent=message.get("intent") or "",
                destination=message.get("destination") or "",
                executed=turn.get("executed"),
            )
        )
    if not state.get("calls"):
        lines.append("")
        lines.append("No live classifications were recorded.")
    lines.append("")
    return "\n".join(lines)


def _authority(state: dict[str, Any]) -> str:
    lines = [
        "# PR-DR Authority Validation",
        "",
        "The PR-DO adapter does not receive a world and cannot authorize execution. ATTACK is not connected. Requested outcomes are ignored. Unsupported classes do not call a resolver.",
        "",
    ]
    for row in state.get("calls") or []:
        turn = row["turn"]
        lines += [
            f"## {row['scenario_id']}",
            "",
            f"- Disposition: {turn.get('disposition')}",
            f"- Execution authorized flag: {turn.get('execution_authorized')}",
            f"- Unsafe reasons: {turn.get('unsafe_reasons') or 'none'}",
            f"- Isolation breaches: {turn.get('isolation_breaches') or 'none'}",
            f"- Bind reason: {turn.get('bind_reason')}",
            f"- Offered action: `{json.dumps(turn.get('offered_action'), sort_keys=True)}`",
            f"- Resolver invoked: {turn.get('resolver_invoked')}",
            f"- Executed: {turn.get('executed')}",
            "",
        ]
    if not state.get("calls"):
        lines.append("No live authority rows were recorded.")
        lines.append("")
    return "\n".join(lines)


def _engine(state: dict[str, Any]) -> str:
    lines = [
        "# PR-DR Engine Execution",
        "",
        "Accepted IC actions call the existing exploration or social resolver on the disposable world. Deterministic response text comes from that resolver path, not from the model.",
        "",
        "| ID | Executed | Resolver calls | Reason | Scene after | Response |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in state.get("calls") or []:
        turn = row["turn"]
        response = str(turn.get("response") or "").replace("|", "/")
        lines.append(
            f"| {row['scenario_id']} | {turn.get('executed')} | {', '.join(turn.get('new_resolver_calls') or []) or 'none'} | {turn.get('reason')} | {turn.get('scene_after')} | {response} |"
        )
    lines.append("")
    return "\n".join(lines)


def _persistence(state: dict[str, Any]) -> str:
    lines = [
        "# PR-DR State Persistence",
        "",
        "Each turn is written to `disposable_session.json` under the experiment artifacts and read back into a new harness. Production saves are not this file.",
        "",
        "| ID | Persisted | Reload match | Scene | time_pressure | Notice resolved | Turn counter |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in state.get("calls") or []:
        turn = row["turn"]
        lines.append(
            f"| {row['scenario_id']} | {turn.get('persisted')} | {turn.get('persistence_match')} | {turn.get('scene_after')} | {turn.get('time_after')} | {turn.get('notice_resolved')} | {turn.get('turn_counter')} |"
        )
    lines += [
        "",
        f"Production fingerprint at prepare was recorded. Saves unchanged after the live calls: {state.get('saves_unchanged_after_live')}. Stop reason `{state.get('stop_reason') or 'none'}` covers an isolation failure when one was detected.",
        "",
    ]
    return "\n".join(lines)


def _taxonomy(state: dict[str, Any]) -> str:
    lines = [
        "# PR-DR Failure Taxonomy",
        "",
        "A failed row gets one primary class, in this order: schema generation, mode classification, operation-class selection, entity binding, authority validation, resolver compatibility, resolver execution, persistence, response generation.",
        "",
        "| ID | Failure class | Schema valid | Predicted mode | Classes | Targets |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in state.get("calls") or []:
        turn = row["turn"]
        label = turn.get("failure_class") or "none"
        lines.append(
            f"| {row['scenario_id']} | {label} | {turn.get('schema_valid')} | {turn.get('predicted_mode')} | {' '.join(turn.get('operation_classes') or []) or 'none'} | {' '.join(turn.get('target_refs') or []) or 'none'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _cost(state: dict[str, Any]) -> str:
    budget = _budget(state)
    latencies = [
        float((row.get("usage") or {}).get("latency_ms") or 0)
        for row in state.get("calls") or []
    ]
    local = [float(row["turn"].get("local_resolution_ms") or 0) for row in state.get("calls") or []]
    lines = [
        "# PR-DR Cost Analysis",
        "",
        "Provider tokens are interpretation only. Authoritative resolution and the deterministic response used no provider tokens. Narration savings are not estimated.",
        "",
        f"Provider model: `{_model(state) or 'none'}`.",
        "",
        f"Requests: {budget['requests']}.",
        "",
        f"Input tokens: {budget['input_tokens']}.",
        "",
        f"Output tokens: {budget['output_tokens']}.",
        "",
        f"Total tokens: {budget['total_tokens']}.",
        "",
        f"Provider latency ms: {round(sum(latencies), 3)} across {len(latencies)} calls.",
        "",
        f"Local resolution and response latency ms: {round(sum(local), 3)}. Tokens: 0.",
        "",
        "This is not a full-turn affordability claim.",
        "",
    ]
    return "\n".join(lines)


def _inherited_nodes() -> list[str]:
    if not INHERITED.exists():
        return []
    found = []
    for line in INHERITED.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("FAILED "):
            found.append(stripped.removeprefix("FAILED ").strip())
    return found


def _regression(rows: list[dict[str, Any]]) -> str:
    inherited = _inherited_nodes()
    inherited_set = set(inherited)
    lines = [
        "# PR-DR Regression Results",
        "",
        "No suite was repaired. These commands set ASHEN_DISABLE_LIVE_INTERPRETATION=1.",
        "Turn-pipeline failures that appear in the PR-DQ regression file are inherited.",
        "",
        "| Suite | Timeout | Timed out | Return code | Summary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['timeout']}s | {row['timed_out']} | {row['return_code']} | {row['summary']} |"
        )
    pipeline = next((row for row in rows if row["name"] == "Turn pipeline"), None)
    lines += ["", "## Inherited turn-pipeline failures", ""]
    if pipeline is None:
        lines.append("Turn pipeline did not run.")
    elif pipeline["timed_out"]:
        lines.append("Turn pipeline timed out. Inherited names were not compared.")
    else:
        observed = pipeline["failed"]
        kept = [name for name in observed if name in inherited_set]
        fresh = [name for name in observed if name not in inherited_set]
        cleared = [name for name in inherited if name not in set(observed)]
        lines.append(f"Inherited and still failing: {len(kept)}")
        lines.append(f"New failures: {len(fresh)}")
        lines.append(f"Recorded in PR-DQ but not in this run: {len(cleared)}")
        if fresh:
            lines += ["", "New failures:", ""]
            lines += [f"- {name}" for name in fresh]
    lines += ["", "## Suite output", ""]
    for row in rows:
        lines += [
            f"### {row['name']}",
            "",
            f"Command: `python -m pytest {' '.join(row['args'])}`",
            f"Timeout: {row['timeout']}s. Timed out: {row['timed_out']}. Return code: {row['return_code']}.",
            "",
            "```",
            (row.get("output") or "")[-4000:],
            "```",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def _recommendation(state: dict[str, Any]) -> str:
    letter = str(state.get("decision") or "H")
    budget = _budget(state)
    return "\n".join(
        [
            "# PR-DR Recommendation",
            "",
            f"PR-DR decision: {letter} — {LETTERS.get(letter, '')}",
            "",
            f"Live requests: {budget['requests']}",
            f"Actual input tokens: {budget['input_tokens']}",
            f"Actual output tokens: {budget['output_tokens']}",
            f"Actual total tokens: {budget['total_tokens']}",
            f"Stop reason: {state.get('stop_reason') or 'none'}",
            "",
            f"Recommended next step: {NEXT_STEP[letter]}",
            "",
            "No production integration was performed. No AI narration was added.",
            "",
        ]
    )


def _risks(state: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# PR-DR Remaining Risks",
            "",
            "- The live path is an experiment module. Production chat still does not call it.",
            "- AUTO mode depends on one lightweight model sample. A later sentence can still be misclassified.",
            "- ATTACK remains in the PR-DO allowlist and is refused only by this experiment's connector.",
            "- Compound utterances are not segmented. A mixed sentence stays unresolved instead of being split.",
            "- OOC questions receive a fixed deferral, not a rules answer.",
            "- There is no conversation rollback. A committed IC action stays committed.",
            "- The disposable world has one gate and one notice board. Other scenes were not sampled.",
            "- Token totals cover interpretation only.",
            f"- Stop reason on this run: {state.get('stop_reason') or 'none'}.",
            "",
        ]
    )


def _current_review(state: dict[str, Any], regression_rows: list[dict[str, Any]]) -> str:
    budget = _budget(state)
    letter = str(state.get("decision") or "H")
    turns = _turns(state)
    by_id = {row.scenario_id: row for row in scenarios()}
    schema_ok = sum(1 for turn in turns if turn.get("schema_valid"))
    class_ok = 0
    entity_ok = 0
    for turn in turns:
        scenario = by_id.get(str(turn.get("scenario_id")))
        if scenario is None:
            continue
        if tuple(turn.get("operation_classes") or []) in scenario.acceptable_classes:
            class_ok += 1
        if scenario.expect_execution and tuple(turn.get("target_refs") or []) == (scenario.required_target,):
            entity_ok += 1
        elif not scenario.expect_execution and not turn.get("executed"):
            entity_ok += 1
    executed = [str(turn.get("scenario_id")) for turn in turns if turn.get("executed")]
    persisted = [turn for turn in turns if turn.get("persistence_match") is True]
    isolated = [
        turn
        for turn in turns
        if not by_id[str(turn.get("scenario_id"))].expect_execution
        and not turn.get("executed")
        and not turn.get("mutated_state")
    ]
    controls = [turn for turn in turns if not by_id[str(turn.get("scenario_id"))].expect_execution]
    breaches = [turn.get("scenario_id") for turn in turns if turn.get("isolation_breaches")]
    regression = ", ".join(f"{row['name']} {row['summary'] or ('timed out' if row['timed_out'] else 'no summary')}" for row in regression_rows)
    mode_lines = []
    for turn in turns:
        message = turn.get("message") or {}
        mode_lines.append(
            f"{turn.get('scenario_id')}: predicted {turn.get('predicted_mode') or 'none'}, envelope {message.get('mode')} via {message.get('mode_source')}"
        )
    text = "\n".join(
        [
            "# CURRENT REVIEW",
            "",
            "PR-DR",
            "",
            "MODE:",
            "LIVE INTERPRETATION",
            "AND GAMEPLAY EXECUTION",
            "",
            "PR-DQ inherited decision:",
            "A — VERTICAL SLICE EXECUTED",
            "",
            f"Provider model: {_model(state) or 'none'}",
            "",
            f"Live request count: {budget['requests']}",
            "",
            f"Actual input tokens: {budget['input_tokens']}",
            "",
            f"Actual output tokens: {budget['output_tokens']}",
            "",
            f"Actual total tokens: {budget['total_tokens']}",
            "",
            "IC/OOC classification results:",
            "; ".join(mode_lines) if mode_lines else "none",
            "",
            f"Schema validity: {schema_ok} of {len(turns)}",
            "",
            f"Operation-class accuracy: {class_ok} of {len(turns)}",
            "",
            f"Entity-binding accuracy: {entity_ok} of {len(turns)}",
            "",
            f"Gameplay actions executed: {', '.join(executed) if executed else 'none'}",
            "",
            f"State persistence: {len(persisted)} of {len(turns)} reloads matched",
            "",
            f"OOC isolation: {len(isolated)} of {len(controls)} non-gameplay rows left state unchanged",
            "",
            f"Authority findings: {', '.join(str(item) for item in breaches) if breaches else 'no isolation breach recorded'}",
            "",
            f"Regression results: {regression}",
            "",
            f"PR-DR decision: {letter} — {LETTERS.get(letter, '')}",
            "",
            f"Recommended next step: {NEXT_STEP[letter]}",
            "",
        ]
    )
    return text if text.endswith("\n") else text + "\n"
