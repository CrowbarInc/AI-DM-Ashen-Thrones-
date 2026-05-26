from __future__ import annotations

from typing import Any

import pytest

from game.final_emission_meta import OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED, SEALED_FALLBACK_OWNER_SEALED_GATE
from tests.helpers.failure_dashboard_report import (
    build_failure_dashboard_rows,
    failure_dashboard_requested,
    record_failure_dashboard_rows,
    render_failure_dashboard_markdown,
)

pytestmark = pytest.mark.failure_dashboard_probe

# Ownership note:
# Controlled probes own dashboard/classifier behavior on known-bad replay-shaped
# rows. They intentionally duplicate projection fields to preserve triage
# locality; runtime prose and routing behavior stay with their direct owners.
# Cycle F.I: controlled opening-fallback rows preserve taxonomy while allowing
# symptom-specific ``investigate_first`` routing for classifier-owned triage.


def _observed(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "scenario_id": "controlled_probe",
        "turn_index": 0,
        "final_text": "The runner answers.",
        "final_text_hash": "probehash",
        "route_kind": "dialogue",
        "selected_speaker_id": "runner",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "fallback_temporal_frame": None,
        "opening_fallback_owner_bucket": None,
        "sealed_fallback_owner_bucket": None,
        "visibility_fallback_owner_bucket": None,
        "visibility_replacement_applied": None,
        "visibility_fallback_pool": None,
        "visibility_fallback_kind": None,
        "response_type_required": "dialogue_response",
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "post_gate_mutation_detected": False,
        "strict_social_active": False,
        "speaker_contract_enforcement_reason": None,
        "fallback_behavior_repaired": False,
        "sanitizer_mode": None,
        "sanitizer_event_count": None,
        "sanitizer_changed_count": None,
        "sanitizer_rewrite_used": None,
        "unavailable": [],
        "raw_signal_presence": {},
        "normalized_signal_presence": {},
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }
    base.update(overrides)
    return base


CONTROLLED_FAILURE_CASES: tuple[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]], ...] = (
    (
        "wrong_speaker",
        _observed(selected_speaker_id="guard"),
        {
            "field_path": "selected_speaker_id",
            "expected": "runner",
            "actual": "guard",
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "speaker",
            "primary_owner": "speaker",
            "secondary_owner": "emission",
            "severity": "critical",
            "investigate_first": "game/speaker_contract_enforcement.py",
        },
    ),
    (
        "forced_fallback_source",
        _observed(final_emitted_source="global_scene_fallback", fallback_family="gate_terminal_repair"),
        {
            "field_path": "final_emitted_source",
            "expected": "generated_candidate",
            "actual": "global_scene_fallback",
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "fallback",
            "primary_owner": "fallback",
            "secondary_owner": "emission",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "terminal_fallback",
        },
    ),
    # Opening fallback owner-bucket rows intentionally duplicate projection
    # fields for dashboard/triage contracts, not deterministic prose ownership.
    # Owner-bucket mapping now routes to FEM metadata; gate selection/final
    # source symptoms remain final-gate-owned.
    (
        "opening_fallback_owner_bucket",
        _observed(
            final_emitted_source="opening_deterministic_fallback",
            response_type_repair_kind="opening_deterministic_fallback",
            opening_recovered_via_fallback=True,
            opening_fallback_authorship_source="upstream_prepared_opening_fallback",
            opening_fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            fallback_family="scene_opening",
            fallback_temporal_frame="first_impression",
        ),
        {
            "field_path": "opening_fallback_owner_bucket",
            "expected": "sealed-gate",
            "actual": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "fallback",
            "primary_owner": "fallback",
            "secondary_owner": "emission",
            "severity": "high",
            "investigate_first": "game/final_emission_meta.py",
            "emission_sublayer": "opening_fallback",
            "opening_fallback_owner_bucket": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        },
    ),
    (
        "opening_fallback_authorship_source",
        _observed(
            opening_recovered_via_fallback=True,
            opening_fallback_authorship_source="compatibility_local_opening_deterministic",
            fallback_family="scene_opening",
        ),
        {
            "field_path": "opening_fallback_authorship_source",
            "expected": "upstream_prepared_opening_fallback",
            "actual": "compatibility_local_opening_deterministic",
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "fallback",
            "primary_owner": "fallback",
            "secondary_owner": "emission",
            "severity": "high",
            "investigate_first": "game/upstream_response_repairs.py",
            "emission_sublayer": "opening_fallback",
        },
    ),
    (
        "opening_fallback_basis",
        _observed(
            opening_recovered_via_fallback=True,
            fallback_family="scene_opening",
        ),
        {
            "field_path": "opening_final_fallback_basis",
            "expected": ["journal seed"],
            "actual": ["visible fact"],
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "replay_drift",
            "primary_owner": "replay",
            "secondary_owner": "emission",
            "severity": "medium",
            "investigate_first": "game/opening_deterministic_fallback.py",
            "emission_sublayer": "opening_fallback",
        },
    ),
    (
        "opening_fallback_projection_missing",
        _observed(
            unavailable=["opening_fallback_owner_bucket"],
            raw_signal_presence={"opening_fallback_owner_bucket": True},
        ),
        {
            "field_path": "opening_fallback_owner_bucket",
            "expected": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            "actual": None,
            "reason": "unexpected unavailable field",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "projection",
            "primary_owner": "projection",
            "secondary_owner": None,
            "severity": "medium",
            "investigate_first": "tests/helpers/golden_replay.py",
            "missing_source_kind": "projection_missing_raw_present",
        },
    ),
    # Sealed fallback rows intentionally repeat final source and owner bucket as
    # dashboard/triage projection locks, not sealed helper prose ownership.
    (
        "sealed_fallback_owner_bucket",
        _observed(
            final_emitted_source="global_scene_fallback",
            fallback_family="gate_terminal_repair",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
        {
            "field_path": "sealed_fallback_owner_bucket",
            "expected": "strict-social-sealed",
            "actual": SEALED_FALLBACK_OWNER_SEALED_GATE,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "fallback",
            "primary_owner": "fallback",
            "secondary_owner": "emission",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "terminal_fallback",
            "sealed_fallback_owner_bucket": SEALED_FALLBACK_OWNER_SEALED_GATE,
        },
    ),
    (
        "visibility_fallback_owner_bucket",
        _observed(
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket="sealed-gate",
            visibility_replacement_applied=True,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
        ),
        {
            "field_path": "visibility_fallback_owner_bucket",
            "expected": "strict-social-visibility",
            "actual": "sealed-gate",
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "fallback",
            "primary_owner": "fallback",
            "secondary_owner": "emission",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "visibility_fallback_owner_bucket": "sealed-gate",
            "visibility_replacement_applied": True,
            "visibility_fallback_pool": "global_scene_narrative",
            "visibility_fallback_kind": "narrative_safe_fallback",
        },
    ),
    (
        "sanitizer_leakage",
        _observed(
            sanitizer_mode="strip_only",
            sanitizer_event_count=1,
            sanitizer_changed_count=0,
            sanitizer_lineage_mode="strip_only",
            sanitizer_lineage_changed_count=1,
            sanitizer_lineage_dropped_count=1,
            sanitizer_lineage_empty_fallback_used=False,
            sanitizer_lineage_legacy_rewrite_active=False,
        ),
        {
            "field_path": "scaffold_leakage",
            "expected": False,
            "actual": True,
            "reason": "scaffold leakage mismatch",
            "drift_bucket": "semantic_drift",
        },
        {
            "category": "sanitizer",
            "primary_owner": "sanitizer",
            "secondary_owner": "emission",
            "severity": "critical",
            "investigate_first": "game/output_sanitizer.py",
            "emission_sublayer": "sanitizer",
            "sanitizer_lineage_mode": "strip_only",
            "sanitizer_lineage_changed_count": 1,
            "sanitizer_lineage_dropped_count": 1,
        },
    ),
    (
        "sanitizer_empty_fallback",
        _observed(
            sanitizer_mode="strip_only",
            sanitizer_empty_fallback_used=True,
            sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
            sanitizer_empty_fallback_owner="output_sanitizer",
            sanitizer_lineage_mode="strip_only",
            sanitizer_lineage_changed_count=1,
            sanitizer_lineage_dropped_count=1,
            sanitizer_lineage_empty_fallback_used=True,
            sanitizer_lineage_legacy_rewrite_active=False,
            final_emission_mutation_lineage=[
                "pre_gate_sanitizer",
                "sanitizer_empty_fallback",
                "finalize_packaging",
            ],
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
        ),
        {
            "field_path": "sanitizer_empty_fallback_used",
            "expected": False,
            "actual": True,
            "reason": "sanitizer empty fallback selected",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "sanitizer",
            "primary_owner": "sanitizer",
            "secondary_owner": "emission",
            "severity": "critical",
            "investigate_first": "game/output_sanitizer.py",
            "emission_sublayer": "sanitizer",
            "sanitizer_empty_fallback_owner": "output_sanitizer",
            "sanitizer_lineage_empty_fallback_used": True,
            "final_emission_mutation_lineage": [
                "pre_gate_sanitizer",
                "sanitizer_empty_fallback",
                "finalize_packaging",
            ],
        },
    ),
    (
        "strict_social_sanitizer_fallback",
        _observed(
            strict_social_active=True,
            sanitizer_strict_social_fallback_used=True,
            sanitizer_strict_social_selection_owner="output_sanitizer",
            sanitizer_strict_social_prose_owner="strict_social_emission",
            sanitizer_strict_social_source="social_fallback_line_for_sanitizer.empty_output",
            sanitizer_empty_fallback_used=None,
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
        ),
        {
            "field_path": "sanitizer_strict_social_fallback_used",
            "expected": False,
            "actual": True,
            "reason": "sanitizer selected strict-social fallback",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "sanitizer",
            "primary_owner": "sanitizer",
            "secondary_owner": "emission",
            "severity": "critical",
            "investigate_first": "game/output_sanitizer.py",
            "emission_sublayer": "strict_social_replacement",
            "sanitizer_strict_social_selection_owner": "output_sanitizer",
            "sanitizer_strict_social_prose_owner": "strict_social_emission",
            "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
            "prepared_emission_owner": None,
            "sanitizer_empty_fallback_used": None,
        },
    ),
    (
        "legacy_sanitizer_rewrite_diagnostic",
        _observed(
            sanitizer_lineage_mode="legacy_sentence_rewrite",
            sanitizer_lineage_changed_count=1,
            sanitizer_lineage_dropped_count=0,
            sanitizer_lineage_empty_fallback_used=False,
            sanitizer_lineage_legacy_rewrite_active=True,
        ),
        {
            "field_path": "scaffold_leakage",
            "expected": False,
            "actual": True,
            "reason": "legacy sentence rewrite diagnostic evidence",
            "drift_bucket": "semantic_drift",
        },
        {
            "category": "sanitizer",
            "primary_owner": "sanitizer",
            "secondary_owner": "emission",
            "severity": "critical",
            "investigate_first": "game/output_sanitizer.py",
            "emission_sublayer": "sanitizer",
            "sanitizer_lineage_legacy_rewrite_active": True,
        },
    ),
    (
        "response_type_repair_unexpected",
        _observed(
            response_type_repair_used=True,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            upstream_prepared_emission_source="prepared_action_fallback_text",
            final_emission_mutation_lineage=[
                "response_type_repair",
                "prepared_emission_selection",
                "finalize_packaging",
            ],
        ),
        {
            "field_path": "response_type_repair_used",
            "expected": False,
            "actual": True,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "emission",
            "primary_owner": "upstream_prepared_emission",
            "secondary_owner": "emission",
            "severity": "medium",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "upstream_prepared_emission",
            "repair_kind": "action_outcome_upstream_prepared_repair",
            "prepared_emission_owner": "upstream_prepared_emission",
            "final_emission_mutation_lineage": [
                "response_type_repair",
                "prepared_emission_selection",
                "finalize_packaging",
            ],
        },
    ),
    (
        "prepared_emission_rejected",
        _observed(
            response_type_repair_used=True,
            response_type_repair_kind="answer_upstream_prepared_repair",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="prepared_answer_fallback_text",
            upstream_prepared_emission_reject_reason="missing_answer_specificity",
        ),
        {
            "field_path": "upstream_prepared_emission_valid",
            "expected": True,
            "actual": False,
            "reason": "malformed prepared emission rejected",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "emission",
            "primary_owner": "upstream_prepared_emission",
            "secondary_owner": "emission",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "upstream_prepared_emission",
            "prepared_emission_owner": "upstream_prepared_emission",
            "upstream_prepared_emission_reject_reason": "missing_answer_specificity",
        },
    ),
    (
        "missing_route_metadata_raw_absent",
        _observed(route_kind=None, unavailable=["route_kind"], raw_signal_presence={"route_kind": False}),
        {
            "field_path": "route_kind",
            "expected": "present",
            "actual": None,
            "reason": "unexpected unavailable field",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "route",
            "primary_owner": "route",
            "secondary_owner": "projection",
            "severity": "medium",
            "investigate_first": "game/interaction_context.py",
            "missing_source_kind": "runtime_missing_raw_absent",
        },
    ),
    (
        "missing_route_metadata_raw_present",
        _observed(route_kind=None, unavailable=["route_kind"], raw_signal_presence={"route_kind": True}),
        {
            "field_path": "route_kind",
            "expected": "present",
            "actual": None,
            "reason": "unexpected unavailable field",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "projection",
            "primary_owner": "projection",
            "secondary_owner": None,
            "severity": "medium",
            "investigate_first": "tests/helpers/golden_replay.py",
            "missing_source_kind": "projection_missing_raw_present",
        },
    ),
    (
        "semantic_mutation",
        _observed(),
        {
            "field_path": "final_text",
            "expected": "include 'east-road talk'",
            "actual": "The answer changed.",
            "reason": "required text fragment missing",
            "drift_bucket": "semantic_drift",
        },
        {
            "category": "semantic_mutation",
            "primary_owner": "semantic_mutation",
            "secondary_owner": "emission",
            "severity": "critical",
            "investigate_first": "game/stage_diff_telemetry.py",
        },
    ),
    (
        "post_gate_unknown_mutation",
        _observed(
            post_gate_mutation_detected=True,
        ),
        {
            "field_path": "post_gate_mutation_detected",
            "expected": False,
            "actual": True,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "emission",
            "primary_owner": "emission",
            "secondary_owner": "validator",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "emission.post_gate_mutation_unknown",
            "mutation_source": "emission.post_gate_mutation_unknown",
            "final_emission_mutation_lineage": None,
        },
    ),
    (
        "post_gate_route_illegal_strip_reduced",
        _observed(
            post_gate_mutation_detected=True,
            final_emission_mutation_lineage=["finalize_route_illegal_strip", "finalize_packaging"],
        ),
        {
            "field_path": "post_gate_mutation_detected",
            "expected": False,
            "actual": True,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "emission",
            "primary_owner": "emission",
            "secondary_owner": "validator",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "final_emission.finalize_route_illegal_strip",
            "mutation_source": "final_emission.finalize_route_illegal_strip",
            "final_emission_mutation_lineage": ["finalize_route_illegal_strip", "finalize_packaging"],
        },
    ),
    (
        "post_gate_sanitizer_empty_reduced",
        _observed(
            post_gate_mutation_detected=True,
            final_emission_mutation_lineage=["pre_gate_sanitizer", "sanitizer_empty_fallback", "finalize_packaging"],
        ),
        {
            "field_path": "post_gate_mutation_detected",
            "expected": False,
            "actual": True,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "emission",
            "primary_owner": "emission",
            "secondary_owner": "validator",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "sanitizer.empty_fallback",
            "mutation_source": "sanitizer.empty_fallback",
            "final_emission_mutation_lineage": ["pre_gate_sanitizer", "sanitizer_empty_fallback", "finalize_packaging"],
        },
    ),
    (
        "post_gate_response_type_reduced",
        _observed(
            post_gate_mutation_detected=True,
            final_emission_mutation_lineage=["response_type_repair", "finalize_packaging"],
        ),
        {
            "field_path": "post_gate_mutation_detected",
            "expected": False,
            "actual": True,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "emission",
            "primary_owner": "emission",
            "secondary_owner": "validator",
            "severity": "high",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "response_type",
            "mutation_source": "response_type",
            "final_emission_mutation_lineage": ["response_type_repair", "finalize_packaging"],
        },
    ),
)


def _classified_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (case_id, observed, drift_row, _expected) in enumerate(CONTROLLED_FAILURE_CASES):
        case_observed = {**observed, "scenario_id": case_id, "turn_index": index}
        rows.extend(
            build_failure_dashboard_rows(
                observed_turn=case_observed,
                drift_rows=[drift_row],
                scenario_id=case_id,
                turn_index=index,
            )
        )
    return rows


@pytest.mark.parametrize(("case_id", "observed", "drift_row", "expected"), CONTROLLED_FAILURE_CASES)
def test_controlled_failure_probe_classifies_known_bad_case(case_id, observed, drift_row, expected):
    row = build_failure_dashboard_rows(
        observed_turn={**observed, "scenario_id": case_id},
        drift_rows=[drift_row],
        scenario_id=case_id,
        turn_index=0,
    )[0]

    for key, value in expected.items():
        assert row.get(key) == value


def test_controlled_failure_probe_dashboard_contains_triage_columns():
    rows = _classified_rows()
    if failure_dashboard_requested():
        record_failure_dashboard_rows(rows)

    report = render_failure_dashboard_markdown(
        rows,
        title="Failure Dashboard Probe Sample",
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest -m failure_dashboard_probe -q",
    )

    assert "Evidence" in report
    assert "wrong_speaker" in report
    assert "speaker_mismatch" in report
    assert "forced_fallback_source" in report
    assert "fallback_source_mismatch" in report
    assert "opening_fallback_owner_bucket" in report
    assert "opening_owner=upstream-prepared" in report
    assert "opening_authorship=upstream_prepared_opening_fallback" in report
    assert "game/final_emission_meta.py" in report
    assert "opening_fallback_authorship_source" in report
    assert "game/upstream_response_repairs.py" in report
    assert "opening_final_fallback_basis" in report
    assert "game/opening_deterministic_fallback.py" in report
    assert "opening_fallback_projection_missing" in report
    assert "tests/helpers/golden_replay.py" in report
    assert "sealed_fallback_owner_bucket" in report
    assert "sealed_owner=sealed-gate" in report
    assert "visibility_fallback_owner_bucket" in report
    assert "visibility_owner=sealed-gate" in report
    assert "visibility_replaced=True" in report
    assert "visibility_pool=global_scene_narrative" in report
    assert "visibility_kind=narrative_safe_fallback" in report
    assert "prepared_emission=used valid=True source=prepared_action_fallback_text" in report
    assert "lineage=response_type_repair>prepared_emission_selection>finalize_packaging" in report
    assert "prepared_emission=rejected reason=missing_answer_specificity" in report
    assert "sanitizer_empty_owner=output_sanitizer" in report
    assert "sanitizer_lineage_changed=1" in report
    assert "sanitizer_lineage_dropped=1" in report
    assert "sanitizer_lineage_empty=True" in report
    assert "sanitizer_lineage_legacy=legacy_diagnostic" in report
    assert "strict_social_selection_owner=output_sanitizer" in report
    assert "strict_social_prose_owner=strict_social_emission" in report
    assert "strict_social_source=social_fallback_line_for_sanitizer.empty_output" in report
    assert "missing=runtime_missing_raw_absent" in report
    assert "missing=projection_missing_raw_present" in report
    assert "sublayer=emission.post_gate_mutation_unknown" in report
    assert "lineage=finalize_route_illegal_strip>finalize_packaging" in report
    assert "mutation=final_emission.finalize_route_illegal_strip" in report
    assert "lineage=pre_gate_sanitizer>sanitizer_empty_fallback>finalize_packaging" in report
    assert "mutation=sanitizer.empty_fallback" in report
    assert "lineage=response_type_repair>finalize_packaging" in report
    assert "mutation=response_type" in report
    assert "route_kind" in report
