#!/usr/bin/env python3
"""BV3D — measurement corpus scope filters (read-side only; archives preserved on disk)."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.final_emission_replay_projection import build_fem_runtime_lineage_events  # noqa: E402
from tools.fallback_projection_gap_reality_audit import (  # noqa: E402
    AUDIT_REFERENCE_NAMES,
    FEM_KEYS,
    _artifact_files,
    _load_records,
    _relative,
    _route_kind,
    _walk_mappings,
)

# Narrower roots than DEFAULT_ROOTS (artifacts/, data/) — excludes refresh staging archives.
MEASUREMENT_ROOTS: tuple[Path, ...] = (
    ROOT / "data",
    ROOT / "artifacts" / "scene_canon_hygiene_runtime",
    ROOT / "artifacts" / "scenario_spine_validation",
    ROOT / "artifacts" / "bv3d_measurement",
)

# Entire subtrees preserved on disk but excluded from BV3 incidence / BV3A metrics.
EXCLUDED_PATH_PREFIXES: tuple[str, ...] = (
    "artifacts/bv3b_replay_refresh/",
)

# Filenames treated as debug or derived — never canonical finalized-turn sources.
EXCLUDED_FILE_NAMES: frozenset[str] = frozenset(
    {
        *AUDIT_REFERENCE_NAMES,
        "run_debug.json",
        "bv3a_referential_clarity_metrics.json",
        "bv3b_referential_clarity_metrics.json",
        "bv3d_eligibility_report.json",
        "session_log.pre_refresh.jsonl",
        "fallback_maintenance_economics.json",
        "fallback_risk_report.json",
        "fallback_recurrence_report.json",
        "fallback_incidence_anomalies.json",
        "fallback_incidence_history.json",
        "bv1_fallback_summary.json",
        "bv1b_fallback_summary.json",
    }
)

# Context-path substrings indicating non-finalized stage / retry snapshots inside debug bundles.
DEBUG_FEM_CONTEXT_MARKERS: tuple[str, ...] = (
    ".stage_diff_telemetry",
    ".narration_constraint_debug",
    ".turn_packet_cache",
    ".gate_turn_packet",
    ".metadata.emission_debug",
)

# Terminal finalized FEM locations on API/replay turn records (not mid-pipeline snapshots).
CANONICAL_FEM_PATH_SUFFIXES: tuple[str, ...] = (
    ".gm_output._final_emission_meta",
    ".gm_output.final_emission_meta",
    ".gm_output.internal_state.emission_debug_lane._final_emission_meta",
    ".chat_response.gm_output.internal_state.emission_debug_lane._final_emission_meta",
    "._final_emission_meta",
    ".final_emission_meta",
)

DERIVED_ARTIFACT_PREFIXES: tuple[str, ...] = (
    "artifacts/golden_replay/",
)

POSITIVE_CONTROL_FIXTURES = ROOT / "artifacts" / "bv3d_measurement" / "positive_control_fixtures.jsonl"


@dataclass(frozen=True)
class MeasurementFemHit:
    artifact: str
    locator: str
    context_path: str
    route_kind: str | None
    fem: dict[str, Any]
    source_class: str


def classify_artifact_path(relative_path: str) -> str:
    """Classify a repo-relative artifact path for audit inventory."""
    if relative_path.startswith(EXCLUDED_PATH_PREFIXES):
        return "archive"
    if relative_path.endswith("run_debug.json") or any(m in relative_path for m in DEBUG_FEM_CONTEXT_MARKERS):
        return "debug artifact"
    if relative_path.startswith("artifacts/bv3d_measurement/"):
        return "measurement fixture"
    if any(relative_path.startswith(p) for p in DERIVED_ARTIFACT_PREFIXES):
        if relative_path.endswith(".json") or relative_path.endswith(".md"):
            return "derived artifact"
    if relative_path == "data/session_log.jsonl":
        return "canonical replay"
    if relative_path.startswith("artifacts/scene_canon_hygiene_runtime/"):
        return "refreshed replay"
    if relative_path.startswith("artifacts/scenario_spine_validation/"):
        if relative_path.endswith("transcript.json"):
            return "refreshed replay"
        return "debug artifact"
    if relative_path.startswith("data/"):
        return "canonical replay"
    return "derived artifact"


def is_excluded_artifact_path(path: Path, *, root: Path = ROOT) -> bool:
    relative = _relative(path, root)
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if any(relative.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return True
    if path.name == "run_debug.json":
        return True
    if relative.startswith("artifacts/golden_replay/") and path.suffix.lower() in {".json", ".md"}:
        return True
    return False


def is_canonical_finalized_fem_context(context_path: str) -> bool:
    """True when FEM dict is terminal finalized emission on a turn record."""
    if context_path.rsplit(".", 1)[-1] not in FEM_KEYS:
        return False
    if any(context_path.endswith(suffix) for suffix in CANONICAL_FEM_PATH_SUFFIXES):
        lowered = context_path.lower()
        if any(marker in lowered for marker in DEBUG_FEM_CONTEXT_MARKERS):
            return False
        return True
    return False


def _route_kind_for_record(record: Mapping[str, Any]) -> str | None:
    from tools.fallback_projection_gap_reality_audit import _route_kind, _token

    return _route_kind(record) or _token(record.get("route_kind"))


def iter_measurement_artifact_files(*, roots: Iterable[Path] = MEASUREMENT_ROOTS) -> list[Path]:
    files: list[Path] = []
    for path in _artifact_files(roots):
        if is_excluded_artifact_path(path):
            continue
        files.append(path)
    return files


def scan_measurement_fem_turns(
    *,
    roots: Iterable[Path] = MEASUREMENT_ROOTS,
    include_hits: bool = False,
) -> tuple[list[dict[str, Any]], int, list[MeasurementFemHit]]:
    """Build incidence turn rows from BV3D-filtered finalized FEM instances."""
    turns: list[dict[str, Any]] = []
    hits: list[MeasurementFemHit] = []
    seen: set[tuple[str, str, str]] = set()
    files = iter_measurement_artifact_files(roots=roots)

    for path in files:
        relative = _relative(path, ROOT)
        records, _errors = _load_records(path)
        for record, locator in records:
            route = _route_kind_for_record(record)
            resolution = record.get("resolution") if isinstance(record.get("resolution"), Mapping) else None
            for mapping, context_path, _inside_fem in _walk_mappings(record):
                if not is_canonical_finalized_fem_context(context_path):
                    continue
                fingerprint = json.dumps(mapping, sort_keys=True, default=str)
                identity = (relative, locator, fingerprint)
                if identity in seen:
                    continue
                seen.add(identity)
                fem = dict(mapping)
                turn: dict[str, Any] = {
                    "meta": {
                        "final_emission_meta": fem,
                        "runtime_lineage_events": build_fem_runtime_lineage_events(mapping),
                    },
                    "_measurement": {
                        "artifact": relative,
                        "locator": locator,
                        "context_path": context_path,
                        "source_class": classify_artifact_path(relative),
                    },
                }
                if route:
                    turn["route_kind"] = route
                if isinstance(resolution, Mapping):
                    turn["resolution"] = dict(resolution)
                elif route:
                    turn["resolution"] = {"kind": route}
                turns.append(turn)
                if include_hits:
                    hits.append(
                        MeasurementFemHit(
                            artifact=relative,
                            locator=locator,
                            context_path=context_path,
                            route_kind=route,
                            fem=fem,
                            source_class=classify_artifact_path(relative),
                        )
                    )
    return turns, len(seen), hits


def inventory_scan_roots() -> list[dict[str, str]]:
    """Enumerate artifact files consumed by legacy vs BV3D measurement scanners."""
    rows: list[dict[str, str]] = []
    legacy_files = _artifact_files((ROOT / "artifacts", ROOT / "data"))
    measurement_files = set(iter_measurement_artifact_files())
    for path in sorted(set(legacy_files), key=lambda p: p.as_posix().lower()):
        rel = _relative(path, ROOT)
        rows.append(
            {
                "path": rel,
                "classification": classify_artifact_path(rel),
                "measurement_scope": "included" if path in measurement_files else "excluded",
            }
        )
    return rows
