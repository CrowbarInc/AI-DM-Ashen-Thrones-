from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_BUCKETS,
    SEALED_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
)
from tests.failure_classification_contract import (
    ALLOWED_FAILURE_CATEGORIES,
    ALLOWED_FAILURE_OWNERS,
    ALLOWED_FAILURE_SEVERITIES,
    ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS,
    ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS,
    ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS,
    MAJOR_OWNER_INVESTIGATION_TARGETS,
)
from tests.helpers.failure_classifier import CATEGORY_RULES, INVESTIGATION_TARGETS, validate_failure_classification_row
from tests.failure_classification_contract import (
    ALLOWED_CLASSIFICATION_ROW_FIELDS,
    CLASSIFIER_EVIDENCE_EXTENSION_FIELDS,
    CLASSIFIER_EVIDENCE_FIELDS,
    FAILURE_DASHBOARD_EVIDENCE_LABELS,
    FAILURE_DASHBOARD_EVIDENCE_MANIFEST,
    FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS,
    OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS,
    PROTECTED_CLASSIFIER_EVIDENCE_FIELDS,
    REQUIRED_CLASSIFICATION_FIELDS,
)
from tests.helpers.failure_classifier import FailureClassification
from tests.helpers.failure_classification_sync import (
    assert_classifier_evidence_manifest_locked,
    assert_contract_classifier_alignment,
    assert_failure_classification_row_contract_locked,
    classification_contract_summary,
    classifier_evidence_manifest_misalignments,
    contract_classifier_misalignments,
    dashboard_evidence_manifest_misalignments,
    failure_classification_row_contract_fields,
    failure_classification_row_contract_misalignments,
    failure_classification_typeddict_field_sets,
    known_failure_categories,
    known_owner_buckets,
)
from tests.helpers.failure_dashboard_report import (
    build_failure_dashboard_rows,
    render_failure_dashboard_markdown,
)
from tests.helpers.failure_dashboard_fixtures import classified_rows

# Ownership note:
# This file owns the failure-classification schema and taxonomy contract.
# Dashboard rendering assertions here validate contract enforcement, not runtime
# fallback, route, speaker, or visibility behavior.


def test_contract_classifier_alignment_is_locked():
    assert_contract_classifier_alignment()


def test_classifier_evidence_manifest_matches_optional_contract_fields():
    assert_classifier_evidence_manifest_locked()
    assert CLASSIFIER_EVIDENCE_FIELDS == OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS
    assert len(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS) == 32
    assert len(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS) == 15
    assert not (PROTECTED_CLASSIFIER_EVIDENCE_FIELDS & CLASSIFIER_EVIDENCE_EXTENSION_FIELDS)
    assert classifier_evidence_manifest_misalignments() == []


def test_ao2_protected_classifier_evidence_derived_from_observation_registry():
    from tests.helpers.golden_replay_projection import (
        protected_classifier_evidence_excluded_paths,
        protected_classifier_evidence_field_paths,
        protected_observation_field_paths,
    )

    derived = protected_classifier_evidence_field_paths()
    assert derived == PROTECTED_CLASSIFIER_EVIDENCE_FIELDS
    flat_protected = {path for path in protected_observation_field_paths() if "." not in path}
    assert derived == flat_protected - protected_classifier_evidence_excluded_paths()
    assert derived <= set(OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS)


def test_dashboard_evidence_keys_are_subset_of_classifier_evidence_fields():
    assert set(FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS) <= CLASSIFIER_EVIDENCE_FIELDS
    assert dashboard_evidence_manifest_misalignments() == []


def test_ao3_dashboard_evidence_manifest_owned_by_classifier_contract():
    from tests.helpers.failure_dashboard_report import (
        FAILURE_DASHBOARD_EVIDENCE_LABELS as dashboard_labels,
        FAILURE_DASHBOARD_EVIDENCE_MANIFEST as dashboard_manifest,
        FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS as dashboard_row_keys,
    )
    from tests.failure_classification_contract import failure_dashboard_evidence_manifest

    contract_manifest = failure_dashboard_evidence_manifest()
    assert len(FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS) == 29
    assert dashboard_manifest == contract_manifest == FAILURE_DASHBOARD_EVIDENCE_MANIFEST
    assert dashboard_row_keys == FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS
    assert dashboard_labels == FAILURE_DASHBOARD_EVIDENCE_LABELS
    assert tuple(label for label, _row_key in contract_manifest) == FAILURE_DASHBOARD_EVIDENCE_LABELS


def test_ao4_synthetic_observed_row_factory_is_single_authority():
    from tests.helpers.failure_classification_sync import observed_failure_row
    from tests.helpers.replay_observed_row_fixtures import (
        observed_dashboard_probe_row,
        synthetic_observed_replay_row,
    )

    classifier_row = observed_failure_row()
    dashboard_row = observed_dashboard_probe_row()
    assert classifier_row == synthetic_observed_replay_row(profile="classifier_probe")
    assert dashboard_row == synthetic_observed_replay_row(profile="dashboard_probe")
    assert classifier_row["scenario_id"] == "probe"
    assert classifier_row["final_text_hash"] == "hash123"
    assert "raw_signal_presence" not in classifier_row
    assert dashboard_row["scenario_id"] == "controlled_probe"
    assert dashboard_row["final_text_hash"] == "probehash"
    assert dashboard_row["raw_signal_presence"] == {}
    assert dashboard_row["normalized_signal_presence"] == {}


def test_failure_classification_row_contract_helper_matches_contract_constants():
    fields = failure_classification_row_contract_fields()
    assert fields["required"] == REQUIRED_CLASSIFICATION_FIELDS
    assert fields["optional_evidence"] == OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS
    assert fields["allowed"] == ALLOWED_CLASSIFICATION_ROW_FIELDS
    assert fields["required"] | fields["optional_evidence"] == fields["allowed"]


def test_failure_classification_typeddict_matches_row_contract():
    assert_failure_classification_row_contract_locked()
    assert failure_classification_row_contract_misalignments() == []
    typed_required, typed_optional = failure_classification_typeddict_field_sets()
    assert typed_required == REQUIRED_CLASSIFICATION_FIELDS
    assert typed_optional == OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS
    assert set(FailureClassification.__annotations__) == ALLOWED_CLASSIFICATION_ROW_FIELDS


def test_unknown_classification_field_validation_message_unchanged():
    row = _valid_sample_row()
    row["unexpected_probe_field"] = "value"
    assert validate_failure_classification_row(row) == ["unknown classification field: unexpected_probe_field"]


def test_classification_contract_summary_matches_known_taxonomy():
    summary = classification_contract_summary()
    assert summary["failure_category_count"] == len(known_failure_categories())
    buckets = known_owner_buckets()
    assert summary["opening_owner_bucket_count"] == len(buckets["opening"])
    assert summary["sealed_owner_bucket_count"] == len(buckets["sealed"])
    assert summary["visibility_owner_bucket_count"] == len(buckets["visibility"])
    assert summary["category_rule_count"] > 0


def test_sync_helper_reports_category_rule_category_drift():
    drift = contract_classifier_misalignments(
        category_rules=CATEGORY_RULES + (("bad", ("x",), "not-a-category", "interaction_context"),),
    )
    assert any("not-a-category" in item for item in drift)


def test_sync_helper_reports_investigation_target_drift():
    drift = contract_classifier_misalignments(
        investigation_targets={**INVESTIGATION_TARGETS, "route": "game/wrong.py"},
    )
    assert any("game/wrong.py" in item for item in drift)


def _valid_sample_row() -> dict[str, Any]:
    return build_failure_dashboard_rows(
        observed_turn={
            "scenario_id": "contract_sample",
            "turn_index": 0,
            "route_kind": "dialogue",
            "selected_speaker_id": "guard",
            "final_emitted_source": "generated_candidate",
            "fallback_family": None,
            "unavailable": [],
            "trace": {"canonical_entry": {"target_actor_id": "runner"}},
        },
        drift_rows=[
            {
                "field_path": "selected_speaker_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="contract_sample",
        turn_index=0,
    )[0]


def test_controlled_probe_rows_validate_against_contract():
    rows = classified_rows()
    assert rows
    for row in rows:
        assert validate_failure_classification_row(row) == []


def test_sample_classifier_row_validates_against_contract():
    assert validate_failure_classification_row(_valid_sample_row()) == []


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("category", "mystery", "invalid category"),
        ("severity", "catastrophic", "invalid severity"),
        ("primary_owner", None, "invalid primary_owner"),
        ("investigate_first", "", "investigate_first must be a non-empty string"),
    ],
)
def test_invalid_core_contract_fields_fail_validation(field, value, expected_error):
    row = _valid_sample_row()
    row[field] = value

    errors = validate_failure_classification_row(row)

    assert any(expected_error in error for error in errors)


def test_unknown_replay_tag_fails_unless_experimental():
    row = _valid_sample_row()
    row["replay_tags"] = ["structural_drift", "new_unreviewed_tag"]
    assert any("invalid replay_tag" in error for error in validate_failure_classification_row(row))

    row["replay_tags"] = ["structural_drift", "experimental:new_unreviewed_tag"]
    assert validate_failure_classification_row(row) == []


# Opening fallback owner buckets are cross-layer contract values; runtime
# selection and prose behavior remain owned by the gate and opening fallback tests.
def test_allowed_fallback_owner_buckets_match_canonical_meta_registry() -> None:
    assert ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS is OPENING_FALLBACK_OWNER_BUCKETS
    assert ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS is SEALED_FALLBACK_OWNER_BUCKETS
    assert ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS is VISIBILITY_FALLBACK_OWNER_BUCKETS


def test_opening_fallback_owner_bucket_values_are_contract_locked():
    row = _valid_sample_row()
    row["opening_fallback_owner_bucket"] = "upstream-prepared"
    assert row["opening_fallback_owner_bucket"] in ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS
    assert validate_failure_classification_row(row) == []

    row["opening_fallback_owner_bucket"] = "mystery-owner"
    assert "invalid opening_fallback_owner_bucket: 'mystery-owner'" in validate_failure_classification_row(row)


# Sealed fallback owner buckets are cross-layer contract values; helper shaping
# is owned by final_emission_sealed_fallback and gate orchestration by final_emission_gate.
def test_sealed_fallback_owner_bucket_values_are_contract_locked():
    row = _valid_sample_row()
    row["sealed_fallback_owner_bucket"] = "sealed-gate"
    assert row["sealed_fallback_owner_bucket"] in ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS
    assert validate_failure_classification_row(row) == []

    row["sealed_fallback_owner_bucket"] = "mystery-owner"
    assert "invalid sealed_fallback_owner_bucket: 'mystery-owner'" in validate_failure_classification_row(row)


def test_visibility_fallback_owner_bucket_values_are_contract_locked():
    row = _valid_sample_row()
    row["visibility_fallback_owner_bucket"] = "strict-social-visibility"
    row["visibility_replacement_applied"] = True
    row["visibility_fallback_pool"] = "strict_social_visibility_minimal"
    row["visibility_fallback_kind"] = "visibility_minimal_social_fallback"
    assert row["visibility_fallback_owner_bucket"] in ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS
    assert validate_failure_classification_row(row) == []

    row["visibility_fallback_owner_bucket"] = "mystery-owner"
    assert "invalid visibility_fallback_owner_bucket: 'mystery-owner'" in validate_failure_classification_row(row)


def test_runtime_response_type_repair_kind_taxonomy_is_contract_locked():
    assert_contract_classifier_alignment()


def test_upstream_prepared_emission_owner_and_source_family_are_contract_locked():
    row = _valid_sample_row()
    row["primary_owner"] = "upstream_prepared_emission"
    row["secondary_owner"] = "emission"
    row["source_family"] = "upstream_prepared_emission"
    row["prepared_emission_owner"] = "upstream_prepared_emission"
    row["upstream_prepared_emission_used"] = True
    row["upstream_prepared_emission_valid"] = True
    row["upstream_prepared_emission_source"] = "prepared_answer_fallback_text"
    row["upstream_prepared_emission_reject_reason"] = None

    assert validate_failure_classification_row(row) == []


def test_strict_social_from_sanitizer_owner_split_fields_are_contract_locked():
    row = _valid_sample_row()
    row["category"] = "sanitizer"
    row["primary_owner"] = "sanitizer"
    row["secondary_owner"] = "emission"
    row["source_family"] = "output_sanitizer"
    row["emission_sublayer"] = "strict_social_replacement"
    row["sanitizer_strict_social_fallback_used"] = True
    row["sanitizer_strict_social_selection_owner"] = "output_sanitizer"
    row["sanitizer_strict_social_prose_owner"] = "strict_social_emission"
    row["sanitizer_strict_social_source"] = "social_fallback_line_for_sanitizer.empty_output"
    row["prepared_emission_owner"] = None

    assert validate_failure_classification_row(row) == []

    row["sanitizer_strict_social_prose_owner"] = "output_sanitizer"
    assert "invalid sanitizer_strict_social_prose_owner: 'output_sanitizer'" in validate_failure_classification_row(row)


@pytest.mark.parametrize(
    "sublayer",
    [
        "sanitizer.empty_fallback",
        "sealed_gate",
        "final_emission.finalize_packaging",
        "final_emission.finalize_route_illegal_strip",
        "emission.post_gate_mutation_unknown",
    ],
)
def test_post_gate_mutation_reduction_sublayers_are_contract_locked(sublayer):
    row = _valid_sample_row()
    row["category"] = "emission"
    row["primary_owner"] = "emission"
    row["secondary_owner"] = "validator"
    row["source_family"] = "stage_diff"
    row["post_gate_mutation_detected"] = True
    row["emission_sublayer"] = sublayer
    row["mutation_source"] = sublayer

    assert validate_failure_classification_row(row) == []


def test_missing_primary_owner_fails_validation():
    row = _valid_sample_row()
    del row["primary_owner"]

    errors = validate_failure_classification_row(row)

    assert "missing required field: primary_owner" in errors
    assert any("invalid primary_owner" in error for error in errors)


def test_dashboard_renderer_rejects_invalid_classification_rows():
    row = _valid_sample_row()
    row["category"] = "mystery"

    with pytest.raises(ValueError, match="invalid failure dashboard row"):
        render_failure_dashboard_markdown([row])


def test_dashboard_markdown_keeps_diagnostic_headers():
    report = render_failure_dashboard_markdown(
        [_valid_sample_row()],
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest contract",
    )

    for header in (
        "Scenario",
        "Turn",
        "Category",
        "Severity",
        "Primary Owner",
        "Secondary Owner",
        "Investigate First",
        "Replay Tags",
        "Evidence",
    ):
        assert header in report


def test_owner_matrix_and_schema_docs_cover_contract_taxonomy():
    root = Path(__file__).resolve().parents[1]
    owner_doc = (root / "audits" / "failure_owner_matrix.md").read_text(encoding="utf-8")
    schema_doc = (root / "audits" / "proposed_failure_classification_schema.md").read_text(encoding="utf-8")
    thin_answer_doc = (root / "audits" / "thin_answer_fallback_surface_inventory_2026-05-12.md").read_text(encoding="utf-8")
    combined = f"{owner_doc}\n{schema_doc}\n{thin_answer_doc}"

    for owner in ALLOWED_FAILURE_OWNERS:
        if owner == "none":
            continue
        assert owner in combined

    for category in ALLOWED_FAILURE_CATEGORIES:
        assert f"`{category}`" in schema_doc or category in owner_doc

    for owner, target in MAJOR_OWNER_INVESTIGATION_TARGETS.items():
        assert owner
        assert target
