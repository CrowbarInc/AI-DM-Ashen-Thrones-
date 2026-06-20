"""BRL1 bug-fix locality repository metric validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.bug_fix_locality_metric import (
    BRL1_BASELINE_LOCALITY,
    CATEGORY_BUG_FIX,
    CATEGORY_REFACTOR,
    _distribution_stats_for_category,
    _percentile,
    build_bug_fix_locality_report,
    classify_changed_path,
    load_commit_classification_rows,
    path_cluster,
    render_bug_fix_locality_report_md,
    write_bug_fix_locality_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "docs" / "reports" / "BR_commit_classification.csv"


def test_commit_classification_loading():
    rows = load_commit_classification_rows(CSV_PATH)
    assert len(rows) == 235
    assert rows[0].short_sha
    assert rows[0].category
    assert rows[0].files_touched_count >= 0


def test_percentile_calculation_is_deterministic():
    values = [7, 9, 16, 52, 216, 538]
    assert _percentile(values, 75) == 175.0
    assert _percentile(values, 90) == 377.0
    assert _percentile([9], 50) == 9.0


def test_path_classification_and_cluster_helpers():
    assert classify_changed_path("tests/test_foo.py") == "test"
    assert classify_changed_path("docs/reports/foo.md") == "docs_tooling"
    assert classify_changed_path("game/final_emission_meta.py") == "production"
    assert path_cluster("game/final_emission_meta.py") == "game/final_emission_meta.py"
    assert path_cluster("game/final_emission/meta.py") == "game/final_emission"


def test_bug_fix_locality_metrics_match_baseline_snapshot():
    rows = load_commit_classification_rows(CSV_PATH)
    current_bug_fix = _distribution_stats_for_category(rows, CATEGORY_BUG_FIX)
    baseline_bug_fix = BRL1_BASELINE_LOCALITY[CATEGORY_BUG_FIX]
    assert current_bug_fix["commit_count"] == baseline_bug_fix["commit_count"]
    assert current_bug_fix["median_files_touched"] == baseline_bug_fix["median_files_touched"]
    assert current_bug_fix["p75_files_touched"] == baseline_bug_fix["p75_files_touched"]
    assert current_bug_fix["p90_files_touched"] == baseline_bug_fix["p90_files_touched"]
    assert current_bug_fix["max_files_touched"] == baseline_bug_fix["max_files_touched"]


def test_metric_generation_is_deterministic():
    first = build_bug_fix_locality_report(csv_path=CSV_PATH, repo_root=REPO_ROOT)
    second = build_bug_fix_locality_report(csv_path=CSV_PATH, repo_root=REPO_ROOT)
    assert first == second
    rendered = render_bug_fix_locality_report_md(first)
    assert rendered == render_bug_fix_locality_report_md(second)


def test_bug_fix_locality_report_generation(tmp_path):
    output = tmp_path / "bug_fix_locality_report.md"
    report, markdown = write_bug_fix_locality_report(
        output,
        csv_path=CSV_PATH,
        repo_root=REPO_ROOT,
    )
    assert output.exists()
    assert report["schema_version"] == 1
    assert "Bug-Fix Locality Report" in markdown
    assert "Refactor Locality" in markdown
    assert "Governance Locality" in markdown
    assert "Feature Locality" in markdown
    assert "Repository Economics Summary" in markdown
    assert "Hotspot Reporting" in markdown
    assert report["current"][CATEGORY_REFACTOR]["median_files_touched"] == 16.0


def test_report_without_hotspots_uses_csv_only(tmp_path):
    report = build_bug_fix_locality_report(
        csv_path=CSV_PATH,
        repo_root=REPO_ROOT,
        include_hotspots=False,
    )
    assert "hotspots" not in report
    assert report["current"][CATEGORY_BUG_FIX]["locality_score"] == pytest.approx(11.11)


def test_fixture_csv_supports_classification_loading(tmp_path):
    fixture = tmp_path / "classification.csv"
    fixture.write_text(
        "short_sha,date,subject,category,files_touched_count,"
        "production_files_touched_count,test_files_touched_count,"
        "docs_tooling_files_touched_count,notes\n"
        "abc1234,2026-06-20,Fix routing,bug_fix,3,2,1,0,corrective\n"
        "def5678,2026-06-20,Extract gate module,refactor_architecture,12,4,8,0,architecture\n",
        encoding="utf-8",
    )
    rows = load_commit_classification_rows(fixture)
    assert len(rows) == 2
    assert rows[0].category == "bug_fix"
    stats = _distribution_stats_for_category(rows, CATEGORY_BUG_FIX)
    assert stats["median_files_touched"] == 3.0
    assert stats["max_files_touched"] == 3
