"""Conservative normalization of an approach preamble; never a movement grant."""
from __future__ import annotations

import copy
import re

from game.player_interpretation_bridge import visible_catalog, normalized_action_from_interpretation


def normalize_local_approach(record, *, player_text, scene, world, session=None):
    """Keep only the interaction when authored eligibility and literal wording agree.

    Addressability is conversational eligibility, not physical reachability. We
    require an explicitly authored addressable NPC and reject any access caveat;
    no position, travel, or successful movement is asserted or persisted.
    """
    components = record.get("action_components") or []
    if (record.get("communication_mode") != "IN_WORLD_ACTION"
            or record.get("interpretation_status") != "INTERPRETED"
            or (record.get("references") or {}).get("unresolved_references")
            or len(components) != 2 or not all(isinstance(c, dict) for c in components)):
        return record
    move, interaction = components
    if move.get("order") != 1 or interaction.get("order") != 2:
        return record
    target_id = move.get("target_ref")
    operation = interaction.get("operation_class")
    if (move.get("operation_class") != "MOVE" or operation not in {"ASK", "INSPECT"}
            or not target_id or target_id != interaction.get("target_ref")):
        return record
    current = (scene or {}).get("scene", scene or {})
    target = visible_catalog(scene, world).get(target_id)
    if not target or target["kind"] == "exit":
        return record
    row = target["row"]
    authored = []
    if operation == "ASK":
        from game.interaction_context import is_actor_addressable_in_current_scene
        authored = [a for a in current.get("addressables", [])
                    if isinstance(a, dict) and a.get("id") == target_id and a.get("addressable") is True
                    and a.get("scene_id") == current.get("id")]
        if (target["kind"] != "npc" or not authored
                or not is_actor_addressable_in_current_scene(session or {}, scene, target_id, world=world)):
            return record
    elif target["kind"] not in {"inspect_target", "perceive_target"}:
        return record
    # There is no general local access solver. Unknown/caveated access remains
    # unnormalized. Scan authored public context conservatively, not model prose.
    context = " ".join(str(v) for v in [row, current.get("summary", ""),
                                       current.get("visible_facts", []),
                                       current.get("addressables", [])])
    if (current.get("mode") == "combat" or (session or {}).get("in_combat")
            or any(spec.get(k) is False for spec in [row, *authored]
                   for k in ("addressable", "accessible", "reachable"))
            or row.get("availability", "available") != "available"
            or re.search(r"\b(?:locked|barred|blocked|inaccessible|unreachable|impassable|hostile|across|behind|another room|distant)\b", context, re.I)):
        return record
    labels = [row.get("name"), row.get("label"), *row.get("aliases", [])]
    names = [re.escape(str(label).strip()) for label in labels if label]
    if not names:
        return record
    preamble = (r"(?:I\s+)?(?:approach|walk\s+over\s+to|step\s+up\s+to|go\s+over\s+to)\s+"
                r"(?:the\s+)?(?:" + "|".join(names) + r")")
    if not re.fullmatch(preamble + r"[.]?", str(move.get("description", "")).strip(), re.I):
        return record
    match = re.match(r"^" + preamble + r"\s+(?:and|to)\s+((?:I\s+)?(?:ask|question|speak\s+to|talk\s+to|examine|inspect|investigate)\b.*)$",
                     player_text.strip(), re.I)
    if not match:
        return record
    proposed = copy.deepcopy(record)
    proposed["action_components"] = [copy.deepcopy(interaction)]
    action, meta = normalized_action_from_interpretation(
        proposed, scene=scene, world=world, player_text=player_text, session=session)
    if action is None or meta.get("target_ref") != target_id:
        return record
    proposed["local_approach_normalization"] = {
        "rule": "authored_same_scene_interaction_preamble", "target_id": target_id,
        "original_components": copy.deepcopy(components), "movement_executed": False,
    }
    return proposed


_OUTSIDE_CLASS = re.compile(
    r"\b(?:take|grab|pocket|steal|pick\s+up|open|close|unlock|unlatch|break|smash|"
    r"destroy|damage|pry|write|copy|inscribe|carve|climb|read|reads|reading|"
    r"examine|inspect|investigate|search|ask|question|speak|talk|push|pull|lift|"
    r"move\s+the|shift\s+the)\b",
    re.IGNORECASE,
)
_APPROACH = re.compile(
    r"\b(?:walk\s+over\s+to|step\s+up\s+to|go\s+over\s+to|approach)\s+"
    r"(?:the\s+|a\s+|an\s+)?(?P<target>.+)$",
    re.IGNORECASE,
)
_CONTACT_PATTERNS = (
    re.compile(
        r"\b(?:put|place|rest|lay)\s+(?:a\s+|my\s+)?hand\s+(?:on|against)\s+"
        r"(?:the\s+|its\s+|a\s+)?(?P<target>.+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"\btouch(?:es|ed|ing)?\s+(?:the\s+|a\s+|an\s+)?(?P<target>.+)$",
        re.IGNORECASE,
    ),
)
_PART_WORDS = frozenset({"frame", "surface", "edge", "rail", "railing", "post", "rim", "side"})
_BLOCK_WORDS = re.compile(
    r"\b(?:locked|barred|blocked|inaccessible|unreachable|impassable)\b",
    re.IGNORECASE,
)


def _inner_scene(scene):
    if isinstance(scene, dict) and isinstance(scene.get("scene"), dict):
        return scene["scene"]
    return scene if isinstance(scene, dict) else {}


def _names(row, entity_id):
    labels = [row.get("label"), row.get("name"), str(entity_id or "").replace("_", " ")]
    labels.extend(row.get("aliases") or [])
    return [str(label).strip() for label in labels if str(label or "").strip()]


def _phrase_hits(phrase, rows):
    from game.conversational_orchestration import _place_match

    found = []
    for entity_id, row, kind in rows:
        if any(_place_match(phrase, name) for name in _names(row, entity_id)):
            found.append((entity_id, row, kind))
    return found


def _part_of_target(phrase):
    tokens = [tok for tok in re.findall(r"[a-z]+", (phrase or "").casefold()) if tok not in {"the", "a", "an", "its", "it"}]
    return bool(tokens) and set(tokens) <= _PART_WORDS


def _row_veto(row):
    if not isinstance(row, dict):
        return "access"
    check = row.get("skill_check")
    if isinstance(check, dict) and check.get("skill_id"):
        return "check"
    if row.get("hidden") or row.get("visible") is False or row.get("accessible") is False or row.get("reachable") is False:
        return "access"
    availability = row.get("availability")
    if availability not in (None, "", "available"):
        return "access"
    blob = " ".join(str(row.get(key) or "") for key in ("label", "name", "description", "notes", "access"))
    if _BLOCK_WORDS.search(blob):
        return "access"
    return None


def _surface_authority(scene, entity_id, label):
    from game.referenced_surface import AUTHORITY_AUTHORED_INTERACTABLE, classify_referenced_surface

    classified = classify_referenced_surface("", scene, explicit_target=label)
    if classified.get("authority") != AUTHORITY_AUTHORED_INTERACTABLE:
        return None
    if str(classified.get("interactable_id") or "") != str(entity_id):
        return None
    if not (classified.get("existence") and classified.get("visibility") and classified.get("inspectability")):
        return None
    return classified


def _narrate(label, location, *, movement, contact_phrase):
    name = label[:1].lower() + label[1:] if label else "object"
    stay = f" You remain in {location}." if location else ""
    if movement and contact_phrase:
        return f"You walk over to the {name} and rest a hand on {contact_phrase}.{stay}"
    if movement:
        return f"You walk over to the {name}.{stay}"
    return f"You rest a hand on the {name}.{stay}"


def resolve_transient_local_action(player_text, *, scene, world, session=None):
    """Authorize low-stakes approach or contact, or refuse it without a new owner.

    Returns None when the utterance belongs to travel, speech, inspection,
    consequential manipulation, or the experimental physical owner. A returned
    record is the authoritative transient outcome. It does not mutate state.
    """
    text = re.sub(r"\s+", " ", str(player_text or "")).strip()
    if not text or "?" in text or _OUTSIDE_CLASS.search(text):
        return None
    if not re.match(r"^(?:i|we|let me|let's|lets)\b", text, re.IGNORECASE):
        return None
    from game.physical_adjudication import enabled

    if enabled(session):
        return None
    inner = _inner_scene(scene)
    if inner.get("mode") == "combat" or (session or {}).get("in_combat"):
        return None
    parts = [part.strip(" .") for part in re.split(r"\s+\band\s+", text, flags=re.IGNORECASE) if part.strip(" .")]
    if len(parts) > 2:
        return None
    clauses = parts or [text]
    approach_phrase = None
    contact_phrase = None
    for clause in clauses:
        approached = _APPROACH.search(clause)
        contacted = next((match for pattern in _CONTACT_PATTERNS if (match := pattern.search(clause))), None)
        if approached and contacted:
            return None
        if approached:
            if approach_phrase is not None:
                return None
            approach_phrase = approached.group("target").strip(" .")
        elif contacted:
            if contact_phrase is not None:
                return None
            contact_phrase = contacted.group("target").strip(" .")
        else:
            return None
    if not approach_phrase and not contact_phrase:
        return None
    from game.player_interpretation_bridge import visible_catalog

    catalog = visible_catalog(scene, world)
    visible_rows = []
    npc_rows = []
    for entity_id, info in catalog.items():
        row = info.get("row") if isinstance(info.get("row"), dict) else {}
        kind = str(info.get("kind") or "")
        if kind == "npc":
            npc_rows.append((entity_id, row, kind))
        elif kind in {"inspect_target", "perceive_target"}:
            visible_rows.append((entity_id, row, kind))
    raw_rows = []
    for item in inner.get("interactables") or []:
        if isinstance(item, dict) and item.get("id"):
            raw_rows.append((str(item.get("id")), item, "interactable"))
    anchor = approach_phrase or contact_phrase
    if npc_rows and _phrase_hits(anchor, npc_rows) and not _phrase_hits(anchor, visible_rows):
        return None
    visible_hits = _phrase_hits(anchor, visible_rows)
    if len(visible_hits) > 1:
        labels = [str(row.get("label") or entity_id) for entity_id, row, _kind in visible_hits[:4]]
        return {
            "status": "refused",
            "category": "clarify",
            "reason": "ambiguous_local_object",
            "target_id": None,
            "player_facing_text": (
                "More than one thing here could match. Do you mean "
                + " or ".join(labels)
                + "? Nothing has been attempted."
            ),
            "scene_transition": False,
            "persistent_state_changed": False,
            "narration_authorized": False,
        }
    if len(visible_hits) == 0:
        hidden_hits = [
            (entity_id, row) for entity_id, row, _kind in _phrase_hits(anchor, raw_rows)
            if row.get("hidden") or row.get("visible") is False
        ]
        blocked_hits = [
            (entity_id, row) for entity_id, row, _kind in _phrase_hits(anchor, raw_rows)
            if row.get("accessible") is False or row.get("reachable") is False
        ]
        if hidden_hits:
            return {
                "status": "refused",
                "category": "decline",
                "reason": "hidden_local_object",
                "target_id": None,
                "player_facing_text": "Nothing here matches that. Nothing has been attempted.",
                "scene_transition": False,
                "persistent_state_changed": False,
                "narration_authorized": False,
            }
        if blocked_hits:
            label = str(blocked_hits[0][1].get("label") or blocked_hits[0][0])
            return {
                "status": "refused",
                "category": "decline",
                "reason": "inaccessible_local_object",
                "target_id": blocked_hits[0][0],
                "label": label,
                "player_facing_text": (
                    f"{label} is not accessible from here. "
                    "You have not approached or touched it."
                ),
                "scene_transition": False,
                "persistent_state_changed": False,
                "narration_authorized": False,
            }
        return None
    entity_id, row, kind = visible_hits[0]
    veto = _row_veto(row)
    if veto:
        label = str(row.get("label") or entity_id)
        if veto == "check":
            message = f"Touching or approaching the {label[:1].lower() + label[1:]} needs a check that is not resolved. Nothing was attempted."
            reason = "unresolved_local_check"
        else:
            message = f"{label} is not accessible from here. You have not approached or touched it."
            reason = "inaccessible_local_object"
        return {
            "status": "refused",
            "category": "decline",
            "reason": reason,
            "target_id": entity_id,
            "label": label,
            "player_facing_text": message,
            "scene_transition": False,
            "persistent_state_changed": False,
            "narration_authorized": False,
        }
    label = str(row.get("label") or entity_id)
    authority = _surface_authority(scene, entity_id, label)
    if authority is None:
        return None
    contact_binding = None
    if contact_phrase:
        contact_hits = _phrase_hits(contact_phrase, visible_rows)
        same = len(contact_hits) == 1 and contact_hits[0][0] == entity_id
        if same or (approach_phrase and _part_of_target(contact_phrase)):
            contact_binding = "its " + next(iter(_PART_WORDS & set(re.findall(r"[a-z]+", contact_phrase.casefold()))), "").strip()
            if same and not _part_of_target(contact_phrase):
                contact_binding = "it"
            elif _part_of_target(contact_phrase):
                part = next(tok for tok in re.findall(r"[a-z]+", contact_phrase.casefold()) if tok in _PART_WORDS)
                contact_binding = f"its {part}"
        else:
            return None
    movement = approach_phrase is not None
    narration = _narrate(
        label, str(inner.get("location") or "").strip(),
        movement=movement, contact_phrase=contact_binding,
    )
    categories = []
    if movement:
        categories.append("local_movement")
    if contact_phrase:
        categories.append("physical_contact")
    return {
        "status": "completed",
        "category": "transient_local_action",
        "reason": "transient_local_action_completed",
        "target_id": entity_id,
        "label": label,
        "action_category": "_and_".join(categories),
        "categories": categories,
        "completion": {
            "local_movement": "completed" if movement else "not_requested",
            "physical_contact": "completed" if contact_phrase else "not_requested",
        },
        "authority_basis": {
            "source": "authored_interactable_visible_catalog",
            "visible_catalog_kind": kind,
            "referenced_surface_authority": authority.get("authority"),
            "existence": True,
            "visibility": True,
            "inspectability": True,
            "explicit_access_block": False,
        },
        "scene_transition": False,
        "persistent_state_changed": False,
        "narration_authorized": True,
        "player_facing_text": narration,
        "scene_id": str(inner.get("id") or ""),
    }
