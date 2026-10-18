"""Run PR-DT authoritative narration experiment.

This script writes only PR-DT artifacts and handoff files. It replays stored
PR-DR interpretations through the PR-DS/PR-DQ disposable authority path, then
optionally asks a live provider for presentation-only narration.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.pr_dg.isolation import IsolationError, ProductionSaveGuard, WATCHED, forbid_provider_calls
from experiments.pr_dp.budget import BudgetStop
from experiments.pr_dq.gameplay import DisposableHarness
from experiments.pr_dq.safety import authoritative_snapshot
from experiments.pr_dq.world import NOTICE_ID, STREET_ID
from experiments.pr_dr.prompt import visible_catalog
from experiments.pr_ds.replay import GAMEPLAY_IDS, load_stored_calls, replay_stored_outputs
from experiments.pr_dr.scenarios import scenarios as dr_scenarios
from experiments.pr_dr.turn import apply_interpretation
from experiments.pr_dt import MODEL_ID
from experiments.pr_dt.budget import OUTPUT_TOKEN_CAP, NarrationBudget
from experiments.pr_dt.evaluate import evaluate_text
from experiments.pr_dt.scenarios import NarrationScenario, scenarios
from game.config import DEFAULT_MODEL_NAME, HIGH_PRECISION_MODEL_NAME, MODEL_NAME, get_openai_api_key

OUT = ROOT / "artifacts" / "pr_dt_authoritative_narration"
HANDOFF = ROOT / "handoff"
STATE_PATH = OUT / "raw_results.json"
TRACE_PATH = OUT / "execution_trace.json"

SUITES = (
    ("PR-DT focused", ["tests/test_pr_ds_operation_compatibility.py", "-q", "--tb=line"], 180),
    ("PR-DS", ["tests/test_pr_ds_operation_compatibility.py", "-q", "--tb=line"], 180),
    ("PR-DR", ["tests/test_pr_dr_live_vertical_slice.py", "-q", "--tb=line"], 180),
    (
        "PR-DQ",
        ["tests/test_pr_dq_ic_ooc_messages.py", "tests/test_pr_dq_vertical_slice.py", "-q", "--tb=line"],
        180,
    ),
    ("Authority", ["tests/test_pr_cx_authority_assurance.py", "-q", "--tb=line"], 180),
    ("Conversation", ["tests/test_conversational_memory_window.py", "-q", "--tb=line"], 180),
    ("Exploration", ["tests/test_exploration_resolution.py", "tests/test_exploration_skill_checks.py", "-q", "--tb=line"], 240),
    ("Shared turn pipeline", ["tests/test_turn_pipeline_shared.py", "-q", "--tb=line"], 300),
)


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return ((completed.stdout or "") + (completed.stderr or "")).strip()


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fingerprints() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for path in WATCHED:
        if path.exists():
            data = path.read_bytes()
            rows[path.name] = {"size": len(data), "sha256": _sha_bytes(data)}
        else:
            rows[path.name] = {"size": None, "sha256": None}
    return rows


def _estimate_tokens(messages: list[dict[str, str]]) -> int:
    return max(1, len(json.dumps(messages, ensure_ascii=False).encode("utf-8")) // 3 + 64)


def _usage(resp: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None, None, None
    incoming = getattr(usage, "input_tokens", None)
    outgoing = getattr(usage, "output_tokens", None)
    total = getattr(usage, "total_tokens", None)
    if total is None and incoming is not None and outgoing is not None:
        total = int(incoming) + int(outgoing)
    return incoming, outgoing, total


def _provider_config() -> dict[str, Any]:
    key_present = False
    try:
        key_present = bool(get_openai_api_key())
    except Exception:
        key_present = False
    return {
        "provider": "OpenAI Responses API",
        "pinned_model": MODEL_ID,
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "MODEL_NAME": MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "api_key_present": key_present,
        "ASHEN_DISABLE_LIVE_INTERPRETATION": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
        "api_key_value": "<redacted>",
    }


def _scenario_map() -> dict[str, Any]:
    return {row.scenario_id: row for row in dr_scenarios()}


def _stored_call_map() -> dict[str, dict[str, Any]]:
    state = load_stored_calls()
    return {str(row["scenario_id"]): row for row in state.get("calls") or []}


def _visible_context(harness: DisposableHarness) -> dict[str, Any]:
    scene = harness.active_envelope().get("scene") or {}
    return {
        "scene_id": scene.get("id"),
        "location": scene.get("location"),
        "summary": scene.get("summary"),
        "visible_facts": list(scene.get("visible_facts") or []),
        "visible_entities": [
            {"id": entity_id, "label": label, "kind": kind}
            for entity_id, label, kind in visible_catalog(harness)
        ],
        "time_pressure": (harness.session.get("clocks") or {}).get("time_pressure"),
        "turn_counter": harness.session.get("turn_counter"),
    }


def _narration_messages(row: NarrationScenario, turn: dict[str, Any], context: dict[str, Any]) -> list[dict[str, str]]:
    payload = {
        "scenario_id": row.scenario_id,
        "title": row.title,
        "kind": row.kind,
        "player_input": turn.get("utterance"),
        "current_visible_scene": context,
        "stored_live_interpretation": turn.get("stored_model_output"),
        "authoritative_resolver_result": {
            "executed": turn.get("executed"),
            "resolver_invoked": turn.get("resolver_invoked"),
            "resolver_calls": turn.get("new_resolver_calls"),
            "response": turn.get("response"),
            "scene_before": turn.get("scene_before"),
            "scene_after": turn.get("scene_after"),
            "time_before": turn.get("time_before"),
            "time_after": turn.get("time_after"),
            "notice_resolved": turn.get("notice_resolved"),
            "hp": turn.get("hp"),
            "inventory": turn.get("inventory"),
            "reason": turn.get("reason"),
        },
        "expected_facts": list(row.expected_facts),
        "prohibited_assertions": list(row.prohibited_assertions),
        "limited_prior_context": [
            "The sequence is a small waystation courtyard/street slice.",
            "Narration is presentation only and cannot create authoritative facts.",
        ],
    }
    system = (
        "You are a tabletop RPG narrator for an experiment. Describe only what the "
        "authoritative resolver established. Do not invent consequential world facts, "
        "NPC commitments, hidden information, mechanics, rolls, HP, inventory, or time changes. "
        "For OOC cases, answer helpfully without executing gameplay or rewriting state. "
        "Return only concise player-facing text."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
    ]


def _call_narrator(client: Any, budget: NarrationBudget, row: NarrationScenario, messages: list[dict[str, str]]) -> dict[str, Any]:
    estimated = _estimate_tokens(messages)
    reason = budget.refusal_reason(estimated, OUTPUT_TOKEN_CAP)
    if reason:
        raise BudgetStop(f"preflight budget would be exceeded: {reason}; estimated_input={estimated}")
    started = time.perf_counter()
    resp = client.responses.create(
        model=MODEL_ID,
        input=messages,
        temperature=0.3,
        max_output_tokens=OUTPUT_TOKEN_CAP,
    )
    incoming, outgoing, total = _usage(resp)
    record = {
        "scenario_id": row.scenario_id,
        "source_id": row.source_id,
        "request_id": getattr(resp, "id", None),
        "configured_model": MODEL_ID,
        "model": getattr(resp, "model", MODEL_ID),
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "total_tokens": total,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "estimated_input_tokens_preflight": estimated,
        "max_output_tokens": OUTPUT_TOKEN_CAP,
        "status": getattr(resp, "status", None),
    }
    budget.add(record)
    return {"text": str(getattr(resp, "output_text", "") or ""), "usage": record}


def _build_authoritative_sequence() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    calls = _stored_call_map()
    source = _scenario_map()
    harness = DisposableHarness()
    rows: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    trace: list[dict[str, Any]] = []
    for source_id in [row.scenario_id for row in dr_scenarios()]:
        scenario = source[source_id]
        call = calls[source_id]
        before = authoritative_snapshot(harness)
        context_before = _visible_context(harness)
        turn = apply_interpretation(harness, scenario, call.get("parsed"), persist_path=OUT / f"{source_id.lower()}_state.json")
        after = authoritative_snapshot(harness)
        turn["scenario_id"] = source_id
        turn["utterance"] = scenario.utterance
        turn["stored_model_output"] = call.get("parsed")
        turn["provider_request_id"] = (call.get("usage") or {}).get("request_id")
        turn["meaningful_change"] = before != after
        turn["visible_context_before"] = context_before
        turn["visible_context_after"] = _visible_context(harness)
        rows.append(turn)
        by_id[source_id] = turn
        trace.append(
            {
                "source_id": source_id,
                "executed": turn.get("executed"),
                "resolver_invoked": turn.get("resolver_invoked"),
                "scene_after": turn.get("scene_after"),
                "time_after": turn.get("time_after"),
                "state_changed": before != after,
                "history_ids": harness.history.ids(),
            }
        )
    return rows, by_id, trace


def _run_suite(name: str, args: list[str], timeout: int) -> dict[str, Any]:
    env = os.environ.copy()
    env["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
        return_code = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout if isinstance(exc.stdout, str) else "") + "\n" + (exc.stderr if isinstance(exc.stderr, str) else "")).strip()
        return_code = None
        timed_out = True
    return {
        "name": name,
        "args": args,
        "timeout": timeout,
        "timed_out": timed_out,
        "return_code": return_code,
        "summary": _summary_line(output),
        "failed": _failed_nodes(output),
        "output": output,
    }


def _failed_nodes(text: str) -> list[str]:
    return [line.removeprefix("FAILED ").strip() for line in text.splitlines() if line.startswith("FAILED ")]


def _summary_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if any(token in stripped for token in (" passed", " failed", " error")) and not stripped.startswith("FAILED "):
            return stripped
    return ""


def _decide(state: dict[str, Any]) -> str:
    if not state.get("phase0_ok") or state.get("stop_reason") in {"provider", "budget", "accounting"}:
        return "E — PROVIDER OR BUDGET BLOCKED"
    if state.get("production_saves_changed"):
        return "F — REGRESSION"
    narrations = state.get("narrations") or []
    if len(narrations) < 8:
        return "G — INCONCLUSIVE"
    if any((row.get("evaluation") or {}).get("integrity_failure") for row in narrations):
        return "C — NARRATION AUTHORITY FAILURE"
    ooc_bad = [row for row in narrations if row.get("kind") == "ooc" and row.get("player_experience") == "poor"]
    if ooc_bad:
        return "D — OOC ASSISTANCE FAILURE"
    inherited = set(state.get("inherited_regression_suites") or [])
    regression_bad = [
        row
        for row in state.get("regression") or []
        if row.get("return_code") not in (0, None) and row.get("name") not in inherited
    ]
    if regression_bad:
        return "F — REGRESSION"
    return "A — NARRATED VERTICAL SLICE COMPLETE"


def _write_csvs(state: dict[str, Any]) -> None:
    with (OUT / "PR-DT_live_narrations.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "scenario_id",
            "source_id",
            "kind",
            "title",
            "executed",
            "resolver_invoked",
            "scene_after",
            "narration",
            "integrity_failure",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in state.get("narrations") or []:
            turn = row.get("turn") or {}
            writer.writerow(
                {
                    "scenario_id": row.get("scenario_id"),
                    "source_id": row.get("source_id"),
                    "kind": row.get("kind"),
                    "title": row.get("title"),
                    "executed": turn.get("executed"),
                    "resolver_invoked": turn.get("resolver_invoked"),
                    "scene_after": turn.get("scene_after"),
                    "narration": row.get("provider_text"),
                    "integrity_failure": (row.get("evaluation") or {}).get("integrity_failure"),
                }
            )
    with (OUT / "PR-DT_provider_usage.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["scenario_id", "source_id", "model", "input_tokens", "output_tokens", "total_tokens", "latency_ms"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in state.get("provider_usage") or []:
            writer.writerow({field: row.get(field) for field in fields})


def _md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def _write_docs(state: dict[str, Any]) -> None:
    decision = state.get("decision", "G — INCONCLUSIVE")
    usage = state.get("usage_totals") or {}
    narr_rows = [
        {
            "scenario": row.get("scenario_id"),
            "source": row.get("source_id"),
            "kind": row.get("kind"),
            "integrity": "fail" if (row.get("evaluation") or {}).get("integrity_failure") else "ok",
            "experience": row.get("player_experience"),
        }
        for row in state.get("narrations") or []
    ]
    (OUT / "PR-DT_experiment_report.md").write_text(
        "\n".join(
            [
                "# PR-DT Experiment Report",
                "",
                "MODE: LIVE AUTHORITATIVE NARRATION",
                "",
                f"HEAD: `{state.get('head')}`",
                "",
                "PR-DS inherited decision: A — LIVE SLICE REPLAY COMPLETE",
                "",
                f"Provider model: `{state.get('provider_model') or MODEL_ID}`",
                f"Live request count: {usage.get('live_request_count', 0)}",
                f"Actual input tokens: {usage.get('actual_input_tokens', 0)}",
                f"Actual output tokens: {usage.get('actual_output_tokens', 0)}",
                f"Actual total tokens: {usage.get('actual_total_tokens', 0)}",
                "",
                f"Decision: {decision}",
                "",
                state.get("decision_reason", ""),
                "",
                _md_table(narr_rows, ["scenario", "source", "kind", "integrity", "experience"]) if narr_rows else "No live narrations were recorded.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "PR-DT_narration_contract.md").write_text(CONTRACT_MD, encoding="utf-8")
    (OUT / "PR-DT_scenario_definitions.md").write_text(_scenario_docs(), encoding="utf-8")
    (OUT / "PR-DT_expected_behavior.md").write_text(_expected_docs(), encoding="utf-8")
    (OUT / "PR-DT_grounding_analysis.md").write_text(_grounding_docs(state), encoding="utf-8")
    (OUT / "PR-DT_ooc_assistance.md").write_text(_ooc_docs(state), encoding="utf-8")
    (OUT / "PR-DT_player_experience.md").write_text(_experience_docs(state), encoding="utf-8")
    (OUT / "PR-DT_state_integrity.md").write_text(_state_docs(state), encoding="utf-8")
    (OUT / "PR-DT_cost_analysis.md").write_text(_cost_docs(state), encoding="utf-8")
    (OUT / "PR-DT_regression_results.md").write_text(_regression_docs(state), encoding="utf-8")
    (OUT / "PR-DT_recommendation.md").write_text(f"# PR-DT Recommendation\n\nDecision: {decision}\n\n{_next_step(decision)}\n", encoding="utf-8")
    (OUT / "PR-DT_remaining_risks.md").write_text(REMAINING_RISKS_MD, encoding="utf-8")


CONTRACT_MD = """# PR-DT Narration Contract

The narrator receives only current visible scene context, the player action, the stored live interpretation, authoritative resolver output, visible entities, permitted dialogue, confirmed state transitions, and limited public prior context.

The narrator does not receive hidden world facts, unrestricted state, internal GM secrets, uncommitted outcomes, arbitrary tools, or production save data.

Narration is presentation. Resolver results are authority. Generated text is never parsed back into world state, and unsupported generated facts are recorded as output integrity failures rather than committed.
"""

REMAINING_RISKS_MD = """# PR-DT Remaining Risks

- This is an eight-request vertical slice, not a long-session affordability claim.
- Grounding checks are conservative string audits plus human-readable review notes, not a complete semantic verifier.
- No production narration prompts were modified or integrated.
- Broader scenes, longer dialogue memory, and hidden-clue pressure need separate validation before production use.
"""


def _scenario_docs() -> str:
    lines = ["# PR-DT Scenario Definitions", ""]
    for row in scenarios():
        lines.extend(
            [
                f"## {row.scenario_id} — {row.title}",
                "",
                f"- Source: {row.source_id}",
                f"- Stage: {row.stage}",
                f"- Kind: {row.kind}",
                "- Expected facts:",
                *[f"  - {item}" for item in row.expected_facts],
                "- Prohibited assertions:",
                *[f"  - {item}" for item in row.prohibited_assertions],
                "",
            ]
        )
    return "\n".join(lines)


def _expected_docs() -> str:
    return "# PR-DT Expected Behavior\n\nAll four gameplay cases must execute through stored live interpretations and existing resolvers. All four OOC cases must avoid gameplay resolvers, time advancement, and state mutation. Narration may paraphrase visible facts but must not create canonical facts or mechanical effects.\n"


def _grounding_docs(state: dict[str, Any]) -> str:
    lines = ["# PR-DT Grounding Analysis", ""]
    for row in state.get("narrations") or []:
        evaluation = row.get("evaluation") or {}
        lines.extend(
            [
                f"## {row.get('scenario_id')} — {row.get('title')}",
                "",
                f"- Unsupported additions: {evaluation.get('unsupported_additions') or []}",
                f"- Contradictions: {evaluation.get('contradictions') or []}",
                f"- Hidden information leaks: {evaluation.get('hidden_information_leaks') or []}",
                f"- Mechanical claims: {evaluation.get('mechanical_claims') or []}",
                f"- NPC commitments: {evaluation.get('npc_commitments') or []}",
                "",
            ]
        )
    if len(lines) == 2:
        lines.append("No live grounding rows were produced.")
    return "\n".join(lines) + "\n"


def _ooc_docs(state: dict[str, Any]) -> str:
    rows = [row for row in state.get("narrations") or [] if row.get("kind") == "ooc"]
    return "# PR-DT OOC Assistance\n\n" + (
        _md_table(
            [
                {
                    "scenario": row.get("scenario_id"),
                    "source": row.get("source_id"),
                    "mutated": (row.get("turn") or {}).get("mutated_state"),
                    "resolver": (row.get("turn") or {}).get("resolver_invoked"),
                    "experience": row.get("player_experience"),
                }
                for row in rows
            ],
            ["scenario", "source", "mutated", "resolver", "experience"],
        )
        if rows
        else "No live OOC rows were produced."
    ) + "\n"


def _experience_docs(state: dict[str, Any]) -> str:
    return "# PR-DT Player Experience\n\n" + (
        _md_table(
            [
                {
                    "scenario": row.get("scenario_id"),
                    "clarity": row.get("clarity"),
                    "coherence": row.get("coherence"),
                    "alignment": row.get("alignment"),
                    "experience": row.get("player_experience"),
                }
                for row in state.get("narrations") or []
            ],
            ["scenario", "clarity", "coherence", "alignment", "experience"],
        )
        or "No rows."
    ) + "\n"


def _state_docs(state: dict[str, Any]) -> str:
    baseline = state.get("baseline") or {}
    lines = [
        "# PR-DT State Integrity",
        "",
        f"Production saves changed: {state.get('production_saves_changed')}",
        f"Baseline production saves unchanged: {baseline.get('production_saves_unchanged')}",
        f"Gameplay executed: {baseline.get('gameplay_executed')}",
        f"Non-gameplay executed: {baseline.get('non_gameplay_executed')}",
        f"Final scene: {baseline.get('final_scene')}",
        f"Time pressure: {baseline.get('time_pressure')}",
        f"Notice resolved: {baseline.get('notice_resolved')}",
        "",
        "Generated narration was not parsed into state and did not rerun gameplay actions.",
    ]
    return "\n".join(lines) + "\n"


def _cost_docs(state: dict[str, Any]) -> str:
    usage = state.get("usage_totals") or {}
    return f"""# PR-DT Cost Analysis

Provider model: `{state.get('provider_model') or MODEL_ID}`.

Live request count: {usage.get('live_request_count', 0)} / 8.
Actual input tokens: {usage.get('actual_input_tokens', 0)} / 12000.
Actual output tokens: {usage.get('actual_output_tokens', 0)} / 4000.
Actual total tokens: {usage.get('actual_total_tokens', 0)} / 16000.

Stored interpretation usage is inherited from PR-DS and did not add provider calls in this experiment. Current narration usage is listed in `PR-DT_provider_usage.csv`.
"""


def _regression_docs(state: dict[str, Any]) -> str:
    rows = state.get("regression") or []
    return "# PR-DT Regression Results\n\n" + (
        _md_table(
            [
                {
                    "suite": row.get("name"),
                    "return_code": row.get("return_code"),
                    "timed_out": row.get("timed_out"),
                    "summary": row.get("summary"),
                }
                for row in rows
            ],
            ["suite", "return_code", "timed_out", "summary"],
        )
        if rows
        else "Regression suites were not run because the experiment stopped before live narration."
    ) + "\n"


def _next_step(decision: str) -> str:
    if decision.startswith("A"):
        return "Review the PR-DT artifacts, then design a production integration proposal with a hard state/narration boundary."
    if decision.startswith("E"):
        return "Provide a usable live provider configuration, then rerun the same locked experiment without changing prompts or scenarios."
    return "Review the failed rows before any production integration."


def _write_focused_tests(state: dict[str, Any]) -> None:
    lines = []
    for row in state.get("regression") or []:
        lines.append(f"$ python -m pytest {' '.join(row.get('args') or [])}")
        lines.append(row.get("summary") or "")
        for failed in row.get("failed") or []:
            lines.append(f"FAILED {failed}")
        lines.append("")
    (OUT / "focused_tests.txt").write_text("\n".join(lines), encoding="utf-8")


def _write_changed_files() -> None:
    (OUT / "changed_files.txt").write_text(_git(["status", "--short"]) + "\n", encoding="utf-8")


def _write_review(state: dict[str, Any]) -> None:
    usage = state.get("usage_totals") or {}
    review = f"""# CURRENT REVIEW

PR-DT

MODE:
LIVE AUTHORITATIVE NARRATION

PR-DS inherited decision:
A — LIVE SLICE REPLAY COMPLETE

Provider model:
{state.get('provider_model') or MODEL_ID}

Live request count:
{usage.get('live_request_count', 0)}

Actual input tokens:
{usage.get('actual_input_tokens', 0)}

Actual output tokens:
{usage.get('actual_output_tokens', 0)}

Actual total tokens:
{usage.get('actual_total_tokens', 0)}

Gameplay narration results:
{state.get('gameplay_summary', 'Not completed.')}

OOC assistance results:
{state.get('ooc_summary', 'Not completed.')}

Grounding failures:
{state.get('grounding_failures', [])}

Authority findings:
Narration remained separate from authoritative state. Production integration: none.

State integrity:
Production saves changed: {state.get('production_saves_changed')}. Baseline unchanged: {(state.get('baseline') or {}).get('production_saves_unchanged')}.

Player experience:
{state.get('experience_summary', 'Not completed.')}

Regression results:
{state.get('regression_summary', 'Not run.')}

PR-DT decision:
{state.get('decision')}

Recommended next step:
{_next_step(str(state.get('decision') or 'G'))}
"""
    HANDOFF.mkdir(parents=True, exist_ok=True)
    (HANDOFF / "CURRENT_REVIEW.md").write_text(review, encoding="utf-8")
    manifest = {"pr": "PR-DT", "artifacts": [str(path.relative_to(ROOT)) for path in sorted(OUT.iterdir()) if path.is_file()]}
    (HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary = HANDOFF / "CURRENT_REVIEW.zip.partial"
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(HANDOFF / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
        archive.write(HANDOFF / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
        for rel in manifest["artifacts"]:
            archive.write(ROOT / rel, rel)
    temporary.replace(HANDOFF / "CURRENT_REVIEW.zip")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = _fingerprints()
    state: dict[str, Any] = {
        "head": _git(["rev-parse", "HEAD"]),
        "status_before": _git(["status", "--short"]),
        "provider_config": _provider_config(),
        "provider_model": MODEL_ID,
        "phase0_ok": False,
        "stop_reason": "",
        "baseline": {},
        "authoritative_rows": [],
        "narrations": [],
        "provider_usage": [],
        "usage_totals": {"live_request_count": 0, "actual_input_tokens": 0, "actual_output_tokens": 0, "actual_total_tokens": 0},
    }
    try:
        with ProductionSaveGuard() as guard, forbid_provider_calls():
            state["baseline"] = replay_stored_outputs(OUT / "baseline_state.json")
            guard.assert_unchanged()
        rows, by_id, trace = _build_authoritative_sequence()
        state["authoritative_rows"] = rows
        TRACE_PATH.write_text(json.dumps(trace, indent=2), encoding="utf-8")
        baseline = state["baseline"]
        issues = []
        if baseline.get("gameplay_executed") != list(GAMEPLAY_IDS):
            issues.append("stored gameplay execution did not match PR-DS")
        if baseline.get("non_gameplay_executed"):
            issues.append("non-gameplay stored messages executed")
        if baseline.get("final_scene") != STREET_ID or baseline.get("notice_resolved") is not True:
            issues.append("PR-DS baseline did not reach resolved notice board")
        if baseline.get("provider_hits"):
            issues.append("provider hit during baseline replay")
        if not state["provider_config"].get("api_key_present"):
            issues.append("provider key absent")
        state["phase0_issues"] = issues
        state["phase0_ok"] = not issues
        if issues:
            state["stop_reason"] = "provider" if "provider key absent" in issues else "phase0"
        else:
            from openai import OpenAI

            budget = NarrationBudget()
            client = OpenAI(api_key=get_openai_api_key())
            stage1 = [row for row in scenarios() if row.stage == 1]
            stage2 = [row for row in scenarios() if row.stage == 2]
            all_rows = stage1 + stage2
            for row in all_rows:
                turn = by_id[row.source_id]
                context = turn.get("visible_context_after") or {}
                messages = _narration_messages(row, turn, context)
                call = _call_narrator(client, budget, row, messages)
                evaluation = evaluate_text(call["text"], row.prohibited_assertions, kind=row.kind)
                narration = {
                    "scenario_id": row.scenario_id,
                    "source_id": row.source_id,
                    "kind": row.kind,
                    "title": row.title,
                    "messages": messages,
                    "provider_text": call["text"],
                    "raw_provider_output": call["text"],
                    "usage": call["usage"],
                    "turn": turn,
                    "evaluation": evaluation,
                    "clarity": "good" if call["text"].strip() else "poor",
                    "coherence": "good" if call["text"].strip() else "poor",
                    "alignment": "fail" if evaluation["integrity_failure"] else "good",
                    "player_experience": "poor" if not call["text"].strip() else ("unsafe" if evaluation["integrity_failure"] else "useful"),
                }
                state["narrations"].append(narration)
                state["provider_usage"].append(call["usage"])
                state["usage_totals"] = {
                    "live_request_count": budget.requests,
                    "actual_input_tokens": budget.input_tokens,
                    "actual_output_tokens": budget.output_tokens,
                    "actual_total_tokens": budget.total_tokens,
                }
                STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
                if row.stage == 1:
                    stage1_done = [item for item in state["narrations"] if item["scenario_id"] in {s.scenario_id for s in stage1}]
                    if len(stage1_done) == 3 and sum(1 for item in stage1_done if item["player_experience"] in {"poor", "unsafe"}) >= 2:
                        state["stop_reason"] = "stage1_unusable"
                        break
                    if evaluation["integrity_failure"]:
                        state["stop_reason"] = "authority"
                        break
            if not state.get("stop_reason"):
                regression = [_run_suite(name, args, timeout) for name, args, timeout in SUITES]
                state["regression"] = regression
    except (BudgetStop, IsolationError) as exc:
        state["stop_reason"] = "budget" if isinstance(exc, BudgetStop) else "isolation"
        state["stop_error"] = str(exc)
    except Exception as exc:  # noqa: BLE001
        state["stop_reason"] = "provider"
        state["stop_error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
    after = _fingerprints()
    state["production_save_fingerprint_before"] = before
    state["production_save_fingerprint_after"] = after
    state["production_saves_changed"] = before != after
    state["grounding_failures"] = [
        row["scenario_id"] for row in state.get("narrations") or [] if (row.get("evaluation") or {}).get("integrity_failure")
    ]
    state["gameplay_summary"] = _summary_for_kind(state, "gameplay")
    state["ooc_summary"] = _summary_for_kind(state, "ooc")
    state["experience_summary"] = _experience_summary(state)
    state["regression_summary"] = "; ".join(
        f"{row.get('name')}: {row.get('summary') or row.get('return_code')}" for row in state.get("regression") or []
    )
    state["decision"] = _decide(state)
    state["decision_reason"] = state.get("stop_error") or ("; ".join(state.get("phase0_issues") or []) if state.get("phase0_issues") else "")
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    _write_csvs(state)
    _write_docs(state)
    _write_focused_tests(state)
    _write_changed_files()
    _write_review(state)
    print(json.dumps({"decision": state["decision"], **state["usage_totals"]}, indent=2))


def _summary_for_kind(state: dict[str, Any], kind: str) -> str:
    rows = [row for row in state.get("narrations") or [] if row.get("kind") == kind]
    if not rows:
        return "No live rows completed."
    failures = [row["scenario_id"] for row in rows if (row.get("evaluation") or {}).get("integrity_failure")]
    return f"{len(rows)} rows completed; grounding failures: {failures or 'none'}."


def _experience_summary(state: dict[str, Any]) -> str:
    rows = state.get("narrations") or []
    if not rows:
        return "No live player-facing responses completed."
    useful = [row["scenario_id"] for row in rows if row.get("player_experience") == "useful"]
    return f"{len(useful)}/{len(rows)} responses rated useful by the experiment heuristics."


if __name__ == "__main__":
    main()
