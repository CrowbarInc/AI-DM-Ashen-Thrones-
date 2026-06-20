"""BR1 attribution completeness repository metric validation."""
from __future__ import annotations

from tests.helpers.attribution_completeness_metric import (
    build_attribution_completeness_report,
    build_field_coverage_report,
    build_path_coverage_report,
    render_attribution_completeness_report_md,
    write_attribution_completeness_report,
)
from tests.helpers.attribution_contract import REPLACEMENT_PATHS, REQUIRED_ATTRIBUTION_FIELDS
from tests.helpers.replacement_attribution_inventory import build_baseline_attribution_corpus


def test_attribution_completeness_report_generation(tmp_path):
    output = tmp_path / "attribution_completeness_report.md"
    report, markdown = write_attribution_completeness_report(output)
    assert output.exists()
    assert report["schema_version"] == 1
    assert "Attribution Completeness Report" in markdown
    assert "Contract Integration (BS3)" in markdown
    assert "Field Coverage" in markdown
    assert "Path Coverage" in markdown
    assert "Risk Summary" in markdown


def test_attribution_completeness_percentages_are_deterministic():
    records = build_baseline_attribution_corpus()
    first = build_attribution_completeness_report(records=records)
    second = build_attribution_completeness_report(records=records)
    assert first == second
    rendered = render_attribution_completeness_report_md(first)
    assert rendered == render_attribution_completeness_report_md(second)


def test_path_totals_reconcile_with_corpus():
    records = build_baseline_attribution_corpus()
    report = build_attribution_completeness_report(records=records)
    path_total = sum(stats["total"] for stats in report["path_coverage"].values())
    assert path_total == report["overall"]["current"]["total_records"]
    assert set(report["path_coverage"]) == set(REPLACEMENT_PATHS)


def test_field_coverage_reconciles_with_missing_fields():
    records = build_baseline_attribution_corpus()
    field_coverage = build_field_coverage_report(records)
    total = len(records)
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        stats = field_coverage[field]
        assert stats["present"] + stats["missing"] == total
        assert stats["strict_present"] <= stats["present"]
        assert stats["coverage_pct"] == round(100.0 * stats["present"] / total, 2)


def test_path_coverage_reconciles_with_completeness():
    records = build_baseline_attribution_corpus()
    path_coverage = build_path_coverage_report(records)
    resolved_complete = sum(stats["resolved_complete"] for stats in path_coverage.values())
    assert resolved_complete == sum(
        1 for record in records if not record.get("missing_fields")
    )
