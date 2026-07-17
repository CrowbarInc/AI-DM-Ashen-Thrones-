"""BZ recurrence movement reporting (test/tooling only).

Compares explicit recurrence snapshots without mutating recurrence history or
inferring BW-time state from cumulative files.
"""
from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from tests.helpers.golden_replay_trend import write_deterministic_json
from tests.helpers.replay_bug_recurrence_events import (
    RECURRENCE_EVENT_SOURCE_UNKNOWN,
    RECURRENCE_REPORT_ONLY,
    RECURRENCE_SCHEMA_VERSION,
    classify_recurrence_status,
    load_recurrence_event_log,
    normalized_recurrence_event_source,
    recurrence_owner,
)
from tests.helpers.replay_bug_recurrence_history import _protected_events_ordered

BZ_RECURRENCE_MOVEMENT_FILENAME: Final[str] = "BZ_recurrence_movement.json"
BZ_WINDOW_SUMMARY_MD: Final[str] = "BZ_protected_replay_trend_window_2.md"

COMPARISON_MODE_BASELINE_ESTABLISHMENT: Final[str] = "baseline_establishment"
COMPARISON_MODE_HISTORICAL: Final[str] = "historical_snapshot_comparison"

RECURRING_LIFECYCLE_STAGES: Final[frozenset[str]] = frozenset({"recurring", "persistent"})


def _portable_artifact_path(path: Path | str | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path).resolve()
    for parent in resolved.parents:
        if (parent / "pyproject.toml").is_file() or (parent / ".git").is_dir():
            try:
                return resolved.relative_to(parent).as_posix()
            except ValueError:
                break
    return resolved.as_posix()


def _parse_recurrence_key_parts(recurrence_key: str) -> dict[str, str]:
    key = str(recurrence_key or "").strip()
    if not key.startswith("recurrence:v1:"):
        return {
            "owner_bucket": "unknown",
            "category": "unknown",
            "field_path": "unknown",
            "investigate_first": "unknown",
        }
    parts = key.split("recurrence:v1:", 1)[1].split("|")
    while len(parts) < 4:
        parts.append("unknown")
    return {
        "owner_bucket": parts[0],
        "category": parts[1],
        "field_path": parts[2],
        "investigate_first": parts[3],
    }


def _normalized_path_token(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _lifecycle_stage_from_entry(entry: Mapping[str, Any]) -> str:
    explicit = str(entry.get("lifecycle_stage") or "").strip().lower()
    if explicit:
        return explicit
    status = classify_recurrence_status(entry)
    recurrence_status = str(entry.get("status") or entry.get("recurrence_status") or "active").strip().lower()
    if status == "retired" or recurrence_status in {"retired", "deprecated"}:
        return "retired"
    occurrence_count = int(entry.get("occurrence_count") or 0)
    if occurrence_count >= 2:
        return "recurring"
    return "emerging"


def _is_recurring_or_persistent(entry: Mapping[str, Any]) -> bool:
    stage = _lifecycle_stage_from_entry(entry)
    if stage in RECURRING_LIFECYCLE_STAGES:
        return True
    if stage in {"retired", "dormant"}:
        return False
    occurrence_count = int(entry.get("occurrence_count") or 0)
    recurrence_status = str(entry.get("recurrence_status") or entry.get("status") or "active").strip().lower()
    if recurrence_status in {"retired", "deprecated"}:
        return False
    return occurrence_count >= 2


def _event_sources_by_recurrence_key(event_log_path: Path | str | None) -> dict[str, str]:
    if event_log_path is None:
        return {}
    path = Path(event_log_path)
    if not path.is_file():
        return {}
    event_log = load_recurrence_event_log(path)
    sources: dict[str, str] = {}
    for event in _protected_events_ordered(event_log):
        key = str(event.get("recurrence_key") or "").strip()
        if not key:
            continue
        sources[key] = normalized_recurrence_event_source(event.get("event_source"))
    return sources


def _snapshot_entry_from_history_row(
    row: Mapping[str, Any],
    *,
    event_sources_by_key: Mapping[str, str],
) -> dict[str, Any]:
    key = str(row.get("recurrence_key") or "").strip()
    parsed = _parse_recurrence_key_parts(key)
    categories = row.get("categories")
    field_paths = row.get("field_paths")
    category = str(
        categories[0]
        if isinstance(categories, list) and categories
        else parsed["category"]
    )
    field_path = str(
        field_paths[0]
        if isinstance(field_paths, list) and field_paths
        else parsed["field_path"]
    )
    owner = str(row.get("owner") or recurrence_owner(row))
    investigate_first = row.get("latest_investigate_first") or parsed["investigate_first"]
    return {
        "recurrence_key": key,
        "occurrence_count": int(row.get("occurrence_count") or 0),
        "recurrence_status": str(row.get("status") or row.get("recurrence_status") or "active"),
        "lifecycle_stage": _lifecycle_stage_from_entry(row),
        "recurrence_owner": owner,
        "investigate_first": investigate_first,
        "event_source": event_sources_by_key.get(key, RECURRENCE_EVENT_SOURCE_UNKNOWN),
        "category": category,
        "field_path": field_path,
        "subject_key": f"{category}|{field_path}",
    }


def build_recurrence_snapshot(
    *,
    source_path: Path | str | None = None,
    history: Mapping[str, Any] | None = None,
    event_log_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build a deterministic recurrence snapshot from explicit history input."""
    payload: dict[str, Any] = {}
    available = False
    portable_path: str | None = None

    if history is not None:
        payload = dict(history)
        available = True
    elif source_path is not None:
        path = Path(source_path)
        if path.is_file():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, Mapping):
                payload = dict(loaded)
                available = True
                portable_path = _portable_artifact_path(path)

    recurrences = payload.get("recurrences")
    rows = [row for row in recurrences if isinstance(row, Mapping)] if isinstance(recurrences, list) else []
    event_sources_by_key = _event_sources_by_recurrence_key(event_log_path)

    entries = [
        _snapshot_entry_from_history_row(row, event_sources_by_key=event_sources_by_key)
        for row in rows
        if str(row.get("recurrence_key") or "").strip()
    ]
    entries.sort(key=lambda entry: str(entry["recurrence_key"]))

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "source_path": portable_path,
        "available": available,
        "key_count": len(entries),
        "entries": entries,
        "keys_by_recurrence_key": {entry["recurrence_key"]: entry for entry in entries},
    }


def _movement_row(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "recurrence_key": str(entry.get("recurrence_key") or ""),
        "occurrence_count": int(entry.get("occurrence_count") or 0),
        "lifecycle_stage": str(entry.get("lifecycle_stage") or ""),
        "recurrence_status": str(entry.get("recurrence_status") or ""),
        "recurrence_owner": str(entry.get("recurrence_owner") or ""),
        "investigate_first": entry.get("investigate_first"),
        "event_source": str(entry.get("event_source") or RECURRENCE_EVENT_SOURCE_UNKNOWN),
        "subject_key": str(entry.get("subject_key") or ""),
    }


def _empty_movement_payload() -> dict[str, Any]:
    empty_lists = {
        "newly_recurring": [],
        "still_recurring": [],
        "no_longer_recurring": [],
        "count_increased": [],
        "count_decreased": [],
        "unchanged_count": [],
        "owner_changed": [],
        "investigate_first_changed": [],
        "event_source_changed": [],
        "ambiguous_subjects": [],
    }
    summary = {
        "newly_recurring_count": 0,
        "still_recurring_count": 0,
        "no_longer_recurring_count": 0,
        "count_increased_count": 0,
        "count_decreased_count": 0,
        "owner_changed_count": 0,
        "investigate_first_changed_count": 0,
        "event_source_changed_count": 0,
        "ambiguous_subject_count": 0,
    }
    return {"summary": summary, "movement": empty_lists}


def _subject_groups(entries: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        subject_key = str(entry.get("subject_key") or "")
        if subject_key:
            groups[subject_key].append(dict(entry))
    return groups


def _compare_subject_movement(
    baseline_snapshot: Mapping[str, Any],
    current_snapshot: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    baseline_groups = _subject_groups(baseline_snapshot.get("entries") or ())
    current_groups = _subject_groups(current_snapshot.get("entries") or ())

    owner_changed: list[dict[str, Any]] = []
    investigate_first_changed: list[dict[str, Any]] = []
    event_source_changed: list[dict[str, Any]] = []
    ambiguous_subjects: list[dict[str, Any]] = []

    for subject_key in sorted(set(baseline_groups) | set(current_groups)):
        baseline_entries = baseline_groups.get(subject_key, [])
        current_entries = current_groups.get(subject_key, [])

        if len(baseline_entries) > 1 or len(current_entries) > 1:
            ambiguous_subjects.append(
                {
                    "subject_key": subject_key,
                    "baseline_recurrence_keys": sorted(
                        str(entry.get("recurrence_key") or "") for entry in baseline_entries
                    ),
                    "current_recurrence_keys": sorted(
                        str(entry.get("recurrence_key") or "") for entry in current_entries
                    ),
                }
            )
            continue

        if not baseline_entries or not current_entries:
            continue

        baseline_entry = baseline_entries[0]
        current_entry = current_entries[0]
        base_row = {
            "subject_key": subject_key,
            "baseline_recurrence_key": baseline_entry.get("recurrence_key"),
            "current_recurrence_key": current_entry.get("recurrence_key"),
        }

        if baseline_entry.get("recurrence_owner") != current_entry.get("recurrence_owner"):
            owner_changed.append(
                {
                    **base_row,
                    "baseline_owner": baseline_entry.get("recurrence_owner"),
                    "current_owner": current_entry.get("recurrence_owner"),
                }
            )

        baseline_investigate = _normalized_path_token(baseline_entry.get("investigate_first"))
        current_investigate = _normalized_path_token(current_entry.get("investigate_first"))
        if baseline_investigate != current_investigate:
            investigate_first_changed.append(
                {
                    **base_row,
                    "baseline_investigate_first": baseline_entry.get("investigate_first"),
                    "current_investigate_first": current_entry.get("investigate_first"),
                }
            )

        if baseline_entry.get("event_source") != current_entry.get("event_source"):
            event_source_changed.append(
                {
                    **base_row,
                    "baseline_event_source": baseline_entry.get("event_source"),
                    "current_event_source": current_entry.get("event_source"),
                }
            )

    return {
        "owner_changed": sorted(owner_changed, key=lambda row: str(row.get("subject_key") or "")),
        "investigate_first_changed": sorted(
            investigate_first_changed,
            key=lambda row: str(row.get("subject_key") or ""),
        ),
        "event_source_changed": sorted(
            event_source_changed,
            key=lambda row: str(row.get("subject_key") or ""),
        ),
        "ambiguous_subjects": sorted(
            ambiguous_subjects,
            key=lambda row: str(row.get("subject_key") or ""),
        ),
    }


def compare_recurrence_snapshots(
    baseline_snapshot: Mapping[str, Any],
    current_snapshot: Mapping[str, Any],
    *,
    comparison_mode: str = COMPARISON_MODE_HISTORICAL,
) -> dict[str, Any]:
    """Classify recurrence movement between two explicit snapshots."""
    if comparison_mode == COMPARISON_MODE_BASELINE_ESTABLISHMENT:
        return _empty_movement_payload()

    baseline_by_key = baseline_snapshot.get("keys_by_recurrence_key")
    current_by_key = current_snapshot.get("keys_by_recurrence_key")
    if not isinstance(baseline_by_key, Mapping):
        baseline_by_key = {}
    if not isinstance(current_by_key, Mapping):
        current_by_key = {}

    baseline_keys = {str(key) for key in baseline_by_key}
    current_keys = {str(key) for key in current_by_key}
    all_keys = sorted(baseline_keys | current_keys)

    newly_recurring: list[dict[str, Any]] = []
    still_recurring: list[dict[str, Any]] = []
    no_longer_recurring: list[dict[str, Any]] = []
    count_increased: list[dict[str, Any]] = []
    count_decreased: list[dict[str, Any]] = []
    unchanged_count: list[dict[str, Any]] = []

    for key in all_keys:
        baseline_entry = baseline_by_key.get(key)
        current_entry = current_by_key.get(key)

        if baseline_entry is None and current_entry is not None:
            if _is_recurring_or_persistent(current_entry):
                newly_recurring.append(_movement_row(current_entry))
            continue

        if baseline_entry is not None and current_entry is None:
            if _is_recurring_or_persistent(baseline_entry):
                no_longer_recurring.append(_movement_row(baseline_entry))
            continue

        if baseline_entry is None or current_entry is None:
            continue

        baseline_recurring = _is_recurring_or_persistent(baseline_entry)
        current_recurring = _is_recurring_or_persistent(current_entry)

        if baseline_recurring and current_recurring:
            still_recurring.append(_movement_row(current_entry))
        elif baseline_recurring and not current_recurring:
            no_longer_recurring.append(_movement_row(baseline_entry))
        elif not baseline_recurring and current_recurring:
            newly_recurring.append(_movement_row(current_entry))

        baseline_count = int(baseline_entry.get("occurrence_count") or 0)
        current_count = int(current_entry.get("occurrence_count") or 0)
        if current_count > baseline_count:
            count_increased.append(
                {
                    "recurrence_key": key,
                    "baseline_occurrence_count": baseline_count,
                    "current_occurrence_count": current_count,
                }
            )
        elif current_count < baseline_count:
            count_decreased.append(
                {
                    "recurrence_key": key,
                    "baseline_occurrence_count": baseline_count,
                    "current_occurrence_count": current_count,
                }
            )
        else:
            unchanged_count.append(
                {
                    "recurrence_key": key,
                    "occurrence_count": current_count,
                }
            )

    subject_movement = _compare_subject_movement(baseline_snapshot, current_snapshot)
    movement = {
        "newly_recurring": sorted(newly_recurring, key=lambda row: row["recurrence_key"]),
        "still_recurring": sorted(still_recurring, key=lambda row: row["recurrence_key"]),
        "no_longer_recurring": sorted(no_longer_recurring, key=lambda row: row["recurrence_key"]),
        "count_increased": sorted(count_increased, key=lambda row: row["recurrence_key"]),
        "count_decreased": sorted(count_decreased, key=lambda row: row["recurrence_key"]),
        "unchanged_count": sorted(unchanged_count, key=lambda row: row["recurrence_key"]),
        **subject_movement,
    }
    summary = {
        "newly_recurring_count": len(movement["newly_recurring"]),
        "still_recurring_count": len(movement["still_recurring"]),
        "no_longer_recurring_count": len(movement["no_longer_recurring"]),
        "count_increased_count": len(movement["count_increased"]),
        "count_decreased_count": len(movement["count_decreased"]),
        "owner_changed_count": len(movement["owner_changed"]),
        "investigate_first_changed_count": len(movement["investigate_first_changed"]),
        "event_source_changed_count": len(movement["event_source_changed"]),
        "ambiguous_subject_count": len(movement["ambiguous_subjects"]),
    }
    return {"summary": summary, "movement": movement}


def build_bz_recurrence_movement_report(
    *,
    baseline_snapshot: Mapping[str, Any] | None,
    current_snapshot: Mapping[str, Any],
    comparison_mode: str,
    baseline_path: Path | str | None,
    current_path: Path | str | None,
) -> dict[str, Any]:
    """Assemble the BZ recurrence movement artifact payload."""
    baseline_available = bool(
        baseline_snapshot
        and baseline_snapshot.get("available")
        and comparison_mode == COMPARISON_MODE_HISTORICAL
    )
    current_available = bool(current_snapshot.get("available"))

    if comparison_mode == COMPARISON_MODE_HISTORICAL and baseline_snapshot is not None:
        comparison = compare_recurrence_snapshots(
            baseline_snapshot,
            current_snapshot,
            comparison_mode=comparison_mode,
        )
    else:
        comparison = _empty_movement_payload()

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": True,
        "comparison_mode": comparison_mode,
        "baseline_path": _portable_artifact_path(baseline_path) if baseline_path else None,
        "current_path": _portable_artifact_path(current_path) if current_path else None,
        "baseline_available": baseline_available,
        "current_available": current_available,
        "summary": comparison["summary"],
        "movement": comparison["movement"],
    }


def write_bz_recurrence_movement_artifact(
    *,
    out_dir: Path,
    baseline_path: Path | str | None = None,
    current_path: Path | str | None = None,
    event_log_path: Path | str | None = None,
) -> dict[str, Any]:
    """Write BZ_recurrence_movement.json without mutating recurrence persistence files."""
    baseline_resolved = Path(baseline_path).resolve() if baseline_path is not None else None
    current_resolved = Path(current_path).resolve() if current_path is not None else None

    if baseline_resolved is not None and baseline_resolved.is_file():
        comparison_mode = COMPARISON_MODE_HISTORICAL
        baseline_snapshot = build_recurrence_snapshot(
            source_path=baseline_resolved,
            event_log_path=event_log_path,
        )
    else:
        comparison_mode = COMPARISON_MODE_BASELINE_ESTABLISHMENT
        baseline_snapshot = build_recurrence_snapshot(history={"recurrences": []})

    if current_resolved is None or not current_resolved.is_file():
        current_snapshot = build_recurrence_snapshot(history={"recurrences": []})
    else:
        current_snapshot = build_recurrence_snapshot(
            source_path=current_resolved,
            event_log_path=event_log_path,
        )

    report = build_bz_recurrence_movement_report(
        baseline_snapshot=baseline_snapshot,
        current_snapshot=current_snapshot,
        comparison_mode=comparison_mode,
        baseline_path=baseline_resolved,
        current_path=current_resolved,
    )
    write_deterministic_json(out_dir / BZ_RECURRENCE_MOVEMENT_FILENAME, report)
    return report


RECURRENCE_SUMMARY_TO_MOVEMENT: Final[dict[str, str]] = {
    "newly_recurring_count": "newly_recurring",
    "still_recurring_count": "still_recurring",
    "no_longer_recurring_count": "no_longer_recurring",
    "count_increased_count": "count_increased",
    "count_decreased_count": "count_decreased",
    "owner_changed_count": "owner_changed",
    "investigate_first_changed_count": "investigate_first_changed",
    "event_source_changed_count": "event_source_changed",
    "ambiguous_subject_count": "ambiguous_subjects",
}


def recurrence_movement_summary_matches_lists(report: Mapping[str, Any]) -> bool:
    """Return True when recurrence summary counts match movement list lengths."""
    summary = report.get("summary")
    movement = report.get("movement")
    if not isinstance(summary, Mapping) or not isinstance(movement, Mapping):
        return False
    for summary_field, movement_field in RECURRENCE_SUMMARY_TO_MOVEMENT.items():
        rows = movement.get(movement_field)
        if not isinstance(rows, list):
            return False
        if int(summary.get(summary_field) or 0) != len(rows):
            return False
    return True


def render_bz_protected_replay_trend_window_2_markdown(
    *,
    replay_key_movement: Mapping[str, Any] | None,
    recurrence_movement: Mapping[str, Any] | None,
) -> str:
    """Render a concise BZ window summary for operators."""
    lines = [
        "# BZ Protected Replay Trend Window #2",
        "",
        "Report-only measurement lane comparing BW baseline run artifacts to BZ window output.",
        "",
    ]

    if isinstance(replay_key_movement, Mapping):
        summary = replay_key_movement.get("summary")
        if isinstance(summary, Mapping):
            lines.extend(
                [
                    "## Replay Key Movement",
                    "",
                    f"- Corpus match: `{replay_key_movement.get('corpus_match')}`",
                    f"- Baseline: `{replay_key_movement.get('baseline')}`",
                    f"- Current: `{replay_key_movement.get('current')}`",
                    f"- Active keys: `{summary.get('active_key_count')}`",
                    f"- New keys: `{summary.get('new_key_count')}`",
                    f"- Retired keys: `{summary.get('retired_key_count')}`",
                    f"- Unchanged keys: `{summary.get('unchanged_key_count')}`",
                    "",
                ]
            )

    if isinstance(recurrence_movement, Mapping):
        summary = recurrence_movement.get("summary")
        if isinstance(summary, Mapping):
            lines.extend(
                [
                    "## Recurrence Movement",
                    "",
                    f"- Comparison mode: `{recurrence_movement.get('comparison_mode')}`",
                    f"- Baseline available: `{recurrence_movement.get('baseline_available')}`",
                    f"- Current available: `{recurrence_movement.get('current_available')}`",
                    f"- Current snapshot: `{recurrence_movement.get('current_path')}`",
                    f"- Newly recurring: `{summary.get('newly_recurring_count')}`",
                    f"- Still recurring: `{summary.get('still_recurring_count')}`",
                    f"- No longer recurring: `{summary.get('no_longer_recurring_count')}`",
                    f"- Count increased: `{summary.get('count_increased_count')}`",
                    f"- Count decreased: `{summary.get('count_decreased_count')}`",
                    "",
                    "## Regression Recurrence Rate Evidence",
                    "",
                    "Use the explicit current recurrence snapshot at "
                    "`artifacts/golden_replay/bug_recurrence_history.json` "
                    "(`protected_replay_regression_recurrence_rate`) to score Regression Recurrence Rate. "
                    "BZ recurrence movement does not infer BW-time recurrence state when "
                    "`comparison_mode` is `baseline_establishment`.",
                    "",
                ]
            )

    lines.extend(
        [
            "## Success Criteria",
            "",
            "- Measurement only; no replay behavior changes.",
            "- BW artifacts under `artifacts/golden_replay/trend_window/` remain immutable inputs.",
            "- BZ artifacts are written only under `artifacts/golden_replay/trend_window_2/`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_bz_window_summary_markdown(
    *,
    out_dir: Path,
    replay_key_movement: Mapping[str, Any] | None,
    recurrence_movement: Mapping[str, Any] | None,
) -> None:
    """Write BZ_protected_replay_trend_window_2.md beside BZ JSON reports."""
    text = render_bz_protected_replay_trend_window_2_markdown(
        replay_key_movement=replay_key_movement,
        recurrence_movement=recurrence_movement,
    )
    (out_dir / BZ_WINDOW_SUMMARY_MD).write_text(text, encoding="utf-8")
