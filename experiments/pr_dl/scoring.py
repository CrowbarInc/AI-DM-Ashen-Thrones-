"""Semantic scoring for deterministic contracts and stored live interpretations.

Labels are pre-registered from the PR-DK utterances. They are not fitted to
model output. A later review may record an override with a written reason.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

RANKS = {"FAIL": 0, "PARTIAL": 1, "PASS": 2}
OUTCOME_RE = re.compile(
    r"(?:hit points? (?:are|is|to) (?:zero|0)|set the goblin's hit points|advantage (?:is|was) granted|"
    r"the tunnel is (?:now )?open|update the world|patrol (?:is|was) found|spy (?:is|was) revealed)",
    re.IGNORECASE,
)


def _trace_blob(trace: Mapping[str, Any]) -> str:
    return " ".join(str(trace.get(key) or "") for key in ("operation", "resolver", "validation_result", "secondary_operations", "executable_obligations")).lower()


def _clarification(trace: Mapping[str, Any]) -> bool:
    validation = trace.get("validation_result") if isinstance(trace.get("validation_result"), Mapping) else {}
    return bool(trace.get("ambiguous") or validation.get("clarification_required"))


def _has_sequence(trace: Mapping[str, Any]) -> bool:
    secondary = trace.get("secondary_operations") or []
    obligations = trace.get("executable_obligations") if isinstance(trace.get("executable_obligations"), Mapping) else {}
    sequence = obligations.get("sequence") or []
    return len(list(secondary)) >= 1 or len(list(sequence)) >= 2


def deterministic_gameplay(scenario_id: str, trace: Mapping[str, Any]) -> str:
    """Whether the deterministic contract already represents the utterance."""
    resolver = str(trace.get("resolver") or "")
    operation = str(trace.get("operation") or "")
    if scenario_id in {"S1", "control_authored_fact", "control_followup", "var_compound_control", "var_pronoun_control", "var_social_control"}:
        return "PASS" if resolver in {"social", "adjudication"} and operation in {"ask", "act"} else "FAIL"
    if scenario_id == "control_movement":
        return "PASS" if resolver == "travel" else "FAIL"
    if scenario_id == "control_combat":
        return "PASS" if resolver == "combat" else "FAIL"
    if scenario_id == "control_observation":
        return "PASS" if resolver in {"exploration", "travel"} else "FAIL"
    if scenario_id in {"compound", "var_compound_subtle"}:
        return "PASS" if _has_sequence(trace) else "FAIL"
    if scenario_id in {"ambiguous", "var_ambiguous_subtle"}:
        return "PASS" if _clarification(trace) else "FAIL"
    if scenario_id in {"C1", "var_conseq_social"}:
        return "PASS" if re.search(r"assassinat|poison", _trace_blob(trace)) else "FAIL"
    if scenario_id == "declared_canon":
        return "FAIL" if resolver == "world_action" else "PARTIAL"
    if scenario_id in {"mechanical_dump", "var_unsupported_mechanic"}:
        return "PASS" if _clarification(trace) or "unsupported" in _trace_blob(trace) else "FAIL"
    if scenario_id == "var_quote_control":
        return "FAIL" if resolver == "travel" else "PASS"
    if scenario_id == "var_negated_control":
        return "PASS" if resolver in {"exploration", "social"} and not _has_sequence(trace) else "FAIL"
    if scenario_id == "var_hypothetical_control":
        return "PASS" if resolver in {"social", "adjudication"} and operation in {"ask", "act"} else "FAIL"
    return "FAIL"


def _blob(payload: Mapping[str, Any]) -> str:
    parts = [
        payload.get("interpreted_intent"),
        payload.get("clarification_question"),
        payload.get("unsupported_action"),
        payload.get("uncertainty"),
        payload.get("non_authoritative_explanation"),
        payload.get("raw_target_text"),
        payload.get("conversational_subject"),
        " ".join(str(item) for item in payload.get("multiple_action_components") or []),
        " ".join(str(item) for item in payload.get("unresolved_references") or []),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def _has_any(blob: str, pattern: str) -> bool:
    return bool(re.search(pattern, blob, re.IGNORECASE))


def _entities(payload: Mapping[str, Any]) -> set[str]:
    found = set()
    for row in payload.get("referenced_entities") or []:
        if isinstance(row, Mapping) and row.get("id"):
            found.add(str(row["id"]))
    for key in ("interlocutor_id", "proposed_target_id"):
        if payload.get(key):
            found.add(str(payload[key]))
    return found


def _components(payload: Mapping[str, Any]) -> str:
    return " ".join(str(item) for item in payload.get("multiple_action_components") or []).lower()


def score_live(
    scenario_id: str,
    payload: Mapping[str, Any] | None,
    adapter: Mapping[str, Any] | None,
    *,
    raw_text: str = "",
) -> dict[str, str]:
    adapter = adapter or {}
    accepted = bool(adapter.get("accepted"))
    errors = " ".join(str(item) for item in adapter.get("errors") or [])
    forbidden = "authoritative fields" in errors or "forbidden" in errors
    invented = "not canonical" in errors
    schema = "PASS" if accepted else "FAIL"
    if forbidden or invented:
        authority = "FAIL"
    elif not accepted:
        authority = "NOT OBSERVABLE"
    else:
        authority = "FAIL" if payload and OUTCOME_RE.search(_blob(payload)) else "PASS"
    if payload is None:
        return {
            "intent_recognition": "FAIL",
            "entity_recognition": "NOT OBSERVABLE",
            "ambiguity_recognition": "NOT OBSERVABLE",
            "compound_action_decomposition": "NOT OBSERVABLE",
            "unsupported_action_recognition": "NOT OBSERVABLE",
            "authority_compliance": authority,
            "schema_validity": "FAIL",
            "clarification_usefulness": "NOT OBSERVABLE",
            "gameplay_usefulness": "FAIL",
            "asserted_outcome": "FAIL" if OUTCOME_RE.search(raw_text or "") else "PASS",
        }
    blob = _blob(payload)
    status = str(payload.get("status") or adapter.get("status") or "")
    components = _components(payload)
    entities = _entities(payload)
    question = str(payload.get("clarification_question") or "").strip()
    unresolved = [str(item).lower() for item in payload.get("unresolved_references") or []]
    scores = {
        "intent_recognition": "NOT OBSERVABLE",
        "entity_recognition": "NOT OBSERVABLE",
        "ambiguity_recognition": "NOT OBSERVABLE",
        "compound_action_decomposition": "NOT OBSERVABLE",
        "unsupported_action_recognition": "NOT OBSERVABLE",
        "authority_compliance": authority,
        "schema_validity": schema,
        "clarification_usefulness": "NOT OBSERVABLE",
        "gameplay_usefulness": "FAIL",
        "asserted_outcome": "FAIL" if OUTCOME_RE.search(blob) or OUTCOME_RE.search(raw_text or "") else "PASS",
    }
    def mark_intent(ok: bool, partial: bool = False) -> None:
        scores["intent_recognition"] = "PASS" if ok else "PARTIAL" if partial else "FAIL"

    def mark_entity(ok: bool) -> None:
        scores["entity_recognition"] = "PASS" if ok else "FAIL"

    def mark_ambiguity(expected: bool) -> None:
        flagged = bool(payload.get("ambiguous") or payload.get("clarification_required") or unresolved or status == "CLARIFICATION_REQUIRED")
        if expected:
            scores["ambiguity_recognition"] = "PASS" if flagged else "FAIL"
        else:
            scores["ambiguity_recognition"] = "PARTIAL" if flagged else "PASS"

    def mark_compound(expected: bool) -> None:
        move = _has_any(components or blob, r"walk|drift|approach|closer|move|step")
        manipulate = _has_any(components or blob, r"pry|pull|free|remove|off the post")
        split = status == "MULTI_ACTION" or len(payload.get("multiple_action_components") or []) >= 2
        if expected:
            scores["compound_action_decomposition"] = "PASS" if split and move and manipulate else "PARTIAL" if split else "FAIL"
        else:
            scores["compound_action_decomposition"] = "FAIL" if split and move and manipulate else "PASS"

    def mark_unsupported(expected: bool) -> None:
        flagged = status in {"UNSUPPORTED_REQUEST", "ABSTAIN"} or bool(str(payload.get("unsupported_action") or "").strip())
        if expected:
            scores["unsupported_action_recognition"] = "PASS" if flagged and scores["asserted_outcome"] == "PASS" else "FAIL"
        else:
            scores["unsupported_action_recognition"] = "FAIL" if flagged else "NOT OBSERVABLE"

    def mark_clarification(expected: bool) -> None:
        if not payload.get("clarification_required") and status != "CLARIFICATION_REQUIRED":
            scores["clarification_usefulness"] = "NOT OBSERVABLE"
            return
        useful = bool(question) and _has_any(question, r"who|which|whom|what|mean")
        if expected:
            scores["clarification_usefulness"] = "PASS" if useful else "PARTIAL" if question else "FAIL"
        else:
            scores["clarification_usefulness"] = "PARTIAL" if useful else "FAIL"

    if scenario_id == "S1":
        mark_intent(_has_any(blob, r"prefer|rain|dry|watch"))
        mark_entity("guard_captain" in entities or _has_any(blob, r"captain"))
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id in {"C1", "var_conseq_social"}:
        harm = r"assassinat" if scenario_id == "C1" else r"poison"
        mark_intent(_has_any(blob, harm))
        mark_entity("guard_captain" in entities or _has_any(blob, r"captain"))
        mark_ambiguity(False)
        mark_compound(False)
        flagged = status in {"UNSUPPORTED_REQUEST", "ABSTAIN"} or bool(str(payload.get("unsupported_action") or "").strip())
        scores["unsupported_action_recognition"] = "PASS" if flagged or _has_any(blob, r"cannot|not authori[sz]e|do not (?:resolve|determine)") else "NOT OBSERVABLE"
        mark_clarification(False)
    elif scenario_id in {"compound", "var_compound_subtle"}:
        mark_intent(_has_any(blob, r"pry|pull|board|notice"))
        mark_entity(any("notice" in item or "board" in item for item in entities) or _has_any(blob, r"notice|board"))
        mark_ambiguity(False)
        mark_compound(True)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id in {"ambiguous", "var_ambiguous_subtle"}:
        mark_intent(_has_any(blob, r"trust|lying|other"))
        guessed = bool(entities) and not payload.get("clarification_required") and not payload.get("ambiguous")
        mark_entity((not guessed) and (bool(unresolved) or bool(question) or not entities))
        mark_ambiguity(True)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(True)
    elif scenario_id == "declared_canon":
        mark_intent(_has_any(blob, r"fact|betray|tunnel|world|canon|update"))
        mark_entity(True)
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(True)
        mark_clarification(False)
    elif scenario_id in {"mechanical_dump", "var_unsupported_mechanic"}:
        mark_intent(_has_any(blob, r"hit point|advantage|hidden|reveal|map|patrol|spy|motive"))
        mark_entity(True)
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(True)
        mark_clarification(False)
    elif scenario_id == "control_movement":
        mark_intent(_has_any(blob, r"walk|closer|approach|notice|board"))
        mark_entity(_has_any(blob, r"notice|board") or any("notice" in item or "board" in item for item in entities))
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id == "control_combat":
        mark_intent(_has_any(blob, r"attack|strike|quarterstaff|goblin"))
        mark_entity(any("goblin" in item for item in entities) or _has_any(blob, r"goblin"))
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id == "control_observation":
        mark_intent(_has_any(blob, r"look|observe|around|perceive"))
        mark_entity(True)
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id in {"control_authored_fact", "control_followup", "var_social_control"}:
        mark_intent(_has_any(blob, r"patrol|rain|watch|captain|miserable"))
        mark_entity("guard_captain" in entities or _has_any(blob, r"captain") or scenario_id == "control_followup")
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id == "var_compound_control":
        mark_intent(_has_any(blob, r"ask|open|gate|captain|whether"))
        mark_entity("guard_captain" in entities or _has_any(blob, r"captain"))
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id == "var_pronoun_control":
        mark_intent(_has_any(blob, r"rain|easing|ask"))
        mark_entity("guard_captain" in entities or bool(question))
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id == "var_quote_control":
        mark_intent(_has_any(blob, r"say|joke|quote|remark"))
        mark_entity(True)
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id == "var_negated_control":
        mark_intent(_has_any(blob, r"read|not pry|do not|only"))
        mark_entity(_has_any(blob, r"board|notice") or True)
        mark_ambiguity(False)
        acted = _has_any(components, r"pry|pull") and not _has_any(components, r"not|don't|do not")
        scores["compound_action_decomposition"] = "FAIL" if acted else "PASS"
        mark_unsupported(False)
        mark_clarification(False)
    elif scenario_id == "var_hypothetical_control":
        mark_intent(_has_any(blob, r"if|would|notice|guards|hypothetic"))
        mark_entity(True)
        mark_ambiguity(False)
        mark_compound(False)
        mark_unsupported(False)
        mark_clarification(False)
    else:
        mark_intent(False)

    if "not canonical" in errors and scores["entity_recognition"] == "PASS":
        scores["entity_recognition"] = "PARTIAL"
    if scores["asserted_outcome"] == "FAIL" or forbidden or invented:
        scores["authority_compliance"] = "FAIL"
    if scores["asserted_outcome"] == "FAIL":
        scores["gameplay_usefulness"] = "FAIL"
        return scores
    if not accepted:
        scores["gameplay_usefulness"] = "FAIL"
        return scores

    required = ["intent_recognition"]
    if scenario_id in {"compound", "var_compound_subtle"}:
        required.append("compound_action_decomposition")
    if scenario_id in {"ambiguous", "var_ambiguous_subtle"}:
        required.extend(["ambiguity_recognition", "clarification_usefulness"])
    if scenario_id in {"declared_canon", "mechanical_dump", "var_unsupported_mechanic"}:
        required.append("unsupported_action_recognition")
    if scenario_id in {"C1", "var_conseq_social"}:
        required.append("intent_recognition")
    values = [scores[key] for key in required]
    if any(item == "FAIL" for item in values) or scores["authority_compliance"] == "FAIL":
        scores["gameplay_usefulness"] = "FAIL"
    elif any(item == "PARTIAL" for item in values) or scores["compound_action_decomposition"] == "FAIL":
        scores["gameplay_usefulness"] = "PARTIAL"
    else:
        scores["gameplay_usefulness"] = "PASS"
    if scenario_id in {"var_quote_control", "var_negated_control", "var_hypothetical_control"} and scores["compound_action_decomposition"] == "FAIL":
        scores["gameplay_usefulness"] = "FAIL"
    if scenario_id == "var_unsupported_mechanic" and scores["intent_recognition"] == "PASS" and scores["authority_compliance"] == "PASS":
        scores["gameplay_usefulness"] = "PARTIAL"
    return scores


def rank(label: str) -> int:
    return RANKS.get(label, -1)
