"""Tests for read-side runtime lineage event vocabulary."""

from __future__ import annotations

import json

from game.ownership_projection_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
)
from game.final_emission_replay_projection import (
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
)
from game.runtime_lineage_telemetry import (
    RUNTIME_LINEAGE_EVENT_TYPE,
    build_recurrence_key,
    make_runtime_lineage_event,
    normalize_runtime_lineage_events,
    runtime_lineage_vocabulary_summary,
    summarize_runtime_lineage_events,
)
from tests.helpers.failure_classification_sync import (
    assert_split_owner_matrix_fem_projection,
    assert_split_owner_matrix_lineage_event,
    project_split_owner_matrix_row,
    split_owner_acceptance_matrix_rows,
    split_owner_fem_meta_from_matrix_row,
    split_owner_fem_projection_excluded,
    split_owner_lineage_event_from_matrix_row,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.attribution_read_views import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
)
from tests.helpers.runtime_lineage_reporting import (
    build_runtime_lineage_summary,
    build_runtime_lineage_summary_from_branch_transcripts,
    runtime_lineage_markdown_lines,
)


def test_make_runtime_lineage_event_is_json_serializable_and_normalized() -> None:
    event = make_runtime_lineage_event(
        event_kind=" Fallback Selected ",
        stage="GATE",
        owner="game.final_emission_gate",
        source=" game.final_emission_gate.apply_final_emission_gate ",
        fallback_kind="Opening Failed-Closed",
        fallback_authorship_source="upstream_prepared_opening_fallback",
        fallback_owner_bucket="upstream-prepared",
        fallback_selection_owner="game.final_emission_gate",
        fallback_content_owner="game.opening_deterministic_fallback",
        notes=["selected", "selected", " sealed "],
    )

    assert event == {
        "event_type": RUNTIME_LINEAGE_EVENT_TYPE,
        "event_kind": "fallback_selected",
        "stage": "gate",
        "owner": "game.final_emission_gate",
        "source": "game.final_emission_gate.apply_final_emission_gate",
        "gate_path": None,
        "mutation_kind": None,
        "fallback_kind": "opening_failed_closed",
        "fallback_authorship_source": "upstream_prepared_opening_fallback",
        "fallback_owner_bucket": "upstream-prepared",
        "fallback_selection_owner": "game.final_emission_gate",
        "fallback_content_owner": "game.opening_deterministic_fallback",
        "repair_kind": None,
        "recurrence_key": "fallback_selected:gate:game.final_emission_gate:opening_failed_closed",
        "notes": ["selected", "sealed"],
    }
    assert json.loads(json.dumps(event)) == event


def test_build_recurrence_key_is_deterministic_and_uses_kind_precedence() -> None:
    kwargs = {
        "event_kind": "mutation",
        "stage": "sanitizer",
        "owner": "game.output_sanitizer",
        "fallback_kind": "empty-output",
        "repair_kind": "repair-mode",
        "mutation_kind": "final-emission-mutation",
        "gate_path": "replaced",
    }
    assert build_recurrence_key(**kwargs) == build_recurrence_key(**kwargs)
    assert build_recurrence_key(**kwargs).endswith(":empty_output")

    assert build_recurrence_key(
        event_kind="speaker_repair",
        stage="gate",
        owner="game.speaker_contract_enforcement",
        repair_kind="local_rebind",
        mutation_kind="repair_only_mutation",
        gate_path="accept_repaired",
    ).endswith(":local_rebind")
    assert build_recurrence_key(
        event_kind="mutation",
        stage="gate",
        owner="game.final_emission_gate",
        mutation_kind="gate_mutation",
        gate_path="accept_repaired",
    ).endswith(":gate_mutation")
    assert build_recurrence_key(
        event_kind="gate_outcome",
        stage="gate",
        owner="game.final_emission_gate",
        gate_path="accept_unchanged",
    ).endswith(":accept_unchanged")


def test_make_runtime_lineage_event_preserves_sanitizer_split_owners() -> None:
    event = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="sanitizer",
        owner="game.output_sanitizer",
        fallback_kind="sanitizer_strict_social",
        fallback_selection_owner="game.output_sanitizer",
        fallback_content_owner="game.social_exchange_emission",
    )
    assert event["owner"] == "game.output_sanitizer"
    assert event["fallback_selection_owner"] == "game.output_sanitizer"
    assert event["fallback_content_owner"] == "game.social_exchange_emission"
    assert event["recurrence_key"] == "fallback_selected:sanitizer:game.output_sanitizer:sanitizer_strict_social"


def test_missing_optional_fields_are_safe_and_require_no_runtime_object() -> None:
    event = make_runtime_lineage_event(event_kind="gate_outcome")

    assert event["event_type"] == "runtime_lineage"
    assert event["event_kind"] == "gate_outcome"
    assert event["stage"] == "unknown"
    assert event["owner"] is None
    assert event["source"] is None
    assert event["notes"] == []
    assert event["recurrence_key"] == "gate_outcome:unknown:unknown:unknown"


def test_normalize_runtime_lineage_events_is_safe_bounded_projection() -> None:
    raw = [
        {
            "event_kind": "speaker repair",
            "stage": "post-emission",
            "owner": "game.post_emission_speaker_adoption",
            "repair_kind": "stale interlocutor invalidation",
            "fallback_authorship_source": "upstream_prepared_opening_fallback",
            "fallback_owner_bucket": "upstream-prepared",
            "fallback_selection_owner": "game.final_emission_gate",
            "fallback_content_owner": "game.opening_deterministic_fallback",
            "notes": " corrected ",
        },
        {"event_kind": "not-supported", "stage": "nowhere", "mutation_kind": "state mutation"},
        "skip me",
    ]

    normalized = normalize_runtime_lineage_events(raw)

    assert len(normalized) == 2
    assert normalized[0]["event_kind"] == "speaker_repair"
    assert normalized[0]["stage"] == "post_emission"
    assert normalized[0]["repair_kind"] == "stale_interlocutor_invalidation"
    assert normalized[0]["fallback_authorship_source"] == "upstream_prepared_opening_fallback"
    assert normalized[0]["fallback_owner_bucket"] == "upstream-prepared"
    assert normalized[0]["fallback_selection_owner"] == "game.final_emission_gate"
    assert normalized[0]["fallback_content_owner"] == "game.opening_deterministic_fallback"
    assert normalized[0]["notes"] == ["corrected"]
    assert normalized[1]["event_kind"] == "unknown"
    assert normalized[1]["stage"] == "unknown"
    assert raw[0]["repair_kind"] == "stale interlocutor invalidation"
    assert normalize_runtime_lineage_events(None) == []
    assert normalize_runtime_lineage_events({"event_kind": "mutation"}) == []


def test_summarize_runtime_lineage_events_owns_frequency_and_persisted_recurrence_buckets() -> None:
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
    recorded = dict(fallback)
    recorded["recurrence_key"] = "persisted:opening:key"
    summary = summarize_runtime_lineage_events(
        [
            recorded,
            recorded,
            make_runtime_lineage_event(
                event_kind="gate_outcome",
                stage="gate",
                owner="game.final_emission_gate",
                gate_path="opening_fallback",
            ),
            {"event_type": "different_event_type", "event_kind": "fallback_selected"},
        ]
    )

    assert summary["total_events"] == 3
    assert summary["by_event_kind"] == {"fallback_selected": 2, "gate_outcome": 1}
    assert summary["fallback_frequency"] == {"scene_opening": 2}
    assert summary["fallback_authorship_frequency"] == {"upstream_prepared_opening_fallback": 2}
    assert summary["fallback_owner_bucket_frequency"] == {"upstream-prepared": 2}
    assert summary["fallback_selection_owner_frequency"] == {"game.final_emission_gate": 2}
    assert summary["fallback_content_owner_frequency"] == {"game.opening_deterministic_fallback": 2}
    assert summary["gate_path_frequency"] == {"opening_fallback": 1}
    assert summary["recurring_events"] == [{"recurrence_key": "persisted:opening:key", "count": 2}]


def test_summarize_runtime_lineage_events_counts_opening_family_split_owner_trifecta() -> None:
    summary = summarize_runtime_lineage_events(
        [
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="gate",
                owner=OPENING_FALLBACK_SELECTION_OWNER,
                fallback_kind="scene_opening",
                fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
                fallback_authorship_source="upstream_prepared_opening_fallback",
                fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
                fallback_content_owner=OPENING_FALLBACK_CONTENT_OWNER,
                repair_kind="opening_deterministic_fallback",
            ),
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="gate",
                owner=OPENING_FALLBACK_SELECTION_OWNER,
                fallback_kind="opening_failed_closed",
                fallback_owner_bucket=OPENING_FALLBACK_OWNER_SEALED_GATE,
                fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
                fallback_content_owner=OPENING_FAIL_CLOSED_CONTENT_OWNER,
                repair_kind="opening_deterministic_fallback_failed_closed",
            ),
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="gate",
                owner=OPENING_FALLBACK_SELECTION_OWNER,
                fallback_kind="scene_opening",
                fallback_owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
                fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
                fallback_content_owner=OPENING_FALLBACK_CONTENT_OWNER,
            ),
        ]
    )

    assert summary["fallback_selection_owner_frequency"] == {OPENING_FALLBACK_SELECTION_OWNER: 3}
    assert summary["fallback_content_owner_frequency"] == {
        OPENING_FALLBACK_CONTENT_OWNER: 2,
        OPENING_FAIL_CLOSED_CONTENT_OWNER: 1,
    }
    assert summary["fallback_owner_bucket_frequency"] == {
        OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED: 2,
        OPENING_FALLBACK_OWNER_SEALED_GATE: 1,
    }
    assert summary["fallback_frequency"] == {"scene_opening": 2, "opening_failed_closed": 1}


def test_summarize_runtime_lineage_events_counts_sanitizer_upstream_fast_split_owner_trifecta() -> None:
    summary = summarize_runtime_lineage_events(
        [
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="sanitizer",
                owner="game.output_sanitizer",
                fallback_kind="sanitizer_strict_social",
                fallback_selection_owner="game.output_sanitizer",
                fallback_content_owner="game.social_exchange_emission",
            ),
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="sanitizer",
                owner="game.output_sanitizer",
                fallback_kind="sanitizer_empty_output",
                fallback_selection_owner="game.output_sanitizer",
                fallback_content_owner="game.output_sanitizer",
            ),
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="retry",
                owner="game.api",
                fallback_kind="upstream_fast_fallback",
                fallback_owner_bucket="retry",
                fallback_selection_owner="game.api",
                fallback_content_owner="game.gm_retry",
            ),
        ]
    )

    assert summary["fallback_selection_owner_frequency"] == {
        "game.output_sanitizer": 2,
        "game.api": 1,
    }
    assert summary["fallback_content_owner_frequency"] == {
        "game.output_sanitizer": 1,
        "game.social_exchange_emission": 1,
        "game.gm_retry": 1,
    }
    assert summary["fallback_owner_bucket_frequency"] == {"retry": 1}


def test_summarize_runtime_lineage_events_counts_sealed_family_split_owner_trifecta() -> None:
    summary = summarize_runtime_lineage_events(
        [
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="gate",
                owner=SEALED_FALLBACK_SELECTION_OWNER,
                fallback_kind=SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
                fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
                fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
                fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
            ),
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="gate",
                owner=SEALED_FALLBACK_SELECTION_OWNER,
                fallback_kind=SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
                fallback_owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
                fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
                fallback_content_owner=STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
            ),
            make_runtime_lineage_event(
                event_kind="fallback_selected",
                stage="gate",
                owner=SEALED_FALLBACK_SELECTION_OWNER,
                fallback_kind="sealed_or_global_replacement",
                fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
                fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
                fallback_content_owner=SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
            ),
        ]
    )

    assert summary["fallback_selection_owner_frequency"] == {SEALED_FALLBACK_SELECTION_OWNER: 3}
    assert summary["fallback_content_owner_frequency"] == {
        SEALED_FALLBACK_MODULE_CONTENT_OWNER: 1,
        STRICT_SOCIAL_FALLBACK_CONTENT_OWNER: 1,
        SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER: 1,
    }
    assert summary["fallback_owner_bucket_frequency"] == {
        SEALED_FALLBACK_OWNER_SEALED_GATE: 2,
        SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED: 1,
    }
    assert summary["fallback_frequency"] == {
        SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE: 1,
        SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR: 1,
        "sealed_or_global_replacement": 1,
    }


def test_runtime_lineage_reporting_helper_delegates_to_runtime_summarize() -> None:
    events = [
        make_runtime_lineage_event(
            event_kind="fallback_selected",
            stage="gate",
            owner="game.final_emission_gate",
            fallback_kind="scene_opening",
        ),
        make_runtime_lineage_event(
            event_kind="gate_outcome",
            stage="gate",
            owner="game.final_emission_gate",
            gate_path="opening_fallback",
        ),
    ]
    via_helper = build_runtime_lineage_summary(events)
    via_runtime = summarize_runtime_lineage_events(normalize_runtime_lineage_events(events))
    assert via_helper == via_runtime

    branch_summary = build_runtime_lineage_summary_from_branch_transcripts(
        {
            "branch_a": [
                {"meta": {"runtime_lineage_events": events}},
            ]
        }
    )
    assert branch_summary == via_helper

    markdown = runtime_lineage_markdown_lines(via_helper, profile="dashboard")
    assert "## Runtime Lineage Summary" in "\n".join(markdown)
    assert "Top fallback kinds" in "\n".join(markdown)
    assert "Top fallback selection owners" in "\n".join(markdown)
    assert "Top fallback content owners" in "\n".join(markdown)
    assert "Top fallback owner buckets" in "\n".join(markdown)


def test_runtime_lineage_vocabulary_summary_documents_visibility_producer_stamps() -> None:
    summary = runtime_lineage_vocabulary_summary()
    note = str(summary.get("producer_stamp_helpers_note") or "")
    assert "visibility" in note
    assert "final_emission_meta" in note


def test_split_owner_acceptance_matrix_runtime_lineage_summary_covers_all_rows() -> None:
    """BU15: runtime lineage summary counts every canonical split-owner matrix row."""
    events = [split_owner_lineage_event_from_matrix_row(row) for row in split_owner_acceptance_matrix_rows()]
    for row, event in zip(split_owner_acceptance_matrix_rows(), events, strict=True):
        assert_split_owner_matrix_lineage_event(row, event)

    summary = summarize_runtime_lineage_events(events)
    assert summary["total_events"] == len(events)

    fallback_rows = [row for row in split_owner_acceptance_matrix_rows() if row.event_kind == "fallback_selected"]
    for row in fallback_rows:
        assert summary["fallback_frequency"][str(row.fallback_kind)] >= 1
        assert summary["fallback_selection_owner_frequency"][str(row.fallback_selection_owner)] >= 1
        assert summary["fallback_content_owner_frequency"][str(row.fallback_content_owner)] >= 1

    bucket_rows = [row for row in fallback_rows if row.owner_bucket is not None]
    for row in bucket_rows:
        assert summary["fallback_owner_bucket_frequency"][str(row.owner_bucket)] >= 1

    assert summary["by_event_kind"]["mutation"] >= 1


def test_split_owner_acceptance_matrix_fem_builder_projection_matches_matrix() -> None:
    """BU16: production FEM lineage builder matches canonical matrix for every projectable row."""
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events

    for row in split_owner_acceptance_matrix_rows():
        if split_owner_fem_projection_excluded(row):
            continue
        fem = split_owner_fem_meta_from_matrix_row(row)
        events = build_fem_runtime_lineage_events(fem)
        if row.event_kind == "mutation":
            event = next(item for item in events if item.get("event_kind") == "mutation")
        else:
            event = next(item for item in events if item.get("event_kind") == "fallback_selected")
        assert_split_owner_matrix_lineage_event(row, event)

        observed = project_split_owner_matrix_row(row)
        assert_split_owner_matrix_fem_projection(row, observed)
