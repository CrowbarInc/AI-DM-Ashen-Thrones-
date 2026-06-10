from __future__ import annotations

from pathlib import Path

from tests.helpers.replay_bug_recurrence import (
    RECURRENCE_ADVISORY_ONLY,
    RECURRENCE_REPORT_ONLY,
    SUMMARY_RECURRENCE_STATUSES,
    aggregate_recurrence_history,
    build_recurrence_key,
    build_recurrence_summary,
    classify_recurrence_status,
    recurrence_rows,
    recurrence_status,
)


def _classification_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "scenario_id": "recurrence_probe",
        "turn_index": 2,
        "category": "speaker",
        "primary_owner": "speaker",
        "owner_drift_bucket": "speaker_drift",
        "field_path": "selected_speaker_id",
        "investigate_first": "game/speaker_contract_enforcement.py",
    }
    row.update(overrides)
    return row


def test_same_owner_category_field_produces_same_recurrence_key() -> None:
    left = _classification_row(scenario_id="left", turn_index=0)
    right = _classification_row(scenario_id="right", turn_index=9)

    assert build_recurrence_key(left) == build_recurrence_key(right)


def test_different_field_path_produces_different_recurrence_key() -> None:
    speaker_key = build_recurrence_key(_classification_row(field_path="selected_speaker_id"))
    route_key = build_recurrence_key(_classification_row(field_path="route_kind"))

    assert speaker_key != route_key


def test_missing_owner_bucket_falls_back_to_replay_drift_unclassified() -> None:
    row = _classification_row(owner_drift_bucket=None)

    assert build_recurrence_key(row).startswith("recurrence:v1:replay_drift_unclassified|")
    assert recurrence_rows([row])[0]["owner_drift_bucket"] == "replay_drift_unclassified"


def test_recurrence_rows_preserve_existing_classification_identity() -> None:
    row = _classification_row()

    projected = recurrence_rows([row])[0]

    assert projected["scenario_id"] == "recurrence_probe"
    assert projected["turn_index"] == 2
    assert projected["category"] == "speaker"
    assert projected["primary_owner"] == "speaker"
    assert projected["owner_drift_bucket"] == "speaker_drift"
    assert projected["recurrence_status"] == "active"


def test_helper_is_report_only_and_advisory_only() -> None:
    row = recurrence_rows([_classification_row()])[0]

    assert RECURRENCE_REPORT_ONLY is True
    assert RECURRENCE_ADVISORY_ONLY is True
    assert row["report_only"] is True
    assert row["advisory_only"] is True
    assert recurrence_status({"status": "retired"}) == "retired"
    assert recurrence_status({"status": "BLOCKED"}) == "active"


def test_repeated_keys_increment_occurrence_count() -> None:
    rows = recurrence_rows(
        [
            _classification_row(scenario_id="a"),
            _classification_row(scenario_id="b"),
        ]
    )

    history = aggregate_recurrence_history(rows)

    assert history["unique_recurrence_count"] == 1
    assert history["recurrences"][0]["occurrence_count"] == 2
    assert build_recurrence_summary(history)[0]["occurrence_count"] == 2


def test_first_and_last_seen_indexes_are_deterministic() -> None:
    repeated = _classification_row(scenario_id="a")
    other = _classification_row(
        scenario_id="b",
        field_path="route_kind",
        investigate_first="game/interaction_context.py",
    )
    rows = recurrence_rows([repeated, other, repeated])

    history = aggregate_recurrence_history(rows)
    repeated_entry = history["recurrences"][0]

    assert repeated_entry["first_seen_index"] == 0
    assert repeated_entry["last_seen_index"] == 2
    assert history["recurrences"][1]["first_seen_index"] == 1
    assert history["recurrences"][1]["last_seen_index"] == 1


def test_affected_scenarios_are_deduplicated_and_sorted() -> None:
    rows = recurrence_rows(
        [
            _classification_row(scenario_id="zeta"),
            _classification_row(scenario_id="alpha"),
            _classification_row(scenario_id="zeta"),
        ]
    )

    entry = aggregate_recurrence_history(rows)["recurrences"][0]

    assert entry["affected_scenarios"] == ["alpha", "zeta"]
    assert entry["categories"] == ["speaker"]
    assert entry["field_paths"] == ["selected_speaker_id"]


def test_active_status_is_preserved() -> None:
    rows = recurrence_rows([_classification_row(status="active")])

    entry = aggregate_recurrence_history(rows)["recurrences"][0]

    assert entry["status"] == "active"


def test_empty_input_returns_empty_report_only_advisory_only_history() -> None:
    history = aggregate_recurrence_history([])

    assert history["report_only"] is True
    assert history["advisory_only"] is True
    assert history["total_rows"] == 0
    assert history["unique_recurrence_count"] == 0
    assert history["recurrences"] == []
    assert build_recurrence_summary(history) == []


def test_repeated_recurrence_summary_becomes_active() -> None:
    history = aggregate_recurrence_history(
        recurrence_rows(
            [
                _classification_row(scenario_id="a"),
                _classification_row(scenario_id="b"),
            ]
        )
    )

    summary = build_recurrence_summary(history)

    assert summary[0]["status"] == "active"
    assert classify_recurrence_status(summary[0]) == "active"


def test_single_recurrence_summary_becomes_watch() -> None:
    history = aggregate_recurrence_history(recurrence_rows([_classification_row()]))

    assert build_recurrence_summary(history)[0]["status"] == "watch"


def test_explicit_retired_or_deprecated_input_becomes_retired() -> None:
    retired_history = aggregate_recurrence_history(recurrence_rows([_classification_row(status="retired")]))
    deprecated_history = aggregate_recurrence_history(recurrence_rows([_classification_row(status="deprecated")]))

    assert build_recurrence_summary(retired_history)[0]["status"] == "retired"
    assert build_recurrence_summary(deprecated_history)[0]["status"] == "retired"
    assert recurrence_status({"status": "deprecated"}) == "active"


def test_missing_status_never_becomes_retired_automatically() -> None:
    history = aggregate_recurrence_history(recurrence_rows([_classification_row(status=None)]))

    assert build_recurrence_summary(history)[0]["status"] == "watch"


def test_recurrence_status_vocabulary_is_bounded() -> None:
    assert SUMMARY_RECURRENCE_STATUSES == frozenset({"active", "watch", "retired"})
    history = aggregate_recurrence_history(
        recurrence_rows(
            [
                _classification_row(),
                _classification_row(field_path="route_kind", investigate_first="game/interaction_context.py"),
                _classification_row(status="deprecated"),
            ]
        )
    )

    assert {row["status"] for row in build_recurrence_summary(history)} <= SUMMARY_RECURRENCE_STATUSES


def test_protected_replay_manifest_documents_cycle_ay_recurrence_policy() -> None:
    manifest = Path("docs/testing/protected_replay_manifest.md").read_text(encoding="utf-8")

    assert "## Cycle AY Recurrence Reporting Addendum" in manifest
    assert "report_only: true" in manifest
    assert "advisory_only: true" in manifest
    assert "owner_drift_bucket`, `category`, `field_path`, and `investigate_first" in manifest
    assert "`retired` is explicit-only" in manifest
    assert "governance registry decisions" in manifest
