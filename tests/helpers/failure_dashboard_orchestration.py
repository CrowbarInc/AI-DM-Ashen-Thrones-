"""Pytest-session artifact orchestration for replay diagnostic dashboards.

Coordinates env-gated writes across dashboard, protected replay, drift, and stability
surfaces. Rendering implementations remain in failure_dashboard_report.py and sibling
artifact-family modules.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from tests.helpers.failure_dashboard_drift import (
    rerun_drift_scorecard_requested,
    write_rerun_drift_scorecard_artifacts,
)
from tests.helpers.failure_dashboard_session import (
    clear_recorded_failure_dashboard_rows,
    clear_recorded_long_session_stability_scorecards,
    clear_recorded_rerun_drift_scorecards,
    recorded_failure_dashboard_rows,
    recorded_long_session_stability_scorecards,
    recorded_rerun_drift_scorecards,
)
from tests.helpers.failure_dashboard_stability import (
    long_session_stability_scorecard_requested,
    write_long_session_stability_scorecard_artifacts,
)


def clear_requested_artifact_recordings(env: Mapping[str, str] | None = None) -> None:
    """Clear recorder state for artifact writers requested in this pytest session."""
    from tests.helpers.failure_dashboard_report import failure_dashboard_requested

    if failure_dashboard_requested(env):
        clear_recorded_failure_dashboard_rows()
    if rerun_drift_scorecard_requested(env):
        clear_recorded_rerun_drift_scorecards()
    if long_session_stability_scorecard_requested(env):
        clear_recorded_long_session_stability_scorecards()


def write_requested_dashboard_artifacts(
    *,
    exitstatus: int,
    command_used: str | None = None,
    env: Mapping[str, str] | None = None,
) -> list[Path]:
    """Write all pytest-session dashboard artifacts requested by status and env."""
    from tests.helpers.failure_dashboard_report import (
        failure_dashboard_requested,
        write_failure_dashboard_artifact,
        write_protected_replay_failure_report_if_present,
    )

    written: list[Path] = []

    if exitstatus != 0:
        failure_report = write_protected_replay_failure_report_if_present(command_used=command_used)
        if failure_report is not None:
            written.append(failure_report)

    if exitstatus == 0 and rerun_drift_scorecard_requested(env):
        scorecards = recorded_rerun_drift_scorecards()
        written.extend(
            write_rerun_drift_scorecard_artifacts(
                scorecards[-1] if scorecards else None,
                command_used=command_used,
            )
        )

    if exitstatus == 0 and long_session_stability_scorecard_requested(env):
        stability_scorecards = recorded_long_session_stability_scorecards()
        written.extend(
            write_long_session_stability_scorecard_artifacts(
                stability_scorecards[-1] if stability_scorecards else None,
                command_used=command_used,
            )
        )

    if failure_dashboard_requested(env):
        written.append(
            write_failure_dashboard_artifact(
                recorded_failure_dashboard_rows(),
                command_used=command_used,
            )
        )

    return written
