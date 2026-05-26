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


def pytest_configure(config):
    if config.getoption("--write-failure-dashboard", default=False):
        os.environ["ASHEN_WRITE_FAILURE_DASHBOARD"] = "1"
    if str(os.environ.get("ASHEN_WRITE_FAILURE_DASHBOARD") or "").strip().lower() in {"1", "true", "yes", "on"}:
        from tests.helpers.failure_dashboard_report import clear_recorded_failure_dashboard_rows

        clear_recorded_failure_dashboard_rows()


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
    from tests.helpers.failure_dashboard_report import write_protected_replay_failure_report_if_present

    if exitstatus != 0:
        write_protected_replay_failure_report_if_present(command_used=" ".join(sys.argv))
    if str(os.environ.get("ASHEN_WRITE_FAILURE_DASHBOARD") or "").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    from tests.helpers.failure_dashboard_report import (
        recorded_failure_dashboard_rows,
        write_failure_dashboard_artifact,
    )

    write_failure_dashboard_artifact(
        recorded_failure_dashboard_rows(),
        command_used=" ".join(sys.argv),
    )
