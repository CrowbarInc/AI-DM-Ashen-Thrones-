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
    match = re.match(r"^" + preamble + r"\s+and\s+((?:I\s+)?(?:ask|question|speak\s+to|talk\s+to|examine|inspect)\b.*)$",
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
