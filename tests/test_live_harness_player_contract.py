"""Deterministic acceptance of the player-mode evaluator lifecycle."""
import json
from pathlib import Path

import pytest

from development.campaigns.product_realization.pr_play_live_harness_player_contract_reconciliation import (
    campaign_lifecycle as lifecycle,
    offline_dry_run,
)
from game import storage

REPORT = Path(offline_dry_run.__file__).parent


def evidence(name):
    return json.loads((REPORT / "evidence" / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture
def creation(tmp_path, monkeypatch):
    capture = evidence("offline_dry_run")
    before, initial = capture["snapshots"][:2]
    paths = {
        "CAMPAIGN_PATH": ("campaign.json", {"id": "bootstrap"}),
        "CHARACTER_PATH": ("character.json", initial["character"]),
        "SESSION_PATH": ("session.json", initial["session"]),
        "WORLD_PATH": ("world.json", initial["world"]),
        "COMBAT_PATH": ("combat.json", initial["combat"]),
        "SESSION_LOG_PATH": ("session_log.jsonl", None),
    }
    for attribute, (name, value) in paths.items():
        path = tmp_path / name
        monkeypatch.setattr(storage, attribute, path)
        path.write_text("" if value is None else json.dumps(value), encoding="utf-8")
    scene = tmp_path / "frontier_gate.json"
    scene.write_text(json.dumps(initial["scene"]), encoding="utf-8")
    monkeypatch.setattr(storage, "scene_path", lambda _scene_id: scene)
    monkeypatch.setattr(storage, "is_known_scene_id", lambda scene_id: scene_id == "frontier_gate")
    return capture["requests"][0], before, initial


@pytest.mark.parametrize("location,key,value,classification", [
    ("record", "http_status", 503, lifecycle.PLAYER_RESPONSE),
    ("record", "response", None, lifecycle.PLAYER_RESPONSE),
    ("body", "ok", False, lifecycle.PLAYER_RESPONSE),
    ("body", "ok", 1, lifecycle.PLAYER_RESPONSE),
    ("body", "status", "blocked", lifecycle.PLAYER_RESPONSE),
    ("body", "ui_mode", "operator", lifecycle.PLAYER_RESPONSE),
    ("body", "campaign_run_id", None, lifecycle.IDENTITY),
    ("body", "campaign_run_id", "another", lifecycle.IDENTITY),
    ("body", "session_id", "another", lifecycle.SESSION),
    ("body", "ruleset_binding", None, lifecycle.RULESET),
    ("body", "ruleset_binding", {"ruleset_id": "pf1e", "ruleset_version": "1", "binding_version": True}, lifecycle.RULESET),
    ("session", "campaign_run_id", "another", lifecycle.IDENTITY),
    ("session", "session_id", "another", lifecycle.SESSION),
    ("session", "ruleset_binding", {"ruleset_id": "unregistered", "ruleset_version": "1", "binding_version": 1}, lifecycle.RULESET),
    ("session", "active_scene_id", "unknown", lifecycle.PERSISTED),
    ("session", "campaign_started", True, lifecycle.PERSISTED),
    ("session", "turn_counter", 2, lifecycle.PERSISTED),
    ("session", "clocks", {}, lifecycle.PERSISTED),
    ("session", "clue_knowledge", {"injected": True}, lifecycle.PERSISTED),
    ("character", "id", "", lifecycle.PERSISTED),
    ("character", "hp", {"current": 1, "max": 8}, lifecycle.PERSISTED),
    ("world", "world_state", {"flags": {"new": True}}, lifecycle.PERSISTED),
], ids=lambda value: str(value) if value is None or isinstance(value, (int, str)) else None)
def test_initialization_stops_before_start(creation, location, key, value, classification):
    record, before, initial = creation
    if location == "record":
        record[key] = value
    elif location == "body":
        if value is None:
            record["response"].pop(key)
        else:
            record["response"][key] = value
    else:
        initial[location][key] = value
        path = getattr(storage, f"{location.upper()}_PATH")
        path.write_text(json.dumps(initial[location]), encoding="utf-8")
    if location == "body" and key == "campaign_run_id" and value == "another":
        record["response"]["session_id"] = value
    assert_rejected(record, before, classification)


def assert_rejected(record, before, classification):
    stages = []

    def request(stage, path):
        stages.append((stage, path))
        return record

    def read():
        return before if not stages else lifecycle.read_persisted()

    with pytest.raises(lifecycle.LifecycleFailure) as exc:
        lifecycle.initialize_campaign(request, read=read)
    assert exc.value.classification == classification
    assert stages == [("creation", "/api/new_campaign")]


@pytest.mark.parametrize("document", ["SESSION", "COMBAT", "CHARACTER", "SESSION_LOG"])
def test_missing_persisted_document_never_bootstraps(creation, document):
    record, before, _ = creation
    path = getattr(storage, f"{document}_PATH")
    path.unlink()
    assert_rejected(record, before, lifecycle.PERSISTED)
    assert not path.exists()


def test_corrupt_combat_envelope_does_not_fall_back(creation):
    record, before, _ = creation
    storage.COMBAT_PATH.write_text('{"version":999,"kind":"combat","payload":null}', encoding="utf-8")
    assert_rejected(record, before, lifecycle.PERSISTED)


def test_existing_runtime_verifier_exception_stops_start(creation, monkeypatch):
    def broken_verifier(*args, **kwargs):
        raise RuntimeError("forced verifier failure")

    record, before, _ = creation
    monkeypatch.setattr(lifecycle.fresh_campaign_verify, "verify_fresh_campaign_runtime", broken_verifier)
    assert_rejected(record, before, lifecycle.PERSISTED)


def test_public_capture_without_developer_fields_is_accepted(creation):
    record, before, _ = creation
    assert set(record["response"]) == {"ok", "status", "ui_mode", "campaign_run_id", "session_id", "ruleset_binding"}
    initial, verified = lifecycle.validate_creation(record, before)
    assert verified == {"ok": True, "violations": []}
    assert initial["session"]["ruleset_binding"] == record["response"]["ruleset_binding"]


@pytest.mark.parametrize("fault,classification", [
    ("start_http_failure", lifecycle.START),
    ("public_campaign_changed", lifecycle.IDENTITY),
    ("persisted_session_changed", lifecycle.SESSION),
    ("public_scene_changed", lifecycle.PERSISTED),
    ("missing_narration", lifecycle.OPENING),
    ("transcript_disagrees", lifecycle.OPENING),
    ("clue_disclosure", lifecycle.OPENING),
    ("resource_change", lifecycle.PERSISTED),
    ("npc_exchange", lifecycle.PERSISTED),
    ("extra_turn", lifecycle.PERSISTED),
])
def test_opening_rejects_invalid_publication_or_consequences(fault, classification):
    capture = evidence("offline_dry_run")
    _, initial, after, _ = capture["snapshots"]
    opening = capture["requests"][1]
    body = opening["response"]
    if fault == "start_http_failure":
        opening["http_status"] = 503
    elif fault == "public_campaign_changed":
        body["campaign_run_id"] = "other"
    elif fault == "persisted_session_changed":
        after["session"]["session_id"] = "other"
    elif fault == "public_scene_changed":
        body["scene"]["scene"]["id"] = "market_quarter"
    elif fault == "missing_narration":
        body["gm_output"]["player_facing_text"] = ""
    elif fault == "transcript_disagrees":
        after["log"][0]["gm_output"]["player_facing_text"] = "other"
    elif fault == "clue_disclosure":
        secret = initial["scene"]["scene"]["discoverable_clues"][0]["text"]
        body["gm_output"]["player_facing_text"] += " " + secret
        after["log"][0]["gm_output"]["player_facing_text"] += " " + secret
    elif fault == "resource_change":
        after["character"]["hp"]["current"] -= 1
    elif fault == "npc_exchange":
        after["session"]["conversational_context"]["delivered_exchanges"][0]["speaker_id"] = "guard_captain"
    elif fault == "extra_turn":
        after["session"]["turn_counter"] += 1
    with pytest.raises(lifecycle.LifecycleFailure) as exc:
        lifecycle.validate_opening(opening, initial, after)
    assert exc.value.classification == classification


@pytest.mark.parametrize("name,outcome,tally", [
    ("offline_dry_run", "published", 1),
    ("provider_disabled_host", "safely_withheld", 0),
])
def test_offline_http_evidence(name, outcome, tally):
    capture = evidence(name)
    assert capture["opening_disposition"] == outcome
    assert [item["stage"] for item in capture["requests"]] == ["creation", "opening"]
    assert capture["readback_matches_persisted"]
    assert capture["storage_isolated"]
    assert capture["player_requests"] == capture["provider_expenditure_usd"] == capture["transport_retries"] == 0
    assert not capture["provider_boundary_attempts"] and not any(capture["provider_ledger"].values())
    assert len(capture["deterministic_fixture_uses"]) == tally
    assert capture["snapshots"][2]["session"]["turn_counter"] == tally


def test_external_transport_guard_fails_before_dispatch():
    attempts = []
    guard = offline_dry_run.make_network_guard(attempts)
    with pytest.raises(offline_dry_run.ProviderBoundaryFailure):
        guard("socket.connect", (None, ("203.0.113.1", 443)))
    assert attempts == ["socket.connect"]


def test_sdk_guard_fails_before_provider_construction(monkeypatch):
    import openai

    attempts = []
    monkeypatch.setattr(openai, "OpenAI", offline_dry_run.make_sdk_guard(attempts))
    with pytest.raises(offline_dry_run.ProviderBoundaryFailure):
        openai.OpenAI(api_key="test-guard")
    assert attempts == ["OpenAI client construction"]
