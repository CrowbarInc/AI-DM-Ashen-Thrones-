"""Upstream prepared emission telemetry and drift classification coverage."""
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



@pytest.mark.parametrize(
    ("required", "repair_kind", "source"),
    [
        (
            "answer",
            "answer_upstream_prepared_repair",
            "upstream_prepared_emission.prepared_answer_fallback_text",
        ),
        (
            "action_outcome",
            "action_outcome_upstream_prepared_repair",
            "upstream_prepared_emission.prepared_action_fallback_text",
        ),
    ],
)
def test_golden_projection_projects_valid_upstream_prepared_emission_telemetry(
    required: str,
    repair_kind: str,
    source: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=f"{required}_prepared_projection",
        gm_text="Projected prepared text.",
        player_text="Do the thing.",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source=repair_kind,
            response_type_required=required,
            response_type_candidate_ok=True,
            response_type_repair_used=True,
            response_type_repair_kind=repair_kind,
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            upstream_prepared_emission_source=source,
            upstream_prepared_emission_reject_reason=None,
            realization_fallback_family="upstream_prepared_emission",
        ),
    )

    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is True
    assert observed["upstream_prepared_emission_source"] == source
    assert observed["upstream_prepared_emission_reject_reason"] is None
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert f"upstream_prepared_emission_source: {source!r}" in debug


def test_golden_projection_projects_rejected_upstream_prepared_emission_telemetry() -> None:
    observed = project_synthetic_turn(
        scenario_id="rejected_prepared_projection",
        gm_text="You pry the chest, but nothing gives yet.",
        player_text="Pry the chest.",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            response_type_required="action_outcome",
            response_type_candidate_ok=False,
            response_type_repair_used=False,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="upstream_prepared_emission.prepared_action_fallback_text",
            upstream_prepared_emission_reject_reason="action_outcome_replaced_by_dialogue",
            realization_fallback_family="upstream_prepared_emission",
        ),
    )

    assert observed["upstream_prepared_emission_used"] is False
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_source"] == "upstream_prepared_emission.prepared_action_fallback_text"
    assert observed["upstream_prepared_emission_reject_reason"] == "action_outcome_replaced_by_dialogue"
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "upstream_prepared_emission_reject_reason: 'action_outcome_replaced_by_dialogue'" in debug


@pytest.mark.parametrize(
    ("required", "repair_kind", "source"),
    [
        ("answer", None, "absent"),
        ("action_outcome", None, "absent"),
    ],
)
def test_golden_projection_projects_absent_upstream_prepared_emission_telemetry(
    required: str,
    repair_kind: str | None,
    source: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=f"{required}_prepared_absent_projection",
        gm_text="Only mist between the torches.",
        player_text="Can I do it?",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            response_type_required=required,
            response_type_candidate_ok=False,
            response_type_repair_used=False,
            response_type_repair_kind=repair_kind,
            response_type_upstream_prepared_absent=True,
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source=source,
            upstream_prepared_emission_reject_reason=None,
        ),
    )

    assert observed["upstream_prepared_emission_used"] is False
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_source"] == "absent"
    assert observed["upstream_prepared_emission_reject_reason"] is None
    assert observed["raw_signal_presence"]["upstream_prepared_emission_used"] is True
    assert observed["raw_signal_presence"]["upstream_prepared_emission_valid"] is True
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "upstream_prepared_emission_used: False" in debug
    assert "upstream_prepared_emission_source: 'absent'" in debug


def test_golden_projection_drift_classification_preserves_malformed_prepared_emission_reject_reason() -> None:
    observed = project_synthetic_turn(
        scenario_id="malformed_prepared_projection",
        gm_text="The lock remains stubborn.",
        player_text="Pry the lock.",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            response_type_required="action_outcome",
            response_type_candidate_ok=False,
            response_type_repair_used=False,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="upstream_prepared_emission.prepared_action_fallback_text",
            upstream_prepared_emission_reject_reason="action_outcome_missing_result",
            realization_fallback_family="upstream_prepared_emission",
        ),
    )

    drift = classify_golden_drift(
        observed,
        {
            "equals": {
                "upstream_prepared_emission_valid": True,
            }
        },
    )

    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_reject_reason"] == "action_outcome_missing_result"
    row = drift["failure_classifications"][0]
    assert row["primary_owner"] == "upstream_prepared_emission"
    assert row["upstream_prepared_emission_reject_reason"] == "action_outcome_missing_result"
    debug = format_golden_replay_debug(
        {"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed], "drift": drift}
    )
    assert "upstream_prepared_emission_reject_reason: 'action_outcome_missing_result'" in debug
    assert "owner='upstream_prepared_emission'" in debug
