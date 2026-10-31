"""Narration-constraint debug merge owner for final emission gate terminal tail.

Wires response-type debug, visibility contract, speaker selection, and speaker-contract
enforcement into ``metadata.emission_debug.narration_constraint_debug`` on gm output and
resolution sidecars. Called by :mod:`game.final_emission_terminal_pipeline` after IC attach.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict

from game.final_emission_meta import (
    build_narration_constraint_debug,
    merge_narration_constraint_debug_meta,
)
from game.narration_visibility import build_narration_visibility_contract
from game.speaker_contract_enforcement import get_speaker_selection_contract


def _resolve_narration_constraint_debug_visibility_contract(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    try:
        contract = build_narration_visibility_contract(
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
    except Exception:
        return {}
    return contract if isinstance(contract, dict) else {}


def _current_speaker_binding_bridge(out: Dict[str, Any]) -> Dict[str, Any]:
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    em = md.get("emission_debug") if isinstance(md.get("emission_debug"), dict) else {}
    bridge = em.get("interaction_continuity_speaker_binding_bridge")
    return bridge if isinstance(bridge, dict) else {}


def merge_narration_constraint_debug_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    response_type_debug: Mapping[str, Any] | None,
    speaker_contract_enforcement: Mapping[str, Any] | None = None,
) -> None:
    """Merge narration-constraint debug into gm output and resolution metadata sidecars."""
    md_out = out.setdefault("metadata", {})
    if not isinstance(md_out, dict):
        return

    visibility_meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    speaker_selection_contract = get_speaker_selection_contract(
        eff_resolution if isinstance(eff_resolution, dict) else resolution,
        metadata=md_out,
        trace=out.get("trace") if isinstance(out.get("trace"), dict) else None,
    )
    payload = build_narration_constraint_debug(
        response_type_debug=response_type_debug,
        narration_visibility=_resolve_narration_constraint_debug_visibility_contract(
            session=session,
            scene=scene,
            world=world,
        ),
        visibility_meta=visibility_meta,
        speaker_selection_contract=speaker_selection_contract,
        speaker_contract_enforcement=speaker_contract_enforcement,
        speaker_binding_bridge=_current_speaker_binding_bridge(out),
    )
    merge_narration_constraint_debug_meta(md_out, payload)

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            merge_narration_constraint_debug_meta(md_r, payload)

    if eff_resolution is not None and eff_resolution is not resolution:
        md_eff = eff_resolution.setdefault("metadata", {})
        if isinstance(md_eff, dict):
            merge_narration_constraint_debug_meta(md_eff, payload)
