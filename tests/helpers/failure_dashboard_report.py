"""Markdown report builder for replay failure classifications."""
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from game.runtime_lineage_telemetry import normalize_runtime_lineage_events
from tests.helpers.failure_classifier import (
    FailureClassification,
    classify_replay_failure,
    validate_failure_classification_row,
)

FAILURE_DASHBOARD_ENV_VAR = "ASHEN_WRITE_FAILURE_DASHBOARD"
FAILURE_DASHBOARD_LATEST_PATH = Path("audits/failure_dashboard_latest.md")
_RECORDED_FAILURE_DASHBOARD_ROWS: list[Mapping[str, Any]] = []
_RECORDED_RUNTIME_LINEAGE_EVENTS: list[dict[str, Any]] = []


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


def record_failure_dashboard_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Record rows for the pytest session-level dashboard artifact."""
    _RECORDED_FAILURE_DASHBOARD_ROWS.extend(dict(row) for row in rows if isinstance(row, Mapping))


def record_runtime_lineage_events(events: Any) -> None:
    """Record separate replay lineage diagnostics without changing classification rows."""
    _RECORDED_RUNTIME_LINEAGE_EVENTS.extend(normalize_runtime_lineage_events(events)[:16])


def clear_recorded_failure_dashboard_rows() -> None:
    _RECORDED_FAILURE_DASHBOARD_ROWS.clear()
    _RECORDED_RUNTIME_LINEAGE_EVENTS.clear()


def recorded_failure_dashboard_rows() -> list[Mapping[str, Any]]:
    return list(_RECORDED_FAILURE_DASHBOARD_ROWS)


def recorded_runtime_lineage_events() -> list[dict[str, Any]]:
    return list(_RECORDED_RUNTIME_LINEAGE_EVENTS)


def build_runtime_lineage_summary(events: Any) -> dict[str, Any]:
    """Build a diagnostic-only replay lineage frequency and recurrence summary."""
    normalized = normalize_runtime_lineage_events(events)
    buckets: dict[str, dict[str, int]] = {
        "by_event_kind": {},
        "by_stage": {},
        "by_recurrence_key": {},
        "fallback_frequency": {},
        "fallback_authorship_frequency": {},
        "fallback_owner_bucket_frequency": {},
        "speaker_repair_frequency": {},
        "mutation_kind_frequency": {},
        "gate_path_frequency": {},
    }

    def _count(bucket: str, value: Any) -> None:
        if isinstance(value, str) and value.strip():
            key = value.strip()
            values = buckets[bucket]
            values[key] = values.get(key, 0) + 1

    for event in normalized:
        kind = event.get("event_kind")
        _count("by_event_kind", kind)
        _count("by_stage", event.get("stage"))
        _count("by_recurrence_key", event.get("recurrence_key"))
        if kind == "fallback_selected":
            _count("fallback_frequency", event.get("fallback_kind"))
            _count("fallback_authorship_frequency", event.get("fallback_authorship_source"))
            _count("fallback_owner_bucket_frequency", event.get("fallback_owner_bucket"))
        elif kind == "speaker_repair":
            _count("speaker_repair_frequency", event.get("repair_kind"))
        elif kind == "mutation":
            _count("mutation_kind_frequency", event.get("mutation_kind"))
        elif kind == "gate_outcome":
            _count("gate_path_frequency", event.get("gate_path"))

    recurrence = buckets["by_recurrence_key"]
    return {
        "total_events": len(normalized),
        **{key: dict(sorted(values.items())) for key, values in buckets.items()},
        "recurring_events": [
            {"recurrence_key": key, "count": count}
            for key, count in sorted(recurrence.items(), key=lambda item: (-item[1], item[0]))
            if count > 1
        ],
    }


def _runtime_lineage_markdown_lines(events: Any) -> list[str]:
    summary = build_runtime_lineage_summary(events)
    if summary["total_events"] == 0:
        return []

    def _top(bucket: str) -> str:
        values = summary[bucket]
        if not isinstance(values, Mapping) or not values:
            return "_(none)_"
        return "; ".join(f"`{key}` ({count})" for key, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:5])

    kinds = summary["by_event_kind"]
    recurring = summary["recurring_events"]
    recurring_s = (
        "; ".join(f"`{item['recurrence_key']}` ({item['count']})" for item in recurring[:5])
        if recurring
        else "_(none)_"
    )
    return [
        "",
        "## Runtime Lineage Summary",
        "",
        f"- **Total lineage events:** {summary['total_events']}",
        f"- **Fallback selected:** {kinds.get('fallback_selected', 0)}",
        f"- **Speaker repair:** {kinds.get('speaker_repair', 0)}",
        f"- **Mutation:** {kinds.get('mutation', 0)}",
        f"- **Gate outcome:** {kinds.get('gate_outcome', 0)}",
        f"- **Top recurring recurrence keys:** {recurring_s}",
        f"- **Top fallback kinds:** {_top('fallback_frequency')}",
        f"- **Top fallback authorship sources:** {_top('fallback_authorship_frequency')}",
        f"- **Top fallback owner buckets:** {_top('fallback_owner_bucket_frequency')}",
        f"- **Top repair kinds:** {_top('speaker_repair_frequency')}",
        f"- **Top mutation kinds:** {_top('mutation_kind_frequency')}",
        f"- **Top gate paths:** {_top('gate_path_frequency')}",
        "",
    ]


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
            "| Scenario | Turn | Category | Severity | Primary Owner | Secondary Owner | Investigate First | Evidence | Replay Tags | Field | Expected | Actual | Unavailable | Final Source | Fallback | Post-Gate Mutation | Mutation Flags |",
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
        validation_errors = validate_failure_classification_row(row)
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
