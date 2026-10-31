"""Live resolution-mode routing for ordinary player-input gaps.

This module is the production bridge between raw turn text and bounded
improvisational authority.  It does not loosen the bounded-improvisation
validator; it detects low-risk opportunities in the live path, binds a compact
target/topic, and can synthesize a proposal from the already selected player
facing response when the response resolves the request.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence

from game.bounded_improvisation import (
    IMPROVISATION_PROPOSAL_KEY,
    INCIDENTAL_KIND,
    NPC_CLAIM_KIND,
)
from game.resolution_contract import (
    construct_resolution_contract,
    contract_mapping_from_resolution,
    contract_requests_consequential_protection,
    contract_trace,
)
from game.gm_resolution_decision import DECISION_METADATA_KEY, attach_gm_resolution_decision


AUTHORITATIVE_MECHANICAL_ACTION = "authoritative_mechanical_action"
GROUNDED_INFORMATION_REQUEST = "grounded_information_request"
BOUNDED_IMPROVISABLE_REQUEST = "bounded_improvisable_request"
NPC_CLAIM_RESPONSE = "npc_claim_response"
UNSUPPORTED_CONSEQUENTIAL_REQUEST = "unsupported_consequential_request"
CLARIFICATION_TARGET_FAILURE = "clarification_target_failure"

QUESTION = "question"
ACTION_REQUEST = "action_request"
INSPECTION = "inspection"
SOCIAL_REQUEST = "social_request"
FOLLOW_UP = "follow_up"
CLARIFICATION = "clarification"

_QUESTION_RE = re.compile(
    r"^\s*(?:what|who|where|when|why|how|which|whose|whom|can|could|would|do|does|did|is|are|tell me|heard|hear)\b",
    re.IGNORECASE,
)
_INCIDENTAL_DESCRIPTION_RE = re.compile(
    r"\b("
    r"look like|looks like|color|colors|colour|colours|smell|taste|sound|what(?:'s| is) (?:cooking|served|on offer)|"
    r"describe|more about|what does (?:it|this|that|the [^?.!]{1,40}) look like|"
    r"what kind of|what sort of"
    r")\b",
    re.IGNORECASE,
)
_NPC_CLAIM_RE = re.compile(
    r"\b(rumou?rs?|gossip|heard anything|what(?:'s| is) going on|what do you know|who told|where did you hear|they say|word is)\b",
    re.IGNORECASE,
)
_SERVICE_RE = re.compile(
    r"\b(food|drink|meal|stew|soup|lodging|sleep|room|bed|service|work|job|hire|directions?)\b",
    re.IGNORECASE,
)
_MECHANICAL_RE = re.compile(
    r"\b(attack|strike|stab|shoot|cast|damage|hp|hit points?|inventory|take|buy|pay|spend|coin|gold|silver|copper|roll|check|dc|initiative)\b",
    re.IGNORECASE,
)
_PHYSICAL_ACTION_RE = re.compile(
    r"\b(open|knock|push|pull|break|force|climb|jump|leap|enter|sprint|shoulder|search|inspect|examine|read)\b",
    re.IGNORECASE,
)
_CONSEQUENTIAL_RE = re.compile(
    r"\b(secret|hidden|traitor|conspiracy|murderer|spy|cult|passage|vault|artifact|curse|prophecy|true motive|really works for)\b",
    re.IGNORECASE,
)
_REFUSAL_RE = re.compile(
    r"\b(can't|cannot|couldn't|could not|won't|will not|not able|no authority|not mine to|can't arrange|cannot arrange|refuses?)\b",
    re.IGNORECASE,
)
_ACTION_REQUEST_RE = re.compile(
    r"\b(?:can|could|would|will)\s+(?:you|they|he|she)\s+"
    r"(?:introduce|take|bring|show|open|close|help|point|lead|give|send|ask|arrange)\b",
    re.IGNORECASE,
)
_SOCIAL_REQUEST_RE = re.compile(
    r"\b(?:ask|greet|persuade|convince|request|bargain|barter|recruit|intimidate|talk\s+to|speak\s+to)\b",
    re.IGNORECASE,
)
_EMBEDDED_INFORMATION_REQUEST_RE = re.compile(
    r"\bask\b[^.!?]{0,100}\b(?:what|who|where|when|why|how|whether|about|"
    r"for\s+(?:a\s+|one\s+|the\s+)?(?:clear|concrete|safe|useful|final|immediate|next))\b",
    re.IGNORECASE,
)
_FOLLOW_UP_RE = re.compile(
    r"\b(?:who told|where did (?:you|they) hear|when did|do you believe|how certain|who would know|"
    r"introduce me|point me to (?:them|him|her)|what else|tell me more)\b",
    re.IGNORECASE,
)
_CLARIFICATION_RE = re.compile(r"\b(?:what do you mean|which one|which person|clarify)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ResolutionModeDecision:
    mode: str
    reason_codes: list[str] = field(default_factory=list)
    target: str | None = None
    speaker_id: str | None = None
    topic: str | None = None
    proposal_kind: str | None = None
    proposal_category: str | None = None
    epistemic_status: str | None = None
    requested_dimension: str | None = None
    contract_id: str | None = None


@dataclass(frozen=True)
class InteractionObligation:
    kind: str
    target: str | None
    interlocutor_id: str | None
    subject: str | None
    requested_outcome: str
    claim_id: str | None = None
    resolution_mode: str | None = None
    turn_index: int | None = None


def _clean_text(value: Any, *, limit: int = 180) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:limit]


def _scene_inner(scene: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(scene, Mapping):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, Mapping) else scene


def _scene_id(scene: Mapping[str, Any] | None, session: Mapping[str, Any] | None) -> str:
    inner = _scene_inner(scene)
    sid = str(inner.get("id") or "").strip()
    if sid:
        return sid
    if isinstance(session, Mapping):
        return str(session.get("active_scene_id") or "").strip()
    return ""


def _target_from_action(normalized_action: Mapping[str, Any] | None) -> str:
    if not isinstance(normalized_action, Mapping):
        return ""
    for key in ("target_id", "targetEntityId", "target_scene_id", "targetSceneId", "label", "prompt"):
        val = _clean_text(normalized_action.get(key), limit=100)
        if val:
            return val
    return ""


def _target_from_resolution(resolution: Mapping[str, Any] | None) -> tuple[str, str]:
    if not isinstance(resolution, Mapping):
        return "", ""
    speaker = ""
    social = resolution.get("social")
    if isinstance(social, Mapping):
        speaker = _clean_text(social.get("npc_id"), limit=80)
    for key in ("target_id", "targetEntityId", "action_id", "label", "prompt"):
        val = _clean_text(resolution.get(key), limit=120)
        if val:
            return val, speaker
    return "", speaker


def _target_from_context(session: Mapping[str, Any] | None) -> str:
    if not isinstance(session, Mapping):
        return ""
    ctx = session.get("interaction_context")
    if isinstance(ctx, Mapping):
        for key in ("active_interaction_target_id", "last_referenced_target_id", "topic_anchor"):
            val = _clean_text(ctx.get(key), limit=100)
            if val:
                return val
    return ""


def _latest_npc_claim(session: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not isinstance(session, Mapping):
        return None
    ledger = session.get("bounded_improvisation")
    entries = ledger.get("entries") if isinstance(ledger, Mapping) else None
    if not isinstance(entries, list):
        return None
    for entry in reversed(entries):
        if (
            isinstance(entry, Mapping)
            and entry.get("kind") == NPC_CLAIM_KIND
            and str(entry.get("status") or "").strip().lower() in {"accepted", "promoted"}
        ):
            return entry
    return None


def _topic_from_text(player_text: str) -> str:
    text = _clean_text(player_text, limit=160)
    if not text:
        return ""
    embedded = re.search(
        r"\bask\b[^.!?]{0,80}?\b((?:what|who|where|when|why|how|whether)\b[^.!?]{0,100})",
        text,
        re.IGNORECASE,
    )
    if embedded:
        return _clean_text(embedded.group(1), limit=100)
    about = re.search(r"\babout\s+(?:the\s+|a\s+|an\s+)?([^?.!]{1,80})", text, re.IGNORECASE)
    if about:
        return _clean_text(about.group(1), limit=80)
    look = re.search(r"\b(?:look at|inspect|examine|read|check)\s+(?:the\s+|a\s+|an\s+)?([^?.!]{1,80})", text, re.IGNORECASE)
    if look:
        return _clean_text(look.group(1), limit=80)
    if "?" in text:
        return _clean_text(text.rstrip("?"), limit=80)
    return ""


def _kind_from_contract(resolution: Mapping[str, Any] | None) -> tuple[str, str] | None:
    """Let a built resolution contract own kind when it already classified the turn."""
    contract = contract_mapping_from_resolution(resolution)
    if not contract.get("contract_id"):
        return None
    if contract.get("ambiguous") or contract.get("request_kind") == "clarification":
        return CLARIFICATION, "clarify the referenced subject or state that it cannot be identified"
    operation = str(contract.get("operation") or "")
    if operation in {"act", "follow", "confirm"}:
        return ACTION_REQUEST, "accept, refuse, condition, or redirect the requested action"
    if operation == "repeat":
        return QUESTION, "restate the established claim, or say that it cannot be repeated"
    if operation in {"perceive", "inspect"} or "content" in {
        str(item) for item in (contract.get("dimensions") or []) if str(item).strip()
    }:
        return INSPECTION, "resolve the inspection from authoritative or bounded incidental detail"
    dims = {str(item) for item in (contract.get("dimensions") or []) if str(item).strip()}
    if contract.get("dimension"):
        dims.add(str(contract.get("dimension")))
    if dims & {"source", "confidence", "location", "time"}:
        return FOLLOW_UP, "answer, qualify, refuse, or redirect the follow-up about the established claim"
    return None


def _perception_inability_line(dims: set[str], target: str = "") -> str:
    named = _clean_text(target, limit=80)
    if dims & {"sound", "smell"}:
        return "No distinct sound or smell can be established beyond the current scene's general activity."
    if dims & {"wear", "use"}:
        if named:
            return f"The visible wear and marks establish no reliable use of the {named}."
        return "The visible wear and marks establish no reliable use beyond what is already apparent."
    if "change" in dims:
        if named:
            return f"No change can be established in the {named}; it remains as it was."
        return "No change can be established from that action; the scene remains as it was."
    if "appearance" in dims:
        if named:
            return f"No further reliable appearance can be established for the {named}."
        return "No further reliable appearance can be established beyond what is already visible."
    if named:
        return f"The inspection establishes no further reliable detail about the {named}."
    return "The inspection establishes no further reliable detail from the current scene."


def derive_interaction_obligation(
    *,
    player_text: str | None,
    session: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
    decision: ResolutionModeDecision | None = None,
) -> InteractionObligation:
    """Capture the semantic result a turn owes before narration or retries can mutate it."""
    text = _clean_text(player_text, limit=240)
    low = text.lower()
    res_social = resolution.get("social") if isinstance(resolution, Mapping) else None
    interlocutor = _clean_text(res_social.get("npc_id"), limit=80) if isinstance(res_social, Mapping) else ""
    if not interlocutor:
        interlocutor = _target_from_context(session)
    target = (
        (decision.target if isinstance(decision, ResolutionModeDecision) else None)
        or _target_from_action(normalized_action)
        or _target_from_resolution(resolution)[0]
        or interlocutor
        or None
    )
    claim = _latest_npc_claim(session)
    claim_subject = _clean_text(claim.get("content"), limit=220) if isinstance(claim, Mapping) else ""
    claim_id = _clean_text(claim.get("id"), limit=80) if isinstance(claim, Mapping) else ""

    action_type = str((normalized_action or {}).get("type") or "").strip().lower() if isinstance(normalized_action, Mapping) else ""
    if _CLARIFICATION_RE.search(low):
        kind, outcome = CLARIFICATION, "clarify the referenced subject or state that it cannot be identified"
    elif _ACTION_REQUEST_RE.search(low):
        kind, outcome = ACTION_REQUEST, "accept, refuse, condition, or redirect the requested action"
    elif _FOLLOW_UP_RE.search(low) and (claim_subject or interlocutor):
        kind, outcome = FOLLOW_UP, "answer, qualify, refuse, or redirect the follow-up about the established claim"
    elif _EMBEDDED_INFORMATION_REQUEST_RE.search(low):
        kind, outcome = QUESTION, "answer, admit uncertainty, refuse, or redirect the question"
    elif action_type in {"investigate", "observe"} or _INCIDENTAL_DESCRIPTION_RE.search(low):
        kind, outcome = INSPECTION, "resolve the inspection from authoritative or bounded incidental detail"
    elif action_type in {"interact", "custom", "travel", "scene_transition", "attack"} or _PHYSICAL_ACTION_RE.search(low):
        kind, outcome = ACTION_REQUEST, "resolve the attempted action, obstruction, or consequence"
    elif _SOCIAL_REQUEST_RE.search(low) and not _QUESTION_RE.search(low):
        kind, outcome = SOCIAL_REQUEST, "respond to the social request with acceptance, refusal, condition, or redirection"
    else:
        kind, outcome = QUESTION, "answer, admit uncertainty, refuse, or redirect the question"

    override = _kind_from_contract(resolution)
    if override is not None:
        kind, outcome = override

    subject = claim_subject if kind == FOLLOW_UP else ((decision.topic if decision else None) or _topic_from_text(text) or target)
    if kind in {ACTION_REQUEST, SOCIAL_REQUEST}:
        subject = text or subject
    return InteractionObligation(
        kind=kind,
        target=target,
        interlocutor_id=interlocutor or None,
        subject=subject or None,
        requested_outcome=outcome,
        claim_id=claim_id or None,
        resolution_mode=decision.mode if decision else None,
        turn_index=(
            int(session.get("turn_counter"))
            if isinstance(session, Mapping) and isinstance(session.get("turn_counter"), int)
            else None
        ),
    )


def _contract_target_label(resolution: Mapping[str, Any] | None) -> str:
    contract = contract_mapping_from_resolution(resolution)
    target = contract.get("target_ref") if isinstance(contract.get("target_ref"), Mapping) else {}
    discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), Mapping) else {}
    return _clean_text(target.get("id_or_text") or discourse.get("label"), limit=120)


def _contract_dimensions(resolution: Mapping[str, Any] | None) -> set[str]:
    contract = contract_mapping_from_resolution(resolution)
    dims = contract.get("dimensions")
    found = {str(item) for item in dims if str(item).strip()} if isinstance(dims, list) else set()
    if contract.get("dimension"):
        found.add(str(contract.get("dimension")))
    return found


def _stamp_decision(decision: ResolutionModeDecision, resolution: Mapping[str, Any] | None) -> ResolutionModeDecision:
    contract = contract_mapping_from_resolution(resolution)
    if not contract:
        return decision
    mode = decision.mode
    proposal_kind = decision.proposal_kind
    proposal_category = decision.proposal_category
    reasons = list(decision.reason_codes)
    if contract_requests_consequential_protection(contract) and mode != AUTHORITATIVE_MECHANICAL_ACTION:
        if mode != UNSUPPORTED_CONSEQUENTIAL_REQUEST:
            reasons.append("resolution_contract_consequential")
        mode = UNSUPPORTED_CONSEQUENTIAL_REQUEST
        proposal_kind = None
        proposal_category = None
    dimension = str(contract.get("dimension") or "").strip() or None
    if dimension:
        reasons.append(f"contract_dimension:{dimension}")
    return ResolutionModeDecision(
        mode,
        reasons,
        decision.target,
        decision.speaker_id,
        decision.topic,
        proposal_kind,
        proposal_category,
        decision.epistemic_status,
        requested_dimension=dimension,
        contract_id=str(contract.get("contract_id") or "").strip() or None,
    )


def attach_interaction_obligation(
    resolution: dict[str, Any],
    *,
    player_text: str | None,
    session: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    visible_turns: Sequence[Mapping[str, Any]] | None = None,
    enable_model_interpretation: bool = False,
) -> dict[str, Any]:
    if not isinstance(resolution, dict):
        return resolution
    md = resolution.setdefault("metadata", {})
    if not isinstance(md, dict):
        md = {}
        resolution["metadata"] = md
    existing = md.get("resolution_contract")
    if isinstance(existing, dict) and existing.get("contract_id"):
        # The contract is already authoritative. Do not rebuild it.
        # Social, movement, perception, clarification, and retry paths can
        # arrive here. They still need a decision that consumes this contract.
        existing["retry_preserved"] = True
        if isinstance(session, dict):
            from game.storage import append_debug_trace

            append_debug_trace(
                session,
                contract_trace(existing, obligation_kind=str((md.get("interaction_obligation") or {}).get("kind") or ""), retry_preserved=True),
            )
        contract_id = str(existing.get("contract_id") or "")
        current = md.get(DECISION_METADATA_KEY) if isinstance(md.get(DECISION_METADATA_KEY), dict) else {}
        if str(current.get("contract_id") or "") != contract_id:
            attach_gm_resolution_decision(
                resolution,
                session=session,
                scene=scene,
                world=world,
                normalized_action=normalized_action,
            )
        return resolution
    catalog = None
    interpreter = None
    if scene is not None or world is not None or enable_model_interpretation:
        from game.scene_referent_catalog import build_canonical_referent_catalog

        catalog = build_canonical_referent_catalog(
            scene=scene,
            world=world,
            session=session,
            scene_id=scene_id,
        )
    if enable_model_interpretation:
        from game.semantic_interpreter import interpret_for_contract

        interpreter = interpret_for_contract
    contract = construct_resolution_contract(
        player_text=player_text,
        session=session,
        resolution=resolution,
        normalized_action=normalized_action,
        scene_id=scene_id,
        canonical_referents=catalog,
        model_interpreter=interpreter,
        visible_turns=visible_turns,
        scene=scene,
    )
    md["resolution_contract"] = contract.as_dict()
    if isinstance(session, dict):
        from game.incidental_entity import apply_entity_binding

        apply_entity_binding(resolution, session, scene_id=scene_id)
    decision = select_resolution_mode(
        player_text=player_text,
        scene=None,
        session=session,
        resolution=resolution,
        normalized_action=normalized_action,
    )
    obligation = derive_interaction_obligation(
        player_text=player_text,
        session=session,
        resolution=resolution,
        normalized_action=normalized_action,
        decision=decision,
    )
    md["interaction_obligation"] = {
        "kind": obligation.kind,
        "target": obligation.target,
        "interlocutor_id": obligation.interlocutor_id,
        "subject": obligation.subject,
        "requested_outcome": obligation.requested_outcome,
        "claim_id": obligation.claim_id,
        "resolution_mode": decision.mode,
        "turn_index": obligation.turn_index,
        "resolution_contract_id": contract.contract_id,
        "executable_obligations": dict(
            (contract.as_dict().get("construction") or {}).get("executable_obligations") or {}
        ),
    }
    attach_gm_resolution_decision(
        resolution,
        session=session,
        scene=scene,
        world=world,
        normalized_action=normalized_action,
    )
    if isinstance(session, dict):
        from game.discourse_state import effective_discourse_focus
        from game.storage import append_debug_trace

        append_debug_trace(
            session,
            contract_trace(
                md["resolution_contract"],
                focus=effective_discourse_focus(session, scene_id=scene_id),
                obligation_kind=obligation.kind,
                authority_route=decision.mode,
            ),
        )
    return resolution


def interaction_obligation_from_resolution(resolution: Mapping[str, Any] | None) -> Mapping[str, Any]:
    md = resolution.get("metadata") if isinstance(resolution, Mapping) else None
    obligation = md.get("interaction_obligation") if isinstance(md, Mapping) else None
    return obligation if isinstance(obligation, Mapping) else {}


def obligation_preserving_fallback_line(resolution: Mapping[str, Any] | None) -> str:
    """Safe terminal answer that preserves the obligation without inventing facts."""
    obligation = interaction_obligation_from_resolution(resolution)
    kind = str(obligation.get("kind") or "").strip().lower()
    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    speaker = _clean_text(social.get("npc_name"), limit=80) if isinstance(social, Mapping) else ""
    def voiced(statement: str) -> str:
        if speaker:
            return f'{speaker} says, "{statement}"'
        return statement
    contract = contract_mapping_from_resolution(resolution)
    operation = str(contract.get("operation") or "")
    if contract.get("ambiguous") or contract.get("request_kind") == "clarification":
        if speaker:
            return voiced("Which do you mean? I cannot tell which one that refers to.")
        return "The reference cannot be identified clearly enough to resolve without clarification."
    if operation in {"act", "follow", "confirm"}:
        if speaker:
            return voiced("I will not carry out that request; you will need another route.")
        return "The requested action cannot be completed here; another route is needed."
    if operation == "repeat":
        label = _contract_target_label(resolution)
        if label:
            statement = label if label.endswith((".", "!", "?")) else f"{label}."
            return voiced(statement)
        if speaker:
            return voiced("I cannot repeat that; I do not have the earlier wording.")
        return "The earlier wording cannot be repeated from here."
    if kind == FOLLOW_UP:
        dims = _contract_dimensions(resolution)
        if "time" in dims and not (dims & {"source", "confidence", "location"}):
            statement = "I cannot say how recently that was."
            if speaker:
                return voiced(statement)
            return "No one here can say how recently that was."
        if "location" in dims and not (dims & {"source", "confidence"}):
            statement = "I cannot say where that was."
            if speaker:
                return voiced(statement)
            return "No one here can say where that was."
        if "confidence" in dims and "source" not in dims:
            statement = "I cannot say how certain that is."
            if speaker:
                return voiced(statement)
            return "No one here can say how certain that is."
        if speaker:
            return voiced("I cannot verify the source or certainty of that earlier claim.")
        return "No reliable source can verify who began the earlier claim or how certain it is."
    if kind in {ACTION_REQUEST, SOCIAL_REQUEST}:
        if speaker:
            return voiced("I will not carry out that request; you will need another route.")
        return "The requested action cannot be completed here; another route is needed."
    if kind == INSPECTION:
        dims = _contract_dimensions(resolution)
        if dims & {"sound", "smell", "wear", "use", "change", "appearance"}:
            return _perception_inability_line(dims, _contract_target_label(resolution))
        named = _clean_text(_contract_target_label(resolution), limit=120)
        subject = named or _clean_text(obligation.get("subject"), limit=120)
        if subject and re.fullmatch(r"[a-z0-9_]+", subject) and "_" in subject and not named:
            subject = ""
        if re.search(r"\b(?:sounds?|smells?)\b", subject, re.IGNORECASE):
            return "No distinct sound or smell can be established beyond the current scene's general activity."
        if re.search(r"\b(?:wear|marks?|use)\b", subject, re.IGNORECASE):
            return "The visible wear and marks establish no reliable use beyond what is already apparent."
        if subject:
            statement = f"The inspection establishes no further reliable detail about {subject}."
            return voiced(statement) if speaker else statement
        statement = "The inspection establishes no further reliable detail from the current scene."
        return voiced(statement) if speaker else statement
    if kind == CLARIFICATION:
        return "The reference cannot be identified clearly enough to resolve without clarification."
    subject = _clean_text(obligation.get("subject"), limit=120)
    contract = contract_mapping_from_resolution(resolution)
    raw_input = str(contract.get("raw_input") or "") if contract else ""
    raw_norm = " ".join(re.findall(r"[a-z0-9]+", raw_input.lower()))
    subject_norm = " ".join(re.findall(r"[a-z0-9]+", subject.lower()))
    from game.interaction_completion import subject_repeats_player_opening

    if subject and raw_norm and (
        raw_norm in subject_norm
        or subject_repeats_player_opening(subject, raw_input)
    ):
        subject = ""
    if re.search(r"\brumou?rs?\b", raw_input, re.IGNORECASE):
        if speaker:
            return voiced("I do not know which rumor the travelers are repeating.")
        return "No one here can say which rumor the travelers are repeating."
    dims = _contract_dimensions(resolution)
    if operation in {"perceive", "inspect"} and dims & {"sound", "smell", "wear", "use", "change", "appearance"}:
        return _perception_inability_line(dims, _contract_target_label(resolution))
    if subject and subject.lower() not in {str(obligation.get("target") or "").strip().lower(), speaker.lower()}:
        if speaker:
            return voiced(f"I couldn't tell you {subject}; you will need another source.")
        return f"No reliable source here can verify {subject}; another source is needed."
    if speaker:
        return voiced("I couldn't tell you the requested information; you will need another source.")
    return "No reliable source here can verify the requested information; another source is needed."


def _authored_text(scene: Mapping[str, Any] | None) -> str:
    inner = _scene_inner(scene)
    bits: list[str] = []
    for key in ("summary", "visible_facts", "opening_seed_facts"):
        val = inner.get(key)
        if isinstance(val, str):
            bits.append(val)
        elif isinstance(val, list):
            bits.extend(str(v) for v in val if isinstance(v, str))
    return "\n".join(bits)


def _has_grounded_answer(player_text: str, scene: Mapping[str, Any] | None) -> bool:
    topic_terms = {
        t
        for t in re.findall(r"[a-z0-9']+", _topic_from_text(player_text).lower())
        if len(t) >= 4
    }
    if not topic_terms:
        return False
    authored = _authored_text(scene).lower()
    return bool(topic_terms and topic_terms <= set(re.findall(r"[a-z0-9']+", authored)))


def _select_resolution_mode_body(
    *,
    player_text: str | None,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
    route_choice: str | None = None,
) -> ResolutionModeDecision:
    text = _clean_text(player_text, limit=240)
    low = text.lower()
    target_from_res, speaker = _target_from_resolution(resolution)
    target = _target_from_action(normalized_action) or target_from_res or _target_from_context(session) or None
    topic = _topic_from_text(text) or target
    reasons: list[str] = []

    res_kind = str((resolution or {}).get("kind") or "").strip().lower() if isinstance(resolution, Mapping) else ""
    action_type = str((normalized_action or {}).get("type") or "").strip().lower() if isinstance(normalized_action, Mapping) else ""
    if res_kind in {"attack", "spell", "skill_check", "enemy_attack", "initiative"} or action_type == "attack":
        return ResolutionModeDecision(AUTHORITATIVE_MECHANICAL_ACTION, ["mechanical_resolution"], target, speaker, topic)

    if _CONSEQUENTIAL_RE.search(low):
        return ResolutionModeDecision(UNSUPPORTED_CONSEQUENTIAL_REQUEST, ["consequential_terms"], target, speaker, topic)

    if _MECHANICAL_RE.search(low) and not (_SERVICE_RE.search(low) and _QUESTION_RE.search(low)):
        return ResolutionModeDecision(AUTHORITATIVE_MECHANICAL_ACTION, ["mechanical_or_economy_terms"], target, speaker, topic)

    if _NPC_CLAIM_RE.search(low):
        return ResolutionModeDecision(
            NPC_CLAIM_RESPONSE,
            ["npc_claim_or_epistemic_question"],
            target,
            speaker,
            topic,
            NPC_CLAIM_KIND,
            "rumor",
            "hearsay",
        )

    if _QUESTION_RE.search(low) and _has_grounded_answer(text, scene):
        return ResolutionModeDecision(GROUNDED_INFORMATION_REQUEST, ["authored_topic_overlap"], target, speaker, topic)

    if _INCIDENTAL_DESCRIPTION_RE.search(low):
        return ResolutionModeDecision(
            BOUNDED_IMPROVISABLE_REQUEST,
            ["incidental_description_gap"],
            target,
            speaker,
            topic,
            INCIDENTAL_KIND,
            "sensory_detail",
        )

    if _QUESTION_RE.search(low) and _SERVICE_RE.search(low):
        return ResolutionModeDecision(
            BOUNDED_IMPROVISABLE_REQUEST,
            ["mundane_service_gap"],
            target,
            speaker,
            topic,
            INCIDENTAL_KIND,
            "mundane_service_detail",
        )

    if _PHYSICAL_ACTION_RE.search(low):
        return ResolutionModeDecision(AUTHORITATIVE_MECHANICAL_ACTION, ["physical_affordance_action"], target, speaker, topic)

    if _QUESTION_RE.search(low) and not target:
        return ResolutionModeDecision(CLARIFICATION_TARGET_FAILURE, ["question_without_bound_target"], None, speaker, topic)

    return ResolutionModeDecision(GROUNDED_INFORMATION_REQUEST, reasons or ["default_existing_resolution"], target, speaker, topic)


def select_resolution_mode(
    *,
    player_text: str | None,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
    route_choice: str | None = None,
) -> ResolutionModeDecision:
    decision = _select_resolution_mode_body(
        player_text=player_text,
        scene=scene,
        session=session,
        world=world,
        resolution=resolution,
        normalized_action=normalized_action,
        route_choice=route_choice,
    )
    return _stamp_decision(decision, resolution)


def _gm_text(gm: Mapping[str, Any] | None) -> str:
    if not isinstance(gm, Mapping):
        return ""
    return _clean_text(gm.get("player_facing_text"), limit=500)


def _response_is_complete_for_mode(text: str, decision: ResolutionModeDecision) -> tuple[bool, str]:
    if not text:
        return False, "missing_player_facing_text"
    mode = decision.mode
    if mode in {BOUNDED_IMPROVISABLE_REQUEST, NPC_CLAIM_RESPONSE}:
        if _REFUSAL_RE.search(text) and mode == BOUNDED_IMPROVISABLE_REQUEST:
            return False, "refusal_not_incidental_answer"
        return True, "resolved_or_claimed"
    if mode == AUTHORITATIVE_MECHANICAL_ACTION:
        return True, "engine_owned"
    if mode == UNSUPPORTED_CONSEQUENTIAL_REQUEST:
        return _REFUSAL_RE.search(text), "refused_unsafe_request" if _REFUSAL_RE.search(text) else "unsafe_request_not_refused"
    if mode == CLARIFICATION_TARGET_FAILURE:
        return bool(re.search(r"\b(which|what do you mean|clarify|be specific)\b", text, re.IGNORECASE)), "clarification_requested"
    return True, "not_gap_mode"


def attach_live_resolution_metadata(
    gm: dict[str, Any],
    *,
    decision: ResolutionModeDecision,
    proposal_created: bool = False,
    proposal_reason: str = "",
) -> dict[str, Any]:
    md = gm.setdefault("metadata", {})
    if not isinstance(md, dict):
        md = {}
        gm["metadata"] = md
    dbg = md.setdefault("emission_debug", {})
    if not isinstance(dbg, dict):
        dbg = {}
        md["emission_debug"] = dbg
    complete, completeness_reason = _response_is_complete_for_mode(_gm_text(gm), decision)
    dbg["live_resolution_mode"] = {
        "mode": decision.mode,
        "reason_codes": list(decision.reason_codes),
        "target": decision.target,
        "speaker_id": decision.speaker_id,
        "topic": decision.topic,
        "improvisation_opportunity_detected": decision.mode in {BOUNDED_IMPROVISABLE_REQUEST, NPC_CLAIM_RESPONSE},
        "proposal_created": bool(proposal_created),
        "proposal_reason": proposal_reason,
        "response_complete": bool(complete),
        "response_completeness_reason": completeness_reason,
        "requested_dimension": decision.requested_dimension,
        "contract_id": decision.contract_id,
    }
    return gm


def synthesize_live_improvisation_proposal(
    gm: dict[str, Any],
    *,
    decision: ResolutionModeDecision,
) -> dict[str, Any]:
    if not isinstance(gm, dict):
        return gm
    proposals = gm.get(IMPROVISATION_PROPOSAL_KEY)
    if isinstance(proposals, list) and proposals:
        existing_md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
        existing_dbg = existing_md.get("emission_debug") if isinstance(existing_md.get("emission_debug"), dict) else {}
        existing_live = existing_dbg.get("live_resolution_mode") if isinstance(existing_dbg.get("live_resolution_mode"), dict) else {}
        if existing_live.get("proposal_created") is True:
            return gm
        return attach_live_resolution_metadata(gm, decision=decision, proposal_created=False, proposal_reason="model_supplied")
    if decision.mode not in {BOUNDED_IMPROVISABLE_REQUEST, NPC_CLAIM_RESPONSE}:
        return attach_live_resolution_metadata(gm, decision=decision, proposal_created=False, proposal_reason="not_improvable_mode")
    content = _gm_text(gm)
    complete, reason = _response_is_complete_for_mode(content, decision)
    if not complete:
        return attach_live_resolution_metadata(gm, decision=decision, proposal_created=False, proposal_reason=reason)
    proposal = {
        "kind": decision.proposal_kind or INCIDENTAL_KIND,
        "category": decision.proposal_category or "local_color",
        "content": content,
        "scope": "scene",
        "consequence_level": "low",
        "source": f"npc:{decision.speaker_id}" if decision.speaker_id and decision.proposal_kind == NPC_CLAIM_KIND else "dm_improvisation",
        "speaker_id": decision.speaker_id if decision.proposal_kind == NPC_CLAIM_KIND else None,
        "epistemic_status": decision.epistemic_status if decision.proposal_kind == NPC_CLAIM_KIND else None,
        "satisfies_contract_id": decision.contract_id,
        "requested_dimension": decision.requested_dimension,
    }
    gm[IMPROVISATION_PROPOSAL_KEY] = [proposal]
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    if "live_bounded_improvisation_proposal" not in tag_list:
        tag_list.append("live_bounded_improvisation_proposal")
    gm["tags"] = tag_list
    return attach_live_resolution_metadata(gm, decision=decision, proposal_created=True, proposal_reason="runtime_live_gap_bridge")


def live_resolution_trace(decision: ResolutionModeDecision) -> dict[str, Any]:
    return {
        "mode": decision.mode,
        "reason_codes": list(decision.reason_codes),
        "target": decision.target,
        "speaker_id": decision.speaker_id,
        "topic": decision.topic,
        "proposal_kind": decision.proposal_kind,
        "proposal_category": decision.proposal_category,
        "epistemic_status": decision.epistemic_status,
        "requested_dimension": decision.requested_dimension,
        "contract_id": decision.contract_id,
    }
