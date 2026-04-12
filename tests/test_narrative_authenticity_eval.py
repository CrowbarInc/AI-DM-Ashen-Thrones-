"""Unit tests for deterministic narrative authenticity proof-layer scoring."""

from __future__ import annotations

import pytest

from game.narrative_authenticity_eval import evaluate_narrative_authenticity


def _resp(*, text: str, fem: dict) -> dict:
    return {"ok": True, "gm_output": {"player_facing_text": text, "_final_emission_meta": fem}}


def test_missing_telemetry_fails_closed() -> None:
    r = evaluate_narrative_authenticity({}, {"ok": True, "gm_output": {"player_facing_text": "x"}}, {})
    assert r["passed"] is False
    assert r["scores"]["signal_gain"] == 0
    assert "missing_narrative_authenticity_telemetry" in r["reasons"]


def test_skip_not_checked_neutral_scores() -> None:
    fem = {
        "narrative_authenticity_checked": False,
        "narrative_authenticity_skip_reason": "fallback_uncertainty_brief_compat",
    }
    r = evaluate_narrative_authenticity({}, _resp(text="A guard shrugs.", fem=fem), fem)
    assert r["scores"]["signal_gain"] == 3
    assert r["passed"] is True


def test_gate_failed_unrepaired_hard_fail() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": True,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_reason_codes": ["low_signal_generic_reply"],
        "narrative_authenticity_metrics": {"generic_filler_score": 0.61, "signal_markers_detected": 0},
    }
    r = evaluate_narrative_authenticity(
        {"prior_gm_text": "The gate is crowded."},
        _resp(text="He pauses.", fem=fem),
        fem,
    )
    assert r["passed"] is False
    assert r["scores"]["signal_gain"] == 0
    assert r["scores"]["non_generic_specificity"] == 0
    assert "narrative_authenticity_gate_failed_unrepaired" in r["reasons"]


def test_repaired_failure_clears_pass_when_scores_ok() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": True,
        "narrative_authenticity_reason_codes": [],
        "narrative_authenticity_metrics": {"generic_filler_score": 0.12, "signal_markers_detected": 2},
    }
    text = (
        'Captain Morrow studies the ledger. "East gate by midnight—'
        'that is what the clerk heard," she says, pointing two fingers toward the yard.'
    )
    r = evaluate_narrative_authenticity({"prior_gm_text": "Prior beat about the watch."}, _resp(text=text, fem=fem), fem)
    assert r["passed"] is True
    assert r["scores"]["signal_gain"] == 5
    assert r["supporting_metrics"]["narrative_authenticity_metrics"]["generic_filler_score"] == 0.12


def test_dialogue_echo_reason_caps_anti_echoing() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": True,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_reason_codes": ["dialogue_echoes_prior_narration"],
        "narrative_authenticity_metrics": {"quote_narration_overlap": 0.62},
    }
    r = evaluate_narrative_authenticity({}, _resp(text="Echo case.", fem=fem), fem)
    assert r["scores"]["anti_echoing"] == 0
    assert r["passed"] is False


def test_determinism_same_inputs_same_output() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_metrics": {
            "generic_filler_score": 0.2,
            "followup_overlap": 0.5,
            "signal_markers_detected": 1,
        },
    }
    text = "The sergeant leans in. \"If you want names, start with the harbor clerk.\""
    payload = _resp(text=text, fem=fem)
    a = evaluate_narrative_authenticity({"prior_gm_text": "x" * 40}, payload, fem)
    b = evaluate_narrative_authenticity({"prior_gm_text": "x" * 40}, payload, fem)
    assert a == b


@pytest.mark.integration
def test_api_chat_includes_fem_for_eval() -> None:
    from fastapi.testclient import TestClient

    from game.api import app

    with TestClient(app) as client:
        r = client.post("/api/chat", json={"text": "I look around."})
        assert r.status_code == 200
        data = r.json()
    assert isinstance(data, dict)
    gm = data.get("gm_output")
    assert isinstance(gm, dict)
    assert "_final_emission_meta" in gm
    na = evaluate_narrative_authenticity({}, data, {})
    assert "scores" in na and "passed" in na
    assert set(na["scores"]) == {
        "signal_gain",
        "anti_echoing",
        "followup_evolution",
        "non_generic_specificity",
        "npc_voice_grounding",
    }
