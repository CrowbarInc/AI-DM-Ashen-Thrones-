"""BS3 canonical attribution contract tests."""
from __future__ import annotations

from tests.helpers.attribution_contract import (
    ALLOWED_ATTRIBUTION_ORIGINS,
    ALLOWED_MUTATION_CLASSIFICATIONS,
    ALLOWED_OWNER_BUCKETS,
    ALLOWED_REPAIR_KINDS,
    ALLOWED_SOURCE_FAMILY_TAGS,
    DEPRECATED_FALLBACK_KIND_ALIASES,
    DEPRECATED_REPAIR_KINDS,
    REPAIR_KIND_ALIASES,
    REPLACEMENT_PATHS,
    REQUIRED_ATTRIBUTION_FIELDS,
    calculate_attribution_maturity_scores,
    normalize_fallback_kind,
    normalize_repair_kind,
    validate_mutation_classification,
    validate_owner_bucket,
    validate_recurrence_key,
    validate_repair_kind,
    validate_replacement_path,
    validate_source_family,
    write_bs3_contract_compliance_report,
)
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.replacement_attribution_inventory import (
    BS1_BASELINE_COMPLETENESS,
    attribution_record_from_fem,
    baseline_attribution_classifier_inputs,
    build_baseline_attribution_corpus,
)


def test_every_owner_bucket_value_validates():
    for bucket in sorted(ALLOWED_OWNER_BUCKETS):
        assert validate_owner_bucket(bucket).valid is True


def test_invalid_owner_bucket_fails_validation():
    result = validate_owner_bucket("not-a-real-bucket")
    assert result.valid is False
    assert result.reason == "not_in_allowed_owner_buckets"


def test_every_repair_kind_value_validates():
    for kind in sorted(ALLOWED_REPAIR_KINDS):
        assert validate_repair_kind(kind).valid is True


def test_invalid_repair_kind_fails_validation():
    assert validate_repair_kind("visibility_hard_replace").valid is False
    assert validate_repair_kind("canonical_rewrite").valid is False


def test_repair_kind_normalization_is_deterministic():
    alias_source = next(iter(REPAIR_KIND_ALIASES))
    alias_target = REPAIR_KIND_ALIASES[alias_source]
    assert normalize_repair_kind(alias_source) == alias_target
    assert normalize_repair_kind(alias_source) == normalize_repair_kind(alias_source)


def test_fallback_kind_normalization_maps_deprecated_alias():
    for legacy, modern in DEPRECATED_FALLBACK_KIND_ALIASES.items():
        assert normalize_fallback_kind(legacy) == modern


def test_every_source_family_value_validates():
    for tag in sorted(ALLOWED_SOURCE_FAMILY_TAGS):
        assert validate_source_family(tag).valid is True


def test_every_mutation_classification_value_validates():
    for kind in sorted(ALLOWED_MUTATION_CLASSIFICATIONS):
        assert validate_mutation_classification(kind).valid is True


def test_recurrence_key_shape_validation():
    assert validate_recurrence_key("fallback_selected:gate:game.final_emission_gate:scene_opening").valid is True
    assert validate_recurrence_key("bad").valid is False


def test_replacement_paths_and_origins_are_locked():
    assert len(REPLACEMENT_PATHS) == 9
    assert ALLOWED_ATTRIBUTION_ORIGINS == frozenset({"direct", "projected", "classifier_inferred"})


def test_projection_lineage_output_conforms_to_contract():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "visibility_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "visibility_enforcement",
    }
    events = build_fem_runtime_lineage_events(fem)
    for event in events:
        if event.get("repair_kind"):
            assert validate_repair_kind(event["repair_kind"]).valid
        if event.get("recurrence_key"):
            assert validate_recurrence_key(event["recurrence_key"]).valid
        if event.get("mutation_kind"):
            assert validate_mutation_classification(event["mutation_kind"]).valid
        if event.get("fallback_owner_bucket"):
            assert validate_owner_bucket(event["fallback_owner_bucket"]).valid


def test_classifier_output_conforms_to_contract():
    observed, drift = baseline_attribution_classifier_inputs()[0]
    rows = classify_replay_failure(
        scenario_id="bs3_contract_test",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[drift],
    )
    assert rows
    row = rows[0]
    assert validate_source_family(row.get("source_family")).valid
    if row.get("repair_kind"):
        assert validate_repair_kind(row.get("repair_kind")).valid


def test_inventory_records_use_required_fields():
    for record in build_baseline_attribution_corpus():
        assert record["replacement_path"] in REPLACEMENT_PATHS
        assert set(record.keys()) >= set(REQUIRED_ATTRIBUTION_FIELDS)


def test_fem_inventory_repair_kind_conforms_after_normalization():
    record = attribution_record_from_fem(
        {
            "visibility_replacement_applied": True,
            "producer_repair_kind": "visibility_enforcement",
            "visibility_fallback_owner_bucket": "sealed-gate",
        }
    )
    assert record is not None
    assert validate_repair_kind(record.get("repair_kind")).valid


def test_deprecated_repair_kinds_remain_valid_legacy_tokens():
    for kind in DEPRECATED_REPAIR_KINDS:
        assert validate_repair_kind(kind).valid is True


def test_bs3_maturity_improves_over_bs1_baseline():
    maturity = calculate_attribution_maturity_scores()
    assert maturity["coverage_score_pct"] >= BS1_BASELINE_COMPLETENESS["resolved_completeness_pct"]
    assert maturity["taxonomy_consistency_score_pct"] == 100.0


def test_bs3_contract_compliance_report_generation():
    _audit, maturity, markdown = write_bs3_contract_compliance_report()
    assert "BS3 Contract Compliance Report" in markdown
    assert maturity["contract_compliance_score_pct"] > 0
