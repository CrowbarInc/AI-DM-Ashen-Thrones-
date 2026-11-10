"""PR-PLAY-37: deterministic opening recovery after an eligible narration rejection.

No live provider client is constructed. HTTP cases stub ``call_gpt``.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
import game.opening_initialization_recovery as recovery
import game.storage as st
from game.api import app
from game.immutable_valid_response import validate_generated_response
from game.opening_initialization_recovery import (
    apply_opening_initialization_recovery,
    classify_opening_initialization_failure,
)
from game.storage import load_character, load_combat, load_log, load_session, load_world
from tests.helpers.turn_pipeline_http_fixtures import _seed_campaign_start_storage
from tests.test_pr_play_36_opening_rejection import _audit, _captured, _opening_decision
from tests.test_start_campaign_api import CONTRACT_OPENING_GPT_RESPONSE

pytestmark = pytest.mark.integration

UNAUTHORIZED_TRAVEL = "You leave the gate and arrive at the market quarter."
UNAUTHORIZED_LETTER = "The serjeant gives you a sealed letter at the eastern gate."
GATE_FACT = "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate."
CHOKE_FACT = (
    "Refugees, wagons, and foot traffic clog the muddy approach; "
    "guards hold the choke while the crowd presses in."
)
NOTICE_FACT = "A notice board lists new taxes, curfews, and a posted warning about a missing patrol."
FACTS = [GATE_FACT, CHOKE_FACT, NOTICE_FACT]


def _resolution() -> dict[str, Any]:
    return {
        "kind": "scene_opening",
        "action_id": "campaign_start_opening_scene",
        "success": True,
        "world_updates": None,
        "state_changes": {"opening_scene_turn": True, "arrived_at_scene": True},
    }


def _contract() -> dict[str, Any]:
    return {"required_response_type": "scene_opening"}


def _rejected_gm(
    reasons: list[str],
    *,
    rejected_text: str,
    declaration_valid: bool | None = True,
) -> dict[str, Any]:
    audit: dict[str, Any] | None
    if declaration_valid is None:
        audit = None
    else:
        audit = {
            "hard_valid": False,
            "declaration_validation": {"hard_valid": declaration_valid, "violations": []},
        }
    attempt: dict[str, Any] = {"hard_valid": False, "reasons": list(reasons), "text": rejected_text}
    if audit is not None:
        attempt["gm_resolution_decision_audit"] = audit
    return {
        "player_facing_text": "I cannot provide a validated response to that request.",
        "tags": [],
        "opening_curated_facts": list(FACTS),
        "opening_selector_selected_facts": list(FACTS),
        "scene_update": {"invented": True},
        "world_updates": {"inventory_add": ["sealed letter"]},
        "metadata": {
            "narration_provider_calls": 1,
            "hard_validation_attempt_1": attempt,
            "realization_envelope": {
                "narration": rejected_text,
                "declared_claims": [{"text": rejected_text, "source_claim_id": "rc_rejected"}],
            },
            "accepted_response": {
                "provenance": "safe_nonresolution",
                "authorization_source": "safe_nonresolution",
                "immutable": True,
                "text": "I cannot provide a validated response to that request.",
                "rejected_candidate": {"hard_invalid_reasons": list(reasons), "text": rejected_text},
                "hard_validation": {"hard_valid": False, "reasons": []},
            },
        },
    }


def _client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    return TestClient(app)


def _snap() -> dict[str, Any]:
    session = load_session()
    return {
        "campaign_started": bool(session.get("campaign_started")),
        "turn_counter": int(session.get("turn_counter") or 0),
        "time_pressure": int((session.get("clocks") or {}).get("time_pressure") or 0),
        "scene_id": session.get("active_scene_id"),
        "character": load_character(),
        "combat": load_combat(),
        "log_len": len(load_log()),
    }


def test_valid_ai_opening_does_not_call_the_composer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"composer": 0, "provider": 0}
    original = recovery.deterministic_opening_fallback_text_and_meta

    def _composer(gm_output):
        calls["composer"] += 1
        return original(gm_output)

    def _provider(*_args, **_kwargs):
        calls["provider"] += 1
        return dict(CONTRACT_OPENING_GPT_RESPONSE)

    monkeypatch.setattr(recovery, "deterministic_opening_fallback_text_and_meta", _composer)
    monkeypatch.setattr("game.api.call_gpt", _provider)
    with _client(tmp_path, monkeypatch) as client:
        assert client.post("/api/new_campaign").status_code == 200
        response = client.post("/api/start_campaign")
    assert response.status_code == 200, response.text
    body = response.json()
    text = str(body["gm_output"]["player_facing_text"])
    assert "You stand at Cinderwatch's eastern gate" in text
    assert calls["composer"] == 0
    assert calls["provider"] == 1
    logged = (load_log()[0].get("gm_output") or {}).get("metadata") or {}
    debug = logged.get("opening_recovery_debug") or {}
    assert debug.get("opening_source") == "ai"
    assert debug.get("fallback_attempted") is False
    assert debug.get("initialization_outcome") == "started"
    assert load_session().get("campaign_started") is True


def test_captured_opening_passes_without_recovery() -> None:
    _session, _scene, resolution, decision = _opening_decision()
    parsed = _captured()
    audit = _audit(parsed["narration"], parsed["declared_claims"], decision)
    assert audit["hard_valid"] is True
    assert audit["declaration_validation"]["hard_valid"] is True
    verdict = validate_generated_response(
        parsed["narration"],
        decision=decision,
        declared_claims=parsed["declared_claims"],
        player_text="",
        resolution=resolution,
        authored_corpus="",
    )
    assert verdict["hard_valid"] is True
    gm = {
        "player_facing_text": parsed["narration"],
        "opening_curated_facts": list(FACTS),
        "opening_selector_selected_facts": list(FACTS),
        "metadata": {
            "accepted_response": {
                "provenance": "initial_generation",
                "authorization_source": "initial_generation",
                "immutable": True,
                "text": parsed["narration"],
            },
            "hard_validation_attempt_1": {"hard_valid": True, "reasons": [], "text": parsed["narration"]},
        },
    }
    classification = classify_opening_initialization_failure(gm, resolution, _contract())
    assert classification["recoverable"] is False
    assert classification["recovery_eligibility"] == "ai_accepted"
    _installed, record = apply_opening_initialization_recovery(gm, resolution, _contract())
    assert record["fallback_attempted"] is False
    assert gm["player_facing_text"] == parsed["narration"]


def test_semantic_rejection_recovers_without_keeping_rejected_text() -> None:
    gm = _rejected_gm(
        ["unauthorized_resolution_decision_fact"],
        rejected_text=UNAUTHORIZED_TRAVEL,
        declaration_valid=True,
    )
    installed, record = apply_opening_initialization_recovery(copy.deepcopy(gm), _resolution(), _contract())
    assert record["fallback_attempted"] is True
    assert record["fallback_succeeded"] is True
    assert record["opening_source"] == "deterministic_fallback"
    assert record["original_rejection_code"] == "safe_nonresolution"
    assert record["recovery_eligibility"] == "semantic_narration_rejection"
    text = str(installed["player_facing_text"])
    assert UNAUTHORIZED_TRAVEL not in text
    assert "market quarter" not in text.lower()
    assert "sealed letter" not in text.lower()
    assert installed.get("world_updates") is None
    assert installed.get("scene_update") is None
    blob = json.dumps(installed)
    assert UNAUTHORIZED_TRAVEL not in blob
    assert "inventory_add" not in blob


def test_invalid_declarations_discard_the_provider_result() -> None:
    gm = _rejected_gm(
        ["unauthorized_resolution_decision_fact"],
        rejected_text=UNAUTHORIZED_LETTER,
        declaration_valid=False,
    )
    installed, record = apply_opening_initialization_recovery(gm, _resolution(), _contract())
    assert record["recovery_eligibility"] == "invalid_declarations"
    assert record["fallback_attempted"] is False
    assert record["fallback_succeeded"] is False
    assert record["initialization_outcome"] == "rejected"
    assert installed is gm
    assert UNAUTHORIZED_LETTER not in str(installed["player_facing_text"])


def test_mechanical_failure_does_not_invoke_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"n": 0}

    def _composer(*_args, **_kwargs):
        called["n"] += 1
        raise AssertionError("composer must not run")

    monkeypatch.setattr(recovery, "deterministic_opening_fallback_text_and_meta", _composer)
    gm = _rejected_gm(
        ["mechanical_contradiction", "unauthorized_resolution_decision_fact"],
        rejected_text="You fail to hit the guard at the eastern gate.",
    )
    installed, record = apply_opening_initialization_recovery(gm, _resolution(), _contract())
    assert called["n"] == 0
    assert record["fallback_attempted"] is False
    assert record["recovery_eligibility"] == "mechanical_validation_failure"
    assert record["initialization_outcome"] == "rejected"
    assert installed["player_facing_text"].startswith("I cannot provide")


def test_malformed_and_transport_failures_stay_nonrecoverable(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"n": 0}
    monkeypatch.setattr(
        recovery,
        "deterministic_opening_fallback_text_and_meta",
        lambda *_a, **_k: called.__setitem__("n", called["n"] + 1),
    )
    malformed = {
        "player_facing_text": "",
        "tags": ["structured_contract_failure"],
        "opening_curated_facts": list(FACTS),
        "opening_selector_selected_facts": list(FACTS),
        "metadata": {"structured_contract_failure": True, "structured_contract_reason": "malformed_envelope"},
    }
    transport = {
        "player_facing_text": "Provider calls are disabled for this run, so no live narration was generated.",
        "tags": ["provider_calls_disabled"],
        "debug_notes": "call_gpt error: timeout",
        "opening_curated_facts": list(FACTS),
        "opening_selector_selected_facts": list(FACTS),
        "metadata": {},
    }
    for gm, expected in (
        (malformed, "malformed_provider_response"),
        (transport, "provider_transport_failure"),
    ):
        _gm, record = apply_opening_initialization_recovery(gm, _resolution(), _contract())
        assert record["recovery_eligibility"] == expected
        assert record["fallback_attempted"] is False
    assert called["n"] == 0


def test_composer_failure_preserves_both_causes(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("forced")

    monkeypatch.setattr(recovery, "deterministic_opening_fallback_text_and_meta", _boom)
    gm = _rejected_gm(["unauthorized_resolution_decision_fact"], rejected_text=UNAUTHORIZED_TRAVEL)
    installed, record = apply_opening_initialization_recovery(gm, _resolution(), _contract())
    assert record["fallback_attempted"] is True
    assert record["fallback_succeeded"] is False
    assert record["fallback_error"] == "RuntimeError"
    assert record["original_rejection_code"] == "safe_nonresolution"
    assert record["initialization_outcome"] == "failed"
    assert UNAUTHORIZED_TRAVEL not in str(installed.get("player_facing_text"))
    assert installed.get("world_updates") == {"inventory_add": ["sealed letter"]}


def test_fallback_is_deterministic() -> None:
    left_gm = _rejected_gm(["unauthorized_resolution_decision_fact"], rejected_text=UNAUTHORIZED_TRAVEL)
    right_gm = copy.deepcopy(left_gm)
    left, left_record = apply_opening_initialization_recovery(left_gm, _resolution(), _contract())
    right, right_record = apply_opening_initialization_recovery(right_gm, _resolution(), _contract())
    assert left["player_facing_text"] == right["player_facing_text"]
    assert left["metadata"]["opening_recovery_debug"] == right["metadata"]["opening_recovery_debug"]
    assert left_record == right_record
    assert "notice board" in left["player_facing_text"].lower() or "gate" in left["player_facing_text"].lower()


def _http_rejection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any], *, composer=None):
    calls = {"provider": 0}

    def _provider(*_args, **_kwargs):
        calls["provider"] += 1
        return copy.deepcopy(payload)

    monkeypatch.setattr("game.api.call_gpt", _provider)
    if composer is not None:
        monkeypatch.setattr(recovery, "deterministic_opening_fallback_text_and_meta", composer)
    before_character = None
    with _client(tmp_path, monkeypatch) as client:
        assert client.post("/api/new_campaign").status_code == 200
        before = _snap()
        before_character = load_character()
        response = client.post("/api/start_campaign")
    return response, calls, before, before_character


def test_http_semantic_rejection_initializes_from_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        **CONTRACT_OPENING_GPT_RESPONSE,
        "player_facing_text": UNAUTHORIZED_TRAVEL,
    }
    response, calls, before, before_character = _http_rejection(tmp_path, monkeypatch, payload)
    assert response.status_code == 200, response.text
    body = response.json()
    text = str(body["gm_output"]["player_facing_text"])
    assert "market quarter" not in text.lower()
    assert "leave the gate" not in text.lower()
    assert body.get("session", {}).get("campaign_started") is True or load_session().get("campaign_started") is True
    assert calls["provider"] == 1
    session = load_session()
    assert int(session.get("turn_counter") or 0) == 1
    assert int((session.get("clocks") or {}).get("time_pressure") or 0) == before["time_pressure"] + 1
    assert session.get("active_scene_id") == before["scene_id"]
    assert load_character() == before_character
    assert load_log()
    assert load_log()[0].get("resolution", {}).get("kind") == "scene_opening"
    logged = json.dumps(load_log())
    assert UNAUTHORIZED_TRAVEL not in logged
    debug = ((load_log()[0].get("gm_output") or {}).get("metadata") or {}).get("opening_recovery_debug") or {}
    assert debug.get("opening_source") == "deterministic_fallback"
    assert debug.get("fallback_succeeded") is True
    assert debug.get("original_rejection_code") == "safe_nonresolution"
    assert debug.get("provider_requests_consumed") == 1
    assert debug.get("initialization_outcome") == "started"
    evidence = os.environ.get("ASHEN_PR_PLAY_37_EVIDENCE", "").strip()
    if evidence:
        path = Path(evidence)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "provider_request_count": calls["provider"],
                    "status_code": response.status_code,
                    "player_facing_text": text,
                    "opening_recovery_debug": debug,
                    "before": {k: before[k] for k in ("campaign_started", "turn_counter", "time_pressure", "scene_id", "log_len")},
                    "after": {
                        "campaign_started": session.get("campaign_started"),
                        "turn_counter": session.get("turn_counter"),
                        "time_pressure": (session.get("clocks") or {}).get("time_pressure"),
                        "scene_id": session.get("active_scene_id"),
                        "log_len": len(load_log()),
                        "character_unchanged": load_character() == before_character,
                        "combat_hp": (load_combat().get("hp") if isinstance(load_combat(), dict) else None),
                    },
                    "stubbed_provider_narration": payload["player_facing_text"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def test_http_invalid_declaration_discards_provider_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        **CONTRACT_OPENING_GPT_RESPONSE,
        "player_facing_text": UNAUTHORIZED_LETTER,
        "metadata": {
            "realization_envelope": {
                "declared_claims": [
                    {
                        "declaration_id": "dc_bad",
                        "declaration_mode": "realize",
                        "source_claim_id": "rc_not_authorized",
                        "text": UNAUTHORIZED_LETTER,
                        "provenance_requested": "authored_world_fact",
                        "realization_role": "MUST_STATE",
                        "relation_kind": "observation",
                    }
                ],
                "narration": UNAUTHORIZED_LETTER,
            }
        },
    }
    response, calls, before, _character = _http_rejection(tmp_path, monkeypatch, payload)
    assert calls["provider"] == 1
    assert response.status_code == 422
    body = response.json()
    assert body.get("campaign_started") is False
    assert body.get("opening_failure_reason") == "safe_nonresolution"
    assert "opening_recovery_error" not in body
    assert load_session().get("campaign_started") in (False, None)
    assert load_session().get("turn_counter") == before["turn_counter"]
    assert load_log() == []


def test_http_hidden_information_does_not_start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"composer": 0}

    def _composer(*_args, **_kwargs):
        calls["composer"] += 1
        raise AssertionError("composer must not run")

    payload = {
        **CONTRACT_OPENING_GPT_RESPONSE,
        "player_facing_text": "The secret is the patrol was murdered at the eastern gate.",
    }
    response, provider_calls, before, _character = _http_rejection(
        tmp_path, monkeypatch, payload, composer=_composer
    )
    assert calls["composer"] == 0
    assert response.status_code == 422
    body = response.json()
    assert body.get("ok") is False
    assert body.get("campaign_started") is False
    assert body.get("gameplay_committed") is False
    assert "opening_recovery_error" not in body
    assert load_session().get("campaign_started") in (False, None)
    assert int(load_session().get("turn_counter") or 0) == 0
    assert load_log() == []
    assert provider_calls["provider"] == 1
    assert _snap()["scene_id"] == before["scene_id"]


def test_http_composer_failure_does_not_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("forced")

    payload = {
        **CONTRACT_OPENING_GPT_RESPONSE,
        "player_facing_text": UNAUTHORIZED_TRAVEL,
    }
    response, calls, _before, _character = _http_rejection(tmp_path, monkeypatch, payload, composer=_boom)
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("campaign_started") is False
    assert body.get("gameplay_committed") is False
    assert body.get("opening_failure_reason") == "safe_nonresolution"
    assert body.get("opening_recovery_error") == "RuntimeError"
    assert body.get("opening_recovery_class") == "semantic_narration_rejection"
    assert load_session().get("campaign_started") in (False, None)
    assert int(load_session().get("turn_counter") or 0) == 0
    assert load_log() == []
    assert calls["provider"] == 1


def test_repeated_start_does_not_apply_recovery_twice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"provider": 0}

    def _provider(*_args, **_kwargs):
        calls["provider"] += 1
        return {
            **CONTRACT_OPENING_GPT_RESPONSE,
            "player_facing_text": UNAUTHORIZED_TRAVEL,
        }

    monkeypatch.setattr("game.api.call_gpt", _provider)
    with _client(tmp_path, monkeypatch) as client:
        assert client.post("/api/new_campaign").status_code == 200
        first = client.post("/api/start_campaign")
        second = client.post("/api/start_campaign")
    assert first.status_code == 200, first.text
    assert second.status_code == 409
    assert second.json().get("status") == "already_started"
    assert calls["provider"] == 1
    assert len(load_log()) == 1
    assert int(load_session().get("turn_counter") or 0) == 1
    assert load_session().get("campaign_started") is True
