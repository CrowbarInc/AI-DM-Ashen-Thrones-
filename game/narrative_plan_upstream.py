"""Upstream-only helpers for CTIR → narrative plan construction (bundle / tooling seam).

This module is **not** a narration renderer. :mod:`game.prompt_context` consumes plans
and plan-adjacent inputs produced here (via :mod:`game.narration_plan_bundle`); it must
not silently re-invoke this planner for production CTIR-backed turns.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Set

from game.narrative_planning import build_narrative_plan
from game.response_policy_contracts import peek_response_type_contract_from_resolution
from game.response_type_gating import derive_response_type_contract


def interaction_context_snapshot_from_ctir_semantics(interaction_sem: Mapping[str, Any] | None) -> dict[str, Any]:
    """Shape CTIR interaction into the compact dict used by response-type derivation."""
    if not isinstance(interaction_sem, dict):
        return {}
    return {
        "active_interaction_target_id": str(interaction_sem.get("active_target_id") or "").strip() or None,
        "active_interaction_kind": str(interaction_sem.get("interaction_kind") or "").strip() or None,
        "interaction_mode": str(interaction_sem.get("interaction_mode") or "").strip() or None,
        "engagement_level": None,
        "conversation_privacy": None,
        "player_position_context": None,
    }


def published_entities_slice_for_narrative_planning(
    visibility_contract: Mapping[str, Any] | None,
) -> List[Dict[str, Any]]:
    if not isinstance(visibility_contract, Mapping):
        return []
    ids_raw = visibility_contract.get("visible_entity_ids") or []
    names_raw = visibility_contract.get("visible_entity_names") or []
    if not isinstance(ids_raw, list):
        return []
    names_list = names_raw if isinstance(names_raw, list) else []
    rows: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for i, raw_id in enumerate(ids_raw):
        eid = str(raw_id or "").strip()
        if not eid or eid in seen:
            continue
        seen.add(eid)
        row: Dict[str, Any] = {"entity_id": eid}
        if i < len(names_list):
            nm = str(names_list[i] or "").strip()
            if nm:
                row["display_name"] = nm
        rows.append(row)
        if len(rows) >= 48:
            break
    rows.sort(key=lambda r: str(r.get("entity_id") or ""))
    return rows


def public_scene_slice_for_narrative_plan(
    public_scene: Mapping[str, Any] | None,
    scene_state_anchor_contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    ps = public_scene if isinstance(public_scene, Mapping) else {}
    out: Dict[str, Any] = {}
    sid = str(ps.get("id") or "").strip()
    if sid:
        out["scene_id"] = sid
    title = str(ps.get("name") or ps.get("title") or "").strip()
    if title:
        out["scene_name"] = title[:160]
    loc = ps.get("location_tokens") or ps.get("location_anchors")
    if isinstance(loc, (list, tuple)):
        toks = [str(x).strip() for x in loc if isinstance(x, str) and str(x).strip()]
        if toks:
            out["location_tokens"] = toks[:16]
    elif isinstance(loc, str) and loc.strip():
        out["location_tokens"] = [loc.strip()[:160]]
    elif isinstance(scene_state_anchor_contract, Mapping):
        lt = scene_state_anchor_contract.get("location_tokens")
        if isinstance(lt, list) and lt:
            out["location_tokens"] = [
                str(x).strip() for x in lt if isinstance(x, str) and str(x).strip()
            ][:16]
    return out


def pending_lead_ids_from_active_pending(rows: Sequence[Any] | None) -> List[str]:
    if not rows:
        return []
    out: List[str] = []
    seen: Set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        lid = str(
            row.get("authoritative_lead_id") or row.get("lead_id") or row.get("id") or ""
        ).strip()
        if not lid or lid in seen:
            continue
        seen.add(lid)
        out.append(lid)
        if len(out) >= 48:
            break
    return sorted(out)


def session_interaction_slice_for_narrative_plan(
    session_view: Mapping[str, Any] | None,
    pending_lead_ids: Sequence[str],
) -> Dict[str, Any]:
    sv = session_view if isinstance(session_view, Mapping) else {}
    out: Dict[str, Any] = {}
    at = str(sv.get("active_interaction_target_id") or "").strip()
    if at:
        out["active_interaction_target_id"] = at
    pids = [str(x).strip() for x in pending_lead_ids if str(x).strip()]
    if pids:
        out["pending_lead_ids"] = pids[:48]
    return out


def compute_narrative_plan_for_bundle_from_head(
    head: Mapping[str, Any], *, user_text: str
) -> tuple[Dict[str, Any] | None, str | None]:
    """Build narrative plan from pre-assembled head state (bundle / offline tooling only)."""
    ctir_obj = head.get("ctir_obj")
    narrative_plan: Dict[str, Any] | None = None
    narrative_plan_build_error: str | None = None
    if ctir_obj is None:
        return None, None
    resolution_sem = head.get("resolution_sem")
    interaction_sem = head.get("interaction_sem")
    response_policy = head.get("response_policy")
    visibility_contract = head.get("visibility_contract")
    public_scene = head.get("public_scene")
    scene_state_anchor_contract = head.get("scene_state_anchor_contract")
    active_pending_leads = head.get("active_pending_leads")
    session_view = head.get("session_view")
    recent_log_compact = head.get("recent_log_compact")
    narration_obligations = head.get("narration_obligations")
    if not isinstance(response_policy, dict):
        return None, "response_policy_missing_for_narrative_plan"
    rp_mut = response_policy
    if isinstance(resolution_sem, dict):
        _rtc_peek_plan = peek_response_type_contract_from_resolution(resolution_sem)
        _ic_rtc_plan = interaction_context_snapshot_from_ctir_semantics(
            interaction_sem if isinstance(interaction_sem, dict) else None
        )
        _rtc_plan_dict = _rtc_peek_plan or derive_response_type_contract(
            segmented_turn=None,
            normalized_action=None,
            resolution=resolution_sem,
            interaction_context=_ic_rtc_plan,
            directed_social_entry=None,
            route_choice=None,
            raw_player_text=str(user_text or ""),
        ).to_dict()
        if isinstance(_rtc_plan_dict, dict):
            rp_mut["response_type_contract"] = _rtc_plan_dict
    try:
        _pub_ent = published_entities_slice_for_narrative_planning(
            visibility_contract if isinstance(visibility_contract, Mapping) else None
        )
        _pub_scene_slice = public_scene_slice_for_narrative_plan(
            public_scene if isinstance(public_scene, Mapping) else None,
            scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        )
        _plids = pending_lead_ids_from_active_pending(
            active_pending_leads if isinstance(active_pending_leads, list) else None
        )
        _sess_int = session_interaction_slice_for_narrative_plan(
            session_view if isinstance(session_view, dict) else None,
            _plids,
        )
        narrative_plan = build_narrative_plan(
            ctir=ctir_obj,
            session_interaction=_sess_int or None,
            public_scene_slice=_pub_scene_slice or None,
            published_entities=_pub_ent,
            recent_compressed_events=list(recent_log_compact or []),
            narration_obligations=narration_obligations if isinstance(narration_obligations, dict) else {},
            response_policy=rp_mut,
        )
        assert narrative_plan is None or isinstance(narrative_plan, dict)
    except Exception as exc:
        narrative_plan_build_error = f"{type(exc).__name__}: {exc}"
        narrative_plan = None
    return narrative_plan, narrative_plan_build_error
