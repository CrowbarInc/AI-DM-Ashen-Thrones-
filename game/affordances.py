from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from game.utils import slugify
from game.leads import pending_lead_surfaces_as_active_follow_opportunity
from game.scene_actions import normalize_scene_action
from game.scene_graph import get_reachable_from
from game.clues import get_all_known_clue_ids as get_known_clue_ids, get_all_known_clue_texts as get_known_clue_texts
from game.storage import (
    get_scene_runtime,
    get_world_flag,
    list_scene_ids as _list_scene_ids,
)


def _humanize_id(obj_id: str) -> str:
    """Convert id like 'patrol_maps' to 'patrol maps' for display labels."""
    if not obj_id or not isinstance(obj_id, str):
        return str(obj_id or "")
    return " ".join(obj_id.strip().split("_")).strip().title() or obj_id


def _affordance_passes_conditions(
    action: Dict[str, Any],
    scene_id: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
) -> bool:
    """Return True if the affordance has no conditions or all conditions pass. Deterministic filtering."""
    cond = action.get("conditions")
    if not cond or not isinstance(cond, dict):
        return True

    # Use clue knowledge layer (includes discovered + inferred)
    discovered_ids = get_known_clue_ids(session)
    discovered_texts = get_known_clue_texts(session)
    # requires_flags: all must be truthy in world_state.flags
    for flag in cond.get("requires_flags") or []:
        if not flag:
            continue
        val = get_world_flag(world, str(flag).strip())
        if not val:
            return False

    # excludes_flags: none may be truthy
    for flag in cond.get("excludes_flags") or []:
        if not flag:
            continue
        val = get_world_flag(world, str(flag).strip())
        if val:
            return False

    # requires_clues: all must be discovered (by id or text)
    for clue in cond.get("requires_clues") or []:
        c = str(clue).strip() if clue else ""
        if not c:
            continue
        if c not in discovered_ids and c not in discovered_texts:
            return False

    # excludes_clues: none may be discovered
    for clue in cond.get("excludes_clues") or []:
        c = str(clue).strip() if clue else ""
        if not c:
            continue
        if c in discovered_ids or c in discovered_texts:
            return False

    return True


ALREADY_SEARCHED_SUFFIX = " (already searched)"
MAX_RETURNED_AFFORDANCES = 5

SOCIAL_ACTION_TYPES = {"question", "interact", "talk", "speak", "persuade", "intimidate", "deceive"}


def _normalize_text_key(text: str) -> str:
    t = str(text or "").strip().lower()
    if not t:
        return ""
    t = re.sub(r"[^a-z0-9\s]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalize_noun_phrase(text: str) -> str:
    phrase = str(text or "").strip().strip(".!?")
    if not phrase:
        return ""
    words = phrase.split()
    if len(words) > 1 and all(w[:1].isupper() for w in words if w and w[:1].isalpha()):
        return phrase.lower()
    return phrase


def _with_article(phrase: str) -> str:
    p = _normalize_noun_phrase(phrase)
    if not p:
        return "it"
    lower = p.lower()
    if lower.startswith(("the ", "a ", "an ", "my ", "your ", "their ", "his ", "her ", "this ", "that ")):
        return p
    if len(p.split()) == 1 and p[:1].isupper():
        return p
    return f"the {p}"


def _looks_like_person(text: str) -> bool:
    t = _normalize_text_key(text)
    if not t:
        return False
    tokens = {"npc", "man", "woman", "guard", "captain", "merchant", "priest", "runner", "child", "person", "people"}
    return any(tok in t.split() for tok in tokens)


def _extract_subject_from_fact(fact: str) -> str:
    text = str(fact or "").strip().strip(".!?")
    if not text:
        return "something nearby"
    lowered = text.lower()
    for prefix in ("there is ", "there are ", "you see ", "you notice ", "nearby ", "ahead "):
        if lowered.startswith(prefix):
            return text[len(prefix):].strip(" ,.")
    if "," in text:
        return text.split(",", 1)[0].strip()
    return text


def _truncate_phrase(text: str, max_len: int = 40) -> str:
    phrase = str(text or "").strip()
    if len(phrase) <= max_len:
        return phrase
    return phrase[: max_len - 3].rstrip() + "..."


def _label_and_prompt_for_visible_fact(fact: str) -> Tuple[str, str]:
    subject = _truncate_phrase(_extract_subject_from_fact(fact), 40)
    subject_key = _normalize_text_key(subject)
    exit_words = {"exit", "gate", "road", "path", "district", "alley", "bridge", "stairs"}
    group_words = {"men", "women", "figures", "crowd", "group", "voices", "whispers", "shadows"}

    if any(w in subject_key.split() for w in exit_words):
        destination = _normalize_noun_phrase(subject)
        return f"Leave for {destination}", f"I head toward {destination}."
    if any(w in subject_key.split() for w in group_words):
        target = _with_article(subject)
        return f"Approach {target}", f"I approach {target}."
    if _looks_like_person(subject):
        target = _normalize_noun_phrase(subject)
        return f"Talk to {target}", f"I talk to {target}."

    target = _with_article(subject)
    return f"Examine {target}", f"I examine {target}."


def _is_explicit_action(scene: Dict[str, Any], action: Dict[str, Any]) -> bool:
    raw_actions = ((scene.get("scene") or {}).get("actions") or (scene.get("scene") or {}).get("suggested_actions") or [])
    explicit_ids: Set[str] = set()
    for raw in raw_actions:
        norm = normalize_scene_action(raw)
        aid = str(norm.get("id") or "").strip()
        if aid:
            explicit_ids.add(aid)
    return str(action.get("id") or "").strip() in explicit_ids


def _affordance_dedupe_key(action: Dict[str, Any]) -> str:
    action_type = str(action.get("type") or "").strip().lower()
    target_entity = str(action.get("targetEntityId") or action.get("target_entity_id") or action.get("target_id") or "").strip().lower()
    target_scene = str(action.get("targetSceneId") or action.get("target_scene_id") or "").strip().lower()
    target_location = str(action.get("targetLocationId") or action.get("target_location_id") or "").strip().lower()
    target = target_entity or target_scene or target_location

    label_key = _normalize_text_key(str(action.get("label") or ""))
    prompt_key = _normalize_text_key(str(action.get("prompt") or ""))

    if action_type in SOCIAL_ACTION_TYPES and target_entity:
        return f"social|{target_entity}"

    type_key = "inspect" if action_type in {"observe", "investigate"} and target else action_type
    return f"{type_key}|{target}|{label_key}|{prompt_key}"


def _affordance_rank(action: Dict[str, Any], scene: Dict[str, Any]) -> int:
    action_type = str(action.get("type") or "").strip().lower()
    label = str(action.get("label") or "").strip().lower()
    target_entity = str(action.get("targetEntityId") or action.get("target_entity_id") or action.get("target_id") or "").strip()
    target_scene = str(action.get("targetSceneId") or action.get("target_scene_id") or "").strip()

    score = 0
    if _is_explicit_action(scene, action):
        score += 100
    if action_type in SOCIAL_ACTION_TYPES and target_entity:
        score += 80
    elif action_type in {"investigate", "interact"} and target_entity:
        score += 65
    elif action_type in {"investigate", "interact"}:
        score += 45
    elif action_type in {"scene_transition", "travel"} and target_scene:
        score += 25
    elif action_type == "observe":
        score += 10

    if label in {"observe the area", "scan for details", "look around", "survey the area"}:
        score -= 5
    return score


def _dedupe_rank_and_prune(actions: List[Dict[str, Any]], scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked: List[Tuple[int, int, Dict[str, Any]]] = []
    for idx, action in enumerate(actions):
        ranked.append((_affordance_rank(action, scene), idx, action))
    ranked.sort(key=lambda x: (-x[0], x[1]))

    seen_keys: Set[str] = set()
    result: List[Dict[str, Any]] = []
    for _, _, action in ranked:
        key = _affordance_dedupe_key(action)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        result.append(action)
        if len(result) >= MAX_RETURNED_AFFORDANCES:
            break
    return result


def _affordance_for_interactable(interactable: Dict[str, Any]) -> Dict[str, Any] | None:
    """Generate a single affordance from an interactable. Returns None if interactable is invalid."""
    if not isinstance(interactable, dict):
        return None
    obj_id = str(interactable.get("id") or "").strip()
    if not obj_id:
        return None
    label = str(interactable.get("label") or "").strip() or _humanize_id(obj_id)
    itype = (str(interactable.get("type") or "investigate")).strip().lower()

    if itype == "investigate":
        target = _with_article(label)
        return {
            "id": obj_id,
            "label": f"Examine {target}",
            "type": "investigate",
            "prompt": f"I examine {target}.",
            "targetEntityId": obj_id,
            "targetSceneId": None,
            "targetLocationId": None,
        }
    if itype == "interact":
        if _looks_like_person(label):
            action_label = f"Talk to {_normalize_noun_phrase(label)}"
            prompt = f"I talk to {_normalize_noun_phrase(label)}."
        else:
            target = _with_article(label)
            action_label = f"Approach {target}"
            prompt = f"I approach {target}."
        return {
            "id": obj_id,
            "label": action_label,
            "type": "interact",
            "prompt": prompt,
            "targetEntityId": obj_id,
            "targetSceneId": None,
            "targetLocationId": None,
        }
    if itype == "observe":
        target = _with_article(label)
        return {
            "id": obj_id,
            "label": f"Inspect {target}",
            "type": "observe",
            "prompt": f"I inspect {target}.",
            "targetEntityId": obj_id,
            "targetSceneId": None,
            "targetLocationId": None,
        }
    # Default to investigate
    target = _with_article(label)
    return {
        "id": obj_id,
        "label": f"Examine {target}",
        "type": "investigate",
        "prompt": f"I examine {target}.",
        "targetEntityId": obj_id,
        "targetSceneId": None,
        "targetLocationId": None,
    }


def _affordance_for_object(obj: Dict[str, Any]) -> Dict[str, Any] | None:
    """Generate a single affordance from a scene object. Returns None if object is invalid."""
    if not isinstance(obj, dict):
        return None
    obj_id = str(obj.get("id") or "").strip()
    if not obj_id:
        return None
    label = str(obj.get("label") or "").strip() or _humanize_id(obj_id)
    itype = (str(obj.get("type") or "investigate")).strip().lower()
    if itype not in ("investigate", "observe", "interact"):
        itype = "investigate"

    if itype == "investigate":
        target = _with_article(label)
        return {
            "id": obj_id,
            "label": f"Examine {target}",
            "type": "investigate",
            "prompt": f"I examine {target}.",
            "targetEntityId": obj_id,
            "targetSceneId": None,
            "targetLocationId": None,
        }
    if itype == "interact":
        if _looks_like_person(label):
            action_label = f"Talk to {_normalize_noun_phrase(label)}"
            prompt = f"I talk to {_normalize_noun_phrase(label)}."
        else:
            target = _with_article(label)
            action_label = f"Approach {target}"
            prompt = f"I approach {target}."
        return {
            "id": obj_id,
            "label": action_label,
            "type": "interact",
            "prompt": prompt,
            "targetEntityId": obj_id,
            "targetSceneId": None,
            "targetLocationId": None,
        }
    target = _with_article(label)
    return {
        "id": obj_id,
        "label": f"Inspect {target}",
        "type": "observe",
        "prompt": f"I inspect {target}.",
        "targetEntityId": obj_id,
        "targetSceneId": None,
        "targetLocationId": None,
    }


def _generate_affordances_from_interactables(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate affordances from scene.interactables. Each interactable yields one affordance based on its type."""
    interactables = scene.get("interactables") or []
    if not isinstance(interactables, list):
        return []
    result: List[Dict[str, Any]] = []
    for i in interactables:
        a = _affordance_for_interactable(i)
        if a:
            result.append(a)
    return result


def _generate_affordances_from_objects(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate affordances from scene.objects (optional). Each object yields one affordance based on its type."""
    objects = scene.get("objects") or []
    if not isinstance(objects, list):
        return []
    result: List[Dict[str, Any]] = []
    for o in objects:
        a = _affordance_for_object(o)
        if a:
            result.append(a)
    return result


def get_available_affordances(
    scene: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    *,
    mode: str | None = None,
    list_scene_ids_fn: Any = None,
    scene_graph: Optional[Dict[str, Set[str]]] = None,
) -> List[Dict[str, Any]]:
    """Return filtered affordances for the current scene. Only includes actions that pass conditions.
    When scene_graph is provided, scene_transition affordances are filtered to only those whose
    target is reachable from the current scene (exits + pending leads).
    """
    all_affs = generate_scene_affordances(
        scene, mode or (scene.get("scene") or {}).get("mode", "exploration") or "exploration", session, list_scene_ids_fn
    )
    scene_id = (scene.get("scene") or {}).get("id") or ""
    # Default social affordances from NPCs in this scene.
    # If the scene already authors social actions for a target NPC, skip auto-defaults for that NPC.
    authored_social_targets: Set[str] = set()
    raw_scene_actions = (scene.get("scene") or {}).get("actions") or (scene.get("scene") or {}).get("suggested_actions") or []
    for raw in raw_scene_actions:
        if not isinstance(raw, dict):
            continue
        raw_type = str(raw.get("type") or "").strip().lower()
        raw_label = str(raw.get("label") or "").strip().lower()
        raw_prompt = str(raw.get("prompt") or "").strip().lower()
        target = str(raw.get("targetEntityId") or raw.get("target_entity_id") or raw.get("target_id") or "").strip()
        if target and (raw_type in SOCIAL_ACTION_TYPES or "talk" in raw_label or "ask" in raw_label or "talk" in raw_prompt or "ask" in raw_prompt):
            authored_social_targets.add(target)

    for npc in (world.get("npcs") or [])[:10]:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        name = str(npc.get("name") or "someone").strip()
        loc = npc.get("location") or npc.get("scene_id") or ""
        loc = str(loc).strip() if loc else ""
        if not nid or (loc and loc != scene_id):
            continue
        if nid in authored_social_targets:
            continue
        all_affs.append({
            "id": slugify(f"question-{nid}") or f"question-{nid}",
            "label": f"Talk to {name}",
            "type": "question",
            "prompt": f"I talk to {name}.",
            "targetSceneId": None,
            "targetEntityId": nid,
            "targetLocationId": None,
        })
    scene_rt = get_scene_runtime(session, scene_id) if scene_id and isinstance(session, dict) else {}
    consumed = set(str(x) for x in (scene_rt.get("consumed_action_ids") or []) if x)
    searched = set(str(x) for x in (scene_rt.get("searched_targets") or []) if x)
    known_set = set((list_scene_ids_fn or _list_scene_ids)()) if list_scene_ids_fn or True else set()
    reachable: Set[str] = set()
    if scene_graph and scene_id:
        reachable = get_reachable_from(scene_id, scene_graph, session=session, known_scene_ids=known_set)
    result: List[Dict[str, Any]] = []
    for a in all_affs:
        aid = str(a.get("id") or "").strip()
        if aid and aid in consumed:
            continue
        if not _affordance_passes_conditions(a, scene_id, session, world):
            continue
        # Scene graph filter: only show scene_transition affordances whose target is reachable
        if scene_graph and (a.get("type") or "").strip().lower() == "scene_transition":
            tid = (a.get("targetSceneId") or a.get("target_scene_id") or "").strip()
            if tid and tid not in reachable:
                continue
        # Relabel investigate actions whose target was already searched
        if aid and aid in searched and (a.get("type") or "").strip().lower() == "investigate":
            label = str(a.get("label") or "").strip()
            if label and ALREADY_SEARCHED_SUFFIX not in label:
                a = dict(a)
                a["label"] = label + ALREADY_SEARCHED_SUFFIX
        result.append(a)
    return _dedupe_rank_and_prune(result, scene)


def generate_scene_affordances(scene_envelope: Dict[str, Any], mode: str, session: Dict[str, Any], list_scene_ids_fn: Any = None) -> List[Dict[str, Any]]:
    """Generate structured scene actions (suggested actions) from the current scene. Merges optional scene.actions with generated ones."""
    scene = (scene_envelope or {}).get('scene', {}) if isinstance(scene_envelope, dict) else {}
    visible = scene.get('visible_facts', []) or []
    exits = scene.get('exits', []) or []
    mode = mode or scene.get('mode', 'exploration') or 'exploration'
    scene_id = scene.get('id') or ''
    known_ids = set((list_scene_ids_fn or _list_scene_ids)())

    actions: List[Dict[str, Any]] = []

    def add_action(
        label: str,
        action_type: str,
        prompt: str,
        *,
        target_scene_id: str | None = None,
        target_entity_id: str | None = None,
        target_location_id: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        aid = slugify(label) or slugify(prompt) or "action"
        row: Dict[str, Any] = {
            "id": aid,
            "label": label,
            "type": action_type,
            "prompt": prompt,
            "targetSceneId": target_scene_id,
            "targetEntityId": target_entity_id,
            "targetLocationId": target_location_id,
        }
        if metadata:
            row["metadata"] = dict(metadata)
        actions.append(row)

    # Small baseline set: keep one generic look action.
    add_action("Observe the area", "observe", "I look around and take in the area.")

    # From visible facts: one concise action each (no observe/investigate duplicates).
    for fact in visible[:5]:
        text = str(fact)
        label, prompt = _label_and_prompt_for_visible_fact(text)
        add_action(label, "investigate", prompt)

    # From interactables: auto-generated affordances (manual scene.actions override via by_id)
    for a in _generate_affordances_from_interactables(scene):
        actions.append(a)

    # From scene.objects (optional): auto-generated affordances
    for a in _generate_affordances_from_objects(scene):
        actions.append(a)

    # From exits: scene_transition with targetSceneId; support conditions for flag-gating
    for ex in exits[:5]:
        if not isinstance(ex, dict):
            continue
        label = str(ex.get("label", "Travel")).strip() or "Travel"
        target = (ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip() or None
        short_label = label if len(label) <= 44 else label[:41] + "..."
        exit_action: Dict[str, Any] = {
            "id": slugify(f"Leave for {short_label}") or "leave",
            "label": f"Leave for {short_label}",
            "type": "scene_transition" if target else "travel",
            "prompt": f"I leave for {label}.",
            "targetSceneId": target,
            "targetEntityId": None,
            "targetLocationId": None,
        }
        if ex.get("conditions") and isinstance(ex["conditions"], dict):
            exit_action["conditions"] = ex["conditions"]
        actions.append(exit_action)

    # From pending leads (clue leads_to_scene): exploration affordances
    rt = get_scene_runtime(session, scene_id) if scene_id and isinstance(session, dict) else {}
    for lead in (rt.get("pending_leads") or [])[:5]:
        if not isinstance(lead, dict):
            continue
        if not pending_lead_surfaces_as_active_follow_opportunity(session, lead):
            continue
        target = lead.get("leads_to_scene")
        if target and str(target).strip() in known_ids:
            text = lead.get("text", "")[:60]
            label = f"Follow lead: {text}..." if len(str(lead.get("text", ""))) > 60 else f"Follow lead: {text}"
            auth_lid = str(lead.get("authoritative_lead_id") or "").strip() or str(lead.get("clue_id") or "").strip()
            if not auth_lid:
                continue
            clue_id_val = str(lead.get("clue_id") or "").strip()
            fl_meta: Dict[str, Any] = {
                "authoritative_lead_id": auth_lid,
                "commitment_source": "follow_lead_affordance",
                "commitment_strength": 1,
                "target_scene_id": str(target).strip(),
            }
            if clue_id_val:
                fl_meta["clue_id"] = clue_id_val
            lt_raw = lead.get("text")
            if lt_raw is not None:
                lt_s = str(lt_raw).strip()
                if lt_s:
                    fl_meta["lead_text"] = lt_s
            add_action(
                label,
                "scene_transition",
                f"I follow the lead to {target}.",
                target_scene_id=str(target).strip(),
                metadata=fl_meta,
            )

    # Mode-specific
    if mode == "combat":
        add_action("Assess tactical options", "custom", "I quickly assess positions, cover, and threats.")
    elif mode == "social":
        add_action("Gauge the mood", "interact", "I gauge the mood and look for someone approachable to talk to.")

    # Legacy: merge optional scene.actions (strings or structured) normalized.
    # Build by id: generated first, scene.actions override (allows conditional overrides e.g. scan-for-details with excludes_clues).
    by_id: Dict[str, Dict[str, Any]] = {}
    for a in actions:
        norm = normalize_scene_action(a)
        if norm.get("id"):
            by_id[norm["id"]] = norm
    raw_actions = scene.get("actions") or scene.get("suggested_actions") or []
    for raw in raw_actions:
        norm = normalize_scene_action(raw)
        if norm.get("id") and norm.get("label"):
            by_id[norm["id"]] = norm
    # Preserve order: scene.actions first (explicit author intent), then generated
    seen: set = set()
    result: List[Dict[str, Any]] = []
    for raw in raw_actions:
        norm = normalize_scene_action(raw)
        aid = norm.get("id")
        if aid and aid not in seen:
            seen.add(aid)
            result.append(norm)
    for a in actions:
        norm = by_id.get(normalize_scene_action(a).get("id", "") or "")
        if norm and norm.get("id") not in seen:
            seen.add(norm["id"])
            result.append(norm)
    return result

