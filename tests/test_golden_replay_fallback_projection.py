from __future__ import annotations

import pytest

from game.final_emission_ownership_schema import (
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

from tests.helpers.golden_replay_projection import (
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


def test_golden_projection_projects_visibility_fallback_evidence() -> None:
    observed = project_synthetic_turn(
        scenario_id="synthetic_visibility_owner",
        gm_text="A visibility fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket=VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            visibility_replacement_applied=True,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == VISIBILITY_FALLBACK_OWNER_SEALED_GATE
    assert observed["visibility_replacement_applied"] is True
    assert observed["visibility_fallback_pool"] == "global_scene_narrative"
    assert observed["visibility_fallback_kind"] == "narrative_safe_fallback"


@pytest.mark.parametrize(
    ("scenario_id", "pool", "kind", "source", "expected_bucket"),
    [
        (
            "visibility_hard_replace_sealed_gate",
            "global_scene_narrative",
            "narrative_safe_fallback",
            "global_scene_fallback",
            VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
        ),
        (
            "visibility_hard_replace_strict_social",
            "strict_social_visibility_minimal",
            "visibility_minimal_social_fallback",
            "minimal_social_emergency_fallback",
            VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        ),
        (
            "visibility_hard_replace_opening_visibility",
            "scene_opening_deterministic",
            "opening_deterministic_fallback",
            "opening_deterministic_fallback",
            VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
        ),
    ],
)
def test_golden_projection_projects_visibility_hard_replacement_canonical_owner_buckets(
    scenario_id: str,
    pool: str,
    kind: str,
    source: str,
    expected_bucket: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=scenario_id,
        gm_text="A visibility hard-replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source=source,
            visibility_fallback_owner_bucket=expected_bucket,
            visibility_replacement_applied=True,
            visibility_fallback_pool=pool,
            visibility_fallback_kind=kind,
            producer_repair_kind="visibility_enforcement",
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == expected_bucket
    assert observed["visibility_fallback_pool"] == pool
    assert observed["visibility_fallback_kind"] == kind


def _fallback_selected_event(observed: dict) -> dict:
    return next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )


def _mutation_event(observed: dict, mutation_kind: str) -> dict:
    return next(
        event
        for event in observed["runtime_lineage_events"]
        if event.get("event_kind") == "mutation" and event.get("mutation_kind") == mutation_kind
    )


@pytest.mark.parametrize(
    (
        "scenario_id",
        "replacement_flag",
        "fallback_kind",
        "producer_repair_kind",
        "mutation_kind",
        "expected_bucket",
        "expected_content_owner",
    ),
    [
        (
            "visibility_hard_replace_split_owner",
            {"visibility_replacement_applied": True},
            "visibility_hard_replacement",
            "visibility_enforcement",
            "visibility_replacement_mutation",
            VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "first_mention_hard_replace_split_owner",
            {"first_mention_replacement_applied": True},
            "first_mention_hard_replacement",
            "first_mention_enforcement",
            "first_mention_replacement_mutation",
            VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "referential_hard_replace_split_owner",
            {"referential_clarity_replacement_applied": True},
            "referential_clarity_hard_replacement",
            "referential_clarity_enforcement",
            "referential_clarity_replacement_mutation",
            VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
            "game.social_exchange_emission",
        ),
    ],
)
def test_golden_projection_projects_visibility_family_hard_replacement_split_owner_trifecta(
    scenario_id: str,
    replacement_flag: dict[str, bool],
    fallback_kind: str,
    producer_repair_kind: str,
    mutation_kind: str,
    expected_bucket: str,
    expected_content_owner: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=scenario_id,
        gm_text="A visibility-family hard-replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket=expected_bucket,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            producer_repair_kind=producer_repair_kind,
            **replacement_flag,
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == expected_bucket
    fallback = _fallback_selected_event(observed)
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_owner_bucket"] == expected_bucket
    assert fallback["fallback_selection_owner"] == VISIBILITY_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == expected_content_owner
    assert fallback["repair_kind"] == producer_repair_kind
    mutation = _mutation_event(observed, mutation_kind)
    assert mutation["mutation_kind"] == mutation_kind


def test_golden_projection_projects_referential_local_substitution_owner_bucket_and_repair_kind() -> None:
    observed = project_synthetic_turn(
        scenario_id="referential_local_substitution_projection",
        gm_text="The Tavern Runner says she will return.",
        fem_meta=fem_payload(
            final_route="accept_candidate",
            referential_clarity_local_substitution_applied=True,
            referential_clarity_local_substitution_token="she",
            referential_clarity_local_substitution_replacement="The Tavern Runner",
            visibility_fallback_owner_bucket=VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
            producer_repair_kind="referential_clarity_local_substitution",
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY
    mutation = _mutation_event(observed, "referential_clarity_local_substitution_mutation")
    assert mutation["owner"] == "game.final_emission_gate"
    assert mutation["source"] == "she"


def test_golden_projection_observed_turn_passes_classifier_contract_for_visibility_family_split_owners() -> None:
    from tests.helpers.failure_classification_sync import classify_replay_probe_row

    observed = project_synthetic_turn(
        scenario_id="golden_classifier_visibility_family_bridge",
        gm_text="A first-mention hard-replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            first_mention_replacement_applied=True,
            visibility_fallback_owner_bucket=VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            producer_repair_kind="first_mention_enforcement",
        ),
    )
    row = classify_replay_probe_row(
        observed_turn=observed,
        drift_row=exact_value_drift_row(
            "fallback_content_owner",
            expected="game.final_emission_gate",
            actual=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
            reason="golden replay classifier bridge",
        ),
        scenario_id=observed["scenario_id"],
        turn_index=observed["turn_index"],
    )

    assert row["fallback_selection_owner"] == VISIBILITY_FALLBACK_SELECTION_OWNER
    assert row["fallback_content_owner"] == SEALED_FALLBACK_MODULE_CONTENT_OWNER
    assert row["visibility_fallback_owner_bucket"] == VISIBILITY_FALLBACK_OWNER_SEALED_GATE
    assert row["repair_kind"] == "first_mention_enforcement"
    assert validate_failure_classification_row(row) == []


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


def test_long_session_summary_preserves_sanitizer_upstream_fast_split_owner_lineage_stability() -> None:
    turns = [
        project_synthetic_turn(
            scenario_id="streak_sanitizer_split",
            gm_text="Silence.",
            player_text="Wait.",
            resolution={"kind": "observe"},
            payload=minimal_gm_output_payload(
                fem_meta=fem_payload(
                    final_emitted_source="generated_candidate",
                    sanitizer_empty_fallback_used=True,
                    sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                    sanitizer_empty_fallback_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
                ),
                metadata={
                    "sanitizer_trace": {
                        "sanitizer_empty_fallback_used": True,
                        "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                    }
                },
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_upstream_fast_split",
            gm_text="The road holds.",
            player_text="Wait again.",
            resolution={"kind": "observe"},
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                fallback_provenance_trace={
                    "source": "fallback",
                    "stage": "fallback_selector",
                    "content_fingerprint": "def456",
                    "gate_exit_vs_selector_match": True,
                },
            ),
        ),
    ]

    for turn in turns:
        fallback = _fallback_selected_event(turn)
        assert fallback["fallback_selection_owner"] in {
            SANITIZER_FALLBACK_SELECTION_OWNER,
            UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        }
        assert fallback["fallback_content_owner"] in {
            SANITIZER_FALLBACK_SELECTION_OWNER,
            UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        }

    summary = summarize_long_session_replay_observations(turns)
    lineage = summary["lineage_summary"]
    assert lineage["fallback_selection_owner_frequency"] == {
        SANITIZER_FALLBACK_SELECTION_OWNER: 1,
        UPSTREAM_FAST_FALLBACK_SELECTION_OWNER: 1,
    }
    assert lineage["fallback_content_owner_frequency"] == {
        SANITIZER_FALLBACK_SELECTION_OWNER: 1,
        UPSTREAM_FAST_FALLBACK_CONTENT_OWNER: 1,
    }
    assert lineage["fallback_frequency"]["sanitizer_empty_output"] == 1
    assert lineage["fallback_frequency"]["upstream_fast_fallback"] == 1


def test_long_session_summary_preserves_opening_family_split_owner_lineage_stability() -> None:
    turns = [
        project_synthetic_turn(
            scenario_id="streak_opening_scene",
            gm_text="The road opens.",
            player_text="Begin.",
            resolution={"kind": "scene_opening"},
            fem_meta=successful_opening_fem_meta(
                response_type_repair_kind="opening_deterministic_fallback",
                fallback_temporal_frame="first_impression",
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_opening_failed_closed",
            gm_text="[opening_fallback_failed_closed:no_curated_facts]",
            player_text="Begin again.",
            resolution={"kind": "scene_opening"},
            fem_meta=fail_closed_opening_fem_meta(
                opening_recovered_via_fallback=True,
                fallback_family_used="scene_opening",
            ),
        ),
    ]

    for turn in turns:
        fallback = _fallback_selected_event(turn)
        assert fallback["fallback_selection_owner"] == OPENING_FALLBACK_SELECTION_OWNER
        assert fallback["fallback_content_owner"] in {
            OPENING_FALLBACK_CONTENT_OWNER,
            OPENING_FAIL_CLOSED_CONTENT_OWNER,
        }
        assert fallback["fallback_owner_bucket"] in {
            OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            OPENING_FALLBACK_OWNER_SEALED_GATE,
        }

    summary = summarize_long_session_replay_observations(turns)
    lineage = summary["lineage_summary"]
    assert lineage["fallback_selection_owner_frequency"] == {OPENING_FALLBACK_SELECTION_OWNER: 2}
    assert lineage["fallback_content_owner_frequency"] == {
        OPENING_FALLBACK_CONTENT_OWNER: 1,
        OPENING_FAIL_CLOSED_CONTENT_OWNER: 1,
    }
    assert lineage["fallback_owner_bucket_frequency"] == {
        OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED: 1,
        OPENING_FALLBACK_OWNER_SEALED_GATE: 1,
    }
    assert lineage["fallback_frequency"]["scene_opening"] == 1
    assert lineage["fallback_frequency"]["opening_failed_closed"] == 1


def test_long_session_summary_preserves_sealed_family_split_owner_lineage_stability() -> None:
    turns = [
        project_synthetic_turn(
            scenario_id="streak_sealed_global_scene",
            gm_text="The scene holds.",
            player_text="Wait.",
            resolution={"kind": "observe"},
            fem_meta=fem_payload(
                final_route="replaced",
                final_emitted_source="global_scene_fallback",
                sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
                realization_fallback_family="gate_terminal_repair",
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_sealed_social_interlocutor",
            gm_text="The runner stays quiet.",
            player_text="Ask again.",
            resolution={"kind": "question"},
            fem_meta=fem_payload(
                final_route="replaced",
                final_emitted_source="social_interlocutor_minimal_fallback",
                sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
                realization_fallback_family="gate_terminal_repair",
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_sealed_unknown",
            gm_text="The road closes.",
            player_text="Leave.",
            resolution={"kind": "action"},
            fem_meta=fem_payload(
                final_route="replaced",
                final_emitted_source="unclassified_terminal_fallback",
                sealed_fallback_owner_bucket="unknown-none",
                realization_fallback_family="gate_terminal_repair",
            ),
        ),
    ]

    for turn in turns:
        fallback = _fallback_selected_event(turn)
        assert fallback["fallback_selection_owner"] == SEALED_FALLBACK_SELECTION_OWNER
        assert fallback["fallback_content_owner"] in {
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
            STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
            SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        }
        assert fallback["fallback_owner_bucket"] in {
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
            "unknown-none",
        }

    summary = summarize_long_session_replay_observations(turns)
    lineage = summary["lineage_summary"]
    assert lineage["fallback_selection_owner_frequency"] == {SEALED_FALLBACK_SELECTION_OWNER: 3}
    assert lineage["fallback_content_owner_frequency"] == {
        SEALED_FALLBACK_MODULE_CONTENT_OWNER: 1,
        STRICT_SOCIAL_FALLBACK_CONTENT_OWNER: 1,
        SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER: 1,
    }
    assert lineage["fallback_owner_bucket_frequency"] == {
        SEALED_FALLBACK_OWNER_SEALED_GATE: 1,
        SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED: 1,
        "unknown-none": 1,
    }
    assert lineage["fallback_frequency"][SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE] == 1
    assert lineage["fallback_frequency"][SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR] == 1
    assert lineage["fallback_frequency"][SEALED_REPLACEMENT_SUBKIND_UNKNOWN] == 1


def test_long_session_summary_treats_scene_action_fallback_speaker_absence_as_optional():
    turns = [
        {
            "turn_index": 0,
            "route_kind": "undecided",
            "response_type_required": "neutral_narration",
            "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "fallback_family": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "unavailable": ["selected_speaker_id"],
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="sealed_or_global_replacement",
                )
            ],
        },
        {
            "turn_index": 1,
            "route_kind": "action",
            "response_type_required": "action_outcome",
            "final_emitted_source": "anti_reset_local_continuation_fallback",
            "fallback_family": "gate_terminal_repair",
            "unavailable": ["selected_speaker_id"],
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="response_type_prepared_emission",
                )
            ],
        },
    ]

    fallback_escalation = summarize_long_session_replay_observations(turns)["fallback_escalation_summary"]

    assert fallback_escalation["unavailable_with_fallback_count"] == 2
    assert fallback_escalation["scene_action_speaker_optional_unavailable_count"] == 2
    assert fallback_escalation["blocking_unavailable_with_fallback_count"] == 0
    assert fallback_escalation["max_fallback_streak"] == 2
    assert fallback_escalation["max_scene_action_nonblocking_fallback_streak"] == 2
    assert fallback_escalation["max_blocking_fallback_streak"] == 0
    assert "fallback_streak_gt_1" not in fallback_escalation["escalation_warnings"]
    assert "unavailable_to_fallback_coupling_recurrence" not in fallback_escalation["escalation_warnings"]


def test_split_owner_acceptance_matrix_golden_replay_observed_lineage_matches_builders() -> None:
    """BU15: golden-replay observed rows embed the same lineage trifecta as the canonical matrix."""
    for row in split_owner_acceptance_matrix_rows():
        observed = split_owner_observed_row_from_matrix_row(row)
        embedded = observed["runtime_lineage_events"][0]
        built = split_owner_lineage_event_from_matrix_row(row)
        assert_split_owner_matrix_lineage_event(row, embedded)
        assert embedded.get("fallback_selection_owner") == built.get("fallback_selection_owner")
        assert embedded.get("fallback_content_owner") == built.get("fallback_content_owner")
        assert embedded.get("fallback_owner_bucket") == built.get("fallback_owner_bucket")
        assert embedded.get("repair_kind") == built.get("repair_kind")
        assert embedded.get("mutation_kind") == built.get("mutation_kind")


def test_split_owner_acceptance_matrix_production_fem_projection_stays_aligned() -> None:
    """BU16: golden replay validates production FEM/replay projection for every matrix row."""
    for row in split_owner_acceptance_matrix_rows():
        if split_owner_fem_projection_excluded(row):
            continue
        observed = project_split_owner_matrix_row(row)
        assert_split_owner_matrix_fem_projection(row, observed)
