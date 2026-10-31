"""Upstream prepared-emission attach for gate entry/preflight (Cycle BN5).

Setup-only for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
Preserves exact call order and in-place ``out`` mutations; no routing or terminal enforcement.
"""
from __future__ import annotations

from typing import Any, Dict

from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_EMISSION_KEY,
    maybe_attach_upstream_prepared_opening_fallback_payload,
    merge_upstream_prepared_emission_into_gm_output,
)


def apply_gate_preflight_upstream_attach(
    out: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """Merge upstream prepared emission and attach opening fallback payload into ``out``."""
    merge_upstream_prepared_emission_into_gm_output(
        out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
    )
    maybe_attach_upstream_prepared_opening_fallback_payload(
        out,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    return out


def upstream_prepared_emission_payload(out: Dict[str, Any]) -> Dict[str, Any] | None:
    """Return the upstream prepared emission dict from ``out`` when present."""
    payload = out.get(UPSTREAM_PREPARED_EMISSION_KEY)
    return payload if isinstance(payload, dict) else None
