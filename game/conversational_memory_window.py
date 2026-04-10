"""Prompt-side conversational memory window contract and selection helpers (Objective #15).

Pure, deterministic ranking of prior conversational items by recency plus active-scene
relevance, with stale deprioritization unless an item is explicitly re-grounded.

This module does **not** mutate session state or repair model text — callers wire outputs
into prompt assembly (e.g. :mod:`game.prompt_context`).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

WINDOW_VERSION = "v1"

# Scoring weights (inspectable; tune at call sites via contract flags, not hidden state).
RECENCY_WEIGHT = 100.0
RECENT_TURN_KIND_BONUS = 18.0
ACTIVE_SCENE_ENTITY_HIT_WEIGHT = 26.0
ACTIVE_INTERACTION_TARGET_BONUS = 42.0
ANCHORED_INTERLOCUTOR_BONUS = 36.0
EXPLICIT_REINTRO_ENTITY_BONUS = 52.0
EXPLICIT_REINTRO_TOPIC_BONUS = 28.0
STALE_PENALTY_WEIGHT = 88.0
INACTIVE_PENALTY_WEIGHT = 46.0

# Narrow, deterministic topical-callback markers (avoid broad lexical “importance”).
_TOPIC_CALLBACK_MARKERS: Tuple[str, ...] = (
    "as we discussed",
    "we discussed",
    "you said",
    "you mentioned",
    "you told me",
    "about that",
    "regarding that",
    "regarding the",
    "back to",
    "earlier",
    "remind me",
    "the matter of",
    "pick up where",
    "return to",
)

_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)


def _clean_str(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _norm_id(value: Any) -> str:
    return _clean_str(value).lower()


def _sorted_unique_ids(ids: Sequence[Any]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for raw in ids:
        nid = _norm_id(raw)
        if not nid or nid in seen:
            continue
        seen.add(nid)
        out.append(nid)
    return sorted(out)


def _parse_turn(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _words_lower(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def _phrase_in_text(haystack_lower: str, phrase_lower: str) -> bool:
    if not phrase_lower or not haystack_lower:
        return False
    return phrase_lower in haystack_lower


def _word_set(text: str) -> frozenset[str]:
    return frozenset(_words_lower(text))


# --- Public contract builder -------------------------------------------------


def build_conversational_memory_window_contract(
    *,
    enabled: bool = True,
    recent_turn_window: int = 6,
    soft_memory_limit: int = 12,
    stale_after_turns: int = 18,
    prioritize_recent_turns: bool = True,
    prioritize_active_scene_entities: bool = True,
    deprioritize_stale_inactive_elements: bool = True,
    allow_explicit_reintroduction: bool = True,
    active_scene_entity_ids: Sequence[str] | None = None,
    anchored_interlocutor_id: str = "",
    active_interaction_target_id: str = "",
    explicit_reintroduced_entity_ids: Sequence[str] | None = None,
    explicit_reintroduced_topics: Sequence[str] | None = None,
    selection_debug: Mapping[str, Any] | None = None,
    source_of_activity_anchor: str = "",
    source_of_recentness: str = "",
    source_of_reintroductions: str = "",
) -> Dict[str, Any]:
    """Build the machine-readable policy contract for conversational memory selection."""
    rt = max(0, int(recent_turn_window))
    cap = max(0, int(soft_memory_limit))
    stale = max(0, int(stale_after_turns))

    scene_ids = _sorted_unique_ids(list(active_scene_entity_ids or []))
    re_ent = _sorted_unique_ids(list(explicit_reintroduced_entity_ids or []))
    re_top = sorted(
        {_clean_str(t).lower() for t in (explicit_reintroduced_topics or []) if _clean_str(t)},
    )

    dbg: Dict[str, Any] = {}
    if isinstance(selection_debug, Mapping):
        dbg = {str(k): v for k, v in selection_debug.items()}
    dbg.setdefault("source_of_activity_anchor", _clean_str(source_of_activity_anchor) or "unspecified")
    dbg.setdefault("source_of_recentness", _clean_str(source_of_recentness) or "unspecified")
    dbg.setdefault("source_of_reintroductions", _clean_str(source_of_reintroductions) or "unspecified")

    return {
        "enabled": bool(enabled),
        "window_version": WINDOW_VERSION,
        "prioritize_recent_turns": bool(prioritize_recent_turns),
        "prioritize_active_scene_entities": bool(prioritize_active_scene_entities),
        "deprioritize_stale_inactive_elements": bool(deprioritize_stale_inactive_elements),
        "allow_explicit_reintroduction": bool(allow_explicit_reintroduction),
        "recent_turn_window": rt,
        "soft_memory_limit": cap,
        "stale_after_turns": stale,
        "active_scene_entity_ids": scene_ids,
        "anchored_interlocutor_id": _norm_id(anchored_interlocutor_id),
        "active_interaction_target_id": _norm_id(active_interaction_target_id),
        "explicit_reintroduced_entity_ids": re_ent,
        "explicit_reintroduced_topics": re_top,
        "selection_debug": dbg,
    }


# --- Pure scoring helpers ----------------------------------------------------


def recency_score(
    source_turn: int | None,
    current_turn: int,
    *,
    recent_turn_window: int,
    prioritize_recent_turns: bool = True,
) -> float:
    """Higher score for newer items within ``recent_turn_window``; zero outside the window."""
    if not prioritize_recent_turns:
        return 0.0
    if source_turn is None:
        return 0.0
    ct = max(0, int(current_turn))
    st = int(source_turn)
    age = ct - st
    if age < 0:
        age = 0
    rw = max(0, int(recent_turn_window))
    if rw == 0:
        return float(RECENCY_WEIGHT) if age == 0 else 0.0
    if age > rw:
        return 0.0
    # Deterministic linear ramp: newest turn gets full weight.
    return float(RECENCY_WEIGHT) * float(rw - age + 1) / float(rw + 1)


def active_scene_entity_bonus(
    entity_ids: Sequence[str] | None,
    active_scene_entity_ids: Sequence[str] | None,
    *,
    prioritize_active_scene_entities: bool = True,
) -> float:
    """Bonus proportional to how many candidate entities appear in the active scene roster."""
    if not prioritize_active_scene_entities:
        return 0.0
    act = {_norm_id(x) for x in (active_scene_entity_ids or []) if _norm_id(x)}
    if not act:
        return 0.0
    hits = 0
    for e in entity_ids or []:
        if _norm_id(e) in act:
            hits += 1
    return float(hits * ACTIVE_SCENE_ENTITY_HIT_WEIGHT)


def interaction_anchor_bonuses(
    entity_ids: Sequence[str] | None,
    *,
    active_interaction_target_id: str = "",
    anchored_interlocutor_id: str = "",
) -> Tuple[float, float]:
    """Return (active_target_bonus, anchored_interlocutor_bonus) for entity-tied memory."""
    cand = {_norm_id(x) for x in (entity_ids or []) if _norm_id(x)}
    tgt = _norm_id(active_interaction_target_id)
    anc = _norm_id(anchored_interlocutor_id)
    tb = float(ACTIVE_INTERACTION_TARGET_BONUS) if tgt and tgt in cand else 0.0
    ab = float(ANCHORED_INTERLOCUTOR_BONUS) if anc and anc in cand else 0.0
    return tb, ab


def explicit_reintroduction_bonus(
    entity_ids: Sequence[str] | None,
    topic_tokens: Sequence[str] | None,
    *,
    explicit_reintroduced_entity_ids: Sequence[str] | None,
    explicit_reintroduced_topics: Sequence[str] | None,
    allow_explicit_reintroduction: bool = True,
) -> float:
    """Bonus when candidate entities/topics overlap explicit reintroduction sets."""
    if not allow_explicit_reintroduction:
        return 0.0
    e_ids = {_norm_id(x) for x in (explicit_reintroduced_entity_ids or []) if _norm_id(x)}
    topics = {_clean_str(t).lower() for t in (explicit_reintroduced_topics or []) if _clean_str(t)}
    if not e_ids and not topics:
        return 0.0
    score = 0.0
    for e in entity_ids or []:
        if _norm_id(e) in e_ids:
            score += EXPLICIT_REINTRO_ENTITY_BONUS
    for tt in topic_tokens or []:
        key = _clean_str(tt).lower()
        if key and key in topics:
            score += EXPLICIT_REINTRO_TOPIC_BONUS
    return float(score)


def stale_penalty(
    source_turn: int | None,
    current_turn: int,
    *,
    stale_after_turns: int,
    deprioritize: bool = True,
    exempt: bool = False,
) -> float:
    """Non-negative penalty applied to stale items (subtracted in aggregate scoring)."""
    if not deprioritize or exempt:
        return 0.0
    if source_turn is None:
        return 0.0
    ct = max(0, int(current_turn))
    st = int(source_turn)
    age = max(0, ct - st)
    thresh = max(0, int(stale_after_turns))
    if age <= thresh:
        return 0.0
    return float(STALE_PENALTY_WEIGHT)


def inactive_penalty(
    *,
    has_active_scene_overlap: bool,
    is_recent: bool,
    is_anchor_or_target: bool,
    is_explicit_reintro: bool,
    deprioritize_stale_inactive: bool = True,
) -> float:
    """Penalty for old, inactive-scene items with no anchor/reintroduction grounding."""
    if not deprioritize_stale_inactive:
        return 0.0
    if is_recent or has_active_scene_overlap or is_anchor_or_target or is_explicit_reintro:
        return 0.0
    return float(INACTIVE_PENALTY_WEIGHT)


# --- Explicit reintroduction (narrow, caller-supplied surface forms only) ---


def _extract_explicit_reintroductions(
    player_text: str,
    *,
    entity_alias_map: Mapping[str, Sequence[str]] | None = None,
    topic_anchor_tokens: Sequence[str] | None = None,
    anchored_interlocutor_id: str = "",
    active_interaction_target_id: str = "",
    allow_explicit_reintroduction: bool = True,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Detect explicit reintroductions using **only** caller-provided aliases and anchors.

    No world invention: ``entity_alias_map`` must list surface strings per entity id
    (from interaction continuity, roster labels, social/topic helpers, etc.).
    """
    debug: Dict[str, Any] = {
        "matched_entity_ids": [],
        "matched_topics": [],
        "matched_grounded_ids": [],
        "callback_marker_hit": None,
    }
    if not allow_explicit_reintroduction:
        return [], [], {**debug, "reason": "disabled"}

    text = _clean_str(player_text)
    if not text:
        return [], [], {**debug, "reason": "empty_player_text"}

    lower = text.lower()
    words = _word_set(text)

    matched_entities: set[str] = set()
    alias_map = entity_alias_map if isinstance(entity_alias_map, Mapping) else {}

    for eid, aliases in alias_map.items():
        nid = _norm_id(eid)
        if not nid:
            continue
        if not isinstance(aliases, (list, tuple)):
            continue
        for al in aliases:
            a = _clean_str(al)
            if not a:
                continue
            alow = a.lower()
            if len(alow.split()) > 1:
                if _phrase_in_text(lower, alow):
                    matched_entities.add(nid)
                    break
            else:
                if len(alow) >= 4 and alow in words:
                    matched_entities.add(nid)
                    break
                if len(alow) == 3 and alow in words:
                    matched_entities.add(nid)
                    break

    # Grounded social anchor / target: treat as explicit refocus when their alias appears.
    grounded: List[str] = []
    for gid, label in (
        (_norm_id(anchored_interlocutor_id), "anchored_interlocutor_id"),
        (_norm_id(active_interaction_target_id), "active_interaction_target_id"),
    ):
        if not gid:
            continue
        als = alias_map.get(gid)
        if not isinstance(als, (list, tuple)):
            continue
        for al in als:
            a = _clean_str(al)
            if not a:
                continue
            alow = a.lower()
            ok = _phrase_in_text(lower, alow) if len(alow.split()) > 1 else (len(alow) >= 4 and alow in words)
            if ok:
                matched_entities.add(gid)
                grounded.append(gid)
                debug["matched_grounded_ids"].append({"id": gid, "via": label})
                break

    # Topic anchors: require a callback marker **and** a known anchor token in-window.
    anchors = [
        _clean_str(t).lower()
        for t in (topic_anchor_tokens or [])
        if _clean_str(t)
    ]
    matched_topics: set[str] = set()
    callback_hit: str | None = None
    for marker in _TOPIC_CALLBACK_MARKERS:
        if marker and marker in lower:
            callback_hit = marker
            break
    debug["callback_marker_hit"] = callback_hit

    if callback_hit and anchors:
        window = 140
        idx = lower.find(callback_hit)
        start = max(0, idx - window // 2)
        end = min(len(lower), idx + len(callback_hit) + window // 2)
        chunk = lower[start:end]
        for an in sorted(set(anchors)):
            if an and an in chunk:
                matched_topics.add(an)

    ent_sorted = sorted(matched_entities)
    top_sorted = sorted(matched_topics)
    debug["matched_entity_ids"] = list(ent_sorted)
    debug["matched_topics"] = list(top_sorted)
    return ent_sorted, top_sorted, debug


# --- Candidate normalization / scoring --------------------------------------


def _normalize_memory_candidate(raw: Mapping[str, Any]) -> Dict[str, Any]:
    kind = _clean_str(raw.get("kind")) or "unknown"
    eids = [_norm_id(x) for x in (raw.get("entity_ids") or []) if _norm_id(x)]
    topics = [_clean_str(t).lower() for t in (raw.get("topic_tokens") or []) if _clean_str(t)]
    st = _parse_turn(raw.get("source_turn"))
    text = _clean_str(raw.get("text"))
    return {
        "kind": kind,
        "entity_ids": sorted(set(eids)),
        "topic_tokens": sorted(set(topics)),
        "source_turn": st,
        "text": text,
    }


def _is_candidate_stale(
    source_turn: int | None,
    current_turn: int,
    *,
    stale_after_turns: int,
) -> bool:
    if source_turn is None:
        return False
    ct = max(0, int(current_turn))
    age = max(0, ct - int(source_turn))
    return age > max(0, int(stale_after_turns))


def _stale_exempt(
    norm: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
    current_turn: int,
    has_active_scene_overlap: bool,
    is_explicit_reintro: bool,
) -> bool:
    if not _is_candidate_stale(
        norm.get("source_turn"),
        current_turn,
        stale_after_turns=int(contract.get("stale_after_turns") or 0),
    ):
        return True

    rw = max(0, int(contract.get("recent_turn_window") or 0))
    st = norm.get("source_turn")
    if isinstance(st, int) and rw > 0:
        age = max(0, int(current_turn) - st)
        if age <= rw:
            return True

    if has_active_scene_overlap:
        return True

    tgt = _norm_id(contract.get("active_interaction_target_id"))
    anc = _norm_id(contract.get("anchored_interlocutor_id"))
    cand = {_norm_id(x) for x in (norm.get("entity_ids") or [])}
    if tgt and tgt in cand:
        return True
    if anc and anc in cand:
        return True
    if is_explicit_reintro:
        return True
    return False


def _score_memory_candidate(
    norm: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    current_turn: int,
) -> Tuple[float, Dict[str, float], List[str]]:
    """Return total score, component breakdown, and human-readable reasons."""
    reasons: List[str] = []
    ct = max(0, int(current_turn))
    st = norm.get("source_turn")
    src_turn = st if isinstance(st, int) else None

    pr = bool(contract.get("prioritize_recent_turns", True))
    pse = bool(contract.get("prioritize_active_scene_entities", True))
    dsi = bool(contract.get("deprioritize_stale_inactive_elements", True))
    aer = bool(contract.get("allow_explicit_reintroduction", True))

    rw = max(0, int(contract.get("recent_turn_window") or 0))
    stale_after = max(0, int(contract.get("stale_after_turns") or 0))

    scene_ids = list(contract.get("active_scene_entity_ids") or [])
    r_ent = list(contract.get("explicit_reintroduced_entity_ids") or [])
    r_top = list(contract.get("explicit_reintroduced_topics") or [])

    rs = recency_score(src_turn, ct, recent_turn_window=rw, prioritize_recent_turns=pr)
    if rs > 0:
        reasons.append("recency")

    kind = _clean_str(norm.get("kind"))
    kind_bonus = 0.0
    if pr and kind == "recent_turn":
        kind_bonus = RECENT_TURN_KIND_BONUS
        reasons.append("recent_turn_kind")

    as_bonus = active_scene_entity_bonus(
        list(norm.get("entity_ids") or []),
        scene_ids,
        prioritize_active_scene_entities=pse,
    )
    if as_bonus > 0:
        reasons.append("active_scene_entity")

    tb, ab = interaction_anchor_bonuses(
        list(norm.get("entity_ids") or []),
        active_interaction_target_id=str(contract.get("active_interaction_target_id") or ""),
        anchored_interlocutor_id=str(contract.get("anchored_interlocutor_id") or ""),
    )
    if tb > 0:
        reasons.append("active_interaction_target")
    if ab > 0:
        reasons.append("anchored_interlocutor")

    er_bonus = explicit_reintroduction_bonus(
        list(norm.get("entity_ids") or []),
        list(norm.get("topic_tokens") or []),
        explicit_reintroduced_entity_ids=r_ent,
        explicit_reintroduced_topics=r_top,
        allow_explicit_reintroduction=aer,
    )
    is_explicit_reintro = er_bonus > 0
    if is_explicit_reintro:
        reasons.append("explicit_reintroduction")

    cand_ids = {_norm_id(x) for x in (norm.get("entity_ids") or [])}
    act_scene = {_norm_id(x) for x in scene_ids}
    has_overlap = bool(cand_ids & act_scene) if act_scene else False

    is_recent = False
    if src_turn is not None and rw >= 0:
        is_recent = max(0, ct - int(src_turn)) <= rw

    exempt = _stale_exempt(
        norm,
        contract=contract,
        current_turn=ct,
        has_active_scene_overlap=has_overlap,
        is_explicit_reintro=is_explicit_reintro,
    )
    if _is_candidate_stale(src_turn, ct, stale_after_turns=stale_after) and exempt:
        reasons.append("stale_exempt")

    sp = stale_penalty(
        src_turn,
        ct,
        stale_after_turns=stale_after,
        deprioritize=True,
        exempt=exempt,
    )
    if sp > 0:
        reasons.append("stale_penalty")

    anchor_or_target = (tb > 0) or (ab > 0)
    ip = 0.0
    if src_turn is not None:
        ip = inactive_penalty(
            has_active_scene_overlap=has_overlap,
            is_recent=is_recent,
            is_anchor_or_target=anchor_or_target,
            is_explicit_reintro=is_explicit_reintro,
            deprioritize_stale_inactive=dsi,
        )
    if ip > 0:
        reasons.append("inactive_penalty")

    total = rs + kind_bonus + as_bonus + tb + ab + er_bonus - sp - ip

    breakdown = {
        "recency_score": rs,
        "recent_turn_kind_bonus": kind_bonus,
        "active_scene_entity_bonus": as_bonus,
        "active_interaction_target_bonus": tb,
        "anchored_interlocutor_bonus": ab,
        "explicit_reintroduction_bonus": er_bonus,
        "stale_penalty": sp,
        "inactive_penalty": ip,
        "total": total,
    }
    return float(total), breakdown, reasons


def select_conversational_memory_window(
    candidates: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    *,
    current_turn: int,
) -> List[Dict[str, Any]]:
    """Rank candidates and return up to ``soft_memory_limit`` items with scores and reasons."""
    if not bool(contract.get("enabled", True)):
        return []

    cap = max(0, int(contract.get("soft_memory_limit") or 0))
    if cap < 1:
        return []

    scored: List[Tuple[float, str, int, str, Dict[str, Any]]] = []
    for raw in candidates:
        if not isinstance(raw, Mapping):
            continue
        norm = _normalize_memory_candidate(raw)
        total, _breakdown, why = _score_memory_candidate(
            norm,
            contract,
            current_turn=current_turn,
        )
        tie_text = norm.get("text") or ""
        st_key = norm.get("source_turn")
        st_sort = int(st_key) if isinstance(st_key, int) else -1
        scored.append(
            (
                float(total),
                str(norm.get("kind")),
                st_sort,
                str(tie_text),
                {**norm, "score": total, "why_selected": why},
            )
        )

    scored.sort(key=lambda row: (-row[0], row[1], -row[2], row[3]))

    out: List[Dict[str, Any]] = []
    for total, _k, _st, _tx, item in scored[:cap]:
        # Ensure score matches tuple ordering float
        item["score"] = float(total)
        out.append(item)
    return out
