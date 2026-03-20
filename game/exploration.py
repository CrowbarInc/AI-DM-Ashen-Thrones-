"""Deterministic exploration action resolution: runs before GPT narration for scene_transition, observe, investigate, interact, custom."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from game.models import ExplorationEngineResult
from game.utils import slugify
from game.storage import get_scene_runtime, add_pending_lead, is_interactable_resolved, is_target_searched
from game.clues import apply_authoritative_clue_discovery, set_clue_presentation
from game.scene_graph import build_scene_graph, is_transition_valid
from game.skill_checks import resolve_skill_check, should_trigger_check


EXPLORATION_KINDS = ("scene_transition", "travel", "observe", "investigate", "interact", "custom", "discover_clue", "already_searched")


def _infer_transition_target_from_prompt(
    prompt: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: set[str],
) -> Optional[str]:
    """Best-effort deterministic destination inference from prompt text and exits."""
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


def parse_exploration_intent(text: str, scene_envelope: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detect exploration patterns in free text. Returns a raw dict compatible with normalize_scene_action, or None.

    Delegates to intent_parser.parse_freeform_to_action for deterministic parsing with scene context.
    """
    from game.intent_parser import parse_freeform_to_action

    result = parse_freeform_to_action(text, scene_envelope)
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
    if transition_candidate and not target_scene_id:
        target_scene_id = _infer_transition_target_from_prompt(prompt, scene.get("exits") or [], known_set)

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
        elif target_scene_id and target_scene_id in known_set:
            hint = (
                f"Player attempted to travel to {target_scene_id}, but that path is not reachable from here. "
                "Narrate blocked movement, attempted path, or unresolved travel—do not imply arrival."
            )
        else:
            hint = "Player expressed travel intent; target scene not resolved. Narrate based on current scene and intent."
    elif action_type == "observe":
        hint = "Player is focusing on observing the current scene. Narrate what stands out or what careful observation reveals—avoid repeating the same summary."
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
        metadata={"skill_check": skill_check_result} if skill_check_result else {},
    )
    d = result.to_dict()
    if skill_check_result:
        d["skill_check"] = skill_check_result
    return d


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
            return [rec]
    return []
