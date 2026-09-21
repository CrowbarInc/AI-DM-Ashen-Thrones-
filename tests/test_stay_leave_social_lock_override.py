"""PR-AE: explicit stay/leave/pursuit must override stale social capture."""

from __future__ import annotations

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import default_scene, default_session, default_world
from game.intent_parser import (
    looks_like_explicit_actionable_stay_leave_or_pursuit,
    parse_freeform_to_action,
    recover_actionable_stay_leave_or_pursuit,
)
from game.interaction_context import (
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
    set_social_target,
)
from game.interaction_routing import choose_interaction_route, is_world_action
from game.leads import LeadLifecycle, LeadStatus, create_lead, upsert_lead
from game.narration_state_consistency import apply_stay_leave_narration_agreement_to_gm
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

NOTICE_FACT = "The missing patrol was last seen taking the northwest mud track past the crates."
T7_PURSUIT = "Fine. I'll follow the missing patrol rumor along that northwest mud track."


def _gate_scene() -> dict:
    scene = default_scene("frontier_gate")
    scene["scene"]["discoverable_clues"] = [
        {"id": "notice_patrol_route", "text": NOTICE_FACT},
    ]
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "board"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_route",
        }
    ]
    return scene


def _gate_world() -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "topics": [{"id": "watch_command", "text": "Captain Thoran commands the gate watch tonight."}],
        },
        {
            "id": "guard_captain",
            "name": "Guard Captain",
            "location": "frontier_gate",
            "topics": [{"id": "patrol", "text": NOTICE_FACT}],
        },
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "stew", "text": "Hot stew and rumors for coin."}],
        },
    ]
    return world


def _engaged_session(world: dict, npc_id: str = "guard_captain") -> dict:
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=_gate_scene())
    set_social_target(session, npc_id)
    upsert_lead(
        session,
        create_lead(
            id="notice_patrol_route",
            title=NOTICE_FACT,
            summary=NOTICE_FACT,
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["old_milestone"],
        ),
    )
    return session


def test_t7_pursuit_parses_as_authored_exit_transition():
    parsed = parse_freeform_to_action(T7_PURSUIT, _gate_scene(), session=_engaged_session(_gate_world()))
    assert parsed is not None
    assert parsed.get("type") == "scene_transition"
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) == "old_milestone"


def test_heading_out_after_them_binds_authored_exit():
    parsed = parse_freeform_to_action(
        "Okay. I'm heading out after them along that northwest track.",
        _gate_scene(),
        session=_engaged_session(_gate_world()),
    )
    assert parsed is not None
    assert parsed.get("type") == "scene_transition"
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) == "old_milestone"


def test_stay_plus_question_stays_conversational():
    text = "Alright, I'll stay here a moment and hear you out. When did that patrol go missing?"
    assert looks_like_explicit_actionable_stay_leave_or_pursuit(text) is False
    parsed = parse_freeform_to_action(text, _gate_scene(), session=_engaged_session(_gate_world()))
    assert parsed is None or parsed.get("type") not in {"scene_transition", "travel"}
    assert (parsed or {}).get("metadata", {}).get("parser_lane") != "explicit_stay"
    assert (parsed or {}).get("metadata", {}).get("parser_lane") != "human_adjacent_observe"


def test_northwest_track_pursuit_binds_authored_exit_not_invented_place():
    parsed = parse_freeform_to_action(
        "I'll follow the northwest track.",
        _gate_scene(),
        session=_engaged_session(_gate_world()),
    )
    assert parsed is not None
    assert parsed.get("type") == "scene_transition"
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) == "old_milestone"


def test_stay_is_not_inverted_into_cinderwatch_entry():
    parsed = parse_freeform_to_action(
        "I'll stay at the gate a bit longer instead of entering Cinderwatch.",
        _gate_scene(),
        session=_engaged_session(_gate_world()),
    )
    assert parsed is not None
    assert parsed.get("type") != "scene_transition"
    assert (parsed.get("metadata") or {}).get("parser_lane") == "explicit_stay"
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) in (None, "")


def test_not_leaving_yet_is_stay():
    parsed = parse_freeform_to_action("I'm not leaving yet.", _gate_scene())
    assert parsed is not None
    assert (parsed.get("metadata") or {}).get("intent") == "stay"
    assert parsed.get("type") != "scene_transition"


def test_conversational_patrol_question_is_not_travel():
    text = "What happened to the patrol?"
    assert looks_like_explicit_actionable_stay_leave_or_pursuit(text) is False
    parsed = parse_freeform_to_action(text, _gate_scene(), session=_engaged_session(_gate_world()))
    assert parsed is None or parsed.get("type") not in {"scene_transition", "travel"}


def test_ambiguous_track_noun_is_not_forced_travel():
    text = "the northwest track"
    assert looks_like_explicit_actionable_stay_leave_or_pursuit(text) is False
    parsed = recover_actionable_stay_leave_or_pursuit(text, _gate_scene(), session=_engaged_session(_gate_world()))
    assert parsed is None


def test_follow_person_is_not_stolen_as_unresolved_travel():
    parsed = recover_actionable_stay_leave_or_pursuit(
        "I follow the tattered man.",
        _gate_scene(),
        session=_engaged_session(_gate_world()),
    )
    assert parsed is None


def test_unavailable_destination_is_not_invented():
    parsed = recover_actionable_stay_leave_or_pursuit(
        "I'll go to House Verevin.",
        _gate_scene(),
        session=_engaged_session(_gate_world()),
    )
    assert parsed is not None
    assert parsed.get("type") == "travel"
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) in (None, "")


def test_stone_boar_follow_instructions_still_prefers_named_place():
    scene = _gate_scene()
    scene["scene"]["exits"] = [
        {"label": "Enter the Stone Boar", "target_scene_id": "stone_boar_tavern"},
        {"label": "Follow the missing patrol rumor", "target_scene_id": "old_milestone"},
    ]
    parsed = parse_freeform_to_action(
        "Galinor follows the instructions, entering the Stone Boar.",
        scene,
        session=default_session(),
        world=default_world(),
    )
    assert parsed is not None
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) == "stone_boar_tavern"


def test_ill_follow_is_world_action_and_not_dialogue_route():
    scene = _gate_scene()
    world = _gate_world()
    session = _engaged_session(world)
    assert is_world_action(T7_PURSUIT)
    entry = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=T7_PURSUIT,
    )
    assert entry.get("should_route_social") is False
    assert choose_interaction_route(T7_PURSUIT, scene=scene, session=session, world=world) != "dialogue"


def test_patrol_question_stays_dialogue_while_engaged():
    scene = _gate_scene()
    world = _gate_world()
    session = _engaged_session(world)
    text = "When did they leave?"
    assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"


def test_narration_repairs_pursuit_without_player_movement():
    gm = apply_stay_leave_narration_agreement_to_gm(
        {"player_facing_text": 'Guard Captain mutters, "Word is, the missing patrol was last seen taking the northwest mud track."', "tags": []},
        resolution={
            "kind": "scene_transition",
            "resolved_transition": True,
            "target_scene_id": "old_milestone",
            "metadata": {"parser_lane": "legacy_follow_exit_match"},
        },
        origin_scene_id="frontier_gate",
    )
    low = str((gm or {}).get("player_facing_text") or "").lower()
    assert "leave along the available path" in low
    assert "mutters" not in low


def test_narration_repairs_stay_inverted_into_departure():
    gm = apply_stay_leave_narration_agreement_to_gm(
        {"player_facing_text": "You leave the gate and enter Cinderwatch.", "tags": []},
        resolution={"kind": "observe", "metadata": {"parser_lane": "explicit_stay", "intent": "stay"}},
        origin_scene_id="frontier_gate",
    )
    low = str((gm or {}).get("player_facing_text") or "").lower()
    assert "remain where you are" in low
    assert "enter cinderwatch" not in low


def _seed_engaged_gate_http(tmp_path, monkeypatch, *, npc_id: str = "guard_captain"):
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), _gate_scene())
    world = _gate_world()
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=_gate_scene())
    set_social_target(session, npc_id)
    upsert_lead(
        session,
        create_lead(
            id="notice_patrol_route",
            title=NOTICE_FACT,
            summary=NOTICE_FACT,
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["old_milestone"],
        ),
    )
    storage.save_session(session)


def test_http_pursuit_while_socially_engaged_leaves_the_gate(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response('Guard Captain mutters, "Word is, the missing patrol was last seen taking the northwest mud track."'),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": T7_PURSUIT})
    assert resp.status_code == 200
    data = resp.json()
    res = data.get("resolution") or {}
    assert res.get("kind") == "scene_transition"
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "old_milestone"
    assert data.get("session", {}).get("active_scene_id") == "old_milestone"
    ctx = inspect_interaction_context(data.get("session") or {})
    assert str(ctx.get("active_interaction_target_id") or "") == ""
    low = str((data.get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert any(token in low for token in ("leave", "path", "move", "position"))
    assert "mutters" not in low


def test_http_explicit_leave_overrides_dialogue_lock(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The captain keeps talking as if you had asked another question."))
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I'm leaving. I'll head down the road after the patrol."})
    assert resp.status_code == 200
    data = resp.json()
    res = data.get("resolution") or {}
    assert res.get("kind") in {"scene_transition", "travel"}
    assert res.get("kind") not in {"question", "social_probe"}


def test_http_explicit_stay_does_not_enter_cinderwatch(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("You leave the gate and enter Cinderwatch."))
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I'll remain at the gate."})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("session", {}).get("active_scene_id") == "frontier_gate"
    res = data.get("resolution") or {}
    assert res.get("kind") != "scene_transition"
    low = str((data.get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "enter cinderwatch" not in low


def test_http_conversational_followup_stays_social(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response('Guard Captain says, "They left before dawn."'))
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "What happened to the patrol?"})
    assert resp.status_code == 200
    data = resp.json()
    res = data.get("resolution") or {}
    assert res.get("kind") in {"question", "social_probe"}
    assert data.get("session", {}).get("active_scene_id") == "frontier_gate"


def test_http_ambiguous_track_mention_does_not_travel(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The captain watches the line."))
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "that northwest track"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("session", {}).get("active_scene_id") == "frontier_gate"
    res = data.get("resolution") or {}
    assert res.get("resolved_transition") is not True


def test_http_unavailable_travel_does_not_invent_house_verevin(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("You arrive at House Verevin's rooftop."))
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I'll go to House Verevin."})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("session", {}).get("active_scene_id") == "frontier_gate"
    res = data.get("resolution") or {}
    assert res.get("resolved_transition") is not True
    assert res.get("target_scene_id") not in {"house_verevin", "House Verevin"}
    low = str((data.get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "arrive at house verevin" not in low


def test_http_post_departure_followup_is_not_recaptured_by_gate_captain(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("You take the muddy path away from the gate."))
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": T7_PURSUIT})
        assert first.status_code == 200
        assert first.json().get("session", {}).get("active_scene_id") == "old_milestone"
        second = client.post("/api/chat", json={"text": "I look around this stretch of road."})
    assert second.status_code == 200
    data = second.json()
    assert data.get("session", {}).get("active_scene_id") == "old_milestone"
    ctx = inspect_interaction_context(data.get("session") or {})
    assert str(ctx.get("active_interaction_target_id") or "") == ""
    res = data.get("resolution") or {}
    assert res.get("kind") not in {"question", "social_probe"}
