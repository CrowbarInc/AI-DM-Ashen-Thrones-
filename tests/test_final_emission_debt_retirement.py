"""Audit tests for final-emission semantic debt retirement (see docs/final_emission_debt_retirement.md)."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from game.final_emission_contract import (
    FINAL_EMISSION_ALLOWED_RESPONSIBILITIES,
    FINAL_EMISSION_FORBIDDEN_IDENTIFIER_SUBSTRINGS,
    FINAL_EMISSION_FORBIDDEN_RESPONSIBILITIES,
)

pytestmark = pytest.mark.unit

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GAME = _REPO_ROOT / "game"


def _name_hits_forbidden_substrings(name: str) -> bool:
    low = name.lower()
    return any(sub in low for sub in FINAL_EMISSION_FORBIDDEN_IDENTIFIER_SUBSTRINGS)


def _collect_def_and_import_hits(tree: ast.AST) -> frozenset[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _name_hits_forbidden_substrings(node.name):
                out.add(node.name)
        elif isinstance(node, ast.ClassDef):
            if _name_hits_forbidden_substrings(node.name):
                out.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                nm = alias.asname or alias.name
                if nm == "*":
                    continue
                if nm and _name_hits_forbidden_substrings(nm):
                    out.add(nm)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                nm = alias.asname or alias.name
                if nm and _name_hits_forbidden_substrings(nm):
                    out.add(nm)
    return frozenset(out)


# Snapshot: every ``def`` / import alias in ``game/final_emission_*.py`` whose name contains a
# forbidden substring. Shrink this set as debt is retired; new hits fail the test until listed.
_EXPECTED_FORBIDDEN_SUBSTRING_SYMBOLS_BY_MODULE: dict[str, frozenset[str]] = {
    "final_emission_gate.py": frozenset(),
    "final_emission_repairs.py": frozenset(),
    "final_emission_boundary_contract.py": frozenset(),
    "final_emission_contract.py": frozenset(),
    "final_emission_meta.py": frozenset(),
    "final_emission_text.py": frozenset(),
    "final_emission_validators.py": frozenset(),
}


def test_contract_constants_are_nonempty() -> None:
    assert FINAL_EMISSION_ALLOWED_RESPONSIBILITIES
    assert FINAL_EMISSION_FORBIDDEN_RESPONSIBILITIES
    assert FINAL_EMISSION_FORBIDDEN_IDENTIFIER_SUBSTRINGS


def test_final_emission_modules_forbidden_substring_snapshot() -> None:
    """Fail on new forbidden-pattern defs/imports; require snapshot update when debt changes."""
    paths = sorted(_GAME.glob("final_emission*.py"))
    assert paths, "expected game/final_emission*.py"
    by_name = {p.name: p for p in paths}
    assert set(by_name) == set(_EXPECTED_FORBIDDEN_SUBSTRING_SYMBOLS_BY_MODULE), (
        "Add/remove game/final_emission*.py entries in _EXPECTED_FORBIDDEN_SUBSTRING_SYMBOLS_BY_MODULE"
    )
    for name, path in by_name.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found = _collect_def_and_import_hits(tree)
        expected = _EXPECTED_FORBIDDEN_SUBSTRING_SYMBOLS_BY_MODULE[name]
        assert found == expected, (
            f"{name}: forbidden-substring symbols mismatch.\n"
            f"  found={sorted(found)}\n"
            f"  expected={sorted(expected)}\n"
            f"  extra={sorted(found - expected)}\n"
            f"  missing={sorted(expected - found)}"
        )


# Curated semantic-composition helpers whose names do not match the forbidden-substring list.
_REPAIRS_SEMANTIC_DEBT_NO_SUBSTRING: frozenset[str] = frozenset()

_REPAIRS_SEMANTIC_DEBT_REGISTRY: frozenset[str] = frozenset()

# Exact ``def`` / ``class`` / import-alias names Block B removed from final emission (belt-and-suspenders
# alongside :data:`FINAL_EMISSION_FORBIDDEN_IDENTIFIER_SUBSTRINGS`).
_BLOCK_B_RETIRED_EXACT_SYMBOL_NAMES: frozenset[str] = frozenset(
    {
        "repair_answer_shape_primacy",
        "micro_smooth",
        "restore_spoken",
        "normalize_dialogue_cadence",
        "trim_leading_expository",
        "merge_substantive",
        "fallback_template",
        "rewrite_meta_fallback",
        "smooth_repaired",
        "dialogue_cadence",
        "spoken_opening",
    }
)


def _collect_exact_block_b_symbol_hits(tree: ast.AST) -> frozenset[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nm = node.name
            base = nm.lstrip("_")
            if nm in _BLOCK_B_RETIRED_EXACT_SYMBOL_NAMES or base in _BLOCK_B_RETIRED_EXACT_SYMBOL_NAMES:
                out.add(nm)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                nm = alias.asname or alias.name
                if nm == "*":
                    continue
                if nm in _BLOCK_B_RETIRED_EXACT_SYMBOL_NAMES:
                    out.add(nm)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                nm = alias.asname or alias.name
                if nm in _BLOCK_B_RETIRED_EXACT_SYMBOL_NAMES:
                    out.add(nm)
    return frozenset(out)


def test_block_b_retired_helper_exact_names_not_reintroduced() -> None:
    """Fail if a removed Block B helper name is reintroduced as a live identifier (not string data)."""
    hits_by: dict[str, frozenset[str]] = {}
    for path in sorted(_GAME.glob("final_emission*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hits = _collect_exact_block_b_symbol_hits(tree)
        if hits:
            hits_by[path.name] = hits
    assert not hits_by, f"Block B retired exact symbol(s) reintroduced: {hits_by!r}"


def test_final_emission_repairs_semantic_debt_inventory() -> None:
    """Substring hits plus curated non-substring debt must match the registry (no drift)."""
    path = _GAME / "final_emission_repairs.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    all_funcs = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    hits = {n for n in all_funcs if _name_hits_forbidden_substrings(n)}
    assert hits.isdisjoint(_REPAIRS_SEMANTIC_DEBT_NO_SUBSTRING)
    assert _REPAIRS_SEMANTIC_DEBT_REGISTRY == hits | _REPAIRS_SEMANTIC_DEBT_NO_SUBSTRING
    assert _REPAIRS_SEMANTIC_DEBT_REGISTRY <= all_funcs, sorted(_REPAIRS_SEMANTIC_DEBT_REGISTRY - all_funcs)
