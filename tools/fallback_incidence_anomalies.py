#!/usr/bin/env python3
"""Detect advisory anomalies in BP5 fallback-incidence history."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.fallback_incidence_trends import analyze_fallback_incidence_history, load_history  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_MINIMUM_HISTORY_SNAPSHOTS = 5
DEFAULT_ROLLING_WINDOW = 10
DEFAULT_HISTORY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_incidence_history.json"
DEFAULT_JSON_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_incidence_anomalies.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_incidence_anomalies.md"

BAND_STANDARD_DEVIATIONS = 2.0
SEVERITY_THRESHOLDS = ((5.0, "critical"), (4.0, "warning"), (3.0, "watch"), (2.0, "info"))
METRIC_FLOORS = {
    "fallback_trigger_rate": 0.02,
    "fallback_turn_count": 1.0,
    "fallback_event_count": 1.0,
    "route_trigger_rate": 0.02,
    "dimension_count": 1.0,
}
NAMED_DIMENSIONS = (
    ("fallback_kind", "top_fallback_kinds", "fallback_kind"),
    ("owner_bucket", "top_owner_buckets", "owner_bucket"),
    ("selection_owner", "top_selection_owners", "selection_owner"),
    ("content_owner", "top_content_owners", "content_owner"),
)
SEVERITY_ORDER = {"critical": 0, "warning": 1, "watch": 2, "info": 3}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _stats(values: Sequence[float], *, floor: float) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values)
    mean = statistics.fmean(ordered) if ordered else 0.0
    deviation = statistics.stdev(ordered) if len(ordered) >= 2 else None
    scale = max(deviation or 0.0, floor)
    return {
        "sample_size": len(ordered),
        "mean": mean,
        "median": statistics.median(ordered) if ordered else 0.0,
        "minimum": ordered[0] if ordered else 0.0,
        "maximum": ordered[-1] if ordered else 0.0,
        "standard_deviation": deviation,
        "expected_minimum": max(0.0, mean - BAND_STANDARD_DEVIATIONS * scale),
        "expected_maximum": mean + BAND_STANDARD_DEVIATIONS * scale,
        "effective_scale": scale,
    }


def _named_counts(snapshot: Mapping[str, Any], key: str) -> dict[str, float]:
    rows = snapshot.get(key)
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("name")): _number(row.get("count"))
        for row in rows
        if isinstance(row, Mapping) and str(row.get("name") or "").strip()
    }


def _route_rates(snapshot: Mapping[str, Any]) -> dict[str, float]:
    rows = snapshot.get("route_rates")
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("route_kind")): _number(row.get("fallback_trigger_rate"))
        for row in rows
        if isinstance(row, Mapping) and str(row.get("route_kind") or "").strip()
    }


def _severity(score: float) -> str:
    for threshold, severity in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return severity
    return "info"


def _anomaly(
    *,
    category: str,
    metric: str,
    direction: str,
    current: float,
    baseline: Mapping[str, Any],
    name: str | None = None,
) -> dict[str, Any] | None:
    limit_key = "expected_maximum" if direction == "above" else "expected_minimum"
    limit = _number(baseline.get(limit_key))
    if (direction == "above" and current <= limit) or (direction == "below" and current >= limit):
        return None
    score = abs(current - _number(baseline.get("mean"))) / _number(baseline.get("effective_scale"))
    row = {
        "category": category,
        "metric": metric,
        "direction": direction,
        "current_value": current,
        "expected_minimum": _number(baseline.get("expected_minimum")),
        "expected_maximum": _number(baseline.get("expected_maximum")),
        "standardized_distance": score,
        "severity": _severity(score),
    }
    if name is not None:
        row["name"] = name
    return row


def _thresholds(minimum_history_snapshots: int, rolling_window: int) -> dict[str, Any]:
    return {
        "minimum_history_snapshots": minimum_history_snapshots,
        "rolling_window_prior_snapshots": rolling_window,
        "expected_band_standard_deviations": BAND_STANDARD_DEVIATIONS,
        "metric_scale_floors": dict(METRIC_FLOORS),
        "severity_standardized_distance": {
            "info": ">= 2 and < 3",
            "watch": ">= 3 and < 4",
            "warning": ">= 4 and < 5",
            "critical": ">= 5",
        },
    }


def analyze_fallback_incidence_anomalies(
    history: Mapping[str, Any],
    *,
    minimum_history_snapshots: int = DEFAULT_MINIMUM_HISTORY_SNAPSHOTS,
    rolling_window: int = DEFAULT_ROLLING_WINDOW,
) -> dict[str, Any]:
    """Compare the current snapshot with a rolling prior-snapshot baseline."""
    minimum = max(1, int(minimum_history_snapshots))
    window = max(minimum, int(rolling_window))
    snapshots = [item for item in history.get("snapshots", []) if isinstance(item, Mapping)]
    current = snapshots[-1] if snapshots else None
    prior = snapshots[max(0, len(snapshots) - 1 - window) : -1]
    trend = analyze_fallback_incidence_history(history, rolling_window=window).get(
        "classification", "insufficient_history"
    )
    base = {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "insufficient_history" if len(prior) < minimum else "ok",
        "snapshot_count": len(snapshots),
        "baseline_snapshot_count": len(prior),
        "thresholds": _thresholds(minimum, window),
        "trend_classification": trend,
        "stability": f"{trend} + anomaly detection suppressed" if len(prior) < minimum else "",
        "baseline": {},
        "current_snapshot": dict(current) if current is not None else None,
        "anomalies": [],
        "severity": "none",
        "recommendations": [],
    }
    if len(prior) < minimum or current is None:
        base["recommendations"] = [
            f"Collect at least {minimum} prior snapshots before interpreting anomaly signals."
        ]
        return base

    baselines = {
        metric: _stats([_number(item.get(metric)) for item in prior], floor=METRIC_FLOORS[metric])
        for metric in ("fallback_trigger_rate", "fallback_turn_count", "fallback_event_count")
    }
    anomalies: list[dict[str, Any]] = []
    for metric, category in (
        ("fallback_trigger_rate", "trigger_rate"),
        ("fallback_turn_count", "volume"),
        ("fallback_event_count", "volume"),
    ):
        for direction in ("above", "below"):
            found = _anomaly(
                category=category,
                metric=metric,
                direction=direction,
                current=_number(current.get(metric)),
                baseline=baselines[metric],
            )
            if found:
                anomalies.append(found)

    prior_routes = [_route_rates(item) for item in prior]
    current_routes = _route_rates(current)
    route_baselines: dict[str, Any] = {}
    for name in sorted(set().union(*(set(row) for row in prior_routes), set(current_routes))):
        route_baselines[name] = _stats(
            [row.get(name, 0.0) for row in prior_routes], floor=METRIC_FLOORS["route_trigger_rate"]
        )
        found = _anomaly(
            category="route",
            metric="fallback_trigger_rate",
            name=name,
            direction="above",
            current=current_routes.get(name, 0.0),
            baseline=route_baselines[name],
        )
        if found:
            anomalies.append(found)

    dimension_baselines: dict[str, Any] = {}
    for category, key, metric in NAMED_DIMENSIONS:
        histories = [_named_counts(item, key) for item in prior]
        current_counts = _named_counts(current, key)
        dimension_baselines[category] = {}
        for name in sorted(set().union(*(set(row) for row in histories), set(current_counts))):
            baseline = _stats(
                [row.get(name, 0.0) for row in histories], floor=METRIC_FLOORS["dimension_count"]
            )
            dimension_baselines[category][name] = baseline
            directions = ("above", "below") if category == "fallback_kind" else ("above",)
            for direction in directions:
                found = _anomaly(
                    category=category,
                    metric=metric,
                    name=name,
                    direction=direction,
                    current=current_counts.get(name, 0.0),
                    baseline=baseline,
                )
                if found:
                    if category == "fallback_kind" and direction == "below" and current_counts.get(name, 0.0) == 0:
                        found["change_kind"] = "disappearance"
                    elif category == "fallback_kind" and direction == "above":
                        found["change_kind"] = "growth"
                    anomalies.append(found)

    anomalies.sort(
        key=lambda row: (
            SEVERITY_ORDER[row["severity"]],
            str(row["category"]),
            str(row["metric"]),
            str(row.get("name") or ""),
            str(row["direction"]),
        )
    )
    severity = anomalies[0]["severity"] if anomalies else "none"
    base.update(
        {
            "status": "anomalies_detected" if anomalies else "no_anomalies",
            "stability": f"{trend} + {'anomaly' if anomalies else 'no anomalies'}",
            "baseline": {
                "metrics": baselines,
                "routes": route_baselines,
                "dimensions": dimension_baselines,
            },
            "anomalies": anomalies,
            "severity": severity,
            "recommendations": (
                ["Review the highest-severity anomaly against recent fallback ownership and route changes."]
                if anomalies
                else ["Continue collecting snapshots; no unusual fallback incidence is currently detected."]
            ),
        }
    )
    return base


def _format_number(value: Any) -> str:
    number = _number(value)
    return f"{number:.4f}" if not math.isclose(number, round(number)) else str(int(round(number)))


def render_fallback_incidence_anomalies_markdown(report: Mapping[str, Any]) -> str:
    baseline = _mapping(report.get("baseline"))
    metrics = _mapping(baseline.get("metrics"))
    current = _mapping(report.get("current_snapshot"))
    anomalies = report.get("anomalies") if isinstance(report.get("anomalies"), list) else []
    thresholds = _mapping(report.get("thresholds"))
    lines = [
        "# Fallback Incidence Anomalies",
        "",
        "> Advisory-only anomaly detection over BP5 fallback incidence history.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Stability: `{report.get('stability')}`",
        f"- Highest severity: `{report.get('severity')}`",
        f"- Detected anomalies: {len(anomalies)}",
        "",
        "## Baseline",
        "",
        f"- Prior snapshots used: {report.get('baseline_snapshot_count', 0)}",
        f"- Minimum required: {thresholds.get('minimum_history_snapshots', 0)}",
        f"- Rolling window: {thresholds.get('rolling_window_prior_snapshots', 0)}",
        "- Expected band: mean +/- 2 effective standard deviations.",
        "- Effective deviation floors: trigger/route rate 0.02; count metrics 1.",
        "- Severity: info >=2, watch >=3, warning >=4, critical >=5 effective standard deviations.",
        "",
        "| Metric | Mean | Median | Min | Max | Std Dev | Expected Band |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    if metrics:
        for name in sorted(metrics):
            row = _mapping(metrics[name])
            deviation = row.get("standard_deviation")
            deviation_text = "n/a" if deviation is None else _format_number(deviation)
            lines.append(
                f"| `{name}` | {_format_number(row.get('mean'))} | {_format_number(row.get('median'))} | "
                f"{_format_number(row.get('minimum'))} | {_format_number(row.get('maximum'))} | {deviation_text} | "
                f"{_format_number(row.get('expected_minimum'))} to {_format_number(row.get('expected_maximum'))} |"
            )
    else:
        lines.append("| _insufficient history_ | - | - | - | - | - | - |")
    lines.extend(["", "## Current Snapshot", ""])
    if current:
        lines.extend(
            [
                f"- Timestamp: `{current.get('timestamp')}`",
                f"- Fallback trigger rate: {_format_number(current.get('fallback_trigger_rate'))}",
                f"- Fallback turns: {_format_number(current.get('fallback_turn_count'))}",
                f"- Fallback events: {_format_number(current.get('fallback_event_count'))}",
            ]
        )
    else:
        lines.append("No current snapshot is available.")
    lines.extend(["", "## Detected Anomalies", ""])
    if anomalies:
        lines.extend(["| Severity | Category | Metric | Name | Direction | Current | Band |", "|---|---|---|---|---|---:|---:|"])
        for row in anomalies:
            lines.append(
                f"| `{row.get('severity')}` | `{row.get('category')}` | `{row.get('metric')}` | "
                f"`{row.get('name') or '-'}` | `{row.get('direction')}` | {_format_number(row.get('current_value'))} | "
                f"{_format_number(row.get('expected_minimum'))} to {_format_number(row.get('expected_maximum'))} |"
            )
    else:
        lines.append("No anomalies emitted." if report.get("status") != "insufficient_history" else "`insufficient_history`: anomaly emission is suppressed.")
    lines.extend(["", "## Severity", "", f"`{report.get('severity')}`", "", "## Recommendations", ""])
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_fallback_incidence_anomaly_artifacts(
    report: Mapping[str, Any], *, json_path: Path | str, markdown_path: Path | str
) -> tuple[Path, Path]:
    json_out, markdown_out = Path(json_path), Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_fallback_incidence_anomalies_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--minimum-history-snapshots", type=int, default=DEFAULT_MINIMUM_HISTORY_SNAPSHOTS)
    parser.add_argument("--rolling-window", type=int, default=DEFAULT_ROLLING_WINDOW)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = analyze_fallback_incidence_anomalies(
            load_history(args.history),
            minimum_history_snapshots=args.minimum_history_snapshots,
            rolling_window=args.rolling_window,
        )
        json_out, markdown_out = write_fallback_incidence_anomaly_artifacts(
            report, json_path=args.json_out, markdown_path=args.md_out
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback incidence anomaly report failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback incidence anomalies: {report['status']} severity={report['severity']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
