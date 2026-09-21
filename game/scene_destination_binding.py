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
    }
)
_QUESTION_LEAD_RE = re.compile(
    r"^\s*(?:what|where|why|how|who|which|when)\b",
    re.IGNORECASE,
)
_COMMITMENT_PREFIX_RE = re.compile(
    r"^\s*(?:(?:fine|alright|all\s+right|okay|ok|right)\s*[.!,]\s*)?"
    r"(?:(?:i|we)(?:'ll| will|'m| am| are|'re)\s+(?:going\s+to\s+)?|let(?:'s| us)\s+)",
    re.IGNORECASE,
)
_TRAVEL_VERB_PREFIX_RE = re.compile(
    r"^(?:(?:please\s+)?"
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


def resolve_place_phrase_to_exit_target(
    phrase: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: Set[str],
) -> Optional[str]:
    """Map a free-text place phrase to a single exit ``target_scene_id``; fail closed."""
    tid = _strict_unique_exit_destination(phrase, exits)
    if not tid:
        tid = _declared_unique_exit_target_for_dest(phrase, exits)
    if not tid:
        tid = _unique_exit_target_from_destination_identity(phrase, exits)
    if tid and tid in known_scene_ids:
        return tid
    return None


def _strip_travel_commitment_prefix(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return raw
    match = _COMMITMENT_PREFIX_RE.match(raw)
    if not match:
        return raw
    rest = raw[match.end() :].strip()
    return rest or raw


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
    if _RETURN_MOTION_RE.search(work):
        return ""
    return None


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
    raw = str(text or "").strip()
    if not raw or not exits:
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
    return None


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
