"""Run ATGB scenarios without adding a second chat path or a scorer."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from tools.atgb import (
    BENCHMARK_VERSION,
    EVIDENCE_INFRASTRUCTURE,
    PARTITION_REVISION,
    RUBRIC_VERSION,
    SCENARIO_VERSION,
    UNAVAILABLE,
    UNCONTROLLED,
)
from tools.atgb.budget import Budget, estimated_cost, stop_reason
from tools.atgb.baseline import provenance
from tools.atgb.fixtures import authoritative_context, load_corpus
from tools.atgb.isolation import (
    player_campaign_dir_from_env,
    prepare_isolated_store,
    repo_root,
)
from tools.atgb.results import (
    blank_judgment,
    evidence_distinction,
    gameplay_performance_claim,
    result_document,
    unavailable_telemetry,
    write_json,
)
from tools.atgb.worksheet import build_worksheet, context_for_turn, render_worksheet

SIMULATED_RESPONSE = (
    "[ATGB SIMULATED TEST DOUBLE] This is not an AI-DM response. Infrastructure validation only."
)
SIMULATED_ORIGIN = "simulated_test_double"
HOST_ORIGIN = "host_provider_disabled"
LIVE_ORIGIN = "live_provider"

MODES = ("provider_disabled_simulated", "provider_disabled_host", "live_provider")


class LiveRunRefused(RuntimeError):
    """Live provider execution was requested without the explicit confirmation gate."""


@dataclass
class RunConfig:
    mode: str = "provider_disabled_simulated"
    output_dir: Path | None = None
    partitions: tuple[str, ...] | None = None
    scenario_ids: tuple[str, ...] | None = None
    trial_number: int = 1
    confirm_live_provider: bool = False
    keep_stores: bool = False
    budget: Budget = field(default_factory=Budget)
    scores: dict[str, Any] | None = None
    worker_timeout_seconds: float = 180.0
    preflight_only: bool = False


def build_chat_request(player_input: str) -> dict[str, str]:
    """The same player-facing body the chat route already accepts."""

    return {"text": player_input, "ui_mode": "player"}


def repository_revision(root: Path | None = None) -> dict[str, Any]:
    repo = root or repo_root()
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return {"revision": UNAVAILABLE, "worktree_dirty": UNAVAILABLE}
    if revision.returncode != 0:
        return {"revision": UNAVAILABLE, "worktree_dirty": UNAVAILABLE}
    dirty = bool(status.stdout.strip()) if status.returncode == 0 else UNAVAILABLE
    return {
        "revision": revision.stdout.strip(),
        "worktree_dirty": dirty,
        "note": "HEAD identifies the commit. A dirty worktree means the running files can differ from that commit.",
    }


def _origin(mode: str) -> str:
    if mode == "provider_disabled_simulated":
        return SIMULATED_ORIGIN
    if mode == "provider_disabled_host":
        return HOST_ORIGIN
    return LIVE_ORIGIN


def _sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in ("api_key", "secret", "password", "authorization", "credential"))


def scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items() if not _sensitive_key(str(key))}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def run_benchmark(config: RunConfig, *, root: Path | None = None) -> dict[str, Any]:
    if config.mode not in MODES:
        raise ValueError(f"Unknown execution mode {config.mode!r}.")
    if config.preflight_only and config.mode != "provider_disabled_host":
        raise ValueError("Preflight-only execution requires provider_disabled_host.")
    if config.mode == "live_provider" and not config.confirm_live_provider:
        raise LiveRunRefused(
            "Live-provider execution is refused without --confirm-live-provider. "
            "This implementation pass does not run it."
        )
    config.budget.validate(mode=config.mode)
    repo = root or repo_root()
    if config.mode == "live_provider":
        from tools.atgb.accounting import live_accounting_readiness

        readiness = live_accounting_readiness(repo)
        if not readiness["ok"]:
            if config.output_dir is not None:
                config.output_dir.mkdir(parents=True, exist_ok=True)
                write_json(config.output_dir / "accounting_readiness.json", readiness)
            raise LiveRunRefused(
                "provider_call_ceiling_not_observable: existing ledger coverage cannot "
                "establish a request upper bound; see ATGB-03A accounting readiness."
            )
    player_campaign = player_campaign_dir_from_env(repo)
    loaded = load_corpus(repo, partitions=config.partitions)
    scenarios = loaded["scenarios"]
    if config.scenario_ids:
        wanted = set(config.scenario_ids)
        scenarios = [item for item in scenarios if item["scenario_id"] in wanted]
        missing = wanted.difference(item["scenario_id"] for item in scenarios)
        if missing:
            raise ValueError(f"Unknown scenario id(s): {', '.join(sorted(missing))}.")
    started = time.monotonic()
    provider_calls = 0
    provider_calls_known = True
    tokens = 0
    token_status = "recorded"
    cost_total = 0.0
    cost_status = "recorded"
    stop = stop_reason(
        budget=config.budget,
        mode=config.mode,
        elapsed_seconds=0.0,
        provider_calls=0,
        tokens=0,
        token_status="recorded",
        cost=0.0,
        cost_status="recorded",
    )
    turns: list[dict[str, Any]] = []
    conversations: list[dict[str, Any]] = []
    scenario_records: list[dict[str, Any]] = []
    for scenario in scenarios:
        if stop:
            break
        record, scenario_turns, stop = _run_scenario(
            scenario,
            manifest=loaded["manifest"],
            config=config,
            repo=repo,
            player_campaign=player_campaign,
            started=started,
            provider_calls=provider_calls,
            provider_calls_known=provider_calls_known,
            tokens=tokens,
            token_status=token_status,
            cost_total=cost_total,
            cost_status=cost_status,
        )
        scenario_records.append(record)
        conversations.append(
            {
                "scenario_id": scenario["scenario_id"],
                "partition": scenario["partition"],
                "evidence_status": scenario["evidence_status"],
                "turn_ids": [turn["turn_id"] for turn in scenario_turns],
                "qualitative_observations": [],
                "qualitative_notes": "",
                "qualitative_is_a_score": False,
            }
        )
        for turn in scenario_turns:
            turns.append(turn)
            call_field = turn["telemetry"]["provider_call_count"]
            if call_field["status"] == "recorded" and isinstance(call_field["value"], int):
                provider_calls += int(call_field["value"])
            elif config.mode == "live_provider":
                provider_calls_known = False
            token_field_in = turn["telemetry"]["input_tokens"]
            token_field_out = turn["telemetry"]["output_tokens"]
            if token_field_in["status"] == "recorded" and token_field_out["status"] == "recorded":
                tokens += int(token_field_in["value"]) + int(token_field_out["value"])
            elif config.mode == "live_provider" and call_field.get("status") == "recorded" and call_field.get("value"):
                token_status = UNAVAILABLE
            cost_field = turn["telemetry"]["estimated_cost"]
            if cost_field["status"] == "recorded" and isinstance(cost_field["value"], (int, float)):
                cost_total += float(cost_field["value"])
            elif config.mode == "live_provider" and config.budget.max_estimated_cost is not None and call_field.get("value"):
                cost_status = UNAVAILABLE
        if not stop:
            stop = stop_reason(
                budget=config.budget,
                mode=config.mode,
                elapsed_seconds=time.monotonic() - started,
                provider_calls=provider_calls if provider_calls_known else None,
                tokens=tokens if token_status == "recorded" else None,
                token_status=token_status,
                cost=cost_total if cost_status == "recorded" else None,
                cost_status=cost_status,
            )
    revision = repository_revision(repo)
    document = result_document(
        benchmark_version=BENCHMARK_VERSION,
        scenario_version=SCENARIO_VERSION,
        rubric_version=RUBRIC_VERSION,
        partition_revision=PARTITION_REVISION,
        repository_revision=revision.get("revision"),
        worktree_dirty=revision.get("worktree_dirty"),
        revision_note=revision.get("note"),
        execution_mode=config.mode,
        baseline=provenance(),
        preflight_only=config.preflight_only,
        evidence_distinction=evidence_distinction(mode=config.mode, human_review_complete=False),
        gameplay_performance_claim=False,
        human_review_complete=False,
        trial_number=config.trial_number,
        trial_count=1,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        run_id=uuid.uuid4().hex,
        model_configuration=_model_configuration(config.mode, scenario_records),
        execution_environment={
            "python": platform.python_version(),
            "platform": platform.platform(),
            "sampling": UNCONTROLLED,
        },
        budget=config.budget.as_dict(),
        stop_reason=stop,
        scenario_ids=[item["scenario_id"] for item in scenario_records],
        scenario_records=scenario_records,
        conversations=conversations,
        turns=turns,
        limitations=_limitations(config.mode),
    )
    document["gameplay_performance_claim"] = gameplay_performance_claim(document["evidence_distinction"])
    if config.scores:
        from tools.atgb.results import apply_scores

        document = apply_scores(document, config.scores)
    if config.output_dir is not None:
        _write_package(config.output_dir, document, loaded["manifest"])
    return document


def _model_configuration(mode: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    observed = next((record.get("model_configuration") for record in records if record.get("model_configuration")), None)
    configuration = dict(observed or {})
    configuration.setdefault("sampling", UNCONTROLLED)
    configuration["api_key_recorded"] = False
    configuration["provider_calls"] = "disabled" if mode != "live_provider" else "enabled"
    configuration["live_interpretation"] = "disabled" if mode != "live_provider" else "enabled_unless_the_process_already_disabled_it"
    if "default_model_name" not in configuration:
        configuration["default_model_name"] = UNAVAILABLE
    return configuration


def _limitations(mode: str) -> list[str]:
    common = [
        "Frontier Gate is the initial environment. The runner does not hard-code that location; each fixture names its own environment.",
        "No additional environments are implemented in this pass.",
        "Held-out scenarios were visible in the ATGB-01 review. Their partition is held-out. Their evidence status is previously exposed.",
        "evaluate_playability is not called and is not the ATGB verdict.",
        "Historical builds are not executed and no compatibility adapter is installed.",
        "Token totals that the host reports as null stay null. Cost is not invented.",
    ]
    if mode == "provider_disabled_simulated":
        common.append(
            "Simulated responses are a test double for infrastructure validation. They are not AI-DM responses and are not a gameplay result."
        )
        common.append(
            "Simulated mode does not import the game and does not call the campaign reset. It does create and then discard an isolated store."
        )
    elif mode == "provider_disabled_host":
        common.append(
            "Host responses with providers disabled show host behavior. They are not natural conversational competence and are not a gameplay benchmark result."
        )
        common.append(
            "The host performance counter can include a provider-disabled narration fallback. "
            "That count is preserved. It is not treated as a sent provider request when the reply is stamped provider-disabled and no token usage was recorded."
        )
    else:
        common.append("A live transcript is a gameplay benchmark result only after human review of the three judgments.")
    return common


def _run_scenario(
    scenario: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    config: RunConfig,
    repo: Path,
    player_campaign: Path,
    started: float,
    provider_calls: int,
    provider_calls_known: bool,
    tokens: int,
    token_status: str,
    cost_total: float,
    cost_status: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], str | None]:
    store_parent = Path(config.output_dir) / "stores" if config.keep_stores and config.output_dir else None
    if store_parent is not None:
        store_parent.mkdir(parents=True, exist_ok=True)
        store = store_parent / f"{scenario['scenario_id']}-{uuid.uuid4().hex}"
    else:
        from tempfile import mkdtemp

        temporary_root = repo / "development" / "tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        store = Path(mkdtemp(prefix=f"atgb-{scenario['scenario_id']}-", dir=temporary_root))
    prepared = prepare_isolated_store(
        store,
        scenario_id=scenario["scenario_id"],
        repo=repo,
        player_campaign_dir=player_campaign,
    )
    try:
        location_id = _location_id(scenario, manifest)
        if config.mode == "provider_disabled_simulated":
            captured, stop = _simulate_scenario(
                scenario,
                config=config,
                started=started,
                provider_calls=provider_calls,
                provider_calls_known=provider_calls_known,
                tokens=tokens,
                token_status=token_status,
                cost_total=cost_total,
                cost_status=cost_status,
            )
            model_configuration = None
        else:
            captured, stop, model_configuration = _host_scenario(
                scenario,
                prepared=prepared,
                config=config,
                repo=repo,
                player_campaign=player_campaign,
                started=started,
                expected_location_id=location_id,
            )
        captured_turns = list(captured.get("turns") or [])
        expected_ids = [turn["turn_id"] for turn in scenario["turns"]]
        actual_ids = [turn.get("turn_id") for turn in captured_turns]
        if actual_ids != expected_ids[: len(actual_ids)]:
            raise RuntimeError(
                f"{scenario['scenario_id']} returned turns out of catalog order: {actual_ids}."
            )
        turns = [
            _assemble_turn(scenario, turn, captured_turn, manifest, index)
            for index, (turn, captured_turn) in enumerate(zip(scenario["turns"], captured_turns))
        ]
        for turn in turns:
            turn["telemetry"]["estimated_cost"] = estimated_cost(turn["telemetry"], config.budget)
        record = {
            "scenario_id": scenario["scenario_id"],
            "title": scenario["title"],
            "partition": scenario["partition"],
            "evidence_status": scenario["evidence_status"],
            "environment_id": scenario["environment_id"],
            "expected_location_id": _location_id(scenario, manifest),
            "isolation": {
                "accepted": True,
                "reset_invoked": bool(captured.get("reset_invoked")),
                "canonical_data_used_as_store": False,
            },
            "context_establishment": captured.get("context_establishment"),
            "context_limitation": captured.get("context_limitation"),
            "preflight": captured.get("preflight"),
            "model_configuration": model_configuration,
            "authoritative_context": authoritative_context(scenario, manifest),
        }
        return record, turns, stop
    finally:
        if not config.keep_stores:
            shutil.rmtree(prepared, ignore_errors=True)


def _location_id(scenario: Mapping[str, Any], manifest: Mapping[str, Any]) -> Any:
    environments = manifest.get("environments") if isinstance(manifest.get("environments"), dict) else {}
    environment = environments.get(scenario["environment_id"]) if isinstance(environments, dict) else None
    if isinstance(environment, dict):
        return environment.get("location_id")
    return None


def _simulate_scenario(
    scenario: Mapping[str, Any],
    *,
    config: RunConfig,
    started: float,
    provider_calls: int,
    provider_calls_known: bool,
    tokens: int,
    token_status: str,
    cost_total: float,
    cost_status: str,
) -> tuple[dict[str, Any], str | None]:
    captured_turns = []
    stop = None
    calls = provider_calls
    known = provider_calls_known
    token_sum = tokens
    tokens_state = token_status
    cost_sum = cost_total
    cost_state = cost_status
    for turn in scenario["turns"]:
        stop = stop_reason(
            budget=config.budget,
            mode=config.mode,
            elapsed_seconds=time.monotonic() - started,
            provider_calls=calls if known else None,
            tokens=token_sum if tokens_state == "recorded" else None,
            token_status=tokens_state,
            cost=cost_sum if cost_state == "recorded" else None,
            cost_status=cost_state,
        )
        if stop:
            break
        telemetry = unavailable_telemetry()
        telemetry["estimated_cost"] = estimated_cost(telemetry, config.budget)
        captured_turns.append(
            {
                "turn_id": turn["turn_id"],
                "request": build_chat_request(turn["player_input"]),
                "response_text": SIMULATED_RESPONSE,
                "response_origin": SIMULATED_ORIGIN,
                "simulated": True,
                "telemetry": telemetry,
                "state_evidence": {
                    "status": UNAVAILABLE,
                    "reason": "simulated_mode_does_not_execute_the_game",
                },
                "resolution_kind": UNAVAILABLE,
                "communication_mode": UNAVAILABLE,
                "conversational_decision": UNAVAILABLE,
                "addressee": UNAVAILABLE,
                "authoritative_mutation": UNAVAILABLE,
                "capture_status": "captured",
                "error": None,
            }
        )
    return (
        {
            "reset_invoked": False,
            "context_establishment": "not_executed_in_simulated_mode",
            "context_limitation": (
                "Simulated mode validates request construction and isolation. "
                "It does not establish campaign context and it does not call POST /api/chat."
            ),
            "turns": captured_turns,
        },
        stop,
    )


def _host_scenario(
    scenario: Mapping[str, Any],
    *,
    prepared: Path,
    config: RunConfig,
    repo: Path,
    player_campaign: Path,
    started: float,
    expected_location_id: Any,
) -> tuple[dict[str, Any], str | None, dict[str, Any] | None]:
    job = {
        "mode": config.mode,
        "preflight_only": config.preflight_only,
        "data_dir": str(prepared),
        "player_campaign_dir": str(player_campaign),
        "repo_root": str(repo),
        "expected_location_id": expected_location_id,
        "scenario_id": scenario["scenario_id"],
        "turns": [
            {"turn_id": turn["turn_id"], "player_input": turn["player_input"]}
            for turn in scenario["turns"]
        ],
        "deadline_epoch": None
        if config.budget.max_elapsed_seconds is None
        else time.time() + max(0.0, config.budget.max_elapsed_seconds - (time.monotonic() - started)),
        "max_provider_calls": config.budget.max_provider_calls,
        "max_tokens": config.budget.max_tokens,
        "max_estimated_cost": config.budget.max_estimated_cost,
        "price_per_million_input_tokens": config.budget.price_per_million_input_tokens,
        "price_per_million_output_tokens": config.budget.price_per_million_output_tokens,
        "confirm_live_provider": config.confirm_live_provider,
    }
    process_env = os.environ.copy()
    for name in list(process_env):
        if _sensitive_key(name) and config.mode != "live_provider":
            process_env.pop(name, None)
    process_env["ASHEN_DATA_DIR"] = str(prepared)
    process_env["PYTHONPATH"] = str(repo) + os.pathsep + process_env.get("PYTHONPATH", "")
    process_env["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    if config.mode == "provider_disabled_host":
        process_env["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
        process_env["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
        process_env["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
        process_env["ASHEN_PROVIDER_REQUEST_LIMIT"] = "0"
    job_path = prepared / "atgb-job.json"
    output_path = prepared / "atgb-worker.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "tools.atgb.chat_worker", "--job", str(job_path), "--output", str(output_path)],
            cwd=repo,
            env=process_env,
            check=False,
            capture_output=True,
            text=True,
            timeout=config.worker_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return (
            {
                "reset_invoked": False,
                "context_establishment": "worker_timeout",
                "context_limitation": "The chat worker exceeded the harness timeout. No gameplay result is claimed.",
                "turns": [],
            },
            "worker_timeout",
            None,
        )
    if not output_path.is_file():
        return (
            {
                "reset_invoked": False,
                "context_establishment": "worker_failed",
                "context_limitation": _worker_failure_text(completed),
                "turns": [],
            },
            "worker_failed",
            None,
        )
    payload = scrub(json.loads(output_path.read_text(encoding="utf-8")))
    if not isinstance(payload, dict):
        raise RuntimeError("ATGB worker returned a non-object result.")
    return payload, payload.get("stop_reason"), payload.get("model_configuration")


def _worker_failure_text(completed: subprocess.CompletedProcess[str]) -> str:
    text = (completed.stderr or completed.stdout or "").strip()
    lowered = text.lower()
    if "api_key" in lowered or "sk-" in lowered:
        return "The chat worker failed. The failure text was withheld because it may contain a credential."
    return text[-2000:] or f"The chat worker exited {completed.returncode} without a result."


def _assemble_turn(
    scenario: Mapping[str, Any],
    turn: Mapping[str, Any],
    captured: Mapping[str, Any],
    manifest: Mapping[str, Any],
    index: int,
) -> dict[str, Any]:
    return {
        "turn_id": turn["turn_id"],
        "scenario_id": scenario["scenario_id"],
        "order": index,
        "partition": scenario["partition"],
        "evidence_status": scenario["evidence_status"],
        "primary_capability": turn["primary_capability"],
        "player_input": turn["player_input"],
        "request": captured.get("request"),
        "response_text": captured.get("response_text"),
        "response_origin": captured.get("response_origin"),
        "simulated": bool(captured.get("simulated")),
        "telemetry": captured.get("telemetry") or unavailable_telemetry(),
        "state_evidence": captured.get("state_evidence"),
        "resolution_kind": captured.get("resolution_kind", UNAVAILABLE),
        "communication_mode": captured.get("communication_mode", UNAVAILABLE),
        "conversational_decision": captured.get("conversational_decision", UNAVAILABLE),
        "addressee": captured.get("addressee", UNAVAILABLE),
        "authoritative_mutation": captured.get("authoritative_mutation", UNAVAILABLE),
        "provider_calls_disabled": captured.get("provider_calls_disabled"),
        "provider_request_sent": captured.get("provider_request_sent"),
        "capture_status": captured.get("capture_status"),
        "error": captured.get("error"),
        "turn_context": context_for_turn(scenario, turn, manifest),
        "clarification_expected": turn["clarification_expected"],
        "continuity_expected": turn["continuity_expected"],
        "judgment": blank_judgment(),
        "prior_turn_id": None if index == 0 else scenario["turns"][index - 1]["turn_id"],
        "evidence_references": [
            f"scenario:{scenario['scenario_id']}",
            f"turn:{turn['turn_id']}",
            f"catalog:{turn['catalog_heading']}",
        ],
    }


def _write_package(output_dir: Path, document: dict[str, Any], manifest: Mapping[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "result.json", document)
    (output_dir / "report.md").write_text(document["report"], encoding="utf-8")
    worksheet = build_worksheet(document, manifest)
    write_json(output_dir / "worksheet.json", worksheet)
    (output_dir / "worksheet.md").write_text(render_worksheet(worksheet), encoding="utf-8")


def project_for_comparison(result: Mapping[str, Any]) -> dict[str, Any]:
    """Drop fields that change between identical infrastructure runs."""

    return {
        "benchmark_version": result.get("benchmark_version"),
        "scenario_version": result.get("scenario_version"),
        "rubric_version": result.get("rubric_version"),
        "partition_revision": result.get("partition_revision"),
        "execution_mode": result.get("execution_mode"),
        "evidence_distinction": result.get("evidence_distinction"),
        "gameplay_performance_claim": result.get("gameplay_performance_claim"),
        "scenario_ids": result.get("scenario_ids"),
        "turns": [
            {
                "turn_id": turn["turn_id"],
                "order": turn["order"],
                "player_input": turn["player_input"],
                "request": turn["request"],
                "response_text": turn["response_text"],
                "response_origin": turn["response_origin"],
                "simulated": turn["simulated"],
                "telemetry": turn["telemetry"],
                "judgment": turn["judgment"],
            }
            for turn in result.get("turns") or []
        ],
    }
