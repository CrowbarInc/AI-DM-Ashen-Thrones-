"""Report-only recurrence keys for replay bug-class diagnostics.

This helper derives stable identities from existing replay classification rows
and supports append-only event-log persistence for cross-run recurrence history.
It does not change governance decisions or affect replay pass/fail behavior.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS


RECURRENCE_SCHEMA_VERSION = 1
RECURRENCE_REPORT_ONLY = True
RECURRENCE_ADVISORY_ONLY = True
DEFAULT_OWNER_DRIFT_BUCKET = "replay_drift_unclassified"
DEFAULT_RECURRENCE_STATUS = "active"
DEFAULT_EVENT_SOURCE = "session"
PROTECTED_REPLAY_FAILURE_EVENT_SOURCE = "protected_replay_failure"
RECURRENCE_EVENT_SOURCE_UNKNOWN = "unknown"
RECURRENCE_EVENT_SOURCE_BUCKETS: frozenset[str] = frozenset(
    {
        PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
        DEFAULT_EVENT_SOURCE,
        RECURRENCE_EVENT_SOURCE_UNKNOWN,
    }
)
RECURRENCE_PERSISTENCE_LANE_PROTECTED = "protected_replay_history"
RECURRENCE_PERSISTENCE_LANE_SESSION_DIAGNOSTIC = "session_diagnostic_history"
GOLDEN_REPLAY_ARTIFACT_SOURCE_PREFIX = "artifacts/golden_replay/"
DEFAULT_DISALLOWED_ARTIFACT_SOURCE_SUBSTRINGS: tuple[str, ...] = (
    "codex_pytest_tmp",
    "pytest_tmp",
    "/tmp/",
    "\\tmp\\",
)
ALLOWED_RECURRENCE_STATUSES: frozenset[str] = frozenset({"active", "retired"})
SUMMARY_RECURRENCE_STATUSES: frozenset[str] = frozenset({"active", "retired", "watch"})
REGRESSION_RECURRENCE_RATE_METRIC = "regression_recurrence_rate"
REGRESSION_RECURRENCE_RATE_DEFINITION = (
    "Share of observed recurrence keys with occurrence_count >= 2 "
    "in the measured history window."
)
REGRESSION_RECURRENCE_RATE_INTERPRETATION = (
    "Initial measurable proxy for recurrence keys that became active after prior "
    "observation; refine when richer state transitions exist. Advisory and report-only; "
    "does not gate protected replay."
)


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


def normalized_recurrence_event_source(value: Any) -> str:
    """Classify recurrence event provenance into report-only source buckets."""
    text = str(value or "").strip().lower()
    if text == PROTECTED_REPLAY_FAILURE_EVENT_SOURCE:
        return PROTECTED_REPLAY_FAILURE_EVENT_SOURCE
    if text in {"", DEFAULT_EVENT_SOURCE}:
        return DEFAULT_EVENT_SOURCE
    return RECURRENCE_EVENT_SOURCE_UNKNOWN


class RecurrenceCommitWorthinessPolicy:
    """Explicit policy for routing recurrence events into committed protected history."""

    __slots__ = (
        "allowed_event_sources",
        "require_golden_replay_artifact_prefix",
        "disallow_artifact_source_substrings",
        "disallow_synthetic_drift_keys",
        "disallow_null_scenario_for_protected",
    )

    def __init__(
        self,
        *,
        allowed_event_sources: frozenset[str] | None = None,
        require_golden_replay_artifact_prefix: bool = True,
        disallow_artifact_source_substrings: tuple[str, ...] = DEFAULT_DISALLOWED_ARTIFACT_SOURCE_SUBSTRINGS,
        disallow_synthetic_drift_keys: bool = True,
        disallow_null_scenario_for_protected: bool = True,
    ) -> None:
        self.allowed_event_sources = (
            allowed_event_sources
            if allowed_event_sources is not None
            else frozenset({PROTECTED_REPLAY_FAILURE_EVENT_SOURCE})
        )
        self.require_golden_replay_artifact_prefix = require_golden_replay_artifact_prefix
        self.disallow_artifact_source_substrings = disallow_artifact_source_substrings
        self.disallow_synthetic_drift_keys = disallow_synthetic_drift_keys
        self.disallow_null_scenario_for_protected = disallow_null_scenario_for_protected


DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY = RecurrenceCommitWorthinessPolicy()
BACKFILL_PROTECTED_REPLAY_PERSISTENCE_INTENT = "backfill_protected_replay"


def _normalized_artifact_source(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def is_synthetic_drift_recurrence_key(recurrence_key: str) -> bool:
    """Return True for placeholder drift keys with unknown category/investigate_first."""
    key = str(recurrence_key or "").strip()
    return key.endswith("|unknown") and "|unknown|" in key


def is_commit_worthy_recurrence_event(
    event: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> tuple[bool, str]:
    """Return whether an event belongs in committed protected replay history."""
    active_policy = policy or DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY
    source = event if isinstance(event, Mapping) else {}
    event_source = normalized_recurrence_event_source(source.get("event_source"))
    persistence_intent = str(source.get("persistence_intent") or "").strip()
    if persistence_intent == BACKFILL_PROTECTED_REPLAY_PERSISTENCE_INTENT:
        if event_source != PROTECTED_REPLAY_FAILURE_EVENT_SOURCE:
            return False, "backfill_requires_protected_replay_failure"
        if active_policy.disallow_null_scenario_for_protected and not str(source.get("scenario_id") or "").strip():
            return False, "null_scenario_id"
        return True, "backfilled_protected_replay_history"
    if event_source == DEFAULT_EVENT_SOURCE:
        return False, "session_event_source"
    if event_source not in active_policy.allowed_event_sources:
        return False, f"unsupported_event_source:{event_source}"

    artifact_source = _normalized_artifact_source(source.get("artifact_source"))
    artifact_lower = artifact_source.lower()
    for substring in active_policy.disallow_artifact_source_substrings:
        if substring.lower() in artifact_lower:
            return False, f"ephemeral_artifact_source:{artifact_source or '(none)'}"

    if active_policy.require_golden_replay_artifact_prefix:
        if not artifact_lower.startswith(GOLDEN_REPLAY_ARTIFACT_SOURCE_PREFIX.lower()):
            return False, f"non_golden_replay_artifact_source:{artifact_source or '(none)'}"

    recurrence_key = str(source.get("recurrence_key") or build_recurrence_key(source)).strip()
    if active_policy.disallow_synthetic_drift_keys and is_synthetic_drift_recurrence_key(recurrence_key):
        return False, "synthetic_drift_recurrence_key"

    if active_policy.disallow_null_scenario_for_protected and not str(source.get("scenario_id") or "").strip():
        return False, "null_scenario_id"

    return True, "protected_replay_failure"


def classify_recurrence_event_commit_worthiness(
    events: Sequence[Mapping[str, Any]] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Split recurrence events into protected and session-diagnostic lanes with reasons."""
    active_policy = policy or DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY
    protected_events: list[dict[str, Any]] = []
    session_diagnostic_events: list[dict[str, Any]] = []
    classifications: list[dict[str, Any]] = []
    for event in events or ():
        if not isinstance(event, Mapping):
            continue
        event_copy = dict(event)
        worthy, reason = is_commit_worthy_recurrence_event(event_copy, policy=active_policy)
        lane = (
            RECURRENCE_PERSISTENCE_LANE_PROTECTED
            if worthy
            else RECURRENCE_PERSISTENCE_LANE_SESSION_DIAGNOSTIC
        )
        classifications.append(
            {
                "event_index": event_copy.get("event_index"),
                "recurrence_key": event_copy.get("recurrence_key"),
                "event_source": normalized_recurrence_event_source(event_copy.get("event_source")),
                "artifact_source": _normalized_artifact_source(event_copy.get("artifact_source")) or None,
                "scenario_id": event_copy.get("scenario_id"),
                "persistence_lane": lane,
                "commit_worthy": worthy,
                "reason": reason,
            }
        )
        if worthy:
            protected_events.append(event_copy)
        else:
            session_diagnostic_events.append(event_copy)
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_history": protected_events,
        "session_diagnostic_history": session_diagnostic_events,
        "classifications": classifications,
        "counts": {
            "total": len(classifications),
            "protected_replay_history": len(protected_events),
            "session_diagnostic_history": len(session_diagnostic_events),
        },
    }


def filter_commit_worthy_recurrence_event_log(
    event_log: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return a protected-lane view of an event log without mutating the source artifact."""
    classification = classify_recurrence_event_commit_worthiness(
        _event_log_events(event_log),
        policy=policy,
    )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": classification["protected_replay_history"],
    }


def classify_committed_recurrence_event_log(
    event_log: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Audit a committed recurrence event log without rewriting it."""
    active_policy = policy or DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY
    classification = classify_recurrence_event_commit_worthiness(
        _event_log_events(event_log),
        policy=active_policy,
    )
    synthetic_keys = sorted(
        {
            str(item.get("recurrence_key") or "")
            for item in classification["classifications"]
            if is_synthetic_drift_recurrence_key(str(item.get("recurrence_key") or ""))
        }
    )
    protected_log = filter_commit_worthy_recurrence_event_log(event_log, policy=active_policy)
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "total_events": classification["counts"]["total"],
        "events_retained_for_protected_history": classification["counts"]["protected_replay_history"],
        "events_excluded_from_protected_history": classification["counts"]["session_diagnostic_history"],
        "events_classified_as_session_noise": sum(
            1
            for item in classification["classifications"]
            if item.get("reason") == "session_event_source"
        ),
        "protected_replay_events_retained": classification["counts"]["protected_replay_history"],
        "synthetic_keys_identified": synthetic_keys,
        "classifications": classification["classifications"],
        "regression_recurrence_rate_comparison": {
            "legacy_unified": calculate_regression_recurrence_rate(event_log),
            "protected_replay_history": calculate_protected_replay_regression_recurrence_rate(
                event_log,
                policy=active_policy,
            ),
            "session_diagnostic_history": calculate_regression_recurrence_rate(
                event_log,
                event_source_filter=DEFAULT_EVENT_SOURCE,
            ),
        },
    }


def calculate_protected_replay_regression_recurrence_rate(
    event_log_or_history: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return Regression Recurrence Rate for commit-worthy protected replay history only."""
    if isinstance(event_log_or_history, Mapping) and isinstance(event_log_or_history.get("events"), list):
        protected_log = filter_commit_worthy_recurrence_event_log(event_log_or_history, policy=policy)
        metric = calculate_regression_recurrence_rate(protected_log)
    else:
        metric = calculate_regression_recurrence_rate(
            event_log_or_history,
            event_source_filter=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
        )
    metric["population"] = RECURRENCE_PERSISTENCE_LANE_PROTECTED
    return metric


def _occurrence_counts_by_recurrence_key(
    source: Mapping[str, Any],
    *,
    event_source_filter: str | None = None,
) -> dict[str, int]:
    recurrences = source.get("recurrences")
    if isinstance(recurrences, list):
        if event_source_filter is not None:
            return {}
        counts: dict[str, int] = {}
        for entry in recurrences:
            if not isinstance(entry, Mapping):
                continue
            key = str(entry.get("recurrence_key") or "").strip()
            if not key:
                continue
            counts[key] = int(entry.get("occurrence_count") or 0)
        return counts

    events = source.get("events")
    if isinstance(events, list):
        counts: dict[str, int] = {}
        ordered = sorted(
            [dict(event) for event in events if isinstance(event, Mapping)],
            key=lambda event: (
                int(event.get("event_index") or 0),
                str(event.get("recurrence_key") or ""),
            ),
        )
        for event in ordered:
            if event_source_filter is not None:
                if normalized_recurrence_event_source(event.get("event_source")) != event_source_filter:
                    continue
            key = str(event.get("recurrence_key") or build_recurrence_key(event)).strip()
            if key:
                counts[key] = counts.get(key, 0) + 1
        return counts
    return {}


def calculate_regression_recurrence_rate(
    event_log_or_history: Mapping[str, Any] | None,
    *,
    event_source_filter: str | None = None,
) -> dict[str, Any]:
    """Return report-only Regression Recurrence Rate from history or event log."""
    counts = (
        _occurrence_counts_by_recurrence_key(
            event_log_or_history,
            event_source_filter=event_source_filter,
        )
        if isinstance(event_log_or_history, Mapping)
        else {}
    )
    denominator = len(counts)
    numerator = sum(1 for count in counts.values() if count >= 2)
    rate = (numerator / denominator) if denominator else 0.0
    payload: dict[str, Any] = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "metric": REGRESSION_RECURRENCE_RATE_METRIC,
        "numerator": numerator,
        "denominator": denominator,
        "rate": rate,
        "definition": REGRESSION_RECURRENCE_RATE_DEFINITION,
        "interpretation": REGRESSION_RECURRENCE_RATE_INTERPRETATION,
    }
    if event_source_filter is not None:
        payload["event_source_filter"] = event_source_filter
    return payload


def _event_log_events(event_log: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(event_log, Mapping):
        return []
    events = event_log.get("events")
    if not isinstance(events, list):
        return []
    return [dict(event) for event in events if isinstance(event, Mapping)]


def audit_recurrence_event_log_provenance(
    event_log: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize recurrence event-log provenance and source-filtered metric distortion."""
    events = _event_log_events(event_log)
    source_distribution: dict[str, int] = {bucket: 0 for bucket in sorted(RECURRENCE_EVENT_SOURCE_BUCKETS)}
    source_keys: dict[str, set[str]] = {bucket: set() for bucket in RECURRENCE_EVENT_SOURCE_BUCKETS}
    source_first_last: dict[str, dict[str, str | None]] = {
        bucket: {"first_recorded_at": None, "last_recorded_at": None}
        for bucket in RECURRENCE_EVENT_SOURCE_BUCKETS
    }
    scenario_counts: dict[str, int] = {}
    artifact_counts: dict[str, int] = {}
    recurrence_key_counts: dict[str, int] = {}

    for event in events:
        source = normalized_recurrence_event_source(event.get("event_source"))
        source_distribution[source] = source_distribution.get(source, 0) + 1
        key = str(event.get("recurrence_key") or build_recurrence_key(event)).strip()
        if key:
            source_keys.setdefault(source, set()).add(key)
            recurrence_key_counts[key] = recurrence_key_counts.get(key, 0) + 1
        scenario = str(event.get("scenario_id") or "").strip() or "(null)"
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        artifact = str(event.get("artifact_source") or "").strip() or "(none)"
        artifact_counts[artifact] = artifact_counts.get(artifact, 0) + 1
        recorded_at = str(event.get("recorded_at") or "").strip() or None
        bounds = source_first_last.setdefault(
            source,
            {"first_recorded_at": None, "last_recorded_at": None},
        )
        if recorded_at:
            if bounds["first_recorded_at"] is None or recorded_at < str(bounds["first_recorded_at"]):
                bounds["first_recorded_at"] = recorded_at
            if bounds["last_recorded_at"] is None or recorded_at > str(bounds["last_recorded_at"]):
                bounds["last_recorded_at"] = recorded_at

    total_events = len(events)
    unique_recurrence_keys = len(recurrence_key_counts)
    rate_comparison = {
        "overall": calculate_regression_recurrence_rate(event_log),
        PROTECTED_REPLAY_FAILURE_EVENT_SOURCE: calculate_regression_recurrence_rate(
            event_log,
            event_source_filter=PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
        ),
        DEFAULT_EVENT_SOURCE: calculate_regression_recurrence_rate(
            event_log,
            event_source_filter=DEFAULT_EVENT_SOURCE,
        ),
    }
    if RECURRENCE_EVENT_SOURCE_UNKNOWN in source_distribution:
        rate_comparison[RECURRENCE_EVENT_SOURCE_UNKNOWN] = calculate_regression_recurrence_rate(
            event_log,
            event_source_filter=RECURRENCE_EVENT_SOURCE_UNKNOWN,
        )

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "total_events": total_events,
        "unique_recurrence_keys": unique_recurrence_keys,
        "event_source_distribution": source_distribution,
        "unique_recurrence_keys_by_source": {
            source: len(keys) for source, keys in sorted(source_keys.items())
        },
        "source_buckets": {
            source: {
                "event_count": source_distribution.get(source, 0),
                "unique_recurrence_keys": len(source_keys.get(source, set())),
                "first_recorded_at": source_first_last.get(source, {}).get("first_recorded_at"),
                "last_recorded_at": source_first_last.get(source, {}).get("last_recorded_at"),
            }
            for source in sorted(RECURRENCE_EVENT_SOURCE_BUCKETS)
        },
        "scenario_id_distribution": dict(sorted(scenario_counts.items())),
        "artifact_source_distribution": dict(sorted(artifact_counts.items())),
        "recurrence_key_event_counts": dict(sorted(recurrence_key_counts.items())),
        "regression_recurrence_rate_comparison": rate_comparison,
    }


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
    history = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "total_rows": total_rows,
        "unique_recurrence_count": len(recurrence_entries),
        "recurrences": recurrence_entries,
    }
    history["regression_recurrence_rate"] = calculate_regression_recurrence_rate(history)
    return history


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


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _non_empty_metadata_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def normalize_recurrence_event_metadata(
    metadata: Mapping[str, Any] | None = None,
    *,
    event_source: str | None = None,
    recorded_at: str | None = None,
    test_node_id: str | None = None,
    command: str | None = None,
    run_id: str | None = None,
    artifact_source: str | None = None,
    persistence_intent: str | None = None,
) -> dict[str, Any]:
    """Normalize optional recurrence event metadata, omitting empty values."""
    merged: dict[str, Any] = {}
    if isinstance(metadata, Mapping):
        merged.update(metadata)
    for key, value in (
        ("event_source", event_source),
        ("recorded_at", recorded_at),
        ("test_node_id", test_node_id),
        ("command", command),
        ("run_id", run_id),
        ("artifact_source", artifact_source),
        ("persistence_intent", persistence_intent),
    ):
        if value is not None:
            merged[key] = value

    normalized: dict[str, Any] = {}
    source = _non_empty_metadata_value(merged.get("event_source")) or DEFAULT_EVENT_SOURCE
    normalized["event_source"] = source
    for key in ("recorded_at", "test_node_id", "command", "run_id", "artifact_source", "persistence_intent"):
        value = _non_empty_metadata_value(merged.get(key))
        if value is not None:
            normalized[key] = value
    return normalized


def _row_recurrence_event_metadata(
    batch_metadata: Mapping[str, Any],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge batch metadata with row-local protected failure identifiers."""
    event_metadata = dict(batch_metadata)
    row_test_node_id = _non_empty_metadata_value(row.get("test_node_id"))
    if row_test_node_id is not None:
        event_metadata["test_node_id"] = row_test_node_id
    return event_metadata


def empty_recurrence_event_log() -> dict[str, Any]:
    """Return an empty append-only recurrence event log envelope."""
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": [],
    }


def load_recurrence_event_log(path: Path | str) -> dict[str, Any]:
    """Load a persisted recurrence event log; missing paths return an empty log."""
    log_path = Path(path)
    if not log_path.is_file():
        return empty_recurrence_event_log()
    raw = json.loads(log_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("events"), list):
        raise ValueError("event log must be a JSON object with an events list")
    if raw.get("schema_version") != RECURRENCE_SCHEMA_VERSION:
        raise ValueError(f"unsupported event log schema_version: {raw.get('schema_version')!r}")
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": [dict(item) for item in raw["events"] if isinstance(item, Mapping)],
    }


def write_recurrence_event_log(path: Path | str, payload: Mapping[str, Any]) -> Path:
    """Write a recurrence event log JSON artifact."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return log_path


def _next_event_index(events: Sequence[Mapping[str, Any]]) -> int:
    if not events:
        return 0
    return max(int(event.get("event_index") or 0) for event in events) + 1


def _project_recurrence_events_for_append(
    existing_log: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    event_metadata: Mapping[str, Any] | None = None,
    event_source: str | None = None,
    recorded_at: str | None = None,
    start_index: int | None = None,
) -> list[dict[str, Any]]:
    """Project classification rows into append-ready recurrence events."""
    prior_events = (
        existing_log.get("events")
        if isinstance(existing_log, Mapping) and isinstance(existing_log.get("events"), list)
        else []
    )
    source_rows = [row for row in (rows or ()) if isinstance(row, Mapping)]
    projected: list[tuple[Mapping[str, Any], dict[str, Any]]] = []
    for source_row in source_rows:
        for projected_row in recurrence_rows([source_row]):
            projected.append((source_row, projected_row))
    if not projected:
        return []

    batch_metadata = normalize_recurrence_event_metadata(
        event_metadata,
        event_source=event_source,
        recorded_at=recorded_at,
    )
    batch_metadata["recorded_at"] = batch_metadata.get("recorded_at") or _utc_now_iso()
    resolved_start = start_index if start_index is not None else _next_event_index(prior_events)
    appended: list[dict[str, Any]] = []
    for offset, (source_row, row) in enumerate(projected):
        event = dict(row)
        event["event_index"] = resolved_start + offset
        event.update(_row_recurrence_event_metadata(batch_metadata, source_row))
        appended.append(event)
    return appended


def append_recurrence_events(
    existing_log: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    event_metadata: Mapping[str, Any] | None = None,
    event_source: str | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Return an event log with projected classification rows appended."""
    prior_events = (
        existing_log.get("events")
        if isinstance(existing_log, Mapping) and isinstance(existing_log.get("events"), list)
        else []
    )
    preserved = [dict(item) for item in prior_events if isinstance(item, Mapping)]
    appended = _project_recurrence_events_for_append(
        existing_log,
        rows,
        event_metadata=event_metadata,
        event_source=event_source,
        recorded_at=recorded_at,
    )
    if not appended:
        return {
            "schema_version": RECURRENCE_SCHEMA_VERSION,
            "report_only": RECURRENCE_REPORT_ONLY,
            "advisory_only": RECURRENCE_ADVISORY_ONLY,
            "events": preserved,
        }

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": preserved + appended,
    }


def append_recurrence_events_to_persistence_lanes(
    protected_log: Mapping[str, Any],
    session_diagnostic_log: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    event_metadata: Mapping[str, Any] | None = None,
    event_source: str | None = None,
    recorded_at: str | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Route projected recurrence events into protected or session-diagnostic lanes explicitly."""
    active_policy = policy or DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY
    protected_preserved = [dict(item) for item in _event_log_events(protected_log)]
    session_preserved = [dict(item) for item in _event_log_events(session_diagnostic_log)]
    start_index = max(
        _next_event_index(protected_preserved),
        _next_event_index(session_preserved),
    )
    projected = _project_recurrence_events_for_append(
        empty_recurrence_event_log(),
        rows,
        event_metadata=event_metadata,
        event_source=event_source,
        recorded_at=recorded_at,
        start_index=start_index,
    )

    routing: list[dict[str, Any]] = []
    protected_new: list[dict[str, Any]] = []
    session_new: list[dict[str, Any]] = []
    for event in projected:
        worthy, reason = is_commit_worthy_recurrence_event(event, policy=active_policy)
        lane = (
            RECURRENCE_PERSISTENCE_LANE_PROTECTED
            if worthy
            else RECURRENCE_PERSISTENCE_LANE_SESSION_DIAGNOSTIC
        )
        routing.append(
            {
                "event_index": event.get("event_index"),
                "recurrence_key": event.get("recurrence_key"),
                "persistence_lane": lane,
                "commit_worthy": worthy,
                "reason": reason,
            }
        )
        if worthy:
            protected_new.append(event)
        else:
            session_new.append(event)

    updated_protected = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": protected_preserved + protected_new,
    }
    updated_session = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": session_preserved + session_new,
    }
    return {
        "protected_log": updated_protected,
        "session_diagnostic_log": updated_session,
        "protected_appended": len(protected_new),
        "session_diagnostic_appended": len(session_new),
        "routing": routing,
    }


def aggregate_recurrence_history_from_event_log(
    event_log: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Aggregate bug-class recurrence history from a persisted event log."""
    if not isinstance(event_log, Mapping):
        return aggregate_recurrence_history([])
    events = event_log.get("events")
    if not isinstance(events, list):
        return aggregate_recurrence_history([])
    ordered = sorted(
        [dict(event) for event in events if isinstance(event, Mapping)],
        key=lambda event: (
            int(event.get("event_index") or 0),
            str(event.get("recurrence_key") or ""),
        ),
    )
    return aggregate_recurrence_history(ordered)


def aggregate_protected_recurrence_history_from_event_log(
    event_log: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Aggregate committed protected replay recurrence history from an event log."""
    protected_log = filter_commit_worthy_recurrence_event_log(event_log, policy=policy)
    history = aggregate_recurrence_history_from_event_log(protected_log)
    history["persistence_population"] = RECURRENCE_PERSISTENCE_LANE_PROTECTED
    history["protected_replay_regression_recurrence_rate"] = (
        calculate_protected_replay_regression_recurrence_rate(event_log, policy=policy)
    )
    return history


def recurrence_backfill_dedupe_key(
    row: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Return a stable dedupe key for backfill idempotency checks."""
    projected = recurrence_rows([row])
    if not projected:
        return ()
    projected_row = projected[0]
    meta = normalize_recurrence_event_metadata(metadata)
    test_node_id = _non_empty_metadata_value(row.get("test_node_id")) or meta.get("test_node_id") or ""
    return (
        str(meta.get("event_source") or ""),
        str(meta.get("artifact_source") or ""),
        str(projected_row.get("scenario_id") or ""),
        str(projected_row.get("turn_index") or ""),
        str(projected_row.get("category") or ""),
        str(projected_row.get("owner_drift_bucket") or ""),
        str(projected_row.get("field_path") or ""),
        str(projected_row.get("investigate_first") or ""),
        str(test_node_id),
        str(meta.get("command") or ""),
    )


def recurrence_event_backfill_dedupe_key(event: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Return the backfill dedupe key for one persisted recurrence event."""
    source = event if isinstance(event, Mapping) else {}
    return (
        str(source.get("event_source") or ""),
        str(source.get("artifact_source") or ""),
        str(source.get("scenario_id") or ""),
        str(source.get("turn_index") or ""),
        str(source.get("category") or ""),
        str(source.get("owner_drift_bucket") or ""),
        str(source.get("field_path") or ""),
        str(source.get("investigate_first") or ""),
        str(source.get("test_node_id") or ""),
        str(source.get("command") or ""),
    )


def existing_backfill_dedupe_keys(event_log: Mapping[str, Any] | None) -> set[tuple[str, ...]]:
    """Collect dedupe keys already present in a recurrence event log."""
    if not isinstance(event_log, Mapping):
        return set()
    events = event_log.get("events")
    if not isinstance(events, list):
        return set()
    keys: set[tuple[str, ...]] = set()
    for event in events:
        if isinstance(event, Mapping):
            key = recurrence_event_backfill_dedupe_key(event)
            if key:
                keys.add(key)
    return keys


RECURRENCE_TREND_CLASSIFICATION_EMERGING = "emerging"
RECURRENCE_TREND_CLASSIFICATION_RECURRING = "recurring"
RECURRENCE_TREND_CLASSIFICATION_PERSISTENT = "persistent"
RECURRENCE_TREND_CLASSIFICATION_DORMANT = "dormant"
RECURRENCE_TREND_CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        RECURRENCE_TREND_CLASSIFICATION_EMERGING,
        RECURRENCE_TREND_CLASSIFICATION_RECURRING,
        RECURRENCE_TREND_CLASSIFICATION_PERSISTENT,
        RECURRENCE_TREND_CLASSIFICATION_DORMANT,
    }
)
RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS = 7
RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS = 30
RECURRENCE_TREND_GROWTH_RATE_DEFINITION = (
    "Share of protected recurrence keys currently classified as emerging "
    "(first observation only)."
)
RECURRENCE_TREND_CLASSIFICATION_DEFINITIONS: dict[str, str] = {
    RECURRENCE_TREND_CLASSIFICATION_EMERGING: (
        "Exactly one protected observation exists for the recurrence key."
    ),
    RECURRENCE_TREND_CLASSIFICATION_RECURRING: (
        "Multiple protected observations with recent activity and without an extended active span."
    ),
    RECURRENCE_TREND_CLASSIFICATION_PERSISTENT: (
        "Multiple protected observations spanning at least "
        f"{RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS} days between first and last seen."
    ),
    RECURRENCE_TREND_CLASSIFICATION_DORMANT: (
        "Multiple protected observations historically, but no observation within the last "
        f"{RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS} days."
    ),
}


def _parse_iso_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _protected_events_ordered(
    event_log: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> list[dict[str, Any]]:
    protected_log = filter_commit_worthy_recurrence_event_log(event_log, policy=policy)
    events = protected_log.get("events")
    if not isinstance(events, list):
        return []
    return sorted(
        [dict(event) for event in events if isinstance(event, Mapping)],
        key=lambda event: (
            int(event.get("event_index") or 0),
            str(event.get("recurrence_key") or ""),
        ),
    )


def _timeline_as_of(
    events: Sequence[Mapping[str, Any]],
    *,
    as_of: Any | None = None,
) -> datetime:
    explicit = _parse_iso_timestamp(as_of)
    if explicit is not None:
        return explicit
    latest: datetime | None = None
    for event in events:
        recorded_at = _parse_iso_timestamp(event.get("recorded_at"))
        if recorded_at is None:
            continue
        if latest is None or recorded_at > latest:
            latest = recorded_at
    return latest or datetime.now(UTC)


def classify_recurrence_trend_entry(
    *,
    occurrence_count: int,
    first_seen: Any | None,
    last_seen: Any | None,
    as_of: Any | None = None,
    persistent_min_active_duration_days: float = RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS,
    dormant_inactivity_days: float = RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS,
) -> str:
    """Classify one protected recurrence key into a deterministic trend bucket."""
    count = max(int(occurrence_count or 0), 0)
    if count <= 1:
        return RECURRENCE_TREND_CLASSIFICATION_EMERGING

    first_dt = _parse_iso_timestamp(first_seen)
    last_dt = _parse_iso_timestamp(last_seen)
    as_of_dt = _parse_iso_timestamp(as_of) or last_dt or first_dt or datetime.now(UTC)

    if last_dt is not None:
        inactivity_days = max((as_of_dt - last_dt).total_seconds() / 86400.0, 0.0)
        if inactivity_days >= dormant_inactivity_days:
            return RECURRENCE_TREND_CLASSIFICATION_DORMANT

    if first_dt is not None and last_dt is not None:
        active_duration_days = max((last_dt - first_dt).total_seconds() / 86400.0, 0.0)
        if active_duration_days >= persistent_min_active_duration_days:
            return RECURRENCE_TREND_CLASSIFICATION_PERSISTENT

    return RECURRENCE_TREND_CLASSIFICATION_RECURRING


def build_recurrence_timeline(
    event_log: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
    as_of: Any | None = None,
    persistent_min_active_duration_days: float = RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS,
    dormant_inactivity_days: float = RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS,
) -> list[dict[str, Any]]:
    """Build per-key protected replay recurrence timelines for future visualization."""
    events = _protected_events_ordered(event_log, policy=policy)
    as_of_dt = _timeline_as_of(events, as_of=as_of)
    buckets: dict[str, dict[str, Any]] = {}

    for event in events:
        key = str(event.get("recurrence_key") or build_recurrence_key(event)).strip()
        if not key:
            continue
        recorded_at = str(event.get("recorded_at") or "").strip() or None
        bucket = buckets.setdefault(
            key,
            {
                "recurrence_key": key,
                "occurrence_count": 0,
                "first_seen": recorded_at,
                "last_seen": recorded_at,
                "_first_dt": _parse_iso_timestamp(recorded_at),
                "_last_dt": _parse_iso_timestamp(recorded_at),
            },
        )
        bucket["occurrence_count"] += 1
        parsed = _parse_iso_timestamp(recorded_at)
        if parsed is not None:
            if bucket["_first_dt"] is None or parsed < bucket["_first_dt"]:
                bucket["_first_dt"] = parsed
                bucket["first_seen"] = recorded_at
            if bucket["_last_dt"] is None or parsed > bucket["_last_dt"]:
                bucket["_last_dt"] = parsed
                bucket["last_seen"] = recorded_at
        elif recorded_at:
            if bucket["first_seen"] is None:
                bucket["first_seen"] = recorded_at
            bucket["last_seen"] = recorded_at

    timeline: list[dict[str, Any]] = []
    for bucket in buckets.values():
        first_dt = bucket.pop("_first_dt")
        last_dt = bucket.pop("_last_dt")
        if first_dt is not None and last_dt is not None:
            active_duration_days = max((last_dt - first_dt).total_seconds() / 86400.0, 0.0)
        else:
            active_duration_days = 0.0
        occurrence_count = int(bucket["occurrence_count"])
        if active_duration_days > 0.0:
            recurrence_velocity = round(occurrence_count / active_duration_days, 4)
        else:
            recurrence_velocity = float(occurrence_count)
        trend_classification = classify_recurrence_trend_entry(
            occurrence_count=occurrence_count,
            first_seen=bucket.get("first_seen"),
            last_seen=bucket.get("last_seen"),
            as_of=as_of_dt.isoformat().replace("+00:00", "Z"),
            persistent_min_active_duration_days=persistent_min_active_duration_days,
            dormant_inactivity_days=dormant_inactivity_days,
        )
        timeline.append(
            {
                "recurrence_key": bucket["recurrence_key"],
                "first_seen": bucket.get("first_seen"),
                "last_seen": bucket.get("last_seen"),
                "occurrence_count": occurrence_count,
                "active_duration_days": round(active_duration_days, 4),
                "recurrence_velocity": recurrence_velocity,
                "trend_classification": trend_classification,
            }
        )

    timeline.sort(key=lambda entry: (str(entry.get("first_seen") or ""), str(entry.get("recurrence_key") or "")))
    return timeline


def summarize_recurrence_growth(
    timeline: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Summarize protected recurrence key growth from a trend timeline."""
    rows = [dict(row) for row in (timeline or ()) if isinstance(row, Mapping)]
    total_keys = len(rows)
    classification_counts = {label: 0 for label in sorted(RECURRENCE_TREND_CLASSIFICATIONS)}
    for row in rows:
        classification = str(row.get("trend_classification") or "").strip()
        if classification in classification_counts:
            classification_counts[classification] += 1
    emerging_keys = classification_counts[RECURRENCE_TREND_CLASSIFICATION_EMERGING]
    growth_rate = (emerging_keys / total_keys) if total_keys else 0.0
    return {
        "total_keys": total_keys,
        "emerging_keys": emerging_keys,
        "recurring_keys": classification_counts[RECURRENCE_TREND_CLASSIFICATION_RECURRING],
        "persistent_keys": classification_counts[RECURRENCE_TREND_CLASSIFICATION_PERSISTENT],
        "dormant_keys": classification_counts[RECURRENCE_TREND_CLASSIFICATION_DORMANT],
        "growth_rate": growth_rate,
        "classification_counts": classification_counts,
    }


def build_recurrence_trend_summary(
    event_log: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
    as_of: Any | None = None,
    persistent_min_active_duration_days: float = RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS,
    dormant_inactivity_days: float = RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS,
) -> dict[str, Any]:
    """Build protected replay recurrence trend metrics from the protected event log."""
    timeline = build_recurrence_timeline(
        event_log,
        policy=policy,
        as_of=as_of,
        persistent_min_active_duration_days=persistent_min_active_duration_days,
        dormant_inactivity_days=dormant_inactivity_days,
    )
    growth = summarize_recurrence_growth(timeline)
    regression_recurrence_rate = calculate_protected_replay_regression_recurrence_rate(event_log, policy=policy)
    top_recurring_keys = sorted(
        [
            {
                "recurrence_key": row.get("recurrence_key"),
                "occurrence_count": int(row.get("occurrence_count") or 0),
                "trend_classification": row.get("trend_classification"),
            }
            for row in timeline
            if int(row.get("occurrence_count") or 0) >= 2
        ],
        key=lambda row: (
            -int(row.get("occurrence_count") or 0),
            str(row.get("recurrence_key") or ""),
        ),
    )
    newest_recurrence_keys = sorted(
        [
            {
                "recurrence_key": row.get("recurrence_key"),
                "first_seen": row.get("first_seen"),
                "trend_classification": row.get("trend_classification"),
            }
            for row in timeline
        ],
        key=lambda row: (
            str(row.get("first_seen") or ""),
            str(row.get("recurrence_key") or ""),
        ),
        reverse=True,
    )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definitions": RECURRENCE_TREND_CLASSIFICATION_DEFINITIONS,
        "growth_rate_definition": RECURRENCE_TREND_GROWTH_RATE_DEFINITION,
        "total_keys": growth["total_keys"],
        "emerging_keys": growth["emerging_keys"],
        "recurring_keys": growth["recurring_keys"],
        "persistent_keys": growth["persistent_keys"],
        "dormant_keys": growth["dormant_keys"],
        "growth_rate": growth["growth_rate"],
        "regression_recurrence_rate": regression_recurrence_rate,
        "top_recurring_keys": top_recurring_keys,
        "newest_recurrence_keys": newest_recurrence_keys,
    }


def enrich_recurrence_history_with_trends(
    history: Mapping[str, Any],
    event_log: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay trend fields."""
    payload = dict(history)
    timeline = build_recurrence_timeline(event_log, policy=policy, as_of=as_of)
    payload["recurrence_timeline"] = timeline
    payload["recurrence_trends"] = build_recurrence_trend_summary(
        event_log,
        policy=policy,
        as_of=as_of,
    )
    return payload


RECURRENCE_FORECAST_STABLE = "stable"
RECURRENCE_FORECAST_WATCH = "watch"
RECURRENCE_FORECAST_ELEVATED = "elevated"
RECURRENCE_FORECAST_CONCENTRATED = "concentrated"
RECURRENCE_FORECAST_CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        RECURRENCE_FORECAST_STABLE,
        RECURRENCE_FORECAST_WATCH,
        RECURRENCE_FORECAST_ELEVATED,
        RECURRENCE_FORECAST_CONCENTRATED,
    }
)
RECURRENCE_FORECAST_CONCENTRATED_OBSERVATION_SHARE = 0.5
RECURRENCE_FORECAST_ELEVATED_MIN_VELOCITY = 1.0
RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS = 5
RECURRENCE_STABILITY_SCORE_DEFINITION = (
    "100 * (1 - regression_recurrence_rate.rate). 100 means no protected recurrence keys "
    "have repeated observations; 0 means every observed key is recurrence-active."
)
RECURRENCE_FORECAST_RISK_SCORE_DEFINITION = (
    "Advisory 0-100 blend: 50% regression_recurrence_rate + 20% emerging_key_share + "
    "20% elevated_key_share + 10% concentration_ratio (HHI of observation shares)."
)
RECURRENCE_FORECAST_CLASSIFICATION_DEFINITIONS: dict[str, str] = {
    RECURRENCE_FORECAST_STABLE: (
        "Low estimated future recurrence risk; typically dormant trend or no upward trajectory."
    ),
    RECURRENCE_FORECAST_WATCH: (
        "Emerging protected recurrence requiring observation before transition to recurring."
    ),
    RECURRENCE_FORECAST_ELEVATED: (
        "Repeated protected observations with upward trajectory (recurring or persistent trend)."
    ),
    RECURRENCE_FORECAST_CONCENTRATED: (
        "Recurrence risk concentrated in this key within a multi-key population: observation share "
        f"meets or exceeds {RECURRENCE_FORECAST_CONCENTRATED_OBSERVATION_SHARE:.0%} with multiple "
        "total observations across at least two keys."
    ),
}


def _timeline_rows(timeline: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    return [dict(row) for row in (timeline or ()) if isinstance(row, Mapping)]


def _regression_rate_value(regression_recurrence_rate: Mapping[str, Any] | None) -> float:
    if not isinstance(regression_recurrence_rate, Mapping):
        return 0.0
    return float(regression_recurrence_rate.get("rate") or 0.0)


def summarize_recurrence_risk(
    timeline: Sequence[Mapping[str, Any]] | None,
    *,
    regression_recurrence_rate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure protected recurrence observation concentration and dominance."""
    rows = _timeline_rows(timeline)
    total_observations = sum(int(row.get("occurrence_count") or 0) for row in rows)
    total_keys = len(rows)
    ranked = sorted(
        rows,
        key=lambda row: (
            -int(row.get("occurrence_count") or 0),
            str(row.get("recurrence_key") or ""),
        ),
    )
    top_count = int(ranked[0].get("occurrence_count") or 0) if ranked else 0
    top_three_count = sum(int(row.get("occurrence_count") or 0) for row in ranked[:3])
    top_key_share = (top_count / total_observations) if total_observations else 0.0
    top_three_key_share = (top_three_count / total_observations) if total_observations else 0.0
    if total_observations:
        shares = [
            int(row.get("occurrence_count") or 0) / total_observations
            for row in rows
        ]
        concentration_ratio = round(sum(share * share for share in shares), 4)
    else:
        concentration_ratio = 0.0
    dominant_recurrence_key = str(ranked[0].get("recurrence_key") or "") if ranked else None
    if dominant_recurrence_key == "":
        dominant_recurrence_key = None
    return {
        "total_keys": total_keys,
        "total_observations": total_observations,
        "top_key_share": round(top_key_share, 4),
        "top_three_key_share": round(top_three_key_share, 4),
        "concentration_ratio": concentration_ratio,
        "dominant_recurrence_key": dominant_recurrence_key,
        "regression_recurrence_rate": _regression_rate_value(regression_recurrence_rate),
    }


def classify_recurrence_forecast(
    timeline_entry: Mapping[str, Any] | None,
    *,
    observation_share: float = 0.0,
    total_observations: int = 0,
    total_keys: int = 0,
) -> str:
    """Classify one protected recurrence key into a deterministic forecast bucket."""
    entry = timeline_entry if isinstance(timeline_entry, Mapping) else {}
    trend = str(entry.get("trend_classification") or "").strip()
    occurrence_count = int(entry.get("occurrence_count") or 0)
    velocity = float(entry.get("recurrence_velocity") or 0.0)
    share = max(float(observation_share or 0.0), 0.0)
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 0)

    if trend == RECURRENCE_TREND_CLASSIFICATION_EMERGING:
        return RECURRENCE_FORECAST_WATCH
    if trend == RECURRENCE_TREND_CLASSIFICATION_DORMANT:
        return RECURRENCE_FORECAST_STABLE
    if (
        keys >= 2
        and observations >= 2
        and occurrence_count >= 2
        and share >= RECURRENCE_FORECAST_CONCENTRATED_OBSERVATION_SHARE
    ):
        return RECURRENCE_FORECAST_CONCENTRATED
    if trend in {
        RECURRENCE_TREND_CLASSIFICATION_RECURRING,
        RECURRENCE_TREND_CLASSIFICATION_PERSISTENT,
    }:
        return RECURRENCE_FORECAST_ELEVATED
    if occurrence_count >= 2 and velocity >= RECURRENCE_FORECAST_ELEVATED_MIN_VELOCITY:
        return RECURRENCE_FORECAST_ELEVATED
    return RECURRENCE_FORECAST_STABLE


def _forecast_classification_counts(key_forecasts: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {label: 0 for label in sorted(RECURRENCE_FORECAST_CLASSIFICATIONS)}
    for row in key_forecasts:
        if not isinstance(row, Mapping):
            continue
        classification = str(row.get("forecast_classification") or "").strip()
        if classification in counts:
            counts[classification] += 1
    return counts


def _stability_score(regression_recurrence_rate: Mapping[str, Any] | None) -> float:
    rate = _regression_rate_value(regression_recurrence_rate)
    return round(max(0.0, min(100.0, 100.0 * (1.0 - rate))), 1)


def _forecast_risk_score(
    *,
    regression_recurrence_rate: Mapping[str, Any] | None,
    total_keys: int,
    forecast_counts: Mapping[str, int],
    concentration_ratio: float,
) -> float:
    regression_rate = _regression_rate_value(regression_recurrence_rate)
    keys = max(int(total_keys or 0), 0)
    emerging_share = (
        int(forecast_counts.get(RECURRENCE_FORECAST_WATCH) or 0) / keys if keys else 0.0
    )
    elevated_share = (
        int(forecast_counts.get(RECURRENCE_FORECAST_ELEVATED) or 0) / keys if keys else 0.0
    )
    concentrated_share = (
        int(forecast_counts.get(RECURRENCE_FORECAST_CONCENTRATED) or 0) / keys if keys else 0.0
    )
    blended = (
        0.5 * regression_rate
        + 0.2 * emerging_share
        + 0.15 * elevated_share
        + 0.05 * concentrated_share
        + 0.1 * float(concentration_ratio or 0.0)
    )
    return round(max(0.0, min(100.0, 100.0 * blended)), 1)


def _forecast_confidence(total_observations: int) -> float:
    observations = max(int(total_observations or 0), 0)
    return round(
        min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS)),
        2,
    )


def build_recurrence_forecast(
    *,
    recurrence_timeline: Sequence[Mapping[str, Any]] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    regression_recurrence_rate: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence forecast from timeline and trend inputs."""
    timeline = _timeline_rows(recurrence_timeline)
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    if not timeline and event_log is not None:
        timeline = build_recurrence_timeline(event_log, policy=policy, as_of=as_of)
    if not trends and event_log is not None:
        trends = build_recurrence_trend_summary(event_log, policy=policy, as_of=as_of)

    regression = regression_recurrence_rate
    if not isinstance(regression, Mapping):
        nested = trends.get("regression_recurrence_rate")
        regression = nested if isinstance(nested, Mapping) else {}

    risk = summarize_recurrence_risk(timeline, regression_recurrence_rate=regression)
    total_observations = int(risk["total_observations"])
    total_keys = int(risk["total_keys"])
    key_forecasts: list[dict[str, Any]] = []
    for row in timeline:
        occurrence_count = int(row.get("occurrence_count") or 0)
        observation_share = (
            occurrence_count / total_observations if total_observations else 0.0
        )
        forecast_classification = classify_recurrence_forecast(
            row,
            observation_share=observation_share,
            total_observations=total_observations,
            total_keys=total_keys,
        )
        key_forecasts.append(
            {
                "recurrence_key": row.get("recurrence_key"),
                "trend_classification": row.get("trend_classification"),
                "forecast_classification": forecast_classification,
                "occurrence_count": occurrence_count,
                "observation_share": round(observation_share, 4),
                "recurrence_velocity": row.get("recurrence_velocity"),
                "first_seen": row.get("first_seen"),
                "last_seen": row.get("last_seen"),
            }
        )

    forecast_counts = _forecast_classification_counts(key_forecasts)
    stability_score = _stability_score(regression)
    forecast_risk_score = _forecast_risk_score(
        regression_recurrence_rate=regression,
        total_keys=int(risk["total_keys"]),
        forecast_counts=forecast_counts,
        concentration_ratio=float(risk["concentration_ratio"]),
    )
    forecast_confidence = _forecast_confidence(total_observations)
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definitions": RECURRENCE_FORECAST_CLASSIFICATION_DEFINITIONS,
        "stability_score_definition": RECURRENCE_STABILITY_SCORE_DEFINITION,
        "forecast_risk_score_definition": RECURRENCE_FORECAST_RISK_SCORE_DEFINITION,
        "forecast_summary": {
            "schema_version": RECURRENCE_SCHEMA_VERSION,
            "report_only": RECURRENCE_REPORT_ONLY,
            "advisory_only": RECURRENCE_ADVISORY_ONLY,
            "protected_replay_only": True,
            "stable_keys": forecast_counts[RECURRENCE_FORECAST_STABLE],
            "watch_keys": forecast_counts[RECURRENCE_FORECAST_WATCH],
            "elevated_keys": forecast_counts[RECURRENCE_FORECAST_ELEVATED],
            "concentrated_keys": forecast_counts[RECURRENCE_FORECAST_CONCENTRATED],
            "forecast_risk_score": forecast_risk_score,
            "stability_score": stability_score,
            "forecast_confidence": forecast_confidence,
        },
        "risk_concentration": {
            "top_key_share": risk["top_key_share"],
            "top_three_key_share": risk["top_three_key_share"],
            "concentration_ratio": risk["concentration_ratio"],
            "dominant_recurrence_key": risk["dominant_recurrence_key"],
            "total_observations": total_observations,
            "total_keys": risk["total_keys"],
        },
        "key_forecasts": key_forecasts,
        "regression_recurrence_rate": regression,
    }


def enrich_recurrence_history_with_forecasts(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay forecast fields."""
    payload = dict(history)
    timeline = payload.get("recurrence_timeline")
    trends = payload.get("recurrence_trends")
    regression = payload.get("regression_recurrence_rate")
    payload["recurrence_forecast"] = build_recurrence_forecast(
        recurrence_timeline=timeline if isinstance(timeline, list) else None,
        recurrence_trends=trends if isinstance(trends, Mapping) else None,
        regression_recurrence_rate=regression if isinstance(regression, Mapping) else None,
        event_log=event_log,
        policy=policy,
        as_of=as_of,
    )
    return payload


RECURRENCE_PORTFOLIO_RISK_SCORE_DEFINITION = (
    "Advisory 0-100 blend: 60% forecast_risk_score/100 + 10% each dimension concentration "
    "ratio (owner, category, field_path, scenario). Higher scores indicate greater localized "
    "or forecast-weighted recurrence risk."
)
RECURRENCE_PORTFOLIO_CONCENTRATION_DEFINITION = (
    "Herfindahl index (sum of squared observation risk shares) per dimension. "
    "High concentration means risk is localized (easier remediation); low concentration means "
    "distributed risk (broader systemic concern)."
)
RECURRENCE_PORTFOLIO_DIMENSIONS: tuple[str, ...] = (
    "owner",
    "category",
    "field_path",
    "scenario",
)


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


def _portfolio_owner_label(event: Mapping[str, Any]) -> str:
    return recurrence_owner(event)


def _portfolio_key_catalog(
    *,
    recurrence_timeline: Sequence[Mapping[str, Any]] | None,
    recurrence_forecast: Mapping[str, Any] | None,
    event_log: Mapping[str, Any] | None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> list[dict[str, Any]]:
    """Build per-key protected recurrence metadata for portfolio aggregation."""
    timeline = _timeline_rows(recurrence_timeline)
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    key_forecasts = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (forecast.get("key_forecasts") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }
    timeline_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in timeline
        if str(row.get("recurrence_key") or "").strip()
    }
    events = _protected_events_ordered(event_log, policy=policy)
    events_by_key: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        key = str(event.get("recurrence_key") or build_recurrence_key(event)).strip()
        if not key:
            continue
        events_by_key.setdefault(key, []).append(event)

    all_keys = sorted(set(timeline_by_key) | set(key_forecasts) | set(events_by_key))
    catalog: list[dict[str, Any]] = []
    for key in all_keys:
        timeline_row = timeline_by_key.get(key, {})
        forecast_row = key_forecasts.get(key, {})
        key_events = events_by_key.get(key, [])
        parsed = _parse_recurrence_key_parts(key)
        sample_event = key_events[0] if key_events else {}
        owner = _portfolio_owner_label(sample_event) if key_events else parsed["owner_bucket"]
        category = str(sample_event.get("category") or parsed["category"] or "unknown").strip() or "unknown"
        field_path = str(sample_event.get("field_path") or parsed["field_path"] or "unknown").strip() or "unknown"
        scenarios = sorted(
            {
                str(event.get("scenario_id") or "").strip() or "(null)"
                for event in key_events
            }
        ) if key_events else ["(null)"]
        occurrence_count = int(
            timeline_row.get("occurrence_count")
            or len(key_events)
            or 0
        )
        forecast_classification = str(
            forecast_row.get("forecast_classification") or RECURRENCE_FORECAST_STABLE
        ).strip()
        trend_classification = str(
            timeline_row.get("trend_classification")
            or forecast_row.get("trend_classification")
            or RECURRENCE_TREND_CLASSIFICATION_EMERGING
        ).strip()
        catalog.append(
            {
                "recurrence_key": key,
                "owner": owner,
                "category": category,
                "field_path": field_path,
                "scenarios": scenarios,
                "occurrence_count": occurrence_count,
                "trend_classification": trend_classification,
                "forecast_classification": forecast_classification,
                "is_recurring": occurrence_count >= 2,
                "is_elevated": forecast_classification
                in {RECURRENCE_FORECAST_ELEVATED, RECURRENCE_FORECAST_CONCENTRATED},
            }
        )
    return catalog


def _dimension_concentration_ratio(buckets: Sequence[Mapping[str, Any]]) -> float:
    total_observations = sum(int(row.get("observations") or 0) for row in buckets)
    if total_observations <= 0:
        return 0.0
    shares = [int(row.get("observations") or 0) / total_observations for row in buckets]
    return round(sum(share * share for share in shares), 4)


def _highest_risk_bucket(buckets: Sequence[Mapping[str, Any]], *, label_field: str) -> str | None:
    if not buckets:
        return None
    ranked = sorted(
        buckets,
        key=lambda row: (
            -float(row.get("risk_share") or 0.0),
            str(row.get(label_field) or ""),
        ),
    )
    label = str(ranked[0].get(label_field) or "").strip()
    return label or None


def _apply_risk_shares(
    buckets: list[dict[str, Any]],
    *,
    total_observations: int,
    label_field: str,
) -> list[dict[str, Any]]:
    for bucket in buckets:
        observations = int(bucket.get("observations") or 0)
        bucket["risk_share"] = round(
            observations / total_observations if total_observations else 0.0,
            4,
        )
        bucket["recurrence_keys"] = int(bucket.get("recurrence_keys") or 0)
    return sorted(
        buckets,
        key=lambda row: (
            -float(row.get("risk_share") or 0.0),
            str(row.get(label_field) or ""),
        ),
    )


def aggregate_recurrence_risk_dimensions(
    *,
    recurrence_timeline: Sequence[Mapping[str, Any]] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Aggregate protected recurrence risk by owner, category, field path, and scenario."""
    catalog = _portfolio_key_catalog(
        recurrence_timeline=recurrence_timeline,
        recurrence_forecast=recurrence_forecast,
        event_log=event_log,
        policy=policy,
    )
    events = _protected_events_ordered(event_log, policy=policy)
    total_observations = sum(int(entry.get("occurrence_count") or 0) for entry in catalog)
    if total_observations <= 0:
        total_observations = len(events)

    owner_buckets: dict[str, dict[str, Any]] = {}
    category_buckets: dict[str, dict[str, Any]] = {}
    field_path_buckets: dict[str, dict[str, Any]] = {}
    scenario_buckets: dict[str, dict[str, Any]] = {}
    owner_recurring_keys: dict[str, set[str]] = {}
    owner_elevated_keys: dict[str, set[str]] = {}

    for entry in catalog:
        owner = str(entry.get("owner") or "unknown")
        category = str(entry.get("category") or "unknown")
        field_path = str(entry.get("field_path") or "unknown")
        key = str(entry.get("recurrence_key") or "")
        occurrence_count = int(entry.get("occurrence_count") or 0)

        for bucket_map, label, label_value in (
            (owner_buckets, "owner", owner),
            (category_buckets, "category", category),
            (field_path_buckets, "field_path", field_path),
        ):
            bucket = bucket_map.setdefault(
                label_value,
                {
                    label: label_value,
                    "recurrence_keys": 0,
                    "observations": 0,
                    "risk_share": 0.0,
                },
            )
            bucket["recurrence_keys"] += 1
            bucket["observations"] += occurrence_count

        if entry.get("is_recurring"):
            owner_recurring_keys.setdefault(owner, set()).add(key)
        if entry.get("is_elevated"):
            owner_elevated_keys.setdefault(owner, set()).add(key)

    for event in events:
        scenario = str(event.get("scenario_id") or "").strip() or "(null)"
        bucket = scenario_buckets.setdefault(
            scenario,
            {
                "scenario_id": scenario,
                "recurrence_keys": 0,
                "observations": 0,
                "risk_share": 0.0,
                "_keys": set(),
            },
        )
        bucket["observations"] += 1
        key = str(event.get("recurrence_key") or build_recurrence_key(event)).strip()
        if key:
            bucket["_keys"].add(key)

    owners = []
    for owner, bucket in owner_buckets.items():
        owners.append(
            {
                "owner": owner,
                "recurrence_keys": bucket["recurrence_keys"],
                "observations": bucket["observations"],
                "recurring_keys": len(owner_recurring_keys.get(owner, set())),
                "elevated_keys": len(owner_elevated_keys.get(owner, set())),
                "risk_share": 0.0,
            }
        )
    categories = [
        {
            "category": label,
            "recurrence_keys": bucket["recurrence_keys"],
            "observations": bucket["observations"],
            "risk_share": 0.0,
        }
        for label, bucket in category_buckets.items()
    ]
    field_paths = [
        {
            "field_path": label,
            "recurrence_keys": bucket["recurrence_keys"],
            "observations": bucket["observations"],
            "risk_share": 0.0,
        }
        for label, bucket in field_path_buckets.items()
    ]
    scenarios = []
    for scenario, bucket in scenario_buckets.items():
        scenarios.append(
            {
                "scenario_id": scenario,
                "recurrence_keys": len(bucket["_keys"]),
                "observations": bucket["observations"],
                "risk_share": 0.0,
            }
        )

    owners = _apply_risk_shares(owners, total_observations=total_observations, label_field="owner")
    categories = _apply_risk_shares(categories, total_observations=total_observations, label_field="category")
    field_paths = _apply_risk_shares(field_paths, total_observations=total_observations, label_field="field_path")
    scenarios = _apply_risk_shares(scenarios, total_observations=total_observations, label_field="scenario_id")

    owner_concentration_ratio = _dimension_concentration_ratio(owners)
    category_concentration_ratio = _dimension_concentration_ratio(categories)
    field_path_concentration_ratio = _dimension_concentration_ratio(field_paths)
    scenario_concentration_ratio = _dimension_concentration_ratio(scenarios)

    return {
        "owner_count": len(owners),
        "owners": owners,
        "highest_risk_owner": _highest_risk_bucket(owners, label_field="owner"),
        "owner_concentration_ratio": owner_concentration_ratio,
        "categories": categories,
        "highest_risk_category": _highest_risk_bucket(categories, label_field="category"),
        "category_concentration_ratio": category_concentration_ratio,
        "field_paths": field_paths,
        "highest_risk_field_path": _highest_risk_bucket(field_paths, label_field="field_path"),
        "field_path_concentration_ratio": field_path_concentration_ratio,
        "scenarios": scenarios,
        "highest_risk_scenario": _highest_risk_bucket(scenarios, label_field="scenario_id"),
        "scenario_concentration_ratio": scenario_concentration_ratio,
        "total_observations": total_observations,
        "total_keys": len(catalog),
    }


def _largest_risk_bucket(dimensions: Mapping[str, Any]) -> dict[str, Any] | None:
    mapping = (
        ("owner", "highest_risk_owner", "owner_concentration_ratio", 0),
        ("category", "highest_risk_category", "category_concentration_ratio", 1),
        ("field_path", "highest_risk_field_path", "field_path_concentration_ratio", 2),
        ("scenario", "highest_risk_scenario", "scenario_concentration_ratio", 3),
    )
    candidates: list[tuple[str, str, float, int]] = []
    for dimension, highest_key, ratio_key, priority in mapping:
        ratio = float(dimensions.get(ratio_key) or 0.0)
        label = dimensions.get(highest_key)
        if label:
            candidates.append((dimension, str(label), ratio, priority))
    if not candidates:
        return None
    dimension, label, ratio, _priority = max(
        candidates,
        key=lambda item: (item[2], -item[3], item[1]),
    )
    return {
        "dimension": dimension,
        "label": label,
        "concentration_ratio": round(ratio, 4),
    }


def _portfolio_risk_score(
    *,
    forecast_risk_score: float,
    owner_concentration_ratio: float,
    category_concentration_ratio: float,
    field_path_concentration_ratio: float,
    scenario_concentration_ratio: float,
) -> float:
    blended = (
        0.6 * (float(forecast_risk_score) / 100.0)
        + 0.1 * float(owner_concentration_ratio)
        + 0.1 * float(category_concentration_ratio)
        + 0.1 * float(field_path_concentration_ratio)
        + 0.1 * float(scenario_concentration_ratio)
    )
    return round(max(0.0, min(100.0, 100.0 * blended)), 1)


def summarize_recurrence_portfolio(
    portfolio: Mapping[str, Any] | None,
    *,
    recurrence_forecast: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence portfolio health metrics."""
    source = portfolio if isinstance(portfolio, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = source.get("forecast_summary") if isinstance(source.get("forecast_summary"), Mapping) else {}
    forecast_risk_score = float(forecast_summary.get("forecast_risk_score") or 0.0)
    forecast_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    owner_concentration_ratio = float(source.get("owner_concentration_ratio") or 0.0)
    category_concentration_ratio = float(source.get("category_concentration_ratio") or 0.0)
    field_path_concentration_ratio = float(source.get("field_path_concentration_ratio") or 0.0)
    scenario_concentration_ratio = float(source.get("scenario_concentration_ratio") or 0.0)
    largest = _largest_risk_bucket(source)
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "portfolio_risk_score": _portfolio_risk_score(
            forecast_risk_score=forecast_risk_score,
            owner_concentration_ratio=owner_concentration_ratio,
            category_concentration_ratio=category_concentration_ratio,
            field_path_concentration_ratio=field_path_concentration_ratio,
            scenario_concentration_ratio=scenario_concentration_ratio,
        ),
        "owner_concentration_ratio": owner_concentration_ratio,
        "category_concentration_ratio": category_concentration_ratio,
        "field_path_concentration_ratio": field_path_concentration_ratio,
        "scenario_concentration_ratio": scenario_concentration_ratio,
        "largest_risk_bucket": largest,
        "forecast_confidence": forecast_confidence,
        "portfolio_risk_score_definition": RECURRENCE_PORTFOLIO_RISK_SCORE_DEFINITION,
        "concentration_definition": RECURRENCE_PORTFOLIO_CONCENTRATION_DEFINITION,
    }


def build_recurrence_portfolio(
    *,
    recurrence_timeline: Sequence[Mapping[str, Any]] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence portfolio analytics."""
    dimensions = aggregate_recurrence_risk_dimensions(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        event_log=event_log,
        policy=policy,
    )
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    portfolio_summary = summarize_recurrence_portfolio(dimensions, recurrence_forecast=forecast)
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        **dimensions,
        "portfolio_summary": portfolio_summary,
    }


def enrich_recurrence_history_with_portfolio(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay portfolio fields."""
    payload = dict(history)
    portfolio = build_recurrence_portfolio(
        recurrence_timeline=payload.get("recurrence_timeline")
        if isinstance(payload.get("recurrence_timeline"), list)
        else None,
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        event_log=event_log,
        policy=policy,
    )
    payload["recurrence_portfolio"] = portfolio
    payload["recurrence_portfolio_summary"] = portfolio["portfolio_summary"]
    return payload


RECURRENCE_REMEDIATION_PRIORITY_CRITICAL = "critical"
RECURRENCE_REMEDIATION_PRIORITY_HIGH = "high"
RECURRENCE_REMEDIATION_PRIORITY_MEDIUM = "medium"
RECURRENCE_REMEDIATION_PRIORITY_LOW = "low"
RECURRENCE_REMEDIATION_PRIORITIES: frozenset[str] = frozenset(
    {
        RECURRENCE_REMEDIATION_PRIORITY_CRITICAL,
        RECURRENCE_REMEDIATION_PRIORITY_HIGH,
        RECURRENCE_REMEDIATION_PRIORITY_MEDIUM,
        RECURRENCE_REMEDIATION_PRIORITY_LOW,
    }
)
RECURRENCE_REMEDIATION_PRIORITY_THRESHOLDS: tuple[tuple[str, float], ...] = (
    (RECURRENCE_REMEDIATION_PRIORITY_CRITICAL, 75.0),
    (RECURRENCE_REMEDIATION_PRIORITY_HIGH, 50.0),
    (RECURRENCE_REMEDIATION_PRIORITY_MEDIUM, 25.0),
    (RECURRENCE_REMEDIATION_PRIORITY_LOW, 0.0),
)
RECURRENCE_REDUCTION_POTENTIAL_DEFINITION = (
    "Advisory 0-100 score: 35% risk_share + 20% recurrence_intensity + 20% trend_weight + "
    "15% forecast_weight + 10% concentration_contribution, where recurrence_intensity is "
    "occurrence_count/total_observations and concentration_contribution is "
    "risk_share multiplied by the max dimension concentration ratio."
)
RECURRENCE_REMEDIATION_PRIORITY_DEFINITION = (
    "Deterministic priority from reduction_potential: critical >= 75, high >= 50, "
    "medium >= 25, low < 25."
)
RECURRENCE_REMEDIATION_CONFIDENCE_DEFINITION = (
    "forecast_confidence multiplied by min(1, total_observations / 5)."
)
RECURRENCE_ESTIMATED_PORTFOLIO_REDUCTION_DEFINITION = (
    "Advisory estimate: highest key reduction_potential multiplied by remediation_confidence."
)
RECURRENCE_TREND_REDUCTION_WEIGHTS: dict[str, float] = {
    RECURRENCE_TREND_CLASSIFICATION_EMERGING: 0.35,
    RECURRENCE_TREND_CLASSIFICATION_RECURRING: 0.75,
    RECURRENCE_TREND_CLASSIFICATION_PERSISTENT: 0.90,
    RECURRENCE_TREND_CLASSIFICATION_DORMANT: 0.25,
}
RECURRENCE_FORECAST_REDUCTION_WEIGHTS: dict[str, float] = {
    RECURRENCE_FORECAST_WATCH: 0.40,
    RECURRENCE_FORECAST_ELEVATED: 0.85,
    RECURRENCE_FORECAST_CONCENTRATED: 0.95,
    RECURRENCE_FORECAST_STABLE: 0.20,
}


def classify_remediation_priority(reduction_potential: float) -> str:
    """Map reduction potential to a deterministic remediation priority."""
    score = float(reduction_potential or 0.0)
    for label, threshold in RECURRENCE_REMEDIATION_PRIORITY_THRESHOLDS:
        if score >= threshold:
            return label
    return RECURRENCE_REMEDIATION_PRIORITY_LOW


def calculate_recurrence_reduction_potential(
    *,
    risk_share: float,
    occurrence_count: int,
    total_observations: int,
    trend_classification: str,
    forecast_classification: str,
    concentration_contribution: float,
) -> float:
    """Return advisory 0-100 expected recurrence reduction if the target is addressed."""
    observations = max(int(total_observations or 0), 0)
    count = max(int(occurrence_count or 0), 0)
    share = max(float(risk_share or 0.0), 0.0)
    recurrence_intensity = (count / observations) if observations else 0.0
    trend_weight = RECURRENCE_TREND_REDUCTION_WEIGHTS.get(
        str(trend_classification or "").strip(),
        0.20,
    )
    forecast_weight = RECURRENCE_FORECAST_REDUCTION_WEIGHTS.get(
        str(forecast_classification or "").strip(),
        0.20,
    )
    concentration = max(float(concentration_contribution or 0.0), 0.0)
    blended = (
        0.35 * share
        + 0.20 * recurrence_intensity
        + 0.20 * trend_weight
        + 0.15 * forecast_weight
        + 0.10 * concentration
    )
    return round(max(0.0, min(100.0, 100.0 * blended)), 1)


def _portfolio_concentration_max(portfolio: Mapping[str, Any]) -> float:
    return max(
        float(portfolio.get("owner_concentration_ratio") or 0.0),
        float(portfolio.get("category_concentration_ratio") or 0.0),
        float(portfolio.get("field_path_concentration_ratio") or 0.0),
        float(portfolio.get("scenario_concentration_ratio") or 0.0),
    )


def _remediation_confidence(
    *,
    forecast_confidence: float,
    total_observations: int,
) -> float:
    observations = max(int(total_observations or 0), 0)
    volume_factor = min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS))
    return round(max(0.0, min(1.0, float(forecast_confidence or 0.0) * volume_factor)), 2)


def _enrich_remediation_bucket(
    bucket: Mapping[str, Any],
    *,
    total_observations: int,
    concentration_max: float,
    trend_classification: str = RECURRENCE_TREND_CLASSIFICATION_EMERGING,
    forecast_classification: str = RECURRENCE_FORECAST_WATCH,
) -> dict[str, Any]:
    enriched = dict(bucket)
    risk_share = float(enriched.get("risk_share") or 0.0)
    observations = int(enriched.get("observations") or 0)
    concentration_contribution = round(risk_share * concentration_max, 4)
    reduction_potential = calculate_recurrence_reduction_potential(
        risk_share=risk_share,
        occurrence_count=observations,
        total_observations=total_observations,
        trend_classification=trend_classification,
        forecast_classification=forecast_classification,
        concentration_contribution=concentration_contribution,
    )
    enriched["reduction_potential"] = reduction_potential
    enriched["remediation_priority"] = classify_remediation_priority(reduction_potential)
    return enriched


def _highest_leverage_row(
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
) -> dict[str, Any] | None:
    candidates = [dict(row) for row in (rows or ()) if isinstance(row, Mapping)]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            float(row.get("reduction_potential") or 0.0),
            float(row.get("risk_share") or 0.0),
            str(row.get(label_field) or ""),
        ),
    )


def summarize_recurrence_remediation_opportunities(
    targets: Mapping[str, Any] | None,
    *,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize highest-leverage remediation opportunities across protected recurrence targets."""
    source = targets if isinstance(targets, Mapping) else {}
    portfolio_summary = (
        recurrence_portfolio_summary
        if isinstance(recurrence_portfolio_summary, Mapping)
        else {}
    )
    keys = [dict(row) for row in (source.get("keys") or ()) if isinstance(row, Mapping)]
    owners = [dict(row) for row in (source.get("owners") or ()) if isinstance(row, Mapping)]
    field_paths = [dict(row) for row in (source.get("field_paths") or ()) if isinstance(row, Mapping)]
    scenarios = [dict(row) for row in (source.get("scenarios") or ()) if isinstance(row, Mapping)]
    total_observations = int(source.get("total_observations") or 0)
    forecast_confidence = float(portfolio_summary.get("forecast_confidence") or 0.0)
    remediation_confidence = _remediation_confidence(
        forecast_confidence=forecast_confidence,
        total_observations=total_observations,
    )
    top_key = _highest_leverage_row(keys, label_field="recurrence_key")
    top_owner = _highest_leverage_row(owners, label_field="owner")
    top_field_path = _highest_leverage_row(field_paths, label_field="field_path")
    top_scenario = _highest_leverage_row(scenarios, label_field="scenario_id")
    top_reduction = float(top_key.get("reduction_potential") or 0.0) if top_key else 0.0
    estimated_portfolio_reduction = round(top_reduction * remediation_confidence, 1)
    highest_leverage_target = None
    if top_key:
        highest_leverage_target = {
            "dimension": "key",
            "label": top_key.get("recurrence_key"),
            "reduction_potential": top_key.get("reduction_potential"),
            "remediation_priority": top_key.get("remediation_priority"),
        }
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "highest_leverage_key": top_key.get("recurrence_key") if top_key else None,
        "highest_leverage_owner": top_owner.get("owner") if top_owner else None,
        "highest_leverage_field_path": top_field_path.get("field_path") if top_field_path else None,
        "highest_leverage_scenario": top_scenario.get("scenario_id") if top_scenario else None,
        "highest_leverage_target": highest_leverage_target,
        "owner_reduction_opportunity": float(top_owner.get("reduction_potential") or 0.0) if top_owner else 0.0,
        "field_path_reduction_opportunity": (
            float(top_field_path.get("reduction_potential") or 0.0) if top_field_path else 0.0
        ),
        "scenario_reduction_opportunity": (
            float(top_scenario.get("reduction_potential") or 0.0) if top_scenario else 0.0
        ),
        "estimated_portfolio_reduction": estimated_portfolio_reduction,
        "remediation_confidence": remediation_confidence,
        "estimated_portfolio_reduction_definition": RECURRENCE_ESTIMATED_PORTFOLIO_REDUCTION_DEFINITION,
        "remediation_confidence_definition": RECURRENCE_REMEDIATION_CONFIDENCE_DEFINITION,
    }


def build_recurrence_remediation_targets(
    *,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_timeline: Sequence[Mapping[str, Any]] | None = None,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence remediation target rankings."""
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    timeline = _timeline_rows(recurrence_timeline)
    if not timeline and event_log is not None:
        timeline = build_recurrence_timeline(event_log, policy=policy)
    if not forecast and event_log is not None:
        forecast = build_recurrence_forecast(
            recurrence_timeline=timeline,
            recurrence_trends=trends,
            event_log=event_log,
            policy=policy,
        )
    if not portfolio and event_log is not None:
        portfolio = build_recurrence_portfolio(
            recurrence_timeline=timeline,
            recurrence_trends=trends,
            recurrence_forecast=forecast,
            event_log=event_log,
            policy=policy,
        )
    catalog = _portfolio_key_catalog(
        recurrence_timeline=timeline,
        recurrence_forecast=forecast,
        event_log=event_log,
        policy=policy,
    )
    if not catalog and isinstance(recurrence_history, Mapping):
        for entry in recurrence_history.get("recurrences") or ():
            if not isinstance(entry, Mapping):
                continue
            key = str(entry.get("recurrence_key") or "").strip()
            if not key:
                continue
            catalog.append(
                {
                    "recurrence_key": key,
                    "owner": str(entry.get("owner") or "unknown"),
                    "category": (entry.get("categories") or ["unknown"])[0]
                    if isinstance(entry.get("categories"), list) and entry.get("categories")
                    else "unknown",
                    "field_path": (entry.get("field_paths") or ["unknown"])[0]
                    if isinstance(entry.get("field_paths"), list) and entry.get("field_paths")
                    else "unknown",
                    "scenarios": list(entry.get("affected_scenarios") or ["(null)"]),
                    "occurrence_count": int(entry.get("occurrence_count") or 0),
                    "trend_classification": RECURRENCE_TREND_CLASSIFICATION_EMERGING,
                    "forecast_classification": RECURRENCE_FORECAST_WATCH,
                }
            )

    total_observations = int(portfolio.get("total_observations") or 0)
    if total_observations <= 0:
        total_observations = sum(int(entry.get("occurrence_count") or 0) for entry in catalog)
    concentration_max = _portfolio_concentration_max(portfolio)
    forecast_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (forecast.get("key_forecasts") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }

    keys: list[dict[str, Any]] = []
    for entry in catalog:
        key = str(entry.get("recurrence_key") or "")
        forecast_row = forecast_by_key.get(key, {})
        observations = int(entry.get("occurrence_count") or 0)
        risk_share = (observations / total_observations) if total_observations else 0.0
        trend_classification = str(
            entry.get("trend_classification")
            or forecast_row.get("trend_classification")
            or RECURRENCE_TREND_CLASSIFICATION_EMERGING
        )
        forecast_classification = str(
            entry.get("forecast_classification")
            or forecast_row.get("forecast_classification")
            or RECURRENCE_FORECAST_WATCH
        )
        concentration_contribution = round(risk_share * concentration_max, 4)
        reduction_potential = calculate_recurrence_reduction_potential(
            risk_share=risk_share,
            occurrence_count=observations,
            total_observations=total_observations,
            trend_classification=trend_classification,
            forecast_classification=forecast_classification,
            concentration_contribution=concentration_contribution,
        )
        keys.append(
            {
                "recurrence_key": key,
                "observations": observations,
                "trend_classification": trend_classification,
                "forecast_classification": forecast_classification,
                "risk_share": round(risk_share, 4),
                "reduction_potential": reduction_potential,
                "remediation_priority": classify_remediation_priority(reduction_potential),
            }
        )
    keys.sort(
        key=lambda row: (
            -float(row.get("reduction_potential") or 0.0),
            -float(row.get("risk_share") or 0.0),
            str(row.get("recurrence_key") or ""),
        )
    )

    def _aggregate_owner_forecast(owner_name: str) -> tuple[str, str]:
        owner_entries = [entry for entry in catalog if str(entry.get("owner") or "") == owner_name]
        if not owner_entries:
            return RECURRENCE_TREND_CLASSIFICATION_EMERGING, RECURRENCE_FORECAST_WATCH
        trend = max(
            owner_entries,
            key=lambda entry: (
                RECURRENCE_TREND_REDUCTION_WEIGHTS.get(str(entry.get("trend_classification") or ""), 0.0),
                int(entry.get("occurrence_count") or 0),
            ),
        )
        forecast = max(
            owner_entries,
            key=lambda entry: (
                RECURRENCE_FORECAST_REDUCTION_WEIGHTS.get(str(entry.get("forecast_classification") or ""), 0.0),
                int(entry.get("occurrence_count") or 0),
            ),
        )
        return (
            str(trend.get("trend_classification") or RECURRENCE_TREND_CLASSIFICATION_EMERGING),
            str(forecast.get("forecast_classification") or RECURRENCE_FORECAST_WATCH),
        )

    owners = []
    for bucket in portfolio.get("owners") or ():
        if not isinstance(bucket, Mapping):
            continue
        owner_name = str(bucket.get("owner") or "unknown")
        trend_classification, forecast_classification = _aggregate_owner_forecast(owner_name)
        owners.append(
            _enrich_remediation_bucket(
                bucket,
                total_observations=total_observations,
                concentration_max=concentration_max,
                trend_classification=trend_classification,
                forecast_classification=forecast_classification,
            )
        )
    owners.sort(
        key=lambda row: (
            -float(row.get("reduction_potential") or 0.0),
            str(row.get("owner") or ""),
        )
    )

    field_paths = []
    for bucket in portfolio.get("field_paths") or ():
        if not isinstance(bucket, Mapping):
            continue
        field_path = str(bucket.get("field_path") or "unknown")
        matching = [entry for entry in catalog if str(entry.get("field_path") or "") == field_path]
        trend_classification = (
            str(matching[0].get("trend_classification") or RECURRENCE_TREND_CLASSIFICATION_EMERGING)
            if matching
            else RECURRENCE_TREND_CLASSIFICATION_EMERGING
        )
        forecast_classification = (
            str(matching[0].get("forecast_classification") or RECURRENCE_FORECAST_WATCH)
            if matching
            else RECURRENCE_FORECAST_WATCH
        )
        field_paths.append(
            _enrich_remediation_bucket(
                bucket,
                total_observations=total_observations,
                concentration_max=concentration_max,
                trend_classification=trend_classification,
                forecast_classification=forecast_classification,
            )
        )
    field_paths.sort(
        key=lambda row: (
            -float(row.get("reduction_potential") or 0.0),
            str(row.get("field_path") or ""),
        )
    )

    scenarios = []
    for bucket in portfolio.get("scenarios") or ():
        if not isinstance(bucket, Mapping):
            continue
        scenario_id = str(bucket.get("scenario_id") or "(null)")
        matching = [
            entry
            for entry in catalog
            if scenario_id in {str(item) for item in (entry.get("scenarios") or [])}
        ]
        trend_classification = (
            str(matching[0].get("trend_classification") or RECURRENCE_TREND_CLASSIFICATION_EMERGING)
            if matching
            else RECURRENCE_TREND_CLASSIFICATION_EMERGING
        )
        forecast_classification = (
            str(matching[0].get("forecast_classification") or RECURRENCE_FORECAST_WATCH)
            if matching
            else RECURRENCE_FORECAST_WATCH
        )
        scenarios.append(
            _enrich_remediation_bucket(
                bucket,
                total_observations=total_observations,
                concentration_max=concentration_max,
                trend_classification=trend_classification,
                forecast_classification=forecast_classification,
            )
        )
    scenarios.sort(
        key=lambda row: (
            -float(row.get("reduction_potential") or 0.0),
            str(row.get("scenario_id") or ""),
        )
    )

    portfolio_summary = portfolio.get("portfolio_summary")
    if not isinstance(portfolio_summary, Mapping):
        portfolio_summary = summarize_recurrence_portfolio(portfolio, recurrence_forecast=forecast)
    targets_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "reduction_potential_definition": RECURRENCE_REDUCTION_POTENTIAL_DEFINITION,
        "remediation_priority_definition": RECURRENCE_REMEDIATION_PRIORITY_DEFINITION,
        "total_observations": total_observations,
        "total_keys": len(keys),
        "keys": keys,
        "owners": owners,
        "field_paths": field_paths,
        "scenarios": scenarios,
        "highest_leverage_owner": _highest_leverage_row(owners, label_field="owner"),
        "highest_leverage_field_path": _highest_leverage_row(field_paths, label_field="field_path"),
        "highest_leverage_scenario": _highest_leverage_row(scenarios, label_field="scenario_id"),
    }
    remediation_summary = summarize_recurrence_remediation_opportunities(
        targets_without_summary,
        recurrence_portfolio_summary=portfolio_summary,
    )
    top_owner = targets_without_summary["highest_leverage_owner"]
    top_field_path = targets_without_summary["highest_leverage_field_path"]
    top_scenario = targets_without_summary["highest_leverage_scenario"]
    return {
        **targets_without_summary,
        "owner_reduction_opportunity": (
            float(top_owner.get("reduction_potential") or 0.0) if isinstance(top_owner, Mapping) else 0.0
        ),
        "field_path_reduction_opportunity": (
            float(top_field_path.get("reduction_potential") or 0.0)
            if isinstance(top_field_path, Mapping)
            else 0.0
        ),
        "scenario_reduction_opportunity": (
            float(top_scenario.get("reduction_potential") or 0.0)
            if isinstance(top_scenario, Mapping)
            else 0.0
        ),
        "remediation_summary": remediation_summary,
    }


def enrich_recurrence_history_with_remediation(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay remediation target fields."""
    payload = dict(history)
    targets = build_recurrence_remediation_targets(
        recurrence_portfolio=payload.get("recurrence_portfolio")
        if isinstance(payload.get("recurrence_portfolio"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_timeline=payload.get("recurrence_timeline")
        if isinstance(payload.get("recurrence_timeline"), list)
        else None,
        event_log=event_log,
        policy=policy,
    )
    payload["recurrence_remediation_targets"] = targets
    payload["recurrence_remediation_summary"] = targets["remediation_summary"]
    return payload


RECURRENCE_REMEDIATION_COST_TRIVIAL = "trivial"
RECURRENCE_REMEDIATION_COST_LOW = "low"
RECURRENCE_REMEDIATION_COST_MEDIUM = "medium"
RECURRENCE_REMEDIATION_COST_HIGH = "high"
RECURRENCE_REMEDIATION_COST_CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        RECURRENCE_REMEDIATION_COST_TRIVIAL,
        RECURRENCE_REMEDIATION_COST_LOW,
        RECURRENCE_REMEDIATION_COST_MEDIUM,
        RECURRENCE_REMEDIATION_COST_HIGH,
    }
)
RECURRENCE_REMEDIATION_COST_THRESHOLDS: tuple[tuple[str, float], ...] = (
    (RECURRENCE_REMEDIATION_COST_TRIVIAL, 20.0),
    (RECURRENCE_REMEDIATION_COST_LOW, 40.0),
    (RECURRENCE_REMEDIATION_COST_MEDIUM, 70.0),
    (RECURRENCE_REMEDIATION_COST_HIGH, 100.0),
)
RECURRENCE_REMEDIATION_COST_FLOOR = 5.0
RECURRENCE_REMEDIATION_COST_DEFINITION = (
    "Advisory 0-100 estimate: 25% key_scope + 25% owner_dispersion + 20% field_path_dispersion + "
    "15% scenario_scope + 15% recurrence_depth, where key_scope is "
    "min(1, recurrence_keys / max(total_keys, 1)), owner_dispersion is 1 - owner_concentration_ratio, "
    "field_path_dispersion is 1 - field_path_concentration_ratio, scenario_scope is min(1, scenario_count / 5), "
    "and recurrence_depth is min(1, observations / 10). Higher concentration lowers cost; broader scope raises it."
)
RECURRENCE_ROI_SCORE_DEFINITION = (
    "Advisory 0-100 score: min(100, 100 * expected_benefit / max(estimated_remediation_cost, 5)), "
    "where expected_benefit is reduction_potential multiplied by remediation_confidence. "
    "Higher scores indicate better expected return on remediation investment."
)
RECURRENCE_ROI_CONFIDENCE_DEFINITION = (
    "Weighted blend of forecast_confidence (35%), remediation_confidence (35%), and "
    "observation volume factor min(1, total_observations / 5) (30%)."
)
RECURRENCE_PROJECTED_IMPROVEMENT_DEFINITION = (
    "projected_recurrence_reduction is expected_benefit; projected_risk_reduction is "
    "expected_benefit multiplied by portfolio_risk_score / 100; projected_stability_improvement is "
    "expected_benefit multiplied by (100 - stability_score) / 100."
)


def classify_remediation_cost(estimated_remediation_cost: float) -> str:
    """Map estimated remediation cost to a deterministic cost classification."""
    score = float(estimated_remediation_cost or 0.0)
    for label, threshold in RECURRENCE_REMEDIATION_COST_THRESHOLDS:
        if score < threshold:
            return label
    return RECURRENCE_REMEDIATION_COST_HIGH


def calculate_estimated_remediation_cost(
    *,
    owner_concentration_ratio: float,
    field_path_concentration_ratio: float,
    recurrence_keys: int,
    scenario_count: int,
    recurrence_count: int,
    total_keys: int,
) -> float:
    """Return advisory 0-100 deterministic remediation cost for one protected replay target."""
    keys = max(int(recurrence_keys or 0), 0)
    total = max(int(total_keys or 0), 1)
    observations = max(int(recurrence_count or 0), 0)
    scenarios = max(int(scenario_count or 0), 0)
    owner_concentration = max(min(float(owner_concentration_ratio or 0.0), 1.0), 0.0)
    field_path_concentration = max(min(float(field_path_concentration_ratio or 0.0), 1.0), 0.0)
    key_scope = min(1.0, keys / float(total))
    owner_dispersion = 1.0 - owner_concentration
    field_path_dispersion = 1.0 - field_path_concentration
    scenario_scope = min(1.0, scenarios / 5.0)
    recurrence_depth = min(1.0, observations / 10.0)
    blended = (
        0.25 * key_scope
        + 0.25 * owner_dispersion
        + 0.20 * field_path_dispersion
        + 0.15 * scenario_scope
        + 0.15 * recurrence_depth
    )
    return round(max(RECURRENCE_REMEDIATION_COST_FLOOR, min(100.0, 100.0 * blended)), 1)


def _roi_confidence(
    *,
    forecast_confidence: float,
    remediation_confidence: float,
    total_observations: int,
) -> float:
    observations = max(int(total_observations or 0), 0)
    volume_factor = min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS))
    return round(
        0.35 * float(forecast_confidence or 0.0)
        + 0.35 * float(remediation_confidence or 0.0)
        + 0.30 * volume_factor,
        2,
    )


def calculate_recurrence_roi(
    *,
    reduction_potential: float,
    remediation_confidence: float,
    estimated_remediation_cost: float,
    portfolio_risk_score: float = 0.0,
    stability_score: float = 100.0,
) -> dict[str, Any]:
    """Return projected improvements and ROI score for one remediation target."""
    expected_benefit = round(float(reduction_potential or 0.0) * float(remediation_confidence or 0.0), 1)
    cost = max(float(estimated_remediation_cost or 0.0), RECURRENCE_REMEDIATION_COST_FLOOR)
    roi_score = round(min(100.0, 100.0 * expected_benefit / cost), 1)
    risk_score = max(min(float(portfolio_risk_score or 0.0), 100.0), 0.0)
    stability = max(min(float(stability_score or 0.0), 100.0), 0.0)
    projected_recurrence_reduction = expected_benefit
    projected_risk_reduction = round(expected_benefit * risk_score / 100.0, 1)
    projected_stability_improvement = round(expected_benefit * (100.0 - stability) / 100.0, 1)
    return {
        "expected_benefit": expected_benefit,
        "expected_portfolio_reduction": expected_benefit,
        "estimated_remediation_cost": round(cost, 1),
        "cost_classification": classify_remediation_cost(cost),
        "projected_recurrence_reduction": projected_recurrence_reduction,
        "projected_risk_reduction": projected_risk_reduction,
        "projected_stability_improvement": projected_stability_improvement,
        "roi_score": roi_score,
    }


def _enrich_roi_bucket(
    bucket: Mapping[str, Any],
    *,
    owner_concentration_ratio: float,
    field_path_concentration_ratio: float,
    total_keys: int,
    remediation_confidence: float,
    portfolio_risk_score: float,
    stability_score: float,
    scenario_count: int | None = None,
) -> dict[str, Any]:
    enriched = dict(bucket)
    recurrence_keys = int(enriched.get("recurrence_keys") or 1)
    observations = int(enriched.get("observations") or 0)
    scenarios = scenario_count if scenario_count is not None else recurrence_keys
    estimated_cost = calculate_estimated_remediation_cost(
        owner_concentration_ratio=owner_concentration_ratio,
        field_path_concentration_ratio=field_path_concentration_ratio,
        recurrence_keys=recurrence_keys,
        scenario_count=scenarios,
        recurrence_count=observations,
        total_keys=total_keys,
    )
    roi_metrics = calculate_recurrence_roi(
        reduction_potential=float(enriched.get("reduction_potential") or 0.0),
        remediation_confidence=remediation_confidence,
        estimated_remediation_cost=estimated_cost,
        portfolio_risk_score=portfolio_risk_score,
        stability_score=stability_score,
    )
    enriched.update(roi_metrics)
    return enriched


def _highest_roi_row(
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
) -> dict[str, Any] | None:
    candidates = [dict(row) for row in (rows or ()) if isinstance(row, Mapping)]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            float(row.get("roi_score") or 0.0),
            float(row.get("expected_benefit") or 0.0),
            str(row.get(label_field) or ""),
        ),
    )


def _rank_roi_rows(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    ranked = sorted(
        [dict(row) for row in (rows or ()) if isinstance(row, Mapping)],
        key=lambda row: (
            -float(row.get("roi_score") or 0.0),
            -float(row.get("expected_benefit") or 0.0),
        ),
    )
    for index, row in enumerate(ranked, start=1):
        row["roi_rank"] = index
    return ranked


def summarize_recurrence_roi(
    analysis: Mapping[str, Any] | None,
    *,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_remediation_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence ROI across remediation dimensions."""
    source = analysis if isinstance(analysis, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    portfolio_summary = (
        recurrence_portfolio_summary
        if isinstance(recurrence_portfolio_summary, Mapping)
        else {}
    )
    remediation_summary = (
        recurrence_remediation_summary
        if isinstance(recurrence_remediation_summary, Mapping)
        else {}
    )
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    total_observations = int(source.get("total_observations") or 0)
    forecast_confidence = float(portfolio_summary.get("forecast_confidence") or 0.0)
    remediation_confidence = float(
        remediation_summary.get("remediation_confidence")
        or source.get("remediation_confidence")
        or 0.0
    )
    roi_confidence = _roi_confidence(
        forecast_confidence=forecast_confidence,
        remediation_confidence=remediation_confidence,
        total_observations=total_observations,
    )
    keys = [dict(row) for row in (source.get("keys") or ()) if isinstance(row, Mapping)]
    owners = [dict(row) for row in (source.get("owners") or ()) if isinstance(row, Mapping)]
    field_paths = [dict(row) for row in (source.get("field_paths") or ()) if isinstance(row, Mapping)]
    scenarios = [dict(row) for row in (source.get("scenarios") or ()) if isinstance(row, Mapping)]
    top_key = _highest_roi_row(keys, label_field="recurrence_key")
    top_owner = _highest_roi_row(owners, label_field="owner")
    top_field_path = _highest_roi_row(field_paths, label_field="field_path")
    top_scenario = _highest_roi_row(scenarios, label_field="scenario_id")
    highest_roi_target = None
    if top_key:
        highest_roi_target = {
            "dimension": "key",
            "label": top_key.get("recurrence_key"),
            "roi_score": top_key.get("roi_score"),
            "cost_classification": top_key.get("cost_classification"),
            "expected_benefit": top_key.get("expected_benefit"),
        }
    portfolio_roi_score = float(top_key.get("roi_score") or 0.0) if top_key else 0.0
    projected_stability_gain = float(top_key.get("projected_stability_improvement") or 0.0) if top_key else 0.0
    projected_risk_reduction = float(top_key.get("projected_risk_reduction") or 0.0) if top_key else 0.0
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "highest_roi_target": highest_roi_target,
        "highest_roi_owner": top_owner.get("owner") if top_owner else None,
        "highest_roi_field_path": top_field_path.get("field_path") if top_field_path else None,
        "highest_roi_scenario": top_scenario.get("scenario_id") if top_scenario else None,
        "projected_stability_gain": projected_stability_gain,
        "projected_risk_reduction": projected_risk_reduction,
        "portfolio_roi_score": portfolio_roi_score,
        "roi_confidence": roi_confidence,
        "estimated_remediation_cost_definition": RECURRENCE_REMEDIATION_COST_DEFINITION,
        "roi_score_definition": RECURRENCE_ROI_SCORE_DEFINITION,
        "roi_confidence_definition": RECURRENCE_ROI_CONFIDENCE_DEFINITION,
        "projected_improvement_definition": RECURRENCE_PROJECTED_IMPROVEMENT_DEFINITION,
    }


def build_recurrence_roi_analysis(
    *,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence ROI analysis from remediation and portfolio inputs."""
    targets = recurrence_remediation_targets if isinstance(recurrence_remediation_targets, Mapping) else {}
    if not targets and event_log is not None:
        targets = build_recurrence_remediation_targets(
            recurrence_forecast=recurrence_forecast if isinstance(recurrence_forecast, Mapping) else None,
            recurrence_portfolio=recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else None,
            recurrence_history=recurrence_history if isinstance(recurrence_history, Mapping) else None,
            event_log=event_log,
            policy=policy,
        )
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    if not portfolio and event_log is not None:
        portfolio = build_recurrence_portfolio(
            recurrence_forecast=forecast if forecast else None,
            event_log=event_log,
            policy=policy,
        )
    if not forecast and event_log is not None:
        forecast = build_recurrence_forecast(event_log=event_log, policy=policy)

    portfolio_summary = portfolio.get("portfolio_summary")
    if not isinstance(portfolio_summary, Mapping):
        portfolio_summary = summarize_recurrence_portfolio(portfolio, recurrence_forecast=forecast)
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    remediation_summary = targets.get("remediation_summary")
    if not isinstance(remediation_summary, Mapping):
        remediation_summary = summarize_recurrence_remediation_opportunities(
            targets,
            recurrence_portfolio_summary=portfolio_summary,
        )

    total_observations = int(targets.get("total_observations") or portfolio.get("total_observations") or 0)
    total_keys = int(targets.get("total_keys") or portfolio.get("total_keys") or 0)
    owner_concentration = float(portfolio.get("owner_concentration_ratio") or 0.0)
    field_path_concentration = float(portfolio.get("field_path_concentration_ratio") or 0.0)
    portfolio_risk_score = float(portfolio_summary.get("portfolio_risk_score") or 0.0)
    stability_score = float(forecast_summary.get("stability_score") or 100.0)
    remediation_confidence = float(remediation_summary.get("remediation_confidence") or 0.0)

    keys = []
    for bucket in targets.get("keys") or ():
        if not isinstance(bucket, Mapping):
            continue
        keys.append(
            _enrich_roi_bucket(
                bucket,
                owner_concentration_ratio=owner_concentration,
                field_path_concentration_ratio=field_path_concentration,
                total_keys=max(total_keys, 1),
                remediation_confidence=remediation_confidence,
                portfolio_risk_score=portfolio_risk_score,
                stability_score=stability_score,
                scenario_count=1,
            )
        )

    owners = []
    for bucket in targets.get("owners") or ():
        if not isinstance(bucket, Mapping):
            continue
        owners.append(
            _enrich_roi_bucket(
                bucket,
                owner_concentration_ratio=owner_concentration,
                field_path_concentration_ratio=field_path_concentration,
                total_keys=max(total_keys, 1),
                remediation_confidence=remediation_confidence,
                portfolio_risk_score=portfolio_risk_score,
                stability_score=stability_score,
                scenario_count=int(bucket.get("recurrence_keys") or 1),
            )
        )

    field_paths = []
    for bucket in targets.get("field_paths") or ():
        if not isinstance(bucket, Mapping):
            continue
        field_paths.append(
            _enrich_roi_bucket(
                bucket,
                owner_concentration_ratio=owner_concentration,
                field_path_concentration_ratio=field_path_concentration,
                total_keys=max(total_keys, 1),
                remediation_confidence=remediation_confidence,
                portfolio_risk_score=portfolio_risk_score,
                stability_score=stability_score,
                scenario_count=int(bucket.get("recurrence_keys") or 1),
            )
        )

    scenarios = []
    for bucket in targets.get("scenarios") or ():
        if not isinstance(bucket, Mapping):
            continue
        scenarios.append(
            _enrich_roi_bucket(
                bucket,
                owner_concentration_ratio=owner_concentration,
                field_path_concentration_ratio=field_path_concentration,
                total_keys=max(total_keys, 1),
                remediation_confidence=remediation_confidence,
                portfolio_risk_score=portfolio_risk_score,
                stability_score=stability_score,
                scenario_count=1,
            )
        )

    keys = _rank_roi_rows(keys)
    owners = _rank_roi_rows(owners)
    field_paths = _rank_roi_rows(field_paths)
    scenarios = _rank_roi_rows(scenarios)

    analysis_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "estimated_remediation_cost_definition": RECURRENCE_REMEDIATION_COST_DEFINITION,
        "roi_score_definition": RECURRENCE_ROI_SCORE_DEFINITION,
        "projected_improvement_definition": RECURRENCE_PROJECTED_IMPROVEMENT_DEFINITION,
        "total_observations": total_observations,
        "total_keys": total_keys,
        "remediation_confidence": remediation_confidence,
        "keys": keys,
        "owners": owners,
        "field_paths": field_paths,
        "scenarios": scenarios,
        "highest_roi_key": _highest_roi_row(keys, label_field="recurrence_key"),
        "highest_roi_owner": _highest_roi_row(owners, label_field="owner"),
        "highest_roi_field_path": _highest_roi_row(field_paths, label_field="field_path"),
        "highest_roi_scenario": _highest_roi_row(scenarios, label_field="scenario_id"),
    }
    roi_summary = summarize_recurrence_roi(
        analysis_without_summary,
        recurrence_forecast=forecast,
        recurrence_portfolio_summary=portfolio_summary,
        recurrence_remediation_summary=remediation_summary,
    )
    return {
        **analysis_without_summary,
        "roi_summary": roi_summary,
    }


def enrich_recurrence_history_with_roi(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay ROI analytics fields."""
    payload = dict(history)
    analysis = build_recurrence_roi_analysis(
        recurrence_remediation_targets=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_portfolio=payload.get("recurrence_portfolio")
        if isinstance(payload.get("recurrence_portfolio"), Mapping)
        else None,
        recurrence_history=payload,
        event_log=event_log,
        policy=policy,
    )
    payload["recurrence_roi"] = analysis
    payload["recurrence_roi_summary"] = analysis["roi_summary"]
    return payload


RECURRENCE_GOVERNANCE_OBSERVE = "observe"
RECURRENCE_GOVERNANCE_WATCH = "watch"
RECURRENCE_GOVERNANCE_INVESTIGATE = "investigate"
RECURRENCE_GOVERNANCE_PRIORITIZE = "prioritize"
RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE = "retire_candidate"
RECURRENCE_GOVERNANCE_STATUSES: frozenset[str] = frozenset(
    {
        RECURRENCE_GOVERNANCE_OBSERVE,
        RECURRENCE_GOVERNANCE_WATCH,
        RECURRENCE_GOVERNANCE_INVESTIGATE,
        RECURRENCE_GOVERNANCE_PRIORITIZE,
        RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE,
    }
)
RECURRENCE_GOVERNANCE_ACTION_CONTINUE_OBSERVATION = "continue_observation"
RECURRENCE_GOVERNANCE_ACTION_GATHER_HISTORY = "gather_more_history"
RECURRENCE_GOVERNANCE_ACTION_INVESTIGATE = "investigate_root_cause"
RECURRENCE_GOVERNANCE_ACTION_PRIORITIZE = "prioritize_remediation"
RECURRENCE_GOVERNANCE_ACTION_RETIRE = "retire_tracking"
RECURRENCE_GOVERNANCE_ACTIONS: frozenset[str] = frozenset(
    {
        RECURRENCE_GOVERNANCE_ACTION_CONTINUE_OBSERVATION,
        RECURRENCE_GOVERNANCE_ACTION_GATHER_HISTORY,
        RECURRENCE_GOVERNANCE_ACTION_INVESTIGATE,
        RECURRENCE_GOVERNANCE_ACTION_PRIORITIZE,
        RECURRENCE_GOVERNANCE_ACTION_RETIRE,
    }
)
RECURRENCE_GOVERNANCE_WATCH_THRESHOLD = 0.0
RECURRENCE_GOVERNANCE_INVESTIGATE_THRESHOLD = 50.0
RECURRENCE_GOVERNANCE_PRIORITIZE_THRESHOLD = 25.0
RECURRENCE_GOVERNANCE_RETIRE_THRESHOLD = 0.0
RECURRENCE_GOVERNANCE_PRIORITIZE_ROI_CONFIDENCE_THRESHOLD = 0.15
RECURRENCE_GOVERNANCE_STATUS_DEFINITIONS: dict[str, str] = {
    RECURRENCE_GOVERNANCE_OBSERVE: "Limited evidence; continue passive monitoring without escalation.",
    RECURRENCE_GOVERNANCE_WATCH: "Emerging recurrence or watch forecast; gather more protected history.",
    RECURRENCE_GOVERNANCE_INVESTIGATE: "Elevated or concentrated recurrence risk warrants root-cause review.",
    RECURRENCE_GOVERNANCE_PRIORITIZE: "Strong ROI and actionable leverage; prioritize remediation work.",
    RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE: "Dormant recurrence with no recent activity; candidate to retire tracking.",
}
RECURRENCE_GOVERNANCE_STATUS_CLASSIFICATION_DEFINITION = (
    "Deterministic priority order: retire_candidate when trend is dormant or status is retired; "
    "prioritize when roi_score >= prioritize_threshold (25), roi_confidence >= 0.15, and "
    "reduction_potential >= investigate_threshold (50); investigate when forecast is elevated/concentrated, "
    "trend is recurring/persistent, reduction_potential >= investigate_threshold (50) with non-emerging trend, "
    "or recurrence_rate >= 0.5 with at least two observations; watch when trend is emerging or forecast is watch; "
    "otherwise observe."
)
RECURRENCE_GOVERNANCE_HEALTH_SCORE_DEFINITION = (
    "Advisory 0-100 score: 30% stability_score/100 + 25% (1 - portfolio_risk_score/100) + "
    "20% (1 - watchlist_size/max(total_keys, 1)) + 15% (1 - prioritized_targets/max(total_keys, 1)) + "
    "10% (1 - regression_recurrence_rate). Higher scores indicate healthier governance posture."
)
RECURRENCE_GOVERNANCE_CONFIDENCE_DEFINITION = (
    "Weighted blend of roi_confidence (40%), forecast_confidence (35%), and observation volume "
    "factor min(1, total_observations / 5) (25%)."
)
RECURRENCE_GOVERNANCE_STATUS_TO_ACTION: dict[str, str] = {
    RECURRENCE_GOVERNANCE_OBSERVE: RECURRENCE_GOVERNANCE_ACTION_CONTINUE_OBSERVATION,
    RECURRENCE_GOVERNANCE_WATCH: RECURRENCE_GOVERNANCE_ACTION_GATHER_HISTORY,
    RECURRENCE_GOVERNANCE_INVESTIGATE: RECURRENCE_GOVERNANCE_ACTION_INVESTIGATE,
    RECURRENCE_GOVERNANCE_PRIORITIZE: RECURRENCE_GOVERNANCE_ACTION_PRIORITIZE,
    RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE: RECURRENCE_GOVERNANCE_ACTION_RETIRE,
}


def _governance_intervention_thresholds() -> dict[str, float]:
    return {
        "watch_threshold": RECURRENCE_GOVERNANCE_WATCH_THRESHOLD,
        "investigate_threshold": RECURRENCE_GOVERNANCE_INVESTIGATE_THRESHOLD,
        "prioritize_threshold": RECURRENCE_GOVERNANCE_PRIORITIZE_THRESHOLD,
        "retire_threshold": RECURRENCE_GOVERNANCE_RETIRE_THRESHOLD,
        "prioritize_roi_confidence_threshold": RECURRENCE_GOVERNANCE_PRIORITIZE_ROI_CONFIDENCE_THRESHOLD,
    }


def classify_recurrence_governance_status(
    *,
    trend_classification: str,
    forecast_classification: str,
    reduction_potential: float,
    roi_score: float,
    roi_confidence: float,
    recurrence_rate: float = 0.0,
    total_observations: int = 0,
    recurrence_status: str = "active",
) -> str:
    """Classify one protected recurrence key into a deterministic governance status."""
    trend = str(trend_classification or "").strip()
    forecast = str(forecast_classification or "").strip()
    status = str(recurrence_status or "active").strip().lower()
    thresholds = _governance_intervention_thresholds()

    if trend == RECURRENCE_TREND_CLASSIFICATION_DORMANT or status in {"retired", "deprecated"}:
        return RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE

    if (
        float(roi_score or 0.0) >= thresholds["prioritize_threshold"]
        and float(roi_confidence or 0.0) >= thresholds["prioritize_roi_confidence_threshold"]
        and float(reduction_potential or 0.0) >= thresholds["investigate_threshold"]
    ):
        return RECURRENCE_GOVERNANCE_PRIORITIZE

    if (
        forecast in {RECURRENCE_FORECAST_ELEVATED, RECURRENCE_FORECAST_CONCENTRATED}
        or trend in {
            RECURRENCE_TREND_CLASSIFICATION_RECURRING,
            RECURRENCE_TREND_CLASSIFICATION_PERSISTENT,
        }
        or (
            float(reduction_potential or 0.0) >= thresholds["investigate_threshold"]
            and trend != RECURRENCE_TREND_CLASSIFICATION_EMERGING
        )
        or (
            float(recurrence_rate or 0.0) >= 0.5
            and max(int(total_observations or 0), 0) >= 2
        )
    ):
        return RECURRENCE_GOVERNANCE_INVESTIGATE

    if (
        trend == RECURRENCE_TREND_CLASSIFICATION_EMERGING
        or forecast == RECURRENCE_FORECAST_WATCH
    ):
        return RECURRENCE_GOVERNANCE_WATCH

    return RECURRENCE_GOVERNANCE_OBSERVE


def _recommended_action_for_governance_status(governance_status: str) -> str:
    return RECURRENCE_GOVERNANCE_STATUS_TO_ACTION.get(
        str(governance_status or "").strip(),
        RECURRENCE_GOVERNANCE_ACTION_CONTINUE_OBSERVATION,
    )


def _governance_confidence(
    *,
    roi_confidence: float,
    forecast_confidence: float,
    total_observations: int,
) -> float:
    observations = max(int(total_observations or 0), 0)
    volume_factor = min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS))
    return round(
        0.40 * float(roi_confidence or 0.0)
        + 0.35 * float(forecast_confidence or 0.0)
        + 0.25 * volume_factor,
        2,
    )


def _governance_health_score(
    *,
    stability_score: float,
    portfolio_risk_score: float,
    watchlist_size: int,
    prioritized_targets: int,
    total_keys: int,
    regression_recurrence_rate: float,
) -> float:
    keys = max(int(total_keys or 0), 1)
    watch_ratio = min(1.0, int(watchlist_size or 0) / float(keys))
    prioritize_ratio = min(1.0, int(prioritized_targets or 0) / float(keys))
    stability = max(min(float(stability_score or 0.0), 100.0), 0.0)
    risk = max(min(float(portfolio_risk_score or 0.0), 100.0), 0.0)
    regression = max(min(float(regression_recurrence_rate or 0.0), 1.0), 0.0)
    blended = (
        0.30 * (stability / 100.0)
        + 0.25 * (1.0 - risk / 100.0)
        + 0.20 * (1.0 - watch_ratio)
        + 0.15 * (1.0 - prioritize_ratio)
        + 0.10 * (1.0 - regression)
    )
    return round(max(0.0, min(100.0, 100.0 * blended)), 1)


def _governance_status_counts(watchlist: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(RECURRENCE_GOVERNANCE_STATUSES)}
    for entry in watchlist:
        if not isinstance(entry, Mapping):
            continue
        status = str(entry.get("governance_status") or RECURRENCE_GOVERNANCE_OBSERVE).strip()
        if status in counts:
            counts[status] += 1
    return counts


def _build_owner_governance_summary(
    watchlist: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], str | None, dict[str, int]]:
    owners: dict[str, dict[str, int]] = {}
    for entry in watchlist:
        if not isinstance(entry, Mapping):
            continue
        owner = str(entry.get("owner") or "unknown").strip() or "unknown"
        status = str(entry.get("governance_status") or RECURRENCE_GOVERNANCE_OBSERVE).strip()
        bucket = owners.setdefault(
            owner,
            {
                "governed_keys": 0,
                "watch_keys": 0,
                "prioritized_keys": 0,
                "retire_candidates": 0,
            },
        )
        bucket["governed_keys"] += 1
        if status == RECURRENCE_GOVERNANCE_WATCH:
            bucket["watch_keys"] += 1
        elif status == RECURRENCE_GOVERNANCE_PRIORITIZE:
            bucket["prioritized_keys"] += 1
        elif status == RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE:
            bucket["retire_candidates"] += 1

    rows = [
        {"owner": owner, **metrics}
        for owner, metrics in sorted(owners.items())
    ]
    highest_load_owner = None
    if rows:
        highest_load_owner = max(
            rows,
            key=lambda row: (
                int(row.get("prioritized_keys") or 0),
                int(row.get("watch_keys") or 0),
                int(row.get("governed_keys") or 0),
                str(row.get("owner") or ""),
            ),
        ).get("owner")
    distribution = {row["owner"]: int(row["governed_keys"]) for row in rows}
    return rows, highest_load_owner, distribution


def _build_retirement_summary(
    watchlist: Sequence[Mapping[str, Any]],
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    retired_keys = 0
    for entry in history.get("recurrences") or ():
        if not isinstance(entry, Mapping):
            continue
        if classify_recurrence_status(entry) == "retired":
            retired_keys += 1
    status_counts = _governance_status_counts(watchlist)
    dormant_keys = int(trends.get("dormant_keys") or 0)
    retire_candidates = int(status_counts.get(RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE) or 0)
    retirement_opportunities = retire_candidates + dormant_keys
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "dormant_keys": dormant_keys,
        "retire_candidates": retire_candidates,
        "retired_keys": retired_keys,
        "retirement_opportunities": retirement_opportunities,
    }


def summarize_recurrence_governance(
    governance: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence governance posture."""
    source = governance if isinstance(governance, Mapping) else {}
    watchlist = [
        dict(entry)
        for entry in (source.get("watchlist") or ())
        if isinstance(entry, Mapping)
    ]
    status_counts = _governance_status_counts(watchlist)
    owners = source.get("owners")
    if not isinstance(owners, list):
        owners = []
    highest_load_owner = source.get("highest_governance_load_owner")
    if highest_load_owner is None and owners:
        highest_load_owner = owners[0].get("owner")
    retirement = source.get("retirement_summary")
    if not isinstance(retirement, Mapping):
        retirement = {}
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "watchlist_size": len(watchlist),
        "prioritized_targets": int(status_counts.get(RECURRENCE_GOVERNANCE_PRIORITIZE) or 0),
        "retire_candidates": int(status_counts.get(RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE) or 0),
        "highest_governance_load_owner": highest_load_owner,
        "governance_health_score": float(source.get("governance_health_score") or 0.0),
        "governance_confidence": float(source.get("governance_confidence") or 0.0),
        "retirement_opportunities": int(retirement.get("retirement_opportunities") or 0),
        "governance_health_score_definition": RECURRENCE_GOVERNANCE_HEALTH_SCORE_DEFINITION,
        "governance_confidence_definition": RECURRENCE_GOVERNANCE_CONFIDENCE_DEFINITION,
        "governance_status_definitions": RECURRENCE_GOVERNANCE_STATUS_DEFINITIONS,
    }


def build_recurrence_governance(
    *,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_timeline: Sequence[Mapping[str, Any]] | None = None,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence governance analytics."""
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    targets = recurrence_remediation_targets if isinstance(recurrence_remediation_targets, Mapping) else {}
    roi = recurrence_roi if isinstance(recurrence_roi, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    timeline = _timeline_rows(recurrence_timeline)

    if not timeline and event_log is not None:
        timeline = build_recurrence_timeline(event_log, policy=policy)
    if not forecast and event_log is not None:
        forecast = build_recurrence_forecast(
            recurrence_timeline=timeline,
            recurrence_trends=trends,
            event_log=event_log,
            policy=policy,
        )
    if not portfolio and event_log is not None:
        portfolio = build_recurrence_portfolio(
            recurrence_timeline=timeline,
            recurrence_trends=trends,
            recurrence_forecast=forecast,
            event_log=event_log,
            policy=policy,
        )
    if not targets and event_log is not None:
        targets = build_recurrence_remediation_targets(
            recurrence_portfolio=portfolio,
            recurrence_forecast=forecast,
            recurrence_trends=trends,
            recurrence_history=history,
            recurrence_timeline=timeline,
            event_log=event_log,
            policy=policy,
        )
    if not roi and event_log is not None:
        roi = build_recurrence_roi_analysis(
            recurrence_remediation_targets=targets,
            recurrence_forecast=forecast,
            recurrence_portfolio=portfolio,
            recurrence_history=history,
            event_log=event_log,
            policy=policy,
        )

    portfolio_summary = portfolio.get("portfolio_summary")
    if not isinstance(portfolio_summary, Mapping):
        portfolio_summary = summarize_recurrence_portfolio(portfolio, recurrence_forecast=forecast)
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    roi_summary = roi.get("roi_summary")
    if not isinstance(roi_summary, Mapping):
        roi_summary = summarize_recurrence_roi(
            roi,
            recurrence_forecast=forecast,
            recurrence_portfolio_summary=portfolio_summary,
            recurrence_remediation_summary=targets.get("remediation_summary")
            if isinstance(targets.get("remediation_summary"), Mapping)
            else None,
        )

    catalog = _portfolio_key_catalog(
        recurrence_timeline=timeline,
        recurrence_forecast=forecast,
        event_log=event_log,
        policy=policy,
    )
    if not catalog and history:
        for entry in history.get("recurrences") or ():
            if not isinstance(entry, Mapping):
                continue
            key = str(entry.get("recurrence_key") or "").strip()
            if not key:
                continue
            catalog.append(
                {
                    "recurrence_key": key,
                    "owner": str(entry.get("owner") or "unknown"),
                    "scenarios": list(entry.get("affected_scenarios") or ["(null)"]),
                    "occurrence_count": int(entry.get("occurrence_count") or 0),
                    "trend_classification": RECURRENCE_TREND_CLASSIFICATION_EMERGING,
                    "forecast_classification": RECURRENCE_FORECAST_WATCH,
                }
            )

    remediation_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (targets.get("keys") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }
    roi_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (roi.get("keys") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }
    history_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (history.get("recurrences") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }

    total_observations = int(
        targets.get("total_observations") or portfolio.get("total_observations") or 0
    )
    total_keys = int(targets.get("total_keys") or portfolio.get("total_keys") or len(catalog))
    forecast_confidence = float(portfolio_summary.get("forecast_confidence") or 0.0)
    roi_confidence = float(roi_summary.get("roi_confidence") or 0.0)
    governance_confidence = _governance_confidence(
        roi_confidence=roi_confidence,
        forecast_confidence=forecast_confidence,
        total_observations=total_observations,
    )
    regression_rate = _regression_rate_value(
        history.get("regression_recurrence_rate")
        if isinstance(history.get("regression_recurrence_rate"), Mapping)
        else trends.get("regression_recurrence_rate")
    )
    stability_score = float(forecast_summary.get("stability_score") or 100.0)
    portfolio_risk_score = float(portfolio_summary.get("portfolio_risk_score") or 0.0)

    watchlist: list[dict[str, Any]] = []
    for entry in catalog:
        key = str(entry.get("recurrence_key") or "")
        remediation = remediation_by_key.get(key, {})
        roi_row = roi_by_key.get(key, {})
        history_row = history_by_key.get(key, {})
        observations = int(entry.get("occurrence_count") or remediation.get("observations") or 0)
        recurrence_rate = (observations / total_observations) if total_observations else 0.0
        reduction_potential = float(
            remediation.get("reduction_potential") or roi_row.get("reduction_potential") or 0.0
        )
        roi_score = float(roi_row.get("roi_score") or 0.0)
        governance_status = classify_recurrence_governance_status(
            trend_classification=str(
                entry.get("trend_classification") or remediation.get("trend_classification") or ""
            ),
            forecast_classification=str(
                entry.get("forecast_classification") or remediation.get("forecast_classification") or ""
            ),
            reduction_potential=reduction_potential,
            roi_score=roi_score,
            roi_confidence=roi_confidence,
            recurrence_rate=recurrence_rate,
            total_observations=total_observations,
            recurrence_status=classify_recurrence_status(history_row) if history_row else "active",
        )
        scenarios = entry.get("scenarios") or history_row.get("affected_scenarios") or ["(null)"]
        scenario = str(scenarios[0] if isinstance(scenarios, list) and scenarios else "(null)")
        watchlist.append(
            {
                "recurrence_key": key,
                "owner": str(entry.get("owner") or history_row.get("owner") or "unknown"),
                "scenario": scenario,
                "governance_status": governance_status,
                "roi_score": roi_score,
                "forecast_classification": str(
                    entry.get("forecast_classification")
                    or remediation.get("forecast_classification")
                    or RECURRENCE_FORECAST_WATCH
                ),
                "trend_classification": str(
                    entry.get("trend_classification")
                    or remediation.get("trend_classification")
                    or RECURRENCE_TREND_CLASSIFICATION_EMERGING
                ),
                "recommended_action": _recommended_action_for_governance_status(governance_status),
            }
        )

    watchlist.sort(
        key=lambda row: (
            {
                RECURRENCE_GOVERNANCE_PRIORITIZE: 0,
                RECURRENCE_GOVERNANCE_INVESTIGATE: 1,
                RECURRENCE_GOVERNANCE_WATCH: 2,
                RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE: 3,
                RECURRENCE_GOVERNANCE_OBSERVE: 4,
            }.get(str(row.get("governance_status") or ""), 5),
            -float(row.get("roi_score") or 0.0),
            str(row.get("recurrence_key") or ""),
        )
    )

    owners, highest_load_owner, ownership_distribution = _build_owner_governance_summary(watchlist)
    retirement_summary = _build_retirement_summary(
        watchlist,
        recurrence_history=history,
        recurrence_trends=trends,
    )
    status_counts = _governance_status_counts(watchlist)
    governance_health_score = _governance_health_score(
        stability_score=stability_score,
        portfolio_risk_score=portfolio_risk_score,
        watchlist_size=len(watchlist),
        prioritized_targets=int(status_counts.get(RECURRENCE_GOVERNANCE_PRIORITIZE) or 0),
        total_keys=max(total_keys, 1),
        regression_recurrence_rate=regression_rate,
    )

    governance_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "intervention_thresholds": _governance_intervention_thresholds(),
        "governance_status_classification_definition": RECURRENCE_GOVERNANCE_STATUS_CLASSIFICATION_DEFINITION,
        "total_keys": total_keys,
        "total_observations": total_observations,
        "governance_confidence": governance_confidence,
        "governance_health_score": governance_health_score,
        "watchlist": watchlist,
        "owners": owners,
        "highest_governance_load_owner": highest_load_owner,
        "ownership_distribution": ownership_distribution,
        "retirement_summary": retirement_summary,
    }
    governance_summary = summarize_recurrence_governance(governance_without_summary)
    return {
        **governance_without_summary,
        "governance_summary": governance_summary,
    }


def enrich_recurrence_history_with_governance(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay governance fields."""
    payload = dict(history)
    governance = build_recurrence_governance(
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_portfolio=payload.get("recurrence_portfolio")
        if isinstance(payload.get("recurrence_portfolio"), Mapping)
        else None,
        recurrence_remediation_targets=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_roi=payload.get("recurrence_roi")
        if isinstance(payload.get("recurrence_roi"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_timeline=payload.get("recurrence_timeline")
        if isinstance(payload.get("recurrence_timeline"), list)
        else None,
        event_log=event_log,
        policy=policy,
    )
    payload["recurrence_governance"] = governance
    payload["recurrence_watchlist"] = governance["watchlist"]
    payload["recurrence_governance_summary"] = governance["governance_summary"]
    payload["recurrence_retirement_summary"] = governance["retirement_summary"]
    return payload


RECURRENCE_LIFECYCLE_EMERGING = "emerging"
RECURRENCE_LIFECYCLE_RECURRING = "recurring"
RECURRENCE_LIFECYCLE_PERSISTENT = "persistent"
RECURRENCE_LIFECYCLE_DORMANT = "dormant"
RECURRENCE_LIFECYCLE_RETIRED = "retired"
RECURRENCE_LIFECYCLE_STAGES: frozenset[str] = frozenset(
    {
        RECURRENCE_LIFECYCLE_EMERGING,
        RECURRENCE_LIFECYCLE_RECURRING,
        RECURRENCE_LIFECYCLE_PERSISTENT,
        RECURRENCE_LIFECYCLE_DORMANT,
        RECURRENCE_LIFECYCLE_RETIRED,
    }
)
RECURRENCE_LIFECYCLE_RETIREMENT_INACTIVITY_DAYS = 90.0
RECURRENCE_LIFECYCLE_STALLED_AGE_DAYS = 7.0
RECURRENCE_LIFECYCLE_ADVANCING_TRANSITIONS: tuple[str, ...] = (
    "emerging->recurring",
    "recurring->persistent",
)
RECURRENCE_LIFECYCLE_RETIRING_TRANSITIONS: tuple[str, ...] = (
    "persistent->dormant",
    "recurring->dormant",
    "dormant->retired",
)
RECURRENCE_LIFECYCLE_STAGE_DEFINITIONS: dict[str, str] = {
    RECURRENCE_LIFECYCLE_EMERGING: "First observed protected recurrence for the key.",
    RECURRENCE_LIFECYCLE_RECURRING: "Repeated protected observations without an extended active span.",
    RECURRENCE_LIFECYCLE_PERSISTENT: (
        f"Repeated protected observations spanning at least "
        f"{RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS} days between first and last seen."
    ),
    RECURRENCE_LIFECYCLE_DORMANT: (
        f"Historical protected recurrence without observation within the last "
        f"{RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS} days."
    ),
    RECURRENCE_LIFECYCLE_RETIRED: (
        f"Explicitly retired recurrence status, or dormant beyond "
        f"{RECURRENCE_LIFECYCLE_RETIREMENT_INACTIVITY_DAYS} days of inactivity."
    ),
}
RECURRENCE_LIFECYCLE_STAGE_CLASSIFICATION_DEFINITION = (
    "Deterministic lifecycle stage from trend classification and recurrence status: retired when "
    "status is retired/deprecated or dormant inactivity exceeds retirement threshold; otherwise "
    "lifecycle stage mirrors trend classification (emerging, recurring, persistent, dormant)."
)
RECURRENCE_LIFECYCLE_CLOSURE_RATE_DEFINITION = (
    "Advisory closure rate: (retired_keys + dormant_keys) / max(total_keys, 1)."
)
RECURRENCE_LIFECYCLE_HEALTH_SCORE_DEFINITION = (
    "Advisory 0-100 score: 25% retired_ratio + 15% dormant_ratio + 20% (1 - persistent_ratio) + "
    "20% (1 - min(1, advancement_rate * 2)) + 20% emerging_ratio. Higher scores indicate healthier "
    "lifecycle posture with more closures and fewer advancing persistent recurrences."
)
RECURRENCE_LIFECYCLE_VELOCITY_DEFINITION = (
    "observations_per_day is occurrence_count / max(recurrence_age_days, active_duration_days, 1); "
    "lifecycle_velocity equals observations_per_day; advancement_rate is advancing_transitions / "
    "max(total_keys, 1)."
)


def classify_recurrence_lifecycle_stage(
    *,
    trend_classification: str,
    recurrence_status: str = "active",
    last_seen: Any | None = None,
    as_of: Any | None = None,
    dormant_inactivity_days: float = RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS,
    retirement_inactivity_days: float = RECURRENCE_LIFECYCLE_RETIREMENT_INACTIVITY_DAYS,
) -> str:
    """Classify one protected recurrence key into a deterministic lifecycle stage."""
    status = str(recurrence_status or "active").strip().lower()
    if status in {"retired", "deprecated"}:
        return RECURRENCE_LIFECYCLE_RETIRED

    trend = str(trend_classification or "").strip()
    last_dt = _parse_iso_timestamp(last_seen)
    as_of_dt = _parse_iso_timestamp(as_of) or datetime.now(UTC)

    if trend == RECURRENCE_TREND_CLASSIFICATION_DORMANT:
        if last_dt is not None:
            inactivity_days = max((as_of_dt - last_dt).total_seconds() / 86400.0, 0.0)
            if inactivity_days >= retirement_inactivity_days:
                return RECURRENCE_LIFECYCLE_RETIRED
        return RECURRENCE_LIFECYCLE_DORMANT

    if trend == RECURRENCE_TREND_CLASSIFICATION_EMERGING:
        return RECURRENCE_LIFECYCLE_EMERGING
    if trend == RECURRENCE_TREND_CLASSIFICATION_RECURRING:
        return RECURRENCE_LIFECYCLE_RECURRING
    if trend == RECURRENCE_TREND_CLASSIFICATION_PERSISTENT:
        return RECURRENCE_LIFECYCLE_PERSISTENT

    return RECURRENCE_LIFECYCLE_EMERGING


def _lifecycle_age_days(
    *,
    first_seen: Any | None,
    as_of: Any | None,
) -> float:
    first_dt = _parse_iso_timestamp(first_seen)
    as_of_dt = _parse_iso_timestamp(as_of) or datetime.now(UTC)
    if first_dt is None:
        return 0.0
    return round(max((as_of_dt - first_dt).total_seconds() / 86400.0, 0.0), 4)


def _median_value(values: Sequence[float]) -> float:
    numbers = sorted(float(value or 0.0) for value in values)
    if not numbers:
        return 0.0
    midpoint = len(numbers) // 2
    if len(numbers) % 2:
        return round(numbers[midpoint], 4)
    return round((numbers[midpoint - 1] + numbers[midpoint]) / 2.0, 4)


def _infer_lifecycle_transitions(
    *,
    lifecycle_stage: str,
    occurrence_count: int,
    active_duration_days: float,
) -> list[str]:
    transitions: list[str] = []
    count = max(int(occurrence_count or 0), 0)
    duration = max(float(active_duration_days or 0.0), 0.0)
    stage = str(lifecycle_stage or "").strip()

    if count >= 2:
        transitions.append("emerging->recurring")
    if count >= 2 and duration >= RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS:
        transitions.append("recurring->persistent")

    if stage in {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}:
        if count >= 2 and duration >= RECURRENCE_TREND_PERSISTENT_MIN_ACTIVE_DURATION_DAYS:
            transitions.append("persistent->dormant")
        elif count >= 2:
            transitions.append("recurring->dormant")

    if stage == RECURRENCE_LIFECYCLE_RETIRED:
        transitions.append("dormant->retired")

    return transitions


def _is_stalled_lifecycle_key(entry: Mapping[str, Any]) -> bool:
    stage = str(entry.get("lifecycle_stage") or "").strip()
    age_days = float(entry.get("recurrence_age_days") or 0.0)
    count = int(entry.get("occurrence_count") or 0)
    velocity = float(entry.get("lifecycle_velocity") or 0.0)
    if stage == RECURRENCE_LIFECYCLE_EMERGING and count <= 1 and age_days >= RECURRENCE_LIFECYCLE_STALLED_AGE_DAYS:
        return True
    if (
        stage in {RECURRENCE_LIFECYCLE_RECURRING, RECURRENCE_LIFECYCLE_PERSISTENT}
        and velocity < 0.01
        and age_days >= RECURRENCE_LIFECYCLE_STALLED_AGE_DAYS * 2
    ):
        return True
    return False


def _lifecycle_distribution(keys: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {stage: 0 for stage in sorted(RECURRENCE_LIFECYCLE_STAGES)}
    for entry in keys:
        if not isinstance(entry, Mapping):
            continue
        stage = str(entry.get("lifecycle_stage") or RECURRENCE_LIFECYCLE_EMERGING).strip()
        if stage in counts:
            counts[stage] += 1
    return counts


def _build_age_distribution(keys: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ages = [float(entry.get("recurrence_age_days") or 0.0) for entry in keys if isinstance(entry, Mapping)]
    if not ages:
        return {
            "youngest_key": None,
            "oldest_key": None,
            "average_age_days": 0.0,
            "median_age_days": 0.0,
        }
    youngest_age = min(ages)
    oldest_age = max(ages)
    youngest_key = None
    oldest_key = None
    for entry in keys:
        if not isinstance(entry, Mapping):
            continue
        age = float(entry.get("recurrence_age_days") or 0.0)
        if age == youngest_age and youngest_key is None:
            youngest_key = entry.get("recurrence_key")
        if age == oldest_age:
            oldest_key = entry.get("recurrence_key")
    return {
        "youngest_key": youngest_key,
        "oldest_key": oldest_key,
        "average_age_days": round(sum(ages) / len(ages), 4),
        "median_age_days": _median_value(ages),
    }


def _build_transition_summary(keys: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    all_transitions: list[str] = []
    stalled_keys: list[str] = []
    for entry in keys:
        if not isinstance(entry, Mapping):
            continue
        transitions = _infer_lifecycle_transitions(
            lifecycle_stage=str(entry.get("lifecycle_stage") or ""),
            occurrence_count=int(entry.get("occurrence_count") or 0),
            active_duration_days=float(entry.get("active_duration_days") or 0.0),
        )
        all_transitions.extend(transitions)
        if _is_stalled_lifecycle_key(entry):
            stalled_keys.append(str(entry.get("recurrence_key") or ""))
    advancing = [transition for transition in all_transitions if transition in RECURRENCE_LIFECYCLE_ADVANCING_TRANSITIONS]
    retiring = [transition for transition in all_transitions if transition in RECURRENCE_LIFECYCLE_RETIRING_TRANSITIONS]
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "transition_count": len(all_transitions),
        "advancing_transitions": len(advancing),
        "retiring_transitions": len(retiring),
        "stalled_keys": stalled_keys,
        "stalled_key_count": len(stalled_keys),
        "transitions": all_transitions,
    }


def _build_closure_effectiveness_summary(
    lifecycle_distribution: Mapping[str, int],
) -> dict[str, Any]:
    total_keys = sum(int(value or 0) for value in lifecycle_distribution.values())
    retired_keys = int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_RETIRED) or 0)
    dormant_keys = int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_DORMANT) or 0)
    active_keys = (
        int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_EMERGING) or 0)
        + int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_RECURRING) or 0)
        + int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_PERSISTENT) or 0)
    )
    denominator = max(total_keys, 1)
    closure_rate = round((retired_keys + dormant_keys) / float(denominator), 4)
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "retired_keys": retired_keys,
        "dormant_keys": dormant_keys,
        "active_keys": active_keys,
        "closure_rate": closure_rate,
        "closure_rate_definition": RECURRENCE_LIFECYCLE_CLOSURE_RATE_DEFINITION,
    }


def _lifecycle_health_score(
    *,
    lifecycle_distribution: Mapping[str, int],
    advancement_rate: float,
) -> float:
    total_keys = sum(int(value or 0) for value in lifecycle_distribution.values())
    if total_keys <= 0:
        return 100.0
    retired_ratio = int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_RETIRED) or 0) / float(total_keys)
    dormant_ratio = int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_DORMANT) or 0) / float(total_keys)
    persistent_ratio = int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_PERSISTENT) or 0) / float(total_keys)
    emerging_ratio = int(lifecycle_distribution.get(RECURRENCE_LIFECYCLE_EMERGING) or 0) / float(total_keys)
    advancement = min(1.0, max(float(advancement_rate or 0.0), 0.0) * 2.0)
    blended = (
        0.25 * retired_ratio
        + 0.15 * dormant_ratio
        + 0.20 * (1.0 - persistent_ratio)
        + 0.20 * (1.0 - advancement)
        + 0.20 * emerging_ratio
    )
    return round(max(0.0, min(100.0, 100.0 * blended)), 1)


def summarize_recurrence_lifecycle(
    lifecycle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence lifecycle health metrics."""
    source = lifecycle if isinstance(lifecycle, Mapping) else {}
    distribution = source.get("lifecycle_distribution")
    if not isinstance(distribution, Mapping):
        distribution = {}
    closure = source.get("closure_effectiveness")
    if not isinstance(closure, Mapping):
        closure = _build_closure_effectiveness_summary(distribution)
    age_distribution = source.get("age_distribution")
    if not isinstance(age_distribution, Mapping):
        age_distribution = {}
    transition_summary = source.get("transition_summary")
    if not isinstance(transition_summary, Mapping):
        transition_summary = {}
    total_keys = sum(int(value or 0) for value in distribution.values())
    advancement_rate = (
        float(transition_summary.get("advancing_transitions") or 0) / float(max(total_keys, 1))
    )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "active_keys": int(closure.get("active_keys") or 0),
        "retired_keys": int(closure.get("retired_keys") or 0),
        "dormant_keys": int(closure.get("dormant_keys") or 0),
        "closure_rate": float(closure.get("closure_rate") or 0.0),
        "average_age_days": float(age_distribution.get("average_age_days") or 0.0),
        "advancement_rate": round(advancement_rate, 4),
        "lifecycle_health_score": float(source.get("lifecycle_health_score") or 0.0),
        "lifecycle_health_score_definition": RECURRENCE_LIFECYCLE_HEALTH_SCORE_DEFINITION,
        "closure_rate_definition": RECURRENCE_LIFECYCLE_CLOSURE_RATE_DEFINITION,
    }


def build_recurrence_lifecycle(
    *,
    recurrence_timeline: Sequence[Mapping[str, Any]] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence lifecycle analytics."""
    timeline = _timeline_rows(recurrence_timeline)
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}

    if not timeline and event_log is not None:
        timeline = build_recurrence_timeline(event_log, policy=policy, as_of=as_of)

    events = _protected_events_ordered(event_log, policy=policy) if event_log is not None else []
    as_of_value = as_of
    if as_of_value is None and events:
        as_of_value = _timeline_as_of(events).isoformat().replace("+00:00", "Z")
    elif as_of_value is None and timeline:
        as_of_value = max((str(row.get("last_seen") or "") for row in timeline), default=None)

    governance_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (governance.get("watchlist") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }
    history_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (history.get("recurrences") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }

    keys: list[dict[str, Any]] = []
    for row in timeline:
        if not isinstance(row, Mapping):
            continue
        key = str(row.get("recurrence_key") or "")
        history_row = history_by_key.get(key, {})
        governance_row = governance_by_key.get(key, {})
        trend_classification = str(row.get("trend_classification") or RECURRENCE_TREND_CLASSIFICATION_EMERGING)
        recurrence_status = classify_recurrence_status(history_row) if history_row else "active"
        lifecycle_stage = classify_recurrence_lifecycle_stage(
            trend_classification=trend_classification,
            recurrence_status=recurrence_status,
            last_seen=row.get("last_seen"),
            as_of=as_of_value,
        )
        recurrence_age_days = _lifecycle_age_days(first_seen=row.get("first_seen"), as_of=as_of_value)
        active_duration_days = float(row.get("active_duration_days") or 0.0)
        occurrence_count = int(row.get("occurrence_count") or 0)
        age_denominator = max(recurrence_age_days, active_duration_days, 1.0)
        observations_per_day = round(occurrence_count / age_denominator, 4)
        keys.append(
            {
                "recurrence_key": key,
                "lifecycle_stage": lifecycle_stage,
                "first_seen": row.get("first_seen"),
                "last_seen": row.get("last_seen"),
                "recurrence_age_days": recurrence_age_days,
                "active_duration_days": active_duration_days,
                "occurrence_count": occurrence_count,
                "observations_per_day": observations_per_day,
                "lifecycle_velocity": observations_per_day,
                "trend_classification": trend_classification,
                "governance_status": governance_row.get("governance_status"),
            }
        )

    lifecycle_distribution = _lifecycle_distribution(keys)
    age_distribution = _build_age_distribution(keys)
    transition_summary = _build_transition_summary(keys)
    closure_effectiveness = _build_closure_effectiveness_summary(lifecycle_distribution)
    total_keys = sum(lifecycle_distribution.values())
    advancement_rate = float(transition_summary.get("advancing_transitions") or 0) / float(max(total_keys, 1))
    lifecycle_health_score = _lifecycle_health_score(
        lifecycle_distribution=lifecycle_distribution,
        advancement_rate=advancement_rate,
    )

    lifecycle_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "lifecycle_stage_definitions": RECURRENCE_LIFECYCLE_STAGE_DEFINITIONS,
        "lifecycle_stage_classification_definition": RECURRENCE_LIFECYCLE_STAGE_CLASSIFICATION_DEFINITION,
        "lifecycle_velocity_definition": RECURRENCE_LIFECYCLE_VELOCITY_DEFINITION,
        "total_keys": total_keys,
        "keys": keys,
        "lifecycle_distribution": lifecycle_distribution,
        "age_distribution": age_distribution,
        "transition_summary": transition_summary,
        "closure_effectiveness": closure_effectiveness,
        "lifecycle_health_score": lifecycle_health_score,
        "advancement_rate": round(advancement_rate, 4),
    }
    lifecycle_summary = summarize_recurrence_lifecycle(lifecycle_without_summary)
    return {
        **lifecycle_without_summary,
        "lifecycle_summary": lifecycle_summary,
    }


def enrich_recurrence_history_with_lifecycle(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay lifecycle fields."""
    payload = dict(history)
    lifecycle = build_recurrence_lifecycle(
        recurrence_timeline=payload.get("recurrence_timeline")
        if isinstance(payload.get("recurrence_timeline"), list)
        else None,
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_history=payload,
        event_log=event_log,
        policy=policy,
        as_of=as_of,
    )
    payload["recurrence_lifecycle"] = lifecycle
    payload["recurrence_lifecycle_summary"] = lifecycle["lifecycle_summary"]
    payload["recurrence_age_distribution"] = lifecycle["age_distribution"]
    payload["recurrence_transition_summary"] = lifecycle["transition_summary"]
    payload["recurrence_closure_effectiveness"] = lifecycle["closure_effectiveness"]
    return payload


RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_OBSERVATIONS = RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS
RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS = 3
RECURRENCE_FORECAST_LIFECYCLE_ALIGNMENT: dict[str, frozenset[str]] = {
    RECURRENCE_FORECAST_WATCH: frozenset({RECURRENCE_LIFECYCLE_EMERGING}),
    RECURRENCE_FORECAST_ELEVATED: frozenset(
        {RECURRENCE_LIFECYCLE_RECURRING, RECURRENCE_LIFECYCLE_PERSISTENT}
    ),
    RECURRENCE_FORECAST_CONCENTRATED: frozenset(
        {RECURRENCE_LIFECYCLE_PERSISTENT, RECURRENCE_LIFECYCLE_RECURRING}
    ),
    RECURRENCE_FORECAST_STABLE: frozenset(
        {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}
    ),
}
RECURRENCE_GOVERNANCE_CONVERSION_DEFINITION = (
    "Advisory conversion rates from current governance funnel snapshot: "
    "watchlist_conversion_rate is investigate_keys / max(watch_keys, 1); "
    "investigate_conversion_rate is prioritize_keys / max(investigate_keys, 1); "
    "prioritize_conversion_rate is remediation_ready_keys / max(prioritize_keys, 1), "
    "where remediation_ready_keys have reduction_potential >= investigate threshold; "
    "retirement_conversion_rate is retirement_outcome_keys / max(total_governed_keys, 1)."
)
RECURRENCE_REMEDIATION_EFFECTIVENESS_DEFINITION = (
    "Advisory remediation effectiveness: targeted_keys from remediation summary; "
    "improved_keys are targeted keys in dormant or retired lifecycle stages; "
    "unresolved_keys are targeted keys still active; recurrence_reduction_rate is "
    "resolved_or_retired_keys / max(historically_targeted_keys, 1). Without longitudinal "
    "remediation history, historically_targeted_keys defaults to current targeted_keys."
)
RECURRENCE_FORECAST_EFFECTIVENESS_DEFINITION = (
    "Advisory forecast effectiveness: forecast_accuracy is the share of key forecasts whose "
    "lifecycle_stage aligns with the forecast_classification alignment map; "
    "predicted_recurrences counts watch/elevated/concentrated forecasts; "
    "realized_recurrences counts aligned lifecycle outcomes. Low observation volume yields "
    "low effectiveness_confidence without fabricating accuracy."
)
RECURRENCE_PORTFOLIO_TRAJECTORY_DEFINITION = (
    "Portfolio trajectory compares current portfolio, governance, lifecycle, and stability "
    "metrics against a stored baseline snapshot when available; otherwise reports baseline "
    "values with trajectory_available=false and zero change metrics."
)
RECURRENCE_STABILITY_TRAJECTORY_DEFINITION = (
    "Stability trajectory reports current stability_score and regression_recurrence_rate "
    "against baseline values; change metrics are zero when no prior baseline snapshot exists."
)
RECURRENCE_TRAJECTORY_SCHEMA_VERSION = 1
RECURRENCE_TRAJECTORY_HISTORY_DEFINITION = (
    "Append-only protected replay recurrence trajectory snapshots. Snapshot #1 is the "
    "longitudinal baseline; trajectory_available becomes true once two or more snapshots exist."
)
RECURRENCE_TRAJECTORY_SUMMARY_DEFINITION = (
    "Trajectory summary compares the current snapshot against the baseline snapshot. "
    "With one snapshot only, trajectory_available=false and change metrics remain zero."
)
RECURRENCE_TRAJECTORY_ACTIVATION_MIN_SNAPSHOTS = 2
RECURRENCE_TRAJECTORY_BASELINE_MESSAGE = (
    "Trajectory baseline established. Additional snapshots required for change detection."
)


def empty_recurrence_trajectory_history() -> dict[str, Any]:
    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
        "snapshots": [],
    }


def load_recurrence_trajectory_history(path: Path | str | None = None) -> dict[str, Any]:
    """Load append-only recurrence trajectory history from disk."""
    from tests.helpers.failure_dashboard_report import RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH

    history_path = Path(path or RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH)
    if not history_path.is_file():
        return empty_recurrence_trajectory_history()
    raw = json.loads(history_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("snapshots"), list):
        raise ValueError("trajectory history must be a JSON object with a snapshots list")
    if raw.get("schema_version") != RECURRENCE_TRAJECTORY_SCHEMA_VERSION:
        raise ValueError(f"unsupported trajectory history schema_version: {raw.get('schema_version')!r}")
    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
        "snapshots": [dict(item) for item in raw["snapshots"] if isinstance(item, Mapping)],
    }


def write_recurrence_trajectory_history(
    history: Mapping[str, Any],
    path: Path | str | None = None,
) -> Path:
    """Write recurrence trajectory history JSON."""
    from tests.helpers.failure_dashboard_report import RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH

    history_path = Path(path or RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(dict(history), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return history_path


def _trajectory_float(value: Any) -> float:
    try:
        return round(float(value or 0.0), 4)
    except (TypeError, ValueError):
        return 0.0


def _trajectory_snapshot_fingerprint(snapshot: Mapping[str, Any]) -> tuple[Any, ...]:
    source = snapshot if isinstance(snapshot, Mapping) else {}
    return (
        int(source.get("protected_observation_count") or 0),
        int(source.get("unique_recurrence_keys") or 0),
        _trajectory_float(source.get("regression_recurrence_rate")),
        _trajectory_float(source.get("governance_health_score")),
        _trajectory_float(source.get("lifecycle_health_score")),
        _trajectory_float(source.get("portfolio_risk_score")),
        _trajectory_float(source.get("operational_readiness_score")),
        _trajectory_float(source.get("effectiveness_score")),
        _trajectory_float(source.get("maturity_score")),
        _trajectory_float(source.get("stability_score")),
        _trajectory_float(source.get("program_effectiveness_score")),
    )


def build_recurrence_trajectory_snapshot(
    *,
    timestamp: str,
    artifact_source: str,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    recurrence_governance_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    snapshot_index: int | None = None,
) -> dict[str, Any]:
    """Build one protected replay recurrence trajectory snapshot."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    governance_summary = recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    maturity_summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    protected_observation_count = int(
        portfolio_summary.get("total_observations")
        or history.get("total_rows")
        or 0
    )
    unique_recurrence_keys = int(history.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0)
    return {
        "snapshot_index": int(snapshot_index or 0),
        "timestamp": str(timestamp or "").strip(),
        "artifact_source": str(artifact_source or "").strip(),
        "protected_observation_count": protected_observation_count,
        "unique_recurrence_keys": unique_recurrence_keys,
        "regression_recurrence_rate": _regression_rate_value(history.get("regression_recurrence_rate")),
        "governance_health_score": _trajectory_float(
            governance_summary.get("governance_health_score")
        ),
        "lifecycle_health_score": _trajectory_float(
            lifecycle_summary.get("lifecycle_health_score")
        ),
        "portfolio_risk_score": _trajectory_float(portfolio_summary.get("portfolio_risk_score")),
        "operational_readiness_score": _trajectory_float(
            maturity_summary.get("operational_readiness_score")
        ),
        "effectiveness_score": _trajectory_float(program_summary.get("effectiveness_confidence")),
        "maturity_score": _trajectory_float(maturity_summary.get("overall_maturity_score")),
        "stability_score": _trajectory_float(forecast_summary.get("stability_score")),
        "program_effectiveness_score": _trajectory_float(
            program_summary.get("program_effectiveness_score")
        ),
    }


def append_recurrence_trajectory_history(
    history: Mapping[str, Any] | None,
    snapshot: Mapping[str, Any],
    *,
    temporal_capture: bool = False,
) -> dict[str, Any]:
    """Return trajectory history with one deduped snapshot appended."""
    base = history if isinstance(history, Mapping) else empty_recurrence_trajectory_history()
    snapshots = [
        dict(item) for item in (base.get("snapshots") or ()) if isinstance(item, Mapping)
    ]
    candidate = dict(snapshot)
    if snapshots and _trajectory_snapshot_fingerprint(snapshots[-1]) == _trajectory_snapshot_fingerprint(candidate):
        same_timestamp = str(snapshots[-1].get("timestamp") or "") == str(candidate.get("timestamp") or "")
        if not temporal_capture or same_timestamp:
            return {
                "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
                "report_only": RECURRENCE_REPORT_ONLY,
                "advisory_only": RECURRENCE_ADVISORY_ONLY,
                "protected_replay_only": True,
                "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
                "snapshots": snapshots,
            }
    candidate["snapshot_index"] = len(snapshots) + 1
    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
        "snapshots": snapshots + [candidate],
    }


def prior_program_effectiveness_from_trajectory_snapshot(
    snapshot: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Convert one trajectory snapshot into prior program-effectiveness inputs."""
    source = snapshot if isinstance(snapshot, Mapping) else {}
    return {
        "program_effectiveness_summary": {
            "program_effectiveness_score": source.get("program_effectiveness_score"),
            "effectiveness_confidence": source.get("effectiveness_score"),
        },
        "portfolio_trajectory_summary": {
            "portfolio_risk_current": source.get("portfolio_risk_score"),
            "governance_health_current": source.get("governance_health_score"),
            "lifecycle_health_current": source.get("lifecycle_health_score"),
        },
        "stability_trajectory_summary": {
            "stability_score_current": source.get("stability_score"),
            "recurrence_rate_current": source.get("regression_recurrence_rate"),
        },
    }


def _trajectory_direction(change: float, *, higher_is_better: bool = True) -> str:
    if abs(float(change or 0.0)) <= 0.0001:
        return "stable"
    if higher_is_better:
        return "improving" if change > 0 else "regressing"
    return "improving" if change < 0 else "regressing"


def _trajectory_percent_change(baseline: float, current: float) -> float:
    baseline_value = float(baseline or 0.0)
    current_value = float(current or 0.0)
    if abs(baseline_value) <= 0.0001:
        return 0.0 if abs(current_value) <= 0.0001 else round(current_value * 100.0, 2)
    return round(((current_value - baseline_value) / baseline_value) * 100.0, 2)


def _trajectory_metric_change(
    *,
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    field: str,
    higher_is_better: bool = True,
) -> dict[str, Any]:
    baseline_value = _trajectory_float(baseline.get(field))
    current_value = _trajectory_float(current.get(field))
    absolute_change = round(current_value - baseline_value, 4)
    return {
        "baseline": baseline_value,
        "current": current_value,
        "absolute_change": absolute_change,
        "percent_change": _trajectory_percent_change(baseline_value, current_value),
        "direction": _trajectory_direction(absolute_change, higher_is_better=higher_is_better),
    }


def summarize_recurrence_trajectory(
    history: Mapping[str, Any] | None,
    *,
    current_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence trajectory from stored snapshots."""
    source = history if isinstance(history, Mapping) else empty_recurrence_trajectory_history()
    snapshots = [dict(item) for item in (source.get("snapshots") or ()) if isinstance(item, Mapping)]
    if current_snapshot and isinstance(current_snapshot, Mapping):
        projected = append_recurrence_trajectory_history(source, current_snapshot)
        snapshots = [dict(item) for item in (projected.get("snapshots") or ()) if isinstance(item, Mapping)]
    snapshot_count = len(snapshots)
    trajectory_available = snapshot_count >= RECURRENCE_TRAJECTORY_ACTIVATION_MIN_SNAPSHOTS
    baseline_snapshot = dict(snapshots[0]) if snapshots else {}
    latest_snapshot = dict(snapshots[-1]) if snapshots else dict(current_snapshot or {})
    if not latest_snapshot and isinstance(current_snapshot, Mapping):
        latest_snapshot = dict(current_snapshot)

    portfolio_risk = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="portfolio_risk_score",
        higher_is_better=False,
    )
    governance_health = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="governance_health_score",
    )
    lifecycle_health = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="lifecycle_health_score",
    )
    operational_readiness = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="operational_readiness_score",
    )
    effectiveness = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="effectiveness_score",
    )
    maturity = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="maturity_score",
    )
    stability = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="stability_score",
    )
    program_effectiveness = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="program_effectiveness_score",
    )
    regression_rate = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="regression_recurrence_rate",
        higher_is_better=False,
    )

    if not trajectory_available:
        portfolio_risk["absolute_change"] = 0.0
        portfolio_risk["percent_change"] = 0.0
        portfolio_risk["direction"] = "stable"
        governance_health["absolute_change"] = 0.0
        governance_health["percent_change"] = 0.0
        governance_health["direction"] = "stable"
        lifecycle_health["absolute_change"] = 0.0
        lifecycle_health["percent_change"] = 0.0
        lifecycle_health["direction"] = "stable"
        operational_readiness["absolute_change"] = 0.0
        operational_readiness["percent_change"] = 0.0
        operational_readiness["direction"] = "stable"
        effectiveness["absolute_change"] = 0.0
        effectiveness["percent_change"] = 0.0
        effectiveness["direction"] = "stable"
        maturity["absolute_change"] = 0.0
        maturity["percent_change"] = 0.0
        maturity["direction"] = "stable"
        stability["absolute_change"] = 0.0
        stability["percent_change"] = 0.0
        stability["direction"] = "stable"
        program_effectiveness["absolute_change"] = 0.0
        program_effectiveness["percent_change"] = 0.0
        program_effectiveness["direction"] = "stable"
        regression_rate["absolute_change"] = 0.0
        regression_rate["percent_change"] = 0.0
        regression_rate["direction"] = "stable"

    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_SUMMARY_DEFINITION,
        "trajectory_available": trajectory_available,
        "baseline_only": not trajectory_available,
        "snapshot_count": snapshot_count,
        "baseline_snapshot": baseline_snapshot,
        "current_snapshot": latest_snapshot,
        "portfolio_risk_change": portfolio_risk["absolute_change"],
        "governance_health_change": governance_health["absolute_change"],
        "lifecycle_health_change": lifecycle_health["absolute_change"],
        "operational_readiness_change": operational_readiness["absolute_change"],
        "effectiveness_change": effectiveness["absolute_change"],
        "maturity_change": maturity["absolute_change"],
        "portfolio_trajectory": portfolio_risk,
        "governance_trajectory": governance_health,
        "lifecycle_trajectory": lifecycle_health,
        "operational_readiness_trajectory": operational_readiness,
        "effectiveness_trajectory": effectiveness,
        "maturity_trajectory": maturity,
        "stability_trajectory": stability,
        "program_effectiveness_trajectory": program_effectiveness,
        "regression_rate_trajectory": regression_rate,
        "message": (
            RECURRENCE_TRAJECTORY_BASELINE_MESSAGE
            if snapshot_count <= 1
            else "Trajectory change detection active across baseline and current snapshots."
        ),
    }


def apply_recurrence_trajectory_to_analytics(
    *,
    timestamp: str,
    artifact_source: str,
    recurrence_history: Mapping[str, Any],
    recurrence_timeline: Sequence[Mapping[str, Any]] | None,
    recurrence_trends: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any],
    recurrence_portfolio: Mapping[str, Any],
    recurrence_remediation_targets: Mapping[str, Any],
    recurrence_roi: Mapping[str, Any],
    recurrence_governance: Mapping[str, Any],
    recurrence_lifecycle: Mapping[str, Any],
    recurrence_program_effectiveness: Mapping[str, Any],
    recurrence_maturity: Mapping[str, Any],
    recurrence_roadmap: Mapping[str, Any],
    recurrence_completion: Mapping[str, Any],
    recurrence_graduation_audit: Mapping[str, Any],
    trajectory_history_path: Path | str | None = None,
    temporal_capture: bool = False,
) -> dict[str, Any]:
    """Append trajectory snapshots and rebuild analytics when trajectory activates."""
    current_snapshot = build_recurrence_trajectory_snapshot(
        timestamp=timestamp,
        artifact_source=artifact_source,
        recurrence_history=recurrence_history,
        recurrence_portfolio_summary=recurrence_portfolio.get("portfolio_summary")
        if isinstance(recurrence_portfolio.get("portfolio_summary"), Mapping)
        else None,
        recurrence_forecast_summary=recurrence_forecast.get("forecast_summary")
        if isinstance(recurrence_forecast.get("forecast_summary"), Mapping)
        else None,
        recurrence_governance_summary=recurrence_governance.get("governance_summary")
        if isinstance(recurrence_governance.get("governance_summary"), Mapping)
        else None,
        recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
        if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
        else None,
        recurrence_program_effectiveness_summary=recurrence_program_effectiveness.get(
            "program_effectiveness_summary"
        )
        if isinstance(recurrence_program_effectiveness.get("program_effectiveness_summary"), Mapping)
        else None,
        recurrence_maturity_summary=recurrence_maturity.get("recurrence_maturity_summary")
        if isinstance(recurrence_maturity.get("recurrence_maturity_summary"), Mapping)
        else None,
    )
    loaded_history = load_recurrence_trajectory_history(trajectory_history_path)
    from tests.helpers.failure_dashboard_report import RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH

    artifact_source_normalized = str(artifact_source or "").replace("\\", "/").lower()
    committed_history = (
        Path(trajectory_history_path or RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH).resolve()
        == RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH.resolve()
    )
    if committed_history and not artifact_source_normalized.startswith(
        GOLDEN_REPLAY_ARTIFACT_SOURCE_PREFIX.lower()
    ):
        projected_history = loaded_history
    else:
        projected_history = append_recurrence_trajectory_history(
            loaded_history,
            current_snapshot,
            temporal_capture=temporal_capture,
        )
    trajectory_summary = summarize_recurrence_trajectory(projected_history)
    trajectory_available = bool(trajectory_summary.get("trajectory_available"))

    program_effectiveness = recurrence_program_effectiveness
    maturity = recurrence_maturity
    roadmap = recurrence_roadmap
    completion = recurrence_completion
    graduation_audit = recurrence_graduation_audit

    if trajectory_available:
        prior = prior_program_effectiveness_from_trajectory_snapshot(
            trajectory_summary.get("baseline_snapshot")
        )
        program_effectiveness = build_recurrence_program_effectiveness(
            recurrence_governance=recurrence_governance,
            recurrence_remediation_summary=recurrence_remediation_targets.get("remediation_summary")
            if isinstance(recurrence_remediation_targets.get("remediation_summary"), Mapping)
            else None,
            recurrence_roi_summary=recurrence_roi.get("roi_summary")
            if isinstance(recurrence_roi.get("roi_summary"), Mapping)
            else None,
            recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
            if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
            else None,
            recurrence_portfolio_summary=recurrence_portfolio.get("portfolio_summary")
            if isinstance(recurrence_portfolio.get("portfolio_summary"), Mapping)
            else None,
            recurrence_forecast=recurrence_forecast,
            recurrence_history=recurrence_history,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_remediation_targets=recurrence_remediation_targets,
            prior_program_effectiveness=prior,
            trajectory_available=True,
        )
        maturity = build_recurrence_maturity_assessment(
            recurrence_history=recurrence_history,
            recurrence_trends=recurrence_trends,
            recurrence_forecast=recurrence_forecast,
            recurrence_portfolio=recurrence_portfolio,
            recurrence_remediation=recurrence_remediation_targets,
            recurrence_roi=recurrence_roi,
            recurrence_governance=recurrence_governance,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_program_effectiveness=program_effectiveness,
        )
        roadmap = build_recurrence_strategic_roadmap(
            recurrence_maturity_summary=maturity["recurrence_maturity_summary"],
            recurrence_maturity_gap_analysis=maturity["maturity_gap_analysis"],
            recurrence_program_effectiveness_summary=program_effectiveness["program_effectiveness_summary"],
            recurrence_portfolio_summary=recurrence_portfolio.get("portfolio_summary")
            if isinstance(recurrence_portfolio.get("portfolio_summary"), Mapping)
            else None,
            recurrence_forecast_summary=recurrence_forecast.get("forecast_summary")
            if isinstance(recurrence_forecast.get("forecast_summary"), Mapping)
            else None,
            recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
            if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
            else None,
            recurrence_remediation_effectiveness_summary=program_effectiveness[
                "remediation_effectiveness_summary"
            ],
            portfolio_trajectory_summary=program_effectiveness["portfolio_trajectory_summary"],
            total_observations=int(recurrence_history.get("total_rows") or 0),
            total_keys=int(recurrence_history.get("unique_recurrence_count") or 0),
        )
        completion = build_recurrence_completion_assessment(
            recurrence_maturity_summary=maturity["recurrence_maturity_summary"],
            recurrence_program_effectiveness_summary=program_effectiveness["program_effectiveness_summary"],
            recurrence_target_state=roadmap["recurrence_target_state"],
            recurrence_roadmap_summary=roadmap["recurrence_roadmap_summary"],
            recurrence_history={
                **recurrence_history,
                "recurrence_timeline": list(recurrence_timeline or ()),
                "recurrence_trends": recurrence_trends or {},
                "recurrence_forecast": recurrence_forecast,
                "recurrence_portfolio": recurrence_portfolio,
                "recurrence_portfolio_summary": recurrence_portfolio.get("portfolio_summary"),
                "recurrence_governance": recurrence_governance,
                "recurrence_governance_summary": recurrence_governance.get("governance_summary"),
                "recurrence_retirement_summary": recurrence_governance.get("retirement_summary"),
                "recurrence_lifecycle": recurrence_lifecycle,
                "recurrence_lifecycle_summary": recurrence_lifecycle.get("lifecycle_summary"),
                "recurrence_transition_summary": recurrence_lifecycle.get("transition_summary"),
                "recurrence_age_distribution": recurrence_lifecycle.get("age_distribution"),
                "recurrence_closure_effectiveness": recurrence_lifecycle.get("closure_effectiveness"),
                "recurrence_remediation_targets": recurrence_remediation_targets,
                "recurrence_remediation_summary": recurrence_remediation_targets.get("remediation_summary"),
                "recurrence_roi": recurrence_roi,
                "recurrence_roi_summary": recurrence_roi.get("roi_summary"),
            },
            recurrence_governance_summary=recurrence_governance.get("governance_summary")
            if isinstance(recurrence_governance.get("governance_summary"), Mapping)
            else None,
            recurrence_forecast_summary=recurrence_forecast.get("forecast_summary")
            if isinstance(recurrence_forecast.get("forecast_summary"), Mapping)
            else None,
            forecast_effectiveness_summary=program_effectiveness["forecast_effectiveness_summary"],
            remediation_effectiveness_summary=program_effectiveness["remediation_effectiveness_summary"],
            recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
            if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
            else None,
            recurrence_roi_summary=recurrence_roi.get("roi_summary")
            if isinstance(recurrence_roi.get("roi_summary"), Mapping)
            else None,
            portfolio_trajectory_summary=program_effectiveness["portfolio_trajectory_summary"],
        )
        graduation_audit = build_recurrence_graduation_audit(
            recurrence_history={
                **recurrence_history,
                "recurrence_timeline": list(recurrence_timeline or ()),
                "recurrence_trends": recurrence_trends or {},
                "recurrence_forecast": recurrence_forecast,
                "recurrence_portfolio": recurrence_portfolio,
                "recurrence_portfolio_summary": recurrence_portfolio.get("portfolio_summary"),
                "recurrence_governance": recurrence_governance,
                "recurrence_governance_summary": recurrence_governance.get("governance_summary"),
                "recurrence_lifecycle": recurrence_lifecycle,
                "recurrence_lifecycle_summary": recurrence_lifecycle.get("lifecycle_summary"),
                "recurrence_program_effectiveness": program_effectiveness,
                "recurrence_program_effectiveness_summary": program_effectiveness[
                    "program_effectiveness_summary"
                ],
                "recurrence_maturity": maturity,
                "recurrence_maturity_summary": maturity["recurrence_maturity_summary"],
                "recurrence_roadmap": roadmap,
                "recurrence_roadmap_summary": roadmap["recurrence_roadmap_summary"],
                "recurrence_completion": completion,
                "recurrence_completion_summary": completion["recurrence_completion_summary"],
                "portfolio_trajectory_summary": program_effectiveness["portfolio_trajectory_summary"],
                "stability_trajectory_summary": program_effectiveness["stability_trajectory_summary"],
                "recurrence_trajectory_summary": trajectory_summary,
            },
            recurrence_trends=recurrence_trends,
            recurrence_forecast=recurrence_forecast,
            recurrence_portfolio=recurrence_portfolio,
            recurrence_remediation=recurrence_remediation_targets,
            recurrence_roi=recurrence_roi,
            recurrence_governance=recurrence_governance,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_program_effectiveness=program_effectiveness,
            recurrence_maturity=maturity,
            recurrence_roadmap=roadmap,
            recurrence_completion=completion,
        )
        trajectory_summary = summarize_recurrence_trajectory(projected_history)

    write_recurrence_trajectory_history(projected_history, trajectory_history_path)
    return {
        "recurrence_trajectory_history": projected_history,
        "recurrence_trajectory_summary": trajectory_summary,
        "recurrence_program_effectiveness": program_effectiveness,
        "recurrence_maturity": maturity,
        "recurrence_roadmap": roadmap,
        "recurrence_completion": completion,
        "recurrence_graduation_audit": graduation_audit,
    }


RECURRENCE_PROGRAM_EFFECTIVENESS_SCORE_DEFINITION = (
    "Advisory 0-100 score: 100 * clamp01(0.20*closure_rate + 0.20*(forecast_accuracy*forecast_confidence) "
    "+ 0.20*(stability_score/100) + 0.15*(1-regression_rate) + 0.15*(governance_health_score/100) "
    "+ 0.10*(lifecycle_health_score/100)) * (1 - 0.30*watchlist_pressure), where watchlist_pressure is "
    "watchlist_size/max(total_keys,1). Higher scores indicate improving program outcomes."
)
RECURRENCE_EFFECTIVENESS_CONFIDENCE_DEFINITION = (
    "Weighted blend of forecast_confidence (35%), governance_confidence (35%), and "
    "observation/key volume factor min(1, observations/5)*min(1, keys/3) scaled by 0.4 when "
    "trajectory history is unavailable (30%)."
)


def _effectiveness_confidence(
    *,
    total_observations: int,
    total_keys: int,
    forecast_confidence: float,
    governance_confidence: float,
    trajectory_available: bool,
) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 0)
    volume_factor = min(1.0, observations / float(RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_OBSERVATIONS))
    volume_factor *= min(1.0, keys / float(RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS))
    if not trajectory_available:
        volume_factor *= 0.4
    return round(
        0.35 * float(forecast_confidence or 0.0)
        + 0.35 * float(governance_confidence or 0.0)
        + 0.30 * volume_factor,
        2,
    )


def _forecast_lifecycle_aligned(forecast_classification: str, lifecycle_stage: str) -> bool:
    forecast = str(forecast_classification or "").strip()
    stage = str(lifecycle_stage or "").strip()
    allowed = RECURRENCE_FORECAST_LIFECYCLE_ALIGNMENT.get(forecast)
    return stage in allowed if allowed else False


def _governance_status_counts_from_watchlist(
    watchlist: Sequence[Mapping[str, Any]] | None,
) -> dict[str, int]:
    counts = {status: 0 for status in sorted(RECURRENCE_GOVERNANCE_STATUSES)}
    for entry in watchlist or ():
        if not isinstance(entry, Mapping):
            continue
        status = str(entry.get("governance_status") or RECURRENCE_GOVERNANCE_OBSERVE).strip()
        if status in counts:
            counts[status] += 1
    return counts


def calculate_recurrence_effectiveness_metrics(
    *,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_remediation_summary: Mapping[str, Any] | None = None,
    recurrence_roi_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_governance_summary: Mapping[str, Any] | None = None,
    prior_program_effectiveness: Mapping[str, Any] | None = None,
    trajectory_available: bool | None = None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence program effectiveness metrics."""
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    remediation_summary = (
        recurrence_remediation_summary if isinstance(recurrence_remediation_summary, Mapping) else {}
    )
    roi_summary = recurrence_roi_summary if isinstance(recurrence_roi_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    targets = recurrence_remediation_targets if isinstance(recurrence_remediation_targets, Mapping) else {}
    governance_summary = (
        recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    )
    prior = prior_program_effectiveness if isinstance(prior_program_effectiveness, Mapping) else {}

    watchlist = [
        dict(row) for row in (governance.get("watchlist") or ()) if isinstance(row, Mapping)
    ]
    lifecycle_keys = [
        dict(row) for row in (lifecycle.get("keys") or ()) if isinstance(row, Mapping)
    ]
    if not lifecycle_keys and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle_keys = [
            dict(row)
            for row in (history["recurrence_lifecycle"].get("keys") or ())
            if isinstance(row, Mapping)
        ]
    lifecycle_by_key = {
        str(row.get("recurrence_key") or ""): row for row in lifecycle_keys if str(row.get("recurrence_key") or "")
    }
    remediation_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (targets.get("keys") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }

    total_keys = int(
        lifecycle_summary.get("active_keys", 0)
        + lifecycle_summary.get("dormant_keys", 0)
        + lifecycle_summary.get("retired_keys", 0)
        or history.get("unique_recurrence_count")
        or len(lifecycle_keys)
        or 0
    )
    total_observations = int(history.get("total_rows") or targets.get("total_observations") or 0)
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    forecast_confidence = float(
        forecast_summary.get("forecast_confidence") or portfolio_summary.get("forecast_confidence") or 0.0
    )
    governance_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    stability_score_current = float(forecast_summary.get("stability_score") or 100.0)
    regression_rate_current = _regression_rate_value(history.get("regression_recurrence_rate"))
    portfolio_risk_current = float(portfolio_summary.get("portfolio_risk_score") or 0.0)
    concentration_current = max(
        float(portfolio_summary.get("owner_concentration_ratio") or 0.0),
        float(portfolio_summary.get("category_concentration_ratio") or 0.0),
        float(portfolio_summary.get("field_path_concentration_ratio") or 0.0),
        float(portfolio_summary.get("scenario_concentration_ratio") or 0.0),
    )
    governance_health_current = float(
        governance_summary.get("governance_health_score") or governance.get("governance_health_score") or 0.0
    )
    lifecycle_health_current = float(
        lifecycle_summary.get("lifecycle_health_score") or lifecycle.get("lifecycle_health_score") or 0.0
    )
    closure_rate = float(lifecycle_summary.get("closure_rate") or 0.0)
    watchlist_size = int(governance_summary.get("watchlist_size") or len(watchlist) or 0)

    prior_summary = prior.get("program_effectiveness_summary")
    if not isinstance(prior_summary, Mapping):
        prior_summary = prior.get("recurrence_program_effectiveness_summary")
    if not isinstance(prior_summary, Mapping):
        prior_summary = {}
    prior_portfolio = prior.get("portfolio_trajectory_summary")
    if not isinstance(prior_portfolio, Mapping):
        prior_portfolio = {}
    prior_stability = prior.get("stability_trajectory_summary")
    if not isinstance(prior_stability, Mapping):
        prior_stability = {}
    if trajectory_available is None:
        trajectory_available = bool(prior_summary)
    trajectory_available = bool(trajectory_available)

    status_counts = _governance_status_counts_from_watchlist(watchlist)
    watch_keys = int(status_counts.get(RECURRENCE_GOVERNANCE_WATCH) or 0)
    investigate_keys = int(status_counts.get(RECURRENCE_GOVERNANCE_INVESTIGATE) or 0)
    prioritize_keys = int(status_counts.get(RECURRENCE_GOVERNANCE_PRIORITIZE) or 0)
    retire_candidates = int(status_counts.get(RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE) or 0)
    retirement_outcome_keys = retire_candidates + int(lifecycle_summary.get("retired_keys") or 0) + int(
        lifecycle_summary.get("dormant_keys") or 0
    )
    remediation_ready_keys = sum(
        1
        for row in watchlist
        if str(row.get("governance_status") or "") == RECURRENCE_GOVERNANCE_PRIORITIZE
        and float(remediation_by_key.get(str(row.get("recurrence_key") or ""), {}).get("reduction_potential") or 0.0)
        >= RECURRENCE_GOVERNANCE_INVESTIGATE_THRESHOLD
    )
    total_governed_keys = max(len(watchlist), 1)
    watchlist_conversion_rate = round(investigate_keys / float(max(watch_keys, 1)), 4)
    investigate_conversion_rate = round(prioritize_keys / float(max(investigate_keys, 1)), 4)
    prioritize_conversion_rate = round(remediation_ready_keys / float(max(prioritize_keys, 1)), 4)
    retirement_conversion_rate = round(retirement_outcome_keys / float(total_governed_keys), 4)
    governance_effectiveness = round(
        (
            watchlist_conversion_rate
            + investigate_conversion_rate
            + prioritize_conversion_rate
            + retirement_conversion_rate
        )
        / 4.0,
        4,
    )

    targeted_keys = int(targets.get("total_keys") or len(remediation_by_key) or 0)
    if targeted_keys <= 0 and remediation_summary.get("highest_leverage_key"):
        targeted_keys = 1
    improved_keys = 0
    unresolved_keys = 0
    resolved_or_retired_keys = 0
    for key, remediation_row in remediation_by_key.items():
        lifecycle_row = lifecycle_by_key.get(key, {})
        stage = str(lifecycle_row.get("lifecycle_stage") or "")
        if stage in {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}:
            improved_keys += 1
            resolved_or_retired_keys += 1
        else:
            unresolved_keys += 1
    historically_targeted_keys = max(targeted_keys, 1)
    recurrence_reduction_rate = round(resolved_or_retired_keys / float(historically_targeted_keys), 4)
    remediation_effectiveness = round(
        (recurrence_reduction_rate + (1.0 - unresolved_keys / float(max(targeted_keys, 1)))) / 2.0,
        4,
    )

    forecast_rows = [
        dict(row) for row in (forecast.get("key_forecasts") or ()) if isinstance(row, Mapping)
    ]
    predicted_recurrences = 0
    realized_recurrences = 0
    aligned_forecasts = 0
    for row in forecast_rows:
        key = str(row.get("recurrence_key") or "")
        forecast_classification = str(row.get("forecast_classification") or "")
        lifecycle_stage = str(lifecycle_by_key.get(key, {}).get("lifecycle_stage") or "")
        if forecast_classification in {
            RECURRENCE_FORECAST_WATCH,
            RECURRENCE_FORECAST_ELEVATED,
            RECURRENCE_FORECAST_CONCENTRATED,
        }:
            predicted_recurrences += 1
        if _forecast_lifecycle_aligned(forecast_classification, lifecycle_stage):
            aligned_forecasts += 1
            realized_recurrences += 1
    forecast_key_count = max(len(forecast_rows), 1)
    forecast_accuracy = round(aligned_forecasts / float(forecast_key_count), 4)
    forecast_effectiveness = round(forecast_accuracy * forecast_confidence, 4)

    portfolio_risk_baseline = float(
        prior_portfolio.get("portfolio_risk_current") or portfolio_risk_current
    )
    concentration_baseline = float(
        prior_portfolio.get("concentration_current") or concentration_current
    )
    governance_health_baseline = float(
        prior_portfolio.get("governance_health_current") or governance_health_current
    )
    lifecycle_health_baseline = float(
        prior_portfolio.get("lifecycle_health_current") or lifecycle_health_current
    )

    if trajectory_available:
        stability_score_baseline = float(
            prior_stability.get("stability_score_current") or stability_score_current
        )
        regression_rate_baseline = float(
            prior_stability.get("recurrence_rate_current")
            if prior_stability.get("recurrence_rate_current") is not None
            else regression_rate_current
        )
        stability_change = round(stability_score_current - stability_score_baseline, 4)
        recurrence_rate_change = round(regression_rate_current - regression_rate_baseline, 4)
        portfolio_risk_change = round(portfolio_risk_current - portfolio_risk_baseline, 4)
        concentration_change = round(concentration_current - concentration_baseline, 4)
        governance_health_change = round(governance_health_current - governance_health_baseline, 4)
        lifecycle_health_change = round(lifecycle_health_current - lifecycle_health_baseline, 4)
    else:
        stability_score_baseline = stability_score_current
        regression_rate_baseline = regression_rate_current
        portfolio_risk_baseline = portfolio_risk_current
        concentration_baseline = concentration_current
        governance_health_baseline = governance_health_current
        lifecycle_health_baseline = lifecycle_health_current
        stability_change = 0.0
        recurrence_rate_change = 0.0
        portfolio_risk_change = 0.0
        concentration_change = 0.0
        governance_health_change = 0.0
        lifecycle_health_change = 0.0

    watchlist_pressure = min(1.0, watchlist_size / float(max(total_keys, 1)))
    if total_keys <= 0:
        program_effectiveness_score = 0.0
    else:
        blended = (
            0.20 * closure_rate
            + 0.20 * forecast_effectiveness
            + 0.20 * (stability_score_current / 100.0)
            + 0.15 * (1.0 - regression_rate_current)
            + 0.15 * (governance_health_current / 100.0)
            + 0.10 * (lifecycle_health_current / 100.0)
        )
        program_effectiveness_score = round(
            max(0.0, min(100.0, 100.0 * blended * (1.0 - 0.30 * watchlist_pressure))),
            1,
        )
    effectiveness_confidence = _effectiveness_confidence(
        total_observations=total_observations,
        total_keys=total_keys,
        forecast_confidence=forecast_confidence,
        governance_confidence=governance_confidence,
        trajectory_available=trajectory_available,
    )

    return {
        "total_keys": total_keys,
        "total_observations": total_observations,
        "trajectory_available": trajectory_available,
        "baseline_only": not trajectory_available,
        "governance_effectiveness": governance_effectiveness,
        "watchlist_conversion_rate": watchlist_conversion_rate,
        "investigate_conversion_rate": investigate_conversion_rate,
        "prioritize_conversion_rate": prioritize_conversion_rate,
        "retirement_conversion_rate": retirement_conversion_rate,
        "targeted_keys": targeted_keys,
        "improved_keys": improved_keys,
        "unresolved_keys": unresolved_keys,
        "recurrence_reduction_rate": recurrence_reduction_rate,
        "remediation_effectiveness": remediation_effectiveness,
        "forecast_accuracy": forecast_accuracy,
        "forecast_confidence": forecast_confidence,
        "predicted_recurrences": predicted_recurrences,
        "realized_recurrences": realized_recurrences,
        "forecast_effectiveness": forecast_effectiveness,
        "portfolio_risk_current": portfolio_risk_current,
        "portfolio_risk_baseline": portfolio_risk_baseline,
        "portfolio_risk_change": portfolio_risk_change,
        "concentration_current": concentration_current,
        "concentration_baseline": concentration_baseline,
        "concentration_change": concentration_change,
        "stability_score_current": stability_score_current,
        "stability_score_baseline": stability_score_baseline,
        "stability_change": stability_change,
        "recurrence_rate_current": regression_rate_current,
        "recurrence_rate_baseline": regression_rate_baseline,
        "recurrence_rate_change": recurrence_rate_change,
        "governance_health_current": governance_health_current,
        "governance_health_baseline": governance_health_baseline,
        "governance_health_change": governance_health_change,
        "lifecycle_health_current": lifecycle_health_current,
        "lifecycle_health_baseline": lifecycle_health_baseline,
        "lifecycle_health_change": lifecycle_health_change,
        "program_effectiveness_score": program_effectiveness_score,
        "effectiveness_confidence": effectiveness_confidence,
        "closure_rate": closure_rate,
        "watchlist_pressure": watchlist_pressure,
    }


def summarize_recurrence_program_effectiveness(
    effectiveness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence program effectiveness."""
    source = effectiveness if isinstance(effectiveness, Mapping) else {}
    program_summary = source.get("program_effectiveness_summary")
    if isinstance(program_summary, Mapping):
        return dict(program_summary)
    metrics = source.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = calculate_recurrence_effectiveness_metrics()
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "program_effectiveness_score": float(metrics.get("program_effectiveness_score") or 0.0),
        "governance_effectiveness": float(metrics.get("governance_effectiveness") or 0.0),
        "remediation_effectiveness": float(metrics.get("remediation_effectiveness") or 0.0),
        "forecast_effectiveness": float(metrics.get("forecast_effectiveness") or 0.0),
        "stability_trajectory": {
            "stability_score_current": float(metrics.get("stability_score_current") or 0.0),
            "stability_change": float(metrics.get("stability_change") or 0.0),
            "recurrence_rate_change": float(metrics.get("recurrence_rate_change") or 0.0),
            "trajectory_available": bool(metrics.get("trajectory_available")),
        },
        "effectiveness_confidence": float(metrics.get("effectiveness_confidence") or 0.0),
        "recurrence_reduction_rate": float(metrics.get("recurrence_reduction_rate") or 0.0),
        "forecast_accuracy": float(metrics.get("forecast_accuracy") or 0.0),
        "stability_change": float(metrics.get("stability_change") or 0.0),
        "program_effectiveness_score_definition": RECURRENCE_PROGRAM_EFFECTIVENESS_SCORE_DEFINITION,
        "effectiveness_confidence_definition": RECURRENCE_EFFECTIVENESS_CONFIDENCE_DEFINITION,
    }


def build_recurrence_program_effectiveness(
    *,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_remediation_summary: Mapping[str, Any] | None = None,
    recurrence_roi_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    prior_program_effectiveness: Mapping[str, Any] | None = None,
    trajectory_available: bool | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence program effectiveness analytics."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    governance_summary = history.get("recurrence_governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}

    prior = prior_program_effectiveness
    if prior is None and isinstance(history.get("recurrence_program_effectiveness"), Mapping):
        prior = history["recurrence_program_effectiveness"]

    metrics = calculate_recurrence_effectiveness_metrics(
        recurrence_governance=governance,
        recurrence_remediation_summary=recurrence_remediation_summary,
        recurrence_roi_summary=recurrence_roi_summary,
        recurrence_lifecycle_summary=recurrence_lifecycle_summary,
        recurrence_portfolio_summary=recurrence_portfolio_summary,
        recurrence_forecast=recurrence_forecast,
        recurrence_history=history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_governance_summary=governance_summary,
        prior_program_effectiveness=prior,
        trajectory_available=trajectory_available,
    )

    governance_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "watchlist_conversion_rate": metrics["watchlist_conversion_rate"],
        "investigate_conversion_rate": metrics["investigate_conversion_rate"],
        "prioritize_conversion_rate": metrics["prioritize_conversion_rate"],
        "retirement_conversion_rate": metrics["retirement_conversion_rate"],
        "governance_effectiveness": metrics["governance_effectiveness"],
        "conversion_definition": RECURRENCE_GOVERNANCE_CONVERSION_DEFINITION,
        "confidence_adjusted": not bool(metrics["trajectory_available"]),
    }
    remediation_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "targeted_keys": metrics["targeted_keys"],
        "improved_keys": metrics["improved_keys"],
        "unresolved_keys": metrics["unresolved_keys"],
        "recurrence_reduction_rate": metrics["recurrence_reduction_rate"],
        "remediation_effectiveness": metrics["remediation_effectiveness"],
        "effectiveness_definition": RECURRENCE_REMEDIATION_EFFECTIVENESS_DEFINITION,
    }
    forecast_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "forecast_accuracy": metrics["forecast_accuracy"],
        "forecast_confidence": metrics["forecast_confidence"],
        "predicted_recurrences": metrics["predicted_recurrences"],
        "realized_recurrences": metrics["realized_recurrences"],
        "forecast_effectiveness": metrics["forecast_effectiveness"],
        "low_confidence": metrics["effectiveness_confidence"] < 0.25,
        "effectiveness_definition": RECURRENCE_FORECAST_EFFECTIVENESS_DEFINITION,
    }
    portfolio_trajectory_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "trajectory_available": metrics["trajectory_available"],
        "baseline_only": metrics["baseline_only"],
        "portfolio_risk_current": metrics["portfolio_risk_current"],
        "portfolio_risk_baseline": metrics["portfolio_risk_baseline"],
        "portfolio_risk_change": metrics["portfolio_risk_change"],
        "concentration_current": metrics["concentration_current"],
        "concentration_baseline": metrics["concentration_baseline"],
        "concentration_change": metrics["concentration_change"],
        "governance_health_current": metrics["governance_health_current"],
        "governance_health_baseline": metrics["governance_health_baseline"],
        "governance_health_change": metrics["governance_health_change"],
        "lifecycle_health_current": metrics["lifecycle_health_current"],
        "lifecycle_health_baseline": metrics["lifecycle_health_baseline"],
        "lifecycle_health_change": metrics["lifecycle_health_change"],
        "trajectory_definition": RECURRENCE_PORTFOLIO_TRAJECTORY_DEFINITION,
    }
    stability_trajectory_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "trajectory_available": metrics["trajectory_available"],
        "baseline_only": metrics["baseline_only"],
        "stability_score_current": metrics["stability_score_current"],
        "stability_score_baseline": metrics["stability_score_baseline"],
        "stability_change": metrics["stability_change"],
        "recurrence_rate_current": metrics["recurrence_rate_current"],
        "recurrence_rate_baseline": metrics["recurrence_rate_baseline"],
        "recurrence_rate_change": metrics["recurrence_rate_change"],
        "trajectory_definition": RECURRENCE_STABILITY_TRAJECTORY_DEFINITION,
    }
    program_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "program_effectiveness_score": metrics["program_effectiveness_score"],
        "governance_effectiveness": metrics["governance_effectiveness"],
        "remediation_effectiveness": metrics["remediation_effectiveness"],
        "forecast_effectiveness": metrics["forecast_effectiveness"],
        "stability_trajectory": {
            "stability_score_current": metrics["stability_score_current"],
            "stability_change": metrics["stability_change"],
            "recurrence_rate_change": metrics["recurrence_rate_change"],
            "trajectory_available": metrics["trajectory_available"],
        },
        "effectiveness_confidence": metrics["effectiveness_confidence"],
        "recurrence_reduction_rate": metrics["recurrence_reduction_rate"],
        "forecast_accuracy": metrics["forecast_accuracy"],
        "stability_change": metrics["stability_change"],
        "program_effectiveness_score_definition": RECURRENCE_PROGRAM_EFFECTIVENESS_SCORE_DEFINITION,
        "effectiveness_confidence_definition": RECURRENCE_EFFECTIVENESS_CONFIDENCE_DEFINITION,
    }

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "effectiveness_metrics": metrics,
        "governance_effectiveness_summary": governance_effectiveness_summary,
        "remediation_effectiveness_summary": remediation_effectiveness_summary,
        "forecast_effectiveness_summary": forecast_effectiveness_summary,
        "portfolio_trajectory_summary": portfolio_trajectory_summary,
        "stability_trajectory_summary": stability_trajectory_summary,
        "program_effectiveness_summary": program_effectiveness_summary,
    }


def enrich_recurrence_history_with_program_effectiveness(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay program effectiveness fields."""
    payload = dict(history)
    effectiveness = build_recurrence_program_effectiveness(
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_remediation_summary=payload.get("recurrence_remediation_summary")
        if isinstance(payload.get("recurrence_remediation_summary"), Mapping)
        else None,
        recurrence_roi_summary=payload.get("recurrence_roi_summary")
        if isinstance(payload.get("recurrence_roi_summary"), Mapping)
        else None,
        recurrence_lifecycle_summary=payload.get("recurrence_lifecycle_summary")
        if isinstance(payload.get("recurrence_lifecycle_summary"), Mapping)
        else None,
        recurrence_portfolio_summary=payload.get("recurrence_portfolio_summary")
        if isinstance(payload.get("recurrence_portfolio_summary"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_remediation_targets=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
    )
    payload["recurrence_program_effectiveness"] = effectiveness
    payload["recurrence_program_effectiveness_summary"] = effectiveness["program_effectiveness_summary"]
    payload["governance_effectiveness_summary"] = effectiveness["governance_effectiveness_summary"]
    payload["remediation_effectiveness_summary"] = effectiveness["remediation_effectiveness_summary"]
    payload["forecast_effectiveness_summary"] = effectiveness["forecast_effectiveness_summary"]
    payload["portfolio_trajectory_summary"] = effectiveness["portfolio_trajectory_summary"]
    payload["stability_trajectory_summary"] = effectiveness["stability_trajectory_summary"]
    return payload


RECURRENCE_MATURITY_TARGET_SCORE = 80.0
RECURRENCE_MATURITY_LEVEL_INITIAL = "initial"
RECURRENCE_MATURITY_LEVEL_DEVELOPING = "developing"
RECURRENCE_MATURITY_LEVEL_MANAGED = "managed"
RECURRENCE_MATURITY_LEVEL_MEASURED = "measured"
RECURRENCE_MATURITY_LEVEL_OPTIMIZED = "optimized"
RECURRENCE_MATURITY_LEVEL_THRESHOLDS: tuple[tuple[str, int, int], ...] = (
    (RECURRENCE_MATURITY_LEVEL_INITIAL, 0, 19),
    (RECURRENCE_MATURITY_LEVEL_DEVELOPING, 20, 39),
    (RECURRENCE_MATURITY_LEVEL_MANAGED, 40, 59),
    (RECURRENCE_MATURITY_LEVEL_MEASURED, 60, 79),
    (RECURRENCE_MATURITY_LEVEL_OPTIMIZED, 80, 100),
)
RECURRENCE_MATURITY_LEVEL_DEFINITION = (
    "Maturity levels map 0-100 scores to capability stages: "
    "0-19 Initial, 20-39 Developing, 40-59 Managed, 60-79 Measured, 80-100 Optimized."
)
RECURRENCE_MATURITY_DIMENSION_WEIGHTS: dict[str, float] = {
    "observability": 0.20,
    "governance": 0.15,
    "forecasting": 0.15,
    "remediation": 0.15,
    "lifecycle": 0.15,
    "operational_readiness": 0.20,
}
RECURRENCE_MATURITY_OVERALL_SCORE_DEFINITION = (
    "Advisory 0-100 weighted maturity score: "
    "20% observability + 15% governance + 15% forecasting + 15% remediation "
    "+ 15% lifecycle + 20% operational_readiness. Higher scores indicate a more "
    "mature recurrence capability independent of program outcome effectiveness."
)
RECURRENCE_MATURITY_GAP_PRIORITY_DEFINITION = (
    "Improvement priority from current_score and gap to target (80): "
    "critical when current_score < 20 or gap >= 40; high when current_score < 40 or gap >= 25; "
    "medium when gap >= 15; otherwise low."
)
RECURRENCE_MATURITY_MIN_OBSERVATIONS = RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_OBSERVATIONS
RECURRENCE_MATURITY_MIN_KEYS = RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS


def _clamp_maturity_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value or 0.0))), 1)


def _maturity_volume_factor(*, total_observations: int, total_keys: int) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 0)
    return min(1.0, observations / float(RECURRENCE_MATURITY_MIN_OBSERVATIONS)) * min(
        1.0, keys / float(RECURRENCE_MATURITY_MIN_KEYS)
    )


def _recurrence_maturity_level(score: float) -> str:
    bounded = round(max(0.0, min(100.0, float(score or 0.0))))
    for level, lower, upper in RECURRENCE_MATURITY_LEVEL_THRESHOLDS:
        if lower <= bounded <= upper:
            return level
    return RECURRENCE_MATURITY_LEVEL_OPTIMIZED


def _recurrence_maturity_level_label(level: str) -> str:
    return str(level or RECURRENCE_MATURITY_LEVEL_INITIAL).replace("_", " ").title()


def _maturity_dimension_result(*, score: float, confidence: float, rationale: str) -> dict[str, Any]:
    bounded_score = _clamp_maturity_score(score)
    return {
        "maturity_score": bounded_score,
        "maturity_level": _recurrence_maturity_level(bounded_score),
        "confidence": round(max(0.0, min(1.0, float(confidence or 0.0))), 2),
        "rationale": rationale,
    }


def _maturity_improvement_priority(*, current_score: float, gap: float) -> str:
    score = float(current_score or 0.0)
    gap_value = float(gap or 0.0)
    if score < 20.0 or gap_value >= 40.0:
        return "critical"
    if score < 40.0 or gap_value >= 25.0:
        return "high"
    if gap_value >= 15.0:
        return "medium"
    return "low"


def _score_observability_maturity(
    *,
    recurrence_history: Mapping[str, Any],
    recurrence_trends: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_portfolio: Mapping[str, Any] | None,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    portfolio_trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(portfolio_trajectory, Mapping):
        portfolio_trajectory = {}

    signals = {
        "recurrence_history": bool(history.get("unique_recurrence_count") or history.get("summary")),
        "trend_analytics": bool(trends) and (
            trends.get("total_keys") is not None
            or trends.get("growth_rate") is not None
            or trends.get("top_recurring_keys") is not None
        ),
        "forecasting": bool(forecast.get("key_forecasts") or forecast.get("forecast_summary")),
        "portfolio_analytics": bool(
            portfolio.get("portfolio_summary") or history.get("recurrence_portfolio_summary")
        ),
        "governance_signals": bool(governance.get("watchlist") or governance.get("governance_summary")),
        "longitudinal_measurements": bool(
            portfolio_trajectory.get("trajectory_available")
            or total_observations >= 2
            or (
                isinstance(history.get("recurrence_timeline"), list)
                and bool(history.get("recurrence_timeline"))
            )
        ),
    }
    presence_ratio = sum(1 for present in signals.values() if present) / float(len(signals))
    presence_score = presence_ratio * 70.0
    completeness_bonus = 0.0
    if history.get("recurrence_timeline"):
        completeness_bonus += 3.0
    if history.get("recurrence_roi") or history.get("recurrence_roi_summary"):
        completeness_bonus += 3.0
    if history.get("recurrence_remediation_targets") or history.get("recurrence_remediation_summary"):
        completeness_bonus += 4.0
    volume_quality = _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    ) * 20.0
    score = presence_score + completeness_bonus + volume_quality
    confidence = round(0.35 + 0.45 * presence_ratio + 0.20 * _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    ), 2)
    present_labels = [name for name, present in signals.items() if present]
    missing_labels = [name for name, present in signals.items() if not present]
    rationale = (
        f"Observability reflects analytics coverage ({len(present_labels)}/{len(signals)} signals present: "
        f"{', '.join(present_labels) or 'none'}). "
    )
    if missing_labels:
        rationale += f"Missing: {', '.join(missing_labels)}. "
    rationale += (
        f"Volume quality factor {_maturity_volume_factor(total_observations=total_observations, total_keys=total_keys):.2f} "
        f"from {total_observations} observations across {total_keys} keys."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_governance_maturity(
    *,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = history.get("recurrence_governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}
    watchlist = [row for row in (governance.get("watchlist") or ()) if isinstance(row, Mapping)]
    owners = [row for row in (governance.get("owners") or ()) if isinstance(row, Mapping)]
    retirement_summary = governance.get("retirement_summary")
    if not isinstance(retirement_summary, Mapping):
        retirement_summary = history.get("recurrence_retirement_summary")
    accountability = bool(watchlist) and all(
        str(row.get("governance_status") or "").strip() for row in watchlist
    )
    structure_signals = [
        bool(watchlist),
        bool(owners),
        bool(retirement_summary),
        accountability,
        bool(governance_summary.get("governance_health_score") is not None),
    ]
    structure_score = (sum(structure_signals) / float(len(structure_signals))) * 30.0
    governance_health = float(
        governance_summary.get("governance_health_score") or governance.get("governance_health_score") or 0.0
    )
    governance_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    health_score = governance_health * 0.25
    confidence_score = governance_confidence * 20.0
    score = structure_score + health_score + confidence_score
    confidence = round(0.40 * governance_confidence + 0.35 * (sum(structure_signals) / len(structure_signals)) + 0.25 * _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    ), 2)
    rationale = (
        f"Governance maturity from watchlist/ownership/retirement structures "
        f"({sum(structure_signals)}/{len(structure_signals)} present), "
        f"governance_health_score {governance_health:.1f}, "
        f"and governance_confidence {governance_confidence:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_forecasting_maturity(
    *,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    key_forecasts = [row for row in (forecast.get("key_forecasts") or ()) if isinstance(row, Mapping)]
    forecast_confidence = float(
        forecast_summary.get("forecast_confidence") or metrics.get("forecast_confidence") or 0.0
    )
    forecast_accuracy = float(metrics.get("forecast_accuracy") or 0.0)
    availability_score = 20.0 if key_forecasts else 0.0
    confidence_score = forecast_confidence * 35.0
    validation_score = 15.0 if key_forecasts else 0.0
    accuracy_score = forecast_accuracy * forecast_confidence * 40.0
    raw_score = availability_score + confidence_score + validation_score + accuracy_score
    volume_scale = max(0.45, _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys))
    score = raw_score * volume_scale
    confidence = round(0.50 * forecast_confidence + 0.30 * (1.0 if key_forecasts else 0.0) + 0.20 * volume_scale, 2)
    rationale = (
        f"Forecasting maturity from model availability ({len(key_forecasts)} key forecasts), "
        f"forecast_confidence {forecast_confidence:.2f}, "
        f"confidence-weighted accuracy {forecast_accuracy * forecast_confidence:.2f}, "
        f"scaled by volume factor {volume_scale:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_remediation_maturity(
    *,
    recurrence_remediation: Mapping[str, Any] | None,
    recurrence_roi: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    remediation = recurrence_remediation if isinstance(recurrence_remediation, Mapping) else {}
    roi = recurrence_roi if isinstance(recurrence_roi, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}
    remediation_summary = remediation.get("remediation_summary")
    if not isinstance(remediation_summary, Mapping):
        remediation_summary = {}
    roi_summary = roi.get("roi_summary")
    if not isinstance(roi_summary, Mapping):
        roi_summary = {}
    remediation_keys = [row for row in (remediation.get("keys") or ()) if isinstance(row, Mapping)]
    targeting_score = 20.0 if remediation_keys else (10.0 if remediation_summary else 0.0)
    roi_score = 20.0 if roi_summary else 0.0
    reduction_rate = float(metrics.get("recurrence_reduction_rate") or 0.0)
    remediation_effectiveness = float(metrics.get("remediation_effectiveness") or 0.0)
    remediation_confidence = float(remediation_summary.get("remediation_confidence") or 0.0)
    outcome_score = reduction_rate * 25.0 + remediation_effectiveness * 25.0
    structure_score = targeting_score + roi_score
    volume_scale = 0.55 + 0.45 * _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    )
    score = (structure_score + outcome_score) * volume_scale + remediation_confidence * 15.0
    confidence = round(
        0.35 * remediation_confidence
        + 0.35 * (1.0 if remediation_keys else 0.5 if remediation_summary else 0.0)
        + 0.30 * _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys),
        2,
    )
    rationale = (
        f"Remediation maturity from targeting/ROI structures "
        f"({'present' if structure_score >= 30 else 'partial' if structure_score else 'absent'}), "
        f"recurrence_reduction_rate {reduction_rate:.2f}, remediation_effectiveness "
        f"{remediation_effectiveness:.2f}, remediation_confidence {remediation_confidence:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_lifecycle_maturity(
    *,
    recurrence_lifecycle: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle_summary = lifecycle.get("lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = history.get("recurrence_lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    lifecycle_keys = [row for row in (lifecycle.get("keys") or ()) if isinstance(row, Mapping)]
    transition_summary = lifecycle.get("transition_summary")
    if not isinstance(transition_summary, Mapping):
        transition_summary = history.get("recurrence_transition_summary")
    age_distribution = lifecycle.get("age_distribution")
    if not isinstance(age_distribution, Mapping):
        age_distribution = history.get("recurrence_age_distribution")
    lifecycle_health = float(
        lifecycle_summary.get("lifecycle_health_score") or lifecycle.get("lifecycle_health_score") or 0.0
    )
    tracking_score = 15.0 if lifecycle_keys else 0.0
    transition_score = 10.0 if isinstance(transition_summary, Mapping) else 0.0
    age_score = 10.0 if isinstance(age_distribution, Mapping) else 0.0
    health_score = lifecycle_health * 0.25
    score = tracking_score + transition_score + age_score + health_score
    confidence = round(
        0.40 * (1.0 if lifecycle_keys else 0.0)
        + 0.30 * (1.0 if isinstance(transition_summary, Mapping) else 0.0)
        + 0.30 * _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys),
        2,
    )
    rationale = (
        f"Lifecycle maturity from lifecycle tracking ({len(lifecycle_keys)} keys), "
        f"transition_summary {'present' if isinstance(transition_summary, Mapping) else 'absent'}, "
        f"age_distribution {'present' if isinstance(age_distribution, Mapping) else 'absent'}, "
        f"and lifecycle_health_score {lifecycle_health:.1f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_operational_readiness_maturity(
    *,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    portfolio_trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(portfolio_trajectory, Mapping):
        portfolio_trajectory = {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}
    governance_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    effectiveness_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    forecast_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    trajectory_available = bool(portfolio_trajectory.get("trajectory_available"))
    volume_factor = _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys)
    score = (
        governance_confidence * 20.0
        + effectiveness_confidence * 20.0
        + forecast_confidence * 20.0
        + (20.0 if trajectory_available else 0.0)
        + volume_factor * 20.0
    )
    confidence = round(
        0.30 * governance_confidence
        + 0.30 * effectiveness_confidence
        + 0.20 * forecast_confidence
        + 0.20 * volume_factor,
        2,
    )
    rationale = (
        f"Operational readiness from governance_confidence {governance_confidence:.2f}, "
        f"effectiveness_confidence {effectiveness_confidence:.2f}, "
        f"forecast_confidence {forecast_confidence:.2f}, "
        f"trajectory_available {str(trajectory_available).lower()}, "
        f"and data sufficiency factor {volume_factor:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def calculate_recurrence_maturity_score(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence maturity dimension scores."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    if not trends and isinstance(history.get("recurrence_trends"), Mapping):
        trends = history["recurrence_trends"]
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    if not forecast and isinstance(history.get("recurrence_forecast"), Mapping):
        forecast = history["recurrence_forecast"]
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    if not portfolio and isinstance(history.get("recurrence_portfolio"), Mapping):
        portfolio = history["recurrence_portfolio"]
    remediation = recurrence_remediation if isinstance(recurrence_remediation, Mapping) else {}
    if not remediation and isinstance(history.get("recurrence_remediation_targets"), Mapping):
        remediation = history["recurrence_remediation_targets"]
    roi = recurrence_roi if isinstance(recurrence_roi, Mapping) else {}
    if not roi and isinstance(history.get("recurrence_roi"), Mapping):
        roi = history["recurrence_roi"]
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    if not governance and isinstance(history.get("recurrence_governance"), Mapping):
        governance = history["recurrence_governance"]
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    program_effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    if not program_effectiveness and isinstance(history.get("recurrence_program_effectiveness"), Mapping):
        program_effectiveness = history["recurrence_program_effectiveness"]

    total_keys = int(
        history.get("unique_recurrence_count")
        or (lifecycle.get("lifecycle_summary") or {}).get("active_keys")
        or len(lifecycle.get("keys") or ())
        or 0
    )
    total_observations = int(history.get("total_rows") or remediation.get("total_observations") or 0)

    observability = _score_observability_maturity(
        recurrence_history=history,
        recurrence_trends=trends,
        recurrence_forecast=forecast,
        recurrence_portfolio=portfolio,
        recurrence_governance=governance,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    governance_maturity = _score_governance_maturity(
        recurrence_governance=governance,
        recurrence_history=history,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    forecasting = _score_forecasting_maturity(
        recurrence_forecast=forecast,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    remediation_maturity = _score_remediation_maturity(
        recurrence_remediation=remediation,
        recurrence_roi=roi,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    lifecycle_maturity = _score_lifecycle_maturity(
        recurrence_lifecycle=lifecycle,
        recurrence_history=history,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    operational_readiness = _score_operational_readiness_maturity(
        recurrence_governance=governance,
        recurrence_forecast=forecast,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )

    dimension_scores = {
        "observability": observability["maturity_score"],
        "governance": governance_maturity["maturity_score"],
        "forecasting": forecasting["maturity_score"],
        "remediation": remediation_maturity["maturity_score"],
        "lifecycle": lifecycle_maturity["maturity_score"],
        "operational_readiness": operational_readiness["maturity_score"],
    }
    overall_maturity_score = round(
        sum(
            float(dimension_scores[name]) * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        1,
    )

    return {
        "total_keys": total_keys,
        "total_observations": total_observations,
        "dimension_scores": dimension_scores,
        "overall_maturity_score": _clamp_maturity_score(overall_maturity_score),
        "observability_maturity": observability,
        "governance_maturity": governance_maturity,
        "forecasting_maturity": forecasting,
        "remediation_maturity": remediation_maturity,
        "lifecycle_maturity": lifecycle_maturity,
        "operational_readiness": operational_readiness,
    }


def _build_maturity_gap_analysis(dimension_scores: Mapping[str, float]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for dimension, current_score in dimension_scores.items():
        current = float(current_score or 0.0)
        target = RECURRENCE_MATURITY_TARGET_SCORE
        gap = round(max(0.0, target - current), 1)
        gaps.append(
            {
                "dimension": dimension,
                "current_score": round(current, 1),
                "target_score": target,
                "gap": gap,
                "improvement_priority": _maturity_improvement_priority(
                    current_score=current,
                    gap=gap,
                ),
            }
        )
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda row: (priority_order.get(str(row["improvement_priority"]), 9), -float(row["gap"])))
    return gaps


def summarize_recurrence_maturity(
    maturity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence maturity scores."""
    source = maturity if isinstance(maturity, Mapping) else {}
    summary = source.get("recurrence_maturity_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    maturity_scores = source.get("maturity_scores")
    if not isinstance(maturity_scores, Mapping):
        maturity_scores = calculate_recurrence_maturity_score()
    dimension_scores = maturity_scores.get("dimension_scores")
    if not isinstance(dimension_scores, Mapping):
        dimension_scores = {}
    overall_score = float(
        maturity_scores.get("overall_maturity_score")
        or source.get("overall_maturity_score")
        or 0.0
    )
    if not dimension_scores:
        dimension_scores = {
            "observability": 0.0,
            "governance": 0.0,
            "forecasting": 0.0,
            "remediation": 0.0,
            "lifecycle": 0.0,
            "operational_readiness": 0.0,
        }
    highest_dimension = max(dimension_scores, key=lambda name: float(dimension_scores[name] or 0.0))
    lowest_dimension = min(dimension_scores, key=lambda name: float(dimension_scores[name] or 0.0))
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "overall_maturity_score": _clamp_maturity_score(overall_score),
        "overall_maturity_level": _recurrence_maturity_level(overall_score),
        "observability_score": float(dimension_scores.get("observability") or 0.0),
        "governance_score": float(dimension_scores.get("governance") or 0.0),
        "forecasting_score": float(dimension_scores.get("forecasting") or 0.0),
        "remediation_score": float(dimension_scores.get("remediation") or 0.0),
        "lifecycle_score": float(dimension_scores.get("lifecycle") or 0.0),
        "operational_readiness_score": float(dimension_scores.get("operational_readiness") or 0.0),
        "highest_dimension": highest_dimension,
        "lowest_dimension": lowest_dimension,
        "maturity_level_definition": RECURRENCE_MATURITY_LEVEL_DEFINITION,
        "overall_maturity_score_definition": RECURRENCE_MATURITY_OVERALL_SCORE_DEFINITION,
    }


def build_recurrence_maturity_assessment(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence maturity assessment analytics."""
    maturity_scores = calculate_recurrence_maturity_score(
        recurrence_history=recurrence_history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    gap_analysis = _build_maturity_gap_analysis(maturity_scores["dimension_scores"])
    maturity_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "maturity_scores": maturity_scores,
        "observability_maturity": maturity_scores["observability_maturity"],
        "governance_maturity": maturity_scores["governance_maturity"],
        "forecasting_maturity": maturity_scores["forecasting_maturity"],
        "remediation_maturity": maturity_scores["remediation_maturity"],
        "lifecycle_maturity": maturity_scores["lifecycle_maturity"],
        "operational_readiness": maturity_scores["operational_readiness"],
        "maturity_gap_analysis": gap_analysis,
        "maturity_level_definition": RECURRENCE_MATURITY_LEVEL_DEFINITION,
        "overall_maturity_score_definition": RECURRENCE_MATURITY_OVERALL_SCORE_DEFINITION,
        "maturity_gap_priority_definition": RECURRENCE_MATURITY_GAP_PRIORITY_DEFINITION,
        "dimension_weights": dict(RECURRENCE_MATURITY_DIMENSION_WEIGHTS),
    }
    recurrence_maturity_summary = summarize_recurrence_maturity(maturity_without_summary)
    return {
        **maturity_without_summary,
        "recurrence_maturity_summary": recurrence_maturity_summary,
    }


def enrich_recurrence_history_with_maturity(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay maturity fields."""
    payload = dict(history)
    maturity = build_recurrence_maturity_assessment(
        recurrence_history=payload,
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_portfolio=payload.get("recurrence_portfolio")
        if isinstance(payload.get("recurrence_portfolio"), Mapping)
        else None,
        recurrence_remediation=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_roi=payload.get("recurrence_roi")
        if isinstance(payload.get("recurrence_roi"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
    )
    payload["recurrence_maturity"] = maturity
    payload["recurrence_maturity_summary"] = maturity["recurrence_maturity_summary"]
    payload["recurrence_maturity_gap_analysis"] = maturity["maturity_gap_analysis"]
    return payload


RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME = "data_volume_expansion"
RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY = "trajectory_establishment"
RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION = "forecast_validation"
RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE = "lifecycle_closure_tracking"
RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK = "remediation_feedback_loop"
RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION = "operationalization"
RECURRENCE_ROADMAP_INITIATIVES: tuple[str, ...] = (
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
)
RECURRENCE_ROADMAP_DEFAULT_SEQUENCE: tuple[str, ...] = RECURRENCE_ROADMAP_INITIATIVES
RECURRENCE_ROADMAP_INITIATIVE_LABELS: dict[str, str] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: "Data Volume Expansion",
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: "Trajectory Establishment",
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: "Forecast Validation",
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: "Lifecycle Closure Tracking",
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: "Remediation Feedback Loop",
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: "Operationalization",
}
RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: (),
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: (RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,),
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: (
        RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
        RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
    ),
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: (RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,),
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: (
        RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
        RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    ),
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: (
        RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    ),
}
RECURRENCE_ROADMAP_INITIATIVE_BASE_COMPLEXITY: dict[str, float] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: 12.0,
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: 22.0,
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: 28.0,
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: 24.0,
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: 32.0,
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: 35.0,
}
RECURRENCE_ROADMAP_INITIATIVE_DIMENSION_DELTAS: dict[str, dict[str, float]] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: {
        "observability": 8.0,
        "governance": 12.0,
        "forecasting": 18.0,
        "remediation": 15.0,
        "lifecycle": 8.0,
        "operational_readiness": 28.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: {
        "observability": 5.0,
        "governance": 6.0,
        "forecasting": 8.0,
        "remediation": 4.0,
        "lifecycle": 6.0,
        "operational_readiness": 20.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: {
        "observability": 2.0,
        "governance": 4.0,
        "forecasting": 25.0,
        "remediation": 6.0,
        "lifecycle": 4.0,
        "operational_readiness": 8.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: {
        "observability": 2.0,
        "governance": 5.0,
        "forecasting": 4.0,
        "remediation": 6.0,
        "lifecycle": 25.0,
        "operational_readiness": 6.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: {
        "observability": 2.0,
        "governance": 6.0,
        "forecasting": 5.0,
        "remediation": 30.0,
        "lifecycle": 8.0,
        "operational_readiness": 10.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: {
        "observability": 4.0,
        "governance": 8.0,
        "forecasting": 6.0,
        "remediation": 8.0,
        "lifecycle": 6.0,
        "operational_readiness": 20.0,
    },
}
RECURRENCE_ROADMAP_MATURITY_ROI_DEFINITION = (
    "Advisory 0-100 maturity ROI: 100 * (expected_maturity_gain / implementation_complexity) "
    "/ max_initiative_raw_roi, where expected_maturity_gain is the weighted sum of projected "
    "dimension deltas using recurrence maturity dimension weights and implementation_complexity "
    "is base complexity plus 5 per dependency. Higher values indicate better maturity return "
    "per unit implementation effort."
)
RECURRENCE_ROADMAP_INVESTMENT_PRIORITY_DEFINITION = (
    "Advisory 0-100 investment priority blends maturity ROI (45%), gap alignment (35%), "
    "and readiness impact (20%). Gap alignment weights initiative dimension deltas against "
    "current maturity gap analysis; readiness impact favors initiatives that unlock "
    "downstream dependencies when volume or trajectory prerequisites are unmet."
)
RECURRENCE_ROADMAP_TARGET_STATE_DEFINITION = (
    "Optimized recurrence target state requires all maturity dimensions >= 80, "
    "operational_readiness >= 80, forecast_confidence >= 0.75, effectiveness_confidence >= 0.75, "
    "trajectory_available=true, measurable closure effectiveness, and measurable remediation "
    "effectiveness. Completion criteria are explicit boolean checks against these thresholds."
)
RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE = 0.75
RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE = 0.75
RECURRENCE_ROADMAP_LOW_VOLUME_GUIDANCE = (
    "Collect more protected replay observations before optimizing models."
)


def _roadmap_dimension_scores_from_summary(
    maturity_summary: Mapping[str, Any] | None,
) -> dict[str, float]:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    return {
        "observability": float(summary.get("observability_score") or 0.0),
        "governance": float(summary.get("governance_score") or 0.0),
        "forecasting": float(summary.get("forecasting_score") or 0.0),
        "remediation": float(summary.get("remediation_score") or 0.0),
        "lifecycle": float(summary.get("lifecycle_score") or 0.0),
        "operational_readiness": float(summary.get("operational_readiness_score") or 0.0),
    }


def _roadmap_weighted_overall_maturity(dimension_scores: Mapping[str, float]) -> float:
    return round(
        sum(
            float(dimension_scores.get(name) or 0.0) * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        1,
    )


def _roadmap_projected_dimension_scores(
    current_scores: Mapping[str, float],
    deltas: Mapping[str, float],
) -> dict[str, float]:
    projected: dict[str, float] = {}
    for dimension in RECURRENCE_MATURITY_DIMENSION_WEIGHTS:
        projected[dimension] = _clamp_maturity_score(
            float(current_scores.get(dimension) or 0.0) + float(deltas.get(dimension) or 0.0)
        )
    return projected


def _roadmap_expected_maturity_gain(dimension_deltas: Mapping[str, float]) -> float:
    return round(
        sum(
            float(dimension_deltas.get(name) or 0.0) * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        2,
    )


def _roadmap_implementation_complexity(initiative_id: str) -> float:
    dependencies = RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ())
    base = float(RECURRENCE_ROADMAP_INITIATIVE_BASE_COMPLEXITY.get(initiative_id) or 20.0)
    return round(base + 5.0 * len(dependencies), 1)


def _roadmap_gap_by_dimension(
    gap_analysis: Sequence[Mapping[str, Any]] | None,
) -> dict[str, float]:
    gaps: dict[str, float] = {}
    for row in gap_analysis or ():
        if not isinstance(row, Mapping):
            continue
        dimension = str(row.get("dimension") or "").strip()
        if dimension:
            gaps[dimension] = float(row.get("gap") or 0.0)
    return gaps


def _roadmap_volume_deficiency(
    *,
    total_observations: int,
    total_keys: int,
) -> float:
    volume_factor = _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    )
    return round(max(0.0, 1.0 - volume_factor), 2)


def _roadmap_initiative_completion_status(
    initiative_id: str,
    *,
    total_observations: int,
    total_keys: int,
    trajectory_available: bool,
    forecast_confidence: float,
    effectiveness_confidence: float,
    operational_readiness_score: float,
    lifecycle_score: float,
    remediation_score: float,
    closure_measurable: bool,
    remediation_measurable: bool,
) -> bool:
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME:
        return (
            total_observations >= RECURRENCE_MATURITY_MIN_OBSERVATIONS
            and total_keys >= RECURRENCE_MATURITY_MIN_KEYS
        )
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY:
        return trajectory_available
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION:
        return forecast_confidence >= RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE:
        return lifecycle_score >= RECURRENCE_MATURITY_TARGET_SCORE and closure_measurable
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK:
        return remediation_score >= RECURRENCE_MATURITY_TARGET_SCORE and remediation_measurable
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION:
        return operational_readiness_score >= RECURRENCE_MATURITY_TARGET_SCORE
    return False


def calculate_maturity_investment_priority(
    *,
    initiative_id: str,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    recurrence_maturity_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    maturity_roi: float | None = None,
    dependency_count: int | None = None,
) -> dict[str, Any]:
    """Calculate protected replay maturity investment priority for one initiative."""
    initiative = str(initiative_id or "").strip()
    summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    gaps = _roadmap_gap_by_dimension(recurrence_maturity_gap_analysis)
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}

    dimension_deltas = RECURRENCE_ROADMAP_INITIATIVE_DIMENSION_DELTAS.get(initiative, {})
    gap_alignment = 0.0
    if gaps and dimension_deltas:
        alignment_total = 0.0
        weight_total = 0.0
        for dimension, delta in dimension_deltas.items():
            gap = float(gaps.get(dimension) or 0.0)
            weight = RECURRENCE_MATURITY_DIMENSION_WEIGHTS.get(dimension, 0.0)
            alignment_total += min(gap, float(delta)) * weight
            weight_total += gap * weight
        gap_alignment = alignment_total / weight_total if weight_total > 0 else 0.0
    volume_deficiency = _roadmap_volume_deficiency(
        total_observations=int(program_summary.get("total_observations") or portfolio_summary.get("total_observations") or 0),
        total_keys=int(summary.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0),
    )
    readiness_impact = 0.0
    if initiative == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME:
        readiness_impact = volume_deficiency
    elif initiative == RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY:
        readiness_impact = 0.7 if volume_deficiency < 0.5 else 0.3
    elif initiative == RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION:
        readiness_impact = float(summary.get("operational_readiness_score") or 0.0) / 100.0
    else:
        readiness_impact = min(
            1.0,
            float(forecast_summary.get("forecast_confidence") or 0.0)
            + float(lifecycle_summary.get("closure_rate") or 0.0),
        ) / 2.0
    roi_component = float(maturity_roi or 0.0) / 100.0
    investment_priority_score = round(
        100.0 * (0.45 * roi_component + 0.35 * gap_alignment + 0.20 * readiness_impact),
        1,
    )
    return {
        "initiative_id": initiative,
        "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative, initiative),
        "investment_priority_score": investment_priority_score,
        "gap_alignment": round(gap_alignment, 2),
        "readiness_impact": round(readiness_impact, 2),
        "maturity_roi": round(float(maturity_roi or 0.0), 1),
        "dependency_count": int(dependency_count or len(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative, ()))),
        "investment_priority_definition": RECURRENCE_ROADMAP_INVESTMENT_PRIORITY_DEFINITION,
    }


def _build_recurrence_target_state(
    *,
    maturity_summary: Mapping[str, Any] | None,
    program_summary: Mapping[str, Any] | None,
    forecast_summary: Mapping[str, Any] | None,
    lifecycle_summary: Mapping[str, Any] | None,
    remediation_summary: Mapping[str, Any] | None,
    portfolio_trajectory: Mapping[str, Any] | None,
) -> dict[str, Any]:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    program = program_summary if isinstance(program_summary, Mapping) else {}
    forecast = forecast_summary if isinstance(forecast_summary, Mapping) else {}
    lifecycle = lifecycle_summary if isinstance(lifecycle_summary, Mapping) else {}
    remediation = remediation_summary if isinstance(remediation_summary, Mapping) else {}
    trajectory = portfolio_trajectory if isinstance(portfolio_trajectory, Mapping) else {}
    dimension_scores = _roadmap_dimension_scores_from_summary(summary)
    forecast_confidence = float(forecast.get("forecast_confidence") or 0.0)
    effectiveness_confidence = float(program.get("effectiveness_confidence") or 0.0)
    closure_measurable = "closure_rate" in lifecycle or bool(lifecycle.get("closure_rate_definition"))
    remediation_measurable = remediation.get("remediation_effectiveness") is not None or bool(
        remediation.get("effectiveness_definition")
    )
    completion_criteria = {
        "all_dimensions_optimized": all(
            float(dimension_scores.get(name) or 0.0) >= RECURRENCE_MATURITY_TARGET_SCORE
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        "operational_readiness_optimized": float(summary.get("operational_readiness_score") or 0.0)
        >= RECURRENCE_MATURITY_TARGET_SCORE,
        "forecast_confidence_target_met": forecast_confidence >= RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE,
        "effectiveness_confidence_target_met": effectiveness_confidence
        >= RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE,
        "trajectory_available": bool(trajectory.get("trajectory_available")),
        "closure_effectiveness_measurable": closure_measurable,
        "remediation_effectiveness_measurable": remediation_measurable,
    }
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "target_maturity_level": RECURRENCE_MATURITY_LEVEL_OPTIMIZED,
        "dimension_targets": {
            name: RECURRENCE_MATURITY_TARGET_SCORE for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        },
        "forecast_confidence_target": RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE,
        "effectiveness_confidence_target": RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE,
        "trajectory_required": True,
        "closure_effectiveness_measurable": True,
        "remediation_effectiveness_measurable": True,
        "completion_criteria": completion_criteria,
        "completion_criteria_met": all(completion_criteria.values()),
        "completion_criteria_definition": RECURRENCE_ROADMAP_TARGET_STATE_DEFINITION,
    }


def _build_roadmap_sequence(
    initiatives: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {
        str(row.get("initiative_id") or ""): row for row in initiatives if isinstance(row, Mapping)
    }
    sequence: list[dict[str, Any]] = []
    for step, initiative_id in enumerate(RECURRENCE_ROADMAP_DEFAULT_SEQUENCE, start=1):
        row = dict(by_id.get(initiative_id) or {})
        if not row:
            continue
        sequence.append(
            {
                "sequence_step": step,
                "initiative_id": initiative_id,
                "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative_id, initiative_id),
                "dependency_count": int(row.get("dependency_count") or 0),
                "dependencies": list(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ())),
                "completed": bool(row.get("completed")),
                "investment_priority_score": float(row.get("investment_priority_score") or 0.0),
                "maturity_roi": float(row.get("maturity_roi") or 0.0),
            }
        )
    return sequence


def build_recurrence_strategic_roadmap(
    *,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    recurrence_maturity_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_remediation_effectiveness_summary: Mapping[str, Any] | None = None,
    portfolio_trajectory_summary: Mapping[str, Any] | None = None,
    total_observations: int | None = None,
    total_keys: int | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence strategic roadmap analytics."""
    maturity_summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    gap_analysis = [
        dict(row) for row in (recurrence_maturity_gap_analysis or ()) if isinstance(row, Mapping)
    ]
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    remediation_summary = (
        recurrence_remediation_effectiveness_summary
        if isinstance(recurrence_remediation_effectiveness_summary, Mapping)
        else {}
    )
    portfolio_trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}

    current_scores = _roadmap_dimension_scores_from_summary(maturity_summary)
    current_overall = _roadmap_weighted_overall_maturity(current_scores)
    observations = int(
        total_observations
        or program_summary.get("total_observations")
        or portfolio_summary.get("total_observations")
        or 0
    )
    keys = int(total_keys or maturity_summary.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0)
    trajectory_available = bool(portfolio_trajectory.get("trajectory_available"))
    forecast_confidence = float(
        forecast_summary.get("forecast_confidence") or portfolio_summary.get("forecast_confidence") or 0.0
    )
    effectiveness_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    volume_deficiency = _roadmap_volume_deficiency(total_observations=observations, total_keys=keys)

    initiative_rows: list[dict[str, Any]] = []
    raw_rois: dict[str, float] = {}
    for initiative_id in RECURRENCE_ROADMAP_INITIATIVES:
        base_deltas = dict(RECURRENCE_ROADMAP_INITIATIVE_DIMENSION_DELTAS.get(initiative_id, {}))
        if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME:
            scale = 0.75 + 0.25 * volume_deficiency
            dimension_deltas = {
                dimension: round(float(delta) * scale, 1)
                for dimension, delta in base_deltas.items()
            }
        else:
            dimension_deltas = {dimension: round(float(delta), 1) for dimension, delta in base_deltas.items()}
        expected_gain = _roadmap_expected_maturity_gain(dimension_deltas)
        complexity = _roadmap_implementation_complexity(initiative_id)
        raw_rois[initiative_id] = expected_gain / max(complexity, 1.0)
        projected_scores = _roadmap_projected_dimension_scores(current_scores, dimension_deltas)
        maturity_impact = round(expected_gain, 2)
        readiness_impact = round(
            float(dimension_deltas.get("operational_readiness") or 0.0) / 100.0,
            2,
        )
        dependency_count = len(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ()))
        completed = _roadmap_initiative_completion_status(
            initiative_id,
            total_observations=observations,
            total_keys=keys,
            trajectory_available=trajectory_available,
            forecast_confidence=forecast_confidence,
            effectiveness_confidence=effectiveness_confidence,
            operational_readiness_score=float(current_scores.get("operational_readiness") or 0.0),
            lifecycle_score=float(current_scores.get("lifecycle") or 0.0),
            remediation_score=float(current_scores.get("remediation") or 0.0),
            closure_measurable="closure_rate" in lifecycle_summary
            or bool(lifecycle_summary.get("closure_rate_definition")),
            remediation_measurable=remediation_summary.get("remediation_effectiveness") is not None
            or bool(remediation_summary.get("effectiveness_definition")),
        )
        initiative_rows.append(
            {
                "initiative_id": initiative_id,
                "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative_id, initiative_id),
                "initiative_score": round(expected_gain + readiness_impact * 10.0, 1),
                "maturity_impact": maturity_impact,
                "readiness_impact": readiness_impact,
                "implementation_complexity": complexity,
                "dependency_count": dependency_count,
                "dependencies": list(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ())),
                "expected_maturity_gain": maturity_impact,
                "dimension_deltas": dimension_deltas,
                "projected_maturity_after_completion": {
                    "overall_maturity_score": _roadmap_weighted_overall_maturity(projected_scores),
                    "overall_maturity_level": _recurrence_maturity_level(
                        _roadmap_weighted_overall_maturity(projected_scores)
                    ),
                    "dimension_scores": projected_scores,
                },
                "completed": completed,
            }
        )

    max_raw_roi = max(raw_rois.values()) if raw_rois else 1.0
    for row in initiative_rows:
        initiative_id = str(row["initiative_id"])
        raw_roi = raw_rois.get(initiative_id, 0.0)
        row["maturity_roi"] = round(100.0 * raw_roi / max(max_raw_roi, 0.001), 1)
        priority = calculate_maturity_investment_priority(
            initiative_id=initiative_id,
            recurrence_maturity_summary=maturity_summary,
            recurrence_maturity_gap_analysis=gap_analysis,
            recurrence_program_effectiveness_summary=program_summary,
            recurrence_portfolio_summary=portfolio_summary,
            recurrence_forecast_summary=forecast_summary,
            recurrence_lifecycle_summary=lifecycle_summary,
            maturity_roi=row["maturity_roi"],
            dependency_count=row["dependency_count"],
        )
        row["investment_priority_score"] = priority["investment_priority_score"]
        row["gap_alignment"] = priority["gap_alignment"]

    initiative_rows.sort(
        key=lambda row: (
            -float(row.get("maturity_roi") or 0.0),
            -float(row.get("investment_priority_score") or 0.0),
        )
    )
    roadmap_sequence = _build_roadmap_sequence(initiative_rows)
    recurrence_target_state = _build_recurrence_target_state(
        maturity_summary=maturity_summary,
        program_summary=program_summary,
        forecast_summary=forecast_summary,
        lifecycle_summary=lifecycle_summary,
        remediation_summary=remediation_summary,
        portfolio_trajectory=portfolio_trajectory,
    )
    remaining_initiatives = [row for row in initiative_rows if not row.get("completed")]
    next_initiative = next(
        (row for row in roadmap_sequence if not row.get("completed")),
        roadmap_sequence[0] if roadmap_sequence else {},
    )
    next_initiative_id = str(next_initiative.get("initiative_id") or RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME)
    next_initiative_row = next(
        (row for row in initiative_rows if row["initiative_id"] == next_initiative_id),
        initiative_rows[0] if initiative_rows else {},
    )
    highest_roi_initiative = max(
        initiative_rows,
        key=lambda row: float(row.get("maturity_roi") or 0.0),
    )
    highest_gap_dimension = str(maturity_summary.get("lowest_dimension") or "operational_readiness")
    if gap_analysis:
        highest_gap_dimension = str(
            max(gap_analysis, key=lambda row: float(row.get("gap") or 0.0)).get("dimension")
            or highest_gap_dimension
        )
    projected_next = next_initiative_row.get("projected_maturity_after_completion") or {}
    roadmap_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "current_maturity_score": current_overall,
        "current_maturity_level": _recurrence_maturity_level(current_overall),
        "initiatives": initiative_rows,
        "roadmap_sequence": roadmap_sequence,
        "recurrence_target_state": recurrence_target_state,
        "highest_roi_initiative": highest_roi_initiative.get("initiative_id"),
        "highest_gap_dimension": highest_gap_dimension,
        "next_recommended_initiative": next_initiative_id,
        "roadmap_priority_guidance": (
            RECURRENCE_ROADMAP_LOW_VOLUME_GUIDANCE
            if volume_deficiency >= 0.5
            else "Execute roadmap sequence in dependency order to reach optimized maturity."
        ),
        "maturity_roi_definition": RECURRENCE_ROADMAP_MATURITY_ROI_DEFINITION,
        "investment_priority_definition": RECURRENCE_ROADMAP_INVESTMENT_PRIORITY_DEFINITION,
        "target_state_definition": RECURRENCE_ROADMAP_TARGET_STATE_DEFINITION,
    }
    recurrence_roadmap_summary = summarize_recurrence_roadmap(roadmap_without_summary)
    recurrence_roadmap_summary["estimated_initiatives_remaining"] = len(remaining_initiatives)
    return {
        **roadmap_without_summary,
        "recurrence_roadmap_summary": recurrence_roadmap_summary,
    }


def summarize_recurrence_roadmap(
    roadmap: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence strategic roadmap."""
    source = roadmap if isinstance(roadmap, Mapping) else {}
    summary = source.get("recurrence_roadmap_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    initiatives = [row for row in (source.get("initiatives") or ()) if isinstance(row, Mapping)]
    remaining = [row for row in initiatives if not row.get("completed")]
    next_initiative = str(
        source.get("next_recommended_initiative")
        or (remaining[0].get("initiative_id") if remaining else RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME)
    )
    next_row = next((row for row in initiatives if row.get("initiative_id") == next_initiative), {})
    projected = next_row.get("projected_maturity_after_completion") or {}
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "highest_roi_initiative": source.get("highest_roi_initiative")
        or RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
        "highest_gap_dimension": source.get("highest_gap_dimension") or "operational_readiness",
        "projected_next_maturity_level": projected.get("overall_maturity_level")
        or _recurrence_maturity_level(float(source.get("current_maturity_score") or 0.0)),
        "projected_next_maturity_score": float(projected.get("overall_maturity_score") or 0.0),
        "estimated_initiatives_remaining": len(remaining),
        "next_recommended_initiative": next_initiative,
        "roadmap_priority_guidance": source.get("roadmap_priority_guidance")
        or RECURRENCE_ROADMAP_LOW_VOLUME_GUIDANCE,
        "target_state_defined": bool(source.get("recurrence_target_state")),
    }


def enrich_recurrence_history_with_roadmap(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay roadmap fields."""
    payload = dict(history)
    maturity_summary = payload.get("recurrence_maturity_summary")
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    program_summary = payload.get("recurrence_program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    portfolio_summary = payload.get("recurrence_portfolio_summary")
    if not isinstance(portfolio_summary, Mapping):
        portfolio_summary = {}
    forecast = payload.get("recurrence_forecast")
    forecast_summary = forecast.get("forecast_summary") if isinstance(forecast, Mapping) else None
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    lifecycle_summary = payload.get("recurrence_lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    remediation_summary = payload.get("remediation_effectiveness_summary")
    if not isinstance(remediation_summary, Mapping):
        remediation_summary = {}
    portfolio_trajectory = payload.get("portfolio_trajectory_summary")
    if not isinstance(portfolio_trajectory, Mapping):
        portfolio_trajectory = {}
    roadmap = build_recurrence_strategic_roadmap(
        recurrence_maturity_summary=maturity_summary,
        recurrence_maturity_gap_analysis=payload.get("recurrence_maturity_gap_analysis")
        if isinstance(payload.get("recurrence_maturity_gap_analysis"), list)
        else None,
        recurrence_program_effectiveness_summary=program_summary,
        recurrence_portfolio_summary=portfolio_summary,
        recurrence_forecast_summary=forecast_summary,
        recurrence_lifecycle_summary=lifecycle_summary,
        recurrence_remediation_effectiveness_summary=remediation_summary,
        portfolio_trajectory_summary=portfolio_trajectory,
        total_observations=int(payload.get("total_rows") or 0),
        total_keys=int(payload.get("unique_recurrence_count") or 0),
    )
    payload["recurrence_roadmap"] = roadmap
    payload["recurrence_roadmap_summary"] = roadmap["recurrence_roadmap_summary"]
    payload["recurrence_target_state"] = roadmap["recurrence_target_state"]
    return payload


RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET = RECURRENCE_MATURITY_TARGET_SCORE
RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET = RECURRENCE_MATURITY_TARGET_SCORE
RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET = RECURRENCE_MATURITY_TARGET_SCORE
RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET = RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE
RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET = RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE
RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET = RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE
RECURRENCE_COMPLETION_GRADUATION_DEFINITION = (
    "Program graduated when all six capability dimensions report completion_met=true, "
    "overall_maturity_score >= 80, operational_readiness_score >= 80, "
    "forecast_confidence >= 0.75, and effectiveness_confidence >= 0.75."
)
RECURRENCE_COMPLETION_SCORE_DEFINITION = (
    "Advisory 0-100 overall completion score: weighted average of dimension completion scores "
    "using recurrence maturity dimension weights. Each dimension completion_score is "
    "100 * met_requirements / total_requirements."
)
RECURRENCE_COMPLETION_DISTANCE_DEFINITION = (
    "Estimated completion distance is 100 - overall_completion_score; lower values indicate "
    "closer proximity to program graduation."
)
RECURRENCE_COMPLETION_REQUIREMENT_ROADMAP: dict[str, str] = {
    "recurrence_history_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "trend_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "forecasting_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "portfolio_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "governance_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "lifecycle_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "governance_health_target_met": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "watchlist_operational": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "ownership_accountability_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "retirement_tracking_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "forecast_confidence_target_met": RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    "forecast_effectiveness_measurable": RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    "trajectory_available": RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
    "forecast_validation_available": RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    "remediation_targeting_available": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "roi_analytics_available": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "recurrence_reduction_measurable": RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    "remediation_effectiveness_measurable": RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    "lifecycle_tracking_available": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "transition_tracking_available": RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    "closure_effectiveness_measurable": RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    "age_distribution_available": RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    "operational_readiness_target_met": RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
    "effectiveness_confidence_target_met": RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
    "governance_confidence_target_met": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "overall_maturity_target_met": RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
}


def _completion_dimension_result(
    *,
    requirements: Sequence[tuple[str, bool, Any, Any]],
) -> dict[str, Any]:
    unmet: list[str] = []
    met_count = 0
    requirement_rows: list[dict[str, Any]] = []
    for requirement_id, met, current_value, target_value in requirements:
        requirement_rows.append(
            {
                "requirement": requirement_id,
                "met": bool(met),
                "current_value": current_value,
                "target_value": target_value,
            }
        )
        if met:
            met_count += 1
        else:
            unmet.append(requirement_id)
    total = max(len(requirements), 1)
    completion_score = round(100.0 * met_count / float(total), 1)
    return {
        "completion_met": met_count == len(requirements) and len(requirements) > 0,
        "completion_score": completion_score,
        "unmet_requirements": unmet,
        "requirements": requirement_rows,
    }


def _completion_numeric_gap(current: float, target: float) -> float:
    return round(max(0.0, float(target) - float(current)), 2)


def _assess_observability_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    checks = [
        (
            "recurrence_history_present",
            bool(history.get("unique_recurrence_count") or history.get("summary")),
            bool(history.get("unique_recurrence_count") or history.get("summary")),
            True,
        ),
        (
            "trend_analytics_present",
            isinstance(history.get("recurrence_trends"), Mapping),
            isinstance(history.get("recurrence_trends"), Mapping),
            True,
        ),
        (
            "forecasting_present",
            isinstance(history.get("recurrence_forecast"), Mapping),
            isinstance(history.get("recurrence_forecast"), Mapping),
            True,
        ),
        (
            "portfolio_analytics_present",
            isinstance(history.get("recurrence_portfolio"), Mapping)
            or isinstance(history.get("recurrence_portfolio_summary"), Mapping),
            isinstance(history.get("recurrence_portfolio"), Mapping)
            or isinstance(history.get("recurrence_portfolio_summary"), Mapping),
            True,
        ),
        (
            "governance_analytics_present",
            isinstance(history.get("recurrence_governance"), Mapping)
            or isinstance(history.get("recurrence_governance_summary"), Mapping),
            isinstance(history.get("recurrence_governance"), Mapping)
            or isinstance(history.get("recurrence_governance_summary"), Mapping),
            True,
        ),
        (
            "lifecycle_analytics_present",
            isinstance(history.get("recurrence_lifecycle"), Mapping)
            or isinstance(history.get("recurrence_lifecycle_summary"), Mapping),
            isinstance(history.get("recurrence_lifecycle"), Mapping)
            or isinstance(history.get("recurrence_lifecycle_summary"), Mapping),
            True,
        ),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_governance_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_governance_summary: Mapping[str, Any] | None,
    maturity_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance_summary = (
        recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    )
    if not governance_summary and isinstance(history.get("recurrence_governance_summary"), Mapping):
        governance_summary = history["recurrence_governance_summary"]
    governance = history.get("recurrence_governance")
    if not isinstance(governance, Mapping):
        governance = {}
    governance_health = float(
        governance_summary.get("governance_health_score")
        or governance.get("governance_health_score")
        or (maturity_summary.get("governance_score") if isinstance(maturity_summary, Mapping) else None)
        or 0.0
    )
    watchlist = governance.get("watchlist") if isinstance(governance.get("watchlist"), list) else []
    watchlist_operational = bool(watchlist) or int(governance_summary.get("watchlist_size") or 0) > 0
    owners = governance.get("owners") if isinstance(governance.get("owners"), list) else []
    ownership_present = bool(owners)
    retirement_present = isinstance(governance.get("retirement_summary"), Mapping) or isinstance(
        history.get("recurrence_retirement_summary"), Mapping
    )
    checks = [
        (
            "governance_health_target_met",
            governance_health >= RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET,
            round(governance_health, 1),
            RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET,
        ),
        ("watchlist_operational", watchlist_operational, watchlist_operational, True),
        ("ownership_accountability_present", ownership_present, ownership_present, True),
        ("retirement_tracking_present", retirement_present, retirement_present, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_forecasting_completion(
    *,
    recurrence_forecast_summary: Mapping[str, Any] | None,
    forecast_effectiveness_summary: Mapping[str, Any] | None,
    portfolio_trajectory_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    forecast_effectiveness = (
        forecast_effectiveness_summary if isinstance(forecast_effectiveness_summary, Mapping) else {}
    )
    trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}
    forecast_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    forecast_measurable = forecast_effectiveness.get("forecast_accuracy") is not None or bool(
        forecast_effectiveness.get("effectiveness_definition")
    )
    trajectory_available = bool(trajectory.get("trajectory_available"))
    validation_available = bool(forecast_effectiveness.get("predicted_recurrences") is not None) or bool(
        forecast_summary.get("watch_keys") is not None
    )
    checks = [
        (
            "forecast_confidence_target_met",
            forecast_confidence >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
            round(forecast_confidence, 2),
            RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
        ),
        ("forecast_effectiveness_measurable", forecast_measurable, forecast_measurable, True),
        ("trajectory_available", trajectory_available, trajectory_available, True),
        ("forecast_validation_available", validation_available, validation_available, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_remediation_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
    remediation_effectiveness_summary: Mapping[str, Any] | None,
    recurrence_roi_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    remediation = (
        remediation_effectiveness_summary if isinstance(remediation_effectiveness_summary, Mapping) else {}
    )
    roi_summary = recurrence_roi_summary if isinstance(recurrence_roi_summary, Mapping) else {}
    if not roi_summary and isinstance(history.get("recurrence_roi_summary"), Mapping):
        roi_summary = history["recurrence_roi_summary"]
    remediation_targets = history.get("recurrence_remediation_targets")
    targeting_available = isinstance(remediation_targets, Mapping) and bool(
        remediation_targets.get("keys") or remediation_targets.get("remediation_summary")
    )
    roi_available = bool(roi_summary) or isinstance(history.get("recurrence_roi"), Mapping)
    reduction_measurable = remediation.get("recurrence_reduction_rate") is not None
    effectiveness_measurable = remediation.get("remediation_effectiveness") is not None or bool(
        remediation.get("effectiveness_definition")
    )
    checks = [
        ("remediation_targeting_available", targeting_available, targeting_available, True),
        ("roi_analytics_available", roi_available, roi_available, True),
        ("recurrence_reduction_measurable", reduction_measurable, reduction_measurable, True),
        ("remediation_effectiveness_measurable", effectiveness_measurable, effectiveness_measurable, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_lifecycle_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    lifecycle = history.get("recurrence_lifecycle")
    if not isinstance(lifecycle, Mapping):
        lifecycle = {}
    tracking_available = bool(lifecycle.get("keys")) or bool(lifecycle_summary)
    transition_available = isinstance(lifecycle.get("transition_summary"), Mapping) or isinstance(
        history.get("recurrence_transition_summary"), Mapping
    )
    closure_measurable = "closure_rate" in lifecycle_summary or isinstance(
        history.get("recurrence_closure_effectiveness"), Mapping
    )
    age_available = isinstance(lifecycle.get("age_distribution"), Mapping) or isinstance(
        history.get("recurrence_age_distribution"), Mapping
    )
    checks = [
        ("lifecycle_tracking_available", tracking_available, tracking_available, True),
        ("transition_tracking_available", transition_available, transition_available, True),
        ("closure_effectiveness_measurable", closure_measurable, closure_measurable, True),
        ("age_distribution_available", age_available, age_available, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_operational_readiness_completion(
    *,
    maturity_summary: Mapping[str, Any] | None,
    program_summary: Mapping[str, Any] | None,
    governance_summary: Mapping[str, Any] | None,
    portfolio_trajectory_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    program = program_summary if isinstance(program_summary, Mapping) else {}
    governance = governance_summary if isinstance(governance_summary, Mapping) else {}
    trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}
    operational_readiness = float(summary.get("operational_readiness_score") or 0.0)
    effectiveness_confidence = float(program.get("effectiveness_confidence") or 0.0)
    governance_confidence = float(governance.get("governance_confidence") or 0.0)
    trajectory_available = bool(trajectory.get("trajectory_available"))
    checks = [
        (
            "operational_readiness_target_met",
            operational_readiness >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET,
            round(operational_readiness, 1),
            RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET,
        ),
        (
            "effectiveness_confidence_target_met",
            effectiveness_confidence >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
            round(effectiveness_confidence, 2),
            RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
        ),
        (
            "governance_confidence_target_met",
            governance_confidence >= RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET,
            round(governance_confidence, 2),
            RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET,
        ),
        ("trajectory_available", trajectory_available, trajectory_available, True),
    ]
    return _completion_dimension_result(requirements=checks)


def calculate_recurrence_completion_score(
    *,
    observability_completion: Mapping[str, Any] | None = None,
    governance_completion: Mapping[str, Any] | None = None,
    forecasting_completion: Mapping[str, Any] | None = None,
    remediation_completion: Mapping[str, Any] | None = None,
    lifecycle_completion: Mapping[str, Any] | None = None,
    operational_readiness_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence program completion scores."""
    dimensions = {
        "observability": observability_completion if isinstance(observability_completion, Mapping) else {},
        "governance": governance_completion if isinstance(governance_completion, Mapping) else {},
        "forecasting": forecasting_completion if isinstance(forecasting_completion, Mapping) else {},
        "remediation": remediation_completion if isinstance(remediation_completion, Mapping) else {},
        "lifecycle": lifecycle_completion if isinstance(lifecycle_completion, Mapping) else {},
        "operational_readiness": operational_readiness_completion
        if isinstance(operational_readiness_completion, Mapping)
        else {},
    }
    dimension_scores = {
        name: float(row.get("completion_score") or 0.0) for name, row in dimensions.items()
    }
    overall_completion_score = round(
        sum(
            dimension_scores[name] * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        1,
    )
    completed_dimensions = [name for name, row in dimensions.items() if row.get("completion_met")]
    remaining_dimensions = [name for name, row in dimensions.items() if not row.get("completion_met")]
    return {
        "dimension_scores": dimension_scores,
        "overall_completion_score": overall_completion_score,
        "completed_dimensions": completed_dimensions,
        "remaining_dimensions": remaining_dimensions,
        "dimensions": dimensions,
    }


def _build_completion_gap_analysis(
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for dimension, row in dimensions.items():
        if not isinstance(row, Mapping):
            continue
        for requirement in row.get("requirements") or ():
            if not isinstance(requirement, Mapping) or requirement.get("met"):
                continue
            requirement_id = str(requirement.get("requirement") or "")
            current_value = requirement.get("current_value")
            target_value = requirement.get("target_value")
            if isinstance(current_value, (int, float)) and isinstance(target_value, (int, float)):
                gap = _completion_numeric_gap(float(current_value), float(target_value))
            elif current_value == target_value:
                gap = 0.0
            else:
                gap = 1.0
            gaps.append(
                {
                    "dimension": dimension,
                    "requirement": requirement_id,
                    "current_value": current_value,
                    "target_value": target_value,
                    "gap": gap,
                    "roadmap_dependency": RECURRENCE_COMPLETION_REQUIREMENT_ROADMAP.get(
                        requirement_id,
                        RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
                    ),
                }
            )
    gaps.sort(key=lambda row: (-float(row.get("gap") or 0.0), str(row.get("dimension") or "")))
    return gaps


def _program_graduation_met(
    *,
    dimensions: Mapping[str, Mapping[str, Any]],
    maturity_summary: Mapping[str, Any] | None,
    program_summary: Mapping[str, Any] | None,
    forecast_summary: Mapping[str, Any] | None,
) -> bool:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    program = program_summary if isinstance(program_summary, Mapping) else {}
    forecast = forecast_summary if isinstance(forecast_summary, Mapping) else {}
    all_dimensions_complete = all(
        isinstance(row, Mapping) and row.get("completion_met") for row in dimensions.values()
    )
    return bool(
        all_dimensions_complete
        and float(summary.get("overall_maturity_score") or 0.0)
        >= RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET
        and float(summary.get("operational_readiness_score") or 0.0)
        >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET
        and float(forecast.get("forecast_confidence") or 0.0) >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET
        and float(program.get("effectiveness_confidence") or 0.0)
        >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET
    )


def summarize_recurrence_completion(
    completion: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence program completion."""
    source = completion if isinstance(completion, Mapping) else {}
    summary = source.get("recurrence_completion_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    scores = source.get("completion_scores")
    if not isinstance(scores, Mapping):
        scores = calculate_recurrence_completion_score()
    remaining_requirements: list[str] = []
    for dimension, row in (scores.get("dimensions") or {}).items():
        if isinstance(row, Mapping):
            remaining_requirements.extend(list(row.get("unmet_requirements") or ()))
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "overall_completion_score": float(scores.get("overall_completion_score") or 0.0),
        "completion_criteria_met": bool(source.get("program_graduated")),
        "program_graduated": bool(source.get("program_graduated")),
        "completed_dimensions": list(scores.get("completed_dimensions") or ()),
        "remaining_dimensions": list(scores.get("remaining_dimensions") or ()),
        "remaining_requirements": remaining_requirements,
        "estimated_completion_distance": round(
            100.0 - float(scores.get("overall_completion_score") or 0.0),
            1,
        ),
        "graduation_definition": RECURRENCE_COMPLETION_GRADUATION_DEFINITION,
        "completion_score_definition": RECURRENCE_COMPLETION_SCORE_DEFINITION,
        "completion_distance_definition": RECURRENCE_COMPLETION_DISTANCE_DEFINITION,
    }


def build_recurrence_completion_assessment(
    *,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_target_state: Mapping[str, Any] | None = None,
    recurrence_roadmap_summary: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_governance_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    forecast_effectiveness_summary: Mapping[str, Any] | None = None,
    remediation_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_roi_summary: Mapping[str, Any] | None = None,
    portfolio_trajectory_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence program completion assessment."""
    maturity_summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    target_state = recurrence_target_state if isinstance(recurrence_target_state, Mapping) else {}
    roadmap_summary = recurrence_roadmap_summary if isinstance(recurrence_roadmap_summary, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance_summary = (
        recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    )
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    forecast_effectiveness = (
        forecast_effectiveness_summary if isinstance(forecast_effectiveness_summary, Mapping) else {}
    )
    remediation_summary = (
        remediation_effectiveness_summary if isinstance(remediation_effectiveness_summary, Mapping) else {}
    )
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    roi_summary = recurrence_roi_summary if isinstance(recurrence_roi_summary, Mapping) else {}
    portfolio_trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}

    observability_completion = _assess_observability_completion(recurrence_history=history)
    governance_completion = _assess_governance_completion(
        recurrence_history=history,
        recurrence_governance_summary=governance_summary,
        maturity_summary=maturity_summary,
    )
    forecasting_completion = _assess_forecasting_completion(
        recurrence_forecast_summary=forecast_summary,
        forecast_effectiveness_summary=forecast_effectiveness,
        portfolio_trajectory_summary=portfolio_trajectory,
    )
    remediation_completion = _assess_remediation_completion(
        recurrence_history=history,
        remediation_effectiveness_summary=remediation_summary,
        recurrence_roi_summary=roi_summary,
    )
    lifecycle_completion = _assess_lifecycle_completion(
        recurrence_history=history,
        recurrence_lifecycle_summary=lifecycle_summary,
    )
    operational_readiness_completion = _assess_operational_readiness_completion(
        maturity_summary=maturity_summary,
        program_summary=program_summary,
        governance_summary=governance_summary,
        portfolio_trajectory_summary=portfolio_trajectory,
    )
    completion_scores = calculate_recurrence_completion_score(
        observability_completion=observability_completion,
        governance_completion=governance_completion,
        forecasting_completion=forecasting_completion,
        remediation_completion=remediation_completion,
        lifecycle_completion=lifecycle_completion,
        operational_readiness_completion=operational_readiness_completion,
    )
    dimensions = completion_scores["dimensions"]
    completion_gap_analysis = _build_completion_gap_analysis(dimensions)
    program_graduated = _program_graduation_met(
        dimensions=dimensions,
        maturity_summary=maturity_summary,
        program_summary=program_summary,
        forecast_summary=forecast_summary,
    )
    completion_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "completion_scores": completion_scores,
        "observability_completion": observability_completion,
        "governance_completion": governance_completion,
        "forecasting_completion": forecasting_completion,
        "remediation_completion": remediation_completion,
        "lifecycle_completion": lifecycle_completion,
        "operational_readiness_completion": operational_readiness_completion,
        "completion_gap_analysis": completion_gap_analysis,
        "program_graduated": program_graduated,
        "graduation_definition": RECURRENCE_COMPLETION_GRADUATION_DEFINITION,
        "completion_score_definition": RECURRENCE_COMPLETION_SCORE_DEFINITION,
        "completion_distance_definition": RECURRENCE_COMPLETION_DISTANCE_DEFINITION,
        "target_state_reference": target_state,
        "roadmap_reference": roadmap_summary,
    }
    recurrence_completion_summary = summarize_recurrence_completion(completion_without_summary)
    return {
        **completion_without_summary,
        "recurrence_completion_summary": recurrence_completion_summary,
    }


def enrich_recurrence_history_with_completion(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay completion fields."""
    payload = dict(history)
    forecast = payload.get("recurrence_forecast")
    forecast_summary = forecast.get("forecast_summary") if isinstance(forecast, Mapping) else None
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    completion = build_recurrence_completion_assessment(
        recurrence_maturity_summary=payload.get("recurrence_maturity_summary")
        if isinstance(payload.get("recurrence_maturity_summary"), Mapping)
        else None,
        recurrence_program_effectiveness_summary=payload.get("recurrence_program_effectiveness_summary")
        if isinstance(payload.get("recurrence_program_effectiveness_summary"), Mapping)
        else None,
        recurrence_target_state=payload.get("recurrence_target_state")
        if isinstance(payload.get("recurrence_target_state"), Mapping)
        else None,
        recurrence_roadmap_summary=payload.get("recurrence_roadmap_summary")
        if isinstance(payload.get("recurrence_roadmap_summary"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_governance_summary=payload.get("recurrence_governance_summary")
        if isinstance(payload.get("recurrence_governance_summary"), Mapping)
        else None,
        recurrence_forecast_summary=forecast_summary,
        forecast_effectiveness_summary=payload.get("forecast_effectiveness_summary")
        if isinstance(payload.get("forecast_effectiveness_summary"), Mapping)
        else None,
        remediation_effectiveness_summary=payload.get("remediation_effectiveness_summary")
        if isinstance(payload.get("remediation_effectiveness_summary"), Mapping)
        else None,
        recurrence_lifecycle_summary=payload.get("recurrence_lifecycle_summary")
        if isinstance(payload.get("recurrence_lifecycle_summary"), Mapping)
        else None,
        recurrence_roi_summary=payload.get("recurrence_roi_summary")
        if isinstance(payload.get("recurrence_roi_summary"), Mapping)
        else None,
        portfolio_trajectory_summary=payload.get("portfolio_trajectory_summary")
        if isinstance(payload.get("portfolio_trajectory_summary"), Mapping)
        else None,
    )
    payload["recurrence_completion"] = completion
    payload["recurrence_completion_summary"] = completion["recurrence_completion_summary"]
    payload["recurrence_completion_gap_analysis"] = completion["completion_gap_analysis"]
    return payload


RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE = "historical_persistence"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS = "trend_analytics"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING = "forecasting"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS = "portfolio_analytics"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING = "remediation_targeting"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS = "roi_analytics"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE = "governance"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT = "lifecycle_management"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT = "effectiveness_measurement"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT = "maturity_assessment"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP = "strategic_roadmap"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING = "completion_tracking"
RECURRENCE_GRADUATION_AUDIT_CAPABILITIES: tuple[str, ...] = (
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING,
)
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LABELS: dict[str, str] = {
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE: "Historical Persistence",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS: "Trend Analytics",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING: "Forecasting",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS: "Portfolio Analytics",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING: "Remediation Targeting",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS: "ROI Analytics",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE: "Governance",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT: "Lifecycle Management",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT: "Effectiveness Measurement",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT: "Maturity Assessment",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP: "Strategic Roadmap",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING: "Completion Tracking",
}
RECURRENCE_GRADUATION_AUDIT_OPERATIONAL_CONFIDENCE_THRESHOLD = 0.15
RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION = (
    "Advisory 0-100 graduation readiness score: 45% overall_completion_score + "
    "30% operational_capability_ratio*100 + 15% validated_capability_ratio*100 + "
    "10% average_capability_confidence*100 - 8 per critical blind spot - 3 per critical "
    "redundancy. Interpretation: 90-100 ready; 70-89 minor gaps; 50-69 moderate gaps; "
    "<50 major gaps."
)
RECURRENCE_GRADUATION_AUDIT_DOC_PATH = Path("docs/audits/BQ16_recurrence_graduation_audit.md")


def _audit_capability_row(
    *,
    capability_id: str,
    implemented: bool,
    validated: bool,
    operational: bool,
    confidence: float,
    remaining_concerns: Sequence[str],
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "capability_label": RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LABELS.get(capability_id, capability_id),
        "implemented": bool(implemented),
        "validated": bool(validated),
        "operational": bool(operational),
        "confidence": round(max(0.0, min(1.0, float(confidence or 0.0))), 2),
        "remaining_concerns": list(remaining_concerns),
    }


def validate_recurrence_program_capabilities(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_roadmap: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Validate protected replay recurrence program capability coverage."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    if not trends and isinstance(history.get("recurrence_trends"), Mapping):
        trends = history["recurrence_trends"]
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    if not forecast and isinstance(history.get("recurrence_forecast"), Mapping):
        forecast = history["recurrence_forecast"]
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    if not portfolio and isinstance(history.get("recurrence_portfolio"), Mapping):
        portfolio = history["recurrence_portfolio"]
    remediation = recurrence_remediation if isinstance(recurrence_remediation, Mapping) else {}
    if not remediation and isinstance(history.get("recurrence_remediation_targets"), Mapping):
        remediation = history["recurrence_remediation_targets"]
    roi = recurrence_roi if isinstance(recurrence_roi, Mapping) else {}
    if not roi and isinstance(history.get("recurrence_roi"), Mapping):
        roi = history["recurrence_roi"]
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    if not governance and isinstance(history.get("recurrence_governance"), Mapping):
        governance = history["recurrence_governance"]
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    roadmap = recurrence_roadmap if isinstance(recurrence_roadmap, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}

    observations = int(history.get("total_rows") or portfolio.get("total_observations") or 0)
    keys = int(history.get("unique_recurrence_count") or portfolio.get("total_keys") or 0)
    volume_factor = _maturity_volume_factor(total_observations=observations, total_keys=keys)
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    forecast_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    effectiveness_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)

    def _operational(validated_flag: bool, confidence: float) -> bool:
        return validated_flag and confidence >= RECURRENCE_GRADUATION_AUDIT_OPERATIONAL_CONFIDENCE_THRESHOLD

    rows: list[dict[str, Any]] = []

    history_impl = bool(history.get("unique_recurrence_count") is not None or history.get("summary"))
    history_valid = int(history.get("unique_recurrence_count") or 0) > 0 and observations > 0
    history_conf = volume_factor
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE,
            implemented=history_impl,
            validated=history_valid,
            operational=_operational(history_valid, history_conf),
            confidence=history_conf,
            remaining_concerns=(
                ["Protected replay observation volume remains below confidence threshold."]
                if volume_factor < 0.5
                else []
            ),
        )
    )

    trends_impl = bool(trends)
    trends_valid = trends.get("total_keys") is not None and int(trends.get("total_keys") or 0) >= 0
    trends_conf = min(1.0, volume_factor + 0.1) if trends_valid else 0.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS,
            implemented=trends_impl,
            validated=trends_valid and observations > 0,
            operational=_operational(trends_valid and observations > 0, trends_conf),
            confidence=trends_conf,
            remaining_concerns=(
                ["Trend classifications rely on sparse protected history."]
                if observations < RECURRENCE_MATURITY_MIN_OBSERVATIONS
                else []
            ),
        )
    )

    forecast_impl = bool(forecast.get("key_forecasts") or forecast_summary)
    forecast_valid = bool(forecast.get("key_forecasts")) and keys > 0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING,
            implemented=forecast_impl,
            validated=forecast_valid,
            operational=_operational(forecast_valid, forecast_confidence),
            confidence=forecast_confidence,
            remaining_concerns=(
                ["Forecast confidence remains below operational threshold."]
                if forecast_confidence < RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET
                else []
            ),
        )
    )

    portfolio_impl = bool(portfolio.get("portfolio_summary") or history.get("recurrence_portfolio_summary"))
    portfolio_valid = portfolio_impl and observations > 0
    portfolio_conf = min(1.0, volume_factor + forecast_confidence * 0.3)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS,
            implemented=portfolio_impl,
            validated=portfolio_valid,
            operational=_operational(portfolio_valid, portfolio_conf),
            confidence=portfolio_conf,
            remaining_concerns=[],
        )
    )

    remediation_impl = bool(remediation.get("keys") or remediation.get("remediation_summary"))
    remediation_valid = remediation_impl and keys > 0
    remediation_conf = min(1.0, volume_factor * 0.8 + 0.1)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING,
            implemented=remediation_impl,
            validated=remediation_valid,
            operational=_operational(remediation_valid, remediation_conf),
            confidence=remediation_conf,
            remaining_concerns=(
                ["Remediation confidence remains low at current observation volume."]
                if remediation_conf < RECURRENCE_GRADUATION_AUDIT_OPERATIONAL_CONFIDENCE_THRESHOLD
                else []
            ),
        )
    )

    roi_impl = bool(roi.get("roi_summary") or history.get("recurrence_roi_summary"))
    roi_valid = roi_impl and keys > 0
    roi_conf = min(1.0, volume_factor * 0.7 + 0.15)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS,
            implemented=roi_impl,
            validated=roi_valid,
            operational=_operational(roi_valid, roi_conf),
            confidence=roi_conf,
            remaining_concerns=[],
        )
    )

    governance_impl = bool(governance.get("watchlist") or governance.get("governance_summary"))
    governance_valid = governance_impl and bool(governance.get("watchlist"))
    governance_conf = float(
        (governance.get("governance_summary") or {}).get("governance_confidence")
        or governance.get("governance_confidence")
        or 0.0
    )
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE,
            implemented=governance_impl,
            validated=governance_valid,
            operational=_operational(governance_valid, governance_conf),
            confidence=governance_conf,
            remaining_concerns=(
                ["Governance health remains below completion target."]
                if float((governance.get("governance_summary") or {}).get("governance_health_score") or 0.0)
                < RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET
                else []
            ),
        )
    )

    lifecycle_impl = bool(lifecycle.get("keys") or lifecycle.get("lifecycle_summary"))
    lifecycle_valid = lifecycle_impl and keys > 0
    lifecycle_conf = min(1.0, volume_factor + 0.2)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT,
            implemented=lifecycle_impl,
            validated=lifecycle_valid,
            operational=_operational(lifecycle_valid, lifecycle_conf),
            confidence=lifecycle_conf,
            remaining_concerns=[],
        )
    )

    effectiveness_impl = bool(effectiveness.get("program_effectiveness_summary"))
    effectiveness_valid = effectiveness_impl and keys > 0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT,
            implemented=effectiveness_impl,
            validated=effectiveness_valid,
            operational=_operational(effectiveness_valid, effectiveness_confidence),
            confidence=effectiveness_confidence,
            remaining_concerns=(
                ["Effectiveness confidence remains below graduation threshold."]
                if effectiveness_confidence < RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET
                else []
            ),
        )
    )

    maturity_impl = bool(maturity.get("recurrence_maturity_summary"))
    maturity_valid = maturity_impl and float(
        (maturity.get("recurrence_maturity_summary") or {}).get("overall_maturity_score") or 0.0
    ) > 0.0
    maturity_conf = float(
        (maturity.get("recurrence_maturity_summary") or {}).get("overall_maturity_score") or 0.0
    ) / 100.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT,
            implemented=maturity_impl,
            validated=maturity_valid,
            operational=_operational(maturity_valid, maturity_conf),
            confidence=maturity_conf,
            remaining_concerns=[],
        )
    )

    roadmap_impl = bool(roadmap.get("recurrence_roadmap_summary") or roadmap.get("initiatives"))
    roadmap_valid = roadmap_impl and bool(roadmap.get("roadmap_sequence"))
    roadmap_conf = 0.8 if roadmap_valid else 0.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP,
            implemented=roadmap_impl,
            validated=roadmap_valid,
            operational=roadmap_valid,
            confidence=roadmap_conf,
            remaining_concerns=[],
        )
    )

    completion_impl = bool(completion.get("recurrence_completion_summary"))
    completion_valid = completion_impl and float(
        (completion.get("recurrence_completion_summary") or {}).get("overall_completion_score") or 0.0
    ) >= 0.0
    completion_conf = float(
        (completion.get("recurrence_completion_summary") or {}).get("overall_completion_score") or 0.0
    ) / 100.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING,
            implemented=completion_impl,
            validated=completion_valid,
            operational=_operational(completion_valid, completion_conf),
            confidence=completion_conf,
            remaining_concerns=(
                ["Program graduation criteria not yet met."]
                if not (completion.get("recurrence_completion_summary") or {}).get("program_graduated")
                else []
            ),
        )
    )
    return rows


def _audit_completion_criteria_validation(
    *,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_maturity: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    maturity_summary = {}
    if isinstance(recurrence_maturity, Mapping):
        maturity_summary = recurrence_maturity.get("recurrence_maturity_summary") or {}
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    program_summary = {}
    if isinstance(recurrence_program_effectiveness, Mapping):
        program_summary = recurrence_program_effectiveness.get("program_effectiveness_summary") or {}
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}

    rows: list[dict[str, Any]] = []
    dimension_completion = {
        "observability": completion.get("observability_completion"),
        "governance": completion.get("governance_completion"),
        "forecasting": completion.get("forecasting_completion"),
        "remediation": completion.get("remediation_completion"),
        "lifecycle": completion.get("lifecycle_completion"),
        "operational_readiness": completion.get("operational_readiness_completion"),
    }
    for dimension, payload in dimension_completion.items():
        if not isinstance(payload, Mapping):
            continue
        for requirement in payload.get("requirements") or ():
            if not isinstance(requirement, Mapping):
                continue
            rows.append(
                {
                    "requirement": str(requirement.get("requirement") or ""),
                    "dimension": dimension,
                    "current_value": requirement.get("current_value"),
                    "target_value": requirement.get("target_value"),
                    "status": "met" if requirement.get("met") else "unmet",
                    "confidence": 0.9 if requirement.get("met") else 0.4,
                    "threshold_appropriate": True,
                }
            )
    rows.extend(
        [
            {
                "requirement": "overall_maturity_target_met",
                "dimension": "program",
                "current_value": float(maturity_summary.get("overall_maturity_score") or 0.0),
                "target_value": RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET,
                "status": "met"
                if float(maturity_summary.get("overall_maturity_score") or 0.0)
                >= RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET
                else "unmet",
                "confidence": 0.85,
                "threshold_appropriate": True,
            },
            {
                "requirement": "forecast_confidence_graduation",
                "dimension": "program",
                "current_value": float(forecast_summary.get("forecast_confidence") or 0.0),
                "target_value": RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
                "status": "met"
                if float(forecast_summary.get("forecast_confidence") or 0.0)
                >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET
                else "unmet",
                "confidence": float(forecast_summary.get("forecast_confidence") or 0.0),
                "threshold_appropriate": True,
            },
            {
                "requirement": "effectiveness_confidence_graduation",
                "dimension": "program",
                "current_value": float(program_summary.get("effectiveness_confidence") or 0.0),
                "target_value": RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
                "status": "met"
                if float(program_summary.get("effectiveness_confidence") or 0.0)
                >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET
                else "unmet",
                "confidence": float(program_summary.get("effectiveness_confidence") or 0.0),
                "threshold_appropriate": True,
            },
        ]
    )
    return rows


def _audit_roadmap_assumption_validation(
    *,
    recurrence_roadmap: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    roadmap = recurrence_roadmap if isinstance(recurrence_roadmap, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    observations = int(history.get("total_rows") or 0)
    keys = int(history.get("unique_recurrence_count") or 0)
    volume_factor = _maturity_volume_factor(total_observations=observations, total_keys=keys)
    trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(trajectory, Mapping):
        trajectory = {}
    trajectory_available = bool(trajectory.get("trajectory_available"))

    assumptions: list[tuple[str, str, str]] = []
    if volume_factor < 0.5:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
                "still_valid",
                "Low protected replay volume confirms data expansion remains highest ROI.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
                "partially_valid",
                "Volume threshold partially met; continued expansion still improves confidence.",
            )
        )
    if not trajectory_available:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
                "still_valid",
                "Trajectory unavailable; baseline-only posture validates trajectory-first sequencing.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
                "partially_valid",
                "Trajectory exists but downstream forecasting and readiness remain incomplete.",
            )
        )
    forecast_summary = (history.get("recurrence_forecast") or {}).get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    if float(forecast_summary.get("forecast_confidence") or 0.0) < RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
                "still_valid",
                "Forecast confidence below target; validation initiative remains appropriate.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
                "partially_valid",
                "Forecast confidence met structurally but effectiveness evidence remains thin.",
            )
        )
    lifecycle_summary = history.get("recurrence_lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    if float(lifecycle_summary.get("closure_rate") or 0.0) <= 0.0:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
                "still_valid",
                "No closure outcomes observed; lifecycle closure tracking remains necessary.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
                "partially_valid",
                "Closure signal exists but longitudinal closure effectiveness remains limited.",
            )
        )
    remediation_summary = effectiveness.get("remediation_effectiveness_summary")
    if not isinstance(remediation_summary, Mapping):
        remediation_summary = {}
    if float(remediation_summary.get("recurrence_reduction_rate") or 0.0) <= 0.0:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
                "still_valid",
                "Zero recurrence reduction rate; remediation feedback loop not yet evidenced.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
                "partially_valid",
                "Reduction signal present but sample size may be insufficient.",
            )
        )
    maturity_summary = (history.get("recurrence_maturity_summary") or {}) if isinstance(history, Mapping) else {}
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    if float(maturity_summary.get("operational_readiness_score") or 0.0) < RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
                "still_valid",
                "Operational readiness below target; final operationalization stage remains required.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
                "partially_valid",
                "Operational readiness improved but graduation thresholds not fully met.",
            )
        )

    return [
        {
            "initiative_id": initiative_id,
            "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative_id, initiative_id),
            "validation_status": status,
            "rationale": rationale,
        }
        for initiative_id, status, rationale in assumptions
    ]


def _audit_effectiveness_assumption_validation(
    *,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    forecast = effectiveness.get("forecast_effectiveness_summary")
    if not isinstance(forecast, Mapping):
        forecast = {}
    governance = effectiveness.get("governance_effectiveness_summary")
    if not isinstance(governance, Mapping):
        governance = {}
    remediation = effectiveness.get("remediation_effectiveness_summary")
    if not isinstance(remediation, Mapping):
        remediation = {}
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}

    rows: list[dict[str, Any]] = []
    forecast_accuracy = float(forecast.get("forecast_accuracy") or metrics.get("forecast_accuracy") or 0.0)
    forecast_confidence = float(forecast.get("forecast_confidence") or metrics.get("forecast_confidence") or 0.0)
    if forecast_accuracy >= 0.99 and forecast_confidence < 0.25:
        evidence = "potentially_misleading"
        rationale = "Perfect accuracy with very low confidence suggests insufficient validation volume."
    elif forecast_confidence >= 0.25:
        evidence = "supported_by_evidence"
        rationale = "Forecast effectiveness metrics available with non-trivial confidence."
    else:
        evidence = "insufficient_evidence"
        rationale = "Forecast effectiveness measurable but confidence remains low."
    rows.append(
        {
            "metric": "forecast_accuracy",
            "current_value": forecast_accuracy,
            "evidence_status": evidence,
            "rationale": rationale,
        }
    )

    governance_effectiveness = float(
        governance.get("governance_effectiveness") or metrics.get("governance_effectiveness") or 0.0
    )
    rows.append(
        {
            "metric": "governance_effectiveness",
            "current_value": governance_effectiveness,
            "evidence_status": "insufficient_evidence"
            if governance_effectiveness <= 0.0
            else "supported_by_evidence",
            "rationale": "Zero conversion rates indicate governance funnel not yet exercised by history volume.",
        }
    )

    remediation_effectiveness = float(
        remediation.get("remediation_effectiveness") or metrics.get("remediation_effectiveness") or 0.0
    )
    rows.append(
        {
            "metric": "remediation_effectiveness",
            "current_value": remediation_effectiveness,
            "evidence_status": "insufficient_evidence"
            if remediation_effectiveness <= 0.0
            else "supported_by_evidence",
            "rationale": "No resolved remediation outcomes observed in protected replay history.",
        }
    )

    closure_rate = float(metrics.get("closure_rate") or 0.0)
    rows.append(
        {
            "metric": "lifecycle_closure_effectiveness",
            "current_value": closure_rate,
            "evidence_status": "insufficient_evidence"
            if closure_rate <= 0.0
            else "supported_by_evidence",
            "rationale": "Lifecycle closure rate requires retired or dormant keys to validate effectiveness.",
        }
    )
    return rows


def _audit_blind_spot_analysis(
    *,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    observations = int(history.get("total_rows") or 0)
    keys = int(history.get("unique_recurrence_count") or 0)
    volume_factor = _maturity_volume_factor(total_observations=observations, total_keys=keys)
    trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(trajectory, Mapping):
        trajectory = {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}

    blind_spots: list[dict[str, Any]] = []
    if volume_factor < 0.5:
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_data_quality",
                "severity": "critical",
                "description": "Protected replay observation and key volume remain below maturity confidence thresholds.",
                "recommendation": "Continue data volume expansion before trusting downstream scores.",
            }
        )
    if not bool(trajectory.get("trajectory_available")):
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_trajectory_history",
                "severity": "critical",
                "description": "No longitudinal trajectory baseline exists for portfolio and readiness comparisons.",
                "recommendation": "Establish trajectory snapshots after sufficient protected replay history.",
            }
        )
    blind_spots.append(
        {
            "blind_spot_id": "recurrence_confidence_decay",
            "severity": "medium",
            "description": "Confidence scores do not decay with stale observations or aging keys.",
            "recommendation": "Consider temporal decay modeling in a future cycle if history spans long idle periods.",
        }
    )
    if not history.get("persistence_population"):
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_artifact_integrity",
                "severity": "medium",
                "description": "Artifact provenance is not continuously re-audited during graduation assessment.",
                "recommendation": "Run periodic provenance audits on protected recurrence event logs.",
            }
        )
    blind_spots.append(
        {
            "blind_spot_id": "recurrence_auditability",
            "severity": "low",
            "description": "No immutable audit chain links recurrence analytics revisions over time.",
            "recommendation": "Retain versioned history artifacts for audit replay if formal compliance is required.",
        }
    )
    if float(forecast_summary.get("forecast_confidence") or 0.0) < 0.25 and float(
        metrics.get("forecast_accuracy") or 0.0
    ) >= 0.99:
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_model_calibration",
                "severity": "high",
                "description": "High forecast accuracy coexists with low forecast confidence, risking over-interpretation.",
                "recommendation": "Treat forecast accuracy as advisory until confidence crosses graduation threshold.",
            }
        )
    blind_spots.append(
        {
            "blind_spot_id": "recurrence_ownership_drift",
            "severity": "medium",
            "description": "Recurrence ownership drift across runs is not tracked as a dedicated longitudinal signal.",
            "recommendation": "Monitor owner_drift_bucket transitions separately from recurrence key lifecycle.",
        }
    )
    return blind_spots


def _audit_redundancy_analysis(
    *,
    recurrence_maturity: Mapping[str, Any] | None,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_portfolio: Mapping[str, Any] | None,
    recurrence_governance: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}

    redundancies: list[dict[str, Any]] = []
    maturity_summary = maturity.get("recurrence_maturity_summary")
    completion_summary = completion.get("recurrence_completion_summary")
    if isinstance(maturity_summary, Mapping) and isinstance(completion_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "maturity_vs_completion_dimensions",
                "severity": "medium",
                "overlapping_signals": ["observability", "governance", "forecasting", "remediation", "lifecycle"],
                "consolidation_recommendation": (
                    "Use maturity scores for capability posture and completion scores for graduation gates; "
                    "avoid treating both as independent KPIs in operator dashboards."
                ),
            }
        )
    program_summary = effectiveness.get("program_effectiveness_summary")
    if isinstance(program_summary, Mapping) and isinstance(maturity_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "program_effectiveness_vs_overall_maturity",
                "severity": "medium",
                "overlapping_signals": ["program_effectiveness_score", "overall_maturity_score"],
                "consolidation_recommendation": (
                    "Program effectiveness measures outcomes; maturity measures capability. "
                    "Report both but do not average them into a single headline metric."
                ),
            }
        )
    governance_summary = governance.get("governance_summary")
    governance_effectiveness = effectiveness.get("governance_effectiveness_summary")
    if isinstance(governance_summary, Mapping) and isinstance(governance_effectiveness, Mapping):
        redundancies.append(
            {
                "redundancy_id": "governance_health_vs_governance_effectiveness",
                "severity": "high",
                "overlapping_signals": ["governance_health_score", "governance_effectiveness"],
                "consolidation_recommendation": (
                    "Health score reflects posture; effectiveness reflects funnel conversion. "
                    "Keep both, but label clearly to prevent duplicate escalation triggers."
                ),
            }
        )
    forecast_summary = forecast.get("forecast_summary")
    portfolio_summary = portfolio.get("portfolio_summary")
    if isinstance(forecast_summary, Mapping) and isinstance(portfolio_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "forecast_risk_vs_portfolio_risk",
                "severity": "medium",
                "overlapping_signals": ["forecast_risk_score", "portfolio_risk_score"],
                "consolidation_recommendation": (
                    "Portfolio risk already blends forecast risk; prefer portfolio_risk_score for prioritization "
                    "summaries unless forecast-specific drill-down is required."
                ),
            }
        )
    if isinstance(program_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "multiple_confidence_metrics",
                "severity": "low",
                "overlapping_signals": [
                    "forecast_confidence",
                    "governance_confidence",
                    "effectiveness_confidence",
                    "remediation_confidence",
                ],
                "consolidation_recommendation": (
                    "Expose a single operator-facing readiness confidence only when all component "
                    "confidences exceed graduation thresholds."
                ),
            }
        )
    return redundancies


def calculate_recurrence_graduation_readiness_score(
    *,
    capability_coverage: Sequence[Mapping[str, Any]] | None,
    blind_spots: Sequence[Mapping[str, Any]] | None,
    redundancies: Sequence[Mapping[str, Any]] | None,
    overall_completion_score: float,
) -> dict[str, Any]:
    """Calculate protected replay recurrence graduation readiness score."""
    capabilities = [row for row in (capability_coverage or ()) if isinstance(row, Mapping)]
    total = max(len(capabilities), 1)
    operational_count = sum(1 for row in capabilities if row.get("operational"))
    validated_count = sum(1 for row in capabilities if row.get("validated"))
    avg_confidence = (
        sum(float(row.get("confidence") or 0.0) for row in capabilities) / float(total) if capabilities else 0.0
    )
    critical_blind_spots = sum(
        1 for row in (blind_spots or ()) if isinstance(row, Mapping) and row.get("severity") == "critical"
    )
    critical_redundancies = sum(
        1 for row in (redundancies or ()) if isinstance(row, Mapping) and row.get("severity") in {"high", "critical"}
    )
    raw_score = (
        0.45 * float(overall_completion_score or 0.0)
        + 0.30 * (operational_count / float(total) * 100.0)
        + 0.15 * (validated_count / float(total) * 100.0)
        + 0.10 * (avg_confidence * 100.0)
        - critical_blind_spots * 8.0
        - critical_redundancies * 3.0
    )
    graduation_readiness_score = _clamp_maturity_score(raw_score)
    if graduation_readiness_score >= 90.0:
        readiness_level = "ready_for_graduation"
        readiness_label = "Ready for graduation"
    elif graduation_readiness_score >= 70.0:
        readiness_level = "minor_gaps_remain"
        readiness_label = "Minor gaps remain"
    elif graduation_readiness_score >= 50.0:
        readiness_level = "moderate_gaps_remain"
        readiness_label = "Moderate gaps remain"
    else:
        readiness_level = "major_gaps_remain"
        readiness_label = "Major capability gaps remain"
    return {
        "graduation_readiness_score": graduation_readiness_score,
        "readiness_level": readiness_level,
        "readiness_label": readiness_label,
        "operational_capability_ratio": round(operational_count / float(total), 2),
        "validated_capability_ratio": round(validated_count / float(total), 2),
        "average_capability_confidence": round(avg_confidence, 2),
        "critical_blind_spots": critical_blind_spots,
        "critical_redundancies": critical_redundancies,
        "readiness_definition": RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION,
    }


def summarize_recurrence_graduation_audit(
    audit: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence graduation audit."""
    source = audit if isinstance(audit, Mapping) else {}
    summary = source.get("recurrence_graduation_audit_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    capabilities = [row for row in (source.get("capability_coverage") or ()) if isinstance(row, Mapping)]
    blind_spots = [row for row in (source.get("blind_spots") or ()) if isinstance(row, Mapping)]
    redundancies = [row for row in (source.get("redundancies") or ()) if isinstance(row, Mapping)]
    readiness = source.get("graduation_readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    completion_summary = source.get("completion_reference")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "capabilities_complete": sum(1 for row in capabilities if row.get("implemented") and row.get("operational")),
        "validated_capabilities": sum(1 for row in capabilities if row.get("validated")),
        "critical_blind_spots": int(readiness.get("critical_blind_spots") or 0),
        "critical_redundancies": int(readiness.get("critical_redundancies") or 0),
        "graduation_readiness_score": float(readiness.get("graduation_readiness_score") or 0.0),
        "readiness_level": readiness.get("readiness_level") or "major_gaps_remain",
        "readiness_label": readiness.get("readiness_label") or "Major capability gaps remain",
        "program_graduated": bool(completion_summary.get("program_graduated")),
        "recommended_next_action": source.get("recommended_next_action")
        or "Expand protected replay observation volume before graduation.",
        "readiness_definition": RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION,
    }


def build_recurrence_graduation_audit(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_roadmap: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence graduation audit analytics."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    capability_coverage = validate_recurrence_program_capabilities(
        recurrence_history=history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_roadmap=recurrence_roadmap,
        recurrence_completion=recurrence_completion,
    )
    completion_criteria_validation = _audit_completion_criteria_validation(
        recurrence_completion=recurrence_completion,
        recurrence_maturity=recurrence_maturity,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_forecast=recurrence_forecast if isinstance(recurrence_forecast, Mapping) else history.get("recurrence_forecast"),
    )
    roadmap_validation = _audit_roadmap_assumption_validation(
        recurrence_roadmap=recurrence_roadmap,
        recurrence_history=history,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    effectiveness_validation = _audit_effectiveness_assumption_validation(
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    blind_spots = _audit_blind_spot_analysis(
        recurrence_history=history,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_forecast=recurrence_forecast if isinstance(recurrence_forecast, Mapping) else history.get("recurrence_forecast"),
    )
    redundancies = _audit_redundancy_analysis(
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_forecast=recurrence_forecast if isinstance(recurrence_forecast, Mapping) else history.get("recurrence_forecast"),
        recurrence_portfolio=recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else history.get("recurrence_portfolio"),
        recurrence_governance=recurrence_governance if isinstance(recurrence_governance, Mapping) else history.get("recurrence_governance"),
    )
    completion_summary = {}
    if isinstance(recurrence_completion, Mapping):
        completion_summary = recurrence_completion.get("recurrence_completion_summary") or {}
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}
    overall_completion_score = float(completion_summary.get("overall_completion_score") or 0.0)
    graduation_readiness = calculate_recurrence_graduation_readiness_score(
        capability_coverage=capability_coverage,
        blind_spots=blind_spots,
        redundancies=redundancies,
        overall_completion_score=overall_completion_score,
    )
    roadmap_summary = {}
    if isinstance(recurrence_roadmap, Mapping):
        roadmap_summary = recurrence_roadmap.get("recurrence_roadmap_summary") or {}
    if not isinstance(roadmap_summary, Mapping):
        roadmap_summary = {}
    recommended_next_action = str(
        roadmap_summary.get("roadmap_priority_guidance")
        or "Expand protected replay observation volume and establish trajectory baseline before graduation."
    )
    audit_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "capability_coverage": capability_coverage,
        "completion_criteria_validation": completion_criteria_validation,
        "roadmap_validation": roadmap_validation,
        "effectiveness_validation": effectiveness_validation,
        "blind_spots": blind_spots,
        "redundancies": redundancies,
        "graduation_readiness": graduation_readiness,
        "completion_reference": completion_summary,
        "recommended_next_action": recommended_next_action,
        "readiness_definition": RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION,
    }
    recurrence_graduation_audit_summary = summarize_recurrence_graduation_audit(audit_without_summary)
    return {
        **audit_without_summary,
        "recurrence_graduation_audit_summary": recurrence_graduation_audit_summary,
    }


def render_recurrence_graduation_audit_report_markdown(
    audit: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ16 recurrence graduation audit report."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = payload.get("recurrence_graduation_audit_summary")
    if not isinstance(summary, Mapping):
        summary = summarize_recurrence_graduation_audit(payload)
    readiness = payload.get("graduation_readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# BQ16 Recurrence Graduation Audit",
        "",
        f"**Date:** {generated_at_s}",
        f"**Protected replay only:** true",
        "",
        "## Graduation Readiness",
        "",
        f"- Graduation readiness score: `{float(summary.get('graduation_readiness_score') or 0.0):.1f}`",
        f"- Readiness level: `{summary.get('readiness_label') or 'unknown'}`",
        f"- Program graduated: `{str(bool(summary.get('program_graduated'))).lower()}`",
        f"- Recommended next action: {summary.get('recommended_next_action') or 'none recorded'}",
        "",
        "# Capability Coverage",
        "",
        "| Capability | Implemented | Validated | Operational | Confidence |",
        "|---|---|---|---|---:|",
    ]
    for row in payload.get("capability_coverage") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| {row.get('capability_label')} | `{str(bool(row.get('implemented'))).lower()}` | "
            f"`{str(bool(row.get('validated'))).lower()}` | `{str(bool(row.get('operational'))).lower()}` | "
            f"`{float(row.get('confidence') or 0.0):.2f}` |"
        )
    lines.extend(["", "# Completion Criteria Validation", ""])
    for row in payload.get("completion_criteria_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('requirement')}` ({row.get('dimension')}): "
            f"current `{row.get('current_value')}`, target `{row.get('target_value')}`, "
            f"status `{row.get('status')}`"
        )
    lines.extend(["", "# Roadmap Validation", ""])
    for row in payload.get("roadmap_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- {row.get('initiative_label')}: `{row.get('validation_status')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Effectiveness Validation", ""])
    for row in payload.get("effectiveness_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- {row.get('metric')}: `{row.get('evidence_status')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Blind Spots", ""])
    for row in payload.get("blind_spots") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- **{row.get('blind_spot_id')}** ({row.get('severity')}): {row.get('description')}"
        )
    lines.extend(["", "# Redundancies", ""])
    for row in payload.get("redundancies") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- **{row.get('redundancy_id')}** ({row.get('severity')}): {row.get('consolidation_recommendation')}"
        )
    lines.extend(
        [
            "",
            "# Recommended Actions",
            "",
            f"1. {summary.get('recommended_next_action') or 'Continue protected replay observation collection.'}",
            "2. Establish trajectory baseline before treating forecasting and operational readiness as graduation-ready.",
            "3. Keep maturity, effectiveness, and completion scores distinct in operator reporting to avoid redundant escalation.",
            "",
        ]
    )
    return "\n".join(lines)


def enrich_recurrence_history_with_graduation_audit(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay graduation audit fields."""
    payload = dict(history)
    audit = build_recurrence_graduation_audit(
        recurrence_history=payload,
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_portfolio=payload.get("recurrence_portfolio")
        if isinstance(payload.get("recurrence_portfolio"), Mapping)
        else None,
        recurrence_remediation=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_roi=payload.get("recurrence_roi")
        if isinstance(payload.get("recurrence_roi"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
        recurrence_maturity=payload.get("recurrence_maturity")
        if isinstance(payload.get("recurrence_maturity"), Mapping)
        else None,
        recurrence_roadmap=payload.get("recurrence_roadmap")
        if isinstance(payload.get("recurrence_roadmap"), Mapping)
        else None,
        recurrence_completion=payload.get("recurrence_completion")
        if isinstance(payload.get("recurrence_completion"), Mapping)
        else None,
    )
    payload["recurrence_graduation_audit"] = audit
    payload["recurrence_graduation_audit_summary"] = audit["recurrence_graduation_audit_summary"]
    return payload


RECURRENCE_CONFIDENCE_CALIBRATION_TOLERANCE = 0.10
RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH = Path("docs/audits/BQC3_confidence_calibration_audit.md")
RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT = "underconfident"
RECURRENCE_CONFIDENCE_STATUS_CALIBRATED = "calibrated"
RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT = "overconfident"
RECURRENCE_CONFIDENCE_STATUSES: frozenset[str] = frozenset(
    {
        RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT,
        RECURRENCE_CONFIDENCE_STATUS_CALIBRATED,
        RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT,
    }
)
RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED = "supported"
RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC = "optimistic"
RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED = "unsupported"
RECURRENCE_GRADUATION_THRESHOLD_STATUSES: frozenset[str] = frozenset(
    {
        RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED,
        RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC,
        RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED,
    }
)
RECURRENCE_BLIND_SPOT_REDUCED = "reduced"
RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED = "partially_reduced"
RECURRENCE_BLIND_SPOT_UNCHANGED = "unchanged"
RECURRENCE_BLIND_SPOT_ESCALATED = "escalated"
RECURRENCE_CONFIDENCE_CALIBRATION_DEFINITION = (
    "Advisory confidence calibration compares reported confidence metrics against evidence "
    "strength derived from protected replay observation volume, key coverage, trajectory "
    "availability, forecast accuracy, governance posture, and lifecycle/remediation outcomes. "
    "calibration_gap = reported_confidence - evidence_strength. Positive gaps indicate "
    "overconfidence; negative gaps indicate underconfidence; gaps within tolerance indicate calibration."
)
RECURRENCE_CONFIDENCE_CALIBRATION_SCORE_DEFINITION = (
    "Advisory 0-100 calibration score: 100 * (1 - average(abs(calibration_gap))) minus 5 points "
    "per component with overconfident status and gap > 0.20. Interpretation: 90-100 well calibrated; "
    "70-89 acceptable; 50-69 needs monitoring; <50 significant calibration risk."
)
RECURRENCE_FORECAST_EVIDENCE_DEFINITION = (
    "Weighted blend: 30% observation volume factor min(1, observations/5), 20% key coverage "
    "factor min(1, keys/3), 25% trajectory factor (1.0 when trajectory_available else 0.4), "
    "25% accuracy evidence forecast_accuracy * observation volume factor."
)
RECURRENCE_GOVERNANCE_EVIDENCE_DEFINITION = (
    "Weighted blend: 30% observation volume factor, 25% watchlist coverage "
    "watchlist_size/max(keys,1), 20% owner dispersion 1 - owner_concentration_ratio, "
    "25% governance_health_score/100."
)
RECURRENCE_EFFECTIVENESS_EVIDENCE_DEFINITION = (
    "Weighted blend: 25% trajectory factor (1.0 when trajectory_available else 0.4), "
    "25% remediation effectiveness, 25% closure_rate, 25% lifecycle_health_score/100."
)
BQ16_CALIBRATION_BLIND_SPOT_IDS: tuple[str, ...] = (
    "recurrence_data_quality",
    "recurrence_trajectory_history",
    "recurrence_model_calibration",
    "recurrence_ownership_drift",
    "recurrence_confidence_decay",
    "recurrence_auditability",
)
BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES: dict[str, str] = {
    "recurrence_data_quality": "critical",
    "recurrence_trajectory_history": "critical",
    "recurrence_model_calibration": "high",
    "recurrence_ownership_drift": "medium",
    "recurrence_confidence_decay": "medium",
    "recurrence_auditability": "low",
}


def _confidence_calibration_status(
    reported_confidence: float,
    evidence_strength: float,
    *,
    tolerance: float = RECURRENCE_CONFIDENCE_CALIBRATION_TOLERANCE,
) -> str:
    gap = float(reported_confidence or 0.0) - float(evidence_strength or 0.0)
    if gap > tolerance:
        return RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
    if gap < -tolerance:
        return RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT
    return RECURRENCE_CONFIDENCE_STATUS_CALIBRATED


def _forecast_evidence_strength(
    *,
    total_observations: int,
    total_keys: int,
    forecast_accuracy: float,
    trajectory_available: bool,
) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 0)
    observation_factor = min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS))
    key_factor = min(1.0, keys / float(RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS))
    trajectory_factor = 1.0 if trajectory_available else 0.4
    accuracy = max(min(float(forecast_accuracy or 0.0), 1.0), 0.0)
    accuracy_evidence = accuracy * observation_factor
    return round(
        min(
            1.0,
            0.30 * observation_factor
            + 0.20 * key_factor
            + 0.25 * trajectory_factor
            + 0.25 * accuracy_evidence,
        ),
        2,
    )


def _governance_evidence_strength(
    *,
    total_observations: int,
    total_keys: int,
    watchlist_size: int,
    owner_concentration_ratio: float,
    governance_health_score: float,
) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 1)
    watchlist = max(int(watchlist_size or 0), 0)
    observation_factor = min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS))
    watchlist_coverage = min(1.0, watchlist / float(keys))
    owner_dispersion = 1.0 - max(min(float(owner_concentration_ratio or 0.0), 1.0), 0.0)
    governance_health_factor = max(min(float(governance_health_score or 0.0), 100.0), 0.0) / 100.0
    return round(
        min(
            1.0,
            0.30 * observation_factor
            + 0.25 * watchlist_coverage
            + 0.20 * owner_dispersion
            + 0.25 * governance_health_factor,
        ),
        2,
    )


def _effectiveness_evidence_strength(
    *,
    trajectory_available: bool,
    remediation_effectiveness: float,
    closure_rate: float,
    lifecycle_health_score: float,
) -> float:
    trajectory_factor = 1.0 if trajectory_available else 0.4
    remediation = max(min(float(remediation_effectiveness or 0.0), 1.0), 0.0)
    closure = max(min(float(closure_rate or 0.0), 1.0), 0.0)
    lifecycle_health_factor = max(min(float(lifecycle_health_score or 0.0), 100.0), 0.0) / 100.0
    return round(
        min(
            1.0,
            0.25 * trajectory_factor
            + 0.25 * remediation
            + 0.25 * closure
            + 0.25 * lifecycle_health_factor,
        ),
        2,
    )


def _audit_forecast_confidence(
    *,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    forecast_effectiveness = effectiveness.get("forecast_effectiveness_summary")
    if not isinstance(forecast_effectiveness, Mapping):
        forecast_effectiveness = {}
    trajectory_available = bool(
        trajectory.get("trajectory_available")
        or (effectiveness.get("portfolio_trajectory_summary") or {}).get("trajectory_available")
    )
    reported_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    forecast_accuracy = float(forecast_effectiveness.get("forecast_accuracy") or 0.0)
    evidence_strength = _forecast_evidence_strength(
        total_observations=total_observations,
        total_keys=total_keys,
        forecast_accuracy=forecast_accuracy,
        trajectory_available=trajectory_available,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": _confidence_calibration_status(reported_confidence, evidence_strength),
        "forecast_accuracy": forecast_accuracy,
        "total_observations": total_observations,
        "total_keys": total_keys,
        "trajectory_available": trajectory_available,
        "evidence_definition": RECURRENCE_FORECAST_EVIDENCE_DEFINITION,
    }


def _audit_governance_confidence(
    *,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_portfolio_summary: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}
    watchlist = [row for row in (governance.get("watchlist") or ()) if isinstance(row, Mapping)]
    owners = [row for row in (governance.get("owners") or ()) if isinstance(row, Mapping)]
    owner_concentration = float(portfolio_summary.get("owner_concentration_ratio") or 0.0)
    if owners:
        owner_loads = [int(row.get("watchlist_entries") or row.get("governance_load") or 0) for row in owners]
        total_load = sum(owner_loads) or 1
        owner_concentration = max(owner_concentration, max(owner_loads) / float(total_load))
    reported_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    governance_health_score = float(
        governance_summary.get("governance_health_score") or governance.get("governance_health_score") or 0.0
    )
    evidence_strength = _governance_evidence_strength(
        total_observations=total_observations,
        total_keys=total_keys,
        watchlist_size=len(watchlist),
        owner_concentration_ratio=owner_concentration,
        governance_health_score=governance_health_score,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": _confidence_calibration_status(reported_confidence, evidence_strength),
        "watchlist_size": len(watchlist),
        "total_observations": total_observations,
        "owner_count": len(owners),
        "owner_concentration_ratio": round(owner_concentration, 4),
        "governance_health_score": governance_health_score,
        "evidence_definition": RECURRENCE_GOVERNANCE_EVIDENCE_DEFINITION,
    }


def _audit_effectiveness_confidence(
    *,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_lifecycle: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    lifecycle_summary = lifecycle.get("lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    remediation = effectiveness.get("remediation_effectiveness_summary")
    if not isinstance(remediation, Mapping):
        remediation = {}
    closure = lifecycle.get("closure_effectiveness")
    if not isinstance(closure, Mapping):
        closure = {}
    trajectory_available = bool(
        trajectory.get("trajectory_available")
        or (effectiveness.get("portfolio_trajectory_summary") or {}).get("trajectory_available")
    )
    reported_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    remediation_effectiveness = float(
        remediation.get("remediation_effectiveness") or program_summary.get("remediation_effectiveness") or 0.0
    )
    closure_rate = float(closure.get("closure_rate") or lifecycle_summary.get("closure_rate") or 0.0)
    lifecycle_health_score = float(
        lifecycle_summary.get("lifecycle_health_score") or lifecycle.get("lifecycle_health_score") or 0.0
    )
    evidence_strength = _effectiveness_evidence_strength(
        trajectory_available=trajectory_available,
        remediation_effectiveness=remediation_effectiveness,
        closure_rate=closure_rate,
        lifecycle_health_score=lifecycle_health_score,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": _confidence_calibration_status(reported_confidence, evidence_strength),
        "trajectory_available": trajectory_available,
        "remediation_effectiveness": remediation_effectiveness,
        "closure_rate": closure_rate,
        "lifecycle_health_score": lifecycle_health_score,
        "evidence_definition": RECURRENCE_EFFECTIVENESS_EVIDENCE_DEFINITION,
    }


def _validate_graduation_confidence_thresholds(
    *,
    forecast_audit: Mapping[str, Any],
    governance_audit: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    recurrence_maturity: Mapping[str, Any] | None,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    maturity_summary = maturity.get("recurrence_maturity_summary")
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    completion_summary = completion.get("recurrence_completion_summary")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}

    forecast_confidence = float(forecast_audit.get("reported_confidence") or 0.0)
    effectiveness_confidence = float(effectiveness_audit.get("reported_confidence") or 0.0)
    operational_readiness = float(maturity_summary.get("operational_readiness_score") or 0.0)
    trajectory_available = bool(forecast_audit.get("trajectory_available"))
    snapshot_count = int(trajectory.get("snapshot_count") or 0)

    rows: list[dict[str, Any]] = []

    if forecast_confidence >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET:
        if str(forecast_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
            forecast_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            forecast_rationale = (
                "Forecast confidence meets graduation threshold but exceeds evidence strength; "
                "treat as structurally met, not empirically validated."
            )
        elif float(forecast_audit.get("evidence_strength") or 0.0) >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET:
            forecast_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            forecast_rationale = "Forecast confidence and evidence strength both meet graduation threshold."
        else:
            forecast_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            forecast_rationale = (
                "Forecast confidence meets threshold via observation volume, but supporting evidence "
                "remains below target."
            )
    else:
        forecast_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        forecast_rationale = "Forecast confidence remains below graduation threshold."

    rows.append(
        {
            "threshold": "forecast_confidence",
            "current_value": forecast_confidence,
            "target_value": RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
            "validation_status": forecast_status,
            "rationale": forecast_rationale,
        }
    )

    if effectiveness_confidence >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET:
        if str(effectiveness_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
            effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            effectiveness_rationale = (
                "Effectiveness confidence meets threshold but substantially exceeds remediation, "
                "closure, and trajectory evidence."
            )
        elif float(effectiveness_audit.get("evidence_strength") or 0.0) >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET:
            effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            effectiveness_rationale = "Effectiveness confidence and evidence strength both meet graduation threshold."
        else:
            effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            effectiveness_rationale = (
                "Effectiveness confidence meets threshold structurally but outcome evidence remains thin."
            )
    else:
        effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        effectiveness_rationale = "Effectiveness confidence remains below graduation threshold."

    rows.append(
        {
            "threshold": "effectiveness_confidence",
            "current_value": effectiveness_confidence,
            "target_value": RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
            "validation_status": effectiveness_status,
            "rationale": effectiveness_rationale,
        }
    )

    if operational_readiness >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET:
        if float(maturity_summary.get("overall_maturity_score") or 0.0) < RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET:
            readiness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            readiness_rationale = (
                "Operational readiness meets target while overall maturity remains below program target."
            )
        else:
            readiness_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            readiness_rationale = "Operational readiness and maturity posture support graduation threshold."
    elif operational_readiness >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET - 5.0:
        readiness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
        readiness_rationale = (
            f"Operational readiness is within 5 points of target ({operational_readiness:.1f} vs "
            f"{RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET:.1f})."
        )
    else:
        readiness_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        readiness_rationale = "Operational readiness remains materially below graduation threshold."

    rows.append(
        {
            "threshold": "operational_readiness",
            "current_value": operational_readiness,
            "target_value": RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET,
            "validation_status": readiness_status,
            "rationale": readiness_rationale,
        }
    )

    if trajectory_available:
        trajectory_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
        trajectory_rationale = "Longitudinal trajectory comparison is active across two or more snapshots."
    elif snapshot_count >= 1:
        trajectory_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
        trajectory_rationale = (
            "Trajectory baseline exists but trajectory_available remains false until snapshot #2 is captured."
        )
    else:
        trajectory_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        trajectory_rationale = "No trajectory baseline exists for protected replay recurrence analytics."

    rows.append(
        {
            "threshold": "trajectory_available",
            "current_value": trajectory_available,
            "target_value": True,
            "validation_status": trajectory_status,
            "rationale": trajectory_rationale,
        }
    )

    governance_confidence = float(governance_audit.get("reported_confidence") or 0.0)
    if governance_confidence >= RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET:
        if str(governance_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
            governance_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            governance_rationale = (
                "Governance confidence meets threshold but exceeds governance health and funnel evidence."
            )
        elif float(governance_audit.get("evidence_strength") or 0.0) >= RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET:
            governance_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            governance_rationale = "Governance confidence and evidence strength both meet graduation threshold."
        else:
            governance_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            governance_rationale = "Governance confidence meets threshold structurally but health score remains moderate."
    else:
        governance_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        governance_rationale = "Governance confidence remains below graduation threshold."

    rows.append(
        {
            "threshold": "governance_confidence",
            "current_value": governance_confidence,
            "target_value": RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET,
            "validation_status": governance_status,
            "rationale": governance_rationale,
        }
    )

    if bool(completion_summary.get("program_graduated")):
        rows.append(
            {
                "threshold": "program_graduated",
                "current_value": True,
                "target_value": True,
                "validation_status": RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED,
                "rationale": "Completion assessment marks program as graduated.",
            }
        )

    return rows


def _reassess_calibration_blind_spots(
    *,
    total_observations: int,
    total_keys: int,
    forecast_audit: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    volume_factor = _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys)
    trajectory_available = bool(trajectory.get("trajectory_available"))
    snapshot_count = int(trajectory.get("snapshot_count") or 0)
    has_trajectory_infrastructure = snapshot_count >= 1 or bool(history.get("recurrence_trajectory_history"))

    reassessments: list[dict[str, Any]] = []

    data_quality_status = (
        RECURRENCE_BLIND_SPOT_REDUCED
        if volume_factor >= 0.5
        else RECURRENCE_BLIND_SPOT_UNCHANGED
    )
    reassessments.append(
        {
            "blind_spot_id": "recurrence_data_quality",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_data_quality"],
            "status_change": data_quality_status,
            "current_severity": "medium" if data_quality_status == RECURRENCE_BLIND_SPOT_REDUCED else "critical",
            "rationale": (
                "Protected replay observation and key volume now meet maturity confidence thresholds."
                if data_quality_status == RECURRENCE_BLIND_SPOT_REDUCED
                else "Protected replay volume remains below maturity confidence thresholds."
            ),
            "blockers_remaining": [] if data_quality_status == RECURRENCE_BLIND_SPOT_REDUCED else [
                "Continue protected replay observation collection."
            ],
        }
    )

    if trajectory_available:
        trajectory_status = RECURRENCE_BLIND_SPOT_REDUCED
        trajectory_rationale = "Longitudinal trajectory comparison is active."
        trajectory_severity = "low"
        trajectory_blockers: list[str] = []
    elif has_trajectory_infrastructure:
        trajectory_status = RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
        trajectory_rationale = (
            "Trajectory infrastructure and baseline snapshot exist; trajectory_available remains false "
            "until snapshot #2."
        )
        trajectory_severity = "high"
        trajectory_blockers = ["Capture snapshot #2 to activate trajectory comparisons."]
    else:
        trajectory_status = RECURRENCE_BLIND_SPOT_UNCHANGED
        trajectory_rationale = "No longitudinal trajectory baseline exists."
        trajectory_severity = "critical"
        trajectory_blockers = ["Establish trajectory baseline snapshots."]

    reassessments.append(
        {
            "blind_spot_id": "recurrence_trajectory_history",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_trajectory_history"],
            "status_change": trajectory_status,
            "current_severity": trajectory_severity,
            "rationale": trajectory_rationale,
            "blockers_remaining": trajectory_blockers,
        }
    )

    forecast_status = str(forecast_audit.get("confidence_status") or "")
    forecast_gap = float(forecast_audit.get("calibration_gap") or 0.0)
    if forecast_status == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT and forecast_gap > 0.15:
        calibration_status = RECURRENCE_BLIND_SPOT_ESCALATED
        calibration_rationale = (
            "Forecast confidence exceeds evidence strength despite high reported accuracy; "
            "calibration audit flags overconfidence risk."
        )
        calibration_severity = "critical"
        calibration_blockers = ["Recalibrate forecast confidence or expand validation volume before graduation."]
    elif forecast_status == RECURRENCE_CONFIDENCE_STATUS_CALIBRATED:
        calibration_status = RECURRENCE_BLIND_SPOT_REDUCED
        calibration_rationale = "Forecast confidence aligns with evidence strength."
        calibration_severity = "low"
        calibration_blockers = []
    else:
        calibration_status = RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
        calibration_rationale = (
            "Volume thresholds met, but forecast confidence calibration still warrants monitoring."
        )
        calibration_severity = "medium"
        calibration_blockers = ["Monitor forecast accuracy as observation volume grows."]

    reassessments.append(
        {
            "blind_spot_id": "recurrence_model_calibration",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_model_calibration"],
            "status_change": calibration_status,
            "current_severity": calibration_severity,
            "rationale": calibration_rationale,
            "blockers_remaining": calibration_blockers,
        }
    )

    reassessments.append(
        {
            "blind_spot_id": "recurrence_ownership_drift",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_ownership_drift"],
            "status_change": RECURRENCE_BLIND_SPOT_UNCHANGED,
            "current_severity": "medium",
            "rationale": "Recurrence ownership drift is still not tracked as a dedicated longitudinal signal.",
            "blockers_remaining": ["Monitor owner_drift_bucket transitions separately from recurrence lifecycle."],
        }
    )

    reassessments.append(
        {
            "blind_spot_id": "recurrence_confidence_decay",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_confidence_decay"],
            "status_change": RECURRENCE_BLIND_SPOT_UNCHANGED,
            "current_severity": "medium",
            "rationale": "Confidence scores still do not decay with stale observations or aging keys.",
            "blockers_remaining": ["Consider temporal decay modeling if history spans long idle periods."],
        }
    )

    auditability_status = (
        RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
        if has_trajectory_infrastructure
        else RECURRENCE_BLIND_SPOT_UNCHANGED
    )
    reassessments.append(
        {
            "blind_spot_id": "recurrence_auditability",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_auditability"],
            "status_change": auditability_status,
            "current_severity": "low" if auditability_status == RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED else "low",
            "rationale": (
                "Trajectory history artifacts provide versioned snapshots, but no immutable audit chain exists."
                if auditability_status == RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
                else "No immutable audit chain links recurrence analytics revisions over time."
            ),
            "blockers_remaining": (
                ["Retain versioned history artifacts for audit replay if formal compliance is required."]
            ),
        }
    )

    if str(effectiveness_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
        reassessments.append(
            {
                "blind_spot_id": "recurrence_effectiveness_overconfidence",
                "bq16_severity": "high",
                "status_change": RECURRENCE_BLIND_SPOT_ESCALATED,
                "current_severity": "high",
                "rationale": (
                    "Effectiveness confidence substantially exceeds remediation, closure, and trajectory evidence."
                ),
                "blockers_remaining": [
                    "Do not treat effectiveness confidence as graduation-ready without outcome validation."
                ],
            }
        )

    return reassessments


def calculate_confidence_calibration_score(
    *,
    forecast_confidence_audit: Mapping[str, Any] | None,
    governance_confidence_audit: Mapping[str, Any] | None,
    effectiveness_confidence_audit: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence confidence calibration score."""
    audits = [
        forecast_confidence_audit if isinstance(forecast_confidence_audit, Mapping) else {},
        governance_confidence_audit if isinstance(governance_confidence_audit, Mapping) else {},
        effectiveness_confidence_audit if isinstance(effectiveness_confidence_audit, Mapping) else {},
    ]
    gaps = [abs(float(row.get("calibration_gap") or 0.0)) for row in audits]
    largest_gap = max(gaps) if gaps else 0.0
    average_gap = sum(gaps) / float(len(gaps)) if gaps else 0.0
    severe_overconfidence = sum(
        1
        for row in audits
        if str(row.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and float(row.get("calibration_gap") or 0.0) > 0.20
    )
    raw_score = 100.0 * (1.0 - average_gap) - severe_overconfidence * 5.0
    confidence_calibration_score = round(_clamp_maturity_score(raw_score), 1)
    if confidence_calibration_score >= 90.0:
        interpretation = "well_calibrated"
        interpretation_label = "Well calibrated"
    elif confidence_calibration_score >= 70.0:
        interpretation = "acceptable"
        interpretation_label = "Acceptable"
    elif confidence_calibration_score >= 50.0:
        interpretation = "needs_monitoring"
        interpretation_label = "Needs monitoring"
    else:
        interpretation = "significant_calibration_risk"
        interpretation_label = "Significant calibration risk"

    forecast_status = str(audits[0].get("confidence_status") or RECURRENCE_CONFIDENCE_STATUS_CALIBRATED)
    governance_status = str(audits[1].get("confidence_status") or RECURRENCE_CONFIDENCE_STATUS_CALIBRATED)
    effectiveness_status = str(audits[2].get("confidence_status") or RECURRENCE_CONFIDENCE_STATUS_CALIBRATED)
    graduation_confidence_ready = (
        confidence_calibration_score >= 70.0
        and largest_gap <= 0.20
        and severe_overconfidence == 0
        and forecast_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and governance_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and effectiveness_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
    )

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "protected_replay_only": True,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "forecast_status": forecast_status,
        "governance_status": governance_status,
        "effectiveness_status": effectiveness_status,
        "confidence_calibration_score": confidence_calibration_score,
        "interpretation": interpretation,
        "interpretation_label": interpretation_label,
        "largest_calibration_gap": round(largest_gap, 2),
        "average_calibration_gap": round(average_gap, 2),
        "severe_overconfidence_count": severe_overconfidence,
        "graduation_confidence_ready": graduation_confidence_ready,
        "score_definition": RECURRENCE_CONFIDENCE_CALIBRATION_SCORE_DEFINITION,
    }


def build_recurrence_confidence_audit(
    *,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence confidence calibration audit."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    if not portfolio_summary and isinstance(history.get("recurrence_portfolio_summary"), Mapping):
        portfolio_summary = history["recurrence_portfolio_summary"]
    total_observations = int(
        history.get("total_rows") or portfolio_summary.get("total_observations") or 0
    )
    total_keys = int(
        history.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0
    )

    forecast_confidence_audit = _audit_forecast_confidence(
        recurrence_forecast=recurrence_forecast,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    governance_confidence_audit = _audit_governance_confidence(
        recurrence_governance=recurrence_governance,
        recurrence_portfolio_summary=portfolio_summary,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    effectiveness_confidence_audit = _audit_effectiveness_confidence(
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_lifecycle=lifecycle,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
    )
    graduation_threshold_validation = _validate_graduation_confidence_thresholds(
        forecast_audit=forecast_confidence_audit,
        governance_audit=governance_confidence_audit,
        effectiveness_audit=effectiveness_confidence_audit,
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
    )
    blind_spot_reassessment = _reassess_calibration_blind_spots(
        total_observations=total_observations,
        total_keys=total_keys,
        forecast_audit=forecast_confidence_audit,
        effectiveness_audit=effectiveness_confidence_audit,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_history=history,
    )
    confidence_calibration_summary = calculate_confidence_calibration_score(
        forecast_confidence_audit=forecast_confidence_audit,
        governance_confidence_audit=governance_confidence_audit,
        effectiveness_confidence_audit=effectiveness_confidence_audit,
    )
    recommended_actions = _confidence_calibration_recommended_actions(
        confidence_calibration_summary=confidence_calibration_summary,
        graduation_threshold_validation=graduation_threshold_validation,
        blind_spot_reassessment=blind_spot_reassessment,
        forecast_audit=forecast_confidence_audit,
        effectiveness_audit=effectiveness_confidence_audit,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
    )
    audit_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "calibration_definition": RECURRENCE_CONFIDENCE_CALIBRATION_DEFINITION,
        "forecast_confidence_audit": forecast_confidence_audit,
        "governance_confidence_audit": governance_confidence_audit,
        "effectiveness_confidence_audit": effectiveness_confidence_audit,
        "graduation_threshold_validation": graduation_threshold_validation,
        "blind_spot_reassessment": blind_spot_reassessment,
        "recommended_actions": recommended_actions,
    }
    recurrence_confidence_calibration_summary = summarize_recurrence_confidence_calibration(
        audit_without_summary,
        confidence_calibration_summary=confidence_calibration_summary,
    )
    return {
        **audit_without_summary,
        "recurrence_confidence_calibration_summary": recurrence_confidence_calibration_summary,
    }


def _confidence_calibration_recommended_actions(
    *,
    confidence_calibration_summary: Mapping[str, Any],
    graduation_threshold_validation: Sequence[Mapping[str, Any]] | None,
    blind_spot_reassessment: Sequence[Mapping[str, Any]] | None,
    forecast_audit: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> list[str]:
    actions: list[str] = []
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    if not bool(trajectory.get("trajectory_available")):
        actions.append("Capture snapshot #2 to activate trajectory_available before final graduation audit.")
    if str(forecast_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
        actions.append(
            "Treat forecast confidence as volume-saturated; prioritize forecast validation over threshold celebration."
        )
    if str(effectiveness_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
        actions.append(
            "Do not treat effectiveness confidence as graduation-ready until remediation and closure evidence exists."
        )
    unsupported = [
        row
        for row in (graduation_threshold_validation or ())
        if isinstance(row, Mapping)
        and row.get("validation_status") == RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
    ]
    if unsupported:
        actions.append(
            "Resolve unsupported graduation thresholds before closing the BQ recurrence program."
        )
    for row in blind_spot_reassessment or ():
        if not isinstance(row, Mapping):
            continue
        if row.get("status_change") in {RECURRENCE_BLIND_SPOT_UNCHANGED, RECURRENCE_BLIND_SPOT_ESCALATED}:
            blockers = row.get("blockers_remaining")
            if isinstance(blockers, list):
                actions.extend(str(item) for item in blockers if str(item).strip())
    if not actions:
        if bool(confidence_calibration_summary.get("graduation_confidence_ready")):
            actions.append(
                "Confidence metrics appear calibration-ready; proceed to snapshot #2 and final graduation audit."
            )
        else:
            actions.append("Continue monitoring confidence calibration until graduation_confidence_ready is true.")
    deduped: list[str] = []
    seen: set[str] = set()
    for action in actions:
        normalized = str(action).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped[:8]


def summarize_recurrence_confidence_calibration(
    audit: Mapping[str, Any] | None,
    *,
    confidence_calibration_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence confidence calibration audit."""
    source = audit if isinstance(audit, Mapping) else {}
    summary = confidence_calibration_summary if isinstance(confidence_calibration_summary, Mapping) else {}
    if not summary:
        summary = calculate_confidence_calibration_score(
            forecast_confidence_audit=source.get("forecast_confidence_audit")
            if isinstance(source.get("forecast_confidence_audit"), Mapping)
            else None,
            governance_confidence_audit=source.get("governance_confidence_audit")
            if isinstance(source.get("governance_confidence_audit"), Mapping)
            else None,
            effectiveness_confidence_audit=source.get("effectiveness_confidence_audit")
            if isinstance(source.get("effectiveness_confidence_audit"), Mapping)
            else None,
        )
    return dict(summary)


def render_recurrence_confidence_calibration_report_markdown(
    audit: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ-C3 confidence calibration audit report."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = payload.get("recurrence_confidence_calibration_summary")
    if not isinstance(summary, Mapping):
        summary = summarize_recurrence_confidence_calibration(payload)
    forecast = payload.get("forecast_confidence_audit")
    if not isinstance(forecast, Mapping):
        forecast = {}
    governance = payload.get("governance_confidence_audit")
    if not isinstance(governance, Mapping):
        governance = {}
    effectiveness = payload.get("effectiveness_confidence_audit")
    if not isinstance(effectiveness, Mapping):
        effectiveness = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# BQ-C3 Confidence Calibration Audit",
        "",
        f"**Date:** {generated_at_s}",
        "**Protected replay only:** true",
        "",
        "## Summary",
        "",
        f"- Calibration score: `{float(summary.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Interpretation: `{summary.get('interpretation_label') or 'unknown'}`",
        f"- Largest calibration gap: `{float(summary.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Graduation confidence ready: `{str(bool(summary.get('graduation_confidence_ready'))).lower()}`",
        "",
        "# Forecast Confidence",
        "",
        f"- Reported confidence: `{float(forecast.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(forecast.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(forecast.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{forecast.get('confidence_status')}`",
        f"- Forecast accuracy: `{float(forecast.get('forecast_accuracy') or 0.0):.2f}`",
        f"- Observations: `{int(forecast.get('total_observations') or 0)}`",
        f"- Keys: `{int(forecast.get('total_keys') or 0)}`",
        f"- Trajectory available: `{str(bool(forecast.get('trajectory_available'))).lower()}`",
        "",
        "# Governance Confidence",
        "",
        f"- Reported confidence: `{float(governance.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(governance.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(governance.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{governance.get('confidence_status')}`",
        f"- Watchlist size: `{int(governance.get('watchlist_size') or 0)}`",
        f"- Governance health: `{float(governance.get('governance_health_score') or 0.0):.1f}`",
        "",
        "# Effectiveness Confidence",
        "",
        f"- Reported confidence: `{float(effectiveness.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(effectiveness.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(effectiveness.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{effectiveness.get('confidence_status')}`",
        f"- Trajectory available: `{str(bool(effectiveness.get('trajectory_available'))).lower()}`",
        f"- Remediation effectiveness: `{float(effectiveness.get('remediation_effectiveness') or 0.0):.2f}`",
        f"- Closure rate: `{float(effectiveness.get('closure_rate') or 0.0):.2f}`",
        "",
        "# Graduation Threshold Validation",
        "",
    ]
    for row in payload.get("graduation_threshold_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('threshold')}`: current `{row.get('current_value')}`, target `{row.get('target_value')}`, "
            f"status `{row.get('validation_status')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Blind Spot Reassessment", ""])
    for row in payload.get("blind_spot_reassessment") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- **{row.get('blind_spot_id')}** (BQ16 `{row.get('bq16_severity')}`, now `{row.get('current_severity')}`): "
            f"`{row.get('status_change')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Recommended Actions", ""])
    actions = payload.get("recommended_actions") or []
    if actions:
        for index, action in enumerate(actions, start=1):
            lines.append(f"{index}. {action}")
    else:
        lines.append("1. Continue monitoring confidence calibration.")
    lines.append("")
    return "\n".join(lines)


def enrich_recurrence_history_with_confidence_audit(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay confidence audit fields."""
    payload = dict(history)
    audit = build_recurrence_confidence_audit(
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
        recurrence_maturity=payload.get("recurrence_maturity")
        if isinstance(payload.get("recurrence_maturity"), Mapping)
        else None,
        recurrence_completion=payload.get("recurrence_completion")
        if isinstance(payload.get("recurrence_completion"), Mapping)
        else None,
        recurrence_trajectory_summary=payload.get("recurrence_trajectory_summary")
        if isinstance(payload.get("recurrence_trajectory_summary"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_portfolio_summary=payload.get("recurrence_portfolio_summary")
        if isinstance(payload.get("recurrence_portfolio_summary"), Mapping)
        else None,
    )
    payload["recurrence_confidence_audit"] = audit
    payload["recurrence_confidence_calibration_summary"] = audit["recurrence_confidence_calibration_summary"]
    return payload


RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH = Path("docs/audits/BQC4_final_graduation_decision.md")
RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE = "graduate_recurrence_program"
RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE = "one_final_targeted_validation_cycle_required"
RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE = "recurrence_program_remains_operationally_immature"
BQC3_CALIBRATION_BASELINE: dict[str, Any] = {
    "confidence_calibration_score": 57.3,
    "largest_calibration_gap": 0.61,
    "graduation_confidence_ready": False,
    "trajectory_available": False,
    "snapshot_count": 1,
}
RECURRENCE_FINAL_GRADUATION_DECISION_DEFINITION = (
    "Advisory final graduation decision compares post-activation calibration, readiness, and blind-spot "
    "posture against BQ-C3 baseline. Formal graduation requires calibration score >= 70, largest gap <= 0.20, "
    "trajectory_available=true, and no critical blind spots."
)


def _collect_remaining_graduation_blockers(
    *,
    recurrence_confidence_audit: Mapping[str, Any] | None,
    recurrence_graduation_audit: Mapping[str, Any] | None,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    confidence = recurrence_confidence_audit if isinstance(recurrence_confidence_audit, Mapping) else {}
    calibration = confidence.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration, Mapping):
        calibration = {}
    graduation = recurrence_graduation_audit if isinstance(recurrence_graduation_audit, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    completion_summary = completion.get("recurrence_completion_summary")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}

    if not bool(trajectory.get("trajectory_available")):
        blockers.append("trajectory_available remains false")
    if float(calibration.get("confidence_calibration_score") or 0.0) < 70.0:
        blockers.append(
            f"calibration score below target ({float(calibration.get('confidence_calibration_score') or 0.0):.1f} < 70)"
        )
    if float(calibration.get("largest_calibration_gap") or 0.0) > 0.20:
        blockers.append(
            f"largest calibration gap above target ({float(calibration.get('largest_calibration_gap') or 0.0):.2f} > 0.20)"
        )
    if not bool(calibration.get("graduation_confidence_ready")):
        blockers.append("graduation_confidence_ready is false")
    if int(graduation.get("recurrence_graduation_audit_summary", {}).get("critical_blind_spots") or 0) > 0:
        blockers.append("critical blind spots remain in graduation audit")
    for row in confidence.get("blind_spot_reassessment") or ():
        if not isinstance(row, Mapping):
            continue
        if row.get("status_change") in {"unchanged", "escalated"} and row.get("current_severity") == "critical":
            blockers.append(f"critical blind spot unresolved: {row.get('blind_spot_id')}")
    if not bool(completion_summary.get("program_graduated")):
        if completion_summary.get("remaining_dimensions"):
            remaining = completion_summary.get("remaining_dimensions")
            if isinstance(remaining, list) and remaining:
                blockers.append(
                    f"completion dimensions incomplete: {', '.join(str(item) for item in remaining)}"
                )
    readiness = graduation.get("graduation_readiness")
    if isinstance(readiness, Mapping):
        if float(readiness.get("graduation_readiness_score") or 0.0) < 90.0:
            blockers.append(
                f"graduation readiness below formal threshold ({float(readiness.get('graduation_readiness_score') or 0.0):.1f} < 90)"
            )
    for row in confidence.get("graduation_threshold_validation") or ():
        if not isinstance(row, Mapping):
            continue
        if row.get("validation_status") == RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED:
            blockers.append(f"unsupported graduation threshold: {row.get('threshold')}")
    deduped: list[str] = []
    seen: set[str] = set()
    for blocker in blockers:
        if blocker not in seen:
            seen.add(blocker)
            deduped.append(blocker)
    return deduped


def _determine_final_graduation_recommendation(
    *,
    calibration_summary: Mapping[str, Any],
    trajectory_summary: Mapping[str, Any],
    graduation_audit_summary: Mapping[str, Any],
    remaining_blockers: Sequence[str],
) -> tuple[str, str]:
    calibration_score = float(calibration_summary.get("confidence_calibration_score") or 0.0)
    largest_gap = float(calibration_summary.get("largest_calibration_gap") or 0.0)
    trajectory_available = bool(trajectory_summary.get("trajectory_available"))
    critical_blind_spots = int(graduation_audit_summary.get("critical_blind_spots") or 0)
    readiness_score = float(graduation_audit_summary.get("graduation_readiness_score") or 0.0)

    formal_ready = (
        calibration_score >= 70.0
        and largest_gap <= 0.20
        and trajectory_available
        and critical_blind_spots == 0
        and bool(calibration_summary.get("graduation_confidence_ready"))
    )
    if formal_ready and readiness_score >= 90.0 and not remaining_blockers:
        return (
            RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE,
            "Formal graduation criteria met: calibration, trajectory, readiness, and blind-spot posture support program closure.",
        )

    if trajectory_available and readiness_score >= 70.0:
        return (
            RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE,
            "Trajectory is active and readiness improved, but confidence or outcome evidence still requires one narrowly scoped validation cycle.",
        )

    return (
        RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE,
        "Recurrence program remains operationally immature relative to graduation confidence and outcome evidence requirements.",
    )


def build_recurrence_final_graduation_decision(
    *,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    recurrence_trajectory_history: Mapping[str, Any] | None = None,
    recurrence_confidence_audit: Mapping[str, Any] | None = None,
    recurrence_graduation_audit: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    bqc3_calibration_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay final graduation decision audit (BQ-C4)."""
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    trajectory_history = (
        recurrence_trajectory_history if isinstance(recurrence_trajectory_history, Mapping) else {}
    )
    confidence = recurrence_confidence_audit if isinstance(recurrence_confidence_audit, Mapping) else {}
    graduation = recurrence_graduation_audit if isinstance(recurrence_graduation_audit, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    baseline = bqc3_calibration_baseline if isinstance(bqc3_calibration_baseline, Mapping) else BQC3_CALIBRATION_BASELINE

    calibration_summary = confidence.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration_summary, Mapping):
        calibration_summary = summarize_recurrence_confidence_calibration(confidence)
    graduation_summary = graduation.get("recurrence_graduation_audit_summary")
    if not isinstance(graduation_summary, Mapping):
        graduation_summary = summarize_recurrence_graduation_audit(graduation)
    completion_summary = completion.get("recurrence_completion_summary")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}
    maturity_summary = maturity.get("recurrence_maturity_summary")
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}

    calibration_score = float(calibration_summary.get("confidence_calibration_score") or 0.0)
    largest_gap = float(calibration_summary.get("largest_calibration_gap") or 0.0)
    baseline_score = float(baseline.get("confidence_calibration_score") or 0.0)
    baseline_gap = float(baseline.get("largest_calibration_gap") or 0.0)
    remaining_blockers = _collect_remaining_graduation_blockers(
        recurrence_confidence_audit=confidence,
        recurrence_graduation_audit=graduation,
        recurrence_completion=completion,
        recurrence_trajectory_summary=trajectory,
    )
    recommendation, recommendation_rationale = _determine_final_graduation_recommendation(
        calibration_summary=calibration_summary,
        trajectory_summary=trajectory,
        graduation_audit_summary=graduation_summary,
        remaining_blockers=remaining_blockers,
    )

    snapshots = [row for row in (trajectory_history.get("snapshots") or ()) if isinstance(row, Mapping)]
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "decision_definition": RECURRENCE_FINAL_GRADUATION_DECISION_DEFINITION,
        "trajectory_activation": {
            "snapshot_count": int(trajectory.get("snapshot_count") or len(snapshots)),
            "trajectory_available": bool(trajectory.get("trajectory_available")),
            "baseline_only": bool(trajectory.get("baseline_only")),
            "portfolio_risk_change": float(trajectory.get("portfolio_risk_change") or 0.0),
            "governance_health_change": float(trajectory.get("governance_health_change") or 0.0),
            "lifecycle_health_change": float(trajectory.get("lifecycle_health_change") or 0.0),
            "operational_readiness_change": float(trajectory.get("operational_readiness_change") or 0.0),
            "effectiveness_change": float(trajectory.get("effectiveness_change") or 0.0),
            "maturity_change": float(trajectory.get("maturity_change") or 0.0),
            "stability_change": float((trajectory.get("stability_trajectory") or {}).get("absolute_change") or 0.0),
            "message": trajectory.get("message"),
        },
        "confidence_recalculation": {
            "forecast_confidence_audit": confidence.get("forecast_confidence_audit"),
            "governance_confidence_audit": confidence.get("governance_confidence_audit"),
            "effectiveness_confidence_audit": confidence.get("effectiveness_confidence_audit"),
            "recurrence_confidence_calibration_summary": dict(calibration_summary),
        },
        "calibration_comparison": {
            "bqc3_baseline": dict(baseline),
            "bqc4_current": {
                "confidence_calibration_score": calibration_score,
                "largest_calibration_gap": largest_gap,
                "graduation_confidence_ready": bool(calibration_summary.get("graduation_confidence_ready")),
                "trajectory_available": bool(trajectory.get("trajectory_available")),
                "snapshot_count": int(trajectory.get("snapshot_count") or len(snapshots)),
            },
            "calibration_score_delta": round(calibration_score - baseline_score, 1),
            "largest_gap_delta": round(largest_gap - baseline_gap, 2),
            "trajectory_activated": bool(trajectory.get("trajectory_available"))
            and not bool(baseline.get("trajectory_available")),
        },
        "graduation_readiness": {
            "graduation_readiness_score": float(graduation_summary.get("graduation_readiness_score") or 0.0),
            "readiness_level": graduation_summary.get("readiness_level"),
            "readiness_label": graduation_summary.get("readiness_label"),
            "overall_completion_score": float(completion_summary.get("overall_completion_score") or 0.0),
            "overall_maturity_score": float(maturity_summary.get("overall_maturity_score") or 0.0),
            "operational_readiness_score": float(maturity_summary.get("operational_readiness_score") or 0.0),
            "program_graduated": bool(completion_summary.get("program_graduated")),
            "critical_blind_spots": int(graduation_summary.get("critical_blind_spots") or 0),
        },
        "remaining_blockers": remaining_blockers,
        "final_recommendation": recommendation,
        "final_recommendation_rationale": recommendation_rationale,
        "formal_graduation_criteria_met": recommendation == RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE,
    }


def render_recurrence_final_graduation_decision_report_markdown(
    decision: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ-C4 final graduation decision report."""
    payload = decision if isinstance(decision, Mapping) else {}
    activation = payload.get("trajectory_activation")
    if not isinstance(activation, Mapping):
        activation = {}
    comparison = payload.get("calibration_comparison")
    if not isinstance(comparison, Mapping):
        comparison = {}
    bqc3 = comparison.get("bqc3_baseline")
    if not isinstance(bqc3, Mapping):
        bqc3 = {}
    bqc4 = comparison.get("bqc4_current")
    if not isinstance(bqc4, Mapping):
        bqc4 = {}
    readiness = payload.get("graduation_readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    confidence = payload.get("confidence_recalculation")
    if not isinstance(confidence, Mapping):
        confidence = {}
    calibration = confidence.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration, Mapping):
        calibration = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    recommendation = payload.get("final_recommendation")
    if recommendation == RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE:
        recommendation_label = "A. Graduate recurrence program"
    elif recommendation == RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE:
        recommendation_label = "B. One final targeted validation cycle required"
    else:
        recommendation_label = "C. Recurrence program remains operationally immature"

    lines = [
        "# BQ-C4 Final Graduation Decision",
        "",
        f"**Date:** {generated_at_s}",
        "**Protected replay only:** true",
        "",
        "# Trajectory Activation",
        "",
        f"- Snapshot count: `{int(activation.get('snapshot_count') or 0)}`",
        f"- Trajectory available: `{str(bool(activation.get('trajectory_available'))).lower()}`",
        f"- Portfolio risk change: `{float(activation.get('portfolio_risk_change') or 0.0):.4f}`",
        f"- Governance health change: `{float(activation.get('governance_health_change') or 0.0):.4f}`",
        f"- Lifecycle health change: `{float(activation.get('lifecycle_health_change') or 0.0):.4f}`",
        f"- Operational readiness change: `{float(activation.get('operational_readiness_change') or 0.0):.4f}`",
        f"- Effectiveness change: `{float(activation.get('effectiveness_change') or 0.0):.4f}`",
        f"- Maturity change: `{float(activation.get('maturity_change') or 0.0):.4f}`",
        f"- Stability change: `{float(activation.get('stability_change') or 0.0):.4f}`",
        f"- Message: {activation.get('message') or 'none recorded'}",
        "",
        "# Confidence Recalculation",
        "",
        f"- Calibration score: `{float(calibration.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Largest calibration gap: `{float(calibration.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Graduation confidence ready: `{str(bool(calibration.get('graduation_confidence_ready'))).lower()}`",
        f"- Forecast status: `{calibration.get('forecast_status')}`",
        f"- Governance status: `{calibration.get('governance_status')}`",
        f"- Effectiveness status: `{calibration.get('effectiveness_status')}`",
        "",
        "# Calibration Comparison",
        "",
        f"- BQ-C3 calibration score: `{float(bqc3.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- BQ-C4 calibration score: `{float(bqc4.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Score delta: `{float(comparison.get('calibration_score_delta') or 0.0):+.1f}`",
        f"- BQ-C3 largest gap: `{float(bqc3.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- BQ-C4 largest gap: `{float(bqc4.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Gap delta: `{float(comparison.get('largest_gap_delta') or 0.0):+.2f}`",
        f"- Trajectory activated: `{str(bool(comparison.get('trajectory_activated'))).lower()}`",
        "",
        "# Graduation Readiness",
        "",
        f"- Graduation readiness score: `{float(readiness.get('graduation_readiness_score') or 0.0):.1f}`",
        f"- Readiness level: `{readiness.get('readiness_label') or readiness.get('readiness_level')}`",
        f"- Overall completion score: `{float(readiness.get('overall_completion_score') or 0.0):.1f}`",
        f"- Overall maturity score: `{float(readiness.get('overall_maturity_score') or 0.0):.1f}`",
        f"- Operational readiness score: `{float(readiness.get('operational_readiness_score') or 0.0):.1f}`",
        f"- Program graduated: `{str(bool(readiness.get('program_graduated'))).lower()}`",
        f"- Critical blind spots: `{int(readiness.get('critical_blind_spots') or 0)}`",
        "",
        "# Remaining Blockers",
        "",
    ]
    blockers = payload.get("remaining_blockers") or []
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- No remaining blockers recorded.")
    lines.extend(
        [
            "",
            "# Final Recommendation",
            "",
            f"**{recommendation_label}**",
            "",
            str(payload.get("final_recommendation_rationale") or "No rationale recorded."),
            "",
        ]
    )
    return "\n".join(lines)


RECURRENCE_OUTCOME_VALIDATION_DOC_PATH = Path("docs/audits/BQC5_effectiveness_validation.md")
RECURRENCE_OUTCOME_SIGNAL_RETIRED = "retired_recurrence_key"
RECURRENCE_OUTCOME_SIGNAL_DORMANT = "dormant_recurrence_key"
RECURRENCE_OUTCOME_SIGNAL_REDUCTION = "measurable_recurrence_reduction"
RECURRENCE_OUTCOME_SIGNAL_REMEDIATION = "confirmed_remediation_impact"
RECURRENCE_OUTCOME_SIGNALS: frozenset[str] = frozenset(
    {
        RECURRENCE_OUTCOME_SIGNAL_RETIRED,
        RECURRENCE_OUTCOME_SIGNAL_DORMANT,
        RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
        RECURRENCE_OUTCOME_SIGNAL_REMEDIATION,
    }
)
RECURRENCE_OUTCOME_REJECTION_SYNTHETIC = "synthetic_key_rejected"
RECURRENCE_OUTCOME_REJECTION_INFERRED = "inferred_without_evidence"
RECURRENCE_OUTCOME_REJECTION_FORCED = "manually_forced_status_rejected"
RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT = "insufficient_evidence"
RECURRENCE_OUTCOME_VALIDATION_DEFINITION = (
    "Advisory protected replay outcome validation accepts only evidenced lifecycle closures "
    "(retired/dormant keys with event-log or inactivity backing), measurable trajectory "
    "recurrence reduction, or confirmed remediation impact on targeted keys. Synthetic keys, "
    "manually forced statuses, and inferred success without evidence are rejected."
)
RECURRENCE_OUTCOME_EVIDENCE_STRENGTH_DEFINITION = (
    "Outcome-grounded 0-1 effectiveness evidence: 20% trajectory factor + 40% validated outcome "
    "coverage (validated_outcomes / total_keys) + 40% max(validated_closure_rate, "
    "validated_recurrence_reduction_rate, validated_remediation_impact_rate)."
)
BQC4_EFFECTIVENESS_BASELINE: dict[str, Any] = {
    "reported_confidence": 0.82,
    "evidence_strength": 0.18,
    "calibration_gap": 0.64,
    "confidence_calibration_score": 61.3,
    "largest_calibration_gap": 0.64,
    "graduation_confidence_ready": False,
}
BQC5_GRADUATION_RECOMMENDATION_GRADUATE = "graduate_recurrence_program"
BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD = "one_additional_validation_period_required"
BQC5_GRADUATION_RECOMMENDATION_IMMATURE = "recurrence_program_remains_operationally_immature"


def _days_since_timestamp(value: Any, *, as_of: Any | None = None) -> float:
    last_dt = _parse_iso_timestamp(value)
    as_of_dt = _parse_iso_timestamp(as_of) or datetime.now(UTC)
    if last_dt is None:
        return 0.0
    return max((as_of_dt - last_dt).total_seconds() / 86400.0, 0.0)


def _event_log_rows_for_key(
    event_log: Mapping[str, Any] | None,
    recurrence_key: str,
) -> list[dict[str, Any]]:
    log = event_log if isinstance(event_log, Mapping) else {}
    rows: list[dict[str, Any]] = []
    for event in log.get("events") or ():
        if not isinstance(event, Mapping):
            continue
        if str(event.get("recurrence_key") or "").strip() == str(recurrence_key or "").strip():
            rows.append(dict(event))
    return rows


def _validate_retired_outcome_signal(
    key_row: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    key = str(key_row.get("recurrence_key") or "").strip()
    if not key:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    if is_synthetic_drift_recurrence_key(key):
        return None, RECURRENCE_OUTCOME_REJECTION_SYNTHETIC
    if str(key_row.get("lifecycle_stage") or "") != RECURRENCE_LIFECYCLE_RETIRED:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    events = _event_log_rows_for_key(event_log, key)
    explicit_retired = any(
        str(event.get("recurrence_status") or "").lower() in {"retired", "deprecated"} for event in events
    )
    inactivity_days = _days_since_timestamp(key_row.get("last_seen"), as_of=as_of)
    if explicit_retired:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_RETIRED,
            "recurrence_key": key,
            "evidence_source": "event_log_recurrence_status",
            "inactivity_days": round(inactivity_days, 4),
        }, None
    if inactivity_days >= RECURRENCE_LIFECYCLE_RETIREMENT_INACTIVITY_DAYS:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_RETIRED,
            "recurrence_key": key,
            "evidence_source": "natural_inactivity_retirement_threshold",
            "inactivity_days": round(inactivity_days, 4),
        }, None
    return None, RECURRENCE_OUTCOME_REJECTION_INFERRED


def _validate_dormant_outcome_signal(
    key_row: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    key = str(key_row.get("recurrence_key") or "").strip()
    if not key:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    if is_synthetic_drift_recurrence_key(key):
        return None, RECURRENCE_OUTCOME_REJECTION_SYNTHETIC
    if str(key_row.get("lifecycle_stage") or "") != RECURRENCE_LIFECYCLE_DORMANT:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    events = _event_log_rows_for_key(event_log, key)
    if any(str(event.get("recurrence_status") or "").lower() in {"retired", "deprecated"} for event in events):
        return None, RECURRENCE_OUTCOME_REJECTION_FORCED
    inactivity_days = _days_since_timestamp(key_row.get("last_seen"), as_of=as_of)
    if inactivity_days < RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS:
        return None, RECURRENCE_OUTCOME_REJECTION_INFERRED
    return {
        "signal_type": RECURRENCE_OUTCOME_SIGNAL_DORMANT,
        "recurrence_key": key,
        "evidence_source": "protected_replay_inactivity_threshold",
        "inactivity_days": round(inactivity_days, 4),
    }, None


def _validate_measurable_recurrence_reduction(
    *,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    if not bool(trajectory.get("trajectory_available")):
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    regression_trajectory = trajectory.get("regression_rate_trajectory")
    if not isinstance(regression_trajectory, Mapping):
        regression_trajectory = {}
    regression_change = float(regression_trajectory.get("absolute_change") or 0.0)
    if regression_change < -0.0001:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
            "evidence_source": "trajectory_regression_rate_decrease",
            "absolute_change": round(regression_change, 4),
        }, None
    portfolio_change = float(trajectory.get("portfolio_risk_change") or 0.0)
    if portfolio_change < -0.0001:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
            "evidence_source": "trajectory_portfolio_risk_decrease",
            "absolute_change": round(portfolio_change, 4),
        }, None
    remediation = effectiveness.get("remediation_effectiveness_summary")
    if isinstance(remediation, Mapping):
        reduction_rate = float(remediation.get("recurrence_reduction_rate") or 0.0)
        improved_keys = int(remediation.get("improved_keys") or 0)
        if reduction_rate > 0.0 and improved_keys > 0:
            return {
                "signal_type": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
                "evidence_source": "remediation_improved_keys",
                "recurrence_reduction_rate": round(reduction_rate, 4),
                "improved_keys": improved_keys,
            }, None
    return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT


def _validate_remediation_impact_signal(
    key_row: Mapping[str, Any],
    *,
    remediation_by_key: Mapping[str, Mapping[str, Any]],
    validated_closure_keys: set[str],
) -> tuple[dict[str, Any] | None, str | None]:
    key = str(key_row.get("recurrence_key") or "").strip()
    if not key or key not in validated_closure_keys:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    remediation = remediation_by_key.get(key)
    if not isinstance(remediation, Mapping):
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    reduction_potential = float(remediation.get("reduction_potential") or 0.0)
    if reduction_potential <= 0.0:
        return None, RECURRENCE_OUTCOME_REJECTION_INFERRED
    return {
        "signal_type": RECURRENCE_OUTCOME_SIGNAL_REMEDIATION,
        "recurrence_key": key,
        "evidence_source": "targeted_key_with_validated_closure",
        "reduction_potential": round(reduction_potential, 4),
    }, None


def summarize_recurrence_outcomes(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Summarize validated protected replay recurrence outcome evidence."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    targets = recurrence_remediation_targets if isinstance(recurrence_remediation_targets, Mapping) else {}
    if not targets and isinstance(history.get("recurrence_remediation_targets"), Mapping):
        targets = history["recurrence_remediation_targets"]
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    if not trajectory and isinstance(history.get("recurrence_trajectory_summary"), Mapping):
        trajectory = history["recurrence_trajectory_summary"]

    lifecycle_keys = [dict(row) for row in (lifecycle.get("keys") or ()) if isinstance(row, Mapping)]
    total_keys = int(lifecycle.get("total_keys") or history.get("unique_recurrence_count") or len(lifecycle_keys))
    remediation_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (targets.get("keys") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }

    validated_outcomes: list[dict[str, Any]] = []
    rejected_signals: list[dict[str, Any]] = []
    validated_closure_keys: set[str] = set()
    retired_keys = 0
    dormant_keys = 0

    for key_row in lifecycle_keys:
        retired_signal, retired_reason = _validate_retired_outcome_signal(
            key_row,
            event_log=event_log,
            as_of=as_of,
        )
        if retired_signal:
            validated_outcomes.append(retired_signal)
            validated_closure_keys.add(str(retired_signal.get("recurrence_key") or ""))
            retired_keys += 1
            continue
        if retired_reason and str(key_row.get("lifecycle_stage") or "") == RECURRENCE_LIFECYCLE_RETIRED:
            rejected_signals.append(
                {
                    "recurrence_key": key_row.get("recurrence_key"),
                    "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_RETIRED,
                    "rejection_reason": retired_reason,
                }
            )

        dormant_signal, dormant_reason = _validate_dormant_outcome_signal(
            key_row,
            event_log=event_log,
            as_of=as_of,
        )
        if dormant_signal:
            validated_outcomes.append(dormant_signal)
            validated_closure_keys.add(str(dormant_signal.get("recurrence_key") or ""))
            dormant_keys += 1
            continue
        if dormant_reason and str(key_row.get("lifecycle_stage") or "") == RECURRENCE_LIFECYCLE_DORMANT:
            rejected_signals.append(
                {
                    "recurrence_key": key_row.get("recurrence_key"),
                    "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_DORMANT,
                    "rejection_reason": dormant_reason,
                }
            )

    reduction_signal, reduction_reason = _validate_measurable_recurrence_reduction(
        recurrence_trajectory_summary=trajectory,
        recurrence_program_effectiveness=effectiveness,
    )
    if reduction_signal:
        validated_outcomes.append(reduction_signal)
    elif reduction_reason:
        rejected_signals.append(
            {
                "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
                "rejection_reason": reduction_reason,
            }
        )

    for key_row in lifecycle_keys:
        remediation_signal, remediation_reason = _validate_remediation_impact_signal(
            key_row,
            remediation_by_key=remediation_by_key,
            validated_closure_keys=validated_closure_keys,
        )
        if remediation_signal:
            validated_outcomes.append(remediation_signal)
        elif (
            remediation_reason
            and str(key_row.get("recurrence_key") or "") in remediation_by_key
            and str(key_row.get("lifecycle_stage") or "")
            in {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}
        ):
            rejected_signals.append(
                {
                    "recurrence_key": key_row.get("recurrence_key"),
                    "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_REMEDIATION,
                    "rejection_reason": remediation_reason,
                }
            )

    validated_outcome_count = len(validated_outcomes)
    denominator = max(total_keys, 1)
    validated_closure_rate = round((retired_keys + dormant_keys) / float(denominator), 4)
    validated_reduction_rate = 0.0
    validated_remediation_rate = 0.0
    for row in validated_outcomes:
        signal_type = str(row.get("signal_type") or "")
        if signal_type == RECURRENCE_OUTCOME_SIGNAL_REDUCTION:
            validated_reduction_rate = max(
                validated_reduction_rate,
                float(row.get("recurrence_reduction_rate") or abs(float(row.get("absolute_change") or 0.0))),
            )
        if signal_type == RECURRENCE_OUTCOME_SIGNAL_REMEDIATION:
            validated_remediation_rate = max(validated_remediation_rate, 1.0 / float(denominator))

    active_keys = sum(
        1
        for row in lifecycle_keys
        if str(row.get("lifecycle_stage") or "")
        not in {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}
    )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_OUTCOME_VALIDATION_DEFINITION,
        "total_keys": total_keys,
        "active_keys": active_keys,
        "retired_keys": retired_keys,
        "dormant_keys": dormant_keys,
        "validated_outcome_count": validated_outcome_count,
        "validated_outcomes": validated_outcomes,
        "rejected_signals": rejected_signals,
        "validated_closure_rate": validated_closure_rate,
        "validated_recurrence_reduction_rate": round(validated_reduction_rate, 4),
        "validated_remediation_impact_rate": round(validated_remediation_rate, 4),
        "has_validated_outcomes": validated_outcome_count > 0,
        "outcome_evidence_strength_definition": RECURRENCE_OUTCOME_EVIDENCE_STRENGTH_DEFINITION,
    }


def calculate_effectiveness_evidence_strength(
    *,
    outcome_validation_summary: Mapping[str, Any] | None,
    trajectory_available: bool,
) -> float:
    """Calculate outcome-grounded protected replay effectiveness evidence strength."""
    summary = outcome_validation_summary if isinstance(outcome_validation_summary, Mapping) else {}
    total_keys = max(int(summary.get("total_keys") or 0), 1)
    validated_count = int(summary.get("validated_outcome_count") or 0)
    outcome_coverage = min(1.0, validated_count / float(total_keys))
    validated_closure_rate = float(summary.get("validated_closure_rate") or 0.0)
    validated_reduction_rate = float(summary.get("validated_recurrence_reduction_rate") or 0.0)
    validated_remediation_rate = float(summary.get("validated_remediation_impact_rate") or 0.0)
    outcome_signal = max(validated_closure_rate, validated_reduction_rate, validated_remediation_rate)
    trajectory_factor = 1.0 if trajectory_available else 0.4
    if not bool(summary.get("has_validated_outcomes")):
        outcome_coverage = 0.0
        outcome_signal = 0.0
    return round(
        min(
            1.0,
            0.20 * trajectory_factor + 0.40 * outcome_coverage + 0.40 * outcome_signal,
        ),
        2,
    )


def _audit_effectiveness_confidence_with_outcomes(
    *,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    outcome_validation_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    trajectory_available = bool(
        trajectory.get("trajectory_available")
        or (effectiveness.get("portfolio_trajectory_summary") or {}).get("trajectory_available")
    )
    reported_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    evidence_strength = calculate_effectiveness_evidence_strength(
        outcome_validation_summary=outcome_validation_summary,
        trajectory_available=trajectory_available,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    outcome_summary = outcome_validation_summary if isinstance(outcome_validation_summary, Mapping) else {}
    confidence_status = _confidence_calibration_status(reported_confidence, evidence_strength)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": confidence_status,
        "trajectory_available": trajectory_available,
        "validated_outcome_count": int(outcome_summary.get("validated_outcome_count") or 0),
        "validated_closure_rate": float(outcome_summary.get("validated_closure_rate") or 0.0),
        "validated_recurrence_reduction_rate": float(
            outcome_summary.get("validated_recurrence_reduction_rate") or 0.0
        ),
        "validated_remediation_impact_rate": float(
            outcome_summary.get("validated_remediation_impact_rate") or 0.0
        ),
        "outcome_supported": bool(outcome_summary.get("has_validated_outcomes"))
        and confidence_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and evidence_strength >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET * 0.5,
        "evidence_definition": RECURRENCE_OUTCOME_EVIDENCE_STRENGTH_DEFINITION,
    }


def _determine_bqc5_graduation_recommendation(
    *,
    calibration_summary: Mapping[str, Any],
    trajectory_summary: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    graduation_audit_summary: Mapping[str, Any],
    outcome_validation_summary: Mapping[str, Any],
) -> tuple[str, str]:
    calibration_score = float(calibration_summary.get("confidence_calibration_score") or 0.0)
    largest_gap = float(calibration_summary.get("largest_calibration_gap") or 0.0)
    trajectory_available = bool(trajectory_summary.get("trajectory_available"))
    critical_blind_spots = int(graduation_audit_summary.get("critical_blind_spots") or 0)
    outcome_supported = bool(effectiveness_audit.get("outcome_supported"))
    has_outcomes = bool(outcome_validation_summary.get("has_validated_outcomes"))

    formal_ready = (
        calibration_score >= 70.0
        and largest_gap <= 0.20
        and trajectory_available
        and outcome_supported
        and has_outcomes
        and critical_blind_spots == 0
        and bool(calibration_summary.get("graduation_confidence_ready"))
    )
    if formal_ready:
        return (
            BQC5_GRADUATION_RECOMMENDATION_GRADUATE,
            "Outcome evidence validates effectiveness confidence; calibration and readiness criteria support formal program graduation.",
        )
    if trajectory_available and has_outcomes:
        return (
            BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD,
            "Some outcome evidence exists but calibration or effectiveness support remains insufficient for graduation.",
        )
    if trajectory_available:
        return (
            BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD,
            "Trajectory is active but no validated outcome evidence exists; one additional validation period is required.",
        )
    return (
        BQC5_GRADUATION_RECOMMENDATION_IMMATURE,
        "Recurrence program lacks trajectory activation and validated outcome evidence required for graduation.",
    )


def build_recurrence_outcome_validation(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
    recurrence_graduation_audit: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
    bqc4_effectiveness_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence outcome validation and recalibrated confidence audit."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    outcome_validation_summary = summarize_recurrence_outcomes(
        recurrence_history=history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        event_log=event_log,
        as_of=as_of,
    )
    base_confidence_audit = build_recurrence_confidence_audit(
        recurrence_forecast=recurrence_forecast,
        recurrence_governance=recurrence_governance,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_history=history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_portfolio_summary=history.get("recurrence_portfolio_summary")
        if isinstance(history.get("recurrence_portfolio_summary"), Mapping)
        else None,
    )
    outcome_effectiveness_audit = _audit_effectiveness_confidence_with_outcomes(
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        outcome_validation_summary=outcome_validation_summary,
    )
    confidence_audit = dict(base_confidence_audit)
    confidence_audit["effectiveness_confidence_audit"] = outcome_effectiveness_audit
    confidence_audit["outcome_validation_summary"] = outcome_validation_summary
    confidence_audit["recurrence_confidence_calibration_summary"] = calculate_confidence_calibration_score(
        forecast_confidence_audit=confidence_audit.get("forecast_confidence_audit"),
        governance_confidence_audit=confidence_audit.get("governance_confidence_audit"),
        effectiveness_confidence_audit=outcome_effectiveness_audit,
    )
    calibration_summary = confidence_audit["recurrence_confidence_calibration_summary"]
    baseline = bqc4_effectiveness_baseline if isinstance(bqc4_effectiveness_baseline, Mapping) else BQC4_EFFECTIVENESS_BASELINE
    graduation = recurrence_graduation_audit if isinstance(recurrence_graduation_audit, Mapping) else {}
    graduation_summary = graduation.get("recurrence_graduation_audit_summary")
    if not isinstance(graduation_summary, Mapping):
        graduation_summary = summarize_recurrence_graduation_audit(graduation)
    recommendation, recommendation_rationale = _determine_bqc5_graduation_recommendation(
        calibration_summary=calibration_summary,
        trajectory_summary=recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {},
        effectiveness_audit=outcome_effectiveness_audit,
        graduation_audit_summary=graduation_summary,
        outcome_validation_summary=outcome_validation_summary,
    )
    missing_outcome_signal = None
    if not bool(outcome_validation_summary.get("has_validated_outcomes")):
        missing_outcome_signal = (
            "At least one validated outcome event is required: retired key, dormant key, "
            "measurable recurrence reduction, or confirmed remediation impact."
        )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "validation_definition": RECURRENCE_OUTCOME_VALIDATION_DEFINITION,
        "outcome_validation_summary": outcome_validation_summary,
        "effectiveness_confidence_audit": outcome_effectiveness_audit,
        "recurrence_confidence_audit": confidence_audit,
        "recurrence_confidence_calibration_summary": calibration_summary,
        "calibration_comparison": {
            "bqc4_baseline": dict(baseline),
            "bqc5_current": {
                "reported_confidence": float(outcome_effectiveness_audit.get("reported_confidence") or 0.0),
                "evidence_strength": float(outcome_effectiveness_audit.get("evidence_strength") or 0.0),
                "calibration_gap": float(outcome_effectiveness_audit.get("calibration_gap") or 0.0),
                "confidence_calibration_score": float(
                    calibration_summary.get("confidence_calibration_score") or 0.0
                ),
                "largest_calibration_gap": float(calibration_summary.get("largest_calibration_gap") or 0.0),
                "graduation_confidence_ready": bool(calibration_summary.get("graduation_confidence_ready")),
            },
            "effectiveness_evidence_delta": round(
                float(outcome_effectiveness_audit.get("evidence_strength") or 0.0)
                - float(baseline.get("evidence_strength") or 0.0),
                2,
            ),
            "calibration_score_delta": round(
                float(calibration_summary.get("confidence_calibration_score") or 0.0)
                - float(baseline.get("confidence_calibration_score") or 0.0),
                1,
            ),
            "largest_gap_delta": round(
                float(calibration_summary.get("largest_calibration_gap") or 0.0)
                - float(baseline.get("largest_calibration_gap") or 0.0),
                2,
            ),
        },
        "final_graduation_recommendation": recommendation,
        "final_graduation_recommendation_rationale": recommendation_rationale,
        "missing_outcome_signal": missing_outcome_signal,
        "formal_graduation_criteria_met": recommendation == BQC5_GRADUATION_RECOMMENDATION_GRADUATE,
    }


def render_recurrence_outcome_validation_report_markdown(
    validation: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ-C5 effectiveness outcome validation report."""
    payload = validation if isinstance(validation, Mapping) else {}
    outcomes = payload.get("outcome_validation_summary")
    if not isinstance(outcomes, Mapping):
        outcomes = {}
    effectiveness = payload.get("effectiveness_confidence_audit")
    if not isinstance(effectiveness, Mapping):
        effectiveness = {}
    calibration = payload.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration, Mapping):
        calibration = {}
    comparison = payload.get("calibration_comparison")
    if not isinstance(comparison, Mapping):
        comparison = {}
    bqc4 = comparison.get("bqc4_baseline")
    if not isinstance(bqc4, Mapping):
        bqc4 = {}
    bqc5 = comparison.get("bqc5_current")
    if not isinstance(bqc5, Mapping):
        bqc5 = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    recommendation = payload.get("final_graduation_recommendation")
    if recommendation == BQC5_GRADUATION_RECOMMENDATION_GRADUATE:
        recommendation_label = "A. Graduate recurrence program"
    elif recommendation == BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD:
        recommendation_label = "B. One additional validation period required"
    else:
        recommendation_label = "C. Recurrence program remains operationally immature"

    lines = [
        "# BQ-C5 Effectiveness Outcome Validation",
        "",
        f"**Date:** {generated_at_s}",
        "**Protected replay only:** true",
        "",
        "# Outcome Evidence",
        "",
        f"- Total keys: `{int(outcomes.get('total_keys') or 0)}`",
        f"- Active keys: `{int(outcomes.get('active_keys') or 0)}`",
        f"- Validated retired keys: `{int(outcomes.get('retired_keys') or 0)}`",
        f"- Validated dormant keys: `{int(outcomes.get('dormant_keys') or 0)}`",
        f"- Validated outcome count: `{int(outcomes.get('validated_outcome_count') or 0)}`",
        f"- Has validated outcomes: `{str(bool(outcomes.get('has_validated_outcomes'))).lower()}`",
        "",
    ]
    validated_rows = outcomes.get("validated_outcomes") or []
    if validated_rows:
        for row in validated_rows:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"- `{row.get('signal_type')}`: {row.get('recurrence_key') or row.get('evidence_source')}"
            )
    else:
        lines.append("- No validated outcome signals discovered.")
    rejected_rows = outcomes.get("rejected_signals") or []
    if rejected_rows:
        lines.extend(["", "### Rejected Candidates", ""])
        for row in rejected_rows:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"- `{row.get('candidate_signal')}` ({row.get('recurrence_key') or 'portfolio'}): "
                f"{row.get('rejection_reason')}"
            )
    lines.extend(
        [
            "",
            "# Effectiveness Confidence",
            "",
            f"- Reported confidence: `{float(effectiveness.get('reported_confidence') or 0.0):.2f}`",
            f"- Outcome evidence strength: `{float(effectiveness.get('evidence_strength') or 0.0):.2f}`",
            f"- Calibration gap: `{float(effectiveness.get('calibration_gap') or 0.0):.2f}`",
            f"- Status: `{effectiveness.get('confidence_status')}`",
            f"- Outcome supported: `{str(bool(effectiveness.get('outcome_supported'))).lower()}`",
            "",
            "# Calibration Recalculation",
            "",
            f"- Calibration score: `{float(calibration.get('confidence_calibration_score') or 0.0):.1f}`",
            f"- Largest calibration gap: `{float(calibration.get('largest_calibration_gap') or 0.0):.2f}`",
            f"- Graduation confidence ready: `{str(bool(calibration.get('graduation_confidence_ready'))).lower()}`",
            f"- BQ-C4 effectiveness evidence: `{float(bqc4.get('evidence_strength') or 0.0):.2f}`",
            f"- BQ-C5 effectiveness evidence: `{float(bqc5.get('evidence_strength') or 0.0):.2f}`",
            f"- Evidence delta: `{float(comparison.get('effectiveness_evidence_delta') or 0.0):+.2f}`",
            f"- BQ-C4 calibration score: `{float(bqc4.get('confidence_calibration_score') or 0.0):.1f}`",
            f"- BQ-C5 calibration score: `{float(bqc5.get('confidence_calibration_score') or 0.0):.1f}`",
            f"- Calibration score delta: `{float(comparison.get('calibration_score_delta') or 0.0):+.1f}`",
            "",
            "# Graduation Impact",
            "",
            f"- Formal graduation criteria met: `{str(bool(payload.get('formal_graduation_criteria_met'))).lower()}`",
            f"- Missing outcome signal: {payload.get('missing_outcome_signal') or 'none'}",
            "",
            "# Final Recommendation",
            "",
            f"**{recommendation_label}**",
            "",
            str(payload.get("final_graduation_recommendation_rationale") or "No rationale recorded."),
            "",
        ]
    )
    return "\n".join(lines)


def enrich_recurrence_history_with_outcome_validation(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay outcome validation fields."""
    payload = dict(history)
    validation = build_recurrence_outcome_validation(
        recurrence_history=payload,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_remediation_targets=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
        recurrence_trajectory_summary=payload.get("recurrence_trajectory_summary")
        if isinstance(payload.get("recurrence_trajectory_summary"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_maturity=payload.get("recurrence_maturity")
        if isinstance(payload.get("recurrence_maturity"), Mapping)
        else None,
        recurrence_completion=payload.get("recurrence_completion")
        if isinstance(payload.get("recurrence_completion"), Mapping)
        else None,
        recurrence_graduation_audit=payload.get("recurrence_graduation_audit")
        if isinstance(payload.get("recurrence_graduation_audit"), Mapping)
        else None,
        event_log=event_log,
        as_of=as_of,
    )
    payload["recurrence_outcome_validation"] = validation
    payload["outcome_validation_summary"] = validation["outcome_validation_summary"]
    payload["recurrence_confidence_audit"] = validation["recurrence_confidence_audit"]
    payload["recurrence_confidence_calibration_summary"] = validation["recurrence_confidence_calibration_summary"]
    return payload
