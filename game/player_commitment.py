"""Current player commitment.

The resolution contract should follow the action the player commits to now,
and the person they commit to addressing. A supporting perception phrase,
a later intention, or an unresolved name must not become that commitment.
"""
from __future__ import annotations

import re

EXECUTED_NOW = "executed_now"
INTENDED_LATER = "intended_later"
CONDITIONAL = "conditional"
HYPOTHETICAL = "hypothetical"
CONTEMPLATED = "contemplated"

_EXPLICIT_SOCIAL_RE = re.compile(
    r"\b(?:ask|inquire|tell|question|request|speak(?:ing)?\s+(?:to|with)|talk(?:ing)?\s+(?:to|with))\b",
    re.IGNORECASE,
)
_INDEPENDENT_LISTEN_RE = re.compile(
    r"\blisten(?:ing|ed)?\s+(?:carefully\s+|closely\s+)?(?:at|through|toward|towards|for)\b",
    re.IGNORECASE,
)
_SPEECH_LISTEN_RE = re.compile(
    r"\blisten(?:ing|ed)?\b[^.?!]{0,80}\b(?:rumou?rs?|offering|what\s+(?:he|she|they)\b)\b",
    re.IGNORECASE,
)
_APPROACH_RE = re.compile(r"\bapproach(?:ing|es)?\b", re.IGNORECASE)
_SUPPORTING_WATCH_RE = re.compile(
    r"\bwhile\s+(?:i\s+)?(?:watch(?:ing)?|observ(?:e|ing)|glance|glancing)\b"
    r"|\bwatch(?:ing)?\s+(?:his|her|their)\s+reaction\b"
    r"|\b(?:keep(?:ing)?\s+my\s+voice\s+low|glance(?:ing)?\s+around)\b",
    re.IGNORECASE,
)
_LISTEN_OR_WATCH_RE = re.compile(
    r"\blisten(?:ing|ed)?\b|\bwatch(?:ing)?\b|\bobserv(?:e|ing)\b",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.?!])\s+")
_IF_SENTENCE_RE = re.compile(r"^\s*if\b", re.IGNORECASE)
_HYPOTHETICAL_RE = re.compile(r"\b(?:would|could)\b", re.IGNORECASE)
_CONDITIONAL_RE = re.compile(r"^\s*if\b|\bif\s+necessary\b", re.IGNORECASE)
_LATER_RE = re.compile(
    r"\b(?:later|afterwards)\b|\bafter\s+i\b|\bonce\s+i\b|\bwhen\s+i(?:'m| am)\s+done\b"
    r"|^\s*then\s+i(?:'ll| will)\s+(?:go|head|walk|leave|travel|follow)\b",
    re.IGNORECASE,
)
_CONTEMPLATED_RE = re.compile(
    r"\b(?:i|we)\s+might\b"
    r"|\b(?:maybe|perhaps)\s+i(?:'ll| will)?\b"
    r"|\b(?:i|we)\s+(?:consider|am considering|think about|am thinking about)\b",
    re.IGNORECASE,
)
_UNCOMMITTED_SPAN_RES = (
    re.compile(r"\bbefore\s+deciding\b[^.?!;]*", re.IGNORECASE),
    re.compile(r"\bdecid(?:e|ing)\s+whether\b[^.?!;]*", re.IGNORECASE),
    re.compile(
        r"\bwhether\s+to\s+(?:follow|go|walk|open|leave|enter|head|take|travel|climb|pay)\b[^.?!;]*",
        re.IGNORECASE,
    ),
    re.compile(r"\bif\s+necessary\b[^.?!]*", re.IGNORECASE),
)


def perception_is_supporting(text: str | None) -> bool:
    """True when listen/watch modifies a social commitment instead of being the act.

    An independent listen (at a door, for footsteps) still owns perception.
    """
    raw = str(text or "")
    if not raw.strip():
        return False
    independent = bool(_INDEPENDENT_LISTEN_RE.search(raw))
    explicit_social = bool(_EXPLICIT_SOCIAL_RE.search(raw))
    if independent and not explicit_social:
        return False
    if explicit_social and not independent and (
        re.search(r"\blisten", raw, re.IGNORECASE) or _SUPPORTING_WATCH_RE.search(raw)
    ):
        return True
    if not independent and _SPEECH_LISTEN_RE.search(raw) and _APPROACH_RE.search(raw):
        return True
    return False


def supporting_operations(text: str | None) -> tuple[str, ...]:
    raw = str(text or "")
    if perception_is_supporting(raw) and _LISTEN_OR_WATCH_RE.search(raw):
        return ("perceive",)
    return ()


_MODAL_MOVE_RE = re.compile(
    r"\b(?:whether|if)\b[^.?!]{0,80}\b(?:should|could|would|might)\b"
    r"[^.?!]{0,48}\b(?:go|head|walk|leave|travel|cross|return)\b",
    re.IGNORECASE,
)
_WHILE_MOVE_RE = re.compile(
    r"\bwhile\b|\bon\s+(?:my|our)\s+way\b|\bas\s+i\b",
    re.IGNORECASE,
)
_SOCIAL_ACT_RES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("thank", re.compile(r"\bthank(?:s|ed|ing)?\b", re.IGNORECASE)),
    ("farewell", re.compile(r"\b(?:farewell|goodbye|good-bye)\b", re.IGNORECASE)),
    ("ask", re.compile(r"\b(?:ask|inquire)s?\b", re.IGNORECASE)),
    ("tell", re.compile(r"\btell(?:s|ing)?\b", re.IGNORECASE)),
)
_QUOTED_SPEECH_RE = re.compile(r'["“]([^"”]{1,160})["”]')
_INFO_ACTS = frozenset({"ask"})


def _move_span(text: str) -> str:
    """Scene travel, not an approach to a person in the current scene.

    Uses the existing declared-travel patterns and the immediate
    verb-plus-preposition shape. "Leave the runner and step up to the guard"
    is not a destination.
    """
    raw = str(text or "")
    from game.intent_parser import _RE_SCENE_TRAVEL_DESTINATION, _first_declared_travel_pattern_match

    declared, _tag = _first_declared_travel_pattern_match(raw, 0)
    if declared:
        return " ".join(declared.group(0).split())
    match = _RE_SCENE_TRAVEL_DESTINATION.search(raw)
    if match:
        return " ".join(match.group(0).split())
    way = re.search(
        r"\bon\s+(?:my|our)\s+way\s+(?:to|toward|towards|for)\s+(?:the\s+)?[a-z][\w\s]{0,32}",
        raw,
        re.IGNORECASE,
    )
    if way:
        return " ".join(way.group(0).split())
    cross = re.search(
        r"\b(?:cross|crosses|crossing)\s+(?:the\s+|a\s+|an\s+)?[a-z][\w\s]{0,24}",
        raw,
        re.IGNORECASE,
    )
    if cross:
        return " ".join(cross.group(0).split())
    return ""


def _social_act(text: str) -> dict[str, str] | None:
    raw = str(text or "")
    for act, pattern in _SOCIAL_ACT_RES:
        match = pattern.search(raw)
        if match:
            start = max(0, match.start() - 24)
            return {"kind": "social", "act": act, "commitment": EXECUTED_NOW, "text": raw[start : match.end() + 48].strip()}
    return None


def _quoted_farewell(text: str) -> dict[str, str] | None:
    match = _QUOTED_SPEECH_RE.search(text or "")
    if not match:
        return None
    return {
        "kind": "social",
        "act": "farewell",
        "commitment": EXECUTED_NOW,
        "text": match.group(1).strip(),
    }


def executable_obligations(text: str | None) -> dict[str, object]:
    """Primary resolution plus at most the other committed act in an ordinary mixed line.

    The Resolution Contract keeps one operation. This record does not replace it.
    A move inside a whether/if-should question, or a conditional, hypothetical,
    or contemplated line, is not an executable travel obligation.
    """
    empty: dict[str, object] = {
        "primary": None,
        "mutation_owner": None,
        "sequence": [],
        "supporting": [],
    }
    committed = committed_world_text(text)
    if not committed:
        return empty
    from game.interpretation_proposal import ask_governs_embedded_act

    move_text = _move_span(committed)
    move = bool(move_text) and not ask_governs_embedded_act(committed) and not _MODAL_MOVE_RE.search(committed)
    social = _social_act(committed)
    if social is None and move:
        social = _quoted_farewell(str(text or ""))
    if not move:
        return empty
    travel = {
        "kind": "travel",
        "act": "travel",
        "commitment": EXECUTED_NOW,
        "text": move_text,
    }
    info = bool(social and social.get("act") in _INFO_ACTS)
    while_move = bool(_WHILE_MOVE_RE.search(committed))
    then = re.search(r"\bthen\b", committed, re.IGNORECASE)
    social_at = committed.lower().find(str((social or {}).get("act") or "\0"))
    move_at = committed.lower().find(move_text.lower()[:12]) if move_text else -1
    if info and while_move and (then is None or (move_at >= 0 and then.start() > move_at)):
        primary = "social"
        sequence = ["travel", "social"] if move_at >= 0 and social_at > move_at else ["social", "travel"]
        supporting = [travel]
    elif social and then is not None and move_at > then.start() and 0 <= social_at < then.start():
        primary = "travel"
        sequence = ["social", "travel"]
        supporting = [social]
    elif social and info and then is not None and social_at > then.start():
        primary = "social"
        sequence = ["travel", "social"]
        supporting = [travel]
    elif social:
        primary = "travel"
        sequence = ["social", "travel"] if social_at <= move_at else ["travel", "social"]
        supporting = [social]
    else:
        primary = "travel"
        sequence = ["travel"]
        supporting = []
    return {
        "primary": primary,
        "mutation_owner": "travel",
        "sequence": sequence,
        "supporting": supporting,
    }


def committed_travel_recorded(contract: object) -> bool:
    """True when the contract already recorded an executed travel obligation."""
    if not isinstance(contract, dict):
        construction = getattr(contract, "construction", None)
    else:
        construction = contract.get("construction")
    if not isinstance(construction, dict):
        return False
    record = construction.get("executable_obligations")
    if not isinstance(record, dict):
        return False
    if record.get("mutation_owner") == "travel" or record.get("primary") == "travel":
        return True
    supporting = record.get("supporting")
    if not isinstance(supporting, list):
        return False
    return any(
        isinstance(item, dict) and item.get("kind") == "travel" and item.get("commitment") == EXECUTED_NOW
        for item in supporting
    )


def _sentence_uncommitted(sentence: str) -> bool:
    raw = str(sentence or "").strip()
    if not raw:
        return False
    if _HYPOTHETICAL_RE.search(raw) and "?" in raw:
        return True
    if _IF_SENTENCE_RE.search(raw):
        return True
    if _LATER_RE.search(raw) and not re.search(r"\b(?:inspect|examine|check|ask)\b", raw, re.IGNORECASE):
        return True
    if _CONTEMPLATED_RE.search(raw) and not re.search(
        r"\b(?:inspect|examine|check|read|study)\b",
        raw,
        re.IGNORECASE,
    ):
        return True
    return False


def _mask_uncommitted_spans(sentence: str) -> str:
    masked = str(sentence or "")
    for pattern in _UNCOMMITTED_SPAN_RES:
        masked = pattern.sub(" ", masked)
    return " ".join(masked.split())


def committed_world_text(text: str | None) -> str:
    """Utterance with future, conditional, hypothetical, and undecided acts removed.

    A committed sequence (inspect, then follow) stays. Question content
    (ask whether the wagons are through) stays.
    """
    raw = str(text or "").strip()
    if not raw:
        return ""
    kept: list[str] = []
    for sentence in _SENTENCE_SPLIT_RE.split(raw):
        if _sentence_uncommitted(sentence):
            continue
        masked = _mask_uncommitted_spans(sentence)
        if masked:
            kept.append(masked)
    return " ".join(kept).strip()


def commitment_status(text: str | None) -> str:
    """Modality of the utterance's world-changing commitment."""
    if committed_world_text(text).strip():
        return EXECUTED_NOW
    raw = str(text or "")
    if _HYPOTHETICAL_RE.search(raw) and "?" in raw:
        return HYPOTHETICAL
    if _CONDITIONAL_RE.search(raw):
        return CONDITIONAL
    if _LATER_RE.search(raw):
        return INTENDED_LATER
    return CONTEMPLATED
