from __future__ import annotations

from typing import Any

import pytest

from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure, validate_failure_classification_row
from tests.helpers.failure_dashboard_report import (
    build_failure_dashboard_rows,
    build_runtime_lineage_summary,
    render_failure_dashboard_markdown,
    write_failure_dashboard_artifact_if_requested,
)

# Ownership note:
# This suite owns classifier locality: category, owners, severity,
# investigate_first, and evidence projection. Projection-field duplication is
# intentional so replay failures remain diagnosable without re-owning runtime.
# Cycle F.H: opening-fallback routing is intentionally still gate-biased in the
# current classifier contract; symptom-specific first-fault routing is future
# reviewed policy work, not behavior asserted in this file today.


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


def test_failure_dashboard_renders_optional_runtime_lineage_summary_without_changing_rows():
    observed = _observed(final_emitted_source="global_scene_fallback", fallback_family="gate_terminal_repair")
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": "final_emitted_source",
                "expected": "generated_candidate",
                "actual": "global_scene_fallback",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="lineage_report_probe",
        turn_index=2,
    )
    fallback = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="scene_opening",
    )
    events = [
        fallback,
        fallback,
        make_runtime_lineage_event(
            event_kind="speaker_repair",
            stage="gate",
            owner="game.speaker_contract_enforcement",
            repair_kind="local_rebind",
        ),
        make_runtime_lineage_event(
            event_kind="mutation",
            stage="gate",
            owner="game.final_emission_gate",
            mutation_kind="fallback_mutation",
        ),
        make_runtime_lineage_event(
            event_kind="gate_outcome",
            stage="gate",
            owner="game.final_emission_gate",
            gate_path="opening_fallback",
        ),
    ]
    summary = build_runtime_lineage_summary(events)
    assert summary["total_events"] == 5
    assert summary["fallback_frequency"] == {"scene_opening": 2}
    assert summary["speaker_repair_frequency"] == {"local_rebind": 1}
    assert summary["mutation_kind_frequency"] == {"fallback_mutation": 1}
    assert summary["gate_path_frequency"] == {"opening_fallback": 1}
    assert summary["recurring_events"][0]["count"] == 2

    ordinary = render_failure_dashboard_markdown(rows, generated_at="2026-05-11T00:00:00Z", command_used="pytest")
    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest",
        runtime_lineage_events=events,
    )
    assert "Runtime Lineage Summary" not in ordinary
    assert "## Runtime Lineage Summary" in report
    assert "**Total lineage events:** 5" in report
    assert "**Fallback selected:** 2" in report
    assert "`scene_opening` (2)" in report
    assert "`local_rebind` (1)" in report
    assert "`fallback_mutation` (1)" in report
    assert "`opening_fallback` (1)" in report
    assert rows[0]["category"] == "fallback"


# Opening fallback owner-bucket assertions here are classifier projection locks,
# not duplicate ownership of gate selection or deterministic opening prose.
# Current rows keep category/source-family taxonomy stable while routing selected
# opening symptoms to first-fault targets: gate selection remains gate-owned,
# owner-bucket mapping routes to FEM metadata, payload symptoms to upstream
# repairs, composition/basis to the deterministic composer, and raw-present
# projection omissions to golden replay.
@pytest.mark.parametrize(
    ("case", "observed", "expected_bucket"),
    [
        (
            "canonical_upstream_prepared",
            _observed(
                final_emitted_source="opening_deterministic_fallback",
                response_type_repair_kind="opening_deterministic_fallback",
                opening_recovered_via_fallback=True,
                opening_fallback_authorship_source="upstream_prepared_opening_fallback",
                fallback_family="scene_opening",
                fallback_temporal_frame="first_impression",
            ),
            OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
        (
            "fail_closed_sealed_gate",
            _observed(
                final_emitted_source="opening_fallback_failed_closed",
                response_type_repair_kind="opening_deterministic_fallback_failed_closed",
                opening_recovered_via_fallback=True,
                fallback_family="scene_opening",
            ),
            OPENING_FALLBACK_OWNER_SEALED_GATE,
        ),
        (
            "legacy_compatibility_local_unknown_ambiguous",
            _observed(
                final_emitted_source="opening_deterministic_fallback",
                response_type_repair_kind="opening_deterministic_fallback",
                opening_recovered_via_fallback=True,
                opening_fallback_authorship_source="compatibility_local_opening_deterministic",
                fallback_family="scene_opening",
            ),
            OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        ),
    ],
)
def test_failure_classifier_rows_split_canonical_legacy_and_sealed_opening_owner_buckets(case, observed, expected_bucket):
    row = classify_replay_failure(
        scenario_id=f"{case}_scenario",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": "opening_recovered_via_fallback",
                "expected": False,
                "actual": True,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "fallback"
    assert row["source_family"] == "opening_fallback"
    assert row["emission_sublayer"] == "opening_fallback"
    assert row["opening_fallback_owner_bucket"] == expected_bucket


def test_failure_classifier_preserves_projected_opening_owner_bucket_evidence():
    row = classify_replay_failure(
        scenario_id="projected_owner_scenario",
        turn_index=0,
        observed_turn=_observed(
            opening_recovered_via_fallback=True,
            opening_fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            fallback_family="scene_opening",
        ),
        drift_rows=[
            {
                "field_path": "opening_fallback_owner_bucket",
                "expected": OPENING_FALLBACK_OWNER_SEALED_GATE,
                "actual": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert row["source_family"] == "opening_fallback"
    assert row["investigate_first"] == "game/final_emission_meta.py"


def test_failure_classifier_routes_opening_authorship_payload_symptom_to_upstream_repairs():
    row = classify_replay_failure(
        scenario_id="opening_authorship_payload",
        turn_index=0,
        observed_turn=_observed(
            opening_recovered_via_fallback=True,
            opening_fallback_authorship_source="compatibility_local_opening_deterministic",
            fallback_family="scene_opening",
        ),
        drift_rows=[
            {
                "field_path": "opening_fallback_authorship_source",
                "expected": "upstream_prepared_opening_fallback",
                "actual": "compatibility_local_opening_deterministic",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "fallback"
    assert row["source_family"] == "opening_fallback"
    assert row["investigate_first"] == "game/upstream_response_repairs.py"


def test_failure_classifier_routes_opening_basis_symptom_to_deterministic_composer():
    row = classify_replay_failure(
        scenario_id="opening_basis_divergence",
        turn_index=0,
        observed_turn=_observed(opening_recovered_via_fallback=True, fallback_family="scene_opening"),
        drift_rows=[
            {
                "field_path": "opening_final_fallback_basis",
                "expected": ["journal seed"],
                "actual": ["visible fact"],
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["investigate_first"] == "game/opening_deterministic_fallback.py"


def test_failure_classifier_routes_opening_projection_omission_to_golden_replay():
    row = classify_replay_failure(
        scenario_id="opening_projection_missing",
        turn_index=0,
        observed_turn=_observed(
            unavailable=["opening_fallback_owner_bucket"],
            raw_signal_presence={"opening_fallback_owner_bucket": True},
        ),
        drift_rows=[
            {
                "field_path": "opening_fallback_owner_bucket",
                "expected": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
                "actual": None,
                "reason": "unexpected unavailable field",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "projection"
    assert row["investigate_first"] == "tests/helpers/golden_replay.py"


def test_failure_classifier_keeps_opening_gate_selection_symptom_gate_routed():
    row = classify_replay_failure(
        scenario_id="opening_gate_selection",
        turn_index=0,
        observed_turn=_observed(
            final_emitted_source="opening_deterministic_fallback",
            opening_recovered_via_fallback=True,
            fallback_family="scene_opening",
        ),
        drift_rows=[
            {
                "field_path": "final_emitted_source",
                "expected": "generated_candidate",
                "actual": "opening_deterministic_fallback",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "fallback"
    assert row["investigate_first"] == "game/final_emission_gate.py"


def test_failure_classification_contract_rejects_invalid_opening_owner_bucket():
    row = classify_replay_failure(
        scenario_id="invalid_owner_scenario",
        turn_index=0,
        observed_turn=_observed(opening_recovered_via_fallback=True, opening_fallback_owner_bucket="not-a-bucket"),
        drift_rows=[
            {
                "field_path": "opening_fallback_owner_bucket",
                "expected": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
                "actual": "not-a-bucket",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert "invalid opening_fallback_owner_bucket: 'not-a-bucket'" in validate_failure_classification_row(row)
    assert row["investigate_first"] == "game/final_emission_meta.py"


# Sealed owner-bucket evidence is intentionally preserved as classifier
# projection; it does not re-own sealed helper prose/output behavior.
def test_failure_classifier_preserves_projected_sealed_owner_bucket_evidence():
    row = classify_replay_failure(
        scenario_id="projected_sealed_owner_scenario",
        turn_index=0,
        observed_turn=_observed(
            final_emitted_source="global_scene_fallback",
            fallback_family="gate_terminal_repair",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
        drift_rows=[
            {
                "field_path": "sealed_fallback_owner_bucket",
                "expected": "not-sealed",
                "actual": SEALED_FALLBACK_OWNER_SEALED_GATE,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "fallback"
    assert row["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE


def test_failure_classifier_preserves_projected_visibility_fallback_evidence():
    row = classify_replay_failure(
        scenario_id="projected_visibility_owner_scenario",
        turn_index=0,
        observed_turn=_observed(
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket="sealed-gate",
            visibility_replacement_applied=True,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
        ),
        drift_rows=[
            {
                "field_path": "visibility_fallback_owner_bucket",
                "expected": "strict-social-visibility",
                "actual": "sealed-gate",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "fallback"
    assert row["visibility_fallback_owner_bucket"] == "sealed-gate"
    assert row["visibility_replacement_applied"] is True
    assert row["visibility_fallback_pool"] == "global_scene_narrative"
    assert row["visibility_fallback_kind"] == "narrative_safe_fallback"


def test_failure_classification_contract_rejects_invalid_visibility_owner_bucket():
    row = classify_replay_failure(
        scenario_id="invalid_visibility_owner_scenario",
        turn_index=0,
        observed_turn=_observed(
            visibility_fallback_owner_bucket="not-a-bucket",
            visibility_replacement_applied=True,
        ),
        drift_rows=[
            {
                "field_path": "visibility_fallback_owner_bucket",
                "expected": "sealed-gate",
                "actual": "not-a-bucket",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert "invalid visibility_fallback_owner_bucket: 'not-a-bucket'" in validate_failure_classification_row(row)


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
            "answer upstream prepared repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="answer_upstream_prepared_repair"),
            {"field_path": "response_type_repair_used", "expected": False, "actual": True, "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "answer_upstream_prepared_repair", None),
        ),
        (
            "action outcome upstream prepared repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="action_outcome_upstream_prepared_repair"),
            {"field_path": "response_type_repair_used", "expected": False, "actual": True, "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "action_outcome_upstream_prepared_repair", None),
        ),
        (
            "strict social dialogue repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="strict_social_dialogue_repair"),
            {"field_path": "response_type_repair_used", "expected": False, "actual": True, "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "strict_social_dialogue_repair", None),
        ),
        (
            "dialogue minimal repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="dialogue_minimal_repair"),
            {"field_path": "response_type_repair_used", "expected": False, "actual": True, "reason": "exact value mismatch", "drift_bucket": "structural_drift"},
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "dialogue_minimal_repair", None),
        ),
        (
            "legacy thin answer backward-compatible sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="thin_answer"),
            {"field_path": "response_type_repair_used", "expected": False, "actual": True, "reason": "legacy backward-compatible fixture", "drift_bucket": "structural_drift"},
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


@pytest.mark.parametrize(
    ("lineage", "expected_source"),
    [
        (["finalize_route_illegal_strip", "post_gate_mutation_detected"], "final_emission.finalize_route_illegal_strip"),
        (["pre_gate_sanitizer", "sanitizer_empty_fallback", "finalize_packaging"], "sanitizer.empty_fallback"),
        (["response_type_repair", "finalize_packaging"], "response_type"),
    ],
)
def test_failure_classifier_reduces_post_gate_unknown_from_final_emission_lineage(lineage, expected_source):
    row = classify_replay_failure(
        scenario_id="post_gate_lineage_reduction",
        turn_index=0,
        observed_turn=_observed(
            post_gate_mutation_detected=True,
            final_emission_mutation_lineage=lineage,
        ),
        drift_rows=[
            {
                "field_path": "post_gate_mutation_detected",
                "expected": False,
                "actual": True,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "emission"
    assert row["emission_sublayer"] == expected_source
    assert row["mutation_source"] == expected_source
    assert row["final_emission_mutation_lineage"] == lineage


def test_failure_classifier_keeps_post_gate_unknown_without_lineage_or_specific_evidence():
    row = classify_replay_failure(
        scenario_id="post_gate_no_lineage_unknown",
        turn_index=0,
        observed_turn=_observed(post_gate_mutation_detected=True, final_emission_mutation_lineage=None),
        drift_rows=[
            {
                "field_path": "post_gate_mutation_detected",
                "expected": False,
                "actual": True,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["emission_sublayer"] == "emission.post_gate_mutation_unknown"
    assert row["mutation_source"] == "emission.post_gate_mutation_unknown"


@pytest.mark.parametrize(
    ("case", "repair_kind", "source_field"),
    [
        ("answer_prepared_owner", "answer_upstream_prepared_repair", "prepared_answer_fallback_text"),
        ("action_prepared_owner", "action_outcome_upstream_prepared_repair", "prepared_action_fallback_text"),
    ],
)
def test_failure_classifier_maps_valid_prepared_answer_action_repairs_to_upstream_owner(case, repair_kind, source_field):
    row = classify_replay_failure(
        scenario_id=case,
        turn_index=0,
        observed_turn=_observed(
            response_type_repair_used=True,
            response_type_repair_kind=repair_kind,
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            upstream_prepared_emission_source=source_field,
            upstream_prepared_emission_reject_reason=None,
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
    )[0]

    assert row["category"] == "emission"
    assert row["primary_owner"] == "upstream_prepared_emission"
    assert row["secondary_owner"] == "emission"
    assert row["source_family"] == "upstream_prepared_emission"
    assert row["investigate_first"] == "game/final_emission_gate.py"
    assert row["emission_sublayer"] == "upstream_prepared_emission"
    assert row["prepared_emission_owner"] == "upstream_prepared_emission"
    assert row["upstream_prepared_emission_used"] is True
    assert row["upstream_prepared_emission_valid"] is True
    assert row["upstream_prepared_emission_source"] == source_field


def test_failure_classifier_preserves_rejected_prepared_emission_reason():
    row = classify_replay_failure(
        scenario_id="malformed_prepared_owner",
        turn_index=0,
        observed_turn=_observed(
            response_type_repair_used=True,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="prepared_action_fallback_text",
            upstream_prepared_emission_reject_reason="missing_concrete_action_outcome",
        ),
        drift_rows=[
            {
                "field_path": "upstream_prepared_emission_valid",
                "expected": True,
                "actual": False,
                "reason": "malformed prepared emission rejected",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["primary_owner"] == "upstream_prepared_emission"
    assert row["prepared_emission_owner"] == "upstream_prepared_emission"
    assert row["upstream_prepared_emission_valid"] is False
    assert row["upstream_prepared_emission_reject_reason"] == "missing_concrete_action_outcome"


def test_failure_dashboard_evidence_shows_rejected_prepared_emission_reason():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(
            response_type_repair_used=False,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="upstream_prepared_emission.prepared_action_fallback_text",
            upstream_prepared_emission_reject_reason="action_outcome_missing_result",
        ),
        drift_rows=[
            {
                "field_path": "upstream_prepared_emission_valid",
                "expected": True,
                "actual": False,
                "reason": "malformed prepared emission rejected",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="rejected_prepared_dashboard",
        turn_index=0,
    )

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-13T00:00:00Z",
        command_used="pytest rejected prepared evidence",
    )

    assert rows[0]["primary_owner"] == "upstream_prepared_emission"
    assert rows[0]["upstream_prepared_emission_reject_reason"] == "action_outcome_missing_result"
    assert "prepared_emission=rejected reason=action_outcome_missing_result" in report


def test_failure_classifier_absent_prepared_emission_telemetry_does_not_assign_upstream_owner():
    row = classify_replay_failure(
        scenario_id="absent_prepared_telemetry",
        turn_index=0,
        observed_turn=_observed(
            response_type_repair_used=False,
            response_type_repair_kind=None,
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="absent",
            upstream_prepared_emission_reject_reason=None,
        ),
        drift_rows=[
            {
                "field_path": "upstream_prepared_emission_used",
                "expected": True,
                "actual": False,
                "reason": "absent prepared emission telemetry",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "emission"
    assert row["primary_owner"] == "emission"
    assert row["secondary_owner"] == "validator"
    assert row["source_family"] == "upstream_prepared_emission"
    assert row["prepared_emission_owner"] is None


def test_failure_classifier_sanitizer_empty_fallback_is_sanitizer_owned_not_prepared_answer_action():
    row = classify_replay_failure(
        scenario_id="sanitizer_empty_split",
        turn_index=0,
        observed_turn=_observed(
            sanitizer_mode="strip_only",
            sanitizer_empty_fallback_used=True,
            sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
            sanitizer_empty_fallback_owner="output_sanitizer",
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source=None,
            upstream_prepared_emission_reject_reason=None,
        ),
        drift_rows=[
            {
                "field_path": "sanitizer_empty_fallback_used",
                "expected": False,
                "actual": True,
                "reason": "sanitizer empty fallback selected",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["category"] == "sanitizer"
    assert row["primary_owner"] == "sanitizer"
    assert row["secondary_owner"] == "emission"
    assert row["source_family"] == "output_sanitizer"
    assert row["emission_sublayer"] == "sanitizer"
    assert row["prepared_emission_owner"] is None
    assert row["sanitizer_empty_fallback_owner"] == "output_sanitizer"
    assert row["sanitizer_empty_fallback_source"] == "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"


@pytest.mark.parametrize("repair_kind", ["strict_social_dialogue_repair", "dialogue_minimal_repair"])
def test_failure_classifier_keeps_dialogue_repairs_separate_from_prepared_emission(repair_kind):
    row = classify_replay_failure(
        scenario_id=f"{repair_kind}_separate",
        turn_index=0,
        observed_turn=_observed(response_type_repair_used=True, response_type_repair_kind=repair_kind),
        drift_rows=[
            {
                "field_path": "response_type_repair_used",
                "expected": False,
                "actual": True,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["primary_owner"] == "emission"
    assert row["source_family"] == "final_emission_gate"
    assert row["emission_sublayer"] == "response_type"
    assert row["prepared_emission_owner"] is None


def test_failure_dashboard_evidence_renders_sanitizer_empty_fallback_distinctly():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(
            sanitizer_mode="strip_only",
            sanitizer_empty_fallback_used=True,
            sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
            sanitizer_empty_fallback_owner="output_sanitizer",
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
        ),
        drift_rows=[
            {
                "field_path": "sanitizer_empty_fallback_used",
                "expected": False,
                "actual": True,
                "reason": "sanitizer empty fallback selected",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="sanitizer_empty_dashboard",
        turn_index=0,
    )

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-13T00:00:00Z",
        command_used="pytest sanitizer empty evidence",
    )

    assert rows[0]["primary_owner"] == "sanitizer"
    assert rows[0]["prepared_emission_owner"] is None
    assert "sanitizer_empty=True" in report
    assert "sanitizer_empty_source=upstream_prepared_emission.prepared_sanitizer_empty_fallback_text" in report
    assert "sanitizer_empty_owner=output_sanitizer" in report
    assert "prepared_emission=used" not in report


def test_failure_classifier_missing_prepared_emission_telemetry_preserves_legacy_owner():
    row = classify_replay_failure(
        scenario_id="legacy_no_prepared_telemetry",
        turn_index=0,
        observed_turn=_observed(response_type_repair_used=True, response_type_repair_kind="answer_upstream_prepared_repair"),
        drift_rows=[
            {
                "field_path": "response_type_repair_used",
                "expected": False,
                "actual": True,
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
    )[0]

    assert row["primary_owner"] == "emission"
    assert row["secondary_owner"] == "validator"
    assert row["source_family"] == "final_emission_gate"
    assert row["emission_sublayer"] == "response_type"
    assert row["prepared_emission_owner"] is None


def test_failure_dashboard_evidence_column_compacts_precision_fields():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(
            response_type_repair_used=True,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            upstream_prepared_emission_source="prepared_action_fallback_text",
            final_emission_mutation_lineage=[
                "pre_gate_sanitizer",
                "response_type_repair",
                "prepared_emission_selection",
                "finalize_packaging",
            ],
            sanitizer_mode="strip_only",
            sanitizer_event_count=2,
            sanitizer_lineage_mode="strip_only",
            sanitizer_lineage_changed_count=2,
            sanitizer_lineage_dropped_count=1,
            sanitizer_lineage_empty_fallback_used=False,
            sanitizer_lineage_legacy_rewrite_active=False,
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
    assert "prepared_emission=used valid=True source=prepared_action_fallback_text" in report
    assert "sublayer=upstream_prepared_emission" in report
    assert "repair=action_outcome_upstream_prepared_repair" in report
    assert "lineage=pre_gate_sanitizer>response_type_repair>prepared_emission_selection>finalize_packaging" in report
    assert "sanitizer_mode=strip_only" in report
    assert "sanitizer_events=2" in report
    assert "sanitizer_lineage_mode=strip_only" in report
    assert "sanitizer_lineage_changed=2" in report
    assert "sanitizer_lineage_dropped=1" in report
    assert "sanitizer_lineage_empty=False" in report
    assert "sanitizer_lineage_legacy=False" in report


def test_failure_dashboard_evidence_preserves_legacy_thin_answer_as_backward_compatible_label():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(response_type_repair_used=True, response_type_repair_kind="thin_answer"),
        drift_rows=[
            {
                "field_path": "response_type_repair_used",
                "expected": False,
                "actual": True,
                "reason": "legacy backward-compatible fixture",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="legacy_thin_answer_probe",
        turn_index=1,
    )

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest legacy evidence",
    )

    assert rows[0]["repair_kind"] == "thin_answer"
    assert "legacy_thin_answer_probe" in report
    assert "repair=thin_answer" in report


def test_failure_classifier_legacy_sanitizer_rewrite_is_diagnostic_output_sanitizer_evidence():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(
            sanitizer_lineage_mode="legacy_sentence_rewrite",
            sanitizer_lineage_changed_count=1,
            sanitizer_lineage_dropped_count=0,
            sanitizer_lineage_empty_fallback_used=False,
            sanitizer_lineage_legacy_rewrite_active=True,
        ),
        drift_rows=[
            {
                "field_path": "scaffold_leakage",
                "expected": False,
                "actual": True,
                "reason": "legacy sentence rewrite diagnostic evidence",
                "drift_bucket": "semantic_drift",
            }
        ],
        scenario_id="legacy_sanitizer_rewrite_probe",
        turn_index=2,
    )

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-13T00:00:00Z",
        command_used="pytest legacy sanitizer evidence",
    )

    assert rows[0]["category"] == "sanitizer"
    assert rows[0]["primary_owner"] == "sanitizer"
    assert rows[0]["secondary_owner"] == "emission"
    assert rows[0]["source_family"] == "output_sanitizer"
    assert rows[0]["emission_sublayer"] == "sanitizer"
    assert rows[0]["sanitizer_lineage_legacy_rewrite_active"] is True
    assert "sanitizer_lineage_mode=legacy_sentence_rewrite" in report
    assert "sanitizer_lineage_legacy=legacy_diagnostic" in report


def test_failure_classifier_strict_social_sanitizer_fallback_keeps_selection_and_prose_owners_split():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(
            strict_social_active=True,
            sanitizer_strict_social_fallback_used=True,
            sanitizer_strict_social_selection_owner="output_sanitizer",
            sanitizer_strict_social_prose_owner="strict_social_emission",
            sanitizer_strict_social_source="social_fallback_line_for_sanitizer.empty_output",
            sanitizer_empty_fallback_used=None,
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
        ),
        drift_rows=[
            {
                "field_path": "sanitizer_strict_social_fallback_used",
                "expected": False,
                "actual": True,
                "reason": "sanitizer selected strict-social fallback",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="strict_social_sanitizer_split_probe",
        turn_index=2,
    )

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-13T00:00:00Z",
        command_used="pytest strict social sanitizer split",
    )

    assert rows[0]["category"] == "sanitizer"
    assert rows[0]["primary_owner"] == "sanitizer"
    assert rows[0]["source_family"] == "output_sanitizer"
    assert rows[0]["emission_sublayer"] == "strict_social_replacement"
    assert rows[0]["prepared_emission_owner"] is None
    assert rows[0]["sanitizer_empty_fallback_used"] is None
    assert rows[0]["sanitizer_strict_social_selection_owner"] == "output_sanitizer"
    assert rows[0]["sanitizer_strict_social_prose_owner"] == "strict_social_emission"
    assert "strict_social_selection_owner=output_sanitizer" in report
    assert "strict_social_prose_owner=strict_social_emission" in report
    assert "strict_social_source=social_fallback_line_for_sanitizer.empty_output" in report
