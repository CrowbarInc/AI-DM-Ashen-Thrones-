"""Opening gate attach-then-helper harness (Cycle AS1).

Mirrors opening-prep sequence at ``apply_final_emission_gate`` entry for owner tests in
``tests/test_final_emission_opening_fallback.py`` and downstream diegetic provenance wiring
in ``tests/test_diegetic_fallback_narration.py``. Uses private gate seams intentionally
only within this narrow harness — not via the broad ``final_emission_gate_fixtures`` hub.
"""
from __future__ import annotations

from typing import Any, Mapping

import game.final_emission_gate as feg
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
from game.upstream_response_repairs import maybe_attach_upstream_prepared_opening_fallback_payload

_DEFAULT_OPENING_HARNESS_RESOLUTION: dict[str, Any] = {"kind": "scene_opening", "prompt": "Start the campaign."}


def opening_gate_attach_then_opening_scene_safe_fallback_selection(
    gm_output: dict[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
) -> VisibilitySelectedFallback:
    """Run upstream attach then ``_opening_scene_safe_fallback_selection`` (Block O). Mutates *gm_output*."""
    resolved = dict(resolution) if isinstance(resolution, Mapping) else dict(_DEFAULT_OPENING_HARNESS_RESOLUTION)
    maybe_attach_upstream_prepared_opening_fallback_payload(gm_output, resolution=resolved)
    return feg._opening_scene_safe_fallback_selection(gm_output)


def opening_gate_attach_then_enforce_response_type_contract(
    candidate_text: str,
    gm_output: dict[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
    session: dict[str, Any] | None = None,
    scene_id: str = "frontier_gate",
    world: dict[str, Any] | None = None,
    strict_social_turn: bool = False,
    strict_social_suppressed_non_social_turn: bool = False,
    active_interlocutor: str = "",
) -> tuple[str, dict[str, Any]]:
    """Run upstream attach then ``_enforce_response_type_contract``. Mutates *gm_output* in place."""
    resolved = dict(resolution) if isinstance(resolution, Mapping) else dict(_DEFAULT_OPENING_HARNESS_RESOLUTION)
    maybe_attach_upstream_prepared_opening_fallback_payload(gm_output, resolution=resolved)
    return feg._enforce_response_type_contract(
        candidate_text,
        gm_output=gm_output,
        resolution=resolved,
        session=session if session is not None else {},
        scene_id=scene_id,
        world=world if world is not None else {},
        strict_social_turn=strict_social_turn,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        active_interlocutor=active_interlocutor,
    )
