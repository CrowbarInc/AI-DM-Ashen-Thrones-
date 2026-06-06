"""Canonical long-session stability reporting contract (Cycle AT6).

Governance-only lock for AT1–AT5 advisory reporting surfaces. Does not change
gameplay, replay behavior, ranking logic, or acceptance thresholds.

Alignment with projection helpers is enforced by
``tests.helpers.stability_reporting_sync``.
"""
from __future__ import annotations

from typing import Any, Mapping

STABILITY_REPORTING_SCHEMA_VERSION: int = 1
STABILITY_REPORTING_ADVISORY_ONLY: bool = True
STABILITY_REPORTING_REPORT_ONLY: bool = True

# Long-session stability scorecard (AT1 / metric generation surface).
REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "report_only",
        "scenario_id",
        "turn_count",
        "route_stability",
        "speaker_stability",
        "fallback_stability",
        "lineage_stability",
        "degradation",
        "operational_summary",
        "owner_drift_classifications",
        "owner_drift_bucket_counts",
    }
)

OPTIONAL_LONG_SESSION_STABILITY_SCORECARD_FIELDS: frozenset[str] = frozenset(
    {
        "branch_id",
        "source_path",
    }
)

ALLOWED_LONG_SESSION_STABILITY_SCORECARD_FIELDS: frozenset[str] = (
    REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS | OPTIONAL_LONG_SESSION_STABILITY_SCORECARD_FIELDS
)

REQUIRED_ROUTE_STABILITY_FIELDS: frozenset[str] = frozenset({"route_change_count", "route_frequency"})
REQUIRED_SPEAKER_STABILITY_FIELDS: frozenset[str] = frozenset(
    {"speaker_change_count", "speaker_missing_count", "speaker_frequency"}
)
REQUIRED_FALLBACK_STABILITY_FIELDS: frozenset[str] = frozenset(
    {
        "fallback_count",
        "fallback_family_frequency",
        "max_fallback_streak",
        "late_window_fallback_count",
        "escalation_warnings",
    }
)
REQUIRED_LINEAGE_STABILITY_FIELDS: frozenset[str] = frozenset({"recurring_events", "event_counts"})
REQUIRED_DEGRADATION_FIELDS: frozenset[str] = frozenset(
    {
        "progressive_degradation_detected",
        "reason_codes",
        "health",
        "classification",
        "long_session_band",
        "overall_passed",
    }
)
REQUIRED_OPERATIONAL_SUMMARY_FIELDS: frozenset[str] = frozenset(
    {"actionable", "warning_count", "stability_status"}
)

ALLOWED_STABILITY_STATUS_VALUES: frozenset[str] = frozenset({"stable", "watch", "degraded", "unknown"})

# Embedded scorecard owner drift rows (AT1 metric surface).
REQUIRED_SCORECARD_OWNER_DRIFT_CLASSIFICATION_FIELDS: frozenset[str] = frozenset(
    {
        "signal",
        "owner_drift_bucket",
        "severity_hint",
        "reason",
        "evidence",
    }
)

# Projected stability ownership classification rows (AT2 / AT3).
REQUIRED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS: frozenset[str] = frozenset(
    {
        "scenario_id",
        "signal",
        "owner_drift_bucket",
        "severity_hint",
        "stability_status",
        "reason",
        "evidence",
    }
)

OPTIONAL_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS: frozenset[str] = frozenset()

ALLOWED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS: frozenset[str] = (
    REQUIRED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS | OPTIONAL_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS
)

# Stability trend rows (AT4).
REQUIRED_STABILITY_TREND_ROW_FIELDS: frozenset[str] = frozenset(
    {
        "owner_drift_bucket",
        "current_count",
        "previous_count",
        "delta",
        "trend",
    }
)

OPTIONAL_STABILITY_TREND_ROW_FIELDS: frozenset[str] = frozenset()

ALLOWED_STABILITY_TREND_ROW_FIELDS: frozenset[str] = (
    REQUIRED_STABILITY_TREND_ROW_FIELDS | OPTIONAL_STABILITY_TREND_ROW_FIELDS
)

ALLOWED_STABILITY_TREND_LABELS: frozenset[str] = frozenset(
    {"worsening", "improving", "stable", "insufficient_data"}
)

# Stability hotspot rows (AT5).
REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS: frozenset[str] = frozenset(
    {
        "rank",
        "owner_drift_bucket",
        "occurrence_count",
        "scenario_count",
        "worsening_count",
        "degraded_count",
        "trend",
        "priority",
    }
)

OPTIONAL_STABILITY_HOTSPOT_ROW_FIELDS: frozenset[str] = frozenset()

ALLOWED_STABILITY_HOTSPOT_ROW_FIELDS: frozenset[str] = (
    REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS | OPTIONAL_STABILITY_HOTSPOT_ROW_FIELDS
)

ALLOWED_STABILITY_HOTSPOT_PRIORITIES: frozenset[str] = frozenset({"critical", "elevated", "normal"})

REQUIRED_STABILITY_HOTSPOT_BUCKET_RANKING_FIELDS: frozenset[str] = frozenset(
    {
        "rank",
        "owner_drift_bucket",
        "occurrence_count",
        "affected_scorecards",
        "affected_scenarios",
        "worsening_count",
        "degraded_count",
    }
)

REQUIRED_STABILITY_HOTSPOT_PAYLOAD_FIELDS: frozenset[str] = frozenset(
    {
        "bucket_rankings",
        "signal_rankings",
        "scenario_rankings",
        "hotspot_rows",
    }
)

# Stability ownership risk payload (AT3 enrichment surface).
REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS: frozenset[str] = frozenset(
    {
        "report_only",
        "advisory_only",
        "aggregation",
        "stability_risk_signals",
        "history",
        "stability_trend_rows",
        "stability_trend_signals",
        "stability_hotspots",
    }
)

OPTIONAL_STABILITY_OWNERSHIP_PAYLOAD_FIELDS: frozenset[str] = frozenset()

ALLOWED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS: frozenset[str] = (
    REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS | OPTIONAL_STABILITY_OWNERSHIP_PAYLOAD_FIELDS
)

REQUIRED_STABILITY_AGGREGATION_FIELDS: frozenset[str] = frozenset(
    {
        "total_scorecards",
        "bucket_frequencies",
        "scenario_frequencies",
        "stability_status_counts",
        "classification_rows",
    }
)

REQUIRED_STABILITY_HISTORY_FIELDS: frozenset[str] = frozenset(
    {
        "sample_count",
        "bucket_history",
        "status_history",
        "signal_history",
        "trend_summary",
    }
)

REQUIRED_STABILITY_TREND_SUMMARY_FIELDS: frozenset[str] = frozenset(
    {
        "comparison_available",
        "bucket_trends",
        "status_trends",
        "overall_stability_trend",
        "current_stability_status",
        "previous_stability_status",
    }
)

STABILITY_REPORTING_OWNERSHIP: dict[str, dict[str, str]] = {
    "golden_replay": {
        "module": "tests/helpers/golden_replay.py",
        "owns": "long-session metric generation; build_long_session_stability_scorecard",
        "does_not_own": "classification projection; trend/hotspot ranking; markdown rendering; acceptance thresholds",
    },
    "taxonomy": {
        "module": "tests/helpers/replay_drift_taxonomy.py",
        "owns": "owner attribution classification; trend projection; hotspot projection; hotspot markdown lines",
        "does_not_own": "scorecard metric generation; risk enrichment; artifact emission; gameplay behavior",
    },
    "risk_reporting": {
        "module": "tests/helpers/replay_drift_risk.py",
        "owns": "stability ownership enrichment; risk report presentation hooks",
        "does_not_own": "scorecard generation; taxonomy classification; dashboard artifact paths",
    },
    "dashboard_reporting": {
        "module": "tests/helpers/failure_dashboard_report.py",
        "owns": "markdown rendering; artifact emission for stability scorecards and risk reports",
        "does_not_own": "metric generation; ranking logic; acceptance pass/fail",
    },
    "contract": {
        "module": "tests/stability_reporting_contract.py",
        "owns": "schema authority; ownership boundaries; advisory-only governance manifest",
        "does_not_own": "runtime gameplay; protected replay assertions; ranking implementation",
    },
}


def stability_reporting_governance_manifest() -> dict[str, Any]:
    """Return the public governance manifest for AT stability reporting."""
    return {
        "schema_version": STABILITY_REPORTING_SCHEMA_VERSION,
        "advisory_only": STABILITY_REPORTING_ADVISORY_ONLY,
        "report_only": STABILITY_REPORTING_REPORT_ONLY,
        "gameplay_ownership": False,
        "acceptance_ownership": False,
        "acceptance_threshold_ownership": False,
        "purpose": (
            "Package existing long-session replay metrics into operator-facing "
            "stability scorecards, ownership attribution, trend history, and hotspot "
            "rankings without changing protected replay pass/fail behavior."
        ),
        "ownership": dict(STABILITY_REPORTING_OWNERSHIP),
    }


def stability_reporting_field_registries() -> dict[str, Mapping[str, frozenset[str]]]:
    """Return contract-locked field registries for drift-prevention tests."""
    return {
        "long_session_stability_scorecard": {
            "required": REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
            "optional": OPTIONAL_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
            "allowed": ALLOWED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
        },
        "scorecard_owner_drift_classification": {
            "required": REQUIRED_SCORECARD_OWNER_DRIFT_CLASSIFICATION_FIELDS,
            "optional": frozenset(),
            "allowed": REQUIRED_SCORECARD_OWNER_DRIFT_CLASSIFICATION_FIELDS,
        },
        "stability_ownership_classification": {
            "required": REQUIRED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS,
            "optional": OPTIONAL_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS,
            "allowed": ALLOWED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS,
        },
        "stability_trend_row": {
            "required": REQUIRED_STABILITY_TREND_ROW_FIELDS,
            "optional": OPTIONAL_STABILITY_TREND_ROW_FIELDS,
            "allowed": ALLOWED_STABILITY_TREND_ROW_FIELDS,
        },
        "stability_hotspot_row": {
            "required": REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS,
            "optional": OPTIONAL_STABILITY_HOTSPOT_ROW_FIELDS,
            "allowed": ALLOWED_STABILITY_HOTSPOT_ROW_FIELDS,
        },
        "stability_ownership_payload": {
            "required": REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
            "optional": OPTIONAL_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
            "allowed": ALLOWED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
        },
    }
