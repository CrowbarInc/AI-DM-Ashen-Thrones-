"""In-memory pytest-session collection buffers for replay diagnostics.

Owns mutable session state and simple record/clear/access helpers only.
Rendering, artifact paths, and writer orchestration stay elsewhere.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from game.runtime_lineage_telemetry import normalize_runtime_lineage_events

_RECORDED_FAILURE_DASHBOARD_ROWS: list[Mapping[str, Any]] = []
_RECORDED_RUNTIME_LINEAGE_EVENTS: list[dict[str, Any]] = []
_RECORDED_PROTECTED_REPLAY_FAILURE_ROWS: list[Mapping[str, Any]] = []
_RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS: list[dict[str, Any]] = []
_RECORDED_RERUN_DRIFT_SCORECARDS: list[Mapping[str, Any]] = []
_RECORDED_LONG_SESSION_STABILITY_SCORECARDS: list[Mapping[str, Any]] = []


def record_failure_dashboard_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Record rows for the pytest session-level dashboard artifact."""
    _RECORDED_FAILURE_DASHBOARD_ROWS.extend(dict(row) for row in rows if isinstance(row, Mapping))


def record_runtime_lineage_events(events: Any) -> None:
    """Record separate replay lineage diagnostics without changing classification rows."""
    _RECORDED_RUNTIME_LINEAGE_EVENTS.extend(normalize_runtime_lineage_events(events)[:16])


def append_protected_replay_failure_row(row: Mapping[str, Any]) -> None:
    """Append one enriched protected replay failure row to the session buffer."""
    _RECORDED_PROTECTED_REPLAY_FAILURE_ROWS.append(dict(row))


def extend_protected_replay_runtime_lineage_events(events: Any) -> None:
    """Append normalized runtime lineage events for protected replay failures."""
    _RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS.extend(
        normalize_runtime_lineage_events(events)[:16]
    )


def clear_recorded_failure_dashboard_rows() -> None:
    _RECORDED_FAILURE_DASHBOARD_ROWS.clear()
    _RECORDED_RUNTIME_LINEAGE_EVENTS.clear()


def recorded_failure_dashboard_rows() -> list[Mapping[str, Any]]:
    return list(_RECORDED_FAILURE_DASHBOARD_ROWS)


def recorded_runtime_lineage_events() -> list[dict[str, Any]]:
    return list(_RECORDED_RUNTIME_LINEAGE_EVENTS)


def clear_recorded_protected_replay_failures() -> None:
    _RECORDED_PROTECTED_REPLAY_FAILURE_ROWS.clear()
    _RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS.clear()


def recorded_protected_replay_failure_rows() -> list[Mapping[str, Any]]:
    return list(_RECORDED_PROTECTED_REPLAY_FAILURE_ROWS)


def recorded_protected_replay_runtime_lineage_events() -> list[dict[str, Any]]:
    return list(_RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS)


def clear_recorded_rerun_drift_scorecards() -> None:
    _RECORDED_RERUN_DRIFT_SCORECARDS.clear()


def record_rerun_drift_scorecard(scorecard: Mapping[str, Any] | None) -> None:
    """Record one successful-run rerun drift scorecard for optional artifacts."""
    if isinstance(scorecard, Mapping):
        _RECORDED_RERUN_DRIFT_SCORECARDS.append(dict(scorecard))


def recorded_rerun_drift_scorecards() -> list[Mapping[str, Any]]:
    return list(_RECORDED_RERUN_DRIFT_SCORECARDS)


def clear_recorded_long_session_stability_scorecards() -> None:
    _RECORDED_LONG_SESSION_STABILITY_SCORECARDS.clear()


def record_long_session_stability_scorecard(scorecard: Mapping[str, Any] | None) -> None:
    """Record one long-session stability scorecard for optional artifacts."""
    if isinstance(scorecard, Mapping):
        _RECORDED_LONG_SESSION_STABILITY_SCORECARDS.append(dict(scorecard))


def recorded_long_session_stability_scorecards() -> list[Mapping[str, Any]]:
    return list(_RECORDED_LONG_SESSION_STABILITY_SCORECARDS)


def clear_all_session_buffers() -> None:
    """Clear every in-memory diagnostic collection buffer."""
    clear_recorded_failure_dashboard_rows()
    clear_recorded_protected_replay_failures()
    clear_recorded_rerun_drift_scorecards()
    clear_recorded_long_session_stability_scorecards()
