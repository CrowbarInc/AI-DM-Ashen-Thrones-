"""Bounded incidental interlocutors under PR-BN authority.

A player reference is a proposed interaction target. This module decides
whether that target is already canonical, may exist as a minimal incidental
person, or must be refused. It does not invent biographies, and it does not
let player language establish consequential world truth.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping, Sequence

from game.bounded_improvisation import (
    CONSEQUENTIAL_TERMS,
    HIDDEN_INFO_TERMS,
    ensure_bounded_improvisation_ledger,
    validate_bounded_improvisation_proposal,
)

BIND_CANONICAL = "bound_canonical"
BIND_INCIDENTAL = "bound_incidental"
BIND_UNRESOLVED = "unresolved"
BIND_AMBIGUOUS = "ambiguous"
BIND_REJECTED = "rejected_consequential"

CLASS_CANONICAL = "canonical_established"
CLASS_INCIDENTAL = "permitted_bounded_incidental"
CLASS_CONSEQUENTIAL = "unsupported_consequential"
CLASS_AMBIGUOUS = "ambiguous_unresolved"

_POPULATED_RE = re.compile(
    r"\b(?:crowd|crowds|traffic|refugees|travelers|travellers|wagons|market|"
    r"square|street|tavern|dock|patrons|residents|people|gathering|bustle|"
    r"throng|queue|clamor|shoppers|vendors)\b",
    re.IGNORECASE,
)
_ISOLATED_RE = re.compile(
    r"\b(?:sealed|abandoned|deserted|uninhabited|nobody|no one)\b"
    r"|\bempty\b"
    r"|\blocked\b.{0,32}\b(?:crypt|tomb|chamber)\b"
    r"|\b(?:isolated|private|royal)\b.{0,32}\b(?:shrine|chamber|crypt|ruin)\b"
    r"|\b(?:crypt|ruin|ruins)\b.{0,48}\b(?:empty|sealed|abandoned|deserted)\b",
    re.IGNORECASE,
)
_PLOT_ASSERTION_RE = re.compile(
    r"\bwho\s+(?:killed|murdered|slew|ordered|betrayed|poisoned|assassinated)\b"
    r"|\b(?:killed|murdered|ordered)\s+the\b"
    r"|\b(?:working|works|worked)\s+for\b"
    r"|\bknows?\s+the\s+(?:secret|hidden)\b",
    re.IGNORECASE,
)
_AUTHORITY_OFFICE_RE = re.compile(
    r"\b(?:king|queen|duke|baron)(?:'s|s)?\s+(?:secret\s+)?(?:adviser|advisor|commander|minister)\b"
    r"|\b(?:secret|hidden)\s+(?:adviser|advisor|commander)\b"
    r"|\bcommander\s+of\s+the\b"
    r"|\bmagistrate\b"
    r"|\bofficer\s+who\b"
    r"|\brebel\s+cell\b",
    re.IGNORECASE,
)
_LEADING = frozenset(
    {"the", "a", "an", "that", "this", "one", "of", "passing", "nearby", "nearest", "some"}
)
_CLAUSE_CUT_RE = re.compile(
    r"\b(?:whether|if|what|how|when|why|because|so|whatever|while)\b|,",
    re.IGNORECASE,
)
_WH_RELATIVE_RE = re.compile(r"\b(?:who|that|which)\s+[a-z']+\b", re.IGNORECASE)
_OTHER_RELATIVE_RE = re.compile(r"\b(?:he|she|they)\s+[a-z']+\b", re.IGNORECASE)
_PLAYER_CLAUSE_RE = re.compile(r"\b(?:i|we)\s+[a-z']+\b", re.IGNORECASE)
_FINITE_RE = re.compile(
    r"\b(?:is|are|was|were|am|be|been|lingered|linger|lean|leans|leaned|"
    r"went|left|pass|passed|moving|did|does|do)\b",
    re.IGNORECASE,
)
_PRONOUN_START_RE = re.compile(r"^(?:i|i'm|they|them|he|she|him|her|we|you)\b", re.IGNORECASE)
_PREP_START_RE = re.compile(
    r"^(?:for|under|toward|towards|into|past|across|with|without|about)\b",
    re.IGNORECASE,
)
_PARTICIPLE_RE = re.compile(
    r"\b(?:carrying|holding|sweeping|wearing|standing|watching|walking|working|waiting|"
    r"blocking|sitting|leaning|looking|stacked)\b",
    re.IGNORECASE,
)
_PURPOSE_INFINITIVE_RE = re.compile(r"\s+to\s+[a-z']+(?:\s+with)?\s*$", re.IGNORECASE)
_TRAILING_MODIFIER_RE = re.compile(
    r"\s+(?:by|near|behind|beside|from|with|at|on|in|for|next\s+to|in\s+front\s+of|to)\s+.+$",
    re.IGNORECASE,
)
_DETERMINER_RE = re.compile(
    r"^(?:the|a|an|that|this|one|some|nearby|first|tired|old|passing)\b",
    re.IGNORECASE,
)
# Semantic class of the head. This is not an occupation whitelist: an unknown
# common-noun head can still denote a person. These heads cannot.
_NONPERSON_HEADS = frozenset(
    {
        "inn",
        "tavern",
        "gate",
        "market",
        "board",
        "road",
        "crate",
        "room",
        "rumor",
        "rumour",
        "price",
        "passage",
        "patrol",
        "rule",
        "fee",
        "coin",
        "tax",
        "curfew",
        "yard",
        "underbrush",
        "brush",
        "patch",
        "pace",
        "track",
        "mark",
        "crest",
        "window",
        "door",
        "coinage",
        "notice",
        "barrel",
        "wall",
        "banner",
        "rain",
        "wagon",
        "crowd",
        "queue",
        "step",
        "stone",
        "sign",
        "paper",
        "mud",
        "sky",
        "ground",
        "street",
        "square",
        "bridge",
        "lantern",
        "roster",
        "floor",
        "ceiling",
        "shop",
        "house",
        "hall",
        "alley",
        "dock",
        "pier",
        "town",
        "city",
        "quarter",
        "courtyard",
        "stable",
        "fortress",
        "counter",
        "path",
        "route",
        "fringe",
        "shelter",
        "meal",
    }
)
_ACTION_HEADS = frozenset(
    {
        "see",
        "inspect",
        "find",
        "read",
        "follow",
        "examine",
        "search",
        "visit",
        "ask",
        "question",
        "speak",
        "lean",
        "linger",
        "pass",
        "look",
        "head",
        "walk",
        "check",
        "study",
        "watch",
        "listen",
        "enter",
        "barter",
        "earn",
        "pay",
        "meet",
        "hear",
        "learn",
        "leave",
        "tell",
        "say",
        "move",
        "go",
        "wait",
    }
)
_PRONOUN_HEADS = frozenset(
    {"i", "me", "you", "he", "she", "him", "her", "they", "them", "we", "it"}
)
# Closed grammatical classes for nominal structure. These are not a
# person/non-person vocabulary. A compass token is a locative adjunct, so it
# cannot be selected as the noun the phrase denotes.
_DETERMINER_TOKENS = frozenset(
    {
        "the", "a", "an", "that", "this", "these", "those", "some", "one",
        "my", "your", "his", "her", "their", "our", "its",
    }
)
_PREPOSITION_TOKENS = frozenset(
    {
        "of", "by", "near", "behind", "beside", "from", "with", "at", "on",
        "in", "for", "to", "under", "toward", "towards", "into", "past",
        "across", "along", "down", "through", "over", "above", "below",
        "around", "about", "without", "onto", "upon", "off", "via", "next",
    }
)
_LOCATIVE_ADJUNCTS = frozenset(
    {
        "upstairs", "downstairs", "ahead", "overhead", "nearby", "ashore",
        "abroad", "indoors", "outdoors", "here", "there",
    }
)
_PRENOMINAL_ADJECTIVES = frozenset(
    {
        "old", "red", "tired", "muddy", "young", "wet", "dry", "cold", "hot",
        "dark", "small", "large", "big", "new", "long", "short", "high", "low",
        "quiet", "loud", "ragged", "nearby", "first", "wooden", "thin", "thick",
        "heavy", "fresh", "dirty", "clean", "empty", "full", "blue", "green",
        "white", "black", "grey", "gray", "brown", "steep", "narrow", "wide",
        "poor", "rich", "sick", "lost", "still", "passing", "nearest",
    }
)
# Roles whose shape is not agentive. Morphology covers porter, cooper,
# lamplighter, dockworker, innkeeper. This set is not an occupation list.
_SOCIAL_HEADS = frozenset(
    {
        "woman", "women", "man", "men", "guard", "merchant", "sentry",
        "spy", "wizard", "assassin", "patron", "magistrate", "child",
        "boy", "girl", "person", "captain", "stranger",
    }
)
# Right-hand compound pieces that are people only with a left noun.
# "stable hand" is a person. "hand" alone is not.
_COMPOUND_PERSON_RIGHT = frozenset({"hand", "hands"})
_AGENTIVE_SUFFIX_RE = re.compile(r"(?:er|or|ist)$")
_COMPASS_RE = re.compile(r"^(?:north|south|east|west)(?:east|west)?$")
_COORD_NOMINAL_RE = re.compile(
    r"\b(?:and|or)\b\s+(?:the|a|an|that|this|these|those)\b",
    re.IGNORECASE,
)
_QUANTIFIER_OF_RE = re.compile(
    r"^(?:one|some|any|either|both|few|several|many|all)\s+of\s+"
    r"(?:the\s+|a\s+|an\s+)?(?P<rest>.+)$",
    re.IGNORECASE,
)
_POSSESSIVE_RE = re.compile(r"['’]s$|s['’]$", re.IGNORECASE)


def _clean(value: Any, *, limit: int = 120) -> str:
    return " ".join(str(value or "").split())[:limit]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", str(text or "").lower())


def _scene_body(scene: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(scene, Mapping):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, Mapping):
        return inner
    return scene


def public_scene_text(scene: Mapping[str, Any] | None) -> str:
    """Population evidence from public scene text. Hidden facts are ignored."""
    body = _scene_body(scene)
    parts: list[str] = []
    for key in ("summary", "location", "mode"):
        text = _clean(body.get(key), limit=400)
        if text:
            parts.append(text)
    for key in ("visible_facts", "opening_seed_facts", "journal_seed_facts"):
        values = body.get(key)
        if isinstance(values, list):
            parts.extend(_clean(item, limit=400) for item in values if _clean(item, limit=400))
    return " ".join(parts)


def scene_population(scene: Mapping[str, Any] | None) -> str:
    text = public_scene_text(scene)
    populated = bool(_POPULATED_RE.search(text))
    isolated = bool(_ISOLATED_RE.search(text))
    if isolated and not populated:
        return "isolated"
    if populated and not isolated:
        return "populated"
    if populated and isolated:
        return "mixed"
    return "unknown"


def consequential_reference(span: str) -> bool:
    """A reference that asserts plot, office, or hidden truth."""
    raw = str(span or "")
    if not raw:
        return False
    if _PLOT_ASSERTION_RE.search(raw) or _AUTHORITY_OFFICE_RE.search(raw):
        return True
    if CONSEQUENTIAL_TERMS.search(raw) or HIDDEN_INFO_TERMS.search(raw):
        return True
    return False


def _content_words(text: str) -> list[str]:
    return [word for word in _tokens(text) if word not in _LEADING and len(word) > 2]


def _stem(word: str) -> str:
    if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _head_keys(head: str) -> set[str]:
    raw = str(head or "").lower()
    if not raw:
        return set()
    keys = {raw, _stem(raw)}
    if len(raw) > 4 and raw.endswith("s") and not raw.endswith("ss"):
        keys.add(raw[:-1])
    return keys


def _is_compass(token: str) -> bool:
    return bool(_COMPASS_RE.match(str(token or "")))


def _is_locative(token: str) -> bool:
    return _is_compass(token) or token in _LOCATIVE_ADJUNCTS


def _looks_prenominal_adjective(token: str) -> bool:
    if token in _PRENOMINAL_ADJECTIVES:
        return True
    if len(token) > 4 and token.endswith("y") and token not in _NONPERSON_HEADS:
        return True
    if len(token) > 4 and token.endswith("ed") and not token.endswith("eed"):
        return True
    return False


def _postnominal_participle(token: str, *, noun_seen: bool, followed: bool) -> bool:
    """An -ing/-ed form after the noun, with a complement, is not the head."""
    if not noun_seen or not followed:
        return False
    if token in {
        "carrying", "holding", "sweeping", "wearing", "standing", "watching",
        "walking", "working", "waiting", "blocking", "sitting", "leaning",
        "looking", "stacked",
    }:
        return True
    if len(token) >= 5 and token.endswith("ing"):
        return True
    if len(token) >= 5 and token.endswith("ed") and not token.endswith("eed"):
        return True
    return False


def _standalone_person(token: str) -> bool:
    """A single noun can denote a person by social category or agentive shape."""
    keys = _head_keys(token)
    if not keys or keys & _NONPERSON_HEADS or keys & _PRONOUN_HEADS or keys & _ACTION_HEADS:
        return False
    if any(_is_locative(key) for key in keys):
        return False
    if keys & _SOCIAL_HEADS:
        return True
    for key in keys:
        if _AGENTIVE_SUFFIX_RE.search(key) and key not in _COMPOUND_PERSON_RIGHT:
            return True
    return False


def _classify_head(expression: str) -> str:
    """person, nonperson, or unknown. Unknown is not a person."""
    tokens = [word for word in _tokens(expression) if word not in _DETERMINER_TOKENS]
    if not tokens:
        return "absent"
    right = tokens[-1]
    keys = _head_keys(right)
    if not keys or keys & _PRONOUN_HEADS or keys & _ACTION_HEADS or keys & _NONPERSON_HEADS:
        return "nonperson"
    if any(_is_locative(key) for key in keys):
        return "nonperson"
    if len(tokens) >= 2 and (right in _COMPOUND_PERSON_RIGHT or _stem(right) in _COMPOUND_PERSON_RIGHT):
        return "person"
    if _standalone_person(right):
        return "person"
    return "unknown"


def _head_denotes_person(head: str) -> bool:
    """Personhood of the referential head. An unknown head is not a person."""
    return _classify_head(head) == "person"


def _core_nominal(span: str | None) -> str | None:
    """Nominal core. Infinitives, participles, and locative tails are not the head.

    A player-pronoun clause glued onto the span is not a recoverable nominal.
    A who/that relative may be cut, because the noun before it is the head.
    """
    raw = _clean(span, limit=160)
    if not raw:
        return None
    cut = _CLAUSE_CUT_RE.split(raw, maxsplit=1)[0].strip(" ,.;")
    relative = _WH_RELATIVE_RE.search(cut)
    if relative and _content_words(cut[: relative.start()]):
        cut = cut[: relative.start()].strip(" ,.;")
    other = _OTHER_RELATIVE_RE.search(cut)
    if other and _content_words(cut[: other.start()]):
        cut = cut[: other.start()].strip(" ,.;")
    if _PLAYER_CLAUSE_RE.search(cut):
        return None
    cut = re.sub(r"\b(?:for|toward|towards|into|with|without|about|at|on|of)\s*$", "", cut).strip(" ,.;")
    if not cut or _PRONOUN_START_RE.match(cut) or _PREP_START_RE.match(cut):
        return None
    cut = _PURPOSE_INFINITIVE_RE.sub("", cut).strip(" ,.;")
    cut = _PARTICIPLE_RE.split(cut, maxsplit=1)[0].strip(" ,.;")
    of_tail = re.search(r"\s+\bof\s+.+$", cut, flags=re.IGNORECASE)
    if of_tail:
        left = cut[: of_tail.start()].strip(" ,.;")
        if _content_words(left):
            cut = left
    cut = _TRAILING_MODIFIER_RE.sub("", cut).strip(" ,.;")
    cut = _PURPOSE_INFINITIVE_RE.sub("", cut).strip(" ,.;")
    if not cut or _FINITE_RE.search(cut):
        return None
    words = _content_words(cut)
    if not words or len(words) > 6:
        return None
    if not _DETERMINER_RE.match(cut) and len(words) > 3:
        return None
    return cut


def _coordinated_nominal(span: str | None) -> bool:
    """Two determined conjuncts are not one person head."""
    return bool(_COORD_NOMINAL_RE.search(str(span or "")))


def _cluster_tokens(text: str) -> list[str] | None:
    """Tokens of the prenominal cluster. None means the phrase is coordinated.

    The cluster stops at the first postnominal boundary: a preposition, a
    relative, an infinitive, a participle with a complement, or a locative
    adjunct that follows a noun. The referential head is the right edge of
    what remains, not the last token of the original span.
    """
    tokens = _tokens(text)
    cluster: list[str] = []
    noun_seen = False
    for index, token in enumerate(tokens):
        followed = index + 1 < len(tokens)
        possessive = bool(_POSSESSIVE_RE.search(token))
        bare = _POSSESSIVE_RE.sub("", token)
        if token in _DETERMINER_TOKENS and not cluster:
            continue
        if noun_seen and token in {"who", "whom", "whose", "which", "that"}:
            break
        if noun_seen and token in {"and", "or"}:
            return None
        if noun_seen and (token in _PREPOSITION_TOKENS or bare in _PREPOSITION_TOKENS):
            break
        if noun_seen and _is_locative(token):
            break
        if _postnominal_participle(token, noun_seen=noun_seen, followed=followed):
            break
        if possessive:
            # The possessor modifies the following noun. It is not the head.
            continue
        if token in _DETERMINER_TOKENS:
            continue
        cluster.append(token)
        if not _looks_prenominal_adjective(token):
            noun_seen = True
    return cluster


def _nominal_cluster(span: str | None) -> list[str] | None:
    if _coordinated_nominal(span):
        return None
    core = _core_nominal(span)
    if not core:
        return []
    quantifier = _QUANTIFIER_OF_RE.match(core)
    if quantifier:
        return _cluster_tokens(quantifier.group("rest"))
    return _cluster_tokens(core)


def _head_expression(cluster: list[str]) -> str:
    """Right-edge noun, plus a left noun when the right noun is not a person alone."""
    if not cluster:
        return ""
    right = cluster[-1]
    compound_right = right in _COMPOUND_PERSON_RIGHT or _stem(right) in _COMPOUND_PERSON_RIGHT
    if _standalone_person(right) or _classify_head(right) == "nonperson" or not compound_right:
        return right
    left = [token for token in cluster[:-1] if not _looks_prenominal_adjective(token)]
    if not left:
        return right
    return " ".join(left + [right])


def referential_head(span: str | None) -> str:
    """The noun this phrase denotes.

    Derived from nominal structure: determiners and prenominal modifiers
    precede the head, and postnominal modifiers do not replace it. A compound
    such as "stable hand" keeps the left noun because "hand" alone is not a person.
    """
    cluster = _nominal_cluster(span)
    if not cluster:
        return ""
    return _head_expression(cluster)


def nominal_semantic_head(span: str | None) -> str:
    """The referential head. The last remaining content word is not the head."""
    return referential_head(span)


def _raw_head(text: str) -> str:
    head = referential_head(text)
    words = _content_words(head) or _tokens(head)
    return words[-1] if words else ""


def _head(text: str) -> str:
    return _stem(_raw_head(text))


def referential_nominal(span: str | None) -> str | None:
    """A nominal phrase. It may denote a person, a place, or an object."""
    if _coordinated_nominal(span):
        return None
    core = _core_nominal(span)
    if not core:
        return None
    if _QUANTIFIER_OF_RE.match(core):
        trimmed = re.sub(r"^(?:the|a|an)\s+", "", core, count=1, flags=re.IGNORECASE)
        return _clean(trimmed, limit=80) or None
    cluster = _cluster_tokens(core)
    if not cluster:
        return None
    return _clean(" ".join(cluster), limit=80) or None


def personhood_of_span(span: str | None) -> str:
    """person, nonperson, unknown, coordinated, or absent.

    Unknown does not default to person. A coordinated phrase has no single head.
    """
    if _coordinated_nominal(span):
        return "coordinated"
    head = referential_head(span)
    if not head:
        if referential_nominal(span):
            return "unknown"
        return "absent"
    return _classify_head(head)


def referential_person_nominal(span: str | None) -> str | None:
    """A nominal whose referential head denotes a person.

    A determiner phrase is not enough. "the inn" and "the muddy lane northwest
    of the crates" are nominals whose heads are not people. A person head stays
    a person when an infinitive, participle, relative, or locative follows it.
    An unknown head abstains. A model label cannot override this.
    """
    if personhood_of_span(span) != "person":
        return None
    nominal = referential_nominal(span)
    if not nominal:
        return None
    if not person_shaped(nominal):
        return None
    return nominal


def person_shaped(nominal: str, catalog: Sequence[Mapping[str, Any]] | None = None) -> bool:
    """An addressed individual, not a place, object, or crowd."""
    if _classify_head(referential_head(nominal)) != "person":
        return False
    core = referential_nominal(nominal) or ""
    words = _content_words(core)
    if not words:
        return False
    for row in catalog or ():
        if not isinstance(row, Mapping) or str(row.get("type") or "") != "object":
            continue
        object_words = _content_words(str(row.get("label") or row.get("id") or ""))
        if object_words and object_words == words:
            return False
    return True


def _entity_id(scene_id: str, label: str) -> str:
    key = " ".join(_content_words(label))
    digest = hashlib.sha1(f"{scene_id}|{key}".encode("utf-8")).hexdigest()[:10]
    return f"inc_{digest}"


def _records(session: Mapping[str, Any] | None, scene_id: str) -> list[dict[str, Any]]:
    ledger = session.get("bounded_improvisation") if isinstance(session, Mapping) else None
    rows = ledger.get("incidental_entities") if isinstance(ledger, Mapping) else None
    if not isinstance(rows, list):
        return []
    current = str(scene_id or "").strip()
    found: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if current and str(row.get("scene_id") or "") not in {"", current}:
            continue
        found.append(dict(row))
    return found


def incidental_catalog_rows(
    session: Mapping[str, Any] | None,
    scene_id: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in _records(session, str(scene_id or "")):
        label = _clean(record.get("label") or record.get("role"), limit=80)
        ident = _clean(record.get("entity_id"), limit=80)
        if not ident or not label:
            continue
        rows.append(
            {
                "type": "interlocutor",
                "id": ident,
                "label": label,
                "aliases": [label],
                "source": "bounded_incidental",
            }
        )
    return rows


def _match_existing(nominal: str, records: Sequence[Mapping[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    head = _head(nominal)
    if not head:
        return "none", None
    hits: list[dict[str, Any]] = []
    for record in records:
        label = str(record.get("label") or "")
        if _head(label) == head or " ".join(_content_words(label)) == " ".join(_content_words(nominal)):
            hits.append(dict(record))
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in hits:
        ident = str(record.get("entity_id") or "")
        if ident in seen:
            continue
        seen.add(ident)
        unique.append(record)
    if len(unique) > 1:
        return "ambiguous", None
    if len(unique) == 1:
        return "one", unique[0]
    return "none", None


def _empty_binding(nominal: str, span: str) -> dict[str, Any]:
    return {
        "status": BIND_UNRESOLVED,
        "entity_class": CLASS_AMBIGUOUS,
        "proposed_interlocutor": nominal or None,
        "proposed_span": span or None,
        "bound_interlocutor_id": None,
        "entity_id": None,
        "label": None,
        "explicit_new_interlocutor": bool(nominal),
        "authority_reasons": [],
        "catalog_row": None,
    }


def resolve_proposed_interlocutor(
    nominal: str,
    span: str,
    *,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
    scene_id: str,
    catalog: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """PR-BN decision for a player-proposed person who is not already canonical."""
    label = referential_person_nominal(nominal) or referential_person_nominal(span) or ""
    full = _clean(span or nominal, limit=180)
    binding = _empty_binding(label, full)
    if not label:
        kind = personhood_of_span(nominal)
        if kind == "absent":
            kind = personhood_of_span(span)
        thing = referential_nominal(nominal) or referential_nominal(span)
        if kind == "coordinated":
            reason = "proposal:coordinated_nominal"
        elif kind == "unknown":
            reason = "proposal:personhood_unresolved"
        elif thing or kind == "nonperson":
            reason = "proposal:not_a_person"
        else:
            reason = "proposal:not_referential_entity"
        binding["authority_reasons"] = [reason]
        binding["explicit_new_interlocutor"] = True
        binding["proposed_interlocutor"] = thing or None
        return binding
    if consequential_reference(full):
        binding["status"] = BIND_REJECTED
        binding["entity_class"] = CLASS_CONSEQUENTIAL
        binding["authority_reasons"] = ["proposal:consequential"]
        return binding
    kind, existing = _match_existing(label, _records(session, scene_id))
    if kind == "ambiguous":
        binding["status"] = BIND_AMBIGUOUS
        binding["entity_class"] = CLASS_AMBIGUOUS
        binding["authority_reasons"] = ["proposal:ambiguous_existing"]
        return binding
    if kind == "one" and existing:
        binding.update(
            {
                "status": BIND_INCIDENTAL,
                "entity_class": CLASS_INCIDENTAL,
                "bound_interlocutor_id": existing.get("entity_id"),
                "entity_id": existing.get("entity_id"),
                "label": existing.get("label") or label,
                "authority_reasons": ["identity:existing_incidental"],
                "catalog_row": {
                    "type": "interlocutor",
                    "id": existing.get("entity_id"),
                    "label": existing.get("label") or label,
                    "aliases": [existing.get("label") or label],
                    "source": "bounded_incidental",
                },
            }
        )
        return binding
    if not person_shaped(label, catalog):
        binding["authority_reasons"] = ["proposal:not_a_person"]
        return binding
    population = scene_population(scene)
    if population != "populated":
        binding["authority_reasons"] = [f"scene:{population}"]
        return binding
    decision = validate_bounded_improvisation_proposal(
        {
            "kind": "incidental_fact",
            "category": "background_npc_detail",
            "content": label,
            "scope": "scene",
            "consequence_level": "incidental",
            "source": "player_proposed_interlocutor",
        },
        session=session,
        scene=scene,
        world=None,
    )
    if not decision.accepted:
        reasons = list(decision.reason_codes)
        if any(code.startswith("content:consequential") or code.startswith("content:hidden") for code in reasons):
            binding["status"] = BIND_REJECTED
            binding["entity_class"] = CLASS_CONSEQUENTIAL
        binding["authority_reasons"] = reasons or ["pr_bn:rejected"]
        return binding
    ident = _entity_id(scene_id, label)
    binding.update(
        {
            "status": BIND_INCIDENTAL,
            "entity_class": CLASS_INCIDENTAL,
            "bound_interlocutor_id": ident,
            "entity_id": ident,
            "label": label,
            "authority_reasons": ["scene:populated", "pr_bn:accepted"],
            "catalog_row": {
                "type": "interlocutor",
                "id": ident,
                "label": label,
                "aliases": [label],
                "source": "bounded_incidental",
            },
        }
    )
    return binding


def persist_incidental_binding(
    session: dict[str, Any] | None,
    binding: Mapping[str, Any] | None,
    scene_id: str | None,
) -> dict[str, Any] | None:
    """Store the minimal continuity record. Rejected proposals are not stored."""
    if not isinstance(session, dict) or not isinstance(binding, Mapping):
        return None
    if str(binding.get("status") or "") != BIND_INCIDENTAL:
        return None
    ident = _clean(binding.get("entity_id") or binding.get("bound_interlocutor_id"), limit=80)
    label = _clean(binding.get("label"), limit=80)
    if not ident or not label:
        return None
    current = _clean(scene_id, limit=80)
    ledger = ensure_bounded_improvisation_ledger(session)
    entities = ledger.setdefault("incidental_entities", [])
    for row in entities:
        if isinstance(row, Mapping) and str(row.get("entity_id") or "") == ident:
            return dict(row)
    record = {
        "entity_id": ident,
        "label": label,
        "role": label,
        "scene_id": current,
        "provenance": "bounded_incidental",
        "authority": "bounded_improvisation",
        "kind": "incidental_fact",
        "category": "background_npc_detail",
        "truth_status": "runtime_incidental",
        "consequence_level": "incidental",
    }
    entities.append(record)
    entries = ledger.setdefault("entries", [])
    if not any(isinstance(row, Mapping) and str(row.get("id") or "") == ident for row in entries):
        entries.append(
            {
                "id": ident,
                "kind": "incidental_fact",
                "category": "background_npc_detail",
                "content": label,
                "scope": "scene",
                "scene_id": current or None,
                "consequence_level": "incidental",
                "source": "player_proposed_interlocutor",
                "status": "promoted",
                "authority": "bounded_improvisation",
                "truth_status": "runtime_incidental",
            }
        )
    return dict(record)


def apply_entity_binding(
    resolution: dict[str, Any] | None,
    session: dict[str, Any] | None,
    *,
    scene_id: str | None = None,
) -> None:
    """Make a validated incidental interlocutor the speaker for this turn.

    An explicit address that did not bind clears the previous speaker instead
    of leaving that speaker in place.
    """
    if not isinstance(resolution, dict):
        return
    metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), Mapping) else {}
    contract = metadata.get("resolution_contract") if isinstance(metadata, Mapping) else None
    if not isinstance(contract, Mapping):
        return
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), Mapping) else {}
    status = str(binding.get("status") or "")
    explicit = bool(binding.get("explicit_new_interlocutor"))
    if status == BIND_INCIDENTAL:
        persist_incidental_binding(session if isinstance(session, dict) else None, binding, scene_id)
        social = resolution.get("social")
        if not isinstance(social, dict):
            social = {}
            resolution["social"] = social
        social["npc_id"] = binding.get("bound_interlocutor_id")
        social["npc_name"] = binding.get("label")
        if isinstance(session, dict):
            from game.interaction_context import set_social_target

            set_social_target(session, str(binding.get("bound_interlocutor_id") or ""))
        return
    if status == BIND_CANONICAL and explicit:
        social = resolution.get("social")
        if not isinstance(social, dict):
            social = {}
            resolution["social"] = social
        social["npc_id"] = binding.get("bound_interlocutor_id")
        if binding.get("label"):
            social["npc_name"] = binding.get("label")
        if isinstance(session, dict):
            from game.interaction_context import set_social_target

            set_social_target(session, str(binding.get("bound_interlocutor_id") or ""))
        return
    if explicit and status in {BIND_UNRESOLVED, BIND_AMBIGUOUS, BIND_REJECTED}:
        social = resolution.get("social")
        if isinstance(social, dict):
            social.pop("npc_id", None)
            social.pop("npc_name", None)
        if isinstance(session, dict):
            from game.interaction_context import set_social_target

            set_social_target(session, None)
