#!/usr/bin/env python3
"""Attribute optional engineering effort to fallback remediation outcomes."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
ENGINEER_MONTH_HOURS = 160.0
ACTIVE_STATUSES = {"proposed", "accepted", "in_progress"}
DEFAULT_EFFECTIVENESS_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_effectiveness.json"
DEFAULT_REGISTRY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_registry.json"
DEFAULT_JSON_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_roi_report.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_roi_report.md"

EFFICIENCY_THRESHOLDS = {
    "ineffective": 0.0,
    "low": 0.0,
    "moderate": 1.0,
    "high": 2.0,
}


def _optional_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if number >= 0 else None
    except (TypeError, ValueError):
        return None


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0 else None


def classify_efficiency(value: float | None, *, risk_removed: float) -> str:
    if value is None:
        return "unavailable"
    if risk_removed <= 0:
        return "ineffective"
    if value >= EFFICIENCY_THRESHOLDS["high"]:
        return "high"
    if value >= EFFICIENCY_THRESHOLDS["moderate"]:
        return "moderate"
    return "low"


def _registry_index(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = registry.get("remediations")
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("remediation_id")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("remediation_id")
    }


def _individual_rows(
    effectiveness_report: Mapping[str, Any], registry: Mapping[str, Any]
) -> list[dict[str, Any]]:
    raw = effectiveness_report.get("remediations")
    entries = [row for row in raw if isinstance(row, Mapping)] if isinstance(raw, list) else []
    effort = _registry_index(registry)
    rows: list[dict[str, Any]] = []
    for entry in entries:
        remediation_id = str(entry.get("remediation_id") or "")
        metadata = effort.get(remediation_id, {})
        estimated = _optional_number(metadata.get("estimated_hours"))
        actual = _optional_number(metadata.get("actual_hours"))
        engineer_count = _optional_number(metadata.get("engineer_count"))
        completed = entry.get("status") == "completed"
        reduction = max(0.0, _number(entry.get("absolute_risk_reduction"))) if completed else 0.0
        removed_per_hour = _ratio(reduction, actual or 0.0)
        hours_per_point = _ratio(actual or 0.0, reduction)
        variance = actual - estimated if actual is not None and estimated is not None else None
        error_percentage = variance / estimated if variance is not None and estimated and estimated > 0 else None
        rows.append(
            {
                "remediation_id": remediation_id,
                "contributor": str(entry.get("contributor") or ""),
                "dimension": str(entry.get("dimension") or ""),
                "status": str(entry.get("status") or ""),
                "effectiveness_classification": str(entry.get("effectiveness_classification") or "unchanged"),
                "estimated_hours": estimated,
                "actual_hours": actual,
                "engineer_count": engineer_count,
                "owner": str(metadata.get("owner") or "unassigned"),
                "remediation_type": str(metadata.get("remediation_type") or "unspecified"),
                "risk_points_removed": reduction,
                "risk_points_removed_per_hour": removed_per_hour,
                "hours_per_risk_point": hours_per_point,
                "remediation_efficiency": classify_efficiency(removed_per_hour, risk_removed=reduction),
                "estimate_variance_hours": variance,
                "estimate_error_percentage": error_percentage,
                "observation_depth": int(entry.get("evidence", {}).get("risk_snapshot_count") or 0)
                if isinstance(entry.get("evidence"), Mapping)
                else 0,
            }
        )
    return sorted(rows, key=lambda row: row["remediation_id"])


def _aggregate(rows: Sequence[Mapping[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get(field) or ("unassigned" if field == "owner" else "unspecified"))
        target = groups.setdefault(
            name,
            {
                field: name,
                "remediation_count": 0,
                "completed_remediation_count": 0,
                "tracked_effort_count": 0,
                "total_actual_hours": 0.0,
                "completed_actual_hours": 0.0,
                "risk_points_removed": 0.0,
            },
        )
        target["remediation_count"] += 1
        actual = row.get("actual_hours")
        if actual is not None:
            target["tracked_effort_count"] += 1
            target["total_actual_hours"] += _number(actual)
        if row.get("status") == "completed":
            target["completed_remediation_count"] += 1
            if actual is not None:
                target["completed_actual_hours"] += _number(actual)
            target["risk_points_removed"] += _number(row.get("risk_points_removed"))
    results = []
    for target in groups.values():
        efficiency = _ratio(target["risk_points_removed"], target["completed_actual_hours"])
        results.append(
            {
                **target,
                "risk_points_removed_per_hour": efficiency,
                "hours_per_risk_point": _ratio(target["completed_actual_hours"], target["risk_points_removed"]),
                "remediation_efficiency": classify_efficiency(
                    efficiency, risk_removed=target["risk_points_removed"]
                ),
            }
        )
    return sorted(results, key=lambda row: str(row[field]))


def _confidence(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    tracked = [row for row in rows if row.get("actual_hours") is not None]
    completed_tracked = [row for row in tracked if row.get("status") == "completed"]
    coverage = len(tracked) / total if total else 0.0
    depths = [_number(row.get("observation_depth")) for row in completed_tracked]
    average_depth = statistics.fmean(depths) if depths else 0.0
    coverage_points = 2 if coverage >= 0.8 else (1 if coverage >= 0.4 else 0)
    depth_points = 2 if average_depth >= 5 else (1 if average_depth >= 3 else 0)
    count_points = 2 if len(completed_tracked) >= 5 else (1 if len(completed_tracked) >= 2 else 0)
    score = coverage_points + depth_points + count_points
    level = "high" if score >= 5 else ("medium" if score >= 3 else "low")
    return {
        "level": level,
        "score": score,
        "maximum_score": 6,
        "effort_data_coverage": coverage,
        "average_observation_depth": average_depth,
        "completed_remediations_with_effort": len(completed_tracked),
        "factors": {
            "effort_coverage_points": coverage_points,
            "observation_depth_points": depth_points,
            "remediation_count_points": count_points,
        },
        "thresholds": {
            "low": "0-2 points",
            "medium": "3-4 points",
            "high": "5-6 points",
            "effort_coverage": "1 point at >=40%; 2 at >=80%",
            "observation_depth": "1 point at average >=3; 2 at >=5",
            "remediation_count": "1 point at >=2 completed tracked remediations; 2 at >=5",
        },
    }


def build_fallback_roi_report(
    effectiveness_report: Mapping[str, Any], registry: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    rows = _individual_rows(effectiveness_report, registry or {})
    tracked = [row for row in rows if row["actual_hours"] is not None]
    completed = [row for row in rows if row["status"] == "completed"]
    completed_tracked = [row for row in completed if row["actual_hours"] is not None]
    active_tracked = [row for row in tracked if row["status"] in ACTIVE_STATUSES]
    total_hours = sum(_number(row["actual_hours"]) for row in tracked)
    completed_hours = sum(_number(row["actual_hours"]) for row in completed_tracked)
    active_hours = sum(_number(row["actual_hours"]) for row in active_tracked)
    actual_values = [_number(row["actual_hours"]) for row in tracked]
    risk_removed = sum(_number(row["risk_points_removed"]) for row in completed_tracked)
    portfolio_efficiency = _ratio(risk_removed, completed_hours)
    paired = [
        row for row in rows if row["estimated_hours"] is not None and row["actual_hours"] is not None
    ]
    variances = [_number(row["estimate_variance_hours"]) for row in paired]
    absolute_errors = [abs(_number(row["estimate_error_percentage"])) for row in paired if row["estimate_error_percentage"] is not None]
    owner_rows = _aggregate(rows, "owner")
    type_rows = _aggregate(rows, "remediation_type")
    owners_with_efficiency = [row for row in owner_rows if row["risk_points_removed_per_hour"] is not None]
    forecasts_available = portfolio_efficiency is not None and completed_hours > 0
    confidence = _confidence(rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "no_remediations" if not rows else ("no_effort_data" if not tracked else "ok"),
        "effort_model": {
            "optional_fields": [
                "estimated_hours",
                "actual_hours",
                "engineer_count",
                "owner",
                "remediation_type",
            ],
            "source": "optional fields on fallback_remediation_registry.json records",
            "engineer_month_hours": ENGINEER_MONTH_HOURS,
            "efficiency_thresholds_risk_points_per_hour": {
                "ineffective": "no risk removed",
                "low": "below 1.0",
                "moderate": "1.0 to below 2.0",
                "high": "2.0 or above",
            },
        },
        "portfolio_roi": {
            "remediation_count": len(rows),
            "effort_tracked_count": len(tracked),
            "completed_effort_tracked_count": len(completed_tracked),
            "risk_points_removed": risk_removed,
            "risk_points_removed_per_hour": portfolio_efficiency,
            "hours_per_risk_point": _ratio(completed_hours, risk_removed),
            "remediation_efficiency": classify_efficiency(
                portfolio_efficiency, risk_removed=risk_removed
            ),
        },
        "remediation_efficiency": rows,
        "owner_efficiency": owner_rows,
        "remediation_type_efficiency": type_rows,
        "owner_analysis": {
            "highest_efficiency_owners": sorted(
                owners_with_efficiency,
                key=lambda row: (-_number(row["risk_points_removed_per_hour"]), row["owner"]),
            ),
            "lowest_efficiency_owners": sorted(
                owners_with_efficiency,
                key=lambda row: (_number(row["risk_points_removed_per_hour"]), row["owner"]),
            ),
            "highest_effort_consumers": sorted(
                owner_rows, key=lambda row: (-row["total_actual_hours"], row["owner"])
            ),
            "largest_risk_reducers": sorted(
                owner_rows, key=lambda row: (-row["risk_points_removed"], row["owner"])
            ),
        },
        "estimate_accuracy": {
            "paired_estimate_count": len(paired),
            "average_estimate_variance_hours": statistics.fmean(variances) if variances else None,
            "median_estimate_variance_hours": statistics.median(variances) if variances else None,
            "mean_absolute_estimate_error_percentage": statistics.fmean(absolute_errors) if absolute_errors else None,
            "overrun_rate": sum(value > 0 for value in variances) / len(variances) if variances else None,
            "underrun_rate": sum(value < 0 for value in variances) / len(variances) if variances else None,
            "on_estimate_rate": sum(value == 0 for value in variances) / len(variances) if variances else None,
        },
        "capacity_analysis": {
            "total_hours_invested": total_hours,
            "average_remediation_effort": statistics.fmean(actual_values) if actual_values else None,
            "median_remediation_effort": statistics.median(actual_values) if actual_values else None,
            "active_effort_load": active_hours,
            "completed_effort_load": completed_hours,
            "total_engineer_participation": sum(
                _number(row["engineer_count"]) for row in tracked if row["engineer_count"] is not None
            ),
        },
        "forecasts": {
            "model": "linear extrapolation from completed tracked effort using a 160-hour engineer-month",
            "available": forecasts_available,
            "expected_risk_reduction_per_engineer_month": (
                portfolio_efficiency * ENGINEER_MONTH_HOURS if portfolio_efficiency is not None else None
            ),
            "expected_portfolio_throughput_per_engineer_month": (
                len(completed_tracked) / completed_hours * ENGINEER_MONTH_HOURS
                if completed_hours > 0
                else None
            ),
            "projected_remediation_capacity_per_engineer_month": (
                ENGINEER_MONTH_HOURS / statistics.fmean(actual_values) if actual_values else None
            ),
        },
        "confidence": confidence,
        "recommendations": (
            ["Add optional effort data to remediation registry records before interpreting ROI."]
            if not tracked
            else [
                "Use forecasts only as linear planning aids and review them alongside ROI confidence.",
                "Improve actual-hour coverage and observation depth before comparing owners or remediation types.",
            ]
        ),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    number = _number(value)
    return str(int(number)) if number.is_integer() else f"{number:.2f}"


def _efficiency_table(title: str, rows: Sequence[Mapping[str, Any]], name_key: str) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Name | Remediations | Hours | Risk Removed | Risk/Hour | Hours/Risk | Efficiency |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    if rows:
        for row in rows:
            lines.append(
                f"| `{row.get(name_key)}` | {row.get('remediation_count')} | "
                f"{_fmt(row.get('total_actual_hours'))} | {_fmt(row.get('risk_points_removed'))} | "
                f"{_fmt(row.get('risk_points_removed_per_hour'))} | {_fmt(row.get('hours_per_risk_point'))} | "
                f"`{row.get('remediation_efficiency')}` |"
            )
    else:
        lines.append("| _none_ | 0 | 0 | 0 | n/a | n/a | `unavailable` |")
    return lines


def render_fallback_roi_markdown(report: Mapping[str, Any]) -> str:
    roi = report.get("portfolio_roi") if isinstance(report.get("portfolio_roi"), Mapping) else {}
    estimate = report.get("estimate_accuracy") if isinstance(report.get("estimate_accuracy"), Mapping) else {}
    capacity = report.get("capacity_analysis") if isinstance(report.get("capacity_analysis"), Mapping) else {}
    forecasts = report.get("forecasts") if isinstance(report.get("forecasts"), Mapping) else {}
    confidence = report.get("confidence") if isinstance(report.get("confidence"), Mapping) else {}
    lines = [
        "# Fallback Engineering Effort and ROI",
        "",
        "> Advisory-only economics derived from BP10 outcomes and optional remediation effort metadata.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- ROI confidence: `{confidence.get('level', 'low')}` ({confidence.get('score', 0)}/6)",
        f"- Effort coverage: {_number(confidence.get('effort_data_coverage')) * 100:.1f}%",
        f"- Risk points removed: {_fmt(roi.get('risk_points_removed'))}",
        f"- Risk points per hour: {_fmt(roi.get('risk_points_removed_per_hour'))}",
        "",
        "## Portfolio ROI",
        "",
        f"- Tracked remediations: {roi.get('effort_tracked_count', 0)} of {roi.get('remediation_count', 0)}",
        f"- Hours per risk point: {_fmt(roi.get('hours_per_risk_point'))}",
        f"- Efficiency: `{roi.get('remediation_efficiency', 'unavailable')}`",
        "- Efficiency bands: ineffective at zero benefit; low below 1; moderate 1-2; high at 2+ risk points/hour.",
        "",
    ]
    lines.extend(_efficiency_table("Owner Efficiency", report.get("owner_efficiency", []), "owner"))
    lines.extend([""] + _efficiency_table("Remediation Efficiency", report.get("remediation_type_efficiency", []), "remediation_type"))
    lines.extend(
        [
            "",
            "## Estimate Accuracy",
            "",
            f"- Paired estimates: {estimate.get('paired_estimate_count', 0)}",
            f"- Average variance: {_fmt(estimate.get('average_estimate_variance_hours'))} hours",
            f"- Median variance: {_fmt(estimate.get('median_estimate_variance_hours'))} hours",
            f"- Mean absolute error: {_fmt(None if estimate.get('mean_absolute_estimate_error_percentage') is None else _number(estimate.get('mean_absolute_estimate_error_percentage')) * 100)}%",
            f"- Overrun rate: {_fmt(None if estimate.get('overrun_rate') is None else _number(estimate.get('overrun_rate')) * 100)}%",
            f"- Underrun rate: {_fmt(None if estimate.get('underrun_rate') is None else _number(estimate.get('underrun_rate')) * 100)}%",
            "",
            "## Capacity Analysis",
            "",
            f"- Total hours invested: {_fmt(capacity.get('total_hours_invested'))}",
            f"- Average remediation effort: {_fmt(capacity.get('average_remediation_effort'))}",
            f"- Median remediation effort: {_fmt(capacity.get('median_remediation_effort'))}",
            f"- Active effort load: {_fmt(capacity.get('active_effort_load'))}",
            f"- Completed effort load: {_fmt(capacity.get('completed_effort_load'))}",
            "",
            "## Forecasts",
            "",
            f"- Model: {forecasts.get('model')}",
            f"- Expected risk reduction per engineer-month: {_fmt(forecasts.get('expected_risk_reduction_per_engineer_month'))}",
            f"- Expected throughput per engineer-month: {_fmt(forecasts.get('expected_portfolio_throughput_per_engineer_month'))}",
            f"- Projected remediation capacity per engineer-month: {_fmt(forecasts.get('projected_remediation_capacity_per_engineer_month'))}",
            "",
            "## Recommendations",
            "",
        ]
    )
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_fallback_roi_artifacts(
    report: Mapping[str, Any], *, json_path: Path | str, markdown_path: Path | str
) -> tuple[Path, Path]:
    json_out, markdown_out = Path(json_path), Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_fallback_roi_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"{path} root must be a JSON object")
    return dict(raw)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effectiveness", type=Path, default=DEFAULT_EFFECTIVENESS_PATH)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = build_fallback_roi_report(_load(args.effectiveness), _load(args.registry))
        json_out, markdown_out = write_fallback_roi_artifacts(
            report, json_path=args.json_out, markdown_path=args.md_out
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback ROI report failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback ROI: {report['status']} confidence={report['confidence']['level']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
