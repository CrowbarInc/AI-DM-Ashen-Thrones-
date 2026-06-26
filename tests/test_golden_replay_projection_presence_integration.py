"""CF5 — presence pipeline integration locks (complements test_cf2_protected_field_routing)."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_fixtures import fem_payload, minimal_gm_output_payload, minimal_turn_payload, project_synthetic_turn
from tests.helpers.golden_replay_projection import project_turn_observation
from tests.helpers.golden_replay_projection_presence import (
    _missing_source_by_field_from_presence,
    protected_path_covered_by_unavailable,
)

pytestmark = pytest.mark.unit


def test_bl3_sparse_fixture_presence_pipeline_locked():
    """Unified presence builder preserves sparse-turn unavailable and raw-absent routing."""
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="bl3_sparse_presence",
            gm_text="Rain on the gate road.",
        )
    )
    assert observed["unavailable"] == [
        "fallback_family",
        "final_emitted_source",
        "response_type_candidate_ok",
        "response_type_repair_used",
        "response_type_required",
        "route_kind",
        "selected_speaker_id",
        "trace.canonical_entry",
        "trace.social_contract_trace",
        "trace.turn_trace",
    ]
    assert observed["raw_signal_presence"]["route_kind"] is False
    assert observed["raw_signal_presence"]["fallback_family"] is False
    assert observed["raw_signal_presence"]["trace.canonical_entry"] is False
    assert observed["missing_source_by_field"]["route_kind"] == "runtime_missing_raw_absent"
    assert observed["missing_source_by_field"]["final_emitted_source"] == "runtime_missing_raw_absent"
    assert observed["normalized_signal_presence"]["final_emitted_source"] is False
    assert observed["normalized_signal_presence"]["fallback_family"] is False


def test_bl3_rich_fixture_presence_pipeline_locked():
    """Unified presence builder preserves FEM-backed raw/normalized presence on rich turns."""
    observed = project_synthetic_turn(
        scenario_id="bl3_rich_presence",
        gm_text="The runner says the patrol moved east.",
        player_text="Ask the runner.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        fem_meta=fem_payload(
            final_emitted_source="upstream_prepared_emission",
            response_type_required="dialogue_response",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            fallback_family_used="social",
            realization_fallback_family="upstream_prepared_emission",
        ),
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="upstream_prepared_emission",
                response_type_required="dialogue_response",
                upstream_prepared_emission_used=True,
                upstream_prepared_emission_valid=True,
                fallback_family_used="social",
                realization_fallback_family="upstream_prepared_emission",
            ),
        ),
    )
    assert "fallback_family" not in observed["unavailable"]
    assert observed["raw_signal_presence"]["final_emitted_source"] is True
    assert observed["raw_signal_presence"]["upstream_prepared_emission_used"] is True
    assert observed["raw_signal_presence"]["upstream_prepared_emission_valid"] is True
    assert observed["normalized_signal_presence"]["final_emitted_source"] is True
    assert observed["normalized_signal_presence"]["upstream_prepared_emission_used"] is True
    assert observed["normalized_signal_presence"]["upstream_prepared_emission_valid"] is True
    assert observed["missing_source_by_field"]["final_emitted_source"] == "projection_missing_raw_present"
    assert observed["missing_source_by_field"]["upstream_prepared_emission_used"] == "projection_missing_raw_present"


def test_bl3_trace_fixture_presence_pipeline_locked():
    """Unified presence builder marks trace containers present when debug traces are stamped."""
    observed = project_synthetic_turn(
        scenario_id="bl3_trace_presence",
        gm_text="The runner nods.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        payload={
            **minimal_gm_output_payload(fem_meta=fem_payload(final_emitted_source="generated_candidate")),
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
    assert observed["raw_signal_presence"]["trace.canonical_entry"] is True
    assert observed["raw_signal_presence"]["trace.social_contract_trace"] is True
    assert observed["raw_signal_presence"]["route_kind"] is True
    assert "trace.canonical_entry" not in observed["unavailable"]
    assert "trace.social_contract_trace" not in observed["unavailable"]
    assert observed["missing_source_by_field"]["trace.canonical_entry"] == "projection_missing_raw_present"


@pytest.mark.parametrize(
    "raw_signal,normalized_signal,field,expected",
    [
        (
            {"final_emitted_source": False},
            {},
            "final_emitted_source",
            "runtime_missing_raw_absent",
        ),
        (
            {"final_emitted_source": True},
            {"final_emitted_source": True},
            "final_emitted_source",
            "projection_missing_raw_present",
        ),
        (
            {"final_emitted_source": True},
            {"final_emitted_source": False},
            "final_emitted_source",
            "normalized_view_missing_raw_present",
        ),
    ],
)
def test_cl2_presence_missing_source_labels_locked(
    raw_signal: dict[str, bool],
    normalized_signal: dict[str, bool],
    field: str,
    expected: str,
) -> None:
    result = _missing_source_by_field_from_presence(raw_signal, normalized_signal)
    assert result[field] == expected


def test_cl2_parent_trace_container_unavailable_covers_dotted_paths() -> None:
    unavailable = frozenset({"trace.canonical_entry"})
    assert protected_path_covered_by_unavailable("trace.canonical_entry.reason", unavailable) is True
    assert protected_path_covered_by_unavailable("trace.social_contract_trace.route_selected", unavailable) is False
