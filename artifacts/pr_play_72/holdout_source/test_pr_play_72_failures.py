"""Adversarial boundaries for natural initiative; no live provider dispatch."""
import copy

import pytest
from game import api, storage
from game.player_interpretation_bridge import normalized_action_from_interpretation
from game.conversational_orchestration import _operation_record
from tests.test_pr_play_72_initiative import campaigns, restore, authority, offline_turns


@pytest.mark.parametrize("fault", ["unavailable", "timeout", "malformed", "hidden_proposal", "invented_target"])
def test_readonly_does_not_need_provider(campaigns, monkeypatch, fault):
    cl = restore(campaigns, "report"); before = authority(); calls = []
    def forbidden(*a, **kw):
        calls.append(fault)
        raise AssertionError("Read-only answer must not call a provider")
    monkeypatch.setattr(api, "call_gpt", forbidden)
    response = cl.post("/api/chat", json={"text": "What have I learned about the patrol?"})
    assert response.status_code == 200
    assert not calls and authority() == before


@pytest.mark.parametrize("record", [None, [], {}, {"communication_mode": "IN_WORLD_ACTION", "interpretation_status": "INVALID"},
    {"communication_mode": "IN_WORLD_ACTION", "interpretation_status": "INTERPRETED", "action_components": [{"operation_class": "INSPECT", "target_ref": "secret"}]},
    {"communication_mode": "IN_WORLD_ACTION", "interpretation_status": "INTERPRETED", "action_components": [{"operation_class": "CREATE_CAMP", "target_ref": "prints"}]}])
def test_invalid_interpretation(campaigns, record):
    restore(campaigns, "survey"); before = authority()
    action, meta = normalized_action_from_interpretation(record, scene=api.load_active_scene(), world=before["world"], session=before["session"], player_text="Examine the tracks.")
    assert action is None and not meta["accepted"] and authority() == before


@pytest.mark.parametrize("branch,target,text", [("report", "prints", "Inspect the footprints."), ("survey", "notice_board", "Read the board."), ("survey", "patrol_warn_watch", "Give the watch my report."), ("report", "patrol_record_survey", "Record my survey.")])
def test_stale_context(campaigns, branch, target, text):
    restore(campaigns, branch); before = authority()
    op = "CUSTOM" if target.startswith("patrol_") else "INSPECT"
    action, meta = normalized_action_from_interpretation(_operation_record(operation=op, target_id=target, player_text=text), scene=api.load_active_scene(), world=before["world"], session=before["session"], player_text=text)
    assert action is None and not meta["accepted"] and authority() == before


@pytest.mark.parametrize("text", ["What have I learned?", "Look at the tracks again."])
def test_persistence_failure_rolls_back(campaigns, monkeypatch, text):
    cl = restore(campaigns, "survey"); before = authority()
    paths = [storage.SESSION_PATH, storage.WORLD_PATH, storage.CHARACTER_PATH, storage.COMBAT_PATH, storage.SESSION_LOG_PATH]
    original = {p: p.read_bytes() for p in paths}
    monkeypatch.setattr(api, "append_log", lambda *a, **kw: (_ for _ in ()).throw(OSError("injected log persistence failure")))
    # TestClient propagates the injected exception; runtime_commit_scope must roll back.
    with pytest.raises(OSError, match="injected log"):
        cl.post("/api/chat", json={"text": text})
    assert {p: p.read_bytes() for p in paths} == original
    assert authority() == before


def test_invalid_http_schema(campaigns):
    cl = restore(campaigns, "report"); before = authority()
    response = cl.post("/api/action", json={"action_type": "exploration", "exploration_action": "invented"})
    assert response.status_code == 422 and authority() == before


def test_unknown_http_fields_fail_closed(campaigns):
    from game.player_http_projection import project_player_response
    restore(campaigns, "survey")
    malicious = {"gm_output": {"player_facing_text": "Safe", "unknown": "SENTINEL_PRIVATE"}, "unknown": "SENTINEL_PRIVATE"}
    # Canonical response projection is tested via its source-specific adapter.
    assert "SENTINEL_PRIVATE" not in str(project_player_response(malicious))
