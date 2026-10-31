"""Offline checks at production constructors/dispatches; never permit network I/O."""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as NS

import openai
import pytest

from game import provider_budget as budget
from game.api_upstream_preflight import _default_openai_client_factory as preflight_factory
from game.semantic_interpreter import _invoke_interpretation_model as contract_request
from game.expressive_dialogue import request_expression as expression_request
from tests.test_provider_accounting_integrity import ledger, response
from tools.atgb.accounting import inspect_ledger

REAL_OPENAI = openai.OpenAI


@pytest.fixture
def playtest(ledger, monkeypatch):
    monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "6")
    return ledger


def invoke_owner(owner, monkeypatch):
    from game import config
    monkeypatch.setattr(config, "get_openai_api_key", lambda: "stub-only")
    if owner == "interpretation":
        from game import live_chat_interpretation as mod
        monkeypatch.setattr(mod, "_contract", lambda: (None, None, None, None, "gpt-4.1-mini", None))
        monkeypatch.setattr(mod, "production_interpretation_schema", lambda: {})
        return lambda: mod.request_interpretation([], estimated_input=10)
    if owner == "narration":
        from tests.helpers.live_model_guard import production_call_gpt
        return lambda: production_call_gpt()([], purpose="narration")
    if owner == "expression":
        return lambda: expression_request({"prompt": {"system": "system", "user": "user"}})
    if owner == "contract":
        from game import semantic_interpreter as mod
        monkeypatch.setattr(mod, "get_openai_api_key", lambda: "stub-only")
        return lambda: contract_request([])
    if owner == "candidate":
        from game.host_constrained_candidates import invoke_candidate_provider
        return lambda: invoke_candidate_provider({})
    if owner == "plan":
        from game.unified_semantic_planning import _invoke_provider
        return lambda: _invoke_provider({})
    from game.api_upstream_preflight import run_upstream_api_preflight
    return lambda: run_upstream_api_preflight(api_key="stub-only", client_factory=preflight_factory)


OWNERS = ["interpretation", "narration", "expression", "contract", "candidate", "plan", "preflight"]


@pytest.mark.parametrize("owner", OWNERS)
@pytest.mark.parametrize("enabled", [False, True])
def test_effective_constructor_and_dispatch(ledger, monkeypatch, owner, enabled):
    if enabled:
        monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    else:
        monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
    constructors, calls = [], []
    def constructor(**kwargs):
        constructors.append(kwargs)
        return NS(responses=NS(create=lambda **kw: calls.append(kw) or response()))
    monkeypatch.setattr(openai, "OpenAI", constructor)
    invoke_owner(owner, monkeypatch)()
    assert len(constructors) == len(calls) == 1
    if enabled:
        assert constructors[0]["max_retries"] == 0
    else:
        assert "max_retries" not in constructors[0]
    assert budget.snapshot()["dispatched_requests"] == 1


@pytest.mark.parametrize("owner", OWNERS)
def test_each_production_path_rejects_seventh_before_sdk(playtest, monkeypatch, owner):
    calls = []
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: NS(responses=NS(create=lambda **kw: calls.append(kw) or response())))
    request = invoke_owner(owner, monkeypatch)
    for _ in range(6):
        request()
    try:
        request()
    except RuntimeError as exc:
        assert str(exc) == "request ceiling"
    snap = budget.snapshot()
    assert len(calls) == snap["requests"] == snap["dispatched_requests"] == 6
    assert len([e for e in snap["events"] if e["event"] == "rejected"]) == 1
    assert inspect_ledger(playtest, snap)["request_upper_bound"] == 6


def test_shared_budget_multiple_operations_and_submissions(playtest, monkeypatch):
    calls = []
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: NS(responses=NS(create=lambda **kw: calls.append(kw) or response())))
    interpretation = invoke_owner("interpretation", monkeypatch)
    narration = invoke_owner("narration", monkeypatch)
    # Three simulated submissions, with two real production operations per submission.
    for _ in range(3):
        interpretation()
        narration()
    refused = interpretation()
    assert refused["sent"] is False and refused["reason"] == "request ceiling"
    snap = budget.snapshot()
    assert len(calls) == snap["dispatched_requests"] == 6
    assert [r["sequence"] for r in snap["records"]] == list(range(1, 7))
    assert snap["total_tokens"] == 72
    assert all(e["sdk_retries"] == 0 and e["host_retries"] == "disabled" for e in snap["events"][1:])
    rejected = snap["events"][-1]
    assert rejected["event"] == "rejected" and rejected["budget_remaining"] == 0
    assert rejected["total_tokens"] is None and rejected["sent"] is False


def test_failed_production_dispatch_consumes_admission_and_usage_unknown(playtest, monkeypatch):
    calls = []
    def fail(**kw):
        calls.append(kw)
        raise TimeoutError("sensitive exception text")
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: NS(responses=NS(create=fail)))
    request = invoke_owner("interpretation", monkeypatch)
    assert request()["ok"] is False
    assert request()["sent"] is False  # Existing fail-closed policy stops on unknown usage.
    snap = budget.snapshot()
    assert len(calls) == snap["requests"] == 1
    assert snap["total_tokens"] is None
    assert snap["records"][0]["completion_status"] == "failed"
    assert "sensitive exception text" not in playtest.read_text()


def test_concurrent_production_operations_share_six_admissions(playtest, monkeypatch):
    calls = []
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: NS(responses=NS(create=lambda **kw: calls.append(kw) or response())))
    interpretation = invoke_owner("interpretation", monkeypatch)
    narration = invoke_owner("narration", monkeypatch)
    barrier = threading.Barrier(16)
    def run(i):
        barrier.wait()
        (interpretation if i % 2 else narration)()
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(run, range(16)))
    snap = budget.snapshot()
    assert len(calls) == snap["requests"] == snap["dispatched_requests"] == 6
    assert len([e for e in snap["events"] if e["event"] == "rejected"]) == 10
    assert inspect_ledger(playtest, snap)["request_upper_bound"] == 6


def test_exhausted_chat_and_opening_do_not_reach_state_or_resolver(playtest, monkeypatch):
    from game import api
    from game.models import ChatRequest
    from starlette.requests import Request
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: NS(responses=NS(create=lambda **kw: response())))
    for _ in range(6):
        invoke_owner("interpretation", monkeypatch)()
    logs = []
    monkeypatch.setattr(api, "append_log", logs.append)
    for name in ["load_session", "load_world", "load_character", "load_combat", "save_session", "save_world", "save_character", "save_combat", "interpret_production_turn"]:
        monkeypatch.setattr(api, name, lambda *a, **kw: pytest.fail("exhausted operation reached state/interpretation"))
    for text in ["I examine the signal mirror.", "Yes, proceed.", "/ooc What happened?"]:
        result = api.chat(ChatRequest(text=text))
        assert "controlled playtest request limit" in result["gm_output"]["player_facing_text"]
        assert result["resolution"]["metadata"]["authoritative_mutation"] is False
    result = api.start_campaign(Request({"type": "http", "headers": []}))
    assert result.status_code == 409
    assert len(logs) == 3 and budget.snapshot()["requests"] == 6


def test_real_sdk_transport_has_no_retry(playtest, monkeypatch):
    # Installed SDK + its supported mock transport: no socket can be reached.
    from openai._base_client import httpx
    calls, clients = [], []
    def transport(request):
        calls.append(request)
        return httpx.Response(429, json={"error": {"message": "stub rate limit", "type": "rate_limit"}})
    def constructor(**kwargs):
        client = REAL_OPENAI(**kwargs, http_client=openai.DefaultHttpxClient(transport=httpx.MockTransport(transport)))
        clients.append(client)
        assert client.max_retries == 0
        return client
    monkeypatch.setattr(openai, "OpenAI", constructor)
    try:
        assert invoke_owner("interpretation", monkeypatch)()["ok"] is False
        assert len(calls) == 1
        assert budget.snapshot()["dispatched_requests"] == 1
    finally:
        for client in clients:
            client.close()


def test_host_retry_refused_before_constructor(playtest, monkeypatch):
    from tests.helpers.live_model_guard import production_call_gpt
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: pytest.fail("host retry constructed SDK"))
    result = production_call_gpt()([], retry_attempt=1)
    assert "provider_retry_disabled" in result["tags"]
    assert budget.snapshot()["requests"] == 0


def test_real_chat_submissions_do_not_reset_budget(playtest, monkeypatch, tmp_path):
    from game import api
    from game.models import ChatRequest
    from tests.test_pr_ef_gm_authority import seed_scene
    seed_scene(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: NS(responses=NS(create=lambda **kw: calls.append(kw) or response())))
    request = invoke_owner("interpretation", monkeypatch)
    def controlled_interpretation(**kwargs):
        result = request()
        # End each fixture turn through the production nonmutating error path.
        return {"status": "blocked", "reason": "fixture_stop", "record": None,
                "player_facing_text": "Fixture interpretation complete.", "provider_requests": [result["usage"]]}
    monkeypatch.setattr(api, "interpret_production_turn", controlled_interpretation)
    monkeypatch.setattr(api, "_stored_interpretation_for_player_text", lambda *_: None)
    for _ in range(6):
        assert api.chat(ChatRequest(text="What is visible near the signal mirror?"))["ok"]
    result = api.chat(ChatRequest(text="I examine the mirror."))
    assert "controlled playtest request limit" in result["gm_output"]["player_facing_text"]
    assert len(calls) == budget.snapshot()["requests"] == 6


def test_supported_data_directory_in_fresh_process(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    env = dict(os.environ, ASHEN_DATA_DIR=str(tmp_path / "disposable"), ASHEN_DISABLE_PROVIDER_CALLS="1")
    result = subprocess.run([sys.executable, "-c", """
from pathlib import Path
import os
from game import storage
from game.campaign_reset import apply_new_campaign_hard_reset
assert storage.DATA_DIR == Path(os.environ['ASHEN_DATA_DIR']).resolve()
result = apply_new_campaign_hard_reset()
assert result['silent_reset_no_implicit_transcript'] is True
assert storage.load_session()['campaign_started'] is False
assert storage.load_log() == []
assert storage.SESSION_PATH.is_file()
print('isolated reset passed; separate Start Campaign still required')
"""], env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr


def test_default_has_no_playtest_gate_or_constructor_override(monkeypatch):
    monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
    monkeypatch.setattr(budget, "_STOPPED", True)
    assert budget.sdk_retry_options() == {}
    assert budget.playtest_stop_reason() == ""
