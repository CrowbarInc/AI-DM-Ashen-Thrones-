"""Classify generated propositions with the PR-BN authority taxonomy.

A sentence may be an authoritative fact, a bounded incidental detail, an NPC
claim, or a consequential proposal. Hard validation uses that class. It does
not rewrite the sentence.

Operational rules are a family: a concrete schedule, access condition, official
levy, or standing legal mandate. The match is structural. It is not a list of
forbidden nouns.
"""
from __future__ import annotations

import re

from game.bounded_improvisation import (
    CONSEQUENTIAL_KIND,
    INCIDENTAL_KIND,
    NPC_CLAIM_KIND,
)

AUTHORITATIVE_KIND = "authoritative_fact"

EPISTEMIC_WORLD = "world_truth"
EPISTEMIC_GROUNDED = "grounded"
EPISTEMIC_RUMOR = "rumor"
EPISTEMIC_HEARSAY = "hearsay"
EPISTEMIC_UNCERTAIN = "uncertain"
EPISTEMIC_SPECULATIVE = "speculative"

FAMILY_SCHEDULE = "schedule"
FAMILY_ACCESS = "access"
FAMILY_LEVY = "levy"
FAMILY_LEGAL = "legal"
FAMILY_IDENTITY = "identity"
FAMILY_BIOGRAPHY = "biography"
FAMILY_GEOGRAPHY = "geography"
FAMILY_HIDDEN_INFORMATION = "hidden_information"
FAMILY_NPC_ACTION = "npc_action"
FAMILY_DISCOVERY = "discovery"
FAMILY_INCIDENTAL = "incidental"
FAMILY_NONE = "none"

PRICE_OFFICIAL = "official"
PRICE_MUNDANE = "mundane"
PRICE_NONE = "none"

_SENTENCE_RE = re.compile(r"[^.!?]+(?:[.!?]+|$)")
_QUOTE_RE = re.compile(r'["“]([^"”]+)["”]')

_HEDGE_RE = re.compile(
    r"\b(?:i heard|i have heard|i've heard|from what i (?:heard|gather)|"
    r"they say|people say|word is|rumou?r|supposedly|allegedly|"
    r"someone said|told me|i was told|"
    r"might|may be|maybe|perhaps|could|sometimes|"
    r"i think|i guess|not sure|"
    r"i can't swear|i cannot swear)\b",
    re.IGNORECASE,
)
_HEARSAY_RE = re.compile(
    r"\b(?:heard|rumou?r|they say|people say|word is|told me|i was told|"
    r"(?:travelers|people|someone|he|she|they)\s+says?)\b",
    re.IGNORECASE,
)
_SPECULATIVE_RE = re.compile(
    r"\b(?:i think|i guess|might|may be|maybe|perhaps|could)\b",
    re.IGNORECASE,
)
_NOT_AN_ASSERTION_RE = re.compile(
    r"\b(?:can't|cannot|can not|don't|do not|won't|will not|unable to)\s+"
    r"(?:say|name|swear|give|tell|share)\b"
    r"|\b(?:does not|doesn't|do not|don't|not)\s+"
    r"(?:specify|name|state|list|post|establish|fix)\b"
    r"|\bno\s+(?:fixed|posted|set)\s+(?:toll|time|schedule|curfew|price)\b",
    re.IGNORECASE,
)
_STATE_CHANGE_RE = re.compile(
    r"\b(?:clos(?:e|es|ed|ing)|shut(?:s|ting)?|bar(?:s|red)?|"
    r"watch\s+changes?|be\s+indoors|"
    r"gates?\s+close|passage\s+(?:ends|stops)|"
    r"must\s+clear|"
    r"(?:the\s+)?curfew\s+(?:is|begins|starts|falls|runs|holds|lifts|ends)|"
    r"(?:enforce[sd]?|enforcing)\s+(?:the\s+)?curfew)\b",
    re.IGNORECASE,
)
_DEFINITE_TIME_RE = re.compile(
    r"\b(?:at|by|until|before|after|around)\s+(?:the\s+)?"
    r"(?:(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last)\s+bell|"
    r"\d{1,2}:\d{2}|dusk|dawn|sunset|sunrise|nightfall)\b"
    r"|\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last)\s+bell\b"
    r"|\buntil\s+(?:morning|dawn|dusk|nightfall)\b",
    re.IGNORECASE,
)
_COARSE_BOUND_RE = re.compile(
    r"\buntil\s+(?:morning|dawn|dusk|nightfall)\b",
    re.IGNORECASE,
)
_SPECIFIC_ANCHOR_RE = re.compile(
    r"\b(?:(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last)\s+bell|"
    r"\d{1,2}:\d{2}|dusk sharp|sunset|sunrise)\b",
    re.IGNORECASE,
)
_DEONTIC_RE = re.compile(
    r"\b(?:need(?:s|ed)?|must|required|have to|has to|only)\b",
    re.IGNORECASE,
)
_CREDENTIAL_RE = re.compile(
    r"\b(?:papers|writs?|permits?|passes|tokens?|documents?|charters?|"
    r"membership|guild\s+members?)\b",
    re.IGNORECASE,
)
_ACCESS_RE = re.compile(
    r"\b(?:enter|entry|pass(?:age)?|cross|admission|get through|may enter)\b",
    re.IGNORECASE,
)
_OFFICIAL_LEVY_RE = re.compile(
    r"\b(?:tolls?|taxes|tax|duties|duty|levies|levy|customs)\b",
    re.IGNORECASE,
)
_AMOUNT_RE = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an)\s+"
    r"(?:silver|gold|copper|coppers|coins?)\b",
    re.IGNORECASE,
)
_VENDOR_GOOD_RE = re.compile(
    r"\b(?:bowl|stew|ale|meal|room|bread|mug|soup|drink|lodging|beer)\b",
    re.IGNORECASE,
)
_CLASS_PAYER_RE = re.compile(
    r"\b(?:travelers?|everyone|anybody|anyone|citizens?|merchants?)\b",
    re.IGNORECASE,
)
_PAY_RE = re.compile(r"\b(?:pay|pays|paid|costs?|priced|charges?)\b", re.IGNORECASE)
_LEGAL_RE = re.compile(
    r"\b(?:the law requires|by official order|the penalty is|it is forbidden|"
    r"punishable by|mandatory that)\b",
    re.IGNORECASE,
)
_INCIDENTAL_RE = re.compile(
    r"\b(?:smells?|tastes?|aroma|cloak|sleeve|mud|rain|gesture|nods?|shrugs?|"
    r"onion|barley|pepper|broth|worn|threadbare|stool|lantern)\b",
    re.IGNORECASE,
)
_BIOGRAPHY_RE = re.compile(
    r"\b(?:was\s+born|born\s+in|grew\s+up|served\s+for\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twenty)\s+years?|"
    r"once\s+served|formerly\s+served|used\s+to\s+serve)\b",
    re.IGNORECASE,
)
_GEOGRAPHY_RE = re.compile(
    r"\b(?:milestone|crossroads?|roads?|routes?|paths?|tunnels?|passages?|keeps?|bridges?|towers?)\b"
    r"[^.!?]{0,80}\b(?:lies?|stands?|sits?|runs?|leads?|passes?)?\s*(?:east|west|north|south|beyond|beneath|under|past|into)\b"
    r"|\b(?:east|west|north|south|beyond|beneath|under|past|into)\b[^.!?]{0,80}\b(?:milestone|crossroads?|roads?|routes?|paths?|tunnels?|passages?|keeps?|bridges?|towers?)\b",
    re.IGNORECASE,
)
_HIDDEN_INFORMATION_RE = re.compile(
    r"\b(?:secret|hidden|buried|sealed)\s+(?:tunnel|passage|map|door|vault|route|cache|letter|ledger|clue|fact)\b"
    r"|\b(?:tunnel|passage|map|door|vault|route|cache|letter|ledger|clue)\b[^.!?]{0,80}\b(?:hidden|secret|buried|sealed)\b",
    re.IGNORECASE,
)
_NPC_ACTION_RE = re.compile(
    r"\b(?:captain|guard|baker|merchant|runner|watchman|sentry|npc|he|she|they)\b[^.!?]{0,80}"
    r"\b(?:unlocks?|opens?|closes?|locks?|lets?\s+you\s+pass|allows?\s+you\s+(?:through|in|past|to\s+pass)|"
    r"gives?\s+you|hands?\s+you|grants?\s+you|issues?\s+you|escorts?\s+you|attacks?|orders?)\b",
    re.IGNORECASE,
)
_DISCOVERY_RE = re.compile(
    r"\byou\s+(?:discover|find|spot|uncover|notice|learn|realize)\b[^.!?]{0,80}"
    r"\b(?:hidden|secret|map|clue|tunnel|passage|vault|cache|letter|ledger|evidence)\b",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(
    r"\b(?:in a (?:few|couple of) minutes|in a moment|shortly|any minute)\b",
    re.IGNORECASE,
)
# A role whose identity changes an investigation, not a capitalization list.
_CONSEQUENTIAL_ROLE_RE = re.compile(
    r"\b(?:(?:missing\s+)?patrol\s+leader|murderer|assassin|"
    r"(?:ash\s+compact\s+)?spy|faction\s+leader|"
    r"official\s+who\s+(?:issued|ordered))\b",
    re.IGNORECASE,
)
_PROPER_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")
_NAME_SKIP = frozenset(
    {
        "the", "a", "an", "this", "that", "missing", "patrol", "leader", "roster",
        "house", "ash", "compact", "gate", "notice", "board", "guard", "captain",
        "i", "no", "one", "they", "he", "she",
    }
)
_SELF_NAME_RE = re.compile(
    r"\b(?:i am|i'm|my name is|call me)\s+([A-Z][a-z]+)\b",
)


def _clean(text: str) -> str:
    return " ".join(str(text or "").split())


def _sentences(text: str) -> list[str]:
    raw = _clean(text)
    if not raw:
        return []
    found = [_clean(match.group(0)) for match in _SENTENCE_RE.finditer(raw)]
    return [sentence for sentence in found if sentence]


def _time_token(sentence: str) -> str:
    match = _DEFINITE_TIME_RE.search(sentence)
    if not match:
        return ""
    token = match.group(0).lower()
    return re.sub(r"^(?:at|by|until|before|after|around)\s+(?:the\s+)?", "", token).strip()


def _corpus_has(corpus: str, token: str) -> bool:
    if not token:
        return False
    return token.lower() in str(corpus or "").lower()


def epistemic_frame(sentence: str) -> str:
    """How the sentence presents its content. Not whether the content is true."""
    if _NOT_AN_ASSERTION_RE.search(sentence):
        return ""
    if _HEARSAY_RE.search(sentence):
        return EPISTEMIC_HEARSAY if not re.search(r"\brumou?r\b", sentence, re.IGNORECASE) else EPISTEMIC_RUMOR
    if re.search(r"\brumou?r\b", sentence, re.IGNORECASE):
        return EPISTEMIC_RUMOR
    if _SPECULATIVE_RE.search(sentence) or _HEDGE_RE.search(sentence):
        return EPISTEMIC_UNCERTAIN
    return EPISTEMIC_WORLD


def _proper_names(sentence: str) -> list[str]:
    names: list[str] = []
    for match in _PROPER_NAME_RE.finditer(sentence or ""):
        name = match.group(1)
        parts = [part for part in name.split() if part.lower() not in _NAME_SKIP]
        if not parts:
            continue
        cleaned = " ".join(parts)
        if cleaned not in names:
            names.append(cleaned)
    return names


def consequential_identity_assertion(sentence: str) -> bool:
    """A proper name bound to a consequential role, asserted as identification.

    A name by itself is not consequential. The name and the role have to be
    the same proposition. Self-introduction without that role is not one.
    """
    if _SELF_NAME_RE.search(sentence) and not _CONSEQUENTIAL_ROLE_RE.search(sentence):
        return False
    role = _CONSEQUENTIAL_ROLE_RE.search(sentence or "")
    if not role:
        return False
    for match in _PROPER_NAME_RE.finditer(sentence or ""):
        parts = [part for part in match.group(1).split() if part.lower() not in _NAME_SKIP]
        if not parts:
            continue
        start = min(role.start(), match.start())
        end = max(role.end(), match.end())
        if end - start > 96:
            continue
        between = sentence[start:end]
        if re.search(r"\b(?:is|was|named|called|name|lists?|roster)\b", between, re.IGNORECASE):
            return True
    return False


def _family(sentence: str) -> str:
    if _NOT_AN_ASSERTION_RE.search(sentence):
        return FAMILY_NONE
    if consequential_identity_assertion(sentence):
        return FAMILY_IDENTITY
    if _LEGAL_RE.search(sentence):
        return FAMILY_LEGAL
    schedule = bool(_STATE_CHANGE_RE.search(sentence) and _DEFINITE_TIME_RE.search(sentence))
    if schedule:
        return FAMILY_SCHEDULE
    access = bool(_DEONTIC_RE.search(sentence) and _CREDENTIAL_RE.search(sentence))
    if access or (
        _DEONTIC_RE.search(sentence)
        and _ACCESS_RE.search(sentence)
        and _CREDENTIAL_RE.search(sentence)
    ):
        return FAMILY_ACCESS
    if _official_levy(sentence):
        return FAMILY_LEVY
    if _DISCOVERY_RE.search(sentence):
        return FAMILY_DISCOVERY
    if _HIDDEN_INFORMATION_RE.search(sentence):
        return FAMILY_HIDDEN_INFORMATION
    if _NPC_ACTION_RE.search(sentence):
        return FAMILY_NPC_ACTION
    if _BIOGRAPHY_RE.search(sentence):
        return FAMILY_BIOGRAPHY
    if _GEOGRAPHY_RE.search(sentence):
        return FAMILY_GEOGRAPHY
    if _INCIDENTAL_RE.search(sentence) or (_DURATION_RE.search(sentence) and not _STATE_CHANGE_RE.search(sentence)):
        return FAMILY_INCIDENTAL
    if price_class(sentence) == PRICE_MUNDANE:
        return FAMILY_INCIDENTAL
    return FAMILY_NONE


def _official_levy(sentence: str) -> bool:
    if re.search(
        r"\b(?:is not|isn't|not fixed|no fixed|cannot name|can't name|won't name|will not name)\b",
        sentence,
        re.IGNORECASE,
    ):
        return False
    if _VENDOR_GOOD_RE.search(sentence) and not _OFFICIAL_LEVY_RE.search(sentence):
        return False
    if not _AMOUNT_RE.search(sentence) and not re.search(r"\bthe\s+(?:toll|tax|duty)\s+is\b", sentence, re.IGNORECASE):
        return False
    if _OFFICIAL_LEVY_RE.search(sentence):
        return True
    return bool(_CLASS_PAYER_RE.search(sentence) and _PAY_RE.search(sentence) and _AMOUNT_RE.search(sentence))


def price_class(text: str) -> str:
    """Mundane vendor prices stay improvisable. Official levies do not."""
    sentence = _clean(text)
    if not sentence or not _AMOUNT_RE.search(sentence):
        if _OFFICIAL_LEVY_RE.search(sentence) and re.search(r"\bthe\s+(?:toll|tax|duty)\s+is\b", sentence, re.IGNORECASE):
            return PRICE_OFFICIAL
        return PRICE_NONE
    if _official_levy(sentence):
        return PRICE_OFFICIAL
    if _VENDOR_GOOD_RE.search(sentence) or re.search(r"\b(?:costs?|priced|sells for|a bowl)\b", sentence, re.IGNORECASE):
        return PRICE_MUNDANE
    if re.search(r"\b(?:about|around|maybe|might|i hear|i heard)\b", sentence, re.IGNORECASE):
        return PRICE_MUNDANE
    return PRICE_NONE


def _schedule_anchor_grounded(sentence: str, corpus: str, response: str) -> bool:
    token = _time_token(sentence)
    if not token:
        return False
    corpus_l = str(corpus or "").lower()
    institutional = bool(_STATE_CHANGE_RE.search(corpus_l) or re.search(r"\b(?:close|curfew|watch)\b", corpus_l))
    if _corpus_has(corpus, token) and institutional:
        return True
    if _COARSE_BOUND_RE.search(sentence) and not _SPECIFIC_ANCHOR_RE.search(sentence):
        for other in _sentences(response):
            specific = _SPECIFIC_ANCHOR_RE.search(other)
            if specific and _corpus_has(corpus, specific.group(0)) and institutional:
                return True
    return False


def _identity_grounded(sentence: str, corpus: str) -> bool:
    role = _CONSEQUENTIAL_ROLE_RE.search(sentence)
    names = _proper_names(sentence)
    if not role or not names:
        return False
    corpus_l = str(corpus or "").lower()
    if role.group(0).lower() not in corpus_l:
        return False
    return any(name.lower() in corpus_l for name in names)


def _grounded(sentence: str, family: str, corpus: str, response: str) -> bool:
    if family == FAMILY_IDENTITY:
        return _identity_grounded(sentence, corpus)
    if family == FAMILY_SCHEDULE:
        return _schedule_anchor_grounded(sentence, corpus, response)
    if family == FAMILY_ACCESS:
        match = _CREDENTIAL_RE.search(sentence)
        return bool(match and _corpus_has(corpus, match.group(0)))
    if family == FAMILY_LEVY:
        amount = _AMOUNT_RE.search(sentence)
        if amount:
            return _corpus_has(corpus, amount.group(0))
        return False
    if family == FAMILY_LEGAL:
        match = _LEGAL_RE.search(sentence)
        return bool(match and _corpus_has(corpus, match.group(0)))
    if family in {
        FAMILY_BIOGRAPHY,
        FAMILY_GEOGRAPHY,
        FAMILY_HIDDEN_INFORMATION,
        FAMILY_NPC_ACTION,
        FAMILY_DISCOVERY,
    }:
        norm = _clean(sentence).lower().strip(" .!?")
        if not norm:
            return False
        corpus_l = str(corpus or "").lower()
        if norm in corpus_l:
            return True
        tokens = [tok for tok in re.findall(r"[a-z0-9']+", norm) if len(tok) >= 4]
        corpus_tokens = set(re.findall(r"[a-z0-9']+", corpus_l))
        return bool(tokens and set(tokens).issubset(corpus_tokens))
    return False


def _kind_for(family: str, frame: str, grounded: bool) -> str:
    if family == FAMILY_NONE and frame in {EPISTEMIC_HEARSAY, EPISTEMIC_RUMOR, EPISTEMIC_UNCERTAIN, EPISTEMIC_SPECULATIVE}:
        return NPC_CLAIM_KIND
    if family in {FAMILY_NONE, FAMILY_INCIDENTAL}:
        return INCIDENTAL_KIND if family == FAMILY_INCIDENTAL else ""
    if frame in {EPISTEMIC_HEARSAY, EPISTEMIC_RUMOR, EPISTEMIC_UNCERTAIN, EPISTEMIC_SPECULATIVE}:
        return NPC_CLAIM_KIND
    if grounded:
        return AUTHORITATIVE_KIND
    return CONSEQUENTIAL_KIND


def classify_propositions(text: str | None, *, authored_corpus: str = "") -> list[dict[str, object]]:
    """One record per sentence that carries an authority class."""
    response = _clean(text or "")
    rows: list[dict[str, object]] = []
    for sentence in _sentences(response):
        frame = epistemic_frame(sentence)
        family = _family(sentence)
        hearsay = frame in {EPISTEMIC_HEARSAY, EPISTEMIC_RUMOR, EPISTEMIC_UNCERTAIN, EPISTEMIC_SPECULATIVE}
        if not frame or (family == FAMILY_NONE and not hearsay):
            continue
        grounded = _grounded(sentence, family, authored_corpus, response) if family not in {FAMILY_NONE, FAMILY_INCIDENTAL} else False
        kind = _kind_for(family, frame, grounded)
        if not kind:
            continue
        consequential = kind == CONSEQUENTIAL_KIND or (
            family in {FAMILY_SCHEDULE, FAMILY_ACCESS, FAMILY_LEVY, FAMILY_LEGAL} and kind != INCIDENTAL_KIND
        )
        rows.append(
            {
                "text": sentence,
                "kind": kind,
                "epistemic_status": EPISTEMIC_GROUNDED if kind == AUTHORITATIVE_KIND else frame,
                "grounded": bool(grounded),
                "consequential": bool(consequential and kind != INCIDENTAL_KIND),
                "family": family,
            }
        )
    return rows


def unauthorized_authoritative_rules(text: str | None, authored_corpus: str = "") -> list[dict[str, object]]:
    """World-truth operational rules the corpus does not already establish."""
    return [
        row
        for row in classify_propositions(text, authored_corpus=authored_corpus)
        if row.get("kind") == CONSEQUENTIAL_KIND
    ]
