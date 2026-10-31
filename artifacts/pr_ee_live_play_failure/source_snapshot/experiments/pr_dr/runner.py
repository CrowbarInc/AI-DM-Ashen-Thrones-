"""PR-DR staged live vertical slice.

Commands: prepare, stage1, stage2, finalize.
prepare does not call a provider. Expected labels are not edited after prepare.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dr_live_vertical_slice"
STATE_PATH = OUT / "state.json"
DISPOSABLE_PATH = OUT / "disposable_session.json"
HANDOFF = ROOT / "handoff"

from experiments.pr_dg.isolation import IsolationError, ProductionSaveGuard, WATCHED, forbid_provider_calls  # noqa: E402
from experiments.pr_do.adapter import adapt_interpretation  # noqa: E402
from experiments.pr_do.schema import schema_grants_execution  # noqa: E402
from experiments.pr_dp.budget import BudgetStop  # noqa: E402
from experiments.pr_dp.prompt import provider_schema  # noqa: E402
from experiments.pr_dq.gameplay import DisposableHarness  # noqa: E402
from experiments.pr_dq.slice import run_vertical_slice  # noqa: E402
from experiments.pr_dq.world import STREET_ID  # noqa: E402
from experiments.pr_dr import MODEL_ID  # noqa: E402
from experiments.pr_dr.budget import OUTPUT_TOKEN_CAP, SliceBudget  # noqa: E402
from experiments.pr_dr.decide import (  # noqa: E402
    RULE_TEXT,
    decide,
    failure_class,
    is_unusable,
    isolation_breaches,
)
from experiments.pr_dr.persist import read_state  # noqa: E402
from experiments.pr_dr.prompt import build_messages, context_leaks, preflight_tokens, visible_catalog  # noqa: E402
from experiments.pr_dr.reports import write_reports  # noqa: E402
from experiments.pr_dr.scenarios import DECISION_RULE, scenarios  # noqa: E402
from experiments.pr_dr.turn import apply_interpretation  # noqa: E402

_SECRET_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}|Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)

SUITES = (
    ("PR-DR", ["tests/test_pr_dr_live_vertical_slice.py", "-q", "--tb=line"], 180),
    (
        "PR-DQ",
        ["tests/test_pr_dq_ic_ooc_messages.py", "tests/test_pr_dq_vertical_slice.py", "-q", "--tb=line"],
        180,
    ),
    ("PR-DO", ["tests/test_pr_do_authority_separation.py", "-q", "--tb=line"], 120),
    ("PR-DP", ["tests/test_pr_dp_contract_qualification.py", "-q", "--tb=line"], 180),
    ("Authority", ["tests/test_pr_cx_authority_assurance.py", "-q", "--tb=line"], 180),
    ("Conversation", ["tests/test_conversational_memory_window.py", "-q", "--tb=line"], 180),
    ("Turn pipeline", ["tests/test_turn_pipeline_shared.py", "-q", "--tb=line"], 300),
)


def redact(text: str) -> str:
    return _SECRET_RE.sub("[REDACTED]", text)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return _sha_bytes(path.read_bytes())


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return (completed.stdout or "") + (completed.stderr or "")


def _provider_config() -> dict[str, Any]:
    from game.config import DEFAULT_MODEL_NAME, HIGH_PRECISION_MODEL_NAME, MODEL_NAME

    return {
        "pinned_model": MODEL_ID,
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "MODEL_NAME": MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "api_key_present": bool(os.getenv("OPENAI_API_KEY") or ""),
        "ASHEN_DISABLE_LIVE_INTERPRETATION": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
        "unrelated_provider_paths": "game.gm.call_gpt and semantic_interpreter are patched closed during the run",
        "note": "The key value is not stored. PR-DR calls only gpt-4.1-mini through the experiment client.",
    }


def _save_fingerprints() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for path in WATCHED:
        if path.exists():
            data = path.read_bytes()
            out[path.name] = {"sha256": _sha_bytes(data), "size": len(data)}
        else:
            out[path.name] = {"sha256": None, "size": None}
    return out


def _labels_blob() -> str:
    rows = []
    for row in scenarios():
        rows.append(
            {
                "scenario_id": row.scenario_id,
                "stage": row.stage,
                "category": row.category,
                "utterance": row.utterance,
                "mode_override": row.mode_override,
                "role": row.role,
                "acceptable_modes": row.acceptable_modes,
                "acceptable_classes": row.acceptable_classes,
                "acceptable_targets": row.acceptable_targets,
                "expect_execution": row.expect_execution,
                "required_operation": row.required_operation,
                "required_target": row.required_target,
                "required_scene": row.required_scene,
            }
        )
    return json.dumps({"scenarios": rows, "rule": DECISION_RULE, "rule_text": RULE_TEXT}, sort_keys=True)


def _baseline_ok(report: dict[str, Any]) -> bool:
    steps = report.get("steps") or []
    if [step.get("message_id") for step in steps] != ["msg_001", "msg_002", "msg_003", "msg_004", "msg_005"]:
        return False
    if [step.get("mode") for step in steps] != ["IC", "OOC", "IC", "IC", "IC"]:
        return False
    if [step.get("executed") for step in steps] != [True, False, True, True, True]:
        return False
    if steps[1].get("mutated_state") or steps[1].get("resolver_invoked"):
        return False
    return bool(
        report.get("final_scene") == "waystation_street"
        and report.get("time_pressure") == 1
        and report.get("notice_resolved") is True
        and report.get("resolver_calls")
        == [
            "game.exploration.resolve_exploration_action",
            "game.social.resolve_social_action",
            "game.exploration.resolve_exploration_action",
            "game.exploration.resolve_exploration_action",
        ]
    )


def _production_links() -> list[str]:
    hits = []
    for folder in (ROOT / "game", ROOT / "tools"):
        if not folder.exists():
            continue
        for path in folder.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if "experiments.pr_dr" in text:
                rel = str(path.relative_to(ROOT)).replace("\\", "/")
                if rel == "game/live_chat_interpretation.py":
                    continue
                hits.append(rel)
    return hits


def _estimate_budget() -> dict[str, Any]:
    courtyard = DisposableHarness()
    street = DisposableHarness()
    street.session["active_scene_id"] = STREET_ID
    rows = []
    projected_input = 0
    for scenario in scenarios():
        harness = street if scenario.scenario_id == "DR10" else courtyard
        messages = build_messages(scenario.utterance, harness)
        leaks = context_leaks(messages, scenario.utterance)
        estimate = preflight_tokens(messages)
        projected_input += estimate
        rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "estimated_input_tokens": estimate,
                "context_leaks": leaks,
                "visible_ids": [entity_id for entity_id, _label, _kind in visible_catalog(harness)],
            }
        )
    return {
        "rows": rows,
        "projected_estimated_input": projected_input,
        "output_cap_times_requests": OUTPUT_TOKEN_CAP * len(rows),
        "estimator": "bytes/3 plus 64, checked again before each live request against actual usage",
    }


def _write_locked_docs() -> None:
    from experiments.pr_dr.reports import expected_behavior, scenario_definitions

    (OUT / "PR-DR_scenario_definitions.md").write_text(scenario_definitions(), encoding="utf-8")
    (OUT / "PR-DR_expected_behavior.md").write_text(expected_behavior(), encoding="utf-8")


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        raise SystemExit("PR-DR state is missing. Run prepare first.")
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _write_state(state: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(redact(json.dumps(state, indent=2)), encoding="utf-8")


def _verify_labels(state: dict[str, Any]) -> None:
    if _sha_bytes(_labels_blob().encode("utf-8")) != state.get("labels_sha256"):
        raise SystemExit("Expected labels changed after prepare. Live calls are refused.")
    for name in ("PR-DR_expected_behavior.md", "PR-DR_scenario_definitions.md"):
        if _sha_file(OUT / name) != (state.get("files") or {}).get(name):
            raise SystemExit(f"{name} changed after prepare. Live calls are refused.")


def prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = _git(["rev-parse", "HEAD"]).strip()
    porcelain = _git(["status", "--porcelain"])
    opening = DisposableHarness()
    fingerprints = _save_fingerprints()
    issues: list[str] = []
    try:
        with ProductionSaveGuard() as guard, forbid_provider_calls():
            baseline = run_vertical_slice()
            sample = adapt_interpretation(
                {"communication_mode": "OTHER"},
                permitted_ids=["courtyard_lantern"],
            )
            if sample.get("executed") or sample.get("mutated_state") or sample.get("authoritative_effects"):
                issues.append("interpretation adapter can mutate or execute")
            if schema_grants_execution(provider_schema()):
                issues.append("provider schema grants execution")
        guard.assert_unchanged()
    except IsolationError as exc:
        issues.append(redact(str(exc)))
        baseline = {}
    if _save_fingerprints() != fingerprints:
        issues.append("production save fingerprint changed during prepare")
    links = _production_links()
    if links:
        issues.append("production modules import experiments.pr_dr: " + ", ".join(links))
    if not _baseline_ok(baseline):
        issues.append("PR-DQ baseline failed")
    estimates = _estimate_budget()
    if any(row["context_leaks"] for row in estimates["rows"]):
        issues.append("prompt context contains a hidden probe")
    if not estimates["rows"] or estimates["rows"][0]["estimated_input_tokens"] <= 0:
        issues.append("token estimate unavailable")
    config = _provider_config()
    if not config["api_key_present"]:
        issues.append("provider key absent")
    _write_locked_docs()
    files = {
        name: _sha_file(OUT / name)
        for name in ("PR-DR_expected_behavior.md", "PR-DR_scenario_definitions.md")
    }
    state = {
        "phase0_ok": not issues,
        "issues": issues,
        "head": head,
        "status_lines": len([line for line in porcelain.splitlines() if line.strip()]),
        "status_sha256": _sha_bytes(porcelain.encode("utf-8")),
        "dirty_worktree_preserved": True,
        "provider": config,
        "fingerprints": fingerprints,
        "baseline": baseline,
        "baseline_ok": _baseline_ok(baseline),
        "estimates": estimates,
        "opening_hp": opening.character.get("hp"),
        "opening_inventory": opening.session.get("inventory"),
        "labels_sha256": _sha_bytes(_labels_blob().encode("utf-8")),
        "files": files,
        "budget": SliceBudget().to_dict(),
        "calls": [],
        "stop_reason": "" if not issues else "phase0",
        "live_started": False,
    }
    _write_state(state)
    print(json.dumps({"phase0_ok": state["phase0_ok"], "issues": issues, "head": head}, indent=2))


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


def _call_one(client: Any, budget: SliceBudget, scenario_id: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    schema = provider_schema()
    estimated = preflight_tokens(messages)
    reason = budget.refusal_reason(estimated, OUTPUT_TOKEN_CAP)
    if reason:
        raise BudgetStop(f"preflight budget would be exceeded: {reason}; estimated_input={estimated}")
    started = time.perf_counter()
    try:
        resp = client.responses.create(
            model=MODEL_ID,
            input=messages,
            temperature=0,
            max_output_tokens=OUTPUT_TOKEN_CAP,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pr_dr_interpretation",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
    except BudgetStop:
        raise
    except Exception as exc:  # noqa: BLE001 - no retry and no model switch
        raise BudgetStop(
            f"provider request failed without retry: {type(exc).__name__}: {redact(str(exc))[:400]}"
        ) from exc
    incoming, outgoing, total = _usage_triplet(resp)
    model = str(getattr(resp, "model", "") or "")
    record = {
        "scenario_id": scenario_id,
        "request_id": getattr(resp, "id", None),
        "configured_model": MODEL_ID,
        "model": model,
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "total_tokens": total,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "estimated_input_tokens_preflight": estimated,
        "max_output_tokens": OUTPUT_TOKEN_CAP,
        "status": getattr(resp, "status", None),
    }
    budget.add(record)
    if model and not model.startswith(MODEL_ID):
        raise BudgetStop(f"provider returned a different model ({model}); automatic switching is forbidden")
    return {"text": str(getattr(resp, "output_text", "") or ""), "record": record}


def _load_harness(state: dict[str, Any]) -> DisposableHarness:
    if DISPOSABLE_PATH.exists() and state.get("calls"):
        harness, _snapshot = read_state(DISPOSABLE_PATH)
        return harness
    return DisposableHarness()


def _run_saved_or_live(client: Any, budget: SliceBudget, state: dict[str, Any], scenario) -> dict[str, Any]:
    harness = _load_harness(state)
    if scenario.scenario_id.lower() in harness.history.ids():
        raise BudgetStop("disposable history already contains this message; not reapplying")
    messages = build_messages(scenario.utterance, harness)
    leaks = context_leaks(messages, scenario.utterance)
    if leaks:
        raise BudgetStop(f"prompt context contains hidden probes: {leaks}")
    if "notice_board" in " ".join(leaks):
        raise BudgetStop("hidden notice leaked into context")
    visible = [entity_id for entity_id, _label, _kind in visible_catalog(harness)]
    scene_id = str(harness.session.get("active_scene_id") or "")
    if scene_id != STREET_ID and "notice_board" in visible:
        raise BudgetStop("notice board became visible before the street scene")
    call = _call_one(client, budget, scenario.scenario_id, messages)
    parsed = None
    parse_error = ""
    try:
        parsed = json.loads(call["text"])
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
    started = time.perf_counter()
    turn = apply_interpretation(
        harness,
        scenario,
        parsed if isinstance(parsed, dict) else None,
        persist_path=DISPOSABLE_PATH,
    )
    local_ms = round((time.perf_counter() - started) * 1000, 3)
    breaches = isolation_breaches(
        turn,
        scenario,
        opening_hp=state.get("opening_hp"),
        opening_inventory=state.get("opening_inventory") or [],
    )
    turn["scenario_id"] = scenario.scenario_id
    turn["stage"] = scenario.stage
    turn["category"] = scenario.category
    turn["isolation_breaches"] = breaches
    turn["failure_class"] = failure_class(turn, scenario)
    turn["unusable"] = is_unusable(turn, scenario) if scenario.stage == 1 else False
    turn["local_resolution_ms"] = local_ms
    return {
        "scenario_id": scenario.scenario_id,
        "stage": scenario.stage,
        "category": scenario.category,
        "utterance": scenario.utterance,
        "messages": messages,
        "provider_text": redact(call["text"]),
        "parse_error": parse_error,
        "parsed": parsed,
        "usage": call["record"],
        "turn": turn,
    }


def _execute(stage: int) -> None:
    state = _load_state()
    if not state.get("phase0_ok"):
        raise SystemExit("Phase 0 did not pass. Refusing live calls.")
    _verify_labels(state)
    if state.get("stop_reason"):
        raise SystemExit(f"Experiment already stopped: {state['stop_reason']}")
    if state.get("in_flight") and not state.get("pending_provider_text"):
        state["stop_reason"] = "provider"
        _write_state(state)
        raise SystemExit("A provider request was left in flight. It will not be retried.")
    wanted = [row for row in scenarios() if row.stage == stage]
    done = {row["scenario_id"] for row in state.get("calls") or []}
    if stage == 2 and any(row.scenario_id not in done for row in scenarios() if row.stage == 1):
        raise SystemExit("Stage 1 is incomplete.")
    pending = [row for row in wanted if row.scenario_id not in done]
    if not pending:
        print(f"Stage {stage} already recorded.")
        return
    from openai import OpenAI

    from game.config import get_openai_api_key

    budget = SliceBudget.from_dict(state.get("budget"))
    calls = list(state.get("calls") or [])
    fingerprints = _save_fingerprints()
    state["live_started"] = True
    client = OpenAI(api_key=get_openai_api_key())
    try:
        with ProductionSaveGuard() as guard, forbid_provider_calls():
            for scenario in pending:
                state["in_flight"] = scenario.scenario_id
                _write_state(state)
                result = _run_saved_or_live(client, budget, state, scenario)
                calls.append(result)
                state["calls"] = calls
                state["budget"] = budget.to_dict()
                state["in_flight"] = ""
                _write_state(state)
                (OUT / "raw_results.json").write_text(redact(json.dumps(state, indent=2)), encoding="utf-8")
                breaches = result["turn"].get("isolation_breaches") or []
                if breaches:
                    state["stop_reason"] = "authority"
                    _write_state(state)
                    raise BudgetStop("unauthorized effect: " + ",".join(breaches))
            if stage == 1:
                stage_rows = [row for row in calls if row["stage"] == 1]
                unusable = sum(1 for row in stage_rows if row["turn"].get("unusable"))
                if unusable >= 2:
                    state["stop_reason"] = "stage1_unusable"
                    _write_state(state)
        guard.assert_unchanged()
    except IsolationError as exc:
        state["stop_reason"] = "isolation"
        _write_state(state)
        raise SystemExit(redact(str(exc))) from exc
    except BudgetStop as exc:
        if not state.get("stop_reason"):
            message = str(exc)
            if "accounting" in message or "usage" in message:
                state["stop_reason"] = "accounting"
            elif "preflight" in message or "ceiling" in message or "budget" in message:
                state["stop_reason"] = "budget"
            elif "unauthorized" in message:
                state["stop_reason"] = "authority"
            else:
                state["stop_reason"] = "provider"
        _write_state(state)
        raise SystemExit(redact(str(exc))) from exc
    if _save_fingerprints() != fingerprints:
        state["stop_reason"] = "isolation"
        _write_state(state)
        raise SystemExit("Production save fingerprint changed during live calls.")
    _write_state(state)
    print(json.dumps({"stage": stage, "requests": budget.requests, "stop": state.get("stop_reason") or ""}, indent=2))


def _failed_nodes(text: str) -> list[str]:
    return [
        line.strip().removeprefix("FAILED ").strip()
        for line in text.splitlines()
        if line.strip().startswith("FAILED ")
    ]


def _summary_line(combined: str) -> str:
    normalized = combined.replace("\r\n", "\n").replace("\r", "\n")
    for line in normalized.splitlines():
        stripped = line.strip()
        if stripped.startswith(("FAILED ", "PASSED ", "ERROR ")):
            continue
        if any(token in stripped for token in (" passed", " failed", " error")):
            return stripped
    bar = ""
    for line in normalized.splitlines():
        if "[100%]" in line:
            bar = line
    chunk = bar.split("[", 1)[0] if bar else ""
    marks = (
        ("passed", chunk.count(".")),
        ("failed", chunk.count("F")),
        ("errors", chunk.count("E")),
        ("skipped", chunk.count("s")),
    )
    parts = [f"{count} {name}" for name, count in marks if count]
    if parts:
        return ", ".join(parts)
    failed = len(_failed_nodes(normalized))
    if failed:
        return f"{failed} failed"
    return ""


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
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        return_code = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return_code = None
        timed_out = True
    combined = (stdout + "\n" + stderr).strip()
    return {
        "name": name,
        "args": args,
        "timeout": timeout,
        "timed_out": timed_out,
        "return_code": return_code,
        "summary": _summary_line(combined),
        "output": combined,
        "failed": _failed_nodes(combined),
    }


def finalize() -> None:
    state = _load_state()
    rows = [_run_suite(name, args, timeout) for name, args, timeout in SUITES]
    state["regression"] = [
        {key: row[key] for key in ("name", "args", "timeout", "timed_out", "return_code", "summary", "failed", "output")}
        for row in rows
    ]
    turns = [row["turn"] for row in state.get("calls") or []]
    state["decision"] = decide(
        turns,
        scenarios(),
        stop_reason=str(state.get("stop_reason") or ""),
        phase0_ok=bool(state.get("phase0_ok")),
    )
    _write_state(state)
    (OUT / "raw_results.json").write_text(redact(json.dumps(state, indent=2)), encoding="utf-8")
    write_reports(state, rows)
    _write_csv(state)
    _write_zip()
    print(json.dumps({"decision": state["decision"], "requests": (state.get("budget") or {}).get("requests")}, indent=2))


def _write_csv(state: dict[str, Any]) -> None:
    interpretations = OUT / "PR-DR_live_interpretations.csv"
    usage = OUT / "PR-DR_provider_usage.csv"
    with interpretations.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "stage",
                "category",
                "model",
                "schema_valid",
                "predicted_mode",
                "envelope_mode",
                "mode_source",
                "intent",
                "destination",
                "interpretation_status",
                "operation_classes",
                "target_refs",
                "disposition",
                "executed",
                "resolver_invoked",
                "mutated_state",
                "failure_class",
                "scene_after",
                "response",
            ],
        )
        writer.writeheader()
        for row in state.get("calls") or []:
            turn = row["turn"]
            message = turn.get("message") or {}
            writer.writerow(
                {
                    "scenario_id": row["scenario_id"],
                    "stage": row["stage"],
                    "category": row["category"],
                    "model": (row.get("usage") or {}).get("model"),
                    "schema_valid": turn.get("schema_valid"),
                    "predicted_mode": turn.get("predicted_mode"),
                    "envelope_mode": message.get("mode"),
                    "mode_source": message.get("mode_source"),
                    "intent": message.get("intent"),
                    "destination": message.get("destination"),
                    "interpretation_status": turn.get("interpretation_status"),
                    "operation_classes": "|".join(turn.get("operation_classes") or []),
                    "target_refs": "|".join(turn.get("target_refs") or []),
                    "disposition": turn.get("disposition"),
                    "executed": turn.get("executed"),
                    "resolver_invoked": turn.get("resolver_invoked"),
                    "mutated_state": turn.get("mutated_state"),
                    "failure_class": turn.get("failure_class"),
                    "scene_after": turn.get("scene_after"),
                    "response": turn.get("response"),
                }
            )
    with usage.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "model",
                "input_tokens",
                "output_tokens",
                "total_tokens",
                "latency_ms",
                "estimated_input_tokens",
                "local_resolution_ms",
            ],
        )
        writer.writeheader()
        for row in state.get("calls") or []:
            usage_row = row.get("usage") or {}
            writer.writerow(
                {
                    "scenario_id": row["scenario_id"],
                    "model": usage_row.get("model"),
                    "input_tokens": usage_row.get("input_tokens"),
                    "output_tokens": usage_row.get("output_tokens"),
                    "total_tokens": usage_row.get("total_tokens"),
                    "latency_ms": usage_row.get("latency_ms"),
                    "estimated_input_tokens": usage_row.get("estimated_input_tokens_preflight"),
                    "local_resolution_ms": row["turn"].get("local_resolution_ms"),
                }
            )


def _write_zip() -> None:
    review = HANDOFF / "CURRENT_REVIEW.md"
    zip_path = HANDOFF / "CURRENT_REVIEW.zip"
    temporary = HANDOFF / "CURRENT_REVIEW.zip.partial"
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        if review.exists():
            archive.write(review, "CURRENT_REVIEW.md")
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path.name != "state.json":
                archive.write(path, f"artifacts/pr_dr_live_vertical_slice/{path.name}")
    temporary.replace(zip_path)


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "prepare":
        prepare()
    elif command == "stage1":
        _execute(1)
    elif command == "stage2":
        _execute(2)
    elif command == "finalize":
        finalize()
    else:
        raise SystemExit("Use prepare, stage1, stage2, or finalize.")


if __name__ == "__main__":
    main()
