"""BR2 attribution completeness regression guard validation."""
from __future__ import annotations

import pytest

from tests.helpers.attribution_completeness_metric import build_attribution_completeness_report
from tests.helpers.attribution_regression_guard import (
    assert_attribution_metrics_not_regressed,
    evaluate_attribution_regression_guard,
    evaluate_contract_compliance_guard,
    evaluate_resolved_completeness_guard,
    evaluate_taxonomy_consistency_guard,
    write_attribution_regression_guard_report,
)


def _synthetic_completeness_report(
    *,
    resolved_completeness_pct: float = 32.65,
    contract_compliance_score_pct: float = 100.0,
    taxonomy_consistency_score_pct: float = 100.0,
    strict_completeness_pct: float = 0.0,
) -> dict:
    report = build_attribution_completeness_report()
    report["overall"]["current"]["resolved_completeness_pct"] = resolved_completeness_pct
    report["overall"]["current"]["strict_completeness_pct"] = strict_completeness_pct
    report["contract_integration"]["current"]["contract_compliance_score_pct"] = contract_compliance_score_pct
    report["contract_integration"]["current"]["taxonomy_consistency_score_pct"] = taxonomy_consistency_score_pct
    return report


def test_live_attribution_regression_guard_passes():
    evaluation = evaluate_attribution_regression_guard()
    assert evaluation["status"] == "pass"
    assert evaluation["regression_warnings"] == []
    assert_attribution_metrics_not_regressed()


def test_compliance_regression_detection():
    check = evaluate_contract_compliance_guard(current=99.5, threshold=100.0)
    assert check.passed is False
    assert "regressed" in check.message

    evaluation = evaluate_attribution_regression_guard(
        completeness_report=_synthetic_completeness_report(contract_compliance_score_pct=99.5),
    )
    assert evaluation["status"] == "fail"
    assert any("contract_compliance_score_pct" in warning for warning in evaluation["regression_warnings"])


def test_taxonomy_regression_detection():
    check = evaluate_taxonomy_consistency_guard(current=80.0, threshold=100.0)
    assert check.passed is False

    evaluation = evaluate_attribution_regression_guard(
        completeness_report=_synthetic_completeness_report(taxonomy_consistency_score_pct=80.0),
    )
    assert evaluation["status"] == "fail"
    assert any("taxonomy_consistency_score_pct" in warning for warning in evaluation["regression_warnings"])


def test_completeness_regression_detection():
    check = evaluate_resolved_completeness_guard(current=30.0, threshold=32.65)
    assert check.passed is False

    evaluation = evaluate_attribution_regression_guard(
        completeness_report=_synthetic_completeness_report(resolved_completeness_pct=30.0),
    )
    assert evaluation["status"] == "fail"
    assert any("resolved_completeness_pct" in warning for warning in evaluation["regression_warnings"])


def test_assert_attribution_metrics_not_regressed_raises_on_failure():
    with pytest.raises(AssertionError, match="Attribution regression guard failed"):
        assert_attribution_metrics_not_regressed(
            completeness_report=_synthetic_completeness_report(resolved_completeness_pct=10.0),
        )


def test_attribution_regression_guard_report_generation(tmp_path):
    output = tmp_path / "attribution_regression_guard_report.md"
    evaluation, markdown = write_attribution_regression_guard_report(output)
    assert output.exists()
    assert evaluation["schema_version"] == 1
    assert "Attribution Regression Guard Report" in markdown
    assert "Guarded Metrics" in markdown
    assert "Threshold Configuration" in markdown
    assert "Regression Warnings" in markdown
    assert "**PASS**" in markdown or "**FAIL**" in markdown
