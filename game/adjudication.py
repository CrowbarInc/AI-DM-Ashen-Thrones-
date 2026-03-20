"""Deterministic adjudication query routing for GM-facing procedural questions.

This module handles lightweight question categories before GPT narration fallback.
It does not mutate authoritative state.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from game.models import make_check_request
from game.social import find_npc_by_target


ADJUDICATION_CATEGORIES = (
    "state_query",
    "perception_query",
    "roll_requirement_query",
    "action_feasibility_query",
)


def _in_scene_npcs(world: Dict[str, Any], scene_id: str) -> list[dict]:
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return []
    out: list[dict] = []
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        loc = str(npc.get("location") or npc.get("scene_id") or "").strip()
        if loc and loc != scene_id:
            continue
        out.append(npc)
    return out


def _resolve_target_hint(text: str, session: Dict[str, Any]) -> Optional[str]:
    t = (text or "").strip().lower()
    if not t:
        return None
    # Pronoun-based targeting uses current interaction target.
    if re.search(r"\b(he|him|his|she|her|they|them|that person)\b", t):
        ctx = session.get("interaction_context") or {}
        target_id = str((ctx or {}).get("active_interaction_target_id") or "").strip()
        if target_id:
            return target_id

    # Common phrase captures.
    matchers = (
        r"\bif\s+(.+?)\s+is\s+armed\b",
        r"\bcan\s+(.+?)\s+tell\s+if\b",
        r"\bhow\s+far\s+away\s+is\s+(.+?)\b",
        r"\bwould\s+(.+?)\s+notice\b",
    )
    for pattern in matchers:
        m = re.search(pattern, t)
        if m and m.lastindex:
            hint = (m.group(1) or "").strip(" .?!,")
            if hint:
                return hint
    return None


def classify_adjudication_query(text: str) -> Optional[str]:
    """Classify likely adjudication questions into a small inspectable category set."""
    t = (text or "").strip().lower()
    if not t or "?" not in t:
        return None

    # Keep this lane explicitly procedural; do not treat ordinary social language
    # (e.g., "I require an audience.") as a mechanics query.
    has_skill_term = bool(
        re.search(
            r"\b("
            r"sleight of hand|"
            r"stealth|"
            r"perception|"
            r"sense motive|"
            r"diplomacy|"
            r"intimidate|"
            r"bluff|"
            r"thievery"
            r")\b",
            t,
        )
    )
    if has_skill_term and re.search(r"\b(need(?:ed)?|require(?:s|d)?)\b", t):
        return "roll_requirement_query"
    if re.search(
        r"\b("
        r"need(?:\s+to)?\s+roll|"
        r"roll\s+needed|"
        r"does\s+this\s+need|"
        r"does\s+that\s+need|"
        r"require(?:s|d)?\s+(?:a\s+)?(?:roll|check)|"
        r"roll\s+required|"
        r"skill\s+check|"
        r"saving\s+throw|"
        r"\bdc\b|"
        r"difficulty"
        r")\b",
        t,
    ):
        return "roll_requirement_query"
    if re.search(r"\b(earshot|nearby|who is here|anyone else here|who can hear|in range|distance|how far)\b", t):
        return "perception_query"
    if re.search(r"\b(can i|can galinor|would it work|is it possible|feasible|can .* tell if)\b", t):
        return "action_feasibility_query"
    if re.search(r"\b(is anyone|who is here|what is my|where is my|how many)\b", t):
        return "state_query"
    return None


def resolve_adjudication_query(
    text: str,
    *,
    scene: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    character: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Resolve an adjudication query from authoritative state only.

    Returns None when text is not an adjudication query.
    """
    _ = character  # Reserved for future skill/context checks.
    category = classify_adjudication_query(text)
    if category is None:
        return None

    scene_id = str(((scene or {}).get("scene") or {}).get("id") or "").strip()
    npcs_here = _in_scene_npcs(world, scene_id)

    # 1) Roll requirement queries.
    if category == "roll_requirement_query":
        low_text = text.lower()
        covert_attempt = bool(
            re.search(r"\b(conceal|hide|palm|slip|pocket|plant|pass)\b", low_text)
            and re.search(r"\b(while|without|unnoticed|watching|observing|in front of|in plain sight)\b", low_text)
        )
        if covert_attempt:
            prompt = (
                "Adjudication: This is a covert action under observation. "
                "Roll Sleight of Hand to determine whether it goes unnoticed."
            )
            return {
                "category": category,
                "answer_type": "check_required",
                "player_facing_text": prompt,
                "requires_check": True,
                "check_request": make_check_request(
                    requires_check=True,
                    check_type="sleight_of_hand",
                    skill="sleight_of_hand",
                    difficulty=None,
                    reason="covert_action_under_observation",
                    player_prompt=prompt,
                ),
            }
        if re.search(r"\b(sleight of hand|stealth|perception|sense motive|diplomacy|intimidate|bluff)\b", text.lower()):
            prompt = "Adjudication: This is uncertain and requires a check. Declare the concrete action/target and resolve it through the engine."
            return {
                "category": category,
                "answer_type": "check_required",
                "player_facing_text": prompt,
                "requires_check": True,
                "check_request": make_check_request(
                    requires_check=True,
                    check_type=None,
                    skill=None,
                    difficulty=None,
                    reason="uncertain_action",
                    player_prompt=prompt,
                ),
            }
        return {
            "category": category,
            "answer_type": "needs_concrete_action",
            "player_facing_text": "Adjudication: I cannot determine roll requirements yet. State the specific action and target first.",
            "requires_check": None,
            "check_request": None,
        }

    # 2) Earshot/nearby presence queries from scene state.
    if "earshot" in text.lower() or "nearby" in text.lower() or "who can hear" in text.lower():
        names = [str(n.get("name") or n.get("id") or "").strip() for n in npcs_here]
        names = [n for n in names if n]
        ctx = session.get("interaction_context") or {}
        active_target = str((ctx or {}).get("active_interaction_target_id") or "").strip()
        filtered = []
        for npc in npcs_here:
            nid = str(npc.get("id") or "").strip()
            name = str(npc.get("name") or nid).strip()
            if not name:
                continue
            if active_target and nid == active_target:
                continue
            filtered.append(name)
        if filtered:
            return {
                "category": "perception_query",
                "answer_type": "direct_answer",
                "player_facing_text": f"Adjudication: In earshot right now: {', '.join(filtered)}.",
                "requires_check": False,
                "check_request": None,
            }
        if names:
            return {
                "category": "perception_query",
                "answer_type": "direct_answer",
                "player_facing_text": "Adjudication: No one else is clearly in earshot beyond your current counterpart.",
                "requires_check": False,
                "check_request": None,
            }
        return {
            "category": "perception_query",
            "answer_type": "direct_answer",
            "player_facing_text": "Adjudication: No nearby NPC presence is currently established in this scene.",
            "requires_check": False,
            "check_request": None,
        }

    # 3) Armed/distance feasibility or perception checks.
    if re.search(r"\barmed\b", text.lower()) or re.search(r"\bhow far\b|\bdistance\b", text.lower()):
        target_hint = _resolve_target_hint(text, session)
        npc = find_npc_by_target(world, target_hint or "", scene_id) if target_hint else None
        if not npc:
            return {
                "category": "action_feasibility_query",
                "answer_type": "needs_concrete_action",
                "player_facing_text": "Adjudication: I need a concrete, in-scene target before I can resolve that.",
                "requires_check": None,
                "check_request": None,
            }
        if "armed" in text.lower():
            armed = npc.get("armed")
            if isinstance(armed, bool):
                armed_text = "is armed" if armed else "does not appear armed"
                return {
                    "category": "action_feasibility_query",
                    "answer_type": "direct_answer",
                    "player_facing_text": f"Adjudication: {npc.get('name') or 'Target'} {armed_text} from established state.",
                    "requires_check": False,
                    "check_request": None,
                }
            return {
                "category": "action_feasibility_query",
                "answer_type": "needs_concrete_action",
                "player_facing_text": "Adjudication: The current state does not establish whether they are armed yet.",
                "requires_check": None,
                "check_request": None,
            }
        if re.search(r"\bhow far\b|\bdistance\b", text.lower()):
            distance = npc.get("distance_ft")
            if isinstance(distance, (int, float)):
                return {
                    "category": "perception_query",
                    "answer_type": "direct_answer",
                    "player_facing_text": f"Adjudication: Estimated distance is about {int(distance)} feet.",
                    "requires_check": False,
                    "check_request": None,
                }
            return {
                "category": "perception_query",
                "answer_type": "needs_concrete_action",
                "player_facing_text": "Adjudication: Distance is not established in authoritative state yet.",
                "requires_check": None,
                "check_request": None,
            }

    # 4) Generic state query fallback.
    return {
        "category": category,
        "answer_type": "needs_concrete_action",
        "player_facing_text": "Adjudication: I need a more concrete action or target to resolve that procedurally.",
        "requires_check": None,
        "check_request": None,
    }
