"""BR2 attribution completeness regression guard (read-side validation only).

Reuses BR1 completeness reporting and BS3 maturity scores. Does not modify
attribution behavior, replacement behavior, projection, or runtime logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.attribution_completeness_metric import build_attribution_completeness_report

DEFAULT_OUTPUT_PATH = "artifacts/attribution_regression_guard_report.md"

# Guard floor recorded at BR2 establishment (2026-06-20) from live baseline corpus.
BR2_RECORDED_BASELINE: dict[str, Any] = {
    "resolved_completeness_pct": 32.65,
    "resolved_complete_records": 16,
    "total_records": 49,
    "strict_completeness_pct": 0.0,
    "strict_complete_records": 0,
    "contract_compliance_score_pct": 100.0,
    "taxonomy_consistency_score_pct": 100.0,
}

BR2_GUARD_THRESHOLDS: dict[str, Any] = {
    "contract_compliance_score_pct_min": 100.0,
    "taxonomy_consistency_score_pct_min": 100.0,
    "resolved_completeness_pct_min": BR2_RECORDED_BASELINE["resolved_completeness_pct"],
}


@dataclass(frozen=True)
class GuardCheckResult:
    metric: str
    severity: str
    threshold: float | None
    baseline: float | None
    current: float
    passed: bool
    message: str


def extract_guarded_metrics(
    completeness_report: Mapping[str, Any],
) -> dict[str, float | int]:
    """Pull guarded headline metrics from a BR1 completeness report payload."""
    overall = completeness_report["overall"]["current"]
    contract = completeness_report["contract_integration"]["current"]
    return {
        "resolved_completeness_pct": float(overall["resolved_completeness_pct"]),
        "resolved_complete_records": int(overall["resolved_complete_records"]),
        "total_records": int(overall["total_records"]),
        "strict_completeness_pct": float(overall["strict_completeness_pct"]),
        "strict_complete_records": int(overall["strict_complete_records"]),
        "contract_compliance_score_pct": float(contract["contract_compliance_score_pct"]),
        "taxonomy_consistency_score_pct": float(contract["taxonomy_consistency_score_pct"]),
    }


def _check_not_below(
    *,
    metric: str,
    severity: str,
    current: float,
    minimum: float,
    baseline: float | None = None,
) -> GuardCheckResult:
    passed = current >= minimum
    if passed:
        message = f"{metric} {current} meets minimum {minimum}."
    else:
        message = f"{metric} regressed: current {current} is below minimum {minimum}."
    return GuardCheckResult(
        metric=metric,
        severity=severity,
        threshold=minimum,
        baseline=baseline,
        current=current,
        passed=passed,
        message=message,
    )


def evaluate_contract_compliance_guard(
    *,
    current: float,
    threshold: float | None = None,
    baseline: float | None = None,
) -> GuardCheckResult:
    """Return guard check for contract compliance (must not decrease below threshold)."""
    minimum = float(threshold if threshold is not None else BR2_GUARD_THRESHOLDS["contract_compliance_score_pct_min"])
    recorded = baseline if baseline is not None else BR2_RECORDED_BASELINE["contract_compliance_score_pct"]
    return _check_not_below(
        metric="contract_compliance_score_pct",
        severity="required",
        current=current,
        minimum=minimum,
        baseline=float(recorded),
    )


def evaluate_taxonomy_consistency_guard(
    *,
    current: float,
    threshold: float | None = None,
    baseline: float | None = None,
) -> GuardCheckResult:
    """Return guard check for taxonomy consistency (must not decrease below threshold)."""
    minimum = float(threshold if threshold is not None else BR2_GUARD_THRESHOLDS["taxonomy_consistency_score_pct_min"])
    recorded = baseline if baseline is not None else BR2_RECORDED_BASELINE["taxonomy_consistency_score_pct"]
    return _check_not_below(
        metric="taxonomy_consistency_score_pct",
        severity="required",
        current=current,
        minimum=minimum,
        baseline=float(recorded),
    )


def evaluate_resolved_completeness_guard(
    *,
    current: float,
    threshold: float | None = None,
    baseline: float | None = None,
) -> GuardCheckResult:
    """Return guard check for resolved completeness (must not decrease below recorded baseline)."""
    minimum = float(threshold if threshold is not None else BR2_GUARD_THRESHOLDS["resolved_completeness_pct_min"])
    recorded = baseline if baseline is not None else BR2_RECORDED_BASELINE["resolved_completeness_pct"]
    return _check_not_below(
        metric="resolved_completeness_pct",
        severity="required",
        current=current,
        minimum=minimum,
        baseline=float(recorded),
    )


def evaluate_strict_completeness_info(
    *,
    current: float,
    baseline: float | None = None,
) -> GuardCheckResult:
    """Return informational strict completeness check (does not fail the guard)."""
    recorded = baseline if baseline is not None else BR2_RECORDED_BASELINE["strict_completeness_pct"]
    return GuardCheckResult(
        metric="strict_completeness_pct",
        severity="informational",
        threshold=None,
        baseline=float(recorded),
        current=current,
        passed=True,
        message=(
            f"strict_completeness_pct {current} recorded for trend tracking "
            f"(baseline {recorded}); informational only."
        ),
    )


def evaluate_attribution_regression_guard(
    *,
    completeness_report: Mapping[str, Any] | None = None,
    recorded_baseline: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate all BR2 guard checks against the current BR1 completeness report."""
    report = completeness_report or build_attribution_completeness_report()
    metrics = extract_guarded_metrics(report)
    baseline = dict(recorded_baseline or BR2_RECORDED_BASELINE)
    guard_thresholds = dict(thresholds or BR2_GUARD_THRESHOLDS)

    checks: list[GuardCheckResult] = [
        evaluate_resolved_completeness_guard(
            current=float(metrics["resolved_completeness_pct"]),
            threshold=float(guard_thresholds["resolved_completeness_pct_min"]),
            baseline=float(baseline["resolved_completeness_pct"]),
        ),
        evaluate_contract_compliance_guard(
            current=float(metrics["contract_compliance_score_pct"]),
            threshold=float(guard_thresholds["contract_compliance_score_pct_min"]),
            baseline=float(baseline["contract_compliance_score_pct"]),
        ),
        evaluate_taxonomy_consistency_guard(
            current=float(metrics["taxonomy_consistency_score_pct"]),
            threshold=float(guard_thresholds["taxonomy_consistency_score_pct_min"]),
            baseline=float(baseline["taxonomy_consistency_score_pct"]),
        ),
        evaluate_strict_completeness_info(
            current=float(metrics["strict_completeness_pct"]),
            baseline=float(baseline["strict_completeness_pct"]),
        ),
    ]

    required_checks = [check for check in checks if check.severity == "required"]
    failed_checks = [check for check in required_checks if not check.passed]
    warnings = [check.message for check in failed_checks]

    return {
        "schema_version": 1,
        "status": "pass" if not failed_checks else "fail",
        "recorded_baseline": baseline,
        "thresholds": guard_thresholds,
        "current_metrics": metrics,
        "checks": [check.__dict__ for check in checks],
        "regression_warnings": warnings,
        "completeness_report_schema_version": report.get("schema_version"),
    }


def assert_attribution_metrics_not_regressed(
    *,
    completeness_report: Mapping[str, Any] | None = None,
    recorded_baseline: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assert required BR2 guard checks pass; raise AssertionError on regression."""
    evaluation = evaluate_attribution_regression_guard(
        completeness_report=completeness_report,
        recorded_baseline=recorded_baseline,
        thresholds=thresholds,
    )
    if evaluation["status"] != "pass":
        warnings = evaluation["regression_warnings"]
        raise AssertionError("Attribution regression guard failed:\n" + "\n".join(f"- {item}" for item in warnings))
    return evaluation


def render_attribution_regression_guard_report_md(evaluation: Mapping[str, Any]) -> str:
    """Render BR2 attribution regression guard markdown report."""
    status = str(evaluation["status"]).upper()
    baseline = evaluation["recorded_baseline"]
    thresholds = evaluation["thresholds"]
    metrics = evaluation["current_metrics"]
    checks = evaluation["checks"]
    warnings = evaluation["regression_warnings"]

    lines = [
        "# Attribution Regression Guard Report",
        "",
        "> BR2 repository guard — validates attribution completeness and BS3 contract scores "
        "against recorded baselines and fixed thresholds.",
        "",
        f"## Status: **{status}**",
        "",
        "## Guarded Metrics",
        "",
        "| Metric | Recorded baseline | Threshold | Current | Result |",
        "|---|---:|---:|---:|---|",
    ]

    for check in checks:
        metric = check["metric"]
        current = check["current"]
        baseline_value = check["baseline"]
        threshold = check["threshold"]
        threshold_display = "—" if threshold is None else str(threshold)
        result = "PASS" if check["passed"] else "FAIL"
        if check["severity"] == "informational":
            result = "INFO"
        baseline_display = "—" if baseline_value is None else str(baseline_value)
        lines.append(
            f"| `{metric}` | {baseline_display} | {threshold_display} | {current} | {result} |"
        )

    lines.extend(
        [
            "",
            "## Threshold Configuration",
            "",
            f"- Contract compliance minimum: **{thresholds['contract_compliance_score_pct_min']}%**",
            f"- Taxonomy consistency minimum: **{thresholds['taxonomy_consistency_score_pct_min']}%**",
            f"- Resolved completeness minimum: **{thresholds['resolved_completeness_pct_min']}%** "
            f"(recorded BR2 baseline)",
            "- Strict completeness: informational only",
            "",
            "## Current Snapshot",
            "",
            f"- Resolved completeness: **{metrics['resolved_completeness_pct']}%** "
            f"({metrics['resolved_complete_records']}/{metrics['total_records']})",
            f"- Strict completeness: **{metrics['strict_completeness_pct']}%** "
            f"({metrics['strict_complete_records']}/{metrics['total_records']})",
            f"- Contract compliance: **{metrics['contract_compliance_score_pct']}%**",
            f"- Taxonomy consistency: **{metrics['taxonomy_consistency_score_pct']}%**",
            "",
            f"_Recorded baseline resolved completeness: {baseline['resolved_completeness_pct']}% "
            f"({baseline['resolved_complete_records']}/{baseline['total_records']})._",
            "",
            "## Regression Warnings",
            "",
        ]
    )
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- _none_")
    lines.append("")
    return "\n".join(lines)


def write_attribution_regression_guard_report(
    output_path: str | Path | None = None,
    *,
    completeness_report: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """Generate BR2 attribution regression guard artifact."""
    evaluation = evaluate_attribution_regression_guard(completeness_report=completeness_report)
    markdown = render_attribution_regression_guard_report_md(evaluation)
    target = Path(output_path or DEFAULT_OUTPUT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return evaluation, markdown
