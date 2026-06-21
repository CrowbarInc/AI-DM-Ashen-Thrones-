"""Golden replay turn-observation projection adapter (Cycle T1).

Centralizes payload/snapshot → observation dict projection and protected
field-path enumeration. Test-only; no runtime behavior changes.

**Cycle AO5 boundary — acceptance observation only (do not merge with runtime lineage):**

This **test-only acceptance** module owns the canonical protected observation paths
(``PROTECTED_OBSERVATION_FIELDS``), ``project_turn_observation``, drift buckets, and
classifier/dashboard overlap derivation. It is CI acceptance authority.

Runtime FEM lineage projection (``fem_runtime_lineage_events``, sealed sub-kinds,
selection/content owner splits on lineage events) is owned by
:mod:`game.final_emission_replay_projection`. Golden replay may consume lineage events
for diagnostics and prefer payload-stamped events when present, but lineage event
**owner** semantics are excluded from protected drift classification unless explicitly
promoted later (see ``test_golden_drift_classification_ignores_runtime_lineage_diagnostics``).

These modules must **not** be merged.

**Dual fallback-family contract (Cycle AB):**

Runtime FEM may carry two independent fallback-family vocabularies:

- ``fallback_family_used`` — diegetic/template taxonomy from
  :mod:`game.diegetic_fallback_narration` (e.g. ``scene_opening``, ``observe``,
  ``social``).
- ``realization_fallback_family`` — governed provenance taxonomy from
  :mod:`game.realization_provenance` / :mod:`game.realization_authority`
  (e.g. ``legacy_diegetic_fallback``, ``upstream_prepared_emission``,
  ``gate_terminal_repair``).

Golden replay exposes a single observed ``fallback_family`` for protected
structural drift checks. :func:`project_replay_fallback_family_from_fem`
implements the read-side precedence rule documented by
:func:`dual_fallback_family_replay_precedence_surface` — diegetic
``fallback_family_used`` first, governed ``realization_fallback_family`` only
when diegetic is absent. That preference is a **read-side compatibility
projection**; runtime code must not rewrite either FEM field to force one
taxonomy into the other, and the two fields must not be collapsed at write time.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping

from game.final_emission_replay_projection import (
    SEALED_REPLACEMENT_SUBKINDS,
    build_fem_runtime_lineage_events,
    is_sealed_replacement_lineage_kind,
    normalize_fem_for_replay_acceptance,
    read_emission_debug_lane_for_replay,
    read_fem_from_turn_for_replay,
    read_opening_fallback_owner_bucket_for_replay,
)
from game.output_sanitizer import resembles_serialized_response_payload
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD
from game.runtime_lineage_telemetry import normalize_runtime_lineage_events

from tests.debug_trace_utils import latest_compact_debug_trace_entry
from tests.helpers.transcript_runner import (
    compact_snapshot_summary,
    latest_target_id,
    latest_target_source,
)

NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY = "neutral_reply_speaker_grounding_bridge"

# Read-side FEM key precedence for golden-replay observed ``fallback_family``.
# Diegetic/template taxonomy wins when present; governed provenance is fallback only.
REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS: tuple[str, ...] = (
    "fallback_family_used",
    REALIZATION_FALLBACK_FAMILY_FIELD,
)

MISSING = object()


@dataclass(frozen=True)
class ProtectedObservationField:
    path: str
    drift_bucket: str
    required: bool = False
    description: str = ""


@dataclass(frozen=True)
class _FlatObservedFieldExtractor:
    """Read-side 1:1 flat observed-key projection from FEM or sanitizer trace."""

    observed_key: str
    source: str  # "fem" | "sanitizer_trace"
    source_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class _SanitizerLineageObservedExtractor:
    """Sanitizer lineage observed key with trace lookup and context fallback."""

    observed_key: str
    trace_key: str
    fallback_context_key: str


@dataclass(frozen=True)
class _ProtectedExtractionSpec:
    """Registry-backed extraction metadata for one protected observation path."""

    path: str
    source: str
    fem_source_keys: tuple[str, ...] = ()
    sanitizer_lineage_trace_key: str = ""
    sanitizer_lineage_context_key: str = ""
    trace_container: str = ""
    raw_presence: str = "none"
    normalized_presence: bool = False
    unavailable_key: str = ""


@dataclass(frozen=True)
class _SupportingRawPresenceSpec:
    """Non-protected keys included in raw_signal_presence for classifier routing."""

    key: str
    fem_source_keys: tuple[str, ...]


def _flat_extractor_source_keys(extractor: _FlatObservedFieldExtractor) -> tuple[str, ...]:
    return extractor.source_keys or (extractor.observed_key,)


def _protected_extraction_spec(
    path: str,
    *,
    source: str,
    fem_source_keys: tuple[str, ...] = (),
    sanitizer_lineage_trace_key: str = "",
    sanitizer_lineage_context_key: str = "",
    trace_container: str = "",
    raw_presence: str = "none",
    normalized_presence: bool = False,
    unavailable_key: str = "",
) -> _ProtectedExtractionSpec:
    return _ProtectedExtractionSpec(
        path=path,
        source=source,
        fem_source_keys=fem_source_keys,
        sanitizer_lineage_trace_key=sanitizer_lineage_trace_key,
        sanitizer_lineage_context_key=sanitizer_lineage_context_key,
        trace_container=trace_container,
        raw_presence=raw_presence,
        normalized_presence=normalized_presence,
        unavailable_key=unavailable_key,
    )


def _extract_fem_flat_observed_fields(fem: Mapping[str, Any]) -> dict[str, Any]:
    """Project registry-listed flat FEM fields into observed-key values."""
    return {
        extractor.observed_key: _first_present(fem, _flat_extractor_source_keys(extractor))
        for extractor in _FEM_FLAT_OBSERVED_EXTRACTORS
    }


def _extract_sanitizer_trace_flat_observed_fields(sanitizer_trace: Mapping[str, Any]) -> dict[str, Any]:
    """Project registry-listed flat sanitizer-trace fields into observed-key values."""
    return {
        extractor.observed_key: _first_present(sanitizer_trace, _flat_extractor_source_keys(extractor))
        for extractor in _SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS
    }


def _extract_sanitizer_lineage_observed_fields(
    sanitizer_trace: Mapping[str, Any],
    *,
    lineage_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Project sanitizer lineage observed keys with trace lookup and context fallbacks."""
    out = {
        extractor.observed_key: _sanitizer_lineage_field(
            sanitizer_trace,
            extractor.trace_key,
            lineage_context.get(extractor.fallback_context_key),
        )
        for extractor in _SANITIZER_LINEAGE_OBSERVED_EXTRACTORS
    }
    sanitizer_lineage_mode = out["sanitizer_lineage_mode"]
    out["sanitizer_lineage_legacy_rewrite_active"] = _sanitizer_lineage_field(
        sanitizer_trace,
        "sanitizer_lineage_legacy_rewrite_active",
        str(sanitizer_lineage_mode or "").strip().lower() == "legacy_sentence_rewrite"
        if sanitizer_lineage_mode is not None
        else None,
    )
    return out


def _observed_fem_flat_values(fem_flat: Mapping[str, Any]) -> dict[str, Any]:
    """Apply observed-turn value shaping for registry-projected FEM flat fields."""
    out = dict(fem_flat)
    lineage = out.get("final_emission_mutation_lineage")
    out["final_emission_mutation_lineage"] = list(lineage) if isinstance(lineage, list) else lineage
    return out


def _protected_structural_fields(*paths: str) -> tuple[ProtectedObservationField, ...]:
    return tuple(
        ProtectedObservationField(path=path, drift_bucket="structural_drift") for path in paths
    )


def _protected_semantic_fields(*paths: str) -> tuple[ProtectedObservationField, ...]:
    return tuple(
        ProtectedObservationField(path=path, drift_bucket="semantic_drift") for path in paths
    )


PROTECTED_OBSERVATION_FIELDS: tuple[ProtectedObservationField, ...] = (
    *_protected_structural_fields(
        "resolution_kind",
        "route_kind",
        "selected_speaker_id",
        "final_emitted_source",
        "final_emission_mutation_lineage",
        "response_type_required",
        "response_type_candidate_ok",
        "response_type_repair_used",
        "response_type_repair_kind",
        "upstream_prepared_emission_used",
        "upstream_prepared_emission_valid",
        "upstream_prepared_emission_source",
        "upstream_prepared_emission_reject_reason",
        "sanitizer_empty_fallback_used",
        "sanitizer_empty_fallback_source",
        "sanitizer_empty_fallback_owner",
        "sanitizer_lineage_mode",
        "sanitizer_lineage_changed_count",
        "sanitizer_lineage_dropped_count",
        "sanitizer_lineage_empty_fallback_used",
        "sanitizer_lineage_legacy_rewrite_active",
        "sanitizer_strict_social_fallback_used",
        "sanitizer_strict_social_selection_owner",
        "sanitizer_strict_social_prose_owner",
        "sanitizer_strict_social_source",
        "opening_recovered_via_fallback",
        "opening_fallback_authorship_source",
        "opening_fallback_owner_bucket",
        "sealed_fallback_owner_bucket",
        "visibility_fallback_owner_bucket",
        "visibility_replacement_applied",
        "visibility_fallback_pool",
        "visibility_fallback_kind",
        "fallback_family",
        "fallback_temporal_frame",
        "trace.canonical_entry.target_actor_id",
        "trace.canonical_entry.target_source",
        "trace.canonical_entry.reason",
        "trace.social_contract_trace.route_selected",
    ),
    *_protected_semantic_fields("final_text", "scaffold_leakage"),
)

STRUCTURAL_DRIFT_FIELDS = frozenset(
    field.path for field in PROTECTED_OBSERVATION_FIELDS if field.drift_bucket == "structural_drift"
)

SEMANTIC_DRIFT_FIELDS = frozenset(
    field.path for field in PROTECTED_OBSERVATION_FIELDS if field.drift_bucket == "semantic_drift"
)

_DRIFT_BUCKET_BY_PATH = {field.path: field.drift_bucket for field in PROTECTED_OBSERVATION_FIELDS}

# Registry-backed extraction specs — one entry per protected path (AO1).
_PROTECTED_EXTRACTION_SPECS: dict[str, _ProtectedExtractionSpec] = {
    "resolution_kind": _protected_extraction_spec("resolution_kind", source="resolution"),
    "route_kind": _protected_extraction_spec(
        "route_kind",
        source="route",
        raw_presence="route",
        unavailable_key="route_kind",
    ),
    "selected_speaker_id": _protected_extraction_spec(
        "selected_speaker_id",
        source="speaker",
        raw_presence="speaker",
        unavailable_key="selected_speaker_id",
    ),
    "final_emitted_source": _protected_extraction_spec(
        "final_emitted_source",
        source="fem_flat",
        fem_source_keys=("final_emitted_source", "final_route", "upstream_prepared_emission_source"),
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="final_emitted_source",
    ),
    "final_emission_mutation_lineage": _protected_extraction_spec(
        "final_emission_mutation_lineage",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "response_type_required": _protected_extraction_spec(
        "response_type_required",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="response_type_required",
    ),
    "response_type_candidate_ok": _protected_extraction_spec(
        "response_type_candidate_ok",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="response_type_candidate_ok",
    ),
    "response_type_repair_used": _protected_extraction_spec(
        "response_type_repair_used",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
        unavailable_key="response_type_repair_used",
    ),
    "response_type_repair_kind": _protected_extraction_spec("response_type_repair_kind", source="fem_flat"),
    "upstream_prepared_emission_used": _protected_extraction_spec(
        "upstream_prepared_emission_used",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "upstream_prepared_emission_valid": _protected_extraction_spec(
        "upstream_prepared_emission_valid",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "upstream_prepared_emission_source": _protected_extraction_spec(
        "upstream_prepared_emission_source",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "upstream_prepared_emission_reject_reason": _protected_extraction_spec(
        "upstream_prepared_emission_reject_reason",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "sanitizer_empty_fallback_used": _protected_extraction_spec(
        "sanitizer_empty_fallback_used",
        source="sanitizer_trace",
    ),
    "sanitizer_empty_fallback_source": _protected_extraction_spec(
        "sanitizer_empty_fallback_source",
        source="sanitizer_trace",
    ),
    "sanitizer_empty_fallback_owner": _protected_extraction_spec(
        "sanitizer_empty_fallback_owner",
        source="sanitizer_trace",
    ),
    "sanitizer_lineage_mode": _protected_extraction_spec(
        "sanitizer_lineage_mode",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_mode",
        sanitizer_lineage_context_key="sanitizer_mode",
    ),
    "sanitizer_lineage_changed_count": _protected_extraction_spec(
        "sanitizer_lineage_changed_count",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_changed_count",
        sanitizer_lineage_context_key="sanitizer_changed_count",
    ),
    "sanitizer_lineage_dropped_count": _protected_extraction_spec(
        "sanitizer_lineage_dropped_count",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_dropped_count",
        sanitizer_lineage_context_key="sanitizer_dropped_count",
    ),
    "sanitizer_lineage_empty_fallback_used": _protected_extraction_spec(
        "sanitizer_lineage_empty_fallback_used",
        source="sanitizer_lineage",
        sanitizer_lineage_trace_key="sanitizer_lineage_empty_fallback_used",
        sanitizer_lineage_context_key="sanitizer_empty_fallback_used",
    ),
    "sanitizer_lineage_legacy_rewrite_active": _protected_extraction_spec(
        "sanitizer_lineage_legacy_rewrite_active",
        source="sanitizer_lineage_legacy",
        sanitizer_lineage_trace_key="sanitizer_lineage_legacy_rewrite_active",
    ),
    "sanitizer_strict_social_fallback_used": _protected_extraction_spec(
        "sanitizer_strict_social_fallback_used",
        source="sanitizer_trace",
    ),
    "sanitizer_strict_social_selection_owner": _protected_extraction_spec(
        "sanitizer_strict_social_selection_owner",
        source="sanitizer_trace",
    ),
    "sanitizer_strict_social_prose_owner": _protected_extraction_spec(
        "sanitizer_strict_social_prose_owner",
        source="sanitizer_trace",
    ),
    "sanitizer_strict_social_source": _protected_extraction_spec(
        "sanitizer_strict_social_source",
        source="sanitizer_trace",
    ),
    "opening_recovered_via_fallback": _protected_extraction_spec(
        "opening_recovered_via_fallback",
        source="fem_flat",
    ),
    "opening_fallback_authorship_source": _protected_extraction_spec(
        "opening_fallback_authorship_source",
        source="fem_flat",
    ),
    "opening_fallback_owner_bucket": _protected_extraction_spec(
        "opening_fallback_owner_bucket",
        source="fem_opening_bucket",
    ),
    "sealed_fallback_owner_bucket": _protected_extraction_spec(
        "sealed_fallback_owner_bucket",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_fallback_owner_bucket": _protected_extraction_spec(
        "visibility_fallback_owner_bucket",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_replacement_applied": _protected_extraction_spec(
        "visibility_replacement_applied",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_fallback_pool": _protected_extraction_spec(
        "visibility_fallback_pool",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "visibility_fallback_kind": _protected_extraction_spec(
        "visibility_fallback_kind",
        source="fem_flat",
        raw_presence="fem_key",
        normalized_presence=True,
    ),
    "fallback_family": _protected_extraction_spec(
        "fallback_family",
        source="fallback_family",
        raw_presence="fem_dual_family",
        normalized_presence=True,
        unavailable_key="fallback_family",
    ),
    "fallback_temporal_frame": _protected_extraction_spec(
        "fallback_temporal_frame",
        source="fem_flat",
    ),
    "trace.canonical_entry.target_actor_id": _protected_extraction_spec(
        "trace.canonical_entry.target_actor_id",
        source="trace_leaf",
        trace_container="canonical_entry",
    ),
    "trace.canonical_entry.target_source": _protected_extraction_spec(
        "trace.canonical_entry.target_source",
        source="trace_leaf",
        trace_container="canonical_entry",
    ),
    "trace.canonical_entry.reason": _protected_extraction_spec(
        "trace.canonical_entry.reason",
        source="trace_leaf",
        trace_container="canonical_entry",
    ),
    "trace.social_contract_trace.route_selected": _protected_extraction_spec(
        "trace.social_contract_trace.route_selected",
        source="trace_leaf",
        trace_container="social_contract_trace",
    ),
    "final_text": _protected_extraction_spec("final_text", source="final_text"),
    "scaffold_leakage": _protected_extraction_spec("scaffold_leakage", source="scaffold"),
}

# Parent trace containers tracked for raw presence and unavailable handling.
_TRACE_CONTAINER_RAW_PRESENCE: tuple[tuple[str, str], ...] = (
    ("trace.canonical_entry", "canonical_entry"),
    ("trace.turn_trace", "turn_trace"),
    ("trace.social_contract_trace", "social_contract_trace"),
)

_TRACE_CONTAINER_UNAVAILABLE_KEYS: frozenset[str] = frozenset(
    key for key, _container in _TRACE_CONTAINER_RAW_PRESENCE
)

# Supporting (non-protected) keys in raw_signal_presence for classifier missing-source routing.
_SUPPORTING_RAW_PRESENCE_SPECS: tuple[_SupportingRawPresenceSpec, ...] = (
    _SupportingRawPresenceSpec("response_delta_checked", ("response_delta_checked",)),
    _SupportingRawPresenceSpec("response_delta_failed", ("response_delta_failed",)),
    _SupportingRawPresenceSpec("response_delta_repaired", ("response_delta_repaired",)),
    _SupportingRawPresenceSpec("response_delta_kind", ("response_delta_kind", "response_delta_kind_detected")),
    _SupportingRawPresenceSpec("response_delta_echo_overlap_ratio", ("response_delta_echo_overlap_ratio",)),
)


def _validate_protected_extraction_registry() -> None:
    registry_paths = {field.path for field in PROTECTED_OBSERVATION_FIELDS}
    spec_paths = set(_PROTECTED_EXTRACTION_SPECS)
    if registry_paths != spec_paths:
        missing = sorted(registry_paths - spec_paths)
        extra = sorted(spec_paths - registry_paths)
        raise AssertionError(
            "Protected extraction registry must cover every PROTECTED_OBSERVATION_FIELDS path; "
            f"missing={missing!r} extra={extra!r}"
        )


def protected_observation_extraction_registry() -> dict[str, _ProtectedExtractionSpec]:
    """Return the canonical protected-field extraction registry (AO1)."""
    return dict(_PROTECTED_EXTRACTION_SPECS)


# Flat protected paths excluded from classifier optional evidence copy (AO2).
# Dotted trace paths are excluded automatically via the flat-path filter.
_PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS: frozenset[str] = frozenset(
    {
        "resolution_kind",
        "response_type_candidate_ok",
        "opening_recovered_via_fallback",
        "final_text",
        "scaffold_leakage",
    }
)

_EXPECTED_PROTECTED_CLASSIFIER_EVIDENCE_COUNT = 32

def _fem_flat_extractors_from_registry() -> tuple[_FlatObservedFieldExtractor, ...]:
    extractors: list[_FlatObservedFieldExtractor] = []
    for spec in _PROTECTED_EXTRACTION_SPECS.values():
        if spec.source != "fem_flat":
            continue
        extractors.append(
            _FlatObservedFieldExtractor(
                spec.path,
                "fem",
                spec.fem_source_keys or (spec.path,),
            )
        )
    return tuple(extractors)


def _sanitizer_trace_extractors_from_registry() -> tuple[_FlatObservedFieldExtractor, ...]:
    return tuple(
        _FlatObservedFieldExtractor(spec.path, "sanitizer_trace")
        for spec in _PROTECTED_EXTRACTION_SPECS.values()
        if spec.source == "sanitizer_trace"
    )


def _sanitizer_lineage_extractors_from_registry() -> tuple[_SanitizerLineageObservedExtractor, ...]:
    return tuple(
        _SanitizerLineageObservedExtractor(
            spec.path,
            spec.sanitizer_lineage_trace_key,
            spec.sanitizer_lineage_context_key,
        )
        for spec in _PROTECTED_EXTRACTION_SPECS.values()
        if spec.source == "sanitizer_lineage"
    )


_validate_protected_extraction_registry()

_FEM_FLAT_OBSERVED_EXTRACTORS = _fem_flat_extractors_from_registry()
_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS = _sanitizer_trace_extractors_from_registry()
_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS = _sanitizer_lineage_extractors_from_registry()

_SCAFFOLD_LEAK_RE = re.compile(
    r"\b(?:planner|router|validator|adjudication|scaffold|authoritative state|"
    r"resolve that procedurally|player_facing_text|scene_update|debug_notes)\b",
    re.IGNORECASE,
)


def protected_observation_field_registry() -> tuple[ProtectedObservationField, ...]:
    """Return the canonical protected observation field registry."""
    return PROTECTED_OBSERVATION_FIELDS


def protected_observation_field_paths() -> tuple[str, ...]:
    """Return sorted unique dotted paths from the protected observation registry."""
    return tuple(sorted({field.path for field in PROTECTED_OBSERVATION_FIELDS}))


def protected_observation_flat_field_paths() -> tuple[str, ...]:
    """Return sorted flat (non-dotted) protected observation registry paths."""
    return tuple(path for path in protected_observation_field_paths() if "." not in path)


def _neutral_default_for_flat_protected_path(path: str) -> Any:
    if path == "scaffold_leakage":
        return False
    if path == "final_text":
        return ""
    return None


def protected_observation_default_row() -> dict[str, Any]:
    """Neutral defaults for every flat protected observation registry path."""
    return {
        path: _neutral_default_for_flat_protected_path(path)
        for path in protected_observation_flat_field_paths()
    }


def observed_projection_schema_defaults() -> dict[str, Any]:
    """Schema-aligned defaults for synthetic observed replay rows."""
    return {
        **protected_observation_default_row(),
        "trace": {
            "canonical_entry": {},
            "turn_trace": {},
            "social_contract_trace": {},
        },
        "unavailable": [],
    }


PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN = "<!-- BEGIN GENERATED: protected_field_paths -->"
PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END = "<!-- END GENERATED: protected_field_paths -->"


def protected_observation_manifest_field_rows() -> tuple[tuple[str, str], ...]:
    """Return sorted ``(path, drift_bucket)`` rows derived from ``PROTECTED_OBSERVATION_FIELDS``."""
    buckets_by_path: dict[str, str] = {}
    for field in PROTECTED_OBSERVATION_FIELDS:
        previous = buckets_by_path.setdefault(field.path, field.drift_bucket)
        if previous != field.drift_bucket:
            raise ValueError(
                f"Protected observation field {field.path!r} has conflicting drift buckets: "
                f"{previous!r} and {field.drift_bucket!r}"
            )
    return tuple((path, buckets_by_path[path]) for path in sorted(buckets_by_path))


def protected_observation_manifest_counts() -> dict[str, int]:
    """Return structural/semantic/total counts for manifest generation."""
    rows = protected_observation_manifest_field_rows()
    structural_count = sum(bucket == "structural_drift" for _path, bucket in rows)
    semantic_count = sum(bucket == "semantic_drift" for _path, bucket in rows)
    return {
        "total": len(rows),
        "structural_drift": structural_count,
        "semantic_drift": semantic_count,
    }


def render_protected_observation_manifest_section(
    *,
    begin_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN,
    end_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END,
    refresh_command: str = "python tools/refresh_protected_replay_manifest.py --write",
    check_command: str = "python tools/refresh_protected_replay_manifest.py --check",
) -> str:
    """Render the bounded protected-field-paths section for ``protected_replay_manifest.md``."""
    rows = protected_observation_manifest_field_rows()
    counts = protected_observation_manifest_counts()
    lines = [
        begin_marker,
        "",
        "## Protected Observation Field Paths (Generated)",
        "",
        "Bounded registry of golden replay observation paths locked by protected replay.",
        "Source: `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`.",
        "",
        "Refresh this section:",
        "",
        "```bash",
        refresh_command,
        "```",
        "",
        "Verify without writing:",
        "",
        "```bash",
        check_command,
        "```",
        "",
        f"- **Path count:** {counts['total']}",
        f"- **Structural drift fields:** {counts['structural_drift']}",
        f"- **Semantic drift fields:** {counts['semantic_drift']}",
        "",
        "| Field path | Drift bucket |",
        "|---|---|",
    ]
    for path, bucket in rows:
        lines.append(f"| `{path}` | `{bucket}` |")
    lines.extend(["", end_marker])
    return "\n".join(lines)


def extract_protected_observation_manifest_section(
    manifest_text: str,
    *,
    begin_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN,
    end_marker: str = PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END,
) -> str | None:
    """Extract the generated protected-field-paths section from manifest markdown."""
    begin = manifest_text.find(begin_marker)
    end = manifest_text.find(end_marker)
    if begin == -1 or end == -1 or end < begin:
        return None
    return manifest_text[begin : end + len(end_marker)]


def protected_observation_manifest_section_is_current(manifest_text: str) -> bool:
    """Return True when the manifest generated section matches ``PROTECTED_OBSERVATION_FIELDS``."""
    current = extract_protected_observation_manifest_section(manifest_text)
    expected = render_protected_observation_manifest_section()
    return current is not None and current == expected


def protected_observation_manifest_registry_parity_errors(
    manifest_text: str,
) -> list[str]:
    """Return parity drift messages when manifest docs diverge from the protected observation registry."""
    errors: list[str] = []

    if extract_protected_observation_manifest_section(manifest_text) is None:
        errors.append(
            "missing generated manifest section markers "
            f"{PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN!r} / "
            f"{PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END!r}"
        )
        return errors

    if not protected_observation_manifest_section_is_current(manifest_text):
        errors.append(
            "generated manifest section is stale; "
            "run: python tools/refresh_protected_replay_manifest.py --write"
        )

    manifest_rows = dict(protected_observation_manifest_field_rows())
    registry_paths = protected_observation_field_paths()
    manifest_paths = tuple(manifest_rows)

    if manifest_paths != registry_paths:
        extra = sorted(set(manifest_paths) - set(registry_paths))
        missing = sorted(set(registry_paths) - set(manifest_paths))
        if extra:
            errors.append(f"manifest has paths not in registry: {extra!r}")
        if missing:
            errors.append(f"manifest missing registry paths: {missing!r}")

    for field in protected_observation_field_registry():
        registry_bucket = field.drift_bucket
        drift_bucket = protected_observation_drift_bucket(field.path)
        if drift_bucket != registry_bucket:
            errors.append(
                f"protected_observation_drift_bucket({field.path!r})={drift_bucket!r} "
                f"but registry declares {registry_bucket!r}"
            )
        manifest_bucket = manifest_rows.get(field.path)
        if manifest_bucket is not None and manifest_bucket != registry_bucket:
            errors.append(
                f"manifest drift bucket for {field.path!r} is {manifest_bucket!r}, "
                f"registry declares {registry_bucket!r}"
            )

    return errors


def protected_observation_drift_bucket(path: str) -> str:
    """Map a protected observation field path to its drift bucket."""
    bucket = _DRIFT_BUCKET_BY_PATH.get(path)
    if bucket is not None:
        return bucket
    if str(path).startswith("trace."):
        return "structural_drift"
    if str(path).startswith("semantic."):
        return "semantic_drift"
    return "structural_drift"


def protected_classifier_evidence_excluded_paths() -> frozenset[str]:
    """Return flat protected paths intentionally excluded from classifier evidence overlap (AO2)."""
    return frozenset(_PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS)


def protected_classifier_evidence_field_paths() -> frozenset[str]:
    """Return flat protected observation paths copied as classifier optional evidence (AO2).

    Derived from :func:`protected_observation_field_paths` and
    :func:`protected_observation_extraction_registry` — flat protected paths minus
    classifier-ineligible exclusions (semantic fields, trace-only locks, etc.).
    """
    return frozenset(
        path
        for path in protected_observation_field_paths()
        if "." not in path and path not in _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS
    )


def _validate_protected_classifier_evidence_derivation() -> None:
    derived = protected_classifier_evidence_field_paths()
    flat_protected = {path for path in protected_observation_field_paths() if "." not in path}
    dotted_protected = {path for path in protected_observation_field_paths() if "." in path}
    if derived & _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS:
        overlap = sorted(derived & _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS)
        raise AssertionError(
            "protected classifier evidence paths must not include excluded paths; "
            f"overlap={overlap!r}"
        )
    if derived & dotted_protected:
        raise AssertionError(
            "protected classifier evidence paths must be flat protected paths only; "
            f"dotted_overlap={sorted(derived & dotted_protected)!r}"
        )
    expected = flat_protected - _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS
    if derived != expected:
        raise AssertionError(
            "protected classifier evidence derivation must equal flat protected paths minus exclusions; "
            f"unexpected={sorted(derived - expected)!r} missing={sorted(expected - derived)!r}"
        )
    if len(derived) != _EXPECTED_PROTECTED_CLASSIFIER_EVIDENCE_COUNT:
        raise AssertionError(
            f"expected {_EXPECTED_PROTECTED_CLASSIFIER_EVIDENCE_COUNT} protected classifier evidence paths, "
            f"got {len(derived)}; update _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS or classifier "
            "OPTIONAL contract if the protected observation registry changed"
        )
    registry_paths = set(protected_observation_extraction_registry())
    if not derived <= registry_paths:
        raise AssertionError(
            "protected classifier evidence paths must be subset of extraction registry; "
            f"outside_registry={sorted(derived - registry_paths)!r}"
        )


_validate_protected_classifier_evidence_derivation()

def final_text_has_scaffold_leakage(text: str) -> bool:
    """Best-effort final-text leak detector for golden structural assertions."""
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(_SCAFFOLD_LEAK_RE.search(text) or resembles_serialized_response_payload(text))


def normalize_golden_text(text: Any) -> str:
    """Stable, opt-in text normalization for exact golden prose checks."""
    return re.sub(r"\s+", " ", str(text or "").strip())


def golden_text_hash(text: Any) -> str:
    """Short deterministic hash for report rows without storing long prose."""
    return hashlib.sha256(normalize_golden_text(text).encode("utf-8")).hexdigest()[:16]


def lookup_observation_path(obj: Mapping[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in str(path or "").split("."):
        if not part:
            return MISSING
        if not isinstance(cur, Mapping) or part not in cur:
            return MISSING
        cur = cur.get(part)
    return cur


def _unavailable_paths(observed: Mapping[str, Any]) -> frozenset[str]:
    raw = observed.get("unavailable")
    if not isinstance(raw, (list, tuple, set, frozenset)):
        return frozenset()
    return frozenset(str(item) for item in raw)


def protected_path_covered_by_unavailable(path: str, unavailable: frozenset[str]) -> bool:
    """Return whether *path* or a dotted parent prefix is listed unavailable."""
    if path in unavailable:
        return True
    parts = path.split(".")
    return any(".".join(parts[:index]) in unavailable for index in range(1, len(parts)))


def protected_path_is_represented_in_observed_turn(
    observed: Mapping[str, Any],
    path: str,
) -> bool:
    """Return whether a protected path is projected or explicitly marked unavailable.

    Flat protected keys count as represented when present on the observed-turn dict,
    even when the stored value is ``None`` or the ``MISSING`` lookup sentinel.
    Dotted protected paths must be navigable via :func:`lookup_observation_path` unless
    an unavailable parent prefix explains the absence.
    """
    unavailable = _unavailable_paths(observed)
    if protected_path_covered_by_unavailable(path, unavailable):
        return True
    if "." not in path:
        return path in observed
    return lookup_observation_path(observed, path) is not MISSING


def protected_path_representation_errors(observed: Mapping[str, Any]) -> list[str]:
    """Return protected registry paths neither projected nor listed unavailable."""
    return [
        field.path
        for field in protected_observation_field_registry()
        if not protected_path_is_represented_in_observed_turn(observed, field.path)
    ]


def _sanitizer_debug_change_counts(sanitizer_debug: list[Any] | None) -> tuple[int | None, int | None]:
    if not sanitizer_debug:
        return None, None
    changed = 0
    dropped = 0
    for event in sanitizer_debug:
        if not isinstance(event, Mapping):
            continue
        event_name = str(event.get("event") or "").lower()
        if any(token in event_name for token in ("dropped", "rewritten", "rewrite", "strip")):
            changed += 1
        if "dropped" in event_name or "drop" in event_name:
            dropped += 1
    return changed, dropped


def _sanitizer_lineage_field(
    sanitizer_trace: Mapping[str, Any] | None,
    key: str,
    fallback: Any = None,
) -> Any:
    if isinstance(sanitizer_trace, Mapping) and key in sanitizer_trace:
        return sanitizer_trace.get(key)
    return fallback


def _echo_overlap_band(value: Any) -> str | None:
    if value is not None and not isinstance(value, bool):
        text = str(value).strip()
        if text and _echo_overlap_ratio(text) is None:
            return text
    ratio = _echo_overlap_ratio(value)
    if ratio is None:
        return None
    if ratio == 0:
        return "none"
    if ratio < 0.25:
        return "low"
    if ratio < 0.5:
        return "medium"
    return "high"


def _echo_overlap_ratio(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        ratio = float(value)
    else:
        try:
            ratio = float(str(value).strip())
        except (TypeError, ValueError):
            return None
    if ratio < 0:
        return None
    return min(ratio, 1.0)


def _trace_from_payload_or_snapshot(payload: Mapping[str, Any], snap: Mapping[str, Any]) -> dict[str, Any]:
    traces = payload.get("debug_traces")
    if not isinstance(traces, list):
        session = payload.get("session") if isinstance(payload.get("session"), Mapping) else {}
        traces = session.get("debug_traces") if isinstance(session.get("debug_traces"), list) else []
    trace = latest_compact_debug_trace_entry(traces)
    if trace:
        return trace
    debug = snap.get("debug") if isinstance(snap.get("debug"), Mapping) else {}
    last = debug.get("last_debug_trace")
    return dict(last) if isinstance(last, Mapping) else {}


def _first_present(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def _has_path(obj: Mapping[str, Any], path: str) -> bool:
    cur: Any = obj
    for part in str(path or "").split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return False
        cur = cur.get(part)
    return True


def _find_nested_mapping(root: Mapping[str, Any], key: str) -> dict[str, Any]:
    stack: list[Any] = [root]
    seen = 0
    while stack and seen < 200:
        seen += 1
        cur = stack.pop()
        if not isinstance(cur, Mapping):
            continue
        value = cur.get(key)
        if isinstance(value, Mapping):
            return dict(value)
        for child in cur.values():
            if isinstance(child, Mapping):
                stack.append(child)
            elif isinstance(child, list):
                stack.extend(item for item in child if isinstance(item, Mapping))
    return {}


def _find_nested_list(root: Mapping[str, Any], key: str) -> list[Any]:
    stack: list[Any] = [root]
    seen = 0
    while stack and seen < 200:
        seen += 1
        cur = stack.pop()
        if not isinstance(cur, Mapping):
            continue
        value = cur.get(key)
        if isinstance(value, list):
            return list(value)
        for child in cur.values():
            if isinstance(child, Mapping):
                stack.append(child)
            elif isinstance(child, list):
                stack.extend(item for item in child if isinstance(item, Mapping))
    return []


def _find_nested_list_field(root: Mapping[str, Any], key: str) -> tuple[bool, list[Any]]:
    """Return whether a nested projected-list field exists, preserving an explicit empty list."""
    stack: list[Any] = [root]
    seen = 0
    while stack and seen < 200:
        seen += 1
        cur = stack.pop()
        if not isinstance(cur, Mapping):
            continue
        if key in cur:
            value = cur.get(key)
            return True, list(value) if isinstance(value, list) else []
        for child in cur.values():
            if isinstance(child, Mapping):
                stack.append(child)
            elif isinstance(child, list):
                stack.extend(item for item in child if isinstance(item, Mapping))
    return False, []


def _runtime_lineage_events_from_payload(payload: Mapping[str, Any], fem: Mapping[str, Any]) -> list[dict[str, Any]]:
    found, events = _find_nested_list_field(payload, "fem_runtime_lineage_events")
    if found:
        return normalize_runtime_lineage_events(events)[:16]
    return build_fem_runtime_lineage_events(fem)[:16] if fem else []


def _project_replay_fallback_family(
    fem: Mapping[str, Any],
    runtime_lineage_events: list[Mapping[str, Any]],
) -> str | None:
    """Return read-side diagnostic family for finalized fallback evidence missing a family field."""
    final_route = str(fem.get("final_route") or "").strip().lower()
    final_source = str(fem.get("final_emitted_source") or "").strip()
    if final_route != "replaced" or final_source != NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY:
        return None
    if any(
        event.get("event_kind") == "fallback_selected"
        and is_sealed_replacement_lineage_kind(event.get("fallback_kind"))
        for event in runtime_lineage_events
        if isinstance(event, Mapping)
    ):
        return NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY
    return None


def dual_fallback_family_replay_precedence_surface() -> dict[str, object]:
    """Document read-side golden-replay precedence for dual FEM fallback-family fields.

    Diagnostic only: does not read live payloads or mutate FEM.
    """
    return {
        "precedence_keys": list(REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS),
        "prefer_field": "fallback_family_used",
        "fallback_field": REALIZATION_FALLBACK_FAMILY_FIELD,
        "projector": "project_replay_fallback_family_from_fem",
        "read_side_only": True,
    }


def project_replay_fallback_family_from_fem(fem: Mapping[str, Any]) -> str | None:
    """Project golden replay ``fallback_family`` from FEM with diegetic-first preference.

    Read-side only: prefers ``fallback_family_used`` (diegetic/template taxonomy)
    and uses ``realization_fallback_family`` (governed provenance) only when the
    diegetic key is absent or null. Returns ``None`` when neither field is present.
    See :func:`dual_fallback_family_replay_precedence_surface`.
    """
    return _first_present(fem, REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS)


def _fem_has_any_key(fem: Mapping[str, Any], keys: tuple[str, ...]) -> bool:
    return any(key in fem for key in keys)


def _fem_dual_fallback_family_present(fem: Mapping[str, Any]) -> bool:
    return _fem_has_any_key(fem, REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS)


def _resolve_route_kind(
    *,
    social_contract_trace: Mapping[str, Any],
    resolution_compact: Mapping[str, Any] | None,
    resolution: Mapping[str, Any],
) -> Any:
    route_kind = _first_present(social_contract_trace, ("route_selected",))
    if route_kind is None and isinstance(resolution_compact, Mapping):
        route_kind = resolution_compact.get("kind")
    if route_kind is None:
        route_kind = resolution.get("kind")
    return route_kind


def _resolve_selected_speaker_id(
    *,
    social_contract_trace: Mapping[str, Any],
    snap: Mapping[str, Any],
    social: Mapping[str, Any],
) -> tuple[Any, str | None]:
    selected_speaker_id = _first_present(
        social_contract_trace,
        ("final_reply_owner", "reply_owner_actor_id", "visible_grounded_speaker"),
    )
    selected_speaker_source = "turn_trace.social_contract_trace" if selected_speaker_id else None
    if selected_speaker_id is None:
        selected_speaker_id = latest_target_id(snap)
        selected_speaker_source = latest_target_source(snap)
    if selected_speaker_id is None:
        selected_speaker_id = social.get("npc_id")
        selected_speaker_source = "resolution.social.npc_id" if selected_speaker_id else None
    return selected_speaker_id, selected_speaker_source


def _resolve_fallback_family(
    fem: Mapping[str, Any],
    runtime_lineage_events: list[Mapping[str, Any]],
) -> Any:
    fallback_family = project_replay_fallback_family_from_fem(fem)
    if fallback_family is None:
        fallback_family = _project_replay_fallback_family(fem, runtime_lineage_events)
    return fallback_family


def _raw_presence_key_for_spec(spec: _ProtectedExtractionSpec) -> str:
    return spec.path


def _raw_presence_for_protected_spec(
    spec: _ProtectedExtractionSpec,
    *,
    fem: Mapping[str, Any],
    route_kind: Any,
    selected_speaker_id: Any,
    payload: Mapping[str, Any],
    trace: Mapping[str, Any],
    canonical_entry: Mapping[str, Any],
    turn_trace: Mapping[str, Any],
    social_contract_trace: Mapping[str, Any],
) -> bool | None:
    """Return raw presence bool for a protected spec, or None when not tracked."""
    if spec.raw_presence == "none":
        return None
    if spec.raw_presence == "route":
        return route_kind is not None or _has_path(payload, "resolution.kind") or _has_path(
            trace,
            "turn_trace.social_contract_trace.route_selected",
        )
    if spec.raw_presence == "speaker":
        return selected_speaker_id is not None
    if spec.raw_presence == "fem_key":
        keys = spec.fem_source_keys or (spec.path,)
        return _fem_has_any_key(fem, keys)
    if spec.raw_presence == "fem_dual_family":
        return _fem_dual_fallback_family_present(fem)
    return None


def _normalized_presence_for_protected_spec(
    spec: _ProtectedExtractionSpec,
    *,
    fem_normalized: Mapping[str, Any],
) -> bool | None:
    """Return normalized presence bool for a protected spec, or None when not tracked."""
    if not spec.normalized_presence:
        return None
    if spec.raw_presence == "fem_dual_family":
        return _fem_dual_fallback_family_present(fem_normalized)
    if spec.raw_presence == "fem_key":
        keys = spec.fem_source_keys or (spec.path,)
        return _fem_has_any_key(fem_normalized, keys)
    return None


def _missing_source_by_field_from_presence(
    raw_signal_presence: Mapping[str, bool],
    normalized_signal_presence: Mapping[str, bool],
) -> dict[str, str]:
    missing_source_by_field: dict[str, str] = {}
    for field, raw_present in raw_signal_presence.items():
        if raw_present is True and field in normalized_signal_presence and normalized_signal_presence[field] is False:
            missing_source_by_field[field] = "normalized_view_missing_raw_present"
        elif raw_present is True:
            missing_source_by_field[field] = "projection_missing_raw_present"
        elif raw_present is False:
            missing_source_by_field[field] = "runtime_missing_raw_absent"
    return missing_source_by_field


def _unavailable_paths_for_projection(
    *,
    protected_flat: Mapping[str, Any],
    trace_observed: Mapping[str, Any],
) -> list[str]:
    unavailable: list[str] = []
    for spec in _PROTECTED_EXTRACTION_SPECS.values():
        if not spec.unavailable_key:
            continue
        key = spec.unavailable_key
        if protected_flat.get(key) is None:
            unavailable.append(key)
    trace = trace_observed if isinstance(trace_observed, Mapping) else {}
    for unavailable_key in _TRACE_CONTAINER_UNAVAILABLE_KEYS:
        container_name = unavailable_key.removeprefix("trace.")
        container = trace.get(container_name) if isinstance(trace, Mapping) else None
        if not container:
            unavailable.append(unavailable_key)
    return sorted(set(unavailable))


@dataclass(frozen=True)
class _ProjectionStatus:
    """Registry-informed presence outputs for one projected observed turn."""

    raw_signal_presence: dict[str, bool]
    normalized_signal_presence: dict[str, bool]
    missing_source_by_field: dict[str, str]
    unavailable: list[str]


def _build_projection_status(
    *,
    fem: Mapping[str, Any],
    fem_normalized: Mapping[str, Any],
    route_kind: Any,
    selected_speaker_id: Any,
    payload: Mapping[str, Any],
    trace: Mapping[str, Any],
    canonical_entry: Mapping[str, Any],
    turn_trace: Mapping[str, Any],
    social_contract_trace: Mapping[str, Any],
    protected_flat: Mapping[str, Any],
    trace_observed: Mapping[str, Any],
) -> _ProjectionStatus:
    """Build raw/normalized presence, missing-source routing, and unavailable in one pass."""
    raw_signal_presence: dict[str, bool] = {}
    normalized_signal_presence: dict[str, bool] = {}
    trace_containers = {
        "canonical_entry": canonical_entry,
        "turn_trace": turn_trace,
        "social_contract_trace": social_contract_trace,
    }

    for spec in _PROTECTED_EXTRACTION_SPECS.values():
        raw_value = _raw_presence_for_protected_spec(
            spec,
            fem=fem,
            route_kind=route_kind,
            selected_speaker_id=selected_speaker_id,
            payload=payload,
            trace=trace,
            canonical_entry=canonical_entry,
            turn_trace=turn_trace,
            social_contract_trace=social_contract_trace,
        )
        if raw_value is not None:
            raw_signal_presence[_raw_presence_key_for_spec(spec)] = raw_value

        normalized_value = _normalized_presence_for_protected_spec(spec, fem_normalized=fem_normalized)
        if normalized_value is not None:
            normalized_signal_presence[spec.path] = normalized_value

    for presence_key, container_key in _TRACE_CONTAINER_RAW_PRESENCE:
        raw_signal_presence[presence_key] = bool(trace_containers[container_key])

    for supporting in _SUPPORTING_RAW_PRESENCE_SPECS:
        raw_signal_presence[supporting.key] = _fem_has_any_key(fem, supporting.fem_source_keys)
        if supporting.key in raw_signal_presence:
            normalized_signal_presence[supporting.key] = _fem_has_any_key(
                fem_normalized,
                supporting.fem_source_keys,
            )

    missing_source_by_field = _missing_source_by_field_from_presence(
        raw_signal_presence,
        normalized_signal_presence,
    )
    unavailable = _unavailable_paths_for_projection(
        protected_flat=protected_flat,
        trace_observed=trace_observed,
    )
    return _ProjectionStatus(
        raw_signal_presence=raw_signal_presence,
        normalized_signal_presence=normalized_signal_presence,
        missing_source_by_field=missing_source_by_field,
        unavailable=unavailable,
    )


# Flat protected paths projected by :func:`_project_flat_protected_observed_fields`.
_HANDLED_FLAT_PROTECTED_SOURCES: frozenset[str] = frozenset(
    {
        "resolution",
        "route",
        "speaker",
        "fem_flat",
        "sanitizer_trace",
        "sanitizer_lineage",
        "sanitizer_lineage_legacy",
        "fem_opening_bucket",
        "fallback_family",
        "final_text",
        "scaffold",
    }
)

# Dotted protected paths nested under ``observed["trace"]`` (not flat keys).
_TRACE_NEST_PROTECTED_SOURCES: frozenset[str] = frozenset({"trace_leaf"})


def _validate_protected_projection_sources() -> None:
    for path, spec in _PROTECTED_EXTRACTION_SPECS.items():
        if spec.source in _HANDLED_FLAT_PROTECTED_SOURCES:
            if "." in path:
                raise AssertionError(
                    f"flat protected projection source {spec.source!r} must not use dotted path {path!r}"
                )
            continue
        if spec.source in _TRACE_NEST_PROTECTED_SOURCES:
            if not spec.trace_container:
                raise AssertionError(
                    f"trace_leaf protected path {path!r} must declare trace_container"
                )
            continue
        raise AssertionError(
            f"protected extraction source {spec.source!r} for {path!r} is not handled by "
            "flat projection or trace nest"
        )


_validate_protected_projection_sources()


def protected_observation_extraction_source_by_path() -> dict[str, str]:
    """Return ``path → extraction source`` from the protected extraction registry."""
    return {path: spec.source for path, spec in _PROTECTED_EXTRACTION_SPECS.items()}


def _project_flat_protected_observed_fields(
    *,
    resolution: Mapping[str, Any],
    route_kind: Any,
    selected_speaker_id: Any,
    fem: Mapping[str, Any],
    fem_flat: Mapping[str, Any],
    sanitizer_trace_flat: Mapping[str, Any],
    sanitizer_lineage_flat: Mapping[str, Any],
    fallback_family: Any,
    final_text: str,
) -> dict[str, Any]:
    """Project registry-backed flat protected observation keys into one dict."""
    fem_shaped = _observed_fem_flat_values(fem_flat)
    out: dict[str, Any] = {}
    for path, spec in _PROTECTED_EXTRACTION_SPECS.items():
        if "." in path:
            continue
        if spec.source == "resolution":
            out[path] = resolution.get("kind")
        elif spec.source == "route":
            out[path] = route_kind
        elif spec.source == "speaker":
            out[path] = selected_speaker_id
        elif spec.source == "fem_flat":
            out[path] = fem_shaped.get(path)
        elif spec.source == "sanitizer_trace":
            out[path] = sanitizer_trace_flat.get(path)
        elif spec.source in ("sanitizer_lineage", "sanitizer_lineage_legacy"):
            out[path] = sanitizer_lineage_flat.get(path)
        elif spec.source == "fem_opening_bucket":
            out[path] = read_opening_fallback_owner_bucket_for_replay(fem)
        elif spec.source == "fallback_family":
            out[path] = fallback_family
        elif spec.source == "final_text":
            out[path] = final_text
        elif spec.source == "scaffold":
            out[path] = final_text_has_scaffold_leakage(final_text)
        else:
            raise AssertionError(
                f"unhandled flat protected extraction source {spec.source!r} for {path!r}"
            )
    return out


def project_turn_observation(turn_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Project chat payload + snapshot into a golden replay observation dict.

    ``turn_payload`` keys:
    - ``scenario_id`` (str, required)
    - ``snap`` (mapping, required)
    - ``payload`` (mapping, required)
    - ``replay_identity`` (optional mapping with source_path/branch_id/turn_id)
    """
    scenario_id = str(turn_payload.get("scenario_id") or "")
    snap_raw = turn_payload.get("snap")
    payload_raw = turn_payload.get("payload")
    snap = dict(snap_raw) if isinstance(snap_raw, Mapping) else {}
    payload = dict(payload_raw) if isinstance(payload_raw, Mapping) else {}
    replay_identity = turn_payload.get("replay_identity")
    replay_identity_map = replay_identity if isinstance(replay_identity, Mapping) else None

    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), Mapping) else {}
    social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else {}
    fem = read_fem_from_turn_for_replay(payload)
    fem_normalized = normalize_fem_for_replay_acceptance(fem)
    fem_flat = _extract_fem_flat_observed_fields(fem)
    runtime_lineage_events = _runtime_lineage_events_from_payload(payload, fem)
    emission_debug_lane = read_emission_debug_lane_for_replay(payload)
    trace = _trace_from_payload_or_snapshot(payload, snap)
    turn_trace = trace.get("turn_trace") if isinstance(trace.get("turn_trace"), Mapping) else {}
    social_contract_trace = (
        turn_trace.get("social_contract_trace")
        if isinstance(turn_trace.get("social_contract_trace"), Mapping)
        else {}
    )
    canonical_entry = trace.get("canonical_entry") if isinstance(trace.get("canonical_entry"), Mapping) else {}
    resolution_compact = (
        (snap.get("debug") or {}).get("resolution_compact")
        if isinstance(snap.get("debug"), Mapping)
        else None
    )

    route_kind = _resolve_route_kind(
        social_contract_trace=social_contract_trace,
        resolution_compact=resolution_compact if isinstance(resolution_compact, Mapping) else None,
        resolution=resolution,
    )

    selected_speaker_id, selected_speaker_source = _resolve_selected_speaker_id(
        social_contract_trace=social_contract_trace,
        snap=snap,
        social=social,
    )

    response_delta_checked = _first_present(fem, ("response_delta_checked",))
    response_delta_failed = _first_present(fem, ("response_delta_failed",))
    response_delta_repaired = _first_present(fem, ("response_delta_repaired",))
    response_delta_kind = _first_present(fem, ("response_delta_kind", "response_delta_kind_detected"))
    response_delta_echo_overlap_ratio = _first_present(fem, ("response_delta_echo_overlap_ratio",))
    response_delta_echo_overlap_band = _echo_overlap_band(response_delta_echo_overlap_ratio)
    response_delta_skip_reason = _first_present(fem, ("response_delta_skip_reason",))
    response_delta_trigger_source = _first_present(fem, ("response_delta_trigger_source",))
    post_gate_mutation_detected = _first_present(fem, ("post_gate_mutation_detected",))
    fallback_family = _resolve_fallback_family(fem, runtime_lineage_events)
    stage_diff = _find_nested_mapping(payload, "stage_diff_telemetry")
    sanitizer_debug = _find_nested_list(payload, "sanitizer_debug")
    sanitizer_trace = _find_nested_mapping(payload, "sanitizer_trace")
    sanitizer_mode = _first_present(
        sanitizer_trace,
        ("sanitizer_boundary_mode", "mode"),
    ) or lookup_observation_path(payload, "gm_output.metadata.sanitizer_boundary_mode")
    sanitizer_event_count = len(sanitizer_debug) if sanitizer_debug else None
    sanitizer_changed_count, sanitizer_dropped_count = _sanitizer_debug_change_counts(sanitizer_debug)
    sanitizer_rewrite_used = bool(sanitizer_changed_count) if sanitizer_changed_count is not None else None
    sanitizer_trace_flat = _extract_sanitizer_trace_flat_observed_fields(sanitizer_trace)
    sanitizer_lineage_flat = _extract_sanitizer_lineage_observed_fields(
        sanitizer_trace,
        lineage_context={
            "sanitizer_mode": sanitizer_mode,
            "sanitizer_changed_count": sanitizer_changed_count,
            "sanitizer_dropped_count": sanitizer_dropped_count,
            "sanitizer_empty_fallback_used": sanitizer_trace_flat.get("sanitizer_empty_fallback_used"),
        },
    )
    interaction_continuity_validation = _find_nested_mapping(payload, "interaction_continuity_validation")

    final_text = str(snap.get("gm_text") or "")
    protected_flat = _project_flat_protected_observed_fields(
        resolution=resolution,
        route_kind=route_kind,
        selected_speaker_id=selected_speaker_id,
        fem=fem,
        fem_flat=fem_flat,
        sanitizer_trace_flat=sanitizer_trace_flat,
        sanitizer_lineage_flat=sanitizer_lineage_flat,
        fallback_family=fallback_family,
        final_text=final_text,
    )
    trace_observed = {
        "canonical_entry_path": trace.get("canonical_entry_path"),
        "canonical_entry_reason": trace.get("canonical_entry_reason"),
        "canonical_entry_target_actor_id": trace.get("canonical_entry_target_actor_id"),
        "canonical_entry": dict(canonical_entry),
        "turn_trace": dict(turn_trace),
        "social_contract_trace": dict(social_contract_trace),
    }
    projection_status = _build_projection_status(
        fem=fem,
        fem_normalized=fem_normalized,
        route_kind=route_kind,
        selected_speaker_id=selected_speaker_id,
        payload=payload,
        trace=trace,
        canonical_entry=canonical_entry,
        turn_trace=turn_trace,
        social_contract_trace=social_contract_trace,
        protected_flat=protected_flat,
        trace_observed=trace_observed,
    )
    observed = {
        "scenario_id": scenario_id,
        "turn_index": snap.get("turn_index"),
        "player_text": snap.get("player_text"),
        "selected_speaker_source": selected_speaker_source,
        **protected_flat,
        "response_delta_checked": response_delta_checked,
        "response_delta_failed": response_delta_failed,
        "response_delta_repaired": response_delta_repaired,
        "response_delta_kind": response_delta_kind,
        "response_delta_echo_overlap_ratio": response_delta_echo_overlap_ratio,
        "response_delta_echo_overlap_band": response_delta_echo_overlap_band,
        "response_delta_skip_reason": response_delta_skip_reason,
        "response_delta_trigger_source": response_delta_trigger_source,
        "post_gate_mutation_detected": post_gate_mutation_detected,
        "strict_social_active": _first_present(fem, ("strict_social_active",)),
        "speaker_contract_enforcement_reason": _first_present(fem, ("speaker_contract_enforcement_reason",)),
        "fallback_behavior_repaired": _first_present(fem, ("fallback_behavior_repaired",)),
        "fallback_behavior_repair_kind": _first_present(fem, ("fallback_behavior_repair_kind",)),
        "fallback_behavior_repair_mode": _first_present(fem, ("fallback_behavior_repair_mode",)),
        "narrative_authenticity_repair_mode": _first_present(fem, ("narrative_authenticity_repair_mode",)),
        "stage_diff": stage_diff,
        "sanitizer_mode": sanitizer_mode,
        "sanitizer_event_count": sanitizer_event_count,
        "sanitizer_changed_count": sanitizer_changed_count,
        "sanitizer_rewrite_used": sanitizer_rewrite_used,
        "sanitizer_leak_terms": ["scaffold_leakage"] if protected_flat.get("scaffold_leakage") else [],
        "final_text_hash": golden_text_hash(final_text),
        "trace": trace_observed,
        "snapshot_summary": compact_snapshot_summary(snap),
        "raw_signal_presence": projection_status.raw_signal_presence,
        "normalized_signal_presence": projection_status.normalized_signal_presence,
        "missing_source_by_field": projection_status.missing_source_by_field,
        "fem_raw_keys": sorted(str(k) for k in fem.keys()),
        "fem_normalized_keys": sorted(str(k) for k in fem_normalized.keys()),
        "emission_debug_lane_keys": sorted(str(k) for k in emission_debug_lane.keys()),
        "runtime_lineage_events": runtime_lineage_events,
        "interaction_continuity_validation": interaction_continuity_validation,
    }
    if replay_identity_map:
        for key in ("source_path", "branch_id", "turn_id"):
            value = replay_identity_map.get(key)
            if value is not None and str(value).strip():
                observed[key] = str(value)
    observed["unavailable"] = projection_status.unavailable
    return observed
