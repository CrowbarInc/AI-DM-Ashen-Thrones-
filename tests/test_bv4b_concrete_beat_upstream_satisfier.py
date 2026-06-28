"""BV4B — passive-scene concrete beat upstream satisfier (EC-4A-01 / EC-4A-02)."""

from __future__ import annotations

import pytest

from game.defaults import default_scene, default_session, default_world
from game.final_emission_passive_scene_pressure import (
    apply_observe_passive_scene_concrete_beat_upstream_satisfier,
    reply_has_concrete_interaction,
)
from game.storage import get_scene_runtime
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer

pytestmark = pytest.mark.unit


def _passive_observe_bundle(*, prompt: str = "I scan the notice board and watch who reacts."):
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    scene = default_scene(sid)
    scene["scene"]["visible_facts"] = [
        "A gate guard watches the notice board.",
        "A notice board lists taxes, curfew rules, and a missing patrol rumor.",
    ]
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_passive"] = True
    rt["passive_action_streak"] = 1
    resolution = {
        "kind": "observe",
        "prompt": prompt,
        "metadata": {"human_adjacent_intent_family": "observe_group"},
    }
    return session, world, scene, sid, resolution


def test_reply_has_concrete_interaction_detects_dialogue_and_approach():
    assert reply_has_concrete_interaction('A guard calls out, "Move along."')
    assert not reply_has_concrete_interaction("The notice board lists taxes and curfew rules.")


def test_upstream_satisfier_injects_beat_when_pressure_due_and_beat_missing():
    session, world, scene, sid, resolution = _passive_observe_bundle()
    upstream = "As you watch the scene, the notice board lists taxes, curfew rules, and a warning."
    gm = {"player_facing_text": upstream, "tags": []}

    out = apply_observe_passive_scene_concrete_beat_upstream_satisfier(
        gm,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        res_kind="observe",
        strict_social_active=False,
    )
    meta = out.get("_final_emission_meta") or out.get("final_emission_meta") or {}
    assert meta.get("passive_scene_concrete_beat_satisfier_applied") is True
    assert meta.get("producer_repair_kind") == "passive_scene_concrete_beat"
    assert meta.get("passive_scene_concrete_beat_type") in {
        "guard_reaction",
        "generic_interruption",
        "observer_interruption",
    }
    assert meta.get("passive_scene_pressure_fallback_avoided") is True
    assert reply_has_concrete_interaction(str(out.get("player_facing_text") or ""))


def test_observe_passive_pressure_avoids_sealed_fallback_via_gate():
    session, world, scene, sid, resolution = _passive_observe_bundle()
    upstream = "As you watch the scene, the notice board lists taxes, curfew rules, and a warning."
    gm = {"player_facing_text": upstream, "tags": []}

    out, _ = apply_final_emission_gate_consumer(
        gm,
        resolution=resolution,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
    )
    meta = final_emission_meta_from_output(out)
    assert meta.get("passive_scene_concrete_beat_satisfier_applied") is True
    assert meta.get("final_emitted_source") != "passive_scene_pressure_fallback"
    assert meta.get("final_route") != "replaced"


def test_upstream_satisfier_skips_when_concrete_beat_already_present():
    session, world, scene, sid, _resolution = _passive_observe_bundle()
    upstream = (
        'As you watch the board, a guard notices you lingering and comes over. '
        '"If you are waiting on trouble, it already passed," he says.'
    )
    gm = {"player_facing_text": upstream, "tags": []}

    out = apply_observe_passive_scene_concrete_beat_upstream_satisfier(
        gm,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        res_kind="observe",
        strict_social_active=False,
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("passive_scene_concrete_beat_satisfier_attempted") is True
    assert meta.get("passive_scene_concrete_beat_satisfier_applied") is not True
    assert out.get("player_facing_text") == upstream
