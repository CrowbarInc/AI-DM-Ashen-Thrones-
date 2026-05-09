"""Caller-boundary provenance tests for legacy diegetic fallback renderers."""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
from game.diegetic_fallback_narration import (
    fallback_template_metadata,
    render_observe_perception_fallback_line,
)
from game.final_emission_meta import read_final_emission_meta_dict
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    LEGACY_DIEGETIC_FALLBACK,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    RETRY_TERMINAL_FALLBACK,
)
from tests.test_final_emission_gate import EXPECTED_FRONTIER_GATE_OPENING_FALLBACK, _opening_gm_output

pytestmark = pytest.mark.unit


def _watch_post_env() -> dict:
    return {
        "scene": {
            "id": "watch_post",
            "location": "Watch Post",
            "visible_facts": ["Torchlight trembles on rain-slick merlons above the gate."],
        }
    }


def _assert_known_family(value: str) -> None:
    assert value in FALLBACK_FAMILIES


def test_direct_diegetic_renderer_returns_text_without_forcing_provenance_metadata() -> None:
    line = render_observe_perception_fallback_line(
        _watch_post_env(),
        seed_key="unit|metadata",
        player_text="I look around.",
    )

    assert line == "As you watch the scene, torchlight trembles on rain-slick merlons above the gate."
    assert not isinstance(line, dict)

    template_meta = fallback_template_metadata("observe_perception_fallback")
    assert template_meta == {"fallback_family": "observe", "temporal_frame": "reinspection"}
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in template_meta


def test_retry_terminal_caller_labels_selected_diegetic_fallback_with_retry_family() -> None:
    import game.gm  # noqa: F401 - initialize gm before importing gm_retry to avoid circular collection imports.
    from game.gm_retry import _nonsocial_forced_retry_progress_line, force_terminal_retry_fallback

    env = _watch_post_env()
    expected_line = _nonsocial_forced_retry_progress_line(
        "I look around.",
        scene_envelope=env,
        session={},
        world={},
        resolution={"kind": "observe", "prompt": "I look around."},
    )

    out = force_terminal_retry_fallback(
        session={"active_scene_id": "watch_post"},
        original_text="",
        failure={"failure_class": "scene_stall", "reasons": ["empty"]},
        retry_failures=[],
        player_text="I look around.",
        scene_envelope=env,
        world={},
        resolution={"kind": "observe", "prompt": "I look around."},
        base_gm={"player_facing_text": "", "tags": [], "metadata": {}},
    )

    assert out["player_facing_text"] == expected_line
    family = out[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == RETRY_TERMINAL_FALLBACK
    assert family != LEGACY_DIEGETIC_FALLBACK
    assert out["metadata"][REALIZATION_FALLBACK_FAMILY_FIELD] == RETRY_TERMINAL_FALLBACK


def test_final_emission_opening_repair_debug_labels_legacy_diegetic_fallback_boundary() -> None:
    text, debug = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=_opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert debug.get("response_type_repair_kind") == "opening_deterministic_fallback"
    assert debug.get("fallback_family_used") == "scene_opening"
    family = debug[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == LEGACY_DIEGETIC_FALLBACK


def test_final_emission_opening_repair_carries_legacy_diegetic_family_to_fem() -> None:
    gm_output = _opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = feg.apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert fem.get("final_route") == "accept_candidate"
    assert fem.get("final_emitted_source") == "opening_deterministic_fallback"
    assert fem.get("fallback_family_used") == "scene_opening"
    family = fem[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == LEGACY_DIEGETIC_FALLBACK
    assert family != GATE_TERMINAL_REPAIR


def test_valid_final_emission_candidate_does_not_gain_diegetic_fallback_family() -> None:
    candidate = (
        "You stand in the churned mud before Cinderwatch's eastern gate as rain spatters soot-dark stone. "
        "Refugees press shoulder to shoulder around the wagon line while guards hold the choke. "
        "You can read the notice board or approach the guards."
    )
    gm_output = _opening_gm_output()
    gm_output["player_facing_text"] = candidate
    gm_output["tags"] = []
    out = feg.apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == candidate
    assert fem.get("final_route") != "replaced"
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) != LEGACY_DIEGETIC_FALLBACK
