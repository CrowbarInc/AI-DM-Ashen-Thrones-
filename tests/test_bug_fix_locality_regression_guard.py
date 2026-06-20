"""BRL2 bug-fix locality regression guard validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.bug_fix_locality_metric import build_bug_fix_locality_report
from tests.helpers.bug_fix_locality_regression_guard import (
    BRL2_GUARD_THRESHOLDS,
    BRL2_RECORDED_BASELINE,
    assert_locality_metrics_not_regressed,
    evaluate_bug_fix_locality_guard,
    evaluate_hotspot_concentration_guard,
    evaluate_locality_regression_guard,
    evaluate_maintenance_concentration_guard,
    evaluate_refactor_locality_guard,
    write_bug_fix_locality_regression_guard_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "docs" / "reports" / "BR_commit_classification.csv"


def _synthetic_locality_report(
    *,
    bug_fix_median: float = 9.0,
    refactor_median: float = 16.0,
    maintenance_top5: float = 3.98,
    maintenance_top_file: float = 1.02,
    hotspot_top_cluster_share: float = 13.85,
) -> dict:
    report = build_bug_fix_locality_report(
        csv_path=CSV_PATH,
        repo_root=REPO_ROOT,
        include_hotspots=False,
    )
    report["current"]["bug_fix"]["median_files_touched"] = bug_fix_median
    report["current"]["refactor_architecture"]["median_files_touched"] = refactor_median
    report["hotspots"] = {
        "maintenance_concentration": {
            "bug_fix": {
                "top5_share_pct": maintenance_top5,
                "top_file_share_pct": maintenance_top_file,
                "distinct_paths": 835,
            }
        },
        "hotspot_concentration": {
            "bug_fix": {
                "top_cluster": "data/session.json",
                "top_cluster_share_pct": hotspot_top_cluster_share,
            }
        },
    }
    return report


def test_live_locality_regression_guard_passes():
    evaluation = evaluate_locality_regression_guard(csv_path=CSV_PATH, repo_root=REPO_ROOT)
    assert evaluation["status"] == "pass"
    assert evaluation["regression_warnings"] == []
    assert_locality_metrics_not_regressed(csv_path=CSV_PATH, repo_root=REPO_ROOT)


def test_bug_fix_locality_regression_detection():
    check = evaluate_bug_fix_locality_guard(current_median=10.0, threshold=9.0)
    assert check.passed is False
    assert "regressed" in check.message

    evaluation = evaluate_locality_regression_guard(
        locality_report=_synthetic_locality_report(bug_fix_median=10.0),
    )
    assert evaluation["status"] == "fail"
    assert any("bug_fix_median_files_touched" in warning for warning in evaluation["regression_warnings"])


def test_refactor_locality_regression_detection():
    check = evaluate_refactor_locality_guard(current_median=20.0, threshold=16.0)
    assert check.passed is False

    evaluation = evaluate_locality_regression_guard(
        locality_report=_synthetic_locality_report(refactor_median=20.0),
    )
    assert evaluation["status"] == "fail"
    assert any("refactor_median_files_touched" in warning for warning in evaluation["regression_warnings"])


def test_maintenance_concentration_regression_detection():
    checks = evaluate_maintenance_concentration_guard(
        current_top5_share_pct=5.0,
        current_top_file_share_pct=1.02,
        top5_threshold=3.98,
    )
    assert checks[0].passed is False

    evaluation = evaluate_locality_regression_guard(
        locality_report=_synthetic_locality_report(maintenance_top5=5.0),
    )
    assert evaluation["status"] == "fail"
    assert any("maintenance_top5_share_pct" in warning for warning in evaluation["regression_warnings"])


def test_hotspot_concentration_regression_detection():
    check = evaluate_hotspot_concentration_guard(current_top_cluster_share_pct=25.0, threshold=13.85)
    assert check.passed is False

    evaluation = evaluate_locality_regression_guard(
        locality_report=_synthetic_locality_report(hotspot_top_cluster_share=25.0),
    )
    assert evaluation["status"] == "fail"
    assert any("hotspot_top_cluster_share_pct" in warning for warning in evaluation["regression_warnings"])


def test_assert_locality_metrics_not_regressed_raises_on_failure():
    with pytest.raises(AssertionError, match="Locality regression guard failed"):
        assert_locality_metrics_not_regressed(
            locality_report=_synthetic_locality_report(bug_fix_median=12.0),
        )


def test_locality_guard_evaluation_is_deterministic():
    first = evaluate_locality_regression_guard(
        locality_report=_synthetic_locality_report(),
    )
    second = evaluate_locality_regression_guard(
        locality_report=_synthetic_locality_report(),
    )
    assert first == second


def test_locality_regression_guard_report_generation(tmp_path):
    output = tmp_path / "bug_fix_locality_regression_guard_report.md"
    evaluation, markdown = write_bug_fix_locality_regression_guard_report(
        output,
        csv_path=CSV_PATH,
        repo_root=REPO_ROOT,
    )
    assert output.exists()
    assert evaluation["schema_version"] == 1
    assert "Bug-Fix Locality Regression Guard Report" in markdown
    assert "Guarded Metrics" in markdown
    assert "Regression Warnings" in markdown
    assert evaluation["thresholds"]["bug_fix_median_files_touched_max"] == pytest.approx(
        BRL2_GUARD_THRESHOLDS["bug_fix_median_files_touched_max"]
    )
    assert evaluation["recorded_baseline"]["bug_fix_median_files_touched"] == pytest.approx(
        BRL2_RECORDED_BASELINE["bug_fix_median_files_touched"]
    )
