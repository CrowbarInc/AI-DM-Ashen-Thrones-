"""PR-BG: recognized empty-subject follow-ups keep the current last-answer thread.

Kiln-yard vocabulary is the scenario-independent gate. Frontier Gate strings
are calibration residue only. Synonym paraphrases remain unsupported.
"""
from __future__ import annotations

import inspect

from game.clues import record_discovered_clue
from game.defaults import default_character, default_session
from game.gm import register_topic_probe
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social import (
    empty_subject_continues_current_thread,
    empty_subject_retains_topic_pressure_key,
    realize_authored_knowledge_answer,
    resolve_social_action,
    select_best_social_answer_candidate,
)
from game.storage import get_npc_runtime, get_scene_runtime

CALIBRATION_ENGINE_TERMS = (
    "stew",
    "tavern_runner",
    "notice_board",
    "frontier_gate",
    "missing_patrol",
    "Cinderwatch",
    "Captain Thoran",
    "guard_captain",
    "old_milestone",
    "western cart road",
)
ROAD_FACT = "The kiln spur has been barred since the wagons vanished."
MASH_FACT = "A kettle of mash sits on the porter's brazier."
WATCH_FACT = "Captain Thoran commands the gate watch tonight."
PATROL_FACT = "The missing patrol was last seen taking the northwest mud track past the crates."


def _kiln_scene() -> dict:
    return {
        "scene": {
            "id": "kiln_yard",
            "location": "Kiln Yard",
            "summary": "A brick kiln, a barred spur, and a night porter.",
            "visible_facts": [
                "A brick kiln smokes under a tin roof.",
                "A barred kiln spur sits behind the yard wall.",
            ],
            "hidden_facts": [],
            "discoverable_clues": [{"id": "clue_kiln_spur", "text": ROAD_FACT}],
            "interactables": [
                {
                    "id": "spur_notice",
                    "label": "Spur notice",
                    "aliases": ["notice", "board"],
                    "type": "investigate",
                    "reveals_clue": "clue_kiln_spur",
                }
            ],
            "addressables": [
                {
                    "id": "night_porter",
                    "name": "Night Porter",
                    "scene_id": "kiln_yard",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["porter"],
                },
                {
                    "id": "lamp_clerk",
                    "name": "Lamp Clerk",
                    "scene_id": "kiln_yard",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["clerk"],
                },
            ],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _kiln_world() -> dict:
    return {
        "npcs": [
            {
                "id": "night_porter",
                "name": "Night Porter",
                "location": "kiln_yard",
                "aliases": ["porter"],
                "topics": [
                    {"id": "kiln_spur_closed", "text": ROAD_FACT, "clue_id": "clue_kiln_spur"},
                    {"id": "mash_exists", "text": MASH_FACT},
                ],
            },
            {
                "id": "lamp_clerk",
                "name": "Lamp Clerk",
                "location": "kiln_yard",
                "aliases": ["clerk"],
                "topics": [{"id": "broth_exists", "text": "A kettle of broth sits on the brazier."}],
            },
        ]
    }


def _gate_scene() -> dict:
    return {
        "scene": {
            "id": "frontier_gate",
            "location": "Cinderwatch Gate District",
            "summary": "A muddy gate and a captain.",
            "visible_facts": [
                "A notice board lists a posted warning about a missing patrol.",
            ],
            "hidden_facts": [],
            "discoverable_clues": [{"id": "notice_patrol_route", "text": PATROL_FACT}],
            "interactables": [
                {
                    "id": "notice_board",
                    "label": "Notice board",
                    "aliases": ["board", "notices"],
                    "type": "investigate",
                    "reveals_clue": "notice_patrol_route",
                }
            ],
            "addressables": [
                {
                    "id": "guard_captain",
                    "name": "Guard Captain",
                    "scene_id": "frontier_gate",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["captain"],
                }
            ],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _gate_world() -> dict:
    return {
        "npcs": [
            {
                "id": "guard_captain",
                "name": "Guard Captain",
                "location": "frontier_gate",
                "aliases": ["captain"],
                "topics": [
                    {
                        "id": "watch_command",
                        "text": WATCH_FACT,
                        "clue_id": "captain_thoran_watch",
                    }
                ],
            }
        ]
    }


def _session_with_last_answer(
    *,
    scene: dict,
    world: dict,
    npc_id: str,
    last_answer: str,
    topic_key: str,
    revealed: list[str] | None = None,
    land_clue: dict | None = None,
) -> dict:
    session = default_session()
    sid = scene["scene"]["id"]
    session["active_scene_id"] = sid
    session["turn_counter"] = 2
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    set_social_target(session, npc_id)
    if revealed:
        get_npc_runtime(session, npc_id)["revealed_topics"] = list(revealed)
    if land_clue:
        record_discovered_clue(
            session,
            sid,
            str(land_clue["id"]),
            clue_text=str(land_clue.get("text") or ""),
            presentation_level="explicit",
        )
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {
        topic_key: {
            "last_answer": last_answer,
            "last_turn": 1,
            "repeat_count": 1,
            "speaker_targets": {npc_id: {"repeat_count": 1, "last_turn": 1}},
        }
    }
    rt["topic_pressure_last_topic_key"] = topic_key
    rt["topic_pressure_current"] = {
        "topic_key": topic_key,
        "speaker_key": npc_id,
        "turn": 1,
        "npc_name": npc_id,
    }
    return session


def _ask(session: dict, scene: dict, world: dict, npc_id: str, player: str) -> dict:
    res = resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question",
            "label": player,
            "type": "question",
            "prompt": player,
            "target_id": npc_id,
        },
        raw_player_text=player,
        character=default_character(),
        turn_counter=int(session.get("turn_counter") or 2),
    )
    probe = register_topic_probe(
        session=session,
        scene_envelope=scene,
        player_text=player,
        resolution=res,
    )
    sid = scene["scene"]["id"]
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id=sid,
        npc_id=npc_id,
        topic_key=str(probe.get("topic_key") or ""),
        player_text=player,
        resolution=res,
        world=world,
        scene=scene,
    )
    authored = realize_authored_knowledge_answer(
        session=session,
        scene_id=sid,
        player_text=player,
        resolution=res,
        world=world,
        scene=scene,
    )
    return {
        "resolution": res,
        "probe": probe,
        "candidate": cand,
        "authored": authored,
    }


def test_recovered_missing_patrol_after_watch_still_refuses():
    scene = _gate_scene()
    world = _gate_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="guard_captain",
        last_answer=WATCH_FACT,
        topic_key="topic:captain_charge_guard",
        revealed=["watch_command"],
    )
    out = _ask(session, scene, world, "guard_captain", "What are you doing about the missing patrol?")
    assert out["candidate"]["answer_kind"] == "refusal"
    assert out["authored"] is None
    social = (out["resolution"].get("social") or {})
    assert social.get("topic_revealed") in (None, {})


def test_kiln_why_is_that_reuses_current_last_answer():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
    )
    out = _ask(session, scene, world, "night_porter", "Why is that?")
    assert out["probe"]["topic_key"] == "topic:barred_spur_wagon"
    assert out["candidate"]["answer_kind"] == "structured_fact"
    assert out["candidate"]["source"] == "topic_pressure:last_answer"
    assert "wagons vanished" in str(out["candidate"]["text"] or "").lower()
    assert out["authored"] is not None


def test_kiln_how_come_keeps_clarification_thread():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
    )
    out = _ask(session, scene, world, "night_porter", "How come?")
    assert out["probe"]["topic_key"] == "topic:barred_spur_wagon"
    assert out["candidate"]["answer_kind"] == "structured_fact"
    assert "wagons vanished" in str(out["candidate"]["text"] or "").lower()


def test_who_is_he_after_watch_reuses_identity_last_answer():
    scene = _gate_scene()
    world = _gate_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="guard_captain",
        last_answer=WATCH_FACT,
        topic_key="topic:captain_charge_guard",
        revealed=["watch_command"],
    )
    out = _ask(session, scene, world, "guard_captain", "Who is he?")
    assert out["probe"]["topic_key"] == "topic:captain_charge_guard"
    assert out["candidate"]["answer_kind"] == "structured_fact"
    assert "thoran" in str(out["candidate"]["text"] or "").lower()


def test_who_is_that_after_road_fact_fails_closed_without_inventing_identity():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
    )
    out = _ask(session, scene, world, "night_porter", "Who is that?")
    assert out["probe"]["topic_key"] == "topic:barred_spur_wagon"
    assert out["candidate"]["answer_kind"] == "refusal"
    authored = str((out["authored"] or {}).get("text") or "").lower()
    assert "harun" not in authored
    assert "thoran" not in authored
    assert "mash" not in authored


def test_predicate_reformulation_shut_down_remains_unsupported():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
        land_clue={"id": "clue_kiln_spur", "text": ROAD_FACT},
    )
    out = _ask(session, scene, world, "night_porter", "Why was it shut down?")
    assert out["candidate"]["answer_kind"] == "refusal"
    assert out["authored"] is None


def test_who_ordered_it_fails_closed_without_inventing_an_official():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
    )
    out = _ask(session, scene, world, "night_porter", "Who ordered it?")
    assert out["candidate"]["answer_kind"] == "refusal"
    authored = str((out["authored"] or {}).get("text") or "").lower()
    assert "harun" not in authored
    assert "clerk" not in authored
    assert "serjeant" not in authored


def test_explicit_switch_to_mash_replaces_road_thread():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
    )
    out = _ask(session, scene, world, "night_porter", "What sits on the brazier?")
    social = out["resolution"].get("social") or {}
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else {}
    assert topic.get("id") == "mash_exists"
    assert out["candidate"]["answer_kind"] == "structured_fact"
    assert "mash" in str(out["candidate"]["text"] or "").lower()


def test_unrelated_barrel_count_does_not_inherit_road_thread():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
    )
    out = _ask(session, scene, world, "night_porter", "How many barrels remain?")
    assert out["candidate"]["answer_kind"] == "refusal"
    assert out["authored"] is None
    assert out["probe"]["topic_key"] != "topic:barred_spur_wagon"


def test_reduced_noun_phrase_why_still_fails_closed_for_missing_cause():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="night_porter",
        last_answer=ROAD_FACT,
        topic_key="topic:barred_spur_wagon",
        revealed=["kiln_spur_closed"],
        land_clue={"id": "clue_kiln_spur", "text": ROAD_FACT},
    )
    out = _ask(session, scene, world, "night_porter", "Why is the kiln spur barred?")
    assert out["candidate"]["answer_kind"] == "refusal"
    assert out["authored"] is None


def test_direct_lexical_watch_followup_still_answers_via_owned_topic():
    scene = _gate_scene()
    world = _gate_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="guard_captain",
        last_answer=WATCH_FACT,
        topic_key="topic:captain_charge_guard",
        revealed=["watch_command"],
    )
    out = _ask(session, scene, world, "guard_captain", "Who commands the watch?")
    text = str(
        (out["candidate"].get("text") or (out["authored"] or {}).get("fact_text") or "")
    ).lower()
    assert "thoran" in text


def test_landed_public_clue_does_not_answer_unrelated_identity():
    scene = _gate_scene()
    world = _gate_world()
    session = _session_with_last_answer(
        scene=scene,
        world=world,
        npc_id="guard_captain",
        last_answer=WATCH_FACT,
        topic_key="topic:captain_charge_guard",
        revealed=["watch_command"],
        land_clue={"id": "notice_patrol_route", "text": PATROL_FACT},
    )
    out = _ask(session, scene, world, "guard_captain", "Who ordered the patrol out?")
    assert out["candidate"]["answer_kind"] == "refusal"
    authored = str((out["authored"] or {}).get("text") or "").lower()
    assert "thoran" not in authored


def test_they_go_and_who_did_it_do_not_inherit_watch_last_answer():
    scene = _gate_scene()
    world = _gate_world()
    for player in ("Where did they go?", "Who did it?"):
        session = _session_with_last_answer(
            scene=scene,
            world=world,
            npc_id="guard_captain",
            last_answer=WATCH_FACT,
            topic_key="topic:captain_charge_guard",
            revealed=["watch_command"],
            land_clue={"id": "notice_patrol_route", "text": PATROL_FACT},
        )
        out = _ask(session, scene, world, "guard_captain", player)
        assert out["candidate"]["answer_kind"] == "refusal"
        authored = str((out["authored"] or {}).get("text") or "").lower()
        assert "thoran" not in authored


def test_empty_subject_helper_rejects_noun_bearing_paraphrases():
    assert empty_subject_continues_current_thread("Why is that?") is True
    assert empty_subject_continues_current_thread("How come?") is True
    assert empty_subject_continues_current_thread("Who is that?") is True
    assert empty_subject_continues_current_thread("Who is he?") is False
    assert empty_subject_retains_topic_pressure_key("Who is he?") is True
    assert empty_subject_continues_current_thread("Where did they go?") is False
    assert empty_subject_continues_current_thread("Who did it?") is False
    assert empty_subject_continues_current_thread("Why was it shut down?") is False
    assert empty_subject_continues_current_thread("What are you doing about the missing patrol?") is False
    assert empty_subject_continues_current_thread("How many barrels remain?") is False


def test_helper_has_no_fixture_special_case():
    helper = inspect.getsource(empty_subject_continues_current_thread)
    helper += inspect.getsource(empty_subject_retains_topic_pressure_key)
    for term in CALIBRATION_ENGINE_TERMS + ("kiln_spur", "wagons vanished", "shut down"):
        assert term.lower() not in helper.lower()
