"""Shared fixtures, scoring, and provider settings for the isolated comparison.

Ground truth never comes from an architecture output. Scoring reads only the
case label and the normalized record the adapter already produced.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Mapping

ARTICLE = re.compile(r"^(?:the|a|an)\s+")
PROTECTED_ROLES = {
    "speaker", "recipient", "courier", "excluded", "debtor", "creditor",
    "assigner", "assignee", "sender", "destination", "audience", "agent", "actor",
}


def norm(value: Any) -> str:
    text = " ".join(str(value or "").casefold().split())
    return ARTICLE.sub("", text)


def role_map(roles: list[Mapping[str, Any]] | Mapping[str, Any] | None) -> dict[str, str]:
    if isinstance(roles, Mapping):
        return {str(key): norm(value) for key, value in roles.items() if norm(value)}
    found = {}
    for row in roles or []:
        if isinstance(row, Mapping) and row.get("name") and row.get("value"):
            found[str(row["name"])] = norm(row["value"])
    return found


def build_world(case: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """In-memory fixture. Restricted topics stay on the NPC and are not public."""
    scene_id = "comparison_yard"
    npcs = []
    for person in case["participants"]:
        topics = []
        for source in case.get("sources") or []:
            if source["npc"] == person["id"]:
                topics.append({
                    "id": source["id"], "text": source["text"],
                    "disclosure": "public", "knowledge_status": "known", "epistemic": "npc_knowledge",
                })
        for source in case.get("restricted") or []:
            if source["npc"] == person["id"]:
                topics.append({
                    "id": source["id"], "text": source["text"],
                    "disclosure": "secret", "secret": True, "knowledge_status": "known",
                    "epistemic": "npc_knowledge",
                })
        npcs.append({
            "id": person["id"], "name": person["name"], "location": scene_id,
            "aliases": list(person.get("aliases") or []), "topics": topics,
        })
    world = {"npcs": npcs}
    scene = {"scene": {
        "id": scene_id,
        "summary": case.get("scene") or "A quiet work yard with several people present.",
        "addressables": [{"id": person["id"], "name": person["name"], "kind": "npc", "aliases": person.get("aliases") or []} for person in case["participants"]],
    }}
    conversation_id = case["id"]
    records = []
    active_id = ""
    for index, ref in enumerate(case.get("referents") or [], start=1):
        ident = ref["local_id"]
        roles = [
            {"name": name, "value": value, "entity_id": "", "evidence": value}
            for name, value in (ref.get("roles") or {}).items()
        ]
        proposition = {
            "predicate": ref["predicate"], "predicate_evidence": ref["predicate"],
            "subject": "", "subject_evidence": "", "object": "", "object_evidence": "",
            "missing_argument": "", "temporal": ref.get("temporal") or "",
            "spatial": ref.get("spatial") or "", "epistemic": "npc_knowledge",
            "prior_reference": "", "negated": bool(ref.get("negated")),
            "roles": roles, "requested_role": ref.get("requested") or "",
        }
        record = {
            "referent_id": ident, "conversation_id": "other-conversation" if ref.get("foreign") else conversation_id,
            "originating_turn_id": index, "delivery_id": f"{case['id']}:{ident}",
            "parent_referent_id": "", "revision": 0, "corrected_fields": [],
            "addressee_id": ref["addressee"], "mentioned_entity_ids": [],
            "requested_subject": next(iter((ref.get("roles") or {}).values()), ""),
            "requested_relationship": f"{ref['predicate']}({next(iter((ref.get('roles') or {}).values()), 'that')})",
            "request_proposition": proposition,
            "witness_text": ref["question"], "answer_status": ref.get("status") or "direct",
            "epistemic_status": "npc_knowledge", "semantic_answer_status": ref.get("status") or "direct",
            "missing_roles": [ref["requested"]] if ref.get("requested") and ref.get("status") != "direct" else [],
            "outstanding_clarification": "", "correction_status": "original",
            "focus_status": "active" if ref.get("active") else "superseded",
            "follow_up_relationship": "", "proposition_referent_id": ident,
            "source_plan_id": "", "delivered_speech": ref.get("delivered") or "",
            "operation": {}, "target_proposition": {}, "provenance": "host_interpretation", "canonical": False,
        }
        records.append(record)
        if ref.get("active"):
            active_id = ident
    session = {"conversational_context": {
        "question_referents": {
            "version": 1, "conversation_id": conversation_id, "active_id": active_id,
            "sequence": len(records), "records": records,
        },
        "delivered_exchanges": [
            {
                "speaker_name": next(person["name"] for person in case["participants"] if person["id"] == ref["addressee"]),
                "player_text": ref["question"], "delivered_text": ref.get("delivered") or "",
                "requested_relationship": f"{ref['predicate']}(prior)",
            }
            for ref in case.get("referents") or [] if not ref.get("foreign")
        ],
    }}
    return session, world, scene


def provider_context_for_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Same public context Architecture A builds. Restricted topics are omitted."""
    from game.conversational_referents import context as referent_context
    from game.unified_semantic_planning import (
        _npc_by_id, _scene_summary, _topic_rows, direct_addressees, match_addressees,
        present_participants, prior_semantic_plan,
    )

    session, world, scene = build_world(case)
    utterance = case["utterance"]
    participants = present_participants(world, scene)
    prior = prior_semantic_plan(session)
    named = direct_addressees(utterance, participants) or match_addressees(utterance, participants)
    focus = named[0]["id"] if len(named) == 1 else (str(prior.get("addressee_id") or "") if prior else "")
    npc = _npc_by_id(world, focus) if focus else None
    candidates = []
    for row in _topic_rows(npc):
        if not row["hidden"] and len(row["text"]) <= 800:
            candidates.append({"id": row["id"], "text": row["text"], "epistemic": row["epistemic"]})
    recent = session["conversational_context"]["delivered_exchanges"][-4:]
    return {
        "utterance": utterance,
        "participants": participants,
        "scene_summary": _scene_summary(scene),
        "prior_plan": prior,
        "recent_dialogue": recent,
        "candidates": candidates,
        "referents": referent_context(session),
        "session": session,
        "world": world,
        "scene": scene,
    }


def scrub_player_text(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {
            key: scrub_player_text(value)
            for key, value in payload.items()
            if key not in {"utterance", "player_text", "player", "question_text"}
        }
    if isinstance(payload, list):
        return [scrub_player_text(item) for item in payload]
    return payload


def restricted_leak(payload: Any, case: Mapping[str, Any]) -> list[str]:
    blob = json.dumps(scrub_player_text(payload), ensure_ascii=False).casefold()
    leaked = []
    for source in case.get("restricted") or []:
        text = str(source.get("text") or "")
        if text and text.casefold() in blob:
            leaked.append(text)
    return leaked


def call_provider(messages: list[dict[str, str]], schema: dict[str, Any], name: str) -> dict[str, Any]:
    """One structured call. No retry. Transport and schema failures stay visible."""
    from openai import OpenAI

    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from game.gm import provider_timeout_seconds

    started = time.perf_counter()
    client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
    response = client.responses.create(
        model=DEFAULT_MODEL_NAME,
        input=messages,
        temperature=0,
        max_output_tokens=1800,
        text={"format": {"type": "json_schema", "name": name, "strict": True, "schema": schema}},
    )
    usage_obj = getattr(response, "usage", None)
    raw = getattr(response, "output_text", None) or ""
    return {
        "raw": str(raw),
        "model": str(getattr(response, "model", "") or DEFAULT_MODEL_NAME),
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "usage": {
            "input_tokens": getattr(usage_obj, "input_tokens", None),
            "output_tokens": getattr(usage_obj, "output_tokens", None),
            "total_tokens": getattr(usage_obj, "total_tokens", None),
        },
    }


def empty_normalized(**overrides: Any) -> dict[str, Any]:
    record = {
        "operation": "malformed",
        "referent_target": "",
        "relationship": "",
        "roles": {},
        "requested_role": "",
        "temporal": "",
        "spatial": "",
        "negated": False,
        "transformation": "",
        "follow_up": "",
        "validation": "rejected",
        "validation_reason": "",
        "ambiguity": False,
        "response_class": "unknown",
        "addressee_id": "",
        "authorized_text": "",
        "disclosure_granted": False,
        "selected_source_ids": [],
        "candidate_available": None,
        "selected_candidate": "",
        "candidate_kind": "",
    }
    record.update(overrides)
    return record


def _target_referent(case: Mapping[str, Any]) -> dict[str, Any] | None:
    intended = case["intended"]["referent"]
    if intended in {"", "none", "ambiguous"}:
        return None
    if intended == "active":
        return next((ref for ref in case.get("referents") or [] if ref.get("active")), None)
    return next((ref for ref in case.get("referents") or [] if ref["local_id"] == intended), None)


def _roles_match(expected: dict[str, str], actual: dict[str, str]) -> bool:
    """Protected role names must match. Other slots match by value, so item/object naming does not decide."""
    if sorted(expected.values()) != sorted(actual.values()):
        return False
    for name, value in expected.items():
        if name in PROTECTED_ROLES and actual.get(name) != value:
            return False
    for name, value in actual.items():
        if name in PROTECTED_ROLES and expected.get(name) != value:
            return False
    return True


def _qualifier_ok(actual: str, expected: str, utterance: str) -> bool:
    if norm(expected):
        return norm(actual) == norm(expected)
    if not norm(actual):
        return True
    return norm(actual) in norm(utterance)


def _acceptable(actual: str, expected: str, extras: list[str]) -> bool:
    choices = {norm(expected), *(norm(item) for item in extras)}
    return norm(actual) in choices


def score_case(case: Mapping[str, Any], normalized: Mapping[str, Any]) -> dict[str, Any]:
    """Independent labels only. A safe unknown is not relevance."""
    intended = case["intended"]
    operation = normalized.get("operation") or "malformed"
    expected_operation = intended["operation"]
    malformed = operation == "malformed" or bool(normalized.get("malformed"))
    if intended.get("genuine_ambiguity"):
        operation_correct = (not malformed) and (operation == "clarification" or (normalized.get("response_class") == "clarification"))
    else:
        operation_correct = (not malformed) and operation == expected_operation
    expected_referent = intended["referent"]
    actual_referent = str(normalized.get("referent_target") or "")
    if expected_referent in {"", "none"}:
        referent_correct = actual_referent == ""
        referent_applicable = False
    elif expected_referent == "ambiguous":
        referent_correct = bool(normalized.get("ambiguity")) and actual_referent == ""
        referent_applicable = True
    elif expected_referent == "active":
        active = next((ref["local_id"] for ref in case.get("referents") or [] if ref.get("active")), "")
        referent_correct = actual_referent == active
        referent_applicable = True
    else:
        referent_correct = actual_referent == expected_referent
        referent_applicable = True
    target = _target_referent(case)
    expected_roles = {key: norm(value) for key, value in (intended.get("roles") or {}).items()}
    actual_roles = {key: norm(value) for key, value in (normalized.get("roles") or {}).items()}
    roles_correct = _roles_match(expected_roles, actual_roles)
    predicate_correct = _acceptable(normalized.get("relationship") or "", intended.get("predicate") or "", intended.get("predicate_ok") or [])
    requested_correct = _acceptable(normalized.get("requested_role") or "", intended.get("requested_role") or "", intended.get("requested_ok") or [])
    temporal_correct = _qualifier_ok(str(normalized.get("temporal") or ""), str(intended.get("temporal") or ""), case["utterance"])
    spatial_correct = _qualifier_ok(str(normalized.get("spatial") or ""), str(intended.get("spatial") or ""), case["utterance"])
    negated_correct = bool(normalized.get("negated")) == bool(intended.get("negated"))
    follow_correct = (normalized.get("follow_up") or "") == (intended.get("follow_up") or "")
    accepted = normalized.get("validation") == "accepted"
    genuine = bool(intended.get("genuine_ambiguity"))
    response = normalized.get("response_class") or "unknown"
    false_clarification = (not genuine) and response == "clarification"
    clarification_success = (response == "clarification") if genuine else None
    # Requested-slot names are reported separately. Speaker/recipient style roles stay inside roles_correct.
    meaning_correct = operation_correct and predicate_correct and roles_correct and temporal_correct and spatial_correct and negated_correct
    if expected_operation == "correction":
        correction_success = bool(meaning_correct and referent_correct and accepted and not false_clarification)
        follow_success = None
    elif expected_operation == "follow_up":
        follow_success = bool(meaning_correct and referent_correct and follow_correct and accepted and not false_clarification)
        correction_success = None
    else:
        correction_success = None
        follow_success = None
    if genuine:
        family_success = clarification_success
    elif expected_operation == "correction":
        family_success = correction_success
    elif expected_operation == "follow_up":
        family_success = follow_success
    else:
        family_success = bool(meaning_correct and referent_correct and accepted and not false_clarification)
    expected_source = intended.get("source") or ""
    selected = list(normalized.get("selected_source_ids") or [])
    if expected_source:
        source_correct = selected == [expected_source]
    else:
        source_correct = None
    leaked = list(normalized.get("restricted_leaks") or [])
    authorized = str(normalized.get("authorized_text") or "")
    secret_in_answer = any(str(item.get("text") or "").casefold() in authorized.casefold() for item in case.get("restricted") or [])
    forbidden_hit = any(norm(item) and norm(item) in norm(authorized) for item in intended.get("forbidden_in_answer") or [])
    security_pass = not leaked and not secret_in_answer and not normalized.get("disclosure_granted") and not forbidden_hit
    forbidden_target = actual_referent in set(intended.get("forbidden_targets") or []) and accepted
    if forbidden_target:
        security_pass = False
    candidate_available = normalized.get("candidate_available")
    kind = str(normalized.get("candidate_kind") or "")
    requirement = intended.get("candidate") or ""
    # Selection accuracy excludes turns whose exact candidate was never offered.
    if requirement in {"", "open"} or candidate_available is not True:
        selection_correct = None
    else:
        selection_correct = kind == requirement and accepted and meaning_correct
    return {
        "operation_correct": operation_correct,
        "referent_applicable": referent_applicable,
        "referent_correct": referent_correct if referent_applicable else None,
        "roles_correct": roles_correct,
        "predicate_correct": predicate_correct,
        "requested_correct": requested_correct,
        "follow_correct": follow_correct if expected_operation == "follow_up" else None,
        "correction_success": correction_success,
        "follow_up_success": follow_success,
        "false_clarification": false_clarification,
        "clarification_success": clarification_success,
        "meaning_success": family_success,
        "accepted": accepted,
        "malformed": malformed,
        "source_correct": source_correct,
        "security_pass": security_pass,
        "candidate_available": candidate_available,
        "selection_correct": selection_correct,
        "missing_candidate": requirement not in {"", "open"} and candidate_available is False,
        "target_roles_were": role_map((target or {}).get("roles")),
    }


def earliest_failure(case: Mapping[str, Any], normalized: Mapping[str, Any], scores: Mapping[str, Any]) -> dict[str, str]:
    if scores["malformed"]:
        return {"code": "F07", "owner": "provider", "detail": normalized.get("validation_reason") or "malformed"}
    if not scores["security_pass"]:
        return {"code": "F12", "owner": "provider" if normalized.get("restricted_leaks") else "host", "detail": "disclosure or restricted leak"}
    if scores["false_clarification"]:
        owner = "host" if normalized.get("validation_reason") in {"ambiguous_historical_target", "proposition_ambiguity"} else "provider"
        return {"code": "F09", "owner": owner, "detail": normalized.get("validation_reason") or "clarification"}
    if not scores["operation_correct"]:
        owner = "host" if normalized.get("compiler_disagreed") else "provider"
        return {"code": "F01", "owner": owner, "detail": f"predicted {normalized.get('operation')}"}
    if scores["referent_correct"] is False:
        return {"code": "F02", "owner": "host" if normalized.get("anchor_error") else "provider", "detail": normalized.get("referent_target") or "missing"}
    if not scores["roles_correct"]:
        return {"code": "F03", "owner": "provider", "detail": json.dumps(normalized.get("roles"), ensure_ascii=False)}
    if scores["follow_correct"] is False:
        return {"code": "F06", "owner": "host" if normalized.get("compiler_disagreed") else "provider", "detail": normalized.get("follow_up") or ""}
    if case["intended"]["operation"] == "correction" and not scores["correction_success"]:
        if not scores["accepted"]:
            return {"code": "F08", "owner": "host", "detail": normalized.get("validation_reason") or "rejected"}
        return {"code": "F05", "owner": "provider", "detail": normalized.get("transformation") or ""}
    if case["intended"]["operation"] == "follow_up" and not scores["follow_up_success"]:
        if not scores["accepted"]:
            return {"code": "F08", "owner": "host", "detail": normalized.get("validation_reason") or "rejected"}
        return {"code": "F06", "owner": "provider", "detail": normalized.get("follow_up") or ""}
    if scores["source_correct"] is False:
        return {"code": "F10", "owner": "host", "detail": ",".join(normalized.get("selected_source_ids") or [])}
    if not scores["meaning_success"]:
        return {"code": "F11", "owner": "provider", "detail": normalized.get("response_class") or ""}
    return {"code": "", "owner": "", "detail": ""}
