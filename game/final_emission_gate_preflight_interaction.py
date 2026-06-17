"""Interaction-context inspection metadata for gate entry/preflight (Cycle BN7).

Metadata-only setup for :func:`game.final_emission_gate_context.initialize_gate_execution_context`.
Preserves exact derived field values; no routing or terminal enforcement.
"""
from __future__ import annotations

from typing import Any, Dict, NamedTuple

from game.interaction_context import inspect as inspect_interaction_context


class GatePreflightInteractionMetadata(NamedTuple):
    """Interaction inspection and resolution-derived metadata for gate preflight."""

    inspected: Dict[str, Any]
    active_interlocutor: str
    npc_id_for_meta: str
    res_kind: str
    social_ic: str


def resolve_gate_preflight_interaction_metadata(
    session: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
) -> GatePreflightInteractionMetadata:
    """Inspect session interaction context and derive gate preflight metadata fields."""
    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    active_interlocutor = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    npc_id_for_meta = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        npc_id_for_meta = str(sp.get("npc_id") or "").strip()

    res_kind = str((eff_resolution or {}).get("kind") or "").strip().lower() if isinstance(eff_resolution, dict) else ""
    social_ic = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        social_ic = str(sp.get("social_intent_class") or "").strip().lower()
    return GatePreflightInteractionMetadata(
        inspected=inspected,
        active_interlocutor=active_interlocutor,
        npc_id_for_meta=npc_id_for_meta,
        res_kind=res_kind,
        social_ic=social_ic,
    )
