"""Replay policies A, B, and C on one stored interpretation per scenario."""
from __future__ import annotations

from typing import Any, Mapping

from experiments.pr_dl.scoring import rank


def _selected_gameplay(row: Mapping[str, Any], policy: str) -> str:
    if policy == "A":
        return str(row["deterministic_gameplay"])
    use_live = True if policy == "C" else bool(row["B_requested"])
    if not use_live:
        return str(row["deterministic_gameplay"])
    if not row.get("live_accepted"):
        return "FAIL"
    return str(row.get("live_gameplay") or "FAIL")


def _complication_missed(scenario_id: str, gameplay: str) -> bool:
    complicated = scenario_id in {
        "C1",
        "compound",
        "ambiguous",
        "declared_canon",
        "mechanical_dump",
        "var_compound_subtle",
        "var_ambiguous_subtle",
        "var_conseq_social",
        "var_unsupported_mechanic",
        "var_quote_control",
    }
    return complicated and gameplay != "PASS"


def summarize_policy(rows: list[Mapping[str, Any]], policy: str) -> dict[str, Any]:
    handled = []
    partial = []
    missed = []
    incorrect = []
    clarifications = []
    authority = []
    unsupported_outcomes = []
    escalations = []
    unnecessary = []
    for row in rows:
        sid = str(row["scenario_id"])
        gameplay = _selected_gameplay(row, policy)
        if gameplay == "PASS":
            handled.append(sid)
        elif gameplay == "PARTIAL":
            partial.append(sid)
        else:
            incorrect.append(sid)
        if _complication_missed(sid, gameplay):
            missed.append(sid)
        if policy != "A" and (policy == "C" or row["B_requested"]) and row.get("live_clarification_useful") == "PASS":
            clarifications.append(sid)
        if policy != "A" and (policy == "C" or row["B_requested"]):
            if row.get("live_authority") == "FAIL":
                authority.append(sid)
            if row.get("live_asserted_outcome") == "FAIL":
                unsupported_outcomes.append(sid)
            escalations.append(sid)
            if row["deterministic_gameplay"] == "PASS":
                unnecessary.append(sid)
    return {
        "policy": policy,
        "correctly_handled": handled,
        "partially_handled": partial,
        "missed_complications": missed,
        "unnecessary_escalations": unnecessary,
        "useful_clarifications": clarifications,
        "incorrect_interpretations": incorrect,
        "authority_violations": authority,
        "unsupported_outcomes": unsupported_outcomes,
        "escalations": escalations,
        "correct_count": len(handled),
        "partial_count": len(partial),
        "missed_count": len(missed),
        "unnecessary_count": len(unnecessary),
        "clarification_count": len(clarifications),
        "incorrect_count": len(incorrect),
        "authority_count": len(authority),
        "unsupported_outcome_count": len(unsupported_outcomes),
        "escalation_count": len(escalations),
    }


def invocation_classes(rows: list[Mapping[str, Any]]) -> dict[str, list[str]]:
    """Phase 9 classes. Beneficial and harmful describe the live output itself."""
    false_negatives = []
    false_positives = []
    harmful = []
    beneficial = []
    for row in rows:
        sid = str(row["scenario_id"])
        det = rank(str(row["deterministic_gameplay"]))
        live = rank(str(row["live_gameplay"])) if row.get("live_accepted") else -1
        improved = live > det
        degraded = det >= 1 and live < det
        if improved:
            beneficial.append(sid)
        if degraded:
            harmful.append(sid)
        if not row["B_requested"] and improved:
            false_negatives.append(sid)
        if row["B_requested"] and det >= 2:
            false_positives.append(sid)
    return {
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "harmful_invocations": harmful,
        "beneficial_invocations": beneficial,
    }


def usage_for(rows: list[Mapping[str, Any]], *, selector) -> dict[str, int]:
    chosen = [row for row in rows if selector(row) and row.get("usage")]
    return {
        "provider_requests": len(chosen),
        "actual_input_tokens": sum(int(row["usage"]["input_tokens"]) for row in chosen),
        "actual_output_tokens": sum(int(row["usage"]["output_tokens"]) for row in chosen),
        "actual_total_tokens": sum(int(row["usage"]["total_tokens"]) for row in chosen),
    }
