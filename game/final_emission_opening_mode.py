"""Opening mode detection and visible-anchor fallback candidate text.

Pure detection and candidate-text helpers. Fallback selection and gate
orchestration remain in :mod:`game.final_emission_opening_fallback` and
:mod:`game.final_emission_gate` respectively.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from game.final_emission_text import _normalize_text


def _narrative_mode_contract_from_gm_output(gm_output: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Return planner-shipped ``narrative_mode_contract`` from the plan / ``prompt_context`` seam only."""
    if not isinstance(gm_output, Mapping):
        return None
    pc = gm_output.get("prompt_context")
    if not isinstance(pc, Mapping):
        return None
    plan = pc.get("narrative_plan")
    if not isinstance(plan, Mapping):
        return None
    raw = plan.get("narrative_mode_contract")
    return dict(raw) if isinstance(raw, dict) else None


def _opening_mode_active_for_turn(gm_output: Mapping[str, Any] | None, resolution: Mapping[str, Any] | None) -> bool:
    if isinstance(resolution, Mapping):
        if str(resolution.get("kind") or "").strip().lower() == "scene_opening":
            return True
    nmc = _narrative_mode_contract_from_gm_output(gm_output)
    if isinstance(nmc, dict) and str(nmc.get("mode") or "").strip().lower() == "opening":
        return True
    if isinstance(gm_output, Mapping):
        pc = gm_output.get("prompt_context")
        if isinstance(pc, Mapping):
            ob = pc.get("narration_obligations")
            if isinstance(ob, Mapping) and bool(ob.get("is_opening_scene")):
                return True
            ri = pc.get("renderer_inputs")
            if isinstance(ri, Mapping):
                ob2 = ri.get("narration_obligations")
                if isinstance(ob2, Mapping) and bool(ob2.get("is_opening_scene")):
                    return True
    return False


def _opening_visible_anchor_fallback_text(gm_output: Mapping[str, Any] | None) -> str:
    """Opening-safe fallback built strictly from shipped visible anchors (no invented facts)."""
    if not isinstance(gm_output, Mapping):
        return ""
    pc = gm_output.get("prompt_context")
    if not isinstance(pc, Mapping):
        return ""
    plan = pc.get("narrative_plan")
    if not isinstance(plan, Mapping):
        return ""

    scene_opening = plan.get("scene_opening") if isinstance(plan.get("scene_opening"), Mapping) else {}
    scene_anchors = plan.get("scene_anchors") if isinstance(plan.get("scene_anchors"), Mapping) else {}
    active_pressures = plan.get("active_pressures") if isinstance(plan.get("active_pressures"), Mapping) else {}

    # Location anchor: prefer the opening projection (already public-token curated), then scene_anchors.
    loc_list: list[str] = []
    for raw in (scene_opening.get("location_anchors"), scene_anchors.get("location_anchors")):
        if isinstance(raw, (list, tuple)):
            loc_list = [str(x).strip() for x in raw if isinstance(x, str) and str(x).strip()]
            if loc_list:
                break
        elif isinstance(raw, str) and raw.strip():
            loc_list = [raw.strip()]
            break
    loc = loc_list[0] if loc_list else ""

    # Actor/opportunity anchor: prefer a published descriptor, not an internal entity id.
    actor_desc = ""
    aer = plan.get("allowable_entity_references")
    if isinstance(aer, list):
        for row in aer:
            if not isinstance(row, Mapping):
                continue
            d = row.get("descriptor") or row.get("name") or row.get("display_name")
            if isinstance(d, str) and d.strip():
                actor_desc = d.strip()
                break

    # Immediate playable situation (non-directive): use contract-shaped pressure codes only.
    situation = ""
    ip = str(active_pressures.get("interaction_pressure") or "").strip().lower()
    if ip == "reply_expected":
        situation = "A reply is expected."
    elif ip == "check_pending":
        situation = "A check is pending."

    parts: list[str] = []
    if loc:
        parts.append(f"{loc}.")
    if actor_desc:
        parts.append(f"{actor_desc} is here.")
    if situation:
        parts.append(situation)
    return _normalize_text(" ".join(parts)).strip()
