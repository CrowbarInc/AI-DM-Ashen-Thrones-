"""CF5 — fallback-family integration tests through canonical projection assembler."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_fixtures import (
    fem_payload,
    minimal_gm_output_payload,
    minimal_turn_payload,
    observed_turn_from_gate_output,
    project_synthetic_turn,
)
from tests.helpers.golden_replay_projection import (
    REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS,
    dual_fallback_family_replay_precedence_surface,
    lookup_observation_path,
    project_replay_fallback_family_from_fem,
    project_turn_observation,
    protected_observation_drift_bucket,
)
from tests.helpers.opening_fallback_evidence import opening_dual_family_fem_meta

pytestmark = pytest.mark.unit


def test_golden_replay_dual_family_projection_prefers_diegetic_fallback_family_used() -> None:
    """Read-side ``fallback_family`` prefers diegetic taxonomy when both FEM fields are present."""
    fem = opening_dual_family_fem_meta(realization_family="upstream_prepared_emission")
    assert project_replay_fallback_family_from_fem(fem) == "scene_opening"

    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_diegetic_first",
            gm_text="Rain on the gate road.",
            fem_meta=fem,
        )
    )
    assert turn["fallback_family"] == "scene_opening"
    assert "fallback_family_used" in turn["fem_raw_keys"]
    assert "realization_fallback_family" in turn["fem_raw_keys"]


def test_golden_replay_dual_family_projection_falls_back_to_realization_when_diegetic_absent() -> None:
    """Read-side projection uses governed provenance only when diegetic field is absent."""
    fem = {"realization_fallback_family": "upstream_prepared_emission"}
    assert project_replay_fallback_family_from_fem(fem) == "upstream_prepared_emission"

    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_realization_fallback",
            gm_text="The notice board creaks.",
            fem_meta=fem,
        )
    )
    assert turn["fallback_family"] == "upstream_prepared_emission"


def test_golden_replay_dual_family_projection_returns_none_when_both_absent() -> None:
    """Read-side projector returns None when neither FEM family field is present."""
    assert project_replay_fallback_family_from_fem({}) is None
    assert project_replay_fallback_family_from_fem({"final_emitted_source": "generated_candidate"}) is None

    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_both_absent",
            gm_text="The lane stays quiet.",
            fem_meta={"final_emitted_source": "generated_candidate"},
        )
    )
    assert turn["fallback_family"] is None
    assert "fallback_family" in turn["unavailable"]


def test_golden_replay_dual_family_precedence_surface_documents_read_side_rule() -> None:
    surface = dual_fallback_family_replay_precedence_surface()
    assert surface["prefer_field"] == "fallback_family_used"
    assert surface["fallback_field"] == "realization_fallback_family"
    assert surface["precedence_keys"] == list(REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS)
    assert surface["read_side_only"] is True
    assert project_replay_fallback_family_from_fem(
        {"fallback_family_used": "social", "realization_fallback_family": "gate_terminal_repair"}
    ) == "social"


def test_golden_replay_dual_family_projection_does_not_rewrite_raw_fem_fields() -> None:
    """Projection must not collapse or rewrite runtime FEM dual-family stamps."""
    raw_fem = opening_dual_family_fem_meta(realization_family="upstream_prepared_emission")
    payload = minimal_gm_output_payload(fem_meta=raw_fem)
    project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_no_rewrite",
            gm_text="Torchlight on wet stone.",
            payload=payload,
        )
    )
    stored = payload["gm_output"]["_final_emission_meta"]
    assert stored["fallback_family_used"] == "scene_opening"
    assert stored["realization_fallback_family"] == "upstream_prepared_emission"


def test_observed_turn_from_gate_output_projects_direct_seam_fields() -> None:
    """Direct-seam helper uses canonical projection and supports extra assertion fields."""
    raw_fem = opening_dual_family_fem_meta(realization_family="upstream_prepared_emission")
    gm_output = {
        "player_facing_text": "Rain on the gate.",
        "_final_emission_meta": dict(raw_fem),
    }
    turn = observed_turn_from_gate_output(
        scenario_id="direct_seam_helper_probe",
        gm_output=gm_output,
        extra_fields={"dialogue_plan_valid": True},
    )
    assert turn["final_text"] == "Rain on the gate."
    assert turn["final_emitted_source"] == "opening_deterministic_fallback"
    assert turn["fallback_family"] == "scene_opening"
    assert "fallback_family_used" in turn["fem_raw_keys"]
    assert "realization_fallback_family" in turn["fem_raw_keys"]
    assert turn["dialogue_plan_valid"] is True
    stored = gm_output["_final_emission_meta"]
    assert stored["fallback_family_used"] == "scene_opening"
    assert stored["realization_fallback_family"] == "upstream_prepared_emission"


def test_ak5_complex_projection_contracts_remain_locked():
    """Dual fallback-family, dotted trace lookup, and semantic drift bucket stay explicit."""
    fem = opening_dual_family_fem_meta(realization_family="upstream_prepared_emission")
    assert project_replay_fallback_family_from_fem(fem) == "scene_opening"

    observed = project_synthetic_turn(
        scenario_id="ak5_complex_projection",
        gm_text="planner scaffold leaked into final text",
        payload={
            **minimal_gm_output_payload(fem_meta=fem_payload(**fem)),
            "debug_traces": [
                {
                    "canonical_entry": {
                        "target_actor_id": "runner",
                        "target_source": "social",
                        "reason": "direct",
                    },
                    "turn_trace": {
                        "social_contract_trace": {"route_selected": "dialogue"},
                    },
                }
            ],
        },
    )

    assert observed["fallback_family"] == "scene_opening"
    assert lookup_observation_path(observed, "trace.canonical_entry.target_actor_id") == "runner"
    assert lookup_observation_path(observed, "trace.canonical_entry.target_source") == "social"
    assert lookup_observation_path(observed, "trace.canonical_entry.reason") == "direct"
    assert lookup_observation_path(observed, "trace.social_contract_trace.route_selected") == "dialogue"
    assert observed["scaffold_leakage"] is True
    assert protected_observation_drift_bucket("scaffold_leakage") == "semantic_drift"
    assert protected_observation_drift_bucket("fallback_family") == "structural_drift"
