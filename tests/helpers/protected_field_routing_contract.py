"""CF2/CL1 read-side protected field routing and ownership contract.

Builds one routing row per protected observation registry path from the canonical
extraction registry and schema defaults. Diagnostic only; does not project turns.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from tests.helpers.golden_replay_projection_registry import (
    _PROTECTED_EXTRACTION_SPECS,
)
from tests.helpers.golden_replay_projection_presence import (
    _TRACE_CONTAINER_UNAVAILABLE_KEYS,
)
from tests.helpers.golden_replay_projection_fields import (
    protected_observation_default_row,
    protected_observation_drift_bucket,
    protected_observation_field_registry,
)

FieldClassification = Literal[
    "direct_runtime_fem",
    "derived_runtime_fem",
    "snapshot_transcript",
    "trace_debug",
    "derived_text",
    "synthetic_default_only",
]

_SOURCE_PATH_BY_EXTRACTION_SOURCE: dict[str, str] = {
    "resolution": "payload.resolution.kind",
    "route": "trace.social_contract_trace.route_selected -> snap.debug.resolution_compact.kind -> payload.resolution.kind",
    "speaker": "social_contract_trace speaker keys -> transcript snapshot -> resolution.social.npc_id",
    "fem_flat": "FEM sidecar (read_fem_from_turn_for_replay)",
    "sanitizer_trace": "payload.metadata.sanitizer_trace",
    "sanitizer_lineage": "sanitizer_trace key -> sanitizer lineage context fallback",
    "sanitizer_lineage_legacy": "sanitizer_trace key -> derived from sanitizer_lineage_mode",
    "fem_opening_bucket": "read_opening_fallback_owner_bucket_for_replay(FEM)",
    "fallback_family": "project_replay_fallback_family_from_fem -> lineage bridge",
    "final_text": "snap.gm_text",
    "scaffold": "final_text_has_scaffold_leakage(final_text)",
    "trace_leaf": "debug trace container leaf",
}

_SOURCE_FAMILY_BY_EXTRACTION_SOURCE: dict[str, str] = {
    "resolution": "payload_resolution",
    "route": "trace_or_snapshot_route",
    "speaker": "trace_or_snapshot_speaker",
    "fem_flat": "fem_metadata",
    "sanitizer_trace": "sanitizer_trace",
    "sanitizer_lineage": "sanitizer_lineage",
    "sanitizer_lineage_legacy": "sanitizer_lineage",
    "fem_opening_bucket": "fem_owner_bucket_read_view",
    "fallback_family": "fem_fallback_family_compatibility",
    "final_text": "snapshot_text",
    "scaffold": "derived_text_quality",
    "trace_leaf": "debug_trace",
}

_FIELD_OWNER_GROUP_BY_SOURCE: dict[str, str] = {
    "resolution": "runtime_resolution_payload",
    "route": "replay_route_projection",
    "speaker": "replay_speaker_projection",
    "fem_flat": "final_emission_metadata",
    "sanitizer_trace": "sanitizer_projection",
    "sanitizer_lineage": "sanitizer_projection",
    "sanitizer_lineage_legacy": "sanitizer_projection",
    "fem_opening_bucket": "owner_bucket_read_views",
    "fallback_family": "replay_fallback_family_projection",
    "final_text": "replay_snapshot_text_projection",
    "scaffold": "replay_text_quality_projection",
    "trace_leaf": "replay_trace_projection",
}

_FIELD_OWNER_GROUP_BY_PATH: dict[str, str] = {
    "response_type_required": "response_type_metadata",
    "response_type_candidate_ok": "response_type_metadata",
    "response_type_repair_used": "response_type_metadata",
    "response_type_repair_kind": "response_type_metadata",
    "upstream_prepared_emission_used": "upstream_prepared_emission_metadata",
    "upstream_prepared_emission_valid": "upstream_prepared_emission_metadata",
    "upstream_prepared_emission_source": "upstream_prepared_emission_metadata",
    "upstream_prepared_emission_reject_reason": "upstream_prepared_emission_metadata",
    "opening_recovered_via_fallback": "opening_fallback_metadata",
    "opening_fallback_authorship_source": "opening_fallback_metadata",
    "opening_fallback_owner_bucket": "owner_bucket_read_views",
    "sealed_fallback_owner_bucket": "sealed_fallback_metadata",
    "visibility_fallback_owner_bucket": "visibility_fallback_metadata",
    "visibility_replacement_applied": "visibility_fallback_metadata",
    "visibility_fallback_pool": "visibility_fallback_metadata",
    "visibility_fallback_kind": "visibility_fallback_metadata",
}

_CLASSIFICATION_BY_SOURCE: dict[str, FieldClassification] = {
    "resolution": "direct_runtime_fem",
    "route": "snapshot_transcript",
    "speaker": "snapshot_transcript",
    "fem_flat": "direct_runtime_fem",
    "sanitizer_trace": "direct_runtime_fem",
    "sanitizer_lineage": "derived_runtime_fem",
    "sanitizer_lineage_legacy": "derived_runtime_fem",
    "fem_opening_bucket": "derived_runtime_fem",
    "fallback_family": "derived_runtime_fem",
    "final_text": "snapshot_transcript",
    "scaffold": "derived_text",
    "trace_leaf": "trace_debug",
}

_TEST_OWNER_BY_SOURCE: dict[str, str] = {
    "resolution": "test_golden_replay_projection.py",
    "route": "test_cf1_route_and_trace_precedence.py",
    "speaker": "test_cf1_speaker_projection_precedence.py",
    "fem_flat": "test_final_emission_meta.py",
    "sanitizer_trace": "test_golden_replay_fallback_sanitizer_projection.py",
    "sanitizer_lineage": "test_golden_replay_fallback_sanitizer_projection.py",
    "sanitizer_lineage_legacy": "test_golden_replay_fallback_sanitizer_projection.py",
    "fem_opening_bucket": "test_golden_replay_fallback_opening_projection.py",
    "fallback_family": "test_cf1_fallback_family_precedence.py",
    "final_text": "test_golden_replay_projection.py",
    "scaffold": "test_golden_replay_projection.py",
    "trace_leaf": "test_golden_replay_projection.py",
}

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
    return _SOURCE_PATH_BY_EXTRACTION_SOURCE[source]


def _field_owner_group(path: str, source: str) -> str:
    return _FIELD_OWNER_GROUP_BY_PATH.get(path, _FIELD_OWNER_GROUP_BY_SOURCE[source])


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
        flat_default = defaults.get(path) if "." not in path else None
        raw_presence_key = _raw_presence_key_for_contract(path, spec.raw_presence)
        rows.append(
            ProtectedFieldRoutingRow(
                field_name=path,
                field=path,
                source_family=_SOURCE_FAMILY_BY_EXTRACTION_SOURCE[source],
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
                classification=_CLASSIFICATION_BY_SOURCE[source],
                projection_owner=f"extractor spec owner: _PROTECTED_EXTRACTION_SPECS[{path!r}].source={source!r}",
                extractor_spec_owner=_EXTRACTOR_SPEC_OWNER,
                presence_policy_owner=_PRESENCE_POLICY_OWNER,
                unavailable_policy_owner=_UNAVAILABLE_POLICY_OWNER,
                representation_policy_owner=_REPRESENTATION_POLICY_OWNER,
                test_owner=_TEST_OWNER_BY_SOURCE[source],
            )
        )
    return tuple(rows)


def protected_field_routing_matrix_by_path() -> dict[str, ProtectedFieldRoutingRow]:
    return {row.field: row for row in build_protected_field_routing_matrix()}
