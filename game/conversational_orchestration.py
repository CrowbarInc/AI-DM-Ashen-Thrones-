"""Conversational turn decision boundary for production chat.

This module decides whether a player turn needs authoritative execution before
the chat pipeline advances clocks, ticks, or resolver state. It does not resolve
world outcomes and it does not create canonical facts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
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
    disposition: str = ""

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
    r"\b(?:instead|make that|revise|change (?:my|the) pending)\b",
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
        if _public_scene_row(item)
    ]
    exits = [
        _clean_text(item.get("label") or item.get("name") or item.get("id"))
        for item in current.get("exits") or []
        if _public_scene_row(item)
    ]
    if visible:
        pieces.append("Visible points of interest: " + ", ".join(item for item in visible if item) + ".")
    if exits:
        pieces.append("Known exits: " + ", ".join(item for item in exits if item) + ".")
    return " ".join(piece for piece in pieces if piece).strip()


def _public_scene_row(item: Any) -> bool:
    return (isinstance(item, Mapping) and not item.get("hidden") and not item.get("gm_only")
            and item.get("visible") is not False and item.get("accessible") is not False)


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


_SCENE_OVERVIEW = re.compile(
    r"what (?:can (?:i|we) see(?: (?:around me|around us|from here|here))?|is here)", re.I,
)
_SCENE_OBSERVATION = re.compile(
    r"(?:"
    r"(?:can|do) (?:i|we) see (?P<sight>(?!if\b|whether\b)[^,!?;]+?)(?: from here)?"
    r"|(?:is|are) (?P<presence>[^,!?;]+?)(?: still)? "
    r"(?P<position>(?:right |directly )?in front of (?:me|us)|visible(?: from here)?|here|nearby|"
    r"around (?:me|us)|at this gate|on the ground here)"
    r"|what is (?P<relative>directly in front of me|in front of me|beside the road)"
    r"|what is on (?P<contents>[^,!?;]+)"
    r")", re.I,
)


def _scene_subject(text: str) -> str:
    return _norm_place(re.sub(r"^(?:there|those|these|that|this|the same)\s+", "", text, flags=re.I))


def _named_visible_scene_rows(subject, scene, world, session):
    from game.interaction_context import canonical_scene_addressable_roster
    from game.player_interpretation_bridge import visible_catalog

    roster = {
        row["id"]: row for row in canonical_scene_addressable_roster(
            world, _scene_id(scene), scene_envelope=scene, session=session,
        ) if _public_scene_row(row) and row.get("id")
    }
    for entity_id, item in visible_catalog(scene, world).items():
        row = item["row"]
        if item["kind"] == "exit" or not _public_scene_row(row):
            continue
        if item["kind"] == "npc":
            if entity_id not in roster:
                continue
            row = roster[entity_id]
        names = (*_aliases(row, entity_id), *(row.get("address_roles") or []))
        if subject in {_norm_place(name) for name in names}:
            yield entity_id, row


def _current_observation_decision(text, *, scene, session, world, defer_unknown=False):
    """Ground literal perception questions in the effective active scene."""
    question = re.sub(r"^(?:GM|DM|Dungeon Master),\s*", "", text, flags=re.I).rstrip("?").strip()
    overview = _SCENE_OVERVIEW.fullmatch(question)
    query = _SCENE_OBSERVATION.fullmatch(question)
    if not overview and not query:
        return None
    # Do not claim a single subject or swallow a second conjunct.
    if query and re.search(r"\b(?:and|or|if|whether)\b", question, re.I):
        return None
    scene_id = (session or {}).get("active_scene_id") or _scene_id(scene)
    if scene_id != _scene_id(scene):
        scene = None
    public = public_conversation_evidence(scene, [])
    evidence = {}
    if overview and public.get("scene"):
        evidence["active_scene_public_summary"] = public["scene"]
    elif query:
        position = _clean_text(query["position"]).lower()
        subject = _scene_subject(query["sight"] or query["presence"] or query["contents"] or "")
        if subject and position != "visible from here" and "in front of" not in position:
            matches = list(_named_visible_scene_rows(subject, scene, world, session))
            names = {subject}
            if len(matches) == 1:
                entity_id, row = matches[0]
                names.add(_norm_place(_label(row, entity_id)))
            evidence = {
                ref: fact for ref, fact in public.items() if ref.startswith("visible:")
                and any(name and f" {name} " in f" {_norm_place(fact)} " for name in names)
                and (not query["contents"] or re.search(r"\b(?:says?|lists?|reads?|posted|written)\b", fact, re.I))
                and (position != "on the ground here" or " on the ground " in f" {fact.casefold()} ")
            }
            if not evidence and len(matches) == 1 and not query["contents"] and position != "on the ground here":
                evidence[f"visible_catalog:{entity_id}"] = f"{_label(row, entity_id)} is here."
        # Off-scene sight lines and precise relative positions require authored
        # support beyond the presence of something with the same name.
        if query["relative"] == "beside the road":
            evidence = {ref: fact for ref, fact in public.items() if ref.startswith("visible:")
                        and " beside the road " in f" {_norm_place(fact)} "}
    if not evidence and defer_unknown:
        return None
    return ConversationalDecision(
        category=ConversationalDecisionCategory.ANSWER, primary_intention=text,
        intent_family="context_question", communication_owner="GM", communication_purpose="QUESTION",
        reason=("visible_scene_context_answer" if evidence else "current_observation_unestablished"),
        player_facing_text=(" ".join(dict.fromkeys(evidence.values())) if evidence else
                            "That is not established by what you can see from here."),
        context_references=list(evidence),
        execution_policy="answer_only", intent_modality="informational",
        authorization={"source": "current_scene_public_evidence", "scene_id": scene_id,
                       "mutation_eligibility": False},
    )


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


def _pending_revision_decision(text: str, *, session, scene, purpose: str, components=()) -> ConversationalDecision | None:
    """Revise an unexecuted intention. Do not execute it and do not undo a resolved one."""
    if purpose == "WITHDRAWAL":
        return None
    ctx = _conversation_context(session)
    pending = ctx.get("pending_intention") if isinstance(ctx.get("pending_intention"), Mapping) else None
    if pending is None and isinstance(ctx.get("pending_clarification"), Mapping):
        pending = ctx.get("pending_clarification")
    # A correction label or conversational repair phrase is not action control.
    # Implicit revisions need both an intention referent and an action proposal;
    # explicit revision requests still reach the no-pending / executed guards.
    if not _REVISION_RE.search(text) and not (
        (purpose == "CORRECTION" or re.search(r"\b(?:i meant|change that)\b", text, re.I))
        and (isinstance(pending, Mapping) or isinstance(ctx.get("last_executed_intention"), Mapping))
        and any(
            isinstance(component, Mapping)
            and component.get("operation_class") in _CONNECTED_OPERATIONS | {"ATTACK", "USE_VISIBLE_OBJECT", "FOLLOW"}
            for component in components
        )
    ):
        return None
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
        _NON_ADDRESSEE_OPERATIONS,
        addressee_authority_applies,
        assess_addressee_grounding,
        conversational_authorization_record,
        pending_addressee_clarification,
        player_text_addresses_someone,
    )

    operations = [
        str(component.get("operation_class") or "").strip().upper()
        for component in components
        if isinstance(component, Mapping) and str(component.get("operation_class") or "").strip()
    ]
    if "ASK" in operations:
        authority_operation = "ASK"
    elif len(operations) == 1:
        authority_operation = operations[0]
    else:
        authority_operation = None
    grounding = assess_addressee_grounding(
        text,
        scene=scene,
        world=world,
        session=session,
        proposed_target_id=ask_targets[0] if len(ask_targets) == 1 else None,
    )
    addresses_someone = player_text_addresses_someone(text)
    mislabeled_noncommunication = bool(
        addresses_someone
        and operations
        and "ASK" not in operations
        and all(operation in _NON_ADDRESSEE_OPERATIONS for operation in operations)
    )
    if (
        addressee_authority_applies(operation=authority_operation, player_text=text)
        and grounding.get("direct_address")
        and grounding.get("operation_eligibility") == "requires_clarification"
    ):
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
    if mislabeled_noncommunication and grounding.get("operation_eligibility") == "executable" and grounding.get("target_id"):
        # The utterance addresses someone. Inspection or travel language in
        # that sentence does not authorize the object or the route.
        target_id = str(grounding.get("target_id") or "")
        label = next(
            (
                str(choice.get("label") or "")
                for choice in (grounding.get("choices") or [])
                if isinstance(choice, Mapping) and str(choice.get("entity_id") or "") == target_id
            ),
            target_id,
        )
        return ConversationalDecision(
            category=ConversationalDecisionCategory.EXECUTE,
            primary_intention=text,
            intent_family="world_operation",
            proposed_operation="ASK",
            proposed_target=target_id,
            proposed_record=_operation_record(
                operation="ASK",
                target_id=target_id,
                player_text=text,
                summary=f"Ask {label}.",
                references={
                    "resolved_references": [{"text": label, "entity_id": target_id}],
                    "unresolved_references": [],
                },
            ),
            requires_authoritative_execution=True,
            reason="communication_act_not_object_or_route",
            player_facing_text="",
            execution_policy="execute_primary",
            authorization=conversational_authorization_record(
                grounding,
                player_text=text,
                authority_provenance="communication_decision",
            ),
        )
    if mislabeled_noncommunication:
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=text,
            intent_family="clarification",
            communication_owner="GM",
            communication_purpose="CLARIFICATION",
            reason="communication_act_not_object_or_route",
            player_facing_text=str(
                grounding.get("clarification")
                or "That request addresses someone. Nothing has been attempted."
            ),
            execution_policy="answer_only",
            intent_modality="informational",
            proposed_operation="ASK",
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
    revision = _pending_revision_decision(text, session=session, scene=scene, purpose=purpose, components=components)
    if revision is not None:
        return revision
    category = ConversationalDecisionCategory.ANSWER
    update = None
    published_refs = []
    if purpose == "WITHDRAWAL":
        answer = "I've set aside the unexecuted intention. Anything already resolved still stands."
        update = _context_update(pending=None, pending_set=True, intention=None, intention_set=True, clear_interlocutor=False)
    elif owner == "MIXED":
        category = ConversationalDecisionCategory.CLARIFY
        answer = "Let's settle the question before attempting the action. "
        current = (public_conversation_evidence(scene, [])
                   if (session or {}).get("active_scene_id") in (None, "", _scene_id(scene)) else {})
        evidence = {ref: current[ref] for ref in evidence_refs if ref in current}
        published_refs = list(evidence)
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
        published_refs = list(evidence)
        answer = " ".join(dict.fromkeys(str(value) for value in evidence.values()))
        # Receipt only for a resolved conversational correction with a grounded
        # answer. Mechanical revisions returned above; no semantic reclassification.
        if (answer and owner == "GM" and purpose == "CORRECTION"
                and status == "INTERPRETED" and not components
                and not (record.get("references") or {}).get("unresolved_references")
                and (record.get("correction") or {}).get("subject") == "REFERENT"
                and evidence_refs and all(ref in evidence for ref in evidence_refs)):
            answer = "Understood. " + answer
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
        context_references=published_refs,
        context_update=update, execution_policy="answer_only", intent_modality="informational",
        secondary_intentions=[dict(c) for c in components if isinstance(c, Mapping)] if owner == "MIXED" or category == ConversationalDecisionCategory.CLARIFY else [],
    )


def _gm_continuation_decision(
    text: str,
    session: Mapping[str, Any] | None,
    log: list | None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> ConversationalDecision | None:
    """Resolve clear facilitator follow-ups before an active NPC can capture them."""
    withdrawal = re.match(
        r"^(?:no[,.!]?\s*)?(?:actually[,.]?\s*)?(?:never\s+mind|forget\s+(?:it|that|the\s+\w+)|cancel|don't\s+(?:do|open|move|go))\b",
        text,
        re.I,
    )
    if withdrawal or (
        _conversation_context(session).get("pending_clarification") and re.fullmatch(r"(?:no|nope|not now)[.!]?", text, re.I)
    ):
        from game.conversational_continuity import span_abandons_intention, without_abandoned_clauses

        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        kept = [part for part in sentences if not span_abandons_intention(part)]
        rest = " ".join(kept).strip() or without_abandoned_clauses(text).strip()
        # "Never mind the captain. What does the runner know?" keeps the question.
        if withdrawal and rest and rest != text and not re.match(r"^(?:never\s+mind|forget|cancel)\b", rest, re.I):
            return deterministic_conversational_decision(
                player_text=rest, scene=scene, world=world, session=session, log=log,
            )
        return _communication_decision({"communication": {"recipient": "GM", "purpose": "WITHDRAWAL"}}, text)
    if re.match(r"^actually\b", text, re.I):
        pending = _conversation_context(session).get("pending_clarification") or {}
        remainder = re.sub(r"^actually[,.]?\s*", "", text, count=1, flags=re.I).strip()
        # "Actually, return to the gate" replaces a withheld compound. A bare
        # correction with no travel verb still uses the existing answer.
        if (
            isinstance(pending, Mapping)
            and pending.get("kind") == "compound_sequence"
            and remainder
            and (_MOVE_CUE_RE.search(remainder) or _BACK_RE.search(remainder))
            and not _ELIDED_CONSEQUENTIAL_RE.search(remainder)
        ):
            return None
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


def _npc_directed_followup(text: str) -> bool:
    if re.search(
        r"\b(?:notice board|where am i|where are we|what do i see|what can i see|what is here|"
        r"what (?:do|did|have) (?:i|we) know|remind me|my (?:inventory|journal))\b",
        text,
        re.I,
    ):
        return False
    if re.search(r"\b(?:attack|follow|move|go|head|walk|travel|inspect|examine|open|take|steal|cast)\b", text, re.I):
        return False
    return bool(
        _QUESTION_START_RE.search(text)
        or "?" in text
        or _FOLLOWUP_FRAGMENT_RE.search(text)
        or _PRONOUN_REFERENCE_RE.search(text)
    )


def _active_interlocutor(session: Mapping[str, Any] | None, catalog: Mapping[str, Any]) -> str:
    ctx = _interaction_context(session)
    kind = _clean_text(ctx.get("active_interaction_kind")).casefold()
    target = _clean_text(ctx.get("active_interaction_target_id"))
    if kind == "social" and target in catalog and catalog[target].get("kind") == "npc":
        return target
    conv = _conversation_context(session).get("active_interlocutor")
    if not isinstance(conv, Mapping) or conv.get("status") != "active":
        return ""
    campaign = _clean_text(conv.get("campaign_id"))
    if campaign and isinstance(session, Mapping) and campaign != _clean_text(session.get("campaign_run_id")):
        return ""
    npc_id = _clean_text(conv.get("npc_id"))
    if npc_id in catalog and catalog[npc_id].get("kind") == "npc":
        return npc_id
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
    catalog = _catalog(scene, world)
    active_id = _active_interlocutor(session, catalog)
    if not active_id:
        return None
    from game.intent_parser import looks_like_explicit_leave_or_pursuit_intent

    # A pronoun such as "them" must not turn an explicit departure into dialogue.
    if looks_like_explicit_leave_or_pursuit_intent(text):
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
    from game.conversational_continuity import established_scene_object_ids

    # A named scene object is not a follow-up to the person who spoke last.
    if established_scene_object_ids(text, scene):
        return None
    # Live interpretation still classifies genuinely open turns. An ordinary
    # follow-up to the person already speaking does not need that call.
    from game.interaction_completion import addressed_person_nominal
    from game.ordinary_semantic_ownership import assess_addressee_grounding, npc_followup_cue

    if addressed_person_nominal(text) or not npc_followup_cue(text) or not _npc_directed_followup(text):
        return None
    grounding = assess_addressee_grounding(text, scene=scene, world=world, session=session)
    if grounding.get("target_id") != active_id or grounding.get("operation_eligibility") != "executable":
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
    if reason == "route_requires_prerequisite":
        return "That route cannot be used right now. You stay where you are.", ["available_route"]
    if reason == "unreconciled_departure_route":
        return "Which available route do you want to take? You stay where you are.", ["destination"]
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
_TRAILING_THOUGHT_RE = re.compile(r"\s+thinking\s+about\b", re.IGNORECASE)


def _committed_move_with_trailing_thought(text: str) -> bool:
    """A completed move whose only tentative cue is a trailing motive.

    "I was thinking about the gate" stays tentative. "I go to the fortress
    trail thinking about the rumor" is the move, with the thought attached.
    """
    match = _TRAILING_THOUGHT_RE.search(text or "")
    if not match:
        return False
    remainder = (text or "")[: match.start()].strip(" .?!")
    if not remainder or _TENTATIVE_RE.search(remainder):
        return False
    return bool(_MOVE_CUE_RE.search(remainder) and _destination_phrase(remainder))
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
_INSPECT_CUE_RE = re.compile(r"\b(?:investigate|inspect|examine|look\s+(?:at|for)|search\s+for|check|study|read)\b", re.IGNORECASE)
_ASK_CUE_RE = re.compile(r"\b(?:ask|question|speak\s+to|talk\s+to)\b", re.IGNORECASE)
_OTHER_CUE_RE = re.compile(
    r"\b(?:open|pick|unlock|attack|draw|sheath|sheathe|unsheathe|put\s+away|"
    r"drop|mark|wipe|remove|equip|unequip|search|take)\b",
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
    r"\b(?:investigate|inspect|examine|look\s+(?:at|for)|search\s+for|check|study|read|open|pick|unlock|ask|watch|watching)\s+(?:the\s+|a\s+)?(.+)$",
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
    from game.route_authority import authored_exit_rows
    rows: list[dict[str, Any]] = []
    for item in authored_exit_rows(dict(scene or {})):
        if (isinstance(item, Mapping) and _clean_text(item.get("id"))
                and not item.get("hidden") and item.get("visible") is not False
                and item.get("source_scene_id", _scene_id(scene)) == _scene_id(scene)):
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


def _match_exit_phrase(phrase: str, exits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in exits:
        if any(_place_match(phrase, name) for name in _exit_names(row)):
            hits.append(row)
    return _unique_exit_rows(hits)


def _matching_exits(phrase: str, exits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Match a destination. A purpose tail is not part of the name.

    The full phrase wins when it is the authored name. The tail is dropped
    only when the remainder is what the catalog actually names.
    """
    hits = _match_exit_phrase(phrase, exits)
    if hits:
        return hits
    from game.scene_destination_binding import (
        _normalized_destination_key,
        _phrase_names_authored_destination,
        destination_phrase_respecting_purpose_tail,
    )

    if _phrase_names_authored_destination(phrase, exits):
        return []
    peeled = destination_phrase_respecting_purpose_tail(phrase, exits)
    if not peeled or _normalized_destination_key(peeled) == _normalized_destination_key(phrase):
        return []
    return _match_exit_phrase(peeled, exits)


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


_PURPOSE_RE = re.compile(
    r"\s+(?:in\s+order\s+to|so\s+as\s+to|to)\s+"
    r"(?=(?:investigate|examine|inspect|look|search|check|study|read|buy|sell|ask|"
    r"speak|talk|meet|find|learn|help|rest|wait|open|take|attack)\b)", re.IGNORECASE,
)
# A coordinated continuation can drop "I" and still request its own consequence.
# These verbs already name social, purchase, or theft acts. They are not purpose
# infinitives and they are not incidental posture.
_ELIDED_VERB_WORDS = frozenset({
    "persuade", "persuading", "intimidate", "intimidating", "deceive", "deceiving",
    "bluff", "bluffing", "buy", "buying", "steal", "stealing", "barter", "bartering",
    "recruit", "recruiting", "convince", "convincing",
})
_SEQUENCE_ADVERB_RE = re.compile(
    r"^(?:afterward|afterwards|then|next|later|first|second)(?:[,.]|\s)+",
    re.IGNORECASE,
)
_ELIDED_CONSEQUENTIAL_RE = re.compile(
    r"^(?:please\s+)?"
    r"(?:(?:just|carefully|slowly|quietly)\s+)?"
    r"(?:(?:try|attempt)(?:ing)?\s+to\s+)?"
    r"(?P<verb>persuad(?:e|ing)|intimidat(?:e|ing)|deceiv(?:e|ing)|bluff(?:ing)?|"
    r"buy(?:ing)?|steal(?:ing)?|barter(?:ing)?|recruit(?:ing)?|convinc(?:e|ing))\b",
    re.IGNORECASE,
)
_BARE_MOVE_RE = re.compile(
    r"^\s*(?:(?:i|we)\s+)?(?:head|go|walk|travel|move|approach|follow|proceed)\s+(.+)$",
    re.IGNORECASE,
)


def _movement_and_purpose(text: str) -> tuple[str, str]:
    """Split a bounded infinitive purpose; recognizing it grants no effects."""
    match = _PURPOSE_RE.search(text)
    if match:
        return text[:match.start()].strip(), text[match.end():].strip(" .?!")
    return text, ""


def _destination_phrase(text: str) -> str:
    cleaned = re.sub(r"\s+(?:from here|right now|instead)\b.*$", "", _clean_text(text), flags=re.IGNORECASE)
    cleaned, _ = _movement_and_purpose(cleaned)
    match = _DEST_PREP_RE.search(cleaned)
    if match is None:
        match = _BARE_MOVE_RE.search(cleaned)
        if match is None:
            return ""
    dest = re.split(r"\s+(?:and|then|while|but)\s+", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
    dest = dest.strip(" .?!")
    if dest.casefold() in {"out", "off", "away"}:
        return ""
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
        if len(pieces) > 1 and all(_clause_has_verb(piece) for piece in pieces):
            clauses.extend(piece.strip(" ,.") for piece in pieces if piece.strip(" ,."))
        else:
            clauses.append(part.strip(" ,."))
    return [clause for clause in clauses if clause]


def _clause_has_verb(text: str) -> bool:
    return bool(
        _MOVE_CUE_RE.search(text)
        or re.search(r"\benter\b", text, re.IGNORECASE)
        or _INSPECT_CUE_RE.search(text)
        or _ASK_CUE_RE.search(text)
        or _OTHER_CUE_RE.search(text)
        or _WATCH_RE.search(text)
        or _SOCIAL_EXIT_RE.search(text)
        or _BACK_RE.search(text)
        or _marking_clause(text)
    )


def _marking_clause(text: str) -> bool:
    # Reuse the actual bounded action recognizers, including their try/use
    # forms, rather than maintaining a second marking vocabulary here.
    from game.marking_action import recognize_marking
    from game.marking_removal import recognize_removal

    return recognize_marking(text) is not None or recognize_removal(text) is not None


_COVERAGE_FUNCTION = frozenset({
    "a", "an", "the", "my", "our", "your", "his", "her", "their", "its",
    "this", "that", "these", "those", "some",
    "to", "of", "in", "on", "at", "for", "from", "with", "into", "onto", "over",
    "under", "through", "toward", "towards", "about", "beside", "by", "as",
    "than", "via", "upon", "off", "out", "up", "down", "away", "back",
    "and", "or", "but", "nor", "so", "yet",
    "not", "no", "never",
    "i", "we", "me", "us", "you",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "just", "carefully", "slowly", "quietly", "please", "now", "still", "really",
    "here", "there", "again",
})
_RESIDUAL_VERB_RE = re.compile(
    r"^(?:please\s+)?(?:i|we)\s+"
    r"(?:(?:will|would|shall|should|can|could|may|might|must|do|am|are)\s+)?"
    r"(?:not\s+)?"
    r"(?:(?:just|carefully|slowly|quietly)\s+)?"
    r"(?:(?:want|need|try|going)\s+to\s+)?"
    r"([a-z]+)\b",
    re.IGNORECASE,
)
_SPAN_NEGATION_RE = re.compile(
    r"^(?:please\s+)?(?:(?:i|we)\s+)?(?:do\s+not|will\s+not|cannot|never|refuse\s+to|not)\b",
    re.IGNORECASE,
)
_ALTERNATIVE_RE = re.compile(
    r"\s+or\s+(?:(?:i|we)\s+)?(?:enter|take|go|travel|inspect|ask|drop|keep)\b",
    re.IGNORECASE,
)
_DEFERRED_START_RE = re.compile(
    r"^\s*(?:when\b|(?:(?:i|we)\s+)?plan\s+to\b)",
    re.IGNORECASE,
)
_FUTURE_DEFERRED_RE = re.compile(
    r"\b(?:i|we)\s+will\b[\s\S]{0,80}\b(?:tomorrow|tonight|later)\b",
    re.IGNORECASE,
)


def _normalize_player_modals(text: str) -> str:
    raw = _clean_text(text)
    raw = re.sub(r"\b([Ii]|[Ww]e)'ll\b", r"\1 will", raw)
    raw = re.sub(r"\b([Ii])'m\b", r"\1 am", raw)
    raw = re.sub(r"\bwon't\b", "will not", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bcan't\b", "cannot", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bdon't\b", "do not", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bn't\b", " not", raw, flags=re.IGNORECASE)
    return raw


def _coverage_scope(span: str) -> str:
    """Drop contrastive tails. 'Instead of entering' is not a requested move."""
    return re.sub(r"\b(?:instead of|rather than)\b.*$", "", span, flags=re.IGNORECASE).strip()


def _known_coverage_operation(span: str) -> str:
    """One existing cue family for this span. This does not add action verbs."""
    sample = _coverage_scope(span)
    if not sample:
        return ""
    from game.conversational_continuity import conversational_topic_return, span_abandons_intention

    # An abandoned topic, or a return to a discussion, is not a gameplay operation.
    if span_abandons_intention(sample) or conversational_topic_return(sample):
        return ""
    if _marking_clause(sample):
        return "OTHER"
    if _WATCH_RE.search(sample) and not _destination_phrase(sample):
        return "OTHER"
    if _INSPECT_CUE_RE.search(sample):
        return "INSPECT"
    if _OTHER_CUE_RE.search(sample):
        return "OTHER"
    if _ASK_CUE_RE.search(sample) and not _MOVE_CUE_RE.search(sample):
        return "ASK"
    if (_MOVE_CUE_RE.search(sample) or _BACK_RE.search(sample)
            or re.search(r"\benter(?:s|ing)?\b", sample, re.IGNORECASE)):
        return "MOVE"
    if re.search(r"\btake\b", sample, re.IGNORECASE) and not re.search(r"\btake\s+a\s+seat\b", sample, re.IGNORECASE):
        return "MOVE"
    from game.physical_adjudication import _operation

    if _operation(sample):
        return "OTHER"
    # Subject-elided "and persuade" is a second act. A purpose infinitive
    # ("to buy", "to find") does not start the span, so it stays with travel.
    if _ELIDED_CONSEQUENTIAL_RE.match(_clean_text(sample)):
        return "OTHER"
    residual = _residual_agentive_verb(sample)
    if residual in _ELIDED_VERB_WORDS:
        return "OTHER"
    sequenced = _SEQUENCE_ADVERB_RE.sub("", _clean_text(sample), count=1)
    if sequenced != _clean_text(sample):
        if _ELIDED_CONSEQUENTIAL_RE.match(sequenced):
            return "OTHER"
        if _residual_agentive_verb(sequenced) in _ELIDED_VERB_WORDS:
            return "OTHER"
    return ""


def _residual_agentive_verb(span: str) -> str:
    """A first-person predicate the existing cue lists do not name.

    Object lists and modifiers do not match: the span must start with I/we.
    The captured word is not added to any verb lexicon.
    """
    match = _RESIDUAL_VERB_RE.match(_normalize_player_modals(_coverage_scope(span)).casefold())
    if not match:
        return ""
    word = match.group(1)
    # Stay/wait are existing non-travel postures, not uncovered physical commands.
    if word in _COVERAGE_FUNCTION or word in {"stay", "remain", "wait", "waiting", "staying", "remaining"}:
        return ""
    return word


def _span_is_incidental(span: str) -> bool:
    return bool(_SOCIAL_EXIT_RE.search(span)) and not _known_coverage_operation(span)


def _span_has_command(span: str) -> bool:
    if _span_is_incidental(span):
        return False
    from game.conversational_continuity import conversational_topic_return

    # Keep a discourse return as its own span so it is not swallowed by an
    # abandoned clause. It is still not an affirmative gameplay operation.
    if conversational_topic_return(span):
        return True
    return bool(_known_coverage_operation(span) or _residual_agentive_verb(span))


def _peel_fronted_adjunct(text: str) -> tuple[str, str]:
    match = re.match(r"^(?P<head>[^,.]{1,120}),\s*(?P<tail>(?:i|we)\b.+)$", text.strip(), re.IGNORECASE)
    if not match:
        return text, ""
    head = match.group("head").strip()
    if re.match(r"^(?:i|we)\b", head, re.IGNORECASE) or _span_has_command(head):
        return text, ""
    return match.group("tail").strip(), head


def _split_sequenced(chunk: str) -> list[str]:
    match = re.search(r"\bbefore\b", chunk, re.IGNORECASE)
    if not match:
        return [chunk]
    left = chunk[:match.start()].strip(" ,.")
    right = chunk[match.end():].strip(" ,.")
    if left and right and _span_has_command(left) and _span_has_command(right):
        return [left, right]
    return [chunk]


def _coordinated_spans(chunk: str) -> list[str]:
    """Split command coordination. Noun-phrase pieces stay with the prior command."""
    pieces = [
        part.strip(" ,.")
        for part in re.split(r"\s*,?\s+then\s+|\s+and\s+then\s+|\s+and\s+|\s+but\s+", chunk, flags=re.IGNORECASE)
        if part.strip(" ,.")
    ]
    refined: list[str] = []
    for piece in pieces or [chunk]:
        refined.extend(_split_sequenced(piece))
    grouped: list[str] = []
    buffer = ""
    for piece in refined:
        if not buffer:
            buffer = piece
            continue
        if _span_has_command(piece) and _span_has_command(buffer):
            grouped.append(buffer)
            buffer = piece
        else:
            buffer = f"{buffer} and {piece}"
    if buffer:
        grouped.append(buffer)
    return grouped


def _coverage_spans(text: str) -> tuple[list[str], str]:
    body, adjunct = _peel_fronted_adjunct(_clean_text(text))
    spans: list[str] = []
    for sentence in re.split(r"(?<=[.!])\s+", body):
        sentence = sentence.strip()
        if not sentence:
            continue
        for clause in re.split(r"\s*;\s*", sentence):
            clause = clause.strip(" ,.")
            if clause:
                spans.extend(_coordinated_spans(clause))
    return [span for span in spans if span], adjunct


def _coverage_span_record(span: str) -> dict[str, Any]:
    raw = span.strip(" .")
    from game.conversational_continuity import conversational_topic_return, span_abandons_intention

    abandoned = span_abandons_intention(raw)
    discourse = conversational_topic_return(raw)
    operation = "" if abandoned or discourse else _known_coverage_operation(raw)
    residual = "" if operation or abandoned or discourse else _residual_agentive_verb(raw)
    if residual:
        operation = "UNRECOGNIZED"
    negated = abandoned or bool(_SPAN_NEGATION_RE.search(_normalize_player_modals(raw)))
    incidental = _span_is_incidental(raw)
    affirmative = bool(operation) and not negated and not incidental
    if abandoned:
        evidence = "abandoned_intention"
        referent = "abandoned"
    elif discourse:
        evidence = "conversational_referent"
        referent = "topic"
    elif incidental:
        evidence = "incidental_social"
        referent = ""
    elif negated and operation:
        evidence = "negated_span"
        referent = "physical" if operation == "MOVE" else "operation"
    elif operation == "UNRECOGNIZED":
        evidence = "unrecognized_agentive_predicate"
        referent = ""
    elif operation:
        evidence = "known_operation_cue"
        referent = "physical" if operation == "MOVE" else "operation"
    else:
        evidence = "manner_object_or_context"
        referent = ""
    return {
        "text": raw,
        "operation": operation,
        "known": bool(operation) and operation != "UNRECOGNIZED",
        "negated": negated,
        "incidental": incidental,
        "affirmative": affirmative,
        "evidence": evidence,
        "referent": referent,
        "residual_verb": residual,
    }


def _request_is_alternative(text: str) -> bool:
    return bool(_ALTERNATIVE_RE.search(text))


def _request_is_deferred(text: str) -> bool:
    normalized = _normalize_player_modals(text)
    if _DEFERRED_START_RE.search(text):
        return True
    return bool(_FUTURE_DEFERRED_RE.search(normalized))


def actionable_coverage(text: str, *, scene: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Whether one selected operation represents the whole actionable request.

    Structural spans reuse the existing cue families. An unrecognized
    first-person predicate is evidence of uncovered content, not a new verb
    list and not permission to execute the recognized part. This record does
    not bind a target, mutate state, or authorize an action.
    """
    raw = _clean_text(text)
    spans, adjunct = _coverage_spans(raw)
    records = [_coverage_span_record(span) for span in spans]
    affirmative = [record for record in records if record["affirmative"]]
    question = bool("?" in raw or _QUESTION_START_RE.search(raw))
    alternative = _request_is_alternative(raw)
    deferred = _request_is_deferred(raw)
    conditional = bool(re.match(r"\s*(?:if|unless)\b", raw, re.IGNORECASE))
    # A condition can follow the act it restricts. Preserve uncertain meaning
    # (including mixed information requests) for the existing interpreter;
    # a recognized singleton action cannot discard its trailing prerequisite.
    if not question and len(affirmative) == 1 and affirmative[0]["known"] and affirmative[0]["operation"] != "ASK":
        conditional = conditional or bool(re.search(
            r"\b(?:if|unless|when|once|provided(?:\s+that)?|as\s+long\s+as)\b", raw, re.I,
        ))
    tentative = bool(_TENTATIVE_RE.search(raw)) and not re.search(
        r"\bbut\s+(?:i\s+)?(?:go|head|walk|leave|travel|enter)\b", raw, re.IGNORECASE,
    ) and not _committed_move_with_trailing_thought(raw)
    from game.intent_parser import _explicit_stay_or_travel_negation

    withheld_travel = _explicit_stay_or_travel_negation(raw) and not affirmative
    unrecognized = [record for record in affirmative if not record["known"]]
    if question or alternative or deferred or conditional or tentative or withheld_travel:
        classification = "NON_EXECUTION"
    elif len(affirmative) > 1 and unrecognized:
        classification = "UNCERTAIN"
    elif len(affirmative) > 1:
        classification = "INCOMPLETE"
    elif len(affirmative) == 1:
        classification = "COMPLETE"
    elif any(record["negated"] for record in records):
        classification = "NON_EXECUTION"
    else:
        classification = "COMPLETE"
    selected = None
    remaining = list(affirmative)
    if affirmative:
        selected = next((record for record in affirmative if record["operation"] == "MOVE"), affirmative[0])
        remaining = [record for record in affirmative if record is not selected]
        if classification == "COMPLETE":
            selected = affirmative[0]
            remaining = []
    admission = "proceed" if classification == "COMPLETE" else "withhold_execution"
    if classification == "NON_EXECUTION":
        admission = "nonexecution"
    return {
        "owner": "conversational_admission",
        "original_text": raw,
        "scene_id": _scene_id(scene) if scene is not None else "",
        "fronted_adjunct": adjunct,
        "spans": records,
        "selected_operation": None if selected is None else {
            "text": selected["text"],
            "operation": selected["operation"],
            "owner": "conversational_admission",
            "known": selected["known"],
        },
        "classification": classification,
        "evidence": [record["evidence"] for record in records],
        "remaining_actionable": [
            {"text": record["text"], "operation": record["operation"], "known": record["known"]}
            for record in remaining
        ],
        "negation": any(record["negated"] for record in records),
        "alternative": alternative,
        "deferred": deferred,
        "conditional": conditional,
        "tentative": tentative,
        "question": question,
        "admission": admission,
        "referent_class": _referent_class(records),
    }


def _referent_class(records: list[dict[str, Any]]) -> str:
    kinds = {str(record.get("referent") or "") for record in records}
    if "topic" in kinds and "physical" in kinds:
        return "mixed"
    if "abandoned" in kinds and "topic" in kinds:
        return "abandoned_topic_return"
    if "topic" in kinds:
        return "topic_return"
    if "abandoned" in kinds and any(record.get("affirmative") for record in records):
        return "abandoned_with_request"
    if "abandoned" in kinds:
        return "abandoned"
    if "physical" in kinds:
        return "physical"
    return "other"


def compound_action_assessment(text: str, *, scene: Mapping[str, Any] | None) -> dict[str, Any]:
    """Retain independent requested acts before a singleton shortcut consumes one.

    Uses the existing clause/operation signals. This record cannot authorize an
    action, bind a destination, or execute a sequence. Context and negated acts
    are deliberately excluded from the affirmative candidate count.
    """
    clauses = [_analyze_clause(part, _exit_rows(scene)) for part in _split_clauses(text)]
    affirmative = []
    for clause in clauses:
        raw = str(clause["text"])
        head = re.sub(r"^(?:i|we)\s+", "", raw, flags=re.I)
        head = re.sub(r"^(?:(?:carefully|slowly|quietly|just)\s+)+", "", head, flags=re.I)
        # A verb inside a contextual or negated clause is not a new request.
        if not (any(cue.match(head) for cue in (
            _MOVE_CUE_RE, _INSPECT_CUE_RE, _ASK_CUE_RE, _OTHER_CUE_RE, _WATCH_RE, _BACK_RE,
        )) or re.match(r"(?:enter|take)\b", head, re.I) or _marking_clause(raw)):
            continue
        if clause.get("consequential"):
            affirmative.append(clause)
    coverage = actionable_coverage(text, scene=scene)
    return {"owner": "conversational_admission", "candidates": clauses,
            "affirmative_operations": affirmative, "unsupported_compound": len(affirmative) > 1,
            "coverage": coverage}


def _coverage_refusal(text: str, coverage: Mapping[str, Any], assessment: Mapping[str, Any]) -> ConversationalDecision:
    classification = str(coverage.get("classification") or "")
    reason = {
        "INCOMPLETE": "incomplete_actionable_coverage",
        "UNCERTAIN": "uncertain_actionable_coverage",
        "NON_EXECUTION": "actionable_request_not_execution",
    }.get(classification, "compound_request_requires_single_action")
    if coverage.get("alternative"):
        reason = "alternative_actions_require_choice"
    elif coverage.get("deferred"):
        reason = "deferred_request_not_committed"
    elif coverage.get("question") and classification == "NON_EXECUTION":
        reason = "action_question_not_execution"
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=text, intent_family="multi_action", reason=reason,
        player_facing_text=("Nothing has been attempted. I can resolve one supported action at a time. "
                            "Which single action do you want to take now?"),
        execution_policy=("interpret_before_execution" if classification == "UNCERTAIN" else "clarify_before_execution"),
        secondary_intentions=list(assessment.get("affirmative_operations") or []),
        authorization={
            **dict(assessment),
            "coverage": dict(coverage),
            "operation_eligibility": "requires_clarification",
            "mutation_eligibility": False,
            "interpretation_eligibility": "read_only" if classification == "UNCERTAIN" else "not_deferred",
            "execution_withheld": True,
        },
    )


def decision_from_uncertain_interpretation(
    restriction: ConversationalDecision, record: Mapping[str, Any] | None,
    *, scene=None, world=None, session=None, character=None, log=None,
) -> ConversationalDecision:
    """Read meaning without transferring coverage or consequence authority.

    Only a host-accounted, read-only sheet answer can discharge this gate.
    Other meanings retain the complete request restriction, including stored
    singleton records and model assertions that a clause is incidental.
    """
    text = restriction.primary_intention
    authorization = dict(restriction.authorization or {})
    coverage = authorization.get("coverage") or {}
    fallback = replace(restriction, execution_policy="clarify_before_execution")
    if coverage.get("classification") != "UNCERTAIN" or not isinstance(record, Mapping):
        return fallback
    communication = record.get("communication")
    from game.live_chat_interpretation import valid_communication

    if (record.get("interpretation_status") not in {"INTERPRETED", "CLARIFICATION_REQUIRED"}
            or not valid_communication(communication, public_conversation_evidence(scene, log))):
        return fallback
    components = record.get("action_components")
    if not isinstance(components, list) or any(not isinstance(c, Mapping) for c in components):
        return fallback
    references = record.get("references") or {}
    if not isinstance(references, Mapping):
        return fallback
    declared = references.get("permitted_entity_ids") or []
    from game.carried_object_grounding import interpretation_catalog

    catalog = interpretation_catalog(scene, world, character)
    if not isinstance(declared, list) or any(not isinstance(ref, str) or ref not in catalog for ref in declared):
        return fallback
    spans = coverage.get("spans") or []
    # An unresolved recipient is itself a reason to clarify speech, not a reason
    # to erase it. Validate the complete original orientation/question shape;
    # never endorse the provider's suggested identity or publish its question.
    orientation = re.fullmatch(r"I turn to (?P<person>[\w '-]+)", spans[0].get("text", ""), re.I) if len(spans) == 2 else None
    asks = [c for c in components if c.get("operation_class") == "ASK"]
    posture = [c for c in components if c.get("operation_class") == "SOCIAL_SIGNAL"]
    contextual_posture = all(re.fullmatch(
        r"(?:I\s+)?turn to (?:the )?[\w '-]+[.]?", str(c.get("description") or ""), re.I,
    ) for c in posture)
    if (orientation and re.fullmatch(r"ask\s+[^.!?]+[.]?", spans[1].get("text", ""), re.I)
            and communication["recipient"] in {"GM", "NPC"}
            and communication["purpose"] == "QUESTION" and len(asks) == 1
            and len(posture) <= 1 and len(components) == len(asks) + len(posture)
            and contextual_posture):
        from game.ordinary_semantic_ownership import assess_addressee_grounding
        grounding = assess_addressee_grounding(
            "I ask " + orientation.group("person") + " " + spans[1]["text"][4:],
            scene=scene, world=world, session=session,
            proposed_target_id=asks[0].get("target_ref"),
        )
        message = grounding.get("clarification") or (
            "Which officer do you mean? Please identify someone established in the current scene."
            if grounding.get("target_resolution") not in {"explicit", "contextual"} else
            "Do you mean only to ask that person your question, with turning as context, without another action?"
        )
        if grounding.get("target_resolution") not in {"explicit", "contextual"}:
            message += " Which established person do you want to ask?"
        if "Nothing has been attempted." not in message:
            message += " Nothing has been attempted."
        return replace(fallback, reason="uncertain_speech_requires_grounding_or_scope",
                       communication_owner="NPC", communication_purpose="QUESTION",
                       incidental_context=[spans[0]["text"]],
                       player_facing_text=message,
                       authorization={**authorization, "addressee_grounding": grounding,
                                      "contract_consistency": "UNRESOLVED" if not grounding.get("target_id") else "AUTHORITATIVELY_RESOLVABLE",
                                      "host_validation": "original_orientation_plus_speech",
                                      "mutation_eligibility": False})
    if references.get("unresolved_references"):
        return fallback
    # Validate the original clauses, never the model's shortened summary.
    noncontact = len(spans) == 2 and bool(re.fullmatch(
        r"(?:I|we) keep (?:my|our) hands off (?:it|that|this|the [\w -]+)",
        spans[0].get("text", ""), re.I,
    ))
    possibility = re.fullmatch(
        r"only ask (?:what|which spells) I (?:could|can) cast"
        r"(?: if (?P<condition>[\w -]+))?[.]?",
        spans[1].get("text", "") if len(spans) == 2 else "", re.I,
    )
    condition = possibility.group("condition") if possibility else None
    simple_condition = not condition or not re.search(
        r"\b(?:and|or|then|but|I|we|cast|touch|take|open|move)\b", condition, re.I,
    )
    informational_ask = (len(components) == 1 and components[0].get("operation_class") == "ASK"
                         and components[0].get("target_ref") is None)
    # CLARIFICATION_REQUIRED alone is insufficient. Only the demonstrated null
    # GM-ASK mismatch can be discharged by the complete host-accounted question.
    information_record = (not components and record.get("interpretation_status") == "INTERPRETED") or informational_ask
    if (noncontact and possibility and simple_condition and information_record
            and communication["recipient"] == "GM"
            and communication["purpose"] in {"QUESTION", "DESCRIPTION", "EXPLANATION"}):
        from game.carried_object_grounding import carried_object_decision

        answer = carried_object_decision(
            "What spells do I have prepared?", character=character,
            scene=scene, world=world, session=session, log=log,
        )
        if answer is not None and answer.category == ConversationalDecisionCategory.ANSWER:
            return replace(
                answer, primary_intention=text,
                reason="uncertain_readonly_prepared_information",
                player_facing_text=(
                    "You keep your hands off it. " + answer.player_facing_text
                    + " This is prepared-spell information, not a complete list of possible spellcasting options."
                    + (f" The condition '{condition}' is hypothetical; no spell is cast now." if condition else "")
                ),
                authorization={**(answer.authorization or {}), **authorization,
                               "host_validation": "noncontact_plus_capability_question",
                               "contract_consistency": "AUTHORITATIVELY_RESOLVABLE" if informational_ask else "CONSISTENT",
                               "hypothetical_condition": condition,
                               "mutation_eligibility": False, "turn_advancement": False},
            )
    return replace(fallback, player_facing_text=(
        "I cannot yet account for every part of that request. Which parts describe context, "
        "and which action or information do you want now? Nothing has been attempted."
    ))


def _local_owner_accounts_for_request(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> bool:
    """True when the existing local-action owner already represents the whole utterance.

    Approach-plus-contact is one transient action in that owner, not two
    gameplay operations left for a singleton to commit. A miss returns false
    and coverage withholding stands.
    """
    if scene is None or world is None:
        return False
    from game.local_interaction import resolve_transient_local_action

    outcome = resolve_transient_local_action(text, scene=scene, world=world, session=session)
    return isinstance(outcome, dict)


def _uncommitted_act_admission(
    text: str,
    coverage: Mapping[str, Any],
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """Withhold a negated or conditional player act before any owner executes it.

    Coverage already marks these non-execution. Travel negation and a leading
    conditional that names travel, ask, or tell keep the existing messages.
    A later affirmative act is not swallowed. An authored decision is left to
    that owner. Questions are not acts.
    """
    if coverage.get("question"):
        return None
    raw = _clean_text(text)
    from game.intent_parser import _explicit_stay_or_travel_negation

    if _explicit_stay_or_travel_negation(raw):
        return None
    if re.match(r"\s*if\b", raw, re.IGNORECASE) and re.search(
        r"\b(?:enter|go|head|take|follow|leave|travel|exit|ask|tell)\b",
        raw,
        re.IGNORECASE,
    ):
        return None
    normalized = _normalize_player_modals(raw)
    player_negated = bool(re.match(
        r"\s*(?:i|we)\s+(?:do not|will not|cannot|never)\b"
        r"|\s*(?:i|we)\s+try not to\b",
        normalized,
        re.IGNORECASE,
    ))
    # "I try not to <verb>" is one negated act. Coverage captures "try" as the
    # verb and would otherwise treat the negation as an affirmative attempt.
    bare_try_not = bool(re.match(r"\s*(?:i|we)\s+try not to\b", normalized, re.IGNORECASE)) and not re.search(
        r"[.;]\s*(?:i|we)\b|\bbut\s+(?:i|we)\b",
        normalized,
        re.IGNORECASE,
    )
    leading_condition = bool(re.match(r"\s*(?:if|unless)\b", raw, re.IGNORECASE))
    negated_only = bare_try_not or (player_negated and not coverage.get("selected_operation"))
    conditional_act = leading_condition or bool(coverage.get("conditional"))
    if coverage.get("classification") != "NON_EXECUTION" and not negated_only:
        return None
    if not conditional_act and not negated_only:
        return None
    if scene is not None and world is not None and session is not None:
        from game.authored_action_language import decision_for

        if decision_for(raw, scene=scene, world=world, session=session) is not None:
            return None
    if conditional_act:
        decision = _nonaction_decision(
            raw,
            modality="hypothetical",
            reason="conditional_player_action",
            message="Nothing has been attempted. That action is only conditional.",
        )
        return replace(decision, authorization={
            "authority_provenance": "conversational_admission",
            "actionable_coverage": dict(coverage),
            "original_text": raw,
            "mutation_eligibility": False,
            "turn_advancement": False,
        })
    return _nonaction_decision(
        raw,
        modality="planning",
        reason="negated_player_action",
        message="You do not do that. Nothing has been attempted.",
    )


def _destination_choice_decision(
    text: str,
    choice: Mapping[str, Any],
    exits: list[dict[str, Any]],
    scene: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """Ask which destination was meant. Do not travel and do not reveal route ids."""
    if choice.get("kind") != "unresolved":
        return None
    wanted = {_clean_text(item) for item in choice.get("exit_ids") or []}
    rows = [row for row in exits if _clean_text(row.get("id")) in wanted]
    labels = [_label(row, "") for row in rows if _label(row, "")]
    extra = []
    seen_phrases = set()
    for phrase in choice.get("phrases") or []:
        shown = _clean_text(phrase)
        key = _norm_place(shown)
        if not shown or key in seen_phrases or any(_place_match(shown, label) for label in labels):
            continue
        seen_phrases.add(key)
        extra.append(shown)
    spoken = labels + extra
    message = "Which destination do you mean"
    if spoken:
        message += ": " + " or ".join(spoken[:4])
    message += "? Nothing has been attempted."
    if rows:
        decision = _ambiguous_destination(text, rows, scene=scene, clear=False)
        return replace(
            decision,
            reason="unresolved_destination_alternatives",
            player_facing_text=message,
            missing_information=["destination"],
        )
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=text,
        intent_family="movement",
        missing_information=["destination"],
        reason="unresolved_destination_alternatives",
        confidence=0.84,
        player_facing_text=message,
        execution_policy="clarify_before_execution",
        intent_modality="incomplete",
    )


def _destination_alternative_admission(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    from game.scene_destination_binding import classify_destination_choice

    exits = _exit_rows(scene)
    choice = classify_destination_choice(text, exits)
    if choice.get("kind") != "unresolved":
        return None
    return _destination_choice_decision(text, choice, exits, scene)


def destination_correction_authorizes_move(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    action: Mapping[str, Any] | None,
) -> bool:
    """A single-route correction is the move, not an address to a person.

    A leading nominal such as "Or rather" or an alias such as "Market Road"
    would otherwise be refused as an unmatched person after the route was
    already selected. This does not authorize a different route, and it does
    not apply when the wording is still an unresolved alternative.
    """
    from game.scene_destination_binding import classify_destination_choice

    if not isinstance(action, Mapping):
        return False
    action_id = _clean_text(action.get("id") or action.get("target_id"))
    if not action_id:
        return False
    choice = classify_destination_choice(text, _exit_rows(scene))
    ids = [_clean_text(item) for item in choice.get("exit_ids") or [] if _clean_text(item)]
    return choice.get("kind") == "correction" and ids == [action_id]


def _single_followup_exit(player_text: str, exits: list[dict[str, Any]]) -> dict[str, Any] | None:
    """One named route in a follow-up. Deictic 'there' is not a new destination."""
    text = re.sub(
        r"^(?:actually|just|only|simply)[,.]?\s*", "", _clean_text(player_text), count=1, flags=re.I,
    )
    if not text or _ELIDED_CONSEQUENTIAL_RE.search(text):
        return None
    if not (_MOVE_CUE_RE.search(text) or _BACK_RE.search(text)):
        return None
    destination = _destination_phrase(text) or _destination_phrase(player_text)
    filler = {"there", "here", "first", "now", "just", "please", "only", "simply"}
    if destination and not (set(_norm_place(destination).split()) - filler):
        return None
    matches = _matching_exits(destination, exits) if destination else []
    if len(matches) != 1:
        matches = _matching_exits(text, exits)
    if len(matches) != 1:
        return None
    return matches[0]


def _coordinated_elided_admission(
    text: str,
    coverage: Mapping[str, Any],
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """Withhold travel joined to an independent social, purchase, or theft act.

    A purpose infinitive stays one movement. This uses the existing compound
    clarification and does not execute either part.
    """
    if coverage.get("classification") != "INCOMPLETE":
        return None
    spans = [span for span in coverage.get("spans") or [] if isinstance(span, Mapping) and span.get("affirmative")]
    if len(spans) < 2 or not any(_elided_consequential_text(str(span.get("text") or "")) for span in spans):
        return None
    exits = _exit_rows(scene)
    clauses: list[dict[str, Any]] = []
    for span in spans:
        raw = str(span.get("text") or "")
        if _elided_consequential_text(raw):
            clauses.append({
                "text": raw, "operation": "OTHER", "destination": "",
                "consequential": True, "incidental": False, "back": False,
            })
        else:
            clauses.append(_analyze_clause(raw, exits))
    moves = [clause for clause in clauses if clause.get("operation") == "MOVE" and clause.get("consequential")]
    if len(moves) != 1:
        return None
    catalog = _catalog(scene, world)
    steps = []
    for clause in clauses:
        if clause.get("operation") == "MOVE":
            steps.append(_step_from_clause(
                clause, exits=exits, catalog=catalog, scene=scene, session=session,
            ))
        else:
            steps.append({
                "text": clause.get("text") or "",
                "operation": "OTHER",
                "consequential": True,
                "dependency": "sequence",
                "status": "pending",
                "supported": False,
                "target_id": "",
                "label": clause.get("text") or "",
            })
    clear = _should_clear_interlocutor(session, [], "MOVE")
    decision = _compound_clarification(
        text, steps, scene=scene, clear=clear, incidental=[], world=world,
    )
    message = decision.player_facing_text or ""
    if "Nothing has been attempted" not in message:
        decision = replace(decision, player_facing_text=message.rstrip() + " Nothing has been attempted.")
    return decision


def full_request_admission(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
) -> ConversationalDecision | None:
    assessment = compound_action_assessment(text, scene=scene)
    coverage = assessment.get("coverage") if isinstance(assessment.get("coverage"), Mapping) else actionable_coverage(text, scene=scene)
    withheld = _uncommitted_act_admission(
        text, coverage, scene=scene, world=world, session=session,
    )
    if withheld is not None:
        return withheld
    # A model or deterministic owner may already have named one destination.
    # The complete player wording still has to leave that choice unresolved.
    alternatives = _destination_alternative_admission(text, scene=scene)
    if alternatives is not None:
        return alternatives
    from game.interaction_completion import corrected_dialogue, npc_correction_prefix
    from game.ordinary_semantic_ownership import corrected_dialogue_target

    if prefix := npc_correction_prefix(text):
        nominal, remainder = prefix
        if not remainder and corrected_dialogue_target(
            None, scene=scene, world=world, session=session, nominal_only=nominal,
        ):
            return _nonaction_decision(text, modality="informational", reason="npc_correction_only",
                                       message="What would you like to ask or do? Nothing has been attempted.")
        correction = corrected_dialogue(text) if remainder else None
        if correction and corrected_dialogue_target(correction, scene=scene, world=world, session=session):
            # The frame accounts for the clarification and any verified
            # attention gesture. The original speech still needs admission.
            return full_request_admission(correction[2], scene=scene, world=world, session=session)
        if remainder and (correction or corrected_dialogue_target(
            None, scene=scene, world=world, session=session, nominal_only=nominal,
        )):
            return _nonaction_decision(
                text, modality="informational", reason="unresolved_npc_correction",
                message=("Who are you addressing? Nothing has been attempted." if correction
                         else "Which single action do you want to take now? Nothing has been attempted."),
            )
    if coverage.get("classification") in {"UNCERTAIN", "INCOMPLETE"}:
        from game.interaction_completion import dialogue_attention
        from game.ordinary_semantic_ownership import dialogue_attention_target

        attention = dialogue_attention(text)
        if attention and dialogue_attention_target(attention, scene=scene, world=world, session=session):
            # Reapply the full gate to the remaining speech. This accounts for
            # the manner phrase only. Model components still need admission.
            return full_request_admission(attention[2], scene=scene, world=world, session=session)
    if coverage.get("classification") == "UNCERTAIN" and _grounded_inspection_posture(
        text, scene=scene, world=world, session=session,
    ):
        # The full request names one examination and a grounded manner phrase.
        # This lift of the coverage veto supplies no execution authority.
        return None
    question = bool(_QUESTION_START_RE.search(text) or "?" in text)
    alternatives = bool(_ALTERNATIVE_RE.search(text))
    deferred = _request_is_deferred(text)
    # Incomplete or uncertain coverage withholds every candidate. A question,
    # alternative, or deferred form is nonexecution even when one verb is recognizable.
    # A request the existing local-action owner already accounts for is not withheld.
    coordinated = _coordinated_elided_admission(
        text, coverage, scene=scene, world=world, session=session,
    )
    if coordinated is not None:
        return coordinated
    local_accounts = (
        coverage.get("classification") in {"INCOMPLETE", "UNCERTAIN"}
        and _local_owner_accounts_for_request(text, scene=scene, world=world, session=session)
    )
    if not local_accounts and (
        coverage.get("classification") in {"INCOMPLETE", "UNCERTAIN"} or (
        coverage.get("classification") == "NON_EXECUTION" and (alternatives or deferred or (
            question and any(_clause_has_verb(part) for part in _split_clauses(text)) and
            re.match(r"\s*(?:can|could|would|should|what\s+happens\s+if|is\s+it|would\s+it)\b", text, re.I)
        ))
    )):
        return _coverage_refusal(text, coverage, assessment)
    if not (assessment["unsupported_compound"] or alternatives or deferred or (
        question and any(_clause_has_verb(c) for c in _split_clauses(text)) and
        re.match(r"\s*(?:can|could|would|should|what\s+happens\s+if)\b", text, re.I)
    )):
        return None
    return _coverage_refusal(text, coverage, assessment)


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
    from game.conversational_continuity import conversational_topic_return, span_abandons_intention

    if span_abandons_intention(text) or conversational_topic_return(text):
        return {
            "text": text, "operation": "", "destination": "",
            "consequential": False, "incidental": False, "back": False,
        }
    movement, purpose = _movement_and_purpose(text)
    if purpose and (_MOVE_CUE_RE.search(movement) or _BARE_MOVE_RE.search(movement)):
        return {**_analyze_clause(movement, exits), "text": text, "purpose": purpose}
    destination = _destination_phrase(text)
    if _ASK_CUE_RE.search(text) and _MOVE_CUE_RE.search(text):
        # Travel vocabulary can be the content of speech. The deterministic
        # shortcut cannot settle that scope; leave it to semantic interpretation.
        return {"text": text, "operation": "", "destination": "", "consequential": False, "incidental": False, "back": False}
    incidental = False
    operation = ""
    consequential = False
    if _marking_clause(text):
        operation = "OTHER"
        consequential = True
    elif _WATCH_RE.search(text) and not destination:
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
    elif re.search(r"\benter(?:s|ing)?\b", text, re.IGNORECASE):
        from game.scene_destination_binding import resolve_authored_exit_from_player_travel

        if resolve_authored_exit_from_player_travel(text, exits):
            operation = "MOVE"
            consequential = True
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


def _transient_local_decision(player_text: str, outcome: Mapping[str, Any]) -> ConversationalDecision:
    """Publish an already authorized transient approach or contact."""
    status = str(outcome.get("status") or "")
    if status == "completed":
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER,
            primary_intention=player_text,
            intent_family="local_interaction",
            context_references=[str(outcome.get("target_id") or "")],
            proposed_target=str(outcome.get("target_id") or "") or None,
            reason="transient_local_action_completed",
            confidence=0.9,
            player_facing_text=str(outcome.get("player_facing_text") or ""),
            intent_modality="committed",
            execution_policy="record_transient_outcome",
            authorization={"transient_local_action": dict(outcome)},
        )
    category = (
        ConversationalDecisionCategory.CLARIFY
        if outcome.get("category") == "clarify"
        else ConversationalDecisionCategory.DECLINE
    )
    return ConversationalDecision(
        category=category,
        primary_intention=player_text,
        intent_family="local_interaction",
        reason=str(outcome.get("reason") or "local_action_refused"),
        confidence=0.84,
        player_facing_text=str(outcome.get("player_facing_text") or ""),
        intent_modality="committed",
        execution_policy="decline_unadjudicated_contact" if category == ConversationalDecisionCategory.DECLINE else "clarify_before_execution",
        authorization={"transient_local_action": dict(outcome)},
    )


def _local_presence_decision(
    player_text: str,
    hits: list[tuple[str, Mapping[str, Any]]],
    *,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
) -> ConversationalDecision:
    """A current-scene object is not an unestablished journey.

    Eligible approach or contact is a transient outcome from the local
    interaction owner. Anything outside that class stays unadjudicated.
    The scene, position, and inventory are left unchanged, and no clue is
    revealed by the approach.
    """
    if len(hits) == 1:
        from game.local_interaction import resolve_transient_local_action

        outcome = resolve_transient_local_action(
            player_text, scene=scene, world=world, session=session,
        )
        if isinstance(outcome, dict):
            return _transient_local_decision(player_text, outcome)
        entity_id, info = hits[0]
        row = info.get("row") if isinstance(info.get("row"), Mapping) else None
        label = _label(row, entity_id)
        return ConversationalDecision(
            category=ConversationalDecisionCategory.DECLINE,
            primary_intention=player_text,
            intent_family="local_interaction",
            context_references=[entity_id],
            reason="local_object_not_a_destination",
            confidence=0.86,
            player_facing_text=(
                f"{label} is here. Approaching or touching it is not a supported action, "
                "and you have not moved."
            ),
            intent_modality="committed",
            execution_policy="decline_unadjudicated_contact",
        )
    labels = []
    for entity_id, info in hits[:4]:
        row = info.get("row") if isinstance(info.get("row"), Mapping) else None
        labels.append(_label(row, entity_id))
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=player_text,
        intent_family="local_interaction",
        reason="ambiguous_local_object",
        confidence=0.8,
        player_facing_text=(
            "More than one thing here could match. Do you mean "
            + " or ".join(labels)
            + "? You have not moved."
        ),
        intent_modality="committed",
        execution_policy="clarify_before_execution",
    )


def _names_known_scene_without_exit(phrase: str, exits: list[dict[str, Any]]) -> bool:
    """True when the phrase names one authored scene that is not an exit from here.

    The check uses scene ids only. It does not describe hidden rooms or routes.
    """
    from game.storage import list_scene_ids

    words = {word for word in _norm_place(phrase).split() if len(word) >= 5}
    if not words:
        return False
    targets = {
        _clean_text(row.get("target_scene_id") or row.get("targetSceneId"))
        for row in exits
    }
    hits: list[tuple[str, set[str]]] = []
    for scene_id in list_scene_ids():
        if scene_id in targets:
            continue
        scene_words = {
            word for word in _norm_place(scene_id.replace("_", " ")).split() if len(word) >= 5
        }
        if scene_words and scene_words <= words:
            hits.append((scene_id, scene_words))
    # A shorter id such as "market" is contained by "market quarter".
    # Keep only the most specific ids so one authored place is not ambiguous.
    specific = [
        scene_id
        for scene_id, scene_words in hits
        if not any(scene_words < other_words for _other, other_words in hits)
    ]
    return len(set(specific)) == 1


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


def _authored_pursuit_row(
    player_text: str,
    exits: list[dict[str, Any]],
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """One authored exit from the existing pursuit matcher. No new route."""
    from game.intent_parser import _match_follow_pursuit_exit, looks_like_explicit_leave_or_pursuit_intent

    if not looks_like_explicit_leave_or_pursuit_intent(player_text):
        return None
    inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
    target = _match_follow_pursuit_exit(
        player_text,
        exits,
        scene=inner if isinstance(inner, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    if not target:
        return None
    hits = [
        row for row in exits
        if str(row.get("target_scene_id") or row.get("targetSceneId") or "").strip() == target
    ]
    return hits[0] if len(hits) == 1 else None


def _move_along_pursuit(
    row: dict[str, Any],
    *,
    player_text: str,
    summary: str,
    incidental: list[str],
    session: Mapping[str, Any] | None,
) -> ConversationalDecision:
    label = _label(row, _clean_text(row.get("id")))
    return _move_decision_for_row(
        row,
        player_text=player_text,
        summary=summary or f"Go to {label}.",
        incidental=incidental,
        session=session,
    )


def _resolve_move_target(
    *,
    player_text: str,
    destination: str,
    back: bool,
    exits: list[dict[str, Any]],
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None,
    incidental: list[str],
    summary: str,
) -> ConversationalDecision | None:
    clear = _should_clear_interlocutor(session, incidental, "MOVE")
    pursuit_row = _authored_pursuit_row(player_text, exits, scene, session)
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
        if pursuit_row is not None:
            return _move_along_pursuit(
                pursuit_row, player_text=player_text, summary=summary,
                incidental=incidental, session=session,
            )
        local = _ground_catalog_target(
            destination,
            _catalog(scene, world),
            {"npc", "inspect_target", "perceive_target"},
        )
        if local:
            return _local_presence_decision(
                player_text, local, scene=scene, world=world, session=session,
            )
        if _names_known_scene_without_exit(destination, exits):
            return ConversationalDecision(
                category=ConversationalDecisionCategory.DECLINE,
                primary_intention=player_text,
                intent_family="movement",
                reason="known_destination_not_reachable",
                confidence=0.82,
                player_facing_text=(
                    "That destination is not an established place you can enter from here. "
                    "You stay where you are."
                ),
                intent_modality="committed",
                execution_policy="decline_unauthorized_route",
                context_update=_context_update(clear_interlocutor=clear) if clear else None,
            )
        return _unknown_destination(player_text, destination, clear=clear)
    if pursuit_row is not None:
        return _move_along_pursuit(
            pursuit_row, player_text=player_text, summary=summary,
            incidental=incidental, session=session,
        )
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
    log: list | None = None,
    character: Mapping[str, Any] | None = None,
) -> ConversationalDecision | None:
    text = _clean_text(player_text)
    exits = _exit_rows(scene)
    if re.fullmatch(r"(?:what|which)\s+(?:routes|exits|ways)\s+(?:can\s+(?:i|we)\s+take|are\s+(?:available|open))(?:\s+from\s+here)?[.?]?", text, re.I):
        from game.route_authority import route_status
        labels = [
            _label(row, str(row.get("id") or "")) + (
                " (not currently available)" if route_status(row, _scene_id(scene), dict(session or {}), dict(world or {})) != "available" else ""
            ) for row in exits
        ]
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER,
            primary_intention=text, intent_family="movement_question",
            reason="available_authored_routes", disposition="GROUNDED_INFORMATION",
            player_facing_text=("Established routes from here: " + ", ".join(labels) + ". You have not moved.")
                if labels else "No route from here is established in the current scene. You have not moved.",
            context_references=["active_scene_exits"], execution_policy="answer_only",
        )
    if _HYPOTHETICAL_RE.search(text):
        return _nonaction_decision(
            text,
            modality="hypothetical",
            reason="hypothetical_action",
            message="I can't say what would happen for certain, and nothing has been attempted.",
        )
    if _STAY_RE.search(text) and not re.search(r"\bbut\s+i\s+(?:go|head|walk|leave|travel|enter)\b", text, re.IGNORECASE):
        return _nonaction_decision(
            text,
            modality="planning",
            reason="explicit_stay",
            message="You stay where you are. Nothing has been attempted.",
        )
    from game.intent_parser import _explicit_stay_or_travel_negation

    if _explicit_stay_or_travel_negation(text) and not re.search(
        r"\bbut\s+(?:i\s+)?(?:go|head|walk|leave|travel|enter|inspect|examine|read|ask|tell)\b", text, re.IGNORECASE
    ):
        later = [
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+", text)
            if part.strip() and re.search(r"\b(?:ask|tell\s+me|what|who)\b", part, re.IGNORECASE)
            and not _explicit_stay_or_travel_negation(part)
        ]
        # "I won't enter. Tell me about the patrol." keeps the question.
        if later:
            return deterministic_conversational_decision(
                player_text=later[-1], scene=scene, world=world, session=session, log=log, character=character,
            )
        kept = actionable_coverage(text, scene=scene)
        selected = kept.get("selected_operation") or {}
        # A negated move does not cancel a later affirmative inspection.
        if not (kept.get("classification") == "COMPLETE" and selected.get("operation") in {"ASK", "INSPECT"}):
            return _nonaction_decision(
                text,
                modality="planning",
                reason="negated_travel",
                message="You stay where you are. Nothing has been attempted.",
            )
    if re.match(r"\s*if\b", text, re.IGNORECASE) and re.search(
        r"\b(?:enter|go|head|take|follow|leave|travel|exit|ask|tell)\b", text, re.IGNORECASE
    ):
        return _nonaction_decision(
            text,
            modality="hypothetical",
            reason="conditional_travel",
            message="Nothing has been attempted. That travel is only conditional.",
        )
    if re.search(
        r"\bi\s+plan\s+to\s+(?:travel|go|head|enter|leave|follow|take|exit)\b",
        text,
        re.IGNORECASE,
    ) or re.search(
        r"\bafter\s+(?:speaking|talking|meeting)\b.{0,80}\b(?:take|go|head|enter|follow|leave|travel)\b",
        text,
        re.IGNORECASE,
    ):
        return _nonaction_decision(
            text,
            modality="planning",
            reason="deferred_travel",
            message="Nothing has been attempted. That travel is not happening now.",
        )
    if re.match(r"^\s*i\s+(?:remember|recall)\b", text, re.IGNORECASE) and not _MOVE_CUE_RE.search(text):
        return _nonaction_decision(
            text,
            modality="planning",
            reason="recalled_context_not_action",
            message="You stay where you are. Nothing has been attempted.",
        )
    if (
        _TENTATIVE_RE.search(text)
        and not re.search(r"\bbut\s+i\s+(?:go|head|walk|leave|travel)\b", text, re.IGNORECASE)
        and not _committed_move_with_trailing_thought(text)
    ):
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
        # A fronted adjunct can contain "is" and a place name while the main
        # clause is still one complete travel request. Do not discard that.
        covered = actionable_coverage(text, scene=scene)
        travel_complete = covered["classification"] == "COMPLETE" and any(
            span.get("affirmative") and span.get("operation") == "MOVE" for span in covered["spans"]
        )
        if not travel_complete:
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
        if not matches:
            from game.scene_destination_binding import resolve_authored_exit_from_player_travel

            target = resolve_authored_exit_from_player_travel(text, exits)
            matches = [
                row for row in exits
                if target and str(row.get("target_scene_id") or row.get("targetSceneId") or "").strip() == target
            ]
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


def _purpose_movement_decision(
    text: str, movement: str, purpose: str, *, exits: list[dict[str, Any]],
    scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision:
    from game.route_authority import route_status
    from game.scene_destination_binding import destination_phrase_respecting_purpose_tail

    destination = destination_phrase_respecting_purpose_tail(_destination_phrase(movement), exits)
    inspection = bool(_INSPECT_CUE_RE.match(purpose))
    step = {"text": purpose, "operation": "INSPECT" if inspection else "OTHER",
            "status": "pending", "dependency": "after_travel", "supported": False,
            "target_id": "", "consequential": True}
    deferred = {"kind": "deferred_intentions", "original_text": text,
                "scene_id": _scene_id(scene), "steps": [step]}
    available = [r for r in exits if route_status(r, _scene_id(scene), dict(session or {}), dict(world or {})) == "available"]
    matches = _matching_exits(destination, exits) if destination else []
    references = []
    target = _norm_place(_object_phrase(purpose)) if inspection else ""
    # A literal reference to known information is only explanation context.
    # It is never an alias for a physical target or an exit.
    for clue_id, entry in ((session or {}).get("clue_knowledge") or {}).items():
        if (target and isinstance(entry, Mapping) and entry.get("state") in {"discovered", "inferred"}
                and re.search(rf"\b{re.escape(target)}\b", _norm_place(str(entry.get("text") or "")))):
            references.append(str(clue_id))
    clear = _should_clear_interlocutor(session, [], "MOVE")
    if len(matches) == 1 and matches[0] in available:
        decision = _move_decision_for_row(
            matches[0], player_text=text, summary=f"Go to {_label(matches[0], '')}.",
            incidental=[], session=session, secondary=[step], pending=deferred,
        )
        outcome = "UNIQUE_AUTHORIZED_ROUTE"
    elif matches and not any(r in available for r in matches):
        decision = ConversationalDecision(
            category=ConversationalDecisionCategory.DECLINE, primary_intention=text,
            intent_family="movement", reason="route_requires_prerequisite",
            player_facing_text="That route cannot be used right now. You stay where you are; your intended follow-up has not been attempted.",
            context_update=_context_update(pending=deferred, pending_set=True),
        )
        outcome = "ROUTE_REQUIRES_PREREQUISITE"
    else:
        choices = [r for r in matches if r in available] if matches else (available if references else [])
        if choices:
            decision = _ambiguous_destination(text, choices, scene=scene, clear=clear)
            pending = decision.context_update["conversational_context"]["pending_clarification"]
            pending["deferred_steps"] = [step]
            message = ("I cannot establish which route reaches the place you mean. Available routes: "
                       + "; ".join(_label(r, "") for r in choices[:4])
                       + f". Which route do you want to take? Your intention to {purpose} is still pending; nothing has been attempted.")
            decision = replace(decision, reason="clue_route_clarification" if not matches else "ambiguous_movement_destination",
                               player_facing_text=message)
            outcome = "MULTIPLE_AUTHORIZED_ROUTES" if matches else "NO_AUTHORIZED_ROUTE"
        else:
            decision = replace(_unknown_destination(text, destination, clear=clear),
                               context_update=_context_update(pending=deferred, pending_set=True, clear_interlocutor=clear))
            outcome = "UNSUPPORTED_REFERENCE" if not references else "NO_AUTHORIZED_ROUTE"
    return replace(decision, secondary_intentions=[step], context_references=references,
                   authorization={"route_decision": outcome, "requested_destination": destination,
                                  "purpose": purpose, "referenced_clues": references,
                                  "selection_evidence": "explicit_destination" if matches else "no_authored_clue_route_link"})


_TRAVEL_FILLER = frozenset({
    "want", "wants", "wanted", "like", "need", "needs", "going", "gonna",
    "connected", "connection", "trail", "path", "route", "road", "track",
    "lead", "follow", "follows", "following", "pursue", "pursues", "pursuing",
    "way", "toward", "towards", "missing",
})


def _follow_overlap_rows(text: str, exits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows whose authored label is contained, or shares two distinctive tokens.

    This is the existing pursuit overlap rule. It does not create labels.
    """
    from game.intent_parser import (
        _PURSUIT_OBJECT_HINTS,
        _RE_FOLLOW_UP_PHRASAL,
        _content_tokens,
        _explicit_stay_or_travel_negation,
    )

    raw = _clean_text(text)
    if not raw or not exits or _RE_FOLLOW_UP_PHRASAL.search(raw) or _explicit_stay_or_travel_negation(raw):
        return []
    from game.scene_destination_binding import affirmative_travel_selection_allowed

    if not affirmative_travel_selection_allowed(raw):
        return []
    if "?" in raw or _QUESTION_START_RE.search(raw):
        return []
    player_tokens = set(_content_tokens(raw))
    pursuit = bool(player_tokens & _PURSUIT_OBJECT_HINTS or re.search(r"\b(?:follow|pursue)\b", raw, re.IGNORECASE))
    lowered = raw.casefold()
    contained: list[dict[str, Any]] = []
    overlapped: list[dict[str, Any]] = []
    for row in exits:
        label = _clean_text(row.get("label"))
        if not label or not _clean_text(row.get("target_scene_id") or row.get("targetSceneId")):
            continue
        if label.casefold() in lowered:
            contained.append(row)
            continue
        overlap = (player_tokens & set(_content_tokens(label))) - {"follow", "pursue", "go", "head"}
        if pursuit and len(overlap) >= 2:
            overlapped.append(row)
    # A fully contained label is the existing explicit match. A weaker overlap
    # on a different exit does not make that explicit label ambiguous.
    if contained:
        return _unique_exit_rows(contained)
    return _unique_exit_rows(overlapped)


def authored_travel_admission(
    player_text: str,
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """Select one authored exit, or refuse an unsupported destination.

    A method, companion, or walking style is not required. A blocked row is
    still selected so route authority can explain the block. No new exit is made.
    An unresolved destination alternative is not a route, and a supported
    correction names only its final destination.
    """
    text = _clean_text(player_text)
    from game.scene_destination_binding import classify_destination_choice

    exits = _exit_rows(scene)
    choice = classify_destination_choice(text, exits)
    if choice.get("kind") == "unresolved":
        return _destination_choice_decision(text, choice, exits, scene)
    if choice.get("kind") == "correction" and len(choice.get("exit_ids") or []) == 1:
        from game.route_authority import route_status

        visible = [
            row for row in exits
            if route_status(row, _scene_id(scene), dict(session or {}), dict(world or {})) != "hidden"
        ]
        row = next((item for item in visible if _clean_text(item.get("id")) == choice["exit_ids"][0]), None)
        if row is not None:
            label = _label(row, _clean_text(row.get("id")))
            return _move_decision_for_row(
                row, player_text=text, summary=f"Go to {label}.", incidental=[], session=session,
            )
    if not text or not _AGENT_RE.search(text) or "?" in text or _QUESTION_START_RE.search(text):
        return None
    # Singleton exit selection cannot commit when the request still contains
    # another affirmative command, or when the request is not an execution.
    if actionable_coverage(text, scene=scene)["classification"] != "COMPLETE":
        return None
    if _movement_and_purpose(text)[1]:
        return None
    from game.intent_parser import _PURSUIT_OBJECT_HINTS, _content_tokens
    from game.route_authority import route_status

    exits = [
        row for row in _exit_rows(scene)
        if route_status(row, _scene_id(scene), dict(session or {}), dict(world or {})) != "hidden"
    ]
    rows = _follow_overlap_rows(text, exits)
    clear = _should_clear_interlocutor(session, [], "MOVE")
    if len(rows) > 1:
        return _ambiguous_destination(text, rows, scene=scene, clear=clear)
    if len(rows) == 1:
        label = _label(rows[0], _clean_text(rows[0].get("id")))
        return _move_decision_for_row(
            rows[0],
            player_text=text,
            summary=f"Go to {label}.",
            incidental=[],
            session=session,
        )
    from game.scene_destination_binding import resolve_authored_exit_from_player_travel

    bound_target = resolve_authored_exit_from_player_travel(text, exits)
    bound = [
        row for row in exits
        if bound_target and str(row.get("target_scene_id") or row.get("targetSceneId") or "").strip() == bound_target
    ]
    if len(bound) > 1:
        return _ambiguous_destination(text, bound, scene=scene, clear=clear)
    if len(bound) == 1:
        label = _label(bound[0], _clean_text(bound[0].get("id")))
        return _move_decision_for_row(
            bound[0],
            player_text=text,
            summary=f"Go to {label}.",
            incidental=[],
            session=session,
        )
    if not re.search(r"\b(?:follow|pursue)\b", text, re.IGNORECASE):
        return None
    tokens = set(_content_tokens(text))
    if not (tokens & _PURSUIT_OBJECT_HINTS):
        return None
    destination = _destination_phrase(text)
    if destination and _ground_catalog_target(
        destination, _catalog(scene, world), {"npc", "inspect_target", "perceive_target"}
    ):
        return None
    label_tokens: set[str] = set()
    for row in exits:
        label_tokens.update(_content_tokens(_clean_text(row.get("label"))))
    unmatched = tokens - _TRAVEL_FILLER - label_tokens - {"follow", "pursue", "go", "head", "want"}
    if not unmatched:
        return None
    return _unknown_destination(text, destination or text, clear=clear)


def unavailable_referent_decision(
    player_text: str,
    record: Mapping[str, Any] | None,
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """Say when an inspection names nothing in the scene. Do not invent it."""
    text = _clean_text(player_text)
    if not text or not isinstance(record, Mapping) or not _INSPECT_CUE_RE.search(text):
        return None
    references = record.get("references") if isinstance(record.get("references"), Mapping) else {}
    phrases = []
    for item in references.get("unresolved_references") or []:
        phrase = _clean_text(item)
        if phrase and phrase.casefold() in text.casefold():
            phrases.append(phrase)
    if not phrases:
        extracted = _object_phrase(text)
        if extracted:
            phrases.append(extracted)
    if not phrases:
        return None
    catalog = _catalog(scene, world)
    exits = _exit_rows(scene)
    for phrase in phrases:
        if _ground_catalog_target(phrase, catalog, {"npc", "inspect_target", "perceive_target"}):
            return None
        if _matching_exits(phrase, exits):
            return None
    shown = phrases[0]
    return ConversationalDecision(
        category=ConversationalDecisionCategory.DECLINE,
        primary_intention=text,
        intent_family="investigation",
        reason="referent_not_in_scene",
        confidence=0.84,
        player_facing_text=f"Nothing here matches {shown}. Nothing has been attempted.",
        intent_modality="committed",
        execution_policy="decline_unauthorized_referent",
    )


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
    from game.interaction_completion import dialogue_attention
    from game.ordinary_semantic_ownership import dialogue_attention_target

    attention = dialogue_attention(text)
    if attention and dialogue_attention_target(attention, scene=scene, world=world, session=session):
        return None
    exits = _exit_rows(scene)
    from game.route_authority import route_status
    exits = [row for row in exits if route_status(row, _scene_id(scene), dict(session or {}), dict(world or {})) != "hidden"]
    movement, purpose = _movement_and_purpose(text)
    if not purpose:
        admitted = authored_travel_admission(
            text, scene=scene, world=world, session=session,
        )
        if admitted is not None:
            return admitted
    if purpose and (_MOVE_CUE_RE.search(movement) or _BARE_MOVE_RE.search(movement)):
        # Same-scene approach binding remains owned by PR-PLAY-23's bridge.
        if _ground_catalog_target(_destination_phrase(movement), _catalog(scene, world), {"npc", "inspect_target", "perceive_target"}):
            return None
        return _purpose_movement_decision(
            text, movement, purpose, exits=exits, scene=scene, world=world, session=session,
        )
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
            world=world,
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
        world=world,
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
    if _movement_and_purpose(text)[1]:
        return restored
    if (_MOVE_CUE_RE.search(text) or _BACK_RE.search(text)) and _destination_phrase(text):
        return text
    return restored


def _elided_consequential_text(text: str) -> bool:
    return bool(_ELIDED_CONSEQUENTIAL_RE.match(_clean_text(text)))


def _select_compound_step(player_text: str, steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    if _YES_RE.match(player_text):
        return steps[0] if steps else None
    for step in steps:
        label = _clean_text(step.get("label") or step.get("text"))
        if step.get("supported") and label and _place_match(player_text, label):
            return step
    moves = [
        step for step in steps
        if step.get("supported") and str(step.get("operation") or "").upper() == "MOVE"
    ]
    if len(moves) != 1 or _ELIDED_CONSEQUENTIAL_RE.search(player_text):
        return None
    # "Just travel there first" and "Only go to the trail" select the withheld
    # move. A different named place is left for the single-route check below.
    text = re.sub(
        r"^(?:actually|just|only|simply)[,.]?\s*", "", _clean_text(player_text), count=1, flags=re.I,
    )
    if not re.search(r"\b(?:go|head|walk|travel|leave|return|set\s+off|there|trail)\b", text, re.I):
        return None
    destination = _destination_phrase(text) or _destination_phrase(player_text)
    label = _clean_text(moves[0].get("label") or moves[0].get("text"))
    filler = {"there", "here", "first", "now", "just", "please", "only", "simply"}
    tokens = set(_norm_place(destination).split()) - filler if destination else set()
    if tokens and label and not (
        _place_match(destination, label) or _place_match(text, label) or _place_match(player_text, label)
    ):
        return None
    if not re.search(r"\b(?:just|only|simply|there|first|trail|go|head|walk|travel|leave|return)\b", player_text, re.I):
        return None
    return moves[0]


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
            named = _single_followup_exit(player_text, exits)
            if named is not None:
                label = _label(named, _clean_text(named.get("id")))
                return _move_decision_for_row(
                    named, player_text=player_text, summary=f"Go to {label}.",
                    incidental=[], session=session,
                )
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
        remaining = [
            step for step in steps
            if step is not selected and not _elided_consequential_text(str(step.get("text") or ""))
        ]
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
        remaining = list(pending.get("deferred_steps") or [])
        remainder = {"kind": "deferred_intentions", "steps": remaining,
                     "original_text": pending.get("original_text"), "scene_id": _scene_id(scene)} if remaining else None
        return _move_decision_for_row(
            matches[0],
            player_text=_clean_text(pending.get("original_text")) or player_text,
            summary=f"Go to {_label(matches[0], _clean_text(matches[0].get('id')))}.",
            incidental=[],
            session=session,
            secondary=remaining,
            pending=remainder,
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


def _inventory_reference_matches(subject, character, *, target_id=None, instance_id=None):
    """Current sheet identities; authored aliases and bounded noun suffixes only."""
    from game.marking_action import _names, _norm
    from game.player_http_projection import project, CHARACTER

    phrase = _norm(subject.replace('_', ' '))
    raw = (character or {}).get('inventory') or []
    hits = []
    for index, row in enumerate(raw):
        if not isinstance(row, Mapping):
            continue
        public = project({'inventory': [row]}, CHARACTER).get('inventory', [])
        if not public or not public[0].get('id') or not public[0].get('name'):
            continue
        if target_id:
            matched = row.get('id') == target_id and (not instance_id or row.get('instance_id') == instance_id)
        else:
            from game.referenced_surface import reference_compatible

            names = _names(row, 'name', 'id')
            matched = any(reference_compatible(phrase, name) for name in names)
        if matched:
            hits.append((index, row))
    return hits


def _scene_object_reference_matches(subject, scene):
    """Visible interactables compatible with the reference. Not every fact."""
    from game.referenced_surface import reference_compatible

    inner = scene.get('scene') if isinstance(scene, Mapping) and isinstance(scene.get('scene'), dict) else scene
    if not isinstance(inner, Mapping):
        return []
    hits = []
    seen = set()
    for item in inner.get('interactables') or []:
        if not isinstance(item, Mapping) or item.get('hidden') is True or item.get('visible') is False or item.get('accessible') is False:
            continue
        iid = str(item.get('id') or '').strip()
        if not iid or iid in seen:
            continue
        labels = [iid.replace('_', ' '), str(item.get('label') or ''), str(item.get('name') or '')]
        aliases = item.get('aliases')
        if isinstance(aliases, list):
            labels.extend(alias for alias in aliases if isinstance(alias, str))
        if any(label.strip() and reference_compatible(subject, label) for label in labels):
            seen.add(iid)
            hits.append(item)
    return hits


def _grounded_reading_target(nominal, *, scene, world, session):
    """Resolve an explicit reading target to one current public interactable."""
    from game.local_interaction import _row_veto, _surface_authority

    current = _scene_obj(scene)
    scene_id = current.get("id")
    if not scene_id or (session or {}).get("active_scene_id", scene_id) != scene_id:
        return None
    matches = _scene_object_reference_matches(nominal, scene)
    if len(matches) != 1:
        return None
    row, = matches
    target_id = row["id"]
    alias = next((name.replace("_", " ") for name in _aliases(row, target_id)
                  if _norm_place(name.replace("_", " ")) == _norm_place(nominal)), None)
    catalog_entry = _catalog(scene, world).get(target_id, {})
    if (not alias or catalog_entry.get("kind") not in {"inspect_target", "perceive_target"}
            or sum(isinstance(item, Mapping) and item.get("id") == target_id
                   for item in current.get("interactables") or []) != 1
            or _row_veto(row) == "access" or row.get("gm_only") or row.get("public") is False
            or not _surface_authority(scene, target_id, alias)):
        return None
    return target_id, alias


GROUNDED_READING_AUTHORITY = "explicit_reading_and_unique_visible_target"


def _with_grounded_reading(record, text, target_id, alias):
    return {
        **record,
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "INTERPRETED",
        "communication": {**(record.get("communication") or {}), "recipient": "CHARACTER", "purpose": "ACTION"},
        "clarification_question": "",
        "contract_consistency": {
            "status": "AUTHORITATIVELY_RESOLVABLE",
            "authority": GROUNDED_READING_AUTHORITY,
            "original_request": text,
            "original_communication": record.get("communication"),
            "target_id": target_id,
            "inspection_alias": alias,
        },
    }


def _posted_reading_decision(text, *, scene, world, session):
    """The posted text is the subject of reading. The named surface owns it."""
    match = re.fullmatch(r"(?:I|we) read (?:the )?posted (?P<topic>[\w -]+?) on (?P<target>[\w -]+)[.]?", text, re.I)
    if not match:
        return None
    grounded = _grounded_reading_target(match["target"], scene=scene, world=world, session=session)
    if not grounded:
        return None
    target_id, alias = grounded
    # Public evidence can establish which topic is posted without supplying its
    # contents. The existing resolver determines what the examination reveals.
    topic = " " + _norm_place(match["topic"]) + " "
    name = " " + _norm_place(alias) + " "
    facts = (" " + _norm_place(value) + " " for ref, value in public_conversation_evidence(scene, None).items()
             if ref.startswith("visible:"))
    if not any(topic in fact and name in fact for fact in facts):
        return None
    record = _operation_record(operation="INSPECT", target_id=target_id, player_text=text)
    return ConversationalDecision(
        category=ConversationalDecisionCategory.EXECUTE,
        primary_intention=text, intent_family="world_operation",
        proposed_operation="INSPECT", proposed_target=target_id,
        proposed_record=_with_grounded_reading(record, text, target_id, alias),
        requires_authoritative_execution=True, reason="grounded_posted_reading",
        context_update=_context_update_clear_pending(),
    )


def settled_reading_decision(text, resolution, *, session, target_id, scene_id):
    """Report a settled reading when a subsequent request repeats its result."""
    prior = _conversation_context(session).get("last_executed_intention") or {}
    if (not isinstance(prior, Mapping) or prior.get("authority") != GROUNDED_READING_AUTHORITY
            or prior.get("target") != target_id or prior.get("scene_id") != scene_id
            or resolution.get("kind") != "already_searched" or resolution.get("success") is not False
            or resolution.get("interactable_id") != target_id or re.search(r"\bagain\b", text, re.I)):
        return None
    recalled = (resolution.get("metadata") or {}).get("recalled_facts") or []
    if not recalled:
        return None
    return ConversationalDecision(
        category=ConversationalDecisionCategory.ANSWER,
        primary_intention=text, intent_family="world_operation",
        reason="reading_already_resolved", execution_policy="answer_only",
        player_facing_text="Previously disclosed here: " + " ".join(recalled) + " There is nothing new to add.",
        context_update=_context_update(pending=None, pending_set=True, intention=None, intention_set=True),
    )


def _object_choice_labels(matches, scene_objects):
    labels = []
    for _index, row in matches:
        name = str(row.get('name') or row.get('id') or '').strip()
        if name and name not in labels:
            labels.append(name)
    for item in scene_objects:
        label = str(item.get('label') or item.get('name') or str(item.get('id') or '').replace('_', ' ')).strip()
        if label and label not in labels:
            labels.append(label)
    return labels


def _which_object(labels):
    if not labels:
        return 'Which object do you mean? Specify the inventory item or the object in the scene.'
    if len(labels) == 1:
        shown = labels[0]
    elif len(labels) == 2:
        shown = f'{labels[0]}, or {labels[1]}'
    else:
        shown = ', '.join(labels[:-1]) + ', or ' + labels[-1]
    return f'Which object do you mean? {shown}.'


def _unmatched_object_decision(text, subject, scene, character, classified):
    """Withhold an object action whose target is not an established object.

    A shared word in a hidden sentence is not an object identity. The public
    sentence stays the existing nonconfirmation, and the turn is not spent.
    """
    from game.referenced_surface import AUTHORITY_UNSUPPORTED, render_referenced_surface_inspection_line

    authority = str((classified or {}).get('authority') or AUTHORITY_UNSUPPORTED)
    answer = render_referenced_surface_inspection_line({'authority': authority}, scene)
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=text, intent_family='inventory_inspection',
        reason='unresolved_object_reference', disposition='UNMATCHED',
        player_facing_text=answer, execution_policy='answer_only', intent_modality='informational',
        missing_information=['object_target'],
        authorization={'authority_provenance': 'player_http_projection.CHARACTER',
            'source': 'character.inventory', 'information_type': 'description',
            'information_disposition': 'UNMATCHED', 'reference_disposition': 'UNMATCHED',
            'subject': subject, 'subject_id': None, 'subject_instance_id': None,
            'scene_id': _scene_id(scene), 'character_id': str((character or {}).get('id') or ''),
            'inventory_candidates': [], 'scene_candidate': None, 'scene_candidates': [],
            'referenced_surface_authority': authority,
            'mutation_eligibility': False, 'turn_advancement': False},
    )


def inspection_action_admission(player_text, normalized_action, *, scene, world, character, reconciled_inspection_alias=None):
    """Ground a selected inspection before resolver or time authority is acquired.

    Coverage alone is not target admission. Carried-object answers have already
    had first refusal; this consumes the same surface classifier as exploration.
    """
    if str(normalized_action.get("type") or "").lower() != "investigate":
        return None
    from game.referenced_surface import classify_referenced_surface, extract_inspection_target

    subject = (
        reconciled_inspection_alias
        or extract_inspection_target(player_text)
        or str(normalized_action.get("target_id") or "")
    )
    matches = _scene_object_reference_matches(subject, scene)
    if len(matches) > 1:
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=player_text, intent_family="investigation",
            reason="ambiguous_inspection_target", missing_information=["object_target"],
            player_facing_text=_which_object(_object_choice_labels([], matches)),
            execution_policy="answer_only",
        )
    classified = classify_referenced_surface(player_text, scene, world=world, explicit_target=subject or None)
    mismatched_alias = reconciled_inspection_alias and classified.get("interactable_id") != normalized_action.get("target_id")
    if not mismatched_alias and classified.get("authority") not in {"unsupported", "authored_hidden", "authored_abstract_reference"}:
        return None
    decision = _unmatched_object_decision(player_text, subject, scene, character, classified)
    if (mismatched_alias or classified.get("authority") == "unsupported") and subject:
        decision = replace(decision, player_facing_text=(
            f"I cannot establish the requested inspection target ({subject}). "
            "Which established object or area do you mean? Nothing has been attempted."
        ))
    return replace(decision, authorization={
        **(decision.authorization or {}),
        "authority_provenance": "referenced_surface.classify_referenced_surface",
        "source": "scene",
        "original_text": player_text,
        "reference_admission": "withheld",
    })


def _recent_inventory_reference(log, scene, character):
    """Only the immediately preceding delivered decision may bind a pronoun."""
    latest = log[-1] if isinstance(log, list) and log else {}
    prior = ((latest.get('resolution') or {}).get('metadata') or {}).get('conversational_decision') or {}
    auth = prior.get('authorization') or {}
    if (prior.get('intent_family') in {'inventory_information', 'inventory_inspection'}
            and auth.get('information_disposition') in {'ANSWERABLE', 'ABSENT'}
            and auth.get('scene_id') == _scene_id(scene)
            and auth.get('character_id') == str((character or {}).get('id') or '')
            and auth.get('subject_id')):
        return auth
    return {}


def _inventory_inspection_decision(text, *, character, session, scene, world, log):
    """Bind a standalone information request; possession never grants observation."""
    import math
    from game.referenced_surface import classify_referenced_surface
    from game.marking_observation import recognize_observation

    # The dedicated marking path owns surface references and their disclosure.
    if recognize_observation(text) is not None:
        return None

    patterns = (
        (r'(?:(?:i|we)\s+)?(?:examine|inspect|look at)\s+(.+?)', 'description'),
        (r'tell me what i know about\s+(.+?)', 'description'),
        (r'what condition is\s+(.+?)\s+in', 'condition'),
        (r'what (?:color|colour|material) is\s+(.+?)', 'property'),
        (r'am i wearing\s+(.+?)', 'equipment'),
        (r'what is in\s+(.+?)', 'contents'),
        (r'what (?:writing|markings) (?:is|are) on\s+(.+?)', 'markings'),
        (r'what (?:is|about)\s+(.+?)', 'identity'),
    )
    match = None
    for pattern, kind in patterns:
        match = re.fullmatch(pattern + r'[?.]?', text, re.I)
        if match:
            break
    if not match:
        return None
    subject = match.group(1).strip(' .?')
    if re.search(r"\b(?:and|or|if|then|but|use|search|drop|tear|put)\b|[;!?]", subject, re.I):
        return None
    owned = bool(re.match(r'my\s', subject, re.I) or re.search(r'\s+in my pack$', subject, re.I))
    subject = re.sub(r'\s+in my pack$', '', subject, flags=re.I)
    if subject.casefold() not in {'this item', 'that item'}:
        subject = re.sub(r'^(?:my|the|a|an|this|that)\s+', '', subject, flags=re.I)
    subject = re.sub(r"['’]s pockets$", '', subject, flags=re.I)
    contextual = subject.casefold() in {'it', 'this', 'that', 'this item', 'that item'}
    prior = _recent_inventory_reference(log, scene, character) if contextual else {}
    if contextual and not prior and not log:
        # Initial scene-pronoun clarification already owns scene choices.
        return None
    if prior:
        subject = prior.get('subject') or subject
    matches = _inventory_reference_matches(subject, character,
        target_id=prior.get('subject_id'), instance_id=prior.get('subject_instance_id')) if (not contextual or prior) else []
    classified = {} if owned or contextual else classify_referenced_surface(text, scene, world=world, explicit_target=subject)
    scene_objects = [] if owned or contextual else _scene_object_reference_matches(subject, scene)
    scene_fact = classified.get('authority') in {'authored_interactable', 'authored_visible_feature'}
    scene_match = scene_fact or bool(scene_objects)
    # An explicit environmental qualifier never disappears during name matching.
    environmental = bool(re.search(r'\b(?:beside|near|by|outside|inside|at)\b', subject, re.I))
    if environmental and scene_match:
        return None
    # A unique visible scene object keeps its existing owner, including a
    # supported examination that is allowed to take the turn.
    if not owned and not contextual and not matches and len(scene_objects) == 1:
        return None
    if (
        not owned and not contextual and not matches and not scene_objects
        and classified.get('authority') not in {'unsupported', 'authored_hidden'}
    ):
        return None
    # Non-inspection identity questions outside inventory retain their current owner.
    if kind == 'identity' and not matches and not contextual and not owned and len(scene_objects) <= 1:
        return None
    if (
        not owned and not contextual and not matches and not scene_objects
        and classified.get('authority') in {'unsupported', 'authored_hidden'}
    ):
        return _unmatched_object_decision(text, subject, scene, character, classified)
    ambiguous = (
        len(matches) > 1 or len(scene_objects) > 1
        or (bool(matches) and scene_match and not owned and not contextual)
    )
    disposition = 'AMBIGUOUS' if ambiguous or (contextual and not prior) else 'UNKNOWN'
    row = None
    index = None
    observation = None
    if disposition == 'AMBIGUOUS':
        answer = _which_object(_object_choice_labels(matches, scene_objects))
    elif len(matches) == 1:
        index, row = matches[0]
        subject = row['name']
        quantity = row.get('quantity')
        if type(quantity) not in (int, float) or not math.isfinite(quantity) or quantity < 0:
            answer = f'I cannot establish whether you have {subject}: its inventory quantity is not established.'
        elif quantity == 0:
            disposition = 'ABSENT'
            answer = f'Your inventory records no {subject} (quantity zero). No inspection is established.'
        else:
            disposition = 'ANSWERABLE'
            answer = f'Your inventory records {subject}. '
            if kind in {'description', 'markings'}:
                from game.marking_observation import resolve_observation, project_observation
                resolved = resolve_observation({'target_phrase': row['id'], 'utterance': row['id'], 'pronoun': False},
                                               character, session or {})
                if resolved.get('outcome') == 'ready':
                    observed = project_observation(character, session or {}, resolved)
                    observation = observed.get('projection')
                    if any(p.get('knowledge') == 'known_present' for p in (observation or {}).get('properties', [])):
                        answer += observed['player_text'] + ' '
            limitation = {'condition': 'Its condition', 'property': 'That property',
                          'equipment': 'Whether it is worn', 'contents': 'Its pocket contents',
                          'identity': 'Further descriptive details', 'description': 'Further descriptive details',
                          'markings': 'Further markings'}[kind]
            answer += limitation + ' are not established by the available information.' if kind in {'contents', 'identity', 'description', 'markings'} else limitation + ' is not established by the available information.'
    else:
        answer = f'I cannot establish the intended inventory object ({subject}) from the current record. Please specify the item; no inspection is established.'
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY if disposition == 'AMBIGUOUS' else ConversationalDecisionCategory.ANSWER,
        primary_intention=text, intent_family='inventory_inspection', reason='player_sheet_inventory_reference',
        disposition=disposition, player_facing_text=answer, execution_policy='answer_only', intent_modality='informational',
        authorization={'authority_provenance': 'player_http_projection.CHARACTER', 'source': 'character.inventory',
            'source_index': index, 'information_type': kind, 'information_disposition': disposition,
            'reference_disposition': 'AMBIGUOUS' if disposition == 'AMBIGUOUS' else ('RESOLVED' if row is not None else 'UNMATCHED'),
            'subject': subject, 'subject_id': row.get('id') if row else None,
            'subject_instance_id': row.get('instance_id') if row else None,
            'scene_id': _scene_id(scene), 'character_id': str((character or {}).get('id') or ''),
            'contextual_reference': contextual, 'inventory_candidates': [
                {'source_index': i, 'id': r.get('id'), 'instance_id': r.get('instance_id')} for i, r in matches],
            'scene_candidate': classified.get('interactable_id') if scene_match and len(scene_objects) == 1 else None,
            'scene_candidates': [
                {'id': item.get('id'), 'label': item.get('label') or item.get('name')} for item in scene_objects],
            'inspection_authority': observation, 'mutation_eligibility': False,
            'turn_advancement': False},
    )


def _inventory_information_decision(
    text: str, *, character, session, scene, log,
) -> ConversationalDecision | None:
    """Answer sheet possession; membership grants no object observation.

    Match one standalone information request. Read only the existing player
    sheet allowlist. Follow-ups bind the latest published decision, never an
    older mention or NPC passage, and always re-read the current quantity.
    """
    import math

    match = re.fullmatch(
        r"(?:do i (?:still )?have|am i carrying)\s+(?:(?:my|a|an|the)\s+)?(?P<item>[\w '\-]+?)[?]?",
        text, re.I,
    )
    holding = bool(re.fullmatch(r"what am i holding[?]?", text, re.I))
    if not match and not holding:
        return None
    subject = _clean_text(match.group('item')) if match else 'items held in your hands'
    if re.search(r"\b(?:and|or|if|then|but)\b", subject, re.I):
        return None
    sid = _scene_id(scene)
    cid = str((character or {}).get('id') or '')
    disposition = 'UNKNOWN'
    category = ConversationalDecisionCategory.ANSWER
    source = 'character.inventory'
    index = None
    target_id = None
    instance_id = None
    if subject.casefold() in {'it', 'that', 'this', 'one'}:
        auth = _recent_inventory_reference(log, scene, character)
        if auth:
            target_id = auth['subject_id']
            instance_id = auth.get('subject_instance_id')
            subject = auth.get('subject') or subject
        else:
            disposition = 'AMBIGUOUS'
    raw_inventory = (character or {}).get('inventory')
    matches = _inventory_reference_matches(subject, character, target_id=target_id, instance_id=instance_id)
    if holding:
        answer = 'The inventory record does not establish which items are held in your hands.'
    elif disposition == 'AMBIGUOUS' or len(matches) > 1:
        disposition = 'AMBIGUOUS'
        category = ConversationalDecisionCategory.CLARIFY
        answer = 'Which inventory item do you mean? Please give its name.'
    elif len(matches) == 1:
        index, row = matches[0]
        # Validate the source quantity, not the DTO's numeric default. The
        # projection may omit malformed rows; identity matching stays fail closed.
        raw_matches = [r for r in raw_inventory if isinstance(r, Mapping)
                       and r.get('id') == row.get('id') and r.get('name') == row.get('name')
                       and (not instance_id or r.get('instance_id') == instance_id)]
        quantity = raw_matches[0].get('quantity') if len(raw_matches) == 1 else None
        subject = row.get('name') or subject
        target_id = row.get('id')
        if type(quantity) in (int, float) and math.isfinite(quantity) and quantity >= 0:
            disposition = 'ANSWERABLE' if quantity > 0 else 'ABSENT'
            answer = (f'Your inventory records {quantity:g} × {subject}.' if quantity > 0
                      else f'Your inventory records no {subject} (quantity zero).')
            answer += ' This record does not establish whether it is equipped, held, or stored.'
        else:
            answer = f'I cannot establish whether you have {subject}: its inventory quantity is not established.'
    else:
        answer = f'I cannot establish whether you have {subject} from the current inventory record. An unlisted item is not proof of absence.'
    return ConversationalDecision(
        category=category, primary_intention=text, intent_family='inventory_information',
        reason='player_sheet_possession', disposition=disposition,
        player_facing_text=answer, execution_policy='answer_only', intent_modality='informational',
        authorization={'authority_provenance':'player_http_projection.CHARACTER',
                       'source':source, 'source_index':index,
                       'information_type':'possession', 'information_disposition':disposition,
                       'subject':subject, 'subject_id':target_id,
                       'subject_instance_id':matches[0][1].get('instance_id') if len(matches) == 1 else None,
                       'scene_id':sid, 'character_id':cid,
                       'relevance_basis':'unique_inventory_identity_and_quantity' if disposition in {'ANSWERABLE','ABSENT'} else 'specific_uncertainty_or_clarification',
                       'mutation_eligibility':False},
    )


_RECALL_TOPIC = re.compile(
    r"^(?:go(?:ing)? back to|back to|returning to|revisiting)\s+([^,!?;]+),\s*",
    re.I,
)
_RECALL_SOURCE_QUESTION = re.compile(
    r"^(?:(?:what did (?P<source>[^,!?;]+?) (?:say|show|reveal|tell us)"
    r"(?: about (?P<about>[^,!?;]+?))?)"
    r"|(?:where did (?P<where_source>[^,!?;]+?) (?:say|show) (?P<detail>[^,!?;]+)))"
    r"(?: earlier| again)?\??$",
    re.I,
)
_RECALL_LAST_SIGHTING = re.compile(
    r"(?P<subject>.+?) (?:was|were) (?:last (?:seen|spotted|sighted)|(?:seen|spotted|sighted) last)",
    re.I,
)
_RECALL_OBSERVATION = re.compile(
    r"(?:what did i (?:see|discover) at (?P<place>[^,!?;]+)"
    r"|what did i (?:notice|learn|find) about (?P<detail>[^,!?;]+)"
    r"|where did i (?:see|encounter|find) (?P<where>[^,!?;]+)"
    r"|where were (?P<located>[^,!?;]+)"
    r"|did i see (?P<seen>[^,!?;]+?) earlier"
    r"|do i remember (?P<remembered>[^,!?;]+?) near (?P<near>[^,!?;]+))", re.I,
)


def _historical_scene_overviews(log):
    """Read previously delivered public overviews with recorded scene attribution."""
    scene_id = ""
    for turn in log or []:
        if not isinstance(turn, Mapping):
            continue
        resolution = turn.get("resolution") or {}
        if resolution.get("kind") == "scene_transition" and resolution.get("success") is True:
            scene_id = resolution.get("target_scene_id") or ""
        decision = (resolution.get("metadata") or {}).get("conversational_decision") or {}
        if (decision.get("reason") != "visible_scene_context_answer"
                or decision.get("context_references") != ["active_scene_public_summary"]):
            continue
        source = (decision.get("authorization") or {}).get("scene_id") or scene_id
        line = turn.get("player_facing_text") or ""
        match = re.fullmatch(r"You are at ([^.]+)\. (.+)", line)
        if source and match:
            yield source, match[1], match[2]


def _historical_observation_decision(text, match, *, session, log):
    """Use persisted discovery or a delivered observation without implying present status."""
    place = _scene_subject(match["place"] or match["near"] or "")
    detail = _scene_subject(next((value for key, value in match.groupdict().items()
                                  if key not in {"place", "near"} and value), ""))
    overviews = {
        sid: (label, observed) for sid, label, observed in _historical_scene_overviews(log)
        if not place or _place_match(place, label)
    }
    matches = {}
    discoveries = "discover" in text.casefold() or bool(match["detail"])
    location_only = bool(match["where"] or match["located"])
    from copy import deepcopy
    from game.storage import get_effective_scene

    detached = deepcopy(dict(session or {}))
    for clue_id, clue in ((session or {}).get("clue_knowledge") or {}).items():
        if not isinstance(clue, Mapping) or clue.get("state") != "discovered" or not clue.get("text"):
            continue
        sid = clue.get("source_scene") or ""
        label = overviews.get(sid, (sid.replace("_", " ").title(), ""))[0]
        if not sid or (match["place"] and not discoveries and sid in overviews):
            continue
        source_id = clue.get("source_interactable") or ""
        body = _scene_obj(get_effective_scene(detached, sid))
        source = next((item for item in body.get("interactables") or []
                       if _public_scene_row(item) and item.get("id") == source_id), None)
        names = {_norm_place(name) for name in _aliases(source, source_id)}
        if place and place not in names and not _place_match(place, label):
            continue
        if (detail and not {detail, detail.removesuffix("s")} & names
                and f" {detail} " not in f" {_norm_place(clue['text'])} "):
            continue
        matches[sid, f"clue_knowledge:{clue_id}"] = (
            f"At {label}, based on your earlier discovery." if location_only else
            f"At {label}, you learned: {clue['text']}"
        )
    if not matches and not discoveries:
        for sid, (label, observed) in overviews.items():
            if (place or detail) and (not detail or f" {detail} " in f" {_norm_place(observed)} "):
                matches[sid, f"historical_scene_overview:{sid}"] = (
                    f"Earlier, at {label}." if location_only else
                    f"Earlier, at {label}, this was described: {observed}"
                )
    ambiguous = len({sid for sid, _ in matches}) > 1
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY if ambiguous else ConversationalDecisionCategory.ANSWER,
        primary_intention=text, intent_family="gm_information",
        communication_owner="GM", communication_purpose="RECALL",
        reason=("historical_observation_recall" if matches and not ambiguous else "historical_observation_unestablished"),
        player_facing_text=("Which earlier location do you mean?" if ambiguous else
                            " ".join(dict.fromkeys(matches.values())) if matches else
                            "That information has not been established."),
        context_references=[ref for _, ref in matches] if not ambiguous else [],
        execution_policy="answer_only", intent_modality="informational",
    )


def _unresolved_pronominal_address(text, *, scene, session, world) -> ConversationalDecision | None:
    if not re.match(r"^(?:(?:i|we)\s+)?(?:ask|tell) (?:him|her|them)\b", text, re.I):
        return None
    from game.ordinary_semantic_ownership import assess_addressee_grounding

    grounding = assess_addressee_grounding(text, scene=scene, session=session, world=world)
    if grounding.get("target_id"):
        return None
    return ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY,
        primary_intention=text, intent_family="clarification", reason="unresolved_addressee",
        communication_owner="GM", communication_purpose="CLARIFICATION",
        player_facing_text="Who do you want to speak to?",
        execution_policy="answer_only", intent_modality="informational",
    )


def _discovery_recall_decision(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    log: list | None = None,
) -> ConversationalDecision | None:
    """Answer past inspection questions from source-bound, disclosed clues."""
    from copy import deepcopy
    from game.exploration import _source_disclosed_facts
    from game.storage import get_effective_scene

    question = re.sub(r"^(?:GM|DM|Dungeon Master),\s*", "", text, flags=re.I)
    topic = _RECALL_TOPIC.match(question)
    source = topic[1] if topic else ""
    question = question[topic.end():] if topic else question
    question = question.rstrip("?").strip()
    source_question = _RECALL_SOURCE_QUESTION.fullmatch(question)
    subject = ""
    unsupported = False
    if source_question and not source:
        source = source_question["source"] or source_question["where_source"]
        if source_question["detail"]:
            detail = re.sub(r" (?:earlier|again)$", "", source_question["detail"], flags=re.I)
            sighting = _RECALL_LAST_SIGHTING.fullmatch(detail)
            subject = sighting["subject"] if sighting else ""
            unsupported = sighting is None
    elif sighting := re.fullmatch(
        r"where (was|were) ([^,!?;]+?) (last (?:seen|spotted|sighted)|(?:seen|spotted|sighted) last)"
        r"(?: earlier| again)?", question, re.I,
    ):
        subject = sighting[2]
    elif not (topic and re.fullmatch(r"what did (?:it|that|this) (?:say|show|reveal)", question, re.I)):
        if not topic and (observation := _RECALL_OBSERVATION.fullmatch(question)):
            return _historical_observation_decision(text, observation, session=session, log=log)
        return None

    source_key = _norm_place(re.sub(r"^(?:that|this)\s+(?=\w)", "", source, flags=re.I))
    about = _norm_place(source_question["about"] or "") if source_question else ""
    if about.startswith("where ") and (sighting := _RECALL_LAST_SIGHTING.fullmatch(about[6:])):
        subject, about = sighting["subject"], ""
    subject_key = _norm_place(subject)
    source_pronoun = source_key in {"it", "that", "this"}
    subject_pronoun = subject_key in {"it", "they", "he", "she"}
    deictic = source_pronoun or subject_pronoun
    session = session or {}
    if source_pronoun:
        last_action = _conversation_context(session).get("last_executed_intention") or {}
        anchor = (last_action.get("scene_id"), last_action.get("target"))
        if last_action.get("operation") != "INSPECT" or not all(anchor):
            anchor = (None, None)
    else:
        anchor = None
    current = _scene_obj(scene)
    knowledge = session.get("clue_knowledge") or {}
    prior_scenes = {item for item in session.get("visited_scene_ids") or [] if isinstance(item, str)}
    if isinstance(knowledge, Mapping):
        prior_scenes.update(
            row["source_scene"] for row in knowledge.values()
            if isinstance(row, Mapping) and isinstance(row.get("source_scene"), str)
        )
    scenes = [current]
    prior_scenes.discard(current.get("id"))
    if prior_scenes:
        # The effective-scene loader lazily normalizes overlays. Keep that
        # normalization off the caller's session during a read-only turn.
        detached = deepcopy(dict(session))
        scenes.extend(_scene_obj(get_effective_scene(detached, sid)) for sid in sorted(prior_scenes) if sid)

    sources = set()
    facts = {}
    for body in scenes:
        for item in body.get("interactables") or []:
            if (not isinstance(item, Mapping) or item.get("hidden") or item.get("gm_only")
                    or item.get("visible") is False or item.get("accessible") is False):
                continue
            clue_id = item.get("reveals_clue")
            if not isinstance(clue_id, str) or not clue_id:
                continue
            if source_key and source_key not in {"it", "that", "this"}:
                aliases = _aliases(item, str(item.get("id") or ""))
                if source_key not in {_norm_place(alias) for alias in (*aliases, clue_id)}:
                    continue
            identity = (body.get("id"), item.get("id"))
            if anchor is not None and identity != anchor:
                continue
            sources.add(identity)
            texts = _source_disclosed_facts(body, session, item)
            for fact in texts:
                if about and f" {about} " not in f" {_norm_place(fact)} ":
                    continue
                if subject:
                    # An inspected source anchors a source pronoun, not a
                    # pronoun for a person or thing mentioned in its text.
                    if subject_pronoun:
                        continue
                    statement = re.match(
                        r"^(.+?) (?:was|were) last (?:seen|spotted|sighted)\b", fact, re.I,
                    )
                    if not statement or (_norm_place(statement[1]) != subject_key
                                         and _norm_place(statement[1]).removeprefix("missing ") != subject_key):
                        continue
                facts[(body.get("id"), clue_id)] = fact

    # Named speech from a person stays with the existing dialogue owner.
    if source_key and not deictic and not sources and source_question and not topic:
        if not subject:
            return None
        from game.conversational_continuity import delivered_exchanges

        people = [*(current.get("addressables") or []), *((world or {}).get("npcs") or [])]
        speaker_names = {_norm_place(row.get("speaker_name")) for row in delivered_exchanges(session)
                         if row.get("ownership") == "npc" and row.get("speaker_id")}
        for person in people:
            if isinstance(person, Mapping) and not person.get("hidden") and person.get("visible") is not False:
                speaker_names.update(_norm_place(name) for name in _aliases(person, str(person.get("id") or "")))
                speaker_names.update(_norm_place(name) for name in person.get("address_roles") or [])
        if source_key in speaker_names:
            return None
    ambiguous = len(facts) > 1 or (bool(source_key) and not deictic and len(sources) > 1)
    if ambiguous or (deictic and not facts):
        reason = "ambiguous_discovery_reference"
        answer = "Which earlier discovery do you mean?"
    elif unsupported or not facts:
        reason = "discovery_information_unavailable"
        answer = "That information has not been established."
    else:
        reason = "discovered_clue_recall"
        answer = next(iter(facts.values()))
    return ConversationalDecision(
        category=(ConversationalDecisionCategory.CLARIFY if reason == "ambiguous_discovery_reference"
                  else ConversationalDecisionCategory.ANSWER),
        primary_intention=text, intent_family="gm_information",
        communication_owner="GM", communication_purpose="QUESTION",
        reason=reason, player_facing_text=answer,
        execution_policy="answer_only", intent_modality="informational",
        authorization={"source": "clue_knowledge", "mutation_eligibility": False},
    )


def deterministic_conversational_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    log: list | None = None,
    character: Mapping[str, Any] | None = None,
) -> ConversationalDecision | None:
    """Return a no-provider decision for obvious non-mutating cases."""
    from game.live_chat_interpretation import production_live_interpretation_enabled
    text = _clean_text(player_text)
    full_request = full_request_admission(text, scene=scene, world=world, session=session)
    if full_request is not None:
        return full_request
    # A supported correction names one route. It must be chosen before a
    # leading phrase can be mistaken for an addressee or a model target.
    from game.scene_destination_binding import classify_destination_choice

    destination_choice = classify_destination_choice(text, _exit_rows(scene))
    if destination_choice.get("kind") == "correction" and len(destination_choice.get("exit_ids") or []) == 1:
        from game.route_authority import route_status

        visible = [
            row for row in _exit_rows(scene)
            if route_status(row, _scene_id(scene), dict(session or {}), dict(world or {})) != "hidden"
        ]
        row = next((item for item in visible if _clean_text(item.get("id")) == destination_choice["exit_ids"][0]), None)
        if row is not None:
            label = _label(row, _clean_text(row.get("id")))
            return _move_decision_for_row(
                row, player_text=text, summary=f"Go to {label}.", incidental=[], session=session,
            )
    from game.interaction_completion import corrected_dialogue

    if corrected_dialogue(text):
        # A new question with an explicit correction does not resume a prior
        # proposal or bind to the last speaker.
        return None
    from game.authored_action_language import decision_for
    authored = decision_for(text, scene=scene, world=world, session=session)
    if authored is not None:
        return authored
    from game.player_initiative import decide as initiative_decision
    initiative = initiative_decision(text, scene=scene, world=world, session=session)
    if initiative is not None:
        return initiative
    inventory = _inventory_information_decision(
        text, character=character, session=session, scene=scene, log=log,
    )
    if inventory is not None:
        return inventory
    inspection = _inventory_inspection_decision(
        text, character=character, session=session, scene=scene, world=world, log=log,
    )
    if inspection is not None:
        return inspection
    posted_reading = _posted_reading_decision(text, scene=scene, world=world, session=session)
    if posted_reading is not None:
        return posted_reading
    from game.carried_object_grounding import carried_object_decision

    carried = carried_object_decision(
        text, character=character, session=session, scene=scene, world=world, log=log,
    )
    if carried is not None:
        pending = _conversation_context(session).get("pending_clarification") or {}
        if (
            isinstance(pending, Mapping)
            and pending.get("kind") == "compound_sequence"
            and re.search(r"\bi mean\b", text, re.I)
        ):
            carried = replace(
                carried,
                context_update=_context_update(pending=None, pending_set=True, intention=None, intention_set=True),
            )
        return carried
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
    address = _unresolved_pronominal_address(text, scene=scene, session=session, world=world)
    if address is not None:
        return address
    recall = _discovery_recall_decision(text, scene=scene, session=session, world=world, log=log)
    if recall is not None:
        return recall
    observation = _current_observation_decision(
        text, scene=scene, session=session, world=world,
        defer_unknown=production_live_interpretation_enabled(),
    )
    if observation is not None:
        return observation
    information = _gm_information_decision(text, scene=scene, world=world, session=session)
    if information is not None:
        # A repeat of speech the captain already gave stays on that exchange.
        # An unmatched "tell me ... again" has no present speaker, so the DM
        # answer above remains.
        from game.conversational_continuity import continuity_directive

        directive = continuity_directive(text, session=session, scene=scene, world=world)
        repeated_npc = (
            isinstance(directive, dict)
            and directive.get("reason") == "repeat_delivered_statement"
            and directive.get("owner") == "npc"
            and str(directive.get("npc_id") or "")
        )
        if not repeated_npc:
            return information
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
    gm_continuation = _gm_continuation_decision(text, session, log, scene=scene, world=world)
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
        log=log,
        character=character,
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
    grounded_object = _grounded_object_question(
        text, scene=scene, session=session,
    )
    if grounded_object is not None:
        return grounded_object
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
    from game.local_interaction import resolve_transient_local_action

    transient = resolve_transient_local_action(
        text, scene=scene, world=world, session=session,
    )
    if isinstance(transient, dict):
        return _transient_local_decision(text, transient)
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
    named_objects = None
    from game.conversational_continuity import established_scene_object_ids
    from game.interaction_completion import addressed_person_nominal
    from game.intent_parser import looks_like_explicit_leave_or_pursuit_intent

    named_objects = established_scene_object_ids(text, scene)
    public_ids = {
        str(item.get("id") or "") for item in _scene_obj(scene).get("interactables") or []
        if isinstance(item, Mapping) and not item.get("hidden") and item.get("visible") is not False
    }
    named_objects &= public_ids
    if (
        len(named_objects) > 1
        and not addressed_person_nominal(text)
        and not looks_like_explicit_leave_or_pursuit_intent(text)
    ):
        inner = scene.get("scene") if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else scene
        labels = []
        for item in (inner.get("interactables") or []) if isinstance(inner, Mapping) else []:
            if isinstance(item, Mapping) and str(item.get("id") or "") in named_objects:
                labels.append(_label(item, str(item.get("id") or "")))
        shown = " or ".join(labels[:4]) or "one of those"
        return ConversationalDecision(
            category=ConversationalDecisionCategory.CLARIFY,
            primary_intention=text,
            intent_family="local_interaction",
            reason="ambiguous_scene_object",
            disposition="CLARIFICATION",
            missing_information=["unique_scene_target"],
            confidence=0.8,
            player_facing_text=f"Your request: {text} More than one thing here is named. Do you mean {shown}? Nothing has been attempted.",
            intent_modality="committed",
            execution_policy="clarify_before_execution",
        )
    recent = _recent_visible_answer(text, log)
    if (
        _QUESTION_START_RE.search(text)
        and recent is not None
        and not named_objects
    ):
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
    unbound = _unbound_physical_decline(text, scene=scene, world=world, session=session)
    if unbound is not None:
        return unbound
    return None


def _gm_information_decision(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """Answer a DM-directed question from public facts, or say the limit.

    An unmatched person is not replaced with someone else who happens to be
    present. A known person with no public answer stays that person.
    """
    from game.ordinary_semantic_ownership import gm_information_disposition

    row = gm_information_disposition(text, scene=scene, world=world, session=session)
    if row is None:
        return None
    kind = str(row.get("disposition") or "")
    subject = str(row.get("subject") or "that")
    person = str(row.get("person") or "")
    label = str(row.get("person_label") or person)
    lines = [str(line) for line in row.get("lines") or [] if str(line).strip()]
    labels = [str(item) for item in row.get("labels") or [] if str(item).strip()]
    if kind == "ambiguous_person" and labels:
        message = "Which person do you mean: " + " or ".join(labels) + "? Nothing has been attempted."
        category = ConversationalDecisionCategory.CLARIFY
        reason = "ambiguous_person_reference"
    elif kind == "unmatched_person":
        shown = re.sub(r"^(?:the|a|an)\s+", "", person or subject, flags=re.IGNORECASE)
        message = f"No established person matches {shown}. Nothing has been attempted."
        category = ConversationalDecisionCategory.CLARIFY
        reason = "unmatched_person_reference"
    elif kind == "unknown_information":
        message = (
            f"{label} is an established person here. "
            "The requested information is not established. Nothing has been attempted."
        )
        category = ConversationalDecisionCategory.ANSWER
        reason = "established_person_information_unavailable"
    elif kind == "public_fact" and lines:
        message = "From what is established here: " + " ".join(lines)
        category = ConversationalDecisionCategory.ANSWER
        reason = "established_public_information"
    elif kind == "public_fact" and label:
        message = (
            f"{label} is an established person here. "
            "Further information about them is not established. Nothing has been attempted."
        )
        category = ConversationalDecisionCategory.ANSWER
        reason = "established_person_information_unavailable"
    else:
        shown = subject or "that"
        message = f"Nothing established here describes {shown}. Nothing has been attempted."
        category = ConversationalDecisionCategory.CLARIFY
        reason = "unresolved_information_subject"
    return ConversationalDecision(
        category=category,
        primary_intention=text,
        intent_family="gm_information",
        communication_owner="GM",
        communication_purpose="QUESTION",
        reason=reason,
        player_facing_text=message,
        execution_policy="answer_only",
        intent_modality="informational",
        context_references=["gm_directed_information", "subject:" + subject[:120]],
    )


def _grounded_object_question(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """A question about an established object does not need an NPC addressee.

    The existing content-question recovery supplies the target. This only
    admits that target to the current inspection owner.
    """
    if not text or not isinstance(scene, Mapping):
        return None
    from game.intent_parser import recover_interactable_content_question

    action = recover_interactable_content_question(text, dict(scene))
    if not isinstance(action, dict) or str(action.get("type") or "").strip().lower() != "investigate":
        return None
    target_id = str(action.get("target_id") or "").strip()
    if not target_id:
        return None
    from game.conversational_continuity import established_scene_object_ids
    from game.intent_parser import _INTERACTABLE_CONTENT_QUESTION_RES

    for pat in _INTERACTABLE_CONTENT_QUESTION_RES:
        match = pat.search(text)
        if not match:
            continue
        raw_target = str(match.group("target") or "")
        if re.search(r"\band\b", raw_target, re.IGNORECASE):
            left, right = re.split(r"\band\b", raw_target, maxsplit=1, flags=re.IGNORECASE)
            left_ids = established_scene_object_ids(left, scene)
            right_ids = established_scene_object_ids(right, scene)
            if left_ids != right_ids or not right_ids:
                return ConversationalDecision(
                    category=ConversationalDecisionCategory.CLARIFY,
                    primary_intention=text,
                    intent_family="local_interaction",
                    reason="ambiguous_scene_object",
                    confidence=0.8,
                    player_facing_text="More than one thing is named, and only one of them is established here. Nothing has been attempted.",
                    intent_modality="committed",
                    execution_policy="clarify_before_execution",
                )
        break
    info = _catalog(scene, None).get(target_id)
    if not isinstance(info, Mapping):
        return None
    if str(info.get("kind") or "") not in {"inspect_target", "perceive_target"}:
        return None
    row = info.get("row") if isinstance(info.get("row"), Mapping) else None
    if re.fullmatch(r"what does\s+[\w '-]+\s+say[?]?", text, re.I):
        # A question about already visible writing is not a new examination.
        # Never use the interactable's reveals_clue or hidden examination text.
        names = _aliases(row, target_id)
        evidence = {ref: value for ref, value in public_conversation_evidence(scene, []).items()
                    if ref.startswith("visible:") and any(
                        re.search(r"\b" + re.escape(_norm_place(name)) + r"\b", _norm_place(value))
                        for name in names if _norm_place(name))}
        return ConversationalDecision(
            category=ConversationalDecisionCategory.ANSWER, primary_intention=text,
            intent_family="gm_communication", communication_owner="GM", communication_purpose="DESCRIPTION",
            reason="established_visible_contents_question", execution_policy="answer_only", intent_modality="informational",
            player_facing_text=(" ".join(dict.fromkeys(evidence.values())) if evidence else
                               "That object's contents have not been established in the visible information. Do you want to examine it?"),
            context_references=list(evidence),
            authorization={"contract_consistency": "CONSISTENT", "mutation_eligibility": False},
        )
    return _operation_execute_decision(
        operation="INSPECT",
        target_id=target_id,
        label=_label(row, target_id),
        player_text=text,
        incidental=[],
        session=session,
    )


def _unbound_physical_decline(
    text: str,
    *,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> ConversationalDecision | None:
    """An improvised manipulation with no authored object is not narration.

    The existing physical owner still runs when that experiment is on, and a
    parser that already bound an action keeps that action.
    """
    if not text or "?" in text or _QUESTION_START_RE.search(text):
        return None
    from game.physical_adjudication import clear_simple_retreat, disabled_action_disposition, enabled

    if enabled(session):
        return None
    # The API's existing retreat refusal retains its publication classification.
    if clear_simple_retreat(text):
        return None
    from game.intent_parser import parse_freeform_to_action, recover_actionable_explicit_world_action

    scene_dict = dict(scene) if isinstance(scene, Mapping) else None
    world_dict = dict(world) if isinstance(world, Mapping) else None
    session_dict = dict(session) if isinstance(session, Mapping) else None
    if parse_freeform_to_action(text, scene_dict, session=session_dict, world=world_dict) is not None:
        return None
    recovered = recover_actionable_explicit_world_action(
        text, scene_dict, session=session_dict, world=world_dict,
    )
    meta = (recovered.get("metadata") or {}) if isinstance(recovered, dict) else {}
    physical_lane = meta.get("parser_lane") == "physical_object_interaction"
    outcome = disabled_action_disposition(
        text, session_dict, scene_dict,
        operation=meta.get("physical_verb") if physical_lane else None,
    )
    if outcome is None:
        return None
    return ConversationalDecision(
        category=ConversationalDecisionCategory(outcome["category"]),
        primary_intention=text,
        intent_family="physical_action",
        reason="unsupported_physical_manipulation",
        confidence=0.84,
        player_facing_text=outcome["text"],
        disposition=outcome["disposition"],
        missing_information=outcome["missing"],
        proposed_target=outcome.get("target_id"),
        authorization={"nonexecution": outcome["reason"]},
        intent_modality="committed",
        execution_policy="decline_unadjudicated_contact",
    )


_IN_PLACE_POSTURE = r"crouch(?: down)?|kneel(?: down)?|bend down|lean closer|lower myself|tilt my head|stoop"
_INSPECTION_POSTURE_RE = re.compile(
    rf"(?:I|we) (?P<posture>{_IN_PLACE_POSTURE}) "
    r"(?:(?:and|to) (?:examine|inspect|study|read|look (?:closely )?at)|for a better look at) "
    r"(?P<target>[\w '-]+)[.]?",
    re.I,
)
_SQUAT_INSPECTION_RE = re.compile(
    r"(?:I|we) (?P<posture>squat beside (?P<target>[\w '-]+?)) and look closely[.]?", re.I,
)


def _grounded_inspection_posture(text, *, scene, world, session):
    """Account for all wording and bind the inspected surface in this scene."""
    match = _INSPECTION_POSTURE_RE.fullmatch(text) or _SQUAT_INSPECTION_RE.fullmatch(text)
    current = _scene_obj(scene)
    if not match or current.get("mode") == "combat" or (session or {}).get("in_combat"):
        return None

    from game.local_interaction import _row_veto
    from game.player_interpretation_bridge import visible_catalog
    from game.referenced_surface import (
        AUTHORITY_AUTHORED_INTERACTABLE, classify_referenced_surface, content_tokens,
    )

    def words(phrase):
        return re.sub(r"^(?:the|a|an) ", "", phrase.casefold()).replace("_", " ").split()

    def signature(phrase):
        tokens = words(phrase)
        stems = content_tokens(" ".join(tokens))
        return stems if len(tokens) == len(stems) else tokens

    target = match["target"]
    names = [signature(target)]
    # The complete locative phrase can name an authored compound surface.
    locative = re.fullmatch(r"([\w'-]+) in (?:the )?([\w'-]+)", " ".join(words(target)))
    if locative:
        names.append(signature(f"{locative[2]} {locative[1]}"))
    matches = [
        (entity_id, alias, info["row"])
        for entity_id, info in visible_catalog(scene, world).items()
        if info["kind"] in {"inspect_target", "perceive_target"}
        for alias in _aliases(info["row"], entity_id)
        if signature(alias) in names
    ]
    if len({entity_id for entity_id, _, _ in matches}) != 1:
        return None
    entity_id, alias, row = matches[0]
    if _row_veto(row) or row.get("gm_only") or row.get("public") is False:
        return None
    surface = classify_referenced_surface("", scene, world=world, explicit_target=alias)
    if surface.get("authority") != AUTHORITY_AUTHORED_INTERACTABLE or surface.get("interactable_id") != entity_id:
        return None
    return match["posture"], target, alias, entity_id


def _normalize_inspection_posture(record, text, *, scene, world, session, log):
    """Reconcile a posture component before communication and bridge admission."""
    communication = record.get("communication") or {}
    components = record.get("action_components") or []
    references = record.get("references") or {}
    if (record.get("communication_mode") != "IN_WORLD_ACTION"
            or record.get("interpretation_status") != "INTERPRETED"
            or not isinstance(communication, Mapping) or not isinstance(references, Mapping)
            or not isinstance(components, list)
            or record.get("clarification_question") or references.get("unresolved_references")
            or communication.get("recipient") not in {"GM", "MIXED", "CHARACTER"}
            or communication.get("purpose") != "ACTION"
            or len(components) != 2 or not all(isinstance(part, Mapping) for part in components)):
        return record
    move, inspect = components
    if (move.get("order") != 1 or inspect.get("order") != 2
            or move.get("operation_class") != "MOVE" or move.get("target_ref") is not None
            or inspect.get("operation_class") != "INSPECT"
            or inspect.get("target_ref") not in (references.get("permitted_entity_ids") or [])):
        return record
    grounded = _grounded_inspection_posture(text, scene=scene, world=world, session=session)
    if grounded is None:
        return record
    posture, target_phrase, alias, entity_id = grounded
    if inspect.get("target_ref") != entity_id:
        return record
    # The component must describe the same posture, optionally with an explicit
    # visual purpose bound to the literal target in the player's request.
    literal_posture = re.escape(posture)
    if posture.casefold() == "crouch":
        literal_posture += r"(?: down)?"
    visual_purpose = rf"(?: to get a closer look at {re.escape(target_phrase)})?"
    if not re.fullmatch(literal_posture + visual_purpose + r"[.]?", _clean_text(move.get("description")), re.I):
        return record

    from game.live_chat_interpretation import valid_communication
    if not valid_communication(communication, public_conversation_evidence(scene, log)):
        return record
    return {
        **record,
        "communication": {**communication, "recipient": "CHARACTER"},
        "action_components": [dict(inspect)],
        "incidental_context": [*(record.get("incidental_context") or []), posture],
        "contract_consistency": {
            "status": "AUTHORITATIVELY_RESOLVABLE",
            "authority": "incidental_posture_and_unique_visible_inspection_target",
            "original_request": text,
            "original_communication": dict(communication),
            "original_components": [dict(move), dict(inspect)],
            "suppressed_component": dict(move),
            "posture_phrase": posture,
            "target_phrase": target_phrase,
            "target_id": entity_id,
            "inspection_alias": alias,
        },
    }


def _reading_restatement(record, text, *, scene, world, session, character, log):
    """An explicit restatement can authorize consideration of a single INSPECT."""
    communication = record.get("communication") or {}
    if not isinstance(communication, Mapping) or communication.get("recipient") != "GM":
        return record, None
    if (communication.get("purpose"), record.get("communication_mode"), record.get("interpretation_status")) == (
        "CLARIFICATION", "CLARIFICATION", "CLARIFICATION_REQUIRED",
    ):
        match = re.fullmatch(
            r"(?P<target>[\w -]+?)(?: by (?:the )?(?P<landmark>[\w-]+))?\. "
            r"That['’]s the (?:sign|board|one) I want to read[.]?", text, re.I,
        )
    elif (communication.get("purpose"), record.get("communication_mode"), record.get("interpretation_status")) == (
        "CONFIRMATION", "IN_WORLD_ACTION", "INTERPRETED",
    ):
        match = re.fullmatch(r"Yes, I(?:['’]d| would) like to read (?P<target>[\w -]+)[.]?", text, re.I)
    else:
        return record, None
    if not match:
        return record, None
    restriction = full_request_admission(text, scene=scene, world=world, session=session)
    if restriction is not None:
        return record, restriction
    from game.live_chat_interpretation import valid_communication

    grounded = _grounded_reading_target(match["target"], scene=scene, world=world, session=session)
    landmark = match.groupdict().get("landmark")
    location = _norm_place(str(_scene_obj(scene).get("location") or "")).split()
    references = record.get("references") or {}
    components = record.get("action_components") or []
    if (grounded and (landmark is None or landmark.casefold() in location)
            and (landmark or not _inventory_reference_matches(match["target"], character))
            and isinstance(components, list) and len(components) == 1 and isinstance(components[0], Mapping)
            and components[0].get("operation_class") == "INSPECT"
            and components[0].get("target_ref") == grounded[0]
            and isinstance(references, Mapping)
            and grounded[0] in (references.get("permitted_entity_ids") or [])
            and not references.get("unresolved_references")
            and valid_communication(communication, public_conversation_evidence(scene, log))):
        return _with_grounded_reading(record, text, *grounded), None
    return record, ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY, primary_intention=text,
        intent_family="clarification", reason="unresolved_reading_target",
        missing_information=["object_target"], execution_policy="answer_only",
        player_facing_text="Which visible object do you want to read? Nothing has been attempted.",
    )


def _inspection_communication_consistency(record, text, *, scene=None, world=None, session=None, log=None):
    """Reconcile an inspection mislabeled as GM information.

    Only a complete affirmative examination and a uniquely matching public
    target may change ownership. The bridge and inspection admission still own
    legality, resolution, and deferred time commitment.
    """
    communication = record.get("communication") or {}
    components = record.get("action_components") or []
    if (not isinstance(communication, Mapping)
            or communication.get("recipient") != "GM"
            or communication.get("purpose") not in {"DESCRIPTION", "QUESTION"}
            or not any(isinstance(c, Mapping) and c.get("operation_class") == "INSPECT" for c in components)):
        return record, None
    # Information wording cannot be made executable by a fabricated component.
    if _QUESTION_START_RE.search(text) or re.match(r"^describe\b", text, re.I):
        return record, None
    restriction = full_request_admission(text, scene=scene, world=world, session=session)
    if restriction is not None:
        return record, restriction
    match = re.fullmatch(
        r"(?:I|we)\s+(?:examine|inspect|study|(?:take|want)\s+a\s+(?:good|closer)\s+look\s+at)\s+"
        r"(?P<target>[\w '-]+?)(?:\s+for\s+hidden markings)?[.]?", text, re.I,
    )
    from game.live_chat_interpretation import valid_communication
    from game.player_interpretation_bridge import visible_catalog
    references = record.get("references") or {}
    target = components[0].get("target_ref") if len(components) == 1 and isinstance(components[0], Mapping) else None
    raw_target = match.group("target") if match else ""
    phrase = _norm_place(raw_target)
    catalog = visible_catalog(scene, world) if match else {}
    candidates = dict(_ground_catalog_target(phrase, catalog, {"inspect_target", "perceive_target"}))
    # Matching a known noun inside a longer phrase must not erase a location,
    # restriction, or trailing intent the host has not accounted for.
    complete_targets = {
        entity_id for entity_id, info in candidates.items()
        if any(set(phrase.split()) <= set(_norm_place(name).split())
               for name in _aliases(info["row"], entity_id))
    }
    # “Warning about X” can name “X warning” when that full alias is authored.
    warning = re.fullmatch(r"(?:(?:the|a|an)\s+)?warning\s+about\s+(?:(?:the|a|an)\s+)?(.+)", raw_target, re.I)
    alias = " ".join(warning.group(1).casefold().split()) + " warning" if warning else ""
    alias_matches = set()
    if alias:
        for entity_id, info in catalog.items():
            if info["kind"] in {"inspect_target", "perceive_target"} and any(
                alias == " ".join(name.casefold().split()) for name in _aliases(info["row"], entity_id)
            ):
                candidates[entity_id] = info
                complete_targets.add(entity_id)
                alias_matches.add(entity_id)
    if (match and len(components) == 1 and components[0].get("operation_class") == "INSPECT"
            and record.get("interpretation_status") == "INTERPRETED"
            and isinstance(references, Mapping) and not references.get("unresolved_references")
            and target in (references.get("permitted_entity_ids") or [])
            and len(candidates) == 1 and target in complete_targets
            and not candidates[target]["row"].get("gm_only")
            and candidates[target]["row"].get("public") is not False
            and valid_communication(communication, public_conversation_evidence(scene, log))):
        prepared = dict(record)
        prepared["communication"] = {**communication, "recipient": "CHARACTER", "purpose": "ACTION"}
        prepared["communication_mode"] = "IN_WORLD_ACTION"
        prepared["contract_consistency"] = {
            "status": "AUTHORITATIVELY_RESOLVABLE", "original_communication": dict(communication),
            "authority": "complete_affirmative_examination_and_unique_visible_target",
            "original_request": text, "target_id": target,
        }
        if target in alias_matches:
            prepared["contract_consistency"]["inspection_alias"] = alias
        return prepared, None
    return record, ConversationalDecision(
        category=ConversationalDecisionCategory.CLARIFY, primary_intention=text,
        intent_family="clarification", reason="unresolved_inspection_communication_conflict",
        player_facing_text="Do you want the existing visible description, or to examine a specific visible object now? Nothing has been attempted.",
        authorization={"contract_consistency": "UNRESOLVED", "mutation_eligibility": False},
    )


def decision_from_interpretation_record(
    record: Mapping[str, Any] | None,
    *,
    bridge_meta: Mapping[str, Any] | None = None,
    player_text: str = "",
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    character: Mapping[str, Any] | None = None,
    log: list | None = None,
    in_combat: bool = False,
) -> ConversationalDecision:
    """Build a decision envelope from an existing interpretation/bridge result."""
    text = _clean_text(player_text)
    from game.interaction_completion import corrected_dialogue, npc_correction_prefix
    from game.ordinary_semantic_ownership import corrected_dialogue_target

    correction = corrected_dialogue(text)
    prefix = npc_correction_prefix(text)
    components = (record.get("action_components") or []) if isinstance(record, Mapping) else []
    if prefix and (prefix[1] or components):
        restriction = full_request_admission(text, scene=scene, world=world, session=session)
        if restriction is not None:
            return restriction
        target = corrected_dialogue_target(correction, scene=scene, world=world, session=session)
        if (not target or len(components) != 1 or not isinstance(components[0], Mapping)
                or components[0].get("operation_class") != "ASK" or components[0].get("target_ref") != target):
            return _nonaction_decision(
                text, modality="informational", reason="unconfirmed_corrected_dialogue",
                message="Please specify one question and who you are addressing. Nothing has been attempted.",
            )
    else:
        address = _unresolved_pronominal_address(text, scene=scene, session=session, world=world)
        if address is not None:
            return address
        recall = _discovery_recall_decision(text, scene=scene, session=session, world=world, log=log)
        if recall is not None:
            return recall
        observation = _current_observation_decision(text, scene=scene, session=session, world=world)
        if observation is not None:
            return observation
        grounded = decision_from_delivered_exchange(text, session=session, scene=scene, world=world)
        if grounded is not None:
            return grounded
    if isinstance(record, Mapping):
        record = _reclassify_direct_npc_address(record, text, scene=scene, world=world, session=session)
        from game.local_interaction import normalize_local_approach
        record = normalize_local_approach(record, player_text=text, scene=scene, world=world, session=session)
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
    if not in_combat:
        record = _normalize_inspection_posture(
            record, text, scene=scene, world=world, session=session, log=log,
        )
        record, reading_decision = _reading_restatement(
            record, text, scene=scene, world=world, session=session, character=character, log=log,
        )
        if reading_decision is not None:
            return reading_decision
    record, consistency_decision = _inspection_communication_consistency(
        record, text, scene=scene, world=world, session=session, log=log,
    )
    if consistency_decision is not None:
        return consistency_decision
    from game.carried_object_grounding import decision_for_model_record

    components = record.get("action_components") or []
    carried_text = text
    if len(components) == 1 and isinstance(components[0], Mapping) and components[0].get("operation_class") == "ASK":
        from game.interaction_completion import dialogue_attention
        from game.ordinary_semantic_ownership import dialogue_attention_target

        attention = dialogue_attention(text)
        if correction:
            carried_text = correction[2]
        elif attention and components[0].get("target_ref") and components[0]["target_ref"] == dialogue_attention_target(
            attention, scene=scene, world=world, session=session,
        ):
            carried_text = attention[2]
    carried = decision_for_model_record(
        record, carried_text, character=character, scene=scene, world=world, session=session, log=log,
    )
    if carried is not None:
        return carried
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
        travel = authored_travel_admission(
            text, scene=scene, world=world, session=session,
        )
        if travel is not None:
            return travel
        missing = unavailable_referent_decision(
            text, record, scene=scene, world=world,
        )
        if missing is not None:
            return missing
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
        if in_combat and primary.get("operation_class") == "MOVE":
            from game.scene_destination_binding import named_departure_destination

            if named_departure_destination(text) is not None:
                return _nonaction_decision(
                    text, modality="committed", reason="departure_during_combat",
                    message="You stay where you are. This route cannot be taken during combat.",
                )
        if (primary.get("operation_class") == "PERCEIVE" and not primary.get("target_ref")
                and re.fullmatch(r"(?:I|we) search for signs of danger[.]?", text, re.I)):
            from game.player_interpretation_bridge import visible_catalog
            labels = [_label(info["row"], entity_id) for entity_id, info in visible_catalog(scene, world).items()
                      if info["kind"] in {"inspect_target", "perceive_target"}]
            return ConversationalDecision(
                category=ConversationalDecisionCategory.CLARIFY, primary_intention=text,
                intent_family="world_operation", proposed_operation="PERCEIVE", reason="missing_target",
                player_facing_text=("You want to search the surroundings for signs of danger. "
                                    "I need a specific visible object or area to search."
                                    + (" Visible objects: " + ", ".join(labels) + "." if labels else "")
                                    + " Which do you mean? Nothing has been attempted."),
                authorization={"contract_consistency": "CONSISTENT", "mutation_eligibility": False},
            )
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
    authorization = (bridge_meta or {}).get("authorization") or {}
    if (operation == "ASK" and reason == "ungrounded_provider_target"
            and authorization.get("communication_ownership") == "gm_directed"):
        from game.ordinary_semantic_ownership import npc_followup_cue

        if not npc_followup_cue(player_text):
            return ConversationalDecision(
                category=ConversationalDecisionCategory.ANSWER,
                primary_intention=_clean_text(player_text),
                intent_family="context_question",
                communication_owner="GM",
                reason=reason,
                player_facing_text="I haven't resolved that question from the disclosed information.",
                execution_policy="answer_only",
            )
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
