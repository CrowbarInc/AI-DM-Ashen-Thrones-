"""Shared text utilities for final emission: normalization, patterns, light HTML cleanup.

No policy orchestration — used by :mod:`game.final_emission_validators`,
:mod:`game.final_emission_repairs`, :mod:`game.response_policy_contracts`, and
:mod:`game.final_emission_gate`.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from game.diegetic_fallback_narration import render_global_scene_anchor_fallback


def _normalize_text(text: str | None) -> str:
    return " ".join(str(text or "").strip().split())


def _normalize_text_preserve_paragraphs(text: str | None) -> str:
    """Like ``_normalize_text`` but keeps ``\\n\\n`` paragraph breaks (strict-social dialogue + NA splits)."""
    raw = str(text or "").strip()
    if not raw:
        return ""
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    if not blocks:
        return ""
    return "\n\n".join(" ".join(part.split()) for part in blocks)


def _sanitize_output_text(text: str) -> str:
    if not text:
        return text

    text = text.replace("<br><br>", "\n\n")
    text = text.replace("<br />", "\n")
    text = text.replace("<br>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_terminal_punctuation(text: str) -> str:
    clean = _normalize_text(text).strip(" ,;")
    if not clean:
        return ""
    if not _has_terminal_punctuation(clean):
        clean += "."
    return clean


def _global_narrative_fallback_stock_line(scene: Dict[str, Any] | None, *, scene_id: str) -> str:
    alt = render_global_scene_anchor_fallback(scene, seed_key=scene_id or "fallback")
    if isinstance(alt, str) and _normalize_text(alt):
        return _normalize_terminal_punctuation(alt)
    return "For a breath, the scene holds while voices shift around you."


def _has_terminal_punctuation(text: str) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    if clean[-1] in ".!?":
        return True
    if clean[-1] in "\"')]}”’" and len(clean) > 1 and clean[-2] in ".!?":
        return True
    return False


def _capitalize_sentence_fragment(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    chars = list(clean)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.upper()
            break
    return "".join(chars)


_RESPONSE_TYPE_VALUES = {"dialogue", "answer", "action_outcome", "neutral_narration", "scene_opening"}
_ANSWER_DIRECT_PATTERNS = (
    re.compile(r"\b(?:yes|no|none|nothing|nowhere|someone|somebody|everyone|nobody)\b", re.IGNORECASE),
    re.compile(r"\b(?:don'?t know|do not know|cannot say|can'?t say|that'?s all i(?:'ve| have) got)\b", re.IGNORECASE),
    re.compile(r"\b(?:requires? a check|calls? for a check|need a more concrete|need a concrete|not established yet)\b", re.IGNORECASE),
    re.compile(r"\b(?:in earshot|nearby npc presence|estimated distance|about \d+\s+feet)\b", re.IGNORECASE),
    re.compile(r"\b(?:is armed|does not appear armed|no one else is clearly in earshot)\b", re.IGNORECASE),
    re.compile(r"\b(?:roll|sleight of hand|stealth|perception|diplomacy|intimidate|bluff)\b", re.IGNORECASE),
    re.compile(r"\b(?:east|west|north|south)\b", re.IGNORECASE),
    re.compile(r"\b(?:road|lane|gate|pier|market|checkpoint|milestone|fold)\b", re.IGNORECASE),
)
_ANSWER_FILLER_PATTERNS = (
    re.compile(r"\bfor a breath\b", re.IGNORECASE),
    re.compile(r"\bthe scene holds\b", re.IGNORECASE),
    re.compile(r"\bvoices shift around you\b", re.IGNORECASE),
    re.compile(r"\brain beads on stone\b", re.IGNORECASE),
    re.compile(r"\bthe truth is still buried\b", re.IGNORECASE),
    re.compile(r"\bnothing in the scene points\b", re.IGNORECASE),
)
_ACTION_RESULT_PATTERNS = (
    re.compile(r"\b(?:find|found|notice|noticed|spot|spotted|discover|discovered|reveal|revealed|turns? up|yields?)\b", re.IGNORECASE),
    re.compile(r"\b(?:arrive|arrives|reach|reaches|move|moves|shift|shifts|change|changes|opens|closes)\b", re.IGNORECASE),
    re.compile(r"\b(?:nothing new|already searched|requires? a check|calls? for a check|meets resistance)\b", re.IGNORECASE),
    re.compile(r"\b(?:fails?|failed|succeeds?|succeeded|result|effect|immediate)\b", re.IGNORECASE),
    re.compile(r"\b(?:clue|trail|mark|trace|scene)\b", re.IGNORECASE),
)
_AGENCY_SUBSTITUTE_PATTERNS = (
    re.compile(r"\byou (?:think|reflect|hesitate|wonder)\b", re.IGNORECASE),
    re.compile(r"\byou merely\b", re.IGNORECASE),
    re.compile(r"\byou only\b", re.IGNORECASE),
)
_ACTION_STOPWORDS = frozenset(
    {
        "the",
        "that",
        "this",
        "with",
        "from",
        "into",
        "over",
        "under",
        "then",
        "your",
        "their",
        "them",
        "they",
        "there",
        "here",
        "about",
        "while",
        "through",
        "would",
        "could",
        "should",
        "just",
        "still",
        "have",
        "been",
        "were",
        "what",
        "where",
        "when",
        "which",
        "who",
    }
)
