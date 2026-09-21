"""PR-AF: arrival at old_milestone must produce a usable authored destination."""

from __future__ import annotations

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import default_scene, default_session, default_world
from game.diegetic_fallback_narration import (
    render_observe_perception_fallback_line,
    render_travel_arrival_fallback_line,
)
from game.exploration import process_investigation_discovery, resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.interaction_context import (
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    set_social_target,
)
from game.leads import LeadLifecycle, LeadStatus, create_lead, upsert_lead
from game.narration_state_consistency import (
    apply_destination_arrival_realization_to_gm,
    apply_stay_leave_narration_agreement_to_gm,
    scene_has_usable_destination_content,
)
from game.scene_actions import normalize_scene_action
from game.validation import validate_scene
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

NOTICE_FACT = "The missing patrol was last seen taking the northwest mud track past the crates."
MILESTONE_CLUE = (
    "Faint overlapping prints mark the mud around the old milestone, "
    "but their number, origin, and direction stay unclear."
)
T7_PURSUIT = "Fine. I'll follow the missing patrol rumor along that northwest mud track."
STUB_PHRASE = "blank scene awaiting definition"
INVENTED_FATE = (
    "the patrol is dead",
    "the patrol was killed",
    "bodies of the patrol",
    "scavenger bandit",
    "house verevin",
)


def _milestone_scene() -> dict:
    return default_scene("old_milestone")


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


def _world() -> dict:
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


def _engaged_gate_session(world: dict) -> dict:
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=_gate_scene())
    set_social_target(session, "guard_captain")
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


def _seed_engaged_gate_http(tmp_path, monkeypatch):
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), _gate_scene())
    storage._save_json(storage.scene_path("old_milestone"), _milestone_scene())
    world = _world()
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=_gate_scene())
    set_social_target(session, "guard_captain")
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


def _assert_no_stub(text: str) -> None:
    assert STUB_PHRASE not in text.lower()


def _assert_no_invented_fate(text: str) -> None:
    low = text.lower()
    for phrase in INVENTED_FATE:
        assert phrase not in low


def test_old_milestone_file_is_no_longer_a_stub():
    scene = _milestone_scene()["scene"]
    assert scene["id"] == "old_milestone"
    assert scene["location"] == "Old Milestone"
    assert STUB_PHRASE not in str(scene.get("summary") or "").lower()
    assert scene.get("visible_facts")
    assert scene.get("interactables")
    assert scene.get("discoverable_clues")
    assert any(
        (ex.get("target_scene_id") or ex.get("targetSceneId")) == "frontier_gate"
        for ex in (scene.get("exits") or [])
        if isinstance(ex, dict)
    )
    validate_scene(_milestone_scene(), "old_milestone", {"old_milestone", "frontier_gate", "market_quarter"})
    assert scene_has_usable_destination_content(_milestone_scene()) is True


def test_pursuit_still_binds_old_milestone():
    parsed = parse_freeform_to_action(T7_PURSUIT, _gate_scene(), session=_engaged_gate_session(_world()))
    assert parsed is not None
    assert parsed.get("type") == "scene_transition"
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) == "old_milestone"


def test_look_around_is_observe_at_old_milestone():
    parsed = parse_freeform_to_action("I look around.", _milestone_scene())
    assert parsed is not None
    assert parsed.get("type") == "observe"


def test_examine_milestone_maps_to_interactable():
    parsed = parse_freeform_to_action("I examine the milestone.", _milestone_scene())
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "milestone"


def test_inspect_footprints_maps_to_prints_interactable():
    parsed = parse_freeform_to_action("I inspect the footprints.", _milestone_scene())
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "prints"


def test_observe_fallback_uses_authored_milestone_facts():
    line = render_observe_perception_fallback_line(
        _milestone_scene(),
        seed_key="praf|look",
        player_text="I look around.",
    )
    assert line
    _assert_no_stub(line)
    low = line.lower()
    assert "milestone" in low or "mud" in low or "track" in low or "prints" in low
    _assert_no_invented_fate(line)


def test_arrival_fallback_orients_without_stub():
    line = render_travel_arrival_fallback_line(_milestone_scene(), seed_key="praf|arrive")
    assert line
    _assert_no_stub(line)
    low = line.lower()
    assert "milestone" in low or "mud track" in low or "old milestone" in low
    _assert_no_invented_fate(line)


def test_stub_placeholder_is_replaced_when_destination_is_defined():
    gm = apply_destination_arrival_realization_to_gm(
        {"player_facing_text": "In Old Milestone, a blank scene awaiting definition", "tags": []},
        resolution={"kind": "observe"},
        scene=_milestone_scene(),
        player_text="I look around.",
    )
    text = str((gm or {}).get("player_facing_text") or "")
    _assert_no_stub(text)
    assert "milestone" in text.lower() or "mud" in text.lower() or "track" in text.lower()
    assert "destination_arrival_realization" in ((gm or {}).get("tags") or [])


def test_stub_placeholder_is_not_invented_when_scene_is_still_a_stub():
    stub = default_scene("wild_moors")
    gm = apply_destination_arrival_realization_to_gm(
        {"player_facing_text": "In Unnamed Scene, a blank scene awaiting definition", "tags": []},
        resolution={"kind": "observe"},
        scene=stub,
        player_text="I look around.",
    )
    assert STUB_PHRASE in str((gm or {}).get("player_facing_text") or "").lower()


def test_prae_stock_movement_is_not_rewritten_by_destination_hook():
    stock = "You act on that decision and leave along the available path."
    gm = apply_destination_arrival_realization_to_gm(
        {"player_facing_text": stock, "tags": []},
        resolution={"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "old_milestone"},
        scene=_milestone_scene(),
        player_text=T7_PURSUIT,
    )
    assert str((gm or {}).get("player_facing_text") or "") == stock


def test_anti_reset_stock_observe_is_replaced_at_defined_destination():
    gm = apply_destination_arrival_realization_to_gm(
        {
            "player_facing_text": "Nothing new locks in yet; you keep the scene's weight without stepping backward.",
            "tags": [],
        },
        resolution={"kind": "observe"},
        scene=_milestone_scene(),
        player_text="I look around.",
    )
    text = str((gm or {}).get("player_facing_text") or "")
    _assert_no_stub(text)
    assert "nothing new locks in yet" not in text.lower()
    assert any(token in text.lower() for token in ("milestone", "mud", "track", "prints", "scrub"))


def test_investigate_milestone_discovers_authored_prints_clue():
    action = normalize_scene_action(
        {
            "id": "inv-milestone",
            "label": "Examine the milestone",
            "type": "investigate",
            "prompt": "I examine the milestone.",
            "target_id": "milestone",
        }
    )
    resolution = resolve_exploration_action(
        _milestone_scene(),
        {},
        {},
        action,
        raw_player_text="I examine the milestone.",
        list_scene_ids=lambda: ["old_milestone", "frontier_gate"],
    )
    assert resolution["kind"] == "discover_clue"
    assert resolution["clue_id"] == "milestone_mud_prints"
    assert resolution["clue_text"] == MILESTONE_CLUE
    _assert_no_invented_fate(str(resolution.get("clue_text") or ""))


def test_generic_patrol_search_reveals_only_authored_uncertainty():
    session = default_session()
    session["active_scene_id"] = "old_milestone"
    revealed = process_investigation_discovery(_milestone_scene(), session, list_scene_ids=lambda: ["old_milestone"])
    assert revealed
    texts = [str(rec.get("text") or "") for rec in revealed if isinstance(rec, dict)]
    assert any("prints" in t.lower() for t in texts)
    for text in texts:
        _assert_no_invented_fate(text)
        assert "dead" not in text.lower()
        assert "alive" not in text.lower()


def test_return_exit_resolves_to_frontier_gate():
    parsed = parse_freeform_to_action(
        "I'll return to Cinderwatch Gate.",
        _milestone_scene(),
    )
    assert parsed is not None
    assert parsed.get("type") in {"scene_transition", "travel"}
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) == "frontier_gate"
    action = normalize_scene_action(parsed)
    resolution = resolve_exploration_action(
        _milestone_scene(),
        {},
        {},
        action,
        raw_player_text="I'll return to Cinderwatch Gate.",
        list_scene_ids=lambda: ["old_milestone", "frontier_gate"],
    )
    assert resolution.get("resolved_transition") is True
    assert resolution.get("target_scene_id") == "frontier_gate"


def test_house_verevin_is_not_invented_from_old_milestone():
    parsed = parse_freeform_to_action("I'll go to House Verevin.", _milestone_scene())
    target = (parsed or {}).get("target_scene_id") or (parsed or {}).get("targetSceneId")
    assert target not in {"house_verevin", "House Verevin"}


def test_stay_leave_agreement_still_repairs_pursuit_without_movement():
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


def test_http_pursuit_arrives_at_defined_old_milestone(tmp_path, monkeypatch):
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
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    _assert_no_stub(text)
    _assert_no_invented_fate(text)


def _seed_at_old_milestone_http(tmp_path, monkeypatch):
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), _gate_scene())
    storage._save_json(storage.scene_path("old_milestone"), _milestone_scene())
    world = _world()
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session["active_scene_id"] = "old_milestone"
    session["visited_scene_ids"] = ["frontier_gate", "old_milestone"]
    rebuild_active_scene_entities(session, world, "old_milestone", scene_envelope=_milestone_scene())
    storage.save_session(session)


def test_http_observe_after_arrival_uses_authored_scene(tmp_path, monkeypatch):
    _seed_at_old_milestone_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("In Old Milestone, a blank scene awaiting definition"),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I look around."})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("session", {}).get("active_scene_id") == "old_milestone"
    res = data.get("resolution") or {}
    assert res.get("kind") not in {"question", "social_probe"}
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    _assert_no_stub(text)
    low = text.lower()
    assert any(token in low for token in ("milestone", "mud", "track", "prints", "scrub")), (
        f"observe text was {text!r} kind={res.get('kind')!r}"
    )
    _assert_no_invented_fate(text)
    ctx = inspect_interaction_context(data.get("session") or {})
    assert str(ctx.get("active_interaction_target_id") or "") == ""


def test_http_examine_milestone_discovers_authored_clue(tmp_path, monkeypatch):
    _seed_at_old_milestone_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("A blank scene awaiting definition, and the patrol is dead."),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I examine the milestone."})
    assert resp.status_code == 200
    data = resp.json()
    res = data.get("resolution") or {}
    assert res.get("kind") in {"discover_clue", "investigate"}
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    _assert_no_stub(text)
    _assert_no_invented_fate(text)
    assert "prints" in text.lower() or "mud" in text.lower() or "milestone" in text.lower()
    assert "the patrol is dead" not in text.lower()


def test_http_patrol_search_does_not_fabricate_fate(tmp_path, monkeypatch):
    _seed_at_old_milestone_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("A blank scene awaiting definition. The missing patrol lies dead behind the milestone."),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I look for signs of the patrol."})
    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    _assert_no_stub(text)
    low = text.lower()
    assert "lies dead" not in low
    assert "the patrol is dead" not in low
    assert any(token in low for token in ("prints", "mud", "unclear", "milestone", "track"))


def test_http_return_path_resolves(tmp_path, monkeypatch):
    _seed_at_old_milestone_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("You remain at the milestone."))
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I'll return to Cinderwatch Gate."})
    assert resp.status_code == 200
    data = resp.json()
    res = data.get("resolution") or {}
    assert data.get("session", {}).get("active_scene_id") == "frontier_gate"
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "frontier_gate"


def test_http_read_notice_still_speaks_authored_patrol_fact(tmp_path, monkeypatch):
    _seed_engaged_gate_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("A gate serjeant manages the crowd and the stew barrel."),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I read the notice board."})
    assert resp.status_code == 200
    text = str((resp.json().get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "northwest" in low
    assert "patrol" in low
    assert resp.json().get("session", {}).get("active_scene_id") == "frontier_gate"
