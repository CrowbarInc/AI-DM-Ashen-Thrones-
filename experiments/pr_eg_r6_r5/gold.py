"""Gold intermediate inputs for diagnostic interventions.

These values are applied only inside the experiment process. They do not
change production modules, and they never add a disclosure-restricted source.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

ARMS = (
    "I1",
    "I2",
    "I3",
    "I4",
    "I5",
    "I6",
    "I7",
    "I8",
    "I9",
    "intent_referent",
    "question_source",
    "retrieval_correspondence",
    "correspondence_sufficiency",
    "I10B",
)

DISCLOSURE_RANK = {"direct": 3, "partial": 2, "refusal": 1, "clarification": 1, "unknown": 0}


def features(arm: str) -> dict[str, bool]:
    return {
        "act": arm in {"I1", "I9", "intent_referent"},
        "referent": arm in {"I2", "I9", "intent_referent"},
        "question": arm in {"I3", "I9", "question_source"},
        "retrieval": arm in {"I4", "I9", "retrieval_correspondence"},
        "source": arm in {"I5", "I9", "question_source"},
        "correspondence": arm in {"I6", "I9", "retrieval_correspondence", "correspondence_sufficiency"},
        "sufficiency": arm in {"I7", "I9", "correspondence_sufficiency"},
        "plan": arm in {"I8", "I10B"},
        "expression_off": arm == "I10B",
    }


def empty_operation() -> dict[str, Any]:
    return {
        "target_referent_id": "",
        "operation": "",
        "changed_fields": [],
        "follow_up_relationship": "",
        "changed_roles": [],
        "evidence": "",
        "target_evidence": "",
    }


def _public_prop(prop: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(prop, Mapping):
        return None
    return {key: value for key, value in prop.items() if not str(key).startswith("_")}


def follow_relationship(player: str) -> str:
    low = player.casefold()
    if "who told" in low:
        return "source_attribution"
    if "how do you know" in low:
        return "evidence"
    if "exact words" in low or low.startswith("please repeat") or "repeat " in low:
        return "speech_clarification"
    if "what about" in low:
        return "alternative_argument"
    return ""


def resolve_referent(session: Mapping[str, Any] | None, turn: Mapping[str, Any]) -> str:
    from game.conversational_referents import state

    spec = turn.get("referent") or {}
    memory = state(session) or {}
    records = [row for row in (memory.get("records") or []) if isinstance(row, Mapping)]
    select = spec.get("select") or "new"
    if select == "new":
        return ""
    if select == "previous":
        return str(memory.get("active_id") or "")
    needle = str(spec.get("text") or "")
    for record in reversed(records):
        if needle and needle.casefold() in str(record.get("question_text") or "").casefold():
            return str(record.get("referent_id") or "")
    return ""


def filter_topic_rows(rows: list[dict], turn: Mapping[str, Any], npc_id: str) -> list[dict]:
    """Keep hidden rows and only the gold public ids for the labeled addressee.

    Rows the host did not already possess are never inserted.
    """
    eligible = set(turn.get("eligible_source_ids") or [])
    expected = str(turn.get("addressee") or "")
    if expected and npc_id != expected:
        return [row for row in rows if row.get("hidden")]
    return [row for row in rows if row.get("hidden") or row.get("id") in eligible]


def correspondence_for_text(source_text: str, turn: Mapping[str, Any], npcs: list[dict]) -> str:
    wanted = turn.get("correspondence") or {}
    for npc in npcs:
        if turn.get("addressee") and npc.get("id") != turn.get("addressee"):
            continue
        for topic in npc.get("topics") or []:
            if topic.get("secret"):
                continue
            if str(topic.get("text") or "") == source_text and topic.get("id") in wanted:
                label = str(wanted[topic["id"]])
                if label in {"direct", "partial", "related_but_nonanswer", "unrelated", "unknown"}:
                    return label
    return ""


def authorized_fact(turn: Mapping[str, Any], npcs: list[dict]) -> dict[str, str] | None:
    """A public source the host already permits. Restricted topics return None."""
    if turn.get("answer_class") not in {"DIRECT", "PARTIAL"}:
        return None
    from game.dialogue_authority import npc_source_permitted

    npc = next((row for row in npcs if row.get("id") == turn.get("addressee")), None)
    if not isinstance(npc, dict):
        return None
    for source_id in turn.get("eligible_source_ids") or []:
        topic = next((row for row in npc.get("topics") or [] if row.get("id") == source_id), None)
        if isinstance(topic, dict) and npc_source_permitted(npc, topic):
            return {
                "source_id": str(source_id),
                "text": str(topic.get("text") or ""),
                "epistemic": str(topic.get("epistemic") or "npc_knowledge"),
                "speaker": str(npc.get("name") or ""),
            }
    return None


def _line_for(turn: Mapping[str, Any], npcs: list[dict]) -> tuple[str, str, str]:
    from game.unified_semantic_planning import _host_line

    npc = next((row for row in npcs if row.get("id") == turn.get("addressee")), None)
    speaker = str((npc or {}).get("name") or "")
    kind = {
        "DIRECT": "direct",
        "PARTIAL": "partial",
        "CLARIFICATION_REQUIRED": "clarification",
        "RESTRICTED": "refusal",
    }.get(str(turn.get("answer_class")), "unknown")
    fact = authorized_fact(turn, npcs)
    if kind in {"direct", "partial"} and fact:
        body = fact["text"]
        if fact["epistemic"] == "rumor":
            body = "I have heard this as a rumor: " + body
        elif fact["epistemic"] == "belief":
            body = "I believe this, but cannot establish it: " + body
        ambiguity = "addressee" if kind == "clarification" and not turn.get("addressee") else ""
        return kind, _host_line(fact["speaker"] or speaker, kind, body, ambiguity=ambiguity), fact["text"]
    ambiguity = "addressee" if not turn.get("addressee") else ""
    return kind, _host_line(speaker, kind, "", ambiguity=ambiguity), ""


def install_authorized_plan(result: dict, turn: Mapping[str, Any], npcs: list[dict]) -> dict:
    """Replace the locked plan with a host line drawn only from a permitted source."""
    kind, line, authorized = _line_for(turn, npcs)
    if turn.get("answer_class") in {"DIRECT", "PARTIAL"} and not authorized:
        result = deepcopy(result)
        result["gold_plan_blocked"] = "no_permitted_source"
        return result
    result = deepcopy(result)
    plan = dict(result.get("plan") or {})
    fact = authorized_fact(turn, npcs)
    plan.update({
        "response_kind": kind,
        "answer_sufficiency": {"direct": "direct", "partial": "partial", "refusal": "refusal", "clarification": "clarification"}.get(kind, "unknown"),
        "answer_status": {"direct": "direct_answer", "partial": "partial_answer", "clarification": "clarification_required"}.get(kind, kind),
        "host_line": line,
        "authorized_text": authorized,
        "selected_source_ids": [fact["source_id"]] if fact else [],
        "addressee_id": str(turn.get("addressee") or plan.get("addressee_id") or ""),
        "reason": "authorized_" + kind if kind in {"direct", "partial"} else plan.get("reason") or kind,
        "ambiguity_type": "addressee" if kind == "clarification" and not turn.get("addressee") else "",
        "validation_failure": "",
        "gold_intervention": "authorized_plan",
    })
    result["plan"] = plan
    if fact and kind == "direct":
        result["topic_rec"] = {"id": fact["source_id"], "text": fact["text"], "clue_text": fact["text"]}
    result["gold_plan_blocked"] = ""
    return result


def relabel_sufficiency(result: dict, turn: Mapping[str, Any], npcs: list[dict]) -> dict:
    """Downgrade an authorized plan. Never introduce a fact the host did not select."""
    result = deepcopy(result)
    plan = dict(result.get("plan") or {})
    host_kind = str(plan.get("response_kind") or "unknown")
    gold_kind, line, _authorized = _line_for(turn, npcs)
    if DISCLOSURE_RANK.get(gold_kind, 0) > DISCLOSURE_RANK.get(host_kind, 0):
        plan["gold_sufficiency"] = "upgrade_blocked"
        result["plan"] = plan
        return result
    if gold_kind == host_kind:
        plan["gold_sufficiency"] = "unchanged"
        result["plan"] = plan
        return result
    plan["response_kind"] = gold_kind
    plan["answer_sufficiency"] = {"direct": "direct", "partial": "partial", "refusal": "refusal", "clarification": "clarification"}.get(gold_kind, "unknown")
    plan["host_line"] = line
    if gold_kind in {"unknown", "refusal", "clarification"}:
        plan["authorized_text"] = ""
        plan["selected_source_ids"] = []
        result["topic_rec"] = None
    plan["gold_sufficiency"] = "downgraded"
    result["plan"] = plan
    return result


COMPACT_KEYS = {
    "conversational_act",
    "addressee_id",
    "referent_operation",
    "request_proposition",
    "source_propositions",
    "ambiguity_type",
    "clarification_needed",
}


def _compact(plan: Mapping[str, Any]) -> bool:
    """Provider payloads are accepted only when their keys match the proposal schema exactly."""
    return "request_proposition" in plan and "requested_relationship" not in plan


def patch_plan(raw: Mapping[str, Any] | None, turn: Mapping[str, Any], session: Mapping[str, Any] | None, arm: str) -> tuple[dict, dict]:
    """Return a proposal and a trace of which fields the arm changed.

    A compact provider payload must keep exactly the proposal-schema keys.
    Adding interpretation_confidence or proposed_coverage makes production
    reject the whole plan before any later stage runs.
    """
    flags = features(arm)
    plan = deepcopy(dict(raw or {}))
    notes: dict[str, Any] = {"arm": arm, "proposal_source": "baseline_capture" if raw else "skeleton"}
    if not plan:
        plan = {
            "conversational_act": "information_question",
            "addressee_id": str(turn.get("addressee") or ""),
            "referent_operation": empty_operation(),
            "request_proposition": _public_prop(turn.get("proposition")) or {
                "predicate": "attribute",
                "predicate_evidence": "",
                "subject": "",
                "subject_evidence": "",
                "object": "",
                "object_evidence": "",
                "missing_argument": "",
                "temporal": "",
                "spatial": "",
                "epistemic": "npc_knowledge",
                "negated": False,
                "prior_reference": "",
                "roles": [],
                "requested_role": "",
            },
            "source_propositions": [],
            "ambiguity_type": "",
            "clarification_needed": False,
        }
    compact = _compact(plan)
    notes["compact_proposal"] = compact
    if flags["act"]:
        plan["conversational_act"] = turn.get("act") or plan.get("conversational_act")
        plan["clarification_needed"] = bool(turn.get("clarification_required"))
        plan["ambiguity_type"] = "addressee" if turn.get("clarification_required") and not turn.get("addressee") else ""
        if not compact:
            plan["correction_of_prior_question"] = turn.get("act") == "correction"
        notes["act"] = plan["conversational_act"]
    if flags["question"] and turn.get("proposition"):
        plan["request_proposition"] = _public_prop(turn["proposition"])
        if not compact:
            plan["entity_roles"] = []
            argument = next((role["value"] for role in turn.get("roles") or []), "that")
            predicate = str(turn.get("predicate") or "attribute")
            slug = "".join(ch if ch.isalnum() else "_" for ch in argument.casefold()).strip("_") or "that"
            plan["requested_relationship"] = f"{predicate}({slug[:40]})"
            plan["requested_subject"] = argument[:120]
        notes["question"] = turn.get("predicate")
    if flags["source"]:
        rows = []
        for source_id, prop in (turn.get("source_propositions") or {}).items():
            if source_id not in set(turn.get("eligible_source_ids") or []):
                continue
            cleaned = _public_prop(prop)
            if cleaned:
                rows.append({"source_id": source_id, "proposition": cleaned})
        plan["source_propositions"] = rows
        notes["source_ids"] = [row["source_id"] for row in rows]
    if flags["referent"] and isinstance(plan.get("referent_operation"), dict):
        target = resolve_referent(session, turn)
        operation = dict(plan["referent_operation"])
        if turn.get("referent", {}).get("select") == "new":
            for key in operation:
                if key == "changed_fields" or key == "changed_roles":
                    operation[key] = []
                elif isinstance(operation[key], str):
                    operation[key] = ""
        else:
            operation["target_referent_id"] = target
            relation = follow_relationship(str(turn.get("player") or ""))
            if turn.get("act") == "follow_up" and relation and "follow_up_relationship" in operation:
                operation["follow_up_relationship"] = relation
                if "operation" in operation:
                    operation["operation"] = ""
                if "changed_fields" in operation:
                    operation["changed_fields"] = []
        plan["referent_operation"] = operation
        notes["referent_id"] = operation.get("target_referent_id", "")
        notes["referent_resolved"] = bool(notes["referent_id"]) or turn.get("referent", {}).get("select") == "new"
    elif flags["referent"]:
        notes["referent_resolved"] = False
        notes["referent_skipped"] = "operation_absent"
    if flags["correspondence"]:
        labels = [
            {"source_id": source_id, "coverage": label}
            for source_id, label in (turn.get("correspondence") or {}).items()
            if label in {"direct", "partial", "related_but_nonanswer", "unrelated", "unknown"}
        ]
        if compact:
            notes["correspondence"] = "coverage_function_only"
        else:
            plan["proposed_coverage"] = labels
            notes["correspondence"] = [row["source_id"] for row in labels]
    if not compact and "interpretation_confidence" not in plan:
        plan["interpretation_confidence"] = 0.5
    notes["features"] = [name for name, enabled in flags.items() if enabled]
    return plan, notes
