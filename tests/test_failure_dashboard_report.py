from __future__ import annotations

import json

from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import (
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
        assert "# Protected Replay Failure Report" in report
        assert "synthetic_protected_bridge" in report
        assert "selected_speaker_id: exact value mismatch" in report
        assert "## Failure Locator" in report
        assert "| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |" in report
        assert "data/validation/scenario_spines/synthetic_fixture.json" in report
        assert "synthetic_branch" in report
        assert "synthetic_turn_01" in report
        assert "structural_drift" in report
        assert "game/speaker_contract_enforcement.py" in report
        assert "speaker_drift" in report
        assert "## Owner Drift Breakdown" in report
        assert "| Owner Drift Bucket |" in report
        assert "## Sanitizer Summary" in report
        assert "## Runtime Lineage Summary" in report
        assert "### Focused failing tests" in report
        assert "### Protected replay lane" in report
        assert "python -m pytest -m golden_replay -q --tb=short" in report
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
        assert "## Failure Locator" in report
        assert (
            "| synthetic_inline_bridge | none | none | 0 | none | selected_speaker_id: exact value mismatch |"
            in report
        )
        assert "python -m pytest -m golden_replay -q --tb=short" in report
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


def test_rerun_drift_scorecard_markdown_summarizes_fabricated_scorecard() -> None:
    scorecard = _synthetic_rerun_scorecard()

    markdown = render_rerun_drift_scorecard_markdown(
        scorecard,
        generated_at="2026-05-30T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert "# Golden Rerun Drift Scorecard" in markdown
    assert "- Total turns compared: `1`" in markdown
    assert "- Speaker deltas: `1`" in markdown
    assert "- Route deltas: `1`" in markdown
    assert "- Fallback deltas: `1`" in markdown
    assert "- Text fingerprint deltas: `1`" in markdown
    assert "- Runtime-lineage deltas: `1`" in markdown
    assert "## Owner Drift Summary" in markdown
    assert "| `speaker_drift` |" in markdown
    assert "## Semantic Delta Frequency" in markdown
    assert "- Semantic delta frequency deltas: `0`" in markdown
    assert "| Turn | Previous Turn ID | Current Turn ID | Drift Fields | Details |" in markdown
    assert "text_hash" in markdown


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
    assert "Golden Rerun Drift Scorecard" in markdown
    assert "Speaker deltas: `1`" in markdown


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
    assert "| Owner Drift Bucket |" in report
    assert "speaker_drift" in report
    assert "## Owner Drift Breakdown" in report


def test_render_rerun_scorecard_includes_owner_drift_summary() -> None:
    scorecard = compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "A."}],
        [{"selected_speaker_id": "guard", "route_kind": "dialogue", "final_text": "A."}],
    )
    markdown = render_rerun_drift_scorecard_markdown(scorecard, generated_at="2026-06-06T00:00:00Z")
    assert "## Owner Drift Summary" in markdown
    assert "| `speaker_drift` | `1` |" in markdown
    assert scorecard["report_only"] is True


def test_render_rerun_scorecard_empty_owner_drift_summary() -> None:
    scorecard = compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "final_text": "Stable."}],
        [{"selected_speaker_id": "runner", "final_text": "Stable."}],
    )
    markdown = render_rerun_drift_scorecard_markdown(scorecard)
    assert "## Owner Drift Summary" in markdown
    assert "No owner drift classifications." in markdown


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
    assert payload["persistence_population"] == "protected_replay_history"
    assert payload["total_rows"] == 0
    assert payload["unique_recurrence_count"] == 0
    assert payload["summary"] == []

    protected_log = json.loads(event_log_path.read_text(encoding="utf-8"))
    session_log = json.loads(session_log_path.read_text(encoding="utf-8"))
    assert protected_log["events"] == []
    assert len(session_log["events"]) == 2
    assert session_log["events"][0]["event_source"] == "session"
    assert session_log["events"][0]["command"] == "pytest recurrence"

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Bug-Class Recurrence History" in markdown
    assert "No recurrence history recorded." in markdown


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
    assert payload["total_rows"] == 2
    assert payload["unique_recurrence_count"] == 1
    assert payload["summary"][0]["occurrence_count"] == 2
    assert payload["summary"][0]["status"] == "active"
    assert payload["protected_replay_regression_recurrence_rate"]["numerator"] == 1
    assert payload["protected_replay_regression_recurrence_rate"]["rate"] == 1.0

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Regression Recurrence Rate: 100.0% (1 / 1 recurrence keys active by repeated observation)." in markdown
    assert " | active | " in markdown

    event_log = json.loads(event_log_path.read_text(encoding="utf-8"))
    assert len(event_log["events"]) == 2
    assert event_log["events"][0]["event_source"] == "protected_replay_failure"
    assert event_log["events"][0]["artifact_source"] == "artifacts/golden_replay/replay_failure_report.md"


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
    assert first_payload["total_rows"] == 1
    assert first_payload["summary"][0]["occurrence_count"] == 1
    assert first_payload["summary"][0]["status"] == "watch"

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
    assert second_payload["total_rows"] == 2
    assert second_payload["summary"][0]["occurrence_count"] == 2
    assert second_payload["summary"][0]["status"] == "active"


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
    assert payload["total_rows"] == 1
    assert payload["unique_recurrence_count"] == 1
    assert "No recurrence history recorded." not in markdown
    assert "selected_speaker_id" in markdown


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
    assert event["event_source"] == "protected_replay_failure"
    assert event["test_node_id"] == "tests/test_golden_replay.py::test_protected_failure"
    assert event["artifact_source"] == str(tmp_path / "replay_failure_report.md")


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
    assert events[0]["recorded_at"] == "2026-06-10T00:00:00Z"


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
    assert " | watch | " in markdown
    assert " | retired | " in markdown


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

    assert "# Bug-Class Recurrence History" in report
    assert "- Total recurrence keys: `0`" in report
    assert "- Total recurrence events: `0`" in report
    assert "## Regression Recurrence Rate" in report
    assert "Regression Recurrence Rate: 0.0% (0 / 0 recurrence keys active by repeated observation)." in report
    assert "does not gate protected replay." in report
    assert "No recurrence history recorded." in report


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

    assert "## Regression Recurrence Rate" in report
    assert "Regression Recurrence Rate: 50.0% (1 / 2 recurrence keys active by repeated observation)." in report
    assert "- Report only: `true`" in report
    assert "- Advisory only: `true`" in report


def test_bug_recurrence_history_markdown_renders_recurrence_trends_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Trends" in markdown
    assert "- Emerging keys: `1`" in markdown
    assert "- Recurring keys: `0`" in markdown
    assert "- Persistent keys: `0`" in markdown
    assert "- Dormant keys: `0`" in markdown
    assert "### Newest Recurrence Keys" in markdown
    assert payload["recurrence_trends"]["protected_replay_only"] is True
    assert payload["recurrence_timeline"][0]["occurrence_count"] == 1
    assert payload["recurrence_timeline"][0]["trend_classification"] == "emerging"


def test_bug_recurrence_history_payload_backward_compatible_core_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["report_only"] is True
    assert payload["unique_recurrence_count"] == 1
    assert payload["regression_recurrence_rate"]["metric"] == "regression_recurrence_rate"
    assert "recurrence_trends" in payload
    assert "recurrence_timeline" in payload


def test_bug_recurrence_history_markdown_renders_recurrence_forecast_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Forecast" in markdown
    assert "- Watch keys: `1`" in markdown
    assert "- Forecast confidence: `low`" in markdown
    assert "- Stability score: `100.0` / 100" in markdown
    assert "### Concentration Metrics" in markdown
    assert payload["recurrence_forecast"]["forecast_summary"]["watch_keys"] == 1
    assert payload["recurrence_forecast"]["risk_concentration"]["top_key_share"] == 1.0


def test_bug_recurrence_history_payload_includes_forecast_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["recurrence_forecast"]["forecast_summary"]["schema_version"] == 1
    assert payload["recurrence_forecast"]["forecast_summary"]["protected_replay_only"] is True
    assert "key_forecasts" in payload["recurrence_forecast"]


def test_bug_recurrence_history_markdown_renders_recurrence_portfolio_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Portfolio" in markdown
    assert "### Top Owners" in markdown
    assert "### Top Categories" in markdown
    assert "### Top Field Paths" in markdown
    assert "### Top Scenarios" in markdown
    assert "- Portfolio risk score:" in markdown
    assert payload["recurrence_portfolio_summary"]["protected_replay_only"] is True
    assert payload["recurrence_portfolio"]["owners"][0]["owner"] == "speaker"


def test_bug_recurrence_history_payload_includes_portfolio_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["unique_recurrence_count"] == 1
    assert "recurrence_portfolio" in payload
    assert "recurrence_portfolio_summary" in payload
    assert payload["recurrence_portfolio_summary"]["schema_version"] == 1


def test_bug_recurrence_history_markdown_renders_remediation_targets_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"
    event_log_path = tmp_path / "bug_recurrence_event_log.json"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        event_log_path=event_log_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Remediation Targets" in markdown
    assert "### Top Keys" in markdown
    assert "### Top Owners" in markdown
    assert "- Estimated portfolio reduction:" in markdown
    assert "- Remediation confidence:" in markdown
    assert payload["recurrence_remediation_summary"]["protected_replay_only"] is True
    assert len(payload["recurrence_remediation_targets"]["keys"]) == 1


def test_bug_recurrence_history_payload_includes_remediation_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_remediation_targets" in payload
    assert "recurrence_remediation_summary" in payload
    assert payload["unique_recurrence_count"] == 1
    assert "reduction_potential" in payload["recurrence_remediation_targets"]["keys"][0]


def test_bug_recurrence_history_markdown_renders_roi_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence ROI" in markdown
    assert "### Top ROI Targets" in markdown
    assert "### Top ROI Owners" in markdown
    assert "- Portfolio ROI score:" in markdown
    assert "- Projected stability gain:" in markdown
    assert "- Projected risk reduction:" in markdown
    assert "- ROI confidence:" in markdown
    assert payload["recurrence_roi_summary"]["protected_replay_only"] is True
    assert "roi_score" in payload["recurrence_roi"]["keys"][0]


def test_bug_recurrence_history_payload_includes_roi_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_roi" in payload
    assert "recurrence_roi_summary" in payload
    assert payload["recurrence_roi_summary"]["schema_version"] == 1
    assert payload["recurrence_roi"]["keys"][0]["roi_rank"] == 1


def test_bug_recurrence_history_markdown_renders_governance_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Governance" in markdown
    assert "### Watchlist" in markdown
    assert "### Prioritized Targets" in markdown
    assert "### Retire Candidates" in markdown
    assert "### Owner Accountability" in markdown
    assert "- Governance health score:" in markdown
    assert "- Watchlist size:" in markdown
    assert payload["recurrence_governance_summary"]["protected_replay_only"] is True
    assert len(payload["recurrence_watchlist"]) == 1


def test_bug_recurrence_history_payload_includes_governance_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_governance" in payload
    assert "recurrence_watchlist" in payload
    assert "recurrence_governance_summary" in payload
    assert "recurrence_retirement_summary" in payload
    assert payload["recurrence_watchlist"][0]["governance_status"] == "watch"


def test_bug_recurrence_history_markdown_renders_lifecycle_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Lifecycle" in markdown
    assert "### Lifecycle Distribution" in markdown
    assert "### Age Distribution" in markdown
    assert "### Transition Summary" in markdown
    assert "### Closure Effectiveness" in markdown
    assert "- Lifecycle health score:" in markdown
    assert "- Closure rate:" in markdown
    assert payload["recurrence_lifecycle_summary"]["protected_replay_only"] is True


def test_bug_recurrence_history_payload_includes_lifecycle_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_lifecycle" in payload
    assert "recurrence_lifecycle_summary" in payload
    assert "recurrence_age_distribution" in payload
    assert "recurrence_transition_summary" in payload
    assert "recurrence_closure_effectiveness" in payload
    assert payload["recurrence_lifecycle"]["keys"][0]["lifecycle_stage"] == "emerging"


def test_bug_recurrence_history_markdown_renders_program_effectiveness_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Program Effectiveness" in markdown
    assert "### Governance Effectiveness" in markdown
    assert "### Remediation Effectiveness" in markdown
    assert "### Forecast Effectiveness" in markdown
    assert "### Portfolio Trajectory" in markdown
    assert "- Program effectiveness score:" in markdown
    assert "- Effectiveness confidence:" in markdown
    assert payload["recurrence_program_effectiveness_summary"]["protected_replay_only"] is True


def test_bug_recurrence_history_payload_includes_program_effectiveness_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_program_effectiveness" in payload
    assert "recurrence_program_effectiveness_summary" in payload
    assert "governance_effectiveness_summary" in payload
    assert "remediation_effectiveness_summary" in payload
    assert "forecast_effectiveness_summary" in payload
    assert "portfolio_trajectory_summary" in payload
    assert "stability_trajectory_summary" in payload
    assert payload["portfolio_trajectory_summary"]["baseline_only"] is True


def test_bug_recurrence_history_markdown_renders_maturity_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Maturity Assessment" in markdown
    assert "### Dimension Scores" in markdown
    assert "### Dimension Levels" in markdown
    assert "### Capability Gaps" in markdown
    assert "### Improvement Priorities" in markdown
    assert "- Overall maturity score:" in markdown
    assert "- Overall maturity level:" in markdown
    assert payload["recurrence_maturity_summary"]["protected_replay_only"] is True


def test_bug_recurrence_history_payload_includes_maturity_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_maturity" in payload
    assert "recurrence_maturity_summary" in payload
    assert "recurrence_maturity_gap_analysis" in payload
    assert len(payload["recurrence_maturity_gap_analysis"]) == 6
    assert payload["recurrence_maturity"]["observability_maturity"]["maturity_score"] >= 0.0


def test_bug_recurrence_history_markdown_renders_roadmap_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Strategic Roadmap" in markdown
    assert "### Priority Initiatives" in markdown
    assert "### Expected Maturity Lift" in markdown
    assert "### Dependency Sequence" in markdown
    assert "### Target State" in markdown
    assert "- Highest ROI initiative:" in markdown
    assert "- Largest gap dimension:" in markdown
    assert payload["recurrence_roadmap_summary"]["protected_replay_only"] is True


def test_bug_recurrence_history_payload_includes_roadmap_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_roadmap" in payload
    assert "recurrence_roadmap_summary" in payload
    assert "recurrence_target_state" in payload
    assert payload["recurrence_roadmap_summary"]["highest_roi_initiative"] == "data_volume_expansion"
    assert payload["recurrence_target_state"]["target_maturity_level"] == "optimized"


def test_bug_recurrence_history_markdown_renders_completion_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Program Completion" in markdown
    assert "### Dimension Completion Status" in markdown
    assert "### Remaining Requirements" in markdown
    assert "### Completion Gaps" in markdown
    assert "### Graduation Status" in markdown
    assert "- Overall completion score:" in markdown
    assert payload["recurrence_completion_summary"]["protected_replay_only"] is True


def test_bug_recurrence_history_payload_includes_completion_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_completion" in payload
    assert "recurrence_completion_summary" in payload
    assert "recurrence_completion_gap_analysis" in payload
    assert payload["recurrence_completion_summary"]["program_graduated"] is False
    assert payload["recurrence_completion"]["observability_completion"]["completion_met"] is True


def test_bug_recurrence_history_markdown_renders_graduation_audit_section(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="vocative_probe")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(
            generated_at="2026-06-04T22:31:59Z",
        ),
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "## Recurrence Graduation Audit" in markdown
    assert "### Capability Coverage" in markdown
    assert "### Blind Spots" in markdown
    assert "### Redundancies" in markdown
    assert "### Graduation Readiness" in markdown
    assert "- Graduation readiness score:" in markdown
    assert payload["recurrence_graduation_audit_summary"]["protected_replay_only"] is True
    assert "## Confidence Calibration Audit" in markdown
    assert "### Forecast Calibration" in markdown
    assert "### Governance Calibration" in markdown
    assert "### Effectiveness Calibration" in markdown
    assert "### Graduation Threshold Validation" in markdown
    assert "recurrence_confidence_audit" in payload
    assert "recurrence_confidence_calibration_summary" in payload


def test_bug_recurrence_history_payload_includes_confidence_audit_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_confidence_audit" in payload
    assert "recurrence_confidence_calibration_summary" in payload
    assert payload["recurrence_confidence_calibration_summary"]["schema_version"] == 1
    assert "forecast_confidence_audit" in payload["recurrence_confidence_audit"]


def test_bug_recurrence_history_payload_includes_graduation_audit_fields(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    write_bug_recurrence_history_artifacts(
        [_recurrence_classification_row(scenario_id="alpha")],
        json_path=json_path,
        markdown_path=markdown_path,
        recurrence_event_metadata=_golden_protected_recurrence_metadata(),
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "recurrence_graduation_audit" in payload
    assert "recurrence_graduation_audit_summary" in payload
    assert payload["recurrence_graduation_audit_summary"]["program_graduated"] is False
    assert len(payload["recurrence_graduation_audit"]["blind_spots"]) >= 1


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
