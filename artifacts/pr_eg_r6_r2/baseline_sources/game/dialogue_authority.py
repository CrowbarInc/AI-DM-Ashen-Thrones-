"""Dialogue authority for ordinary NPC answers.

Separates what the world has established, what an NPC may say, and what
would become a new consequential fact. NPC speech recorded here is not
canonical world truth.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

POLICY_VERSION = "pr-eg-r6-r1-r1"
CATEGORY_WORLD = "world_source"
CATEGORY_HOST = "host_operation"
CATEGORY_BOUNDED = "bounded_expression"
CATEGORY_HISTORY = "verified_history"
_DENIED_HISTORY_SOURCES = frozenset({
    "dialogue_authority.disclosure_denied",
    "host_terminal_safety",
    "provider",
})

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
        r"\b(?:watch(?:es|ed|ing)?|guards?|sentries|under\s+watch|keep(?:s|ing)?\s+an\s+eye|patrol(?:led|s|ling)?|who\s+watches)\b",
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


def authorize_npc_disclosure(npc: Mapping[str, Any] | None, topic: Any) -> dict[str, Any]:
    """Resolve a proposition against its host-owned NPC source, on every route.

    Legacy authored rows without disclosure metadata mean public knowledge.
    Unrecognized policy/knowledge values fail closed; runtime revealed flags
    and provider-selected identifiers never override the authored policy.
    """
    person = npc if isinstance(npc, Mapping) else {}
    raw = person.get("topics") or person.get("knowledge") or []
    candidate = topic if isinstance(topic, Mapping) else {"text": str(topic or "")}
    text = str(candidate.get("text") or candidate.get("clue_text") or candidate.get("label") or "").strip()
    ident = str(candidate.get("id") or "")
    matches = []
    for item in raw if isinstance(raw, list) else []:
        row = item if isinstance(item, Mapping) else {"text": str(item)}
        source_text = str(row.get("text") or row.get("clue_text") or row.get("label") or "").strip()
        clue_matches = (not candidate.get("clue_text") or str(candidate["clue_text"]) in
                        {source_text, str(row.get("clue_text") or "")})
        if text and source_text == text and clue_matches and (not ident or not row.get("id") or str(row.get("id")) == ident):
            matches.append(row)
    source = matches[0] if len(matches) == 1 else {}
    policy = str(source.get("disclosure", "public")).lower().strip()
    knowledge = str(source.get("knowledge_status", "known")).lower().strip()
    known = knowledge in {"known", "npc_knowledge", "belief", "rumor"} and source.get("known") is not False
    permitted = bool(source and person.get("id") and known and policy in {"public", "allowed", "authorized"}
                     and not source.get("hidden") and not source.get("secret"))
    epistemic = str(source.get("epistemic") or source.get("epistemic_status") or "npc_knowledge")
    classification = "unknown" if not source or not known else "public" if permitted else "known_restricted"
    if permitted and epistemic.lower() in {"rumor", "belief", "false", "disputed", "claim"}:
        classification = "false_or_disputed"
    return {"speaker_id": str(person.get("id") or ""), "addressee": "player",
            "source_id": "npc:" + str(person.get("id") or "") + ":" + str(source.get("id") or ident),
            "classification": classification, "knowledge_status": knowledge if source else "unknown",
            "permission": permitted, "epistemic_status": epistemic, "operation": "disclose",
            "authorized_proposition": text if permitted else "", "canonical": False,
            "authorized_clue_text": str(source.get("clue_text") or text) if permitted else "",
            "authorized_clue_id": source.get("clue_id") or source.get("reveals_clue"),
            "provenance": "authored_npc_source", "validation": "authorized" if permitted else "source_or_policy_denied"}


def npc_source_permitted(npc: Mapping[str, Any] | None, topic: Any) -> bool:
    return authorize_npc_disclosure(npc, topic)["permission"]


_PROTECTED_DISCLOSURE = re.compile(
    r"\b(?:passwords?|passcodes?|classified|secrets?|ash\s+cowl|allegiance)\b",
    re.IGNORECASE,
)
_HOST_OPERATION_LINE = re.compile(
    r"\b(?:could(?:n't| not)|cannot|can't|do(?:n't| not) know|not sure|"
    r"which (?:earlier|statement|subject|part|question|person)|"
    r"i cannot share|couldn't tell|couldn't answer|won't say|will not say|"
    r"could you clarify|i understand)\b",
    re.IGNORECASE,
)
_BOUNDED_LINE = re.compile(
    r"\b(?:prefer(?:s|red)? the (?:morning|evening)|the watch wears on me)\b",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return " ".join(str(text or "").replace("\u2019", "'").lower().split()).rstrip(".")


def contains_protected_disclosure(text: str) -> bool:
    return bool(_PROTECTED_DISCLOSURE.search(str(text or "")))


def is_host_operation(text: str) -> bool:
    raw = str(text or "")
    if contains_protected_disclosure(raw) or _CONSEQUENTIAL_CLAIM.search(raw):
        return False
    return bool(_HOST_OPERATION_LINE.search(raw))


def is_bounded_expression(text: str) -> bool:
    raw = str(text or "")
    if contains_protected_disclosure(raw) or _CONSEQUENTIAL_CLAIM.search(raw):
        return False
    return bool(_BOUNDED_LINE.search(raw))


def proposition_covered_by_source(proposition: str, delivered: str, source_text: str) -> bool:
    """True when delivered wording restates this source and adds no protected fact."""
    source = _norm(source_text)
    if not source:
        return False
    prop = _norm(proposition)
    said = _norm(delivered)
    covered = prop == source or said == source or source in prop or source in said or bool(prop and prop in source)
    if not covered:
        return False
    extra = f"{prop.replace(source, ' ')} {said.replace(source, ' ')}"
    return not contains_protected_disclosure(extra)


def consequential_addition(line: str, covered: str = "") -> bool:
    """A second sentence cannot smuggle a consequential claim past a safe operation."""
    covered_norm = _norm(covered)
    for piece in re.split(r"[.!?]", str(line or "")):
        bit = piece.strip()
        if not bit:
            continue
        norm = _norm(bit)
        if covered_norm and (covered_norm in norm or norm in covered_norm):
            continue
        if contains_protected_disclosure(bit) or _CONSEQUENTIAL_CLAIM.search(bit):
            return True
    return False


def provenance_record(
    *,
    category: str,
    speaker_id: str,
    operation: str,
    proposition: str = "",
    source_id: str = "",
    epistemic_status: str = "none",
    validation: str,
    addressee: str = "player",
) -> dict[str, Any]:
    """Host-owned provenance. Provider text cannot mint this record."""
    body = "|".join([
        POLICY_VERSION, category, str(speaker_id or ""), addressee, operation,
        proposition, source_id, epistemic_status, validation,
    ])
    return {
        "authority_category": category,
        "speaker_id": str(speaker_id or ""),
        "addressee": addressee,
        "operation": operation,
        "authorized_proposition": proposition,
        "source_id": source_id,
        "epistemic_status": epistemic_status or "none",
        "validation": validation,
        "provenance_id": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16],
        "policy_version": POLICY_VERSION,
    }


def _npc_topics(npc: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    raw = (npc or {}).get("topics") or (npc or {}).get("knowledge") or []
    return [topic for topic in raw if isinstance(topic, Mapping)] if isinstance(raw, list) else []


def historical_disclosure_permitted(row: Mapping[str, Any], npc: Mapping[str, Any] | None) -> bool:
    """History is evidence of delivery, not an override of current source policy.

    A current NPC source wins. Protected wording and an explicit restricted
    source fail closed. Legacy host deliveries that are not protected remain
    recallable as delivered speech, not as new world-source grants.
    """
    if not isinstance(row, Mapping):
        return False
    source_name = str(row.get("authorization_source") or "")
    if source_name in _DENIED_HISTORY_SOURCES:
        return False
    proposition = str(row.get("authorized_proposition") or "")
    supplied = str(row.get("supplied_text") or "")
    delivered = str(row.get("delivered_text") or "")
    blob = "\n".join((proposition, supplied, delivered))
    topic_id = str(row.get("topic_id") or "")
    topics = _npc_topics(npc)
    same = [topic for topic in topics if topic_id and str(topic.get("id") or "") == topic_id]
    if same:
        return any(
            npc_source_permitted(npc, topic)
            and proposition_covered_by_source(
                proposition or supplied,
                delivered or supplied,
                str(topic.get("text") or topic.get("clue_text") or ""),
            )
            for topic in same
        )
    for topic in topics:
        text = str(topic.get("text") or topic.get("clue_text") or "")
        if not text or _norm(text) not in _norm(blob):
            continue
        if npc_source_permitted(npc, topic) and proposition_covered_by_source(proposition or supplied, delivered or supplied, text):
            return True
        return False
    if contains_protected_disclosure(blob):
        return False
    if row.get("response_integrity_digest") and source_name:
        return True
    if delivered.strip() and str(row.get("speaker_id") or "") and str(row.get("ownership") or "npc") in {"npc", "gm"}:
        return True
    spoken = proposition or supplied or delivered
    return is_host_operation(spoken) or is_bounded_expression(spoken)


def commitment_disclosure_permitted(row: Mapping[str, Any], npc: Mapping[str, Any] | None) -> bool:
    proposition = str(row.get("authorized_proposition") or "")
    text = str(row.get("text") or "")
    if proposition:
        if npc_source_permitted(npc, {"text": proposition, "id": row.get("topic_id") or ""}):
            return True
        if contains_protected_disclosure(proposition) or _CONSEQUENTIAL_CLAIM.search(proposition):
            return False
        return is_host_operation(proposition) or is_bounded_expression(proposition) or is_bounded_expression(text)
    if contains_protected_disclosure(text) or _CONSEQUENTIAL_CLAIM.search(text):
        return False
    if row.get("disclosure_scope") == "nonconsequential_host_speech":
        return True
    return is_host_operation(text) or is_bounded_expression(text)


def requested_information(player_text: str) -> str:
    text = str(player_text or "")
    from game.conversational_continuity import is_incidental_personal
    if is_incidental_personal(text):
        return "opinion"
    for name, pattern in sorted(_REQUESTS, key=lambda item: item[0] == "surveillance"):
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


_ABSENCE = re.compile(r"\b(?:unattended|unguarded|unwatched)\b", re.IGNORECASE)
_COVERAGE = re.compile(
    r"\b(?:watch(?:es|ed|ing)?|guards?|sentries|patrol(?:s|led|ling)?)\b",
    re.IGNORECASE,
)
_PARTIAL_STOP = frozenset(
    """
    ever left leave leaves when what does have been throughout during night nights
    watch watches watched watching guards guard sentries patrol with from that this
    them they your you about into onto
    """.split()
)


def _specific_overlap(question: str, fact: str) -> bool:
    left = {tok for tok in re.findall(r"[a-z]{4,}", str(question or "").lower()) if tok not in _PARTIAL_STOP}
    right = {tok for tok in re.findall(r"[a-z]{4,}", str(fact or "").lower()) if tok not in _PARTIAL_STOP}
    return bool(left & right)


def classify_answer_sufficiency(player_text: str, topic_text: str) -> str:
    """directly_answers, partially_informs, does_not_answer, or unknown.

    A relevant fact is not a complete answer. Coverage of a gate does not
    establish that the gate is never left unattended.
    """
    text = str(topic_text or "").strip()
    if not text:
        return "unknown"
    if _ABSENCE.search(str(player_text or "")):
        if not _specific_overlap(player_text, text):
            return "does_not_answer"
        if _ABSENCE.search(text):
            return "directly_answers"
        if _COVERAGE.search(text):
            return "partially_informs"
        return "does_not_answer"
    if topic_supports_requested_information(player_text, text):
        return "directly_answers"
    return "does_not_answer"


def _partial_answer_line(name: str, fact: str, player_text: str) -> str:
    asked = "unattended"
    for word in ("unguarded", "unwatched", "unattended"):
        if re.search(rf"\b{word}\b", player_text or "", re.IGNORECASE):
            asked = word
            break
    sentence = " ".join(str(fact or "").split()).rstrip(".")
    speaker = name.strip() or "They"
    return f'{speaker} says, "{sentence}. I couldn\'t say whether it is ever left {asked}."'


def _single_partial_topic(npc: Mapping[str, Any] | None, player_text: str) -> dict[str, str] | None:
    person = npc if isinstance(npc, Mapping) else {}
    raw = person.get("topics") or person.get("knowledge") or []
    if not isinstance(raw, list):
        return None
    found: list[dict[str, str]] = []
    for topic in raw:
        if not npc_source_permitted(person, topic):
            continue
        if isinstance(topic, Mapping):
            text = str(topic.get("text") or topic.get("clue_text") or topic.get("label") or "").strip()
            ident = str(topic.get("id") or "")
        else:
            text = str(topic or "").strip()
            ident = ""
        if text and classify_answer_sufficiency(player_text, text) == "partially_informs":
            found.append({"id": ident, "text": text})
    if len(found) != 1:
        return None
    return found[0]


def topic_supports_requested_information(player_text: str, topic_text: str) -> bool:
    """A subject mention is not an answer to a more specific request."""
    kind = requested_information(player_text)
    # A positive watch assertion does not establish the time of an absence.
    absence = re.compile(r"\b(?:unattended|unguarded|unwatched)\b", re.I)
    if absence.search(player_text) and not absence.search(topic_text):
        return False
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
    semantic_plan = payload.get("unified_semantic_plan")
    if isinstance(semantic_plan, Mapping) and semantic_plan.get("locked"):
        from game.unified_semantic_planning import authority_record_from_plan

        return authority_record_from_plan(player_text, npc=person, social=payload, plan=semantic_plan)
    name = str(payload.get("npc_name") or person.get("name") or "They")
    role = str(person.get("role") or person.get("occupation") or "")
    disposition = str(person.get("disposition") or person.get("attitude") or "")
    topic = payload.get("topic_revealed") if isinstance(payload.get("topic_revealed"), Mapping) else {}
    if topic and not npc_source_permitted(person, topic):
        denial = authorize_npc_disclosure(person, topic)
        return {"npc_id": str(payload.get("npc_id") or person.get("id") or ""),
                "npc_name": name, "improvisation_permitted": False,
                "knowledge_posture": "withheld", "narration_determined": True,
                "player_line": f'{name} says, "I cannot share that information."',
                "authorized_proposition": "", "proposition_id": "", "reuse_prior_speech": False,
                "disclosure_authorization": denial,
                "authorization_provenance": provenance_record(
                    category=CATEGORY_WORLD,
                    speaker_id=str(payload.get("npc_id") or person.get("id") or ""),
                    operation="disclose",
                    source_id=str(denial.get("source_id") or ""),
                    epistemic_status=str(denial.get("epistemic_status") or "unknown"),
                    validation="source_or_policy_denied",
                )}
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

    quoted = supplied_clarification(player_text, session, npc_id, name, npc=person)
    history_source = ""
    inherited_proposition = ""
    historical_proposition = ""
    if quoted:
        from game.conversational_continuity import _best_exchange, delivered_exchanges
        historical = _best_exchange(player_text, delivered_exchanges(session), npc_id)
        if isinstance(historical, dict):
            history_source = "delivered:" + str(historical.get("speaker_id") or "") + ":" + str(historical.get("turn") or 0) + ":" + str(historical.get("authorization_source") or historical.get("topic_id") or "statement")
            inherited_proposition = str(historical.get("proposition_id") or "")
            historical_proposition = str(historical.get("authorized_proposition") or historical.get("supplied_text") or "")
            if not inherited_proposition and historical.get("topic_id"):
                from game.expressive_dialogue import proposition_identity

                inherited_proposition = proposition_identity(
                    speaker_id=str(historical.get("speaker_id") or npc_id),
                    topic_id=str(historical.get("topic_id") or ""),
                )
    reused = "" if quoted else find_reusable_commitment(session, npc_id, player_text, npc=person)
    line = ""
    partial = None
    if not quoted and not reused and not topic_text:
        partial = _single_partial_topic(person, player_text)
    if quoted or reused:
        incidental = False
        determined = True
        line = quoted or reused
    if partial:
        incidental = False
        determined = True
        posture = "partial"
        line = _partial_answer_line(name, partial["text"], player_text)
    prior = [r for r in active_commitments(session, npc_id=npc_id, subject=subject)
             if commitment_disclosure_permitted(r, person)]
    if not prior and subject == "that":
        prior = [r for r in active_commitments(session, npc_id=npc_id)
                 if commitment_disclosure_permitted(r, person)][-1:]
    if determined and not line:
        if prior:
            line = str(prior[-1].get("text") or "")
        if not line:
            line = _player_line(name, posture, subject)
    from game.expressive_dialogue import proposition_identity

    resolved_proposition = inherited_proposition or proposition_identity(
        speaker_id=npc_id,
        topic_id=str((partial or {}).get("id") or topic.get("id") or ""),
        text=str((partial or {}).get("text") or topic_text or historical_proposition or ""),
    )
    authorized_proposition = str((partial or {}).get("text") or topic_text or historical_proposition or "")
    if quoted or reused:
        provenance_category = CATEGORY_HISTORY
        provenance_validation = "verified_history"
        provenance_operation = "recall"
    elif incidental:
        provenance_category = CATEGORY_BOUNDED
        provenance_validation = "bounded_expression"
        provenance_operation = "characterize"
    elif authorized_proposition and (topic_text or partial):
        provenance_category = CATEGORY_WORLD
        provenance_validation = "authorized"
        provenance_operation = "disclose"
    else:
        provenance_category = CATEGORY_HOST
        provenance_validation = "host_operation"
        provenance_operation = "converse"
    prohibited = [
        "consequential_world_fact",
        "hidden_disclosure",
        "mechanical_change",
        "new_obligation",
    ]
    if not incidental:
        prohibited.append("invented_answer")
    return {
        "topic_grounding": {
            "speaker_id": npc_id, "addressee": "player", "requested_subject": subject,
            "requested_information": kind, "reference": "delivered_speech" if quoted else "current_request",
            "candidate_sources": ["npc:" + npc_id + ":" + str(topic.get("id") or "")] if topic_text else [],
            "selected_source": (history_source if quoted else "npc:" + npc_id + ":" + str(topic.get("id") or "") if topic_text else ""),
            "ambiguous": "Which earlier remark" in quoted, "ownership": "npc",
            **dict(payload.get("topic_selection") or {}),
            **({"selected_source": history_source,
                "ambiguous": "Which earlier remark" in quoted} if quoted else {}),
        },
        "requested_information": kind,
        "subject": subject,
        "knowledge_posture": posture,
        "answer_relation": (
            "partially_informs" if partial
            else "sufficient" if posture == "established"
            else "partial" if posture == "partial"
            else "none"
        ),
        "answer_sufficiency": (
            "partially_informs" if partial
            else "directly_answers" if topic_text and topic_supports_requested_information(player_text, topic_text)
            else "unknown" if posture in {"unknown", "unestablished", "withheld"}
            else "does_not_answer"
        ),
        "proposition_id": resolved_proposition,
        "authorized_proposition": authorized_proposition,
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
        "authorization_provenance": provenance_record(
            category=provenance_category,
            speaker_id=npc_id,
            operation=provenance_operation,
            proposition=authorized_proposition,
            source_id=str((history_source if quoted else ("npc:" + npc_id + ":" + str(topic.get("id") or "")) if topic_text else "")),
            epistemic_status=str(topic.get("epistemic") or topic.get("epistemic_status") or "none"),
            validation=provenance_validation,
        ),
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


def select_host_speech(
    resolution: Mapping[str, Any] | None,
    *,
    player_text: str,
    session: Mapping[str, Any] | None = None,
) -> tuple[str, str] | None:
    """Project existing social authority for a resolved, nonmechanical question.

    Permission to speak is not permission to invent information. Generated
    paraphrases have no enforceable grant yet, so this lane uses host wording.
    The returned source is attached to the existing accepted_response object;
    it is not another persistent authority store.
    """
    if not isinstance(resolution, Mapping) or resolution.get("requires_check"):
        return None
    social = resolution.get("social")
    if not isinstance(social, Mapping) or social.get("target_resolved") is not True:
        return None
    from game.resolution_contract import contract_mapping_from_resolution

    contract = contract_mapping_from_resolution(resolution)
    if str(contract.get("operation") or "ask").lower() != "ask":
        return None
    construction = contract.get("construction") or {}
    if contract.get("ambiguous") or construction.get("authority_conflict"):
        return None
    if contract.get("interlocutor_id") and str(contract["interlocutor_id"]) != str(social.get("npc_id") or ""):
        return None
    metadata = resolution.get("metadata") or {}
    decision = metadata.get("gm_resolution_decision") or {}
    if (decision.get("executable_obligations") or {}).get("primary"):
        return None
    name = str(social.get("npc_name") or "").strip()
    npc_id = str(social.get("npc_id") or "").strip()
    if not name or not npc_id:
        return None
    semantic_plan = social.get("unified_semantic_plan")
    if isinstance(semantic_plan, Mapping) and semantic_plan.get("locked") and str(semantic_plan.get("host_line") or "").strip():
        return str(semantic_plan["host_line"]).strip(), "unified_semantic_plan." + str(semantic_plan.get("response_kind") or "response")
    record = social.get("dialogue_authority")
    if not isinstance(record, Mapping):
        record = build_dialogue_authority(player_text, social=social, session=session)
    if (record.get("disclosure_authorization") or {}).get("validation") == "source_or_policy_denied":
        return str(record["player_line"]), "dialogue_authority.disclosure_denied"
    # Explicit repeat/clarification binds the relevant delivered exchange even
    # when a resolver also carries a previously selected topic on this turn.
    line = str(record.get("player_line") or "").strip()
    if record.get("reuse_prior_speech") and line:
        return line, "dialogue_authority.reuse_prior_speech"
    grounding = social.get("topic_selection") or {}
    if grounding.get("ambiguous"):
        return f'{name} says, "Which subject do you mean?"', "social.topic_selection.ambiguous"
    topic = social.get("topic_revealed")
    if isinstance(topic, Mapping):
        text = str(topic.get("text") or topic.get("clue_text") or "").strip()
        if text:
            from game.social import format_authored_knowledge_realization_line

            return format_authored_knowledge_realization_line(dict(resolution), text), "social.topic_revealed:" + str(topic.get("id") or "")
    if line:
        return line, "dialogue_authority.player_line"
    from game.conversational_continuity import bounded_personal_line

    if record.get("improvisation_permitted") and record.get("requested_information") in {"opinion", "personal_state"}:
        return bounded_personal_line(name, npc_id, str(record["requested_information"])), "conversational_continuity.bounded_personal_line"
    return _player_line(name, str(record.get("knowledge_posture") or "unknown"), ""), "dialogue_authority.knowledge_posture"


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
    text = str(line or "")
    if not text.strip():
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
        "text": text,
        "canonical": False,
        "turn": int(turn or 0),
        "status": "active",
        "requested_information": str(record.get("requested_information") or ""),
        "authorized_proposition": str(record.get("authorized_proposition") or ""),
        "topic_id": str((social.get("topic_revealed") or {}).get("id") or ""),
        "disclosure_scope": "source_bound" if record.get("authorized_proposition") else "nonconsequential_host_speech",
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
