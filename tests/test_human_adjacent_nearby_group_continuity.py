"""Block K: nearby-group / listen follow-ups consume canonical HA snapshot (scene_runtime)."""
from __future__ import annotations

import pytest

from game.defaults import default_session, default_world
from game.exploration import resolve_exploration_action
from game.human_adjacent_focus import qualifying_canonical_ha_continuity_bundle
from game.intent_parser import parse_freeform_to_action
from game.interaction_context import _looks_like_local_observation_question, resolve_directed_social_entry
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _scene_env(scene_id: str, visible_facts: list[str]) -> dict:
    return {"scene": {"id": scene_id, "exits": [], "visible_facts": visible_facts}}


def _seed_speaking_group_snapshot(session: dict, scene_id: str) -> None:
    snap = qualifying_canonical_ha_continuity_bundle(
        {
            "parser_lane": "human_adjacent_observe",
            "human_adjacent_intent_family": "listen",
            "implicit_focus_resolution": "speaking_group",
            "implicit_focus_anchor_fact": "A huddled group of refugees nearby murmurs about the missing patrol.",
        }
    )
    assert snap is not None
    get_scene_runtime(session, scene_id)["last_human_adjacent_continuity"] = snap


def test_listen_then_what_are_they_saying_carries_group_metadata() -> None:
    scene_id = "gate"
    inner = {
        "id": scene_id,
        "exits": [],
        "visible_facts": [
            "A muddy patch is strewn with crates, providing cover.",
            "A huddled group of refugees nearby murmurs about the missing patrol, their expressions grave.",
        ],
    }
    env = _scene_env(scene_id, inner["visible_facts"])
    session = default_session()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]

    first = parse_freeform_to_action("I eavesdrop on the refugees", env, session=session, world=default_world())
    assert first and first.get("type") == "observe"
    res = resolve_exploration_action(
        env,
        session,
        default_world(),
        first,
        raw_player_text="I eavesdrop on the refugees",
        list_scene_ids=lambda: [scene_id],
        character=None,
        scene_graph=None,
        load_scene_fn=None,
    )
    md0 = res.get("metadata") or {}
    assert md0.get("implicit_focus_resolution") == "speaking_group"
    get_scene_runtime(session, scene_id)["last_human_adjacent_continuity"] = qualifying_canonical_ha_continuity_bundle(
        md0
    )

    follow = parse_freeform_to_action("What are they saying?", env, session=session, world=default_world())
    assert follow is not None
    assert follow.get("type") == "observe"
    fmd = follow.get("metadata") or {}
    assert fmd.get("parser_lane") == "human_adjacent_observe"
    assert fmd.get("nearby_group_continuity_carryover") is True
    assert fmd.get("implicit_focus_resolution") == "speaking_group"
    assert "refugee" in (fmd.get("implicit_focus_anchor_fact") or "").lower()
    assert fmd.get("implicit_focus_target_id") in (None, "")


def test_move_closer_after_listen_preserves_speaking_group() -> None:
    scene_id = "square"
    env = _scene_env(
        scene_id,
        [
            "Two alleyways lead away from the square.",
            "A gossiping cluster of patrons trades rumors near the tavern door, voices rising and falling together.",
        ],
    )
    session = default_session()
    session["active_scene_id"] = scene_id
    _seed_speaking_group_snapshot(session, scene_id)

    act = parse_freeform_to_action("I move closer", env, session=session, world=default_world())
    assert act is not None
    md = act.get("metadata") or {}
    assert md.get("implicit_focus_resolution") == "speaking_group"
    assert md.get("nearby_group_continuity_carryover") is True


def test_crowd_cluster_snapshot_does_not_invent_target_id() -> None:
    scene_id = "crowd"
    env = _scene_env(scene_id, ["A dense crowd fills the square, many voices overlapping."])
    session = default_session()
    session["active_scene_id"] = scene_id
    snap = qualifying_canonical_ha_continuity_bundle(
        {
            "parser_lane": "human_adjacent_observe",
            "human_adjacent_intent_family": "listen",
            "implicit_focus_resolution": "crowd_cluster",
            "implicit_focus_anchor_fact": "A dense crowd fills the square, many voices overlapping.",
        }
    )
    assert snap is not None
    get_scene_runtime(session, scene_id)["last_human_adjacent_continuity"] = snap

    act = parse_freeform_to_action("What do I hear?", env, session=session, world=default_world())
    assert act is not None
    md = act.get("metadata") or {}
    assert md.get("implicit_focus_resolution") == "crowd_cluster"
    assert not md.get("implicit_focus_target_id")


def test_explicit_addressed_npc_breaks_carryover() -> None:
    scene_id = "mix"
    env = _scene_env(
        scene_id,
        [
            "A huddled group of refugees nearby murmurs urgently.",
        ],
    )
    session = default_session()
    session["active_scene_id"] = scene_id
    world = default_world()
    world["npcs"] = [
        {"id": "runner", "name": "Tavern Runner", "location": scene_id, "topics": []},
    ]
    _seed_speaking_group_snapshot(session, scene_id)

    act = parse_freeform_to_action("What does Tavern Runner know about the gate?", env, session=session, world=world)
    assert act is None or (act.get("metadata") or {}).get("nearby_group_continuity_carryover") is not True


def test_physical_inspection_blocks_carryover() -> None:
    scene_id = "yard"
    env = _scene_env(
        scene_id,
        [
            "A huddled group of refugees nearby murmurs urgently.",
            "The muddy ground bears faint footprints leading toward stacked crates.",
        ],
    )
    session = default_session()
    session["active_scene_id"] = scene_id
    _seed_speaking_group_snapshot(session, scene_id)

    act = parse_freeform_to_action(
        "I inspect the footprints near the crates", env, session=session, world=default_world()
    )
    assert act is not None
    assert act.get("type") == "investigate"
    assert (act.get("metadata") or {}).get("nearby_group_continuity_carryover") is not True


def test_what_do_i_hear_suppresses_local_observation_classifier_with_snapshot() -> None:
    scene_id = "z1"
    env = _scene_env(scene_id, ["Refugees argue in low voices near the wagons."])
    session = default_session()
    session["active_scene_id"] = scene_id
    _seed_speaking_group_snapshot(session, scene_id)

    assert not _looks_like_local_observation_question(
        "What do I hear?",
        session=session,
        scene_envelope=env,
        world=default_world(),
        segmented_turn=None,
        apply_ha_continuity_suppress=True,
    )


def test_resolve_directed_social_contract_includes_continuity_basis() -> None:
    scene_id = "z2"
    env = _scene_env(scene_id, ["Patrons gossip near the bar."])
    session = default_session()
    session["active_scene_id"] = scene_id
    world = default_world()
    _seed_speaking_group_snapshot(session, scene_id)

    out = resolve_directed_social_entry(
        session=session,
        scene=env,
        world=world,
        segmented_turn=None,
        raw_text="What do I hear?",
    )
    stc = out.get("social_turn_contract") or {}
    assert stc.get("continuity_basis") == "nearby_group_focus"
    assert stc.get("nearby_group_focus_source") == "implicit_focus_resolution"
