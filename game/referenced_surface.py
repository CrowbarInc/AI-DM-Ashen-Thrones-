"""Reference / existence / visibility / inspectability classification.

Read-side helper over existing scene, interactable, visible-fact, clue, hidden-fact,
and NPC-topic surfaces. Not a persistence owner and not a referenced-object registry.

    mention ≠ existence
    existence ≠ inspectability
    player / narration reference ≠ world authority
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence

AUTHORITY_AUTHORED_INTERACTABLE = "authored_interactable"
AUTHORITY_AUTHORED_VISIBLE_FEATURE = "authored_visible_feature"
AUTHORITY_AUTHORED_ABSTRACT_REFERENCE = "authored_abstract_reference"
AUTHORITY_AUTHORED_HIDDEN = "authored_hidden"
AUTHORITY_UNSUPPORTED = "unsupported"
AUTHORITY_UNTARGETED = "untargeted"

_KIND_PRIORITY = {
    "interactable": 400,
    "visible_fact": 300,
    "hidden_fact": 200,
    "abstract_reference": 100,
}

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "for",
        "from",
        "had",
        "has",
        "have",
        "here",
        "i",
        "if",
        "i'll",
        "im",
        "in",
        "into",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "onto",
        "or",
        "our",
        "over",
        "the",
        "their",
        "then",
        "there",
        "these",
        "this",
        "those",
        "to",
        "under",
        "was",
        "we",
        "were",
        "with",
        "you",
        "your",
    }
)

_INSPECT_TARGET_RE = re.compile(
    r"\b(?:inspect|inspects|examine|examines|study|studies|search|searches|"
    r"check|checks|investigate|read|reads|reading|look\s+at|looks\s+at|"
    r"look\s+for|looks\s+for|look\s+toward|looks\s+toward|look\s+towards|looks\s+towards|"
    r"glance(?:s|d|ing)?(?:\s+back)?\s+(?:at|over|toward|towards))\s+"
    r"(?:the\s+|a\s+|an\s+|this\s+|that\s+)?"
    r"(?P<target>.+)$",
    re.IGNORECASE,
)

_TRAILING_CLAUSE_RE = re.compile(
    r"\b(?:that|which|who|whom|whose|while|as|because|after|before|when|"
    r"where|if|and\s+then)\b.*$",
    re.IGNORECASE,
)
_CONTENT_QUESTION_TARGET_RES = (
    re.compile(
        r"\bwhat(?:'s| is)\s+(?:actually\s+)?(?:posted|written|listed|shown)\s+on\s+"
        r"(?:the\s+|this\s+|that\s+)?(?P<target>.+?)\s*\??\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat(?:'s| is)\s+on\s+(?:the\s+|this\s+|that\s+)?(?P<target>.+?)\s*\??\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhat does\s+(?:the\s+|this\s+|that\s+)?(?P<target>.+?)\s+say\b",
        re.IGNORECASE,
    ),
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _inner_scene(scene_or_envelope: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene_or_envelope, Mapping):
        return {}
    raw = scene_or_envelope.get("scene")
    if isinstance(raw, dict):
        return raw
    return dict(scene_or_envelope)


def _stem_token(token: str) -> str:
    raw = str(token or "").strip().lower()
    if raw.endswith("ies") and len(raw) > 4:
        return raw[:-3] + "y"
    if raw.endswith("es") and len(raw) > 4:
        return raw[:-2]
    if raw.endswith("s") and len(raw) > 3:
        return raw[:-1]
    return raw


def content_tokens(text: str) -> List[str]:
    out: List[str] = []
    for tok in re.findall(r"[a-z0-9']+", str(text or "").lower()):
        if tok in _STOPWORDS or len(tok) <= 1:
            continue
        out.append(_stem_token(tok))
    return out


def extract_inspection_target(text: str, *, explicit_target: str | None = None) -> str:
    raw_explicit = _clean(explicit_target)
    if raw_explicit and (" " in raw_explicit or not re.fullmatch(r"[a-z0-9_]+", raw_explicit.lower())):
        return re.sub(r"[.!?]+$", "", raw_explicit).strip()
    raw = _clean(text)
    if not raw:
        return raw_explicit
    for pat in _CONTENT_QUESTION_TARGET_RES:
        content_match = pat.search(raw)
        if not content_match:
            continue
        tail = _clean(content_match.group("target"))
        tail = re.sub(r"[.!?]+$", "", tail).strip()
        trimmed = _TRAILING_CLAUSE_RE.sub("", tail).strip(" ,;:")
        return trimmed or tail or raw_explicit
    match = _INSPECT_TARGET_RE.search(raw)
    if not match:
        return raw_explicit
    tail = _clean(match.group("target"))
    tail = re.sub(r"[.!?]+$", "", tail).strip()
    trimmed = _TRAILING_CLAUSE_RE.sub("", tail).strip(" ,;:")
    return trimmed or tail or raw_explicit


def _prefix_token_lists(target: str) -> List[List[str]]:
    tokens = content_tokens(target)
    return [tokens[:end] for end in range(len(tokens), 0, -1)]


def _contains_token_phrase(surface_text: str, phrase: Sequence[str]) -> bool:
    if not phrase:
        return False
    surface = content_tokens(surface_text)
    width = len(phrase)
    if width > len(surface):
        return False
    wanted = list(phrase)
    for idx in range(len(surface) - width + 1):
        if surface[idx : idx + width] == wanted:
            return True
    return False


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _interactable_inspectable_text(item: Mapping[str, Any], clues: Mapping[str, str]) -> str:
    clue_id = _clean(item.get("reveals_clue"))
    if clue_id and clues.get(clue_id):
        return clues[clue_id]
    for key in ("description", "text", "readable_text", "contents"):
        text = _clean(item.get(key))
        if text:
            return text
    return ""


def _interactable_surfaces(scene_inner: Mapping[str, Any]) -> List[Dict[str, Any]]:
    clues: Dict[str, str] = {}
    for rec in scene_inner.get("discoverable_clues") or []:
        if not isinstance(rec, dict):
            continue
        cid = _clean(rec.get("id"))
        text = _clean(rec.get("text"))
        if cid and text:
            clues[cid] = text
    out: List[Dict[str, Any]] = []
    raw = scene_inner.get("interactables")
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        iid = _clean(item.get("id"))
        if not iid:
            continue
        labels = [iid.replace("_", " "), _clean(item.get("label")), _clean(item.get("name"))]
        labels.extend(_string_list(item.get("aliases")))
        inspectable_text = _interactable_inspectable_text(item, clues)
        for label in labels:
            if not label:
                continue
            out.append(
                {
                    "kind": "interactable",
                    "text": label,
                    "interactable_id": iid,
                    "label": _clean(item.get("label")) or iid.replace("_", " "),
                    "inspectable_text": inspectable_text,
                    "reveals_clue": _clean(item.get("reveals_clue")),
                }
            )
    return out


def _fact_surfaces(values: Any, kind: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(values, list):
        return out
    for item in values:
        text = _clean(item)
        if text:
            out.append({"kind": kind, "text": text})
    return out


def _present_npc_rows(
    scene_inner: Mapping[str, Any],
    world: Mapping[str, Any] | None,
) -> List[Dict[str, Any]]:
    scene_id = _clean(scene_inner.get("id"))
    addressable_ids = {
        _clean(row.get("id"))
        for row in (scene_inner.get("addressables") or [])
        if isinstance(row, Mapping) and _clean(row.get("id"))
    }
    rows: List[Dict[str, Any]] = []
    if not isinstance(world, Mapping):
        return rows
    raw = world.get("npcs")
    if isinstance(raw, list):
        candidates: Sequence[Any] = raw
    elif isinstance(raw, Mapping):
        candidates = list(raw.values())
    else:
        return rows
    for npc in candidates:
        if not isinstance(npc, Mapping):
            continue
        nid = _clean(npc.get("id"))
        loc = _clean(npc.get("location") or npc.get("scene_id"))
        if nid and (nid in addressable_ids or (scene_id and loc == scene_id)):
            rows.append(dict(npc))
    return rows


def _abstract_surfaces(
    scene_inner: Mapping[str, Any],
    world: Mapping[str, Any] | None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for npc in _present_npc_rows(scene_inner, world):
        topics = npc.get("topics")
        if isinstance(topics, list):
            for topic in topics:
                if isinstance(topic, Mapping):
                    text = _clean(topic.get("text"))
                    if text:
                        out.append({"kind": "abstract_reference", "text": text})
        knowledge = npc.get("knowledge")
        if isinstance(knowledge, list):
            for item in knowledge:
                if isinstance(item, Mapping):
                    text = _clean(item.get("text"))
                    if text:
                        out.append({"kind": "abstract_reference", "text": text})
                else:
                    text = _clean(item)
                    if text:
                        out.append({"kind": "abstract_reference", "text": text})
        elif isinstance(knowledge, Mapping):
            text = _clean(knowledge.get("text"))
            if text:
                out.append({"kind": "abstract_reference", "text": text})
    return out


def _empty_classification(target: str, authority: str) -> Dict[str, Any]:
    return {
        "target": target,
        "authority": authority,
        "existence": False,
        "visibility": False,
        "inspectability": False,
        "interactable_id": "",
        "visible_fact": "",
        "hidden_fact": "",
        "abstract_text": "",
        "inspectable_text": "",
        "label": "",
        "evidence": authority,
    }


def classify_referenced_surface(
    player_text: str,
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    world: Mapping[str, Any] | None = None,
    explicit_target: str | None = None,
) -> Dict[str, Any]:
    """Classify a requested inspect/examine target against authored surfaces only."""
    scene_inner = _inner_scene(scene_or_envelope)
    target = extract_inspection_target(player_text, explicit_target=explicit_target)
    if not content_tokens(target):
        return _empty_classification(target, AUTHORITY_UNTARGETED)

    surfaces: List[Dict[str, Any]] = []
    surfaces.extend(_interactable_surfaces(scene_inner))
    surfaces.extend(_fact_surfaces(scene_inner.get("visible_facts"), "visible_fact"))
    surfaces.extend(_fact_surfaces(scene_inner.get("opening_seed_facts"), "visible_fact"))
    surfaces.extend(_fact_surfaces(scene_inner.get("journal_seed_facts"), "visible_fact"))
    surfaces.extend(_fact_surfaces(scene_inner.get("hidden_facts"), "hidden_fact"))
    surfaces.extend(_abstract_surfaces(scene_inner, world))

    hit: Optional[Dict[str, Any]] = None
    matched_prefix: List[str] = []
    for prefix in _prefix_token_lists(target):
        candidates = [row for row in surfaces if _contains_token_phrase(str(row.get("text") or ""), prefix)]
        if not candidates:
            continue
        candidates.sort(key=lambda row: _KIND_PRIORITY.get(str(row.get("kind") or ""), 0), reverse=True)
        hit = candidates[0]
        matched_prefix = list(prefix)
        break

    full_tokens = content_tokens(target)
    if hit is not None and full_tokens:
        hit_overlap = len(set(content_tokens(str(hit.get("text") or ""))) & set(full_tokens))
        better: Optional[Dict[str, Any]] = None
        better_overlap = hit_overlap
        for row in surfaces:
            overlap = len(set(content_tokens(str(row.get("text") or ""))) & set(full_tokens))
            if overlap < 3 or overlap < better_overlap:
                continue
            if overlap == better_overlap:
                if better is None:
                    continue
                if _KIND_PRIORITY.get(str(row.get("kind") or ""), 0) <= _KIND_PRIORITY.get(
                    str(better.get("kind") or ""), 0
                ):
                    continue
            better = row
            better_overlap = overlap
        if better is not None and better_overlap > hit_overlap:
            hit = better
            matched_prefix = [tok for tok in full_tokens if tok in set(content_tokens(str(hit.get("text") or "")))]

    if hit is None:
        return _empty_classification(target, AUTHORITY_UNSUPPORTED)

    kind = str(hit.get("kind") or "")
    if kind == "interactable":
        inspectable_text = _clean(hit.get("inspectable_text"))
        return {
            "target": " ".join(matched_prefix) or target,
            "authority": AUTHORITY_AUTHORED_INTERACTABLE,
            "existence": True,
            "visibility": True,
            "inspectability": True,
            "interactable_id": _clean(hit.get("interactable_id")),
            "visible_fact": "",
            "hidden_fact": "",
            "abstract_text": "",
            "inspectable_text": inspectable_text,
            "label": _clean(hit.get("label")),
            "evidence": "interactable",
        }
    if kind == "visible_fact":
        fact = _clean(hit.get("text"))
        return {
            "target": " ".join(matched_prefix) or target,
            "authority": AUTHORITY_AUTHORED_VISIBLE_FEATURE,
            "existence": True,
            "visibility": True,
            "inspectability": False,
            "interactable_id": "",
            "visible_fact": fact,
            "hidden_fact": "",
            "abstract_text": "",
            "inspectable_text": "",
            "label": " ".join(matched_prefix),
            "evidence": "visible_fact",
        }
    if kind == "hidden_fact":
        return {
            "target": " ".join(matched_prefix) or target,
            "authority": AUTHORITY_AUTHORED_HIDDEN,
            "existence": True,
            "visibility": False,
            "inspectability": False,
            "interactable_id": "",
            "visible_fact": "",
            "hidden_fact": _clean(hit.get("text")),
            "abstract_text": "",
            "inspectable_text": "",
            "label": " ".join(matched_prefix),
            "evidence": "hidden_fact",
        }
    return {
        "target": " ".join(matched_prefix) or target,
        "authority": AUTHORITY_AUTHORED_ABSTRACT_REFERENCE,
        "existence": True,
        "visibility": False,
        "inspectability": False,
        "interactable_id": "",
        "visible_fact": "",
        "hidden_fact": "",
        "abstract_text": _clean(hit.get("text")),
        "inspectable_text": "",
        "label": " ".join(matched_prefix),
        "evidence": "abstract_reference",
    }


def metadata_from_classification(classification: Mapping[str, Any] | None) -> Dict[str, Any]:
    row = classification if isinstance(classification, Mapping) else {}
    authority = _clean(row.get("authority")) or AUTHORITY_UNTARGETED
    skip = authority in {
        AUTHORITY_UNTARGETED,
        AUTHORITY_AUTHORED_VISIBLE_FEATURE,
        AUTHORITY_AUTHORED_ABSTRACT_REFERENCE,
        AUTHORITY_AUTHORED_HIDDEN,
        AUTHORITY_UNSUPPORTED,
    } or (authority == AUTHORITY_AUTHORED_INTERACTABLE and not _clean(row.get("inspectable_text")))
    return {
        "referenced_surface_authority": authority,
        "referenced_surface_target": _clean(row.get("target")),
        "referenced_surface_existence": bool(row.get("existence")),
        "referenced_surface_visibility": bool(row.get("visibility")),
        "referenced_surface_inspectability": bool(row.get("inspectability")),
        "referenced_surface_interactable_id": _clean(row.get("interactable_id")),
        "referenced_surface_visible_fact": _clean(row.get("visible_fact")),
        "skip_unrelated_clue_discovery": skip,
    }


def _clause(text: str) -> str:
    raw = _clean(text).rstrip(".")
    if not raw:
        return ""
    return raw[0].lower() + raw[1:] if len(raw) > 1 else raw.lower()


def _surroundings_clause(scene_or_envelope: Mapping[str, Any] | None) -> str:
    scene_inner = _inner_scene(scene_or_envelope)
    facts = _string_list(scene_inner.get("visible_facts"))
    if facts:
        return _clause(facts[0])
    summary = _clean(scene_inner.get("summary"))
    if summary:
        return _clause(summary)
    location = _clean(scene_inner.get("location"))
    if location:
        return f"what is actually present in {location}"
    return "what is actually present here"


def render_referenced_surface_inspection_line(
    classification: Mapping[str, Any] | None,
    scene_or_envelope: Mapping[str, Any] | None = None,
) -> str:
    """Player-facing inspect result grounded only in the classified authority."""
    row = classification if isinstance(classification, Mapping) else {}
    authority = _clean(row.get("authority"))
    if authority == AUTHORITY_AUTHORED_INTERACTABLE:
        inspectable_text = _clean(row.get("inspectable_text"))
        if inspectable_text:
            return inspectable_text if inspectable_text.endswith((".", "!", "?")) else f"{inspectable_text}."
        label = _clean(row.get("label")) or _clean(row.get("target")) or "it"
        return f"You examine the {label}. Closer looking yields nothing further."
    if authority == AUTHORITY_AUTHORED_VISIBLE_FEATURE:
        fact = _clean(row.get("visible_fact"))
        if fact:
            return f"On closer inspection, {_clause(fact)}. Closer looking yields nothing further."
        return "On closer inspection, it is present, but closer looking yields nothing further."
    surroundings = _surroundings_clause(scene_or_envelope)
    if authority == AUTHORITY_AUTHORED_ABSTRACT_REFERENCE:
        return (
            "That remains something spoken of, not a surface you can inspect here. "
            f"What you can actually see is {surroundings}."
        )
    if authority == AUTHORITY_AUTHORED_HIDDEN:
        return f"You find no such thing among what is actually present. {surroundings[0].upper() + surroundings[1:]}."
    if authority == AUTHORITY_UNSUPPORTED:
        return f"Nothing here matches that. What you can actually see is {surroundings}."
    if authority == AUTHORITY_UNTARGETED:
        return (
            "You look again. Nothing new resolves into evidence. "
            f"What you can actually see is {surroundings}."
        )
    return ""


def classification_from_resolution(resolution: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(resolution, Mapping):
        return {}
    metadata = resolution.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    authority = _clean(metadata.get("referenced_surface_authority"))
    if not authority:
        return {}
    return {
        "target": _clean(metadata.get("referenced_surface_target")),
        "authority": authority,
        "existence": bool(metadata.get("referenced_surface_existence")),
        "visibility": bool(metadata.get("referenced_surface_visibility")),
        "inspectability": bool(metadata.get("referenced_surface_inspectability")),
        "interactable_id": _clean(metadata.get("referenced_surface_interactable_id")),
        "visible_fact": _clean(metadata.get("referenced_surface_visible_fact")),
        "hidden_fact": "",
        "abstract_text": "",
        "inspectable_text": _clean(resolution.get("clue_text")),
        "label": _clean(metadata.get("referenced_surface_target")),
        "evidence": authority,
    }
