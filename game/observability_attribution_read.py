"""Observability and evaluator read helpers (delegate facade).

Delegates to :mod:`game.final_emission_meta_read`, which in turn delegates to the
canonical FEM write owner. This module adds **no** ownership authority, bucket
mapping, or write paths.

Phase 2 will route diagnostics evaluators and observability tests here instead
of importing ``final_emission_meta_read`` alongside attribution sources.
"""
from __future__ import annotations

from game.final_emission_meta_read import (
    FINAL_EMISSION_META_KEY,
    NARRATIVE_AUTHENTICITY_FEM_KEYS,
    assemble_unified_observational_telemetry_bundle,
    build_fem_observability_events,
    classify_dead_turn,
    default_response_type_debug,
    infer_accept_path_final_emitted_source,
    normalize_final_emission_meta_for_observability,
    normalize_merged_na_telemetry_for_eval,
    normalized_observational_telemetry_bundle,
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
    "assemble_unified_observational_telemetry_bundle",
    "build_fem_observability_events",
    "classify_dead_turn",
    "default_response_type_debug",
    "infer_accept_path_final_emitted_source",
    "normalize_final_emission_meta_for_observability",
    "normalize_merged_na_telemetry_for_eval",
    "normalized_observational_telemetry_bundle",
    "observability_attribution_read_surface",
    "read_dead_turn_from_gm_output",
    "read_debug_notes_from_turn_payload",
    "read_emission_debug_lane",
    "read_emission_debug_lane_from_turn_payload",
    "read_final_emission_meta_dict",
    "read_final_emission_meta_from_turn_payload",
    "stage_diff_narrative_authenticity_projection",
    "summarize_gameplay_validation_for_turn",
]

_OBSERVABILITY_SYMBOLS: tuple[str, ...] = (
    "assemble_unified_observational_telemetry_bundle",
    "build_fem_observability_events",
    "classify_dead_turn",
    "default_response_type_debug",
    "infer_accept_path_final_emitted_source",
    "normalize_final_emission_meta_for_observability",
    "normalize_merged_na_telemetry_for_eval",
    "normalized_observational_telemetry_bundle",
    "read_dead_turn_from_gm_output",
    "read_debug_notes_from_turn_payload",
    "read_emission_debug_lane",
    "read_emission_debug_lane_from_turn_payload",
    "read_final_emission_meta_dict",
    "read_final_emission_meta_from_turn_payload",
    "stage_diff_narrative_authenticity_projection",
    "summarize_gameplay_validation_for_turn",
)


def observability_attribution_read_surface() -> dict[str, object]:
    """Diagnostic registry for BV10 Phase 2 observability read facade."""
    return {
        "facade": "game.observability_attribution_read",
        "delegate_module": "game.final_emission_meta_read",
        "observability_symbols": list(_OBSERVABILITY_SYMBOLS),
        "narrative_authenticity_fem_keys": list(NARRATIVE_AUTHENTICITY_FEM_KEYS),
    }
