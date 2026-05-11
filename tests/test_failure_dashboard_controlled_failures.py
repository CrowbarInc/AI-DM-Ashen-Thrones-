from __future__ import annotations

from typing import Any

import pytest

from tests.helpers.failure_dashboard_report import (
    build_failure_dashboard_rows,
    failure_dashboard_requested,
    record_failure_dashboard_rows,
    render_failure_dashboard_markdown,
)

pytestmark = pytest.mark.failure_dashboard_probe


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
    (
        "sanitizer_leakage",
        _observed(sanitizer_mode="strip_only", sanitizer_event_count=1, sanitizer_changed_count=0),
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
        },
    ),
    (
        "response_type_repair_unexpected",
        _observed(response_type_repair_used=True, response_type_repair_kind="thin_answer"),
        {
            "field_path": "response_type_repair_used",
            "expected": False,
            "actual": True,
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        },
        {
            "category": "emission",
            "primary_owner": "emission",
            "secondary_owner": "validator",
            "severity": "medium",
            "investigate_first": "game/final_emission_gate.py",
            "emission_sublayer": "response_type",
            "repair_kind": "thin_answer",
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
        _observed(post_gate_mutation_detected=True),
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
    assert "missing=runtime_missing_raw_absent" in report
    assert "missing=projection_missing_raw_present" in report
    assert "sublayer=emission.post_gate_mutation_unknown" in report
    assert "route_kind" in report
