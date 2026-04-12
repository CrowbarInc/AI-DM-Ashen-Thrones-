"""Unit tests for narrative_authenticity contract + validator."""
from __future__ import annotations

from game.final_emission_repairs import _apply_narrative_authenticity_layer
from game.narrative_authenticity import (
    build_narrative_authenticity_contract,
    build_narrative_authenticity_emission_trace,
    classify_rumor_secondhand_turn,
    inspect_narrative_authenticity_failure,
    repair_narrative_authenticity_minimal,
    validate_narrative_authenticity,
)


def test_build_contract_schema_stable():
    c = build_narrative_authenticity_contract()
    assert c["enabled"] is True
    assert c["version"] == 1
    assert c["mode"] == "advisory_prompt_with_gate_enforcement"
    assert isinstance(c["signal_sources"], list) and len(c["signal_sources"]) == 5
    assert isinstance(c["anti_goals"], dict)
    assert isinstance(c["fallback_compatibility"], dict)
    assert isinstance(c.get("rumor_realism"), dict)
    assert c["rumor_realism"].get("enabled") is True
    tr = c.get("trace") or {}
    assert "rumor_turn_active" in tr


def test_classify_rumor_turn_from_player_lexicon():
    r = classify_rumor_secondhand_turn(player_text="Any gossip about the captain?")
    assert r["rumor_turn_active"] is True
    assert r["trigger_spans"]


def test_rumor_turn_requires_realism_signal():
    c = build_narrative_authenticity_contract(
        player_text="What have you heard about the east gate?",
        recent_log_compact=[
            {"player_input": "I watch the crowd.", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = 'He shrugs. "The east gate is sealed until dawn," he mutters.'
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v["checked"] is True
    reasons = v.get("failure_reasons", [])
    assert "rumor_adds_no_new_signal" in reasons or "rumor_uses_identical_phrasing_for_known_fact" in reasons
    assert v["metrics"].get("rumor_signal_count") == 0


def test_rumor_turn_passes_with_source_and_uncertainty():
    c = build_narrative_authenticity_contract(
        player_text="What rumors are going around about the east gate?",
        recent_log_compact=[
            {"player_input": "hello", "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
    )
    text = (
        'He keeps his voice low. "Only what the dockhands say—that the east gate is sealed until dawn. '
        'Could be drink talk."'
    )
    v = validate_narrative_authenticity(text, c, gm_output=None)
    assert v["metrics"].get("rumor_turn_active") is True
    assert v["metrics"].get("rumor_signal_count", 0) >= 1
    assert "rumor_adds_no_new_signal" not in v.get("failure_reasons", [])


def test_rumor_relaxed_under_bounded_partial_without_hearsay_markers():
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
    assert v["checked"] is True
    assert v["metrics"].get("rumor_turn_active") is True
    assert "rumor_adds_no_new_signal" not in v.get("failure_reasons", [])


def test_validate_detects_narration_dialogue_echo():
    c = build_narrative_authenticity_contract()
    text = (
        "The harbor clerk keeps his eyes on the ledger stacks near the counting room. "
        '"The harbor clerk keeps his eyes on the ledger stacks near the counting room," he says.'
    )
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert r["checked"] is True
    assert r["passed"] is False
    assert "dialogue_echoes_prior_narration" in r["failure_reasons"]


def test_repair_drops_redundant_quote():
    c = build_narrative_authenticity_contract()
    text = (
        "The rain hammers the slate roofs above the yard. "
        '"The rain hammers the slate roofs above the yard," she mutters.'
    )
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert repaired is not None
    assert mode == "drop_redundant_opening_quote"
    v1 = validate_narrative_authenticity(repaired, c, gm_output=None)
    assert v1["passed"] is True


def test_skips_when_fallback_uncertainty_compat():
    c = build_narrative_authenticity_contract()
    gm = {
        "response_policy": {
            "fallback_behavior": {"uncertainty_active": True},
        }
    }
    r = validate_narrative_authenticity("hard to say", c, gm_output=gm)
    assert r["checked"] is False
    assert r["skip_reason"] == "fallback_uncertainty_brief_compat"


def test_inspect_failure_surfaces_metrics_and_evidence():
    c = build_narrative_authenticity_contract()
    text = (
        "The harbor clerk keeps his eyes on the ledger stacks near the counting room. "
        '"The harbor clerk keeps his eyes on the ledger stacks near the counting room," he says.'
    )
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert r["passed"] is False
    assert r["ok"] is False
    assert "metrics" in r and "evidence" in r
    assert r["metrics"].get("quote_narration_overlap") is not None
    assert r["evidence"].get("redundant_opening_span") is not None
    insp = inspect_narrative_authenticity_failure(r)
    assert insp["failed"] is True
    assert insp["ok"] is False
    assert insp["reasons"] == insp["failure_reasons"]
    assert isinstance(insp["metrics"], dict)


def test_low_signal_atmospheric_padding_detected():
    c = build_narrative_authenticity_contract()
    text = "The mist holds along the quay."
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert r["checked"] is True
    assert r["passed"] is False
    assert "low_signal_generic_reply" in r["failure_reasons"]
    assert "atmospheric_only" in (r.get("evidence") or {}).get("matched_filler_patterns", [])


def test_brief_refusal_with_boundary_not_filler():
    c = build_narrative_authenticity_contract()
    text = 'He meets your eyes. "I will not say more than that about the patrol roster."'
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert r["passed"] is True
    assert "low_signal_generic_reply" not in r.get("failure_reasons", [])


def test_follow_up_stale_when_overlap_without_new_signal():
    c = build_narrative_authenticity_contract(
        recent_log_compact=[
            {"gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
        follow_up_pressure={"pressed": True},
    )
    text = "The east gate is sealed until dawn, and patrols still hold the market lane overnight."
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert r["checked"] is True
    assert "follow_up_stale_restatement" in r["failure_reasons"]
    assert r["metrics"].get("followup_overlap") is not None


def test_follow_up_passes_when_next_lead_present():
    c = build_narrative_authenticity_contract(
        recent_log_compact=[
            {"gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight."}
        ],
        follow_up_pressure={"pressed": True},
    )
    text = (
        "The east gate is sealed until dawn, but if you want names, "
        'ask the watchhouse clerk for the night ledger.'
    )
    r = validate_narrative_authenticity(text, c, gm_output=None)
    assert r["passed"] is True
    assert "follow_up_stale_restatement" not in r.get("failure_reasons", [])
    assert r["metrics"].get("signal_markers_detected", 0) >= 0


def test_repair_filler_compression_keeps_substantive_tail():
    c = build_narrative_authenticity_contract()
    text = "He pauses for a moment. Brass tags are not readable from this distance."
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    assert "low_signal_generic_reply" in v0.get("failure_reasons", [])
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert repaired is not None
    assert mode == "compress_filler_sentence"
    assert "brass tags" in repaired.lower()
    assert "pauses" not in repaired.lower()
    assert validate_narrative_authenticity(repaired, c, gm_output=None)["passed"] is True


def test_repair_adjacent_structural_multi_drop():
    c = build_narrative_authenticity_contract(overrides={"max_anchor_reuse_clauses": 0})
    a = "The harbor clerk keeps his eyes on the ledger stacks near the counting room."
    b = "Patrols rotate at the east gate when curfew bells ring."
    text = f"{a} {a} {a} {b}"
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    assert "adjacent_phrase_reuse" in v0.get("failure_reasons", [])
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert repaired is not None
    assert mode == "drop_adjacent_redundant_sentence_multi"
    assert validate_narrative_authenticity(repaired, c, gm_output=None)["passed"] is True


def test_repair_drops_non_diegetic_sentence():
    c = build_narrative_authenticity_contract()
    text = (
        "Insufficient context pins the clerk shrug. Heavy canvas still hides the berth rack labels."
    )
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    assert "non_diegetic_meta_voice" in v0.get("failure_reasons", [])
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert repaired is not None
    assert mode == "drop_non_diegetic_sentence"
    assert "Insufficient context" not in repaired
    assert "canvas" in repaired.lower()
    assert validate_narrative_authenticity(repaired, c, gm_output=None)["passed"] is True


def test_build_emission_trace_on_failure():
    c = build_narrative_authenticity_contract()
    text = "The mist holds along the quay."
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    trace = build_narrative_authenticity_emission_trace(v0, contract=c)
    assert trace["narrative_authenticity_reason_codes"] == ["low_signal_generic_reply"]
    assert isinstance(trace.get("narrative_authenticity_metrics"), dict)
    assert "matched_filler_patterns" in (trace.get("narrative_authenticity_evidence") or {})
    assert trace.get("narrative_authenticity_status") is None


def test_build_emission_trace_terminal_fail_after_repair():
    c = build_narrative_authenticity_contract()
    text = "The mist holds along the quay."
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    trace = build_narrative_authenticity_emission_trace(
        v0, contract=c, repaired=False, repair_failed=True
    )
    assert trace.get("narrative_authenticity_status") == "fail"


def test_repair_rumor_drops_echo_clause_preserves_source_uncertainty():
    c = build_narrative_authenticity_contract(
        player_text="What have you heard about the east gate?",
        recent_log_compact=[
            {
                "player_input": "x",
                "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight.",
            }
        ],
    )
    text = (
        'He keeps his voice low. "The east gate is sealed until dawn; only what the dockhands '
        'say—that could be drink talk."'
    )
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    assert v0["passed"] is False
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert repaired is not None
    assert mode == "drop_echoed_rumor_clause"
    assert "sealed until dawn" not in repaired.lower()
    assert validate_narrative_authenticity(repaired, c, gm_output=None)["passed"] is True


def test_repair_rumor_fail_closed_single_clause_echo_without_safe_drop():
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the patrols?",
        recent_log_compact=[
            {
                "player_input": "x",
                "gm_snippet": (
                    "Patrols doubled near the yard and the watch tightened curfew checks along the market lane."
                ),
            }
        ],
    )
    text = (
        "He keeps his cloak close and shrugs toward the watch line without meeting your eyes. "
        '"Patrols doubled near the yard and the watch tightened curfew checks along the market lane."'
    )
    v0 = validate_narrative_authenticity(text, c, gm_output=None)
    assert v0["passed"] is False
    assert "rumor_uses_identical_phrasing_for_known_fact" in v0.get("failure_reasons", [])
    repaired, mode = repair_narrative_authenticity_minimal(text, v0, c, gm_output=None)
    assert repaired is None and mode is None


def test_apply_na_layer_mirrors_trace_on_failure():
    gm = {"response_policy": {"narrative_authenticity": build_narrative_authenticity_contract()}}
    text = "The mist holds along the quay."
    _t, meta, _extra = _apply_narrative_authenticity_layer(
        text,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta["narrative_authenticity_failed"] is True
    assert meta["narrative_authenticity_reason_codes"] == ["low_signal_generic_reply"]
    assert meta.get("narrative_authenticity_metrics") is not None
    assert meta.get("narrative_authenticity_evidence") is not None
    assert meta.get("narrative_authenticity_status") == "fail"
    assert meta.get("narrative_authenticity_repair_modes") == []


def test_rumor_realism_relaxed_pass_surfaces_in_emission_trace():
    """Validator-owned relaxation flags map to compact emission (AER3); status ``relaxed`` when flagged."""
    c = build_narrative_authenticity_contract(player_text="What rumor have you heard about the gate?")
    v = {
        "checked": True,
        "passed": True,
        "failure_reasons": [],
        "metrics": {"rumor_turn_active": True, "rumor_signal_count": 0},
        "evidence": {},
        "rumor_realism_relaxed_low_signal": True,
        "rumor_realism_relaxation_flags": {"answer_shape_bounded_partial": True},
    }
    trace = build_narrative_authenticity_emission_trace(
        v, contract=c, repaired=False, repair_failed=False
    )
    assert trace.get("narrative_authenticity_status") == "relaxed"
    assert trace.get("narrative_authenticity_rumor_relaxed_low_signal") is True
    assert trace.get("narrative_authenticity_relaxation_flags", {}).get("answer_shape_bounded_partial") is True
    na_tr = trace.get("narrative_authenticity_trace") or {}
    assert na_tr.get("rumor_turn_active") is True
    assert na_tr.get("rumor_realism_relaxed_low_signal") is True


def test_apply_na_layer_repaired_sets_status_and_repair_modes():
    # Match ``test_repair_rumor_drops_echo_clause_preserves_source_uncertainty`` (known fail → repair).
    c = build_narrative_authenticity_contract(
        player_text="What have you heard about the east gate?",
        recent_log_compact=[
            {
                "player_input": "x",
                "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight.",
            }
        ],
    )
    text = (
        'He keeps his voice low. "The east gate is sealed until dawn; only what the dockhands '
        'say—that could be drink talk."'
    )
    gm = {"response_policy": {"narrative_authenticity": c}}
    out, meta, _extra = _apply_narrative_authenticity_layer(
        text,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert meta.get("narrative_authenticity_status") == "repaired"
    assert meta.get("narrative_authenticity_repair_mode") == "drop_echoed_rumor_clause"
    assert meta.get("narrative_authenticity_repair_modes") == ["drop_echoed_rumor_clause"]
