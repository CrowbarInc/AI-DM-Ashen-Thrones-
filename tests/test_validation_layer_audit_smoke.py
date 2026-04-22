"""Smoke tests for ``tools/validation_layer_audit.py`` (Objective #11 Block C).

Avoids brittle assertions on full report text; checks exit codes and coarse structure.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT = REPO_ROOT / "tools" / "validation_layer_audit.py"


def _run_audit(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AUDIT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_validation_layer_audit_runs_clean_on_game_tree() -> None:
    proc = _run_audit()
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "Likely ownership drift" in proc.stdout
    assert "validation_layer_separation.md" in proc.stdout


def test_validation_layer_audit_json_mode_structure() -> None:
    proc = _run_audit("--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data.get("executable_registry") == "game.validation_layer_contracts"
    assert isinstance(data.get("findings"), list)
    assert "summary" in data


def test_validation_layer_audit_flags_synthetic_evaluator_gate_import(tmp_path: Path) -> None:
    bad = tmp_path / "narrative_authenticity_eval.py"
    bad.write_text("from game.final_emission_gate import apply_final_emission_gate\n", encoding="utf-8")
    proc = _run_audit("--scan-root", str(tmp_path), "--strict", "--json")
    assert proc.returncode == 2, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    cats = {f.get("category") for f in data.get("findings", [])}
    assert "evaluator_drift" in cats
    assert data.get("summary", {}).get("likely_drift", 0) >= 1


def test_validation_layer_audit_strict_succeeds_when_clean_extra_root(tmp_path: Path) -> None:
    innocuous = tmp_path / "helper.py"
    innocuous.write_text("# not a classified bucket\nx = 1\n", encoding="utf-8")
    proc = _run_audit("--scan-root", str(tmp_path), "--strict")
    assert proc.returncode == 0, proc.stderr + proc.stdout
