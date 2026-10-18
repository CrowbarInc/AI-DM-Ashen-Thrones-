from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from experiments.pr_dq.world import (
    COURTYARD_ID,
    GATE_ID,
    LANTERN_ID,
    LANTERN_TEXT,
    MARA_ID,
    NOTICE_ID,
    NOTICE_TEXT,
    STREET_ID,
    build_disposable_world,
)
from game import storage
from game.api import chat
from game.models import ChatRequest
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage


ROOT = Path(__file__).resolve().parents[1]
DR_RAW = ROOT / "artifacts" / "pr_dr_live_vertical_slice" / "raw_results.json"


def _seed_pr_du_world(tmp_path, monkeypatch) -> None:
    _patch_storage(tmp_path, monkeypatch)
    built = build_disposable_world()
    session = copy.deepcopy(built["session"])
    session.setdefault("scene_state", {})["active_scene_id"] = COURTYARD_ID
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, built["world"])
    storage._save_json(storage.CHARACTER_PATH, built["character"])
    storage._save_json(storage.COMBAT_PATH, built["combat"])
    storage._save_json(storage.CONDITIONS_PATH, {"conditions": []})
    storage._save_json(storage.CAMPAIGN_PATH, {"title": "PR-DU", "premise": "", "tone": "", "gm_guidance": []})
    for scene_id, envelope in built["scenes"].items():
        storage._save_json(storage.scene_path(scene_id), envelope)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _stored_interpretations() -> dict[str, dict[str, Any]]:
    raw = json.loads(DR_RAW.read_text(encoding="utf-8"))
    return {str(row["scenario_id"]): row["parsed"] for row in raw["calls"]}


def _fake_gm_for_resolution(messages):
    blob = json.dumps(messages)
    if LANTERN_ID in blob:
        text = "You take a closer look at the lantern beside the gate. It is soot-streaked and still burning."
    elif MARA_ID in blob or "Sergeant Mara" in blob:
        text = 'Sergeant Mara replies, "The street beyond the gate is the north road."'
    elif GATE_ID in blob or STREET_ID in blob:
        text = "You pass through the courtyard gate onto the waystation street. A notice board stands by the road."
    elif NOTICE_ID in blob:
        text = "The notice board says the north road runs past the waystation."
    else:
        text = "The current state resolves the action without adding anything hidden."
    return {
        "player_facing_text": text,
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "pr_du_stored_narration_stub",
    }


def _generic_gm_for_resolution(_messages):
    return {
        "player_facing_text": "The action resolves.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "pr_dv_generic_narration_stub",
    }


def test_pr_du_single_turn_uses_production_chat_entry_with_stored_interpretation(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    interpretations = _stored_interpretations()
    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", lambda *_args: interpretations["DR01"])
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)

    data = chat(ChatRequest(text="Let me get a better look at the lantern beside the gate.", ui_mode="player"))
    assert data["ok"] is True
    assert data["resolution"]["kind"] in {"investigate", "observe"}
    assert data["resolution"]["action_id"] == LANTERN_ID
    assert "hidden" not in data["gm_output"]["player_facing_text"].lower()
    session = storage.load_session()
    assert session["active_scene_id"] == COURTYARD_ID
    assert session["turn_counter"] == 1
    assert len(storage.load_log()) == 1


def test_pr_du_ooc_interruption_is_non_mutating_through_chat_entry(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    before_session = copy.deepcopy(storage.load_session())
    before_world = copy.deepcopy(storage.load_world())
    monkeypatch.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("provider called")))

    data = chat(ChatRequest(text="OOC: I was only asking about the lantern's appearance.", ui_mode="player"))
    assert data["ok"] is True
    assert data["gm_output"]["tags"] == ["ooc_correction", "non_mutating"]
    assert storage.load_session() == before_session
    assert storage.load_world() == before_world
    assert len(storage.load_log()) == 1
    assert storage.load_log()[0]["resolution"]["metadata"]["resolver_invoked"] is False


def test_pr_du_four_action_sequence_and_ooc_through_production_chat(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    interpretations = _stored_interpretations()
    calls = iter([interpretations["DR01"], interpretations["DR05"], interpretations["DR08"], interpretations["DR10"]])

    def _next_interpretation(*_args):
        return next(calls)

    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", _next_interpretation)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)

    prompts = [
        "Let me get a better look at the lantern beside the gate.",
        "OOC: I was only asking about the lantern's appearance.",
        "Sergeant Mara, is the road on the other side of this gate?",
        "I'll head out through the gate.",
        "Let me read the notice board.",
    ]
    outputs = []
    for prompt in prompts:
        data = chat(ChatRequest(text=prompt, ui_mode="player"))
        assert data["ok"] is True
        outputs.append(data)

    session = storage.load_session()
    assert session["active_scene_id"] == STREET_ID
    assert session["turn_counter"] == 4
    assert (session.get("clocks") or {}).get("time_pressure") == 4
    assert NOTICE_ID in (((session.get("scene_runtime") or {}).get(STREET_ID) or {}).get("resolved_interactables") or [])
    assert len(storage.load_log()) == 5
    assert "soot-streaked" in outputs[0]["gm_output"]["player_facing_text"].lower()
    assert "no gameplay action is executed" in outputs[1]["gm_output"]["player_facing_text"].lower()
    assert "north road" in outputs[2]["gm_output"]["player_facing_text"].lower()
    # The authored discovered clue calls it "the board"; the player just
    # selected the notice board and its canonical action id remains explicit.
    # Require the referent and actual reading result, not a rewritten clue.
    assert outputs[4]["resolution"]["action_id"] == NOTICE_ID
    assert "board" in outputs[4]["gm_output"]["player_facing_text"].lower()
    assert "north road" in outputs[4]["gm_output"]["player_facing_text"].lower()
    assert "waystation" in outputs[4]["gm_output"]["player_facing_text"].lower()


def test_pr_dv_structured_resolution_facts_survive_generic_final_text(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    interpretations = _stored_interpretations()
    calls = iter([interpretations["DR01"], interpretations["DR05"], interpretations["DR08"], interpretations["DR10"]])

    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", lambda *_args: next(calls))
    monkeypatch.setattr("game.api.call_gpt", _generic_gm_for_resolution)

    lantern = chat(ChatRequest(text="Let me get a better look at the lantern beside the gate.", ui_mode="player"))
    mara = chat(ChatRequest(text="Sergeant Mara, is the road on the other side of this gate?", ui_mode="player"))
    gate = chat(ChatRequest(text="I'll head out through the gate.", ui_mode="player"))
    notice = chat(ChatRequest(text="Let me read the notice board.", ui_mode="player"))

    assert lantern["ok"] is True
    assert LANTERN_TEXT.lower() in lantern["gm_output"]["player_facing_text"].lower()
    assert mara["ok"] is True
    assert MARA_ID in mara["resolution"]["social"]["npc_id"]
    assert "north road" in mara["gm_output"]["player_facing_text"].lower()
    assert gate["ok"] is True
    assert gate["resolution"]["target_scene_id"] == STREET_ID
    assert "waystation street" in gate["gm_output"]["player_facing_text"].lower()
    assert notice["ok"] is True
    assert NOTICE_TEXT.lower() in notice["gm_output"]["player_facing_text"].lower()


def test_pr_dv_rejected_and_ambiguous_stored_interpretations_do_not_fallback_execute(tmp_path, monkeypatch):
    _seed_pr_du_world(tmp_path, monkeypatch)
    before = copy.deepcopy(storage.load_session())
    resolver_calls = {"count": 0}

    rejected = {
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "REJECTED",
        "action_components": [{"operation_class": "INSPECT", "target_ref": LANTERN_ID}],
        "references": {"unresolved_references": []},
    }

    def _fake_gm(_messages):
        resolver_calls["count"] += 1
        return _generic_gm_for_resolution(_messages)

    monkeypatch.setattr("game.api._stored_interpretation_for_player_text", lambda *_args: rejected)
    monkeypatch.setattr("game.api.call_gpt", _fake_gm)

    data = chat(ChatRequest(text="Let me get a better look at the lantern beside the gate.", ui_mode="player"))

    assert data["ok"] is True
    assert data["resolution"]["kind"] == "interpretation_rejected"
    assert data["resolution"]["success"] is False
    assert "cannot execute" in data["gm_output"]["player_facing_text"].lower()
    assert resolver_calls["count"] == 0
    after = storage.load_session()
    assert after["active_scene_id"] == before["active_scene_id"]
    assert after["turn_counter"] == before["turn_counter"]
    assert (after.get("clocks") or {}).get("time_pressure") == (before.get("clocks") or {}).get("time_pressure")
