from __future__ import annotations

import pytest

from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.golden_replay_api import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    assert_runtime_lineage_event_matches,
    classify_golden_drift,
    expected_runtime_fallback_lineage_event,
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


def test_golden_projection_projects_runtime_lineage_and_prefers_existing_events() -> None:
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

    from_fem = project_synthetic_turn(
        scenario_id="fem_lineage_projection",
        gm_text="The road opens.",
        fem_meta=successful_opening_fem_meta(),
    )
    opening_selected = next(
        event for event in from_fem["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert_runtime_lineage_event_matches(
        opening_selected,
        expected_runtime_fallback_lineage_event(
            fallback_kind="scene_opening",
            owner="game.final_emission_gate",
            fallback_selection_owner="game.final_emission_gate",
            fallback_content_owner="game.opening_deterministic_fallback",
            fallback_authorship_source="upstream_prepared_opening_fallback",
            fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
    )
    debug = format_golden_replay_debug(
        {"scenario_id": from_fem["scenario_id"], "turn_count": 1, "turns": [from_fem]}
    )
    assert "'fallback_authorship_source': 'upstream_prepared_opening_fallback'" in debug
    assert "'fallback_owner_bucket': 'upstream-prepared'" in debug

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
    fallback_selected = [
        event
        for event in observed["runtime_lineage_events"]
        if event.get("event_kind") == "fallback_selected"
    ]
    assert fallback_selected[0]["fallback_kind"] == "sealed_unknown_replacement"

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
    failed_closed_selected = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert_runtime_lineage_event_matches(
        failed_closed_selected,
        expected_runtime_fallback_lineage_event(
            fallback_kind="opening_failed_closed",
            fallback_selection_owner="game.final_emission_gate",
            fallback_content_owner="game.final_emission_gate",
            fallback_authorship_source=None,
            fallback_owner_bucket=OPENING_FALLBACK_OWNER_SEALED_GATE,
        ),
    )
    debug = format_golden_replay_debug(
        {"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]}
    )
    assert "'fallback_kind': 'opening_failed_closed'" in debug
    assert "'fallback_owner_bucket': 'sealed-gate'" in debug


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
    fallback_selected = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert_runtime_lineage_event_matches(
        fallback_selected,
        expected_runtime_fallback_lineage_event(
            fallback_kind="minimal_social_emergency_fallback",
            owner="game.final_emission_gate",
            fallback_selection_owner="game.final_emission_gate",
            fallback_content_owner="game.social_exchange_emission",
        ),
    )


def test_golden_projection_projects_visibility_fallback_evidence() -> None:
    observed = project_synthetic_turn(
        scenario_id="synthetic_visibility_owner",
        gm_text="A visibility fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket="sealed-gate",
            visibility_replacement_applied=True,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == "sealed-gate"
    assert observed["visibility_replacement_applied"] is True
    assert observed["visibility_fallback_pool"] == "global_scene_narrative"
    assert observed["visibility_fallback_kind"] == "narrative_safe_fallback"
    fallback_selected = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    gate_outcome = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "gate_outcome"
    )
    assert fallback_selected["fallback_kind"] == "visibility_or_scene_replacement"
    assert gate_outcome["gate_path"] == "visibility_or_scene_replaced"


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
                    "sanitizer_empty_fallback_owner": "output_sanitizer",
                }
            },
        ),
    )

    assert observed["sanitizer_empty_fallback_used"] is True
    assert observed["sanitizer_empty_fallback_source"] == "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"
    assert observed["sanitizer_empty_fallback_owner"] == "output_sanitizer"
    assert observed["upstream_prepared_emission_used"] is False
    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_empty_fallback_used"] is True
    assert "sanitizer_empty_fallback" in observed["final_emission_mutation_lineage"]
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_empty_fallback_owner: 'output_sanitizer'" in debug
    assert "sanitizer_lineage_empty_fallback_used: True" in debug
    assert "final_emission_mutation_lineage" in debug


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
                upstream_prepared_emission_used=False,
                upstream_prepared_emission_valid=False,
                upstream_prepared_emission_source=None,
                upstream_prepared_emission_reject_reason=None,
            ),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "strip_only",
                    "sanitizer_strict_social_fallback_used": True,
                    "sanitizer_strict_social_selection_owner": "output_sanitizer",
                    "sanitizer_strict_social_prose_owner": "strict_social_emission",
                    "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
                }
            },
        ),
    )

    assert observed["sanitizer_strict_social_fallback_used"] is True
    assert observed["sanitizer_strict_social_selection_owner"] == "output_sanitizer"
    assert observed["sanitizer_strict_social_prose_owner"] == "strict_social_emission"
    assert observed["sanitizer_strict_social_source"] == "social_fallback_line_for_sanitizer.empty_output"
    assert observed["sanitizer_empty_fallback_used"] is None
    assert observed["upstream_prepared_emission_used"] is False
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_strict_social_selection_owner: 'output_sanitizer'" in debug
    assert "sanitizer_strict_social_prose_owner: 'strict_social_emission'" in debug
