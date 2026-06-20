"""BS1 canonical replacement attribution inventory tests."""
from __future__ import annotations

from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_classification_sync import (
    exact_value_drift_row,
    observed_opening_fallback_row,
    observed_visibility_replacement_row,
    response_type_repair_drift_row,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_SUCCESS_REPAIR_KIND,
    successful_opening_fem_meta,
)
from tests.helpers.replacement_attribution_inventory import (
    ATTRIBUTION_ORIGIN_DIRECT,
    ATTRIBUTION_ORIGIN_PROJECTED,
    REPLACEMENT_PATH_OPENING_FALLBACK,
    REPLACEMENT_PATH_RESPONSE_TYPE,
    REPLACEMENT_PATH_VISIBILITY,
    REQUIRED_ATTRIBUTION_FIELDS,
    attribution_record_from_failure_classification,
    attribution_record_from_fem,
    attribution_record_from_lineage_event,
    attribution_record_from_replay_projection,
    build_baseline_attribution_corpus,
    build_replacement_path_attribution_report,
    calculate_attribution_completeness,
    detect_replacement_path_from_fem,
    render_baseline_attribution_report_md,
    write_baseline_attribution_report,
    write_bs5_projection_convergence_report,
)


def test_visibility_fem_inventory_construction():
    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "visibility_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "visibility_fallback_pool": "global_scene_narrative",
        "visibility_fallback_kind": "narrative_safe_fallback",
    }
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert record["replacement_path"] == REPLACEMENT_PATH_VISIBILITY
    assert record["owner_bucket"] == "sealed-gate"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_DIRECT
    assert record["source_family"] == "final_emission_gate"
    assert record["attribution_origin"]["source_family"] == ATTRIBUTION_ORIGIN_PROJECTED
    assert "repair_kind" in record["missing_fields"]


def test_opening_lineage_inventory_has_direct_recurrence_key():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = successful_opening_fem_meta(
        final_route="replaced",
        response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
    )
    events = build_fem_runtime_lineage_events(fem)
    fallback_events = [event for event in events if event.get("event_kind") == "fallback_selected"]
    assert fallback_events
    record = attribution_record_from_lineage_event(fallback_events[0])
    assert record is not None
    assert record["replacement_path"] == REPLACEMENT_PATH_OPENING_FALLBACK
    assert record["recurrence_key"]
    assert record["attribution_origin"]["recurrence_key"] == ATTRIBUTION_ORIGIN_DIRECT
    assert record["owner_bucket"] == "upstream-prepared"


def test_replay_projection_inventory_uses_observed_owner_bucket():
    observed = observed_visibility_replacement_row()
    record = attribution_record_from_replay_projection(observed)
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_DIRECT


def test_failure_classification_inventory_has_direct_source_family():
    observed = observed_opening_fallback_row(owner_bucket=True)
    drift_row = exact_value_drift_row(
        "opening_fallback_owner_bucket",
        expected="unknown-ambiguous",
        actual="upstream-prepared",
    )
    classification = classify_replay_failure(
        scenario_id="inventory_probe",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[drift_row],
    )[0]
    record = attribution_record_from_failure_classification(classification)
    assert record is not None
    assert record["source_family"] == "opening_fallback"
    assert record["attribution_origin"]["source_family"] == ATTRIBUTION_ORIGIN_DIRECT


def test_strict_scoring_counts_only_direct_fields():
    direct_record = {
        "owner_bucket": "sealed-gate",
        "source_family": "final_emission_gate",
        "repair_kind": "opening_deterministic_fallback",
        "recurrence_key": "fallback_selected:gate:game.final_emission_gate:scene_opening",
        "mutation_classification": "fallback_mutation",
        "attribution_origin": {field: ATTRIBUTION_ORIGIN_DIRECT for field in REQUIRED_ATTRIBUTION_FIELDS},
        "replacement_path": REPLACEMENT_PATH_OPENING_FALLBACK,
        "inferred_fields": [],
        "missing_fields": [],
    }
    projected_record = dict(direct_record)
    projected_record["attribution_origin"] = {
        "owner_bucket": ATTRIBUTION_ORIGIN_PROJECTED,
        "source_family": ATTRIBUTION_ORIGIN_PROJECTED,
        "repair_kind": ATTRIBUTION_ORIGIN_DIRECT,
        "recurrence_key": ATTRIBUTION_ORIGIN_PROJECTED,
        "mutation_classification": ATTRIBUTION_ORIGIN_PROJECTED,
    }
    metrics = calculate_attribution_completeness([direct_record, projected_record])
    assert metrics["strict_complete_records"] == 1
    assert metrics["resolved_complete_records"] == 2
    assert metrics["strict_completeness_pct"] == 50.0
    assert metrics["resolved_completeness_pct"] == 100.0


def test_missing_field_detection():
    fem = {
        "first_mention_replacement_applied": True,
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
    }
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert "owner_bucket" in record["missing_fields"]
    assert "repair_kind" in record["missing_fields"]
    assert record["source_family"] == "final_emission_gate"


def test_path_report_breakdown():
    records = build_baseline_attribution_corpus()
    report = build_replacement_path_attribution_report(records)
    assert set(report) == {
        "visibility replacement",
        "first mention replacement",
        "referential replacement",
        "sealed replacement",
        "response type replacement",
        "sanitizer replacement",
        "repair mutation",
        "opening fallback",
        "strict social replacement",
    }
    visibility_stats = report[REPLACEMENT_PATH_VISIBILITY]
    assert visibility_stats["total"] >= 1
    visibility_records = [
        record
        for record in records
        if record.get("replacement_path") == REPLACEMENT_PATH_VISIBILITY
        and record.get("source_kind") == "fem_metadata"
    ]
    assert visibility_records
    assert "owner_bucket" not in visibility_records[0]["missing_fields"]


def test_baseline_corpus_is_deterministic():
    first = build_baseline_attribution_corpus()
    second = build_baseline_attribution_corpus()
    assert len(first) == len(second)
    for left, right in zip(first, second):
        assert left["replacement_path"] == right["replacement_path"]
        assert left["missing_fields"] == right["missing_fields"]
        assert left.get("recurrence_key") == right.get("recurrence_key")


def test_response_type_fem_path_detection():
    fem = {
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
        "final_route": "accept_candidate",
    }
    assert detect_replacement_path_from_fem(fem) == REPLACEMENT_PATH_RESPONSE_TYPE
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert record["repair_kind"] == "answer_upstream_prepared_repair"


def test_speaker_repair_lineage_record():
    event = make_runtime_lineage_event(
        event_kind="speaker_repair",
        stage="gate",
        owner="game.speaker_contract_enforcement",
        repair_kind="canonical_rewrite",
    )
    record = attribution_record_from_lineage_event(event, replacement_path="repair mutation")
    assert record is not None
    assert record["repair_kind"] == "canonical_rewrite"
    assert record["attribution_origin"]["repair_kind"] == ATTRIBUTION_ORIGIN_DIRECT


def test_baseline_report_generation(tmp_path):
    output = tmp_path / "bs_attribution_baseline_report.md"
    completeness, path_report, markdown = write_baseline_attribution_report(output)
    assert output.exists()
    assert completeness["total_records"] > 0
    assert "Strict completeness" in markdown
    assert "Per-Path Completeness" in markdown
    rendered = render_baseline_attribution_report_md(
        completeness=completeness,
        path_report=path_report,
        records=build_baseline_attribution_corpus(),
    )
    assert rendered == markdown


def test_classifier_response_type_row_inventory():
    observed = {
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
    }
    classification = classify_replay_failure(
        scenario_id="inventory_probe",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[response_type_repair_drift_row()],
    )[0]
    record = attribution_record_from_failure_classification(
        classification,
        replacement_path=REPLACEMENT_PATH_RESPONSE_TYPE,
    )
    assert record is not None
    assert record["source_family"] == "upstream_prepared_emission"
    assert record["repair_kind"] == "answer_upstream_prepared_repair"


def test_bs5_visibility_lineage_preserves_owner_bucket_and_mutation_class():
    from game.final_emission_replay_projection import (
        VISIBILITY_HARD_REPLACEMENT,
        build_fem_runtime_lineage_events,
    )

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "visibility_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "visibility_fallback_pool": "global_scene_narrative",
        "visibility_fallback_kind": "narrative_safe_fallback",
    }
    fallback = next(
        event for event in build_fem_runtime_lineage_events(fem) if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == VISIBILITY_HARD_REPLACEMENT
    assert fallback["fallback_owner_bucket"] == "sealed-gate"

    record = attribution_record_from_lineage_event(fallback, replacement_path=REPLACEMENT_PATH_VISIBILITY)
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["mutation_classification"] == "visibility_replacement_mutation"
    assert record["source_family"] == "final_emission_gate"
    assert "owner_bucket" not in record["missing_fields"]
    assert "mutation_classification" not in record["missing_fields"]


def test_bs5_first_mention_and_referential_fallback_kinds_are_distinct():
    from game.final_emission_replay_projection import (
        FIRST_MENTION_HARD_REPLACEMENT,
        REFERENTIAL_CLARITY_HARD_REPLACEMENT,
        build_fem_runtime_lineage_events,
    )

    first_mention = build_fem_runtime_lineage_events(
        {
            "final_route": "replaced",
            "first_mention_replacement_applied": True,
            "final_emitted_source": "global_scene_fallback",
        }
    )
    referential = build_fem_runtime_lineage_events(
        {
            "final_route": "replaced",
            "referential_clarity_replacement_applied": True,
            "final_emitted_source": "global_scene_fallback",
        }
    )
    assert _fallback_kind(first_mention) == FIRST_MENTION_HARD_REPLACEMENT
    assert _fallback_kind(referential) == REFERENTIAL_CLARITY_HARD_REPLACEMENT
    assert _fallback_kind(first_mention) != _fallback_kind(referential)


def _fallback_kind(events: list[dict]) -> str:
    return next(event["fallback_kind"] for event in events if event.get("event_kind") == "fallback_selected")


def test_bs5_repair_mutation_uses_specific_classification():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    events = build_fem_runtime_lineage_events(
        {"final_route": "accept_candidate", "fallback_behavior_repaired": True}
    )
    mutation = next(event for event in events if event.get("event_kind") == "mutation")
    assert mutation["mutation_kind"] == "fallback_behavior_repair_mutation"

    record = attribution_record_from_lineage_event(mutation, replacement_path="repair mutation")
    assert record is not None
    assert record["mutation_classification"] == "fallback_behavior_repair_mutation"
    assert "mutation_classification" not in record["missing_fields"]


def test_bs5_opening_recurrence_identity_unchanged():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = successful_opening_fem_meta(
        final_route="replaced",
        response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
    )
    events = build_fem_runtime_lineage_events(fem)
    fallback = next(event for event in events if event.get("event_kind") == "fallback_selected")
    assert fallback["fallback_kind"] == "scene_opening"
    assert fallback["recurrence_key"] == "fallback_selected:gate:game.final_emission_gate:scene_opening"


def test_bs5_projection_convergence_improves_completeness():
    from tests.helpers.replacement_attribution_inventory import BS1_BASELINE_COMPLETENESS

    _, after, _ = write_bs5_projection_convergence_report()
    assert after["resolved_completeness_pct"] > BS1_BASELINE_COMPLETENESS["resolved_completeness_pct"]
    assert after["resolved_complete_records"] > BS1_BASELINE_COMPLETENESS["resolved_complete_records"]


def test_bs4_visibility_producer_repair_kind_emitted():
    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "visibility_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "visibility_enforcement",
    }
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert record["repair_kind"] == "visibility_enforcement"
    assert record["attribution_origin"]["repair_kind"] == ATTRIBUTION_ORIGIN_DIRECT
    assert "repair_kind" not in record["missing_fields"]


def test_bs4_first_mention_producer_owner_bucket_emitted():
    fem = {
        "final_route": "replaced",
        "first_mention_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "first_mention_enforcement",
    }
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_DIRECT


def test_bs4_projection_preserves_producer_repair_kind():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "visibility_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "visibility_enforcement",
    }
    events = build_fem_runtime_lineage_events(fem)
    fallback = next(event for event in events if event.get("event_kind") == "fallback_selected")
    assert fallback["repair_kind"] == "visibility_enforcement"
    assert fallback["recurrence_key"] == "fallback_selected:gate:game.final_emission_gate:visibility_hard_replacement"


def test_bs4_opening_owner_bucket_direct_stamp():
    fem = successful_opening_fem_meta(
        final_route="replaced",
        response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
        opening_fallback_owner_bucket="upstream-prepared",
    )
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert record["owner_bucket"] == "upstream-prepared"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_DIRECT


def test_bs4_producer_stamp_report_improves_completeness():
    from tests.helpers.replacement_attribution_inventory import (
        BS1_BASELINE_COMPLETENESS,
        BS5_BASELINE_COMPLETENESS,
        write_bs4_producer_stamp_report,
    )

    bs4, _ = write_bs4_producer_stamp_report()
    assert bs4["resolved_completeness_pct"] > BS1_BASELINE_COMPLETENESS["resolved_completeness_pct"]
    assert bs4["resolved_completeness_pct"] >= BS5_BASELINE_COMPLETENESS["resolved_completeness_pct"]
    assert bs4["strict_completeness_pct"] >= BS1_BASELINE_COMPLETENESS["strict_completeness_pct"]
