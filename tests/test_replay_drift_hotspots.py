from __future__ import annotations

from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import write_owner_drift_hotspot_artifacts
from tests.helpers.golden_replay import compare_golden_replay_reruns
from tests.helpers.replay_drift_hotspots import (
    aggregate_field_drift_counts,
    aggregate_investigation_target_counts,
    aggregate_owner_bucket_by_field,
    build_hotspot_rankings,
    classification_rows_from_scorecards,
    render_owner_drift_hotspot_report,
)
from tests.helpers.replay_drift_trends import enrich_hotspots_with_field_trends
from tests.helpers.replay_observed_row_fixtures import observed_failure_row


def _classification(
    *,
    field_path: str,
    owner_drift_bucket: str,
    investigate_first: str,
    category: str,
) -> dict:
    observed = observed_failure_row()
    rows = classify_replay_failure(
        scenario_id="hotspot_probe",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": field_path,
                "expected": "a",
                "actual": "b",
                "reason": "probe",
                "drift_bucket": "structural_drift",
                "replay_tags": ["structural_drift"],
            }
        ],
    )
    row = dict(rows[0])
    row["owner_drift_bucket"] = owner_drift_bucket
    row["investigate_first"] = investigate_first
    row["category"] = category
    return row


def test_aggregate_field_drift_counts_empty() -> None:
    assert aggregate_field_drift_counts([]) == {}
    assert build_hotspot_rankings([])["total_classifications"] == 0


def test_aggregate_field_drift_counts_and_investigation_targets() -> None:
    rows = [
        _classification(
            field_path="route_kind",
            owner_drift_bucket="route_drift",
            investigate_first="game/interaction_context.py",
            category="route",
        ),
        _classification(
            field_path="route_kind",
            owner_drift_bucket="route_drift",
            investigate_first="game/interaction_context.py",
            category="route",
        ),
        _classification(
            field_path="selected_speaker_id",
            owner_drift_bucket="speaker_drift",
            investigate_first="game/speaker_contract_enforcement.py",
            category="speaker",
        ),
    ]

    assert aggregate_field_drift_counts(rows) == {
        "route_kind": 2,
        "selected_speaker_id": 1,
    }
    assert aggregate_investigation_target_counts(rows) == {
        "game/interaction_context.py": 2,
        "game/speaker_contract_enforcement.py": 1,
    }


def test_aggregate_owner_bucket_by_field() -> None:
    rows = [
        _classification(
            field_path="route_kind",
            owner_drift_bucket="route_drift",
            investigate_first="game/interaction_context.py",
            category="route",
        ),
        _classification(
            field_path="selected_speaker_id",
            owner_drift_bucket="speaker_drift",
            investigate_first="game/speaker_contract_enforcement.py",
            category="speaker",
        ),
    ]
    pairs = aggregate_owner_bucket_by_field(rows)
    assert pairs == [
        {"field": "route_kind", "owner_drift_bucket": "route_drift", "count": 1},
        {"field": "selected_speaker_id", "owner_drift_bucket": "speaker_drift", "count": 1},
    ]


def test_build_hotspot_rankings_orders_by_count_with_tie_break() -> None:
    rows = [
        _classification(
            field_path="route_kind",
            owner_drift_bucket="route_drift",
            investigate_first="game/interaction_context.py",
            category="route",
        ),
        _classification(
            field_path="fallback_family",
            owner_drift_bucket="fallback_drift",
            investigate_first="game/final_emission_gate.py",
            category="fallback",
        ),
        _classification(
            field_path="selected_speaker_id",
            owner_drift_bucket="speaker_drift",
            investigate_first="game/speaker_contract_enforcement.py",
            category="speaker",
        ),
        _classification(
            field_path="selected_speaker_id",
            owner_drift_bucket="speaker_drift",
            investigate_first="game/speaker_contract_enforcement.py",
            category="speaker",
        ),
    ]
    hotspots = build_hotspot_rankings(rows)

    assert hotspots["top_drift_fields"][0] == {"name": "selected_speaker_id", "count": 2, "rank": 1}
    assert hotspots["top_drift_fields"][1]["name"] == "fallback_family"
    assert hotspots["top_drift_fields"][2]["name"] == "route_kind"
    assert hotspots["top_owner_drift_buckets"][0]["name"] == "speaker_drift"
    assert hotspots["top_investigation_targets"][0]["name"] == "game/speaker_contract_enforcement.py"


def test_render_owner_drift_hotspot_report() -> None:
    rows = [
        _classification(
            field_path="route_kind",
            owner_drift_bucket="route_drift",
            investigate_first="game/interaction_context.py",
            category="route",
        ),
        _classification(
            field_path="selected_speaker_id",
            owner_drift_bucket="speaker_drift",
            investigate_first="game/speaker_contract_enforcement.py",
            category="speaker",
        ),
    ]
    report = render_owner_drift_hotspot_report(
        build_hotspot_rankings(rows),
        generated_at="2026-06-06T00:00:00Z",
    )

    assert "# Owner Drift Hotspot Report" in report
    assert "- Advisory only: `true`" in report
    assert "## Top Drift Fields" in report
    assert "1. route_kind (1)" in report or "1. selected_speaker_id (1)" in report
    assert "## Top Investigation Targets" in report
    assert "## Top Owner Drift Buckets" in report
    assert "## Owner Drift Buckets By Field" in report
    assert "| `route_kind` | `route_drift` | `1` |" in report


def test_render_owner_drift_hotspot_report_shows_field_trends() -> None:
    history = [
        compare_golden_replay_reruns(
            [{"selected_speaker_id": "runner", "final_text": "A."}],
            [{"selected_speaker_id": "guard", "final_text": "A."}],
        ),
        compare_golden_replay_reruns(
            [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "B."}],
            [{"selected_speaker_id": "runner", "route_kind": "action", "final_text": "B."}],
        ),
    ]
    rows = classification_rows_from_scorecards(history)
    hotspots = enrich_hotspots_with_field_trends(build_hotspot_rankings(rows), history)
    report = render_owner_drift_hotspot_report(hotspots)

    assert "Trend: down" in report or "Trend: stable" in report or "Trend: up" in report
    assert "Count:" in report


def test_render_owner_drift_hotspot_report_empty() -> None:
    report = render_owner_drift_hotspot_report(build_hotspot_rankings([]))
    assert "No drift fields recorded." in report
    assert "No investigation targets recorded." in report


def test_write_owner_drift_hotspot_artifacts(tmp_path) -> None:
    rows = [
        _classification(
            field_path="route_kind",
            owner_drift_bucket="route_drift",
            investigate_first="game/interaction_context.py",
            category="route",
        ),
    ]
    json_path = tmp_path / "owner_drift_hotspots.json"
    markdown_path = tmp_path / "owner_drift_hotspots.md"

    written_json, written_markdown = write_owner_drift_hotspot_artifacts(
        rows,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-06T00:00:00Z",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload_text = json_path.read_text(encoding="utf-8")
    assert '"advisory_only": true' in payload_text
    assert '"field_counts"' in payload_text
    assert '"route_kind": 1' in payload_text or '"route_kind": 1' in payload_text
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Owner Drift Hotspot Report" in markdown
    assert "route_kind" in markdown
