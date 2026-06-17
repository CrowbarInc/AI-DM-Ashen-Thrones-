"""Scene emit integrity travelish-context detection and global fallback selection.

Pure assessment and visibility fallback candidate building for travel-like turns.
Does not own gate fallback ordering or sealed-fallback provider routing.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.final_emission_text import _global_narrative_fallback_stock_line
from game.final_emission_visibility_fallback import (
    VisibilitySelectedFallback,
    first_mention_composition_meta as _first_mention_composition_meta,
)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


_SCENE_EMIT_INTEGRITY_TRAVEL_KINDS = frozenset({"scene_transition", "travel"})

# Deterministic diegetic line when a scene-anchored global stock line would assert the wrong place.
_SCENE_EMIT_INTEGRITY_SAFE_FALLBACK_LINE = (
    "You move as if to cross into it, but the way stays unfinished and leaves you where you began."
)


def _resolution_emit_integrity_flat(resolution: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(resolution, dict):
        return {}
    md = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}

    def pick(key: str) -> Any:
        if key in resolution:
            return resolution[key]
        if key in md:
            return md[key]
        return None

    out: Dict[str, Any] = {}
    for key in (
        "kind",
        "resolved_transition",
        "target_scene_id",
        "blocked_incompatible_scene_transition",
        "destination_compatibility_checked",
        "destination_compatibility_passed",
        "destination_compatibility_failure_reason",
        "destination_binding_source",
        "destination_binding_conflict",
        "destination_binding_resolution_reason",
        "destination_semantic_kind",
    ):
        val = pick(key)
        if val is not None:
            out[key] = val
    return out


def _scene_emit_integrity_travelish_context(
    *,
    res_kind: str,
    response_type_required: str,
    authoritative_resolution: Dict[str, Any] | None,
) -> bool:
    rk = str(res_kind or "").strip().lower()
    if rk in _SCENE_EMIT_INTEGRITY_TRAVEL_KINDS:
        return True
    rt = str(response_type_required or "").strip().lower()
    if rt == "action_outcome":
        return True
    flat = _resolution_emit_integrity_flat(authoritative_resolution)
    kind = str(flat.get("kind") or "").strip().lower()
    return kind in _SCENE_EMIT_INTEGRITY_TRAVEL_KINDS


def _collect_scene_emit_integrity_failure_reasons(
    *,
    authoritative_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> tuple[List[str], str | None]:
    reasons: List[str] = []
    named: str | None = None
    flat = _resolution_emit_integrity_flat(authoritative_resolution)
    sem = str(flat.get("destination_semantic_kind") or "").strip().lower()
    if sem == "named_place":
        named = str(flat.get("destination_binding_source") or "").strip() or "named_place"

    if flat.get("blocked_incompatible_scene_transition") is True:
        reasons.append("blocked_incompatible_scene_transition")

    if flat.get("destination_compatibility_checked") is True and flat.get("destination_compatibility_passed") is not True:
        reasons.append("destination_compatibility_failed")

    resolved = flat.get("resolved_transition") is True
    tgt = str(flat.get("target_scene_id") or "").strip()
    active = str((session or {}).get("active_scene_id") or "").strip() if isinstance(session, dict) else ""
    sid = str(scene_id or "").strip()
    inner_id = ""
    if isinstance(scene, dict):
        inner = scene.get("scene") if isinstance(scene.get("scene"), dict) else scene
        inner_id = str((inner or {}).get("id") or "").strip()

    if resolved and tgt:
        if active and tgt != active:
            reasons.append("resolved_transition_target_session_mismatch")
        if active and sid and sid != active:
            reasons.append("emission_scene_id_session_mismatch")
        if inner_id and active and inner_id != active:
            reasons.append("scene_envelope_active_mismatch")

    dbs = str(flat.get("destination_binding_source") or "").strip()
    if dbs == "explicit_named_place_unresolved":
        reasons.append("explicit_named_place_unresolved")
    elif (
        flat.get("destination_binding_conflict") is True
        and not resolved
        and str(flat.get("kind") or "").strip().lower() in _SCENE_EMIT_INTEGRITY_TRAVEL_KINDS
        and sem == "named_place"
    ):
        reasons.append("named_place_binding_conflict_unresolved")

    return _dedupe_preserve_order(reasons), named


def _compute_scene_emit_integrity_assessment(
    *,
    authoritative_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
    res_kind: str,
    response_type_required: str,
) -> Dict[str, Any]:
    travelish = _scene_emit_integrity_travelish_context(
        res_kind=res_kind,
        response_type_required=response_type_required,
        authoritative_resolution=authoritative_resolution,
    )
    if not travelish:
        return {
            "scene_integrity_checked": True,
            "scene_integrity_passed": True,
            "scene_integrity_failure_reasons": [],
            "scene_integrity_blocked_global_fallback": False,
            "scene_integrity_named_destination": None,
        }
    reasons, named = _collect_scene_emit_integrity_failure_reasons(
        authoritative_resolution=authoritative_resolution,
        session=session,
        scene=scene,
        scene_id=scene_id,
    )
    return {
        "scene_integrity_checked": True,
        "scene_integrity_passed": not reasons,
        "scene_integrity_failure_reasons": reasons,
        "scene_integrity_blocked_global_fallback": bool(reasons),
        "scene_integrity_named_destination": named,
    }


def _scene_emit_integrity_global_fallback_selection(
    scene: Dict[str, Any] | None,
    scene_id: str,
    *,
    authoritative_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    res_kind: str,
    response_type_required: str,
) -> VisibilitySelectedFallback:
    """Canonical global scene / scene-emit-integrity safe fallback selection."""
    travelish = _scene_emit_integrity_travelish_context(
        res_kind=res_kind,
        response_type_required=response_type_required,
        authoritative_resolution=authoritative_resolution,
    )
    if not travelish:
        return VisibilitySelectedFallback(
            text=_global_narrative_fallback_stock_line(scene if isinstance(scene, dict) else None, scene_id=scene_id),
            fallback_pool="global_scene_narrative",
            fallback_kind="narrative_safe_fallback",
            final_emitted_source="global_scene_fallback",
            fallback_strategy="standard_safe_fallback",
            fallback_candidate_source="global_scene_fallback",
            composition_meta=_first_mention_composition_meta(),
        )
    reasons, _named = _collect_scene_emit_integrity_failure_reasons(
        authoritative_resolution=authoritative_resolution,
        session=session,
        scene=scene,
        scene_id=scene_id,
    )
    if reasons:
        return VisibilitySelectedFallback(
            text=_SCENE_EMIT_INTEGRITY_SAFE_FALLBACK_LINE,
            fallback_pool="scene_emit_integrity_neutral",
            fallback_kind="scene_emit_integrity_safe_fallback",
            final_emitted_source="scene_emit_integrity_safe_fallback",
            fallback_strategy="standard_safe_fallback",
            fallback_candidate_source="scene_emit_integrity_safe_fallback",
            composition_meta=_first_mention_composition_meta(),
        )
    return VisibilitySelectedFallback(
        text=_global_narrative_fallback_stock_line(scene if isinstance(scene, dict) else None, scene_id=scene_id),
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta=_first_mention_composition_meta(),
    )
