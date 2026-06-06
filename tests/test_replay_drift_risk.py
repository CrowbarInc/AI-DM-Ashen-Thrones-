from __future__ import annotations

from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import write_owner_drift_risk_artifacts
from tests.helpers.golden_replay import compare_golden_replay_reruns
from tests.helpers.replay_drift_risk import (
    build_risk_payload,
    build_risk_rankings,
    classify_field_source,
    render_owner_drift_risk_report,
    score_drift_risk,
)
from tests.helpers.replay_observed_row_fixtures import observed_failure_row


def _classification(
    *,
    field_path: str,
    owner_drift_bucket: str,
    investigate_first: str,
    category: str,
    severity: str = "high",
) -> dict:
    observed = observed_failure_row()
    rows = classify_replay_failure(
        scenario_id="risk_probe",
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
    row["severity"] = severity
    return row


def _route_scorecard() -> dict:
    return compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "B."}],
        [{"selected_speaker_id": "runner", "route_kind": "action", "final_text": "B."}],
    )


def _speaker_scorecard() -> dict:
    return compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "A."}],
        [{"selected_speaker_id": "guard", "route_kind": "dialogue", "final_text": "A."}],
    )


def test_score_drift_risk_high_protected_worsening_repeated() -> None:
    assert (
        score_drift_risk(
            field_source="protected",
            trend_direction="up",
            longitudinal_frequency=2,
        )
        == "high"
    )


def test_score_drift_risk_medium_protected_stable() -> None:
    assert (
        score_drift_risk(
            field_source="protected",
            trend_direction="stable",
            longitudinal_frequency=5,
        )
        == "medium"
    )


def test_score_drift_risk_medium_supporting_frequent() -> None:
    assert (
        score_drift_risk(
            field_source="supporting",
            trend_direction="stable",
            longitudinal_frequency=2,
        )
        == "medium"
    )


def test_score_drift_risk_low_advisory() -> None:
    assert (
        score_drift_risk(
            field_source="advisory",
            trend_direction="up",
            longitudinal_frequency=10,
        )
        == "low"
    )


def test_score_drift_risk_low_improving() -> None:
    assert (
        score_drift_risk(
            field_source="protected",
            trend_direction="down",
            longitudinal_frequency=3,
        )
        == "low"
    )


def test_classify_field_source_protected_route_kind() -> None:
    assert classify_field_source("route_kind") == "protected"


def test_build_risk_rankings_orders_high_before_low() -> None:
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
            field_path="final_text_hash",
            owner_drift_bucket="replay_drift_unclassified",
            investigate_first="tests/helpers/golden_replay.py",
            category="evaluator",
            severity="low",
        ),
    ]
    history = [_speaker_scorecard(), _route_scorecard()]
    rankings = build_risk_rankings(rows, scorecard_history=history)

    assert rankings["top_risk_fields"][0]["item"] == "route_kind"
    assert rankings["top_risk_fields"][0]["risk"] == "high"
    assert rankings["top_risk_fields"][-1]["item"] == "final_text_hash"
    assert rankings["top_risk_fields"][-1]["risk"] == "low"
    assert rankings["top_risk_owners"][0]["item"] == "route_drift"
    assert rankings["top_risk_investigation_targets"][0]["item"] == "game/interaction_context.py"
    assert rankings["recommended_investigation_order"][0]["risk"] == "high"


def test_render_owner_drift_risk_report() -> None:
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
    ]
    payload = build_risk_payload(rows, scorecard_history=[_speaker_scorecard(), _route_scorecard()])
    report = render_owner_drift_risk_report(payload, generated_at="2026-06-06T00:00:00Z")

    assert "# Owner Drift Risk Report" in report
    assert "- Advisory only: `true`" in report
    assert "## High Risk Drift" in report
    assert "## Medium Risk Drift" in report
    assert "## Low Risk Drift" in report
    assert "## Recommended Investigation Order" in report
    assert "| Rank | Item | Risk |" in report
    assert "`route_kind`" in report


def test_write_owner_drift_risk_artifacts(tmp_path) -> None:
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
    ]
    json_path = tmp_path / "owner_drift_risk.json"
    markdown_path = tmp_path / "owner_drift_risk.md"

    written_json, written_markdown = write_owner_drift_risk_artifacts(
        rows,
        scorecard_history=[_speaker_scorecard(), _route_scorecard()],
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-06-06T00:00:00Z",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload_text = json_path.read_text(encoding="utf-8")
    assert '"advisory_only": true' in payload_text
    assert '"top_risk_fields"' in payload_text
    assert '"recommended_investigation_order"' in payload_text
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Owner Drift Risk Report" in markdown
    assert "route_kind" in markdown
