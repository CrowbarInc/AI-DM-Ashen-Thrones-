"""Longitudinal owner drift aggregation across replay scorecards (Cycle AR4).

Advisory/reporting only. Consumes existing rerun scorecard payloads with
``owner_drift_classifications`` from AR2/AR3; no new telemetry.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS


def _valid_scorecards(scorecards: Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    if not scorecards:
        return []
    valid: list[Mapping[str, Any]] = []
    for scorecard in scorecards:
        if not isinstance(scorecard, Mapping):
            continue
        if scorecard.get("comparison_available") is False:
            continue
        valid.append(scorecard)
    return valid


def _classification_rows(scorecard: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = scorecard.get("owner_drift_classifications")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def aggregate_owner_drift_history(
    scorecards: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Aggregate owner drift bucket counts across multiple rerun scorecards."""
    valid = _valid_scorecards(scorecards)
    owner_bucket_counts = {bucket: 0 for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}
    for scorecard in valid:
        for row in _classification_rows(scorecard):
            bucket = str(row.get("owner_drift_bucket") or "").strip()
            if bucket in ALLOWED_OWNER_DRIFT_BUCKETS:
                owner_bucket_counts[bucket] += 1

    total_events = sum(owner_bucket_counts.values())
    owner_bucket_percentages = {
        bucket: (0.0 if total_events == 0 else round(count * 100.0 / total_events, 1))
        for bucket, count in owner_bucket_counts.items()
    }

    non_zero = {bucket: count for bucket, count in owner_bucket_counts.items() if count > 0}
    if non_zero:
        most_common_bucket = max(non_zero, key=lambda bucket: (non_zero[bucket], bucket))
        least_common_bucket = min(non_zero, key=lambda bucket: (non_zero[bucket], bucket))
    else:
        most_common_bucket = None
        least_common_bucket = None

    return {
        "total_runs": len(valid),
        "total_owner_drift_events": total_events,
        "owner_bucket_counts": owner_bucket_counts,
        "owner_bucket_percentages": owner_bucket_percentages,
        "most_common_bucket": most_common_bucket,
        "least_common_bucket": least_common_bucket,
    }


def build_owner_drift_trend_summary(
    history: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Build ranked trend rows for each owner drift bucket."""
    counts = history.get("owner_bucket_counts")
    if not isinstance(counts, Mapping):
        counts = {}

    total_events = int(history.get("total_owner_drift_events") or 0)
    if total_events <= 0:
        total_events = sum(int(counts.get(bucket) or 0) for bucket in ALLOWED_OWNER_DRIFT_BUCKETS)

    rows: list[dict[str, Any]] = []
    for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS):
        count = int(counts.get(bucket) or 0)
        percentage = 0.0 if total_events == 0 else round(count * 100.0 / total_events, 1)
        rows.append(
            {
                "bucket": bucket,
                "count": count,
                "percentage": percentage,
                "rank": 0,
            }
        )

    ranked = sorted(rows, key=lambda row: (-int(row["count"]), str(row["bucket"])))
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked


def _format_percentage(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "0%"
    if numeric.is_integer():
        return f"{int(numeric)}%"
    return f"{numeric:.1f}%"


def render_owner_drift_longitudinal_report(
    history: Mapping[str, Any],
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
) -> str:
    """Render advisory longitudinal owner drift markdown."""
    lines = [
        "# Owner Drift Longitudinal Report",
        "",
        "- Advisory only: `true`",
        "- Report only: `true`",
    ]
    if generated_at:
        lines.append(f"- Generated at: `{generated_at}`")
    if command_used:
        lines.append(f"- Command: `{command_used}`")
    lines.extend(
        [
            f"- Total runs: `{int(history.get('total_runs') or 0)}`",
            f"- Total owner drift events: `{int(history.get('total_owner_drift_events') or 0)}`",
            "",
        ]
    )

    trend_rows = build_owner_drift_trend_summary(history)
    non_zero_rows = [row for row in trend_rows if int(row.get("count") or 0) > 0]

    lines.extend(["## Owner Drift Trend Summary", ""])
    if not non_zero_rows:
        lines.extend(["No owner drift history recorded.", ""])
    else:
        lines.extend(
            [
                "| Bucket | Count | Percentage |",
                "|---|---:|---:|",
            ]
        )
        for row in sorted(non_zero_rows, key=lambda item: (-int(item["count"]), str(item["bucket"]))):
            lines.append(
                f"| `{row['bucket']}` | `{int(row['count'])}` | {_format_percentage(row['percentage'])} |"
            )
        lines.append("")

    most_common = history.get("most_common_bucket")
    least_common = history.get("least_common_bucket")
    lines.extend(
        [
            "## Highest Concentration",
            "",
            f"`{most_common}`" if most_common else "No owner drift buckets recorded.",
            "",
            "## Lowest Concentration",
            "",
            f"`{least_common}`" if least_common else "No owner drift buckets recorded.",
            "",
        ]
    )
    return "\n".join(lines)
