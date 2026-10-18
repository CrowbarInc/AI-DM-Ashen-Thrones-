"""Pytest-session artifact orchestration for replay diagnostic dashboards.

Coordinates env-gated writes across dashboard, protected replay, drift, and stability
surfaces. Rendering implementations remain in failure_dashboard_report.py and sibling
artifact-family modules.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping
import os
from datetime import datetime, timezone

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

    env_map = env if env is not None else os.environ
    current_report = env_map.get("ASHEN_PROTECTED_REPLAY_REPORT_PATH")
    if exitstatus != 0:
        report_kwargs = {}
        if current_report:
            report_kwargs = {"path": current_report, "side_effect_artifact_root": Path(current_report).parent}
        failure_report = write_protected_replay_failure_report_if_present(command_used=command_used, **report_kwargs)
        if failure_report is not None:
            written.append(failure_report)
        elif current_report:
            # Collection/import failures have no protected assertion rows. Write
            # a fresh run summary rather than publishing a checked-in old report.
            path = Path(current_report)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Protected Replay Execution Failure\n\n"
                f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`\n"
                f"- Command: `{command_used}`\n"
                f"- Pytest exit status: `{exitstatus}`\n"
                "- Protected assertion failures recorded: `0`\n\n"
                "No protected assertion report was produced by this execution. "
                "Inspect pytest-output.txt and pytest.xml for collection, setup, or other failures.\n",
                encoding="utf-8",
            )
            written.append(path)

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
