"""Fallback contract for selective interpretation.

The deterministic reading is kept beside the model proposal. Rejecting the
proposal does not authorize the deterministic reading, and accepting the
proposal does not authorize execution.
"""
from __future__ import annotations

from typing import Any, Mapping

from experiments.pr_dm.authority import (
    CANON_UPDATE,
    DICE,
    DIRECT_HP,
    EXECUTION,
    HIDDEN,
    INVENTORY,
    INVENTED_FACT,
    NPC_COMMITMENT,
    UNSUPPORTED_OP,
)

UNSUPPORTED_REASONS = frozenset(
    {
        DIRECT_HP,
        INVENTED_FACT,
        CANON_UPDATE,
        DICE,
        NPC_COMMITMENT,
        INVENTORY,
        EXECUTION,
        HIDDEN,
        UNSUPPORTED_OP,
    }
)


def _ambiguous(row: Mapping[str, Any], payload: Mapping[str, Any] | None) -> bool:
    checks = row.get("independent_checks") if isinstance(row.get("independent_checks"), Mapping) else {}
    if checks.get("unresolved_personal_pronoun") or checks.get("multiple_plausible_referents"):
        return True
    if not isinstance(payload, Mapping):
        return False
    return bool(
        payload.get("ambiguous")
        or payload.get("clarification_required")
        or str(payload.get("status") or "") == "CLARIFICATION_REQUIRED"
        or payload.get("unresolved_references")
    )


def decide_consumption(
    row: Mapping[str, Any],
    authority: Mapping[str, Any],
    *,
    routed: bool,
) -> dict[str, Any]:
    """Choose what may be retained. Nothing in the result is an execution grant."""
    deterministic = str(row.get("deterministic_gameplay") or "FAIL")
    deterministic_complete = deterministic == "PASS"
    payload = row.get("live_payload") if isinstance(row.get("live_payload"), Mapping) else None
    schema_valid = bool((row.get("live_adapter") or {}).get("accepted")) if routed else False
    authority_valid = bool(authority.get("accepted")) if routed else False
    reasons = list(authority.get("reasons") or []) if routed else []
    live_gameplay = str(row.get("live_gameplay") or row.get("scores", {}).get("gameplay_usefulness") or "FAIL")

    consumed = False
    preserved = False
    clarification = False
    unsupported = False
    abstained = False
    if not routed:
        disposition = "deterministic_unrouted"
        preserved = deterministic_complete
        selected_gameplay = deterministic
        usefulness = "deterministic_interpretation" if deterministic_complete else "missed_complication"
    elif schema_valid and authority_valid:
        disposition = "consume_interpretation"
        consumed = True
        selected_gameplay = live_gameplay
        if live_gameplay == "PASS":
            usefulness = "successful_interpretation"
        elif live_gameplay == "PARTIAL":
            usefulness = "partial_interpretation"
        else:
            usefulness = "incorrect_interpretation"
    elif deterministic_complete:
        disposition = "preserve_deterministic"
        preserved = True
        selected_gameplay = deterministic
        usefulness = "deterministic_interpretation"
    elif any(reason in UNSUPPORTED_REASONS for reason in reasons) or _unsupported_request(row):
        disposition = "unsupported"
        unsupported = True
        selected_gameplay = "FAIL"
        usefulness = "unsupported_action"
    elif _ambiguous(row, payload) and not reasons:
        disposition = "clarification"
        clarification = True
        selected_gameplay = "FAIL"
        usefulness = "clarification"
    else:
        disposition = "safe_abstention"
        abstained = True
        selected_gameplay = "FAIL"
        usefulness = "safe_abstention"

    return {
        "disposition": disposition,
        "routed": routed,
        "schema_valid": schema_valid,
        "authority_valid": authority_valid,
        "authority_reasons": reasons,
        "deterministic_gameplay": deterministic,
        "deterministic_complete": deterministic_complete,
        "consumed_ai": consumed,
        "preserved_deterministic": preserved,
        "clarification": clarification,
        "unsupported": unsupported,
        "abstained": abstained,
        "selected_gameplay": selected_gameplay,
        "interpretation_usefulness": usefulness,
        "execution_success": "not_executed",
        "executed": False,
        "mutated_state": False,
        "authoritative_outcome": False,
        "known_execution_support": False,
    }


def _unsupported_request(row: Mapping[str, Any]) -> bool:
    existing = row.get("existing_signals") if isinstance(row.get("existing_signals"), Mapping) else {}
    return bool(existing.get("unsupported_mechanic") or existing.get("attempted_direct_state_override") or existing.get("attempted_world_canon_declaration"))
