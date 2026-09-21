"""PR-AN: subject relevance is not answer sufficiency.

Synthetic fixtures use mill-race vocabulary. Frontier Gate / notice-board
cases are calibration regression only.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.interaction_context import inspect as inspect_interaction_context
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.social import (
    _match_interactable_authored_knowledge,
    _next_topic_to_reveal,
    _stored_text_supports_dimension,
    apply_authored_knowledge_realization_to_gm,
    authored_answer_sufficient_for_question,
    authored_topic_relevant_to_question,
    classify_social_question_dimension,
    realize_authored_knowledge_answer,
    resolve_social_action,
    select_best_social_answer_candidate,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "notice_board",
    "tavern_runner",
    "patrol_rumor",
    "frontier_gate",
    "Cinderwatch",
    "stew",
    "guard_captain",
    "Captain Thoran",
    "roster_board",
    "old_milestone",
)
SPAN_PLACE = "The mill span sits on the north road."
SPAN_STATUS = "The mill span is cracked along the third pier."
SPAN_REPAIRER = "Neris recaulked the mill span."
SPAN_TIME = "The mill span was recaulked yesterday."
SPAN_OCCURRENCE = "The mill span was recaulked."
BARGE_PLACE = "The grain barge went to the river crossing."
BARGE_TIME = "The grain barge departed yesterday."
BARGE_EAST = "The grain barge traveled east."
SLUICE_STATE = "The western sluice is shut."
SLUICE_CAUSE = "The western sluice is shut because the millrace cracked."
WARDEN_EXIST = "Wardens walk the cistern rim."
WARDEN_COUNT = "Four wardens walk the cistern rim."
SLATE_CONTENT = "The tide slate warns that the north flume is rising."
HOPPER_REPAIRER = "Oren fixed the grain hopper."
HOPPER_CHIT = "The grain hopper hides a mill-chit under the lid."
CHIT_LEAD_ID = "mill_chit_lead"
SPAN_LEAD_ID = "span_crack_lead"
HIDDEN_FACT = "A sealed flume key names the night buyer."
PATROL_RUMOR = "The runner heard the patrol vanished near muddy footprints northwest of the crates."
NOTICE_FACT = "The missing patrol was last seen taking the northwest mud track past the crates."
STEW_RELATED = "Hot stew and rumors for coin."
T14_TEXT = "I step back to the tavern runner and ask who last checked that board."


def _frontier_notice_scene() -> dict:
    scene = default_scene("frontier_gate")
    inner = scene.setdefault("scene", {})
    inner["discoverable_clues"] = [{"id": "notice_patrol_route", "text": NOTICE_FACT}]
    inner["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "board", "curfew notice", "missing patrol warning"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_route",
        }
    ]
    return scene


def _mill_scene() -> dict:
    return {
        "scene": {
            "id": "mill_race",
            "location": "Mill Race",
            "summary": "A mill span, a tide slate, and a cistern rim.",
            "visible_facts": [
                "The mill span crosses the race above the flume.",
                "A tide slate hangs by the hopper.",
            ],
            "hidden_facts": [HIDDEN_FACT],
            "discoverable_clues": [
                {"id": CHIT_LEAD_ID, "text": HOPPER_CHIT},
                {"id": SPAN_LEAD_ID, "text": SPAN_STATUS},
                {"id": "slate_flume", "text": SLATE_CONTENT},
            ],
            "addressables": [
                {
                    "id": "sluice_keeper",
                    "name": "Sluice Keeper",
                    "scene_id": "mill_race",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["keeper"],
                    "aliases": ["race warden"],
                },
                {
                    "id": "mill_hand",
                    "name": "Mill Hand",
                    "scene_id": "mill_race",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["hand"],
                    "aliases": [],
                },
            ],
            "interactables": [
                {
                    "id": "tide_slate",
                    "label": "Tide slate",
                    "aliases": ["slate", "flume slate"],
                    "type": "investigate",
                    "reveals_clue": "slate_flume",
                }
            ],
            "exits": [{"label": "Follow the mill-chit", "target_scene_id": "flume_dock"}],
            "enemies": [],
            "actions": [],
        }
    }


def _mill_world(*, keeper_topics: list[dict] | None = None, hand_topics: list[dict] | None = None) -> dict:
    return {
        "npcs": [
            {
                "id": "sluice_keeper",
                "name": "Sluice Keeper",
                "location": "mill_race",
                "aliases": ["race warden"],
                "topics": keeper_topics
                if keeper_topics is not None
                else [
                    {"id": "span_place", "text": SPAN_PLACE},
                    {"id": "span_status", "text": SPAN_STATUS, "clue_id": SPAN_LEAD_ID},
                    {"id": "span_repairer", "text": SPAN_REPAIRER},
                    {"id": "span_time", "text": SPAN_TIME},
                ],
            },
            {
                "id": "mill_hand",
                "name": "Mill Hand",
                "location": "mill_race",
                "topics": hand_topics
                if hand_topics is not None
                else [{"id": "span_occurrence", "text": SPAN_OCCURRENCE}],
            },
        ]
    }


def _session_for(world: dict, scene_id: str, scene: dict | None = None) -> dict:
    session = default_session()
    session["active_scene_id"] = scene_id
    rebuild_active_scene_entities(session, world, scene_id, scene_envelope=scene)
    return session


def _ask(world: dict, session: dict, npc_id: str, player_text: str, scene: dict | None = None) -> dict:
    envelope = scene or _mill_scene()
    action = {
        "id": "question",
        "label": player_text,
        "type": "question",
        "prompt": player_text,
        "target_id": npc_id,
    }
    return resolve_social_action(
        envelope,
        session,
        world,
        action,
        raw_player_text=player_text,
        character=default_character(),
        turn_counter=int(session.get("turn_counter") or 1),
    )


def _topic_id(resolution: dict) -> str:
    rec = ((resolution.get("social") or {}).get("topic_revealed") or {}) if isinstance(resolution, dict) else {}
    return str(rec.get("id") or "").strip()


def _topic_text(resolution: dict) -> str:
    rec = ((resolution.get("social") or {}).get("topic_revealed") or {}) if isinstance(resolution, dict) else {}
    return str(rec.get("text") or rec.get("clue_text") or "").strip()


def _realize(world: dict, session: dict, player_text: str, npc_id: str | None, scene: dict | None = None):
    name = None
    if npc_id:
        row = next((n for n in world.get("npcs") or [] if n.get("id") == npc_id), None)
        name = str((row or {}).get("name") or "").strip() or None
    social = {"social_intent_class": "social_exchange", "target_resolved": bool(npc_id)}
    if npc_id:
        social["npc_id"] = npc_id
        social["npc_name"] = name or npc_id.replace("_", " ").title()
    return realize_authored_knowledge_answer(
        session=session,
        scene_id=str(((scene or _mill_scene()).get("scene") or {}).get("id") or "mill_race"),
        player_text=player_text,
        resolution={"kind": "question", "social": social},
        world=world,
        scene=scene or _mill_scene(),
    )


def _seed_mill_http(tmp_path, monkeypatch, *, world: dict | None = None, scene: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    envelope = scene or _mill_scene()
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    w = default_world()
    w["npcs"] = (world or _mill_world())["npcs"]
    storage._save_json(storage.WORLD_PATH, w)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return sid


def _chat(monkeypatch, text: str, gm_text: str):
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _lead_ids(session: dict) -> set[str]:
    reg = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
    return {str(k) for k in reg.keys()} if isinstance(reg, dict) else set()


def test_existing_dimensions_still_classify():
    assert classify_social_question_dimension("Who is the he you're referring to?") == "identity"
    assert classify_social_question_dimension("Where was he seen last?") == "location"
    assert classify_social_question_dimension("What do you mean?") == "clarification"


def test_extended_dimensions_are_not_wh_token_only():
    assert classify_social_question_dimension("Who recaulked the mill span?") == "identity"
    assert classify_social_question_dimension("Do you know the name of the person who recaulked it?") == "identity"
    assert classify_social_question_dimension("When did the grain barge leave?") == "time"
    assert classify_social_question_dimension("Any idea when this went up?") == "time"
    assert classify_social_question_dimension("Where did the grain barge go?") == "location"
    assert classify_social_question_dimension("The barge's destination?") == "location"
    assert classify_social_question_dimension("Why is the western sluice shut?") == "cause"
    assert classify_social_question_dimension("Tell me the reason the sluice is shut.") == "cause"
    assert classify_social_question_dimension("How many wardens walk the cistern?") == "quantity"
    assert classify_social_question_dimension("What condition is the mill span in?") == "status"
    assert classify_social_question_dimension("What is posted on the slate?") == "general"


def test_general_person_positive():
    world = _mill_world(keeper_topics=[{"id": "span_repairer", "text": SPAN_REPAIRER}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Who recaulked the mill span?")
    assert _topic_id(res) == "span_repairer"
    assert "neris" in _topic_text(res).lower()
    realized = _realize(world, session, "Who recaulked the mill span?", "sluice_keeper")
    assert "neris" in str((realized or {}).get("fact_text") or (realized or {}).get("text") or "").lower()


def test_general_person_negative_does_not_invent():
    world = _mill_world(keeper_topics=[{"id": "span_time", "text": SPAN_TIME}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Who recaulked the mill span?")
    assert _topic_id(res) == ""
    assert "neris" not in _topic_text(res).lower()
    realized = _realize(world, session, "Who recaulked the mill span?", "sluice_keeper")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "neris" not in blob
    assert "yesterday" not in blob


def test_general_time_positive():
    world = _mill_world(keeper_topics=[{"id": "barge_time", "text": BARGE_TIME}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "When did the grain barge leave?")
    assert _topic_id(res) == "barge_time"
    assert "yesterday" in _topic_text(res).lower()


def test_general_time_negative_does_not_invent():
    world = _mill_world(keeper_topics=[{"id": "barge_east", "text": BARGE_EAST}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "When did the grain barge leave?")
    assert _topic_id(res) == ""
    realized = _realize(world, session, "When did the grain barge leave?", "sluice_keeper")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "dawn" not in blob
    assert "yesterday" not in blob
    assert "traveled east" not in blob


def test_general_location_positive():
    world = _mill_world(keeper_topics=[{"id": "barge_place", "text": BARGE_PLACE}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Where did the grain barge go?")
    assert _topic_id(res) == "barge_place"
    assert "river crossing" in _topic_text(res).lower()


def test_general_location_negative_does_not_invent():
    world = _mill_world(keeper_topics=[{"id": "barge_time", "text": BARGE_TIME}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Where did the grain barge go?")
    assert _topic_id(res) == ""
    realized = _realize(world, session, "Where did the grain barge go?", "sluice_keeper")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "crossing" not in blob
    assert "yesterday" not in blob


def test_general_cause_positive():
    world = _mill_world(keeper_topics=[{"id": "sluice_cause", "text": SLUICE_CAUSE}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Why is the western sluice shut?")
    assert _topic_id(res) == "sluice_cause"
    assert "because" in _topic_text(res).lower()


def test_general_cause_negative_does_not_invent():
    world = _mill_world(keeper_topics=[{"id": "sluice_state", "text": SLUICE_STATE}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Why is the western sluice shut?")
    assert _topic_id(res) == ""
    realized = _realize(world, session, "Why is the western sluice shut?", "sluice_keeper")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "because" not in blob
    assert "millrace" not in blob


def test_general_quantity_positive():
    world = _mill_world(keeper_topics=[{"id": "warden_count", "text": WARDEN_COUNT}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "How many wardens walk the cistern?")
    assert _topic_id(res) == "warden_count"
    assert "four" in _topic_text(res).lower()


def test_general_quantity_negative_does_not_invent():
    world = _mill_world(keeper_topics=[{"id": "warden_exist", "text": WARDEN_EXIST}])
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "How many wardens walk the cistern?")
    assert _topic_id(res) == ""
    realized = _realize(world, session, "How many wardens walk the cistern?", "sluice_keeper")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "four" not in blob
    assert "three" not in blob


def test_general_same_subject_different_property():
    world = _mill_world()
    session = _session_for(world, "mill_race", _mill_scene())
    place = _ask(world, session, "sluice_keeper", "Where is the mill span?")
    assert _topic_id(place) == "span_place"
    assert "north road" in _topic_text(place).lower()
    status = _ask(world, session, "sluice_keeper", "What condition is the mill span in?")
    assert _topic_id(status) == "span_status"
    assert "cracked" in _topic_text(status).lower()
    who = _ask(world, session, "sluice_keeper", "Who recaulked the mill span?")
    assert _topic_id(who) == "span_repairer"
    assert "neris" in _topic_text(who).lower()
    when = _ask(world, session, "sluice_keeper", "When was the mill span recaulked?")
    assert _topic_id(when) == "span_time"
    assert "yesterday" in _topic_text(when).lower()


def test_general_sufficient_but_unauthorized_does_not_leak():
    world = _mill_world(
        keeper_topics=[{"id": "span_repairer", "text": SPAN_REPAIRER}],
        hand_topics=[{"id": "span_occurrence", "text": SPAN_OCCURRENCE}],
    )
    session = _session_for(world, "mill_race", _mill_scene())
    set_social_target(session, "mill_hand")
    res = _ask(world, session, "mill_hand", "Who recaulked the mill span?")
    assert _topic_id(res) != "span_repairer"
    assert "neris" not in _topic_text(res).lower()
    realized = _realize(world, session, "Who recaulked the mill span?", "mill_hand")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "neris" not in blob


def test_general_right_dimension_wrong_subject_does_not_substitute():
    world = _mill_world(
        keeper_topics=[
            {"id": "span_repairer", "text": SPAN_REPAIRER},
            {"id": "hopper_repairer", "text": HOPPER_REPAIRER},
        ]
    )
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Who recaulked the mill span?")
    assert _topic_id(res) == "span_repairer"
    assert "neris" in _topic_text(res).lower()
    assert "oren" not in _topic_text(res).lower()


def test_general_content_question_still_uses_surface_fact():
    world = _mill_world(keeper_topics=[{"id": "span_place", "text": SPAN_PLACE}])
    session = _session_for(world, "mill_race", _mill_scene())
    realized = _realize(world, session, "What does the tide slate say?", "sluice_keeper")
    blob = str((realized or {}).get("fact_text") or (realized or {}).get("text") or "").lower()
    assert "north flume" in blob
    assert _match_interactable_authored_knowledge(
        "What does the tide slate say?",
        _mill_scene(),
        "general",
    )["text"] == SLATE_CONTENT


def test_general_same_surface_unsupported_actor_question():
    world = _mill_world(keeper_topics=[{"id": "span_place", "text": SPAN_PLACE}])
    session = _session_for(world, "mill_race", _mill_scene())
    q = "Who last checked that slate?"
    assert classify_social_question_dimension(q) == "identity"
    inter = _match_interactable_authored_knowledge(q, _mill_scene(), "identity")
    assert inter is None
    realized = _realize(world, session, q, "sluice_keeper")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "north flume" not in blob
    assert "neris" not in blob


def test_general_nonliteral_name_of_person_paraphrase():
    world = _mill_world(keeper_topics=[{"id": "span_repairer", "text": SPAN_REPAIRER}])
    session = _session_for(world, "mill_race", _mill_scene())
    q = "Do you know the name of the person who recaulked the mill span?"
    assert classify_social_question_dimension(q) == "identity"
    res = _ask(world, session, "sluice_keeper", q)
    assert _topic_id(res) == "span_repairer"
    assert "neris" in _topic_text(res).lower()


def test_general_rejected_insufficient_fact_has_no_consequence():
    world = _mill_world(
        keeper_topics=[
            {"id": "span_status", "text": SPAN_STATUS, "clue_id": SPAN_LEAD_ID},
            {"id": "hopper_chit", "text": HOPPER_CHIT, "clue_id": CHIT_LEAD_ID, "leads_to_scene": "flume_dock"},
        ]
    )
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "Who recaulked the mill span?")
    assert _topic_id(res) == ""
    assert res.get("clue_id") not in {SPAN_LEAD_ID, CHIT_LEAD_ID}
    revealed = ((session.get("npc_runtime") or {}).get("sluice_keeper") or {}).get("revealed_topics") or []
    assert "span_status" not in revealed
    assert "hopper_chit" not in revealed


def test_general_legitimate_consequence_preserved():
    world = _mill_world(
        keeper_topics=[
            {
                "id": "hopper_chit",
                "text": HOPPER_CHIT,
                "clue_id": CHIT_LEAD_ID,
                "leads_to_scene": "flume_dock",
            }
        ]
    )
    session = _session_for(world, "mill_race", _mill_scene())
    res = _ask(world, session, "sluice_keeper", "What is hidden in the grain hopper?")
    assert _topic_id(res) == "hopper_chit"
    assert res.get("clue_id") == CHIT_LEAD_ID
    assert HOPPER_CHIT in (res.get("discovered_clues") or [])


def test_general_partial_compound_does_not_invent_missing_time():
    world = _mill_world(keeper_topics=[{"id": "span_repairer", "text": SPAN_REPAIRER}])
    session = _session_for(world, "mill_race", _mill_scene())
    q = "Who recaulked the mill span and when?"
    res = _ask(world, session, "sluice_keeper", q)
    assert _topic_id(res) == "span_repairer"
    assert "neris" in _topic_text(res).lower()
    assert "yesterday" not in _topic_text(res).lower()


def test_general_grounded_absence_with_related_knowledge():
    world = _mill_world(keeper_topics=[{"id": "span_place", "text": SPAN_PLACE}, {"id": "span_status", "text": SPAN_STATUS}])
    session = _session_for(world, "mill_race", _mill_scene())
    q = "Who recaulked the mill span?"
    assert authored_topic_relevant_to_question(q, {"id": "span_place", "text": SPAN_PLACE})
    assert not authored_answer_sufficient_for_question(q, {"id": "span_place", "text": SPAN_PLACE})
    res = _ask(world, session, "sluice_keeper", q)
    assert _topic_id(res) == ""
    realized = _realize(world, session, q, "sluice_keeper")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "north road" not in blob
    assert "cracked" not in blob
    assert "neris" not in blob


def test_general_content_and_actor_on_same_surface_are_distinct():
    world = _mill_world(keeper_topics=[{"id": "span_place", "text": SPAN_PLACE}])
    session = _session_for(world, "mill_race", _mill_scene())
    content = _realize(world, session, "What does the tide slate say?", "sluice_keeper")
    actor = _realize(world, session, "Who last checked that slate?", "sluice_keeper")
    assert "north flume" in str((content or {}).get("fact_text") or (content or {}).get("text") or "").lower()
    assert actor is None or "north flume" not in str(actor.get("fact_text") or actor.get("text") or "").lower()


def test_communication_detection_does_not_treat_subject_overlap_as_identity():
    session = default_session()
    gm = apply_authored_knowledge_realization_to_gm(
        {"player_facing_text": 'Sluice Keeper says, "The mill span was recaulked yesterday."', "tags": []},
        player_text="Who recaulked the mill span?",
        resolution={
            "kind": "question",
            "social": {"npc_id": "sluice_keeper", "npc_name": "Sluice Keeper", "topic_revealed": None},
        },
        session=session,
        world=_mill_world(keeper_topics=[{"id": "span_time", "text": SPAN_TIME}]),
        scene=_mill_scene(),
        scene_id="mill_race",
    )
    text = str(gm.get("player_facing_text") or "").lower()
    assert "neris" not in text


def test_occurrence_last_answer_is_not_sufficient_for_identity():
    session = default_session()
    sid = "mill_race"
    rebuild_active_scene_entities(session, _mill_world(), sid, scene_envelope=_mill_scene())
    from game.storage import get_scene_runtime

    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {
        "topic:span": {
            "last_answer": SPAN_TIME,
            "speaker_targets": {"sluice_keeper": {"repeat_count": 1, "last_turn": 1}},
        }
    }
    rt["topic_pressure_current"] = {"topic_key": "topic:span", "speaker_key": "sluice_keeper"}
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id=sid,
        npc_id="sluice_keeper",
        topic_key="topic:span",
        player_text="Who recaulked the mill span?",
        resolution={"social": {"npc_id": "sluice_keeper", "npc_name": "Sluice Keeper"}},
    )
    assert cand["answer_kind"] == "refusal"


def test_general_http_person_positive(tmp_path, monkeypatch):
    _seed_mill_http(tmp_path, monkeypatch, world=_mill_world(keeper_topics=[{"id": "span_repairer", "text": SPAN_REPAIRER}]))
    data = _chat(
        monkeypatch,
        'I turn to the Sluice Keeper. "Who recaulked the mill span?"',
        'Sluice Keeper shakes their head. "I don\'t know."',
    )
    text = _facing(data).lower()
    assert "neris" in text
    assert "i don't know" not in text


def test_general_http_insufficient_related_fact_is_absent(tmp_path, monkeypatch):
    _seed_mill_http(tmp_path, monkeypatch, world=_mill_world(keeper_topics=[{"id": "span_place", "text": SPAN_PLACE}]))
    data = _chat(
        monkeypatch,
        'I turn to the Sluice Keeper. "Who recaulked the mill span?"',
        'Sluice Keeper mutters, "Word is, the mill span sits on the north road."',
    )
    text = _facing(data).lower()
    assert "neris" not in text
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") == "sluice_keeper"


def test_general_http_rejected_consequence_does_not_land(tmp_path, monkeypatch):
    world = _mill_world(
        keeper_topics=[
            {"id": "span_status", "text": SPAN_STATUS, "clue_id": SPAN_LEAD_ID},
            {"id": "hopper_chit", "text": HOPPER_CHIT, "clue_id": CHIT_LEAD_ID, "leads_to_scene": "flume_dock"},
        ]
    )
    _seed_mill_http(tmp_path, monkeypatch, world=world)
    data = _chat(
        monkeypatch,
        'I turn to the Sluice Keeper. "Who recaulked the mill span?"',
        'Sluice Keeper mutters, "Word is, the mill span is cracked along the third pier."',
    )
    leads = _lead_ids(data.get("session") or {})
    assert SPAN_LEAD_ID not in leads
    assert CHIT_LEAD_ID not in leads


def test_general_http_legitimate_hook_still_lands(tmp_path, monkeypatch):
    world = _mill_world(
        keeper_topics=[
            {"id": "hopper_chit", "text": HOPPER_CHIT, "clue_id": CHIT_LEAD_ID, "leads_to_scene": "flume_dock"}
        ]
    )
    _seed_mill_http(tmp_path, monkeypatch, world=world)
    data = _chat(
        monkeypatch,
        'I turn to the Sluice Keeper. "What is hidden in the grain hopper?"',
        'Sluice Keeper shakes their head. "I don\'t know."',
    )
    text = _facing(data).lower()
    assert "mill-chit" in text or "hopper" in text
    assert CHIT_LEAD_ID in _lead_ids(data.get("session") or {})


def test_calibration_t14_does_not_emit_notice_or_patrol_as_last_reader():
    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "aliases": ["runner", "tavern runner"],
            "topics": [
                {
                    "id": "patrol_rumor",
                    "text": PATROL_RUMOR,
                    "clue_id": "muddy_footprints_northwest",
                }
            ],
        }
    ]
    scene = _frontier_notice_scene()
    session = _session_for(world, "frontier_gate", scene)
    res = resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question_board",
            "label": T14_TEXT,
            "type": "question",
            "prompt": T14_TEXT,
            "target_id": "tavern_runner",
        },
        raw_player_text=T14_TEXT,
        character=default_character(),
        turn_counter=14,
    )
    assert classify_social_question_dimension(T14_TEXT) == "identity"
    assert _topic_id(res) == ""
    assert res.get("clue_id") not in {"muddy_footprints_northwest", "notice_patrol_route"}
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="frontier_gate",
        player_text=T14_TEXT,
        resolution=res,
        world=world,
        scene=scene,
    )
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "missing patrol" not in blob
    assert "northwest mud" not in blob
    assert "last seen" not in blob
    assert PATROL_RUMOR.lower() not in blob
    inter = _match_interactable_authored_knowledge(T14_TEXT, scene, "identity")
    assert inter is None


def test_calibration_board_content_question_still_uses_notice_fact():
    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "stew", "text": STEW_RELATED}],
        }
    ]
    scene = _frontier_notice_scene()
    session = _session_for(world, "frontier_gate", scene)
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="frontier_gate",
        player_text="What is posted on the notice board?",
        resolution={"kind": "question", "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"}},
        world=world,
        scene=scene,
    )
    blob = str((realized or {}).get("fact_text") or (realized or {}).get("text") or "").lower()
    assert "northwest" in blob
    assert "patrol" in blob


def test_calibration_stew_cost_is_quantity_absence_not_price_invention():
    assert classify_social_question_dimension("What does the stew cost?") == "quantity"
    assert authored_answer_sufficient_for_question("What does the stew cost?", {"id": "stew", "text": STEW_RELATED}) is False


def test_anti_overfitting_generic_helpers_have_no_calibration_special_case():
    for fn in (
        authored_answer_sufficient_for_question,
        authored_topic_relevant_to_question,
        classify_social_question_dimension,
        _next_topic_to_reveal,
        _match_interactable_authored_knowledge,
    ):
        src = inspect.getsource(fn)
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in src, f"{fn.__name__} contains calibration term {term!r}"
    social = Path("game/social.py").read_text(encoding="utf-8")
    start = social.find("def authored_answer_sufficient_for_question")
    end = social.find("def npc_social_knowledge_exhausted")
    slice_src = social[start:end]
    for term in CALIBRATION_ENGINE_TERMS:
        assert term not in slice_src, f"sufficiency helpers contain calibration term {term!r}"
    classify_src = inspect.getsource(classify_social_question_dimension)
    support_src = inspect.getsource(_stored_text_supports_dimension)
    for banned in ("who last checked", "notice_board", "tavern_runner", "checked the board"):
        assert banned not in classify_src
        assert banned not in support_src
