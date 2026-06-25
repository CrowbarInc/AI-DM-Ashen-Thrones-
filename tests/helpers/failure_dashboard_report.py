"""Markdown report builder for replay failure classifications."""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

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
from tests.helpers.failure_dashboard_paths import (
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
    FAILURE_DASHBOARD_ENV_VAR,
    FAILURE_DASHBOARD_LATEST_PATH,
    LONG_SESSION_STABILITY_SCORECARD_ENV_VAR,
    LONG_SESSION_STABILITY_SCORECARD_JSON_PATH,
    LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH,
    OWNER_DRIFT_HOTSPOTS_JSON_PATH,
    OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH,
    OWNER_DRIFT_LONGITUDINAL_JSON_PATH,
    OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH,
    OWNER_DRIFT_RISK_JSON_PATH,
    OWNER_DRIFT_RISK_MARKDOWN_PATH,
    OWNER_DRIFT_TRENDS_JSON_PATH,
    OWNER_DRIFT_TRENDS_MARKDOWN_PATH,
    PROTECTED_REPLAY_FAILURE_REPORT_PATH,
    RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH,
    RERUN_DRIFT_SCORECARD_ENV_VAR,
    RERUN_DRIFT_SCORECARD_JSON_PATH,
    RERUN_DRIFT_SCORECARD_MARKDOWN_PATH,
)
# CE2.6 — pytest-session artifact orchestration moved to failure_dashboard_orchestration.py;
# names below are compatibility re-exports for existing import sites.
from tests.helpers.failure_dashboard_orchestration import (
    clear_requested_artifact_recordings,
    write_requested_dashboard_artifacts,
)
# CE2.5 — stability scorecard rendering/orchestration authority moved to failure_dashboard_stability.py;
# names below are compatibility re-exports for existing import sites.
from tests.helpers.failure_dashboard_stability import (
    long_session_stability_scorecard_requested,
    render_long_session_stability_scorecard_markdown,
    write_long_session_stability_scorecard_artifacts,
    write_long_session_stability_scorecard_artifacts_if_requested,
)
# CE2.4 — drift artifact writing/orchestration authority moved to failure_dashboard_drift.py;
# names below are compatibility re-exports for existing import sites.
from tests.helpers.failure_dashboard_drift import (
    _owner_drift_breakdown_lines,
    append_owner_drift_longitudinal_markdown,
    collected_hotspot_classifications,
    rerun_drift_scorecard_requested,
    render_rerun_drift_scorecard_markdown,
    scorecards_for_longitudinal_aggregation,
    write_owner_drift_hotspot_artifacts,
    write_owner_drift_longitudinal_artifacts,
    write_owner_drift_risk_artifacts,
    write_owner_drift_trend_artifacts,
    write_rerun_drift_scorecard_artifacts,
    write_rerun_drift_scorecard_artifacts_if_requested,
)
# CE2.3 — recurrence rendering/orchestration authority moved to failure_dashboard_recurrence.py;
# names below are compatibility re-exports for existing import sites.
from tests.helpers.failure_dashboard_recurrence import (
    protected_replay_recurrence_event_metadata,
    render_bug_recurrence_history_markdown,
    write_bug_recurrence_history_artifacts,
)
# CE2.2 — session buffer authority moved to tests/helpers/failure_dashboard_session.py;
# names below are compatibility re-exports for existing import sites.
from tests.helpers.failure_dashboard_session import (
    append_protected_replay_failure_row as _append_protected_replay_failure_row,
    clear_recorded_failure_dashboard_rows,
    clear_recorded_long_session_stability_scorecards,
    clear_recorded_protected_replay_failures,
    clear_recorded_rerun_drift_scorecards,
    extend_protected_replay_runtime_lineage_events as _extend_protected_replay_runtime_lineage_events,
    record_failure_dashboard_rows,
    record_long_session_stability_scorecard,
    record_rerun_drift_scorecard,
    record_runtime_lineage_events,
    recorded_failure_dashboard_rows,
    recorded_long_session_stability_scorecards,
    recorded_protected_replay_failure_rows,
    recorded_protected_replay_runtime_lineage_events,
    recorded_rerun_drift_scorecards,
    recorded_runtime_lineage_events,
)
from tests.helpers.golden_replay_projection import protected_observation_field_paths
from tests.helpers.runtime_lineage_reporting import (
    build_runtime_lineage_summary,
    runtime_lineage_markdown_lines as _runtime_lineage_markdown_lines,
)
from tests.helpers.replay_drift_reports import summarize_owner_drift_buckets

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


# Artifact recording helpers ----------------------------------------------

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
        _append_protected_replay_failure_row(enriched)
    _extend_protected_replay_runtime_lineage_events(observed_turn.get("runtime_lineage_events"))
    return rows


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
