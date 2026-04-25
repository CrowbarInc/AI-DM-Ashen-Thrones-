"""Upstream-only helpers for CTIR → narrative plan construction (bundle / tooling seam).

This module is **not** a narration renderer. :mod:`game.prompt_context` consumes plans
and plan-adjacent inputs produced here (via :mod:`game.narration_plan_bundle`); it must
not silently re-invoke this planner for production CTIR-backed turns. Full plans from
:func:`game.narrative_planning.build_narrative_plan` include Objective N3 ``narrative_roles``
(composition shaping only; CTIR remains authoritative).

**Objective N3 upstream role re-emphasis (this module only):** bounded, deterministic
composition-band bumps when validated plan metadata shows a *low* role emphasis alongside
clear omission-risk signals already encoded in sibling plan slices. Never invents facts,
mutates CTIR, alters contracts, or replaces downstream trimming—see
:func:`apply_upstream_narrative_role_reemphasis`.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Mapping, Sequence, Set

from game.narrative_planning import build_narrative_plan, validate_narrative_plan
from game.response_policy_contracts import peek_response_type_contract_from_resolution
from game.response_type_gating import derive_response_type_contract

# Transient session flag: first CTIR narration after snapshot restore (or tests) requests plan ``resume_entry``.
SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY = "_narration_resume_entry_pending"


def mark_session_narration_resume_entry_pending(session: Mapping[str, Any] | None) -> None:
    if isinstance(session, dict):
        session[SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY] = True


def clear_session_narration_resume_entry_pending(session: Mapping[str, Any] | None) -> None:
    if isinstance(session, dict):
        session.pop(SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY, None)


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


_N3_EMPHASIS_ORDER: tuple[str, ...] = ("minimal", "low", "moderate", "elevated", "high")
_N3_MAX_REPAIR_BAND = "elevated"
_N3_ROLE_FAMILY_ORDER: tuple[str, ...] = ("location_anchor", "actor_anchor", "pressure", "hook", "consequence")
_N3_UPSTREAM_ROLE_REPAIR_DEBUG_KEY = "n3_upstream_role_reemphasis"


def _n3_low_emphasis_band(band: Any) -> bool:
    return isinstance(band, str) and band in ("minimal", "low")


def _n3_bump_emphasis_band(band: str) -> str | None:
    if band not in _N3_EMPHASIS_ORDER:
        return None
    idx = _N3_EMPHASIS_ORDER.index(band)
    cap = _N3_EMPHASIS_ORDER.index(_N3_MAX_REPAIR_BAND)
    if idx >= cap:
        return None
    return _N3_EMPHASIS_ORDER[min(idx + 1, cap)]


def _n3_weak_role_families(plan: Mapping[str, Any]) -> List[str]:
    """Return role families judged weak (low emphasis + plan-derived omission risk)."""
    nr = plan.get("narrative_roles")
    if not isinstance(nr, Mapping):
        return []
    weak: List[str] = []
    for rk in _N3_ROLE_FAMILY_ORDER:
        sub = nr.get(rk)
        if not isinstance(sub, Mapping):
            continue
        band = sub.get("emphasis_band")
        if not _n3_low_emphasis_band(band):
            continue
        if rk == "location_anchor":
            if bool(sub.get("scene_id_present")) or bool(sub.get("scene_label_present")) or int(sub.get("location_token_n") or 0) > 0:
                weak.append(rk)
        elif rk == "actor_anchor":
            if (
                bool(sub.get("interlocutor_present"))
                or int(sub.get("relevant_actor_n") or 0) > 0
                or int(sub.get("visible_entity_handle_n") or 0) > 1
            ):
                weak.append(rk)
        elif rk == "pressure":
            ip = str(sub.get("interaction_pressure") or "").strip()
            if ip and ip != "none":
                weak.append(rk)
                continue
            if int(sub.get("pending_lead_n") or 0) > 0:
                weak.append(rk)
                continue
            if int(sub.get("context_code_n") or 0) > 0 or int(sub.get("tension_code_n") or 0) > 0:
                weak.append(rk)
                continue
            if bool(sub.get("world_pressure_present")) or int(sub.get("clock_summary_n") or 0) > 0:
                weak.append(rk)
        elif rk == "hook":
            if int(sub.get("required_new_information_n") or 0) > 0:
                weak.append(rk)
                continue
            if int(sub.get("distinct_information_kind_n") or 0) >= 2:
                weak.append(rk)
                continue
            tags = sub.get("information_kind_tags")
            if isinstance(tags, list) and any(isinstance(x, str) and str(x).strip() for x in tags):
                weak.append(rk)
        elif rk == "consequence":
            if bool(sub.get("has_consequence_information")) or bool(sub.get("has_state_or_mutation_information")):
                weak.append(rk)
                continue
            if bool(sub.get("has_transition_information")):
                weak.append(rk)
                continue
            oft = str(sub.get("outcome_forward_tier") or "").strip()
            if oft in ("elevated", "max"):
                weak.append(rk)
    return weak


def _n3_attach_role_repair_trace(plan: dict[str, Any], trace: Mapping[str, Any]) -> None:
    dbg = plan.get("debug")
    dbg_m = dict(dbg) if isinstance(dbg, dict) else {}
    dbg_m[_N3_UPSTREAM_ROLE_REPAIR_DEBUG_KEY] = dict(trace)
    plan["debug"] = dbg_m


def apply_upstream_narrative_role_reemphasis(plan: dict[str, Any] | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Bounded upstream re-emphasis for N3 ``narrative_roles`` (shaping only).

    Runs only when :func:`game.narrative_planning.validate_narrative_plan` passes with
    ``strict=False`` (same trust gate as :func:`game.prompt_context._narrative_plan_roles_trustworthy`).
    At most one emphasis step per weak family, capped at ``elevated``. A second call on the
    same plan object after a successful ``applied`` repair is a no-op (bands must not stack).
    No CTIR, state, contracts, or ``role_allocation`` changes. On any post-edit validation failure, the
    plan is left unchanged and ``applied`` is false.
    """
    # Trace is debug-only; consumers must not treat it as authority or scoring input.
    empty_trace: dict[str, Any] = {
        "version": 1,
        "applied": False,
        "weak_roles": [],
        "reinforced_families": [],
        "actions": [],
        "safety_notes": [],
        "skip_reason": None,
    }
    if not isinstance(plan, dict) or not plan:
        out_t = {**empty_trace, "skip_reason": "no_plan"}
        return None, out_t

    if validate_narrative_plan(plan, strict=False) is not None:
        # Do not mutate invalid / harness-tampered plans (Block B trustworthy gating).
        return plan, {**empty_trace, "skip_reason": "plan_not_trustworthy"}

    # One repair pass per plan object: a second call must not stack further band bumps
    # (weak families can remain low/minimal after a single step; re-entry would otherwise escalate).
    dbg_prior = plan.get("debug") if isinstance(plan.get("debug"), dict) else {}
    prior_trace = dbg_prior.get(_N3_UPSTREAM_ROLE_REPAIR_DEBUG_KEY)
    if isinstance(prior_trace, dict) and prior_trace.get("applied") is True:
        return plan, {
            **empty_trace,
            "skip_reason": "upstream_repair_idempotent_already_applied",
        }

    weak = _n3_weak_role_families(plan)
    if not weak:
        out_t = {**empty_trace, "skip_reason": "no_weak_roles"}
        _n3_attach_role_repair_trace(plan, out_t)
        return plan, out_t

    snap = copy.deepcopy(plan)
    nr = plan.get("narrative_roles")
    if not isinstance(nr, dict):
        out_t = {**empty_trace, "skip_reason": "narrative_roles_missing"}
        _n3_attach_role_repair_trace(plan, out_t)
        return plan, out_t

    actions: List[str] = []
    safety_notes: List[str] = []
    reinforced: List[str] = []
    for rk in weak:
        sub = nr.get(rk)
        if not isinstance(sub, dict):
            continue
        old_band = sub.get("emphasis_band")
        if not isinstance(old_band, str):
            continue
        new_band = _n3_bump_emphasis_band(old_band)
        if not new_band or new_band == old_band:
            continue
        sub["emphasis_band"] = new_band
        reinforced.append(rk)
        actions.append(f"bump_emphasis:{rk}:{old_band}->{new_band}")
        safety_notes.append(
            f"safe:{rk}:metadata_only_band_bump_no_counters_no_allocation_contract_slice_unchanged"
        )

    if not reinforced:
        out_t = {
            **empty_trace,
            "weak_roles": weak,
            "skip_reason": "no_bumpable_band",
        }
        _n3_attach_role_repair_trace(plan, out_t)
        return plan, out_t

    if validate_narrative_plan(plan, strict=False) is not None:
        plan.clear()
        plan.update(snap)
        out_t = {
            **empty_trace,
            "weak_roles": weak,
            "skip_reason": "validation_failed_after_repair_reverted",
        }
        _n3_attach_role_repair_trace(plan, out_t)
        return plan, out_t

    out_t = {
        "version": 1,
        "applied": True,
        "weak_roles": weak,
        "reinforced_families": sorted(set(reinforced)),
        "actions": actions,
        "safety_notes": safety_notes[:8],
        "skip_reason": None,
    }
    _n3_attach_role_repair_trace(plan, out_t)
    return plan, out_t


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
    if bool(sv.get("resume_entry")):
        out["resume_entry"] = True
    return out


def compute_narrative_plan_for_bundle_from_head(
    head: Mapping[str, Any], *, user_text: str
) -> tuple[Dict[str, Any] | None, str | None, Dict[str, Any]]:
    """Build narrative plan from pre-assembled head state (bundle / offline tooling only).

    Returns ``(plan, build_error, planning_session_interaction)`` for bundle metadata and seam audits.
    """
    ctir_obj = head.get("ctir_obj")
    narrative_plan: Dict[str, Any] | None = None
    narrative_plan_build_error: str | None = None
    if ctir_obj is None:
        return None, None, {}
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
        return None, "response_policy_missing_for_narrative_plan", {}
    rp_mut = response_policy
    _plids = pending_lead_ids_from_active_pending(
        active_pending_leads if isinstance(active_pending_leads, list) else None
    )
    planning_session_interaction = session_interaction_slice_for_narrative_plan(
        session_view if isinstance(session_view, dict) else None,
        _plids,
    )
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
        _no = narration_obligations if isinstance(narration_obligations, dict) else {}
        _vfs = head.get("visible_facts_for_prompt")
        _opening_strings = None
        if isinstance(_vfs, list) and _vfs:
            if _no.get("is_opening_scene"):
                _opening_strings = list(_vfs)
            elif bool(planning_session_interaction.get("resume_entry")):
                _opening_strings = list(_vfs)[:12]
        narrative_plan = build_narrative_plan(
            ctir=ctir_obj,
            session_interaction=planning_session_interaction or None,
            public_scene_slice=_pub_scene_slice or None,
            published_entities=_pub_ent,
            recent_compressed_events=list(recent_log_compact or []),
            narration_obligations=narration_obligations if isinstance(narration_obligations, dict) else {},
            response_policy=rp_mut,
            opening_visible_fact_strings=_opening_strings,
        )
        assert narrative_plan is None or isinstance(narrative_plan, dict)
    except Exception as exc:
        narrative_plan_build_error = f"{type(exc).__name__}: {exc}"
        narrative_plan = None
    return narrative_plan, narrative_plan_build_error, dict(planning_session_interaction)
