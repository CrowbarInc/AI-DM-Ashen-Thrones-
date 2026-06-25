"""CF3 — raw vs normalized FEM contract for protected replay projection.

Documents which protected fields are FEM-backed, how raw and normalized FEM
relate, and which presence surfaces track each representation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from game.final_emission_replay_projection import normalize_fem_for_replay_acceptance
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD

from tests.helpers.golden_replay_projection_extractors import _PROTECTED_EXTRACTION_SPECS

FEMBackedClassification = Literal[
    "raw_projected",
    "raw_and_normalized_presence",
    "derived_from_raw_fem",
]

_NORMALIZATION_OWNER = "game.final_emission_meta.normalize_final_emission_meta_for_observability"
_REPLAY_NORMALIZATION_ADAPTER = "game.final_emission_replay_projection.normalize_fem_for_replay_acceptance"
_PROJECTION_OWNER = "tests.helpers.golden_replay_projection_extractors._extract_fem_flat_observed_fields"
_PRESENCE_OWNER = "tests.helpers.golden_replay_projection_extractors._build_projection_status"


@dataclass(frozen=True)
class FemBackedFieldRow:
    protected_field: str
    raw_fem_keys: tuple[str, ...]
    normalized_presence_tracked: bool
    raw_presence_kind: str
    projection_owner: str
    normalization_owner: str
    test_owner: str
    classification: FemBackedClassification
    notes: str


def _fem_keys_for_spec(path: str) -> tuple[str, ...]:
    spec = _PROTECTED_EXTRACTION_SPECS[path]
    if spec.source == "fallback_family":
        return ("fallback_family_used", REALIZATION_FALLBACK_FAMILY_FIELD)
    if spec.source == "fem_opening_bucket":
        return ("opening_fallback_owner_bucket",)
    return spec.fem_source_keys or (path,)


def _classification_for_spec(path: str, *, normalized_presence: bool) -> FemBackedClassification:
    spec = _PROTECTED_EXTRACTION_SPECS[path]
    if spec.source == "fem_opening_bucket":
        return "derived_from_raw_fem"
    if normalized_presence:
        return "raw_and_normalized_presence"
    return "raw_projected"


def _test_owner_for_path(path: str) -> str:
    if path == "fallback_family":
        return "test_cf1_fallback_family_precedence.py"
    if path.startswith("opening"):
        return "test_golden_replay_fallback_opening_projection.py"
    if path.startswith("visibility"):
        return "test_golden_replay_fallback_visibility_projection.py"
    if path.startswith("sealed"):
        return "test_golden_replay_fallback_sealed_projection.py"
    if path.startswith("upstream_prepared"):
        return "test_golden_replay_fallback_upstream_projection.py"
    return "test_final_emission_meta.py"


def fem_backed_protected_field_paths() -> tuple[str, ...]:
    """Return sorted protected paths whose extraction source reads FEM."""
    return tuple(
        sorted(
            path
            for path, spec in _PROTECTED_EXTRACTION_SPECS.items()
            if spec.source in {"fem_flat", "fallback_family", "fem_opening_bucket"}
        )
    )


def build_fem_backed_field_matrix() -> tuple[FemBackedFieldRow, ...]:
    """Return one contract row per FEM-backed protected observation path."""
    rows: list[FemBackedFieldRow] = []
    for path in fem_backed_protected_field_paths():
        spec = _PROTECTED_EXTRACTION_SPECS[path]
        keys = _fem_keys_for_spec(path)
        rows.append(
            FemBackedFieldRow(
                protected_field=path,
                raw_fem_keys=keys,
                normalized_presence_tracked=spec.normalized_presence,
                raw_presence_kind=spec.raw_presence,
                projection_owner=(
                    "read_opening_fallback_owner_bucket_for_replay"
                    if spec.source == "fem_opening_bucket"
                    else "_project_flat_protected_observed_fields / _resolve_fallback_family"
                ),
                normalization_owner=_NORMALIZATION_OWNER,
                test_owner=_test_owner_for_path(path),
                classification=_classification_for_spec(path, normalized_presence=spec.normalized_presence),
                notes=(
                    "Projected value from raw FEM; dual-family presence uses both keys"
                    if spec.source == "fallback_family"
                    else (
                        "Derived via opening_fallback_owner_bucket_from_meta; not a direct FEM key"
                        if spec.source == "fem_opening_bucket"
                        else "Projected via _first_present on raw FEM keys"
                    )
                ),
            )
        )
    return tuple(rows)


def fem_backed_field_matrix_by_path() -> dict[str, FemBackedFieldRow]:
    return {row.protected_field: row for row in build_fem_backed_field_matrix()}


def normalize_fem_for_replay(raw: dict[str, object]) -> dict[str, object]:
    """Canonical replay acceptance normalization entry (adapter + meta owner)."""
    return normalize_fem_for_replay_acceptance(raw)
