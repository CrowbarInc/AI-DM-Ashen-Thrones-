"""Owner drift trend analysis across longitudinal scorecard history (Cycle AR6).

Advisory/reporting only. Compares the latest rerun scorecard to the prior scorecard
using existing ``owner_drift_classifications`` from AR2/AR3/AR4.
"""
from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence

from tests.helpers.replay_drift_hotspots import aggregate_field_drift_counts
from tests.helpers.replay_drift_rows import classification_rows_from_scorecards
from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS, summarize_owner_drift_buckets

TrendDirection = Literal["up", "down", "stable"]


def _valid_scorecard_history(
    history: Sequence[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]]:
    if not history:
        return []
    valid: list[Mapping[str, Any]] = []
    for scorecard in history:
        if not isinstance(scorecard, Mapping):
            continue
        if scorecard.get("comparison_available") is False:
            continue
        valid.append(scorecard)
    return valid


def _trend_direction(delta: int) -> TrendDirection:
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "stable"


def _format_delta(delta: int) -> str:
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def _bucket_counts_for_scorecard(scorecard: Mapping[str, Any]) -> dict[str, int]:
    rows = scorecard.get("owner_drift_classifications")
    if not isinstance(rows, list):
        return {bucket: 0 for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}
    return summarize_owner_drift_buckets(row for row in rows if isinstance(row, Mapping))


def _empty_bucket_trend() -> dict[str, Any]:
    return {"current": 0, "previous": 0, "delta": 0, "direction": "stable"}


def compute_owner_drift_trends(
    history: Sequence[Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Compare owner drift bucket counts: latest scorecard vs prior scorecard."""
    scorecards = _valid_scorecard_history(history)
    zero_counts = {bucket: 0 for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}

    if not scorecards:
        return {bucket: _empty_bucket_trend() for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}

    current_counts = _bucket_counts_for_scorecard(scorecards[-1])
    previous_counts = (
        _bucket_counts_for_scorecard(scorecards[-2]) if len(scorecards) >= 2 else zero_counts
    )

    trends: dict[str, dict[str, Any]] = {}
    for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS):
        current = int(current_counts.get(bucket) or 0)
        previous = int(previous_counts.get(bucket) or 0)
        delta = current - previous
        trends[bucket] = {
            "current": current,
            "previous": previous,
            "delta": delta,
            "direction": _trend_direction(delta),
        }
    return trends


def compute_field_drift_trends(
    history: Sequence[Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Compare field-path drift counts: latest scorecard vs prior scorecard."""
    scorecards = _valid_scorecard_history(history)
    if not scorecards:
        return {}

    current_counts = aggregate_field_drift_counts(
        classification_rows_from_scorecards([scorecards[-1]])
    )
    previous_counts = (
        aggregate_field_drift_counts(classification_rows_from_scorecards([scorecards[-2]]))
        if len(scorecards) >= 2
        else {}
    )

    field_names = sorted(set(current_counts) | set(previous_counts))
    trends: dict[str, dict[str, Any]] = {}
    for field in field_names:
        current = int(current_counts.get(field) or 0)
        previous = int(previous_counts.get(field) or 0)
        delta = current - previous
        trends[field] = {
            "current": current,
            "previous": previous,
            "delta": delta,
            "direction": _trend_direction(delta),
        }
    return trends


def build_owner_bucket_trend_summary(
    trends: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return table rows for all nine owner drift buckets."""
    rows: list[dict[str, Any]] = []
    for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS):
        entry = trends.get(bucket) if isinstance(trends.get(bucket), Mapping) else {}
        delta = int(entry.get("delta") or 0)
        rows.append(
            {
                "bucket": bucket,
                "previous": int(entry.get("previous") or 0),
                "current": int(entry.get("current") or 0),
                "delta": delta,
                "delta_label": _format_delta(delta),
                "direction": str(entry.get("direction") or "stable"),
            }
        )
    return rows


def enrich_hotspots_with_field_trends(
    hotspots: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Attach field trend direction to top hotspot rows."""
    enriched = dict(hotspots)
    field_trends = compute_field_drift_trends(history)
    enriched["field_trends"] = field_trends

    top_fields: list[dict[str, Any]] = []
    for row in hotspots.get("top_drift_fields") or []:
        if not isinstance(row, Mapping):
            continue
        name = str(row.get("name") or "")
        trend = field_trends.get(name, {})
        direction = str(trend.get("direction") or "stable") if isinstance(trend, Mapping) else "stable"
        top_fields.append(
            {
                **dict(row),
                "current_count": int(row.get("count") or 0),
                "trend_direction": direction,
            }
        )
    enriched["top_drift_fields"] = top_fields
    return enriched


def render_owner_drift_trend_report(
    trends: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
) -> str:
    """Render advisory owner drift trend markdown."""
    summary_rows = build_owner_bucket_trend_summary(trends)
    lines = [
        "# Owner Drift Trend Report",
        "",
        "- Advisory only: `true`",
        "- Report only: `true`",
    ]
    if generated_at:
        lines.append(f"- Generated at: `{generated_at}`")
    if command_used:
        lines.append(f"- Command: `{command_used}`")
    lines.append("")

    lines.extend(
        [
            "## Drift Trend Summary",
            "",
            "| Bucket | Previous | Current | Delta | Direction |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in summary_rows:
        lines.append(
            f"| `{row['bucket']}` | `{row['previous']}` | `{row['current']}` | "
            f"{row['delta_label']} | `{row['direction']}` |"
        )
    lines.append("")

    improving = [row for row in summary_rows if row["direction"] == "down"]
    worsening = [row for row in summary_rows if row["direction"] == "up"]
    stable = [row for row in summary_rows if row["direction"] == "stable"]

    lines.extend(["## Improving Areas", ""])
    if improving:
        for row in improving:
            lines.append(f"- `{row['bucket']}` ({row['delta_label']})")
    else:
        lines.append("No improving owner drift buckets in the latest comparison.")
    lines.append("")

    lines.extend(["## Worsening Areas", ""])
    if worsening:
        for row in worsening:
            lines.append(f"- `{row['bucket']}` ({row['delta_label']})")
    else:
        lines.append("No worsening owner drift buckets in the latest comparison.")
    lines.append("")

    lines.extend(["## Stable Areas", ""])
    if stable:
        for row in stable:
            lines.append(f"- `{row['bucket']}`")
    else:
        lines.append("No stable owner drift buckets in the latest comparison.")
    lines.append("")

    return "\n".join(lines)


def build_trend_payload(
    history: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Build JSON-serializable trend payload from scorecard history."""
    trends = compute_owner_drift_trends(history)
    return {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        "scorecard_runs_compared": min(len(_valid_scorecard_history(history)), 2),
        "owner_drift_trends": trends,
        "owner_bucket_trend_summary": build_owner_bucket_trend_summary(trends),
        "field_drift_trends": compute_field_drift_trends(history),
    }
