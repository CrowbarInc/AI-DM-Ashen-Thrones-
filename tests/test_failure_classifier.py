from __future__ import annotations

import pytest

from game.attribution_read_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    FIRST_MENTION_HARD_REPLACEMENT,
    REFERENTIAL_CLARITY_HARD_REPLACEMENT,
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
    VISIBILITY_HARD_REPLACEMENT,
)
from game.attribution_read_views import SEALED_FALLBACK_OWNER_SEALED_GATE
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure, validate_failure_classification_row
from tests.helpers.failure_classification_sync import (
    assert_classification_owner_mapping,
    assert_classification_contract_categories_contain,
    assert_classification_contract_summary,
    assert_compact_evidence_field,
    assert_contract_classifier_alignment,
    assert_dashboard_evidence_cell,
    assert_dashboard_evidence_column_present,
    assert_failure_classification_row,
    assert_failure_dashboard_row_shape,
    assert_fallback_authorship_evidence,
    assert_lineage_aggregation_parity,
    assert_lineage_matrix_row_aggregated,
    assert_lineage_summary_counts,
    assert_owner_buckets_contain,
    assert_prepared_emission_evidence,
    assert_registry_contract_fields,
    assert_registry_summary_contains,
    assert_registry_summary_counts,
    assert_runtime_lineage_source_counts,
    assert_runtime_lineage_summary_absent,
    assert_runtime_lineage_summary_contains,
    assert_sanitizer_empty_fallback_evidence,
    assert_sanitizer_lineage_evidence,
    assert_split_owner_classification,
    assert_split_owner_matrix_classifier_row,
    assert_split_owner_matrix_dashboard_expected,
    assert_split_owner_matrix_lineage_event,
    assert_strict_social_sanitizer_evidence,
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
    legacy_compatibility_local_opening_classifier_row,
    observed_opening_fallback_row,
    observed_opening_family_split_owner_row,
    observed_opening_projection_missing_row,
    observed_post_gate_mutation_row,
    observed_response_type_repair_row,
    observed_sanitizer_empty_fallback_row,
    observed_sanitizer_legacy_rewrite_row,
    observed_sanitizer_row,
    observed_sealed_replacement_row,
    observed_sealed_family_split_owner_row,
    observed_social_fallback_row,
    observed_speaker_mismatch_observed_row,
    observed_upstream_prepared_emission_row,
    observed_visibility_replacement_row,
    observed_visibility_family_hard_replacement_row,
    observed_sanitizer_split_owner_row,
    observed_upstream_fast_split_owner_row,
    observed_referential_local_substitution_classifier_row,
    opening_recovered_drift_row,
    post_gate_mutation_drift_row,
    projection_unavailable_drift_row,
    protected_observation_registry_summary,
    render_split_owner_acceptance_matrix_report,
    replay_drift_row,
    response_type_repair_drift_row,
    route_mismatch_drift_row,
    scaffold_leakage_drift_row,
    semantic_text_fragment_drift_row,
    speaker_mismatch_drift_row,
    split_owner_acceptance_matrix_rows,
    split_owner_fem_projection_excluded,
    split_owner_lineage_event_from_matrix_row,
    split_owner_matrix_classifier_drift_row,
    split_owner_observed_row_from_matrix_row,
    project_split_owner_matrix_row,
    assert_split_owner_matrix_fem_projection,
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
#
# CO13 lock classification (residual direct asserts after CO4–CO8):
# - scenario-specific classifier parity: canonical routing, symptom routing, precision evidence
# - row-field / lineage-event parity: split-owner projection fields + embedded lineage mirrors
# - matrix governance report prose: BU15 acceptance-matrix report anchors
# - dashboard shape / empty-dashboard markdown: columns, empty state, report fragments
# - validation error lock: invalid buckets, short owner names, unknown split owners
# - static/AST structural lock: compat-local literal scan, deprecated alias guards
# Repeated row/lineage literals across families are intentional parity locks unless noted.


# --- Registry/sync parity locks ------------------------------------------------


def test_classifier_tables_stay_aligned_with_contract():
    assert_contract_classifier_alignment()


def test_classifier_consumer_reads_taxonomy_from_sync_helpers():
    summary = classification_contract_summary()
    categories = known_failure_categories()
    buckets = known_owner_buckets()
    registry_summary = protected_observation_registry_summary()
    row_fields = expected_failure_classification_row_fields()

    assert_classification_contract_summary(
        summary,
        categories=categories,
        owner_buckets=buckets,
    )
    assert_classification_contract_categories_contain(categories, "speaker", "fallback")
    assert_owner_buckets_contain(
        buckets,
        opening=(OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED, OPENING_FALLBACK_OWNER_SEALED_GATE),
        sealed=(SEALED_FALLBACK_OWNER_SEALED_GATE,),
    )
    assert_registry_summary_counts(registry_summary)
    assert_registry_summary_contains(
        registry_summary,
        fallback_family_bucket="structural_drift",
        scaffold_leakage_bucket="semantic_drift",
    )
    assert_registry_contract_fields(
        summary,
        row_fields,
        required_contains=("category",),
        optional_evidence_contains=("fallback_family",),
    )


# --- Scenario-specific classifier parity (canonical routing) -------------------


@pytest.mark.parametrize(
    ("case", "observed", "drift_row", "expected"),
    [
        (
            "wrong speaker",
            observed_speaker_mismatch_observed_row(),
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
            observed_response_type_repair_row("dialogue_shape"),
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
    assert_classification_owner_mapping(
        row,
        category=category,
        primary_owner=owner,
        severity=severity,
        investigate_first=target,
    )


# --- Dashboard shape / empty-dashboard markdown --------------------------------


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
    assert_lineage_aggregation_parity(
        summary,
        total_events=5,
        fallback_frequency={"scene_opening": 2},
        fallback_authorship_frequency={"upstream_prepared_opening_fallback": 2},
        fallback_owner_bucket_frequency={"upstream-prepared": 2},
        fallback_selection_owner_frequency={"game.final_emission_gate": 2},
        fallback_content_owner_frequency={"game.opening_deterministic_fallback": 2},
        speaker_repair_frequency={"local_rebind": 1},
        mutation_kind_frequency={"fallback_mutation": 1},
        gate_path_frequency={"opening_fallback": 1},
        first_recurring_count=2,
    )

    ordinary = render_failure_dashboard_markdown(rows, generated_at="2026-05-11T00:00:00Z", command_used="pytest")
    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest",
        runtime_lineage_events=events,
    )
    assert_runtime_lineage_summary_absent(ordinary)
    assert_runtime_lineage_summary_contains(
        report,
        total_events=5,
        fallback_selected=2,
        frequency_rows={
            "scene_opening": 2,
            "upstream_prepared_opening_fallback": 2,
            "upstream-prepared": 2,
            "game.final_emission_gate": 2,
            "game.opening_deterministic_fallback": 2,
            "local_rebind": 1,
            "fallback_mutation": 1,
            "opening_fallback": 1,
        },
    )
    assert rows[0]["category"] == "fallback"


# --- Scenario-specific classifier parity (opening fallback projection) -----------
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
            legacy_compatibility_local_opening_classifier_row(),
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

    assert_failure_classification_row(
        row,
        category="fallback",
        source_family="opening_fallback",
        emission_sublayer="opening_fallback",
        opening_fallback_owner_bucket=expected_bucket,
        opening_fallback_authorship_source=observed.get("opening_fallback_authorship_source"),
    )


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

    assert_failure_classification_row(
        row,
        opening_fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        source_family="opening_fallback",
        investigate_first="game/final_emission_meta.py",
    )


def test_failure_classifier_routes_opening_authorship_payload_symptom_to_upstream_repairs():
    row = classify_replay_probe_row(
        scenario_id="opening_authorship_payload",
        turn_index=0,
        observed_turn=legacy_compatibility_local_opening_classifier_row(),
        drift_row=exact_value_drift_row(
            "opening_fallback_authorship_source",
            expected="upstream_prepared_opening_fallback",
            actual=legacy_compatibility_local_opening_classifier_row()[
                "opening_fallback_authorship_source"
            ],
        ),
    )

    assert_classification_owner_mapping(
        row,
        category="fallback",
        investigate_first="game/upstream_response_repairs.py",
    )
    assert_failure_classification_row(row, source_family="opening_fallback")


def test_ordinary_classifier_opening_builders_never_emit_compat_local_authorship() -> None:
    """Current-path opening classifier rows must use upstream-prepared authorship or omit authorship."""
    from game.attribution_read_views import OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES

    ordinary_builders = (
        observed_opening_fallback_row,
        observed_fail_closed_opening_fallback_row,
        observed_opening_family_split_owner_row,
    )
    for builder in ordinary_builders:
        if builder is observed_opening_family_split_owner_row:
            row = builder(
                fallback_kind="scene_opening",
                fallback_content_owner=OPENING_FALLBACK_CONTENT_OWNER,
                opening_fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            )
        else:
            row = builder()
        authorship = row.get("opening_fallback_authorship_source")
        if authorship is not None:
            assert authorship not in OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES


# --- Static/AST structural lock (compat-local authorship literals) -------------


def test_only_legacy_named_helpers_emit_compat_local_opening_authorship() -> None:
    """Retired authorship must be reachable only through explicit legacy-evidence helpers."""
    import importlib

    from tests.helpers.opening_fallback_evidence import (
        build_legacy_compatibility_local_opening_fallback_evidence,
        legacy_compatibility_local_opening_authorship_meta,
        legacy_compatibility_local_opening_authorship_source,
    )
    from tests.helpers.failure_classification_builders import (
        legacy_compatibility_local_opening_authorship_classifier_row,
    )

    for deprecated in (
        "observed_legacy_opening_fallback_row",
        "observed_opening_authorship_compat_row",
    ):
        assert not hasattr(importlib.import_module("tests.helpers.failure_classification_builders"), deprecated)

    legacy_token = legacy_compatibility_local_opening_authorship_source()
    legacy_row = legacy_compatibility_local_opening_classifier_row()
    assert legacy_row["opening_fallback_authorship_source"] == legacy_token
    authorship_row = legacy_compatibility_local_opening_authorship_classifier_row()
    assert authorship_row["opening_fallback_authorship_source"] == legacy_token
    assert (
        build_legacy_compatibility_local_opening_fallback_evidence()["opening_fallback_authorship_source"]
        == legacy_token
    )
    assert (
        legacy_compatibility_local_opening_authorship_meta()["opening_fallback_authorship_source"]
        == legacy_token
    )


def test_failure_classification_builders_compat_local_literals_only_in_legacy_helpers() -> None:
    """Static lock: compat-local authorship literals only in legacy_compatibility_local_* builders."""
    import ast
    from pathlib import Path

    from game.attribution_read_views import (
        OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES,
    )

    path = Path(__file__).resolve().parent / "helpers" / "failure_classification_builders.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    legacy_tokens = frozenset(OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES)
    deprecated_aliases = frozenset(
        {
            "observed_legacy_opening_fallback_row",
            "observed_opening_authorship_compat_row",
        }
    )

    defined_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert deprecated_aliases.isdisjoint(defined_names), (
        f"deprecated aliases remain: {sorted(deprecated_aliases & defined_names)}"
    )

    offenders: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("legacy_compatibility_local_"):
                continue
            scope = node.name
        else:
            scope = "module"
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                if child.value in legacy_tokens:
                    offenders.append(f"{scope}:{child.lineno}:{child.value!r}")
    assert offenders == []


# --- Scenario-specific classifier parity (opening symptom routing) -------------


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

    assert_classification_owner_mapping(row, investigate_first="game/opening_deterministic_fallback.py")


def test_failure_classifier_routes_opening_projection_omission_to_golden_replay():
    row = classify_replay_probe_row(
        scenario_id="opening_projection_missing",
        turn_index=0,
        observed_turn=observed_opening_projection_missing_row(),
        drift_row=projection_unavailable_drift_row(
            "opening_fallback_owner_bucket",
            expected=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
    )

    assert_classification_owner_mapping(
        row,
        category="projection",
        investigate_first="tests/helpers/golden_replay.py",
    )


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

    assert_classification_owner_mapping(
        row,
        category="fallback",
        investigate_first="game/final_emission_gate.py",
    )


# --- Validation error lock (invalid fallback owner buckets) --------------------


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
    assert_classification_owner_mapping(row, investigate_first="game/final_emission_meta.py")


# --- Scenario-specific classifier parity (sealed/visibility projection) --------
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

    assert_failure_classification_row(
        row,
        category="fallback",
        sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
    )


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

    assert_failure_classification_row(
        row,
        category="fallback",
        visibility_fallback_owner_bucket="sealed-gate",
        visibility_replacement_applied=True,
        visibility_fallback_pool="global_scene_narrative",
        visibility_fallback_kind="narrative_safe_fallback",
    )


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


# --- Dashboard shape / empty-dashboard markdown --------------------------------


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

    assert_classification_owner_mapping(
        rows[0],
        primary_owner="route",
        severity="medium",
        investigate_first="game/interaction_context.py",
    )
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


# --- Scenario-specific classifier parity (precision evidence) ------------------


@pytest.mark.parametrize(
    ("case", "observed", "drift_row", "expected"),
    [
        (
            "answer upstream prepared repair sublayer",
            observed_response_type_repair_row("answer_upstream_prepared_repair"),
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "answer_upstream_prepared_repair", None),
        ),
        (
            "action outcome upstream prepared repair sublayer",
            observed_response_type_repair_row("action_outcome_upstream_prepared_repair"),
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "action_outcome_upstream_prepared_repair", None),
        ),
        (
            "strict social dialogue repair sublayer",
            observed_response_type_repair_row("strict_social_dialogue_repair"),
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "strict_social_dialogue_repair", None),
        ),
        (
            "dialogue minimal repair sublayer",
            observed_response_type_repair_row("dialogue_minimal_repair"),
            response_type_repair_drift_row(),
            ("emission", "emission", "validator", "medium", "game/final_emission_gate.py", "response_type", "dialogue_minimal_repair", None),
        ),
        (
            "legacy thin answer backward-compatible sublayer",
            observed_response_type_repair_row("thin_answer"),
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
            observed_post_gate_mutation_row(),
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

    assert_failure_classification_row(
        row,
        category=category,
        primary_owner=primary,
        secondary_owner=secondary,
        severity=severity,
        investigate_first=target,
        emission_sublayer=sublayer,
        repair_kind=repair_kind,
        missing_source_kind=missing_kind,
    )


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
        observed_turn=observed_post_gate_mutation_row(final_emission_mutation_lineage=lineage),
        drift_rows=[post_gate_mutation_drift_row()],
    )[0]

    assert_failure_classification_row(
        row,
        category="emission",
        emission_sublayer=expected_source,
        mutation_source=expected_source,
        final_emission_mutation_lineage=lineage,
    )


def test_failure_classifier_keeps_post_gate_unknown_without_lineage_or_specific_evidence():
    row = classify_replay_failure(
        scenario_id="post_gate_no_lineage_unknown",
        turn_index=0,
        observed_turn=observed_post_gate_mutation_row(final_emission_mutation_lineage=None),
        drift_rows=[post_gate_mutation_drift_row()],
    )[0]

    assert_failure_classification_row(
        row,
        emission_sublayer="emission.post_gate_mutation_unknown",
        mutation_source="emission.post_gate_mutation_unknown",
    )


def test_cu3_failure_classifier_prefers_write_site_over_projection_inference():
    rows = build_failure_dashboard_rows(
        observed_turn={
            "scenario_id": "cu3_classifier_write_site",
            "turn_index": 1,
            "final_text_hash": "hash",
            "semantic_mutation_write_sites": [
                {
                    "write_site_family": "fallback",
                    "write_site_file": "game/fallback_provenance_debug.py",
                    "write_site_function": "finalize_upstream_fallback_overwrite_containment",
                    "owner": "game.fallback_provenance_debug",
                    "selected_active_stream": True,
                    "candidate_only": False,
                }
            ],
            "first_semantic_mutation_bucket": "sanitizer",
            "first_semantic_mutation_owner": "game.output_sanitizer",
            "first_semantic_mutation_source": "projected.sanitizer",
        },
        drift_rows=[
            {
                "field_path": "final_text",
                "expected": "old",
                "actual": "new",
                "drift_bucket": "semantic_drift",
                "reason": "semantic mutation",
            }
        ],
    )

    assert rows[0]["category"] == "semantic_mutation"
    assert rows[0]["authoritative_mutation_owner"] == "game.fallback_provenance_debug"
    assert rows[0]["authoritative_mutation_family"] == "fallback"
    assert rows[0]["authoritative_evidence_source"] == "write_site"
    assert rows[0]["used_projection_inference"] is False
    assert rows[0]["mutation_source"] == "fallback"


def test_cu3_failure_classifier_uses_projection_inference_only_without_write_site():
    rows = build_failure_dashboard_rows(
        observed_turn={
            "scenario_id": "cu3_classifier_inference",
            "turn_index": 1,
            "final_text_hash": "hash",
            "first_semantic_mutation_bucket": "sanitizer",
            "first_semantic_mutation_owner": "game.output_sanitizer",
            "first_semantic_mutation_source": "projected.sanitizer",
        },
        drift_rows=[
            {
                "field_path": "final_text",
                "expected": "old",
                "actual": "new",
                "drift_bucket": "semantic_drift",
                "reason": "semantic mutation",
            }
        ],
    )

    assert rows[0]["authoritative_mutation_owner"] == "game.output_sanitizer"
    assert rows[0]["authoritative_mutation_family"] == "sanitizer"
    assert rows[0]["authoritative_evidence_source"] == "projection_inference"
    assert rows[0]["used_projection_inference"] is True


# --- Scenario-specific classifier parity (prepared emission routing) -----------


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
        observed_turn=observed_upstream_prepared_emission_row(
            response_type_repair_kind=repair_kind,
            upstream_prepared_emission_source=source_field,
        ),
        drift_rows=[response_type_repair_drift_row()],
    )[0]

    assert_split_owner_classification(
        row,
        category="emission",
        primary_owner="upstream_prepared_emission",
        secondary_owner="emission",
        source_family="upstream_prepared_emission",
        investigate_first="game/final_emission_gate.py",
        emission_sublayer="upstream_prepared_emission",
        prepared_emission_owner="upstream_prepared_emission",
        upstream_prepared_emission_used=True,
        upstream_prepared_emission_valid=True,
        upstream_prepared_emission_source=source_field,
    )


def test_failure_classifier_preserves_rejected_prepared_emission_reason():
    row = classify_replay_probe_row(
        scenario_id="malformed_prepared_owner",
        turn_index=0,
        observed_turn=observed_upstream_prepared_emission_row(
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_source="prepared_action_fallback_text",
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_reject_reason="missing_concrete_action_outcome",
        ),
        drift_row=replay_drift_row(
            "upstream_prepared_emission_valid",
            expected=True,
            actual=False,
            reason="malformed prepared emission rejected",
        ),
    )

    assert_failure_classification_row(
        row,
        primary_owner="upstream_prepared_emission",
        prepared_emission_owner="upstream_prepared_emission",
        upstream_prepared_emission_valid=False,
        upstream_prepared_emission_reject_reason="missing_concrete_action_outcome",
    )


def test_failure_dashboard_evidence_shows_rejected_prepared_emission_reason():
    rows = build_failure_dashboard_rows(
        observed_turn=observed_upstream_prepared_emission_row(
            response_type_repair_used=False,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_source="upstream_prepared_emission.prepared_action_fallback_text",
            upstream_prepared_emission_valid=False,
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
    assert_prepared_emission_evidence(
        report,
        status="rejected",
        reject_reason="action_outcome_missing_result",
    )


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

    assert_split_owner_classification(
        row,
        category="emission",
        primary_owner="emission",
        secondary_owner="validator",
        source_family="upstream_prepared_emission",
        prepared_emission_owner=None,
    )


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

    assert_split_owner_classification(
        row,
        category="sanitizer",
        primary_owner="sanitizer",
        secondary_owner="emission",
        source_family="output_sanitizer",
        emission_sublayer="sanitizer",
        prepared_emission_owner=None,
        sanitizer_empty_fallback_owner="game.output_sanitizer",
        sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
    )


@pytest.mark.parametrize("repair_kind", ["strict_social_dialogue_repair", "dialogue_minimal_repair"])
def test_failure_classifier_keeps_dialogue_repairs_separate_from_prepared_emission(repair_kind):
    row = classify_replay_failure(
        scenario_id=f"{repair_kind}_separate",
        turn_index=0,
        observed_turn=observed_response_type_repair_row(repair_kind),
        drift_rows=[response_type_repair_drift_row()],
    )[0]

    assert_split_owner_classification(
        row,
        primary_owner="emission",
        source_family="final_emission_gate",
        emission_sublayer="response_type",
        prepared_emission_owner=None,
    )


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
    assert_sanitizer_empty_fallback_evidence(
        report,
        source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
        owner="game.output_sanitizer",
    )


def test_failure_classifier_missing_prepared_emission_telemetry_preserves_legacy_owner():
    row = classify_replay_failure(
        scenario_id="legacy_no_prepared_telemetry",
        turn_index=0,
        observed_turn=observed_response_type_repair_row("answer_upstream_prepared_repair"),
        drift_rows=[response_type_repair_drift_row()],
    )[0]

    assert_split_owner_classification(
        row,
        primary_owner="emission",
        secondary_owner="validator",
        source_family="final_emission_gate",
        emission_sublayer="response_type",
        prepared_emission_owner=None,
    )


def test_failure_dashboard_evidence_column_compacts_precision_fields():
    rows = build_failure_dashboard_rows(
        observed_turn=observed_upstream_prepared_emission_row(
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
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

    assert_dashboard_evidence_column_present(report)
    assert_prepared_emission_evidence(
        report,
        status="used",
        valid=True,
        source="prepared_action_fallback_text",
    )
    assert_compact_evidence_field(report, "sublayer", "upstream_prepared_emission")
    assert_compact_evidence_field(report, "repair", "action_outcome_upstream_prepared_repair")
    assert_compact_evidence_field(
        report,
        "lineage",
        "pre_gate_sanitizer>response_type_repair>prepared_emission_selection>finalize_packaging",
    )
    assert_compact_evidence_field(report, "sanitizer_mode", "strip_only")
    assert_compact_evidence_field(report, "sanitizer_events", 2)
    assert_sanitizer_lineage_evidence(
        report,
        mode="strip_only",
        changed=2,
        dropped=1,
        empty=False,
        legacy=False,
    )


def test_failure_dashboard_evidence_preserves_legacy_thin_answer_as_backward_compatible_label():
    rows = build_failure_dashboard_rows(
        observed_turn=observed_response_type_repair_row("thin_answer"),
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
    assert_compact_evidence_field(report, "repair", "thin_answer")


def test_failure_classifier_legacy_sanitizer_rewrite_is_diagnostic_output_sanitizer_evidence():
    rows = build_failure_dashboard_rows(
        observed_turn=observed_sanitizer_legacy_rewrite_row(),
        drift_rows=[scaffold_leakage_drift_row(reason="legacy sentence rewrite diagnostic evidence")],
        scenario_id="legacy_sanitizer_rewrite_probe",
        turn_index=2,
    )

    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-05-13T00:00:00Z",
        command_used="pytest legacy sanitizer evidence",
    )

    assert_split_owner_classification(
        rows[0],
        category="sanitizer",
        primary_owner="sanitizer",
        secondary_owner="emission",
        source_family="output_sanitizer",
        emission_sublayer="sanitizer",
        sanitizer_lineage_legacy_rewrite_active=True,
    )
    assert_sanitizer_lineage_evidence(
        report,
        mode="legacy_sentence_rewrite",
        legacy="legacy_diagnostic",
    )


def test_failure_classifier_strict_social_sanitizer_fallback_keeps_selection_and_prose_owners_split():
    rows = build_failure_dashboard_rows(
        observed_turn=_observed(
            strict_social_active=True,
            sanitizer_strict_social_fallback_used=True,
            sanitizer_strict_social_selection_owner="game.output_sanitizer",
            sanitizer_strict_social_prose_owner="game.social_exchange_emission",
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

    assert_split_owner_classification(
        rows[0],
        category="sanitizer",
        primary_owner="sanitizer",
        source_family="output_sanitizer",
        emission_sublayer="strict_social_replacement",
        prepared_emission_owner=None,
        sanitizer_empty_fallback_used=None,
        sanitizer_strict_social_selection_owner="game.output_sanitizer",
        sanitizer_strict_social_prose_owner="game.social_exchange_emission",
    )
    assert_strict_social_sanitizer_evidence(
        report,
        selection_owner="game.output_sanitizer",
        prose_owner="game.social_exchange_emission",
        source="social_fallback_line_for_sanitizer.empty_output",
    )


# --- Row-field / lineage-event parity (split-owner runtime lineage) --------------
# Direct row-field and embedded-event asserts lock classifier projection against lineage.


@pytest.mark.parametrize(
    (
        "scenario_suffix",
        "fallback_kind",
        "fallback_content_owner",
        "opening_fallback_owner_bucket",
        "repair_kind",
    ),
    [
        (
            "scene_opening",
            "scene_opening",
            OPENING_FALLBACK_CONTENT_OWNER,
            OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            "opening_deterministic_fallback",
        ),
        (
            "opening_failed_closed",
            "opening_failed_closed",
            OPENING_FAIL_CLOSED_CONTENT_OWNER,
            OPENING_FALLBACK_OWNER_SEALED_GATE,
            "opening_deterministic_fallback_failed_closed",
        ),
    ],
)
def test_failure_classifier_accepts_opening_family_runtime_lineage_split_owners(
    scenario_suffix: str,
    fallback_kind: str,
    fallback_content_owner: str,
    opening_fallback_owner_bucket: str,
    repair_kind: str | None,
) -> None:
    observed = observed_opening_family_split_owner_row(
        fallback_kind=fallback_kind,
        fallback_content_owner=fallback_content_owner,
        opening_fallback_owner_bucket=opening_fallback_owner_bucket,
    )
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected=OPENING_FALLBACK_SELECTION_OWNER,
                actual=fallback_content_owner,
                reason=f"{scenario_suffix} opening-family split owner projection changed",
            )
        ],
        scenario_id=f"opening_family_split_owner_{scenario_suffix}",
        turn_index=0,
    )
    report = render_failure_dashboard_markdown(rows, generated_at="2026-06-20T00:00:00Z", command_used="pytest")

    assert rows[0]["fallback_selection_owner"] == OPENING_FALLBACK_SELECTION_OWNER
    assert rows[0]["fallback_content_owner"] == fallback_content_owner
    assert rows[0]["opening_fallback_owner_bucket"] == opening_fallback_owner_bucket
    if repair_kind is not None:
        assert rows[0]["repair_kind"] == repair_kind
    assert_failure_dashboard_row_shape(rows[0])
    assert_fallback_authorship_evidence(
        report,
        selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        content_owner=fallback_content_owner,
        opening_owner=opening_fallback_owner_bucket,
        repair=repair_kind,
    )
    fallback = next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_owner_bucket"] == opening_fallback_owner_bucket
    assert fallback["fallback_selection_owner"] == OPENING_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == fallback_content_owner


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


@pytest.mark.parametrize(
    (
        "scenario_suffix",
        "observed_kwargs",
        "fallback_kind",
        "repair_kind",
        "expected_bucket",
        "expected_content_owner",
    ),
    [
        (
            "visibility_enforcement",
            {
                "visibility_replacement_applied": True,
                "fallback_kind": VISIBILITY_HARD_REPLACEMENT,
                "repair_kind": "visibility_enforcement",
            },
            VISIBILITY_HARD_REPLACEMENT,
            "visibility_enforcement",
            "sealed-gate",
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "first_mention_enforcement",
            {
                "first_mention_replacement_applied": True,
                "fallback_kind": FIRST_MENTION_HARD_REPLACEMENT,
                "repair_kind": "first_mention_enforcement",
            },
            FIRST_MENTION_HARD_REPLACEMENT,
            "first_mention_enforcement",
            "sealed-gate",
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "referential_clarity_enforcement",
            {
                "referential_clarity_replacement_applied": True,
                "fallback_kind": REFERENTIAL_CLARITY_HARD_REPLACEMENT,
                "repair_kind": "referential_clarity_enforcement",
                "visibility_fallback_owner_bucket": "strict-social-visibility",
                "fallback_content_owner": STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
            },
            REFERENTIAL_CLARITY_HARD_REPLACEMENT,
            "referential_clarity_enforcement",
            "strict-social-visibility",
            STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        ),
    ],
)
def test_failure_classifier_accepts_visibility_family_runtime_lineage_split_owners(
    scenario_suffix: str,
    observed_kwargs: dict,
    fallback_kind: str,
    repair_kind: str,
    expected_bucket: str,
    expected_content_owner: str,
) -> None:
    observed = observed_visibility_family_hard_replacement_row(**observed_kwargs)
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected="game.final_emission_gate",
                actual=expected_content_owner,
                reason=f"{scenario_suffix} split owner projection changed",
            )
        ],
        scenario_id=f"visibility_family_split_owner_{scenario_suffix}",
        turn_index=0,
    )
    report = render_failure_dashboard_markdown(rows, generated_at="2026-06-20T00:00:00Z", command_used="pytest")

    assert rows[0]["fallback_selection_owner"] == VISIBILITY_FALLBACK_SELECTION_OWNER
    assert rows[0]["fallback_content_owner"] == expected_content_owner
    assert rows[0]["visibility_fallback_owner_bucket"] == expected_bucket
    assert rows[0]["repair_kind"] == repair_kind
    assert_failure_dashboard_row_shape(rows[0])
    assert_fallback_authorship_evidence(
        report,
        selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        content_owner=expected_content_owner,
        visibility_owner=expected_bucket,
        repair=repair_kind,
    )
    fallback = next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_owner_bucket"] == expected_bucket


@pytest.mark.parametrize(
    (
        "scenario_suffix",
        "observed_kwargs",
        "fallback_kind",
        "repair_kind",
        "expected_content_owner",
    ),
    [
        (
            "strict_social",
            {
                "fallback_kind": "sanitizer_strict_social",
                "fallback_content_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                "repair_kind": "strict_social_repair",
            },
            "sanitizer_strict_social",
            "strict_social_repair",
            SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
        ),
        (
            "empty_output",
            {
                "fallback_kind": "sanitizer_empty_output",
                "fallback_content_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                "repair_kind": "sanitizer_empty_output",
            },
            "sanitizer_empty_output",
            "sanitizer_empty_output",
            SANITIZER_FALLBACK_SELECTION_OWNER,
        ),
    ],
)
def test_failure_classifier_accepts_sanitizer_runtime_lineage_split_owners(
    scenario_suffix: str,
    observed_kwargs: dict,
    fallback_kind: str,
    repair_kind: str,
    expected_content_owner: str,
) -> None:
    observed = observed_sanitizer_split_owner_row(**observed_kwargs)
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected="game.final_emission_gate",
                actual=expected_content_owner,
                reason=f"{scenario_suffix} sanitizer split owner projection changed",
            )
        ],
        scenario_id=f"sanitizer_split_owner_{scenario_suffix}",
        turn_index=0,
    )
    report = render_failure_dashboard_markdown(rows, generated_at="2026-06-20T00:00:00Z", command_used="pytest")

    assert rows[0]["fallback_selection_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert rows[0]["fallback_content_owner"] == expected_content_owner
    assert rows[0]["repair_kind"] == repair_kind
    assert_failure_dashboard_row_shape(rows[0])
    assert_fallback_authorship_evidence(
        report,
        selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        content_owner=expected_content_owner,
        repair=repair_kind,
    )
    fallback = next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_selection_owner"] == SANITIZER_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == expected_content_owner


def test_failure_classifier_accepts_upstream_fast_runtime_lineage_split_owners() -> None:
    observed = observed_upstream_fast_split_owner_row()
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
                actual=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
                reason="upstream-fast split owner projection changed",
            )
        ],
        scenario_id="upstream_fast_split_owner_probe",
        turn_index=0,
    )
    report = render_failure_dashboard_markdown(rows, generated_at="2026-06-20T00:00:00Z", command_used="pytest")

    assert rows[0]["fallback_selection_owner"] == UPSTREAM_FAST_FALLBACK_SELECTION_OWNER
    assert rows[0]["fallback_content_owner"] == UPSTREAM_FAST_FALLBACK_CONTENT_OWNER
    assert_failure_dashboard_row_shape(rows[0])
    assert_fallback_authorship_evidence(
        report,
        selection_owner=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        content_owner=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    )
    fallback = next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == "upstream_fast_fallback"
    assert fallback["stage"] == "retry"


@pytest.mark.parametrize(
    (
        "scenario_suffix",
        "fallback_kind",
        "final_emitted_source",
        "expected_bucket",
        "expected_content_owner",
    ),
    [
        (
            "social_interlocutor",
            SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
            "social_interlocutor_minimal_fallback",
            "strict-social-sealed",
            STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        ),
        (
            "passive_scene_pressure",
            SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
            "passive_scene_pressure_fallback",
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "npc_pursuit_neutral",
            SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
            "npc_pursuit_neutral_fallback",
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "anti_reset_continuation",
            SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
            "anti_reset_local_continuation_fallback",
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "global_scene",
            SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
            "global_scene_fallback",
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "unknown_replacement",
            SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
            "unclassified_terminal_fallback",
            "unknown-none",
            SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        ),
        (
            "legacy_sealed_or_global",
            "sealed_or_global_replacement",
            "global_scene_fallback",
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        ),
    ],
)
def test_failure_classifier_accepts_sealed_family_runtime_lineage_split_owners(
    scenario_suffix: str,
    fallback_kind: str,
    final_emitted_source: str,
    expected_bucket: str,
    expected_content_owner: str,
) -> None:
    observed = observed_sealed_family_split_owner_row(
        fallback_kind=fallback_kind,
        final_emitted_source=final_emitted_source,
        fallback_content_owner=expected_content_owner,
        sealed_fallback_owner_bucket=expected_bucket,
    )
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected=SEALED_FALLBACK_SELECTION_OWNER,
                actual=expected_content_owner,
                reason=f"{scenario_suffix} sealed-family split owner projection changed",
            )
        ],
        scenario_id=f"sealed_family_split_owner_{scenario_suffix}",
        turn_index=0,
    )
    report = render_failure_dashboard_markdown(rows, generated_at="2026-06-20T00:00:00Z", command_used="pytest")

    assert rows[0]["fallback_selection_owner"] == SEALED_FALLBACK_SELECTION_OWNER
    assert rows[0]["fallback_content_owner"] == expected_content_owner
    assert rows[0]["sealed_fallback_owner_bucket"] == expected_bucket
    assert_failure_dashboard_row_shape(rows[0])
    assert_fallback_authorship_evidence(
        report,
        selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        content_owner=expected_content_owner,
        sealed_owner=expected_bucket,
    )
    fallback = next(
        event for event in observed["runtime_lineage_events"] if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_owner_bucket"] == expected_bucket
    assert fallback["fallback_selection_owner"] == SEALED_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == expected_content_owner


# --- Row-field / lineage-event parity (lineage summary trifecta) ----------------


def test_failure_dashboard_runtime_lineage_summary_counts_sanitizer_upstream_fast_owner_trifecta() -> None:
    sanitizer_strict = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="sanitizer",
        owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_kind="sanitizer_strict_social",
        fallback_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    )
    sanitizer_empty = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="sanitizer",
        owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_kind="sanitizer_empty_output",
        fallback_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
    )
    upstream_fast = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="retry",
        owner=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        fallback_kind="upstream_fast_fallback",
        fallback_owner_bucket="retry",
        fallback_selection_owner=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    )
    events = [sanitizer_strict, sanitizer_empty, upstream_fast, upstream_fast]
    summary = build_runtime_lineage_summary(events)

    assert_lineage_aggregation_parity(
        summary,
        total_events=4,
        fallback_frequency={
            "sanitizer_strict_social": 1,
            "sanitizer_empty_output": 1,
            "upstream_fast_fallback": 2,
        },
        fallback_owner_bucket_frequency={"retry": 2},
        fallback_selection_owner_frequency={
            SANITIZER_FALLBACK_SELECTION_OWNER: 2,
            UPSTREAM_FAST_FALLBACK_SELECTION_OWNER: 2,
        },
        fallback_content_owner_frequency={
            SANITIZER_FALLBACK_SELECTION_OWNER: 1,
            SANITIZER_STRICT_SOCIAL_CONTENT_OWNER: 1,
            UPSTREAM_FAST_FALLBACK_CONTENT_OWNER: 2,
        },
    )

    report = render_failure_dashboard_markdown(
        [],
        generated_at="2026-06-20T00:00:00Z",
        command_used="pytest sanitizer-upstream-lineage-summary",
        runtime_lineage_events=events,
    )
    assert_runtime_lineage_source_counts(
        report,
        {
            "game.output_sanitizer": 2,
            "game.social_exchange_emission": 1,
            "game.api": 2,
            "game.gm_retry": 2,
            "retry": 2,
        },
    )


def test_failure_dashboard_runtime_lineage_summary_counts_sealed_family_split_owner_trifecta() -> None:
    global_scene = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
        fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    )
    social_interlocutor = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
        fallback_owner_bucket="strict-social-sealed",
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    )
    unknown_replacement = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
        fallback_owner_bucket="unknown-none",
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    )
    events = [global_scene, social_interlocutor, unknown_replacement, global_scene]
    summary = build_runtime_lineage_summary(events)

    assert_lineage_aggregation_parity(
        summary,
        total_events=4,
        fallback_frequency={
            SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE: 2,
            SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR: 1,
            SEALED_REPLACEMENT_SUBKIND_UNKNOWN: 1,
        },
        fallback_owner_bucket_frequency={
            SEALED_FALLBACK_OWNER_SEALED_GATE: 2,
            "strict-social-sealed": 1,
            "unknown-none": 1,
        },
        fallback_selection_owner_frequency={SEALED_FALLBACK_SELECTION_OWNER: 4},
        fallback_content_owner_frequency={
            SEALED_FALLBACK_MODULE_CONTENT_OWNER: 2,
            STRICT_SOCIAL_FALLBACK_CONTENT_OWNER: 1,
            SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER: 1,
        },
    )

    report = render_failure_dashboard_markdown(
        [],
        generated_at="2026-06-20T00:00:00Z",
        command_used="pytest sealed-family-lineage-summary",
        runtime_lineage_events=events,
    )
    assert_runtime_lineage_source_counts(
        report,
        {
            "game.final_emission_gate": 4,
            "game.final_emission_sealed_fallback": 2,
            "game.social_exchange_emission": 1,
            "sealed-gate": 2,
            "strict-social-sealed": 1,
            "unknown-none": 1,
        },
    )


def test_failure_dashboard_runtime_lineage_summary_counts_opening_family_split_owner_trifecta() -> None:
    scene_opening = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_kind="scene_opening",
        fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        fallback_authorship_source="upstream_prepared_opening_fallback",
        fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=OPENING_FALLBACK_CONTENT_OWNER,
        repair_kind="opening_deterministic_fallback",
    )
    opening_failed_closed = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_kind="opening_failed_closed",
        fallback_owner_bucket=OPENING_FALLBACK_OWNER_SEALED_GATE,
        fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=OPENING_FAIL_CLOSED_CONTENT_OWNER,
        repair_kind="opening_deterministic_fallback_failed_closed",
    )
    events = [scene_opening, opening_failed_closed, scene_opening]
    summary = build_runtime_lineage_summary(events)

    assert_lineage_aggregation_parity(
        summary,
        total_events=3,
        fallback_frequency={"scene_opening": 2, "opening_failed_closed": 1},
        fallback_owner_bucket_frequency={
            OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED: 2,
            OPENING_FALLBACK_OWNER_SEALED_GATE: 1,
        },
        fallback_selection_owner_frequency={OPENING_FALLBACK_SELECTION_OWNER: 3},
        fallback_content_owner_frequency={
            OPENING_FALLBACK_CONTENT_OWNER: 2,
            OPENING_FAIL_CLOSED_CONTENT_OWNER: 1,
        },
    )

    report = render_failure_dashboard_markdown(
        [],
        generated_at="2026-06-20T00:00:00Z",
        command_used="pytest opening-family-lineage-summary",
        runtime_lineage_events=events,
    )
    assert_runtime_lineage_source_counts(
        report,
        {
            "game.final_emission_gate": 3,
            "game.opening_deterministic_fallback": 2,
            "upstream-prepared": 2,
            "sealed-gate": 1,
        },
    )


def test_failure_classifier_accepts_sanitizer_strip_only_producer_repair_kind() -> None:
    observed = {
        "final_route": "accept_candidate",
        "sanitizer_mode": "strip_only",
        "sanitizer_lineage_mode": "strip_only",
        "sanitizer_event_count": 1,
        "sanitizer_changed_count": 1,
        "sanitizer_lineage_changed_count": 1,
        "producer_repair_kind": "sanitizer_strip_only",
        "sealed_fallback_owner_bucket": "unknown-none",
    }
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "producer_repair_kind",
                expected=None,
                actual="sanitizer_strip_only",
                reason="sanitizer strip-only producer stamp",
            )
        ],
        scenario_id="sanitizer_strip_only_classifier_probe",
        turn_index=0,
    )
    assert rows[0]["repair_kind"] == "sanitizer_strip_only"
    assert_failure_dashboard_row_shape(rows[0])


def test_failure_classifier_accepts_passive_scene_concrete_beat_producer_repair_kind() -> None:
    observed = {
        "final_route": "accept_candidate",
        "passive_scene_concrete_beat_satisfier_applied": True,
        "passive_scene_pressure_fallback_avoided": True,
        "producer_repair_kind": "passive_scene_concrete_beat",
    }
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "producer_repair_kind",
                expected=None,
                actual="passive_scene_concrete_beat",
                reason="passive scene upstream satisfier producer stamp",
            )
        ],
        scenario_id="passive_scene_concrete_beat_classifier_probe",
        turn_index=0,
    )
    assert rows[0]["repair_kind"] == "passive_scene_concrete_beat"
    assert_failure_dashboard_row_shape(rows[0])


def test_failure_classifier_accepts_referential_local_substitution_producer_bucket_without_short_owner_names() -> None:
    observed = observed_referential_local_substitution_classifier_row()
    rows = build_failure_dashboard_rows(
        observed_turn=observed,
        drift_rows=[
            exact_value_drift_row(
                "producer_repair_kind",
                expected="visibility_enforcement",
                actual="referential_clarity_local_substitution",
                reason="local substitution repair kind drift",
            )
        ],
        scenario_id="referential_local_substitution_classifier_probe",
        turn_index=0,
    )
    report = render_failure_dashboard_markdown(rows, generated_at="2026-06-20T00:00:00Z", command_used="pytest")

    assert rows[0]["visibility_fallback_owner_bucket"] == "strict-social-visibility"
    assert rows[0]["repair_kind"] == "referential_clarity_local_substitution"
    assert rows[0]["fallback_selection_owner"] is None
    assert rows[0]["fallback_content_owner"] is None
    assert_failure_dashboard_row_shape(rows[0])
    assert_fallback_authorship_evidence(
        report,
        visibility_owner="strict-social-visibility",
        repair="referential_clarity_local_substitution",
    )
    assert_dashboard_evidence_cell(report, "fallback_selection_owner=", present=False)


# --- Validation error lock (short owner names and unknown split owners) --------


def test_failure_classification_contract_rejects_short_names_on_visibility_family_split_owner_fields() -> None:
    row = build_failure_dashboard_rows(
        observed_turn=observed_visibility_family_hard_replacement_row(
            visibility_replacement_applied=True,
            fallback_kind=VISIBILITY_HARD_REPLACEMENT,
            repair_kind="visibility_enforcement",
        ),
        drift_rows=[
            exact_value_drift_row(
                "fallback_selection_owner",
                expected="final_emission_visibility_fallback",
                actual="game.final_emission_visibility_fallback",
                reason="short selection owner rejected",
            )
        ],
        scenario_id="visibility_short_owner_probe",
        turn_index=0,
    )[0]
    row["fallback_selection_owner"] = "final_emission_visibility_fallback"
    row["fallback_content_owner"] = "final_emission_sealed_fallback"
    errors = validate_failure_classification_row(row)
    assert "invalid fallback_selection_owner: 'final_emission_visibility_fallback'" in errors
    assert "invalid fallback_content_owner: 'final_emission_sealed_fallback'" in errors

    row["fallback_selection_owner"] = VISIBILITY_FALLBACK_SELECTION_OWNER
    row["fallback_content_owner"] = SEALED_FALLBACK_MODULE_CONTENT_OWNER
    assert_failure_dashboard_row_shape(row)


def test_failure_classification_contract_rejects_short_names_on_sanitizer_upstream_split_owner_fields() -> None:
    row = build_failure_dashboard_rows(
        observed_turn=observed_sanitizer_split_owner_row(
            fallback_kind="sanitizer_strict_social",
            fallback_content_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            repair_kind="strict_social_repair",
        ),
        drift_rows=[
            exact_value_drift_row(
                "fallback_selection_owner",
                expected=SANITIZER_FALLBACK_SELECTION_OWNER,
                actual="output_sanitizer",
                reason="short selection owner rejected",
            )
        ],
        scenario_id="sanitizer_short_owner_probe",
        turn_index=0,
    )[0]
    row["fallback_selection_owner"] = "output_sanitizer"
    row["fallback_content_owner"] = "strict_social_emission"
    errors = validate_failure_classification_row(row)
    assert "invalid fallback_selection_owner: 'output_sanitizer'" in errors
    assert "invalid fallback_content_owner: 'strict_social_emission'" in errors

    row["fallback_selection_owner"] = SANITIZER_FALLBACK_SELECTION_OWNER
    row["fallback_content_owner"] = SANITIZER_STRICT_SOCIAL_CONTENT_OWNER
    assert_failure_dashboard_row_shape(row)

    upstream_row = build_failure_dashboard_rows(
        observed_turn=observed_upstream_fast_split_owner_row(),
        drift_rows=[
            exact_value_drift_row(
                "fallback_content_owner",
                expected=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
                actual="gm_retry",
                reason="short upstream content owner rejected",
            )
        ],
        scenario_id="upstream_fast_short_owner_probe",
        turn_index=0,
    )[0]
    upstream_row["fallback_selection_owner"] = "api"
    upstream_row["fallback_content_owner"] = "gm_retry"
    upstream_errors = validate_failure_classification_row(upstream_row)
    assert "invalid fallback_selection_owner: 'api'" in upstream_errors
    assert "invalid fallback_content_owner: 'gm_retry'" in upstream_errors

    upstream_row["fallback_selection_owner"] = UPSTREAM_FAST_FALLBACK_SELECTION_OWNER
    upstream_row["fallback_content_owner"] = UPSTREAM_FAST_FALLBACK_CONTENT_OWNER
    assert_failure_dashboard_row_shape(upstream_row)


def test_failure_classification_contract_rejects_short_names_on_sealed_family_split_owner_fields() -> None:
    row = build_failure_dashboard_rows(
        observed_turn=observed_sealed_family_split_owner_row(
            fallback_kind=SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
            final_emitted_source="global_scene_fallback",
            fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        drift_rows=[
            exact_value_drift_row(
                "fallback_selection_owner",
                expected="final_emission_gate",
                actual=SEALED_FALLBACK_SELECTION_OWNER,
                reason="short selection owner rejected",
            )
        ],
        scenario_id="sealed_family_short_owner_probe",
        turn_index=0,
    )[0]
    row["fallback_selection_owner"] = "final_emission_gate"
    row["fallback_content_owner"] = "final_emission_sealed_fallback"
    errors = validate_failure_classification_row(row)
    assert "invalid fallback_selection_owner: 'final_emission_gate'" in errors
    assert "invalid fallback_content_owner: 'final_emission_sealed_fallback'" in errors

    row["fallback_selection_owner"] = SEALED_FALLBACK_SELECTION_OWNER
    row["fallback_content_owner"] = SEALED_FALLBACK_MODULE_CONTENT_OWNER
    assert_failure_dashboard_row_shape(row)


def test_failure_classification_contract_rejects_short_names_on_opening_family_split_owner_fields() -> None:
    row = build_failure_dashboard_rows(
        observed_turn=observed_opening_family_split_owner_row(
            fallback_kind="scene_opening",
            fallback_content_owner=OPENING_FALLBACK_CONTENT_OWNER,
            opening_fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        ),
        drift_rows=[
            exact_value_drift_row(
                "fallback_selection_owner",
                expected="final_emission_gate",
                actual=OPENING_FALLBACK_SELECTION_OWNER,
                reason="short selection owner rejected",
            )
        ],
        scenario_id="opening_family_short_owner_probe",
        turn_index=0,
    )[0]
    row["fallback_selection_owner"] = "final_emission_gate"
    row["fallback_content_owner"] = "opening_deterministic_fallback"
    errors = validate_failure_classification_row(row)
    assert "invalid fallback_selection_owner: 'final_emission_gate'" in errors
    assert "invalid fallback_content_owner: 'opening_deterministic_fallback'" in errors

    row["fallback_selection_owner"] = OPENING_FALLBACK_SELECTION_OWNER
    row["fallback_content_owner"] = OPENING_FALLBACK_CONTENT_OWNER
    assert_failure_dashboard_row_shape(row)


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


# --- Matrix governance report prose (BU15 acceptance matrix) --------------------


def test_cross_family_split_owner_acceptance_matrix_stays_aligned() -> None:
    """BU15: one matrix drives classifier, dashboard, lineage, and observed-row builders."""
    from game.runtime_lineage_telemetry import summarize_runtime_lineage_events
    from tests.helpers.failure_dashboard_fixtures import CONTROLLED_FAILURE_CASES

    dashboard_case_ids = {case_id for case_id, _observed, _drift, _expected in CONTROLLED_FAILURE_CASES}
    lineage_events: list[dict] = []

    for row in split_owner_acceptance_matrix_rows():
        built_event = split_owner_lineage_event_from_matrix_row(row)
        assert_split_owner_matrix_lineage_event(row, built_event)
        lineage_events.append(built_event)

        observed = split_owner_observed_row_from_matrix_row(row)
        embedded = observed["runtime_lineage_events"][0]
        assert_split_owner_matrix_lineage_event(row, embedded)

        classified = build_failure_dashboard_rows(
            observed_turn=observed,
            drift_rows=[split_owner_matrix_classifier_drift_row(row)],
            scenario_id=f"matrix_{row.matrix_id}",
            turn_index=0,
        )[0]
        assert_split_owner_matrix_classifier_row(row, classified)
        assert_failure_dashboard_row_shape(classified)

        if row.dashboard_case_id is not None:
            assert row.dashboard_case_id in dashboard_case_ids
            assert_split_owner_matrix_dashboard_expected(row, classified)

    summary = summarize_runtime_lineage_events(lineage_events)
    assert_lineage_summary_counts(summary, total_events=len(lineage_events))
    for row in split_owner_acceptance_matrix_rows():
        assert_lineage_matrix_row_aggregated(
            summary,
            event_kind=row.event_kind,
            fallback_kind=str(row.fallback_kind) if row.fallback_kind is not None else None,
            fallback_selection_owner=(
                str(row.fallback_selection_owner)
                if row.fallback_selection_owner is not None
                else None
            ),
            fallback_content_owner=(
                str(row.fallback_content_owner)
                if row.fallback_content_owner is not None
                else None
            ),
        )

    report = render_split_owner_acceptance_matrix_report()
    # Matrix report prose anchors are governance locks, not runtime behavior checks.
    assert "scene_opening" in report
    assert "referential_local_substitution" in report
    assert "Legacy matrix rows (BU17 synthetic-only)" in report
    assert "Dashboard case id aliases" not in report
    assert "sealed_or_global_replacement_legacy" in report
    assert "Dashboard probes: 15" in report
    assert "Sealed subkind dashboard parity: 6/6 non-legacy rows" in report
    assert f"Total rows: {len(split_owner_acceptance_matrix_rows())}" in report

    for row in split_owner_acceptance_matrix_rows():
        if split_owner_fem_projection_excluded(row):
            continue
        observed = project_split_owner_matrix_row(row)
        assert_split_owner_matrix_fem_projection(row, observed)
