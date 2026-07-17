"""CL5 semantic mutation projection policy locks."""
from __future__ import annotations

import json

import pytest

from tests.helpers.golden_replay_fixtures import minimal_turn_payload
from tests.helpers.golden_replay_projection import (
    project_semantic_mutation_summary as facade_project_semantic_mutation_summary,
    project_turn_observation,
    protected_observation_field_paths,
)
from tests.helpers.golden_replay_projection_extractors import (
    project_semantic_mutation_summary as extractor_project_semantic_mutation_summary,
)
from tests.helpers.golden_replay_projection_semantic import project_semantic_mutation_summary

pytestmark = pytest.mark.unit


_SEMANTIC_TRACE = {
    "first_semantic_mutation_bucket": "narrative_authenticity",
    "first_semantic_mutation_source": "stage_diff",
    "first_semantic_mutation_checkpoint_id": "checkpoint-7",
    "first_semantic_mutation_sequence": 3,
    "semantic_mutation_changed_count": 2,
    "semantic_mutation_unknown_count": 1,
    "semantic_mutation_risk_score": 40,
    "semantic_mutation_risk_band": "medium",
    "semantic_mutation_trace_complete": False,
    "trace_continuity": None,
    "semantic_mutation_trace": [{"sequence": 3}],
    "first_semantic_mutation_owner": "not projected by replay summary",
}


def test_cl5_semantic_summary_projection_shape_locked() -> None:
    expected = {
        "first_semantic_mutation_bucket": "narrative_authenticity",
        "first_semantic_mutation_source": "stage_diff",
        "first_semantic_mutation_checkpoint_id": "checkpoint-7",
        "first_semantic_mutation_sequence": 3,
        "semantic_mutation_changed_count": 2,
        "semantic_mutation_unknown_count": 1,
        "semantic_mutation_risk_score": 40,
        "semantic_mutation_risk_band": "medium",
        "semantic_mutation_trace_complete": False,
        "trace_continuity": None,
    }
    assert project_semantic_mutation_summary(_SEMANTIC_TRACE) == expected
    assert json.dumps(project_semantic_mutation_summary(_SEMANTIC_TRACE), sort_keys=True) == json.dumps(
        expected,
        sort_keys=True,
    )


def test_cl5_semantic_summary_compatibility_imports_are_same_callable() -> None:
    assert extractor_project_semantic_mutation_summary is project_semantic_mutation_summary
    assert facade_project_semantic_mutation_summary is project_semantic_mutation_summary


def test_cl5_semantic_summary_ignores_missing_or_none_optional_values() -> None:
    assert project_semantic_mutation_summary(None) == {}
    assert project_semantic_mutation_summary({"semantic_mutation_trace_complete": None}) == {
        "semantic_mutation_trace_complete": None,
    }
    assert project_semantic_mutation_summary(
        {
            "first_semantic_mutation_bucket": None,
            "semantic_mutation_changed_count": 0,
            "trace_continuity": False,
        }
    ) == {
        "semantic_mutation_changed_count": 0,
        "trace_continuity": False,
    }


def test_cl5_project_turn_observation_semantic_output_locked() -> None:
    observed = project_turn_observation(
        {
            **minimal_turn_payload(
                scenario_id="cl5_semantic_projection",
                gm_text="The road bends toward the gate.",
            ),
            "semantic_mutation_trace": _SEMANTIC_TRACE,
        }
    )
    summary = project_semantic_mutation_summary(_SEMANTIC_TRACE)
    assert {key: observed.get(key) for key in summary} == summary
    assert "semantic_mutation_trace" not in observed
    assert "first_semantic_mutation_owner" not in observed


def test_semantic_mutation_write_sites_project_diagnostically_not_protected() -> None:
    write_site = {
        "mutation_id": "abc123",
        "write_site_family": "fallback",
        "write_site_file": "game/final_emission_sealed_fallback.py",
        "write_site_function": "prepare_sealed_replacement_route_meta",
        "before_semantic_hash": "beforehash",
        "after_semantic_hash": "afterhash",
        "selected_active_stream": True,
        "candidate_only": False,
    }
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cu2_write_site_projection",
            gm_text="The road bends toward the gate.",
            fem_meta={"semantic_mutation_write_sites": [write_site]},
        )
    )

    assert observed["semantic_mutation_write_sites"] == [write_site]
    assert "semantic_mutation_write_sites" not in protected_observation_field_paths()


def test_cu3_projection_prefers_explicit_write_site_attribution() -> None:
    write_site = {
        "write_site_family": "fallback",
        "write_site_file": "game/fallback_provenance_debug.py",
        "write_site_function": "finalize_upstream_fallback_overwrite_containment",
        "owner": "game.fallback_provenance_debug",
        "before_semantic_hash": "before",
        "after_semantic_hash": "after",
        "selected_active_stream": True,
        "candidate_only": False,
    }

    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cu3_write_site_wins",
            gm_text="fallback text",
            fem_meta={"semantic_mutation_write_sites": [write_site]},
            semantic_mutation_trace={
                "first_semantic_mutation_bucket": "sanitizer",
                "first_semantic_mutation_source": "projected.sanitizer",
                "first_semantic_mutation_owner": "game.output_sanitizer",
            },
        )
    )

    assert observed["first_write_family"] == "fallback"
    assert observed["first_write_owner"] == "game.fallback_provenance_debug"
    assert observed["authoritative_mutation_owner"] == "game.fallback_provenance_debug"
    assert observed["authoritative_mutation_family"] == "fallback"
    assert observed["authoritative_evidence_source"] == "write_site"
    assert observed["used_projection_inference"] is False
    assert observed["first_semantic_mutation_bucket"] == "sanitizer"


def test_cu3_projection_falls_back_to_legacy_inference_without_write_site() -> None:
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cu3_projection_inference",
            gm_text="projected text",
            semantic_mutation_trace={
                "first_semantic_mutation_bucket": "sanitizer",
                "first_semantic_mutation_source": "projected.sanitizer",
                "first_semantic_mutation_owner": "game.output_sanitizer",
            },
        )
    )

    assert observed["authoritative_mutation_owner"] is None
    assert observed["authoritative_mutation_family"] == "sanitizer"
    assert observed["authoritative_evidence_source"] == "projection_inference"
    assert observed["used_projection_inference"] is True


def test_cu3_projection_selects_no_authoritative_mutation_when_no_evidence() -> None:
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cu3_no_mutation",
            gm_text="unchanged text",
        )
    )

    assert observed["authoritative_mutation_owner"] is None
    assert observed["authoritative_mutation_family"] is None
    assert observed["authoritative_write_site"] is None
    assert observed["authoritative_evidence_source"] is None
    assert observed["used_projection_inference"] is False


def test_cu4_projection_exposes_prompt_and_policy_write_diagnostics() -> None:
    prompt_write = {
        "write_site_family": "prompt",
        "write_site_file": "game/upstream_response_repairs.py",
        "write_site_function": "apply_spoken_state_refinement_cash_out",
        "owner": "game.upstream_response_repairs",
        "selected_active_stream": True,
        "candidate_only": False,
    }
    policy_write = {
        "write_site_family": "policy",
        "write_site_file": "game/response_policy_enforcement.py",
        "write_site_function": "_apply_diegetic_validator_voice_enforcement",
        "owner": "game.response_policy_enforcement",
        "selected_active_stream": True,
        "candidate_only": False,
    }

    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cu4_prompt_policy_projection",
            gm_text="projected text",
            fem_meta={"semantic_mutation_write_sites": [prompt_write, policy_write]},
        )
    )

    assert observed["first_prompt_write"] == (
        "game/upstream_response_repairs.py:apply_spoken_state_refinement_cash_out"
    )
    assert observed["first_policy_write"] == (
        "game/response_policy_enforcement.py:_apply_diegetic_validator_voice_enforcement"
    )
    assert observed["authoritative_mutation_owner"] == "game.upstream_response_repairs"
    assert "first_prompt_write" not in protected_observation_field_paths()
