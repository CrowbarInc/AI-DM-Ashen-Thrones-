"""Player-facing rubric.

Ground truth comes from the frozen turn. Engine-selected operations, referents,
sources, and response classes are not treated as truth.
"""

from __future__ import annotations

from typing import Any, Mapping

IGNORANCE = (
    "couldn't tell",
    "could not tell",
    "don't know",
    "do not know",
    "not sure",
    "couldn't answer",
    "could not answer",
    "can't answer",
    "cannot answer",
    "i couldn't tell you",
    "i could not tell you",
)
CLARIFY = (
    "which person",
    "which question",
    "which part",
    "which earlier",
    "which one",
    "which of",
    "do you mean",
    "who do you mean",
    "what do you mean",
)


def _hits(text: str, phrases: list[str]) -> list[str]:
    lowered = text.casefold()
    return [phrase for phrase in phrases if phrase and phrase.casefold() in lowered]


def _any(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(phrase in lowered for phrase in phrases)


def score_reply(turn: Mapping[str, Any], text: str) -> dict[str, Any]:
    body = str(text or "")
    allowed = _hits(body, list(turn.get("allowed") or []))
    forbidden = _hits(body, list(turn.get("forbidden") or []))
    distractors = _hits(body, list(turn.get("distractors") or []))
    hedge_needed = list(turn.get("hedge_any") or [])
    hedge_ok = (not hedge_needed) or bool(_hits(body, hedge_needed))
    ignorance = _any(body, IGNORANCE)
    clarify = _any(body, CLARIFY)
    kind = str(turn.get("answer_class") or "")
    if not body.strip():
        success = False
    elif kind == "DIRECT":
        success = bool(allowed) and not forbidden and hedge_ok
    elif kind == "PARTIAL":
        success = bool(allowed) and not forbidden and not distractors
    elif kind == "UNKNOWN":
        success = ignorance and not forbidden and not allowed and not distractors
    elif kind == "CLARIFICATION_REQUIRED":
        success = clarify and not forbidden and not allowed
    elif kind == "RESTRICTED":
        success = (not forbidden) and (ignorance or clarify)
    elif kind == "RELATED_NONANSWER":
        success = (not forbidden) and (not distractors) and (ignorance or clarify)
    else:
        success = False
    false_uncertainty = kind in {"DIRECT", "PARTIAL"} and ignorance and not allowed
    false_clarification = kind != "CLARIFICATION_REQUIRED" and clarify and not allowed
    if success and " says, " not in body and " says," not in body:
        naturalness = 2
    elif success:
        naturalness = 1
    else:
        naturalness = 0
    return {
        "player_facing_success": success,
        "allowed_hits": allowed,
        "forbidden_hits": forbidden,
        "distractor_hits": distractors,
        "hedge_ok": hedge_ok,
        "ignorance": ignorance,
        "clarification": clarify,
        "false_uncertainty": false_uncertainty,
        "false_clarification": false_clarification,
        "naturalness": naturalness,
        "correct_interpretation": success and kind != "CLARIFICATION_REQUIRED" or (kind == "CLARIFICATION_REQUIRED" and clarify),
        "factual_content": bool(allowed) and not forbidden if kind in {"DIRECT", "PARTIAL"} else not forbidden,
        "appropriate_uncertainty": (not false_uncertainty) and (ignorance if kind == "UNKNOWN" else True),
        "appropriate_clarification": (clarify if kind == "CLARIFICATION_REQUIRED" else not false_clarification),
    }


def engine_class(plan: Mapping[str, Any] | None) -> str:
    plan = plan or {}
    kind = str(plan.get("answer_sufficiency") or plan.get("response_kind") or "")
    reason = str(plan.get("reason") or "")
    if reason == "unauthorized_source" or kind in {"refusal", "restricted"}:
        return "RESTRICTED"
    if kind in {"clarification", "clarification_required"}:
        return "CLARIFICATION_REQUIRED"
    if kind in {"direct", "direct_answer"}:
        return "DIRECT"
    if kind in {"partial", "partial_answer"}:
        return "PARTIAL"
    if any(isinstance(row, Mapping) and row.get("coverage") == "related_but_nonanswer" for row in plan.get("source_relevance") or []):
        return "RELATED_NONANSWER"
    return "UNKNOWN"


def request_predicate(plan: Mapping[str, Any]) -> str:
    prop = plan.get("request_proposition")
    if isinstance(prop, Mapping) and prop.get("predicate"):
        return str(prop.get("predicate") or "")
    relationship = str(plan.get("requested_relationship") or "")
    return relationship.split("(", 1)[0]


def attribute_failure(turn: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    """Earliest causal failure for a failed baseline turn. Success has no first failure."""
    score = row.get("score") or {}
    if score.get("player_facing_success"):
        return {"first": None, "downstream": []}
    plan = row.get("plan") if isinstance(row.get("plan"), Mapping) else {}
    text = str(row.get("text") or "")
    found: list[str] = []
    if not plan:
        found.append("F01")
    else:
        if plan.get("conversational_act") and plan.get("conversational_act") != turn.get("act"):
            found.append("F01")
        if turn.get("addressee") and plan.get("addressee_id") and plan.get("addressee_id") != turn.get("addressee"):
            found.append("F02")
        selected = set(plan.get("selected_source_ids") or [])
        related = {source_id for source_id, label in (turn.get("correspondence") or {}).items() if label == "related_but_nonanswer"}
        direct = {source_id for source_id, label in (turn.get("correspondence") or {}).items() if label == "direct"}
        if selected & related and direct and not (selected & direct):
            found.append("F03")
        predicate = request_predicate(plan)
        if turn.get("predicate") and predicate and predicate != turn.get("predicate"):
            found.append("F04")
        relevance = {}
        for item in plan.get("source_relevance") or []:
            if isinstance(item, Mapping):
                relevance[str(item.get("source_id") or "")] = str(item.get("coverage") or "")
        for source_id, label in (turn.get("correspondence") or {}).items():
            if label in {"direct", "partial"} and source_id not in relevance and source_id not in selected:
                found.append("F05")
                break
        for source_id, label in (turn.get("correspondence") or {}).items():
            got = relevance.get(source_id)
            if label in {"direct", "partial"} and got in {"unknown", "unrelated", "related_but_nonanswer"}:
                found.append("F07")
                break
            if label in {"unknown", "unrelated", "related_but_nonanswer"} and got == "direct":
                found.append("F08")
                break
        if str(plan.get("reason") or "") == "unauthorized_source" and turn.get("answer_class") == "DIRECT":
            found.append("F10")
        mapped = engine_class(plan)
        if mapped != turn.get("answer_class") and not (
            turn.get("answer_class") == "RESTRICTED" and mapped in {"RESTRICTED", "UNKNOWN"}
        ):
            found.append("F11")
        if turn.get("answer_class") != "CLARIFICATION_REQUIRED" and mapped == "CLARIFICATION_REQUIRED":
            found.append("F12")
        if turn.get("answer_class") in {"DIRECT", "PARTIAL"} and mapped in {"UNKNOWN", "RESTRICTED"}:
            found.append("F13")
        authorized = str(plan.get("authorized_text") or "")
        if turn.get("answer_class") in {"DIRECT", "PARTIAL"} and authorized and not _hits(authorized, list(turn.get("allowed") or [])):
            found.append("F14")
        host_line = str(plan.get("host_line") or "")
        if _hits(host_line, list(turn.get("allowed") or [])) and not _hits(text, list(turn.get("allowed") or [])):
            found.append("F15")
    checks = row.get("checks") or {}
    if checks.get("exact") is False:
        found.append("F16")
    if checks.get("history_exact") is False:
        found.append("F17")
    order = [f"F{number:02d}" for number in range(1, 19)]
    first = next((code for code in order if code in found), "F18" if not found else None)
    if first is None and not found:
        first = "F18"
    downstream = [code for code in order if code in found and code != first]
    return {"first": first, "downstream": downstream}
