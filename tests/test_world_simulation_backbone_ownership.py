"""Objective #9 Block D: structural and ownership invariants for the world simulation backbone."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from game.state_authority import WORLD_STATE, can_owner_mutate_domain
from game.world_progression import iter_world_progression_nodes

pytestmark = pytest.mark.unit


def test_state_authority_allows_world_progression_to_mutate_world_state():
    assert can_owner_mutate_domain("game.world_progression", WORLD_STATE)


def test_state_authority_allows_world_routing_to_mutate_world_state():
    assert can_owner_mutate_domain("game.world", WORLD_STATE)


def test_repo_game_sources_do_not_persist_world_progression_shadow_root_on_world_dict():
    root = Path(__file__).resolve().parents[1] / "game"
    for path in sorted(root.rglob("*.py")):
        if "test" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if 'world["progression"]' in text or "world['progression']" in text:
            pytest.fail(f"world document must not gain progression subtree: {path.relative_to(root.parent)}")


def test_session_documents_do_not_define_world_progression_assignment_in_defaults():
    """Sanity: default session factory should not introduce ``session['world_progression']``."""
    from game.defaults import default_session

    s = default_session()
    assert "world_progression" not in s


def test_progression_iterator_covers_only_persistent_supported_kinds():
    from game.world import ensure_defaults

    w = {
        "projects": [],
        "factions": [],
        "event_log": [],
        "world_state": {"flags": {}, "counters": {"n": 1}, "clocks": {}},
    }
    ensure_defaults(w)
    kinds = {n.get("kind") for n in iter_world_progression_nodes(w)}
    assert kinds <= {
        "project",
        "faction_pressure",
        "faction_agenda",
        "world_clock",
        "world_flag",
    }


def test_prompt_context_source_has_no_ctir_builder_coupling():
    """Boundary: CTIR is built in API/runtime; prompt_context consumes attachments only."""
    root = Path(__file__).resolve().parents[1] / "game"
    blob = (root / "prompt_context.py").read_text(encoding="utf-8")
    assert "build_ctir" not in blob
    assert "from game.ctir import" not in blob
    assert "import game.ctir\n" not in blob
    assert "import game.ctir\r\n" not in blob


def test_prompt_context_imports_compose_slice_from_world_progression_not_ctir():
    pc_path = Path(__file__).resolve().parents[1] / "game" / "prompt_context.py"
    tree = ast.parse(pc_path.read_text(encoding="utf-8"))
    imported_from_wp = False
    imported_compose_from_elsewhere = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = {alias.name for alias in node.names}
            if mod == "game.world_progression":
                imported_from_wp = True
                if "compose_ctir_world_progression_slice" in names:
                    pass
            if "compose_ctir_world_progression_slice" in names and mod not in ("game.world_progression", None):
                imported_compose_from_elsewhere = True
    assert imported_from_wp
    assert not imported_compose_from_elsewhere
