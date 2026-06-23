"""BZ protected replay trend window #2 lifecycle and recurrence movement tests (BZ1/BZ2)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from tests.helpers.golden_replay_trend import (
    BZ_REPLAY_KEY_DIMENSIONS,
    BZ_REPLAY_KEY_MOVEMENT_FILENAME,
    build_bz_replay_key_movement_report,
    build_replay_key_catalog,
    build_run_envelope,
    compare_replay_key_catalogs,
    protected_replay_corpus_scenario_ids,
    run_protected_replay_trend_window,
    validate_protected_replay_corpus_parity,
    write_deterministic_json,
)
from tests.helpers.protected_replay_registry import protected_replay_corpus
from tests.helpers.protected_replay_trend_movement import (
    BZ_RECURRENCE_MOVEMENT_FILENAME,
    BZ_WINDOW_SUMMARY_MD,
    COMPARISON_MODE_BASELINE_ESTABLISHMENT,
    COMPARISON_MODE_HISTORICAL,
    build_recurrence_snapshot,
    compare_recurrence_snapshots,
    recurrence_movement_summary_matches_lists,
    render_bz_protected_replay_trend_window_2_markdown,
    write_bz_recurrence_movement_artifact,
)
from tests.helpers.replay_observed_row_fixtures import synthetic_rerun_turn

REPO_ROOT = Path(__file__).resolve().parents[1]
BW_TREND_WINDOW = REPO_ROOT / "artifacts" / "golden_replay" / "trend_window"
BW_BASELINE_RUN = BW_TREND_WINDOW / "runs" / "run-000.json"
RECURRENCE_HISTORY = REPO_ROOT / "artifacts" / "golden_replay" / "bug_recurrence_history.json"
RECURRENCE_EVENT_LOG = REPO_ROOT / "artifacts" / "golden_replay" / "bug_recurrence_event_log.json"


def _raw_turn(**overrides: Any) -> dict[str, Any]:
    row = synthetic_rerun_turn(
        turn_index=overrides.pop("turn_index", 0),
        turn_id=overrides.pop("turn_id", "t01"),
        route_kind=overrides.pop("route_kind", "dialogue"),
        selected_speaker_id=overrides.pop("selected_speaker_id", "runner"),
        final_text=overrides.pop("final_text", "The runner answers."),
    )
    row.update(
        {
            "scenario_id": overrides.pop("scenario_id", "directed_npc_question"),
            "resolution_kind": overrides.pop("resolution_kind", "social"),
            "final_emitted_source": overrides.pop("final_emitted_source", "generated_candidate"),
            "final_text_hash": overrides.pop("final_text_hash", "hash-runner"),
            "post_gate_mutation_detected": overrides.pop("post_gate_mutation_detected", False),
            "final_emission_mutation_lineage": overrides.pop("final_emission_mutation_lineage", []),
            "sanitizer_lineage_changed_count": overrides.pop("sanitizer_lineage_changed_count", 0),
            "sanitizer_lineage_dropped_count": overrides.pop("sanitizer_lineage_dropped_count", 0),
            "opening_fallback_owner_bucket": overrides.pop("opening_fallback_owner_bucket", None),
            "sealed_fallback_owner_bucket": overrides.pop("sealed_fallback_owner_bucket", None),
            "trace": overrides.pop(
                "trace",
                {
                    "social_contract_trace": {"route_selected": "dialogue"},
                    "canonical_entry": {"target_actor_id": "runner"},
                },
            ),
        }
    )
    row.update(overrides)
    return row


def _envelope_from_turns(run_index: int, turns: list[dict[str, Any]]) -> dict[str, Any]:
    return build_run_envelope(run_index=run_index, observations=turns)


def _catalog_from_turns(run_index: int, turns: list[dict[str, Any]]) -> dict[str, Any]:
    return build_replay_key_catalog(_envelope_from_turns(run_index, turns))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _recurrence_row(
    *,
    owner_bucket: str = "speaker_drift",
    category: str = "speaker",
    field_path: str = "selected_speaker_id",
    investigate_first: str = "game/speaker.py",
    occurrence_count: int = 1,
    status: str = "active",
    owner: str | None = None,
    lifecycle_stage: str | None = None,
) -> dict[str, Any]:
    key = f"recurrence:v1:{owner_bucket}|{category}|{field_path}|{investigate_first}"
    row: dict[str, Any] = {
        "recurrence_key": key,
        "occurrence_count": occurrence_count,
        "status": status,
        "owner": owner or category,
        "latest_investigate_first": investigate_first,
        "categories": [category],
        "field_paths": [field_path],
    }
    if lifecycle_stage is not None:
        row["lifecycle_stage"] = lifecycle_stage
    return row


def _history_snapshot(*rows: dict[str, Any]) -> dict[str, Any]:
    return build_recurrence_snapshot(history={"recurrences": list(rows)})


def _snapshot_from_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_entries = sorted(entries, key=lambda row: str(row.get("recurrence_key") or ""))
    return {
        "available": True,
        "entries": sorted_entries,
        "keys_by_recurrence_key": {
            str(entry["recurrence_key"]): entry for entry in sorted_entries
        },
    }


def _entry(
    *,
    owner_bucket: str = "speaker_drift",
    category: str = "speaker",
    field_path: str = "selected_speaker_id",
    investigate_first: str = "game/speaker.py",
    occurrence_count: int = 2,
    recurrence_owner: str = "speaker",
    event_source: str = "protected_replay_failure",
    lifecycle_stage: str = "recurring",
) -> dict[str, Any]:
    key = f"recurrence:v1:{owner_bucket}|{category}|{field_path}|{investigate_first}"
    return {
        "recurrence_key": key,
        "occurrence_count": occurrence_count,
        "recurrence_status": "active",
        "lifecycle_stage": lifecycle_stage,
        "recurrence_owner": recurrence_owner,
        "investigate_first": investigate_first,
        "event_source": event_source,
        "category": category,
        "field_path": field_path,
        "subject_key": f"{category}|{field_path}",
    }


def test_bz_corpus_matches_bw() -> None:
    registry_ids = protected_replay_corpus_scenario_ids()
    assert len(registry_ids) == 6

    bw_manifest_path = BW_TREND_WINDOW / "manifest.json"
    assert bw_manifest_path.is_file()
    bw_manifest = json.loads(bw_manifest_path.read_text(encoding="utf-8"))
    bw_ids = bw_manifest["corpus_scenario_ids"]

    parity = validate_protected_replay_corpus_parity(bw_ids, list(registry_ids))
    assert parity["corpus_match"] is True
    assert parity["scenario_count"] == 6
    assert parity["baseline_scenario_ids"] == parity["current_scenario_ids"]
    assert parity["ordered_corpus_identity"] == "|".join(registry_ids)
    assert [entry.scenario_id for entry in protected_replay_corpus()] == list(registry_ids)


def test_replay_key_catalog_generation() -> None:
    turn = _raw_turn(scenario_id="directed_npc_question", turn_index=0, turn_id=None)
    catalog = _catalog_from_turns(0, [turn])

    assert catalog["run_id"] == "run-000"
    assert catalog["entry_count"] > 0
    assert len(catalog["entries"]) == catalog["entry_count"]
    keys = [entry["key"] for entry in catalog["entries"]]
    assert keys == sorted(keys)
    assert keys == keys[::-1][::-1]  # stable sort

    sample = catalog["entries"][0]
    assert set(sample) == {"key", "dimension", "field", "value", "contributing_identities"}
    assert sample["dimension"] in BZ_REPLAY_KEY_DIMENSIONS
    assert sample["contributing_identities"] == sorted(sample["contributing_identities"])


def test_new_key_classification() -> None:
    baseline_turn = _raw_turn(selected_speaker_id="runner")
    current_turn = _raw_turn(selected_speaker_id="guard")
    comparison = compare_replay_key_catalogs(
        _catalog_from_turns(0, [baseline_turn]),
        _catalog_from_turns(1, [current_turn]),
    )

    assert comparison["summary"]["new_key_count"] >= 1
    assert comparison["summary"]["retired_key_count"] >= 1
    assert comparison["summary"]["unchanged_key_count"] >= 1
    assert set(comparison["new_keys"]).isdisjoint(comparison["retired_keys"])
    assert set(comparison["unchanged_keys"]) <= set(comparison["active_keys"])


def test_retired_key_classification() -> None:
    baseline_turn = _raw_turn(route_kind="dialogue")
    current_turn = _raw_turn(
        route_kind="action",
        trace={"social_contract_trace": {"route_selected": "action"}},
    )
    comparison = compare_replay_key_catalogs(
        _catalog_from_turns(0, [baseline_turn]),
        _catalog_from_turns(1, [current_turn]),
    )

    assert comparison["summary"]["retired_key_count"] >= 1
    assert comparison["summary"]["new_key_count"] >= 1
    retired_route_keys = comparison["dimensions"]["route"]["retired_keys"]
    new_route_keys = comparison["dimensions"]["route"]["new_keys"]
    assert retired_route_keys
    assert new_route_keys
    assert set(retired_route_keys).isdisjoint(new_route_keys)


def test_unchanged_key_classification() -> None:
    turn = _raw_turn()
    baseline = _catalog_from_turns(0, [turn])
    current = _catalog_from_turns(1, [turn])
    comparison = compare_replay_key_catalogs(baseline, current)

    assert comparison["summary"]["unchanged_key_count"] == comparison["summary"]["active_key_count"]
    assert comparison["summary"]["new_key_count"] == 0
    assert comparison["summary"]["retired_key_count"] == 0
    assert set(comparison["unchanged_keys"]) == set(comparison["active_keys"])


def test_active_key_classification() -> None:
    baseline_turn = _raw_turn(selected_speaker_id="runner")
    current_turn = _raw_turn(selected_speaker_id="guard")
    current_catalog = _catalog_from_turns(1, [current_turn])
    comparison = compare_replay_key_catalogs(
        _catalog_from_turns(0, [baseline_turn]),
        current_catalog,
    )

    current_keys = {entry["key"] for entry in current_catalog["entries"]}
    assert set(comparison["active_keys"]) == current_keys
    assert comparison["summary"]["active_key_count"] == len(current_keys)


def test_field_state_distinction() -> None:
    absent_turn = _raw_turn()
    absent_turn.pop("route_kind", None)

    unavailable_turn = _raw_turn(unavailable=["route_kind"])

    null_turn = _raw_turn(route_kind=None)

    value_turn = _raw_turn(route_kind="dialogue")

    catalogs = [
        build_replay_key_catalog(_envelope_from_turns(index, [turn]))
        for index, turn in enumerate([absent_turn, unavailable_turn, null_turn, value_turn])
    ]
    route_kind_keys = {
        entry["key"]
        for catalog in catalogs
        for entry in catalog["entries"]
        if entry["dimension"] == "route" and entry["field"] == "route_kind"
    }
    assert len(route_kind_keys) == 4


def test_catalog_order_is_deterministic() -> None:
    turn_a = _raw_turn(scenario_id="directed_npc_question", turn_index=0, turn_id=None)
    turn_b = _raw_turn(scenario_id="directed_npc_question", turn_index=1, turn_id=None, selected_speaker_id="guard")

    forward = build_replay_key_catalog(_envelope_from_turns(0, [turn_a, turn_b]))
    reverse = build_replay_key_catalog(_envelope_from_turns(0, [turn_b, turn_a]))

    assert forward == reverse
    assert [entry["key"] for entry in forward["entries"]] == sorted(
        entry["key"] for entry in forward["entries"]
    )


def test_bz_artifacts_do_not_touch_bw_paths(tmp_path: Path) -> None:
    if not BW_BASELINE_RUN.is_file():
        pytest.skip("BW baseline run artifact is not present in this checkout")

    bw_files = sorted(
        path
        for path in BW_TREND_WINDOW.rglob("*")
        if path.is_file() and "_storage" not in path.parts
    )
    before = {path: _file_digest(path) for path in bw_files}

    bz_dir = tmp_path / "trend_window_2"
    report = run_protected_replay_trend_window(
        runs=2,
        out_dir=bz_dir,
        bz_replay_key_baseline_run=BW_BASELINE_RUN,
        bz_corpus_baseline_scenario_ids=list(protected_replay_corpus_scenario_ids()),
    )

    after = {path: _file_digest(path) for path in bw_files}
    assert before == after
    assert (bz_dir / BZ_REPLAY_KEY_MOVEMENT_FILENAME).is_file()
    assert report["bz_replay_key_movement"]["corpus_match"] is True


def test_recurrence_newly_recurring() -> None:
    baseline = _history_snapshot()
    current = _history_snapshot(
        _recurrence_row(occurrence_count=2, owner_bucket="fallback_drift", category="fallback")
    )
    result = compare_recurrence_snapshots(baseline, current)
    keys = [row["recurrence_key"] for row in result["movement"]["newly_recurring"]]
    assert len(keys) == 1
    assert result["summary"]["newly_recurring_count"] == 1


def test_recurrence_still_recurring() -> None:
    row = _recurrence_row(occurrence_count=3, category="route", field_path="route_kind")
    baseline = _history_snapshot(row)
    current = _history_snapshot({**row, "occurrence_count": 4})
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["still_recurring_count"] == 1
    assert result["movement"]["still_recurring"][0]["occurrence_count"] == 4


def test_recurrence_no_longer_recurring() -> None:
    row = _recurrence_row(occurrence_count=2, lifecycle_stage="recurring")
    baseline = _history_snapshot(row)
    current = _history_snapshot({**row, "occurrence_count": 1, "lifecycle_stage": "emerging"})
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["no_longer_recurring_count"] == 1


def test_recurrence_count_increased() -> None:
    row = _recurrence_row(occurrence_count=2)
    baseline = _history_snapshot(row)
    current = _history_snapshot({**row, "occurrence_count": 5})
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["count_increased_count"] == 1
    assert result["movement"]["count_increased"][0]["current_occurrence_count"] == 5


def test_recurrence_count_decreased() -> None:
    row = _recurrence_row(occurrence_count=4)
    baseline = _history_snapshot(row)
    current = _history_snapshot({**row, "occurrence_count": 2})
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["count_decreased_count"] == 1
    assert result["movement"]["count_decreased"][0]["baseline_occurrence_count"] == 4


def test_recurrence_owner_changed_by_subject() -> None:
    baseline = _snapshot_from_entries(
        [_entry(owner_bucket="speaker_drift", recurrence_owner="speaker")]
    )
    current = _snapshot_from_entries(
        [_entry(owner_bucket="projection_drift", recurrence_owner="projection")]
    )
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["owner_changed_count"] == 1
    assert result["movement"]["owner_changed"][0]["subject_key"] == "speaker|selected_speaker_id"


def test_recurrence_investigate_first_changed_by_subject() -> None:
    baseline = _snapshot_from_entries([_entry(investigate_first="game/a.py")])
    current = _snapshot_from_entries([_entry(investigate_first="game/b.py")])
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["investigate_first_changed_count"] == 1


def test_recurrence_event_source_changed_by_subject() -> None:
    baseline = _snapshot_from_entries([_entry(event_source="protected_replay_failure")])
    current = _snapshot_from_entries([_entry(event_source="unknown")])
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["event_source_changed_count"] == 1


def test_recurrence_ambiguous_subject_is_reported() -> None:
    baseline = _snapshot_from_entries(
        [
            _entry(owner_bucket="a", investigate_first="game/a.py"),
            _entry(owner_bucket="b", investigate_first="game/b.py"),
        ]
    )
    current = _snapshot_from_entries([_entry(owner_bucket="c")])
    result = compare_recurrence_snapshots(baseline, current)
    assert result["summary"]["ambiguous_subject_count"] == 1
    assert result["movement"]["ambiguous_subjects"][0]["subject_key"] == "speaker|selected_speaker_id"


def test_recurrence_baseline_establishment_mode_without_bw_snapshot(tmp_path: Path) -> None:
    report = write_bz_recurrence_movement_artifact(
        out_dir=tmp_path,
        baseline_path=None,
        current_path=RECURRENCE_HISTORY if RECURRENCE_HISTORY.is_file() else None,
        event_log_path=RECURRENCE_EVENT_LOG if RECURRENCE_EVENT_LOG.is_file() else None,
    )
    assert report["comparison_mode"] == COMPARISON_MODE_BASELINE_ESTABLISHMENT
    assert report["baseline_available"] is False
    assert report["current_available"] is RECURRENCE_HISTORY.is_file()
    assert report["summary"]["newly_recurring_count"] == 0
    assert report["summary"]["still_recurring_count"] == 0
    assert (tmp_path / BZ_RECURRENCE_MOVEMENT_FILENAME).is_file()


def test_recurrence_report_does_not_mutate_event_log(tmp_path: Path) -> None:
    if not RECURRENCE_EVENT_LOG.is_file():
        pytest.skip("recurrence event log artifact is not present in this checkout")

    before_original_log = _file_digest(RECURRENCE_EVENT_LOG)
    before_original_history = _file_digest(RECURRENCE_HISTORY) if RECURRENCE_HISTORY.is_file() else None

    copied_log = tmp_path / "bug_recurrence_event_log.json"
    copied_history = tmp_path / "bug_recurrence_history.json"
    shutil.copy2(RECURRENCE_EVENT_LOG, copied_log)
    if RECURRENCE_HISTORY.is_file():
        shutil.copy2(RECURRENCE_HISTORY, copied_history)

    before_log = _file_digest(copied_log)
    before_history = _file_digest(copied_history) if copied_history.is_file() else None

    write_bz_recurrence_movement_artifact(
        out_dir=tmp_path / "out",
        baseline_path=copied_history if copied_history.is_file() else None,
        current_path=copied_history if copied_history.is_file() else None,
        event_log_path=copied_log,
    )

    assert _file_digest(copied_log) == before_log
    if before_history is not None:
        assert _file_digest(copied_history) == before_history
    assert _file_digest(RECURRENCE_EVENT_LOG) == before_original_log
    if before_original_history is not None and RECURRENCE_HISTORY.is_file():
        assert _file_digest(RECURRENCE_HISTORY) == before_original_history


def test_recurrence_historical_snapshot_comparison_mode(tmp_path: Path) -> None:
    baseline_history = tmp_path / "baseline_history.json"
    current_history = tmp_path / "current_history.json"
    baseline_history.write_text(
        json.dumps({"recurrences": [_recurrence_row(occurrence_count=2)]}, indent=2),
        encoding="utf-8",
    )
    current_history.write_text(
        json.dumps(
            {"recurrences": [_recurrence_row(occurrence_count=2), _recurrence_row(category="route", field_path="route_kind", owner_bucket="route_drift", investigate_first="game/route.py", occurrence_count=3)]},
            indent=2,
        ),
        encoding="utf-8",
    )
    report = write_bz_recurrence_movement_artifact(
        out_dir=tmp_path / "out",
        baseline_path=baseline_history,
        current_path=current_history,
    )
    assert report["comparison_mode"] == COMPARISON_MODE_HISTORICAL
    assert report["baseline_available"] is True
    assert report["summary"]["newly_recurring_count"] >= 1


def test_bz_replay_key_movement_json_is_byte_stable_on_repeated_write(tmp_path: Path) -> None:
    turn = _raw_turn()
    baseline_catalog = build_replay_key_catalog(_envelope_from_turns(0, [turn]))
    current_catalog = build_replay_key_catalog(_envelope_from_turns(0, [turn]))
    corpus_ids = list(protected_replay_corpus_scenario_ids())
    corpus_parity = validate_protected_replay_corpus_parity(corpus_ids, corpus_ids)
    report = build_bz_replay_key_movement_report(
        baseline_run_path="artifacts/golden_replay/trend_window/runs/run-000.json",
        current_run_path="artifacts/golden_replay/trend_window_2/runs/run-000.json",
        baseline_catalog=baseline_catalog,
        current_catalog=current_catalog,
        corpus_parity=corpus_parity,
    )

    out_a = tmp_path / "a" / BZ_REPLAY_KEY_MOVEMENT_FILENAME
    out_b = tmp_path / "b" / BZ_REPLAY_KEY_MOVEMENT_FILENAME
    write_deterministic_json(out_a, report)
    write_deterministic_json(out_b, report)
    assert _file_digest(out_a) == _file_digest(out_b)


def test_bz_recurrence_movement_json_is_byte_stable_on_repeated_write(tmp_path: Path) -> None:
    baseline_history = tmp_path / "baseline_history.json"
    current_history = tmp_path / "current_history.json"
    payload = {"recurrences": [_recurrence_row(occurrence_count=2)]}
    baseline_history.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    current_history.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    out_a = tmp_path / "out-a"
    out_b = tmp_path / "out-b"
    write_bz_recurrence_movement_artifact(
        out_dir=out_a,
        baseline_path=baseline_history,
        current_path=current_history,
    )
    write_bz_recurrence_movement_artifact(
        out_dir=out_b,
        baseline_path=baseline_history,
        current_path=current_history,
    )
    assert _file_digest(out_a / BZ_RECURRENCE_MOVEMENT_FILENAME) == _file_digest(
        out_b / BZ_RECURRENCE_MOVEMENT_FILENAME
    )


def test_recurrence_movement_output_is_order_independent() -> None:
    row_a = _recurrence_row(category="route", field_path="route_kind", owner_bucket="route_drift", occurrence_count=2)
    row_b = _recurrence_row(category="speaker", field_path="selected_speaker_id", occurrence_count=3)
    baseline = _history_snapshot(row_a, row_b)
    baseline_reversed = build_recurrence_snapshot(history={"recurrences": [row_b, row_a]})
    current = _history_snapshot({**row_a, "occurrence_count": 4}, row_b)

    forward = compare_recurrence_snapshots(baseline, current)
    reverse = compare_recurrence_snapshots(baseline_reversed, current)
    assert forward == reverse


def test_recurrence_summary_counts_match_movement_list_lengths() -> None:
    baseline = _history_snapshot(_recurrence_row(occurrence_count=2))
    current = _history_snapshot(
        _recurrence_row(occurrence_count=2),
        _recurrence_row(category="route", field_path="route_kind", owner_bucket="route_drift", occurrence_count=3),
    )
    report = compare_recurrence_snapshots(baseline, current)
    assert recurrence_movement_summary_matches_lists(
        {"summary": report["summary"], "movement": report["movement"]}
    )


def test_replay_key_summary_counts_match_catalog_lists() -> None:
    turn_a = _raw_turn(scenario_id="directed_npc_question", turn_index=0, turn_id=None)
    turn_b = _raw_turn(scenario_id="directed_npc_question", turn_index=1, turn_id=None, selected_speaker_id="guard")
    baseline = _catalog_from_turns(0, [turn_a])
    current = _catalog_from_turns(1, [turn_a, turn_b])
    comparison = compare_replay_key_catalogs(baseline, current)

    assert comparison["summary"]["new_key_count"] == len(comparison["new_keys"])
    assert comparison["summary"]["retired_key_count"] == len(comparison["retired_keys"])
    assert comparison["summary"]["unchanged_key_count"] == len(comparison["unchanged_keys"])
    assert comparison["summary"]["active_key_count"] == len(comparison["active_keys"])
    assert comparison["new_keys"] == sorted(comparison["new_keys"])
    assert comparison["active_keys"] == sorted(comparison["active_keys"])


def test_bz_generation_does_not_write_bw_trend_window(tmp_path: Path) -> None:
    if not BW_BASELINE_RUN.is_file():
        pytest.skip("BW baseline run artifact is not present in this checkout")

    bw_files = sorted(
        path
        for path in BW_TREND_WINDOW.rglob("*")
        if path.is_file() and "_storage" not in path.parts
    )
    before = {path: _file_digest(path) for path in bw_files}

    run_protected_replay_trend_window(
        runs=2,
        out_dir=tmp_path / "trend_window_2",
        bz_replay_key_baseline_run=BW_BASELINE_RUN,
        bz_corpus_baseline_scenario_ids=list(protected_replay_corpus_scenario_ids()),
        write_bz_recurrence_movement=False,
    )

    after = {path: _file_digest(path) for path in bw_files}
    assert before == after


def test_protected_replay_corpus_ids_are_six_and_in_registry_order() -> None:
    registry_ids = [entry.scenario_id for entry in protected_replay_corpus()]
    corpus_ids = list(protected_replay_corpus_scenario_ids())
    assert len(corpus_ids) == 6
    assert corpus_ids == registry_ids


def test_bz_window_summary_markdown_is_deterministic() -> None:
    replay_report = {
        "corpus_match": True,
        "baseline": "artifacts/golden_replay/trend_window/runs/run-000.json",
        "current": "artifacts/golden_replay/trend_window_2/runs/run-000.json",
        "summary": {
            "active_key_count": 49,
            "new_key_count": 10,
            "retired_key_count": 0,
            "unchanged_key_count": 39,
        },
    }
    recurrence_report = {
        "comparison_mode": COMPARISON_MODE_BASELINE_ESTABLISHMENT,
        "baseline_available": False,
        "current_available": True,
        "current_path": "artifacts/golden_replay/bug_recurrence_history.json",
        "summary": {
            "newly_recurring_count": 0,
            "still_recurring_count": 0,
            "no_longer_recurring_count": 0,
            "count_increased_count": 0,
            "count_decreased_count": 0,
            "owner_changed_count": 0,
            "investigate_first_changed_count": 0,
            "event_source_changed_count": 0,
            "ambiguous_subject_count": 0,
        },
    }
    first = render_bz_protected_replay_trend_window_2_markdown(
        replay_key_movement=replay_report,
        recurrence_movement=recurrence_report,
    )
    second = render_bz_protected_replay_trend_window_2_markdown(
        replay_key_movement=replay_report,
        recurrence_movement=recurrence_report,
    )
    assert first == second
    assert "baseline_establishment" in first


def test_bz_full_window_writes_summary_markdown(tmp_path: Path) -> None:
    if not BW_BASELINE_RUN.is_file():
        pytest.skip("BW baseline run artifact is not present in this checkout")

    out_dir = tmp_path / "trend_window_2"
    run_protected_replay_trend_window(
        runs=2,
        out_dir=out_dir,
        bz_replay_key_baseline_run=BW_BASELINE_RUN,
        bz_corpus_baseline_scenario_ids=list(protected_replay_corpus_scenario_ids()),
        write_bz_recurrence_movement=True,
        bz_recurrence_current=None,
    )
    assert (out_dir / BZ_WINDOW_SUMMARY_MD).is_file()

