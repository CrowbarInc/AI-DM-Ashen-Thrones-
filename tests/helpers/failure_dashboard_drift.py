"""Drift artifact writing and orchestration for replay diagnostics.

Consumes drift analytics from replay_drift_reports.py, paths from
failure_dashboard_paths.py, and session buffers from failure_dashboard_session.py.
Recurrence side-effects for risk artifacts delegate to failure_dashboard_recurrence.py.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_paths import (
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH,
    OWNER_DRIFT_HOTSPOTS_JSON_PATH,
    OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH,
    OWNER_DRIFT_LONGITUDINAL_JSON_PATH,
    OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH,
    OWNER_DRIFT_RISK_JSON_PATH,
    OWNER_DRIFT_RISK_MARKDOWN_PATH,
    OWNER_DRIFT_TRENDS_JSON_PATH,
    OWNER_DRIFT_TRENDS_MARKDOWN_PATH,
    BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH,
    RERUN_DRIFT_SCORECARD_ENV_VAR,
    RERUN_DRIFT_SCORECARD_JSON_PATH,
    RERUN_DRIFT_SCORECARD_MARKDOWN_PATH,
)
from tests.helpers.failure_dashboard_recurrence import write_bug_recurrence_history_artifacts
from tests.helpers.failure_dashboard_session import (
    recorded_failure_dashboard_rows,
    recorded_long_session_stability_scorecards,
    recorded_protected_replay_failure_rows,
    recorded_rerun_drift_scorecards,
)
from tests.helpers.replay_drift_reports import (
    aggregate_owner_drift_history,
    build_hotspot_rankings,
    build_owner_drift_trend_summary,
    build_risk_payload,
    build_trend_payload,
    classification_rows_for_analysis,
    classification_rows_from_scorecards,
    enrich_hotspots_with_field_trends,
    render_owner_drift_hotspot_report,
    render_owner_drift_longitudinal_report,
    render_owner_drift_risk_report,
    render_owner_drift_trend_report,
    summarize_owner_drift_buckets,
)


def _cell(value: Any) -> str:
    if value is None or value == "":
        text = "none"
    elif isinstance(value, (list, tuple, set, frozenset)):
        text = ", ".join(str(item) for item in value if str(item).strip()) or "none"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _owner_drift_summary_table_lines(counts: Mapping[str, int]) -> list[str]:
    """Render owner drift bucket frequency table for scorecard/failure reports."""
    non_zero = [(bucket, count) for bucket, count in sorted(counts.items()) if count > 0]
    lines = ["", "## Owner Drift Summary", ""]
    if not non_zero:
        lines.extend(["No owner drift classifications.", ""])
        return lines
    lines.extend(
        [
            "| Owner Drift Bucket | Count |",
            "|---|---:|",
        ]
    )
    for bucket, count in non_zero:
        lines.append(f"| `{bucket}` | `{count}` |")
    lines.append("")
    return lines


def _owner_drift_breakdown_lines(counts: Mapping[str, int]) -> list[str]:
    """Render dot-aligned owner drift breakdown for protected failure reports."""
    non_zero = [(bucket, count) for bucket, count in sorted(counts.items()) if count > 0]
    lines = ["", "## Owner Drift Breakdown", ""]
    if not non_zero:
        lines.extend(["No owner drift buckets recorded.", ""])
        return lines
    width = max(len(bucket) for bucket, _count in non_zero)
    lines.append("```")
    for bucket, count in non_zero:
        dots = "." * max(1, 18 - (width - len(bucket)))
        lines.append(f"{bucket.ljust(width)} {dots} {count}")
    lines.extend(["```", ""])
    return lines


def rerun_drift_scorecard_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return whether successful rerun drift diagnostics should be written."""
    env_map = env if env is not None else os.environ
    return str(env_map.get(RERUN_DRIFT_SCORECARD_ENV_VAR) or "").strip().lower() in {"1", "true", "yes", "on"}


def scorecards_for_longitudinal_aggregation(
    current: Mapping[str, Any] | None = None,
) -> list[Mapping[str, Any]]:
    """Return scorecard history for longitudinal aggregation."""
    recorded = recorded_rerun_drift_scorecards()
    if recorded:
        return recorded
    if isinstance(current, Mapping) and current.get("comparison_available") is not False:
        return [current]
    return []


def write_owner_drift_longitudinal_artifacts(
    scorecards: Sequence[Mapping[str, Any]] | None = None,
    *,
    json_path: Path | str = OWNER_DRIFT_LONGITUDINAL_JSON_PATH,
    markdown_path: Path | str = OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH,
    command_used: str | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    """Write advisory longitudinal owner drift JSON and markdown artifacts."""
    history = aggregate_owner_drift_history(scorecards)
    payload = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        **history,
        "trend_summary": build_owner_drift_trend_summary(history),
    }
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_owner_drift_longitudinal_report(
            history,
            generated_at=generated_at,
            command_used=command_used,
        ),
        encoding="utf-8",
    )
    return json_out, markdown_out


def append_owner_drift_longitudinal_markdown(
    markdown_path: Path | str,
    scorecards: Sequence[Mapping[str, Any]] | None,
    *,
    command_used: str | None = None,
    generated_at: str | None = None,
) -> None:
    """Append longitudinal owner drift summary to an existing markdown artifact."""
    path = Path(markdown_path)
    if not path.exists():
        return
    history = aggregate_owner_drift_history(scorecards)
    appendix = render_owner_drift_longitudinal_report(
        history,
        generated_at=generated_at,
        command_used=command_used,
    )
    existing = path.read_text(encoding="utf-8").rstrip()
    path.write_text(f"{existing}\n\n{appendix}\n", encoding="utf-8")


def collected_hotspot_classifications(
    *,
    failure_rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[Mapping[str, Any]]:
    """Collect classification rows available for hotspot aggregation."""
    rows: list[Mapping[str, Any]] = []
    if failure_rows is not None:
        rows.extend(row for row in failure_rows if isinstance(row, Mapping))
    else:
        rows.extend(recorded_protected_replay_failure_rows())
        rows.extend(recorded_failure_dashboard_rows())
    rows.extend(classification_rows_from_scorecards(recorded_rerun_drift_scorecards()))
    return rows


def write_owner_drift_hotspot_artifacts(
    classifications: Sequence[Mapping[str, Any]] | None = None,
    *,
    json_path: Path | str = OWNER_DRIFT_HOTSPOTS_JSON_PATH,
    markdown_path: Path | str = OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH,
    scorecard_history: Sequence[Mapping[str, Any]] | None = None,
    command_used: str | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    """Write advisory owner drift hotspot JSON and markdown artifacts."""
    rows = collected_hotspot_classifications() if classifications is None else list(classifications)
    history = (
        list(scorecard_history)
        if scorecard_history is not None
        else recorded_rerun_drift_scorecards()
    )
    hotspots = enrich_hotspots_with_field_trends(build_hotspot_rankings(rows), history)
    payload = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        **hotspots,
    }
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_owner_drift_hotspot_report(
            hotspots,
            generated_at=generated_at,
            command_used=command_used,
        ),
        encoding="utf-8",
    )
    return json_out, markdown_out


def write_owner_drift_trend_artifacts(
    scorecard_history: Sequence[Mapping[str, Any]] | None = None,
    *,
    json_path: Path | str = OWNER_DRIFT_TRENDS_JSON_PATH,
    markdown_path: Path | str = OWNER_DRIFT_TRENDS_MARKDOWN_PATH,
    command_used: str | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    """Write advisory owner drift trend JSON and markdown artifacts."""
    history = (
        list(scorecard_history)
        if scorecard_history is not None
        else recorded_rerun_drift_scorecards()
    )
    payload = build_trend_payload(history)
    trends = payload.get("owner_drift_trends") if isinstance(payload.get("owner_drift_trends"), Mapping) else {}
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_owner_drift_trend_report(
            trends,
            generated_at=generated_at,
            command_used=command_used,
        ),
        encoding="utf-8",
    )
    return json_out, markdown_out


def write_owner_drift_risk_artifacts(
    classifications: Sequence[Mapping[str, Any]] | None = None,
    *,
    json_path: Path | str = OWNER_DRIFT_RISK_JSON_PATH,
    markdown_path: Path | str = OWNER_DRIFT_RISK_MARKDOWN_PATH,
    recurrence_json_path: Path | str | None = None,
    recurrence_markdown_path: Path | str | None = None,
    recurrence_event_log_path: Path | str | None = None,
    recurrence_session_diagnostic_event_log_path: Path | str | None = None,
    recurrence_session_event_log_path: Path | str | None = None,
    recurrence_synthetic_test_artifact_event_log_path: Path | str | None = None,
    scorecard_history: Sequence[Mapping[str, Any]] | None = None,
    command_used: str | None = None,
    generated_at: str | None = None,
    recurrence_event_metadata: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    """Write advisory owner drift risk JSON and markdown artifacts."""
    history = (
        list(scorecard_history)
        if scorecard_history is not None
        else recorded_rerun_drift_scorecards()
    )
    stability_history = recorded_long_session_stability_scorecards()
    source_rows = collected_hotspot_classifications() if classifications is None else list(classifications)
    rows = classification_rows_for_analysis(source_rows, scorecard_history=history)
    payload = build_risk_payload(
        rows,
        scorecard_history=history,
        stability_scorecards=stability_history,
    )
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_owner_drift_risk_report(
            payload,
            generated_at=generated_at,
            command_used=command_used,
        ),
        encoding="utf-8",
    )
    write_bug_recurrence_history_artifacts(
        rows,
        json_path=(
            Path(recurrence_json_path)
            if recurrence_json_path is not None
            else json_out.with_name(BUG_RECURRENCE_HISTORY_JSON_PATH.name)
        ),
        markdown_path=(
            Path(recurrence_markdown_path)
            if recurrence_markdown_path is not None
            else markdown_out.with_name(BUG_RECURRENCE_HISTORY_MARKDOWN_PATH.name)
        ),
        event_log_path=recurrence_event_log_path,
        session_diagnostic_event_log_path=recurrence_session_diagnostic_event_log_path,
        session_event_log_path=recurrence_session_event_log_path,
        synthetic_test_artifact_event_log_path=recurrence_synthetic_test_artifact_event_log_path,
        command_used=command_used,
        generated_at=generated_at,
        recurrence_event_metadata=recurrence_event_metadata,
    )
    return json_out, markdown_out


def _scorecard_summary(scorecard: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(scorecard, Mapping):
        return {}
    summary = scorecard.get("summary")
    return summary if isinstance(summary, Mapping) else {}


def _nested_delta(scorecard: Mapping[str, Any] | None, key: str) -> Mapping[str, Any]:
    if not isinstance(scorecard, Mapping):
        return {}
    frequencies = scorecard.get("frequencies")
    if not isinstance(frequencies, Mapping):
        return {}
    response_delta = frequencies.get("response_delta")
    if not isinstance(response_delta, Mapping):
        return {}
    item = response_delta.get(key)
    if not isinstance(item, Mapping):
        return {}
    delta = item.get("delta")
    return delta if isinstance(delta, Mapping) else {}


def render_rerun_drift_scorecard_markdown(
    scorecard: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
) -> str:
    """Render an operator-readable report-only rerun drift scorecard."""
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command_s = command_used if command_used is not None else " ".join(sys.argv)
    lines = [
        "# Golden Rerun Drift Scorecard",
        "",
        f"- Generated at: `{generated_at_s}`",
        f"- Command: `{command_s or 'unavailable'}`",
        "- Report only: `true`",
        "",
    ]
    if not isinstance(scorecard, Mapping) or scorecard.get("comparison_available") is False:
        reason = "no rerun comparison available"
        if isinstance(scorecard, Mapping) and scorecard.get("reason"):
            reason = str(scorecard.get("reason"))
        lines.extend(
            [
                "## Summary",
                "",
                f"No rerun comparison available: {reason}.",
                "",
            ]
        )
        return "\n".join(lines)

    summary = _scorecard_summary(scorecard)
    lines.extend(
        [
            "## Summary",
            "",
            f"- Total turns compared: `{scorecard.get('total_turns_compared', 0)}`",
            f"- Speaker deltas: `{summary.get('speaker_delta_count', 0)}`",
            f"- Route deltas: `{summary.get('route_delta_count', 0)}`",
            f"- Fallback deltas: `{summary.get('fallback_delta_count', 0)}`",
            f"- Text fingerprint deltas: `{summary.get('text_fingerprint_delta_count', 0)}`",
            f"- Scaffold predicate deltas: `{summary.get('scaffold_delta_count', 0)}`",
            f"- Runtime-lineage deltas: `{summary.get('runtime_lineage_delta_count', 0)}`",
            f"- Semantic delta frequency deltas: `{summary.get('semantic_delta_frequency_delta_count', 0)}`",
            "",
        ]
    )
    owner_classifications = scorecard.get("owner_drift_classifications")
    if isinstance(owner_classifications, list):
        lines.extend(_owner_drift_summary_table_lines(summarize_owner_drift_buckets(owner_classifications)))
    else:
        lines.extend(_owner_drift_summary_table_lines({}))
    lines.extend(
        [
            "## Semantic Delta Frequency",
            "",
            f"- Response-delta checked delta: `{_nested_delta(scorecard, 'checked')}`",
            f"- Response-delta failed delta: `{_nested_delta(scorecard, 'failed')}`",
            f"- Response-delta repaired delta: `{_nested_delta(scorecard, 'repaired')}`",
            f"- Response-delta kind deltas: `{_nested_delta(scorecard, 'kinds')}`",
            f"- Echo-overlap band deltas: `{_nested_delta(scorecard, 'echo_overlap_bands')}`",
            f"- Response-delta unknown delta: `{_nested_delta(scorecard, 'unknown')}`",
            "",
            "## Compact Per-Turn Drift Rows",
            "",
        ]
    )
    rows = scorecard.get("per_turn_deltas")
    if not isinstance(rows, (list, tuple)) or not rows:
        lines.extend(["No per-turn drift rows.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Turn | Previous Turn ID | Current Turn ID | Drift Fields | Details |",
            "|---:|---|---|---|---|",
        ]
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        deltas = row.get("deltas") if isinstance(row.get("deltas"), Mapping) else {}
        fields = ", ".join(str(key) for key in sorted(deltas)) or "none"
        details: list[str] = []
        for key in sorted(deltas):
            value = deltas.get(key)
            if not isinstance(value, Mapping):
                details.append(f"{key}=changed")
                continue
            if key == "text_fingerprint":
                details.append(f"text_hash {value.get('previous')} -> {value.get('current')}")
            elif key == "fallback":
                details.append(
                    "fallback "
                    f"{value.get('previous_family')}/{value.get('previous_owner')} -> "
                    f"{value.get('current_family')}/{value.get('current_owner')}"
                )
            elif key == "runtime_lineage":
                details.append(
                    "runtime_lineage "
                    f"events_delta={value.get('total_event_delta', 0)} "
                    f"changed_keys={value.get('changed_key_count', 0)}"
                )
            elif key == "response_delta":
                changed = ", ".join(str(field) for field in sorted(value)) or "metadata"
                details.append(f"response_delta {changed}")
            else:
                details.append(f"{key} {value.get('previous')} -> {value.get('current')}")
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("turn_index")),
                    _cell(row.get("previous_turn_id")),
                    _cell(row.get("current_turn_id")),
                    _cell(fields),
                    _cell("; ".join(details) or "none"),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _no_rerun_scorecard() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "report_only": True,
        "comparison_available": False,
        "reason": "no rerun comparison available",
    }


def write_rerun_drift_scorecard_artifacts(
    scorecard: Mapping[str, Any] | None = None,
    *,
    json_path: Path | str = RERUN_DRIFT_SCORECARD_JSON_PATH,
    markdown_path: Path | str = RERUN_DRIFT_SCORECARD_MARKDOWN_PATH,
    longitudinal_json_path: Path | str = OWNER_DRIFT_LONGITUDINAL_JSON_PATH,
    longitudinal_markdown_path: Path | str = OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH,
    side_effect_artifact_root: Path | str | None = None,
    command_used: str | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    """Write report-only rerun drift JSON and markdown artifacts."""
    payload = dict(scorecard) if isinstance(scorecard, Mapping) else _no_rerun_scorecard()
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_rerun_drift_scorecard_markdown(
            payload,
            generated_at=generated_at,
            command_used=command_used,
        ),
        encoding="utf-8",
    )
    history_scorecards = scorecards_for_longitudinal_aggregation(payload)
    append_owner_drift_longitudinal_markdown(
        markdown_out,
        history_scorecards,
        command_used=command_used,
        generated_at=generated_at,
    )
    write_owner_drift_longitudinal_artifacts(
        history_scorecards,
        json_path=longitudinal_json_path,
        markdown_path=longitudinal_markdown_path,
        command_used=command_used,
        generated_at=generated_at,
    )
    side_effect_root = Path(side_effect_artifact_root) if side_effect_artifact_root is not None else None
    write_owner_drift_hotspot_artifacts(
        collected_hotspot_classifications(),
        json_path=(
            side_effect_root / OWNER_DRIFT_HOTSPOTS_JSON_PATH.name
            if side_effect_root is not None
            else OWNER_DRIFT_HOTSPOTS_JSON_PATH
        ),
        markdown_path=(
            side_effect_root / OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH.name
            if side_effect_root is not None
            else OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH
        ),
        scorecard_history=history_scorecards,
        command_used=command_used,
        generated_at=generated_at,
    )
    write_owner_drift_trend_artifacts(
        history_scorecards,
        json_path=(
            side_effect_root / OWNER_DRIFT_TRENDS_JSON_PATH.name
            if side_effect_root is not None
            else OWNER_DRIFT_TRENDS_JSON_PATH
        ),
        markdown_path=(
            side_effect_root / OWNER_DRIFT_TRENDS_MARKDOWN_PATH.name
            if side_effect_root is not None
            else OWNER_DRIFT_TRENDS_MARKDOWN_PATH
        ),
        command_used=command_used,
        generated_at=generated_at,
    )
    write_owner_drift_risk_artifacts(
        collected_hotspot_classifications(),
        json_path=(
            side_effect_root / OWNER_DRIFT_RISK_JSON_PATH.name
            if side_effect_root is not None
            else OWNER_DRIFT_RISK_JSON_PATH
        ),
        markdown_path=(
            side_effect_root / OWNER_DRIFT_RISK_MARKDOWN_PATH.name
            if side_effect_root is not None
            else OWNER_DRIFT_RISK_MARKDOWN_PATH
        ),
        recurrence_json_path=(
            side_effect_root / BUG_RECURRENCE_HISTORY_JSON_PATH.name
            if side_effect_root is not None
            else None
        ),
        recurrence_markdown_path=(
            side_effect_root / BUG_RECURRENCE_HISTORY_MARKDOWN_PATH.name
            if side_effect_root is not None
            else None
        ),
        recurrence_session_event_log_path=(
            side_effect_root / BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH.name
            if side_effect_root is not None
            else None
        ),
        recurrence_synthetic_test_artifact_event_log_path=(
            side_effect_root / BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH.name
            if side_effect_root is not None
            else None
        ),
        scorecard_history=history_scorecards,
        command_used=command_used,
        generated_at=generated_at,
    )
    return json_out, markdown_out


def write_rerun_drift_scorecard_artifacts_if_requested(
    scorecard: Mapping[str, Any] | None = None,
    *,
    json_path: Path | str = RERUN_DRIFT_SCORECARD_JSON_PATH,
    markdown_path: Path | str = RERUN_DRIFT_SCORECARD_MARKDOWN_PATH,
    command_used: str | None = None,
    env: Mapping[str, str] | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path] | None:
    """Write successful rerun drift artifacts only under the explicit opt-in flag."""
    if not rerun_drift_scorecard_requested(env):
        return None
    return write_rerun_drift_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        command_used=command_used,
        generated_at=generated_at,
    )
