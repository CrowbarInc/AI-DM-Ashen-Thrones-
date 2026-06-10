from __future__ import annotations

from tests.helpers.failure_dashboard_report import (
    write_owner_drift_longitudinal_artifacts,
    write_rerun_drift_scorecard_artifacts,
)
from tests.helpers.golden_replay_api import compare_golden_replay_reruns
from tests.helpers.replay_drift_taxonomy import route_drift_scorecard_fixture
from tests.helpers.replay_drift_longitudinal import (
    aggregate_owner_drift_history,
    build_owner_drift_trend_summary,
    render_owner_drift_longitudinal_report,
)


def _scorecard_with_speaker_drift() -> dict:
    return compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "A."}],
        [{"selected_speaker_id": "guard", "route_kind": "dialogue", "final_text": "A."}],
    )


def _scorecard_with_route_drift() -> dict:
    return route_drift_scorecard_fixture(scenario_id="longitudinal_route_scorecard")


def test_aggregate_owner_drift_history_empty() -> None:
    history = aggregate_owner_drift_history([])

    assert history["total_runs"] == 0
    assert history["total_owner_drift_events"] == 0
    assert history["most_common_bucket"] is None
    assert history["least_common_bucket"] is None
    assert sum(history["owner_bucket_counts"].values()) == 0
    assert all(value == 0.0 for value in history["owner_bucket_percentages"].values())


def test_aggregate_owner_drift_history_single_scorecard() -> None:
    scorecard = _scorecard_with_speaker_drift()
    history = aggregate_owner_drift_history([scorecard])

    assert history["total_runs"] == 1
    assert history["total_owner_drift_events"] == 1
    assert history["owner_bucket_counts"]["speaker_drift"] == 1
    assert history["owner_bucket_percentages"]["speaker_drift"] == 100.0
    assert history["most_common_bucket"] == "speaker_drift"
    assert history["least_common_bucket"] == "speaker_drift"
    assert scorecard["report_only"] is True


def test_aggregate_owner_drift_history_multiple_scorecards() -> None:
    history = aggregate_owner_drift_history(
        [
            _scorecard_with_speaker_drift(),
            _scorecard_with_route_drift(),
            _scorecard_with_speaker_drift(),
        ]
    )

    assert history["total_runs"] == 3
    assert history["total_owner_drift_events"] == 3
    assert history["owner_bucket_counts"]["speaker_drift"] == 2
    assert history["owner_bucket_counts"]["route_drift"] == 1
    assert history["owner_bucket_percentages"]["speaker_drift"] == 66.7
    assert history["owner_bucket_percentages"]["route_drift"] == 33.3
    assert history["most_common_bucket"] == "speaker_drift"
    assert history["least_common_bucket"] == "route_drift"


def test_build_owner_drift_trend_summary_ranking() -> None:
    history = aggregate_owner_drift_history(
        [
            _scorecard_with_speaker_drift(),
            _scorecard_with_route_drift(),
        ]
    )
    trend = build_owner_drift_trend_summary(history)

    assert len(trend) == 9
    assert trend[0]["bucket"] == "route_drift"
    assert trend[0]["rank"] == 1
    assert trend[0]["count"] == 1
    assert trend[1]["bucket"] == "speaker_drift"
    assert trend[1]["rank"] == 2
    zero_rows = [row for row in trend if row["count"] == 0]
    assert len(zero_rows) == 7
    assert all(row["percentage"] == 0.0 for row in zero_rows)


def test_render_owner_drift_longitudinal_report() -> None:
    history = aggregate_owner_drift_history(
        [
            _scorecard_with_speaker_drift(),
            _scorecard_with_route_drift(),
        ]
    )
    report = render_owner_drift_longitudinal_report(
        history,
        generated_at="2026-06-06T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert "# Owner Drift Longitudinal Report" in report
    assert "- Advisory only: `true`" in report
    assert "## Owner Drift Trend Summary" in report
    assert "| `speaker_drift` | `1` | 50%" in report
    assert "| `route_drift` | `1` | 50%" in report
    assert "## Highest Concentration" in report
    assert "## Lowest Concentration" in report


def test_render_owner_drift_longitudinal_report_empty_history() -> None:
    report = render_owner_drift_longitudinal_report(aggregate_owner_drift_history([]))
    assert "No owner drift history recorded." in report
    assert "No owner drift buckets recorded." in report


def test_write_owner_drift_longitudinal_artifacts(tmp_path) -> None:
    scorecards = [_scorecard_with_speaker_drift(), _scorecard_with_route_drift()]
    json_path = tmp_path / "owner_drift_longitudinal.json"
    markdown_path = tmp_path / "owner_drift_longitudinal.md"

    written_json, written_markdown = write_owner_drift_longitudinal_artifacts(
        scorecards,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-06T00:00:00Z",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload = json_path.read_text(encoding="utf-8")
    assert '"report_only": true' in payload
    assert '"advisory_only": true' in payload
    assert '"total_runs": 2' in payload
    assert '"trend_summary"' in payload
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Owner Drift Longitudinal Report" in markdown


def test_write_rerun_scorecard_artifacts_appends_longitudinal_summary(tmp_path) -> None:
    scorecard = _scorecard_with_speaker_drift()
    json_path = tmp_path / "rerun_drift_scorecard.json"
    markdown_path = tmp_path / "rerun_drift_scorecard.md"
    longitudinal_json = tmp_path / "owner_drift_longitudinal.json"
    longitudinal_md = tmp_path / "owner_drift_longitudinal.md"

    write_rerun_drift_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        longitudinal_json_path=longitudinal_json,
        longitudinal_markdown_path=longitudinal_md,
        generated_at="2026-06-06T00:00:00Z",
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Golden Rerun Drift Scorecard" in markdown
    assert "## Owner Drift Summary" in markdown
    assert "# Owner Drift Longitudinal Report" in markdown
    assert scorecard["report_only"] is True

    assert longitudinal_json.exists()
    assert longitudinal_md.exists()
    assert '"advisory_only": true' in longitudinal_json.read_text(encoding="utf-8")
