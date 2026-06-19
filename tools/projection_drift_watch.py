#!/usr/bin/env python3
"""Watch finalized FEM artifacts for known BP3 projection-gap drift.

This report-only tool applies the existing read-side projector to stored FEM. It
does not change projection rules, runtime behavior, incidence calculations, or
replay scoring.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.fallback_projection_gap_reality_audit import (  # noqa: E402
    AUDIT_REFERENCE_NAMES,
    DEFAULT_ROOTS,
    FEM_KEYS,
    _artifact_files,
    _fallback_selected_from_fem,
    _load_records,
    _relative,
    _route_kind,
    _turn_identifier,
    _walk_mappings,
)

SCHEMA_VERSION = 1
DEFAULT_JSON_OUTPUT = ROOT / "artifacts" / "golden_replay" / "projection_drift_watch_report.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "artifacts" / "golden_replay" / "projection_drift_watch_report.md"

WATCH_SHAPES: dict[str, dict[str, str]] = {
    "forced_retry_fallback": {
        "name": "forced_retry_fallback",
        "bp3_classification": "C. Packaging-only",
        "expected_status": "absent_from_finalized_fem",
        "rationale": "Observed by BP3 only on outer GM output and pre-final gate stage snapshots.",
    },
    "nonsocial_fallback_minimal": {
        "name": "nonsocial_fallback_minimal",
        "bp3_classification": "C. Packaging-only",
        "expected_status": "absent_from_finalized_fem",
        "rationale": "Observed by BP3 only on outer GM/stage packaging for one turn.",
    },
    "provider_failure_without_trace": {
        "name": "provider_failure_without_trace",
        "bp3_classification": "D. Unreachable in scanned corpus",
        "expected_status": "absent_from_finalized_fem",
        "rationale": "No finalized provider-failure family was observed without positive provenance trace.",
    },
    "social_fallback_minimal": {
        "name": "social_fallback_minimal",
        "bp3_classification": "D. Unreachable in scanned corpus",
        "expected_status": "absent_from_finalized_fem",
        "rationale": "No exact route occurrence was observed in the BP3 repository artifact corpus.",
    },
}


def _token(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def matching_watch_shapes(fem: Mapping[str, Any]) -> list[str]:
    """Return watch names present on one canonical finalized FEM mapping."""
    matches: list[str] = []
    final_route = _token(fem.get("final_route"))
    if final_route in {
        "forced_retry_fallback",
        "nonsocial_fallback_minimal",
        "social_fallback_minimal",
    }:
        matches.append(final_route)
    trace = fem.get("fallback_provenance_trace")
    trace_proves_fallback = isinstance(trace, Mapping) and _token(trace.get("source")) == "fallback"
    if (
        _token(fem.get("realization_fallback_family")) == "gpt_budget_or_provider_failure"
        and not trace_proves_fallback
    ):
        matches.append("provider_failure_without_trace")
    return sorted(matches)


def _observation(
    *,
    artifact_path: str,
    record: Mapping[str, Any],
    locator: str,
    context_path: str,
    fem: Mapping[str, Any],
    projected: bool,
) -> dict[str, Any]:
    return {
        "artifact": artifact_path,
        "turn": _turn_identifier(record, locator),
        "record_locator": locator,
        "fem_context_path": context_path,
        "route_kind": _route_kind(record),
        "final_route": _token(fem.get("final_route")),
        "final_emitted_source": _token(fem.get("final_emitted_source")),
        "fallback_selected_projected": projected,
    }


def scan_projection_drift_watch(
    *,
    roots: Iterable[Path] = DEFAULT_ROOTS,
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    """Scan canonical finalized FEM and alert only on unprojected watch shapes."""
    files = _artifact_files(roots)
    observations: dict[str, list[dict[str, Any]]] = {name: [] for name in WATCH_SHAPES}
    parse_errors: list[dict[str, str]] = []
    audit_references: list[str] = []
    finalized_fem_count = 0
    seen_fem: set[tuple[str, str, str]] = set()

    for path in files:
        relative = _relative(path, repository_root)
        if path.name in AUDIT_REFERENCE_NAMES:
            audit_references.append(relative)
            continue
        records, errors = _load_records(path)
        parse_errors.extend({"artifact": relative, "error": error} for error in errors)
        for record, locator in records:
            for fem, context_path, _ in _walk_mappings(record):
                if context_path.rsplit(".", 1)[-1] not in FEM_KEYS:
                    continue
                fingerprint = json.dumps(fem, sort_keys=True, default=str)
                identity = (relative, locator, fingerprint)
                if identity in seen_fem:
                    continue
                seen_fem.add(identity)
                finalized_fem_count += 1
                matches = matching_watch_shapes(fem)
                if not matches:
                    continue
                projected = _fallback_selected_from_fem(fem)
                row = _observation(
                    artifact_path=relative,
                    record=record,
                    locator=locator,
                    context_path=context_path,
                    fem=fem,
                    projected=projected,
                )
                for name in matches:
                    observations[name].append(dict(row))

    for name in observations:
        observations[name].sort(
            key=lambda row: (row["artifact"], row["record_locator"], row["fem_context_path"])
        )

    observed_count = {name: len(observations[name]) for name in sorted(WATCH_SHAPES)}
    observed_without_projection = {
        name: sum(not row["fallback_selected_projected"] for row in observations[name])
        for name in sorted(WATCH_SHAPES)
    }
    observed_with_projection = {
        name: observed_count[name] - observed_without_projection[name]
        for name in sorted(WATCH_SHAPES)
    }
    alerts: list[dict[str, Any]] = []
    for name in sorted(WATCH_SHAPES):
        for row in observations[name]:
            if row["fallback_selected_projected"]:
                continue
            alerts.append(
                {
                    "watch_shape": name,
                    "condition": "finalized_fem_watch_shape_without_fallback_selected_projection",
                    **row,
                }
            )

    new_projection_risk = {
        name: {
            "status": "alert" if observed_without_projection[name] else "healthy",
            "observed_on_finalized_fem": observed_count[name],
            "observed_with_projection": observed_with_projection[name],
            "observed_without_projection": observed_without_projection[name],
        }
        for name in sorted(WATCH_SHAPES)
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "status": "alert" if alerts else "healthy",
        "watch_shapes": {name: dict(WATCH_SHAPES[name]) for name in sorted(WATCH_SHAPES)},
        "observed_count": observed_count,
        "observed_with_projection": observed_with_projection,
        "observed_without_projection": observed_without_projection,
        "new_projection_risk": new_projection_risk,
        "observations": observations,
        "alerts": alerts,
        "scan_scope": {
            "roots": sorted(_relative(Path(root), repository_root) for root in roots),
            "artifact_file_count": len(files),
            "finalized_fem_instance_count": finalized_fem_count,
            "parse_error_count": len(parse_errors),
            "parse_errors": parse_errors,
            "audit_reference_artifacts_excluded": sorted(audit_references),
        },
    }


def render_projection_drift_watch_markdown(report: Mapping[str, Any]) -> str:
    watch_shapes = report.get("watch_shapes") if isinstance(report.get("watch_shapes"), Mapping) else {}
    observed = report.get("observed_count") if isinstance(report.get("observed_count"), Mapping) else {}
    without = (
        report.get("observed_without_projection")
        if isinstance(report.get("observed_without_projection"), Mapping)
        else {}
    )
    risks = report.get("new_projection_risk") if isinstance(report.get("new_projection_risk"), Mapping) else {}
    alerts = report.get("alerts") if isinstance(report.get("alerts"), list) else []
    scan = report.get("scan_scope") if isinstance(report.get("scan_scope"), Mapping) else {}
    lines = [
        "# Projection Drift Watch Report",
        "",
        "> Read-only advisory monitoring. This report does not change projection, runtime, incidence, or replay scoring.",
        "",
        "## Executive Summary",
        "",
        f"- **Status:** `{report.get('status', 'healthy')}`",
        f"- **Alerts:** {len(alerts)}",
        f"- **Finalized FEM instances scanned:** {int(scan.get('finalized_fem_instance_count', 0) or 0)}",
        f"- **Artifact files considered:** {int(scan.get('artifact_file_count', 0) or 0)}",
        "",
        "## Watch Registry",
        "",
        "| Shape | BP3 Classification | Expected Status | Rationale |",
        "|---|---|---|---|",
    ]
    for name in sorted(watch_shapes):
        item = watch_shapes[name] if isinstance(watch_shapes[name], Mapping) else {}
        lines.append(
            f"| `{name}` | {item.get('bp3_classification', '')} | "
            f"`{item.get('expected_status', '')}` | {item.get('rationale', '')} |"
        )
    lines.extend(
        [
            "",
            "## Current Observations",
            "",
            "| Shape | Finalized FEM Observations | Without Projection |",
            "|---|---:|---:|",
        ]
    )
    for name in sorted(watch_shapes):
        lines.append(f"| `{name}` | {int(observed.get(name, 0))} | {int(without.get(name, 0))} |")
    lines.extend(
        [
            "",
            "## New Projection Risks",
            "",
            "| Shape | Status | Projected | Unprojected |",
            "|---|---|---:|---:|",
        ]
    )
    for name in sorted(watch_shapes):
        risk = risks[name] if isinstance(risks.get(name), Mapping) else {}
        lines.append(
            f"| `{name}` | `{risk.get('status', 'healthy')}` | "
            f"{int(risk.get('observed_with_projection', 0) or 0)} | "
            f"{int(risk.get('observed_without_projection', 0) or 0)} |"
        )
    lines.extend(["", "## Alert Conditions", ""])
    if alerts:
        lines.append("Alerts fire only when a watch shape appears on canonical finalized FEM and the current projector emits no `fallback_selected` event.")
        lines.append("")
        lines.append("| Shape | Artifact | Turn | Route | Final Route | Final Source |")
        lines.append("|---|---|---|---|---|---|")
        for alert in alerts:
            lines.append(
                f"| `{alert.get('watch_shape')}` | `{alert.get('artifact')}` | "
                f"`{alert.get('turn')}` | `{alert.get('route_kind') or ''}` | "
                f"`{alert.get('final_route') or ''}` | `{alert.get('final_emitted_source') or ''}` |"
            )
    else:
        lines.append("No alert conditions were met. Packaging-only and stage-snapshot occurrences are outside this finalized-FEM watch boundary.")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            (
                "Investigate each alert before changing projection rules; confirm that the FEM represents emitted fallback content and is not stale or synthetic."
                if alerts
                else "Keep all four shapes on watch. No projection expansion is justified by the current finalized-FEM corpus."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_projection_drift_watch_reports(
    report: Mapping[str, Any],
    *,
    json_path: Path | str,
    markdown_path: Path | str,
) -> tuple[Path, Path]:
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_projection_drift_watch_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, dest="roots", help="Artifact root; repeatable.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUTPUT, help="JSON watch report path.")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MARKDOWN_OUTPUT, help="Markdown watch report path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    roots = tuple(args.roots) if args.roots else DEFAULT_ROOTS
    report = scan_projection_drift_watch(roots=roots)
    json_out, markdown_out = write_projection_drift_watch_reports(
        report,
        json_path=args.json_out,
        markdown_path=args.md_out,
    )
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    print(f"Projection drift watch: {report['status']} alerts={len(report['alerts'])}")
    return 1 if report["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
