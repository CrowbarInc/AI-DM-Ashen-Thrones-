"""Static drift guard: single registry source for public narrative_plan prompt top keys.

Narrow checks only — no repo-wide string bans, no docs coupling, no unrelated registries.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from game.contract_registry import PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS
from game.narration_plan_bundle import public_narrative_plan_projection_for_prompt

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _parse(rel: str) -> ast.Module:
    tree = ast.parse(_read(rel))
    assert isinstance(tree, ast.Module)
    return tree


def _frozenset_literal_string_elements(node: ast.expr) -> frozenset[str] | None:
    """If *node* is ``frozenset({...})`` with only string constants, return those strings."""
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if not isinstance(func, ast.Name) or func.id != "frozenset":
        return None
    if not node.args:
        return None
    arg0 = node.args[0]
    if not isinstance(arg0, ast.Set):
        return None
    keys: list[str] = []
    for elt in arg0.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            keys.append(elt.value)
        else:
            return None
    return frozenset(keys)


def _module_level_assign_value(tree: ast.Module, name: str) -> ast.expr | None:
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                return node.value
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return node.value
    return None


def _iter_frozenset_literal_string_sets(tree: ast.AST) -> list[frozenset[str]]:
    found: list[frozenset[str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            lit = _frozenset_literal_string_elements(node)
            if lit is not None:
                found.append(lit)
    return found


def test_planner_convergence_audit_references_registry_public_keys() -> None:
    rel = "tools/planner_convergence_audit.py"
    src = _read(rel)
    assert "PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS" in src
    assert "from game.contract_registry import PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS" in src


def test_planner_convergence_audit_approved_keys_not_inline_duplicate_frozenset() -> None:
    tree = _parse("tools/planner_convergence_audit.py")
    rhs = _module_level_assign_value(tree, "APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS")
    assert rhs is not None, "expected module-level APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS binding"
    assert isinstance(rhs, ast.Name) and rhs.id == "PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS", (
        "APPROVED_PROMPT_NARRATIVE_PLAN_TOP_KEYS must alias PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS "
        "(no inline frozenset duplicate of the approval list)"
    )


def test_planner_convergence_static_audit_references_registry_public_keys() -> None:
    rel = "tests/test_planner_convergence_static_audit.py"
    src = _read(rel)
    assert "PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS" in src
    assert "from game.contract_registry import PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS" in src


def test_planner_convergence_static_audit_no_second_full_duplicate_approval_frozenset() -> None:
    tree = _parse("tests/test_planner_convergence_static_audit.py")
    for lit in _iter_frozenset_literal_string_sets(tree):
        assert lit != PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS, (
            "test_planner_convergence_static_audit must not embed a full duplicate "
            "frozenset of PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS; use the registry import."
        )


def test_public_projection_top_level_keys_match_registry() -> None:
    """Maximal plan (all projected branches + extra keys) → projection keys == registry."""
    maximal: dict[str, Any] = {
        "version": 1,
        "narrative_mode": "standard",
        "role_allocation": {"allocation_version": 1},
        "scene_anchors": {"anchors_version": 1},
        "active_pressures": {"pressures_version": 1},
        "required_new_information": [{"id": "info_1"}],
        "allowable_entity_references": [{"id": "ent_1"}],
        "narrative_roles": {"roles_version": 1},
        "narrative_mode_contract": {"contract_version": 1},
        "scene_opening": {"opening_version": 1},
        "action_outcome": {"outcome_version": 1},
        "transition_node": {"transition_version": 1},
        "answer_exposition_plan": {"plan_version": 1},
        "debug": {"must_not_appear_in_projection": True},
        "resolution_meta": {"strip": True},
        "recent_compressed_events": ["noise"],
    }
    projected = public_narrative_plan_projection_for_prompt(maximal)
    assert isinstance(projected, dict)
    assert frozenset(projected.keys()) == PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS
