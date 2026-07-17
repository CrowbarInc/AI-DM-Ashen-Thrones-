"""Sealed and strict-social sealed fallback projection coverage."""
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


def test_golden_projection_projects_sealed_fallback_owner_bucket() -> None:
    observed = project_synthetic_turn(
        scenario_id="synthetic_sealed_owner",
        gm_text="A sealed fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
            realization_fallback_family="gate_terminal_repair",
        ),
    )

    assert observed["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE


def test_golden_projection_projects_strict_social_sealed_fallback_owner_bucket() -> None:
    observed = project_synthetic_turn(
        scenario_id="synthetic_strict_social_sealed_owner",
        gm_text="A strict-social sealed fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="minimal_social_emergency_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
            realization_fallback_family="strict_social_deterministic_fallback",
        ),
    )

    assert observed["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED
@pytest.mark.parametrize(
    (
        "scenario_id",
        "final_emitted_source",
        "fallback_kind",
        "expected_bucket",
        "expected_content_owner",
    ),
    [
        (
            "sealed_social_interlocutor_split_owner",
            "social_interlocutor_minimal_fallback",
            SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
            SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
            STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        ),
        (
            "sealed_passive_scene_pressure_split_owner",
            "passive_scene_pressure_fallback",
            SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "sealed_npc_pursuit_neutral_split_owner",
            "npc_pursuit_neutral_fallback",
            SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "sealed_anti_reset_continuation_split_owner",
            "anti_reset_local_continuation_fallback",
            SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "sealed_global_scene_split_owner",
            "global_scene_fallback",
            SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "sealed_unknown_replacement_split_owner",
            "unclassified_terminal_fallback",
            SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
            "unknown-none",
            SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        ),
    ],
)
def test_golden_projection_projects_sealed_family_replacement_split_owner_trifecta(
    scenario_id: str,
    final_emitted_source: str,
    fallback_kind: str,
    expected_bucket: str,
    expected_content_owner: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=scenario_id,
        gm_text="A sealed-family replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source=final_emitted_source,
            sealed_fallback_owner_bucket=expected_bucket,
            realization_fallback_family="gate_terminal_repair",
        ),
    )

    assert observed["sealed_fallback_owner_bucket"] == expected_bucket
    fallback = _fallback_selected_event(observed)
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_owner_bucket"] == expected_bucket
    assert fallback["fallback_selection_owner"] == SEALED_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == expected_content_owner
    assert fallback["stage"] == "gate"


def test_golden_projection_observed_turn_passes_classifier_contract_for_sealed_family_split_owners() -> None:
    observed = project_synthetic_turn(
        scenario_id="golden_classifier_sealed_family_split_bridge",
        gm_text="A sealed global-scene replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
            realization_fallback_family="gate_terminal_repair",
        ),
    )
    row = classify_replay_probe_row(
        observed_turn=observed,
        drift_row=exact_value_drift_row(
            "fallback_content_owner",
            expected=SEALED_FALLBACK_SELECTION_OWNER,
            actual=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
            reason="golden replay sealed-family classifier bridge",
        ),
        scenario_id=observed["scenario_id"],
        turn_index=observed["turn_index"],
    )

    assert row["fallback_selection_owner"] == SEALED_FALLBACK_SELECTION_OWNER
    assert row["fallback_content_owner"] == SEALED_FALLBACK_MODULE_CONTENT_OWNER
    assert row["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE
    assert validate_failure_classification_row(row) == []
