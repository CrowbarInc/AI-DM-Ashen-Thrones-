"""BZ closeout doc/command validation locks for protected replay trend window #2."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from tests.helpers.golden_replay_trend import BZ_REPLAY_KEY_MOVEMENT_FILENAME
from tests.helpers.protected_replay_registry import (
    protected_replay_corpus,
    protected_replay_registry_validation_errors,
)
from tests.helpers.protected_replay_trend_movement import BZ_RECURRENCE_MOVEMENT_FILENAME

REPO_ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_DOC = REPO_ROOT / "docs" / "BZ_protected_replay_trend_window_2_closeout.md"
TREND_CLI = REPO_ROOT / "tools" / "run_protected_replay_trend.py"
BZ_OUTPUT_DIR = REPO_ROOT / "artifacts" / "golden_replay" / "trend_window_2"

REQUIRED_SECTION_MARKERS = (
    "## Objective",
    "## Commands run",
    "## Corpus used",
    "## Baseline and output paths",
    "## Corpus parity result",
    "## Replay key movement summary",
    "## Recurrence movement summary",
    "## Baseline establishment mode",
    "## Known limitations",
    "## Final assessment against success criteria",
)

DOC_COMMAND_PATTERNS = (
    r"python tools/run_protected_replay_trend\.py --runs 2 --out-dir artifacts/golden_replay/trend_window_2",
    r"python -m pytest tests/test_bz_protected_replay_trend_window_2\.py tests/test_bz_protected_replay_trend_window_2_closeout\.py tests/test_bw_protected_replay_trend_window_closeout\.py tests/test_golden_replay_trend\.py -q",
    r"python -m pytest -m golden_replay -q",
)


def test_closeout_doc_exists_and_declares_bz_closed() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    assert CLOSEOUT_DOC.is_file()
    assert "BZ is **closed**" in text
    assert "measurement only" in text.lower() or "measurement-only" in text.lower()


def test_closeout_doc_required_sections_exist() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    for marker in REQUIRED_SECTION_MARKERS:
        assert marker in text, f"closeout doc missing section {marker!r}"


def test_closeout_doc_command_references_trend_window_2() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    for pattern in DOC_COMMAND_PATTERNS:
        assert re.search(pattern, text), f"closeout doc missing command matching {pattern!r}"
    assert "artifacts/golden_replay/trend_window_2" in text
    assert TREND_CLI.is_file()


def test_closeout_doc_references_bz_replay_key_movement_artifact() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    assert BZ_REPLAY_KEY_MOVEMENT_FILENAME in text
    assert f"artifacts/golden_replay/trend_window_2/{BZ_REPLAY_KEY_MOVEMENT_FILENAME}" in text


def test_closeout_doc_references_bz_recurrence_movement_artifact() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    assert BZ_RECURRENCE_MOVEMENT_FILENAME in text
    assert f"artifacts/golden_replay/trend_window_2/{BZ_RECURRENCE_MOVEMENT_FILENAME}" in text


def test_closeout_doc_states_bw_artifacts_are_not_modified() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    assert "artifacts/golden_replay/trend_window/" in text
    assert "not modified" in text.lower() or "are not modified" in text.lower()
    assert "immutable" in text.lower()


def test_closeout_doc_states_recurrence_historical_movement_requires_explicit_baseline() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    for marker in (
        "baseline_establishment",
        "not claimed",
        "explicit",
        "BW-time recurrence snapshot",
    ):
        assert marker.lower() in text.lower(), f"closeout doc missing recurrence honesty marker {marker!r}"


def test_closeout_doc_states_six_scenario_protected_corpus() -> None:
    text = CLOSEOUT_DOC.read_text(encoding="utf-8")
    assert "six short structural scenarios" in text
    assert len(protected_replay_corpus()) == 6
    assert protected_replay_registry_validation_errors() == []


def test_closeout_doc_bz_output_artifacts_exist_in_repo() -> None:
    assert (BZ_OUTPUT_DIR / BZ_REPLAY_KEY_MOVEMENT_FILENAME).is_file()
    assert (BZ_OUTPUT_DIR / BZ_RECURRENCE_MOVEMENT_FILENAME).is_file()
    assert (BZ_OUTPUT_DIR / "BZ_protected_replay_trend_window_2.md").is_file()


def test_trend_cli_help_exposes_bz_recurrence_baseline_flag() -> None:
    completed = subprocess.run(
        [sys.executable, str(TREND_CLI), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--bz-recurrence-baseline" in completed.stdout
    assert "--bz-replay-key-baseline-run" in completed.stdout
