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
from typing import Any, Dict, List, Optional, Tuple

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

# Passive wait / observe-interruption (Block 3): narrow declared-action shapes that must not route as social follow-up.
_PASSIVE_INTERRUPTION_WAIT_PATTERNS: Tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(?:wait|waits|waiting)\s+for\b[^?.!]{0,120}\bto\s+pass\b",
        r"\b(?:let|lets|letting)\s+(?:the\s+)?(?:shouting|disturbance|commotion|interruption|noise|ruckus)\s+pass\b",
        r"\blooks?\s+to\s+the\s+distraction\b",
        r"\bwatches?\s+the\s+commotion\b",
        r"\bpauses?\s+to\s+observe\b",
        r"\bholds?\s+position\s+and\s+waits\b",
        r"\b(?:wait|waits|waiting)\s+for\s+(?:the\s+)?interruption\s+to\s+end\b",
    )
)
_RE_PASSIVE_WAIT_BLOCKS_DIRECTED_SPEECH = re.compile(
    r"\basks?\s+the\b|\bask\s+the\b|\b(?:i|we)\s+asks?\s+",
    re.IGNORECASE,
)
_RE_PASSIVE_WAIT_BLOCKS_ASK_ABOUT = re.compile(r"\basks?\s+about\b", re.IGNORECASE)

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
_MIXED_INVESTIGATION_VERB_RE = re.compile(
    r"\b(?P<verb>study|studies|inspect|inspects|examine|examines|check|checks|search|searches|look\s+at|looks\s+at|look\s+for|looks\s+for)\b",
    re.IGNORECASE,
)
_MIXED_INVESTIGATION_TARGET_RE = re.compile(
    r"\b(?:study|studies|inspect|inspects|examine|examines|check|checks|search|searches|look\s+at|looks\s+at|look\s+for|looks\s+for)\s+(?:the\s+|a\s+|an\s+|this\s+|that\s+)?(?P<target>[^.;?!]{1,120})",
    re.IGNORECASE,
)
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


def _declared_matches_passive_interruption_wait(declared: str) -> bool:
    """True when *declared* is a narrow passive wait / observe-disturbance clause (lowercasing internally)."""
    d = (declared or "").strip()
    if not d or "?" in d:
        return False
    low = d.lower()
    if re.match(r"^\s*(?:what|where|why|how|who|which|when)\b", low):
        return False
    if _RE_PASSIVE_WAIT_BLOCKS_DIRECTED_SPEECH.search(low) or _RE_PASSIVE_WAIT_BLOCKS_ASK_ABOUT.search(low):
        return False
    return any(p.search(low) for p in _PASSIVE_INTERRUPTION_WAIT_PATTERNS)


def passive_interruption_wait_declared_action_text(
    segmented_turn: Optional[Dict[str, Any]],
    *,
    raw_player_text: Optional[str] = None,
) -> Optional[str]:
    """Return the declared clause to classify as passive wait, or None when guards fail."""
    if not isinstance(segmented_turn, dict):
        return None
    spoken = segmented_turn.get("spoken_text")
    if isinstance(spoken, str) and spoken.strip():
        return None
    if isinstance(segmented_turn.get("adjudication_question_text"), str) and str(
        segmented_turn.get("adjudication_question_text") or ""
    ).strip():
        return None
    declared = segmented_turn.get("declared_action_text")
    if not isinstance(declared, str) or not declared.strip():
        raw = (raw_player_text or "").strip()
        if not raw or '"' in raw:
            return None
        declared = raw
    if not _declared_matches_passive_interruption_wait(declared):
        return None
    return declared.strip()


def maybe_build_passive_interruption_wait_action(
    segmented_turn: Optional[Dict[str, Any]],
    raw_player_text: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Deterministic observe action for passive wait / interruption beats (not social follow-up)."""
    declared = passive_interruption_wait_declared_action_text(
        segmented_turn, raw_player_text=raw_player_text
    )
    if not declared:
        return None
    label = (raw_player_text or "").strip() or declared
    meta = {
        "passive_interruption_wait": True,
        "parser_lane": "passive_interruption_wait",
    }
    return _build_action(
        "observe",
        label[:200],
        declared,
        metadata=meta,
    )


def _raw_text_eligible_for_passive_interruption_wait_parse(text: str) -> bool:
    t = (text or "").strip()
    if not t or '"' in t:
        return False
    return True


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


def _scene_grounding_terms(scene: Dict[str, Any]) -> List[Dict[str, str]]:
    """Scene-authored target surfaces for shape-based mixed investigation recovery."""
    terms: List[Dict[str, str]] = []
    for i in scene.get("interactables") or []:
        if not isinstance(i, dict):
            continue
        target_id = str(i.get("id") or "").strip()
        if not target_id:
            continue
        for field in ("id", "label", "name"):
            value = str(i.get(field) or "").strip()
            if value:
                terms.append({"kind": "interactable", "text": value, "target_id": target_id})
        for alias in i.get("aliases") or []:
            value = str(alias or "").strip()
            if value:
                terms.append({"kind": "interactable", "text": value, "target_id": target_id})
    for fact in scene.get("visible_facts") or []:
        text = str(fact or "").strip()
        if text:
            terms.append({"kind": "visible_fact", "text": text, "target_id": slugify(text)[:40] or "visible_fact"})
    for clue in scene.get("discoverable_clues") or []:
        rec = clue if isinstance(clue, dict) else {"id": slugify(str(clue)), "text": str(clue)}
        cid = str(rec.get("id") or slugify(str(rec.get("text") or ""))).strip()
        for field in ("id", "text", "label", "name"):
            value = str(rec.get(field) or "").strip()
            if value:
                terms.append({"kind": "discoverable_clue", "text": value, "target_id": cid or slugify(value)[:40]})
    for action in scene.get("actions") or scene.get("suggested_actions") or []:
        if not isinstance(action, dict):
            continue
        aid = str(action.get("id") or action.get("action_id") or "").strip()
        for field in ("label", "name", "prompt"):
            value = str(action.get(field) or "").strip()
            if value:
                terms.append({"kind": "suggested_action", "text": value, "target_id": aid or slugify(value)[:40]})
    return terms


def _ground_scene_investigation_target(target_text: str, scene: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Resolve an extracted target against scene-authored surfaces only."""
    target_slug = slugify(target_text or "")
    if not target_slug:
        return None
    best: Optional[Dict[str, str]] = None
    best_score = -1
    priority = {
        "interactable": 400,
        "suggested_action": 300,
        "discoverable_clue": 200,
        "visible_fact": 100,
    }
    for term in _scene_grounding_terms(scene):
        surface = term.get("text") or ""
        surface_slug = slugify(surface)
        if not surface_slug:
            continue
        if target_slug in surface_slug or surface_slug in target_slug:
            score = priority.get(term.get("kind") or "", 0) + len(surface_slug)
            if score > best_score:
                best = term
                best_score = score
    return best


def _split_mixed_investigation_detail_question(text: str) -> tuple[Optional[str], Optional[str]]:
    if not isinstance(text, str) or "?" not in text or '"' in text:
        return None, None
    q_end = text.rfind("?")
    if q_end < 0:
        return None, None
    prefix = text[:q_end]
    boundary = max(prefix.rfind("."), prefix.rfind(";"), prefix.rfind("\n"))
    if boundary < 0:
        comma_q = re.search(
            r"[,]\s*(?=(?:does|do|did|is|are|was|were|can|could|would|will|anything|any|what|where|why|how)\b)",
            prefix,
            re.IGNORECASE,
        )
        boundary = comma_q.start() if comma_q else -1
    if boundary < 0:
        return None, None
    action_part = _clean_clause(text[:boundary])
    question = _clean_clause(text[boundary + 1 : q_end + 1])
    if not action_part or not question:
        return None, None
    q_low = question.lower()
    if _looks_like_npc_directed_second_person_question(q_low):
        return None, None
    if not _MIXED_INVESTIGATION_VERB_RE.search(action_part):
        return None, None
    return action_part, question


def _recover_mixed_scene_object_investigation(
    text: str,
    scene: Dict[str, Any],
    *,
    detail_question_text: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    if isinstance(detail_question_text, str) and detail_question_text.strip() and "?" not in text:
        action_part = _clean_clause(text)
        question = _clean_clause(detail_question_text)
    else:
        action_part, question = _split_mixed_investigation_detail_question(text)
    if not action_part or not question:
        return None
    candidates = [_clean_clause(c) for c in re.split(r"[.;]\s*", action_part)]
    action_clause = None
    for candidate in reversed([c for c in candidates if c]):
        if _MIXED_INVESTIGATION_VERB_RE.search(candidate):
            action_clause = candidate
            break
    if not action_clause:
        action_clause = action_part
    m = _MIXED_INVESTIGATION_TARGET_RE.search(action_clause)
    if not m:
        return None
    target = _clean_clause(m.group("target"))
    if not target:
        return None
    grounding = _ground_scene_investigation_target(target, scene)
    if grounding is None:
        return None
    target_id = str(grounding.get("target_id") or "").strip()
    aid = target_id or (slugify(action_clause) or "investigate")[:40]
    return _build_action(
        "investigate",
        action_clause,
        action_clause,
        target_id=target_id or None,
        action_id=aid,
        metadata={
            "parser_lane": "mixed_scene_object_investigation",
            "mixed_turn_detail_question": question,
            "adjudication_or_detail_question_text": question,
            "recovered_action_clause": action_clause,
            "scene_grounding_kind": grounding.get("kind"),
            "scene_grounding_text": grounding.get("text"),
        },
    )


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


def _npc_display_name_from_world(world: Optional[Dict[str, Any]], npc_id: str) -> Optional[str]:
    nid = str(npc_id or "").strip()
    if not nid or not isinstance(world, dict):
        return None
    for n in world.get("npcs") or []:
        if not isinstance(n, dict):
            continue
        if str(n.get("id") or "").strip() != nid:
            continue
        name = str(n.get("name") or "").strip()
        return name or None
    return None


def _world_npc_ids_matching_name_fragment(
    target_cf: str,
    target_slug: str,
    world: Optional[Dict[str, Any]],
) -> set[str]:
    """NPC ids in world whose id/name/aliases match the pursuit fragment (for fail-closed guard)."""
    out: set[str] = set()
    if not isinstance(world, dict):
        return out
    for n in world.get("npcs") or []:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or "").strip()
        if not nid:
            continue
        if _npc_destination_matches_target(
            nid,
            target_cf,
            target_slug,
            world=world,
            reg_row=None,
            pending_text="",
        ):
            out.add(nid)
    return out


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
    base = _commitment_meta_for_pursuit(aid)
    if ts:
        meta = {
            **base,
            "target_kind": "scene",
            "destination_scene_id": ts,
        }
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
        meta = {
            **base,
            "target_kind": "npc",
            "target_npc_id": npc,
            "destination_scene_id": loc,
        }
        tname = _npc_display_name_from_world(world, npc)
        if tname:
            meta["target_npc_name"] = tname
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
    """Pick exactly one pending row for qualified pursuit; None if ambiguous or unresolved.

    Scene-target and NPC-target leads are distinguished: naming a known NPC without an NPC-target
    lead fails closed (no repurposing scene-only leads). Text/slug fallbacks bind scene/thread
    labels, not world NPC names that lack a ``leads_to_npc`` row.
    """
    raw = (target_fragment or "").strip()
    if not raw:
        return None
    target_cf = raw.casefold()
    target_slug = slugify(raw)
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    exit_tid = _strict_unique_exit_destination(raw, exits)

    npc_matches: List[Dict[str, Any]] = []
    scene_matches: List[Dict[str, Any]] = []
    seen_npc: set[str] = set()
    seen_scene: set[str] = set()
    for p in actionable:
        if not isinstance(p, dict):
            continue
        aid = str(p.get("authoritative_lead_id") or "").strip()
        if not aid:
            continue
        ts = str(p.get("leads_to_scene") or "").strip()
        npc = str(p.get("leads_to_npc") or "").strip()
        reg_row = get_lead(session, aid) if aid else None
        pend_txt = str(p.get("text") or "")
        if npc and _npc_destination_matches_target(
            npc, target_cf, target_slug, world=world, reg_row=reg_row, pending_text=pend_txt
        ):
            if aid not in seen_npc:
                seen_npc.add(aid)
                npc_matches.append(p)
            continue
        if ts and _scene_destination_matches_target(ts, target_cf, target_slug, exit_tid):
            if aid not in seen_scene:
                seen_scene.add(aid)
                scene_matches.append(p)

    chosen: Optional[Dict[str, Any]] = None
    if len(npc_matches) == 1:
        chosen = npc_matches[0]
    elif len(npc_matches) > 1:
        return None
    elif len(scene_matches) == 1:
        chosen = scene_matches[0]
    elif len(scene_matches) > 1:
        return None
    else:
        world_npc_ids = _world_npc_ids_matching_name_fragment(target_cf, target_slug, world)
        if world_npc_ids:
            has_npc_lead = any(
                str(p.get("leads_to_npc") or "").strip() in world_npc_ids
                for p in actionable
                if isinstance(p, dict)
            )
            if not has_npc_lead:
                return None
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
    segmented_turn: Optional[Dict[str, Any]] = None,
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

    NPC-target rows include ``metadata.target_kind`` ``"npc"``, ``target_npc_id``, optional
    ``target_npc_name``, and ``destination_scene_id`` as travel context (authoritative target is
    the NPC, not the scene alone).

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

    from game.interaction_context import (
        human_adjacent_continuity_carryover_metadata_if_eligible,
        should_emit_observe_for_local_observation_parse,
    )

    co_md = human_adjacent_continuity_carryover_metadata_if_eligible(
        t,
        scene_envelope if isinstance(scene_envelope, dict) else None,
        session,
        world,
        segmented_turn if isinstance(segmented_turn, dict) else None,
    )
    if co_md:
        return _build_action("observe", t, t, metadata=co_md)

    if should_emit_observe_for_local_observation_parse(
        t,
        scene_envelope if isinstance(scene_envelope, dict) else None,
        session=session,
        world=world,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
    ):
        return _build_action(
            "observe",
            t,
            t,
            metadata={"parser_lane": "local_observation_question"},
        )

    mixed_detail_question = (
        segmented_turn.get("adjudication_question_text")
        if isinstance(segmented_turn, dict)
        else None
    )
    mixed_investigation = _recover_mixed_scene_object_investigation(
        t,
        scene,
        detail_question_text=mixed_detail_question if isinstance(mixed_detail_question, str) else None,
    )
    if mixed_investigation is not None:
        return mixed_investigation

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

    # ---- 0b. Passive wait / observe interruption (before travel; no quoted speech) ----
    if _raw_text_eligible_for_passive_interruption_wait_parse(t) and _declared_matches_passive_interruption_wait(t):
        return _build_action(
            "observe",
            t,
            t,
            metadata={
                "passive_interruption_wait": True,
                "parser_lane": "passive_interruption_wait",
            },
        )

    # ---- 0c. Human-adjacent non-social (listen / approach+listen / group watch) → observe ----
    from game.human_adjacent_focus import classify_human_adjacent_intent_family, is_physical_clue_inspection_intent

    if not is_physical_clue_inspection_intent(t):
        ha_fam = classify_human_adjacent_intent_family(t)
        if ha_fam != "none":
            return _build_action(
                "observe",
                t,
                t,
                metadata={
                    "parser_lane": "human_adjacent_observe",
                    "human_adjacent_intent_family": ha_fam,
                },
            )

    # ---- 0d. Embedded named-place movement ("… entering the Stone Boar") before generic travel/follow ----
    from game.scene_destination_binding import try_embedded_named_place_scene_action

    emb = try_embedded_named_place_scene_action(t, scene)
    if emb is not None:
        return emb

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
            metadata = None
            if isinstance(mixed_detail_question, str) and mixed_detail_question.strip() and target:
                grounding = _ground_scene_investigation_target(target, scene)
                if grounding is not None:
                    metadata = {
                        "parser_lane": "mixed_scene_object_investigation",
                        "mixed_turn_detail_question": mixed_detail_question.strip(),
                        "adjudication_or_detail_question_text": mixed_detail_question.strip(),
                        "recovered_action_clause": _clean_clause(t) or t,
                        "scene_grounding_kind": grounding.get("kind"),
                        "scene_grounding_text": grounding.get("text"),
                    }
            return _build_action(
                "investigate",
                t,
                t,
                target_id=matched_id or target,
                action_id=aid,
                metadata=metadata,
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
    # Use word-boundary "follow" so "follows" (third person) does not arm this path; never
    # `_match_exit("follow", …)` on unrelated prose — that can latch onto "Follow the … rumor" exits.
    m_follow = re.search(r"\bfollow\b", low)
    if m_follow and exits:
        tail = low[m_follow.end() :].strip()
        target_id = _match_exit(tail, exits)
        if not target_id and re.match(r"^\s*the\s+", tail):
            target_id = _match_exit(tail[4:].lstrip(), exits)
        if not target_id and re.match(r"^\s*follow\s*[\s\.,;?!]*$", low):
            target_id = _match_exit("follow", exits)
        if target_id:
            return _build_action(
                "scene_transition",
                t,
                t,
                target_scene_id=target_id,
                metadata={"parser_lane": "legacy_follow_exit_match"},
            )
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


_DECLARED_TRAVEL_DEST_STOPWORDS = frozenset(
    {
        "later",
        "now",
        "tomorrow",
        "another day",
        "someday",
    }
)


def _infer_transition_target_from_declared_text(
    prompt: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: set[str],
) -> Optional[str]:
    """Match prompt text to exit labels / scene ids (mirrors exploration inference; avoids import cycle)."""
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    prompt_low = prompt.strip().lower()
    prompt_slug = slugify(prompt_low)
    for ex in exits or []:
        if not isinstance(ex, dict):
            continue
        label = str(ex.get("label") or "").strip()
        target = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not target:
            continue
        label_low = label.lower()
        label_slug = slugify(label_low)
        target_slug = slugify(target)
        if (
            (label_low and label_low in prompt_low)
            or (label_low and prompt_low in label_low)
            or (label_slug and label_slug in prompt_slug)
            or (target_slug and target_slug in prompt_slug)
        ):
            if target in known_scene_ids:
                return target
    return None


def _collect_exit_targets_matching_dest_fragment(
    dest: str, exits: List[Dict[str, Any]]
) -> List[str]:
    """All exit target_scene_ids whose label/slug overlaps *dest* (same loose signals as :func:`_match_exit`)."""
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
    """Single exit target when *dest* matches exactly one exit; fail closed on ambiguity."""
    hits = _collect_exit_targets_matching_dest_fragment(dest, exits)
    uniq = list(dict.fromkeys(hits))
    if len(uniq) == 1:
        return uniq[0]
    return None


def _infer_unique_transition_target_from_declared_text(
    prompt: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: set[str],
) -> Optional[str]:
    """Like :func:`_infer_transition_target_from_declared_text` but requires a unique exit match."""
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    prompt_low = prompt.strip().lower()
    prompt_slug = slugify(prompt_low)
    hits: List[str] = []
    for ex in exits or []:
        if not isinstance(ex, dict):
            continue
        label = str(ex.get("label") or "").strip()
        target = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
        if not target:
            continue
        label_low = label.lower()
        label_slug = slugify(label_low)
        target_slug = slugify(target)
        if (
            (label_low and label_low in prompt_low)
            or (label_low and prompt_low in label_low)
            or (label_slug and label_slug in prompt_slug)
            or (target_slug and target_slug in prompt_slug)
        ):
            if target in known_scene_ids:
                hits.append(target)
    uniq = list(dict.fromkeys(hits))
    if len(uniq) == 1:
        return uniq[0]
    return None


def _unique_known_scene_id_for_dest_phrase(dest: str, known_scene_ids: set[str]) -> Optional[str]:
    """When the affirmed phrase maps to exactly one known scene id (slug / substring); fail closed."""
    d = (dest or "").strip()
    if not d or not known_scene_ids:
        return None
    dest_cf = d.casefold()
    dest_slug = slugify(d)
    if len(dest_slug) < 4:
        return None
    hits: List[str] = []
    for sid in known_scene_ids:
        s = str(sid).strip()
        if not s:
            continue
        s_slug = slugify(s)
        if s.casefold() == dest_cf or s_slug == dest_slug:
            hits.append(s)
            continue
        if len(dest_slug) >= 6 and dest_slug in s_slug:
            hits.append(s)
    uniq = list(dict.fromkeys(hits))
    if len(uniq) == 1:
        return uniq[0]
    return None


def _resolve_declared_travel_target_scene_id(
    dest: str,
    infer_scope: str,
    exits: List[Dict[str, Any]],
    known_scene_ids: set[str],
) -> Optional[str]:
    """Resolve affirmed destination: exits first (strict then unique fuzzy), then unique inference, then phrase→id."""
    tid = _strict_unique_exit_destination(dest, exits)
    if not tid:
        tid = _declared_unique_exit_target_for_dest(dest, exits)
    if not tid:
        tid = _infer_unique_transition_target_from_declared_text(infer_scope, exits, known_scene_ids)
    if not tid:
        tid = _infer_unique_transition_target_from_declared_text(dest, exits, known_scene_ids)
    if not tid:
        tid = _unique_known_scene_id_for_dest_phrase(dest, known_scene_ids)
    return tid


def _declared_travel_local_prefix_before_match(declared: str, match_start: int) -> str:
    """Clause/sentence tail immediately before a travel match (avoids skipping real movement after a prior question)."""
    prefix = declared[:match_start] if match_start > 0 else ""
    if not isinstance(prefix, str) or not prefix.strip():
        return ""
    cut = -1
    for sep in (".", "!", "?", ";", ",", "\n", "\u2014", "\u2013"):  # clause / em dash / en dash
        idx = prefix.rfind(sep)
        if idx > cut:
            cut = idx
    tail = prefix[cut + 1 :].strip() if cut >= 0 else prefix.strip()
    return tail.lstrip(" \t\"'«»").strip()


def _declared_travel_embedded_in_addressing_question(declared: str, match_start: int) -> bool:
    """True when the travel phrase is part of the same addressing/question clause, not a separate declared move."""
    local = _declared_travel_local_prefix_before_match(declared, match_start)
    if not local:
        return False
    low = local.lower()
    return bool(
        re.search(
            r"\b(?:ask|asks|asking|question|questions|questioned|wonder|wonders|wondering|"
            r"inquire|inquires|tell|tells|telling)\s+",
            low,
        )
    )


_PURPOSE_INFINITIVE_TAIL = re.compile(
    r"^(?P<core>.+?)\s+to\s+(?:look|find|search|seek|check|speak|talk|meet|see|ask|buy|sell|grab|scout)\b",
    re.IGNORECASE,
)


def _trim_declared_travel_dest_purpose_tail(s: str) -> str:
    """Drop bounded trailing purpose clauses: '… to look for scrap' → '…'."""
    t = (s or "").strip()
    if not t:
        return t
    m = _PURPOSE_INFINITIVE_TAIL.match(t)
    if m:
        return (m.group("core") or "").strip()
    return t


def _normalize_declared_travel_dest_fragment(raw: str) -> Optional[str]:
    s = (raw or "").strip()
    s = re.sub(r'^["\'\s]+|["\'\s]+$', "", s).strip()
    s = re.sub(r"\s+", " ", s).strip(" \t.-")
    s = _trim_declared_travel_dest_purpose_tail(s)
    if not s or len(s) < 3:
        return None
    core = s.casefold().strip()
    if core in _DECLARED_TRAVEL_DEST_STOPWORDS:
        return None
    return s


# (regex, debug tag) — ordered; first match wins.
_DECLARED_TRAVEL_WITH_DEST_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(p, re.IGNORECASE | re.DOTALL), tag)
    for p, tag in (
        (
            r"\bleaves?\s+.+?\s+for\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "leave_X_for_Y",
        ),
        (
            r"\bleaving\s+.+?\s+for\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "leaving_X_for_Y",
        ),
        (
            r"\bleaves?\s+for\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "leave_for_Y",
        ),
        (
            r"\bleaving\s+for\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "leaving_for_Y",
        ),
        (
            r"\b(?:goes|going)\s+to\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "going_to_Y",
        ),
        (
            r"\b(?:head|heads|heading)\s+(?:off\s+)?to\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "head_to_Y",
        ),
        (
            r"\b(?:head|heads|heading)\s+for\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "head_for_Y",
        ),
        (
            r"\b(?:travel|travels|traveling|travelling)\s+(?:to|towards?)\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "travel_to_Y",
        ),
        (
            r"\b(?:journey|journeys|journeying)\s+to\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "journey_to_Y",
        ),
        (
            r"\b(?:move|moves|moving)\s+to\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "move_to_Y",
        ),
        (
            r"\b(?:walk|walks|walking|run|runs|running)\s+(?:off\s+)?to\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "walk_run_to_Y",
        ),
        (
            r"\benter(?:s|ing)?\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "enter_Y",
        ),
        (
            r"\b(?:depart|departs|departing)\s+for\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "depart_for_Y",
        ),
        (
            r"\b(?:return|returns|returning)\s+to\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "return_to_Y",
        ),
        (
            r"\bset\s+out\s+for\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "set_out_for_Y",
        ),
        (
            r"\b(?:ride|rides|riding|march|marches|marching)\s+to\s+(?:the\s+)?(.+?)(?:\s*[.,;?!]|$)",
            "ride_march_to_Y",
        ),
    )
)


def _declared_travel_match_prefix(declared: str, m: re.Match) -> str:
    i = m.start()
    return declared[max(0, i - 220) : i].lower()


def _declared_travel_match_starts_with_travel_verb(m: re.Match) -> bool:
    head = (m.group(0) or "").lower().lstrip()
    return bool(
        re.match(
            r"(?:goes|going|go)\s+|(?:travel|travels|traveling|travelling)\s+|"
            r"(?:head|heads|heading)\s+|(?:leave|leaves|leaving)\b|"
            r"(?:move|moves|moving)\s+|(?:walk|walks|walking|run|runs|running)\s+|"
            r"(?:journey|journeys|journeying)\s+|(?:return|returns|returning)\s+|"
            r"(?:depart|departs|departing)\s+|(?:ride|rides|riding|march|marches|marching)\s+",
            head,
        )
    )


def _declared_travel_negation_blocks_match(declared: str, m: re.Match) -> bool:
    """True when bounded phrasing marks this travel phrase as refused, postponed, or contrastive."""
    pre = _declared_travel_match_prefix(declared, m)
    g0 = (m.group(0) or "").lower()
    g0_head = g0.lstrip()

    # Contrastive: the matched phrase is the rejected branch (instead of … to …).
    if pre.rstrip().endswith("instead of") and _declared_travel_match_starts_with_travel_verb(m):
        return True

    # Decides / rules out travel to this destination.
    if re.search(r"\bdecides?\s+against\s*$", pre) and _declared_travel_match_starts_with_travel_verb(m):
        return True
    if re.search(r"\bagainst\s*$", pre) and g0_head.startswith(
        ("traveling ", "travelling ", "going ")
    ):
        return True

    # "not going to" / "not traveling to" / copula + not
    if re.search(r"\bnot\s*$", pre) and g0_head.startswith(("going ", "traveling ", "travelling ")):
        return True
    if re.search(r"\b(?:is|are|was|were)\s+not\s*$", pre) and g0_head.startswith(
        ("going ", "traveling ", "travelling ")
    ):
        return True

    # do/does/did not go to …
    if re.search(r"\b(?:do|does|did)\s+not\s+go\s+to\s*$", pre):
        return True

    # won't / refuse / choose not
    if re.search(r"\b(?:won't|wont)\s+go\s+to\s*$", pre):
        return True
    if re.search(r"\brefuses?\s+to\s+go\s+to\s*$", pre):
        return True
    if re.search(r"\bchooses?\s+not\s+to\s+go\s+to\s*$", pre):
        return True

    # Postponement scoped to this destination (e.g. "against … to … for now").
    if m.lastindex and m.end(1) <= len(declared):
        post = declared[m.end(1) : min(len(declared), m.end(1) + 80)].lower()
        if re.search(r"\bfor\s+now\b", post):
            if re.search(r"\bdecides?\s+against\s*$", pre) and _declared_travel_match_starts_with_travel_verb(m):
                return True
            if re.search(r"\bnot\s*$", pre) and g0_head.startswith(("going ", "traveling ", "travelling ")):
                return True
            if re.search(r"\b(?:is|are|was|were)\s+not\s*$", pre) and g0_head.startswith(
                ("going ", "traveling ", "travelling ")
            ):
                return True
            if re.search(r"\b(?:do|does|did)\s+not\s+go\s+to\s*$", pre):
                return True

    return False


def _first_declared_travel_pattern_match(
    declared: str, pos: int
) -> Tuple[Optional[re.Match], Optional[str]]:
    """Mirror legacy behavior: first pattern in tuple that matches from *pos*, not embedded in a question."""
    for pat, tag in _DECLARED_TRAVEL_WITH_DEST_PATTERNS:
        m = pat.search(declared, pos)
        if not m:
            continue
        if _declared_travel_embedded_in_addressing_question(declared, m.start()):
            continue
        return m, tag
    return None, None


def maybe_build_declared_travel_action(
    segmented_turn: Optional[Dict[str, Any]],
    *,
    scene: Dict[str, Any],
    session: Optional[Dict[str, Any]],
    world: Optional[Dict[str, Any]],
    known_scene_ids: set[str],
) -> Optional[Dict[str, Any]]:
    """If *declared_action_text* is explicit travel, return scene_transition/travel; else None.

    Used to override social-only classification on mixed dialogue + movement turns.
    Deterministic; inspect via ``metadata.declared_travel_*``.
    """
    if not isinstance(scene, dict):
        return None
    declared = None
    if isinstance(segmented_turn, dict):
        dt = segmented_turn.get("declared_action_text")
        if isinstance(dt, str) and dt.strip():
            declared = dt.strip()
    if not declared:
        return None

    from game.scene_destination_binding import extract_last_explicit_named_place

    low_decl = declared.lower()
    if re.match(r"^\s*(?:what|where|why|how|who|which|when)\b", low_decl):
        return None
    if low_decl.endswith("?") and any(
        low_decl.startswith(p)
        for p in ("what ", "where ", "why ", "how ", "who ", "which ", "when ")
    ):
        return None

    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    scene_id = str(scene.get("id") or "").strip()

    cursor = 0
    max_passes = 8
    for _ in range(max_passes):
        m, matched_tag = _first_declared_travel_pattern_match(declared, cursor)
        if not m or not matched_tag:
            return None
        dest_raw = m.group(1)
        if not dest_raw:
            return None

        if _declared_travel_negation_blocks_match(declared, m):
            nxt = m.end()
            if nxt <= cursor:
                cursor = cursor + 1
            else:
                cursor = nxt
            continue

        dest = _normalize_declared_travel_dest_fragment(dest_raw)
        if not dest:
            return None

        base_meta: Dict[str, Any] = {
            "declared_travel_override": True,
            "declared_travel_pattern": matched_tag,
            "declared_travel_dest_hint": dest,
        }

        infer_scope = declared[m.start() :]
        tid = _resolve_declared_travel_target_scene_id(dest, infer_scope, exits, known_scene_ids)

        actionable: List[Dict[str, Any]] = []
        if isinstance(session, dict) and scene_id:
            actionable = _actionable_pending_with_registry_rows(session, scene_id)

        row: Optional[Dict[str, Any]] = None
        if actionable:
            row = _resolve_qualified_pursuit_target_to_row(dest, scene, session, world, actionable)
        row_scene = _pending_row_resolved_scene_id(row, world) if row else None

        if tid is None and extract_last_explicit_named_place(declared) is not None:
            row = None
            row_scene = None

        # Affirmed exit/scene resolution wins; attach lead metadata only when the lead's destination matches.
        if tid and tid in known_scene_ids:
            if row and row_scene and row_scene == tid:
                act = _build_pursuit_scene_transition_action(declared, row, world=world)
                if act is not None:
                    md = act.setdefault("metadata", {})
                    md.update(base_meta)
                    return act
            return _build_action(
                "scene_transition",
                declared,
                declared,
                target_scene_id=tid,
                metadata=base_meta,
            )

        if row is not None:
            act = _build_pursuit_scene_transition_action(declared, row, world=world)
            if act is not None:
                md = act.setdefault("metadata", {})
                md.update(base_meta)
                return act

        return _build_action("travel", declared, declared, target_scene_id=None, metadata=base_meta)

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

    if re.search(r"\bfollow\b", low):
        return _build_action("interact", text.strip(), text.strip(), metadata={"intent": "follow_target"})
    if "leave" in low or "exit" in low:
        return _build_action("travel", text.strip(), text.strip(), metadata={"intent": "leave_area"})
    if "search" in low or "look" in low or "investigate" in low:
        return _build_action("investigate", text.strip(), text.strip())
    if "talk" in low or "ask" in low:
        return _build_action("interact", text.strip(), text.strip(), metadata={"intent": "conversation"})

    return None
