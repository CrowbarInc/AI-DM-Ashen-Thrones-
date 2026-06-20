"""BRL2 bug-fix locality regression guard (read-side validation only).

Reuses BRL1 locality reporting. Does not modify runtime behavior, ownership,
commit classification methodology, or hotspot calculation rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from tests.helpers.bug_fix_locality_metric import (
    BRL1_BASELINE_LOCALITY,
    CATEGORY_BUG_FIX,
    CATEGORY_REFACTOR,
    build_bug_fix_locality_report,
)

DEFAULT_OUTPUT_PATH = "artifacts/bug_fix_locality_regression_guard_report.md"

# Guard ceilings recorded at BRL2 establishment (2026-06-20) from BRL1 live report.
BRL2_RECORDED_BASELINE: dict[str, Any] = {
    "bug_fix_median_files_touched": 9.0,
    "refactor_median_files_touched": 16.0,
    "bug_fix_maintenance_top5_share_pct": 3.98,
    "bug_fix_maintenance_top_file_share_pct": 1.02,
    "bug_fix_hotspot_top_cluster_share_pct": 13.85,
    "bug_fix_hotspot_top_cluster": "data/session.json",
}

BRL2_GUARD_THRESHOLDS: dict[str, Any] = {
    "bug_fix_median_files_touched_max": BRL2_RECORDED_BASELINE["bug_fix_median_files_touched"],
    "refactor_median_files_touched_max": BRL2_RECORDED_BASELINE["refactor_median_files_touched"],
    "bug_fix_maintenance_top5_share_pct_max": BRL2_RECORDED_BASELINE["bug_fix_maintenance_top5_share_pct"],
    "bug_fix_maintenance_top_file_share_pct_max": BRL2_RECORDED_BASELINE[
        "bug_fix_maintenance_top_file_share_pct"
    ],
    "bug_fix_hotspot_top_cluster_share_pct_max": BRL2_RECORDED_BASELINE[
        "bug_fix_hotspot_top_cluster_share_pct"
    ],
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


def extract_locality_guard_metrics(locality_report: Mapping[str, Any]) -> dict[str, Any]:
    """Pull guarded metrics from a BRL1 locality report payload."""
    hotspots = locality_report.get("hotspots") or {}
    maintenance = hotspots.get("maintenance_concentration") or {}
    hotspot_concentration = hotspots.get("hotspot_concentration") or {}
    bug_maintenance = maintenance.get(CATEGORY_BUG_FIX) or {}
    bug_hotspot = hotspot_concentration.get(CATEGORY_BUG_FIX) or {}
    return {
        "bug_fix_median_files_touched": float(
            locality_report["current"][CATEGORY_BUG_FIX]["median_files_touched"]
        ),
        "refactor_median_files_touched": float(
            locality_report["current"][CATEGORY_REFACTOR]["median_files_touched"]
        ),
        "bug_fix_maintenance_top5_share_pct": float(bug_maintenance.get("top5_share_pct") or 0.0),
        "bug_fix_maintenance_top_file_share_pct": float(
            bug_maintenance.get("top_file_share_pct") or 0.0
        ),
        "bug_fix_hotspot_top_cluster_share_pct": float(
            bug_hotspot.get("top_cluster_share_pct") or 0.0
        ),
        "bug_fix_hotspot_top_cluster": bug_hotspot.get("top_cluster"),
    }


def _check_not_above(
    *,
    metric: str,
    severity: str,
    current: float,
    maximum: float,
    baseline: float | None = None,
) -> GuardCheckResult:
    passed = current <= maximum
    if passed:
        message = f"{metric} {current} is within ceiling {maximum}."
    else:
        message = f"{metric} regressed: current {current} exceeds ceiling {maximum}."
    return GuardCheckResult(
        metric=metric,
        severity=severity,
        threshold=maximum,
        baseline=baseline,
        current=current,
        passed=passed,
        message=message,
    )


def evaluate_bug_fix_locality_guard(
    *,
    current_median: float,
    threshold: float | None = None,
    baseline: float | None = None,
) -> GuardCheckResult:
    """Return guard check for bug-fix median files touched."""
    maximum = float(
        threshold if threshold is not None else BRL2_GUARD_THRESHOLDS["bug_fix_median_files_touched_max"]
    )
    recorded = baseline if baseline is not None else BRL2_RECORDED_BASELINE["bug_fix_median_files_touched"]
    return _check_not_above(
        metric="bug_fix_median_files_touched",
        severity="required",
        current=current_median,
        maximum=maximum,
        baseline=float(recorded),
    )


def evaluate_refactor_locality_guard(
    *,
    current_median: float,
    threshold: float | None = None,
    baseline: float | None = None,
) -> GuardCheckResult:
    """Return guard check for refactor median files touched."""
    maximum = float(
        threshold if threshold is not None else BRL2_GUARD_THRESHOLDS["refactor_median_files_touched_max"]
    )
    recorded = baseline if baseline is not None else BRL2_RECORDED_BASELINE["refactor_median_files_touched"]
    return _check_not_above(
        metric="refactor_median_files_touched",
        severity="required",
        current=current_median,
        maximum=maximum,
        baseline=float(recorded),
    )


def evaluate_maintenance_concentration_guard(
    *,
    current_top5_share_pct: float,
    current_top_file_share_pct: float,
    top5_threshold: float | None = None,
    top_file_threshold: float | None = None,
    baseline_top5: float | None = None,
    baseline_top_file: float | None = None,
) -> list[GuardCheckResult]:
    """Return guard checks for maintenance concentration (lower share is better)."""
    top5_max = float(
        top5_threshold
        if top5_threshold is not None
        else BRL2_GUARD_THRESHOLDS["bug_fix_maintenance_top5_share_pct_max"]
    )
    top_file_max = float(
        top_file_threshold
        if top_file_threshold is not None
        else BRL2_GUARD_THRESHOLDS["bug_fix_maintenance_top_file_share_pct_max"]
    )
    recorded_top5 = (
        baseline_top5
        if baseline_top5 is not None
        else BRL2_RECORDED_BASELINE["bug_fix_maintenance_top5_share_pct"]
    )
    recorded_top_file = (
        baseline_top_file
        if baseline_top_file is not None
        else BRL2_RECORDED_BASELINE["bug_fix_maintenance_top_file_share_pct"]
    )
    return [
        _check_not_above(
            metric="bug_fix_maintenance_top5_share_pct",
            severity="required",
            current=current_top5_share_pct,
            maximum=top5_max,
            baseline=float(recorded_top5),
        ),
        _check_not_above(
            metric="bug_fix_maintenance_top_file_share_pct",
            severity="required",
            current=current_top_file_share_pct,
            maximum=top_file_max,
            baseline=float(recorded_top_file),
        ),
    ]


def evaluate_hotspot_concentration_guard(
    *,
    current_top_cluster_share_pct: float,
    threshold: float | None = None,
    baseline: float | None = None,
) -> GuardCheckResult:
    """Return guard check for bug-fix hotspot cluster concentration."""
    maximum = float(
        threshold
        if threshold is not None
        else BRL2_GUARD_THRESHOLDS["bug_fix_hotspot_top_cluster_share_pct_max"]
    )
    recorded = (
        baseline
        if baseline is not None
        else BRL2_RECORDED_BASELINE["bug_fix_hotspot_top_cluster_share_pct"]
    )
    return _check_not_above(
        metric="bug_fix_hotspot_top_cluster_share_pct",
        severity="required",
        current=current_top_cluster_share_pct,
        maximum=maximum,
        baseline=float(recorded),
    )


def evaluate_locality_regression_guard(
    *,
    locality_report: Mapping[str, Any] | None = None,
    recorded_baseline: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, Any] | None = None,
    csv_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Evaluate all BRL2 guard checks against the current BRL1 locality report."""
    report = locality_report or build_bug_fix_locality_report(
        csv_path=csv_path,
        repo_root=repo_root,
        include_hotspots=True,
    )
    metrics = extract_locality_guard_metrics(report)
    baseline = dict(recorded_baseline or BRL2_RECORDED_BASELINE)
    guard_thresholds = dict(thresholds or BRL2_GUARD_THRESHOLDS)

    checks: list[GuardCheckResult] = [
        evaluate_bug_fix_locality_guard(
            current_median=metrics["bug_fix_median_files_touched"],
            threshold=float(guard_thresholds["bug_fix_median_files_touched_max"]),
            baseline=float(baseline["bug_fix_median_files_touched"]),
        ),
        evaluate_refactor_locality_guard(
            current_median=metrics["refactor_median_files_touched"],
            threshold=float(guard_thresholds["refactor_median_files_touched_max"]),
            baseline=float(baseline["refactor_median_files_touched"]),
        ),
        *evaluate_maintenance_concentration_guard(
            current_top5_share_pct=metrics["bug_fix_maintenance_top5_share_pct"],
            current_top_file_share_pct=metrics["bug_fix_maintenance_top_file_share_pct"],
            top5_threshold=float(guard_thresholds["bug_fix_maintenance_top5_share_pct_max"]),
            top_file_threshold=float(guard_thresholds["bug_fix_maintenance_top_file_share_pct_max"]),
            baseline_top5=float(baseline["bug_fix_maintenance_top5_share_pct"]),
            baseline_top_file=float(baseline["bug_fix_maintenance_top_file_share_pct"]),
        ),
        evaluate_hotspot_concentration_guard(
            current_top_cluster_share_pct=metrics["bug_fix_hotspot_top_cluster_share_pct"],
            threshold=float(guard_thresholds["bug_fix_hotspot_top_cluster_share_pct_max"]),
            baseline=float(baseline["bug_fix_hotspot_top_cluster_share_pct"]),
        ),
    ]

    required_checks = [check for check in checks if check.severity == "required"]
    failed_checks = [check for check in required_checks if not check.passed]
    warnings = [check.message for check in failed_checks]

    trend: dict[str, dict[str, Any]] = {}
    for key in (
        "bug_fix_median_files_touched",
        "refactor_median_files_touched",
        "bug_fix_maintenance_top5_share_pct",
        "bug_fix_maintenance_top_file_share_pct",
        "bug_fix_hotspot_top_cluster_share_pct",
    ):
        current_value = metrics[key]
        baseline_value = baseline.get(key)
        delta = None
        if isinstance(baseline_value, (int, float)):
            delta = round(float(current_value) - float(baseline_value), 2)
        trend[key] = {
            "baseline": baseline_value,
            "current": current_value,
            "delta": delta,
        }

    return {
        "schema_version": 1,
        "status": "pass" if not failed_checks else "fail",
        "recorded_baseline": baseline,
        "thresholds": guard_thresholds,
        "current_metrics": metrics,
        "trend": trend,
        "checks": [check.__dict__ for check in checks],
        "regression_warnings": warnings,
        "locality_report_schema_version": report.get("schema_version"),
        "brl1_baseline_reference": BRL1_BASELINE_LOCALITY,
    }


def assert_locality_metrics_not_regressed(
    *,
    locality_report: Mapping[str, Any] | None = None,
    recorded_baseline: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, Any] | None = None,
    csv_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Assert required BRL2 guard checks pass; raise AssertionError on regression."""
    evaluation = evaluate_locality_regression_guard(
        locality_report=locality_report,
        recorded_baseline=recorded_baseline,
        thresholds=thresholds,
        csv_path=csv_path,
        repo_root=repo_root,
    )
    if evaluation["status"] != "pass":
        warnings = evaluation["regression_warnings"]
        raise AssertionError("Locality regression guard failed:\n" + "\n".join(f"- {item}" for item in warnings))
    return evaluation


def render_bug_fix_locality_regression_guard_report_md(evaluation: Mapping[str, Any]) -> str:
    """Render BRL2 bug-fix locality regression guard markdown report."""
    status = str(evaluation["status"]).upper()
    baseline = evaluation["recorded_baseline"]
    thresholds = evaluation["thresholds"]
    metrics = evaluation["current_metrics"]
    trend = evaluation["trend"]
    warnings = evaluation["regression_warnings"]

    lines = [
        "# Bug-Fix Locality Regression Guard Report",
        "",
        "> BRL2 repository guard — validates locality economics against recorded BRL1 baselines.",
        "",
        f"## Status: **{status}**",
        "",
        "## Guarded Metrics",
        "",
        "| Metric | Baseline | Threshold | Current | Delta | Result |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for check in evaluation["checks"]:
        metric = check["metric"]
        block = trend.get(metric) or {}
        delta = block.get("delta")
        delta_display = "—" if delta is None else f"{delta:+}"
        threshold = check["threshold"]
        threshold_display = "—" if threshold is None else str(threshold)
        baseline_value = block.get("baseline", check.get("baseline"))
        baseline_display = "—" if baseline_value is None else str(baseline_value)
        result = "PASS" if check["passed"] else "FAIL"
        lines.append(
            f"| `{metric}` | {baseline_display} | {threshold_display} | "
            f"{check['current']} | {delta_display} | {result} |"
        )

    lines.extend(
        [
            "",
            "## Threshold Configuration",
            "",
            f"- Bug-fix median files touched ceiling: **{thresholds['bug_fix_median_files_touched_max']}**",
            f"- Refactor median files touched ceiling: **{thresholds['refactor_median_files_touched_max']}**",
            f"- Bug-fix maintenance top-5 share ceiling: **{thresholds['bug_fix_maintenance_top5_share_pct_max']}%**",
            f"- Bug-fix maintenance top-file share ceiling: **{thresholds['bug_fix_maintenance_top_file_share_pct_max']}%**",
            f"- Bug-fix hotspot top-cluster share ceiling: **{thresholds['bug_fix_hotspot_top_cluster_share_pct_max']}%**",
            "",
            "## Current Snapshot",
            "",
            f"- Bug-fix median files touched: **{metrics['bug_fix_median_files_touched']}**",
            f"- Refactor median files touched: **{metrics['refactor_median_files_touched']}**",
            f"- Bug-fix maintenance top-5 share: **{metrics['bug_fix_maintenance_top5_share_pct']}%**",
            f"- Bug-fix maintenance top-file share: **{metrics['bug_fix_maintenance_top_file_share_pct']}%**",
            f"- Bug-fix hotspot top cluster: **`{metrics['bug_fix_hotspot_top_cluster']}`** "
            f"({metrics['bug_fix_hotspot_top_cluster_share_pct']}%)",
            "",
            f"_Recorded baseline bug-fix median: {baseline['bug_fix_median_files_touched']} files._",
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


def write_bug_fix_locality_regression_guard_report(
    output_path: str | Path | None = None,
    *,
    locality_report: Mapping[str, Any] | None = None,
    csv_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Generate BRL2 bug-fix locality regression guard artifact."""
    evaluation = evaluate_locality_regression_guard(
        locality_report=locality_report,
        csv_path=csv_path,
        repo_root=repo_root,
    )
    markdown = render_bug_fix_locality_regression_guard_report_md(evaluation)
    target = Path(output_path or DEFAULT_OUTPUT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return evaluation, markdown
