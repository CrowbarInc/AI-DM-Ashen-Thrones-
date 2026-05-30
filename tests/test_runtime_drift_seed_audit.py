"""Audit replay-sensitive runtime paths for process-randomized seed seams."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
REPLAY_SENSITIVE_SEED_PATHS = (
    ROOT / "game" / "speaker_contract_enforcement.py",
    ROOT / "game" / "final_emission_gate.py",
    ROOT / "game" / "final_emission_repairs.py",
    ROOT / "game" / "final_emission_replay_projection.py",
    ROOT / "game" / "final_emission_visibility_fallback.py",
    ROOT / "game" / "opening_deterministic_fallback.py",
    ROOT / "game" / "diegetic_fallback_narration.py",
)
PROCESS_RANDOMIZED_MODULES = {"random", "uuid", "time"}


def _seed_seam_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    randomized_aliases: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                if root_name in PROCESS_RANDOMIZED_MODULES:
                    local_name = alias.asname or root_name
                    randomized_aliases.add(local_name)
                    violations.append(f"{path.name}:{node.lineno}: imports process-randomized module {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module_root = (node.module or "").split(".", 1)[0]
            if module_root in PROCESS_RANDOMIZED_MODULES:
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    randomized_aliases.add(local_name)
                violations.append(f"{path.name}:{node.lineno}: imports from process-randomized module {node.module}")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "hash":
            violations.append(f"{path.name}:{node.lineno}: calls process-randomized hash()")
        elif isinstance(func, ast.Name) and func.id in randomized_aliases:
            violations.append(f"{path.name}:{node.lineno}: calls process-randomized {func.id}()")
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in randomized_aliases:
            violations.append(f"{path.name}:{node.lineno}: calls process-randomized {func.value.id}.{func.attr}()")

    return violations


def test_replay_sensitive_seed_paths_do_not_use_process_randomized_seed_material() -> None:
    violations: list[str] = []
    for path in REPLAY_SENSITIVE_SEED_PATHS:
        violations.extend(_seed_seam_violations(path))

    assert violations == []

