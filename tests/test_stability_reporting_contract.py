from __future__ import annotations

from tests.helpers.golden_replay_api import build_long_session_stability_scorecard
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
