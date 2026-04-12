"""AER4 regression: shipped NA + rumor realism state, ordering, relaxation, telemetry (tests only)."""

from __future__ import annotations

import inspect
import pytest

from game.final_emission_repairs import _apply_narrative_authenticity_layer
from game.narrative_authenticity import (
    build_narrative_authenticity_contract,
    build_narrative_authenticity_emission_trace,
    repair_narrative_authenticity_minimal,
    validate_narrative_authenticity,
)
from game.narrative_authenticity_eval import evaluate_narrative_authenticity
from game.stage_diff_telemetry import snapshot_turn_stage


def _gm_with_na(contract: dict) -> dict:
    return {"response_policy": {"narrative_authenticity": contract}}


# --- 1) Terminal state model ---


def test_emission_status_clean_pass_not_relaxed():
    c = build_narrative_authenticity_contract()
    v = validate_narrative_authenticity("The sergeant leans in without echoing herself.", c, gm_output=None)
    tr = build_narrative_authenticity_emission_trace(v, contract=c, repaired=False, repair_failed=False)
    assert tr.get("narrative_authenticity_status") == "pass"
    assert tr.get("narrative_authenticity_rumor_relaxed_low_signal") is None
    assert tr.get("narrative_authenticity_relaxation_flags") in (None, {})
    assert tr.get("narrative_authenticity_skip_reason") is None
    assert tr.get("narrative_authenticity_repair_modes") == []


def test_emission_status_relaxed_pass_surfaces_flags():
    c = build_narrative_authenticity_contract()
    v = {
        "checked": True,
        "passed": True,
        "failure_reasons": [],
        "metrics": {"rumor_turn_active": True},
        "evidence": {},
        "rumor_realism_relaxed_low_signal": True,
        "rumor_realism_relaxation_flags": {"fallback_uncertainty_active": True},
    }
    tr = build_narrative_authenticity_emission_trace(v, contract=c, repaired=False, repair_failed=False)
    assert tr["narrative_authenticity_status"] == "relaxed"
    assert tr.get("narrative_authenticity_rumor_relaxed_low_signal") is True
    assert tr.get("narrative_authenticity_relaxation_flags", {}).get("fallback_uncertainty_active") is True
    na_tr = tr.get("narrative_authenticity_trace") or {}
    assert na_tr.get("rumor_relaxation_flags", {}).get("fallback_uncertainty_active") is True


def test_emission_status_repaired_sets_repair_mode_fields():
    c = build_narrative_authenticity_contract()
    v = {
        "checked": True,
        "passed": True,
        "failure_reasons": [],
        "metrics": {},
        "evidence": {},
    }
    tr = build_narrative_authenticity_emission_trace(
        v, contract=c, repaired=True, repair_mode="drop_echoed_rumor_clause", repair_failed=False
    )
    assert tr["narrative_authenticity_status"] == "repaired"
    assert tr["narrative_authenticity_repair_mode"] == "drop_echoed_rumor_clause"
    assert tr["narrative_authenticity_repair_modes"] == ["drop_echoed_rumor_clause"]


def test_emission_status_fail_terminal_after_repair_failed():
    c = build_narrative_authenticity_contract()
    v = validate_narrative_authenticity("The mist holds along the quay.", c, gm_output=None)
    tr = build_narrative_authenticity_emission_trace(v, contract=c, repaired=False, repair_failed=True)
    assert tr.get("narrative_authenticity_status") == "fail"
    assert tr.get("narrative_authenticity_rumor_relaxed_low_signal") is None


def test_emission_skip_layer_has_skip_reason_and_no_terminal_status():
    """Layer skip (``checked`` false from pipeline) is not ``relaxed`` and does not emit ``pass``."""
    tr = build_narrative_authenticity_emission_trace(
        {"skip_reason": "response_type_contract_failed", "checked": False, "passed": True},
        contract=build_narrative_authenticity_contract(),
    )
    assert tr.get("narrative_authenticity_skip_reason") == "response_type_contract_failed"
    assert "narrative_authenticity_status" not in tr


def test_emission_validator_skip_fallback_uncertainty_not_terminal_status():
    tr = build_narrative_authenticity_emission_trace(
        {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "skip_reason": "fallback_uncertainty_brief_compat",
        },
        contract=build_narrative_authenticity_contract(),
    )
    assert tr.get("narrative_authenticity_skip_reason") == "fallback_uncertainty_brief_compat"
    assert "narrative_authenticity_status" not in tr


def test_apply_na_layer_skip_distinct_from_relaxed_and_fail():
    c = build_narrative_authenticity_contract()
    gm = _gm_with_na(c)
    out, meta, _extra = _apply_narrative_authenticity_layer(
        "Any text here about the gate.",
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": False},
        strict_social_path=False,
    )
    assert out == "Any text here about the gate."
    assert meta.get("narrative_authenticity_skip_reason") == "response_type_contract_failed"
    assert meta.get("narrative_authenticity_checked") is False
    assert meta.get("narrative_authenticity_status") is None
    assert meta.get("narrative_authenticity_failed") is False


def test_apply_na_layer_fail_is_checked_and_terminal_not_skip():
    c = build_narrative_authenticity_contract()
    gm = _gm_with_na(c)
    _out, meta, _extra = _apply_narrative_authenticity_layer(
        "The mist holds along the quay.",
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta.get("narrative_authenticity_checked") is True
    assert meta.get("narrative_authenticity_failed") is True
    assert meta.get("narrative_authenticity_status") == "fail"
    assert meta.get("narrative_authenticity_skip_reason") in (None, "fallback_uncertainty_brief_compat")


def test_fail_is_distinct_from_validator_skip_in_apply_layer():
    c = build_narrative_authenticity_contract()
    gm_uncertain = {
        "response_policy": {
            "narrative_authenticity": c,
            "fallback_behavior": {"uncertainty_active": True},
        }
    }
    out_s, meta_s, _ = _apply_narrative_authenticity_layer(
        "hard to say",
        gm_output=gm_uncertain,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert out_s == "hard to say"
    assert meta_s.get("narrative_authenticity_skip_reason") == "fallback_uncertainty_brief_compat"
    assert meta_s.get("narrative_authenticity_status") is None
    assert meta_s.get("narrative_authenticity_failed") is False

    gm2 = _gm_with_na(c)
    _out_f, meta_f, _ = _apply_narrative_authenticity_layer(
        "The mist holds along the quay.",
        gm_output=gm2,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta_f.get("narrative_authenticity_status") == "fail"
    assert meta_f.get("narrative_authenticity_skip_reason") not in (
        "fallback_uncertainty_brief_compat",
        "response_type_contract_failed",
    )


# --- 2) Clean-pass rumor trace preservation ---


def test_clean_rumor_pass_emission_preserves_trace_metrics_and_pass_status():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {"player_input": "x", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = 'He shrugs. "Dock talk says the sealed gate holds until morning, could be wrong," he mutters.'
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v["passed"] is True
    assert v["metrics"].get("rumor_turn_active") is True
    tr = build_narrative_authenticity_emission_trace(v, contract=c, repaired=False, repair_failed=False)
    assert tr.get("narrative_authenticity_status") == "pass"
    assert tr.get("narrative_authenticity_metrics", {}).get("rumor_turn_active") is True
    assert "rumor_signal_count" in (tr.get("narrative_authenticity_metrics") or {})
    na_tr = tr.get("narrative_authenticity_trace") or {}
    assert na_tr.get("rumor_turn_active") is True
    assert na_tr.get("rumor_trigger_spans")
    assert tr.get("narrative_authenticity_repair_mode") is None
    assert tr.get("narrative_authenticity_repair_modes") == []


def test_clean_rumor_pass_apply_layer_matches_emission_contract():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {"player_input": "x", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = 'He shrugs. "Dock talk says the sealed gate holds until morning, could be wrong," he mutters.'
    gm = _gm_with_na(c)
    _out, meta, _ = _apply_narrative_authenticity_layer(
        text,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta.get("narrative_authenticity_status") == "pass"
    assert meta.get("narrative_authenticity_rumor_relaxed_low_signal") is False
    na_tr = meta.get("narrative_authenticity_trace") or {}
    assert na_tr.get("rumor_turn_active") is True
    assert meta.get("narrative_authenticity_repair_mode") is None
    assert meta.get("narrative_authenticity_repair_modes") == []


# --- 3) Relaxation behavior ---


def test_brevity_alone_relaxation_surfaces_in_validation_and_emission():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the patrol?",
        recent_log_compact=[{"gm_snippet": "Merchants argued over spice crates near the south stairs before curfew."}],
        overrides={
            "rumor_realism": {
                "fallback_compatibility": {"do_not_fail_for_brevity_alone": True},
            }
        },
    )
    text = "They say patrols doubled."
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v.get("rumor_realism_relaxed_low_signal") is True
    assert (v.get("rumor_realism_relaxation_flags") or {}).get("brevity_alone") is True
    tr = build_narrative_authenticity_emission_trace(v, contract=c, repaired=False, repair_failed=False)
    assert tr.get("narrative_authenticity_status") == "relaxed"
    assert tr.get("narrative_authenticity_rumor_relaxed_low_signal") is True


def test_answer_shape_bounded_partial_relaxation_flag_on_rumor_turn():
    """Bounded-partial relaxation can activate alongside other rumor failures (status may stay unset until repair)."""
    c = build_narrative_authenticity_contract(
        player_text="What's the word on the street about the patrol?",
        recent_log_compact=[{"player_input": "x", "gm_snippet": "Patrols doubled near the yard."}],
        overrides={
            "rumor_realism": {
                "fallback_compatibility": {"do_not_fail_for_brevity_alone": False},
            }
        },
    )
    gm = {
        "response_policy": {
            "answer_completeness": {"expected_answer_shape": "bounded_partial"},
        }
    }
    text = (
        '"Patrols doubled near the yard, patrols doubled near the yard, patrols doubled near the yard," '
        "he says, voice flat."
    )
    v = validate_narrative_authenticity(text, c, gm_output=gm)
    assert v.get("rumor_realism_relaxed_low_signal") is True
    assert (v.get("rumor_realism_relaxation_flags") or {}).get("answer_shape_bounded_partial") is True
    tr = build_narrative_authenticity_emission_trace(v, contract=c, repaired=False, repair_failed=False)
    assert "narrative_authenticity_status" not in tr
    assert (tr.get("narrative_authenticity_relaxation_flags") or {}).get("answer_shape_bounded_partial") is True


def test_emission_trace_relaxation_flags_synthetic_fallback_and_refusal_keys():
    """Contract-level emission trace carries validator relaxation flags (including stable debug keys)."""
    c = build_narrative_authenticity_contract(player_text="What rumors about the gate?")
    for flag_key in ("fallback_uncertainty_active", "source_limited_or_refusal_language"):
        v = {
            "checked": True,
            "passed": True,
            "failure_reasons": [],
            "metrics": {"rumor_turn_active": True},
            "evidence": {},
            "rumor_realism_relaxed_low_signal": True,
            "rumor_realism_relaxation_flags": {flag_key: True},
        }
        tr = build_narrative_authenticity_emission_trace(v, contract=c, repaired=False, repair_failed=False)
        assert tr.get("narrative_authenticity_relaxation_flags", {}).get(flag_key) is True
        na_tr = tr.get("narrative_authenticity_trace") or {}
        assert na_tr.get("rumor_relaxation_flags", {}).get(flag_key) is True


def test_identical_phrasing_rumor_failure_not_silenced_by_bounded_partial_shape():
    """Echo / identical phrasing remains a hard failure under bounded partial (not converted to relaxed pass)."""
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {"player_input": "x", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    gm = {
        "response_policy": {
            "answer_completeness": {"expected_answer_shape": "bounded_partial"},
        }
    }
    text = (
        "He keeps his voice low. \"The east gate is sealed until dawn; only what the dockhands say\u2014that could be drink talk.\""
    )
    v = validate_narrative_authenticity(text, c, gm_output=gm)
    assert v["passed"] is False
    assert "rumor_uses_identical_phrasing_for_known_fact" in v.get("failure_reasons", [])
    assert v.get("rumor_realism_relaxed_low_signal") is not True


# --- 4) Repair ordering & acceptance ---


def test_repair_narrative_authenticity_minimal_orders_dialogue_echo_before_rumor_subset():
    """Source-order regression: dialogue-echo branch is evaluated before rumor bounded repair (AER2)."""
    src = inspect.getsource(repair_narrative_authenticity_minimal)
    d = src.find("dialogue_echoes_prior_narration")
    r = src.find("rumor_subset = reasons")
    assert d != -1 and r != -1 and d < r


def test_unquoted_rumor_echo_repair_still_applies_under_brevity_rumor_relaxation():
    """Echo-class rumor repairs remain available when low-signal relaxation is active (AER2/AER3 split)."""
    c = build_narrative_authenticity_contract(
        player_text="What have you heard about the patrols?",
        recent_log_compact=[
            {
                "player_input": "x",
                "gm_snippet": (
                    "Patrols doubled near the yard and the watch tightened curfew checks along the market lane overnight."
                ),
            }
        ],
        overrides={
            "rumor_realism": {
                "fallback_compatibility": {"do_not_fail_for_brevity_alone": True},
            }
        },
    )
    text = "He nods once. Patrols doubled near the yard and the watch tightened overnight."
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    assert v0.get("rumor_realism_relaxed_low_signal") is True
    assert "rumor_uses_identical_phrasing_for_known_fact" in v0.get("failure_reasons", [])
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert mode == "drop_echoed_rumor_clause"
    assert repaired is not None
    assert "patrols doubled" not in repaired.lower()


def test_apply_layer_repaired_vs_fail_terminal_meta():
    c = build_narrative_authenticity_contract(
        player_text="What have you heard about the east gate?",
        recent_log_compact=[
            {
                "player_input": "x",
                "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight.",
            }
        ],
    )
    ok_text = 'He shrugs. "Dock talk says the sealed gate holds until morning, could be wrong," he mutters.'
    gm = _gm_with_na(c)
    _o, meta_ok, _ = _apply_narrative_authenticity_layer(
        ok_text,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta_ok.get("narrative_authenticity_status") == "pass"

    bad_text = (
        "He keeps his voice low. \"The east gate is sealed until dawn; only what the dockhands say\u2014that could be drink talk.\""
    )
    _o2, meta_rep, _ = _apply_narrative_authenticity_layer(
        bad_text,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta_rep.get("narrative_authenticity_status") == "repaired"
    assert meta_rep.get("narrative_authenticity_repair_mode") == "drop_echoed_rumor_clause"

    gm2 = _gm_with_na(c)
    _o3, meta_fail, _ = _apply_narrative_authenticity_layer(
        "The mist holds along the quay.",
        gm_output=gm2,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta_fail.get("narrative_authenticity_status") == "fail"


# --- 5) Additional rumor repair modes ---
# Extra bounded quote transforms (``compress_redundant_reported_speech``, ``reorder_distinct_rumor_clause_first``,
# ``compress_generic_rumor_shell``, ``retain_*``) are hard to trigger in full ``validate`` fixtures without
# echo-class reasons winning first; public tests above lock ``drop_echoed_rumor_clause`` (quoted and unquoted).


# --- 6) Rumor validation edge cases ---


def test_phrase_identical_overlap_fails_even_when_semantic_overlap_allowed():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {"player_input": "x", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = 'He shrugs. "The east gate is sealed until dawn," he mutters.'
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v["passed"] is False
    assert "rumor_uses_identical_phrasing_for_known_fact" in v.get("failure_reasons", [])


def test_same_fact_passes_when_rephrased_with_uncertainty():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {"player_input": "x", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = (
        'He shrugs. "Dock talk says the sealed gate holds until morning—could be wrong," he mutters.'
    )
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v["passed"] is True


def test_same_fact_passes_when_rephrased_with_bias_perspective():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {"player_input": "x", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = 'He shrugs. "Sailors always say the sealed gate story with a slant," he mutters.'
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v["passed"] is True


def test_same_fact_passes_with_net_new_detail_without_truth_overclaim():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {"player_input": "x", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = (
        "He shrugs. \"Heard from a runner\u2014the eastern gatehouse seal holds until sunrise, "
        'and quartermasters invented a chalk ledger code zebryn," he mutters.'
    )
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v["passed"] is True
    assert v["metrics"].get("rumor_new_detail_count", 0) >= 1


def test_no_quote_rumor_does_not_flag_scene_restatement_without_prose_rumor_split():
    c = build_narrative_authenticity_contract(
        player_text="What have you heard about the patrols?",
        recent_log_compact=[
            {
                "player_input": "x",
                "gm_snippet": (
                    "Patrols doubled near the yard and the watch tightened curfew checks along the market lane overnight."
                ),
            }
        ],
    )
    text = (
        "Patrols doubled near the yard and the watch tightened curfew checks along the market lane overnight."
    )
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert "rumor_restates_scene_description" not in v.get("failure_reasons", [])


def test_no_quote_rumor_prior_overlap_still_applies():
    c = build_narrative_authenticity_contract(
        player_text="What have you heard about the patrols?",
        recent_log_compact=[
            {
                "player_input": "x",
                "gm_snippet": (
                    "Patrols doubled near the yard and the watch tightened curfew checks along the market lane overnight."
                ),
            }
        ],
    )
    text = (
        "Patrols doubled near the yard and the watch tightened curfew checks along the market lane overnight."
    )
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert "rumor_uses_identical_phrasing_for_known_fact" in v.get("failure_reasons", [])


# --- 7) Stage-diff / telemetry ---


def test_snapshot_turn_stage_includes_na_status_relaxed_and_rumor_turn_active():
    gm = {
        "player_facing_text": "stub",
        "metadata": {},
        "_final_emission_meta": {
            "narrative_authenticity_status": "relaxed",
            "narrative_authenticity_rumor_relaxed_low_signal": True,
            "narrative_authenticity_trace": {"rumor_turn_active": True},
        },
    }
    snap = snapshot_turn_stage(gm, "na_probe")
    assert snap["narrative_authenticity_status"] == "relaxed"
    assert snap["narrative_authenticity_rumor_relaxed_low_signal"] is True
    assert snap["rumor_turn_active"] is True


def test_evaluator_supporting_metrics_includes_shipped_na_keys_for_relaxed():
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_status": "relaxed",
        "narrative_authenticity_rumor_relaxed_low_signal": True,
        "narrative_authenticity_relaxation_flags": {"answer_shape_bounded_partial": True},
        "narrative_authenticity_trace": {"rumor_turn_active": True},
        "narrative_authenticity_reason_codes": [],
        "narrative_authenticity_metrics": {"rumor_turn_active": True},
        "narrative_authenticity_evidence": {},
    }
    r = evaluate_narrative_authenticity({}, {"ok": True, "gm_output": {"player_facing_text": "x", "_final_emission_meta": fem}}, fem)
    sup = r.get("supporting_metrics") or {}
    assert sup.get("narrative_authenticity_status") == "relaxed"
    assert sup.get("narrative_authenticity_rumor_relaxed_low_signal") is True
    assert (sup.get("narrative_authenticity_trace") or {}).get("rumor_turn_active") is True


# --- 8) Broader NA regression (non-rumor) ---


def test_na_dialogue_echo_still_detected():
    c = build_narrative_authenticity_contract()
    text = (
        "The harbor clerk keeps his eyes on the ledger stacks near the counting room. "
        '"The harbor clerk keeps his eyes on the ledger stacks near the counting room," he says.'
    )
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert r["passed"] is False
    assert "dialogue_echoes_prior_narration" in r["failure_reasons"]


def test_na_adjacent_phrase_reuse_still_detected():
    c = build_narrative_authenticity_contract(overrides={"max_anchor_reuse_clauses": 0})
    a = "The harbor clerk keeps his eyes on the ledger stacks near the counting room."
    text = f"{a} {a}"
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert "adjacent_phrase_reuse" in r.get("failure_reasons", [])


def test_na_low_signal_generic_reply_still_detected():
    c = build_narrative_authenticity_contract()
    r = validate_narrative_authenticity("The mist holds along the quay.", c, gm_output=None)
    assert "low_signal_generic_reply" in r.get("failure_reasons", [])


def test_na_non_diegetic_drop_repair_still_works():
    c = build_narrative_authenticity_contract()
    text = (
        "Insufficient context pins the clerk shrug. Heavy canvas still hides the berth rack labels."
    )
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert mode == "drop_non_diegetic_sentence"
    assert validate_narrative_authenticity(repaired, c, gm_output=None)["passed"] is True


def test_na_bounded_partial_outside_rumor_clears_low_signal_only_failure():
    c = build_narrative_authenticity_contract()
    gm = {
        "response_policy": {
            "answer_completeness": {"expected_answer_shape": "bounded_partial"},
        }
    }
    text = "He pauses for a moment."
    v = validate_narrative_authenticity(text, c, gm_output=gm)
    assert v["passed"] is True
    assert v.get("failure_reasons") == []
