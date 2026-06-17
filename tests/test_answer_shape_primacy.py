"""Answer-shape primacy (ASP) gate-layer ownership coverage.

ASP heuristics and boundary apply live on ``game.final_emission_answer_shape_primacy``.
Gate-integration ASP pins remain in ``tests/test_player_facing_narration_purity.py`` and
orchestration order coverage in ``tests/test_final_emission_gate.py``."""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
from game.final_emission_answer_shape_primacy import (
    answer_shape_primacy_applies,
    apply_answer_shape_primacy_layer,
    validate_answer_shape_primacy,
)

pytestmark = pytest.mark.unit


def test_validate_answer_shape_primacy_passes_clean_observation():
    text = "Rain hammers the slate roof; torchlight shivers in the gutter below."
    out = validate_answer_shape_primacy(
        text,
        player_input="I look around the street.",
        resolution={"kind": "observe"},
        response_type_debug={"response_type_required": "neutral_narration"},
    )
    assert out["passed"] is True
    assert out["failure_reasons"] == []


def test_validate_answer_shape_primacy_fails_pressure_monologue_without_payload():
    text = (
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps."
    )
    out = validate_answer_shape_primacy(
        text,
        player_input="What do I see on the street?",
        resolution={"kind": "observe"},
        response_type_debug={"response_type_required": "neutral_narration"},
    )
    assert out["passed"] is False
    assert "missing_observation_or_result_payload" in out["failure_reasons"]


def test_validate_answer_shape_primacy_fails_pressure_before_payload():
    text = (
        "The ward's tension mounts; confrontation feels inevitable. "
        "You hear boots on wet cobbles to your left, uneven and hurried."
    )
    out = validate_answer_shape_primacy(
        text,
        player_input="I listen for movement.",
        resolution={"kind": "observe"},
        response_type_debug={"response_type_required": "neutral_narration"},
    )
    assert out["passed"] is False
    assert "pressure_or_consequence_before_payload" in out["failure_reasons"]
    assert out["repairable_pressure_lead"] is True


def test_answer_shape_primacy_applies_for_neutral_narration_response_type():
    assert answer_shape_primacy_applies(
        resolution={"kind": "social"},
        response_type_debug={"response_type_required": "neutral_narration"},
        strict_social_details=None,
    )


def test_answer_shape_primacy_applies_skips_strict_social():
    assert not answer_shape_primacy_applies(
        resolution={"kind": "observe"},
        response_type_debug={"response_type_required": "neutral_narration"},
        strict_social_details={"active": True},
    )


def test_bj36_apply_answer_shape_primacy_layer_boundary_no_rewrite_on_failure():
    text = (
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps."
    )
    out_text, meta, extra = apply_answer_shape_primacy_layer(
        text,
        gm_output={},
        resolution={"kind": "observe", "prompt": "What do I see on the street?"},
        session={},
        scene_id="market_square",
        response_type_debug={
            "response_type_required": "neutral_narration",
            "response_type_candidate_ok": True,
        },
        strict_social_details=None,
    )
    assert out_text == text
    assert meta.get("answer_shape_primacy_failed") is True
    assert meta.get("answer_shape_primacy_repaired") is False
    assert "answer_shape_primacy_violation" in extra


def test_bj84_gate_delegator_removed_stacks_call_owner_directly() -> None:
    """BJ-84: gate delegator removed; stacks call answer_shape_primacy owner directly."""
    import inspect

    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    assert not hasattr(feg, "_apply_answer_shape_primacy_layer")
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_answer_shape_primacy_layer(" in nss_src
    assert "apply_answer_shape_primacy_layer(" in ss_src
    assert "feg._apply_answer_shape_primacy_layer" not in nss_src
    assert "feg._apply_answer_shape_primacy_layer" not in ss_src
