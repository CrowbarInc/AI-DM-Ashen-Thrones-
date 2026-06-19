#!/usr/bin/env python3
"""Build an advisory remediation queue from BP8 structural risk output."""

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
DEFAULT_ROLLING_WINDOW = 5
DEFAULT_RISK_REPORT_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_risk_report.json"
DEFAULT_HISTORY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_risk_history.json"
DEFAULT_JSON_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_queue.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_queue.md"

PRIORITY_THRESHOLDS = {
    "monitor": 0.0,
    "investigate": 25.0,
    "schedule": 40.0,
    "prioritize": 60.0,
    "urgent": 80.0,
}
PRIORITY_RANK = {"monitor": 0, "investigate": 1, "schedule": 2, "prioritize": 3, "urgent": 4}
RECURRENCE_RANK = {"transient": 0, "recurring": 1, "persistent": 2, "dominant": 3}
MINIMUM_SNAPSHOT_APPEARANCES = 2
MINIMUM_RISK_OBSERVATIONS_FOR_SCHEDULE = 2
SCORE_TREND_DELTA_THRESHOLD = 2.0


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def empty_risk_history() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "snapshots": []}


def load_risk_history(path: Path | str) -> dict[str, Any]:
    history_path = Path(path)
    if not history_path.is_file():
        return empty_risk_history()
    raw = json.loads(history_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("snapshots"), list):
        raise ValueError("risk history must be a JSON object with a snapshots list")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported risk history schema_version: {raw.get('schema_version')!r}")
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshots": [dict(item) for item in raw["snapshots"] if isinstance(item, Mapping)],
    }


def append_risk_snapshot(history: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    snapshots = history.get("snapshots") if isinstance(history.get("snapshots"), list) else []
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshots": [dict(item) for item in snapshots if isinstance(item, Mapping)] + [dict(snapshot)],
    }


def write_risk_history(history: Mapping[str, Any], path: Path | str) -> Path:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return history_path


def _risk_rows(risk_report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    ranked = risk_report.get("ranked_hotspots")
    rows = ranked.get("all") if isinstance(ranked, Mapping) else None
    return [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, list) else []


def _history_contributors(snapshot: Mapping[str, Any]) -> dict[tuple[str, str], Mapping[str, Any]]:
    contributors = snapshot.get("contributors")
    if not isinstance(contributors, list):
        return {}
    return {
        (str(row.get("dimension")), str(row.get("contributor"))): row
        for row in contributors
        if isinstance(row, Mapping) and row.get("dimension") and row.get("contributor")
    }


def _score_history(
    history: Mapping[str, Any], key: tuple[str, str], *, rolling_window: int
) -> list[float]:
    snapshots = history.get("snapshots") if isinstance(history.get("snapshots"), list) else []
    scores: list[float] = []
    for snapshot in snapshots[-rolling_window:]:
        if not isinstance(snapshot, Mapping):
            continue
        row = _history_contributors(snapshot).get(key)
        if row is not None:
            scores.append(_number(row.get("score")))
    return scores


def _score_trend(delta: float | None) -> str:
    if delta is None:
        return "insufficient_history"
    if delta > SCORE_TREND_DELTA_THRESHOLD:
        return "increasing"
    if delta < -SCORE_TREND_DELTA_THRESHOLD:
        return "decreasing"
    return "stable"


def _rolling_score_trend(scores: Sequence[float]) -> str:
    if len(scores) < 2:
        return "insufficient_history"
    return _score_trend(scores[-1] - scores[0])


def _base_priority(score: float) -> str:
    for priority in ("urgent", "prioritize", "schedule", "investigate"):
        if score >= PRIORITY_THRESHOLDS[priority]:
            return priority
    return "monitor"


def _priority(
    *,
    score: float,
    rolling_average: float,
    observation_count: int,
    recurrence: str,
    snapshot_appearances: int,
    anomaly_count: int,
) -> tuple[str, list[str]]:
    desired = _base_priority(score)
    protections: list[str] = []
    if score < PRIORITY_THRESHOLDS["investigate"]:
        return "monitor", protections
    if snapshot_appearances < MINIMUM_SNAPSHOT_APPEARANCES or RECURRENCE_RANK.get(recurrence, 0) < RECURRENCE_RANK["recurring"]:
        protections.append("promotion held: requires at least 2 appearances and recurring classification")
        return "monitor", protections
    if desired == "investigate":
        return desired, protections
    if observation_count < MINIMUM_RISK_OBSERVATIONS_FOR_SCHEDULE or rolling_average < PRIORITY_THRESHOLDS["schedule"]:
        protections.append("promotion held at investigate: schedule requires 2 risk observations averaging at least 40")
        return "investigate", protections
    if desired == "schedule":
        return desired, protections
    if RECURRENCE_RANK.get(recurrence, 0) < RECURRENCE_RANK["persistent"] or rolling_average < PRIORITY_THRESHOLDS["prioritize"]:
        protections.append("promotion held at schedule: prioritize requires persistent recurrence and average risk at least 60")
        return "schedule", protections
    if desired == "prioritize":
        return desired, protections
    if recurrence != "dominant" or anomaly_count < 1 or rolling_average < PRIORITY_THRESHOLDS["urgent"]:
        protections.append("promotion held at prioritize: urgent requires dominant recurrence, anomaly participation, and average risk at least 80")
        return "prioritize", protections
    return "urgent", protections


def build_remediation_queue(
    risk_report: Mapping[str, Any],
    risk_history: Mapping[str, Any],
    *,
    rolling_window: int = DEFAULT_ROLLING_WINDOW,
) -> dict[str, Any]:
    """Rank current BP8 contributors using append-only prior risk observations."""
    window = max(1, int(rolling_window))
    snapshots = risk_history.get("snapshots") if isinstance(risk_history.get("snapshots"), list) else []
    previous_rows = _history_contributors(snapshots[-1]) if snapshots and isinstance(snapshots[-1], Mapping) else {}
    queue: list[dict[str, Any]] = []
    for row in _risk_rows(risk_report):
        dimension, contributor = str(row.get("dimension")), str(row.get("name"))
        key = (dimension, contributor)
        score = _number(row.get("risk_score"))
        prior_scores = _score_history(risk_history, key, rolling_window=window - 1 if window > 1 else 1)
        rolling_scores = (prior_scores + [score])[-window:]
        previous = previous_rows.get(key)
        previous_score = _number(previous.get("score")) if previous is not None else None
        score_delta = score - previous_score if previous_score is not None else None
        recurrence_evidence = row.get("recurrence_evidence") if isinstance(row.get("recurrence_evidence"), Mapping) else {}
        anomaly_evidence = row.get("anomaly_evidence") if isinstance(row.get("anomaly_evidence"), Mapping) else {}
        recurrence = str(recurrence_evidence.get("classification") or "transient")
        appearances = int(recurrence_evidence.get("snapshot_appearances") or 0)
        anomaly_count = int(anomaly_evidence.get("participation_count") or 0)
        rolling_average = statistics.fmean(rolling_scores) if rolling_scores else score
        priority, protections = _priority(
            score=score,
            rolling_average=rolling_average,
            observation_count=len(rolling_scores),
            recurrence=recurrence,
            snapshot_appearances=appearances,
            anomaly_count=anomaly_count,
        )
        previous_priority = str(previous.get("priority")) if previous and previous.get("priority") else None
        if previous_priority and PRIORITY_RANK[priority] > PRIORITY_RANK.get(previous_priority, 0):
            transition = "promotion"
        elif previous_priority and PRIORITY_RANK[priority] < PRIORITY_RANK.get(previous_priority, 0):
            transition = "demotion"
        else:
            transition = "stable"
        promotion_signals = []
        demotion_signals = []
        if transition == "promotion":
            promotion_signals.append(
                f"priority increased from {previous_priority} to {priority} as risk reached {score:g}"
            )
        if transition == "demotion":
            demotion_signals.append(
                f"priority decreased from {previous_priority} to {priority} as risk moved to {score:g}"
            )
        if score_delta is not None and score_delta > SCORE_TREND_DELTA_THRESHOLD:
            promotion_signals.append(f"risk score increased by {score_delta:g}")
        if score_delta is not None and score_delta < -SCORE_TREND_DELTA_THRESHOLD:
            demotion_signals.append(f"risk score decreased by {abs(score_delta):g}")
        demotion_signals.extend(protections)
        if not promotion_signals:
            promotion_signals.append("none: priority did not increase and risk did not materially rise")
        if not demotion_signals:
            demotion_signals.append("none: priority did not decrease and no stability protection applied")
        rationale_parts = [
            f"risk {score:g} maps to {_base_priority(score)} before stability protection",
            f"recurrence is {recurrence} across {appearances} snapshots",
            f"rolling average is {rolling_average:.2f} across {len(rolling_scores)} risk observations",
            f"anomaly participation count is {anomaly_count}",
        ]
        rationale_parts.extend(protections)
        queue.append(
            {
                "contributor": contributor,
                "dimension": dimension,
                "risk_score": score,
                "risk_classification": row.get("risk_classification"),
                "priority": priority,
                "score_delta": score_delta,
                "rolling_average_score": rolling_average,
                "rolling_score_trend": _rolling_score_trend(rolling_scores),
                "recurrence": recurrence,
                "snapshot_appearances": appearances,
                "trend": row.get("trend_evidence", {}).get("classification") if isinstance(row.get("trend_evidence"), Mapping) else None,
                "anomaly_count": anomaly_count,
                "transition": transition,
                "previous_priority": previous_priority,
                "rationale": "; ".join(rationale_parts),
                "promotion_signals": promotion_signals,
                "demotion_signals": demotion_signals,
            }
        )
    queue.sort(
        key=lambda item: (
            -PRIORITY_RANK[item["priority"]],
            -item["risk_score"],
            -item["rolling_average_score"],
            item["dimension"],
            item["contributor"],
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "empty" if not queue else "ok",
        "risk_history_snapshot_count": len(snapshots),
        "thresholds": {
            "priority_score_minimums": dict(PRIORITY_THRESHOLDS),
            "minimum_snapshot_appearances": MINIMUM_SNAPSHOT_APPEARANCES,
            "minimum_recurrence_for_promotion": "recurring",
            "minimum_risk_observations_for_schedule": MINIMUM_RISK_OBSERVATIONS_FOR_SCHEDULE,
            "rolling_window_reports": window,
            "score_trend_absolute_delta": SCORE_TREND_DELTA_THRESHOLD,
            "prioritize_requires": "persistent recurrence and rolling average >= 60",
            "urgent_requires": "dominant recurrence, anomaly participation, and rolling average >= 80",
        },
        "queue": queue,
        "promotions": [item for item in queue if item["transition"] == "promotion"],
        "demotions": [item for item in queue if item["transition"] == "demotion"],
        "stable_entries": [item for item in queue if item["transition"] == "stable"],
        "recommendations": (
            ["Collect BP8 risk reports before assigning remediation priority."]
            if not queue
            else [
                "Address urgent and prioritize entries first, using each item's promotion and demotion signals.",
                "Keep stability protections advisory until risk-history calibration demonstrates low queue churn.",
            ]
        ),
    }


def risk_snapshot_from_queue(
    risk_report: Mapping[str, Any], queue_report: Mapping[str, Any], *, timestamp: str
) -> dict[str, Any]:
    queue_index = {
        (str(item.get("dimension")), str(item.get("contributor"))): item
        for item in queue_report.get("queue", [])
        if isinstance(item, Mapping)
    }
    contributors = []
    for row in _risk_rows(risk_report):
        key = (str(row.get("dimension")), str(row.get("name")))
        queue_item = queue_index.get(key, {})
        contributors.append(
            {
                "timestamp": str(timestamp),
                "contributor": key[1],
                "dimension": key[0],
                "score": _number(row.get("risk_score")),
                "risk_classification": row.get("risk_classification"),
                "priority": queue_item.get("priority", "monitor"),
                "recurrence": queue_item.get("recurrence", "transient"),
                "snapshot_appearances": int(queue_item.get("snapshot_appearances") or 0),
                "anomaly_count": int(queue_item.get("anomaly_count") or 0),
            }
        )
    contributors.sort(key=lambda row: (row["dimension"], row["contributor"]))
    return {"timestamp": str(timestamp), "contributors": contributors}


def _queue_section(title: str, rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Priority | Contributor | Dimension | Risk | Delta | Rolling Avg | Score Trend | Recurrence | Anomalies | Why |",
        "|---|---|---|---:|---:|---:|---|---|---:|---|",
    ]
    if rows:
        for row in rows:
            delta = "n/a" if row.get("score_delta") is None else f"{_number(row.get('score_delta')):+g}"
            lines.append(
                f"| `{row.get('priority')}` | `{row.get('contributor')}` | `{row.get('dimension')}` | "
                f"{_number(row.get('risk_score')):g} | {delta} | {_number(row.get('rolling_average_score')):.2f} | "
                f"`{row.get('rolling_score_trend')}` | `{row.get('recurrence')}` | "
                f"{row.get('anomaly_count')} | {row.get('rationale')} |"
            )
    else:
        lines.append("| _none_ | - | - | 0 | - | 0 | - | - | 0 | No entries. |")
    return lines


def render_remediation_queue_markdown(report: Mapping[str, Any]) -> str:
    thresholds = report.get("thresholds") if isinstance(report.get("thresholds"), Mapping) else {}
    queue = report.get("queue") if isinstance(report.get("queue"), list) else []
    lines = [
        "# Fallback Remediation Priority Queue",
        "",
        "> Advisory-only maintenance prioritization derived from BP8 risk output.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Queue entries: {len(queue)}",
        f"- Prior risk snapshots: {report.get('risk_history_snapshot_count', 0)}",
        "- Priority score bands: monitor <25, investigate 25+, schedule 40+, prioritize 60+, urgent 80+.",
        f"- Stability: at least {thresholds.get('minimum_snapshot_appearances', 2)} appearances and recurring classification before promotion.",
        "- Schedule and above require two risk observations and a qualifying rolling average.",
        "- Prioritize requires persistent recurrence; urgent requires dominant recurrence plus anomaly participation.",
        "",
    ]
    lines.extend(_queue_section("Priority Queue", queue))
    lines.extend([""] + _queue_section("Promotions", report.get("promotions", [])))
    lines.extend([""] + _queue_section("Demotions", report.get("demotions", [])))
    lines.extend([""] + _queue_section("Stable Entries", report.get("stable_entries", [])))
    lines.extend(["", "## Recommendations", ""])
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_queue_artifacts(
    report: Mapping[str, Any], *, json_path: Path | str, markdown_path: Path | str
) -> tuple[Path, Path]:
    json_out, markdown_out = Path(json_path), Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_remediation_queue_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--risk-report", type=Path, default=DEFAULT_RISK_REPORT_PATH)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--timestamp")
    parser.add_argument("--rolling-window", type=int, default=DEFAULT_ROLLING_WINDOW)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        risk_report = json.loads(args.risk_report.read_text(encoding="utf-8"))
        if not isinstance(risk_report, Mapping):
            raise ValueError("risk report root must be a JSON object")
        history = load_risk_history(args.history)
        report = build_remediation_queue(risk_report, history, rolling_window=args.rolling_window)
        snapshot = risk_snapshot_from_queue(
            risk_report, report, timestamp=args.timestamp or _utc_timestamp()
        )
        write_risk_history(append_risk_snapshot(history, snapshot), args.history)
        json_out, markdown_out = write_queue_artifacts(
            report, json_path=args.json_out, markdown_path=args.md_out
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback remediation queue failed: {exc}", file=sys.stderr)
        return 2
    print(f"Appended risk snapshot to {args.history}")
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback remediation queue: {report['status']} entries={len(report['queue'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
