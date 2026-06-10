"""Shared failure-dashboard controlled probe fixtures (Cycle AL1b).

Support residue for controlled failure probes and classification contract checks.
Probe test assertions stay in ``tests/test_failure_dashboard_controlled_failures.py``.
"""
from __future__ import annotations

from typing import Any

from game.final_emission_meta import OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED, SEALED_FALLBACK_OWNER_SEALED_GATE
from tests.helpers.failure_classification_sync import (
    exact_value_drift_row,
    global_fallback_source_drift_row,
    post_gate_mutation_drift_row,
    projection_unavailable_drift_row,
    replay_drift_row,
    response_type_repair_drift_row,
    scaffold_leakage_drift_row,
    semantic_text_fragment_drift_row,
    speaker_mismatch_drift_row,
)
from tests.helpers.failure_dashboard_report import build_classified_dashboard_row, record_protected_replay_assertion_failure
from tests.helpers.opening_fallback_evidence import successful_opening_observed_fields
from tests.helpers.replay_observed_row_fixtures import observed_dashboard_probe_row as _observed

SYNTHETIC_PROTECTED_BRIDGE_SCENARIO_ID = "synthetic_protected_bridge"
SYNTHETIC_PROTECTED_BRIDGE_TEST_NODE_ID = "tests/test_golden_replay.py::synthetic_protected_bridge"

CONTROLLED_FAILURE_CASES: tuple[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]], ...] = (
    (
        "wrong_speaker",
        _observed(selected_speaker_id="guard"),
        speaker_mismatch_drift_row(),
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
        global_fallback_source_drift_row(),
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
        _observed(**successful_opening_observed_fields(include_owner_bucket=True)),
        exact_value_drift_row(
            "opening_fallback_owner_bucket",
            expected="sealed-gate",
            actual=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
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
        exact_value_drift_row(
            "opening_fallback_authorship_source",
            expected="upstream_prepared_opening_fallback",
            actual="compatibility_local_opening_deterministic",
        ),
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
        exact_value_drift_row(
            "opening_final_fallback_basis",
            expected=["journal seed"],
            actual=["visible fact"],
        ),
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
        projection_unavailable_drift_row(
            "opening_fallback_owner_bucket",
            expected=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
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
        exact_value_drift_row(
            "sealed_fallback_owner_bucket",
            expected="strict-social-sealed",
            actual=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
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
        exact_value_drift_row(
            "visibility_fallback_owner_bucket",
            expected="strict-social-visibility",
            actual="sealed-gate",
        ),
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
        scaffold_leakage_drift_row(),
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
        replay_drift_row(
            "sanitizer_empty_fallback_used",
            expected=False,
            actual=True,
            reason="sanitizer empty fallback selected",
        ),
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
        replay_drift_row(
            "sanitizer_strict_social_fallback_used",
            expected=False,
            actual=True,
            reason="sanitizer selected strict-social fallback",
        ),
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
        scaffold_leakage_drift_row(reason="legacy sentence rewrite diagnostic evidence"),
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
        response_type_repair_drift_row(),
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
        replay_drift_row(
            "upstream_prepared_emission_valid",
            expected=True,
            actual=False,
            reason="malformed prepared emission rejected",
        ),
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
        projection_unavailable_drift_row("route_kind", expected="present"),
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
        projection_unavailable_drift_row("route_kind", expected="present"),
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
        semantic_text_fragment_drift_row(
            expected="include 'east-road talk'",
            actual="The answer changed.",
        ),
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
        post_gate_mutation_drift_row(),
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
        post_gate_mutation_drift_row(),
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
        post_gate_mutation_drift_row(),
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
        post_gate_mutation_drift_row(),
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

def classified_rows() -> list[dict[str, Any]]:
    """Build dashboard rows for all controlled failure probe cases."""
    rows: list[dict[str, Any]] = []
    for index, (case_id, observed, drift_row, _expected) in enumerate(CONTROLLED_FAILURE_CASES):
        case_observed = {**observed, "scenario_id": case_id, "turn_index": index}
        rows.append(
            build_classified_dashboard_row(
                observed_turn=case_observed,
                drift_row=drift_row,
                scenario_id=case_id,
                turn_index=index,
            )
        )
    return rows


def record_selected_speaker_protected_failure(
    turn: dict[str, Any],
    *,
    scenario_id: str = SYNTHETIC_PROTECTED_BRIDGE_SCENARIO_ID,
    test_node_id: str = SYNTHETIC_PROTECTED_BRIDGE_TEST_NODE_ID,
) -> None:
    """Record the canonical protected replay selected-speaker failure."""
    record_protected_replay_assertion_failure(
        scenario_id=scenario_id,
        test_node_id=test_node_id,
        observed_turn=turn,
        field_path="selected_speaker_id",
        expected="runner",
        actual="guard",
        reason="exact value mismatch",
        drift_bucket="structural_drift",
    )
