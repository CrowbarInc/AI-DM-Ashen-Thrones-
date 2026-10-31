"""ATGB-03A accounting checks. No live provider is invoked."""
import copy
import json
from pathlib import Path

import pytest

from tools.atgb.accounting import inspect_ledger, live_accounting_readiness
from tools.atgb.budget import Budget, stop_reason
from tools.atgb.chat_worker import _telemetry_from, execute_job
from tools.atgb.driver import LiveRunRefused, RunConfig, run_benchmark
from tools.atgb.isolation import UnsafeBenchmarkDataDir, prepare_isolated_store

ROOT = Path(__file__).resolve().parents[1]


def record(purpose="interpretation", rid="r1"):
    return dict(purpose=purpose, sent=True, request_id=rid, input_tokens=10,
                output_tokens=2, total_tokens=12, usage_consistent=True)


def observe(tmp_path, records):
    path = tmp_path / "usage.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    snap = dict(records=copy.deepcopy(records), requests=sum(r.get("sent") is True for r in records), stopped=False)
    return path, snap


def test_missing_host_performance_never_becomes_zero(tmp_path):
    telemetry = _telemetry_from({"metadata": {"provider_calls": {"interpretation_requests": 0}}})
    assert telemetry["provider_call_count"] == {"status": "unavailable", "value": None}
    path, snap = observe(tmp_path, [record()])
    observation = inspect_ledger(path, snap)
    assert observation["observed_sent_requests"] == 1
    assert observation["request_upper_bound"] is None
    assert telemetry["provider_call_count"]["value"] is None


@pytest.mark.parametrize("purposes", [[], ["expression"], ["interpretation", "expression", "narration"]])
def test_no_provider_expression_and_multiple_requests(tmp_path, purposes):
    path, snap = observe(tmp_path, [record(p, str(i)) for i, p in enumerate(purposes)])
    observation = inspect_ledger(path, snap)
    assert observation["status"] == "recorded"
    assert observation["observed_sent_requests"] == len(purposes)
    assert observation["request_upper_bound"] is None


def test_host_disagreement_is_not_added_or_substituted(tmp_path):
    host = _telemetry_from({"metadata": {"performance": {"provider_call_count": 1}}})
    path, snap = observe(tmp_path, [record(), record("expression", "r2")])
    assert inspect_ledger(path, snap)["observed_sent_requests"] == 2
    assert host["provider_call_count"]["value"] == 1


@pytest.mark.parametrize("damage", ["missing_file", "partial_line", "missing_sent", "missing_id", "missing_usage", "duplicate", "counter", "snapshot", "stopped"])
def test_incomplete_or_disagreeing_accounting_is_unavailable(tmp_path, damage):
    records = [record()]
    if damage == "missing_sent":
        del records[0]["sent"]
    elif damage == "missing_id":
        del records[0]["request_id"]
    elif damage == "missing_usage":
        records[0]["usage_consistent"] = False
    elif damage == "duplicate":
        records *= 2
    path, snap = observe(tmp_path, records)
    if damage == "missing_file":
        path.unlink()
    elif damage == "partial_line":
        path.write_text(path.read_text().rstrip("\n"))
    elif damage == "counter":
        snap["requests"] += 1
    elif damage == "snapshot":
        snap["records"] = []
    elif damage == "stopped":
        snap["stopped"] = True
    observation = inspect_ledger(path, snap)
    assert observation["status"] == "unavailable"
    assert observation["observed_sent_requests"] is None
    assert observation["request_upper_bound"] is None


def test_budget_and_time_exhaustion_still_stop():
    args = dict(budget=Budget(max_provider_calls=2, max_elapsed_seconds=5), mode="live_provider",
                elapsed_seconds=0, provider_calls=2, tokens=None, token_status="unavailable",
                cost=None, cost_status="unavailable")
    assert stop_reason(**args) == "provider_call_ceiling"
    args["provider_calls"] = None
    assert stop_reason(**args) == "provider_call_ceiling_not_observable"
    args["elapsed_seconds"] = 5
    assert stop_reason(**args) == "elapsed_time_ceiling"


def test_existing_request_guard_bounds_multiple_completed_attempts(monkeypatch, tmp_path):
    import game.provider_budget as owner
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "2")
    monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(tmp_path / "owner.jsonl"))
    for name, value in [("_REQUESTS", 0), ("_RECORDS", []), ("_INPUT", 0), ("_OUTPUT", 0), ("_STOPPED", False), ("_STOP_REASON", "")]:
        monkeypatch.setattr(owner, name, value)
    for i in range(2):
        assert owner.begin_request(purpose="expression", estimated_input=10, max_output=2) == ""
        owner.finish_request(record("expression", str(i)))
    assert owner.begin_request(purpose="expression", estimated_input=10, max_output=2) == "request ceiling"
    assert inspect_ledger(tmp_path / "owner.jsonl", owner.snapshot())["observed_sent_requests"] == 2


def test_completion_only_guard_cannot_bound_unfinished_dispatch(monkeypatch):
    import game.provider_budget as owner
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "1")
    monkeypatch.setattr(owner, "_REQUESTS", 0)
    monkeypatch.setattr(owner, "_STOPPED", False)
    monkeypatch.setattr(owner, "_INPUT", 0)
    monkeypatch.setattr(owner, "_OUTPUT", 0)
    # Simulate dispatch raising before finish_request. No transport is involved.
    assert owner.begin_request(purpose="semantic_plan", estimated_input=1, max_output=1) == ""
    assert owner.snapshot()["requests"] == 0
    assert owner.begin_request(purpose="semantic_plan", estimated_input=1, max_output=1) == ""


def test_readiness_identifies_unledgered_dispatch_and_exception_gaps():
    audit = live_accounting_readiness(ROOT)
    assert not audit["ok"]
    names = {g["function"] for g in audit["established_gaps"]}
    assert "_invoke_interpretation_model" in names
    assert "invoke_candidate_provider" in names
    assert audit["request_upper_bound"] is None


def test_live_runner_refuses_before_store_or_provider(monkeypatch, tmp_path):
    monkeypatch.setattr("tools.atgb.driver.prepare_isolated_store", lambda *a, **kw: pytest.fail("store created"))
    with pytest.raises(LiveRunRefused, match="provider_call_ceiling_not_observable"):
        run_benchmark(RunConfig(mode="live_provider", confirm_live_provider=True, output_dir=tmp_path,
                               budget=Budget(max_provider_calls=68, max_elapsed_seconds=300)))
    assert (tmp_path / "accounting_readiness.json").is_file()


def test_direct_worker_refuses_even_on_resume_before_game_import_or_reset(tmp_path):
    result = execute_job(dict(mode="live_provider", confirm_live_provider=True, repo_root=str(ROOT),
                              data_dir=str(tmp_path / "old_store"), turns=[{"turn_id": "S04.3"}]))
    assert result["turns"] == [] and result["reset_invoked"] is False
    assert result["stop_reason"] == "provider_call_ceiling_not_observable"
    assert not (tmp_path / "old_store").exists()


def test_interrupted_scenario_store_cannot_be_reused(tmp_path):
    store = prepare_isolated_store(tmp_path / "store", scenario_id="S04", repo=ROOT)
    marker = (store / ".atgb-isolated").read_bytes()
    with pytest.raises(UnsafeBenchmarkDataDir):
        prepare_isolated_store(store, scenario_id="S04", repo=ROOT)
    assert (store / ".atgb-isolated").read_bytes() == marker
