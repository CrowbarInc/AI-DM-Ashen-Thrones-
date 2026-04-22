"""Block D regression lock for Objective #11 (validation layer separation).

Focused invariants only: registry vs docs, import seams, audit behavior, metadata separation.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from game import narrative_authenticity as na_mod
from game import narrative_authenticity_eval as nae_mod
from game import prompt_context as pc_mod
from game import validation_layer_contracts as vlc

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_CONTRACT = REPO_ROOT / "docs" / "validation_layer_separation.md"
AUDIT = REPO_ROOT / "tools" / "validation_layer_audit.py"


def _game_submodule_roots_from_source(source: str) -> set[str]:
    tree = ast.parse(source)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("game."):
            out.add(node.module[len("game.") :].split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("game."):
                    out.add(name[len("game.") :].split(".", 1)[0])
    return out


def test_main_contract_doc_mentions_each_canonical_layer_id() -> None:
    text = MAIN_CONTRACT.read_text(encoding="utf-8")
    for layer in vlc.CANONICAL_VALIDATION_LAYERS:
        assert f"`{layer}`" in text, f"missing canonical layer id {layer!r} in {MAIN_CONTRACT}"


def test_main_contract_doc_states_closeout_status() -> None:
    text = MAIN_CONTRACT.read_text(encoding="utf-8")
    assert "Block D closeout" in text
    assert "satisfied with narrow fenced residue" in text


def test_na_live_module_does_not_import_gate_or_evaluator_surfaces() -> None:
    src = Path(na_mod.__file__).read_text(encoding="utf-8")
    roots = _game_submodule_roots_from_source(src)
    forbidden = {"final_emission_gate", "final_emission_repairs", "narrative_authenticity_eval"}
    assert not (roots & forbidden), f"NA must not import gate/evaluator surfaces: {roots & forbidden}"


def test_planner_prompt_context_does_not_import_gate_or_evaluator_surfaces() -> None:
    src = Path(pc_mod.__file__).read_text(encoding="utf-8")
    roots = _game_submodule_roots_from_source(src)
    forbidden = {"final_emission_gate", "final_emission_repairs", "narrative_authenticity_eval"}
    assert not (roots & forbidden), f"planner-class prompt_context must not import: {roots & forbidden}"


def test_offline_evaluator_import_allowlist_matches_audit_policy() -> None:
    """Evaluator may read meta + registry only (see tools/validation_layer_audit.py)."""
    src = Path(nae_mod.__file__).read_text(encoding="utf-8")
    roots = _game_submodule_roots_from_source(src)
    allowed = {"final_emission_meta", "validation_layer_contracts"}
    assert roots <= allowed, f"evaluator game imports {roots!r} exceed allowlist {allowed!r}"


def test_audit_json_reports_benign_gate_split_on_game_tree() -> None:
    proc = subprocess.run(
        [sys.executable, str(AUDIT), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    benign = data.get("benign_within_layer") or []
    joined = " ".join(benign)
    assert "final_emission_gate.py" in joined and "final_emission_repairs.py" in joined


def test_audit_strict_flags_synthetic_na_importing_repairs(tmp_path: Path) -> None:
    bad = tmp_path / "narrative_authenticity.py"
    bad.write_text("from game.final_emission_repairs import validate_response_delta\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(AUDIT), "--scan-root", str(tmp_path), "--strict", "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    assert data.get("summary", {}).get("likely_drift", 0) >= 1
    cats = {f.get("category") for f in data.get("findings", [])}
    assert "na_response_delta_drift" in cats
