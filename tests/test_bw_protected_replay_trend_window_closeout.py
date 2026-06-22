"""BW5 closeout doc/command validation locks for protected replay trend windows."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from tests.helpers.golden_replay_trend import (
    GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL,
    GOLDEN_TRANSCRIPT_DRIFT_HISTORY_MD,
)
from tests.helpers.protected_replay_registry import (
    protected_replay_corpus,
    protected_replay_registry_validation_errors,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_DOC = REPO_ROOT / "docs" / "BW_protected_replay_trend_window_closeout.md"
TREND_CLI = REPO_ROOT / "tools" / "run_protected_replay_trend.py"
MANIFEST_CLI = REPO_ROOT / "tools" / "refresh_protected_replay_manifest.py"

REQUIRED_ARTIFACTS = (
    "manifest.json",
    "golden_transcript_drift.json",
    "golden_transcript_drift.md",
    GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL,
    GOLDEN_TRANSCRIPT_DRIFT_HISTORY_MD,
    "runs/run-000.json",
    "runs/run-001.json",
    "comparisons/run-001-vs-run-000.json",
)

DOC_COMMAND_PATTERNS = (
    r"python tools/run_protected_replay_trend\.py --runs 2 --out-dir artifacts/golden_replay/trend_window --append-history",
    r"python -m pytest tests/test_golden_replay_trend\.py tests/test_protected_replay_registry\.py -q",
    r"python -m pytest -m golden_replay -q",
    r"python tools/refresh_protected_replay_manifest\.py --check",
    r"python -m pytest tests/test_runtime_drift_seed_audit\.py -q",
)


def test_closeout_doc_exists_and_declares_bw_closed() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    assert "BW is **closed**" in text
    assert "Golden Transcript Drift" in text
    assert "report-only" in text.lower()


def test_closeout_doc_lists_all_required_artifact_paths() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    for artifact in REQUIRED_ARTIFACTS:
        assert artifact in text, f"missing artifact path {artifact!r} in closeout doc"


def test_closeout_doc_command_examples_match_implementation() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    for pattern in DOC_COMMAND_PATTERNS:
        assert re.search(pattern, text), f"closeout doc missing command matching {pattern!r}"

    assert TREND_CLI.is_file()
    assert MANIFEST_CLI.is_file()
    assert (REPO_ROOT / "tests" / "test_golden_replay_trend.py").is_file()
    assert (REPO_ROOT / "tests" / "test_protected_replay_registry.py").is_file()
    assert (REPO_ROOT / "tests" / "test_runtime_drift_seed_audit.py").is_file()


def test_closeout_doc_states_six_scenario_protected_corpus() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    assert "exactly the six short structural scenarios" in text
    assert len(protected_replay_corpus()) == 6
    assert protected_replay_registry_validation_errors() == []


def test_closeout_doc_documents_supporting_scenarios_not_in_bw_corpus() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    for marker in (
        "test_golden_replay_long_session.py",
        "test_golden_replay_direct_seam.py",
        "test_golden_replay_scenario_spine.py",
        "SUPPORTING",
    ):
        assert marker in text, f"closeout doc missing supporting-scenario marker {marker!r}"


def test_trend_cli_help_is_invocable() -> None:
    completed = subprocess.run(
        [sys.executable, str(TREND_CLI), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--runs" in completed.stdout
    assert "--append-history" in completed.stdout
    assert "--out-dir" in completed.stdout
