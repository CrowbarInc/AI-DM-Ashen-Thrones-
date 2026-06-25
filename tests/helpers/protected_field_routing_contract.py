"""CF2 — read-side protected field source/default/unavailable routing contract.

Builds one routing row per protected observation registry path from the canonical
extraction registry and schema defaults. Diagnostic only; does not project turns.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from tests.helpers.golden_replay_projection_extractors import (
    _PROTECTED_EXTRACTION_SPECS,
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
    "route": "trace.social_contract_trace.route_selected → snap.debug.resolution_compact.kind → payload.resolution.kind",
    "speaker": "social_contract_trace speaker keys → transcript snapshot → resolution.social.npc_id",
    "fem_flat": "FEM sidecar (read_fem_from_turn_for_replay)",
    "sanitizer_trace": "payload nested sanitizer_trace",
    "sanitizer_lineage": "sanitizer_trace key → sanitizer lineage context fallback",
    "sanitizer_lineage_legacy": "sanitizer_trace key → derived from sanitizer_lineage_mode",
    "fem_opening_bucket": "read_opening_fallback_owner_bucket_for_replay(FEM)",
    "fallback_family": "project_replay_fallback_family_from_fem → lineage bridge",
    "final_text": "snap.gm_text",
    "scaffold": "final_text_has_scaffold_leakage(final_text)",
    "trace_leaf": "debug trace container leaf",
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


@dataclass(frozen=True)
class ProtectedFieldRoutingRow:
    field: str
    source_path: str
    normalized_source: str | None
    default: Any
    unavailable_rule: str
    missing_source_rule: str
    drift_bucket: str
    classification: FieldClassification
    projection_owner: str
    test_owner: str


def _fem_source_detail(path: str, fem_keys: tuple[str, ...]) -> str:
    keys = fem_keys or (path,)
    if len(keys) == 1 and keys[0] == path:
        return f"FEM.{path}"
    return f"FEM _first_present({', '.join(keys)})"


def _missing_source_rule(raw_presence: str, normalized_presence: bool) -> str:
    if raw_presence == "none":
        return "not tracked"
    if normalized_presence:
        return "raw absent → runtime_missing_raw_absent; raw present + normalized absent → normalized_view_missing_raw_present; raw present → projection_missing_raw_present"
    return "raw absent → runtime_missing_raw_absent; raw present → projection_missing_raw_present"


def _unavailable_rule(path: str, unavailable_key: str, trace_container: str) -> str:
    if path in _TRACE_CONTAINER_UNAVAILABLE_KEYS:
        return f"trace container empty → unavailable includes {path!r}"
    if unavailable_key:
        return f"projected {unavailable_key!r} is None → listed in unavailable"
    if trace_container:
        return f"parent trace.{trace_container} unavailable covers dotted path"
    return "never listed unavailable; projected null/empty/default still represented"


def _normalized_source(source: str, fem_keys: tuple[str, ...], normalized_presence: bool) -> str | None:
    if not normalized_presence:
        return None
    if source in {"fem_flat", "fallback_family"}:
        detail = _fem_source_detail("", fem_keys) if fem_keys else "FEM keys"
        return f"normalize_fem_for_replay_acceptance → {detail or 'dual-family keys'}"
    return None


def build_protected_field_routing_matrix() -> tuple[ProtectedFieldRoutingRow, ...]:
    """Return one routing contract row per protected observation registry path."""
    defaults = protected_observation_default_row()
    rows: list[ProtectedFieldRoutingRow] = []
    for field in protected_observation_field_registry():
        path = field.path
        spec = _PROTECTED_EXTRACTION_SPECS[path]
        source = spec.source
        source_path = _SOURCE_PATH_BY_EXTRACTION_SOURCE[source]
        if source == "fem_flat" and spec.fem_source_keys:
            source_path = _fem_source_detail(path, spec.fem_source_keys)
        elif source == "trace_leaf" and spec.trace_container:
            leaf = path.split(".")[-1]
            source_path = f"trace.{spec.trace_container}.{leaf}"
        flat_default = defaults.get(path) if "." not in path else None
        rows.append(
            ProtectedFieldRoutingRow(
                field=path,
                source_path=source_path,
                normalized_source=_normalized_source(source, spec.fem_source_keys, spec.normalized_presence),
                default=flat_default if "." not in path else "nested under observed.trace (no flat default)",
                unavailable_rule=_unavailable_rule(path, spec.unavailable_key, spec.trace_container),
                missing_source_rule=_missing_source_rule(spec.raw_presence, spec.normalized_presence),
                drift_bucket=protected_observation_drift_bucket(path),
                classification=_CLASSIFICATION_BY_SOURCE[source],
                projection_owner=f"_PROTECTED_EXTRACTION_SPECS[{path!r}].source={source!r}",
                test_owner=_TEST_OWNER_BY_SOURCE[source],
            )
        )
    return tuple(rows)


def protected_field_routing_matrix_by_path() -> dict[str, ProtectedFieldRoutingRow]:
    return {row.field: row for row in build_protected_field_routing_matrix()}
