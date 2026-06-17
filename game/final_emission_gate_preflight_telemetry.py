"""Telemetry and pregate containment for gate entry/preflight (Cycle BN4).

Observability-only setup for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
Preserves exact call order and in-place ``out`` mutations; no routing or terminal enforcement.
"""
from __future__ import annotations

from typing import Any, Dict, NamedTuple

from game.fallback_provenance_debug import (
    apply_upstream_fallback_pregate_containment,
    record_final_emission_gate_entry,
)
from game.final_emission_text import _normalize_text
from game.stage_diff_telemetry import (
    diff_turn_stage,
    record_stage_snapshot,
    record_stage_transition,
    snapshot_turn_stage,
)


class GatePreflightTelemetryResult(NamedTuple):
    """Refreshed text values after gate preflight telemetry and containment."""

    pre_gate_text: str
    text: str


def apply_gate_preflight_telemetry_and_containment(
    out: Dict[str, Any],
    *,
    pre_gate_text: str,
) -> GatePreflightTelemetryResult:
    """Record gate-entry telemetry, run pregate containment, and return refreshed text."""
    record_final_emission_gate_entry(out)
    record_stage_snapshot(out, "final_emission_gate_entry")
    snap_before_pregate = snapshot_turn_stage(out, "gate_before_pregate_containment")
    refreshed_pre_gate_text = pre_gate_text
    if apply_upstream_fallback_pregate_containment(out):
        refreshed_pre_gate_text = _normalize_text(out.get("player_facing_text"))
        snap_after_pregate = snapshot_turn_stage(out, "gate_after_pregate_containment")
        _pregate_diff = diff_turn_stage(snap_before_pregate, snap_after_pregate)
        if _pregate_diff.get("text_fingerprint_changed") or _pregate_diff.get("route_changed"):
            record_stage_snapshot(out, "final_emission_gate_after_pregate_containment")
            record_stage_transition(
                out,
                "gate_before_pregate_containment",
                "final_emission_gate_after_pregate_containment",
                snap_before_pregate,
                snap_after_pregate,
            )
    text = _normalize_text(out.get("player_facing_text"))
    return GatePreflightTelemetryResult(
        pre_gate_text=refreshed_pre_gate_text,
        text=text,
    )
