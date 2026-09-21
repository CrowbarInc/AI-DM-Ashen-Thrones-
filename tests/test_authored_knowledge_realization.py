"""PR-AD: authored-knowledge questions and inspections must reach the player."""

from __future__ import annotations

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import default_session, default_world
from game.intent_parser import parse_freeform_to_action, recover_interactable_content_question
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social import (
    apply_authored_knowledge_realization_to_gm,
    classify_social_question_dimension,
    realize_authored_knowledge_answer,
    select_best_social_answer_candidate,
    _stored_text_supports_dimension,
)
from game.social_exchange_fallback_catalog import apply_social_exchange_retry_fallback_gm


WATCH_FACT = "Captain Thoran commands the gate watch tonight."
NOTICE_FACT = "The missing patrol was last seen taking the northwest mud track past the crates."
HIDDEN_FACT = "An agent of a noble house is watching new arrivals from the square's edge."


def _frontier_scene() -> dict:
    return {
        "scene": {
            "id": "frontier_gate",
            "visible_facts": [
                "The notice board lists taxes, curfew rules, and a warning about a missing patrol.",
            ],
            "discoverable_clues": [
                {"id": "notice_patrol_route", "text": NOTICE_FACT},
            ],
            "hidden_facts": [HIDDEN_FACT],
            "interactables": [
                {
                    "id": "notice_board",
                    "label": "Notice board",
                    "aliases": ["notice", "board", "curfew notice", "missing patrol warning"],
                    "type": "investigate",
                    "reveals_clue": "notice_patrol_route",
                }
            ],
        }
    }


def _frontier_world() -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [
                {
                    "id": "watch_command",
                    "text": WATCH_FACT,
                    "clue_id": "captain_thoran_watch",
                }
            ],
        },
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "stew", "text": "Hot stew and rumors for coin."}],
        },
    ]
    return world


def _session(world: dict) -> dict:
    session = default_session()
    rebuild_active_scene_entities(session, world, "frontier_gate")
    return session


def test_identity_dimension_accepts_unquoted_captain_name():
    assert classify_social_question_dimension("Who commands the watch here?") == "identity"
    assert _stored_text_supports_dimension(WATCH_FACT, "identity") is True


def test_watch_command_candidate_from_present_npc_topic():
    world = _frontier_world()
    session = _session(world)
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="frontier_gate",
        player_text="Who commands the watch here?",
        resolution={"kind": "question", "social": {"social_intent_class": "social_exchange"}},
        world=world,
        scene=_frontier_scene(),
    )
    assert realized is not None
    assert "Thoran" in (realized.get("fact_text") or realized.get("text") or "")
    assert "watch" in (realized.get("fact_text") or realized.get("text") or "").lower()


def test_notice_question_candidate_from_interactable_clue():
    world = _frontier_world()
    session = _session(world)
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="frontier_gate",
        player_text="What is posted on the notice?",
        resolution={"kind": "question", "social": {"social_intent_class": "social_exchange"}},
        world=world,
        scene=_frontier_scene(),
    )
    assert realized is not None
    assert "northwest" in (realized.get("fact_text") or realized.get("text") or "").lower()
    assert "patrol" in (realized.get("fact_text") or realized.get("text") or "").lower()


def test_chapel_relic_does_not_invent_watch_or_notice_answer():
    world = _frontier_world()
    session = _session(world)
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id="frontier_gate",
        npc_id=None,
        topic_key=None,
        player_text="Who stole the relic from the chapel?",
        resolution={"kind": "question", "social": {"social_intent_class": "social_exchange"}},
        world=world,
        scene=_frontier_scene(),
    )
    assert cand.get("answer_kind") == "refusal"
    assert not cand.get("text")


def test_hidden_fact_is_not_selected_as_authored_answer():
    world = _frontier_world()
    session = _session(world)
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id="frontier_gate",
        npc_id=None,
        topic_key=None,
        player_text="Who is the noble agent watching arrivals?",
        resolution={"kind": "question", "social": {"social_intent_class": "social_exchange"}},
        world=world,
        scene=_frontier_scene(),
    )
    text = str(cand.get("text") or "").lower()
    assert "noble house" not in text
    assert HIDDEN_FACT.lower() not in text


def test_neutral_bridge_emits_watch_command_instead_of_murmur():
    world = _frontier_world()
    session = _session(world)
    resolution = {
        "kind": "question",
        "prompt": "Who commands the watch here?",
        "social": {
            "social_intent_class": "social_exchange",
            "reply_speaker_grounding_neutral_bridge": True,
            "npc_id": None,
            "npc_name": None,
            "npc_reply_expected": False,
        },
    }
    gm = apply_authored_knowledge_realization_to_gm(
        {
            "player_facing_text": "The murmur around you never tightens into a single clear voice on that point.",
            "tags": [],
        },
        player_text="Who commands the watch here?",
        resolution=resolution,
        session=session,
        world=world,
        scene=_frontier_scene(),
        scene_id="frontier_gate",
    )
    text = str(gm.get("player_facing_text") or "")
    low = text.lower()
    assert "thoran" in low
    assert "murmur around you never tightens" not in low
    assert "authored_knowledge_realization" in (gm.get("tags") or [])
    assert "emergent_" not in low


def test_retry_fallback_prefers_authored_topic_over_ignorance():
    world = _frontier_world()
    session = _session(world)
    set_social_target(session, "gate_guard")
    resolution = {
        "kind": "question",
        "prompt": "What do you know about the missing patrol posted on the board?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "gate_guard",
            "npc_name": "Gate Guard",
            "target_resolved": True,
            "npc_reply_expected": True,
        },
    }
    gm = apply_social_exchange_retry_fallback_gm(
        {"player_facing_text": 'Gate Guard shakes their head. "I don\'t know."', "tags": []},
        player_text="What do you know about the missing patrol posted on the board?",
        session=session,
        world=world,
        resolution=resolution,
        scene_id="frontier_gate",
    )
    low = str(gm.get("player_facing_text") or "").lower()
    assert "northwest" in low or "patrol" in low
    assert "i don't know" not in low
    assert "authored_knowledge_realization" in (gm.get("tags") or [])


def test_bound_captain_can_realize_watch_command_topic():
    world = _frontier_world()
    session = _session(world)
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="frontier_gate",
        player_text="Who commands the watch here?",
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "guard_captain",
                "npc_name": "Guard Captain",
                "target_resolved": True,
            },
        },
        world=world,
        scene=_frontier_scene(),
    )
    assert realized is not None
    assert "Thoran" in (realized.get("text") or "")
    assert "Guard Captain" in (realized.get("text") or "")


def test_phase3_written_notice_clue_is_spoken():
    gm = apply_authored_knowledge_realization_to_gm(
        {"player_facing_text": "A gate serjeant manages the crowd and the stew barrel.", "tags": []},
        player_text="I read the notice board.",
        resolution={
            "kind": "discover_clue",
            "clue_id": "notice_patrol_route",
            "clue_text": NOTICE_FACT,
            "discovered_clues": [NOTICE_FACT],
        },
        session=default_session(),
        world=_frontier_world(),
        scene=_frontier_scene(),
        scene_id="frontier_gate",
    )
    low = str(gm.get("player_facing_text") or "").lower()
    assert "northwest" in low
    assert "patrol" in low


def test_read_notice_board_parses_as_investigate():
    parsed = parse_freeform_to_action("I read the notice board.", _frontier_scene())
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "notice_board"


def test_step_closer_and_read_notice_parses_as_investigate():
    parsed = parse_freeform_to_action(
        "I step closer and read the notice board carefully.",
        _frontier_scene(),
    )
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "notice_board"


def test_what_is_posted_on_the_notice_recovers_interactable():
    parsed = recover_interactable_content_question("What is posted on the notice?", _frontier_scene())
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "notice_board"


def test_pressed_notice_question_recovers_interactable():
    parsed = recover_interactable_content_question(
        "I press again: what is actually posted on the notice?",
        _frontier_scene(),
    )
    assert parsed is not None
    assert parsed.get("target_id") == "notice_board"


def _seed_frontier_http(tmp_path, monkeypatch):
    from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

    _seed_campaign_start_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), _frontier_scene())
    world = storage.load_world()
    world["npcs"] = _frontier_world()["npcs"]
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    storage.save_session(session)
    return _gm_response


def test_http_watch_command_survives_murmur_fallback(tmp_path, monkeypatch):
    _gm_response = _seed_frontier_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "The murmur around you never tightens into a single clear voice on that point."
            ),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who commands the watch here?"})
    assert resp.status_code == 200
    text = str((resp.json().get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "thoran" in low
    assert "murmur around you never tightens" not in low


def test_http_notice_question_communicates_patrol_fact(tmp_path, monkeypatch):
    _gm_response = _seed_frontier_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response('Gate Guard says, "I do not know enough to answer that."'),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "What is posted on the notice?"})
    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "northwest" in low
    assert "patrol" in low
    assert "i do not know enough" not in low


def test_http_read_notice_board_speaks_written_clue(tmp_path, monkeypatch):
    _gm_response = _seed_frontier_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "A gate serjeant manages the crowd and keeps one eye on the roster board."
            ),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I read the notice board."})
    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert "northwest" in low
    assert "patrol" in low
