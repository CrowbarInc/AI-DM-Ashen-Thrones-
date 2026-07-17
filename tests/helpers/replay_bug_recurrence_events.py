"""Recurrence key derivation, event persistence, and history aggregation foundations.

**Owns (CG-4):** recurrence identity key (``build_recurrence_key``, ``recurrence:v1``),
input status (``ALLOWED_RECURRENCE_STATUSES``), summary status
(``SUMMARY_RECURRENCE_STATUSES``, ``classify_recurrence_status``), event source buckets,
persistence lanes, commit-worthiness policy.

**Consumes:** ``owner_drift_bucket``, ``category``, ``field_path``, ``investigate_first``
from classification rows — all four are key-sensitive.

**Does not own:** trend, forecast, governance, lifecycle, maturity, confidence, graduation,
or outcome taxonomies (see ``replay_bug_recurrence_history.py`` and downstream modules).

Registry: ``docs/audits/CG_recurrence_taxonomy_registry.md``
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_paths import RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH
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
RECURRENCE_PERSISTENCE_LANE_SYNTHETIC_TEST_ARTIFACT = "synthetic_test_artifact_history"
GOLDEN_REPLAY_ARTIFACT_SOURCE_PREFIX = "artifacts/golden_replay/"
DEFAULT_DISALLOWED_ARTIFACT_SOURCE_SUBSTRINGS: tuple[str, ...] = (
    "codex_pytest_tmp",
    "pytest_tmp",
    "/tmp/",
    "\\tmp\\",
)
ALLOWED_RECURRENCE_STATUSES: frozenset[str] = frozenset({"active", "retired"})
SUMMARY_RECURRENCE_STATUSES: frozenset[str] = frozenset({"active", "retired", "watch"})
RECURRENCE_POPULATION_PROTECTED_REPLAY = "protected_replay"
RECURRENCE_POPULATION_SESSION_DIAGNOSTIC = "session_diagnostic"
RECURRENCE_POPULATION_SYNTHETIC_TEST_ARTIFACT = "synthetic_test_artifact"
RECURRENCE_POPULATION_LEGACY_UNIFIED = "legacy_unified"
RECURRENCE_POPULATIONS: frozenset[str] = frozenset(
    {
        RECURRENCE_POPULATION_PROTECTED_REPLAY,
        RECURRENCE_POPULATION_SESSION_DIAGNOSTIC,
        RECURRENCE_POPULATION_SYNTHETIC_TEST_ARTIFACT,
        RECURRENCE_POPULATION_LEGACY_UNIFIED,
    }
)
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
    """Split recurrence events into protected, session, and synthetic/test artifact lanes."""
    active_policy = policy or DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY
    protected_events: list[dict[str, Any]] = []
    session_diagnostic_events: list[dict[str, Any]] = []
    synthetic_test_artifact_events: list[dict[str, Any]] = []
    classifications: list[dict[str, Any]] = []
    for event in events or ():
        if not isinstance(event, Mapping):
            continue
        event_copy = dict(event)
        worthy, reason = is_commit_worthy_recurrence_event(event_copy, policy=active_policy)
        if worthy:
            lane = RECURRENCE_PERSISTENCE_LANE_PROTECTED
        elif reason == "session_event_source":
            lane = RECURRENCE_PERSISTENCE_LANE_SESSION_DIAGNOSTIC
        else:
            lane = RECURRENCE_PERSISTENCE_LANE_SYNTHETIC_TEST_ARTIFACT
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
        elif lane == RECURRENCE_PERSISTENCE_LANE_SESSION_DIAGNOSTIC:
            session_diagnostic_events.append(event_copy)
        else:
            synthetic_test_artifact_events.append(event_copy)
    diagnostic_events = session_diagnostic_events + synthetic_test_artifact_events
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_history": protected_events,
        "session_diagnostic_history": session_diagnostic_events,
        "synthetic_test_artifact_history": synthetic_test_artifact_events,
        "diagnostic_history": diagnostic_events,
        "classifications": classifications,
        "counts": {
            "total": len(classifications),
            "protected_replay_history": len(protected_events),
            "session_diagnostic_history": len(session_diagnostic_events),
            "synthetic_test_artifact_history": len(synthetic_test_artifact_events),
            "diagnostic_history": len(diagnostic_events),
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
        "events_excluded_from_protected_history": classification["counts"]["diagnostic_history"],
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
            "synthetic_test_artifact_history": calculate_synthetic_test_artifact_regression_recurrence_rate(
                event_log,
                policy=active_policy,
            ),
        },
        **build_scoped_recurrence_population_metrics(event_log, policy=active_policy),
    }


def classify_recurrence_event_population(
    event: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> str:
    """Classify one recurrence event into an explicit population taxonomy bucket."""
    worthy, reason = is_commit_worthy_recurrence_event(event, policy=policy)
    if worthy:
        return RECURRENCE_POPULATION_PROTECTED_REPLAY
    if reason == "session_event_source":
        return RECURRENCE_POPULATION_SESSION_DIAGNOSTIC
    return RECURRENCE_POPULATION_SYNTHETIC_TEST_ARTIFACT


def _occurrence_counts_for_event_population(
    events: Sequence[Mapping[str, Any]] | None,
    population: str,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, int]:
    """Return recurrence-key occurrence counts for one population bucket."""
    if population not in RECURRENCE_POPULATIONS - {RECURRENCE_POPULATION_LEGACY_UNIFIED}:
        return {}
    active_policy = policy or DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY
    counts: dict[str, int] = {}
    ordered = sorted(
        [dict(event) for event in events or () if isinstance(event, Mapping)],
        key=lambda event: (
            int(event.get("event_index") or 0),
            str(event.get("recurrence_key") or ""),
        ),
    )
    for event in ordered:
        if population == RECURRENCE_POPULATION_LEGACY_UNIFIED:
            include = True
        else:
            include = classify_recurrence_event_population(event, policy=active_policy) == population
        if not include:
            continue
        key = str(event.get("recurrence_key") or build_recurrence_key(event)).strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    return counts


def _regression_recurrence_rate_from_counts(
    counts: Mapping[str, int],
    *,
    population: str | None = None,
    event_source_filter: str | None = None,
) -> dict[str, Any]:
    """Build a regression recurrence rate payload from precomputed key counts."""
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
    if population is not None:
        payload["population"] = population
    if event_source_filter is not None:
        payload["event_source_filter"] = event_source_filter
    return payload


def calculate_regression_recurrence_rate_for_population(
    event_log_or_history: Mapping[str, Any] | None,
    population: str,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return Regression Recurrence Rate scoped to one recurrence population bucket."""
    if population == RECURRENCE_POPULATION_PROTECTED_REPLAY:
        return calculate_protected_replay_regression_recurrence_rate(
            event_log_or_history,
            policy=policy,
        )
    if population == RECURRENCE_POPULATION_LEGACY_UNIFIED:
        return calculate_legacy_unified_regression_recurrence_rate(event_log_or_history)

    events = _event_log_events(event_log_or_history)
    counts = _occurrence_counts_for_event_population(events, population, policy=policy)
    metric = _regression_recurrence_rate_from_counts(counts, population=population)
    if population == RECURRENCE_POPULATION_SESSION_DIAGNOSTIC:
        metric["event_source_filter"] = DEFAULT_EVENT_SOURCE
    return metric


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


def calculate_session_diagnostic_regression_recurrence_rate(
    event_log_or_history: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return Regression Recurrence Rate for session diagnostic events only."""
    if isinstance(event_log_or_history, Mapping) and isinstance(event_log_or_history.get("events"), list):
        return calculate_regression_recurrence_rate_for_population(
            event_log_or_history,
            RECURRENCE_POPULATION_SESSION_DIAGNOSTIC,
            policy=policy,
        )
    return calculate_regression_recurrence_rate(
        event_log_or_history,
        event_source_filter=DEFAULT_EVENT_SOURCE,
    )


def calculate_synthetic_test_artifact_regression_recurrence_rate(
    event_log_or_history: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return Regression Recurrence Rate for synthetic/test artifact rejects only."""
    return calculate_regression_recurrence_rate_for_population(
        event_log_or_history,
        RECURRENCE_POPULATION_SYNTHETIC_TEST_ARTIFACT,
        policy=policy,
    )


def calculate_legacy_unified_regression_recurrence_rate(
    event_log_or_history: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return legacy unified Regression Recurrence Rate for compatibility comparisons."""
    metric = calculate_regression_recurrence_rate(event_log_or_history)
    metric["population"] = RECURRENCE_POPULATION_LEGACY_UNIFIED
    metric["compatibility_only"] = True
    return metric


def build_recurrence_rate_by_population(
    event_log_or_history: Mapping[str, Any] | None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return grouped recurrence rates with explicit population health semantics."""
    protected_rate = calculate_protected_replay_regression_recurrence_rate(
        event_log_or_history,
        policy=policy,
    )
    session_rate = calculate_session_diagnostic_regression_recurrence_rate(
        event_log_or_history,
        policy=policy,
    )
    synthetic_rate = calculate_synthetic_test_artifact_regression_recurrence_rate(
        event_log_or_history,
        policy=policy,
    )
    legacy_rate = calculate_legacy_unified_regression_recurrence_rate(event_log_or_history)
    return {
        RECURRENCE_POPULATION_PROTECTED_REPLAY: {
            "recurrence_rate": protected_rate,
            "health_metric": True,
        },
        RECURRENCE_POPULATION_SESSION_DIAGNOSTIC: {
            "recurrence_rate": session_rate,
            "health_metric": False,
        },
        RECURRENCE_POPULATION_SYNTHETIC_TEST_ARTIFACT: {
            "recurrence_rate": synthetic_rate,
            "health_metric": False,
        },
        RECURRENCE_POPULATION_LEGACY_UNIFIED: {
            "recurrence_rate": legacy_rate,
            "health_metric": False,
            "compatibility_only": True,
        },
    }


def build_scoped_recurrence_population_metrics(
    protected_log: Mapping[str, Any] | None,
    session_diagnostic_log: Mapping[str, Any] | None = None,
    synthetic_test_artifact_log: Mapping[str, Any] | None = None,
    *,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Return additive scoped recurrence metrics from protected and diagnostic lanes."""
    combined_events = (
        _event_log_events(protected_log)
        + _event_log_events(session_diagnostic_log)
        + _event_log_events(synthetic_test_artifact_log)
    )
    combined_log = {"events": combined_events} if combined_events else empty_recurrence_event_log()
    by_population = build_recurrence_rate_by_population(combined_log, policy=policy)
    protected_rate = calculate_protected_replay_regression_recurrence_rate(protected_log, policy=policy)
    return {
        "protected_replay_regression_recurrence_rate": protected_rate,
        "session_diagnostic_regression_recurrence_rate": by_population[
            RECURRENCE_POPULATION_SESSION_DIAGNOSTIC
        ]["recurrence_rate"],
        "synthetic_test_artifact_regression_recurrence_rate": by_population[
            RECURRENCE_POPULATION_SYNTHETIC_TEST_ARTIFACT
        ]["recurrence_rate"],
        "legacy_unified_regression_recurrence_rate": by_population[
            RECURRENCE_POPULATION_LEGACY_UNIFIED
        ]["recurrence_rate"],
        "recurrence_rate_by_population": {
            **by_population,
            RECURRENCE_POPULATION_PROTECTED_REPLAY: {
                "recurrence_rate": protected_rate,
                "health_metric": True,
            },
        },
    }


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
    scoped_metrics = build_scoped_recurrence_population_metrics(event_log)

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
        **scoped_metrics,
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
    loaded = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": [dict(item) for item in raw["events"] if isinstance(item, Mapping)],
    }
    if bool(raw.get("compatibility_only")):
        loaded["compatibility_only"] = True
    return loaded


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
    synthetic_test_artifact_log: Mapping[str, Any] | None = None,
    event_metadata: Mapping[str, Any] | None = None,
    event_source: str | None = None,
    recorded_at: str | None = None,
    policy: RecurrenceCommitWorthinessPolicy | None = None,
) -> dict[str, Any]:
    """Route projected recurrence events into explicit protected, session, or synthetic lanes."""
    active_policy = policy or DEFAULT_RECURRENCE_COMMIT_WORTHINESS_POLICY
    protected_preserved = [dict(item) for item in _event_log_events(protected_log)]
    session_preserved = [dict(item) for item in _event_log_events(session_diagnostic_log)]
    synthetic_preserved = [dict(item) for item in _event_log_events(synthetic_test_artifact_log)]
    start_index = max(
        _next_event_index(protected_preserved),
        _next_event_index(session_preserved),
        _next_event_index(synthetic_preserved),
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
    synthetic_new: list[dict[str, Any]] = []
    for event in projected:
        worthy, reason = is_commit_worthy_recurrence_event(event, policy=active_policy)
        if worthy:
            lane = RECURRENCE_PERSISTENCE_LANE_PROTECTED
        elif reason == "session_event_source":
            lane = RECURRENCE_PERSISTENCE_LANE_SESSION_DIAGNOSTIC
        else:
            lane = RECURRENCE_PERSISTENCE_LANE_SYNTHETIC_TEST_ARTIFACT
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
        elif lane == RECURRENCE_PERSISTENCE_LANE_SESSION_DIAGNOSTIC:
            session_new.append(event)
        else:
            synthetic_new.append(event)

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
    updated_synthetic = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": synthetic_preserved + synthetic_new,
    }
    updated_compatibility_diagnostic = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "compatibility_only": True,
        "events": updated_session["events"] + updated_synthetic["events"],
    }
    return {
        "protected_log": updated_protected,
        "session_diagnostic_log": updated_session,
        "synthetic_test_artifact_log": updated_synthetic,
        "compatibility_diagnostic_log": updated_compatibility_diagnostic,
        "protected_appended": len(protected_new),
        "session_diagnostic_appended": len(session_new),
        "synthetic_test_artifact_appended": len(synthetic_new),
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
    history.update(build_scoped_recurrence_population_metrics(event_log, policy=policy))
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


