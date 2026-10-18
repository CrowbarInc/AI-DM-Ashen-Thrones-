"""Pre-execution reroute versus post-execution adjudication.

Committed turns are not rewritten and are not rolled back.
"""

from __future__ import annotations

from experiments.pr_dq.envelope import CORRECTION_SUBJECTS, MESSAGE_INTENTS, PlayerMessage
from experiments.pr_dq.route import route_message


def reclassify_message(
    message: PlayerMessage,
    *,
    mode: str | None = None,
    intent: str | None = None,
    correction_subject: str | None = None,
) -> PlayerMessage:
    """Reroute a message that has not committed. Otherwise record adjudication."""
    if message.committed:
        result = dict(message.processing_result)
        result["reclassification"] = "POST_EXECUTION_CORRECTION"
        result["requested_mode"] = mode
        result["requested_intent"] = intent
        result["requested_correction_subject"] = correction_subject
        result["history_rewritten"] = False
        result["state_reverted"] = False
        message.processing_result = result
        message.adjudication_required = True
        return message

    if mode is not None:
        if mode not in {"IC", "OOC", "MIXED", "UNRESOLVED"}:
            raise ValueError("mode is not a known communication mode")
        message.mode = mode
        message.mode_source = "USER_OVERRIDE"
        message.classification_basis = "pre_execution_reclassification"
    if intent is not None:
        if intent not in MESSAGE_INTENTS:
            raise ValueError("intent is not a known message intent")
        message.intent = intent
    if correction_subject is not None:
        if correction_subject not in CORRECTION_SUBJECTS:
            raise ValueError("correction_subject is not a known subject")
        message.correction_subject = correction_subject
    message.committed = False
    message.adjudication_required = False
    route_message(message)
    result = dict(message.processing_result)
    result["reclassification"] = "PRE_EXECUTION"
    result["executed"] = False
    result["resolver_invoked"] = False
    message.processing_result = result
    return message
