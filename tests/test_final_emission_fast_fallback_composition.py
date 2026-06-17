"""Owner tests for fast-fallback neutral opening composition helpers.

Direct owner for ``game.final_emission_fast_fallback_composition``. Layer
orchestration and gate integration remain in ``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

import game.final_emission_fast_fallback_composition as fast_fallback_composition
from game.defaults import default_scene, default_session


def _ssa_contract(**overrides: object) -> dict:
    base = {
        "enabled": True,
        "scene_id": "frontier_gate",
        "scene_location_label": "Frontier Gate",
        "location_tokens": ["frontier gate", "gate", "checkpoint"],
        "actor_tokens": ["emergent lord aldric"],
    }
    base.update(overrides)
    return base


def test_default_fast_fallback_neutral_composition_meta_keys() -> None:
    meta = fast_fallback_composition.default_fast_fallback_neutral_composition_meta()

    assert meta == {
        "fast_fallback_neutral_composition_checked": False,
        "fast_fallback_neutral_composition_applicable": False,
        "fast_fallback_neutral_composition_malformed_detected": False,
        "fast_fallback_neutral_composition_failure_reasons": [],
        "fast_fallback_neutral_composition_repaired": False,
        "fast_fallback_neutral_composition_repair_mode": None,
    }


def test_apply_fast_fallback_neutral_composition_layer_not_applicable_passthrough() -> None:
    text = "Rain darkens the flagstones around the checkpoint."
    session = default_session()
    session["turn_counter"] = 5
    session["visited_scene_ids"] = ["frontier_gate"]

    out_text, meta = fast_fallback_composition.apply_fast_fallback_neutral_composition_layer(
        text,
        gm_output={"tags": ["upstream_api_fast_fallback"]},
        session=session,
        scene=default_scene("frontier_gate"),
        scene_id="frontier_gate",
        strict_social_active=False,
    )

    assert out_text == text
    assert meta["fast_fallback_neutral_composition_checked"] is False
    assert meta["fast_fallback_neutral_composition_applicable"] is False


def test_apply_fast_fallback_neutral_composition_layer_detects_malformed_without_repair() -> None:
    session = default_session()
    session["turn_counter"] = 0
    session["visited_scene_ids"] = ["frontier_gate"]
    gm_output = {
        "scene_state_anchor_contract": _ssa_contract(),
        "tags": ["upstream_api_fast_fallback"],
    }
    text = (
        "Emergent Lord Aldric Several patrons exchange furtive glances. "
        "The rain holds; beside it, a notice board lists a missing patrol."
    )

    out_text, meta = fast_fallback_composition.apply_fast_fallback_neutral_composition_layer(
        text,
        gm_output=gm_output,
        session=session,
        scene=default_scene("frontier_gate"),
        scene_id="frontier_gate",
        strict_social_active=False,
    )

    assert out_text == text
    assert meta["fast_fallback_neutral_composition_checked"] is True
    assert meta["fast_fallback_neutral_composition_applicable"] is True
    assert meta["fast_fallback_neutral_composition_malformed_detected"] is True
    assert "bare_actor_header" in meta["fast_fallback_neutral_composition_failure_reasons"]
    assert "fact_fragment_collision" in meta["fast_fallback_neutral_composition_failure_reasons"]
    assert meta["fast_fallback_neutral_composition_repaired"] is False
    assert meta["fast_fallback_neutral_composition_repair_mode"] is None
    assert meta["fast_fallback_neutral_composition_boundary_semantic_repair_disabled"] is True


def test_fast_fallback_neutral_composition_applicable_requires_opening_and_tags() -> None:
    session = default_session()
    session["turn_counter"] = 0
    session["visited_scene_ids"] = ["frontier_gate"]
    gm_output = {"tags": ["upstream_api_fast_fallback"]}

    assert fast_fallback_composition._fast_fallback_neutral_composition_applicable(
        gm_output,
        session=session,
        strict_social_active=False,
    )
    assert not fast_fallback_composition._fast_fallback_neutral_composition_applicable(
        gm_output,
        session=session,
        strict_social_active=True,
    )
    session["turn_counter"] = 5
    assert not fast_fallback_composition._fast_fallback_neutral_composition_applicable(
        gm_output,
        session=session,
        strict_social_active=False,
    )


def test_fast_fallback_neutral_composition_failure_reasons_detects_malformed_patterns() -> None:
    gm_output = {
        "scene_state_anchor_contract": _ssa_contract(),
        "tags": ["upstream_api_fast_fallback"],
    }
    text = (
        "Emergent Lord Aldric Several patrons exchange furtive glances. "
        "The rain holds; beside it, a notice board lists a missing patrol."
    )

    reasons = fast_fallback_composition._fast_fallback_neutral_composition_failure_reasons(
        text,
        gm_output=gm_output,
    )

    assert "bare_actor_header" in reasons
    assert "fact_fragment_collision" in reasons


def test_build_fast_fallback_opening_scene_template_composes_summary_and_detail() -> None:
    scene = default_scene("frontier_gate")
    scene["scene"]["summary"] = "A rain-soaked checkpoint holds a nervous crowd at the gate."
    scene["scene"]["visible_facts"] = [
        "Several patrons exchange furtive glances.",
        "Rain darkens the flagstones around the checkpoint.",
    ]
    gm_output = {"scene_state_anchor_contract": _ssa_contract(actor_tokens=[])}

    composed = fast_fallback_composition._build_fast_fallback_opening_scene_template(
        scene,
        gm_output=gm_output,
        scene_id="frontier_gate",
    )

    low = composed.lower()
    assert "rain-soaked checkpoint" in low
    assert "patrons" in low or "furtive" in low


def test_fast_fallback_opening_detail_candidates_skip_bad_join_fragments() -> None:
    scene = default_scene("frontier_gate")
    scene["scene"]["visible_facts"] = [
        "The rain holds; beside it, a notice board lists a missing patrol.",
        "Several patrons exchange furtive glances.",
    ]

    details = fast_fallback_composition._fast_fallback_opening_detail_candidates(scene, gm_output=None)

    assert details == ["Several patrons exchange furtive glances."]


def test_bj86_gate_delegator_removed_stacks_call_owner_directly() -> None:
    """BJ-86: gate delegator removed; stacks call fast_fallback_composition owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    assert not hasattr(feg, "_apply_fast_fallback_neutral_composition_layer")
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_fast_fallback_neutral_composition_layer(" in nss_src
    assert "apply_fast_fallback_neutral_composition_layer(" in ss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in nss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in ss_src
