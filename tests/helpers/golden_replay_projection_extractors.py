"""Payload extraction and protected observation projection helpers (CE5)."""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_replay_projection import build_fem_runtime_lineage_events
from game.runtime_lineage_telemetry import normalize_runtime_lineage_events

from tests.debug_trace_utils import latest_compact_debug_trace_entry
from tests.helpers.golden_replay_projection_fallbacks import (
    _fem_dual_fallback_family_present,
    _fem_has_any_key,
)
from tests.helpers.golden_replay_projection_engine import (
    _extract_fem_flat_observed_fields,
    _extract_sanitizer_lineage_observed_fields,
    _extract_sanitizer_trace_flat_observed_fields,
    _observed_fem_flat_values,
    _project_flat_protected_observed_fields,
    _resolve_route_kind,
    _sanitizer_lineage_field,
    _validate_protected_projection_sources,
)
from tests.helpers.golden_replay_projection_registry import (
    _FEM_FLAT_OBSERVED_EXTRACTORS,
    _HANDLED_FLAT_PROTECTED_SOURCES,
    _PROTECTED_EXTRACTION_SPECS,
    _SANITIZER_LINEAGE_OBSERVED_EXTRACTORS,
    _SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS,
    _TRACE_CONTAINER_RAW_PRESENCE,
    _TRACE_CONTAINER_UNAVAILABLE_KEYS,
    _TRACE_NEST_PROTECTED_SOURCES,
    _FlatObservedFieldExtractor,
    _ProtectedExtractionSpec,
    _SanitizerLineageObservedExtractor,
    _flat_extractor_source_keys,
    protected_observation_extraction_registry,
    protected_observation_extraction_source_by_path,
)
from tests.helpers.golden_replay_projection_fields import (
    MISSING,
    _EXPECTED_PROTECTED_CLASSIFIER_EVIDENCE_COUNT,
    _PROTECTED_CLASSIFIER_EVIDENCE_EXCLUDED_PATHS,
    _first_present,
    protected_observation_field_paths,
    protected_classifier_evidence_field_paths,
)
from tests.helpers.golden_replay_projection_presence import (
    _ProjectionStatus,
    _build_projection_status as _build_projection_status_from_presence,
    _missing_source_by_field_from_presence,
    _unavailable_paths_for_projection as _unavailable_paths_for_projection_from_presence,
    lookup_observation_path,
    protected_path_covered_by_unavailable,
    protected_path_is_represented_in_observed_turn,
    protected_path_representation_errors,
)
from tests.helpers.golden_replay_projection_semantic import project_semantic_mutation_summary


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

def _unavailable_paths_for_projection(
    *,
    protected_flat: Mapping[str, Any],
    trace_observed: Mapping[str, Any],
) -> list[str]:
    """Compatibility wrapper for the presence policy module."""
    return _unavailable_paths_for_projection_from_presence(
        protected_specs=_PROTECTED_EXTRACTION_SPECS,
        protected_flat=protected_flat,
        trace_observed=trace_observed,
    )


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
    """Compatibility wrapper for the presence policy module."""
    return _build_projection_status_from_presence(
        protected_specs=_PROTECTED_EXTRACTION_SPECS,
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


