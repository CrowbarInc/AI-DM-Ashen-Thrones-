"""Golden replay trend-window harness tests (BW2/BW3/BW4)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.golden_replay_trend import (
    ADVISORY_GUARDRAIL_FIELD,
    BW_DIMENSION_FINAL_TEXT,
    BW_DIMENSION_MUTATION,
    BW_DIMENSION_OWNER,
    BW_DIMENSION_ROUTE,
    BW_DIMENSION_SOURCE,
    BW_DIMENSION_SPEAKER,
    GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL,
    GOLDEN_TRANSCRIPT_DRIFT_HISTORY_MD,
    GUARDRAIL_STATUS_PASS,
    GUARDRAIL_STATUS_WARN,
    HISTORY_FORBIDDEN_EQUALITY_KEYS,
    append_golden_transcript_drift_history,
    apply_guardrail_to_drift_report,
    build_golden_transcript_drift_report,
    build_run_envelope,
    build_trend_history_row,
    classify_history_trend_direction,
    compare_trend_runs,
    default_guardrail_thresholds,
    evaluate_drift_guardrails,
    execute_protected_replay_corpus,
    load_guardrail_thresholds,
    normalize_trend_observation,
    read_trend_history_rows,
    render_golden_transcript_drift_history_markdown,
    run_protected_replay_trend_window,
    turn_identity_key,
)
from tests.helpers.replay_observed_row_fixtures import synthetic_rerun_turn


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


def _sample_drift_report(*, drift_count: int = 0, aligned: int = 8) -> dict[str, Any]:
    comparison = {
        "baseline_run_id": "run-000",
        "current_run_id": "run-001",
        "golden_transcript_drift_count": drift_count,
        "identity_alignment": {
            "aligned_count": aligned,
            "missing_in_current": [],
            "missing_in_baseline": [],
        },
        "dimension_summary": {
            BW_DIMENSION_ROUTE: {"drift_count": drift_count, "affected_identities": []},
            BW_DIMENSION_SPEAKER: {"drift_count": 0, "affected_identities": []},
            BW_DIMENSION_SOURCE: {"drift_count": 0, "affected_identities": []},
            BW_DIMENSION_OWNER: {"drift_count": 0, "affected_identities": []},
            BW_DIMENSION_MUTATION: {"drift_count": 0, "affected_identities": []},
            BW_DIMENSION_FINAL_TEXT: {"drift_count": 0, "affected_identities": []},
        },
    }
    return apply_guardrail_to_drift_report(
        build_golden_transcript_drift_report(
            run_envelopes=[{"run_id": "run-000"}, {"run_id": "run-001"}],
            comparisons=[comparison],
        )
    )


def _zero_guardrail_metrics(**overrides: int) -> dict[str, int]:
    metrics = {
        "run_count": 2,
        "aligned_identity_count": 8,
        "golden_transcript_drift_count": 0,
        "route_drift_count": 0,
        "speaker_drift_count": 0,
        "source_drift_count": 0,
        "owner_drift_count": 0,
        "mutation_drift_count": 0,
        "final_text_hash_drift_count": 0,
        "missing_identity_count": 0,
        "extra_identity_count": 0,
    }
    metrics.update(overrides)
    return metrics


def test_two_run_zero_drift_integration(tmp_path: Path) -> None:
    monkeypatch = pytest.MonkeyPatch()
    try:
        first = execute_protected_replay_corpus(storage_root=tmp_path / "run-0", monkeypatch=monkeypatch)
        second = execute_protected_replay_corpus(storage_root=tmp_path / "run-1", monkeypatch=monkeypatch)
    finally:
        monkeypatch.undo()

    comparison = compare_trend_runs(
        _envelope_from_turns(0, first),
        _envelope_from_turns(1, second),
    )
    assert comparison["golden_transcript_drift_count"] == 0
    assert comparison["identity_alignment"]["missing_in_current"] == []
    assert comparison["identity_alignment"]["missing_in_baseline"] == []
    assert comparison["identity_alignment"]["aligned_count"] == 8


def test_synthetic_route_drift() -> None:
    baseline = _raw_turn(scenario_id="directed_npc_question", turn_index=0, turn_id=None)
    current = _raw_turn(
        scenario_id="directed_npc_question",
        turn_index=0,
        turn_id=None,
        route_kind="action",
        trace={"social_contract_trace": {"route_selected": "action"}},
    )
    comparison = compare_trend_runs(_envelope_from_turns(0, [baseline]), _envelope_from_turns(1, [current]))
    assert comparison["golden_transcript_drift_count"] == 1
    assert comparison["dimension_summary"][BW_DIMENSION_ROUTE]["drift_count"] == 1


def test_synthetic_speaker_drift() -> None:
    baseline = _raw_turn(selected_speaker_id="runner")
    current = _raw_turn(selected_speaker_id="guard")
    comparison = compare_trend_runs(_envelope_from_turns(0, [baseline]), _envelope_from_turns(1, [current]))
    assert comparison["dimension_summary"][BW_DIMENSION_SPEAKER]["drift_count"] == 1


def test_synthetic_source_drift() -> None:
    baseline = _raw_turn(final_emitted_source="generated_candidate")
    current = _raw_turn(final_emitted_source="global_scene_fallback")
    comparison = compare_trend_runs(_envelope_from_turns(0, [baseline]), _envelope_from_turns(1, [current]))
    assert comparison["dimension_summary"][BW_DIMENSION_SOURCE]["drift_count"] == 1


def test_synthetic_owner_bucket_drift() -> None:
    baseline = _raw_turn(sealed_fallback_owner_bucket="upstream_prepared_emission")
    current = _raw_turn(sealed_fallback_owner_bucket="compatibility_local")
    comparison = compare_trend_runs(_envelope_from_turns(0, [baseline]), _envelope_from_turns(1, [current]))
    assert comparison["dimension_summary"][BW_DIMENSION_OWNER]["drift_count"] == 1


def test_synthetic_mutation_drift() -> None:
    baseline = _raw_turn(post_gate_mutation_detected=False, sanitizer_lineage_changed_count=0)
    current = _raw_turn(
        post_gate_mutation_detected=True,
        sanitizer_lineage_changed_count=2,
        runtime_lineage_events=[
            make_runtime_lineage_event(
                event_kind="gate_outcome",
                stage="gate",
                owner="game.final_emission_gate",
                mutation_kind="repair_only_mutation",
            )
        ],
    )
    comparison = compare_trend_runs(_envelope_from_turns(0, [baseline]), _envelope_from_turns(1, [current]))
    assert comparison["dimension_summary"][BW_DIMENSION_MUTATION]["drift_count"] == 1


def test_synthetic_final_text_hash_drift_is_advisory() -> None:
    baseline = _raw_turn(final_text_hash="hash-a")
    current = _raw_turn(final_text_hash="hash-b")
    comparison = compare_trend_runs(_envelope_from_turns(0, [baseline]), _envelope_from_turns(1, [current]))
    assert comparison["dimension_summary"][BW_DIMENSION_FINAL_TEXT]["drift_count"] == 1


def test_missing_identity_handling() -> None:
    baseline = _raw_turn(scenario_id="directed_npc_question", turn_index=0, turn_id=None)
    current = _raw_turn(scenario_id="directed_npc_question", turn_index=1, turn_id=None)
    comparison = compare_trend_runs(_envelope_from_turns(0, [baseline]), _envelope_from_turns(1, [current]))
    assert comparison["identity_alignment"]["aligned_count"] == 0
    assert comparison["identity_alignment"]["missing_in_current"] == [turn_identity_key(baseline)]
    assert comparison["identity_alignment"]["missing_in_baseline"] == [turn_identity_key(current)]
    assert comparison["golden_transcript_drift_count"] == 0


def test_reordered_identity_handling() -> None:
    turn_a = _raw_turn(scenario_id="directed_npc_question", turn_index=0, turn_id=None, selected_speaker_id="runner")
    turn_b = _raw_turn(scenario_id="directed_npc_question", turn_index=1, turn_id=None, selected_speaker_id="guard")
    comparison = compare_trend_runs(
        _envelope_from_turns(0, [turn_a, turn_b]),
        _envelope_from_turns(1, [turn_b, turn_a]),
    )
    assert comparison["identity_alignment"]["aligned_count"] == 2
    assert comparison["golden_transcript_drift_count"] == 0


def test_turn_identity_key_prefers_turn_id() -> None:
    turn = _raw_turn(scenario_id="scenario", turn_index=0, turn_id="turn-abc")
    assert turn_identity_key(turn) == "scenario|id:turn-abc"
    normalized = normalize_trend_observation(turn)
    assert normalized["identity"] == "scenario|id:turn-abc"


def test_run_protected_replay_trend_window_writes_artifacts(tmp_path: Path) -> None:
    report = run_protected_replay_trend_window(runs=2, out_dir=tmp_path)
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "runs" / "run-000.json").is_file()
    assert (tmp_path / "runs" / "run-001.json").is_file()
    assert (tmp_path / "comparisons" / "run-001-vs-run-000.json").is_file()
    assert (tmp_path / "golden_transcript_drift.json").is_file()
    assert (tmp_path / "golden_transcript_drift.md").is_file()
    assert report["golden_transcript_drift_count"] == 0


def test_first_history_write_creates_jsonl_and_markdown(tmp_path: Path) -> None:
    report = _sample_drift_report()
    row = append_golden_transcript_drift_history(out_dir=tmp_path, drift_report=report)

    jsonl_path = tmp_path / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL
    md_path = tmp_path / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_MD
    assert jsonl_path.is_file()
    assert md_path.is_file()
    assert row["sequence_id"] == 1
    assert row["window_id"] == "window-001"
    assert row["report_only"] is True
    assert "Latest Window" in md_path.read_text(encoding="utf-8")


def test_second_history_write_appends_without_overwriting(tmp_path: Path) -> None:
    append_golden_transcript_drift_history(out_dir=tmp_path, drift_report=_sample_drift_report())
    append_golden_transcript_drift_history(out_dir=tmp_path, drift_report=_sample_drift_report(drift_count=1))

    rows = read_trend_history_rows(tmp_path / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL)
    assert len(rows) == 2
    assert rows[0]["sequence_id"] == 1
    assert rows[1]["sequence_id"] == 2
    assert rows[0]["golden_transcript_drift_count"] == 0
    assert rows[1]["golden_transcript_drift_count"] == 1

    raw_lines = (tmp_path / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL).read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 2


def test_compute_history_delta_works() -> None:
    from tests.helpers.golden_replay_trend import compute_history_delta

    previous = build_trend_history_row(drift_report=_sample_drift_report(), sequence_id=1)
    current = build_trend_history_row(drift_report=_sample_drift_report(drift_count=2), sequence_id=2)
    delta = compute_history_delta(current, previous)
    assert delta["golden_transcript_drift_count"] == 2
    assert delta["route_drift_count"] == 2


def test_history_trend_direction_classification() -> None:
    stable_prev = build_trend_history_row(drift_report=_sample_drift_report(drift_count=1), sequence_id=1)
    stable_cur = build_trend_history_row(drift_report=_sample_drift_report(drift_count=1), sequence_id=2)
    improved_cur = build_trend_history_row(drift_report=_sample_drift_report(drift_count=0), sequence_id=3)
    worsened_cur = build_trend_history_row(drift_report=_sample_drift_report(drift_count=3), sequence_id=4)

    assert classify_history_trend_direction(stable_cur, stable_prev) == "stable"
    assert classify_history_trend_direction(improved_cur, stable_prev) == "improved"
    assert classify_history_trend_direction(worsened_cur, stable_prev) == "worsened"


def test_history_rows_do_not_include_timestamps_in_equality_material() -> None:
    row = build_trend_history_row(drift_report=_sample_drift_report(), sequence_id=1)
    assert HISTORY_FORBIDDEN_EQUALITY_KEYS.isdisjoint(row)
    encoded = json.dumps(row, sort_keys=True)
    assert "timestamp" not in encoded.lower()
    markdown = render_golden_transcript_drift_history_markdown([row])
    assert "timestamp" not in markdown.lower()


def test_run_protected_replay_trend_window_append_history(tmp_path: Path) -> None:
    run_protected_replay_trend_window(runs=2, out_dir=tmp_path, append_history=True)
    assert (tmp_path / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL).is_file()
    assert (tmp_path / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_MD).is_file()
    rows = read_trend_history_rows(tmp_path / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL)
    assert len(rows) == 1
    assert rows[0]["golden_transcript_drift_count"] == 0
    assert rows[0]["guardrail"]["status"] == GUARDRAIL_STATUS_PASS


def test_zero_drift_guardrail_returns_pass() -> None:
    report = _sample_drift_report()
    guardrail = report["guardrail"]
    assert guardrail["status"] == GUARDRAIL_STATUS_PASS
    assert guardrail["report_only"] is True
    assert guardrail["exceeded_fields"] == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("route_drift_count", 1),
        ("speaker_drift_count", 1),
        ("source_drift_count", 1),
        ("owner_drift_count", 1),
        ("mutation_drift_count", 1),
    ],
)
def test_dimension_drift_returns_warn(field: str, value: int) -> None:
    guardrail = evaluate_drift_guardrails(
        metrics=_zero_guardrail_metrics(**{field: value}),
        thresholds=default_guardrail_thresholds(),
    )
    assert guardrail["status"] == GUARDRAIL_STATUS_WARN
    assert any(row["field"] == field for row in guardrail["exceeded_fields"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("missing_identity_count", 1),
        ("extra_identity_count", 1),
    ],
)
def test_identity_mismatch_returns_warn(field: str, value: int) -> None:
    guardrail = evaluate_drift_guardrails(
        metrics=_zero_guardrail_metrics(**{field: value}),
        thresholds=default_guardrail_thresholds(),
    )
    assert guardrail["status"] == GUARDRAIL_STATUS_WARN
    assert any(row["field"] == field for row in guardrail["exceeded_fields"])


def test_final_text_hash_drift_is_advisory_only_by_default() -> None:
    guardrail = evaluate_drift_guardrails(
        metrics=_zero_guardrail_metrics(final_text_hash_drift_count=2),
        thresholds=default_guardrail_thresholds(),
    )
    assert guardrail["status"] == GUARDRAIL_STATUS_PASS
    assert guardrail["advisory_exceeded_fields"][0]["field"] == ADVISORY_GUARDRAIL_FIELD


def test_final_text_hash_drift_can_warn_when_explicitly_configured() -> None:
    thresholds = default_guardrail_thresholds()
    thresholds[ADVISORY_GUARDRAIL_FIELD] = 0
    guardrail = evaluate_drift_guardrails(
        metrics=_zero_guardrail_metrics(final_text_hash_drift_count=1),
        thresholds=thresholds,
    )
    assert guardrail["status"] == GUARDRAIL_STATUS_WARN
    assert any(row["field"] == ADVISORY_GUARDRAIL_FIELD for row in guardrail["exceeded_fields"])


def test_history_rows_preserve_guardrail_status() -> None:
    report = _sample_drift_report(drift_count=1)
    row = build_trend_history_row(drift_report=report, sequence_id=1)
    assert row["guardrail"]["status"] == GUARDRAIL_STATUS_WARN
    assert row["guardrail"]["report_only"] is True


def test_load_guardrail_thresholds_rejects_invalid_file(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_guardrail_thresholds(bad_path)


def test_cli_exits_successfully_on_guardrail_warn(tmp_path: Path) -> None:
    thresholds_path = tmp_path / "thresholds.json"
    thresholds_path.write_text(json.dumps({"route_drift_count": 0}), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "tools/run_protected_replay_trend.py",
            "--runs",
            "2",
            "--out-dir",
            str(tmp_path / "trend"),
            "--thresholds",
            str(thresholds_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((tmp_path / "trend" / "golden_transcript_drift.json").read_text(encoding="utf-8"))
    assert report["guardrail"]["status"] in {GUARDRAIL_STATUS_PASS, GUARDRAIL_STATUS_WARN}
