from __future__ import annotations

from tests.helpers.failure_dashboard_report import write_owner_drift_trend_artifacts
from tests.helpers.golden_replay import compare_golden_replay_reruns
from tests.helpers.replay_drift_hotspots import build_hotspot_rankings, classification_rows_from_scorecards
from tests.helpers.replay_drift_trends import (
    build_owner_bucket_trend_summary,
    build_trend_payload,
    compute_owner_drift_trends,
    enrich_hotspots_with_field_trends,
    render_owner_drift_trend_report,
)
from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS, route_drift_scorecard_fixture


def _speaker_scorecard() -> dict:
    return compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "A."}],
        [{"selected_speaker_id": "guard", "route_kind": "dialogue", "final_text": "A."}],
    )


def _route_scorecard() -> dict:
    return route_drift_scorecard_fixture(scenario_id="trend_route_scorecard")


def test_compute_owner_drift_trends_empty_history() -> None:
    trends = compute_owner_drift_trends([])
    assert len(trends) == len(ALLOWED_OWNER_DRIFT_BUCKETS)
    assert all(entry["direction"] == "stable" for entry in trends.values())
    assert all(entry["delta"] == 0 for entry in trends.values())


def test_compute_owner_drift_trends_increasing() -> None:
    history = [_speaker_scorecard(), _speaker_scorecard(), _route_scorecard()]
    trends = compute_owner_drift_trends(history)

    assert trends["speaker_drift"]["previous"] == 1
    assert trends["speaker_drift"]["current"] == 0
    assert trends["speaker_drift"]["delta"] == -1
    assert trends["speaker_drift"]["direction"] == "down"
    assert trends["route_drift"]["previous"] == 0
    assert trends["route_drift"]["current"] == 1
    assert trends["route_drift"]["delta"] == 1
    assert trends["route_drift"]["direction"] == "up"


def test_compute_owner_drift_trends_stable_single_run() -> None:
    trends = compute_owner_drift_trends([_speaker_scorecard()])
    assert trends["speaker_drift"]["current"] == 1
    assert trends["speaker_drift"]["previous"] == 0
    assert trends["speaker_drift"]["direction"] == "up"


def test_build_owner_bucket_trend_summary_covers_all_buckets() -> None:
    summary = build_owner_bucket_trend_summary(compute_owner_drift_trends([_route_scorecard()]))
    assert len(summary) == len(ALLOWED_OWNER_DRIFT_BUCKETS)
    route_row = next(row for row in summary if row["bucket"] == "route_drift")
    assert route_row["current"] == 1
    assert route_row["direction"] == "up"
    assert route_row["delta_label"] == "+1"


def test_render_owner_drift_trend_report() -> None:
    history = [_speaker_scorecard(), _route_scorecard()]
    trends = compute_owner_drift_trends(history)
    report = render_owner_drift_trend_report(trends, generated_at="2026-06-06T00:00:00Z")

    assert "# Owner Drift Trend Report" in report
    assert "## Drift Trend Summary" in report
    assert "| Bucket | Previous | Current | Delta | Direction |" in report
    assert "## Improving Areas" in report
    assert "## Worsening Areas" in report
    assert "## Stable Areas" in report
    assert "`route_drift`" in report


def test_enrich_hotspots_with_field_trends() -> None:
    from tests.helpers.replay_drift_hotspots import classification_rows_from_scorecards

    history = [_speaker_scorecard(), _route_scorecard()]
    hotspots = enrich_hotspots_with_field_trends(
        build_hotspot_rankings(classification_rows_from_scorecards(history)),
        history,
    )
    speaker_row = next(
        row for row in hotspots["top_drift_fields"] if row["name"] == "selected_speaker_id"
    )
    assert speaker_row["trend_direction"] == "down"
    assert speaker_row["current_count"] == 1


def test_write_owner_drift_trend_artifacts(tmp_path) -> None:
    history = [_speaker_scorecard(), _route_scorecard()]
    json_path = tmp_path / "owner_drift_trends.json"
    markdown_path = tmp_path / "owner_drift_trends.md"

    written_json, written_markdown = write_owner_drift_trend_artifacts(
        history,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-06T00:00:00Z",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload_text = json_path.read_text(encoding="utf-8")
    assert '"advisory_only": true' in payload_text
    assert '"owner_drift_trends"' in payload_text
    assert '"field_drift_trends"' in payload_text
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Owner Drift Trend Report" in markdown
    assert build_trend_payload(history)["scorecard_runs_compared"] == 2
