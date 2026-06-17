"""Strict-social routing and suppression for gate entry/preflight (Cycle BN8).

Routing setup for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
Preserves exact call order, sanitizer context, and in-place ``out`` mutations.
"""
from __future__ import annotations

from typing import Any, Dict, List, NamedTuple

from game.final_emission_gate_preflight_upstream import upstream_prepared_emission_payload
from game.final_emission_text import _normalize_text
from game.output_sanitizer import sanitize_player_facing_output
from game.social_exchange_emission import (
    effective_strict_social_resolution_for_emission,
    merged_player_prompt_for_gate,
    strict_social_emission_will_apply,
    strict_social_suppress_non_native_coercion_for_narration_beat,
)


class GatePreflightStrictSocialRouting(NamedTuple):
    """Strict-social routing state produced before interaction metadata resolution."""

    eff_resolution: Any
    strict_social_turn: bool
    strict_social_suppressed_non_social_turn: bool
    strict_social_suppression_reason: str | None
    original_coercion_reason: str
    coercion_reason: str
    pre_gate_text: str


def resolve_gate_preflight_strict_social_routing(
    out: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    pre_gate_text: str,
    tag_list: List[str],
) -> GatePreflightStrictSocialRouting:
    """Resolve strict-social route, apply suppression sanitizer when required, and return routing state."""
    sid = str(scene_id or "").strip()
    eff_resolution, _effective_social_route, coercion_reason = effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
    )
    strict_social_turn = strict_social_emission_will_apply(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
    )
    merged_for_suppress = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    strict_social_suppressed_non_social_turn = False
    strict_social_suppression_reason: str | None = None
    original_coercion_reason = coercion_reason
    refreshed_pre_gate_text = pre_gate_text
    if strict_social_turn:
        do_suppress, sup_reason = strict_social_suppress_non_native_coercion_for_narration_beat(
            resolution if isinstance(resolution, dict) else None,
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            sid,
            coercion_reason=coercion_reason,
            merged_player_prompt=merged_for_suppress,
        )
        if do_suppress:
            strict_social_suppressed_non_social_turn = True
            strict_social_suppression_reason = sup_reason
            strict_social_turn = False
            refreshed_pre_gate_text = _normalize_text(
                sanitize_player_facing_output(
                    refreshed_pre_gate_text,
                    {
                        "resolution": resolution if isinstance(resolution, dict) else None,
                        "include_resolution": True,
                        "session": session if isinstance(session, dict) else None,
                        "scene_id": sid,
                        "world": world if isinstance(world, dict) else None,
                        "tags": tag_list,
                        "sanitizer_boundary_mode": "strip_only",
                        "upstream_prepared_emission": upstream_prepared_emission_payload(out),
                    },
                )
            )
            eff_resolution = resolution if isinstance(resolution, dict) else None
            coercion_reason = f"{original_coercion_reason}|suppressed_non_social_narration:{sup_reason}"
            out["player_facing_text"] = refreshed_pre_gate_text
    return GatePreflightStrictSocialRouting(
        eff_resolution=eff_resolution,
        strict_social_turn=strict_social_turn,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        strict_social_suppression_reason=strict_social_suppression_reason,
        original_coercion_reason=original_coercion_reason,
        coercion_reason=coercion_reason,
        pre_gate_text=refreshed_pre_gate_text,
    )
