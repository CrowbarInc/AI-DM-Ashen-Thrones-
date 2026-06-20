"""Markdown report builder for replay failure classifications."""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from game.runtime_lineage_telemetry import normalize_runtime_lineage_events
from tests.helpers.failure_classifier import (
    FailureClassification,
    classify_replay_failure,
)
from tests.helpers.failure_classification_sync import (
    failure_dashboard_evidence_labels,
    failure_dashboard_evidence_manifest,
    failure_dashboard_evidence_row_keys,
    failure_dashboard_row_shape_errors,
    known_failure_categories,
)
from tests.helpers.golden_replay_projection import protected_observation_field_paths
from tests.helpers.runtime_lineage_reporting import (
    build_runtime_lineage_summary,
    runtime_lineage_markdown_lines as _runtime_lineage_markdown_lines,
)
from tests.helpers.replay_bug_recurrence import (
    PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    aggregate_protected_recurrence_history_from_event_log,
    append_recurrence_events_to_persistence_lanes,
    apply_recurrence_trajectory_to_analytics,
    build_recurrence_forecast,
    build_recurrence_portfolio,
    build_recurrence_remediation_targets,
    build_recurrence_roi_analysis,
    build_recurrence_governance,
    build_recurrence_lifecycle,
    build_recurrence_program_effectiveness,
    build_recurrence_maturity_assessment,
    build_recurrence_strategic_roadmap,
    build_recurrence_completion_assessment,
    build_recurrence_graduation_audit,
    build_recurrence_confidence_audit,
    build_recurrence_final_graduation_decision,
    render_recurrence_graduation_audit_report_markdown,
    render_recurrence_confidence_calibration_report_markdown,
    render_recurrence_final_graduation_decision_report_markdown,
    RECURRENCE_GRADUATION_AUDIT_DOC_PATH,
    RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH,
    RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH,
    RECURRENCE_TRAJECTORY_BASELINE_MESSAGE,
    build_recurrence_timeline,
    build_recurrence_trend_summary,
    calculate_regression_recurrence_rate,
    build_recurrence_outcome_validation,
    render_recurrence_outcome_validation_report_markdown,
    RECURRENCE_OUTCOME_VALIDATION_DOC_PATH,
    load_recurrence_event_log,
    normalize_recurrence_event_metadata,
    write_recurrence_event_log,
)
from tests.helpers.replay_drift_reports import (
    aggregate_owner_drift_history,
    aggregate_recurrence_history,
    build_hotspot_rankings,
    build_long_session_stability_history,
    build_owner_drift_trend_summary,
    build_recurrence_summary,
    build_risk_payload,
    build_stability_hotspots,
    build_trend_payload,
    classification_rows_for_analysis,
    classification_rows_from_scorecards,
    enrich_hotspots_with_field_trends,
    render_owner_drift_hotspot_report,
    render_owner_drift_longitudinal_report,
    render_owner_drift_risk_report,
    render_owner_drift_trend_report,
    render_stability_hotspots_markdown_lines,
    render_stability_trends_markdown_lines,
    stability_classification_rows_from_scorecard,
    summarize_owner_drift_buckets,
)

# Cycle T3: dashboard reporting consumes projection/sync surfaces instead of
# re-enumerating protected replay field paths or failure categories inline.
REPLAY_PROTECTED_FIELD_PATHS = protected_observation_field_paths()
KNOWN_FAILURE_CATEGORIES = known_failure_categories()
FAILURE_DASHBOARD_EVIDENCE_MANIFEST = failure_dashboard_evidence_manifest()
FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS = failure_dashboard_evidence_row_keys()
FAILURE_DASHBOARD_EVIDENCE_LABELS = failure_dashboard_evidence_labels()

FAILURE_DASHBOARD_TABLE_COLUMNS: tuple[str, ...] = (
    "Scenario",
    "Turn",
    "Category",
    "Severity",
    "Primary Owner",
    "Secondary Owner",
    "Investigate First",
    "Evidence",
    "Replay Tags",
    "Field",
    "Expected",
    "Actual",
    "Unavailable",
    "Final Source",
    "Fallback",
    "Post-Gate Mutation",
    "Mutation Flags",
    "Owner Drift Bucket",
)

# Cycle AO3 — dashboard consumes contract-owned evidence manifest; formatting stays here.

def _format_dashboard_evidence_value(row_key: str, value: Any) -> Any:
    if row_key == "final_emission_mutation_lineage" and isinstance(value, list):
        joined = ">".join(str(item) for item in value if str(item).strip())
        return joined or None
    if row_key == "sanitizer_lineage_legacy_rewrite_active" and value is True:
        return "legacy_diagnostic"
    return value


def _prepared_emission_evidence_parts(row: Mapping[str, Any]) -> list[str]:
    if row.get("prepared_emission_owner") != "upstream_prepared_emission":
        return []
    if row.get("upstream_prepared_emission_valid") is False:
        reason = row.get("upstream_prepared_emission_reject_reason") or "unknown"
        return [f"prepared_emission=rejected reason={reason}"]
    valid = row.get("upstream_prepared_emission_valid")
    source = row.get("upstream_prepared_emission_source") or "unknown"
    return [f"prepared_emission=used valid={valid} source={source}"]


def expected_failure_dashboard_columns() -> tuple[str, ...]:
    """Return markdown table column headers for the main failure dashboard table."""
    return FAILURE_DASHBOARD_TABLE_COLUMNS


def _failure_dashboard_table_header() -> str:
    return "| " + " | ".join(FAILURE_DASHBOARD_TABLE_COLUMNS) + " |"


def _failure_dashboard_table_separator() -> str:
    parts = ["---"] + ["---:" if index == 1 else "---" for index in range(1, len(FAILURE_DASHBOARD_TABLE_COLUMNS))]
    return "|" + "|".join(parts) + "|"


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


FAILURE_DASHBOARD_ENV_VAR = "ASHEN_WRITE_FAILURE_DASHBOARD"
RERUN_DRIFT_SCORECARD_ENV_VAR = "ASHEN_WRITE_RERUN_DRIFT_SCORECARD"
LONG_SESSION_STABILITY_SCORECARD_ENV_VAR = "ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD"
FAILURE_DASHBOARD_LATEST_PATH = Path("audits/failure_dashboard_latest.md")
PROTECTED_REPLAY_FAILURE_REPORT_PATH = Path("artifacts/golden_replay/replay_failure_report.md")
RERUN_DRIFT_SCORECARD_JSON_PATH = Path("artifacts/golden_replay/rerun_drift_scorecard.json")
RERUN_DRIFT_SCORECARD_MARKDOWN_PATH = Path("artifacts/golden_replay/rerun_drift_scorecard.md")
LONG_SESSION_STABILITY_SCORECARD_JSON_PATH = Path(
    "artifacts/golden_replay/long_session_stability_scorecard.json"
)
LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH = Path(
    "artifacts/golden_replay/long_session_stability_scorecard.md"
)
OWNER_DRIFT_LONGITUDINAL_JSON_PATH = Path("artifacts/golden_replay/owner_drift_longitudinal.json")
OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_longitudinal.md")
OWNER_DRIFT_HOTSPOTS_JSON_PATH = Path("artifacts/golden_replay/owner_drift_hotspots.json")
OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_hotspots.md")
OWNER_DRIFT_TRENDS_JSON_PATH = Path("artifacts/golden_replay/owner_drift_trends.json")
OWNER_DRIFT_TRENDS_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_trends.md")
OWNER_DRIFT_RISK_JSON_PATH = Path("artifacts/golden_replay/owner_drift_risk.json")
OWNER_DRIFT_RISK_MARKDOWN_PATH = Path("artifacts/golden_replay/owner_drift_risk.md")
BUG_RECURRENCE_HISTORY_JSON_PATH = Path("artifacts/golden_replay/bug_recurrence_history.json")
BUG_RECURRENCE_HISTORY_MARKDOWN_PATH = Path("artifacts/golden_replay/bug_recurrence_history.md")
BUG_RECURRENCE_EVENT_LOG_JSON_PATH = Path("artifacts/golden_replay/bug_recurrence_event_log.json")
BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH = Path(
    "artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json"
)
RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH = Path(
    "artifacts/golden_replay/recurrence_trajectory_history.json"
)
_RECORDED_FAILURE_DASHBOARD_ROWS: list[Mapping[str, Any]] = []
_RECORDED_RUNTIME_LINEAGE_EVENTS: list[dict[str, Any]] = []
_RECORDED_PROTECTED_REPLAY_FAILURE_ROWS: list[Mapping[str, Any]] = []
_RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS: list[dict[str, Any]] = []
_RECORDED_RERUN_DRIFT_SCORECARDS: list[Mapping[str, Any]] = []
_RECORDED_LONG_SESSION_STABILITY_SCORECARDS: list[Mapping[str, Any]] = []


# Data shaping helpers -----------------------------------------------------

def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set, frozenset)):
        return list(value)
    return [value]


def _flatten_drift_rows(drift: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    if drift is None:
        return []
    if isinstance(drift, Mapping):
        rows: list[Mapping[str, Any]] = []
        for bucket in ("exact_drift", "structural_drift", "semantic_drift"):
            for row in _as_list(drift.get(bucket)):
                if isinstance(row, Mapping):
                    enriched = dict(row)
                    enriched.setdefault("drift_bucket", bucket)
                    enriched.setdefault("replay_tags", [bucket])
                    if drift.get("observed_text_hash") and "observed_text_hash" not in enriched:
                        enriched["observed_text_hash"] = drift.get("observed_text_hash")
                    rows.append(enriched)
        return rows
    return [row for row in drift if isinstance(row, Mapping)]


def build_failure_dashboard_rows(
    *,
    replay_results: Sequence[Mapping[str, Any]] | None = None,
    observed_turn: Mapping[str, Any] | None = None,
    drift_rows: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    scenario_id: str | None = None,
    turn_index: int | None = None,
) -> list[FailureClassification]:
    """Build one dashboard row per classified replay failure.

    The function accepts either full replay/report rows or one explicit
    observed turn plus drift rows.  No runtime state is read.
    """
    rows: list[FailureClassification] = []
    if observed_turn is not None:
        rows.extend(
            classify_replay_failure(
                scenario_id=str(scenario_id or observed_turn.get("scenario_id") or ""),
                turn_index=int(turn_index if turn_index is not None else observed_turn.get("turn_index") or 0),
                observed_turn=observed_turn,
                drift_rows=_flatten_drift_rows(drift_rows),
            )
        )

    for result in replay_results or ():
        if not isinstance(result, Mapping):
            continue
        turns = result.get("turns") if isinstance(result.get("turns"), list) else []
        by_index = {turn.get("turn_index"): turn for turn in turns if isinstance(turn, Mapping)}
        result_drift = result.get("drift")
        if isinstance(result_drift, Mapping):
            classifications = result_drift.get("failure_classifications")
            if isinstance(classifications, list):
                rows.extend(row for row in classifications if isinstance(row, Mapping))
                continue
            turn = by_index.get(result_drift.get("turn_index")) or (turns[0] if turns else {})
            if isinstance(turn, Mapping):
                rows.extend(
                    classify_replay_failure(
                        scenario_id=str(result.get("scenario_id") or turn.get("scenario_id") or ""),
                        turn_index=int(turn.get("turn_index") or 0),
                        observed_turn=turn,
                        drift_rows=_flatten_drift_rows(result_drift),
                    )
                )
        for turn in turns:
            if not isinstance(turn, Mapping):
                continue
            turn_drift = turn.get("drift")
            if turn_drift:
                rows.extend(
                    classify_replay_failure(
                        scenario_id=str(result.get("scenario_id") or turn.get("scenario_id") or ""),
                        turn_index=int(turn.get("turn_index") or 0),
                        observed_turn=turn,
                        drift_rows=_flatten_drift_rows(turn_drift),
                    )
                )
    return rows


def build_classified_dashboard_row(
    *,
    observed_turn: Mapping[str, Any],
    drift_row: Mapping[str, Any],
    scenario_id: str,
    turn_index: int = 0,
) -> FailureClassification:
    """Build one classified dashboard row from an observed turn and drift row."""
    rows = build_failure_dashboard_rows(
        observed_turn=observed_turn,
        drift_rows=[drift_row],
        scenario_id=scenario_id,
        turn_index=turn_index,
    )
    if not rows:
        raise ValueError("build_classified_dashboard_row expected at least one classified row")
    return rows[0]


def _cell(value: Any) -> str:
    if value is None or value == "":
        text = "none"
    elif isinstance(value, (list, tuple, set, frozenset)):
        text = ", ".join(str(item) for item in value if str(item).strip()) or "none"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _drift_type(row: Mapping[str, Any]) -> str:
    for tag in _as_list(row.get("replay_tags")):
        if tag in {"exact_drift", "structural_drift", "semantic_drift"}:
            return str(tag)
    return "unclassified"


def _evidence_cell(row: Mapping[str, Any]) -> str:
    parts = _prepared_emission_evidence_parts(row)
    for label, row_key in FAILURE_DASHBOARD_EVIDENCE_MANIFEST:
        value = _format_dashboard_evidence_value(row_key, row.get(row_key))
        if value is None or value == "":
            continue
        parts.append(f"{label}={value}")
    return "; ".join(parts) or "none"


# Artifact request helpers -------------------------------------------------

def failure_dashboard_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return whether replay classification rows should be recorded/written."""
    env_map = env if env is not None else os.environ
    return str(env_map.get(FAILURE_DASHBOARD_ENV_VAR) or "").strip().lower() in {"1", "true", "yes", "on"}


def rerun_drift_scorecard_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return whether successful rerun drift diagnostics should be written."""
    env_map = env if env is not None else os.environ
    return str(env_map.get(RERUN_DRIFT_SCORECARD_ENV_VAR) or "").strip().lower() in {"1", "true", "yes", "on"}


def long_session_stability_scorecard_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return whether successful long-session stability scorecards should be written."""
    env_map = env if env is not None else os.environ
    return str(env_map.get(LONG_SESSION_STABILITY_SCORECARD_ENV_VAR) or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# Artifact recording helpers ----------------------------------------------

def record_failure_dashboard_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Record rows for the pytest session-level dashboard artifact."""
    _RECORDED_FAILURE_DASHBOARD_ROWS.extend(dict(row) for row in rows if isinstance(row, Mapping))


def record_runtime_lineage_events(events: Any) -> None:
    """Record separate replay lineage diagnostics without changing classification rows."""
    _RECORDED_RUNTIME_LINEAGE_EVENTS.extend(normalize_runtime_lineage_events(events)[:16])


def record_protected_replay_assertion_failure(
    *,
    scenario_id: str,
    test_node_id: str,
    observed_turn: Mapping[str, Any],
    field_path: str,
    expected: Any,
    actual: Any,
    reason: str,
    drift_bucket: str,
) -> list[FailureClassification]:
    """Translate one protected assertion failure into existing classification rows."""
    rows = build_failure_dashboard_rows(
        observed_turn=observed_turn,
        drift_rows=[
            {
                "field_path": field_path,
                "expected": expected,
                "actual": actual,
                "reason": reason,
                "drift_bucket": drift_bucket,
                "replay_tags": [drift_bucket],
            }
        ],
        scenario_id=scenario_id,
        turn_index=int(observed_turn.get("turn_index") or 0),
    )
    for row in rows:
        enriched = dict(row)
        for key in ("source_path", "branch_id", "turn_id"):
            value = observed_turn.get(key)
            if value is not None and str(value).strip():
                enriched[key] = str(value)
        enriched["test_node_id"] = test_node_id
        enriched["failed_invariant"] = f"{field_path}: {reason}"
        _RECORDED_PROTECTED_REPLAY_FAILURE_ROWS.append(enriched)
    _RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS.extend(
        normalize_runtime_lineage_events(observed_turn.get("runtime_lineage_events"))[:16]
    )
    return rows


def clear_recorded_failure_dashboard_rows() -> None:
    _RECORDED_FAILURE_DASHBOARD_ROWS.clear()
    _RECORDED_RUNTIME_LINEAGE_EVENTS.clear()


def recorded_failure_dashboard_rows() -> list[Mapping[str, Any]]:
    return list(_RECORDED_FAILURE_DASHBOARD_ROWS)


def recorded_runtime_lineage_events() -> list[dict[str, Any]]:
    return list(_RECORDED_RUNTIME_LINEAGE_EVENTS)


def clear_recorded_protected_replay_failures() -> None:
    _RECORDED_PROTECTED_REPLAY_FAILURE_ROWS.clear()
    _RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS.clear()


def recorded_protected_replay_failure_rows() -> list[Mapping[str, Any]]:
    return list(_RECORDED_PROTECTED_REPLAY_FAILURE_ROWS)


def recorded_protected_replay_runtime_lineage_events() -> list[dict[str, Any]]:
    return list(_RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS)


def clear_recorded_rerun_drift_scorecards() -> None:
    _RECORDED_RERUN_DRIFT_SCORECARDS.clear()


def record_rerun_drift_scorecard(scorecard: Mapping[str, Any] | None) -> None:
    """Record one successful-run rerun drift scorecard for optional artifacts."""
    if isinstance(scorecard, Mapping):
        _RECORDED_RERUN_DRIFT_SCORECARDS.append(dict(scorecard))


def recorded_rerun_drift_scorecards() -> list[Mapping[str, Any]]:
    return list(_RECORDED_RERUN_DRIFT_SCORECARDS)


def clear_recorded_long_session_stability_scorecards() -> None:
    _RECORDED_LONG_SESSION_STABILITY_SCORECARDS.clear()


def record_long_session_stability_scorecard(scorecard: Mapping[str, Any] | None) -> None:
    """Record one long-session stability scorecard for optional artifacts."""
    if isinstance(scorecard, Mapping):
        _RECORDED_LONG_SESSION_STABILITY_SCORECARDS.append(dict(scorecard))


def recorded_long_session_stability_scorecards() -> list[Mapping[str, Any]]:
    return list(_RECORDED_LONG_SESSION_STABILITY_SCORECARDS)


def clear_requested_artifact_recordings(env: Mapping[str, str] | None = None) -> None:
    """Clear recorder state for artifact writers requested in this pytest session."""
    if failure_dashboard_requested(env):
        clear_recorded_failure_dashboard_rows()
    if rerun_drift_scorecard_requested(env):
        clear_recorded_rerun_drift_scorecards()
    if long_session_stability_scorecard_requested(env):
        clear_recorded_long_session_stability_scorecards()


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


def _regression_recurrence_rate_markdown_lines(metric: Mapping[str, Any]) -> list[str]:
    numerator = int(metric.get("numerator") or 0)
    denominator = int(metric.get("denominator") or 0)
    rate = float(metric.get("rate") or 0.0)
    pct_text = f"{rate * 100.0:.1f}%" if denominator else "0.0%"
    return [
        "## Regression Recurrence Rate",
        "",
        (
            f"Regression Recurrence Rate: {pct_text} ({numerator} / {denominator} "
            "recurrence keys active by repeated observation). "
            "This is advisory/report-only and does not gate protected replay."
        ),
        "",
        f"- Definition: {metric.get('definition')}",
        f"- Interpretation: {metric.get('interpretation')}",
        f"- Report only: `{str(bool(metric.get('report_only', True))).lower()}`",
        f"- Advisory only: `{str(bool(metric.get('advisory_only', True))).lower()}`",
        "",
    ]


def _recurrence_trends_markdown_lines(
    trends: Mapping[str, Any] | None,
    *,
    timeline: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    """Render protected replay recurrence trend section for history markdown."""
    payload = trends if isinstance(trends, Mapping) else {}
    total_keys = int(payload.get("total_keys") or 0)
    growth_rate = float(payload.get("growth_rate") or 0.0)
    regression = payload.get("regression_recurrence_rate")
    if not isinstance(regression, Mapping):
        regression = {}
    regression_numerator = int(regression.get("numerator") or 0)
    regression_denominator = int(regression.get("denominator") or 0)
    regression_rate = float(regression.get("rate") or 0.0)
    regression_pct = (
        f"{regression_rate * 100.0:.1f}%"
        if regression_denominator
        else "0.0%"
    )
    lines = [
        "## Recurrence Trends",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Total protected recurrence keys: `{total_keys}`",
        f"- Emerging keys: `{int(payload.get('emerging_keys') or 0)}`",
        f"- Recurring keys: `{int(payload.get('recurring_keys') or 0)}`",
        f"- Persistent keys: `{int(payload.get('persistent_keys') or 0)}`",
        f"- Dormant keys: `{int(payload.get('dormant_keys') or 0)}`",
        (
            f"- Growth rate: `{growth_rate * 100.0:.1f}%` "
            f"({int(payload.get('emerging_keys') or 0)} / {total_keys or 0} keys emerging)"
        ),
        (
            f"- Regression recurrence rate: `{regression_pct}` "
            f"({regression_numerator} / {regression_denominator})"
        ),
        "",
    ]
    top_recurring = payload.get("top_recurring_keys")
    if isinstance(top_recurring, list) and top_recurring:
        lines.extend(["### Top Recurring Keys", ""])
        for row in top_recurring[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(count `{_cell(row.get('occurrence_count'))}`, "
                + f"class `{_cell(row.get('trend_classification'))}`)"
            )
        lines.append("")
    else:
        lines.extend(["### Top Recurring Keys", "", "No recurring protected keys yet.", ""])

    newest = payload.get("newest_recurrence_keys")
    if isinstance(newest, list) and newest:
        lines.extend(["### Newest Recurrence Keys", ""])
        for row in newest[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(first seen `{_cell(row.get('first_seen'))}`, "
                + f"class `{_cell(row.get('trend_classification'))}`)"
            )
        lines.append("")
    elif isinstance(timeline, Sequence) and timeline:
        lines.extend(["### Newest Recurrence Keys", ""])
        for row in list(timeline)[-5:][::-1]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(first seen `{_cell(row.get('first_seen'))}`, "
                + f"class `{_cell(row.get('trend_classification'))}`)"
            )
        lines.append("")
    else:
        lines.extend(["### Newest Recurrence Keys", "", "No protected recurrence keys recorded.", ""])
    return lines


def _recurrence_forecast_markdown_lines(forecast: Mapping[str, Any] | None) -> list[str]:
    """Render protected replay recurrence forecast section for history markdown."""
    payload = forecast if isinstance(forecast, Mapping) else {}
    summary = payload.get("forecast_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    risk = payload.get("risk_concentration")
    if not isinstance(risk, Mapping):
        risk = {}
    confidence = float(summary.get("forecast_confidence") or 0.0)
    confidence_label = "low" if confidence < 0.5 else "moderate" if confidence < 0.8 else "high"
    lines = [
        "## Recurrence Forecast",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Forecast confidence: `{confidence_label}` (`{confidence:.2f}`)",
        f"- Stable keys: `{int(summary.get('stable_keys') or 0)}`",
        f"- Watch keys: `{int(summary.get('watch_keys') or 0)}`",
        f"- Elevated keys: `{int(summary.get('elevated_keys') or 0)}`",
        f"- Concentrated keys: `{int(summary.get('concentrated_keys') or 0)}`",
        f"- Forecast risk score: `{float(summary.get('forecast_risk_score') or 0.0):.1f}` / 100",
        f"- Stability score: `{float(summary.get('stability_score') or 0.0):.1f}` / 100",
        "",
        "### Concentration Metrics",
        "",
        f"- Top key share: `{float(risk.get('top_key_share') or 0.0) * 100.0:.1f}%`",
        f"- Top three key share: `{float(risk.get('top_three_key_share') or 0.0) * 100.0:.1f}%`",
        f"- Concentration ratio (HHI): `{float(risk.get('concentration_ratio') or 0.0):.4f}`",
        f"- Dominant recurrence key: `{_cell(risk.get('dominant_recurrence_key'))}`",
        "",
    ]
    key_forecasts = payload.get("key_forecasts")
    if isinstance(key_forecasts, list) and key_forecasts:
        lines.extend(["### Key Forecasts", ""])
        for row in key_forecasts[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(forecast `{_cell(row.get('forecast_classification'))}`, "
                + f"trend `{_cell(row.get('trend_classification'))}`, "
                + f"share `{float(row.get('observation_share') or 0.0) * 100.0:.1f}%`)"
            )
        lines.append("")
    else:
        lines.extend(["### Key Forecasts", "", "No protected recurrence keys to forecast.", ""])
    return lines


def _portfolio_bucket_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
    extra_fields: Sequence[tuple[str, str]] = (),
) -> list[str]:
    """Render ranked portfolio bucket lines for one dimension."""
    lines = [heading, ""]
    if not rows:
        lines.extend(["No protected recurrence observations recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"`{_cell(row.get(label_field))}`",
            f"keys `{_cell(row.get('recurrence_keys'))}`",
            f"obs `{_cell(row.get('observations'))}`",
            f"share `{float(row.get('risk_share') or 0.0) * 100.0:.1f}%`",
        ]
        for extra_label, extra_field in extra_fields:
            parts.append(f"{extra_label} `{_cell(row.get(extra_field))}`")
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_portfolio_markdown_lines(
    portfolio: Mapping[str, Any] | None,
    *,
    portfolio_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence portfolio section for history markdown."""
    payload = portfolio if isinstance(portfolio, Mapping) else {}
    summary = portfolio_summary if isinstance(portfolio_summary, Mapping) else payload.get("portfolio_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    largest = summary.get("largest_risk_bucket")
    if not isinstance(largest, Mapping):
        largest = {}
    lines = [
        "## Recurrence Portfolio",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Portfolio risk score: `{float(summary.get('portfolio_risk_score') or 0.0):.1f}` / 100",
        (
            "- Largest risk bucket: "
            f"`{_cell(largest.get('dimension'))}` / `{_cell(largest.get('label'))}` "
            f"(HHI `{float(largest.get('concentration_ratio') or 0.0):.4f}`)"
        ),
        f"- Forecast confidence: `{float(summary.get('forecast_confidence') or 0.0):.2f}`",
        "",
        "### Portfolio Metrics",
        "",
        f"- Owner concentration ratio: `{float(summary.get('owner_concentration_ratio') or 0.0):.4f}`",
        f"- Category concentration ratio: `{float(summary.get('category_concentration_ratio') or 0.0):.4f}`",
        f"- Field path concentration ratio: `{float(summary.get('field_path_concentration_ratio') or 0.0):.4f}`",
        f"- Scenario concentration ratio: `{float(summary.get('scenario_concentration_ratio') or 0.0):.4f}`",
        "",
    ]
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Owners",
            payload.get("owners") if isinstance(payload.get("owners"), list) else None,
            label_field="owner",
            extra_fields=(("recurring", "recurring_keys"), ("elevated", "elevated_keys")),
        )
    )
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Categories",
            payload.get("categories") if isinstance(payload.get("categories"), list) else None,
            label_field="category",
        )
    )
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Field Paths",
            payload.get("field_paths") if isinstance(payload.get("field_paths"), list) else None,
            label_field="field_path",
        )
    )
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Scenarios",
            payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else None,
            label_field="scenario_id",
        )
    )
    return lines


def _remediation_bucket_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
    extra_fields: Sequence[tuple[str, str]] = (),
) -> list[str]:
    lines = [heading, ""]
    if not rows:
        lines.extend(["No remediation targets recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"`{_cell(row.get(label_field))}`",
            f"priority `{_cell(row.get('remediation_priority'))}`",
            f"reduction `{float(row.get('reduction_potential') or 0.0):.1f}`",
            f"share `{float(row.get('risk_share') or 0.0) * 100.0:.1f}%`",
        ]
        for extra_label, extra_field in extra_fields:
            parts.append(f"{extra_label} `{_cell(row.get(extra_field))}`")
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_remediation_markdown_lines(
    targets: Mapping[str, Any] | None,
    *,
    remediation_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence remediation section for history markdown."""
    payload = targets if isinstance(targets, Mapping) else {}
    summary = remediation_summary if isinstance(remediation_summary, Mapping) else payload.get("remediation_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    highest = summary.get("highest_leverage_target")
    if not isinstance(highest, Mapping):
        highest = {}
    lines = [
        "## Recurrence Remediation Targets",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        (
            "- Highest leverage target: "
            f"`{_cell(highest.get('dimension') or summary.get('highest_leverage_key'))}` / "
            f"`{_cell(highest.get('label') or summary.get('highest_leverage_key'))}` "
            f"(priority `{_cell(highest.get('remediation_priority'))}`)"
        ),
        f"- Estimated portfolio reduction: `{float(summary.get('estimated_portfolio_reduction') or 0.0):.1f}`",
        f"- Remediation confidence: `{float(summary.get('remediation_confidence') or 0.0):.2f}`",
        "",
    ]
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Keys",
            payload.get("keys") if isinstance(payload.get("keys"), list) else None,
            label_field="recurrence_key",
            extra_fields=(("trend", "trend_classification"), ("forecast", "forecast_classification")),
        )
    )
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Owners",
            payload.get("owners") if isinstance(payload.get("owners"), list) else None,
            label_field="owner",
            extra_fields=(("keys", "recurrence_keys"),),
        )
    )
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Field Paths",
            payload.get("field_paths") if isinstance(payload.get("field_paths"), list) else None,
            label_field="field_path",
        )
    )
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Scenarios",
            payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else None,
            label_field="scenario_id",
        )
    )
    return lines


def _roi_bucket_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
) -> list[str]:
    lines = [heading, ""]
    if not rows:
        lines.extend(["No ROI targets recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"rank `{int(row.get('roi_rank') or 0)}`",
            f"`{_cell(row.get(label_field))}`",
            f"ROI `{float(row.get('roi_score') or 0.0):.1f}`",
            f"cost `{_cell(row.get('cost_classification'))}`",
            f"benefit `{float(row.get('expected_benefit') or 0.0):.1f}`",
        ]
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_roi_markdown_lines(
    analysis: Mapping[str, Any] | None,
    *,
    roi_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence ROI section for history markdown."""
    payload = analysis if isinstance(analysis, Mapping) else {}
    summary = roi_summary if isinstance(roi_summary, Mapping) else payload.get("roi_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    highest = summary.get("highest_roi_target")
    if not isinstance(highest, Mapping):
        highest = {}
    lines = [
        "## Recurrence ROI",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        (
            "- Highest ROI target: "
            f"`{_cell(highest.get('dimension') or 'key')}` / "
            f"`{_cell(highest.get('label'))}` "
            f"(ROI `{float(highest.get('roi_score') or summary.get('portfolio_roi_score') or 0.0):.1f}`, "
            f"cost `{_cell(highest.get('cost_classification'))}`)"
        ),
        f"- Portfolio ROI score: `{float(summary.get('portfolio_roi_score') or 0.0):.1f}`",
        f"- Projected stability gain: `{float(summary.get('projected_stability_gain') or 0.0):.1f}`",
        f"- Projected risk reduction: `{float(summary.get('projected_risk_reduction') or 0.0):.1f}`",
        f"- ROI confidence: `{float(summary.get('roi_confidence') or 0.0):.2f}`",
        "",
    ]
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Targets",
            payload.get("keys") if isinstance(payload.get("keys"), list) else None,
            label_field="recurrence_key",
        )
    )
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Owners",
            payload.get("owners") if isinstance(payload.get("owners"), list) else None,
            label_field="owner",
        )
    )
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Field Paths",
            payload.get("field_paths") if isinstance(payload.get("field_paths"), list) else None,
            label_field="field_path",
        )
    )
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Scenarios",
            payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else None,
            label_field="scenario_id",
        )
    )
    return lines


def _governance_watchlist_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
) -> list[str]:
    lines = [heading, ""]
    if not rows:
        lines.extend(["No watchlist entries recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"`{_cell(row.get('recurrence_key'))}`",
            f"status `{_cell(row.get('governance_status'))}`",
            f"action `{_cell(row.get('recommended_action'))}`",
            f"ROI `{float(row.get('roi_score') or 0.0):.1f}`",
            f"trend `{_cell(row.get('trend_classification'))}`",
            f"forecast `{_cell(row.get('forecast_classification'))}`",
        ]
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_governance_markdown_lines(
    governance: Mapping[str, Any] | None,
    *,
    governance_summary: Mapping[str, Any] | None = None,
    watchlist: Sequence[Mapping[str, Any]] | None = None,
    retirement_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence governance section for history markdown."""
    payload = governance if isinstance(governance, Mapping) else {}
    summary = governance_summary if isinstance(governance_summary, Mapping) else payload.get("governance_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    entries = watchlist if watchlist is not None else payload.get("watchlist")
    if not isinstance(entries, list):
        entries = []
    retirement = retirement_summary if isinstance(retirement_summary, Mapping) else payload.get("retirement_summary")
    if not isinstance(retirement, Mapping):
        retirement = {}
    owners = payload.get("owners") if isinstance(payload.get("owners"), list) else []
    prioritized = [
        row for row in entries if isinstance(row, Mapping) and row.get("governance_status") == "prioritize"
    ]
    retire_candidates = [
        row
        for row in entries
        if isinstance(row, Mapping) and row.get("governance_status") == "retire_candidate"
    ]
    lines = [
        "## Recurrence Governance",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Governance health score: `{float(summary.get('governance_health_score') or 0.0):.1f}`",
        f"- Governance confidence: `{float(summary.get('governance_confidence') or 0.0):.2f}`",
        f"- Watchlist size: `{int(summary.get('watchlist_size') or 0)}`",
        f"- Prioritized targets: `{int(summary.get('prioritized_targets') or 0)}`",
        f"- Retirement opportunities: `{int(summary.get('retirement_opportunities') or retirement.get('retirement_opportunities') or 0)}`",
        "",
    ]
    lines.extend(_governance_watchlist_markdown_lines("### Watchlist", entries))
    lines.extend(_governance_watchlist_markdown_lines("### Prioritized Targets", prioritized))
    lines.extend(_governance_watchlist_markdown_lines("### Retire Candidates", retire_candidates))
    lines.extend(["### Owner Accountability", ""])
    if not owners:
        lines.extend(["No owner governance metrics recorded.", ""])
    else:
        for row in owners[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + ", ".join(
                    [
                        f"`{_cell(row.get('owner'))}`",
                        f"governed `{int(row.get('governed_keys') or 0)}`",
                        f"watch `{int(row.get('watch_keys') or 0)}`",
                        f"prioritized `{int(row.get('prioritized_keys') or 0)}`",
                        f"retire `{int(row.get('retire_candidates') or 0)}`",
                    ]
                )
            )
        load_owner = summary.get("highest_governance_load_owner") or payload.get("highest_governance_load_owner")
        if load_owner:
            lines.append(f"- Highest governance load owner: `{_cell(load_owner)}`")
        lines.append("")
    return lines


def _recurrence_lifecycle_markdown_lines(
    lifecycle: Mapping[str, Any] | None,
    *,
    lifecycle_summary: Mapping[str, Any] | None = None,
    age_distribution: Mapping[str, Any] | None = None,
    transition_summary: Mapping[str, Any] | None = None,
    closure_effectiveness: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence lifecycle section for history markdown."""
    payload = lifecycle if isinstance(lifecycle, Mapping) else {}
    summary = lifecycle_summary if isinstance(lifecycle_summary, Mapping) else payload.get("lifecycle_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    ages = age_distribution if isinstance(age_distribution, Mapping) else payload.get("age_distribution")
    if not isinstance(ages, Mapping):
        ages = {}
    transitions = transition_summary if isinstance(transition_summary, Mapping) else payload.get("transition_summary")
    if not isinstance(transitions, Mapping):
        transitions = {}
    closure = closure_effectiveness if isinstance(closure_effectiveness, Mapping) else payload.get("closure_effectiveness")
    if not isinstance(closure, Mapping):
        closure = {}
    distribution = payload.get("lifecycle_distribution")
    if not isinstance(distribution, Mapping):
        distribution = {}

    lines = [
        "## Recurrence Lifecycle",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Lifecycle health score: `{float(summary.get('lifecycle_health_score') or 0.0):.1f}`",
        f"- Closure rate: `{float(summary.get('closure_rate') or 0.0) * 100.0:.1f}%`",
        f"- Average age (days): `{float(summary.get('average_age_days') or 0.0):.1f}`",
        f"- Advancement rate: `{float(summary.get('advancement_rate') or 0.0):.2f}`",
        "",
        "### Lifecycle Distribution",
        "",
    ]
    if not distribution:
        lines.extend(["No lifecycle distribution recorded.", ""])
    else:
        for stage, count in sorted(distribution.items()):
            lines.append(f"- `{_cell(stage)}`: `{int(count or 0)}`")
        lines.append("")

    lines.extend(
        [
            "### Age Distribution",
            "",
            f"- Youngest key: `{_cell(ages.get('youngest_key'))}`",
            f"- Oldest key: `{_cell(ages.get('oldest_key'))}`",
            f"- Average age (days): `{float(ages.get('average_age_days') or 0.0):.1f}`",
            f"- Median age (days): `{float(ages.get('median_age_days') or 0.0):.1f}`",
            "",
            "### Transition Summary",
            "",
            f"- Transition count: `{int(transitions.get('transition_count') or 0)}`",
            f"- Advancing transitions: `{int(transitions.get('advancing_transitions') or 0)}`",
            f"- Retiring transitions: `{int(transitions.get('retiring_transitions') or 0)}`",
            f"- Stalled keys: `{int(transitions.get('stalled_key_count') or 0)}`",
            "",
            "### Closure Effectiveness",
            "",
            f"- Active keys: `{int(closure.get('active_keys') or 0)}`",
            f"- Dormant keys: `{int(closure.get('dormant_keys') or 0)}`",
            f"- Retired keys: `{int(closure.get('retired_keys') or 0)}`",
            f"- Closure rate: `{float(closure.get('closure_rate') or 0.0) * 100.0:.1f}%`",
            "",
        ]
    )
    return lines


def _recurrence_trajectory_markdown_lines(
    trajectory_history: Mapping[str, Any] | None,
    *,
    trajectory_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence trajectory section."""
    history = trajectory_history if isinstance(trajectory_history, Mapping) else {}
    summary = trajectory_summary if isinstance(trajectory_summary, Mapping) else {}
    baseline = summary.get("baseline_snapshot")
    current = summary.get("current_snapshot")
    if not isinstance(baseline, Mapping):
        baseline = {}
    if not isinstance(current, Mapping):
        current = {}
    lines = [
        "## Recurrence Trajectory",
        "",
        f"- Trajectory available: `{str(bool(summary.get('trajectory_available', False))).lower()}`",
        f"- Snapshot count: `{int(summary.get('snapshot_count') or len(history.get('snapshots') or []))}`",
        "",
        "### Current Snapshot",
        "",
        f"- Timestamp: `{_cell(current.get('timestamp'))}`",
        f"- Protected observations: `{int(current.get('protected_observation_count') or 0)}`",
        f"- Unique recurrence keys: `{int(current.get('unique_recurrence_keys') or 0)}`",
        f"- Portfolio risk score: `{float(current.get('portfolio_risk_score') or 0.0):.1f}`",
        f"- Governance health score: `{float(current.get('governance_health_score') or 0.0):.1f}`",
        f"- Operational readiness score: `{float(current.get('operational_readiness_score') or 0.0):.1f}`",
        f"- Effectiveness confidence: `{float(current.get('effectiveness_score') or 0.0):.2f}`",
        f"- Maturity score: `{float(current.get('maturity_score') or 0.0):.1f}`",
        "",
        "### Baseline Snapshot",
        "",
        f"- Timestamp: `{_cell(baseline.get('timestamp'))}`",
        f"- Protected observations: `{int(baseline.get('protected_observation_count') or 0)}`",
        f"- Unique recurrence keys: `{int(baseline.get('unique_recurrence_keys') or 0)}`",
        f"- Portfolio risk score: `{float(baseline.get('portfolio_risk_score') or 0.0):.1f}`",
        f"- Governance health score: `{float(baseline.get('governance_health_score') or 0.0):.1f}`",
        f"- Operational readiness score: `{float(baseline.get('operational_readiness_score') or 0.0):.1f}`",
        f"- Effectiveness confidence: `{float(baseline.get('effectiveness_score') or 0.0):.2f}`",
        f"- Maturity score: `{float(baseline.get('maturity_score') or 0.0):.1f}`",
        "",
        "### Trajectory Availability",
        "",
    ]
    message = str(summary.get("message") or "").strip()
    if message:
        lines.append(message)
    else:
        lines.append(RECURRENCE_TRAJECTORY_BASELINE_MESSAGE)
    lines.append("")
    if bool(summary.get("trajectory_available")):
        lines.extend(
            [
                "### Trajectory Changes",
                "",
                f"- Portfolio risk change: `{float(summary.get('portfolio_risk_change') or 0.0):+.1f}`",
                f"- Governance health change: `{float(summary.get('governance_health_change') or 0.0):+.1f}`",
                f"- Lifecycle health change: `{float(summary.get('lifecycle_health_change') or 0.0):+.1f}`",
                f"- Operational readiness change: `{float(summary.get('operational_readiness_change') or 0.0):+.1f}`",
                f"- Effectiveness change: `{float(summary.get('effectiveness_change') or 0.0):+.2f}`",
                f"- Maturity change: `{float(summary.get('maturity_change') or 0.0):+.1f}`",
                "",
            ]
        )
    return lines


def _recurrence_program_effectiveness_markdown_lines(
    effectiveness: Mapping[str, Any] | None,
    *,
    program_summary: Mapping[str, Any] | None = None,
    governance_effectiveness: Mapping[str, Any] | None = None,
    remediation_effectiveness: Mapping[str, Any] | None = None,
    forecast_effectiveness: Mapping[str, Any] | None = None,
    portfolio_trajectory: Mapping[str, Any] | None = None,
    stability_trajectory: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence program effectiveness section."""
    payload = effectiveness if isinstance(effectiveness, Mapping) else {}
    summary = program_summary if isinstance(program_summary, Mapping) else payload.get("program_effectiveness_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    governance = (
        governance_effectiveness
        if isinstance(governance_effectiveness, Mapping)
        else payload.get("governance_effectiveness_summary")
    )
    if not isinstance(governance, Mapping):
        governance = {}
    remediation = (
        remediation_effectiveness
        if isinstance(remediation_effectiveness, Mapping)
        else payload.get("remediation_effectiveness_summary")
    )
    if not isinstance(remediation, Mapping):
        remediation = {}
    forecast = (
        forecast_effectiveness
        if isinstance(forecast_effectiveness, Mapping)
        else payload.get("forecast_effectiveness_summary")
    )
    if not isinstance(forecast, Mapping):
        forecast = {}
    portfolio = (
        portfolio_trajectory
        if isinstance(portfolio_trajectory, Mapping)
        else payload.get("portfolio_trajectory_summary")
    )
    if not isinstance(portfolio, Mapping):
        portfolio = {}
    stability = (
        stability_trajectory
        if isinstance(stability_trajectory, Mapping)
        else payload.get("stability_trajectory_summary")
    )
    if not isinstance(stability, Mapping):
        stability = {}

    lines = [
        "## Recurrence Program Effectiveness",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Program effectiveness score: `{float(summary.get('program_effectiveness_score') or 0.0):.1f}`",
        f"- Effectiveness confidence: `{float(summary.get('effectiveness_confidence') or 0.0):.2f}`",
        f"- Recurrence reduction rate: `{float(summary.get('recurrence_reduction_rate') or 0.0) * 100.0:.1f}%`",
        f"- Forecast accuracy: `{float(summary.get('forecast_accuracy') or 0.0) * 100.0:.1f}%`",
        f"- Stability change: `{float(summary.get('stability_change') or 0.0):+.1f}`",
        "",
        "### Governance Effectiveness",
        "",
        f"- Watchlist conversion rate: `{float(governance.get('watchlist_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Investigate conversion rate: `{float(governance.get('investigate_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Prioritize conversion rate: `{float(governance.get('prioritize_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Retirement conversion rate: `{float(governance.get('retirement_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Governance effectiveness: `{float(governance.get('governance_effectiveness') or 0.0):.2f}`",
        "",
        "### Remediation Effectiveness",
        "",
        f"- Targeted keys: `{int(remediation.get('targeted_keys') or 0)}`",
        f"- Improved keys: `{int(remediation.get('improved_keys') or 0)}`",
        f"- Unresolved keys: `{int(remediation.get('unresolved_keys') or 0)}`",
        f"- Recurrence reduction rate: `{float(remediation.get('recurrence_reduction_rate') or 0.0) * 100.0:.1f}%`",
        "",
        "### Forecast Effectiveness",
        "",
        f"- Forecast accuracy: `{float(forecast.get('forecast_accuracy') or 0.0) * 100.0:.1f}%`",
        f"- Forecast confidence: `{float(forecast.get('forecast_confidence') or 0.0):.2f}`",
        f"- Predicted recurrences: `{int(forecast.get('predicted_recurrences') or 0)}`",
        f"- Realized recurrences: `{int(forecast.get('realized_recurrences') or 0)}`",
        f"- Low confidence: `{str(bool(forecast.get('low_confidence', False))).lower()}`",
        "",
        "### Portfolio Trajectory",
        "",
        f"- Trajectory available: `{str(bool(portfolio.get('trajectory_available', False))).lower()}`",
        f"- Portfolio risk change: `{float(portfolio.get('portfolio_risk_change') or 0.0):+.1f}`",
        f"- Concentration change: `{float(portfolio.get('concentration_change') or 0.0):+.4f}`",
        f"- Governance health change: `{float(portfolio.get('governance_health_change') or 0.0):+.1f}`",
        f"- Lifecycle health change: `{float(portfolio.get('lifecycle_health_change') or 0.0):+.1f}`",
        "",
        "### Stability Trajectory",
        "",
        f"- Trajectory available: `{str(bool(stability.get('trajectory_available', False))).lower()}`",
        f"- Stability score current: `{float(stability.get('stability_score_current') or 0.0):.1f}`",
        f"- Stability change: `{float(stability.get('stability_change') or 0.0):+.1f}`",
        f"- Recurrence rate change: `{float(stability.get('recurrence_rate_change') or 0.0):+.4f}`",
        "",
    ]
    return lines


def _recurrence_maturity_markdown_lines(
    maturity: Mapping[str, Any] | None,
    *,
    maturity_summary: Mapping[str, Any] | None = None,
    maturity_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    """Render protected replay recurrence maturity assessment section."""
    payload = maturity if isinstance(maturity, Mapping) else {}
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else payload.get("recurrence_maturity_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    gaps = [
        dict(row)
        for row in (maturity_gap_analysis or payload.get("maturity_gap_analysis") or ())
        if isinstance(row, Mapping)
    ]

    dimension_fields = (
        ("observability", "observability_maturity", summary.get("observability_score")),
        ("governance", "governance_maturity", summary.get("governance_score")),
        ("forecasting", "forecasting_maturity", summary.get("forecasting_score")),
        ("remediation", "remediation_maturity", summary.get("remediation_score")),
        ("lifecycle", "lifecycle_maturity", summary.get("lifecycle_score")),
        ("operational_readiness", "operational_readiness", summary.get("operational_readiness_score")),
    )

    lines = [
        "## Recurrence Maturity Assessment",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Overall maturity score: `{float(summary.get('overall_maturity_score') or 0.0):.1f}`",
        f"- Overall maturity level: `{str(summary.get('overall_maturity_level') or 'initial').replace('_', ' ').title()}`",
        f"- Highest dimension: `{summary.get('highest_dimension') or 'none'}`",
        f"- Lowest dimension: `{summary.get('lowest_dimension') or 'none'}`",
        "",
        "### Dimension Scores",
        "",
    ]
    for label, field_name, fallback_score in dimension_fields:
        dimension = payload.get(field_name)
        score = float(fallback_score or 0.0)
        if isinstance(dimension, Mapping):
            score = float(dimension.get("maturity_score") or score)
        lines.append(f"- {label.replace('_', ' ').title()}: `{score:.1f}`")

    lines.extend(["", "### Dimension Levels", ""])
    for label, field_name, _ in dimension_fields:
        dimension = payload.get(field_name)
        level = "initial"
        if isinstance(dimension, Mapping):
            level = str(dimension.get("maturity_level") or level)
        lines.append(f"- {label.replace('_', ' ').title()}: `{level.replace('_', ' ').title()}`")

    lines.extend(["", "### Capability Gaps", ""])
    if gaps:
        for row in gaps:
            lines.append(
                f"- {str(row.get('dimension') or 'unknown').replace('_', ' ').title()}: "
                f"current `{float(row.get('current_score') or 0.0):.1f}`, "
                f"target `{float(row.get('target_score') or 80.0):.1f}`, "
                f"gap `{float(row.get('gap') or 0.0):.1f}`"
            )
    else:
        lines.append("- No capability gaps recorded.")

    lines.extend(["", "### Improvement Priorities", ""])
    if gaps:
        for row in gaps:
            lines.append(
                f"- {str(row.get('dimension') or 'unknown').replace('_', ' ').title()}: "
                f"`{str(row.get('improvement_priority') or 'low')}`"
            )
    else:
        lines.append("- No improvement priorities recorded.")

    lines.append("")
    return lines


def _recurrence_roadmap_markdown_lines(
    roadmap: Mapping[str, Any] | None,
    *,
    roadmap_summary: Mapping[str, Any] | None = None,
    target_state: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence strategic roadmap section."""
    payload = roadmap if isinstance(roadmap, Mapping) else {}
    summary = roadmap_summary if isinstance(roadmap_summary, Mapping) else payload.get("recurrence_roadmap_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    target = target_state if isinstance(target_state, Mapping) else payload.get("recurrence_target_state")
    if not isinstance(target, Mapping):
        target = {}
    initiatives = [row for row in (payload.get("initiatives") or ()) if isinstance(row, Mapping)]
    sequence = [row for row in (payload.get("roadmap_sequence") or ()) if isinstance(row, Mapping)]

    lines = [
        "## Recurrence Strategic Roadmap",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Highest ROI initiative: `{summary.get('highest_roi_initiative') or 'data_volume_expansion'}`",
        f"- Largest gap dimension: `{summary.get('highest_gap_dimension') or 'operational_readiness'}`",
        f"- Estimated remaining initiatives: `{int(summary.get('estimated_initiatives_remaining') or 0)}`",
        f"- Target maturity state: `{str(target.get('target_maturity_level') or 'optimized').replace('_', ' ').title()}`",
        f"- Roadmap priority: `{summary.get('roadmap_priority_guidance') or 'Collect more protected replay observations before optimizing models.'}`",
        "",
        "### Priority Initiatives",
        "",
    ]
    for row in initiatives[:6]:
        lines.append(
            f"- {str(row.get('initiative_label') or row.get('initiative_id'))}: "
            f"ROI `{float(row.get('maturity_roi') or 0.0):.1f}`, "
            f"priority `{float(row.get('investment_priority_score') or 0.0):.1f}`, "
            f"complexity `{float(row.get('implementation_complexity') or 0.0):.1f}`"
        )

    lines.extend(["", "### Expected Maturity Lift", ""])
    for row in initiatives[:6]:
        projected = row.get("projected_maturity_after_completion")
        if not isinstance(projected, Mapping):
            projected = {}
        lines.append(
            f"- {str(row.get('initiative_label') or row.get('initiative_id'))}: "
            f"projected overall `{float(projected.get('overall_maturity_score') or 0.0):.1f}` "
            f"(`{str(projected.get('overall_maturity_level') or 'initial').replace('_', ' ').title()}`)"
        )

    lines.extend(["", "### Dependency Sequence", ""])
    if sequence:
        for row in sequence:
            deps = ", ".join(str(dep) for dep in (row.get("dependencies") or ()))
            dep_text = deps if deps else "none"
            lines.append(
                f"- Step `{int(row.get('sequence_step') or 0)}`: "
                f"`{row.get('initiative_id')}` "
                f"(dependencies: {dep_text}, completed: `{str(bool(row.get('completed'))).lower()}`)"
            )
    else:
        lines.append("- No roadmap sequence recorded.")

    lines.extend(["", "### Target State", ""])
    criteria = target.get("completion_criteria")
    if isinstance(criteria, Mapping):
        for name, met in criteria.items():
            lines.append(f"- {str(name).replace('_', ' ').title()}: `{str(bool(met)).lower()}`")
    else:
        lines.append("- Target state criteria not defined.")

    lines.append("")
    return lines


def _recurrence_completion_markdown_lines(
    completion: Mapping[str, Any] | None,
    *,
    completion_summary: Mapping[str, Any] | None = None,
    completion_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    """Render protected replay recurrence program completion section."""
    payload = completion if isinstance(completion, Mapping) else {}
    summary = (
        completion_summary
        if isinstance(completion_summary, Mapping)
        else payload.get("recurrence_completion_summary")
    )
    if not isinstance(summary, Mapping):
        summary = {}
    gaps = [
        dict(row)
        for row in (completion_gap_analysis or payload.get("completion_gap_analysis") or ())
        if isinstance(row, Mapping)
    ]
    dimension_fields = (
        ("observability", "observability_completion"),
        ("governance", "governance_completion"),
        ("forecasting", "forecasting_completion"),
        ("remediation", "remediation_completion"),
        ("lifecycle", "lifecycle_completion"),
        ("operational_readiness", "operational_readiness_completion"),
    )

    lines = [
        "## Recurrence Program Completion",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Overall completion score: `{float(summary.get('overall_completion_score') or 0.0):.1f}`",
        f"- Completed dimensions: `{len(summary.get('completed_dimensions') or [])}`",
        f"- Remaining dimensions: `{len(summary.get('remaining_dimensions') or [])}`",
        f"- Estimated completion distance: `{float(summary.get('estimated_completion_distance') or 0.0):.1f}`",
        f"- Graduation achieved: `{str(bool(summary.get('program_graduated'))).lower()}`",
        "",
        "### Dimension Completion Status",
        "",
    ]
    for label, field_name in dimension_fields:
        dimension = payload.get(field_name)
        if not isinstance(dimension, Mapping):
            dimension = {}
        status = "complete" if dimension.get("completion_met") else "incomplete"
        score = float(dimension.get("completion_score") or 0.0)
        lines.append(
            f"- {label.replace('_', ' ').title()}: `{status}` (score `{score:.1f}`)"
        )

    lines.extend(["", "### Remaining Requirements", ""])
    remaining = summary.get("remaining_requirements")
    if isinstance(remaining, list) and remaining:
        for requirement in remaining:
            lines.append(f"- `{requirement}`")
    else:
        lines.append("- No remaining requirements.")

    lines.extend(["", "### Completion Gaps", ""])
    if gaps:
        for row in gaps[:12]:
            lines.append(
                f"- {str(row.get('dimension') or 'unknown').replace('_', ' ').title()} / "
                f"`{row.get('requirement')}`: current `{row.get('current_value')}`, "
                f"target `{row.get('target_value')}`, gap `{float(row.get('gap') or 0.0):.2f}`, "
                f"roadmap `{row.get('roadmap_dependency')}`"
            )
    else:
        lines.append("- No completion gaps recorded.")

    lines.extend(["", "### Graduation Status", ""])
    lines.append(
        f"- Program graduated: `{str(bool(summary.get('program_graduated'))).lower()}`"
    )
    lines.append(
        f"- Completion criteria met: `{str(bool(summary.get('completion_criteria_met'))).lower()}`"
    )
    lines.append("")
    return lines


def _recurrence_graduation_audit_markdown_lines(
    audit: Mapping[str, Any] | None,
    *,
    audit_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence graduation audit section."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = audit_summary if isinstance(audit_summary, Mapping) else payload.get("recurrence_graduation_audit_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    blind_spots = [row for row in (payload.get("blind_spots") or ()) if isinstance(row, Mapping)]
    redundancies = [row for row in (payload.get("redundancies") or ()) if isinstance(row, Mapping)]
    capabilities = [row for row in (payload.get("capability_coverage") or ()) if isinstance(row, Mapping)]

    lines = [
        "## Recurrence Graduation Audit",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Graduation readiness score: `{float(summary.get('graduation_readiness_score') or 0.0):.1f}`",
        f"- Readiness level: `{summary.get('readiness_label') or 'unknown'}`",
        f"- Critical blind spots: `{int(summary.get('critical_blind_spots') or 0)}`",
        f"- Critical redundancies: `{int(summary.get('critical_redundancies') or 0)}`",
        f"- Recommended next action: {summary.get('recommended_next_action') or 'none recorded'}",
        "",
        "### Capability Coverage",
        "",
    ]
    for row in capabilities:
        lines.append(
            f"- {row.get('capability_label')}: implemented `{str(bool(row.get('implemented'))).lower()}`, "
            f"validated `{str(bool(row.get('validated'))).lower()}`, operational `{str(bool(row.get('operational'))).lower()}`, "
            f"confidence `{float(row.get('confidence') or 0.0):.2f}`"
        )
    lines.extend(["", "### Blind Spots", ""])
    if blind_spots:
        for row in blind_spots:
            lines.append(
                f"- `{row.get('blind_spot_id')}` ({row.get('severity')}): {row.get('description')}"
            )
    else:
        lines.append("- No blind spots identified.")
    lines.extend(["", "### Redundancies", ""])
    if redundancies:
        for row in redundancies:
            lines.append(
                f"- `{row.get('redundancy_id')}` ({row.get('severity')}): {row.get('consolidation_recommendation')}"
            )
    else:
        lines.append("- No redundancies identified.")
    lines.extend(["", "### Graduation Readiness", ""])
    readiness = payload.get("graduation_readiness")
    if isinstance(readiness, Mapping):
        lines.append(f"- Operational capability ratio: `{float(readiness.get('operational_capability_ratio') or 0.0):.2f}`")
        lines.append(f"- Validated capability ratio: `{float(readiness.get('validated_capability_ratio') or 0.0):.2f}`")
        lines.append(f"- Average capability confidence: `{float(readiness.get('average_capability_confidence') or 0.0):.2f}`")
    lines.append(f"- Program graduated: `{str(bool(summary.get('program_graduated'))).lower()}`")
    lines.append("")
    return lines


def _recurrence_confidence_calibration_markdown_lines(
    audit: Mapping[str, Any] | None,
    *,
    calibration_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence confidence calibration audit section."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = calibration_summary if isinstance(calibration_summary, Mapping) else payload.get(
        "recurrence_confidence_calibration_summary"
    )
    if not isinstance(summary, Mapping):
        summary = {}
    forecast = payload.get("forecast_confidence_audit")
    if not isinstance(forecast, Mapping):
        forecast = {}
    governance = payload.get("governance_confidence_audit")
    if not isinstance(governance, Mapping):
        governance = {}
    effectiveness = payload.get("effectiveness_confidence_audit")
    if not isinstance(effectiveness, Mapping):
        effectiveness = {}
    threshold_rows = [
        row for row in (payload.get("graduation_threshold_validation") or ()) if isinstance(row, Mapping)
    ]

    lines = [
        "## Confidence Calibration Audit",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Calibration score: `{float(summary.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Interpretation: `{summary.get('interpretation_label') or 'unknown'}`",
        f"- Largest calibration gap: `{float(summary.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Graduation confidence ready: `{str(bool(summary.get('graduation_confidence_ready'))).lower()}`",
        "",
        "### Forecast Calibration",
        "",
        f"- Reported confidence: `{float(forecast.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(forecast.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(forecast.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{forecast.get('confidence_status') or 'unknown'}`",
        "",
        "### Governance Calibration",
        "",
        f"- Reported confidence: `{float(governance.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(governance.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(governance.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{governance.get('confidence_status') or 'unknown'}`",
        "",
        "### Effectiveness Calibration",
        "",
        f"- Reported confidence: `{float(effectiveness.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(effectiveness.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(effectiveness.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{effectiveness.get('confidence_status') or 'unknown'}`",
        "",
        "### Graduation Threshold Validation",
        "",
    ]
    if threshold_rows:
        for row in threshold_rows:
            lines.append(
                f"- `{row.get('threshold')}`: current `{row.get('current_value')}`, "
                f"target `{row.get('target_value')}`, status `{row.get('validation_status')}`"
            )
    else:
        lines.append("- No graduation threshold validation recorded.")
    lines.append("")
    return lines


def render_bug_recurrence_history_markdown(
    history: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
) -> str:
    """Render report-only bug-class recurrence history markdown."""
    payload = history if isinstance(history, Mapping) else aggregate_recurrence_history([])
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command_s = command_used if command_used is not None else " ".join(sys.argv)
    summary_rows = build_recurrence_summary(payload)
    report_only = str(bool(payload.get("report_only", True))).lower()
    advisory_only = str(bool(payload.get("advisory_only", True))).lower()
    metric = payload.get("regression_recurrence_rate")
    if not isinstance(metric, Mapping):
        metric = calculate_regression_recurrence_rate(payload)
    lines = [
        "# Bug-Class Recurrence History",
        "",
        f"- Generated at: `{generated_at_s}`",
        f"- Command: `{command_s or 'unavailable'}`",
        f"- Report only: `{report_only}`",
        f"- Advisory only: `{advisory_only}`",
        f"- Total recurrence keys: `{int(payload.get('unique_recurrence_count') or 0)}`",
        f"- Total recurrence events: `{int(payload.get('total_rows') or 0)}`",
        "",
    ]
    lines.extend(_regression_recurrence_rate_markdown_lines(metric))
    trends = payload.get("recurrence_trends")
    timeline = payload.get("recurrence_timeline")
    if isinstance(trends, Mapping):
        lines.extend(
            _recurrence_trends_markdown_lines(
                trends,
                timeline=timeline if isinstance(timeline, list) else None,
            )
        )
    forecast = payload.get("recurrence_forecast")
    if isinstance(forecast, Mapping):
        lines.extend(_recurrence_forecast_markdown_lines(forecast))
    portfolio = payload.get("recurrence_portfolio")
    portfolio_summary = payload.get("recurrence_portfolio_summary")
    if isinstance(portfolio, Mapping):
        lines.extend(
            _recurrence_portfolio_markdown_lines(
                portfolio,
                portfolio_summary=portfolio_summary if isinstance(portfolio_summary, Mapping) else None,
            )
        )
    remediation = payload.get("recurrence_remediation_targets")
    remediation_summary = payload.get("recurrence_remediation_summary")
    if isinstance(remediation, Mapping):
        lines.extend(
            _recurrence_remediation_markdown_lines(
                remediation,
                remediation_summary=remediation_summary if isinstance(remediation_summary, Mapping) else None,
            )
        )
    roi = payload.get("recurrence_roi")
    roi_summary = payload.get("recurrence_roi_summary")
    if isinstance(roi, Mapping):
        lines.extend(
            _recurrence_roi_markdown_lines(
                roi,
                roi_summary=roi_summary if isinstance(roi_summary, Mapping) else None,
            )
        )
    governance = payload.get("recurrence_governance")
    governance_summary = payload.get("recurrence_governance_summary")
    watchlist = payload.get("recurrence_watchlist")
    retirement_summary = payload.get("recurrence_retirement_summary")
    if isinstance(governance, Mapping):
        lines.extend(
            _recurrence_governance_markdown_lines(
                governance,
                governance_summary=governance_summary if isinstance(governance_summary, Mapping) else None,
                watchlist=watchlist if isinstance(watchlist, list) else None,
                retirement_summary=retirement_summary if isinstance(retirement_summary, Mapping) else None,
            )
        )
    lifecycle = payload.get("recurrence_lifecycle")
    lifecycle_summary = payload.get("recurrence_lifecycle_summary")
    if isinstance(lifecycle, Mapping):
        lines.extend(
            _recurrence_lifecycle_markdown_lines(
                lifecycle,
                lifecycle_summary=lifecycle_summary if isinstance(lifecycle_summary, Mapping) else None,
                age_distribution=payload.get("recurrence_age_distribution")
                if isinstance(payload.get("recurrence_age_distribution"), Mapping)
                else None,
                transition_summary=payload.get("recurrence_transition_summary")
                if isinstance(payload.get("recurrence_transition_summary"), Mapping)
                else None,
                closure_effectiveness=payload.get("recurrence_closure_effectiveness")
                if isinstance(payload.get("recurrence_closure_effectiveness"), Mapping)
                else None,
            )
        )
    effectiveness = payload.get("recurrence_program_effectiveness")
    if isinstance(effectiveness, Mapping):
        lines.extend(
            _recurrence_program_effectiveness_markdown_lines(
                effectiveness,
                program_summary=payload.get("recurrence_program_effectiveness_summary")
                if isinstance(payload.get("recurrence_program_effectiveness_summary"), Mapping)
                else None,
                governance_effectiveness=payload.get("governance_effectiveness_summary")
                if isinstance(payload.get("governance_effectiveness_summary"), Mapping)
                else None,
                remediation_effectiveness=payload.get("remediation_effectiveness_summary")
                if isinstance(payload.get("remediation_effectiveness_summary"), Mapping)
                else None,
                forecast_effectiveness=payload.get("forecast_effectiveness_summary")
                if isinstance(payload.get("forecast_effectiveness_summary"), Mapping)
                else None,
                portfolio_trajectory=payload.get("portfolio_trajectory_summary")
                if isinstance(payload.get("portfolio_trajectory_summary"), Mapping)
                else None,
                stability_trajectory=payload.get("stability_trajectory_summary")
                if isinstance(payload.get("stability_trajectory_summary"), Mapping)
                else None,
            )
        )
    maturity = payload.get("recurrence_maturity")
    if isinstance(maturity, Mapping):
        lines.extend(
            _recurrence_maturity_markdown_lines(
                maturity,
                maturity_summary=payload.get("recurrence_maturity_summary")
                if isinstance(payload.get("recurrence_maturity_summary"), Mapping)
                else None,
                maturity_gap_analysis=payload.get("recurrence_maturity_gap_analysis")
                if isinstance(payload.get("recurrence_maturity_gap_analysis"), list)
                else None,
            )
        )
    roadmap = payload.get("recurrence_roadmap")
    if isinstance(roadmap, Mapping):
        lines.extend(
            _recurrence_roadmap_markdown_lines(
                roadmap,
                roadmap_summary=payload.get("recurrence_roadmap_summary")
                if isinstance(payload.get("recurrence_roadmap_summary"), Mapping)
                else None,
                target_state=payload.get("recurrence_target_state")
                if isinstance(payload.get("recurrence_target_state"), Mapping)
                else None,
            )
        )
    completion = payload.get("recurrence_completion")
    if isinstance(completion, Mapping):
        lines.extend(
            _recurrence_completion_markdown_lines(
                completion,
                completion_summary=payload.get("recurrence_completion_summary")
                if isinstance(payload.get("recurrence_completion_summary"), Mapping)
                else None,
                completion_gap_analysis=payload.get("recurrence_completion_gap_analysis")
                if isinstance(payload.get("recurrence_completion_gap_analysis"), list)
                else None,
            )
        )
    graduation_audit = payload.get("recurrence_graduation_audit")
    if isinstance(graduation_audit, Mapping):
        lines.extend(
            _recurrence_graduation_audit_markdown_lines(
                graduation_audit,
                audit_summary=payload.get("recurrence_graduation_audit_summary")
                if isinstance(payload.get("recurrence_graduation_audit_summary"), Mapping)
                else None,
            )
        )
    trajectory_history = payload.get("recurrence_trajectory_history")
    trajectory_summary = payload.get("recurrence_trajectory_summary")
    if isinstance(trajectory_history, Mapping) or isinstance(trajectory_summary, Mapping):
        lines.extend(
            _recurrence_trajectory_markdown_lines(
                trajectory_history if isinstance(trajectory_history, Mapping) else None,
                trajectory_summary=trajectory_summary if isinstance(trajectory_summary, Mapping) else None,
            )
        )
    confidence_audit = payload.get("recurrence_confidence_audit")
    if isinstance(confidence_audit, Mapping):
        lines.extend(
            _recurrence_confidence_calibration_markdown_lines(
                confidence_audit,
                calibration_summary=payload.get("recurrence_confidence_calibration_summary")
                if isinstance(payload.get("recurrence_confidence_calibration_summary"), Mapping)
                else None,
            )
        )
    if not summary_rows:
        lines.extend(["No recurrence history recorded.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |",
            "|---|---:|---|---|---|---|---|---|",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("recurrence_key")),
                    _cell(row.get("occurrence_count")),
                    _cell(row.get("owner")),
                    _cell(row.get("status")),
                    _cell(row.get("categories")),
                    _cell(row.get("field_paths")),
                    _cell(row.get("affected_scenarios")),
                    _cell(row.get("latest_investigate_first")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _bug_recurrence_event_log_path(json_path: Path | str) -> Path:
    history_path = Path(json_path)
    if history_path.name == BUG_RECURRENCE_HISTORY_JSON_PATH.name:
        return history_path.with_name(BUG_RECURRENCE_EVENT_LOG_JSON_PATH.name)
    return history_path.with_name(f"{history_path.stem}_event_log.json")


def _bug_recurrence_session_diagnostic_event_log_path(json_path: Path | str) -> Path:
    history_path = Path(json_path)
    if history_path.name == BUG_RECURRENCE_HISTORY_JSON_PATH.name:
        return history_path.with_name(BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH.name)
    return history_path.with_name(f"{history_path.stem}_session_diagnostic_event_log.json")


def _bug_recurrence_trajectory_history_path(json_path: Path | str) -> Path:
    history_path = Path(json_path).resolve()
    if history_path == BUG_RECURRENCE_HISTORY_JSON_PATH.resolve():
        return RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH
    return history_path.with_name("recurrence_trajectory_history.json")


def protected_replay_recurrence_event_metadata(
    *,
    command_used: str | None = None,
    generated_at: str | None = None,
    artifact_source: Path | str | None = None,
    persistence_intent: str | None = None,
) -> dict[str, Any]:
    """Build recurrence metadata for protected replay failure report writes."""
    artifact = str(artifact_source).strip() if artifact_source is not None else ""
    return normalize_recurrence_event_metadata(
        {
            "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
            "recorded_at": generated_at,
            "command": command_used,
            "run_id": generated_at,
            "artifact_source": artifact or str(PROTECTED_REPLAY_FAILURE_REPORT_PATH),
            "persistence_intent": persistence_intent,
        }
    )


def write_bug_recurrence_history_artifacts(
    rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    markdown_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    event_log_path: Path | str | None = None,
    session_diagnostic_event_log_path: Path | str | None = None,
    command_used: str | None = None,
    generated_at: str | None = None,
    recurrence_event_metadata: Mapping[str, Any] | None = None,
    event_source: str | None = None,
    recorded_at: str | None = None,
    persistence_report: dict[str, Any] | None = None,
    temporal_trajectory_capture: bool = False,
) -> tuple[Path, Path]:
    """Write report-only bug-class recurrence JSON and markdown artifacts."""
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    log_out = Path(event_log_path) if event_log_path is not None else _bug_recurrence_event_log_path(json_out)
    session_log_out = (
        Path(session_diagnostic_event_log_path)
        if session_diagnostic_event_log_path is not None
        else _bug_recurrence_session_diagnostic_event_log_path(json_out)
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)

    protected_log = load_recurrence_event_log(log_out)
    session_diagnostic_log = load_recurrence_event_log(session_log_out)
    if rows:
        merge_kwargs: dict[str, Any] = {
            "event_source": event_source,
            "recorded_at": recorded_at or generated_at,
        }
        if not (isinstance(recurrence_event_metadata, Mapping) and recurrence_event_metadata.get("command")):
            merge_kwargs["command"] = command_used
        metadata = normalize_recurrence_event_metadata(
            recurrence_event_metadata,
            **merge_kwargs,
        )
        lane_result = append_recurrence_events_to_persistence_lanes(
            protected_log,
            session_diagnostic_log,
            rows,
            event_metadata=metadata,
        )
        protected_log = lane_result["protected_log"]
        session_diagnostic_log = lane_result["session_diagnostic_log"]
        write_recurrence_event_log(log_out, protected_log)
        write_recurrence_event_log(session_log_out, session_diagnostic_log)
        if persistence_report is not None:
            persistence_report.clear()
            persistence_report.update(lane_result)

    recurrence_history = aggregate_protected_recurrence_history_from_event_log(protected_log)
    recurrence_timeline = build_recurrence_timeline(protected_log)
    recurrence_trends = build_recurrence_trend_summary(protected_log)
    recurrence_forecast = build_recurrence_forecast(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        regression_recurrence_rate=recurrence_history.get("regression_recurrence_rate"),
    )
    recurrence_portfolio = build_recurrence_portfolio(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        event_log=protected_log,
    )
    recurrence_remediation_targets = build_recurrence_remediation_targets(
        recurrence_portfolio=recurrence_portfolio,
        recurrence_forecast=recurrence_forecast,
        recurrence_trends=recurrence_trends,
        recurrence_history=recurrence_history,
        recurrence_timeline=recurrence_timeline,
        event_log=protected_log,
    )
    recurrence_roi = build_recurrence_roi_analysis(
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_history=recurrence_history,
    )
    recurrence_governance = build_recurrence_governance(
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_history=recurrence_history,
        recurrence_timeline=recurrence_timeline,
    )
    recurrence_lifecycle = build_recurrence_lifecycle(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_governance=recurrence_governance,
        recurrence_history=recurrence_history,
    )
    recurrence_program_effectiveness = build_recurrence_program_effectiveness(
        recurrence_governance=recurrence_governance,
        recurrence_remediation_summary=recurrence_remediation_targets["remediation_summary"],
        recurrence_roi_summary=recurrence_roi["roi_summary"],
        recurrence_lifecycle_summary=recurrence_lifecycle["lifecycle_summary"],
        recurrence_portfolio_summary=recurrence_portfolio["portfolio_summary"],
        recurrence_forecast=recurrence_forecast,
        recurrence_history=recurrence_history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_remediation_targets=recurrence_remediation_targets,
    )
    recurrence_maturity = build_recurrence_maturity_assessment(
        recurrence_history=recurrence_history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    recurrence_roadmap = build_recurrence_strategic_roadmap(
        recurrence_maturity_summary=recurrence_maturity["recurrence_maturity_summary"],
        recurrence_maturity_gap_analysis=recurrence_maturity["maturity_gap_analysis"],
        recurrence_program_effectiveness_summary=recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        recurrence_portfolio_summary=recurrence_portfolio["portfolio_summary"],
        recurrence_forecast_summary=recurrence_forecast["forecast_summary"],
        recurrence_lifecycle_summary=recurrence_lifecycle["lifecycle_summary"],
        recurrence_remediation_effectiveness_summary=recurrence_program_effectiveness[
            "remediation_effectiveness_summary"
        ],
        portfolio_trajectory_summary=recurrence_program_effectiveness["portfolio_trajectory_summary"],
        total_observations=int(recurrence_history.get("total_rows") or 0),
        total_keys=int(recurrence_history.get("unique_recurrence_count") or 0),
    )
    recurrence_completion = build_recurrence_completion_assessment(
        recurrence_maturity_summary=recurrence_maturity["recurrence_maturity_summary"],
        recurrence_program_effectiveness_summary=recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        recurrence_target_state=recurrence_roadmap["recurrence_target_state"],
        recurrence_roadmap_summary=recurrence_roadmap["recurrence_roadmap_summary"],
        recurrence_history={
            **recurrence_history,
            "recurrence_timeline": recurrence_timeline,
            "recurrence_trends": recurrence_trends,
            "recurrence_forecast": recurrence_forecast,
            "recurrence_portfolio": recurrence_portfolio,
            "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
            "recurrence_governance": recurrence_governance,
            "recurrence_governance_summary": recurrence_governance["governance_summary"],
            "recurrence_retirement_summary": recurrence_governance["retirement_summary"],
            "recurrence_lifecycle": recurrence_lifecycle,
            "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
            "recurrence_transition_summary": recurrence_lifecycle["transition_summary"],
            "recurrence_age_distribution": recurrence_lifecycle["age_distribution"],
            "recurrence_closure_effectiveness": recurrence_lifecycle["closure_effectiveness"],
            "recurrence_remediation_targets": recurrence_remediation_targets,
            "recurrence_remediation_summary": recurrence_remediation_targets["remediation_summary"],
            "recurrence_roi": recurrence_roi,
            "recurrence_roi_summary": recurrence_roi["roi_summary"],
        },
        recurrence_governance_summary=recurrence_governance["governance_summary"],
        recurrence_forecast_summary=recurrence_forecast["forecast_summary"],
        forecast_effectiveness_summary=recurrence_program_effectiveness[
            "forecast_effectiveness_summary"
        ],
        remediation_effectiveness_summary=recurrence_program_effectiveness[
            "remediation_effectiveness_summary"
        ],
        recurrence_lifecycle_summary=recurrence_lifecycle["lifecycle_summary"],
        recurrence_roi_summary=recurrence_roi["roi_summary"],
        portfolio_trajectory_summary=recurrence_program_effectiveness["portfolio_trajectory_summary"],
    )
    enriched_history = {
        **recurrence_history,
        "recurrence_timeline": recurrence_timeline,
        "recurrence_trends": recurrence_trends,
        "recurrence_forecast": recurrence_forecast,
        "recurrence_portfolio": recurrence_portfolio,
        "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
        "recurrence_governance": recurrence_governance,
        "recurrence_governance_summary": recurrence_governance["governance_summary"],
        "recurrence_retirement_summary": recurrence_governance["retirement_summary"],
        "recurrence_lifecycle": recurrence_lifecycle,
        "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
        "recurrence_transition_summary": recurrence_lifecycle["transition_summary"],
        "recurrence_age_distribution": recurrence_lifecycle["age_distribution"],
        "recurrence_closure_effectiveness": recurrence_lifecycle["closure_effectiveness"],
        "recurrence_remediation_targets": recurrence_remediation_targets,
        "recurrence_remediation_summary": recurrence_remediation_targets["remediation_summary"],
        "recurrence_roi": recurrence_roi,
        "recurrence_roi_summary": recurrence_roi["roi_summary"],
        "recurrence_maturity": recurrence_maturity,
        "recurrence_maturity_summary": recurrence_maturity["recurrence_maturity_summary"],
        "recurrence_roadmap": recurrence_roadmap,
        "recurrence_roadmap_summary": recurrence_roadmap["recurrence_roadmap_summary"],
        "recurrence_target_state": recurrence_roadmap["recurrence_target_state"],
        "recurrence_completion": recurrence_completion,
        "recurrence_completion_summary": recurrence_completion["recurrence_completion_summary"],
    }
    recurrence_graduation_audit = build_recurrence_graduation_audit(
        recurrence_history=enriched_history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_roadmap=recurrence_roadmap,
        recurrence_completion=recurrence_completion,
    )
    trajectory_result = apply_recurrence_trajectory_to_analytics(
        timestamp=generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        artifact_source=str(json_out),
        recurrence_history=recurrence_history,
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_roadmap=recurrence_roadmap,
        recurrence_completion=recurrence_completion,
        recurrence_graduation_audit=recurrence_graduation_audit,
        trajectory_history_path=_bug_recurrence_trajectory_history_path(json_out),
        temporal_capture=temporal_trajectory_capture,
    )
    recurrence_program_effectiveness = trajectory_result["recurrence_program_effectiveness"]
    recurrence_maturity = trajectory_result["recurrence_maturity"]
    recurrence_roadmap = trajectory_result["recurrence_roadmap"]
    recurrence_completion = trajectory_result["recurrence_completion"]
    recurrence_graduation_audit = trajectory_result["recurrence_graduation_audit"]
    recurrence_trajectory_history = trajectory_result["recurrence_trajectory_history"]
    recurrence_trajectory_summary = trajectory_result["recurrence_trajectory_summary"]
    enriched_history_for_confidence = {
        **recurrence_history,
        "recurrence_timeline": recurrence_timeline,
        "recurrence_trends": recurrence_trends,
        "recurrence_forecast": recurrence_forecast,
        "recurrence_portfolio": recurrence_portfolio,
        "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
        "recurrence_governance": recurrence_governance,
        "recurrence_governance_summary": recurrence_governance["governance_summary"],
        "recurrence_lifecycle": recurrence_lifecycle,
        "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
        "recurrence_program_effectiveness": recurrence_program_effectiveness,
        "recurrence_program_effectiveness_summary": recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        "recurrence_maturity": recurrence_maturity,
        "recurrence_maturity_summary": recurrence_maturity["recurrence_maturity_summary"],
        "recurrence_completion": recurrence_completion,
        "recurrence_completion_summary": recurrence_completion["recurrence_completion_summary"],
        "recurrence_trajectory_summary": recurrence_trajectory_summary,
    }
    recurrence_confidence_audit = build_recurrence_confidence_audit(
        recurrence_forecast=recurrence_forecast,
        recurrence_governance=recurrence_governance,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_history=enriched_history_for_confidence,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_portfolio_summary=recurrence_portfolio["portfolio_summary"],
    )
    recurrence_outcome_validation = None
    if bool(recurrence_trajectory_summary.get("trajectory_available")):
        recurrence_outcome_validation = build_recurrence_outcome_validation(
            recurrence_history=enriched_history_for_confidence,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_remediation_targets=recurrence_remediation_targets,
            recurrence_program_effectiveness=recurrence_program_effectiveness,
            recurrence_trajectory_summary=recurrence_trajectory_summary,
            recurrence_forecast=recurrence_forecast,
            recurrence_governance=recurrence_governance,
            recurrence_maturity=recurrence_maturity,
            recurrence_completion=recurrence_completion,
            recurrence_graduation_audit=recurrence_graduation_audit,
            event_log=protected_log,
            as_of=generated_at,
        )
        recurrence_confidence_audit = recurrence_outcome_validation["recurrence_confidence_audit"]
    recurrence_final_graduation_decision = build_recurrence_final_graduation_decision(
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_trajectory_history=recurrence_trajectory_history,
        recurrence_confidence_audit=recurrence_confidence_audit,
        recurrence_graduation_audit=recurrence_graduation_audit,
        recurrence_completion=recurrence_completion,
        recurrence_maturity=recurrence_maturity,
    )
    payload = {
        **recurrence_history,
        "summary": build_recurrence_summary(recurrence_history),
        "recurrence_timeline": recurrence_timeline,
        "recurrence_trends": recurrence_trends,
        "recurrence_forecast": recurrence_forecast,
        "recurrence_portfolio": recurrence_portfolio,
        "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
        "recurrence_remediation_targets": recurrence_remediation_targets,
        "recurrence_remediation_summary": recurrence_remediation_targets["remediation_summary"],
        "recurrence_roi": recurrence_roi,
        "recurrence_roi_summary": recurrence_roi["roi_summary"],
        "recurrence_governance": recurrence_governance,
        "recurrence_watchlist": recurrence_governance["watchlist"],
        "recurrence_governance_summary": recurrence_governance["governance_summary"],
        "recurrence_retirement_summary": recurrence_governance["retirement_summary"],
        "recurrence_lifecycle": recurrence_lifecycle,
        "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
        "recurrence_age_distribution": recurrence_lifecycle["age_distribution"],
        "recurrence_transition_summary": recurrence_lifecycle["transition_summary"],
        "recurrence_closure_effectiveness": recurrence_lifecycle["closure_effectiveness"],
        "recurrence_program_effectiveness": recurrence_program_effectiveness,
        "recurrence_program_effectiveness_summary": recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        "governance_effectiveness_summary": recurrence_program_effectiveness[
            "governance_effectiveness_summary"
        ],
        "remediation_effectiveness_summary": recurrence_program_effectiveness[
            "remediation_effectiveness_summary"
        ],
        "forecast_effectiveness_summary": recurrence_program_effectiveness[
            "forecast_effectiveness_summary"
        ],
        "portfolio_trajectory_summary": recurrence_program_effectiveness["portfolio_trajectory_summary"],
        "stability_trajectory_summary": recurrence_program_effectiveness["stability_trajectory_summary"],
        "recurrence_maturity": recurrence_maturity,
        "recurrence_maturity_summary": recurrence_maturity["recurrence_maturity_summary"],
        "recurrence_maturity_gap_analysis": recurrence_maturity["maturity_gap_analysis"],
        "recurrence_roadmap": recurrence_roadmap,
        "recurrence_roadmap_summary": recurrence_roadmap["recurrence_roadmap_summary"],
        "recurrence_target_state": recurrence_roadmap["recurrence_target_state"],
        "recurrence_completion": recurrence_completion,
        "recurrence_completion_summary": recurrence_completion["recurrence_completion_summary"],
        "recurrence_completion_gap_analysis": recurrence_completion["completion_gap_analysis"],
        "recurrence_graduation_audit": recurrence_graduation_audit,
        "recurrence_graduation_audit_summary": recurrence_graduation_audit[
            "recurrence_graduation_audit_summary"
        ],
        "recurrence_trajectory_history": recurrence_trajectory_history,
        "recurrence_trajectory_summary": recurrence_trajectory_summary,
        "recurrence_confidence_audit": recurrence_confidence_audit,
        "recurrence_confidence_calibration_summary": recurrence_confidence_audit[
            "recurrence_confidence_calibration_summary"
        ],
        "recurrence_final_graduation_decision": recurrence_final_graduation_decision,
    }
    if isinstance(recurrence_outcome_validation, Mapping):
        payload["recurrence_outcome_validation"] = recurrence_outcome_validation
        payload["outcome_validation_summary"] = recurrence_outcome_validation["outcome_validation_summary"]
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_bug_recurrence_history_markdown(
            payload,
            generated_at=generated_at,
            command_used=command_used,
        ),
        encoding="utf-8",
    )
    if json_out.name == BUG_RECURRENCE_HISTORY_JSON_PATH.name:
        audit_doc_path = RECURRENCE_GRADUATION_AUDIT_DOC_PATH
        audit_doc_path.parent.mkdir(parents=True, exist_ok=True)
        audit_doc_path.write_text(
            render_recurrence_graduation_audit_report_markdown(
                recurrence_graduation_audit,
                generated_at=generated_at,
            ),
            encoding="utf-8",
        )
        if not bool(recurrence_trajectory_summary.get("trajectory_available")):
            calibration_doc_path = RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH
            calibration_doc_path.parent.mkdir(parents=True, exist_ok=True)
            calibration_doc_path.write_text(
                render_recurrence_confidence_calibration_report_markdown(
                    recurrence_confidence_audit,
                    generated_at=generated_at,
                ),
                encoding="utf-8",
            )
        final_decision_doc_path = RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH
        final_decision_doc_path.parent.mkdir(parents=True, exist_ok=True)
        final_decision_doc_path.write_text(
            render_recurrence_final_graduation_decision_report_markdown(
                recurrence_final_graduation_decision,
                generated_at=generated_at,
            ),
            encoding="utf-8",
        )
        if isinstance(recurrence_outcome_validation, Mapping):
            outcome_doc_path = RECURRENCE_OUTCOME_VALIDATION_DOC_PATH
            outcome_doc_path.parent.mkdir(parents=True, exist_ok=True)
            outcome_doc_path.write_text(
                render_recurrence_outcome_validation_report_markdown(
                    recurrence_outcome_validation,
                    generated_at=generated_at,
                ),
                encoding="utf-8",
            )
    return json_out, markdown_out


def write_owner_drift_risk_artifacts(
    classifications: Sequence[Mapping[str, Any]] | None = None,
    *,
    json_path: Path | str = OWNER_DRIFT_RISK_JSON_PATH,
    markdown_path: Path | str = OWNER_DRIFT_RISK_MARKDOWN_PATH,
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
        json_path=json_out.with_name(BUG_RECURRENCE_HISTORY_JSON_PATH.name),
        markdown_path=markdown_out.with_name(BUG_RECURRENCE_HISTORY_MARKDOWN_PATH.name),
        command_used=command_used,
        generated_at=generated_at,
        recurrence_event_metadata=recurrence_event_metadata,
    )
    return json_out, markdown_out


def render_failure_dashboard_markdown(
    rows: Sequence[Mapping[str, Any]],
    *,
    title: str = "Replay Failure Classification Dashboard",
    generated_at: str | None = None,
    command_used: str | None = None,
    runtime_lineage_events: Any = None,
) -> str:
    """Render deterministic markdown table rows for replay failure diagnostics."""
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command_s = command_used if command_used is not None else " ".join(sys.argv)
    lines = [
        f"# {title}",
        "",
        f"- Generated at: `{generated_at_s}`",
        f"- Command: `{command_s or 'unavailable'}`",
        "",
    ]
    if not rows:
        lines.extend(["No replay failures classified.", ""])
        lines.extend(_runtime_lineage_markdown_lines(runtime_lineage_events))
        return "\n".join(lines)
    lines.extend(
        [
            _failure_dashboard_table_header(),
            _failure_dashboard_table_separator(),
        ]
    )
    for row in sorted(
        rows,
        key=lambda item: (
            str(item.get("scenario_id") or ""),
            int(item.get("turn_index") or 0),
            str(item.get("field_path") or ""),
            str(item.get("category") or ""),
        ),
    ):
        validation_errors = failure_dashboard_row_shape_errors(row)
        if validation_errors:
            raise ValueError(f"invalid failure dashboard row: {validation_errors}")
        mutation_flags = [
            tag
            for tag in _as_list(row.get("replay_tags"))
            if str(tag) in {"semantic_mutation", "scaffold_leakage", "post_gate_mutation", "response_type_repair_mismatch"}
        ]
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("scenario_id")),
                    _cell(row.get("turn_index")),
                    _cell(row.get("category")),
                    _cell(row.get("severity")),
                    _cell(row.get("primary_owner")),
                    _cell(row.get("secondary_owner")),
                    _cell(row.get("investigate_first")),
                    _cell(_evidence_cell(row)),
                    _cell(row.get("replay_tags")),
                    _cell(row.get("field_path")),
                    _cell(row.get("expected")),
                    _cell(row.get("actual")),
                    _cell(row.get("unavailable_fields")),
                    _cell(row.get("final_emitted_source")),
                    _cell(row.get("fallback_family")),
                    _cell(row.get("post_gate_mutation_detected")),
                    _cell(mutation_flags),
                    _cell(row.get("owner_drift_bucket")),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.extend(_owner_drift_breakdown_lines(summarize_owner_drift_buckets(rows)))
    lines.extend(_runtime_lineage_markdown_lines(runtime_lineage_events))
    return "\n".join(lines)


def write_failure_dashboard_artifact(
    rows: Sequence[Mapping[str, Any]],
    *,
    path: Path | str = FAILURE_DASHBOARD_LATEST_PATH,
    command_used: str | None = None,
    generated_at: str | None = None,
    runtime_lineage_events: Any = None,
) -> Path:
    """Write the latest failure dashboard artifact and return its path."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_failure_dashboard_markdown(
            rows,
            title="Latest Replay Failure Classification Dashboard",
            generated_at=generated_at,
            command_used=command_used,
            runtime_lineage_events=(
                runtime_lineage_events
                if runtime_lineage_events is not None
                else recorded_runtime_lineage_events()
            ),
        ),
        encoding="utf-8",
    )
    return out_path


def write_failure_dashboard_artifact_if_requested(
    rows: Sequence[Mapping[str, Any]],
    *,
    path: Path | str = FAILURE_DASHBOARD_LATEST_PATH,
    command_used: str | None = None,
    env: Mapping[str, str] | None = None,
    generated_at: str | None = None,
    runtime_lineage_events: Any = None,
) -> Path | None:
    """Write the dashboard only when the opt-in environment flag is enabled."""
    if not failure_dashboard_requested(env):
        return None
    return write_failure_dashboard_artifact(
        rows,
        path=path,
        command_used=command_used,
        generated_at=generated_at,
        runtime_lineage_events=runtime_lineage_events,
    )


# Session artifact writer facade ------------------------------------------

def write_requested_dashboard_artifacts(
    *,
    exitstatus: int,
    command_used: str | None = None,
    env: Mapping[str, str] | None = None,
) -> list[Path]:
    """Write all pytest-session dashboard artifacts requested by status and env."""
    written: list[Path] = []

    if exitstatus != 0:
        failure_report = write_protected_replay_failure_report_if_present(command_used=command_used)
        if failure_report is not None:
            written.append(failure_report)

    if exitstatus == 0 and rerun_drift_scorecard_requested(env):
        scorecards = recorded_rerun_drift_scorecards()
        written.extend(
            write_rerun_drift_scorecard_artifacts(
                scorecards[-1] if scorecards else None,
                command_used=command_used,
            )
        )

    if exitstatus == 0 and long_session_stability_scorecard_requested(env):
        stability_scorecards = recorded_long_session_stability_scorecards()
        written.extend(
            write_long_session_stability_scorecard_artifacts(
                stability_scorecards[-1] if stability_scorecards else None,
                command_used=command_used,
            )
        )

    if failure_dashboard_requested(env):
        written.append(
            write_failure_dashboard_artifact(
                recorded_failure_dashboard_rows(),
                command_used=command_used,
            )
        )

    return written


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
    write_owner_drift_hotspot_artifacts(
        collected_hotspot_classifications(),
        scorecard_history=history_scorecards,
        command_used=command_used,
        generated_at=generated_at,
    )
    write_owner_drift_trend_artifacts(
        history_scorecards,
        command_used=command_used,
        generated_at=generated_at,
    )
    write_owner_drift_risk_artifacts(
        collected_hotspot_classifications(),
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


def render_protected_replay_failure_report(
    rows: Sequence[Mapping[str, Any]],
    *,
    path: Path | str = PROTECTED_REPLAY_FAILURE_REPORT_PATH,
    command_used: str | None = None,
    generated_at: str | None = None,
    runtime_lineage_events: Any = None,
) -> str:
    """Render the canonical report for classified protected replay failures."""
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command_s = command_used if command_used is not None else " ".join(sys.argv)
    artifact_path = str(path).replace("\\", "/")
    ordered_rows = sorted(
        rows,
        key=lambda item: (
            str(item.get("scenario_id") or ""),
            str(item.get("test_node_id") or ""),
            int(item.get("turn_index") or 0),
            str(item.get("field_path") or ""),
        ),
    )
    has_replay_identity = any(
        row.get("scenario_id")
        or row.get("source_path")
        or row.get("branch_id")
        or row.get("turn_id")
        or row.get("turn_index") is not None
        for row in ordered_rows
    )
    lines = [
        "# Protected Replay Failure Report",
        "",
        "## Run Summary",
        "",
        f"- Status: `failed`",
        f"- Command: `{command_s or 'unavailable'}`",
        f"- Generated at: `{generated_at_s}`",
        f"- Artifact location: `{artifact_path}`",
        f"- Classified failures: `{len(ordered_rows)}`",
    ]
    if has_replay_identity:
        lines.extend(
            [
                "",
                "## Failure Locator",
                "",
                "| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |",
                "|---|---|---|---:|---|---|---|",
            ]
        )
        for row in ordered_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(row.get("scenario_id")),
                        _cell(row.get("source_path")),
                        _cell(row.get("branch_id")),
                        _cell(row.get("turn_index")),
                        _cell(row.get("turn_id")),
                        _cell(row.get("failed_invariant")),
                        _cell(row.get("test_node_id")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Failure Table",
            "",
            "| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First | Owner Drift Bucket |",
            "|---|---|---:|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in ordered_rows:
        classification_row = {
            key: value
            for key, value in row.items()
            if key not in {"test_node_id", "failed_invariant", "source_path", "branch_id", "turn_id"}
        }
        validation_errors = failure_dashboard_row_shape_errors(classification_row)
        if validation_errors:
            raise ValueError(f"invalid protected replay failure row: {validation_errors}")
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("scenario_id")),
                    _cell(row.get("test_node_id")),
                    _cell(row.get("turn_index")),
                    _cell(row.get("failed_invariant")),
                    _cell(_drift_type(row)),
                    _cell(row.get("expected")),
                    _cell(row.get("actual")),
                    _cell(row.get("category")),
                    _cell(row.get("severity")),
                    _cell(row.get("primary_owner")),
                    _cell(row.get("secondary_owner")),
                    _cell(row.get("investigate_first")),
                    _cell(row.get("owner_drift_bucket")),
                ]
            )
            + " |"
        )
    owner_drift_counts = summarize_owner_drift_buckets(ordered_rows)
    category_counts: dict[str, int] = {}
    owner_counts: dict[str, int] = {}
    for row in ordered_rows:
        category = str(row.get("category") or "unknown")
        owner = str(row.get("primary_owner") or "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
    lines.extend(
        [
            "",
            "## Classification Summary",
            "",
            "- Categories: " + "; ".join(f"`{key}` ({value})" for key, value in sorted(category_counts.items())),
            "- Primary owners: " + "; ".join(f"`{key}` ({value})" for key, value in sorted(owner_counts.items())),
            "",
        ]
    )
    lines.extend(_owner_drift_breakdown_lines(owner_drift_counts))
    lines.extend(
        [
            "## Fallback Summary",
            "",
            "| Scenario | Final Source | Fallback Family | Temporal Frame | Opening Authorship | Opening Owner | Sealed Owner | Sanitizer Empty Owner |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in ordered_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("scenario_id")),
                    _cell(row.get("final_emitted_source")),
                    _cell(row.get("fallback_family")),
                    _cell(row.get("fallback_temporal_frame")),
                    _cell(row.get("opening_fallback_authorship_source")),
                    _cell(row.get("opening_fallback_owner_bucket")),
                    _cell(row.get("sealed_fallback_owner_bucket")),
                    _cell(row.get("sanitizer_empty_fallback_owner")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Sanitizer Summary",
            "",
            "| Scenario | Mode | Changed | Dropped | Empty Fallback | Empty Owner | Legacy Rewrite | Strict Social Owner |",
            "|---|---|---:|---:|---|---|---|---|",
        ]
    )
    for row in ordered_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("scenario_id")),
                    _cell(_first_non_none(row.get("sanitizer_lineage_mode"), row.get("sanitizer_mode"))),
                    _cell(_first_non_none(row.get("sanitizer_lineage_changed_count"), row.get("sanitizer_changed_count"))),
                    _cell(row.get("sanitizer_lineage_dropped_count")),
                    _cell(_first_non_none(row.get("sanitizer_lineage_empty_fallback_used"), row.get("sanitizer_empty_fallback_used"))),
                    _cell(row.get("sanitizer_empty_fallback_owner")),
                    _cell(row.get("sanitizer_lineage_legacy_rewrite_active")),
                    _cell(row.get("sanitizer_strict_social_prose_owner")),
                ]
            )
            + " |"
        )
    lines.extend(_runtime_lineage_markdown_lines(runtime_lineage_events))
    lines.extend(["## Reproduce Locally", "", "### Focused failing tests", ""])
    node_ids = sorted({str(row.get("test_node_id") or "").strip() for row in ordered_rows if str(row.get("test_node_id") or "").strip()})
    if node_ids:
        for node_id in node_ids:
            lines.extend(["```bash", f"python -m pytest {node_id} -q --tb=short", "```", ""])
    else:
        lines.extend(["No focused pytest node was recorded for these rows.", ""])
    lines.extend(["### Protected replay lane", "", "```bash", "python -m pytest -m golden_replay -q --tb=short", "```", ""])
    return "\n".join(lines)


def write_protected_replay_failure_report_if_present(
    rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    path: Path | str = PROTECTED_REPLAY_FAILURE_REPORT_PATH,
    command_used: str | None = None,
    generated_at: str | None = None,
    runtime_lineage_events: Any = None,
) -> Path | None:
    """Write the canonical protected replay report only when failures were recorded."""
    report_rows = list(rows) if rows is not None else recorded_protected_replay_failure_rows()
    if not report_rows:
        return None
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_protected_replay_failure_report(
            report_rows,
            path=out_path,
            command_used=command_used,
            generated_at=generated_at,
            runtime_lineage_events=(
                runtime_lineage_events
                if runtime_lineage_events is not None
                else recorded_protected_replay_runtime_lineage_events()
            ),
        ),
        encoding="utf-8",
    )
    write_owner_drift_hotspot_artifacts(
        report_rows,
        command_used=command_used,
        generated_at=generated_at,
    )
    write_owner_drift_risk_artifacts(
        report_rows,
        command_used=command_used,
        generated_at=generated_at,
        recurrence_event_metadata=protected_replay_recurrence_event_metadata(
            command_used=command_used,
            generated_at=generated_at,
            artifact_source=out_path,
        ),
    )
    return out_path


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
