"""Structural interaction completion.

A response completes the player's interaction only when it carries the
outcome that interaction required. Speaker attribution, manner, and scene
atmosphere do not. Explicit current-turn discourse outranks an inherited
interlocutor. This module does not generate narration and does not add
scenario phrase rules.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

_QUOTE_RE = re.compile(r'["“]([^"”]{2,})["”]')
_ATTRIBUTION_VERBS = (
    r"(?:says|said|replies|replied|answers|answered|asks|asked|mutters|muttered|"
    r"whispers|whispered|adds|adding|continues|continued)"
)
_PRONOUN_ATTRIB_RE = re.compile(
    r"\b(?:he|she|they|the\s+[a-z]+(?:\s+[a-z]+){0,3})\s+" + _ATTRIBUTION_VERBS + r"\b",
    re.IGNORECASE,
)
_NAME_ATTRIB_RE = re.compile(
    r"\b[A-Z][\w']+(?:\s+[A-Z][\w']+){0,3}\s+" + _ATTRIBUTION_VERBS + r"\b"
)
_DELIVERY_RE = re.compile(
    r"\b(?:voice|tone|quietly|warily|hurried(?:ly)?|low|careful(?:ly)?|tight|"
    r"shrug(?:s|ging)?|eyes|gaze|glanc(?:e|es|ing)|flick(?:s|ing)?|"
    r"nod(?:s|ding)?|nervous(?:ly)?|cautious(?:ly)?|wary|weight)\b",
    re.IGNORECASE,
)
_OUTCOME_VERB_RE = re.compile(
    r"\b(?:bars?|barred|blocks?|blocked|refuses?|refused|denies?|denied|"
    r"shakes?|shook|turns?|turned away|steps aside|hands?|handed|opens?|"
    r"closes?|points?|pointed|waves?|waved|lets?|allowed|stops?|stopped)\b",
    re.IGNORECASE,
)
_PROPOSITION_RE = re.compile(
    r"\b(?:is|are|was|were|will|won't|cannot|can't|could|couldn't|must|"
    r"need|needs|costs?|means?|because|whether)\b",
    re.IGNORECASE,
)
_NONVERBAL_RE = re.compile(
    r"\bshakes?\b.{0,24}\bhead\b|\bbars?\b|\bblocks?\b|\bturns?\b.{0,16}\baway\b",
    re.IGNORECASE,
)
_PASSIVE_RE = re.compile(
    r"\b(?:as you watch|you watch the|watching the scene|you look on)\b",
    re.IGNORECASE,
)
_LOCATE_RE = re.compile(
    r"\b(?:find|locate|look for|go find|seek out|need to find|have to find)\b",
    re.IGNORECASE,
)
_ABSENT_RE = re.compile(
    r"\b(?:left|gone|walked away|no longer here|not here|departed)\b",
    re.IGNORECASE,
)
_STALL_RE = re.compile(r"\bnothing (?:further|else|more)\b", re.IGNORECASE)
_ADDRESS_RE = re.compile(
    r"\b(?:ask|asking|question|questioning|face|facing|approach(?:ing)?|address(?:ing)?|"
    r"speak(?:ing)?\s+(?:to|with)|talk(?:ing)?\s+(?:to|with)|turn to|stop|find|"
    r"walk(?:s|ing)? over to|step(?:s|ping)? up to|"
    r"walk(?:s|ing)? to|go over to|toward|towards)\s+"
    r"(?P<nominal>(?:the\s+|a\s+|an\s+|that\s+|this\s+|one\s+of\s+the\s+)?"
    r"(?:(?!\b(?:and|whether|if|what|how|where|when|why|about)\b)[a-z0-9']+\s*){1,8})",
    re.IGNORECASE,
)
_SPEECH_ADDRESS_RE = re.compile(
    r"\b(?:ask|asking|tell|warn|inform|address(?:ing)?|"
    r"speak(?:ing)?\s+(?:to|with)|talk(?:ing)?\s+(?:to|with)|turn to|question(?:ing)?\s+to)\s+"
    r"(?P<nominal>(?:the\s+|a\s+|an\s+|that\s+|this\s+|one\s+of\s+(?:the\s+)?)?"
    r"(?:(?!\b(?:and|whether|if|what|how|where|when|why|about)\b)[a-z0-9']+\s*){1,8})",
    re.IGNORECASE,
)
_TELL_RE = re.compile(
    r"\b(?:tell|warn|inform)\s+"
    r"(?P<nominal>(?:the\s+|a\s+|an\s+|that\s+|this\s+|one\s+of\s+(?:the\s+)?)?"
    r"(?:(?!\b(?:and|whether|if|what|how|where|when|why|about)\b)[a-z0-9']+\s*){1,8})",
    re.IGNORECASE,
)
_MEAN_RE = re.compile(
    r"\bi mean\s+(?:the\s+|a\s+|an\s+)?(?P<nominal>[a-z][^?.!,]{0,40})",
    re.IGNORECASE,
)
_VOCATIVE_RE = re.compile(
    r"^(?P<nominal>[A-Za-z]+(?:\s+[A-Za-z]+){0,2})\s*[,:]"
)
_NOT_A_VOCATIVE = frozenset({
    "instead", "actually", "well", "so", "then", "please", "wait", "now",
    "yes", "no", "okay", "ok", "never", "rather", "anyway", "still",
})
_INTERJECTION_RE = re.compile(
    r"^(?:fine|okay|ok|alright|all right|well|yes|no|hey|oh|ah|hmm|right|sure|wait|now|then)$",
    re.IGNORECASE,
)
_REJECT_RE = re.compile(
    r"\b(?:not asking|stop talking to|turn away from|step back from|done with|"
    r"leave|leaving|ignore|ignoring|forget)\s+"
    r"(?P<nominal>(?:the\s+|a\s+|an\s+)?[a-z][^?.!]{0,48})",
    re.IGNORECASE,
)
_REJECT_PRONOUN_RE = re.compile(
    r"\b(?:not asking|done with|leave|ignore|forget)\s+(?:him|her|them)\b"
    r"|\b(?:i am|i'm) not asking him\b",
    re.IGNORECASE,
)
_QUESTION_NOMINAL_RE = re.compile(
    r"^(?:what|whether|how|who|where|when|why|if|calmly|quietly|directly)\b",
    re.IGNORECASE,
)
_PURPOSE_PERSON_RE = re.compile(
    r"\bto\s+(?:see|ask|find|check|visit|speak)\s+(?:if|whether)\s+"
    r"(?P<nominal>(?:the|a|an)\s+[a-z]+(?:\s+[a-z]+){0,3})",
    re.IGNORECASE,
)
_COMPLEMENT_RE = re.compile(r",|\b(?:and|whether|if|about)\b", re.IGNORECASE)
_PRONOUN_NOMINAL_RE = re.compile(r"^(?:him|her|them|you|me)$", re.IGNORECASE)
_ROLE_LABEL_SKIP = frozenset(
    {"the", "a", "an", "that", "this", "one", "of", "passing", "nearby", "nearest", "some"}
)
_ASK_OP_RE = re.compile(r"\b(?:ask|inquire)\b", re.IGNORECASE)
_INSPECT_OP_RE = re.compile(r"\b(?:inspect|examine|read|study|check)\b", re.IGNORECASE)
_PERCEIVE_OP_RE = re.compile(
    r"\b(?:listen|smell)\b"
    r"|\b(?:look|looking|watch|watching)\s+(?:into|past|across|around|through)\b",
    re.IGNORECASE,
)
_ACT_OP_RE = re.compile(
    r"\bhand\s+(?:him|her|them|me|you|the|a|an|it)\b|\b(?:knock|push|pull)\b|\bopen\s+(?:the|a|an|it|that|this|up)\b",
    re.IGNORECASE,
)
_STOP = frozenset(
    {
        "the", "a", "an", "of", "on", "to", "and", "or", "at", "for", "with",
        "from", "into", "over", "that", "this", "nearest", "holding", "line",
    }
)


def _clean(text: str | None) -> str:
    return " ".join(str(text or "").split())


def _tokens(text: str | None) -> list[str]:
    return re.findall(r"[a-z0-9']+", str(text or "").lower())


def quoted_payload(text: str | None) -> bool:
    return bool(_QUOTE_RE.search(str(text or "")))


def attribution_shell(text: str | None) -> bool:
    """Speech attribution with no proposition, quote, or resolving action."""
    raw = _clean(text)
    if not raw or quoted_payload(raw):
        return False
    if not (_PRONOUN_ATTRIB_RE.search(raw) or _NAME_ATTRIB_RE.search(raw)):
        return False
    if _NONVERBAL_RE.search(raw):
        return False
    residual = _NAME_ATTRIB_RE.sub(" ", _PRONOUN_ATTRIB_RE.sub(" ", raw))
    residual = _DELIVERY_RE.sub(" ", residual)
    if _OUTCOME_VERB_RE.search(residual) or _PROPOSITION_RE.search(residual):
        return False
    return True


def nonverbal_resolution(text: str | None) -> bool:
    """A gesture or action that itself answers, refuses, or blocks the ask."""
    raw = _clean(text)
    if not raw or attribution_shell(raw):
        return False
    return bool(_NONVERBAL_RE.search(raw))


def passive_observation(text: str | None) -> bool:
    """Scene-watching narration standing in for an interaction."""
    raw = _clean(text)
    if not raw or quoted_payload(raw) or nonverbal_resolution(raw):
        return False
    if (_PRONOUN_ATTRIB_RE.search(raw) or _NAME_ATTRIB_RE.search(raw)) and not attribution_shell(raw):
        return False
    return bool(_PASSIVE_RE.search(raw))


def inspection_stall(text: str | None) -> bool:
    """The engine's generic closer-look close, with no further proposition."""
    raw = _clean(text)
    if not raw or not _STALL_RE.search(raw):
        return False
    residual = _STALL_RE.sub(" ", raw)
    leftover = [word for word in _tokens(residual) if len(word) > 3 and word not in _STOP]
    return len(leftover) < 4


def subject_repeats_player_opening(subject: str | None, raw_input: str | None) -> bool:
    """The fallback subject is the player's own opening, often cut mid-word.

    A later clause such as "where I can sleep" is a real topic and stays.
    """
    subject_norm = re.sub(r"[^a-z0-9]+", " ", str(subject or "").lower()).strip()
    raw_norm = re.sub(r"[^a-z0-9]+", " ", str(raw_input or "").lower()).strip()
    if len(subject_norm) < 40 or not raw_norm:
        return False
    return raw_norm.startswith(subject_norm) or subject_norm.startswith(raw_norm)


def player_utterance_embedded(fragment: str | None, raw_input: str | None) -> bool:
    """True when a long slice of the player's words is inside the candidate.

    A short overlap is not enough. The failure mode is a fallback that uses
    the utterance, or a truncated prefix of it, as the spoken content.
    """
    raw_tokens = _tokens(raw_input)
    fragment_tokens = _tokens(fragment)
    if len(raw_tokens) < 6 or len(fragment_tokens) < 6:
        return False
    raw_join = " ".join(raw_tokens)
    fragment_join = " ".join(fragment_tokens)
    if raw_join in fragment_join or fragment_join in raw_join:
        return True
    width = min(8, len(raw_tokens))
    for start in range(0, len(raw_tokens) - width + 1):
        window = " ".join(raw_tokens[start : start + width])
        if window in fragment_join:
            return True
    return False


def _labels(contract: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(contract, Mapping):
        return []
    found: list[str] = []
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    for value in (
        discourse.get("label"),
        discourse.get("id"),
        target.get("id_or_text"),
        contract.get("interlocutor_id"),
        contract.get("conversational_subject"),
    ):
        text = _clean(str(value or ""))
        if text and text not in found:
            found.append(text)
    return found


def recommends_locating_interlocutor(text: str | None, contract: Mapping[str, Any] | None) -> bool:
    """The line tells the player to go find the person already in the contract."""
    raw = _clean(text)
    if not raw or not _LOCATE_RE.search(raw):
        return False
    if _ABSENT_RE.search(raw):
        return False
    low = raw.lower()
    for label in _labels(contract):
        words = [word for word in _tokens(label) if len(word) > 3 and word not in _STOP]
        if words and all(word in low for word in words):
            return True
    return False


_SPEAKER_VERB = (
    r"(?:says|said|replies|replied|answers|answered|asks|asked|mutters|muttered|"
    r"whispers|whispered|shrugs|shrugged|grimaces|grimaced|narrows|narrowed|shakes|shook|"
    r"repeats|repeated|repeat)"
)
_SPEAKER_HEAD_SKIP = frozenset(
    {"eyes", "eye", "gaze", "voice", "hand", "hands", "head", "path", "door", "mouth"}
)
_SPEAKER_FUNCTION = frozenset(
    {
        "with", "for", "or", "and", "to", "of", "in", "on", "at", "from", "by", "that", "when",
        "their", "your", "its", "a", "an", "but", "those", "these", "are", "is", "was", "were",
        "often", "then", "not", "where", "just", "too", "more", "than", "into", "over",
    }
)
_SPEAKER_PRONOUNS = frozenset({"he", "she", "they", "them", "him", "her"})


def attributed_speaker_label(text: str | None) -> str:
    """The person who performs the communicative act, including a later pronoun."""
    raw = _clean(text)
    if not raw:
        return ""
    pattern = re.compile(
        rf"\b(?:the\s+)?([a-z]+(?:\s+[a-z]+){{0,3}})\s+{_SPEAKER_VERB}\b",
        re.IGNORECASE,
    )
    for match in pattern.finditer(raw):
        label = " ".join(match.group(1).split())
        words = [word.lower() for word in label.split()]
        head = words[-1] if words else ""
        if head in _SPEAKER_HEAD_SKIP or any(word in _SPEAKER_FUNCTION for word in words):
            continue
        if label.lower() in _SPEAKER_PRONOUNS or head in _SPEAKER_PRONOUNS:
            prior = [
                " ".join(item.group(1).split())
                for item in pattern.finditer(raw[: match.start()])
                if item.group(1).split()[-1].lower() not in _SPEAKER_PRONOUNS | _SPEAKER_HEAD_SKIP
            ]
            if prior:
                return prior[-1]
            continue
        return label
    return ""


def response_attributes_npc_speech(text: str | None) -> bool:
    """Quoted or verb-attributed speech. A head-shake without a quote is not speech."""
    raw = _clean(text)
    if not raw or not attributed_speaker_label(raw):
        return False
    if '"' in raw or "“" in raw:
        return True
    return bool(
        re.search(
            r"\b(?:says|said|replies|replied|answers|answered|asks|asked|mutters|whispers)\b",
            raw,
            re.IGNORECASE,
        )
    )


def _same_speaker(left: str, right: str) -> bool:
    a = [word for word in _tokens(left) if len(word) > 2]
    b = [word for word in _tokens(right) if len(word) > 2]
    if not a or not b:
        return True
    return bool(set(a) & set(b))


def social_payload(text: str | None) -> bool:
    raw = _clean(text)
    if not raw or attribution_shell(raw) or passive_observation(raw):
        return False
    if quoted_payload(raw) or nonverbal_resolution(raw):
        return True
    if _PROPOSITION_RE.search(raw) or _OUTCOME_VERB_RE.search(raw):
        return True
    if "?" in raw and re.search(r"\b(?:which|clarify|mean)\b", raw, re.IGNORECASE):
        return True
    return len(_tokens(raw)) >= 6


def structural_assessment(text: str | None, contract: Mapping[str, Any] | None) -> dict[str, Any]:
    """Whether this candidate completes the contract's operation."""
    raw = _clean(text)
    operation = str((contract or {}).get("operation") or "")
    shell = attribution_shell(raw)
    passive = passive_observation(raw)
    leak = player_utterance_embedded(raw, str((contract or {}).get("raw_input") or ""))
    locate = recommends_locating_interlocutor(raw, contract)
    payload = social_payload(raw)
    nonverbal = nonverbal_resolution(raw)
    stall = inspection_stall(raw)
    valid = True
    reasons: list[str] = []
    if operation == "ask":
        if not raw:
            pass
        elif shell:
            valid = False
            reasons.append("structurally_incomplete")
        elif passive:
            valid = False
            reasons.append("passive_observation_collapse")
        elif leak:
            valid = False
            reasons.append("player_text_leakage")
        elif locate:
            valid = False
            reasons.append("discourse_state_contradiction")
    elif operation in {"inspect", "perceive"} and not raw:
        valid = False
        reasons.append("interaction_not_completed")
    elif operation in {"act", "follow", "confirm"} and passive:
        valid = False
        reasons.append("passive_observation_collapse")
    return {
        "valid": valid,
        "reasons": reasons,
        "shell": shell,
        "passive": passive,
        "leak": leak,
        "locate": locate,
        "payload": payload,
        "nonverbal": nonverbal,
        "stall": stall,
        "speaker": attributed_speaker_label(raw),
    }


def ask_structural_block(text: str | None, contract: Mapping[str, Any] | None) -> str | None:
    if str((contract or {}).get("operation") or "") != "ask":
        return None
    report = structural_assessment(text, contract)
    if report["valid"]:
        return None
    return str((report["reasons"] or ["structurally_incomplete"])[0])


def generic_ask_completion(contract: Mapping[str, Any] | None) -> str:
    """A completed inability that does not invent a fact or quote the player."""
    label = ""
    for item in _labels(contract):
        if " " in item or item[:1].isupper():
            label = item
            break
    statement = "I cannot answer that from what is settled here."
    if label and " " in label:
        return f'{label} says, "{statement}"'
    return "No one here can answer that from what is settled here."


def _row_names(row: Mapping[str, Any]) -> list[str]:
    names = [str(row.get("label") or ""), str(row.get("id") or "").replace("_", " ")]
    aliases = row.get("aliases") or ()
    if isinstance(aliases, str):
        aliases = (aliases,)
    names.extend(str(alias) for alias in aliases)
    return [name for name in names if name.strip()]


_GENERIC_ROLE_TOKENS = frozenset({"guard", "soldier", "watchman", "sentry", "guardsman"})
_ADDRESS_MODIFIERS = frozenset(
    {
        "near", "nearby", "roster", "board", "gate", "line", "queue", "standing",
        "next", "beside", "current", "inside", "outside", "there",
    }
)


def _match_score(nominal: str, row: Mapping[str, Any]) -> int:
    words = {word for word in _tokens(nominal) if len(word) > 2 and word not in _STOP}
    if not words:
        return 0
    known = {
        token
        for name in _row_names(row)
        for token in _tokens(name)
        if len(token) > 2 and token not in _STOP
    }
    best = 0
    for name in _row_names(row):
        name_words = [word for word in _tokens(name) if len(word) > 2 and word not in _STOP]
        if not name_words:
            continue
        if all(word in words for word in name_words):
            # A generic role alias must not absorb a more specific unmatched title.
            if len(name_words) == 1 and name_words[0] in _GENERIC_ROLE_TOKENS:
                extra = [
                    word
                    for word in words
                    if word not in known and word not in _ADDRESS_MODIFIERS and len(word) > 3
                ]
                if extra:
                    continue
            best = max(best, len(name_words) + 2)
        elif any(word in words for word in name_words if len(word) > 4):
            generic = {"figure", "person", "woman", "man", "people", "someone", "somebody"}
            extra = [word for word in words if word not in name_words and word not in generic and len(word) > 3]
            if not extra:
                best = max(best, 1)
    return best


def _matches_row(nominal: str, row: Mapping[str, Any]) -> bool:
    return _match_score(nominal, row) > 0


def _unique_matches(nominal: str, referents: Sequence[Mapping[str, Any]], kind: str) -> list[Mapping[str, Any]]:
    scored: list[tuple[int, Mapping[str, Any]]] = []
    seen: set[str] = set()
    for row in referents:
        if not isinstance(row, Mapping) or str(row.get("type") or "") != kind:
            continue
        ident = str(row.get("id") or "")
        score = _match_score(nominal, row)
        if not ident or ident in seen or score <= 0:
            continue
        seen.add(ident)
        scored.append((score, row))
    if not scored:
        return []
    top = max(score for score, _row in scored)
    return [row for score, row in scored if score == top]


def _nominal_chunk(raw: str) -> str:
    chunk = re.split(r",|\b(?:not|and|who|which|holding)\b", raw, maxsplit=1, flags=re.IGNORECASE)[0]
    return _clean(chunk).strip(" \"'")


def _complement_cut(raw: str) -> str:
    """Keep a relative clause. Drop the question that follows the address."""
    return _clean(_COMPLEMENT_RE.split(str(raw or ""), maxsplit=1)[0]).strip(" \"'")


def _role_label(nominal: str) -> str:
    words = [word for word in _tokens(nominal) if word not in _ROLE_LABEL_SKIP]
    return " ".join(words)[:80]


def _active_interlocutor(focus: Mapping[str, Any] | None) -> tuple[str, str]:
    slot = focus.get("active_interlocutor") if isinstance(focus, Mapping) else None
    if not isinstance(slot, Mapping):
        return "", ""
    return _clean(str(slot.get("id") or "")), _clean(str(slot.get("label") or slot.get("id") or ""))


def _ordered_content(text: str | None) -> list[str]:
    return [word for word in _tokens(text) if len(word) > 2 and word not in _STOP]


def _object_score(nominal: str, row: Mapping[str, Any]) -> int:
    """Contiguous name match that ignores a short alias inside a different noun."""
    nominal_words = _ordered_content(nominal)
    if not nominal_words:
        return 0
    best = 0
    known = {word for name in _row_names(row) for word in _ordered_content(name)}
    for name in _row_names(row):
        name_words = _ordered_content(name)
        width = len(name_words)
        if not name_words:
            continue
        for start in range(0, len(nominal_words) - width + 1):
            if nominal_words[start : start + width] != name_words:
                continue
            if start:
                previous = nominal_words[start - 1]
                if previous not in known:
                    continue
            best = max(best, width + 2)
    return best


def _object_matches(nominal: str, referents: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    scored: list[tuple[int, Mapping[str, Any]]] = []
    seen: set[str] = set()
    for row in referents:
        if not isinstance(row, Mapping) or str(row.get("type") or "") != "object":
            continue
        ident = str(row.get("id") or "")
        score = _object_score(nominal, row)
        if not ident or ident in seen or score <= 0:
            continue
        seen.add(ident)
        scored.append((score, row))
    if not scored:
        return []
    top = max(score for score, _row in scored)
    return [row for score, row in scored if score == top]


def _select_object(text: str, catalog: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Bind the inspected object from the verb's object, not a buried alias."""
    spans: list[str] = []
    for pattern in (_INSPECT_OP_RE, _PERCEIVE_OP_RE):
        match = pattern.search(text)
        if match:
            spans.append(text[match.end() :])
    spans.extend(match.group(0) for match in re.finditer(r"\b(?:the|a|an)\s+[a-z]+(?:\s+[a-z]+){0,3}", text, re.I))
    best_row: Mapping[str, Any] | None = None
    best_score = 0
    tied = False
    for span in spans:
        rows = _object_matches(span, catalog)
        if len(rows) != 1:
            continue
        score = _object_score(span, rows[0])
        if score < 3:
            continue
        if score > best_score:
            best_row = rows[0]
            best_score = score
            tied = False
        elif score == best_score and str(rows[0].get("id") or "") != str((best_row or {}).get("id") or ""):
            tied = True
    if tied:
        return None
    return best_row


def unique_interlocutor(nominal: str | None, referents: Sequence[Mapping[str, Any]] | None) -> Mapping[str, Any] | None:
    hits = _unique_matches(str(nominal or ""), referents or (), "interlocutor")
    if len(hits) == 1:
        return hits[0]
    return None


def terminal_resolution_operation(text: str | None) -> str | None:
    """Resolution-bearing operation when one family is clearly last.

    Ask together with inspect or act stays unresolved. Movement verbs do not
    count as a second family, so approach-plus-ask stays an ask. A supporting
    listen or watch does not replace an explicit or approached social act.
    """
    raw = str(text or "")
    ask = bool(_ASK_OP_RE.search(raw))
    inspect = bool(_INSPECT_OP_RE.search(raw))
    perceive = bool(_PERCEIVE_OP_RE.search(raw))
    act = bool(_ACT_OP_RE.search(raw))
    from game.player_commitment import perception_is_supporting

    supporting = perception_is_supporting(raw)
    if ask and (inspect or perceive or act):
        if supporting and not inspect and not act:
            return "ask"
        return None
    if perceive and not inspect and not act:
        if supporting:
            return "ask"
        return "perceive"
    if inspect:
        return "inspect"
    if act:
        return "act"
    if ask:
        return "ask"
    return None


def addressed_person_nominal(text: str | None) -> str:
    """Nominal of a direct address, or empty when the utterance does not address anyone.

    Question complements are cut off. A mention of a person inside a GM question
    is not an address. ``tell`` and ``warn`` are included here because the
    existing address pattern does not own those verbs.
    """
    raw = _clean(text)
    if not raw:
        return ""
    for pattern in (_VOCATIVE_RE, _SPEECH_ADDRESS_RE, _TELL_RE):
        for match in pattern.finditer(raw):
            span = _complement_cut(match.group("nominal") or "")
            nominal = _nominal_chunk(span)
            if not nominal or _QUESTION_NOMINAL_RE.match(nominal) or _INTERJECTION_RE.match(nominal):
                continue
            if pattern is _VOCATIVE_RE and nominal.casefold() in _NOT_A_VOCATIVE:
                continue
            return nominal
    return ""


def explicit_discourse_binding(
    text: str | None,
    referents: Sequence[Mapping[str, Any]] | None,
    focus: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Current-turn address, rejection, and terminal operation.

    A pronoun follow-up with no new nominal does not suppress inheritance.
    """
    raw = _clean(text)
    catalog = [row for row in (referents or []) if isinstance(row, Mapping)]
    active_id, active_label = _active_interlocutor(focus)
    rejected = bool(_REJECT_PRONOUN_RE.search(raw))
    for match in _REJECT_RE.finditer(raw):
        nominal = _nominal_chunk(match.group("nominal") or "")
        if not nominal or _QUESTION_NOMINAL_RE.match(nominal):
            continue
        hits = _unique_matches(nominal, catalog, "interlocutor")
        if any(str(row.get("id") or "") == active_id for row in hits):
            rejected = True
        elif active_label and _matches_label(nominal, active_label):
            rejected = True
    selected: Mapping[str, Any] | None = None
    ambiguous = False
    addressed_unbound = False
    proposed_span = ""
    proposed_nominal = ""
    from game.incidental_entity import referential_person_nominal

    for pattern in (_VOCATIVE_RE, _MEAN_RE, _ADDRESS_RE):
        for match in pattern.finditer(raw):
            span = _complement_cut(match.group("nominal") or "")
            nominal = _nominal_chunk(span)
            if not nominal or _QUESTION_NOMINAL_RE.match(nominal) or _INTERJECTION_RE.match(nominal):
                continue
            hits = _unique_matches(nominal, catalog, "interlocutor")
            if len(hits) > 1:
                ambiguous = True
                proposed_span = span
                proposed_nominal = _role_label(nominal)
                continue
            if len(hits) == 1:
                chosen = hits[0]
                if rejected and str(chosen.get("id") or "") == active_id:
                    continue
                selected = chosen
                proposed_span = ""
                proposed_nominal = ""
                continue
            first_word = nominal.split()[0] if nominal.split() else ""
            if _PRONOUN_NOMINAL_RE.match(nominal) or _PRONOUN_NOMINAL_RE.match(first_word):
                continue
            person = referential_person_nominal(nominal) or referential_person_nominal(span)
            if person:
                if not _matches_label(person, active_label):
                    addressed_unbound = True
                    proposed_span = span
                    proposed_nominal = person
                continue
            if selected or proposed_nominal or _matches_label(nominal, active_label):
                continue
            addressed_unbound = True
            proposed_span = span
            proposed_nominal = nominal or span
    purpose = _PURPOSE_PERSON_RE.search(raw)
    if purpose and not selected:
        words = _clean(purpose.group("nominal") or "").split()
        purpose_span = ""
        purpose_person = ""
        for end in range(2, min(len(words), 5) + 1):
            chunk = " ".join(words[:end])
            person = referential_person_nominal(chunk)
            if person:
                purpose_span = chunk
                purpose_person = person
                break
        already_person = bool(proposed_nominal and referential_person_nominal(proposed_nominal))
        if purpose_person and not already_person and not _matches_label(purpose_person, active_label):
            addressed_unbound = True
            proposed_span = purpose_span
            proposed_nominal = purpose_person
    selected_object: Mapping[str, Any] | None = None
    terminal = terminal_resolution_operation(raw)
    if terminal in {"inspect", "perceive"}:
        selected_object = _select_object(raw, catalog)
    explicit_new = bool(
        ambiguous
        or addressed_unbound
        or (selected and str(selected.get("id") or "") != active_id)
    )
    suppress = bool(rejected or addressed_unbound or (selected and str(selected.get("id") or "") != active_id))
    if selected and str(selected.get("id") or "") == active_id and not rejected:
        suppress = False
        explicit_new = False
    return {
        "selected_interlocutor_id": str(selected.get("id") or "") if selected else "",
        "selected_interlocutor_label": str(selected.get("label") or selected.get("id") or "") if selected else "",
        "selected_object_id": str(selected_object.get("id") or "") if selected_object else "",
        "selected_object_label": str(selected_object.get("label") or "") if selected_object else "",
        "suppress_inherited_interlocutor": suppress and not ambiguous,
        "ambiguous_addressee": ambiguous,
        "terminal_operation": terminal,
        "proposed_nominal": proposed_nominal,
        "proposed_span": proposed_span,
        "explicit_new_interlocutor": explicit_new,
    }


def _matches_label(nominal: str, label: str) -> bool:
    if not nominal or not label:
        return False
    return _matches_row(nominal, {"label": label, "id": label, "aliases": []})


def degradation_reasons(
    before: str | None,
    after: str | None,
    contract: Mapping[str, Any] | None,
) -> list[str]:
    """Structural losses that equal satisfaction rank does not hide."""
    before_view = structural_assessment(before, contract)
    after_view = structural_assessment(after, contract)
    reasons: list[str] = []
    if before_view["valid"] and not after_view["valid"]:
        reasons.append("interaction_completion_loss")
    if before_view["payload"] and not after_view["payload"]:
        reasons.append("social_payload_loss")
    if before_view["speaker"] and after_view["speaker"] and not _same_speaker(before_view["speaker"], after_view["speaker"]):
        reasons.append("interlocutor_loss")
    if not before_view["passive"] and after_view["passive"]:
        reasons.append("operation_loss")
    if before_view["shell"] is False and after_view["shell"]:
        reasons.append("structural_incompleteness")
    if not before_view["leak"] and after_view["leak"]:
        reasons.append("player_text_leakage")
    if drops_inspection_detail(before, after, contract):
        reasons.append("inspection_detail_loss")
    return list(dict.fromkeys(reasons))


def drops_inspection_detail(before: str | None, after: str | None, contract: Mapping[str, Any] | None) -> bool:
    """A later inspection drops specific content and closes with a generic stall."""
    if str((contract or {}).get("operation") or "") not in {"inspect", "perceive"}:
        return False
    if inspection_stall(before):
        return False
    if not (inspection_stall(after) or _STALL_RE.search(str(after or ""))):
        return False
    before_words = {word for word in _tokens(before) if len(word) > 4}
    after_words = {word for word in _tokens(after) if len(word) > 4}
    return len(before_words - after_words) >= 4
