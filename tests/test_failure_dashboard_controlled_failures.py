from __future__ import annotations

import pytest

from tests.helpers.failure_classification_builders import classify_replay_probe_row
from tests.helpers.failure_classification_sync import (
    assert_classification_contract_summary,
    assert_contract_classifier_alignment,
    assert_controlled_failure_dashboard_entry,
    assert_controlled_failure_evidence_cell,
    assert_controlled_failure_probe_coverage,
    assert_controlled_failure_probe_row,
    assert_split_owner_matrix_dashboard_case_id_parity,
    assert_split_owner_matrix_dashboard_expected,
    assert_split_owner_matrix_lineage_event,
    classifier_evidence_field_paths,
    classification_contract_summary,
    CONTROLLED_FAILURE_DASHBOARD_REPORT_FRAGMENTS,
    CONTROLLED_PROBE_EVIDENCE_CELLS,
    failure_dashboard_evidence_labels,
    failure_dashboard_evidence_manifest,
    failure_dashboard_evidence_row_keys,
    dashboard_evidence_manifest_misalignments,
    known_failure_categories,
    known_owner_buckets,
    split_owner_acceptance_matrix_rows,
    SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES,
    split_owner_expected_dashboard_case_id,
    split_owner_matrix_legacy,
    split_owner_matrix_classifier_drift_row,
    split_owner_observed_row_from_matrix_row,
    split_owner_sealed_matrix_rows_requiring_dashboard_probe,
)
from tests.helpers.golden_replay_projection import (
    project_turn_observation,
    protected_observation_field_paths,
)
from tests.helpers.failure_dashboard_report import (
    FAILURE_DASHBOARD_EVIDENCE_LABELS as DASHBOARD_EVIDENCE_LABELS,
    FAILURE_DASHBOARD_EVIDENCE_MANIFEST as DASHBOARD_EVIDENCE_MANIFEST,
    FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS as DASHBOARD_EVIDENCE_ROW_KEYS,
    KNOWN_FAILURE_CATEGORIES,
    REPLAY_PROTECTED_FIELD_PATHS,
    _evidence_cell,
    build_classified_dashboard_row,
    failure_dashboard_requested,
    record_failure_dashboard_rows,
    render_failure_dashboard_markdown,
)
from tests.helpers.failure_dashboard_fixtures import (
    CONTROLLED_FAILURE_CASES,
    classified_rows,
    _observed,
)

pytestmark = pytest.mark.failure_dashboard_probe

# Group B presentation goldens live in failure_classification_dashboard_expectations
# (family-grouped as CONTROLLED_*_EVIDENCE_CELLS / CONTROLLED_*_DASHBOARD_FRAGMENTS).
# This module consumes merged tables only; literals stay authoritative, not hidden.

_CONTROLLED_PROBE_EXTENSION_FIELD_PATHS = frozenset(
    {
        "opening_fallback_authorship_source",
        "opening_final_fallback_basis",
        "fallback_content_owner",
        "post_gate_mutation_detected",
        "referential_clarity_local_substitution_applied",
        "sanitizer_strict_social_fallback_used",
    }
)

# CG-3 grouping:
# - Group A (behavior probes): parametrize cases below; routing derived from classifier.
# - Group B (presentation goldens): CONTROLLED_PROBE_EVIDENCE_CELLS and
#   CONTROLLED_FAILURE_DASHBOARD_REPORT_FRAGMENTS (imported; CO11 family-grouped).
# - Group C (compatibility): export parity and split-owner case-id alias guards.


def test_dashboard_report_module_exports_projection_and_taxonomy_surfaces():
    assert REPLAY_PROTECTED_FIELD_PATHS == protected_observation_field_paths()
    assert KNOWN_FAILURE_CATEGORIES == known_failure_categories()
    assert_contract_classifier_alignment()


def test_dashboard_evidence_row_keys_are_classifier_contract_backed():
    assert set(DASHBOARD_EVIDENCE_ROW_KEYS) <= classifier_evidence_field_paths()
    assert DASHBOARD_EVIDENCE_ROW_KEYS == failure_dashboard_evidence_row_keys()
    assert dashboard_evidence_manifest_misalignments() == []


def test_dashboard_evidence_manifest_labels_are_locked():
    assert dashboard_evidence_manifest_misalignments() == []
    assert DASHBOARD_EVIDENCE_MANIFEST == failure_dashboard_evidence_manifest()
    assert DASHBOARD_EVIDENCE_LABELS == failure_dashboard_evidence_labels()
    assert tuple(label for label, _row_key in DASHBOARD_EVIDENCE_MANIFEST) == DASHBOARD_EVIDENCE_LABELS


@pytest.mark.parametrize("case_id", tuple(CONTROLLED_PROBE_EVIDENCE_CELLS))
def test_controlled_probe_evidence_cells_unchanged(case_id: str):
    rows_by_id = {row["scenario_id"]: row for row in classified_rows()}
    assert_controlled_failure_evidence_cell(
        rows_by_id[case_id],
        CONTROLLED_PROBE_EVIDENCE_CELLS[case_id],
        render_cell=_evidence_cell,
    )


def test_controlled_failure_probe_categories_use_sync_taxonomy():
    assert_controlled_failure_probe_coverage(
        CONTROLLED_FAILURE_CASES,
        categories=known_failure_categories(),
    )


def test_controlled_failure_probe_owner_buckets_use_sync_taxonomy():
    assert_controlled_failure_probe_coverage(
        CONTROLLED_FAILURE_CASES,
        owner_buckets=known_owner_buckets(),
    )


def test_controlled_failure_probe_field_paths_use_projection_surface():
    assert_controlled_failure_probe_coverage(
        CONTROLLED_FAILURE_CASES,
        protected_field_paths=protected_observation_field_paths(),
        extension_field_paths=_CONTROLLED_PROBE_EXTENSION_FIELD_PATHS,
    )


def test_controlled_wrong_speaker_projection_matches_hand_observed_shape():
    observed = _observed(selected_speaker_id="guard")
    projected = project_turn_observation(
        {
            "scenario_id": "controlled_probe",
            "snap": {
                "turn_index": observed["turn_index"],
                "gm_text": observed["final_text"],
            },
            "payload": {
                "resolution": {"kind": observed["route_kind"], "social": {"npc_id": "guard"}},
                "gm_output": {
                    "_final_emission_meta": {
                        "final_emitted_source": observed["final_emitted_source"],
                        "response_type_required": observed["response_type_required"],
                    }
                },
            },
        }
    )
    for key in ("route_kind", "selected_speaker_id", "final_emitted_source", "final_text"):
        assert projected.get(key) == observed.get(key)


def test_controlled_failure_dashboard_summary_matches_sync_helpers():
    summary = classification_contract_summary()
    assert_classification_contract_summary(
        summary,
        categories=KNOWN_FAILURE_CATEGORIES,
    )


@pytest.mark.parametrize(("case_id", "observed", "drift_row", "expected"), CONTROLLED_FAILURE_CASES)
def test_controlled_failure_probe_classifies_known_bad_case(case_id, observed, drift_row, expected):
    case_observed = {**observed, "scenario_id": case_id}
    row = build_classified_dashboard_row(
        observed_turn=case_observed,
        drift_row=drift_row,
        scenario_id=case_id,
        turn_index=0,
    )
    classifier_row = classify_replay_probe_row(
        scenario_id=case_id,
        turn_index=0,
        observed_turn=case_observed,
        drift_row=drift_row,
    )

    assert_controlled_failure_probe_row(row, classifier_row, expected)


def test_controlled_failure_probe_dashboard_contains_triage_columns():
    rows = classified_rows()
    if failure_dashboard_requested():
        record_failure_dashboard_rows(rows)

    report = render_failure_dashboard_markdown(
        rows,
        title="Failure Dashboard Probe Sample",
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest -m failure_dashboard_probe -q",
    )

    assert_controlled_failure_dashboard_entry(report, *CONTROLLED_FAILURE_DASHBOARD_REPORT_FRAGMENTS)


def test_split_owner_matrix_dashboard_case_id_parity_guard() -> None:
    """BU18/BU19: dashboard probe ids must equal {matrix_id}_split_owner with no aliases."""
    assert SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES == {}
    assert_split_owner_matrix_dashboard_case_id_parity()


def test_sealed_subkind_matrix_rows_have_dashboard_parity_except_legacy() -> None:
    """BU17/BU18: every non-legacy sealed matrix row must have a matrix-wired dashboard probe."""
    assert_split_owner_matrix_dashboard_case_id_parity()
    for row in split_owner_sealed_matrix_rows_requiring_dashboard_probe():
        assert row.dashboard_case_id is not None, row.matrix_id
        assert row.dashboard_case_id == split_owner_expected_dashboard_case_id(row)

    legacy_rows = [row for row in split_owner_acceptance_matrix_rows() if split_owner_matrix_legacy(row)]
    assert [row.matrix_id for row in legacy_rows] == ["sealed_or_global_replacement_legacy"]
    for row in legacy_rows:
        assert row.dashboard_case_id is None


def test_split_owner_acceptance_matrix_controlled_probe_owners_match_canonical_literals() -> None:
    """BU15: dashboard controlled split-owner probes stay aligned with the canonical matrix."""
    dashboard_case_ids = {case_id for case_id, _observed, _drift, _expected in CONTROLLED_FAILURE_CASES}
    matrix_dashboard_ids = {
        row.dashboard_case_id
        for row in split_owner_acceptance_matrix_rows()
        if row.dashboard_case_id is not None
    }
    assert matrix_dashboard_ids <= dashboard_case_ids

    for row in split_owner_acceptance_matrix_rows():
        if row.dashboard_case_id is None:
            continue
        observed = split_owner_observed_row_from_matrix_row(row, profile="dashboard_probe")
        classified = build_classified_dashboard_row(
            observed_turn={**observed, "scenario_id": row.dashboard_case_id},
            drift_row=split_owner_matrix_classifier_drift_row(row),
            scenario_id=row.dashboard_case_id,
            turn_index=0,
        )
        assert_split_owner_matrix_dashboard_expected(row, classified)
        embedded = observed["runtime_lineage_events"][0]
        assert_split_owner_matrix_lineage_event(row, embedded)
