from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "replay_maintenance_metrics.py"


@pytest.fixture(scope="module")
def metrics_mod():
    name = "_replay_maintenance_metrics_test"
    spec = importlib.util.spec_from_file_location(name, TOOL_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _mini_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "mini_repo"
    _write(
        repo / "tests" / "helpers" / "golden_replay.py",
        "def run_replay():\n    return True\n",
    )
    _write(
        repo / "tests" / "helpers" / "failure_dashboard_report.py",
        "from tests.helpers.golden_replay import run_replay\n\n"
        "def render_report():\n    return run_replay()\n",
    )
    _write(
        repo / "tests" / "helpers" / "failure_dashboard_paths.py",
        "FAILURE_DASHBOARD_LATEST_PATH = 'audits/failure_dashboard_latest.md'\n",
    )
    _write(
        repo / "tests" / "test_golden_replay.py",
        "from tests.helpers.golden_replay import run_replay\n\n"
        "def test_run():\n    assert run_replay()\n",
    )
    return repo


def test_metrics_tool_runs(metrics_mod, tmp_path: Path) -> None:
    repo = _mini_repo(tmp_path)
    report = metrics_mod.build_metrics(repo, generated_at="2026-06-24T00:00:00Z")
    assert report["schema_version"] == metrics_mod.SCHEMA_VERSION
    assert report["audit_id"] == "CE1"
    assert report["executive_summary"]["replay_file_count"] >= 3


def test_output_schema_is_stable(metrics_mod, tmp_path: Path) -> None:
    repo = _mini_repo(tmp_path)
    report = metrics_mod.build_metrics(repo, generated_at="2026-06-24T00:00:00Z")
    assert tuple(report.keys()) == metrics_mod.TOP_LEVEL_JSON_KEYS
    assert "dependency_concentration" in report
    assert len(report["dependency_concentration"]) == len(metrics_mod.TARGET_MODULES)
    for row in report["dependency_concentration"]:
        assert set(row) == {"module", "fan_in", "fan_out"}


def test_json_generation_succeeds(metrics_mod, tmp_path: Path) -> None:
    repo = _mini_repo(tmp_path)
    report = metrics_mod.build_metrics(repo, generated_at="2026-06-24T00:00:00Z")
    json_out = tmp_path / "replay_maintenance_metrics.json"
    markdown_out = tmp_path / "replay_maintenance_metrics.md"
    metrics_mod.write_reports(report, json_out=json_out, markdown_out=markdown_out)
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["generated_at"] == "2026-06-24T00:00:00Z"
    assert json_out.is_file()
    assert markdown_out.is_file()


def test_markdown_generation_succeeds(metrics_mod, tmp_path: Path) -> None:
    repo = _mini_repo(tmp_path)
    report = metrics_mod.build_metrics(repo, generated_at="2026-06-24T00:00:00Z")
    markdown = metrics_mod.render_markdown(report)
    assert markdown.startswith("# Replay Maintenance Metrics")
    assert "## Executive Summary" in markdown
    assert "## Import Concentration" in markdown
    assert "## Maintenance Risk Assessment" in markdown
    assert "| Module | Fan-In | Fan-Out |" in markdown


def test_cli_writes_default_artifact_paths(metrics_mod, tmp_path: Path) -> None:
    repo = _mini_repo(tmp_path)
    json_out = repo / "artifacts" / "golden_replay" / "replay_maintenance_metrics.json"
    md_out = repo / "artifacts" / "golden_replay" / "replay_maintenance_metrics.md"
    exit_code = metrics_mod.main(
        [
            "--repo-root",
            str(repo),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(md_out),
            "--generated-at",
            "2026-06-24T00:00:00Z",
        ]
    )
    assert exit_code == 0
    assert json_out.is_file()
    assert md_out.is_file()


def test_real_repo_snapshot_includes_report_hub(metrics_mod) -> None:
    report = metrics_mod.build_metrics(ROOT, generated_at="2026-06-24T00:00:00Z")
    paths = {row["path"] for row in report["largest_replay_files"]}
    assert "tests/helpers/failure_dashboard_report.py" in paths or any(
        "failure_dashboard_report.py" in path for path in paths
    )
    modules = {row["module"] for row in report["dependency_concentration"]}
    assert "tests.helpers.failure_dashboard_report" in modules
