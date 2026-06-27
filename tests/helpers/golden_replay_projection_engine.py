"""Protected field projection execution for golden replay observations."""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_replay_projection import read_opening_fallback_owner_bucket_for_replay

from tests.helpers.golden_replay_projection_fields import (
    _first_present,
    final_text_has_scaffold_leakage,
)
from tests.helpers.golden_replay_projection_registry import (
    _FEM_FLAT_OBSERVED_EXTRACTORS,
    _PROTECTED_EXTRACTION_SPECS,
    _SANITIZER_LINEAGE_OBSERVED_EXTRACTORS,
    _SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS,
    _flat_extractor_source_keys,
    protected_flat_extraction_sources,
    protected_trace_extraction_sources,
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


def _sanitizer_lineage_field(
    sanitizer_trace: Mapping[str, Any] | None,
    key: str,
    fallback: Any = None,
) -> Any:
    if isinstance(sanitizer_trace, Mapping) and key in sanitizer_trace:
        return sanitizer_trace.get(key)
    return fallback


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


def _validate_protected_projection_sources() -> None:
    flat_sources = protected_flat_extraction_sources()
    trace_sources = protected_trace_extraction_sources()
    for path, spec in _PROTECTED_EXTRACTION_SPECS.items():
        if spec.source in flat_sources:
            if "." in path:
                raise AssertionError(
                    f"flat protected projection source {spec.source!r} must not use dotted path {path!r}"
                )
            continue
        if spec.source in trace_sources:
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
