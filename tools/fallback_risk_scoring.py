#!/usr/bin/env python3
"""Build explainable advisory structural fallback risk scores."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.fallback_incidence_anomalies import analyze_fallback_incidence_anomalies  # noqa: E402
from tools.fallback_incidence_trends import analyze_fallback_incidence_history, load_history  # noqa: E402
from tools.fallback_recurrence import analyze_fallback_recurrence  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_HISTORY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_incidence_history.json"
DEFAULT_JSON_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_risk_report.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_risk_report.md"

FACTOR_MAXIMUMS = {
    "frequency_contribution": 20.0,
    "recurrence_strength": 25.0,
    "anomaly_participation": 15.0,
    "anomaly_severity": 20.0,
    "trend_direction": 20.0,
}
RECURRENCE_POINTS = {"transient": 0.0, "recurring": 8.0, "persistent": 16.0, "dominant": 25.0}
ANOMALY_SEVERITY_POINTS = {"none": 0.0, "info": 4.0, "watch": 8.0, "warning": 14.0, "critical": 20.0}
ANOMALY_PARTICIPATION_POINTS = 5.0
TREND_POINTS = {"insufficient_history": 0.0, "improving": 0.0, "stable": 5.0, "worsening": 20.0}
RISK_THRESHOLDS = (
    (80.0, "critical"),
    (60.0, "high"),
    (40.0, "elevated"),
    (25.0, "moderate"),
    (10.0, "low"),
    (0.0, "negligible"),
)
ANOMALY_DIMENSIONS = {
    "fallback_kind": "fallback_kind",
    "route": "route_kind",
    "owner_bucket": "owner_bucket",
    "selection_owner": "selection_owner",
    "content_owner": "content_owner",
}
OWNER_DIMENSIONS = {"owner_bucket", "selection_owner", "content_owner"}
FAMILY_DIMENSIONS = {"diegetic_family", "realization_family"}
RISK_RANK = {"critical": 0, "high": 1, "elevated": 2, "moderate": 3, "low": 4, "negligible": 5}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def classify_risk(score: float) -> str:
    for minimum, classification in RISK_THRESHOLDS:
        if score >= minimum:
            return classification
    return "negligible"


def _anomaly_index(anomaly_report: Mapping[str, Any]) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    index: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    anomalies = anomaly_report.get("anomalies")
    if not isinstance(anomalies, list):
        return index
    for anomaly in anomalies:
        if not isinstance(anomaly, Mapping) or not anomaly.get("name"):
            continue
        dimension = ANOMALY_DIMENSIONS.get(str(anomaly.get("category")))
        if dimension:
            index.setdefault((dimension, str(anomaly.get("name"))), []).append(anomaly)
    return index


def _risk_sort(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -_number(row.get("risk_score")),
        RISK_RANK[str(row.get("risk_classification"))],
        -int(_number(row.get("anomaly_evidence", {}).get("participation_count"))),
        -_number(row.get("incidence_evidence", {}).get("cumulative_contribution")),
        str(row.get("dimension")),
        str(row.get("name")),
    )


def build_fallback_risk_report(
    trend_report: Mapping[str, Any],
    anomaly_report: Mapping[str, Any],
    recurrence_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Combine BP5, BP6, and BP7 outputs without altering their thresholds."""
    trend = str(trend_report.get("classification") or "insufficient_history")
    anomaly_index = _anomaly_index(anomaly_report)
    entities = recurrence_report.get("entities")
    entities = entities if isinstance(entities, Mapping) else {}
    dimension_totals = {
        str(dimension): sum(
            _number(row.get("cumulative_incidence_contribution"))
            for row in rows
            if isinstance(row, Mapping)
        )
        for dimension, rows in entities.items()
        if isinstance(rows, list)
    }
    scored: list[dict[str, Any]] = []
    for dimension in sorted(entities):
        rows = entities.get(dimension)
        if not isinstance(rows, list):
            continue
        for entity in rows:
            if not isinstance(entity, Mapping):
                continue
            name = str(entity.get("name"))
            cumulative = _number(entity.get("cumulative_incidence_contribution"))
            total = dimension_totals.get(str(dimension), 0.0)
            share = cumulative / total if total else 0.0
            recurrence_classification = str(entity.get("classification") or "transient")
            matching_anomalies = anomaly_index.get((str(dimension), name), [])
            severities = sorted(
                {str(row.get("severity") or "none") for row in matching_anomalies},
                key=lambda severity: -ANOMALY_SEVERITY_POINTS.get(severity, 0.0),
            )
            max_severity = severities[0] if severities else "none"
            factor_points = {
                "frequency_contribution": round(share * FACTOR_MAXIMUMS["frequency_contribution"], 4),
                "recurrence_strength": RECURRENCE_POINTS.get(recurrence_classification, 0.0),
                "anomaly_participation": min(
                    FACTOR_MAXIMUMS["anomaly_participation"],
                    len(matching_anomalies) * ANOMALY_PARTICIPATION_POINTS,
                ),
                "anomaly_severity": ANOMALY_SEVERITY_POINTS.get(max_severity, 0.0),
                "trend_direction": TREND_POINTS.get(trend, 0.0),
            }
            score = round(sum(factor_points.values()), 4)
            scored.append(
                {
                    "dimension": str(dimension),
                    "name": name,
                    "risk_score": score,
                    "risk_classification": classify_risk(score),
                    "contributing_factors": {
                        factor: {
                            "points": points,
                            "maximum_points": FACTOR_MAXIMUMS[factor],
                        }
                        for factor, points in factor_points.items()
                    },
                    "incidence_evidence": {
                        "cumulative_contribution": cumulative,
                        "dimension_total_contribution": total,
                        "frequency_contribution_percentage": share,
                    },
                    "recurrence_evidence": {
                        "classification": recurrence_classification,
                        "snapshot_appearances": int(entity.get("snapshot_appearances") or 0),
                        "consecutive_appearances": int(entity.get("consecutive_appearances") or 0),
                        "appearance_percentage": _number(entity.get("appearance_percentage")),
                        "first_seen": entity.get("first_seen"),
                        "most_recent_seen": entity.get("most_recent_seen"),
                    },
                    "anomaly_evidence": {
                        "participation_count": len(matching_anomalies),
                        "severities": severities,
                        "maximum_severity": max_severity,
                        "anomalies": [dict(row) for row in matching_anomalies],
                    },
                    "trend_evidence": {
                        "classification": trend,
                        "points": factor_points["trend_direction"],
                    },
                }
            )
    scored.sort(key=_risk_sort)
    ranked = {
        "all": scored,
        "fallback_kinds": [row for row in scored if row["dimension"] == "fallback_kind"],
        "owners": [row for row in scored if row["dimension"] in OWNER_DIMENSIONS],
        "routes": [row for row in scored if row["dimension"] == "route_kind"],
        "families": [row for row in scored if row["dimension"] in FAMILY_DIMENSIONS],
    }
    highest = scored[0] if scored else None
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "no_history" if recurrence_report.get("status") == "no_history" else "ok",
        "snapshot_count": int(recurrence_report.get("snapshot_count") or 0),
        "risk_model": {
            "maximum_score": 100.0,
            "factor_maximums": dict(FACTOR_MAXIMUMS),
            "recurrence_points": dict(RECURRENCE_POINTS),
            "anomaly_participation_points_each": ANOMALY_PARTICIPATION_POINTS,
            "anomaly_severity_points": dict(ANOMALY_SEVERITY_POINTS),
            "trend_points": dict(TREND_POINTS),
            "classification_thresholds": {
                "negligible": "0 to <10",
                "low": "10 to <25",
                "moderate": "25 to <40",
                "elevated": "40 to <60",
                "high": "60 to <80",
                "critical": "80 to 100",
            },
        },
        "source_status": {
            "bp5_trend": trend,
            "bp6_anomalies": anomaly_report.get("status"),
            "bp7_recurrence": recurrence_report.get("status"),
        },
        "ranked_hotspots": ranked,
        "highest_risk_contributor": highest,
        "recommendations": (
            ["Collect fallback-incidence history before interpreting structural risk."]
            if not scored
            else [
                "Review elevated, high, and critical contributors using their factor-level evidence.",
                "Treat scores as maintenance prioritization signals, not runtime or replay acceptance gates.",
            ]
        ),
    }


def analyze_fallback_risk(history: Mapping[str, Any]) -> dict[str, Any]:
    return build_fallback_risk_report(
        analyze_fallback_incidence_history(history),
        analyze_fallback_incidence_anomalies(history),
        analyze_fallback_recurrence(history),
    )


def _risk_rows(title: str, rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |",
        "|---:|---|---:|---|---|---:|---|---:|---|---|",
    ]
    if not rows:
        lines.append("| - | _none_ | 0 | - | - | 0.0% | - | 0 | - | - |")
        return lines
    for rank, row in enumerate(rows, 1):
        incidence = row.get("incidence_evidence", {})
        recurrence = row.get("recurrence_evidence", {})
        anomaly = row.get("anomaly_evidence", {})
        trend = row.get("trend_evidence", {})
        lines.append(
            f"| {rank} | `{row.get('risk_classification')}` | {row.get('risk_score')} | "
            f"`{row.get('dimension')}` | `{row.get('name')}` | "
            f"{_number(incidence.get('frequency_contribution_percentage')) * 100:.1f}% | "
            f"`{recurrence.get('classification')}` | {anomaly.get('participation_count', 0)} | "
            f"`{anomaly.get('maximum_severity')}` | `{trend.get('classification')}` |"
        )
    return lines


def render_fallback_risk_markdown(report: Mapping[str, Any]) -> str:
    model = report.get("risk_model") if isinstance(report.get("risk_model"), Mapping) else {}
    ranked = report.get("ranked_hotspots") if isinstance(report.get("ranked_hotspots"), Mapping) else {}
    source = report.get("source_status") if isinstance(report.get("source_status"), Mapping) else {}
    highest = report.get("highest_risk_contributor")
    lines = [
        "# Structural Fallback Risk Report",
        "",
        "> Advisory-only maintenance risk scoring. Scores do not affect runtime or replay acceptance.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Snapshots analyzed: {report.get('snapshot_count', 0)}",
        f"- Highest-risk contributor: `{highest.get('dimension')}/{highest.get('name')}` at {highest.get('risk_score')} (`{highest.get('risk_classification')}`)" if isinstance(highest, Mapping) else "- Highest-risk contributor: none",
        f"- Source signals: BP5 `{source.get('bp5_trend')}`, BP6 `{source.get('bp6_anomalies')}`, BP7 `{source.get('bp7_recurrence')}`.",
        "",
        "## Risk Model",
        "",
        "Score = frequency contribution (20) + recurrence strength (25) + anomaly participation (15) + anomaly severity (20) + trend direction (20).",
        "",
        "- Frequency: within-dimension cumulative incidence share, scaled to 20 points.",
        "- Recurrence: transient 0, recurring 8, persistent 16, dominant 25.",
        "- Anomaly participation: 5 points per matching named anomaly, capped at 15.",
        "- Anomaly severity: none 0, info 4, watch 8, warning 14, critical 20.",
        "- Trend: insufficient/improving 0, stable 5, worsening 20.",
        "- Classes: negligible <10; low <25; moderate <40; elevated <60; high <80; critical >=80.",
        f"- Maximum score: {model.get('maximum_score', 100)}.",
        "",
    ]
    lines.extend(_risk_rows("Ranked Hotspots", ranked.get("all", [])))
    lines.extend([""] + _risk_rows("Highest-Risk Kinds", ranked.get("fallback_kinds", [])))
    lines.extend([""] + _risk_rows("Highest-Risk Owners", ranked.get("owners", [])))
    lines.extend([""] + _risk_rows("Highest-Risk Routes", ranked.get("routes", [])))
    lines.extend([""] + _risk_rows("Highest-Risk Families", ranked.get("families", [])))
    lines.extend(["", "## Recommendations", ""])
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_fallback_risk_artifacts(
    report: Mapping[str, Any], *, json_path: Path | str, markdown_path: Path | str
) -> tuple[Path, Path]:
    json_out, markdown_out = Path(json_path), Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_fallback_risk_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = analyze_fallback_risk(load_history(args.history))
        json_out, markdown_out = write_fallback_risk_artifacts(
            report, json_path=args.json_out, markdown_path=args.md_out
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback risk report failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback risk: {report['status']} contributors={len(report['ranked_hotspots']['all'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
