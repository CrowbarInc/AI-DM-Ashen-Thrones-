#!/usr/bin/env python3
"""Audit whether BP2 projection-gap shapes occur in recorded repository artifacts.

The scanner is read-only and advisory. It distinguishes canonical finalized FEM
containers from outer GM metadata and stage snapshots, then invokes the existing
projector only to estimate current coverage. It never changes runtime behavior,
projection rules, replay scoring, or stored inputs.
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

import game.final_emission_meta  # noqa: E402,F401 - establishes repository import order
from game.final_emission_replay_projection import build_fem_runtime_lineage_events  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_ROOTS = (ROOT / "artifacts", ROOT / "data")
DEFAULT_OUTPUT = ROOT / "artifacts" / "golden_replay" / "projection_gap_reality_report.json"
FEM_KEYS = frozenset({"_final_emission_meta", "final_emission_meta"})
AUDIT_REFERENCE_NAMES = frozenset(
    {
        "projection_coverage_report.json",
        "projection_gap_reality_report.json",
        "projection_drift_watch_report.json",
    }
)

GAP_SHAPES: tuple[dict[str, str], ...] = (
    {
        "shape_id": "forced_retry_fallback",
        "field": "final_route",
        "value": "forced_retry_fallback",
        "source": "game/gm_retry.py::force_terminal_retry_fallback",
    },
    {
        "shape_id": "social_fallback_minimal",
        "field": "final_route",
        "value": "social_fallback_minimal",
        "source": "game/gm_retry.py::ensure_minimal_social_resolution",
    },
    {
        "shape_id": "nonsocial_fallback_minimal",
        "field": "final_route",
        "value": "nonsocial_fallback_minimal",
        "source": "game/gm_retry.py::ensure_minimal_nonsocial_resolution",
    },
    {
        "shape_id": "gpt_budget_or_provider_failure_without_trace",
        "field": "realization_fallback_family",
        "value": "gpt_budget_or_provider_failure",
        "source": "game/api.py and game/gm.py",
    },
)

PREFILTER_TERMS = (
    '"_final_emission_meta"',
    '"final_emission_meta"',
    '"forced_retry_fallback"',
    '"social_fallback_minimal"',
    '"nonsocial_fallback_minimal"',
    '"gpt_budget_or_provider_failure"',
    '"runtime_lineage_events"',
)


def _token(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _lookup(value: Mapping[str, Any], *path: str) -> Any:
    current: Any = value
    for part in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _first_token(*values: Any) -> str | None:
    for value in values:
        found = _token(value)
        if found is not None:
            return found
    return None


def _route_kind(record: Mapping[str, Any]) -> str | None:
    meta = _mapping(record.get("meta"))
    return _first_token(
        record.get("route_kind"),
        meta.get("route_kind"),
        record.get("resolution_kind"),
        _lookup(record, "resolution", "kind"),
        _lookup(record, "trace", "social_contract_trace", "route_selected"),
        _lookup(record, "trace", "turn_trace", "social_contract_trace", "route_selected"),
        _lookup(meta, "trace", "social_contract_trace", "route_selected"),
        _lookup(meta, "trace", "turn_trace", "social_contract_trace", "route_selected"),
    )


def _turn_identifier(record: Mapping[str, Any], record_locator: str) -> str:
    meta = _mapping(record.get("meta"))
    scenario = _mapping(meta.get("scenario_spine"))
    value = _first_token(
        record.get("turn_id"),
        scenario.get("turn_id"),
        str(record.get("turn_index")) if record.get("turn_index") is not None else None,
        str(scenario.get("turn_index")) if scenario.get("turn_index") is not None else None,
        record.get("timestamp"),
    )
    return value or record_locator


def _walk_mappings(
    value: Any,
    *,
    path: str = "$",
    inside_fem: bool = False,
) -> Iterable[tuple[Mapping[str, Any], str, bool]]:
    if isinstance(value, Mapping):
        yield value, path, inside_fem
        for key in sorted(value, key=str):
            child = value[key]
            child_path = f"{path}.{key}"
            child_inside_fem = inside_fem or (str(key) in FEM_KEYS and isinstance(child, Mapping))
            yield from _walk_mappings(child, path=child_path, inside_fem=child_inside_fem)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_mappings(child, path=f"{path}[{index}]", inside_fem=inside_fem)


def _has_persisted_fallback_event(record: Mapping[str, Any]) -> bool:
    return any(
        mapping.get("event_type") == "runtime_lineage" and mapping.get("event_kind") == "fallback_selected"
        for mapping, _, _ in _walk_mappings(record)
    )


def _has_fallback_trace(mapping: Mapping[str, Any]) -> bool:
    trace = mapping.get("fallback_provenance_trace")
    return isinstance(trace, Mapping) and _token(trace.get("source")) == "fallback"


def _matching_shape_ids(mapping: Mapping[str, Any]) -> list[str]:
    matches: list[str] = []
    final_route = _token(mapping.get("final_route"))
    if final_route in {"forced_retry_fallback", "social_fallback_minimal", "nonsocial_fallback_minimal"}:
        matches.append(final_route)
    if (
        _token(mapping.get("realization_fallback_family")) == "gpt_budget_or_provider_failure"
        and not _has_fallback_trace(mapping)
    ):
        matches.append("gpt_budget_or_provider_failure_without_trace")
    return matches


def _fallback_selected_from_fem(fem: Mapping[str, Any]) -> bool:
    return any(
        event.get("event_type") == "runtime_lineage" and event.get("event_kind") == "fallback_selected"
        for event in build_fem_runtime_lineage_events(fem)
    )


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _artifact_files(roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix.lower() in {".json", ".jsonl"}:
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".jsonl"})
    return sorted(set(files), key=lambda path: path.as_posix().lower())


def _records_from_json(root: Any) -> list[tuple[Mapping[str, Any], str]]:
    if isinstance(root, Mapping) and isinstance(root.get("turns"), list):
        return [
            (turn, f"$.turns[{index}]")
            for index, turn in enumerate(root["turns"])
            if isinstance(turn, Mapping)
        ]
    if isinstance(root, Mapping):
        return [(root, "$")]
    if isinstance(root, list):
        return [(item, f"$[{index}]") for index, item in enumerate(root) if isinstance(item, Mapping)]
    return []


def _load_records(path: Path) -> tuple[list[tuple[Mapping[str, Any], str]], list[str]]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [], [str(exc)]
    if not any(term in text for term in PREFILTER_TERMS):
        return [], []
    if path.suffix.lower() == ".jsonl":
        records: list[tuple[Mapping[str, Any], str]] = []
        for index, line in enumerate(text.splitlines(), start=1):
            if not line.strip() or not any(term in line for term in PREFILTER_TERMS):
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {index}: {exc}")
                continue
            if isinstance(raw, Mapping):
                records.append((raw, f"$line[{index}]"))
        return records, errors
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], [str(exc)]
    return _records_from_json(raw), errors


def _occurrence(
    *,
    artifact_path: str,
    record: Mapping[str, Any],
    record_locator: str,
    context_path: str,
    mapping: Mapping[str, Any],
    survives_to_finalized_fem: bool,
    persisted_event: bool,
) -> dict[str, Any]:
    return {
        "artifact_path": artifact_path,
        "turn_identifier": _turn_identifier(record, record_locator),
        "record_locator": record_locator,
        "context_path": context_path,
        "route_kind": _route_kind(record),
        "final_route": _token(mapping.get("final_route")),
        "final_emitted_source": _token(mapping.get("final_emitted_source")),
        "fallback_family_used": _token(mapping.get("fallback_family_used")),
        "realization_fallback_family": _token(mapping.get("realization_fallback_family")),
        "fallback_selected_runtime_lineage_event_exists": persisted_event,
        "survives_to_finalized_fem": survives_to_finalized_fem,
        "current_projector_would_emit_fallback": (
            _fallback_selected_from_fem(mapping) if survives_to_finalized_fem else None
        ),
    }


def _reachability_for(shape_id: str, occurrences: list[dict[str, Any]]) -> dict[str, str]:
    finalized = [row for row in occurrences if row["survives_to_finalized_fem"]]
    if finalized:
        current = [row for row in finalized if row["artifact_path"].startswith("data/")]
        if current:
            classification = "A. Confirmed active"
            rationale = "Observed on canonical finalized FEM in the active data artifact tree."
            recommendation = "Add projection"
        else:
            classification = "B. Historical"
            rationale = "Observed on finalized FEM only in stored artifacts, not the active data tree."
            recommendation = "Needs further investigation"
    elif occurrences:
        classification = "C. Packaging-only"
        rationale = "Observed only outside canonical finalized FEM containers."
        recommendation = "Leave unprojected"
    else:
        classification = "D. Unreachable"
        rationale = "No recorded evidence in the scanned repository artifact corpus."
        recommendation = "Needs further investigation"
    if shape_id == "gpt_budget_or_provider_failure_without_trace" and not finalized:
        recommendation = "Leave unprojected"
    if shape_id == "gpt_budget_or_provider_failure_without_trace" and finalized:
        classification = "E. Ambiguous"
        rationale = "Finalized family evidence exists, but selection cannot be distinguished safely without provenance trace."
        recommendation = "Needs further investigation"
    return {"classification": classification, "rationale": rationale, "recommendation": recommendation}


def scan_projection_gap_reality(
    *,
    roots: Iterable[Path] = DEFAULT_ROOTS,
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    """Scan stored JSON/JSONL artifacts for BP2 gap evidence."""
    files = _artifact_files(roots)
    observed: dict[str, list[dict[str, Any]]] = {shape["shape_id"]: [] for shape in GAP_SHAPES}
    parse_errors: list[dict[str, str]] = []
    audit_references: list[str] = []
    relevant_artifacts: set[str] = set()
    finalized_fem_instances: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    current_projected_keys: set[tuple[str, str, str]] = set()
    persisted_event_record_keys: set[tuple[str, str]] = set()

    for path in files:
        relative = _relative(path, repository_root)
        if path.name in AUDIT_REFERENCE_NAMES:
            audit_references.append(relative)
            continue
        records, errors = _load_records(path)
        parse_errors.extend({"artifact_path": relative, "error": error} for error in errors)
        for record, locator in records:
            persisted_event = _has_persisted_fallback_event(record)
            if persisted_event:
                persisted_event_record_keys.add((relative, locator))
            seen_fem_payloads: set[str] = set()
            for mapping, context_path, inside_fem in _walk_mappings(record):
                is_fem_root = context_path.rsplit(".", 1)[-1] in FEM_KEYS
                if is_fem_root:
                    fingerprint = json.dumps(mapping, sort_keys=True, default=str)
                    fem_key = (relative, locator, fingerprint)
                    if fingerprint not in seen_fem_payloads:
                        seen_fem_payloads.add(fingerprint)
                        finalized_fem_instances[fem_key] = mapping
                        if _fallback_selected_from_fem(mapping):
                            current_projected_keys.add(fem_key)
                matches = _matching_shape_ids(mapping)
                if not matches:
                    continue
                relevant_artifacts.add(relative)
                row = _occurrence(
                    artifact_path=relative,
                    record=record,
                    record_locator=locator,
                    context_path=context_path,
                    mapping=mapping,
                    survives_to_finalized_fem=inside_fem,
                    persisted_event=persisted_event,
                )
                for shape_id in matches:
                    observed[shape_id].append(dict(row))

    occurrence_metrics: dict[str, dict[str, int]] = {}
    reachability: dict[str, dict[str, str]] = {}
    additional_finalized_keys: set[tuple[str, str, str]] = set()
    for shape in GAP_SHAPES:
        shape_id = shape["shape_id"]
        rows = sorted(
            observed[shape_id],
            key=lambda row: (row["artifact_path"], row["record_locator"], row["context_path"]),
        )
        observed[shape_id] = rows
        turn_keys = {(row["artifact_path"], row["record_locator"]) for row in rows}
        artifact_paths = {row["artifact_path"] for row in rows}
        finalized_rows = [row for row in rows if row["survives_to_finalized_fem"]]
        occurrence_metrics[shape_id] = {
            "shape_occurrence_count": len(rows),
            "shape_turn_count": len(turn_keys),
            "shape_artifact_count": len(artifact_paths),
            "finalized_fem_occurrence_count": len(finalized_rows),
            "packaging_only_occurrence_count": len(rows) - len(finalized_rows),
        }
        reachability[shape_id] = _reachability_for(shape_id, rows)

    for fem_key, fem in finalized_fem_instances.items():
        if _matching_shape_ids(fem) and fem_key not in current_projected_keys:
            additional_finalized_keys.add(fem_key)

    confirmed_shape_count = sum(
        1 for shape in GAP_SHAPES if occurrence_metrics[shape["shape_id"]]["finalized_fem_occurrence_count"] > 0
    )
    current_projected_count = len(current_projected_keys)
    additional_count = len(additional_finalized_keys)
    adjusted_shape_coverage = (15 + confirmed_shape_count) / 19
    return {
        "schema_version": SCHEMA_VERSION,
        "advisory_only": True,
        "scan_scope": {
            "roots": sorted(_relative(Path(root), repository_root) for root in roots),
            "artifact_file_count": len(files),
            "relevant_artifact_count": len(relevant_artifacts),
            "finalized_fem_instance_count": len(finalized_fem_instances),
            "parse_error_count": len(parse_errors),
            "parse_errors": parse_errors,
            "audit_reference_artifacts_excluded_from_occurrences": sorted(audit_references),
        },
        "gap_shapes": [dict(shape) for shape in GAP_SHAPES],
        "observed_occurrences": observed,
        "frequency": occurrence_metrics,
        "reachability": reachability,
        "projection_impact": {
            "current_projected_fallback_count": current_projected_count,
            "persisted_fallback_selected_turn_count": len(persisted_event_record_keys),
            "additional_fallback_count_if_projected": additional_count,
            "estimated_adjusted_projected_fallback_count": current_projected_count + additional_count,
            "estimated_relative_fallback_count_increase": (
                additional_count / current_projected_count if current_projected_count else 0.0
            ),
            "bp2_shape_coverage_before": 15 / 19,
            "confirmed_gap_shape_count": confirmed_shape_count,
            "estimated_adjusted_coverage": adjusted_shape_coverage,
        },
        "notes": [
            "Occurrences under _final_emission_meta/final_emission_meta are canonical finalized FEM evidence.",
            "Outer GM fields and stage snapshots are packaging-only evidence and do not increase projected incidence.",
            "Projection impact derives existing fallback_selected events from stored FEM without modifying artifacts.",
            "Absence from this repository corpus does not prove code-level impossibility.",
        ],
    }


def write_report(report: Mapping[str, Any], output: Path | str) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, dest="roots", help="Artifact root; repeatable.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Deterministic JSON output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    roots = tuple(args.roots) if args.roots else DEFAULT_ROOTS
    report = scan_projection_gap_reality(roots=roots)
    output = write_report(report, args.output)
    print(f"Wrote {output}")
    for shape in GAP_SHAPES:
        shape_id = shape["shape_id"]
        metrics = report["frequency"][shape_id]
        classification = report["reachability"][shape_id]["classification"]
        print(
            f"{shape_id}: occurrences={metrics['shape_occurrence_count']} "
            f"finalized_fem={metrics['finalized_fem_occurrence_count']} {classification}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
