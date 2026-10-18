"""Logical destinations. Routing does not decide mechanical legality."""

from __future__ import annotations

from experiments.pr_dq.envelope import IC_EXECUTING_DESTINATIONS, PlayerMessage


def route_message(message: PlayerMessage) -> PlayerMessage:
    """Choose a processing destination from mode and intent.

    An IC destination is permission to offer the message to the gameplay
    adapter. It is not permission to change the world. OOC, mixed, and
    unresolved destinations never execute authoritative gameplay.
    """
    if message.mode == "MIXED":
        message.destination = "MIXED_MESSAGE"
        message.status = "AWAITING_CLARIFICATION"
        return message
    if message.mode == "UNRESOLVED":
        message.destination = "CLARIFICATION_REQUIRED"
        message.status = "AWAITING_CLARIFICATION"
        return message
    if message.mode == "OOC":
        destinations = {
            "CORRECTION": "OOC_CORRECTION",
            "RULES_QUERY": "OOC_RULES_QUERY",
            "QUESTION": "OOC_QUESTION",
        }
        destination = destinations.get(message.intent)
        if destination is None:
            message.destination = "CLARIFICATION_REQUIRED"
            message.status = "AWAITING_CLARIFICATION"
            return message
        message.destination = destination
        if message.status == "PENDING":
            message.status = "CLASSIFIED"
        return message
    if message.mode == "IC":
        if message.intent == "ACTION":
            message.destination = "IC_ACTION"
        elif message.intent in {"DIALOGUE", "QUESTION"}:
            message.destination = "IC_DIALOGUE"
        else:
            message.destination = "CLARIFICATION_REQUIRED"
            message.status = "AWAITING_CLARIFICATION"
            return message
        message.status = "CLASSIFIED"
        return message
    message.destination = "CLARIFICATION_REQUIRED"
    message.status = "AWAITING_CLARIFICATION"
    return message


def execution_permitted(message: PlayerMessage) -> bool:
    """True only for an uncommitted IC action or dialogue that is still open."""
    if message.committed or message.adjudication_required:
        return False
    if message.mode != "IC":
        return False
    if message.destination not in IC_EXECUTING_DESTINATIONS:
        return False
    if message.status in {"REJECTED", "AWAITING_CLARIFICATION", "PROCESSED"}:
        return False
    return True
