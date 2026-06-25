"""Opening and sealed-gate opening fallback projection coverage."""
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


# Opening fallback owner-bucket boundary:
# this suite owns transport from FEM/runtime-lineage metadata into replay
# observations and debug output. Gate behavior/selection remains in
# test_final_emission_gate.py; FEM owner-bucket/lineage construction remains in
# test_final_emission_meta.py; classifier diagnostics remain in
# test_failure_classifier.py.

def test_golden_projection_projects_canonical_upstream_prepared_opening_owner_bucket() -> None:
    observed = project_synthetic_turn(
        scenario_id="synthetic_opening_owner",
        gm_text="The road opens.",
        fem_meta=successful_opening_fem_meta(
            response_type_repair_kind="opening_deterministic_fallback",
            fallback_temporal_frame="first_impression",
        ),
    )

    assert observed["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_golden_projection_prefers_bundle_runtime_lineage_events_and_empty_when_absent() -> None:
    existing = make_runtime_lineage_event(
        event_kind="speaker_repair",
        stage="gate",
        owner="game.speaker_contract_enforcement",
        source="provided_projection",
        repair_kind="local_rebind",
    )
    observed = project_synthetic_turn(
        scenario_id="existing_lineage_projection",
        gm_text="The road opens.",
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="opening_deterministic_fallback",
                opening_recovered_via_fallback=True,
                fallback_family_used="scene_opening",
            ),
            metadata={"observability_bundle": {"fem_runtime_lineage_events": [existing]}},
        ),
    )
    assert observed["runtime_lineage_events"] == [existing]

    missing = project_synthetic_turn(
        scenario_id="missing_lineage_projection",
        gm_text="The road remains quiet.",
        payload=minimal_gm_output_payload(player_facing_text="The road remains quiet."),
    )
    assert missing["runtime_lineage_events"] == []


def test_golden_projection_projects_neutral_speaker_grounding_replacement_family() -> None:
    observed = project_synthetic_turn(
        scenario_id="neutral_grounding_family_projection",
        gm_text="The moment passes without anyone stepping forward to own that thread.",
        player_text="I force the side door.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source=NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            response_type_repair_used=False,
        ),
    )

    assert observed["fallback_family"] == NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY
    assert "fallback_family" not in observed["unavailable"]
    assert observed["runtime_lineage_events"]

    summary = summarize_long_session_replay_observations([observed])
    fallback_escalation = summary["fallback_escalation_summary"]
    assert summary["fallback_turn_count"] == 1
    assert fallback_escalation["fallback_selected_without_family_count"] == 0
    assert "fallback_selected_without_family_recurrence" not in fallback_escalation["escalation_warnings"]


def test_golden_projection_projects_fail_closed_sealed_gate_opening_owner_bucket() -> None:
    observed = project_synthetic_turn(
        scenario_id="synthetic_opening_owner_fail_closed",
        gm_text="[opening_fallback_failed_closed:no_curated_facts]",
        fem_meta=fail_closed_opening_fem_meta(
            opening_recovered_via_fallback=True,
            fallback_family_used="scene_opening",
        ),
    )

    assert observed["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_SEALED_GATE
    debug = format_golden_replay_debug(
        {"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]}
    )
    assert "'fallback_kind': 'opening_failed_closed'" in debug
    assert "'fallback_owner_bucket': 'sealed-gate'" in debug


@pytest.mark.parametrize(
    (
        "scenario_id",
        "fem_meta",
        "fallback_kind",
        "expected_bucket",
        "expected_content_owner",
        "expected_repair_kind",
    ),
    [
        (
            "opening_scene_split_owner",
            successful_opening_fem_meta(
                response_type_repair_kind="opening_deterministic_fallback",
                fallback_temporal_frame="first_impression",
            ),
            "scene_opening",
            OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            OPENING_FALLBACK_CONTENT_OWNER,
            "opening_deterministic_fallback",
        ),
        (
            "opening_failed_closed_split_owner",
            fail_closed_opening_fem_meta(
                opening_recovered_via_fallback=True,
                fallback_family_used="scene_opening",
            ),
            "opening_failed_closed",
            OPENING_FALLBACK_OWNER_SEALED_GATE,
            OPENING_FAIL_CLOSED_CONTENT_OWNER,
            "opening_deterministic_fallback_failed_closed",
        ),
    ],
)
def test_golden_projection_projects_opening_family_split_owner_trifecta(
    scenario_id: str,
    fem_meta: dict,
    fallback_kind: str,
    expected_bucket: str,
    expected_content_owner: str,
    expected_repair_kind: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=scenario_id,
        gm_text="The road opens under sealed gate light.",
        fem_meta=fem_meta,
    )

    assert observed["opening_fallback_owner_bucket"] == expected_bucket
    fallback = _fallback_selected_event(observed)
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_owner_bucket"] == expected_bucket
    assert fallback["fallback_selection_owner"] == OPENING_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == expected_content_owner
    assert fallback["repair_kind"] == expected_repair_kind
    assert fallback["stage"] == "gate"


def test_golden_projection_observed_turn_passes_classifier_contract_for_opening_family_split_owners() -> None:
    observed = project_synthetic_turn(
        scenario_id="golden_classifier_opening_family_split_bridge",
        gm_text="The road opens.",
        fem_meta=successful_opening_fem_meta(
            response_type_repair_kind="opening_deterministic_fallback",
            fallback_temporal_frame="first_impression",
        ),
    )
    row = classify_replay_probe_row(
        observed_turn=observed,
        drift_row=exact_value_drift_row(
            "fallback_content_owner",
            expected=OPENING_FALLBACK_SELECTION_OWNER,
            actual=OPENING_FALLBACK_CONTENT_OWNER,
            reason="golden replay opening-family classifier bridge",
        ),
        scenario_id=observed["scenario_id"],
        turn_index=observed["turn_index"],
    )

    assert row["fallback_selection_owner"] == OPENING_FALLBACK_SELECTION_OWNER
    assert row["fallback_content_owner"] == OPENING_FALLBACK_CONTENT_OWNER
    assert row["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert validate_failure_classification_row(row) == []
