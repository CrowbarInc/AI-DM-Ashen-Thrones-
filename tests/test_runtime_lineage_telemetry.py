"""Tests for read-side runtime lineage event vocabulary."""

from __future__ import annotations

import json

from game.runtime_lineage_telemetry import (
    RUNTIME_LINEAGE_EVENT_TYPE,
    build_recurrence_key,
    make_runtime_lineage_event,
    normalize_runtime_lineage_events,
    summarize_runtime_lineage_events,
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
    assert summary["gate_path_frequency"] == {"opening_fallback": 1}
    assert summary["recurring_events"] == [{"recurrence_key": "persisted:opening:key", "count": 2}]
