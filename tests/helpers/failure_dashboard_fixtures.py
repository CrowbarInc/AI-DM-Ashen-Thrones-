"""Shared failure-dashboard controlled probe fixtures (Cycle AL1b).

Support residue for controlled failure probes and classification contract checks.
Probe test assertions stay in ``tests/test_failure_dashboard_controlled_failures.py``.
"""
from __future__ import annotations

from typing import Any

from game.final_emission_ownership_schema import (
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    VISIBILITY_HARD_REPLACEMENT,
)
from tests.helpers.golden_replay_projection import SEALED_FALLBACK_OWNER_SEALED_GATE
from tests.helpers.failure_classification_sync import (
    exact_value_drift_row,
    global_fallback_source_drift_row,
    observed_global_replacement_row,
    observed_opening_authorship_compat_row,
    observed_opening_basis_row,
    observed_opening_fallback_row,
    observed_opening_projection_missing_row,
    observed_post_gate_mutation_row,
    observed_sanitizer_empty_fallback_row,
    observed_sanitizer_leakage_dashboard_row,
    observed_sanitizer_legacy_rewrite_row,
    observed_sealed_replacement_row,
    observed_speaker_mismatch_observed_row,
    observed_upstream_prepared_emission_row,
    observed_visibility_replacement_row,
    post_gate_mutation_drift_row,
    projection_unavailable_drift_row,
    replay_drift_row,
    response_type_repair_drift_row,
    scaffold_leakage_drift_row,
    semantic_text_fragment_drift_row,
    speaker_mismatch_drift_row,
    split_owner_matrix_controlled_failure_cases,
)
from tests.helpers.failure_dashboard_report import build_classified_dashboard_row, record_protected_replay_assertion_failure
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
)
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
from tests.helpers.replay_observed_row_fixtures import observed_dashboard_probe_row as _observed

SYNTHETIC_PROTECTED_BRIDGE_SCENARIO_ID = "synthetic_protected_bridge"
SYNTHETIC_PROTECTED_BRIDGE_TEST_NODE_ID = "tests/test_golden_replay.py::synthetic_protected_bridge"

_DASHBOARD_PROFILE = "dashboard_probe"

_BASE_CONTROLLED_FAILURE_CASES: tuple[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]], ...] = (
    (
        "wrong_speaker",
        observed_speaker_mismatch_observed_row(profile=_DASHBOARD_PROFILE),
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
        observed_global_replacement_row(profile=_DASHBOARD_PROFILE),
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
        observed_opening_fallback_row(owner_bucket=True, profile=_DASHBOARD_PROFILE),
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
        observed_opening_authorship_compat_row(profile=_DASHBOARD_PROFILE),
        exact_value_drift_row(
            "opening_fallback_authorship_source",
            expected=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
            actual=OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
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
        observed_opening_basis_row(profile=_DASHBOARD_PROFILE),
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
        observed_opening_projection_missing_row(profile=_DASHBOARD_PROFILE),
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
        observed_sealed_replacement_row(profile=_DASHBOARD_PROFILE),
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
        observed_visibility_replacement_row(profile=_DASHBOARD_PROFILE),
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
        observed_sanitizer_leakage_dashboard_row(),
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
        observed_sanitizer_empty_fallback_row(
            profile=_DASHBOARD_PROFILE,
            final_emission_mutation_lineage=[
                "pre_gate_sanitizer",
                "sanitizer_empty_fallback",
                "finalize_packaging",
            ],
            sanitizer_lineage_mode="strip_only",
            sanitizer_lineage_changed_count=1,
            sanitizer_lineage_dropped_count=1,
            sanitizer_lineage_empty_fallback_used=True,
            sanitizer_lineage_legacy_rewrite_active=False,
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
            "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
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
            sanitizer_strict_social_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
            sanitizer_strict_social_prose_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            sanitizer_strict_social_selection_owner_trace_short=SANITIZER_TRACE_SELECTION_OWNER_SHORT,
            sanitizer_strict_social_prose_owner_trace_short=SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
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
            "sanitizer_strict_social_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
            "sanitizer_strict_social_prose_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
            "prepared_emission_owner": None,
            "sanitizer_empty_fallback_used": None,
        },
    ),
    (
        "legacy_sanitizer_rewrite_diagnostic",
        observed_sanitizer_legacy_rewrite_row(profile=_DASHBOARD_PROFILE),
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
        observed_upstream_prepared_emission_row(
            profile=_DASHBOARD_PROFILE,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
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
        observed_upstream_prepared_emission_row(
            profile=_DASHBOARD_PROFILE,
            response_type_repair_kind="answer_upstream_prepared_repair",
            upstream_prepared_emission_source="prepared_answer_fallback_text",
            upstream_prepared_emission_valid=False,
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
        observed_post_gate_mutation_row(profile=_DASHBOARD_PROFILE, final_emission_mutation_lineage=None),
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
        observed_post_gate_mutation_row(
            profile=_DASHBOARD_PROFILE,
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
        observed_post_gate_mutation_row(
            profile=_DASHBOARD_PROFILE,
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
        observed_post_gate_mutation_row(
            profile=_DASHBOARD_PROFILE,
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

CONTROLLED_FAILURE_CASES: tuple[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]], ...] = (
    _BASE_CONTROLLED_FAILURE_CASES + split_owner_matrix_controlled_failure_cases()
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
