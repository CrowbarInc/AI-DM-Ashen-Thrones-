"""PR-PLAY-79D-F3 operational refusal classification.

Development checks against the HTTP publication boundary. The frozen holdout
is a separate module.
"""
from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.player_http_projection import project_player_response
from game.publication_contract import (
    OPERATIONAL_REFUSAL,
    note_completed_publication,
    record_completed_publication,
    response_is_operational_refusal,
)
from tests.pr_play_79df3_harness import PRIOR, chat_turn, reset_budget, seed_gate

PHRASE = "Good day, Gate Guard."


def _assert_operational(row, category):
    assert row["status"] == 200
    assert row["ok"] is True
    assert row["visible"]
    assert row["operational"] is True
    assert row["response_class"] == OPERATIONAL_REFUSAL
    assert row["refusal_category"] == category
    assert row["publication_events"] == []
    assert row["pointer_unchanged"] is True
    assert row["pointer_after"] == PRIOR
    assert row["turn_after"] == row["turn_before"] == 4
    assert row["world_unchanged"] is True
    assert row["character_unchanged"] is True
    assert row["hidden_exposed"] is False
    assert row["log_class"] == OPERATIONAL_REFUSAL
    assert row["gameplay_publication_completed"] is False
    assert "response_class" not in row["body"]
    assert row["body"].get("resolution") == {}


def test_request_ceiling_is_operational(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, PHRASE, request_limit="0")
    _assert_operational(row, "request ceiling")
    assert "no gameplay action was taken" in row["visible"]
    assert row["requests_after"] == 0
    assert row["tokens_after"] == 0
    assert row["provider_calls"] == 0
    assert row["provider_request_sent"] is False
    assert row["failure_stage"] == "provider_admission"


def test_input_ceiling_is_operational(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, PHRASE, input_limit="1")
    _assert_operational(row, "input-token ceiling")
    assert row["requests_after"] == 0 and row["tokens_after"] == 0 and row["provider_calls"] == 0


def test_output_ceiling_is_operational(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, PHRASE, output_limit="10")
    _assert_operational(row, "output-token ceiling")
    assert row["requests_after"] == 0 and row["provider_calls"] == 0


def test_total_ceiling_is_operational(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, PHRASE, total_limit="50", input_limit="100000", output_limit="100000")
    _assert_operational(row, "total-token ceiling")
    assert row["requests_after"] == 0 and row["provider_calls"] == 0


def test_accounting_unavailable_is_operational(tmp_path, monkeypatch):
    blocked = tmp_path / "ledger-dir"
    blocked.mkdir()
    row = chat_turn(tmp_path, monkeypatch, PHRASE, usage_path=blocked)
    _assert_operational(row, "provider admission accounting unavailable")
    assert row["requests_after"] == 0 and row["provider_calls"] == 0


def test_playtest_ceiling_is_operational(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, PHRASE, request_limit="0", playtest=True)
    _assert_operational(row, "playtest_stopped")
    assert "controlled playtest request limit" in row["visible"].casefold()
    assert row["provider_calls"] == 0 and row["requests_after"] == 0


def test_token_estimate_unavailable_is_operational(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, PHRASE, estimate=0)
    _assert_operational(row, "token_estimate_unavailable")
    assert "token estimate is unavailable" in row["visible"]
    assert row["provider_calls"] == 0 and row["requests_after"] == 0


def test_provider_exception_is_operational(tmp_path, monkeypatch):
    def create(**_kwargs):
        raise TimeoutError("secret prompt text")

    row = chat_turn(tmp_path, monkeypatch, PHRASE, create=create)
    _assert_operational(row, "provider_failure")
    assert row["failure_stage"] == "interpretation_service"
    assert row["provider_request_sent"] is True
    assert row["provider_calls"] == 1
    assert row["requests_after"] == 1
    assert "secret prompt" not in row["visible"]
    assert "secret prompt" not in json.dumps(row["body"])


def test_model_mismatch_is_operational(tmp_path, monkeypatch):
    def create(**_kwargs):
        usage = type("Usage", (), {"input_tokens": 2, "output_tokens": 1, "total_tokens": 3})()
        return type("Resp", (), {"model": "other-model", "output_text": "{}", "id": "r", "usage": usage})()

    row = chat_turn(tmp_path, monkeypatch, PHRASE, create=create)
    _assert_operational(row, "model_mismatch")
    assert row["provider_calls"] == 1
    assert row["requests_after"] == 1
    assert row["provider_request_sent"] is True
    assert row["publication_events"] == []


def test_malformed_provider_output_stays_gameplay(tmp_path, monkeypatch):
    def create(**_kwargs):
        usage = type("Usage", (), {"input_tokens": 2, "output_tokens": 1, "total_tokens": 3})()
        return type("Resp", (), {"model": "gpt-4.1-mini", "output_text": "not-json", "id": "r", "usage": usage})()

    row = chat_turn(tmp_path, monkeypatch, PHRASE, create=create)
    assert row["operational"] is False
    assert row["status"] == 200
    assert "plain words" in row["visible"]
    assert row["publication_events"]
    assert row["publication_events"][-1]["response_category"] != "operational_refusal"
    assert row["pointer_unchanged"] is True
    assert "not-json" not in row["visible"]


def test_context_leak_stays_a_gameplay_refusal(tmp_path, monkeypatch):
    blocked = {
        "status": "blocked",
        "reason": "context_leak",
        "player_facing_text": "I can't interpret that from the current scene without using information you have not been shown.",
        "tags": ["interpretation_rejected", "non_mutating"],
        "record": None,
        "provider_requests": [],
    }
    row = chat_turn(tmp_path, monkeypatch, PHRASE, interpret_result=blocked)
    assert row["operational"] is False
    assert row["refusal_category"] is None
    assert "have not been shown" in row["visible"]
    assert row["publication_events"]
    assert row["pointer_unchanged"] is True
    assert row["provider_calls"] == 0


def test_clarification_remains_gameplay(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, "", interpret=False)
    assert row["operational"] is False
    assert row["status"] == 200
    assert row["visible"]
    assert row["publication_events"]
    assert row["publication_events"][-1]["final_player_facing_response"] == row["visible"]
    assert row["pointer_unchanged"] is True
    assert row["world_unchanged"] is True
    assert row["requests_after"] == 0


def test_unsupported_action_remains_gameplay(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, "I fly to the moon.", interpret=False)
    assert row["operational"] is False
    assert "cannot carry that out" in row["visible"].casefold()
    assert row["publication_events"]
    assert row["publication_events"][-1]["final_player_facing_response"] == row["visible"]
    assert row["pointer_unchanged"] is True
    assert row["turn_after"] == 4
    assert row["world_unchanged"] is True


def test_direct_recorder_drops_operational_class(tmp_path, monkeypatch):
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
    assert record_completed_publication(
        {"gm_output": {"player_facing_text": "I couldn't interpret that just now, so no gameplay action was taken."}},
        source_handler="api_chat",
        response_class=OPERATIONAL_REFUSAL,
    ) is None
    assert not (tmp_path / "events.jsonl").exists()


def test_server_error_is_not_a_successful_gameplay_publication(tmp_path, monkeypatch):
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))

    class Response:
        status_code = 500
        body = json.dumps({"ok": False, "error": "You cannot act right now."}).encode()

    row = record_completed_publication(Response(), source_handler="api_chat")
    assert row["status_code"] == 500
    assert row["response_category"] == "error"
    assert row["validation_outcome"] != "accepted_expression"


def test_projection_and_frontend_shape(tmp_path, monkeypatch):
    row = chat_turn(tmp_path, monkeypatch, PHRASE, request_limit="0")
    projected = project_player_response({
        "ok": True,
        "gm_output": {"player_facing_text": row["visible"], "debug_notes": "hidden"},
        "resolution": {"metadata": {"response_class": OPERATIONAL_REFUSAL, "refusal_category": "request ceiling"}},
    })
    assert projected["ok"] is True
    assert projected["gm_output"]["player_facing_text"] == row["visible"]
    assert projected["resolution"] == {}
    assert "debug_notes" not in json.dumps(projected)
    assert "refusal_category" not in json.dumps(projected)
    source = (tmp_path.parents[3] / "static" / "app.js").read_text(encoding="utf-8") if False else open(
        __import__("pathlib").Path(__file__).resolve().parents[1] / "static" / "app.js", encoding="utf-8"
    ).read()
    assert "data.gm_output?.player_facing_text" in source
    assert "if(!data.ok)" in source


def test_duplicate_refusal_does_not_publish(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    events = tmp_path / "events.jsonl"
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(events))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
    monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
    with TestClient(app) as client:
        reset_budget(tmp_path / "usage.jsonl")
        first = client.post("/api/chat?ui_mode=player", json={"text": PHRASE, "client_request_id": "same"})
        second = client.post("/api/chat?ui_mode=player", json={"text": PHRASE, "client_request_id": "same"})
    assert first.status_code == second.status_code == 200
    assert first.json()["gm_output"]["player_facing_text"] == second.json()["gm_output"]["player_facing_text"]
    assert not events.exists() or events.read_text(encoding="utf-8").strip() == ""
    assert storage.load_session()["last_publication"]["visible"] == PRIOR
    assert len(storage.load_log()) == 1


def test_two_refusals_then_gameplay_advances(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    events = tmp_path / "events.jsonl"
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(events))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
    monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
    with TestClient(app) as client:
        reset_budget(tmp_path / "usage.jsonl")
        client.post("/api/chat?ui_mode=player", json={"text": PHRASE, "client_request_id": "a"})
        client.post("/api/chat?ui_mode=player", json={"text": "Blargh the seventh bell.", "client_request_id": "b"})
        assert storage.load_session()["last_publication"]["visible"] == PRIOR
        assert storage.load_session()["turn_counter"] == 4
        monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
        monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "5")
        played = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "c"})
    assert played.status_code == 200
    visible = played.json()["gm_output"]["player_facing_text"]
    assert visible and "no gameplay action was taken" not in visible
    assert storage.load_session()["last_publication"]["visible"] == visible
    assert "CANARY" not in visible
    lines = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    assert lines[0]["final_player_facing_response"] == visible


def test_repeat_investigation_does_not_add_a_hidden_canary(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    events = tmp_path / "events.jsonl"
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(events))
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "4")
    with TestClient(app) as client:
        reset_budget(tmp_path / "usage.jsonl")
        first = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "e1"})
        after_first = json.dumps(storage.load_world(), sort_keys=True)
        second = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "e2"})
    assert first.status_code == second.status_code == 200
    one = first.json()["gm_output"]["player_facing_text"]
    two = second.json()["gm_output"]["player_facing_text"]
    assert "CANARY" not in one and "CANARY" not in two
    assert storage.load_session()["last_publication"]["visible"] == two
    assert json.dumps(storage.load_world(), sort_keys=True) == after_first or "nothing new" in two.casefold() or two == one
    blob = json.dumps(storage.load_session())
    assert "CANARY_UNDISCOVERED_CLUE" not in blob


def test_save_reload_keeps_the_preceding_publication(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
    monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
    with TestClient(app) as client:
        reset_budget(tmp_path / "usage.jsonl")
        refused = client.post("/api/chat?ui_mode=player", json={"text": PHRASE, "client_request_id": "save"})
        created = client.post("/api/snapshots?ui_mode=player", json={"label": "after-refusal"})
        snapshot_id = created.json()["snapshot"]["id"]
        loaded = client.post("/api/snapshots/load?ui_mode=player", json={"snapshot_id": snapshot_id})
    assert refused.status_code == 200
    assert loaded.status_code == 200
    assert storage.load_session()["last_publication"]["visible"] == PRIOR
    assert storage.load_session()["turn_counter"] == 4
    assert any(item.get("log_meta", {}).get("response_class") == OPERATIONAL_REFUSAL for item in storage.load_log())


def test_cross_campaign_refusal_does_not_touch_the_other_store(tmp_path, monkeypatch):
    seed_gate(tmp_path / "alpha", monkeypatch)
    alpha_session = storage.SESSION_PATH.read_bytes()
    seed_gate(tmp_path / "beta", monkeypatch)
    chat_turn(tmp_path / "beta", monkeypatch, PHRASE, request_limit="0")
    assert (tmp_path / "alpha" / "data" / "session.json").read_bytes() == alpha_session


def test_accepted_dialogue_record_is_still_gameplay():
    spoken = 'Gate Guard says, "I do not know anything beyond the warning about a missing patrol."'
    session = {"campaign_run_id": "alpha", "turn_counter": 5, "last_publication": {"visible": PRIOR, "final": True, "dialogue_accepted": True, "campaign_run_id": "alpha"}}
    gm = {"metadata": {"expression_generation": {
        "decision": "adopted", "fallback_used": False,
        "candidate": "I do not know anything beyond the warning about a missing patrol.",
        "delivered_generated": True,
    }}}
    record = note_completed_publication(session, text=spoken, gm=gm)
    assert record["dialogue_accepted"] is True
    assert record["validation_outcome"] == "accepted_expression"
    assert record["visible"] == spoken
    payload = {"ok": True, "gm_output": {"player_facing_text": spoken}, "resolution": {"kind": "question", "metadata": {"authoritative_mutation": False}}}
    assert response_is_operational_refusal(payload) is False


def test_grounded_fallback_record_is_still_gameplay(tmp_path, monkeypatch):
    fallback = 'Gate Guard mutters, "Word is, check the notice board."'
    session = {"campaign_run_id": "alpha", "turn_counter": 5, "conversational_context": {"last_gm_exchange": {}}}
    gm = {"player_facing_text": fallback, "metadata": {"expression_generation": {
        "decision": "rejected", "fallback_used": True, "candidate": "The king paid them.", "delivered_generated": False,
    }}}
    record = note_completed_publication(session, text=fallback, gm=gm)
    assert record["dialogue_accepted"] is False
    assert record["validation_outcome"] == "engine_or_grounded_fallback"
    assert "king" not in record["visible"]
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
    row = record_completed_publication(
        {"gm_output": {"player_facing_text": fallback}},
        source_handler="api_chat",
        publication_context=record,
    )
    assert row["validation_outcome"] == "engine_or_grounded_fallback"
    assert row["final_player_facing_response"] == fallback
    assert response_is_operational_refusal({"resolution": {"kind": "question", "metadata": {}}}) is False


def test_physical_narration_remains_one_expression(monkeypatch):
    from tests.pr_play_79df_executor import ACCEPTED as line
    from tests.pr_play_79df_executor import physical

    acted = physical(monkeypatch, line, narrate=True)
    assert acted["calls"] == 1
    session = {"campaign_run_id": "alpha", "turn_counter": 2, "last_narration": {"adopted": True, "candidate": acted["published"]}}
    record = note_completed_publication(session, text=acted["published"])
    assert record["visible"] == acted["published"]
    assert record["narration_published"] is True
    assert response_is_operational_refusal({"resolution": {"kind": "interact", "metadata": {"publication_contract": "FINAL_ENGINE_RESPONSE"}}}) is False


def test_second_expression_is_not_requested(monkeypatch):
    from tests.pr_play_79df_executor import ACCEPTED as line
    from tests.pr_play_79df_executor import physical

    acted = physical(monkeypatch, line, narrate=True, second_skip=True)
    assert acted["calls"] == 1


def test_http_fallback_is_not_an_operational_refusal(tmp_path, monkeypatch):
    from game.expressive_dialogue import set_expression_transport
    from tests.test_pr_play_62_investigation_quality import setup_session

    setup_session(tmp_path, monkeypatch)
    monkeypatch.delenv("ASHEN_DISABLE_EXPRESSION_GENERATION", raising=False)
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
    session = storage.load_session()
    session["last_publication"] = {
        "owner": "integrated_play.commit_integrated",
        "contract": "FINAL_ENGINE_RESPONSE",
        "final": True,
        "dialogue_accepted": True,
        "dialogue_published": True,
        "visible": PRIOR,
        "turn": 1,
        "campaign_run_id": session.get("campaign_run_id"),
    }
    storage.save_session(session)
    set_expression_transport(lambda _contract: "They were last seen taking the northwest mud track, and the king paid them.")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/chat?ui_mode=player",
                json={"text": "Gate Guard, what does the notice board say about the patrol?", "client_request_id": uuid.uuid4().hex},
            )
    finally:
        set_expression_transport(None)
    assert response.status_code == 200
    visible = response.json()["gm_output"]["player_facing_text"]
    assert "king paid" not in visible.casefold()
    assert storage.load_session()["last_publication"]["visible"] == visible
    assert storage.load_session()["last_publication"]["dialogue_accepted"] is False
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert event["final_player_facing_response"] == visible
    assert event["validation_outcome"] == "engine_or_grounded_fallback"


def test_classifier_does_not_treat_state_stillness_as_operational():
    assert response_is_operational_refusal({
        "resolution": {"kind": "conversational_clarify", "metadata": {"authoritative_mutation": False, "resolver_invoked": False, "processing_outcome": "clarification_required"}}
    }) is False
    assert response_is_operational_refusal({
        "resolution": {"kind": "interpretation_rejected", "metadata": {"authoritative_mutation": False, "resolver_invoked": False, "processing_outcome": "malformed_interpretation"}}
    }) is False
    assert response_is_operational_refusal({
        "resolution": {"kind": "interpretation_rejected", "metadata": {"authoritative_mutation": False, "resolver_invoked": False, "processing_outcome": "input-token ceiling"}}
    }) is True
