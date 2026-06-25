"""Trend, forecast, portfolio, remediation, governance, and lifecycle analytics."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_paths import RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH
from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS

from tests.helpers.replay_bug_recurrence_events import *  # noqa: F403

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
