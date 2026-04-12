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
        "report_version": 1,
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
