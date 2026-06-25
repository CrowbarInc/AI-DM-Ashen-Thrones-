"""Sanitizer empty and strict-social fallback projection coverage."""
from __future__ import annotations

import pytest

from game.ownership_projection_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
)

from game.attribution_read_views import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import validate_failure_classification_row
from tests.helpers.failure_classification_sync import (
    assert_split_owner_matrix_fem_projection,
    assert_split_owner_matrix_lineage_event,
    classify_replay_probe_row,
    exact_value_drift_row,
    project_split_owner_matrix_row,
    split_owner_acceptance_matrix_rows,
    split_owner_fem_projection_excluded,
    split_owner_lineage_event_from_matrix_row,
    split_owner_observed_row_from_matrix_row,
)
from tests.helpers.golden_replay_api import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    classify_golden_drift,
    format_golden_replay_debug,
    summarize_long_session_replay_observations,
)
from tests.helpers.golden_replay_fixtures import (
    fem_payload,
    minimal_gm_output_payload,
    project_synthetic_turn,
)
from tests.helpers.opening_fallback_evidence import (
    fail_closed_opening_fem_meta,
    successful_opening_fem_meta,
)

from tests.helpers.golden_replay_fallback_projection_helpers import (
    fallback_selected_event as _fallback_selected_event,
    mutation_event as _mutation_event,
)


def test_golden_projection_projects_sanitizer_empty_fallback_as_sanitizer_owned() -> None:
    observed = project_synthetic_turn(
        scenario_id="sanitizer_empty_projection",
        gm_text="For a breath, the scene stays still.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                final_emission_mutation_lineage=[
                    "pre_gate_sanitizer",
                    "sanitizer_empty_fallback",
                    "finalize_packaging",
                ],
                response_type_repair_used=False,
                upstream_prepared_emission_used=False,
                upstream_prepared_emission_valid=False,
                upstream_prepared_emission_source=None,
                upstream_prepared_emission_reject_reason=None,
            ),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_boundary_mode": "strip_only",
                    "sanitizer_empty_fallback_used": True,
                    "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                    "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                }
            },
        ),
    )

    assert observed["sanitizer_empty_fallback_used"] is True
    assert observed["sanitizer_empty_fallback_source"] == "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"
    assert observed["sanitizer_empty_fallback_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert observed["upstream_prepared_emission_used"] is False
    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_empty_fallback_used"] is True
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_empty_fallback_owner: 'game.output_sanitizer'" in debug
    assert "sanitizer_lineage_empty_fallback_used: True" in debug


def test_golden_projection_projects_strict_social_sanitizer_fallback_owner_split() -> None:
    observed = project_synthetic_turn(
        scenario_id="strict_social_sanitizer_split",
        gm_text='The runner says, "No names."',
        player_text="Ask the runner.",
        resolution={"kind": "question"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                strict_social_active=True,
                sanitizer_strict_social_fallback_used=True,
                sanitizer_strict_social_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
                sanitizer_strict_social_prose_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                sanitizer_strict_social_source="social_fallback_line_for_sanitizer.empty_output",
                upstream_prepared_emission_used=False,
                upstream_prepared_emission_valid=False,
                upstream_prepared_emission_source=None,
                upstream_prepared_emission_reject_reason=None,
            ),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "strip_only",
                    "sanitizer_strict_social_fallback_used": True,
                    "sanitizer_strict_social_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                    "sanitizer_strict_social_prose_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
                    "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
                }
            },
        ),
    )

    assert observed["sanitizer_strict_social_fallback_used"] is True
    assert observed["sanitizer_strict_social_selection_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert observed["sanitizer_strict_social_prose_owner"] == SANITIZER_STRICT_SOCIAL_CONTENT_OWNER
    assert observed["sanitizer_strict_social_source"] == "social_fallback_line_for_sanitizer.empty_output"
    assert observed["sanitizer_empty_fallback_used"] is None
    assert observed["upstream_prepared_emission_used"] is False
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_strict_social_selection_owner: 'game.output_sanitizer'" in debug
    assert "sanitizer_strict_social_prose_owner: 'game.social_exchange_emission'" in debug
    fallback = _fallback_selected_event(observed)
    assert fallback["fallback_kind"] == "sanitizer_strict_social"
    assert fallback["fallback_selection_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == SANITIZER_STRICT_SOCIAL_CONTENT_OWNER
    assert fallback["stage"] == "sanitizer"


def test_golden_projection_projects_sanitizer_empty_split_owner_trifecta() -> None:
    observed = project_synthetic_turn(
        scenario_id="sanitizer_empty_split_owner_projection",
        gm_text="For a breath, the scene stays still.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                sanitizer_empty_fallback_used=True,
                sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                sanitizer_empty_fallback_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
                final_emission_mutation_lineage=[
                    "pre_gate_sanitizer",
                    "sanitizer_empty_fallback",
                    "finalize_packaging",
                ],
            ),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_boundary_mode": "strip_only",
                    "sanitizer_empty_fallback_used": True,
                    "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                    "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                }
            },
        ),
    )

    fallback = _fallback_selected_event(observed)
    assert fallback["fallback_kind"] == "sanitizer_empty_output"
    assert fallback["fallback_selection_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert fallback["stage"] == "sanitizer"
def test_golden_projection_observed_turn_passes_classifier_contract_for_sanitizer_split_owners() -> None:
    observed = project_synthetic_turn(
        scenario_id="golden_classifier_sanitizer_split_bridge",
        gm_text='The runner says, "No names."',
        player_text="Ask the runner.",
        resolution={"kind": "question"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                strict_social_active=True,
                sanitizer_strict_social_fallback_used=True,
                sanitizer_strict_social_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
                sanitizer_strict_social_prose_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                sanitizer_strict_social_source="social_fallback_line_for_sanitizer.empty_output",
            ),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "strip_only",
                    "sanitizer_strict_social_fallback_used": True,
                    "sanitizer_strict_social_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                    "sanitizer_strict_social_prose_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                    "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
                }
            },
        ),
    )
    row = classify_replay_probe_row(
        observed_turn=observed,
        drift_row=exact_value_drift_row(
            "fallback_content_owner",
            expected=SANITIZER_FALLBACK_SELECTION_OWNER,
            actual=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            reason="golden replay sanitizer classifier bridge",
        ),
        scenario_id=observed["scenario_id"],
        turn_index=observed["turn_index"],
    )

    assert row["fallback_selection_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert row["fallback_content_owner"] == SANITIZER_STRICT_SOCIAL_CONTENT_OWNER
    assert row["sanitizer_strict_social_selection_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert row["sanitizer_strict_social_prose_owner"] == SANITIZER_STRICT_SOCIAL_CONTENT_OWNER
    assert validate_failure_classification_row(row) == []
