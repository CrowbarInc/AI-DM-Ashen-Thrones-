"""Unit tests for deterministic narrative authenticity proof-layer scoring."""

from __future__ import annotations

import pytest

from game.narrative_authenticity_eval import evaluate_narrative_authenticity


def _resp(*, text: str, fem: dict) -> dict:
    return {"ok": True, "gm_output": {"player_facing_text": text, "_final_emission_meta": fem}}


def _resp_sidecar(*, text: str, fem: dict) -> dict:
    """Emit canonical post-gate envelope shape (FEM in gm_output_debug.emission_debug_lane)."""
    return {
        "ok": True,
        "gm_output": {"player_facing_text": text},
        "gm_output_debug": {"emission_debug_lane": {"_final_emission_meta": fem}},
    }


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


def test_supporting_metrics_includes_shipped_na_status_and_trace_for_repaired() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": True,
        "narrative_authenticity_status": "repaired",
        "narrative_authenticity_trace": {"rumor_turn_active": True},
        "narrative_authenticity_reason_codes": [],
        "narrative_authenticity_metrics": {"rumor_turn_active": True},
        "narrative_authenticity_evidence": {},
    }
    r = evaluate_narrative_authenticity({}, _resp(text="He nods toward the yard.", fem=fem), fem)
    sup = r.get("supporting_metrics") or {}
    assert sup.get("narrative_authenticity_status") == "repaired"
    assert (sup.get("narrative_authenticity_trace") or {}).get("rumor_turn_active") is True


def test_na_verdict_clean_pass_and_rumor_axes() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_status": "pass",
        "narrative_authenticity_trace": {"rumor_turn_active": True},
        "narrative_authenticity_metrics": {"rumor_turn_active": True, "rumor_signal_count": 2},
        "narrative_authenticity_evidence": {},
    }
    r = evaluate_narrative_authenticity({}, _resp(text="Dock talk says the gate holds.", fem=fem), fem)
    assert r["narrative_authenticity_verdict"] == "clean_pass"
    assert r["rumor_realism_axes"]["rumor_repair_success"] == 5


def test_na_verdict_relaxed_pass() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_status": "relaxed",
        "narrative_authenticity_rumor_relaxed_low_signal": True,
        "narrative_authenticity_relaxation_flags": {"brevity_alone": True},
        "narrative_authenticity_trace": {"rumor_turn_active": True, "rumor_relaxation_flags": {"brevity_alone": True}},
        "narrative_authenticity_metrics": {"rumor_turn_active": True},
        "narrative_authenticity_evidence": {},
    }
    r = evaluate_narrative_authenticity({}, _resp(text="They say patrols doubled.", fem=fem), fem)
    assert r["narrative_authenticity_verdict"] == "relaxed_pass"
    assert r["rumor_realism_axes"]["rumor_relaxation_correctness"] == 5


def test_na_verdict_repaired_pass_low_signal_repair_mode() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": True,
        "narrative_authenticity_status": "repaired",
        "narrative_authenticity_repair_mode": "compress_generic_rumor_shell",
        "narrative_authenticity_repair_modes": ["compress_generic_rumor_shell"],
        "narrative_authenticity_trace": {"rumor_turn_active": True},
        "narrative_authenticity_metrics": {"rumor_turn_active": True},
        "narrative_authenticity_evidence": {},
    }
    r = evaluate_narrative_authenticity({}, _resp(text="He mutters a tightened rumor line.", fem=fem), fem)
    assert r["narrative_authenticity_verdict"] == "repaired_pass"
    assert r["rumor_realism_axes"]["rumor_repair_success"] == 5
    assert any("compress_generic_rumor_shell" in str(x) for x in r["rumor_realism_axis_reasons"]["rumor_repair_success"])


def test_na_verdict_fail_and_distinct_from_unchecked() -> None:
    fem_fail = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": True,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_status": "fail",
        "narrative_authenticity_reason_codes": ["low_signal_generic_reply"],
        "narrative_authenticity_metrics": {"generic_filler_score": 0.7},
        "narrative_authenticity_evidence": {},
    }
    r_fail = evaluate_narrative_authenticity({}, _resp(text="The mist holds.", fem=fem_fail), fem_fail)
    assert r_fail["narrative_authenticity_verdict"] == "fail"
    assert r_fail["passed"] is False

    fem_skip = {
        "narrative_authenticity_checked": False,
        "narrative_authenticity_skip_reason": "fallback_uncertainty_brief_compat",
    }
    r_skip = evaluate_narrative_authenticity({}, _resp(text="hard to say", fem=fem_skip), fem_skip)
    assert r_skip["narrative_authenticity_verdict"] == "unchecked"
    assert r_skip["passed"] is True


def test_rumor_turn_trace_absent_vs_present_in_state_hygiene() -> None:
    fem_ok = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_status": "pass",
        "narrative_authenticity_trace": {},
        "narrative_authenticity_metrics": {"rumor_turn_active": True},
        "narrative_authenticity_evidence": {},
    }
    r_ok = evaluate_narrative_authenticity({}, _resp(text="No rumor trace slice.", fem=fem_ok), fem_ok)
    assert r_ok["rumor_realism_axes"]["rumor_state_hygiene"] == 2

    fem_match = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_status": "pass",
        "narrative_authenticity_trace": {"rumor_turn_active": True},
        "narrative_authenticity_metrics": {"rumor_turn_active": True},
        "narrative_authenticity_evidence": {},
    }
    r_m = evaluate_narrative_authenticity({}, _resp(text="Rumor trace aligned.", fem=fem_match), fem_match)
    assert r_m["rumor_realism_axes"]["rumor_state_hygiene"] == 5


def test_missing_telemetry_verdict() -> None:
    r = evaluate_narrative_authenticity({}, {"ok": True, "gm_output": {"player_facing_text": "x"}}, {})
    assert r["narrative_authenticity_verdict"] == "missing_telemetry"


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


def test_eval_reads_fem_from_sidecar_lane_not_only_legacy_top_level() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_status": "pass",
        "narrative_authenticity_trace": {"rumor_turn_active": True},
        "narrative_authenticity_metrics": {"rumor_turn_active": True, "rumor_signal_count": 2},
        "narrative_authenticity_evidence": {},
    }
    payload = _resp_sidecar(text="Dock talk says the gate holds.", fem=fem)
    r = evaluate_narrative_authenticity({}, payload, {})
    assert r["passed"] is True
    assert r["narrative_authenticity_verdict"] in {"clean_pass", "relaxed_pass", "repaired_pass"}
    sup = r.get("supporting_metrics") or {}
    assert sup.get("narrative_authenticity_status") == "pass"
    assert (sup.get("narrative_authenticity_trace") or {}).get("rumor_turn_active") is True


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
    # Public surface invariant: no debug/meta keys on gm_output.
    for forbidden in (
        "_final_emission_meta",
        "debug_notes",
        "stage_diff_telemetry",
        "dead_turn",
        "reason_codes",
        "internal_state",
        "prompt_debug",
    ):
        assert forbidden not in gm
    dbg = data.get("gm_output_debug")
    assert isinstance(dbg, dict)
    assert isinstance(dbg.get("emission_debug_lane"), dict)
    assert "_final_emission_meta" in dbg["emission_debug_lane"]
    na = evaluate_narrative_authenticity({}, data, {})
    assert "scores" in na and "passed" in na
    assert set(na["scores"]) == {
        "signal_gain",
        "anti_echoing",
        "followup_evolution",
        "non_generic_specificity",
        "npc_voice_grounding",
    }
