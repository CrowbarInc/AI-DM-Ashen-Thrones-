"""Owner drift hotspot aggregation for replay diagnostics (Cycle AR5).

Advisory/reporting only. Consumes existing failure classification rows with
``field_path``, ``owner_drift_bucket``, ``category``, and ``investigate_first``.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from tests.helpers.replay_drift_rows import valid_classification_rows
from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS


def aggregate_field_drift_counts(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> dict[str, int]:
    """Count drift events by ``field_path``."""
    counts: dict[str, int] = {}
    for row in valid_classification_rows(classifications):
        field_path = str(row.get("field_path") or "")
        counts[field_path] = counts.get(field_path, 0) + 1
    return dict(sorted(counts.items()))


def aggregate_investigation_target_counts(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> dict[str, int]:
    """Count drift events by ``investigate_first`` target."""
    counts: dict[str, int] = {}
    for row in valid_classification_rows(classifications):
        target = str(row.get("investigate_first") or "").strip()
        if not target:
            continue
        counts[target] = counts.get(target, 0) + 1
    return dict(sorted(counts.items()))


def aggregate_owner_bucket_by_field(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Count (field_path, owner_drift_bucket) pairs."""
    pair_counts: dict[tuple[str, str], int] = {}
    for row in valid_classification_rows(classifications):
        field_path = str(row.get("field_path") or "")
        bucket = str(row.get("owner_drift_bucket") or "").strip()
        if bucket not in ALLOWED_OWNER_DRIFT_BUCKETS:
            continue
        key = (field_path, bucket)
        pair_counts[key] = pair_counts.get(key, 0) + 1

    rows = [
        {"field": field_path, "owner_drift_bucket": bucket, "count": count}
        for (field_path, bucket), count in pair_counts.items()
    ]
    return sorted(rows, key=lambda item: (-int(item["count"]), str(item["field"]), str(item["owner_drift_bucket"])))


def aggregate_owner_drift_bucket_counts(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> dict[str, int]:
    """Count drift events by ``owner_drift_bucket``."""
    counts = {bucket: 0 for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}
    for row in valid_classification_rows(classifications):
        bucket = str(row.get("owner_drift_bucket") or "").strip()
        if bucket in ALLOWED_OWNER_DRIFT_BUCKETS:
            counts[bucket] += 1
    return {bucket: count for bucket, count in counts.items() if count > 0}


def _rank_counts(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    ranked = sorted(
        ((str(key), int(value)) for key, value in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return [{"name": name, "count": count, "rank": index} for index, (name, count) in enumerate(ranked, start=1)]


def build_hotspot_rankings(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Build ranked hotspot summaries for fields, owners, and investigation targets."""
    field_counts = aggregate_field_drift_counts(classifications)
    investigation_counts = aggregate_investigation_target_counts(classifications)
    owner_bucket_counts = aggregate_owner_drift_bucket_counts(classifications)
    owner_bucket_by_field = aggregate_owner_bucket_by_field(classifications)
    rows = valid_classification_rows(classifications)

    return {
        "total_classifications": len(rows),
        "field_counts": field_counts,
        "investigation_target_counts": investigation_counts,
        "owner_drift_bucket_counts": owner_bucket_counts,
        "owner_bucket_by_field": owner_bucket_by_field,
        "top_drift_fields": _rank_counts(field_counts),
        "top_investigation_targets": _rank_counts(investigation_counts),
        "top_owner_drift_buckets": _rank_counts(owner_bucket_counts),
    }


def render_owner_drift_hotspot_report(
    hotspots: Mapping[str, Any],
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
) -> str:
    """Render advisory owner drift hotspot markdown."""
    lines = [
        "# Owner Drift Hotspot Report",
        "",
        "- Advisory only: `true`",
        "- Report only: `true`",
    ]
    if generated_at:
        lines.append(f"- Generated at: `{generated_at}`")
    if command_used:
        lines.append(f"- Command: `{command_used}`")
    lines.append(f"- Total classifications: `{int(hotspots.get('total_classifications') or 0)}`")
    lines.append("")

    top_fields = hotspots.get("top_drift_fields")
    top_targets = hotspots.get("top_investigation_targets")
    top_buckets = hotspots.get("top_owner_drift_buckets")
    owner_by_field = hotspots.get("owner_bucket_by_field")

    lines.extend(["## Top Drift Fields", ""])
    if isinstance(top_fields, list) and top_fields:
        for row in top_fields:
            if isinstance(row, Mapping):
                trend_direction = row.get("trend_direction")
                if trend_direction:
                    lines.append(f"{row.get('rank')}. {row.get('name')}")
                    lines.append(f"   Count: {row.get('current_count', row.get('count'))}")
                    lines.append(f"   Trend: {trend_direction}")
                else:
                    lines.append(f"{row.get('rank')}. {row.get('name')} ({row.get('count')})")
    else:
        lines.append("No drift fields recorded.")
    lines.append("")

    lines.extend(["## Top Investigation Targets", ""])
    if isinstance(top_targets, list) and top_targets:
        for row in top_targets:
            if isinstance(row, Mapping):
                lines.append(f"{row.get('rank')}. {row.get('name')} ({row.get('count')})")
    else:
        lines.append("No investigation targets recorded.")
    lines.append("")

    lines.extend(["## Top Owner Drift Buckets", ""])
    if isinstance(top_buckets, list) and top_buckets:
        for row in top_buckets:
            if isinstance(row, Mapping):
                lines.append(f"{row.get('rank')}. {row.get('name')} ({row.get('count')})")
    else:
        lines.append("No owner drift buckets recorded.")
    lines.append("")

    lines.extend(["## Owner Drift Buckets By Field", ""])
    if isinstance(owner_by_field, list) and owner_by_field:
        lines.extend(
            [
                "| Field | Owner Drift Bucket | Count |",
                "|---|---|---:|",
            ]
        )
        for row in owner_by_field:
            if isinstance(row, Mapping):
                lines.append(
                    f"| `{row.get('field')}` | `{row.get('owner_drift_bucket')}` | `{row.get('count')}` |"
                )
        lines.append("")
    else:
        lines.extend(["No field/bucket pairings recorded.", ""])

    return "\n".join(lines)
