from __future__ import annotations

import json

from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_dashboard_report import (
    clear_recorded_failure_dashboard_rows,
    clear_recorded_protected_replay_failures,
    clear_recorded_rerun_drift_scorecards,
    recorded_protected_replay_failure_rows,
    recorded_runtime_lineage_events,
    record_rerun_drift_scorecard,
    recorded_rerun_drift_scorecards,
    render_bug_recurrence_history_markdown,
    render_rerun_drift_scorecard_markdown,
    write_bug_recurrence_history_artifacts,
    write_protected_replay_failure_report_if_present,
    write_rerun_drift_scorecard_artifacts,
    write_rerun_drift_scorecard_artifacts_if_requested,
)
from tests.helpers.golden_replay_api import classify_golden_drift, compare_golden_replay_reruns
from tests.helpers.failure_dashboard_fixtures import record_selected_speaker_protected_failure
from tests.helpers.replay_observed_row_fixtures import protected_speaker_failure_turn, synthetic_rerun_turn


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


def test_bug_recurrence_history_writer_creates_report_only_json_and_markdown(tmp_path) -> None:
    json_path = tmp_path / "bug_recurrence_history.json"
    markdown_path = tmp_path / "bug_recurrence_history.md"

    written_json, written_markdown = write_bug_recurrence_history_artifacts(
        [
            _recurrence_classification_row(scenario_id="b"),
            _recurrence_classification_row(scenario_id="a"),
        ],
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-10T00:00:00Z",
        command_used="pytest recurrence",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["report_only"] is True
    assert payload["advisory_only"] is True
    assert payload["total_rows"] == 2
    assert payload["unique_recurrence_count"] == 1
    assert {row["status"] for row in payload["summary"]} <= {"active", "watch", "retired"}
    assert payload["summary"][0]["affected_scenarios"] == ["a", "b"]

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Bug-Class Recurrence History" in markdown
    assert "- Report only: `true`" in markdown
    assert "- Advisory only: `true`" in markdown
    assert "| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |" in markdown
    assert "| recurrence:v1:speaker_drift" in markdown
    assert " | active | " in markdown
    assert "selected_speaker_id" in markdown
    assert "game/speaker_contract_enforcement.py" in markdown


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
    assert "No recurrence history recorded." in report
