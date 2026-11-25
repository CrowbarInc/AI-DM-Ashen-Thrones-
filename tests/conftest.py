"""Pytest defaults: avoid real OpenAI calls on every ``TestClient(app)`` lifespan startup."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

from tests.helpers.storage_isolation import ARTIFACTS, ROOT
from tools.execution_workspace import OwnedWorkspace
from tests.helpers.storage_isolation import install as _install_storage_isolation

# Default on in CI / local pytest so importing ``game.api`` + TestClient does not hit the network.
os.environ.setdefault("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
# Interpretation model calls are live-only. Pytest keeps the deterministic boundary.
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
# Bounded expression generation is live-only. Deterministic tests keep host wording.
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"


def pytest_addoption(parser):
    parser.addoption(
        "--ashen-test-workspace",
        type=Path,
        help="Use an existing, execution-owned workspace. The caller owns its cleanup.",
    )
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


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    # Install storage before test collection imports game.storage. Reserve the
    # pytest base as a child because pytest clears an explicit base on first use.
    scratch = ROOT / "development" / "tmp"
    supplied = config.getoption("--ashen-test-workspace")
    owned_workspace: OwnedWorkspace | None = None
    if supplied is None:
        owned_workspace = OwnedWorkspace.allocate(scratch, "pytest-run-")
        workspace = owned_workspace.root
    else:
        workspace = Path(supplied).resolve(strict=True)
        if scratch not in workspace.parents:
            raise pytest.UsageError("--ashen-test-workspace must be inside development/tmp")

    config._ashen_exitstatus = None
    storage_variables = ("ASHEN_DATA_DIR", "ASHEN_PROVIDER_USAGE_PATH", "ASHEN_TEST_EVIDENCE_DIR")
    previous_environment = {name: os.environ.get(name) for name in storage_variables}

    def finish_workspace():
        for name, value in previous_environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        if owned_workspace is None:
            return
        if config._ashen_exitstatus != pytest.ExitCode.OK:
            print(f"Pytest diagnostics retained at {workspace}", file=sys.stderr)
            return
        try:
            owned_workspace.discard()
        except OSError as exc:
            print(f"Could not clean pytest workspace {workspace}: {exc}", file=sys.stderr)
            raise

    config.add_cleanup(finish_workspace)
    storage = workspace / "storage"
    storage.mkdir()
    config._ashen_test_storage_root = _install_storage_isolation(storage)
    if config.option.basetemp is None:
        config.option.basetemp = str(workspace / "pytest")

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
    # Older analysis suites use a module-level OUT for generated reports. Keep
    # their read-only ROOT fixtures intact while isolating report destinations.
    for module in {item.module for item in items}:
        output = getattr(module, "OUT", None)
        if isinstance(output, Path) and (output.resolve() == ARTIFACTS or ARTIFACTS in output.resolve().parents):
            isolated_output = config._ashen_test_storage_root / "test_artifacts" / module.__name__
            isolated_output.mkdir(parents=True, exist_ok=True)
            module.OUT = isolated_output
    if _failure_dashboard_probe_requested(config):
        return
    skip_probe = pytest.mark.skip(
        reason="failure dashboard probes are opt-in; run the file, use -m failure_dashboard_probe, or set ASHEN_RUN_FAILURE_DASHBOARD_PROBES=1"
    )
    for item in items:
        if item.get_closest_marker("failure_dashboard_probe"):
            item.add_marker(skip_probe)


@pytest.fixture(autouse=True)
def _forbid_live_model_calls(monkeypatch):
    """Turn an accidental live model call into an immediate test error.

    Generation stubs installed by a test replace the wrapper. The OpenAI
    constructor remains blocked for the whole test.
    """
    from tests.helpers.live_model_guard import install_live_model_guard

    install_live_model_guard(monkeypatch)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    from tests.helpers.failure_dashboard_report import write_requested_dashboard_artifacts

    write_requested_dashboard_artifacts(
        exitstatus=exitstatus,
        command_used=" ".join(sys.argv),
    )
    result = yield
    session.config._ashen_exitstatus = exitstatus
    return result
