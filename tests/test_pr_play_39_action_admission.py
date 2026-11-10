"""PR-PLAY-39: admit a grounded NPC ask and an authored exit without inventing either.

The captured PR-PLAY-38 records are replayed. No provider client is constructed.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game.conversational_orchestration import (
    authored_travel_admission,
    decision_from_interpretation_record,
    unavailable_referent_decision,
)
from game.defaults import default_combat, default_conditions, default_session
from game.ordinary_semantic_ownership import assess_addressee_grounding
from game.player_interpretation_bridge import normalized_action_from_interpretation
from game.social import _next_topic_to_reveal
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "artifacts" / "atgb" / "pr_play_38" / "live" / "20261102T021036Z-943166c96646"
BASELINE = ROOT / "data" / "validation" / "atgb" / "baselines" / "frontier-gate-v1"
RUMOR = "Have you heard any interesting rumors lately?"
PATROL = "I want to follow the trail connected to the missing patrol."
FOOTPRINTS = "I want to investigate the footprints."


def _turn(step: str) -> dict:
    return json.loads((LIVE / "turns" / step / "record.json").read_text(encoding="utf-8"))


def _record(step: str) -> dict:
    return _turn(step)["engine"]["live_interpretation"]["record"]


def _captured_state() -> tuple[dict, dict, dict]:
    folder = LIVE / "turns" / "T2" / "before" / "persistent"
    scene = json.loads((folder / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
    world = json.loads((folder / "world.json").read_text(encoding="utf-8"))
    session = json.loads((folder / "session.json").read_text(encoding="utf-8"))
    return scene, world, session


def _ask(target: str, text: str = RUMOR) -> dict:
    record = copy.deepcopy(_record("T2"))
    record["action_components"][0]["target_ref"] = target
    record["references"]["permitted_entity_ids"] = [target]
    return record


def _bridge(record, text, scene, world, session):
    return normalized_action_from_interpretation(
        record, scene=scene, world=world, player_text=text, session=session,
        known_scene_ids=lambda: ["frontier_gate", "market_quarter", "old_milestone"],
    )


def test_canonical_npc_target_resolves():
    scene, world, session = _captured_state()
    before = copy.deepcopy(world)
    grounding = assess_addressee_grounding(
        RUMOR, scene=scene, world=world, session=session, proposed_target_id="tavern_runner",
    )
    _action, meta = _bridge(_ask("tavern_runner"), RUMOR, scene, world, session)
    assert grounding["operation_eligibility"] == "executable"
    assert grounding["target_id"] == "tavern_runner"
    assert grounding["target_provenance"] == "unique_contextual"
    assert meta["accepted"] is True
    assert meta["target_ref"] == "tavern_runner"
    assert meta.get("reason") != "ungrounded_provider_target"
    assert world == before


def test_display_name_and_alias_resolve_to_the_same_npc():
    scene, world, session = _captured_state()
    for proposed in ("Tavern Runner", "tavern runner", "runner"):
        grounding = assess_addressee_grounding(
            RUMOR, scene=scene, world=world, session=session, proposed_target_id=proposed,
        )
        _action, meta = _bridge(_ask(proposed), RUMOR, scene, world, session)
        assert grounding["target_id"] == "tavern_runner", proposed
        assert meta["accepted"] is True
        assert meta["target_ref"] == "tavern_runner"


def test_unknown_npc_is_not_admitted():
    scene, world, session = _captured_state()
    before = copy.deepcopy(world)
    text = "I ask Captain Voss what he knows about the gate."
    grounding = assess_addressee_grounding(
        text, scene=scene, world=world, session=session, proposed_target_id="captain_voss",
    )
    record = _ask("captain_voss", text)
    record["action_components"][0]["description"] = text
    _action, meta = _bridge(record, text, scene, world, session)
    assert grounding["target_id"] is None
    assert meta["accepted"] is False
    assert meta["reason"] in {"ungrounded_provider_target", "ambiguous_addressee"}
    assert all(npc["id"] != "captain_voss" for npc in world["npcs"])
    assert world == before


def test_ambiguous_npc_reference_requires_clarification():
    scene = {"scene": {"id": "yard", "summary": "Two clerks trade rumors.", "visible_facts": [
        "Clerk Ivo trades rumors by the door.",
        "Clerk Hale trades rumors by the window.",
    ]}}
    world = {"npcs": [
        {"id": "clerk_ivo", "name": "Clerk Ivo", "location": "yard", "aliases": ["clerk"], "topics": []},
        {"id": "clerk_hale", "name": "Clerk Hale", "location": "yard", "aliases": ["clerk"], "topics": []},
    ]}
    grounding = assess_addressee_grounding(
        "Have you heard any interesting rumors lately?",
        scene=scene, world=world, session={}, proposed_target_id="clerk_ivo",
    )
    assert grounding["target_id"] is None
    assert grounding["operation_eligibility"] == "requires_clarification"
    assert {choice["entity_id"] for choice in grounding["choices"]} == {"clerk_ivo", "clerk_hale"}


def test_captured_rumor_request_is_no_longer_ungrounded():
    scene, world, session = _captured_state()
    record = _record("T2")
    assert record["action_components"][0]["target_ref"] == "tavern_runner"
    _action, meta = _bridge(record, RUMOR, scene, world, session)
    assert meta.get("reason") != "ungrounded_provider_target"
    assert meta["accepted"] is True
    assert meta["target_ref"] == "tavern_runner"
    topic = _next_topic_to_reveal(
        next(npc for npc in world["npcs"] if npc["id"] == "tavern_runner"),
        {},
        player_text=RUMOR,
    )
    assert topic["id"] == "patrol_rumor"


def test_canonical_and_natural_patrol_exit_are_selected():
    scene, world, session = _captured_state()
    explicit = authored_travel_admission(
        "I go to Follow the missing patrol rumor.", scene=scene, world=world, session=session,
    )
    natural = decision_from_interpretation_record(
        _record("T4"), player_text=PATROL, scene=scene, world=world, session=session,
    )
    assert explicit.category.value == "EXECUTE"
    assert explicit.proposed_target == "leave_for_follow_the_missing_patrol_rumor"
    assert natural.category.value == "EXECUTE"
    assert natural.proposed_operation == "MOVE"
    assert natural.proposed_target == explicit.proposed_target
    assert "with whom" not in natural.player_facing_text.casefold()
    _action, meta = _bridge(natural.proposed_record, PATROL, scene, world, session)
    assert meta["accepted"] is True
    assert meta["engine_type"] == "scene_transition"


def test_unknown_exit_does_not_create_a_route():
    scene, world, session = _captured_state()
    before = copy.deepcopy(scene)
    decision = authored_travel_admission(
        "I want to follow the trail to the glass observatory.",
        scene=scene, world=world, session=session,
    )
    assert decision.category.value == "DECLINE"
    assert decision.reason == "destination_not_established"
    assert scene == before
    assert len(scene["scene"]["exits"]) == 2


def test_ambiguous_exit_requires_clarification():
    scene, world, session = _captured_state()
    scene = copy.deepcopy(scene)
    scene["scene"]["exits"].append(
        {"label": "Follow the missing patrol road", "target_scene_id": "other_track"}
    )
    decision = authored_travel_admission(PATROL, scene=scene, world=world, session=session)
    assert decision.category.value == "CLARIFY"
    assert decision.reason == "ambiguous_movement_destination"
    labels = " ".join(choice["label"] for choice in decision.context_update["conversational_context"]["pending_clarification"]["choices"])
    assert "missing patrol rumor" in labels.casefold()
    assert "missing patrol road" in labels.casefold()


def test_blocked_exit_does_not_authorize_movement():
    scene, world, session = _captured_state()
    scene = copy.deepcopy(scene)
    for exit_row in scene["scene"]["exits"]:
        if "missing patrol" in exit_row["label"].casefold():
            exit_row["locked"] = True
    decision = authored_travel_admission(PATROL, scene=scene, world=world, session=session)
    assert decision.category.value == "EXECUTE"
    _action, meta = _bridge(decision.proposed_record, PATROL, scene, world, session)
    assert meta["accepted"] is False
    assert meta["reason"] == "route_requires_prerequisite"
    assert "old_milestone" not in json.dumps(meta)


def test_optional_method_is_not_required_for_the_patrol_route():
    scene, world, session = _captured_state()
    decision = decision_from_interpretation_record(
        _record("T4"), player_text=PATROL, scene=scene, world=world, session=session,
    )
    assert decision.category.value == "EXECUTE"
    assert decision.missing_information == []
    assert decision.player_facing_text != _turn("T4")["player_facing_text"]


def test_missing_footprints_are_not_created():
    scene, world, session = _captured_state()
    before = copy.deepcopy((scene, world, session))
    for step, text in (("T3", FOOTPRINTS), ("T5", "I examine the footprints here more carefully.")):
        decision = decision_from_interpretation_record(
            _record(step), player_text=text, scene=scene, world=world, session=session,
        )
        assert decision.category.value == "DECLINE"
        assert decision.reason == "referent_not_in_scene"
        assert "footprints" in decision.player_facing_text.casefold()
        assert "with whom" not in decision.player_facing_text.casefold()
    assert (scene, world, session) == before
    ids = [item.get("id") for item in scene["scene"].get("interactables") or []]
    assert "footprints" not in ids


def test_rejected_decisions_do_not_mutate_state():
    scene, world, session = _captured_state()
    before = copy.deepcopy((scene, world, session))
    unavailable_referent_decision(FOOTPRINTS, _record("T3"), scene=scene, world=world)
    authored_travel_admission(
        "I want to follow the trail to the glass observatory.",
        scene=scene, world=world, session=session,
    )
    assess_addressee_grounding(
        "I ask Captain Voss what he knows.",
        scene=scene, world=world, session=session, proposed_target_id="captain_voss",
    )
    assert (scene, world, session) == before


def test_second_person_without_a_unique_referent_still_clarifies():
    scene = {"scene": {"id": "yard", "summary": "A plain yard.", "visible_facts": []}}
    world = {"npcs": [
        {"id": "porter_hale", "name": "Porter Hale", "location": "yard", "aliases": ["porter"], "description": ""},
        {"id": "clerk_ivo", "name": "Clerk Ivo", "location": "yard", "aliases": ["clerk"], "description": ""},
    ]}
    grounding = assess_addressee_grounding(
        "Can you tell me what happened?",
        scene=scene, world=world, session={}, proposed_target_id="porter_hale",
    )
    assert grounding["target_id"] is None
    assert grounding["operation_eligibility"] == "requires_clarification"


def _install_frontier(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.WORLD_PATH, json.loads((BASELINE / "world.json").read_text(encoding="utf-8")))
    storage._save_json(storage.CAMPAIGN_PATH, json.loads((BASELINE / "campaign.json").read_text(encoding="utf-8")))
    storage._save_json(storage.CHARACTER_PATH, json.loads((BASELINE / "character.json").read_text(encoding="utf-8")))
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    for name in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(
            storage.scene_path(name),
            json.loads((BASELINE / "scenes" / f"{name}.json").read_text(encoding="utf-8")),
        )
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["campaign_started"] = True
    session["turn_counter"] = 1
    clocks = dict(session.get("clocks") or {})
    clocks["time_pressure"] = 1
    session["clocks"] = clocks
    storage.save_session(session)


def _quiet_models(monkeypatch, interpretations: dict):
    calls = {"interpretation": [], "narration": [], "social": [], "exploration": []}

    def interpret(**kwargs):
        text = kwargs.get("player_text") or ""
        calls["interpretation"].append(text)
        for key, outcome in interpretations.items():
            if key in text:
                return outcome
        return {
            "status": "blocked",
            "reason": "stub_unmatched",
            "record": None,
            "player_facing_text": "Unmatched offline stub.",
            "provider_requests": [],
        }

    def narrate(*_args, **_kwargs):
        calls["narration"].append(True)
        return {
            "player_facing_text": "The mud track leaves the gate.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": "moon_gate",
            "new_scene_draft": {"id": "moon_gate", "summary": "Invented by narration."},
            "world_updates": {"npcs": [{"id": "invented_guide", "name": "Invented Guide"}]},
            "suggested_action": None,
            "debug_notes": "offline narration stub",
        }

    import game.exploration as exploration_mod
    import game.social as social_mod

    social = social_mod.resolve_social_action
    exploration = exploration_mod.resolve_exploration_action

    def social_spy(*args, **kwargs):
        calls["social"].append(True)
        return social(*args, **kwargs)

    def exploration_spy(*args, **kwargs):
        calls["exploration"].append(True)
        return exploration(*args, **kwargs)

    monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
    monkeypatch.delenv("ASHEN_DISABLE_PROVIDER_CALLS", raising=False)
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setattr(api, "interpret_production_turn", interpret)
    monkeypatch.setattr(api, "call_gpt", narrate)
    monkeypatch.setattr(social_mod, "resolve_social_action", social_spy)
    monkeypatch.setattr(exploration_mod, "resolve_exploration_action", exploration_spy)
    return calls


def _post(client, text):
    response = client.post("/api/chat?ui_mode=player", json={"text": text})
    assert response.status_code == 200, response.text
    return response.json()


def test_sequence_rumor_interaction_reaches_the_social_resolver(tmp_path, monkeypatch):
    _install_frontier(tmp_path, monkeypatch)
    calls = _quiet_models(monkeypatch, {
        RUMOR: {"status": "accepted", "reason": "captured_record", "record": _record("T2"), "provider_requests": []},
    })
    before = storage.load_session()
    with TestClient(api.app) as client:
        body = _post(client, RUMOR)
    after = storage.load_session()
    text = body["gm_output"]["player_facing_text"]
    assert calls["social"] == [True]
    assert calls["interpretation"] == [RUMOR]
    assert calls["narration"] == []
    assert "muddy footprints" in text.casefold() or "patrol" in text.casefold()
    assert after["active_scene_id"] == "frontier_gate"
    assert "invented_guide" not in json.dumps(storage.load_world())
    assert after["turn_counter"] == before["turn_counter"] + 1
    log = storage.load_log()[-1]
    assert log["resolution"]["social"]["npc_id"] == "tavern_runner"
    assert log["resolution"]["social"]["topic_revealed"]["id"] == "patrol_rumor"


def test_sequence_patrol_travel_reaches_the_movement_resolver(tmp_path, monkeypatch):
    _install_frontier(tmp_path, monkeypatch)
    calls = _quiet_models(monkeypatch, {
        PATROL: {
            "status": "blocked",
            "reason": "clarification_required",
            "record": _record("T4"),
            "player_facing_text": _turn("T4")["player_facing_text"],
            "provider_requests": [],
        },
    })
    before = storage.load_session()
    with TestClient(api.app) as client:
        body = _post(client, PATROL)
    after = storage.load_session()
    assert calls["exploration"] == [True]
    assert calls["interpretation"] == []
    assert after["active_scene_id"] == "old_milestone"
    assert "old_milestone" in after["visited_scene_ids"]
    assert after["clocks"]["time_pressure"] == before["clocks"]["time_pressure"] + 1
    assert body["resolution"]["resolved_transition"] is True
    assert body["resolution"]["target_scene_id"] == "old_milestone"
    assert storage.load_active_scene()["scene"]["id"] == "old_milestone"
    assert "moon_gate" not in json.dumps(storage.load_world())


def test_sequence_unsupported_actions_invent_nothing(tmp_path, monkeypatch):
    _install_frontier(tmp_path, monkeypatch)
    unknown = "I ask Captain Voss what he knows about the gate."
    observatory = "I want to follow the trail to the glass observatory."
    calls = _quiet_models(monkeypatch, {
        unknown: {
            "status": "accepted",
            "reason": "captured_style",
            "record": _ask("captain_voss", unknown),
            "provider_requests": [],
        },
        FOOTPRINTS: {
            "status": "blocked",
            "reason": "clarification_required",
            "record": _record("T3"),
            "player_facing_text": _turn("T3")["player_facing_text"],
            "provider_requests": [],
        },
    })
    before_world = storage.load_world()
    before_session = storage.load_session()
    with TestClient(api.app) as client:
        npc_body = _post(client, unknown)
        route_body = _post(client, observatory)
        print_body = _post(client, FOOTPRINTS)
    after_world = storage.load_world()
    after_session = storage.load_session()
    assert calls["social"] == []
    assert calls["exploration"] == []
    assert "captain_voss" not in json.dumps(after_world)
    assert "glass observatory" in route_body["gm_output"]["player_facing_text"].casefold()
    assert "footprints" in print_body["gm_output"]["player_facing_text"].casefold()
    assert "with whom" not in print_body["gm_output"]["player_facing_text"].casefold()
    assert npc_body["resolution"]["resolved_transition"] is False
    assert after_session["active_scene_id"] == before_session["active_scene_id"] == "frontier_gate"
    assert after_session["clocks"] == before_session["clocks"]
    assert after_session["turn_counter"] == before_session["turn_counter"]
    assert after_world["npcs"] == before_world["npcs"]
    assert [row.get("label") for row in storage.load_active_scene()["scene"]["exits"]] == [
        "Enter Cinderwatch",
        "Follow the missing patrol rumor",
    ]
