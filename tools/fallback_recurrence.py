#!/usr/bin/env python3
"""Report recurring fallback contributors from BP5 history (advisory only)."""

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

SCHEMA_VERSION = 1
DEFAULT_HISTORY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_incidence_history.json"
DEFAULT_JSON_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_recurrence_report.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_recurrence_report.md"

CLASSIFICATION_THRESHOLDS = {
    "transient_max_appearances": 1,
    "recurring_min_appearances": 2,
    "persistent_min_appearance_percentage": 0.50,
    "dominant_min_appearance_percentage": 0.75,
}
CLASSIFICATION_RANK = {"dominant": 0, "persistent": 1, "recurring": 2, "transient": 3}
DIMENSIONS = (
    ("fallback_kind", "top_fallback_kinds"),
    ("route_kind", "route_rates"),
    ("owner_bucket", "top_owner_buckets"),
    ("selection_owner", "top_selection_owners"),
    ("content_owner", "top_content_owners"),
    ("diegetic_family", "top_diegetic_families"),
    ("realization_family", "top_realization_families"),
)
OWNER_DIMENSIONS = {"owner_bucket", "selection_owner", "content_owner"}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _counts(snapshot: Mapping[str, Any], key: str) -> dict[str, float]:
    rows = snapshot.get(key)
    if not isinstance(rows, list):
        return {}
    name_key = "route_kind" if key == "route_rates" else "name"
    count_key = "fallback_turn_count" if key == "route_rates" else "count"
    return {
        str(row.get(name_key)): _number(row.get(count_key))
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get(name_key) or "").strip()
        and _number(row.get(count_key)) > 0
    }


def classify_recurrence(snapshot_appearances: int, snapshot_count: int) -> str:
    """Classify appearances, giving the one-off transient rule precedence."""
    if snapshot_appearances <= CLASSIFICATION_THRESHOLDS["transient_max_appearances"]:
        return "transient"
    percentage = snapshot_appearances / snapshot_count if snapshot_count else 0.0
    if percentage >= CLASSIFICATION_THRESHOLDS["dominant_min_appearance_percentage"]:
        return "dominant"
    if percentage >= CLASSIFICATION_THRESHOLDS["persistent_min_appearance_percentage"]:
        return "persistent"
    return "recurring"


def _longest_streak(presence: Sequence[bool]) -> int:
    longest = current = 0
    for present in presence:
        current = current + 1 if present else 0
        longest = max(longest, current)
    return longest


def _dimension_rows(
    snapshots: Sequence[Mapping[str, Any]], dimension: str, key: str
) -> list[dict[str, Any]]:
    per_snapshot = [_counts(snapshot, key) for snapshot in snapshots]
    names = sorted(set().union(*(set(counts) for counts in per_snapshot))) if per_snapshot else []
    rows: list[dict[str, Any]] = []
    for name in names:
        presence = [counts.get(name, 0.0) > 0 for counts in per_snapshot]
        indices = [index for index, present in enumerate(presence) if present]
        appearances = len(indices)
        rows.append(
            {
                "dimension": dimension,
                "name": name,
                "snapshot_appearances": appearances,
                "consecutive_appearances": _longest_streak(presence),
                "appearance_percentage": appearances / len(snapshots) if snapshots else 0.0,
                "first_seen": snapshots[indices[0]].get("timestamp") if indices else None,
                "most_recent_seen": snapshots[indices[-1]].get("timestamp") if indices else None,
                "cumulative_incidence_contribution": sum(counts.get(name, 0.0) for counts in per_snapshot),
                "classification": classify_recurrence(appearances, len(snapshots)),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            CLASSIFICATION_RANK[row["classification"]],
            -row["snapshot_appearances"],
            -row["cumulative_incidence_contribution"],
            row["name"],
        ),
    )


def _hotspot_sort(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        CLASSIFICATION_RANK[str(row.get("classification"))],
        -int(row.get("snapshot_appearances") or 0),
        -_number(row.get("cumulative_incidence_contribution")),
        str(row.get("dimension")),
        str(row.get("name")),
    )


def _integration_signals(
    trend: str, anomaly_report: Mapping[str, Any], entities: Mapping[str, Sequence[Mapping[str, Any]]]
) -> list[str]:
    lookup = {
        (dimension, str(row.get("name"))): str(row.get("classification"))
        for dimension, rows in entities.items()
        for row in rows
    }
    category_map = {
        "fallback_kind": "fallback_kind",
        "route": "route_kind",
        "owner_bucket": "owner_bucket",
        "selection_owner": "selection_owner",
        "content_owner": "content_owner",
    }
    signals: set[str] = set()
    anomalies = anomaly_report.get("anomalies")
    if isinstance(anomalies, list):
        for anomaly in anomalies:
            if not isinstance(anomaly, Mapping) or not anomaly.get("name"):
                continue
            dimension = category_map.get(str(anomaly.get("category")))
            classification = lookup.get((dimension, str(anomaly.get("name")))) if dimension else None
            if classification:
                hotspot = "persistent" if classification in {"persistent", "dominant"} else "transient"
                signals.add(f"anomaly + {hotspot} hotspot: {dimension}/{anomaly.get('name')}")
    if trend == "worsening":
        for dimension in sorted(OWNER_DIMENSIONS):
            for row in entities.get(dimension, []):
                if row.get("classification") in {"persistent", "dominant"}:
                    signals.add(f"worsening trend + persistent owner: {dimension}/{row.get('name')}")
    if not signals:
        recurrence_state = "recurrence observed" if lookup else "no recurrence evidence"
        signals.add(f"{trend} trend + {anomaly_report.get('status', 'unknown')} + {recurrence_state}")
    return sorted(signals)


def analyze_fallback_recurrence(history: Mapping[str, Any]) -> dict[str, Any]:
    snapshots = [item for item in history.get("snapshots", []) if isinstance(item, Mapping)]
    entities = {
        dimension: _dimension_rows(snapshots, dimension, key)
        for dimension, key in DIMENSIONS
    }
    recurring = {
        dimension: [row for row in rows if row["classification"] != "transient"]
        for dimension, rows in entities.items()
    }
    structural_hotspots = {
        "fallback_kinds": sorted(recurring["fallback_kind"], key=_hotspot_sort),
        "owners": sorted(
            [row for dimension in sorted(OWNER_DIMENSIONS) for row in recurring[dimension]],
            key=_hotspot_sort,
        ),
        "routes": sorted(recurring["route_kind"], key=_hotspot_sort),
    }
    dominant = sorted(
        [row for rows in entities.values() for row in rows if row["classification"] == "dominant"],
        key=_hotspot_sort,
    )
    trend = analyze_fallback_incidence_history(history).get("classification", "insufficient_history")
    anomaly_report = analyze_fallback_incidence_anomalies(history)
    counts = {
        classification: sum(
            row["classification"] == classification for rows in entities.values() for row in rows
        )
        for classification in ("transient", "recurring", "persistent", "dominant")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "no_history" if not snapshots else "ok",
        "snapshot_count": len(snapshots),
        "thresholds": dict(CLASSIFICATION_THRESHOLDS),
        "classification_counts": counts,
        "entities": entities,
        "structural_hotspots": structural_hotspots,
        "dominant_contributors": dominant,
        "trend_classification": trend,
        "anomaly_status": anomaly_report.get("status"),
        "integrated_signals": _integration_signals(trend, anomaly_report, entities),
        "recommendations": (
            ["Collect fallback-incidence snapshots before interpreting recurrence."]
            if not snapshots
            else [
                "Review dominant and persistent contributors before treating isolated anomalies as structural.",
                "Continue snapshot collection to distinguish stable recurrence from short-history concentration.",
            ]
        ),
    }


def _percent(value: Any) -> str:
    return f"{_number(value) * 100:.1f}%"


def _contribution(value: Any) -> str:
    number = _number(value)
    return str(int(number)) if number.is_integer() else f"{number:.2f}"


def _rows_section(title: str, rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Classification | Dimension | Name | Appearances | Consecutive | Percentage | Contribution | First Seen | Most Recent |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    if rows:
        for row in rows:
            lines.append(
                f"| `{row.get('classification')}` | `{row.get('dimension')}` | `{row.get('name')}` | "
                f"{row.get('snapshot_appearances')} | {row.get('consecutive_appearances')} | "
                f"{_percent(row.get('appearance_percentage'))} | "
                f"{_contribution(row.get('cumulative_incidence_contribution'))} | "
                f"`{row.get('first_seen')}` | `{row.get('most_recent_seen')}` |"
            )
    else:
        lines.append("| _none_ | - | - | 0 | 0 | 0.0% | 0 | - | - |")
    return lines


def render_fallback_recurrence_markdown(report: Mapping[str, Any]) -> str:
    hotspots = report.get("structural_hotspots") if isinstance(report.get("structural_hotspots"), Mapping) else {}
    counts = report.get("classification_counts") if isinstance(report.get("classification_counts"), Mapping) else {}
    lines = [
        "# Fallback Recurrence Report",
        "",
        "> Advisory-only recurrence and persistence analysis over BP5 history.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Snapshots analyzed: {report.get('snapshot_count', 0)}",
        f"- BP5 trend: `{report.get('trend_classification')}`",
        f"- BP6 anomaly status: `{report.get('anomaly_status')}`",
        "- Thresholds: transient once; recurring 2+ times; persistent in at least 50%; dominant in at least 75%.",
        "",
        "## Recurrence Summary",
        "",
        f"- Transient: {counts.get('transient', 0)}",
        f"- Recurring: {counts.get('recurring', 0)}",
        f"- Persistent: {counts.get('persistent', 0)}",
        f"- Dominant: {counts.get('dominant', 0)}",
        "- Consecutive appearances are the longest uninterrupted snapshot streak.",
        "",
        "### Integrated Signals",
        "",
    ]
    for signal in report.get("integrated_signals", []):
        lines.append(f"- {signal}")
    lines.extend([""] + _rows_section("Persistent Fallback Kinds", hotspots.get("fallback_kinds", [])))
    lines.extend([""] + _rows_section("Persistent Owners", hotspots.get("owners", [])))
    lines.extend([""] + _rows_section("Persistent Routes", hotspots.get("routes", [])))
    lines.extend([""] + _rows_section("Dominant Contributors", report.get("dominant_contributors", [])))
    lines.extend(["", "## Recommendations", ""])
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_fallback_recurrence_artifacts(
    report: Mapping[str, Any], *, json_path: Path | str, markdown_path: Path | str
) -> tuple[Path, Path]:
    json_out, markdown_out = Path(json_path), Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_fallback_recurrence_markdown(report), encoding="utf-8")
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
        report = analyze_fallback_recurrence(load_history(args.history))
        json_out, markdown_out = write_fallback_recurrence_artifacts(
            report, json_path=args.json_out, markdown_path=args.md_out
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback recurrence report failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback recurrence: {report['status']} snapshots={report['snapshot_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
