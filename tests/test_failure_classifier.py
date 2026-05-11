from __future__ import annotations

from typing import Any

import pytest

from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import (
    build_failure_dashboard_rows,
    render_failure_dashboard_markdown,
    write_failure_dashboard_artifact_if_requested,
)


def _observed(**overrides: Any) -> dict[str, Any]:
    base = {
        "scenario_id": "probe",
        "turn_index": 0,
        "final_text": "The runner answers.",
        "final_text_hash": "hash123",
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
        "fallback_behavior_repair_kind": None,
        "sanitizer_mode": None,
        "sanitizer_event_count": None,
        "sanitizer_changed_count": None,
        "sanitizer_rewrite_used": None,
        "unavailable": [],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("case", "observed", "drift_row", "expected"),
    [
        (
            "wrong speaker",
            _observed(selected_speaker_id="guard"),
            {
                "field_path": "selected_speaker_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            },
            ("speaker", "speaker", "critical", "game/speaker_contract_enforcement.py"),
        ),
        (
            "fallback substitution",
            _observed(final_emitted_source="global_scene_fallback", fallback_family="gate_terminal_repair"),
            {
                "field_path": "final_emitted_source",
                "expected": "anything except 'global_scene_fallback'",
                "actual": "global_scene_fallback",
                "reason": "forbidden value observed",
                "drift_bucket": "structural_drift",
            },
            ("fallback", "fallback", "high", "game/final_emission_gate.py"),
        ),
        (
            "sanitizer leakage",
            _observed(),
            {
                "field_path": "scaffold_leakage",
                "expected": False,
                "actual": True,
                "reason": "scaffold leakage mismatch",
                "drift_bucket": "semantic_drift",
            },
            ("sanitizer", "sanitizer", "critical", "game/output_sanitizer.py"),
        ),
        (
            "projection ambiguity",
            _observed(unavailable=["trace.canonical_entry"], trace={"canonical_entry": {}, "social_contract_trace": {}}),
            {
                "field_path": "trace.canonical_entry",
                "expected": "available",
                "actual": None,
                "reason": "unexpected unavailable field",
                "drift_bucket": "structural_drift",
            },
            ("projection", "projection", "medium", "tests/helpers/golden_replay.py"),
        ),
        (
            "route mismatch",
            _observed(route_kind="action"),
            {
                "field_path": "route_kind",
                "expected": "dialogue",
                "actual": "action",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            },
            ("route", "route", "high", "game/interaction_context.py"),
        ),
        (
            "continuity break",
            _observed(),
            {
                "field_path": "continuity.active_interaction_target_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            },
            ("continuity", "continuity", "high", "game/interaction_context.py"),
        ),
        (
            "semantic mutation",
            _observed(),
            {
                "field_path": "final_text",
                "expected": "include 'east-road talk'",
                "actual": "The answer changed.",
                "reason": "required text fragment missing",
                "drift_bucket": "semantic_drift",
            },
            ("semantic_mutation", "semantic_mutation", "critical", "game/stage_diff_telemetry.py"),
        ),
        (
            "exact-only prose drift",
            _observed(),
            {
                "field_path": "final_text",
                "expected": "hash-a",
                "actual": "hash-b",
                "reason": "opt-in exact text hash mismatch",
                "drift_bucket": "exact_drift",
            },
            ("replay_drift", "replay", "low", "tests/helpers/golden_replay.py"),
        ),
        (
            "response-type repair",
            _observed(response_type_repair_used=True, response_type_repair_kind="dialogue_shape"),
            {
                "field_path": "response_type_repair_used",
                "expected": False,
                "actual": True,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            },
            ("emission", "emission", "medium", "game/final_emission_gate.py"),
        ),
        (
            "missing route metadata",
            _observed(route_kind=None, unavailable=["route_kind"]),
            {
                "field_path": "route_kind",
                "expected": "available or allowed unavailable; allowed=[]",
                "actual": None,
                "reason": "unexpected unavailable field",
                "drift_bucket": "structural_drift",
            },
            ("route", "route", "medium", "game/interaction_context.py"),
        ),
    ],
)
def test_failure_classifier_routes_canonical_failure_cases(case, observed, drift_row, expected):
    category, owner, severity, target = expected

    rows = classify_replay_failure(
        scenario_id=f"{case}_scenario",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[drift_row],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["category"] == category
    assert row["primary_owner"] == owner
    assert row["severity"] == severity
    assert row["investigate_first"] == target


def test_failure_dashboard_report_includes_required_replay_columns():
    observed = _observed(final_emitted_source="global_scene_fallback", fallback_family="gate_terminal_repair")
    drift_rows = [
        {
            "field_path": "final_emitted_source",
            "expected": "generated_candidate",
            "actual": "global_scene_fallback",
            "reason": "exact value mismatch",
            "drift_bucket": "structural_drift",
        }
    ]

    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=drift_rows,
        scenario_id="report_probe",
        turn_index=2,
    )
    report = render_failure_dashboard_markdown(rows, title="Synthetic Failure Dashboard")

    assert "| Scenario | Turn | Category | Severity | Primary Owner |" in report
    assert "| report_probe | 2 | fallback | high | fallback |" in report
    assert "game/final_emission_gate.py" in report
    assert "global_scene_fallback" in report
    assert "gate_terminal_repair" in report


def test_failure_dashboard_markdown_renders_empty_state():
    report = render_failure_dashboard_markdown(
        [],
        title="Empty Dashboard",
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert "# Empty Dashboard" in report
    assert "Generated at: `2026-05-11T00:00:00Z`" in report
    assert "Command: `pytest synthetic`" in report
    assert "No replay failures classified." in report
    assert "| Scenario | Turn |" not in report


def test_failure_dashboard_markdown_renders_one_failure_with_required_fields():
    observed = _observed(
        route_kind=None,
        unavailable=["route_kind", "trace.social_contract_trace"],
        post_gate_mutation_detected=True,
    )
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": "route_kind",
                "expected": "dialogue",
                "actual": None,
                "reason": "unexpected unavailable field",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="one_failure",
        turn_index=7,
    )

    assert rows[0]["primary_owner"] == "route"
    assert rows[0]["severity"] == "medium"
    assert rows[0]["investigate_first"] == "game/interaction_context.py"
    assert rows[0]["unavailable_fields"] == ["route_kind", "trace.social_contract_trace"]

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest one-failure",
    )

    assert "| one_failure | 7 | route | medium | route | projection | game/interaction_context.py |" in report
    assert "route_kind" in report
    assert "dialogue" in report
    assert "trace.social_contract_trace" in report
    assert "True" in report


def test_failure_dashboard_artifact_generation_is_opt_in(tmp_path):
    path = tmp_path / "failure_dashboard_latest.md"
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(),
        drift_rows=[
            {
                "field_path": "selected_speaker_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="opt_in_probe",
        turn_index=1,
    )

    skipped = write_failure_dashboard_artifact_if_requested(
        rows,
        path=path,
        env={},
        command_used="pytest skipped",
        generated_at="2026-05-11T00:00:00Z",
    )
    assert skipped is None
    assert not path.exists()

    written = write_failure_dashboard_artifact_if_requested(
        rows,
        path=path,
        env={"ASHEN_WRITE_FAILURE_DASHBOARD": "1"},
        command_used="pytest written",
        generated_at="2026-05-11T00:00:00Z",
    )
    assert written == path
    text = path.read_text(encoding="utf-8")
    assert "opt_in_probe" in text
    assert "pytest written" in text


@pytest.mark.parametrize(
    ("case", "observed", "drift_row", "expected"),
    [
        (
            "response-type repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="thin_answer"),
            {"field_path": "response_type_repair_used", "expected": False, "actual": True, "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "thin_answer", None),
        ),
        (
            "strict-social replacement sublayer",
            _observed(strict_social_active=True, final_emitted_source="strict_social_visibility_minimal"),
            {"field_path": "final_emitted_source", "expected": "generated_candidate", "actual": "strict_social_visibility_minimal", "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("fallback", "fallback", "emission", "high", "game/final_emission_gate.py", "strict_social_replacement", None, None),
        ),
        (
            "opening fallback sublayer",
            _observed(opening_recovered_via_fallback=True, opening_fallback_authorship_source="upstream_prepared_opening_fallback", fallback_family="scene_opening"),
            {"field_path": "opening_recovered_via_fallback", "expected": False, "actual": True, "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("fallback", "fallback", "emission", "high", "game/final_emission_gate.py", "opening_fallback", None, None),
        ),
        (
            "post-gate mutation unknown",
            _observed(post_gate_mutation_detected=True),
            {"field_path": "post_gate_mutation_detected", "expected": False, "actual": True, "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("emission", "emission", "validator", "high", "game/final_emission_gate.py", "emission.post_gate_mutation_unknown", None, None),
        ),
        (
            "sanitizer leakage metadata present",
            _observed(sanitizer_mode="strip_only", sanitizer_event_count=2, sanitizer_changed_count=1, sanitizer_rewrite_used=True),
            {"field_path": "scaffold_leakage", "expected": False, "actual": True, "reason": "scaffold leakage mismatch", "drift_bucket": "semantic_drift"},
            ("sanitizer", "sanitizer", "emission", "critical", "game/output_sanitizer.py", "sanitizer", None, None),
        ),
        (
            "sanitizer leakage metadata absent",
            _observed(),
            {"field_path": "scaffold_leakage", "expected": False, "actual": True, "reason": "scaffold leakage mismatch", "drift_bucket": "semantic_drift"},
            ("sanitizer", "sanitizer", "emission", "critical", "game/output_sanitizer.py", None, None, None),
        ),
        (
            "projection missing raw-present",
            _observed(unavailable=["trace.canonical_entry"], raw_signal_presence={"trace.canonical_entry": True}),
            {"field_path": "trace.canonical_entry", "expected": "present", "actual": None, "reason": "unexpected unavailable field", "drift_bucket": "structural_drift"},
            ("projection", "projection", None, "medium", "tests/helpers/golden_replay.py", None, None, "projection_missing_raw_present"),
        ),
        (
            "runtime missing raw-absent",
            _observed(route_kind=None, unavailable=["route_kind"], raw_signal_presence={"route_kind": False}),
            {"field_path": "route_kind", "expected": "present", "actual": None, "reason": "unexpected unavailable field", "drift_bucket": "structural_drift"},
            ("route", "route", "projection", "medium", "game/interaction_context.py", None, None, "runtime_missing_raw_absent"),
        ),
        (
            "normalized missing raw-present",
            _observed(unavailable=["fallback_family"], raw_signal_presence={"fallback_family": True}, normalized_signal_presence={"fallback_family": False}),
            {"field_path": "fallback_family", "expected": "present", "actual": None, "reason": "unexpected unavailable field", "drift_bucket": "structural_drift"},
            ("normalization", "normalization", "projection", "low", "game/final_emission_meta.py", None, None, "normalized_view_missing_raw_present"),
        ),
    ],
)
def test_failure_classifier_uses_precision_evidence_for_ambiguous_locality(case, observed, drift_row, expected):
    category, primary, secondary, severity, target, sublayer, repair_kind, missing_kind = expected

    row = classify_replay_failure(
        scenario_id=f"{case}_scenario",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[drift_row],
    )[0]

    assert row["category"] == category
    assert row["primary_owner"] == primary
    assert row["secondary_owner"] == secondary
    assert row["severity"] == severity
    assert row["investigate_first"] == target
    assert row["emission_sublayer"] == sublayer
    assert row["repair_kind"] == repair_kind
    assert row["missing_source_kind"] == missing_kind


def test_failure_dashboard_evidence_column_compacts_precision_fields():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(
            response_type_repair_used=True,
            response_type_repair_kind="thin_answer",
            sanitizer_mode="strip_only",
            sanitizer_event_count=2,
        ),
        drift_rows=[
            {
                "field_path": "response_type_repair_used",
                "expected": False,
                "actual": True,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="evidence_probe",
        turn_index=3,
    )

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest evidence",
    )

    assert "Evidence" in report
    assert "sublayer=response_type" in report
    assert "repair=thin_answer" in report
    assert "sanitizer_mode=strip_only" in report
    assert "sanitizer_events=2" in report
