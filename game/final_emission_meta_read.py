"""Stable read-side accessors for final-emission metadata (FEM).

Delegates to :mod:`game.final_emission_meta`, the canonical FEM packaging owner.
Downstream diagnostics, observability, and smoke helpers should import from here
instead of the write owner unless they are FEM owner suites.

This module must not add write paths, bucket authority, or schema changes.
"""
from __future__ import annotations

from game.final_emission_meta import (
    FINAL_EMISSION_META_KEY,
    NARRATIVE_AUTHENTICITY_FEM_KEYS,
    OPENING_FALLBACK_EMITTED_METADATA_FIELDS,
    OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS,
    OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS,
    OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS,
    assemble_unified_observational_telemetry_bundle,
    build_fem_observability_events,
    classify_dead_turn,
    default_response_type_debug,
    final_emission_meta_read_side_surface,
    infer_accept_path_final_emitted_source,
    merge_response_type_meta,
    normalize_final_emission_meta_for_observability,
    normalize_merged_na_telemetry_for_eval,
    normalized_observational_telemetry_bundle,
    opening_fallback_metadata_classification_parity_errors,
    opening_fallback_metadata_field_registry_parity_errors,
    read_dead_turn_from_gm_output,
    read_debug_notes_from_turn_payload,
    read_emission_debug_lane,
    read_emission_debug_lane_from_turn_payload,
    read_final_emission_meta_dict,
    read_final_emission_meta_from_turn_payload,
    stage_diff_narrative_authenticity_projection,
    summarize_gameplay_validation_for_turn,
)

__all__ = [
    "FINAL_EMISSION_META_KEY",
    "NARRATIVE_AUTHENTICITY_FEM_KEYS",
    "OPENING_FALLBACK_EMITTED_METADATA_FIELDS",
    "OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS",
    "OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS",
    "OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS",
    "assemble_unified_observational_telemetry_bundle",
    "build_fem_observability_events",
    "classify_dead_turn",
    "default_response_type_debug",
    "final_emission_meta_read_side_surface",
    "infer_accept_path_final_emitted_source",
    "merge_response_type_meta",
    "normalize_final_emission_meta_for_observability",
    "normalize_merged_na_telemetry_for_eval",
    "normalized_observational_telemetry_bundle",
    "opening_fallback_metadata_classification_parity_errors",
    "opening_fallback_metadata_field_registry_parity_errors",
    "read_dead_turn_from_gm_output",
    "read_debug_notes_from_turn_payload",
    "read_emission_debug_lane",
    "read_emission_debug_lane_from_turn_payload",
    "read_final_emission_meta_dict",
    "read_final_emission_meta_from_turn_payload",
    "stage_diff_narrative_authenticity_projection",
    "summarize_gameplay_validation_for_turn",
]
