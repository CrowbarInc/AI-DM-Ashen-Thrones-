"""Pytest defaults: avoid real OpenAI calls on every ``TestClient(app)`` lifespan startup."""

from __future__ import annotations

import os
import sys

import pytest

# Default on in CI / local pytest so importing ``game.api`` + TestClient does not hit the network.
os.environ.setdefault("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")


def pytest_addoption(parser):
    parser.addoption(
        "--write-failure-dashboard",
        action="store_true",
        default=False,
        help="Write audits/failure_dashboard_latest.md from opt-in golden replay failure classifications.",
    )
    parser.addoption(
        "--write-rerun-drift-scorecard",
        action="store_true",
        default=False,
        help="Write artifacts/golden_replay/rerun_drift_scorecard.{json,md} from opt-in replay rerun diagnostics.",
    )
    parser.addoption(
        "--write-long-session-stability-scorecard",
        action="store_true",
        default=False,
        help="Write artifacts/golden_replay/long_session_stability_scorecard.{json,md} from opt-in long-session diagnostics.",
    )


def pytest_configure(config):
    if config.getoption("--write-failure-dashboard", default=False):
        os.environ["ASHEN_WRITE_FAILURE_DASHBOARD"] = "1"
    if config.getoption("--write-rerun-drift-scorecard", default=False):
        os.environ["ASHEN_WRITE_RERUN_DRIFT_SCORECARD"] = "1"
    if config.getoption("--write-long-session-stability-scorecard", default=False):
        os.environ["ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD"] = "1"
    if any(
        str(os.environ.get(name) or "").strip().lower() in {"1", "true", "yes", "on"}
        for name in (
            "ASHEN_WRITE_FAILURE_DASHBOARD",
            "ASHEN_WRITE_RERUN_DRIFT_SCORECARD",
            "ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD",
        )
    ):
        from tests.helpers.failure_dashboard_report import clear_requested_artifact_recordings

        clear_requested_artifact_recordings()


def _failure_dashboard_probe_requested(config) -> bool:
    if str(os.environ.get("ASHEN_RUN_FAILURE_DASHBOARD_PROBES") or "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    markexpr = str(getattr(config.option, "markexpr", "") or "")
    if "failure_dashboard_probe" in markexpr:
        return True
    for arg in getattr(config, "args", []) or []:
        if "test_failure_dashboard_controlled_failures.py" in str(arg):
            return True
    return False


def pytest_collection_modifyitems(config, items):
    if _failure_dashboard_probe_requested(config):
        return
    skip_probe = pytest.mark.skip(
        reason="failure dashboard probes are opt-in; run the file, use -m failure_dashboard_probe, or set ASHEN_RUN_FAILURE_DASHBOARD_PROBES=1"
    )
    for item in items:
        if item.get_closest_marker("failure_dashboard_probe"):
            item.add_marker(skip_probe)


def pytest_sessionfinish(session, exitstatus):
    from tests.helpers.failure_dashboard_report import write_requested_dashboard_artifacts

    write_requested_dashboard_artifacts(
        exitstatus=exitstatus,
        command_used=" ".join(sys.argv),
    )
