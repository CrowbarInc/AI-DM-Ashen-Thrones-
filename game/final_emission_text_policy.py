"""Canonical validator policy vocabulary for final emission text checks.

Response-type values and regex pattern tuples consumed by
:mod:`game.final_emission_validators`, :mod:`game.response_policy_contracts`,
and gate-layer contract modules.

BV13A: extracted from ``game.final_emission_text`` compat barrel.
"""
from __future__ import annotations

import re

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
