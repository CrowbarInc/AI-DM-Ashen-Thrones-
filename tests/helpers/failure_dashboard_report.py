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
    failure_dashboard_row_shape_errors,
    known_failure_categories,
)
from tests.helpers.golden_replay_projection import protected_observation_field_paths
from tests.helpers.runtime_lineage_reporting import (
    build_runtime_lineage_summary,
    runtime_lineage_markdown_lines as _runtime_lineage_markdown_lines,
)

# Cycle T3: dashboard reporting consumes projection/sync surfaces instead of
# re-enumerating protected replay field paths or failure categories inline.
REPLAY_PROTECTED_FIELD_PATHS = protected_observation_field_paths()
KNOWN_FAILURE_CATEGORIES = known_failure_categories()

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
)


def expected_failure_dashboard_columns() -> tuple[str, ...]:
    """Return markdown table column headers for the main failure dashboard table."""
    return FAILURE_DASHBOARD_TABLE_COLUMNS


def _failure_dashboard_table_header() -> str:
    return "| " + " | ".join(FAILURE_DASHBOARD_TABLE_COLUMNS) + " |"

FAILURE_DASHBOARD_ENV_VAR = "ASHEN_WRITE_FAILURE_DASHBOARD"
RERUN_DRIFT_SCORECARD_ENV_VAR = "ASHEN_WRITE_RERUN_DRIFT_SCORECARD"
FAILURE_DASHBOARD_LATEST_PATH = Path("audits/failure_dashboard_latest.md")
PROTECTED_REPLAY_FAILURE_REPORT_PATH = Path("artifacts/golden_replay/replay_failure_report.md")
RERUN_DRIFT_SCORECARD_JSON_PATH = Path("artifacts/golden_replay/rerun_drift_scorecard.json")
RERUN_DRIFT_SCORECARD_MARKDOWN_PATH = Path("artifacts/golden_replay/rerun_drift_scorecard.md")
_RECORDED_FAILURE_DASHBOARD_ROWS: list[Mapping[str, Any]] = []
_RECORDED_RUNTIME_LINEAGE_EVENTS: list[dict[str, Any]] = []
_RECORDED_PROTECTED_REPLAY_FAILURE_ROWS: list[Mapping[str, Any]] = []
_RECORDED_PROTECTED_REPLAY_RUNTIME_LINEAGE_EVENTS: list[dict[str, Any]] = []
_RECORDED_RERUN_DRIFT_SCORECARDS: list[Mapping[str, Any]] = []


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
    parts: list[str] = []
    if row.get("prepared_emission_owner") == "upstream_prepared_emission":
        if row.get("upstream_prepared_emission_valid") is False:
            reason = row.get("upstream_prepared_emission_reject_reason") or "unknown"
            parts.append(f"prepared_emission=rejected reason={reason}")
        else:
            valid = row.get("upstream_prepared_emission_valid")
            source = row.get("upstream_prepared_emission_source") or "unknown"
            parts.append(f"prepared_emission=used valid={valid} source={source}")
    evidence_keys = (
        ("sublayer", "emission_sublayer"),
        ("repair", "repair_kind"),
        ("lineage", "final_emission_mutation_lineage"),
        ("opening_authorship", "opening_fallback_authorship_source"),
        ("opening_owner", "opening_fallback_owner_bucket"),
        ("fallback_selection_owner", "fallback_selection_owner"),
        ("fallback_content_owner", "fallback_content_owner"),
        ("sealed_owner", "sealed_fallback_owner_bucket"),
        ("visibility_owner", "visibility_fallback_owner_bucket"),
        ("visibility_replaced", "visibility_replacement_applied"),
        ("visibility_pool", "visibility_fallback_pool"),
        ("visibility_kind", "visibility_fallback_kind"),
        ("mutation", "mutation_source"),
        ("missing", "missing_source_kind"),
        ("sanitizer_mode", "sanitizer_mode"),
        ("sanitizer_events", "sanitizer_event_count"),
        ("sanitizer_changed", "sanitizer_changed_count"),
        ("sanitizer_empty", "sanitizer_empty_fallback_used"),
        ("sanitizer_empty_source", "sanitizer_empty_fallback_source"),
        ("sanitizer_empty_owner", "sanitizer_empty_fallback_owner"),
        ("sanitizer_lineage_mode", "sanitizer_lineage_mode"),
        ("sanitizer_lineage_changed", "sanitizer_lineage_changed_count"),
        ("sanitizer_lineage_dropped", "sanitizer_lineage_dropped_count"),
        ("sanitizer_lineage_empty", "sanitizer_lineage_empty_fallback_used"),
        ("sanitizer_lineage_legacy", "sanitizer_lineage_legacy_rewrite_active"),
        ("strict_social_fallback", "sanitizer_strict_social_fallback_used"),
        ("strict_social_selection_owner", "sanitizer_strict_social_selection_owner"),
        ("strict_social_prose_owner", "sanitizer_strict_social_prose_owner"),
        ("strict_social_source", "sanitizer_strict_social_source"),
    )
    for label, key in evidence_keys:
        value = row.get(key)
        if value is None or value == "":
            continue
        if key == "final_emission_mutation_lineage" and isinstance(value, list):
            value = ">".join(str(item) for item in value if str(item).strip())
            if not value:
                continue
        if key == "sanitizer_lineage_legacy_rewrite_active" and value is True:
            value = "legacy_diagnostic"
        parts.append(f"{label}={value}")
    return "; ".join(parts) or "none"


def failure_dashboard_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return whether replay classification rows should be recorded/written."""
    env_map = env if env is not None else os.environ
    return str(env_map.get(FAILURE_DASHBOARD_ENV_VAR) or "").strip().lower() in {"1", "true", "yes", "on"}


def rerun_drift_scorecard_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return whether successful rerun drift diagnostics should be written."""
    env_map = env if env is not None else os.environ
    return str(env_map.get(RERUN_DRIFT_SCORECARD_ENV_VAR) or "").strip().lower() in {"1", "true", "yes", "on"}


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
            "|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                ]
            )
            + " |"
        )
    lines.append("")
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
            "| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First |",
            "|---|---|---:|---|---|---|---|---|---|---|---|---|",
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
                ]
            )
            + " |"
        )
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
    return out_path
