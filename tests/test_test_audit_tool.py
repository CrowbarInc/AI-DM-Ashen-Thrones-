"""Unit tests for ``tools/test_audit.py`` helpers (no full-suite pytest collect)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "test_audit.py"


@pytest.fixture(scope="module")
def audit_mod():
    name = "_test_audit_tool_under_test"
    spec = importlib.util.spec_from_file_location(name, TOOL_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_parse_game_import_from_game_package(audit_mod) -> None:
    src = "from game import api\nfrom game.final_emission_gate import apply_final_emission_gate\n"
    mods = audit_mod._parse_game_import_modules(src)
    assert "game.api" in mods
    assert "game.final_emission_gate" in mods


def test_game_import_roots_dedupes(audit_mod) -> None:
    roots = audit_mod._game_import_roots(["game.final_emission_gate", "game.final_emission_repairs", "game.api"])
    assert sorted(roots) == ["api", "final_emission_gate", "final_emission_repairs"]


def test_architecture_layer_prefers_transcript_signals(audit_mod) -> None:
    fp = "tests/test_mixed_state_recovery_regressions.py"
    src = "from tests.helpers.transcript_runner import run_transcript\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "regression")
    assert audit_mod._primary_architecture_layer(scores) == "transcript"


def test_architecture_layer_prefers_gate_when_gate_imported(audit_mod) -> None:
    fp = "tests/test_final_emission_gate.py"
    src = "from game.final_emission_gate import apply_final_emission_gate\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "mixed/unclear")
    assert scores["gate"] >= 8
    assert audit_mod._primary_architecture_layer(scores) == "gate"


def test_architecture_layer_smoke_filename(audit_mod) -> None:
    fp = "tests/test_behavioral_gauntlet_smoke.py"
    src = "# no imports\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "mixed/unclear")
    assert audit_mod._primary_architecture_layer(scores) == "smoke"


def test_likely_ownership_theme_uses_majority_feature(audit_mod) -> None:
    theme = audit_mod._likely_ownership_theme(
        "tests/test_clue_knowledge.py",
        {"clue system": 5, "general": 1},
        ["clue"],
    )
    assert "clue" in theme.lower()


def test_overlap_hints_surface_shadowing(audit_mod) -> None:
    hints = audit_mod._overlap_hints_for_file(
        "tests/test_x.py",
        "from game.final_emission_gate import x\nfrom game.prompt_context import y\n",
        ["game.final_emission_gate", "game.prompt_context"],
        ["final_emission_gate", "prompt_context"],
        True,
        ["test_dup_name"],
        "routing",
        "gate",
    )
    joined = " ".join(hints)
    assert "module_shadowed_duplicate_test_names" in joined
    assert "cross_file_same_test_base_name" in joined
    assert "gate_stack_adjacent_to_prompt_context" in joined


def test_keyword_overlap_hints_multi_hit(audit_mod) -> None:
    body = "route routing dialogue_lock"
    hints = audit_mod._test_keyword_overlap_hints("tests/test_foo.py::test_bar", body)
    assert any(h.startswith("multi_keyword:") for h in hints)
