"""Owner drift risk prioritization for replay diagnostics (Cycle AR7).

Advisory/reporting only. Converts existing drift observations, trends, and field
source metadata into prioritized replay risk signals without changing counts.
"""
from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence

from tests.failure_classification_contract import CLASSIFIER_EVIDENCE_EXTENSION_FIELDS
from tests.helpers.golden_replay_projection import protected_observation_field_paths
from tests.helpers.replay_drift_hotspots import (
    aggregate_field_drift_counts,
    aggregate_investigation_target_counts,
    aggregate_owner_drift_bucket_counts,
    classification_rows_from_scorecards,
)
from tests.helpers.replay_drift_taxonomy import (
    aggregate_long_session_stability_classifications,
    build_long_session_stability_history,
    build_stability_hotspots,
    render_stability_hotspots_markdown_lines,
    render_stability_trends_markdown_lines,
    stability_trend_rows_from_history,
)
from tests.helpers.replay_drift_trends import compute_field_drift_trends, compute_owner_drift_trends

RiskLevel = Literal["low", "medium", "high"]
FieldSource = Literal["protected", "supporting", "advisory"]
TrendDirection = Literal["up", "down", "stable"]

REPEATED_OCCURRENCE_THRESHOLD = 2
FREQUENT_SUPPORTING_THRESHOLD = 2

PROTECTED_FIELD_PATHS: frozenset[str] = frozenset(protected_observation_field_paths())
SUPPORTING_FIELD_PATHS: frozenset[str] = frozenset(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS)

PROTECTED_OWNER_BUCKETS: frozenset[str] = frozenset(
    {
        "route_drift",
        "speaker_drift",
        "fallback_drift",
        "ownership_drift",
    }
)
SUPPORTING_OWNER_BUCKETS: frozenset[str] = frozenset(
    {
        "emission_drift",
        "semantic_drift",
        "lineage_drift",
        "projection_drift",
    }
)

_SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

_RISK_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


def classify_field_source(field_path: str) -> FieldSource:
    """Map a replay field path to protected, supporting, or advisory source tier."""
    path = str(field_path or "").strip()
    if path in PROTECTED_FIELD_PATHS:
        return "protected"
    if path in SUPPORTING_FIELD_PATHS:
        return "supporting"
    return "advisory"


def classify_owner_bucket_source(owner_drift_bucket: str) -> FieldSource:
    """Map an owner drift bucket to protected, supporting, or advisory source tier."""
    bucket = str(owner_drift_bucket or "").strip()
    if bucket in PROTECTED_OWNER_BUCKETS:
        return "protected"
    if bucket in SUPPORTING_OWNER_BUCKETS:
        return "supporting"
    return "advisory"


def _normalize_trend(value: Any) -> TrendDirection:
    trend = str(value or "stable").strip()
    if trend in {"up", "down", "stable"}:
        return trend  # type: ignore[return-value]
    return "stable"


def _normalize_frequency(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def score_drift_risk(
    *,
    owner_drift_bucket: str = "",
    field_path: str = "",
    category: str = "",
    severity: str = "",
    field_source: FieldSource = "advisory",
    longitudinal_frequency: int = 0,
    trend_direction: TrendDirection | str = "stable",
) -> RiskLevel:
    """Score one drift risk signal deterministically."""
    _ = owner_drift_bucket, field_path, category, severity
    freq = _normalize_frequency(longitudinal_frequency)
    trend = _normalize_trend(trend_direction)
    source = field_source if field_source in {"protected", "supporting", "advisory"} else "advisory"

    if source == "protected" and trend == "up" and freq >= REPEATED_OCCURRENCE_THRESHOLD:
        return "high"

    if source == "protected" and trend == "stable":
        return "medium"

    if source == "supporting" and freq >= FREQUENT_SUPPORTING_THRESHOLD:
        return "medium"

    if source == "advisory":
        return "low"

    if freq <= 1 and trend != "up":
        return "low"

    if trend == "down":
        return "low"

    if source == "protected" and trend == "up":
        return "medium"

    if source == "supporting":
        return "low"

    return "low"


def _valid_classification_rows(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]]:
    if not classifications:
        return []
    rows: list[Mapping[str, Any]] = []
    for row in classifications:
        if not isinstance(row, Mapping):
            continue
        field_path = str(row.get("field_path") or "").strip()
        if not field_path:
            continue
        rows.append(row)
    return rows


def _dominant_value(rows: Sequence[Mapping[str, Any]], key: str) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "").strip()
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return ""
    return max(counts, key=lambda item: (counts[item], item))


def _max_severity(rows: Sequence[Mapping[str, Any]]) -> str:
    best = "low"
    best_rank = _SEVERITY_RANK[best]
    for row in rows:
        severity = str(row.get("severity") or "low").strip()
        rank = _SEVERITY_RANK.get(severity, _SEVERITY_RANK["low"])
        if rank < best_rank:
            best = severity
            best_rank = rank
    return best


def _risk_signal_rows_for_fields(
    classifications: Sequence[Mapping[str, Any]],
    field_trends: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = _valid_classification_rows(classifications)
    field_counts = aggregate_field_drift_counts(rows)
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        field_path = str(row.get("field_path") or "")
        grouped.setdefault(field_path, []).append(row)

    signals: list[dict[str, Any]] = []
    for field_path in sorted(field_counts):
        field_rows = grouped.get(field_path, [])
        trend = field_trends.get(field_path, {})
        direction = _normalize_trend(trend.get("direction") if isinstance(trend, Mapping) else "stable")
        frequency = int(field_counts[field_path])
        source = classify_field_source(field_path)
        signal = {
            "item": field_path,
            "item_kind": "field",
            "owner_drift_bucket": _dominant_value(field_rows, "owner_drift_bucket"),
            "field_path": field_path,
            "category": _dominant_value(field_rows, "category"),
            "severity": _max_severity(field_rows),
            "field_source": source,
            "longitudinal_frequency": frequency,
            "trend_direction": direction,
        }
        signal["risk_level"] = score_drift_risk(
            owner_drift_bucket=str(signal["owner_drift_bucket"]),
            field_path=field_path,
            category=str(signal["category"]),
            severity=str(signal["severity"]),
            field_source=source,
            longitudinal_frequency=frequency,
            trend_direction=direction,
        )
        signals.append(signal)
    return signals


def _risk_signal_rows_for_owners(
    classifications: Sequence[Mapping[str, Any]],
    bucket_trends: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = _valid_classification_rows(classifications)
    bucket_counts = aggregate_owner_drift_bucket_counts(rows)
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        bucket = str(row.get("owner_drift_bucket") or "").strip()
        if not bucket:
            continue
        grouped.setdefault(bucket, []).append(row)

    signals: list[dict[str, Any]] = []
    for bucket in sorted(bucket_counts):
        bucket_rows = grouped.get(bucket, [])
        trend = bucket_trends.get(bucket, {})
        direction = _normalize_trend(trend.get("direction") if isinstance(trend, Mapping) else "stable")
        frequency = int(bucket_counts[bucket])
        source = classify_owner_bucket_source(bucket)
        signal = {
            "item": bucket,
            "item_kind": "owner",
            "owner_drift_bucket": bucket,
            "field_path": _dominant_value(bucket_rows, "field_path"),
            "category": _dominant_value(bucket_rows, "category"),
            "severity": _max_severity(bucket_rows),
            "field_source": source,
            "longitudinal_frequency": frequency,
            "trend_direction": direction,
        }
        signal["risk_level"] = score_drift_risk(
            owner_drift_bucket=bucket,
            field_path=str(signal["field_path"]),
            category=str(signal["category"]),
            severity=str(signal["severity"]),
            field_source=source,
            longitudinal_frequency=frequency,
            trend_direction=direction,
        )
        signals.append(signal)
    return signals


def _risk_signal_rows_for_investigation_targets(
    classifications: Sequence[Mapping[str, Any]],
    field_trends: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = _valid_classification_rows(classifications)
    target_counts = aggregate_investigation_target_counts(rows)
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        target = str(row.get("investigate_first") or "").strip()
        if not target:
            continue
        grouped.setdefault(target, []).append(row)

    signals: list[dict[str, Any]] = []
    for target in sorted(target_counts):
        target_rows = grouped.get(target, [])
        dominant_field = _dominant_value(target_rows, "field_path")
        trend = field_trends.get(dominant_field, {})
        direction = _normalize_trend(trend.get("direction") if isinstance(trend, Mapping) else "stable")
        frequency = int(target_counts[target])
        source = classify_field_source(dominant_field)
        signal = {
            "item": target,
            "item_kind": "investigation_target",
            "owner_drift_bucket": _dominant_value(target_rows, "owner_drift_bucket"),
            "field_path": dominant_field,
            "category": _dominant_value(target_rows, "category"),
            "severity": _max_severity(target_rows),
            "field_source": source,
            "longitudinal_frequency": frequency,
            "trend_direction": direction,
        }
        signal["risk_level"] = score_drift_risk(
            owner_drift_bucket=str(signal["owner_drift_bucket"]),
            field_path=dominant_field,
            category=str(signal["category"]),
            severity=str(signal["severity"]),
            field_source=source,
            longitudinal_frequency=frequency,
            trend_direction=direction,
        )
        signals.append(signal)
    return signals


def _rank_risk_items(signals: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        signals,
        key=lambda row: (
            _RISK_RANK.get(str(row.get("risk_level") or "low"), 2),
            -_normalize_frequency(row.get("longitudinal_frequency")),
            str(row.get("item") or ""),
        ),
    )
    ranked: list[dict[str, Any]] = []
    for index, row in enumerate(ordered, start=1):
        ranked.append(
            {
                "rank": index,
                "item": str(row.get("item") or ""),
                "risk": str(row.get("risk_level") or "low"),
            }
        )
    return ranked


def _group_signals_by_risk(signals: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {"high": [], "medium": [], "low": []}
    for row in signals:
        level = str(row.get("risk_level") or "low")
        if level not in grouped:
            level = "low"
        grouped[level].append(dict(row))
    for level in grouped:
        grouped[level] = sorted(
            grouped[level],
            key=lambda row: (
                -_normalize_frequency(row.get("longitudinal_frequency")),
                str(row.get("item") or ""),
            ),
        )
    return grouped


def build_risk_rankings(
    classifications: Sequence[Mapping[str, Any]] | None,
    *,
    scorecard_history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build ranked replay drift risk summaries for fields, owners, and targets."""
    rows = list(classifications or [])
    history = list(scorecard_history or [])
    field_trends = compute_field_drift_trends(history)
    bucket_trends = compute_owner_drift_trends(history)

    field_signals = _risk_signal_rows_for_fields(rows, field_trends)
    owner_signals = _risk_signal_rows_for_owners(rows, bucket_trends)
    target_signals = _risk_signal_rows_for_investigation_targets(rows, field_trends)
    all_signals = field_signals + owner_signals + target_signals

    recommended = _rank_risk_items(target_signals)
    if not recommended:
        recommended = _rank_risk_items(field_signals)

    return {
        "total_signals": len(all_signals),
        "risk_signals": all_signals,
        "risk_by_level": _group_signals_by_risk(all_signals),
        "top_risk_fields": _rank_risk_items(field_signals),
        "top_risk_owners": _rank_risk_items(owner_signals),
        "top_risk_investigation_targets": _rank_risk_items(target_signals),
        "recommended_investigation_order": recommended,
    }


def build_risk_payload(
    classifications: Sequence[Mapping[str, Any]] | None,
    *,
    scorecard_history: Sequence[Mapping[str, Any]] | None = None,
    stability_scorecards: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build JSON-serializable owner drift risk payload."""
    rankings = build_risk_rankings(classifications, scorecard_history=scorecard_history)
    payload = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        **rankings,
    }
    return enrich_risk_payload_with_stability_ownership(payload, stability_scorecards)


def _stability_bucket_risk_level(bucket: str, frequency: int) -> RiskLevel:
    if frequency >= 3:
        return "high"
    if frequency >= REPEATED_OCCURRENCE_THRESHOLD:
        return "medium"
    if frequency >= 1 and bucket in PROTECTED_OWNER_BUCKETS:
        return "low"
    return "low"


def enrich_risk_payload_with_stability_ownership(
    payload: Mapping[str, Any],
    stability_scorecards: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Add supplementary stability-ownership risk fields without changing drift rankings."""
    enriched = dict(payload)
    aggregation = aggregate_long_session_stability_classifications(stability_scorecards)
    bucket_frequencies = (
        aggregation.get("bucket_frequencies")
        if isinstance(aggregation.get("bucket_frequencies"), Mapping)
        else {}
    )
    status_counts = (
        aggregation.get("stability_status_counts")
        if isinstance(aggregation.get("stability_status_counts"), Mapping)
        else {}
    )

    stability_risk_signals: list[dict[str, Any]] = []
    for bucket in ("fallback_drift", "speaker_drift", "route_drift"):
        frequency = _normalize_frequency(bucket_frequencies.get(bucket))
        if frequency < REPEATED_OCCURRENCE_THRESHOLD:
            continue
        stability_risk_signals.append(
            {
                "signal": f"recurring_{bucket}",
                "owner_drift_bucket": bucket,
                "risk_level": _stability_bucket_risk_level(bucket, frequency),
                "longitudinal_frequency": frequency,
                "reason": f"{bucket} observed {frequency} time(s) across long-session stability scorecards",
                "source": "stability_ownership",
            }
        )

    degraded_count = _normalize_frequency(status_counts.get("degraded"))
    if degraded_count > 0:
        stability_risk_signals.append(
            {
                "signal": "degraded_stability_status",
                "owner_drift_bucket": "semantic_drift",
                "risk_level": "high" if degraded_count >= REPEATED_OCCURRENCE_THRESHOLD else "medium",
                "longitudinal_frequency": degraded_count,
                "reason": f"degraded stability status observed in {degraded_count} long-session scorecard(s)",
                "source": "stability_ownership",
            }
        )

    watch_count = _normalize_frequency(status_counts.get("watch"))
    if watch_count >= REPEATED_OCCURRENCE_THRESHOLD:
        stability_risk_signals.append(
            {
                "signal": "watch_stability_status",
                "owner_drift_bucket": "replay_drift_unclassified",
                "risk_level": "medium",
                "longitudinal_frequency": watch_count,
                "reason": f"watch stability status observed in {watch_count} long-session scorecard(s)",
                "source": "stability_ownership",
            }
        )

    stability_risk_signals.sort(
        key=lambda row: (
            _RISK_RANK.get(str(row.get("risk_level") or "low"), 2),
            -_normalize_frequency(row.get("longitudinal_frequency")),
            str(row.get("signal") or ""),
        )
    )

    history = build_long_session_stability_history(stability_scorecards)
    trend_rows = stability_trend_rows_from_history(history)
    stability_trend_signals = _stability_trend_risk_signals(history, trend_rows)

    stability_hotspots = build_stability_hotspots(stability_scorecards)

    enriched["stability_ownership"] = {
        "report_only": True,
        "advisory_only": True,
        "aggregation": aggregation,
        "stability_risk_signals": stability_risk_signals,
        "history": history,
        "stability_trend_rows": trend_rows,
        "stability_trend_signals": stability_trend_signals,
        "stability_hotspots": stability_hotspots,
    }
    return enriched


def _stability_trend_risk_signals(
    history: Mapping[str, Any],
    trend_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build supplementary stability trend signals without changing drift rankings."""
    trend_summary = history.get("trend_summary") if isinstance(history.get("trend_summary"), Mapping) else {}
    if not trend_summary.get("comparison_available"):
        return []

    signals: list[dict[str, Any]] = []
    for row in trend_rows:
        if not isinstance(row, Mapping):
            continue
        bucket = str(row.get("owner_drift_bucket") or "")
        trend = str(row.get("trend") or "insufficient_data")
        if trend != "worsening":
            continue
        if bucket in {"fallback_drift", "speaker_drift", "route_drift", "semantic_drift"}:
            signals.append(
                {
                    "signal": f"worsening_{bucket}",
                    "owner_drift_bucket": bucket,
                    "risk_level": "high" if int(row.get("delta") or 0) >= 2 else "medium",
                    "longitudinal_frequency": int(row.get("current_count") or 0),
                    "reason": (
                        f"{bucket} increased from {int(row.get('previous_count') or 0)} "
                        f"to {int(row.get('current_count') or 0)} across stability scorecard generations"
                    ),
                    "source": "stability_trends",
                    "trend": trend,
                    "delta": int(row.get("delta") or 0),
                }
            )
        elif bucket == "overall_stability":
            signals.append(
                {
                    "signal": "worsening_overall_stability",
                    "owner_drift_bucket": "semantic_drift",
                    "risk_level": "high",
                    "longitudinal_frequency": 1,
                    "reason": "overall long-session stability trend is worsening",
                    "source": "stability_trends",
                    "trend": trend,
                    "delta": 0,
                }
            )
        elif bucket == "stability_status:degraded" and int(row.get("current_count") or 0) == 1:
            signals.append(
                {
                    "signal": "repeated_degraded_stability_status",
                    "owner_drift_bucket": "semantic_drift",
                    "risk_level": "high",
                    "longitudinal_frequency": 1,
                    "reason": "latest long-session stability scorecard is degraded after a non-degraded prior run",
                    "source": "stability_trends",
                    "trend": trend,
                    "delta": int(row.get("delta") or 0),
                }
            )

    signals.sort(
        key=lambda row: (
            _RISK_RANK.get(str(row.get("risk_level") or "low"), 2),
            -_normalize_frequency(row.get("longitudinal_frequency")),
            str(row.get("signal") or ""),
        )
    )
    return signals


def _risk_table_lines(title: str, ranked_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not ranked_rows:
        lines.append("No drift risk signals recorded.")
        lines.append("")
        return lines
    lines.extend(
        [
            "| Rank | Item | Risk |",
            "|---:|---|---|",
        ]
    )
    for row in ranked_rows:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| {int(row.get('rank') or 0)} | `{row.get('item')}` | `{row.get('risk')}` |"
        )
    lines.append("")
    return lines


def _risk_section_lines(title: str, signals: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not signals:
        lines.append("No drift risk signals in this band.")
        lines.append("")
        return lines
    for row in signals:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('item')}` "
            f"(source=`{row.get('field_source')}`, "
            f"frequency=`{int(row.get('longitudinal_frequency') or 0)}`, "
            f"trend=`{row.get('trend_direction')}`)"
        )
    lines.append("")
    return lines


def render_owner_drift_risk_report(
    payload: Mapping[str, Any],
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
) -> str:
    """Render advisory owner drift risk markdown."""
    lines = [
        "# Owner Drift Risk Report",
        "",
        "- Advisory only: `true`",
        "- Report only: `true`",
    ]
    if generated_at:
        lines.append(f"- Generated at: `{generated_at}`")
    if command_used:
        lines.append(f"- Command: `{command_used}`")
    lines.append(f"- Total risk signals: `{int(payload.get('total_signals') or 0)}`")
    lines.append("")

    risk_by_level = payload.get("risk_by_level") if isinstance(payload.get("risk_by_level"), Mapping) else {}
    lines.extend(_risk_section_lines("High Risk Drift", risk_by_level.get("high") or []))
    lines.extend(_risk_section_lines("Medium Risk Drift", risk_by_level.get("medium") or []))
    lines.extend(_risk_section_lines("Low Risk Drift", risk_by_level.get("low") or []))

    lines.extend(_risk_table_lines("Top Risk Fields", payload.get("top_risk_fields") or []))
    lines.extend(_risk_table_lines("Top Risk Owners", payload.get("top_risk_owners") or []))
    lines.extend(
        _risk_table_lines(
            "Top Risk Investigation Targets",
            payload.get("top_risk_investigation_targets") or [],
        )
    )
    lines.extend(
        _risk_table_lines(
            "Recommended Investigation Order",
            payload.get("recommended_investigation_order") or [],
        )
    )
    lines.extend(_stability_ownership_risk_report_lines(payload))
    return "\n".join(lines)


def _stability_ownership_risk_report_lines(payload: Mapping[str, Any]) -> list[str]:
    stability = payload.get("stability_ownership") if isinstance(payload.get("stability_ownership"), Mapping) else {}
    if not stability:
        return []
    lines = ["## Stability Ownership", ""]
    aggregation = stability.get("aggregation") if isinstance(stability.get("aggregation"), Mapping) else {}
    status_counts = aggregation.get("stability_status_counts") if isinstance(aggregation.get("stability_status_counts"), Mapping) else {}
    bucket_frequencies = aggregation.get("bucket_frequencies") if isinstance(aggregation.get("bucket_frequencies"), Mapping) else {}
    classification_rows = aggregation.get("classification_rows") if isinstance(aggregation.get("classification_rows"), list) else []

    lines.append(f"- Stability scorecards aggregated: `{int(aggregation.get('total_scorecards') or 0)}`")
    lines.append(f"- Stability status counts: `{dict(status_counts)}`")
    lines.append(f"- Owner bucket frequencies: `{dict(bucket_frequencies)}`")
    lines.append("")

    signals = stability.get("stability_risk_signals")
    if isinstance(signals, list) and signals:
        lines.extend(["### Stability Risk Signals", ""])
        for row in signals:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"- `{row.get('signal')}` "
                f"bucket=`{row.get('owner_drift_bucket')}` "
                f"risk=`{row.get('risk_level')}` "
                f"frequency=`{int(row.get('longitudinal_frequency') or 0)}` "
                f"— {row.get('reason')}"
            )
        lines.append("")

    if not classification_rows:
        lines.extend(["No stability ownership classifications.", ""])
    else:
        lines.extend(
            [
                "### Stability Ownership Classifications",
                "",
                "| Scenario | Signal | Owner Drift Bucket | Stability Status | Severity | Reason |",
                "|---|---|---|---|---|---|",
            ]
        )
        for row in classification_rows:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row.get('scenario_id')}`",
                        f"`{row.get('signal')}`",
                        f"`{row.get('owner_drift_bucket')}`",
                        f"`{row.get('stability_status')}`",
                        f"`{row.get('severity_hint')}`",
                        str(row.get("reason") or ""),
                    ]
                )
                + " |"
            )
        lines.append("")

    history = stability.get("history") if isinstance(stability.get("history"), Mapping) else {}
    trend_rows = stability.get("stability_trend_rows")
    lines.extend(
        render_stability_trends_markdown_lines(
            history=history,
            trend_rows=trend_rows if isinstance(trend_rows, list) else None,
        )
    )

    trend_signals = stability.get("stability_trend_signals")
    if isinstance(trend_signals, list) and trend_signals:
        lines.extend(["### Stability Trend Signals", ""])
        for row in trend_signals:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"- `{row.get('signal')}` "
                f"bucket=`{row.get('owner_drift_bucket')}` "
                f"risk=`{row.get('risk_level')}` "
                f"trend=`{row.get('trend')}` "
                f"— {row.get('reason')}"
            )
        lines.append("")

    stability_hotspots = stability.get("stability_hotspots")
    hotspot_rows = (
        stability_hotspots.get("hotspot_rows")
        if isinstance(stability_hotspots, Mapping)
        else None
    )
    lines.extend(render_stability_hotspots_markdown_lines(hotspot_rows if isinstance(hotspot_rows, list) else None))

    return lines


def classifications_for_risk_analysis(
    classifications: Sequence[Mapping[str, Any]] | None,
    *,
    scorecard_history: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Normalize classification rows for risk analysis, including scorecard expansion."""
    rows: list[dict[str, Any]] = []
    if classifications:
        rows.extend(dict(row) for row in classifications if isinstance(row, Mapping))
    if scorecard_history:
        rows.extend(classification_rows_from_scorecards(scorecard_history))
    return rows
