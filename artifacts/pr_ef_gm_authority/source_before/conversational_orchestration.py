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


def _conversation_context(session: Mapping[str, Any] | None) -> Mapping[str, Any]:
    ctx = session.get("conversational_context") if isinstance(session, Mapping) else None
    return ctx if isinstance(ctx, Mapping) else {}


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
) -> dict[str, Any]:
    conversational: dict[str, Any] = {}
    if pending_set:
        conversational["pending_clarification"] = None if pending is None else dict(pending)
    if focused_set:
        conversational["focused_destination"] = None if focused is None else dict(focused)
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
    if kind in {"missing_destination", "ambiguous_destination", "compound_sequence"} or (
        operation == "MOVE" and kind != "missing_target"
    ):
        return _resume_bounded_pending(player_text=player_text, scene=scene, session=session, pending=pending)
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
    r"\b(?:go(?:es|ing)?|head(?:s|ing)?|walk(?:s|ing)?|travel(?:s|ing|led)?|"
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
    r"^\s*(?:yes|yeah|yep|do\s+that|do\s+the\s+first(?:\s+one)?|the\s+first(?:\s+one)?|go\s+ahead)\.?\s*$",
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
    if not _AGENT_RE.search(text) and _STATIVE_RE.search(text) and _mentioned_exits(text, exits):
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
) -> ConversationalDecision:
    pending = {
        "kind": "compound_sequence",
        "operation": _clean_text(steps[0].get("operation")) if steps else "",
        "original_text": player_text,
        "steps": steps,
        "scene_id": _scene_id(scene),
    }
    supported = [step for step in steps if step.get("supported")]
    unsupported = [step for step in steps if not step.get("supported")]
    if len(supported) == 1 and unsupported:
        message = (
            f"You can {_spoken_step(supported[0].get('text'))} first. I have not done this yet: "
            + ", ".join(_spoken_step(step.get("text")) for step in unsupported)
            + ". Should I do the first one now?"
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
        return _compound_clarification(text, steps, scene=scene, clear=clear, incidental=incidental)
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
        return _compound_clarification(text, [step], scene=scene, clear=clear, incidental=incidental)
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
        if label and _place_match(player_text, label):
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
                context_update=_context_update(pending=dict(pending), pending_set=True),
            )
        remaining = [step for step in steps if step is not selected]
        remainder = None
        if remaining:
            remainder = {
                "kind": "compound_sequence",
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
) -> ConversationalDecision:
    steps: list[dict[str, Any]] = []
    for component in connected:
        description = _clean_text(component.get("description")) or _clean_text(component.get("operation_class"))
        steps.append(
            {
                "text": description,
                "label": description,
                "operation": _clean_text(component.get("operation_class")).upper(),
                "target_id": _clean_text(component.get("target_ref")),
                "supported": bool(_clean_text(component.get("target_ref"))),
                "consequential": True,
                "dependency": "sequence",
                "status": "pending",
            }
        )
    for description in unsupported:
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
    return _compound_clarification(summary or player_text, steps, scene=None, clear=False, incidental=incidental)


def deterministic_conversational_decision(
    *,
    player_text: str,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    log: list | None = None,
) -> ConversationalDecision | None:
    """Return a no-provider decision for obvious non-mutating cases."""
    text = _clean_text(player_text)
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
) -> ConversationalDecision:
    """Build a decision envelope from an existing interpretation/bridge result."""
    text = _clean_text(player_text)
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
    mode = _clean_text(record.get("communication_mode"))
    status = _clean_text(record.get("interpretation_status"))
    summary = _clean_text((record.get("player_intent") or {}).get("summary") if isinstance(record.get("player_intent"), Mapping) else "")
    components = record.get("action_components") if isinstance(record.get("action_components"), list) else []
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
    incidental: list[str] = []
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
    if len(connected) > 1 or unsupported:
        return _compound_from_record_parts(text, summary, connected, unsupported, incidental)
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
    message, missing = _focused_bridge_clarification(reason, operation=operation)
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
    )
