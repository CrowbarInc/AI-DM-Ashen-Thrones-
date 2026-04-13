"""Deterministic exploration action resolution: runs before GPT narration for scene_transition, observe, investigate, interact, custom."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Literal, Optional

from game.models import ExplorationEngineResult
from game.utils import slugify
from game.storage import get_scene_runtime, add_pending_lead, is_interactable_resolved, is_target_searched
from game.clues import _canonical_registry_lead_id, apply_authoritative_clue_discovery, set_clue_presentation
from game.leads import (
    LeadLifecycle,
    LeadStatus,
    commit_session_lead_with_context,
    get_lead,
    is_lead_terminal,
    normalize_lead,
    obsolete_session_lead,
    obsolete_superseded_lead,
    resolve_session_lead,
)
from game.scene_graph import build_scene_graph, is_transition_valid
from game.skill_checks import resolve_skill_check, should_trigger_check
from game.social import SOCIAL_KINDS as _SOCIAL_ENGINE_KINDS
from game.human_adjacent_focus import enrich_exploration_resolution_for_human_adjacent_focus
from game.scene_destination_binding import (
    evaluate_destination_semantic_compatibility,
    reconcile_scene_transition_destination,
)


EXPLORATION_KINDS = ("scene_transition", "travel", "observe", "investigate", "interact", "custom", "discover_clue", "already_searched")


def _infer_transition_target_from_prompt(
    prompt: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: set[str],
) -> Optional[str]:
    """Best-effort deterministic destination inference from prompt text and exits.

    Mixed-turn *declared* movement uses stricter unique matching in
    :func:`game.intent_parser.maybe_build_declared_travel_action` (ambiguous exits stay unresolved).
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    prompt_low = prompt.strip().lower()
    prompt_slug = slugify(prompt_low)

    for ex in exits or []:
        if not isinstance(ex, dict):
            continue
        label = str(ex.get("label") or "").strip()
        target = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not target:
            continue
        label_low = label.lower()
        label_slug = slugify(label_low)
        target_slug = slugify(target)
        if (
            (label_low and label_low in prompt_low)
            or (label_low and prompt_low in label_low)
            or (label_slug and label_slug in prompt_slug)
            or (target_slug and target_slug in prompt_slug)
        ):
            if target in known_scene_ids:
                return target
    return None


def _build_skill_check_context(
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    normalized_action: Dict[str, Any],
    character: Optional[Dict[str, Any]],
    interactable: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build context for should_trigger_check and resolve_skill_check."""
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    scene_runtime = get_scene_runtime(session, scene_id) if scene_id else {}
    action_id = str(normalized_action.get("id") or "").strip() or "action"
    character_id = (character or {}).get("id", "")
    turn_counter = session.get("turn_counter", 0)
    return {
        "engine": "exploration",
        "action": normalized_action,
        "scene": scene_envelope or scene,
        "session": session,
        "interactable": interactable,
        "scene_runtime": scene_runtime,
        "seed_parts": [turn_counter, scene_id, action_id, character_id, "explore"],
    }


def _get_skill_check_config(
    scene: Dict[str, Any],
    action_type: str,
    action_id: str,
    interactable: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Find skill_check config from interactable, matched scene action, or scene defaults.
    Returns dict with skill_id, dc, on_success (optional), on_failure (optional) or None.
    """
    if interactable and isinstance(interactable.get("skill_check"), dict):
        sc = interactable["skill_check"]
        if sc.get("skill_id") and sc.get("dc") is not None:
            return sc

    for raw in scene.get("actions") or scene.get("suggested_actions") or []:
        if not isinstance(raw, dict):
            continue
        raw_id = str(raw.get("id") or raw.get("action_id") or "").strip()
        if raw_id and raw_id == action_id and isinstance(raw.get("skill_check"), dict):
            sc = raw["skill_check"]
            if sc.get("skill_id") and sc.get("dc") is not None:
                return sc

    defaults = scene.get("skill_check_defaults")
    if isinstance(defaults, dict) and action_type in ("observe", "investigate", "interact"):
        sc = defaults.get(action_type)
        if isinstance(sc, dict) and sc.get("skill_id") and sc.get("dc") is not None:
            return sc
    return None


def parse_exploration_intent(
    text: str,
    scene_envelope: Dict[str, Any],
    session: Optional[Dict[str, Any]] = None,
    world: Optional[Dict[str, Any]] = None,
    segmented_turn: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Detect exploration patterns in free text. Returns a raw dict compatible with normalize_scene_action, or None.

    Delegates to intent_parser.parse_freeform_to_action for deterministic parsing with scene context.
    When ``session`` is set, explicit pursuit phrases may attach authoritative follow-lead metadata.
    """
    from game.intent_parser import parse_freeform_to_action

    result = parse_freeform_to_action(
        text,
        scene_envelope,
        session=session,
        world=world,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
    )
    # Exclude combat-only intents (attack) from exploration pipeline; caller handles routing
    if result and (result.get("type") or "").strip().lower() == "attack":
        return None  # API chat will route attack via combat when in_combat
    return result


def resolve_exploration_action(
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    normalized_action: Dict[str, Any],
    raw_player_text: str | None = None,
    list_scene_ids: Callable[[], List[str]] | None = None,
    character: Optional[Dict[str, Any]] = None,
    scene_graph: Optional[Dict[str, set]] = None,
    load_scene_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Produce a structured resolution object for the GM prompt. No side effects; caller performs activate_scene etc.

    When character is provided and a skill_check is configured (on action, interactable, or scene defaults),
    the engine rolls the check and attaches skill_check + success to the result. GPT must narrate the
    already-resolved outcome.

    Returns:
        kind: one of scene_transition, observe, investigate, interact, custom, discover_clue
        resolved_transition: True only when type is scene_transition and target is known
        skill_check: {roll, modifier, total, dc, success} when a check was run
        success: True/False when skill_check ran; None otherwise
    """
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    action_type = (normalized_action.get("type") or "custom").strip().lower()
    if action_type not in EXPLORATION_KINDS:
        action_type = "custom"
    label = str(normalized_action.get("label") or "").strip() or "Action"
    prompt = str(normalized_action.get("prompt") or raw_player_text or label).strip() or label
    target_scene_id = normalized_action.get("targetSceneId") or normalized_action.get("target_scene_id")
    if target_scene_id is not None:
        target_scene_id = str(target_scene_id).strip() or None
    action_id = str(normalized_action.get("id") or "").strip() or "action"

    known_ids: List[str] = []
    if list_scene_ids is not None:
        known_ids = list(list_scene_ids())
    known_set = set(known_ids)

    # Build scene graph if not provided (for transition validation)
    if scene_graph is None and list_scene_ids is not None and load_scene_fn is not None:
        scene_graph = build_scene_graph(list_scene_ids, load_scene_fn)

    current_scene_id = str(scene.get("id") or "").strip()
    transition_candidate = action_type in {"scene_transition", "travel"}
    binding_meta_subset: Dict[str, Any] = {}
    blocked_incompatible_scene_transition = False
    if transition_candidate:
        proposed_target = target_scene_id
        inferred_target: Optional[str] = None
        if not target_scene_id:
            inferred_target = _infer_transition_target_from_prompt(
                prompt, scene.get("exits") or [], known_set
            )
        rebind = reconcile_scene_transition_destination(
            normalized_action=normalized_action,
            prompt=prompt,
            raw_player_text=raw_player_text,
            exits=scene.get("exits") or [],
            known_scene_ids=known_set,
            proposed_target_scene_id=proposed_target,
            inferred_target_scene_id=inferred_target,
        )
        target_scene_id = str(rebind.get("effective_target_scene_id") or "").strip() or None
        binding_meta_subset = {
            k: rebind[k]
            for k in (
                "destination_binding_source",
                "destination_binding_conflict",
                "destination_binding_conflict_candidates",
                "destination_binding_resolution_reason",
                "destination_semantic_kind",
            )
            if k in rebind
        }
        if target_scene_id:
            compat = evaluate_destination_semantic_compatibility(
                normalized_action=normalized_action,
                raw_player_text=raw_player_text,
                prompt=prompt,
                effective_target_scene_id=target_scene_id,
                destination_semantic_kind=str(rebind.get("destination_semantic_kind") or ""),
                exits=scene.get("exits") or [],
                load_scene_fn=load_scene_fn,
            )
            clear_t = bool(compat.pop("compatibility_clear_target", False))
            binding_meta_subset.update(compat)
            if clear_t:
                blocked_incompatible_scene_transition = True
                target_scene_id = None

    resolved_transition = False
    if transition_candidate and target_scene_id and target_scene_id in known_set:
        if scene_graph is not None:
            resolved_transition = is_transition_valid(
                current_scene_id,
                target_scene_id,
                scene_graph,
                session=session,
                known_scene_ids=known_set,
            )
        else:
            resolved_transition = True  # backward compat: no graph = allow if known

    # Check interactables when player investigates: match prompt to interactable id
    if action_type == "investigate":
        interactables = scene.get("interactables") or []
        prompt_slug = slugify(prompt)
        for i in interactables:
            if not isinstance(i, dict):
                continue
            i_type = (i.get("type") or "").strip().lower()
            if i_type != "investigate":
                continue
            reveals_clue = i.get("reveals_clue")
            if not reveals_clue or not isinstance(reveals_clue, str):
                continue
            i_id = str(i.get("id") or "").strip()
            if not i_id:
                continue
            i_id_slug = slugify(i_id)
            if i_id_slug and i_id_slug in prompt_slug:
                scene_id = scene.get("id") or ""
                if scene_id and is_interactable_resolved(session, scene_id, i_id):
                    result = ExplorationEngineResult(
                        kind="already_searched",
                        action_id=action_id,
                        label=label,
                        prompt=prompt,
                        success=False,
                        resolved_transition=False,
                        target_scene_id=None,
                        clue_id=None,
                        discovered_clues=[],
                        world_updates=None,
                        state_changes={"already_searched": True, "interactable_id": i_id},
                        hint=f"Player has already searched [{i_id}]. Narrate that they find nothing new.",
                        interactable_id=i_id,
                        metadata={},
                    )
                    return result.to_dict()
                # Skill check authority: engine decides when to roll
                ctx = _build_skill_check_context(scene_envelope, session, normalized_action, character, interactable=i)
                ctx["scene"] = scene_envelope or {"scene": scene}
                decision = should_trigger_check(normalized_action, ctx)
                check_result: Optional[Dict[str, Any]] = None
                if decision.get("requires_check") and character and decision.get("skill") and decision.get("difficulty") is not None:
                    check_result = resolve_skill_check(
                        decision["skill"],
                        decision["difficulty"],
                        character,
                        ctx,
                    )
                    if not check_result["success"]:
                        skill_config = _get_skill_check_config(scene, "investigate", action_id, interactable=i)
                        on_fail = (skill_config or {}).get("on_failure") or {}
                        hint = str(on_fail.get("hint") or "").strip()
                        if not hint:
                            hint = f"Player investigated [{i_id}] but failed the check (d20={check_result['roll']}+{check_result['modifier']}={check_result['total']} vs DC {check_result.get('difficulty', check_result.get('dc', 10))}). Narrate the failed attempt—they notice nothing decisive."
                        wu = on_fail.get("world_updates") if isinstance(on_fail.get("world_updates"), dict) else None
                        result = ExplorationEngineResult(
                            kind="investigate",
                            action_id=action_id,
                            label=label,
                            prompt=prompt,
                            success=False,
                            resolved_transition=False,
                            target_scene_id=None,
                            clue_id=None,
                            discovered_clues=[],
                            world_updates=wu,
                            state_changes={"skill_check_failed": True, "interactable_id": i_id},
                            hint=hint,
                            metadata={"skill_check": check_result},
                        )
                        d = result.to_dict()
                        d["skill_check"] = check_result
                        return d
                    # Success: check_result already set; use it for metadata below
                # Resolve clue text from discoverable_clues
                clue_text = reveals_clue
                discoverable_raw = scene.get("discoverable_clues") or []
                for c in discoverable_raw:
                    rec = c if isinstance(c, dict) else {"id": slugify(str(c)), "text": str(c)}
                    cid = str(rec.get("id") or slugify(rec.get("text", ""))).strip()
                    if cid and slugify(cid) == slugify(reveals_clue):
                        clue_text = str(rec.get("text") or reveals_clue).strip() or reveals_clue
                        break
                wu = i.get("world_updates_on_discover")
                world_updates_val = wu if isinstance(wu, dict) and wu else None
                metadata: Dict[str, Any] = {}
                if check_result:
                    metadata["skill_check"] = check_result
                result = ExplorationEngineResult(
                    kind="discover_clue",
                    action_id=action_id,
                    label=label,
                    prompt=prompt,
                    success=True,
                    resolved_transition=False,
                    target_scene_id=None,
                    clue_id=reveals_clue,
                    discovered_clues=[clue_text],
                    world_updates=world_updates_val,
                    state_changes={"clue_revealed": True, "interactable_id": i_id},
                    hint=f"Player investigated [{i_id}] and discovered clue [{reveals_clue}]. Narrate the discovery and its significance.",
                    interactable_id=i_id,
                    clue_text=clue_text,
                    metadata=metadata,
                )
                d = result.to_dict()
                if metadata.get("skill_check"):
                    d["skill_check"] = metadata["skill_check"]
                return d

        # No interactable matched; check if this generic investigate target was already searched
        scene_id = scene.get("id") or ""
        if scene_id and is_target_searched(session, scene_id, action_id):
            result = ExplorationEngineResult(
                kind="already_searched",
                action_id=action_id,
                label=label,
                prompt=prompt,
                success=False,
                resolved_transition=False,
                target_scene_id=None,
                clue_id=None,
                discovered_clues=[],
                world_updates=None,
                state_changes={"already_searched": True},
                hint="Player has already searched this. Narrate that they find nothing new.",
                metadata={},
            )
            return result.to_dict()

    hint: str
    if transition_candidate:
        if resolved_transition:
            hint = f"Player has moved to scene {target_scene_id}. Narrate arrival and what they see there."
        elif blocked_incompatible_scene_transition:
            hint = (
                "Player declared a specific destination that does not match the resolved scene transition "
                "(semantic mismatch). Narrate the mismatch or blocked movement without changing location."
            )
        elif target_scene_id and target_scene_id in known_set:
            hint = (
                f"Player attempted to travel to {target_scene_id}, but that path is not reachable from here. "
                "Narrate blocked movement, attempted path, or unresolved travel—do not imply arrival."
            )
        else:
            hint = "Player expressed travel intent; target scene not resolved. Narrate based on current scene and intent."
    elif action_type == "observe":
        hint = "Player is focusing on observing the current scene. Narrate what stands out or what careful observation reveals—avoid repeating the same summary."
        _am_obs = normalized_action.get("metadata")
        if isinstance(_am_obs, dict) and _am_obs.get("passive_interruption_wait") is True:
            hint = (
                "The player waits out a disturbance or distraction. Narrate the interruption easing and the scene settling; "
                "do not force a fresh in-character reply from a prior conversational partner unless the fiction already queued one."
            )
    elif action_type == "investigate":
        hint = "Player is investigating or seeking clues. Narrate what deeper scrutiny reveals; advance discovery if appropriate."
    elif action_type == "interact":
        hint = "Player is attempting social interaction or probing NPCs. Narrate the encounter or response."
    else:
        hint = "Player took a custom exploration action. Narrate outcome without simply restating the scene summary."

    # Engine-level world updates: from exit (scene_transition) or scene.actions
    world_updates: Dict[str, Any] = {}
    if resolved_transition and target_scene_id:
        for ex in scene.get("exits") or []:
            if isinstance(ex, dict):
                tid = (ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
                if tid == target_scene_id:
                    wu = ex.get("world_updates_on_transition")
                    if isinstance(wu, dict) and wu:
                        world_updates = _merge_world_updates(world_updates, wu)
                    break
    for raw in scene.get("actions") or scene.get("suggested_actions") or []:
        if not isinstance(raw, dict):
            continue
        raw_id = str(raw.get("id") or raw.get("action_id") or "").strip()
        if raw_id and raw_id == action_id:
            wu = raw.get("world_updates_on_use")
            if isinstance(wu, dict) and wu:
                world_updates = _merge_world_updates(world_updates, wu)
            break

    success_val: Optional[bool] = None
    skill_check_result: Optional[Dict[str, Any]] = None
    state_changes: Dict[str, Any] = {}
    if transition_candidate:
        success_val = resolved_transition
    else:
        # Skill check authority: engine decides when to roll (observe/investigate/interact, non-interactable path)
        ctx = _build_skill_check_context(scene_envelope, session, normalized_action, character, interactable=None)
        ctx["scene"] = scene_envelope or {"scene": scene}
        decision = should_trigger_check(normalized_action, ctx)
        if decision.get("requires_check") and character and decision.get("skill") and decision.get("difficulty") is not None:
            skill_check_result = resolve_skill_check(
                decision["skill"],
                decision["difficulty"],
                character,
                ctx,
            )
            success_val = skill_check_result["success"]
            skill_config = _get_skill_check_config(scene, action_type, action_id, interactable=None)
            on_success = (skill_config or {}).get("on_success") or {}
            on_failure = (skill_config or {}).get("on_failure") or {}
            branch = on_success if success_val else on_failure
            custom_hint = str(branch.get("hint") or "").strip()
            if custom_hint:
                hint = custom_hint
            elif not success_val:
                dc = decision["difficulty"]
                hint = (
                    f"Player action failed the check (d20={skill_check_result['roll']}+{skill_check_result['modifier']}"
                    f"={skill_check_result['total']} vs DC {dc}). Narrate the failed attempt and its consequence."
                )
            branch_wu = branch.get("world_updates") if isinstance(branch.get("world_updates"), dict) else None
            if branch_wu:
                world_updates = _merge_world_updates(world_updates, branch_wu)
            if not success_val:
                state_changes["skill_check_failed"] = True

    state_changes_final: Dict[str, Any] = {}
    if resolved_transition and target_scene_id:
        state_changes_final["scene_changed"] = True
        state_changes_final["scene_transition_occurred"] = True
        state_changes_final["arrived_at_scene"] = True
        state_changes_final["new_scene_context_available"] = True
    for k, v in state_changes.items():
        state_changes_final[k] = v

    res_metadata: Dict[str, Any] = {}
    am = normalized_action.get("metadata")
    if isinstance(am, dict):
        if transition_candidate:
            res_metadata.update(am)
        else:
            if am.get("passive_interruption_wait") is True:
                res_metadata["passive_interruption_wait"] = True
            for key in (
                "parser_lane",
                "human_adjacent_intent_family",
                "human_adjacent_phrase",
                "implicit_focus_resolution",
                "implicit_focus_target_id",
                "implicit_focus_anchor_fact",
                "nearby_group_continuity_carryover",
            ):
                if key in am:
                    res_metadata[key] = am[key]
    if skill_check_result:
        res_metadata["skill_check"] = skill_check_result
    if transition_candidate and binding_meta_subset:
        res_metadata.update(binding_meta_subset)

    hint, res_metadata = enrich_exploration_resolution_for_human_adjacent_focus(
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else {"scene": scene},
        session=session,
        world=world,
        normalized_action=normalized_action,
        raw_player_text=raw_player_text,
        prompt=prompt,
        action_type=action_type,
        hint=hint,
        res_metadata=res_metadata,
        transition_candidate=transition_candidate,
    )

    result = ExplorationEngineResult(
        kind=action_type,
        action_id=action_id,
        label=label,
        prompt=prompt,
        success=success_val,
        resolved_transition=resolved_transition,
        target_scene_id=target_scene_id if resolved_transition else None,
        clue_id=None,
        discovered_clues=[],
        world_updates=world_updates if world_updates else None,
        state_changes=state_changes_final,
        hint=hint,
        metadata=res_metadata,
    )
    d = result.to_dict()
    if skill_check_result:
        d["skill_check"] = skill_check_result
    return d


def _follow_lead_commitment_snapshot(row: Dict[str, Any] | None) -> tuple[Any, ...] | None:
    if not row:
        return None
    return (
        row.get("lifecycle"),
        row.get("status"),
        row.get("committed_at_turn"),
        row.get("commitment_source"),
        row.get("commitment_strength"),
    )


# Canonical resolution_type when a pursued destination-scene lead pays off via arrival (see
# :func:`maybe_finalize_pursued_lead_destination_payoff_after_scene_transition`).
RESOLUTION_TYPE_REACHED_DESTINATION = "reached_destination"

# Canonical resolution_type when parser-built NPC-target pursuit pays off via grounded contact (see
# :func:`maybe_finalize_pursued_lead_npc_contact_payoff`).
RESOLUTION_TYPE_REACHED_NPC = "reached_npc"

# Session key: parser-built NPC-target pursuit context after a successful follow transition (explicit_player_pursuit).
_NPC_PURSUIT_CONTACT_CONTEXT_KEY = "_npc_pursuit_contact_context"
NPC_PURSUIT_CONTACT_SESSION_KEY = _NPC_PURSUIT_CONTACT_CONTEXT_KEY


def _effective_follow_action_target_scene_id(normalized_action: Dict[str, Any]) -> str:
    """Destination encoded on the follow/pursuit action (metadata or top-level)."""
    meta = normalized_action.get("metadata")
    if isinstance(meta, dict):
        for key in ("target_scene_id", "targetSceneId"):
            v = meta.get(key)
            if v is not None and str(v).strip():
                return str(v).strip()
    for key in ("target_scene_id", "targetSceneId"):
        v = normalized_action.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _merge_action_resolution_metadata(
    normalized_action: Dict[str, Any] | None, resolution: Dict[str, Any] | None
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for src in (normalized_action, resolution):
        if not isinstance(src, dict):
            continue
        md = src.get("metadata")
        if isinstance(md, dict):
            out.update(md)
    return out


def _effective_parser_npc_pursuit_metadata(
    session: Dict[str, Any],
    normalized_action: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    """Metadata for parser-built NPC-target pursuit (explicit_player_pursuit), merged with session context."""
    merged = _merge_action_resolution_metadata(normalized_action, resolution)
    ctx_raw = session.get(_NPC_PURSUIT_CONTACT_CONTEXT_KEY) if isinstance(session, dict) else None
    if isinstance(ctx_raw, dict):
        ctx = dict(ctx_raw)
        if str(ctx.get("commitment_source") or "").strip() == "explicit_player_pursuit":
            aid_c = str(ctx.get("authoritative_lead_id") or "").strip()
            if aid_c and not str(merged.get("authoritative_lead_id") or "").strip():
                merged = {**ctx, **merged}
    if str(merged.get("target_kind") or "").strip().lower() != "npc":
        return None
    tn = str(merged.get("target_npc_id") or "").strip()
    if not tn:
        return None
    aid = str(merged.get("authoritative_lead_id") or "").strip()
    if not aid:
        return None
    if str(merged.get("commitment_source") or "").strip() != "explicit_player_pursuit":
        return None
    return merged


def _grounded_respondent_npc_id(resolution: Dict[str, Any]) -> str:
    """Authoritative NPC id for who was reached in social resolution (no prose inference)."""
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if soc.get("offscene_target"):
        return ""
    if soc.get("reply_speaker_grounding_neutral_bridge"):
        return ""
    gs = str(soc.get("grounded_speaker_id") or "").strip()
    if gs:
        return gs
    if soc.get("target_resolved") is True:
        return str(soc.get("npc_id") or "").strip()
    return ""


def clear_npc_pursuit_contact_context_if_lead(session: Dict[str, Any], authoritative_lead_id: Any) -> None:
    """Drop session NPC pursuit context when it matches the given lead id."""
    if not isinstance(session, dict):
        return
    ctx = session.get(_NPC_PURSUIT_CONTACT_CONTEXT_KEY)
    if not isinstance(ctx, dict):
        return
    if str(ctx.get("authoritative_lead_id") or "").strip() == str(authoritative_lead_id or "").strip():
        session[_NPC_PURSUIT_CONTACT_CONTEXT_KEY] = None


def maybe_finalize_pursued_lead_npc_contact_payoff(
    session: Dict[str, Any],
    resolution: Dict[str, Any],
    normalized_action: Dict[str, Any] | None,
) -> None:
    """Resolve an NPC-target pursued lead when grounded social resolution confirms contact with ``target_npc_id``.

    Restricted to parser-built pursuit (``commitment_source`` ``explicit_player_pursuit`` and ``target_kind`` ``npc``).
    Does not run on scene arrival alone — caller should invoke after social engine resolution.
    """
    if not isinstance(session, dict) or not isinstance(resolution, dict):
        return
    res_kind = str(resolution.get("kind") or "").strip().lower()
    if res_kind not in _SOCIAL_ENGINE_KINDS:
        return
    meta = _effective_parser_npc_pursuit_metadata(session, normalized_action, resolution)
    if not meta:
        return
    aid = str(meta.get("authoritative_lead_id") or "").strip()
    target_npc = str(meta.get("target_npc_id") or "").strip()
    if not aid or not target_npc:
        return
    if resolution.get("success") is False:
        return

    grounded = _grounded_respondent_npc_id(resolution)
    if not grounded or grounded != target_npc:
        return

    row = get_lead(session, aid)
    if row is None or is_lead_terminal(row):
        return
    snap = normalize_lead(dict(row))
    if snap.get("lifecycle") != LeadLifecycle.COMMITTED.value:
        return
    if snap.get("status") != LeadStatus.PURSUED.value:
        return

    finalize_followed_lead(
        session,
        aid,
        terminal_mode="resolved",
        turn=session.get("turn_counter"),
        resolution_type=RESOLUTION_TYPE_REACHED_NPC,
        resolution_summary="Reached the pursued contact.",
    )
    clear_npc_pursuit_contact_context_if_lead(session, aid)


def maybe_finalize_pursued_lead_destination_payoff_after_scene_transition(
    session: Dict[str, Any],
    resolution: Dict[str, Any],
    normalized_action: Dict[str, Any] | None,
    *,
    target_scene_id: str,
) -> None:
    """If a scene transition is the grounded payoff of a pursued destination lead, resolve that lead.

    Runs only after :func:`apply_follow_lead_commitment_after_resolved_scene_transition` so pursuit
    commitment is already applied. Uses ``metadata.authoritative_lead_id`` (or equivalent) on the
    transition action — no guessing. Requires the action to encode the same destination as
    ``target_scene_id`` (affordance metadata or top-level target id, including qualified pursuit),
    and the registry row to list that scene in ``related_scene_ids`` (engine signal destination).

    Does not run on generic travel without a matching encoded destination on the action.
    Skips NPC-target pursuit (metadata ``target_kind`` ``npc``): arrival at a scene is not the
    same as reaching the pursued NPC.
    """
    if not isinstance(session, dict) or not isinstance(resolution, dict):
        return
    if not isinstance(normalized_action, dict):
        return
    if str(normalized_action.get("type") or "").strip().lower() != "scene_transition":
        return
    if str(resolution.get("kind") or "").strip().lower() != "scene_transition":
        return
    if resolution.get("success") is False:
        return
    if not resolution.get("resolved_transition"):
        return
    tid = str(target_scene_id or "").strip()
    if not tid or str(resolution.get("target_scene_id") or "").strip() != tid:
        return

    meta_raw = normalized_action.get("metadata")
    meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}
    aid = str(meta.get("authoritative_lead_id") or "").strip() or None
    if not aid:
        return
    # NPC-target pursuit: travel only reaches a scene where the NPC may be — not destination payoff.
    if str(meta.get("target_kind") or "").strip().lower() == "npc":
        return

    encoded = _effective_follow_action_target_scene_id(normalized_action)
    if not encoded or encoded != tid:
        return

    rmeta = resolution.get("metadata")
    if isinstance(rmeta, dict):
        cid = rmeta.get("committed_lead_id")
        if cid is not None and str(cid).strip() and str(cid).strip() != aid:
            return

    row = get_lead(session, aid)
    if row is None or is_lead_terminal(row):
        return

    snap = normalize_lead(dict(row))
    scenes = [str(x).strip() for x in (snap.get("related_scene_ids") or []) if str(x).strip()]
    if tid not in scenes:
        return

    if snap.get("lifecycle") != LeadLifecycle.COMMITTED.value:
        return
    if snap.get("status") != LeadStatus.PURSUED.value:
        return

    finalize_followed_lead(
        session,
        aid,
        terminal_mode="resolved",
        turn=session.get("turn_counter"),
        resolution_type=RESOLUTION_TYPE_REACHED_DESTINATION,
        resolution_summary="Arrived at the lead's destination.",
    )


def finalize_followed_lead(
    session: Dict[str, Any],
    authoritative_lead_id: Any,
    *,
    terminal_mode: Literal["resolved", "obsolete"] | str,
    turn: Any = None,
    resolution_type: Any = None,
    resolution_summary: Any = "",
    obsolete_reason: Any = None,
    consequence_ids: Any | None = None,
) -> Dict[str, Any]:
    """End an authoritative lead after payoff: resolve or obsolete via session registry wrappers.

    No automatic lifecycle changes from travel or follow success — call this only when fiction delivers closure.

    Raises :class:`ValueError` for blank ``authoritative_lead_id``, unknown ``terminal_mode``, or missing registry row
    (same as :func:`resolve_session_lead` / :func:`obsolete_session_lead`). ``resolution_type`` is required when
    ``terminal_mode`` is ``resolved``; ``obsolete_reason`` when ``obsolete``.
    """
    if not isinstance(session, dict):
        raise ValueError("session is required")
    mode = str(terminal_mode or "").strip().lower()
    if mode == "resolved":
        return resolve_session_lead(
            session,
            authoritative_lead_id,
            resolution_type=resolution_type,
            resolution_summary=resolution_summary,
            turn=turn,
            consequence_ids=consequence_ids,
        )
    if mode == "obsolete":
        return obsolete_session_lead(
            session,
            authoritative_lead_id,
            obsolete_reason=obsolete_reason,
            turn=turn,
            consequence_ids=consequence_ids,
        )
    raise ValueError("terminal_mode must be 'resolved' or 'obsolete'")


def apply_follow_lead_commitment_after_resolved_scene_transition(
    session: Dict[str, Any],
    resolution: Dict[str, Any],
    normalized_action: Dict[str, Any] | None,
    *,
    target_scene_id: str,
) -> None:
    """Commit authoritative lead when a successful scene_transition used follow-lead metadata.

    Call only after :func:`game.api._apply_authoritative_scene_transition` (or equivalent) so ``session``
    is the post-transition authoritative dict. Requires ``metadata.authoritative_lead_id`` on the action;
    generic transitions without that key are ignored (legacy-safe).
    """
    if not isinstance(session, dict) or not isinstance(resolution, dict):
        return
    if not isinstance(normalized_action, dict):
        return
    if str(normalized_action.get("type") or "").strip().lower() != "scene_transition":
        return
    if str(resolution.get("kind") or "").strip().lower() != "scene_transition":
        return
    if not resolution.get("resolved_transition"):
        return
    tid = str(target_scene_id or "").strip()
    if not tid or str(resolution.get("target_scene_id") or "").strip() != tid:
        return
    meta_raw = normalized_action.get("metadata")
    meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}
    lead_id = str(meta.get("authoritative_lead_id") or "").strip() or None
    if not lead_id:
        return

    commitment_source = meta.get("commitment_source")
    commitment_strength = meta.get("commitment_strength")

    row_before = get_lead(session, lead_id)
    if row_before is None:
        return
    snap_before = _follow_lead_commitment_snapshot(row_before)
    commit_session_lead_with_context(
        session,
        lead_id,
        turn=int(session.get("turn_counter", 0) or 0),
        commitment_source=commitment_source,
        commitment_strength=commitment_strength,
    )
    row_after = get_lead(session, lead_id)
    snap_after = _follow_lead_commitment_snapshot(row_after)

    rmeta = resolution.get("metadata")
    if not isinstance(rmeta, dict):
        rmeta = {}
        resolution["metadata"] = rmeta
    rmeta["committed_lead_id"] = lead_id
    if commitment_source is not None:
        rmeta["commitment_source"] = commitment_source
    rmeta["commitment_applied"] = bool(
        snap_before is not None and snap_after is not None and snap_before != snap_after
    )
    # Parser-built NPC-target travel: remember contact target for payoff on a later grounded social turn.
    if str(meta.get("commitment_source") or "").strip() == "explicit_player_pursuit":
        if str(meta.get("target_kind") or "").strip().lower() == "npc":
            tn = str(meta.get("target_npc_id") or "").strip()
            if tn:
                session[_NPC_PURSUIT_CONTACT_CONTEXT_KEY] = {
                    "authoritative_lead_id": lead_id,
                    "target_kind": "npc",
                    "target_npc_id": tn,
                    "destination_scene_id": str(meta.get("destination_scene_id") or "").strip() or None,
                    "commitment_source": "explicit_player_pursuit",
                    "commitment_strength": meta.get("commitment_strength"),
                }
        else:
            session[_NPC_PURSUIT_CONTACT_CONTEXT_KEY] = None


def _merge_world_updates(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    """Merge extra world_updates into base. set_flags overwrite; increment_counters/advance_clocks add."""
    out = dict(base)
    for key in ("set_flags", "increment_counters", "advance_clocks"):
        if key not in extra or not isinstance(extra[key], dict):
            continue
        out.setdefault(key, {})
        if not isinstance(out[key], dict):
            out[key] = {}
        for k, v in extra[key].items():
            if isinstance(k, str) and k.strip() and not k.startswith("_"):
                if key == "set_flags":
                    out[key][k] = v
                elif key == "increment_counters":
                    out[key][k] = out[key].get(k, 0) + (int(v) if v is not None else 1)
                elif key == "advance_clocks":
                    out[key][k] = out[key].get(k, 0) + (int(v) if v is not None else 1)
    return out


def process_investigation_discovery(
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    list_scene_ids: Callable[[], List[str]] | None = None,
    world: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """For investigate actions: reveal the next undiscovered clue if investigation depth increases.
    Mutates session (discovered_clues, pending_leads). Returns list of newly revealed clue records.
    """
    from game.gm import normalize_clue_record  # avoid circular import

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = scene.get("id")
    if not scene_id:
        return []

    discoverable_raw = scene.get("discoverable_clues") or []
    if not discoverable_raw:
        return []

    rt = get_scene_runtime(session, scene_id)
    discovered_texts = {s for s in (rt.get("discovered_clues") or []) if isinstance(s, str)}
    discovered_set = {t.strip().lower() for t in discovered_texts if t}

    normalized = [normalize_clue_record(c) for c in discoverable_raw]
    # ``normalize_clue_record`` drops authoring-only keys; keep explicit supersession targets by normalized id.
    supersede_by_clue_id: Dict[str, str] = {}
    for raw, nrec in zip(discoverable_raw, normalized):
        if isinstance(raw, dict):
            sup = str(raw.get("supersedes_lead_id") or "").strip()
            rid = str(nrec.get("id") or "").strip()
            if rid and sup:
                supersede_by_clue_id[rid] = sup

    for rec in normalized:
        text = rec.get("text") or ""
        if not text.strip():
            continue
        text_key = text.strip().lower()
        if text_key in discovered_set:
            continue
        # Next undiscovered clue: reveal it once through the shared clue gateway.
        clue_id = str(rec.get("id", "") or "").strip() or None
        added_texts = apply_authoritative_clue_discovery(
            session,
            scene_id,
            clue_id=clue_id,
            clue_text=text.strip(),
            discovered_clues=[text.strip()],
            world=world,
            structured_clue=rec,
        )
        if added_texts:
            lead: Dict[str, Any] = {"clue_id": rec.get("id", ""), "text": text.strip()}
            for key in ("leads_to_scene", "leads_to_npc", "leads_to_rumor"):
                v = rec.get(key)
                if v and isinstance(v, str) and v.strip():
                    lead[key] = v.strip()
            if lead.get("leads_to_scene") or lead.get("leads_to_npc") or lead.get("leads_to_rumor"):
                add_pending_lead(session, scene_id, lead)
                # Lead-bearing clues are explicitly actionable for affordance/context packaging.
                set_clue_presentation(session, clue_id=str(rec.get("id") or "").strip() or None, clue_text=text.strip(), level="actionable")
            superseded_id = supersede_by_clue_id.get(str(rec.get("id") or "").strip(), "")
            if superseded_id:
                cid_for_registry = str(rec.get("id") or clue_id or "").strip()
                w = world if isinstance(world, dict) else None
                new_registry_id = _canonical_registry_lead_id(cid_for_registry, w, rec)
                if (
                    new_registry_id
                    and superseded_id != new_registry_id
                    and get_lead(session, new_registry_id) is not None
                ):
                    try:
                        obsolete_superseded_lead(
                            session,
                            superseded_id,
                            replaced_by_lead_id=new_registry_id,
                            turn=session.get("turn_counter"),
                        )
                    except ValueError:
                        pass
            return [rec]
    return []
