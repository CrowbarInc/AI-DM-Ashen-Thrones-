"""Host-owned expression contracts for bounded NPC wording.

The resolver still decides which facts, refusals, and uncertainties exist.
This module may only ask a provider to word an already authorized contract.
A candidate is delivered only after a deterministic check against that
contract. Prompt instructions are not the safety boundary. There is no
second speech store: adopted lines are sealed by the existing host-speech
path, and rejected lines stay on the turn audit.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any, Mapping

_OUTPUT_CAP = 80

_FUNCTION = frozenset(
    """
    a an the is are was were be been being am of to in on at for and or if it its
    that this these those who whom what which when where why how do does did not
    no nor so as with from into about than then there here they them their we our
    he she his her hers him have has had i me my mine you your yours just simply
    because when it's that's i'm i've don't cant can't cannot wont won't couldn't
    could would should
    """.split()
)
_FRAMING = frozenset({"called", "named", "known", "means", "mean", "call", "calls"})
_HEDGE_WORDS = frozenset(
    {"heard", "hearsay", "rumor", "rumour", "maybe", "perhaps", "sure", "might", "may", "think"}
)
_SYNONYM_GROUPS = (
    frozenset({"street", "road", "streets", "roads"}),
    frozenset({"beyond", "outside", "past", "beside"}),
    frozenset({"throughout", "during"}),
    frozenset({"watch", "watches", "watched", "watching"}),
    frozenset({"guard", "guards"}),
    frozenset({"gate", "gates"}),
    frozenset({"night", "nights"}),
    frozenset({"north", "northern"}),
    frozenset({"own", "owns", "owned", "owner"}),
    frozenset({"bell", "bells"}),
    frozenset({"harbor", "harbour"}),
    frozenset({"ferry", "ferries"}),
)
_SUBJECTIVE = frozenset(
    """
    find found easier easy little bit think thinking thought thoughts mind day
    winding down quiet quieter calm calmer restful soft softer slow slower pleasant
    like likes enjoy enjoying feel feels feeling settle settles settled still gentle
    personally light fades fade cool cooler breathe breath pace ease eases unwind
    unwinds myself simple nicer better rather peaceful peace
    """.split()
)
# Grammar that cannot name a person, place, or duty. It may accompany an
# authorized feeling. It cannot itself be the authorized explanation.
_NONREFERENTIAL = frozenset(
    "everything anything something nothing all things bit".split()
)
# Degree words modify an authorized feeling. They are not a new feeling and
# they are not a world claim. "more peaceful" is the same theme as "peaceful".
_DEGREE = frozenset("more less very quite really too much most".split())
_PROHIBITED_CHARACTERIZATION = re.compile(
    r"\b(?:guards?|gates?|patrols?|sentries|unattended|unguarded|unwatched|"
    r"captains?|corporals?|sergeants?|keepers?|warders?|millers?|"
    r"passwords?|secrets?|contacts?|promise[sd]?|rewards?|silver|quests?|"
    r"abandon(?:s|ed)?|schedules?|duties|duty|meets?|meeting|sunset)\b",
    re.IGNORECASE,
)
_PREFER_ANCHOR = re.compile(
    r"\bprefer(?:s)?\s+(?:the\s+|a\s+|an\s+)?([a-z']+)",
    re.IGNORECASE,
)
_REASON_CUE = frozenset(
    """
    easier easy think thinking thought thoughts quiet quieter calm calmer restful
    peaceful peace enjoy enjoying like likes feel feels feeling gentle soft softer
    slow slower pleasant unwind unwinds ease eases nicer better settle settles
    settled breathe breath
    """.split()
)
_PARAPHRASE = re.compile(
    r"\b(?:(?:simpler|plainer|plain|other)\s+words|in other words|another way|rephrase|paraphrase)\b",
    re.IGNORECASE,
)
_EXPLAIN = re.compile(
    r"\b(?:explain(?:\s+that)?|what (?:does|did|do) (?:that|this|it|you) mean)\b",
    re.IGNORECASE,
)
_REASON = re.compile(
    r"\b(?:why\b|what do you (?:like|enjoy)|what(?:'s| is) (?:nice|good|pleasant) about)\b",
    re.IGNORECASE,
)
_PERSONAL_PROP = re.compile(r"\b(?:prefer|morning|evening|wears on me)\b", re.IGNORECASE)
_REAL_HEDGE = re.compile(
    r"\b(?:i(?:'ve| have) heard|rumou?r|not sure|might\b|maybe|perhaps|i think)\b|\bmay\b",
    re.IGNORECASE,
)
_STRENGTHEN = re.compile(
    r"\b(?:definitely|certainly|confirmed|for certain|without doubt|proven|i know)\b",
    re.IGNORECASE,
)
_UNCERTAIN = re.compile(
    r"\b(?:do not know|don't know|not sure|no idea|couldn't tell|could not tell|"
    r"couldn't say|could not say|can't say|cannot say|haven't heard|have not heard|"
    r"never heard|never learned|nobody told me|no one told me)\b",
    re.IGNORECASE,
)
_REFUSAL = re.compile(
    r"\b(?:can't|cannot|couldn't|could not|won't|will not|unable to)\b.{0,48}\b(?:promise|reward|pay|offer)\b|"
    r"\b(?:no reward|nothing (?:has been|is) promised|i have nothing to promise)\b",
    re.IGNORECASE,
)
_POSITIVE_COMMIT = re.compile(
    r"\b(?:i will pay|i'll pay|i shall pay|i promise you a|i promise a|i owe you)\b",
    re.IGNORECASE,
)
_EXPLAIN_CLAUSE = re.compile(r"\b(?:because|since|but|although|however)\b", re.IGNORECASE)
_NUMBER = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"dozen|hundred|thousand|several)\b",
    re.IGNORECASE,
)
_INTERNAL = re.compile(
    r"speech authority|canonical world|expression contract|authorized fact",
    re.IGNORECASE,
)
_WORD_IS = re.compile(r"(?i)^word is,\s*")


def expression_generation_disabled() -> bool:
    """Pytest and explicit kills stay on the host sentence. Production leaves this unset."""
    from game.provider_budget import provider_calls_disabled

    flag = os.environ.get("ASHEN_DISABLE_EXPRESSION_GENERATION", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    return provider_calls_disabled()


_PLACE_HEAD = frozenset({"road", "roads", "street", "streets", "gate", "gates", "bell", "bells", "ferry", "ferries"})
_SPATIAL = frozenset({"beyond", "outside", "past", "beside"})


def _plain(text: str) -> str:
    """Fold typographic quotes so marker checks see the words the model spoke."""
    return (
        str(text or "")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", _plain(text).lower())


def _content(text: str, *, framing: bool) -> list[str]:
    skip = _FUNCTION | (_FRAMING if framing else frozenset())
    return [tok for tok in _tokens(text) if tok not in skip]


def _group(token: str) -> frozenset[str]:
    for group in _SYNONYM_GROUPS:
        if token in group:
            return group
    return frozenset({token})


def _covered(token: str, source_tokens: list[str]) -> bool:
    group = _group(token)
    return any(tok in group for tok in source_tokens)


def _strip_frame(text: str) -> tuple[str, bool]:
    raw = " ".join(str(text or "").split()).strip()
    if _WORD_IS.match(raw):
        return _WORD_IS.sub("", raw).strip(), True
    return raw, False


def _inner(line: str) -> str:
    spans = re.findall(r'["“]([^"”]+)', str(line or ""))
    if spans:
        return " ".join(spans[-1].split()).strip()
    return " ".join(str(line or "").split()).strip()


def spoken_text(candidate: str, speaker: str) -> str:
    """Drop a speaker label the model was not asked to invent."""
    text = " ".join(_plain(candidate).split()).strip()
    text = text.strip().strip('"').strip("“”").strip()
    if speaker:
        text = re.sub(
            rf"(?i)^{re.escape(speaker)}\s+(?:says|mutters|replies|answers),?\s*",
            "",
            text,
        ).strip()
    text = re.sub(
        r"(?i)^(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(?:says|mutters|replies),?\s*",
        "",
        text,
    ).strip()
    spans = re.findall(r'["“]([^"”]+)', text)
    if spans:
        text = spans[-1]
    return " ".join(text.split()).strip().strip('"').strip("“”")


def wrap_speech(speaker: str, spoken: str, template: str) -> str:
    verb = "mutters" if re.search(r"\bmutters,", template or "") else "says"
    line = spoken.strip().replace('"', "")
    if line and line[-1] not in ".!?":
        line += "."
    return f'{speaker} {verb}, "{line}"'


def _norm(text: str) -> str:
    return " ".join(_tokens(_strip_frame(text)[0]))


def _numbers_added(candidate: str, source: str) -> bool:
    source_nums = {m.group(0).lower() for m in _NUMBER.finditer(source or "")}
    return any(m.group(0).lower() not in source_nums for m in _NUMBER.finditer(candidate or ""))


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]


def _revision(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def proposition_identity(
    *,
    speaker_id: str = "",
    topic_id: str = "",
    text: str = "",
    explicit: str = "",
) -> str:
    """One id for a host proposition. Wording does not mint a second subject."""
    if str(explicit or "").strip():
        return str(explicit).strip()
    speaker = str(speaker_id or "").strip()
    topic = str(topic_id or "").strip()
    if topic:
        return f"topic:{speaker}:{topic}"
    body = _norm(text)
    if not body:
        return ""
    digest = hashlib.sha256(f"{speaker}|{body}".encode("utf-8")).hexdigest()[:12]
    return f"statement:{digest}"


def _preference_anchor(proposition: str) -> str:
    """The object of an established preference. The player's question is not authority."""
    match = _PREFER_ANCHOR.search(str(proposition or ""))
    if not match:
        return ""
    anchor = match.group(1).lower().strip("'")
    if anchor in _FUNCTION or anchor in {"it", "to", "that", "this"}:
        return ""
    return anchor


def _entity_identities(proposition: str, speaker_name: str, aliases: list[Any] | None) -> list[dict[str, Any]]:
    """Proper names taken from the authorized sentence, speaker, and declared aliases."""
    identities: list[dict[str, Any]] = []
    speaker = " ".join(str(speaker_name or "").split())
    if speaker:
        identities.append({"id": "speaker", "forms": [speaker], "aliases": []})
    seq = _sequence(proposition)
    for left, right in zip(seq, seq[1:]):
        if right not in _PLACE_HEAD or left in _SPATIAL or left in _group("beyond"):
            continue
        form = f"{left} {right}"
        identities.append({"id": "name:" + form, "forms": [form], "aliases": []})
    for raw in aliases or []:
        alias = " ".join(str(raw or "").split())
        if not alias:
            continue
        alias_seq = _sequence(alias)
        attached = False
        for ident in identities:
            if str(ident.get("id") or "").startswith("speaker"):
                continue
            form_seq = _sequence(str((ident.get("forms") or [""])[0]))
            if len(form_seq) < 2 or len(alias_seq) < 2 or form_seq[-1] != alias_seq[-1]:
                continue
            if alias_seq[-2] == form_seq[-2] or alias_seq[-2] in _group(form_seq[-2]):
                ident["aliases"].append(alias)
                attached = True
                break
        if not attached:
            identities.append({"id": "alias:" + alias.lower(), "forms": [alias], "aliases": []})
    return identities


def _public_contract(fields: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "speaker_id", "speaker_name", "speaker_identity", "addressee", "player_question",
        "operation", "authorized_source", "source_identity", "proposition_id",
        "authorized_propositions", "knowledge_posture", "epistemic_posture",
        "answer_sufficiency", "disclosure_posture", "permitted_expression_scope",
        "permitted_meaning", "prohibited_speech_acts", "prohibited_additions",
        "entity_identities", "prior_delivered_statement", "source_revision",
        "fallback_response", "canonical", "delivery_frame",
    )
    return {key: fields.get(key) for key in keys}


def _operation_for(
    player_text: str,
    *,
    proposition: str,
    knowledge_posture: str,
    requested: str,
    topic_text: str,
    forced: str = "",
) -> str:
    if forced:
        return forced
    if _PARAPHRASE.search(player_text) and proposition:
        return "faithful_paraphrase"
    if _EXPLAIN.search(player_text) and proposition and not _PERSONAL_PROP.search(proposition):
        return "simple_explanation"
    personal = bool(_PERSONAL_PROP.search(proposition)) or requested in {"opinion", "personal_state"}
    if _REASON.search(player_text) and personal and _PERSONAL_PROP.search(proposition):
        return "incidental_characterization"
    if _REASON.search(player_text) and proposition and not personal:
        return "simple_explanation"
    if topic_text:
        return ""
    # A withheld secret has a host refusal. Generated uncertainty would falsely
    # claim ignorance, and a reward-shaped refusal would change the subject.
    if requested == "hidden" or (knowledge_posture == "withheld" and requested != "promise"):
        return ""
    if requested == "promise":
        return "nonbinding_refusal"
    if knowledge_posture in {"unknown", "unestablished"} and requested not in {"opinion", "personal_state"}:
        return "uncertainty"
    return ""


def build_expression_contract(
    *,
    player_text: str,
    speaker_name: str,
    speaker_id: str,
    fallback_line: str,
    fallback_source: str,
    resolution: Mapping[str, Any] | None = None,
    forced_operation: str = "",
    proposition_id: str = "",
    entity_aliases: list[Any] | None = None,
) -> dict[str, Any] | None:
    """Build a contract from host authority only. Provider text is not an input."""
    social = {}
    if isinstance(resolution, Mapping):
        social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else {}
    authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else {}
    topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), Mapping) else {}
    topic_text = str(topic.get("text") or topic.get("clue_text") or "").strip()
    inner = _inner(fallback_line)
    if str(fallback_source).startswith("social.topic_revealed") and topic_text:
        proposition = topic_text
        disclosure = "authorized_topic"
    else:
        proposition = inner
        disclosure = "prior_delivered_speech" if "reuse" in fallback_source or "delivered" in fallback_source or "repeat" in fallback_source else "host_line"
    if re.search(r"\bwhich\b.+\bmean\b", inner, re.IGNORECASE):
        return None
    posture = str(authority.get("knowledge_posture") or "")
    requested = str(authority.get("requested_information") or "")
    if forced_operation == "nonbinding_refusal":
        proposition_for_op = ""
        posture = posture or "withheld"
        requested = requested or "promise"
    else:
        proposition_for_op = proposition
    operation = _operation_for(
        player_text,
        proposition=proposition_for_op,
        knowledge_posture=posture,
        requested=requested,
        topic_text=topic_text if not forced_operation else "",
        forced=forced_operation,
    )
    if not operation:
        return None
    body, framed = _strip_frame(proposition)
    if operation in {"uncertainty", "nonbinding_refusal"}:
        propositions: list[str] = []
        framed = False
        body = ""
    else:
        propositions = [body or proposition]
    anchor = _preference_anchor(proposition)
    if operation == "incidental_characterization" and not anchor:
        return None
    aliases = list(entity_aliases or [])
    if isinstance(topic.get("aliases"), list):
        aliases.extend(topic.get("aliases") or [])
    explicit_prop = str(proposition_id or social.get("proposition_id") or authority.get("proposition_id") or "")
    prop_id = proposition_identity(
        speaker_id=speaker_id,
        topic_id="" if explicit_prop else str(topic.get("id") or ""),
        text=" ".join(propositions),
        explicit=explicit_prop,
    )
    prohibited = [
        "new_consequential_fact",
        "new_obligation",
        "hidden_disclosure",
        "epistemic_strengthening",
        "unauthorized_commitment",
        "entity_substitution",
        "factual_strengthening",
        "security_information",
        "new_relationship",
        "secret",
    ]
    scope = {
        "faithful_paraphrase": "reword_authorized_proposition",
        "simple_explanation": "restate_authorized_proposition",
        "incidental_characterization": "nonconsequential_subjective_reason",
        "uncertainty": "state_lack_of_knowledge",
        "nonbinding_refusal": "refuse_without_commitment",
    }[operation]
    sufficiency = str(authority.get("answer_sufficiency") or "")
    if operation == "incidental_characterization":
        meaning: dict[str, Any] = {
            "operation": "explain_own_preference",
            "preference_anchor": anchor,
            "subject": "speaker_experience",
            "theme_id": "speaker_preference_ease",
            "licensed_by": "established_preference",
            "external_world": False,
            "consequential_commitment": False,
        }
    elif operation in {"uncertainty", "nonbinding_refusal"}:
        meaning = {"operation": scope, "new_facts": False, "commitment": False}
    else:
        meaning = {
            "operation": scope,
            "preserve_entities": True,
            "preserve_epistemic_posture": True,
            "answer_sufficiency": sufficiency or "directly_answers",
        }
    entities = _entity_identities(" ".join(propositions), speaker_name, aliases)
    revision_payload = {
        "speaker_id": speaker_id,
        "operation": operation,
        "propositions": propositions,
        "source": fallback_source,
        "proposition_id": prop_id,
        "meaning": meaning,
        "entities": entities,
        "posture": posture or ("withheld" if operation == "nonbinding_refusal" else "unknown" if operation == "uncertainty" else "delivered"),
        "question": " ".join(str(player_text or "").split()),
    }
    revision = _revision(revision_payload)
    epistemic = revision_payload["posture"]
    fields = {
        "speaker_id": speaker_id,
        "speaker_name": speaker_name,
        "speaker_identity": {"id": speaker_id, "name": speaker_name},
        "addressee": "player",
        "player_question": " ".join(str(player_text or "").split()),
        "operation": operation,
        "authorized_source": fallback_source,
        "source_identity": {"ref": fallback_source, "proposition_id": prop_id},
        "proposition_id": prop_id,
        "authorized_propositions": propositions,
        "knowledge_posture": epistemic,
        "epistemic_posture": epistemic,
        "answer_sufficiency": sufficiency or ("not_applicable" if operation in {"uncertainty", "nonbinding_refusal", "incidental_characterization"} else "directly_answers"),
        "disclosure_posture": disclosure if propositions else "none",
        "permitted_expression_scope": scope,
        "permitted_meaning": meaning,
        "prohibited_speech_acts": prohibited,
        "prohibited_additions": list(prohibited),
        "entity_identities": entities,
        "prior_delivered_statement": inner if disclosure == "prior_delivered_speech" else "",
        "source_revision": revision,
        "fallback_response": fallback_line,
        "canonical": False,
        "delivery_frame": "word_is" if framed else "",
    }
    contract = _public_contract(fields)
    contract["prompt"] = build_expression_prompt(contract)
    return contract


def build_expression_prompt(contract: Mapping[str, Any]) -> dict[str, str]:
    """Compact prompt. Authorized facts are listed apart from optional wording."""
    operation = str(contract.get("operation") or "")
    speaker = str(contract.get("speaker_name") or "The speaker")
    question = str(contract.get("player_question") or "")
    facts = [str(item) for item in (contract.get("authorized_propositions") or []) if str(item).strip()]
    fact_block = "\n".join(f"- {item}" for item in facts) if facts else "- (none)"
    frame = str(contract.get("delivery_frame") or "")
    if operation in {"faithful_paraphrase", "simple_explanation"}:
        guidance = (
            "OPTIONAL NONCANONICAL EXPRESSION: reword the authorized facts in one spoken sentence. "
            "You may use just, simply, called, named, or known. "
            "You may swap only these pairs: street/road, beyond/outside/past/beside, throughout/during, "
            "watch/watching, guard/guards. Keep every other fact. "
            "Do not add a place, person, time, number, cause, promise, or danger."
        )
        if frame == "word_is":
            guidance += " A leading 'Word is' is only a delivery frame and may be omitted."
        if any(_REAL_HEDGE.search(item) for item in facts):
            guidance += " Keep the uncertainty (heard, rumor, may, or not sure). Do not make it certain."
    elif operation == "incidental_characterization":
        anchor = str((contract.get("permitted_meaning") or {}).get("preference_anchor") or "that")
        guidance = (
            f"AUTHORIZED MEANING: you prefer {anchor}. "
            "OPTIONAL NONCANONICAL EXPRESSION: one personal reason, only about how that feels to you. "
            "You may say it feels easier, calmer, quieter, or more peaceful. Ordinary grammar is allowed. "
            "Do not mention other people, places, guards, schedules, secrets, payments, duties, or meetings."
        )
    elif operation == "uncertainty":
        guidance = (
            "AUTHORIZED FACTS are empty. OPTIONAL NONCANONICAL EXPRESSION: say you do not know the answer. "
            "You may repeat the player's subject only to name what is unknown. "
            "Do not invent a maker, owner, place, time, or cause. Do not use because, but, or since."
        )
    else:
        guidance = (
            "AUTHORIZED FACTS are empty. OPTIONAL NONCANONICAL EXPRESSION: refuse the request in one sentence. "
            "Say you cannot promise a reward. Do not promise payment, name an authority, or explain a rule. "
            "Do not use because, but, or since."
        )
    system = (
        f"You write one sentence spoken by {speaker} to the player. "
        "AUTHORIZED FACTS are the only consequential claims you may express. "
        "OPTIONAL NONCANONICAL EXPRESSION is wording only and cannot establish a new fact. "
        "Do not mention rules, contracts, or that you are a model. "
        "Reply with the spoken sentence only."
    )
    user = (
        f"Player question: {question}\n"
        f"Operation: {operation}\n"
        f"AUTHORIZED FACTS:\n{fact_block}\n"
        f"{guidance}"
    )
    return {"system": system, "user": user}


def _shared_reasons(spoken: str, contract: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    words = _tokens(spoken)
    if not spoken or len(words) < 2 or len(words) > 40:
        reasons.append("length")
    if len(_sentences(spoken)) > 2:
        reasons.append("too_many_sentences")
    if _INTERNAL.search(spoken):
        reasons.append("internal_voice")
    if _numbers_added(spoken, " ".join(contract.get("authorized_propositions") or [])):
        reasons.append("unsupported_number")
    return reasons


def _sequence(text: str) -> list[str]:
    body, _framed = _strip_frame(text)
    return [tok for tok in _tokens(body) if tok not in _FUNCTION and tok not in _FRAMING]


def _alias_pairs_for(left: str, right: str, identities: list[Any] | None) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for ident in identities or []:
        if not isinstance(ident, Mapping):
            continue
        forms = [str(item) for item in (ident.get("forms") or [])]
        canonical = any(tuple(_sequence(form)[-2:]) == (left, right) for form in forms if len(_sequence(form)) >= 2)
        if not canonical:
            continue
        for alias in ident.get("aliases") or []:
            seq = _sequence(str(alias))
            if len(seq) >= 2:
                found.append((seq[-2], seq[-1]))
    return found


def _name_reasons(source: str, candidate: str, identities: list[Any] | None = None) -> list[str]:
    """A modified proper name is not a free synonym. 'north road' may not become 'north street'."""
    src = _sequence(source)
    cand_seq = _sequence(candidate)
    cand_pairs = set(zip(cand_seq, cand_seq[1:]))
    for left, right in zip(src, src[1:]):
        if right not in _PLACE_HEAD:
            continue
        if left in _SPATIAL or left in _group("beyond"):
            if not any(prev in _group(left) and tok == right for prev, tok in cand_pairs):
                return ["name_changed"]
        elif (left, right) not in cand_pairs and not any(
            pair in cand_pairs for pair in _alias_pairs_for(left, right, identities)
        ):
            return ["name_changed"]
    return []


def _introduced_name_reasons(spoken: str, identities: list[Any] | None) -> list[str]:
    """A capitalized name that is not the speaker, the proposition, or a declared alias."""
    allowed: list[str] = []
    for ident in identities or []:
        if not isinstance(ident, Mapping):
            continue
        for form in list(ident.get("forms") or []) + list(ident.get("aliases") or []):
            allowed.append(str(form).lower())
    for span in re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", spoken or ""):
        low = span.lower()
        if any(low == form or low in form or form in low for form in allowed):
            continue
        return ["entity_substitution"]
    return []


def _faithful_reasons(spoken: str, proposition: str, identities: list[Any] | None = None) -> list[str]:
    reasons: list[str] = []
    body, _framed = _strip_frame(proposition)
    cand_body, _cand_frame = _strip_frame(spoken)
    if _STRENGTHEN.search(spoken) and not _STRENGTHEN.search(proposition):
        reasons.append("epistemic_strengthening")
    if _REAL_HEDGE.search(body) and not _REAL_HEDGE.search(spoken):
        reasons.append("epistemic_status_lost")
    source_all = _content(body, framing=True)
    source_tokens = [tok for tok in source_all if tok not in _HEDGE_WORDS]
    cand_all = _content(cand_body, framing=True)
    cand_tokens = [tok for tok in cand_all if tok not in _HEDGE_WORDS]
    for anchor in source_tokens:
        if not _covered(anchor, cand_tokens):
            reasons.append("missing_authorized_claim")
            break
    for tok in cand_all:
        if tok in _HEDGE_WORDS:
            if tok not in source_all and not _REAL_HEDGE.search(body):
                reasons.append("epistemic_status_changed")
                break
            continue
        if not _covered(tok, source_all):
            reasons.append("unsupported_addition")
            break
    if _norm(spoken) == _norm(proposition):
        reasons.append("verbatim_repetition")
    reasons.extend(_name_reasons(body, cand_body, identities))
    reasons.extend(_introduced_name_reasons(spoken, identities))
    return reasons


def _characterization_reasons(spoken: str, proposition: str, contract: Mapping[str, Any] | None = None) -> list[str]:
    """Check the host premise. A new feeling-word is not authority, and a safe clause cannot carry an unsafe one."""
    reasons: list[str] = []
    premise = {}
    if isinstance(contract, Mapping) and isinstance(contract.get("permitted_meaning"), Mapping):
        premise = contract["permitted_meaning"]
    anchor = str(premise.get("preference_anchor") or _preference_anchor(proposition))
    if premise.get("licensed_by") != "established_preference" or not anchor:
        return ["characterization_not_authorized"]
    prop_tokens = set(_content(proposition, framing=False))
    for match in _PROHIBITED_CHARACTERIZATION.finditer(spoken or ""):
        word = match.group(0).lower()
        stem = word[:-1] if word.endswith("s") else word
        if word not in prop_tokens and stem not in prop_tokens:
            reasons.append("prohibited_addition")
            break
    licensed = set(prop_tokens) | _SUBJECTIVE | _NONREFERENTIAL | _DEGREE
    if anchor:
        licensed.add(anchor)
    for tok in _content(spoken, framing=False):
        if _same_word(tok, licensed):
            continue
        reasons.append("unsupported_addition")
        break
    if "evening" in prop_tokens and "morning" in _tokens(spoken) and "morning" not in prop_tokens:
        reasons.append("contradicts_authorized_preference")
    if "morning" in prop_tokens and "evening" in _tokens(spoken) and "evening" not in prop_tokens:
        reasons.append("contradicts_authorized_preference")
    cues = set(_tokens(spoken)) & _REASON_CUE
    if not cues or "because" not in _tokens(spoken) and "when" not in _tokens(spoken):
        reasons.append("not_an_explanation")
    if _norm(spoken) == _norm(proposition):
        reasons.append("verbatim_repetition")
    if _POSITIVE_COMMIT.search(spoken):
        reasons.append("unauthorized_commitment")
    return reasons


def _same_word(token: str, allowed: set[str]) -> bool:
    if token in allowed:
        return True
    for suffix in ("ing", "ed", "es", "s"):
        if len(token) > len(suffix) + 2 and token.endswith(suffix) and token[: -len(suffix)] in allowed:
            return True
    return False


def _closure_reasons(spoken: str, question: str, lexicon: frozenset[str]) -> list[str]:
    allowed = set(_content(question, framing=False)) | lexicon
    for tok in _content(spoken, framing=False):
        if not _same_word(tok, allowed):
            return ["unsupported_addition"]
    return []


def _uncertainty_reasons(spoken: str, question: str) -> list[str]:
    reasons = _closure_reasons(
        spoken,
        question,
        frozenset(
            "know knew sure idea tell say said heard learned told recall remember answer exactly really anyone nobody never".split()
        ),
    )
    if not _UNCERTAIN.search(spoken):
        reasons.append("uncertainty_not_expressed")
    if _EXPLAIN_CLAUSE.search(spoken):
        reasons.append("unsupported_explanation")
    for sentence in _sentences(spoken):
        if not _UNCERTAIN.search(sentence):
            reasons.append("asserted_unknown")
            break
    if _STRENGTHEN.search(spoken):
        reasons.append("epistemic_strengthening")
    return reasons


def _refusal_reasons(spoken: str, question: str) -> list[str]:
    reasons = _closure_reasons(
        spoken,
        question,
        frozenset("promise reward pay offer able unable nothing commit commitment owe afraid sorry kind".split()),
    )
    if not _REFUSAL.search(spoken):
        reasons.append("refusal_not_expressed")
    if _POSITIVE_COMMIT.search(spoken):
        reasons.append("unauthorized_commitment")
    if _EXPLAIN_CLAUSE.search(spoken):
        reasons.append("unsupported_explanation")
    for sentence in _sentences(spoken):
        if not _REFUSAL.search(sentence):
            reasons.append("asserted_commitment")
            break
    return reasons


def validate_expression(spoken: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministic contract check. A second model is not consulted."""
    spoken = _plain(spoken)
    started = time.perf_counter()
    operation = str(contract.get("operation") or "")
    reasons = _shared_reasons(spoken, contract)
    proposition = " ".join(str(item) for item in (contract.get("authorized_propositions") or []))
    question = str(contract.get("player_question") or "")
    identities = contract.get("entity_identities") if isinstance(contract.get("entity_identities"), list) else None
    if operation in {"faithful_paraphrase", "simple_explanation"}:
        reasons.extend(_faithful_reasons(spoken, proposition, identities))
    elif operation == "incidental_characterization":
        reasons.extend(_characterization_reasons(spoken, proposition, contract))
    elif operation == "uncertainty":
        reasons.extend(_uncertainty_reasons(spoken, question))
    elif operation == "nonbinding_refusal":
        reasons.extend(_refusal_reasons(spoken, question))
    else:
        reasons.append("operation_disabled")
    # Stable unique reasons, first-seen order.
    unique: list[str] = []
    for reason in reasons:
        if reason not in unique:
            unique.append(reason)
    return {
        "adopt": not unique,
        "reasons": unique,
        "operation": operation,
        "validation_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def request_expression(contract: Mapping[str, Any]) -> dict[str, Any]:
    """One plain-text completion. No narration stack and no retry."""
    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from game.provider_budget import begin_request, finish_request

    prompt = contract.get("prompt") if isinstance(contract.get("prompt"), Mapping) else {}
    system = str(prompt.get("system") or "")
    user = str(prompt.get("user") or "")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    estimated = max(1, (len(system) + len(user)) // 4)
    refusal = begin_request(purpose="expression", estimated_input=estimated, max_output=_OUTPUT_CAP)
    if refusal:
        usage = finish_request(
            {
                "purpose": "expression",
                "sent": False,
                "model": DEFAULT_MODEL_NAME,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "refusal": refusal,
            }
        )
        return {"ok": False, "sent": False, "text": "", "reason": refusal, "usage": usage, "latency_ms": 0}
    from openai import OpenAI

    from game.gm import provider_timeout_seconds

    started = time.perf_counter()
    try:
        client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
        response = client.responses.create(
            model=DEFAULT_MODEL_NAME,
            input=messages,
            temperature=0.2,
            max_output_tokens=_OUTPUT_CAP,
        )
    except Exception as exc:  # noqa: BLE001 - one failure falls back; it is not retried
        latency = round((time.perf_counter() - started) * 1000, 3)
        finish_request(
            {
                "purpose": "expression",
                "sent": True,
                "model": DEFAULT_MODEL_NAME,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "latency_ms": latency,
                "error": type(exc).__name__,
            }
        )
        return {"ok": False, "sent": True, "text": "", "error": type(exc).__name__, "latency_ms": latency}
    latency = round((time.perf_counter() - started) * 1000, 3)
    usage_obj = getattr(response, "usage", None)
    incoming = getattr(usage_obj, "input_tokens", None) if usage_obj is not None else None
    outgoing = getattr(usage_obj, "output_tokens", None) if usage_obj is not None else None
    total = getattr(usage_obj, "total_tokens", None) if usage_obj is not None else None
    if incoming is None or outgoing is None or total is None:
        incoming = outgoing = total = None
    else:
        incoming, outgoing, total = int(incoming), int(outgoing), int(total)
    model = str(getattr(response, "model", "") or "")
    usage = finish_request(
        {
            "purpose": "expression",
            "sent": True,
            "configured_model": DEFAULT_MODEL_NAME,
            "model": model,
            "request_id": getattr(response, "id", None),
            "input_tokens": incoming,
            "output_tokens": outgoing,
            "total_tokens": total,
            "latency_ms": latency,
            "max_output_tokens": _OUTPUT_CAP,
            "model_mismatch": bool(model and not model.startswith(DEFAULT_MODEL_NAME)),
        }
    )
    return {
        "ok": True,
        "sent": True,
        "text": str(getattr(response, "output_text", "") or ""),
        "usage": usage,
        "latency_ms": latency,
        "model": model,
    }


def _attempt(contract: Mapping[str, Any], fallback_line: str) -> tuple[str, dict[str, Any]]:
    speaker = str(contract.get("speaker_name") or "")
    result = request_expression(contract)
    raw = str(result.get("text") or "")
    spoken = spoken_text(raw, speaker)
    verdict = validate_expression(spoken, contract) if spoken else {
        "adopt": False, "reasons": ["empty_candidate"], "operation": contract.get("operation"), "validation_ms": 0,
    }
    adopted = bool(verdict.get("adopt"))
    line = wrap_speech(speaker, spoken, fallback_line) if adopted else fallback_line
    audit = {
        "attempted": True,
        "calls": 1 if result.get("sent") else 0,
        "operation": contract.get("operation"),
        "revision": contract.get("source_revision"),
        "decision": "adopted" if adopted else "rejected",
        "reasons": list(verdict.get("reasons") or []),
        "candidate": spoken,
        "raw_candidate": raw[:500],
        "delivered_generated": adopted,
        "fallback_used": not adopted,
        "validation_ms": verdict.get("validation_ms"),
        "latency_ms": result.get("latency_ms"),
        "provider": {
            "sent": bool(result.get("sent")),
            "ok": bool(result.get("ok")),
            "model": result.get("model") or (result.get("usage") or {}).get("model"),
            "input_tokens": (result.get("usage") or {}).get("input_tokens"),
            "output_tokens": (result.get("usage") or {}).get("output_tokens"),
            "error": result.get("error") or result.get("reason") or "",
        },
        "contract": {key: value for key, value in contract.items() if key != "prompt"},
        "prompt": contract.get("prompt"),
    }
    return line, audit


def apply_expression(
    *,
    player_text: str,
    speaker_name: str,
    speaker_id: str,
    fallback_line: str,
    fallback_source: str,
    resolution: Mapping[str, Any] | None = None,
    forced_operation: str = "",
    proposition_id: str = "",
    entity_aliases: list[Any] | None = None,
) -> tuple[str, str, dict[str, Any]] | None:
    """Return a replacement line only when generation is enabled and the turn is eligible."""
    if expression_generation_disabled():
        return None
    contract = build_expression_contract(
        player_text=player_text,
        speaker_name=speaker_name,
        speaker_id=speaker_id,
        fallback_line=fallback_line,
        fallback_source=fallback_source,
        resolution=resolution,
        forced_operation=forced_operation,
        proposition_id=proposition_id,
        entity_aliases=entity_aliases,
    )
    if contract is None:
        return None
    line, audit = _attempt(contract, fallback_line)
    return line, fallback_source, audit


def attach_expression_audit(gm: dict[str, Any], audit: Mapping[str, Any] | None) -> None:
    if not isinstance(gm, dict) or not isinstance(audit, Mapping):
        return
    metadata = gm.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        return
    metadata["expression_generation"] = dict(audit)
    record = metadata.get("accepted_response")
    if not isinstance(record, dict):
        return
    record["expression_operation"] = audit.get("operation")
    record["expression_decision"] = audit.get("decision")
    record["expression_contract_revision"] = audit.get("revision")
    record["canonical"] = False
    contract = audit.get("contract") if isinstance(audit.get("contract"), Mapping) else {}
    if contract.get("proposition_id"):
        record["proposition_id"] = contract.get("proposition_id")
        record["authorized_proposition"] = " ".join(str(item) for item in (contract.get("authorized_propositions") or []))
        record["answer_sufficiency"] = contract.get("answer_sufficiency") or ""
    if audit.get("decision") == "adopted":
        record["candidate_disposition"] = "ADOPTED_GENERATED_EXPRESSION"
        record["expression_adoption"] = "ADOPTED_GENERATED_EXPRESSION"
    else:
        record["expression_adoption"] = "HOST_FALLBACK"
    from game.immutable_valid_response import seal_delivery_contract

    seal_delivery_contract(gm)


def maybe_reword_continuity_line(
    gm: dict[str, Any],
    decision: Any,
    *,
    player_text: str,
) -> tuple[str, dict[str, Any] | None]:
    """Paraphrase or refusal wording for a continuity answer, before the existing seal."""
    original = str(gm.get("player_facing_text") or "")
    if expression_generation_disabled():
        return original, None
    reason = str(getattr(decision, "reason", "") or "")
    owner = str(getattr(decision, "communication_owner", "") or "")
    if owner != "NPC":
        return original, None
    if reason == "repeat_delivered_statement" and (_PARAPHRASE.search(player_text) or _EXPLAIN.search(player_text)):
        forced = "simple_explanation" if _EXPLAIN.search(player_text) and not _PARAPHRASE.search(player_text) else "faithful_paraphrase"
    elif reason == "npc_request_declined":
        forced = "nonbinding_refusal"
    else:
        return original, None
    speaker_id = str(getattr(decision, "proposed_target", "") or "")
    speaker_name = next(
        (ref.split(":", 1)[1] for ref in (getattr(decision, "context_references", None) or []) if str(ref).startswith("name:")),
        "",
    )
    if not speaker_name:
        speaker_name = original.split(" ", 1)[0]
    inherited = ""
    for ref in getattr(decision, "context_references", None) or []:
        if str(ref).startswith("proposition_id="):
            inherited = str(ref).split("=", 1)[1]
    result = apply_expression(
        player_text=player_text,
        speaker_name=speaker_name,
        speaker_id=speaker_id,
        fallback_line=original,
        fallback_source="conversational_decision:" + reason,
        forced_operation=forced,
        proposition_id=inherited,
    )
    if result is None:
        return original, None
    line, _source, audit = result
    return line, audit
