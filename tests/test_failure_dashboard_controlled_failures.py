from __future__ import annotations

import pytest

from tests.helpers.failure_classification_builders import classify_replay_probe_row
from tests.helpers.failure_classification_sync import (
    assert_classifier_routing_parity,
    assert_contract_classifier_alignment,
    assert_split_owner_matrix_dashboard_case_id_parity,
    assert_split_owner_matrix_dashboard_expected,
    assert_split_owner_matrix_lineage_event,
    classifier_evidence_field_paths,
    classification_contract_summary,
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
from tests.helpers.opening_fallback_evidence import legacy_compatibility_local_opening_authorship_source

pytestmark = pytest.mark.failure_dashboard_probe

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
# - Group B (presentation goldens): _CONTROLLED_PROBE_EVIDENCE_CELLS and report shape test.
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


_CONTROLLED_PROBE_EVIDENCE_CELLS: dict[str, str] = {
    "wrong_speaker": "none",
    "forced_fallback_source": "sublayer=terminal_fallback; mutation=terminal_fallback",
    "opening_fallback_owner_bucket": (
        "sublayer=opening_fallback; repair=opening_deterministic_fallback; "
        "opening_authorship=upstream_prepared_opening_fallback; opening_owner=upstream-prepared; "
        "mutation=opening_fallback"
    ),
    "scene_opening_split_owner": (
        "sublayer=opening_fallback; repair=opening_deterministic_fallback; "
        "opening_authorship=upstream_prepared_opening_fallback; opening_owner=upstream-prepared; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.opening_deterministic_fallback; mutation=opening_fallback"
    ),
    "opening_failed_closed_split_owner": (
        "sublayer=opening_fallback; repair=opening_deterministic_fallback_failed_closed; "
        "opening_owner=sealed-gate; fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_gate; mutation=opening_fallback"
    ),
    "opening_fallback_authorship_source": (
        "sublayer=opening_fallback; "
        f"opening_authorship={legacy_compatibility_local_opening_authorship_source()}; "
        "opening_owner=unknown-ambiguous; mutation=opening_fallback"
    ),
    "opening_fallback_basis": "sublayer=opening_fallback; opening_owner=unknown-ambiguous; mutation=opening_fallback",
    "opening_fallback_projection_missing": "opening_owner=unknown-ambiguous; missing=projection_missing_raw_present",
    "sealed_fallback_owner_bucket": "sublayer=terminal_fallback; sealed_owner=sealed-gate; mutation=terminal_fallback",
    "visibility_fallback_owner_bucket": (
        "sublayer=terminal_fallback; visibility_owner=sealed-gate; visibility_replaced=True; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
    "visibility_enforcement_split_owner": (
        "sublayer=terminal_fallback; repair=visibility_enforcement; "
        "fallback_selection_owner=game.final_emission_visibility_fallback; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "visibility_owner=sealed-gate; visibility_replaced=True; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
    "first_mention_enforcement_split_owner": (
        "sublayer=terminal_fallback; repair=first_mention_enforcement; "
        "fallback_selection_owner=game.final_emission_visibility_fallback; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "visibility_owner=sealed-gate; visibility_replaced=False; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
    "referential_clarity_enforcement_split_owner": (
        "sublayer=terminal_fallback; repair=referential_clarity_enforcement; "
        "fallback_selection_owner=game.final_emission_visibility_fallback; "
        "fallback_content_owner=game.social_exchange_emission; "
        "visibility_owner=strict-social-visibility; visibility_replaced=False; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
    "referential_local_substitution_split_owner": (
        "repair=referential_clarity_local_substitution; visibility_owner=strict-social-visibility; "
        "mutation=referential_clarity_local_substitution_mutation"
    ),
    "sanitizer_strict_social_split_owner": (
        "sublayer=strict_social_replacement; repair=strict_social_repair; "
        "fallback_selection_owner=game.output_sanitizer; fallback_content_owner=game.social_exchange_emission; "
        "mutation=strict_social_replacement; strict_social_fallback=True; "
        "strict_social_selection_owner=game.output_sanitizer; strict_social_prose_owner=game.social_exchange_emission; "
        "strict_social_source=social_fallback_line_for_sanitizer.empty_output"
    ),
    "sanitizer_empty_output_split_owner": (
        "sublayer=sanitizer; repair=sanitizer_empty_output; "
        "fallback_selection_owner=game.output_sanitizer; fallback_content_owner=game.output_sanitizer; "
        "mutation=sanitizer; sanitizer_empty=True; "
        "sanitizer_empty_source=upstream_prepared_emission.prepared_sanitizer_empty_fallback_text; "
        "sanitizer_empty_owner=game.output_sanitizer; sanitizer_lineage_mode=strip_only; sanitizer_lineage_empty=True"
    ),
    "upstream_fast_fallback_split_owner": (
        "fallback_selection_owner=game.api; fallback_content_owner=game.gm_retry"
    ),
    "sealed_global_scene_split_owner": (
        "sublayer=terminal_fallback; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=terminal_fallback"
    ),
    "sealed_social_interlocutor_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.social_exchange_emission; "
        "sealed_owner=strict-social-sealed; mutation=fallback_behavior"
    ),
    "sealed_passive_scene_pressure_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=fallback_behavior"
    ),
    "sealed_npc_pursuit_neutral_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=fallback_behavior"
    ),
    "sealed_anti_reset_continuation_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=fallback_behavior"
    ),
    "sealed_unknown_replacement_split_owner": (
        "sublayer=terminal_fallback; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_gate; "
        "sealed_owner=unknown-none; mutation=terminal_fallback"
    ),
    "sanitizer_leakage": (
        "sublayer=sanitizer; mutation=sanitizer; sanitizer_mode=strip_only; sanitizer_events=1; "
        "sanitizer_changed=0; sanitizer_lineage_mode=strip_only; sanitizer_lineage_changed=1; "
        "sanitizer_lineage_dropped=1; sanitizer_lineage_empty=False; sanitizer_lineage_legacy=False"
    ),
    "sanitizer_empty_fallback": (
        "sublayer=sanitizer; lineage=pre_gate_sanitizer>sanitizer_empty_fallback>finalize_packaging; "
        "mutation=sanitizer; sanitizer_mode=strip_only; sanitizer_empty=True; "
        "sanitizer_empty_source=upstream_prepared_emission.prepared_sanitizer_empty_fallback_text; "
        "sanitizer_empty_owner=game.output_sanitizer; sanitizer_lineage_mode=strip_only; sanitizer_lineage_changed=1; "
        "sanitizer_lineage_dropped=1; sanitizer_lineage_empty=True; sanitizer_lineage_legacy=False"
    ),
    "strict_social_sanitizer_fallback": (
        "sublayer=strict_social_replacement; mutation=strict_social_replacement; strict_social_fallback=True; "
        "strict_social_selection_owner=game.output_sanitizer; strict_social_prose_owner=game.social_exchange_emission; "
        "strict_social_source=social_fallback_line_for_sanitizer.empty_output"
    ),
    "legacy_sanitizer_rewrite_diagnostic": (
        "sublayer=sanitizer; mutation=sanitizer; sanitizer_lineage_mode=legacy_sentence_rewrite; "
        "sanitizer_lineage_changed=1; sanitizer_lineage_dropped=0; sanitizer_lineage_empty=False; "
        "sanitizer_lineage_legacy=legacy_diagnostic"
    ),
    "response_type_repair_unexpected": (
        "prepared_emission=used valid=True source=prepared_action_fallback_text; sublayer=upstream_prepared_emission; "
        "repair=action_outcome_upstream_prepared_repair; lineage=response_type_repair>prepared_emission_selection>finalize_packaging; "
        "mutation=upstream_prepared_emission"
    ),
    "prepared_emission_rejected": (
        "prepared_emission=rejected reason=missing_answer_specificity; sublayer=upstream_prepared_emission; "
        "repair=answer_upstream_prepared_repair; mutation=upstream_prepared_emission"
    ),
    "missing_route_metadata_raw_absent": "missing=runtime_missing_raw_absent",
    "missing_route_metadata_raw_present": "missing=projection_missing_raw_present",
    "semantic_mutation": "none",
    "post_gate_unknown_mutation": "sublayer=emission.post_gate_mutation_unknown; mutation=emission.post_gate_mutation_unknown",
    "post_gate_route_illegal_strip_reduced": (
        "sublayer=final_emission.finalize_route_illegal_strip; lineage=finalize_route_illegal_strip>finalize_packaging; "
        "mutation=final_emission.finalize_route_illegal_strip"
    ),
    "post_gate_sanitizer_empty_reduced": (
        "sublayer=sanitizer.empty_fallback; lineage=pre_gate_sanitizer>sanitizer_empty_fallback>finalize_packaging; "
        "mutation=sanitizer.empty_fallback"
    ),
    "post_gate_response_type_reduced": (
        "sublayer=response_type; lineage=response_type_repair>finalize_packaging; mutation=response_type"
    ),
}


@pytest.mark.parametrize("case_id", tuple(_CONTROLLED_PROBE_EVIDENCE_CELLS))
def test_controlled_probe_evidence_cells_unchanged(case_id: str):
    rows_by_id = {row["scenario_id"]: row for row in classified_rows()}
    assert _evidence_cell(rows_by_id[case_id]) == _CONTROLLED_PROBE_EVIDENCE_CELLS[case_id]


def test_controlled_failure_probe_categories_use_sync_taxonomy():
    categories = set(known_failure_categories())
    for _case_id, _observed, _drift_row, expected in CONTROLLED_FAILURE_CASES:
        assert expected["category"] in categories


def test_controlled_failure_probe_owner_buckets_use_sync_taxonomy():
    buckets = known_owner_buckets()
    for _case_id, observed, _drift_row, expected in CONTROLLED_FAILURE_CASES:
        opening_bucket = expected.get("opening_fallback_owner_bucket") or observed.get("opening_fallback_owner_bucket")
        if opening_bucket is not None:
            assert opening_bucket in buckets["opening"]
        sealed_bucket = expected.get("sealed_fallback_owner_bucket") or observed.get("sealed_fallback_owner_bucket")
        if sealed_bucket is not None:
            assert sealed_bucket in buckets["sealed"]
        visibility_bucket = expected.get("visibility_fallback_owner_bucket") or observed.get(
            "visibility_fallback_owner_bucket"
        )
        if visibility_bucket is not None:
            assert visibility_bucket in buckets["visibility"]


def test_controlled_failure_probe_field_paths_use_projection_surface():
    protected = set(protected_observation_field_paths())
    for _case_id, _observed, drift_row, _expected in CONTROLLED_FAILURE_CASES:
        field_path = str(drift_row["field_path"])
        assert field_path in protected or field_path in _CONTROLLED_PROBE_EXTENSION_FIELD_PATHS


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
    assert summary["failure_category_count"] == len(KNOWN_FAILURE_CATEGORIES)


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

    assert_classifier_routing_parity(row, classifier_row)
    for key, value in expected.items():
        assert row.get(key) == value


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

    assert "Evidence" in report
    assert "wrong_speaker" in report
    assert "speaker_mismatch" in report
    assert "forced_fallback_source" in report
    assert "fallback_source_mismatch" in report
    assert "opening_fallback_owner_bucket" in report
    assert "opening_owner=upstream-prepared" in report
    assert "scene_opening_split_owner" in report
    assert "fallback_content_owner=game.opening_deterministic_fallback" in report
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
    assert "fallback_selection_owner=game.final_emission_visibility_fallback" in report
    assert "fallback_content_owner=game.final_emission_sealed_fallback" in report
    assert "fallback_selection_owner=game.output_sanitizer" in report
    assert "fallback_content_owner=game.social_exchange_emission" in report
    assert "fallback_selection_owner=game.api" in report
    assert "fallback_content_owner=game.gm_retry" in report
    assert "sealed_global_scene_split_owner" in report
    assert "sealed_social_interlocutor_split_owner" in report
    assert "sealed_passive_scene_pressure_split_owner" in report
    assert "sealed_unknown_replacement_split_owner" in report
    assert "fallback_content_owner=game.social_exchange_emission" in report
    assert "sealed_owner=strict-social-sealed" in report
    assert "sealed_owner=unknown-none" in report
    assert "fallback_selection_owner=game.final_emission_gate" in report
    assert "fallback_content_owner=game.final_emission_sealed_fallback" in report
    assert "prepared_emission=used valid=True source=prepared_action_fallback_text" in report
    assert "lineage=response_type_repair>prepared_emission_selection>finalize_packaging" in report
    assert "prepared_emission=rejected reason=missing_answer_specificity" in report
    assert "sanitizer_empty_owner=game.output_sanitizer" in report
    assert "sanitizer_lineage_changed=1" in report
    assert "sanitizer_lineage_dropped=1" in report
    assert "sanitizer_lineage_empty=True" in report
    assert "sanitizer_lineage_legacy=legacy_diagnostic" in report
    assert "strict_social_selection_owner=game.output_sanitizer" in report
    assert "strict_social_prose_owner=game.social_exchange_emission" in report
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
