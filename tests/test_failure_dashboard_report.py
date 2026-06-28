from __future__ import annotations

import json
from pathlib import Path

from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import (
    assert_dashboard_recurrence_payload,
    assert_dashboard_recurrence_sections,
    assert_long_session_operator_metrics,
    assert_recurrence_history_payload_shape,
    assert_recurrence_payload_counts,
    assert_recurrence_payload_entry,
    assert_recurrence_payload_regression_rate,
    assert_recurrence_payload_status,
    assert_report_has_command_guidance,
    assert_report_has_failure_locator,
    assert_report_has_lineage_summary,
    assert_report_has_owner_drift,
    assert_report_has_recurrence_summary,
    assert_report_has_rerun_scorecard_summary,
    assert_report_sections_present,
    clear_recorded_failure_dashboard_rows,
    clear_recorded_protected_replay_failures,
    clear_recorded_rerun_drift_scorecards,
    protected_replay_recurrence_event_metadata,
    recorded_protected_replay_failure_rows,
    recorded_runtime_lineage_events,
    record_rerun_drift_scorecard,
    recorded_rerun_drift_scorecards,
    render_bug_recurrence_history_markdown,
    render_protected_replay_failure_report,
    render_rerun_drift_scorecard_markdown,
    write_bug_recurrence_history_artifacts,
    write_owner_drift_risk_artifacts,
    write_protected_replay_failure_report_if_present,
    write_rerun_drift_scorecard_artifacts,
    write_rerun_drift_scorecard_artifacts_if_requested,
)
from tests.helpers.replay_bug_recurrence import (
    aggregate_protected_recurrence_history_from_event_log,
    append_recurrence_events,
    append_recurrence_events_to_persistence_lanes,
    empty_recurrence_event_log,
    normalize_recurrence_event_metadata,
)
from tests.helpers.golden_replay_api import (
    classify_golden_drift,
    compare_golden_replay_reruns,
    render_long_session_replay_summary_markdown,
)
from tests.helpers.failure_dashboard_fixtures import record_selected_speaker_protected_failure
from tests.helpers.replay_observed_row_fixtures import (
    observed_failure_row,
    protected_speaker_failure_turn,
    synthetic_rerun_turn,
)


# Protected replay failure report lock: scenario-specific locator text and row identity stay direct.


def test_protected_replay_failure_report_renders_canonical_sections(tmp_path) -> None:
    report_path = tmp_path / "replay_failure_report.md"
    clear_recorded_protected_replay_failures()
    try:
        assert write_protected_replay_failure_report_if_present(path=report_path) is None
        record_selected_speaker_protected_failure(
            protected_speaker_failure_turn(),
        )

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

        written = write_protected_replay_failure_report_if_present(
            path=report_path,
            command_used="python -m pytest -m golden_replay -q",
            generated_at="2026-05-26T00:00:00Z",
        )
        assert written == report_path
        report = report_path.read_text(encoding="utf-8")
        assert "synthetic_protected_bridge" in report
        assert "selected_speaker_id: exact value mismatch" in report
        assert "data/validation/scenario_spines/synthetic_fixture.json" in report
        assert "synthetic_branch" in report
        assert "synthetic_turn_01" in report
        assert "structural_drift" in report
        assert "game/speaker_contract_enforcement.py" in report
        assert_report_sections_present(
            report,
            title="# Protected Replay Failure Report",
            failure_locator=True,
            owner_drift_breakdown=True,
            sanitizer_summary=True,
            lineage_summary=True,
            focused_failing_tests=True,
            protected_replay_lane=True,
            command_guidance=True,
        )
        assert_report_has_owner_drift(report, bucket="speaker_drift")
    finally:
        clear_recorded_protected_replay_failures()


def test_protected_replay_failure_report_handles_missing_replay_identity(tmp_path) -> None:
    turn = protected_speaker_failure_turn(include_replay_identity=False)
    report_path = tmp_path / "replay_failure_report_no_identity.md"
    clear_recorded_protected_replay_failures()
    try:
        record_selected_speaker_protected_failure(
            turn,
            scenario_id="synthetic_inline_bridge",
            test_node_id="tests/test_golden_replay.py::synthetic_inline_bridge",
        )
        written = write_protected_replay_failure_report_if_present(
            path=report_path,
            command_used="python -m pytest -m golden_replay -q",
            generated_at="2026-05-26T00:00:00Z",
        )
        assert written == report_path
        report = report_path.read_text(encoding="utf-8")
        assert "synthetic_inline_bridge" in report
        assert_report_has_failure_locator(
            report,
            table_row=(
                "| synthetic_inline_bridge | none | none | 0 | none | selected_speaker_id: exact value mismatch |"
            ),
        )
        assert_report_has_command_guidance(report)
    finally:
        clear_recorded_protected_replay_failures()


def test_golden_drift_classifier_buckets_exact_structural_and_semantic_drift() -> None:
    observed = {
        "final_text": "Planner: the guard shrugs.",
        "route_kind": "action",
        "selected_speaker_id": "guard",
        "final_emitted_source": "global_scene_fallback",
        "fallback_family": "gate_terminal_repair",
        "scaffold_leakage": True,
        "unavailable": [],
        "trace": {"canonical_entry": {"target_actor_id": "guard"}},
    }
    expectation = {
        "exact_text": "The runner answers.",
        "equals": {
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "trace.canonical_entry.target_actor_id": "runner",
        },
        "not_equals": {"final_emitted_source": "global_scene_fallback"},
        "text_must_not_include": ["Planner"],
        "scaffold_leakage": False,
    }

    drift = classify_golden_drift(observed, expectation)

    assert drift["status"] == "fail"
    assert drift["summary"]["exact_drift"] == 1
    assert drift["summary"]["structural_drift"] == 4
    assert drift["summary"]["semantic_drift"] == 2


def test_golden_drift_classification_ignores_runtime_lineage_diagnostics() -> None:
    observed = {
        "scenario_id": "lineage_diagnostic_only",
        "turn_index": 0,
        "final_text": "The runner answers.",
        "route_kind": "dialogue",
        "unavailable": [],
    }
    expectation = {"equals": {"route_kind": "dialogue"}}
    baseline = classify_golden_drift(observed, expectation)
    with_lineage = classify_golden_drift(
        {
            **observed,
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="scene_opening",
                )
            ],
        },
        expectation,
    )
    assert with_lineage == baseline


def test_golden_drift_opt_in_dashboard_records_lineage_outside_classification_rows(monkeypatch) -> None:
    event = make_runtime_lineage_event(
        event_kind="gate_outcome",
        stage="gate",
        owner="game.final_emission_gate",
        gate_path="accept_unchanged",
    )
    clear_recorded_failure_dashboard_rows()
    monkeypatch.setenv("ASHEN_WRITE_FAILURE_DASHBOARD", "1")
    try:
        drift = classify_golden_drift(
            {
                "scenario_id": "recorded_lineage",
                "turn_index": 0,
                "final_text": "The runner answers.",
                "route_kind": "dialogue",
                "unavailable": [],
                "runtime_lineage_events": [event],
            },
            {"equals": {"route_kind": "dialogue"}},
        )
        assert drift["status"] == "pass"
        assert drift["failure_classifications"] == []
        assert recorded_runtime_lineage_events() == [event]
    finally:
        clear_recorded_failure_dashboard_rows()


def _synthetic_rerun_scorecard() -> dict:
    event = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="sealed_or_global_replacement",
    )
    return compare_golden_replay_reruns(
        [synthetic_rerun_turn(final_text="The runner answers.")],
        [
            synthetic_rerun_turn(
                selected_speaker_id="guard",
                route_kind="action",
                fallback_family="gate_terminal_repair",
                fallback_owner="sealed_gate",
                final_text="The guard answers.",
                runtime_lineage_events=[event],
            )
        ],
    )


# Rerun scorecard/report lock: delta counts and owner-drift summary are per-scorecard contracts.


def test_rerun_drift_scorecard_markdown_summarizes_fabricated_scorecard() -> None:
    scorecard = _synthetic_rerun_scorecard()

    markdown = render_rerun_drift_scorecard_markdown(
        scorecard,
        generated_at="2026-05-30T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert_report_has_rerun_scorecard_summary(
        markdown,
        turns_compared=1,
        speaker_deltas=1,
        route_deltas=1,
        fallback_deltas=1,
        text_fingerprint_deltas=1,
        runtime_lineage_deltas=1,
        semantic_delta_frequency_deltas=0,
        owner_drift_bucket="speaker_drift",
        drift_turn_table=True,
        text_hash=True,
    )


def test_rerun_drift_scorecard_writer_creates_json_and_markdown(tmp_path) -> None:
    scorecard = _synthetic_rerun_scorecard()
    json_path = tmp_path / "rerun_drift_scorecard.json"
    markdown_path = tmp_path / "rerun_drift_scorecard.md"

    written_json, written_markdown = write_rerun_drift_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-05-30T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    assert json.loads(json_path.read_text(encoding="utf-8")) == scorecard
    markdown = markdown_path.read_text(encoding="utf-8")
    assert_report_has_rerun_scorecard_summary(markdown, speaker_deltas=1)


def test_rerun_drift_scorecard_writer_is_opt_in_by_default(tmp_path) -> None:
    scorecard = _synthetic_rerun_scorecard()
    json_path = tmp_path / "default_off.json"
    markdown_path = tmp_path / "default_off.md"

    written = write_rerun_drift_scorecard_artifacts_if_requested(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        env={},
    )

    assert written is None
    assert not json_path.exists()
    assert not markdown_path.exists()


def test_rerun_drift_scorecard_writer_handles_missing_comparison(tmp_path) -> None:
    json_path = tmp_path / "no_comparison.json"
    markdown_path = tmp_path / "no_comparison.md"

    written_json, written_markdown = write_rerun_drift_scorecard_artifacts(
        None,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-05-30T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["comparison_available"] is False
    assert "No rerun comparison available" in markdown_path.read_text(encoding="utf-8")


def test_rerun_drift_scorecard_recording_does_not_change_failure_dashboard_behavior(tmp_path) -> None:
    scorecard = _synthetic_rerun_scorecard()
    clear_recorded_rerun_drift_scorecards()
    clear_recorded_protected_replay_failures()
    try:
        record_rerun_drift_scorecard(scorecard)

        assert recorded_rerun_drift_scorecards() == [scorecard]
        assert write_protected_replay_failure_report_if_present(path=tmp_path / "failure_report.md") is None
    finally:
        clear_recorded_rerun_drift_scorecards()
        clear_recorded_protected_replay_failures()


def test_render_protected_replay_failure_report_includes_owner_drift_bucket() -> None:
    observed = observed_failure_row(selected_speaker_id="guard")
    rows = classify_replay_failure(
        scenario_id="report_probe",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": "selected_speaker_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "equals mismatch",
                "drift_bucket": "structural_drift",
                "replay_tags": ["structural_drift"],
            }
        ],
    )
    enriched = dict(rows[0])
    enriched["test_node_id"] = "tests/test_failure_dashboard_report.py::probe"
    enriched["failed_invariant"] = "selected_speaker_id: equals mismatch"

    report = render_protected_replay_failure_report([enriched], generated_at="2026-06-06T00:00:00Z")
    assert_report_has_owner_drift(report, bucket="speaker_drift", breakdown=True)


def test_render_rerun_scorecard_includes_owner_drift_summary() -> None:
    scorecard = compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "A."}],
        [{"selected_speaker_id": "guard", "route_kind": "dialogue", "final_text": "A."}],
    )
    markdown = render_rerun_drift_scorecard_markdown(scorecard, generated_at="2026-06-06T00:00:00Z")
    assert_report_has_owner_drift(
        markdown,
        summary=True,
        summary_row="| `speaker_drift` | `1` |",
    )
    assert scorecard["report_only"] is True


def test_render_rerun_scorecard_empty_owner_drift_summary() -> None:
    scorecard = compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "final_text": "Stable."}],
        [{"selected_speaker_id": "runner", "final_text": "Stable."}],
    )
    markdown = render_rerun_drift_scorecard_markdown(scorecard)
    assert_report_has_owner_drift(markdown, summary=True, empty_summary=True)


def _recurrence_classification_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "scenario_id": "bug_recurrence_probe",
        "turn_index": 0,
        "category": "speaker",
        "primary_owner": "speaker",
        "owner_drift_bucket": "speaker_drift",
        "field_path": "selected_speaker_id",
        "investigate_first": "game/speaker_contract_enforcement.py",
    }
    row.update(overrides)
    return row


def _golden_protected_recurrence_metadata(**overrides: object) -> dict[str, object]:
    defaults: dict[str, object] = {
        "command_used": "pytest protected recurrence",
        "generated_at": "2026-06-10T00:00:00Z",
        "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
    }
    defaults.update(overrides)
    return protected_replay_recurrence_event_metadata(**defaults)


_VOCATIVE_PROBE_RECORDED_AT = "2026-06-04T22:31:59Z"


def _recurrence_history_artifact_paths(tmp_path: Path) -> tuple[Path, Path]:
    return (
        tmp_path / "bug_recurrence_history.json",
        tmp_path / "bug_recurrence_history.md",
    )


def _write_vocative_recurrence_artifacts(
    tmp_path: Path,
    **row_overrides: object,
) -> tuple[str, dict[str, object]]:
    """Write protected vocative_probe recurrence artifacts and return markdown + JSON payload."""
    json_path, markdown_path = _recurrence_history_artifact_paths(tmp_path)
    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe", **row_overrides)],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at=_VOCATIVE_PROBE_RECORDED_AT,
        ),
    )
    return (
        markdown_path.read_text(encoding="utf-8"),
        json.loads(json_path.read_text(encoding="utf-8")),
    )


def _write_alpha_recurrence_payload(
    tmp_path: Path,
    **row_overrides: object,
) -> dict[str, object]:
    """Write protected alpha recurrence artifacts and return the JSON payload."""
    json_path, markdown_path = _recurrence_history_artifact_paths(tmp_path)
    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha", **row_overrides)],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    return json.loads(json_path.read_text(encoding="utf-8"))


# Recurrence writer/routing lock: each test encodes a distinct lane, append, or empty-write contract.


def test_bug_recurrence_history_writer_routes_session_rows_to_diagnostic_lane(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"
    session_log_path = tmp_path / "bug_recurrence_session_diagnostic_event_log.json"
    persistence: dict[str, object] = {}

    written_json, written_markdown = write_bug_recurrence_history_artifacts(
        [
            _recurrence_classification_row(scenario_id="b"),
            _recurrence_classification_row(scenario_id="a"),
        ],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        session_diagnostic_event_log_path=session_log_path,
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest recurrence",
        persistence_report=persistence,
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    assert persistence["protected_appended"] == 0
    assert persistence["session_diagnostic_appended"] == 2
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert_recurrence_payload_counts(
        payload,
        total_rows=0,
        unique_recurrence_count=0,
        summary_empty=True,
        persistence_population="protected_replay_history",
    )

    protected_log = json.loads(event_log_path.read_text(encoding="utf-8"))
    session_log = json.loads(session_log_path.read_text(encoding="utf-8"))
    assert protected_log["events"] == []
    assert len(session_log["events"]) == 2
    assert_recurrence_payload_entry(
        session_log["events"][0],
        event_source="session",
        command="pytest recurrence",
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    assert_report_has_recurrence_summary(markdown, empty=True)


def test_bug_recurrence_history_writer_appends_commit_worthy_protected_rows(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    write_bug_recurrence_history_artifacts(
        [
            _recurrence_classification_row(scenario_id="b"),
            _recurrence_classification_row(scenario_id="a"),
        ],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest recurrence",
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert_recurrence_payload_counts(payload, total_rows=2, unique_recurrence_count=1)
    assert_recurrence_payload_status(payload, occurrence_count=2, status="active")
    assert_recurrence_payload_regression_rate(payload, numerator=1, rate=1.0)

    markdown = markdown_path.read_text(encoding="utf-8")
    assert_report_has_recurrence_summary(
        markdown,
        regression_rate=(
            "Regression Recurrence Rate: 100.0% (1 / 1 recurrence keys active by repeated observation)."
        ),
        status_markers=("active",),
    )

    event_log = json.loads(event_log_path.read_text(encoding="utf-8"))
    assert len(event_log["events"]) == 2
    assert_recurrence_payload_entry(
        event_log["events"][0],
        event_source="protected_replay_failure",
        artifact_source="artifacts/golden_replay/replay_failure_report.md",
    )


def test_bug_recurrence_history_writer_appends_and_increases_occurrence_count(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"
    row = _recurrence_classification_row(scenario_id="first-run")

    write_bug_recurrence_history_artifacts(
        [row],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest recurrence append 1",
        recorded_at="2026-06-10T00:00:00Z",
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            command_used="pytest recurrence append 1",
        ),
    )
    first_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert_recurrence_payload_counts(first_payload, total_rows=1)
    assert_recurrence_payload_status(first_payload, occurrence_count=1, status="watch")

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="second-run")],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        generated_at="2026-06-11T00:00:00Z",
        command_used="pytest recurrence append 2",
        recorded_at="2026-06-11T00:00:00Z",
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            command_used="pytest recurrence append 2",
            generated_at="2026-06-11T00:00:00Z",
        ),
    )
    second_payload = json.loads(json_path.read_text(encoding="utf-8"))
    event_log = json.loads(event_log_path.read_text(encoding="utf-8"))

    assert len(event_log["events"]) == 2
    assert_recurrence_payload_counts(second_payload, total_rows=2)
    assert_recurrence_payload_status(second_payload, occurrence_count=2, status="active")


def test_bug_recurrence_history_empty_write_preserves_prior_history(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="seed")],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest recurrence seed",
        recorded_at="2026-06-10T00:00:00Z",
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            command_used="pytest recurrence seed",
        ),
    )

    write_bug_recurrence_history_artifacts(
        [],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        generated_at="2026-06-11T00:00:00Z",
        command_used="pytest recurrence empty",
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    event_log = json.loads(event_log_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert len(event_log["events"]) == 1
    assert_recurrence_payload_counts(payload, total_rows=1, unique_recurrence_count=1)
    assert "No recurrence history recorded." not in markdown
    assert "selected_speaker_id" in markdown


# Owner-drift / risk-routing lock: ephemeral artifact paths route to session diagnostic lane by policy.


def test_protected_replay_recurrence_write_routes_ephemeral_tmp_events_to_diagnostic_lane(tmp_path) -> None:
    json_path = tmp_path / "owner_drift_risk.json"
    markdown_path = tmp_path / "owner_drift_risk.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"
    session_log_path = tmp_path / "bug_recurrence_session_diagnostic_event_log.json"

    write_owner_drift_risk_artifacts(
        [
            _recurrence_classification_row(
                test_node_id="tests/test_golden_replay.py::test_protected_failure",
            )
        ],
        json_path=json_path,
        markdown_path=markdown_path,
        command_used="pytest protected recurrence",
        generated_at="2026-06-12T00:00:00Z",
        recurrence_event_metadata=protected_replay_recurrence_event_metadata(
            command_used="pytest protected recurrence",
            generated_at="2026-06-12T00:00:00Z",
            artifact_source=tmp_path / "replay_failure_report.md",
        ),
    )

    assert json.loads(event_log_path.read_text(encoding="utf-8"))["events"] == []
    event = json.loads(session_log_path.read_text(encoding="utf-8"))["events"][0]
    assert_recurrence_payload_entry(
        event,
        event_source="protected_replay_failure",
        test_node_id="tests/test_golden_replay.py::test_protected_failure",
        artifact_source=str(tmp_path / "replay_failure_report.md"),
    )


def test_bug_recurrence_empty_write_does_not_append_metadata_only_event(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row()],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest seed",
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            command_used="pytest seed",
        ),
    )

    write_bug_recurrence_history_artifacts(
        [],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        generated_at="2026-06-11T00:00:00Z",
        command_used="pytest empty metadata",
        recurrence_event_metadata=protected_replay_recurrence_event_metadata(
            command_used="pytest empty metadata",
            generated_at="2026-06-11T00:00:00Z",
        ),
    )

    events = json.loads(event_log_path.read_text(encoding="utf-8"))["events"]
    assert len(events) == 1
    assert_recurrence_payload_entry(events[0], recorded_at="2026-06-10T00:00:00Z")


def test_bug_recurrence_history_markdown_shows_watch_and_retired_statuses(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [
            _recurrence_classification_row(
                scenario_id="single",
                field_path="route_kind",
                investigate_first="game/interaction_context.py",
            ),
            _recurrence_classification_row(scenario_id="old", status="deprecated"),
        ],
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest recurrence statuses",
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            command_used="pytest recurrence statuses",
        ),
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    assert_report_has_recurrence_summary(markdown, status_markers=("watch", "retired"))


def test_bug_recurrence_history_markdown_renders_empty_state_cleanly() -> None:
    report = render_bug_recurrence_history_markdown(
        {
            "schema_version": 1,
            "report_only": True,
            "advisory_only": True,
            "total_rows": 0,
            "unique_recurrence_count": 0,
            "recurrences": [],
        },
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest empty recurrence",
    )

    assert_report_has_recurrence_summary(
        report,
        empty=True,
        total_keys=0,
        total_events=0,
        regression_rate=(
            "Regression Recurrence Rate: 0.0% (0 / 0 recurrence keys active by repeated observation)."
        ),
    )


def test_bug_recurrence_history_markdown_renders_regression_recurrence_rate_section() -> None:
    protected_log = append_recurrence_events_to_persistence_lanes(
        empty_recurrence_event_log(),
        empty_recurrence_event_log(),
        [
            _recurrence_classification_row(scenario_id="a"),
            _recurrence_classification_row(scenario_id="b"),
            _recurrence_classification_row(
                scenario_id="c",
                field_path="route_kind",
                investigate_first="game/interaction_context.py",
            ),
        ],
        event_metadata=_golden_protected_recurrence_metadata(),
    )["protected_log"]
    report = render_bug_recurrence_history_markdown(
        aggregate_protected_recurrence_history_from_event_log(protected_log),
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest regression recurrence rate",
    )

    assert_report_has_recurrence_summary(
        report,
        regression_rate=(
            "Regression Recurrence Rate: 50.0% (1 / 2 recurrence keys active by repeated observation)."
        ),
        report_only=True,
        advisory_only=True,
    )


# Recurrence payload spot-check lock: one layer-specific field assertion per markdown/payload pair.


def test_bug_recurrence_history_markdown_renders_recurrence_trends_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Trends",
        required_substrings=(
            "- Emerging keys: `1`",
            "- Recurring keys: `0`",
            "- Persistent keys: `0`",
            "- Dormant keys: `0`",
            "### Newest Recurrence Keys",
        ),
        summary_key="recurrence_trends",
    )
    assert payload["recurrence_timeline"][0]["occurrence_count"] == 1
    assert payload["recurrence_timeline"][0]["trend_classification"] == "emerging"


def test_bug_recurrence_history_payload_backward_compatible_core_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        schema_version=1,
        report_only=True,
        unique_recurrence_count=1,
        required_keys=("recurrence_trends", "recurrence_timeline"),
        regression_rate_metric="regression_recurrence_rate",
    )


def test_bug_recurrence_history_markdown_renders_recurrence_forecast_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        None,
        section="## Recurrence Forecast",
        required_substrings=(
            "- Watch keys: `1`",
            "- Forecast confidence: `low`",
            "- Stability score: `100.0` / 100",
            "### Concentration Metrics",
        ),
    )
    assert payload["recurrence_forecast"]["forecast_summary"]["watch_keys"] == 1
    assert payload["recurrence_forecast"]["risk_concentration"]["top_key_share"] == 1.0


def test_bug_recurrence_history_payload_includes_forecast_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    forecast_summary = payload["recurrence_forecast"]["forecast_summary"]
    assert forecast_summary["schema_version"] == 1
    assert forecast_summary["protected_replay_only"] is True
    assert "key_forecasts" in payload["recurrence_forecast"]


def test_bug_recurrence_history_markdown_renders_recurrence_portfolio_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Portfolio",
        required_substrings=(
            "### Top Owners",
            "### Top Categories",
            "### Top Field Paths",
            "### Top Scenarios",
            "- Portfolio risk score:",
        ),
        summary_key="recurrence_portfolio_summary",
    )
    assert payload["recurrence_portfolio"]["owners"][0]["owner"] == "speaker"


def test_bug_recurrence_history_payload_includes_portfolio_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_dashboard_recurrence_payload(
        payload,
        unique_recurrence_count=1,
        required_keys=("recurrence_portfolio", "recurrence_portfolio_summary"),
        summary_key="recurrence_portfolio_summary",
        summary_schema_version=1,
    )


def test_bug_recurrence_history_markdown_renders_remediation_targets_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Remediation Targets",
        required_substrings=(
            "### Top Keys",
            "### Top Owners",
            "- Estimated portfolio reduction:",
            "- Remediation confidence:",
        ),
        summary_key="recurrence_remediation_summary",
    )
    assert len(payload["recurrence_remediation_targets"]["keys"]) == 1


def test_bug_recurrence_history_payload_includes_remediation_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        unique_recurrence_count=1,
        required_keys=("recurrence_remediation_targets", "recurrence_remediation_summary"),
    )
    assert "reduction_potential" in payload["recurrence_remediation_targets"]["keys"][0]


def test_bug_recurrence_history_markdown_renders_roi_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence ROI",
        required_substrings=(
            "### Top ROI Targets",
            "### Top ROI Owners",
            "- Portfolio ROI score:",
            "- Projected stability gain:",
            "- Projected risk reduction:",
            "- ROI confidence:",
        ),
        summary_key="recurrence_roi_summary",
    )
    assert "roi_score" in payload["recurrence_roi"]["keys"][0]


def test_bug_recurrence_history_payload_includes_roi_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_dashboard_recurrence_payload(
        payload,
        required_keys=("recurrence_roi", "recurrence_roi_summary"),
        summary_key="recurrence_roi_summary",
        summary_schema_version=1,
    )
    assert payload["recurrence_roi"]["keys"][0]["roi_rank"] == 1


def test_bug_recurrence_history_markdown_renders_governance_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Governance",
        required_substrings=(
            "### Watchlist",
            "### Prioritized Targets",
            "### Retire Candidates",
            "### Owner Accountability",
            "- Governance health score:",
            "- Watchlist size:",
        ),
        summary_key="recurrence_governance_summary",
    )
    assert len(payload["recurrence_watchlist"]) == 1


def test_bug_recurrence_history_payload_includes_governance_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        required_keys=(
            "recurrence_governance",
            "recurrence_watchlist",
            "recurrence_governance_summary",
            "recurrence_retirement_summary",
        ),
    )
    assert payload["recurrence_watchlist"][0]["governance_status"] == "watch"


def test_bug_recurrence_history_markdown_renders_lifecycle_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Lifecycle",
        required_substrings=(
            "### Lifecycle Distribution",
            "### Age Distribution",
            "### Transition Summary",
            "### Closure Effectiveness",
            "- Lifecycle health score:",
            "- Closure rate:",
        ),
        summary_key="recurrence_lifecycle_summary",
    )


def test_bug_recurrence_history_payload_includes_lifecycle_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        required_keys=(
            "recurrence_lifecycle",
            "recurrence_lifecycle_summary",
            "recurrence_age_distribution",
            "recurrence_transition_summary",
            "recurrence_closure_effectiveness",
        ),
    )
    assert payload["recurrence_lifecycle"]["keys"][0]["lifecycle_stage"] == "emerging"


def test_bug_recurrence_history_markdown_renders_program_effectiveness_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Program Effectiveness",
        required_substrings=(
            "### Governance Effectiveness",
            "### Remediation Effectiveness",
            "### Forecast Effectiveness",
            "### Portfolio Trajectory",
            "- Program effectiveness score:",
            "- Effectiveness confidence:",
        ),
        summary_key="recurrence_program_effectiveness_summary",
    )


def test_bug_recurrence_history_payload_includes_program_effectiveness_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        required_keys=(
            "recurrence_program_effectiveness",
            "recurrence_program_effectiveness_summary",
            "governance_effectiveness_summary",
            "remediation_effectiveness_summary",
            "forecast_effectiveness_summary",
            "portfolio_trajectory_summary",
            "stability_trajectory_summary",
        ),
    )
    assert payload["portfolio_trajectory_summary"]["baseline_only"] is True


def test_bug_recurrence_history_markdown_renders_maturity_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Maturity Assessment",
        required_substrings=(
            "### Dimension Scores",
            "### Dimension Levels",
            "### Capability Gaps",
            "### Improvement Priorities",
            "- Overall maturity score:",
            "- Overall maturity level:",
        ),
        summary_key="recurrence_maturity_summary",
    )


def test_bug_recurrence_history_payload_includes_maturity_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        required_keys=("recurrence_maturity", "recurrence_maturity_summary", "recurrence_maturity_gap_analysis"),
    )
    assert len(payload["recurrence_maturity_gap_analysis"]) == 6
    assert payload["recurrence_maturity"]["observability_maturity"]["maturity_score"] >= 0.0


def test_bug_recurrence_history_markdown_renders_roadmap_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Strategic Roadmap",
        required_substrings=(
            "### Priority Initiatives",
            "### Expected Maturity Lift",
            "### Dependency Sequence",
            "### Target State",
            "- Highest ROI initiative:",
            "- Largest gap dimension:",
        ),
        summary_key="recurrence_roadmap_summary",
    )


def test_bug_recurrence_history_payload_includes_roadmap_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        required_keys=("recurrence_roadmap", "recurrence_roadmap_summary", "recurrence_target_state"),
    )
    assert payload["recurrence_roadmap_summary"]["highest_roi_initiative"] == "data_volume_expansion"
    assert payload["recurrence_target_state"]["target_maturity_level"] == "optimized"


def test_bug_recurrence_history_markdown_renders_completion_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Program Completion",
        required_substrings=(
            "### Dimension Completion Status",
            "### Remaining Requirements",
            "### Completion Gaps",
            "### Graduation Status",
            "- Overall completion score:",
        ),
        summary_key="recurrence_completion_summary",
    )


def test_bug_recurrence_history_payload_includes_completion_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        required_keys=(
            "recurrence_completion",
            "recurrence_completion_summary",
            "recurrence_completion_gap_analysis",
        ),
    )
    assert payload["recurrence_completion_summary"]["program_graduated"] is False
    assert payload["recurrence_completion"]["observability_completion"]["completion_met"] is True


def test_bug_recurrence_history_markdown_renders_graduation_audit_section(tmp_path) -> None:
    markdown, payload = _write_vocative_recurrence_artifacts(tmp_path)

    assert_dashboard_recurrence_sections(
        markdown,
        payload,
        section="## Recurrence Graduation Audit",
        required_substrings=(
            "### Capability Coverage",
            "### Blind Spots",
            "### Redundancies",
            "### Graduation Readiness",
            "- Graduation readiness score:",
            "## Confidence Calibration Audit",
            "### Forecast Calibration",
            "### Governance Calibration",
            "### Effectiveness Calibration",
            "### Graduation Threshold Validation",
        ),
        summary_key="recurrence_graduation_audit_summary",
    )
    assert_recurrence_history_payload_shape(
        payload,
        required_keys=("recurrence_confidence_audit", "recurrence_confidence_calibration_summary"),
    )


def test_bug_recurrence_history_payload_includes_confidence_audit_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_dashboard_recurrence_payload(
        payload,
        required_keys=("recurrence_confidence_audit", "recurrence_confidence_calibration_summary"),
        summary_key="recurrence_confidence_calibration_summary",
        summary_schema_version=1,
    )
    assert "forecast_confidence_audit" in payload["recurrence_confidence_audit"]


def test_bug_recurrence_history_payload_includes_graduation_audit_fields(tmp_path) -> None:
    payload = _write_alpha_recurrence_payload(tmp_path)

    assert_recurrence_history_payload_shape(
        payload,
        required_keys=("recurrence_graduation_audit", "recurrence_graduation_audit_summary"),
    )
    assert payload["recurrence_graduation_audit_summary"]["program_graduated"] is False
    assert len(payload["recurrence_graduation_audit"]["blind_spots"]) >= 1


# Long-session operator metric lock: synthetic fixture encodes the full operator-readable summary contract.


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

    assert_long_session_operator_metrics(
        report,
        route_changes=0,
        speaker_changes=0,
        speaker_missing=0,
        continuity_classification="clean",
        fallback_total_count=1,
        fallback_lineage_kinds={"sealed_or_global_replacement": 1},
        mutation_turn_count=1,
        response_delta_checked=1,
        response_delta_failed=0,
        response_delta_repaired=0,
        response_delta_kinds={"new_fact": 1},
        response_delta_unknown_count=1,
        echo_overlap_bands={"low": 1},
        unavailable_counts={"fallback_family": 1},
        lineage_recurrence_present=True,
        absent_labels=("- Fallback frequency:", "- Mutation turns:"),
    )
