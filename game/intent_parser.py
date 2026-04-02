"""Intent parser for freeform player input.

Converts typed player text into structured engine actions deterministically.
Scene context (exits, interactables, visible_facts) is used for target matching.
When the parser cannot confidently resolve intent, returns None → GPT fallback.

``adjudication_question_text`` is syntactic extraction only; whether that clause is treated as
procedural adjudication vs in-scene dialogue is decided by
:func:`game.interaction_context.resolve_directed_social_entry` (canonical entry) and
``game.adjudication``, not here.

Explicit spoken comma vocatives (including discourse-prefixed forms like "Alright Runner, …") are
resolved by :func:`game.interaction_context.resolve_spoken_vocative_target` using segmented
``spoken_text`` / merged addressing text — see that module for roster-aware precedence over
interlocutor continuity.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from game.leads import get_lead, pending_lead_surfaces_as_active_follow_opportunity
from game.storage import get_scene_runtime
from game.utils import slugify

_EXPLICIT_PURSUIT_COMMITMENT_SOURCE = "explicit_player_pursuit"
_EXPLICIT_PURSUIT_COMMITMENT_STRENGTH = 2

# Narrow explicit pursuit (Block 3). Must not fire on generic investigate/travel.
_RE_PURSUIT_BARE = re.compile(
    r"^\s*(?:i\s+(?:will\s+)?)?(?:follow|pursue)\s+the\s+lead\s*[\s\.,;?!]*$",
    re.IGNORECASE,
)
_RE_PURSUIT_GO_TO_THE_X_LEAD = re.compile(
    r"\b(?:go|head|travel)\s+to\s+the\s+(.+?)\s+lead\b",
    re.IGNORECASE,
)
_RE_PURSUIT_FOLLOW_THE_X_LEAD = re.compile(
    r"\b(?:follow|pursue)\s+the\s+(.+?)\s+lead\b",
    re.IGNORECASE,
)
_RE_PURSUIT_INVESTIGATE_THE_X_LEAD = re.compile(
    r"\binvestigate\s+the\s+(.+?)\s+lead\b",
    re.IGNORECASE,
)
# Qualified pursuit: explicit destination after "the lead to …" (fail-closed when unresolved).
_RE_QUAL_FOLLOW_PURSE_LEAD_TO = re.compile(
    r"\b(?:follow|pursue)\s+the\s+lead\s+to\s+(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
_RE_QUAL_GO_TO_THE_LEAD_TO = re.compile(
    r"\bgo\s+to\s+the\s+lead\s+to\s+(.+)$",
    re.IGNORECASE | re.MULTILINE,
)

# Returned from pursuit resolver → parse_freeform_to_action must not fall through to travel/follow.
_QUALIFIED_PURSUIT_FAILED = object()

# Action types compatible with exploration engine and normalize_scene_action
ACTION_TYPES = ("observe", "investigate", "interact", "scene_transition", "travel", "attack", "custom")
TURN_SEGMENT_KEYS = (
    "spoken_text",
    "declared_action_text",
    "adjudication_question_text",
    "observation_intent_text",
    "contingency_text",
)

# Verb patterns: (pattern, action_type, extracts_target)
# Order matters: more specific patterns first
OBSERVE_PATTERNS = [
    (r"\b(look\s+around|scan|survey|glance|take\s+in|watch\s+the\s+area)\b", "observe", False),
    (r"\bobserve\s+(?:the\s+)?(.+)\b", "observe", True),
]
INVESTIGATE_PATTERNS = [
    (r"\b(look\s+at|look\s+behind|look\s+under|look\s+in|look\s+for)\s+(?:the\s+)?(.+?)(?:\s+carefully|\s+closely)?\.?$", "investigate", True),
    (r"\b(inspect|examine|study|search|check)\s+(?:the\s+)?(.+?)(?:\s+carefully|\s+for\s+)?\.?$", "investigate", True),
    (r"\binvestigate\s+(?:the\s+)?(.+?)(?:\s+carefully)?\.?$", "investigate", True),
    (r"\b(dig\s+through|rifle\s+through|search)\s+(?:the\s+)?(.+?)\.?$", "investigate", True),
    (r"\b(look|search|inspect|examine)\b", "investigate", False),  # fallback when no target
]
INTERACT_PATTERNS = [
    (r"\b(talk\s+to|talk\s+with|speak\s+to|speak\s+with|ask|question|chat\s+with|greet)\s+(?:the\s+)?(.+?)(?:\s+about\s+)?\.?$", "interact", True),
    (r"\b(gauge|approach)\s+(?:the\s+)?(.+?)\.?$", "interact", True),
    (r"\b(talk|speak|ask|question)\b", "interact", False),
]
TRAVEL_PREFIXES = (
    "go ", "go to ", "follow ", "enter ", "travel ", "travel to ", "head ", "head to ",
    "walk ", "walk to ", "move ", "move to ", "journey ", "journey to ", "leave for ",
    "return to ", "take the route ", "take the path ", "run to ", "run ",
)
TRAVEL_BARE = ("go", "travel", "leave", "move", "north", "south", "east", "west")
ATTACK_PATTERNS = [
    (r"\b(attack|strike|hit|smite|slash|stab)\s+(?:the\s+)?(.+?)(?:\s+with\s+)?\.?$", "attack", True),
    (r"\b(cast|use)\s+(?:my\s+)?(.+?)\s+(?:at|on)\s+(?:the\s+)?(.+?)\.?$", "attack", True),  # e.g. "cast magic missile at orc"
    (r"\b(attack|strike|hit)\b", "attack", False),
]

_ADJUDICATION_TOKENS = (
    "need",
    "needed",
    "require",
    "required",
    "roll",
    "check",
    "can",
    "could",
    "would",
    "is",
    "are",
    "how far",
    "earshot",
    "who can hear",
    "in range",
)

_OBSERVATION_VERBS = (
    "see",
    "spot",
    "identify",
    "listen",
    "hear",
    "notice",
    "make out",
)


def _clean_clause(value: str | None) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    cleaned = re.sub(r"\s+([,.;:?!])", r"\1", cleaned)
    return cleaned or None


def _looks_like_npc_directed_second_person_question(low: str) -> bool:
    """Spoken questions to an NPC ('can you…', 'do you know…') — not GM adjudication clauses."""
    if not low or "?" not in low:
        return False
    if re.search(r"\b(?:can|could|would|will)\s+you\b", low):
        return True
    if re.search(r"\b(?:do|does|did)\s+you\s+know\b", low):
        return True
    if re.search(r"\bhave\s+you\s+seen\b", low):
        return True
    return False


def _looks_like_adjudication_question(text: str) -> bool:
    low = (text or "").strip().lower()
    if not low or "?" not in low:
        return False
    if _looks_like_npc_directed_second_person_question(low):
        return False
    return any(token in low for token in _ADJUDICATION_TOKENS)


def _extract_parenthetical_adjudication(text: str) -> tuple[str, Optional[str]]:
    if not isinstance(text, str) or not text.strip():
        return text, None
    for match in re.finditer(r"\(([^()]{1,200})\)", text):
        candidate = _clean_clause(match.group(1))
        if not candidate or not _looks_like_adjudication_question(candidate):
            continue
        updated = (text[: match.start()] + " " + text[match.end() :]).strip()
        return updated, candidate
    return text, None


def _extract_inline_adjudication_clause(text: str) -> tuple[str, Optional[str]]:
    if not isinstance(text, str) or "?" not in text:
        return text, None
    candidates = re.findall(r"([^?.!]{0,220}\?)", text)
    for raw in reversed(candidates):
        candidate = _clean_clause(raw)
        if not candidate or not _looks_like_adjudication_question(candidate):
            continue
        updated = text.replace(raw, " ", 1).strip()
        return updated, candidate
    return text, None


def _extract_contingency(text: str) -> tuple[str, Optional[str]]:
    if not isinstance(text, str):
        return text, None
    low = text.lower()
    m_then = re.search(r"\bif\b(.+?)\bthen\b(.+)", low)
    if m_then:
        start, end = m_then.span()
        contingency_raw = text[start:end].strip()
        remainder = text[end:].strip(" ,;.")
        return (remainder or text), _clean_clause(contingency_raw)
    if low.startswith("if "):
        comma_idx = text.find(",")
        if 3 <= comma_idx <= 200:
            contingency_raw = text[:comma_idx]
            remainder = text[comma_idx + 1 :].strip(" ,;.")
            return (remainder or text), _clean_clause(contingency_raw)
    return text, None


def _extract_observation_intent(text: str) -> tuple[str, Optional[str]]:
    if not isinstance(text, str):
        return text, None
    joined_verbs = "|".join(re.escape(v) for v in _OBSERVATION_VERBS)
    pattern = (
        r"\b(?:and|while|as)\s+(?:i am |i'm |i )?"
        r"(?:trying|tries|try|attempting|attempts|attempt)\s+to\s+"
        r"(?:"
        + joined_verbs
        + r")\b[^.?!;]*"
    )
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        candidate = _clean_clause(m.group(0))
        updated = (text[: m.start()] + " " + text[m.end() :]).strip()
        return updated, candidate
    return text, None


def segment_mixed_player_turn(text: str) -> Dict[str, Optional[str]]:
    """Extract a narrow, inspectable mixed-turn shape before intent classification.

    This is intentionally conservative and deterministic. It does not attempt full
    natural-language decomposition, and only fills fields when cues are clear.
    """
    out: Dict[str, Optional[str]] = {k: None for k in TURN_SEGMENT_KEYS}
    if not isinstance(text, str):
        return out
    raw = text.strip()
    if not raw:
        return out

    spoken_matches = re.findall(r'"([^"\n]{1,240})"', raw)
    if spoken_matches:
        out["spoken_text"] = _clean_clause(" ".join(spoken_matches))
    working = re.sub(r'"[^"\n]{1,240}"', " ", raw)

    working, parenthetical_q = _extract_parenthetical_adjudication(working)
    if parenthetical_q:
        out["adjudication_question_text"] = parenthetical_q
    else:
        working, inline_q = _extract_inline_adjudication_clause(working)
        if inline_q:
            out["adjudication_question_text"] = inline_q

    working, contingency = _extract_contingency(working)
    if contingency:
        out["contingency_text"] = contingency

    working, observation = _extract_observation_intent(working)
    if observation:
        out["observation_intent_text"] = observation

    declared = _clean_clause(working)
    if declared:
        out["declared_action_text"] = declared
    elif not any(out.values()):
        out["declared_action_text"] = raw
    return out


def _extract_target(pattern: str, text: str, group: int = 1) -> Optional[str]:
    """Extract target from regex match. Group 1 or 2 typically holds the target noun phrase."""
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    for g in (group, 2, 1):
        if m.lastindex and g <= m.lastindex:
            t = m.group(g)
            if t and len(t.strip()) > 0 and len(t.strip()) < 80:
                return t.strip()
    return None


def _match_exit(dest_hint: str, exits: List[Dict[str, Any]]) -> Optional[str]:
    """Match a destination hint to an exit's label; return target_scene_id or None."""
    if not dest_hint or not exits:
        return None
    dh = dest_hint.lower().strip()
    for ex in exits:
        if not isinstance(ex, dict):
            continue
        label = (ex.get("label") or "").strip().lower()
        target = (ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not target:
            continue
        if dh in label or label in dh:
            return target
        if slugify(dh) in slugify(label) or slugify(label) in slugify(dh):
            return target
    return None


def _match_target_to_interactable(target_slug: str, interactables: List[Dict[str, Any]]) -> Optional[str]:
    """Match target slug to an interactable id. Returns interactable id or None."""
    if not target_slug or not interactables:
        return None
    for i in interactables:
        if not isinstance(i, dict):
            continue
        i_id = str(i.get("id") or "").strip()
        if not i_id:
            continue
        i_slug = slugify(i_id)
        if target_slug in i_slug or i_slug in target_slug:
            return i_id
    return None


def _match_target_to_visible_fact(target_slug: str, visible_facts: List[Any]) -> Optional[str]:
    """Match target slug to a visible fact (string). Returns the fact text or None."""
    if not target_slug or not visible_facts:
        return None
    for f in visible_facts:
        text = str(f).strip() if f else ""
        if not text:
            continue
        f_slug = slugify(text)
        if target_slug in f_slug or f_slug in target_slug:
            return text
    return None


def _build_action(
    action_type: str,
    label: str,
    prompt: str,
    *,
    target_scene_id: Optional[str] = None,
    target_id: Optional[str] = None,
    action_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build canonical structured action for the engine."""
    aid = action_id or (slugify(label) or slugify(prompt) or action_type)[:40]
    out: Dict[str, Any] = {
        "id": aid,
        "label": label,
        "type": action_type,
        "prompt": prompt,
        "targetSceneId": target_scene_id,
        "target_scene_id": target_scene_id,
    }
    if target_id:
        out["target_id"] = target_id
        out["targetEntityId"] = target_id
    if metadata:
        out["metadata"] = metadata
    return out


def _actionable_pending_with_registry_rows(
    session: Dict[str, Any], scene_id: str
) -> List[Dict[str, Any]]:
    """Pending leads that carry an authoritative id with a real registry row (no clue_id fallback)."""
    if not isinstance(session, dict) or not isinstance(scene_id, str) or not scene_id.strip():
        return []
    rt = get_scene_runtime(session, scene_id)
    pending = rt.get("pending_leads") or []
    out: List[Dict[str, Any]] = []
    for p in pending:
        if not isinstance(p, dict):
            continue
        aid = str(p.get("authoritative_lead_id") or "").strip()
        if not aid:
            continue
        if not pending_lead_surfaces_as_active_follow_opportunity(session, p):
            continue
        out.append(p)
    return out


def _commitment_meta_for_pursuit(authoritative_lead_id: str) -> Dict[str, Any]:
    return {
        "authoritative_lead_id": authoritative_lead_id,
        "commitment_source": _EXPLICIT_PURSUIT_COMMITMENT_SOURCE,
        "commitment_strength": _EXPLICIT_PURSUIT_COMMITMENT_STRENGTH,
    }


def _strip_trailing_pursuit_fragment_punct(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[\s\.,;:!?]+$", "", s)
    return s.strip()


def _strict_unique_exit_destination(target_text: str, exits: List[Dict[str, Any]]) -> Optional[str]:
    """Map target_text to exactly one exit target_scene_id (casefold or slugify on label); else None."""
    raw = (target_text or "").strip()
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


def _npc_location_from_world(world: Optional[Dict[str, Any]], npc_id: str) -> Optional[str]:
    nid = str(npc_id or "").strip()
    if not nid or not isinstance(world, dict):
        return None
    for n in world.get("npcs") or []:
        if not isinstance(n, dict):
            continue
        if str(n.get("id") or "").strip() != nid:
            continue
        loc = str(n.get("location") or n.get("scene_id") or "").strip()
        return loc or None
    return None


def _town_crier_find_name_from_label(label: str) -> Optional[str]:
    m = re.match(
        r"^\s*find\s+(.+?)\s*\(\s*town\s+crier\s*\)\s*$",
        (label or "").strip(),
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    inner = m.group(1).strip()
    return inner or None


def _npc_destination_matches_target(
    npc_id: str,
    target_cf: str,
    target_slug: str,
    *,
    world: Optional[Dict[str, Any]],
    reg_row: Optional[Dict[str, Any]],
    pending_text: str,
) -> bool:
    nid = str(npc_id or "").strip()
    if not nid:
        return False
    if nid.casefold() == target_cf or slugify(nid) == target_slug:
        return True
    if isinstance(world, dict):
        for n in world.get("npcs") or []:
            if not isinstance(n, dict):
                continue
            if str(n.get("id") or "").strip() != nid:
                continue
            name = str(n.get("name") or "").strip().casefold()
            if name == target_cf:
                return True
            for al in n.get("aliases") or []:
                if isinstance(al, str) and al.strip().casefold() == target_cf:
                    return True
    for label in (pending_text, str((reg_row or {}).get("title") or "")):
        if not label or not str(label).strip():
            continue
        cn = _town_crier_find_name_from_label(str(label))
        if cn and cn.casefold() == target_cf:
            return True
    return False


def _scene_destination_matches_target(
    leads_to_scene: str,
    target_cf: str,
    target_slug: str,
    exit_tid: Optional[str],
) -> bool:
    ts = str(leads_to_scene or "").strip()
    if not ts:
        return False
    if ts.casefold() == target_cf or slugify(ts) == target_slug:
        return True
    if exit_tid and ts == exit_tid:
        return True
    return False


def _pending_row_resolved_scene_id(
    p: Dict[str, Any],
    world: Optional[Dict[str, Any]],
) -> Optional[str]:
    ts = str(p.get("leads_to_scene") or "").strip()
    if ts:
        return ts
    npc = str(p.get("leads_to_npc") or "").strip()
    if npc:
        return _npc_location_from_world(world, npc)
    return None


def _build_pursuit_scene_transition_action(
    prompt: str,
    p: Dict[str, Any],
    *,
    world: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    aid = str(p.get("authoritative_lead_id") or "").strip()
    if not aid:
        return None
    ts = str(p.get("leads_to_scene") or "").strip()
    npc = str(p.get("leads_to_npc") or "").strip()
    meta = _commitment_meta_for_pursuit(aid)
    if ts:
        return _build_action(
            "scene_transition",
            prompt,
            prompt,
            target_scene_id=ts,
            metadata=meta,
        )
    if npc:
        loc = _npc_location_from_world(world, npc)
        if not loc:
            return None
        return _build_action(
            "scene_transition",
            prompt,
            prompt,
            target_scene_id=loc,
            target_id=npc,
            metadata=meta,
        )
    return None


def is_qualified_pursuit_shaped(text: str | None) -> bool:
    """True when *text* is explicit target-qualified lead pursuit phrasing (not bare ``follow the lead``).

    Chat routing uses this to run :func:`parse_freeform_to_action` / exploration pursuit resolution
    before dialogue-lock social follow-up. Matches the same patterns as
    :func:`_extract_qualified_pursuit_target_text`.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    return _extract_qualified_pursuit_target_text(text) is not None


def _extract_qualified_pursuit_target_text(text: str) -> Optional[str]:
    """If input matches a qualified pursuit phrase, return normalized target fragment; else None."""
    raw = (text or "").strip()
    if not raw or _RE_PURSUIT_BARE.fullmatch(raw):
        return None
    m = _RE_QUAL_FOLLOW_PURSE_LEAD_TO.search(raw) or _RE_QUAL_GO_TO_THE_LEAD_TO.search(raw)
    if m:
        frag = _strip_trailing_pursuit_fragment_punct(m.group(1))
        return frag or None
    low = raw.lower()
    m = _RE_PURSUIT_GO_TO_THE_X_LEAD.search(low)
    if m:
        frag = _strip_trailing_pursuit_fragment_punct(m.group(1))
        return frag or None
    m = _RE_PURSUIT_INVESTIGATE_THE_X_LEAD.search(low)
    if m:
        frag = _strip_trailing_pursuit_fragment_punct(m.group(1))
        return frag or None
    m = _RE_PURSUIT_FOLLOW_THE_X_LEAD.search(low)
    if m:
        frag = _strip_trailing_pursuit_fragment_punct(m.group(1))
        if not frag or frag.strip().casefold() == "lead":
            return None
        return frag
    return None


def _resolve_qualified_pursuit_target_to_row(
    target_fragment: str,
    scene: Dict[str, Any],
    session: Dict[str, Any],
    world: Optional[Dict[str, Any]],
    actionable: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Pick exactly one pending row for qualified pursuit; None if ambiguous or unresolved."""
    raw = (target_fragment or "").strip()
    if not raw:
        return None
    target_cf = raw.casefold()
    target_slug = slugify(raw)
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    exit_tid = _strict_unique_exit_destination(raw, exits)

    matches_a: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for p in actionable:
        if not isinstance(p, dict):
            continue
        aid = str(p.get("authoritative_lead_id") or "").strip()
        matched = False
        ts = str(p.get("leads_to_scene") or "").strip()
        npc = str(p.get("leads_to_npc") or "").strip()
        reg_row = get_lead(session, aid) if aid else None
        pend_txt = str(p.get("text") or "")
        if ts and _scene_destination_matches_target(ts, target_cf, target_slug, exit_tid):
            matched = True
        if npc and _npc_destination_matches_target(
            npc, target_cf, target_slug, world=world, reg_row=reg_row, pending_text=pend_txt
        ):
            matched = True
        if matched and aid and aid not in seen_ids:
            seen_ids.add(aid)
            matches_a.append(p)

    chosen: Optional[Dict[str, Any]] = None
    if len(matches_a) == 1:
        chosen = matches_a[0]
    elif len(matches_a) > 1:
        return None
    else:
        text_hits = [
            p
            for p in actionable
            if isinstance(p, dict) and str(p.get("text") or "").strip().casefold() == target_cf
        ]
        if len(text_hits) == 1:
            chosen = text_hits[0]
        elif len(text_hits) > 1:
            return None
        else:
            slug_hits = [
                p
                for p in actionable
                if isinstance(p, dict)
                and str(p.get("text") or "").strip()
                and slugify(str(p.get("text") or "")) == target_slug
            ]
            if len(slug_hits) != 1:
                return None
            chosen = slug_hits[0]

    if not isinstance(chosen, dict):
        return None
    if not _pending_row_resolved_scene_id(chosen, world):
        return None
    return chosen


def _try_explicit_pursuit_scene_transition(
    text: str,
    scene: Dict[str, Any],
    session: Dict[str, Any],
    *,
    world: Optional[Dict[str, Any]] = None,
) -> Any:
    """Explicit pursuit: scene_transition + commitment metadata, or _QUALIFIED_PURSUIT_FAILED, or None."""
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return None
    exits = scene.get("exits") or []
    actionable = _actionable_pending_with_registry_rows(session, scene_id)

    q_target = _extract_qualified_pursuit_target_text(text)
    if q_target is not None:
        if not actionable:
            return _QUALIFIED_PURSUIT_FAILED
        row = _resolve_qualified_pursuit_target_to_row(q_target, scene, session, world, actionable)
        if row is None:
            return _QUALIFIED_PURSUIT_FAILED
        act = _build_pursuit_scene_transition_action(text, row, world=world)
        return act if act is not None else _QUALIFIED_PURSUIT_FAILED

    if not actionable:
        if _RE_PURSUIT_BARE.fullmatch(text.strip()):
            return _QUALIFIED_PURSUIT_FAILED
        return None

    if _RE_PURSUIT_BARE.fullmatch(text.strip()):
        if len(actionable) != 1:
            return _QUALIFIED_PURSUIT_FAILED
        p0 = actionable[0]
        act = _build_pursuit_scene_transition_action(text, p0, world=world)
        return act

    return None


def parse_freeform_to_action(
    text: str,
    scene_envelope: Optional[Dict[str, Any]] = None,
    *,
    session: Optional[Dict[str, Any]] = None,
    world: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Parse freeform player input into a structured engine action.

    Uses verb patterns and scene context (exits, interactables, visible_facts)
    to map common commands to structured actions. Returns None when ambiguous
    → caller falls back to GPT narration.

    When ``session`` is provided, narrow explicit pursuit phrases may attach
    ``metadata.authoritative_lead_id`` (and commitment fields) on a deterministic
    ``scene_transition``; no lead state is mutated here.

    ``world`` is optional; when set, ``leads_to_npc`` rows resolve ``target_scene_id`` from
    ``world[\"npcs\"]`` (``location`` / ``scene_id``). Qualified pursuit phrases that name a
    target but cannot be resolved return ``None`` and do not fall through to generic travel.

    Returns:
        Structured action dict with id, label, type, prompt, targetSceneId?,
        target_id?, or None if intent cannot be confidently resolved.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.strip()
    if not t:
        return None
    low = t.lower()

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    exits = scene.get("exits") or []
    interactables = scene.get("interactables") or []
    visible_facts = scene.get("visible_facts") or []

    # ---- 0. Qualified explicit pursuit (fail-closed) + bare follow-the-lead (session) ----
    q_frag = _extract_qualified_pursuit_target_text(t)
    if q_frag is not None and not isinstance(session, dict):
        return None
    if isinstance(session, dict):
        pursuit = _try_explicit_pursuit_scene_transition(t, scene, session, world=world)
        if pursuit is _QUALIFIED_PURSUIT_FAILED:
            return None
        if pursuit is not None:
            return pursuit

    # ---- 1. Travel / scene_transition ----
    for prefix in sorted(TRAVEL_PREFIXES, key=len, reverse=True):
        if low.startswith(prefix):
            dest_hint = t[len(prefix) :].strip()
            target_id = _match_exit(dest_hint, exits) or _match_exit(t, exits)
            return _build_action(
                "scene_transition" if target_id else "travel",
                t,
                t,
                target_scene_id=target_id,
            )
    if low in TRAVEL_BARE:
        target_id = _match_exit(t, exits)
        return _build_action(
            "scene_transition" if target_id else "travel",
            t,
            t,
            target_scene_id=target_id,
        )
    # Direction-only: "north", "south", etc. when no prefix
    if low in ("north", "south", "east", "west") and exits:
        target_id = _match_exit(low, exits)
        if target_id:
            return _build_action("scene_transition", t, t, target_scene_id=target_id)

    # ---- 2. Attack (API routes to combat when in_combat; otherwise falls back to GPT) ----
    for pattern, action_type, extracts in ATTACK_PATTERNS:
        m = re.search(pattern, low)
        if m:
            target = None
            if extracts and m.lastindex:
                # Group 2 for "attack X"; group 3 for "cast X at Y"
                if m.lastindex >= 3:
                    target = m.group(3).strip()
                elif m.lastindex >= 2:
                    target = m.group(2).strip()
                if target and len(target) > 50:
                    target = target[:50]
            return _build_action(
                "attack",
                t,
                t,
                target_id=target,
                metadata={"intent": "attack"},
            )

    # ---- 3. Observe (check before investigate; "look around" != "look at X") ----
    for pattern, action_type, extracts in OBSERVE_PATTERNS:
        if re.search(pattern, low):
            target = _extract_target(pattern, low, 2) if extracts else None
            if target:
                target_slug = slugify(target)
                matched = _match_target_to_interactable(target_slug, interactables)
                if matched:
                    return _build_action("investigate", t, t, target_id=matched, action_id=matched)
                matched_fact = _match_target_to_visible_fact(target_slug, visible_facts)
                if matched_fact:
                    aid = slugify(target)[:40] or "observe"
                    return _build_action("investigate", t, t, target_id=aid, action_id=aid)
            return _build_action("observe", t, t)

    # ---- 4. Investigate (with target extraction) ----
    for pattern, action_type, extracts in INVESTIGATE_PATTERNS:
        m = re.search(pattern, low)
        if m:
            target = None
            if extracts and m.lastindex and m.lastindex >= 2:
                target = m.group(2).strip() if m.lastindex >= 2 else (m.group(1) if m.lastindex >= 1 else None)
            elif extracts and m.lastindex:
                target = m.group(1).strip() if m.lastindex >= 1 else None
            target_slug = slugify(target) if target else None
            matched_id = _match_target_to_interactable(target_slug, interactables) if target_slug else None
            aid = matched_id or (slugify(t) or "investigate")[:40]
            return _build_action(
                "investigate",
                t,
                t,
                target_id=matched_id or target,
                action_id=aid,
            )

    # ---- 4. Observe (general look-around) ----
    for pattern, action_type, extracts in OBSERVE_PATTERNS:
        if re.search(pattern, low):
            target = _extract_target(pattern, low, 2) if extracts else None
            if target:
                target_slug = slugify(target)
                matched = _match_target_to_interactable(target_slug, interactables)
                if matched:
                    return _build_action("investigate", t, t, target_id=matched, action_id=matched)
                matched_fact = _match_target_to_visible_fact(target_slug, visible_facts)
                if matched_fact:
                    aid = slugify(target)[:40] or "observe"
                    return _build_action("investigate", t, t, target_id=aid, action_id=aid)
            return _build_action("observe", t, t)

    # ---- 5. Interact (social) ----
    for pattern, action_type, extracts in INTERACT_PATTERNS:
        if re.search(pattern, low):
            target = None
            if extracts:
                m = re.search(pattern, low)
                if m and m.lastindex >= 2:
                    target = m.group(2).strip()
            target_slug = slugify(target) if target else None
            matched_id = _match_target_to_interactable(target_slug, interactables) if target_slug else None
            return _build_action(
                "interact",
                t,
                t,
                target_id=matched_id or target,
            )

    # ---- 6. Legacy fallbacks from original parse_intent ----
    if "follow" in low and exits:
        target_id = _match_exit(low.replace("follow", "").strip(), exits) or _match_exit("follow", exits)
        if target_id:
            return _build_action("scene_transition", t, t, target_scene_id=target_id)
        return _build_action("interact", t, t, metadata={"intent": "follow_target"})
    if "leave" in low or "exit" in low:
        target_id = _match_exit(low, exits)
        return _build_action(
            "scene_transition" if target_id else "travel",
            t,
            t,
            target_scene_id=target_id,
        )

    return None


def parse_intent(text: str) -> Optional[Dict[str, Any]]:
    """Lightweight fallback when no scene context. Returns structured intent or None.

    Used when parse_freeform_to_action(text, scene) returns None but we want
    to try a minimal keyword match. Prefer parse_freeform_to_action when
    scene_envelope is available.
    """
    result = parse_freeform_to_action(text, scene_envelope=None)
    if result is not None:
        return result
    # Minimal patterns without scene (no exit matching, no interactable matching)
    if not text or not isinstance(text, str):
        return None
    low = text.strip().lower()
    if not low:
        return None

    if "follow" in low:
        return _build_action("interact", text.strip(), text.strip(), metadata={"intent": "follow_target"})
    if "leave" in low or "exit" in low:
        return _build_action("travel", text.strip(), text.strip(), metadata={"intent": "leave_area"})
    if "search" in low or "look" in low or "investigate" in low:
        return _build_action("investigate", text.strip(), text.strip())
    if "talk" in low or "ask" in low:
        return _build_action("interact", text.strip(), text.strip(), metadata={"intent": "conversation"})

    return None
