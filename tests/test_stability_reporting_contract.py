from __future__ import annotations

import pytest

from tests.helpers.failure_dashboard_report import render_long_session_stability_scorecard_markdown
from tests.helpers.golden_replay import FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
from tests.helpers.golden_replay_api import (
    build_long_session_stability_scorecard,
    summarize_long_session_replay_observations,
)
from tests.helpers.replay_observed_row_fixtures import synthetic_rerun_turn
from tests.helpers.replay_drift_reports import (
    build_long_session_stability_history,
    build_risk_payload,
    build_stability_hotspots,
    stability_classification_rows_from_scorecard,
)
from tests.helpers.replay_drift_risk import enrich_risk_payload_with_stability_ownership
from tests.helpers.replay_drift_taxonomy import (
    stability_trend_rows_from_history,
)
from tests.stability_reporting_contract import (
    ALLOWED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
    ALLOWED_STABILITY_HOTSPOT_ROW_FIELDS,
    ALLOWED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
    ALLOWED_STABILITY_TREND_ROW_FIELDS,
    REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
    REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS,
    REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
    REQUIRED_STABILITY_TREND_ROW_FIELDS,
    STABILITY_REPORTING_OWNERSHIP,
    stability_reporting_field_registries,
    stability_reporting_governance_manifest,
)
from tests.helpers.stability_reporting_sync import (
    assert_stability_hotspot_contract_locked,
    assert_stability_ownership_contract_locked,
    assert_stability_reporting_boundary_documented,
    assert_stability_scorecard_contract_locked,
    assert_stability_trend_contract_locked,
    stability_hotspot_row_contract_misalignments,
    stability_scorecard_contract_misalignments,
    stability_trend_row_contract_misalignments,
    validate_stability_hotspot_row,
    validate_stability_ownership_classification_row,
    validate_stability_scorecard,
    validate_stability_trend_row,
)

# Ownership note:
# This file owns the AT stability reporting schema and governance contract.
# Projection and enrichment behavior remain owned by taxonomy/risk helpers.


def _stable_scorecard(scenario_id: str) -> dict:
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


def _degraded_scorecard(scenario_id: str) -> dict:
    return build_long_session_stability_scorecard(
        scenario_id=scenario_id,
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


def test_stability_scorecard_contract_locked() -> None:
    scorecard = _route_drift_scorecard("contract_probe")
    assert_stability_scorecard_contract_locked(scorecard)
    assert validate_stability_scorecard(scorecard) == []
    assert stability_scorecard_contract_misalignments(scorecard) == []
    assert REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS <= frozenset(scorecard)
    assert frozenset(scorecard) <= ALLOWED_LONG_SESSION_STABILITY_SCORECARD_FIELDS
    registries = stability_reporting_field_registries()
    assert registries["long_session_stability_scorecard"]["required"] == REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS


def test_stability_trend_contract_locked() -> None:
    history = build_long_session_stability_history([_stable_scorecard("prior"), _route_drift_scorecard("current")])
    rows = stability_trend_rows_from_history(history)
    assert rows
    assert_stability_trend_contract_locked(rows)
    for row in rows:
        assert validate_stability_trend_row(row) == []
        assert stability_trend_row_contract_misalignments(row) == []
        assert REQUIRED_STABILITY_TREND_ROW_FIELDS <= frozenset(row)
        assert frozenset(row) <= ALLOWED_STABILITY_TREND_ROW_FIELDS


def test_stability_hotspot_contract_locked() -> None:
    scorecards = [_stable_scorecard("prior"), _route_drift_scorecard("current")]
    hotspots = build_stability_hotspots(scorecards)
    assert_stability_hotspot_contract_locked(hotspots)
    assert hotspots["hotspot_rows"]
    for row in hotspots["hotspot_rows"]:
        assert validate_stability_hotspot_row(row) == []
        assert stability_hotspot_row_contract_misalignments(row) == []
        assert REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS <= frozenset(row)
        assert frozenset(row) <= ALLOWED_STABILITY_HOTSPOT_ROW_FIELDS


def test_stability_ownership_contract_locked() -> None:
    scorecards = [_stable_scorecard("prior"), _route_drift_scorecard("current"), _degraded_scorecard("degraded")]
    payload = build_risk_payload([], stability_scorecards=scorecards)["stability_ownership"]
    assert_stability_ownership_contract_locked(payload)
    assert REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS <= frozenset(payload)
    assert frozenset(payload) <= ALLOWED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS
    projected_rows = stability_classification_rows_from_scorecard(scorecards[-1])
    assert projected_rows
    for row in projected_rows:
        assert validate_stability_ownership_classification_row(row) == []
    assert payload["aggregation"]["classification_rows"]


def test_stability_reporting_boundary_documented() -> None:
    assert_stability_reporting_boundary_documented()
    manifest = stability_reporting_governance_manifest()
    assert manifest["advisory_only"] is True
    assert manifest["report_only"] is True
    assert manifest["gameplay_ownership"] is False
    assert manifest["acceptance_ownership"] is False
    assert manifest["acceptance_threshold_ownership"] is False
    assert STABILITY_REPORTING_OWNERSHIP["golden_replay"]["owns"].startswith("long-session metric generation")
    assert STABILITY_REPORTING_OWNERSHIP["taxonomy"]["owns"].startswith("owner attribution classification")
    assert STABILITY_REPORTING_OWNERSHIP["risk_reporting"]["owns"].startswith("stability ownership enrichment")
    assert STABILITY_REPORTING_OWNERSHIP["dashboard_reporting"]["owns"].startswith("markdown rendering")
    enriched = enrich_risk_payload_with_stability_ownership({"report_only": True}, [_route_drift_scorecard("probe")])
    assert "stability_ownership" in enriched


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
