"""Deterministic scene transition destination binding (named places vs leads vs inference).

This module centralizes precedence when multiple signals could map to ``target_scene_id``.
It is intentionally small and testable; it does not perform model routing or narration.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Set

from game.utils import slugify

# Regexes for *explicit* named-place movement embedded in prose (not sentence-initial only).
# Lookahead must stop at punctuation *or* common clause boundaries ("… waste to look …"),
# otherwise a non-greedy capture can absorb the whole sentence until the final period.
_PLACE_TAIL_LOOKAHEAD = (
    r"(?=(?:\s*[.,;?!]|[.,;?!]|\s+(?:to|for|and|but|instead|then|before|after)\b|\s*$))"
)

_EMBEDDED_PLACE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p, re.IGNORECASE | re.DOTALL), tag)
    for p, tag in (
        (
            r"\benter(?:s|ing)?\s+(?:the\s+)?([A-Za-z0-9][A-Za-z0-9\s'\-]{1,78}?)"
            + _PLACE_TAIL_LOOKAHEAD,
            "enter_place",
        ),
        (
            r"\bgo(?:es|ing)?\s+to\s+(?:the\s+)?([A-Za-z0-9][A-Za-z0-9\s'\-]{1,78}?)" + _PLACE_TAIL_LOOKAHEAD,
            "go_to_place",
        ),
        (
            r"\bhead(?:s|ing)?\s+(?:off\s+)?to\s+(?:the\s+)?([A-Za-z0-9][A-Za-z0-9\s'\-]{1,78}?)"
            + _PLACE_TAIL_LOOKAHEAD,
            "head_to_place",
        ),
        (
            r"\b(?:walk|walks|walking|run|runs|running)\s+to\s+(?:the\s+)?([A-Za-z0-9][A-Za-z0-9\s'\-]{1,78}?)"
            + _PLACE_TAIL_LOOKAHEAD,
            "walk_to_place",
        ),
    )
)


def _trim_place_fragment(raw: str) -> str:
    s = (raw or "").strip()
    s = re.sub(r"\s+", " ", s).strip(" \t\"'")
    s = re.sub(r"\s+(?:and|then|before|after)\s+.*$", "", s, flags=re.IGNORECASE).strip()
    return s


def extract_last_explicit_named_place(text: str | None) -> Optional[str]:
    """Return the last embedded explicit place phrase (e.g. ``Stone Boar``), or None."""
    if not isinstance(text, str) or not text.strip():
        return None
    last: Optional[str] = None
    for pat, _tag in _EMBEDDED_PLACE_PATTERNS:
        for m in pat.finditer(text):
            frag = _trim_place_fragment(m.group(1) or "")
            if frag and len(frag) >= 2:
                last = frag
    return last


def known_scene_ids_from_exits(exits: List[Dict[str, Any]]) -> Set[str]:
    out: Set[str] = set()
    for ex in exits or []:
        if not isinstance(ex, dict):
            continue
        tid = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if tid:
            out.add(tid)
    return out


_NAMED_DEPARTURE_RE = re.compile(
    r"(?P<place>[a-z][a-z0-9' -]*?),\s+then\.\s+(?:i|we)\s+set off that way[.!]?",
    re.IGNORECASE,
)


def named_departure_destination(text: str | None) -> str | None:
    """Extract the destination of a bare selection followed by explicit departure."""
    match = _NAMED_DEPARTURE_RE.fullmatch(" ".join(str(text or "").split()))
    return match["place"] if match else None


def named_departure_route_ids(place: str, exits: list[dict]) -> set[str]:
    """Match the complete name against authored route names and aliases."""
    def key(name: str) -> str:
        return slugify(re.sub(r"^(?:the|a|an)\s+", "", name.strip(), flags=re.I))

    wanted = key(place)
    matches = set()
    for row in exits:
        label = str(row.get("label") or "")
        # Authored labels may describe an action such as "Seek the fortress trail".
        subject = re.sub(r"^seek\s+", "", label, flags=re.I)
        names = [label, subject, *(str(alias) for alias in row.get("aliases") or [])]
        if wanted and any(wanted == key(name) for name in names):
            matches.add(row["id"])
    return matches


def _strict_unique_exit_destination(dest: str, exits: List[Dict[str, Any]]) -> Optional[str]:
    raw = (dest or "").strip()
    if not raw or not isinstance(exits, list):
        return None
    cf = raw.casefold()
    sg = slugify(raw)
    hits: List[str] = []
    for ex in exits:
        if not isinstance(ex, dict):
            continue
        lab = str(ex.get("label") or "").strip()
        tid = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not lab or not tid:
            continue
        if lab.casefold() == cf or slugify(lab) == sg:
            hits.append(tid)
    uniq = list(dict.fromkeys(hits))
    if len(uniq) == 1:
        return uniq[0]
    return None


def _collect_exit_targets_matching_dest_fragment(dest: str, exits: List[Dict[str, Any]]) -> List[str]:
    hits: List[str] = []
    if not (dest or "").strip() or not exits:
        return hits
    dh = dest.strip().lower()
    for ex in exits:
        if not isinstance(ex, dict):
            continue
        label = (ex.get("label") or "").strip().lower()
        target = (ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not target:
            continue
        if dh in label or label in dh or slugify(dh) in slugify(label) or slugify(label) in slugify(dh):
            hits.append(target)
    return hits


def _declared_unique_exit_target_for_dest(dest: str, exits: List[Dict[str, Any]]) -> Optional[str]:
    hits = _collect_exit_targets_matching_dest_fragment(dest, exits)
    uniq = list(dict.fromkeys(hits))
    if len(uniq) == 1:
        return uniq[0]
    return None


_EXIT_PHRASE_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "to",
        "toward",
        "towards",
        "for",
        "back",
        "again",
        "my",
        "our",
        "this",
        "that",
        "and",
        "or",
        "of",
        "at",
        "in",
        "on",
        "i",
        "im",
        "ill",
        "we",
        "well",
        "lets",
        "please",
        "just",
        "then",
        "along",
        "available",
        "here",
        "there",
    }
)
_TRAVEL_VERB_STOPWORDS = frozenset(
    {
        "head",
        "heads",
        "heading",
        "go",
        "goes",
        "going",
        "walk",
        "walks",
        "walking",
        "run",
        "runs",
        "running",
        "travel",
        "travels",
        "traveling",
        "travelling",
        "move",
        "moves",
        "moving",
        "come",
        "comes",
        "coming",
        "return",
        "returns",
        "returning",
        "take",
        "takes",
        "taking",
        "follow",
        "follows",
        "following",
        "leave",
        "leaves",
        "leaving",
        "depart",
        "departs",
        "departing",
        "enter",
        "enters",
        "entering",
        "journey",
        "journeys",
        "pursue",
        "pursues",
        "pursuing",
        "proceed",
        "proceeds",
        "proceeding",
    }
)
_QUESTION_LEAD_RE = re.compile(
    r"^\s*(?:what|where|why|how|who|which|when|is\s+there|are\s+there)\b",
    re.IGNORECASE,
)
_COMMITMENT_PREFIX_RE = re.compile(
    r"^\s*(?:(?:fine|alright|all\s+right|okay|ok|right)\s*[.!,]\s*)?"
    r"(?:(?:i|we)(?:'ll| will|'m| am| are|'re)\s+(?:going\s+to\s+)?|let(?:'s| us)\s+)",
    re.IGNORECASE,
)
_TRAVEL_VERB_PREFIX_RE = re.compile(
    r"^(?:(?:i|we)\s+)?(?:(?:please\s+)?"
    r"(?:head|heads|heading|go|goes|going|walk|walks|walking|run|runs|running|"
    r"travel|travels|traveling|travelling|move|moves|moving|come|comes|coming|"
    r"return|returns|returning|journey|journeys|enter|enters|entering|"
    r"follow|follows|following|take|takes|taking|leave|leaves|leaving|"
    r"depart|departs|departing|pursue|pursues|pursuing)"
    r"(?:\s+(?:back|off|out|again))?"
    r"(?:\s+(?:to|toward|towards|for|along|down|through))?"
    r"(?:\s+the)?"
    r")(?:\s+|$)",
    re.IGNORECASE,
)
_RETURN_MOTION_RE = re.compile(
    r"\b(?:head|heads|heading|go|goes|going|walk|walks|walking|come|comes|coming|"
    r"move|moves|moving|return|returns|returning)\s+back\b"
    r"|\b(?:return|returns|returning)\b",
    re.IGNORECASE,
)
_EXPLICIT_TRAVEL_COMMITMENT_RE = re.compile(
    r"\b(?:i(?:'ll| will| am|'m)|we(?:'ll| will| are|'re)|let(?:'s| us))\s+"
    r"(?:going\s+to\s+)?"
    r"(?:follow|pursue|leave|return|head(?:ing)?|travel|walk|depart|"
    r"go\s+(?:to|after|towards?|back)|"
    r"head(?:ing)?\s+(?:to|for|down|off|out|back)|"
    r"take\s+(?:the|a)\b)\b",
    re.IGNORECASE,
)


def _exit_content_tokens(text: str) -> Set[str]:
    stop = _EXIT_PHRASE_STOPWORDS | _TRAVEL_VERB_STOPWORDS
    return {
        tok
        for tok in re.findall(r"[a-z0-9']+", str(text or "").lower())
        if tok not in stop and len(tok) >= 3
    }


def _iter_authored_exits(exits: List[Dict[str, Any]]) -> List[tuple[str, str]]:
    rows: List[tuple[str, str]] = []
    for ex in exits or []:
        if not isinstance(ex, dict):
            continue
        label = str(ex.get("label") or "").strip()
        target = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if target:
            rows.append((label, target))
    return rows


def _unique_target(hits: List[str]) -> Optional[str]:
    uniq = [item for item in dict.fromkeys(hits) if item]
    return uniq[0] if len(uniq) == 1 else None


def _unique_exit_target_from_destination_identity(
    phrase: str,
    exits: List[Dict[str, Any]],
) -> Optional[str]:
    """Match a destination phrase to exactly one authored exit via id/label tokens."""
    raw = (phrase or "").strip()
    if not raw:
        return None
    dest_cf = raw.casefold()
    dest_slug = slugify(raw)
    dest_tokens = _exit_content_tokens(raw)
    hits: List[str] = []
    for label, target in _iter_authored_exits(exits):
        target_cf = target.casefold()
        target_slug = slugify(target)
        label_cf = label.casefold()
        surface_tokens = _exit_content_tokens(label) | _exit_content_tokens(target.replace("_", " "))
        matched = False
        if dest_cf and (dest_cf == target_cf or dest_cf == label_cf):
            matched = True
        elif dest_slug and len(dest_slug) >= 4 and (
            dest_slug == target_slug
            or dest_slug in target_slug
            or target_slug in dest_slug
        ):
            matched = True
        elif dest_tokens and dest_tokens <= surface_tokens:
            matched = True
        if matched:
            hits.append(target)
    return _unique_target(hits)


def _resolve_known_place_phrase(
    phrase: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: Set[str],
) -> Optional[str]:
    """Map one place phrase to a single known exit. Does not drop purpose language."""
    tid = _strict_unique_exit_destination(phrase, exits)
    if not tid:
        tid = _declared_unique_exit_target_for_dest(phrase, exits)
    if not tid:
        tid = _unique_exit_target_from_destination_identity(phrase, exits)
    if tid and tid in known_scene_ids:
        return tid
    return None


def resolve_place_phrase_to_exit_target(
    phrase: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: Set[str],
) -> Optional[str]:
    """Map a free-text place phrase to a single exit ``target_scene_id``; fail closed.

    A purpose, reason, or dangling participle stays attached only when that full
    phrase is itself an authored destination. Otherwise the remainder is tried
    against the same catalog. No second binder and no new route.
    """
    tid = _resolve_known_place_phrase(phrase, exits, known_scene_ids)
    if tid or _phrase_names_authored_destination(phrase, exits):
        return tid
    peeled = destination_phrase_respecting_purpose_tail(phrase, exits)
    if not peeled or _normalized_destination_key(peeled) == _normalized_destination_key(phrase):
        return None
    return _resolve_known_place_phrase(peeled, exits, known_scene_ids)


def _strip_travel_commitment_prefix(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return raw
    match = _COMMITMENT_PREFIX_RE.match(raw)
    if not match:
        return raw
    rest = raw[match.end() :].strip()
    return rest or raw


# Directional proceed joins the existing travel-verb family. Manner ("with") and
# purpose infinitives ("to question") stay outside scene travel.
_DIRECTIONAL_PROCEED_RE = re.compile(
    r"(?:^|[,;]\s*)(?:i|we)(?:'ll|\s+will)?(?:\s+(?:am|are))?\s+"
    r"proceed(?:s|ing)?\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_PROCEED_COMPASS_RE = re.compile(
    r"^(?:north|south|east|west)(?:[-\s]?(?:north|south|east|west))?\b",
    re.IGNORECASE,
)
_PROCEED_ROUTE_PREP_RE = re.compile(
    r"^(?:toward|towards|along|down|into|through|for|to)\b",
    re.IGNORECASE,
)
_PROCEED_PURPOSE_INFINITIVE_RE = re.compile(
    r"^to\s+(?!the\b|a\b|an\b)",
    re.IGNORECASE,
)


def _proceed_destination_rest(text: str) -> Optional[str]:
    """Destination remainder after directional proceed, or None when proceed is not scene travel."""
    raw = str(text or "").strip()
    if not raw:
        return None
    work = _strip_travel_commitment_prefix(raw)
    work = re.sub(r"[.!?]+$", "", work).strip()
    match = _DIRECTIONAL_PROCEED_RE.search(work)
    if not match:
        return None
    rest = str(match.group("rest") or "").strip()
    rest = re.split(r"\s*,\s*", rest, maxsplit=1)[0].strip(" \t.,;:!?\"'")
    if not rest or re.match(r"^with\b", rest, flags=re.IGNORECASE):
        return None
    if _PROCEED_PURPOSE_INFINITIVE_RE.match(rest):
        return None
    if not (_PROCEED_COMPASS_RE.match(rest) or _PROCEED_ROUTE_PREP_RE.match(rest)):
        return None
    rest = re.sub(
        r"^(?:toward|towards|along|down|into|through|for|to)\s+",
        "",
        rest,
        flags=re.IGNORECASE,
    ).strip()
    rest = re.sub(r"^(?:the|a|an)\s+", "", rest, flags=re.IGNORECASE).strip()
    return rest or None


def looks_like_directional_proceed_travel(text: str | None) -> bool:
    """True when proceed carries a compass direction or a route/destination, not a local task."""
    return _proceed_destination_rest(text) is not None


def extract_travel_destination_phrase(text: str) -> Optional[str]:
    """Return dest after travel verbs, '' for bare return/back, or None if not travel-shaped."""
    raw = str(text or "").strip()
    if not raw:
        return None
    work = _strip_travel_commitment_prefix(raw)
    work = re.sub(r"[.!?]+$", "", work).strip()
    match = _TRAVEL_VERB_PREFIX_RE.match(work)
    if match:
        dest = work[match.end() :].strip(" \t.,;:!?\"'")
        dest = re.sub(r"^(?:the|a|an)\s+", "", dest, flags=re.IGNORECASE).strip()
        if dest.casefold() in {"back", "again"}:
            dest = ""
        return dest
    proceed_dest = _proceed_destination_rest(work)
    if proceed_dest is not None:
        return proceed_dest
    if _RETURN_MOTION_RE.search(work):
        return ""
    return None


_TRAVEL_SELECTION_VERB_RE = re.compile(
    r"\b(?:go|goes|going|head|heads|heading|enter|enters|entering|leave|leaves|leaving|"
    r"travel|travels|traveling|travelling|walk|walks|walking|follow|follows|following|"
    r"pursue|pursues|pursuing|take|takes|taking|return|returns|returning|exit|exits|exiting|"
    r"proceed|proceeds|proceeding|depart|departs|departing)\b",
    re.IGNORECASE,
)
_NONTRAVEL_GOVERNING_RE = re.compile(
    r"\b(?:read|reads|reading|examine|examines|examining|inspect|inspects|inspecting|"
    r"study|studies|studying|search|searching|ask|asks|asking|tell|tells|telling)\b",
    re.IGNORECASE,
)
_COMPOUND_JOIN_RE = re.compile(r"\b(?:and then|and|then)\b", re.IGNORECASE)
_GENERIC_DESTINATION_TOKENS = frozenset(
    {
        "gate",
        "exit",
        "door",
        "road",
        "street",
        "way",
        "path",
        "track",
        "trail",
        "route",
        "passage",
        "entrance",
        "lane",
        "through",
        "into",
        "toward",
        "towards",
        "northwest",
        "northeast",
        "southwest",
        "southeast",
        "north",
        "south",
        "east",
        "west",
        "missing",
        "patrol",
        "rumor",
        "rumour",
    }
)


def _topic_return_travel_remainder(raw: str) -> str | None:
    """'' blocks travel. A remainder is the physical clause. None means not a topic return."""
    from game.conversational_continuity import conversational_topic_return, without_nonphysical_clauses

    if not conversational_topic_return(raw):
        return None
    remainder = without_nonphysical_clauses(raw)
    if not remainder or remainder == raw or not _TRAVEL_SELECTION_VERB_RE.search(remainder):
        return ""
    return remainder


def affirmative_travel_selection_allowed(text: str | None) -> bool:
    """True only when this utterance affirmatively authorizes exit selection.

    Negation, questions, non-travel verbs, and a travel clause joined to another
    action do not authorize a move. An earlier negated clause does not cancel a
    later affirmative one: that case does not match the existing negation shape.
    """
    from game.player_commitment import committed_world_text
    from game.intent_parser import _explicit_stay_or_travel_negation

    raw = committed_world_text(str(text or ""))
    if not raw:
        return False
    topic_remainder = _topic_return_travel_remainder(raw)
    if topic_remainder == "":
        return False
    if isinstance(topic_remainder, str):
        raw = topic_remainder
    if _looks_like_information_question(raw):
        return False
    if _explicit_stay_or_travel_negation(raw):
        return False
    travel = _TRAVEL_SELECTION_VERB_RE.search(raw)
    nontravel = _NONTRAVEL_GOVERNING_RE.search(raw)
    if travel and nontravel and _COMPOUND_JOIN_RE.search(raw):
        return False
    return bool(travel or _looks_like_return_or_back_intent(raw))


def _distinctive_destination_tokens(text: str) -> Set[str]:
    return {
        tok
        for tok in _exit_content_tokens(text)
        if tok not in _GENERIC_DESTINATION_TOKENS and len(tok) >= 4
    }


def _unique_exit_by_distinctive_tokens(
    text: str,
    exits: List[Dict[str, Any]],
    known: Optional[Set[str]],
) -> Optional[str]:
    """One authored exit whose label, alias, or destination id shares a distinctive token."""
    tokens = _distinctive_destination_tokens(text)
    if not tokens:
        return None
    hits: List[str] = []
    for ex in exits or []:
        if not isinstance(ex, dict):
            continue
        label = str(ex.get("label") or "").strip()
        target = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not target:
            continue
        if known is not None and target not in known:
            continue
        surface = _exit_content_tokens(label) | _exit_content_tokens(target.replace("_", " "))
        for alias in ex.get("aliases") or []:
            surface |= _exit_content_tokens(str(alias))
        surface -= _GENERIC_DESTINATION_TOKENS
        if tokens & surface:
            hits.append(target)
    return _unique_target(hits)


def _looks_like_information_question(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False
    if _EXPLICIT_TRAVEL_COMMITMENT_RE.search(raw):
        return False
    return bool(_QUESTION_LEAD_RE.search(raw))


def _looks_like_return_or_back_intent(text: str) -> bool:
    return bool(_RETURN_MOTION_RE.search(str(text or "")))


def _unique_return_or_single_exit_target(exits: List[Dict[str, Any]]) -> Optional[str]:
    rows = _iter_authored_exits(exits)
    if not rows:
        return None
    return_hits = [
        target
        for label, target in rows
        if re.search(r"\b(?:return|back)\b", label, flags=re.IGNORECASE)
    ]
    unique_return = _unique_target(return_hits)
    if unique_return:
        return unique_return
    unique_all = _unique_target([target for _label, target in rows])
    return unique_all


def resolve_authored_exit_from_player_travel(
    text: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: Optional[Set[str]] = None,
) -> Optional[str]:
    """Resolve natural travel/return intent against the current scene's authored exits.

    Consumes only current-scene exit labels and destination ids. Fail closed on
    ambiguity, unavailable destinations, and information-seeking mentions.
    """
    from game.player_commitment import committed_world_text

    raw = committed_world_text(text)
    if not raw or not exits:
        return None
    topic_remainder = _topic_return_travel_remainder(raw)
    if topic_remainder == "":
        return None
    if isinstance(topic_remainder, str):
        raw = topic_remainder
    if not affirmative_travel_selection_allowed(raw):
        return None
    if _looks_like_information_question(raw):
        return None
    known = set(known_scene_ids) if known_scene_ids is not None else known_scene_ids_from_exits(exits)

    phrases: List[str] = [raw, _strip_travel_commitment_prefix(raw)]
    dest = extract_travel_destination_phrase(raw)
    if dest:
        phrases.append(dest)
    for phrase in phrases:
        tid = resolve_place_phrase_to_exit_target(phrase, exits, known)
        if tid:
            return tid

    if dest == "" and _looks_like_return_or_back_intent(raw):
        tid = _unique_return_or_single_exit_target(exits)
        if tid and tid in known:
            return tid
    return _unique_exit_by_distinctive_tokens(raw, exits, known)


def _pursuit_action_metadata(normalized_action: Dict[str, Any]) -> Dict[str, Any]:
    md = normalized_action.get("metadata")
    return md if isinstance(md, dict) else {}


def _is_authoritative_pursuit_transition(normalized_action: Dict[str, Any]) -> bool:
    md = _pursuit_action_metadata(normalized_action)
    if not str(md.get("authoritative_lead_id") or "").strip():
        return False
    return str(md.get("commitment_source") or "").strip() == "explicit_player_pursuit"


# Lexical buckets for post-binding semantic compatibility (deterministic; no model calls).
_TRAVEL_BUCKET_INTERIOR = "interior_establishment"
_TRAVEL_BUCKET_OUTDOOR = "outdoor_road_wilderness_ruin"
_TRAVEL_BUCKET_GENERIC = "generic_travel"
_TRAVEL_BUCKET_UNKNOWN = "unknown"

_INTERIOR_LABEL_RE = re.compile(
    r"(?i)\b(enter\b|tavern|inn|pub|taproom|alehouse|shop\b|market\s+stall|guildhall|hall\b|cellar|shrine\b|temple\b)"
)
_OUTDOOR_LABEL_RE = re.compile(
    r"(?i)\b(milestone|crossroads|road\b|trail|wilderness|forest|woods?\b|ruin|ruins|scrub|moor|heath|"
    r"ditch|patrol\b|rumor|gate\s+district|waystone|bridge\b|field\b|hills?\b)"
)


def _declared_destination_phrase(
    *,
    raw_player_text: str | None,
    prompt: str,
    metadata: Dict[str, Any],
) -> Optional[str]:
    emb = str(metadata.get("embedded_place_phrase") or "").strip()
    if emb:
        return emb
    raw = (raw_player_text or prompt or "").strip()
    return extract_last_explicit_named_place(raw)


def _exit_matching_phrase(phrase: str, exits: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not phrase or not isinstance(exits, list):
        return None
    pcf = phrase.casefold().strip()
    if len(pcf) < 2:
        return None
    best: Optional[Dict[str, Any]] = None
    best_len = 0
    for ex in exits:
        if not isinstance(ex, dict):
            continue
        lab = str(ex.get("label") or "").strip()
        if not lab:
            continue
        lcf = lab.casefold()
        if pcf in lcf or lcf in pcf:
            if len(lab) > best_len:
                best_len = len(lab)
                best = ex
    return best


def _travel_bucket_from_exit_label(label: str) -> Optional[str]:
    if not (label or "").strip():
        return None
    if _INTERIOR_LABEL_RE.search(label):
        return _TRAVEL_BUCKET_INTERIOR
    if _OUTDOOR_LABEL_RE.search(label):
        return _TRAVEL_BUCKET_OUTDOOR
    return None


def _travel_bucket_from_free_text(text: str) -> Optional[str]:
    if not (text or "").strip():
        return None
    if _INTERIOR_LABEL_RE.search(text):
        return _TRAVEL_BUCKET_INTERIOR
    if _OUTDOOR_LABEL_RE.search(text):
        return _TRAVEL_BUCKET_OUTDOOR
    return None


def _enter_context_for_phrase(raw: str, phrase: str) -> bool:
    """True when prose uses enter/entering the <phrase> (building-style entry)."""
    if not raw or not phrase:
        return False
    esc = re.escape(phrase.strip())
    if len(esc) < 2:
        return False
    return bool(
        re.search(
            r"\benter(?:s|ing)?\s+(?:the\s+)?" + esc + r"\b",
            raw,
            flags=re.IGNORECASE,
        )
    )


def _expected_travel_bucket(
    phrase: str,
    raw_combined: str,
    exits: List[Dict[str, Any]],
) -> str:
    ex = _exit_matching_phrase(phrase, exits)
    if ex:
        b = _travel_bucket_from_exit_label(str(ex.get("label") or ""))
        if b:
            return b
    b2 = _travel_bucket_from_free_text(phrase)
    if b2:
        return b2
    if _enter_context_for_phrase(raw_combined, phrase):
        return _TRAVEL_BUCKET_INTERIOR
    return _TRAVEL_BUCKET_UNKNOWN


def _scene_blob_for_bucket(scene: Dict[str, Any]) -> str:
    parts: List[str] = []
    sid = str(scene.get("id") or "").strip()
    if sid:
        parts.append(sid.replace("_", " "))
    loc = str(scene.get("location") or "").strip()
    if loc:
        parts.append(loc)
    summ = str(scene.get("summary") or "").strip()
    if summ:
        parts.append(summ[:240])
    return " ".join(parts)


def infer_travel_semantic_bucket_for_scene(
    scene: Optional[Dict[str, Any]],
    *,
    scene_id: str,
) -> str:
    """Classify a destination scene into a travel bucket using id + location + summary only."""
    blob = _scene_blob_for_bucket(scene) if isinstance(scene, dict) else ""
    if not blob.strip():
        blob = scene_id.replace("_", " ")
    if _INTERIOR_LABEL_RE.search(blob) or re.search(
        r"(?i)\b(tavern|innhouse|inn\b|public\s+house)\b",
        blob,
    ):
        return _TRAVEL_BUCKET_INTERIOR
    if _OUTDOOR_LABEL_RE.search(blob):
        return _TRAVEL_BUCKET_OUTDOOR
    sid_l = (scene_id or "").lower()
    if any(
        tok in sid_l
        for tok in (
            "tavern",
            "inn",
            "pub",
            "shop",
            "market_hall",
            "guildhall",
            "hall",
            "cellar",
            "temple",
            "shrine",
        )
    ):
        return _TRAVEL_BUCKET_INTERIOR
    if any(
        tok in sid_l
        for tok in (
            "milestone",
            "road",
            "trail",
            "wild",
            "forest",
            "ruin",
            "moor",
            "crossroads",
            "wilderness",
            "scrub",
            "field",
            "bridge",
            "gate",
        )
    ):
        return _TRAVEL_BUCKET_OUTDOOR
    return _TRAVEL_BUCKET_GENERIC


def _phrase_coheres_with_target(
    phrase: str,
    target_scene_id: str,
    scene: Optional[Dict[str, Any]],
) -> bool:
    """True when the place phrase clearly names the target scene (slug / token overlap)."""
    ph = slugify(phrase)
    tid = slugify(target_scene_id)
    if ph and tid and (ph in tid or tid in ph):
        return True
    if ph and tid:
        ptoks = {t for t in ph.split("-") if len(t) >= 3}
        ttoks = {t for t in tid.split("-") if len(t) >= 3}
        if ptoks and ptoks <= ttoks:
            return True
    if isinstance(scene, dict):
        loc = slugify(str(scene.get("location") or ""))
        if ph and loc and ph in loc:
            return True
    return False


def _buckets_semantically_compatible(expected: str, actual: str) -> bool:
    if expected in (_TRAVEL_BUCKET_UNKNOWN, _TRAVEL_BUCKET_GENERIC):
        return True
    if actual in (_TRAVEL_BUCKET_UNKNOWN, _TRAVEL_BUCKET_GENERIC):
        return True
    if expected == actual:
        return True
    pairs = {_TRAVEL_BUCKET_INTERIOR, _TRAVEL_BUCKET_OUTDOOR}
    if expected in pairs and actual in pairs and expected != actual:
        return False
    return True


def evaluate_destination_semantic_compatibility(
    *,
    normalized_action: Dict[str, Any],
    raw_player_text: str | None,
    prompt: str,
    effective_target_scene_id: str,
    destination_semantic_kind: str,
    exits: List[Dict[str, Any]],
    load_scene_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Post-binding check: block transitions whose target bucket clashes with the declared place phrase.

    Runs after :func:`reconcile_scene_transition_destination`. Skipped for authoritative
    ``explicit_player_pursuit`` transitions (lead commitment already encodes intent).
    """
    base_meta: Dict[str, Any] = {
        "destination_compatibility_checked": False,
        "destination_compatibility_passed": True,
        "destination_compatibility_failure_reason": None,
        "blocked_incompatible_scene_transition": False,
        "destination_compatibility_expected_kind": "",
        "destination_compatibility_actual_kind": "",
    }
    tid = str(effective_target_scene_id or "").strip()
    if not tid:
        return {**base_meta, "compatibility_clear_target": False}

    if _is_authoritative_pursuit_transition(normalized_action):
        return {
            **base_meta,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "destination_compatibility_failure_reason": None,
            "destination_compatibility_expected_kind": _TRAVEL_BUCKET_GENERIC,
            "destination_compatibility_actual_kind": _TRAVEL_BUCKET_GENERIC,
            "compatibility_clear_target": False,
        }

    md = _pursuit_action_metadata(normalized_action)
    parser_lane = str(md.get("parser_lane") or "").strip()
    raw_combined = ((raw_player_text or "") + " " + (prompt or "")).strip()

    phrase = _declared_destination_phrase(
        raw_player_text=raw_player_text,
        prompt=prompt,
        metadata=md,
    )
    # Only enforce when the player anchored a concrete named destination in text/metadata,
    # or the binding layer already classified this as an explicit named-place resolution.
    if not phrase and destination_semantic_kind != "named_place":
        return {
            **base_meta,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "destination_compatibility_failure_reason": None,
            "destination_compatibility_expected_kind": _TRAVEL_BUCKET_GENERIC,
            "destination_compatibility_actual_kind": "",
            "compatibility_clear_target": False,
        }

    if not phrase and destination_semantic_kind == "named_place":
        phrase = extract_last_explicit_named_place(raw_combined) or ""

    if not phrase.strip():
        return {
            **base_meta,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "destination_compatibility_failure_reason": None,
            "destination_compatibility_expected_kind": _TRAVEL_BUCKET_GENERIC,
            "destination_compatibility_actual_kind": "",
            "compatibility_clear_target": False,
        }

    # The route catalog already named this arrival. A word inside that
    # authored label (Inn, Looking) is not a reason to discard the route.
    if _authored_name_selects_target(phrase, exits, tid):
        return {
            **base_meta,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "destination_compatibility_failure_reason": None,
            "destination_compatibility_expected_kind": _TRAVEL_BUCKET_GENERIC,
            "destination_compatibility_actual_kind": _TRAVEL_BUCKET_GENERIC,
            "compatibility_clear_target": False,
        }

    loaded: Optional[Dict[str, Any]] = None
    if load_scene_fn is not None:
        try:
            env = load_scene_fn(tid)
            if isinstance(env, dict):
                sc = env.get("scene")
                loaded = sc if isinstance(sc, dict) else None
        except Exception:
            loaded = None

    actual = infer_travel_semantic_bucket_for_scene(loaded, scene_id=tid)
    expected = _expected_travel_bucket(phrase.strip(), raw_combined, exits)

    if parser_lane == "embedded_named_place_travel" and destination_semantic_kind == "named_place":
        if expected == _TRAVEL_BUCKET_UNKNOWN:
            expected = _TRAVEL_BUCKET_INTERIOR

    if _phrase_coheres_with_target(phrase.strip(), tid, loaded):
        return {
            **base_meta,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "destination_compatibility_failure_reason": None,
            "destination_compatibility_expected_kind": expected or _TRAVEL_BUCKET_GENERIC,
            "destination_compatibility_actual_kind": actual,
            "compatibility_clear_target": False,
        }

    ok = _buckets_semantically_compatible(expected, actual)
    if ok:
        return {
            **base_meta,
            "destination_compatibility_checked": True,
            "destination_compatibility_passed": True,
            "destination_compatibility_failure_reason": None,
            "destination_compatibility_expected_kind": expected,
            "destination_compatibility_actual_kind": actual,
            "compatibility_clear_target": False,
        }

    return {
        **base_meta,
        "destination_compatibility_checked": True,
        "destination_compatibility_passed": False,
        "destination_compatibility_failure_reason": "declared_place_bucket_mismatches_target_scene_bucket",
        "blocked_incompatible_scene_transition": True,
        "destination_compatibility_expected_kind": expected,
        "destination_compatibility_actual_kind": actual,
        "compatibility_clear_target": True,
    }


def merge_destination_binding_metadata(
    base: Dict[str, Any],
    *,
    destination_binding_source: str,
    destination_binding_conflict: bool,
    destination_binding_conflict_candidates: List[str],
    destination_binding_resolution_reason: str,
    destination_semantic_kind: str,
) -> Dict[str, Any]:
    out = dict(base)
    out["destination_binding_source"] = destination_binding_source
    out["destination_binding_conflict"] = bool(destination_binding_conflict)
    out["destination_binding_conflict_candidates"] = list(destination_binding_conflict_candidates)
    out["destination_binding_resolution_reason"] = destination_binding_resolution_reason
    out["destination_semantic_kind"] = destination_semantic_kind
    return out


def reconcile_scene_transition_destination(
    *,
    normalized_action: Dict[str, Any],
    prompt: str,
    raw_player_text: str | None,
    exits: List[Dict[str, Any]],
    known_scene_ids: Set[str],
    proposed_target_scene_id: Optional[str],
    inferred_target_scene_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return effective target + binding diagnostics.

    ``proposed_target_scene_id`` is the target already on the normalized action (parser/affordance).
    ``inferred_target_scene_id`` is optional loose inference (e.g. substring exit match) when
    the action had no explicit target.
    """
    md = _pursuit_action_metadata(normalized_action)
    parser_lane = str(md.get("parser_lane") or "").strip()

    raw = (raw_player_text or prompt or "").strip()
    explicit_place = extract_last_explicit_named_place(raw)
    explicit_resolved: Optional[str] = None
    if explicit_place:
        explicit_resolved = resolve_place_phrase_to_exit_target(
            explicit_place, exits, known_scene_ids
        )

    proposed = str(proposed_target_scene_id or "").strip() or None
    inferred = str(inferred_target_scene_id or "").strip() or None

    conflict = False
    candidates: List[str] = []
    effective: Optional[str] = proposed
    source = "normalized_action_target"
    reason = "use_parser_or_affordance_target_scene_id"
    semantic = "explicit_scene_id"

    choice = classify_destination_choice(raw, exits)
    if choice.get("kind") == "unresolved":
        # Neither alternative may become the arrival. The admitted route id
        # stays untouched because this turn does not commit a transition.
        return {
            "effective_target_scene_id": None,
            "destination_binding_source": "unresolved_destination_alternatives",
            "destination_binding_conflict": True,
            "destination_binding_conflict_candidates": list(choice.get("exit_ids") or []),
            "destination_binding_resolution_reason": "unresolved_destination_alternatives",
            "destination_semantic_kind": "named_place",
            "suppress_loose_inference": True,
            "clear_proposed_target": True,
        }
    if (
        choice.get("kind") == "correction"
        and proposed
        and choice.get("target_scene_id") == proposed
        and explicit_resolved
        and explicit_resolved != proposed
    ):
        return {
            "effective_target_scene_id": proposed,
            "destination_binding_source": "corrected_destination",
            "destination_binding_conflict": True,
            "destination_binding_conflict_candidates": sorted({explicit_resolved, proposed}),
            "destination_binding_resolution_reason": "correction_preserves_authoritative_route",
            "destination_semantic_kind": "named_place",
            "suppress_loose_inference": True,
            "clear_proposed_target": False,
        }

    if explicit_resolved:
        effective = explicit_resolved
        source = "explicit_named_place_in_player_text"
        semantic = "named_place"
        reason = "authoritative_exit_match_for_embedded_place_phrase"
        if proposed and proposed != explicit_resolved:
            conflict = True
            candidates = sorted({explicit_resolved, proposed})
            reason = "explicit_named_place_overrides_conflicting_proposed_target"
        return {
            "effective_target_scene_id": effective,
            "destination_binding_source": source,
            "destination_binding_conflict": conflict,
            "destination_binding_conflict_candidates": candidates,
            "destination_binding_resolution_reason": reason,
            "destination_semantic_kind": semantic,
            "suppress_loose_inference": bool(explicit_place),
            "clear_proposed_target": False,
        }

    if explicit_place and not explicit_resolved:
        inferred_tid = str(inferred_target_scene_id or "").strip() or None
        suppress_inference = True
        if _is_authoritative_pursuit_transition(normalized_action) and proposed:
            effective = proposed
            source = "authoritative_pursuit_metadata"
            semantic = "lead_scene"
            reason = "pursuit_commitment_kept_while_named_place_fragment_did_not_resolve_to_exit"
            return {
                "effective_target_scene_id": effective,
                "destination_binding_source": source,
                "destination_binding_conflict": conflict,
                "destination_binding_conflict_candidates": candidates,
                "destination_binding_resolution_reason": reason,
                "destination_semantic_kind": semantic,
                "suppress_loose_inference": suppress_inference,
                "clear_proposed_target": False,
            }
        if proposed and parser_lane == "legacy_follow_exit_match":
            return {
                "effective_target_scene_id": None,
                "destination_binding_source": "explicit_named_place_unresolved",
                "destination_binding_conflict": conflict,
                "destination_binding_conflict_candidates": candidates,
                "destination_binding_resolution_reason": "suppress_legacy_follow_exit_when_named_place_unresolved",
                "destination_semantic_kind": "named_place",
                "suppress_loose_inference": suppress_inference,
                "clear_proposed_target": True,
            }
        if proposed and not _is_authoritative_pursuit_transition(normalized_action):
            return {
                "effective_target_scene_id": None,
                "destination_binding_source": "explicit_named_place_unresolved",
                "destination_binding_conflict": conflict,
                "destination_binding_conflict_candidates": [proposed] if proposed else [],
                "destination_binding_resolution_reason": "suppress_non_pursuit_target_when_named_place_present_but_unresolved",
                "destination_semantic_kind": "named_place",
                "suppress_loose_inference": suppress_inference,
                "clear_proposed_target": True,
            }
        if inferred_tid:
            return {
                "effective_target_scene_id": None,
                "destination_binding_source": "explicit_named_place_unresolved",
                "destination_binding_conflict": conflict,
                "destination_binding_conflict_candidates": [inferred_tid],
                "destination_binding_resolution_reason": "suppress_loose_inference_when_named_place_present_but_unresolved",
                "destination_semantic_kind": "named_place",
                "suppress_loose_inference": suppress_inference,
                "clear_proposed_target": True,
            }
        return {
            "effective_target_scene_id": None,
            "destination_binding_source": "explicit_named_place_unresolved",
            "destination_binding_conflict": conflict,
            "destination_binding_conflict_candidates": candidates,
            "destination_binding_resolution_reason": "named_place_present_but_unresolved_no_target",
            "destination_semantic_kind": "named_place",
            "suppress_loose_inference": suppress_inference,
            "clear_proposed_target": False,
        }

    # No explicit named-place phrase: pursuit / proposed / inference precedence
    if _is_authoritative_pursuit_transition(normalized_action) and proposed:
        effective = proposed
        source = "authoritative_pursuit_metadata"
        semantic = "lead_scene"
        reason = "explicit_player_pursuit_commitment"
    elif inferred and not proposed:
        effective = inferred
        source = "prompt_exit_inference"
        semantic = "fallback_guess"
        reason = "loose_prompt_to_exit_match"
    elif proposed:
        effective = proposed
        source = "normalized_action_target"
        semantic = "explicit_scene_id"
        reason = "use_parser_or_affordance_target_scene_id"

    return {
        "effective_target_scene_id": effective,
        "destination_binding_source": source,
        "destination_binding_conflict": conflict,
        "destination_binding_conflict_candidates": candidates,
        "destination_binding_resolution_reason": reason,
        "destination_semantic_kind": semantic,
        "suppress_loose_inference": False,
        "clear_proposed_target": False,
    }


def try_embedded_named_place_scene_action(
    text: str,
    scene: Dict[str, Any],
    *,
    known_scene_ids: Optional[Set[str]] = None,
) -> Optional[Dict[str, Any]]:
    """If embedded ``entering the X`` style text resolves to exactly one exit, return a scene_transition action."""
    if not isinstance(text, str) or not text.strip() or not isinstance(scene, dict):
        return None
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    known = set(known_scene_ids) if known_scene_ids else known_scene_ids_from_exits(exits)
    place = extract_last_explicit_named_place(text)
    if not place:
        return None
    tid = resolve_place_phrase_to_exit_target(place, exits, known)
    if not tid:
        return None
    bind_meta = merge_destination_binding_metadata(
        {
            "parser_lane": "embedded_named_place_travel",
            "embedded_place_phrase": place,
        },
        destination_binding_source="explicit_named_place_in_player_text",
        destination_binding_conflict=False,
        destination_binding_conflict_candidates=[],
        destination_binding_resolution_reason="embedded_place_phrase_resolved_before_generic_parser",
        destination_semantic_kind="named_place",
    )
    tstrip = text.strip()
    aid = slugify(place)[:40] or slugify(tstrip)[:40] or "scene_transition"
    return {
        "id": aid,
        "label": tstrip[:200],
        "type": "scene_transition",
        "prompt": tstrip,
        "targetSceneId": tid,
        "target_scene_id": tid,
        "metadata": bind_meta,
    }


_HEDGE_OR_RE = re.compile(r"\bor\s+whatever\b", re.IGNORECASE)
_HEDGE_SIDE_RE = re.compile(
    r"^(?:whatever(?:\s+(?:they|you)\s+call\s+it)?|so\s+they\s+call\s+it|"
    r"as\s+(?:they|folks)\s+call\s+it|or\s+so|something|the\s+like)\b",
    re.IGNORECASE,
)
_CORRECTION_OR_RATHER_RE = re.compile(
    r"\bor rather\b[,:\s-]*(?P<chosen>.+)$",
    re.IGNORECASE,
)
_CORRECTION_MAKE_THAT_RE = re.compile(
    r"\bactually,?\s+make that\s+(?P<chosen>.+)$",
    re.IGNORECASE,
)
_CORRECTION_MEANT_RE = re.compile(
    r"^(?:i|we)\s+meant\s+(?P<chosen>.+?)(?:[,.]?\s+not\s+(?P<rejected>.+))?$",
    re.IGNORECASE,
)
_CORRECTION_NOT_THEN_RE = re.compile(
    r"^not\s+(?:the\s+)?(?P<rejected>.+?)[.]\s*(?P<chosen>.+)$",
    re.IGNORECASE,
)
_CATALOG_CHOICE_RE = re.compile(
    r"\b(?:one of (?:those|these) two(?:\s+routes)?|whichever\s+(?:route|path|road|way|exit))\b",
    re.IGNORECASE,
)
_EITHER_OR_RE = re.compile(r"\beither\s+(?P<a>.+?)\s+or\s+(?P<b>.+)$", re.IGNORECASE)
_MAYBE_PAIR_RE = re.compile(
    r"\bmaybe\s+(?P<a>.+?)\s*,?\s*maybe\s+(?P<b>.+)$",
    re.IGNORECASE,
)
_VERSUS_RE = re.compile(r"\b(?P<a>.+?)\s+(?:versus|vs\.?)\s+(?P<b>.+)$", re.IGNORECASE)
_BETWEEN_RE = re.compile(
    r"\b(?:deciding|choosing|choose|decided)\s+between\s+(?P<a>.+?)\s+and\s+(?P<b>.+)$",
    re.IGNORECASE,
)
_MODAL_QUESTION_RE = re.compile(r"\b(?:should|could|would)\s+(?:i|we)\b", re.IGNORECASE)
_NONDESTINATION_ACTION_RE = re.compile(
    r"\b(?:ask|attack|inspect|examine|search|persuade|open|read|tell|say)\b",
    re.IGNORECASE,
)
_LEADING_DESTINATION_RE = re.compile(
    r"^(?:either|maybe|perhaps|rather)\s+|"
    r"^(?:(?:i|we)\s+)?(?:could|should|might|will|would|can|want(?:\s+to)?|need(?:\s+to)?)?\s*"
    r"(?:go|head|walk|travel|return|take|leave|follow|exit|enter|proceed|depart)"
    r"(?:\s+(?:back|off|out))?(?:\s+(?:to|toward|towards|for|along|down|through))?\s*",
    re.IGNORECASE,
)


def _choice_none() -> Dict[str, Any]:
    return {"kind": "none", "exit_ids": [], "target_scene_id": None, "phrases": []}


def _authored_choice_rows(exits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from game.route_authority import authored_exit_rows

    return authored_exit_rows({"scene": {"exits": list(exits or [])}})


def _clean_destination_phrase(phrase: str) -> str:
    text = " ".join(str(phrase or "").split()).strip(" \t\"'.,;:!?-")
    return re.sub(r"^(?:the|a|an)\s+", "", text, flags=re.IGNORECASE).strip()


# A trailing reason or participle is not part of the destination name.
# Bare "to" and "for" are not tails: they occur inside authored place names.
# "of Looking" is a name, not a dangling participle.
_UNAMBIGUOUS_PURPOSE_TAIL_RE = re.compile(
    r"\s+(?:"
    r"(?:looking|hoping|searching|trying|seeking|waiting)\s+(?:for|to)\b"
    r"|(?:thinking|wondering)\s+about\b"
    r"|because\s+(?:i|we|a|an|the|it|he|she|they|there|my|our|you)\b"
    r"|since\s+(?:i|we|it|he|she|they|there|my|our|you)\b"
    r"|so\s+(?:i|we)\s+can\b"
    r"|so\s+that\b"
    r"|in\s+order\s+to\b"
    r"|for\s+the\s+purpose\s+of\b"
    r"|with\s+the\s+intention\s+of\b"
    r").*$",
    re.IGNORECASE,
)
_DANGLING_MOTIVATION_RE = re.compile(
    r"^(?P<place>.+?)(?<!of)\s+(?:looking|hoping|searching|trying|seeking|thinking|waiting|wanting)\s*$",
    re.IGNORECASE,
)


def _normalized_destination_key(phrase: str) -> str:
    text = _clean_destination_phrase(phrase).casefold()
    text = re.sub(r"^seek\s+", "", text).strip()
    return " ".join(text.split())


def _authored_name_rows(phrase: str, exits: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Exits whose label, alias, or destination id is exactly this phrase."""
    key = _normalized_destination_key(phrase)
    if len(key) < 3 or not exits:
        return []
    found: List[Dict[str, Any]] = []
    for row in exits:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "")
        names = [label, re.sub(r"^seek\s+", "", label, flags=re.IGNORECASE)]
        names.extend(str(alias) for alias in (row.get("aliases") or []))
        target = str(row.get("target_scene_id") or row.get("targetSceneId") or "").replace("_", " ")
        names.append(target)
        if any(key == _normalized_destination_key(name) for name in names):
            found.append(row)
    return found


def _phrase_names_authored_destination(phrase: str, exits: List[Dict[str, Any]] | None) -> bool:
    """True when the whole phrase is one authored label, alias, or destination id."""
    return bool(_authored_name_rows(phrase, exits))


def _authored_name_selects_target(phrase: str, exits: List[Dict[str, Any]] | None, target: str) -> bool:
    """True when this phrase is the authored name of the exit that arrives at target."""
    wanted = str(target or "").strip()
    if not wanted:
        return False
    for row in _authored_name_rows(phrase, exits):
        tid = str(row.get("target_scene_id") or row.get("targetSceneId") or "").strip()
        if tid == wanted:
            return True
    return False


def peel_destination_purpose_tail(phrase: str) -> str:
    """Drop a structural purpose tail. Does not consult the route catalog."""
    text = " ".join(str(phrase or "").split()).strip(" \t\"'.,;:!?")
    if not text:
        return ""
    peeled = _UNAMBIGUOUS_PURPOSE_TAIL_RE.sub("", text).strip(" \t\"'.,;:!?")
    if peeled:
        text = peeled
    dangling = _DANGLING_MOTIVATION_RE.match(text)
    if dangling:
        place = dangling.group("place").strip(" \t\"'.,;:!?")
        if place and not re.search(r"\bof$", place, flags=re.IGNORECASE):
            text = place
    return text


def destination_phrase_respecting_purpose_tail(
    phrase: str,
    exits: List[Dict[str, Any]] | None = None,
) -> str:
    """Return the destination the player named, without a trailing purpose.

    An authored name that contains purpose words is kept whole. A dangling
    participle is removed only when the remainder is an authored name. A
    reason clause (because, so I can, looking for) is not a destination.
    """
    raw = " ".join(str(phrase or "").split()).strip(" \t\"'.,;:!?")
    if not raw:
        return ""
    if exits and _phrase_names_authored_destination(raw, exits):
        return raw
    peeled = peel_destination_purpose_tail(raw)
    if not peeled or _normalized_destination_key(peeled) == _normalized_destination_key(raw):
        return raw
    if not exits:
        return peeled
    if _phrase_names_authored_destination(peeled, exits):
        return peeled
    if _UNAMBIGUOUS_PURPOSE_TAIL_RE.search(raw):
        return peeled
    # "the gate hoping" is not the full label "Return to the Gate".
    # Keep the peel only when that remainder is one existing route.
    known = known_scene_ids_from_exits(exits)
    if _resolve_known_place_phrase(peeled, exits, known):
        return peeled
    return raw


def _side_phrase(part: str) -> str:
    """Destination words on one side of a choice. Empty means a bare return."""
    clause = re.split(r"\s+and\s+", str(part or ""), maxsplit=1, flags=re.IGNORECASE)[0]
    clause = " ".join(clause.split()).strip(" \t\"'.,;:!?")
    extracted = extract_travel_destination_phrase(clause)
    if extracted:
        return _clean_destination_phrase(extracted)
    if extracted == "":
        return ""
    trimmed = _LEADING_DESTINATION_RE.sub("", clause).strip()
    return _clean_destination_phrase(trimmed or clause)


def _rows_for_phrase(phrase: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    raw = _clean_destination_phrase(phrase)
    if not raw or _HEDGE_SIDE_RE.match(raw) or len(raw) < 3:
        return []
    dh = raw.casefold()
    hits: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for row in rows:
        names = [str(row.get("label") or "")]
        names.extend(str(alias) for alias in (row.get("aliases") or []))
        if names[0]:
            names.append(re.sub(r"^seek\s+", "", names[0], flags=re.IGNORECASE))
        matched = False
        for name in names:
            cleaned = " ".join(name.split()).strip()
            bare = re.sub(r"^(?:the|a|an)\s+", "", cleaned, flags=re.IGNORECASE).casefold()
            if len(bare) < 3:
                continue
            if dh == bare or dh in bare or bare in dh:
                matched = True
                break
        ident = str(row.get("id") or "")
        if matched and ident and ident not in seen:
            seen.add(ident)
            hits.append(row)
    return hits


def _pack_choice(kind: str, chosen: List[Dict[str, Any]], phrases: List[str]) -> Dict[str, Any]:
    ids: List[str] = []
    seen: Set[str] = set()
    for row in chosen:
        ident = str(row.get("id") or "")
        if ident and ident not in seen:
            seen.add(ident)
            ids.append(ident)
    target = None
    if kind == "correction" and len(chosen) == 1:
        target = str(chosen[0].get("target_scene_id") or chosen[0].get("targetSceneId") or "") or None
    return {"kind": kind, "exit_ids": ids, "target_scene_id": target, "phrases": [p for p in phrases if p]}


def _substantive_place(phrase: str) -> bool:
    tokens = [
        tok for tok in re.findall(r"[a-z0-9']+", phrase.casefold())
        if len(tok) >= 3 and tok not in _EXIT_PHRASE_STOPWORDS and tok not in _TRAVEL_VERB_STOPWORDS
        and tok not in _GENERIC_DESTINATION_TOKENS and tok not in {"maybe", "either", "rather", "actually"}
    ]
    return bool(tokens)


def classify_destination_choice(text: str | None, exits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tell a supported correction from unresolved destination alternatives.

    A unique corrected destination is not travel authority by itself. Two
    requested destinations are not permission to choose one. Questions stay
    with the existing question owners. Synonym hedges such as ``or whatever``
    are not a second destination.
    """
    none = _choice_none()
    body = " ".join(str(text or "").split())
    if not body or not exits:
        return none
    if "?" in body or re.match(
        r"^\s*(?:who|what|when|where|why|how|is|are|do|does|did|can|could|should|would)\b",
        body,
        re.IGNORECASE,
    ):
        return none
    rows = _authored_choice_rows(exits)
    if not rows:
        return none

    def correction_from(chosen_text: str) -> Dict[str, Any] | None:
        # A later independent action is not part of the corrected destination.
        if _NONDESTINATION_ACTION_RE.search(body) or re.search(r"\band\b", chosen_text, re.IGNORECASE):
            return None
        phrase = _side_phrase(chosen_text) or _clean_destination_phrase(chosen_text)
        matched = _rows_for_phrase(phrase, rows) if phrase else []
        if len(matched) == 1:
            return _pack_choice("correction", matched, [phrase])
        # A correction marker that still does not name one route is not travel.
        return _pack_choice("unresolved", matched, [phrase or _clean_destination_phrase(chosen_text)])

    make_that = _CORRECTION_MAKE_THAT_RE.search(body)
    if make_that:
        found = correction_from(make_that.group("chosen"))
        if found is not None:
            return found
    rather = _CORRECTION_OR_RATHER_RE.search(body)
    if rather:
        found = correction_from(rather.group("chosen"))
        if found is not None:
            return found
    meant = _CORRECTION_MEANT_RE.match(body.rstrip(".!?"))
    if meant:
        found = correction_from(meant.group("chosen"))
        if found is not None:
            return found
    not_then = _CORRECTION_NOT_THEN_RE.match(body.rstrip())
    if not_then:
        found = correction_from(not_then.group("chosen"))
        if found is not None:
            return found
    if _HEDGE_OR_RE.search(body):
        return none
    if _CATALOG_CHOICE_RE.search(body) and len(rows) > 1:
        return _pack_choice("unresolved", rows[:4], [])

    parts: List[str] | None = None
    either = _EITHER_OR_RE.search(body)
    maybe = _MAYBE_PAIR_RE.search(body)
    versus = _VERSUS_RE.search(body)
    between = _BETWEEN_RE.search(body)
    if either:
        parts = [either.group("a"), either.group("b")]
    elif maybe:
        parts = [maybe.group("a"), maybe.group("b")]
    elif versus:
        parts = [versus.group("a"), versus.group("b")]
    elif between:
        parts = [between.group("a"), between.group("b")]
    else:
        pieces = [piece for piece in re.split(r"\s+or\s+", body, flags=re.IGNORECASE) if piece.strip()]
        if len(pieces) >= 2:
            parts = pieces
    if not parts:
        return none

    phrases: List[str] = []
    matched: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    unmatched: List[str] = []
    for part in parts:
        phrase = _side_phrase(part)
        if phrase == "" and _looks_like_return_or_back_intent(part):
            for row in rows:
                if re.search(r"\b(?:return|back)\b", str(row.get("label") or ""), re.IGNORECASE):
                    ident = str(row.get("id") or "")
                    if ident and ident not in seen:
                        seen.add(ident)
                        matched.append(row)
            phrases.append("return")
            continue
        if not phrase or _HEDGE_SIDE_RE.match(phrase):
            continue
        phrases.append(phrase)
        found = _rows_for_phrase(phrase, rows)
        if found:
            for row in found:
                ident = str(row.get("id") or "")
                if ident and ident not in seen:
                    seen.add(ident)
                    matched.append(row)
        else:
            # A side the catalog does not name is still an alternative.
            # Generic words such as "north road" must not disappear and
            # leave some other route free to travel.
            unmatched.append(phrase)
    distinct = len({str(row.get("id") or "") for row in matched})
    alternatives = distinct + len(unmatched)
    modal = bool(_MODAL_QUESTION_RE.search(body))
    if distinct > 1 or (distinct == 1 and unmatched) or len(unmatched) >= 2 or (modal and alternatives >= 2):
        return _pack_choice("unresolved", matched, phrases)
    # Two names for one authoritative route are synonyms, not a choice.
    if distinct == 1 and not unmatched and not modal:
        return _pack_choice("correction", matched, phrases)
    return none
