from __future__ import annotations

import pytest

from tests.failure_classification_contract import (
    CLASSIFIER_EVIDENCE_FIELDS,
    FAILURE_DASHBOARD_EVIDENCE_LABELS,
    FAILURE_DASHBOARD_EVIDENCE_MANIFEST,
    FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS,
)
from tests.helpers.failure_classification_sync import (
    assert_contract_classifier_alignment,
    classification_contract_summary,
    dashboard_evidence_manifest_misalignments,
    known_failure_categories,
    known_owner_buckets,
)
from tests.helpers.failure_dashboard_report import (
    FAILURE_DASHBOARD_EVIDENCE_LABELS,
    FAILURE_DASHBOARD_EVIDENCE_MANIFEST,
    FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS,
    KNOWN_FAILURE_CATEGORIES,
    REPLAY_PROTECTED_FIELD_PATHS,
    _evidence_cell,
    build_failure_dashboard_rows,
    failure_dashboard_requested,
    record_failure_dashboard_rows,
    render_failure_dashboard_markdown,
)
from tests.helpers.failure_dashboard_fixtures import (
    CONTROLLED_FAILURE_CASES,
    classified_rows,
    _observed,
)
from tests.helpers.golden_replay_projection import project_turn_observation, protected_field_paths

pytestmark = pytest.mark.failure_dashboard_probe

_CONTROLLED_PROBE_EXTENSION_FIELD_PATHS = frozenset(
    {
        "opening_fallback_authorship_source",
        "opening_final_fallback_basis",
        "fallback_content_owner",
        "post_gate_mutation_detected",
        "sanitizer_strict_social_fallback_used",
    }
)

# Ownership note:
# Controlled probes own dashboard/classifier behavior on known-bad replay-shaped
# rows. They intentionally duplicate projection fields to preserve triage
# locality; runtime prose and routing behavior stay with their direct owners.
# Cycle F.I: controlled opening-fallback rows preserve taxonomy while allowing
# symptom-specific ``investigate_first`` routing for classifier-owned triage.



def test_dashboard_report_module_exports_projection_and_taxonomy_surfaces():
    assert REPLAY_PROTECTED_FIELD_PATHS == protected_field_paths()
    assert KNOWN_FAILURE_CATEGORIES == known_failure_categories()
    assert_contract_classifier_alignment()


def test_dashboard_evidence_row_keys_are_classifier_contract_backed():
    assert set(FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS) <= CLASSIFIER_EVIDENCE_FIELDS
    assert dashboard_evidence_manifest_misalignments() == []


def test_dashboard_evidence_manifest_labels_are_locked():
    assert dashboard_evidence_manifest_misalignments() == []
    assert tuple(label for label, _row_key in FAILURE_DASHBOARD_EVIDENCE_MANIFEST) == FAILURE_DASHBOARD_EVIDENCE_LABELS


_CONTROLLED_PROBE_EVIDENCE_CELLS: dict[str, str] = {
    "wrong_speaker": "none",
    "forced_fallback_source": "sublayer=terminal_fallback; mutation=terminal_fallback",
    "opening_fallback_owner_bucket": (
        "sublayer=opening_fallback; repair=opening_deterministic_fallback; "
        "opening_authorship=upstream_prepared_opening_fallback; opening_owner=upstream-prepared; "
        "mutation=opening_fallback"
    ),
    "opening_fallback_authorship_source": (
        "sublayer=opening_fallback; opening_authorship=compatibility_local_opening_deterministic; "
        "opening_owner=unknown-ambiguous; mutation=opening_fallback"
    ),
    "opening_fallback_basis": "sublayer=opening_fallback; opening_owner=unknown-ambiguous; mutation=opening_fallback",
    "opening_fallback_projection_missing": "opening_owner=unknown-ambiguous; missing=projection_missing_raw_present",
    "sealed_fallback_owner_bucket": "sublayer=terminal_fallback; sealed_owner=sealed-gate; mutation=terminal_fallback",
    "visibility_fallback_owner_bucket": (
        "sublayer=terminal_fallback; visibility_owner=sealed-gate; visibility_replaced=True; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
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
        "sanitizer_empty_owner=output_sanitizer; sanitizer_lineage_mode=strip_only; sanitizer_lineage_changed=1; "
        "sanitizer_lineage_dropped=1; sanitizer_lineage_empty=True; sanitizer_lineage_legacy=False"
    ),
    "strict_social_sanitizer_fallback": (
        "sublayer=strict_social_replacement; mutation=strict_social_replacement; strict_social_fallback=True; "
        "strict_social_selection_owner=output_sanitizer; strict_social_prose_owner=strict_social_emission; "
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
    protected = set(protected_field_paths())
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
    row = build_failure_dashboard_rows(
        observed_turn={**observed, "scenario_id": case_id},
        drift_rows=[drift_row],
        scenario_id=case_id,
        turn_index=0,
    )[0]

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
