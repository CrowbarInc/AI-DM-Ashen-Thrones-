"""CF5 — metadata and sanitizer projection tests through canonical assembler."""
from __future__ import annotations

import pytest

from game.ownership_projection_views import (
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
)

from tests.helpers.golden_replay_fixtures import (
    fem_payload,
    minimal_gm_output_payload,
    minimal_turn_payload,
    project_synthetic_turn,
)
from tests.helpers.golden_replay_projection import (
    lookup_observation_path,
    project_turn_observation,
    protected_path_representation_errors,
)
from tests.helpers.golden_replay_projection_test_support import ak5_rich_projection_payload
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED

pytestmark = pytest.mark.unit


def test_bl2_representative_projected_observed_turns_unchanged():
    """Lock representative fixture projections after registry-driven flat assembly."""
    sparse = project_turn_observation(
        minimal_turn_payload(
            scenario_id="bl2_sparse_projection",
            gm_text="Rain on the gate road.",
        )
    )
    assert sparse["resolution_kind"] is None
    assert sparse["route_kind"] is None
    assert sparse["selected_speaker_id"] is None
    assert sparse["fallback_family"] is None
    assert sparse["scaffold_leakage"] is False
    assert sparse["final_text"] == "Rain on the gate road."
    assert protected_path_representation_errors(sparse) == []

    rich = project_synthetic_turn(
        scenario_id="bl2_rich_projection",
        gm_text="The runner says the patrol moved east.",
        player_text="Ask the runner.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        payload=ak5_rich_projection_payload(),
    )
    assert rich["final_emitted_source"] == "upstream_prepared_emission"
    assert rich["fallback_family"] == "social"
    assert rich["opening_fallback_authorship_source"] == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    assert rich["sanitizer_lineage_mode"] == "strip_only"
    assert lookup_observation_path(rich, "trace.canonical_entry.target_actor_id") == "runner"
    assert lookup_observation_path(rich, "trace.social_contract_trace.route_selected") == "dialogue"
    assert protected_path_representation_errors(rich) == []


def test_ak5_synthetic_turn_exercises_fem_backed_protected_fields():
    observed = project_synthetic_turn(
        scenario_id="ak5_fem_backed_projection",
        gm_text="The runner confirms the patrol route.",
        resolution={"kind": "question"},
        fem_meta=fem_payload(
            final_emitted_source="upstream_prepared_emission",
            response_type_required="dialogue_response",
            response_type_repair_used=True,
            response_type_repair_kind="dialogue_minimal_repair",
            fallback_temporal_frame="present",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
        ),
    )

    assert observed["final_emitted_source"] == "upstream_prepared_emission"
    assert observed["response_type_required"] == "dialogue_response"
    assert observed["response_type_repair_used"] is True
    assert observed["response_type_repair_kind"] == "dialogue_minimal_repair"
    assert observed["fallback_temporal_frame"] == "present"
    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is True


def test_ak5_synthetic_turn_exercises_sanitizer_backed_protected_fields():
    observed = project_synthetic_turn(
        scenario_id="ak5_sanitizer_backed_projection",
        gm_text="For a breath, the scene stays still.",
        resolution={"kind": "observe"},
        payload={
            **minimal_gm_output_payload(
                fem_meta=fem_payload(final_emitted_source="generated_candidate"),
                metadata={
                    "sanitizer_trace": {
                        "sanitizer_lineage_mode": "strip_only",
                        "sanitizer_empty_fallback_used": True,
                        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                        "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                        SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                        "sanitizer_lineage_changed_count": 2,
                        "sanitizer_lineage_dropped_count": 1,
                    }
                },
            ),
            "sanitizer_debug": [
                {"event": "strip_only_dropped_rewrite_candidate", "sentence": "Planner scaffold."},
                {"event": "strip_only_dropped_non_diegetic", "sentence": "Validator scaffold."},
            ],
        },
    )

    assert observed["sanitizer_empty_fallback_used"] is True
    assert observed["sanitizer_empty_fallback_source"] == "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"
    assert observed["sanitizer_empty_fallback_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 2
    assert observed["sanitizer_lineage_dropped_count"] == 1


def test_golden_observed_turn_projects_response_delta_metadata():
    observed = project_synthetic_turn(
        scenario_id="response_delta_projection",
        gm_text="The runner adds a new location lead.",
        fem_meta=fem_payload(
            response_delta_checked=True,
            response_delta_failed=True,
            response_delta_repaired=False,
            response_delta_kind_detected="new_actionable_lead",
            response_delta_echo_overlap_ratio=0.2,
            response_delta_trigger_source="strict_social_answer_pressure",
        ),
    )

    assert observed["response_delta_checked"] is True
    assert observed["response_delta_failed"] is True
    assert observed["response_delta_repaired"] is False
    assert observed["response_delta_kind"] == "new_actionable_lead"
    assert observed["response_delta_echo_overlap_ratio"] == 0.2
    assert observed["response_delta_echo_overlap_band"] == "low"
    assert observed["response_delta_trigger_source"] == "strict_social_answer_pressure"


def test_golden_observed_turn_projects_clean_sanitizer_lineage():
    observed = project_synthetic_turn(
        scenario_id="sanitizer_clean_lineage",
        gm_text="Rain needles across the checkpoint.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(final_emitted_source="generated_candidate"),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "strip_only",
                    "sanitizer_lineage_changed_count": 0,
                    "sanitizer_lineage_dropped_count": 0,
                    "sanitizer_lineage_empty_fallback_used": False,
                    "sanitizer_lineage_legacy_rewrite_active": False,
                }
            },
        ),
    )

    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 0
    assert observed["sanitizer_lineage_dropped_count"] == 0
    assert observed["sanitizer_lineage_empty_fallback_used"] is False
    assert observed["sanitizer_lineage_legacy_rewrite_active"] is False


def test_golden_observed_turn_projects_sanitizer_lineage_from_debug_events():
    observed = project_synthetic_turn(
        scenario_id="sanitizer_debug_lineage",
        gm_text="",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(final_emitted_source="generated_candidate"),
            metadata={
                "sanitizer_trace": {"sanitizer_boundary_mode": "strip_only"},
                "sanitizer_debug": [
                    {"event": "strip_only_dropped_rewrite_candidate", "sentence": "Validator scaffold."},
                    {"event": "strip_only_dropped_non_diegetic", "sentence": "Planner scaffold."},
                ],
            },
        ),
    )

    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 2
    assert observed["sanitizer_lineage_dropped_count"] == 2


def test_golden_observed_turn_projects_legacy_sanitizer_lineage():
    observed = project_synthetic_turn(
        scenario_id="sanitizer_legacy_lineage",
        gm_text="The answer has not formed yet.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(final_emitted_source="generated_candidate"),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "legacy_sentence_rewrite",
                    "sanitizer_lineage_changed_count": 1,
                    "sanitizer_lineage_dropped_count": 0,
                    "sanitizer_lineage_empty_fallback_used": False,
                    "sanitizer_lineage_legacy_rewrite_active": True,
                }
            },
        ),
    )

    assert observed["sanitizer_lineage_mode"] == "legacy_sentence_rewrite"
    assert observed["sanitizer_lineage_legacy_rewrite_active"] is True
