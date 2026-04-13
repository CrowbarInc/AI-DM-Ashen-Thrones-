"""Scene emit integrity gating for global narrative fallback (STI2 downstream).

STI closeout: explicit named destination beats an active lead unless the player explicitly
pursues the lead; incompatible transitions do not commit; blocked travel-like turns must not
launder a mismatched scene envelope into ``global_scene_fallback`` narration (see
``scene_emit_integrity_safe_fallback`` / ``_final_emission_meta`` keys).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.final_emission_gate import apply_final_emission_gate


_REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_old_milestone_envelope() -> dict:
    p = _REPO_ROOT / "data" / "scenes" / "old_milestone.json"
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def _banned_pregate_text() -> str:
    """Triggers ``banned_stock_phrase`` in :func:`apply_final_emission_gate` non-strict path."""
    return (
        "From here, no certain answer presents itself about the road ahead, "
        "so you watch the dust settle instead."
    )


def test_blocked_incompatible_scene_transition_blocks_global_scene_fallback():
    session = {"active_scene_id": "frontier_gate"}
    wrong_place = _load_old_milestone_envelope()
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": False,
        "target_scene_id": None,
        "metadata": {
            "blocked_incompatible_scene_transition": True,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": False,
            "destination_compatibility_failure_reason": "declared_place_bucket_mismatches_target_scene_bucket",
        },
    }
    gm_out = {
        "player_facing_text": _banned_pregate_text(),
        "tags": [],
    }
    out = apply_final_emission_gate(
        gm_out,
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        scene=wrong_place,
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    text = str(out.get("player_facing_text") or "")
    low = text.lower()

    assert meta.get("scene_integrity_blocked_global_fallback") is True
    assert meta.get("scene_integrity_passed") is False
    assert "blocked_incompatible_scene_transition" in (meta.get("scene_integrity_failure_reasons") or [])
    assert meta.get("final_emitted_source") == "scene_emit_integrity_safe_fallback"
    assert "milestone" not in low
    assert "weathered milestone" not in low
    assert "unfinished" in low


def test_stone_boar_blocked_transition_does_not_emit_old_milestone_roadside_prose():
    """Wrong-scene envelope must not yield old_milestone global stock when travel integrity fails."""
    session = {"active_scene_id": "frontier_gate"}
    wrong_place = _load_old_milestone_envelope()
    resolution = {
        "kind": "scene_transition",
        "prompt": "Galinor enters the Stone Boar.",
        "resolved_transition": False,
        "target_scene_id": None,
        "metadata": {
            "blocked_incompatible_scene_transition": True,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": False,
            "destination_binding_source": "normalized_action_target",
            "destination_semantic_kind": "explicit_scene_id",
        },
    }
    gm_out = {"player_facing_text": _banned_pregate_text(), "tags": []}
    out = apply_final_emission_gate(
        gm_out,
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        scene=wrong_place,
        world={},
    )
    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = out.get("_final_emission_meta") or {}

    assert meta.get("final_emitted_source") == "scene_emit_integrity_safe_fallback"
    assert "blasted scrub" not in low
    assert "black rainwater" not in low
    assert "carrion" not in low


def test_valid_resolved_scene_transition_allows_global_scene_fallback():
    session = {"active_scene_id": "old_milestone"}
    envelope = _load_old_milestone_envelope()
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "old_milestone",
        "metadata": {
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "blocked_incompatible_scene_transition": False,
        },
    }
    gm_out = {"player_facing_text": _banned_pregate_text(), "tags": []}
    out = apply_final_emission_gate(
        gm_out,
        resolution=resolution,
        session=session,
        scene_id="old_milestone",
        scene=envelope,
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    text = str(out.get("player_facing_text") or "")
    low = text.lower()

    assert meta.get("scene_integrity_passed") is True
    assert meta.get("scene_integrity_blocked_global_fallback") is False
    assert meta.get("final_emitted_source") == "global_scene_fallback"
    assert "milestone" in low or "road" in low or "rain" in low or "scrub" in low


@pytest.mark.parametrize(
    "binding_source,expect_block",
    [
        ("explicit_named_place_unresolved", True),
        ("explicit_named_place_in_player_text", False),
    ],
)
def test_named_place_unresolved_suppresses_global_fallback(binding_source: str, expect_block: bool):
    session = {"active_scene_id": "frontier_gate"}
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": False,
        "target_scene_id": None,
        "metadata": {
            "destination_binding_source": binding_source,
            "destination_semantic_kind": "named_place",
            "destination_compatibility_checked": False,
            "destination_compatibility_passed": True,
        },
    }
    gate_scene = {
        "scene": {
            "id": "frontier_gate",
            "location": "Cinderwatch Gate",
            "summary": "Ash drifts between spearpoints and merchant calls.",
            "visible_facts": ["Guards watch the gate line."],
        }
    }
    gm_out = {"player_facing_text": _banned_pregate_text(), "tags": []}
    out = apply_final_emission_gate(
        gm_out,
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        scene=gate_scene,
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    if expect_block:
        assert meta.get("scene_integrity_blocked_global_fallback") is True
        assert meta.get("final_emitted_source") == "scene_emit_integrity_safe_fallback"
    else:
        assert meta.get("scene_integrity_blocked_global_fallback") is not True
        assert meta.get("final_emitted_source") == "global_scene_fallback"
