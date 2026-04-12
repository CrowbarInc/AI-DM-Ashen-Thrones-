"""Unit tests for :mod:`game.final_emission_meta` (NA telemetry write/read helpers)."""

from __future__ import annotations

from game.final_emission_meta import (
    NARRATIVE_AUTHENTICITY_FEM_KEYS,
    build_narrative_authenticity_emission_trace,
    build_narrative_authenticity_trace_slice,
    default_narrative_authenticity_layer_meta,
    merge_narrative_authenticity_into_final_emission_meta,
    normalize_merged_na_telemetry_for_eval,
    resolve_narrative_authenticity_emission_status,
    slim_na_evidence,
    slim_na_metrics,
)


def test_default_layer_meta_has_all_fem_keys() -> None:
    d = default_narrative_authenticity_layer_meta()
    for k in NARRATIVE_AUTHENTICITY_FEM_KEYS:
        assert k in d


def test_merge_into_final_emission_meta_round_trip() -> None:
    fem: dict = {"final_route": "accept_candidate"}
    na = default_narrative_authenticity_layer_meta()
    na["narrative_authenticity_checked"] = True
    na["narrative_authenticity_failed"] = False
    na["narrative_authenticity_reason_codes"] = []
    na["narrative_authenticity_metrics"] = {"generic_filler_score": 0.1}
    merge_narrative_authenticity_into_final_emission_meta(fem, na)
    assert fem["narrative_authenticity_checked"] is True
    assert fem["final_route"] == "accept_candidate"


def test_emission_trace_terminal_statuses() -> None:
    contract = {"trace": {"rumor_turn_active": True, "rumor_turn_reason_codes": ["player_text:lex_rumor"]}}
    v_pass = {"checked": True, "passed": True, "failure_reasons": [], "metrics": {"rumor_turn_active": True}}
    t_pass = build_narrative_authenticity_emission_trace(v_pass, contract=contract)
    assert t_pass.get("narrative_authenticity_status") == "pass"
    assert "narrative_authenticity_metrics" in t_pass
    assert (t_pass.get("narrative_authenticity_trace") or {}).get("rumor_turn_active") is True

    v_relaxed = {
        **v_pass,
        "rumor_realism_relaxed_low_signal": True,
        "rumor_realism_relaxation_flags": {"brevity_alone": True},
    }
    t_relaxed = build_narrative_authenticity_emission_trace(v_relaxed, contract=contract)
    assert t_relaxed.get("narrative_authenticity_status") == "relaxed"
    assert t_relaxed.get("narrative_authenticity_rumor_relaxed_low_signal") is True

    v1 = {"checked": True, "passed": True, "failure_reasons": [], "metrics": {}}
    t_rep = build_narrative_authenticity_emission_trace(v1, contract=None, repaired=True, repair_mode="drop_adjacent_redundant_sentence")
    assert t_rep.get("narrative_authenticity_status") == "repaired"
    assert t_rep.get("narrative_authenticity_repair_modes") == ["drop_adjacent_redundant_sentence"]

    v_fail = {"checked": True, "passed": False, "failure_reasons": ["low_signal_generic_reply"], "metrics": {}}
    t_fail = build_narrative_authenticity_emission_trace(v_fail, contract=None, repaired=False, repair_failed=True)
    assert t_fail.get("narrative_authenticity_status") == "fail"
    assert "low_signal_generic_reply" in (t_fail.get("narrative_authenticity_reason_codes") or [])


def test_resolve_status_checked_failure_pre_repair_is_none() -> None:
    v = {"checked": True, "passed": False, "failure_reasons": ["x"], "metrics": {}}
    assert resolve_narrative_authenticity_emission_status(v, repaired=False, repair_failed=False) is None


def test_slim_helpers_stable() -> None:
    assert slim_na_metrics({"a": 1.234567, "b": None, "c": "ok"}) == {"a": 1.2346, "c": "ok"}
    ev = slim_na_evidence({"long": "x" * 200, "lst": list(range(10))})
    assert str(ev["long"]).endswith("…")
    assert len(ev["lst"]) <= 6


def test_trace_slice_contract_only() -> None:
    c = {"trace": {"rumor_turn_active": True, "rumor_trigger_spans": ["a", "b", "c", "d", "e", "f", "g"]}}
    sl = build_narrative_authenticity_trace_slice(None, contract=c)
    assert sl["rumor_turn_active"] is True
    assert len(sl.get("rumor_trigger_spans") or []) <= 6


def test_normalize_merged_na_for_eval_fills_none_nested() -> None:
    raw = {"narrative_authenticity_checked": True, "narrative_authenticity_metrics": None}
    n = normalize_merged_na_telemetry_for_eval(raw)
    assert n["narrative_authenticity_metrics"] == {}
    assert n["narrative_authenticity_trace"] == {}
    # Original mapping unchanged
    assert raw.get("narrative_authenticity_metrics") is None
