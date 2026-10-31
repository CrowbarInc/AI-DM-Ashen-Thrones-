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
MAX_DELIVERED = 8

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
    r"your answer|by that|what was that|that name)\b",
    re.IGNORECASE,
)
_CONDITIONAL_ACTION = re.compile(
    r"\?\s*(?:if|provided|unless|otherwise)\b",
    re.IGNORECASE,
)
_HIDDEN = re.compile(r"\b(?:passwords?|passcodes?)\b", re.IGNORECASE)
_REPEAT = re.compile(
    r"\b(?:say that again|plainer words|in other words|go back to|back to the)\b",
    re.IGNORECASE,
)
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
    delivered = " ".join(str(delivered_text or "").split())
    if not delivered:
        return None
    if adoption is not None:
        from game.immutable_valid_response import semantic_equal

        if not adoption.get("immutable") or not semantic_equal(delivered, str(adoption.get("text") or "")):
            raise ValueError("Delivered speech does not match the accepted response")
    payload = social if isinstance(social, Mapping) else {}
    authority = payload.get("dialogue_authority") if isinstance(payload.get("dialogue_authority"), Mapping) else {}
    speaker_id = str((authority or {}).get("npc_id") or payload.get("npc_id") or "")
    speaker_name = str((authority or {}).get("npc_name") or payload.get("npc_name") or "")
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
        "requested_information": str((authority or {}).get("requested_information") or ""),
        "supplied_text": supplied[:240],
        "uncertain": bool(_UNCERTAIN.search(supplied or delivered)),
        "commitment": bool(authority) and str((authority or {}).get("knowledge_posture") or "") not in {"", "established"},
        "scene_id": str(scene_id or ""),
        "turn": int(turn or 0),
        "active": True,
    }
    if adoption is not None:
        row["authorization_source"] = str(adoption.get("authorization_source") or adoption.get("provenance") or "")
        row["adoption_turn_identity"] = str(adoption.get("turn_identity") or "")
        if adoption.get("speaker_id") and str(adoption["speaker_id"]) != speaker_id:
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


def _supplied_overlap(text: str, exchange: Mapping[str, Any] | None) -> bool:
    if not isinstance(exchange, Mapping) or exchange.get("uncertain"):
        return False
    supplied = set(_tokens(str(exchange.get("supplied_text") or "")))
    return any(token in supplied for token in _tokens(text))


def _blob(row: Mapping[str, Any]) -> str:
    return " ".join(
        str(row.get(key) or "")
        for key in ("supplied_text", "subject", "player_text", "delivered_text", "requested_information")
    ).lower()


def _tokens(text: str) -> list[str]:
    found = []
    for tok in re.findall(r"[a-z']{3,}", str(text or "").lower()):
        tok = tok.strip("'")
        if tok.endswith("'s"):
            tok = tok[:-2]
        if len(tok) >= 3 and tok not in _STOP:
            found.append(tok)
    return found


def _best_exchange(text: str, rows: list[dict[str, Any]], npc_id: str = "") -> dict[str, Any] | str | None:
    pool = [row for row in rows if row.get("ownership") == "npc"]
    if npc_id:
        owned = [row for row in pool if str(row.get("speaker_id") or "") == npc_id]
        if owned:
            pool = owned
    if not pool:
        return None
    wanted = _WANTED.search(text)
    if wanted:
        needle = wanted.group(1).strip().lower()
        hits = [row for row in pool if needle and needle in _blob(row)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            return hits[-1]
    scored: list[tuple[int, dict[str, Any]]] = []
    tokens = _tokens(text)
    for row in pool:
        supplied = set(_tokens(str(row.get("supplied_text") or "") + " " + str(row.get("subject") or "")))
        mentioned = set(_tokens(str(row.get("player_text") or "") + " " + str(row.get("delivered_text") or "")))
        score = sum(2 for token in tokens if token in supplied) + sum(1 for token in tokens if token in mentioned)
        if str(row.get("requested_information") or "") == "surveillance" and _SURVEILLANCE.search(text):
            score += 3
        if row.get("uncertain") and not any(token in supplied for token in tokens):
            score = min(score, 1)
        scored.append((score, row))
    positive = [item for item in scored if item[0] > 0]
    if not positive:
        speakers = {str(row.get("speaker_id") or "") for row in pool}
        if len(speakers) > 1 and not npc_id:
            return "ambiguous"
        return pool[-1]
    positive.sort(key=lambda item: (item[0], 0 if item[1].get("uncertain") else 1))
    if (
        len(positive) >= 2
        and positive[-1][0] == positive[-2][0]
        and positive[-1][1].get("speaker_id") != positive[-2][1].get("speaker_id")
    ):
        return "ambiguous"
    return positive[-1][1]


def _npc_quote(name: str, exchange: Mapping[str, Any]) -> str:
    supplied = str(exchange.get("supplied_text") or "").strip()
    speaker = name or str(exchange.get("speaker_name") or "They")
    supplied = _core_statement(supplied)
    if exchange.get("uncertain") or _UNCERTAIN.search(supplied):
        inner = "I meant that I don't know."
    else:
        inner = f"I meant this: {supplied}"
        if inner[-1:] not in ".?!":
            inner += "."
    return f'{speaker} says, "{inner}"'


def _gm_quote(exchange: Mapping[str, Any]) -> str:
    name = str(exchange.get("speaker_name") or "They")
    supplied = str(exchange.get("supplied_text") or "").strip()
    supplied = _core_statement(supplied)
    if exchange.get("uncertain") or not supplied:
        return f"{name} said they could not answer that. They have not spoken again."
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
_AGAIN = re.compile(r"\b(?:the same|asked again|that one)\b", re.IGNORECASE)
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
) -> str:
    """Quote the delivered statement when this question asks what it meant."""
    text = " ".join(str(player_text or "").split())
    if not text or not (_MEANING.search(text) or _REPEAT.search(text)):
        return ""
    if (_GM.search(text) or _THIRD.search(text)) and not _YOU.search(text):
        return ""
    found = _best_exchange(text, delivered_exchanges(session), npc_id)
    if not isinstance(found, dict):
        return ""
    if npc_id and str(found.get("speaker_id") or "") not in {"", npc_id}:
        return ""
    return _npc_quote(npc_name or str(found.get("speaker_name") or "They"), found)


def find_reusable_commitment(session: Mapping[str, Any] | None, npc_id: str, player_text: str) -> str:
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
        subject = set(str(row.get("subject") or "").split())
        if tokens & subject or (tokens & pref and subject & pref) or (pref & set(_tokens(str(row.get("text") or "")))):
            text = str(row.get("text") or "").strip()
            if text:
                return text
    return ""


def continuity_directive(
    player_text: str,
    *,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return a grounding directive, or None to leave the existing decision path alone."""
    text = " ".join(str(player_text or "").split())
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
    if _WORLD.search(text) and not _REPEAT.search(text) and not _NEGOTIATION.search(text):
        return None
    if _pending_blocks(session, text):
        return None
    present = _present(scene, world)
    active = _active_id(session, present)
    if _names_other(text, present, active):
        return None
    rows = delivered_exchanges(session)
    found = _best_exchange(text, rows, active)
    if found == "ambiguous" and (_MEANING.search(text) or _REPEAT.search(text) or _DEICTIC.search(text)):
        return {
            "action": "clarify",
            "owner": "gm",
            "npc_id": "",
            "npc_name": "",
            "line": _ambiguous_line(rows),
            "reason": "ambiguous_delivered_reference",
        }
    exchange = found if isinstance(found, dict) else None
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

    gm_about_speech = bool(_GM.search(text) or (_THIRD.search(text) and not _YOU.search(text) and (_MEANING.search(text) or _EARLIER.search(text))))
    if gm_about_speech:
        if not exchange:
            return None
        return {
            "action": "answer",
            "owner": "gm",
            "npc_id": str(exchange.get("speaker_id") or ""),
            "npc_name": str(exchange.get("speaker_name") or ""),
            "line": _gm_quote(exchange),
            "reason": "gm_recall_of_npc_statement",
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
    if _REPEAT.search(text) and exchange:
        if speaker_present:
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
    if _EARLIER.search(text):
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
        if re.search(r"\b(?:what was that|that name)\b", text, re.IGNORECASE):
            chosen = exchange if isinstance(exchange, dict) and not exchange.get("uncertain") else None
            if chosen is None:
                certain = [
                    row for row in rows
                    if row.get("ownership") == "npc" and not row.get("uncertain")
                    and (not active or str(row.get("speaker_id") or "") == active)
                ]
                chosen = certain[-1] if certain else None
            if isinstance(chosen, dict):
                chosen_name = speaker_name or str(chosen.get("speaker_name") or "They")
                if speaker_present:
                    return {
                        "action": "answer",
                        "owner": "npc",
                        "npc_id": speaker_id or str(chosen.get("speaker_id") or ""),
                        "npc_name": chosen_name,
                        "line": _npc_quote(chosen_name, chosen),
                        "reason": "repeat_delivered_statement",
                    }
                return {
                    "action": "clarify",
                    "owner": "gm",
                    "npc_id": str(chosen.get("speaker_id") or ""),
                    "npc_name": str(chosen.get("speaker_name") or ""),
                    "line": _absent_line(chosen),
                    "reason": "absent_npc_reference",
                }
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
    if _DEICTIC.search(text) and _QUESTION.search(text) and speaker_present and exchange:
        if str(exchange.get("requested_information") or "") in {"opinion", "personal_state"}:
            return {
                "action": "answer",
                "owner": "npc",
                "npc_id": speaker_id,
                "npc_name": speaker_name,
                "line": _npc_quote(speaker_name, exchange),
                "reason": "repeat_delivered_statement",
            }
        return _ask()
    if _vocative(text, present) and speaker_present and _QUESTION.search(text) and not gm_about_speech:
        return _ask()
    if _AGAIN.search(text) and speaker_present and exchange and str(exchange.get("requested_information") or "") in {"opinion", "personal_state"}:
        return {
            "action": "answer",
            "owner": "npc",
            "npc_id": speaker_id,
            "npc_name": speaker_name,
            "line": _npc_quote(speaker_name, exchange),
            "reason": "repeat_delivered_statement",
        }
    if _supplied_overlap(text, exchange) and not re.search(r"\bwhich\b.+\bmean\b", text, re.IGNORECASE):
        if speaker_present:
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
