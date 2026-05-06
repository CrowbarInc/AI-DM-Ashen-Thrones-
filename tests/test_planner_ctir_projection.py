"""Planner CTIR projection seam — ownership vs prompt_context packager."""

from __future__ import annotations

import ast
import inspect

import pytest

import game.planner_head_state as planner_hs
import game.planner_ctir_projection as pcp
import game.prompt_context as pc


pytestmark = pytest.mark.unit


def test_planner_head_state_imports_projection_not_prompt_context_helpers() -> None:
    src = inspect.getsource(planner_hs)
    tree = ast.parse(src)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "game.prompt_context":
                names.update(alias.name for alias in node.names)
    offenders = names & {
        "_CLASSIFIER_ONLY_INTENT_KEYS",
        "_compress_recent_log",
        "_compress_scene_runtime",
        "_compress_session",
        "_ctir_to_prompt_semantics",
        "_session_view_overlay_from_ctir_interaction",
        "_world_progression_projection_for_prompt",
        "build_active_interlocutor_export",
        "build_response_policy",
        "derive_narration_obligations",
        "deterministic_interlocutor_answer_style_hints",
    }
    assert not offenders, f"planner_head_state must not import these from prompt_context: {sorted(offenders)}"


def test_prompt_context_reexports_projection_symbols() -> None:
    """Backward-compat bundle: same function objects as planner_ctir_projection."""
    assert pc.build_response_policy is pcp.build_response_policy
    assert pc.derive_narration_obligations is pcp.derive_narration_obligations
    assert pc._ctir_to_prompt_semantics is pcp._ctir_to_prompt_semantics
    assert pc.build_answer_completeness_contract is pcp.build_answer_completeness_contract


def test_compression_caps_aligned_with_prompt_context() -> None:
    assert pcp.MAX_RECENT_LOG == pc.MAX_RECENT_LOG
    assert pcp.MAX_LOG_ENTRY_SNIPPET == pc.MAX_LOG_ENTRY_SNIPPET
