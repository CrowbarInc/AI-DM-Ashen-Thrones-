from __future__ import annotations

import copy

from game import ctir
from game.narrative_planning import build_narrative_plan, validate_narrative_plan


def _base_ctir() -> dict:
    return ctir.build_ctir(
        turn_id="t-1",
        scene_id="scene_a",
        player_input="go",
        builder_source="test.transition_node",
    )


def test_target_scene_id_creates_transition_node() -> None:
    c = _base_ctir()
    c["resolution"] = {"kind": "scene_transition", "target_scene_id": "scene_b"}
    plan = build_narrative_plan(ctir=c)
    tn = plan["transition_node"]
    assert tn["transition_required"] is True
    assert tn["transition_type"] in ("location_change", "scene_entry")
    assert tn["before_anchor"]["scene_id"] == "scene_a"
    assert tn["after_anchor"]["scene_id"] == "scene_b"
    assert "resolution.target_scene_id" in (tn.get("source_fields") or [])
    assert validate_narrative_plan(plan, strict=True) is None


def test_resolved_transition_creates_transition_node() -> None:
    c = _base_ctir()
    c["resolution"] = {"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "scene_b"}
    plan = build_narrative_plan(ctir=c)
    tn = plan["transition_node"]
    assert tn["transition_required"] is True
    assert tn["transition_type"] != "none"
    assert tn["after_anchor"]["scene_id"] == "scene_b"
    assert any("resolution.resolved_transition" in s for s in (tn.get("source_fields") or []))


def test_state_mutations_scene_activates_transition_node() -> None:
    c = _base_ctir()
    c["state_mutations"] = {"scene": {"activate_scene_id": "scene_b"}}
    plan = build_narrative_plan(ctir=c)
    tn = plan["transition_node"]
    assert tn["transition_required"] is True
    assert tn["after_anchor"]["scene_id"] == "scene_b"
    assert any("state_mutations.scene" in s for s in (tn.get("source_fields") or []))


def test_time_skip_creates_time_anchors() -> None:
    c = _base_ctir()
    c["resolution"] = {
        "kind": "custom",
        "metadata": {
            "transition_type": "time_skip",
            "time_anchor_before": "day:3:night",
            "time_anchor_after": "day:4:dawn",
        },
    }
    plan = build_narrative_plan(ctir=c)
    tn = plan["transition_node"]
    assert tn["transition_required"] is True
    assert tn["transition_type"] == "time_skip"
    assert tn["before_anchor"]["time_anchor"] == "day:3:night"
    assert tn["after_anchor"]["time_anchor"] == "day:4:dawn"


def test_no_transition_signal_produces_none_type() -> None:
    c = _base_ctir()
    plan = build_narrative_plan(ctir=c)
    tn = plan["transition_node"]
    assert tn["transition_required"] is False
    assert tn["transition_type"] == "none"
    assert tn["before_anchor"] is None
    assert tn["after_anchor"] is None


def test_transition_node_rejects_prose_keys() -> None:
    c = _base_ctir()
    plan = build_narrative_plan(ctir=c)
    tampered = copy.deepcopy(plan)
    tampered["transition_node"]["prompt"] = "FORBIDDEN"  # banned key anywhere in plan tree
    err = validate_narrative_plan(tampered, strict=True)
    assert err and "banned_key_path" in err

