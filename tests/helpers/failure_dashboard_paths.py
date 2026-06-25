"""Canonical paths for replay diagnostic and report artifacts.

This module owns path constants and simple path derivation helpers only.
Rendering, aggregation, and artifact-writing orchestration stay elsewhere.
"""
from __future__ import annotations

from pathlib import Path

# Opt-in environment gates for pytest-session artifact writers.
FAILURE_DASHBOARD_ENV_VAR = "ASHEN_WRITE_FAILURE_DASHBOARD"
RERUN_DRIFT_SCORECARD_ENV_VAR = "ASHEN_WRITE_RERUN_DRIFT_SCORECARD"
LONG_SESSION_STABILITY_SCORECARD_ENV_VAR = "ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD"

# Failure dashboard and protected replay reports.
FAILURE_DASHBOARD_LATEST_PATH = Path("audits/failure_dashboard_latest.md")
PROTECTED_REPLAY_FAILURE_REPORT_PATH = Path("artifacts/golden_replay/replay_failure_report.md")

# Rerun drift scorecard.
RERUN_DRIFT_SCORECARD_JSON_PATH = Path("artifacts/golden_replay/rerun_drift_scorecard.json")
RERUN_DRIFT_SCORECARD_MARKDOWN_PATH = Path("artifacts/golden_replay/rerun_drift_scorecard.md")

# Long-session stability scorecard.
LONG_SESSION_STABILITY_SCORECARD_JSON_PATH = Path(
    "artifacts/golden_replay/long_session_stability_scorecard.json"
)
LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH = Path(
    "artifacts/golden_replay/long_session_stability_scorecard.md"
)

# Owner drift diagnostic artifacts.
OWNER_DRIFT_LONGITUDINAL_JSON_PATH = Path("artifacts/golden_replay/owner_drift_longitudinal.json")
OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_longitudinal.md")
OWNER_DRIFT_HOTSPOTS_JSON_PATH = Path("artifacts/golden_replay/owner_drift_hotspots.json")
OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_hotspots.md")
OWNER_DRIFT_TRENDS_JSON_PATH = Path("artifacts/golden_replay/owner_drift_trends.json")
OWNER_DRIFT_TRENDS_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_trends.md")
OWNER_DRIFT_RISK_JSON_PATH = Path("artifacts/golden_replay/owner_drift_risk.json")
OWNER_DRIFT_RISK_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_risk.md")

# Bug-class recurrence history and event logs.
BUG_RECURRENCE_HISTORY_JSON_PATH = Path("artifacts/golden_replay/bug_recurrence_history.json")
BUG_RECURRENCE_HISTORY_MARKDOWN_PATH = Path("artifacts/golden_replay/bug_recurrence_history.md")
BUG_RECURRENCE_EVENT_LOG_JSON_PATH = Path("artifacts/golden_replay/bug_recurrence_event_log.json")
BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH = Path(
    "artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json"
)
RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH = Path(
    "artifacts/golden_replay/recurrence_trajectory_history.json"
)


def bug_recurrence_event_log_path(json_path: Path | str) -> Path:
    """Derive the recurrence event-log path from a history JSON path."""
    history_path = Path(json_path)
    if history_path.name == BUG_RECURRENCE_HISTORY_JSON_PATH.name:
        return history_path.with_name(BUG_RECURRENCE_EVENT_LOG_JSON_PATH.name)
    return history_path.with_name(f"{history_path.stem}_event_log.json")


def bug_recurrence_session_diagnostic_event_log_path(json_path: Path | str) -> Path:
    """Derive the session-diagnostic event-log path from a history JSON path."""
    history_path = Path(json_path)
    if history_path.name == BUG_RECURRENCE_HISTORY_JSON_PATH.name:
        return history_path.with_name(BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH.name)
    return history_path.with_name(f"{history_path.stem}_session_diagnostic_event_log.json")


def bug_recurrence_trajectory_history_path(json_path: Path | str) -> Path:
    """Derive the recurrence trajectory history path from a history JSON path."""
    history_path = Path(json_path).resolve()
    if history_path == BUG_RECURRENCE_HISTORY_JSON_PATH.resolve():
        return RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH
    return history_path.with_name("recurrence_trajectory_history.json")
