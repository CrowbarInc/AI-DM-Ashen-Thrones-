"""Contract-first bridge for the unparsed adjudication arm.

Ordinary gameplay that reaches this arm already has an authoritative
Resolution Contract. Specialized resolvers are chosen from that contract.
They do not read a segmented trailing clause as a second semantic owner.

Category A exclusions are the only pre-contract routes this cycle leaves
alone. They are not chat sentences.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from game.adjudication import resolve_adjudication_query
from game.interaction_context import _looks_like_place_existence_question
from game.player_commitment import EXECUTED_NOW

# Named, enumerable, testable. A chat sentence is not on this list.
CATEGORY_A_EXCLUSIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "session_administration",
        "entry": "HTTP session administration, not /api/chat",
        "examples": ("snapshot", "load", "reset", "new_campaign", "response_mode", "editors"),
    },
    {
        "id": "initiative_status_line",
        "entry": "api.action roll_initiative",
        "examples": ("roll_initiative",),
    },
    {
        "id": "end_turn_status_line",
        "entry": "api.action end_turn with no enemy",
        "examples": ("end_turn",),
    },
    {
        "id": "campaign_start_cue",
        "entry": "api._is_campaign_start_turn_request",
        "examples": ("start the campaign", "begin the campaign"),
    },
)

CATEGORY_A_IDS = tuple(row["id"] for row in CATEGORY_A_EXCLUSIONS)

RESOLVER_FAMILIES = (
    "earshot",
    "nearby_presence",
    "place_location",
    "feasibility",
    "state_query",
    "roll_mechanical",
    "generic_adjudication",
)

_SOCIAL_PRIMARY_RE = re.compile(
    r"\b(?:i\s+ask|ask\s+the|ask\s+(?:him|her|them|you)|have\s+you\s+heard|"
    r"did\s+you\s+hear|what\s+have\s+you\s+heard|thank\s+you|ask(?:s|ed|ing)?)\b",
    re.IGNORECASE,
)
_PRESENCE_RE = re.compile(
    r"\b(?:who(?:'s| is)\s+(?:nearby|here|around)|"
    r"anyone(?:\s+else)?\s+(?:nearby|here|around|in\s+earshot)|"
    r"in\s+earshot|who\s+can\s+hear|"
    r"listen(?:ing)?\s+for\s+anyone|"
    r"is\s+anyone(?:\s+else)?\s+(?:nearby|here|in\s+earshot))\b",
    re.IGNORECASE,
)
_PLACE_RE = re.compile(
    r"\b(?:supplies|shelter|tavern|inn|lodging)\b",
    re.IGNORECASE,
)
_ROLL_RE = re.compile(
    r"\b(?:sleight of hand|skill\s+check|saving\s+throw|\bdc\b|"
    r"need(?:ed)?\s+(?:to\s+)?(?:a\s+)?roll|roll\s+needed|does\s+this\s+need|"
    r"is\s+a\s+roll\s+needed|need\s+a\s+roll)\b",
    re.IGNORECASE,
)
_STATE_RE = re.compile(
    r"\b(?:what\s+actions?\s+are\s+available|where\s+is\s+my|what\s+is\s+my|how\s+many)\b",
    re.IGNORECASE,
)
_FEASIBILITY_RE = re.compile(
    r"\b(?:can\s+i|could\s+i|would\s+i|would\s+the|is\s+it\s+possible|how\s+far|distance|\barmed\b)\b",
    re.IGNORECASE,
)
_ATTACK_RE = re.compile(r"\b(?:attack|strike|stab|slash|smite)\b", re.IGNORECASE)
_TRAVEL_RE = re.compile(
    r"\b(?:go|walk|head|travel|leave|return)\b|\bfollow\s+the\s+(?:road|path|trail|way)\b",
    re.IGNORECASE,
)
# A direct "where is the X" question. Not a noun list. "where is my" stays a state query.
_DIRECT_WHERE_RE = re.compile(
    r"\bwhere(?:'s| is| are)\s+(?:the|a|an|that|this)\b",
    re.IGNORECASE,
)
_DIRECT_TRAVEL_INQUIRY_RE = re.compile(
    r"\bwhere\s+does\s+(?:the|this|that)\s+\w+\s+(?:lead|go)\b",
    re.IGNORECASE,
)
# Current-scene orientation. "Where is the harbor" stays a place question.
_DEICTIC_SCENE_ORIENTATION_RE = re.compile(
    r"\bwhere\s+(?:am\s+i|are\s+we)\b|\bwhere\s+is\s+this(?:\s+place)?\b",
    re.IGNORECASE,
)
_DESCRIBE_SCENE_RE = re.compile(r"\bdescribe\b", re.IGNORECASE)
_SOCIAL_INQUIRY_CUE_RE = re.compile(
    r"\?|\b(?:what|who|how|whether|please|ask|inquire)\b|[\"“]"
    r"|\bwhere\s+(?:is|are|'s)\s+(?:the|a|an|that|this|you|he|she|they)\b",
    re.IGNORECASE,
)
_DIRECT_OBJECT_READING_RE = re.compile(
    r"\bwhat\s+does\s+((?:the|this|that)\s+[a-z]+(?:\s+[a-z]+){0,3})\s+say\b",
    re.IGNORECASE,
)
_THIRD_PERSON_SPEECH_RE = re.compile(
    r"\b(?:he|she|they)\s+(?:speak|speaks|speaking|say|says|said|ask|asks|asked|"
    r"reply|replies|replied|answer|answers)\b"
    r"|\bthe\s+[a-z]+(?:\s+[a-z]+){0,3}\s+(?:speaks|says|said|asks|asked|replies|replied|answers)\b",
    re.IGNORECASE,
)
_PLAYER_ADDRESS_FRAME_RE = re.compile(
    r"\b(?:i\s+(?:approach|ask|tell|say|speak|address|call)|my\s+voice)\b",
    re.IGNORECASE,
)
_SECOND_PERSON_RE = re.compile(r"\byou(?:r|rself)?\b", re.IGNORECASE)
_SPAN_QUESTION_RE = re.compile(
    r"\?|\b(?:do|did|can|could|have|will|would|what|who|where|how|whether)\b",
    re.IGNORECASE,
)
# Adjudication families the contract may name. Selection reads this set.
# It does not rediscover the family from raw tokens.
_ADJUDICATION_SUBJECTS = frozenset(
    {
        "earshot",
        "nearby_presence",
        "place_location",
        "feasibility",
        "state_query",
        "roll_mechanical",
    }
)


def category_a_ids() -> tuple[str, ...]:
    return CATEGORY_A_IDS


def is_category_a(exclusion_id: str | None) -> bool:
    return str(exclusion_id or "").strip() in CATEGORY_A_IDS


def construction_source(contract: Mapping[str, Any] | None) -> str:
    """deterministic or structured_interpretation. Existing construction fields only."""
    construction = contract.get("construction") if isinstance(contract, Mapping) else None
    if not isinstance(construction, Mapping):
        return "deterministic"
    if (
        str(construction.get("proposal_source") or "") == "model_assisted"
        and not construction.get("model_proposal_rejected")
        and construction.get("model_interpreter_invoked")
    ):
        return "structured_interpretation"
    return "deterministic"


def contract_authorizes_specialized_resolution(contract: Mapping[str, Any] | None) -> bool:
    """True only when an ordinary-gameplay contract already exists."""
    if not isinstance(contract, Mapping):
        return False
    if not str(contract.get("contract_id") or "").strip():
        return False
    return bool(str(contract.get("operation") or "").strip())


def direct_feasibility_question(text: str | None) -> bool:
    """A modal possibility question, not an addressed social ask."""
    raw = str(text or "")
    if _explicit_social_address(raw) or player_voiced_interrogative(raw):
        return False
    return bool(_FEASIBILITY_RE.search(raw) and "?" in raw)


def _explicit_social_address(raw: str) -> bool:
    """Speech addressed to someone. Place and combat words inside it are content."""
    if _SOCIAL_PRIMARY_RE.search(raw):
        return True
    return bool(
        re.search(
            r"\b(?:tell|order|command|persuade|convince|speak(?:ing)?\s+to|talk(?:ing)?\s+to)\b",
            raw,
            re.IGNORECASE,
        )
    )


def _speech_spans(raw: str) -> list[tuple[str, str]]:
    """Opening-quote spans, including a quote the player never closed."""
    spans: list[tuple[str, str]] = []
    pos = 0
    while pos < len(raw):
        opened = re.search(r'["“]', raw[pos:])
        if not opened:
            break
        open_at = pos + opened.start()
        content_at = pos + opened.end()
        closed = re.search(r'["”]', raw[content_at:])
        if closed:
            content = raw[content_at : content_at + closed.start()]
            pos = content_at + closed.end()
        else:
            content = raw[content_at:]
            pos = len(raw)
        spans.append((raw[:open_at], content))
    return spans


def player_voiced_interrogative(text: str | None) -> bool:
    """Quoted question the player is speaking to someone.

    A quote attributed to another speaker is their line, not the player's
    request. Topic words inside the player's own question stay topic words.
    """
    raw = str(text or "")
    for preceding, span in _speech_spans(raw):
        if not span or not _SPAN_QUESTION_RE.search(span):
            continue
        window = preceding[-220:]
        third = list(_THIRD_PERSON_SPEECH_RE.finditer(window))
        player = list(_PLAYER_ADDRESS_FRAME_RE.finditer(window))
        attributed = bool(third) and (not player or third[-1].start() > player[-1].start())
        if attributed:
            continue
        if player or _SECOND_PERSON_RE.search(span):
            return True
    return False


def social_interaction_frame(
    text: str | None,
    *,
    operation: str,
    explicit_addressee: bool = False,
) -> bool:
    """Addressed social ask. Inherited scene focus is not an addressee."""
    raw = str(text or "")
    operation = str(operation or "").strip().lower()
    if operation not in {"ask", "repeat"}:
        return False
    if _explicit_social_address(raw) or player_voiced_interrogative(raw):
        return True
    return bool(explicit_addressee)


def structural_interaction_frame(
    text: str | None,
    *,
    operation: str,
    commitment: str,
    explicit_addressee: bool = False,
) -> str:
    """Implementation label for the player's structural frame. Not a contract field."""
    raw = str(text or "")
    operation = str(operation or "").strip().lower()
    commitment = str(commitment or "").strip()
    if social_interaction_frame(raw, operation=operation, explicit_addressee=explicit_addressee):
        return "social_ask"
    if operation == "perceive":
        return "perception"
    if operation == "inspect":
        return "inspection"
    if operation in {"act", "follow"} and commitment == EXECUTED_NOW:
        if _ATTACK_RE.search(raw):
            return "combat_action"
        if operation == "follow" or _TRAVEL_RE.search(raw):
            return "committed_movement"
        return "world_action"
    if operation == "ask" and (
        _DIRECT_WHERE_RE.search(raw)
        or _PLACE_RE.search(raw)
        or _looks_like_place_existence_question(raw)
    ):
        return "direct_place"
    if operation == "ask" and _PRESENCE_RE.search(raw):
        return "direct_presence"
    if operation == "ask" and _FEASIBILITY_RE.search(raw):
        return "direct_feasibility"
    if operation == "ask" and _DIRECT_TRAVEL_INQUIRY_RE.search(raw):
        return "direct_travel"
    if operation == "ask" and "?" in raw:
        return "direct_inquiry"
    if commitment != EXECUTED_NOW:
        return "uncommitted"
    return "unspecified"


def _ask_names_social_subject(raw: str) -> bool:
    """Informational questions and requests name a social subject.

    Current-scene orientation, a bare description, and unmatched statements do not.
    Place, presence, and feasibility questions are classified before this fallback.
    """
    if _DEICTIC_SCENE_ORIENTATION_RE.search(raw) and not re.search(r"\b(?:ask|inquire)\b", raw, re.IGNORECASE):
        return False
    if _DESCRIBE_SCENE_RE.search(raw) and not re.search(r"\b(?:ask|inquire|please)\b|[\"“]", raw):
        return False
    return bool(_SOCIAL_INQUIRY_CUE_RE.search(raw))


def _direct_object_reading(raw: str) -> bool:
    """'What does the inscription say' is a reading, not an addressed person."""
    match = _DIRECT_OBJECT_READING_RE.search(raw)
    if not match:
        return False
    from game.incidental_entity import referential_person_nominal

    return referential_person_nominal(match.group(1)) is None


def _topical_resolution_subject(
    raw: str,
    *,
    operation: str,
    proposed: str,
    commitment: str,
    dimension: str,
) -> str:
    """Topic and action labels. Social address is applied by the caller."""
    # An uncommitted plan is not a place, presence, or feasibility question,
    # even when the plan mentions those words.
    if commitment != EXECUTED_NOW and "?" not in raw:
        if operation == "ask" or proposed in {"act", "follow", "ask"}:
            return "social" if operation == "ask" else "action"
        return "action"
    if operation in {"ask", "perceive", "inspect"}:
        presence = bool(_PRESENCE_RE.search(raw)) or (
            operation == "perceive" and dimension == "sound" and bool(re.search(r"\banyone\b", raw, re.IGNORECASE))
        )
        if presence:
            if re.search(r"\bearshot\b|\bwho can hear\b|\blisten", raw, re.IGNORECASE):
                return "earshot"
            return "nearby_presence"
    if operation == "ask" and _STATE_RE.search(raw):
        return "state_query"
    if operation == "ask" and (
        _PLACE_RE.search(raw)
        or _looks_like_place_existence_question(raw)
        or (_DIRECT_WHERE_RE.search(raw) and not _STATE_RE.search(raw))
    ):
        return "place_location"
    if operation == "ask" and _ROLL_RE.search(raw):
        return "roll_mechanical"
    if operation == "ask" and _FEASIBILITY_RE.search(raw):
        return "feasibility"
    if operation == "ask" and _DIRECT_TRAVEL_INQUIRY_RE.search(raw):
        return "travel"
    if operation == "ask" and _direct_object_reading(raw):
        return "perception"
    if operation in {"inspect", "perceive"}:
        return "perception"
    if operation in {"act", "follow", "confirm"} and commitment == EXECUTED_NOW:
        if _ATTACK_RE.search(raw):
            return "combat"
        from game.intent_parser import is_qualified_pursuit_shaped

        pursuit = is_qualified_pursuit_shaped(raw)
        if operation == "follow" or pursuit:
            if pursuit and not _TRAVEL_RE.search(raw):
                return "perception"
        if operation == "follow" or _TRAVEL_RE.search(raw):
            return "travel"
        return "world_action"
    if operation == "repeat" or (operation == "ask" and _ask_names_social_subject(raw)):
        return "social"
    if operation == "ask":
        return "unspecified"
    return "unspecified"


def resolve_subject_coherence(
    text: str | None,
    *,
    operation: str,
    proposed_operation: str | None,
    commitment: str,
    dimension: str | None = None,
    explicit_addressee: bool = False,
) -> tuple[str, str]:
    """Apply structural frame to a topical subject before the contract is authoritative.

    Unambiguous addressed speech canonicalizes a direct-world topic to social.
    A direct question with no address keeps the topical subject. Ambiguous
    operation conflicts stay on the existing abstention path and are not forced.
    """
    raw = str(text or "")
    operation = str(operation or "").strip().lower()
    proposed = str(proposed_operation or operation or "").strip().lower()
    commitment = str(commitment or "").strip()
    dimension = str(dimension or "").strip().lower()
    topical = _topical_resolution_subject(
        raw,
        operation=operation,
        proposed=proposed,
        commitment=commitment,
        dimension=dimension,
    )
    addressed = social_interaction_frame(raw, operation=operation, explicit_addressee=explicit_addressee)
    if addressed:
        if topical == "social":
            return "social", "accepted"
        return "social", "canonicalized"
    return topical, "accepted"


def derive_resolution_subject(
    text: str | None,
    *,
    operation: str,
    proposed_operation: str | None,
    commitment: str,
    dimension: str | None = None,
    explicit_addressee: bool = False,
) -> str:
    """Name the resolution subject while the contract is being built.

    This is the interpretation step. After the contract exists, resolver
    selection reads ``construction.resolution_subject`` and does not run these
    checks again.
    """
    subject, _status = resolve_subject_coherence(
        text,
        operation=operation,
        proposed_operation=proposed_operation,
        commitment=commitment,
        dimension=dimension,
        explicit_addressee=explicit_addressee,
    )
    return subject


def select_resolver_family(contract: Mapping[str, Any] | None) -> str | None:
    """Choose an adjudication family from the contract subject only.

    Raw player text is not read here. A missing subject selects nothing.
    """
    if not contract_authorizes_specialized_resolution(contract):
        return None
    assert isinstance(contract, Mapping)
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    subject = str(construction.get("resolution_subject") or "").strip()
    if subject in _ADJUDICATION_SUBJECTS:
        return subject
    return None


def resolve_selected_family(
    family: str | None,
    contract: Mapping[str, Any] | None,
    *,
    scene: dict,
    session: dict,
    world: dict,
    character: dict,
    has_active_interaction: bool = False,
) -> dict | None:
    """Run one already-selected resolver. Refuses to run without a contract.

    The contract operation and addressee are not rewritten. A resolver that
    cannot answer returns None so the caller can use contract-aware generation
    or nonresolution.
    """
    if family not in RESOLVER_FAMILIES:
        return None
    if not contract_authorizes_specialized_resolution(contract):
        return None
    assert isinstance(contract, Mapping)
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    subject = str(construction.get("resolution_subject") or "").strip()
    operation = str(contract.get("operation") or "").strip().lower()
    # A contract that already named a non-adjudication subject cannot be
    # overridden by a caller-supplied place, presence, or earshot family.
    if family in {"earshot", "nearby_presence", "place_location"} and (
        subject == "social" or (operation == "ask" and subject not in _ADJUDICATION_SUBJECTS)
    ):
        return None
    text = str(contract.get("raw_input") or "").strip()
    if not text:
        return None
    result = resolve_adjudication_query(
        text,
        scene=scene,
        session=session,
        world=world,
        character=character,
        has_active_interaction=has_active_interaction,
        resolver_family=family,
    )
    if not isinstance(result, dict):
        return None
    # The resolver reports facts. It does not replace the contract's operation.
    result = dict(result)
    result["resolver_family"] = family
    result["contract_id"] = str(contract.get("contract_id") or "")
    result["contract_operation"] = str(contract.get("operation") or "")
    result["contract_interlocutor_id"] = str(contract.get("interlocutor_id") or "")
    return result
