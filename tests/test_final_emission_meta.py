"""Unit tests for :mod:`game.final_emission_meta` (telemetry schema + normalization helpers)."""

from __future__ import annotations

import json

from game.final_emission_meta import (
    EVALUATOR_FEM_KEY_PREFIX_FAMILIES,
    EMISSION_DEBUG_LANE_KEY,
    FINAL_EMISSION_META_KEY,
    INTERNAL_STATE_KEY,
    NARRATIVE_AUTHENTICITY_FEM_KEYS,
    NARRATIVE_MODE_OUTPUT_FEM_KEYS,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    assemble_unified_observational_telemetry_bundle,
    build_fem_observability_events,
    build_fem_runtime_lineage_events,
    build_narrative_authenticity_emission_trace,
    build_narrative_authenticity_trace_slice,
    default_narrative_authenticity_layer_meta,
    default_narrative_mode_output_layer_meta,
    default_response_type_debug,
    ensure_final_emission_meta_dict,
    merge_narrative_authenticity_into_final_emission_meta,
    merge_narrative_mode_output_into_final_emission_meta,
    merge_response_type_meta,
    normalize_final_emission_meta_for_observability,
    normalize_merged_na_telemetry_for_eval,
    opening_fallback_owner_bucket_from_meta,
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
from game.upstream_response_repairs import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED

from game.narrative_mode_contract import (
    build_narrative_mode_contract,
    build_narrative_mode_emission_trace,
    validate_narrative_mode_output,
)


def test_default_layer_meta_has_all_fem_keys() -> None:
    d = default_narrative_authenticity_layer_meta()
    for k in NARRATIVE_AUTHENTICITY_FEM_KEYS:
        assert k in d


def test_default_narrative_mode_output_layer_meta_covers_registry() -> None:
    d = default_narrative_mode_output_layer_meta()
    assert set(d.keys()) == NARRATIVE_MODE_OUTPUT_FEM_KEYS


def test_evaluator_fem_prefix_registry_includes_acceptance_quality_family() -> None:
    assert "acceptance_quality_" in EVALUATOR_FEM_KEY_PREFIX_FAMILIES


def test_merge_narrative_mode_output_into_final_emission_meta() -> None:
    c = build_narrative_mode_contract(narration_obligations={"is_opening_scene": True})
    v = validate_narrative_mode_output("As before, the gate waits.", c)
    trace = build_narrative_mode_emission_trace(v, narrative_mode_contract=c)
    fem: dict = {"final_route": "accept_candidate"}
    merge_narrative_mode_output_into_final_emission_meta(fem, trace)
    assert fem["final_route"] == "accept_candidate"
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_passed") is False
    assert isinstance(fem.get("narrative_mode_output_failure_reasons"), list)


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
    expected_stable = {
        "response_type_required": "dialogue",
        "response_type_contract_source": "resolution.metadata",
        "response_type_candidate_ok": True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
        "opening_generic_action_repair_blocked": False,
        "opening_specific_repair_used": False,
        "opening_validation_failed": False,
        "opening_failure_reasons": [],
        "opening_recovered_via_fallback": False,
        "opening_fallback_context_source": None,
        "opening_fallback_basis_count": 0,
        "opening_fallback_context_missing": False,
        "opening_fallback_failed_closed": False,
        "blocked_repair_kind": None,
        "opening_repair_source": "not_opening",
        "response_type_upstream_prepared_absent": False,
        "upstream_prepared_emission_used": False,
        "upstream_prepared_emission_valid": False,
        "upstream_prepared_emission_source": None,
        "upstream_prepared_emission_reject_reason": None,
        "final_emission_boundary_repair_used": False,
        "final_emission_boundary_semantic_repair_disabled": True,
        "fallback_family_used": None,
        "fallback_temporal_frame": None,
    }
    for key, value in expected_stable.items():
        assert dbg.get(key) == value
    assert {
        "opening_fallback_compatibility_local_disabled": False,
        "opening_fallback_missing_upstream_prepared_payload": False,
        "opening_fallback_missing_curated_facts": False,
        "opening_fallback_upstream_payload_unusable": False,
        "opening_fallback_upstream_payload_recovered": False,
        "opening_upstream_prepare_attach_build_failed": False,
        "opening_upstream_prepare_attach_failure_exc_type": None,
        "opening_upstream_prepare_attach_no_usable_payload_after_attempt": False,
        "opening_fallback_authorship_source": None,
    }.items() <= dbg.items()

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
    assert fem["opening_validation_failed"] is False
    assert fem["opening_fallback_basis_count"] == 0
    assert fem["fallback_family_used"] is None
    assert fem["fallback_temporal_frame"] is None
    assert fem["response_type_upstream_prepared_absent"] is False
    assert fem["upstream_prepared_emission_used"] is False
    assert fem["upstream_prepared_emission_valid"] is False
    assert fem["upstream_prepared_emission_source"] is None
    assert fem["upstream_prepared_emission_reject_reason"] is None
    assert fem["final_emission_boundary_repair_used"] is False
    assert fem["final_emission_boundary_semantic_repair_disabled"] is True

    # Payload used by trace/log sinks is canonical and shallow.
    payload = response_type_decision_payload(dbg)
    for key, value in expected_stable.items():
        assert payload.get(key) == value
    assert {
        "opening_fallback_compatibility_local_disabled": False,
        "opening_fallback_missing_upstream_prepared_payload": False,
        "opening_fallback_missing_curated_facts": False,
        "opening_fallback_upstream_payload_unusable": False,
        "opening_fallback_upstream_payload_recovered": False,
        "opening_upstream_prepare_attach_build_failed": False,
        "opening_upstream_prepare_attach_failure_exc_type": None,
        "opening_upstream_prepare_attach_no_usable_payload_after_attempt": False,
        "opening_fallback_authorship_source": None,
    }.items() <= payload.items()


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


def test_stage_diff_na_projection_merges_failure_reasons_into_reason_codes() -> None:
    fem = {
        "narrative_authenticity_failure_reasons": ["gate_reason"],
        "narrative_authenticity_reason_codes": ["packaged", "gate_reason"],
        "narrative_authenticity_status": "pass",
    }
    proj = stage_diff_narrative_authenticity_projection(fem)
    assert proj["narrative_authenticity_reason_codes"] == ["packaged", "gate_reason"]
    assert "narrative_authenticity_failure_reasons" not in proj


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


def test_build_fem_observability_events_bounded_curated_and_stable() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_reason_codes": ["a", "a"],
        "answer_completeness_checked": True,
        "answer_completeness_failed": False,
        "response_delta_checked": True,
        "response_delta_echo_overlap_ratio": 0.25,
        "fallback_behavior_checked": True,
        "fallback_behavior_contract_present": True,
        "response_type_required": "dialogue",
        "response_type_candidate_ok": True,
        "response_type_rejection_reasons": ["x"],
        "dead_turn": {"is_dead_turn": False, "dead_turn_class": "none"},
        "secret_blob": {"nested": "should-not-appear"},
        "narrative_authenticity_metrics": {"heavy": "payload"},
    }
    ev1 = build_fem_observability_events(fem)
    ev2 = build_fem_observability_events(fem)
    assert ev1 == ev2
    assert len(ev1) == 6
    owners = [e["owner"] for e in ev1]
    assert owners == [
        "narrative_authenticity",
        "answer_completeness",
        "response_delta",
        "fallback_behavior",
        "response_type",
        "dead_turn",
    ]
    for e in ev1:
        assert set(e.keys()) == {"phase", "owner", "action", "reasons", "scope", "data"}
        assert e["phase"] == "gate"
        assert e["scope"] == "turn"
        assert "secret_blob" not in e["data"]
    na = ev1[0]
    assert na["owner"] == "narrative_authenticity"
    assert na["data"].keys() <= {
        "checked",
        "failed",
        "repaired",
        "status",
        "skip_reason",
        "rumor_relaxed_low_signal",
    }
    assert "metrics" not in na["data"]
    assert na["reasons"] == ["a"]


def test_build_fem_observability_events_malformed_fem_does_not_crash() -> None:
    assert build_fem_observability_events(None) == []
    assert build_fem_observability_events([]) == []
    assert build_fem_observability_events({}) == []


def test_assemble_unified_bundle_stage_diff_surface_keys_sorted() -> None:
    fem = {"dead_turn": {"is_dead_turn": False, "dead_turn_class": "none"}}
    stage_diff = {
        "transitions": [{"from": "a", "to": "b", "diff": {"route_changed": True}}],
        "snapshots": [{"stage": "s"}],
    }
    b = assemble_unified_observational_telemetry_bundle(fem=fem, stage_diff=stage_diff, evaluator_result=None)
    assert list(b["stage_diff_surface"].keys()) == ["snapshots", "transitions"]


def test_assemble_unified_observational_telemetry_bundle_merges_three_sources_without_leakage() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "dead_turn": {"is_dead_turn": False, "dead_turn_class": "none"},
    }
    stage_diff = {
        "snapshots": [{"stage": "s", "final_route": "accept"}],
        "transitions": [{"from": "a", "to": "b", "diff": {"route_changed": True}}],
        "prior_custom": {"secret": "must_not_surface"},
    }
    evaluator_result = {
        "passed": True,
        "narrative_authenticity_verdict": "clean_pass",
        "scores": {"signal_gain": 5},
        "reasons": [],
        "gameplay_validation": {"excluded_from_scoring": False},
    }
    b = assemble_unified_observational_telemetry_bundle(
        fem=fem,
        stage_diff=stage_diff,
        evaluator_result=evaluator_result,
    )
    assert set(b.keys()) == {
        "final_emission_meta",
        "fem_observability_events",
        "fem_runtime_lineage_events",
        "stage_diff_observability_events",
        "evaluator_observability_events",
        "stage_diff_surface",
    }
    assert isinstance(b["final_emission_meta"], dict)
    assert b["fem_observability_events"]
    assert b["fem_runtime_lineage_events"] == []
    assert b["stage_diff_observability_events"]
    assert b["evaluator_observability_events"]
    assert "prior_custom" not in b["stage_diff_surface"]
    assert set(b["stage_diff_surface"].keys()) <= {"snapshots", "transitions"}
    ev0 = b["evaluator_observability_events"][0]
    assert ev0["phase"] == "evaluator"
    assert "scores" not in ev0["data"]


def test_assemble_unified_observational_telemetry_bundle_optional_inputs_safe() -> None:
    b = assemble_unified_observational_telemetry_bundle(fem=None, stage_diff=None, evaluator_result=None)
    assert b["stage_diff_observability_events"] == []
    assert b["evaluator_observability_events"] == []
    assert b["fem_runtime_lineage_events"] == []
    assert b["stage_diff_surface"] == {}
    assert isinstance(b["fem_observability_events"], list)
    assert isinstance(b["final_emission_meta"], dict)
    # Normalized FEM always materializes ``dead_turn`` defaults, which yields a single dead_turn FEM event.
    assert all(e.get("owner") != "stage_diff_telemetry" for e in b["fem_observability_events"])


def test_build_fem_observability_events_no_arbitrary_pass_through_in_data() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_evidence": {"should": "not leak"},
    }
    ev = build_fem_observability_events(fem)
    assert len(ev) == 1
    assert "evidence" not in ev[0]["data"]


def _lineage_event(events: list[dict], event_kind: str) -> dict:
    return next(event for event in events if event["event_kind"] == event_kind)


def test_build_fem_runtime_lineage_events_acceptance_outcomes_do_not_invent_fallbacks() -> None:
    unchanged = build_fem_runtime_lineage_events(
        {
            "final_route": "accept_candidate",
            "final_emitted_source": "generated_candidate",
            "post_gate_mutation_detected": False,
        }
    )
    assert [event["event_kind"] for event in unchanged] == ["gate_outcome"]
    assert unchanged[0]["gate_path"] == "accept_unchanged"

    repaired = build_fem_runtime_lineage_events(
        {
            "final_route": "accept_candidate",
            "final_emitted_source": "response_delta_repair",
            "post_gate_mutation_detected": True,
        }
    )
    assert _lineage_event(repaired, "gate_outcome")["gate_path"] == "accept_repaired"
    assert not any(event["event_kind"] == "fallback_selected" for event in repaired)


def test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks() -> None:
    opening_meta = {
        "final_route": "accept_candidate",
        "final_emitted_source": "opening_deterministic_fallback",
        "opening_recovered_via_fallback": True,
        "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        "fallback_family_used": "scene_opening",
    }
    opening = build_fem_runtime_lineage_events(opening_meta)
    assert opening_fallback_owner_bucket_from_meta(opening_meta) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    opening_selected = _lineage_event(opening, "fallback_selected")
    assert opening_selected["fallback_kind"] == "scene_opening"
    assert opening_selected["owner"] == "game.final_emission_gate"
    assert opening_selected["fallback_authorship_source"] == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    assert opening_selected["fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert _lineage_event(opening, "gate_outcome")["gate_path"] == "opening_fallback"

    failed_closed_meta = {
        "final_route": "replaced",
        "final_emitted_source": "opening_fallback_failed_closed",
        "opening_fallback_failed_closed": True,
        "response_type_repair_kind": "opening_deterministic_fallback_failed_closed",
    }
    failed_closed = build_fem_runtime_lineage_events(failed_closed_meta)
    assert opening_fallback_owner_bucket_from_meta(failed_closed_meta) == OPENING_FALLBACK_OWNER_SEALED_GATE
    failed_closed_selected = _lineage_event(failed_closed, "fallback_selected")
    assert failed_closed_selected["fallback_kind"] == "opening_failed_closed"
    assert failed_closed_selected["owner"] == "game.final_emission_gate"
    assert failed_closed_selected["fallback_authorship_source"] is None
    assert failed_closed_selected["fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_SEALED_GATE
    assert _lineage_event(failed_closed, "gate_outcome")["gate_path"] == "opening_failed_closed"
    assert opening_selected["fallback_kind"] != failed_closed_selected["fallback_kind"]


def test_build_fem_runtime_lineage_events_projects_strict_social_and_sanitizer_fallbacks() -> None:
    strict_social = build_fem_runtime_lineage_events(
        {
            "final_route": "replaced",
            "strict_social_active": True,
            "final_emitted_source": "deterministic_social_fallback",
        }
    )
    assert _lineage_event(strict_social, "fallback_selected")["fallback_kind"] == "strict_social_fallback"
    assert _lineage_event(strict_social, "gate_outcome")["gate_path"] == "strict_social_fallback"

    emergency = build_fem_runtime_lineage_events(
        {
            "final_route": "replaced",
            "strict_social_active": True,
            "final_emitted_source": "minimal_social_emergency_fallback",
        }
    )
    assert _lineage_event(emergency, "fallback_selected")["fallback_kind"] == "minimal_social_emergency_fallback"
    assert _lineage_event(emergency, "gate_outcome")["gate_path"] == "strict_social_emergency"

    sanitizer = build_fem_runtime_lineage_events(
        {
            "sanitizer_empty_fallback_used": True,
            "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
        }
    )
    fallback = _lineage_event(sanitizer, "fallback_selected")
    assert fallback["stage"] == "sanitizer"
    assert fallback["fallback_kind"] == "sanitizer_empty_output"
    assert _lineage_event(sanitizer, "gate_outcome")["gate_path"] == "sanitizer_fallback"

    sanitizer_social = build_fem_runtime_lineage_events(
        {
            "sanitizer_strict_social_fallback_used": True,
            "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
        }
    )
    assert _lineage_event(sanitizer_social, "fallback_selected")["fallback_kind"] == "sanitizer_strict_social"
    assert _lineage_event(sanitizer_social, "gate_outcome")["gate_path"] == "sanitizer_fallback"


def test_build_fem_runtime_lineage_events_is_conservative_serializable_and_recurrence_ready() -> None:
    assert build_fem_runtime_lineage_events(None) == []
    assert build_fem_runtime_lineage_events({}) == []
    assert build_fem_runtime_lineage_events({"upstream_prepared_emission_valid": True}) == []

    events = build_fem_runtime_lineage_events(
        {
            "upstream_prepared_emission_used": True,
            "response_type_repair_used": True,
            "response_type_repair_kind": "answer_upstream_prepared_repair",
            "final_emitted_source": "answer_upstream_prepared_repair",
        }
    )
    assert _lineage_event(events, "fallback_selected")["fallback_kind"] == "response_type_prepared_emission"
    assert _lineage_event(events, "gate_outcome")["gate_path"] == "prepared_repair"
    assert all(event["recurrence_key"] for event in events)
    assert json.loads(json.dumps(events)) == events


def test_assemble_unified_observational_bundle_exposes_fem_runtime_lineage_sibling_surface() -> None:
    bundle = assemble_unified_observational_telemetry_bundle(
        fem={
            "final_route": "replaced",
            "final_emitted_source": "global_scene_fallback",
            "visibility_replacement_applied": True,
        }
    )
    events = bundle["fem_runtime_lineage_events"]
    assert _lineage_event(events, "fallback_selected")["fallback_kind"] == "visibility_or_scene_replacement"
    assert _lineage_event(events, "gate_outcome")["gate_path"] == "visibility_or_scene_replaced"


def test_build_fem_runtime_lineage_events_projects_explicit_speaker_contract_repairs() -> None:
    for reason, expected_kind in (
        ("continuity_locked_speaker_repair", "local_rebind"),
        ("canonical_speaker_rewrite", "canonical_rewrite"),
        ("narrator_neutral_no_allowed_speaker", "narrator_neutral"),
    ):
        events = build_fem_runtime_lineage_events({"speaker_contract_enforcement_reason": reason})
        speaker = _lineage_event(events, "speaker_repair")
        mutation = _lineage_event(events, "mutation")
        assert speaker["repair_kind"] == expected_kind
        assert speaker["owner"] == "game.speaker_contract_enforcement"
        assert mutation["mutation_kind"] == "speaker_repair_mutation"
        assert all(event["recurrence_key"] for event in events)


def test_build_fem_runtime_lineage_events_projects_interaction_continuity_repairs() -> None:
    expected = {
        "repair_malformed_speaker_attribution": "continuity_malformed_attribution",
        "strip_uncued_interruption": "continuity_strip_uncued_interruption",
        "insert_explicit_bridge": "continuity_insert_bridge",
        "narration_to_dialogue": "continuity_wrap_dialogue",
    }
    for raw_type, repair_kind in expected.items():
        events = build_fem_runtime_lineage_events(
            {
                "interaction_continuity_repair": {
                    "applied": True,
                    "repair_type": raw_type,
                    "violations": ["continuity_violation"],
                }
            }
        )
        assert _lineage_event(events, "speaker_repair")["repair_kind"] == repair_kind
        assert _lineage_event(events, "mutation")["mutation_kind"] == "continuity_repair_mutation"


def test_build_fem_runtime_lineage_events_projects_explicit_mutation_evidence_without_explosion() -> None:
    events = build_fem_runtime_lineage_events(
        {
            "final_route": "accept_candidate",
            "final_emitted_source": "answer_upstream_prepared_repair",
            "response_type_repair_used": True,
            "response_type_repair_kind": "answer_upstream_prepared_repair",
            "upstream_prepared_emission_used": True,
            "post_gate_mutation_detected": True,
            "final_emission_mutation_lineage": [
                "response_type_repair",
                "response_type_repair",
                "prepared_emission_selection",
                "finalize_route_illegal_strip",
                "finalize_packaging",
                "post_gate_mutation_detected",
            ],
        }
    )
    mutations = [event for event in events if event["event_kind"] == "mutation"]
    kinds = [event["mutation_kind"] for event in mutations]
    assert kinds.count("response_type_repair_mutation") == 1
    assert kinds.count("fallback_mutation") == 1
    assert kinds.count("final_emission_mutation") == 1
    assert all(event["recurrence_key"] for event in mutations)
    assert json.loads(json.dumps(events)) == events


def test_build_fem_runtime_lineage_events_projects_sanitizer_and_unknown_post_gate_mutation() -> None:
    sanitizer = build_fem_runtime_lineage_events(
        {
            "sanitizer_lineage_changed_count": 2,
            "sanitizer_empty_fallback_used": True,
            "sanitizer_empty_fallback_source": "prepared_empty",
            "final_emission_mutation_lineage": ["sanitizer_empty_fallback"],
        }
    )
    sanitizer_kinds = {
        event["mutation_kind"] for event in sanitizer if event["event_kind"] == "mutation"
    }
    assert sanitizer_kinds == {"fallback_mutation", "sanitizer_mutation"}
    assert len([event for event in sanitizer if event.get("mutation_kind") == "fallback_mutation"]) == 1

    generic = build_fem_runtime_lineage_events({"post_gate_mutation_detected": True})
    assert _lineage_event(generic, "mutation")["mutation_kind"] == "final_emission_mutation"


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
