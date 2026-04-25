"""Runtime narration plan bundle seam (CTIR → Narrative Plan → prompt_context).

**Non-negotiable ownership (C1 seam promotion):**

- **CTIR** is the sole narration-*semantic* source for resolved turns: bounded meaning
  snapshot attached on ``session`` (see :mod:`game.ctir_runtime`).
- **Narrative Plan** is the sole narration-*facing semantic projection*: deterministic
  structural bridge produced only by :func:`game.narrative_planning.build_narrative_plan`
  from CTIR plus explicitly passed bounded non-CTIR slices (visibility allowlist, public
  scene labels, compressed log summaries, shipped ``narration_obligations`` /
  ``response_policy`` for mode contract, etc.). The plan’s ``narrative_roles`` block (N3) is
  abstract composition shaping only—never a second authority alongside CTIR. After a
  successful build, :func:`game.narrative_plan_upstream.apply_upstream_narrative_role_reemphasis`
  may bump bounded ``emphasis_band`` values only (trusted plans); it never edits CTIR,
  contracts, or :mod:`game.final_emission_repairs` surfaces.
- :mod:`game.prompt_context` is a **renderer and packager** only: it may map,
  compress, and attach already-owned artifacts into the model payload. It must **not**
  perform fresh semantic derivation from raw engine state, raw ``resolution`` dict
  meaning, or ad-hoc scene/public-state interpretation to invent alternate narration
  structure when CTIR is attached—except for bounded formatting and packaging of slices
  owned upstream (including the narrative plan bundle).
- **N5:** ``renderer_inputs["referent_tracking"]`` is a deep copy of the full artifact
  (optional root ``clause_referent_plan`` included). Transport only; construction stays
  in :mod:`game.referent_tracking` (``docs/clause_level_referent_tracking.md``).

Operator-facing audit names (see ``plan_metadata``): ``narration_plan_bundle_error``;
``semantic_bypass_blocked`` corresponds to the requested ``planner_bypass_blocked``
signal (the literal ``planner_`` prefix is reserved as an *author* channel key shape in
:mod:`game.state_channels` and would be stripped from nested model payloads).
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any

from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, get_attached_ctir
from game.interaction_context import build_speaker_selection_contract, response_type_context_snapshot
from game.interaction_continuity import build_interaction_continuity_contract
from game.narrative_plan_upstream import (
    apply_upstream_narrative_role_reemphasis,
    clear_session_narration_resume_entry_pending,
    compute_narrative_plan_for_bundle_from_head,
    interaction_context_snapshot_from_ctir_semantics,
    pending_lead_ids_from_active_pending,
    session_interaction_slice_for_narrative_plan,
)
from game.narrative_planning import NARRATIVE_PLAN_VERSION
from game.referent_tracking import build_referent_tracking_artifact
from game.response_type_gating import derive_response_type_contract
from game.response_policy_contracts import peek_response_type_contract_from_resolution
from game.turn_packet import build_turn_packet

SESSION_NARRATION_PLAN_BUNDLE_KEY = "_runtime_narration_plan_bundle_v1"
SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY = "_runtime_narration_plan_bundle_stamp_v1"
NARRATIVE_PLAN_BUNDLE_VERSION = 1


def public_narrative_plan_projection_for_prompt(full_plan: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Compact ``narrative_plan`` for the model prompt: copy only bundle-owned structural fields.

    Strips plan ``debug``, ``resolution_meta``, ``recent_compressed_events``, and other
    non-prompt slices so :mod:`game.prompt_context` does not ship a second full planner blob.
    """
    if not isinstance(full_plan, Mapping) or not full_plan:
        return None
    out: dict[str, Any] = {}
    if "version" in full_plan:
        out["version"] = full_plan["version"]
    nm = full_plan.get("narrative_mode")
    if isinstance(nm, str) and nm.strip():
        out["narrative_mode"] = str(nm).strip()
    for key in ("role_allocation", "scene_anchors", "active_pressures"):
        val = full_plan.get(key)
        if isinstance(val, Mapping):
            out[key] = copy.deepcopy(val)
    for key in ("required_new_information", "allowable_entity_references"):
        val = full_plan.get(key)
        if isinstance(val, list):
            out[key] = copy.deepcopy(val)
    nr = full_plan.get("narrative_roles")
    if isinstance(nr, Mapping) and nr:
        out["narrative_roles"] = copy.deepcopy(nr)
    nmc = full_plan.get("narrative_mode_contract")
    if isinstance(nmc, Mapping) and nmc:
        out["narrative_mode_contract"] = copy.deepcopy(nmc)
    so = full_plan.get("scene_opening")
    if isinstance(so, Mapping) and so:
        out["scene_opening"] = copy.deepcopy(so)
    ao = full_plan.get("action_outcome")
    if isinstance(ao, Mapping) and ao:
        out["action_outcome"] = copy.deepcopy(ao)
    return out if out else None


def get_attached_narration_plan_bundle(container: MutableMapping[str, Any] | None) -> dict[str, Any] | None:
    raw = container.get(SESSION_NARRATION_PLAN_BUNDLE_KEY) if isinstance(container, MutableMapping) else None
    return dict(raw) if isinstance(raw, dict) else None


def get_narration_plan_bundle_stamp(container: MutableMapping[str, Any] | None) -> str:
    if not isinstance(container, MutableMapping):
        return ""
    return str(container.get(SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY) or "").strip()


def detach_narration_plan_bundle(container: MutableMapping[str, Any] | None) -> None:
    if not isinstance(container, MutableMapping):
        return
    container.pop(SESSION_NARRATION_PLAN_BUNDLE_KEY, None)
    container.pop(SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY, None)


def attach_narration_plan_bundle(container: MutableMapping[str, Any], bundle: dict[str, Any]) -> None:
    container[SESSION_NARRATION_PLAN_BUNDLE_KEY] = bundle


def ensure_narration_plan_bundle_for_turn(
    container: MutableMapping[str, Any],
    *,
    turn_stamp: str,
    builder: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Return existing bundle when *turn_stamp* matches; otherwise build via *builder* and attach."""
    existing = get_attached_narration_plan_bundle(container)
    stamp_ok = get_narration_plan_bundle_stamp(container) == turn_stamp
    if existing is not None and stamp_ok:
        return existing
    built = builder()
    attach_narration_plan_bundle(container, built)
    container[SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY] = turn_stamp
    return built


def _assemble_plan_adjacent_renderer_inputs(
    *,
    narration_context_kwargs: dict[str, Any],
    head: dict[str, Any],
    narrative_plan: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Build turn_packet + referent_tracking at the bundle seam (upstream of prompt_context)."""
    session = narration_context_kwargs.get("session")
    world = narration_context_kwargs.get("world")
    scene = narration_context_kwargs.get("scene")
    user_text = str(narration_context_kwargs.get("user_text") or "")
    ctir_obj = head.get("ctir_obj")
    resolution_sem = head.get("resolution_sem")
    interaction_sem = head.get("interaction_sem")
    response_policy = head.get("response_policy")
    session_view = head.get("session_view")
    visibility_contract = head.get("visibility_contract")
    narration_obligations = head.get("narration_obligations")
    interaction_continuity = head.get("interaction_continuity")
    active_pending_leads = head.get("active_pending_leads")
    runtime = head.get("runtime")
    scene_state_anchor_contract = head.get("scene_state_anchor_contract")
    scene_pub_id = str(head.get("scene_pub_id") or "").strip()
    wp_projection = head.get("wp_projection")

    if not isinstance(session, dict) or not isinstance(world, dict):
        return None, None
    if not isinstance(response_policy, dict) or not isinstance(interaction_continuity, dict):
        return None, None
    if not isinstance(narration_obligations, dict):
        return None, None

    scene_id_for_speaker = scene_pub_id or (
        str((session.get("scene_state") or {}).get("active_scene_id") or "").strip()
        if isinstance(session, dict)
        else ""
    )
    speaker_selection = build_speaker_selection_contract(
        session,
        world,
        scene_id_for_speaker,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
    )
    interaction_for_rtc = (
        interaction_context_snapshot_from_ctir_semantics(
            interaction_sem if isinstance(interaction_sem, dict) else None
        )
        if ctir_obj is not None
        else response_type_context_snapshot(session)
    )
    _rtc_policy = response_policy.get("response_type_contract")
    if isinstance(_rtc_policy, dict):
        rtc_for_social_structure = _rtc_policy
    else:
        rtc_peeked = peek_response_type_contract_from_resolution(resolution_sem)
        rtc_for_social_structure = rtc_peeked or derive_response_type_contract(
            segmented_turn=None,
            normalized_action=None,
            resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
            interaction_context=interaction_for_rtc,
            directed_social_entry=None,
            route_choice=None,
            raw_player_text=user_text,
        ).to_dict()
    interaction_continuity_contract = build_interaction_continuity_contract(
        session,
        scene_id=scene_pub_id or None,
        scene_envelope=scene if isinstance(scene, dict) else None,
        world=world,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
    )

    _turn_packet = build_turn_packet(
        response_policy=response_policy,
        scene_id=scene_pub_id or None,
        player_text=user_text,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        interaction_continuity=interaction_continuity,
        narration_obligations=narration_obligations,
        last_human_adjacent_continuity=(
            runtime.get("last_human_adjacent_continuity") if isinstance(runtime, dict) else None
        ),
        response_type=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        sources_used=["game.narration_plan_bundle._assemble_plan_adjacent_renderer_inputs"],
    )
    _plids_for_referent = pending_lead_ids_from_active_pending(
        active_pending_leads if isinstance(active_pending_leads, list) else None
    )
    _session_interaction_for_referent = session_interaction_slice_for_narrative_plan(
        session_view if isinstance(session_view, dict) else None,
        _plids_for_referent,
    )
    referent_tracking = build_referent_tracking_artifact(
        narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
        speaker_selection=speaker_selection if isinstance(speaker_selection, dict) else None,
        interaction_continuity=interaction_continuity_contract if isinstance(interaction_continuity_contract, dict) else None,
        session_interaction=_session_interaction_for_referent if _session_interaction_for_referent else None,
        narrative_plan=narrative_plan if isinstance(narrative_plan, dict) else None,
        turn_packet=_turn_packet if isinstance(_turn_packet, dict) else None,
    )
    if isinstance(_turn_packet, dict):
        _turn_packet["referent_tracking_compact"] = {
            "referent_artifact_version": referent_tracking.get("version"),
            "active_interaction_target": referent_tracking.get("active_interaction_target"),
            "referential_ambiguity_class": referent_tracking.get("referential_ambiguity_class"),
            "ambiguity_risk": referent_tracking.get("ambiguity_risk"),
        }
        _tp_dbg = _turn_packet.get("debug")
        if isinstance(_tp_dbg, dict):
            _turn_packet["debug"] = {
                **_tp_dbg,
                "world_progression": {
                    "changed_nodes_head": list((wp_projection or {}).get("changed_node_ids") or [])[:8],
                    "active_projects_n": len((wp_projection or {}).get("active_projects") or []),
                    "world_clocks_n": len((wp_projection or {}).get("world_clocks") or []),
                },
            }
    return _turn_packet if isinstance(_turn_packet, dict) else None, referent_tracking


def build_narration_plan_bundle(
    *,
    session: dict[str, Any],
    narration_context_kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Construct JSON-safe narration plan bundle from CTIR + bounded renderer-side inputs.

    Reads attached CTIR only for *semantic* planning (via :func:`game.narrative_planning.build_narrative_plan`);
    ``narration_context_kwargs`` must be the same keyword bundle passed to
    :func:`game.prompt_context.build_narration_context` so bounded slices match the renderer path.
    """
    from game.prompt_context import _build_narration_context_head_state

    ctir_obj = get_attached_ctir(session if isinstance(session, dict) else None)
    if not isinstance(ctir_obj, dict):
        return {
            "plan_metadata": {
                "ctir_stamp": str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip(),
                "narrative_plan_bundle_version": NARRATIVE_PLAN_BUNDLE_VERSION,
                "narrative_plan_version": NARRATIVE_PLAN_VERSION,
                "narration_plan_bundle_error": None,
                "semantic_bypass_blocked": False,
            },
            "narrative_plan": None,
            "renderer_inputs": {},
        }

    head = _build_narration_context_head_state(**narration_context_kwargs)
    narrative_plan, narrative_plan_build_error, planning_session_interaction = compute_narrative_plan_for_bundle_from_head(
        head,
        user_text=str(narration_context_kwargs.get("user_text") or ""),
    )
    if isinstance(narrative_plan, dict) and not narrative_plan_build_error:
        narrative_plan, _ = apply_upstream_narrative_role_reemphasis(narrative_plan)
        clear_session_narration_resume_entry_pending(session)
    ctir_stamp = str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip()
    bypass = bool(narrative_plan_build_error) or (narrative_plan is None)
    plan_meta: dict[str, Any] = {
        "ctir_stamp": ctir_stamp,
        "narrative_plan_bundle_version": NARRATIVE_PLAN_BUNDLE_VERSION,
        "narrative_plan_version": NARRATIVE_PLAN_VERSION,
        "narration_plan_bundle_error": narrative_plan_build_error,
        "semantic_bypass_blocked": bypass,
        "planning_session_interaction": dict(planning_session_interaction)
        if isinstance(planning_session_interaction, dict)
        else {},
    }
    rp = head.get("response_policy")
    turn_packet, referent_tracking = _assemble_plan_adjacent_renderer_inputs(
        narration_context_kwargs=narration_context_kwargs,
        head=head,
        narrative_plan=narrative_plan if isinstance(narrative_plan, dict) else None,
    )
    bundle: dict[str, Any] = {
        "plan_metadata": plan_meta,
        "narrative_plan": narrative_plan,
        "renderer_inputs": {
            "response_policy": copy.deepcopy(rp) if isinstance(rp, dict) else {},
            "narration_visibility": copy.deepcopy(head.get("narration_visibility")),
            "scene_state_anchor_contract": copy.deepcopy(head.get("scene_state_anchor_contract")),
            "narration_obligations": copy.deepcopy(head.get("narration_obligations")),
            "turn_packet": copy.deepcopy(turn_packet) if isinstance(turn_packet, dict) else None,
            # Full artifact including optional N5 ``clause_referent_plan``; transport-only deepcopy.
            "referent_tracking": copy.deepcopy(referent_tracking) if isinstance(referent_tracking, dict) else None,
        },
    }
    return bundle
