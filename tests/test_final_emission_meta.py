"""Unit tests for :mod:`game.final_emission_meta` (telemetry schema + normalization helpers)."""

from __future__ import annotations

from game.final_emission_meta import (
    EMISSION_DEBUG_LANE_KEY,
    FINAL_EMISSION_META_KEY,
    INTERNAL_STATE_KEY,
    NARRATIVE_AUTHENTICITY_FEM_KEYS,
    build_narrative_authenticity_emission_trace,
    build_narrative_authenticity_trace_slice,
    default_narrative_authenticity_layer_meta,
    default_response_type_debug,
    ensure_final_emission_meta_dict,
    merge_narrative_authenticity_into_final_emission_meta,
    merge_response_type_meta,
    normalize_final_emission_meta_for_observability,
    normalize_merged_na_telemetry_for_eval,
    normalized_observational_telemetry_bundle,
    patch_final_emission_meta,
    read_emission_debug_lane,
    read_final_emission_meta_dict,
    read_final_emission_meta_from_turn_payload,
    response_type_decision_payload,
    resolve_narrative_authenticity_emission_status,
    slim_na_evidence,
    slim_na_metrics,
    stage_diff_narrative_authenticity_projection,
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


def test_response_type_debug_defaults_and_fem_merge_are_stable() -> None:
    dbg = default_response_type_debug({"required_response_type": "dialogue"}, "resolution.metadata")
    assert dbg == {
        "response_type_required": "dialogue",
        "response_type_contract_source": "resolution.metadata",
        "response_type_candidate_ok": True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
        "response_type_upstream_prepared_absent": False,
    }

    fem: dict = {"final_route": "accept_candidate"}
    merge_response_type_meta(fem, dbg)
    assert fem["final_route"] == "accept_candidate"
    assert fem["response_type_required"] == "dialogue"
    assert fem["response_type_contract_source"] == "resolution.metadata"
    assert fem["response_type_candidate_ok"] is True
    assert fem["response_type_repair_used"] is False
    assert fem["response_type_repair_kind"] is None
    assert fem["response_type_rejection_reasons"] == []
    assert fem["non_hostile_escalation_blocked"] is False
    assert fem["response_type_upstream_prepared_absent"] is False

    # Payload used by trace/log sinks is canonical and shallow.
    assert response_type_decision_payload(dbg) == {
        "response_type_required": "dialogue",
        "response_type_contract_source": "resolution.metadata",
        "response_type_candidate_ok": True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
        "response_type_upstream_prepared_absent": False,
    }


def test_read_helpers_prefer_sidecar_lane_over_legacy_top_level() -> None:
    gm = {
        "_final_emission_meta": {"from": "legacy"},
        INTERNAL_STATE_KEY: {EMISSION_DEBUG_LANE_KEY: {FINAL_EMISSION_META_KEY: {"from": "sidecar"}}},
    }
    assert read_final_emission_meta_dict(gm) == {"from": "sidecar"}

    # Legacy-only fallback still works for mixed fixtures.
    assert read_final_emission_meta_dict({"_final_emission_meta": {"k": 1}}) == {"k": 1}
    assert read_final_emission_meta_dict({}) == {}


def test_read_final_emission_meta_from_turn_payload_supports_api_envelope_and_gm_output_dict() -> None:
    payload = {
        "gm_output": {"player_facing_text": "x"},
        "gm_output_debug": {
            EMISSION_DEBUG_LANE_KEY: {
                FINAL_EMISSION_META_KEY: {"narrative_authenticity_checked": True},
            }
        },
    }
    assert read_final_emission_meta_from_turn_payload(payload).get("narrative_authenticity_checked") is True

    gm_output_only = {
        "player_facing_text": "x",
        INTERNAL_STATE_KEY: {EMISSION_DEBUG_LANE_KEY: {FINAL_EMISSION_META_KEY: {"final_route": "accept_candidate"}}},
    }
    assert read_final_emission_meta_from_turn_payload(gm_output_only).get("final_route") == "accept_candidate"


def test_read_emission_debug_lane_reads_sidecar_lane_when_present() -> None:
    gm = {INTERNAL_STATE_KEY: {EMISSION_DEBUG_LANE_KEY: {"debug_notes": "hi", FINAL_EMISSION_META_KEY: {"k": 2}}}}
    lane = read_emission_debug_lane(gm)
    assert lane.get("debug_notes") == "hi"
    assert isinstance(lane.get(FINAL_EMISSION_META_KEY), dict)


def test_normalize_final_emission_meta_for_observability_fills_nested_defaults_deterministically() -> None:
    fem = {
        "narrative_authenticity_metrics": None,
        "narrative_authenticity_trace": None,
        "narrative_authenticity_evidence": None,
        "narrative_authenticity_relaxation_flags": None,
        "narrative_authenticity_reason_codes": None,
        "narrative_authenticity_failure_reasons": "not-a-list",
        "dead_turn": None,
    }
    n = normalize_final_emission_meta_for_observability(fem)
    assert isinstance(n["dead_turn"], dict)
    assert n["dead_turn"]["is_dead_turn"] is False
    assert n["narrative_authenticity_metrics"] == {}
    assert n["narrative_authenticity_trace"] == {}
    assert n["narrative_authenticity_evidence"] == {}
    assert n["narrative_authenticity_relaxation_flags"] == {}
    assert n["narrative_authenticity_failure_reasons"] == []
    # reason_codes None is treated as absent (no forced list insertion)
    assert "narrative_authenticity_reason_codes" in n


def test_stage_diff_na_projection_is_curated_and_does_not_pass_through_nested_payloads() -> None:
    fem = {
        "narrative_authenticity_status": "pass",
        "narrative_authenticity_reason_codes": ["a", "  ", 1],
        "narrative_authenticity_trace": {"rumor_turn_active": True, "extra": {"nested": "nope"}},
        # Should not pass through nested dict values.
        "narrative_authenticity_metrics": {"x": 1},
        "narrative_authenticity_evidence": {"y": 2},
        # Unknown key should not surface.
        "narrative_authenticity_private_blob": {"z": 3},
    }
    proj = stage_diff_narrative_authenticity_projection(fem)
    assert proj["narrative_authenticity_status"] == "pass"
    assert proj["narrative_authenticity_reason_codes"] == ["a", "1"]
    assert proj["rumor_turn_active"] is True
    assert "narrative_authenticity_metrics" not in proj
    assert "narrative_authenticity_evidence" not in proj
    assert "narrative_authenticity_private_blob" not in proj


def test_normalized_observational_bundle_has_stable_top_level_shapes() -> None:
    payload = {
        "gm_output": {"player_facing_text": "x"},
        "gm_output_debug": {
            EMISSION_DEBUG_LANE_KEY: {
                "debug_notes": "note",
                FINAL_EMISSION_META_KEY: {"dead_turn": {"is_dead_turn": True, "validation_playable": False}},
                "extra_lane_key": 1,
            }
        },
    }
    b = normalized_observational_telemetry_bundle(payload)
    assert set(b) == {
        "final_emission_meta",
        "dead_turn",
        "debug_notes",
        "stage_diff_na_projection",
        "emission_debug_lane_keys",
    }
    assert b["debug_notes"] == "note"
    assert isinstance(b["final_emission_meta"], dict)
    assert isinstance(b["dead_turn"], dict)
    assert b["dead_turn"]["is_dead_turn"] is True
    assert b["dead_turn"]["validation_playable"] is False
    assert isinstance(b["stage_diff_na_projection"], dict)
    assert sorted(b["emission_debug_lane_keys"]) == b["emission_debug_lane_keys"]
    assert FINAL_EMISSION_META_KEY in b["emission_debug_lane_keys"]


def test_write_time_mutation_seam_helpers_ensure_and_patch_fem_in_place() -> None:
    gm: dict = {}
    meta = ensure_final_emission_meta_dict(gm)
    assert gm[FINAL_EMISSION_META_KEY] is meta
    meta["k"] = 1
    assert gm[FINAL_EMISSION_META_KEY]["k"] == 1

    patch_final_emission_meta(gm, {"a": 2})
    assert gm[FINAL_EMISSION_META_KEY]["a"] == 2

    # Malformed FEM gets replaced with a dict.
    gm2: dict = {FINAL_EMISSION_META_KEY: "bad"}
    patch_final_emission_meta(gm2, {"b": 3})
    assert isinstance(gm2[FINAL_EMISSION_META_KEY], dict)
    assert gm2[FINAL_EMISSION_META_KEY]["b"] == 3
