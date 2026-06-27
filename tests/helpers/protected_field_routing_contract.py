"""CF2/CL1 read-side protected field routing and ownership contract.

Builds one routing row per protected observation registry path from the canonical
extraction registry and schema defaults. Diagnostic only; does not project turns.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tests.helpers.golden_replay_projection_registry import (
    FieldClassification,
    _PROTECTED_EXTRACTION_SPECS,
    _TRACE_CONTAINER_UNAVAILABLE_KEYS,
    protected_extraction_source_ownership,
    protected_field_owner_group,
)

from tests.helpers.golden_replay_projection_fields import (
    protected_observation_default_row,
    protected_observation_drift_bucket,
    protected_observation_field_registry,
)

_EXTRACTOR_SPEC_OWNER = "extractor spec owner: tests.helpers.golden_replay_projection_registry._PROTECTED_EXTRACTION_SPECS"
_PRESENCE_POLICY_OWNER = "presence policy owner: tests.helpers.golden_replay_projection_presence._build_projection_status"
_UNAVAILABLE_POLICY_OWNER = (
    "unavailable policy owner: tests.helpers.golden_replay_projection_presence._unavailable_paths_for_projection"
)
_REPRESENTATION_POLICY_OWNER = (
    "representation policy owner: "
    "tests.helpers.golden_replay_projection_presence.protected_path_is_represented_in_observed_turn"
)


@dataclass(frozen=True)
class ProtectedFieldRoutingRow:
    field_name: str
    field: str
    source_family: str
    source_path: str
    field_owner_group: str
    normalized_source: str | None
    default: Any
    default_behavior: str
    unavailable_rule: str
    unavailable_behavior: str
    unavailable_key: str | None
    raw_presence_expectation: str
    raw_presence_key: str | None
    normalized_presence_expectation: str
    normalized_presence_key: str | None
    missing_source_rule: str
    drift_bucket: str
    classification: FieldClassification
    projection_owner: str
    extractor_spec_owner: str
    presence_policy_owner: str
    unavailable_policy_owner: str
    representation_policy_owner: str
    test_owner: str


def _fem_source_detail(path: str, fem_keys: tuple[str, ...]) -> str:
    keys = fem_keys or (path,)
    if len(keys) == 1 and keys[0] == path:
        return f"FEM.{path}"
    return f"FEM _first_present({', '.join(keys)})"


def _source_path_for_spec(path: str, source: str, fem_keys: tuple[str, ...], trace_container: str) -> str:
    if source == "fem_flat":
        return _fem_source_detail(path, fem_keys)
    if source == "trace_leaf" and trace_container:
        leaf = path.split(".")[-1]
        return f"trace.{trace_container}.{leaf}"
    return protected_extraction_source_ownership(source).source_path


def _field_owner_group(path: str, source: str) -> str:
    _ = source
    return protected_field_owner_group(path)


def _default_behavior(path: str) -> str:
    if "." in path:
        return "nested_trace_no_flat_default"
    if path == "final_text":
        return "flat_default_empty_string"
    if path == "scaffold_leakage":
        return "flat_default_false"
    return "flat_default_none"


def _raw_presence_key_for_contract(path: str, raw_presence: str) -> str | None:
    if raw_presence == "none":
        return None
    if raw_presence == "route":
        return "route_kind"
    if raw_presence == "speaker":
        return "selected_speaker_id"
    if raw_presence in {"fem_key", "fem_dual_family"}:
        return path
    return path


def _raw_presence_expectation(raw_presence: str) -> str:
    if raw_presence == "none":
        return "not_tracked"
    return raw_presence


def _normalized_presence_expectation(normalized_presence: bool) -> str:
    return "tracked" if normalized_presence else "not_tracked"


def _missing_source_rule(raw_presence: str, normalized_presence: bool) -> str:
    if raw_presence == "none":
        return "not tracked"
    if normalized_presence:
        return (
            "raw absent -> runtime_missing_raw_absent; "
            "raw present + normalized absent -> normalized_view_missing_raw_present; "
            "raw present -> projection_missing_raw_present"
        )
    return "raw absent -> runtime_missing_raw_absent; raw present -> projection_missing_raw_present"


def _unavailable_rule(path: str, unavailable_key: str, trace_container: str) -> str:
    if path in _TRACE_CONTAINER_UNAVAILABLE_KEYS:
        return f"trace container empty -> unavailable includes {path!r}"
    if unavailable_key:
        return f"projected {unavailable_key!r} is None -> listed in unavailable"
    if trace_container:
        return f"parent trace.{trace_container} unavailable covers dotted path"
    return "never listed unavailable; projected null/empty/default still represented"


def _unavailable_behavior(path: str, unavailable_key: str, trace_container: str) -> str:
    if path in _TRACE_CONTAINER_UNAVAILABLE_KEYS:
        return "trace_container_empty"
    if unavailable_key:
        return "projected_none"
    if trace_container:
        return "covered_by_trace_container"
    return "represented_when_null"


def _normalized_source(source: str, fem_keys: tuple[str, ...], normalized_presence: bool) -> str | None:
    if not normalized_presence:
        return None
    if source in {"fem_flat", "fallback_family"}:
        detail = _fem_source_detail("", fem_keys) if fem_keys else "FEM keys"
        return f"normalize_fem_for_replay_acceptance -> {detail or 'dual-family keys'}"
    return None


def build_protected_field_routing_matrix() -> tuple[ProtectedFieldRoutingRow, ...]:
    """Return one routing contract row per protected observation registry path."""
    defaults = protected_observation_default_row()
    rows: list[ProtectedFieldRoutingRow] = []
    for field in protected_observation_field_registry():
        path = field.path
        spec = _PROTECTED_EXTRACTION_SPECS[path]
        source = spec.source
        ownership = protected_extraction_source_ownership(source)
        flat_default = defaults.get(path) if "." not in path else None
        raw_presence_key = _raw_presence_key_for_contract(path, spec.raw_presence)
        rows.append(
            ProtectedFieldRoutingRow(
                field_name=path,
                field=path,
                source_family=ownership.source_family,
                source_path=_source_path_for_spec(path, source, spec.fem_source_keys, spec.trace_container),
                field_owner_group=_field_owner_group(path, source),
                normalized_source=_normalized_source(source, spec.fem_source_keys, spec.normalized_presence),
                default=flat_default if "." not in path else "nested under observed.trace (no flat default)",
                default_behavior=_default_behavior(path),
                unavailable_rule=_unavailable_rule(path, spec.unavailable_key, spec.trace_container),
                unavailable_behavior=_unavailable_behavior(path, spec.unavailable_key, spec.trace_container),
                unavailable_key=spec.unavailable_key or (path if path in _TRACE_CONTAINER_UNAVAILABLE_KEYS else None),
                raw_presence_expectation=_raw_presence_expectation(spec.raw_presence),
                raw_presence_key=raw_presence_key,
                normalized_presence_expectation=_normalized_presence_expectation(spec.normalized_presence),
                normalized_presence_key=path if spec.normalized_presence else None,
                missing_source_rule=_missing_source_rule(spec.raw_presence, spec.normalized_presence),
                drift_bucket=protected_observation_drift_bucket(path),
                classification=ownership.classification,
                projection_owner=f"extractor spec owner: _PROTECTED_EXTRACTION_SPECS[{path!r}].source={source!r}",
                extractor_spec_owner=_EXTRACTOR_SPEC_OWNER,
                presence_policy_owner=_PRESENCE_POLICY_OWNER,
                unavailable_policy_owner=_UNAVAILABLE_POLICY_OWNER,
                representation_policy_owner=_REPRESENTATION_POLICY_OWNER,
                test_owner=ownership.test_owner,
            )
        )
    return tuple(rows)


def protected_field_routing_matrix_by_path() -> dict[str, ProtectedFieldRoutingRow]:
    return {row.field: row for row in build_protected_field_routing_matrix()}
