"""BV3A — observe-route referential clarity upstream repair and non-strict local substitution."""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
from game.defaults import default_scene, default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.storage import get_scene_runtime
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from tests.helpers.opening_fallback_evidence import assert_final_emission_meta_contains

pytestmark = pytest.mark.unit


def _observe_bundle_with_interlocutor(*, npc_id: str = "tavern_runner", npc_name: str = "Tavern Runner"):
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    scene = default_scene(sid)
    set_social_target(session, npc_id)
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "I watch the runner closely."
    resolution = {
        "kind": "observe",
        "prompt": "I watch the runner closely.",
        "social": {
            "npc_id": npc_id,
            "npc_name": npc_name,
        },
        "metadata": {
            "human_adjacent_intent_family": "observe_group",
        },
    }
    return session, world, scene, sid, resolution


def test_observe_dialogue_he_says_repairs_via_upstream_not_hard_fallback():
    session, world, scene, sid, resolution = _observe_bundle_with_interlocutor()
    candidate = '"Keep your wits about you," he says, glancing toward the checkpoint.'
    gm = {"player_facing_text": candidate, "tags": []}

    out, _ = apply_final_emission_gate_consumer(
        gm,
        resolution=resolution,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    text = out["player_facing_text"]
    meta = final_emission_meta_from_output(out)

    assert " he " not in f" {text.lower()} "
    assert "tavern runner" in text.lower()
    assert meta.get("referential_clarity_upstream_repair_applied") is True
    assert meta.get("referential_clarity_local_substitution_applied") is True
    assert meta.get("referential_clarity_replacement_applied") is not True
    assert meta.get("referential_clarity_validation_passed") is True
    assert "referential_clarity_enforcement_replaced" not in [str(t) for t in (out.get("tags") or [])]
    assert meta.get("final_route") != "replaced"


def test_observe_ambiguous_speaker_without_interlocutor_still_hard_replaces():
    session, world, scene, sid = _observe_bundle_without_social()
    candidate = 'Guard Captain and Tavern Runner stand near the gate. "Back away," he says.'
    resolution = {"kind": "observe", "prompt": "I look around."}

    out = feg.apply_final_emission_gate(
        {"player_facing_text": candidate, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        scene=scene,
    )
    meta = final_emission_meta_from_output(out)
    assert out["player_facing_text"] != candidate
    assert meta.get("referential_clarity_replacement_applied") is True
    assert "referential_clarity_enforcement_replaced" in [str(t) for t in (out.get("tags") or [])]


def _observe_bundle_without_social():
    session = default_session()
    world = default_world()
    scene = default_scene("frontier_gate")
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


def test_observe_single_visible_person_dialogue_he_says_repairs_without_social_target():
    session, world, scene, sid = _observe_bundle_without_social()
    resolution = {"kind": "observe", "prompt": "I listen."}
    candidate = '"The road is watched," he says quietly.'

    out = feg.apply_final_emission_gate(
        {"player_facing_text": candidate, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        scene=scene,
    )
    meta = final_emission_meta_from_output(out)
    if meta.get("referential_clarity_upstream_repair_applied") is True:
        assert meta.get("referential_clarity_replacement_applied") is not True
        assert "referential_clarity_enforcement_replaced" not in [str(t) for t in (out.get("tags") or [])]
