"""PR-PLAY-04 campaign-opening acceptance and commit integrity.

Deterministic provider stubs only. These checks do not show that a live model
will generate a valid opening.
"""

from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from types import SimpleNamespace

import openai
import pytest
from starlette.requests import Request

import game.api as api
import game.gm as gm
import game.storage as st
from game import provider_budget as budget
from game.immutable_valid_response import safe_nonresolution
from game.models import ChatRequest
from tests.helpers.live_model_guard import production_call_gpt
from tests.helpers.turn_pipeline_http_fixtures import _seed_campaign_start_storage

VALID_NARRATION = (
    "You stand at Cinderwatch's eastern gate. Rain spatters soot-dark stone; frayed banners hang "
    "above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; "
    "guards hold the choke while the crowd presses in. A tavern runner shouts offers of hot stew and "
    "paid rumor. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. "
    "You can read the notice board, approach the tavern runner, or watch the crowd."
)
MARKET_NARRATION = (
    "A moneylender's house flies noble colors. Canvases snap in the wind over the market stalls."
)


def _request() -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/start_campaign",
        "headers": [],
        "query_string": b"ui_mode=player",
    })


def _decode(response):
    if hasattr(response, "body"):
        return json.loads(response.body), getattr(response, "status_code", 200)
    return response, 200


def _factions(world: dict) -> list[dict]:
    rows = []
    for faction in world.get("factions") or []:
        if isinstance(faction, dict):
            rows.append({
                "id": faction.get("id"),
                "pressure": faction.get("pressure"),
                "agenda_progress": faction.get("agenda_progress"),
            })
    return rows


def _snap() -> dict:
    session = st.load_session()
    world = st.load_world()
    return {
        "campaign_started": bool(session.get("campaign_started")),
        "turn_counter": int(session.get("turn_counter") or 0),
        "time_pressure": int((session.get("clocks") or {}).get("time_pressure") or 0),
        "log_length": len(st.load_log()),
        "can_start": api._session_allows_structured_start_campaign(session, st.load_log()),
        "factions": _factions(world),
        "event_types": [row.get("type") for row in (world.get("event_log") or []) if isinstance(row, dict)],
    }


def _envelope(narration: str) -> str:
    return json.dumps({"declared_claims": [], "narration": narration})


@pytest.fixture
def opening_world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")
    monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    monkeypatch.delenv("ASHEN_PROVIDER_REQUEST_LIMIT", raising=False)
    monkeypatch.delenv("ASHEN_PROVIDER_USAGE_PATH", raising=False)
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(api, "_compute_upstream_gate_for_live_gameplay", lambda: ({"manual_testing_blocked": False}, {}))
    monkeypatch.setattr(gm, "get_openai_api_key", lambda: "offline-placeholder")
    calls: list[dict] = []
    state = {"text": _envelope(VALID_NARRATION), "raise": False}

    def create(**kwargs):
        calls.append({"max_seen": True})
        if state["raise"]:
            raise RuntimeError("synthetic SDK operation failure")
        return SimpleNamespace(
            output_text=state["text"],
            model="offline-stub",
            id="synthetic-response",
            usage=SimpleNamespace(input_tokens=20, output_tokens=10, total_tokens=30),
            status="completed",
        )

    def ctor(**kwargs):
        assert kwargs.get("max_retries") == 0
        return SimpleNamespace(responses=SimpleNamespace(create=create))

    monkeypatch.setattr(openai, "OpenAI", ctor)
    real_call = production_call_gpt()
    monkeypatch.setattr(gm, "call_gpt", real_call)
    monkeypatch.setattr(api, "call_gpt", real_call)
    api.new_campaign(_request())
    before = _snap()
    return {"calls": calls, "state": state, "before": before}


def _start():
    return _decode(api.start_campaign(_request()))


def test_valid_opening_commits_once_and_repeat_does_not(opening_world):
    body, status = _start()
    assert status == 200, body.get("opening_failure_reason")
    assert body.get("ok") is True
    assert body["gm_output"]["player_facing_text"] == VALID_NARRATION
    assert ((body["gm_output"].get("metadata") or {}).get("accepted_response") or {}).get("provenance") == "initial_generation"
    after = _snap()
    assert after["campaign_started"] is True
    assert after["turn_counter"] == 1
    assert after["time_pressure"] == 1
    assert after["log_length"] == 1
    assert after["can_start"] is False
    assert [row["pressure"] for row in after["factions"]] == [3, 3, 2]
    assert len(opening_world["calls"]) == 1

    again, again_status = _start()
    assert again_status == 409
    assert again.get("status") == "already_started"
    assert _snap() == after
    assert len(opening_world["calls"]) == 1


@pytest.mark.parametrize(
    "label,text",
    [
        ("missing_envelope", "You stand beside the gate in the rain."),
        ("malformed_json", "{not json"),
        ("incomplete_envelope", '{"declared_claims": []'),
        ("truncated_json", '{"declared_claims": [], "narration": "You stand at the gate'),
        ("empty_response", ""),
    ],
)
def test_invalid_provider_output_fails_without_progression(opening_world, label, text):
    opening_world["state"]["text"] = text
    before = _snap()
    body, status = _start()
    assert status == 422, label
    assert body.get("ok") is False
    assert body.get("status") == "opening_failed"
    assert body.get("gameplay_committed") is False
    assert "could not be generated" in body.get("error", "")
    assert "answer that" not in body.get("error", "").lower()
    assert body.get("gm_output") is None
    assert _snap() == before
    assert len(opening_world["calls"]) == 1


def test_provider_exception_does_not_commit(opening_world):
    opening_world["state"]["raise"] = True
    before = _snap()
    body, status = _start()
    assert status == 422
    assert body.get("opening_failure_reason") == "provider_opening_not_delivered"
    assert _snap() == before
    assert len(opening_world["calls"]) == 1


def test_failure_then_failure_then_success_commits_once(opening_world):
    opening_world["state"]["text"] = "plain prose"
    before = _snap()
    first, first_status = _start()
    second, second_status = _start()
    assert first_status == second_status == 422
    assert _snap() == before
    opening_world["state"]["text"] = _envelope(VALID_NARRATION)
    body, status = _start()
    assert status == 200
    assert body["gm_output"]["player_facing_text"] == VALID_NARRATION
    after = _snap()
    assert after["turn_counter"] == 1
    assert after["time_pressure"] == 1
    assert [row["agenda_progress"] for row in after["factions"]] == [1, 1, 1]
    assert len(opening_world["calls"]) == 3


def test_provider_exception_then_success_commits_once(opening_world):
    opening_world["state"]["raise"] = True
    assert _start()[1] == 422
    opening_world["state"]["raise"] = False
    body, status = _start()
    assert status == 200
    assert body["gm_output"]["player_facing_text"] == VALID_NARRATION
    assert _snap()["turn_counter"] == 1
    assert len(opening_world["calls"]) == 2


def test_pipeline_exception_restores_world_and_session(opening_world, monkeypatch):
    before = _snap()

    def _boom(**_kwargs):
        raise RuntimeError("synthetic pipeline failure")

    monkeypatch.setattr(api, "_run_resolved_turn_pipeline", _boom)
    with pytest.raises(RuntimeError):
        api.start_campaign(_request())
    assert _snap() == before


def test_exception_before_provider_dispatch_restores_state(opening_world, monkeypatch):
    before = _snap()

    def _boom(*_args, **_kwargs):
        raise RuntimeError("before dispatch")

    monkeypatch.setattr(api, "call_gpt", _boom)
    with pytest.raises(RuntimeError):
        api.start_campaign(_request())
    assert _snap() == before
    assert opening_world["calls"] == []


def test_persistence_failure_before_commit_restores_baseline(opening_world, monkeypatch):
    before = _snap()
    real_save = st.save_world
    seen = {"n": 0}

    def _fail_once(data):
        seen["n"] += 1
        if seen["n"] == 1:
            raise OSError("injected world save failure")
        return real_save(data)

    monkeypatch.setattr(st, "save_world", _fail_once)
    monkeypatch.setattr(api, "save_world", _fail_once)
    with pytest.raises(OSError):
        api.start_campaign(_request())
    assert _snap() == before


def test_budget_rejection_is_before_dispatch(opening_world, monkeypatch, tmp_path):
    for name, value in {
        "_REQUESTS": 0, "_RECORDS": [], "_EVENTS": [], "_ATTEMPTS": {},
        "_INPUT": 0, "_OUTPUT": 0, "_RESERVED_INPUT": 0, "_RESERVED_OUTPUT": 0,
        "_USAGE_KNOWN": True, "_STOPPED": False, "_STOP_REASON": "",
        "_INITIALIZED": False, "_LEDGER_PATH": None,
    }.items():
        monkeypatch.setattr(budget, name, value)
    monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(tmp_path / f"usage-{uuid.uuid4().hex}.jsonl"))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    monkeypatch.setenv("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", "1000000")
    monkeypatch.setenv("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT", "1000000")
    monkeypatch.setenv("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", "1000000")
    monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    before = _snap()
    body, status = _start()
    assert status == 409
    assert body.get("status") == "blocked"
    assert _snap() == before
    assert opening_world["calls"] == []


def test_dispatched_failure_consumes_admission_and_blocks_the_next_start(opening_world, monkeypatch, tmp_path):
    for name, value in {
        "_REQUESTS": 0, "_RECORDS": [], "_EVENTS": [], "_ATTEMPTS": {},
        "_INPUT": 0, "_OUTPUT": 0, "_RESERVED_INPUT": 0, "_RESERVED_OUTPUT": 0,
        "_USAGE_KNOWN": True, "_STOPPED": False, "_STOP_REASON": "",
        "_INITIALIZED": False, "_LEDGER_PATH": None,
    }.items():
        monkeypatch.setattr(budget, name, value)
    monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(tmp_path / f"usage-{uuid.uuid4().hex}.jsonl"))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "1")
    monkeypatch.setenv("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", "1000000")
    monkeypatch.setenv("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT", "1000000")
    monkeypatch.setenv("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", "1000000")
    monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    opening_world["state"]["text"] = "plain prose"
    before = _snap()
    failed, failed_status = _start()
    assert failed_status == 422
    assert len(opening_world["calls"]) == 1
    blocked, blocked_status = _start()
    assert blocked_status == 409
    assert blocked.get("status") == "blocked"
    assert len(opening_world["calls"]) == 1
    assert _snap() == before


def test_market_quarter_opening_is_independent_of_cinderwatch_text(opening_world):
    session = st.load_session()
    session["active_scene_id"] = "market_quarter"
    st.save_session(session)
    opening_world["state"]["text"] = "The harbor bell is not an opening."
    before = _snap()
    failed, failed_status = _start()
    assert failed_status == 422
    assert _snap()["factions"] == before["factions"]
    assert _snap()["turn_counter"] == 0
    opening_world["state"]["text"] = _envelope(MARKET_NARRATION)
    body, status = _start()
    assert status == 200
    assert body["gm_output"]["player_facing_text"] == MARKET_NARRATION
    assert _snap()["turn_counter"] == 1
    assert _snap()["campaign_started"] is True


def test_concurrent_starts_commit_one_opening(opening_world, monkeypatch):
    entered = threading.Event()
    release = threading.Event()

    def ctor(**kwargs):
        assert kwargs.get("max_retries") == 0

        def _create(**_kwargs):
            opening_world["calls"].append({"concurrent": True})
            entered.set()
            release.wait(timeout=5)
            return SimpleNamespace(
                output_text=_envelope(VALID_NARRATION),
                model="offline-stub",
                id="synthetic-response",
                usage=SimpleNamespace(input_tokens=20, output_tokens=10, total_tokens=30),
                status="completed",
            )

        return SimpleNamespace(responses=SimpleNamespace(create=_create))

    monkeypatch.setattr(openai, "OpenAI", ctor)
    results = []

    def run():
        try:
            results.append(_start())
        except BaseException as exc:  # noqa: BLE001 - keep the thread from escaping
            results.append(({"error": type(exc).__name__}, 500))

    first = threading.Thread(target=run)
    second = threading.Thread(target=run)
    first.start()
    assert entered.wait(timeout=5)
    second.start()
    second.join(timeout=0.5)
    assert second.is_alive()
    assert len(opening_world["calls"]) == 1
    release.set()
    first.join(timeout=10)
    second.join(timeout=10)
    assert not first.is_alive() and not second.is_alive()
    statuses = sorted(item[1] for item in results)
    assert statuses == [200, 409]
    assert len(opening_world["calls"]) == 1
    assert _snap()["turn_counter"] == 1
    assert _snap()["campaign_started"] is True


def test_ordinary_information_fallback_is_not_treated_as_an_opening():
    line = safe_nonresolution({"operation": "unresolved", "raw_input": "What is sold at the stall?"}, player_text="What is sold at the stall?")
    assert "answer" in line.lower()
    reason = api._opening_response_rejection(
        {
            "player_facing_text": line,
            "metadata": {"accepted_response": {"provenance": "safe_nonresolution"}},
        },
        {"kind": "observe", "action_id": "look"},
        {"required_response_type": "answer"},
    )
    assert reason is None


def test_chat_campaign_start_failure_then_success(opening_world):
    opening_world["state"]["text"] = "not an envelope"
    failed = api.chat(ChatRequest(text="Start the campaign."))
    failed_body, failed_status = _decode(failed)
    assert failed_status == 422
    assert failed_body.get("status") == "opening_failed"
    assert _snap()["campaign_started"] is False
    assert _snap()["turn_counter"] == 0
    opening_world["state"]["text"] = _envelope(VALID_NARRATION)
    succeeded = api.chat(ChatRequest(text="Start the campaign."))
    body, status = _decode(succeeded)
    assert status == 200
    assert body.get("ok") is True
    assert _snap()["turn_counter"] == 1
    assert _snap()["time_pressure"] == 1
