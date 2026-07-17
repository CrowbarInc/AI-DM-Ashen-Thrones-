"""Stability scorecard rendering and artifact orchestration for replay diagnostics.

Consumes stability analytics from replay_drift_reports.py, paths from
failure_dashboard_paths.py, and session buffers from failure_dashboard_session.py.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_drift import _owner_drift_summary_table_lines
from tests.helpers.failure_dashboard_paths import (
    LONG_SESSION_STABILITY_SCORECARD_ENV_VAR,
    LONG_SESSION_STABILITY_SCORECARD_JSON_PATH,
    LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH,
)
from tests.helpers.failure_dashboard_session import recorded_long_session_stability_scorecards
from tests.helpers.replay_drift_reports import (
    build_long_session_stability_history,
    build_stability_hotspots,
    render_stability_hotspots_markdown_lines,
    render_stability_trends_markdown_lines,
    stability_classification_rows_from_scorecard,
)


def _cell(value: Any) -> str:
    if value is None or value == "":
        text = "none"
    elif isinstance(value, (list, tuple, set, frozenset)):
        text = ", ".join(str(item) for item in value if str(item).strip()) or "none"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _stability_ownership_markdown_lines(
    *,
    scorecard: Mapping[str, Any] | None = None,
    classification_rows: Sequence[Mapping[str, Any]] | None = None,
    owner_bucket_counts: Mapping[str, int] | None = None,
    stability_status: str | None = None,
) -> list[str]:
    """Render stability ownership rows for long-session and risk markdown surfaces."""
    lines = ["## Stability Ownership", ""]

    resolved_status = stability_status
    if resolved_status is None and isinstance(scorecard, Mapping):
        operational = (
            scorecard.get("operational_summary")
            if isinstance(scorecard.get("operational_summary"), Mapping)
            else {}
        )
        resolved_status = str(operational.get("stability_status") or "unknown")
    if resolved_status is not None:
        lines.append(f"- Stability status: `{resolved_status}`")
        lines.append("")

    resolved_counts = owner_bucket_counts
    if resolved_counts is None and isinstance(scorecard, Mapping):
        raw_counts = scorecard.get("owner_drift_bucket_counts")
        resolved_counts = dict(raw_counts) if isinstance(raw_counts, Mapping) else None
    if isinstance(resolved_counts, Mapping):
        lines.extend(_owner_drift_summary_table_lines(dict(resolved_counts)))

    rows = list(classification_rows or [])
    if not rows and isinstance(scorecard, Mapping):
        rows = stability_classification_rows_from_scorecard(scorecard)

    if not rows:
        lines.extend(["No stability ownership classifications.", ""])
        return lines

    lines.extend(
        [
            "| Scenario | Signal | Owner Drift Bucket | Stability Status | Severity | Reason |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("scenario_id")),
                    _cell(row.get("signal")),
                    _cell(row.get("owner_drift_bucket")),
                    _cell(row.get("stability_status")),
                    _cell(row.get("severity_hint")),
                    _cell(row.get("reason")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def long_session_stability_scorecard_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return whether successful long-session stability scorecards should be written."""
    env_map = env if env is not None else os.environ
    return str(env_map.get(LONG_SESSION_STABILITY_SCORECARD_ENV_VAR) or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def render_long_session_stability_scorecard_markdown(
    scorecard: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
    stability_scorecard_history: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    """Render an operator-readable report-only long-session stability scorecard."""
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command_s = command_used if command_used is not None else " ".join(sys.argv)
    lines = [
        "# Long-Session Stability Scorecard",
        "",
        f"- Generated at: `{generated_at_s}`",
        f"- Command: `{command_s or 'unavailable'}`",
        "- Report only: `true`",
        "- Advisory only: `true`",
        "",
    ]
    if not isinstance(scorecard, Mapping):
        lines.extend(["No long-session stability scorecard available.", ""])
        return "\n".join(lines)

    route = scorecard.get("route_stability") if isinstance(scorecard.get("route_stability"), Mapping) else {}
    speaker = scorecard.get("speaker_stability") if isinstance(scorecard.get("speaker_stability"), Mapping) else {}
    fallback = scorecard.get("fallback_stability") if isinstance(scorecard.get("fallback_stability"), Mapping) else {}
    lineage = scorecard.get("lineage_stability") if isinstance(scorecard.get("lineage_stability"), Mapping) else {}
    degradation = scorecard.get("degradation") if isinstance(scorecard.get("degradation"), Mapping) else {}
    operational = scorecard.get("operational_summary") if isinstance(scorecard.get("operational_summary"), Mapping) else {}

    lines.extend(
        [
            "## Session",
            "",
            f"- Scenario: `{scorecard.get('scenario_id')}`",
            f"- Branch: `{scorecard.get('branch_id')}`",
            f"- Source path: `{scorecard.get('source_path')}`",
            f"- Turns: `{scorecard.get('turn_count')}`",
            "",
            "## Operational Summary",
            "",
            f"- Stability status: `{operational.get('stability_status', 'unknown')}`",
            f"- Actionable: `{operational.get('actionable', False)}`",
            f"- Warning count: `{operational.get('warning_count', 0)}`",
            "",
            "## Route Stability",
            "",
            f"- Route changes: `{route.get('route_change_count', 0)}`",
            f"- Route frequency: `{route.get('route_frequency', {})}`",
            "",
            "## Speaker Stability",
            "",
            f"- Speaker changes: `{speaker.get('speaker_change_count', 0)}`",
            f"- Speaker missing: `{speaker.get('speaker_missing_count', 0)}`",
            f"- Speaker frequency: `{speaker.get('speaker_frequency', {})}`",
            "",
            "## Fallback Stability",
            "",
            f"- Fallback count: `{fallback.get('fallback_count', 0)}`",
            f"- Fallback family frequency: `{fallback.get('fallback_family_frequency', {})}`",
            f"- Max fallback streak: `{fallback.get('max_fallback_streak', 0)}`",
            f"- Late-window fallback count: `{fallback.get('late_window_fallback_count', 0)}`",
            f"- Escalation warnings: `{fallback.get('escalation_warnings', [])}`",
            "",
            "## Lineage Stability",
            "",
            f"- Event counts: `{lineage.get('event_counts', {})}`",
            f"- Recurring events: `{lineage.get('recurring_events', [])}`",
            "",
            "## Degradation",
            "",
            f"- Progressive degradation detected: `{degradation.get('progressive_degradation_detected', False)}`",
            f"- Reason codes: `{degradation.get('reason_codes', [])}`",
            f"- Health / classification: `{degradation.get('health')}`",
            f"- Long-session band: `{degradation.get('long_session_band')}`",
            f"- Overall passed: `{degradation.get('overall_passed')}`",
            "",
        ]
    )
    lines.extend(
        _stability_ownership_markdown_lines(
            scorecard=scorecard,
            owner_bucket_counts=(
                dict(scorecard.get("owner_drift_bucket_counts"))
                if isinstance(scorecard.get("owner_drift_bucket_counts"), Mapping)
                else None
            ),
        )
    )
    history_source = (
        list(stability_scorecard_history)
        if stability_scorecard_history is not None
        else recorded_long_session_stability_scorecards()
    )
    history = build_long_session_stability_history(history_source)
    lines.extend(render_stability_trends_markdown_lines(history=history))
    hotspots = build_stability_hotspots(history_source)
    lines.extend(render_stability_hotspots_markdown_lines(hotspots.get("hotspot_rows")))
    return "\n".join(lines)


def write_long_session_stability_scorecard_artifacts(
    scorecard: Mapping[str, Any] | None = None,
    *,
    json_path: Path | str = LONG_SESSION_STABILITY_SCORECARD_JSON_PATH,
    markdown_path: Path | str = LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH,
    command_used: str | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    """Write report-only long-session stability JSON and markdown artifacts."""
    payload = dict(scorecard) if isinstance(scorecard, Mapping) else {}
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_long_session_stability_scorecard_markdown(
            payload,
            generated_at=generated_at,
            command_used=command_used,
            stability_scorecard_history=recorded_long_session_stability_scorecards(),
        ),
        encoding="utf-8",
    )
    return json_out, markdown_out


def write_long_session_stability_scorecard_artifacts_if_requested(
    scorecard: Mapping[str, Any] | None = None,
    *,
    json_path: Path | str = LONG_SESSION_STABILITY_SCORECARD_JSON_PATH,
    markdown_path: Path | str = LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH,
    command_used: str | None = None,
    env: Mapping[str, str] | None = None,
    generated_at: str | None = None,
) -> tuple[Path, Path] | None:
    """Write long-session stability artifacts only under the explicit opt-in flag."""
    if not long_session_stability_scorecard_requested(env):
        return None
    return write_long_session_stability_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        command_used=command_used,
        generated_at=generated_at,
    )
