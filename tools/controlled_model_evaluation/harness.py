"""Evaluation driver. Validation never attaches a live provider transport."""
from __future__ import annotations

from decimal import Decimal
import json
import os
from pathlib import Path
import time

from controlled_model_evaluation.authorization import (
    AuthorizationRefused,
    LiveRequest,
    ProviderIdentity,
    authorize,
)
from controlled_model_evaluation.budget import BudgetGuard, BudgetRefused
from controlled_model_evaluation.cases import CASES, case_by_id
from controlled_model_evaluation.fixtures import validation_traces
from controlled_model_evaluation.pricing import (
    MAX_INPUT_TOKENS_PER_CALL,
    MAX_OUTPUT_TOKENS_PER_CALL,
    MAX_TOTAL_PROVIDER_CALLS,
    MAX_WALL_CLOCK_SECONDS,
    MODEL,
    PER_CALL_TIMEOUT_SECONDS,
    PROVIDER,
    approved_cost_ceiling,
)
from controlled_model_evaluation.redaction import assert_redacted, redact
from controlled_model_evaluation.scoring import score_trace

REPEAT_POLICY = (
    "Pass 2 does not start when pass 1 finishes. A repeat is allowed only for "
    "PROVIDER_TRANSPORT or PROVIDER_TIMEOUT, restarts the affected sequence from "
    "its initial snapshot, and is refused when another call would exceed the "
    "40-request, token, cost, or wall-clock ceiling. At most two attempts per case. "
    "Host narration retries and SDK retries are disabled for the authorized run, "
    "so they cannot create uncounted requests."
)


def discover_identity() -> ProviderIdentity:
    """Read configured model names. The key value is never returned."""
    from game.config import (
        DEFAULT_MODEL_NAME,
        ENABLE_MODEL_ROUTING,
        HIGH_PRECISION_MODEL_NAME,
        RETRY_ESCALATION_MODEL_NAME,
    )

    from experiments.pr_dp import CONFIGURED_MODEL

    return ProviderIdentity(
        provider=PROVIDER,
        model=DEFAULT_MODEL_NAME,
        high_precision_model=HIGH_PRECISION_MODEL_NAME,
        retry_model=RETRY_ESCALATION_MODEL_NAME,
        routing_enabled=bool(ENABLE_MODEL_ROUTING),
        key_present=bool(os.getenv("OPENAI_API_KEY")),
        interpretation_model=str(CONFIGURED_MODEL),
    )


def live_request(data_dir: Path, production_data_dir: Path, **overrides) -> LiveRequest:
    payload = dict(
        granted=False,
        provider=PROVIDER,
        model=MODEL,
        pricing_verified=True,
        max_calls=MAX_TOTAL_PROVIDER_CALLS,
        max_input_tokens_per_call=MAX_INPUT_TOKENS_PER_CALL,
        max_output_tokens_per_call=MAX_OUTPUT_TOKENS_PER_CALL,
        max_wall_seconds=MAX_WALL_CLOCK_SECONDS,
        per_call_timeout_seconds=PER_CALL_TIMEOUT_SECONDS,
        ceiling_usd=approved_cost_ceiling(),
        data_dir=data_dir,
        production_data_dir=production_data_dir,
        snapshot_available=True,
        redaction_ok=True,
        preparation_phase=True,
    )
    payload.update(overrides)
    return LiveRequest(**payload)


def execute_live(request: LiveRequest, identity: ProviderIdentity, transport, estimated_input: int, max_output: int) -> dict:
    """Dispatch only after the gate. Validation does not call this."""
    authorize(request, identity)
    if transport is None:
        raise AuthorizationRefused("live transport is not attached")
    guard = BudgetGuard(
        pricing_verified=request.pricing_verified,
        ceiling_usd=request.ceiling_usd,
        max_calls=request.max_calls,
        max_input_per_call=request.max_input_tokens_per_call,
        max_output_per_call=request.max_output_tokens_per_call,
    )
    guard.preflight(estimated_input, max_output)
    started = time.perf_counter()
    try:
        response = transport()
    except Exception as exc:
        guard.commit(input_tokens=None, output_tokens=None, failed=True)
        raise AuthorizationRefused("provider transport failed: " + type(exc).__name__) from exc
    usage = response.get("usage") if isinstance(response, dict) else None
    incoming = usage.get("input_tokens") if isinstance(usage, dict) else None
    outgoing = usage.get("output_tokens") if isinstance(usage, dict) else None
    account = guard.commit(input_tokens=incoming, output_tokens=outgoing, failed=False)
    return {
        "elapsed_seconds": time.perf_counter() - started,
        "response": response,
        "account": account,
    }


def write_text(path: Path, text: str) -> None:
    cleaned = redact(text)
    assert_redacted(cleaned)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cleaned, encoding="utf-8")


def review_row(case, trace: dict, scored: dict) -> dict:
    return {
        "case_id": case.case_id,
        "player_request": case.utterance,
        "relevant_prior_context": case.prior_context,
        "authoritative_state_before": case.initial_state,
        "model_output": trace.get("narration"),
        "interpreted_intent": trace.get("interpreted_intent"),
        "reference_binding": trace.get("reference_ids"),
        "admission_decision": trace.get("admission"),
        "state_after": {
            "scene": trace.get("scene_after"),
            "turn_delta": trace.get("turn_delta"),
            "inventory_changed": trace.get("inventory_changed"),
            "stance_changed": trace.get("stance_changed"),
        },
        "turn_advancement": trace.get("turn_delta"),
        "published_narration": trace.get("narration"),
        "automated_score": scored["scores"],
        "reviewer_score": None,
        "failure_attribution": scored["attribution"],
        "notes": case.scoring_focus,
    }


def score_fixtures() -> list[dict]:
    traces = validation_traces()
    results = []
    for name, row in traces.items():
        case = case_by_id(row["case_id"])
        scored = score_trace(case, row)
        scored["fixture"] = name
        scored["review"] = review_row(case, row, scored)
        results.append(scored)
    return results


def negative_safety_checks(root: Path, identity: ProviderIdentity) -> list[dict]:
    production = root / "production_data"
    isolated = root / "evaluation_session"
    production.mkdir(parents=True, exist_ok=True)
    isolated.mkdir(parents=True, exist_ok=True)
    checks = []

    def expect(name: str, request: LiveRequest, ident: ProviderIdentity = identity):
        try:
            authorize(request, ident)
            checks.append({"name": name, "refused": False, "reason": ""})
        except AuthorizationRefused as exc:
            checks.append({"name": name, "refused": True, "reason": exc.reason})

    expect("no_authorization", live_request(isolated, production))
    expect("pricing_unverified", live_request(isolated, production, granted=True, preparation_phase=False, pricing_verified=False))
    expect("model_unknown", live_request(isolated, production, granted=True, preparation_phase=False, model=""))
    expect(
        "provider_ambiguous",
        live_request(isolated, production, granted=True, preparation_phase=False),
        ProviderIdentity("openai", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-mini", True, False),
    )
    expect("token_limits_missing", live_request(isolated, production, granted=True, preparation_phase=False, max_input_tokens_per_call=0))
    expect("cost_ceiling_missing", live_request(isolated, production, granted=True, preparation_phase=False, ceiling_usd=Decimal("0")))
    expect("call_ceiling_missing", live_request(isolated, production, granted=True, preparation_phase=False, max_calls=0))
    expect("production_campaign", live_request(production, production, granted=True, preparation_phase=False))
    expect(
        "provider_changed",
        live_request(isolated, production, granted=True, preparation_phase=False),
        ProviderIdentity("other", MODEL, MODEL, MODEL, True, False),
    )
    expect("snapshot_missing", live_request(isolated, production, granted=True, preparation_phase=False, snapshot_available=False))
    expect("redaction_failed", live_request(isolated, production, granted=True, preparation_phase=False, redaction_ok=False))

    guard = BudgetGuard(max_calls=1, max_input_total=100, max_output_total=100, ceiling_usd=Decimal("1"))
    budget_reasons = []
    guard.preflight(10, 10)
    guard.commit(input_tokens=10, output_tokens=10)
    for label, kwargs in (
        ("budget_exceeded", dict(estimated_input=10, max_output=10)),
        ("retry_exceeds_calls", dict(estimated_input=10, max_output=10, retry=True)),
    ):
        try:
            guard.preflight(**kwargs)
            budget_reasons.append({"name": label, "refused": False, "reason": ""})
        except BudgetRefused as exc:
            budget_reasons.append({"name": label, "refused": True, "reason": exc.reason})
    token_guard = BudgetGuard()
    try:
        token_guard.preflight(MAX_INPUT_TOKENS_PER_CALL + 1, 10)
        budget_reasons.append({"name": "input_token_limit", "refused": False, "reason": ""})
    except BudgetRefused as exc:
        budget_reasons.append({"name": "input_token_limit", "refused": True, "reason": exc.reason})
    try:
        BudgetGuard(pricing_verified=False).preflight(10, 10)
        budget_reasons.append({"name": "unpriced_budget", "refused": False, "reason": ""})
    except BudgetRefused as exc:
        budget_reasons.append({"name": "unpriced_budget", "refused": True, "reason": exc.reason})
    checks.extend(budget_reasons)
    return checks


def run_isolation_check(root: Path) -> dict:
    """Two temporary sessions, providers disabled, no external socket."""
    import sys

    network: list[str] = []

    def guard(event, args):
        if event in ("socket.connect", "socket.getaddrinfo"):
            dest = args[1] if event == "socket.connect" else args[0]
            host = dest[0] if isinstance(dest, tuple) else dest
            if host not in ("127.0.0.1", "::1", "localhost"):
                network.append(str(host))
                raise RuntimeError("external networking forbidden")

    sys.addaudithook(guard)
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
    os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
    os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    os.environ.pop("OPENAI_API_KEY", None)
    from pytest import MonkeyPatch
    from fastapi.testclient import TestClient

    from game.api import app
    from game.provider_budget import snapshot
    from tests.pr_play_79df3_harness import seed_gate

    constructed = {"count": 0}

    class OpenAI:
        def __init__(self, *args, **kwargs):
            constructed["count"] += 1
            raise AssertionError("provider client constructed")

    import openai

    turns = {}
    with MonkeyPatch.context() as mp:
        mp.setattr(openai, "OpenAI", OpenAI)
        for label, text in (("left", "I read the warning the watch posted beside the gate."), ("right", "I keep my argument to myself.")):
            data = root / label
            seed_gate(data, mp)
            from game.integrated_play import _LANES
            from game import storage
            _LANES.clear()
            before = snapshot()["records"]
            with TestClient(app) as client:
                response = client.post("/api/chat?ui_mode=player", json={"text": text, "client_request_id": "iso-" + label})
            session = storage.load_session()
            turns[label] = {
                "status": response.status_code,
                "turn": session.get("turn_counter"),
                "scene": session.get("active_scene_id"),
                "provider_records": len(snapshot()["records"]) - len(before),
                "data_dir": str(data),
            }
    return {
        "turns": turns,
        "openai_constructed": constructed["count"],
        "external_hosts": network,
        "isolated": turns["left"]["data_dir"] != turns["right"]["data_dir"],
    }


def validate(output_dir: Path, *, include_isolation: bool = False) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    timing = {}
    mark = time.perf_counter()
    identity = discover_identity()
    timing["initialization_seconds"] = round(time.perf_counter() - mark, 6)
    mark = time.perf_counter()
    loaded = [case.case_id for case in CASES]
    timing["fixture_loading_seconds"] = round(time.perf_counter() - mark, 6)
    mark = time.perf_counter()
    scored = score_fixtures()
    timing["scoring_seconds"] = round(time.perf_counter() - mark, 6)
    mark = time.perf_counter()
    negatives = negative_safety_checks(output_dir / "negative", identity)
    guard = BudgetGuard()
    timing["budget_guard_seconds"] = round(time.perf_counter() - mark, 6)
    mark = time.perf_counter()
    secret = "fixture sk-testsecretvalue123 narration"
    write_text(output_dir / "redaction_sample.txt", secret)
    sample = (output_dir / "redaction_sample.txt").read_text(encoding="utf-8")
    assert_redacted(sample)
    reviews = [row["review"] for row in scored]
    write_text(output_dir / "fixture_reviews.json", json.dumps(reviews, indent=2))
    timing["artifact_generation_seconds"] = round(time.perf_counter() - mark, 6)
    isolation = None
    if include_isolation:
        mark = time.perf_counter()
        isolation = run_isolation_check(output_dir / "sessions")
        timing["isolation_seconds"] = round(time.perf_counter() - mark, 6)
    report = {
        "cases": len(loaded),
        "case_ids": loaded,
        "fixture_results": [{key: value for key, value in row.items() if key != "review"} for row in scored],
        "negative_checks": negatives,
        "negative_failures": [row["name"] for row in negatives if not row["refused"]],
        "redaction_sample_clean": "sk-" not in sample,
        "identity": {
            "provider": identity.provider,
            "model": identity.model,
            "high_precision_model": identity.high_precision_model,
            "retry_model": identity.retry_model,
            "routing_enabled": identity.routing_enabled,
            "key_present": identity.key_present,
            "interpretation_model": identity.interpretation_model,
            "unambiguous": identity.unambiguous,
        },
        "ceiling_usd": format(approved_cost_ceiling(), "f"),
        "budget_snapshot": guard.snapshot(),
        "provider_calls_during_validation": 0,
        "isolation": isolation,
        "timing": timing,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "repeat_policy": REPEAT_POLICY,
    }
    write_text(output_dir / "validation_report.json", json.dumps(report, indent=2))
    return report
