"""BV3E — expanded observe-route referential clarity eligibility and alias introducer repair."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import game.final_emission_gate as feg
import game.storage as storage
from game.defaults import default_scene, default_session, default_world
from game.final_emission_referential_clarity import apply_observe_referential_clarity_upstream_repair
from game.interaction_context import rebuild_active_scene_entities
from game.narration_visibility import validate_player_facing_referential_clarity
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.golden_replay_fixtures import seed_frontier_gate_world

pytestmark = pytest.mark.unit

_PRODUCTION_OBSERVE_TEXT = (
    "The pause snaps when a nearby guard points with his spear-butt instead of "
    'waiting for you to choose. "Board, runner, or road," he says. '
    '"Pick one before the gate swallows the trail."'
)


def _observe_bundle_frontier_gate(*, seed_hygiene_world: bool = True):
    if seed_hygiene_world:
        seed_frontier_gate_world()
    session = storage.load_session() if seed_hygiene_world else default_session()
    world = storage.load_world() if seed_hygiene_world else default_world()
    sid = "frontier_gate"
    scene = storage.load_scene(sid) if seed_hygiene_world else default_scene(sid)
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    resolution = {"kind": "observe", "prompt": "I watch the gate."}
    return session, world, scene, sid, resolution


def _apply_upstream_repair(candidate: str, *, session, world, scene, sid, resolution):
    out = {"player_facing_text": candidate, "tags": []}
    return apply_observe_referential_clarity_upstream_repair(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution=resolution,
        active_interlocutor="",
        res_kind="observe",
        strict_social_active=False,
    )


def test_production_observe_multi_violation_guard_introducer_is_bv3e_eligible():
    session, world, scene, sid, _resolution = _observe_bundle_frontier_gate()
    validation = validate_player_facing_referential_clarity(
        _PRODUCTION_OBSERVE_TEXT,
        session=session,
        scene=scene,
        world=world,
    )
    assert validation.get("ok") is not True
    assert len(validation.get("violations") or []) >= 2


def test_production_observe_multi_violation_repairs_via_alias_introducer_not_hard_replace():
    session, world, scene, sid, resolution = _observe_bundle_frontier_gate()
    out = _apply_upstream_repair(
        _PRODUCTION_OBSERVE_TEXT,
        session=session,
        world=world,
        scene=scene,
        sid=sid,
        resolution=resolution,
    )
    meta = final_emission_meta_from_output(out)
    text = out["player_facing_text"]

    assert meta.get("referential_clarity_upstream_repair_applied") is True
    assert meta.get("referential_clarity_local_substitution_applied") is True
    assert meta.get("referential_clarity_replacement_applied") is not True
    assert meta.get("referential_clarity_bv3e_repair_mode") == "exact_alias_introducer"
    assert meta.get("referential_clarity_validation_passed") is True
    assert "gate guard" in text.lower()
    assert meta.get("referential_clarity_unrepaired_violation_count") == 0


def test_multi_person_dialogue_he_without_introducer_still_ineligible():
    session = default_session()
    world = default_world()
    scene = default_scene("frontier_gate")
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    resolution = {"kind": "observe", "prompt": "I look around."}
    candidate = (
        "Guard Captain and Tavern Runner stand near the gate. "
        '"Back away," he says.'
    )
    out = _apply_upstream_repair(
        candidate,
        session=session,
        world=world,
        scene=scene,
        sid=sid,
        resolution=resolution,
    )
    meta = final_emission_meta_from_output(out)
    assert meta.get("referential_clarity_upstream_repair_applied") is not True
    assert meta.get("referential_clarity_upstream_repair_eligible") is not True


def test_multi_person_dialogue_he_without_introducer_still_hard_replaces_via_gate():
    session, world, scene, sid = _observe_bundle_frontier_gate(seed_hygiene_world=False)[0:4]
    resolution = {"kind": "observe", "prompt": "I look around."}
    candidate = (
        "Guard Captain and Tavern Runner stand near the gate. "
        '"Back away," he says.'
    )
    out = feg.apply_final_emission_gate(
        {"player_facing_text": candidate, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        scene=scene,
    )
    meta = final_emission_meta_from_output(out)
    assert meta.get("referential_clarity_replacement_applied") is True


def test_canonical_session_log_observe_shape_repairs_when_replayed():
    log_path = Path("data/session_log.jsonl")
    if not log_path.is_file():
        pytest.skip("canonical session_log.jsonl not present")
    record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    candidate = str((record.get("gm_output") or {}).get("player_facing_text") or "")
    if not candidate.strip():
        pytest.skip("session_log observe turn missing player_facing_text")
    session, world, scene, sid, resolution = _observe_bundle_frontier_gate()
    out = _apply_upstream_repair(
        candidate,
        session=session,
        world=world,
        scene=scene,
        sid=sid,
        resolution=resolution,
    )
    meta = final_emission_meta_from_output(out)
    assert meta.get("referential_clarity_upstream_repair_applied") is True
    assert meta.get("referential_clarity_bv3e_repair_mode") == "exact_alias_introducer"
    assert meta.get("referential_clarity_replacement_applied") is not True
