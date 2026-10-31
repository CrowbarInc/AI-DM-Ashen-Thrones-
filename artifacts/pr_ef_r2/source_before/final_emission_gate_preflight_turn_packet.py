"""Response-policy and turn-packet setup for gate entry/preflight (Cycle BN6).

Top-of-preflight setup for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
Preserves exact call order and in-place ``out`` mutations; no routing or terminal enforcement.
"""
from __future__ import annotations

from typing import Any, Dict

from game.response_policy_contracts import materialize_response_policy_bundle
from game.turn_packet import get_turn_packet


def initialize_gate_preflight_turn_packet(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Materialize response policy and attach gate turn-packet cache to ``out``."""
    out = materialize_response_policy_bundle(out, session if isinstance(session, dict) else None)
    out["_gate_turn_packet_cache"] = get_turn_packet(
        out, out.get("response_policy"), out.get("prompt_context")
    )
    return out
