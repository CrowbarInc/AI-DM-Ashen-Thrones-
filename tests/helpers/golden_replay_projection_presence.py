"""Presence, missing-source, and unavailable policy for replay projection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tests.helpers.golden_replay_projection_fallbacks import (
    _fem_dual_fallback_family_present,
    _fem_has_any_key,
)
from tests.helpers.golden_replay_projection_fields import (
    MISSING,
    protected_observation_field_registry,
)


@dataclass(frozen=True)
class _SupportingRawPresenceSpec:
    """Non-protected keys included in raw_signal_presence for classifier routing."""

    key: str
    fem_source_keys: tuple[str, ...]


@dataclass(frozen=True)
class _ProjectionStatus:
    """Registry-informed presence outputs for one projected observed turn."""

    raw_signal_presence: dict[str, bool]
    normalized_signal_presence: dict[str, bool]
    missing_source_by_field: dict[str, str]
    unavailable: list[str]


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


def lookup_observation_path(obj: Mapping[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in str(path or "").split("."):
        if not part:
            return MISSING
        if not isinstance(cur, Mapping) or part not in cur:
            return MISSING
        cur = cur.get(part)
    return cur


def _has_path(obj: Mapping[str, Any], path: str) -> bool:
    cur: Any = obj
    for part in str(path or "").split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return False
        cur = cur.get(part)
    return True


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
    """Return whether a protected path is projected or explicitly marked unavailable."""
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


def _raw_presence_key_for_spec(spec: Any) -> str:
    return str(spec.path)


def _raw_presence_for_protected_spec(
    spec: Any,
    *,
    fem: Mapping[str, Any],
    route_kind: Any,
    selected_speaker_id: Any,
    payload: Mapping[str, Any],
    trace: Mapping[str, Any],
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
    spec: Any,
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
    protected_specs: Mapping[str, Any],
    protected_flat: Mapping[str, Any],
    trace_observed: Mapping[str, Any],
) -> list[str]:
    unavailable: list[str] = []
    for spec in protected_specs.values():
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


def _build_projection_status(
    *,
    protected_specs: Mapping[str, Any],
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

    for spec in protected_specs.values():
        raw_value = _raw_presence_for_protected_spec(
            spec,
            fem=fem,
            route_kind=route_kind,
            selected_speaker_id=selected_speaker_id,
            payload=payload,
            trace=trace,
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
        normalized_signal_presence[supporting.key] = _fem_has_any_key(
            fem_normalized,
            supporting.fem_source_keys,
        )

    missing_source_by_field = _missing_source_by_field_from_presence(
        raw_signal_presence,
        normalized_signal_presence,
    )
    unavailable = _unavailable_paths_for_projection(
        protected_specs=protected_specs,
        protected_flat=protected_flat,
        trace_observed=trace_observed,
    )
    return _ProjectionStatus(
        raw_signal_presence=raw_signal_presence,
        normalized_signal_presence=normalized_signal_presence,
        missing_source_by_field=missing_source_by_field,
        unavailable=unavailable,
    )
