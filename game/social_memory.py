"""Social discussion-memory and topic-anchor helpers.

This module isolates persistent social memory bookkeeping from interaction resolution.
`game.social` re-exports these functions as a compatibility surface.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from game.leads import get_lead
from game.storage import get_scene_runtime

_SOCIAL_DISCUSSION_DISCLOSURE_LEVELS: tuple[str, ...] = ("hinted", "explicit")
_SOCIAL_DISCUSSION_RANK = {"hinted": 0, "explicit": 1}
_SOCIAL_DISCUSSION_BUCKET_KEY = "npc_lead_discussions"
_SOCIAL_LEAD_ACK_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "have",
        "your",
        "they",
        "their",
        "about",
        "lead",
        "scene",
        "clue",
        "hint",
        "road",
    }
)


def _social_turn_counter(session: Dict[str, Any]) -> int | None:
    if not isinstance(session, dict):
        return None
    tc = session.get("turn_counter")
    if tc is None:
        return None
    try:
        return int(tc)
    except (TypeError, ValueError):
        return None


def _get_scene_social_discussion_bucket(
    session: Dict[str, Any],
    scene_id: str,
    *,
    create: bool = False,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    sid = str(scene_id or "").strip()
    if not isinstance(session, dict) or not sid:
        return {}
    rt = get_scene_runtime(session, sid)
    raw = rt.get(_SOCIAL_DISCUSSION_BUCKET_KEY)
    if isinstance(raw, dict):
        return raw
    if not create:
        return {}
    rt[_SOCIAL_DISCUSSION_BUCKET_KEY] = {}
    return rt[_SOCIAL_DISCUSSION_BUCKET_KEY]


def _normalize_disclosure_level(value: Any) -> str | None:
    norm = str(value or "").strip().lower()
    if norm in _SOCIAL_DISCUSSION_DISCLOSURE_LEVELS:
        return norm
    return None


def _merge_disclosure_level(old: Any, new: Any) -> str:
    old_norm = _normalize_disclosure_level(old) or "hinted"
    new_norm = _normalize_disclosure_level(new) or "hinted"
    if _SOCIAL_DISCUSSION_RANK.get(new_norm, 0) >= _SOCIAL_DISCUSSION_RANK.get(old_norm, 0):
        return new_norm
    return old_norm


def get_npc_lead_discussion(
    session: Dict[str, Any],
    scene_id: str,
    npc_id: str,
    lead_id: str,
) -> Dict[str, Any] | None:
    nid = str(npc_id or "").strip()
    lid = str(lead_id or "").strip()
    if not nid or not lid:
        return None
    bucket = _get_scene_social_discussion_bucket(session, scene_id, create=False)
    npc_bucket = bucket.get(nid) if isinstance(bucket.get(nid), dict) else {}
    rec = npc_bucket.get(lid)
    return rec if isinstance(rec, dict) else None


def record_npc_lead_discussion(
    session: Dict[str, Any],
    scene_id: str,
    npc_id: str,
    lead_id: str,
    *,
    disclosure_level: str,
    turn_counter: int | None = None,
) -> Dict[str, Any] | None:
    sid = str(scene_id or "").strip()
    nid = str(npc_id or "").strip()
    lid = str(lead_id or "").strip()
    if not sid or not nid or not lid:
        return None
    bucket = _get_scene_social_discussion_bucket(session, sid, create=True)
    npc_bucket = bucket.get(nid)
    if not isinstance(npc_bucket, dict):
        npc_bucket = {}
        bucket[nid] = npc_bucket
    tc = turn_counter if isinstance(turn_counter, int) else _social_turn_counter(session)
    rec = npc_bucket.get(lid)
    if not isinstance(rec, dict):
        rec = {
            "npc_id": nid,
            "lead_id": lid,
            "first_discussed_turn": tc,
            "last_discussed_turn": tc,
            "disclosure_level": _merge_disclosure_level(None, disclosure_level),
            "player_acknowledged": False,
            "player_acknowledged_turn": None,
            "mention_count": 1,
            "last_scene_id": sid,
        }
        npc_bucket[lid] = rec
        return rec

    rec["npc_id"] = nid
    rec["lead_id"] = lid
    rec["disclosure_level"] = _merge_disclosure_level(rec.get("disclosure_level"), disclosure_level)
    rec["mention_count"] = int(rec.get("mention_count") or 0) + 1
    prev_last = rec.get("last_discussed_turn")
    if tc is not None:
        if isinstance(prev_last, int):
            rec["last_discussed_turn"] = max(prev_last, tc)
        else:
            rec["last_discussed_turn"] = tc
    rec["last_scene_id"] = sid
    if rec.get("first_discussed_turn") is None and tc is not None:
        rec["first_discussed_turn"] = tc
    return rec


def mark_player_acknowledged_npc_lead(
    session: Dict[str, Any],
    scene_id: str,
    npc_id: str,
    lead_id: str,
    *,
    turn_counter: int | None = None,
) -> Dict[str, Any] | None:
    rec = get_npc_lead_discussion(session, scene_id, npc_id, lead_id)
    if not isinstance(rec, dict):
        return None
    rec["player_acknowledged"] = True
    if rec.get("player_acknowledged_turn") is None:
        tc = turn_counter if isinstance(turn_counter, int) else _social_turn_counter(session)
        rec["player_acknowledged_turn"] = tc
    return rec


def list_recent_npc_lead_discussions(
    session: Dict[str, Any],
    scene_id: str,
    *,
    npc_id: str | None = None,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    sid = str(scene_id or "").strip()
    if not sid:
        return []
    bucket = _get_scene_social_discussion_bucket(session, sid, create=False)
    rows: List[Dict[str, Any]] = []
    filter_npc = str(npc_id or "").strip() or None
    for nid, leads in bucket.items():
        if filter_npc and str(nid) != filter_npc:
            continue
        if not isinstance(leads, dict):
            continue
        for lid, rec in leads.items():
            if not isinstance(rec, dict):
                continue
            if str(rec.get("npc_id") or "").strip() != str(nid):
                continue
            if str(rec.get("lead_id") or "").strip() != str(lid):
                continue
            rows.append(dict(rec))
    rows.sort(
        key=lambda r: (
            int(r.get("last_discussed_turn") or -1),
            int(r.get("mention_count") or 0),
            str(r.get("npc_id") or ""),
            str(r.get("lead_id") or ""),
        ),
        reverse=True,
    )
    if limit <= 0:
        return []
    return rows[: int(limit)]


def _lead_discussion_token_candidates(session: Dict[str, Any], lead_id: str) -> set[str]:
    lid = str(lead_id or "").strip().lower()
    if not lid:
        return set()
    title = ""
    row = get_lead(session, lid)
    if isinstance(row, dict):
        title = str(row.get("title") or "").strip()
    tokens = set(re.findall(r"[a-z0-9]{3,}", f"{lid} {title}".lower()))
    return {
        t
        for t in tokens
        if t and t not in _SOCIAL_LEAD_ACK_STOPWORDS and not t.isdigit() and not (len(t) <= 3 and t.endswith("ing"))
    }


def _player_text_mentions_lead_token(
    session: Dict[str, Any],
    lead_id: str,
    player_text: str | None,
) -> bool:
    text = str(player_text or "").strip().lower()
    if not text:
        return False
    words = set(re.findall(r"[a-z0-9]{3,}", text))
    if not words:
        return False
    tokens = _lead_discussion_token_candidates(session, lead_id)
    return bool(tokens and (tokens & words))


def _is_followup_ack_question(
    *,
    player_text: str | None,
    current_turn: int | None,
    previous_record: Dict[str, Any] | None,
) -> bool:
    if not isinstance(previous_record, dict):
        return False
    prev_turn = previous_record.get("last_discussed_turn")
    if not isinstance(prev_turn, int) or not isinstance(current_turn, int):
        return False
    if current_turn - prev_turn != 1:
        return False
    text = str(player_text or "").strip().lower()
    if not text:
        return False
    if "?" not in text:
        if not re.search(r"\b(what|where|when|why|how|who|which|and|then)\b", text):
            return False
    return True


def _collect_social_discussion_implicated_leads(
    resolution: Dict[str, Any],
) -> List[Tuple[str, str]]:
    if not isinstance(resolution, dict):
        return []
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    lead_landing = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}

    ordered: List[str] = []

    def _push(raw: Any) -> None:
        s = str(raw or "").strip()
        if s and s not in ordered:
            ordered.append(s)

    explicit_ids: set[str] = set()

    top_clue = str(resolution.get("clue_id") or "").strip()
    topic_clue = str(topic.get("clue_id") or "").strip()
    _push(top_clue)
    _push(topic_clue)

    for key in (
        "revealed_lead_ids",
        "already_known_lead_ids",
        "actionable_lead_ids",
        "extracted_lead_ids",
        "authoritative_created_ids",
        "authoritative_updated_ids",
        "authoritative_unchanged_ids",
        "authoritative_promoted_ids",
    ):
        vals = lead_landing.get(key)
        if not isinstance(vals, list):
            continue
        for raw in vals:
            _push(raw)
            if key != "already_known_lead_ids":
                explicit_ids.add(str(raw or "").strip())

    if any(
        str(topic.get(k) or "").strip()
        for k in ("leads_to_scene", "leads_to_npc", "leads_to_rumor")
    ):
        if topic_clue:
            explicit_ids.add(topic_clue)
        if top_clue:
            explicit_ids.add(top_clue)

    out: List[Tuple[str, str]] = []
    for lid in ordered:
        lvl = "explicit" if lid in explicit_ids else "hinted"
        out.append((lid, lvl))
    return out


def apply_social_lead_discussion_tracking(
    *,
    session: Dict[str, Any],
    scene_id: str,
    resolution: Dict[str, Any],
    player_text: str | None = None,
) -> List[Dict[str, Any]]:
    if not isinstance(session, dict) or not isinstance(resolution, dict):
        return []
    sid = str(scene_id or "").strip()
    if not sid:
        return []
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else None
    if not isinstance(social, dict):
        return []
    if social.get("target_resolved") is not True or social.get("offscene_target") is True:
        return []
    npc_id = str(social.get("grounded_speaker_id") or social.get("npc_id") or "").strip()
    if not npc_id:
        return []

    implicated = _collect_social_discussion_implicated_leads(resolution)
    # Empty implicated set: no new discussion writes (e.g. mention_count); same-NPC continuity can still come from existing rows in prompt export.
    if not implicated:
        return []

    tc = _social_turn_counter(session)
    updates: List[Dict[str, Any]] = []
    for lead_id, disclosure_level in implicated:
        previous = get_npc_lead_discussion(session, sid, npc_id, lead_id)
        previous_snap = dict(previous) if isinstance(previous, dict) else None
        rec = record_npc_lead_discussion(
            session,
            sid,
            npc_id,
            lead_id,
            disclosure_level=disclosure_level,
            turn_counter=tc,
        )
        if not isinstance(rec, dict):
            continue
        acknowledged = False
        if isinstance(previous_snap, dict):
            if _player_text_mentions_lead_token(session, lead_id, player_text) or _is_followup_ack_question(
                player_text=player_text,
                current_turn=tc,
                previous_record=previous_snap,
            ):
                ack = mark_player_acknowledged_npc_lead(
                    session,
                    sid,
                    npc_id,
                    lead_id,
                    turn_counter=tc,
                )
                acknowledged = bool(isinstance(ack, dict) and ack.get("player_acknowledged") is True)
        updates.append(
            {
                "npc_id": npc_id,
                "lead_id": lead_id,
                "disclosure_level": str(rec.get("disclosure_level") or "hinted"),
                "player_acknowledged": bool(rec.get("player_acknowledged")),
                "mention_count": int(rec.get("mention_count") or 0),
                "acknowledged_updated": acknowledged,
            }
        )
    if updates:
        social["lead_discussion_updates"] = updates
    return updates


_THREAD_MATCH_STOPWORDS = frozenset(
    {
        "what",
        "about",
        "does",
        "this",
        "that",
        "have",
        "been",
        "with",
        "from",
        "your",
        "here",
        "there",
        "when",
        "where",
        "which",
        "would",
        "could",
        "should",
        "them",
        "they",
        "their",
        "those",
        "these",
        "who",
        "whom",
        "whose",
        "into",
        "onto",
        "upon",
        "some",
        "many",
        "much",
        "very",
        "just",
        "only",
        "even",
        "still",
        "also",
        "then",
        "than",
        "such",
    }
)


def _player_question_covers_stored_thread(player_text: str, stored: str) -> bool:
    """Avoid surfacing unrelated topic_pressure answers on a fresh 'who/what/where' question."""
    pl = str(player_text or "").strip().lower()
    st = str(stored or "").strip().lower()
    if not pl or not st:
        return False
    if re.search(
        r"\b(he|she|him|her|referring|you mean|the one|that guy|that woman|that man)\b",
        pl,
    ):
        return True
    toks = [t for t in re.findall(r"[a-z]{4,}", pl) if t not in _THREAD_MATCH_STOPWORDS]
    return any(t in st for t in toks[:18])


_EXPLICIT_TOPIC_ANCHOR_DETECT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bno\b[,.]?\s+i\s+meant\b", re.IGNORECASE),
    re.compile(r"\bnot\s+what\s+i\s+(?:asked|meant)\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m|\s+am)\s+asking\s+about\b", re.IGNORECASE),
    re.compile(r"\blet\s+me\s+clarify\b", re.IGNORECASE),
)


def explicit_player_topic_anchor_state(player_text: str) -> Dict[str, Any]:
    """Detect explicit player topic correction/clarification (lightweight; prompt + topic-pressure guard).

    When *active*, mystery/lead salience and stored topic_pressure answers must not override the
    clarified subject for this turn unless the stored thread clearly matches that subject.
    """
    raw = str(player_text or "").strip()
    low = raw.lower()
    if not low:
        return {"active": False, "focus_fragment": "", "suppress_lead_thread_bias": False}
    active = any(p.search(low) for p in _EXPLICIT_TOPIC_ANCHOR_DETECT_PATTERNS)
    focus = ""
    if active:
        m = re.search(r"\bi(?:'m|\s+am)\s+asking\s+about\s+(.+)$", low, re.IGNORECASE | re.DOTALL)
        if m:
            focus = m.group(1).strip()
        if not focus:
            m2 = re.search(r"\bno\b[,.]?\s+i\s+meant\s+(.+)$", low, re.IGNORECASE | re.DOTALL)
            if m2:
                focus = m2.group(1).strip()
        if not focus:
            m3 = re.search(
                r"\bnot\s+what\s+i\s+(?:asked|meant)\b[,;:]?\s*(.+)$",
                low,
                re.IGNORECASE | re.DOTALL,
            )
            if m3:
                focus = m3.group(1).strip()
        focus = focus.strip().strip("\"'")
    return {
        "active": bool(active),
        "focus_fragment": focus,
        "suppress_lead_thread_bias": bool(active),
    }


_TOPIC_ANCHOR_GENERIC_TOKENS = frozenset(
    {
        "people",
        "person",
        "someone",
        "anyone",
        "everyone",
        "something",
        "anything",
        "nothing",
        "heard",
        "hearing",
        "saying",
        "talk",
        "talking",
        "tell",
        "told",
        "ask",
        "asking",
        "about",
        "around",
        "really",
        "actually",
        "still",
        "mean",
        "meant",
    }
)


def _topic_anchor_focus_tokens(focus: str) -> List[str]:
    low = str(focus or "").strip().lower()
    if not low:
        return []
    return [
        t
        for t in re.findall(r"[a-z]{4,}", low)
        if t not in _THREAD_MATCH_STOPWORDS and t not in _TOPIC_ANCHOR_GENERIC_TOKENS
    ][:18]


def _topic_anchor_skips_stored_fact(player_text: str, stored: str) -> bool:
    """True when an explicit anchor is active and the stored fact thread does not match the anchor focus."""
    st = explicit_player_topic_anchor_state(player_text)
    if not st.get("active"):
        return False
    if not str(stored or "").strip():
        return False
    focus = str(st.get("focus_fragment") or "").strip()
    if not focus:
        focus = " ".join(str(player_text or "").strip().lower().split())
    ftoks = _topic_anchor_focus_tokens(focus)
    if not ftoks:
        return True
    low_stored = str(stored or "").strip().lower()
    if any(t in low_stored for t in ftoks):
        return False
    return True
