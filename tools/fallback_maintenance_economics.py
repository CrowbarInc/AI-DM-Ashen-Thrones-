#!/usr/bin/env python3
"""Compose BP5-BP12 artifacts into fallback maintenance economics."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
DEFAULT_ARTIFACT_DIR = ROOT / "artifacts" / "golden_replay"
DEFAULT_JSON_PATH = DEFAULT_ARTIFACT_DIR / "fallback_maintenance_economics.json"
DEFAULT_SUMMARY_PATH = DEFAULT_ARTIFACT_DIR / "fallback_maintenance_economics_summary.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_ARTIFACT_DIR / "fallback_maintenance_economics.md"

BURDEN_THRESHOLDS = (
    (75.0, "critical"),
    (50.0, "high"),
    (30.0, "elevated"),
    (15.0, "moderate"),
    (5.0, "low"),
    (0.0, "negligible"),
)
PRIORITY_WEIGHTS = {"monitor": 1, "investigate": 2, "schedule": 3, "prioritize": 4, "urgent": 5}
RECURRENCE_WEIGHTS = {"transient": 0, "recurring": 1, "persistent": 2, "dominant": 3}
TREND_WEIGHTS = {"insufficient_history": 0, "improving": 0, "stable": 2, "worsening": 6}
ANOMALY_SEVERITY_WEIGHTS = {"none": 0, "info": 2, "watch": 4, "warning": 7, "critical": 10}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def classify_burden(score: float) -> str:
    for minimum, classification in BURDEN_THRESHOLDS:
        if score >= minimum:
            return classification
    return "negligible"


def _list(mapping: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = mapping.get(key)
    return [row for row in value if isinstance(row, Mapping)] if isinstance(value, list) else []


def _recurrence_rows(recurrence: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    entities = _mapping(recurrence.get("entities"))
    return [
        row
        for dimension in sorted(entities)
        for row in _list(entities, dimension)
        if str(row.get("classification")) != "transient"
    ]


def _queue_index(queue: Mapping[str, Any]) -> dict[tuple[str, str], Mapping[str, Any]]:
    return {
        (str(row.get("dimension")), str(row.get("contributor"))): row
        for row in _list(queue, "queue")
        if row.get("dimension") and row.get("contributor")
    }


def _hotspots(risk: Mapping[str, Any], queue: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    ranked = _mapping(risk.get("ranked_hotspots"))
    queue_rows = _queue_index(queue)

    def rows(key: str) -> list[dict[str, Any]]:
        results = []
        for row in _list(ranked, key):
            dimension, name = str(row.get("dimension")), str(row.get("name"))
            queued = queue_rows.get((dimension, name), {})
            recurrence = _mapping(row.get("recurrence_evidence"))
            anomaly = _mapping(row.get("anomaly_evidence"))
            results.append(
                {
                    "dimension": dimension,
                    "contributor": name,
                    "risk_score": _number(row.get("risk_score")),
                    "risk_classification": row.get("risk_classification"),
                    "priority": queued.get("priority", "monitor"),
                    "recurrence": recurrence.get("classification", "transient"),
                    "anomaly_count": int(anomaly.get("participation_count") or 0),
                }
            )
        return sorted(
            results,
            key=lambda item: (
                -item["risk_score"],
                -PRIORITY_WEIGHTS.get(str(item["priority"]), 0),
                item["dimension"],
                item["contributor"],
            ),
        )

    return {
        "fallback_kinds": rows("fallback_kinds"),
        "owners": rows("owners"),
        "routes": rows("routes"),
        "families": rows("families"),
    }


def _confidence(
    recurrence: Mapping[str, Any], portfolio: Mapping[str, Any], roi: Mapping[str, Any]
) -> dict[str, Any]:
    history_depth = int(recurrence.get("snapshot_count") or 0)
    portfolio_status = _mapping(portfolio.get("portfolio_status"))
    remediation_count = int(portfolio_status.get("total_remediations") or 0)
    roi_confidence = _mapping(roi.get("confidence"))
    effort_coverage = _number(roi_confidence.get("effort_data_coverage"))
    history_points = 2 if history_depth >= 10 else (1 if history_depth >= 5 else 0)
    remediation_points = 2 if remediation_count >= 5 else (1 if remediation_count >= 2 else 0)
    effort_points = 2 if effort_coverage >= 0.8 else (1 if effort_coverage >= 0.4 else 0)
    score = history_points + remediation_points + effort_points
    level = "high" if score >= 5 else ("medium" if score >= 3 else "low")
    return {
        "level": level,
        "score": score,
        "maximum_score": 6,
        "history_depth": history_depth,
        "remediation_count": remediation_count,
        "effort_coverage": effort_coverage,
        "factors": {
            "history_depth_points": history_points,
            "remediation_count_points": remediation_points,
            "effort_coverage_points": effort_points,
        },
        "thresholds": {
            "low": "0-2 points",
            "medium": "3-4 points",
            "high": "5-6 points",
            "history_depth": "1 point at 5 snapshots; 2 at 10",
            "remediation_count": "1 point at 2 remediations; 2 at 5",
            "effort_coverage": "1 point at 40%; 2 at 80%",
        },
    }


def build_fallback_maintenance_economics(
    *,
    trends: Mapping[str, Any],
    anomalies: Mapping[str, Any],
    recurrence: Mapping[str, Any],
    risk: Mapping[str, Any],
    queue: Mapping[str, Any],
    effectiveness: Mapping[str, Any],
    portfolio: Mapping[str, Any],
    roi: Mapping[str, Any],
) -> dict[str, Any]:
    ranked = _mapping(risk.get("ranked_hotspots"))
    risk_rows = _list(ranked, "all")
    unresolved_rows = [
        row for row in risk_rows if str(row.get("risk_classification")) != "negligible"
    ]
    queue_rows = _list(queue, "queue")
    recurring_rows = _recurrence_rows(recurrence)
    anomaly_rows = _list(anomalies, "anomalies")
    unresolved_risk = sum(
        _number(row.get("risk_score"))
        for row in unresolved_rows
    )
    active_remediation_burden = sum(
        PRIORITY_WEIGHTS.get(str(row.get("priority")), 0) for row in queue_rows
    )
    recurring_hotspot_burden = sum(
        RECURRENCE_WEIGHTS.get(str(row.get("classification")), 0) for row in recurring_rows
    )
    trend = str(trends.get("classification") or recurrence.get("trend_classification") or "insufficient_history")
    severity = str(anomalies.get("severity") or "none")
    instability_burden = (
        TREND_WEIGHTS.get(trend, 0)
        + ANOMALY_SEVERITY_WEIGHTS.get(severity, 0)
        + min(4, len(anomaly_rows))
    )
    components = {
        "unresolved_risk_points": min(40.0, unresolved_risk / 10.0),
        "active_remediation_points": min(20.0, float(active_remediation_burden)),
        "recurring_hotspot_points": min(20.0, float(recurring_hotspot_burden)),
        "instability_points": min(20.0, float(instability_burden)),
    }
    burden_score = sum(components.values())
    portfolio_roi = _mapping(roi.get("portfolio_roi"))
    capacity = _mapping(roi.get("capacity_analysis"))
    risk_per_hour = portfolio_roi.get("risk_points_removed_per_hour")
    hours = _number(capacity.get("total_hours_invested"))
    backlog_risk = sum(_number(row.get("risk_score")) for row in queue_rows)
    recurring_counts = {
        classification: sum(str(row.get("classification")) == classification for row in recurring_rows)
        for classification in ("recurring", "persistent", "dominant")
    }
    hotspots = _hotspots(risk, queue)
    confidence = _confidence(recurrence, portfolio, roi)
    source_status = {
        "bp5_trends": trend,
        "bp6_anomalies": anomalies.get("status", "missing"),
        "bp7_recurrence": recurrence.get("status", "missing"),
        "bp8_risk": risk.get("status", "missing"),
        "bp9_queue": queue.get("status", "missing"),
        "bp10_effectiveness": effectiveness.get("status", "missing"),
        "bp11_portfolio": portfolio.get("status", "missing"),
        "bp12_roi": roi.get("status", "missing"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "insufficient_data" if not risk_rows and not queue_rows else "ok",
        "source_status": source_status,
        "economics_model": {
            "maximum_burden_score": 100.0,
            "component_maximums": {
                "unresolved_risk": 40,
                "active_remediation": 20,
                "recurring_hotspots": 20,
                "trend_and_anomalies": 20,
            },
            "classification_thresholds": {
                "negligible": "0 to <5",
                "low": "5 to <15",
                "moderate": "15 to <30",
                "elevated": "30 to <50",
                "high": "50 to <75",
                "critical": "75 to 100",
            },
        },
        "maintenance_burden": {
            "score": burden_score,
            "classification": classify_burden(burden_score),
            "components": components,
            "fallback_maintenance_burden": burden_score,
            "active_remediation_burden": active_remediation_burden,
            "unresolved_risk_burden": unresolved_risk,
            "recurring_hotspot_burden": recurring_hotspot_burden,
            "instability_burden": instability_burden,
        },
        "risk_analysis": {
            "unresolved_risk": unresolved_risk,
            "unresolved_contributor_count": len(unresolved_rows),
            "backlog_risk": backlog_risk,
            "queue_entry_count": len(queue_rows),
            "trend_classification": trend,
            "anomaly_count": len(anomaly_rows),
            "anomaly_severity": severity,
        },
        "cost_benefit": {
            "risk_removed_per_engineering_hour": risk_per_hour,
            "unresolved_risk_per_engineering_hour": unresolved_risk / hours if hours > 0 else None,
            "backlog_risk": backlog_risk,
            "remediation_efficiency": portfolio_roi.get("remediation_efficiency", "unavailable"),
            "total_hours_invested": hours,
            "portfolio_net_risk_reduction": _mapping(portfolio.get("risk_reduction")).get(
                "cumulative_risk_reduction", 0
            ),
        },
        "recurring_hotspots": {
            "counts": recurring_counts,
            "weighted_burden": recurring_hotspot_burden,
        },
        "structural_hotspots": hotspots,
        "confidence": confidence,
        "recommendations": (
            ["Collect fallback history and remediation evidence before using economics in contraction planning."]
            if confidence["level"] == "low"
            else [
                "Use the summary artifact as advisory scorecard context while preserving upstream acceptance boundaries.",
                "Prioritize high-burden hotspots with demonstrated remediation efficiency and adequate confidence.",
            ]
        ),
    }


def build_scorecard_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "ingestion_contract": "fallback_maintenance_economics_summary/v1",
        "maintenance_burden": report.get("maintenance_burden"),
        "unresolved_risk": _mapping(report.get("risk_analysis")).get("unresolved_risk", 0),
        "roi": report.get("cost_benefit"),
        "recurring_hotspots": report.get("recurring_hotspots"),
        "confidence": report.get("confidence"),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    number = _number(value)
    return str(int(number)) if number.is_integer() else f"{number:.2f}"


def _hotspot_lines(hotspots: Mapping[str, Any]) -> list[str]:
    lines = [
        "## Hotspots",
        "",
        "| Group | Contributor | Risk | Classification | Priority | Recurrence | Anomalies |",
        "|---|---|---:|---|---|---|---:|",
    ]
    found = False
    for group in ("fallback_kinds", "owners", "routes", "families"):
        for row in _list(hotspots, group)[:10]:
            found = True
            lines.append(
                f"| `{group}` | `{row.get('dimension')}/{row.get('contributor')}` | "
                f"{_fmt(row.get('risk_score'))} | `{row.get('risk_classification')}` | "
                f"`{row.get('priority')}` | `{row.get('recurrence')}` | {row.get('anomaly_count')} |"
            )
    if not found:
        lines.append("| _none_ | - | 0 | - | - | - | 0 |")
    return lines


def render_maintenance_economics_markdown(report: Mapping[str, Any]) -> str:
    burden = _mapping(report.get("maintenance_burden"))
    risk = _mapping(report.get("risk_analysis"))
    cost = _mapping(report.get("cost_benefit"))
    confidence = _mapping(report.get("confidence"))
    components = _mapping(burden.get("components"))
    lines = [
        "# Fallback Maintenance Economics",
        "",
        "> Advisory-only integration of BP5-BP12 observability and remediation economics.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Maintenance burden: {_fmt(burden.get('score'))}/100 (`{burden.get('classification')}`)",
        f"- Unresolved risk: {_fmt(risk.get('unresolved_risk'))}",
        f"- Backlog risk: {_fmt(risk.get('backlog_risk'))}",
        f"- Confidence: `{confidence.get('level')}` ({confidence.get('score')}/6)",
        "",
        "## Burden Analysis",
        "",
        f"- Unresolved-risk component: {_fmt(components.get('unresolved_risk_points'))}/40",
        f"- Active-remediation component: {_fmt(components.get('active_remediation_points'))}/20",
        f"- Recurring-hotspot component: {_fmt(components.get('recurring_hotspot_points'))}/20",
        f"- Trend/anomaly component: {_fmt(components.get('instability_points'))}/20",
        "- Classes: negligible <5; low <15; moderate <30; elevated <50; high <75; critical >=75.",
        "",
        "## Risk Analysis",
        "",
        f"- Unresolved contributors: {risk.get('unresolved_contributor_count', 0)}",
        f"- Queue entries: {risk.get('queue_entry_count', 0)}",
        f"- Trend: `{risk.get('trend_classification')}`",
        f"- Anomalies: {risk.get('anomaly_count', 0)} (`{risk.get('anomaly_severity')}`)",
        "",
        "## ROI Analysis",
        "",
        f"- Risk removed per engineering hour: {_fmt(cost.get('risk_removed_per_engineering_hour'))}",
        f"- Unresolved risk per engineering hour: {_fmt(cost.get('unresolved_risk_per_engineering_hour'))}",
        f"- Remediation efficiency: `{cost.get('remediation_efficiency')}`",
        f"- Total hours invested: {_fmt(cost.get('total_hours_invested'))}",
        "",
    ]
    lines.extend(_hotspot_lines(_mapping(report.get("structural_hotspots"))))
    lines.extend(
        [
            "",
            "## Confidence",
            "",
            "- Low: 0-2 points; medium: 3-4; high: 5-6.",
            f"- History depth: {confidence.get('history_depth', 0)} snapshots.",
            f"- Remediation count: {confidence.get('remediation_count', 0)}.",
            f"- Effort coverage: {_number(confidence.get('effort_coverage')) * 100:.1f}%.",
            "",
            "## Recommendations",
            "",
        ]
    )
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_economics_artifacts(
    report: Mapping[str, Any],
    *,
    json_path: Path | str,
    summary_path: Path | str,
    markdown_path: Path | str,
) -> tuple[Path, Path, Path]:
    json_out, summary_out, markdown_out = Path(json_path), Path(summary_path), Path(markdown_path)
    for path in (json_out, summary_out, markdown_out):
        path.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_out.write_text(
        json.dumps(build_scorecard_summary(report), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_out.write_text(render_maintenance_economics_markdown(report), encoding="utf-8")
    return json_out, summary_out, markdown_out


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"{path} root must be a JSON object")
    return dict(raw)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        directory = args.artifact_dir
        recurrence = _load(directory / "fallback_recurrence_report.json")
        report = build_fallback_maintenance_economics(
            trends={"classification": recurrence.get("trend_classification", "insufficient_history")},
            anomalies=_load(directory / "fallback_incidence_anomalies.json"),
            recurrence=recurrence,
            risk=_load(directory / "fallback_risk_report.json"),
            queue=_load(directory / "fallback_remediation_queue.json"),
            effectiveness=_load(directory / "fallback_remediation_effectiveness.json"),
            portfolio=_load(directory / "fallback_portfolio_benefit_report.json"),
            roi=_load(directory / "fallback_roi_report.json"),
        )
        json_out, summary_out, markdown_out = write_economics_artifacts(
            report,
            json_path=args.json_out,
            summary_path=args.summary_out,
            markdown_path=args.md_out,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback maintenance economics failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {json_out}")
    print(f"Wrote {summary_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback maintenance economics: {report['maintenance_burden']['classification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
