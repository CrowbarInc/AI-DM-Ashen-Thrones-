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
    BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH,
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
    write_bug_recurrence_artifact_set,
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
    side_effect_artifact_root: Path | str | None = None,
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
    side_effect_root = Path(side_effect_artifact_root) if side_effect_artifact_root is not None else None
    write_owner_drift_hotspot_artifacts(
        report_rows,
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
        command_used=command_used,
        generated_at=generated_at,
    )
    write_owner_drift_risk_artifacts(
        report_rows,
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
        recurrence_event_log_path=(
            side_effect_root / BUG_RECURRENCE_EVENT_LOG_JSON_PATH.name
            if side_effect_root is not None
            else None
        ),
        recurrence_session_diagnostic_event_log_path=(
            side_effect_root / BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH.name
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
        command_used=command_used,
        generated_at=generated_at,
        recurrence_event_metadata=protected_replay_recurrence_event_metadata(
            command_used=command_used,
            generated_at=generated_at,
            artifact_source=out_path,
        ),
    )
    return out_path


# Report assertion helpers (CO1) ----------------------------------------------

_PROTECTED_REPLAY_FAILURE_REPORT_TITLE = "# Protected Replay Failure Report"
_FAILURE_LOCATOR_HEADER = "## Failure Locator"
_FAILURE_LOCATOR_TABLE_HEADER = (
    "| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |"
)
_OWNER_DRIFT_BREAKDOWN_HEADER = "## Owner Drift Breakdown"
_OWNER_DRIFT_BUCKET_COLUMN = "| Owner Drift Bucket |"
_SANITIZER_SUMMARY_HEADER = "## Sanitizer Summary"
_RUNTIME_LINEAGE_SUMMARY_HEADER = "## Runtime Lineage Summary"
_FOCUSED_FAILING_TESTS_HEADER = "### Focused failing tests"
_PROTECTED_REPLAY_LANE_HEADER = "### Protected replay lane"
_GOLDEN_REPLAY_COMMAND = "python -m pytest -m golden_replay -q --tb=short"

_RERUN_DRIFT_SCORECARD_TITLE = "# Golden Rerun Drift Scorecard"
_OWNER_DRIFT_SUMMARY_HEADER = "## Owner Drift Summary"
_SEMANTIC_DELTA_FREQUENCY_HEADER = "## Semantic Delta Frequency"
_RERUN_DRIFT_TURN_TABLE_HEADER = (
    "| Turn | Previous Turn ID | Current Turn ID | Drift Fields | Details |"
)

_BUG_RECURRENCE_HISTORY_TITLE = "# Bug-Class Recurrence History"
_REGRESSION_RECURRENCE_RATE_HEADER = "## Regression Recurrence Rate"
_RECURRENCE_EMPTY_STATE = "No recurrence history recorded."


def _assert_report_contains(report: str, *needles: str) -> None:
    for needle in needles:
        assert needle in report, f"expected {needle!r} in report"


def assert_report_sections_present(
    report: str,
    *,
    title: str | None = None,
    failure_locator: bool = False,
    owner_drift_breakdown: bool = False,
    sanitizer_summary: bool = False,
    lineage_summary: bool = False,
    focused_failing_tests: bool = False,
    protected_replay_lane: bool = False,
    command_guidance: bool = False,
) -> None:
    """Assert canonical protected replay failure report section headers are present."""
    if title is not None:
        _assert_report_contains(report, title)
    if failure_locator:
        assert_report_has_failure_locator(report)
    if owner_drift_breakdown:
        _assert_report_contains(report, _OWNER_DRIFT_BREAKDOWN_HEADER, _OWNER_DRIFT_BUCKET_COLUMN)
    if sanitizer_summary:
        _assert_report_contains(report, _SANITIZER_SUMMARY_HEADER)
    if lineage_summary:
        assert_report_has_lineage_summary(report)
    if focused_failing_tests:
        _assert_report_contains(report, _FOCUSED_FAILING_TESTS_HEADER)
    if protected_replay_lane:
        _assert_report_contains(report, _PROTECTED_REPLAY_LANE_HEADER)
    if command_guidance:
        assert_report_has_command_guidance(report)


def assert_report_has_failure_locator(
    report: str,
    *,
    table_row: str | None = None,
) -> None:
    """Assert the failure locator section and table header are present."""
    _assert_report_contains(report, _FAILURE_LOCATOR_HEADER, _FAILURE_LOCATOR_TABLE_HEADER)
    if table_row is not None:
        _assert_report_contains(report, table_row)


def assert_report_has_owner_drift(
    report: str,
    *,
    bucket: str | None = None,
    breakdown: bool = False,
    summary: bool = False,
    empty_summary: bool = False,
    summary_row: str | None = None,
) -> None:
    """Assert owner drift breakdown or rerun scorecard summary semantics."""
    if breakdown:
        _assert_report_contains(report, _OWNER_DRIFT_BREAKDOWN_HEADER, _OWNER_DRIFT_BUCKET_COLUMN)
    if summary:
        _assert_report_contains(report, _OWNER_DRIFT_SUMMARY_HEADER)
        if empty_summary:
            _assert_report_contains(report, "No owner drift classifications.")
        if summary_row is not None:
            _assert_report_contains(report, summary_row)
    if bucket is not None:
        _assert_report_contains(report, bucket)


def assert_report_has_command_guidance(report: str) -> None:
    """Assert protected replay lane pytest command guidance is present."""
    _assert_report_contains(report, _GOLDEN_REPLAY_COMMAND)


def assert_report_has_lineage_summary(report: str) -> None:
    """Assert runtime lineage summary section is present."""
    _assert_report_contains(report, _RUNTIME_LINEAGE_SUMMARY_HEADER)


def assert_report_has_rerun_scorecard_summary(
    report: str,
    *,
    turns_compared: int | None = None,
    speaker_deltas: int | None = None,
    route_deltas: int | None = None,
    fallback_deltas: int | None = None,
    text_fingerprint_deltas: int | None = None,
    runtime_lineage_deltas: int | None = None,
    semantic_delta_frequency_deltas: int | None = None,
    owner_drift_bucket: str | None = None,
    owner_drift_summary_row: str | None = None,
    empty_owner_drift: bool = False,
    drift_turn_table: bool = False,
    text_hash: bool = False,
) -> None:
    """Assert rerun drift scorecard summary sections and optional delta counts."""
    _assert_report_contains(report, _RERUN_DRIFT_SCORECARD_TITLE)
    if turns_compared is not None:
        _assert_report_contains(report, f"- Total turns compared: `{turns_compared}`")
    if speaker_deltas is not None:
        _assert_report_contains(report, f"- Speaker deltas: `{speaker_deltas}`")
    if route_deltas is not None:
        _assert_report_contains(report, f"- Route deltas: `{route_deltas}`")
    if fallback_deltas is not None:
        _assert_report_contains(report, f"- Fallback deltas: `{fallback_deltas}`")
    if text_fingerprint_deltas is not None:
        _assert_report_contains(report, f"- Text fingerprint deltas: `{text_fingerprint_deltas}`")
    if runtime_lineage_deltas is not None:
        _assert_report_contains(report, f"- Runtime-lineage deltas: `{runtime_lineage_deltas}`")
    if semantic_delta_frequency_deltas is not None:
        _assert_report_contains(
            report,
            _SEMANTIC_DELTA_FREQUENCY_HEADER,
            f"- Semantic delta frequency deltas: `{semantic_delta_frequency_deltas}`",
        )
    if owner_drift_bucket is not None or owner_drift_summary_row is not None or empty_owner_drift:
        assert_report_has_owner_drift(
            report,
            bucket=owner_drift_bucket,
            summary=True,
            empty_summary=empty_owner_drift,
            summary_row=owner_drift_summary_row,
        )
    if drift_turn_table:
        _assert_report_contains(report, _RERUN_DRIFT_TURN_TABLE_HEADER)
    if text_hash:
        _assert_report_contains(report, "text_hash")


def assert_report_has_recurrence_summary(
    report: str,
    *,
    empty: bool = False,
    total_keys: int | None = None,
    total_events: int | None = None,
    regression_rate: str | None = None,
    advisory_only: bool = False,
    report_only: bool = False,
    status_markers: tuple[str, ...] = (),
) -> None:
    """Assert bug-class recurrence history header and summary semantics."""
    _assert_report_contains(report, _BUG_RECURRENCE_HISTORY_TITLE)
    if empty:
        if total_keys is not None:
            _assert_report_contains(report, f"- Total recurrence keys: `{total_keys}`")
        if total_events is not None:
            _assert_report_contains(report, f"- Total recurrence events: `{total_events}`")
        _assert_report_contains(
            report,
            _REGRESSION_RECURRENCE_RATE_HEADER,
            "does not gate protected replay.",
            _RECURRENCE_EMPTY_STATE,
        )
    if regression_rate is not None:
        _assert_report_contains(report, _REGRESSION_RECURRENCE_RATE_HEADER, regression_rate)
    if report_only:
        _assert_report_contains(report, "- Report only: `true`")
    if advisory_only:
        _assert_report_contains(report, "- Advisory only: `true`")
    for marker in status_markers:
        _assert_report_contains(report, f" | {marker} | ")


def assert_recurrence_report_section(
    report: str,
    section: str,
    *required_substrings: str,
) -> None:
    """Assert a recurrence report section header and required detail substrings."""
    _assert_report_contains(report, section, *required_substrings)


def assert_dashboard_recurrence_sections(
    report: str,
    payload: Mapping[str, Any] | None,
    *,
    section: str,
    required_substrings: tuple[str, ...] = (),
    summary_key: str | None = None,
    protected_replay_only: bool | None = True,
    schema_version: int | None = None,
) -> None:
    """Assert a bug-recurrence markdown section and optional payload summary scope."""
    assert_recurrence_report_section(report, section, *required_substrings)
    if summary_key is None:
        return
    assert payload is not None, "payload is required when summary_key is set"
    assert_recurrence_payload_summary_scope(
        payload,
        summary_key,
        protected_replay_only=protected_replay_only,
        schema_version=schema_version,
    )


def assert_dashboard_recurrence_payload(
    payload: Mapping[str, Any],
    *,
    required_keys: tuple[str, ...] = (),
    schema_version: int | None = None,
    report_only: bool | None = None,
    unique_recurrence_count: int | None = None,
    regression_rate_metric: str | None = None,
    summary_key: str | None = None,
    summary_schema_version: int | None = None,
    summary_protected_replay_only: bool | None = None,
) -> None:
    """Assert recurrence history JSON contract fields and optional embedded summary scope."""
    assert_recurrence_history_payload_shape(
        payload,
        schema_version=schema_version,
        report_only=report_only,
        unique_recurrence_count=unique_recurrence_count,
        required_keys=required_keys,
        regression_rate_metric=regression_rate_metric,
    )
    if summary_key is not None:
        assert_recurrence_payload_summary_scope(
            payload,
            summary_key,
            schema_version=summary_schema_version,
            protected_replay_only=summary_protected_replay_only,
        )


# Long-session replay summary assertion helpers (CO2) -------------------------

_LONG_SESSION_TURN_TABLE_HEADER = (
    "| Turn | Route | Speaker | Fallback | Owner | Mutation | Unavailable | Lineage |"
)


def _assert_report_lacks(report: str, *needles: str) -> None:
    for needle in needles:
        assert needle not in report, f"expected {needle!r} not in report"


def _format_report_mapping(value: Mapping[str, Any] | str) -> str:
    return value if isinstance(value, str) else str(dict(value))


def assert_long_session_summary_sections_present(
    report: str,
    *,
    title: str | None = None,
    scenario_id: str | None = None,
    turn_count: int | None = None,
    turn_table: bool = False,
) -> None:
    """Assert long-session replay summary title and structural sections."""
    if title is not None:
        _assert_report_contains(report, f"# {title}")
    if scenario_id is not None:
        _assert_report_contains(report, f"- Scenario: `{scenario_id}`")
    if turn_count is not None:
        _assert_report_contains(report, f"- Turns: `{turn_count}`")
    if turn_table:
        _assert_report_contains(report, _LONG_SESSION_TURN_TABLE_HEADER)


def assert_long_session_operator_metrics(
    report: str,
    *,
    route_changes: int | None = None,
    speaker_changes: int | None = None,
    speaker_missing: int | None = None,
    continuity_classification: str | None = None,
    fallback_total_count: int | None = None,
    fallback_lineage_kinds: Mapping[str, Any] | str | None = None,
    mutation_turn_count: int | None = None,
    response_delta_checked: int | None = None,
    response_delta_failed: int | None = None,
    response_delta_repaired: int | None = None,
    response_delta_kinds: Mapping[str, Any] | str | None = None,
    response_delta_unknown_count: int | None = None,
    echo_overlap_bands: Mapping[str, Any] | str | None = None,
    unavailable_counts: Mapping[str, Any] | str | None = None,
    lineage_recurrence_present: bool = False,
    absent_labels: tuple[str, ...] = (),
) -> None:
    """Assert operator-readable long-session replay summary metric bullets."""
    if route_changes is not None:
        _assert_report_contains(report, f"- Route changes: `{route_changes}`")
    if speaker_changes is not None and speaker_missing is not None:
        _assert_report_contains(
            report,
            f"- Speaker changes / missing: `{speaker_changes}` / `{speaker_missing}`",
        )
    if continuity_classification is not None:
        _assert_report_contains(
            report,
            f"- Continuity classification: `{continuity_classification}`",
        )
    if fallback_total_count is not None:
        _assert_report_contains(report, f"- Fallback total count: `{fallback_total_count}`")
    if fallback_lineage_kinds is not None:
        _assert_report_contains(
            report,
            f"- Fallback lineage kinds: `{_format_report_mapping(fallback_lineage_kinds)}`",
        )
    if mutation_turn_count is not None:
        _assert_report_contains(report, f"- Mutation turn count: `{mutation_turn_count}`")
    if (
        response_delta_checked is not None
        and response_delta_failed is not None
        and response_delta_repaired is not None
    ):
        _assert_report_contains(
            report,
            "- Response-delta checked / failed / repaired: "
            f"`{response_delta_checked}` / `{response_delta_failed}` / `{response_delta_repaired}`",
        )
    if response_delta_kinds is not None:
        _assert_report_contains(
            report,
            f"- Response-delta kinds: `{_format_report_mapping(response_delta_kinds)}`",
        )
    if response_delta_unknown_count is not None:
        _assert_report_contains(
            report,
            f"- Response-delta unknown count: `{response_delta_unknown_count}`",
        )
    if echo_overlap_bands is not None:
        _assert_report_contains(
            report,
            f"- Echo-overlap bands: `{_format_report_mapping(echo_overlap_bands)}`",
        )
    if unavailable_counts is not None:
        _assert_report_contains(
            report,
            f"- Unavailable counts: `{_format_report_mapping(unavailable_counts)}`",
        )
    if lineage_recurrence_present:
        _assert_report_contains(report, "- Lineage recurrence: `[")
    if absent_labels:
        _assert_report_lacks(report, *absent_labels)


# Recurrence payload assertion helpers (CO3) ------------------------------------
# Distinct from markdown/report rendering helpers above.


def _assert_payload_value(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    assert payload.get(key) == expected, f"payload[{key!r}]: expected {expected!r}, got {payload.get(key)!r}"


def _assert_payload_has_keys(payload: Mapping[str, Any], *keys: str) -> None:
    for key in keys:
        assert key in payload, f"payload missing key {key!r}"


def assert_recurrence_payload_counts(
    payload: Mapping[str, Any],
    *,
    total_rows: int | None = None,
    unique_recurrence_count: int | None = None,
    summary_empty: bool = False,
    persistence_population: str | None = None,
) -> None:
    """Assert recurrence history aggregate row/key counts."""
    if total_rows is not None:
        _assert_payload_value(payload, "total_rows", total_rows)
    if unique_recurrence_count is not None:
        _assert_payload_value(payload, "unique_recurrence_count", unique_recurrence_count)
    if summary_empty:
        _assert_payload_value(payload, "summary", [])
    if persistence_population is not None:
        _assert_payload_value(payload, "persistence_population", persistence_population)


def assert_recurrence_payload_status(
    payload: Mapping[str, Any],
    *,
    index: int = 0,
    occurrence_count: int | None = None,
    status: str | None = None,
) -> None:
    """Assert recurrence summary entry status fields."""
    summary = payload.get("summary")
    assert isinstance(summary, list), "payload['summary'] must be a list"
    assert len(summary) > index, f"payload['summary'] missing index {index}"
    entry = summary[index]
    assert isinstance(entry, Mapping), f"payload['summary'][{index}] must be a mapping"
    if occurrence_count is not None:
        _assert_payload_value(entry, "occurrence_count", occurrence_count)
    if status is not None:
        _assert_payload_value(entry, "status", status)


def assert_recurrence_payload_regression_rate(
    payload: Mapping[str, Any],
    *,
    numerator: int | None = None,
    rate: float | None = None,
    metric: str | None = None,
) -> None:
    """Assert protected or core regression recurrence rate payload fields."""
    if metric is not None:
        regression = payload.get("regression_recurrence_rate")
        assert isinstance(regression, Mapping), "payload['regression_recurrence_rate'] must be a mapping"
        _assert_payload_value(regression, "metric", metric)
    if numerator is not None or rate is not None:
        protected_rate = payload.get("protected_replay_regression_recurrence_rate")
        assert isinstance(protected_rate, Mapping), (
            "payload['protected_replay_regression_recurrence_rate'] must be a mapping"
        )
        if numerator is not None:
            _assert_payload_value(protected_rate, "numerator", numerator)
        if rate is not None:
            _assert_payload_value(protected_rate, "rate", rate)


def assert_recurrence_payload_scoped_populations(
    payload: Mapping[str, Any],
    *,
    legacy_compatibility_only: bool = True,
) -> None:
    """Assert additive scoped recurrence population metrics remain present."""
    _assert_payload_has_keys(
        payload,
        "protected_replay_regression_recurrence_rate",
        "session_diagnostic_regression_recurrence_rate",
        "synthetic_test_artifact_regression_recurrence_rate",
        "legacy_unified_regression_recurrence_rate",
        "recurrence_rate_by_population",
    )
    by_population = payload["recurrence_rate_by_population"]
    assert isinstance(by_population, Mapping), "payload['recurrence_rate_by_population'] must be a mapping"
    for population in (
        "protected_replay",
        "session_diagnostic",
        "synthetic_test_artifact",
        "legacy_unified",
    ):
        bucket = by_population.get(population)
        assert isinstance(bucket, Mapping), f"recurrence_rate_by_population[{population!r}] must be a mapping"
        recurrence_rate = bucket.get("recurrence_rate")
        assert isinstance(recurrence_rate, Mapping), (
            f"recurrence_rate_by_population[{population!r}]['recurrence_rate'] must be a mapping"
        )
    assert by_population["protected_replay"]["health_metric"] is True
    assert by_population["session_diagnostic"]["health_metric"] is False
    assert by_population["synthetic_test_artifact"]["health_metric"] is False
    assert by_population["legacy_unified"]["health_metric"] is False
    if legacy_compatibility_only:
        assert by_population["legacy_unified"]["compatibility_only"] is True
        legacy_rate = payload["legacy_unified_regression_recurrence_rate"]
        assert isinstance(legacy_rate, Mapping)
        assert legacy_rate.get("compatibility_only") is True


def assert_recurrence_history_payload_shape(
    payload: Mapping[str, Any],
    *,
    schema_version: int | None = None,
    report_only: bool | None = None,
    unique_recurrence_count: int | None = None,
    required_keys: tuple[str, ...] = (),
    regression_rate_metric: str | None = None,
) -> None:
    """Assert core recurrence history JSON payload contract fields."""
    if schema_version is not None:
        _assert_payload_value(payload, "schema_version", schema_version)
    if report_only is not None:
        _assert_payload_value(payload, "report_only", report_only)
    if unique_recurrence_count is not None:
        _assert_payload_value(payload, "unique_recurrence_count", unique_recurrence_count)
    if required_keys:
        _assert_payload_has_keys(payload, *required_keys)
    if regression_rate_metric is not None:
        assert_recurrence_payload_regression_rate(payload, metric=regression_rate_metric)


def assert_recurrence_payload_entry(
    entry: Mapping[str, Any],
    *,
    event_source: str | None = None,
    artifact_source: str | None = None,
    test_node_id: str | None = None,
    command: str | None = None,
    recorded_at: str | None = None,
) -> None:
    """Assert one recurrence event-log entry field contract."""
    if event_source is not None:
        _assert_payload_value(entry, "event_source", event_source)
    if artifact_source is not None:
        _assert_payload_value(entry, "artifact_source", artifact_source)
    if test_node_id is not None:
        _assert_payload_value(entry, "test_node_id", test_node_id)
    if command is not None:
        _assert_payload_value(entry, "command", command)
    if recorded_at is not None:
        _assert_payload_value(entry, "recorded_at", recorded_at)


def assert_recurrence_payload_summary_scope(
    payload: Mapping[str, Any],
    summary_key: str,
    *,
    protected_replay_only: bool | None = None,
    schema_version: int | None = None,
) -> None:
    """Assert recurrence subsection summary scope metadata."""
    summary = payload.get(summary_key)
    assert isinstance(summary, Mapping), f"payload[{summary_key!r}] must be a mapping"
    if protected_replay_only is not None:
        _assert_payload_value(summary, "protected_replay_only", protected_replay_only)
    if schema_version is not None:
        _assert_payload_value(summary, "schema_version", schema_version)
