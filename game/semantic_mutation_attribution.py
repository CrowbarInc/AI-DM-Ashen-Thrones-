"""Semantic mutation evidence reconciliation helpers.

Read-side diagnostics can see the same semantic text change through several
surfaces.  Prefer recorded write-site evidence over projection-derived guesses:

1. ``semantic_mutation_write_sites``
2. runtime lineage mutation events
3. fallback provenance
4. sanitizer lineage
5. FEM mutation lineage
6. stage-diff telemetry
7. projection-derived inference

This module is diagnostic-only.  It does not instrument new write sites, mutate
player-facing text, or promote replay schema fields.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, NamedTuple


SEMANTIC_MUTATION_WRITE_SITE_FAMILIES: frozenset[str] = frozenset(
    {
        "prompt",
        "policy",
        "sanitizer",
        "repair",
        "fallback",
        "final_emission",
    }
)

SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE: tuple[str, ...] = (
    "write_site",
    "runtime_lineage",
    "fallback_provenance",
    "sanitizer_lineage",
    "fem_mutation_lineage",
    "stage_diff",
    "projection_inference",
)

SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT: dict[str, Any] = {
    "name": "semantic_mutation_authoritative_attribution",
    "write_site_families": tuple(sorted(SEMANTIC_MUTATION_WRITE_SITE_FAMILIES)),
    "evidence_precedence": SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE,
    "guarantees": (
        "exactly one authoritative mutation owner per emitted mutation",
        "authoritative owner must come from precedence rules",
        "candidate-only evidence can never become authoritative",
        "projection inference is only used when no stronger evidence exists",
        "authoritative evidence must never be overwritten by weaker evidence",
    ),
}


class SemanticMutationAttribution(NamedTuple):
    authoritative_mutation_owner: str | None
    authoritative_mutation_family: str | None
    authoritative_write_site: str | None
    authoritative_evidence_source: str | None
    confidence: str
    used_projection_inference: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "authoritative_mutation_owner": self.authoritative_mutation_owner,
            "authoritative_mutation_family": self.authoritative_mutation_family,
            "authoritative_write_site": self.authoritative_write_site,
            "authoritative_evidence_source": self.authoritative_evidence_source,
            "authoritative_mutation_confidence": self.confidence,
            "used_projection_inference": self.used_projection_inference,
        }


NO_SEMANTIC_MUTATION_ATTRIBUTION = SemanticMutationAttribution(
    authoritative_mutation_owner=None,
    authoritative_mutation_family=None,
    authoritative_write_site=None,
    authoritative_evidence_source=None,
    confidence="none",
    used_projection_inference=False,
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_iterable_mappings(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _write_site_label(row: Mapping[str, Any]) -> str | None:
    file_name = _clean(row.get("write_site_file"))
    function_name = _clean(row.get("write_site_function"))
    if file_name and function_name:
        return f"{file_name}:{function_name}"
    return file_name or function_name


def selected_semantic_mutation_write_site(
    rows: Any,
    *,
    family: str | None = None,
) -> Mapping[str, Any] | None:
    """Return the first selected non-candidate semantic mutation write-site row."""
    for row in _as_iterable_mappings(rows):
        if row.get("candidate_only") is True:
            continue
        if row.get("selected_active_stream") is not True:
            continue
        if family is not None and _clean(row.get("write_site_family")) != family:
            continue
        return row
    return None


def semantic_mutation_write_site_label(row: Mapping[str, Any] | None) -> str | None:
    """Return the governed display label for a semantic mutation write-site row."""
    return _write_site_label(_as_mapping(row))


def _first_explicit_write_site(fem: Mapping[str, Any]) -> SemanticMutationAttribution | None:
    for row in _as_iterable_mappings(fem.get("semantic_mutation_write_sites")):
        if selected_semantic_mutation_write_site([row]) is None:
            continue
        owner = _clean(row.get("owner")) or _clean(row.get("write_site_file"))
        family = (
            _clean(row.get("write_site_family"))
            or _clean(row.get("fallback_family"))
            or _clean(row.get("repair_family"))
        )
        write_site = _write_site_label(row)
        if owner or family or write_site:
            return SemanticMutationAttribution(
                authoritative_mutation_owner=owner,
                authoritative_mutation_family=family,
                authoritative_write_site=write_site,
                authoritative_evidence_source="write_site",
                confidence="high",
                used_projection_inference=False,
            )
    return None


def _first_runtime_mutation(runtime_lineage: Any) -> SemanticMutationAttribution | None:
    for event in _as_iterable_mappings(runtime_lineage):
        if _clean(event.get("event_kind")) != "mutation":
            continue
        owner = _clean(event.get("owner"))
        family = _clean(event.get("mutation_kind")) or _clean(event.get("stage"))
        if owner or family:
            return SemanticMutationAttribution(
                authoritative_mutation_owner=owner,
                authoritative_mutation_family=family,
                authoritative_write_site=None,
                authoritative_evidence_source="runtime_lineage",
                confidence="medium",
                used_projection_inference=False,
            )
    return None


def _fallback_provenance_attribution(fallback_provenance: Mapping[str, Any]) -> SemanticMutationAttribution | None:
    if not fallback_provenance:
        return None
    owner = (
        _clean(fallback_provenance.get("owner"))
        or _clean(fallback_provenance.get("selection_owner"))
        or _clean(fallback_provenance.get("packager"))
        or "game.fallback_provenance_debug"
    )
    family = _clean(fallback_provenance.get("fallback_family")) or _clean(fallback_provenance.get("source")) or "fallback"
    return SemanticMutationAttribution(
        authoritative_mutation_owner=owner,
        authoritative_mutation_family=family,
        authoritative_write_site=None,
        authoritative_evidence_source="fallback_provenance",
        confidence="medium",
        used_projection_inference=False,
    )


def _sanitizer_lineage_attribution(sanitizer_trace: Mapping[str, Any]) -> SemanticMutationAttribution | None:
    if not sanitizer_trace:
        return None
    changed = sanitizer_trace.get("sanitizer_lineage_changed_count")
    empty = sanitizer_trace.get("sanitizer_lineage_empty_fallback_used") is True or sanitizer_trace.get("sanitizer_empty_fallback_used") is True
    strict = sanitizer_trace.get("sanitizer_strict_social_fallback_used") is True
    if not empty and not strict and not (isinstance(changed, (int, float)) and not isinstance(changed, bool) and changed > 0):
        return None
    owner = (
        _clean(sanitizer_trace.get("sanitizer_empty_fallback_owner"))
        or _clean(sanitizer_trace.get("sanitizer_strict_social_selection_owner"))
        or "game.output_sanitizer"
    )
    family = "sanitizer_empty_output" if empty else "sanitizer_mutation"
    return SemanticMutationAttribution(
        authoritative_mutation_owner=owner,
        authoritative_mutation_family=family,
        authoritative_write_site=None,
        authoritative_evidence_source="sanitizer_lineage",
        confidence="medium",
        used_projection_inference=False,
    )


def _fem_mutation_lineage_attribution(fem: Mapping[str, Any]) -> SemanticMutationAttribution | None:
    raw = fem.get("final_emission_mutation_lineage")
    if not isinstance(raw, list):
        return None
    first = next((_clean(item) for item in raw if _clean(item)), None)
    if not first:
        return None
    owner = "game.output_sanitizer" if "sanitizer" in first else "game.final_emission_gate"
    return SemanticMutationAttribution(
        authoritative_mutation_owner=owner,
        authoritative_mutation_family=first,
        authoritative_write_site=None,
        authoritative_evidence_source="fem_mutation_lineage",
        confidence="low",
        used_projection_inference=False,
    )


def _stage_diff_attribution(stage_diff: Mapping[str, Any]) -> SemanticMutationAttribution | None:
    if not stage_diff:
        return None
    transitions = stage_diff.get("transitions")
    if not _as_iterable_mappings(transitions):
        return None
    return SemanticMutationAttribution(
        authoritative_mutation_owner="game.stage_diff_telemetry",
        authoritative_mutation_family="stage_diff",
        authoritative_write_site=None,
        authoritative_evidence_source="stage_diff",
        confidence="low",
        used_projection_inference=False,
    )


def _projection_attribution(projection_metadata: Mapping[str, Any]) -> SemanticMutationAttribution | None:
    owner = _clean(projection_metadata.get("first_semantic_mutation_owner"))
    family = _clean(projection_metadata.get("first_semantic_mutation_bucket"))
    source = _clean(projection_metadata.get("first_semantic_mutation_source"))
    if not owner and not family and not source:
        return None
    return SemanticMutationAttribution(
        authoritative_mutation_owner=owner,
        authoritative_mutation_family=family or source,
        authoritative_write_site=None,
        authoritative_evidence_source="projection_inference",
        confidence="inferred",
        used_projection_inference=True,
    )


def _evidence_by_source(
    *,
    fem: Mapping[str, Any],
    runtime_lineage: Any,
    sanitizer_trace: Mapping[str, Any],
    fallback_provenance: Mapping[str, Any],
    projection_metadata: Mapping[str, Any],
    stage_diff: Mapping[str, Any],
) -> dict[str, SemanticMutationAttribution]:
    evidence = {
        "write_site": _first_explicit_write_site(fem),
        "runtime_lineage": _first_runtime_mutation(runtime_lineage),
        "fallback_provenance": _fallback_provenance_attribution(fallback_provenance),
        "sanitizer_lineage": _sanitizer_lineage_attribution(sanitizer_trace),
        "fem_mutation_lineage": _fem_mutation_lineage_attribution(fem),
        "stage_diff": _stage_diff_attribution(stage_diff),
        "projection_inference": _projection_attribution(projection_metadata),
    }
    return {source: value for source, value in evidence.items() if value is not None}


def _attribution_from_mapping(value: Mapping[str, Any]) -> SemanticMutationAttribution:
    return SemanticMutationAttribution(
        authoritative_mutation_owner=_clean(value.get("authoritative_mutation_owner")),
        authoritative_mutation_family=_clean(value.get("authoritative_mutation_family")),
        authoritative_write_site=_clean(value.get("authoritative_write_site")),
        authoritative_evidence_source=_clean(value.get("authoritative_evidence_source")),
        confidence=_clean(value.get("authoritative_mutation_confidence")) or "none",
        used_projection_inference=bool(value.get("used_projection_inference")),
    )


def _has_authoritative_value(attribution: SemanticMutationAttribution) -> bool:
    return any(
        (
            attribution.authoritative_mutation_owner,
            attribution.authoritative_mutation_family,
            attribution.authoritative_write_site,
            attribution.authoritative_evidence_source,
        )
    )


def validate_semantic_mutation_contract(
    *,
    fem: Mapping[str, Any] | None = None,
    runtime_lineage: Any = None,
    sanitizer_trace: Mapping[str, Any] | None = None,
    fallback_provenance: Mapping[str, Any] | None = None,
    projection_metadata: Mapping[str, Any] | None = None,
    stage_diff: Mapping[str, Any] | None = None,
    projected_attribution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate diagnostic attribution against the governed compatibility contract.

    The validator is intentionally read-only.  Malformed metadata is reported as
    diagnostics instead of raising so replay/classifier callers can tolerate old
    payloads and still surface compatibility drift.
    """
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    fem_map = _as_mapping(fem)
    sanitizer_map = _as_mapping(sanitizer_trace)
    fallback_map = _as_mapping(fallback_provenance)
    projection_map = _as_mapping(projection_metadata)
    stage_diff_map = _as_mapping(stage_diff)

    raw_write_sites = fem_map.get("semantic_mutation_write_sites")
    write_site_rows = _as_iterable_mappings(raw_write_sites)
    if raw_write_sites is not None and not isinstance(raw_write_sites, list):
        warnings.append(
            {
                "code": "malformed_write_sites",
                "message": "semantic_mutation_write_sites must be a list when present",
            }
        )

    for index, row in enumerate(write_site_rows):
        family = _clean(row.get("write_site_family"))
        if family not in SEMANTIC_MUTATION_WRITE_SITE_FAMILIES:
            errors.append(
                {
                    "code": "invalid_write_site_family",
                    "index": index,
                    "value": family,
                    "allowed": tuple(sorted(SEMANTIC_MUTATION_WRITE_SITE_FAMILIES)),
                }
            )
        selected = row.get("selected_active_stream")
        candidate_only = row.get("candidate_only")
        if selected not in (True, False, None):
            warnings.append(
                {
                    "code": "malformed_selected_active_stream",
                    "index": index,
                    "value": selected,
                }
            )
        if candidate_only not in (True, False, None):
            warnings.append(
                {
                    "code": "malformed_candidate_only",
                    "index": index,
                    "value": candidate_only,
                }
            )
        if candidate_only is True and selected is True:
            errors.append(
                {
                    "code": "candidate_only_selected_active_stream",
                    "index": index,
                    "message": "candidate-only records cannot be selected active-stream evidence",
                }
            )

    evidence = _evidence_by_source(
        fem=fem_map,
        runtime_lineage=runtime_lineage,
        sanitizer_trace=sanitizer_map,
        fallback_provenance=fallback_map,
        projection_metadata=projection_map,
        stage_diff=stage_diff_map,
    )
    expected = reconcile_semantic_mutation_owner(
        fem=fem_map,
        runtime_lineage=runtime_lineage,
        sanitizer_trace=sanitizer_map,
        fallback_provenance=fallback_map,
        projection_metadata=projection_map,
        stage_diff=stage_diff_map,
    )
    actual = (
        _attribution_from_mapping(projected_attribution)
        if isinstance(projected_attribution, Mapping)
        else expected
    )

    expected_source = expected.authoritative_evidence_source
    actual_source = actual.authoritative_evidence_source
    if actual_source not in (None, *SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE):
        errors.append(
            {
                "code": "invalid_authoritative_evidence_source",
                "value": actual_source,
                "allowed": SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE,
            }
        )
    if actual_source != expected_source:
        errors.append(
            {
                "code": "invalid_precedence",
                "expected": expected_source,
                "actual": actual_source,
                "available_evidence_sources": tuple(evidence.keys()),
            }
        )
    if actual.authoritative_mutation_owner != expected.authoritative_mutation_owner:
        errors.append(
            {
                "code": "authoritative_owner_mismatch",
                "expected": expected.authoritative_mutation_owner,
                "actual": actual.authoritative_mutation_owner,
            }
        )
    if actual.authoritative_mutation_family != expected.authoritative_mutation_family:
        errors.append(
            {
                "code": "authoritative_family_mismatch",
                "expected": expected.authoritative_mutation_family,
                "actual": actual.authoritative_mutation_family,
            }
        )
    if actual.authoritative_write_site != expected.authoritative_write_site:
        errors.append(
            {
                "code": "authoritative_write_site_mismatch",
                "expected": expected.authoritative_write_site,
                "actual": actual.authoritative_write_site,
            }
        )
    if actual.used_projection_inference != expected.used_projection_inference:
        errors.append(
            {
                "code": "projection_inference_mismatch",
                "expected": expected.used_projection_inference,
                "actual": actual.used_projection_inference,
            }
        )
    if actual.used_projection_inference and expected_source != "projection_inference":
        errors.append(
            {
                "code": "projection_inference_overrode_stronger_evidence",
                "expected": expected_source,
                "actual": actual_source,
            }
        )
    if not evidence and _has_authoritative_value(actual):
        errors.append(
            {
                "code": "authoritative_without_mutation_evidence",
                "actual": actual.as_dict(),
            }
        )
    if expected_source == "write_site":
        selected_rows = [
            row for row in write_site_rows
            if row.get("candidate_only") is not True
            and row.get("selected_active_stream") is True
        ]
        if not selected_rows:
            errors.append(
                {
                    "code": "missing_selected_write_site",
                    "message": "write-site attribution requires selected active-stream evidence",
                }
            )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "contract": dict(SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT),
        "evidence_sources": tuple(evidence.keys()),
        "expected_attribution": expected.as_dict(),
        "actual_attribution": actual.as_dict(),
    }


def reconcile_semantic_mutation_owner(
    *,
    fem: Mapping[str, Any] | None = None,
    runtime_lineage: Any = None,
    sanitizer_trace: Mapping[str, Any] | None = None,
    fallback_provenance: Mapping[str, Any] | None = None,
    projection_metadata: Mapping[str, Any] | None = None,
    stage_diff: Mapping[str, Any] | None = None,
) -> SemanticMutationAttribution:
    """Select the authoritative semantic mutation attribution by precedence."""
    fem_map = _as_mapping(fem)
    candidates = (
        _first_explicit_write_site(fem_map),
        _first_runtime_mutation(runtime_lineage),
        _fallback_provenance_attribution(_as_mapping(fallback_provenance)),
        _sanitizer_lineage_attribution(_as_mapping(sanitizer_trace)),
        _fem_mutation_lineage_attribution(fem_map),
        _stage_diff_attribution(_as_mapping(stage_diff)),
        _projection_attribution(_as_mapping(projection_metadata)),
    )
    for candidate in candidates:
        if candidate is not None:
            return candidate
    return NO_SEMANTIC_MUTATION_ATTRIBUTION


__all__ = [
    "NO_SEMANTIC_MUTATION_ATTRIBUTION",
    "SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT",
    "SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE",
    "SEMANTIC_MUTATION_WRITE_SITE_FAMILIES",
    "SemanticMutationAttribution",
    "reconcile_semantic_mutation_owner",
    "selected_semantic_mutation_write_site",
    "semantic_mutation_write_site_label",
    "validate_semantic_mutation_contract",
]
