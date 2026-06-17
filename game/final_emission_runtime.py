"""API/runtime seam for final player-facing emission (Cycle BN1 entry).

``game.final_emission_gate`` remains the canonical **orchestration owner** for layer
order, repairs, FEM packaging, and telemetry. This module is the **single
production-facing delegate** for runtime/API turn finalization: callers outside the
gate orchestration cluster should import :func:`finalize_player_facing_emission`
here rather than :func:`game.final_emission_gate.apply_final_emission_gate`
directly.

Downstream integration tests should prefer
``tests.helpers.emission_smoke_assertions.apply_final_emission_gate_consumer``.
"""
from __future__ import annotations

from typing import Any, Dict

from game.final_emission_gate import apply_final_emission_gate


def finalize_player_facing_emission(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    scene: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Delegate API/runtime finalization to the canonical final-emission gate."""
    return apply_final_emission_gate(
        gm_output,
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        scene=scene,
        world=world,
    )
