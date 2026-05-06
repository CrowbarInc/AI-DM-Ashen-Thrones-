"""Planner-owned narration **head state** assembly (bundle / prompt seam).

Constructs the dict consumed by :mod:`game.narration_plan_bundle` and
:func:`game.prompt_context.build_narration_context`. This module is the canonical
owner of that preparation; :mod:`game.prompt_context` delegates here and remains a
renderer/packager for model-facing payloads.

See :mod:`game.planner_input_manifest` and :mod:`game.planner_seam_fencing` for
classification and CTIR fence metadata on ``response_policy``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Set

from game.ctir_runtime import get_attached_ctir
from game.leads import filter_pending_leads_for_active_follow_surface
from game.narration_visibility import _normalize_visibility_text, build_narration_visibility_contract
from game.opening_scene_realization import build_opening_scene_realization, opening_realization_none
from game.opening_visible_fact_selection import (
    OPENING_NARRATION_VISIBLE_FACT_MAX,
    select_opening_narration_visible_facts_with_telemetry,
)
from game.planner_seam_fencing import (
    GUARD_LEGACY_NO_CTIR_ONLY,
    GUARD_NON_CTIR_SEMANTIC_PATH,
    merge_planner_seam_trace,
)
from game.scene_state_anchoring import build_scene_state_anchor_contract
from game.planner_ctir_projection import (
    _CLASSIFIER_ONLY_INTENT_KEYS,
    _compress_recent_log,
    _compress_scene_runtime,
    _compress_session,
    _ctir_to_prompt_semantics,
    _session_view_overlay_from_ctir_interaction,
    _world_progression_projection_for_prompt,
    build_active_interlocutor_export,
    build_response_policy,
    derive_narration_obligations,
    deterministic_interlocutor_answer_style_hints,
)


def build_planner_head_state(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None,
    scene_runtime: Dict[str, Any] | None,
    *,
    public_scene: Dict[str, Any],
    discoverable_clues: List[str],
    gm_only_hidden_facts: List[str],
    gm_only_discoverable_locked: List[str],
    discovered_clue_records: List[Dict[str, Any]],
    undiscovered_clue_records: List[Dict[str, Any]],
    pending_leads: List[Any],
    intent: Dict[str, Any],
    world_state_view: Dict[str, Any],
    mode_instruction: str,
    recent_log_for_prompt: List[Dict[str, Any]],
    uncertainty_hint: Dict[str, Any] | None = None,
    prompt_profile: str = "full",
    include_non_public_prompt_keys: bool = False,
) -> Dict[str, Any]:
    """Assemble prompt-context head state through ``scene_state_anchor_contract`` (bundle / plan seam).

    Shared by :mod:`game.narration_plan_bundle` and :func:`game.prompt_context.build_narration_context`.
    """
    ctir_obj = get_attached_ctir(session if isinstance(session, dict) else None)
    if ctir_obj is not None:
        prompt_sem = _ctir_to_prompt_semantics(ctir_obj)
        resolution_sem: Dict[str, Any] | None = prompt_sem["resolution"]
        intent_sem: Dict[str, Any] = prompt_sem["intent"]
        interaction_sem: Dict[str, Any] = prompt_sem["interaction"]
    else:
        prompt_sem = None
        resolution_sem = resolution if isinstance(resolution, dict) else None
        intent_sem = intent if isinstance(intent, dict) else {}
        interaction_sem = {}
    intent_for_scene_payload: Dict[str, Any] = dict(intent_sem) if ctir_obj is not None else (intent if isinstance(intent, dict) else {})
    if ctir_obj is not None and isinstance(intent, dict):
        for _ik in _CLASSIFIER_ONLY_INTENT_KEYS:
            if _ik in intent:
                intent_for_scene_payload[_ik] = intent[_ik]
    wp_projection, wp_hint_lines = _world_progression_projection_for_prompt(
        ctir_obj=ctir_obj,
        world=world if isinstance(world, dict) else None,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    active_pending_leads = (
        filter_pending_leads_for_active_follow_surface(session, pending_leads)
        if isinstance(session, dict)
        else list(pending_leads or [])
    )
    runtime = _compress_scene_runtime(scene_runtime or {}, session=session if isinstance(session, dict) else None)
    session_view = _compress_session(session, world, public_scene)
    if ctir_obj is not None:
        session_view = _session_view_overlay_from_ctir_interaction(
            session_view,
            interaction_sem,
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            public_scene=public_scene if isinstance(public_scene, dict) else None,
        )
    narration_obligations = derive_narration_obligations(
        session_view=session_view,
        resolution=resolution_sem,
        intent=intent_sem,
        recent_log_for_prompt=recent_log_for_prompt,
        scene_runtime=runtime,
    )
    social_authority = bool(narration_obligations.get("suppress_non_social_emitters"))
    eff_uncertainty_hint = None if social_authority else uncertainty_hint
    recent_log_compact = (
        _compress_recent_log(recent_log_for_prompt) if recent_log_for_prompt else []
    )
    response_policy = build_response_policy(
        narration_obligations=narration_obligations,
        player_text=str(user_text or ""),
        resolution=resolution_sem,
        session_view=session_view,
        uncertainty_hint=eff_uncertainty_hint,
        recent_log_compact=recent_log_compact,
    )
    merge_planner_seam_trace(
        response_policy,
        {
            "head_state": {
                GUARD_LEGACY_NO_CTIR_ONLY: ctir_obj is None,
                GUARD_NON_CTIR_SEMANTIC_PATH: ctir_obj is None,
                "ctir_backed_head_state": ctir_obj is not None,
            }
        },
    )
    res = resolution_sem if isinstance(resolution_sem, dict) else {}
    state_changes = res.get("state_changes") if isinstance(res.get("state_changes"), dict) else {}
    scene_advancement = {
        "scene_transition_occurred": bool(res.get("resolved_transition")) or bool(state_changes.get("scene_transition_occurred")),
        "arrived_at_scene": bool(state_changes.get("arrived_at_scene")),
        "new_scene_context_available": bool(state_changes.get("new_scene_context_available")),
    }
    has_scene_change_context = any(bool(v) for v in scene_advancement.values())
    interaction_continuity = {
        'active_interaction_target_id': session_view.get('active_interaction_target_id'),
        'active_interaction_target_name': session_view.get('active_interaction_target_name'),
        'active_interaction_kind': session_view.get('active_interaction_kind'),
        'interaction_mode': session_view.get('interaction_mode'),
        'engagement_level': session_view.get('engagement_level'),
        'conversation_privacy': session_view.get('conversation_privacy'),
        'player_position_context': session_view.get('player_position_context'),
    }
    has_active_interlocutor = bool(str(interaction_continuity.get('active_interaction_target_id') or '').strip())
    scene_pub_id = str((public_scene or {}).get("id") or "").strip()
    # Presentation-only interlocutor export for prompt prose (CTIR-backed meaning stays on attached CTIR).
    interlocutor_export = build_active_interlocutor_export(session, world, public_scene)
    answer_style_hints_list = deterministic_interlocutor_answer_style_hints(
        interlocutor_export, scene_id=scene_pub_id
    )

    clue_records_all: List[Dict[str, Any]] = list(discovered_clue_records) + list(undiscovered_clue_records)
    clue_visibility = {
        'implicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'implicit'],
        'explicit': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'explicit'],
        'actionable': [c for c in clue_records_all if isinstance(c, dict) and c.get('presentation') == 'actionable'],
    }

    visibility_contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_facts_for_prompt = list(visibility_contract.get("visible_fact_strings") or [])
    opening_inputs_are_curated = False
    opening_fact_telemetry: Dict[str, Any] = {
        "opening_fact_source_used": "none",
        "opening_fact_eligibility_mode": "none",
        "opening_fact_rejected_by_lifecycle_count": 0,
        "opening_fact_rejected_by_form_count": 0,
        "opening_journal_filtered_count": 0,
    }
    opening_selector_selected_facts: List[str] = []
    if narration_obligations.get("is_opening_scene") and isinstance(public_scene, Mapping):
        curated_opening, opening_fact_telemetry = select_opening_narration_visible_facts_with_telemetry(
            public_scene,
            eligibility_metadata={
                "character": character if isinstance(character, dict) else {},
                "session_player_context": session.get("player_context") if isinstance(session, dict) else {},
            },
        )
        opening_selector_selected_facts = curated_opening[:OPENING_NARRATION_VISIBLE_FACT_MAX]
        visible_facts_for_prompt = list(opening_selector_selected_facts)
        opening_inputs_are_curated = True
    res_for_vis = resolution_sem if isinstance(resolution_sem, dict) else {}
    res_md_vis = res_for_vis.get("metadata") if isinstance(res_for_vis.get("metadata"), dict) else {}
    # Human-adjacent lane (bounded): reorders already-eligible visible_fact_strings using engine metadata
    # (intent_family, implicit_focus_resolution) plus player_text only inside the dedicated helper —
    # visibility_contract facts remain the bounded substrate; this is not CTIR semantic reconstruction.
    if res_md_vis.get("human_adjacent_intent_family") in {"listen", "approach_listen", "observe_group"}:
        from game.human_adjacent_focus import prioritize_visible_facts_for_human_adjacent

        opening_fact_telemetry["human_adjacent_bounded_visibility_reorder"] = True
        visible_facts_for_prompt = prioritize_visible_facts_for_human_adjacent(
            visible_facts_for_prompt,
            player_text=str(user_text or ""),
            implicit_focus_resolution=str(res_md_vis.get("implicit_focus_resolution") or ""),
            human_adjacent_intent_family=str(res_md_vis.get("human_adjacent_intent_family") or ""),
        )
    opening_scene_export: Dict[str, Any] = opening_realization_none()
    if narration_obligations.get("is_opening_scene") and isinstance(public_scene, Mapping):
        assert opening_inputs_are_curated is True
        opening_scene_export = build_opening_scene_realization(
            public_scene=public_scene,
            curated_visible_fact_strings=visible_facts_for_prompt,
            visibility_contract=visibility_contract,
        )
        _opening_contract = opening_scene_export.get("contract") if isinstance(opening_scene_export, dict) else None
        if isinstance(_opening_contract, dict):
            _opening_contract.update(opening_fact_telemetry)
        _opening_basis = (opening_scene_export.get("contract") or {}).get("narration_basis_visible_facts")
        if isinstance(_opening_basis, list):
            visible_facts_for_prompt = list(_opening_basis)
    if narration_obligations.get("is_opening_scene") and not visible_facts_for_prompt:
        _vf_fallback = list(visibility_contract.get("visible_fact_strings") or [])
        if _vf_fallback:
            visible_facts_for_prompt = _vf_fallback
    _seen_visible_fact: Set[str] = set()
    visible_facts_export: List[str] = []
    for _vf in visible_facts_for_prompt:
        if not isinstance(_vf, str):
            continue
        _n = _normalize_visibility_text(_vf)
        if not _n or _n in _seen_visible_fact:
            continue
        _seen_visible_fact.add(_n)
        visible_facts_export.append(_n)
    narration_visibility: Dict[str, Any] = {
        "visible_entities": list(visibility_contract.get("visible_entity_names") or []),
        "active_interlocutor_id": visibility_contract.get("active_interlocutor_id"),
        "visible_facts": visible_facts_export,
        "rules": {
            "no_unseen_entities": True,
            "no_hidden_facts": True,
            "no_undiscovered_facts": True,
        },
    }
    scene_state_anchor_contract = build_scene_state_anchor_contract(
        session if isinstance(session, dict) else None,
        scene if isinstance(scene, dict) else None,
        world if isinstance(world, dict) else None,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
    )
    return {
        "ctir_obj": ctir_obj,
        "prompt_sem": prompt_sem,
        "resolution_sem": resolution_sem,
        "intent_sem": intent_sem,
        "interaction_sem": interaction_sem,
        "intent_for_scene_payload": intent_for_scene_payload,
        "wp_projection": wp_projection,
        "wp_hint_lines": wp_hint_lines,
        "active_pending_leads": active_pending_leads,
        "runtime": runtime,
        "session_view": session_view,
        "narration_obligations": narration_obligations,
        "social_authority": social_authority,
        "eff_uncertainty_hint": eff_uncertainty_hint,
        "recent_log_compact": recent_log_compact,
        "response_policy": response_policy,
        "res": res,
        "state_changes": state_changes,
        "scene_advancement": scene_advancement,
        "has_scene_change_context": has_scene_change_context,
        "interaction_continuity": interaction_continuity,
        "has_active_interlocutor": has_active_interlocutor,
        "scene_pub_id": scene_pub_id,
        "interlocutor_export": interlocutor_export,
        "answer_style_hints_list": answer_style_hints_list,
        "clue_records_all": clue_records_all,
        "clue_visibility": clue_visibility,
        "visibility_contract": visibility_contract,
        "visible_facts_for_prompt": visible_facts_for_prompt,
        "opening_inputs_are_curated": opening_inputs_are_curated,
        "opening_fact_telemetry": opening_fact_telemetry,
        "opening_selector_selected_facts": opening_selector_selected_facts,
        "res_for_vis": res_for_vis,
        "res_md_vis": res_md_vis,
        "opening_scene_export": opening_scene_export,
        "visible_facts_export": visible_facts_export,
        "narration_visibility": narration_visibility,
        "scene_state_anchor_contract": scene_state_anchor_contract,
        "public_scene": public_scene,
    }


# Keys returned by :func:`build_planner_head_state` (stable contract for tests).
EXPECTED_PLANNER_HEAD_STATE_KEYS: frozenset[str] = frozenset(
    {
        "ctir_obj",
        "prompt_sem",
        "resolution_sem",
        "intent_sem",
        "interaction_sem",
        "intent_for_scene_payload",
        "wp_projection",
        "wp_hint_lines",
        "active_pending_leads",
        "runtime",
        "session_view",
        "narration_obligations",
        "social_authority",
        "eff_uncertainty_hint",
        "recent_log_compact",
        "response_policy",
        "res",
        "state_changes",
        "scene_advancement",
        "has_scene_change_context",
        "interaction_continuity",
        "has_active_interlocutor",
        "scene_pub_id",
        "interlocutor_export",
        "answer_style_hints_list",
        "clue_records_all",
        "clue_visibility",
        "visibility_contract",
        "visible_facts_for_prompt",
        "opening_inputs_are_curated",
        "opening_fact_telemetry",
        "opening_selector_selected_facts",
        "res_for_vis",
        "res_md_vis",
        "opening_scene_export",
        "visible_facts_export",
        "narration_visibility",
        "scene_state_anchor_contract",
        "public_scene",
    }
)
