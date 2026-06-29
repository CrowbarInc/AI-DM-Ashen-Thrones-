"""Golden replay turn-observation projection adapter (Cycle T1).

**Authority (CG-1):** protected observation field paths, acceptance projection,
and derived classifier-evidence overlap inputs. Test-only CI acceptance schema.

**Does not own:** failure row taxonomy, recurrence keys, or runtime FEM lineage
(see ``game.final_emission_replay_projection``). Registry:
``docs/audits/CG_failure_classification_authority_registry.md``

Centralizes payload/snapshot → observation dict projection and protected
field-path enumeration. Test-only; no runtime behavior changes.

**Cycle AO5 boundary — acceptance observation only (do not merge with runtime lineage):**

This **test-only acceptance** module owns the canonical protected observation paths
(``PROTECTED_OBSERVATION_FIELDS``), ``project_turn_observation``, drift buckets, and
classifier/dashboard overlap derivation. It is CI acceptance authority.

Runtime FEM lineage projection (``fem_runtime_lineage_events``, sealed sub-kinds,
selection/content owner splits on lineage events) is owned by
:mod:`game.final_emission_replay_projection`. Golden replay may consume lineage events
for diagnostics and prefer payload-stamped events when present, but lineage event
**owner** semantics are excluded from protected drift classification unless explicitly
promoted later (see ``test_golden_drift_classification_ignores_runtime_lineage_diagnostics``).

These modules must **not** be merged.

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

CE5 splits implementation into focused modules; this file remains the public facade.
"""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_replay_projection import (
    FIRST_MENTION_HARD_REPLACEMENT,
    REFERENTIAL_CLARITY_HARD_REPLACEMENT,
    SEALED_REPLACEMENT_SUBKINDS,
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
    SEALED_REPLACEMENT_SUBKIND_OPENING,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
    VISIBILITY_HARD_REPLACEMENT,
    build_fem_runtime_lineage_events,
    is_sealed_replacement_lineage_kind,
    normalize_fem_for_replay_acceptance,
    project_mutation_classification_from_fallback_kind,
    project_sealed_replacement_subkind_from_fem,
    project_source_family_from_fallback_kind,
    read_emission_debug_lane_for_replay,
    read_fem_from_turn_for_replay,
    read_opening_fallback_owner_bucket_for_replay,
)
from game.semantic_mutation_attribution import (
    reconcile_semantic_mutation_owner,
    selected_semantic_mutation_write_site,
    semantic_mutation_write_site_label,
)

build_runtime_lineage_events_from_fem = build_fem_runtime_lineage_events

from tests.helpers.transcript_runner import compact_snapshot_summary

from tests.helpers.golden_replay_projection_extractors import (
    _ProtectedExtractionSpec,
    _build_projection_status,
    _echo_overlap_band,
    _extract_fem_flat_observed_fields,
    _extract_sanitizer_lineage_observed_fields,
    _extract_sanitizer_trace_flat_observed_fields,
    _find_nested_list,
    _find_nested_mapping,
    _project_flat_protected_observed_fields,
    _resolve_route_kind,
    _runtime_lineage_events_from_payload,
    _sanitizer_debug_change_counts,
    _trace_from_payload_or_snapshot,
    lookup_observation_path,
    project_semantic_mutation_summary,
    protected_observation_extraction_registry,
    protected_observation_extraction_source_by_path,
    protected_path_covered_by_unavailable,
    protected_path_is_represented_in_observed_turn,
    protected_path_representation_errors,
)
from tests.helpers.golden_replay_projection_fallbacks import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS,
    _resolve_fallback_family,
    dual_fallback_family_replay_precedence_surface,
    project_replay_fallback_family_from_fem,
)
from tests.helpers.golden_replay_projection_fields import (
    MISSING,
    PROTECTED_OBSERVATION_FIELDS,
    ProtectedObservationField,
    SEMANTIC_DRIFT_FIELDS,
    STRUCTURAL_DRIFT_FIELDS,
    _first_present,
    final_text_has_scaffold_leakage,
    golden_text_hash,
    normalize_golden_text,
    observed_projection_schema_defaults,
    protected_classifier_evidence_excluded_paths,
    protected_classifier_evidence_field_paths,
    protected_observation_default_row,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_observation_flat_field_paths,
)
from tests.helpers.golden_replay_projection_manifest import (
    PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_BEGIN,
    PROTECTED_REPLAY_MANIFEST_FIELD_PATHS_END,
    extract_protected_observation_manifest_section,
    protected_observation_manifest_counts,
    protected_observation_manifest_field_rows,
    protected_observation_manifest_registry_parity_errors,
    protected_observation_manifest_section_is_current,
    render_protected_observation_manifest_section,
)
from tests.helpers.golden_replay_projection_speaker import (
    SpeakerProjectionParityStatus,
    project_speaker_projection_parity,
    read_final_speaker_observation_for_replay,
    _resolve_selected_speaker_id,
)

def project_turn_observation(turn_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Project chat payload + snapshot into a golden replay observation dict.

    ``turn_payload`` keys:
    - ``scenario_id`` (str, required)
    - ``snap`` (mapping, required)
    - ``payload`` (mapping, required)
    - ``replay_identity`` (optional mapping with source_path/branch_id/turn_id)
    - ``semantic_mutation_trace`` (optional BY1 diagnostic record)
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
    fem = read_fem_from_turn_for_replay(payload)
    fem_normalized = normalize_fem_for_replay_acceptance(fem)
    fem_flat = _extract_fem_flat_observed_fields(fem)
    runtime_lineage_events = _runtime_lineage_events_from_payload(payload, fem)
    emission_debug_lane = read_emission_debug_lane_for_replay(payload)
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

    route_kind = _resolve_route_kind(
        social_contract_trace=social_contract_trace,
        resolution_compact=resolution_compact if isinstance(resolution_compact, Mapping) else None,
        resolution=resolution,
    )

    selected_speaker_id, selected_speaker_source = _resolve_selected_speaker_id(
        social_contract_trace=social_contract_trace,
        snap=snap,
        social=social,
    )

    response_delta_checked = _first_present(fem, ("response_delta_checked",))
    response_delta_failed = _first_present(fem, ("response_delta_failed",))
    response_delta_repaired = _first_present(fem, ("response_delta_repaired",))
    response_delta_kind = _first_present(fem, ("response_delta_kind", "response_delta_kind_detected"))
    response_delta_echo_overlap_ratio = _first_present(fem, ("response_delta_echo_overlap_ratio",))
    response_delta_echo_overlap_band = _echo_overlap_band(response_delta_echo_overlap_ratio)
    response_delta_skip_reason = _first_present(fem, ("response_delta_skip_reason",))
    response_delta_trigger_source = _first_present(fem, ("response_delta_trigger_source",))
    post_gate_mutation_detected = _first_present(fem, ("post_gate_mutation_detected",))
    fallback_family = _resolve_fallback_family(fem, runtime_lineage_events)
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
    sanitizer_lineage_flat = _extract_sanitizer_lineage_observed_fields(
        sanitizer_trace,
        lineage_context={
            "sanitizer_mode": sanitizer_mode,
            "sanitizer_changed_count": sanitizer_changed_count,
            "sanitizer_dropped_count": sanitizer_dropped_count,
            "sanitizer_empty_fallback_used": sanitizer_trace_flat.get("sanitizer_empty_fallback_used"),
        },
    )
    interaction_continuity_validation = _find_nested_mapping(payload, "interaction_continuity_validation")

    final_text = str(snap.get("gm_text") or "")
    protected_flat = _project_flat_protected_observed_fields(
        resolution=resolution,
        route_kind=route_kind,
        selected_speaker_id=selected_speaker_id,
        fem=fem,
        fem_flat=fem_flat,
        sanitizer_trace_flat=sanitizer_trace_flat,
        sanitizer_lineage_flat=sanitizer_lineage_flat,
        fallback_family=fallback_family,
        final_text=final_text,
    )
    trace_observed = {
        "canonical_entry_path": trace.get("canonical_entry_path"),
        "canonical_entry_reason": trace.get("canonical_entry_reason"),
        "canonical_entry_target_actor_id": trace.get("canonical_entry_target_actor_id"),
        "canonical_entry": dict(canonical_entry),
        "turn_trace": dict(turn_trace),
        "social_contract_trace": dict(social_contract_trace),
    }
    projection_status = _build_projection_status(
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
    final_speaker_observation = read_final_speaker_observation_for_replay(
        emission_debug_lane,
        payload=payload,
    )
    speaker_projection_parity = project_speaker_projection_parity(
        selected_speaker_id=selected_speaker_id,
        selected_speaker_source=selected_speaker_source,
        emission_debug_lane=emission_debug_lane,
        payload=payload,
        final_speaker_observation=final_speaker_observation,
    )
    semantic_trace = turn_payload.get("semantic_mutation_trace")
    if not isinstance(semantic_trace, Mapping):
        semantic_trace = payload.get("semantic_mutation_trace")
    semantic_summary = project_semantic_mutation_summary(
        semantic_trace if isinstance(semantic_trace, Mapping) else None
    )
    observed = {
        "scenario_id": scenario_id,
        "turn_index": snap.get("turn_index"),
        "player_text": snap.get("player_text"),
        "selected_speaker_source": selected_speaker_source,
        "final_speaker_observation": final_speaker_observation,
        "speaker_projection_parity": speaker_projection_parity,
        **protected_flat,
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
        "sanitizer_leak_terms": ["scaffold_leakage"] if protected_flat.get("scaffold_leakage") else [],
        "final_text_hash": golden_text_hash(final_text),
        "trace": trace_observed,
        "snapshot_summary": compact_snapshot_summary(snap),
        "raw_signal_presence": projection_status.raw_signal_presence,
        "normalized_signal_presence": projection_status.normalized_signal_presence,
        "missing_source_by_field": projection_status.missing_source_by_field,
        "fem_raw_keys": sorted(str(k) for k in fem.keys()),
        "fem_normalized_keys": sorted(str(k) for k in fem_normalized.keys()),
        "emission_debug_lane_keys": sorted(str(k) for k in emission_debug_lane.keys()),
        "runtime_lineage_events": runtime_lineage_events,
        "interaction_continuity_validation": interaction_continuity_validation,
    }
    write_sites = fem.get("semantic_mutation_write_sites")
    if isinstance(write_sites, list):
        projected_write_sites = [
            dict(row) for row in write_sites if isinstance(row, Mapping)
        ]
        observed["semantic_mutation_write_sites"] = projected_write_sites
        first_write_site = selected_semantic_mutation_write_site(projected_write_sites)
        first_prompt_write = selected_semantic_mutation_write_site(projected_write_sites, family="prompt")
        first_policy_write = selected_semantic_mutation_write_site(projected_write_sites, family="policy")
        if isinstance(first_prompt_write, Mapping):
            observed["first_prompt_write"] = semantic_mutation_write_site_label(first_prompt_write)
        if isinstance(first_policy_write, Mapping):
            observed["first_policy_write"] = semantic_mutation_write_site_label(first_policy_write)
        if isinstance(first_write_site, Mapping):
            observed["first_write_site"] = semantic_mutation_write_site_label(first_write_site)
            observed["first_write_family"] = first_write_site.get("write_site_family")
            observed["first_write_owner"] = first_write_site.get("owner")
            observed["semantic_mutation_attribution_evidence_source"] = "write_site"
    if replay_identity_map:
        for key in ("source_path", "branch_id", "turn_id"):
            value = replay_identity_map.get(key)
            if value is not None and str(value).strip():
                observed[key] = str(value)
    observed["unavailable"] = projection_status.unavailable
    observed.update(semantic_summary)
    reconciled = reconcile_semantic_mutation_owner(
        fem=fem,
        runtime_lineage=runtime_lineage_events,
        sanitizer_trace=sanitizer_trace,
        fallback_provenance=fem.get("fallback_provenance_trace"),
        projection_metadata=semantic_summary,
        stage_diff=stage_diff,
    )
    observed.update(reconciled.as_dict())
    return observed
