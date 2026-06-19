#!/usr/bin/env python3
"""Build advisory fallback-incidence reports from recorded turn artifacts.

This tool is read-only. It consumes finalized runtime-lineage and final-emission
metadata; it does not execute or alter fallback selection, replay scoring, or
player-facing emission behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.runtime_lineage_telemetry import normalize_runtime_lineage_events  # noqa: E402

SCHEMA_VERSION = 1
UNKNOWN = "unknown"

FREQUENCY_FIELDS = (
    "fallback_kind",
    "diegetic_family",
    "realization_family",
    "observed_family",
    "event_owner",
    "fallback_owner_bucket",
    "fallback_selection_owner",
    "fallback_content_owner",
    "fallback_authorship_source",
    "final_route",
    "gate_path",
)

CROSS_TAB_FIELDS = (
    "route_kind_x_fallback_kind",
    "route_kind_x_fallback_owner_bucket",
    "route_kind_x_final_route",
    "final_route_x_fallback_kind",
)

COVERAGE_FIELDS = (
    "turns_with_runtime_lineage_events",
    "turns_with_final_emission_meta",
    "fallback_events_with_owner_bucket",
    "fallback_events_with_selection_owner",
    "fallback_events_with_content_owner",
    "fallback_events_with_diegetic_family",
    "fallback_events_with_realization_family",
    "fallback_events_with_observed_family",
    "fallback_events_with_known_route",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _lookup_path(value: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = value
    for part in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _token(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _first_token(*values: Any) -> str | None:
    for value in values:
        normalized = _token(value)
        if normalized is not None:
            return normalized
    return None


def _turn_meta(turn: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(turn.get("meta"))


def _final_emission_meta(turn: Mapping[str, Any]) -> tuple[Mapping[str, Any], bool]:
    meta = _turn_meta(turn)
    candidates = (
        meta.get("final_emission_meta"),
        turn.get("final_emission_meta"),
        _lookup_path(turn, ("metadata", "final_emission_meta")),
    )
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            return candidate, True
    return {}, False


def _runtime_lineage_source(turn: Mapping[str, Any]) -> tuple[Any, bool]:
    meta = _turn_meta(turn)
    candidates = (
        (meta, "runtime_lineage_events"),
        (turn, "runtime_lineage_events"),
        (_mapping(meta.get("observational_telemetry_bundle")), "fem_runtime_lineage_events"),
        (_mapping(meta.get("telemetry_bundle")), "fem_runtime_lineage_events"),
    )
    for owner, key in candidates:
        if key in owner:
            return owner.get(key), isinstance(owner.get(key), list)
    return None, False


def _route_kind(turn: Mapping[str, Any]) -> str:
    meta = _turn_meta(turn)
    route = _first_token(
        turn.get("route_kind"),
        meta.get("route_kind"),
        _lookup_path(turn, ("observed", "route_kind")),
        _lookup_path(turn, ("trace", "social_contract_trace", "route_selected")),
        _lookup_path(turn, ("trace", "turn_trace", "social_contract_trace", "route_selected")),
        _lookup_path(meta, ("trace", "social_contract_trace", "route_selected")),
        _lookup_path(meta, ("trace", "turn_trace", "social_contract_trace", "route_selected")),
        _lookup_path(turn, ("resolution", "kind")),
        turn.get("resolution_kind"),
        meta.get("resolution_kind"),
    )
    return route or UNKNOWN


def _observed_family(turn: Mapping[str, Any], fem: Mapping[str, Any]) -> str | None:
    meta = _turn_meta(turn)
    return _first_token(
        turn.get("observed_family"),
        turn.get("fallback_family"),
        meta.get("observed_family"),
        meta.get("fallback_family"),
        _lookup_path(turn, ("observed", "fallback_family")),
        fem.get("fallback_family"),
    )


def _increment(bucket: dict[str, int], value: str | None) -> None:
    if value is not None:
        bucket[value] = bucket.get(value, 0) + 1


def _increment_cross_tab(bucket: dict[str, dict[str, int]], row: str, column: str | None) -> None:
    if column is None:
        return
    row_bucket = bucket.setdefault(row, {})
    row_bucket[column] = row_bucket.get(column, 0) + 1


def _sorted_counts(values: Mapping[str, int]) -> dict[str, int]:
    return {key: int(values[key]) for key in sorted(values)}


def _sorted_cross_tab(values: Mapping[str, Mapping[str, int]]) -> dict[str, dict[str, int]]:
    return {row: _sorted_counts(values[row]) for row in sorted(values)}


def build_fallback_incidence_report(turns: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate finalized fallback evidence without mutating input turns."""
    frequency: dict[str, dict[str, int]] = {field: {} for field in FREQUENCY_FIELDS}
    cross_tabs: dict[str, dict[str, dict[str, int]]] = {field: {} for field in CROSS_TAB_FIELDS}
    coverage = {field: 0 for field in COVERAGE_FIELDS}
    route_turn_count: dict[str, int] = {}
    route_fallback_turn_count: dict[str, int] = {}

    eligible_turn_count = 0
    fallback_turn_count = 0
    fallback_event_count = 0

    for turn in turns:
        if not isinstance(turn, Mapping):
            continue
        eligible_turn_count += 1
        route_kind = _route_kind(turn)
        _increment(route_turn_count, route_kind)

        fem, has_fem = _final_emission_meta(turn)
        if has_fem:
            coverage["turns_with_final_emission_meta"] += 1

        raw_events, has_lineage = _runtime_lineage_source(turn)
        if has_lineage:
            coverage["turns_with_runtime_lineage_events"] += 1
        recorded_runtime_events = (
            [
                event
                for event in raw_events
                if isinstance(event, Mapping) and event.get("event_type") == "runtime_lineage"
            ]
            if isinstance(raw_events, list)
            else []
        )
        events = normalize_runtime_lineage_events(recorded_runtime_events)
        fallback_events = [
            event
            for event in events
            if event.get("event_type") == "runtime_lineage" and event.get("event_kind") == "fallback_selected"
        ]
        if fallback_events:
            fallback_turn_count += 1
            _increment(route_fallback_turn_count, route_kind)

        final_route = _first_token(fem.get("final_route")) or UNKNOWN
        diegetic_family = _first_token(fem.get("fallback_family_used"))
        realization_family = _first_token(fem.get("realization_fallback_family"))
        observed_family = _observed_family(turn, fem)

        for event in fallback_events:
            fallback_event_count += 1
            fallback_kind = _first_token(event.get("fallback_kind")) or UNKNOWN
            event_owner = _first_token(event.get("owner"))
            owner_bucket = _first_token(event.get("fallback_owner_bucket"))
            selection_owner = _first_token(event.get("fallback_selection_owner"))
            content_owner = _first_token(event.get("fallback_content_owner"))
            authorship_source = _first_token(event.get("fallback_authorship_source"))
            gate_path = _first_token(event.get("gate_path"))

            dimensions = {
                "fallback_kind": fallback_kind,
                "diegetic_family": diegetic_family,
                "realization_family": realization_family,
                "observed_family": observed_family,
                "event_owner": event_owner,
                "fallback_owner_bucket": owner_bucket,
                "fallback_selection_owner": selection_owner,
                "fallback_content_owner": content_owner,
                "fallback_authorship_source": authorship_source,
                "final_route": final_route,
                "gate_path": gate_path,
            }
            for field, value in dimensions.items():
                _increment(frequency[field], value)

            _increment_cross_tab(cross_tabs["route_kind_x_fallback_kind"], route_kind, fallback_kind)
            _increment_cross_tab(cross_tabs["route_kind_x_fallback_owner_bucket"], route_kind, owner_bucket)
            _increment_cross_tab(cross_tabs["route_kind_x_final_route"], route_kind, final_route)
            _increment_cross_tab(cross_tabs["final_route_x_fallback_kind"], final_route, fallback_kind)

            coverage["fallback_events_with_owner_bucket"] += int(owner_bucket is not None)
            coverage["fallback_events_with_selection_owner"] += int(selection_owner is not None)
            coverage["fallback_events_with_content_owner"] += int(content_owner is not None)
            coverage["fallback_events_with_diegetic_family"] += int(diegetic_family is not None)
            coverage["fallback_events_with_realization_family"] += int(realization_family is not None)
            coverage["fallback_events_with_observed_family"] += int(observed_family is not None)
            coverage["fallback_events_with_known_route"] += int(route_kind != UNKNOWN)

    route_rates = {
        route: (route_fallback_turn_count.get(route, 0) / count if count else 0.0)
        for route, count in route_turn_count.items()
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "eligible_turn_count": eligible_turn_count,
        "fallback_turn_count": fallback_turn_count,
        "fallback_event_count": fallback_event_count,
        "fallback_trigger_rate": fallback_turn_count / eligible_turn_count if eligible_turn_count else 0.0,
        "route_turn_count": _sorted_counts(route_turn_count),
        "route_fallback_turn_count": _sorted_counts(route_fallback_turn_count),
        "route_fallback_trigger_rate": {key: route_rates[key] for key in sorted(route_rates)},
        "unknown_route_turn_count": route_turn_count.get(UNKNOWN, 0),
        "frequency": {field: _sorted_counts(frequency[field]) for field in FREQUENCY_FIELDS},
        "cross_tabs": {field: _sorted_cross_tab(cross_tabs[field]) for field in CROSS_TAB_FIELDS},
        "metadata_coverage": coverage,
    }


def build_report_from_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a report from a scenario-spine transcript-shaped JSON object."""
    turns = payload.get("turns")
    if not isinstance(turns, list):
        raise ValueError("input must be a JSON object with a top-level 'turns' list")
    return build_fallback_incidence_report(turns)


def _percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def _ranked_rows(values: Mapping[str, Any]) -> list[tuple[str, int]]:
    rows = [(str(key), int(count)) for key, count in values.items()]
    return sorted(rows, key=lambda row: (-row[1], row[0]))


def _frequency_section(title: str, values: Mapping[str, Any]) -> list[str]:
    lines = [f"## {title}", "", "| Value | Events |", "|---|---:|"]
    rows = _ranked_rows(values)
    if rows:
        lines.extend(f"| `{value}` | {count} |" for value, count in rows)
    else:
        lines.append("| _none_ | 0 |")
    return lines


def render_fallback_incidence_markdown(report: Mapping[str, Any]) -> str:
    """Render a deterministic operator-facing Markdown report."""
    frequency = _mapping(report.get("frequency"))
    coverage = _mapping(report.get("metadata_coverage"))
    route_counts = _mapping(report.get("route_turn_count"))
    route_fallback_counts = _mapping(report.get("route_fallback_turn_count"))
    route_rates = _mapping(report.get("route_fallback_trigger_rate"))

    lines = [
        "# Fallback Incidence Report",
        "",
        "> Read-only advisory report derived from finalized recorded turn metadata. It does not affect runtime or replay scoring.",
        "",
        "## Summary",
        "",
        f"- **Fallback trigger rate:** {_percent(report.get('fallback_trigger_rate'))}",
        f"- **Eligible turns:** {int(report.get('eligible_turn_count') or 0)}",
        f"- **Fallback turns:** {int(report.get('fallback_turn_count') or 0)}",
        f"- **Fallback events:** {int(report.get('fallback_event_count') or 0)}",
        f"- **Unknown-route turns:** {int(report.get('unknown_route_turn_count') or 0)}",
        "",
    ]
    lines.extend(_frequency_section("Fallback Kinds", _mapping(frequency.get("fallback_kind"))))
    lines.extend([""])
    lines.extend(_frequency_section("Event Owners", _mapping(frequency.get("event_owner"))))
    lines.extend([""])
    lines.extend(_frequency_section("Owner Buckets", _mapping(frequency.get("fallback_owner_bucket"))))
    lines.extend([""])
    lines.extend(_frequency_section("Selection Owners", _mapping(frequency.get("fallback_selection_owner"))))
    lines.extend([""])
    lines.extend(_frequency_section("Content Owners", _mapping(frequency.get("fallback_content_owner"))))
    lines.extend(
        [
            "",
            "## Route Trigger Rates",
            "",
            "| Route | Eligible Turns | Fallback Turns | Trigger Rate |",
            "|---|---:|---:|---:|",
        ]
    )
    if route_counts:
        for route in sorted(route_counts):
            lines.append(
                f"| `{route}` | {int(route_counts[route])} | "
                f"{int(route_fallback_counts.get(route, 0))} | {_percent(route_rates.get(route, 0.0))} |"
            )
    else:
        lines.append("| _none_ | 0 | 0 | 0.00% |")

    lines.extend([""])
    lines.extend(_frequency_section("Final Routes", _mapping(frequency.get("final_route"))))
    lines.extend(
        [
            "",
            "## Metadata Coverage",
            "",
            "| Measure | Count |",
            "|---|---:|",
        ]
    )
    for key in COVERAGE_FIELDS:
        lines.append(f"| `{key}` | {int(coverage.get(key, 0) or 0)} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Rates are turn-scoped: a turn with one or more finalized `fallback_selected` events counts once as a fallback turn. Event counts remain separate so multi-event turns are visible. `route_kind`, FEM `final_route`, and event `gate_path` are intentionally not collapsed.",
            "",
        ]
    )
    return "\n".join(lines)


def write_fallback_incidence_artifacts(
    report: Mapping[str, Any],
    *,
    json_path: Path | str,
    markdown_path: Path | str,
) -> tuple[Path, Path]:
    """Write deterministic UTF-8 JSON and Markdown report artifacts."""
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_fallback_incidence_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Scenario-spine transcript JSON with top-level turns.")
    parser.add_argument("--json-out", required=True, type=Path, help="JSON report output path.")
    parser.add_argument("--md-out", required=True, type=Path, help="Markdown report output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("input JSON root must be an object")
        report = build_report_from_artifact(payload)
        json_out, markdown_out = write_fallback_incidence_artifacts(
            report,
            json_path=args.json_out,
            markdown_path=args.md_out,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fallback incidence report failed: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
