"""Player-message envelope for the experimental boundary.

IC and OOC are properties of one message. They are not separate conversations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


COMMUNICATION_MODES = frozenset({"IC", "OOC", "MIXED", "UNRESOLVED"})
MODE_SOURCES = frozenset({"AUTO", "USER_OVERRIDE", "SYSTEM_DEFAULT"})
MODE_OVERRIDES = frozenset({"AUTO", "IC", "OOC"})
MESSAGE_INTENTS = frozenset(
    {
        "ACTION",
        "DIALOGUE",
        "QUESTION",
        "CORRECTION",
        "RULES_QUERY",
        "CLARIFICATION",
        "OTHER",
    }
)
PROCESSING_STATUSES = frozenset(
    {
        "PENDING",
        "CLASSIFIED",
        "AWAITING_CLARIFICATION",
        "PROCESSED",
        "REJECTED",
    }
)
DESTINATIONS = frozenset(
    {
        "IC_ACTION",
        "IC_DIALOGUE",
        "OOC_QUESTION",
        "OOC_CORRECTION",
        "OOC_RULES_QUERY",
        "CLARIFICATION_REQUIRED",
        "MIXED_MESSAGE",
    }
)
CORRECTION_SUBJECTS = frozenset({"NONE", "REFERENT", "INTENTION", "COMMITTED_ACTION"})

IC_EXECUTING_DESTINATIONS = frozenset({"IC_ACTION", "IC_DIALOGUE"})


def _require(value: str, allowed: frozenset[str], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"{label} must be one of {sorted(allowed)}")
    return value


@dataclass
class PlayerMessage:
    """One player utterance and the metadata needed to route it.

    ``text`` stays the original input. Routing updates this object in place
    and does not copy it into another history.
    """

    message_id: str
    text: str
    mode: str
    mode_source: str
    intent: str
    status: str
    requested_override: str = "AUTO"
    destination: str = ""
    correction_subject: str = "NONE"
    classification_basis: str = ""
    processing_result: dict[str, Any] = field(default_factory=dict)
    committed: bool = False
    adjudication_required: bool = False

    def __post_init__(self) -> None:
        if not str(self.message_id).strip():
            raise ValueError("message_id is required")
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")
        _require(self.mode, COMMUNICATION_MODES, "mode")
        _require(self.mode_source, MODE_SOURCES, "mode_source")
        _require(self.intent, MESSAGE_INTENTS, "intent")
        _require(self.status, PROCESSING_STATUSES, "status")
        _require(self.requested_override, MODE_OVERRIDES, "requested_override")
        _require(self.correction_subject, CORRECTION_SUBJECTS, "correction_subject")
        if self.destination:
            _require(self.destination, DESTINATIONS, "destination")

    def to_record(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "text": self.text,
            "mode": self.mode,
            "mode_source": self.mode_source,
            "intent": self.intent,
            "status": self.status,
            "destination": self.destination,
            "requested_override": self.requested_override,
            "classification_basis": self.classification_basis,
            "correction_subject": self.correction_subject,
            "committed": self.committed,
            "adjudication_required": self.adjudication_required,
            "processing_result": self.processing_result,
        }
