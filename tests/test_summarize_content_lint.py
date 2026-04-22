"""Tests for ``tools/summarize_content_lint.py`` (read-only presenter for canonical JSON)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARIZER = REPO_ROOT / "tools" / "summarize_content_lint.py"


def _run(*argv: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SUMMARIZER), *argv]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


MINIMAL_REPORT = {
    "ok": False,
    "error_count": 2,
    "warning_count": 1,
    "scene_ids_checked": ["a", "b"],
    "messages": [
        {"severity": "error", "code": "z.code", "message": "z", "scene_id": "b"},
        {"severity": "error", "code": "a.code", "message": "m1", "scene_id": "a"},
        {"severity": "error", "code": "a.code", "message": "m2", "scene_id": "a"},
        {"severity": "warning", "code": "w.b", "message": "mw", "scene_id": "b"},
        {"severity": "warning", "code": "w.a", "message": "gw"},
    ],
}


def test_reads_canonical_json_successfully(tmp_path: Path) -> None:
    p = tmp_path / "report.json"
    p.write_text(json.dumps(MINIMAL_REPORT, indent=2), encoding="utf-8")
    proc = _run("--input", str(p))
    assert proc.returncode == 0, proc.stderr
    assert "scenes_checked: 2" in proc.stdout
    assert "errors: 2" in proc.stdout
    assert "warnings: 1" in proc.stdout


def test_summary_text_deterministic_small_fixture(tmp_path: Path) -> None:
    p = tmp_path / "report.json"
    p.write_text(json.dumps(MINIMAL_REPORT), encoding="utf-8")
    proc = _run("--input", str(p), "--top", "2")
    assert proc.returncode == 0, proc.stderr
    expected = (
        "scenes_checked: 2\n"
        "errors: 2   warnings: 1\n"
        "\n"
        "where to look first (code family rollup, max 2):\n"
        "  a: 2 errors / 0 warnings (total 2)\n"
        "  w: 0 errors / 2 warnings (total 2)\n"
        "  ... (1 more family)\n"
        "\n"
        "--- detail (stable ordering) ---\n"
        "\n"
        "top error codes (max 2):\n"
        "  a.code  x2\n"
        "  z.code  x1\n"
        "\n"
        "top warning codes (max 2):\n"
        "  w.a  x1\n"
        "  w.b  x1\n"
        "\n"
        "errors by code family prefix (max 2):\n"
        "  a: 2\n"
        "  z: 1\n"
        "\n"
        "warnings by code family prefix (max 2):\n"
        "  w: 2\n"
        "\n"
        "by scene (errors / warnings, max 2 rows):\n"
        "  [a] 2 / 0\n"
        "  [b] 1 / 1\n"
        "  ... (1 more scene)\n"
        "\n"
        "hint: bundle-level governance uses prefixes such as bundle.*, campaign.*, "
        "scene.reference.*, clue.reference.*, faction.reference.*, world_state.reference.* "
        "(see docs/content_lint_pipeline.md).\n"
    )
    assert expected in proc.stdout


def test_compare_mode_deltas_and_multiset(tmp_path: Path) -> None:
    old = {
        "ok": False,
        "error_count": 1,
        "warning_count": 2,
        "scene_ids_checked": ["x"],
        "messages": [
            {"severity": "error", "code": "gone", "message": "old err", "scene_id": "x"},
            {"severity": "warning", "code": "w.old", "message": "dup", "scene_id": "x"},
            {"severity": "warning", "code": "w.old", "message": "dup", "scene_id": "x"},
        ],
    }
    new = {
        "ok": False,
        "error_count": 2,
        "warning_count": 1,
        "scene_ids_checked": ["x"],
        "messages": [
            {"severity": "error", "code": "gone", "message": "old err", "scene_id": "x"},
            {"severity": "error", "code": "fresh", "message": "new err", "scene_id": "x"},
            {"severity": "warning", "code": "w.new", "message": "only in new", "scene_id": "x"},
        ],
    }
    pa = tmp_path / "a.json"
    pb = tmp_path / "b.json"
    pa.write_text(json.dumps(old), encoding="utf-8")
    pb.write_text(json.dumps(new), encoding="utf-8")
    proc = _run("--input", str(pa), "--compare", str(pb), "--top", "10")
    assert proc.returncode == 0, proc.stderr
    assert "delta_error_count: +1" in proc.stdout
    assert "delta_warning_count: -1" in proc.stdout
    assert "new_codes:" in proc.stdout and "fresh" in proc.stdout
    assert "resolved_codes:" in proc.stdout and "w.old" in proc.stdout
    assert "new_messages" in proc.stdout and "fresh" in proc.stdout
    assert "resolved_messages" in proc.stdout and "w.old" in proc.stdout


def test_missing_input_nonzero(tmp_path: Path) -> None:
    proc = _run("--input", str(tmp_path / "nope.json"))
    assert proc.returncode == 1
    assert proc.stdout == ""
