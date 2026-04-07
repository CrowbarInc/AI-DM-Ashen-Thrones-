from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
import json
import re
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from game.models import ActionRequest, ChatRequest, ResponseModeUpdate, SnapshotCreateRequest
from game.storage import (
    BASE_DIR,
    create_snapshot,
    ensure_data_files_exist,
    get_save_summary,
    list_snapshots,
    load_snapshot,
    load_campaign,
    save_campaign,
    load_character,
    save_character,
    load_session,
    save_session,
    load_world,
    save_world,
    load_combat,
    save_combat,
    load_conditions,
    load_active_scene,
    load_scene,
    save_scene,
    activate_scene,
    list_scene_ids,
    is_known_scene_id,
    load_log,
    append_log,
    clear_log,
    get_scene_runtime,
    mark_interactable_resolved,
    mark_target_searched,
    apply_repeated_description_guard,
    update_scene_momentum_runtime,
    append_debug_trace,
)
from game.combat import (
    player_can_act,
    roll_initiative,
    resolve_attack,
    resolve_skill,
    resolve_spell,
    advance_turn,
    prune_initiative,
    end_combat_if_done,
    enemy_take_turn,
    cleanup_player_turn,
    build_end_turn_result,
)
from game.gm import (
    build_messages,
    call_gpt,
    guard_gm_output,
    apply_response_policy_enforcement,
    MAX_TARGETED_RETRY_ATTEMPTS,
    detect_retry_failures,
    choose_retry_strategy,
    prioritize_retry_failures_for_social_answer_candidate,
    build_retry_prompt_for_failure,
    apply_deterministic_retry_fallback,
    force_terminal_retry_fallback,
    remember_recent_contextual_leads,
    register_topic_probe,
    _gm_has_usable_player_facing_text,
    _session_social_authority,
    ensure_minimal_nonsocial_resolution,
    ensure_minimal_social_resolution,
)
from game import leads as leads_module
from game.journal import build_player_journal
from game.affordances import get_available_affordances
from game.scene_actions import normalize_scene_action
from game.exploration import (
    apply_follow_lead_commitment_after_resolved_scene_transition,
    maybe_finalize_pursued_lead_destination_payoff_after_scene_transition,
    maybe_finalize_pursued_lead_npc_contact_payoff,
    parse_exploration_intent,
    process_investigation_discovery,
    resolve_exploration_action,
)
from game.adjudication import (
    classify_adjudication_query,
    neutralize_engine_voice_for_player,
    resolve_adjudication_query,
)
from game.social import (
    apply_social_lead_discussion_tracking,
    parse_social_intent,
    resolve_social_action,
    apply_social_topic_escalation_to_resolution,
    SOCIAL_KINDS,
    find_npc_by_target,
)
from game.interaction_context import (
    apply_conservative_emergent_enrollment_from_gm_output,
    apply_explicit_non_social_commitment_break,
    apply_turn_input_implied_context,
    assert_valid_speaker,
    build_intent_route_debug_adjudication_query,
    build_intent_route_debug_social_exchange,
    clear_emergent_scene_actors_on_scene_change,
    clear_for_scene_change,
    clear_turn_start_interlocutor_snapshot,
    establish_dialogue_interaction_from_input,
    find_addressed_npc_id_for_turn,
    find_world_npc_reference_id_in_text,
    inspect as inspect_interaction_context,
    merge_turn_segments_for_directed_social_entry,
    response_type_context_snapshot,
    resolve_declared_actor_switch,
    resolve_dialogue_lock_action_target_id,
    resolve_directed_social_entry,
    scene_npcs_in_active_scene,
    should_route_addressed_question_to_social,
    snapshot_turn_start_interlocutor,
    synchronize_scene_addressability,
    update_after_resolved_action,
)
from game.scene_graph import build_scene_graph, is_transition_valid
from game.intent_parser import (
    is_qualified_pursuit_shaped,
    maybe_build_declared_travel_action,
    maybe_build_passive_interruption_wait_action,
    parse_intent,
    segment_mixed_player_turn,
)
from game.prompt_context import build_response_policy
from game.response_type_gating import compact_response_type_contract, derive_response_type_contract
from game.social_exchange_emission import strict_social_emission_will_apply
from game.utils import slugify, utc_iso_now
from game.world import advance_world_tick, apply_world_updates, apply_resolution_world_updates
from game.clocks import get_or_init_clocks, advance_clock, DEFAULT_CLOCKS
from game.importers.pf_json_importer import import_sheet
from game.session import reset_session_state
from game.campaign_reset import apply_new_campaign_hard_reset
from game.campaign_state import create_fresh_combat_state
from game.clues import (
    apply_authoritative_clue_discovery,
    apply_social_narration_lead_supplements,
    apply_socially_revealed_leads,
    ensure_scene_has_minimum_actionable_lead,
    get_all_known_clue_texts,
    get_known_clues_with_presentation,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: startup (ensure data files) and optional shutdown."""
    ensure_data_files_exist()
    yield


app = FastAPI(title='Ashen Thrones AI GM', lifespan=lifespan)  # noqa: E302
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

STATIC_DIR = BASE_DIR / 'static'
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

@app.get('/')
def index():
    return FileResponse(STATIC_DIR / 'index.html')


def _sanitize_incoming_payload(req: ActionRequest | None) -> dict:
    """Sanitized incoming payload for debug trace. No secrets or hidden content."""
    if req is None:
        return {}
    d = req.model_dump()
    out: dict = {
        'action_type': d.get('action_type'),
        'intent': (d.get('intent') or '')[:200],
    }
    exp = d.get('exploration_action')
    if isinstance(exp, dict):
        out['exploration_action'] = {
            k: exp.get(k)
            for k in ('id', 'label', 'type', 'targetSceneId', 'targetEntityId', 'targetLocationId')
            if k in exp
        }
    return out


_COMBAT_IDLE = {'in_combat': False, 'round': 0, 'initiative_order': [], 'turn_index': 0, 'active_actor_id': None, 'player_turn_used': False}


def _reset_combat(combat: dict) -> None:
    """Reset combat to idle state after scene transition or reset."""
    combat.update(_COMBAT_IDLE)


def _apply_authoritative_scene_transition(
    target_scene_id: str,
    scene: dict,
    session: dict,
    combat: dict,
    world: dict,
) -> tuple[dict, dict, dict]:
    """Apply the single authoritative scene transition path.

    All runtime transition effects (activation, scene/combat reload, combat reset,
    and interaction-context clear) flow through this helper.
    """
    sid = (target_scene_id or "").strip()
    if not sid:
        return scene, session, combat
    activate_scene(sid)
    scene = load_scene(sid)
    session = load_session()
    combat = load_combat()
    _reset_combat(combat)
    clear_for_scene_change(session)
    clear_emergent_scene_actors_on_scene_change(session)
    synchronize_scene_addressability(session, scene, world)
    return scene, session, combat


def _resolution_explicitly_breaks_social_continuity(resolution: dict | None) -> bool:
    """Engine resolutions that should drop social continuity (movement/combat class)."""
    if not isinstance(resolution, dict):
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    if kind in ("scene_transition", "travel", "attack", "combat"):
        return True
    if resolution.get("disengage_social") is True:
        return True
    res_meta = resolution.get("metadata")
    if isinstance(res_meta, dict) and res_meta.get("passive_interruption_wait") is True:
        return True
    return False


def _update_interaction_context_after_action(
    session: dict,
    resolution: dict | None,
    *,
    scene_changed: bool,
    preserve_continuity: bool = False,
) -> None:
    """Maintain deterministic interaction context after each action/chat turn."""
    if scene_changed:
        clear_for_scene_change(session)
        clear_emergent_scene_actors_on_scene_change(session)
        return

    if not isinstance(resolution, dict):
        inspect_interaction_context(session)
        return

    breaks_social = _resolution_explicitly_breaks_social_continuity(resolution)
    # Movement-class resolutions must drop dialogue-lock preservation even when turn input
    # implied continuity (e.g. quoted farewell + declared travel); otherwise unresolved travel
    # would keep the prior interlocutor as active.
    effective_preserve = bool(
        (preserve_continuity and not breaks_social)
        or (
            _session_ongoing_social_exchange(session)
            and not breaks_social
        )
    )

    kind = str(resolution.get("kind") or "").strip().lower()
    if kind in SOCIAL_KINDS:
        update_after_resolved_action(session, kind, preserve_continuity=True)
        return

    update_after_resolved_action(session, kind, preserve_continuity=effective_preserve)
    # Keep context inspectable for debugging even after owner updates.
    inspect_interaction_context(session)


def _prepare_interaction_from_turn_input(
    session: dict,
    world: dict,
    scene_id: str,
    player_text: str | None,
    scene: dict | None = None,
    normalized_action: dict | None = None,
) -> dict:
    """Stage 2 normalization helper: deterministic implied continuity preparation."""
    # Commitment break uses turn-start social state + raw/normalized action; must run before
    # apply_turn_input_implied_context so same-turn courtesy (sit, lowered voice) is not mistaken
    # for an active interlocutor lock from the prior turn.
    commitment = apply_explicit_non_social_commitment_break(
        session,
        world,
        scene_id,
        player_text,
        normalized_action,
        scene_envelope=scene if isinstance(scene, dict) else None,
    )
    implied = apply_turn_input_implied_context(session, world, scene_id, player_text)
    merged = {**implied, **commitment}
    if scene is not None:
        est = establish_dialogue_interaction_from_input(session, world, scene, player_text)
        merged["interaction_established"] = bool(est.get("established"))
        merged["dialogue_target_id"] = est.get("target_id")
        return merged
    return merged


_PASSIVE_ACTION_CUES: tuple[tuple[str, str], ...] = (
    ("hold position", "hold_position"),
    ("remain silent", "remain_silent"),
    ("stay silent", "remain_silent"),
    ("say nothing", "remain_silent"),
    ("keep watching", "watch"),
    ("look around", "observe"),
    ("wait", "wait"),
    ("watch", "watch"),
    ("observe", "observe"),
)


def _detect_passive_action_markers(
    player_text: str | None,
    normalized_action: dict | None = None,
    resolution: dict | None = None,
) -> list[str]:
    """Detect passive/holding actions in a simple, inspectable way."""
    markers: list[str] = []
    low = str(player_text or "").strip().lower()
    normalized_type = str((normalized_action or {}).get("type") or "").strip().lower()
    resolution_kind = str((resolution or {}).get("kind") or "").strip().lower()
    if normalized_type == "observe" or resolution_kind == "observe":
        markers.append("observe")
    for needle, label in _PASSIVE_ACTION_CUES:
        if needle not in low:
            continue
        if label not in markers:
            markers.append(label)
    return markers


def _record_scene_pressure_input(
    session: dict,
    scene_id: str,
    player_text: str | None,
    *,
    normalized_action: dict | None = None,
    resolution: dict | None = None,
) -> dict:
    """Track recent passive actions so pressure escalation can stay deterministic."""
    sid = str(scene_id or "").strip()
    if not sid:
        return {}
    runtime = get_scene_runtime(session, sid)
    markers = _detect_passive_action_markers(
        player_text,
        normalized_action=normalized_action,
        resolution=resolution,
    )
    is_passive = bool(markers)
    previous_streak = int(runtime.get("passive_action_streak", 0) or 0)
    runtime["passive_action_streak"] = (previous_streak + 1) if is_passive else 0
    recent = runtime.get("recent_player_actions")
    if not isinstance(recent, list):
        recent = []
    recent.append(
        {
            "text": str(player_text or "").strip()[:160],
            "passive": is_passive,
            "markers": list(markers[:3]),
            "resolution_kind": str((resolution or {}).get("kind") or "").strip() or None,
            "turn": int(session.get("turn_counter", 0) or 0),
        }
    )
    runtime["recent_player_actions"] = recent[-4:]
    runtime["last_player_action_text"] = str(player_text or "").strip()[:200]
    runtime["last_player_action_passive"] = is_passive
    return runtime


def _apply_authoritative_clues_from_resolution(
    session: dict,
    scene_id: str,
    resolution: dict | None,
    world: dict,
) -> list[str]:
    """Apply deterministic clue resolution through a single clue gateway."""
    if not isinstance(resolution, dict):
        return []
    return apply_authoritative_clue_discovery(
        session,
        scene_id,
        clue_id=resolution.get('clue_id'),
        clue_text=resolution.get('clue_text'),
        discovered_clues=resolution.get('discovered_clues') if isinstance(resolution.get('discovered_clues'), list) else None,
        world=world,
    )


def _apply_post_gm_updates(
    gm: dict,
    scene: dict,
    session: dict,
    world: dict,
    combat: dict,
    resolution: dict | None = None,
) -> tuple[dict, dict, dict, list, list]:
    """Apply GM-proposed updates (scene_update, new_scene_draft, activate_scene_id, world_updates),
    repeated description guard, detect surfaced clues (telemetry only), and narration-based social leads.

    Returns (scene, session, combat, surfaced_in_text, narration_social_lead_clue_texts)."""
    if gm.get('scene_update'):
        su = gm['scene_update']
        scene['scene'].setdefault('visible_facts', [])
        scene['scene'].setdefault('discoverable_clues', [])
        scene['scene'].setdefault('hidden_facts', [])
        scene['scene']['visible_facts'].extend([x for x in su.get('visible_facts_add', []) if x not in scene['scene']['visible_facts']])
        scene['scene']['discoverable_clues'].extend([x for x in su.get('discoverable_clues_add', []) if x not in scene['scene']['discoverable_clues']])
        scene['scene']['hidden_facts'].extend([x for x in su.get('hidden_facts_add', []) if x not in scene['scene']['hidden_facts']])
        if su.get('mode'):
            scene['scene']['mode'] = su['mode']

    # Scene-transition ownership invariant:
    # GPT transition proposals remain advisory only; authoritative transitions are
    # applied solely by deterministic engine resolution paths.
    ignored_transition_proposals: list[str] = []
    if gm.get('new_scene_draft'):
        ignored_transition_proposals.append('new_scene_draft')
    if gm.get('activate_scene_id'):
        ignored_transition_proposals.append('activate_scene_id')
    if ignored_transition_proposals:
        dbg = gm.get('debug_notes') if isinstance(gm.get('debug_notes'), str) else ''
        reason = 'advisory_only:' + ','.join(ignored_transition_proposals)
        gm['debug_notes'] = (dbg + ' | ' if dbg else '') + reason

    if gm.get('world_updates'):
        updates = gm['world_updates']
        if updates.get('append_events'):
            updates['append_events'] = [{'type': 'gm_event', 'text': t} if isinstance(t, str) else t for t in updates['append_events']]
        apply_world_updates(world, updates)

    if not gm.get("_player_facing_emission_finalized"):
        apply_repeated_description_guard(gm, session, scene['scene']['id'])
        if not _session_ongoing_social_exchange(session):
            update_scene_momentum_runtime(session, scene['scene']['id'], gm)

    surfaced_in_text: list = []
    if isinstance(gm.get('player_facing_text'), str):
        from game.gm import detect_surfaced_clues  # local import to avoid cycles
        for clue_text in detect_surfaced_clues(gm['player_facing_text'], scene):
            surfaced_in_text.append(clue_text)

    narration_social_leads: list[str] = []
    ptext = gm.get('player_facing_text') if isinstance(gm.get('player_facing_text'), str) else ''
    if resolution and isinstance(resolution, dict) and isinstance(ptext, str) and ptext.strip():
        narration_social_leads.extend(
            apply_social_narration_lead_supplements(
                session,
                scene['scene']['id'],
                world,
                resolution,
                ptext.strip(),
                scene,
            )
        )

    if resolution and isinstance(resolution, dict):
        ensure_scene_has_minimum_actionable_lead(
            scene_id=scene['scene']['id'],
            session=session,
            scene=scene,
            resolution=resolution,
            gm_output=gm if isinstance(gm, dict) else None,
            world=world,
        )

    emergent_debug = {
        "emergent_actor_enrolled": False,
        "emergent_actor_id": None,
        "emergent_actor_source_text": None,
    }
    if isinstance(session, dict) and isinstance(scene, dict) and isinstance(scene.get("scene"), dict):
        narr = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
        emergent_debug = apply_conservative_emergent_enrollment_from_gm_output(
            session=session,
            scene=scene,
            narration_text=narr.strip() or None,
        )
    session["emergent_actor_debug"] = emergent_debug

    return (scene, session, combat, surfaced_in_text, narration_social_leads)


def _apply_authoritative_resolution_state_mutation(
    *,
    session: dict,
    world: dict,
    combat: dict,
    scene: dict,
    resolution: dict,
    normalized_action: dict | None,
) -> tuple[dict, dict, dict, list[str], dict]:
    """Stage 5: apply deterministic state mutation from resolved engine output."""
    authoritative_clue_updates: list[str] = []

    if resolution.get("world_updates"):
        apply_resolution_world_updates(world, resolution["world_updates"])
        save_world(world)

    originating_scene_id = str(scene['scene']['id'] or '').strip()
    if resolution.get('resolved_transition') and resolution.get('target_scene_id'):
        target_scene_id = str(resolution['target_scene_id'] or '').strip()
        resolution['originating_scene_id'] = originating_scene_id
        # Block 2: authoritative same-scene — no reload/re-entry; skip follow-lead hook.
        if originating_scene_id and target_scene_id and originating_scene_id == target_scene_id:
            resolution['same_scene_transition_suppressed'] = True
            resolution['transition_applied'] = False
            resolution['resolved_transition'] = False
            resolution['target_scene_id'] = None
            sc = resolution.get('state_changes')
            if isinstance(sc, dict):
                for k in (
                    'scene_changed',
                    'scene_transition_occurred',
                    'arrived_at_scene',
                    'new_scene_context_available',
                ):
                    sc.pop(k, None)
                resolution['state_changes'] = sc
        else:
            print("[ENGINE] Scene transition →", target_scene_id)
            scene, session, combat = _apply_authoritative_scene_transition(target_scene_id, scene, session, combat, world)
            apply_follow_lead_commitment_after_resolved_scene_transition(
                session,
                resolution,
                normalized_action,
                target_scene_id=target_scene_id,
            )
            maybe_finalize_pursued_lead_destination_payoff_after_scene_transition(
                session,
                resolution,
                normalized_action,
                target_scene_id=target_scene_id,
            )

    res_kind = str(resolution.get("kind") or "").strip().lower()
    if res_kind in SOCIAL_KINDS:
        # Canonical first landing for socially revealed clues/leads (clue_knowledge, runtime, pending_leads, event_log).
        authoritative_clue_updates.extend(
            apply_socially_revealed_leads(
                session, scene["scene"]["id"], world, resolution, scene=scene
            )
        )
        apply_social_lead_discussion_tracking(
            session=session,
            scene_id=scene["scene"]["id"],
            resolution=resolution,
            player_text=str(resolution.get("prompt") or ""),
        )
        maybe_finalize_pursued_lead_npc_contact_payoff(session, resolution, normalized_action)
    else:
        authoritative_clue_updates.extend(
            _apply_authoritative_clues_from_resolution(session, scene['scene']['id'], resolution, world)
        )

    scene_rt = get_scene_runtime(session, scene['scene']['id'])
    action_key = resolution.get('action_id') or ((normalized_action or {}).get('id') if isinstance(normalized_action, dict) else None)
    last_key = scene_rt.get('last_exploration_action_key')
    if action_key == last_key:
        scene_rt['repeated_action_count'] = (scene_rt.get('repeated_action_count') or 0) + 1
    else:
        scene_rt['repeated_action_count'] = 1
    scene_rt['last_exploration_action_key'] = action_key
    scene_rt['last_resolution_kind'] = resolution.get('kind')

    if resolution.get('kind') == 'investigate':
        # Skip clue discovery when a skill check was run and failed.
        if not (resolution.get('skill_check') and resolution.get('success') is False):
            newly_revealed = process_investigation_discovery(scene, session, list_scene_ids=list_scene_ids, world=world)
            for rec in newly_revealed:
                txt = rec.get('text') if isinstance(rec, dict) else None
                if isinstance(txt, str) and txt.strip() and txt.strip() not in authoritative_clue_updates:
                    authoritative_clue_updates.append(txt.strip())
        # Discovery memory: mark generic investigate target as searched.
        target_id = resolution.get('action_id') or (normalized_action.get('id') if normalized_action else None)
        if target_id:
            mark_target_searched(session, scene['scene']['id'], target_id)
        scene_rt = get_scene_runtime(session, scene['scene']['id'])
    elif resolution.get('kind') == 'discover_clue':
        # Discovery memory: mark interactable as resolved (one-time clue exhausted).
        inter_id = resolution.get('interactable_id')
        if isinstance(inter_id, str) and inter_id.strip():
            mark_interactable_resolved(session, scene['scene']['id'], inter_id.strip())
        # Also mark action_id so affordances keyed by it get relabeled.
        action_id = resolution.get('action_id') or (normalized_action.get('id') if normalized_action else None)
        if action_id:
            mark_target_searched(session, scene['scene']['id'], action_id)
        scene_rt = get_scene_runtime(session, scene['scene']['id'])

    return (scene, session, combat, authoritative_clue_updates, scene_rt)


def _attach_response_type_contract_to_resolution(
    resolution: dict | None,
    response_type_contract: dict | None,
) -> None:
    if not isinstance(resolution, dict) or not isinstance(response_type_contract, dict):
        return
    metadata = resolution.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        resolution["metadata"] = metadata
    metadata["response_type_contract"] = dict(response_type_contract)


def _derive_response_type_contract_for_turn(
    *,
    session: dict,
    segmented_turn: dict | None,
    normalized_action: dict | None,
    resolution: dict | None,
    raw_player_text: str | None,
    route_choice: str | None = None,
    directed_social_entry: dict | None = None,
    attach_to_resolution: bool = True,
) -> dict:
    contract = derive_response_type_contract(
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
        resolution=resolution if isinstance(resolution, dict) else None,
        interaction_context=response_type_context_snapshot(session),
        directed_social_entry=directed_social_entry if isinstance(directed_social_entry, dict) else None,
        route_choice=route_choice,
        raw_player_text=raw_player_text,
    ).to_dict()
    if attach_to_resolution:
        _attach_response_type_contract_to_resolution(resolution, contract)
    return contract


def _build_gpt_narration_from_authoritative_state(
    *,
    campaign: dict,
    world: dict,
    session: dict,
    character: dict,
    scene: dict,
    combat: dict,
    recent_log: list,
    user_text: str,
    resolution: dict,
    scene_runtime: dict,
    segmented_turn: dict | None = None,
    route_choice: str | None = None,
    directed_social_entry: dict | None = None,
    response_type_contract: dict | None = None,
) -> dict:
    """Stages 6-7: build prompt context from authoritative state, then narrate with GPT."""
    register_topic_probe(
        session=session,
        scene_envelope=scene,
        player_text=user_text,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    if isinstance(resolution, dict):
        apply_social_topic_escalation_to_resolution(
            world=world,
            session=session,
            scene=scene,
            user_text=user_text,
            resolution=resolution,
        )
    messages = build_messages(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        user_text,
        resolution,
        scene_runtime=scene_runtime,
    )
    prompt_payload: dict = {}
    if isinstance(messages, list) and len(messages) > 1:
        try:
            m1 = messages[1]
            if isinstance(m1, dict) and isinstance(m1.get("content"), str):
                prompt_payload = json.loads(m1["content"])
        except Exception:
            prompt_payload = {}
    response_policy = (
        prompt_payload.get("response_policy")
        if isinstance(prompt_payload, dict) and isinstance(prompt_payload.get("response_policy"), dict)
        else build_response_policy()
    )
    contract_payload = (
        dict(response_type_contract)
        if isinstance(response_type_contract, dict)
        else _derive_response_type_contract_for_turn(
            session=session,
            segmented_turn=segmented_turn,
            normalized_action=None,
            resolution=resolution if isinstance(resolution, dict) else None,
            raw_player_text=user_text,
            route_choice=route_choice,
            directed_social_entry=directed_social_entry,
        )
    )
    if isinstance(prompt_payload, dict) and contract_payload:
        prompt_payload["response_type_contract"] = dict(contract_payload)
        response_policy = dict(response_policy) if isinstance(response_policy, dict) else build_response_policy()
        compact_contract = compact_response_type_contract(contract_payload)
        if compact_contract:
            response_policy["response_type_contract"] = compact_contract
        prompt_payload["response_policy"] = response_policy
        if (
            isinstance(messages, list)
            and len(messages) > 1
            and isinstance(messages[1], dict)
        ):
            messages = list(messages)
            messages[1] = dict(messages[1])
            messages[1]["content"] = json.dumps(prompt_payload, ensure_ascii=True)

    def _failures_after_social_answer_priority(raw: list) -> list:
        prioritized, _dbg = prioritize_retry_failures_for_social_answer_candidate(
            raw,
            player_text=user_text,
            resolution=resolution,
            session=session,
            scene_envelope=scene,
        )
        return prioritized

    def _repair_terminal_player_facing_if_needed(gm_dict: dict, *, reason: str) -> dict:
        sid = str((scene.get("scene") or {}).get("id") or "").strip()
        social_lane = _session_social_authority(session) or strict_social_emission_will_apply(
            resolution, session, world, sid
        )
        if _gm_has_usable_player_facing_text(gm_dict):
            return gm_dict
        if social_lane:
            repaired = ensure_minimal_social_resolution(
                gm=gm_dict,
                session=session,
                reason=reason,
                world=world,
                resolution=resolution if isinstance(resolution, dict) else None,
                scene_envelope=scene,
            )
            print("[SOCIAL RESOLUTION REPAIR] terminal empty social output repaired")
            return repaired
        repaired_ns = ensure_minimal_nonsocial_resolution(gm=gm_dict, session=session)
        dbg = repaired_ns.get("debug_notes") if isinstance(repaired_ns.get("debug_notes"), str) else ""
        repaired_ns["debug_notes"] = (dbg + " | " if dbg else "") + f"nonsocial_repair_context:{reason}"
        print("[NON-SOCIAL RESOLUTION REPAIR] empty output repaired")
        return repaired_ns

    known_clues = list(get_all_known_clue_texts(session))
    gm = guard_gm_output(
        call_gpt(messages),
        scene,
        user_text,
        known_clues,
        session=session,
        world=world,
        resolution=resolution,
    )
    retry_attempt = 0
    while True:
        failures = _failures_after_social_answer_priority(
            detect_retry_failures(
                player_text=user_text,
                gm_reply=gm,
                scene_envelope=scene,
                session=session,
                world=world,
                resolution=resolution,
            )
        )
        selected_failure = choose_retry_strategy(failures)
        if not selected_failure:
            break
        if retry_attempt >= MAX_TARGETED_RETRY_ATTEMPTS:
            fc = str(selected_failure.get("failure_class") or "").strip()
            print(f"[RETRY ESCAPE HATCH] class={fc} attempts={retry_attempt}")
            gm = force_terminal_retry_fallback(
                session=session,
                original_text=str(gm.get("player_facing_text") or ""),
                failure=selected_failure,
                retry_failures=failures,
                player_text=user_text,
                scene_envelope=scene,
                world=world,
                resolution=resolution,
                base_gm=gm,
            )
            gm = _repair_terminal_player_facing_if_needed(
                gm, reason="api_post_force_terminal_retry_fallback"
            )
            break
        retry_attempt += 1
        retry_instruction = build_retry_prompt_for_failure(
            selected_failure,
            response_policy=response_policy,
        )
        print(
            "[RETRY] selected_strategy=",
            selected_failure.get("failure_class"),
            "attempt=",
            retry_attempt,
            "reasons=",
            selected_failure.get("reasons"),
        )
        retry_messages = (
            list(messages) if isinstance(messages, list) else []
        ) + [{'role': 'user', 'content': retry_instruction}]
        gm_retry = guard_gm_output(
            call_gpt(retry_messages),
            scene,
            user_text,
            known_clues,
            session=session,
            world=world,
            resolution=resolution,
        )
        retry_dbg = gm_retry.get('debug_notes') if isinstance(gm_retry.get('debug_notes'), str) else ''
        reason_suffix = ','.join(str(r) for r in (selected_failure.get("reasons") or []) if isinstance(r, str)) or 'unknown'
        gm_retry['debug_notes'] = (
            (retry_dbg + ' | ' if retry_dbg else '')
            + f"retry_strategy:selected={selected_failure.get('failure_class')}:attempt={retry_attempt}:reasons={reason_suffix}"
        )
        retry_failures = _failures_after_social_answer_priority(
            detect_retry_failures(
                player_text=user_text,
                gm_reply=gm_retry,
                scene_envelope=scene,
                session=session,
                world=world,
                resolution=resolution,
            )
        )
        selected_class = str(selected_failure.get("failure_class") or "").strip()
        still_failing = next(
            (
                failure for failure in retry_failures
                if isinstance(failure, dict) and str(failure.get("failure_class") or "").strip() == selected_class
            ),
            None,
        )
        still_unresolved_after_answer_retry = next(
            (
                failure
                for failure in retry_failures
                if isinstance(failure, dict)
                and str(failure.get("failure_class") or "").strip() == "unresolved_question"
            ),
            None,
        )
        use_question_retry_fallback = (selected_class == "unresolved_question" and still_failing) or (
            selected_class == "answer" and still_unresolved_after_answer_retry
        )
        if use_question_retry_fallback:
            _vf = still_failing if isinstance(still_failing, dict) else still_unresolved_after_answer_retry
            print(
                "[RETRY] validation_failed selected_strategy=",
                selected_class,
                "attempt=",
                retry_attempt,
                "reasons=",
                (_vf.get("reasons") if isinstance(_vf, dict) else None),
                "action=deterministic_fallback",
            )
            fallback_failure = (
                still_failing if selected_class == "unresolved_question" else selected_failure
            )
            gm_retry = apply_deterministic_retry_fallback(
                gm_retry,
                failure=fallback_failure,
                player_text=user_text,
                scene_envelope=scene,
                session=session,
                world=world,
                resolution=resolution,
            )
            fallback_failures = _failures_after_social_answer_priority(
                detect_retry_failures(
                    player_text=user_text,
                    gm_reply=gm_retry,
                    scene_envelope=scene,
                    session=session,
                    world=world,
                    resolution=resolution,
                )
            )
            fallback_still_failing = any(
                isinstance(failure, dict) and str(failure.get("failure_class") or "").strip() == selected_class
                for failure in fallback_failures
            )
            print(
                "[RETRY] fallback_result selected_strategy=",
                selected_class,
                "attempt=",
                retry_attempt,
                "status=",
                "failed" if fallback_still_failing else "passed",
            )
            if fallback_still_failing:
                print(f"[RETRY ESCAPE HATCH] class={selected_class} attempts={retry_attempt}")
                fail_meta = next(
                    (
                        f
                        for f in fallback_failures
                        if isinstance(f, dict) and str(f.get("failure_class") or "").strip() == selected_class
                    ),
                    selected_failure,
                )
                gm = force_terminal_retry_fallback(
                    session=session,
                    original_text=str(gm_retry.get("player_facing_text") or ""),
                    failure=fail_meta if isinstance(fail_meta, dict) else selected_failure,
                    retry_failures=fallback_failures,
                    player_text=user_text,
                    scene_envelope=scene,
                    world=world,
                    resolution=resolution,
                    base_gm=gm_retry,
                )
                gm = _repair_terminal_player_facing_if_needed(
                    gm, reason="api_post_force_terminal_retry_fallback"
                )
            else:
                gm = gm_retry
            break
        gm = gm_retry
    gm = _repair_terminal_player_facing_if_needed(
        gm, reason="api_targeted_retry_post_terminal"
    )
    gm = apply_response_policy_enforcement(
        gm,
        response_policy=response_policy,
        player_text=user_text,
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
        discovered_clues=known_clues,
    )
    gm = _repair_terminal_player_facing_if_needed(
        gm, reason="api_post_response_policy_enforcement"
    )
    return gm


def _run_resolved_turn_pipeline(
    *,
    campaign: dict,
    character: dict,
    session: dict,
    world: dict,
    combat: dict,
    scene: dict,
    recent_log: list,
    resolution: dict,
    normalized_action: dict | None,
    fallback_user_text: str,
    segmented_turn: dict | None = None,
    route_choice: str | None = None,
    directed_social_entry: dict | None = None,
) -> tuple[dict, dict, dict, dict, list[str], dict]:
    """Shared resolved-turn flow for both `/api/action` and `/api/chat`.

    Stage 5: authoritative engine mutation is applied first.
    Stage 6-7: prompt context and GPT narration are built only from that post-resolution state.
    """
    scene, session, combat, authoritative_clue_updates, scene_rt = _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=normalized_action,
    )

    user_text = resolution.get('prompt') or fallback_user_text
    response_type_contract = _derive_response_type_contract_for_turn(
        session=session,
        segmented_turn=segmented_turn,
        normalized_action=normalized_action,
        resolution=resolution,
        raw_player_text=user_text,
        route_choice=route_choice,
        directed_social_entry=directed_social_entry,
    )
    gm = _build_gpt_narration_from_authoritative_state(
        campaign=campaign,
        world=world,
        session=session,
        character=character,
        scene=scene,
        combat=combat,
        recent_log=recent_log,
        user_text=user_text,
        resolution=resolution,
        scene_runtime=scene_rt,
        segmented_turn=segmented_turn,
        route_choice=route_choice,
        directed_social_entry=directed_social_entry,
        response_type_contract=response_type_contract,
    )
    return (scene, session, combat, gm, authoritative_clue_updates, response_type_contract)


def _is_pending_check_resolution(resolution: dict | None) -> bool:
    """True when resolution asks player for a roll instead of a resolved outcome."""
    if not isinstance(resolution, dict):
        return False
    if not resolution.get("requires_check"):
        return False
    if resolution.get("skill_check"):
        return False
    return isinstance(resolution.get("check_request"), dict)


def _is_offscene_social_target_resolution(resolution: dict | None) -> bool:
    if not isinstance(resolution, dict):
        return False
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return bool(social.get("offscene_target"))


def _build_offscene_target_gm_output(resolution: dict) -> dict:
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    npc_name = str(social.get("npc_name") or "").strip() or "That person"
    return {
        "player_facing_text": f"{npc_name} is no longer here to answer.",
        "tags": ["offscene_target"],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "engine_offscene_target_guard",
    }


def _build_check_prompt_gm_output(resolution: dict) -> dict:
    """Engine-authored response when a check is required before narration."""
    check = resolution.get("check_request") if isinstance(resolution.get("check_request"), dict) else {}
    prompt = (
        str(check.get("player_prompt") or "").strip()
        or str(resolution.get("hint") or "").strip()
        or "A check is required before this action can be resolved."
    )
    prompt = neutralize_engine_voice_for_player(prompt)
    return {
        "player_facing_text": prompt,
        "tags": ["check_required"],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "engine_check_prompt",
    }


def _build_adjudication_gm_output(adjudication: dict) -> dict:
    """Engine-authored adjudication output kept separate from GPT narration."""
    return {
        'player_facing_text': neutralize_engine_voice_for_player(str(adjudication.get('player_facing_text') or '')),
        'tags': ['adjudication_query'],
        'scene_update': None,
        'activate_scene_id': None,
        'new_scene_draft': None,
        'world_updates': None,
        'suggested_action': None,
        'debug_notes': f"adjudication:{adjudication.get('category')}",
    }


def _is_campaign_start_turn_request(text: str | None, session: dict, recent_log: list | None) -> bool:
    """Detect explicit campaign-start/opening requests on a fresh turn."""
    if not isinstance(text, str) or not text.strip():
        return False
    turn_counter = int(session.get("turn_counter", 0) or 0)
    if turn_counter > 1:
        return False
    if recent_log:
        return False
    low = text.strip().lower()
    cues = (
        "begin the campaign",
        "begin campaign",
        "start the campaign",
        "start campaign",
        "begin the game",
        "start the game",
        "begin adventure",
        "start adventure",
    )
    return any(cue in low for cue in cues)


_MECHANICS_OR_PROCEDURAL_TOKENS: tuple[str, ...] = (
    "roll",
    "check",
    "skill check",
    "dc",
    "difficulty",
    "saving throw",
    "need to roll",
    "do i need",
    "does this need",
    "mechanically",
    "rules-wise",
    "rules wise",
    "what actions are available",
    "which actions are available",
    "actions are available",
    "mechanic",
    "rules",
    "procedure",
)
_ENGINE_STATE_QUERY_PATTERNS: tuple[str, ...] = (
    "earshot",
    "who can hear",
    "in range",
    "how far",
    "distance",
    "is anyone else here",
    "who is here",
    "what is my",
    "current hp",
    "spell slots",
    "inventory",
)
_OOC_MARKER_PATTERNS: tuple[str, ...] = (
    r"\booc\b",
    r"\bout of character\b",
    r"\bas a player\b",
    r"^\s*\(\(",
)
_QUESTION_START_TOKENS: tuple[str, ...] = (
    "where",
    "what",
    "who",
    "when",
    "why",
    "how",
    "can",
    "could",
    "would",
    "should",
    "do",
    "does",
    "is",
    "are",
    "will",
)
_IN_CHARACTER_REPLY_PREFIXES: tuple[str, ...] = (
    "yes",
    "no",
    "maybe",
    "i say",
    "i tell",
    "i reply",
    "i answer",
)
_IN_CHARACTER_COMMAND_PREFIXES: tuple[str, ...] = (
    "lead the way",
    "tell me",
    "show me",
    "take me",
    "bring me",
    "let me through",
    "stand aside",
    "step aside",
)
_DIALOGUE_QUESTION_WORDS: tuple[str, ...] = (
    "who",
    "what",
    "where",
    "when",
    "why",
    "how",
    "which",
)
_DIALOGUE_SPEECH_TOKENS: tuple[str, ...] = (
    "ask",
    "asks",
    "asked",
    "question",
    "tell me",
    "do you know",
    "what do you know",
    "say",
    "reply",
    "answer",
    "i ask",
    "we ask",
)
_DIALOGUE_INFO_REQUEST_PHRASES: tuple[str, ...] = (
    "do you know",
    "what do you know",
    "tell me what you know",
    "who attacked",
    "what are they planning",
    "who saw this happen",
    "who saw it",
    "where can i find",
    "where can we find",
    "where do i find",
    "where are they",
)
_AMBIGUOUS_DIALOGUE_FOLLOWUP_PHRASES: tuple[str, ...] = (
    "what should i do next",
    "what's the next step",
    "what is the next step",
    "where does this lead",
    "where does this go",
    "what now",
)
_WORLD_ACTION_STRONG_PATTERNS: tuple[str, ...] = (
    r"\b(?:i|we)\s+(?:search|sneak|attack|follow|track|cast|inspect|examine|check|investigate)\b",
    r"\b(?:i|we)\s+(?:grab|seize|shove|push|pull|pin|restrain|force|coerce|threaten)\b",
    r"\b(?:i|we)\s+(?:pick up|open|unlock|break|climb|jump|hide|steal|manipulate)\b",
)
_WORLD_ACTION_FORCEFUL_PATTERNS: tuple[str, ...] = (
    r"\b(?:i|we)\s+(?:grab|seize|attack|strike|cast|force|coerce|threaten|restrain)\b",
    r"\b(?:i|we)\s+(?:follow|track|sneak|search)\b",
)


def _merged_text_for_dialogue_routing(segmented_turn: dict | None, player_text: str) -> str:
    """Rejoin turn segments so hail + extracted question still read as one line for addressing."""
    if not isinstance(segmented_turn, dict):
        return str(player_text or "").strip()
    ordered_keys = (
        "declared_action_text",
        "spoken_text",
        "adjudication_question_text",
        "observation_intent_text",
    )
    parts: list[str] = []
    seen: set[str] = set()
    for key in ordered_keys:
        raw = segmented_turn.get(key)
        if not isinstance(raw, str):
            continue
        s = raw.strip()
        if not s or s in seen:
            continue
        parts.append(s)
        seen.add(s)
    return " ".join(parts) if parts else str(player_text or "").strip()


def _find_world_npc_reference_id(text: str, world: dict) -> str | None:
    return find_world_npc_reference_id_in_text(text, world)


def _is_information_seeking_clause(text: str) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    if any(phrase in low for phrase in _DIALOGUE_INFO_REQUEST_PHRASES):
        return True
    if any(token in low for token in _DIALOGUE_SPEECH_TOKENS) and any(word in low for word in _DIALOGUE_QUESTION_WORDS):
        return True
    if "?" in low:
        lead = re.sub(r'^[^a-z0-9"]+', "", low)
        lead = lead.replace('"', "")
        first = lead.split(" ", 1)[0] if lead else ""
        if first in _QUESTION_START_TOKENS:
            return True
        if any(word in low for word in _DIALOGUE_QUESTION_WORDS):
            return True
    return False


def _has_dialogue_cue(*, text: str, segmented_turn: dict | None) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    spoken_text = segmented_turn.get("spoken_text") if isinstance(segmented_turn, dict) else None
    if isinstance(spoken_text, str) and spoken_text.strip():
        return True
    if '"' in low:
        return True
    if _is_information_seeking_clause(low):
        return True
    return any(token in low for token in _DIALOGUE_SPEECH_TOKENS)


def is_world_action(text: str, segmented_turn: dict | None = None) -> bool:
    clause = (
        (segmented_turn.get("declared_action_text") if isinstance(segmented_turn, dict) else None)
        or text
    )
    low = str(clause or "").strip().lower()
    if not low:
        return False
    return any(re.search(pattern, low) for pattern in _WORLD_ACTION_STRONG_PATTERNS)


def is_directed_dialogue(
    text: str,
    *,
    scene: dict,
    session: dict,
    world: dict,
    segmented_turn: dict | None = None,
    canonical_social_entry: dict | None = None,
) -> bool:
    ce = canonical_social_entry
    if ce is None:
        ce = resolve_directed_social_entry(
            session=session,
            scene=scene,
            world=world,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=str(text or ""),
        )
    if ce.get("should_route_social"):
        return True
    merged = _merged_text_for_dialogue_routing(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(text or ""),
    )
    primary_clause = merged.strip() or str(text or "").strip()
    clause = str(primary_clause or "").strip()
    if not clause:
        return False
    if _is_explicit_ooc(clause) or _is_explicit_ooc(text):
        return False
    if _contains_mechanics_or_procedural_language(clause):
        return False
    if _is_engine_state_question(clause):
        return False
    # Ambiguity rule: during an active NPC exchange, "next step"-style
    # follow-ups default to that interlocutor unless explicit procedural/OOC
    # markers were present above.
    if _has_active_social_interlocutor(session, scene=scene, world=world) and _is_ambiguous_dialogue_followup(
        clause
    ):
        return True

    scene_npcs = scene_npcs_in_active_scene(scene, world)
    addressed_npc_id = find_addressed_npc_id_for_turn(clause, session, world, scene)
    has_present_character = bool(scene_npcs)
    has_world_reference = bool(_find_world_npc_reference_id(clause, world))
    has_dialogue_cue = _has_dialogue_cue(text=text, segmented_turn=segmented_turn)
    asks_for_information = _is_information_seeking_clause(clause)

    if addressed_npc_id:
        return True
    if has_dialogue_cue and has_world_reference:
        return True
    if has_dialogue_cue and has_present_character:
        return True
    if asks_for_information and has_present_character:
        return True
    return False


def choose_interaction_route(
    text: str,
    *,
    scene: dict,
    session: dict,
    world: dict,
    segmented_turn: dict | None = None,
    canonical_social_entry: dict | None = None,
) -> str:
    """Choose coarse chat lane: dialogue, action, or undecided.

    Canonical social entry is computed in :func:`game.interaction_context.resolve_directed_social_entry`
    (pass *canonical_social_entry* from /api/chat to avoid duplicate work).
    """
    directed_dialogue = is_directed_dialogue(
        text,
        scene=scene,
        session=session,
        world=world,
        segmented_turn=segmented_turn,
        canonical_social_entry=canonical_social_entry,
    )
    world_action = is_world_action(text, segmented_turn=segmented_turn)
    has_dialogue_cue = _has_dialogue_cue(text=text, segmented_turn=segmented_turn)
    low = str(text or "").strip().lower()
    forceful_action = any(re.search(pattern, low) for pattern in _WORLD_ACTION_FORCEFUL_PATTERNS)

    if directed_dialogue:
        # Dialogue lock: keep spoken questioning in social lane unless action intent is forceful.
        if world_action and (forceful_action or not has_dialogue_cue):
            return "action"
        return "dialogue"
    if world_action:
        return "action"
    return "undecided"


def _build_dialogue_first_action(
    *,
    player_text: str,
    scene: dict,
    session: dict,
    world: dict,
    segmented_turn: dict | None,
    canonical_social_entry: dict | None = None,
) -> dict | None:
    ce = canonical_social_entry
    if ce is None:
        ce = resolve_directed_social_entry(
            session=session,
            scene=scene,
            world=world,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=str(player_text or ""),
        )
    merged_address = merge_turn_segments_for_directed_social_entry(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(player_text or ""),
    )
    if not ce.get("should_route_social") and not is_directed_dialogue(
        player_text,
        scene=scene,
        session=session,
        world=world,
        segmented_turn=segmented_turn,
        canonical_social_entry=ce,
    ):
        return None

    target_id = str(ce.get("target_actor_id") or "").strip() or resolve_dialogue_lock_action_target_id(
        merged_address or player_text,
        scene=scene,
        session=session,
        world=world,
    )

    action_kind = (
        "question"
        if _is_information_seeking_clause(merged_address or player_text)
        or "?" in str(merged_address or player_text or "")
        else "social_probe"
    )
    action_label = str(player_text or "").strip()
    if not action_label:
        return None
    _, _route_meta = should_route_addressed_question_to_social(
        merged_address or player_text,
        session=session,
        world=world,
        scene_envelope=scene if isinstance(scene, dict) else None,
    )
    metadata = {
        "routed_via_dialogue_lock": True,
        "route": "dialogue",
        "canonical_entry_path": "social",
        "canonical_entry_reason": ce.get("reason"),
        "canonical_entry_target_actor_id": ce.get("target_actor_id") or target_id,
        "intent_route_debug": build_intent_route_debug_social_exchange(
            should_route_meta=_route_meta if isinstance(_route_meta, dict) else None,
            resolved_target_id=target_id,
        ),
    }
    if target_id:
        metadata["active_interaction_target_id"] = target_id
    out = {
        "id": slugify(f"{action_kind}-{target_id or 'npc'}") or "social",
        "label": action_label[:140],
        "type": action_kind,
        "social_intent_class": "social_exchange",
        "prompt": action_label,
        "metadata": metadata,
    }
    if target_id:
        out["target_id"] = target_id
        out["targetEntityId"] = target_id
    return out


def _is_explicit_ooc(text: str | None) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    return any(re.search(pattern, low) for pattern in _OOC_MARKER_PATTERNS)


def _contains_mechanics_or_procedural_language(text: str | None) -> bool:
    low = str(text or "").strip().lower()
    if not low:
        return False
    return any(token in low for token in _MECHANICS_OR_PROCEDURAL_TOKENS)


def _has_active_social_interlocutor(
    session: dict | None,
    *,
    scene: dict | None = None,
    world: dict | None = None,
) -> bool:
    inspected = inspect_interaction_context(session if isinstance(session, dict) else {})
    target_id = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    if not target_id:
        return False
    if not assert_valid_speaker(
        target_id,
        session if isinstance(session, dict) else {},
        scene_envelope=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    ):
        return False
    kind = str((inspected or {}).get("active_interaction_kind") or "").strip().lower()
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    engagement = str((inspected or {}).get("engagement_level") or "").strip().lower()
    return (kind == "social" or mode == "social") and engagement in {"engaged", "active", ""}


def _is_ambiguous_dialogue_followup(text: str | None) -> bool:
    """Return True for short follow-up prompts that can read IC or OOC."""
    low = str(text or "").strip().lower()
    if not low:
        return False
    return any(phrase in low for phrase in _AMBIGUOUS_DIALOGUE_FOLLOWUP_PHRASES)


def _is_engine_state_question(text: str | None) -> bool:
    low = str(text or "").strip().lower()
    if not low or "?" not in low:
        return False
    return any(pattern in low for pattern in _ENGINE_STATE_QUERY_PATTERNS)


def _looks_like_in_character_exchange_clause(text: str | None, spoken_text: str | None) -> bool:
    clause = str(text or "").strip()
    low = clause.lower()
    if not clause:
        return False
    if isinstance(spoken_text, str) and spoken_text.strip():
        return True
    if "?" in clause:
        words = low.replace("?", " ").split()
        if words and words[0] in _QUESTION_START_TOKENS:
            return True
    if any(low.startswith(prefix) for prefix in _IN_CHARACTER_COMMAND_PREFIXES):
        return True
    if " require an audience" in f" {low}" or low.startswith("footman? i require an audience"):
        return True
    return any(low.startswith(prefix) for prefix in _IN_CHARACTER_REPLY_PREFIXES)


def _prefer_dialogue_over_adjudication(
    *,
    player_text: str,
    segmented_turn: dict | None,
    adjudication_text: str | None,
    has_active_interaction: bool = False,
    scene: dict | None = None,
    session: dict | None = None,
    world: dict | None = None,
    canonical_social_entry: dict | None = None,
) -> bool:
    """Bias ambiguous turns toward dialogue instead of procedural adjudication.

    When *has_active_interaction* is True the classifier uses narrowed
    feasibility patterns so that normal in-character social questioning
    during an active NPC conversation is not captured as adjudication.
    """
    if isinstance(scene, dict) and isinstance(session, dict) and isinstance(world, dict):
        ce = canonical_social_entry
        if ce is None:
            ce = resolve_directed_social_entry(
                session=session,
                scene=scene,
                world=world,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                raw_text=str(player_text or ""),
            )
        if ce.get("should_route_social"):
            return True
    spoken_text = segmented_turn.get("spoken_text") if isinstance(segmented_turn, dict) else None
    declared_action_text = segmented_turn.get("declared_action_text") if isinstance(segmented_turn, dict) else None
    primary_clause = _merged_text_for_dialogue_routing(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        str(player_text or ""),
    ).strip() or str(declared_action_text or spoken_text or player_text or "").strip()
    if not primary_clause:
        return False
    if _is_explicit_ooc(player_text) or _is_explicit_ooc(primary_clause):
        return False
    if _contains_mechanics_or_procedural_language(primary_clause):
        return False
    if _is_engine_state_question(adjudication_text or primary_clause):
        return False
    if has_active_interaction and _is_ambiguous_dialogue_followup(primary_clause):
        return True
    if isinstance(scene, dict) and isinstance(session, dict) and isinstance(world, dict):
        if choose_interaction_route(
            player_text,
            scene=scene,
            session=session,
            world=world,
            segmented_turn=segmented_turn,
        ) == "dialogue":
            return True
    if classify_adjudication_query(
        adjudication_text or primary_clause,
        has_active_interaction=has_active_interaction,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
    ) is not None:
        return False
    return _looks_like_in_character_exchange_clause(primary_clause, spoken_text)


def _build_opening_scene_resolution(user_text: str, scene_id: str) -> dict:
    """Engine-owned opening-scene resolution for explicit campaign start requests."""
    text = (user_text or "").strip() or "Begin the campaign."
    return {
        "kind": "scene_opening",
        "action_id": "campaign_start_opening_scene",
        "label": text,
        "prompt": text,
        "success": True,
        "resolved_transition": False,
        "target_scene_id": scene_id or None,
        "clue_id": None,
        "discovered_clues": [],
        "world_updates": None,
        "state_changes": {
            "opening_scene_turn": True,
            "arrived_at_scene": True,
            "new_scene_context_available": True,
        },
        "hint": (
            "Campaign opening turn: narrate the active scene as an immediate playable situation, "
            "with concrete opportunities grounded in the current scene state."
        ),
    }


def compose_state():
    campaign = load_campaign()
    character = load_character()
    session = load_session()
    world = load_world()
    combat = load_combat()
    conditions = load_conditions()
    scene = load_active_scene()
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    state = {
        'campaign': campaign,
        'character': character,
        'session': session,
        'world': world,
        'combat': combat,
        'conditions': conditions,
        'scene': scene,
        'ui': {
            'player_can_act': player_can_act(character, combat, conditions),
            'living_enemies': [
                {'id': e['id'], 'name': e['name'], 'hp': e['hp']['current'], 'max_hp': e['hp']['max']}
                for e in scene['scene'].get('enemies', []) if e['hp']['current'] > 0
            ],
            'scene_ids': list_scene_ids(),
            'affordances': get_available_affordances(scene, session, world, mode=scene['scene'].get('mode', 'exploration'), list_scene_ids_fn=list_scene_ids, scene_graph=build_scene_graph(list_scene_ids, load_scene)),
            'clues': {
                'known': get_known_clues_with_presentation(session),
            },
        }
    }
    state['ui']['clues']['implicit'] = [c for c in state['ui']['clues']['known'] if c.get('presentation') == 'implicit']
    state['ui']['clues']['explicit'] = [c for c in state['ui']['clues']['known'] if c.get('presentation') == 'explicit']
    state['ui']['clues']['actionable'] = [c for c in state['ui']['clues']['known'] if c.get('presentation') == 'actionable']
    # Ensure clocks are initialized for the session so callers can rely on presence.
    had_clocks = isinstance(session.get('clocks'), dict) and set(session.get('clocks', {}).keys()) >= set(DEFAULT_CLOCKS.keys())
    get_or_init_clocks(session)
    if not had_clocks:
        save_session(session)
    # Sync session.character_name from character when loading (startup, import, etc.)
    char_name = (character.get('name') or '').strip() or 'You'
    if session.get('character_name') != char_name:
        session['character_name'] = char_name
        save_session(session)
    state['player_name'] = session.get('character_name') or char_name
    state['journal'] = build_player_journal(session, world, scene)
    if session.get('last_action_debug'):
        state['debug'] = session['last_action_debug']
    state['debug_traces'] = session.get('debug_traces') or []
    state['save_summary'] = get_save_summary()
    state['snapshots'] = list_snapshots()
    state['campaign_run_id'] = session.get('campaign_run_id')
    return state


@app.get('/api/state')
def get_state():
    return compose_state()


@app.get('/api/log')
def get_log():
    return {'entries': load_log()}


@app.get('/api/debug_trace')
def get_debug_trace():
    session = load_session()
    return {'traces': session.get('debug_traces') or []}


@app.post('/api/clear_log')
def api_clear_log():
    clear_log()
    return {'ok': True}


@app.post('/api/campaign')
def update_campaign(payload: dict):
    save_campaign(payload)
    return {'ok': True, 'campaign': load_campaign()}


@app.post('/api/scene')
def update_scene(payload: dict):
    save_scene(payload)
    return {'ok': True, 'scene': payload}


@app.post('/api/scene/activate')
def api_activate_scene(payload: dict):
    scene_id = (payload.get('scene_id') or '').strip()
    if not is_known_scene_id(scene_id):
        return {'ok': False, 'error': 'Unknown or invalid scene ID.'}
    scene = load_active_scene()
    session = load_session()
    combat = load_combat()
    world = load_world()
    scene, session, combat = _apply_authoritative_scene_transition(scene_id, scene, session, combat, world)
    save_session(session)
    save_combat(combat)
    return {'ok': True, 'scene': scene, 'session': session}


@app.post('/api/character')
def update_character(payload: dict):
    save_character(payload)
    return {'ok': True, 'character': payload}


@app.post('/api/world')
def update_world(payload: dict):
    save_world(payload)
    return {'ok': True, 'world': payload}


@app.post('/api/import_sheet')
def api_import_sheet(file: UploadFile = File(...)):
    temp_path = BASE_DIR / 'data' / '_import_temp.json'
    temp_path.write_bytes(file.file.read())
    character = import_sheet(temp_path)
    save_character(character)
    temp_path.unlink(missing_ok=True)
    return {'ok': True, 'character': character}


@app.post('/api/response_mode')
def update_response_mode(req: ResponseModeUpdate):
    session = load_session()
    allowed = {'terse', 'standard', 'vivid', 'tactical', 'investigative'}
    mode = req.mode if isinstance(req.mode, str) else 'standard'
    if mode not in allowed:
        mode = 'standard'
    session['response_mode'] = mode
    save_session(session)
    return {'ok': True, 'session': session}



@app.post('/api/reset_combat')
def api_reset_combat():
    combat = load_combat()
    combat.clear()
    combat.update(create_fresh_combat_state())
    save_combat(combat)
    return {'ok': True}


@app.post('/api/new_campaign')
def new_campaign():
    """Hard reset: new session graph, fresh combat, world playthrough cleared, transcript empty."""
    meta = apply_new_campaign_hard_reset()
    # When ASHEN_THRONES_DEV_VERIFY=1, ``campaign_reset`` prints a compact runtime-clean summary.
    if "dev_verify_ok" not in meta:
        print("[API] New campaign started", meta.get("campaign_run_id"))
    return {"status": "ok", **meta}


@app.post('/api/reset_session')
def api_reset_session():
    """Reset runtime session state; preserves campaign/world data."""
    session = load_session()
    reset_session_state(session)
    save_session(session)
    clear_log()
    combat = load_combat()
    combat.clear()
    combat.update(create_fresh_combat_state())
    save_combat(combat)
    return {'ok': True, **compose_state()}


@app.get('/api/snapshots')
def api_list_snapshots():
    """List all save snapshots (id, created_at, label)."""
    return {'snapshots': list_snapshots()}


@app.post('/api/snapshots')
def api_create_snapshot(req: SnapshotCreateRequest):
    """Create a snapshot of current runtime state. Optional label for playtesting."""
    meta = create_snapshot(label=req.label)
    return {'ok': True, 'snapshot': meta, **compose_state()}


@app.post('/api/snapshots/load')
def api_load_snapshot(payload: dict):
    """Load a snapshot by id. Restores session, world, combat, character, log."""
    snapshot_id = (payload.get('snapshot_id') or payload.get('id') or '').strip()
    if not snapshot_id:
        return {'ok': False, 'error': 'snapshot_id required'}
    meta = load_snapshot(snapshot_id)
    if meta is None:
        return {'ok': False, 'error': 'Snapshot not found'}
    return {'ok': True, 'snapshot': meta, **compose_state()}


@app.post('/api/action')
def action(req: ActionRequest):
    campaign = load_campaign()
    character = load_character()
    session = load_session()
    world = load_world()
    combat = load_combat()
    conditions = load_conditions()
    scene = load_active_scene()
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    scene_before_id = scene['scene']['id']

    trace: dict = {
        'timestamp': utc_iso_now(),
        'source': 'action',
        'action_type': req.action_type,
        'raw_input': (req.intent or '').strip() or req.action_type,
        'turn_stage_order': list(AUTHORITATIVE_TURN_STAGE_ORDER),
        'incoming_payload': _sanitize_incoming_payload(req),
        'parsed_intent': None,
        'normalized_action': None,
        'resolution': None,
        'scene_before': scene['scene']['id'],
        'scene_after': None,
        'clue_updates': [],
        'world_flag_updates': [],
        'turn_trace': None,
        'gpt_called': False,
        'response_ok': True,
        'error': None,
    }
    clue_presentation_before = _snapshot_known_clue_presentations(session)

    resolution = None
    normalized_action = None
    authoritative_clue_updates: list[str] = []
    surfaced_clue_telemetry: list[str] = []
    fallback_user_text = req.intent or req.action_type
    gm: dict | None = None
    response_type_contract: dict | None = None
    run_resolved_pipeline = False
    implied_context = {"applied": False}
    # Stages 1-3: request payload provides player input and normalized/classified action type.
    if req.action_type == 'roll_initiative':
        # Stage 4 (engine resolution) only; no GPT narration for initiative start.
        resolution = roll_initiative(character, scene, combat, conditions)
        gm = {'player_facing_text': 'Initiative is rolled.', 'tags': ['initiative'], 'scene_update': None, 'activate_scene_id': None, 'new_scene_draft': None, 'world_updates': None, 'suggested_action': None, 'debug_notes': 'Initiative app-side.'}
    elif req.action_type == 'attack':
        # Stages 1-4: input -> classification -> deterministic engine resolution.
        if not player_can_act(character, combat, conditions):
            _finalize_and_append_trace(session, trace, False, 'You cannot act right now.')
            return {'ok': False, 'error': 'You cannot act right now.'}
        resolution = resolve_attack(character, scene, req.attack_id, req.target_id, req.modifiers, conditions)
        combat['player_turn_used'] = True
        prune_initiative(scene, combat, character['id'])
        fallback_user_text = req.intent or f'Attack with {req.attack_id}'
        run_resolved_pipeline = True
    elif req.action_type == 'skill_check':
        # Stages 1-4: input -> classification -> deterministic engine resolution.
        if not player_can_act(character, combat, conditions):
            _finalize_and_append_trace(session, trace, False, 'You cannot act right now.')
            return {'ok': False, 'error': 'You cannot act right now.'}
        resolution = resolve_skill(character, req.skill_id, req.intent or '')
        combat['player_turn_used'] = True
        fallback_user_text = req.intent or f'Use {req.skill_id}'
        run_resolved_pipeline = True
    elif req.action_type == 'cast_spell':
        # Stages 1-4: input -> classification -> deterministic engine resolution.
        if not player_can_act(character, combat, conditions):
            _finalize_and_append_trace(session, trace, False, 'You cannot act right now.')
            return {'ok': False, 'error': 'You cannot act right now.'}
        resolution = resolve_spell(character, scene, req.spell_id, req.target_id, conditions)
        combat['player_turn_used'] = True
        prune_initiative(scene, combat, character['id'])
        fallback_user_text = req.intent or f'Cast {req.spell_id}'
        run_resolved_pipeline = True
    elif req.action_type == 'end_turn':
        if not combat['in_combat']:
            _finalize_and_append_trace(session, trace, False, 'Combat is not active.')
            return {'ok': False, 'error': 'Combat is not active.'}
        if not combat['player_turn_used']:
            _finalize_and_append_trace(session, trace, False, 'Take an action before ending the turn.')
            return {'ok': False, 'error': 'Take an action before ending the turn.'}
        advance_turn(combat)
        enemy_result = None
        if combat['active_actor_id'] and combat['active_actor_id'] != character['id']:
            resolution = enemy_take_turn(character, scene, combat, conditions)
            prune_initiative(scene, combat, character['id'])
            if not end_combat_if_done(scene, combat):
                advance_turn(combat)
                cleanup_player_turn(character)
                combat['player_turn_used'] = False
            fallback_user_text = resolution.get('hint', 'Enemy takes its turn.')
            run_resolved_pipeline = True
        else:
            cleanup_player_turn(character)
            combat['player_turn_used'] = False
            resolution = build_end_turn_result(combat)
            gm = {'player_facing_text': f'Round {combat["round"]}. Your turn.', 'tags': ['end_turn'], 'scene_update': None, 'activate_scene_id': None, 'new_scene_draft': None, 'world_updates': None, 'suggested_action': None, 'debug_notes': 'No enemy response.'}
    elif req.action_type == 'exploration':
        raw = req.exploration_action if isinstance(req.exploration_action, dict) else None
        if not raw and req.intent:
            raw = req.intent
        normalized_action = normalize_scene_action(raw)
        implied_context = _prepare_interaction_from_turn_input(
            session,
            world,
            scene_before_id,
            req.intent or normalized_action.get('prompt') or normalized_action.get('label'),
            scene=scene,
            normalized_action=normalized_action,
        )
        normalized_type = (normalized_action.get('type') or '').strip().lower()
        raw_type = (raw.get('type') or '').strip().lower() if isinstance(raw, dict) else ''
        if raw_type in SOCIAL_KINDS:
            normalized_action['type'] = raw_type
            normalized_type = raw_type
        if normalized_type in SOCIAL_KINDS:
            normalized_action['type'] = normalized_type
            resolution = resolve_social_action(
                scene, session, world, normalized_action,
                raw_player_text=req.intent or None,
                character=character,
                turn_counter=session.get('turn_counter', 0),
            )
        else:
            resolution = resolve_exploration_action(
                scene, session, world, normalized_action,
                raw_player_text=req.intent or None,
                list_scene_ids=list_scene_ids,
                character=character,
                load_scene_fn=load_scene,
            )
        fallback_user_text = req.intent or resolution.get('label', '')
        run_resolved_pipeline = True
    elif req.action_type == 'social':
        raw = req.social_action if isinstance(req.social_action, dict) else None
        if not raw and req.intent:
            raw = req.intent
        normalized_action = normalize_scene_action(raw) if raw else normalize_scene_action({'type': 'social_probe', 'label': req.intent or 'Social', 'prompt': req.intent or 'Social'})
        implied_context = _prepare_interaction_from_turn_input(
            session,
            world,
            scene_before_id,
            req.intent or normalized_action.get('prompt') or normalized_action.get('label'),
            scene=scene,
            normalized_action=normalized_action,
        )
        if raw and (raw.get('type') or '').strip().lower() in SOCIAL_KINDS:
            normalized_action['type'] = (raw.get('type') or 'social_probe').strip().lower()
        resolution = resolve_social_action(
            scene, session, world, normalized_action,
            raw_player_text=req.intent or None,
            character=character,
            turn_counter=session.get('turn_counter', 0),
        )
        fallback_user_text = req.intent or resolution.get('label', '')
        run_resolved_pipeline = True
    else:
        _finalize_and_append_trace(session, trace, False, f'Unsupported action type: {req.action_type}')
        return {'ok': False, 'error': f'Unsupported action type: {req.action_type}'}

    _record_scene_pressure_input(
        session,
        scene_before_id,
        fallback_user_text,
        normalized_action=normalized_action,
        resolution=resolution if isinstance(resolution, dict) else None,
    )

    # Engine-owned roll prompting: when a check is required, skip GPT and return
    # deterministic check prompt text from authoritative resolution payload.
    if run_resolved_pipeline and _is_offscene_social_target_resolution(resolution):
        response_type_contract = _derive_response_type_contract_for_turn(
            session=session,
            segmented_turn=None,
            normalized_action=normalized_action,
            resolution=resolution,
            raw_player_text=fallback_user_text,
        )
        gm = _build_offscene_target_gm_output(resolution)
        run_resolved_pipeline = False
        trace['gpt_called'] = False

    if run_resolved_pipeline and _is_pending_check_resolution(resolution):
        response_type_contract = _derive_response_type_contract_for_turn(
            session=session,
            segmented_turn=None,
            normalized_action=normalized_action,
            resolution=resolution,
            raw_player_text=fallback_user_text,
        )
        gm = _build_check_prompt_gm_output(resolution)
        run_resolved_pipeline = False
        trace['gpt_called'] = False

    # Stages 5-7: authoritative mutation -> prompt context from mutated state -> GPT narration.
    if run_resolved_pipeline and isinstance(resolution, dict):
        scene, session, combat, gm, turn_clue_updates, response_type_contract = _run_resolved_turn_pipeline(
            campaign=campaign,
            character=character,
            session=session,
            world=world,
            combat=combat,
            scene=scene,
            recent_log=load_log(),
            resolution=resolution,
            normalized_action=normalized_action,
            fallback_user_text=fallback_user_text,
        )
        authoritative_clue_updates.extend(turn_clue_updates)
    if gm is None:
        gm = {'player_facing_text': '', 'tags': [], 'scene_update': None, 'activate_scene_id': None, 'new_scene_draft': None, 'world_updates': None, 'suggested_action': None, 'debug_notes': 'No narration generated.'}
    if response_type_contract is None:
        response_type_contract = _derive_response_type_contract_for_turn(
            session=session,
            segmented_turn=None,
            normalized_action=normalized_action,
            resolution=resolution if isinstance(resolution, dict) else None,
            raw_player_text=fallback_user_text,
            attach_to_resolution=bool(isinstance(resolution, dict)),
        )

    gm, _narr_consistency = _finalize_player_facing_for_turn(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session,
        world=world,
        scene=scene,
        include_resolution_in_sanitizer=True,
    )
    for _rt in _narr_consistency.get("repaired_discovered_clue_texts") or []:
        if isinstance(_rt, str) and _rt.strip() and _rt.strip() not in authoritative_clue_updates:
            authoritative_clue_updates.append(_rt.strip())

    scene, session, combat, surfaced_clue_telemetry, narration_social_leads = _apply_post_gm_updates(
        gm, scene, session, world, combat, resolution=resolution if isinstance(resolution, dict) else None
    )
    for _txt in narration_social_leads:
        if isinstance(_txt, str) and _txt.strip() and _txt.strip() not in authoritative_clue_updates:
            authoritative_clue_updates.append(_txt.strip())
    remember_recent_contextual_leads(
        session,
        scene['scene']['id'],
        gm.get('player_facing_text') if isinstance(gm.get('player_facing_text'), str) else '',
    )
    _update_interaction_context_after_action(
        session,
        resolution,
        scene_changed=scene_before_id != scene['scene']['id'],
        preserve_continuity=bool(
            (implied_context.get("applied") or implied_context.get("interaction_established"))
            and not implied_context.get("commitment_broken")
        ),
    )
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")

    leads_inspection = _lead_debug_trace_around_authoritative_reconcile(session)

    # Build action pipeline debug (no hidden facts or secrets).
    if isinstance(req.intent, str):
        _player_input = req.intent
    elif req.action_type == 'exploration' and resolution and isinstance(resolution, dict) and resolution.get('prompt'):
        _player_input = resolution['prompt']
    else:
        _player_input = req.action_type
    session['last_action_debug'] = _build_action_debug(
        req.action_type, _player_input, normalized_action, resolution, response_type_contract
    )
    _merge_emergent_actor_debug_into_action_debug(session)

    # Populate trace for success path.
    trace['normalized_action'] = (
        {k: normalized_action[k] for k in ('id', 'label', 'type', 'prompt', 'targetSceneId', 'target_scene_id') if k in normalized_action}
        if normalized_action and isinstance(normalized_action, dict) else None
    )
    trace['resolution'] = _sanitize_resolution(resolution)
    trace['response_type_contract'] = compact_response_type_contract(response_type_contract)
    trace['scene_after'] = scene['scene']['id']
    deduped_clue_updates: list[str] = []
    for txt in authoritative_clue_updates:
        if isinstance(txt, str) and txt.strip() and txt.strip() not in deduped_clue_updates:
            deduped_clue_updates.append(txt.strip())
    trace['clue_updates'] = deduped_clue_updates
    trace['world_flag_updates'] = _trace_world_updates(gm.get('world_updates'))
    trace['turn_trace'] = _build_compact_turn_trace(
        source='action',
        action_type=req.action_type,
        raw_input=trace['raw_input'],
        parsed_intent=None,
        segmented_turn=None,
        normalized_action=normalized_action,
        implied_context=implied_context,
        resolution=resolution,
        scene_before=trace['scene_before'],
        scene_after=trace['scene_after'],
        authoritative_clue_updates=deduped_clue_updates,
        clue_presentation_before=clue_presentation_before,
        session=session,
        world=world,
        scene=scene,
        leads_inspection=leads_inspection,
        response_type_contract=response_type_contract,
    )
    trace['gpt_called'] = req.action_type != 'roll_initiative' and not (
        req.action_type == 'end_turn' and gm.get('debug_notes') == 'No enemy response.'
    )
    _finalize_and_append_trace(session, trace, True, None)

    save_character(character)
    save_world(world)
    save_combat(combat)
    save_session(session)
    save_scene(scene)

    from game.gm import classify_player_intent

    # Build structured log meta without leaking hidden-fact content.
    if isinstance(req.intent, str):
        player_input = req.intent
    elif req.action_type == 'exploration' and resolution and isinstance(resolution, dict) and resolution.get('prompt'):
        player_input = resolution['prompt']
    else:
        player_input = req.action_type
    intent = classify_player_intent(player_input)

    gm_prompt_summary: dict = {
        'scene_id': scene['scene'].get('id'),
        'scene_mode': scene['scene'].get('mode'),
        'response_mode': session.get('response_mode', 'standard'),
        'response_type_contract': compact_response_type_contract(response_type_contract),
    }
    if req.action_type == 'exploration' and resolution and isinstance(resolution, dict):
        gm_prompt_summary['exploration'] = {
            'action_id': resolution.get('action_id'),
            'kind': resolution.get('kind'),
            'scene_transition_occurred': bool(resolution.get('resolved_transition')),
        }

    append_log(
        {
            'timestamp': utc_iso_now(),
            'request': req.model_dump(),
            'resolution': resolution,
            'gm_output': gm,
            'log_meta': {
                'player_input': player_input,
                'intent_classification': intent,
                'gm_prompt_context_summary': gm_prompt_summary,
                'gm_raw_output_meta': {'has_output': True},
                'approved_state_updates': {
                    'scene_update': gm.get('scene_update'),
                    'world_updates': gm.get('world_updates'),
                    'new_scene_draft': gm.get('new_scene_draft'),
                },
                'rejected_state_updates': [],
                'discovered_clues_added': deduped_clue_updates,
                'surfaced_clues_in_narration_non_authoritative': surfaced_clue_telemetry,
                'clocks_changed': {},
                'response_type_contract': compact_response_type_contract(response_type_contract),
            },
        }
    )
    return _build_turn_response_payload(gm=gm, resolution=resolution, include_resolution=True)


@app.post('/api/chat')
def chat(req: ChatRequest):
    campaign = load_campaign()
    character = load_character()
    session = load_session()
    snapshot_turn_start_interlocutor(session)
    world = load_world()
    combat = load_combat()
    conditions = load_conditions()
    scene = load_active_scene()
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    scene_before_id = scene['scene']['id']

    trace: dict = {
        'timestamp': utc_iso_now(),
        'source': 'chat',
        'action_type': 'chat',
        'raw_input': (req.text or '')[:500],
        'turn_stage_order': list(AUTHORITATIVE_TURN_STAGE_ORDER),
        'incoming_payload': {'text': (req.text or '')[:200]},
        'parsed_intent': None,
        'segmented_turn': None,
        'normalized_action': None,
        'resolution': None,
        'scene_before': scene['scene']['id'],
        'scene_after': None,
        'clue_updates': [],
        'world_flag_updates': [],
        'turn_trace': None,
        'gpt_called': True,
        'response_ok': True,
        'error': None,
    }
    clue_presentation_before = _snapshot_known_clue_presentations(session)

    if session.get('turn_counter') is None:
        session['turn_counter'] = 0
    session['turn_counter'] += 1

    tick = advance_world_tick(world, campaign)
    save_world(world)

    # Advance a simple time pressure clock each chat turn.
    clocks_before = dict(get_or_init_clocks(session))
    time_pressure_after = advance_clock(session, "time_pressure", 1)

    recent_log = load_log()
    scene_rt = get_scene_runtime(session, scene['scene']['id'])

    resolution: dict = {'world_tick_events': tick.get('events', [])}
    routed_via_exploration = False
    routed_via_adjudication = False
    normalized_chat: dict | None = None
    authoritative_clue_updates: list[str] = []
    surfaced_clue_telemetry: list[str] = []
    gm: dict | None = None
    response_type_contract: dict | None = None
    route_choice: str | None = None
    # Segment + canonical social entry before implied dialogue establishment so prior interlocutor
    # and continuity flags (declared switch / spoken vocative) see pre-turn binding.
    segmented_turn = segment_mixed_player_turn(req.text)
    trace['segmented_turn'] = _compact_segmented_turn(segmented_turn)
    canonical_entry = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text=req.text,
    )
    declared_switch_meta = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text=req.text,
    )
    trace['canonical_entry'] = {
        'should_route_social': bool(canonical_entry.get('should_route_social')),
        'target_actor_id': canonical_entry.get('target_actor_id'),
        'target_source': canonical_entry.get('target_source'),
        'reason': canonical_entry.get('reason'),
        'spoken_text': canonical_entry.get('spoken_text'),
        'declared_switch_detected': bool(declared_switch_meta.get('has_declared_switch')),
        'declared_switch_target_actor_id': (
            declared_switch_meta.get('target_actor_id')
            if declared_switch_meta.get('has_declared_switch')
            else None
        ),
        'continuity_overridden_by_declared_switch': bool(
            canonical_entry.get('continuity_overridden_by_declared_switch')
        ),
        'spoken_vocative_detected': bool(canonical_entry.get('spoken_vocative_detected')),
        'spoken_vocative_target_actor_id': canonical_entry.get('spoken_vocative_target_actor_id'),
        'continuity_overridden_by_spoken_vocative': bool(
            canonical_entry.get('continuity_overridden_by_spoken_vocative')
        ),
    }
    trace['canonical_entry_path'] = (
        'social' if canonical_entry.get('should_route_social') else 'undecided'
    )
    trace['canonical_entry_reason'] = canonical_entry.get('reason')
    trace['canonical_entry_target_actor_id'] = canonical_entry.get('target_actor_id')
    implied_context = _prepare_interaction_from_turn_input(
        session, world, scene_before_id, req.text, scene=scene
    )
    merged_classification = merge_turn_segments_for_directed_social_entry(
        segmented_turn if isinstance(segmented_turn, dict) else None,
        req.text,
    )
    classification_text = (
        merged_classification.strip()
        if isinstance(merged_classification, str) and merged_classification.strip()
        else (
            (segmented_turn.get("declared_action_text") if isinstance(segmented_turn, dict) else None)
            or (segmented_turn.get("spoken_text") if isinstance(segmented_turn, dict) else None)
            or req.text
        )
    )
    embedded_question_text = (
        segmented_turn.get("adjudication_question_text")
        if isinstance(segmented_turn, dict)
        else None
    )
    compact_segmented = _compact_segmented_turn(segmented_turn)

    # Stages 1-3: player input -> deterministic intent normalization/expansion -> classification.
    # Try social first when world has npcs; then exploration; then minimal intent fallback.
    if _is_campaign_start_turn_request(req.text, session, recent_log):
        routed_via_exploration = True
        normalized_chat = {
            "id": "campaign_start_opening_scene",
            "label": req.text.strip(),
            "type": "scene_opening",
            "prompt": req.text.strip(),
            "targetSceneId": scene["scene"].get("id"),
            "target_scene_id": scene["scene"].get("id"),
        }
        resolution = _build_opening_scene_resolution(req.text, scene["scene"].get("id", ""))
        scene, session, combat, gm, turn_clue_updates, response_type_contract = _run_resolved_turn_pipeline(
            campaign=campaign,
            character=character,
            session=session,
            world=world,
            combat=combat,
            scene=scene,
            recent_log=recent_log,
            resolution=resolution,
            normalized_action=normalized_chat,
            fallback_user_text=req.text,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            route_choice="action",
            directed_social_entry=canonical_entry,
        )
        authoritative_clue_updates.extend(turn_clue_updates)
        resolution['world_tick_events'] = tick.get('events', [])
        parsed = normalized_chat
    else:
        route_choice = choose_interaction_route(
            req.text,
            scene=scene,
            session=session,
            world=world,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            canonical_social_entry=canonical_entry,
        )
        # Block 4A: explicit "follow/pursue the lead to <target>" must be parsed as qualified pursuit
        # before dialogue-lock / social follow-up (which otherwise skips exploration when route is "dialogue").
        qualified_pursuit_shaped = is_qualified_pursuit_shaped(classification_text)
        parsed = None
        if not declared_switch_meta.get("has_declared_switch"):
            parsed = maybe_build_passive_interruption_wait_action(
                segmented_turn if isinstance(segmented_turn, dict) else None,
                raw_player_text=req.text,
            )
        if parsed is None and qualified_pursuit_shaped:
            parsed = parse_exploration_intent(classification_text, scene, session, world)
        if parsed is None and not qualified_pursuit_shaped:
            parsed = parse_social_intent(classification_text, scene, world)
        if parsed is None and route_choice != "action" and not qualified_pursuit_shaped:
            parsed = _build_dialogue_first_action(
                player_text=req.text,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                scene=scene,
                session=session,
                world=world,
                canonical_social_entry=canonical_entry,
            )
        if parsed is None and route_choice != "dialogue" and not qualified_pursuit_shaped:
            parsed = parse_exploration_intent(classification_text, scene, session, world)
        intent = None
        if parsed is None and route_choice != "dialogue" and not qualified_pursuit_shaped:
            intent = parse_intent(classification_text)
            if intent:
                parsed = intent  # Use full structured action from parser (id, label, type, prompt, target_id, etc.)
        # Attack when not in combat: fall back to GPT (don't route to exploration or combat)
        if parsed and (parsed.get("type") or "").strip().lower() == "attack" and not combat.get("in_combat"):
            parsed = None
        # Declared movement in segmented turns overrides social-only lanes (dialogue lock / follow-up).
        if isinstance(parsed, dict):
            _ptype = (parsed.get("type") or "").strip().lower()
            if _ptype in SOCIAL_KINDS:
                travel_override = maybe_build_declared_travel_action(
                    segmented_turn if isinstance(segmented_turn, dict) else None,
                    scene=scene["scene"],
                    session=session,
                    world=world,
                    known_scene_ids=set(list_scene_ids()),
                )
                if travel_override is not None:
                    trace["declared_travel_override"] = {
                        "applied": True,
                        "prior_action_type": _ptype,
                        "normalized_type": (travel_override.get("type") or "").strip().lower(),
                        "target_scene_id": travel_override.get("target_scene_id")
                        or travel_override.get("targetSceneId"),
                    }
                    parsed = travel_override
                else:
                    trace["declared_travel_override"] = {"applied": False}
        # Declared movement in declared_action_text must still win when the main classifier
        # chain produced no action (e.g. route/action interplay) — avoids GPT or adjudication
        # treating explicit travel as generic dialogue.
        if parsed is None:
            travel_fallback = maybe_build_declared_travel_action(
                segmented_turn if isinstance(segmented_turn, dict) else None,
                scene=scene["scene"],
                session=session,
                world=world,
                known_scene_ids=set(list_scene_ids()),
            )
            if travel_fallback is not None:
                trace["declared_travel_override"] = {
                    "applied": True,
                    "prior_action_type": None,
                    "normalized_type": (travel_fallback.get("type") or "").strip().lower(),
                    "target_scene_id": travel_fallback.get("target_scene_id")
                    or travel_fallback.get("targetSceneId"),
                    "from_unparsed_fallback": True,
                }
                parsed = travel_fallback
            elif "declared_travel_override" not in trace:
                trace["declared_travel_override"] = {"applied": False}
    _record_scene_pressure_input(
        session,
        scene_before_id,
        req.text,
        normalized_action=parsed if isinstance(parsed, dict) else None,
        resolution=None,
    )
    if parsed is not None and gm is None:
        # Stage 4: engine resolution from classified action.
        parsed_type = (parsed.get("type") or "").strip().lower()
        normalized: dict | None = None
        # Route attack to combat when in_combat; social to social engine; else exploration
        if parsed_type == "attack" and combat.get("in_combat"):
            if not player_can_act(character, combat, conditions):
                return {'ok': False, 'error': 'You cannot act right now.', **compose_state()}
            attacks = character.get("attacks") or []
            attack_id = attacks[0]["id"] if attacks else None
            if not attack_id:
                return {'ok': False, 'error': 'You have no attacks available.', **compose_state()}
            target_hint = parsed.get("target_id") or parsed.get("targetEntityId")
            resolution = resolve_attack(character, scene, attack_id, target_hint, [], conditions)
            combat["player_turn_used"] = True
            save_combat(combat)
            prune_initiative(scene, combat, character["id"])
            routed_via_exploration = True
            normalized_chat = normalize_scene_action(parsed)
            normalized = normalized_chat
            implied_context.update(
                apply_explicit_non_social_commitment_break(
                    session, world, scene_before_id, req.text, normalized, scene_envelope=scene
                )
            )
        elif parsed_type in SOCIAL_KINDS:
            routed_via_exploration = True
            normalized = parsed  # Social actions use own shape; ensure type is set
            normalized_chat = normalized
            implied_context.update(
                apply_explicit_non_social_commitment_break(
                    session, world, scene_before_id, req.text, normalized, scene_envelope=scene
                )
            )
            _sm = normalized.get("metadata")
            if not isinstance(_sm, dict):
                _sm = {}
                normalized["metadata"] = _sm
            _sm.setdefault("canonical_entry_path", "social")
            _sm.setdefault("canonical_entry_reason", canonical_entry.get("reason"))
            _sm.setdefault("canonical_entry_target_actor_id", canonical_entry.get("target_actor_id"))
            if isinstance(compact_segmented, dict) and compact_segmented:
                _sm.setdefault("segmented_turn", compact_segmented)
            trace["canonical_entry_path"] = "social"
            resolution = resolve_social_action(
                scene, session, world, normalized,
                raw_player_text=req.text,
                character=character,
                turn_counter=session.get('turn_counter', 0),
            )
        else:
            routed_via_exploration = True
            normalized = normalize_scene_action(parsed)
            normalized_chat = normalized
            implied_context.update(
                apply_explicit_non_social_commitment_break(
                    session, world, scene_before_id, req.text, normalized, scene_envelope=scene
                )
            )
            resolution = resolve_exploration_action(
                scene, session, world, normalized,
                raw_player_text=req.text,
                list_scene_ids=list_scene_ids,
                character=character,
                load_scene_fn=load_scene,
            )
        if isinstance(normalized, dict) and compact_segmented:
            meta = normalized.get("metadata")
            if not isinstance(meta, dict):
                meta = {}
                normalized["metadata"] = meta
            meta["turn_segmentation"] = compact_segmented
        embedded_adjudication = (
            resolve_adjudication_query(
                embedded_question_text,
                scene=scene,
                session=session,
                world=world,
                character=character,
                has_active_interaction=bool(
                    str((inspect_interaction_context(session) or {}).get("active_interaction_target_id") or "").strip()
                ),
            )
            if isinstance(embedded_question_text, str) and embedded_question_text.strip()
            else None
        )
        if isinstance(resolution, dict) and (compact_segmented or embedded_adjudication):
            res_meta = resolution.get("metadata")
            if not isinstance(res_meta, dict):
                res_meta = {}
                resolution["metadata"] = res_meta
            if compact_segmented:
                res_meta["turn_segmentation"] = compact_segmented
            if isinstance(embedded_adjudication, dict):
                res_meta["embedded_adjudication"] = {
                    "question": embedded_question_text,
                    "category": embedded_adjudication.get("category"),
                    "answer_type": embedded_adjudication.get("answer_type"),
                    "requires_check": embedded_adjudication.get("requires_check"),
                }
        if _is_offscene_social_target_resolution(resolution):
            trace['gpt_called'] = False
            response_type_contract = _derive_response_type_contract_for_turn(
                session=session,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                normalized_action=normalized,
                resolution=resolution,
                raw_player_text=req.text,
                route_choice=route_choice,
                directed_social_entry=canonical_entry,
            )
            gm = _build_offscene_target_gm_output(resolution)
        elif _is_pending_check_resolution(resolution):
            trace['gpt_called'] = False
            response_type_contract = _derive_response_type_contract_for_turn(
                session=session,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                normalized_action=normalized,
                resolution=resolution,
                raw_player_text=req.text,
                route_choice=route_choice,
                directed_social_entry=canonical_entry,
            )
            gm = _build_check_prompt_gm_output(resolution)
        else:
            scene, session, combat, gm, turn_clue_updates, response_type_contract = _run_resolved_turn_pipeline(
                campaign=campaign,
                character=character,
                session=session,
                world=world,
                combat=combat,
                scene=scene,
                recent_log=recent_log,
                resolution=resolution,
                normalized_action=normalized,
                fallback_user_text=req.text,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                route_choice=route_choice,
                directed_social_entry=canonical_entry,
            )
            authoritative_clue_updates.extend(turn_clue_updates)
        resolution['world_tick_events'] = tick.get('events', [])
    elif gm is None:
        # Final route when no deterministic engine action matched: procedural adjudication vs freeform GPT.
        # Social exchange was already considered via parse_social_intent / dialogue-first / exploration / intent;
        # _prefer_dialogue_over_adjudication only biases ambiguous *unparsed* lines away from adjudication.
        adjudication_text = embedded_question_text or req.text
        adjudication = None
        _interaction_ctx = inspect_interaction_context(session)
        _has_active_interaction = bool(
            str((_interaction_ctx or {}).get("active_interaction_target_id") or "").strip()
        )
        if not _prefer_dialogue_over_adjudication(
            player_text=req.text,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            adjudication_text=adjudication_text,
            has_active_interaction=_has_active_interaction,
            scene=scene,
            session=session,
            world=world,
            canonical_social_entry=canonical_entry,
        ):
            adjudication = resolve_adjudication_query(
                adjudication_text,
                scene=scene,
                session=session,
                world=world,
                character=character,
                has_active_interaction=_has_active_interaction,
            )
        if adjudication is not None:
            routed_via_adjudication = True
            trace['gpt_called'] = False
            trace['canonical_entry_path'] = 'adjudication'
            resolution = {
                'kind': 'adjudication_query',
                'action_id': 'adjudication_query',
                'label': adjudication_text,
                'prompt': adjudication_text,
                'success': None,
                'resolved_transition': False,
                'target_scene_id': None,
                'clue_id': None,
                'discovered_clues': [],
                'world_updates': None,
                'state_changes': {},
                'hint': '',
                'adjudication': {
                    'category': adjudication.get('category'),
                    'answer_type': adjudication.get('answer_type'),
                    'requires_check': adjudication.get('requires_check'),
                    'check_request': adjudication.get('check_request'),
                },
                'requires_check': bool(adjudication.get('requires_check')),
                'check_request': adjudication.get('check_request') if isinstance(adjudication.get('check_request'), dict) else None,
                'metadata': {
                    **({'turn_segmentation': compact_segmented} if compact_segmented else {}),
                    'canonical_entry_path': 'adjudication',
                    'canonical_entry_reason': canonical_entry.get('reason'),
                    'canonical_entry_target_actor_id': canonical_entry.get('target_actor_id'),
                    'intent_route_debug': build_intent_route_debug_adjudication_query(
                        category=adjudication.get('category') if isinstance(adjudication, dict) else None,
                    ),
                },
                'world_tick_events': tick.get('events', []),
            }
            response_type_contract = _derive_response_type_contract_for_turn(
                session=session,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                normalized_action=None,
                resolution=resolution,
                raw_player_text=adjudication_text,
                route_choice=route_choice,
                directed_social_entry=canonical_entry,
            )
            gm = _build_adjudication_gm_output(adjudication)
        else:
            trace['canonical_entry_path'] = 'procedural'
            response_type_contract = _derive_response_type_contract_for_turn(
                session=session,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                normalized_action=None,
                resolution=None,
                raw_player_text=req.text,
                route_choice=route_choice,
                directed_social_entry=canonical_entry,
                attach_to_resolution=False,
            )
            gm = _build_gpt_narration_from_authoritative_state(
                campaign=campaign,
                world=world,
                session=session,
                character=character,
                scene=scene,
                combat=combat,
                recent_log=recent_log,
                user_text=req.text,
                resolution=None,
                scene_runtime=scene_rt,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                route_choice=route_choice,
                directed_social_entry=canonical_entry,
                response_type_contract=response_type_contract,
            )

    _include_res_chat = bool(
        (routed_via_exploration or routed_via_adjudication) and isinstance(resolution, dict)
    )
    if response_type_contract is None:
        response_type_contract = _derive_response_type_contract_for_turn(
            session=session,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            normalized_action=normalized_chat,
            resolution=resolution if isinstance(resolution, dict) else None,
            raw_player_text=req.text,
            route_choice=route_choice,
            directed_social_entry=canonical_entry,
            attach_to_resolution=bool(isinstance(resolution, dict)),
        )
    gm, _narr_consistency_chat = _finalize_player_facing_for_turn(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session,
        world=world,
        scene=scene,
        include_resolution_in_sanitizer=_include_res_chat,
    )
    for _rt in _narr_consistency_chat.get("repaired_discovered_clue_texts") or []:
        if isinstance(_rt, str) and _rt.strip() and _rt.strip() not in authoritative_clue_updates:
            authoritative_clue_updates.append(_rt.strip())

    scene, session, combat, surfaced_clue_telemetry, narration_social_leads = _apply_post_gm_updates(
        gm, scene, session, world, combat, resolution=resolution if isinstance(resolution, dict) else None
    )
    for _txt in narration_social_leads:
        if isinstance(_txt, str) and _txt.strip() and _txt.strip() not in authoritative_clue_updates:
            authoritative_clue_updates.append(_txt.strip())
    remember_recent_contextual_leads(
        session,
        scene['scene']['id'],
        gm.get('player_facing_text') if isinstance(gm.get('player_facing_text'), str) else '',
    )
    context_resolution = (
        resolution
        if isinstance(resolution, dict) and resolution.get('kind') and resolution.get('kind') != 'adjudication_query'
        else None
    )
    _update_interaction_context_after_action(
        session,
        context_resolution,
        scene_changed=scene_before_id != scene['scene']['id'],
        preserve_continuity=bool(
            (implied_context.get("applied") or implied_context.get("interaction_established"))
            and not implied_context.get("commitment_broken")
        ),
    )
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    # Persist world every turn (matches /api/action). Engine paths may mutate event_log / flags
    # without GM-proposed world_updates (e.g. social lead landing).
    save_world(world)

    leads_inspection = _lead_debug_trace_around_authoritative_reconcile(session)

    # Build action pipeline debug for chat (no hidden facts or secrets).
    session['last_action_debug'] = _build_action_debug(
        'chat', req.text, normalized_chat, resolution, response_type_contract
    )
    _merge_emergent_actor_debug_into_action_debug(session)

    clocks_changed = {"time_pressure": time_pressure_after} if clocks_before.get("time_pressure") != time_pressure_after else {}

    # Populate trace for chat success path.
    trace['parsed_intent'] = parsed if parsed is not None else None
    trace['normalized_action'] = (
        {k: normalized_chat[k] for k in ('id', 'label', 'type', 'prompt', 'targetSceneId', 'target_scene_id') if k in (normalized_chat or {})}
        if normalized_chat and isinstance(normalized_chat, dict) else None
    )
    trace['resolution'] = _sanitize_resolution(resolution)
    trace['response_type_contract'] = compact_response_type_contract(response_type_contract)
    trace['scene_after'] = scene['scene']['id']
    deduped_clue_updates: list[str] = []
    for txt in authoritative_clue_updates:
        if isinstance(txt, str) and txt.strip() and txt.strip() not in deduped_clue_updates:
            deduped_clue_updates.append(txt.strip())
    trace['clue_updates'] = deduped_clue_updates
    trace['world_flag_updates'] = _trace_world_updates(gm.get('world_updates'), clocks_changed)
    trace['turn_trace'] = _build_compact_turn_trace(
        source='chat',
        action_type='chat',
        raw_input=trace['raw_input'],
        parsed_intent=parsed if isinstance(parsed, dict) else None,
        segmented_turn=compact_segmented,
        normalized_action=normalized_chat,
        implied_context=implied_context,
        resolution=resolution,
        scene_before=trace['scene_before'],
        scene_after=trace['scene_after'],
        authoritative_clue_updates=deduped_clue_updates,
        clue_presentation_before=clue_presentation_before,
        session=session,
        world=world,
        scene=scene,
        leads_inspection=leads_inspection,
        response_type_contract=response_type_contract,
    )
    _finalize_and_append_trace(session, trace, True, None)

    clear_turn_start_interlocutor_snapshot(session)
    save_session(session)
    save_scene(scene)
    save_combat(combat)
    from game.gm import classify_player_intent

    intent = classify_player_intent(req.text)
    if (routed_via_exploration or routed_via_adjudication) and isinstance(resolution, dict):
        resolution.setdefault('world_tick_events', tick.get('events', []))

    gm_prompt_summary: dict = {
        'scene_id': scene['scene'].get('id'),
        'scene_mode': scene['scene'].get('mode'),
        'response_mode': session.get('response_mode', 'standard'),
        'response_type_contract': compact_response_type_contract(response_type_contract),
    }
    if routed_via_exploration and isinstance(resolution, dict):
        gm_prompt_summary['exploration'] = {
            'action_id': resolution.get('action_id'),
            'kind': resolution.get('kind'),
            'scene_transition_occurred': bool(resolution.get('resolved_transition')),
        }
    if routed_via_adjudication and isinstance(resolution, dict):
        gm_prompt_summary['adjudication'] = dict(resolution.get('adjudication') or {})

    append_log(
        {
            'timestamp': utc_iso_now(),
            'request': {'chat': req.text},
            'resolution': resolution,
            'gm_output': gm,
            'log_meta': {
                'player_input': req.text,
                'intent_classification': intent,
                'gm_prompt_context_summary': gm_prompt_summary,
                'gm_raw_output_meta': {'has_output': True},
                'approved_state_updates': {
                    'scene_update': gm.get('scene_update'),
                    'world_updates': gm.get('world_updates'),
                    'new_scene_draft': gm.get('new_scene_draft'),
                },
                'rejected_state_updates': [],
                'discovered_clues_added': deduped_clue_updates,
                'surfaced_clues_in_narration_non_authoritative': surfaced_clue_telemetry,
                'clocks_changed': clocks_changed,
                'response_type_contract': compact_response_type_contract(response_type_contract),
            },
        }
    )
    return _build_turn_response_payload(
        gm=gm,
        resolution=resolution if (routed_via_exploration or routed_via_adjudication) and isinstance(resolution, dict) else None,
        include_resolution=bool((routed_via_exploration or routed_via_adjudication) and isinstance(resolution, dict)),
    )


from game.api_turn_support import (
    AUTHORITATIVE_TURN_STAGE_ORDER,
    _build_action_debug,
    _build_compact_turn_trace,
    _build_turn_response_payload,
    _compact_affordances_for_trace,
    _compact_segmented_turn,
    _derive_affordances_from_authoritative_state,
    _diff_clue_presentation,
    _finalize_and_append_trace,
    _finalize_player_facing_for_turn,
    _lead_debug_trace_around_authoritative_reconcile,
    _merge_emergent_actor_debug_into_action_debug,
    _sanitize_resolution,
    _session_ongoing_social_exchange,
    _snapshot_known_clue_presentations,
    _strip_internal_gm_keys,
    _trace_resolution_path,
    _trace_world_updates,
)
