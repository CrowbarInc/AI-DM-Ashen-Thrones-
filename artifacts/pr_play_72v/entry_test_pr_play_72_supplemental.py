"""Post-freeze harness correction; frozen product and holdout stay untouched."""
import pytest
from game import api, storage
from tests.test_pr_play_72_initiative import campaigns, restore, authority, offline_turns


@pytest.mark.parametrize("text", ["What have I learned?", "Look at the tracks again."])
def test_http_boundary_handles_persistence_fault(campaigns, monkeypatch, text):
    cl = restore(campaigns, "survey"); before = authority()
    paths = [storage.SESSION_PATH, storage.WORLD_PATH, storage.CHARACTER_PATH, storage.COMBAT_PATH, storage.SESSION_LOG_PATH]
    original = {p: p.read_bytes() for p in paths}
    monkeypatch.setattr(api, "append_log", lambda *a, **kw: (_ for _ in ()).throw(OSError("injected log persistence failure")))
    response = cl.post("/api/chat", json={"text": text})
    assert response.status_code == 500
    assert "injected" not in response.text
    assert {p: p.read_bytes() for p in paths} == original and authority() == before


def test_reinspection_may_authoritatively_add_nothing(campaigns):
    cl = restore(campaigns, "report")
    world_before = storage.load_world()
    response = cl.post("/api/chat", json={"text": "Please examine the notice board again."})
    resolution = storage.load_log()[-1]["resolution"]
    assert response.status_code == 200
    assert resolution["action_id"] == "notice_board"
    assert resolution["kind"] == "already_searched" and resolution["success"] is False
    # An attempted investigation can advance normal simulation time; it cannot
    # duplicate discoveries or one-time branch effects.
    assert storage.load_world()["world_state"]["flags"] == world_before["world_state"]["flags"]


def test_explicit_npc_interaction_resolves(campaigns):
    cl = restore(campaigns, "report")
    response = cl.post("/api/chat", json={"text": "I ask the Gate Serjeant about the patrol route."})
    resolution = storage.load_log()[-1]["resolution"]
    assert response.status_code == 200
    assert resolution.get("kind") not in {"conversational_clarify", "conversational_decline"}
    assert (resolution.get("state_changes") or {}).get("npc_id") == "gate_serjeant" or (resolution.get("metadata") or {}).get("npc_id") == "gate_serjeant"
    fact = resolution["social"]["topic_revealed"]["text"]
    assert fact.casefold() in response.json()["gm_output"]["player_facing_text"].casefold()
