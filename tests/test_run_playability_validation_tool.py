"""Unit tests for playability validation CLI helpers (no /api/chat)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_ROOT = Path(__file__).resolve().parents[1]
_TOOL = _ROOT / "tools" / "run_playability_validation.py"
_spec = importlib.util.spec_from_file_location("run_playability_validation_tool", _TOOL)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["run_playability_validation_tool"] = _mod
_spec.loader.exec_module(_mod)
summary_from_eval = _mod.summary_from_eval


def test_summary_from_eval_mirrors_evaluator_slices():
    eval_out = {
        "version": 1,
        "overall": {"score": 42, "rating": "acceptable", "passed": True},
        "axes": {
            "direct_answer": {"score": 10, "passed": True, "reasons": [], "signals": {}},
            "player_intent": {"score": 11, "passed": True, "reasons": [], "signals": {}},
            "logical_escalation": {"score": 12, "passed": False, "reasons": [], "signals": {}},
            "immersion": {"score": 9, "passed": False, "reasons": [], "signals": {}},
        },
        "summary": {
            "strengths": [],
            "failures": ["logical_escalation: weak (12/25)."],
            "warnings": ["immersion: borderline (9/25)."],
        },
    }
    s = summary_from_eval("p1_direct_answer", eval_out)
    assert s == {
        "report_version": 3,
        "scenario_id": "p1_direct_answer",
        "overall": eval_out["overall"],
        "axis_scores": {
            "direct_answer": 10,
            "player_intent": 11,
            "logical_escalation": 12,
            "immersion": 9,
        },
        "failures": eval_out["summary"]["failures"],
        "warnings": eval_out["summary"]["warnings"],
    }


def test_summary_from_eval_includes_dead_turn_report_when_passed():
    from game.dead_turn_report_visibility import build_dead_turn_run_report

    eval_out = {
        "version": 1,
        "overall": {"score": 1, "rating": "weak", "passed": False},
        "axes": {},
        "summary": {"strengths": [], "failures": [], "warnings": []},
    }
    turns_stub = [
        {
            "ok": True,
            "_final_emission_meta": {
                "dead_turn": {
                    "is_dead_turn": True,
                    "dead_turn_class": "retry_terminal_fallback",
                    "dead_turn_reason_codes": ["x"],
                    "validation_playable": False,
                    "manual_test_valid": False,
                }
            },
        }
    ]
    dead_rep = build_dead_turn_run_report(turns_stub)
    rollup = {"run_valid": False, "excluded_from_scoring": True, "invalidation_reason": "excluded_from_score:dead_turn:retry_terminal_fallback"}
    s = summary_from_eval("p1_direct_answer", eval_out, run_gameplay_validation=rollup, dead_turn_report=dead_rep)
    assert s["report_version"] == 3
    assert s["dead_turn_report"]["dead_turn_count"] == 1
    assert "retry_terminal_fallback" in (s["dead_turn_report"].get("banner") or "")
