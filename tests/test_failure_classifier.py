from __future__ import annotations

import pytest

from tests.helpers.golden_replay_projection import SEALED_FALLBACK_OWNER_SEALED_GATE
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure, validate_failure_classification_row
from tests.helpers.failure_classification_sync import (
    assert_contract_classifier_alignment,
    assert_failure_dashboard_row_shape,
    classification_contract_summary,
    classify_replay_probe_row,
    expected_failure_classification_row_fields,
    exact_value_drift_row,
    failure_dashboard_row_shape_errors,
    forbidden_global_fallback_source_drift_row,
    global_fallback_source_drift_row,
    known_failure_categories,
    known_owner_buckets,
    observed_fail_closed_opening_fallback_row,
    observed_failure_row as _observed,
    observed_global_replacement_row,
    observed_legacy_opening_fallback_row,
    observed_opening_fallback_row,
    observed_sanitizer_empty_fallback_row,
    observed_sanitizer_row,
    observed_sealed_replacement_row,
    observed_social_fallback_row,
    observed_visibility_replacement_row,
    opening_recovered_drift_row,
    post_gate_mutation_drift_row,
    projection_unavailable_drift_row,
    protected_observation_registry_summary,
    replay_drift_row,
    response_type_repair_drift_row,
    route_mismatch_drift_row,
    scaffold_leakage_drift_row,
    semantic_text_fragment_drift_row,
    speaker_mismatch_drift_row,
)
from tests.helpers.failure_dashboard_report import (
    build_classified_dashboard_row,
    build_failure_dashboard_rows,
    build_runtime_lineage_summary,
    expected_failure_dashboard_columns,
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


def test_classifier_tables_stay_aligned_with_contract():
    assert_contract_classifier_alignment()


def test_classifier_consumer_reads_taxonomy_from_sync_helpers():
    summary = classification_contract_summary()
    categories = known_failure_categories()
    buckets = known_owner_buckets()
    registry_summary = protected_observation_registry_summary()

    assert summary["failure_category_count"] == len(categories)
    assert summary["opening_owner_bucket_count"] == len(buckets["opening"])
    assert summary["sealed_owner_bucket_count"] == len(buckets["sealed"])
    assert summary["visibility_owner_bucket_count"] == len(buckets["visibility"])
    assert OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED in buckets["opening"]
    assert OPENING_FALLBACK_OWNER_SEALED_GATE in buckets["opening"]
    assert SEALED_FALLBACK_OWNER_SEALED_GATE in buckets["sealed"]
    assert "speaker" in categories
    assert "fallback" in categories
    assert registry_summary["protected_field_count"] == (
        registry_summary["structural_field_count"] + registry_summary["semantic_field_count"]
    )
    assert registry_summary["paths_unique"] is True
    assert registry_summary["paths_sorted"] is True
    assert registry_summary["fallback_family_bucket"] == "structural_drift"
    assert registry_summary["scaffold_leakage_bucket"] == "semantic_drift"
    row_fields = expected_failure_classification_row_fields()
    assert len(row_fields["required"]) == summary["required_field_count"]
    assert "category" in row_fields["required"]
    assert "fallback_family" in row_fields["optional_evidence"]

@pytest.mark.parametrize(
    ("case", "observed", "drift_row", "expected"),
    [
        (
            "wrong speaker",
            _observed(selected_speaker_id="guard"),
            speaker_mismatch_drift_row(),
            ("speaker", "speaker", "critical", "game/speaker_contract_enforcement.py"),
        ),
        (
            "fallback substitution",
            observed_global_replacement_row(),
            forbidden_global_fallback_source_drift_row(),
            ("fallback", "fallback", "high", "game/final_emission_gate.py"),
        ),
        (
            "sanitizer leakage",
            _observed(),
            scaffold_leakage_drift_row(),
            ("sanitizer", "sanitizer", "critical", "game/output_sanitizer.py"),
        ),
        (
            "projection ambiguity",
            _observed(unavailable=["trace.canonical_entry"], trace={"canonical_entry": {}, "social_contract_trace": {}}),
            projection_unavailable_drift_row("trace.canonical_entry", expected="available"),
            ("projection", "projection", "medium", "tests/helpers/golden_replay.py"),
        ),
        (
            "route mismatch",
            _observed(route_kind="action"),
            route_mismatch_drift_row(expected="dialogue", actual="action"),
            ("route", "route", "high", "game/interaction_context.py"),
        ),
        (
            "continuity break",
            _observed(),
            exact_value_drift_row(
                "continuity.active_interaction_target_id",
                expected="runner",
                actual="guard",
            ),
            ("continuity", "continuity", "high", "game/interaction_context.py"),
        ),
        (
            "semantic mutation",
            _observed(),
            semantic_text_fragment_drift_row(
                expected="include 'east-road talk'",
                actual="The answer changed.",
            ),
            ("semantic_mutation", "semantic_mutation", "critical", "game/stage_diff_telemetry.py"),
        ),
        (
            "exact-only prose drift",
            _observed(),
            replay_drift_row(
                "final_text",
                expected="hash-a",
                actual="hash-b",
                reason="opt-in exact text hash mismatch",
                drift_bucket="exact_drift",
            ),
            ("replay_drift", "replay", "low", "tests/helpers/golden_replay.py"),
        ),
        (
            "response-type repair",
            _observed(response_type_repair_used=True, response_type_repair_kind="dialogue_shape"),
            response_type_repair_drift_row(),
            ("emission", "emission", "medium", "game/final_emission_gate.py"),
        ),
        (
            "missing route metadata",
            _observed(route_kind=None, unavailable=["route_kind"]),
            projection_unavailable_drift_row(
                "route_kind",
                expected="available or allowed unavailable; allowed=[]",
            ),
            ("route", "route", "medium", "game/interaction_context.py"),
        ),
    ],
)
def test_failure_classifier_routes_canonical_failure_cases(case, observed, drift_row, expected):
    category, owner, severity, target = expected

    row = classify_replay_probe_row(
        scenario_id=f"{case}_scenario",
        turn_index=0,
        observed_turn=observed,
        drift_row=drift_row,
    )
    assert row["category"] == category
    assert row["primary_owner"] == owner
    assert row["severity"] == severity
    assert row["investigate_first"] == target


def test_failure_dashboard_report_includes_required_replay_columns():
    observed = observed_global_replacement_row()
    drift_rows = [global_fallback_source_drift_row()]

    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=drift_rows,
        scenario_id="report_probe",
        turn_index=2,
    )
    assert_failure_dashboard_row_shape(rows[0])
    report = render_failure_dashboard_markdown(rows, title="Synthetic Failure Dashboard")
    header = "| " + " | ".join(expected_failure_dashboard_columns()) + " |"

    assert header in report
    assert "| report_probe | 2 | fallback | high | fallback |" in report
    assert "game/final_emission_gate.py" in report
    assert "global_scene_fallback" in report
    assert "gate_terminal_repair" in report


def test_failure_dashboard_row_shape_accepts_classified_row():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(),
        drift_rows=[speaker_mismatch_drift_row()],
        scenario_id="row_shape_probe",
        turn_index=0,
    )

    assert failure_dashboard_row_shape_errors(rows[0]) == []
    assert_failure_dashboard_row_shape(rows[0])


def test_failure_dashboard_row_shape_rejects_missing_required_fields():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(),
        drift_rows=[speaker_mismatch_drift_row()],
        scenario_id="row_shape_missing_probe",
        turn_index=0,
    )
    incomplete = {key: value for key, value in rows[0].items() if key != "investigate_first"}

    errors = failure_dashboard_row_shape_errors(incomplete)
    assert any("missing required field: investigate_first" in error for error in errors)
    with pytest.raises(AssertionError, match="investigate_first"):
        assert_failure_dashboard_row_shape(incomplete)


def test_failure_dashboard_markdown_raises_on_invalid_row_shape():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(),
        drift_rows=[speaker_mismatch_drift_row()],
        scenario_id="invalid_row_shape_probe",
        turn_index=0,
    )
    invalid = dict(rows[0])
    del invalid["category"]

    with pytest.raises(ValueError, match="invalid failure dashboard row"):
        render_failure_dashboard_markdown(
            [invalid],
            generated_at="2026-05-31T00:00:00Z",
            command_used="pytest invalid-row-shape",
        )


def test_failure_dashboard_renders_optional_runtime_lineage_summary_without_changing_rows():
    observed = observed_global_replacement_row()
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[global_fallback_source_drift_row()],
        scenario_id="lineage_report_probe",
        turn_index=2,
    )
    fallback = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="scene_opening",
        fallback_authorship_source="upstream_prepared_opening_fallback",
        fallback_owner_bucket="upstream-prepared",
        fallback_selection_owner="game.final_emission_gate",
        fallback_content_owner="game.opening_deterministic_fallback",
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
    assert summary["fallback_authorship_frequency"] == {"upstream_prepared_opening_fallback": 2}
    assert summary["fallback_owner_bucket_frequency"] == {"upstream-prepared": 2}
    assert summary["fallback_selection_owner_frequency"] == {"game.final_emission_gate": 2}
    assert summary["fallback_content_owner_frequency"] == {"game.opening_deterministic_fallback": 2}
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
    assert "`upstream_prepared_opening_fallback` (2)" in report
    assert "`upstream-prepared` (2)" in report
    assert "`game.final_emission_gate` (2)" in report
    assert "`game.opening_deterministic_fallback` (2)" in report
    assert "`local_rebind` (1)" in report
    assert "`fallback_mutation` (1)" in report
    assert "`opening_fallback` (1)" in report
    assert rows[0]["category"] == "fallback"


# Opening fallback owner-bucket assertions here are classifier projection locks,
# not duplicate ownership of gate selection or deterministic opening prose.
# Gate behavior/selection remains in test_final_emission_gate.py, FEM projection
# and runtime-lineage construction in test_final_emission_meta.py, and golden
# replay observed-field transport in test_golden_replay_fallback_projection.py.
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
            observed_opening_fallback_row(),
            OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
        (
            "fail_closed_sealed_gate",
            observed_fail_closed_opening_fallback_row(),
            OPENING_FALLBACK_OWNER_SEALED_GATE,
        ),
        (
            "legacy_compatibility_local_unknown_ambiguous",
            observed_legacy_opening_fallback_row(),
            OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
        ),
    ],
)
def test_failure_classifier_rows_split_canonical_legacy_and_sealed_opening_owner_buckets(case, observed, expected_bucket):
    row = classify_replay_probe_row(
        scenario_id=f"{case}_scenario",
        turn_index=0,
        observed_turn=observed,
        drift_row=opening_recovered_drift_row(),
    )

    assert row["category"] == "fallback"
    assert row["source_family"] == "opening_fallback"
    assert row["emission_sublayer"] == "opening_fallback"
    assert row["opening_fallback_owner_bucket"] == expected_bucket
    assert row["opening_fallback_authorship_source"] == observed.get("opening_fallback_authorship_source")


def test_failure_classifier_preserves_projected_opening_owner_bucket_evidence():
    row = classify_replay_probe_row(
        scenario_id="projected_owner_scenario",
        turn_index=0,
        observed_turn=observed_opening_fallback_row(owner_bucket=True),
        drift_row=exact_value_drift_row(
            "opening_fallback_owner_bucket",
            expected=OPENING_FALLBACK_OWNER_SEALED_GATE,
            actual=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
    )

    assert row["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert row["source_family"] == "opening_fallback"
    assert row["investigate_first"] == "game/final_emission_meta.py"


def test_failure_classifier_routes_opening_authorship_payload_symptom_to_upstream_repairs():
    row = classify_replay_probe_row(
        scenario_id="opening_authorship_payload",
        turn_index=0,
        observed_turn=observed_legacy_opening_fallback_row(),
        drift_row=exact_value_drift_row(
            "opening_fallback_authorship_source",
            expected="upstream_prepared_opening_fallback",
            actual="compatibility_local_opening_deterministic",
        ),
    )

    assert row["category"] == "fallback"
    assert row["source_family"] == "opening_fallback"
    assert row["investigate_first"] == "game/upstream_response_repairs.py"


def test_failure_classifier_routes_opening_basis_symptom_to_deterministic_composer():
    row = classify_replay_probe_row(
        scenario_id="opening_basis_divergence",
        turn_index=0,
        observed_turn=observed_opening_fallback_row(),
        drift_row=exact_value_drift_row(
            "opening_final_fallback_basis",
            expected=["journal seed"],
            actual=["visible fact"],
        ),
    )

    assert row["investigate_first"] == "game/opening_deterministic_fallback.py"


def test_failure_classifier_routes_opening_projection_omission_to_golden_replay():
    row = classify_replay_probe_row(
        scenario_id="opening_projection_missing",
        turn_index=0,
        observed_turn=_observed(
            unavailable=["opening_fallback_owner_bucket"],
            raw_signal_presence={"opening_fallback_owner_bucket": True},
        ),
        drift_row=projection_unavailable_drift_row(
            "opening_fallback_owner_bucket",
            expected=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
    )

    assert row["category"] == "projection"
    assert row["investigate_first"] == "tests/helpers/golden_replay.py"


def test_failure_classifier_keeps_opening_gate_selection_symptom_gate_routed():
    row = classify_replay_probe_row(
        scenario_id="opening_gate_selection",
        turn_index=0,
        observed_turn=observed_opening_fallback_row(),
        drift_row=global_fallback_source_drift_row(
            expected="generated_candidate",
            actual="opening_deterministic_fallback",
        ),
    )

    assert row["category"] == "fallback"
    assert row["investigate_first"] == "game/final_emission_gate.py"


def test_failure_classification_contract_rejects_invalid_opening_owner_bucket():
    row = classify_replay_probe_row(
        scenario_id="invalid_owner_scenario",
        turn_index=0,
        observed_turn=observed_opening_fallback_row(opening_fallback_owner_bucket="not-a-bucket"),
        drift_row=exact_value_drift_row(
            "opening_fallback_owner_bucket",
            expected=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            actual="not-a-bucket",
        ),
    )

    assert "invalid opening_fallback_owner_bucket: 'not-a-bucket'" in validate_failure_classification_row(row)
    assert row["investigate_first"] == "game/final_emission_meta.py"


# Sealed owner-bucket evidence is intentionally preserved as classifier
# projection; it does not re-own sealed helper prose/output behavior.
def test_failure_classifier_preserves_projected_sealed_owner_bucket_evidence():
    row = classify_replay_probe_row(
        scenario_id="projected_sealed_owner_scenario",
        turn_index=0,
        observed_turn=observed_sealed_replacement_row(),
        drift_row=exact_value_drift_row(
            "sealed_fallback_owner_bucket",
            expected="not-sealed",
            actual=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
    )

    assert row["category"] == "fallback"
    assert row["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE


def test_failure_classifier_preserves_projected_visibility_fallback_evidence():
    row = classify_replay_probe_row(
        scenario_id="projected_visibility_owner_scenario",
        turn_index=0,
        observed_turn=observed_visibility_replacement_row(),
        drift_row=exact_value_drift_row(
            "visibility_fallback_owner_bucket",
            expected="strict-social-visibility",
            actual="sealed-gate",
        ),
    )

    assert row["category"] == "fallback"
    assert row["visibility_fallback_owner_bucket"] == "sealed-gate"
    assert row["visibility_replacement_applied"] is True
    assert row["visibility_fallback_pool"] == "global_scene_narrative"
    assert row["visibility_fallback_kind"] == "narrative_safe_fallback"


def test_failure_classification_contract_rejects_invalid_visibility_owner_bucket():
    row = classify_replay_probe_row(
        scenario_id="invalid_visibility_owner_scenario",
        turn_index=0,
        observed_turn=observed_visibility_replacement_row(visibility_fallback_owner_bucket="not-a-bucket"),
        drift_row=exact_value_drift_row(
            "visibility_fallback_owner_bucket",
            expected="sealed-gate",
            actual="not-a-bucket",
        ),
    )

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
            projection_unavailable_drift_row("route_kind", expected="dialogue"),
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
        drift_rows=[speaker_mismatch_drift_row()],
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
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "answer_upstream_prepared_repair", None),
        ),
        (
            "action outcome upstream prepared repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="action_outcome_upstream_prepared_repair"),
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "action_outcome_upstream_prepared_repair", None),
        ),
        (
            "strict social dialogue repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="strict_social_dialogue_repair"),
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "strict_social_dialogue_repair", None),
        ),
        (
            "dialogue minimal repair sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="dialogue_minimal_repair"),
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "dialogue_minimal_repair", None),
        ),
        (
            "legacy thin answer backward-compatible sublayer",
            _observed(response_type_repair_used=True, response_type_repair_kind="thin_answer"),
            response_type_repair_drift_row(reason="legacy backward-compatible fixture"),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "thin_answer", None),
        ),
        (
            "strict-social replacement sublayer",
            observed_social_fallback_row(),
            global_fallback_source_drift_row(
                expected="generated_candidate",
                actual="strict_social_visibility_minimal",
            ),
            ("fallback", "fallback", "emission", "high", "game/final_emission_gate.py", "strict_social_replacement", None, None),
        ),
        (
            "opening fallback sublayer",
            observed_opening_fallback_row(response_type_repair_kind=None),
            opening_recovered_drift_row(),
            ("fallback", "fallback", "emission", "high", "game/final_emission_gate.py", "opening_fallback", None, None),
        ),
        (
            "post-gate mutation unknown",
            _observed(post_gate_mutation_detected=True),
            post_gate_mutation_drift_row(),
            ("emission", "emission", "validator", "high", "game/final_emission_gate.py", "emission.post_gate_mutation_unknown", None, None),
        ),
        (
            "sanitizer leakage metadata present",
            observed_sanitizer_row(),
            scaffold_leakage_drift_row(),
            ("sanitizer", "sanitizer", "emission", "critical", "game/output_sanitizer.py", "sanitizer", None, None),
        ),
        (
            "sanitizer leakage metadata absent",
            _observed(),
            scaffold_leakage_drift_row(),
            ("sanitizer", "sanitizer", "emission", "critical", "game/output_sanitizer.py", None, None, None),
        ),
        (
            "projection missing raw-present",
            _observed(unavailable=["trace.canonical_entry"], raw_signal_presence={"trace.canonical_entry": True}),
            projection_unavailable_drift_row("trace.canonical_entry", expected="present"),
            ("projection", "projection", None, "medium", "tests/helpers/golden_replay.py", None, None, "projection_missing_raw_present"),
        ),
        (
            "runtime missing raw-absent",
            _observed(route_kind=None, unavailable=["route_kind"], raw_signal_presence={"route_kind": False}),
            projection_unavailable_drift_row("route_kind", expected="present"),
            ("route", "route", "projection", "medium", "game/interaction_context.py", None, None, "runtime_missing_raw_absent"),
        ),
        (
            "normalized missing raw-present",
            _observed(unavailable=["fallback_family"], raw_signal_presence={"fallback_family": True}, normalized_signal_presence={"fallback_family": False}),
            projection_unavailable_drift_row("fallback_family", expected="present"),
            ("normalization", "normalization", "projection", "low", "game/final_emission_meta.py", None, None, "normalized_view_missing_raw_present"),
        ),
    ],
)
def test_failure_classifier_uses_precision_evidence_for_ambiguous_locality(case, observed, drift_row, expected):
    category, primary, secondary, severity, target, sublayer, repair_kind, missing_kind = expected

    row = classify_replay_probe_row(
        scenario_id=f"{case}_scenario",
        turn_index=0,
        observed_turn=observed,
        drift_row=drift_row,
    )

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
        drift_rows=[post_gate_mutation_drift_row()],
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
        drift_rows=[post_gate_mutation_drift_row()],
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
        drift_rows=[response_type_repair_drift_row()],
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
    row = classify_replay_probe_row(
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
        drift_row=replay_drift_row(
            "upstream_prepared_emission_valid",
            expected=True,
            actual=False,
            reason="malformed prepared emission rejected",
        ),
    )

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
            replay_drift_row(
                "upstream_prepared_emission_valid",
                expected=True,
                actual=False,
                reason="malformed prepared emission rejected",
            )
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
    row = classify_replay_probe_row(
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
        drift_row=replay_drift_row(
            "upstream_prepared_emission_used",
            expected=True,
            actual=False,
            reason="absent prepared emission telemetry",
        ),
    )

    assert row["category"] == "emission"
    assert row["primary_owner"] == "emission"
    assert row["secondary_owner"] == "validator"
    assert row["source_family"] == "upstream_prepared_emission"
    assert row["prepared_emission_owner"] is None


def test_failure_classifier_sanitizer_empty_fallback_is_sanitizer_owned_not_prepared_answer_action():
    row = classify_replay_failure(
        scenario_id="sanitizer_empty_split",
        turn_index=0,
        observed_turn=observed_sanitizer_empty_fallback_row(
            upstream_prepared_emission_source=None,
            upstream_prepared_emission_reject_reason=None,
        ),
        drift_rows=[
            replay_drift_row(
                "sanitizer_empty_fallback_used",
                expected=False,
                actual=True,
                reason="sanitizer empty fallback selected",
            )
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
        drift_rows=[response_type_repair_drift_row()],
    )[0]

    assert row["primary_owner"] == "emission"
    assert row["source_family"] == "final_emission_gate"
    assert row["emission_sublayer"] == "response_type"
    assert row["prepared_emission_owner"] is None


def test_failure_dashboard_evidence_renders_sanitizer_empty_fallback_distinctly():
    rows = build_failure_dashboard_rows(
        observed_turn=observed_sanitizer_empty_fallback_row(),
        drift_rows=[
            replay_drift_row(
                "sanitizer_empty_fallback_used",
                expected=False,
                actual=True,
                reason="sanitizer empty fallback selected",
            )
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
        drift_rows=[response_type_repair_drift_row()],
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
        drift_rows=[response_type_repair_drift_row()],
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
        drift_rows=[response_type_repair_drift_row(reason="legacy backward-compatible fixture")],
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
        drift_rows=[scaffold_leakage_drift_row(reason="legacy sentence rewrite diagnostic evidence")],
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
            replay_drift_row(
                "sanitizer_strict_social_fallback_used",
                expected=False,
                actual=True,
                reason="sanitizer selected strict-social fallback",
            )
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


def test_failure_classifier_accepts_opening_runtime_lineage_split_owners():
    rows = build_failure_dashboard_rows(
        observed_turn=observed_opening_fallback_row(
            owner_bucket=True,
            runtime_lineage_events=[
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="scene_opening",
                    fallback_selection_owner="game.final_emission_gate",
                    fallback_content_owner="game.opening_deterministic_fallback",
                )
            ],
        ),
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected="game.final_emission_gate",
                actual="game.opening_deterministic_fallback",
                reason="split owner projection changed",
            )
        ],
        scenario_id="opening_split_owner_probe",
        turn_index=0,
    )

    report = render_failure_dashboard_markdown(rows, generated_at="2026-05-29T00:00:00Z", command_used="pytest")

    assert rows[0]["fallback_selection_owner"] == "game.final_emission_gate"
    assert rows[0]["fallback_content_owner"] == "game.opening_deterministic_fallback"
    assert_failure_dashboard_row_shape(rows[0])
    assert "fallback_selection_owner=game.final_emission_gate" in report
    assert "fallback_content_owner=game.opening_deterministic_fallback" in report


def test_failure_classifier_accepts_gate_selected_strict_social_runtime_lineage_split_owners():
    rows = build_failure_dashboard_rows(
        observed_turn=observed_social_fallback_row(
            final_emitted_source="minimal_social_emergency_fallback",
            runtime_lineage_events=[
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="minimal_social_emergency_fallback",
                    fallback_selection_owner="game.final_emission_gate",
                    fallback_content_owner="game.social_exchange_emission",
                )
            ],
        ),
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected="game.final_emission_gate",
                actual="game.social_exchange_emission",
                reason="strict-social split owner projection changed",
            )
        ],
        scenario_id="strict_social_split_owner_probe",
        turn_index=0,
    )

    assert rows[0]["fallback_selection_owner"] == "game.final_emission_gate"
    assert rows[0]["fallback_content_owner"] == "game.social_exchange_emission"
    assert_failure_dashboard_row_shape(rows[0])


def test_failure_classification_contract_rejects_unknown_runtime_lineage_split_owner():
    row = build_failure_dashboard_rows(
        observed_turn=_observed(
            runtime_lineage_events=[
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="scene_opening",
                    fallback_selection_owner="game.unowned_selector",
                    fallback_content_owner="game.unknown_content_owner",
                )
            ],
        ),
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected="game.opening_deterministic_fallback",
                actual="game.unknown_content_owner",
                reason="unknown split owner",
            )
        ],
        scenario_id="unknown_split_owner_probe",
        turn_index=0,
    )

    errors = validate_failure_classification_row(row[0])
    assert "invalid fallback_selection_owner: 'game.unowned_selector'" in errors
    assert "invalid fallback_content_owner: 'game.unknown_content_owner'" in errors
