"""BS1 canonical replacement attribution inventory tests."""
from __future__ import annotations

from game.attribution_read_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_classification_sync import (
    assert_split_owner_matrix_lineage_event,
    project_split_owner_matrix_row,
    split_owner_acceptance_matrix_rows,
    split_owner_fem_meta_from_matrix_row,
    split_owner_fem_projection_excluded,
    split_owner_lineage_event_from_matrix_row,
    split_owner_observed_row_from_matrix_row,
    exact_value_drift_row,
    observed_opening_fallback_row,
    observed_visibility_replacement_row,
    response_type_repair_drift_row,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_SUCCESS_REPAIR_KIND,
    fail_closed_opening_fem_meta,
    successful_opening_fem_meta,
)
from tests.helpers.replacement_attribution_inventory import (
    ATTRIBUTION_ORIGIN_DIRECT,
    ATTRIBUTION_ORIGIN_PROJECTED,
    REPLACEMENT_PATH_FIRST_MENTION,
    REPLACEMENT_PATH_OPENING_FALLBACK,
    REPLACEMENT_PATH_REPAIR_MUTATION,
    REPLACEMENT_PATH_RESPONSE_TYPE,
    REPLACEMENT_PATH_REFERENTIAL,
    REPLACEMENT_PATH_SANITIZER,
    REPLACEMENT_PATH_SEALED,
    REPLACEMENT_PATH_STRICT_SOCIAL,
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


def test_opening_lineage_inventory_preserves_split_owner_trifecta_from_fem_builder():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    cases = (
        (
            successful_opening_fem_meta(
                final_route="replaced",
                response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
            ),
            "scene_opening",
            OPENING_FALLBACK_CONTENT_OWNER,
        ),
        (
            fail_closed_opening_fem_meta(
                opening_recovered_via_fallback=True,
                fallback_family_used="scene_opening",
            ),
            "opening_failed_closed",
            OPENING_FAIL_CLOSED_CONTENT_OWNER,
        ),
    )
    for fem, expected_kind, expected_content_owner in cases:
        events = build_fem_runtime_lineage_events(fem)
        fallback = next(event for event in events if event.get("event_kind") == "fallback_selected")
        assert fallback["fallback_kind"] == expected_kind
        assert fallback["fallback_selection_owner"] == OPENING_FALLBACK_SELECTION_OWNER
        assert fallback["fallback_content_owner"] == expected_content_owner


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


def test_bu10_first_mention_lineage_preserves_split_owner_trifecta():
    from game.attribution_read_views import (
        SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        VISIBILITY_FALLBACK_SELECTION_OWNER,
    )
    from game.final_emission_replay_projection import (
        FIRST_MENTION_HARD_REPLACEMENT,
        build_fem_runtime_lineage_events,
    )

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "first_mention_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "first_mention_enforcement",
    }
    fallback = next(
        event for event in build_fem_runtime_lineage_events(fem) if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == FIRST_MENTION_HARD_REPLACEMENT
    assert fallback["fallback_owner_bucket"] == "sealed-gate"
    assert fallback["fallback_selection_owner"] == VISIBILITY_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == SEALED_FALLBACK_MODULE_CONTENT_OWNER
    assert fallback["repair_kind"] == "first_mention_enforcement"

    record = attribution_record_from_lineage_event(fallback, replacement_path=REPLACEMENT_PATH_FIRST_MENTION)
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["repair_kind"] == "first_mention_enforcement"
    assert record["mutation_classification"] == "first_mention_replacement_mutation"
    assert "owner_bucket" not in record["missing_fields"]
    assert "repair_kind" not in record["missing_fields"]


def test_bu10_referential_lineage_preserves_split_owner_trifecta():
    from game.attribution_read_views import (
        SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        VISIBILITY_FALLBACK_SELECTION_OWNER,
    )
    from game.final_emission_replay_projection import (
        REFERENTIAL_CLARITY_HARD_REPLACEMENT,
        build_fem_runtime_lineage_events,
    )

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "referential_clarity_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "referential_clarity_enforcement",
    }
    fallback = next(
        event for event in build_fem_runtime_lineage_events(fem) if event.get("event_kind") == "fallback_selected"
    )
    assert fallback["fallback_kind"] == REFERENTIAL_CLARITY_HARD_REPLACEMENT
    assert fallback["fallback_owner_bucket"] == "sealed-gate"
    assert fallback["fallback_selection_owner"] == VISIBILITY_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == SEALED_FALLBACK_MODULE_CONTENT_OWNER
    assert fallback["repair_kind"] == "referential_clarity_enforcement"

    record = attribution_record_from_lineage_event(fallback, replacement_path=REPLACEMENT_PATH_REFERENTIAL)
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["repair_kind"] == "referential_clarity_enforcement"
    assert record["mutation_classification"] == "referential_clarity_replacement_mutation"
    assert "owner_bucket" not in record["missing_fields"]
    assert "repair_kind" not in record["missing_fields"]


def test_bu10_referential_local_substitution_fem_preserves_owner_bucket_and_repair_kind():
    fem = {
        "final_route": "accept_candidate",
        "referential_clarity_local_substitution_applied": True,
        "visibility_fallback_owner_bucket": "strict-social-visibility",
        "producer_repair_kind": "referential_clarity_local_substitution",
    }
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert record["owner_bucket"] == "strict-social-visibility"
    assert record["repair_kind"] == "referential_clarity_local_substitution"
    assert "owner_bucket" not in record["missing_fields"]
    assert "repair_kind" not in record["missing_fields"]


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


def test_bs4_passive_scene_concrete_beat_attribution_is_resolved_complete():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "accept_candidate",
        "passive_scene_concrete_beat_satisfier_applied": True,
        "passive_scene_pressure_fallback_avoided": True,
        "passive_scene_concrete_beat_type": "guard_reaction",
        "producer_repair_kind": "passive_scene_concrete_beat",
        "final_emission_mutation_lineage": ["passive_scene_concrete_beat"],
    }
    record = attribution_record_from_fem(fem, replacement_path=REPLACEMENT_PATH_REPAIR_MUTATION)
    assert record is not None
    assert record["repair_kind"] == "passive_scene_concrete_beat"
    assert record["owner_bucket"] == "sealed-gate"
    assert record["mutation_classification"] == "final_emission_mutation"
    assert record["recurrence_key"] == (
        "mutation:gate:game.final_emission_gate:passive_scene_concrete_beat"
    )
    assert record["missing_fields"] == []


def test_bs4_sanitizer_strip_only_lineage_projects_producer_repair_kind():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "sanitizer_empty_fallback_used": False,
        "sanitizer_mode": "strip_only",
        "sanitizer_lineage_mode": "strip_only",
        "sanitizer_event_count": 1,
        "sanitizer_changed_count": 1,
        "sanitizer_lineage_changed_count": 1,
        "final_route": "accept_candidate",
        "final_emitted_source": "generated_candidate",
        "sealed_fallback_owner_bucket": "unknown-none",
        "producer_repair_kind": "sanitizer_strip_only",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_SANITIZER,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == "sanitizer_strip_only"
    assert record["owner_bucket"] == "unknown-none"
    assert record["missing_fields"] == []


def test_bs4_repair_mutation_path_baseline_records_are_resolved_complete():
    from tests.helpers.replacement_attribution_inventory import (
        build_replacement_path_attribution_report,
        build_baseline_attribution_corpus,
    )

    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    repair_stats = path_report[REPLACEMENT_PATH_REPAIR_MUTATION]
    assert repair_stats["total"] == 7
    assert repair_stats["complete"] == 7


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


def test_co84_sanitizer_empty_fallback_lineage_projects_owner_bucket():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "sanitizer_empty_fallback_used": True,
        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "sealed_fallback_owner_bucket": "unknown-none",
        "producer_repair_kind": "sanitizer_empty_output",
    }
    fallback = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "fallback_selected"
    )
    record = attribution_record_from_lineage_event(
        fallback,
        replacement_path=REPLACEMENT_PATH_SANITIZER,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "unknown-none"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_PROJECTED
    assert "owner_bucket" not in record["missing_fields"]


def test_co84_sanitizer_gate_outcome_projects_repair_owner_and_source_family():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "sanitizer_empty_fallback_used": True,
        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "sealed_fallback_owner_bucket": "unknown-none",
        "producer_repair_kind": "sanitizer_empty_output",
    }
    gate_outcome = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "gate_outcome"
    )
    record = attribution_record_from_lineage_event(
        gate_outcome,
        replacement_path=REPLACEMENT_PATH_SANITIZER,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == "sanitizer_empty_output"
    assert record["owner_bucket"] == "unknown-none"
    assert record["source_family"] == "output_sanitizer"
    assert "mutation_classification" in record["missing_fields"]


def test_co84_sanitizer_replay_projection_projects_owner_when_sealed_wiped():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events
    from tests.helpers.failure_classification_sync import observed_sanitizer_empty_fallback_row

    fem = {
        "sanitizer_empty_fallback_used": True,
        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "sealed_fallback_owner_bucket": "unknown-none",
        "producer_repair_kind": "sanitizer_empty_output",
    }
    observed = dict(fem)
    observed.update(observed_sanitizer_empty_fallback_row())
    observed["fem_runtime_lineage_events"] = build_fem_runtime_lineage_events(fem)
    record = attribution_record_from_replay_projection(observed, replacement_path=REPLACEMENT_PATH_SANITIZER)
    assert record is not None
    assert record["owner_bucket"] == "unknown-none"
    assert "owner_bucket" not in record["missing_fields"]


def test_co84_sanitizer_path_baseline_resolved_completeness():
    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    sanitizer_stats = path_report[REPLACEMENT_PATH_SANITIZER]
    assert sanitizer_stats["total"] == 10
    assert sanitizer_stats["complete"] == 9
    assert sanitizer_stats["missing_owner_bucket"] == 0
    assert sanitizer_stats["missing_mutation_classification"] == 1


def test_co85_visibility_mutation_lineage_projects_producer_attribution():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "visibility_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "visibility_fallback_pool": "global_scene_narrative",
        "visibility_fallback_kind": "narrative_safe_fallback",
        "producer_repair_kind": "visibility_enforcement",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_VISIBILITY,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["repair_kind"] == "visibility_enforcement"
    assert record["missing_fields"] == []


def test_co85_visibility_gate_outcome_projects_repair_owner_and_source_family():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "visibility_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "visibility_enforcement",
    }
    gate_outcome = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "gate_outcome"
    )
    record = attribution_record_from_lineage_event(
        gate_outcome,
        replacement_path=REPLACEMENT_PATH_VISIBILITY,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == "visibility_enforcement"
    assert record["owner_bucket"] == "sealed-gate"
    assert record["source_family"] == "final_emission_gate"
    assert "mutation_classification" in record["missing_fields"]


def test_co85_sealed_mutation_lineage_projects_owner_and_repair_kind():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "passive_scene_pressure_fallback",
        "sealed_fallback_owner_bucket": "sealed-gate",
        "fallback_kind": "passive_scene_pressure_fallback",
        "producer_repair_kind": "passive_scene_pressure_fallback",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_SEALED,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["repair_kind"] == "passive_scene_pressure_fallback"
    assert "repair_kind" not in record["missing_fields"]


def test_co85_response_type_mutation_lineage_projects_repair_kind():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "accept_candidate",
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_RESPONSE_TYPE,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == "answer_upstream_prepared_repair"
    assert "owner_bucket" in record["missing_fields"]


def test_co85_target_path_baseline_resolved_completeness():
    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    visibility_stats = path_report[REPLACEMENT_PATH_VISIBILITY]
    sealed_stats = path_report[REPLACEMENT_PATH_SEALED]
    response_stats = path_report[REPLACEMENT_PATH_RESPONSE_TYPE]
    assert visibility_stats["total"] == 5
    assert visibility_stats["complete"] == 4
    assert visibility_stats["missing_owner_bucket"] == 0
    assert visibility_stats["missing_repair_kind"] == 0
    assert visibility_stats["missing_mutation_classification"] == 1
    assert sealed_stats["total"] == 5
    assert sealed_stats["complete"] == 4
    assert sealed_stats["missing_owner_bucket"] == 0
    assert sealed_stats["missing_repair_kind"] == 0
    assert response_stats["total"] == 6
    assert response_stats["complete"] == 5
    assert response_stats["missing_repair_kind"] == 0
    assert response_stats["missing_owner_bucket"] == 0


def test_co86_first_mention_mutation_lineage_projects_producer_attribution():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "first_mention_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "first_mention_enforcement",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_FIRST_MENTION,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["repair_kind"] == "first_mention_enforcement"
    assert record["missing_fields"] == []


def test_co86_referential_gate_outcome_projects_repair_and_owner():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "global_scene_fallback",
        "referential_clarity_replacement_applied": True,
        "visibility_fallback_owner_bucket": "sealed-gate",
        "producer_repair_kind": "referential_clarity_enforcement",
    }
    gate_outcome = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "gate_outcome"
    )
    record = attribution_record_from_lineage_event(
        gate_outcome,
        replacement_path=REPLACEMENT_PATH_REFERENTIAL,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == "referential_clarity_enforcement"
    assert record["owner_bucket"] == "sealed-gate"
    assert "mutation_classification" in record["missing_fields"]


def test_co86_referential_local_substitution_fem_projects_repair_kind():
    fem = {
        "final_route": "accept_candidate",
        "referential_clarity_local_substitution_applied": True,
        "visibility_fallback_owner_bucket": "strict-social-visibility",
        "producer_repair_kind": "referential_clarity_local_substitution",
    }
    record = attribution_record_from_fem(fem)
    assert record is not None
    assert record["repair_kind"] == "referential_clarity_local_substitution"
    assert record["owner_bucket"] == "strict-social-visibility"


def test_co86_strict_social_replay_projection_projects_owner_when_sealed_wiped():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events
    from tests.helpers.failure_classification_sync import observed_social_fallback_row

    fem = {
        "final_route": "replaced",
        "strict_social_active": True,
        "final_emitted_source": "strict_social_replacement",
        "response_type_repair_used": True,
        "response_type_repair_kind": "strict_social_dialogue_repair",
        "sealed_fallback_owner_bucket": "strict-social-sealed",
        "producer_repair_kind": "strict_social_repair",
    }
    observed = dict(fem)
    observed.update(observed_social_fallback_row())
    observed["fem_runtime_lineage_events"] = build_fem_runtime_lineage_events(fem)
    record = attribution_record_from_replay_projection(
        observed,
        replacement_path=REPLACEMENT_PATH_STRICT_SOCIAL,
    )
    assert record is not None
    assert record["owner_bucket"] == "strict-social-sealed"
    assert "owner_bucket" not in record["missing_fields"]


def test_co86_gate_family_path_baseline_resolved_completeness():
    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    first_mention_stats = path_report[REPLACEMENT_PATH_FIRST_MENTION]
    referential_stats = path_report[REPLACEMENT_PATH_REFERENTIAL]
    strict_stats = path_report[REPLACEMENT_PATH_STRICT_SOCIAL]
    assert first_mention_stats["total"] == 5
    assert first_mention_stats["complete"] == 4
    assert first_mention_stats["missing_owner_bucket"] == 0
    assert first_mention_stats["missing_repair_kind"] == 0
    assert first_mention_stats["missing_mutation_classification"] == 1
    assert referential_stats["total"] == 5
    assert referential_stats["complete"] == 4
    assert referential_stats["missing_owner_bucket"] == 0
    assert referential_stats["missing_repair_kind"] == 0
    assert strict_stats["total"] == 6
    assert strict_stats["complete"] == 5
    assert strict_stats["missing_owner_bucket"] == 0
    assert strict_stats["missing_repair_kind"] == 0


def test_co87_opening_mutation_lineage_projects_preserved_repair_kind():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = successful_opening_fem_meta(
        final_route="replaced",
        response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
        opening_fallback_owner_bucket="upstream-prepared",
    )
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_OPENING_FALLBACK,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == OPENING_SUCCESS_REPAIR_KIND
    assert record["attribution_origin"]["repair_kind"] == ATTRIBUTION_ORIGIN_PROJECTED
    assert "repair_kind" not in record["missing_fields"]


def test_co87_opening_gate_outcome_projects_repair_and_owner():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = successful_opening_fem_meta(
        final_route="replaced",
        response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
        opening_fallback_owner_bucket="upstream-prepared",
    )
    gate_outcome = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "gate_outcome"
    )
    record = attribution_record_from_lineage_event(
        gate_outcome,
        replacement_path=REPLACEMENT_PATH_OPENING_FALLBACK,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == OPENING_SUCCESS_REPAIR_KIND
    assert record["owner_bucket"] == "upstream-prepared"
    assert record["source_family"] == "final_emission_gate"
    assert "mutation_classification" in record["missing_fields"]


def test_co87_opening_gate_outcome_without_fem_repair_kind_stays_unresolved():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "opening_deterministic_fallback",
        "opening_recovered_via_fallback": True,
        "opening_fallback_authorship_source": "upstream_prepared_opening_fallback",
        "fallback_family_used": "scene_opening",
        "opening_fallback_owner_bucket": "upstream-prepared",
    }
    gate_outcome = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "gate_outcome"
    )
    record = attribution_record_from_lineage_event(
        gate_outcome,
        replacement_path=REPLACEMENT_PATH_OPENING_FALLBACK,
        fem=fem,
    )
    assert record is not None
    assert "repair_kind" in record["missing_fields"]


def test_co87_opening_path_baseline_resolved_completeness():
    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    opening_stats = path_report[REPLACEMENT_PATH_OPENING_FALLBACK]
    assert opening_stats["total"] == 7
    assert opening_stats["complete"] == 6
    assert opening_stats["missing_owner_bucket"] == 0
    assert opening_stats["missing_repair_kind"] == 0
    assert opening_stats["missing_recurrence_key"] == 0
    assert opening_stats["missing_mutation_classification"] == 1


def test_co93_sealed_passive_baseline_resolved_repair_kind():
    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    sealed_stats = path_report[REPLACEMENT_PATH_SEALED]
    assert sealed_stats["total"] == 5
    assert sealed_stats["complete"] == 4
    assert sealed_stats["missing_owner_bucket"] == 0
    assert sealed_stats["missing_repair_kind"] == 0
    assert sealed_stats["missing_mutation_classification"] == 1


def test_co88_sealed_mutation_projects_preserved_fem_repair_kind():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "passive_scene_pressure_fallback",
        "sealed_fallback_owner_bucket": "sealed-gate",
        "fallback_kind": "passive_scene_pressure_fallback",
        "producer_repair_kind": "passive_scene_pressure_fallback",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_SEALED,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == "passive_scene_pressure_fallback"
    assert record["attribution_origin"]["repair_kind"] == ATTRIBUTION_ORIGIN_PROJECTED
    assert "repair_kind" not in record["missing_fields"]


def test_co88_sealed_gate_outcome_projects_preserved_fem_repair_kind():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "passive_scene_pressure_fallback",
        "sealed_fallback_owner_bucket": "sealed-gate",
        "fallback_kind": "passive_scene_pressure_fallback",
        "producer_repair_kind": "passive_scene_pressure_fallback",
    }
    gate_outcome = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "gate_outcome"
    )
    record = attribution_record_from_lineage_event(
        gate_outcome,
        replacement_path=REPLACEMENT_PATH_SEALED,
        fem=fem,
    )
    assert record is not None
    assert record["repair_kind"] == "passive_scene_pressure_fallback"
    assert record["owner_bucket"] == "sealed-gate"
    assert "mutation_classification" in record["missing_fields"]


def test_co93_sealed_passive_producer_stamp_is_direct_on_fem():
    fem = {
        "final_route": "replaced",
        "final_emitted_source": "passive_scene_pressure_fallback",
        "sealed_fallback_owner_bucket": "sealed-gate",
        "fallback_kind": "passive_scene_pressure_fallback",
        "producer_repair_kind": "passive_scene_pressure_fallback",
    }
    record = attribution_record_from_fem(fem, replacement_path=REPLACEMENT_PATH_SEALED)
    assert record is not None
    assert record["repair_kind"] == "passive_scene_pressure_fallback"
    assert record["attribution_origin"]["repair_kind"] == ATTRIBUTION_ORIGIN_DIRECT
    assert "repair_kind" not in record["missing_fields"]


def test_co94_gate_outcome_events_omit_mutation_kind_by_lineage_contract() -> None:
    """CO94: gate_outcome records routing (gate_path); mutation_kind belongs on mutation events only."""
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events
    from tests.helpers.replacement_attribution_inventory import _baseline_corpus_fixtures

    for path, fem, _drift in _baseline_corpus_fixtures():
        events = build_fem_runtime_lineage_events(fem)
        gate_outcomes = [event for event in events if event.get("event_kind") == "gate_outcome"]
        if not gate_outcomes:
            continue
        for gate_outcome in gate_outcomes:
            assert gate_outcome.get("mutation_kind") is None
            assert gate_outcome.get("gate_path")
            record = attribution_record_from_lineage_event(
                gate_outcome,
                replacement_path=path,
                fem=fem,
            )
            assert record is not None
            assert "mutation_classification" in record["missing_fields"]


def test_co94_baseline_gate_outcome_mutation_gap_matches_sibling_mutation_coverage() -> None:
    """CO94: every baseline gate_outcome gap has a sibling mutation event carrying classification."""
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events
    from tests.helpers.replacement_attribution_inventory import _baseline_corpus_fixtures

    gap_count = 0
    for path, fem, _drift in _baseline_corpus_fixtures():
        events = build_fem_runtime_lineage_events(fem)
        mutations = [event for event in events if event.get("event_kind") == "mutation"]
        for gate_outcome in (event for event in events if event.get("event_kind") == "gate_outcome"):
            gate_record = attribution_record_from_lineage_event(
                gate_outcome,
                replacement_path=path,
                fem=fem,
            )
            assert gate_record is not None
            if "mutation_classification" not in gate_record["missing_fields"]:
                continue
            gap_count += 1
            assert mutations, f"{path} gate_outcome gap requires sibling mutation event"
            mutation_record = attribution_record_from_lineage_event(
                mutations[0],
                replacement_path=path,
                fem=fem,
            )
            assert mutation_record is not None
            assert "mutation_classification" not in mutation_record["missing_fields"]
    assert gap_count == 8


def test_co94_bs5_mutation_classification_gap_is_gate_outcome_only() -> None:
    records = build_baseline_attribution_corpus()
    missing_mutation = [
        record
        for record in records
        if "mutation_classification" in (record.get("missing_fields") or [])
    ]
    assert len(missing_mutation) == 8
    assert all(record.get("source_kind") == "runtime_lineage_event" for record in missing_mutation)


def test_co88_sealed_passive_without_preserved_repair_stays_unresolved():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "replaced",
        "final_emitted_source": "passive_scene_pressure_fallback",
        "sealed_fallback_owner_bucket": "sealed-gate",
        "fallback_kind": "passive_scene_pressure_fallback",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_SEALED,
        fem=fem,
    )
    assert record is not None
    assert "repair_kind" in record["missing_fields"]


def test_co89_response_type_passive_baseline_resolved_owner_bucket():
    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    response_stats = path_report[REPLACEMENT_PATH_RESPONSE_TYPE]
    assert response_stats["total"] == 6
    assert response_stats["complete"] == 5
    assert response_stats["missing_owner_bucket"] == 0
    assert response_stats["missing_repair_kind"] == 0
    assert response_stats["missing_mutation_classification"] == 1


def test_co89_response_type_mutation_projects_preserved_sealed_owner_bucket():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "accept_candidate",
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
        "sealed_fallback_owner_bucket": "sealed-gate",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_RESPONSE_TYPE,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_DIRECT
    assert "owner_bucket" not in record["missing_fields"]


def test_co89_response_type_gate_outcome_projects_preserved_sealed_owner_bucket():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "accept_candidate",
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
        "sealed_fallback_owner_bucket": "sealed-gate",
    }
    gate_outcome = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "gate_outcome"
    )
    record = attribution_record_from_lineage_event(
        gate_outcome,
        replacement_path=REPLACEMENT_PATH_RESPONSE_TYPE,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert "mutation_classification" in record["missing_fields"]


def test_co89_response_type_fem_metadata_projects_direct_sealed_owner_bucket():
    fem = {
        "final_route": "accept_candidate",
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
        "sealed_fallback_owner_bucket": "sealed-gate",
    }
    record = attribution_record_from_fem(fem, replacement_path=REPLACEMENT_PATH_RESPONSE_TYPE)
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_DIRECT
    assert record["missing_fields"] == []


def test_co89_response_type_failure_classification_projects_owner_from_observed_turn():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    observed = {
        "final_route": "accept_candidate",
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
        "sealed_fallback_owner_bucket": "sealed-gate",
        "fem_runtime_lineage_events": build_fem_runtime_lineage_events(
            {
                "final_route": "accept_candidate",
                "response_type_repair_used": True,
                "response_type_repair_kind": "answer_upstream_prepared_repair",
                "upstream_prepared_emission_used": True,
                "sealed_fallback_owner_bucket": "sealed-gate",
            }
        ),
    }
    classification = classify_replay_failure(
        scenario_id="co89_response_type",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[response_type_repair_drift_row()],
    )[0]
    record = attribution_record_from_failure_classification(
        classification,
        replacement_path=REPLACEMENT_PATH_RESPONSE_TYPE,
        observed_turn=observed,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert "owner_bucket" not in record["missing_fields"]


def test_co89_response_type_without_preserved_bucket_stays_unresolved():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "accept_candidate",
        "response_type_repair_used": True,
        "response_type_repair_kind": "answer_upstream_prepared_repair",
        "upstream_prepared_emission_used": True,
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_RESPONSE_TYPE,
        fem=fem,
    )
    assert record is not None
    assert "owner_bucket" in record["missing_fields"]


def test_co90_repair_mutation_baseline_resolved_completeness():
    path_report = build_replacement_path_attribution_report(build_baseline_attribution_corpus())
    repair_stats = path_report[REPLACEMENT_PATH_REPAIR_MUTATION]
    assert repair_stats["total"] == 7
    assert repair_stats["complete"] == 7
    assert repair_stats["missing_owner_bucket"] == 0
    assert repair_stats["missing_repair_kind"] == 0
    assert repair_stats["missing_mutation_classification"] == 0


def test_co90_passive_scene_mutation_lineage_projects_owner_from_producer_evidence():
    from game.runtime_lineage_telemetry import make_runtime_lineage_event

    fem = {
        "final_route": "accept_candidate",
        "passive_scene_concrete_beat_satisfier_applied": True,
        "passive_scene_pressure_fallback_avoided": True,
        "passive_scene_concrete_beat_type": "guard_reaction",
        "producer_repair_kind": "passive_scene_concrete_beat",
    }
    mutation = make_runtime_lineage_event(
        event_kind="mutation",
        stage="gate",
        owner="game.final_emission_gate",
        mutation_kind="final_emission_mutation",
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_REPAIR_MUTATION,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_PROJECTED
    assert "owner_bucket" not in record["missing_fields"]


def test_co90_fallback_behavior_mutation_lineage_projects_direct_sealed_owner():
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    fem = {
        "final_route": "accept_candidate",
        "fallback_behavior_repaired": True,
        "fallback_behavior_repair_kind": "fallback_behavior_repair",
        "producer_repair_kind": "fallback_behavior_repair",
        "sealed_fallback_owner_bucket": "sealed-gate",
    }
    mutation = next(
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_kind") == "mutation"
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_REPAIR_MUTATION,
        fem=fem,
    )
    assert record is not None
    assert record["owner_bucket"] == "sealed-gate"
    assert record["attribution_origin"]["owner_bucket"] == ATTRIBUTION_ORIGIN_DIRECT
    assert "owner_bucket" not in record["missing_fields"]


def test_co90_repair_mutation_without_bucket_evidence_stays_unresolved():
    from game.runtime_lineage_telemetry import make_runtime_lineage_event

    mutation = make_runtime_lineage_event(
        event_kind="mutation",
        stage="gate",
        owner="game.final_emission_gate",
        mutation_kind="repair_only_mutation",
    )
    record = attribution_record_from_lineage_event(
        mutation,
        replacement_path=REPLACEMENT_PATH_REPAIR_MUTATION,
    )
    assert record is not None
    assert "owner_bucket" in record["missing_fields"]


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


def test_split_owner_acceptance_matrix_attribution_inventory_lineage_alignment() -> None:
    """BU15: attribution inventory reads the same owner literals as the canonical matrix."""
    for row in split_owner_acceptance_matrix_rows():
        if row.event_kind == "mutation":
            observed = split_owner_observed_row_from_matrix_row(row)
            record = attribution_record_from_replay_projection(observed)
            assert record is not None
            assert record["owner_bucket"] == row.owner_bucket
            assert record["repair_kind"] == row.repair_kind
            continue

        event = split_owner_lineage_event_from_matrix_row(row)
        assert_split_owner_matrix_lineage_event(row, event)
        record = attribution_record_from_lineage_event(event)
        assert record is not None
        if row.owner_bucket is not None:
            assert record["owner_bucket"] == row.owner_bucket
            assert "owner_bucket" not in record["missing_fields"]
        if row.repair_kind is not None:
            assert record["repair_kind"] == row.repair_kind
            assert "repair_kind" not in record["missing_fields"]


def test_split_owner_acceptance_matrix_fem_attribution_inventory_matches_production_projection() -> None:
    """BU16: attribution inventory reads owner literals from production FEM projection fixtures."""
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    for row in split_owner_acceptance_matrix_rows():
        if split_owner_fem_projection_excluded(row):
            continue
        fem = split_owner_fem_meta_from_matrix_row(row)
        events = build_fem_runtime_lineage_events(fem)
        if row.event_kind == "mutation":
            observed = project_split_owner_matrix_row(row)
            fem_record = attribution_record_from_fem(fem)
            assert fem_record is not None
            assert fem_record["owner_bucket"] == row.owner_bucket
            assert fem_record["repair_kind"] == row.repair_kind
            assert observed.get(row.owner_bucket_field) == row.owner_bucket
            continue

        event = next(item for item in events if item.get("event_kind") == "fallback_selected")
        assert_split_owner_matrix_lineage_event(row, event)
        record = attribution_record_from_lineage_event(event)
        assert record is not None
        if row.owner_bucket is not None and record.get("owner_bucket") is not None:
            assert record["owner_bucket"] == row.owner_bucket
        if row.repair_kind is not None and record.get("repair_kind") is not None:
            assert record["repair_kind"] == row.repair_kind
