from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.replay_bug_recurrence import (
    BACKFILL_PROTECTED_REPLAY_PERSISTENCE_INTENT,
    DEFAULT_EVENT_SOURCE,
    PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    RECURRENCE_ADVISORY_ONLY,
    RECURRENCE_REPORT_ONLY,
    RECURRENCE_TREND_CLASSIFICATION_DORMANT,
    RECURRENCE_TREND_CLASSIFICATION_EMERGING,
    RECURRENCE_TREND_CLASSIFICATION_PERSISTENT,
    RECURRENCE_TREND_CLASSIFICATION_RECURRING,
    RECURRENCE_FORECAST_ELEVATED,
    RECURRENCE_FORECAST_STABLE,
    RECURRENCE_FORECAST_WATCH,
    RECURRENCE_FORECAST_CONCENTRATED,
    RECURRENCE_REMEDIATION_PRIORITY_CRITICAL,
    RECURRENCE_REMEDIATION_PRIORITY_HIGH,
    RECURRENCE_REMEDIATION_PRIORITY_LOW,
    RECURRENCE_REMEDIATION_PRIORITY_MEDIUM,
    RECURRENCE_GOVERNANCE_ACTION_GATHER_HISTORY,
    RECURRENCE_GOVERNANCE_ACTION_INVESTIGATE,
    RECURRENCE_GOVERNANCE_ACTION_PRIORITIZE,
    RECURRENCE_GOVERNANCE_ACTION_RETIRE,
    RECURRENCE_GOVERNANCE_INVESTIGATE,
    RECURRENCE_GOVERNANCE_OBSERVE,
    RECURRENCE_GOVERNANCE_PRIORITIZE,
    RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE,
    RECURRENCE_GOVERNANCE_WATCH,
    RECURRENCE_LIFECYCLE_DORMANT,
    RECURRENCE_LIFECYCLE_EMERGING,
    RECURRENCE_LIFECYCLE_PERSISTENT,
    RECURRENCE_LIFECYCLE_RECURRING,
    RECURRENCE_LIFECYCLE_RETIRED,
    RECURRENCE_LIFECYCLE_RETIREMENT_INACTIVITY_DAYS,
    RECURRENCE_MATURITY_DIMENSION_WEIGHTS,
    RECURRENCE_MATURITY_LEVEL_DEVELOPING,
    RECURRENCE_MATURITY_LEVEL_INITIAL,
    RECURRENCE_MATURITY_LEVEL_MANAGED,
    RECURRENCE_MATURITY_LEVEL_MEASURED,
    RECURRENCE_MATURITY_LEVEL_OPTIMIZED,
    RECURRENCE_MATURITY_TARGET_SCORE,
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
    RECURRENCE_REMEDIATION_COST_FLOOR,
    RECURRENCE_REMEDIATION_COST_HIGH,
    RECURRENCE_REMEDIATION_COST_LOW,
    RECURRENCE_REMEDIATION_COST_TRIVIAL,
    REGRESSION_RECURRENCE_RATE_METRIC,
    SUMMARY_RECURRENCE_STATUSES,
    aggregate_recurrence_history,
    aggregate_recurrence_history_from_event_log,
    aggregate_protected_recurrence_history_from_event_log,
    append_recurrence_events,
    append_recurrence_events_to_persistence_lanes,
    audit_recurrence_event_log_provenance,
    build_recurrence_forecast,
    build_recurrence_key,
    build_recurrence_portfolio,
    build_recurrence_remediation_targets,
    build_recurrence_roi_analysis,
    build_recurrence_governance,
    build_recurrence_lifecycle,
    build_recurrence_program_effectiveness,
    build_recurrence_maturity_assessment,
    build_recurrence_strategic_roadmap,
    build_recurrence_completion_assessment,
    build_recurrence_graduation_audit,
    build_recurrence_summary,
    build_recurrence_timeline,
    build_recurrence_trend_summary,
    calculate_protected_replay_regression_recurrence_rate,
    calculate_recurrence_reduction_potential,
    calculate_recurrence_roi,
    calculate_estimated_remediation_cost,
    calculate_recurrence_effectiveness_metrics,
    calculate_recurrence_maturity_score,
    calculate_maturity_investment_priority,
    calculate_recurrence_completion_score,
    calculate_recurrence_graduation_readiness_score,
    calculate_regression_recurrence_rate,
    classify_remediation_cost,
    classify_recurrence_governance_status,
    classify_recurrence_lifecycle_stage,
    classify_committed_recurrence_event_log,
    classify_recurrence_event_commit_worthiness,
    classify_recurrence_forecast,
    classify_remediation_priority,
    classify_recurrence_status,
    classify_recurrence_trend_entry,
    empty_recurrence_event_log,
    enrich_recurrence_history_with_forecasts,
    enrich_recurrence_history_with_portfolio,
    enrich_recurrence_history_with_remediation,
    enrich_recurrence_history_with_roi,
    enrich_recurrence_history_with_governance,
    enrich_recurrence_history_with_lifecycle,
    enrich_recurrence_history_with_program_effectiveness,
    enrich_recurrence_history_with_maturity,
    enrich_recurrence_history_with_roadmap,
    enrich_recurrence_history_with_completion,
    enrich_recurrence_history_with_graduation_audit,
    enrich_recurrence_history_with_confidence_audit,
    build_recurrence_confidence_audit,
    summarize_recurrence_confidence_calibration,
    calculate_confidence_calibration_score,
    render_recurrence_confidence_calibration_report_markdown,
    build_recurrence_final_graduation_decision,
    render_recurrence_final_graduation_decision_report_markdown,
    RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE,
    RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE,
    RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE,
    RECURRENCE_CONFIDENCE_STATUS_CALIBRATED,
    RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT,
    RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT,
    RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC,
    RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED,
    RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED,
    RECURRENCE_BLIND_SPOT_REDUCED,
    RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED,
    build_recurrence_outcome_validation,
    summarize_recurrence_outcomes,
    calculate_effectiveness_evidence_strength,
    render_recurrence_outcome_validation_report_markdown,
    enrich_recurrence_history_with_outcome_validation,
    RECURRENCE_OUTCOME_SIGNAL_DORMANT,
    RECURRENCE_OUTCOME_REJECTION_SYNTHETIC,
    BQC4_EFFECTIVENESS_BASELINE,
    BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD,
    enrich_recurrence_history_with_trends,
    is_commit_worthy_recurrence_event,
    is_synthetic_drift_recurrence_key,
    load_recurrence_event_log,
    normalize_recurrence_event_metadata,
    normalized_recurrence_event_source,
    recurrence_rows,
    recurrence_status,
    summarize_recurrence_growth,
    summarize_recurrence_portfolio,
    summarize_recurrence_remediation_opportunities,
    summarize_recurrence_roi,
    summarize_recurrence_governance,
    summarize_recurrence_lifecycle,
    summarize_recurrence_program_effectiveness,
    summarize_recurrence_maturity,
    summarize_recurrence_roadmap,
    summarize_recurrence_completion,
    summarize_recurrence_graduation_audit,
    validate_recurrence_program_capabilities,
    render_recurrence_graduation_audit_report_markdown,
    summarize_recurrence_risk,
    write_recurrence_event_log,
)


def _classification_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "scenario_id": "recurrence_probe",
        "turn_index": 2,
        "category": "speaker",
        "primary_owner": "speaker",
        "owner_drift_bucket": "speaker_drift",
        "field_path": "selected_speaker_id",
        "investigate_first": "game/speaker_contract_enforcement.py",
    }
    row.update(overrides)
    return row


def test_same_owner_category_field_produces_same_recurrence_key() -> None:
    left = _classification_row(scenario_id="left", turn_index=0)
    right = _classification_row(scenario_id="right", turn_index=9)

    assert build_recurrence_key(left) == build_recurrence_key(right)


def test_different_field_path_produces_different_recurrence_key() -> None:
    speaker_key = build_recurrence_key(_classification_row(field_path="selected_speaker_id"))
    route_key = build_recurrence_key(_classification_row(field_path="route_kind"))

    assert speaker_key != route_key


def test_missing_owner_bucket_falls_back_to_replay_drift_unclassified() -> None:
    row = _classification_row(owner_drift_bucket=None)

    assert build_recurrence_key(row).startswith("recurrence:v1:replay_drift_unclassified|")
    assert recurrence_rows([row])[0]["owner_drift_bucket"] == "replay_drift_unclassified"


def test_recurrence_rows_preserve_existing_classification_identity() -> None:
    row = _classification_row()

    projected = recurrence_rows([row])[0]

    assert projected["scenario_id"] == "recurrence_probe"
    assert projected["turn_index"] == 2
    assert projected["category"] == "speaker"
    assert projected["primary_owner"] == "speaker"
    assert projected["owner_drift_bucket"] == "speaker_drift"
    assert projected["recurrence_status"] == "active"


def test_helper_is_report_only_and_advisory_only() -> None:
    row = recurrence_rows([_classification_row()])[0]

    assert RECURRENCE_REPORT_ONLY is True
    assert RECURRENCE_ADVISORY_ONLY is True
    assert row["report_only"] is True
    assert row["advisory_only"] is True
    assert recurrence_status({"status": "retired"}) == "retired"
    assert recurrence_status({"status": "BLOCKED"}) == "active"


def test_repeated_keys_increment_occurrence_count() -> None:
    rows = recurrence_rows(
        [
            _classification_row(scenario_id="a"),
            _classification_row(scenario_id="b"),
        ]
    )

    history = aggregate_recurrence_history(rows)

    assert history["unique_recurrence_count"] == 1
    assert history["recurrences"][0]["occurrence_count"] == 2
    assert build_recurrence_summary(history)[0]["occurrence_count"] == 2


def test_first_and_last_seen_indexes_are_deterministic() -> None:
    repeated = _classification_row(scenario_id="a")
    other = _classification_row(
        scenario_id="b",
        field_path="route_kind",
        investigate_first="game/interaction_context.py",
    )
    rows = recurrence_rows([repeated, other, repeated])

    history = aggregate_recurrence_history(rows)
    repeated_entry = history["recurrences"][0]

    assert repeated_entry["first_seen_index"] == 0
    assert repeated_entry["last_seen_index"] == 2
    assert history["recurrences"][1]["first_seen_index"] == 1
    assert history["recurrences"][1]["last_seen_index"] == 1


def test_affected_scenarios_are_deduplicated_and_sorted() -> None:
    rows = recurrence_rows(
        [
            _classification_row(scenario_id="zeta"),
            _classification_row(scenario_id="alpha"),
            _classification_row(scenario_id="zeta"),
        ]
    )

    entry = aggregate_recurrence_history(rows)["recurrences"][0]

    assert entry["affected_scenarios"] == ["alpha", "zeta"]
    assert entry["categories"] == ["speaker"]
    assert entry["field_paths"] == ["selected_speaker_id"]


def test_active_status_is_preserved() -> None:
    rows = recurrence_rows([_classification_row(status="active")])

    entry = aggregate_recurrence_history(rows)["recurrences"][0]

    assert entry["status"] == "active"


def test_empty_input_returns_empty_report_only_advisory_only_history() -> None:
    history = aggregate_recurrence_history([])

    assert history["report_only"] is True
    assert history["advisory_only"] is True
    assert history["total_rows"] == 0
    assert history["unique_recurrence_count"] == 0
    assert history["recurrences"] == []
    assert build_recurrence_summary(history) == []
    metric = history["regression_recurrence_rate"]
    assert metric["metric"] == REGRESSION_RECURRENCE_RATE_METRIC
    assert metric["numerator"] == 0
    assert metric["denominator"] == 0
    assert metric["rate"] == 0.0
    assert metric["report_only"] is True
    assert metric["advisory_only"] is True


def test_repeated_recurrence_summary_becomes_active() -> None:
    history = aggregate_recurrence_history(
        recurrence_rows(
            [
                _classification_row(scenario_id="a"),
                _classification_row(scenario_id="b"),
            ]
        )
    )

    summary = build_recurrence_summary(history)

    assert summary[0]["status"] == "active"
    assert classify_recurrence_status(summary[0]) == "active"


def test_single_recurrence_summary_becomes_watch() -> None:
    history = aggregate_recurrence_history(recurrence_rows([_classification_row()]))

    assert build_recurrence_summary(history)[0]["status"] == "watch"


def test_explicit_retired_or_deprecated_input_becomes_retired() -> None:
    retired_history = aggregate_recurrence_history(recurrence_rows([_classification_row(status="retired")]))
    deprecated_history = aggregate_recurrence_history(recurrence_rows([_classification_row(status="deprecated")]))

    assert build_recurrence_summary(retired_history)[0]["status"] == "retired"
    assert build_recurrence_summary(deprecated_history)[0]["status"] == "retired"
    assert recurrence_status({"status": "deprecated"}) == "active"


def test_missing_status_never_becomes_retired_automatically() -> None:
    history = aggregate_recurrence_history(recurrence_rows([_classification_row(status=None)]))

    assert build_recurrence_summary(history)[0]["status"] == "watch"


def test_recurrence_status_vocabulary_is_bounded() -> None:
    assert SUMMARY_RECURRENCE_STATUSES == frozenset({"active", "watch", "retired"})
    history = aggregate_recurrence_history(
        recurrence_rows(
            [
                _classification_row(),
                _classification_row(field_path="route_kind", investigate_first="game/interaction_context.py"),
                _classification_row(status="deprecated"),
            ]
        )
    )

    assert {row["status"] for row in build_recurrence_summary(history)} <= SUMMARY_RECURRENCE_STATUSES


def test_protected_replay_manifest_documents_cycle_ay_recurrence_policy() -> None:
    manifest = Path("docs/testing/protected_replay_manifest.md").read_text(encoding="utf-8")

    assert "## Cycle AY Recurrence Reporting Addendum" in manifest
    assert "report_only: true" in manifest
    assert "advisory_only: true" in manifest
    assert "owner_drift_bucket`, `category`, `field_path`, and `investigate_first" in manifest
    assert "`retired` is explicit-only" in manifest
    assert "governance registry decisions" in manifest


def test_empty_recurrence_event_log_shape() -> None:
    log = empty_recurrence_event_log()

    assert log == {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        "events": [],
    }


def test_append_recurrence_events_preserves_existing_events() -> None:
    first = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="first")],
        event_source="run-a",
        recorded_at="2026-06-10T00:00:00Z",
    )
    second = append_recurrence_events(
        first,
        [_classification_row(scenario_id="second")],
        event_source="run-b",
        recorded_at="2026-06-11T00:00:00Z",
    )

    assert len(first["events"]) == 1
    assert len(second["events"]) == 2
    assert second["events"][0]["scenario_id"] == "first"
    assert second["events"][1]["scenario_id"] == "second"


def test_append_recurrence_events_assigns_monotonic_event_index() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a"), _classification_row(scenario_id="b")],
        recorded_at="2026-06-10T00:00:00Z",
    )
    log = append_recurrence_events(
        log,
        [_classification_row(scenario_id="c")],
        recorded_at="2026-06-11T00:00:00Z",
    )

    assert [event["event_index"] for event in log["events"]] == [0, 1, 2]


def test_aggregate_recurrence_history_from_event_log_becomes_active_after_two_same_key_events() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a")],
        recorded_at="2026-06-10T00:00:00Z",
    )
    log = append_recurrence_events(
        log,
        [_classification_row(scenario_id="b")],
        recorded_at="2026-06-11T00:00:00Z",
    )

    history = aggregate_recurrence_history_from_event_log(log)

    assert history["total_rows"] == 2
    assert history["unique_recurrence_count"] == 1
    assert build_recurrence_summary(history)[0]["status"] == "active"


def test_missing_event_log_loads_as_empty(tmp_path: Path) -> None:
    log = load_recurrence_event_log(tmp_path / "missing.json")

    assert log == empty_recurrence_event_log()


def test_malformed_event_log_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text('{"schema_version": 1}', encoding="utf-8")

    with pytest.raises(ValueError, match="events list"):
        load_recurrence_event_log(path)


def test_unsupported_event_log_schema_version_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "version.json"
    path.write_text('{"schema_version": 99, "events": []}', encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported event log schema_version"):
        load_recurrence_event_log(path)


def test_write_and_reload_event_log_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "event_log.json"
    updated = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row()],
        recorded_at="2026-06-10T00:00:00Z",
    )
    write_recurrence_event_log(path, updated)
    reloaded = load_recurrence_event_log(path)

    assert reloaded["events"] == updated["events"]
    assert json.loads(path.read_text(encoding="utf-8"))["events"][0]["event_index"] == 0


def test_append_recurrence_events_attaches_metadata_to_each_event() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a"), _classification_row(scenario_id="b")],
        event_metadata=normalize_recurrence_event_metadata(
            {
                "event_source": "protected_replay_failure",
                "recorded_at": "2026-06-12T00:00:00Z",
                "command": "pytest recurrence metadata",
                "run_id": "2026-06-12T00:00:00Z",
                "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
            }
        ),
    )

    for event in log["events"]:
        assert event["event_source"] == "protected_replay_failure"
        assert event["recorded_at"] == "2026-06-12T00:00:00Z"
        assert event["command"] == "pytest recurrence metadata"
        assert event["run_id"] == "2026-06-12T00:00:00Z"
        assert event["artifact_source"] == "artifacts/golden_replay/replay_failure_report.md"


def test_append_recurrence_event_metadata_does_not_alter_recurrence_key() -> None:
    row = _classification_row()
    without_metadata = append_recurrence_events(
        empty_recurrence_event_log(),
        [row],
        recorded_at="2026-06-10T00:00:00Z",
    )
    with_metadata = append_recurrence_events(
        empty_recurrence_event_log(),
        [row],
        event_metadata=normalize_recurrence_event_metadata(
            {
                "event_source": "protected_replay_failure",
                "test_node_id": "tests/test_golden_replay.py::test_foo",
                "command": "pytest metadata",
            }
        ),
    )

    assert without_metadata["events"][0]["recurrence_key"] == with_metadata["events"][0]["recurrence_key"]


def test_append_recurrence_event_metadata_does_not_change_aggregation_counts() -> None:
    rows = [_classification_row(scenario_id="a"), _classification_row(scenario_id="b")]
    plain_log = append_recurrence_events(empty_recurrence_event_log(), rows, recorded_at="2026-06-10T00:00:00Z")
    rich_log = append_recurrence_events(
        empty_recurrence_event_log(),
        rows,
        event_metadata=normalize_recurrence_event_metadata(
            {"event_source": "protected_replay_failure", "command": "pytest metadata"}
        ),
    )

    plain_history = aggregate_recurrence_history_from_event_log(plain_log)
    rich_history = aggregate_recurrence_history_from_event_log(rich_log)

    assert plain_history["total_rows"] == rich_history["total_rows"] == 2
    assert plain_history["unique_recurrence_count"] == rich_history["unique_recurrence_count"] == 1
    assert build_recurrence_summary(plain_history)[0]["status"] == "active"
    assert build_recurrence_summary(rich_history)[0]["status"] == "active"


def test_normalize_recurrence_event_metadata_omits_empty_values() -> None:
    metadata = normalize_recurrence_event_metadata(
        {"event_source": " ", "command": "pytest", "test_node_id": ""},
    )

    assert metadata == {"event_source": "session", "command": "pytest"}


def test_row_test_node_id_overrides_batch_metadata() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(test_node_id="tests/test_golden_replay.py::test_row_node")],
        event_metadata=normalize_recurrence_event_metadata(
            {"test_node_id": "tests/test_batch.py::test_batch_node"}
        ),
    )

    assert log["events"][0]["test_node_id"] == "tests/test_golden_replay.py::test_row_node"


def test_empty_history_regression_recurrence_rate_is_zero() -> None:
    metric = calculate_regression_recurrence_rate(aggregate_recurrence_history([]))

    assert metric["numerator"] == 0
    assert metric["denominator"] == 0
    assert metric["rate"] == 0.0
    assert metric["report_only"] is True
    assert metric["advisory_only"] is True


def test_single_watch_recurrence_rate_is_zero_over_one() -> None:
    history = aggregate_recurrence_history(recurrence_rows([_classification_row()]))

    metric = history["regression_recurrence_rate"]
    assert metric["numerator"] == 0
    assert metric["denominator"] == 1
    assert metric["rate"] == 0.0


def test_repeated_same_key_recurrence_rate_is_one_over_one() -> None:
    history = aggregate_recurrence_history(
        recurrence_rows(
            [
                _classification_row(scenario_id="a"),
                _classification_row(scenario_id="b"),
            ]
        )
    )

    metric = history["regression_recurrence_rate"]
    assert metric["numerator"] == 1
    assert metric["denominator"] == 1
    assert metric["rate"] == 1.0


def test_mixed_keys_regression_recurrence_rate() -> None:
    history = aggregate_recurrence_history(
        recurrence_rows(
            [
                _classification_row(scenario_id="a"),
                _classification_row(scenario_id="b"),
                _classification_row(
                    scenario_id="c",
                    field_path="route_kind",
                    investigate_first="game/interaction_context.py",
                ),
            ]
        )
    )

    metric = history["regression_recurrence_rate"]
    assert metric["numerator"] == 1
    assert metric["denominator"] == 2
    assert metric["rate"] == 0.5


def test_regression_recurrence_rate_from_event_log_matches_history() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [
            _classification_row(scenario_id="a"),
            _classification_row(scenario_id="b"),
            _classification_row(
                scenario_id="c",
                field_path="route_kind",
                investigate_first="game/interaction_context.py",
            ),
        ],
        recorded_at="2026-06-10T00:00:00Z",
    )
    history = aggregate_recurrence_history_from_event_log(log)

    assert calculate_regression_recurrence_rate(log) == history["regression_recurrence_rate"]


def test_calculate_regression_recurrence_rate_backward_compatible_without_filter() -> None:
    history = aggregate_recurrence_history(
        recurrence_rows([_classification_row(scenario_id="a"), _classification_row(scenario_id="b")])
    )

    metric = calculate_regression_recurrence_rate(history)

    assert "event_source_filter" not in metric
    assert metric == history["regression_recurrence_rate"]


def test_filtered_regression_recurrence_rate_protected_only() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a")],
        event_source="session",
        recorded_at="2026-06-10T00:00:00Z",
    )
    log = append_recurrence_events(
        log,
        [_classification_row(scenario_id="b"), _classification_row(scenario_id="c")],
        event_source=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
        recorded_at="2026-06-11T00:00:00Z",
    )

    metric = calculate_regression_recurrence_rate(
        log,
        event_source_filter=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    )

    assert metric["event_source_filter"] == PROTECTED_REPLAY_FAILURE_EVENT_SOURCE
    assert metric["numerator"] == 1
    assert metric["denominator"] == 1
    assert metric["rate"] == 1.0


def test_filtered_regression_recurrence_rate_session_only() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a")],
        event_source=DEFAULT_EVENT_SOURCE,
        recorded_at="2026-06-10T00:00:00Z",
    )
    log = append_recurrence_events(
        log,
        [_classification_row(scenario_id="b"), _classification_row(scenario_id="c")],
        event_source=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
        recorded_at="2026-06-11T00:00:00Z",
    )

    metric = calculate_regression_recurrence_rate(log, event_source_filter=DEFAULT_EVENT_SOURCE)

    assert metric["event_source_filter"] == DEFAULT_EVENT_SOURCE
    assert metric["numerator"] == 0
    assert metric["denominator"] == 1
    assert metric["rate"] == 0.0


def test_filtered_regression_recurrence_rate_empty_population() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a")],
        event_source=DEFAULT_EVENT_SOURCE,
        recorded_at="2026-06-10T00:00:00Z",
    )

    metric = calculate_regression_recurrence_rate(
        log,
        event_source_filter=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    )

    assert metric["numerator"] == 0
    assert metric["denominator"] == 0
    assert metric["rate"] == 0.0


def test_filtered_regression_recurrence_rate_on_history_without_events_is_empty() -> None:
    history = aggregate_recurrence_history(recurrence_rows([_classification_row()]))

    metric = calculate_regression_recurrence_rate(
        history,
        event_source_filter=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    )

    assert metric["numerator"] == 0
    assert metric["denominator"] == 0
    assert metric["rate"] == 0.0


def test_normalized_recurrence_event_source_buckets() -> None:
    assert normalized_recurrence_event_source(PROTECTED_REPLAY_FAILURE_EVENT_SOURCE) == PROTECTED_REPLAY_FAILURE_EVENT_SOURCE
    assert normalized_recurrence_event_source("session") == DEFAULT_EVENT_SOURCE
    assert normalized_recurrence_event_source(None) == DEFAULT_EVENT_SOURCE
    assert normalized_recurrence_event_source("manual_import") == "unknown"


def test_audit_recurrence_event_log_provenance_reports_source_buckets() -> None:
    log = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a"), _classification_row(scenario_id="b")],
        event_source=DEFAULT_EVENT_SOURCE,
        recorded_at="2026-06-10T00:00:00Z",
    )
    log = append_recurrence_events(
        log,
        [_classification_row(scenario_id="c")],
        event_source=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
        recorded_at="2026-06-11T00:00:00Z",
    )

    audit = audit_recurrence_event_log_provenance(log)

    assert audit["total_events"] == 3
    assert audit["event_source_distribution"][DEFAULT_EVENT_SOURCE] == 2
    assert audit["event_source_distribution"][PROTECTED_REPLAY_FAILURE_EVENT_SOURCE] == 1
    assert audit["regression_recurrence_rate_comparison"]["overall"]["numerator"] == 1
    assert (
        audit["regression_recurrence_rate_comparison"][DEFAULT_EVENT_SOURCE]["rate"]
        == 1.0
    )
    assert (
        audit["regression_recurrence_rate_comparison"][PROTECTED_REPLAY_FAILURE_EVENT_SOURCE]["rate"]
        == 0.0
    )


def _sample_recurrence_event(**overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
        "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
        "scenario_id": "vocative_override_after_prior_continuity",
        "recurrence_key": build_recurrence_key(_classification_row()),
    }
    event.update(overrides)
    return event


def test_is_commit_worthy_allows_golden_replay_protected_event() -> None:
    worthy, reason = is_commit_worthy_recurrence_event(_sample_recurrence_event())

    assert worthy is True
    assert reason == "protected_replay_failure"


def test_is_commit_worthy_rejects_session_event_source() -> None:
    worthy, reason = is_commit_worthy_recurrence_event(
        _sample_recurrence_event(event_source=DEFAULT_EVENT_SOURCE)
    )

    assert worthy is False
    assert reason == "session_event_source"


def test_is_commit_worthy_rejects_null_scenario_protected_event() -> None:
    worthy, reason = is_commit_worthy_recurrence_event(
        _sample_recurrence_event(scenario_id=None)
    )

    assert worthy is False
    assert reason == "null_scenario_id"


def test_is_commit_worthy_rejects_synthetic_drift_recurrence_key() -> None:
    worthy, reason = is_commit_worthy_recurrence_event(
        _sample_recurrence_event(
            recurrence_key="recurrence:v1:route_drift|unknown|route_kind|unknown"
        )
    )

    assert worthy is False
    assert reason == "synthetic_drift_recurrence_key"
    assert is_synthetic_drift_recurrence_key("recurrence:v1:route_drift|unknown|route_kind|unknown")


def test_is_commit_worthy_rejects_ephemeral_pytest_artifact_source() -> None:
    worthy, reason = is_commit_worthy_recurrence_event(
        _sample_recurrence_event(
            artifact_source="codex_pytest_tmp/test_protected_replay_failure_0/replay_failure_report.md"
        )
    )

    assert worthy is False
    assert reason.startswith("ephemeral_artifact_source:")


def test_is_commit_worthy_allows_backfill_persistence_intent() -> None:
    worthy, reason = is_commit_worthy_recurrence_event(
        _sample_recurrence_event(
            artifact_source="codex_pytest_tmp/test_backfill/replay_failure_report.md",
            persistence_intent=BACKFILL_PROTECTED_REPLAY_PERSISTENCE_INTENT,
        )
    )

    assert worthy is True
    assert reason == "backfilled_protected_replay_history"


def test_append_recurrence_events_to_persistence_lanes_routes_explicitly() -> None:
    lane_result = append_recurrence_events_to_persistence_lanes(
        empty_recurrence_event_log(),
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="session-only")],
        event_source=DEFAULT_EVENT_SOURCE,
        recorded_at="2026-06-10T00:00:00Z",
    )

    assert lane_result["protected_appended"] == 0
    assert lane_result["session_diagnostic_appended"] == 1
    assert lane_result["routing"][0]["reason"] == "session_event_source"


def test_calculate_protected_replay_regression_recurrence_rate_uses_commit_worthy_events_only() -> None:
    log = append_recurrence_events_to_persistence_lanes(
        empty_recurrence_event_log(),
        empty_recurrence_event_log(),
        [_classification_row(scenario_id="a"), _classification_row(scenario_id="b")],
        event_metadata=normalize_recurrence_event_metadata(
            {
                "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                "recorded_at": "2026-06-10T00:00:00Z",
            }
        ),
    )["protected_log"]

    metric = calculate_protected_replay_regression_recurrence_rate(log)

    assert metric["population"] == "protected_replay_history"
    assert metric["numerator"] == 1
    assert metric["denominator"] == 1
    assert metric["rate"] == 1.0


def _protected_event_log_with_recorded_at(*recorded_at_values: str) -> dict[str, object]:
    log = empty_recurrence_event_log()
    for recorded_at in recorded_at_values:
        log = append_recurrence_events(
            log,
            [_classification_row(scenario_id=f"scenario-{recorded_at}")],
            event_metadata=normalize_recurrence_event_metadata(
                {
                    "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                    "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                    "recorded_at": recorded_at,
                }
            ),
        )
    return log


def test_single_event_history_classifies_as_emerging() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    timeline = build_recurrence_timeline(log)

    assert len(timeline) == 1
    assert timeline[0]["trend_classification"] == RECURRENCE_TREND_CLASSIFICATION_EMERGING
    assert timeline[0]["occurrence_count"] == 1

    trends = build_recurrence_trend_summary(log)
    assert trends["total_keys"] == 1
    assert trends["emerging_keys"] == 1
    assert trends["recurring_keys"] == 0
    assert trends["persistent_keys"] == 0
    assert trends["dormant_keys"] == 0
    assert trends["growth_rate"] == 1.0


def test_repeated_recent_events_classify_as_recurring() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z")
    timeline = build_recurrence_timeline(log, as_of="2026-06-02T00:00:00Z")

    assert timeline[0]["trend_classification"] == RECURRENCE_TREND_CLASSIFICATION_RECURRING
    trends = build_recurrence_trend_summary(log, as_of="2026-06-02T00:00:00Z")
    assert trends["recurring_keys"] == 1
    assert trends["emerging_keys"] == 0


def test_extended_span_classifies_as_persistent() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-01T00:00:00Z", "2026-06-10T00:00:00Z")
    timeline = build_recurrence_timeline(log, as_of="2026-06-10T00:00:00Z")

    assert timeline[0]["trend_classification"] == RECURRENCE_TREND_CLASSIFICATION_PERSISTENT
    assert timeline[0]["active_duration_days"] >= 7.0


def test_historically_repeated_but_inactive_classifies_as_dormant() -> None:
    log = _protected_event_log_with_recorded_at("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
    timeline = build_recurrence_timeline(log, as_of="2026-03-15T00:00:00Z")

    assert timeline[0]["trend_classification"] == RECURRENCE_TREND_CLASSIFICATION_DORMANT
    trends = build_recurrence_trend_summary(log, as_of="2026-03-15T00:00:00Z")
    assert trends["dormant_keys"] == 1


def test_empty_history_trend_summary_is_zeroed() -> None:
    trends = build_recurrence_trend_summary(empty_recurrence_event_log())
    growth = summarize_recurrence_growth(build_recurrence_timeline(empty_recurrence_event_log()))

    assert trends["total_keys"] == 0
    assert trends["emerging_keys"] == 0
    assert trends["growth_rate"] == 0.0
    assert growth["total_keys"] == 0
    assert build_recurrence_timeline(empty_recurrence_event_log()) == []


def test_enrich_recurrence_history_with_trends_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = aggregate_protected_recurrence_history_from_event_log(log)
    enriched = enrich_recurrence_history_with_trends(history, log)

    assert enriched["unique_recurrence_count"] == history["unique_recurrence_count"]
    assert "recurrence_trends" in enriched
    assert "recurrence_timeline" in enriched
    assert enriched["recurrence_trends"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(enriched, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_timeline"][0]["first_seen"] == "2026-06-04T22:31:59Z"


def test_trend_summary_excludes_session_diagnostic_events() -> None:
    protected = _protected_event_log_with_recorded_at("2026-06-10T00:00:00Z", "2026-06-11T00:00:00Z")
    polluted = append_recurrence_events(
        protected,
        [_classification_row(scenario_id="session-noise")],
        event_source=DEFAULT_EVENT_SOURCE,
        recorded_at="2026-06-12T00:00:00Z",
    )

    trends = build_recurrence_trend_summary(polluted)

    assert trends["total_keys"] == 1
    assert trends["recurring_keys"] == 1
    assert classify_recurrence_trend_entry(
        occurrence_count=2,
        first_seen="2026-06-01T00:00:00Z",
        last_seen="2026-06-02T00:00:00Z",
        as_of="2026-06-02T00:00:00Z",
    ) == RECURRENCE_TREND_CLASSIFICATION_RECURRING


def test_empty_history_forecast_is_zeroed() -> None:
    forecast = build_recurrence_forecast(recurrence_timeline=[])

    summary = forecast["forecast_summary"]
    assert summary["stable_keys"] == 0
    assert summary["watch_keys"] == 0
    assert summary["forecast_risk_score"] == 0.0
    assert summary["stability_score"] == 100.0
    assert summary["forecast_confidence"] == 0.0
    assert forecast["risk_concentration"]["concentration_ratio"] == 0.0


def test_single_emerging_key_forecast_is_watch_with_high_stability() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    forecast = build_recurrence_forecast(event_log=log)
    summary = forecast["forecast_summary"]

    assert summary["watch_keys"] == 1
    assert summary["elevated_keys"] == 0
    assert summary["stability_score"] == 100.0
    assert summary["forecast_confidence"] == 0.2
    assert forecast["key_forecasts"][0]["forecast_classification"] == RECURRENCE_FORECAST_WATCH
    assert forecast["risk_concentration"]["top_key_share"] == 1.0


def test_recurring_key_forecast_is_elevated() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z")
    forecast = build_recurrence_forecast(event_log=log, recurrence_trends=None)

    assert forecast["forecast_summary"]["elevated_keys"] == 1
    assert forecast["key_forecasts"][0]["forecast_classification"] == RECURRENCE_FORECAST_ELEVATED


def test_concentrated_population_flags_dominant_key() -> None:
    log = empty_recurrence_event_log()
    for index, field_path in enumerate(("selected_speaker_id", "route_kind")):
        repeats = 3 if index == 0 else 1
        for offset in range(repeats):
            log = append_recurrence_events(
                log,
                [_classification_row(scenario_id=f"s-{field_path}-{offset}", field_path=field_path)],
                event_metadata=normalize_recurrence_event_metadata(
                    {
                        "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                        "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                        "recorded_at": f"2026-06-0{index + 1}T0{offset}:00:00Z",
                    }
                ),
            )
    forecast = build_recurrence_forecast(event_log=log)
    classifications = {
        row["recurrence_key"]: row["forecast_classification"] for row in forecast["key_forecasts"]
    }
    dominant = forecast["risk_concentration"]["dominant_recurrence_key"]

    assert forecast["risk_concentration"]["top_key_share"] >= 0.5
    assert classifications[dominant] == RECURRENCE_FORECAST_CONCENTRATED


def test_stability_score_extremes() -> None:
    empty_forecast = build_recurrence_forecast(recurrence_timeline=[])
    assert empty_forecast["forecast_summary"]["stability_score"] == 100.0

    fully_recurring = build_recurrence_forecast(
        recurrence_timeline=[
            {
                "recurrence_key": "recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py",
                "occurrence_count": 2,
                "trend_classification": RECURRENCE_TREND_CLASSIFICATION_RECURRING,
                "recurrence_velocity": 2.0,
            }
        ],
        regression_recurrence_rate={
            "numerator": 1,
            "denominator": 1,
            "rate": 1.0,
        },
    )
    assert fully_recurring["forecast_summary"]["stability_score"] == 0.0


def test_enrich_recurrence_history_with_forecasts_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_trends(
        aggregate_protected_recurrence_history_from_event_log(log),
        log,
    )
    enriched = enrich_recurrence_history_with_forecasts(history, event_log=log)

    assert enriched["unique_recurrence_count"] == 1
    assert "recurrence_forecast" in enriched
    assert enriched["recurrence_forecast"]["forecast_summary"]["watch_keys"] == 1

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(enriched, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_forecast"]["protected_replay_only"] is True


def test_summarize_recurrence_risk_concentration_metrics() -> None:
    timeline = [
        {"recurrence_key": "a", "occurrence_count": 3},
        {"recurrence_key": "b", "occurrence_count": 1},
    ]
    risk = summarize_recurrence_risk(timeline)

    assert risk["top_key_share"] == 0.75
    assert risk["top_three_key_share"] == 1.0
    assert risk["concentration_ratio"] == round(0.75**2 + 0.25**2, 4)
    assert risk["dominant_recurrence_key"] == "a"


def test_classify_recurrence_forecast_stable_for_dormant_trend() -> None:
    assert (
        classify_recurrence_forecast(
            {
                "trend_classification": RECURRENCE_TREND_CLASSIFICATION_DORMANT,
                "occurrence_count": 2,
            },
            observation_share=1.0,
            total_observations=2,
        )
        == RECURRENCE_FORECAST_STABLE
    )


def test_empty_portfolio_is_zeroed() -> None:
    portfolio = build_recurrence_portfolio(recurrence_timeline=[])

    assert portfolio["owner_count"] == 0
    assert portfolio["owners"] == []
    summary = portfolio["portfolio_summary"]
    assert summary["portfolio_risk_score"] == 0.0
    assert summary["owner_concentration_ratio"] == 0.0
    assert summary["largest_risk_bucket"] is None


def test_single_key_portfolio_attributes_all_dimensions() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    forecast = build_recurrence_forecast(event_log=log)
    portfolio = build_recurrence_portfolio(
        recurrence_timeline=build_recurrence_timeline(log),
        recurrence_forecast=forecast,
        event_log=log,
    )

    assert portfolio["owner_count"] == 1
    assert portfolio["owners"][0]["owner"] == "speaker"
    assert portfolio["categories"][0]["category"] == "speaker"
    assert portfolio["field_paths"][0]["field_path"] == "selected_speaker_id"
    assert portfolio["scenarios"][0]["scenario_id"] == "scenario-2026-06-04T22:31:59Z"
    assert portfolio["owners"][0]["risk_share"] == 1.0
    assert portfolio["owner_concentration_ratio"] == 1.0
    assert portfolio["portfolio_summary"]["largest_risk_bucket"]["dimension"] == "owner"


def test_multi_owner_portfolio_distribution() -> None:
    log = empty_recurrence_event_log()
    for field_path, owner, category in (
        ("selected_speaker_id", "projection", "projection"),
        ("route_kind", "routing", "routing"),
    ):
        log = append_recurrence_events(
            log,
            [
                _classification_row(
                    scenario_id=f"scenario-{field_path}",
                    field_path=field_path,
                    primary_owner=owner,
                    category=category,
                    owner_drift_bucket="speaker_drift" if field_path == "selected_speaker_id" else "route_drift",
                    investigate_first="tests/helpers/golden_replay.py",
                )
            ],
            event_metadata=normalize_recurrence_event_metadata(
                {
                    "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                    "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                    "recorded_at": "2026-06-10T00:00:00Z",
                }
            ),
        )
    portfolio = build_recurrence_portfolio(event_log=log)

    assert portfolio["owner_count"] == 2
    assert {row["owner"] for row in portfolio["owners"]} == {"projection", "routing"}
    assert portfolio["owner_concentration_ratio"] == 0.5


def test_concentrated_portfolio_has_high_owner_concentration() -> None:
    log = empty_recurrence_event_log()
    for offset in range(3):
        log = append_recurrence_events(
            log,
            [_classification_row(scenario_id=f"s-{offset}")],
            event_metadata=normalize_recurrence_event_metadata(
                {
                    "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                    "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                    "recorded_at": f"2026-06-0{(offset % 3) + 1}T00:00:00Z",
                }
            ),
        )
    for field_path in ("route_kind",):
        log = append_recurrence_events(
            log,
            [
                _classification_row(
                    scenario_id="other",
                    field_path=field_path,
                    owner_drift_bucket="route_drift",
                    category="routing",
                    primary_owner="routing",
                    investigate_first="game/interaction_context.py",
                )
            ],
            event_metadata=normalize_recurrence_event_metadata(
                {
                    "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                    "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                    "recorded_at": "2026-06-04T00:00:00Z",
                }
            ),
        )
    portfolio = build_recurrence_portfolio(event_log=log)

    assert portfolio["owner_concentration_ratio"] >= 0.5
    assert portfolio["highest_risk_owner"] == "speaker"


def test_distributed_portfolio_has_lower_concentration_than_concentrated() -> None:
    concentrated = build_recurrence_portfolio(
        event_log=_protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    )
    distributed_log = empty_recurrence_event_log()
    for field_path, owner, category, bucket in (
        ("selected_speaker_id", "projection", "projection", "speaker_drift"),
        ("route_kind", "routing", "routing", "route_drift"),
        ("fallback_family", "fallback", "fallback", "fallback_drift"),
    ):
        distributed_log = append_recurrence_events(
            distributed_log,
            [
                _classification_row(
                    scenario_id=f"scenario-{field_path}",
                    field_path=field_path,
                    primary_owner=owner,
                    category=category,
                    owner_drift_bucket=bucket,
                    investigate_first="tests/helpers/golden_replay.py",
                )
            ],
            event_metadata=normalize_recurrence_event_metadata(
                {
                    "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                    "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                    "recorded_at": "2026-06-10T00:00:00Z",
                }
            ),
        )
    distributed = build_recurrence_portfolio(event_log=distributed_log)

    assert distributed["owner_concentration_ratio"] < concentrated["owner_concentration_ratio"]


def test_summarize_recurrence_portfolio_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    forecast = build_recurrence_forecast(event_log=log)
    portfolio = build_recurrence_portfolio(
        recurrence_timeline=build_recurrence_timeline(log),
        recurrence_forecast=forecast,
        event_log=log,
    )
    summary = summarize_recurrence_portfolio(portfolio, recurrence_forecast=forecast)

    assert summary == portfolio["portfolio_summary"]


def test_enrich_recurrence_history_with_portfolio_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_forecasts(
        enrich_recurrence_history_with_trends(
            aggregate_protected_recurrence_history_from_event_log(log),
            log,
        ),
        event_log=log,
    )
    enriched = enrich_recurrence_history_with_portfolio(history, event_log=log)

    assert "recurrence_portfolio" in enriched
    assert "recurrence_portfolio_summary" in enriched
    assert enriched["recurrence_portfolio_summary"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(enriched, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_portfolio"]["owners"][0]["owner"] == "speaker"


def test_empty_remediation_targets_are_zeroed() -> None:
    targets = build_recurrence_remediation_targets(recurrence_portfolio={})

    assert targets["keys"] == []
    assert targets["remediation_summary"]["estimated_portfolio_reduction"] == 0.0
    assert targets["remediation_summary"]["remediation_confidence"] == 0.0
    assert targets["remediation_summary"]["highest_leverage_key"] is None


def test_single_key_remediation_target_is_ranked() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    targets = build_recurrence_remediation_targets(event_log=log)

    assert len(targets["keys"]) == 1
    key = targets["keys"][0]
    assert key["remediation_priority"] in {
        RECURRENCE_REMEDIATION_PRIORITY_HIGH,
        RECURRENCE_REMEDIATION_PRIORITY_MEDIUM,
        RECURRENCE_REMEDIATION_PRIORITY_CRITICAL,
    }
    assert targets["remediation_summary"]["highest_leverage_key"] == key["recurrence_key"]
    assert targets["owners"][0]["reduction_potential"] == key["reduction_potential"]
    assert targets["remediation_summary"]["remediation_confidence"] == 0.04


def test_calculate_recurrence_reduction_potential_is_bounded() -> None:
    score = calculate_recurrence_reduction_potential(
        risk_share=1.0,
        occurrence_count=2,
        total_observations=2,
        trend_classification=RECURRENCE_TREND_CLASSIFICATION_PERSISTENT,
        forecast_classification=RECURRENCE_FORECAST_ELEVATED,
        concentration_contribution=1.0,
    )

    assert 0.0 <= score <= 100.0
    assert score >= 75.0
    assert classify_remediation_priority(score) == RECURRENCE_REMEDIATION_PRIORITY_CRITICAL


def test_classify_remediation_priority_thresholds() -> None:
    assert classify_remediation_priority(80.0) == RECURRENCE_REMEDIATION_PRIORITY_CRITICAL
    assert classify_remediation_priority(55.0) == RECURRENCE_REMEDIATION_PRIORITY_HIGH
    assert classify_remediation_priority(30.0) == RECURRENCE_REMEDIATION_PRIORITY_MEDIUM
    assert classify_remediation_priority(10.0) == RECURRENCE_REMEDIATION_PRIORITY_LOW


def test_concentrated_portfolio_ranks_dominant_owner_highest() -> None:
    log = empty_recurrence_event_log()
    for offset in range(3):
        log = append_recurrence_events(
            log,
            [_classification_row(scenario_id=f"s-{offset}")],
            event_metadata=normalize_recurrence_event_metadata(
                {
                    "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                    "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                    "recorded_at": f"2026-06-0{(offset % 3) + 1}T00:00:00Z",
                }
            ),
        )
    log = append_recurrence_events(
        log,
        [
            _classification_row(
                scenario_id="other",
                field_path="route_kind",
                owner_drift_bucket="route_drift",
                category="routing",
                primary_owner="routing",
                investigate_first="game/interaction_context.py",
            )
        ],
        event_metadata=normalize_recurrence_event_metadata(
            {
                "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                "recorded_at": "2026-06-04T00:00:00Z",
            }
        ),
    )
    targets = build_recurrence_remediation_targets(event_log=log)

    assert targets["owners"][0]["owner"] == "speaker"
    assert targets["owners"][0]["reduction_potential"] >= targets["owners"][1]["reduction_potential"]


def test_distributed_portfolio_spreads_reduction_opportunity() -> None:
    concentrated = build_recurrence_remediation_targets(
        event_log=_protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    )
    distributed_log = empty_recurrence_event_log()
    for field_path, owner, category, bucket in (
        ("selected_speaker_id", "projection", "projection", "speaker_drift"),
        ("route_kind", "routing", "routing", "route_drift"),
        ("fallback_family", "fallback", "fallback", "fallback_drift"),
    ):
        distributed_log = append_recurrence_events(
            distributed_log,
            [
                _classification_row(
                    scenario_id=f"scenario-{field_path}",
                    field_path=field_path,
                    primary_owner=owner,
                    category=category,
                    owner_drift_bucket=bucket,
                    investigate_first="tests/helpers/golden_replay.py",
                )
            ],
            event_metadata=normalize_recurrence_event_metadata(
                {
                    "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
                    "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                    "recorded_at": "2026-06-10T00:00:00Z",
                }
            ),
        )
    distributed = build_recurrence_remediation_targets(event_log=distributed_log)

    assert len(distributed["keys"]) == 3
    assert distributed["keys"][0]["reduction_potential"] < concentrated["keys"][0]["reduction_potential"]


def test_summarize_recurrence_remediation_opportunities_matches_targets() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    portfolio = build_recurrence_portfolio(event_log=log)
    targets = build_recurrence_remediation_targets(
        recurrence_portfolio=portfolio,
        recurrence_forecast=build_recurrence_forecast(event_log=log),
        recurrence_timeline=build_recurrence_timeline(log),
        event_log=log,
    )
    summary = summarize_recurrence_remediation_opportunities(
        targets,
        recurrence_portfolio_summary=portfolio["portfolio_summary"],
    )

    assert summary == targets["remediation_summary"]


def test_enrich_recurrence_history_with_remediation_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_remediation(
        enrich_recurrence_history_with_portfolio(
            enrich_recurrence_history_with_forecasts(
                enrich_recurrence_history_with_trends(
                    aggregate_protected_recurrence_history_from_event_log(log),
                    log,
                ),
                event_log=log,
            ),
            event_log=log,
        ),
        event_log=log,
    )

    assert "recurrence_remediation_targets" in history
    assert "recurrence_remediation_summary" in history
    assert history["recurrence_remediation_summary"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(reloaded["recurrence_remediation_targets"]["keys"]) == 1


def test_empty_recurrence_roi_analysis_is_zeroed() -> None:
    analysis = build_recurrence_roi_analysis(recurrence_remediation_targets={})

    assert analysis["keys"] == []
    assert analysis["roi_summary"]["portfolio_roi_score"] == 0.0
    assert analysis["roi_summary"]["highest_roi_target"] is None
    assert analysis["roi_summary"]["roi_confidence"] == 0.0


def test_low_cost_high_benefit_target_scores_higher_roi() -> None:
    low_cost = calculate_recurrence_roi(
        reduction_potential=40.0,
        remediation_confidence=1.0,
        estimated_remediation_cost=10.0,
        portfolio_risk_score=60.0,
        stability_score=50.0,
    )
    high_cost = calculate_recurrence_roi(
        reduction_potential=40.0,
        remediation_confidence=1.0,
        estimated_remediation_cost=80.0,
        portfolio_risk_score=60.0,
        stability_score=50.0,
    )

    assert low_cost["roi_score"] > high_cost["roi_score"]
    assert low_cost["expected_benefit"] == 40.0
    assert classify_remediation_cost(10.0) == RECURRENCE_REMEDIATION_COST_TRIVIAL
    assert classify_remediation_cost(80.0) == RECURRENCE_REMEDIATION_COST_HIGH


def test_high_cost_low_benefit_target_scores_lower_roi() -> None:
    roi = calculate_recurrence_roi(
        reduction_potential=10.0,
        remediation_confidence=0.5,
        estimated_remediation_cost=90.0,
    )

    assert roi["roi_score"] < 10.0
    assert roi["expected_benefit"] == 5.0
    assert roi["cost_classification"] == RECURRENCE_REMEDIATION_COST_HIGH


def test_single_key_roi_analysis_is_ranked() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    analysis = build_recurrence_roi_analysis(event_log=log)

    assert len(analysis["keys"]) == 1
    key = analysis["keys"][0]
    assert key["roi_rank"] == 1
    assert 0.0 <= key["roi_score"] <= 100.0
    assert key["cost_classification"] in {
        RECURRENCE_REMEDIATION_COST_TRIVIAL,
        RECURRENCE_REMEDIATION_COST_LOW,
    }
    assert analysis["roi_summary"]["highest_roi_target"]["label"] == key["recurrence_key"]
    assert analysis["roi_summary"]["portfolio_roi_score"] == key["roi_score"]


def test_roi_ranking_orders_by_score_then_benefit() -> None:
    targets = {
        "total_observations": 4,
        "total_keys": 2,
        "keys": [
            {"recurrence_key": "low", "reduction_potential": 20.0, "observations": 1},
            {"recurrence_key": "high", "reduction_potential": 80.0, "observations": 3},
        ],
        "owners": [],
        "field_paths": [],
        "scenarios": [],
        "remediation_summary": {"remediation_confidence": 1.0},
    }
    portfolio = {
        "owner_concentration_ratio": 0.5,
        "field_path_concentration_ratio": 0.5,
        "total_keys": 2,
        "portfolio_summary": {
            "portfolio_risk_score": 50.0,
            "forecast_confidence": 1.0,
        },
    }
    forecast = {"forecast_summary": {"stability_score": 80.0}}

    analysis = build_recurrence_roi_analysis(
        recurrence_remediation_targets=targets,
        recurrence_portfolio=portfolio,
        recurrence_forecast=forecast,
    )

    assert analysis["keys"][0]["recurrence_key"] == "high"
    assert analysis["keys"][0]["roi_rank"] == 1
    assert analysis["keys"][1]["roi_rank"] == 2


def test_roi_confidence_blends_forecast_remediation_and_volume() -> None:
    summary = summarize_recurrence_roi(
        {"total_observations": 5, "keys": [], "owners": [], "field_paths": [], "scenarios": []},
        recurrence_portfolio_summary={"forecast_confidence": 1.0},
        recurrence_remediation_summary={"remediation_confidence": 1.0},
    )

    assert summary["roi_confidence"] == 1.0


def test_calculate_estimated_remediation_cost_is_bounded() -> None:
    concentrated = calculate_estimated_remediation_cost(
        owner_concentration_ratio=1.0,
        field_path_concentration_ratio=1.0,
        recurrence_keys=1,
        scenario_count=1,
        recurrence_count=1,
        total_keys=1,
    )
    distributed = calculate_estimated_remediation_cost(
        owner_concentration_ratio=0.2,
        field_path_concentration_ratio=0.2,
        recurrence_keys=5,
        scenario_count=5,
        recurrence_count=10,
        total_keys=5,
    )

    assert RECURRENCE_REMEDIATION_COST_FLOOR <= concentrated <= 100.0
    assert distributed > concentrated


def test_summarize_recurrence_roi_matches_analysis_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    analysis = build_recurrence_roi_analysis(event_log=log)
    summary = summarize_recurrence_roi(
        analysis,
        recurrence_forecast=build_recurrence_forecast(event_log=log),
        recurrence_portfolio_summary=build_recurrence_portfolio(event_log=log)["portfolio_summary"],
        recurrence_remediation_summary=build_recurrence_remediation_targets(event_log=log)["remediation_summary"],
    )

    assert summary == analysis["roi_summary"]


def test_enrich_recurrence_history_with_roi_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_roi(
        enrich_recurrence_history_with_remediation(
            enrich_recurrence_history_with_portfolio(
                enrich_recurrence_history_with_forecasts(
                    enrich_recurrence_history_with_trends(
                        aggregate_protected_recurrence_history_from_event_log(log),
                        log,
                    ),
                    event_log=log,
                ),
                event_log=log,
            ),
            event_log=log,
        ),
        event_log=log,
    )

    assert "recurrence_roi" in history
    assert "recurrence_roi_summary" in history
    assert history["recurrence_roi_summary"]["protected_replay_only"] is True
    assert history["recurrence_roi"]["keys"][0]["roi_score"] >= 0.0

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_roi_summary"]["portfolio_roi_score"] == history["recurrence_roi_summary"]["portfolio_roi_score"]


def test_empty_recurrence_governance_is_zeroed() -> None:
    governance = build_recurrence_governance()

    assert governance["watchlist"] == []
    assert governance["governance_summary"]["watchlist_size"] == 0
    assert governance["governance_summary"]["prioritized_targets"] == 0
    assert governance["governance_summary"]["governance_health_score"] == 100.0


def test_classify_recurrence_governance_status_watch() -> None:
    status = classify_recurrence_governance_status(
        trend_classification=RECURRENCE_TREND_CLASSIFICATION_EMERGING,
        forecast_classification=RECURRENCE_FORECAST_WATCH,
        reduction_potential=20.0,
        roi_score=10.0,
        roi_confidence=0.14,
    )

    assert status == RECURRENCE_GOVERNANCE_WATCH


def test_classify_recurrence_governance_status_investigate() -> None:
    status = classify_recurrence_governance_status(
        trend_classification=RECURRENCE_TREND_CLASSIFICATION_RECURRING,
        forecast_classification=RECURRENCE_FORECAST_ELEVATED,
        reduction_potential=55.0,
        roi_score=10.0,
        roi_confidence=0.14,
    )

    assert status == RECURRENCE_GOVERNANCE_INVESTIGATE


def test_classify_recurrence_governance_status_prioritize() -> None:
    status = classify_recurrence_governance_status(
        trend_classification=RECURRENCE_TREND_CLASSIFICATION_RECURRING,
        forecast_classification=RECURRENCE_FORECAST_ELEVATED,
        reduction_potential=80.0,
        roi_score=40.0,
        roi_confidence=0.20,
    )

    assert status == RECURRENCE_GOVERNANCE_PRIORITIZE


def test_classify_recurrence_governance_status_retire_candidate() -> None:
    status = classify_recurrence_governance_status(
        trend_classification=RECURRENCE_TREND_CLASSIFICATION_DORMANT,
        forecast_classification=RECURRENCE_FORECAST_STABLE,
        reduction_potential=10.0,
        roi_score=1.0,
        roi_confidence=0.10,
    )

    assert status == RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE


def test_single_key_governance_watchlist_entry() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    governance = build_recurrence_governance(event_log=log)

    assert len(governance["watchlist"]) == 1
    entry = governance["watchlist"][0]
    assert entry["governance_status"] == RECURRENCE_GOVERNANCE_WATCH
    assert entry["recommended_action"] == RECURRENCE_GOVERNANCE_ACTION_GATHER_HISTORY
    assert governance["governance_summary"]["watchlist_size"] == 1
    assert governance["governance_confidence"] < 0.25


def test_owner_accountability_summary() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    governance = build_recurrence_governance(event_log=log)

    assert governance["owners"][0]["watch_keys"] == 1
    assert governance["owners"][0]["governed_keys"] == 1
    assert governance["highest_governance_load_owner"] == governance["owners"][0]["owner"]


def test_governance_health_score_is_bounded() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    governance = build_recurrence_governance(event_log=log)

    score = governance["governance_summary"]["governance_health_score"]
    assert 0.0 <= score <= 100.0


def test_summarize_recurrence_governance_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    governance = build_recurrence_governance(event_log=log)
    summary = summarize_recurrence_governance(governance)

    assert summary == governance["governance_summary"]


def test_enrich_recurrence_history_with_governance_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_governance(
        enrich_recurrence_history_with_roi(
            enrich_recurrence_history_with_remediation(
                enrich_recurrence_history_with_portfolio(
                    enrich_recurrence_history_with_forecasts(
                        enrich_recurrence_history_with_trends(
                            aggregate_protected_recurrence_history_from_event_log(log),
                            log,
                        ),
                        event_log=log,
                    ),
                    event_log=log,
                ),
                event_log=log,
            ),
            event_log=log,
        ),
        event_log=log,
    )

    assert "recurrence_governance" in history
    assert "recurrence_watchlist" in history
    assert "recurrence_governance_summary" in history
    assert "recurrence_retirement_summary" in history
    assert history["recurrence_governance_summary"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(reloaded["recurrence_watchlist"]) == 1


def test_empty_recurrence_lifecycle_is_zeroed() -> None:
    lifecycle = build_recurrence_lifecycle()

    assert lifecycle["keys"] == []
    assert lifecycle["lifecycle_summary"]["closure_rate"] == 0.0
    assert lifecycle["transition_summary"]["transition_count"] == 0
    assert lifecycle["lifecycle_summary"]["lifecycle_health_score"] == 100.0


def test_classify_recurrence_lifecycle_stage_emerging() -> None:
    assert (
        classify_recurrence_lifecycle_stage(
            trend_classification=RECURRENCE_TREND_CLASSIFICATION_EMERGING,
        )
        == RECURRENCE_LIFECYCLE_EMERGING
    )


def test_classify_recurrence_lifecycle_stage_recurring() -> None:
    assert (
        classify_recurrence_lifecycle_stage(
            trend_classification=RECURRENCE_TREND_CLASSIFICATION_RECURRING,
        )
        == RECURRENCE_LIFECYCLE_RECURRING
    )


def test_classify_recurrence_lifecycle_stage_persistent() -> None:
    assert (
        classify_recurrence_lifecycle_stage(
            trend_classification=RECURRENCE_TREND_CLASSIFICATION_PERSISTENT,
        )
        == RECURRENCE_LIFECYCLE_PERSISTENT
    )


def test_classify_recurrence_lifecycle_stage_dormant() -> None:
    assert (
        classify_recurrence_lifecycle_stage(
            trend_classification=RECURRENCE_TREND_CLASSIFICATION_DORMANT,
            last_seen="2026-01-01T00:00:00Z",
            as_of="2026-03-01T00:00:00Z",
        )
        == RECURRENCE_LIFECYCLE_DORMANT
    )


def test_classify_recurrence_lifecycle_stage_retired() -> None:
    assert (
        classify_recurrence_lifecycle_stage(
            trend_classification=RECURRENCE_TREND_CLASSIFICATION_DORMANT,
            last_seen="2026-01-01T00:00:00Z",
            as_of="2026-06-01T00:00:00Z",
            retirement_inactivity_days=RECURRENCE_LIFECYCLE_RETIREMENT_INACTIVITY_DAYS,
        )
        == RECURRENCE_LIFECYCLE_RETIRED
    )
    assert (
        classify_recurrence_lifecycle_stage(
            trend_classification=RECURRENCE_TREND_CLASSIFICATION_EMERGING,
            recurrence_status="retired",
        )
        == RECURRENCE_LIFECYCLE_RETIRED
    )


def test_single_key_lifecycle_is_emerging() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    lifecycle = build_recurrence_lifecycle(event_log=log)

    assert len(lifecycle["keys"]) == 1
    key = lifecycle["keys"][0]
    assert key["lifecycle_stage"] == RECURRENCE_LIFECYCLE_EMERGING
    assert lifecycle["lifecycle_distribution"]["emerging"] == 1
    assert lifecycle["transition_summary"]["transition_count"] == 0
    assert lifecycle["closure_effectiveness"]["closure_rate"] == 0.0
    assert 0.0 < lifecycle["lifecycle_summary"]["lifecycle_health_score"] < 100.0


def test_recurring_key_lifecycle_tracks_advancing_transition() -> None:
    log = _protected_event_log_with_recorded_at(
        "2026-06-01T00:00:00Z",
        "2026-06-02T00:00:00Z",
    )
    lifecycle = build_recurrence_lifecycle(event_log=log)

    assert lifecycle["keys"][0]["lifecycle_stage"] == RECURRENCE_LIFECYCLE_RECURRING
    assert lifecycle["transition_summary"]["advancing_transitions"] == 1
    assert "emerging->recurring" in lifecycle["transition_summary"]["transitions"]


def test_persistent_key_lifecycle_age_and_velocity() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-01T00:00:00Z", "2026-06-10T00:00:00Z")
    lifecycle = build_recurrence_lifecycle(
        event_log=log,
        as_of="2026-06-10T00:00:00Z",
    )

    key = lifecycle["keys"][0]
    assert key["lifecycle_stage"] == RECURRENCE_LIFECYCLE_PERSISTENT
    assert key["active_duration_days"] >= 7.0
    assert key["recurrence_age_days"] >= 7.0
    assert key["lifecycle_velocity"] > 0.0
    assert lifecycle["age_distribution"]["average_age_days"] >= 7.0


def test_dormant_key_lifecycle_counts_closure() -> None:
    log = _protected_event_log_with_recorded_at("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
    lifecycle = build_recurrence_lifecycle(
        event_log=log,
        as_of="2026-03-15T00:00:00Z",
    )

    assert lifecycle["keys"][0]["lifecycle_stage"] == RECURRENCE_LIFECYCLE_DORMANT
    assert lifecycle["closure_effectiveness"]["dormant_keys"] == 1
    assert lifecycle["closure_effectiveness"]["closure_rate"] == 1.0


def test_summarize_recurrence_lifecycle_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    lifecycle = build_recurrence_lifecycle(event_log=log)
    summary = summarize_recurrence_lifecycle(lifecycle)

    assert summary == lifecycle["lifecycle_summary"]


def test_enrich_recurrence_history_with_lifecycle_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_lifecycle(
        enrich_recurrence_history_with_governance(
            enrich_recurrence_history_with_roi(
                enrich_recurrence_history_with_remediation(
                    enrich_recurrence_history_with_portfolio(
                        enrich_recurrence_history_with_forecasts(
                            enrich_recurrence_history_with_trends(
                                aggregate_protected_recurrence_history_from_event_log(log),
                                log,
                            ),
                            event_log=log,
                        ),
                        event_log=log,
                    ),
                    event_log=log,
                ),
                event_log=log,
            ),
            event_log=log,
        ),
        event_log=log,
    )

    assert "recurrence_lifecycle" in history
    assert "recurrence_lifecycle_summary" in history
    assert "recurrence_age_distribution" in history
    assert "recurrence_transition_summary" in history
    assert "recurrence_closure_effectiveness" in history
    assert history["recurrence_lifecycle_summary"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_lifecycle"]["keys"][0]["lifecycle_stage"] == "emerging"


def _program_effectiveness_inputs_from_log(log: dict[str, object]) -> dict[str, object]:
    history = aggregate_protected_recurrence_history_from_event_log(log)
    timeline = build_recurrence_timeline(log)
    trends = build_recurrence_trend_summary(log)
    forecast = build_recurrence_forecast(
        recurrence_timeline=timeline,
        recurrence_trends=trends,
        regression_recurrence_rate=history.get("regression_recurrence_rate"),
    )
    portfolio = build_recurrence_portfolio(
        recurrence_timeline=timeline,
        recurrence_trends=trends,
        recurrence_forecast=forecast,
        event_log=log,
    )
    remediation_targets = build_recurrence_remediation_targets(
        recurrence_portfolio=portfolio,
        recurrence_forecast=forecast,
        recurrence_trends=trends,
        recurrence_history=history,
        recurrence_timeline=timeline,
        event_log=log,
    )
    roi = build_recurrence_roi_analysis(
        recurrence_remediation_targets=remediation_targets,
        recurrence_forecast=forecast,
        recurrence_portfolio=portfolio,
        recurrence_history=history,
    )
    governance = build_recurrence_governance(
        recurrence_trends=trends,
        recurrence_forecast=forecast,
        recurrence_portfolio=portfolio,
        recurrence_remediation_targets=remediation_targets,
        recurrence_roi=roi,
        recurrence_history=history,
        recurrence_timeline=timeline,
    )
    lifecycle = build_recurrence_lifecycle(
        recurrence_timeline=timeline,
        recurrence_trends=trends,
        recurrence_forecast=forecast,
        recurrence_governance=governance,
        recurrence_history=history,
    )
    return {
        "recurrence_governance": governance,
        "recurrence_remediation_summary": remediation_targets["remediation_summary"],
        "recurrence_roi_summary": roi["roi_summary"],
        "recurrence_lifecycle_summary": lifecycle["lifecycle_summary"],
        "recurrence_portfolio_summary": portfolio["portfolio_summary"],
        "recurrence_forecast": forecast,
        "recurrence_history": history,
        "recurrence_lifecycle": lifecycle,
        "recurrence_remediation_targets": remediation_targets,
    }


def test_empty_program_effectiveness_is_zeroed() -> None:
    effectiveness = build_recurrence_program_effectiveness()

    assert effectiveness["program_effectiveness_summary"]["program_effectiveness_score"] == 0.0
    assert effectiveness["portfolio_trajectory_summary"]["trajectory_available"] is False
    assert effectiveness["forecast_effectiveness_summary"]["low_confidence"] is True


def test_baseline_only_program_effectiveness() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    effectiveness = build_recurrence_program_effectiveness(**_program_effectiveness_inputs_from_log(log))

    assert effectiveness["portfolio_trajectory_summary"]["baseline_only"] is True
    assert effectiveness["stability_trajectory_summary"]["stability_change"] == 0.0
    assert effectiveness["program_effectiveness_summary"]["effectiveness_confidence"] < 0.25
    assert effectiveness["remediation_effectiveness_summary"]["recurrence_reduction_rate"] == 0.0


def test_forecast_accuracy_for_aligned_emerging_watch() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    inputs = _program_effectiveness_inputs_from_log(log)
    metrics = calculate_recurrence_effectiveness_metrics(**inputs)

    assert metrics["forecast_accuracy"] == 1.0
    assert metrics["realized_recurrences"] == 1
    assert metrics["predicted_recurrences"] == 1


def test_forecast_accuracy_for_misaligned_forecast() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    inputs = _program_effectiveness_inputs_from_log(log)
    forecast = dict(inputs["recurrence_forecast"])
    key_forecasts = [dict(row) for row in forecast["key_forecasts"]]
    key_forecasts[0]["forecast_classification"] = RECURRENCE_FORECAST_ELEVATED
    forecast["key_forecasts"] = key_forecasts
    metrics = calculate_recurrence_effectiveness_metrics(
        **{**inputs, "recurrence_forecast": forecast},
    )

    assert metrics["forecast_accuracy"] == 0.0
    assert metrics["realized_recurrences"] == 0


def test_remediation_effectiveness_with_resolved_lifecycle_key() -> None:
    log = _protected_event_log_with_recorded_at("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
    inputs = _program_effectiveness_inputs_from_log(log)
    lifecycle = build_recurrence_lifecycle(
        event_log=log,
        as_of="2026-03-15T00:00:00Z",
    )
    metrics = calculate_recurrence_effectiveness_metrics(
        **{**inputs, "recurrence_lifecycle": lifecycle, "recurrence_lifecycle_summary": lifecycle["lifecycle_summary"]},
    )

    assert lifecycle["keys"][0]["lifecycle_stage"] == RECURRENCE_LIFECYCLE_DORMANT
    assert metrics["improved_keys"] == 1
    assert metrics["recurrence_reduction_rate"] == 1.0


def test_trajectory_unavailable_without_prior_snapshot() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    effectiveness = build_recurrence_program_effectiveness(**_program_effectiveness_inputs_from_log(log))

    assert effectiveness["portfolio_trajectory_summary"]["trajectory_available"] is False
    assert effectiveness["portfolio_trajectory_summary"]["portfolio_risk_change"] == 0.0


def test_trajectory_available_with_prior_snapshot() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    inputs = _program_effectiveness_inputs_from_log(log)
    prior = build_recurrence_program_effectiveness(**inputs)
    prior["portfolio_trajectory_summary"]["portfolio_risk_current"] = 40.0
    prior["stability_trajectory_summary"]["stability_score_current"] = 90.0
    metrics = calculate_recurrence_effectiveness_metrics(
        **inputs,
        prior_program_effectiveness=prior,
    )

    assert metrics["trajectory_available"] is True
    assert metrics["portfolio_risk_change"] != 0.0
    assert metrics["stability_change"] != 0.0


def test_program_effectiveness_score_is_bounded() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    effectiveness = build_recurrence_program_effectiveness(**_program_effectiveness_inputs_from_log(log))
    score = effectiveness["program_effectiveness_summary"]["program_effectiveness_score"]

    assert 0.0 <= score <= 100.0


def test_summarize_recurrence_program_effectiveness_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    effectiveness = build_recurrence_program_effectiveness(**_program_effectiveness_inputs_from_log(log))
    summary = summarize_recurrence_program_effectiveness(effectiveness)

    assert summary == effectiveness["program_effectiveness_summary"]


def test_enrich_recurrence_history_with_program_effectiveness_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_program_effectiveness(
        enrich_recurrence_history_with_lifecycle(
            enrich_recurrence_history_with_governance(
                enrich_recurrence_history_with_roi(
                    enrich_recurrence_history_with_remediation(
                        enrich_recurrence_history_with_portfolio(
                            enrich_recurrence_history_with_forecasts(
                                enrich_recurrence_history_with_trends(
                                    aggregate_protected_recurrence_history_from_event_log(log),
                                    log,
                                ),
                                event_log=log,
                            ),
                            event_log=log,
                        ),
                        event_log=log,
                    ),
                    event_log=log,
                ),
                event_log=log,
            ),
            event_log=log,
        ),
    )

    assert "recurrence_program_effectiveness" in history
    assert "recurrence_program_effectiveness_summary" in history
    assert "governance_effectiveness_summary" in history
    assert "forecast_effectiveness_summary" in history
    assert history["recurrence_program_effectiveness_summary"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["forecast_effectiveness_summary"]["low_confidence"] is True


def _maturity_inputs_from_log(log: dict[str, object]) -> dict[str, object]:
    inputs = _program_effectiveness_inputs_from_log(log)
    timeline = build_recurrence_timeline(log)
    history = dict(inputs["recurrence_history"])
    history["recurrence_timeline"] = timeline
    trends = build_recurrence_trend_summary(log)
    portfolio = build_recurrence_portfolio(
        recurrence_timeline=timeline,
        recurrence_trends=trends,
        recurrence_forecast=inputs["recurrence_forecast"],
        event_log=log,
    )
    roi = build_recurrence_roi_analysis(
        recurrence_remediation_targets=inputs["recurrence_remediation_targets"],
        recurrence_forecast=inputs["recurrence_forecast"],
        recurrence_portfolio=portfolio,
        recurrence_history=history,
    )
    return {
        "recurrence_history": history,
        "recurrence_trends": trends,
        "recurrence_forecast": inputs["recurrence_forecast"],
        "recurrence_portfolio": portfolio,
        "recurrence_remediation": inputs["recurrence_remediation_targets"],
        "recurrence_roi": roi,
        "recurrence_governance": inputs["recurrence_governance"],
        "recurrence_lifecycle": inputs["recurrence_lifecycle"],
        "recurrence_program_effectiveness": build_recurrence_program_effectiveness(**inputs),
    }


def test_empty_maturity_assessment_is_zeroed() -> None:
    maturity = build_recurrence_maturity_assessment()

    summary = maturity["recurrence_maturity_summary"]
    assert summary["overall_maturity_score"] == 0.0
    assert summary["overall_maturity_level"] == RECURRENCE_MATURITY_LEVEL_INITIAL
    assert summary["observability_score"] == 0.0
    assert maturity["maturity_gap_analysis"][0]["improvement_priority"] == "critical"


def test_maturity_dimension_scoring_with_protected_history() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    scores = calculate_recurrence_maturity_score(**_maturity_inputs_from_log(log))

    assert scores["observability_maturity"]["maturity_score"] >= 60.0
    assert scores["governance_maturity"]["maturity_score"] >= 40.0
    assert scores["forecasting_maturity"]["maturity_score"] >= 20.0
    assert scores["operational_readiness"]["maturity_score"] < 40.0


def test_maturity_level_assignment() -> None:
    maturity = build_recurrence_maturity_assessment()

    for dimension in (
        "observability_maturity",
        "governance_maturity",
        "forecasting_maturity",
        "remediation_maturity",
        "lifecycle_maturity",
        "operational_readiness",
    ):
        row = maturity[dimension]
        score = float(row["maturity_score"])
        level = str(row["maturity_level"])
        if score <= 19:
            assert level == RECURRENCE_MATURITY_LEVEL_INITIAL
        elif score <= 39:
            assert level == RECURRENCE_MATURITY_LEVEL_DEVELOPING
        elif score <= 59:
            assert level == RECURRENCE_MATURITY_LEVEL_MANAGED
        elif score <= 79:
            assert level == RECURRENCE_MATURITY_LEVEL_MEASURED
        else:
            assert level == RECURRENCE_MATURITY_LEVEL_OPTIMIZED


def test_weighted_overall_maturity_score() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    scores = calculate_recurrence_maturity_score(**_maturity_inputs_from_log(log))
    expected = round(
        sum(
            float(scores["dimension_scores"][name]) * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        1,
    )

    assert scores["overall_maturity_score"] == expected
    assert 0.0 <= scores["overall_maturity_score"] <= 100.0


def test_maturity_gap_analysis() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    maturity = build_recurrence_maturity_assessment(**_maturity_inputs_from_log(log))

    gaps = maturity["maturity_gap_analysis"]
    assert len(gaps) == 6
    for row in gaps:
        assert row["target_score"] == RECURRENCE_MATURITY_TARGET_SCORE
        assert row["gap"] == round(max(0.0, RECURRENCE_MATURITY_TARGET_SCORE - float(row["current_score"])), 1)


def test_maturity_gap_priority_assignment() -> None:
    maturity = build_recurrence_maturity_assessment()
    priorities = {row["dimension"]: row["improvement_priority"] for row in maturity["maturity_gap_analysis"]}

    assert priorities["operational_readiness"] == "critical"
    assert priorities["observability"] in {"high", "medium", "low", "critical"}


def test_summarize_recurrence_maturity_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    maturity = build_recurrence_maturity_assessment(**_maturity_inputs_from_log(log))
    summary = summarize_recurrence_maturity(maturity)

    assert summary == maturity["recurrence_maturity_summary"]
    assert summary["highest_dimension"] in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
    assert summary["lowest_dimension"] in RECURRENCE_MATURITY_DIMENSION_WEIGHTS


def test_enrich_recurrence_history_with_maturity_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_maturity(
        enrich_recurrence_history_with_program_effectiveness(
            enrich_recurrence_history_with_lifecycle(
                enrich_recurrence_history_with_governance(
                    enrich_recurrence_history_with_roi(
                        enrich_recurrence_history_with_remediation(
                            enrich_recurrence_history_with_portfolio(
                                enrich_recurrence_history_with_forecasts(
                                    enrich_recurrence_history_with_trends(
                                        aggregate_protected_recurrence_history_from_event_log(log),
                                        log,
                                    ),
                                    event_log=log,
                                ),
                                event_log=log,
                            ),
                            event_log=log,
                        ),
                        event_log=log,
                    ),
                    event_log=log,
                ),
                event_log=log,
            ),
        ),
    )

    assert "recurrence_maturity" in history
    assert "recurrence_maturity_summary" in history
    assert "recurrence_maturity_gap_analysis" in history
    assert history["recurrence_maturity_summary"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_maturity_gap_analysis"][0]["dimension"] == "operational_readiness"


def _roadmap_inputs_from_log(log: dict[str, object]) -> dict[str, object]:
    maturity_inputs = _maturity_inputs_from_log(log)
    maturity = build_recurrence_maturity_assessment(**maturity_inputs)
    program = maturity_inputs["recurrence_program_effectiveness"]
    portfolio = maturity_inputs["recurrence_portfolio"]
    forecast = maturity_inputs["recurrence_forecast"]
    lifecycle = maturity_inputs["recurrence_lifecycle"]
    return {
        "recurrence_maturity_summary": maturity["recurrence_maturity_summary"],
        "recurrence_maturity_gap_analysis": maturity["maturity_gap_analysis"],
        "recurrence_program_effectiveness_summary": program["program_effectiveness_summary"],
        "recurrence_portfolio_summary": portfolio["portfolio_summary"],
        "recurrence_forecast_summary": forecast["forecast_summary"],
        "recurrence_lifecycle_summary": lifecycle["lifecycle_summary"],
        "recurrence_remediation_effectiveness_summary": program["remediation_effectiveness_summary"],
        "portfolio_trajectory_summary": program["portfolio_trajectory_summary"],
        "total_observations": int(maturity_inputs["recurrence_history"].get("total_rows") or 0),
        "total_keys": int(maturity_inputs["recurrence_history"].get("unique_recurrence_count") or 0),
    }


def test_empty_roadmap_defaults_to_data_volume_priority() -> None:
    roadmap = build_recurrence_strategic_roadmap()

    summary = roadmap["recurrence_roadmap_summary"]
    assert summary["highest_roi_initiative"] == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME
    assert summary["highest_gap_dimension"] == "operational_readiness"
    assert summary["target_state_defined"] is True
    assert summary["estimated_initiatives_remaining"] == 6


def test_roadmap_initiative_scoring_with_protected_history() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    roadmap = build_recurrence_strategic_roadmap(**_roadmap_inputs_from_log(log))

    initiatives = {row["initiative_id"]: row for row in roadmap["initiatives"]}
    data_volume = initiatives[RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME]
    assert data_volume["initiative_score"] > 0.0
    assert data_volume["maturity_impact"] > 0.0
    assert data_volume["implementation_complexity"] >= 12.0
    assert data_volume["dependency_count"] == 0
    assert "projected_maturity_after_completion" in data_volume


def test_maturity_roi_calculation_ranks_data_volume_highest() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    roadmap = build_recurrence_strategic_roadmap(**_roadmap_inputs_from_log(log))

    initiatives = sorted(roadmap["initiatives"], key=lambda row: -float(row["maturity_roi"]))
    assert initiatives[0]["initiative_id"] == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME
    assert 0.0 <= float(initiatives[0]["maturity_roi"]) <= 100.0


def test_roadmap_dependency_sequence_follows_default_order() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    roadmap = build_recurrence_strategic_roadmap(**_roadmap_inputs_from_log(log))

    sequence_ids = [row["initiative_id"] for row in roadmap["roadmap_sequence"]]
    assert sequence_ids[0] == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME
    assert sequence_ids.index(RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY) > sequence_ids.index(
        RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME
    )
    assert all(row["sequence_step"] == index for index, row in enumerate(roadmap["roadmap_sequence"], start=1))


def test_projected_maturity_lift_increases_overall_score() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    roadmap = build_recurrence_strategic_roadmap(**_roadmap_inputs_from_log(log))

    current = float(roadmap["current_maturity_score"])
    data_volume = next(
        row for row in roadmap["initiatives"] if row["initiative_id"] == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME
    )
    projected = float(data_volume["projected_maturity_after_completion"]["overall_maturity_score"])
    assert projected > current


def test_target_state_validation() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    roadmap = build_recurrence_strategic_roadmap(**_roadmap_inputs_from_log(log))
    target = roadmap["recurrence_target_state"]

    assert target["target_maturity_level"] == RECURRENCE_MATURITY_LEVEL_OPTIMIZED
    assert target["forecast_confidence_target"] == 0.75
    assert target["completion_criteria_met"] is False
    assert target["completion_criteria"]["trajectory_available"] is False


def test_calculate_maturity_investment_priority() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    inputs = _roadmap_inputs_from_log(log)
    roadmap = build_recurrence_strategic_roadmap(**inputs)
    data_volume = next(
        row for row in roadmap["initiatives"] if row["initiative_id"] == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME
    )
    priority = calculate_maturity_investment_priority(
        initiative_id=RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
        recurrence_maturity_summary=inputs["recurrence_maturity_summary"],
        recurrence_maturity_gap_analysis=inputs["recurrence_maturity_gap_analysis"],
        recurrence_program_effectiveness_summary=inputs["recurrence_program_effectiveness_summary"],
        recurrence_portfolio_summary=inputs["recurrence_portfolio_summary"],
        recurrence_forecast_summary=inputs["recurrence_forecast_summary"],
        recurrence_lifecycle_summary=inputs["recurrence_lifecycle_summary"],
        maturity_roi=data_volume["maturity_roi"],
        dependency_count=data_volume["dependency_count"],
    )

    assert 0.0 <= priority["investment_priority_score"] <= 100.0
    assert priority["initiative_id"] == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME


def test_summarize_recurrence_roadmap_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    roadmap = build_recurrence_strategic_roadmap(**_roadmap_inputs_from_log(log))
    summary = summarize_recurrence_roadmap(roadmap)

    assert summary["highest_roi_initiative"] == roadmap["recurrence_roadmap_summary"]["highest_roi_initiative"]
    assert summary["estimated_initiatives_remaining"] == roadmap["recurrence_roadmap_summary"][
        "estimated_initiatives_remaining"
    ]


def test_enrich_recurrence_history_with_roadmap_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_roadmap(
        enrich_recurrence_history_with_maturity(
            enrich_recurrence_history_with_program_effectiveness(
                enrich_recurrence_history_with_lifecycle(
                    enrich_recurrence_history_with_governance(
                        enrich_recurrence_history_with_roi(
                            enrich_recurrence_history_with_remediation(
                                enrich_recurrence_history_with_portfolio(
                                    enrich_recurrence_history_with_forecasts(
                                        enrich_recurrence_history_with_trends(
                                            aggregate_protected_recurrence_history_from_event_log(log),
                                            log,
                                        ),
                                        event_log=log,
                                    ),
                                    event_log=log,
                                ),
                                event_log=log,
                            ),
                            event_log=log,
                        ),
                        event_log=log,
                    ),
                    event_log=log,
                ),
            ),
        ),
    )

    assert "recurrence_roadmap" in history
    assert "recurrence_roadmap_summary" in history
    assert "recurrence_target_state" in history
    assert history["recurrence_roadmap_summary"]["protected_replay_only"] is True
    assert (
        history["recurrence_roadmap_summary"]["roadmap_priority_guidance"]
        == "Collect more protected replay observations before optimizing models."
    )

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_target_state"]["completion_criteria_met"] is False


def _completion_inputs_from_log(log: dict[str, object]) -> dict[str, object]:
    maturity_inputs = _maturity_inputs_from_log(log)
    roadmap_inputs = _roadmap_inputs_from_log(log)
    maturity = build_recurrence_maturity_assessment(**maturity_inputs)
    roadmap = build_recurrence_strategic_roadmap(**roadmap_inputs)
    program = maturity_inputs["recurrence_program_effectiveness"]
    history = dict(maturity_inputs["recurrence_history"])
    history["recurrence_timeline"] = build_recurrence_timeline(log)
    history.update(
        {
            "recurrence_trends": build_recurrence_trend_summary(log),
            "recurrence_forecast": maturity_inputs["recurrence_forecast"],
            "recurrence_portfolio": maturity_inputs["recurrence_portfolio"],
            "recurrence_governance": maturity_inputs["recurrence_governance"],
            "recurrence_governance_summary": maturity_inputs["recurrence_governance"]["governance_summary"],
            "recurrence_lifecycle": maturity_inputs["recurrence_lifecycle"],
            "recurrence_lifecycle_summary": maturity_inputs["recurrence_lifecycle"]["lifecycle_summary"],
            "recurrence_remediation_targets": maturity_inputs["recurrence_remediation"],
            "recurrence_roi_summary": build_recurrence_roi_analysis(
                recurrence_remediation_targets=maturity_inputs["recurrence_remediation"],
                recurrence_forecast=maturity_inputs["recurrence_forecast"],
                recurrence_portfolio=maturity_inputs["recurrence_portfolio"],
                recurrence_history=history,
            )["roi_summary"],
        }
    )
    return {
        "recurrence_maturity_summary": maturity["recurrence_maturity_summary"],
        "recurrence_program_effectiveness_summary": program["program_effectiveness_summary"],
        "recurrence_target_state": roadmap["recurrence_target_state"],
        "recurrence_roadmap_summary": roadmap["recurrence_roadmap_summary"],
        "recurrence_history": history,
        "recurrence_governance_summary": history["recurrence_governance_summary"],
        "recurrence_forecast_summary": maturity_inputs["recurrence_forecast"]["forecast_summary"],
        "forecast_effectiveness_summary": program["forecast_effectiveness_summary"],
        "remediation_effectiveness_summary": program["remediation_effectiveness_summary"],
        "recurrence_lifecycle_summary": maturity_inputs["recurrence_lifecycle"]["lifecycle_summary"],
        "recurrence_roi_summary": history["recurrence_roi_summary"],
        "portfolio_trajectory_summary": program["portfolio_trajectory_summary"],
    }


def _fully_enriched_history(log: dict[str, object]) -> dict[str, object]:
    return enrich_recurrence_history_with_completion(
        enrich_recurrence_history_with_roadmap(
            enrich_recurrence_history_with_maturity(
                enrich_recurrence_history_with_program_effectiveness(
                    enrich_recurrence_history_with_lifecycle(
                        enrich_recurrence_history_with_governance(
                            enrich_recurrence_history_with_roi(
                                enrich_recurrence_history_with_remediation(
                                    enrich_recurrence_history_with_portfolio(
                                        enrich_recurrence_history_with_forecasts(
                                            enrich_recurrence_history_with_trends(
                                                aggregate_protected_recurrence_history_from_event_log(log),
                                                log,
                                            ),
                                            event_log=log,
                                        ),
                                        event_log=log,
                                    ),
                                    event_log=log,
                                ),
                                event_log=log,
                            ),
                            event_log=log,
                        ),
                        event_log=log,
                    ),
                ),
            ),
        ),
    )


def test_empty_completion_assessment_is_not_graduated() -> None:
    completion = build_recurrence_completion_assessment()

    summary = completion["recurrence_completion_summary"]
    assert summary["program_graduated"] is False
    assert summary["overall_completion_score"] == 0.0
    assert summary["completed_dimensions"] == []
    assert len(summary["remaining_dimensions"]) == 6


def test_incomplete_program_with_protected_history() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    completion = build_recurrence_completion_assessment(**_completion_inputs_from_log(log))

    summary = completion["recurrence_completion_summary"]
    assert summary["program_graduated"] is False
    assert completion["observability_completion"]["completion_met"] is True
    assert completion["governance_completion"]["completion_met"] is False
    assert completion["forecasting_completion"]["completion_met"] is False
    assert completion["operational_readiness_completion"]["completion_met"] is False


def test_dimension_completion_scores() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    completion = build_recurrence_completion_assessment(**_completion_inputs_from_log(log))
    scores = calculate_recurrence_completion_score(
        observability_completion=completion["observability_completion"],
        governance_completion=completion["governance_completion"],
        forecasting_completion=completion["forecasting_completion"],
        remediation_completion=completion["remediation_completion"],
        lifecycle_completion=completion["lifecycle_completion"],
        operational_readiness_completion=completion["operational_readiness_completion"],
    )

    assert scores["overall_completion_score"] > 0.0
    assert "observability" in scores["completed_dimensions"] or scores["dimension_scores"]["observability"] == 100.0
    assert 0.0 <= scores["overall_completion_score"] <= 100.0


def test_graduation_criteria_requires_all_dimensions_and_thresholds() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    inputs = _completion_inputs_from_log(log)
    completion = build_recurrence_completion_assessment(**inputs)
    assert completion["program_graduated"] is False

    complete_completion = build_recurrence_completion_assessment(
        recurrence_maturity_summary={
            **inputs["recurrence_maturity_summary"],
            "overall_maturity_score": 85.0,
            "operational_readiness_score": 85.0,
            "observability_score": 85.0,
            "governance_score": 85.0,
            "forecasting_score": 85.0,
            "remediation_score": 85.0,
            "lifecycle_score": 85.0,
        },
        recurrence_program_effectiveness_summary={
            **inputs["recurrence_program_effectiveness_summary"],
            "effectiveness_confidence": 0.8,
        },
        recurrence_target_state=inputs["recurrence_target_state"],
        recurrence_roadmap_summary=inputs["recurrence_roadmap_summary"],
        recurrence_history=inputs["recurrence_history"],
        recurrence_governance_summary={
            **inputs["recurrence_governance_summary"],
            "governance_health_score": 85.0,
            "governance_confidence": 0.8,
        },
        recurrence_forecast_summary={
            **inputs["recurrence_forecast_summary"],
            "forecast_confidence": 0.8,
        },
        forecast_effectiveness_summary=inputs["forecast_effectiveness_summary"],
        remediation_effectiveness_summary=inputs["remediation_effectiveness_summary"],
        recurrence_lifecycle_summary=inputs["recurrence_lifecycle_summary"],
        recurrence_roi_summary=inputs["recurrence_roi_summary"],
        portfolio_trajectory_summary={"trajectory_available": True},
    )
    assert complete_completion["program_graduated"] is True


def test_completion_gap_analysis_links_to_roadmap() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    completion = build_recurrence_completion_assessment(**_completion_inputs_from_log(log))

    gaps = completion["completion_gap_analysis"]
    assert gaps
    assert all("roadmap_dependency" in row for row in gaps)
    assert any(row["roadmap_dependency"] == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME for row in gaps)


def test_summarize_recurrence_completion_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    completion = build_recurrence_completion_assessment(**_completion_inputs_from_log(log))
    summary = summarize_recurrence_completion(completion)

    assert summary == completion["recurrence_completion_summary"]
    assert summary["estimated_completion_distance"] == round(
        100.0 - float(summary["overall_completion_score"]),
        1,
    )


def test_enrich_recurrence_history_with_completion_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = _fully_enriched_history(log)

    assert "recurrence_completion" in history
    assert "recurrence_completion_summary" in history
    assert "recurrence_completion_gap_analysis" in history
    assert history["recurrence_completion_summary"]["protected_replay_only"] is True
    assert history["recurrence_completion_summary"]["program_graduated"] is False

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert reloaded["recurrence_completion"]["observability_completion"]["completion_met"] is True


def _graduation_audit_inputs_from_log(log: dict[str, object]) -> dict[str, object]:
    completion_inputs = _completion_inputs_from_log(log)
    history = completion_inputs["recurrence_history"]
    maturity = build_recurrence_maturity_assessment(**_maturity_inputs_from_log(log))
    roadmap = build_recurrence_strategic_roadmap(**_roadmap_inputs_from_log(log))
    completion = build_recurrence_completion_assessment(**completion_inputs)
    program = _maturity_inputs_from_log(log)["recurrence_program_effectiveness"]
    return {
        "recurrence_history": history,
        "recurrence_trends": history.get("recurrence_trends"),
        "recurrence_forecast": history.get("recurrence_forecast"),
        "recurrence_portfolio": history.get("recurrence_portfolio"),
        "recurrence_remediation": history.get("recurrence_remediation_targets"),
        "recurrence_roi": history.get("recurrence_roi"),
        "recurrence_governance": history.get("recurrence_governance"),
        "recurrence_lifecycle": history.get("recurrence_lifecycle"),
        "recurrence_program_effectiveness": program,
        "recurrence_maturity": maturity,
        "recurrence_roadmap": roadmap,
        "recurrence_completion": completion,
    }


def test_empty_graduation_audit_reports_major_gaps() -> None:
    audit = build_recurrence_graduation_audit()
    summary = audit["recurrence_graduation_audit_summary"]

    assert summary["graduation_readiness_score"] < 50.0
    assert summary["readiness_level"] == "major_gaps_remain"
    assert summary["program_graduated"] is False


def test_capability_validation_with_protected_history() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    capabilities = validate_recurrence_program_capabilities(**_graduation_audit_inputs_from_log(log))

    assert len(capabilities) == 12
    assert all(row["implemented"] for row in capabilities)
    assert any(row["capability_id"] == "historical_persistence" for row in capabilities)


def test_graduation_readiness_scoring() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    audit = build_recurrence_graduation_audit(**_graduation_audit_inputs_from_log(log))
    readiness = audit["graduation_readiness"]

    assert 50.0 <= float(readiness["graduation_readiness_score"]) <= 89.0
    assert readiness["readiness_level"] in {"minor_gaps_remain", "moderate_gaps_remain"}


def test_blind_spot_detection() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    audit = build_recurrence_graduation_audit(**_graduation_audit_inputs_from_log(log))

    blind_spot_ids = {row["blind_spot_id"] for row in audit["blind_spots"]}
    assert "recurrence_data_quality" in blind_spot_ids
    assert "recurrence_trajectory_history" in blind_spot_ids
    assert audit["recurrence_graduation_audit_summary"]["critical_blind_spots"] >= 1


def test_redundancy_detection() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    audit = build_recurrence_graduation_audit(**_graduation_audit_inputs_from_log(log))

    redundancy_ids = {row["redundancy_id"] for row in audit["redundancies"]}
    assert "maturity_vs_completion_dimensions" in redundancy_ids
    assert "governance_health_vs_governance_effectiveness" in redundancy_ids


def test_summarize_recurrence_graduation_audit_matches_build_output() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    audit = build_recurrence_graduation_audit(**_graduation_audit_inputs_from_log(log))
    summary = summarize_recurrence_graduation_audit(audit)

    assert summary == audit["recurrence_graduation_audit_summary"]


def test_render_recurrence_graduation_audit_report_markdown() -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    audit = build_recurrence_graduation_audit(**_graduation_audit_inputs_from_log(log))
    markdown = render_recurrence_graduation_audit_report_markdown(audit)

    assert "# BQ16 Recurrence Graduation Audit" in markdown
    assert "# Capability Coverage" in markdown
    assert "# Blind Spots" in markdown
    assert "# Redundancies" in markdown


def test_enrich_recurrence_history_with_graduation_audit_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_graduation_audit(_fully_enriched_history(log))

    assert "recurrence_graduation_audit" in history
    assert "recurrence_graduation_audit_summary" in history
    assert history["recurrence_graduation_audit_summary"]["protected_replay_only"] is True
    assert history["recurrence_graduation_audit_summary"]["program_graduated"] is False

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(reloaded["recurrence_graduation_audit"]["capability_coverage"]) == 12


def _confidence_audit_base_history(**overrides: object) -> dict[str, object]:
    history: dict[str, object] = {
        "total_rows": 11,
        "unique_recurrence_count": 4,
        "persistence_population": "protected_replay_history",
    }
    history.update(overrides)
    return history


def _confidence_audit_inputs(
    *,
    forecast_confidence: float = 1.0,
    governance_confidence: float = 1.0,
    effectiveness_confidence: float = 0.82,
    forecast_accuracy: float = 1.0,
    trajectory_available: bool = False,
    governance_health_score: float = 55.2,
    remediation_effectiveness: float = 0.0,
    closure_rate: float = 0.0,
    lifecycle_health_score: float = 45.0,
    total_observations: int = 11,
    total_keys: int = 4,
) -> dict[str, object]:
    return {
        "recurrence_forecast": {
            "forecast_summary": {"forecast_confidence": forecast_confidence},
        },
        "recurrence_governance": {
            "governance_confidence": governance_confidence,
            "governance_health_score": governance_health_score,
            "governance_summary": {
                "governance_confidence": governance_confidence,
                "governance_health_score": governance_health_score,
            },
            "watchlist": [{"recurrence_key": f"key-{index}"} for index in range(total_keys)],
            "owners": [{"owner": "owner-a", "watchlist_entries": total_keys}],
        },
        "recurrence_program_effectiveness": {
            "program_effectiveness_summary": {
                "effectiveness_confidence": effectiveness_confidence,
            },
            "forecast_effectiveness_summary": {
                "forecast_accuracy": forecast_accuracy,
            },
            "remediation_effectiveness_summary": {
                "remediation_effectiveness": remediation_effectiveness,
            },
            "portfolio_trajectory_summary": {
                "trajectory_available": trajectory_available,
            },
        },
        "recurrence_lifecycle": {
            "lifecycle_summary": {
                "lifecycle_health_score": lifecycle_health_score,
                "closure_rate": closure_rate,
            },
            "closure_effectiveness": {"closure_rate": closure_rate},
        },
        "recurrence_maturity": {
            "recurrence_maturity_summary": {
                "operational_readiness_score": 76.4,
                "overall_maturity_score": 73.0,
            }
        },
        "recurrence_completion": {
            "recurrence_completion_summary": {
                "program_graduated": False,
                "overall_completion_score": 79.2,
            }
        },
        "recurrence_trajectory_summary": {
            "trajectory_available": trajectory_available,
            "snapshot_count": 2 if trajectory_available else 1,
        },
        "recurrence_history": _confidence_audit_base_history(
            total_rows=total_observations,
            unique_recurrence_count=total_keys,
        ),
        "recurrence_portfolio_summary": {
            "total_observations": total_observations,
            "total_keys": total_keys,
            "owner_concentration_ratio": 0.75,
        },
    }


def test_calibrated_confidence_status() -> None:
    audit = build_recurrence_confidence_audit(
        **_confidence_audit_inputs(
            forecast_confidence=0.86,
            governance_confidence=0.68,
            effectiveness_confidence=0.30,
            forecast_accuracy=1.0,
            trajectory_available=False,
            governance_health_score=55.2,
            remediation_effectiveness=0.0,
            closure_rate=0.0,
            lifecycle_health_score=45.0,
        )
    )

    assert audit["forecast_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_CALIBRATED
    assert audit["governance_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_CALIBRATED
    assert audit["effectiveness_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_CALIBRATED


def test_overconfidence_detection() -> None:
    audit = build_recurrence_confidence_audit(**_confidence_audit_inputs())

    assert audit["forecast_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
    assert audit["effectiveness_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
    assert audit["recurrence_confidence_calibration_summary"]["graduation_confidence_ready"] is False


def test_underconfidence_detection() -> None:
    audit = build_recurrence_confidence_audit(
        **_confidence_audit_inputs(
            forecast_confidence=0.40,
            governance_confidence=0.35,
            effectiveness_confidence=0.10,
            forecast_accuracy=1.0,
            trajectory_available=True,
            governance_health_score=90.0,
            remediation_effectiveness=0.8,
            closure_rate=0.5,
            lifecycle_health_score=85.0,
        )
    )

    assert audit["forecast_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT
    assert audit["governance_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT
    assert audit["effectiveness_confidence_audit"]["confidence_status"] == RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT


def test_graduation_threshold_validation_classifications() -> None:
    audit = build_recurrence_confidence_audit(**_confidence_audit_inputs())
    validations = {
        row["threshold"]: row["validation_status"]
        for row in audit["graduation_threshold_validation"]
    }

    assert validations["forecast_confidence"] == RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
    assert validations["effectiveness_confidence"] == RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
    assert validations["operational_readiness"] == RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
    assert validations["trajectory_available"] == RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC


def test_graduation_threshold_supported_when_trajectory_active() -> None:
    audit = build_recurrence_confidence_audit(
        **_confidence_audit_inputs(
            trajectory_available=True,
            forecast_confidence=0.80,
            effectiveness_confidence=0.80,
            remediation_effectiveness=0.6,
            closure_rate=0.25,
            lifecycle_health_score=80.0,
        )
    )
    validations = {
        row["threshold"]: row["validation_status"]
        for row in audit["graduation_threshold_validation"]
    }

    assert validations["trajectory_available"] == RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED


def test_blind_spot_reassessment_reflects_bq_c1_and_bq_c2() -> None:
    audit = build_recurrence_confidence_audit(**_confidence_audit_inputs())
    reassessments = {
        row["blind_spot_id"]: row["status_change"] for row in audit["blind_spot_reassessment"]
    }

    assert reassessments["recurrence_data_quality"] == RECURRENCE_BLIND_SPOT_REDUCED
    assert reassessments["recurrence_trajectory_history"] == RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED


def test_calculate_confidence_calibration_score() -> None:
    score = calculate_confidence_calibration_score(
        forecast_confidence_audit={
            "calibration_gap": 0.05,
            "confidence_status": RECURRENCE_CONFIDENCE_STATUS_CALIBRATED,
        },
        governance_confidence_audit={
            "calibration_gap": 0.04,
            "confidence_status": RECURRENCE_CONFIDENCE_STATUS_CALIBRATED,
        },
        effectiveness_confidence_audit={
            "calibration_gap": 0.03,
            "confidence_status": RECURRENCE_CONFIDENCE_STATUS_CALIBRATED,
        },
    )

    assert score["confidence_calibration_score"] >= 90.0
    assert score["interpretation"] == "well_calibrated"
    assert score["graduation_confidence_ready"] is True


def test_summarize_recurrence_confidence_calibration_matches_build_output() -> None:
    audit = build_recurrence_confidence_audit(**_confidence_audit_inputs())
    summary = summarize_recurrence_confidence_calibration(audit)

    assert summary == audit["recurrence_confidence_calibration_summary"]
    assert summary["protected_replay_only"] is True


def test_render_recurrence_confidence_calibration_report_markdown() -> None:
    audit = build_recurrence_confidence_audit(**_confidence_audit_inputs())
    markdown = render_recurrence_confidence_calibration_report_markdown(audit)

    assert "# BQ-C3 Confidence Calibration Audit" in markdown
    assert "# Forecast Confidence" in markdown
    assert "# Governance Confidence" in markdown
    assert "# Effectiveness Confidence" in markdown
    assert "# Graduation Threshold Validation" in markdown
    assert "# Blind Spot Reassessment" in markdown
    assert "# Recommended Actions" in markdown


def test_enrich_recurrence_history_with_confidence_audit_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_confidence_audit(_fully_enriched_history(log))

    assert "recurrence_confidence_audit" in history
    assert "recurrence_confidence_calibration_summary" in history
    assert history["recurrence_confidence_calibration_summary"]["protected_replay_only"] is True

    out_path = tmp_path / "history.json"
    out_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reloaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert "forecast_confidence_audit" in reloaded["recurrence_confidence_audit"]
    assert "graduation_threshold_validation" in reloaded["recurrence_confidence_audit"]


def test_build_recurrence_final_graduation_decision_recommends_validation_cycle() -> None:
    audit = build_recurrence_confidence_audit(**_confidence_audit_inputs(trajectory_available=True))
    decision = build_recurrence_final_graduation_decision(
        recurrence_trajectory_summary={
            "trajectory_available": True,
            "snapshot_count": 2,
            "portfolio_risk_change": 0.0,
            "governance_health_change": 0.0,
            "lifecycle_health_change": 0.0,
            "operational_readiness_change": 0.0,
            "effectiveness_change": 0.0,
            "maturity_change": 0.0,
            "stability_trajectory": {"absolute_change": 0.0},
            "message": "Trajectory change detection active across baseline and current snapshots.",
        },
        recurrence_confidence_audit=audit,
        recurrence_graduation_audit=build_recurrence_graduation_audit(),
        recurrence_completion={"recurrence_completion_summary": {"program_graduated": False, "overall_completion_score": 82.5}},
        recurrence_maturity={"recurrence_maturity_summary": {"overall_maturity_score": 73.0, "operational_readiness_score": 76.4}},
    )

    assert decision["trajectory_activation"]["trajectory_available"] is True
    assert decision["calibration_comparison"]["trajectory_activated"] is True
    assert decision["final_recommendation"] in {
        RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE,
        RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE,
    }
    assert decision["formal_graduation_criteria_met"] is False


def test_render_recurrence_final_graduation_decision_report_markdown() -> None:
    audit = build_recurrence_confidence_audit(**_confidence_audit_inputs(trajectory_available=True))
    decision = build_recurrence_final_graduation_decision(
        recurrence_trajectory_summary={"trajectory_available": True, "snapshot_count": 2},
        recurrence_confidence_audit=audit,
    )
    markdown = render_recurrence_final_graduation_decision_report_markdown(decision)

    assert "# BQ-C4 Final Graduation Decision" in markdown
    assert "# Trajectory Activation" in markdown
    assert "# Confidence Recalculation" in markdown
    assert "# Calibration Comparison" in markdown
    assert "# Graduation Readiness" in markdown
    assert "# Remaining Blockers" in markdown
    assert "# Final Recommendation" in markdown


def test_summarize_recurrence_outcomes_finds_no_validated_outcomes_without_closure() -> None:
    summary = summarize_recurrence_outcomes(
        recurrence_lifecycle={
            "total_keys": 4,
            "keys": [
                {
                    "recurrence_key": "recurrence:v1:test|owner|field|path.py",
                    "lifecycle_stage": "emerging",
                    "last_seen": "2026-06-20T12:00:00Z",
                }
            ],
        },
        recurrence_trajectory_summary={"trajectory_available": True},
        as_of="2026-06-20T12:00:00Z",
    )

    assert summary["has_validated_outcomes"] is False
    assert summary["validated_outcome_count"] == 0


def test_summarize_recurrence_outcomes_accepts_dormant_key_with_inactivity() -> None:
    summary = summarize_recurrence_outcomes(
        recurrence_lifecycle={
            "total_keys": 1,
            "keys": [
                {
                    "recurrence_key": "recurrence:v1:test|owner|field|path.py",
                    "lifecycle_stage": "dormant",
                    "last_seen": "2026-01-01T12:00:00Z",
                }
            ],
        },
        recurrence_trajectory_summary={"trajectory_available": True},
        event_log={"events": [{"recurrence_key": "recurrence:v1:test|owner|field|path.py", "recurrence_status": "active"}]},
        as_of="2026-06-20T12:00:00Z",
    )

    assert summary["has_validated_outcomes"] is True
    assert summary["dormant_keys"] == 1
    assert summary["validated_outcomes"][0]["signal_type"] == RECURRENCE_OUTCOME_SIGNAL_DORMANT


def test_summarize_recurrence_outcomes_rejects_synthetic_key() -> None:
    summary = summarize_recurrence_outcomes(
        recurrence_lifecycle={
            "total_keys": 1,
            "keys": [
                {
                    "recurrence_key": "recurrence:v1:unknown|unknown|field|unknown",
                    "lifecycle_stage": "retired",
                    "last_seen": "2026-01-01T12:00:00Z",
                }
            ],
        },
        as_of="2026-06-20T12:00:00Z",
    )

    assert summary["has_validated_outcomes"] is False
    assert summary["rejected_signals"][0]["rejection_reason"] == RECURRENCE_OUTCOME_REJECTION_SYNTHETIC


def test_calculate_effectiveness_evidence_strength_requires_outcomes() -> None:
    with_outcomes = calculate_effectiveness_evidence_strength(
        outcome_validation_summary={
            "total_keys": 4,
            "validated_outcome_count": 1,
            "has_validated_outcomes": True,
            "validated_closure_rate": 0.25,
            "validated_recurrence_reduction_rate": 0.0,
            "validated_remediation_impact_rate": 0.0,
        },
        trajectory_available=True,
    )
    without_outcomes = calculate_effectiveness_evidence_strength(
        outcome_validation_summary={
            "total_keys": 4,
            "validated_outcome_count": 0,
            "has_validated_outcomes": False,
        },
        trajectory_available=True,
    )

    assert with_outcomes > without_outcomes
    assert without_outcomes == 0.2


def _outcome_validation_inputs(**overrides: object) -> dict[str, object]:
    inputs = {
        key: value
        for key, value in _confidence_audit_inputs(trajectory_available=True).items()
        if key != "recurrence_portfolio_summary"
    }
    inputs.update(overrides)
    return inputs


def test_build_recurrence_outcome_validation_recommends_validation_period_without_outcomes() -> None:
    validation = build_recurrence_outcome_validation(**_outcome_validation_inputs())

    assert validation["outcome_validation_summary"]["has_validated_outcomes"] is False
    assert validation["final_graduation_recommendation"] == BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD
    assert validation["formal_graduation_criteria_met"] is False
    assert validation["missing_outcome_signal"] is not None


def test_build_recurrence_outcome_validation_improves_evidence_with_dormant_outcome() -> None:
    lifecycle = {
        "total_keys": 1,
        "keys": [
            {
                "recurrence_key": "recurrence:v1:test|owner|field|path.py",
                "lifecycle_stage": "dormant",
                "last_seen": "2026-01-01T12:00:00Z",
            }
        ],
    }
    validation = build_recurrence_outcome_validation(
        **_outcome_validation_inputs(
            recurrence_lifecycle=lifecycle,
            event_log={"events": [{"recurrence_key": "recurrence:v1:test|owner|field|path.py", "recurrence_status": "active"}]},
            as_of="2026-06-20T12:00:00Z",
        )
    )

    effectiveness = validation["effectiveness_confidence_audit"]
    assert effectiveness["evidence_strength"] > BQC4_EFFECTIVENESS_BASELINE["evidence_strength"]
    assert effectiveness["validated_outcome_count"] == 1


def test_render_recurrence_outcome_validation_report_markdown() -> None:
    validation = build_recurrence_outcome_validation(**_outcome_validation_inputs())
    markdown = render_recurrence_outcome_validation_report_markdown(validation)

    assert "# BQ-C5 Effectiveness Outcome Validation" in markdown
    assert "# Outcome Evidence" in markdown
    assert "# Effectiveness Confidence" in markdown
    assert "# Calibration Recalculation" in markdown
    assert "# Graduation Impact" in markdown
    assert "# Final Recommendation" in markdown


def test_enrich_recurrence_history_with_outcome_validation_is_additive(tmp_path: Path) -> None:
    log = _protected_event_log_with_recorded_at("2026-06-04T22:31:59Z")
    history = enrich_recurrence_history_with_outcome_validation(
        _fully_enriched_history(log),
        event_log=log,
        as_of="2026-06-20T20:00:00Z",
    )

    assert "recurrence_outcome_validation" in history
    assert "outcome_validation_summary" in history
    assert history["outcome_validation_summary"]["protected_replay_only"] is True
