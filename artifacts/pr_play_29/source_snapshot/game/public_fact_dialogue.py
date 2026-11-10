"""Conservative projection of a registered speaker's visible offerings.

Legacy visible facts have no entity IDs. Accept only a complete, positive
subject/offer/list sentence whose exact subject uniquely names an addressable
NPC. This is deliberately not a general prose or public-knowledge matcher.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

_QUESTION = re.compile(
    r"(?:what (?:are (?:you|they) offering|(?:do you|does (?:he|she)) (?:sell|offer|serve)|"
    r"services do you offer|are you serving)|what(?:'s| is) available|"
    r"what they(?:'re| are) offering)", re.I,
)
_UNSAFE = re.compile(
    r"\b(?:not|no|never|only|but|if|unless|and then|secret\w*|hidden|private|"
    r"password\w*|allegiance|classified|reward\w*|quest\w*|promise\w*|"
    r"copper|silver|gold|coin\w*|free|cost\w*|price\w*|pay\w*|"
    r"will|can|must|may|might|has|have|is|are|was|were|for|with|to|of|that|which|who|"
    r"one|two|three|four|five|six|seven|eight|nine|ten|all|unlimited)\b|\d", re.I,
)


def select_public_offering(scene: Mapping[str, Any] | None, npc: Mapping[str, Any],
                           question: str) -> dict[str, Any]:
    """Return selection diagnostics; never mutate scene, NPC, or topics."""
    result: dict[str, Any] = {"candidate_sources": [], "selected_source": "", "reason": "no_safe_match"}
    # Original compound action is supported, but a second question/qualifier is
    # not silently answered by selecting just the convenient clause.
    text = " ".join(question.replace("\u2019", "'").lower().split()).rstrip(".?!")
    text = re.sub(r"^i (?:approach|ask) (?:the )?" + re.escape(str(npc.get("name") or "").lower())
                  + r"(?: and ask)? ", "", text)
    if not _QUESTION.fullmatch(text):
        return result
    env = scene.get("scene", scene) if isinstance(scene, Mapping) else {}
    sid, nid = str(env.get("id") or ""), str(npc.get("id") or "")
    if not sid or not nid or npc.get("location") != sid:
        return result
    roster = env.get("addressables") or []
    own = [r for r in roster if isinstance(r, Mapping) and r.get("id") == nid]
    if len(own) != 1 or own[0].get("kind") != "npc" or own[0].get("addressable") is not True or own[0].get("scene_id") != sid:
        return result
    name = str(own[0].get("name") or "").strip()
    if not name or name.casefold() != str(npc.get("name") or "").strip().casefold():
        return result
    if sum(str(r.get("name") or "").strip().casefold() == name.casefold()
           for r in roster if isinstance(r, Mapping)) != 1:
        result["reason"] = "ambiguous_subject"
        return result
    # Exact subject, affirmative verb, bounded noun lists, optional location.
    grammar = re.compile(r"(?:A |An |The )?" + re.escape(name)
                         + r" (?:offers|sells|serves|trades) (?P<items>[a-z ,'-]+?)"
                         + r"(?: near (?:the |a |an )?[a-z -]+)?[.]?", re.I)
    candidates = []
    for index, fact in enumerate(env.get("visible_facts") or []):
        if not isinstance(fact, str):
            continue
        match = grammar.fullmatch(fact.strip())
        if not match:
            continue
        items = match["items"].strip()
        parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", items)
        if _UNSAFE.search(items) or not 1 <= len(parts) <= 6 or any(
            not re.fullmatch(r"[a-z]+(?:[-' ][a-z]+){0,3}", p, re.I) for p in parts
        ):
            continue
        candidates.append({"source_id": f"scene:{sid}:visible:{index}", "source_text": fact,
                           "npc_id": nid, "relation": "own_offerings", "items": items,
                           "text": f"I offer {items}."})
    result["candidate_sources"] = [c["source_id"] for c in candidates]
    # Authored offerings (including restricted offerings) always take precedence.
    # Do not turn this fallback into a second disclosure route for those topics.
    topics = npc.get("topics") or npc.get("knowledge") or []
    if any(re.search(r"\b(?:offer\w*|sell\w*|serv\w*|trad\w*)\b", str(t), re.I) for t in topics):
        result["reason"] = "authored_offering_precedence"
        return result
    # A restricted topic about an advertised item must not be laundered by
    # the visible sentence even if the topic omits an offering verb.
    from game.dialogue_authority import npc_source_permitted
    for topic in topics:
        if not npc_source_permitted(npc, topic) and any(
            set(re.findall(r"[a-z]+", c["items"].lower())) - {"and", "a", "the"}
            & set(re.findall(r"[a-z]+", str(topic).lower())) for c in candidates
        ):
            result["reason"] = "restricted_item_source"
            return result
    if len(candidates) != 1:
        result["reason"] = "ambiguous_facts" if candidates else "no_safe_match"
        return result
    result.update(selected_source=candidates[0]["source_id"], fact=candidates[0], reason="authorized")
    return result
