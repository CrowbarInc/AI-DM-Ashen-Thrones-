from __future__ import annotations

from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from game.defaults import default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.dialogue_social_plan import validate_dialogue_social_plan
from game.storage import get_scene_runtime
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
 )

import pytest

pytestmark = pytest.mark.unit


def _strict_social_resolution(npc_id: str = "tavern_runner", npc_name: str = "Tavern Runner") -> dict:
    return {
        "kind": "question",
        "prompt": "Where did they go?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": npc_id,
            "npc_name": npc_name,
            "npc_reply_expected": True,
        },
        "metadata": {"response_type_contract": {"required_response_type": "dialogue"}},
    }


def test_quoted_npc_line_without_plan_fails_closed() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Tavern Runner says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_checked") is True
    assert meta.get("dialogue_plan_required") is True
    assert meta.get("dialogue_plan_present") is False
    assert meta.get("dialogue_plan_valid") is False
    assert meta.get("dialogue_plan_failure_reasons")
    assert '"' not in out["player_facing_text"]


def test_quoted_npc_line_with_valid_plan_passes() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
        ),
    )

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Tavern Runner says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_checked") is True
    assert meta.get("dialogue_plan_required") is True
    assert meta.get("dialogue_plan_present") is True
    assert meta.get("dialogue_plan_valid") is True
    assert '"' in out["player_facing_text"]


def test_missing_speaker_id_fails() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    plan = make_valid_dialogue_social_plan(speaker_id="tavern_runner", speaker_name="Tavern Runner")
    plan["speaker_id"] = ""
    attach_dialogue_social_plan_to_resolution(resolution, plan)

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Tavern Runner says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is False
    assert "missing_required:speaker_id" in (meta.get("dialogue_plan_failure_reasons") or [])
    assert '"' not in out["player_facing_text"]


def test_missing_dialogue_intent_fails() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    plan = make_valid_dialogue_social_plan(speaker_id="tavern_runner", speaker_name="Tavern Runner")
    plan["dialogue_intent"] = ""
    attach_dialogue_social_plan_to_resolution(resolution, plan)

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Tavern Runner says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is False
    assert "missing_required:dialogue_intent" in (meta.get("dialogue_plan_failure_reasons") or [])
    assert '"' not in out["player_facing_text"]


def test_wrong_attributed_speaker_fails_closed() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
        ),
    )

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Guard Captain says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is False
    reasons = meta.get("dialogue_plan_failure_reasons") or []
    assert any(str(r).startswith("attributed_speaker_mismatch:") for r in reasons)
    assert '"' not in out["player_facing_text"]


def test_generic_social_stabilization_line_without_plan_fails() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": "Tavern Runner nods and looks at you.", "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_required") is True
    assert meta.get("dialogue_plan_valid") is False


def test_non_dialogue_narration_unaffected_when_not_strict_social() -> None:
    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": "Rain beads on the checkpoint stones.", "tags": []},
        resolution=None,
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert meta.get("dialogue_plan_checked") in (None, False)
    assert out["player_facing_text"] == "Rain beads on the checkpoint stones."


def test_block_z_declared_writer_attribution_label_passes() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
            writer_attribution_label="Ragged stranger",
            speaker_alias_resolution_source="manual_bundle_override",
        ),
    )

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Ragged stranger says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is True
    assert '"' in out["player_facing_text"]


def test_block_z_declared_allowed_pregate_labels_passes() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
            allowed_pregate_speaker_labels=["Ragged stranger", "Hooded figure"],
            speaker_alias_resolution_source="manual_bundle_override",
        ),
    )

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Hooded figure says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is True


def test_block_z_alias_labels_without_provenance_plan_invalid() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    plan = make_valid_dialogue_social_plan(
        speaker_id="tavern_runner",
        speaker_name="Tavern Runner",
        dialogue_intent="question",
    )
    plan["allowed_pregate_speaker_labels"] = ["Ragged stranger"]
    plan.pop("speaker_alias_resolution_source", None)
    attach_dialogue_social_plan_to_resolution(resolution, plan)

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Ragged stranger says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is False
    reasons = meta.get("dialogue_plan_failure_reasons") or []
    assert any(str(r).startswith("plan_invalid:") for r in reasons)


def test_block_z_invalid_provenance_inferred_from_prose_plan_invalid() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    plan = make_valid_dialogue_social_plan(
        speaker_id="tavern_runner",
        speaker_name="Tavern Runner",
        dialogue_intent="question",
        allowed_pregate_speaker_labels=["Ragged stranger"],
        speaker_alias_resolution_source="manual_bundle_override",
    )
    plan["speaker_alias_resolution_source"] = "inferred_from_prose"
    attach_dialogue_social_plan_to_resolution(resolution, plan)

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Ragged stranger says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is False
    reasons = meta.get("dialogue_plan_failure_reasons") or []
    assert any("bad_speaker_alias_resolution_source" in str(r) for r in reasons)


def test_block_z_unrelated_alias_still_mismatch() -> None:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _strict_social_resolution()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = resolution["prompt"]
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
            allowed_pregate_speaker_labels=["Ragged stranger"],
            speaker_alias_resolution_source="manual_bundle_override",
        ),
    )

    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Town crier says, "East road."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("dialogue_plan_valid") is False
    reasons = meta.get("dialogue_plan_failure_reasons") or []
    assert any(str(r).startswith("attributed_speaker_mismatch:") for r in reasons)

