"""Ground the next turn in the response the player actually heard.

Precedence when more than one source could apply:

1. Explicit player wording, including a newly named addressee.
2. The immediately preceding delivered statement, for a deictic or meaning follow-up.
3. The active conversational topic.
4. The established interlocutor, when that person is still present.
5. An earlier delivered exchange.
6. Authoritative scene presence.

A stale interlocutor does not override an explicit new target. An absent
speaker is not addressed from the new scene. Proposed, generated, and
rejected narration are not history; only the delivered line is.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

DELIVERED_KEY = "delivered_exchanges"
MAX_DELIVERED = 32

_STOP = frozenset(
    {
        "what", "that", "this", "with", "from", "your", "you", "about", "have",
        "been", "does", "did", "tell", "could", "would", "should", "mean",
        "meant", "again", "plainer", "words", "back", "name", "still",
        "earlier", "where", "stand", "they", "them", "then", "than", "into",
        "just", "please", "there", "their", "anyone", "someone", "something",
        "how", "feel", "feels", "feeling", "not", "the", "and", "for", "are",
        "was", "were", "say", "said", "says", "ask", "asks",
    }
)
_UNDO = re.compile(
    r"\b(?:undo|take (?:that|it) back|reverse (?:that|the|it)|did(?:n't| not) happen|rewind)\b",
    re.IGNORECASE,
)
_WORLD = re.compile(
    r"\b(?:attack|follow|move|go|head|walk|travel|inspect|examine|open|take|steal|cast|look at|search)\b",
    re.IGNORECASE,
)
_SCENE = re.compile(
    r"\b(?:describe|where are we|what can i see|what is here|look around|our surroundings)\b",
    re.IGNORECASE,
)
_EXPLICIT_ASK = re.compile(r"\b(?:i|we)\s+(?:ask|tell)\b", re.IGNORECASE)
_RULES = re.compile(r"\b(?:rules?|mechanics?|interface|out of character)\b", re.IGNORECASE)
_GM = re.compile(r"\b(?:gm|game master|dungeon master|\bdm\b)\b", re.IGNORECASE)
_YOU = re.compile(r"\b(?:you|your|you're|youre)\b", re.IGNORECASE)
_THIRD = re.compile(r"\b(?:she|he|her|him|his|hers)\b", re.IGNORECASE)
_MEANING = re.compile(
    r"\b(?:what (?:did|do|does) (?:you|she|he|they) mean|what (?:you|she|he) (?:said|meant)|"
    r"your answer|by that)\b",
    re.IGNORECASE,
)
_CONDITIONAL_ACTION = re.compile(
    r"\?\s*(?:if|provided|unless|otherwise)\b",
    re.IGNORECASE,
)
_HIDDEN = re.compile(r"\b(?:passwords?|passcodes?)\b", re.IGNORECASE)
_RECALL_REQUEST_PREFIX = (
    r"^(?:(?:gm|dm|game master|dungeon master),\s*)?(?:please\s+)?"
    r"(?:(?:can|could|would|will)\s+you\s+)?"
)
_REPEAT = re.compile(
    _RECALL_REQUEST_PREFIX
    + r"(?:repeat(?: exactly)? (?:that|it)(?=[?!.]?$| (?:exactly|in )\b)|"
    r"repeat (?:the|that|your) [^.!?]{0,48}(?:warning|statement|answer|remark|words)(?=[?!.]?$| about\b)|"
    r"say (?:that|it) again|(?:in )?(?:simpler|plainer|plain|other) words|"
    r"(?:put|say|in) (?:that |it )?another way|(?:go )?back to (?:what was said|the name of)|"
    r"tell me (?:the|that|your) [^.!?]{0,48}(?:warning|statement|answer|remark|words) again)\b",
    re.IGNORECASE,
)
_REPEAT_SPEAKER_RE = re.compile(
    _RECALL_REQUEST_PREFIX + r"repeat (?:the\s+)?(?P<speaker>[\w'’ -]+?)[?!.]?$",
    re.IGNORECASE,
)
_CONTEXTUAL_STATEMENT_RE = re.compile(
    r"^(?:what was (?:that(?: last)?(?: statement| remark| answer)?|that name|"
    r"your (?:last )?(?:statement|remark|answer)))[?!.]?$",
    re.IGNORECASE,
)
_RECALLED_SPEECH_RE = re.compile(
    r"^(?:please\s+)?(?:(?:can|could|would|will)\s+you\s+)?"
    r"(?P<request>repeat(?: exactly)?|remind me|tell me again) what "
    r"(?:the\s+)?(?P<who>[\w'’ -]+?)\s+(?:said|told me)\b",
    re.IGNORECASE,
)
_POSSESSIVE_STATEMENT_RE = re.compile(
    r"^(?:what was (?:the\s+)?(?P<who>[\w'’ -]+?)['’]s|what was (?P<pronoun>his|her|their)) "
    r"(?:last )?(?:statement|answer|remark)[?!.]?$",
    re.IGNORECASE,
)
_ABANDON_SPAN_RE = re.compile(
    r"^(?:please\s+)?(?:(?:i|we)\s+)?"
    r"(?:(?:just|carefully|slowly|quietly)\s+)?"
    r"(?:abandon(?:ing)?|forget(?:ting)?(?:\s+about)?|never\s+mind|"
    r"set(?:ting)?\s+aside|stop(?:ping)?\s+(?:discussing|talking\s+about)|"
    r"leave(?:\s+\S+){1,8}\s+aside)\b",
    re.IGNORECASE,
)
_TOPIC_RETURN_CUE_RE = re.compile(
    r"\b(?:return(?:ing|s)?\s+to|go(?:ing)?\s+back\s+to|back\s+to|revisit(?:ing)?)\b",
    re.IGNORECASE,
)
_CLARIFICATION_DELIVERY_RE = re.compile(
    r"nothing has been attempted|not established an executable|which single action",
    re.IGNORECASE,
)
_ANAPHORIC_TOPIC_TOKENS = frozenset({
    "lets", "let's", "want", "discuss", "discussing", "discussed", "question",
    "inquiry", "warning", "conversation", "topic", "statement", "about", "were",
    "revisit", "revisiting", "let",
})
_DISCOURSE_OBJECT_RE = re.compile(
    r"\b(?:question|inquiry|discussion|conversation|topic|statement|remark|subject|warning)\b"
    r"|\bwhat\s+(?:we|i|you|he|she|they|the)\b.{0,64}\b(?:said|say|discussed|discussing|talked|talking|asked)\b"
    r"|\bwhat\s+we\s+were\s+discussing\b"
    r"|\bearlier\s+conversation\b",
    re.IGNORECASE,
)
_ATTRIBUTED_SPEECH_RE = re.compile(
    r"^(?:(?:gm|dm|game master|dungeon master),\s*)?"
    r"what did\s+(?:the\s+|this\s+|that\s+)?(?P<who>[\w'’ -]+?)\s+"
    r"(?:just\s+)?(?:say\b|tell me(?: earlier| before| again)?(?=[?!.]?$))",
    re.IGNORECASE,
)
_PRIOR_WARNING_RE = re.compile(
    r"\bwhat was\s+(?:the\s+)?(?P<who>[a-z][a-z' -]{1,40}?)['’]s\s+warning\b",
    re.IGNORECASE,
)
_NON_SPEAKER_WHO_RE = re.compile(
    r"^(?:you|i|we|it|notice|notices|map|maps|board|sign|that|this)$",
    re.IGNORECASE,
)
_WHO_MENTIONED_RE = re.compile(r"\bwho\s+(?:mentioned|said|told)\b", re.IGNORECASE)
_LAST_PERSON_RE = re.compile(r"\bwhat did the last person say\b", re.IGNORECASE)
_THAT_NPC_RE = re.compile(r"\bwhat did that npc mean\b", re.IGNORECASE)
_CLAUSE_SPLIT_RE = re.compile(r"\s*;\s*|\s+\band\b\s+|\s+\bthen\b\s+|\s+\bbut\b\s+", re.IGNORECASE)
_EARLIER = re.compile(
    r"\b(?:earlier|before|back when|still where you stand|is that still)\b",
    re.IGNORECASE,
)
_FEELING = re.compile(
    r"\b(?:not how you feel|not your feelings|i was asking about)\b",
    re.IGNORECASE,
)
_WANTED = re.compile(r"\bi meant(?: the)?\s+(.+?)(?:,| not\b|$)", re.IGNORECASE)
_NEGOTIATION = re.compile(
    r"\b(?:promise me|promise you|reward if i|carry a message|swear you(?:'ll| will)|pay me if)\b",
    re.IGNORECASE,
)
_DEICTIC = re.compile(r"\b(?:it|that|this)\b", re.IGNORECASE)
_QUESTION = re.compile(
    r"\?\s*$|^\s*(?:who|what|when|where|why|how|is|are|do|does|did|can|could|would|has|have)\b",
    re.IGNORECASE,
)
_SURVEILLANCE = re.compile(
    r"\b(?:watch(?:es|ed|ing)?|keep(?:ing)? an eye|after dark|patrol)\b",
    re.IGNORECASE,
)
_PERSONAL = re.compile(
    r"\b(?:prefer|rather|what troubles|how do you feel|"
    r"(?:do you|what do you)\s+(?:personally\s+)?(?:like|enjoy))\b",
    re.IGNORECASE,
)
_UNCERTAIN = re.compile(
    r"\b(?:could(?:n't| not)|cannot|can't|do(?:n't| not) know|couldn't tell|could not tell)\b",
    re.IGNORECASE,
)
_IGNORANCE = re.compile(
    r"\b(?:do not know enough|don't know enough|could(?:n't| not) tell you|could not tell you|"
    r"i do not know|i don't know)\b",
    re.IGNORECASE,
)
_STATED_PERSONAL = re.compile(
    r"\b(?:prefer|morning|evening|it's this|it is this|wears on me)\b",
    re.IGNORECASE,
)
_INTERNAL = re.compile(
    r"settled here|speech authority|reply plan|canonical world|not been established|"
    r"information available to you|cannot carry out",
    re.IGNORECASE,
)
_CONSEQUENTIAL_PREFERENCE = re.compile(
    r"\b(?:patrol schedule|abandon|password|reward|silver|quest)\b",
    re.IGNORECASE,
)


def _normalize_governed_span(text: str) -> str:
    raw = " ".join(str(text or "").split())
    raw = re.sub(r"\bwon't\b", "will not", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bdon't\b", "do not", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bcan't\b", "cannot", raw, flags=re.IGNORECASE)
    return raw


def span_abandons_intention(text: str) -> bool:
    """The span drops a topic or plan. It is not a physical command."""
    return bool(_ABANDON_SPAN_RE.search(_normalize_governed_span(text)))


def _return_complement(text: str) -> str:
    match = _TOPIC_RETURN_CUE_RE.search(str(text or ""))
    if not match:
        return ""
    complement = str(text or "")[match.end():]
    complement = re.split(r"[.!?]", complement, maxsplit=1)[0]
    complement = re.split(r"\s+(?:and|then|but)\s+", complement, maxsplit=1, flags=re.IGNORECASE)[0]
    return complement.strip(" ,;:")


def conversational_topic_return(text: str) -> bool:
    """True when return/back language points at a discussion, not a place."""
    raw = " ".join(str(text or "").split())
    if not raw or not _TOPIC_RETURN_CUE_RE.search(raw):
        return False
    return bool(_DISCOURSE_OBJECT_RE.search(_return_complement(raw)))


def attributed_speech_request(text: str) -> str:
    """The explicit speaker reference in a request for earlier speech."""
    raw = str(text or "")
    match = (_ATTRIBUTED_SPEECH_RE.search(raw) or _PRIOR_WARNING_RE.search(raw)
             or _RECALLED_SPEECH_RE.search(raw) or _POSSESSIVE_STATEMENT_RE.search(raw))
    if not match:
        return ""
    who = " ".join((match.group("who") or "").split())
    # "What did you/the notice/the maps say" stays with the existing recall owner.
    if _NON_SPEAKER_WHO_RE.match(who) or re.fullmatch(r"he|she|they", who, re.I):
        return ""
    return who


def _split_governed_clauses(text: str) -> list[str]:
    raw = " ".join(str(text or "").split())
    return [part.strip(" ,.") for part in _CLAUSE_SPLIT_RE.split(raw) if part.strip(" ,.")]


def without_abandoned_clauses(text: str) -> str:
    parts = _split_governed_clauses(text)
    kept = [part for part in parts if not span_abandons_intention(part)]
    return " ".join(kept)


def _row_voice(row: Mapping[str, Any], delivered: str) -> str:
    speaker_id = str(row.get("speaker_id") or "").strip()
    if speaker_id:
        return speaker_id
    name = str(row.get("speaker_name") or "").strip()
    if name:
        return name.casefold()
    match = re.search(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b", delivered)
    return match.group(1).casefold() if match else "host"


def _heard_statement(text: str, session: Mapping[str, Any] | None, *,
                     speaker_id: str = "", speaker_name: str = "",
                     candidates: list[dict[str, Any]] | None = None):
    """A line the player already heard, including a host delivery that names the speaker.

    Returns a row, ``\"ambiguous\"`` when an anaphoric request matches more than
    one speaker, or None.
    """
    from game.dialogue_authority import contains_protected_disclosure
    from game.interaction_completion import attributed_speaker_label

    tokens = reference_subject_tokens(text, speaker_name)
    content = set(tokens) - _ANAPHORIC_TOPIC_TOKENS
    best: tuple[int, dict[str, Any]] | None = None
    voices: set[str] = set()
    for row in (delivered_exchanges(session) if candidates is None else candidates):
        if not isinstance(row, dict) or row.get("uncertain"):
            continue
        delivered = str(row.get("delivered_text") or "").strip()
        if not delivered or contains_protected_disclosure(delivered):
            continue
        if _CLARIFICATION_DELIVERY_RE.search(delivered):
            continue
        if speaker_id or speaker_name:
            id_match = bool(speaker_id) and str(row.get("speaker_id") or "") == speaker_id
            label = str(row.get("speaker_name") or "") or attributed_speaker_label(delivered)
            name_match = bool(speaker_name) and bool(re.search(rf"\b{re.escape(speaker_name)}\b", label, re.I))
            if not id_match and not name_match:
                continue
        supplied = reference_subject_tokens(
            str(row.get("supplied_text") or "") + " " + delivered, speaker_name,
        )
        asked = reference_subject_tokens(str(row.get("player_text") or ""), speaker_name)
        if content:
            score = len(content & supplied) * 10 + len(content & asked)
            if score <= 0:
                continue
        else:
            score = 1
        voices.add(_row_voice(row, delivered))
        if best is None or score >= best[0]:
            best = (score, row)
    if best is None:
        return None
    if not content and len(voices) > 1:
        return "ambiguous"
    return best[1]


def without_nonphysical_clauses(text: str) -> str:
    """Drop abandoned intentions and discourse returns. Keep physical clauses."""
    parts = _split_governed_clauses(text)
    kept = [
        part for part in parts
        if not span_abandons_intention(part) and not conversational_topic_return(part)
    ]
    return " ".join(kept)


def is_incidental_personal(player_text: str) -> bool:
    """A harmless preference or feeling, not a consequential world question."""
    text = str(player_text or "")
    if _CONSEQUENTIAL_PREFERENCE.search(text):
        return False
    if not _YOU.search(text):
        return False
    low = text.lower()
    if _PERSONAL.search(text):
        return True
    return "morning" in low and "evening" in low


def is_unhelpful_personal_ignorance(text: str, authority: Mapping[str, Any] | None) -> bool:
    record = authority if isinstance(authority, Mapping) else {}
    if record.get("improvisation_permitted") is not True:
        return False
    if str(record.get("requested_information") or "") not in {"opinion", "personal_state"}:
        return False
    raw = str(text or "")
    spoken = _quote_span(raw) or raw
    if _STATED_PERSONAL.search(spoken):
        return False
    if _IGNORANCE.search(spoken):
        return True
    words = re.findall(r"[a-z']+", spoken.lower())
    return len(words) <= 3


def bounded_personal_line(name: str, npc_id: str, kind: str) -> str:
    """A stable non-canonical remark. No schedule, payment, or hidden fact."""
    speaker = (name or "They").strip() or "They"
    if kind == "personal_state":
        return f'{speaker} says, "The watch wears on me. That is all."'
    morning = sum(ord(char) for char in (npc_id or speaker)) % 2 == 0
    choice = "the morning" if morning else "the evening"
    return f'{speaker} says, "I prefer {choice}."'


def _core_statement(text: str) -> str:
    cleaned = " ".join(str(text or "").split())
    while cleaned.lower().startswith("i meant this:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    return cleaned


def _quote_span(text: str) -> str:
    spans = re.findall(r'["“]([^"”]+)', str(text or ""))
    if spans:
        return _core_statement(spans[-1])
    return ""


def record_delivered_exchange(
    session: dict[str, Any] | None,
    *,
    player_text: str,
    delivered_text: str,
    scene_id: str = "",
    turn: int = 0,
    social: Mapping[str, Any] | None = None,
    ownership: str = "",
    adoption: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Store the line the player was given. Rejected candidates are not accepted here."""
    if not isinstance(session, dict):
        return None
    delivered = str(delivered_text or "")
    if not delivered.strip():
        return None
    if adoption is not None:
        from game.immutable_valid_response import verify_delivery_record

        if (not adoption.get("immutable") or delivered != str(adoption.get("text") or "")
                or (adoption.get("integrity_digest") and not verify_delivery_record(adoption))):
            raise ValueError("Delivered speech does not match the accepted response")
    payload = social if isinstance(social, Mapping) else {}
    if adoption is not None and adoption.get("authorization_source") in {"host_terminal_safety", "dialogue_authority.disclosure_denied"}:
        payload = {}
        ownership = "gm"
    authority = payload.get("dialogue_authority") if isinstance(payload.get("dialogue_authority"), Mapping) else {}
    speaker_id = str((authority or {}).get("npc_id") or payload.get("npc_id") or "")
    speaker_name = str((authority or {}).get("npc_name") or payload.get("npc_name") or "")
    topic_row = payload.get("topic_revealed") if isinstance(payload.get("topic_revealed"), Mapping) else {}
    own = ownership or ("npc" if speaker_id and speaker_name and speaker_name.lower() in delivered.lower() else "gm")
    if _INTERNAL.search(delivered):
        own = "gm"
    supplied = _quote_span(delivered)
    row = {
        "speaker_id": speaker_id if own == "npc" else "",
        "speaker_name": speaker_name if own == "npc" else "",
        "addressee": "player",
        "ownership": own,
        "player_text": str(player_text or "")[:400],
        "delivered_text": delivered,
        "subject": str((authority or {}).get("subject") or "")[:80],
        "topic_id": str(topic_row.get("id") or ""),
        "requested_information": str((authority or {}).get("requested_information") or ""),
        "supplied_text": supplied,
        "uncertain": bool(_UNCERTAIN.search(supplied or delivered)),
        "commitment": bool(authority) and str((authority or {}).get("knowledge_posture") or "") not in {"", "established"},
        "scene_id": str(scene_id or ""),
        "turn": int(turn or 0),
        "active": True,
    }
    from game.expressive_dialogue import proposition_identity

    adoption_map = adoption if isinstance(adoption, Mapping) else {}
    topic_text = str(topic_row.get("text") or topic_row.get("clue_text") or "")
    authorized = str(
        adoption_map.get("authorized_proposition")
        or authority.get("authorized_proposition")
        or topic_text
        or supplied
    )
    explicit = str(adoption_map.get("proposition_id") or authority.get("proposition_id") or payload.get("proposition_id") or "")
    row["authorized_proposition"] = authorized
    row["answer_sufficiency"] = str(adoption_map.get("answer_sufficiency") or authority.get("answer_sufficiency") or "")
    semantic_plan = authority.get("unified_semantic_plan") if isinstance(authority.get("unified_semantic_plan"), Mapping) else payload.get("unified_semantic_plan")
    if not (isinstance(semantic_plan, Mapping) and semantic_plan.get("locked")):
        from game.unified_semantic_planning import take_staged_plan

        semantic_plan = take_staged_plan(session, player_text)
    else:
        from game.unified_semantic_planning import take_staged_plan

        take_staged_plan(session, player_text)
    if isinstance(semantic_plan, Mapping) and semantic_plan.get("locked"):
        from game.unified_semantic_planning import delivered_plan_fields

        stored_plan = delivered_plan_fields(semantic_plan)
        if stored_plan:
            row["unified_semantic_plan"] = stored_plan
    row["proposition_id"] = proposition_identity(
        speaker_id=speaker_id if own == "npc" else "",
        topic_id="" if explicit else str(topic_row.get("id") or ""),
        text=authorized,
        explicit=explicit,
    )
    if adoption is not None:
        row["response_integrity_digest"] = str(adoption.get("integrity_digest") or "")
        row["authorization_source"] = str(adoption.get("authorization_source") or adoption.get("provenance") or "")
        row["adoption_turn_identity"] = str(adoption.get("turn_identity") or "")
        # Disclosure refusals are stored as GM-owned rows with no NPC speaker.
        # A different non-empty speaker is still a mismatch.
        if speaker_id and adoption.get("speaker_id") and str(adoption["speaker_id"]) != speaker_id:
            raise ValueError("Delivered speech speaker does not match adoption")
    ctx = session.setdefault("conversational_context", {})
    if not isinstance(ctx, dict):
        return None
    rows = ctx.get(DELIVERED_KEY)
    if not isinstance(rows, list):
        rows = []
        ctx[DELIVERED_KEY] = rows
    if rows and isinstance(rows[-1], dict):
        last = rows[-1]
        if last.get("turn") == row["turn"] and last.get("delivered_text") == row["delivered_text"] and last.get("player_text") == row["player_text"]:
            return last
        last["active"] = False
    rows.append(row)
    if isinstance(semantic_plan, Mapping) and semantic_plan.get('locked'):
        from game.conversational_referents import commit

        commit(session, row, semantic_plan, adoption)
    while len(rows) > MAX_DELIVERED:
        disposable = next((index for index, item in enumerate(rows) if item.get("ownership") != "npc"), None)
        del rows[0 if disposable is None else disposable]
    return row


def delivered_exchanges(session: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(session, Mapping):
        return []
    ctx = session.get("conversational_context")
    if not isinstance(ctx, Mapping):
        return []
    rows = ctx.get(DELIVERED_KEY)
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def last_delivered_exchange(session: Mapping[str, Any] | None) -> dict[str, Any] | None:
    rows = delivered_exchanges(session)
    return rows[-1] if rows else None


def _blob(row: Mapping[str, Any]) -> str:
    return " ".join(
        str(row.get(key) or "")
        for key in ("supplied_text", "subject", "player_text", "delivered_text", "requested_information")
    ).lower()


def _tokens(text: str) -> list[str]:
    found = []
    raw = str(text or "").replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")
    for tok in re.findall(r"[a-z']{3,}", raw.lower()):
        tok = tok.strip("'")
        if tok.endswith("'s"):
            tok = tok[:-2]
        if len(tok) >= 3 and tok not in _STOP:
            found.append(tok)
    return found


def reference_subject_tokens(text: str, names: str = "") -> set[str]:
    """Subject evidence from the request, excluding speech acts and names."""
    structural = {"repeat", "recall", "remind", "told", "last", "answer", "simpler", "plain", "can", "going", "return",
                  "statement", "remark", "thing", "previous", "personally", "whether",
                  "sergeant", "corporal", "captain", "game", "master", "exactly",
                  "she", "her", "him", "his", "earlier", "speech", "one", "why"}
    return set(_tokens(text)) - set(_tokens(names)) - structural


def _best_exchange(text: str, rows: list[dict[str, Any]], npc_id: str = "") -> dict[str, Any] | str | None:
    from game.dialogue_authority import topic_supports_requested_information
    pool = [row for row in rows if row.get("ownership") == "npc"]
    names = " ".join(str(row.get("speaker_name") or "") for row in pool)
    named = {str(row.get("speaker_id")) for row in pool
             if any(re.search(rf"\b{re.escape(word)}\b", text, re.I)
                    for word in str(row.get("speaker_name") or "").split()
                    if word.lower() not in {"sergeant", "corporal", "captain"})}
    if len(named) > 1:
        return "ambiguous"
    constrained = next(iter(named)) if named else npc_id
    if constrained:
        pool = [row for row in pool if row.get("speaker_id") == constrained]
    if not pool:
        return None
    tokens = reference_subject_tokens(text, names)
    if not tokens:
        if not constrained and len({row.get("speaker_id") for row in pool}) > 1:
            return "ambiguous"
        return pool[-1]
    scored = []
    for row in pool:
        supplied = str(row.get("supplied_text") or "")
        if not row.get("uncertain") and not topic_supports_requested_information(text, supplied):
            continue
        overlap = tokens & reference_subject_tokens(str(row.get("subject") or "") + " " + supplied, names)
        if not overlap:
            overlap = tokens & reference_subject_tokens(str(row.get("player_text") or ""), names)
        if overlap:
            scored.append((len(overlap), row))
    if not scored:
        # "In other words" names no new subject. Bind the latest line of the
        # only speaker, the same way an empty "simpler words" request does.
        if re.search(r"\b(?:other words|another way|rephrase|paraphrase)\b", text, re.I):
            speakers = {row.get("speaker_id") for row in pool}
            if len(speakers) == 1:
                return pool[-1]
        return None
    best = max(score for score, _ in scored)
    winners = [row for score, row in scored if score == best]
    if len({_proposition_key(row) for row in winners}) > 1:
        return "ambiguous"
    return winners[-1]


def _proposition_key(row: Mapping[str, Any]) -> tuple[str, str]:
    """Equivalent wording shares a key. Different propositions do not."""
    speaker = str(row.get("speaker_id") or "")
    pid = str(row.get("proposition_id") or "")
    if pid:
        return speaker, pid
    topic = str(row.get("topic_id") or "")
    if topic:
        return speaker, "topic:" + speaker + ":" + topic
    return speaker, "text:" + " ".join(_tokens(str(row.get("supplied_text") or "")))


def recall_kind(player_text: str) -> str:
    """exact, restatement, explanation, or subject. Exact keeps delivered wording."""
    text = str(player_text or "")
    if re.search(r"\b(?:exactly|exact words|word for word)\b", text, re.IGNORECASE):
        return "exact"
    if re.search(r"\b(?:other words|another way|rephrase|paraphrase|(?:simpler|plainer|plain) words)\b", text, re.IGNORECASE):
        return "restatement"
    if re.search(r"\b(?:what (?:did|do|does).{0,32}mean|explain)\b", text, re.IGNORECASE):
        return "explanation"
    if reference_subject_tokens(text):
        return "subject"
    return "exact"


def _equivalent_rows(exchange: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key = _proposition_key(exchange)
    return [row for row in rows if row.get("ownership") == "npc" and _proposition_key(row) == key]


def _quote_many(exchange: Mapping[str, Any], rows: list[dict[str, Any]]) -> str:
    """List distinct delivered sentences of one proposition. One sentence stays unchanged."""
    distinct: list[str] = []
    for row in _equivalent_rows(exchange, rows):
        delivered = str(row.get("delivered_text") or "").strip()
        if delivered and delivered not in distinct:
            distinct.append(delivered)
    if len(distinct) <= 1:
        return ""
    name = str(exchange.get("speaker_name") or "They")
    parts = []
    for index, delivered in enumerate(distinct):
        spans = re.findall(r'["“]([^"”]+)', delivered)
        inner = spans[-1] if spans else str(exchange.get("supplied_text") or delivered)
        lead = f"{name} said" if index == 0 else f"{name} also said"
        parts.append(f'{lead}: "{inner}"')
    return " ".join(parts)


def _npc_quote(name: str, exchange: Mapping[str, Any]) -> str:
    # Faithful repetition needs neither generation nor factual reauthorization.
    delivered = str(exchange.get("delivered_text") or "").strip()
    if delivered:
        return delivered
    speaker = name or str(exchange.get("speaker_name") or "They")
    return f'{speaker} says, "{str(exchange.get("supplied_text") or "")}"'


def _gm_quote(exchange: Mapping[str, Any]) -> str:
    name = str(exchange.get("speaker_name") or "They")
    delivered = str(exchange.get("delivered_text") or "")
    spans = re.findall(r'["“]([^"”]+)', delivered)
    supplied = spans[-1] if spans else str(exchange.get("supplied_text") or "").strip()
    return f'{name} said: "{supplied}"'


def _absent_line(exchange: Mapping[str, Any]) -> str:
    name = str(exchange.get("speaker_name") or "They")
    if exchange.get("uncertain"):
        detail = f"When you last spoke, {name} could not answer that."
    else:
        supplied = str(exchange.get("supplied_text") or "").strip()
        detail = f'When you last spoke, {name} said: "{supplied}"' if supplied else f"When you last spoke, {name} did not establish anything further."
    return (
        f"{name} is not here, so I will not speak to {name} from this place. "
        f"{detail} Nothing new has been established since that conversation. "
        "Do you want that recalled as it stands, or are you speaking to someone here?"
    )


def _ambiguous_line(rows: list[dict[str, Any]]) -> str:
    names = []
    for row in rows:
        name = str(row.get("speaker_name") or "").strip()
        if name and name not in names:
            names.append(name)
    if len(names) >= 2:
        return f"Do you mean what {names[0]} said, or what {names[1]} said? Nothing has been attempted."
    return "Which earlier remark do you mean? Nothing has been attempted."


def _present(scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    from game.ordinary_semantic_ownership import _visible_npcs

    return {str(npc.get("id") or ""): npc for npc in _visible_npcs(scene, world) if npc.get("id")}


def _active_id(session: Mapping[str, Any] | None, present: Mapping[str, Mapping[str, Any]]) -> str:
    from game.ordinary_semantic_ownership import _active_npc_id

    return _active_npc_id(session, list(present.values()))


_REVISION_ONLY = re.compile(
    r"\b(?:instead|make that|change that|i meant|revise)\b",
    re.IGNORECASE,
)
_GM_HELP = re.compile(
    r"\b(?:interpret|explain the rules|summarize|help me understand)\b",
    re.IGNORECASE,
)


def _pending_blocks(session: Mapping[str, Any] | None, text: str) -> bool:
    if not _REVISION_ONLY.search(text) or _FEELING.search(text):
        return False
    if not isinstance(session, Mapping):
        return False
    ctx = session.get("conversational_context")
    if not isinstance(ctx, Mapping):
        return False
    pending = ctx.get("pending_intention") if isinstance(ctx.get("pending_intention"), Mapping) else None
    if pending is None and isinstance(ctx.get("pending_clarification"), Mapping):
        pending = ctx.get("pending_clarification")
    if not isinstance(pending, Mapping):
        return False
    return str(pending.get("status") or "pending") != "executed"


def _names_other(text: str, present: Mapping[str, Mapping[str, Any]], active: str) -> bool:
    """A different person's name does not keep the previous interlocutor."""
    if not active:
        return False
    low = text.lower()
    active_name = str((present.get(active) or {}).get("name") or "").strip().lower()
    if active_name and active_name in low:
        return False
    for npc_id, npc in present.items():
        if npc_id == active:
            continue
        name = str(npc.get("name") or "").strip().lower()
        if name and name in low:
            return True
    return False


def _vocative(text: str, present: Mapping[str, Mapping[str, Any]]) -> str:
    for npc_id, npc in present.items():
        name = str(npc.get("name") or "").strip()
        if name and re.search(rf"(?:^|[.!?]\s+){re.escape(name)}\s*[,:]", text, re.IGNORECASE):
            return npc_id
    return ""


def _unique_name_token(text: str, present: Mapping[str, Mapping[str, Any]]) -> str:
    """One present person named by any whole word of their authored name."""
    hits = []
    for npc_id, npc in present.items():
        words = [word for word in str(npc.get("name") or "").split() if len(word) >= 4]
        if any(re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE) for word in words):
            hits.append(npc_id)
    return hits[0] if len(hits) == 1 else ""


def _unique_named(text: str, present: Mapping[str, Mapping[str, Any]]) -> str:
    low = text.lower()
    hits = [
        npc_id
        for npc_id, npc in present.items()
        if str(npc.get("name") or "").strip() and str(npc.get("name") or "").strip().lower() in low
    ]
    return hits[0] if len(hits) == 1 else ""


def _named(present: Mapping[str, Mapping[str, Any]], npc_id: str) -> str:
    npc = present.get(npc_id) or {}
    return str(npc.get("name") or npc_id or "They")


def supplied_clarification(
    player_text: str,
    session: Mapping[str, Any] | None,
    npc_id: str,
    npc_name: str,
    npc: Mapping[str, Any] | None = None,
) -> str:
    """Quote the delivered statement when this question asks what it meant."""
    text = " ".join(str(player_text or "").split())
    if not text or not (_MEANING.search(text) or _REPEAT.search(text) or _RECALLED_SPEECH_RE.search(text)):
        return ""
    if (_GM.search(text) or _THIRD.search(text)) and not _YOU.search(text):
        return ""
    found = _best_exchange(text, delivered_exchanges(session), npc_id)
    if found == "ambiguous":
        return f'{npc_name or "They"} says, "Which earlier remark do you mean?"'
    if not isinstance(found, dict):
        return f'{npc_name or "They"} says, "Which statement do you mean?"'
    if npc_id and str(found.get("speaker_id") or "") not in {"", npc_id}:
        return ""
    from game.dialogue_authority import historical_disclosure_permitted
    if not historical_disclosure_permitted(found, npc):
        return f'{npc_name or "They"} says, "I cannot share that information."'
    return _npc_quote(npc_name or str(found.get("speaker_name") or "They"), found)


def find_reusable_commitment(session: Mapping[str, Any] | None, npc_id: str, player_text: str,
                             npc: Mapping[str, Any] | None = None) -> str:
    if not is_incidental_personal(player_text) and not _PERSONAL.search(player_text or ""):
        return ""
    if not isinstance(session, Mapping):
        return ""
    ctx = session.get("conversational_context")
    rows = ctx.get("dialogue_commitments") if isinstance(ctx, Mapping) else None
    if not isinstance(rows, list):
        return ""
    tokens = set(_tokens(player_text))
    pref = {"morning", "evening", "prefer", "rather"}
    for row in reversed(rows):
        if not isinstance(row, dict) or str(row.get("status") or "active") != "active":
            continue
        if npc_id and str(row.get("npc_id") or "") != npc_id:
            continue
        if str(row.get("kind") or "") not in {"opinion", "partial_answer"}:
            continue
        from game.dialogue_authority import commitment_disclosure_permitted
        if not commitment_disclosure_permitted(row, npc):
            continue
        subject = set(str(row.get("subject") or "").split())
        if tokens & subject or (tokens & pref and subject & pref) or (pref & set(_tokens(str(row.get("text") or "")))):
            text = str(row.get("text") or "").strip()
            if text:
                return text
    return ""


def established_scene_object_ids(player_text: str, scene: Mapping[str, Any] | None) -> set[str]:
    """Interactable ids whose authored label or alias is named in this utterance.

    A short token is not enough. The match is a whole authored name, so a
    shared word does not select an object and two names stay unresolved.
    """
    text = " ".join(str(player_text or "").split())
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if not text or not isinstance(inner, Mapping):
        return set()
    found: set[str] = set()
    for item in inner.get("interactables") or []:
        if not isinstance(item, Mapping):
            continue
        entity_id = str(item.get("id") or "").strip()
        if not entity_id:
            continue
        names = [item.get("label"), item.get("name"), entity_id.replace("_", " ")]
        names.extend(item.get("aliases") or [])
        for name in names:
            cleaned = " ".join(str(name or "").split())
            if len(cleaned) < 4:
                continue
            if re.search(rf"\b{re.escape(cleaned)}\b", text, re.IGNORECASE):
                found.add(entity_id)
                break
    return found


def continuity_directive(
    player_text: str,
    *,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return a grounding directive, or None to leave the existing decision path alone."""
    text = " ".join(str(player_text or "").split())
    from game.unified_semantic_planning import migrated_turn_should_abstain_legacy

    if migrated_turn_should_abstain_legacy(text, session=session, scene=scene, world=world):
        return None
    if (
        not text
        or _UNDO.search(text)
        or _SCENE.search(text)
        or _EXPLICIT_ASK.search(text)
        or _RULES.search(text)
        or _HIDDEN.search(text)
        or _CONDITIONAL_ACTION.search(text)
    ):
        return None
    # "Go back to what was said" is a topic, even though "go" is also a world verb.
    attributed = _ATTRIBUTED_SPEECH_RE.search(text)
    possessive = _POSSESSIVE_STATEMENT_RE.fullmatch(text)
    recalled_speech = _RECALLED_SPEECH_RE.search(text)
    repeats = bool(_REPEAT.search(text) or recalled_speech
                   or _CONTEXTUAL_STATEMENT_RE.fullmatch(text) or possessive
                   or (attributed and re.fullmatch(r"he|she|they|you", attributed.group("who"), re.I)))
    if (
        _WORLD.search(text)
        and not repeats
        and not attributed
        and not _NEGOTIATION.search(text)
        and not conversational_topic_return(text)
    ):
        return None
    if _pending_blocks(session, text):
        return None
    if (re.match(r"^(?:(?:i|we)\s+)?(?:go back|return) to\b", text, re.I)
            and not _QUESTION.search(text) and established_scene_object_ids(text, scene)):
        return None
    # "Go back to the Frontier Gate" is travel. "Go back to what was said" is not.
    if _TOPIC_RETURN_CUE_RE.search(text) and not conversational_topic_return(text):
        inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else (scene or {})
        exits = [dict(item) for item in (inner.get("exits") or []) if isinstance(item, Mapping)]
        if exits:
            from game.scene_destination_binding import resolve_authored_exit_from_player_travel

            if resolve_authored_exit_from_player_travel(text, exits):
                return None
    present = _present(scene, world)
    active = _active_id(session, present)
    from game.dialogue_authority import historical_disclosure_permitted
    people = {str(n.get("id") or ""): n for n in (world or {}).get("npcs") or [] if isinstance(n, Mapping)}
    rows = [r for r in delivered_exchanges(session)
            if historical_disclosure_permitted(r, people.get(str(r.get("speaker_id") or "")))]
    if repeat_speaker := _REPEAT_SPEAKER_RE.fullmatch(text):
        title = repeat_speaker.group("speaker").casefold()
        repeats = repeats or any(
            title == str(row.get("speaker_name") or "").casefold()
            for row in rows if row.get("ownership") == "npc"
        )
    ctx = (session or {}).get("conversational_context") or {}
    last_gm = ctx.get("last_gm_exchange") or {}
    # Conversational recency includes GM questions that are not NPC disclosures.
    # Keep the filtered rows for historical recall below.
    latest = last_delivered_exchange(session) or {}
    scene_id = str(((scene or {}).get("scene") or scene or {}).get("id") or "")

    def _recall_line(exchange: Mapping[str, Any]) -> str:
        delivered = str(exchange.get("delivered_text") or "").strip()
        return delivered or _gm_quote(exchange)

    def _recall_answer(exchange: Mapping[str, Any], reason: str) -> dict[str, Any]:
        return {
            "action": "answer",
            "owner": "gm",
            "npc_id": str(exchange.get("speaker_id") or ""),
            "npc_name": str(exchange.get("speaker_name") or ""),
            "line": _recall_line(exchange),
            "reason": reason,
            "proposition_id": str(exchange.get("proposition_id") or ""),
            "topic_grounding": {
                "speaker_id": exchange.get("speaker_id"),
                "ownership": "gm",
                "reference": "delivered_speech",
                "topic_id": exchange.get("topic_id"),
                "proposition_id": exchange.get("proposition_id"),
                "selected_source": exchange.get("authorization_source"),
                "delivered_turn": exchange.get("turn"),
                "canonical": False,
            },
        }

    def _not_established(line: str) -> dict[str, Any]:
        return {
            "action": "clarify",
            "owner": "gm",
            "npc_id": "",
            "npc_name": "",
            "line": line,
            "reason": "missing_delivered_reference",
        }

    if conversational_topic_return(text):
        focus = without_abandoned_clauses(text) or text
        topic_found = _best_exchange(focus, rows, "")
        if topic_found == "ambiguous":
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": "",
                "npc_name": "",
                "line": _ambiguous_line(rows),
                "reason": "ambiguous_delivered_reference",
            }
        if isinstance(topic_found, dict):
            return _recall_answer(topic_found, "conversational_topic_return")
        heard = _heard_statement(focus, session)
        if heard == "ambiguous":
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": "",
                "npc_name": "",
                "line": _ambiguous_line(rows),
                "reason": "ambiguous_delivered_reference",
            }
        if isinstance(heard, dict):
            return _recall_answer(heard, "conversational_topic_return")
        return _not_established(
            "That earlier discussion is not established. Nothing has been attempted."
        )
    if _WHO_MENTIONED_RE.search(text):
        mentioned = _best_exchange(text, rows, "")
        if isinstance(mentioned, dict):
            return _recall_answer(mentioned, "delivered_speaker_attribution")
        heard = _heard_statement(text, session)
        if isinstance(heard, dict):
            return _recall_answer(heard, "delivered_speaker_attribution")
        if mentioned == "ambiguous":
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": "",
                "npc_name": "",
                "line": _ambiguous_line(rows),
                "reason": "ambiguous_delivered_reference",
            }
        return _not_established(
            "Nobody in the conversation so far is established as having said that. Nothing has been attempted."
        )
    if _LAST_PERSON_RE.search(text) or _THAT_NPC_RE.search(text):
        latest = [
            row for row in delivered_exchanges(session)
            if isinstance(row, dict)
            and not row.get("uncertain")
            and str(row.get("delivered_text") or "").strip()
            and not _CLARIFICATION_DELIVERY_RE.search(str(row.get("delivered_text") or ""))
        ]
        if _LAST_PERSON_RE.search(text) and latest:
            return _recall_answer(latest[-1], "delivered_speaker_attribution")
        heard = _heard_statement("", session)
        if heard == "ambiguous":
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": "",
                "npc_name": "",
                "line": _ambiguous_line(rows) or "Which speaker do you mean?",
                "reason": "ambiguous_delivered_reference",
            }
        if isinstance(heard, dict):
            return _recall_answer(heard, "delivered_speaker_attribution")
        return _not_established(
            "No earlier statement is established. Nothing has been attempted."
        )
    named_speaker = ""
    who = attributed_speech_request(text)
    if who:
        if established_scene_object_ids(who, scene):
            return None
        named_speaker = _unique_name_token(who, present)
        if not named_speaker:
            hits: list[str] = []
            for row in rows:
                if row.get("ownership") != "npc":
                    continue
                speaker_id = str(row.get("speaker_id") or "")
                words = [word for word in str(row.get("speaker_name") or "").split() if len(word) >= 4]
                if speaker_id and any(re.search(rf"\b{re.escape(word)}\b", who, re.IGNORECASE) for word in words):
                    if speaker_id not in hits:
                        hits.append(speaker_id)
            named_speaker = hits[0] if len(hits) == 1 else ""
        if not named_speaker:
            heard = _heard_statement(text, session, speaker_name=who, candidates=rows)
            if heard == "ambiguous":
                return {
                    "action": "clarify",
                    "owner": "gm",
                    "npc_id": "",
                    "npc_name": "",
                    "line": _ambiguous_line(rows),
                    "reason": "ambiguous_delivered_reference",
                }
            if isinstance(heard, dict):
                return _recall_answer(heard, "delivered_speaker_attribution")
            return _not_established(
                f"Nothing {who} said about that is established. Nothing has been attempted."
            )
    # A bare request to repeat/clarify refers to the latest delivered question,
    # not an older NPC disclosure. Explicit speaker/subject recall still uses
    # the existing historical selector below. Keep the pending intent intact.
    if ((repeats or _MEANING.search(text))
            and latest.get("ownership") == "gm"
            and last_gm.get("category") == "CLARIFY"
            and last_gm.get("scene_id") == scene_id
            and latest.get("delivered_text") == last_gm.get("response")
            and not _unique_named(text, present)
            and not reference_subject_tokens(text, " ".join(str(n.get("name") or "") for n in present.values()))):
        return {"action": "clarify", "owner": "gm", "npc_id": "", "npc_name": "",
                "line": str(last_gm["response"]), "reason": "repeat_pending_clarification"}
    if _names_other(text, present, active) and not named_speaker:
        return None
    found = _best_exchange(
        text, rows, named_speaker or ("" if _GM.search(text) else active),
    )
    if found == "ambiguous" and (named_speaker or repeats or _GM.search(text) or _MEANING.search(text) or _DEICTIC.search(text)):
        return {
            "action": "clarify",
            "owner": "gm",
            "npc_id": "",
            "npc_name": "",
            "line": _ambiguous_line(rows),
            "reason": "ambiguous_delivered_reference",
        }
    exchange = found if isinstance(found, dict) else None
    if named_speaker:
        label = _named(present, named_speaker) if named_speaker in present else "That person"
        for row in rows:
            if str(row.get("speaker_id") or "") == named_speaker and str(row.get("speaker_name") or "").strip():
                label = str(row.get("speaker_name") or label)
                break
        if not isinstance(exchange, dict):
            # "What did the guard say?" names the speaker and no other subject.
            subject = reference_subject_tokens(text, label)
            speaker_rows = [
                row for row in rows
                if str(row.get("speaker_id") or "") == named_speaker
                and row.get("ownership") == "npc"
                and not row.get("uncertain")
            ]
            if speaker_rows and not subject:
                exchange = speaker_rows[-1]
        if not isinstance(exchange, dict):
            exchange = _heard_statement(text, session, speaker_id=named_speaker,
                                        speaker_name=label, candidates=rows)
        if isinstance(exchange, dict) and (
            str(exchange.get("speaker_id") or "") in {"", named_speaker}
            or label.casefold() in str(exchange.get("delivered_text") or "").casefold()
        ):
            if (named_speaker not in present and exchange.get("speaker_id") == named_speaker
                    and recalled_speech and recalled_speech.group("request").lower().startswith("repeat")):
                return {
                    "action": "clarify", "owner": "gm", "npc_id": named_speaker,
                    "npc_name": label, "line": _absent_line(exchange), "reason": "absent_npc_reference",
                }
            return _recall_answer(exchange, "delivered_speaker_attribution")
        return _not_established(
            f"Nothing {label} said about that is established. Nothing has been attempted."
        )
    named = _unique_named(text, present)
    speaker_id = named or active or (str(exchange.get("speaker_id") or "") if exchange else "")
    if not speaker_id and len(present) == 1:
        speaker_id = next(iter(present))
    speaker_present = bool(speaker_id and speaker_id in present)
    speaker_name = _named(present, speaker_id) if speaker_present else str((exchange or {}).get("speaker_name") or "")

    def _ask() -> dict[str, Any]:
        return {
            "action": "ask",
            "owner": "npc",
            "npc_id": speaker_id,
            "npc_name": speaker_name,
            "line": "",
            "reason": "conversational_continuity_ask",
        }

    gm_about_speech = bool(
        (_GM.search(text) and re.search(r"\b(?:said|say|mean|meant|repeat|recall|earlier)\b", text, re.I))
        or (_THIRD.search(text) and not _YOU.search(text) and (_MEANING.search(text) or _EARLIER.search(text)))
    )
    if gm_about_speech:
        if not exchange:
            if not _GM.search(text) or not re.search(r"\b(?:say|said|repeat|recall)\b", text, re.I):
                return None
            return {"action": "clarify", "owner": "gm", "npc_id": "", "npc_name": "",
                    "line": "Which earlier statement do you mean?", "reason": "missing_delivered_reference"}
        recalled = _gm_quote(exchange)
        if recall_kind(text) in {"exact", "subject", "explanation"}:
            many = _quote_many(exchange, rows)
            if many:
                recalled = many
        return {
            "action": "answer",
            "owner": "gm",
            "npc_id": str(exchange.get("speaker_id") or ""),
            "npc_name": str(exchange.get("speaker_name") or ""),
            "line": recalled,
            "reason": "gm_recall_of_npc_statement",
            "proposition_id": str(exchange.get("proposition_id") or ""),
            "topic_grounding": {
                "speaker_id": exchange.get("speaker_id"), "ownership": "gm",
                "reference": "delivered_speech", "topic_id": exchange.get("topic_id"),
                "proposition_id": exchange.get("proposition_id"),
                "selected_source": exchange.get("authorization_source"),
                "delivered_turn": exchange.get("turn"), "canonical": False,
            },
        }
    if _FEELING.search(text):
        if exchange and speaker_present:
            return {
                "action": "answer",
                "owner": "npc",
                "npc_id": speaker_id,
                "npc_name": speaker_name,
                "line": _npc_quote(speaker_name, exchange),
                "reason": "conversational_topic_correction",
            }
        if exchange and not speaker_present:
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": str(exchange.get("speaker_id") or ""),
                "npc_name": str(exchange.get("speaker_name") or ""),
                "line": _absent_line(exchange),
                "reason": "absent_npc_reference",
            }
    if _NEGOTIATION.search(text):
        if not speaker_present:
            if exchange:
                return {
                    "action": "clarify",
                    "owner": "gm",
                    "npc_id": str(exchange.get("speaker_id") or ""),
                    "npc_name": str(exchange.get("speaker_name") or ""),
                    "line": _absent_line(exchange),
                    "reason": "absent_npc_reference",
                }
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": "",
                "npc_name": "",
                "line": "Who are you asking that of? Nothing has been promised.",
                "reason": "unresolved_request_addressee",
            }
        return {
            "action": "answer",
            "owner": "npc",
            "npc_id": speaker_id,
            "npc_name": speaker_name,
            "line": f'{speaker_name} says, "I can\'t promise you a reward for that."',
            "reason": "npc_request_declined",
        }
    if repeats and not isinstance(exchange, dict):
        from game.interaction_completion import attributed_speaker_label

        titled = _unique_name_token(text, present)
        matched = []
        for row in rows:
            if row.get("uncertain"):
                continue
            bound = str(row.get("speaker_id") or "") if row.get("ownership") == "npc" else ""
            if not bound and row.get("scene_id") == scene_id and row.get("supplied_text"):
                # Legacy GM delivery can carry an explicitly attributed quote.
                label = attributed_speaker_label(str(row.get("delivered_text") or ""))
                speakers = [key for key in present if label.casefold() == _named(present, key).casefold()]
                bound = speakers[0] if len(speakers) == 1 else ""
            if bound and (not titled or titled == bound):
                matched.append((row, bound))
        subject = reference_subject_tokens(text, " ".join(_named(present, key) for key in present))
        if subject - _ANAPHORIC_TOPIC_TOKENS or (not titled and len({key for _, key in matched}) > 1):
            matched = []
        if matched:
            exchange, speaker_id = matched[-1]
            speaker_present = speaker_id in present
            speaker_name = _named(present, speaker_id) if speaker_present else str(exchange.get("speaker_name") or "")
    if repeats and exchange:
        if exchange.get("speaker_id") and exchange["speaker_id"] != speaker_id:
            return _not_established("Which earlier statement do you mean?")
        if speaker_present:
            if (latest.get("ownership") == "gm" and latest != exchange and not named and not active
                    and not reference_subject_tokens(text) and not possessive):
                return _not_established("Which earlier statement do you mean?")
            return {
                "action": "answer",
                "owner": "npc",
                "npc_id": speaker_id,
                "npc_name": speaker_name,
                "line": _npc_quote(speaker_name, exchange),
                "reason": "repeat_delivered_statement",
            }
        return {
            "action": "clarify",
            "owner": "gm",
            "npc_id": str(exchange.get("speaker_id") or ""),
            "npc_name": str(exchange.get("speaker_name") or ""),
            "line": _absent_line(exchange),
            "reason": "absent_npc_reference",
        }
    if repeats:
        return _not_established("Which earlier statement do you mean?")
    if _EARLIER.search(text):
        # "What did that notice say earlier?" names the object, not the speaker.
        if established_scene_object_ids(text, scene) and not _unique_named(text, present):
            return None
        if not exchange and not speaker_present:
            speakers = {str(row.get("speaker_id") or ""): str(row.get("speaker_name") or "")
                        for row in rows if row.get("ownership") == "npc"}
            if len(speakers) == 1:
                old_id, old_name = next(iter(speakers.items()))
                return {"action": "clarify", "owner": "gm", "npc_id": old_id,
                        "npc_name": old_name, "line": f"{old_name} is not here. Which earlier statement do you mean?",
                        "reason": "missing_absent_reference"}
        if exchange and not speaker_present:
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": str(exchange.get("speaker_id") or ""),
                "npc_name": str(exchange.get("speaker_name") or ""),
                "line": _absent_line(exchange),
                "reason": "absent_npc_reference",
            }
        if speaker_present:
            return _ask()
        return None
    if _MEANING.search(text):
        if speaker_present:
            return _ask()
        if exchange:
            return {
                "action": "clarify",
                "owner": "gm",
                "npc_id": str(exchange.get("speaker_id") or ""),
                "npc_name": str(exchange.get("speaker_name") or ""),
                "line": _absent_line(exchange),
                "reason": "absent_npc_reference",
            }
        return None
    if is_incidental_personal(text) and speaker_present:
        return _ask()
    if (_DEICTIC.search(text) and _QUESTION.search(text) and speaker_present
            and (exchange or any(row.get("ownership") == "npc" and row.get("speaker_id") == speaker_id for row in rows))):
        # "That notice" names a scene object. It is not a request to continue
        # the previous speaker, and an ambiguous object is not given to them either.
        if established_scene_object_ids(text, scene):
            return None
        return _ask()
    if _vocative(text, present) and speaker_present and _QUESTION.search(text) and not gm_about_speech:
        return _ask()
    return None


def active_followup_target(
    player_text: str,
    *,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> str:
    """An ordinary question in an open conversation stays with that NPC."""
    text = " ".join(str(player_text or "").split())
    if not text or not _QUESTION.search(text):
        return ""
    if _GM.search(text) or _RULES.search(text) or _HIDDEN.search(text) or _SCENE.search(text) or _EXPLICIT_ASK.search(text) or _GM_HELP.search(text):
        return ""
    if _THIRD.search(text) and not _YOU.search(text):
        return ""
    if re.search(r"\b(?:what do i|why did i|what did i|do i already)\b", text, re.IGNORECASE):
        return ""
    present = _present(scene, world)
    active = _active_id(session, present)
    return active if active in present else ""
