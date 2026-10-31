"""PR-EF-R4 conversational authorization holdouts.

The player expressions live in tests/fixtures/pr_ef_r4_holdouts.json and were
frozen before this harness was allowed to pass. Do not edit those strings to
chase a result.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.ordinary_semantic_ownership import social_narration_unnecessary
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution
from tests.test_pr_ef_gm_authority import raw_record, seed_scene

HOLDOUTS = json.loads(
    (Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pr_ef_r4_holdouts.json").read_text(encoding="utf-8")
)
CASE_BY_ID = {row["id"]: row for row in HOLDOUTS["cases"]}


def _integrity(session, world):
    clocks = copy.deepcopy((session or {}).get("clocks") or {})
    factions = copy.deepcopy((world or {}).get("factions") or {})
    return {
        "turn_counter": (session or {}).get("turn_counter"),
        "clocks": clocks,
        "factions": factions,
        "scene": (session or {}).get("active_scene_id"),
        "world": copy.deepcopy(world),
    }


def _add_bren(world, *, role="guard", description=""):
    world = storage.load_world()
    npcs = list(world.get("npcs") or [])
    npcs.append(
        {
            "id": "corporal_bren",
            "name": "Corporal Bren",
            "location": "waystation_courtyard",
            "role": role,
            "description": description,
            "disposition": "neutral",
        }
    )
    world["npcs"] = npcs
    storage.save_world(world)


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "0")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "0")
    monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)
    return TestClient(app)


def _wire(monkeypatch, record):
    monkeypatch.setattr(
        "game.live_chat_interpretation.request_interpretation",
        lambda *args, **kwargs: {"ok": True, "sent": False, "text": json.dumps(record)},
    )


def _record_for(case):
    owner = case.get("provider_owner") or "NPC"
    purpose = case.get("provider_purpose") or "QUESTION"
    components = case.get("provider_components")
    if components is None:
        target = case.get("provider_target", case.get("target"))
        if target:
            components = [("ASK", target)]
        else:
            components = []
    return raw_record(owner, purpose, components=components)


def _prepare(case):
    setup = case.get("setup")
    if setup in {"two_npcs", "two_guards", "two_guards_no_height", "pending_ambiguous_ask", "pending_two_candidates", "save_load_ambiguous"}:
        _add_bren(None, role="guard")
    elif setup == "taller_bren":
        _add_bren(None, role="guard", description="Corporal Bren is the taller guard.")
        scene = storage.load_active_scene()
        scene["scene"]["visible_facts"] = list(scene["scene"].get("visible_facts") or []) + [
            "Corporal Bren is the taller of the two guards."
        ]
        storage.save_scene(scene)
    if setup == "active_mara":
        session = storage.load_session()
        session["interaction_context"] = {
            "active_interaction_kind": "social",
            "active_interaction_target_id": "sergeant_mara",
            "interaction_mode": "dialogue",
            "engagement_level": "engaged",
        }
        storage.save_session(session)
    if setup in {"pending_ambiguous_ask", "pending_two_candidates", "save_load_ambiguous"}:
        _store_pending([
            {"entity_id": "sergeant_mara", "label": "Sergeant Mara"},
            {"entity_id": "corporal_bren", "label": "Corporal Bren"},
        ])
    elif setup == "pending_single_candidate":
        _store_pending([{"entity_id": "sergeant_mara", "label": "Sergeant Mara"}])
    elif setup == "executed_ask":
        session = storage.load_session()
        session.setdefault("conversational_context", {})["last_executed_intention"] = {
            "status": "executed",
            "text": "I ask Sergeant Mara about the road.",
            "operation": "ASK",
            "target": "sergeant_mara",
            "scene_id": session.get("active_scene_id"),
        }
        storage.save_session(session)
    if setup == "save_load_ambiguous":
        storage.save_session(copy.deepcopy(storage.load_session()))


def _store_pending(choices):
    session = storage.load_session()
    pending = {
        "kind": "ambiguous_addressee",
        "operation": "ASK",
        "status": "pending",
        "scene_id": session.get("active_scene_id"),
        "original_text": "I ask one of them what happened.",
        "choices": choices,
        "clarification": "Which person do you mean?",
        "target_resolution": "ambiguous",
    }
    context = session.setdefault("conversational_context", {})
    context["pending_clarification"] = pending
    context["pending_intention"] = pending
    storage.save_session(session)


def _post(campaign, monkeypatch, case):
    _prepare(case)
    if case["id"] != "conditional_gate":
        _wire(monkeypatch, _record_for(case))
    before = _integrity(storage.load_session(), storage.load_world())
    data = campaign.post("/api/chat", json={"text": case["player"]}).json()
    after = _integrity(storage.load_session(), storage.load_world())
    return data, before, after


def _mutated(before, after):
    return (
        before["turn_counter"] != after["turn_counter"]
        or before["clocks"] != after["clocks"]
        or before["factions"] != after["factions"]
        or before["world"] != after["world"]
    )


@pytest.mark.parametrize("case_id", [row["id"] for row in HOLDOUTS["cases"]])
def test_frozen_authorization_holdout(campaign, monkeypatch, case_id):
    case = CASE_BY_ID[case_id]
    data, before, after = _post(campaign, monkeypatch, case)
    resolution = data.get("resolution") or {}
    social = resolution.get("social") or {}
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    expect = case["expect"]
    if expect == "execute_npc":
        assert social.get("npc_id") == case["target"]
        assert social.get("target_resolved") is True
        assert after["turn_counter"] == (before["turn_counter"] or 0) + 1
        assert "cannot be identified" not in text.lower()
    elif expect == "clarify_no_mutation":
        assert not social
        assert not _mutated(before, after)
        lowered = text.lower()
        assert (
            "nothing has been attempted" in lowered
            or "has been attempted" in lowered
            or "which person" in lowered
            or "who are you asking" in lowered
            or "yes does not choose" in lowered
            or "what are you trying" in lowered
            or "does not confirm" in lowered
        )
    elif expect == "gm_no_social":
        assert not social
        assert not _mutated(before, after)
        assert "its cause has not been established" not in text.lower()
        assert "says," not in text.lower()
    elif expect == "revise_no_execution":
        assert not social
        assert not _mutated(before, after)
        assert "revised" in text.lower()
        pending = storage.load_session()["conversational_context"]["pending_intention"]
        assert pending["status"] == "pending"
        assert case["player"] in pending.get("revised_text", "")
    elif expect == "cannot_undo":
        assert not social
        assert not _mutated(before, after)
        assert "cannot undo" in text.lower()
    elif expect == "ask_what_to_change":
        assert not social
        assert not _mutated(before, after)
        assert "what do you want to change" in text.lower()
        assert "lantern" not in text.lower()
    elif expect == "withdraw_no_execution":
        assert not social
        assert not _mutated(before, after)
        assert storage.load_session()["conversational_context"].get("pending_intention") in (None, {})
    elif expect == "preserve_both_no_flatten":
        assert not social
        assert after["scene"] == before["scene"]
        assert not _mutated(before, after)
        lowered = text.lower()
        assert "ask" in lowered and "leave" in lowered
    elif expect == "execute_after_reload":
        assert social.get("npc_id") == case["target"]
        assert after["turn_counter"] == (before["turn_counter"] or 0) + 1


def test_determined_nonresolution_skips_narration_and_characterization_does_not():
    determined = {
        "social": {
            "target_resolved": True,
            "npc_speech_authority": "none",
            "reply_plan_kind": "consequential_information_request",
            "topic_revealed": None,
            "incidental_subjective_allowed": False,
        }
    }
    assert social_narration_unnecessary(determined) is True
    uncertainty = {
        "social": {
            "target_resolved": True,
            "npc_speech_authority": "none",
            "reply_plan_kind": "genuine_uncertainty",
            "topic_revealed": None,
            "incidental_subjective_allowed": False,
        }
    }
    assert social_narration_unnecessary(uncertainty) is False
    characterization = {
        "social": {
            "target_resolved": True,
            "npc_speech_authority": "claim_only",
            "reply_plan_kind": "harmless_subjective_response_permitted",
            "incidental_subjective_allowed": True,
        }
    }
    assert social_narration_unnecessary(characterization) is False
    authored = {
        "social": {
            "target_resolved": True,
            "npc_speech_authority": "none",
            "reply_plan_kind": "consequential_information_request",
            "topic_revealed": {"id": "street", "text": "The north road."},
        }
    }
    assert social_narration_unnecessary(authored) is False


def test_third_person_question_is_not_an_active_npc_continuation(campaign, monkeypatch):
    session = storage.load_session()
    session["interaction_context"] = {
        "active_interaction_kind": "social",
        "active_interaction_target_id": "sergeant_mara",
        "interaction_mode": "dialogue",
        "engagement_level": "engaged",
    }
    storage.save_session(session)
    _wire(monkeypatch, raw_record("NPC", "QUESTION", components=[("ASK", "sergeant_mara")]))
    before = _integrity(storage.load_session(), storage.load_world())
    data = campaign.post("/api/chat", json={"text": "What did she mean by the road?"}).json()
    after = _integrity(storage.load_session(), storage.load_world())
    assert not (data.get("resolution") or {}).get("social")
    assert not _mutated(before, after)
    assert "says," not in (data.get("gm_output") or {}).get("player_facing_text", "").lower()


def test_provider_id_does_not_override_unresolved_lexical_addressee(campaign, monkeypatch):
    """Historical failure: 'one of them' executed as Sergeant Mara and ticked factions."""
    _add_bren(None)
    record = raw_record("NPC", "QUESTION", components=[("ASK", "sergeant_mara")])
    _wire(monkeypatch, record)
    before = _integrity(storage.load_session(), storage.load_world())
    data = campaign.post("/api/chat", json={"text": "I ask one of them what happened."}).json()
    after = _integrity(storage.load_session(), storage.load_world())
    assert not (data.get("resolution") or {}).get("social")
    assert not _mutated(before, after)
    text = data["gm_output"]["player_facing_text"].lower()
    assert "sergeant mara says" not in text
    assert "which person" in text or "do you mean" in text
