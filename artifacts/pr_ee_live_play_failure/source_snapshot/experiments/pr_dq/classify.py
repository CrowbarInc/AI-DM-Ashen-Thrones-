"""Deterministic mode classification. This is not an AI classifier.

Explicit caller overrides win. Explicit IC/OOC markers are recognized.
Anything else stays UNRESOLVED. Intent is caller-supplied or OTHER.
"""

from __future__ import annotations

import re

from experiments.pr_dq.envelope import (
    CORRECTION_SUBJECTS,
    MESSAGE_INTENTS,
    MODE_OVERRIDES,
    PlayerMessage,
)
from experiments.pr_dq.route import route_message

_OOC_MARK = re.compile(r"(?:^|[\s(])(?:ooc|out of character)\s*:", re.IGNORECASE)
_IC_MARK = re.compile(r"(?:^|[\s(])(?:ic|in character)\s*:", re.IGNORECASE)
_OOC_LEADING = re.compile(r"\s*(?:ooc|out of character)\s*:", re.IGNORECASE)
_IC_LEADING = re.compile(r"\s*(?:ic|in character)\s*:", re.IGNORECASE)


def _marked(pattern: re.Pattern[str], text: str) -> bool:
    return pattern.search(text) is not None


def classify_mode(text: str, mode_override: str) -> tuple[str, str, str]:
    """Return mode, mode source, and a short basis label.

    A non-leading explicit marker means the utterance contains both a lead-in
    and a marked clause. That is deferred as MIXED. No default IC is applied.
    """
    if mode_override not in MODE_OVERRIDES:
        raise ValueError("mode_override must be AUTO, IC, or OOC")
    if mode_override in {"IC", "OOC"}:
        return mode_override, "USER_OVERRIDE", "user_override"

    ooc_any = _marked(_OOC_MARK, text)
    ic_any = _marked(_IC_MARK, text)
    ooc_leading = _OOC_LEADING.match(text) is not None
    ic_leading = _IC_LEADING.match(text) is not None
    if (ooc_any and ic_any) or (ooc_any and not ooc_leading) or (ic_any and not ic_leading):
        return "MIXED", "AUTO", "mixed_explicit_markers"
    if ooc_leading:
        return "OOC", "AUTO", "explicit_ooc_prefix"
    if ic_leading:
        return "IC", "AUTO", "explicit_ic_prefix"
    return "UNRESOLVED", "AUTO", "no_explicit_mode"


def ingest_player_message(
    text: str,
    *,
    message_id: str,
    mode_override: str = "AUTO",
    intent: str | None = None,
    correction_subject: str = "NONE",
) -> PlayerMessage:
    """Build one envelope, classify its mode, and route it. Does not execute."""
    if intent is None:
        intent = "OTHER"
    if intent not in MESSAGE_INTENTS:
        raise ValueError("intent is not a known message intent")
    if correction_subject not in CORRECTION_SUBJECTS:
        raise ValueError("correction_subject is not a known subject")
    mode, source, basis = classify_mode(text, mode_override)
    message = PlayerMessage(
        message_id=message_id,
        text=text,
        mode=mode,
        mode_source=source,
        intent=intent,
        status="CLASSIFIED" if mode in {"IC", "OOC"} else "AWAITING_CLARIFICATION",
        requested_override=mode_override,
        correction_subject=correction_subject,
        classification_basis=basis,
    )
    return route_message(message)
