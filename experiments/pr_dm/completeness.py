"""Structural completeness checks for selective interpretation routing.

These checks request interpretation. They do not execute actions.
They extend the stored PR-DK checks without replacing them.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

_QUOTE = re.compile(r'"([^"]*)"|“([^”]*)”')
_TEMPORAL_SPLIT = re.compile(r"\b(?:and\s+then|then)\b", re.IGNORECASE)
_FRONT_SEQUENCE = re.compile(r"\b(?:after|before|once)\b(.+?)[,;]\s*(.+)", re.IGNORECASE)
_DIRECTION = re.compile(
    r"\b(?:over|across|up|down|closer|near|back)\s+to\b|\btoward(?:s)?\b",
    re.IGNORECASE,
)
_OBJECT = re.compile(r"\b(?:it|them|that|this|the|a|an)\b", re.IGNORECASE)
_NEGATED_CLAUSE = re.compile(r"\b(?:do\s+not|don't|will\s+not|won't|never|not)\b", re.IGNORECASE)
_HYPOTHETICAL = re.compile(r"\b(?:if|suppose|imagine)\b", re.IGNORECASE)
_PLAYER_SPEECH = re.compile(
    r"\bI\s+(?:say|said|saying|ask|asked|tell|told|remark|remarked|joke|joked)\b"
    r"|\b(?:as\s+a\s+joke|just\s+kidding|jokingly)\b",
    re.IGNORECASE,
)
_QUOTED_ACTION = re.compile(
    r"\b(?:walk|step|go|head|approach|move|pry|pull|remove|attack|strike|stab)\b",
    re.IGNORECASE,
)
_PHYSICAL_RESOLVERS = frozenset({"travel", "combat", "world_action", "exploration"})
_SKIP = frozenset(
    {
        "i",
        "we",
        "you",
        "he",
        "she",
        "they",
        "please",
        "try",
        "trying",
        "attempt",
        "attempting",
        "to",
        "just",
        "then",
        "and",
        "will",
        "shall",
        "can",
        "could",
        "would",
        "should",
        "a",
        "an",
        "the",
        "my",
        "our",
        "your",
        "his",
        "her",
        "their",
        "over",
        "up",
        "down",
        "across",
        "closer",
        "near",
        "back",
        "of",
        "off",
        "on",
        "at",
        "from",
        "for",
        "with",
        "it",
        "them",
        "that",
        "this",
        "free",
        "do",
        "does",
        "did",
        "not",
        "only",
        "after",
        "before",
        "once",
        "toward",
        "towards",
    }
)


def _outside_quotes(text: str) -> str:
    return _QUOTE.sub(" ", text)


def _quoted_spans(text: str) -> list[str]:
    return [left or right for left, right in _QUOTE.findall(text)]


def _head(clause: str) -> str:
    for word in re.findall(r"[a-z']+", clause.lower()):
        if word not in _SKIP:
            return word
    return ""


def temporal_clauses(text: str) -> list[str]:
    """Split unquoted text on temporal sequencers.

    Bare conjunctions are not sequencers. Hypothetical frames suppress the
    split so a conditional is not treated as two attempted actions.
    """
    raw = _outside_quotes(text)
    if _HYPOTHETICAL.search(raw):
        return []
    parts = [part.strip(" ,;.") for part in _TEMPORAL_SPLIT.split(raw) if part.strip(" ,;.")]
    if len(parts) >= 2:
        return parts
    match = _FRONT_SEQUENCE.search(raw)
    if not match:
        return []
    return [match.group(1).strip(" ,;."), match.group(2).strip(" ,;.")]


def _sequence_recorded(independent: Mapping[str, Any] | None, construction: Mapping[str, Any] | None) -> bool:
    if isinstance(construction, Mapping):
        secondary = construction.get("secondary_operations") or []
        obligations = construction.get("executable_obligations") if isinstance(construction.get("executable_obligations"), Mapping) else {}
        sequence = obligations.get("sequence") or []
        if len(list(secondary)) >= 1 or len(list(sequence)) >= 2:
            return True
    if isinstance(independent, Mapping) and independent.get("multiple_independent_action_clauses"):
        return True
    return False


def temporally_sequenced_components(text: str) -> bool:
    clauses = temporal_clauses(text)
    if len(clauses) < 2:
        return False
    heads = {_head(clause) for clause in clauses}
    heads.discard("")
    if len(heads) < 2:
        return False
    if _NEGATED_CLAUSE.search(clauses[-1]):
        return False
    directed = [clause for clause in clauses if _DIRECTION.search(clause)]
    if not directed:
        return False
    others = [clause for clause in clauses if clause not in directed]
    if not others:
        return False
    return any(_OBJECT.search(clause) for clause in others)


def quoted_speech_boundary(text: str) -> bool:
    """Player-framed quotation. A quoted sign or document is not enough."""
    if not _quoted_spans(text):
        return False
    return bool(_PLAYER_SPEECH.search(_outside_quotes(text)))


def quoted_action_resolver_mismatch(text: str, resolver: str) -> bool:
    """True when a physical resolver consumed verbs that occur only inside a player quote."""
    if str(resolver) not in _PHYSICAL_RESOLVERS:
        return False
    insides = _quoted_spans(text)
    if not insides:
        return False
    unquoted = _outside_quotes(text)
    if not _PLAYER_SPEECH.search(unquoted):
        return False
    inside = " ".join(insides)
    if not _QUOTED_ACTION.search(inside):
        return False
    if _QUOTED_ACTION.search(unquoted):
        return False
    return True


def refined_checks(
    text: str,
    resolver: str,
    *,
    independent: Mapping[str, Any] | None = None,
    construction: Mapping[str, Any] | None = None,
) -> dict[str, bool]:
    sequenced = temporally_sequenced_components(text)
    covered = _sequence_recorded(independent, construction)
    return {
        "temporally_sequenced_components": sequenced,
        "action_contract_uncovered": sequenced and not covered,
        "quoted_speech_boundary": quoted_speech_boundary(text),
        "quoted_action_resolver_mismatch": quoted_action_resolver_mismatch(text, resolver),
    }


def refined_route(checks: Mapping[str, bool]) -> bool:
    """Only uncovered sequences and quote/resolver mismatches escalate."""
    return bool(checks.get("action_contract_uncovered") or checks.get("quoted_action_resolver_mismatch"))
