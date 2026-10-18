"""Lightweight grounding checks for PR-DT narration outputs."""

from __future__ import annotations

import re
from typing import Any

_MECHANICAL_PATTERNS = (
    r"\bhp\b",
    r"\bhit points?\b",
    r"\broll(?:ed|s)?\b",
    r"\bdice\b",
    r"\binventory\b",
    r"\bitem\b",
    r"\badvance(?:s|d)? time\b",
)


def evaluate_text(text: str, prohibited: tuple[str, ...], *, kind: str = "gameplay") -> dict[str, Any]:
    lowered = text.casefold()
    hidden = []
    if "brass token" in lowered or "sealed token" in lowered:
        hidden.append("hidden lantern token")
    if "north road" in lowered and "notice" not in lowered and "mara" not in lowered:
        hidden.append("north-road fact appears outside an authorized source")
    mechanical = sorted(
        {
            pattern.strip("\\b")
            for pattern in _MECHANICAL_PATTERNS
            if re.search(pattern, lowered)
        }
    )
    commitments = []
    for phrase in ("will escort", "promises", "agrees to help", "opens the gate", "joins you"):
        if phrase in lowered:
            commitments.append(phrase)
    unsupported = []
    for rule in prohibited:
        key = _rule_keyword(rule)
        if key and key in lowered and not _is_safe_ooc_refusal(lowered, key, kind):
            unsupported.append(rule)
    contradictions = []
    if "courtyard" in lowered and "notice board" in lowered and "street" not in lowered:
        contradictions.append("notice board appears tied to courtyard visibility")
    return {
        "supported_facts": [],
        "unsupported_additions": unsupported,
        "contradictions": contradictions,
        "hidden_information_leaks": hidden,
        "mechanical_claims": mechanical,
        "npc_commitments": commitments,
        "integrity_failure": bool(
            unsupported
            or contradictions
            or hidden
            or commitments
            or (mechanical and kind != "ooc")
            or _asserts_mechanical_effect(lowered)
        ),
    }


def _rule_keyword(rule: str) -> str:
    lowered = rule.casefold()
    if "hidden token" in lowered:
        return "brass token"
    if "escort" in lowered:
        return "escort"
    if "notice board clue" in lowered or "clue text" in lowered:
        return "north road"
    if "set hp" in lowered:
        return "hp"
    if "grant items" in lowered:
        return "sword"
    return ""


def _is_safe_ooc_refusal(text: str, key: str, kind: str) -> bool:
    if kind != "ooc":
        return False
    refusal_markers = ("cannot", "can't", "not", "unsupported", "no gameplay", "no state")
    return key in text and any(marker in text for marker in refusal_markers)


def _asserts_mechanical_effect(text: str) -> bool:
    effect_markers = (
        "hp is now",
        "hit points are now",
        "you regain",
        "you are healed",
        "the roll succeeds",
        "the dice show",
        "you gain a",
        "added to your inventory",
    )
    return any(marker in text for marker in effect_markers)
