"""Non-authoritative interpretation proposals and canonicalize-or-abstain validation.

A proposal records what an interpreter thinks the player meant. It does not
create entities, discourse slots, claims, or world facts. Only a validated
result may be copied into a Resolution Contract, and only that result may
later be committed to discourse.

Future model output uses this same validator. Self-reported confidence is
advisory and never creates a canonical identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import re
from typing import Any, Mapping, Sequence

from game.resolution_contract import (
    OP_ACT,
    OP_ASK,
    OP_CONFIRM,
    OP_FOLLOW,
    OP_INSPECT,
    OP_PERCEIVE,
    OP_REPEAT,
    PROVENANCE_EXPLICIT,
    PROVENANCE_INHERITED,
)

SOURCE_FAST_PATH = "deterministic_fast_path"
SOURCE_DISCOURSE = "discourse_inheritance"
SOURCE_MODEL = "model_assisted"
SOURCE_CLARIFICATION = "clarification_recovery"

STATUS_VALIDATED = "validated"
STATUS_ABSTAINED = "abstained"

OP_UNRESOLVED = "unresolved"

REASON_TARGET_NOT_CANONICAL = "target_not_canonical"
REASON_AMBIGUOUS_REFERENT = "ambiguous_referent"
REASON_MALFORMED_SPAN = "malformed_target_span"
REASON_CONFLICTING_OPERATIONS = "conflicting_operations"
REASON_UNRESOLVED_COMPOUND = "unresolved_compound_intent"
REASON_UNKNOWN_INTERLOCUTOR = "unknown_interlocutor"
REASON_INSUFFICIENT_DISCOURSE = "insufficient_discourse_context"
REASON_UNSUPPORTED_OPERATION = "unsupported_operation"
REASON_NONEXISTENT_REFERENT = "nonexistent_referent"
REASON_INCOMPLETE_SEMANTICS = "incomplete_semantic_structure"
REASON_UNKNOWN_DIMENSION = "unknown_dimension"

KNOWN_DIMENSIONS = frozenset(
    {
        "appearance",
        "sound",
        "smell",
        "wear",
        "use",
        "change",
        "source",
        "confidence",
        "location",
        "time",
        "next_step",
        "content",
        "interpretation",
    }
)
_DIMENSION_ALIASES = {
    "certainty": "confidence",
    "surety": "confidence",
    "purpose": "use",
    "function": "use",
    "procedure": "next_step",
    "requirement": "next_step",
    "requirements": "next_step",
    "recency": "time",
    "substance": "content",
    "statement": "content",
}

_ELLIPSIS_STOP = frozenset(
    {
        "who", "where", "when", "how", "what", "why", "from", "and", "but", "so", "then",
        "if", "i", "do", "did", "the", "a", "an", "to", "of", "recently", "ago", "sure",
        "certain", "long", "just", "about", "that", "this", "it", "you", "your",
    }
)
_REFERENTIAL_ACTION_SHAPE_RE = re.compile(
    r"\b(?:do|take|follow|try)\s+(?:that|this|the|his|her|their)\s+(?:step|lead|suggestion|advice)\b"
    r"|\b(?:do|take|follow|try)\s+(?:\w+\s+){1,6}(?:that|this|the|his|her|their)\s+(?:step|lead|suggestion|advice)\b"
    r"|\b(?:do|take|follow|try)\s+what\b(?:\s+\w+){0,4}\s+(?:suggest\w*|said|told\w*|meant|advis\w*)"
    r"|\btry\s+(?:it|that|this)\b",
    re.IGNORECASE,
)
_PERSON_POINTER_RE = re.compile(r"\b(?:him|her|them)\b", re.IGNORECASE)
_OBJECT_POINTER_RE = re.compile(r"\b(?:it|that|this)\b", re.IGNORECASE)

KNOWN_OPERATIONS = frozenset(
    {OP_PERCEIVE, OP_INSPECT, OP_ASK, OP_REPEAT, OP_CONFIRM, OP_FOLLOW, OP_ACT, OP_UNRESOLVED}
)
_FAMILY_INSPECT = "inspect"
_FAMILY_ASK = "ask"
_FAMILY_ACT = "act"

_INSPECT_FAMILY_RE = re.compile(
    r"\b(?:inspect|examine|search|check|study|investigat(?:e|es|ed|ing))\b"
    r"|\blook\s+(?:at|for|over)\b"
    r"|\blook(?:\s+\w+){0,3}\s+over\b",
    re.IGNORECASE,
)
_ASK_FAMILY_RE = re.compile(r"\b(?:ask|inquire)\b", re.IGNORECASE)
_ACT_FAMILY_RE = re.compile(
    r"\b(?:knock|push|pull|break|climb|enter)\b|\bopen\s+(?:the|a|an|it|that|this|up)\b|\bi take that step\b",
    re.IGNORECASE,
)
_PRONOUN_HEADS = frozenset({"it", "its", "that", "this", "them", "they", "him", "her"})
_NOMINAL_STOP = frozenset(
    {"the", "a", "an", "of", "on", "to", "and", "or", "at", "for", "with", "from", "into", "over"}
)
_BRIDGE = "unscoped_player_nominal"

# Continuation 11 replaces this. Abstention currently reuses the existing
# clarification contract shape so a rejected parse cannot become a confident
# target. It is not a new player-facing line.
COMPATIBILITY_BRIDGE = (
    "unscoped_player_nominal remains only when a caller omits the referent index "
    "(canonical_referents is None). Ordinary /api/chat supplies the scene catalog, "
    "so a typed noun is not an entity. The omitted-index case still cannot use a "
    "bare preposition capture, a clause span, or an unresolved compound. "
    "It is not used to recover from model-interpretation failure."
)


def elliptical_probe_dimension(text: str) -> str | None:
    """Short follow-up whose subject is missing from the words themselves.

    A content nominal keeps this from firing. "Who from?" is a probe.
    "Who told you about the toll?" is not.
    """
    raw = re.sub(r"[?!.]+", "", str(text or "")).strip()
    tokens = re.findall(r"[a-z']+", raw.lower())
    if tokens and tokens[0] in {"and", "but", "so", "then"}:
        tokens = tokens[1:]
    if not tokens or len(tokens) > 6:
        return None
    content = [token for token in tokens if token not in _ELLIPSIS_STOP and len(token) > 2]
    if content:
        return None
    head = tokens[0]
    rest = set(tokens[1:])
    if head == "who":
        return "source"
    if head == "where":
        return "location"
    if head == "when":
        return "time"
    if head == "how" and rest & {"recently", "ago", "long", "soon"}:
        return "time"
    if head == "how" and rest & {"sure", "certain", "confident"}:
        return "confidence"
    if head == "if":
        return "conditional"
    if head in {"what", "why", "how"}:
        return "unspecified"
    return None


def referential_action_shape(text: str) -> bool:
    """A commitment to an earlier step, lead, or suggestion. Not a phrase list."""
    return bool(_REFERENTIAL_ACTION_SHAPE_RE.search(str(text or "")))


def fast_path_semantic_gaps(
    proposal: InterpretationProposal,
    discourse_focus: Mapping[str, Any] | None,
    validation: InterpretationValidation,
) -> tuple[str, ...]:
    """Obligations the fast path still has not filled. A bound token is not enough."""
    if proposal.source not in {SOURCE_FAST_PATH, SOURCE_DISCOURSE}:
        return ()
    text = proposal.raw_input or ""
    gaps: list[str] = []
    target_type = validation.canonical_target_type or ""
    target_id = validation.canonical_target_id or ""
    probe = elliptical_probe_dimension(text)
    bound = bool(target_id or proposal.referenced_claim_id or proposal.referenced_action_id)
    if probe and not bound:
        gaps.append("elliptical_subject")
    if referential_action_shape(text) and target_type not in {"action", "lead"}:
        gaps.append("referential_action")
    from game.resolution_contract import first_obvious_dimension

    obvious = first_obvious_dimension(text)
    proposed_dims = {item for item in (proposal.dimension, *proposal.dimensions) if item}
    if obvious and obvious not in proposed_dims:
        gaps.append("requested_dimension")
    unbound_content = bool(
        obvious == "content"
        and re.search(
            r"\bwhat\s+(?:did|does)\s+(?:he|she|it|that|this)\s+(?:say|said|tell|told|report|write)\b"
            r"|\bwhat\s+was\s+written\s+(?:there|on\s+(?:it|that|this))\b"
            r"|\bwhat(?:'s| is)\s+written\s+on\s+(?:it|that|this)\b",
            text,
            re.IGNORECASE,
        )
    )
    if unbound_content:
        object_bound = bool(target_id) and target_type in {"object", "claim", "document"}
        person_bound = bool(proposal.interlocutor_id) and re.search(r"\b(?:he|she|him|her)\b", text, re.IGNORECASE)
        if not object_bound and not person_bound:
            gaps.append("content_referent")
    asks = bool(re.search(r"\bask\b", text, re.IGNORECASE)) or proposal.primary_operation == OP_ASK
    if asks and _PERSON_POINTER_RE.search(text) and _OBJECT_POINTER_RE.search(text):
        if not proposal.interlocutor_id:
            gaps.append("interlocutor")
        object_bound = bool(target_id) and target_type not in {"", "interlocutor"} and target_id != proposal.interlocutor_id
        if not object_bound:
            gaps.append("conversational_subject")
    return tuple(dict.fromkeys(gaps))


def fast_path_operation_families(text: str) -> tuple[str, ...]:
    """Operation families present in the utterance. Order is not precedence."""
    found: list[str] = []
    if _INSPECT_FAMILY_RE.search(text or ""):
        found.append(_FAMILY_INSPECT)
    if _ASK_FAMILY_RE.search(text or ""):
        found.append(_FAMILY_ASK)
    if _ACT_FAMILY_RE.search(text or ""):
        found.append(_FAMILY_ACT)
    return tuple(found)


def ask_governs_embedded_act(text: str | None) -> bool:
    """True when climb/open/inspect is the content of an ask, not a second act.

    "I ask the guard whether I can climb" is one social ask.
    "I open the door and ask" is not: the act is outside the ask.
    """
    raw = str(text or "")
    ask = _ASK_FAMILY_RE.search(raw)
    if not ask:
        return False
    other_starts = [
        match.start()
        for pattern in (_ACT_FAMILY_RE, _INSPECT_FAMILY_RE)
        if (match := pattern.search(raw))
    ]
    if not other_starts:
        return False
    other_at = min(other_starts)
    if other_at < ask.start():
        return False
    tail = raw[ask.end() :]
    if re.search(
        r"\b(?:and|then)\s+(?:i\s+)?(?:climb|open|knock|push|pull|break|enter|inspect|examine)\b",
        tail,
        re.IGNORECASE,
    ):
        return False
    span = raw[ask.start() :]
    return bool(re.search(r"\b(?:whether|if)\b", span, re.IGNORECASE) or '"' in span or "“" in span)


def operation_conflict(families: Sequence[str], text: str | None = None) -> bool:
    """True when two speech-act families are present and neither is established as primary."""
    if len(set(families)) < 2:
        return False
    if text and ask_governs_embedded_act(text):
        return False
    return True


def _quoted_spans(raw: str) -> list[str]:
    return re.findall(r"[\"“]([^\"”]*)", str(raw or ""))


def _strong_addressed_ask(raw: str) -> bool:
    """Explicit ask, or quoted interrogative speech. A bare question mark is not enough."""
    if _ASK_FAMILY_RE.search(raw):
        return True
    spans = _quoted_spans(raw)
    interrogative = any("?" in span for span in spans)
    speech = bool(
        re.search(
            r"\b(?:speak(?:ing)?|say(?:s|ing)?|said|told|tell(?:s|ing)?|address(?:ing|es)?)\b",
            raw,
            re.IGNORECASE,
        )
    )
    vocative = any(re.match(r"\s*[A-Za-z][^,]{0,40},", span) for span in spans)
    addressed = vocative or bool(re.search(r"\b(?:to|at)\s+(?:the\s+|a\s+|an\s+)?[a-z]", raw, re.IGNORECASE))
    return bool(interrogative and speech and addressed)


def _explicit_imperative(raw: str) -> bool:
    return bool(
        re.search(
            r"\b(?:tell|order|command)\s+(?:the\s+|a\s+|an\s+)?[a-z]",
            raw,
            re.IGNORECASE,
        )
    )


def _independent_act_outside_speech(raw: str) -> bool:
    if ask_governs_embedded_act(raw):
        return False
    act = _ACT_FAMILY_RE.search(raw)
    ask = _ASK_FAMILY_RE.search(raw)
    return bool(act and ask and act.start() < ask.start())


def _bare_approach(raw: str) -> bool:
    if not re.search(r"\bapproach(?:ing|es)?\b", raw, re.IGNORECASE):
        return False
    if _quoted_spans(raw) or '"' in raw or "“" in raw:
        return False
    return not bool(
        re.search(r"\b(?:ask|inquire|tell|speak|say|said|talk)\b", raw, re.IGNORECASE)
    )


_BARE_INSPECT_RE = re.compile(
    r"\b(?:inspect|examine|look at|check|study|investigat(?:e|es|ed|ing)|search)\b"
    r"|\blook(?:\s+\w+){0,3}\s+over\b",
    re.IGNORECASE,
)
_BARE_PERCEIVE_RE = re.compile(r"\b(?:listen|smell)\b", re.IGNORECASE)
_INFERENCE_FOLLOWUP_RE = re.compile(
    r"\b(?:what\s+(?:does|might|could).{0,60}(?:suggest|mean|tell\s+me|point\s+to)"
    r"|what\s+can\s+i\s+infer|does\s+.{0,50}(?:suggest|point\s+to))\b",
    re.IGNORECASE,
)


def _bare_inspection(raw: str) -> bool:
    if not _BARE_INSPECT_RE.search(raw):
        return False
    if _ASK_FAMILY_RE.search(raw) or _quoted_spans(raw):
        return False
    return True


def _bare_perception(raw: str) -> bool:
    if not _BARE_PERCEIVE_RE.search(raw):
        return False
    if _ASK_FAMILY_RE.search(raw) or _quoted_spans(raw) or _BARE_INSPECT_RE.search(raw):
        return False
    return True


def _bare_attack(raw: str) -> bool:
    if not re.search(r"\b(?:attack|strike|stab|slash|smite)\b", raw, re.IGNORECASE):
        return False
    if _ASK_FAMILY_RE.search(raw) or '"' in raw or "“" in raw:
        return False
    return True


def structural_coherence_operation(text: str | None, proposed: str | None) -> str | None:
    """Canonicalize an unambiguous structural contradiction. Otherwise abstain or leave it.

    Returns an operation, ``\"abstain\"``, or None when the proposal already agrees.
    """
    raw = str(text or "")
    proposed_operation = str(proposed or "")
    if proposed_operation == OP_INSPECT and _bare_inspection(raw) and _INFERENCE_FOLLOWUP_RE.search(raw):
        return None
    strong_ask = _strong_addressed_ask(raw)
    if strong_ask and _independent_act_outside_speech(raw):
        return "abstain"
    if strong_ask and proposed_operation in {OP_ACT, OP_FOLLOW, OP_INSPECT, OP_PERCEIVE, OP_CONFIRM}:
        return OP_ASK
    if _explicit_imperative(raw) and not strong_ask and proposed_operation in {OP_ACT, OP_INSPECT, OP_PERCEIVE}:
        return OP_ASK
    if _bare_approach(raw) and proposed_operation == OP_ASK:
        return OP_ACT
    if _bare_inspection(raw) and proposed_operation in {OP_ASK, OP_ACT}:
        return OP_INSPECT
    if _bare_perception(raw) and proposed_operation in {OP_ASK, OP_ACT, OP_INSPECT}:
        return OP_PERCEIVE
    if _bare_attack(raw) and proposed_operation in {OP_ASK, OP_INSPECT, OP_PERCEIVE}:
        return OP_ACT
    return None


def claim_target_identity(label: str | None, claim_id: str | None) -> str | None:
    """A claim id, once the proposition is too long to be an entity name.

    Short propositions stay readable. A previous response, or any clause-sized
    span, is not a canonical entity.
    """
    text = " ".join(str(label or "").split())
    ident = str(claim_id or "").strip()
    if ident and span_is_malformed(text):
        return ident
    return text or ident or None


def span_is_malformed(span: str | None) -> bool:
    """A clause, or a pronoun with trailing words, is not an object identity."""
    raw = " ".join(str(span or "").split())
    if not raw:
        return False
    tokens = re.findall(r"[A-Za-z0-9']+", raw)
    if not tokens:
        return False
    if tokens[0].lower() in _PRONOUN_HEADS and len(tokens) > 1:
        return True
    if len(tokens) > 6:
        return True
    if re.search(r"\b(?:and|try|trying|work|ask)\b", raw, re.IGNORECASE) and len(tokens) > 4:
        return True
    return False


def structural_inspection_subject(
    span: str | None,
    *,
    capture_kind: str,
    operation: str | None,
    raw_input: str | None = None,
) -> bool:
    """A bounded explicit inspect noun phrase may coordinate more than one nominal.

    This does not establish either nominal as a world entity. It only preserves
    the resolution subject long enough for state-backed inspection to answer it.
    Clauses, pronoun-headed spans, and action sequences remain malformed.
    """
    raw = " ".join(str(span or "").split())
    if operation != OP_INSPECT or capture_kind not in {"verb_object", "look_over"}:
        return False
    if raw_input is not None and not _INFERENCE_FOLLOWUP_RE.search(str(raw_input or "")):
        return False
    tokens = re.findall(r"[A-Za-z0-9'-]+", raw)
    if not 1 <= len(tokens) <= 14 or tokens[0].lower() in _PRONOUN_HEADS:
        return False
    if re.search(r"[?.!;:]", raw):
        return False
    if re.search(
        r"\b(?:ask|tell|say|suggest|mean|infer|know|think|try|trying|work|because|while|when|if)\b",
        raw,
        re.IGNORECASE,
    ):
        return False
    return bool(re.search(r"[A-Za-z]", raw))


def is_unscoped_player_nominal(span: str | None, *, capture_kind: str, has_determiner: bool) -> bool:
    """Short player nominal. A bare 'on duty' capture is not one."""
    raw = " ".join(str(span or "").split())
    if not raw or span_is_malformed(raw):
        return False
    if capture_kind == "preposition" and not has_determiner:
        return False
    if capture_kind not in {"preposition", "verb_object", "look_over", "what_does"}:
        return False
    words = [
        token
        for token in re.findall(r"[a-z0-9']+", raw.lower())
        if token not in _NOMINAL_STOP and token not in _PRONOUN_HEADS and len(token) > 1
    ]
    return 1 <= len(words) <= 4


def _normalized(value: str | None) -> str:
    stripped = re.sub(r"\b(?:the|a|an)\b", " ", str(value or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", stripped).strip()


@dataclass(frozen=True)
class CanonicalReferent:
    type: str
    id: str
    label: str
    source: str = "scene"
    aliases: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["aliases"] = list(self.aliases)
        return payload


@dataclass(frozen=True)
class InterpretationProposal:
    """Interpretation candidate. Constructing one mutates nothing."""

    raw_input: str
    source: str
    primary_operation: str | None = None
    supporting_operations: tuple[str, ...] = ()
    raw_target_text: str | None = None
    proposed_target_id: str | None = None
    target_capture: str = "none"
    has_determiner: bool = False
    interlocutor_id: str | None = None
    conversational_subject: str | None = None
    dimension: str | None = None
    dimensions: tuple[str, ...] = ()
    expected_resolution: str | None = None
    referenced_claim_id: str | None = None
    referenced_action_id: str | None = None
    referenced_inspected_id: str | None = None
    confidence: str | None = None
    clarification_required: bool = False
    ambiguous: bool = False
    operation_conflict: bool = False
    notes: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["supporting_operations"] = list(self.supporting_operations)
        payload["dimensions"] = list(self.dimensions)
        return payload


@dataclass(frozen=True)
class InterpretationValidation:
    status: str
    reason: str | None
    failed_fields: tuple[str, ...]
    clarification_required: bool
    model_interpretation_appropriate: bool
    canonical_target_id: str | None
    canonical_target_label: str | None
    canonical_target_type: str | None
    canonical_basis: str | None
    authoritative_operation: str | None
    discourse_commit_allowed: bool
    compatibility_bridge: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failed_fields"] = list(self.failed_fields)
        return payload


def _canonicalize_dimension(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    return _DIMENSION_ALIASES.get(raw, raw)


def proposal_from_mapping(payload: Mapping[str, Any]) -> InterpretationProposal:
    """Build a proposal from untrusted input, including a future model payload."""
    supporting = payload.get("supporting_operations") or ()
    dimensions = payload.get("dimensions") or ()
    canon_dims: list[str] = []
    for item in dimensions:
        canon = _canonicalize_dimension(str(item))
        if canon and canon not in canon_dims:
            canon_dims.append(canon)
    primary_dimension = _canonicalize_dimension(str(payload.get("dimension") or "")) or None
    if primary_dimension and primary_dimension not in canon_dims:
        canon_dims.insert(0, primary_dimension)
    return InterpretationProposal(
        raw_input=str(payload.get("raw_input") or ""),
        source=str(payload.get("source") or SOURCE_MODEL),
        primary_operation=_blank(payload.get("primary_operation")),
        supporting_operations=tuple(str(item) for item in supporting if str(item).strip()),
        raw_target_text=_blank(payload.get("raw_target_text")),
        proposed_target_id=_blank(payload.get("proposed_target_id")),
        target_capture=str(payload.get("target_capture") or "model"),
        has_determiner=bool(payload.get("has_determiner")),
        interlocutor_id=_blank(payload.get("interlocutor_id")),
        conversational_subject=_blank(payload.get("conversational_subject")),
        dimension=primary_dimension,
        dimensions=tuple(canon_dims),
        expected_resolution=_blank(payload.get("expected_resolution")),
        referenced_claim_id=_blank(payload.get("referenced_claim_id")),
        referenced_action_id=_blank(payload.get("referenced_action_id")),
        referenced_inspected_id=_blank(payload.get("referenced_inspected_id")),
        confidence=_blank(payload.get("confidence")),
        clarification_required=bool(payload.get("clarification_required")),
        ambiguous=bool(payload.get("ambiguous")),
        operation_conflict=bool(payload.get("operation_conflict")),
    )


def referents_from_focus(focus: Mapping[str, Any] | None) -> tuple[CanonicalReferent, ...]:
    if not isinstance(focus, Mapping):
        return ()
    found: list[CanonicalReferent] = []
    for slot_name, kind in (
        ("active_inspected", "object"),
        ("active_interlocutor", "interlocutor"),
        ("active_claim", "claim"),
        ("active_actionable_lead", "lead"),
        ("last_attempted_action", "action"),
    ):
        slot = focus.get(slot_name)
        if not isinstance(slot, Mapping):
            continue
        ident = str(slot.get("id") or "").strip()
        label = str(slot.get("label") or ident).strip()
        if not ident and not label:
            continue
        found.append(CanonicalReferent(type=kind, id=ident or label, label=label or ident, source="discourse"))
    return tuple(found)


def _blank(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _matches(candidate: str, referent: CanonicalReferent) -> bool:
    wanted = _normalized(candidate)
    if not wanted:
        return False
    names = [referent.label, referent.id.replace("_", " "), *referent.aliases]
    normalized = [_normalized(name) for name in names]
    normalized = [name for name in normalized if name]
    if wanted in set(normalized):
        return True
    if len(wanted) >= 4:
        for name in normalized:
            if wanted in name or name in wanted:
                return True
    return False


def _rows_for_id(index: Sequence[CanonicalReferent], ident: str) -> list[CanonicalReferent]:
    """Rows with this id. Scene and discourse copies of one referent count once."""
    matches = [row for row in index if row.id == ident]
    if len({row.id for row in matches}) != 1:
        return []
    return matches[:1]


def export_referent_index(
    focus: Mapping[str, Any] | None,
    canonical_referents: Sequence[CanonicalReferent | Mapping[str, Any]] | None,
) -> list[CanonicalReferent]:
    """Scene plus discourse rows the validator will accept. Read-only."""
    return _index(focus, canonical_referents)


def _index(
    focus: Mapping[str, Any] | None,
    canonical_referents: Sequence[CanonicalReferent | Mapping[str, Any]] | None,
) -> list[CanonicalReferent]:
    rows = list(referents_from_focus(focus))
    if not canonical_referents:
        return rows
    for item in canonical_referents:
        if isinstance(item, CanonicalReferent):
            rows.append(item)
            continue
        if isinstance(item, Mapping):
            ident = str(item.get("id") or "").strip()
            label = str(item.get("label") or ident).strip()
            if ident or label:
                alias_values = item.get("aliases") or ()
                rows.append(
                    CanonicalReferent(
                        type=str(item.get("type") or "object"),
                        id=ident or label,
                        label=label or ident,
                        source=str(item.get("source") or "scene"),
                        aliases=tuple(str(alias) for alias in alias_values if str(alias).strip()),
                    )
                )
    return rows


def _abstain(
    reason: str,
    fields: tuple[str, ...],
    *,
    model_appropriate: bool,
) -> InterpretationValidation:
    return InterpretationValidation(
        status=STATUS_ABSTAINED,
        reason=reason,
        failed_fields=fields,
        clarification_required=True,
        model_interpretation_appropriate=model_appropriate,
        canonical_target_id=None,
        canonical_target_label=None,
        canonical_target_type=None,
        canonical_basis=None,
        authoritative_operation=OP_UNRESOLVED,
        discourse_commit_allowed=False,
    )


def _accept(
    proposal: InterpretationProposal,
    *,
    referent: CanonicalReferent | None,
    basis: str,
    bridge: str | None = None,
) -> InterpretationValidation:
    operation = proposal.primary_operation if proposal.primary_operation in KNOWN_OPERATIONS else None
    if operation == OP_UNRESOLVED:
        operation = None
    return InterpretationValidation(
        status=STATUS_VALIDATED,
        reason=None,
        failed_fields=(),
        clarification_required=False,
        model_interpretation_appropriate=False,
        canonical_target_id=referent.id if referent else None,
        canonical_target_label=referent.label if referent else None,
        canonical_target_type=referent.type if referent else None,
        canonical_basis=basis if referent else None,
        authoritative_operation=operation,
        discourse_commit_allowed=True,
        compatibility_bridge=bridge,
    )


def _validate_interpretation_proposal(
    proposal: InterpretationProposal,
    *,
    discourse_focus: Mapping[str, Any] | None = None,
    canonical_referents: Sequence[CanonicalReferent | Mapping[str, Any]] | None = None,
) -> InterpretationValidation:
    """Map a proposal onto canonical structure, or abstain. This writes no state.

    ``canonical_referents is None`` allows the unscoped player-nominal bridge.
    An empty sequence is a supplied index: unknown nominals abstain.
    Confidence is ignored.
    """
    if proposal.operation_conflict or (
        proposal.primary_operation is None and len(proposal.supporting_operations) >= 2
    ):
        reason = (
            REASON_UNRESOLVED_COMPOUND
            if len(proposal.supporting_operations) >= 2
            else REASON_CONFLICTING_OPERATIONS
        )
        return _abstain(reason, ("primary_operation",), model_appropriate=True)
    if proposal.primary_operation and proposal.primary_operation not in KNOWN_OPERATIONS:
        return _abstain(REASON_UNSUPPORTED_OPERATION, ("primary_operation",), model_appropriate=False)
    if proposal.ambiguous:
        return _abstain(REASON_AMBIGUOUS_REFERENT, ("raw_target_text",), model_appropriate=True)

    index_supplied = canonical_referents is not None
    index = _index(discourse_focus, canonical_referents)
    raw = proposal.raw_target_text or ""
    proposed_id = proposal.proposed_target_id or ""

    if proposal.referenced_claim_id and not any(
        row.type == "claim" and (row.id == proposal.referenced_claim_id or row.label == proposal.referenced_claim_id)
        for row in index
    ):
        return _abstain(REASON_NONEXISTENT_REFERENT, ("referenced_claim_id",), model_appropriate=False)
    if proposal.referenced_action_id and not any(
        row.type == "action" and row.id == proposal.referenced_action_id for row in index
    ):
        return _abstain(REASON_NONEXISTENT_REFERENT, ("referenced_action_id",), model_appropriate=False)
    if proposal.interlocutor_id and proposal.source == SOURCE_MODEL and not any(
        row.type == "interlocutor" and row.id == proposal.interlocutor_id for row in index
    ):
        return _abstain(REASON_UNKNOWN_INTERLOCUTOR, ("interlocutor_id",), model_appropriate=False)

    if proposed_id and proposal.source == SOURCE_MODEL:
        exact = _rows_for_id(index, proposed_id)
        if len(exact) == 1:
            return _accept(proposal, referent=exact[0], basis=exact[0].source)
        named = []
        seen_ids: set[str] = set()
        for row in index:
            if row.id in seen_ids or not _matches(proposed_id, row):
                continue
            seen_ids.add(row.id)
            named.append(row)
        if len(named) > 1:
            return _abstain(REASON_AMBIGUOUS_REFERENT, ("proposed_target_id",), model_appropriate=True)
        if len(named) == 1:
            return _accept(proposal, referent=named[0], basis=named[0].source)
        return _abstain(REASON_TARGET_NOT_CANONICAL, ("proposed_target_id",), model_appropriate=False)

    structural_subject = structural_inspection_subject(
        raw,
        capture_kind=proposal.target_capture,
        operation=proposal.primary_operation,
        raw_input=proposal.raw_input,
    )
    if raw and span_is_malformed(raw) and not proposed_id and not structural_subject:
        if proposal.referenced_inspected_id:
            match = _rows_for_id(index, proposal.referenced_inspected_id)
            if match:
                return _accept(proposal, referent=match[0], basis="discourse")
        return _abstain(REASON_MALFORMED_SPAN, ("raw_target_text",), model_appropriate=True)

    candidate = proposed_id or raw
    if candidate:
        hits = [row for row in index if _matches(candidate, row) or _matches(raw, row)]
        unique: list[CanonicalReferent] = []
        seen: set[str] = set()
        for row in hits:
            if row.id in seen:
                continue
            seen.add(row.id)
            unique.append(row)
        if len(unique) > 1:
            return _abstain(REASON_AMBIGUOUS_REFERENT, ("raw_target_text",), model_appropriate=True)
        if len(unique) == 1:
            return _accept(proposal, referent=unique[0], basis=unique[0].source)
        if structural_subject and proposal.source == SOURCE_FAST_PATH and not proposed_id:
            nominal = CanonicalReferent(
                type="resolution_subject",
                id=raw,
                label=raw,
                source="explicit_resolution_subject",
            )
            return _accept(proposal, referent=nominal, basis="explicit_resolution_subject")
        if (
            not index_supplied
            and proposal.source == SOURCE_FAST_PATH
            and is_unscoped_player_nominal(raw, capture_kind=proposal.target_capture, has_determiner=proposal.has_determiner)
            and not proposed_id
        ):
            nominal = CanonicalReferent(type="object", id=raw, label=raw, source=_BRIDGE)
            return _accept(proposal, referent=nominal, basis=_BRIDGE, bridge=_BRIDGE)
        if proposal.referenced_inspected_id and not raw:
            match = _rows_for_id(index, proposal.referenced_inspected_id)
            if match:
                return _accept(proposal, referent=match[0], basis="discourse")
        return _abstain(REASON_TARGET_NOT_CANONICAL, ("raw_target_text",), model_appropriate=True)

    if proposal.referenced_inspected_id:
        match = _rows_for_id(index, proposal.referenced_inspected_id)
        if match:
            return _accept(proposal, referent=match[0], basis="discourse")
        return _abstain(REASON_INSUFFICIENT_DISCOURSE, ("referenced_inspected_id",), model_appropriate=True)
    if proposal.clarification_required:
        return _abstain(
            REASON_INSUFFICIENT_DISCOURSE,
            ("raw_target_text",),
            model_appropriate=True,
        )
    return _accept(proposal, referent=None, basis=None)


def validate_interpretation_proposal(
    proposal: InterpretationProposal,
    *,
    discourse_focus: Mapping[str, Any] | None = None,
    canonical_referents: Sequence[CanonicalReferent | Mapping[str, Any]] | None = None,
) -> InterpretationValidation:
    """Map a proposal onto canonical structure, or abstain. This writes no state."""
    proposed_dims = [item for item in (proposal.dimension, *proposal.dimensions) if item]
    unknown = [item for item in proposed_dims if item not in KNOWN_DIMENSIONS]
    if unknown:
        return _abstain(REASON_UNKNOWN_DIMENSION, ("dimension",), model_appropriate=False)
    corrected = structural_coherence_operation(proposal.raw_input, proposal.primary_operation)
    if corrected == "abstain":
        return _abstain(
            REASON_CONFLICTING_OPERATIONS,
            ("primary_operation",),
            model_appropriate=proposal.source != SOURCE_MODEL,
        )
    if corrected and corrected != proposal.primary_operation:
        proposal = replace(proposal, primary_operation=corrected, operation_conflict=False)
    result = _validate_interpretation_proposal(
        proposal,
        discourse_focus=discourse_focus,
        canonical_referents=canonical_referents,
    )
    if result.status != STATUS_VALIDATED or proposal.source == SOURCE_MODEL:
        return result
    gaps = fast_path_semantic_gaps(proposal, discourse_focus, result)
    if gaps:
        return _abstain(REASON_INCOMPLETE_SEMANTICS, gaps, model_appropriate=True)
    return result


def discourse_commit_blocked(contract: Mapping[str, Any] | None) -> bool:
    if not isinstance(contract, Mapping):
        return True
    if contract.get("ambiguous"):
        return True
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    if construction.get("validation_status") == STATUS_ABSTAINED:
        return True
    if construction.get("discourse_commit_allowed") is False:
        return True
    return False


def authoritative_provenance(basis: str | None) -> str:
    if basis in {"discourse", "scene"}:
        return PROVENANCE_INHERITED if basis == "discourse" else PROVENANCE_EXPLICIT
    return PROVENANCE_EXPLICIT
