from __future__ import annotations

import pytest

from game import storage
from game.api import chat
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    opening_fallback_owner_bucket_from_meta,
)
from tests.helpers.golden_replay_projection import read_fem_meta_from_gate_output
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from game.final_emission_replay_projection import SEALED_REPLACEMENT_SUBKINDS
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
from game.scenario_spine import (
    ScenarioBranch,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_to_dict,
    validate_scenario_spine_definition,
)
from game.scenario_spine_eval import minimal_complete_transcript_turn_meta
from game.models import ChatRequest
from tests.helpers.golden_replay import (
    FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    _observed_turn,
    assert_fallback_escalation_profile,
    assert_golden_turn_observation,
    assert_long_session_stability_profile,
    assert_protected_golden_turn_observation,
    assert_runtime_lineage_profile,
    build_long_session_stability_scorecard,
    compare_golden_replay_reruns,
    evaluate_golden_replay_continuity_drift,
    final_text_has_scaffold_leakage,
    format_golden_replay_debug,
    frontier_gate_branch_prompts,
    frontier_gate_branch_turn_ids,
    load_frontier_gate_long_session_spine,
    protected_no_scaffold_expectation,
    protected_social_directed_question_expectation,
    protected_social_structural_base,
    protected_social_supplemental_structural_expectation,
    protected_social_trace_target_expectation,
    protected_social_vocative_canonical_entry_expectation,
    protected_structural_expectation,
    protected_unavailable_expectation,
    render_long_session_replay_summary_markdown,
    run_golden_replay,
    summarize_long_session_replay_observations,
)
from tests.helpers.transcript_runner import (
    new_clean_campaign,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)
from tests.helpers.failure_dashboard_report import (
    clear_recorded_protected_replay_failures,
    recorded_protected_replay_failure_rows,
    render_long_session_stability_scorecard_markdown,
    write_long_session_stability_scorecard_artifacts,
    write_protected_replay_failure_report_if_present,
)
from tests.helpers.opening_fallback_evidence import (
    successful_opening_observed_fields,
)
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
)
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details
from tests.helpers.gate_equivalence_monkeypatch import (
    patch_build_final_strict_social_response,
    patch_get_speaker_selection_contract,
)
from tests.helpers.opening_fallback_evidence import opening_gm_output
from tests.helpers.strict_social_harness import runner_strict_bundle
from tests.helpers.replay_observed_row_fixtures import protected_speaker_failure_turn, synthetic_rerun_turn
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    observed_turn_from_gate_output,
    seed_frontier_gate_world,
    seed_investigator_runner_world,
    seed_runner_continuity_world,
    seed_runner_guard_world,
    seed_scene_object_investigation_world,
    seed_spine_three_branch_world,
    seed_tavern_patrol_lead_world,
)

pytestmark = [pytest.mark.integration, pytest.mark.golden_replay]

# Ownership note:
# Golden replay owns protected replay orchestration and live replay bridge checks.
# Synthetic projection contracts live in ``tests.test_golden_replay_projection``.
# Repeated route/speaker/fallback/final-emission fields are intentional diagnostic
# locks, not runtime ownership of those subsystems.


def test_protected_golden_assertion_failure_records_canonical_report(tmp_path):
    turn = protected_speaker_failure_turn()
    report_path = tmp_path / "replay_failure_report.md"
    clear_recorded_protected_replay_failures()
    try:
        assert write_protected_replay_failure_report_if_present(path=report_path) is None
        with pytest.raises(AssertionError) as exc:
            assert_protected_golden_turn_observation(
                turn,
                {"equals": {"selected_speaker_id": "runner"}},
                scenario_id="synthetic_protected_bridge",
                debug_context="synthetic reporting bridge context",
            )
        assert "golden replay expectation failed: exact value mismatch" in str(exc.value)

        rows = recorded_protected_replay_failure_rows()
        assert len(rows) == 1
        assert rows[0]["scenario_id"] == "synthetic_protected_bridge"
        assert rows[0]["source_path"] == "data/validation/scenario_spines/synthetic_fixture.json"
        assert rows[0]["branch_id"] == "synthetic_branch"
        assert rows[0]["turn_id"] == "synthetic_turn_01"
        assert rows[0]["field_path"] == "selected_speaker_id"
        assert rows[0]["expected"] == "runner"
        assert rows[0]["actual"] == "guard"
        assert rows[0]["category"] == "speaker"
        assert rows[0]["severity"] == "critical"
        assert rows[0]["primary_owner"] == "speaker"
        assert rows[0]["investigate_first"] == "game/speaker_contract_enforcement.py"
    finally:
        clear_recorded_protected_replay_failures()


def test_compare_golden_replay_reruns_identical_runs_have_zero_deltas():
    turns = [
        synthetic_rerun_turn(turn_index=0, turn_id="t01"),
        synthetic_rerun_turn(turn_index=1, turn_id="t02", route_kind="action", selected_speaker_id=None),
    ]

    scorecard = compare_golden_replay_reruns(turns, [dict(turn) for turn in turns])

    assert scorecard["report_only"] is True
    assert scorecard["total_turns_compared"] == 2
    assert scorecard["summary"] == {
        "speaker_delta_count": 0,
        "route_delta_count": 0,
        "fallback_delta_count": 0,
        "text_fingerprint_delta_count": 0,
        "scaffold_delta_count": 0,
        "runtime_lineage_delta_count": 0,
        "semantic_delta_frequency_delta_count": 0,
    }
    assert scorecard["per_turn_deltas"] == []


def test_compare_golden_replay_reruns_counts_speaker_only_drift():
    previous = [synthetic_rerun_turn(selected_speaker_id="runner")]
    current = [synthetic_rerun_turn(selected_speaker_id="guard")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["speaker_delta_count"] == 1
    assert scorecard["summary"]["route_delta_count"] == 0
    assert scorecard["per_turn_deltas"][0]["deltas"]["speaker"] == {
        "previous": "runner",
        "current": "guard",
    }
    assert scorecard["frequencies"]["speakers"]["delta"] == {"guard": 1, "runner": -1}


def test_compare_golden_replay_reruns_counts_route_only_drift():
    previous = [synthetic_rerun_turn(route_kind="dialogue")]
    current = [synthetic_rerun_turn(route_kind="action")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["route_delta_count"] == 1
    assert scorecard["summary"]["speaker_delta_count"] == 0
    assert scorecard["per_turn_deltas"][0]["deltas"]["route"] == {
        "previous": "dialogue",
        "current": "action",
    }
    assert scorecard["frequencies"]["routes"]["delta"] == {"action": 1, "dialogue": -1}


def test_compare_golden_replay_reruns_counts_fallback_frequency_drift():
    event = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="sealed_or_global_replacement",
        fallback_selection_owner="final_emission_gate",
    )
    previous = [synthetic_rerun_turn()]
    current = [
        synthetic_rerun_turn(
            fallback_family="gate_terminal_repair",
            fallback_owner="sealed_gate",
            runtime_lineage_events=[event],
        )
    ]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["fallback_delta_count"] == 1
    assert scorecard["summary"]["runtime_lineage_delta_count"] == 1
    assert scorecard["frequencies"]["fallback_families"]["delta"] == {"gate_terminal_repair": 1}
    assert scorecard["frequencies"]["fallback_owners"]["delta"] == {"sealed_gate": 1}
    assert (
        scorecard["frequencies"]["runtime_lineage"]["frequency_deltas"]["fallback_frequency"]["delta"]
        == {"sealed_or_global_replacement": 1}
    )


def test_compare_golden_replay_reruns_reports_text_fingerprints_without_failing():
    previous = [synthetic_rerun_turn(final_text="The runner answers.")]
    current = [synthetic_rerun_turn(final_text="The runner answers with a warning.")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["text_fingerprint_delta_count"] == 1
    fingerprint_delta = scorecard["per_turn_deltas"][0]["deltas"]["text_fingerprint"]
    assert fingerprint_delta["previous"] != fingerprint_delta["current"]
    assert len(fingerprint_delta["previous"]) == 16
    assert len(fingerprint_delta["current"]) == 16
    assert scorecard["report_only"] is True


def test_compare_golden_replay_reruns_handles_missing_optional_metadata():
    previous = [{"turn_index": 0, "final_text": "Rain falls."}]
    current = [{"turn_index": 0, "final_text": "Rain falls.", "runtime_lineage_events": "not-a-list"}]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["total_turns_compared"] == 1
    assert scorecard["summary"]["speaker_delta_count"] == 0
    assert scorecard["summary"]["route_delta_count"] == 0
    assert scorecard["summary"]["fallback_delta_count"] == 0
    assert scorecard["summary"]["runtime_lineage_delta_count"] == 0
    assert scorecard["summary"]["semantic_delta_frequency_delta_count"] == 0
    assert scorecard["frequencies"]["response_delta"]["previous"]["response_delta_unknown_count"] == 1
    assert scorecard["frequencies"]["response_delta"]["current"]["response_delta_unknown_count"] == 1
    assert scorecard["per_turn_deltas"] == []


def test_long_session_summary_counts_response_delta_metadata():
    turns = [
        synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=False,
            response_delta_repaired=False,
            response_delta_kind="new_fact",
            response_delta_echo_overlap_band="low",
        ),
        synthetic_rerun_turn(
            turn_index=1,
            response_delta_checked=True,
            response_delta_failed=True,
            response_delta_repaired=True,
            response_delta_kind="new_fact",
            response_delta_echo_overlap_band="high",
        ),
        synthetic_rerun_turn(turn_index=2),
    ]

    summary = summarize_long_session_replay_observations(turns)["response_delta_summary"]

    assert summary["response_delta_checked_count"] == 2
    assert summary["response_delta_failed_count"] == 1
    assert summary["response_delta_repaired_count"] == 1
    assert summary["response_delta_kind_counts"] == {"new_fact": 2}
    assert summary["response_delta_unknown_count"] == 1
    assert summary["echo_overlap_band_counts"] == {"high": 1, "low": 1}


def test_compare_golden_replay_reruns_reports_response_delta_frequency_deltas():
    previous = [
        synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=False,
            response_delta_repaired=False,
            response_delta_kind="new_fact",
            response_delta_echo_overlap_band="low",
        )
    ]
    current = [
        synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=True,
            response_delta_repaired=True,
            response_delta_kind="new_actionable_lead",
            response_delta_echo_overlap_band="high",
        )
    ]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["semantic_delta_frequency_delta_count"] == 1
    response_delta = scorecard["frequencies"]["response_delta"]
    assert response_delta["failed"]["delta"] == {"failed": 1}
    assert response_delta["repaired"]["delta"] == {"repaired": 1}
    assert response_delta["kinds"]["delta"] == {"new_actionable_lead": 1, "new_fact": -1}
    assert response_delta["echo_overlap_bands"]["delta"] == {"high": 1, "low": -1}
    assert scorecard["per_turn_deltas"][0]["deltas"]["response_delta"]["response_delta_failed"] == {
        "previous": False,
        "current": True,
    }


def test_long_session_replay_summary_renderer_surfaces_operator_metrics():
    turns = [
        {
            "turn_index": 0,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "post_gate_mutation_detected": False,
            "unavailable": [],
            "runtime_lineage_events": [],
        },
        {
            "turn_index": 1,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "post_gate_mutation_detected": True,
            "unavailable": ["fallback_family"],
            "runtime_lineage_events": [
                {
                    "event_type": "runtime_lineage",
                    "event_kind": "fallback_selected",
                    "stage": "gate",
                    "owner": "game.final_emission_gate",
                    "source": "neutral_reply_speaker_grounding_bridge",
                    "fallback_kind": "sealed_or_global_replacement",
                    "recurrence_key": "fallback_selected:gate:game.final_emission_gate:sealed_or_global_replacement",
                }
            ],
        },
    ]
    summary = {
        "turn_count": 2,
        "route_frequency": {"dialogue": 2},
        "route_change_count": 0,
        "speaker_frequency": {"runner": 2},
        "speaker_change_count": 0,
        "speaker_missing_count": 0,
        "mutation_turn_count": 1,
        "unavailable_counts": {"fallback_family": 1},
        "response_delta_summary": {
            "response_delta_checked_count": 1,
            "response_delta_failed_count": 0,
            "response_delta_repaired_count": 0,
            "response_delta_kind_counts": {"new_fact": 1},
            "response_delta_unknown_count": 1,
            "echo_overlap_band_counts": {"low": 1},
        },
        "lineage_summary": {
            "by_event_kind": {"fallback_selected": 1},
            "recurring_events": [
                {
                    "recurrence_key": "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
                    "count": 2,
                }
            ],
        },
        "fallback_escalation_summary": {
            "fallback_total_count": 1,
            "fallback_family_counts": {},
            "fallback_owner_counts": {},
            "fallback_lineage_kind_counts": {"sealed_or_global_replacement": 1},
            "max_fallback_streak": 1,
            "late_window_fallback_count": 0,
            "escalation_warnings": [],
        },
        "continuity_warning_count": 0,
        "continuity_violation_count": 0,
        "continuity_drift": {
            "session_health": {"classification": "clean", "degradation_detected": False},
            "degradation_over_time": {"reason_codes": [], "late_window": {"signals": []}},
        },
    }

    report = render_long_session_replay_summary_markdown(
        scenario_id="synthetic_long_session",
        turns=turns,
        summary=summary,
        title="Synthetic Long Session",
    )

    assert "- Route changes: `0`" in report
    assert "- Speaker changes / missing: `0` / `0`" in report
    assert "- Continuity classification: `clean`" in report
    assert "- Fallback total count: `1`" in report
    assert "- Fallback lineage kinds: `{'sealed_or_global_replacement': 1}`" in report
    assert "- Mutation turn count: `1`" in report
    assert "- Response-delta checked / failed / repaired: `1` / `0` / `0`" in report
    assert "- Response-delta kinds: `{'new_fact': 1}`" in report
    assert "- Response-delta unknown count: `1`" in report
    assert "- Echo-overlap bands: `{'low': 1}`" in report
    assert "- Unavailable counts: `{'fallback_family': 1}`" in report
    assert "- Lineage recurrence: `[" in report
    assert "- Fallback frequency:" not in report
    assert "- Mutation turns:" not in report


def test_long_session_stability_scorecard_projects_existing_metrics(monkeypatch):
    def _forbidden_eval(*_args, **_kwargs):
        raise AssertionError("evaluate_scenario_spine_session must not be called from scorecard projection")

    monkeypatch.setattr(
        "tests.helpers.golden_replay.evaluate_scenario_spine_session",
        _forbidden_eval,
    )
    turns = [
        {
            "turn_index": 0,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "branch_id": "branch_social_inquiry",
            "source_path": FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
            "runtime_lineage_events": [],
        },
        {
            "turn_index": 1,
            "route_kind": "social",
            "selected_speaker_id": "runner",
            "branch_id": "branch_social_inquiry",
            "source_path": FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
            "runtime_lineage_events": [],
        },
    ]
    continuity_result = {
        "evaluation": {
            "session_health": {
                "classification": "clean",
                "long_session_band": "long",
                "overall_passed": True,
            },
            "degradation_over_time": {
                "progressive_degradation_detected": False,
                "reason_codes": [],
            },
        }
    }

    scorecard = build_long_session_stability_scorecard(
        scenario_id="synthetic_long_session",
        branch_id="branch_social_inquiry",
        source_path=FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
        observations=turns,
        continuity_result=continuity_result,
    )

    assert scorecard["schema_version"] == 1
    assert scorecard["artifact_kind"] == "long_session_stability_scorecard"
    assert scorecard["report_only"] is True
    assert scorecard["scenario_id"] == "synthetic_long_session"
    assert scorecard["branch_id"] == "branch_social_inquiry"
    assert scorecard["source_path"] == FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
    assert scorecard["turn_count"] == 2
    assert scorecard["route_stability"]["route_change_count"] == 1
    assert scorecard["route_stability"]["route_frequency"] == {"dialogue": 1, "social": 1}
    assert scorecard["speaker_stability"]["speaker_change_count"] == 0
    assert scorecard["speaker_stability"]["speaker_missing_count"] == 0
    assert scorecard["fallback_stability"]["fallback_count"] == 0
    assert scorecard["fallback_stability"]["escalation_warnings"] == []
    assert scorecard["degradation"]["progressive_degradation_detected"] is False
    assert scorecard["operational_summary"]["stability_status"] == "stable"
    assert scorecard["operational_summary"]["actionable"] is False
    assert scorecard["operational_summary"]["warning_count"] == 0
    route_rows = [row for row in scorecard["owner_drift_classifications"] if row["owner_drift_bucket"] == "route_drift"]
    assert len(route_rows) == 1
    assert route_rows[0]["signal"] == "route_change"
    assert scorecard["owner_drift_bucket_counts"]["route_drift"] == 1

    markdown = render_long_session_stability_scorecard_markdown(scorecard)
    assert "- Stability status: `stable`" in markdown
    assert "- Route changes: `1`" in markdown
    assert "- Speaker changes: `0`" in markdown
    assert "## Stability Ownership" in markdown
    assert "`route_drift`" in markdown


def test_long_session_stability_scorecard_marks_degradation_report_only(monkeypatch):
    def _forbidden_eval(*_args, **_kwargs):
        raise AssertionError("evaluate_scenario_spine_session must not be called from scorecard projection")

    monkeypatch.setattr(
        "tests.helpers.golden_replay.evaluate_scenario_spine_session",
        _forbidden_eval,
    )
    turns = [
        {
            "turn_index": 0,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "runtime_lineage_events": [],
        }
    ]
    continuity_result = {
        "evaluation": {
            "session_health": {
                "classification": "warning",
                "long_session_band": "long",
                "overall_passed": False,
            },
            "degradation_over_time": {
                "progressive_degradation_detected": True,
                "reason_codes": ["rising_generic_filler_progressive"],
            },
        }
    }

    scorecard = build_long_session_stability_scorecard(
        scenario_id="synthetic_degraded_session",
        observations=turns,
        continuity_result=continuity_result,
        lineage_summary={
            "by_event_kind": {"fallback_selected": 3},
            "recurring_events": [
                {"recurrence_key": "fallback_selected:gate:game.final_emission_gate:repair", "count": 3}
            ],
        },
    )

    assert scorecard["report_only"] is True
    assert scorecard["degradation"]["progressive_degradation_detected"] is True
    assert scorecard["degradation"]["reason_codes"] == ["rising_generic_filler_progressive"]
    assert scorecard["operational_summary"]["stability_status"] == "degraded"
    assert scorecard["operational_summary"]["actionable"] is True
    assert scorecard["operational_summary"]["warning_count"] >= 2
    assert scorecard["lineage_stability"]["event_counts"] == {"fallback_selected": 3}
    assert scorecard["report_only"] is True
    degradation_rows = [
        row for row in scorecard["owner_drift_classifications"] if row["signal"] == "progressive_degradation"
    ]
    assert len(degradation_rows) == 1
    assert degradation_rows[0]["owner_drift_bucket"] == "semantic_drift"
    assert scorecard["owner_drift_bucket_counts"]["semantic_drift"] >= 1
    fallback_rows = [
        row for row in scorecard["owner_drift_classifications"] if row["owner_drift_bucket"] == "fallback_drift"
    ]
    assert fallback_rows
    markdown = render_long_session_stability_scorecard_markdown(scorecard)
    assert "## Stability Ownership" in markdown
    assert "`semantic_drift`" in markdown


def test_long_session_stability_scorecard_owner_drift_speaker_signal():
    scorecard = build_long_session_stability_scorecard(
        scenario_id="speaker_drift_probe",
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "dialogue", "selected_speaker_id": "guard"},
            {"turn_index": 2, "route_kind": "dialogue"},
        ],
    )
    speaker_rows = [row for row in scorecard["owner_drift_classifications"] if row["owner_drift_bucket"] == "speaker_drift"]
    assert {row["signal"] for row in speaker_rows} == {"speaker_change", "speaker_missing"}
    assert scorecard["owner_drift_bucket_counts"]["speaker_drift"] == 2


def test_long_session_stability_scorecard_owner_drift_fallback_recurrence():
    scorecard = build_long_session_stability_scorecard(
        scenario_id="fallback_drift_probe",
        observations=[
            {
                "turn_index": 0,
                "route_kind": "action",
                "fallback_family": "gate_terminal_repair",
                "runtime_lineage_events": [
                    {
                        "event_kind": "fallback_selected",
                        "recurrence_key": "fallback_selected:gate:game.final_emission_gate:repair",
                    }
                ],
            },
            {
                "turn_index": 1,
                "route_kind": "action",
                "fallback_family": "gate_terminal_repair",
                "runtime_lineage_events": [
                    {
                        "event_kind": "fallback_selected",
                        "recurrence_key": "fallback_selected:gate:game.final_emission_gate:repair",
                    }
                ],
            },
        ],
        lineage_summary={
            "by_event_kind": {"fallback_selected": 2},
            "recurring_events": [
                {"recurrence_key": "fallback_selected:gate:game.final_emission_gate:repair", "count": 2}
            ],
        },
    )
    fallback_rows = [row for row in scorecard["owner_drift_classifications"] if row["owner_drift_bucket"] == "fallback_drift"]
    assert any(row["signal"] == "fallback_count" for row in fallback_rows)
    assert any(row["signal"] == "lineage_recurrence" for row in fallback_rows)
    assert scorecard["owner_drift_bucket_counts"]["fallback_drift"] >= 2


def test_long_session_stability_scorecard_owner_drift_stable_has_no_classifications():
    scorecard = build_long_session_stability_scorecard(
        scenario_id="stable_probe",
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "dialogue", "selected_speaker_id": "runner"},
        ],
        continuity_result={
            "evaluation": {
                "session_health": {"classification": "clean", "overall_passed": True},
                "degradation_over_time": {
                    "progressive_degradation_detected": False,
                    "reason_codes": [],
                },
            }
        },
    )
    assert scorecard["owner_drift_classifications"] == []
    assert scorecard["owner_drift_bucket_counts"]["route_drift"] == 0
    assert scorecard["owner_drift_bucket_counts"]["speaker_drift"] == 0
    assert scorecard["owner_drift_bucket_counts"]["fallback_drift"] == 0
    markdown = render_long_session_stability_scorecard_markdown(scorecard)
    assert "No stability ownership classifications." in markdown


def test_stability_classification_rows_from_scorecard_projects_owner_fields():
    scorecard = build_long_session_stability_scorecard(
        scenario_id="projection_probe",
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "social", "selected_speaker_id": "runner"},
        ],
    )
    from tests.helpers.replay_drift_taxonomy import (
        aggregate_long_session_stability_classifications,
        stability_classification_rows_from_scorecard,
    )

    rows = stability_classification_rows_from_scorecard(scorecard)
    assert rows
    assert rows[0]["scenario_id"] == "projection_probe"
    assert {"signal", "owner_drift_bucket", "severity_hint", "stability_status", "reason", "evidence"} <= set(rows[0])
    assert rows[0]["owner_drift_bucket"] == "route_drift"

    aggregation = aggregate_long_session_stability_classifications([scorecard])
    assert aggregation["total_scorecards"] == 1
    assert aggregation["bucket_frequencies"]["route_drift"] == 1
    assert aggregation["scenario_frequencies"]["projection_probe"] == 1
    assert aggregation["stability_status_counts"]["stable"] == 1
    assert aggregation == aggregate_long_session_stability_classifications([scorecard])


def test_stability_ownership_projection_stable_scorecard_empty():
    from tests.helpers.replay_drift_taxonomy import stability_classification_rows_from_scorecard

    scorecard = build_long_session_stability_scorecard(
        scenario_id="stable_projection_probe",
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "dialogue", "selected_speaker_id": "runner"},
        ],
    )
    assert stability_classification_rows_from_scorecard(scorecard) == []


def test_stability_ownership_projection_degraded_scorecard_surfaces_rows():
    from tests.helpers.replay_drift_taxonomy import stability_classification_rows_from_scorecard

    scorecard = build_long_session_stability_scorecard(
        scenario_id="degraded_projection_probe",
        observations=[{"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"}],
        continuity_result={
            "evaluation": {
                "session_health": {"classification": "warning", "overall_passed": False},
                "degradation_over_time": {
                    "progressive_degradation_detected": True,
                    "reason_codes": ["rising_generic_filler_progressive"],
                },
            }
        },
    )
    rows = stability_classification_rows_from_scorecard(scorecard)
    assert rows
    assert all(row["stability_status"] == "degraded" for row in rows)
    assert any(row["owner_drift_bucket"] == "semantic_drift" for row in rows)


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


def test_golden_replay_directed_npc_question_structural_invariants(tmp_path, monkeypatch):
    captured_prompts: list[list[dict]] = []

    def _fake_call_gpt(messages):
        captured_prompts.append(messages)
        return gm_response('Tavern Runner grimaces. "I heard east-road talk, but no names."')

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="directed_npc_question",
        turns=["Runner, who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_investigator_runner_world,
    )

    assert captured_prompts
    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert_protected_golden_turn_observation(
        turn,
        protected_social_directed_question_expectation("runner"),
        scenario_id="directed_npc_question",
        debug_context=format_golden_replay_debug(result),
    )


def test_golden_replay_vocative_override_after_prior_continuity_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response('Tavern Runner says, "I saw the patrol turn toward the east lanes."'),
            gm_response('Gate Guard says, "I saw fresh mud by the north arch."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="vocative_override_after_prior_continuity",
        turns=[
            "Runner, where did the patrol go?",
            "Guard, what did you see?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_guard_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="guard",
            require_route_kind=False,
            require_final_emitted_source=False,
            allow_unavailable=(
                "fallback_family",
                "final_emitted_source",
                "route_kind",
                "trace.canonical_entry",
                "trace.turn_trace",
                "trace.social_contract_trace",
            ),
            include_route_kind=False,
        ),
        scenario_id="vocative_override_after_prior_continuity",
        debug_context=debug_context,
    )
    if "route_kind" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            protected_social_supplemental_structural_expectation(),
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
            turn,
            protected_social_vocative_canonical_entry_expectation("guard"),
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    social_contract_trace = (turn.get("trace") or {}).get("social_contract_trace") or {}
    if social_contract_trace.get("route_selected") is not None:
        assert_protected_golden_turn_observation(
            turn,
            protected_social_supplemental_structural_expectation(include_trace_route=True),
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )


def test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response('Merchant says, "I know nothing about that."'),
    )

    result = run_golden_replay(
        scenario_id="wrong_speaker_strict_social_emission",
        turns=["Who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_continuity_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="runner",
            allow_unavailable=("fallback_family", "final_emitted_source"),
            require_route_kind=False,
            require_final_emitted_source=False,
            include_route_kind=False,
            extra_no_scaffold_terms=("Merchant",),
        ),
        scenario_id="wrong_speaker_strict_social_emission",
        debug_context=debug_context,
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            protected_social_supplemental_structural_expectation(
                require_present=("final_emitted_source",),
            ),
            scenario_id="wrong_speaker_strict_social_emission",
            debug_context=debug_context,
        )


def test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants(monkeypatch):
    session, world, scene_id, resolution = runner_strict_bundle()
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
            allowed_pregate_speaker_labels=["Ragged stranger"],
            speaker_alias_resolution_source="manual_bundle_override",
        ),
    )
    patch_get_speaker_selection_contract(monkeypatch, locked_runner_contract())
    pre_gate_line = 'Ragged stranger says, "No names, only rumors."'
    patch_build_final_strict_social_response(
        monkeypatch, line=pre_gate_line, strict_social_details=stub_strict_social_details
    )

    out = apply_final_emission_gate(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        world=world,
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_fem_meta_from_gate_output(out) or {}
    npc_id = (resolution.get("social") or {}).get("npc_id")
    turn = observed_turn_from_gate_output(
        scenario_id="declared_alias_dialogue_plan",
        gm_output=out,
        resolution=resolution,
        extra_fields={
            "trace": {
                "canonical_entry": {
                    "target_actor_id": npc_id,
                    "declared_alias_target_actor_id": npc_id,
                    "allowed_pregate_speaker_labels": ["Ragged stranger"],
                    "speaker_alias_resolution_source": "manual_bundle_override",
                }
            },
            "dialogue_plan_valid": meta.get("dialogue_plan_valid"),
        },
        unavailable=["fallback_family"],
    )

    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="runner",
            canonical_target_id="runner",
            require_present=("trace.canonical_entry.declared_alias_target_actor_id",),
            require_route_kind=False,
            equals={
                "trace.canonical_entry.declared_alias_target_actor_id": "runner",
                "trace.canonical_entry.speaker_alias_resolution_source": "manual_bundle_override",
                "dialogue_plan_valid": True,
            },
            include_route_kind=False,
        ),
        scenario_id="declared_alias_dialogue_plan",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )


def test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response("The scene pauses without offering anything concrete."),
        suppress_exploration=False,
        suppress_intent=False,
    )

    result = run_golden_replay(
        scenario_id="thin_answer_action_outcome_final_emission",
        turns=["I examine the notice board; does it show where the missing patrol went?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    low = str(turn.get("final_text") or "").lower()
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text", "final_emitted_source"),
            allow_unavailable=(
                "fallback_family",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            equals={
                "response_type_required": "action_outcome",
                "response_type_repair_used": True,
            },
            include_route_kind=False,
            disallow_global_scene_fallback=True,
            extra_no_scaffold_terms=(
                "scene pauses",
                "nothing concrete",
                "no name comes clear",
            ),
        ),
        scenario_id="thin_answer_action_outcome_final_emission",
        debug_context=debug_context,
    )
    assert "patrol" in low or "east ridge" in low or "notice" in low, debug_context
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True


def test_golden_replay_sanitizer_scaffold_leakage_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response(
            "Planner: route via router. Validator: unresolved scaffold."
        ),
    )

    result = run_golden_replay(
        scenario_id="sanitizer_scaffold_leakage",
        turns=["Where should I start?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text",),
            allow_unavailable=(
                "fallback_family",
                "final_emitted_source",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            include_route_kind=False,
            extra_no_scaffold_terms=("Planner", "Validator"),
        ),
        scenario_id="sanitizer_scaffold_leakage",
        debug_context=format_golden_replay_debug(result),
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            {
                **protected_unavailable_expectation(
                    "fallback_family",
                    "selected_speaker_id",
                    "trace.canonical_entry",
                    "trace.social_contract_trace",
                ),
                "require_present": ["final_emitted_source"],
            },
            scenario_id="sanitizer_scaffold_leakage",
            debug_context=format_golden_replay_debug(result),
        )


def test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership():
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_fem_meta_from_gate_output(out) or {}
    turn = observed_turn_from_gate_output(
        scenario_id="opening_fallback_path",
        gm_output=out,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        unavailable=[],
    )

    assert_protected_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "final_emitted_source", "fallback_family", "opening_fallback_owner_bucket"],
            "equals": successful_opening_observed_fields(
                include_owner_bucket=True,
                response_type_required="scene_opening",
                response_type_repair_used=True,
            ),
            "not_equals": {
                "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
            },
            **protected_no_scaffold_expectation(),
        },
        scenario_id="opening_fallback_path",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )
    assert turn["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert turn["opening_fallback_authorship_source"] != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert meta.get("fallback_family_used") == "scene_opening"
    assert meta.get("realization_fallback_family") == "upstream_prepared_emission"
    assert meta.get("realization_fallback_family") != "legacy_diegetic_fallback"
    assert meta.get("fallback_family_used") != meta.get("realization_fallback_family")


def test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership():
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    meta = read_fem_meta_from_gate_output(out) or {}
    assert meta.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert opening_fallback_owner_bucket_from_meta(meta) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response(
                'Tavern Runner says, "The patrol never came back from the old milestone beyond the east road."'
            ),
            gm_response('Tavern Runner says, "Last reliable sign was the old milestone."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="lead_followup_with_dialogue_lock",
        turns=[
            "Tavern Runner, what happened to the patrol?",
            "Runner, where were they last seen?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_tavern_patrol_lead_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="tavern_runner",
            require_final_emitted_source=True,
            include_trace_route=True,
        ),
        scenario_id="lead_followup_with_dialogue_lock",
        debug_context=debug_context,
    )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
            turn,
            protected_social_trace_target_expectation("tavern_runner"),
            scenario_id="lead_followup_with_dialogue_lock",
            debug_context=debug_context,
        )


def test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability(tmp_path, monkeypatch):
    turns = frontier_gate_branch_prompts("branch_social_inquiry")
    turn_ids = frontier_gate_branch_turn_ids("branch_social_inquiry")
    spine = load_frontier_gate_long_session_spine()
    assert len(turns) == 25

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The gate inquiry stays anchored: the notice board, Captain Thoran, the Ash Compact census "
                "delay, muddy footprints northwest of the crates, and the missing patrol route remain in view. "
                f"The answer advances the same thread at deterministic call {gpt_call_count}."
            )
        )

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="frontier_gate_social_inquiry_25_turn",
        turns=turns,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_frontier_gate_world,
        starting_scene_id="frontier_gate",
        source_path=FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
        branch_id="branch_social_inquiry",
        turn_ids=turn_ids,
    )

    observed_turns = result["turns"]
    assert observed_turns[0]["source_path"] == FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
    assert observed_turns[0]["branch_id"] == "branch_social_inquiry"
    assert observed_turns[0]["turn_id"] == "inv_01"
    assert observed_turns[-1]["turn_id"] == "inv_25"
    summary = summarize_long_session_replay_observations(observed_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id="branch_social_inquiry",
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_social_inquiry_25_turn",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Structural Stability",
            ),
        ]
    )
    assert f"source_path: {FRONTIER_GATE_LONG_SESSION_SOURCE_PATH!r}" in debug_context
    assert "branch_id: 'branch_social_inquiry'" in debug_context
    assert "turn_id: 'inv_01'" in debug_context

    social_inquiry_stability_profile = {
        "result_turn_count": 25,
        "summary_equals": {"turn_count": 25},
        "no_scaffold_leakage": True,
        "summary_max": {
            "speaker_change_count": 2,
            "speaker_missing_count": 2,
            "fallback_turn_count": 1,
            "fallback_owner_change_count": 1,
            "route_change_count": 2,
        },
        "min_resolved_routes": 12,
        # The full 25-turn branch crosses the evaluator's long-session band; the prior
        # protected 20-turn slice was still classified as standard.
        "session_health": {
            "equals": {"long_session_band": "long", "overall_passed": True},
            "classification_in": {"clean", "warning"},
        },
        "degradation": {
            "equals": {"progressive_degradation_detected": False},
            "absent_reason_codes": {
                "late_session_reset_or_amnesia",
                "rising_generic_filler_strong",
                "rising_generic_filler_progressive",
                "debug_leak_late_window",
                "referent_loss_late",
                "continuity_anchor_late_loss",
            },
        },
        "continuity_axes_passed": {"narrative_grounding", "branch_coherence"},
    }
    assert_long_session_stability_profile(
        result=result,
        turns=observed_turns,
        summary=summary,
        continuity_eval=continuity_eval,
        expected=social_inquiry_stability_profile,
        debug_context=debug_context,
    )

    social_inquiry_lineage_profile = {
        "fallback_frequency_total_max": 1,
        "event_kind_max": {"fallback_selected": 1, "mutation": 25},
        "mutation_kind_max": {"fallback_mutation": 1, "final_emission_mutation": 25},
        "allowed_recurring_keys": {
            "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
            "mutation:gate:game.final_emission_gate:final_emission_mutation",
        },
        "max_recurring_event_count": 25,
    }
    assert_runtime_lineage_profile(
        lineage_summary=summary["lineage_summary"],
        expected=social_inquiry_lineage_profile,
        debug_context=debug_context,
    )

    social_inquiry_fallback_escalation_profile = {
        "equals": {
            "late_window_fallback_count": 0,
            "fallback_owner_change_count": 0,
            "fallback_lineage_owner_change_count": 0,
            "fallback_behavior_repair_count": 0,
            "sanitizer_fallback_count": 0,
            "escalation_warnings": [],
            "model_routing_escalation_observable": False,
        },
        "max": {
            "fallback_total_count": 1,
            "max_fallback_streak": 1,
            "response_type_repair_count": 1,
            "unavailable_with_fallback_count": 1,
            "fallback_selected_without_family_count": 1,
        },
    }
    assert_fallback_escalation_profile(
        fallback_escalation=summary["fallback_escalation_summary"],
        expected=social_inquiry_fallback_escalation_profile,
        debug_context=debug_context,
    )


def test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting(tmp_path, monkeypatch):
    # Supporting checkpoint probe: this uses a real on-disk snapshot restore at
    # the 12/13 boundary, but keeps the protected lock on the uninterrupted run.
    turns = frontier_gate_branch_prompts("branch_social_inquiry")
    turn_ids = frontier_gate_branch_turn_ids("branch_social_inquiry")
    spine = load_frontier_gate_long_session_spine()
    split_at = 12
    assert len(turns) == 25
    assert turn_ids[split_at - 1] == "inv_12"
    assert turn_ids[split_at] == "inv_13"

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The resumed gate inquiry stays anchored: the notice board, Captain Thoran, "
                "the Ash Compact census delay, muddy footprints northwest of the crates, "
                "and the missing patrol route remain in view. "
                f"The answer advances the same thread at deterministic call {gpt_call_count}."
            )
        )

    observed_turns = []
    checkpoint_meta = None
    restored_meta = None
    pre_resume_counter = None
    post_restore_counter = None
    post_restore_log_count = None

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    new_clean_campaign(starting_scene_id="frontier_gate")
    seed_frontier_gate_world()

    for i, text in enumerate(turns[:split_at]):
        payload = chat(ChatRequest(text=text))
        snap = snapshot_from_chat_payload(i, text, payload)
        observed_turns.append(
            _observed_turn(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                snap=snap,
                payload=payload,
                replay_identity={
                    "source_path": FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
                    "branch_id": "branch_social_inquiry",
                    "turn_id": turn_ids[i],
                },
            )
        )

    pre_resume_counter = int(storage.load_session().get("turn_counter") or 0)
    checkpoint_meta = storage.create_snapshot(label="golden-social-inquiry-after-turn-12")
    restored_meta = storage.load_snapshot(str(checkpoint_meta["id"]))
    post_restore_session = storage.load_session()
    post_restore_counter = int(post_restore_session.get("turn_counter") or 0)
    post_restore_log_count = len(storage.load_log())

    for i, text in enumerate(turns[split_at:], start=split_at):
        payload = chat(ChatRequest(text=text))
        snap = snapshot_from_chat_payload(i, text, payload)
        observed_turns.append(
            _observed_turn(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                snap=snap,
                payload=payload,
                replay_identity={
                    "source_path": FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
                    "branch_id": "branch_social_inquiry",
                    "turn_id": turn_ids[i],
                },
            )
        )

    result = {
        "scenario_id": "frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
        "turn_count": len(observed_turns),
        "turns": observed_turns,
    }
    pre_resume_turns = observed_turns[:split_at]
    post_resume_turns = observed_turns[split_at:]
    summary = summarize_long_session_replay_observations(observed_turns)
    pre_summary = summarize_long_session_replay_observations(pre_resume_turns)
    post_summary = summarize_long_session_replay_observations(post_resume_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id="branch_social_inquiry",
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            f"split_at: {split_at}",
            f"checkpoint_meta: {checkpoint_meta!r}",
            f"restored_meta: {restored_meta!r}",
            f"pre_resume_counter: {pre_resume_counter!r}",
            f"post_restore_counter: {post_restore_counter!r}",
            f"post_restore_log_count: {post_restore_log_count!r}",
            f"pre_resume_summary: {pre_summary!r}",
            f"post_resume_summary: {post_summary!r}",
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Resume Persistence Supporting Probe",
            ),
        ]
    )

    assert checkpoint_meta is not None, debug_context
    assert restored_meta is not None, debug_context
    assert pre_resume_counter == split_at, debug_context
    assert post_restore_counter == split_at, debug_context
    assert post_restore_log_count == split_at, debug_context
    assert storage.load_session().get("turn_counter") == 25, debug_context
    assert len(storage.load_log()) == 25, debug_context

    assert result["turn_count"] == 25, debug_context
    assert summary["turn_count"] == 25, debug_context
    assert [turn.get("turn_index") for turn in observed_turns] == list(range(25)), debug_context
    assert [turn.get("turn_id") for turn in observed_turns] == turn_ids, debug_context
    assert observed_turns[split_at - 1]["turn_id"] == "inv_12", debug_context
    assert observed_turns[split_at]["turn_id"] == "inv_13", debug_context
    assert observed_turns[0]["source_path"] == FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
    assert observed_turns[0]["branch_id"] == "branch_social_inquiry"
    assert observed_turns[-1]["turn_id"] == "inv_25"

    assert pre_summary["turn_count"] == split_at, debug_context
    assert post_summary["turn_count"] == 25 - split_at, debug_context
    assert pre_summary["speaker_missing_count"] <= 2, debug_context
    assert post_summary["speaker_missing_count"] <= 1, debug_context
    assert observed_turns[split_at]["selected_speaker_id"] is not None, debug_context
    assert observed_turns[split_at]["selected_speaker_source"] is not None, debug_context
    resume_stability_profile = {
        "result_turn_count": 25,
        "summary_equals": {"turn_count": 25},
        "no_scaffold_leakage": True,
        "summary_max": {
            "speaker_change_count": 2,
            "speaker_missing_count": 2,
            "fallback_turn_count": 1,
            "fallback_owner_change_count": 1,
            "route_change_count": 2,
        },
        "session_health": {
            "equals": {"long_session_band": "long", "overall_passed": True},
            "classification_in": {"clean", "warning"},
        },
        "degradation": {
            "equals": {"progressive_degradation_detected": False},
            "absent_reason_codes": {
                "late_session_reset_or_amnesia",
                "rising_generic_filler_strong",
                "rising_generic_filler_progressive",
                "debug_leak_late_window",
                "referent_loss_late",
                "continuity_anchor_late_loss",
            },
        },
        "continuity_axes_passed": {"narrative_grounding", "branch_coherence"},
    }
    assert_long_session_stability_profile(
        result=result,
        turns=observed_turns,
        summary=summary,
        continuity_eval=continuity_eval,
        expected=resume_stability_profile,
        debug_context=debug_context,
    )

    resume_lineage_profile = {
        "event_kind_max": {"fallback_selected": 1, "mutation": 25},
        "mutation_kind_max": {"fallback_mutation": 1, "final_emission_mutation": 25},
        "allowed_recurring_keys": {
            "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
            "mutation:gate:game.final_emission_gate:final_emission_mutation",
        },
        "max_recurring_event_count": 25,
    }
    assert_runtime_lineage_profile(
        lineage_summary=summary["lineage_summary"],
        expected=resume_lineage_profile,
        debug_context=debug_context,
    )

    resume_fallback_escalation_profile = {
        "equals": {
            "late_window_fallback_count": 0,
            "fallback_owner_change_count": 0,
            "fallback_lineage_owner_change_count": 0,
            "fallback_behavior_repair_count": 0,
            "sanitizer_fallback_count": 0,
            "escalation_warnings": [],
            "model_routing_escalation_observable": False,
        },
        "max": {
            "fallback_total_count": 1,
            "max_fallback_streak": 1,
            "response_type_repair_count": 1,
            "unavailable_with_fallback_count": 1,
            "fallback_selected_without_family_count": 1,
        },
    }
    assert_fallback_escalation_profile(
        fallback_escalation=summary["fallback_escalation_summary"],
        expected=resume_fallback_escalation_profile,
        debug_context=debug_context,
    )


def test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability(tmp_path, monkeypatch):
    # Supporting diagnostic only: this branch intentionally stresses risky
    # action/visibility paths and currently emits more fallback lineage than the
    # protected social-inquiry baseline. Keep it supporting until it gets another
    # clean run after future fallback-family or action-routing changes.
    turns = frontier_gate_branch_prompts("branch_direct_intrusion")
    turn_ids = frontier_gate_branch_turn_ids("branch_direct_intrusion")
    spine = load_frontier_gate_long_session_spine()
    assert len(turns) == 25

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The direct intrusion stays anchored: the gate serjeant, roster board, cordon pressure, "
                "warehouse latch, muddy crates, and watch whistles remain in view. "
                f"The risky push advances the same forced-access thread at deterministic call {gpt_call_count}."
            )
        )

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="frontier_gate_direct_intrusion_25_turn_diagnostic",
        turns=turns,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_frontier_gate_world,
        starting_scene_id="frontier_gate",
        source_path=FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
        branch_id="branch_direct_intrusion",
        turn_ids=turn_ids,
    )

    observed_turns = result["turns"]
    assert observed_turns[0]["source_path"] == FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
    assert observed_turns[0]["branch_id"] == "branch_direct_intrusion"
    assert observed_turns[0]["turn_id"] == "act_01"
    assert observed_turns[-1]["turn_id"] == "act_25"
    summary = summarize_long_session_replay_observations(observed_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id="branch_direct_intrusion",
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_direct_intrusion_25_turn_diagnostic",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Direct-Intrusion Diagnostic Stability",
            ),
        ]
    )
    assert f"source_path: {FRONTIER_GATE_LONG_SESSION_SOURCE_PATH!r}" in debug_context
    assert "branch_id: 'branch_direct_intrusion'" in debug_context
    assert "turn_id: 'act_01'" in debug_context

    direct_intrusion_stability_profile = {
        "result_turn_count": 25,
        "summary_equals": {
            "turn_count": 25,
            "fallback_turn_count": 7,
            "fallback_owner_change_count": 0,
        },
        "no_scaffold_leakage": True,
        "summary_max": {
            "route_change_count": 6,
            "speaker_change_count": 3,
            "speaker_missing_count": 20,
            "mutation_turn_count": 25,
        },
        "session_health": {
            "equals": {"long_session_band": "long", "overall_passed": True},
            "classification_in": {"clean", "warning"},
        },
        "degradation": {
            "equals": {"progressive_degradation_detected": False},
            "absent_reason_codes": {
                "late_session_reset_or_amnesia",
                "rising_generic_filler_strong",
                "rising_generic_filler_progressive",
                "debug_leak_late_window",
                "referent_loss_late",
                "continuity_anchor_late_loss",
            },
        },
        "continuity_axes_passed": {"narrative_grounding", "branch_coherence"},
    }
    assert_long_session_stability_profile(
        result=result,
        turns=observed_turns,
        summary=summary,
        continuity_eval=continuity_eval,
        expected=direct_intrusion_stability_profile,
        debug_context=debug_context,
    )

    fallback_frequency = summary["fallback_frequency"]
    assert set(fallback_frequency) <= {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "gate_terminal_repair",
    }, debug_context
    assert int(fallback_frequency.get(NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY) or 0) <= 4, debug_context
    assert int(fallback_frequency.get("gate_terminal_repair") or 0) <= 3, debug_context
    allowed_recurring_keys = {
        "gate_outcome:gate:game.final_emission_gate:accept_unchanged",
        "mutation:gate:game.final_emission_gate:fallback_mutation",
        "fallback_selected:gate:game.final_emission_gate:sealed_or_global_replacement",
        "gate_outcome:gate:game.final_emission_gate:replaced_or_sealed",
        "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
        "mutation:gate:game.final_emission_gate:final_emission_mutation",
        "fallback_selected:gate:game.final_emission_gate:response_type_prepared_emission",
        "gate_outcome:gate:game.final_emission_gate:prepared_repair",
        "mutation:gate:game.final_emission_gate:response_type_repair_mutation",
    } | {
        f"fallback_selected:gate:game.final_emission_gate:{subkind}"
        for subkind in SEALED_REPLACEMENT_SUBKINDS
    }
    direct_intrusion_lineage_profile = {
        "event_kind_equals": {"fallback_selected": 7},
        "event_kind_max": {"mutation": 14, "speaker_repair": 1},
        "mutation_kind_max": {
            "fallback_mutation": 7,
            "final_emission_mutation": 4,
            "response_type_repair_mutation": 2,
            "speaker_repair_mutation": 1,
        },
        "allowed_recurring_keys": allowed_recurring_keys,
        "max_recurring_event_count": 25,
    }
    assert_runtime_lineage_profile(
        lineage_summary=summary["lineage_summary"],
        expected=direct_intrusion_lineage_profile,
        debug_context=debug_context,
    )

    direct_intrusion_fallback_escalation_profile = {
        "equals": {
            "fallback_total_count": 7,
            "max_blocking_fallback_streak": 0,
            "fallback_owner_change_count": 0,
            "fallback_lineage_owner_change_count": 0,
            "fallback_behavior_repair_count": 0,
            "sanitizer_fallback_count": 0,
            "scene_action_speaker_optional_unavailable_count": 7,
            "blocking_unavailable_with_fallback_count": 0,
            "fallback_selected_without_family_count": 0,
            "escalation_warnings": [],
            "model_routing_escalation_observable": False,
        },
        "max": {
            "max_fallback_streak": 2,
            "max_scene_action_nonblocking_fallback_streak": 2,
            "late_window_fallback_count": 2,
            "response_type_repair_count": 2,
            "unavailable_with_fallback_count": 7,
        },
        "allowed_fallback_families": {
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "gate_terminal_repair",
        },
        "fallback_family_counts": {
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY: 4,
            "gate_terminal_repair": 3,
        },
    }
    assert_fallback_escalation_profile(
        fallback_escalation=summary["fallback_escalation_summary"],
        expected=direct_intrusion_fallback_escalation_profile,
        debug_context=debug_context,
    )


def test_golden_replay_scenario_spine_three_branch_structural_smoke(tmp_path, monkeypatch):
    spine = ScenarioSpine(
        spine_id="golden_smoke_frontier_gate",
        title="Golden smoke three branch spine",
        smoke_only=True,
        fixed_start_state={"scene_id": "scene_investigate"},
        branches=(
            ScenarioBranch(
                branch_id="branch_runner_question",
                label="Ask the runner",
                turns=(ScenarioTurn(turn_id="runner_ask", player_prompt="Runner, who attacked the patrol?"),),
            ),
            ScenarioBranch(
                branch_id="branch_guard_question",
                label="Ask the guard",
                turns=(ScenarioTurn(turn_id="guard_ask", player_prompt="Guard, what did you see?"),),
            ),
            ScenarioBranch(
                branch_id="branch_notice_check",
                label="Check the notice",
                turns=(
                    ScenarioTurn(
                        turn_id="notice_check",
                        player_prompt="I examine the notice board; does it show where the missing patrol went?",
                    ),
                ),
            ),
        ),
    )
    assert validate_scenario_spine_definition(spine) == []
    spine_dict = scenario_spine_to_dict(spine)

    def _fake_call_gpt(_messages):
        return gm_response('Tavern Runner says, "The east road keeps the best clue."')

    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=_fake_call_gpt,
        suppress_exploration=False,
        suppress_intent=False,
    )

    branch_rows: list[dict] = []
    for branch in spine.branches:
        result = run_golden_replay(
            scenario_id=f"scenario_spine_three_branch::{branch.branch_id}",
            turns=[turn.player_prompt for turn in branch.turns],
            tmp_path=tmp_path / branch.branch_id,
            monkeypatch=monkeypatch,
            setup_fn=seed_spine_three_branch_world,
        )
        assert result["turn_count"] == len(branch.turns)
        for i, turn in enumerate(result["turns"]):
            meta = minimal_complete_transcript_turn_meta(
                spine_id=spine.spine_id,
                branch_id=branch.branch_id,
                turn_id=branch.turns[i].turn_id,
                turn_index=i,
                smoke=True,
                max_turns=len(branch.turns),
            )
            assert meta["scenario_spine"]["branch_id"] == branch.branch_id
            assert_golden_turn_observation(
                turn,
                {
                    **protected_structural_expectation(
                        require_present=("final_text",),
                        allow_unavailable=(
                            "fallback_family",
                            "selected_speaker_id",
                            "final_emitted_source",
                            "trace.canonical_entry",
                            "trace.social_contract_trace",
                        ),
                        no_scaffold=False,
                        include_route_kind=False,
                    ),
                    "scaffold_leakage": False,
                },
                debug_context=format_golden_replay_debug(result),
            )
        last = result["turns"][-1]
        branch_rows.append(
            {
                "branch_id": branch.branch_id,
                "turn_count": result["turn_count"],
                "route_kind": last.get("route_kind"),
                "selected_speaker_id": last.get("selected_speaker_id"),
                "final_emitted_source": last.get("final_emitted_source"),
                "fallback_family": last.get("fallback_family"),
            }
        )

    assert [row["branch_id"] for row in branch_rows] == [branch.branch_id for branch in spine.branches]
    assert {row["turn_count"] for row in branch_rows} == {1}
    assert len({(row["route_kind"], row["selected_speaker_id"]) for row in branch_rows}) >= 2
    assert [b["branch_id"] for b in spine_dict["branches"]] == sorted(row["branch_id"] for row in branch_rows)
