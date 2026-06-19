#!/usr/bin/env python3
"""Track advisory remediation effectiveness using BP8/BP9 artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
DEFAULT_REGISTRY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_registry.json"
DEFAULT_RISK_HISTORY_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_risk_history.json"
DEFAULT_QUEUE_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_queue.json"
DEFAULT_JSON_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_effectiveness.json"
DEFAULT_MARKDOWN_PATH = ROOT / "artifacts" / "golden_replay" / "fallback_remediation_effectiveness.md"

VALID_STATUSES = {"proposed", "accepted", "in_progress", "completed", "abandoned"}
ACTIVE_STATUSES = {"proposed", "accepted", "in_progress"}
MEANINGFUL_RISK_CHANGE = 5.0
RESOLVED_RISK_MAXIMUM = 10.0
MINIMUM_POST_COMPLETION_SNAPSHOTS = 2
RECURRENCE_RANK = {"absent": -1, "transient": 0, "recurring": 1, "persistent": 2, "dominant": 3}
EFFECTIVENESS_RANK = {"regressed": 0, "unchanged": 1, "improved": 2, "resolved": 3}


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def empty_registry() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "remediations": []}


def load_registry(path: Path | str) -> dict[str, Any]:
    registry_path = Path(path)
    if not registry_path.is_file():
        return empty_registry()
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("remediations"), list):
        raise ValueError("remediation registry must contain a remediations list")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported remediation registry schema_version: {raw.get('schema_version')!r}")
    return {
        "schema_version": SCHEMA_VERSION,
        "remediations": [dict(item) for item in raw["remediations"] if isinstance(item, Mapping)],
    }


def write_registry(registry: Mapping[str, Any], path: Path | str) -> Path:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry_path


def _snapshot_rows(snapshot: Mapping[str, Any]) -> dict[tuple[str, str], Mapping[str, Any]]:
    contributors = snapshot.get("contributors")
    if not isinstance(contributors, list):
        return {}
    return {
        (str(row.get("dimension")), str(row.get("contributor"))): row
        for row in contributors
        if isinstance(row, Mapping) and row.get("dimension") and row.get("contributor")
    }


def _observations(risk_history: Mapping[str, Any], key: tuple[str, str]) -> list[dict[str, Any]]:
    snapshots = risk_history.get("snapshots")
    if not isinstance(snapshots, list):
        return []
    prepared: list[tuple[int, Mapping[str, Any], datetime, Mapping[str, Any] | None]] = []
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, Mapping):
            continue
        parsed = _timestamp(snapshot.get("timestamp"))
        if parsed is None:
            continue
        row = _snapshot_rows(snapshot).get(key)
        prepared.append((index, snapshot, parsed, row))
    first_present = next((index for index, item in enumerate(prepared) if item[3] is not None), None)
    if first_present is None:
        return []
    observations: list[dict[str, Any]] = []
    for index, snapshot, parsed, row in prepared[first_present:]:
        observations.append(
            {
                "timestamp": str(snapshot.get("timestamp")),
                "parsed_timestamp": parsed,
                "score": _number(row.get("score")) if row is not None else 0.0,
                "risk_classification": row.get("risk_classification") if row is not None else "negligible",
                "recurrence": str(row.get("recurrence") or "absent") if row is not None else "absent",
                "anomaly_count": int(row.get("anomaly_count") or 0) if row is not None else 0,
                "source_index": index,
            }
        )
    return sorted(observations, key=lambda row: (row["parsed_timestamp"], row["source_index"]))


def _queue_index(queue_report: Mapping[str, Any]) -> dict[tuple[str, str], Mapping[str, Any]]:
    rows = queue_report.get("queue")
    if not isinstance(rows, list):
        return {}
    return {
        (str(row.get("dimension")), str(row.get("contributor"))): row
        for row in rows
        if isinstance(row, Mapping) and row.get("dimension") and row.get("contributor")
    }


def _opening_observation(observations: Sequence[Mapping[str, Any]], opened: datetime | None) -> Mapping[str, Any] | None:
    if not observations:
        return None
    if opened is None:
        return observations[0]
    before = [row for row in observations if row["parsed_timestamp"] <= opened]
    return before[-1] if before else next(
        (row for row in observations if row["parsed_timestamp"] >= opened), None
    )


def _completion_observation(
    observations: Sequence[Mapping[str, Any]], closed: datetime | None
) -> Mapping[str, Any] | None:
    if not observations or closed is None:
        return None
    return next((row for row in observations if row["parsed_timestamp"] >= closed), None)


def _trajectory(before: float | None, current: float | None) -> str:
    if before is None or current is None:
        return "insufficient_history"
    delta = current - before
    if delta <= -MEANINGFUL_RISK_CHANGE:
        return "decreasing"
    if delta >= MEANINGFUL_RISK_CHANGE:
        return "increasing"
    return "stable"


def _effectiveness_entry(
    remediation: Mapping[str, Any],
    risk_history: Mapping[str, Any],
    queue_rows: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    remediation_id = str(remediation.get("remediation_id") or "")
    contributor = str(remediation.get("contributor") or "")
    dimension = str(remediation.get("dimension") or "")
    status = str(remediation.get("status") or "proposed")
    key = (dimension, contributor)
    observations = _observations(risk_history, key)
    opened = _timestamp(remediation.get("opened_timestamp"))
    closed = _timestamp(remediation.get("closed_timestamp"))
    opening = _opening_observation(observations, opened)
    completion = _completion_observation(observations, closed) if status == "completed" else None
    post_completion = (
        [row for row in observations if closed is not None and row["parsed_timestamp"] > closed]
        if status == "completed"
        else []
    )
    latest = observations[-1] if observations else None
    queue_row = queue_rows.get(key)
    before_risk = _number(opening.get("score")) if opening is not None else None
    completion_risk = _number(completion.get("score")) if completion is not None else None
    current_risk = (
        _number(queue_row.get("risk_score"))
        if queue_row is not None
        else (_number(latest.get("score")) if latest is not None else None)
    )
    after_risk = (
        _number(post_completion[-1].get("score"))
        if post_completion
        else (current_risk if status == "completed" and closed is not None and latest is not None and latest["parsed_timestamp"] > closed else None)
    )
    evaluation_risk = after_risk if after_risk is not None else (completion_risk if completion_risk is not None else current_risk)
    delta_risk = evaluation_risk - before_risk if evaluation_risk is not None and before_risk is not None else None
    absolute_reduction = before_risk - evaluation_risk if evaluation_risk is not None and before_risk is not None else None
    percentage_reduction = (
        absolute_reduction / before_risk
        if absolute_reduction is not None and before_risk not in (None, 0.0)
        else None
    )
    improvement_observation = None
    if before_risk is not None:
        improvement_observation = next(
            (
                row
                for row in observations
                if (opened is None or row["parsed_timestamp"] >= opened)
                and _number(row.get("score")) <= before_risk - MEANINGFUL_RISK_CHANGE
            ),
            None,
        )
    time_to_improvement_hours = (
        (improvement_observation["parsed_timestamp"] - opened).total_seconds() / 3600
        if improvement_observation is not None and opened is not None
        else None
    )
    completion_recurrence = str(completion.get("recurrence") or "absent") if completion is not None else None
    completion_anomalies = int(completion.get("anomaly_count") or 0) if completion is not None else None
    current_recurrence = (
        str(queue_row.get("recurrence") or "absent")
        if queue_row is not None
        else (str(latest.get("recurrence") or "absent") if latest is not None else "absent")
    )
    current_anomalies = (
        int(queue_row.get("anomaly_count") or 0)
        if queue_row is not None
        else (int(latest.get("anomaly_count") or 0) if latest is not None else 0)
    )
    risk_returned = bool(
        completion_risk is not None
        and after_risk is not None
        and after_risk >= completion_risk + MEANINGFUL_RISK_CHANGE
    )
    recurrence_returned = bool(
        completion_recurrence is not None
        and RECURRENCE_RANK.get(current_recurrence, -1) > RECURRENCE_RANK.get(completion_recurrence, -1)
        and RECURRENCE_RANK.get(current_recurrence, -1) >= RECURRENCE_RANK["recurring"]
    )
    anomaly_returned = bool(
        completion_anomalies is not None and completion_anomalies == 0 and current_anomalies > 0
    )
    regression_reasons = []
    if risk_returned:
        regression_reasons.append("risk returned by at least 5 points after closure")
    if recurrence_returned:
        regression_reasons.append("recurrence returned after closure")
    if anomaly_returned:
        regression_reasons.append("anomaly participation returned after closure")
    if delta_risk is not None and delta_risk >= MEANINGFUL_RISK_CHANGE:
        regression_reasons.append("current risk exceeds opening risk by at least 5 points")
    if regression_reasons:
        effectiveness = "regressed"
    elif (
        status == "completed"
        and evaluation_risk is not None
        and evaluation_risk <= RESOLVED_RISK_MAXIMUM
        and current_recurrence in {"absent", "transient"}
        and current_anomalies == 0
    ):
        effectiveness = "resolved"
    elif absolute_reduction is not None and absolute_reduction >= MEANINGFUL_RISK_CHANGE:
        effectiveness = "improved"
    else:
        effectiveness = "unchanged"
    sustained_improvement = bool(
        status == "completed"
        and before_risk is not None
        and len(post_completion) >= MINIMUM_POST_COMPLETION_SNAPSHOTS
        and all(_number(row.get("score")) <= before_risk - MEANINGFUL_RISK_CHANGE for row in post_completion)
        and not regression_reasons
    )
    original_recurrence = str(opening.get("recurrence") or "absent") if opening is not None else None
    original_anomalies = int(opening.get("anomaly_count") or 0) if opening is not None else None
    return {
        "remediation_id": remediation_id,
        "contributor": contributor,
        "dimension": dimension,
        "opened_timestamp": remediation.get("opened_timestamp"),
        "closed_timestamp": remediation.get("closed_timestamp"),
        "status": status if status in VALID_STATUSES else "proposed",
        "effectiveness_classification": effectiveness,
        "before_risk": before_risk,
        "completion_risk": completion_risk,
        "after_risk": after_risk,
        "current_risk": current_risk,
        "delta_risk": delta_risk,
        "absolute_risk_reduction": absolute_reduction,
        "percentage_risk_reduction": percentage_reduction,
        "time_to_improvement_hours": time_to_improvement_hours,
        "improvement_first_seen": improvement_observation.get("timestamp") if improvement_observation else None,
        "sustained_improvement": sustained_improvement,
        "post_completion_snapshot_count": len(post_completion),
        "recurrence_changes": {
            "original": original_recurrence,
            "at_completion": completion_recurrence,
            "current": current_recurrence,
            "returned_after_closure": recurrence_returned,
        },
        "anomaly_changes": {
            "original_count": original_anomalies,
            "at_completion_count": completion_anomalies,
            "current_count": current_anomalies,
            "returned_after_closure": anomaly_returned,
        },
        "trend_changes": {
            "open_to_completion": _trajectory(before_risk, completion_risk),
            "open_to_current": _trajectory(before_risk, evaluation_risk),
            "current_queue_trend": queue_row.get("trend") if queue_row is not None else None,
        },
        "regression_evidence": {
            "risk_returned_after_closure": risk_returned,
            "recurrence_returned_after_closure": recurrence_returned,
            "anomaly_returned_after_closure": anomaly_returned,
            "reasons": sorted(set(regression_reasons)),
        },
        "evidence": {
            "risk_snapshot_count": len(observations),
            "opening_snapshot": opening.get("timestamp") if opening else None,
            "completion_snapshot": completion.get("timestamp") if completion else None,
            "latest_snapshot": latest.get("timestamp") if latest else None,
            "queue_entry_available": queue_row is not None,
        },
    }


def build_remediation_effectiveness_report(
    registry: Mapping[str, Any],
    risk_history: Mapping[str, Any],
    queue_report: Mapping[str, Any],
) -> dict[str, Any]:
    records = registry.get("remediations")
    records = records if isinstance(records, list) else []
    queue_rows = _queue_index(queue_report)
    entries = [
        _effectiveness_entry(record, risk_history, queue_rows)
        for record in records
        if isinstance(record, Mapping)
    ]
    entries.sort(key=lambda row: (str(row["remediation_id"]), row["dimension"], row["contributor"]))
    active = [row for row in entries if row["status"] in ACTIVE_STATUSES]
    completed = [row for row in entries if row["status"] == "completed"]
    most_effective = sorted(
        [row for row in completed if row["effectiveness_classification"] in {"resolved", "improved"}],
        key=lambda row: (-_number(row.get("absolute_risk_reduction")), row["remediation_id"]),
    )
    regressions = sorted(
        [row for row in completed if row["effectiveness_classification"] == "regressed"],
        key=lambda row: (-_number(row.get("current_risk")), row["remediation_id"]),
    )
    counts = {
        classification: sum(row["effectiveness_classification"] == classification for row in entries)
        for classification in ("resolved", "improved", "unchanged", "regressed")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "no_remediations" if not entries else "ok",
        "thresholds": {
            "meaningful_risk_change": MEANINGFUL_RISK_CHANGE,
            "resolved_risk_maximum": RESOLVED_RISK_MAXIMUM,
            "minimum_post_completion_snapshots_for_sustained_improvement": MINIMUM_POST_COMPLETION_SNAPSHOTS,
        },
        "summary": {
            "remediation_count": len(entries),
            "active_count": len(active),
            "completed_count": len(completed),
            "classification_counts": counts,
        },
        "remediations": entries,
        "active_remediations": active,
        "completed_remediations": completed,
        "most_effective_changes": most_effective,
        "regressions": regressions,
        "improvement_trends": sorted(
            entries,
            key=lambda row: (
                EFFECTIVENESS_RANK[row["effectiveness_classification"]],
                -_number(row.get("absolute_risk_reduction")),
                row["remediation_id"],
            ),
        ),
        "recommendations": (
            ["Register remediation work before evaluating effectiveness."]
            if not entries
            else [
                "Review regressed remediations first and compare their recurrence and anomaly return evidence.",
                "Require at least two post-completion snapshots before treating improvement as sustained.",
            ]
        ),
    }


def _format_number(value: Any) -> str:
    if value is None:
        return "n/a"
    number = _number(value)
    return str(int(number)) if number.is_integer() else f"{number:.2f}"


def _entries_section(title: str, entries: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Remediation | Status | Effectiveness | Contributor | Before | Completion | Current | Reduction | Sustained | Recurrence Change | Anomaly Change | Trend |",
        "|---|---|---|---|---:|---:|---:|---:|---|---|---|---|",
    ]
    if entries:
        for row in entries:
            recurrence = row.get("recurrence_changes", {})
            anomalies = row.get("anomaly_changes", {})
            trends = row.get("trend_changes", {})
            lines.append(
                f"| `{row.get('remediation_id')}` | `{row.get('status')}` | "
                f"`{row.get('effectiveness_classification')}` | `{row.get('dimension')}/{row.get('contributor')}` | "
                f"{_format_number(row.get('before_risk'))} | {_format_number(row.get('completion_risk'))} | "
                f"{_format_number(row.get('current_risk'))} | {_format_number(row.get('absolute_risk_reduction'))} | "
                f"`{str(bool(row.get('sustained_improvement'))).lower()}` | "
                f"`{recurrence.get('original')} -> {recurrence.get('current')}` | "
                f"`{anomalies.get('original_count')} -> {anomalies.get('current_count')}` | "
                f"`{trends.get('open_to_current')}` |"
            )
    else:
        lines.append("| _none_ | - | - | - | - | - | - | - | - | - | - | - |")
    return lines


def render_remediation_effectiveness_markdown(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    counts = summary.get("classification_counts") if isinstance(summary.get("classification_counts"), Mapping) else {}
    lines = [
        "# Fallback Remediation Effectiveness",
        "",
        "> Advisory-only lifecycle analysis derived from BP8 risk history and the BP9 queue.",
        "",
        "## Executive Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Registered remediations: {summary.get('remediation_count', 0)}",
        f"- Active: {summary.get('active_count', 0)}; completed: {summary.get('completed_count', 0)}",
        f"- Resolved: {counts.get('resolved', 0)}; improved: {counts.get('improved', 0)}; unchanged: {counts.get('unchanged', 0)}; regressed: {counts.get('regressed', 0)}",
        "- Meaningful movement: 5 risk points; resolved risk: 10 or below.",
        "- Sustained improvement requires two post-completion snapshots that remain improved.",
        "",
    ]
    lines.extend(_entries_section("Active Remediations", report.get("active_remediations", [])))
    lines.extend([""] + _entries_section("Completed Remediations", report.get("completed_remediations", [])))
    lines.extend([""] + _entries_section("Most Effective Changes", report.get("most_effective_changes", [])))
    lines.extend([""] + _entries_section("Regressions", report.get("regressions", [])))
    lines.extend([""] + _entries_section("Improvement Trends", report.get("improvement_trends", [])))
    lines.extend(["", "## Recommendations", ""])
    for recommendation in report.get("recommendations", []):
        lines.append(f"- {recommendation}")
    lines.append("")
    return "\n".join(lines)


def write_effectiveness_artifacts(
    report: Mapping[str, Any], *, json_path: Path | str, markdown_path: Path | str
) -> tuple[Path, Path]:
    json_out, markdown_out = Path(json_path), Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_remediation_effectiveness_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _load_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} root must be a JSON object")
    return dict(raw)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--risk-history", type=Path, default=DEFAULT_RISK_HISTORY_PATH)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        registry = load_registry(args.registry)
        if not args.registry.is_file():
            write_registry(registry, args.registry)
        risk_history = _load_object(args.risk_history, "risk history")
        queue_report = _load_object(args.queue, "remediation queue")
        report = build_remediation_effectiveness_report(registry, risk_history, queue_report)
        json_out, markdown_out = write_effectiveness_artifacts(
            report, json_path=args.json_out, markdown_path=args.md_out
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback remediation effectiveness failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {args.registry}")
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Fallback remediation effectiveness: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
