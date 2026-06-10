"""Report-only recurrence keys for replay bug-class diagnostics.

This helper derives stable identities from existing replay classification rows.
It does not read or write history, change governance decisions, or affect replay
pass/fail behavior.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS


RECURRENCE_SCHEMA_VERSION = 1
RECURRENCE_REPORT_ONLY = True
RECURRENCE_ADVISORY_ONLY = True
DEFAULT_OWNER_DRIFT_BUCKET = "replay_drift_unclassified"
DEFAULT_RECURRENCE_STATUS = "active"
ALLOWED_RECURRENCE_STATUSES: frozenset[str] = frozenset({"active", "retired"})
SUMMARY_RECURRENCE_STATUSES: frozenset[str] = frozenset({"active", "retired", "watch"})


def _normalized_token(value: Any, *, default: str = "unknown") -> str:
    text = str(value or "").strip().replace("\\", "/").lower()
    return text if text else default


def _owner_bucket(row: Mapping[str, Any] | None) -> str:
    value = _normalized_token((row or {}).get("owner_drift_bucket"), default=DEFAULT_OWNER_DRIFT_BUCKET)
    return value if value in ALLOWED_OWNER_DRIFT_BUCKETS else DEFAULT_OWNER_DRIFT_BUCKET


def build_recurrence_key(row: Mapping[str, Any] | None) -> str:
    """Return a deterministic recurrence key from existing classification fields."""
    source = row if isinstance(row, Mapping) else {}
    parts = (
        _owner_bucket(source),
        _normalized_token(source.get("category")),
        _normalized_token(source.get("field_path")),
        _normalized_token(source.get("investigate_first")),
    )
    return "recurrence:v1:" + "|".join(parts)


def recurrence_owner(row: Mapping[str, Any] | None) -> str:
    """Return the best existing owner signal for a recurrence row."""
    source = row if isinstance(row, Mapping) else {}
    primary_owner = _normalized_token(source.get("primary_owner"), default="")
    if primary_owner:
        return primary_owner
    return _owner_bucket(source)


def recurrence_status(row: Mapping[str, Any] | None) -> str:
    """Infer active/retired recurrence status when present, otherwise active."""
    source = row if isinstance(row, Mapping) else {}
    for field in ("recurrence_status", "status", "classification_status"):
        status = _normalized_token(source.get(field), default="")
        if status in ALLOWED_RECURRENCE_STATUSES:
            return status
    return DEFAULT_RECURRENCE_STATUS


def _input_status(row: Mapping[str, Any] | None) -> str | None:
    source = row if isinstance(row, Mapping) else {}
    for field in ("input_status", "status", "classification_status", "recurrence_status"):
        status = _normalized_token(source.get(field), default="")
        if status:
            return status
    return None


def classify_recurrence_status(entry: Mapping[str, Any] | None) -> str:
    """Classify recurrence summary status without changing governance behavior."""
    source = entry if isinstance(entry, Mapping) else {}
    explicit_statuses = {
        _normalized_token(source.get("status"), default=""),
        _normalized_token(source.get("latest_input_status"), default=""),
        _normalized_token(source.get("recurrence_status"), default=""),
    }
    if explicit_statuses & {"retired", "deprecated"}:
        return "retired"
    occurrence_count = int(source.get("occurrence_count") or 0)
    latest_status = _normalized_token(source.get("status"), default=DEFAULT_RECURRENCE_STATUS)
    if occurrence_count >= 2 and latest_status == "active":
        return "active"
    return "watch"


def recurrence_rows(classifications: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    """Project replay classifications into report-only recurrence rows."""
    rows: list[dict[str, Any]] = []
    for row in classifications or ():
        if not isinstance(row, Mapping):
            continue
        owner_bucket = _owner_bucket(row)
        rows.append(
            {
                "schema_version": RECURRENCE_SCHEMA_VERSION,
                "report_only": RECURRENCE_REPORT_ONLY,
                "advisory_only": RECURRENCE_ADVISORY_ONLY,
                "recurrence_key": build_recurrence_key(row),
                "recurrence_owner": recurrence_owner(row),
                "recurrence_status": recurrence_status(row),
                "input_status": _input_status(row),
                "scenario_id": row.get("scenario_id"),
                "turn_index": row.get("turn_index"),
                "category": row.get("category"),
                "primary_owner": row.get("primary_owner"),
                "owner_drift_bucket": owner_bucket,
                "field_path": row.get("field_path"),
                "investigate_first": row.get("investigate_first"),
            }
        )
    return rows


def _sorted_strings(values: set[str]) -> list[str]:
    return sorted(value for value in values if value)


def aggregate_recurrence_history(rows: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    """Aggregate report-only recurrence rows by stable recurrence key."""
    buckets: dict[str, dict[str, Any]] = {}
    total_rows = 0
    for index, row in enumerate(rows or ()):
        if not isinstance(row, Mapping):
            continue
        total_rows += 1
        key = str(row.get("recurrence_key") or build_recurrence_key(row)).strip()
        if not key:
            continue
        bucket = buckets.setdefault(
            key,
            {
                "recurrence_key": key,
                "occurrence_count": 0,
                "first_seen_index": index,
                "last_seen_index": index,
                "owner": recurrence_owner(row),
                "status": recurrence_status(row),
                "latest_input_status": _input_status(row),
                "_categories": set(),
                "_field_paths": set(),
                "_affected_scenarios": set(),
                "latest_investigate_first": row.get("investigate_first"),
            },
        )
        bucket["occurrence_count"] += 1
        bucket["last_seen_index"] = index
        bucket["owner"] = recurrence_owner(row)
        bucket["status"] = recurrence_status(row)
        bucket["latest_input_status"] = _input_status(row)
        bucket["latest_investigate_first"] = row.get("investigate_first")
        category = _normalized_token(row.get("category"), default="")
        field_path = _normalized_token(row.get("field_path"), default="")
        scenario_id = str(row.get("scenario_id") or "").strip()
        if category:
            bucket["_categories"].add(category)
        if field_path:
            bucket["_field_paths"].add(field_path)
        if scenario_id:
            bucket["_affected_scenarios"].add(scenario_id)

    recurrence_entries: list[dict[str, Any]] = []
    for bucket in buckets.values():
        recurrence_entries.append(
            {
                "recurrence_key": bucket["recurrence_key"],
                "occurrence_count": bucket["occurrence_count"],
                "first_seen_index": bucket["first_seen_index"],
                "last_seen_index": bucket["last_seen_index"],
                "owner": bucket["owner"],
                "status": bucket["status"],
                "latest_input_status": bucket["latest_input_status"],
                "categories": _sorted_strings(bucket["_categories"]),
                "field_paths": _sorted_strings(bucket["_field_paths"]),
                "affected_scenarios": _sorted_strings(bucket["_affected_scenarios"]),
                "latest_investigate_first": bucket["latest_investigate_first"],
            }
        )

    recurrence_entries.sort(
        key=lambda entry: (
            int(entry["first_seen_index"]),
            str(entry["recurrence_key"]),
        )
    )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "total_rows": total_rows,
        "unique_recurrence_count": len(recurrence_entries),
        "recurrences": recurrence_entries,
    }


def build_recurrence_summary(history: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Return recurrence entries ordered by frequency, then first seen index."""
    source = history if isinstance(history, Mapping) else {}
    recurrences = source.get("recurrences")
    if not isinstance(recurrences, list):
        return []
    rows = [dict(row) for row in recurrences if isinstance(row, Mapping)]
    for row in rows:
        row["status"] = classify_recurrence_status(row)
    return sorted(
        rows,
        key=lambda row: (
            -int(row.get("occurrence_count") or 0),
            int(row.get("first_seen_index") or 0),
            str(row.get("recurrence_key") or ""),
        ),
    )
