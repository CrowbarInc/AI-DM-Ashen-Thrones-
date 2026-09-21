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
_write_observability_artifacts = _mod._write_observability_artifacts
PlayabilityScenario = _mod.PlayabilityScenario


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
        "semantic_result": None,
        "mandatory_gates": None,
        "diagnostic_quality": None,
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


def test_observability_artifacts_include_transcript_evaluation_and_state(tmp_path: Path) -> None:
    spec = PlayabilityScenario(
        "p_observe",
        "Observer smoke.",
        ("What do I see?",),
    )
    turns = [
        {
            "turn_index": 0,
            "player_prompt": "What do I see?",
            "gm_text": "You see the gate.",
            "resolution_kind": "observe",
            "api_ok": True,
            "api_error": None,
            "playability_eval": {"overall": {"score": 75, "rating": "acceptable", "passed": True}},
            "narrative_authenticity_eval": {"overall": {"passed": True}},
            "dead_turn_visibility": {"dead_turn_detected": False},
            "_final_emission_meta": {"dead_turn": {"is_dead_turn": False}},
        }
    ]
    summary = {
        "overall": {"score": 75, "rating": "acceptable", "passed": True},
        "failures": [],
        "warnings": [],
        "run_gameplay_validation": {"run_valid": True},
        "dead_turn_report": {"dead_turn_count": 0},
    }

    _write_observability_artifacts(
        run_dir=tmp_path,
        run_id="run1",
        spec=spec,
        started_at="2026-09-17T00:00:00+00:00",
        finished_at="2026-09-17T00:00:01+00:00",
        turns=turns,
        summary=summary,
        state_before={"session": {"turn_counter": 0}},
        state_after={"session": {"turn_counter": 1}},
        apply_reset=True,
        caller_kind="test",
        base_url=None,
        upstream_dependent_run_gate={"startup_run_valid": True},
    )

    transcript = (tmp_path / "transcript.md").read_text(encoding="utf-8")
    evaluation = (tmp_path / "evaluation.json").read_text(encoding="utf-8")
    metadata = (tmp_path / "metadata.json").read_text(encoding="utf-8")
    assert "### PLAYER" in transcript
    assert "What do I see?" in transcript
    assert "You see the gate." in transcript
    assert '"result": "PASS"' in evaluation
    assert "semantic_result" in evaluation
    assert "mandatory_gates" in transcript
    assert (tmp_path / "state_before.json").is_file()
    assert (tmp_path / "state_after.json").is_file()
    assert "fixed scripted natural-language prompts" in metadata
