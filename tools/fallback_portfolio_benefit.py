#!/usr/bin/env python3
"""Aggregate BP10 remediation outcomes into advisory portfolio metrics."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
DEFAULT_EFFECTIVENESS_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_effectiveness.json"
DEFAULT_JSON_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_portfolio_benefit_report.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_portfolio_benefit_report.md"

ACTIVE_STATUSES = {"proposed", "accepted", "in_progress"}
STALE_AFTER_DAYS = 30
LONG_RUNNING_AFTER_DAYS = 90
MINIMUM_OBSERVATION_COUNT = 3
OWNER_DIMENSIONS = {"owner_bucket", "selection_owner", "content_owner"}
FAMILY_DIMENSIONS = {"diegetic_family", "realization_family"}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _outcome_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "remediation_id": str(row.get("remediation_id") or ""),
        "contributor": str(row.get("contributor") or ""),
        "dimension": str(row.get("dimension") or ""),
        "effectiveness_classification": str(row.get("effectiveness_classification") or "unchanged"),
        "risk_reduction": _number(row.get("absolute_risk_reduction")),
        "sustained_improvement": bool(row.get("sustained_improvement")),
    }


def _impact_rows(completed: Sequence[Mapping[str, Any]], dimensions: set[str]) -> list[dict[str, Any]]:
    aggregate: dict[tuple[str, str], dict[str, Any]] = {}
    for row in completed:
        dimension = str(row.get("dimension") or "")
        if dimension not in dimensions:
            continue
        contributor = str(row.get("contributor") or "")
        key = (dimension, contributor)
        target = aggregate.setdefault(
            key,
            {
                "dimension": dimension,
                "contributor": contributor,
                "completed_remediations": 0,
                "cumulative_risk_reduction": 0.0,
                "sustained_improvements": 0,
            },
        )
        target["completed_remediations"] += 1
        target["cumulative_risk_reduction"] += _number(row.get("absolute_risk_reduction"))
        target["sustained_improvements"] += int(bool(row.get("sustained_improvement")))
    return sorted(
        (item for item in aggregate.values() if item["cumulative_risk_reduction"] > 0),
        key=lambda item: (
            -item["cumulative_risk_reduction"],
            -item["sustained_improvements"],
            item["dimension"],
            item["contributor"],
        ),
    )


def _confidence(entries: Sequence[Mapping[str, Any]], completed: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    depths = [
        int(row.get("evidence", {}).get("risk_snapshot_count") or 0)
        for row in entries
        if isinstance(row.get("evidence"), Mapping)
    ]
    average_depth = statistics.fmean(depths) if depths else 0.0
    history_length = max(depths, default=0)
    sustained_count = sum(bool(row.get("sustained_improvement")) for row in completed)
    sustained_rate = sustained_count / len(completed) if completed else 0.0
    observation_points = 2 if average_depth >= 5 else (1 if average_depth >= 3 else 0)
    history_points = 2 if history_length >= 5 else (1 if history_length >= 3 else 0)
    sustained_points = 2 if sustained_count and sustained_rate >= 0.5 else (1 if sustained_count else 0)
    score = observation_points + history_points + sustained_points
    level = "high" if score >= 5 else ("medium" if score >= 3 else "low")
    return {
        "level": level,
        "score": score,
        "maximum_score": 6,
        "average_observation_depth": average_depth,
        "history_length_snapshots": history_length,
        "sustained_improvement_count": sustained_count,
        "sustained_improvement_rate": sustained_rate,
        "factors": {
            "observation_depth_points": observation_points,
            "history_length_points": history_points,
            "sustained_evidence_points": sustained_points,
        },
        "thresholds": {
            "low": "0-2 points",
            "medium": "3-4 points",
            "high": "5-6 points",
            "observation_depth": "1 point at average >=3; 2 at >=5",
            "history_length": "1 point at >=3 snapshots; 2 at >=5",
            "sustained_evidence": "1 point for any sustained result; 2 when >=50% of completed work is sustained",
        },
    }


def build_portfolio_benefit_report(
    effectiveness_report: Mapping[str, Any], *, as_of_timestamp: str
) -> dict[str, Any]:
    raw_entries = effectiveness_report.get("remediations")
    entries = [row for row in raw_entries if isinstance(row, Mapping)] if isinstance(raw_entries, list) else []
    entries = sorted(entries, key=lambda row: (str(row.get("remediation_id")), str(row.get("dimension")), str(row.get("contributor"))))
    completed = [row for row in entries if row.get("status") == "completed"]
    active = [row for row in entries if row.get("status") in ACTIVE_STATUSES]
    abandoned = [row for row in entries if row.get("status") == "abandoned"]
    reductions = [_number(row.get("absolute_risk_reduction")) for row in completed if row.get("absolute_risk_reduction") is not None]
    cumulative = sum(reductions)
    average = statistics.fmean(reductions) if reductions else 0.0
    median = statistics.median(reductions) if reductions else 0.0
    outcome_rows = [
        _outcome_row(row) for row in completed if row.get("absolute_risk_reduction") is not None
    ]
    largest = sorted(outcome_rows, key=lambda row: (-row["risk_reduction"], row["remediation_id"]))
    smallest = sorted(outcome_rows, key=lambda row: (row["risk_reduction"], row["remediation_id"]))
    distribution = {
        classification: sum(row.get("effectiveness_classification") == classification for row in entries)
        for classification in ("resolved", "improved", "unchanged", "regressed")
    }
    risk_points_removed = sum(max(0.0, value) for value in reductions)
    regression_count = sum(row.get("effectiveness_classification") == "regressed" for row in completed)
    successful_count = sum(
        row.get("effectiveness_classification") in {"resolved", "improved"} for row in completed
    )
    as_of = _timestamp(as_of_timestamp) or datetime.now(timezone.utc)
    stale: list[dict[str, Any]] = []
    long_running: list[dict[str, Any]] = []
    lacking_closure: list[dict[str, Any]] = []
    insufficient: list[dict[str, Any]] = []
    for row in entries:
        opened = _timestamp(row.get("opened_timestamp"))
        age_days = max(0.0, (as_of - opened).total_seconds() / 86400) if opened is not None else None
        finding = {
            "remediation_id": str(row.get("remediation_id") or ""),
            "contributor": str(row.get("contributor") or ""),
            "dimension": str(row.get("dimension") or ""),
            "status": str(row.get("status") or ""),
            "age_days": age_days,
        }
        if row.get("status") in ACTIVE_STATUSES and age_days is not None and age_days >= STALE_AFTER_DAYS:
            stale.append({**finding, "reason": f"active for at least {STALE_AFTER_DAYS} days"})
        if row.get("status") in ACTIVE_STATUSES and age_days is not None and age_days >= LONG_RUNNING_AFTER_DAYS:
            long_running.append({**finding, "reason": f"active for at least {LONG_RUNNING_AFTER_DAYS} days"})
        if row.get("status") == "completed" and (
            not row.get("closed_timestamp") or row.get("completion_risk") is None
        ):
            lacking_closure.append({**finding, "reason": "missing closure timestamp or completion risk"})
        evidence = row.get("evidence") if isinstance(row.get("evidence"), Mapping) else {}
        observation_count = int(evidence.get("risk_snapshot_count") or 0)
        if observation_count < MINIMUM_OBSERVATION_COUNT:
            insufficient.append(
                {**finding, "observation_count": observation_count, "reason": f"fewer than {MINIMUM_OBSERVATION_COUNT} risk snapshots"}
            )
    for rows in (stale, long_running, lacking_closure, insufficient):
        rows.sort(key=lambda row: (row["remediation_id"], row["dimension"], row["contributor"]))
    confidence = _confidence(entries, completed)
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "empty_portfolio" if not entries else "ok",
        "as_of_timestamp": as_of_timestamp,
        "thresholds": {
            "stale_after_days": STALE_AFTER_DAYS,
            "long_running_after_days": LONG_RUNNING_AFTER_DAYS,
            "minimum_observation_count": MINIMUM_OBSERVATION_COUNT,
        },
        "portfolio_status": {
            "total_remediations": len(entries),
            "completed_remediations": len(completed),
            "active_remediations": len(active),
            "abandoned_remediations": len(abandoned),
        },
        "risk_reduction": {
            "cumulative_risk_reduction": cumulative,
            "average_risk_reduction": average,
            "median_risk_reduction": median,
            "largest_reductions": largest,
            "smallest_reductions": smallest,
        },
        "effectiveness_distribution": distribution,
        "engineering_yield": {
            "risk_points_removed": risk_points_removed,
            "risk_points_removed_per_completed_remediation": risk_points_removed / len(completed) if completed else 0.0,
            "sustained_improvements": sum(bool(row.get("sustained_improvement")) for row in completed),
            "regression_rate": regression_count / len(completed) if completed else 0.0,
            "successful_outcome_rate": (
                successful_count / len(completed) if completed else 0.0
            ),
        },
        "contributor_impact": {
            "fallback_kinds": _impact_rows(completed, {"fallback_kind"}),
            "owners": _impact_rows(completed, OWNER_DIMENSIONS),
            "routes": _impact_rows(completed, {"route_kind"}),
            "families": _impact_rows(completed, FAMILY_DIMENSIONS),
        },
        "governance_findings": {
            "stale_remediations": stale,
            "long_running_remediations": long_running,
            "lacking_closure_evidence": lacking_closure,
            "insufficient_observations": insufficient,
        },
        "confidence": confidence,
        "recommendations": (
            ["Register and observe remediation outcomes before interpreting portfolio benefit."]
            if not entries
            else [
                "Review regressions and closure-evidence gaps before using portfolio yield for planning.",
                "Increase post-completion observation depth until portfolio confidence reaches high.",
            ]
        ),
    }


def _format(value: Any) -> str:
    number = _number(value)
    return str(int(number)) if number.is_integer() else f"{number:.2f}"


def _impact_section(impact: Mapping[str, Any]) -> list[str]:
    lines = [
        "## Contributor Impact",
        "",
        "| Group | Dimension | Contributor | Completed | Risk Reduction | Sustained |",
        "|---|---|---|---:|---:|---:|",
    ]
    found = False
    for group in ("fallback_kinds", "owners", "routes", "families"):
        rows = impact.get(group) if isinstance(impact.get(group), list) else []
        for row in rows:
            found = True
            lines.append(
                f"| `{group}` | `{row.get('dimension')}` | `{row.get('contributor')}` | "
                f"{row.get('completed_remediations')} | {_format(row.get('cumulative_risk_reduction'))} | "
                f"{row.get('sustained_improvements')} |"
            )
    if not found:
        lines.append("| _none_ | - | - | 0 | 0 | 0 |")
    return lines


def _governance_section(findings: Mapping[str, Any]) -> list[str]:
    lines = [
        "## Governance Findings",
        "",
        "| Finding | Remediation | Contributor | Status | Age Days | Reason |",
        "|---|---|---|---|---:|---|",
    ]
    found = False
    for category in ("stale_remediations", "long_running_remediations", "lacking_closure_evidence", "insufficient_observations"):
        rows = findings.get(category) if isinstance(findings.get(category), list) else []
        for row in rows:
            found = True
            age = "n/a" if row.get("age_days") is None else f"{_number(row.get('age_days')):.1f}"
            lines.append(
                f"| `{category}` | `{row.get('remediation_id')}` | "
                f"`{row.get('dimension')}/{row.get('contributor')}` | `{row.get('status')}` | {age} | {row.get('reason')} |"
            )
    if not found:
        lines.append("| _none_ | - | - | - | - | No governance findings. |")
    return lines


def render_portfolio_benefit_markdown(report: Mapping[str, Any]) -> str:
    portfolio = report.get("portfolio_status") if isinstance(report.get("portfolio_status"), Mapping) else {}
    risk = report.get("risk_reduction") if isinstance(report.get("risk_reduction"), Mapping) else {}
    distribution = report.get("effectiveness_distribution") if isinstance(report.get("effectiveness_distribution"), Mapping) else {}
    engineering = report.get("engineering_yield") if isinstance(report.get("engineering_yield"), Mapping) else {}
    confidence = report.get("confidence") if isinstance(report.get("confidence"), Mapping) else {}
    lines = [
        "# Fallback Portfolio Engineering Benefit",
        "",
        "> Advisory-only portfolio aggregation over BP10 remediation effectiveness results.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Portfolio confidence: `{confidence.get('level', 'low')}` ({confidence.get('score', 0)}/6)",
        f"- Total remediations: {portfolio.get('total_remediations', 0)}",
        f"- Net risk reduction: {_format(risk.get('cumulative_risk_reduction'))}",
        f"- Gross risk points removed: {_format(engineering.get('risk_points_removed'))}",
        "",
        "## Portfolio Status",
        "",
        f"- Completed: {portfolio.get('completed_remediations', 0)}",
        f"- Active: {portfolio.get('active_remediations', 0)}",
        f"- Abandoned: {portfolio.get('abandoned_remediations', 0)}",
        "",
        "## Risk Reduction",
        "",
        f"- Cumulative: {_format(risk.get('cumulative_risk_reduction'))}",
        f"- Average: {_format(risk.get('average_risk_reduction'))}",
        f"- Median: {_format(risk.get('median_risk_reduction'))}",
        f"- Largest: {', '.join(f'`{row.get("remediation_id")}` ({_format(row.get("risk_reduction"))})' for row in risk.get('largest_reductions', [])[:5]) or 'none'}",
        f"- Smallest: {', '.join(f'`{row.get("remediation_id")}` ({_format(row.get("risk_reduction"))})' for row in risk.get('smallest_reductions', [])[:5]) or 'none'}",
        "",
        "## Effectiveness Distribution",
        "",
        f"- Resolved: {distribution.get('resolved', 0)}",
        f"- Improved: {distribution.get('improved', 0)}",
        f"- Unchanged: {distribution.get('unchanged', 0)}",
        f"- Regressed: {distribution.get('regressed', 0)}",
        "",
        "## Engineering Yield",
        "",
        f"- Risk points removed: {_format(engineering.get('risk_points_removed'))}",
        f"- Removed per completed remediation: {_format(engineering.get('risk_points_removed_per_completed_remediation'))}",
        f"- Sustained improvements: {engineering.get('sustained_improvements', 0)}",
        f"- Regression rate: {_number(engineering.get('regression_rate')) * 100:.1f}%",
        f"- Successful outcome rate: {_number(engineering.get('successful_outcome_rate')) * 100:.1f}%",
        "",
    ]
    lines.extend(_impact_section(report.get("contributor_impact", {})))
    lines.extend([""] + _governance_section(report.get("governance_findings", {})))
    lines.extend(
        [
            "",
            "### Confidence Model",
            "",
            "- Low: 0-2 points; medium: 3-4; high: 5-6.",
            "- Observation depth and history length contribute up to two points each.",
            "- Sustained-improvement evidence contributes up to two points.",
            "",
            "## Recommendations",
            "",
        ]
    )
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_portfolio_benefit_artifacts(
    report: Mapping[str, Any], *, json_path: Path | str, markdown_path: Path | str
) -> tuple[Path, Path]:
    json_out, markdown_out = Path(json_path), Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_portfolio_benefit_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effectiveness", type=Path, default=DEFAULT_EFFECTIVENESS_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.effectiveness.read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping):
            raise ValueError("effectiveness report root must be a JSON object")
        report = build_portfolio_benefit_report(raw, as_of_timestamp=args.as_of)
        json_out, markdown_out = write_portfolio_benefit_artifacts(
            report, json_path=args.json_out, markdown_path=args.md_out
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback portfolio benefit failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback portfolio benefit: {report['status']} confidence={report['confidence']['level']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
