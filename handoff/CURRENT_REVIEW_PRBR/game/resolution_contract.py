"""Typed resolution contract for one player turn.

The contract records what the player wants resolved. It does not decide what
the DM may invent, and it does not replace interaction obligations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re
from typing import Any, Mapping

from game.discourse_state import (
    SLOT_ACTION,
    SLOT_CLAIM,
    SLOT_INSPECTED,
    SLOT_INTERLOCUTOR,
    SLOT_LEAD,
    effective_discourse_focus,
    focus_summary,
)


REQUEST_INQUIRY = "inquiry"
REQUEST_ACTION = "action"
REQUEST_SOCIAL_ACTION = "social_action"
REQUEST_CLARIFICATION = "clarification"

OP_PERCEIVE = "perceive"
OP_INSPECT = "inspect"
OP_ASK = "ask"
OP_CONFIRM = "confirm"
OP_FOLLOW = "follow"
OP_ACT = "act"

DIM_APPEARANCE = "appearance"
DIM_SOUND = "sound"
DIM_SMELL = "smell"
DIM_WEAR = "wear"
DIM_USE = "use"
DIM_CHANGE = "change"
DIM_SOURCE = "source"
DIM_CONFIDENCE = "confidence"
DIM_LOCATION = "location"
DIM_TIME = "time"
DIM_NEXT_STEP = "next_step"

PERCEPTION_DIMENSIONS = frozenset({DIM_APPEARANCE, DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, DIM_CHANGE})
CLAIM_DIMENSIONS = frozenset({DIM_SOURCE, DIM_CONFIDENCE, DIM_LOCATION, DIM_TIME})

EXPECT_ANSWER = "answer"
EXPECT_ACTION = "action_outcome"
EXPECT_REFUSAL = "refusal"
EXPECT_CLARIFICATION = "clarification"
EXPECT_PARTIAL = "partial"

EPISTEMIC_AUTHORITATIVE = "authoritative"
EPISTEMIC_INCIDENTAL = "bounded_incidental"
EPISTEMIC_NPC_CLAIM = "npc_claim"
EPISTEMIC_UNKNOWN = "unknown_allowed"
EPISTEMIC_CONSEQUENTIAL = "consequential_protected"

PROVENANCE_EXPLICIT = "explicit_player"
PROVENANCE_INHERITED = "inherited_discourse"
PROVENANCE_UNRESOLVED = "unresolved"
PROVENANCE_AMBIGUOUS = "ambiguous"

_DIMENSION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (DIM_SOUND, re.compile(r"\b(?:sounds?|listen(?:ing|ed)?|hearing)\b|\bhear\b", re.IGNORECASE)),
    (DIM_SMELL, re.compile(r"\b(?:smells?|scent|odor|odour|aroma)\b", re.IGNORECASE)),
    (DIM_APPEARANCE, re.compile(r"\b(?:look(?:s|ed)? like|appearance|colou?rs?)\b", re.IGNORECASE)),
    (DIM_WEAR, re.compile(r"\b(?:wear|worn|marks?|scuffs?|disturbed)\b", re.IGNORECASE)),
    (DIM_USE, re.compile(r"\b(?:signs? of use|use)\b", re.IGNORECASE)),
    (DIM_CHANGE, re.compile(r"\b(?:what changed|what changes|changed when|when i (?:do|did) that)\b", re.IGNORECASE)),
    (DIM_SOURCE, re.compile(r"\b(?:who told|where did you hear|who said|who would know|source of)\b", re.IGNORECASE)),
    (DIM_CONFIDENCE, re.compile(r"\b(?:do you believe|how certain|how sure|are you sure|confidence)\b", re.IGNORECASE)),
    (DIM_TIME, re.compile(r"\b(?:when did|when was|how long ago|what time)\b", re.IGNORECASE)),
    (DIM_LOCATION, re.compile(r"\b(?:where (?:did|does|is|was|can|could)|from here)\b", re.IGNORECASE)),
    (DIM_NEXT_STEP, re.compile(r"\b(?:next step|concrete next|what should i do|immediate next action)\b", re.IGNORECASE)),
)

_CONSEQUENTIAL_RE = re.compile(
    r"\b(?:secret|hidden|traitor|conspiracy|murderer|spy|cult|vault|artifact|curse|prophecy|"
    r"true motive|really works for|allegiance)\b",
    re.IGNORECASE,
)
_LEAD_RE = re.compile(
    r"\b(?:follow|take|pursue)\b[^.!?]{0,40}\b(?:that|the|this|the best|best)\s+lead\b|\bthat lead\b|\bthe lead\b",
    re.IGNORECASE,
)
_PRIOR_ACTION_RE = re.compile(
    r"\b(?:when i (?:do|did) that|after i (?:do|did) that|what changed when)\b",
    re.IGNORECASE,
)
_CONFIRM_RE = re.compile(r"\bconfirm\b[^.!?]{0,40}\b(?:next action|next step|what i should)\b", re.IGNORECASE)
_ACTION_REQUEST_RE = re.compile(
    r"\b(?:can|could|would|will)\s+(?:you|they|he|she)\s+"
    r"(?:introduce|take|bring|show|open|close|help|point|lead|give|send|ask|arrange)\b"
    r"|\b(?:introduce me|point me to)\b",
    re.IGNORECASE,
)
_PHYSICAL_RE = re.compile(
    r"\b(?:open|knock|push|pull|break|force|climb|enter|search)\b",
    re.IGNORECASE,
)
_INSPECT_RE = re.compile(r"\b(?:inspect|examine|look at|check|study)\b", re.IGNORECASE)
_CLARIFY_RE = re.compile(r"\b(?:what do you mean|which one|which person|clarify)\b", re.IGNORECASE)
_SCENE_TARGET_RE = re.compile(r"\b(?:where i am|around me|this place|the scene)\b", re.IGNORECASE)
_EXPLICIT_TARGET_RE = re.compile(
    r"\b(?:inspect|examine|look at|listen(?:\s+to|\s+through)?|open|read|check|study)\s+"
    r"(?:the\s+|a\s+|an\s+)?(?P<target>[^?.!,]{1,60})",
    re.IGNORECASE,
)
_SMELL_TARGET_RE = re.compile(
    r"\b(?:smell|smelling)\s+(?:the\s+|a\s+|an\s+)(?P<target>[^?.!,]{1,60})",
    re.IGNORECASE,
)
_WHAT_DOES_RE = re.compile(
    r"\bwhat does\s+(?:the\s+|a\s+|an\s+)?(?P<target>.+?)\s+(?:look|smell|sound|feel)\b",
    re.IGNORECASE,
)
_PRONOUN_TARGET_RE = re.compile(
    r"^(?:it|its|that|this|them|they|him|her|that lead|the lead|that person|that place|that thing)$",
    re.IGNORECASE,
)
_ANAPHOR_RE = re.compile(r"\b(?:it|its|that|this|them|they|that person|that place)\b", re.IGNORECASE)

_RESPONSE_CUES: dict[str, re.Pattern[str]] = {
    DIM_SOUND: re.compile(
        r"\b(?:sounds?|hear|hearing|listen|quiet|noise|noisy|silence|silent|voices?|footsteps?|"
        r"murmurs?|clang|creak|shouts?|whispers?|music|thuds?|rustle)\b",
        re.IGNORECASE,
    ),
    DIM_SMELL: re.compile(r"\b(?:smells?|scent|odor|odour|aroma|stink|reek|fragrant|stench)\b", re.IGNORECASE),
    DIM_APPEARANCE: re.compile(
        r"\b(?:look(?:s|ed|ing)?|appear(?:s|ance)?|colou?r|visible|seen|shaped|painted|dented|scarred)\b",
        re.IGNORECASE,
    ),
    DIM_WEAR: re.compile(
        r"\b(?:wear|worn|marks?|scuffs?|scratched|faded|dented|disturbed|polished|scarred)\b",
        re.IGNORECASE,
    ),
    DIM_USE: re.compile(r"\b(?:used|use|handled|foot traffic|opened often|rarely touched)\b", re.IGNORECASE),
    DIM_CHANGE: re.compile(
        r"\b(?:change[ds]?|unchanged|no difference|still the same|nothing (?:new|changes)|remains)\b",
        re.IGNORECASE,
    ),
    DIM_SOURCE: re.compile(
        r"\b(?:told|heard from|according to|source|someone|nobody|travelers?|cannot verify)\b",
        re.IGNORECASE,
    ),
    DIM_CONFIDENCE: re.compile(
        r"\b(?:certain|sure|believe|doubt|trust|unsure|confident|certainty|not sure)\b",
        re.IGNORECASE,
    ),
    DIM_LOCATION: re.compile(
        r"\b(?:from here|over there|located|location|took place|happened|nearby|beside|next to|across|near)\b",
        re.IGNORECASE,
    ),
    DIM_TIME: re.compile(r"\b(?:yesterday|tonight|earlier|recently|ago|at dusk|last night|this morning|when)\b", re.IGNORECASE),
    DIM_NEXT_STEP: re.compile(
        r"\b(?:next step|you can|ask the|go to|try to|follow|first|route|another route)\b",
        re.IGNORECASE,
    ),
}
_ACTION_CUE_RE = re.compile(
    r"\b(?:opens?|opened|closes?|refuses?|will not|won't|cannot|can't|fails?|failed|yields?|"
    r"introduce|points?|leads?|done|completed|blocked|does not|doesn't)\b",
    re.IGNORECASE,
)
_LEGITIMATE_RE = re.compile(
    r"\b(?:cannot|can't|could not|couldn't|will not|won't|unable|another (?:source|route)|"
    r"cannot be identified|which (?:one|person)|clarif(?:y|ication)|no reliable|no distinct|"
    r"not able|do not know|don't know|not enough|need another|will not carry)\b",
    re.IGNORECASE,
)
_LONG_VISUAL_RE = re.compile(r"\b(?:stands?|watchers?|crowd|street|gate|square)\b", re.IGNORECASE)


def _clean(value: Any, *, limit: int = 180) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:limit]


@dataclass(frozen=True)
class TargetRef:
    type: str
    id_or_text: str | None
    source: str


@dataclass(frozen=True)
class DiscoursePointer:
    type: str
    id: str | None
    label: str | None
    source_turn: int | None


@dataclass(frozen=True)
class ResolutionContract:
    contract_id: str
    turn_index: int | None
    request_kind: str
    operation: str
    target_ref: TargetRef | None
    interlocutor_id: str | None
    conversational_subject: str | None
    dimension: str | None
    dimensions: tuple[str, ...]
    expected_resolution: str
    epistemic_mode: str
    discourse_ref: DiscoursePointer | None
    referent_provenance: str
    ambiguous: bool
    raw_input: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["dimensions"] = list(self.dimensions)
        return payload


def contract_mapping_from_resolution(resolution: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(resolution, Mapping):
        return {}
    metadata = resolution.get("metadata")
    contract = metadata.get("resolution_contract") if isinstance(metadata, Mapping) else None
    return dict(contract) if isinstance(contract, Mapping) else {}


def contract_requests_consequential_protection(contract: Mapping[str, Any] | None) -> bool:
    return isinstance(contract, Mapping) and contract.get("epistemic_mode") == EPISTEMIC_CONSEQUENTIAL


def _contract_id(turn_index: int | None, text: str) -> str:
    raw = f"{turn_index if turn_index is not None else ''}|{text.lower()}"
    return "rc_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _dimensions(text: str) -> tuple[str, ...]:
    found: list[tuple[int, str]] = []
    for name, pattern in _DIMENSION_PATTERNS:
        match = pattern.search(text)
        if match:
            found.append((match.start(), name))
    found.sort()
    ordered: list[str] = []
    for _, name in found:
        if name not in ordered:
            ordered.append(name)
    if DIM_SOUND in ordered and re.search(r"\bheard\b", text, re.IGNORECASE) and not re.search(
        r"\b(?:sounds?|listen|hearing|\bhear\b)\b", text, re.IGNORECASE
    ):
        ordered = [name for name in ordered if name != DIM_SOUND]
    return tuple(ordered)


def _explicit_target(text: str) -> str:
    for pattern in (_WHAT_DOES_RE, _EXPLICIT_TARGET_RE, _SMELL_TARGET_RE):
        match = pattern.search(text)
        if not match:
            continue
        target = _clean(match.group("target"), limit=80).strip(" \"'")
        target = re.sub(r"\s+\b(?:like|closely|carefully)\b$", "", target, flags=re.IGNORECASE).strip()
        if not target or _PRONOUN_TARGET_RE.match(target):
            continue
        return target
    return ""


def _pointer_from_slot(slot_name: str, slot: Mapping[str, Any] | None) -> DiscoursePointer | None:
    if not isinstance(slot, Mapping):
        return None
    kind = {
        SLOT_CLAIM: "claim",
        SLOT_LEAD: "lead",
        SLOT_INSPECTED: "object",
        SLOT_ACTION: "action",
        SLOT_INTERLOCUTOR: "interlocutor",
    }[slot_name]
    return DiscoursePointer(
        type=kind,
        id=_clean(slot.get("id"), limit=80) or None,
        label=_clean(slot.get("label"), limit=160) or None,
        source_turn=slot.get("turn_index") if isinstance(slot.get("turn_index"), int) else None,
    )


def _resolve_referent(
    text: str,
    *,
    dimensions: tuple[str, ...],
    focus: Mapping[str, Any],
    explicit_target: str,
) -> tuple[str, TargetRef | None, DiscoursePointer | None, bool]:
    """Return provenance, target, discourse pointer, and ambiguity."""
    lead_slot = focus.get(SLOT_LEAD) if isinstance(focus.get(SLOT_LEAD), Mapping) else None
    claim_slot = focus.get(SLOT_CLAIM) if isinstance(focus.get(SLOT_CLAIM), Mapping) else None
    inspected = focus.get(SLOT_INSPECTED) if isinstance(focus.get(SLOT_INSPECTED), Mapping) else None
    action = focus.get(SLOT_ACTION) if isinstance(focus.get(SLOT_ACTION), Mapping) else None
    interlocutor = focus.get(SLOT_INTERLOCUTOR) if isinstance(focus.get(SLOT_INTERLOCUTOR), Mapping) else None

    if _LEAD_RE.search(text):
        pointer = _pointer_from_slot(SLOT_LEAD, lead_slot)
        if pointer is None:
            return (
                PROVENANCE_UNRESOLVED,
                TargetRef("lead", "that lead", PROVENANCE_UNRESOLVED),
                None,
                False,
            )
        return (
            PROVENANCE_INHERITED,
            TargetRef("lead", pointer.label or pointer.id, PROVENANCE_INHERITED),
            pointer,
            False,
        )
    if _PRIOR_ACTION_RE.search(text) or DIM_CHANGE in dimensions and re.search(r"\bthat\b", text, re.IGNORECASE):
        pointer = _pointer_from_slot(SLOT_ACTION, action)
        if pointer is None:
            return PROVENANCE_UNRESOLVED, TargetRef("action", "prior action", PROVENANCE_UNRESOLVED), None, False
        return (
            PROVENANCE_INHERITED,
            TargetRef("action", pointer.label or pointer.id, PROVENANCE_INHERITED),
            pointer,
            False,
        )
    claimish = bool(set(dimensions) & {DIM_SOURCE, DIM_CONFIDENCE}) or bool(
        re.search(r"\b(?:who told|do you believe|how certain|that claim|what they said)\b", text, re.IGNORECASE)
    )
    if not claimish and set(dimensions) & {DIM_LOCATION, DIM_TIME} and re.search(
        r"\b(?:that|it|then|they said)\b", text, re.IGNORECASE
    ):
        claimish = True
    if claimish and not explicit_target:
        pointer = _pointer_from_slot(SLOT_CLAIM, claim_slot)
        if pointer is None:
            return PROVENANCE_UNRESOLVED, TargetRef("claim", None, PROVENANCE_UNRESOLVED), None, False
        return (
            PROVENANCE_INHERITED,
            TargetRef("claim", pointer.label or pointer.id, PROVENANCE_INHERITED),
            pointer,
            False,
        )
    if explicit_target:
        return (
            PROVENANCE_EXPLICIT,
            TargetRef("object", explicit_target, PROVENANCE_EXPLICIT),
            None,
            False,
        )
    if _SCENE_TARGET_RE.search(text) and not _ANAPHOR_RE.search(text):
        return PROVENANCE_EXPLICIT, TargetRef("scene", "current scene", PROVENANCE_EXPLICIT), None, False

    wants_inspected = bool(set(dimensions) & PERCEPTION_DIMENSIONS) or bool(_INSPECT_RE.search(text))
    wants_person = bool(re.search(r"\b(?:them|that person|they)\b", text, re.IGNORECASE))
    wants_place = bool(re.search(r"\bthat place\b", text, re.IGNORECASE))
    if wants_person and interlocutor is not None and not wants_inspected:
        pointer = _pointer_from_slot(SLOT_INTERLOCUTOR, interlocutor)
        return (
            PROVENANCE_INHERITED,
            TargetRef("interlocutor", pointer.label if pointer else None, PROVENANCE_INHERITED),
            pointer,
            False,
        )
    if wants_place:
        if inspected is not None and lead_slot is not None:
            return PROVENANCE_AMBIGUOUS, None, None, True
        if inspected is not None:
            pointer = _pointer_from_slot(SLOT_INSPECTED, inspected)
            return PROVENANCE_INHERITED, TargetRef("place", pointer.label if pointer else None, PROVENANCE_INHERITED), pointer, False
        if lead_slot is not None:
            pointer = _pointer_from_slot(SLOT_LEAD, lead_slot)
            return PROVENANCE_INHERITED, TargetRef("place", pointer.label if pointer else None, PROVENANCE_INHERITED), pointer, False
    if wants_inspected and _ANAPHOR_RE.search(text):
        if inspected is None:
            return PROVENANCE_UNRESOLVED, TargetRef("object", None, PROVENANCE_UNRESOLVED), None, False
        pointer = _pointer_from_slot(SLOT_INSPECTED, inspected)
        return (
            PROVENANCE_INHERITED,
            TargetRef(str(inspected.get("kind") or "object"), pointer.label if pointer else None, PROVENANCE_INHERITED),
            pointer,
            False,
        )
    if _ANAPHOR_RE.search(text) and not explicit_target:
        candidates = [slot for slot in (inspected, claim_slot, lead_slot, interlocutor, action) if isinstance(slot, Mapping)]
        if len(candidates) > 1:
            return PROVENANCE_AMBIGUOUS, None, None, True
        if len(candidates) == 1:
            slot = candidates[0]
            slot_name = next(
                name
                for name in (SLOT_INSPECTED, SLOT_CLAIM, SLOT_LEAD, SLOT_INTERLOCUTOR, SLOT_ACTION)
                if focus.get(name) is slot
            )
            pointer = _pointer_from_slot(slot_name, slot)
            return (
                PROVENANCE_INHERITED,
                TargetRef(pointer.type if pointer else "object", pointer.label if pointer else None, PROVENANCE_INHERITED),
                pointer,
                False,
            )
        return PROVENANCE_UNRESOLVED, None, None, False
    return PROVENANCE_EXPLICIT, None, None, False


def _operation(
    text: str,
    dimensions: tuple[str, ...],
    *,
    action_type: str,
) -> tuple[str, str]:
    if _CLARIFY_RE.search(text):
        return REQUEST_CLARIFICATION, OP_ASK
    if _LEAD_RE.search(text):
        return REQUEST_ACTION, OP_FOLLOW
    if _CONFIRM_RE.search(text) or DIM_NEXT_STEP in dimensions and re.search(r"\bconfirm\b", text, re.IGNORECASE):
        return REQUEST_ACTION, OP_CONFIRM
    if _ACTION_REQUEST_RE.search(text):
        return REQUEST_SOCIAL_ACTION, OP_ACT
    if _PHYSICAL_RE.search(text) and not dimensions:
        return REQUEST_ACTION, OP_ACT
    if dimensions and set(dimensions) <= PERCEPTION_DIMENSIONS | {DIM_NEXT_STEP}:
        if _INSPECT_RE.search(text) and not (set(dimensions) & {DIM_SOUND, DIM_SMELL, DIM_APPEARANCE, DIM_CHANGE}):
            return REQUEST_INQUIRY, OP_INSPECT
        if set(dimensions) & PERCEPTION_DIMENSIONS:
            return REQUEST_INQUIRY, OP_PERCEIVE
    if _INSPECT_RE.search(text) or action_type in {"observe", "investigate"}:
        if set(dimensions) & {DIM_SOUND, DIM_SMELL, DIM_APPEARANCE, DIM_CHANGE}:
            return REQUEST_INQUIRY, OP_PERCEIVE
        return REQUEST_INQUIRY, OP_INSPECT
    if action_type in {"interact", "custom", "travel", "attack"}:
        return REQUEST_ACTION, OP_ACT
    return REQUEST_INQUIRY, OP_ASK


def construct_resolution_contract(
    *,
    player_text: str | None,
    session: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
) -> ResolutionContract:
    """Build a contract from raw player text and current runtime context."""
    text = _clean(player_text, limit=240)
    turn_index = None
    if isinstance(session, Mapping) and isinstance(session.get("turn_counter"), int):
        turn_index = int(session["turn_counter"])
    focus = effective_discourse_focus(session, scene_id=scene_id)
    dimensions = _dimensions(text)
    explicit = _explicit_target(text)
    if not explicit and isinstance(normalized_action, Mapping):
        action_target = _clean(
            normalized_action.get("target_id") or normalized_action.get("label"),
            limit=80,
        )
        if action_target and not _PRONOUN_TARGET_RE.match(action_target):
            explicit = action_target
    provenance, target, discourse, ambiguous = _resolve_referent(
        text,
        dimensions=dimensions,
        focus=focus,
        explicit_target=explicit,
    )
    action_type = ""
    if isinstance(normalized_action, Mapping):
        action_type = str(normalized_action.get("type") or "").strip().lower()
    request_kind, operation = _operation(text, dimensions, action_type=action_type)
    if ambiguous or (provenance == PROVENANCE_UNRESOLVED and _ANAPHOR_RE.search(text)):
        request_kind = REQUEST_CLARIFICATION
        expected = EXPECT_CLARIFICATION
    elif _CONSEQUENTIAL_RE.search(text):
        expected = EXPECT_REFUSAL
    elif operation in {OP_ACT, OP_FOLLOW, OP_CONFIRM}:
        expected = EXPECT_ACTION
    else:
        expected = EXPECT_ANSWER
    if ambiguous:
        provenance = PROVENANCE_AMBIGUOUS
    if _CONSEQUENTIAL_RE.search(text):
        epistemic = EPISTEMIC_CONSEQUENTIAL
    elif set(dimensions) & PERCEPTION_DIMENSIONS:
        epistemic = EPISTEMIC_INCIDENTAL
    elif set(dimensions) & CLAIM_DIMENSIONS or re.search(r"\b(?:rumou?rs?|heard)\b", text, re.IGNORECASE):
        epistemic = EPISTEMIC_NPC_CLAIM
    elif operation in {OP_ACT, OP_FOLLOW} and not (set(dimensions) & PERCEPTION_DIMENSIONS):
        epistemic = EPISTEMIC_AUTHORITATIVE
    else:
        epistemic = EPISTEMIC_UNKNOWN

    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    interlocutor = _clean(social.get("npc_id"), limit=80) if isinstance(social, Mapping) else ""
    if not interlocutor:
        slot = focus.get(SLOT_INTERLOCUTOR)
        if isinstance(slot, Mapping) and request_kind in {REQUEST_INQUIRY, REQUEST_SOCIAL_ACTION, REQUEST_CLARIFICATION}:
            if re.search(r"\b(?:you|your|them|they)\b", text, re.IGNORECASE) or set(dimensions) & CLAIM_DIMENSIONS:
                interlocutor = _clean(slot.get("id"), limit=80)
    subject = None
    if isinstance(discourse, DiscoursePointer) and discourse.type == "claim" and discourse.label:
        subject = discourse.label
    elif isinstance(target, TargetRef) and target.id_or_text:
        subject = target.id_or_text
    else:
        subject = text or None
    return ResolutionContract(
        contract_id=_contract_id(turn_index, text),
        turn_index=turn_index,
        request_kind=request_kind,
        operation=operation,
        target_ref=target,
        interlocutor_id=interlocutor or None,
        conversational_subject=_clean(subject, limit=160) or None,
        dimension=dimensions[0] if dimensions else None,
        dimensions=dimensions,
        expected_resolution=expected,
        epistemic_mode=epistemic,
        discourse_ref=discourse,
        referent_provenance=provenance,
        ambiguous=ambiguous or provenance == PROVENANCE_AMBIGUOUS,
        raw_input=text,
    )


def generation_projection(contract: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Compact model-facing constraint. Internal bookkeeping stays off the prompt."""
    if not isinstance(contract, Mapping) or not contract.get("contract_id"):
        return None
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    dims = [str(item) for item in (contract.get("dimensions") or []) if str(item).strip()]
    target_text = _clean(target.get("id_or_text"), limit=80) or "the established target"
    if contract.get("ambiguous") or contract.get("expected_resolution") == EXPECT_CLARIFICATION and contract.get(
        "referent_provenance"
    ) in {PROVENANCE_AMBIGUOUS, PROVENANCE_UNRESOLVED}:
        constraint = (
            "The referent is not unambiguous. Ask which one is meant, or say it cannot be identified. Do not guess."
        )
    elif contract.get("epistemic_mode") == EPISTEMIC_CONSEQUENTIAL:
        constraint = "This asks for protected information. Refuse or defer. Do not invent hidden or consequential truth."
    else:
        point = ", ".join(dims) if dims else str(contract.get("operation") or "request")
        expected = str(contract.get("expected_resolution") or "answer").replace("_", " ")
        article = "an" if expected[:1].lower() in "aeiou" else "a"
        constraint = (
            f"Resolve {contract.get('operation')} for {target_text} ({point}). "
            f"The reply must be {article} {expected}, a real inability, a refusal, a condition, "
            "or a clarification. Do not replace that request with an unrelated scene description."
        )
    return {
        "request_kind": contract.get("request_kind"),
        "operation": contract.get("operation"),
        "target": target_text if target else None,
        "interlocutor": contract.get("interlocutor_id"),
        "subject": contract.get("conversational_subject"),
        "dimension": contract.get("dimension"),
        "dimensions": dims,
        "expected_resolution": contract.get("expected_resolution"),
        "authority": contract.get("epistemic_mode"),
        "constraint": constraint,
    }


def _dimension_covered(text: str, dimension: str) -> bool:
    pattern = _RESPONSE_CUES.get(dimension)
    return bool(pattern and pattern.search(text))


def assess_contract_satisfaction(text: str | None, contract: Mapping[str, Any] | None) -> dict[str, Any]:
    """Decide whether player-visible text meets the contract. This is not a generator."""
    if not isinstance(contract, Mapping) or not contract.get("contract_id"):
        return {"status": "not_applicable", "reasons": ["no_contract"]}
    body = _clean(text, limit=2000)
    if not body:
        return {"status": "unsatisfied", "reasons": ["empty_text"], "contract_id": contract.get("contract_id")}
    reasons: list[str] = []
    if contract.get("ambiguous") or (
        contract.get("expected_resolution") == EXPECT_CLARIFICATION
        and contract.get("referent_provenance") in {PROVENANCE_AMBIGUOUS, PROVENANCE_UNRESOLVED}
    ):
        if _LEGITIMATE_RE.search(body) or re.search(r"\b(?:which|do you mean|cannot be identified)\b", body, re.IGNORECASE):
            return {
                "status": "legitimate_nonresolution",
                "reasons": ["clarification_or_inability"],
                "contract_id": contract.get("contract_id"),
            }
        reasons.append("clarification_missing")
        return {"status": "unsatisfied", "reasons": reasons, "contract_id": contract.get("contract_id")}
    if contract.get("epistemic_mode") == EPISTEMIC_CONSEQUENTIAL:
        if _LEGITIMATE_RE.search(body) or re.search(r"\b(?:won't|will not|cannot|can't|no one|not something)\b", body, re.IGNORECASE):
            return {
                "status": "legitimate_nonresolution",
                "reasons": ["consequential_refused"],
                "contract_id": contract.get("contract_id"),
            }
        return {
            "status": "unsatisfied",
            "reasons": ["consequential_not_refused"],
            "contract_id": contract.get("contract_id"),
        }
    dims = [str(item) for item in (contract.get("dimensions") or []) if str(item).strip()]
    if not dims and contract.get("dimension"):
        dims = [str(contract.get("dimension"))]
    operation = str(contract.get("operation") or "")
    if operation in {OP_ACT, OP_FOLLOW, OP_CONFIRM} and not dims:
        if _ACTION_CUE_RE.search(body) or _LEGITIMATE_RE.search(body):
            status = "satisfied" if _ACTION_CUE_RE.search(body) else "legitimate_nonresolution"
            return {"status": status, "reasons": [status], "contract_id": contract.get("contract_id")}
        reasons = ["action_outcome_missing"]
        if _LONG_VISUAL_RE.search(body):
            reasons.append("generic_scene_replaced_action")
        return {"status": "unsatisfied", "reasons": reasons, "contract_id": contract.get("contract_id")}
    if not dims:
        return {"status": "unchecked", "reasons": ["no_dimension"], "contract_id": contract.get("contract_id")}
    covered = [dim for dim in dims if _dimension_covered(body, dim)]
    if dims == [DIM_APPEARANCE] or (len(dims) == 1 and dims[0] == DIM_APPEARANCE):
        if covered or (len(body.split()) >= 12 and not _LEGITIMATE_RE.search(body)):
            return {"status": "satisfied", "reasons": ["appearance_addressed"], "contract_id": contract.get("contract_id")}
        if _LEGITIMATE_RE.search(body):
            return {
                "status": "legitimate_nonresolution",
                "reasons": ["legitimate_nonresolution"],
                "contract_id": contract.get("contract_id"),
            }
    if covered and len(covered) == len(dims):
        return {"status": "satisfied", "reasons": [f"covered:{dim}" for dim in covered], "contract_id": contract.get("contract_id")}
    if covered:
        return {
            "status": "partial",
            "reasons": [f"covered:{dim}" for dim in covered] + [f"missing:{dim}" for dim in dims if dim not in covered],
            "contract_id": contract.get("contract_id"),
        }
    if _LEGITIMATE_RE.search(body):
        return {
            "status": "legitimate_nonresolution",
            "reasons": ["legitimate_nonresolution"],
            "contract_id": contract.get("contract_id"),
        }
    if set(dims) & {DIM_SOUND, DIM_SMELL, DIM_WEAR, DIM_USE, DIM_CHANGE, DIM_SOURCE, DIM_CONFIDENCE} and _LONG_VISUAL_RE.search(body):
        reasons.append("generic_scene_replaced_dimension")
    if operation in {OP_ACT, OP_FOLLOW, OP_CONFIRM} and _LONG_VISUAL_RE.search(body):
        reasons.append("generic_scene_replaced_action")
    reasons.append("dimension_not_addressed")
    return {"status": "unsatisfied", "reasons": reasons, "contract_id": contract.get("contract_id")}


def contract_trace(
    contract: Mapping[str, Any] | None,
    *,
    focus: Mapping[str, Any] | None = None,
    obligation_kind: str | None = None,
    authority_route: str | None = None,
    semantic: Mapping[str, Any] | None = None,
    retry_preserved: bool = False,
) -> dict[str, Any]:
    return {
        "event": "resolution_contract",
        "raw_input": (contract or {}).get("raw_input") if isinstance(contract, Mapping) else None,
        "resolution_contract": generation_projection(contract),
        "referent_provenance": (contract or {}).get("referent_provenance") if isinstance(contract, Mapping) else None,
        "discourse_ref": (contract or {}).get("discourse_ref") if isinstance(contract, Mapping) else None,
        "discourse_focus": focus_summary(focus),
        "interaction_obligation_kind": obligation_kind,
        "authority_route": authority_route,
        "semantic_result": dict(semantic) if isinstance(semantic, Mapping) else None,
        "retry_preserved": bool(retry_preserved),
    }
