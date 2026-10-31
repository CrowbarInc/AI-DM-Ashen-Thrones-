"""Branch-flag derivation for gate entry/preflight (Cycle BN10).

Pure derived-state for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
No routing, sanitization, or terminal enforcement.
"""
from __future__ import annotations

from typing import List, NamedTuple


class GatePreflightBranchFlags(NamedTuple):
    """Branch flags derived immediately before gate context assembly."""

    strict_social_active: bool
    coercion_used: bool
    retry_output: bool


def resolve_gate_preflight_branch_flags(
    *,
    strict_social_turn: bool,
    original_coercion_reason: str,
    tag_list: List[str],
) -> GatePreflightBranchFlags:
    """Derive strict-social, coercion, and retry branch flags for gate preflight."""
    strict_social_active = bool(strict_social_turn)
    coercion_used = (
        "|" in original_coercion_reason
        or "synthetic" in original_coercion_reason
        or "npc_directed_guard" in original_coercion_reason
    )
    retry_output = any(
        isinstance(t, str) and ("question_retry_fallback" in t or "social_exchange_retry_fallback" in t)
        for t in tag_list
    )
    return GatePreflightBranchFlags(
        strict_social_active=strict_social_active,
        coercion_used=coercion_used,
        retry_output=retry_output,
    )
