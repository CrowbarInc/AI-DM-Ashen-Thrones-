"""Protected observation field registry and drift bucket classification (CE5)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping

from game.output_sanitizer import resembles_serialized_response_payload

MISSING = object()


@dataclass(frozen=True)
class ProtectedObservationField:
    path: str
    drift_bucket: str
    required: bool = False
    description: str = ""
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

def _first_present(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None
