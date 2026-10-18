"""Conversational turn decision boundary for production chat.

This module decides whether a player turn needs authoritative execution before
the chat pipeline advances clocks, ticks, or resolver state. It does not resolve
world outcomes and it does not create canonical facts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import re
from typing import Any, Mapping


class ConversationalDecisionCategory(str, Enum):
    ANSWER = "ANSWER"
    CLARIFY = "CLARIFY"
    DECLINE = "DECLINE"
    EXECUTE = "EXECUTE"
    PLAN = "PLAN"


@dataclass(frozen=True)
class ConversationalDecision:
    category: ConversationalDecisionCategory
    primary_intention: str
    intent_family: str
    incidental_context: list[str] = field(default_factory=list)
    proposed_operation: str | None = None
    proposed_target: str | None = None
    proposed_record: dict[str, Any] | None = None
    missing_information: list[str] = field(default_factory=list)
    context_references: list[str] = field(default_factory=list)
    requires_authoritative_execution: bool = False
    reason: str = ""
    confidence: float | None = None
    ambiguity: str | None = None
    player_facing_text: str = ""
    context_update: dict[str, Any] | None = None
    intent_modality: str = "committed"
    secondary_intentions: list[dict[str, Any]] = field(default_factory=list)
    execution_policy: str = ""
    communication_owner: str = "CHARACTER"
    communication_purpose: str = "ACTION"
    authorization: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.communication_owner == "CHARACTER" and self.category != ConversationalDecisionCategory.EXECUTE:
            object.__setattr__(self, "communication_owner", "SESSION" if self.intent_family == "ooc_help" else "GM")
            if self.communication_purpose == "ACTION":
                object.__setattr__(self, "communication_purpose", "CLARIFICATION" if self.category == ConversationalDecisionCategory.CLARIFY else "EXPLANATION")
        elif self.category == ConversationalDecisionCategory.EXECUTE and self.proposed_operation == "ASK":
            object.__setattr__(self, "communication_owner", "NPC")

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["category"] = self.category.value
        return payload


_QUESTION_START_RE = re.compile(
    r"^\s*(?:who|what|when|where|why|how|is|are|do|does|did|can|could|should|would)\b",
    re.IGNORECASE,
)
_OOC_HELP_RE = re.compile(
    r"\b(?:rules?|mechanics?|interface|ui|save|load|roll|check|how\s+do\s+i|how\s+does\s+this\s+work|at\s+this\s+table)\b",
    re.IGNORECASE,
)
_EMBEDDED_ACTION_CONDITION_RE = re.compile(
    r"\b(?:if|while|when)\s+i\s+(?:conceal|hide|steal|attack|cast|pick|open|break|climb|sneak|move|go|ask|persuade)\b",
    re.IGNORECASE,
)
_INCOMPLETE_MOVEMENT_RE = re.compile(
    r"^\s*(?:i\s+|we\s+)?(?:leave|go|head|move|walk|travel|depart|continue|proceed)\s*\.?\s*$",
    re.IGNORECASE,
)
_CONVERSATION_EXIT_RE = re.compile(
    r"^\s*(?:"
    r"that'?s\s+(?:enough|all)(?:\s+for\s+now)?|"
    r"enough\s+for\s+now|"
    r"i\s+(?:thank|nod\s+to|leave|turn\s+away\s+from)\s+(?:him|her|them|the\s+\w+)(?:\s+and\s+(?:leave|turn\s+away))?|"
    r"i\s+turn\s+away|"
    r"i\s+end\s+the\s+conversation"
    r")\.?\s*$",
    re.IGNORECASE,
)
_FOLLOWUP_FRAGMENT_RE = re.compile(
    r"^\s*(?:which|who|what|where|why|how)\b|"
    r"^\s*(?:tell\s+me|explain|go\s+on|continue|and\s+then|what\s+about)\b",
    re.IGNORECASE,
)
_PRONOUN_REFERENCE_RE = re.compile(r"\b(?:it|that|this|him|her|them|they|he|she)\b", re.IGNORECASE)
_INSPECT_PRONOUN_RE = re.compile(
    r"\b(?:inspect|examine|look\s+at|check|study|read)\s+(?:it|that|this|them)\b",
    re.IGNORECASE,
)
_SHORT_CLARIFICATION_RE = re.compile(r"^\s*(?:the\s+)?[a-z][a-z0-9 '\-]{0,48}\.?\s*$", re.IGNORECASE)
_PLAN_RE = re.compile(
    r"\b(?:plan|route|strategy|what\s+should\s+i\s+do|how\s+can\s+i|help\s+me\s+figure\s+out)\b",
    re.IGNORECASE,
)
_IMPOSSIBLE_RE = re.compile(
    r"\b(?:fly\s+to\s+the\s+moon|teleport\s+to|become\s+a\s+god|delete\s+the\s+world|rewrite\s+reality)\b",
    re.IGNORECASE,
)
_REVISION_RE = re.compile(
    r"\b(?:instead|make that|change that|i meant|revise)\b",
    re.IGNORECASE,
)
_CAUSE_QUESTION_RE = re.compile(
    r"\b(?:why|how come|what caused|the cause|for what reason)\b",
    re.IGNORECASE,
)

_CONNECTED_OPERATIONS = {"PERCEIVE", "INSPECT", "ASK", "MOVE"}
_INCIDENTAL_OPERATIONS = {
    "ACKNOWLEDGE",
    "THANK",
    "EMOTE",
    "SPEAK",
    "COMMENT",
    "GREETING",
    "FAREWELL",
    "SOCIAL_ACKNOWLEDGMENT",
}


def _clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _scene_obj(scene: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(scene, Mapping):
        return {}
    inner = scene.get("scene")
    return inner if isinstance(inner, Mapping) else scene


def _visible_scene_summary(scene: Mapping[str, Any] | None) -> str:
    current = _scene_obj(scene)
    pieces: list[str] = []
    location = _clean_text(current.get("location") or current.get("name") or current.get("id"))
    summary = _clean_text(current.get("summary") or current.get("description"))
    if location:
        pieces.append(f"You are at {location}.")
    if summary:
        pieces.append(summary)
    visible = [
        _clean_text(item.get("label") or item.get("name") or item.get("id"))
        for item in current.get("interactables") or []
        if isinstance(item, Mapping)
    ]
    exits = [
        _clean_text(item.get("label") or item.get("name") or item.get("id"))
        for item in current.get("exits") or []
        if isinstance(item, Mapping)
    ]
    if visible:
        pieces.append("Visible points of interest: " + ", ".join(item for item in visible if item) + ".")
    if exits:
        pieces.append("Known exits: " + ", ".join(item for item in exits if item) + ".")
    return " ".join(piece for piece in pieces if piece).strip()


def _scene_id(scene: Mapping[str, Any] | None) -> str:
    return _clean_text(_scene_obj(scene).get("id"))


def _catalog(scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    current_scene = _scene_obj(scene)
    sid = _scene_id(scene)
    out: dict[str, dict[str, Any]] = {}
    for item in current_scene.get("interactables") or []:
        if not isinstance(item, Mapping):
            continue
        entity_id = _clean_text(item.get("id"))
        if entity_id:
            out[entity_id] = {
                "kind": "inspect_target" if item.get("reveals_clue") else "perceive_target",
                "row": dict(item),
            }
    for item in current_scene.get("exits") or []:
        if not isinstance(item, Mapping):
            continue
        entity_id = _clean_text(item.get("id"))
        if entity_id:
            out[entity_id] = {"kind": "exit", "row": dict(item)}
    for npc in (world or {}).get("npcs") or []:
        if not isinstance(npc, Mapping):
            continue
        entity_id = _clean_text(npc.get("id"))
        loc = _clean_text(npc.get("location") or npc.get("scene_id"))
        if entity_id and sid and loc == sid:
            out[entity_id] = {"kind": "npc", "row": dict(npc)}
    return out


def _label(row: Mapping[str, Any] | None, fallback: str) -> str:
    if not isinstance(row, Mapping):
        return fallback
    return _clean_text(row.get("label") or row.get("name") or fallback) or fallback


def _aliases(row: Mapping[str, Any] | None, fallback: str) -> list[str]:
    names = [fallback, _label(row, fallback)]
    if isinstance(row, Mapping):
        names.extend(str(item) for item in (row.get("aliases") or []) if str(item).strip())
    return [item for item in {_clean_text(name).casefold(): _clean_text(name) for name in names if _clean_text(name)}.values()]


def _operation_record(
    *,
    operation: str,
    target_id: str,
    player_text: str,
    summary: str = "",
    references: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "INTERPRETED",
        "player_intent": {"summary": summary or player_text},
        "action_components": [
            {
                "operation_class": operation,
                "target_ref": target_id,
                "description": summary or player_text,
            }
        ],
        "references": dict(references or {"resolved_references": [], "unresolved_references": []}),
    }


def decision_from_delivered_exchange(
    player_text: str,
    *,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> ConversationalDecision | None:
    """Use the last delivered exchange before a provider guess can discard it."""
    from game.conversational_continuity import continuity_directive

    directive = continuity_directive(player_text, session=session, scene=scene, world=world)
    if not directive:
        return None
    text = _clean_text(player_text)
    action = str(directive.get("action") or "")
    npc_id = str(directive.get("npc_id") or "")
    name = str(directive.get("npc_name") or "")
    reason = str(directive.get("reason") or "delivered_exchange")
    if action == "ask" and npc_id:
        record = _operation_record(
            operation="ASK",
            target_id=npc_id,
            player_text=text,
            summary=f"Ask {name or npc_id}: {text}",
            references={
                "resolved_references": [{"text": "delivered exchange", "entity_id": npc_id}],
                "unresolved_references": [],
            },
        )
        return ConversationalDecision(
            category=ConversationalDecisionCategory.EXECUTE,
            primary_intention=text,
            intent_family="world_operation",
            proposed_operation="ASK",
            proposed_target=npc_id,
            proposed_record=record,
            requires_authoritative_execution=True,
            reason=reason,
            confidence=0.84,
            context_references=[f"delivered_exchange:{npc_id}"],
        )
    category = ConversationalDecisionCategory.CLARIFY if action == "clarify" else ConversationalDecisionCategory.ANSWER
    owner = "NPC" if directive.get("owner") == "npc" else "GM"
    references = [f"npc:{npc_id}", f"name:{name}"] if npc_id else []
    prop = str(directive.get("proposition_id") or "")
    if not prop and action != "clarify":
        from game.conversational_continuity import _best_exchange, delivered_exchanges

        found = _best_exchange(text, delivered_exchanges(session), npc_id)
        if isinstance(found, dict):
            prop = str(found.get("proposition_id") or "")
    if prop:
        references.append("proposition_id=" + prop)
    return ConversationalDecision(
        category=category,
        primary_intention=text,
        intent_family="dialogue_continuity",
        communication_owner=owner,
        communication_purpose="EXPLANATION" if category == ConversationalDecisionCategory.ANSWER else "CLARIFICATION",
        reason=reason,
        player_facing_text=str(directive.get("line") or ""),
        proposed_target=npc_id or None,
        execution_policy="answer_only",
        intent_modality="informational",
        context_references=references,
    )


def _conversation_context(session: Mapping[str, Any] | None) -> Mapping[str, Any]:
    ctx = session.get("conversational_context") if isinstance(session, Mapping) else None
    return ctx if isinstance(ctx, Mapping) else {}


def public_conversation_evidence(scene: Mapping[str, Any] | None, log: list | None) -> dict[str, str]:
    """Public summaries and previously emitted text only; no clue/NPC/private data."""
    evidence: dict[str, str] = {}
    summary = _visible_scene_summary(scene)
    if summary:
        evidence["scene"] = summary
    for index, fact in enumerate(_scene_obj(scene).get("visible_facts") or []):
        if isinstance(fact, str) and fact.strip():
            evidence[f"visible:{index}"] = fact.strip()
    for index, row in enumerate((log or [])[-4:]):
        if not isinstance(row, Mapping):
            continue
        gm = row.get("gm_output") or {}
        visible = row.get("player_facing_text") or (gm.get("player_facing_text") if isinstance(gm, Mapping) else "")
        if isinstance(visible, str) and visible.strip():
            evidence[f"reply:{index}"] = visible.strip()[:1200]
        resolution = row.get("resolution") or {}
        if isinstance(resolution, Mapping) and resolution.get("success") is True and resolution.get("kind") in {"investigate", "discover_clue"}:
            action_id = str(resolution.get("action_id") or "")
            if action_id and visible:
                evidence[f"cause:reply:{index}"] = (
                    f"Your inspection of {action_id.replace('_', ' ')} revealed the detail. "
                    "That explains how you found it; its origin or purpose has not been established by that discovery."
                )
        social = resolution.get("social") if isinstance(resolution, Mapping) else None
        if isinstance(social, Mapping) and social.get("target_resolved") and visible:
            # Latest spoken inability/refusal is conversation evidence too;
            # older revealed topics must not stand in for a newer reply.
            evidence["npc_latest_reply"] = str(visible).strip()[:1200]
        if isinstance(social, Mapping) and isinstance(social.get("topic_revealed"), Mapping):
            topic = social["topic_revealed"]
            if social.get("npc_id") and topic.get("id") and topic.get("text"):
                evidence[f"npc:{social['npc_id']}:{topic['id']}"] = str(topic["text"])
    return evidence


def _reclassify_direct_npc_address(
    record: Mapping[str, Any],
    text: str,
    *,
    scene=None,
    world=None,
    session=None,
) -> dict[str, Any]:
    """A grounded direct address stays NPC-directed when the recipient label says GM."""
    prepared = dict(record)
    components = [dict(component) if isinstance(component, Mapping) else component for component in (prepared.get("action_components") or [])]
    asks = [component for component in components if isinstance(component, dict) and component.get("operation_class") == "ASK" and component.get("target_ref")]
    communication = prepared.get("communication") if isinstance(prepared.get("communication"), Mapping) else {}
    if len(asks) != 1 or str(communication.get("recipient") or "") != "GM":
        return prepared
    from game.ordinary_semantic_ownership import assess_addressee_grounding

    grounding = assess_addressee_grounding(
        text,
        scene=scene,
        world=world,
        session=session,
        proposed_target_id=str(asks[0].get("target_ref") or ""),
    )
    if not (grounding.get("direct_address") and grounding.get("operation_eligibility") == "executable" and grounding.get("target_id")):
        return prepared
    updated = dict(communication)
    updated["recipient"] = "NPC"
    if str(updated.get("purpose") or "") in {"", "CLARIFICATION"}:
        updated["purpose"] = "QUESTION"
    prepared["communication"] = updated
    prepared["communication_mode"] = "IN_WORLD_ACTION"
    if not prepared.get("interpretation_status"):
        prepared["interpretation_status"] = "INTERPRETED"
    for component in components:
        if isinstance(component, dict) and component.get("operation_class") == "ASK":
            component["target_ref"] = grounding["target_id"]
    prepared["action_components"] = components
    prepared["authorization_conflict"] = {
        "provider_recipient": "GM",
        "resolved_owner": "NPC",
        "target_id": grounding["target_id"],
        "conflict_status": grounding.get("conflict_status") or "resolved_by_explicit_wording",
    }
    return prepared


def _pending_revision_decision(text: str, *, session, scene, purpose: str) -> ConversationalDecision | None:
    """Revise an unexecuted intention. Do not execute it and do not undo a resolved one."""
    if purpose == "WITHDRAWAL" or not (purpose == "CORRECTION" or _REVISION_RE.search(text)):
        return None
    ctx = _conversation_context(session)
    pending = ctx.get("pending_intention") if isinstance(ctx.get("pending_intention"), Mapping) else None
    if pending is None and isinstance(ctx.get("pending_clarification"), Mapping):
        pending = ctx.get("pending_clarification")
    scene_id = _scene_id(scene)
    if isinstance(pending, Mapping) and str(pending.get("status") or "pending") != "executed":
        if pending.get("scene_id") and scene_id and pending.get("scene_id") != scene_id:
            pending = None
        else:
            revised = dict(pending)
            revised["revised_text"] = text
            revised["status"] = "pending"
            return ConversationalDecision(
                category=ConversationalDecisionCategory.CLARIFY,
                primary_intention=text,
                intent_family="clarification",
                communication_owner="GM",
                communication_purpose="CORRECTION",
                reason="pending_intention_revised",
                player_facing_text=(
                    "I've revised that unexecuted intention. It has not been attempted. "
                    + str(revised.get("clarification") or "Tell me who it is addressed to before I carry it out.")
                ),
                context_update=_context_update(pending=revised, pending_set=True, intention=revised, intention_set=True),
                execution_policy="answer_only",
                intent_modality="informational",
            )
    executed = ctx.get("last_executed_intention")
    if isinstance(executed, Mapping) and executed.get("status") == "executed":
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER,
            primary_intention=text,
            intent_family="communication",
            communication_owner="GM",
            communication_purpose="CORRECTION",
            reason="executed_intention_not_reversible",
            player_facing_text="That action already resolved, so I cannot undo it. You can take a new action if you want.",
            execution_policy="answer_only",
            intent_modality="informational",
        )
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=text,
        intent_family="clarification",
        communication_owner="GM",
        communication_purpose="CORRECTION",
        reason="no_pending_intention",
        player_facing_text="I don't have an unexecuted intention to revise. What do you want to change?",
        execution_policy="answer_only",
        intent_modality="informational",
    )


def _communication_decision(record: Mapping[str, Any], text: str, *, session=None, scene=None, world=None) -> ConversationalDecision | None:
    communication = record.get("communication")
    if not isinstance(communication, Mapping):
        return None
    owner = str(communication.get("recipient") or "AMBIGUOUS")
    purpose = str(communication.get("purpose") or "CLARIFICATION")
    if record.get("communication_mode") == "RULES_QUESTION" and owner in {"GM", "SESSION"}:
        owner, purpose = "SESSION", "RULES"
    components = record.get("action_components") or []
    status = str(record.get("interpretation_status") or "")
    evidence_refs = list(communication.get("evidence_refs") or [])
    if status and status != "INTERPRETED":
        evidence = record.get("public_evidence") if isinstance(record.get("public_evidence"), Mapping) else {}
        selected = bool(evidence_refs) and all(ref in evidence for ref in evidence_refs)
        if not (selected and owner == "GM" and purpose in {"QUESTION", "DESCRIPTION", "EXPLANATION", "RECALL", "RULES"}):
            return None
    ask_targets = [
        str(component.get("target_ref") or "")
        for component in components
        if isinstance(component, Mapping) and component.get("operation_class") == "ASK" and component.get("target_ref")
    ]
    from game.ordinary_semantic_ownership import (
        assess_addressee_grounding,
        conversational_authorization_record,
        pending_addressee_clarification,
    )

    grounding = assess_addressee_grounding(
        text,
        scene=scene,
        world=world,
        session=session,
        proposed_target_id=ask_targets[0] if len(ask_targets) == 1 else None,
    )
    if grounding.get("direct_address") and grounding.get("operation_eligibility") == "requires_clarification":
        pending = pending_addressee_clarification(grounding, text, scene)
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=text,
            intent_family="clarification",
            communication_owner="GM",
            communication_purpose="CLARIFICATION",
            reason="unresolved_addressee",
            player_facing_text=str(grounding.get("clarification") or "Which person do you mean? Nothing has been attempted."),
            context_update=_context_update(pending=pending, pending_set=True, intention=pending, intention_set=True),
            execution_policy="answer_only",
            intent_modality="informational",
            proposed_operation="ASK",
            proposed_target=ask_targets[0] if ask_targets else None,
            missing_information=["interlocutor"],
            authorization=conversational_authorization_record(
                grounding,
                player_text=text,
                authority_provenance="communication_decision",
            ),
        )
    if purpose == "CONFIRMATION":
        # The semantic call identifies assent; the existing continuation owner
        # supplies and revalidates the actual pending operation.
        resumed = _resume_pending_clarification(player_text="Yes.", scene=scene, session=session)
        if resumed is not None:
            return resumed
    if purpose == "CORRECTION":
        pending = _conversation_context(session).get("pending_clarification") or {}
        if pending.get("kind") == "compound_sequence" and pending.get("scene_id") == _scene_id(scene) and len(components) == 1:
            component = components[0]
            operation = component.get("operation_class")
            if operation in _CONNECTED_OPERATIONS and component.get("target_ref"):
                steps = [{"operation": operation, "target_id": component["target_ref"],
                          "text": component.get("description") or text, "supported": True},
                         *[dict(s) for s in pending.get("steps", [])[1:] if isinstance(s, Mapping)]]
                revised = _compound_clarification(text, steps, scene=scene, world=world, clear=False, incidental=[])
                return ConversationalDecision(**{**revised.__dict__, "communication_owner": "GM", "communication_purpose": purpose})
    if owner == "GM" and purpose in {"QUESTION", "DESCRIPTION", "EXPLANATION", "RECALL", "RULES"} and any(
        isinstance(c, Mapping) and (c.get("operation_class") in {"MOVE", "ATTACK", "USE_VISIBLE_OBJECT", "FOLLOW"}
                                    or (len(components) > 1 and c.get("operation_class") == "ASK" and c.get("target_ref")))
        for c in components
    ):
        owner = "MIXED"
    if owner in {"CHARACTER", "NPC"} and purpose in {"ACTION", "OBSERVATION", "QUESTION", "CLARIFICATION", "RECALL"} and record.get("action_components"):
        # A provider ASK does not turn a third-person question into NPC dialogue.
        ungrounded_gm_question = (
            any(isinstance(c, Mapping) and c.get("operation_class") == "ASK" for c in components)
            and grounding.get("operation_eligibility") != "executable"
            and _QUESTION_START_RE.search(text)
            and not re.search(r"\b(?:you|your|you're|youre)\b", text, re.IGNORECASE)
        )
        if ungrounded_gm_question:
            owner = "GM"
            if purpose not in {"EXPLANATION", "RECALL", "RULES", "DESCRIPTION"}:
                purpose = "QUESTION"
        else:
            return None
    if owner == "GM" and purpose == "OBSERVATION" and components:
        if all(isinstance(c, Mapping) and c.get("operation_class") in {"PERCEIVE", "INSPECT"} for c in components):
            return None
    revision = _pending_revision_decision(text, session=session, scene=scene, purpose=purpose)
    if revision is not None:
        return revision
    category = ConversationalDecisionCategory.ANSWER
    update = None
    if purpose in {"CORRECTION", "WITHDRAWAL"}:
        answer = "I've set aside the unexecuted intention. Anything already resolved still stands."
        if purpose == "CORRECTION":
            answer += " What do you want to change?"
        update = _context_update(pending=None, pending_set=True, intention=None, intention_set=True, clear_interlocutor=False)
    elif owner == "MIXED":
        category = ConversationalDecisionCategory.CLARIFY
        answer = "Let's settle the question before attempting the action. "
        evidence = record.get("public_evidence") or {}
        answer += " ".join(str(v) for v in evidence.values()) if evidence else "That condition is not established yet."
        answer += " No part of the action has been attempted."
    elif purpose == "TENTATIVE":
        answer = "We can consider that before committing. Nothing has been attempted."
    elif owner == "AMBIGUOUS" or purpose == "CONFIRMATION" or (
        purpose == "CLARIFICATION" and (
            not record.get("public_evidence")
            or record.get("interpretation_status") != "INTERPRETED"
            or (record.get("references") or {}).get("unresolved_references")
        )
    ) or (owner == "CHARACTER" and not components):
        category = ConversationalDecisionCategory.CLARIFY
        answer = str(record.get("clarification_question") or "").strip() or "Which person, object, or pending action do you mean?"
    else:
        evidence = record.get("public_evidence") if isinstance(record.get("public_evidence"), Mapping) else {}
        if evidence_refs:
            evidence = {key: evidence[key] for key in evidence_refs if key in evidence}
        answer = " ".join(dict.fromkeys(str(value) for value in evidence.values()))
        if purpose == "EXPLANATION" and answer and _CAUSE_QUESTION_RE.search(text) and not any(str(ref).startswith("cause:") for ref in evidence):
            answer += " That establishes the observation or result; its cause has not been established."
        if not answer:
            from game.conversational_continuity import active_followup_target

            follow = active_followup_target(text, session=session, scene=scene, world=world)
            if follow:
                record = _operation_record(
                    operation="ASK",
                    target_id=follow,
                    player_text=text,
                    summary=text,
                    references={"resolved_references": [{"text": "active interlocutor", "entity_id": follow}], "unresolved_references": []},
                )
                return ConversationalDecision(
                    category=ConversationalDecisionCategory.EXECUTE,
                    primary_intention=text,
                    intent_family="world_operation",
                    proposed_operation="ASK",
                    proposed_target=follow,
                    proposed_record=record,
                    requires_authoritative_execution=True,
                    reason="active_conversation_followup",
                    player_facing_text="",
                    execution_policy="",
                )
            answer = "That has not been established in the information available to you."
            if purpose == "RULES" or owner == "SESSION":
                answer = "I don't have an established ruling for that question. No action or roll has been made."
    return ConversationalDecision(
        category=category, primary_intention=text, intent_family="gm_communication" if owner == "GM" else "communication",
        communication_owner=owner, communication_purpose=purpose,
        reason="communication_before_execution", player_facing_text=answer,
        context_references=list((record.get("public_evidence") or {}).keys()),
        context_update=update, execution_policy="answer_only", intent_modality="informational",
        secondary_intentions=[dict(c) for c in components if isinstance(c, Mapping)] if owner == "MIXED" or category == ConversationalDecisionCategory.CLARIFY else [],
    )


def _gm_continuation_decision(text: str, session: Mapping[str, Any] | None, log: list | None) -> ConversationalDecision | None:
    """Resolve clear facilitator follow-ups before an active NPC can capture them."""
    if re.match(r"^(?:no[,.!]?\s*)?(?:actually[,.]?\s*)?(?:never\s+mind|forget\s+(?:it|that|the\s+plan)|cancel|don't\s+(?:do|open|move|go))\b", text, re.I) or (
        _conversation_context(session).get("pending_clarification") and re.fullmatch(r"(?:no|nope|not now)[.!]?", text, re.I)
    ):
        return _communication_decision({"communication": {"recipient": "GM", "purpose": "WITHDRAWAL"}}, text)
    if re.match(r"^actually\b", text, re.I):
        return _communication_decision({"communication": {"recipient": "GM", "purpose": "CORRECTION"}}, text)
    is_explanation = bool(re.match(r"^why\b", text, re.I))
    explicit_gm = bool(re.search(r"\b(?:GM|DM|game master|you\s+(?:mean|said|say)|remind\s+me)\b", text, re.I))
    ctx = _conversation_context(session).get("last_gm_exchange") or {}
    refused = isinstance(ctx, Mapping) and ctx.get("category") == "DECLINE"
    if not (explicit_gm or (is_explanation and (refused or re.search(r"\b(?:I|can't|cannot|couldn't|not)\b", text, re.I)))):
        return None
    # A declared character utterance remains owned by the in-world recipient.
    if re.match(r"^(?:I|we)\s+(?:ask|tell|say|warn|explain)\b", text, re.I):
        return None
    from game.live_chat_interpretation import production_live_interpretation_enabled
    if production_live_interpretation_enabled() and not (is_explanation and refused):
        return None
    evidence = public_conversation_evidence(None, log)
    last = list(evidence.values())[-1:]
    record = {"communication": {"recipient": "GM", "purpose": "EXPLANATION"},
              "public_evidence": {"last_reply": last[0]} if last else {}}
    return _communication_decision(record, text)


def _interaction_context(session: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(session, Mapping):
        return {}
    ctx = session.get("interaction_context")
    return ctx if isinstance(ctx, Mapping) else session


def _active_interlocutor(session: Mapping[str, Any] | None, catalog: Mapping[str, Any]) -> str:
    ctx = _interaction_context(session)
    kind = _clean_text(ctx.get("active_interaction_kind")).casefold()
    target = _clean_text(ctx.get("active_interaction_target_id"))
    if kind == "social" and target in catalog and catalog[target].get("kind") == "npc":
        return target
    return ""


def _context_update(
    *,
    pending: Mapping[str, Any] | None = None,
    pending_set: bool = False,
    focused: Mapping[str, Any] | None = None,
    focused_set: bool = False,
    clear_interlocutor: bool = False,
    intention: Mapping[str, Any] | None = None,
    intention_set: bool = False,
    executed: Mapping[str, Any] | None = None,
    executed_set: bool = False,
) -> dict[str, Any]:
    conversational: dict[str, Any] = {}
    if pending_set:
        conversational["pending_clarification"] = None if pending is None else dict(pending)
    if focused_set:
        conversational["focused_destination"] = None if focused is None else dict(focused)
    if intention_set:
        conversational["pending_intention"] = None if intention is None else dict(intention)
    if executed_set:
        conversational["last_executed_intention"] = None if executed is None else dict(executed)
    update: dict[str, Any] = {}
    if conversational:
        update["conversational_context"] = conversational
    if clear_interlocutor:
        update["interaction_context"] = {
            "active_interaction_target_id": None,
            "active_interaction_kind": None,
            "interaction_mode": "none",
            "engagement_level": "none",
        }
    return update


def _context_update_with_pending(pending: Mapping[str, Any] | None) -> dict[str, Any]:
    return _context_update(pending=pending, pending_set=True)


def _context_update_clear_pending(*, clear_interlocutor: bool = False) -> dict[str, Any]:
    return _context_update(pending=None, pending_set=True, clear_interlocutor=clear_interlocutor)


def _pending_clarification_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    if not _INSPECT_PRONOUN_RE.search(player_text):
        return None
    catalog = _catalog(scene, world)
    candidates = [
        (entity_id, info)
        for entity_id, info in catalog.items()
        if str(info.get("kind") or "") in {"inspect_target", "perceive_target"}
    ]
    if len(candidates) == 1:
        entity_id, info = candidates[0]
        record = _operation_record(
            operation="INSPECT",
            target_id=entity_id,
            player_text=player_text,
            summary=f"Inspect {_label(info.get('row'), entity_id)}.",
            references={"resolved_references": [{"text": "it", "entity_id": entity_id}], "unresolved_references": []},
        )
        return decision_from_interpretation_record(record, player_text=player_text)
    if len(candidates) > 1:
        choices = [
            {"entity_id": entity_id, "label": _label(info.get("row"), entity_id)}
            for entity_id, info in candidates[:4]
        ]
        labels = [choice["label"] for choice in choices]
        pending = {
            "kind": "missing_target",
            "operation": "INSPECT",
            "original_text": player_text,
            "choices": choices,
            "scene_id": _scene_id(scene),
        }
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention="Inspect a recently referenced object.",
            intent_family="clarification",
            missing_information=["target"],
            context_references=["ambiguous_pronoun_reference"],
            reason="ambiguous_contextual_reference",
            confidence=0.78,
            ambiguity="More than one visible object could match the pronoun.",
            player_facing_text="Do you mean " + " or ".join(labels) + "?",
            context_update=_context_update_with_pending(pending),
        )
    return None


def _resume_pending_clarification(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    pending = _conversation_context(session).get("pending_clarification")
    if not isinstance(pending, Mapping):
        return None
    if _scene_id(scene) and _clean_text(pending.get("scene_id")) and _scene_id(scene) != _clean_text(pending.get("scene_id")):
        if _AGENT_RE.search(player_text):
            return None
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=_clean_text(player_text),
            intent_family="clarification",
            missing_information=["intention"],
            reason="pending_clarification_expired_scene_changed",
            confidence=0.65,
            player_facing_text="That earlier clarification no longer applies here. What are you trying to do now?",
            context_update=_context_update_clear_pending(),
        )
    kind = _clean_text(pending.get("kind"))
    operation = _clean_text(pending.get("operation")).upper()
    if kind == "deferred_intentions" and _YES_RE.match(player_text):
        return ConversationalDecision(
            category=ConversationalDecisionCategory.DECLINE, primary_intention=player_text,
            intent_family="unsupported_world_operation", reason="deferred_intention_not_eligible",
            player_facing_text="The remaining intention cannot be resolved as stated. Nothing further has been attempted.",
            secondary_intentions=list(pending.get("steps") or []), context_update=_context_update_clear_pending(),
        )
    if kind in {"missing_destination", "ambiguous_destination", "compound_sequence"} or (
        operation == "MOVE" and kind != "missing_target"
    ):
        return _resume_bounded_pending(player_text=player_text, scene=scene, session=session, pending=pending)
    if kind == "ambiguous_addressee" and operation == "ASK":
        choices = [choice for choice in (pending.get("choices") or []) if isinstance(choice, Mapping)]
        selected: Mapping[str, Any] | None = None
        if _YES_RE.match(player_text):
            if len(choices) != 1:
                return ConversationalDecision(
                    category=ConversationalDecisionCategory.CLARIFY,
                    primary_intention=player_text,
                    intent_family="clarification",
                    reason="confirmation_does_not_choose",
                    player_facing_text="Yes does not choose among them. Name the person you mean. Nothing has been attempted.",
                    communication_owner="GM",
                    communication_purpose="CLARIFICATION",
                )
            selected = choices[0]
        else:
            text_low = re.sub(r"[^a-z0-9 ]", "", _clean_text(player_text).casefold()).strip().removeprefix("the ")
            matches = []
            for choice in choices:
                entity_id = _clean_text(choice.get("entity_id"))
                label = _clean_text(choice.get("label"))
                label_words = set(re.findall(r"[a-z0-9]+", label.casefold()))
                tokens = {entity_id.casefold(), label.casefold(), label.casefold().removeprefix("the ")} | label_words
                if text_low and (text_low in tokens or any(text_low == token or text_low in token for token in tokens)):
                    matches.append(choice)
            if len(matches) == 1:
                selected = matches[0]
            elif matches:
                return ConversationalDecision(
                    category=ConversationalDecisionCategory.CLARIFY,
                    primary_intention=player_text,
                    intent_family="clarification",
                    reason="confirmation_still_ambiguous",
                    player_facing_text="Which of those people do you mean? Nothing has been attempted.",
                    communication_owner="GM",
                    communication_purpose="CLARIFICATION",
                )
            else:
                return None
        entity_id = _clean_text(selected.get("entity_id"))
        label = _clean_text(selected.get("label")) or entity_id
        original = _clean_text(pending.get("revised_text") or pending.get("original_text")) or player_text
        record = _operation_record(
            operation="ASK",
            target_id=entity_id,
            player_text=original,
            summary=f"Ask {label}.",
            references={"resolved_references": [{"text": player_text, "entity_id": entity_id}], "unresolved_references": []},
        )
        return ConversationalDecision(
            category=ConversationalDecisionCategory.EXECUTE,
            primary_intention=f"Ask {label}.",
            intent_family="world_operation",
            proposed_operation="ASK",
            proposed_target=entity_id,
            proposed_record=record,
            requires_authoritative_execution=True,
            reason="confirmed_pending_addressee",
            player_facing_text="",
            context_update=_context_update(pending=None, pending_set=True, intention=None, intention_set=True),
            communication_owner="NPC",
            communication_purpose="QUESTION",
        )
    if kind != "missing_target" or operation != "INSPECT":
        return None
    if not _SHORT_CLARIFICATION_RE.match(player_text) or _QUESTION_START_RE.search(player_text):
        return None
    text_low = _clean_text(player_text).casefold().removeprefix("the ")
    matches: list[Mapping[str, Any]] = []
    for choice in pending.get("choices") or []:
        if not isinstance(choice, Mapping):
            continue
        entity_id = _clean_text(choice.get("entity_id"))
        label = _clean_text(choice.get("label"))
        tokens = {entity_id.casefold(), label.casefold(), label.casefold().removeprefix("the ")}
        if text_low in tokens or any(text_low and text_low in token for token in tokens):
            matches.append(choice)
    if len(matches) != 1:
        return None
    entity_id = _clean_text(matches[0].get("entity_id"))
    label = _clean_text(matches[0].get("label")) or entity_id
    record = _operation_record(
        operation="INSPECT",
        target_id=entity_id,
        player_text=_clean_text(pending.get("original_text")) or player_text,
        summary=f"Inspect {label}.",
        references={"resolved_references": [{"text": player_text, "entity_id": entity_id}], "unresolved_references": []},
    )
    decision = decision_from_interpretation_record(record, player_text=player_text)
    return ConversationalDecision(
        **{**decision.__dict__, "context_update": _context_update_clear_pending()}
    )


def _active_dialogue_followup_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    text = _clean_text(player_text)
    low = text.casefold()
    catalog = _catalog(scene, world)
    active_id = _active_interlocutor(session, catalog)
    if not active_id:
        return None
    if _CONVERSATION_EXIT_RE.match(text):
        npc_label = _label(catalog[active_id].get("row"), active_id)
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER,
            primary_intention="End the active conversation.",
            intent_family="conversation_exit",
            context_references=[active_id],
            reason="conversation_exit_expression",
            confidence=0.84,
            player_facing_text=f"You end the conversation with {npc_label}.",
            context_update=_context_update_clear_pending(clear_interlocutor=True),
        )
    # The existing live call classifies recipient as well as action. Do not let
    # an NPC slot capture every question before that boundary can see it.
    from game.live_chat_interpretation import production_live_interpretation_enabled
    if production_live_interpretation_enabled():
        return None
    is_question = bool(_QUESTION_START_RE.search(text) or "?" in text)
    is_followup = bool(_FOLLOWUP_FRAGMENT_RE.search(text) or _PRONOUN_REFERENCE_RE.search(text))
    if not (is_question or is_followup):
        return None
    if re.search(r"\b(?:attack|follow|move|go|head|walk|travel|inspect|examine|open|take|steal|cast)\b", low):
        return None
    record = _operation_record(
        operation="ASK",
        target_id=active_id,
        player_text=text,
        summary=f"Ask {_label(catalog[active_id].get('row'), active_id)}: {text}",
        references={
            "resolved_references": [{"text": "active interlocutor", "entity_id": active_id}],
            "unresolved_references": [],
        },
    )
    decision = decision_from_interpretation_record(record, player_text=text)
    return ConversationalDecision(
        **{
            **decision.__dict__,
            "context_references": [*decision.context_references, f"active_interlocutor:{active_id}"],
            "reason": "active_interlocutor_followup",
            "confidence": 0.82,
        }
    )


def _recent_visible_answer(text: str, log: list | None) -> tuple[str, str] | None:
    from game.live_chat_interpretation import production_live_interpretation_enabled
    if production_live_interpretation_enabled():
        # A previous passage may share a subject without answering this question.
        # Let the existing semantic call select evidence and question purpose.
        return None
    low = text.casefold()
    if not isinstance(log, list):
        return None
    if not any(word in low for word in ("that", "earlier", "mentioned", "said", "person", "detail", "again")):
        return None
    for row in reversed(log[-6:]):
        if not isinstance(row, Mapping):
            continue
        gm = row.get("gm_output") if isinstance(row.get("gm_output"), Mapping) else {}
        visible = _clean_text(row.get("player_facing_text") or gm.get("player_facing_text"))
        if visible:
            return (
                "From what has already been established: " + visible,
                "recent_visible_turn",
            )
    return None


def _focused_bridge_clarification(reason: str, operation: str | None = None) -> tuple[str, list[str]]:
    op = str(operation or "").strip().upper()
    if reason == "missing_target":
        if op == "MOVE":
            return "Where are you trying to go?", ["destination"]
        if op == "ASK":
            return "Who are you asking?", ["interlocutor"]
        if op in {"INSPECT", "PERCEIVE"}:
            return "Which object or area do you mean?", ["target"]
    if reason == "target_not_visible":
        return "I cannot identify that target from what is visible here. Which visible target do you mean?", ["visible_target"]
    if reason == "operation_incompatible_with_entity_kind":
        return "That target does not fit the action as stated. What are you trying to accomplish?", ["compatible_target"]
    if reason == "unresolved_references":
        return "Which person, place, or thing do you mean?", ["reference"]
    if reason == "unsupported_operation":
        return "I cannot route that as a supported gameplay operation yet.", []
    if reason == "exit_has_no_authored_destination":
        return "That way is closed. There is no established passage, and you stay where you are.", ["destination"]
    if reason == "unknown_destination_scene":
        return "That destination is not an established place you can enter from here. You stay where you are.", ["destination"]
    return "What are you trying to accomplish?", ["intention"]


_GENERIC_PLACE_TOKENS = frozenset({"gate", "door", "road", "street", "way", "place", "path", "entrance", "exit"})
_AGENT_RE = re.compile(r"^\s*(?:i|we|let's|lets|let\s+us|i'm|im)\b", re.IGNORECASE)
_MOVE_CUE_RE = re.compile(
    r"\b(?:go(?:es|ing)?|(?<!my )(?<!our )(?<!your )(?<!his )(?<!her )(?<!their )head(?:s|ing)?|walk(?:s|ing)?|travel(?:s|ing|led)?|"
    r"leave|leaves|leaving|depart(?:s|ing)?|return(?:s|ing)?|proceed(?:s|ing)?|"
    r"stroll(?:s|ing)?|hurry|hurries|hurrying|set\s+off|bound\s+for|"
    r"make\s+for|makes\s+for|making\s+for|make\s+(?:my|our)\s+way|makes\s+(?:my|our)\s+way|"
    r"making\s+(?:my|our)\s+way|head\s+out|start\s+off|start\s+heading|start\s+down)\b",
    re.IGNORECASE,
)
_DEST_PREP_RE = re.compile(
    r"\b(?:back\s+to|down\s+to|over\s+to|toward|towards|through|into|to|for)\s+(.+)$",
    re.IGNORECASE,
)
_BACK_RE = re.compile(
    r"\b(?:go\s+back|head\s+back|walk\s+back|turn\s+around|return(?:ing)?|came\s+from|where\s+we\s+were)\b",
    re.IGNORECASE,
)
_DEICTIC_DEST_RE = re.compile(
    r"^(?:the\s+)?(?:place|spot)\s+we\s+came\s+from$|^where\s+we\s+(?:came\s+from|were)$|^back$",
    re.IGNORECASE,
)
_HYPOTHETICAL_RE = re.compile(
    r"\b(?:what\s+would\s+happen\s+if|what\s+if|what\s+happens\s+if|suppose|supposing|imagine\s+if)\b",
    re.IGNORECASE,
)
_TENTATIVE_RE = re.compile(
    r"\b(?:was\s+thinking|am\s+thinking|i'm\s+thinking|im\s+thinking|thinking\s+about|"
    r"considering|might|maybe|perhaps|on\s+my\s+mind|been\s+meaning)\b",
    re.IGNORECASE,
)
_PLANNING_RE = re.compile(
    r"\b(?:i'?ll\s+need\s+to|i\s+will\s+need\s+to|i\s+need\s+to\s+find|i\s+should\s+find|"
    r"i\s+should\s+probably|my\s+plan\s+is)\b",
    re.IGNORECASE,
)
_STAY_RE = re.compile(
    r"\b(?:without\s+leaving|i\s+don'?t\s+(?:go|leave|move)|i\s+stay\s+here|we\s+stay\s+here)\b",
    re.IGNORECASE,
)
_INFO_MOVE_RE = re.compile(
    r"\b(?:can|could|may)\s+(?:i|we)\s+(?:reach|get|go|make\s+it|walk)\b|"
    r"\b(?:within\s+reach|reachable)\b|"
    r"\bhow\s+(?:do|can)\s+(?:i|we)\s+(?:get|go|reach)\b|"
    r"\b(?:which|what)\s+way\s+to\b|"
    r"\b(?:is\s+it|would\s+it\s+be)\s+possible\b|"
    r"\b(?:am\s+i|are\s+we)\s+able\b",
    re.IGNORECASE,
)
_CAPABILITY_RE = re.compile(
    r"\b(?:could|can|would)\s+i\b.*\b(?:open|pick|unlock|reach|enter|cross|leave|go|walk)\b|"
    r"\b(?:is\s+it|would\s+it\s+be)\s+possible\s+to\b|"
    r"\bam\s+i\s+able\s+to\b",
    re.IGNORECASE,
)
_INSPECT_CUE_RE = re.compile(r"\b(?:inspect|examine|look\s+at|check|study|read)\b", re.IGNORECASE)
_ASK_CUE_RE = re.compile(r"\b(?:ask|question)\b", re.IGNORECASE)
_OTHER_CUE_RE = re.compile(
    r"\b(?:open|pick|unlock|attack|draw|sheath|sheathe|unsheathe|put\s+away)\b",
    re.IGNORECASE,
)
_WATCH_RE = re.compile(r"\b(?:keep\s+an\s+eye|watch|watching)\b", re.IGNORECASE)
_SOCIAL_EXIT_RE = re.compile(
    r"\b(?:thank|thanks|nod|wave|ignore|turn\s+away|stop\s+talking)\b|"
    r"\bi'?ll\s+(?:return|be\s+back|come\s+back)\b",
    re.IGNORECASE,
)
_SPLIT_RE = re.compile(r"\s*(?:;|,?\s+then\s+|\s+and\s+then\s+|\s+while\s+)\s*", re.IGNORECASE)
_YES_RE = re.compile(
    r"^\s*(?:yes|yeah|yep|do\s+that|do\s+the\s+first(?:\s+one)?|the\s+first(?:\s+one)?|go\s+ahead|(?:all\s+right|alright|okay|ok|sure)(?:,?\s+(?:proceed|go\s+ahead))?)[.!]?\s*$",
    re.IGNORECASE,
)
_INCOMPLETE_GOAL_RE = re.compile(
    r"\b(?:want\s+to\s+get\s+out|need\s+to\s+get\s+out|want\s+to\s+leave|get\s+out\s+of\s+here|"
    r"start\s+heading\s+out|head\s+out|start\s+off)\b",
    re.IGNORECASE,
)
_STATIVE_RE = re.compile(r"\b(?:is|are|was|were|seems|seem|looks)\b", re.IGNORECASE)
_VISITING_RE = re.compile(r"\b(?:visiting|visit)\s+(?:the\s+)?(.+)$", re.IGNORECASE)
_LEAVE_OBJECT_RE = re.compile(r"\b(?:leave|leaves|leaving)\s+(?:the\s+|a\s+)?(.+)$", re.IGNORECASE)
_OBJECT_RE = re.compile(
    r"\b(?:inspect|examine|look\s+at|check|study|read|open|pick|unlock|ask|watch|watching)\s+(?:the\s+|a\s+)?(.+)$",
    re.IGNORECASE,
)


def _norm_place(text: str) -> str:
    raw = _clean_text(text).casefold().replace("'", "")
    raw = re.sub(r"[^a-z0-9\s]", " ", raw)
    raw = re.sub(r"\b(?:the|a|an|to|toward|towards)\b", " ", raw)
    for src, dst in (("northern", "north"), ("southern", "south"), ("eastern", "east"), ("western", "west")):
        raw = re.sub(rf"\b{src}\b", dst, raw)
    return re.sub(r"\s+", " ", raw).strip()


def _place_match(phrase: str, name: str) -> bool:
    left = _norm_place(phrase)
    right = _norm_place(name)
    if not left or not right or len(right) < 3:
        return False
    if left == right:
        return True
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if left_tokens <= right_tokens or right_tokens <= left_tokens:
        overlap = left_tokens & right_tokens
        if overlap and overlap <= _GENERIC_PLACE_TOKENS and left != right:
            return left_tokens <= _GENERIC_PLACE_TOKENS
        return bool(overlap)
    return False


def _exit_rows(scene: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _scene_obj(scene).get("exits") or []:
        if isinstance(item, Mapping) and _clean_text(item.get("id")):
            rows.append(dict(item))
    return rows


def _exit_names(row: Mapping[str, Any]) -> list[str]:
    names = [_label(row, _clean_text(row.get("id"))), _clean_text(row.get("id")).replace("_", " ").replace("-", " ")]
    names.extend(str(item) for item in (row.get("aliases") or []) if str(item).strip())
    return [item for item in names if _clean_text(item)]


def _unique_exit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        exit_id = _clean_text(row.get("id"))
        if exit_id and exit_id not in seen:
            seen.add(exit_id)
            found.append(row)
    return found


def _matching_exits(phrase: str, exits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in exits:
        if any(_place_match(phrase, name) for name in _exit_names(row)):
            hits.append(row)
    return _unique_exit_rows(hits)


def _mentioned_exits(text: str, exits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    norm = _norm_place(text)
    hits: list[dict[str, Any]] = []
    for row in exits:
        for name in _exit_names(row):
            cleaned = _norm_place(name)
            if cleaned and re.search(rf"\b{re.escape(cleaned)}\b", norm):
                hits.append(row)
                break
    return _unique_exit_rows(hits)


def _destination_phrase(text: str) -> str:
    cleaned = re.sub(r"\s+(?:from here|right now|instead)\b.*$", "", _clean_text(text), flags=re.IGNORECASE)
    match = None
    for item in _DEST_PREP_RE.finditer(cleaned):
        match = item
    if match is None:
        return ""
    dest = re.split(r"\s+(?:and|then|while|but)\s+", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
    dest = dest.strip(" .?!")
    if _DEICTIC_DEST_RE.match(_norm_place(dest)) or _DEICTIC_DEST_RE.match(_clean_text(dest)):
        return ""
    return dest


def _question_destination(text: str) -> str:
    direct = _destination_phrase(text)
    if direct:
        return direct
    cleaned = re.sub(r"\s+(?:from here|right now|instead)\b.*$", "", _clean_text(text), flags=re.IGNORECASE)
    patterns = (
        r"\b(?:reach|visit|get\s+to|make\s+it\s+to)\s+(.+)$",
        r"\b(?:is|are)\s+(.+?)\s+(?:within\s+reach|reachable)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if not match:
            continue
        dest = re.split(r"\s+(?:and|then|while|but)\s+", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
        dest = dest.strip(" .?!")
        if dest and not _DEICTIC_DEST_RE.match(_norm_place(dest)):
            return dest
    return ""


def _leave_object(text: str) -> str:
    match = _LEAVE_OBJECT_RE.search(_clean_text(text))
    if not match:
        return ""
    return re.split(r"\s+(?:and|then|while|but|behind)\s+", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0].strip(" .?!")


def _object_phrase(text: str) -> str:
    match = _OBJECT_RE.search(_clean_text(text))
    if not match:
        return ""
    return re.split(r"\s+(?:and|then|while|but|about)\s+", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0].strip(" .?!")


def _split_clauses(text: str) -> list[str]:
    parts = [part.strip(" ,.") for part in _SPLIT_RE.split(text) if part.strip(" ,.")]
    clauses: list[str] = []
    for part in parts or [text]:
        pieces = re.split(r"\s+and\s+", part, flags=re.IGNORECASE)
        if len(pieces) == 2 and all(_clause_has_verb(piece) for piece in pieces):
            clauses.extend(piece.strip(" ,.") for piece in pieces if piece.strip(" ,."))
        else:
            clauses.append(part.strip(" ,."))
    return [clause for clause in clauses if clause]


def _clause_has_verb(text: str) -> bool:
    return bool(
        _MOVE_CUE_RE.search(text)
        or _INSPECT_CUE_RE.search(text)
        or _ASK_CUE_RE.search(text)
        or _OTHER_CUE_RE.search(text)
        or _WATCH_RE.search(text)
        or _SOCIAL_EXIT_RE.search(text)
        or _BACK_RE.search(text)
    )


def _prior_exit_rows(session: Mapping[str, Any] | None, scene: Mapping[str, Any] | None, exits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visited = session.get("visited_scene_ids") if isinstance(session, Mapping) else None
    if not isinstance(visited, list):
        return []
    current = _scene_id(scene)
    prior = {_clean_text(item) for item in visited if _clean_text(item) and _clean_text(item) != current}
    return [row for row in exits if _clean_text(row.get("target_scene_id")) in prior]


def _focused_exit_row(session: Mapping[str, Any] | None, scene: Mapping[str, Any] | None, exits: list[dict[str, Any]]) -> dict[str, Any] | None:
    focused = _conversation_context(session).get("focused_destination")
    if not isinstance(focused, Mapping):
        return None
    focused_scene = _clean_text(focused.get("scene_id"))
    if focused_scene and _scene_id(scene) and focused_scene != _scene_id(scene):
        return None
    exit_id = _clean_text(focused.get("exit_id"))
    for row in exits:
        if _clean_text(row.get("id")) == exit_id:
            return row
    return None


def _should_clear_interlocutor(session: Mapping[str, Any] | None, incidental: list[str], operation: str) -> bool:
    if any(_SOCIAL_EXIT_RE.search(item or "") for item in incidental):
        return True
    ctx = _interaction_context(session)
    kind = _clean_text(ctx.get("active_interaction_kind")).casefold()
    active = _clean_text(ctx.get("active_interaction_target_id"))
    return operation == "MOVE" and kind == "social" and bool(active)


def _focused_payload(row: Mapping[str, Any], scene: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "exit_id": _clean_text(row.get("id")),
        "label": _label(row, _clean_text(row.get("id"))),
        "scene_id": _scene_id(scene),
    }


def _choice_rows(choices: list[Any], exits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for choice in choices:
        if not isinstance(choice, Mapping):
            continue
        exit_id = _clean_text(choice.get("entity_id") or choice.get("exit_id"))
        for row in exits:
            if _clean_text(row.get("id")) == exit_id:
                rows.append(row)
                break
    return rows


def _ground_catalog_target(phrase: str, catalog: Mapping[str, Any], kinds: set[str]) -> list[tuple[str, Mapping[str, Any]]]:
    hits: list[tuple[str, Mapping[str, Any]]] = []
    for entity_id, info in catalog.items():
        if not isinstance(info, Mapping) or str(info.get("kind") or "") not in kinds:
            continue
        names = _aliases(info.get("row") if isinstance(info.get("row"), Mapping) else None, entity_id)
        if any(_place_match(phrase, name) for name in names):
            hits.append((entity_id, info))
    return hits


def _analyze_clause(clause: str, exits: list[dict[str, Any]]) -> dict[str, Any]:
    text = _clean_text(clause)
    destination = _destination_phrase(text)
    if _ASK_CUE_RE.search(text) and _MOVE_CUE_RE.search(text):
        # Travel vocabulary can be the content of speech. The deterministic
        # shortcut cannot settle that scope; leave it to semantic interpretation.
        return {"text": text, "operation": "", "destination": "", "consequential": False, "incidental": False, "back": False}
    incidental = False
    operation = ""
    consequential = False
    if _WATCH_RE.search(text) and not destination:
        operation = "OTHER"
        consequential = True
    elif _INSPECT_CUE_RE.search(text):
        operation = "INSPECT"
        consequential = True
    elif _OTHER_CUE_RE.search(text):
        operation = "OTHER"
        consequential = True
    elif _ASK_CUE_RE.search(text) and not _MOVE_CUE_RE.search(text):
        operation = "ASK"
        consequential = True
    elif _MOVE_CUE_RE.search(text) or _BACK_RE.search(text) or _INCOMPLETE_GOAL_RE.search(text):
        operation = "MOVE"
        consequential = True
        if re.search(r"\bleave\b", text, re.IGNORECASE) and not destination and not _BACK_RE.search(text):
            obj = _leave_object(text)
            if obj and not _matching_exits(obj, exits):
                consequential = False
                incidental = True
                operation = ""
    if not consequential and _SOCIAL_EXIT_RE.search(text):
        incidental = True
    return {
        "text": text,
        "operation": operation,
        "destination": destination,
        "consequential": consequential,
        "incidental": incidental,
        "back": bool(_BACK_RE.search(text) or _DEICTIC_DEST_RE.match(_norm_place(destination))),
    }


def _secondary_from_clause(clause: Mapping[str, Any], *, status: str) -> dict[str, Any]:
    return {
        "text": clause.get("text") or "",
        "operation": clause.get("operation") or "",
        "consequential": bool(clause.get("consequential")),
        "dependency": "sequence",
        "status": status,
    }


def _move_decision_for_row(
    row: Mapping[str, Any],
    *,
    player_text: str,
    summary: str,
    incidental: list[str],
    session: Mapping[str, Any] | None,
    secondary: list[dict[str, Any]] | None = None,
    pending: Mapping[str, Any] | None = None,
) -> ConversationalDecision:
    exit_id = _clean_text(row.get("id"))
    label = _label(row, exit_id)
    record = _operation_record(
        operation="MOVE",
        target_id=exit_id,
        player_text=player_text,
        summary=summary or f"Go to {label}.",
        references={"resolved_references": [{"text": label, "entity_id": exit_id}], "unresolved_references": []},
    )
    clear = _should_clear_interlocutor(session, incidental, "MOVE")
    return ConversationalDecision(
        category=ConversationalDecisionCategory.EXECUTE,
        primary_intention=summary or f"Go to {label}.",
        intent_family="movement",
        incidental_context=list(incidental),
        proposed_operation="MOVE",
        proposed_target=exit_id,
        proposed_record=record,
        requires_authoritative_execution=True,
        reason="grounded_movement_destination",
        confidence=0.86,
        context_update=_context_update(
            pending=pending,
            pending_set=True,
            focused=None,
            focused_set=True,
            clear_interlocutor=clear,
        ),
        intent_modality="committed",
        secondary_intentions=list(secondary or []),
        execution_policy="execute_primary",
    )


def _operation_execute_decision(
    *,
    operation: str,
    target_id: str,
    label: str,
    player_text: str,
    incidental: list[str],
    session: Mapping[str, Any] | None,
    secondary: list[dict[str, Any]] | None = None,
    pending: Mapping[str, Any] | None = None,
) -> ConversationalDecision:
    record = _operation_record(
        operation=operation,
        target_id=target_id,
        player_text=player_text,
        summary=f"{operation.title()} {label}.",
        references={"resolved_references": [{"text": label, "entity_id": target_id}], "unresolved_references": []},
    )
    decision = decision_from_interpretation_record(record, player_text=player_text)
    clear = _should_clear_interlocutor(session, incidental, operation)
    return ConversationalDecision(
        **{
            **decision.__dict__,
            "incidental_context": list(incidental),
            "context_update": _context_update(
                pending=pending,
                pending_set=True,
                focused=None,
                focused_set=True,
                clear_interlocutor=clear,
            ),
            "intent_modality": "committed",
            "secondary_intentions": list(secondary or []),
            "execution_policy": "execute_primary",
        }
    )


def _clarify_destination(player_text: str, *, exits: list[dict[str, Any]], scene: Mapping[str, Any] | None, clear: bool) -> ConversationalDecision:
    choices = [{"entity_id": _clean_text(row.get("id")), "label": _label(row, _clean_text(row.get("id")))} for row in exits[:4]]
    pending = {
        "kind": "missing_destination",
        "operation": "MOVE",
        "original_text": player_text,
        "choices": choices,
        "scene_id": _scene_id(scene),
    }
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention="Move or leave the current situation.",
        intent_family="movement",
        missing_information=["destination"],
        reason="movement_destination_missing",
        confidence=0.9,
        player_facing_text="Where are you trying to go?",
        context_update=_context_update(pending=pending, pending_set=True, clear_interlocutor=clear),
        intent_modality="incomplete",
        execution_policy="clarify_before_execution",
    )


def _ambiguous_destination(
    player_text: str,
    matches: list[dict[str, Any]],
    *,
    scene: Mapping[str, Any] | None,
    clear: bool,
) -> ConversationalDecision:
    chosen = matches[:4]
    labels = [_label(row, _clean_text(row.get("id"))) for row in chosen]
    pending = {
        "kind": "ambiguous_destination",
        "operation": "MOVE",
        "original_text": player_text,
        "choices": [{"entity_id": _clean_text(row.get("id")), "label": label} for row, label in zip(chosen, labels)],
        "scene_id": _scene_id(scene),
    }
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=player_text,
        intent_family="movement",
        missing_information=["destination"],
        reason="ambiguous_movement_destination",
        confidence=0.84,
        ambiguity="More than one established destination could match.",
        player_facing_text="Do you mean " + " or ".join(labels) + "?",
        context_update=_context_update(pending=pending, pending_set=True, clear_interlocutor=clear),
        intent_modality="committed",
        execution_policy="clarify_before_execution",
    )


def _unknown_destination(player_text: str, phrase: str, *, clear: bool) -> ConversationalDecision:
    shown = _clean_text(phrase) or "that place"
    return ConversationalDecision(
        category=ConversationalDecisionCategory.DECLINE,
        primary_intention=player_text,
        intent_family="movement",
        reason="destination_not_established",
        confidence=0.82,
        player_facing_text=(
            f"You want to reach {shown}, but that is not an established destination from here. "
            "You stay where you are."
        ),
        intent_modality="committed",
        execution_policy="decline_unauthorized_route",
        context_update=_context_update(clear_interlocutor=clear) if clear else None,
    )


def _resolve_move_target(
    *,
    player_text: str,
    destination: str,
    back: bool,
    exits: list[dict[str, Any]],
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
    incidental: list[str],
    summary: str,
) -> ConversationalDecision | None:
    clear = _should_clear_interlocutor(session, incidental, "MOVE")
    if destination:
        matches = _matching_exits(destination, exits)
        if len(matches) == 1:
            label = _label(matches[0], _clean_text(matches[0].get("id")))
            return _move_decision_for_row(
                matches[0],
                player_text=player_text,
                summary=summary or f"Go to {label}.",
                incidental=incidental,
                session=session,
            )
        if len(matches) > 1:
            return _ambiguous_destination(player_text, matches, scene=scene, clear=clear)
        return _unknown_destination(player_text, destination, clear=clear)
    if back:
        prior = _prior_exit_rows(session, scene, exits)
        if len(prior) == 1:
            label = _label(prior[0], _clean_text(prior[0].get("id")))
            return _move_decision_for_row(
                prior[0],
                player_text=player_text,
                summary=summary or f"Return to {label}.",
                incidental=incidental,
                session=session,
            )
        if len(prior) > 1:
            return _ambiguous_destination(player_text, prior, scene=scene, clear=clear)
    focused = _focused_exit_row(session, scene, exits)
    if focused is not None:
        label = _label(focused, _clean_text(focused.get("id")))
        return _move_decision_for_row(
            focused,
            player_text=player_text,
            summary=summary or f"Go to {label}.",
            incidental=incidental,
            session=session,
        )
    return _clarify_destination(player_text, exits=exits, scene=scene, clear=clear)


def _movement_question_decision(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    exits: list[dict[str, Any]],
) -> ConversationalDecision:
    phrase = _question_destination(text) or _object_phrase(text)
    matches = _matching_exits(phrase, exits) if phrase else []
    focused = None
    if len(matches) == 1:
        label = _label(matches[0], _clean_text(matches[0].get("id")))
        message = f"From here, {label} is an established way you could take. You have not moved."
        focused = _focused_payload(matches[0], scene)
    elif len(matches) > 1:
        labels = [_label(row, _clean_text(row.get("id"))) for row in matches[:4]]
        message = "More than one established way could match. Do you mean " + " or ".join(labels) + "? You have not moved."
    else:
        shown = phrase or "that place"
        message = f"I don't have an established route to {shown} from here. You have not moved."
    return ConversationalDecision(
        category=ConversationalDecisionCategory.ANSWER,
        primary_intention="Ask whether a destination can be reached.",
        intent_family="movement_question",
        reason="movement_question",
        confidence=0.86,
        player_facing_text=message,
        requires_authoritative_execution=False,
        intent_modality="informational",
        execution_policy="answer_only",
        context_update=_context_update(focused=focused, focused_set=focused is not None),
    )


def _nonaction_decision(text: str, *, modality: str, reason: str, message: str) -> ConversationalDecision:
    category = ConversationalDecisionCategory.PLAN if modality == "planning" else ConversationalDecisionCategory.ANSWER
    if modality == "hypothetical":
        category = ConversationalDecisionCategory.ANSWER
    return ConversationalDecision(
        category=category,
        primary_intention=text,
        intent_family=modality,
        reason=reason,
        confidence=0.8,
        player_facing_text=message,
        requires_authoritative_execution=False,
        intent_modality=modality,
        execution_policy="answer_only" if modality != "planning" else "defer_uncommitted",
    )


def _uncommitted_intent_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    del world, session
    text = _clean_text(player_text)
    exits = _exit_rows(scene)
    if _HYPOTHETICAL_RE.search(text):
        return _nonaction_decision(
            text,
            modality="hypothetical",
            reason="hypothetical_action",
            message="I can't say what would happen for certain, and nothing has been attempted.",
        )
    if _STAY_RE.search(text) and not re.search(r"\bbut\s+i\s+(?:go|head|walk|leave|travel)\b", text, re.IGNORECASE):
        return _nonaction_decision(
            text,
            modality="planning",
            reason="explicit_stay",
            message="You stay where you are. Nothing has been attempted.",
        )
    if re.match(r"^\s*i\s+(?:remember|recall)\b", text, re.IGNORECASE) and not _MOVE_CUE_RE.search(text):
        return _nonaction_decision(
            text,
            modality="planning",
            reason="recalled_context_not_action",
            message="You stay where you are. Nothing has been attempted.",
        )
    if _TENTATIVE_RE.search(text) and not re.search(r"\bbut\s+i\s+(?:go|head|walk|leave|travel)\b", text, re.IGNORECASE):
        phrase = _destination_phrase(text)
        if not phrase:
            visiting = _VISITING_RE.search(text)
            phrase = visiting.group(1).strip(" .?!") if visiting else ""
        if phrase:
            message = f"You're considering {phrase}. Nothing has been attempted yet. Say when you want to go there."
        else:
            message = "You're considering that. Nothing has been attempted yet. Say when you want to do it."
        return _nonaction_decision(text, modality="tentative", reason="tentative_intention", message=message)
    questionish = bool("?" in text or _QUESTION_START_RE.search(text))
    if questionish and (_INFO_MOVE_RE.search(text) or (_MOVE_CUE_RE.search(text) and _destination_phrase(text))):
        return _movement_question_decision(text, scene=scene, exits=exits)
    if questionish and _CAPABILITY_RE.search(text):
        return _nonaction_decision(
            text,
            modality="capability_question",
            reason="capability_question",
            message="I have not tried that, and I can't say whether it would work from here.",
        )
    if _PLANNING_RE.search(text) and not (_MOVE_CUE_RE.search(text) and _destination_phrase(text) and _AGENT_RE.search(text)):
        return _nonaction_decision(
            text,
            modality="planning",
            reason="planning_statement",
            message="We can hold that plan. Nothing has been attempted yet.",
        )
    from game.live_chat_interpretation import production_live_interpretation_enabled
    if not production_live_interpretation_enabled() and not _AGENT_RE.search(text) and _STATIVE_RE.search(text) and _mentioned_exits(text, exits):
        return _nonaction_decision(
            text,
            modality="informational",
            reason="descriptive_place_statement",
            message="You stay where you are. Nothing has been attempted.",
        )
    return None


def _spoken_step(text: Any) -> str:
    spoken = re.sub(r"^(?:i|we)\s+", "", _clean_text(text), flags=re.IGNORECASE)
    return spoken or "that action"


def _compound_clarification(
    player_text: str,
    steps: list[dict[str, Any]],
    *,
    scene: Mapping[str, Any] | None,
    clear: bool,
    incidental: list[str],
    world: Mapping[str, Any] | None = None,
) -> ConversationalDecision:
    if scene is not None:
        from game.player_interpretation_bridge import normalized_action_from_interpretation
        from game.storage import list_scene_ids
        for step in steps:
            if step.get("supported"):
                proposal = _operation_record(operation=step["operation"], target_id=step["target_id"], player_text=step["text"])
                _, meta = normalized_action_from_interpretation(
                    proposal, scene=dict(scene), world=dict(world or {}),
                    player_text=player_text, known_scene_ids=list_scene_ids,
                )
                step["supported"] = meta.get("accepted") is True
    # Unsupported intentions are retained for explanation, never offered for approval.
    if not steps or not steps[0].get("supported"):
        named = ", then ".join(_spoken_step(step.get("text")) for step in steps)
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY if len(steps) > 1 else ConversationalDecisionCategory.DECLINE,
            primary_intention=player_text, intent_family="unsupported_world_operation",
            reason="proposal_not_eligible", secondary_intentions=steps,
            player_facing_text=f"I cannot carry out {named or 'that attempt'} with the available actions and targets. I have not done any of them yet.",
            context_update=_context_update_clear_pending(),
        )
    pending = {
        "kind": "compound_sequence",
        "operation": _clean_text(steps[0].get("operation")) if steps else "",
        "original_text": player_text,
        "steps": steps,
        "scene_id": _scene_id(scene),
    }
    supported = [step for step in steps if step.get("supported")]
    unsupported = [step for step in steps if not step.get("supported")]
    if unsupported:
        message = (
            f"You can {_spoken_step(supported[0].get('text'))} first. I have not done this yet: "
            + ", ".join(_spoken_step(step.get("text")) for step in unsupported)
            + ". Those later steps cannot be resolved as stated. Should I do the first one now?"
        )
    else:
        named = ", then ".join(_spoken_step(step.get("text")) for step in steps)
        message = (
            f"You asked to {named}. I can resolve one supported action at a time, "
            "and I have not done any of them yet. Should I start with the first one?"
        )
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=str(steps[0].get("text") or player_text) if steps else player_text,
        intent_family="multi_action",
        incidental_context=list(incidental),
        missing_information=["confirmed_step"],
        reason="compound_intention_needs_confirmation",
        confidence=0.8,
        player_facing_text=message,
        context_update=_context_update(pending=pending, pending_set=True, clear_interlocutor=clear),
        intent_modality="committed",
        secondary_intentions=steps[1:],
        execution_policy="clarify_before_execution",
    )


def _step_from_clause(
    clause: Mapping[str, Any],
    *,
    exits: list[dict[str, Any]],
    catalog: Mapping[str, Any],
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> dict[str, Any]:
    operation = str(clause.get("operation") or "")
    text = str(clause.get("text") or "")
    step = _secondary_from_clause(clause, status="pending")
    step["supported"] = False
    step["target_id"] = ""
    step["label"] = text
    if operation == "MOVE":
        destination = str(clause.get("destination") or "")
        if destination:
            matches = _matching_exits(destination, exits)
        elif clause.get("back"):
            matches = _prior_exit_rows(session, scene, exits)
        else:
            focused = _focused_exit_row(session, scene, exits)
            matches = [focused] if focused is not None else []
        if len(matches) == 1:
            step["supported"] = True
            step["target_id"] = _clean_text(matches[0].get("id"))
            step["label"] = _label(matches[0], step["target_id"])
    elif operation in {"INSPECT", "ASK"}:
        kinds = {"inspect_target", "perceive_target"} if operation == "INSPECT" else {"npc"}
        phrase = _object_phrase(text) or text
        matches = _ground_catalog_target(phrase, catalog, kinds)
        if len(matches) == 1:
            step["supported"] = True
            step["target_id"] = matches[0][0]
            step["label"] = _label(matches[0][1].get("row") if isinstance(matches[0][1], Mapping) else None, matches[0][0])
    return step


def _committed_movement_or_compound_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    text = _clean_text(player_text)
    if not _AGENT_RE.search(text):
        return None
    if "?" in text or _QUESTION_START_RE.search(text):
        return None
    exits = _exit_rows(scene)
    clauses = [_analyze_clause(clause, exits) for clause in _split_clauses(text)]
    consequential = [clause for clause in clauses if clause.get("consequential")]
    incidental = [str(clause.get("text") or "") for clause in clauses if clause.get("incidental")]
    oriented: list[str] = []
    kept: list[dict[str, Any]] = []
    for clause in consequential:
        clause_text = str(clause.get("text") or "")
        if (
            clause.get("operation") == "MOVE"
            and not clause.get("destination")
            and re.search(r"\bturn\s+around\b", clause_text, re.IGNORECASE)
            and not _MOVE_CUE_RE.search(clause_text)
        ):
            oriented.append(clause_text)
        else:
            kept.append(clause)
    incidental.extend(oriented)
    consequential = kept
    if not consequential and oriented:
        return _resolve_move_target(
            player_text=text,
            destination="",
            back=True,
            exits=exits,
            scene=scene,
            session=session,
            incidental=incidental,
            summary="",
        )
    if not consequential:
        if any(_SOCIAL_EXIT_RE.search(item) for item in incidental):
            return None
        return None
    catalog = _catalog(scene, world)
    if len(consequential) > 1:
        steps = [
            _step_from_clause(clause, exits=exits, catalog=catalog, scene=scene, session=session)
            for clause in consequential
        ]
        clear = _should_clear_interlocutor(session, incidental, str(consequential[0].get("operation") or ""))
        return _compound_clarification(text, steps, scene=scene, clear=clear, incidental=incidental, world=world)
    clause = consequential[0]
    if clause.get("operation") != "MOVE":
        if not incidental:
            return None
        step = _step_from_clause(clause, exits=exits, catalog=catalog, scene=scene, session=session)
        clear = _should_clear_interlocutor(session, incidental, str(clause.get("operation") or ""))
        if step.get("supported") and step.get("operation") in {"INSPECT", "ASK", "MOVE"}:
            if step["operation"] == "MOVE":
                row = next((item for item in exits if _clean_text(item.get("id")) == step.get("target_id")), None)
                if row is not None:
                    return _move_decision_for_row(
                        row,
                        player_text=text,
                        summary=f"Go to {step.get('label')}.",
                        incidental=incidental,
                        session=session,
                    )
            return _operation_execute_decision(
                operation=str(step["operation"]),
                target_id=str(step["target_id"]),
                label=str(step.get("label") or step["target_id"]),
                player_text=text,
                incidental=incidental,
                session=session,
            )
        return _compound_clarification(text, [step], scene=scene, clear=clear, incidental=incidental, world=world)
    destination = str(clause.get("destination") or "")
    grounded_summary = ""
    if destination:
        grounded_matches = _matching_exits(destination, exits)
        if len(grounded_matches) == 1:
            grounded_summary = f"Go to {_label(grounded_matches[0], _clean_text(grounded_matches[0].get('id')))}."
    elif clause.get("back"):
        prior = _prior_exit_rows(session, scene, exits)
        if len(prior) == 1:
            grounded_summary = f"Return to {_label(prior[0], _clean_text(prior[0].get('id')))}."
    return _resolve_move_target(
        player_text=text,
        destination=destination,
        back=bool(clause.get("back")),
        exits=exits,
        scene=scene,
        session=session,
        incidental=incidental,
        summary=grounded_summary,
    )


def grounded_move_processing_text(player_text: str, summary: str) -> str:
    """Use a grounded move sentence when the reply itself does not name the trip."""
    text = _clean_text(player_text)
    restored = _clean_text(summary)
    if not restored:
        return text
    if (_MOVE_CUE_RE.search(text) or _BACK_RE.search(text)) and _destination_phrase(text):
        return text
    return restored


def _select_compound_step(player_text: str, steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    if _YES_RE.match(player_text):
        return steps[0] if steps else None
    for step in steps:
        label = _clean_text(step.get("label") or step.get("text"))
        if step.get("supported") and label and _place_match(player_text, label):
            return step
    return None


def _resume_bounded_pending(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
    pending: Mapping[str, Any],
) -> ConversationalDecision | None:
    if _QUESTION_START_RE.search(player_text):
        return None
    kind = _clean_text(pending.get("kind"))
    exits = _exit_rows(scene)
    if kind == "compound_sequence":
        steps = [dict(step) for step in pending.get("steps") or [] if isinstance(step, Mapping)]
        selected = _select_compound_step(player_text, steps)
        if selected is None:
            return None
        if not selected.get("supported"):
            return ConversationalDecision(
                category=ConversationalDecisionCategory.DECLINE,
                primary_intention=str(selected.get("text") or player_text),
                intent_family="multi_action",
                reason="unsupported_compound_step",
                confidence=0.75,
                player_facing_text=(
                    f"I have not done this: {selected.get('text') or 'that step'}. "
                    "It is not a supported action I can resolve safely yet."
                ),
                intent_modality="committed",
                execution_policy="decline_unauthorized_route",
                context_update=_context_update_clear_pending(),
            )
        remaining = [step for step in steps if step is not selected]
        remainder = None
        if remaining:
            remainder = {
                "kind": "compound_sequence" if remaining[0].get("supported") else "deferred_intentions",
                "operation": _clean_text(remaining[0].get("operation")),
                "original_text": _clean_text(pending.get("original_text")) or player_text,
                "steps": remaining,
                "scene_id": _clean_text(pending.get("scene_id")) or _scene_id(scene),
            }
        operation = _clean_text(selected.get("operation")).upper()
        target_id = _clean_text(selected.get("target_id"))
        label = _clean_text(selected.get("label")) or target_id
        if operation == "MOVE":
            row = next((item for item in exits if _clean_text(item.get("id")) == target_id), None)
            if row is None:
                return None
            decision = _move_decision_for_row(
                row,
                player_text=_clean_text(pending.get("original_text")) or player_text,
                summary=f"Go to {label}.",
                incidental=[],
                session=session,
                secondary=remaining,
                pending=remainder,
            )
            return decision
        if operation in {"INSPECT", "ASK", "PERCEIVE"} and target_id:
            return _operation_execute_decision(
                operation=operation,
                target_id=target_id,
                label=label,
                player_text=_clean_text(pending.get("original_text")) or player_text,
                incidental=[],
                session=session,
                secondary=remaining,
                pending=remainder,
            )
        return None
    choices = _choice_rows(list(pending.get("choices") or []), exits)
    pool = choices or exits
    if kind == "ambiguous_destination":
        pool = choices
    matches = _matching_exits(player_text, pool)
    if len(matches) == 1:
        return _move_decision_for_row(
            matches[0],
            player_text=_clean_text(pending.get("original_text")) or player_text,
            summary=f"Go to {_label(matches[0], _clean_text(matches[0].get('id')))}.",
            incidental=[],
            session=session,
        )
    if len(matches) > 1:
        return _ambiguous_destination(player_text, matches, scene=scene, clear=False)
    if _YES_RE.match(player_text):
        return _clarify_destination(player_text, exits=exits, scene=scene, clear=False)
    return None


def _compound_from_record_parts(
    player_text: str,
    summary: str,
    connected: list[Mapping[str, Any]],
    unsupported: list[str],
    incidental: list[str],
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    ordered_components: list[Mapping[str, Any]] | None = None,
) -> ConversationalDecision:
    steps: list[dict[str, Any]] = []
    for component in ordered_components if ordered_components is not None else connected:
        operation = _clean_text(component.get("operation_class")).upper()
        if operation in _INCIDENTAL_OPERATIONS:
            continue
        description = _clean_text(component.get("description")) or _clean_text(component.get("operation_class"))
        steps.append(
            {
                "text": description,
                "label": description,
                "operation": _clean_text(component.get("operation_class")).upper(),
                "target_id": _clean_text(component.get("target_ref")),
                "supported": operation in _CONNECTED_OPERATIONS and bool(_clean_text(component.get("target_ref"))),
                "consequential": True,
                "dependency": "sequence",
                "status": "pending",
            }
        )
    for description in unsupported if ordered_components is None else []:
        steps.append(
            {
                "text": description,
                "label": description,
                "operation": "OTHER",
                "target_id": "",
                "supported": False,
                "consequential": True,
                "dependency": "sequence",
                "status": "pending",
            }
        )
    return _compound_clarification(summary or player_text, steps, scene=scene, world=world, clear=False, incidental=incidental)


def deterministic_conversational_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    log: list | None = None,
) -> ConversationalDecision | None:
    """Return a no-provider decision for obvious non-mutating cases."""
    from game.live_chat_interpretation import production_live_interpretation_enabled
    text = _clean_text(player_text)
    if text:
        from game.unified_semantic_planning import planning_decision

        planned = planning_decision(
            player_text=text, scene=scene, world=world, session=session, log=log,
        )
        if planned is not None:
            return planned
    if not text:
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention="Provide a playable turn.",
            intent_family="clarification",
            missing_information=["player_intention"],
            reason="empty_player_text",
            confidence=1.0,
            player_facing_text="What are you trying to accomplish?",
        )
    grounded = decision_from_delivered_exchange(
        text, session=session, scene=scene, world=world,
    )
    if grounded is not None:
        return grounded
    if re.search(r"\?\s*(?:if|provided|unless|otherwise)\b.*?\b(?:I|we)(?:['’]ll|\s+will)?\s+\w+", text, re.I):
        # A question followed by a conditional declaration is not a standalone
        # capability question. Keep the complete condition/action without
        # authorizing an operation or requiring a provider to confirm it.
        return _communication_decision({
            "communication": {"recipient": "MIXED", "purpose": "QUESTION"},
            "action_components": [{"description": text, "operation_class": "UNRESOLVED_CONDITIONAL"}],
        }, text)
    gm_continuation = _gm_continuation_decision(text, session, log)
    if gm_continuation is not None:
        return gm_continuation
    resumed = _resume_pending_clarification(player_text=text, scene=scene, session=session)
    if resumed is not None:
        return resumed
    uncommitted = _uncommitted_intent_decision(
        player_text=text,
        scene=scene,
        world=world,
        session=session,
    )
    if uncommitted is not None:
        return uncommitted
    followup = _active_dialogue_followup_decision(
        player_text=text,
        scene=scene,
        world=world,
        session=session,
    )
    if followup is not None:
        return followup
    contextual_reference = _pending_clarification_decision(player_text=text, scene=scene, world=world)
    if contextual_reference is not None:
        return contextual_reference
    if _YES_RE.match(text) and not isinstance(_conversation_context(session).get("pending_clarification"), Mapping):
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=text,
            intent_family="clarification",
            reason="confirmation_without_proposal",
            player_facing_text="That does not confirm a proposed action. Nothing has been attempted.",
            communication_owner="GM",
            communication_purpose="CONFIRMATION",
        )
    if _IMPOSSIBLE_RE.search(text):
        return ConversationalDecision(
            category=ConversationalDecisionCategory.DECLINE,
            primary_intention=text,
            intent_family="unsupported_world_operation",
            reason="deterministic_impossible_request",
            confidence=0.8,
            player_facing_text="I cannot carry that out under the current scene and rules.",
        )
    committed = _committed_movement_or_compound_decision(
        player_text=text,
        scene=scene,
        world=world,
        session=session,
    )
    if committed is not None:
        return committed
    if (
        _QUESTION_START_RE.search(text)
        and _OOC_HELP_RE.search(text)
        and "sleight of hand" not in text.casefold()
        and not _EMBEDDED_ACTION_CONDITION_RE.search(text)
        and not production_live_interpretation_enabled()
    ):
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER,
            primary_intention="Ask an out-of-character rules or interface question.",
            intent_family="ooc_help",
            context_references=["mode:auto", "deterministic_ooc_help"],
            reason="unmarked_ooc_help_question",
            confidence=0.82,
            player_facing_text=(
                "Out of character: ask rules, interface, or table-procedure questions normally. "
                "I will answer without advancing game time unless you mark it as an in-character action."
            ),
        )
    recent = _recent_visible_answer(text, log)
    if _QUESTION_START_RE.search(text) and recent is not None:
        answer, source = recent
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER,
            primary_intention="Ask about previously established context.",
            intent_family="context_question",
            context_references=[source],
            reason="recent_visible_context_answer",
            confidence=0.72,
            player_facing_text=answer,
        )
    if _QUESTION_START_RE.search(text) and any(term in text.casefold() for term in ("where are we", "what can i see", "what is here")):
        answer = _visible_scene_summary(scene)
        if answer:
            return ConversationalDecision(
                category=ConversationalDecisionCategory.ANSWER,
                primary_intention="Ask about visible established scene context.",
                intent_family="context_question",
                context_references=["active_scene_public_summary"],
                reason="visible_scene_context_answer",
                confidence=0.86,
                player_facing_text=answer,
            )
    if _PLAN_RE.search(text) and _QUESTION_START_RE.search(text):
        return ConversationalDecision(
            category=ConversationalDecisionCategory.PLAN,
            primary_intention="Ask for planning help without committing a world operation.",
            intent_family="planning",
            reason="planning_question",
            confidence=0.7,
            player_facing_text=(
                "We can plan before committing to an action. Tell me the goal you want to prioritize, "
                "and I will help narrow it to a concrete next step."
            ),
        )
    return None


def decision_from_interpretation_record(
    record: Mapping[str, Any] | None,
    *,
    bridge_meta: Mapping[str, Any] | None = None,
    player_text: str = "",
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
) -> ConversationalDecision:
    """Build a decision envelope from an existing interpretation/bridge result."""
    text = _clean_text(player_text)
    grounded = decision_from_delivered_exchange(
        text, session=session, scene=scene, world=world,
    )
    if grounded is not None:
        return grounded
    if isinstance(record, Mapping):
        record = _reclassify_direct_npc_address(record, text, scene=scene, world=world, session=session)
    if not isinstance(record, Mapping):
        reason = _clean_text((bridge_meta or {}).get("reason") if isinstance(bridge_meta, Mapping) else "") or "missing_record"
        message, missing = _focused_bridge_clarification(reason)
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=text or "Unclear player intention.",
            intent_family="clarification",
            missing_information=missing,
            reason=reason,
            confidence=0.4,
            player_facing_text=message,
        )
    communication_decision = _communication_decision(record, text, session=session, scene=scene, world=world)
    if communication_decision is not None:
        return communication_decision
    mode = _clean_text(record.get("communication_mode"))
    status = _clean_text(record.get("interpretation_status"))
    summary = _clean_text((record.get("player_intent") or {}).get("summary") if isinstance(record.get("player_intent"), Mapping) else "")
    components = record.get("action_components") if isinstance(record.get("action_components"), list) else []
    if mode == "RULES_QUESTION":
        return _communication_decision({"communication": {"recipient": "SESSION", "purpose": "RULES"}}, text)
    if mode in {"OUT_OF_CHARACTER", "OUT_OF_CHARACTER_CORRECTION"}:
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER,
            primary_intention=summary or text or "Out-of-character communication.",
            intent_family="ooc_help",
            reason="interpretation_out_of_character",
            confidence=0.8,
            player_facing_text=(
                "Understood. I will treat that as out of character. No gameplay action is executed, "
                "no game time advances, and committed state is unchanged."
            ),
        )
    if status == "UNSUPPORTED_REQUEST":
        return ConversationalDecision(
            category=ConversationalDecisionCategory.DECLINE, primary_intention=summary or text,
            intent_family="unsupported_world_operation", reason="unsupported_request",
            player_facing_text=f"I cannot carry out {summary or text or 'that request'} with the available actions. No action has been attempted.",
            context_update=_context_update_clear_pending(),
        )
    if status and status != "INTERPRETED":
        question = _clean_text(record.get("clarification_question"))
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=summary or text or "Complete the intended action.",
            intent_family="clarification",
            missing_information=["interpretable_action"],
            reason="interpretation_not_interpreted",
            confidence=0.5,
            player_facing_text=question or "What are you trying to accomplish?",
        )
    connected: list[Mapping[str, Any]] = []
    incidental: list[str] = list(record.get("incidental_context") or [])
    unsupported: list[str] = []
    for component in components:
        if not isinstance(component, Mapping):
            continue
        op = _clean_text(component.get("operation_class")).upper()
        desc = _clean_text(component.get("description"))
        if op in _CONNECTED_OPERATIONS:
            connected.append(component)
        elif op in _INCIDENTAL_OPERATIONS:
            incidental.append(desc or op)
        else:
            unsupported.append(desc or op or "unsupported component")
    if len(connected) == 1 and not unsupported:
        primary = dict(connected[0])
        proposed = dict(record)
        proposed["action_components"] = [primary]
        return ConversationalDecision(
            category=ConversationalDecisionCategory.EXECUTE,
            primary_intention=_clean_text(primary.get("description")) or summary or text,
            intent_family="world_operation",
            incidental_context=incidental,
            proposed_operation=_clean_text(primary.get("operation_class")).upper(),
            proposed_target=_clean_text(primary.get("target_ref")) or None,
            proposed_record=proposed,
            requires_authoritative_execution=True,
            reason="single_authoritative_component",
            confidence=0.78 if incidental else 0.9,
        )
    if len(connected) + len(unsupported) > 1:
        return _compound_from_record_parts(text, summary, connected, unsupported, incidental, scene=scene, world=world,
                                           ordered_components=[c for c in components if isinstance(c, Mapping)])
    if unsupported:
        return ConversationalDecision(
            category=ConversationalDecisionCategory.DECLINE, primary_intention=summary or text,
            intent_family="unsupported_world_operation", reason="unsupported_single_intention",
            proposed_operation=_clean_text(components[0].get("operation_class")) if components else None,
            player_facing_text=f"I cannot carry out {unsupported[0]} with the available actions. No action has been attempted.",
            context_update=_context_update_clear_pending(),
        )
    reason = _clean_text((bridge_meta or {}).get("reason") if isinstance(bridge_meta, Mapping) else "") or "no_executable_component"
    operation = _clean_text((bridge_meta or {}).get("operation") if isinstance(bridge_meta, Mapping) else "")
    message, missing = _focused_bridge_clarification(reason, operation=operation)
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=summary or text or "Complete the intended action.",
        intent_family="clarification",
        incidental_context=incidental,
        missing_information=missing,
        reason=reason,
        confidence=0.55,
        player_facing_text=message,
    )


def decision_from_bridge_rejection(
    *,
    bridge_meta: Mapping[str, Any] | None,
    player_text: str,
    record: Mapping[str, Any] | None = None,
) -> ConversationalDecision:
    operation = _clean_text((bridge_meta or {}).get("operation") if isinstance(bridge_meta, Mapping) else "")
    reason = _clean_text((bridge_meta or {}).get("reason") if isinstance(bridge_meta, Mapping) else "") or "bridge_rejected"
    supplied = _clean_text((bridge_meta or {}).get("clarification") if isinstance(bridge_meta, Mapping) else "")
    message, missing = (supplied, ["interlocutor"]) if supplied else _focused_bridge_clarification(reason, operation=operation)
    pending = (bridge_meta or {}).get("pending_intention") if isinstance(bridge_meta, Mapping) else None
    context_update = _context_update(pending=pending, pending_set=True, intention=pending, intention_set=True) if isinstance(pending, Mapping) else None
    if reason in {"unsupported_operation", "operation_incompatible_with_entity_kind"}:
        category = ConversationalDecisionCategory.DECLINE if reason == "unsupported_operation" else ConversationalDecisionCategory.CLARIFY
    else:
        category = ConversationalDecisionCategory.CLARIFY
    return ConversationalDecision(
        category=category,
        primary_intention=_clean_text(player_text),
        intent_family="world_operation",
        proposed_operation=operation or None,
        proposed_target=_clean_text((bridge_meta or {}).get("target_ref") if isinstance(bridge_meta, Mapping) else "") or None,
        proposed_record=dict(record) if isinstance(record, Mapping) else None,
        missing_information=missing,
        requires_authoritative_execution=False,
        reason=reason,
        confidence=0.7,
        player_facing_text=message,
        context_update=context_update,
    )
