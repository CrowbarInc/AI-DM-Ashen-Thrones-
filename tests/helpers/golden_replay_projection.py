"""Golden replay turn-observation projection adapter (Cycle T1).

Centralizes payload/snapshot → observation dict projection and protected
field-path enumeration. Test-only; no runtime behavior changes.

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

from game.final_emission_meta import (
    build_fem_runtime_lineage_events,
    normalize_final_emission_meta_for_observability,
    opening_fallback_owner_bucket_from_meta,
    read_emission_debug_lane_from_turn_payload,
    read_final_emission_meta_from_turn_payload,
)
from game.final_emission_replay_projection import is_sealed_replacement_lineage_kind
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


def _flat_extractor_source_keys(extractor: _FlatObservedFieldExtractor) -> tuple[str, ...]:
    return extractor.source_keys or (extractor.observed_key,)


_FEM_FLAT_OBSERVED_EXTRACTORS: tuple[_FlatObservedFieldExtractor, ...] = (
    _FlatObservedFieldExtractor(
        "final_emitted_source",
        "fem",
        ("final_emitted_source", "final_route", "upstream_prepared_emission_source"),
    ),
    _FlatObservedFieldExtractor("final_emission_mutation_lineage", "fem"),
    _FlatObservedFieldExtractor("response_type_required", "fem"),
    _FlatObservedFieldExtractor("response_type_candidate_ok", "fem"),
    _FlatObservedFieldExtractor("response_type_repair_used", "fem"),
    _FlatObservedFieldExtractor("response_type_repair_kind", "fem"),
    _FlatObservedFieldExtractor("upstream_prepared_emission_used", "fem"),
    _FlatObservedFieldExtractor("upstream_prepared_emission_valid", "fem"),
    _FlatObservedFieldExtractor("upstream_prepared_emission_source", "fem"),
    _FlatObservedFieldExtractor("upstream_prepared_emission_reject_reason", "fem"),
    _FlatObservedFieldExtractor("sealed_fallback_owner_bucket", "fem"),
    _FlatObservedFieldExtractor("visibility_fallback_owner_bucket", "fem"),
    _FlatObservedFieldExtractor("visibility_replacement_applied", "fem"),
    _FlatObservedFieldExtractor("visibility_fallback_pool", "fem"),
    _FlatObservedFieldExtractor("visibility_fallback_kind", "fem"),
    _FlatObservedFieldExtractor("fallback_temporal_frame", "fem"),
)

_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS: tuple[_FlatObservedFieldExtractor, ...] = (
    _FlatObservedFieldExtractor("sanitizer_empty_fallback_used", "sanitizer_trace"),
    _FlatObservedFieldExtractor("sanitizer_empty_fallback_source", "sanitizer_trace"),
    _FlatObservedFieldExtractor("sanitizer_empty_fallback_owner", "sanitizer_trace"),
    _FlatObservedFieldExtractor("sanitizer_strict_social_fallback_used", "sanitizer_trace"),
    _FlatObservedFieldExtractor("sanitizer_strict_social_selection_owner", "sanitizer_trace"),
    _FlatObservedFieldExtractor("sanitizer_strict_social_prose_owner", "sanitizer_trace"),
    _FlatObservedFieldExtractor("sanitizer_strict_social_source", "sanitizer_trace"),
)

_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS: tuple[_SanitizerLineageObservedExtractor, ...] = (
    _SanitizerLineageObservedExtractor("sanitizer_lineage_mode", "sanitizer_lineage_mode", "sanitizer_mode"),
    _SanitizerLineageObservedExtractor(
        "sanitizer_lineage_changed_count",
        "sanitizer_lineage_changed_count",
        "sanitizer_changed_count",
    ),
    _SanitizerLineageObservedExtractor(
        "sanitizer_lineage_dropped_count",
        "sanitizer_lineage_dropped_count",
        "sanitizer_dropped_count",
    ),
    _SanitizerLineageObservedExtractor(
        "sanitizer_lineage_empty_fallback_used",
        "sanitizer_lineage_empty_fallback_used",
        "sanitizer_empty_fallback_used",
    ),
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


def protected_field_paths() -> tuple[str, ...]:
    """Return dotted field paths under protected golden replay observation locks."""
    return protected_observation_field_paths()


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
    fem = read_final_emission_meta_from_turn_payload(payload)
    fem_normalized = normalize_final_emission_meta_for_observability(fem)
    fem_flat = _extract_fem_flat_observed_fields(fem)
    runtime_lineage_events = _runtime_lineage_events_from_payload(payload, fem)
    emission_debug_lane = read_emission_debug_lane_from_turn_payload(payload)
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

    route_kind = _first_present(
        social_contract_trace,
        ("route_selected",),
    )
    if route_kind is None and isinstance(resolution_compact, Mapping):
        route_kind = resolution_compact.get("kind")
    if route_kind is None:
        route_kind = resolution.get("kind")

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

    response_delta_checked = _first_present(fem, ("response_delta_checked",))
    response_delta_failed = _first_present(fem, ("response_delta_failed",))
    response_delta_repaired = _first_present(fem, ("response_delta_repaired",))
    response_delta_kind = _first_present(fem, ("response_delta_kind", "response_delta_kind_detected"))
    response_delta_echo_overlap_ratio = _first_present(fem, ("response_delta_echo_overlap_ratio",))
    response_delta_echo_overlap_band = _echo_overlap_band(response_delta_echo_overlap_ratio)
    response_delta_skip_reason = _first_present(fem, ("response_delta_skip_reason",))
    response_delta_trigger_source = _first_present(fem, ("response_delta_trigger_source",))
    post_gate_mutation_detected = _first_present(fem, ("post_gate_mutation_detected",))
    opening_recovered_via_fallback = _first_present(fem, ("opening_recovered_via_fallback",))
    opening_fallback_authorship_source = _first_present(fem, ("opening_fallback_authorship_source",))
    opening_fallback_owner_bucket = opening_fallback_owner_bucket_from_meta(fem)
    fallback_family = project_replay_fallback_family_from_fem(fem)
    if fallback_family is None:
        fallback_family = _project_replay_fallback_family(fem, runtime_lineage_events)
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
    sanitizer_empty_fallback_used = sanitizer_trace_flat["sanitizer_empty_fallback_used"]
    sanitizer_lineage_flat = _extract_sanitizer_lineage_observed_fields(
        sanitizer_trace,
        lineage_context={
            "sanitizer_mode": sanitizer_mode,
            "sanitizer_changed_count": sanitizer_changed_count,
            "sanitizer_dropped_count": sanitizer_dropped_count,
            "sanitizer_empty_fallback_used": sanitizer_empty_fallback_used,
        },
    )
    interaction_continuity_validation = _find_nested_mapping(payload, "interaction_continuity_validation")

    final_text = str(snap.get("gm_text") or "")
    raw_signal_presence = {
        "route_kind": route_kind is not None or _has_path(payload, "resolution.kind") or _has_path(trace, "turn_trace.social_contract_trace.route_selected"),
        "selected_speaker_id": selected_speaker_id is not None,
        "final_emitted_source": "final_emitted_source" in fem,
        "final_emission_mutation_lineage": "final_emission_mutation_lineage" in fem,
        "response_type_required": "response_type_required" in fem,
        "response_type_candidate_ok": "response_type_candidate_ok" in fem,
        "response_type_repair_used": "response_type_repair_used" in fem,
        "response_delta_checked": "response_delta_checked" in fem,
        "response_delta_failed": "response_delta_failed" in fem,
        "response_delta_repaired": "response_delta_repaired" in fem,
        "response_delta_kind": "response_delta_kind" in fem or "response_delta_kind_detected" in fem,
        "response_delta_echo_overlap_ratio": "response_delta_echo_overlap_ratio" in fem,
        "upstream_prepared_emission_used": "upstream_prepared_emission_used" in fem,
        "upstream_prepared_emission_valid": "upstream_prepared_emission_valid" in fem,
        "upstream_prepared_emission_source": "upstream_prepared_emission_source" in fem,
        "upstream_prepared_emission_reject_reason": "upstream_prepared_emission_reject_reason" in fem,
        "sealed_fallback_owner_bucket": "sealed_fallback_owner_bucket" in fem,
        "visibility_fallback_owner_bucket": "visibility_fallback_owner_bucket" in fem,
        "visibility_replacement_applied": "visibility_replacement_applied" in fem,
        "visibility_fallback_pool": "visibility_fallback_pool" in fem,
        "visibility_fallback_kind": "visibility_fallback_kind" in fem,
        "fallback_family": "fallback_family_used" in fem or "realization_fallback_family" in fem,
        "trace.canonical_entry": bool(canonical_entry),
        "trace.turn_trace": bool(turn_trace),
        "trace.social_contract_trace": bool(social_contract_trace),
    }
    normalized_signal_presence = {
        "final_emitted_source": "final_emitted_source" in fem_normalized,
        "final_emission_mutation_lineage": "final_emission_mutation_lineage" in fem_normalized,
        "response_type_required": "response_type_required" in fem_normalized,
        "response_type_candidate_ok": "response_type_candidate_ok" in fem_normalized,
        "response_type_repair_used": "response_type_repair_used" in fem_normalized,
        "response_delta_checked": "response_delta_checked" in fem_normalized,
        "response_delta_failed": "response_delta_failed" in fem_normalized,
        "response_delta_repaired": "response_delta_repaired" in fem_normalized,
        "response_delta_kind": "response_delta_kind" in fem_normalized or "response_delta_kind_detected" in fem_normalized,
        "response_delta_echo_overlap_ratio": "response_delta_echo_overlap_ratio" in fem_normalized,
        "upstream_prepared_emission_used": "upstream_prepared_emission_used" in fem_normalized,
        "upstream_prepared_emission_valid": "upstream_prepared_emission_valid" in fem_normalized,
        "upstream_prepared_emission_source": "upstream_prepared_emission_source" in fem_normalized,
        "upstream_prepared_emission_reject_reason": "upstream_prepared_emission_reject_reason" in fem_normalized,
        "sealed_fallback_owner_bucket": "sealed_fallback_owner_bucket" in fem_normalized,
        "visibility_fallback_owner_bucket": "visibility_fallback_owner_bucket" in fem_normalized,
        "visibility_replacement_applied": "visibility_replacement_applied" in fem_normalized,
        "visibility_fallback_pool": "visibility_fallback_pool" in fem_normalized,
        "visibility_fallback_kind": "visibility_fallback_kind" in fem_normalized,
        "fallback_family": "fallback_family_used" in fem_normalized or "realization_fallback_family" in fem_normalized,
    }
    missing_source_by_field = {}
    for field, raw_present in raw_signal_presence.items():
        if raw_present is True and field in normalized_signal_presence and normalized_signal_presence[field] is False:
            missing_source_by_field[field] = "normalized_view_missing_raw_present"
        elif raw_present is True:
            missing_source_by_field[field] = "projection_missing_raw_present"
        elif raw_present is False:
            missing_source_by_field[field] = "runtime_missing_raw_absent"
    observed = {
        "scenario_id": scenario_id,
        "turn_index": snap.get("turn_index"),
        "player_text": snap.get("player_text"),
        "final_text": final_text,
        "resolution_kind": resolution.get("kind"),
        "route_kind": route_kind,
        "selected_speaker_id": selected_speaker_id,
        "selected_speaker_source": selected_speaker_source,
        **_observed_fem_flat_values(fem_flat),
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
        **sanitizer_trace_flat,
        **sanitizer_lineage_flat,
        "sanitizer_leak_terms": ["scaffold_leakage"] if final_text_has_scaffold_leakage(final_text) else [],
        "opening_recovered_via_fallback": opening_recovered_via_fallback,
        "opening_fallback_authorship_source": opening_fallback_authorship_source,
        "opening_fallback_owner_bucket": opening_fallback_owner_bucket,
        "fallback_family": fallback_family,
        "scaffold_leakage": final_text_has_scaffold_leakage(final_text),
        "final_text_hash": golden_text_hash(final_text),
        "trace": {
            "canonical_entry_path": trace.get("canonical_entry_path"),
            "canonical_entry_reason": trace.get("canonical_entry_reason"),
            "canonical_entry_target_actor_id": trace.get("canonical_entry_target_actor_id"),
            "canonical_entry": dict(canonical_entry),
            "turn_trace": dict(turn_trace),
            "social_contract_trace": dict(social_contract_trace),
        },
        "snapshot_summary": compact_snapshot_summary(snap),
        "raw_signal_presence": raw_signal_presence,
        "normalized_signal_presence": normalized_signal_presence,
        "missing_source_by_field": missing_source_by_field,
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
    observed["unavailable"] = sorted(
        key
        for key in (
            "route_kind",
            "selected_speaker_id",
            "final_emitted_source",
            "response_type_required",
            "response_type_candidate_ok",
            "response_type_repair_used",
            "fallback_family",
            "trace.canonical_entry",
            "trace.turn_trace",
            "trace.social_contract_trace",
        )
        if (
            (key == "trace.canonical_entry" and not observed["trace"]["canonical_entry"])
            or (key == "trace.turn_trace" and not observed["trace"]["turn_trace"])
            or (key == "trace.social_contract_trace" and not observed["trace"]["social_contract_trace"])
            or (not key.startswith("trace.") and observed.get(key) is None)
        )
    )
    return observed
