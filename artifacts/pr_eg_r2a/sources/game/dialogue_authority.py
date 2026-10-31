"""Dialogue authority for ordinary NPC answers.

Separates what the world has established, what an NPC may say, and what
would become a new consequential fact. NPC speech recorded here is not
canonical world truth.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

COMMITMENT_KEY = "dialogue_commitments"
MAX_COMMITMENTS = 24
MAX_PER_NPC = 8

_STOP = frozenset(
    {
        "ask", "asks", "asking", "tell", "tells", "about", "whether", "what",
        "when", "where", "who", "whom", "whose", "why", "how", "does", "did",
        "have", "has", "with", "from", "that", "this", "them", "they", "your",
        "you", "her", "him", "his", "hers", "she", "the", "and", "for", "are",
        "was", "were", "been", "being", "into", "onto", "over", "then", "just",
        "please", "could", "would", "should", "there", "their", "anyone",
        "someone", "something", "anything", "sergeant", "corporal", "captain",
        "prefer", "think", "trust", "trusted", "like", "likes", "ever",
        "watched", "watch", "forged", "forger", "patrol", "password",
        "promise", "reward", "rumor", "rumors", "killed", "secretly",
        "troubles", "bothers", "worries",
    }
)

_REQUESTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("hidden", re.compile(
        r"\b(?:passwords?|passcodes?|classified|secretly|secrets?|allegiance|ash\s+cowl)\b",
        re.IGNORECASE,
    )),
    ("promise", re.compile(
        r"\b(?:promise|reward|pay\s+me|owe\s+me|\bquest\b|safe\s+passage)\b",
        re.IGNORECASE,
    )),
    ("mystery", re.compile(
        r"\b(?:who\s+killed|who\s+murdered|missing\s+merchant|unsolved)\b",
        re.IGNORECASE,
    )),
    ("relationship", re.compile(
        r"\b(?:are\s+you\s+and|close\s+to|your\s+relationship|in\s+love|married)\b",
        re.IGNORECASE,
    )),
    ("rumor", re.compile(r"\b(?:rumou?rs?|gossip|heard\s+talk)\b", re.IGNORECASE)),
    ("maker", re.compile(
        r"\b(?:forged|forger|makers?|smith(?:ed)?|who\s+(?:made|built|crafted))\b",
        re.IGNORECASE,
    )),
    ("ownership", re.compile(r"\b(?:who\s+owns|whose|belongs\s+to|owner\s+of)\b", re.IGNORECASE)),
    ("surveillance", re.compile(
        r"\b(?:watched|under\s+watch|keep(?:s|ing)?\s+an\s+eye|patrol(?:led|s|ling)?|who\s+watches)\b",
        re.IGNORECASE,
    )),
    ("personal_state", re.compile(
        r"\b(?:what\s+troubles|what\s+bothers|what\s+worries|what(?:'s| is)\s+wrong|"
        r"how\s+are\s+you|are\s+you\s+(?:worried|afraid|angry|upset|troubled|alright))\b",
        re.IGNORECASE,
    )),
    ("opinion", re.compile(
        r"\b(?:what\s+do\s+you\s+think|how\s+do\s+you\s+feel|your\s+opinion|"
        r"do\s+you\s+prefer|have\s+you\s+ever\s+trusted|do\s+you\s+(?:like|trust|enjoy)|"
        r"whether\s+(?:he|she|they)\s+likes?)\b",
        re.IGNORECASE,
    )),
)

_SUPPORT: dict[str, re.Pattern[str]] = {
    "surveillance": re.compile(
        r"\b(?:watch(?:ed|es|ing)?|patrol|guard(?:ed|s|ing)?|unwatched|keep(?:s|ing)? an eye)\b",
        re.IGNORECASE,
    ),
    "maker": re.compile(r"\b(?:forged|forger|smith|crafted|made by|built by)\b", re.IGNORECASE),
    "ownership": re.compile(r"\b(?:owns|owner|belongs to)\b", re.IGNORECASE),
    "personal_state": re.compile(
        r"\b(?:troubled|worried|afraid|angry|upset|concerned|weary|tired)\b",
        re.IGNORECASE,
    ),
    "opinion": re.compile(r"\b(?:prefers?|thinks?|trusts?|likes?|opinion)\b", re.IGNORECASE),
    "hidden": re.compile(r"\b(?:password|passcode|secret|allegiance)\b", re.IGNORECASE),
    "promise": re.compile(r"\b(?:reward|payment|promise|quest)\b", re.IGNORECASE),
    "relationship": re.compile(r"\b(?:close|friend|married|kin|partner)\b", re.IGNORECASE),
    "rumor": re.compile(r"\b(?:rumou?r|gossip|heard)\b", re.IGNORECASE),
    "mystery": re.compile(r"\b(?:killed|murdered|culprit|missing merchant)\b", re.IGNORECASE),
}

_CONSEQUENTIAL_CLAIM = re.compile(
    r"\b(?:usually a patrol|patrol schedule|secretly (?:serves|works|with)|"
    r"i(?:'ll| will) pay|ten silver|the quest|the password is|we're married|"
    r"i forged|new key|hidden passage)\b",
    re.IGNORECASE,
)
_UNCERTAINTY = re.compile(
    r"\b(?:could(?:n't| not)|cannot|can't|do(?:n't| not) know|not that i(?:'ve| have)|"
    r"haven't heard|have not heard|not mine|won't say|will not say|"
    r"couldn't tell|couldn't answer)\b",
    re.IGNORECASE,
)
_INTERNAL = re.compile(
        r"settled here|speech authority|reply plan|canonical world|not been established|"
    r"information authority|from what is settled|emitted_[0-9a-f]",
    re.IGNORECASE,
)
_HEDGE = re.compile(r"\b(?:sometimes|not sure|i have not seen|haven't seen|as far as)\b", re.IGNORECASE)


def requested_information(player_text: str) -> str:
    text = str(player_text or "")
    for name, pattern in _REQUESTS:
        if pattern.search(text):
            return name
    from game.conversational_continuity import is_incidental_personal

    if is_incidental_personal(text):
        return "opinion"
    return "general"


def subject_phrase(player_text: str, *, speaker_name: str = "") -> str:
    blocked = set(_STOP)
    for word in re.findall(r"[a-z']+", str(speaker_name or "").lower()):
        blocked.add(word)
    tokens = [
        tok for tok in re.findall(r"[a-z']{3,}", str(player_text or "").lower())
        if tok not in blocked
    ]
    if not tokens:
        return "that"
    phrase = " ".join(tokens[:3])
    if f"the {phrase}" in str(player_text or "").lower():
        return f"the {phrase}"
    return phrase


def topic_supports_requested_information(player_text: str, topic_text: str) -> bool:
    """A subject mention is not an answer to a more specific request."""
    kind = requested_information(player_text)
    if kind == "general":
        return True
    pattern = _SUPPORT.get(kind)
    if pattern is None:
        return True
    return bool(pattern.search(str(topic_text or "")))


def is_ordinary_personal_question(player_text: str) -> bool:
    kind = requested_information(player_text)
    return kind in {"personal_state", "opinion"}


def is_consequential_request(player_text: str) -> bool:
    return requested_information(player_text) in {"promise", "mystery", "relationship", "rumor"}


def _posture_for(kind: str, *, topic_text: str, plan_kind: str) -> str:
    if topic_text:
        if _HEDGE.search(topic_text):
            return "partial"
        return "established"
    if plan_kind == "genuine_refusal" or kind == "hidden":
        return "withheld"
    if kind in {"personal_state", "opinion"}:
        return "belief"
    if kind in {"promise", "mystery", "relationship", "rumor", "surveillance", "ownership"}:
        return "unestablished"
    return "unknown"


def _player_line(name: str, posture: str, subject: str) -> str:
    speaker = name.strip() or "They"
    del subject
    if posture == "withheld":
        inner = "I couldn't answer that."
    else:
        inner = "I couldn't tell you."
    return f'{speaker} says, "{inner}"'


def visible_supporting_sentence(scene: Mapping[str, Any] | None, player_text: str) -> str:
    """A public sentence that already supports the requested information."""
    kind = requested_information(player_text)
    pattern = _SUPPORT.get(kind)
    if pattern is None or kind in {"hidden", "promise", "mystery", "relationship", "rumor", "general"}:
        return ""
    try:
        from game.incidental_entity import public_scene_text
    except Exception:
        return ""
    blob = public_scene_text(scene if isinstance(scene, Mapping) else None)
    subject_words = [word for word in subject_phrase(player_text).split() if word not in {"the", "that"}]
    if not subject_words:
        return ""
    for sentence in re.split(r"[.!?]", blob):
        piece = " ".join(sentence.split())
        if not piece or not pattern.search(piece):
            continue
        if any(word in piece.lower() for word in subject_words):
            return piece
    return ""


def build_dialogue_authority(
    player_text: str,
    *,
    npc: Mapping[str, Any] | None = None,
    social: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify this turn's speech. Does not mutate the world."""
    person = npc if isinstance(npc, Mapping) else {}
    payload = social if isinstance(social, Mapping) else {}
    name = str(payload.get("npc_name") or person.get("name") or "They")
    role = str(person.get("role") or person.get("occupation") or "")
    disposition = str(person.get("disposition") or person.get("attitude") or "")
    topic = payload.get("topic_revealed") if isinstance(payload.get("topic_revealed"), Mapping) else {}
    topic_text = str(topic.get("text") or topic.get("clue_text") or "").strip()
    kind = requested_information(player_text)
    plan = str(payload.get("reply_plan_kind") or "")
    if topic_text and plan == "authoritative_answer_available":
        pass
    elif topic_text and topic_supports_requested_information(player_text, topic_text):
        plan = plan or "authoritative_answer_available"
    elif plan == "authoritative_answer_available" and not topic_text:
        plan = "genuine_uncertainty"
    posture = _posture_for(kind, topic_text=topic_text, plan_kind=plan)
    incidental = bool(payload.get("incidental_subjective_allowed")) or (
        not topic_text and kind in {"personal_state", "opinion"} and plan != "genuine_refusal"
    )
    determined = bool(
        not topic_text
        and not incidental
        and kind in {
            "surveillance",
            "maker",
            "ownership",
            "hidden",
            "promise",
            "mystery",
            "relationship",
            "rumor",
        }
        and posture in {"unknown", "unestablished", "withheld", "partial"}
    )
    subject = subject_phrase(player_text, speaker_name=name)
    npc_id = str(payload.get("npc_id") or person.get("id") or "")
    from game.conversational_continuity import find_reusable_commitment, supplied_clarification

    quoted = supplied_clarification(player_text, session, npc_id, name)
    reused = "" if quoted else find_reusable_commitment(session, npc_id, player_text)
    line = ""
    if quoted or reused:
        incidental = False
        determined = True
        line = quoted or reused
    prior = active_commitments(session, npc_id=npc_id, subject=subject)
    if not prior and subject == "that":
        prior = active_commitments(session, npc_id=npc_id)[-1:]
    if determined and not line:
        if prior:
            line = str(prior[-1].get("text") or "")
        if not line:
            line = _player_line(name, posture, subject)
    prohibited = [
        "consequential_world_fact",
        "hidden_disclosure",
        "mechanical_change",
        "new_obligation",
    ]
    if not incidental:
        prohibited.append("invented_answer")
    return {
        "requested_information": kind,
        "subject": subject,
        "knowledge_posture": posture,
        "answer_relation": (
            "sufficient" if posture == "established"
            else "partial" if posture == "partial"
            else "none"
        ),
        "improvisation_permitted": incidental,
        "improvisation_scope": "incidental_speech" if incidental else "none",
        "narration_determined": determined,
        "player_line": line,
        "canonical": False,
        "npc_id": npc_id,
        "npc_name": name,
        "npc_role": role,
        "npc_disposition": disposition,
        "prohibited_claims": prohibited,
        "prior_commitments": [
            {"kind": row.get("kind"), "text": row.get("text"), "canonical": False}
            for row in prior[-3:]
        ],
        "reconciled_plan": plan if plan != str(payload.get("reply_plan_kind") or "") else "",
        "reuse_prior_speech": bool(quoted or reused),
    }


def attach_dialogue_authority(
    social: dict[str, Any],
    player_text: str,
    npc: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Write the authority record onto the social payload and reconcile a contradiction."""
    if not isinstance(social, dict):
        return {}
    record = build_dialogue_authority(player_text, npc=npc, social=social, session=session, scene=scene)
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), Mapping) else None
    if (
        str(social.get("reply_plan_kind") or "") == "authoritative_answer_available"
        and not topic
    ):
        social["reply_plan_kind"] = "genuine_uncertainty"
        social["npc_speech_authority"] = "none"
        social["objective_world_fact_authority"] = "none"
        social["reply_kind"] = "unknown"
        social["incidental_subjective_allowed"] = False
        record["reconciled_plan"] = "authoritative_without_answer"
        record = build_dialogue_authority(player_text, npc=npc, social=social, session=session, scene=scene)
        record["reconciled_plan"] = "authoritative_without_answer"
    if record["improvisation_permitted"] and str(social.get("reply_plan_kind") or "") not in {
        "harmless_subjective_response_permitted",
        "authoritative_answer_available",
    }:
        social["reply_plan_kind"] = "harmless_subjective_response_permitted"
        social["npc_speech_authority"] = "claim_only"
        social["incidental_subjective_allowed"] = True
        social["objective_world_fact_authority"] = "none"
        social["durable_state_mutation_allowed"] = False
        record["narration_determined"] = False
        record["player_line"] = ""
        record["reuse_prior_speech"] = False
    if record.get("reuse_prior_speech"):
        social["incidental_subjective_allowed"] = False
        social["npc_speech_authority"] = "none"
        social["objective_world_fact_authority"] = "none"
        social["durable_state_mutation_allowed"] = False
    social["dialogue_authority"] = record
    return record


def authority_codes(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Prompt-safe codes. No player-facing sentence."""
    src = record if isinstance(record, Mapping) else {}
    return {
        "requested_information": str(src.get("requested_information") or "general"),
        "knowledge_posture": str(src.get("knowledge_posture") or "unknown"),
        "improvisation_permitted": bool(src.get("improvisation_permitted")),
        "improvisation_scope": str(src.get("improvisation_scope") or "none"),
        "narration_determined": bool(src.get("narration_determined")),
        "canonical": False,
        "prohibited_claims": list(src.get("prohibited_claims") or [])[:8],
    }


def response_class(text: str) -> str:
    raw = str(text or "")
    if _INTERNAL.search(raw):
        return "internal"
    if _CONSEQUENTIAL_CLAIM.search(raw):
        return "consequential"
    if re.search(r"\bcouldn't answer\b|\bnot mine\b|\bwon't say\b", raw, re.IGNORECASE):
        return "refusal"
    if _UNCERTAINTY.search(raw):
        return "uncertainty"
    return "answer"


def dialogue_rejection_reasons(
    text: str,
    *,
    authority: Mapping[str, Any] | None = None,
) -> list[str]:
    """Specific dialogue failures. Empty when the line stays inside the record."""
    raw = str(text or "")
    record = authority if isinstance(authority, Mapping) else {}
    reasons: list[str] = []
    if not record:
        return reasons
    if _INTERNAL.search(raw):
        reasons.append("internal_authority_voice")
    kind = str(record.get("requested_information") or "general")
    if record.get("improvisation_permitted"):
        if _CONSEQUENTIAL_CLAIM.search(raw):
            reasons.append("unauthorized_consequential_claim")
        return reasons
    if _CONSEQUENTIAL_CLAIM.search(raw):
        reasons.append("unauthorized_consequential_claim")
    if kind != "general" and response_class(raw) == "answer":
        pattern = _SUPPORT.get(kind)
        if pattern is not None and not pattern.search(raw):
            reasons.append("answer_not_relevant")
    return reasons


def _bucket(session: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(session, Mapping):
        return []
    ctx = session.get("conversational_context")
    if not isinstance(ctx, Mapping):
        return []
    rows = ctx.get(COMMITMENT_KEY)
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def active_commitments(
    session: Mapping[str, Any] | None,
    *,
    npc_id: str = "",
    subject: str = "",
) -> list[dict[str, Any]]:
    out = []
    for row in _bucket(session):
        if str(row.get("status") or "active") != "active":
            continue
        if npc_id and str(row.get("npc_id") or "") != npc_id:
            continue
        if subject and str(row.get("subject") or "") != subject:
            continue
        out.append(row)
    return out


def remember_dialogue_commitment(
    session: dict[str, Any] | None,
    *,
    social: Mapping[str, Any] | None,
    player_text: str,
    line: str,
    turn: int = 0,
) -> dict[str, Any] | None:
    """Keep a non-canonical conversational commitment. Does not write world facts."""
    if not isinstance(session, dict) or not isinstance(social, Mapping):
        return None
    record = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else None
    if not isinstance(record, Mapping):
        return None
    text = " ".join(str(line or "").split())
    if not text:
        return None
    posture = str(record.get("knowledge_posture") or "")
    if posture == "established":
        return None
    kind = {
        "belief": "opinion",
        "withheld": "refusal",
        "partial": "partial_answer",
    }.get(posture, "admitted_uncertainty")
    npc_id = str(record.get("npc_id") or social.get("npc_id") or "")
    subject = str(record.get("subject") or subject_phrase(player_text))
    ctx = session.setdefault("conversational_context", {})
    if not isinstance(ctx, dict):
        return None
    rows = ctx.get(COMMITMENT_KEY)
    if not isinstance(rows, list):
        rows = []
        ctx[COMMITMENT_KEY] = rows
    for older in rows:
        if not isinstance(older, dict):
            continue
        if str(older.get("npc_id") or "") == npc_id and str(older.get("subject") or "") == subject:
            if str(older.get("text") or "") != text:
                older["status"] = "revised"
    entry = {
        "npc_id": npc_id,
        "kind": kind,
        "subject": subject,
        "text": text[:180],
        "canonical": False,
        "turn": int(turn or 0),
        "status": "active",
        "requested_information": str(record.get("requested_information") or ""),
    }
    for older in rows:
        if (
            isinstance(older, dict)
            and str(older.get("npc_id") or "") == npc_id
            and str(older.get("subject") or "") == subject
            and str(older.get("text") or "") == text
            and str(older.get("status") or "active") == "active"
        ):
            return older
    rows.append(entry)
    per_npc = [row for row in rows if str(row.get("npc_id") or "") == npc_id and row.get("status") == "active"]
    while len(per_npc) > MAX_PER_NPC:
        per_npc[0]["status"] = "expired"
        per_npc = per_npc[1:]
    while sum(1 for row in rows if row.get("status") == "active") > MAX_COMMITMENTS:
        for row in rows:
            if row.get("status") == "active":
                row["status"] = "expired"
                break
    while len(rows) > MAX_COMMITMENTS:
        stale = next((index for index, row in enumerate(rows) if row.get("status") != "active"), None)
        if stale is None:
            del rows[0]
        else:
            del rows[stale]
    return entry
