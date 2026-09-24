"""A player listen attempt stays perception when a question shares the utterance.

Open solicitations such as "Does anyone know" and "Anyone listening?" stay social.
"""
from __future__ import annotations

import pytest

from game.campaign_state import create_fresh_session_document
from game.exploration import parse_exploration_intent, resolve_exploration_action
from game.intent_parser import (
    is_qualified_pursuit_shaped,
    maybe_build_declared_travel_action,
    maybe_build_passive_interruption_wait_action,
    parse_intent,
    recover_actionable_explicit_world_action,
    segment_mixed_player_turn,
)
from game.interaction_context import (
    merge_turn_segments_for_directed_social_entry,
    rebuild_active_scene_entities,
    resolve_declared_actor_switch,
    resolve_directed_social_entry,
)
from game.interaction_routing import _build_dialogue_first_action, choose_interaction_route
from game.social import SOCIAL_KINDS, parse_social_intent
from game.storage import list_scene_ids, load_scene

pytestmark = pytest.mark.unit

HUMAN = (
    "Galinor eyes the crowd as he steadily moves into Cinderwatch, "
    "eavesdropping where he can. Is anyone talking about what have these "
    "people had to flee from? Do the refugees all seem to be from the same "
    "region, or is it a hodge-podge?"
)


def _session(scene_id: str, world: dict, scene: dict) -> dict:
    session = create_fresh_session_document()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    session["turn_counter"] = 1
    rebuild_active_scene_entities(session, world, scene_id, scene_envelope=scene)
    return session


def _cistern():
    scene = {
        "scene": {
            "id": "slate_cistern",
            "location": "Slate Cistern",
            "visible_facts": [
                "Water ticks against the cistern lip.",
                "A cistern warden murmurs about a drained basin.",
            ],
            "exits": [],
            "interactables": [],
            "addressables": [
                {
                    "id": "cistern_warden",
                    "name": "Cistern Warden",
                    "scene_id": "slate_cistern",
                    "kind": "npc",
                    "addressable": True,
                    "address_priority": 0,
                    "address_roles": ["warden"],
                    "aliases": [],
                },
                {
                    "id": "porter",
                    "name": "Porter",
                    "scene_id": "slate_cistern",
                    "kind": "scene_actor",
                    "addressable": True,
                    "address_priority": 1,
                    "address_roles": ["porter"],
                    "aliases": [],
                },
            ],
        }
    }
    world = {
        "npcs": [
            {
                "id": "cistern_warden",
                "name": "Cistern Warden",
                "location": "slate_cistern",
                "topics": [{"id": "basin", "text": "The basin is drained before second watch."}],
            }
        ]
    }
    return scene, world, _session("slate_cistern", world, scene)


def _frontier():
    scene = load_scene("frontier_gate")
    world = {
        "npcs": [
            {
                "id": "tavern_runner",
                "name": "Tavern Runner",
                "location": "frontier_gate",
                "topics": [
                    {
                        "id": "patrol_milestone",
                        "text": "The patrol never came back from the old milestone.",
                    }
                ],
            }
        ]
    }
    return scene, world, _session("frontier_gate", world, scene)


def _classify(text: str, scene: dict, session: dict, world: dict) -> dict | None:
    segmented = segment_mixed_player_turn(text)
    canonical = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=segmented,
        raw_text=text,
    )
    declared_switch = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=segmented,
        raw_text=text,
    )
    route_choice = choose_interaction_route(
        text,
        scene=scene,
        session=session,
        world=world,
        segmented_turn=segmented,
        canonical_social_entry=canonical,
    )
    merged = merge_turn_segments_for_directed_social_entry(segmented, text)
    classification_text = merged.strip() if isinstance(merged, str) and merged.strip() else text
    qualified = is_qualified_pursuit_shaped(classification_text)
    parsed = None
    if not declared_switch.get("has_declared_switch"):
        parsed = maybe_build_passive_interruption_wait_action(segmented, raw_player_text=text)
    if parsed is None and qualified:
        parsed = parse_exploration_intent(
            classification_text, scene, session, world, segmented_turn=segmented
        )
    if parsed is None and not qualified:
        parsed = recover_actionable_explicit_world_action(
            classification_text,
            scene,
            session=session,
            world=world,
            segmented_turn=segmented,
        )
    if parsed is None and not qualified:
        parsed = parse_social_intent(classification_text, scene, world)
    if parsed is None and route_choice != "action" and not qualified:
        parsed = _build_dialogue_first_action(
            player_text=text,
            segmented_turn=segmented,
            scene=scene,
            session=session,
            world=world,
            canonical_social_entry=canonical,
        )
    if parsed is None and route_choice != "dialogue" and not qualified:
        parsed = parse_exploration_intent(
            classification_text, scene, session, world, segmented_turn=segmented
        )
    if parsed is None and route_choice != "dialogue" and not qualified:
        parsed = parse_intent(classification_text)
    if isinstance(parsed, dict) and str(parsed.get("type") or "").strip().lower() in SOCIAL_KINDS:
        travel_override = maybe_build_declared_travel_action(
            segmented,
            scene=scene.get("scene") or {},
            session=session,
            world=world,
            known_scene_ids=set(list_scene_ids()),
        )
        if travel_override is not None:
            parsed = travel_override
    return parsed


def _lane(parsed: dict | None) -> str:
    if not isinstance(parsed, dict):
        return ""
    meta = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
    return str(meta.get("human_adjacent_intent_family") or meta.get("parser_lane") or "")


def test_player_listen_with_question_stays_perception_not_sole_npc():
    scene, world, session = _cistern()
    text = "I listen to see whether anyone is talking about why the span is shut?"
    parsed = _classify(text, scene, session, world)
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert _lane(parsed) == "listen"
    assert not parsed.get("target_id")


def test_eavesdrop_plus_two_questions_stays_listen():
    scene, world, session = _cistern()
    text = (
        "I eavesdrop on the porters. Is anyone talking about the drained basin? "
        "Do they look like one crew?"
    )
    parsed = _classify(text, scene, session, world)
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert _lane(parsed) == "listen"
    assert parsed.get("target_id") != "cistern_warden"


def test_overhear_while_asking_about_visible_condition_stays_listen():
    scene, world, session = _cistern()
    text = "While I overhear the porters, is the cracked pier still dripping?"
    parsed = _classify(text, scene, session, world)
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert _lane(parsed) == "listen"


def test_open_solicitation_without_listen_attempt_stays_social():
    scene, world, session = _cistern()
    parsed = _classify("Does anyone know why the span is shut?", scene, session, world)
    assert parsed is not None
    assert parsed.get("type") == "question"
    assert _lane(parsed) != "listen"


def test_anyone_listening_solicitation_is_not_a_player_listen():
    scene, world, session = _cistern()
    parsed = _classify("Anyone listening?", scene, session, world)
    assert parsed is None or parsed.get("type") != "observe"
    if isinstance(parsed, dict):
        assert _lane(parsed) != "listen"


def test_explicit_ask_stays_social():
    scene, world, session = _cistern()
    parsed = _classify(
        "I ask the warden why the basin was drained.",
        scene,
        session,
        world,
    )
    assert parsed is not None
    assert str(parsed.get("type") or "") in SOCIAL_KINDS
    assert _lane(parsed) != "listen"


def test_atomic_listen_stays_observe():
    scene, world, session = _cistern()
    parsed = _classify("I listen to the yard.", scene, session, world)
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert _lane(parsed) == "listen"


def test_captured_human_turn_is_listen_not_tavern_runner_question():
    scene, world, session = _frontier()
    parsed = _classify(HUMAN, scene, session, world)
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert _lane(parsed) == "listen"
    assert parsed.get("target_id") != "tavern_runner"
    res = resolve_exploration_action(
        scene,
        session,
        world,
        parsed,
        raw_player_text=HUMAN,
        list_scene_ids=lambda: [],
        character=None,
        scene_graph=None,
        load_scene_fn=None,
    )
    hint = str(res.get("hint") or "").lower()
    assert res.get("kind") == "observe"
    assert "wilderland" not in hint
    assert "all directions" not in hint
    assert "hodge" not in hint
