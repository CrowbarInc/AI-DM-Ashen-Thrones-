"""BY2 — protected replay semantic mutation measurement tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.golden_replay_trend import (
    execute_protected_replay_corpus,
    protected_replay_scenario_specs,
)
from tests.helpers.protected_replay_registry import protected_replay_corpus
from tests.helpers.protected_semantic_mutation_measurement import (
    BY2_REPORT_SCHEMA_VERSION,
    assert_probe_non_interference,
    build_protected_semantic_mutation_report,
    execute_protected_replay_corpus_with_semantic_mutation_probe,
    identify_attribution_gaps,
    measure_protected_replay_semantic_mutation_corpus,
    render_protected_semantic_mutation_report_markdown,
    turn_measurement_row,
    write_protected_semantic_mutation_reports,
)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
BY2_ARTIFACTS = REPO_ROOT / "artifacts" / "by2"


def test_by2_probe_runs_over_protected_replay_corpus(tmp_path, monkeypatch) -> None:
    observations, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
    )
    assert len(observations) == sum(len(spec.turns) for spec in protected_replay_scenario_specs())
    assert len(protected_replay_corpus()) == 6
    for turn in observations:
        assert "final_text_hash" in turn
        assert "semantic_mutation_trace_complete" in turn
        assert "semantic_mutation_changed_count" in turn


def test_by2_probe_does_not_affect_final_output(tmp_path, monkeypatch) -> None:
    baseline = execute_protected_replay_corpus(storage_root=tmp_path / "baseline", monkeypatch=monkeypatch)
    probed, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path / "probed",
        monkeypatch=monkeypatch,
    )
    assert_probe_non_interference(baseline, probed)


def test_by2_corpus_report_schema_is_stable(tmp_path, monkeypatch) -> None:
    probed, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
    )
    rows = [turn_measurement_row(turn) for turn in probed]
    report = build_protected_semantic_mutation_report(probed, turn_rows=rows)

    assert report["schema_version"] == BY2_REPORT_SCHEMA_VERSION
    assert report["corpus"] == "protected_replay"
    assert set(report["summary"]) >= {
        "total_turns",
        "mutated_turns",
        "attributable_first_mutations",
        "first_source_coverage_rate",
        "unknown_first_source_count",
        "bucket_distribution",
        "top_mutation_sources",
        "semantic_mutation_risk_mean",
        "semantic_mutation_risk_max",
        "representative_high_risk_turns",
    }
    assert isinstance(report["attribution_gaps"], list)
    assert len(report["turns"]) == len(probed)

    # Round-trip JSON stability
    encoded = json.dumps(report, sort_keys=True)
    decoded = json.loads(encoded)
    assert decoded["schema_version"] == BY2_REPORT_SCHEMA_VERSION


def test_by2_unknown_attribution_cases_are_surfaced(tmp_path, monkeypatch) -> None:
    probed, _records = execute_protected_replay_corpus_with_semantic_mutation_probe(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
    )
    rows = [turn_measurement_row(turn) for turn in probed]
    gaps = identify_attribution_gaps(probed, turn_rows=rows)

    for gap in gaps:
        assert gap.get("turn_identity")
        assert gap.get("missing_checkpoint")
        assert gap.get("recommended_by3_instrumentation_target") is not None

    report = build_protected_semantic_mutation_report(probed, turn_rows=rows)
    assert report["attribution_gaps"] == gaps


def test_by2_writes_corpus_artifacts(tmp_path, monkeypatch) -> None:
    result = measure_protected_replay_semantic_mutation_corpus(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
        out_dir=tmp_path / "by2_out",
    )
    written = result["written_artifacts"]
    json_path = Path(written["json"])
    md_path = Path(written["markdown"])
    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == BY2_REPORT_SCHEMA_VERSION
    assert "Protected Semantic Mutation Report (BY2)" in md_path.read_text(encoding="utf-8")


def test_by2_generate_repo_corpus_report_artifacts(tmp_path, monkeypatch) -> None:
    """Refresh artifacts/by2 reports used as BY2 deliverables."""
    result = measure_protected_replay_semantic_mutation_corpus(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
        out_dir=BY2_ARTIFACTS,
    )
    report = result["report"]
    summary = report["summary"]
    assert summary["total_turns"] >= 6
    assert (BY2_ARTIFACTS / "protected_semantic_mutation_report.json").is_file()
    assert (BY2_ARTIFACTS / "protected_semantic_mutation_report.md").is_file()
    markdown = render_protected_semantic_mutation_report_markdown(report)
    assert "first-source coverage rate" in markdown
