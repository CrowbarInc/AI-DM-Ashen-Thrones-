"""ATGB-03B deterministic provider lifecycle and dispatch-owner checks."""
import ast
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import threading
from types import SimpleNamespace as NS

import pytest

from game import provider_budget as budget
from game.expressive_dialogue import request_expression as production_request_expression
from game.semantic_interpreter import _invoke_interpretation_model as production_contract_request
from tools.atgb.accounting import inspect_ledger, live_accounting_readiness

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ledger(monkeypatch, tmp_path):
    for name, value in {"_REQUESTS": 0, "_RECORDS": [], "_EVENTS": [], "_ATTEMPTS": {},
                        "_INPUT": 0, "_OUTPUT": 0, "_RESERVED_INPUT": 0, "_RESERVED_OUTPUT": 0,
                        "_USAGE_KNOWN": True, "_STOPPED": False, "_STOP_REASON": "",
                        "_INITIALIZED": False, "_LEDGER_PATH": None}.items():
        monkeypatch.setattr(budget, name, value)
    path = tmp_path / "requests.jsonl"
    monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(path))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "20")
    for key in ("INPUT", "OUTPUT", "TOTAL"):
        monkeypatch.setenv(f"ASHEN_PROVIDER_{key}_TOKEN_LIMIT", "1000000")
    monkeypatch.delenv("ASHEN_DISABLE_PROVIDER_CALLS", raising=False)
    return path


def response(usage=True):
    return NS(id="provider-id", model="gpt-4.1-mini-stub", output_text="{}",
              usage=NS(input_tokens=10, output_tokens=2, total_tokens=12) if usage else None)


def attempt(**overrides):
    return budget.admit_request(**{**dict(purpose="interpretation", owner="test.dispatch",
                                         model="gpt-4.1-mini", estimated_input=10, max_output=2), **overrides})


def test_success_has_durable_admission_before_dispatch_and_one_completion(ledger):
    a = attempt()
    def invoke():
        events = [json.loads(line) for line in ledger.read_text().splitlines()]
        assert [e["event"] for e in events] == ["initialized", "admitted", "dispatch_attempted"]
        assert budget.snapshot()["requests"] == 1
        assert budget.snapshot()["total_tokens"] is None
        return response()
    assert a.dispatch(invoke).output_text == "{}"
    assert a.finish({"sent": True})["attempt_id"] == a.attempt_id
    snap = budget.snapshot()
    assert snap["requests"] == 1 and len(snap["records"]) == 1
    assert snap["total_tokens"] == 12
    assert inspect_ledger(ledger, snap)["request_upper_bound"] == 1
    assert "output_text" not in ledger.read_text()


@pytest.mark.parametrize("error", [RuntimeError("private request content"), TimeoutError(), KeyboardInterrupt()])
def test_failures_and_interruptions_stay_accounted(ledger, error):
    a = attempt()
    def fail():
        raise error
    with pytest.raises(type(error)):
        a.dispatch(fail)
    snap = budget.snapshot()
    assert snap["requests"] == 1 and snap["total_tokens"] is None
    assert snap["records"][0]["sent"] is True
    assert snap["records"][0]["completion_status"] in {"failed", "interrupted"}
    assert "private request content" not in ledger.read_text()
    assert inspect_ledger(ledger, snap)["request_upper_bound"] == 1


def test_admitted_uncompleted_and_no_provider_usage(ledger):
    budget.initialize_accounting()
    assert inspect_ledger(ledger, budget.snapshot())["request_upper_bound"] == 0
    a = attempt()
    snap = budget.snapshot()
    observed = inspect_ledger(ledger, snap)
    assert observed["request_upper_bound"] == 1 and observed["pending_requests"] == 1
    assert observed["observed_sent_requests"] == 0
    a.finish({})
    assert budget.snapshot()["requests"] == 1


@pytest.mark.parametrize("purpose", ["expression", "interpretation", "narration"])
def test_multiple_and_single_purpose_requests(ledger, purpose):
    for _ in range(3):
        attempt(purpose=purpose).dispatch(response)
    assert budget.snapshot()["requests"] == 3
    assert len(budget.snapshot()["records"]) == 3


def test_concurrent_final_allowance_reserved_atomically(ledger, monkeypatch):
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "1")
    barrier = threading.Barrier(12)
    def request(_):
        barrier.wait()
        a = attempt()
        if not a.refusal:
            a.dispatch(response)
        return not a.refusal
    with ThreadPoolExecutor(max_workers=12) as pool:
        assert sum(pool.map(request, range(12))) == 1
    assert budget.snapshot()["requests"] == 1
    assert inspect_ledger(ledger, budget.snapshot())["request_upper_bound"] == 1


def test_concurrent_token_reservations_preserve_limits(ledger, monkeypatch):
    monkeypatch.setenv("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", "10")
    a = attempt()
    assert not a.refusal
    assert attempt().refusal == "input-token ceiling"


def test_exhaustion_duplicate_identity_and_dispatch(ledger, monkeypatch):
    a = attempt(attempt_id="stable")
    assert attempt(attempt_id="stable").refusal == "duplicate request identity"
    a.dispatch(response)
    with pytest.raises(budget.ProviderAccountingError, match="duplicate request dispatch"):
        a.dispatch(lambda: pytest.fail("second dispatch"))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "1")
    refused = attempt()
    assert refused.refusal == "request ceiling"
    with pytest.raises(budget.ProviderBudgetRefused):
        refused.dispatch(lambda: pytest.fail("over-limit dispatch"))
    assert budget.snapshot()["requests"] == 1


@pytest.mark.parametrize("reply", [None, NS(), response(False), NS(usage=NS(input_tokens=1, output_tokens=None, total_tokens=1))])
def test_partial_responses_and_missing_tokens_remain_unknown(ledger, reply):
    a = attempt()
    assert a.dispatch(lambda: reply) is reply
    snap = budget.snapshot()
    assert snap["requests"] == 1 and snap["total_tokens"] is None
    assert snap["records"][0]["input_tokens"] is None
    assert snap["stopped"]
    assert attempt().refusal


def test_ledger_write_failure_blocks_dispatch(ledger, monkeypatch):
    budget.initialize_accounting()
    monkeypatch.setattr(budget.os, "fsync", lambda *a: (_ for _ in ()).throw(OSError("disk")))
    a = attempt()
    assert a.refusal
    with pytest.raises(budget.ProviderBudgetRefused):
        a.dispatch(lambda: pytest.fail("unrecorded dispatch"))


def test_completion_write_failure_does_not_charge_twice(ledger, monkeypatch):
    a = attempt()
    original_append = budget._append
    def append(event):
        if event["event"] == "completed":
            raise OSError("completion disk error")
        original_append(event)
    monkeypatch.setattr(budget, "_append", append)
    with pytest.raises(budget.ProviderAccountingError):
        a.dispatch(response)
    a.finish({"input_tokens": 10, "output_tokens": 2, "total_tokens": 12})
    snap = budget.snapshot()
    assert snap["requests"] == 1 and snap["total_tokens"] == 12
    assert snap["stopped"]
    assert inspect_ledger(ledger, snap)["pending_requests"] == 1


def test_existing_ledger_cannot_restart_with_reset_counter(ledger):
    ledger.write_text("old evidence\n")
    assert attempt().refusal
    assert ledger.read_text() == "old evidence\n"


@pytest.mark.parametrize("damage", ["truncated", "duplicate", "snapshot", "non_object"])
def test_lifecycle_reconciliation_refuses_incomplete_evidence(ledger, damage):
    attempt().dispatch(response)
    snap = budget.snapshot()
    if damage == "truncated":
        ledger.write_text(ledger.read_text().rstrip("\n"))
    elif damage == "duplicate":
        with ledger.open("a") as f:
            f.write(json.dumps(snap["events"][1]) + "\n")
    elif damage == "non_object":
        with ledger.open("a") as f:
            f.write("3\n")
    else:
        snap["requests"] += 1
    assert inspect_ledger(ledger, snap)["request_upper_bound"] is None


@pytest.mark.parametrize("owner", ["expression", "interpretation", "contract", "candidate", "plan", "preflight", "narration"])
@pytest.mark.parametrize("fail", [False, "exception", "interruption", "refused"])
def test_each_dispatch_owner_accounts_success_or_provider_exception(ledger, monkeypatch, owner, fail):
    import openai
    from game import config
    calls = []
    if fail == "refused":
        monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    def create(**kwargs):
        calls.append(kwargs)
        assert budget.snapshot()["requests"] == 1
        assert json.loads(ledger.read_text().splitlines()[-1])["event"] == "dispatch_attempted"
        if fail == "interruption":
            raise KeyboardInterrupt()
        if fail == "exception":
            raise TimeoutError("sensitive content")
        return response()
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: NS(responses=NS(create=create)))
    monkeypatch.setattr(config, "get_openai_api_key", lambda: "stub-only")
    if owner == "expression":
        invoke = lambda: production_request_expression({"prompt": {"system": "system", "user": "user"}})
    elif owner == "interpretation":
        from game import live_chat_interpretation as mod
        monkeypatch.setattr(mod, "_contract", lambda: (None, None, None, None, "gpt-4.1-mini", None))
        monkeypatch.setattr(mod, "production_interpretation_schema", lambda: {})
        invoke = lambda: mod.request_interpretation([], estimated_input=10)
    elif owner == "contract":
        from game import semantic_interpreter as mod
        monkeypatch.setattr(mod, "get_openai_api_key", lambda: "stub-only")
        invoke = lambda: production_contract_request([])
    elif owner == "candidate":
        from game.host_constrained_candidates import invoke_candidate_provider
        invoke = lambda: invoke_candidate_provider({})
    elif owner == "plan":
        from game.unified_semantic_planning import _invoke_provider
        invoke = lambda: _invoke_provider({})
    elif owner == "preflight":
        from game.api_upstream_preflight import run_upstream_api_preflight
        invoke = lambda: run_upstream_api_preflight(api_key="stub-only", client_factory=lambda key: NS(responses=NS(create=create)))
    else:
        from tests.helpers.live_model_guard import production_call_gpt
        invoke = lambda: production_call_gpt()([], purpose="narration")
    try:
        invoke()
    except (TimeoutError, KeyboardInterrupt):
        assert fail in {"exception", "interruption"}
    except RuntimeError:
        assert fail == "refused"
    assert len(calls) == (0 if fail == "refused" else 1)
    snap = budget.snapshot()
    if fail == "refused":
        assert snap["requests"] == 0 and snap["dispatched_requests"] == 0
        return
    assert snap["requests"] == 1 and len(snap["records"]) == 1
    assert snap["records"][0]["owner"].split(".")[-1] in {
        "request_expression", "request_interpretation", "_invoke_interpretation_model", "invoke_candidate_provider",
        "_invoke_provider", "run_upstream_api_preflight", "call_gpt"}
    assert snap["records"][0]["sent"] is True
    assert inspect_ledger(ledger, snap)["request_upper_bound"] == 1


def test_early_return_adds_evidence_without_changing_response(ledger, monkeypatch):
    from game import api
    from game.models import ChatRequest
    logs = []
    monkeypatch.setattr(api, "append_log", logs.append)
    monkeypatch.setattr(api, "_public_live_interpretation", lambda o: o)
    budget.initialize_accounting()
    result = api._live_interpretation_block_response(ChatRequest(text="correction"), NS(original_text="correction", mode="IC", source="test"),
                                                    {"reason": "context_leak", "player_facing_text": "unchanged", "provider_requests": []})
    assert result["gm_output"]["player_facing_text"] == "unchanged"
    assert result["resolution"]["kind"] == "interpretation_rejected"
    md = result["resolution"]["metadata"]
    assert md["performance"]["input_tokens"] is None
    assert md["provider_accounting"]["request_upper_bound"] == 0
    assert logs[0]["resolution"] == result["resolution"]


def test_conditional_gates_do_not_admit_requests(ledger, monkeypatch):
    from game.semantic_interpreter import interpret_for_contract
    from game.host_constrained_candidates import candidate_selection_enabled
    from game.unified_semantic_planning import unified_semantic_planning_enabled
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.delenv("ASHEN_HOST_CONSTRAINED_CANDIDATES", raising=False)
    monkeypatch.delenv("ASHEN_UNIFIED_SEMANTIC_PLANNING", raising=False)
    assert interpret_for_contract({})["api_calls"] == 0
    assert not candidate_selection_enabled() and not unified_semantic_planning_enabled()
    assert budget.snapshot()["requests"] == 0


def test_atgb_worker_job_uses_remaining_budget_and_deadline(monkeypatch, tmp_path):
    import time
    from tools.atgb import driver
    from tools.atgb.budget import Budget
    captured = []
    def worker_stub(args, **kw):
        job = json.loads(Path(args[args.index("--job") + 1]).read_text())
        captured.append(job)
        assert job["max_provider_calls"] == 2
        assert job["max_tokens"] == 70
        assert job["max_estimated_cost"] == 0.5
        assert kw["timeout"] <= 10
        Path(args[args.index("--output") + 1]).write_text(json.dumps({"turns": [], "stop_reason": None}))
        return NS(returncode=0)
    monkeypatch.setattr(driver.subprocess, "run", worker_stub)
    driver._host_scenario({"scenario_id": "S04", "turns": []}, prepared=tmp_path,
        config=driver.RunConfig(mode="live_provider", worker_timeout_seconds=300,
                               budget=Budget(max_provider_calls=5, max_tokens=100, max_estimated_cost=1, max_elapsed_seconds=10)),
        repo=ROOT, player_campaign=ROOT / "data", started=time.monotonic(), expected_location_id="frontier_gate",
        prior_provider_calls=3, prior_tokens=30, prior_cost=0.5)
    assert len(captured) == 1


def test_readiness_acceptance_is_not_live_execution():
    assert live_accounting_readiness(ROOT)["ok"]


@pytest.mark.parametrize("damage", ["unwrapped", "new_site", "new_http", "core", "manifest"])
def test_readiness_refuses_unsafe_or_unreviewed_sources(tmp_path, damage):
    fake = tmp_path / "repo"
    (fake / "game").mkdir(parents=True)
    (fake / "tools/atgb").mkdir(parents=True)
    manifest = json.loads((ROOT / "tools/atgb/provider_accounting_integrity.json").read_text())
    paths = set(manifest["application_source_sha256"]) | {"tools/atgb/provider_accounting_integrity.json"}
    for rel in paths:
        (fake / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, fake / rel)
    if damage == "unwrapped":
        p = fake / "game/semantic_interpreter.py"
        p.write_text(p.read_text().replace("attempt.dispatch(client.responses.create,", "client.responses.create("))
    elif damage == "new_site":
        (fake / "game/new_provider.py").write_text("def send(client):\n    return client.responses.create(model='unknown')\n")
    elif damage == "new_http":
        (fake / "game/new_http.py").write_text("def send(client):\n    return client.post('https://provider.invalid')\n")
    elif damage == "core":
        with (fake / "game/provider_budget.py").open("a") as f:
            f.write("\n# changed implementation\n")
    else:
        (fake / "tools/atgb/provider_accounting_integrity.json").unlink()
    assert not live_accounting_readiness(fake)["ok"]
