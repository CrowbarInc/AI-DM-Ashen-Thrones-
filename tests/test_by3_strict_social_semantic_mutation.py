"""BY3 — strict-social hidden mutation boundary coverage tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.golden_replay_trend import execute_protected_replay_corpus
from tests.helpers.protected_semantic_mutation_measurement import (
    BY2_BASELINE_GAP_TURN,
    BY3_REPORT_SCHEMA_VERSION,
    assert_probe_non_interference,
    build_strict_social_semantic_mutation_report,
    execute_protected_replay_corpus_with_semantic_mutation_probe,
    identify_attribution_gaps,
    measure_protected_replay_semantic_mutation_corpus,
    measure_strict_social_semantic_mutation_corpus,
    protected_field_values,
    turn_measurement_row,
    write_strict_social_semantic_mutation_reports,
)
from tests.helpers.semantic_mutation_attribution import (
    CHECKPOINT_NORMALIZED_SOCIAL_CANDIDATE,
    CHECKPOINT_WRITER_RAW_CANDIDATE,
)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
BY2_ARTIFACTS = REPO_ROOT / "artifacts" / "by2"
BY3_ARTIFACTS = REPO_ROOT / "artifacts" / "by3"


def _load_by2_baseline() -> dict | None:
    path = BY2_ARTIFACTS / "protected_semantic_mutation_report.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def test_by3_strict_social_hidden_mutation_detected(tmp_path, monkeypatch) -> None:
    probed, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
    )
    rows = [turn_measurement_row(turn) for turn in probed]
    target = next(row for row in rows if row["turn_identity"] == BY2_BASELINE_GAP_TURN)

    assert target["post_gate_mutation_detected"] is True
    assert int(target["semantic_mutation_changed_count"] or 0) > 0
    assert target["trace_continuity"] is True
    assert target["first_semantic_mutation_checkpoint_id"] in {
        CHECKPOINT_NORMALIZED_SOCIAL_CANDIDATE,
        "speaker_contract_enforcement",
    }
    assert target["first_semantic_mutation_bucket"] in {"fallback", "repair"}


def test_by3_wrong_speaker_fixture_has_attributable_trace(tmp_path, monkeypatch) -> None:
    probed, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
    )
    rows = [turn_measurement_row(turn) for turn in probed]
    gaps = identify_attribution_gaps(probed, turn_rows=rows)

    target_gaps = [gap for gap in gaps if gap.get("turn_identity") == BY2_BASELINE_GAP_TURN]
    assert target_gaps == []

    target = next(row for row in rows if row["turn_identity"] == BY2_BASELINE_GAP_TURN)
    assert str(target.get("first_semantic_mutation_source") or "").strip()
    assert target.get("first_semantic_mutation_bucket") != "unknown"


def test_by3_probe_does_not_affect_final_output_or_protected_fields(tmp_path, monkeypatch) -> None:
    baseline = execute_protected_replay_corpus(storage_root=tmp_path / "baseline", monkeypatch=monkeypatch)
    probed, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path / "probed",
        monkeypatch=monkeypatch,
    )
    assert_probe_non_interference(baseline, probed)

    for base, probe in zip(baseline, probed):
        assert protected_field_values(base) == protected_field_values(probe)


def test_by3_report_schema_and_gap_closure(tmp_path, monkeypatch) -> None:
    probed, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
    )
    rows = [turn_measurement_row(turn) for turn in probed]
    report = build_strict_social_semantic_mutation_report(
        probed,
        turn_rows=rows,
        by2_baseline=_load_by2_baseline(),
    )

    assert report["schema_version"] == BY3_REPORT_SCHEMA_VERSION
    coverage = report["before_after_coverage"]
    assert coverage["target_turn"] == BY2_BASELINE_GAP_TURN
    assert coverage["gap_closed"] is True
    assert int(coverage["before_by2"]["semantic_mutation_changed_count"] or 0) == 0
    assert coverage["before_by2"]["trace_continuity"] is False
    assert int(coverage["after_by3"]["semantic_mutation_changed_count"] or 0) > 0
    assert coverage["after_by3"]["trace_continuity"] is True


def test_by3_writer_raw_checkpoint_present_on_strict_social_turn(tmp_path, monkeypatch) -> None:
    from tests.helpers.semantic_mutation_attribution import new_trace_collector
    from tests.helpers.golden_replay_trend import protected_replay_scenario_specs
    from tests.helpers.protected_semantic_mutation_measurement import (
        _run_scenario_spec_with_semantic_probe,
        install_semantic_mutation_probe_session,
    )

    spec = next(s for s in protected_replay_scenario_specs() if s.scenario_id == "wrong_speaker_strict_social_emission")
    collector = new_trace_collector()
    phase = install_semantic_mutation_probe_session(monkeypatch, collector)
    _run_scenario_spec_with_semantic_probe(
        spec,
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
        collector=collector,
        phase=phase,
    )

    checkpoint_ids = {entry.checkpoint_id for entry in collector.entries}
    assert CHECKPOINT_WRITER_RAW_CANDIDATE in checkpoint_ids
    assert CHECKPOINT_NORMALIZED_SOCIAL_CANDIDATE in checkpoint_ids


def test_by3_generate_repo_artifacts(tmp_path, monkeypatch) -> None:
    """Refresh artifacts/by2 and artifacts/by3 deliverables."""
    by2_result = measure_protected_replay_semantic_mutation_corpus(
        storage_root=tmp_path / "by2_run",
        monkeypatch=monkeypatch,
        out_dir=BY2_ARTIFACTS,
    )
    by2_summary = by2_result["report"]["summary"]
    assert by2_summary["unknown_first_source_count"] == 0
    assert by2_summary["first_source_coverage_rate"] == 1.0

    by3_result = measure_strict_social_semantic_mutation_corpus(
        storage_root=tmp_path / "by3_run",
        monkeypatch=monkeypatch,
        out_dir=BY3_ARTIFACTS,
        by2_baseline=_load_by2_baseline(),
    )
    by3_report = by3_result["by3_report"]
    assert by3_report["before_after_coverage"]["gap_closed"] is True
    assert (BY3_ARTIFACTS / "strict_social_semantic_mutation_report.json").is_file()
    assert (BY3_ARTIFACTS / "strict_social_semantic_mutation_report.md").is_file()

    gaps = by3_report.get("attribution_gaps")
    assert isinstance(gaps, list)
    assert not any(gap.get("turn_identity") == BY2_BASELINE_GAP_TURN for gap in gaps)
