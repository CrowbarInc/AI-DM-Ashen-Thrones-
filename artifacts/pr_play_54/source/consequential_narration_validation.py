"""Deterministic authority check for quarantined investigation narration.

The check compares candidate claims in prose with facts the engine has already
authorized. It does not call a model, write campaign state, or authorize a
discovery. A passing result is not permission to show the prose to a player.

Uncertainty is not safety. REVIEW_REQUIRED and VALIDATION_ERROR both block a
player-facing pass when this gate is applied.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

PASS = "PASS"
FAIL = "FAIL"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
VALIDATION_ERROR = "VALIDATION_ERROR"

_STOP = frozenset({
    "a", "an", "the", "of", "and", "or", "to", "in", "on", "at", "by", "for",
    "with", "from", "you", "your", "that", "this", "it", "is", "are", "was",
    "were", "be", "as", "into", "onto", "near", "beside", "his", "her", "their",
    "he", "she", "they", "now", "then", "just", "still", "again", "more", "very",
    "small", "little", "newly", "immediately", "before", "after", "under",
    "over", "out", "up", "down", "its", "but", "not", "no", "without", "within",
    "across", "through", "about", "while", "when", "where", "who", "whom",
    "one", "once", "toward", "towards", "around", "along", "upon", "off",
    "into", "past", "away", "back", "here", "there", "only", "own", "another",
})
_CANON = {
    "western": "west", "westward": "west", "eastern": "east", "eastward": "east",
    "northern": "north", "northward": "north", "southern": "south", "southward": "south",
    "sundown": "dusk", "sunset": "dusk", "evening": "dusk",
    "rounds": "patrol", "round": "patrol", "patrols": "patrol", "patrolling": "patrol",
    "path": "road", "paths": "road", "track": "road", "tracks": "road", "trail": "road",
    "route": "road", "routes": "road",
    "sentry": "guard", "watchman": "guard", "guards": "guard",
    "took": "take", "taken": "take", "taking": "take", "takes": "take",
    "seen": "see", "saw": "see", "sees": "see",
    "makes": "make", "made": "make", "making": "make",
    "footprints": "print", "footprint": "print", "prints": "print",
    "keys": "key", "coins": "coin", "crowns": "crown",
}
_OPPOSITE = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "northwest": "southeast", "southeast": "northwest",
    "northeast": "southwest", "southwest": "northeast",
}
_DIRECTION = {
    "north": "north", "northern": "north", "south": "south", "southern": "south",
    "east": "east", "eastern": "east", "west": "west", "western": "west",
    "northwest": "northwest", "northeastern": "northeast", "northeast": "northeast",
    "southwestern": "southwest", "southwest": "southwest",
    "southeastern": "southeast", "southeast": "southeast",
    "northwestern": "northwest",
}
_TOPIC = frozenset({
    "patrol", "guard", "road", "print", "route", "milestone", "crate", "crates",
    "trail", "clue", "notice", "board",
})
_CONSEQUENTIAL_HEADS = frozenset({
    "key", "compass", "coin", "crown", "letter", "map", "clue", "route", "passage",
    "door", "doorway", "cache", "compartment", "tunnel", "cellar", "vault",
    "weapon", "sword", "dagger", "potion", "poison", "token", "ledger", "journal",
    "culprit", "murderer", "killer", "thief", "traitor", "spy", "quest",
    "objective", "mission", "confession",
})
_SURFACE = frozenset({
    "grain", "texture", "surface", "color", "colour", "smell", "sound", "edge",
    "corner", "crack", "stain", "splinter", "wear", "patina", "shadow", "light",
    "rain", "mud", "dust", "wood", "paper", "ink", "wax", "sense", "impression",
    "glimpse", "moment", "chill", "breath", "view", "look", "feeling", "attention",
    "time", "air", "wind", "cold", "heat", "water", "rainwater", "lint", "dirt",
    "grime", "scent", "noise",
})
_INCIDENTAL_OBJECT = re.compile(
    r"\b(?:dust|lint|rain|rainwater|water|light|shadow|mud|smell|scent|cold|heat|dirt|grime|air|wind)\b",
    re.IGNORECASE,
)
_HEDGE = re.compile(
    r"\b(?:sounds?\s+like|looks?\s+like|looks?\s+as\s+though|feels?\s+like|smells?\s+(?:like|of)|"
    r"as\s+if|as\s+though|you\s+wonder|wonder\s+whether|whether\s+someone|perhaps|maybe|"
    r"suggests?|seems?(?:\s+to)?|you\s+suspect|supposedly)\b",
    re.IGNORECASE,
)
_FINITE_CLAIM = re.compile(
    r"\b(?:confesses|confessed|admits|admitted|succeeds|opens|discover|discovers|discovered|"
    r"find|finds|found|acquire|acquires|acquired|uncover|uncovers)\b",
    re.IGNORECASE,
)
_SIMILE = re.compile(
    r"\b(?:sounds?\s+like|looks?\s+like|feels?\s+like|smells?\s+like|as\s+if|as\s+though)\b",
    re.IGNORECASE,
)
_MODAL = re.compile(r"\b(?:might|could|may|would|should)\s*$", re.IGNORECASE)
_NEGATED = re.compile(r"\b(?:not|never|n't|no|without)\s*$", re.IGNORECASE)
_PREPOSITION = re.compile(
    r"\b(?:beneath|under|below|behind|inside|beside|near|on|in|from|at|among|into|upon|"
    r"with|without|past|through|across|over|along|before)\b",
    re.IGNORECASE,
)
_LEADING = re.compile(
    r"^(?:(?:a|an|the|your|newly|discovered|found|recovered|acquired|small|little|another)\s+)+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SemanticAuthority:
    """Facts the narrator may rely on. Absence is not a hidden-fact catalog.

    Restricted entries are explicit withholdings supplied by the caller. The
    quarantined projection usually has none, because those strings never enter
    the narration request. A claim can still be unauthorized without one.
    """

    observable_scene: tuple[str, ...] = ()
    authorized_discoveries: tuple[str, ...] = ()
    authorized_outcomes: tuple[str, ...] = ()
    restricted: tuple[str, ...] = ()
    success: bool | None = None
    items_added: tuple[str, ...] = ()
    items_removed: tuple[str, ...] = ()
    routes_unlocked: tuple[str, ...] = ()
    objectives_completed: tuple[str, ...] = ()
    conditions_applied: tuple[str, ...] = ()
    conditions_removed: tuple[str, ...] = ()
    dialogue: tuple[str, ...] = ()


def authority_from_anchored(contract) -> SemanticAuthority:
    """Read an anchored investigation. Do not copy hidden fixture fields."""
    view = contract.outcome
    outcomes = tuple(anchor.text for anchor in contract.anchors if anchor.source == "engine_status")
    if view.consequences:
        outcomes = outcomes + (view.consequences,)
    return SemanticAuthority(
        observable_scene=tuple(view.observations),
        authorized_discoveries=tuple(view.revealed) + tuple(view.known),
        authorized_outcomes=outcomes,
        success=view.success if isinstance(view.success, bool) else None,
    )


def _canon(word: str) -> str:
    word = word.casefold()
    if word in _CANON:
        return _CANON[word]
    if word.endswith("ing") and len(word) > 6:
        word = word[:-3]
    elif word.endswith("ed") and len(word) > 5:
        word = word[:-2]
    elif word.endswith("s") and not word.endswith("ss") and len(word) > 4:
        word = word[:-1]
    return _CANON.get(word, word)


def _tokens(text: str) -> list[str]:
    found = []
    for word in re.findall(r"[a-z0-9']+", str(text or "").casefold()):
        if word in _STOP:
            continue
        token = _canon(word)
        if token in _STOP or len(token) < 3:
            continue
        found.append(token)
    return found


def _authority_text(authority: SemanticAuthority) -> tuple[str, ...]:
    grants = (
        authority.items_added + authority.items_removed + authority.routes_unlocked
        + authority.objectives_completed + authority.conditions_applied
        + authority.conditions_removed
    )
    rendered = tuple(item.replace("_", " ") for item in grants)
    return (
        authority.observable_scene + authority.authorized_discoveries
        + authority.authorized_outcomes + authority.dialogue + rendered
    )


def _pool(authority: SemanticAuthority) -> set[str]:
    pool: set[str] = set()
    for text in _authority_text(authority):
        pool.update(_tokens(text))
    return pool


def _covered(text: str, authority: SemanticAuthority) -> bool:
    wanted = _tokens(text)
    if not wanted:
        return False
    pool = _pool(authority)
    return all(token in pool for token in wanted)


def _entity(text: str) -> str:
    cleaned = str(text or "").strip(" .,:;\"'")
    cleaned = re.split(
        r"\b(?:without|before|after|while|and then)\b|\band\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    cleaned = _PREPOSITION.split(cleaned, maxsplit=1)[0]
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = _LEADING.sub("", cleaned).strip()
    return cleaned.strip(" .,:;\"'")


def _granted(text: str, grants: tuple[str, ...]) -> bool:
    have = set(_tokens(text))
    for grant in grants:
        need = _tokens(grant.replace("_", " "))
        if need and all(token in have for token in need):
            return True
    return False


def _head(text: str) -> str:
    tokens = _tokens(_entity(text))
    return tokens[-1] if tokens else ""


def _modal(clause: str, start: int) -> bool:
    return bool(_MODAL.search(clause[max(0, start - 16):start]))


def _negated(clause: str, start: int) -> bool:
    window = clause[max(0, start - 28):start]
    return bool(_NEGATED.search(window) or re.search(r"\b(?:do not|don't|does not|doesn't|never)\b", window, re.IGNORECASE))


def _hedged(clause: str) -> bool:
    if _FINITE_CLAIM.search(clause):
        return False
    return bool(_HEDGE.search(clause) or _SIMILE.search(clause))


def _directions(text: str) -> set[str]:
    found = set()
    for word in re.findall(r"[a-z]+", str(text or "").casefold()):
        canon = _DIRECTION.get(word)
        if canon:
            found.add(canon)
    return found


def _claim(category: str, reason: str, text: str, decision: str = FAIL, epistemic: str = "assertion") -> dict:
    return {
        "category": category,
        "reason": reason,
        "decision": decision,
        "epistemic": epistemic,
        "text": text.strip(),
    }


def _clauses(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?;])\s+|;\s+|,\s+(?:but|and)\s+", text, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]


def _conditional(clause: str) -> bool:
    return bool(re.match(r"^(?:if|unless)\b", clause.strip(), re.IGNORECASE))


def _negative_search(clause: str, authority: SemanticAuthority) -> list[dict]:
    """A denied specific object is not an investigation failure.

    "You find nothing" contradicts an authorized discovery. "You do not find a
    silver key" only refuses one unauthorized object.
    """
    broad_failure = re.search(
        r"\byou\s+(?:find|discover|learn|uncover)\s+nothing\b"
        r"|\byou\s+(?:find|discover)\s+no\s+(?:clue|sign|trace|evidence|thing)\b"
        r"|\byou\s+(?:do not|don't|never)\s+(?:find|discover|learn|uncover)\s+anything\b",
        clause,
        re.IGNORECASE,
    )
    if broad_failure is None:
        return []
    if authority.success is True and authority.authorized_discoveries:
        return [_claim("mechanical_outcome", "false_mechanical_failure", clause, epistemic="negation")]
    return []


def _presuppositions(clause: str, authority: SemanticAuthority) -> list[dict]:
    claims = []
    pattern = re.compile(
        r"\b(?:the|your)\s+((?:newly\s+)?(?:discovered|found|recovered|acquired)\s+[a-z][\w\s-]{0,40}?)"
        r"\s+(?:secured|in hand|in your|should|rests|opens)\b"
        r"|\bthe\s+([a-z][\w\s-]{0,32}?)\s+you\s+(?:recovered|found|discovered|acquired|picked up|pocketed)\b"
        r"|\bwith the\s+((?:newly\s+)?(?:discovered|found|recovered)\s+[a-z][\w\s-]{0,40}?)\s+secured\b",
        re.IGNORECASE,
    )
    for match in pattern.finditer(clause):
        raw = next(group for group in match.groups() if group)
        entity = _entity(raw)
        if _covered(entity, authority):
            continue
        claims.append(_claim("discovery", "unauthorized_discovery", clause, epistemic="presupposition"))
    return claims


def _object_after(clause: str, pattern: str) -> tuple[re.Match[str] | None, str]:
    match = re.search(pattern, clause, re.IGNORECASE)
    if match is None:
        return None, ""
    return match, _entity(match.group(1) if match.lastindex else match.group(0))


def _discovery(clause: str, authority: SemanticAuthority) -> list[dict]:
    if re.search(r"\byou\s+find\s+yourself\s+(?:inside|within)\b", clause, re.IGNORECASE):
        return []
    strong = (
        r"\byou\s+(?:now\s+)?(?:discover|uncover|locate|recover|come across|pick up)\s+"
        r"(?!yourself\b)(.+)$"
    )
    weak = r"\byou\s+(?:now\s+)?(?:find|notice|spot)\s+(?!yourself\b)(.+)$"
    revealed = r"\bresolves into\s+((?:a|an)\s+.+)$"
    read_that = r"\byou\s+read\s+that\s+(.+)$"
    for pattern, mode in ((strong, "strong"), (weak, "weak"), (revealed, "strong"), (read_that, "information")):
        match, entity = _object_after(clause, pattern)
        if match is None:
            continue
        if _modal(clause, match.start()) or _negated(clause, match.start()):
            continue
        if re.match(r"^(?:nothing|none|no)\b", entity, re.IGNORECASE):
            continue
        head = _head(entity)
        if head in _SURFACE or (_INCIDENTAL_OBJECT.search(entity) and head in _SURFACE):
            continue
        if mode == "weak" and head not in _CONSEQUENTIAL_HEADS:
            continue
        if _covered(entity, authority):
            continue
        reason = "unauthorized_hidden_location" if re.search(
            r"\b(?:hidden|secret|concealed)\b", entity, re.IGNORECASE
        ) else "unauthorized_discovery"
        category = "hidden_location" if reason == "unauthorized_hidden_location" else "discovery"
        return [_claim(category, reason, clause)]
    return []


def _possession(clause: str, authority: SemanticAuthority) -> list[dict]:
    match = re.search(
        r"\b(.+?)\s+(?:is|are)\s+now\s+yours\b"
        r"|\b(.+?)\s+(?:now\s+)?(?:rests?|lies?)\s+(?:among|in|inside)\s+your\s+"
        r"(?:belongings|possessions|things|gear|inventory|pack|bag)\b"
        r"|\b(?:in your hand|in your palm)\s*:\s*(.+)$"
        r"|\byour\s+(?:purse|inventory|pack|bag)\s+(?:now\s+)?(?:holds?|contains?)\s+(.+)",
        clause,
        re.IGNORECASE,
    )
    if match is None or _modal(clause, match.start()) or _negated(clause, match.start()):
        return []
    raw = next(group for group in match.groups() if group)
    entity = _entity(raw)
    if not entity or _INCIDENTAL_OBJECT.fullmatch(entity) or _head(entity) in _SURFACE:
        return []
    if _INCIDENTAL_OBJECT.search(entity) and _head(entity) in _SURFACE:
        return []
    # A discovered fact is not an inventory grant. Possession needs items_added.
    if _granted(entity, authority.items_added):
        return []
    return [_claim("inventory", "unauthorized_acquisition", clause)]


def _inventory_verb(clause: str, authority: SemanticAuthority) -> list[dict]:
    match = re.search(
        r"\byou\s+(?:now\s+)?(?:receive|acquire|obtain|collect|pocket|stash|claim)\s+"
        r"(?!a\s+(?:moment|look|breath|sense|glimpse)\b)(.+)$"
        r"|\byou\s+take\s+(?:the|a|an)\s+(?!moment\b|look\b|breath\b|step\b)(.+)$"
        r"|\byou\s+are\s+(?:now\s+)?(?:\w+\s+){0,4}richer\b",
        clause,
        re.IGNORECASE,
    )
    if match is None or _modal(clause, match.start()) or _negated(clause, match.start()):
        return []
    if re.search(r"\bricher\b", clause, re.IGNORECASE):
        if not any(token in _pool(authority) for token in ("coin", "crown", "currency")):
            return [_claim("inventory", "unauthorized_acquisition", clause)]
        return []
    entity = _entity(match.group(1) or match.group(2) or "")
    if not entity or _head(entity) in _SURFACE:
        return []
    if _granted(entity, authority.items_added):
        return []
    return [_claim("inventory", "unauthorized_acquisition", clause)]


def _identity(clause: str, authority: SemanticAuthority) -> list[dict]:
    match = re.search(
        r"\byou\s+(?:recognize|identify|name)\b[^.!?]{0,80}\b(?:culprit|murderer|killer|thief|traitor|spy)\b"
        r"|\b(?:culprit|murderer|killer|thief|traitor|spy)\s+is\b"
        r"|\bis\s+the\s+(?:culprit|murderer|killer|thief|traitor|spy)\b"
        r"|\bthe one who\s+(?:killed|murdered|stole|sold)\b"
        r"|\bsettles\s+who\b"
        r"|\bwho\s+(?:was|is)\s+responsible\b"
        r"|\bin disguise\b",
        clause,
        re.IGNORECASE,
    )
    if match is None or _modal(clause, match.start()) or _negated(clause, match.start()):
        return []
    if _covered(clause, authority):
        return []
    return [_claim("npc_identity", "unauthorized_identity", clause)]


def _confession(clause: str, authority: SemanticAuthority) -> list[dict]:
    finite = re.search(r"\b(?:confesses|confessed)\b", clause, re.IGNORECASE)
    admits = re.search(r"\b(?:admits|admitted)\b", clause, re.IGNORECASE)
    admission = re.search(r"\b(?:his|her|their|an|the|whispered)\s+admission\b", clause, re.IGNORECASE)
    if finite is None and admits is None and admission is None:
        return []
    if admits is not None and not re.search(
        r"\b(?:murder\w*|kill\w*|sold|stole|guilt\w*|route|patrol|crime|theft)\b",
        clause,
        re.IGNORECASE,
    ):
        admits = None
    if admission is not None and not re.search(
        r"\b(?:murder\w*|kill\w*|sold|stole|guilt\w*|route|patrol|crime)\b",
        clause,
        re.IGNORECASE,
    ):
        admission = None
    anchor = finite or admits or admission
    if anchor is None or _modal(clause, anchor.start()) or _negated(clause, anchor.start()):
        return []
    if any(clause.casefold() in item.casefold() or _covered(clause, authority) for item in authority.dialogue):
        if _covered(clause, authority):
            return []
    if _covered(clause, authority):
        return []
    return [_claim("npc_admission", "unauthorized_confession", clause)]


def _quoted_killing(clause: str, authority: SemanticAuthority) -> list[dict]:
    if not re.search(r"[\"“][^\"”]{0,160}\b(?:i killed|i murdered|i stole|i sold the)\b", clause, re.IGNORECASE):
        return []
    if _covered(clause, authority):
        return []
    return [_claim("npc_admission", "unauthorized_confession", clause)]


def _motive(clause: str, authority: SemanticAuthority) -> list[dict]:
    if not re.search(
        r"\bsecretly\s+(?:serves|works for|reports to|betrays)\b|\bhopes to betray\b",
        clause,
        re.IGNORECASE,
    ):
        return []
    if _covered(clause, authority):
        return []
    return [_claim("hidden_information", "hidden_disclosure", clause)]


def _outcome(clause: str, authority: SemanticAuthority) -> list[dict]:
    claims = []
    success = re.search(
        r"\byou\s+succeed\b(?!\s+in\s+(?:keeping|staying|remaining)\b)"
        r"|\byou\s+successfully\s+(?:uncover|find|open|identify|learn|discover|recover)\b"
        r"|\b(?:your\s+)?(?:search|investigation|attempt)\s+succeeds\b",
        clause,
        re.IGNORECASE,
    )
    if success is not None and not _modal(clause, success.start()) and not _negated(clause, success.start()):
        uncovered = re.search(
            r"\b(?:uncovering|finding|discovering|opening|learning|identifying|recovering|locating|naming)\s+(.+)$",
            clause,
            re.IGNORECASE,
        )
        extra = uncovered is not None and not _covered(_entity(uncovered.group(1)), authority)
        if authority.success is False:
            claims.append(_claim("mechanical_outcome", "false_mechanical_success", clause))
        elif extra:
            claims.append(_claim("discovery", "unauthorized_discovery", clause))
    failure = re.search(
        r"\byou\s+fail\b|\b(?:your\s+)?(?:search|investigation|attempt)\s+fails\b"
        r"|\byou\s+learn\s+nothing\b|\bnothing\s+new\s+is\s+(?:established|found|learned|discovered)\b",
        clause,
        re.IGNORECASE,
    )
    if (
        failure is not None
        and not _modal(clause, failure.start())
        and not _negated(clause, failure.start())
        and authority.success is True
        and authority.authorized_discoveries
    ):
        claims.append(_claim("mechanical_outcome", "false_mechanical_failure", clause))
    resisted = re.search(r"\bthe lock resists\b|\bstays locked\b|\bwill not open\b", clause, re.IGNORECASE)
    if resisted is not None and authority.success is True and not _covered(clause, authority):
        claims.append(_claim(
            "mechanical_outcome", "ambiguous_consequential", clause, decision=REVIEW_REQUIRED,
        ))
    return claims


def _access(clause: str, authority: SemanticAuthority) -> list[dict]:
    if re.search(r"\b(?:should|would|could|might|may)\s+open\b", clause, re.IGNORECASE):
        return []
    match = re.search(
        r"\b(?:passage|door|doorway|gate|hatch|tunnel|cellar|chamber)\b[^.!?;]{0,48}"
        r"\b(?:opens|swings open|slides aside|unlocks|clicks open|gives way)\b"
        r"|\b(?:opens|swings open|slides aside|unlocks|clicks open)\b[^.!?;]{0,48}"
        r"\b(?:passage|door|doorway|gate|hatch|tunnel|cellar|chamber)\b"
        r"|\byou\s+(?:open|unlock|enter|step into)\s+(?:a|an|the)\s+"
        r"(?:hidden\s+|secret\s+|concealed\s+)?(?:passage|door|doorway|cellar|chamber|tunnel|vault)\b"
        r"|\byou\s+find\s+yourself\s+(?:inside|within)\s+(?:the\s+)?(?:crypt|vault|chamber|tunnel|cellar)\b"
        r"|\bthe lock clicks open\b"
        r"|\byou\s+(?:now\s+)?stand\s+inside\s+the\s+[a-z]+"
        r"|\byou\s+(?:arrive at|arrive in|reach the|enter the)\s+[a-z]",
        clause,
        re.IGNORECASE,
    )
    if match is None or _modal(clause, match.start()) or _negated(clause, match.start()):
        return []
    if _covered(clause, authority) or _granted(clause, authority.routes_unlocked):
        return []
    if re.search(r"\bstand\s+inside\s+the\s+(?:rain|wind|crowd|light|shadow)\b", clause, re.IGNORECASE):
        return []
    if re.search(
        r"\b(?:arrive at|arrive in|reach|enter)\s+(?:the\s+|a\s+|an\s+)?(?:conclusion|decision|understanding|agreement|sense)\b",
        clause,
        re.IGNORECASE,
    ):
        return []
    reason = "false_mechanical_success" if authority.success is False and re.search(
        r"\b(?:opens|clicks open|swings open)\b", clause, re.IGNORECASE
    ) else "unauthorized_access"
    category = "mechanical_outcome" if reason == "false_mechanical_success" else "location_access"
    return [_claim(category, reason, clause)]


def _hidden_place(clause: str, authority: SemanticAuthority) -> list[dict]:
    match = re.search(
        r"\b(?:hidden|secret|concealed)\s+(compartment|cache|tunnel|passage|chamber|cellar|entrance|door|doorway|stairway|vault)\b"
        r"|\b(?:hiding|hidden)\s+in\s+the\s+[a-z]",
        clause,
        re.IGNORECASE,
    )
    if match is None or _hedged(clause):
        return []
    if _covered(clause, authority):
        return []
    return [_claim("hidden_location", "unauthorized_hidden_location", clause)]


def _route_assertion(clause: str, authority: SemanticAuthority) -> list[dict]:
    match = re.search(
        r"\b(?:route|path|trail|passage)\s+leads?\s+(?:into|to|toward|north|south|east|west)\b"
        r"|\b(?:prints|tracks|footprints|trail)\s+lead\w*\s+(?:straight\s+)?to\s+(?:the\s+)?(.+)$"
        r"|\b(?:prints|tracks|footprints)\s+belong\s+to\s+(.+)$",
        clause,
        re.IGNORECASE,
    )
    if match is None or _hedged(clause):
        return []
    destination = ""
    if match.lastindex:
        destination = match.group(match.lastindex) or ""
    if destination and _covered(destination, authority) and re.search(r"\bbelong\b|\blead", match.group(0), re.IGNORECASE) is None:
        return []
    if destination and _covered(clause, authority):
        return []
    if re.search(r"\bbelong\b|\blead", clause, re.IGNORECASE) and not _relation_supported(clause, authority):
        return [_claim("discovery", "unauthorized_discovery", clause)]
    if not _covered(clause, authority):
        return [_claim("discovery", "unauthorized_discovery", clause)]
    return []


def _relation_supported(clause: str, authority: SemanticAuthority) -> bool:
    """A named person or place in an authorized fact does not grant a new relation."""
    for source in authority.authorized_discoveries + authority.authorized_outcomes:
        if re.search(r"\bbelong", clause, re.IGNORECASE) and re.search(r"\bbelong", source, re.IGNORECASE):
            return _covered(clause, authority)
        if re.search(r"\blead", clause, re.IGNORECASE) and re.search(r"\blead", source, re.IGNORECASE):
            return _covered(clause, authority)
    return False


def _count(clause: str, authority: SemanticAuthority) -> list[dict]:
    match = re.search(
        r"\b(?:exactly|precisely)\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
        r"(travelers|travellers|prints|footprints|guards|people|men|culprits)\b",
        clause,
        re.IGNORECASE,
    )
    if match is None:
        return []
    number = re.search(r"\b(?:exactly|precisely)\s+(\w+)", clause, re.IGNORECASE)
    if number is not None and _canon(number.group(1)) in _pool(authority):
        return []
    return [_claim("discovery", "unauthorized_discovery", clause)]


def _quest(clause: str, authority: SemanticAuthority) -> list[dict]:
    if not re.search(
        r"\b(?:completes?|advances?|updates?|finishes)\s+(?:your\s+|the\s+)?(?:[\w]+\s+){0,3}"
        r"(?:quest|objective|mission)\b"
        r"|\byou\s+complete\s+(?:the\s+)?(?:[\w]+\s+){0,4}(?:quest|objective|mission)\b"
        r"|\b(?:quest|objective|mission)\s+(?:is now complete|is complete|advances)\b",
        clause,
        re.IGNORECASE,
    ):
        return []
    if authority.objectives_completed and (
        _covered(clause, authority) or _granted(clause, authority.objectives_completed)
    ):
        return []
    return [_claim("quest", "unauthorized_quest", clause)]


def _condition(clause: str, authority: SemanticAuthority) -> list[dict]:
    if not re.search(
        r"\bwounds?\s+(?:knit|close|heal)\b"
        r"|\b(?:poison|curse)\s+(?:has|have)\s+(?:worn off|faded|lifted|left)\b"
        r"|\byou\s+are\s+no\s+longer\s+(?:poisoned|wounded|injured|cursed|bleeding|stunned|sick)\b"
        r"|\byou\s+(?:become|are now)\s+(?:poisoned|wounded|injured|healed|cursed|bleeding|stunned)\b",
        clause,
        re.IGNORECASE,
    ):
        return []
    grants = authority.conditions_applied + authority.conditions_removed
    if grants and (_covered(clause, authority) or _granted(clause, grants)):
        return []
    return [_claim("condition", "unauthorized_condition", clause)]


def _false_certainty(clause: str, authority: SemanticAuthority) -> list[dict]:
    if not re.search(r"\b(?:definitely|certainly|proves|proven|confirmed|without doubt)\b", clause, re.IGNORECASE):
        return []
    uncertain = [
        source for source in authority.authorized_discoveries + authority.authorized_outcomes
        if re.search(r"\b(?:unclear|unknown|cannot|incomplete)\b", source, re.IGNORECASE)
    ]
    if not uncertain:
        return []
    have = set(_tokens(clause))
    if not any(have & set(_tokens(source)) for source in uncertain):
        return []
    return [_claim("discovery", "discovery_contradiction", clause)]


def _environment(clause: str, authority: SemanticAuthority) -> list[dict]:
    if not re.search(
        r"\bordered the gates sealed\b|\bthe gates (?:are|were|stay) sealed\b",
        clause,
        re.IGNORECASE,
    ):
        return []
    if _covered(clause, authority):
        return []
    return [_claim("environment", "unauthorized_environment", clause)]


def _expansion(clause: str, authority: SemanticAuthority) -> list[dict]:
    match = re.search(r"\b(unprotected|unguarded)\b", clause, re.IGNORECASE)
    if match is None or _hedged(clause):
        return []
    if _canon(match.group(1)) in _pool(authority):
        return []
    return [_claim("discovery", "consequential_expansion", clause)]


def _contradiction(sentence: str, authority: SemanticAuthority) -> list[dict]:
    sent_dirs = _directions(sentence)
    if not sent_dirs:
        return []
    sent_topics = set(_tokens(sentence)) & _TOPIC
    for source in authority.authorized_discoveries + authority.authorized_outcomes:
        src_dirs = _directions(source)
        if not src_dirs or not (sent_topics & (set(_tokens(source)) & _TOPIC)):
            continue
        for direction in sent_dirs:
            opposite = _OPPOSITE.get(direction)
            if opposite and opposite in src_dirs and direction not in src_dirs:
                return [_claim("discovery", "discovery_contradiction", sentence)]
    return []


def _restricted(text: str, authority: SemanticAuthority) -> list[dict]:
    if not authority.restricted:
        return []
    have = set(_tokens(text))
    raw = text.casefold()
    for fact in authority.restricted:
        fact_tokens = _tokens(fact)
        if fact.casefold() in raw:
            return [_claim("hidden_information", "hidden_disclosure", text)]
        if len(fact_tokens) >= 4 and all(token in have for token in fact_tokens):
            return [_claim("hidden_information", "hidden_disclosure", text)]
        if " " not in fact.strip() and len(fact.strip()) >= 8 and fact.casefold() in raw:
            return [_claim("hidden_information", "hidden_disclosure", text)]
    return []


def _identifier(clause: str, authority: SemanticAuthority) -> list[dict]:
    if re.search(r"\b(?:GM_ONLY|hidden fact:|do not reveal|the secret is)\b", clause, re.IGNORECASE):
        return [_claim("hidden_information", "hidden_disclosure", clause)]
    if re.search(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b", clause):
        return [_claim("hidden_information", "hidden_disclosure", clause)]
    return []


def _ambiguous(clause: str, authority: SemanticAuthority) -> list[dict]:
    if re.search(r"\b(?:compartment|cache|lock|lid)\s+yields\b", clause, re.IGNORECASE):
        if not _covered(clause, authority):
            return [_claim("discovery", "ambiguous_consequential", clause, decision=REVIEW_REQUIRED)]
    if re.search(r"\byou have what you came for\b", clause, re.IGNORECASE) and not authority.items_added:
        return [_claim("inventory", "unauthorized_acquisition", clause, epistemic="presupposition")]
    return []


def _clause_claims(clause: str, authority: SemanticAuthority) -> list[dict]:
    if _conditional(clause):
        return []
    claims = _presuppositions(clause, authority)
    claims.extend(_negative_search(clause, authority))
    if _hedged(clause):
        return claims
    for extractor in (
        _discovery, _possession, _inventory_verb, _identity, _confession, _quoted_killing,
        _motive, _outcome, _access, _hidden_place, _route_assertion, _count, _quest,
        _condition, _false_certainty, _environment, _expansion, _ambiguous, _identifier,
    ):
        claims.extend(extractor(clause, authority))
    return claims


def _dedupe(claims: list[dict]) -> list[dict]:
    kept = []
    seen = set()
    for claim in claims:
        key = (claim["reason"], claim["decision"], claim["text"].casefold())
        if key in seen:
            continue
        seen.add(key)
        kept.append(claim)
    return kept


def validate_consequential_narration(text: object, authority: object) -> dict:
    """Classify narration against an authority snapshot.

    The return value never includes a grant. Callers that treat anything other
    than PASS as safe are misusing the result.
    """
    if not isinstance(text, str) or not isinstance(authority, SemanticAuthority):
        return {
            "decision": VALIDATION_ERROR,
            "reasons": ["invalid_validation_input"],
            "claims": [],
            "provider_requests": 0,
            "coverage": "deterministic_frames_not_semantic_proof",
        }
    try:
        claims: list[dict] = []
        claims.extend(_restricted(text, authority))
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) or [text]:
            if not sentence.strip():
                continue
            claims.extend(_contradiction(sentence, authority))
            for clause in _clauses(sentence):
                claims.extend(_clause_claims(clause, authority))
        claims = _dedupe(claims)
    except Exception as exc:
        return {
            "decision": VALIDATION_ERROR,
            "reasons": ["validator_exception"],
            "error_type": type(exc).__name__,
            "claims": [],
            "provider_requests": 0,
            "coverage": "deterministic_frames_not_semantic_proof",
        }
    fails = [claim["reason"] for claim in claims if claim["decision"] == FAIL]
    reviews = [claim["reason"] for claim in claims if claim["decision"] == REVIEW_REQUIRED]
    if fails:
        decision = FAIL
        reasons = list(dict.fromkeys(fails))
    elif reviews:
        decision = REVIEW_REQUIRED
        reasons = list(dict.fromkeys(reviews))
    else:
        decision = PASS
        reasons = []
    return {
        "decision": decision,
        "reasons": reasons,
        "claims": claims,
        "provider_requests": 0,
        "coverage": "deterministic_frames_not_semantic_proof",
    }


def apply_consequential_gate(audit: Mapping, decision: Mapping) -> dict:
    """Reject on FAIL, REVIEW_REQUIRED, and VALIDATION_ERROR. Never grant a pass."""
    merged = dict(audit)
    merged["consequential_validation"] = dict(decision)
    if decision.get("decision") != PASS:
        merged["hard_valid"] = False
        merged["contract_satisfying"] = False
        reason = "consequential_" + str(decision.get("decision") or VALIDATION_ERROR).lower()
        reasons = list(merged.get("reasons") or [])
        if reason not in reasons:
            reasons.append(reason)
        merged["reasons"] = reasons
    return merged
