"""Upstream-fast fallback split-owner and classifier alignment coverage."""
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


def test_golden_projection_projects_upstream_fast_split_owner_trifecta() -> None:
    observed = project_synthetic_turn(
        scenario_id="upstream_fast_split_owner_projection",
        gm_text="The road holds its breath.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            fallback_provenance_trace={
                "source": "fallback",
                "stage": "fallback_selector",
                "content_fingerprint": "abc123",
                "gate_exit_vs_selector_match": True,
            },
        ),
    )

    fallback = _fallback_selected_event(observed)
    assert fallback["fallback_kind"] == "upstream_fast_fallback"
    assert fallback["fallback_selection_owner"] == UPSTREAM_FAST_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == UPSTREAM_FAST_FALLBACK_CONTENT_OWNER
    assert fallback["stage"] == "retry"
    assert fallback["owner"] == UPSTREAM_FAST_FALLBACK_SELECTION_OWNER

def test_golden_projection_observed_turn_passes_classifier_contract_for_upstream_fast_split_owners() -> None:
    observed = project_synthetic_turn(
        scenario_id="golden_classifier_upstream_fast_split_bridge",
        gm_text="The road holds its breath.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            fallback_provenance_trace={
                "source": "fallback",
                "stage": "fallback_selector",
                "content_fingerprint": "abc123",
                "gate_exit_vs_selector_match": True,
            },
        ),
    )
    row = classify_replay_probe_row(
        observed_turn=observed,
        drift_row=exact_value_drift_row(
            "fallback_content_owner",
            expected=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
            actual=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
            reason="golden replay upstream-fast classifier bridge",
        ),
        scenario_id=observed["scenario_id"],
        turn_index=observed["turn_index"],
    )

    assert row["fallback_selection_owner"] == UPSTREAM_FAST_FALLBACK_SELECTION_OWNER
    assert row["fallback_content_owner"] == UPSTREAM_FAST_FALLBACK_CONTENT_OWNER
    assert validate_failure_classification_row(row) == []
