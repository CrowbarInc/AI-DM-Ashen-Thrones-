from __future__ import annotations

from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import write_owner_drift_risk_artifacts
from tests.helpers.golden_replay import compare_golden_replay_reruns
from tests.helpers.replay_drift_risk import (
    build_risk_payload,
    build_risk_rankings,
    classify_field_source,
    enrich_risk_payload_with_stability_ownership,
    render_owner_drift_risk_report,
    score_drift_risk,
)
from tests.helpers.golden_replay import build_long_session_stability_scorecard
from tests.helpers.replay_drift_taxonomy import (
    build_long_session_stability_history,
    build_stability_hotspots,
    render_stability_hotspots_markdown_lines,
    route_drift_classification_kwargs,
    route_drift_scorecard_fixture,
    stability_hotspot_rows,
    stability_trend_rows_from_history,
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
    return route_drift_scorecard_fixture(scenario_id="risk_route_scorecard")


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
            **route_drift_classification_kwargs(),
        ),
        _classification(
            **route_drift_classification_kwargs(),
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
            **route_drift_classification_kwargs(),
        ),
        _classification(
            **route_drift_classification_kwargs(),
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
            **route_drift_classification_kwargs(),
        ),
        _classification(
            **route_drift_classification_kwargs(),
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


def test_risk_payload_stability_enrichment_is_additive_only() -> None:
    rows = [
        _classification(
            **route_drift_classification_kwargs(),
        )
    ]
    base_payload = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        **build_risk_rankings(rows),
    }
    enriched = enrich_risk_payload_with_stability_ownership(base_payload, [])

    for key in (
        "total_signals",
        "risk_signals",
        "top_risk_fields",
        "top_risk_owners",
        "recommended_investigation_order",
    ):
        assert base_payload[key] == enriched[key]
    assert "stability_ownership" in enriched


def test_risk_payload_recurring_fallback_drift_increases_stability_risk() -> None:
    scorecards = [
        build_long_session_stability_scorecard(
            scenario_id=f"fallback_probe_{index}",
            observations=[
                {
                    "turn_index": 0,
                    "route_kind": "action",
                    "fallback_family": "gate_terminal_repair",
                    "runtime_lineage_events": [{"event_kind": "fallback_selected"}],
                }
            ],
        )
        for index in range(2)
    ]
    payload = build_risk_payload([], stability_scorecards=scorecards)
    stability = payload["stability_ownership"]
    assert stability["aggregation"]["bucket_frequencies"]["fallback_drift"] == 2
    signals = stability["stability_risk_signals"]
    assert any(signal["signal"] == "recurring_fallback_drift" for signal in signals)

    report = render_owner_drift_risk_report(payload)
    assert "## Stability Ownership" in report
    assert "recurring_fallback_drift" in report


def _stable_stability_scorecard(scenario_id: str) -> dict:
    return build_long_session_stability_scorecard(
        scenario_id=scenario_id,
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "dialogue", "selected_speaker_id": "runner"},
        ],
    )


def _route_drift_scorecard(scenario_id: str) -> dict:
    return build_long_session_stability_scorecard(
        scenario_id=scenario_id,
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "social", "selected_speaker_id": "runner"},
        ],
    )


def test_long_session_stability_history_aggregation() -> None:
    scorecards = [_stable_stability_scorecard("history_a"), _route_drift_scorecard("history_b")]
    history = build_long_session_stability_history(scorecards)

    assert history["sample_count"] == 2
    assert len(history["bucket_history"]) == 2
    assert len(history["status_history"]) == 2
    assert len(history["signal_history"]) == 2
    assert history["trend_summary"]["comparison_available"] is True
    assert history["trend_summary"]["bucket_trends"]["route_drift"]["current"] == 1
    assert history["trend_summary"]["bucket_trends"]["route_drift"]["previous"] == 0
    assert history == build_long_session_stability_history(scorecards)


def test_stability_trend_rows_worsening() -> None:
    history = build_long_session_stability_history(
        [_stable_stability_scorecard("prior"), _route_drift_scorecard("current")]
    )
    rows = stability_trend_rows_from_history(history)
    route_row = next(row for row in rows if row["owner_drift_bucket"] == "route_drift")
    assert route_row["trend"] == "worsening"
    assert route_row["delta"] == 1


def test_stability_trend_rows_improving() -> None:
    history = build_long_session_stability_history(
        [_route_drift_scorecard("prior"), _stable_stability_scorecard("current")]
    )
    rows = stability_trend_rows_from_history(history)
    route_row = next(row for row in rows if row["owner_drift_bucket"] == "route_drift")
    assert route_row["trend"] == "improving"
    assert route_row["delta"] == -1


def test_stability_trend_rows_stable() -> None:
    history = build_long_session_stability_history(
        [_stable_stability_scorecard("prior"), _stable_stability_scorecard("current")]
    )
    rows = stability_trend_rows_from_history(history)
    route_row = next(row for row in rows if row["owner_drift_bucket"] == "route_drift")
    assert route_row["trend"] == "stable"
    assert route_row["delta"] == 0
    overall_row = next(row for row in rows if row["owner_drift_bucket"] == "overall_stability")
    assert overall_row["trend"] == "stable"


def test_stability_history_risk_enrichment_is_additive_only() -> None:
    rows = [
        _classification(
            **route_drift_classification_kwargs(),
        )
    ]
    base_payload = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        **build_risk_rankings(rows),
    }
    scorecards = [_stable_stability_scorecard("prior"), _route_drift_scorecard("current")]
    enriched = enrich_risk_payload_with_stability_ownership(base_payload, scorecards)

    for key in (
        "total_signals",
        "risk_signals",
        "top_risk_fields",
        "top_risk_owners",
        "recommended_investigation_order",
    ):
        assert base_payload[key] == enriched[key]

    stability = enriched["stability_ownership"]
    assert "history" in stability
    assert "stability_trend_rows" in stability
    assert "stability_trend_signals" in stability
    assert any(signal["signal"] == "worsening_route_drift" for signal in stability["stability_trend_signals"])

    report = render_owner_drift_risk_report(enriched)
    assert "## Stability Trends" in report
    assert "`worsening`" in report


def test_build_stability_hotspots() -> None:
    scorecards = [
        _stable_stability_scorecard("stable_a"),
        _route_drift_scorecard("route_b"),
        _route_drift_scorecard("route_c"),
    ]
    hotspots = build_stability_hotspots(scorecards)

    assert hotspots["bucket_rankings"]
    assert hotspots["bucket_rankings"][0]["owner_drift_bucket"] == "route_drift"
    assert hotspots["bucket_rankings"][0]["occurrence_count"] == 2
    assert hotspots["bucket_rankings"][0]["affected_scenarios"] == 2
    assert hotspots["bucket_rankings"][0]["worsening_count"] == 1
    assert any(row["name"] == "route_change" for row in hotspots["signal_rankings"])
    assert len(hotspots["hotspot_rows"]) == 1
    assert hotspots["hotspot_rows"][0]["owner_drift_bucket"] == "route_drift"


def test_stability_hotspot_priority_ordering() -> None:
    assert stability_hotspot_rows(
        [
            {
                "rank": 1,
                "owner_drift_bucket": "route_drift",
                "occurrence_count": 3,
                "affected_scenarios": 2,
                "worsening_count": 1,
                "degraded_count": 0,
            }
        ]
    )[0]["priority"] == "critical"
    assert stability_hotspot_rows(
        [
            {
                "rank": 1,
                "owner_drift_bucket": "speaker_drift",
                "occurrence_count": 2,
                "affected_scenarios": 1,
                "worsening_count": 0,
                "degraded_count": 1,
            }
        ]
    )[0]["priority"] == "elevated"
    assert stability_hotspot_rows(
        [
            {
                "rank": 1,
                "owner_drift_bucket": "fallback_drift",
                "occurrence_count": 1,
                "affected_scenarios": 1,
                "worsening_count": 0,
                "degraded_count": 0,
            }
        ]
    )[0]["priority"] == "normal"


def test_stability_hotspot_rows_projection() -> None:
    history = build_long_session_stability_history(
        [_stable_stability_scorecard("prior"), _route_drift_scorecard("current")]
    )
    rows = stability_hotspot_rows(
        [
            {
                "rank": 1,
                "owner_drift_bucket": "route_drift",
                "occurrence_count": 1,
                "affected_scenarios": 1,
                "worsening_count": 1,
                "degraded_count": 0,
            }
        ],
        history=history,
    )
    assert rows == [
        {
            "rank": 1,
            "owner_drift_bucket": "route_drift",
            "occurrence_count": 1,
            "scenario_count": 1,
            "worsening_count": 1,
            "degraded_count": 0,
            "trend": "worsening",
            "priority": "elevated",
        }
    ]


def test_stability_hotspot_reporting_empty() -> None:
    lines = render_stability_hotspots_markdown_lines([])
    markdown = "\n".join(lines)
    assert "## Stability Hotspots" in markdown
    assert "No stability hotspots identified." in markdown


def test_stability_hotspot_risk_integration_is_additive() -> None:
    rows = [
        _classification(
            **route_drift_classification_kwargs(),
        )
    ]
    base_payload = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        **build_risk_rankings(rows),
    }
    scorecards = [_stable_stability_scorecard("prior"), _route_drift_scorecard("current")]
    enriched = enrich_risk_payload_with_stability_ownership(base_payload, scorecards)

    for key in (
        "total_signals",
        "risk_signals",
        "top_risk_fields",
        "top_risk_owners",
        "recommended_investigation_order",
    ):
        assert base_payload[key] == enriched[key]

    stability = enriched["stability_ownership"]
    assert "stability_hotspots" in stability
    assert stability["stability_hotspots"]["hotspot_rows"]

    report = render_owner_drift_risk_report(enriched)
    assert "## Stability Hotspots" in report
    assert "`route_drift`" in report
