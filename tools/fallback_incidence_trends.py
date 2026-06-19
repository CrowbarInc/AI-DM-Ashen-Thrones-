#!/usr/bin/env python3
"""Persist and report longitudinal trends from BP1 fallback incidence reports.

This tool is reporting-only. It consumes BP1 JSON output without changing BP1
calculations, runtime behavior, fallback projection, or replay scoring.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = 1
STABLE_TRIGGER_RATE_THRESHOLD = 0.01
DEFAULT_ROLLING_WINDOW = 5
DEFAULT_HISTORY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_incidence_history.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_incidence_trends.md"

HOTSPOT_SPECS: tuple[tuple[str, str], ...] = (
    ("fallback_kinds", "top_fallback_kinds"),
    ("owner_buckets", "top_owner_buckets"),
    ("selection_owners", "top_selection_owners"),
    ("content_owners", "top_content_owners"),
)


def empty_history() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "snapshots": []}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _rank_counts(values: Mapping[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    rows = [
        {"name": str(name), "count": _integer(count)}
        for name, count in values.items()
        if str(name).strip() and _integer(count) > 0
    ]
    return sorted(rows, key=lambda row: (-row["count"], row["name"]))[:limit]


def _route_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    eligible = _mapping(report.get("route_turn_count"))
    fallback = _mapping(report.get("route_fallback_turn_count"))
    rates = _mapping(report.get("route_fallback_trigger_rate"))
    routes = sorted(set(eligible) | set(fallback) | set(rates))
    return [
        {
            "route_kind": str(route),
            "eligible_turn_count": _integer(eligible.get(route)),
            "fallback_turn_count": _integer(fallback.get(route)),
            "fallback_trigger_rate": _float(rates.get(route)),
        }
        for route in routes
    ]


def snapshot_from_incidence_report(
    report: Mapping[str, Any],
    *,
    timestamp: str,
    artifact_source: str,
    top_limit: int = 10,
) -> dict[str, Any]:
    """Create one stable history snapshot from an existing BP1 report."""
    frequency = _mapping(report.get("frequency"))
    return {
        "timestamp": str(timestamp),
        "artifact_source": str(artifact_source),
        "eligible_turn_count": _integer(report.get("eligible_turn_count")),
        "fallback_turn_count": _integer(report.get("fallback_turn_count")),
        "fallback_event_count": _integer(report.get("fallback_event_count")),
        "fallback_trigger_rate": _float(report.get("fallback_trigger_rate")),
        "top_fallback_kinds": _rank_counts(_mapping(frequency.get("fallback_kind")), limit=top_limit),
        "top_diegetic_families": _rank_counts(_mapping(frequency.get("diegetic_family")), limit=top_limit),
        "top_realization_families": _rank_counts(
            _mapping(frequency.get("realization_family")), limit=top_limit
        ),
        "top_owner_buckets": _rank_counts(_mapping(frequency.get("fallback_owner_bucket")), limit=top_limit),
        "top_selection_owners": _rank_counts(
            _mapping(frequency.get("fallback_selection_owner")), limit=top_limit
        ),
        "top_content_owners": _rank_counts(_mapping(frequency.get("fallback_content_owner")), limit=top_limit),
        "route_rates": _route_rows(report),
    }


def load_history(path: Path | str) -> dict[str, Any]:
    history_path = Path(path)
    if not history_path.is_file():
        return empty_history()
    raw = json.loads(history_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("snapshots"), list):
        raise ValueError("history must be a JSON object with a snapshots list")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported history schema_version: {raw.get('schema_version')!r}")
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshots": [dict(item) for item in raw["snapshots"] if isinstance(item, Mapping)],
    }


def append_snapshot(history: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return history with one snapshot appended; existing entries remain unchanged and ordered."""
    snapshots = history.get("snapshots") if isinstance(history.get("snapshots"), list) else []
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshots": [dict(item) for item in snapshots if isinstance(item, Mapping)] + [dict(snapshot)],
    }


def write_history(history: Mapping[str, Any], path: Path | str) -> Path:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return history_path


def append_snapshot_to_history(path: Path | str, snapshot: Mapping[str, Any]) -> dict[str, Any]:
    history = load_history(path)
    updated = append_snapshot(history, snapshot)
    write_history(updated, path)
    return updated


def _direction(delta: float, *, threshold: float = 0.0) -> str:
    if delta > threshold:
        return "increasing"
    if delta < -threshold:
        return "decreasing"
    return "stable"


def classify_trigger_rate(
    current_rate: float,
    previous_rate: float | None,
    *,
    threshold: float = STABLE_TRIGGER_RATE_THRESHOLD,
) -> str:
    if previous_rate is None:
        return "insufficient_history"
    delta = current_rate - previous_rate
    if delta > threshold:
        return "worsening"
    if delta < -threshold:
        return "improving"
    return "stable"


def _named_counts(snapshot: Mapping[str, Any], key: str) -> dict[str, int]:
    rows = snapshot.get(key)
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("name")): _integer(row.get("count"))
        for row in rows
        if isinstance(row, Mapping) and str(row.get("name") or "").strip()
    }


def _hotspot_rows(
    current: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
    history: Sequence[Mapping[str, Any]],
    key: str,
) -> list[dict[str, Any]]:
    current_counts = _named_counts(current, key)
    previous_counts = _named_counts(previous or {}, key)
    history_counts: dict[str, int] = {}
    for snapshot in history:
        for name, count in _named_counts(snapshot, key).items():
            history_counts[name] = history_counts.get(name, 0) + count
    names = sorted(set(current_counts) | set(previous_counts) | set(history_counts))
    rows = []
    for name in names:
        current_count = current_counts.get(name, 0)
        previous_count = previous_counts.get(name, 0)
        delta = current_count - previous_count
        rows.append(
            {
                "name": name,
                "current_count": current_count,
                "previous_count": previous_count,
                "delta": delta,
                "direction": _direction(float(delta)),
                "rolling_history_count": history_counts.get(name, 0),
            }
        )
    return sorted(rows, key=lambda row: (-row["current_count"], -row["rolling_history_count"], row["name"]))


def _routes(snapshot: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = snapshot.get("route_rates")
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("route_kind")): row
        for row in rows
        if isinstance(row, Mapping) and str(row.get("route_kind") or "").strip()
    }


def _route_trends(
    current: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
    history: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    current_routes = _routes(current)
    previous_routes = _routes(previous or {})
    rolling_eligible: dict[str, int] = {}
    rolling_fallback: dict[str, int] = {}
    for snapshot in history:
        for name, row in _routes(snapshot).items():
            rolling_eligible[name] = rolling_eligible.get(name, 0) + _integer(row.get("eligible_turn_count"))
            rolling_fallback[name] = rolling_fallback.get(name, 0) + _integer(row.get("fallback_turn_count"))
    names = sorted(set(current_routes) | set(previous_routes) | set(rolling_eligible))
    rows: list[dict[str, Any]] = []
    for name in names:
        current_row = current_routes.get(name, {})
        previous_row = previous_routes.get(name, {})
        current_rate = _float(current_row.get("fallback_trigger_rate"))
        previous_rate = _float(previous_row.get("fallback_trigger_rate"))
        delta = current_rate - previous_rate
        rows.append(
            {
                "route_kind": name,
                "eligible_turn_count": _integer(current_row.get("eligible_turn_count")),
                "fallback_turn_count": _integer(current_row.get("fallback_turn_count")),
                "fallback_trigger_rate": current_rate,
                "previous_trigger_rate": previous_rate,
                "delta_trigger_rate": delta,
                "direction": _direction(delta, threshold=STABLE_TRIGGER_RATE_THRESHOLD),
                "rolling_eligible_turn_count": rolling_eligible.get(name, 0),
                "rolling_fallback_turn_count": rolling_fallback.get(name, 0),
            }
        )
    return sorted(
        rows,
        key=lambda row: (-row["eligible_turn_count"], -row["rolling_eligible_turn_count"], row["route_kind"]),
    )


def analyze_fallback_incidence_history(
    history: Mapping[str, Any],
    *,
    rolling_window: int = DEFAULT_ROLLING_WINDOW,
) -> dict[str, Any]:
    snapshots = [item for item in history.get("snapshots", []) if isinstance(item, Mapping)]
    if not snapshots:
        return {
            "snapshot_count": 0,
            "classification": "insufficient_history",
            "thresholds": {
                "stable_trigger_rate_absolute_delta_max": STABLE_TRIGGER_RATE_THRESHOLD,
                "improving_below_delta": -STABLE_TRIGGER_RATE_THRESHOLD,
                "worsening_above_delta": STABLE_TRIGGER_RATE_THRESHOLD,
                "rolling_window_prior_snapshots": rolling_window,
            },
            "current_snapshot": None,
            "previous_snapshot": None,
            "change_since_previous": None,
            "rolling_history": None,
            "hotspots": {name: [] for name, _ in HOTSPOT_SPECS},
            "route_trends": [],
            "notable_changes": [],
        }

    current = snapshots[-1]
    previous = snapshots[-2] if len(snapshots) >= 2 else None
    previous_rate = _float(previous.get("fallback_trigger_rate")) if previous else None
    classification = classify_trigger_rate(_float(current.get("fallback_trigger_rate")), previous_rate)
    change = None
    if previous is not None:
        change = {
            "delta_fallback_trigger_rate": _float(current.get("fallback_trigger_rate"))
            - _float(previous.get("fallback_trigger_rate")),
            "delta_fallback_event_count": _integer(current.get("fallback_event_count"))
            - _integer(previous.get("fallback_event_count")),
            "delta_fallback_turn_count": _integer(current.get("fallback_turn_count"))
            - _integer(previous.get("fallback_turn_count")),
        }

    prior = snapshots[max(0, len(snapshots) - 1 - rolling_window) : -1]
    rolling = None
    if prior:
        count = len(prior)
        averages = {
            "fallback_trigger_rate": sum(_float(item.get("fallback_trigger_rate")) for item in prior) / count,
            "fallback_event_count": sum(_integer(item.get("fallback_event_count")) for item in prior) / count,
            "fallback_turn_count": sum(_integer(item.get("fallback_turn_count")) for item in prior) / count,
        }
        rolling = {
            "prior_snapshot_count": count,
            "average_fallback_trigger_rate": averages["fallback_trigger_rate"],
            "average_fallback_event_count": averages["fallback_event_count"],
            "average_fallback_turn_count": averages["fallback_turn_count"],
            "delta_fallback_trigger_rate": _float(current.get("fallback_trigger_rate"))
            - averages["fallback_trigger_rate"],
            "delta_fallback_event_count": _integer(current.get("fallback_event_count"))
            - averages["fallback_event_count"],
            "delta_fallback_turn_count": _integer(current.get("fallback_turn_count"))
            - averages["fallback_turn_count"],
        }

    hotspots = {
        name: _hotspot_rows(current, previous, snapshots, key)
        for name, key in HOTSPOT_SPECS
    }
    route_trends = _route_trends(current, previous, snapshots)
    notable: list[dict[str, Any]] = []
    if change is not None:
        notable.append({"metric": "fallback_trigger_rate", "delta": change["delta_fallback_trigger_rate"]})
        notable.append({"metric": "fallback_event_count", "delta": change["delta_fallback_event_count"]})
        notable.append({"metric": "fallback_turn_count", "delta": change["delta_fallback_turn_count"]})
    for category, rows in hotspots.items():
        changed = [row for row in rows if row["delta"]]
        if changed:
            row = max(changed, key=lambda item: (abs(item["delta"]), item["name"]))
            notable.append(
                {
                    "metric": category,
                    "name": row["name"],
                    "delta": row["delta"],
                    "direction": row["direction"],
                }
            )
    notable.sort(key=lambda row: (-abs(float(row["delta"])), str(row["metric"]), str(row.get("name") or "")))
    return {
        "snapshot_count": len(snapshots),
        "classification": classification,
        "thresholds": {
            "stable_trigger_rate_absolute_delta_max": STABLE_TRIGGER_RATE_THRESHOLD,
            "improving_below_delta": -STABLE_TRIGGER_RATE_THRESHOLD,
            "worsening_above_delta": STABLE_TRIGGER_RATE_THRESHOLD,
            "rolling_window_prior_snapshots": rolling_window,
        },
        "current_snapshot": dict(current),
        "previous_snapshot": dict(previous) if previous is not None else None,
        "change_since_previous": change,
        "rolling_history": rolling,
        "hotspots": hotspots,
        "route_trends": route_trends,
        "notable_changes": notable,
    }


def _percent(value: Any) -> str:
    return f"{_float(value) * 100:.2f}%"


def _signed(value: Any, *, percent: bool = False) -> str:
    number = _float(value)
    if percent:
        return f"{number * 100:+.2f} pp"
    return f"{number:+g}"


def _hotspot_markdown(title: str, rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [f"## {title}", "", "| Name | Current | Previous | Delta | Direction |", "|---|---:|---:|---:|---|"]
    current_rows = [row for row in rows if _integer(row.get("current_count")) > 0]
    if current_rows:
        for row in current_rows:
            lines.append(
                f"| `{row.get('name')}` | {_integer(row.get('current_count'))} | "
                f"{_integer(row.get('previous_count'))} | {_signed(row.get('delta'))} | "
                f"`{row.get('direction')}` |"
            )
    else:
        lines.append("| _none_ | 0 | 0 | 0 | `stable` |")
    return lines


def render_fallback_incidence_trends_markdown(analysis: Mapping[str, Any]) -> str:
    current = analysis.get("current_snapshot") if isinstance(analysis.get("current_snapshot"), Mapping) else None
    change = analysis.get("change_since_previous") if isinstance(analysis.get("change_since_previous"), Mapping) else None
    hotspots = analysis.get("hotspots") if isinstance(analysis.get("hotspots"), Mapping) else {}
    routes = analysis.get("route_trends") if isinstance(analysis.get("route_trends"), list) else []
    thresholds = _mapping(analysis.get("thresholds"))
    lines = [
        "# Fallback Incidence Trends",
        "",
        "> Read-only longitudinal reporting derived from BP1 snapshots.",
        "",
        "## Executive Summary",
        "",
        f"- **Trend classification:** `{analysis.get('classification', 'insufficient_history')}`",
        f"- **Snapshot count:** {_integer(analysis.get('snapshot_count'))}",
        (
            "- **Thresholds:** improving below -1.00 percentage point, stable within +/-1.00 percentage point, worsening above +1.00 percentage point."
        ),
        f"- **Rolling baseline:** up to {_integer(thresholds.get('rolling_window_prior_snapshots'))} prior snapshots.",
        "",
        "## Current Snapshot",
        "",
    ]
    if current is None:
        lines.extend(["No fallback incidence snapshots have been recorded.", ""])
    else:
        lines.extend(
            [
                f"- Timestamp: `{current.get('timestamp')}`",
                f"- Artifact source: `{current.get('artifact_source')}`",
                f"- Eligible turns: {_integer(current.get('eligible_turn_count'))}",
                f"- Fallback turns: {_integer(current.get('fallback_turn_count'))}",
                f"- Fallback events: {_integer(current.get('fallback_event_count'))}",
                f"- Fallback trigger rate: {_percent(current.get('fallback_trigger_rate'))}",
                "",
            ]
        )
    lines.extend(["## Change Since Previous Snapshot", ""])
    if change is None:
        lines.extend(["Insufficient history for a previous-snapshot comparison.", ""])
    else:
        lines.extend(
            [
                f"- Trigger-rate delta: {_signed(change.get('delta_fallback_trigger_rate'), percent=True)}",
                f"- Fallback-event delta: {_signed(change.get('delta_fallback_event_count'))}",
                f"- Fallback-turn delta: {_signed(change.get('delta_fallback_turn_count'))}",
                "",
            ]
        )
    lines.extend(_hotspot_markdown("Top Fallback Kinds", hotspots.get("fallback_kinds", [])))
    lines.append("")
    owner_rows = list(hotspots.get("owner_buckets", [])) + list(hotspots.get("selection_owners", [])) + list(
        hotspots.get("content_owners", [])
    )
    lines.extend(_hotspot_markdown("Top Owners", owner_rows))
    lines.extend(["", "## Top Routes", "", "| Route | Eligible | Fallback Turns | Rate | Delta | Direction |", "|---|---:|---:|---:|---:|---|"])
    current_routes = [row for row in routes if _integer(row.get("eligible_turn_count")) > 0]
    if current_routes:
        for row in current_routes:
            lines.append(
                f"| `{row.get('route_kind')}` | {_integer(row.get('eligible_turn_count'))} | "
                f"{_integer(row.get('fallback_turn_count'))} | {_percent(row.get('fallback_trigger_rate'))} | "
                f"{_signed(row.get('delta_trigger_rate'), percent=True)} | `{row.get('direction')}` |"
            )
    else:
        lines.append("| _none_ | 0 | 0 | 0.00% | +0.00 pp | `stable` |")
    lines.extend(["", "## Trend Direction", "", f"`{analysis.get('classification', 'insufficient_history')}`", ""])
    lines.extend(["## Notable Changes", ""])
    notable = analysis.get("notable_changes") if isinstance(analysis.get("notable_changes"), list) else []
    if notable:
        for row in notable:
            label = f" / {row.get('name')}" if row.get("name") else ""
            lines.append(f"- `{row.get('metric')}{label}`: {_signed(row.get('delta'))}")
    else:
        lines.append("No notable changes are available yet.")
    lines.append("")
    return "\n".join(lines)


def write_trend_markdown(analysis: Mapping[str, Any], path: Path | str) -> Path:
    markdown_path = Path(path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_fallback_incidence_trends_markdown(analysis), encoding="utf-8")
    return markdown_path


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incidence-report", type=Path, help="Optional BP1 JSON report to append as a snapshot.")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH, help="Append-only history JSON path.")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH, help="Trend Markdown output path.")
    parser.add_argument("--timestamp", help="Snapshot timestamp; defaults to current UTC when appending.")
    parser.add_argument("--artifact-source", help="Source label; defaults to the incidence report path.")
    parser.add_argument("--rolling-window", type=int, default=DEFAULT_ROLLING_WINDOW)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        history = load_history(args.history)
        if args.incidence_report is not None:
            report = json.loads(args.incidence_report.read_text(encoding="utf-8"))
            if not isinstance(report, Mapping):
                raise ValueError("incidence report root must be a JSON object")
            snapshot = snapshot_from_incidence_report(
                report,
                timestamp=args.timestamp or _utc_timestamp(),
                artifact_source=args.artifact_source or args.incidence_report.as_posix(),
            )
            history = append_snapshot(history, snapshot)
            write_history(history, args.history)
            print(f"Appended snapshot to {args.history}")
        elif not Path(args.history).is_file():
            write_history(history, args.history)
            print(f"Initialized {args.history}")
        analysis = analyze_fallback_incidence_history(history, rolling_window=max(1, args.rolling_window))
        markdown_path = write_trend_markdown(analysis, args.md_out)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback incidence trend report failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {markdown_path}")
    print(f"Fallback incidence trend: {analysis['classification']} snapshots={analysis['snapshot_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
