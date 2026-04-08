from __future__ import annotations

from game.storage import (
    append_debug_trace,
    save_session,
    apply_repeated_description_guard,
    update_scene_momentum_runtime,
    list_scene_ids,
    load_scene,
)
from game.output_sanitizer import (
    extract_player_text_from_serialized_payload,
    resembles_serialized_response_payload,
    sanitize_player_facing_output,
    strip_serialized_payload_fragments,
)
from game.final_emission_gate import apply_final_emission_gate
from game.narration_state_consistency import reconcile_final_text_with_structured_state
from game.social_exchange_emission import strict_social_emission_will_apply
from game.interaction_context import inspect as inspect_interaction_context
from game.prompt_context import derive_narration_obligations
from game.response_type_gating import compact_response_type_contract
from game.social import SOCIAL_KINDS
from game.clues import get_known_clues_with_presentation
from game.affordances import get_available_affordances
from game.scene_graph import build_scene_graph
from game import leads as leads_module


AUTHORITATIVE_TURN_STAGE_ORDER: tuple[str, ...] = (
    'player_input',
    'intent_normalization_expansion',
    'action_classification',
    'engine_resolution',
    'authoritative_state_mutation',
    'prompt_context_construction',
    'gpt_narration',
    'affordance_derivation',
    'response_debug_packaging',
)


def _merge_emergent_actor_debug_into_action_debug(session: dict) -> None:
    lad = session.get("last_action_debug")
    if not isinstance(lad, dict):
        return
    em = session.get("emergent_actor_debug") if isinstance(session.get("emergent_actor_debug"), dict) else {}
    lad["emergent_actor_enrolled"] = bool(em.get("emergent_actor_enrolled"))
    lad["emergent_actor_id"] = em.get("emergent_actor_id")
    lad["emergent_actor_source_text"] = em.get("emergent_actor_source_text")


def _build_action_debug(
    last_action_type: str,
    player_input: str,
    normalized_action: dict | None,
    resolution: dict | None,
    response_type_contract: dict | None = None,
) -> dict:
    """Build sanitized debug payload for action pipeline. No hidden facts or secrets."""
    debug: dict = {
        'last_action_type': last_action_type,
        'player_input': player_input or '',
        'normalized_action': None,
        'resolution_kind': None,
        'target_scene': None,
        'resolver_result': None,
        'scene_transition': None,
    }
    if normalized_action and isinstance(normalized_action, dict):
        safe_norm = {k: v for k, v in normalized_action.items() if k in ('id', 'label', 'type', 'prompt', 'targetSceneId', 'target_scene_id')}
        debug['normalized_action'] = safe_norm
    if resolution and isinstance(resolution, dict):
        debug['resolution_kind'] = resolution.get('kind')
        if resolution.get('resolved_transition') and resolution.get('target_scene_id'):
            debug['target_scene'] = resolution.get('target_scene_id')
            debug['scene_transition'] = {
                'from': resolution.get('originating_scene_id') or '(previous)',
                'to': resolution.get('target_scene_id'),
            }
        safe_keys = {'kind', 'resolved_transition', 'target_scene_id', 'originating_scene_id',
                     'same_scene_transition_suppressed', 'transition_applied',
                     'action_id', 'label', 'prompt', 'hint', 'attack_id', 'skill_id', 'spell_id',
                     'roll', 'damage', 'total', 'hit', 'round', 'active_actor_id', 'world_tick_events',
                     'clue_id', 'clue_text', 'discovered_clues', 'state_changes', 'success', 'skill_check',
                     'requires_check', 'check_request',
                     'combat', 'social', 'adjudication'}
        debug['resolver_result'] = {k: v for k, v in resolution.items() if k in safe_keys}
        nsc = None
        md = resolution.get('metadata')
        if isinstance(md, dict):
            nsc = md.get('narration_state_consistency')
            if isinstance(nsc, dict):
                debug['narration_state_mismatch_detected'] = bool(nsc.get('narration_state_mismatch_detected'))
                debug['mismatch_kind'] = nsc.get('mismatch_kind') or ''
                debug['mismatch_repair_applied'] = nsc.get('mismatch_repair_applied') or 'none'
                mra = nsc.get('mismatch_repairs_applied')
                debug['mismatch_repairs_applied'] = list(mra) if isinstance(mra, list) else []
            mal = md.get('minimum_actionable_lead')
            if isinstance(mal, dict):
                debug['minimum_actionable_lead_enforced'] = bool(mal.get('minimum_actionable_lead_enforced'))
                debug['enforced_lead_id'] = mal.get('enforced_lead_id')
                debug['enforced_lead_source'] = mal.get('enforced_lead_source')
    compact_contract = compact_response_type_contract(response_type_contract)
    if compact_contract:
        debug["response_type_contract"] = compact_contract
    return debug


def _strip_internal_gm_keys(gm: dict) -> dict:
    out = dict(gm)
    out.pop("_player_facing_emission_finalized", None)
    return out


def _player_facing_text_for_lead_extraction(gm: dict | None) -> str:
    """Raw GM player-facing string before emission gate, for deterministic lead extraction."""
    if not isinstance(gm, dict):
        return ""
    raw_text = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    if resembles_serialized_response_payload(raw_text):
        extracted = extract_player_text_from_serialized_payload(raw_text)
        raw_text = (
            extracted
            if isinstance(extracted, str) and extracted.strip()
            else strip_serialized_payload_fragments(raw_text)
        )
    return raw_text


def _session_ongoing_social_exchange(session: dict | None) -> bool:
    """True when an authoritative social interlocutor is locked (interaction_mode + target)."""
    if not isinstance(session, dict):
        return False
    ctx = inspect_interaction_context(session)
    return (
        str(ctx.get("interaction_mode") or "").strip().lower() == "social"
        and bool(str(ctx.get("active_interaction_target_id") or "").strip())
    )


def _finalize_player_facing_for_turn(
    gm: dict | None,
    *,
    resolution: dict | None,
    session: dict,
    world: dict,
    scene: dict,
    include_resolution_in_sanitizer: bool = True,
) -> tuple[dict | None, dict]:
    """Apply repeated-description guard and scene momentum, then sanitize, emission gate, and mismatch repair.

    Guard/momentum run here (before sanitization) so they match the pre-emission pipeline order; when
    ``_player_facing_emission_finalized`` is set, ``_apply_post_gm_updates`` skips repeating them.

    Must run before ``_apply_post_gm_updates`` so narration supplements use the same text the client receives.

    Returns:
        ``(gm_out, narration_consistency_meta)`` — meta is always a dict (possibly empty flags).
    """
    if not isinstance(gm, dict):
        return gm, {
            "narration_state_mismatch_detected": False,
            "mismatch_kind": "",
            "mismatch_repair_applied": "none",
            "mismatch_repairs_applied": [],
            "repaired_discovered_clue_texts": [],
        }
    gm_out = dict(gm)
    scene_id = str((scene.get("scene") or {}).get("id") or "").strip()
    if scene_id:
        apply_repeated_description_guard(gm_out, session, scene_id)
        if not _session_ongoing_social_exchange(session):
            update_scene_momentum_runtime(session, scene_id, gm_out)
    raw_text = gm_out.get("player_facing_text") if isinstance(gm_out.get("player_facing_text"), str) else ""
    if resembles_serialized_response_payload(raw_text):
        extracted = extract_player_text_from_serialized_payload(raw_text)
        raw_text = (
            extracted
            if isinstance(extracted, str) and extracted.strip()
            else strip_serialized_payload_fragments(raw_text)
        )
    tag_list = gm_out.get("tags") if isinstance(gm_out.get("tags"), list) else []
    tag_list = [str(t) for t in tag_list if isinstance(t, str)]
    strict_social_turn = strict_social_emission_will_apply(
        resolution if isinstance(resolution, dict) else None,
        session,
        world,
        scene_id,
    )
    san_ctx_base = {
        "resolution": resolution if isinstance(resolution, dict) else None,
        "include_resolution": bool(include_resolution_in_sanitizer),
        "session": session,
        "scene_id": scene_id,
        "world": world,
        "tags": tag_list,
    }
    if strict_social_turn:
        gm_out["player_facing_text"] = raw_text
        gm_out = apply_final_emission_gate(
            gm_out,
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session,
            scene_id=scene_id,
            scene=scene,
            world=world,
        )
    else:
        gm_out["player_facing_text"] = sanitize_player_facing_output(raw_text, san_ctx_base)
        gm_out = apply_final_emission_gate(
            gm_out,
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session,
            scene_id=scene_id,
            scene=scene,
            world=world,
        )

    narr_meta = reconcile_final_text_with_structured_state(
        session=session,
        scene=scene,
        world=world,
        resolution=resolution if isinstance(resolution, dict) else None,
        gm_output=gm_out,
    )
    gm_out["_player_facing_emission_finalized"] = True
    return gm_out, narr_meta


def _trace_world_updates(updates: dict | None, clocks_changed: dict | None = None) -> list:
    """Summarize world/clock changes for debug trace."""
    out: list = []
    if clocks_changed and isinstance(clocks_changed, dict):
        for k, v in clocks_changed.items():
            out.append(f'clock:{k}={v}')
    if updates and isinstance(updates, dict):
        if updates.get('append_events'):
            out.append(f'append_events:{len(updates["append_events"])}')
        ws = updates.get('world_state') or {}
        for key in ('flags', 'counters', 'clocks'):
            if isinstance(ws.get(key), dict) and ws[key]:
                out.append(f'world_state.{key}:{",".join(str(x) for x in ws[key].keys())}')
        if updates.get('projects'):
            out.append(f'projects:{len(updates["projects"])}')
    return out


def _trace_resolution_path(
    action_type: str,
    resolution: dict | None,
) -> str:
    """Classify which deterministic resolver path produced this turn outcome."""
    if not isinstance(resolution, dict):
        return "none"
    if isinstance(resolution.get("social"), dict):
        return "social_engine"
    if isinstance(resolution.get("combat"), dict):
        return "combat_engine"
    if isinstance(resolution.get("adjudication"), dict):
        return "adjudication_engine"
    if resolution.get("requires_check"):
        return "check_prompt_engine"
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind in {"initiative", "attack", "spell", "skill_check", "enemy_attack", "enemy_turn_skipped", "end_turn"}:
        return "combat_engine"
    if kind:
        return "exploration_engine"
    return f"{action_type}_engine"


def _snapshot_known_clue_presentations(session: dict) -> dict[str, str]:
    """Capture clue presentation by id for before/after visibility comparisons."""
    snapshot: dict[str, str] = {}
    for clue in get_known_clues_with_presentation(session):
        if not isinstance(clue, dict):
            continue
        clue_id = str(clue.get("id") or "").strip()
        presentation = str(clue.get("presentation") or "").strip()
        if clue_id and presentation:
            snapshot[clue_id] = presentation
    return snapshot


def _diff_clue_presentation(
    before: dict[str, str] | None,
    after: dict[str, str] | None,
) -> list[dict]:
    """Return compact clue visibility/presentation changes."""
    before = before or {}
    after = after or {}
    changes: list[dict] = []
    for clue_id in sorted(set(before.keys()) | set(after.keys())):
        prev = before.get(clue_id)
        curr = after.get(clue_id)
        if prev == curr:
            continue
        changes.append({"id": clue_id, "from": prev, "to": curr})
    return changes


def _compact_affordances_for_trace(affordances: list | None) -> list[dict]:
    """Keep affordances trace developer-facing and compact."""
    out: list[dict] = []
    if not isinstance(affordances, list):
        return out
    for a in affordances:
        if not isinstance(a, dict):
            continue
        compact = {
            "id": a.get("id"),
            "type": a.get("type"),
            "label": a.get("label"),
            "targetSceneId": a.get("targetSceneId"),
            "targetEntityId": a.get("targetEntityId") or a.get("target_id"),
        }
        out.append({k: v for k, v in compact.items() if v is not None})
    return out


def _derive_affordances_from_authoritative_state(scene: dict, session: dict, world: dict) -> list[dict]:
    """Derive affordances from current authoritative state (no narration dependency)."""
    affordances = get_available_affordances(
        scene,
        session,
        world,
        mode=scene["scene"].get("mode", "exploration"),
        list_scene_ids_fn=list_scene_ids,
        scene_graph=build_scene_graph(list_scene_ids, load_scene),
    )
    return _compact_affordances_for_trace(affordances)


def _build_compact_turn_trace(
    *,
    source: str,
    action_type: str,
    raw_input: str,
    parsed_intent: dict | None,
    segmented_turn: dict | None,
    normalized_action: dict | None,
    implied_context: dict | None,
    resolution: dict | None,
    scene_before: str,
    scene_after: str,
    authoritative_clue_updates: list[str],
    clue_presentation_before: dict[str, str],
    session: dict,
    world: dict,
    scene: dict,
    leads_inspection: dict | None = None,
    response_type_contract: dict | None = None,
) -> dict:
    """Build compact resolved-turn trace grounded in post-resolution authoritative state."""
    interaction_after = inspect_interaction_context(session).copy()
    visited = session.get("visited_scene_ids") if isinstance(session.get("visited_scene_ids"), list) else []
    trace_session_view = {
        "turn_counter": int(session.get("turn_counter", 0) or 0),
        "visited_scene_count": len(visited),
        "active_interaction_target_id": interaction_after.get("active_interaction_target_id"),
        "active_interaction_kind": interaction_after.get("active_interaction_kind"),
        "interaction_mode": interaction_after.get("interaction_mode"),
    }
    trace_intent_labels: list[str] = []
    if isinstance(parsed_intent, dict):
        parsed_type = str(parsed_intent.get("type") or "").strip().lower()
        if parsed_type in SOCIAL_KINDS:
            trace_intent_labels.append("social_probe")
    narration_obligations = derive_narration_obligations(
        session_view=trace_session_view,
        resolution=resolution if isinstance(resolution, dict) else None,
        intent={"labels": trace_intent_labels} if trace_intent_labels else None,
        recent_log_for_prompt=[],
    )
    clue_presentation_after = _snapshot_known_clue_presentations(session)
    clue_changes = _diff_clue_presentation(clue_presentation_before, clue_presentation_after)
    known_clues = get_known_clues_with_presentation(session)
    clue_counts = {
        "implicit": sum(1 for c in known_clues if isinstance(c, dict) and c.get("presentation") == "implicit"),
        "explicit": sum(1 for c in known_clues if isinstance(c, dict) and c.get("presentation") == "explicit"),
        "actionable": sum(1 for c in known_clues if isinstance(c, dict) and c.get("presentation") == "actionable"),
    }
    deduped_clues: list[str] = []
    for txt in authoritative_clue_updates:
        if isinstance(txt, str):
            clean = txt.strip()
            if clean and clean not in deduped_clues:
                deduped_clues.append(clean)

    return {
        "source": source,
        "player_input": raw_input,
        "intent": {
            "parsed": parsed_intent if isinstance(parsed_intent, dict) else None,
            "segmented_turn": segmented_turn if isinstance(segmented_turn, dict) else None,
            "normalized": (
                {k: normalized_action.get(k) for k in ("id", "label", "type", "prompt", "targetSceneId", "target_scene_id", "targetEntityId", "target_id")}
                if isinstance(normalized_action, dict)
                else None
            ),
            "implied_context": {
                "applied": bool((implied_context or {}).get("applied")),
                "cases": list((implied_context or {}).get("cases") or []),
                "target_id": (implied_context or {}).get("target_id"),
                "commitment_broken": bool((implied_context or {}).get("commitment_broken")),
                "break_reason": (implied_context or {}).get("break_reason"),
            },
        },
        "classification": {
            "action_type": action_type,
            "resolved_kind": (resolution or {}).get("kind") if isinstance(resolution, dict) else None,
            "requires_check": bool((resolution or {}).get("requires_check")) if isinstance(resolution, dict) else False,
        },
        "response_type_contract": compact_response_type_contract(response_type_contract),
        "resolution_path": _trace_resolution_path(action_type, resolution),
        "authoritative_state_changes": {
            "scene_transition": {"from": scene_before, "to": scene_after} if scene_before != scene_after else None,
            "resolution_state_changes": (resolution or {}).get("state_changes") if isinstance((resolution or {}).get("state_changes"), dict) else {},
            "resolution_world_updates": _trace_world_updates((resolution or {}).get("world_updates")) if isinstance(resolution, dict) else [],
            "check_request": (resolution or {}).get("check_request") if isinstance((resolution or {}).get("check_request"), dict) else None,
        },
        "interaction_after": {
            "active_interaction_target_id": interaction_after.get("active_interaction_target_id"),
            "active_interaction_kind": interaction_after.get("active_interaction_kind"),
            "interaction_mode": interaction_after.get("interaction_mode"),
            "engagement_level": interaction_after.get("engagement_level"),
            "conversation_privacy": interaction_after.get("conversation_privacy"),
            "player_position_context": interaction_after.get("player_position_context"),
        },
        "narration_obligations": narration_obligations,
        "clues": {
            "discovered_texts": deduped_clues,
            "presentation_changes": clue_changes,
            "known_counts": clue_counts,
        },
        "affordances_after": _derive_affordances_from_authoritative_state(scene, session, world),
        "emergent_actor": (
            dict(session.get("emergent_actor_debug"))
            if isinstance(session, dict) and isinstance(session.get("emergent_actor_debug"), dict)
            else None
        ),
        "leads": (
            leads_inspection
            if isinstance(leads_inspection, dict)
            and isinstance(leads_inspection.get("registry_debug"), list)
            and isinstance(leads_inspection.get("delta_after_reconcile"), list)
            and isinstance(leads_inspection.get("changed_count"), int)
            else {
                "registry_debug": [],
                "delta_after_reconcile": [],
                "changed_count": 0,
            }
        ),
    }


def _reconcile_session_lead_progression_after_authoritative_mutation(session: dict) -> None:
    """Apply deterministic lead lifecycle progression for the current session turn.

    Call only after authoritative mutations for the request are complete (including post-narration
    session patches) and before compact turn-trace construction so traces match persisted state.
    """
    leads_module.reconcile_session_lead_progression(session)


def _lead_debug_trace_around_authoritative_reconcile(session: dict) -> dict:
    """Capture compact lead rows before/after the single authoritative reconcile pass."""
    before = leads_module.build_lead_debug_snapshot(session)
    _reconcile_session_lead_progression_after_authoritative_mutation(session)
    after = leads_module.build_lead_debug_snapshot(session)
    delta = leads_module.diff_lead_debug_snapshots(before, after)
    return {
        "registry_debug": leads_module.debug_dump_leads(session),
        "delta_after_reconcile": delta,
        "changed_count": len(delta),
    }


def _finalize_and_append_trace(session: dict, trace: dict, response_ok: bool, error: str | None = None) -> None:
    trace['response_ok'] = response_ok
    trace['error'] = error
    append_debug_trace(session, trace)
    save_session(session)


def _build_turn_response_payload(
    *,
    gm: dict,
    resolution: dict | None,
    include_resolution: bool,
) -> dict:
    """Stages 8-9: derive affordances from authoritative state and package API response."""
    import game.api as _api

    state = _api.compose_state()  # Includes affordances derived from saved authoritative scene/session/world.
    state_session = state.get("session") if isinstance(state.get("session"), dict) else {}
    state_world = state.get("world") if isinstance(state.get("world"), dict) else {}
    state_scene = state.get("scene") if isinstance(state.get("scene"), dict) else {}
    scene_obj = state_scene.get("scene") if isinstance(state_scene.get("scene"), dict) else {}
    scene_id = str(scene_obj.get("id") or "").strip()

    if isinstance(gm, dict):
        gm = dict(gm)
        if gm.get("_player_facing_emission_finalized"):
            gm = _strip_internal_gm_keys(gm)
        else:
            raw_text = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
            if resembles_serialized_response_payload(raw_text):
                extracted = extract_player_text_from_serialized_payload(raw_text)
                raw_text = (
                    extracted
                    if isinstance(extracted, str) and extracted.strip()
                    else strip_serialized_payload_fragments(raw_text)
                )
            tag_list = gm.get("tags") if isinstance(gm.get("tags"), list) else []
            tag_list = [str(t) for t in tag_list if isinstance(t, str)]
            strict_social_turn = strict_social_emission_will_apply(
                resolution if isinstance(resolution, dict) else None,
                state_session,
                state_world,
                scene_id,
            )

            san_ctx_base = {
                "resolution": resolution if isinstance(resolution, dict) else None,
                "include_resolution": bool(include_resolution),
                "session": state_session,
                "scene_id": scene_id,
                "world": state_world,
                "tags": tag_list,
            }

            if strict_social_turn:
                gm["player_facing_text"] = raw_text
                gm = apply_final_emission_gate(
                    gm,
                    resolution=resolution if isinstance(resolution, dict) else None,
                    session=state_session,
                    scene_id=scene_id,
                    scene=state_scene,
                    world=state_world,
                )
                # build_final_strict_social_response (via the gate) is the sole writer; no post-gate sanitizer.
            else:
                gm["player_facing_text"] = sanitize_player_facing_output(raw_text, san_ctx_base)
                gm = apply_final_emission_gate(
                    gm,
                    resolution=resolution if isinstance(resolution, dict) else None,
                    session=state_session,
                    scene_id=scene_id,
                    scene=state_scene,
                    world=state_world,
                )

    payload: dict = {'ok': True, 'gm_output': gm, **state}
    if include_resolution:
        payload['resolution'] = resolution
    return payload


def _sanitize_resolution(res: dict | None) -> dict | None:
    """Safe resolution subset for trace. No hidden content."""
    if not res or not isinstance(res, dict):
        return None
    safe = {'kind', 'resolved_transition', 'target_scene_id', 'originating_scene_id',
            'same_scene_transition_suppressed', 'transition_applied',
            'action_id', 'label', 'prompt', 'hint', 'attack_id', 'skill_id', 'spell_id',
            'roll', 'damage', 'total', 'hit', 'round', 'active_actor_id', 'world_tick_events',
            'clue_id', 'clue_text', 'discovered_clues', 'state_changes', 'success', 'metadata',
            'combat', 'social', 'adjudication', 'requires_check', 'check_request'}
    return {k: v for k, v in res.items() if k in safe}


def _compact_segmented_turn(segmented_turn: dict | None) -> dict | None:
    """Keep segmentation payload compact for traces/metadata."""
    if not isinstance(segmented_turn, dict):
        return None
    compact = {
        "spoken_text": segmented_turn.get("spoken_text"),
        "declared_action_text": segmented_turn.get("declared_action_text"),
        "adjudication_question_text": segmented_turn.get("adjudication_question_text"),
        "observation_intent_text": segmented_turn.get("observation_intent_text"),
        "contingency_text": segmented_turn.get("contingency_text"),
    }
    compact = {k: v for k, v in compact.items() if isinstance(v, str) and v.strip()}
    return compact or None
