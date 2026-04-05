from __future__ import annotations

from copy import deepcopy

import pytest

import game.api_turn_support as api_turn_support
from game.defaults import default_scene, default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.storage import get_scene_runtime


pytestmark = pytest.mark.unit

GLOBAL_VISIBILITY_FALLBACK = "For a breath, the scene holds while voices shift around you."
VISIBLE_FACT = "A brazier throws orange sparks over the checkpoint."
DISCOVERABLE_FACT = "The missing patrol was last seen near the old stone bridge."
HIDDEN_FACT = "The checkpoint taxes are funding an Ash Cowl payoff."


def _base_visibility_bundle():
    session = default_session()
    world = default_world()
    world["npcs"].append(
        {
            "id": "lord_aldric",
            "name": "Lord Aldric",
            "location": "castle_keep",
        }
    )
    scene = default_scene("frontier_gate")
    scene["scene"]["visible_facts"] = [VISIBLE_FACT]
    scene["scene"]["discoverable_clues"] = [DISCOVERABLE_FACT]
    scene["scene"]["hidden_facts"] = [HIDDEN_FACT]
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def _finalize_via_turn_support(
    text: str,
    *,
    session: dict,
    world: dict,
    scene: dict,
    resolution: dict | None = None,
) -> dict:
    scene["scene_state"] = dict(session["scene_state"])
    out, _narr_meta = api_turn_support._finalize_player_facing_for_turn(
        {"player_facing_text": text, "tags": []},
        resolution=resolution,
        session=session,
        world=world,
        scene=scene,
    )
    assert out["_player_facing_emission_finalized"] is True
    return out


def test_pipeline_replaces_offscene_known_npc_reference():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        "Lord Aldric watches the checkpoint from the square.",
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert out["tags"] == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:unseen_entity_reference",
    ]
    assert out["_final_emission_meta"]["visibility_validation_passed"] is False
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is True
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == [
        "unseen_entity_reference",
    ]
    assert out["_final_emission_meta"]["visibility_checked_entities"] == [
        {
            "entity_id": "lord_aldric",
            "matched_aliases": ["lord aldric"],
        }
    ]


def test_pipeline_allows_visible_npc_reference():
    session, world, scene, _sid = _base_visibility_bundle()
    candidate = "Guard Captain scans the crowd and signals another guard forward."

    out = _finalize_via_turn_support(
        candidate,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == candidate
    assert out["tags"] == []
    assert out["_final_emission_meta"]["visibility_validation_passed"] is True
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is False
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == []
    assert out["_final_emission_meta"]["visibility_checked_entities"] == [
        {
            "entity_id": "guard_captain",
            "matched_aliases": ["guard captain"],
        }
    ]


def test_pipeline_allows_active_interlocutor_reference():
    session, world, scene, _sid = _base_visibility_bundle()
    set_social_target(session, "tavern_runner")
    candidate = 'Tavern Runner leans in and says, "Keep your hood up in this rain."'

    out = _finalize_via_turn_support(
        candidate,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == candidate
    assert out["tags"] == []
    assert out["_final_emission_meta"]["active_interlocutor_id"] == "tavern_runner"
    assert out["_final_emission_meta"]["visibility_validation_passed"] is True
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is False
    assert out["_final_emission_meta"]["visibility_checked_entities"] == [
        {
            "entity_id": "tavern_runner",
            "matched_aliases": ["tavern runner"],
        }
    ]


def test_pipeline_replaces_hidden_fact_assertion():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        HIDDEN_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert out["tags"] == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_validation_passed"] is False
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is True
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == [
        "undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_checked_facts"] == [
        {
            "kind": "hidden_fact_strings",
            "fact": "the checkpoint taxes are funding an ash cowl payoff",
            "match_kind": "exact",
        }
    ]


def test_pipeline_replaces_discoverable_but_undiscovered_fact_assertion():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        DISCOVERABLE_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert out["tags"] == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_validation_passed"] is False
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is True
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == [
        "undiscovered_fact_assertion",
    ]
    assert out["_final_emission_meta"]["visibility_checked_facts"] == [
        {
            "kind": "discoverable_fact_strings",
            "fact": "the missing patrol was last seen near the old stone bridge",
            "match_kind": "exact",
        }
    ]


def test_pipeline_allows_visible_fact_assertion():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        VISIBLE_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == VISIBLE_FACT
    assert out["tags"] == []
    assert out["_final_emission_meta"]["visibility_validation_passed"] is True
    assert out["_final_emission_meta"]["visibility_replacement_applied"] is False
    assert out["_final_emission_meta"]["visibility_violation_kinds"] == []
    assert out["_final_emission_meta"]["visibility_checked_facts"] == [
        {
            "kind": "visible_fact_strings",
            "fact": "a brazier throws orange sparks over the checkpoint",
            "match_kind": "exact",
        }
    ]


def test_pipeline_visibility_metadata_captures_entity_and_fact_matches():
    session, world, scene, _sid = _base_visibility_bundle()

    out = _finalize_via_turn_support(
        f"Lord Aldric says {HIDDEN_FACT}",
        session=session,
        world=world,
        scene=scene,
    )

    meta = out["_final_emission_meta"]
    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert meta["visibility_validation_passed"] is False
    assert meta["visibility_replacement_applied"] is True
    assert meta["visibility_violation_kinds"] == [
        "unseen_entity_reference",
        "undiscovered_fact_assertion",
    ]
    assert meta["visibility_checked_entities"] == [
        {
            "entity_id": "lord_aldric",
            "matched_aliases": ["lord aldric"],
        }
    ]
    assert meta["visibility_checked_facts"] == [
        {
            "kind": "hidden_fact_strings",
            "fact": "the checkpoint taxes are funding an ash cowl payoff",
            "match_kind": "substring",
        }
    ]
    assert [sample["kind"] for sample in meta["visibility_violation_sample"]] == [
        "unseen_entity_reference",
        "undiscovered_fact_assertion",
    ]


def test_pipeline_visibility_enforcement_is_read_only_for_discovery_state(monkeypatch):
    session, world, scene, sid = _base_visibility_bundle()
    runtime = get_scene_runtime(session, sid)
    runtime["discovered_clues"].append("Known clue.")
    runtime["revealed_hidden_facts"].append("Known secret.")
    session["clue_knowledge"] = {
        "known_clue": {
            "text": "Known clue.",
            "source_scene": sid,
        }
    }
    scene["scene"]["visible_facts"].append("The rain has started to ease.")

    monkeypatch.setattr(api_turn_support, "apply_repeated_description_guard", lambda gm, session, scene_id: None)
    monkeypatch.setattr(api_turn_support, "update_scene_momentum_runtime", lambda session, scene_id, gm: {})

    before_session = deepcopy(session)
    before_world = deepcopy(world)
    before_scene = deepcopy(scene)
    before_runtime = deepcopy(get_scene_runtime(session, sid))
    before_clue_knowledge = deepcopy(session["clue_knowledge"])

    out = _finalize_via_turn_support(
        HIDDEN_FACT,
        session=session,
        world=world,
        scene=scene,
    )

    assert out["player_facing_text"] == GLOBAL_VISIBILITY_FALLBACK
    assert get_scene_runtime(session, sid) == before_runtime
    assert session["clue_knowledge"] == before_clue_knowledge
    assert session == before_session
    assert world == before_world
    assert scene == before_scene
