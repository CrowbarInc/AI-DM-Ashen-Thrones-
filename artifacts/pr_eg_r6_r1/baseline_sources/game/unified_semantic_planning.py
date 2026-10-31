"""Unified semantic planning for ordinary NPC information questions.

Routing boundary
----------------
When ``ASHEN_UNIFIED_SEMANTIC_PLANNING`` is on, this module owns one
interaction family only:

- explicit-addressee NPC information questions
- corrections of a previous question in that family
- natural follow-ups to a previous question in that family

The provider may propose conversational meaning. The host alone accepts
addressees, source identifiers, disclosure, relevance, and the response
plan. An accepted plan is locked. Legacy topic selectors, delivered-line
repetition, and authored-knowledge search must not replace its subject.

Combat, movement, inventory, bargaining, and every other family stay on
the existing pipeline. The gate defaults off.
"""

from __future__ import annotations

import json
import os
import re
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Mapping

from game.config import env_flag

PLAN_VERSION = "pr-eg-r6.1"
FLAG = "ASHEN_UNIFIED_SEMANTIC_PLANNING"
BINDING_KEY = "_unified_semantic_binding"
ACTS = frozenset({"information_question", "correction", "follow_up"})
AMBIGUITY = frozenset({"", "addressee", "subject", "proposition", "correction_target"})
COVERAGE = frozenset({"direct", "partial", "unrelated", "unknown"})
FORBIDDEN_FIELDS = frozenset({
    "canonical_fact",
    "state_update",
    "reward",
    "promise",
    "world_fact",
    "disclosure_granted",
    "execute_action",
    "mechanical_action",
    "time_advance",
})
_NAME_PREDICATES = frozenset({"name", "called", "named"})
_CAUSE_PREDICATES = frozenset({"cause", "reason", "source", "informant", "other"})
_CAUSE_MARKERS = re.compile(
    r"\b(?:because|therefore|told me|heard from|the reason|so that)\b",
    re.IGNORECASE,
)
_NAME_FACT = re.compile(r"\b(?:is called|are called|called the)\b", re.IGNORECASE)
_CORRECTION_RE = re.compile(
    r"(?:^no\b|^nope\b)|"
    r"\b(?:i meant|i mean|wasn'?t asking|not what i asked|let me rephrase|"
    r"i was asking|i was after|that(?:'s| is) not what|not her\b|not him\b)\b|"
    r"\bthat(?:'s| is) the \w+ again\b",
    re.IGNORECASE,
)
_FOLLOW_RE = re.compile(
    r"^\s*(?:why\??|how do you know\??|who told you\??|could you explain\??|"
    r"explain\??|and the other one\??|what about\b.+)\s*$",
    re.IGNORECASE,
)
_QUESTION_RE = re.compile(r"\b(?:who|what|when|where|why|how|which)\b|\?", re.IGNORECASE)
_IMPERATIVE_RE = re.compile(
    r"^\s*(?:i |we )?(?:attack|go|head|walk|move|take|open|give|cast|steal|search)\b",
    re.IGNORECASE,
)
_ACTION_REQUEST_RE = re.compile(
    r"\b(?:promise me|pay me|give me|grant me|attack|advance (?:the )?clock|open the gate)\b",
    re.IGNORECASE,
)
_STOP = frozenset(
    """
    who what when where why how which whom whose the a an of to do does did is are was were
    you your me my we our tell about please ask asking just from with that this those these
    and but for not yes no there here person someone anyone something anything could would
    should can will didn doesn wasn isn aren into onto over then than them they she her him
    his their said say mean meant again after before really actually
    """.split()
)
_PROPOSER: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None


def unified_semantic_planning_enabled() -> bool:
    """Reversible gate. Off preserves the existing conversational pipeline."""
    return env_flag(FLAG, default=False)


@contextmanager
def plan_proposer(fn: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None) -> Iterator[None]:
    """Test seam. Production leaves this unset and calls the provider."""
    global _PROPOSER
    previous = _PROPOSER
    _PROPOSER = fn
    try:
        yield
    finally:
        _PROPOSER = previous


def _clean(text: Any, limit: int = 400) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def _stem(token: str) -> str:
    text = str(token or "").lower()
    if len(text) > 4 and text.endswith("s") and not text.endswith("ss"):
        text = text[:-1]
    if len(text) > 5 and text.endswith("ing"):
        text = text[:-3]
    elif len(text) > 4 and text.endswith("ed"):
        text = text[:-2]
    return text


def _same(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    if len(left) >= 4 and len(right) >= 4 and (left.startswith(right) or right.startswith(left)):
        return True
    return False


def _tokens(text: str) -> list[str]:
    found: list[str] = []
    for raw in re.findall(r"[a-z']{3,}", str(text or "").lower()):
        token = raw.strip("'")
        if token.endswith("'s"):
            token = token[:-2]
        if token in _STOP or len(token) < 3:
            continue
        stem = _stem(token)
        if stem and stem not in found:
            found.append(stem)
    return found


def _covers(needles: list[str], hay: list[str]) -> int:
    count = 0
    for needle in needles:
        if any(_same(needle, item) for item in hay):
            count += 1
    return count


def _snake(text: str) -> str:
    parts = _tokens(text)[:6]
    return "_".join(parts) or "that"


def parse_relationship(relationship: str) -> tuple[list[str], list[str]]:
    """Split ``predicate(argument)`` into stemmed content tokens.

    The vocabulary is open. Unknown predicates stay as their own tokens.
    """
    raw = _clean(relationship, 160)
    match = re.fullmatch(r"([a-z0-9_]+)\(([^)]*)\)", raw.lower())
    if not match:
        return _tokens(raw), []
    predicate = [tok for tok in _tokens(match.group(1).replace("_", " ")) if tok not in {"of"}]
    argument = _tokens(match.group(2).replace("_", " "))
    return predicate, argument


def _scene_id(scene: Mapping[str, Any] | None) -> str:
    if not isinstance(scene, Mapping):
        return ""
    inner = scene.get("scene") if isinstance(scene.get("scene"), Mapping) else scene
    if not isinstance(inner, Mapping):
        return ""
    return str(inner.get("id") or "")


def _scene_summary(scene: Mapping[str, Any] | None) -> str:
    if not isinstance(scene, Mapping):
        return ""
    inner = scene.get("scene") if isinstance(scene.get("scene"), Mapping) else scene
    if not isinstance(inner, Mapping):
        return ""
    return _clean(inner.get("summary") or inner.get("location") or "", 240)


def present_participants(
    world: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Visible NPC roster only. Hidden facts are not participants."""
    sid = _scene_id(scene)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(npc_id: str, name: str, aliases: list[str]) -> None:
        ident = str(npc_id or "").strip()
        if not ident or ident in seen:
            return
        seen.add(ident)
        rows.append({
            "id": ident,
            "name": _clean(name, 80) or ident,
            "aliases": [_clean(alias, 80) for alias in aliases if _clean(alias, 80)][:6],
        })

    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    if isinstance(inner, Mapping):
        for row in inner.get("addressables") or []:
            if isinstance(row, Mapping) and str(row.get("kind") or "npc") in {"npc", "person"}:
                add(str(row.get("id") or ""), str(row.get("name") or row.get("label") or ""), list(row.get("aliases") or []))
    for npc in (world or {}).get("npcs") or []:
        if not isinstance(npc, Mapping):
            continue
        loc = str(npc.get("location") or npc.get("scene_id") or "")
        if sid and loc and loc != sid:
            continue
        add(str(npc.get("id") or ""), str(npc.get("name") or ""), list(npc.get("aliases") or []))
    return rows


def _labels(participant: Mapping[str, Any]) -> list[str]:
    labels = [str(participant.get("name") or "")]
    labels.extend(str(alias) for alias in participant.get("aliases") or [])
    return [label.strip() for label in labels if label.strip()]


def match_addressees(text: str, participants: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Unique or ambiguous name matches. Does not invent an NPC."""
    raw = str(text or "")
    hits: list[dict[str, Any]] = []
    for person in participants:
        for label in _labels(person):
            if re.search(rf"\b{re.escape(label)}\b", raw, re.IGNORECASE):
                hits.append(dict(person))
                break
    return hits


def prior_semantic_plan(session: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(session, Mapping):
        return {}
    ctx = session.get("conversational_context")
    rows = ctx.get("delivered_exchanges") if isinstance(ctx, Mapping) else None
    if not isinstance(rows, list):
        return {}
    for row in reversed(rows):
        if not isinstance(row, Mapping):
            continue
        plan = row.get("unified_semantic_plan")
        if isinstance(plan, Mapping) and (plan.get("requested_relationship") or plan.get("question_text")):
            return dict(plan)
    return {}


def _looks_like_information(text: str) -> bool:
    if _IMPERATIVE_RE.search(text) and not re.search(r"\b(?:who|what|when|where|why|how|which)\b", text, re.I):
        return False
    return bool(_QUESTION_RE.search(text))


def is_migrated_information_turn(
    text: str,
    *,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> bool:
    """True only for the migrated information-question family."""
    utterance = _clean(text)
    if not utterance:
        return False
    prior = prior_semantic_plan(session)
    participants = present_participants(world, scene)
    named = match_addressees(utterance, participants)
    if prior and (_CORRECTION_RE.search(utterance) or _FOLLOW_RE.search(utterance)):
        return True
    if not _looks_like_information(utterance):
        return False
    return len(named) >= 1


def migrated_turn_should_abstain_legacy(
    text: str,
    *,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> bool:
    """Legacy continuity must not answer a turn this owner has claimed."""
    return unified_semantic_planning_enabled() and is_migrated_information_turn(
        text, session=session, scene=scene, world=world,
    )


def _relationship_from_text(text: str, prior: Mapping[str, Any], act: str) -> tuple[str, str]:
    low = _clean(text).lower()
    if act == "follow_up":
        subject = str(prior.get("requested_subject") or "that")
        if re.search(r"\bwhy\b|could you explain|^explain\b", low):
            return f"cause_of({_snake(subject)})", subject
        if re.search(r"how do you know|who told you", low):
            return f"source_of({_snake(subject)})", subject
        if re.match(r"and the other one", low):
            return f"other_of({_snake(subject)})", subject
        about = re.search(r"what about\s+(.+)", low)
        if about:
            phrase = about.group(1).strip(" ?.!")
            return f"attribute_of({_snake(phrase)})", phrase
        return f"attribute_of({_snake(subject)})", subject
    body = re.sub(
        r"^.*?\b(?:i meant|i was asking(?: about)?|i was after|let me rephrase)\b[:,]?\s*",
        "",
        low,
        count=1,
        flags=re.IGNORECASE,
    )
    body = re.sub(r"^that(?:'s| is) the \w+ again[.,]?\s*", "", body, flags=re.IGNORECASE)
    agent = re.search(r"\b(?:the\s+)?([a-z]{3,})\s+(keeper|manager|runner|clerk)\b", body)
    if agent:
        role = _stem(agent.group(2))
        if role.endswith("er") and len(role) > 4:
            role = role[:-2]
        return f"{role}_of({_snake(agent.group(1))})", f"{agent.group(1)} {agent.group(2)}"
    named = re.search(r"\b(?:what|which)\s+(?:is|are)\s+(?:the\s+)?(.+?)\s+called\b", body)
    if named:
        return f"name_of({_snake(named.group(1))})", named.group(1).strip()
    if re.search(r"\b(?:called|name of|named)\b", body):
        phrase = re.sub(r"^.*\b(?:called|named|name of)\b", "", body).strip(" ?.!") or body
        phrase = re.sub(r"^(?:what|which)\s+(?:is|are)\s+(?:the\s+)?", "", phrase).strip(" ?.!")
        return f"name_of({_snake(phrase or body)})", phrase or body
    who = re.search(r"\b(?:who|which person|which one)\s+([a-z]+)\s+(.+)", body)
    if who:
        obj = who.group(2).strip(" ?.")
        return f"{_stem(who.group(1))}_of({_snake(obj)})", obj
    if re.search(r"\bwhen\b", body):
        phrase = re.sub(r"^.*\bwhen\b", "", body).strip(" ?.")
        return f"time_of({_snake(phrase)})", phrase or "that"
    if re.search(r"\bwhere\b", body):
        phrase = re.sub(r"^.*\bwhere\b", "", body).strip(" ?.")
        return f"location_of({_snake(phrase)})", phrase or "that"
    phrase = re.sub(r"^(?:what|which)\s+(?:is|are|did|do|does)\s+", "", body).strip(" ?.")
    return f"attribute_of({_snake(phrase or body)})", phrase or body


def deterministic_semantic_proposal(context: Mapping[str, Any]) -> dict[str, Any]:
    """General extractor used when tests supply it. Not a closed question list."""
    text = _clean(context.get("utterance"))
    participants = [row for row in context.get("participants") or [] if isinstance(row, Mapping)]
    prior = context.get("prior_plan") if isinstance(context.get("prior_plan"), Mapping) else {}
    named = match_addressees(text, participants)
    act = "information_question"
    correction = False
    if prior and _CORRECTION_RE.search(text):
        act = "correction"
        correction = True
    elif prior and _FOLLOW_RE.search(text):
        act = "follow_up"
    relationship, subject = _relationship_from_text(text, prior, act)
    ambiguity = ""
    if len(named) > 1:
        ambiguity = "addressee"
    chosen = named[0] if len(named) == 1 else {}
    if not chosen and act in {"correction", "follow_up"} and prior.get("addressee_id"):
        chosen = {"id": prior.get("addressee_id"), "name": prior.get("addressee_id")}
    return {
        "plan_version": PLAN_VERSION,
        "conversational_act": act,
        "addressee_reference": str(chosen.get("name") or ""),
        "addressee_id": str(chosen.get("id") or ""),
        "requested_subject": _clean(subject, 120),
        "requested_relationship": relationship,
        "question_text": text,
        "correction_of_prior_question": correction,
        "correction_target": _clean(prior.get("question_text"), 240) if correction else "",
        "referenced_prior_proposition": _clean(prior.get("requested_relationship"), 160) if act != "information_question" else "",
        "candidate_source_ids": [],
        "proposed_coverage": [],
        "ambiguity_type": ambiguity,
        "clarification_needed": bool(ambiguity),
        "interpretation_confidence": 0.74 if relationship else 0.2,
    }


def _proposal_schema() -> dict[str, Any]:
    coverage_row = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "source_id": {"type": "string"},
            "coverage": {"type": "string", "enum": ["direct", "partial", "unrelated", "unknown"]},
        },
        "required": ["source_id", "coverage"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "plan_version": {"type": "string", "enum": [PLAN_VERSION]},
            "conversational_act": {"type": "string", "enum": sorted(ACTS)},
            "addressee_reference": {"type": "string"},
            "addressee_id": {"type": "string"},
            "requested_subject": {"type": "string"},
            "requested_relationship": {"type": "string"},
            "question_text": {"type": "string"},
            "correction_of_prior_question": {"type": "boolean"},
            "correction_target": {"type": "string"},
            "referenced_prior_proposition": {"type": "string"},
            "candidate_source_ids": {"type": "array", "items": {"type": "string"}},
            "proposed_coverage": {"type": "array", "items": coverage_row},
            "ambiguity_type": {"type": "string", "enum": sorted(AMBIGUITY)},
            "clarification_needed": {"type": "boolean"},
            "interpretation_confidence": {"type": "number"},
        },
        "required": [
            "plan_version", "conversational_act", "addressee_reference", "addressee_id",
            "requested_subject", "requested_relationship", "question_text",
            "correction_of_prior_question", "correction_target", "referenced_prior_proposition",
            "candidate_source_ids", "proposed_coverage", "ambiguity_type",
            "clarification_needed", "interpretation_confidence",
        ],
    }


def _provider_context(context: Mapping[str, Any]) -> dict[str, Any]:
    """Compact public context. Hidden world facts are not included."""
    history = []
    for row in list(context.get("recent_dialogue") or [])[-4:]:
        if not isinstance(row, Mapping):
            continue
        history.append({
            "speaker": _clean(row.get("speaker_name"), 80),
            "player": _clean(row.get("player_text"), 240),
            "delivered": _clean(row.get("delivered_text"), 240),
            "relationship": _clean(row.get("requested_relationship"), 120),
        })
    candidates = []
    for row in list(context.get("candidates") or [])[:12]:
        if not isinstance(row, Mapping):
            continue
        candidates.append({
            "id": _clean(row.get("id"), 80),
            "text": _clean(row.get("text"), 180),
        })
    return {
        "utterance": _clean(context.get("utterance")),
        "participants": [
            {"id": row.get("id"), "name": row.get("name"), "aliases": list(row.get("aliases") or [])[:4]}
            for row in list(context.get("participants") or [])[:8]
            if isinstance(row, Mapping)
        ],
        "scene": _clean(context.get("scene_summary"), 240),
        "recent_dialogue": history,
        "prior_question": _clean((context.get("prior_plan") or {}).get("question_text") if isinstance(context.get("prior_plan"), Mapping) else "", 240),
        "permitted_sources": candidates,
    }


def _invoke_provider(payload: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    from openai import OpenAI

    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from game.gm import provider_timeout_seconds
    from game.provider_budget import begin_request, finish_request

    messages = [
        {
            "role": "system",
            "content": (
                "Propose the conversational meaning of one NPC information question. "
                "Return only the schema. You do not decide canonical truth, disclosure, "
                "mechanical success, or commitments. Use participant ids only from the list. "
                "Use source ids only from permitted_sources. Leave source ids empty if none answer "
                "the requested relationship. requested_relationship must be predicate(argument) in snake case, "
                "with the argument also copied to requested_subject. A shared word is not an answer."
            ),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    blob = json.dumps(messages, ensure_ascii=False)
    estimated = max(1, len(blob) // 4)
    refusal = begin_request(purpose="semantic_plan", estimated_input=estimated, max_output=350)
    if refusal:
        usage = finish_request({
            "purpose": "semantic_plan", "sent": False, "model": DEFAULT_MODEL_NAME,
            "input_tokens": None, "output_tokens": None, "total_tokens": None, "refusal": refusal,
        })
        raise RuntimeError(refusal or "provider_budget")
    started = time.perf_counter()
    client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
    response = client.responses.create(
        model=DEFAULT_MODEL_NAME,
        input=messages,
        temperature=0,
        max_output_tokens=350,
        text={
            "format": {
                "type": "json_schema",
                "name": "unified_semantic_plan",
                "strict": True,
                "schema": _proposal_schema(),
            }
        },
    )
    usage_obj = getattr(response, "usage", None)
    incoming = getattr(usage_obj, "input_tokens", None) if usage_obj is not None else None
    outgoing = getattr(usage_obj, "output_tokens", None) if usage_obj is not None else None
    total = getattr(usage_obj, "total_tokens", None) if usage_obj is not None else None
    record = finish_request({
        "purpose": "semantic_plan",
        "sent": True,
        "configured_model": DEFAULT_MODEL_NAME,
        "model": str(getattr(response, "model", "") or ""),
        "request_id": getattr(response, "id", None),
        "input_tokens": int(incoming) if incoming is not None else None,
        "output_tokens": int(outgoing) if outgoing is not None else None,
        "total_tokens": int(total) if total is not None else None,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
    })
    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("empty semantic plan")
    return str(text), record


def propose_semantic_plan(context: Mapping[str, Any]) -> dict[str, Any]:
    """One compact proposal. Malformed output is a failure, not a fact."""
    if _PROPOSER is not None:
        proposed = _PROPOSER(context)
        if isinstance(proposed, Mapping) and proposed.get("status"):
            return dict(proposed)
        return {"status": "proposed", "plan": dict(proposed or {}), "api_calls": 0, "usage": {}}
    from game.provider_budget import provider_calls_disabled

    if provider_calls_disabled() or os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION", "").strip().lower() in {"1", "true", "yes", "on"}:
        return {"status": "failed", "reason": "provider_disabled", "api_calls": 0, "usage": {}}
    try:
        raw, usage = _invoke_provider(_provider_context(context))
    except Exception as exc:  # noqa: BLE001 - transport failure fails closed
        return {"status": "failed", "reason": type(exc).__name__, "api_calls": 1, "usage": {}, "error": str(exc)[:200]}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"status": "failed", "reason": "malformed_json", "api_calls": 1, "usage": usage}
    if not isinstance(payload, dict):
        return {"status": "failed", "reason": "malformed_plan", "api_calls": 1, "usage": usage}
    return {"status": "proposed", "plan": payload, "api_calls": 1, "usage": usage}


def validate_plan_schema(payload: Mapping[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    """Accept a bounded proposal. Reject invented authority fields."""
    if not isinstance(payload, Mapping):
        return None, "not_an_object"
    if any(key in payload for key in FORBIDDEN_FIELDS):
        return None, "unsupported_authority_field"
    act = str(payload.get("conversational_act") or "")
    if act not in ACTS:
        return None, "unsupported_act"
    relationship = re.sub(r"\s+", "_", _clean(payload.get("requested_relationship"), 160).lower()).strip("_")
    if not re.fullmatch(r"[a-z0-9_]+\([^)]*\)", relationship):
        parts = [re.sub(r"[^a-z0-9_]+", "", part) for part in re.split(r"[\s_]+", relationship)]
        parts = [part for part in parts if part]
        argument = re.sub(r"[^a-z0-9_]+", "", re.sub(r"\s+", "_", _clean(payload.get("requested_subject"), 120).lower()))
        named = [part for part in parts if part.rstrip("s") in _NAME_PREDICATES or part in _NAME_PREDICATES]
        predicate = named[0] if named else (parts[0] if parts else "")
        if predicate and not argument:
            argument = "_".join(part for part in parts if part != predicate)
        relationship = f"{predicate}({argument})" if predicate else ""
    if not re.fullmatch(r"[a-z0-9_]+\([^)]*\)", relationship):
        return None, "invalid_relationship"
    ambiguity = str(payload.get("ambiguity_type") or "")
    if ambiguity not in AMBIGUITY:
        return None, "invalid_ambiguity"
    try:
        confidence = float(payload.get("interpretation_confidence"))
    except (TypeError, ValueError):
        return None, "invalid_confidence"
    confidence = min(1.0, max(0.0, confidence))
    source_ids = []
    for item in list(payload.get("candidate_source_ids") or [])[:8]:
        ident = _clean(item, 80)
        if ident and ident not in source_ids:
            source_ids.append(ident)
    coverage = []
    for row in list(payload.get("proposed_coverage") or [])[:8]:
        if not isinstance(row, Mapping):
            continue
        kind = str(row.get("coverage") or "")
        ident = _clean(row.get("source_id"), 80)
        if ident and kind in COVERAGE:
            coverage.append({"source_id": ident, "coverage": kind})
    return {
        "plan_version": PLAN_VERSION,
        "conversational_act": act,
        "addressee_reference": _clean(payload.get("addressee_reference"), 80),
        "addressee_id": _clean(payload.get("addressee_id"), 80),
        "requested_subject": _clean(payload.get("requested_subject"), 120),
        "requested_relationship": relationship,
        "question_text": _clean(payload.get("question_text"), 400),
        "correction_of_prior_question": bool(payload.get("correction_of_prior_question")),
        "correction_target": _clean(payload.get("correction_target"), 240),
        "referenced_prior_proposition": _clean(payload.get("referenced_prior_proposition"), 160),
        "candidate_source_ids": source_ids,
        "proposed_coverage": coverage,
        "ambiguity_type": ambiguity,
        "clarification_needed": bool(payload.get("clarification_needed")),
        "interpretation_confidence": confidence,
    }, ""


def _topic_rows(npc: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    raw = (npc or {}).get("topics") or (npc or {}).get("knowledge") or []
    rows = []
    if not isinstance(raw, list):
        return rows
    for topic in raw:
        if isinstance(topic, Mapping):
            text = str(topic.get("text") or topic.get("clue_text") or topic.get("label") or "").strip()
            ident = str(topic.get("id") or "").strip() or _snake(text)[:40]
            disclosure = str(topic.get("disclosure") or "public").lower()
            hidden = bool(topic.get("hidden") or topic.get("secret") or disclosure in {"secret", "hidden", "withheld", "none", "forbidden"})
            epistemic = str(topic.get("epistemic") or topic.get("epistemic_status") or "npc_knowledge")
            rows.append({
                "id": ident,
                "text": text,
                "clue_id": topic.get("clue_id") or topic.get("reveals_clue"),
                "hidden": hidden,
                "epistemic": epistemic,
                "record": dict(topic),
            })
        elif topic:
            text = str(topic).strip()
            rows.append({"id": _snake(text)[:40], "text": text, "clue_id": None, "hidden": False, "epistemic": "npc_knowledge", "record": {"id": _snake(text)[:40], "text": text}})
    return [row for row in rows if row["text"]]


def _npc_by_id(world: Mapping[str, Any] | None, npc_id: str) -> dict[str, Any] | None:
    for npc in (world or {}).get("npcs") or []:
        if isinstance(npc, Mapping) and str(npc.get("id") or "") == npc_id:
            return dict(npc)
    return None


def _name_tautology(text: str) -> bool:
    return bool(_NAME_FACT.search(text))


def classify_source_coverage(relationship: str, question: str, source_text: str) -> str:
    """Host relevance. Authorization is a separate decision."""
    predicate, argument = parse_relationship(relationship)
    fact = _tokens(source_text)
    if not fact or not (predicate or argument):
        return "unrelated"
    if any(token in _CAUSE_PREDICATES for token in predicate):
        if "other" in predicate:
            return "unrelated"
        subject_hits = _covers(argument, fact)
        if subject_hits and _CAUSE_MARKERS.search(source_text):
            return "direct"
        return "unrelated"
    argument_hits = _covers(argument, fact) if argument else 0
    ratio = argument_hits / len(argument) if argument else 0.0
    predicate_only = [token for token in predicate if not any(_same(token, arg) for arg in argument)]
    predicate_hits = _covers(predicate_only, fact) if predicate_only else False
    question_extra = [tok for tok in _tokens(question) if not any(_same(tok, arg) for arg in argument)]
    question_hit = _covers(question_extra, fact) > 0
    name_question = any(token in _NAME_PREDICATES for token in predicate) or bool(re.search(r"\bcalled\b", question or "", re.I))
    if _name_tautology(source_text) and not name_question:
        return "unrelated"
    if ratio <= 0 and not (predicate_hits and question_hit):
        return "unrelated"
    if predicate_hits and ratio >= 0.5:
        return "direct"
    if name_question and ratio >= 0.5 and (question_hit or predicate_hits):
        return "direct"
    if ratio >= 0.99 and (question_hit or not predicate):
        return "partial" if not predicate_hits else "direct"
    if ratio >= 0.5 and question_hit and predicate_hits:
        return "direct"
    if ratio >= 0.5:
        return "partial"
    return "unrelated"


def _conservative(host: str, proposed: str) -> str:
    rank = {"unknown": 0, "unrelated": 1, "partial": 2, "direct": 3}
    if proposed not in rank:
        return host
    return proposed if rank[proposed] < rank.get(host, 1) else host


def _host_line(name: str, kind: str, fact: str = "", *, ambiguity: str = "") -> str:
    speaker = name.strip() or "They"
    if kind == "clarification" and ambiguity == "addressee":
        return "Which person do you mean?"
    if kind == "clarification" and ambiguity == "correction_target":
        return f'{speaker} says, "Which question do you want me to answer?"'
    if kind == "clarification":
        return f'{speaker} says, "Which part do you mean?"'
    if kind == "refusal":
        return f'{speaker} says, "I couldn\'t answer that."'
    if kind == "partial" and fact:
        sentence = " ".join(fact.split()).rstrip(".")
        return f'{speaker} says, "{sentence}. I couldn\'t say more than that."'
    if kind == "direct" and fact:
        from game.social import format_structured_fact_social_line

        return format_structured_fact_social_line({"social": {"npc_name": speaker}}, fact)
    return f'{speaker} says, "I couldn\'t tell you."'


def _other_sources(prior: Mapping[str, Any], sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = {str(item) for item in prior.get("selected_source_ids") or []}
    relationship = str(prior.get("requested_relationship") or "")
    question = str(prior.get("question_text") or "")
    found = []
    for source in sources:
        if source["id"] in selected or source["hidden"]:
            continue
        if classify_source_coverage(relationship, question, source["text"]) == "direct":
            found.append(source)
    return found


def authorize_information_turn(
    *,
    player_text: str,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    resolved_npc_id: str = "",
    proposal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one proposal and bind an authorized response. Does not mutate the world."""
    started = time.perf_counter()
    utterance = _clean(player_text)
    participants = present_participants(world, scene)
    prior = prior_semantic_plan(session)
    named = match_addressees(utterance, participants)
    usage: dict[str, Any] = {}
    api_calls = 0
    if proposal is None:
        candidates = []
        focus = named[0]["id"] if len(named) == 1 else (str(prior.get("addressee_id") or "") if prior else "")
        npc = _npc_by_id(world, focus) if focus else None
        for row in _topic_rows(npc):
            if not row["hidden"]:
                candidates.append({"id": row["id"], "text": row["text"]})
        recent = []
        ctx = session.get("conversational_context") if isinstance(session, Mapping) else None
        rows = ctx.get("delivered_exchanges") if isinstance(ctx, Mapping) else None
        if isinstance(rows, list):
            recent = [row for row in rows if isinstance(row, Mapping)][-4:]
        outcome = propose_semantic_plan({
            "utterance": utterance,
            "participants": participants,
            "scene_summary": _scene_summary(scene),
            "prior_plan": prior,
            "recent_dialogue": recent,
            "candidates": candidates,
        })
        api_calls = int(outcome.get("api_calls") or 0)
        usage = dict(outcome.get("usage") or {})
        proposal = outcome.get("plan") if outcome.get("status") == "proposed" else None
        schema_error = "" if proposal is not None else str(outcome.get("reason") or "proposal_failed")
    else:
        schema_error = ""
    plan, error = validate_plan_schema(proposal)
    if plan is None:
        error = error or schema_error or "invalid_plan"
        line = "I didn't catch what you're asking."
        return _locked(
            utterance, {}, participants, prior, response_kind="clarification", ambiguity="subject",
            host_line=line, reason=error, api_calls=api_calls, usage=usage, started=started,
        )
    if _ACTION_REQUEST_RE.search(utterance):
        speaker = _speaker_name(named, prior, plan)
        return _locked(
            utterance, plan, participants, prior, response_kind="refusal",
            host_line=_host_line(speaker, "refusal"), reason="unsupported_consequential_request",
            api_calls=api_calls, usage=usage, started=started, addressee_id=_addressee_id(named, prior, plan, resolved_npc_id),
        )
    if prior and _CORRECTION_RE.search(utterance):
        plan["conversational_act"] = "correction"
        plan["correction_of_prior_question"] = True
        if plan.get("requested_relationship") == prior.get("requested_relationship"):
            relationship, subject = _relationship_from_text(utterance, prior, "correction")
            plan["requested_relationship"] = relationship
            plan["requested_subject"] = subject
    elif prior and _FOLLOW_RE.search(utterance):
        plan["conversational_act"] = "follow_up"
        predicate, _argument = parse_relationship(str(plan.get("requested_relationship") or ""))
        if not any(token in _CAUSE_PREDICATES for token in predicate):
            relationship, subject = _relationship_from_text(utterance, prior, "follow_up")
            plan["requested_relationship"] = relationship
            plan["requested_subject"] = subject
    addressee_id, ambiguity = _ground_addressee(named, prior, plan, resolved_npc_id, plan["conversational_act"])
    if ambiguity == "addressee" or not addressee_id:
        return _locked(
            utterance, plan, participants, prior, response_kind="clarification", ambiguity="addressee" if named or not addressee_id else "addressee",
            host_line=_host_line("", "clarification", ambiguity="addressee"), reason="addressee_not_grounded",
            api_calls=api_calls, usage=usage, started=started,
        )
    if plan["conversational_act"] == "correction" and not prior:
        speaker = _name_for(participants, addressee_id)
        return _locked(
            utterance, plan, participants, prior, response_kind="clarification", ambiguity="correction_target",
            host_line=_host_line(speaker, "clarification", ambiguity="correction_target"),
            reason="missing_correction_target", api_calls=api_calls, usage=usage, started=started,
            addressee_id=addressee_id,
        )
    npc = _npc_by_id(world, addressee_id) or {}
    sources = _topic_rows(npc)
    known_ids = {row["id"] for row in sources}
    rejected_ids = [
        ident for ident in plan["candidate_source_ids"] if ident not in known_ids
    ]
    if plan["requested_relationship"].startswith("other_of("):
        others = _other_sources(prior, sources)
        if len(others) == 1:
            return _select(
                utterance, plan, participants, prior, addressee_id, [others[0]], "direct",
                api_calls=api_calls, usage=usage, started=started, rejected_ids=rejected_ids,
            )
        if len(others) > 1:
            speaker = _name_for(participants, addressee_id)
            return _locked(
                utterance, plan, participants, prior, response_kind="clarification", ambiguity="proposition",
                host_line=_host_line(speaker, "clarification", ambiguity="proposition"),
                reason="proposition_ambiguity", api_calls=api_calls, usage=usage, started=started,
                addressee_id=addressee_id, rejected_ids=rejected_ids,
            )
        speaker = _name_for(participants, addressee_id)
        return _locked(
            utterance, plan, participants, prior, response_kind="unknown",
            host_line=_host_line(speaker, "unknown"), reason="no_other_source",
            api_calls=api_calls, usage=usage, started=started, addressee_id=addressee_id,
        )
    proposed = {row["source_id"]: row["coverage"] for row in plan["proposed_coverage"]}
    ranked: list[tuple[str, dict[str, Any]]] = []
    rejected_prior = set(str(item) for item in (prior.get("selected_source_ids") or [])) if plan["conversational_act"] == "correction" else set()
    for source in sources:
        if source["hidden"]:
            continue
        if source["id"] in rejected_prior:
            host_coverage = classify_source_coverage(plan["requested_relationship"], utterance, source["text"])
            if host_coverage != "direct":
                continue
        host_coverage = classify_source_coverage(plan["requested_relationship"], utterance, source["text"])
        if source["id"] in proposed:
            host_coverage = _conservative(host_coverage, proposed[source["id"]])
        if host_coverage in {"direct", "partial"}:
            ranked.append((host_coverage, source))
    direct = [source for coverage, source in ranked if coverage == "direct"]
    partial = [source for coverage, source in ranked if coverage == "partial"]
    speaker = _name_for(participants, addressee_id) or str(npc.get("name") or "")
    if len(direct) > 1:
        return _locked(
            utterance, plan, participants, prior, response_kind="clarification", ambiguity="proposition",
            host_line=_host_line(speaker, "clarification", ambiguity="proposition"),
            reason="proposition_ambiguity", api_calls=api_calls, usage=usage, started=started,
            addressee_id=addressee_id, rejected_ids=rejected_ids,
            candidate_ids=[source["id"] for source in direct],
        )
    if len(direct) == 1:
        return _select(
            utterance, plan, participants, prior, addressee_id, direct, "direct",
            api_calls=api_calls, usage=usage, started=started, rejected_ids=rejected_ids, speaker=speaker,
        )
    if len(partial) > 1:
        return _locked(
            utterance, plan, participants, prior, response_kind="clarification", ambiguity="proposition",
            host_line=_host_line(speaker, "clarification", ambiguity="proposition"),
            reason="proposition_ambiguity", api_calls=api_calls, usage=usage, started=started,
            addressee_id=addressee_id, rejected_ids=rejected_ids,
        )
    if len(partial) == 1:
        return _select(
            utterance, plan, participants, prior, addressee_id, partial, "partial",
            api_calls=api_calls, usage=usage, started=started, rejected_ids=rejected_ids, speaker=speaker,
        )
    hidden_hit = any(source["hidden"] and classify_source_coverage(plan["requested_relationship"], utterance, source["text"]) in {"direct", "partial"} for source in sources)
    kind = "refusal" if hidden_hit else "unknown"
    return _locked(
        utterance, plan, participants, prior, response_kind=kind,
        host_line=_host_line(speaker, kind), reason="unauthorized_source" if hidden_hit else "no_relevant_source",
        api_calls=api_calls, usage=usage, started=started, addressee_id=addressee_id, rejected_ids=rejected_ids,
    )


def _addressee_id(named: list[dict[str, Any]], prior: Mapping[str, Any], plan: Mapping[str, Any], resolved: str) -> str:
    ident, _ambiguity = _ground_addressee(named, prior, plan, resolved, str(plan.get("conversational_act") or ""))
    return ident


def _speaker_name(named: list[dict[str, Any]], prior: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
    if len(named) == 1:
        return str(named[0].get("name") or "")
    return str(plan.get("addressee_reference") or prior.get("addressee_id") or "")


def _name_for(participants: list[Mapping[str, Any]], npc_id: str) -> str:
    for person in participants:
        if str(person.get("id") or "") == npc_id:
            return str(person.get("name") or npc_id)
    return npc_id


def _ground_addressee(
    named: list[dict[str, Any]],
    prior: Mapping[str, Any],
    plan: Mapping[str, Any],
    resolved: str,
    act: str,
) -> tuple[str, str]:
    if len(named) > 1:
        return "", "addressee"
    if len(named) == 1:
        grounded = str(named[0].get("id") or "")
        proposed = str(plan.get("addressee_id") or "")
        if proposed and proposed != grounded:
            proposed = ""
        if resolved and resolved != grounded:
            return grounded, ""
        return grounded, ""
    if act in {"correction", "follow_up"}:
        previous = str(prior.get("addressee_id") or "")
        if previous:
            return previous, ""
        return "", "addressee"
    if resolved:
        return resolved, ""
    return "", "addressee"


def _select(
    utterance: str,
    plan: Mapping[str, Any],
    participants: list[Mapping[str, Any]],
    prior: Mapping[str, Any],
    addressee_id: str,
    sources: list[dict[str, Any]],
    kind: str,
    *,
    api_calls: int,
    usage: Mapping[str, Any],
    started: float,
    rejected_ids: list[str],
    speaker: str = "",
) -> dict[str, Any]:
    source = sources[0]
    name = speaker or _name_for(participants, addressee_id)
    topic = None
    if kind == "direct":
        topic = {
            "id": source["id"],
            "text": source["text"],
            "clue_id": source.get("clue_id"),
            "clue_text": source["text"],
        }
    return _locked(
        utterance, plan, participants, prior, response_kind=kind,
        host_line=_host_line(name, kind, source["text"]), reason="authorized_" + kind,
        api_calls=api_calls, usage=usage, started=started, addressee_id=addressee_id,
        selected=[source], topic_rec=topic, rejected_ids=rejected_ids,
        authorized_text=source["text"], epistemic=str(source.get("epistemic") or "npc_knowledge"),
    )


def _locked(
    utterance: str,
    plan: Mapping[str, Any],
    participants: list[Mapping[str, Any]],
    prior: Mapping[str, Any],
    *,
    response_kind: str,
    host_line: str,
    reason: str,
    api_calls: int,
    usage: Mapping[str, Any],
    started: float,
    ambiguity: str = "",
    addressee_id: str = "",
    selected: list[dict[str, Any]] | None = None,
    topic_rec: dict[str, Any] | None = None,
    rejected_ids: list[str] | None = None,
    candidate_ids: list[str] | None = None,
    authorized_text: str = "",
    epistemic: str = "",
) -> dict[str, Any]:
    selected = selected or []
    sufficiency = {
        "direct": "direct",
        "partial": "partial",
        "refusal": "refusal",
        "clarification": "clarification",
    }.get(response_kind, "unknown")
    locked_plan = {
        "locked": True,
        "plan_version": PLAN_VERSION,
        "conversational_act": str(plan.get("conversational_act") or "information_question"),
        "addressee_id": addressee_id,
        "addressee_reference": _name_for(participants, addressee_id) if addressee_id else "",
        "requested_subject": str(plan.get("requested_subject") or ""),
        "requested_relationship": str(plan.get("requested_relationship") or ""),
        "question_text": str(plan.get("question_text") or utterance),
        "correction_of_prior_question": bool(plan.get("correction_of_prior_question")),
        "correction_target": str(plan.get("correction_target") or prior.get("question_text") or ""),
        "referenced_prior_proposition": str(plan.get("referenced_prior_proposition") or prior.get("requested_relationship") or ""),
        "selected_source_ids": [row["id"] for row in selected],
        "rejected_source_ids": list(rejected_ids or []),
        "candidate_source_ids": list(candidate_ids or [row["id"] for row in selected]),
        "answer_sufficiency": sufficiency,
        "response_kind": response_kind,
        "ambiguity_type": ambiguity,
        "authorized_text": authorized_text,
        "epistemic_status": epistemic or "none",
        "canonical": False,
        "host_line": host_line,
        "reason": reason,
        "provider_calls": api_calls,
        "provider_usage": dict(usage),
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
    }
    return {
        "handled": True,
        "plan": locked_plan,
        "topic_rec": topic_rec,
        "topic_selection": {
            "owner": "unified_semantic_plan",
            "candidate_sources": [f"npc:{addressee_id}:{ident}" for ident in locked_plan["candidate_source_ids"]],
            "selected_source": f"npc:{addressee_id}:{selected[0]['id']}" if selected else "",
            "ambiguous": bool(ambiguity),
        },
    }


def stage_delivered_plan(session: dict[str, Any] | None, player_text: str, plan: Mapping[str, Any]) -> None:
    """Remember a locked plan until this turn's delivered exchange is recorded."""
    if not isinstance(session, dict) or not plan.get("locked"):
        return
    ctx = session.setdefault("conversational_context", {})
    if isinstance(ctx, dict):
        ctx["_unified_semantic_pending_delivery"] = {"player_text": _clean(player_text), "plan": dict(plan)}


def take_staged_plan(session: Mapping[str, Any] | None, player_text: str) -> dict[str, Any] | None:
    if not isinstance(session, dict):
        return None
    ctx = session.get("conversational_context")
    if not isinstance(ctx, dict):
        return None
    pending = ctx.get("_unified_semantic_pending_delivery")
    if not isinstance(pending, Mapping):
        return None
    if _clean(pending.get("player_text")) != _clean(player_text):
        return None
    ctx.pop("_unified_semantic_pending_delivery", None)
    plan = pending.get("plan")
    return dict(plan) if isinstance(plan, Mapping) and plan.get("locked") else None


def store_binding(session: dict[str, Any] | None, player_text: str, locked: Mapping[str, Any]) -> None:
    if not isinstance(session, dict):
        return
    ctx = session.setdefault("conversational_context", {})
    if not isinstance(ctx, dict):
        return
    ctx[BINDING_KEY] = {"player_text": _clean(player_text), "locked": dict(locked)}


def consume_binding(session: Mapping[str, Any] | None, player_text: str) -> dict[str, Any] | None:
    if not isinstance(session, dict):
        return None
    ctx = session.get("conversational_context")
    if not isinstance(ctx, dict):
        return None
    binding = ctx.get(BINDING_KEY)
    if not isinstance(binding, Mapping):
        return None
    if _clean(binding.get("player_text")) != _clean(player_text):
        ctx.pop(BINDING_KEY, None)
        return None
    ctx.pop(BINDING_KEY, None)
    locked = binding.get("locked")
    return dict(locked) if isinstance(locked, Mapping) else None


def planning_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    log: list | None = None,
):
    """Return a conversational decision for the migrated family, else None.

    Clarification fails closed. Accepted questions execute as ASK with the
    locked plan attached. Other families return None.
    """
    del log
    if not unified_semantic_planning_enabled():
        return None
    if not is_migrated_information_turn(player_text, session=session, scene=scene, world=world):
        return None
    from game.conversational_orchestration import ConversationalDecision, ConversationalDecisionCategory, _operation_record

    locked = authorize_information_turn(
        player_text=player_text, session=session, world=world, scene=scene,
    )
    plan = locked["plan"]
    stage_delivered_plan(session if isinstance(session, dict) else None, player_text, plan)
    target = str(plan.get("addressee_id") or "")
    failed = str(plan.get("reason") or "")
    if plan["response_kind"] == "clarification" and (plan.get("ambiguity_type") == "addressee" or not target):
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=player_text,
            intent_family="unified_semantic_plan",
            reason="unified_semantic_addressee_clarification" if plan.get("ambiguity_type") == "addressee" else "unified_semantic_plan_rejected",
            player_facing_text=str(plan["host_line"]),
            execution_policy="answer_only",
            intent_modality="informational",
            authorization={"unified_semantic_plan": plan},
        )
    if failed in {"invalid_plan", "proposal_failed", "not_an_object", "malformed_json", "provider_disabled", "invalid_relationship", "unsupported_act", "invalid_ambiguity", "invalid_confidence", "unsupported_authority_field"} or failed.endswith("_failed"):
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=player_text,
            intent_family="unified_semantic_plan",
            reason="unified_semantic_plan_rejected",
            player_facing_text=str(plan["host_line"]),
            execution_policy="answer_only",
            intent_modality="informational",
            authorization={"unified_semantic_plan": plan},
        )
    if not target:
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=player_text,
            intent_family="unified_semantic_plan",
            reason="unified_semantic_plan_rejected",
            player_facing_text=str(plan["host_line"] or "Which person do you mean?"),
            execution_policy="answer_only",
            intent_modality="informational",
            authorization={"unified_semantic_plan": plan},
        )
    record = _operation_record(
        operation="ASK",
        target_id=target,
        player_text=_clean(player_text),
        summary=f"Ask {plan.get('addressee_reference') or target}: {_clean(player_text)}",
        references={"resolved_references": [{"text": "semantic plan", "entity_id": target}], "unresolved_references": []},
    )
    record["unified_semantic_plan"] = plan
    store_binding(session if isinstance(session, dict) else None, player_text, locked)
    return ConversationalDecision(
        category=ConversationalDecisionCategory.EXECUTE,
        primary_intention=_clean(player_text),
        intent_family="unified_semantic_plan",
        proposed_operation="ASK",
        proposed_target=target,
        proposed_record=record,
        requires_authoritative_execution=True,
        reason="unified_semantic_plan_accepted",
        confidence=0.86,
        execution_policy="answer_only",
        intent_modality="informational",
        communication_owner="NPC",
        communication_purpose="QUESTION",
        authorization={"unified_semantic_plan": plan},
    )


def locked_plan_for_social_turn(
    *,
    player_text: str,
    session: dict | None,
    world: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    npc: Mapping[str, Any] | None,
    npc_id: str,
    npc_name: str,
    action_metadata: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Return a locked plan for this social question, or None to keep legacy selection."""
    del npc_name
    if not unified_semantic_planning_enabled():
        return None
    metadata = action_metadata if isinstance(action_metadata, Mapping) else {}
    existing = metadata.get("unified_semantic_plan")
    if isinstance(existing, Mapping) and existing.get("locked"):
        consume_binding(session, player_text)
        return _from_existing_plan(existing)
    bound = consume_binding(session, player_text)
    if isinstance(bound, Mapping) and bound.get("handled"):
        return bound
    if isinstance(bound, Mapping) and isinstance(bound.get("plan"), Mapping):
        return bound
    if not is_migrated_information_turn(player_text, session=session, scene=scene, world=world):
        return None
    resolved = str(npc_id or (npc or {}).get("id") or "")
    return authorize_information_turn(
        player_text=player_text,
        session=session,
        world=world,
        scene=scene,
        resolved_npc_id=resolved,
    )


def _from_existing_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    topic = None
    if plan.get("response_kind") == "direct" and plan.get("authorized_text") and (plan.get("selected_source_ids") or []):
        topic = {
            "id": str(plan["selected_source_ids"][0]),
            "text": str(plan.get("authorized_text") or ""),
            "clue_text": str(plan.get("authorized_text") or ""),
        }
    addressee = str(plan.get("addressee_id") or "")
    selected = str((plan.get("selected_source_ids") or [""])[0] or "")
    return {
        "handled": True,
        "plan": dict(plan),
        "topic_rec": topic,
        "topic_selection": {
            "owner": "unified_semantic_plan",
            "candidate_sources": [f"npc:{addressee}:{ident}" for ident in plan.get("candidate_source_ids") or []],
            "selected_source": f"npc:{addressee}:{selected}" if selected else "",
            "ambiguous": bool(plan.get("ambiguity_type")),
        },
    }


def authority_record_from_plan(
    player_text: str,
    *,
    npc: Mapping[str, Any] | None,
    social: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Dialogue-authority view of an accepted plan. Speech stays non-canonical."""
    person = npc if isinstance(npc, Mapping) else {}
    name = str(social.get("npc_name") or person.get("name") or plan.get("addressee_reference") or "They")
    npc_id = str(social.get("npc_id") or person.get("id") or plan.get("addressee_id") or "")
    kind = str(plan.get("response_kind") or "unknown")
    posture = {"direct": "established", "partial": "partial", "refusal": "withheld"}.get(kind, "unknown")
    sufficiency = {
        "direct": "directly_answers",
        "partial": "partially_informs",
        "refusal": "unknown",
        "clarification": "does_not_answer",
    }.get(kind, "unknown")
    return {
        "topic_grounding": {
            "speaker_id": npc_id,
            "addressee": "player",
            "requested_subject": plan.get("requested_subject") or "",
            "requested_information": "general",
            "requested_relationship": plan.get("requested_relationship") or "",
            "reference": "unified_semantic_plan",
            "candidate_sources": list((social.get("topic_selection") or {}).get("candidate_sources") or []),
            "selected_source": str((social.get("topic_selection") or {}).get("selected_source") or ""),
            "ambiguous": bool(plan.get("ambiguity_type")),
            "ownership": "npc",
            "owner": "unified_semantic_plan",
        },
        "requested_information": "general",
        "subject": str(plan.get("requested_subject") or ""),
        "knowledge_posture": posture,
        "answer_relation": "sufficient" if kind == "direct" else "partially_informs" if kind == "partial" else "none",
        "answer_sufficiency": sufficiency,
        "proposition_id": "",
        "authorized_proposition": str(plan.get("authorized_text") or ""),
        "improvisation_permitted": False,
        "improvisation_scope": "none",
        "narration_determined": True,
        "player_line": str(plan.get("host_line") or ""),
        "canonical": False,
        "npc_id": npc_id,
        "npc_name": name,
        "npc_role": str(person.get("role") or ""),
        "npc_disposition": str(person.get("disposition") or ""),
        "prohibited_claims": [
            "consequential_world_fact",
            "hidden_disclosure",
            "mechanical_change",
            "new_obligation",
            "invented_answer",
        ],
        "prior_commitments": [],
        "reconciled_plan": "",
        "reuse_prior_speech": False,
        "unified_semantic_plan": dict(plan),
        "epistemic_status": str(plan.get("epistemic_status") or "none"),
    }


def delivered_plan_fields(plan: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(plan, Mapping) or not plan.get("locked"):
        return None
    return {
        "plan_version": PLAN_VERSION,
        "conversational_act": str(plan.get("conversational_act") or ""),
        "addressee_id": str(plan.get("addressee_id") or ""),
        "requested_subject": str(plan.get("requested_subject") or "")[:120],
        "requested_relationship": str(plan.get("requested_relationship") or "")[:160],
        "question_text": str(plan.get("question_text") or "")[:400],
        "selected_source_ids": [str(item) for item in (plan.get("selected_source_ids") or [])][:8],
        "answer_sufficiency": str(plan.get("answer_sufficiency") or ""),
        "response_kind": str(plan.get("response_kind") or ""),
        "ambiguity_type": str(plan.get("ambiguity_type") or ""),
        "referenced_prior_proposition": str(plan.get("referenced_prior_proposition") or "")[:160],
        "rejected_source_ids": [str(item) for item in (plan.get("rejected_source_ids") or [])][:8],
        "authorized_text": str(plan.get("authorized_text") or "")[:400],
        "host_line": str(plan.get("host_line") or "")[:400],
        "reason": str(plan.get("reason") or "")[:120],
        "epistemic_status": str(plan.get("epistemic_status") or ""),
        "canonical": False,
    }
