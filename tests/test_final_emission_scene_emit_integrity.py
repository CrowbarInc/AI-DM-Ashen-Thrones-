"""Owner tests for scene emit integrity global fallback selection helpers.

Direct owner for ``game.final_emission_scene_emit_integrity``. Gate fallback
ordering and integration remain in ``tests/test_final_emission_gate.py`` and
``tests/test_final_emission_scene_integrity.py``.
"""

from __future__ import annotations

import game.final_emission_scene_emit_integrity as scene_emit_integrity
from game.final_emission_visibility_fallback import VisibilitySelectedFallback


def test_scene_emit_integrity_global_fallback_selection_returns_canonical_dataclass() -> None:
    scene = {"scene": {"id": "yard", "visible_facts": ["A guard watches the gate."]}}
    selection_kwargs = {
        "authoritative_resolution": None,
        "session": None,
        "world": None,
        "res_kind": "observe",
        "response_type_required": "narration",
    }
    selected = scene_emit_integrity._scene_emit_integrity_global_fallback_selection(
        scene,
        "yard",
        **selection_kwargs,
    )
    assert isinstance(selected, VisibilitySelectedFallback)
    assert selected.final_emitted_source == "global_scene_fallback"
    assert selected.fallback_pool == "global_scene_narrative"
    assert selected.fallback_kind == "narrative_safe_fallback"
    assert selected.fallback_strategy == "standard_safe_fallback"
    assert selected.fallback_candidate_source == "global_scene_fallback"
    assert selected.text


def test_scene_emit_integrity_travelish_context_detects_travel_resolution_kind() -> None:
    assert scene_emit_integrity._scene_emit_integrity_travelish_context(
        res_kind="travel",
        response_type_required="narration",
        authoritative_resolution=None,
    )
    assert not scene_emit_integrity._scene_emit_integrity_travelish_context(
        res_kind="observe",
        response_type_required="narration",
        authoritative_resolution=None,
    )


def test_scene_emit_integrity_global_fallback_selection_uses_safe_line_on_failure() -> None:
    scene = {"scene": {"id": "frontier_gate"}}
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": False,
        "metadata": {
            "blocked_incompatible_scene_transition": True,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": False,
        },
    }
    selected = scene_emit_integrity._scene_emit_integrity_global_fallback_selection(
        scene,
        "frontier_gate",
        authoritative_resolution=resolution,
        session={"active_scene_id": "frontier_gate"},
        world=None,
        res_kind="scene_transition",
        response_type_required="narration",
    )

    assert selected.final_emitted_source == "scene_emit_integrity_safe_fallback"
    assert selected.fallback_pool == "scene_emit_integrity_neutral"
    assert selected.fallback_kind == "scene_emit_integrity_safe_fallback"
    assert selected.fallback_candidate_source == "scene_emit_integrity_safe_fallback"
    assert selected.text == scene_emit_integrity._SCENE_EMIT_INTEGRITY_SAFE_FALLBACK_LINE


def test_compute_scene_emit_integrity_assessment_marks_blocked_global_fallback() -> None:
    resolution = {
        "kind": "scene_transition",
        "metadata": {"blocked_incompatible_scene_transition": True},
    }
    bundle = scene_emit_integrity._compute_scene_emit_integrity_assessment(
        authoritative_resolution=resolution,
        session={"active_scene_id": "frontier_gate"},
        scene={"scene": {"id": "frontier_gate"}},
        scene_id="frontier_gate",
        res_kind="scene_transition",
        response_type_required="narration",
    )

    assert bundle["scene_integrity_checked"] is True
    assert bundle["scene_integrity_passed"] is False
    assert bundle["scene_integrity_blocked_global_fallback"] is True
    assert "blocked_incompatible_scene_transition" in bundle["scene_integrity_failure_reasons"]
