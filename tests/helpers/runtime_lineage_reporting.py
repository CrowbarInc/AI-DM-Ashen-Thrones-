"""Shared runtime lineage summary surface for reporting consumers (Cycle T4).

Dashboard, golden replay, and scenario-spine paths gather events locally, then
delegate frequency/recurrence aggregation to ``summarize_runtime_lineage_events``.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from game.runtime_lineage_telemetry import normalize_runtime_lineage_events, summarize_runtime_lineage_events


def build_runtime_lineage_summary(events: Any) -> dict[str, Any]:
    """Normalize replay/tool input, then delegate diagnostic-only aggregation."""
    return summarize_runtime_lineage_events(normalize_runtime_lineage_events(events))


def collect_runtime_lineage_events_from_branch_transcripts(
    branch_transcripts: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[Any]:
    """Gather persisted ``meta.runtime_lineage_events`` rows across branch transcripts."""
    events: list[Any] = []
    for branch_id in sorted(branch_transcripts, key=str):
        for row in branch_transcripts[branch_id]:
            meta = row.get("meta") if isinstance(row, Mapping) else None
            raw_events = meta.get("runtime_lineage_events") if isinstance(meta, Mapping) else None
            if not isinstance(raw_events, list):
                continue
            events.extend(raw_events)
    return events


def build_runtime_lineage_summary_from_branch_transcripts(
    branch_transcripts: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Aggregate lineage events collected from scenario-spine branch transcripts."""
    return summarize_runtime_lineage_events(
        collect_runtime_lineage_events_from_branch_transcripts(branch_transcripts)
    )


def _coerce_runtime_lineage_summary(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping) and "total_events" in value:
        return dict(value)
    return build_runtime_lineage_summary(value)


def _top_lineage_frequency_bucket(summary: Mapping[str, Any], bucket: str, *, limit: int = 5) -> str:
    values = summary.get(bucket)
    if not isinstance(values, Mapping) or not values:
        return "_(none)_"
    return "; ".join(
        f"`{key}` ({count})"
        for key, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]
    )


def _recurring_lineage_keys(summary: Mapping[str, Any], *, limit: int = 5) -> str:
    recurring = summary.get("recurring_events")
    if not isinstance(recurring, list) or not recurring:
        return "_(none)_"
    rendered = "; ".join(
        f"`{item.get('recurrence_key')}` ({item.get('count')})"
        for item in recurring[:limit]
        if isinstance(item, Mapping)
    )
    return rendered or "_(none)_"


def runtime_lineage_markdown_lines(
    summary_or_events: Any,
    *,
    profile: str = "dashboard",
) -> list[str]:
    """Render the Runtime Lineage Summary markdown section from a summary or raw events."""
    summary = _coerce_runtime_lineage_summary(summary_or_events)
    if int(summary.get("total_events") or 0) == 0:
        return []

    kinds = summary.get("by_event_kind") if isinstance(summary.get("by_event_kind"), Mapping) else {}
    lines = [
        "",
        "## Runtime Lineage Summary",
        "",
        f"- **Total lineage events:** {summary.get('total_events', 0)}",
        f"- **Fallback selected:** {kinds.get('fallback_selected', 0)}",
        f"- **Speaker repair:** {kinds.get('speaker_repair', 0)}",
        f"- **Mutation:** {kinds.get('mutation', 0)}",
        f"- **Gate outcome:** {kinds.get('gate_outcome', 0)}",
    ]
    if summary.get("first_mutation_owner") or summary.get("first_mutation_family"):
        lines.append(
            "- **First mutation writer:** "
            f"`{summary.get('first_mutation_owner') or '-'}` "
            f"family=`{summary.get('first_mutation_family') or '-'}` "
            f"evidence=`{summary.get('first_mutation_evidence_type') or '-'}` "
            f"inference_used=`{bool(summary.get('first_mutation_inference_used'))}`"
        )
    if profile == "spine_aggregate":
        lines.extend(
            [
                f"- **Top fallback kinds:** {_top_lineage_frequency_bucket(summary, 'fallback_frequency')}",
                f"- **Top fallback authorship sources:** {_top_lineage_frequency_bucket(summary, 'fallback_authorship_frequency')}",
                f"- **Top fallback owner buckets:** {_top_lineage_frequency_bucket(summary, 'fallback_owner_bucket_frequency')}",
                f"- **Top gate paths:** {_top_lineage_frequency_bucket(summary, 'gate_path_frequency')}",
                f"- **Top recurring recurrence keys:** {_recurring_lineage_keys(summary)}",
            ]
        )
    else:
        lines.extend(
            [
                f"- **Top recurring recurrence keys:** {_recurring_lineage_keys(summary)}",
                f"- **Top fallback kinds:** {_top_lineage_frequency_bucket(summary, 'fallback_frequency')}",
                f"- **Top fallback authorship sources:** {_top_lineage_frequency_bucket(summary, 'fallback_authorship_frequency')}",
                f"- **Top fallback owner buckets:** {_top_lineage_frequency_bucket(summary, 'fallback_owner_bucket_frequency')}",
                f"- **Top fallback selection owners:** {_top_lineage_frequency_bucket(summary, 'fallback_selection_owner_frequency')}",
                f"- **Top fallback content owners:** {_top_lineage_frequency_bucket(summary, 'fallback_content_owner_frequency')}",
                f"- **Top repair kinds:** {_top_lineage_frequency_bucket(summary, 'speaker_repair_frequency')}",
                f"- **Top mutation kinds:** {_top_lineage_frequency_bucket(summary, 'mutation_kind_frequency')}",
                f"- **Top gate paths:** {_top_lineage_frequency_bucket(summary, 'gate_path_frequency')}",
            ]
        )
    lines.append("")
    return lines
