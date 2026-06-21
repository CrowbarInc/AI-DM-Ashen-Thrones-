"""Narrow emitted-speaker signature parsing.

This module owns text-level detection of opening speaker attribution and dialogue
ownership cues. Final-emission gate orchestration may consume and re-export this
helper for compatibility, but gate layer order and speaker enforcement semantics
remain owned elsewhere.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from game.final_emission_text_formatting import _normalize_text
from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS
from game.social_exchange_validation import has_explicit_interruption_shape
from game.social_exchange_projection import interruption_cue_present_in_text

_SPEECH_VERB_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|asks|asked|adds|added)\b",
    re.IGNORECASE,
)
_BEAT_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
_QUOTED_THEN_PRONOUN_SPEECH_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|"
    r"asks|asked|adds|added|insists|insisted)\b",
    re.IGNORECASE,
)
_QUOTED_THEN_PRONOUN_BEAT_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
_NON_NAME_ATTRIBUTION_PREFIXES = frozenset(
    {
        "he",
        "she",
        "they",
        "it",
        "someone",
        "a voice",
        "the voice",
        "another voice",
    }
)


def _is_generic_fallback_label(speaker_label: str | None) -> bool:
    if not speaker_label:
        return False
    sl = speaker_label.strip().lower()
    for fb in SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS:
        fbl = str(fb or "").strip().lower()
        if fbl and (fbl == sl or fbl in sl or sl in fbl):
            return True
    return False


def detect_emitted_speaker_signature(
    text: str,
    resolution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Infer opening attribution / dialogue-ownership cues from emitted text."""
    t = _normalize_text(text)
    speaker_label: str | None = None
    speaker_name: str | None = None
    is_explicit = False
    confidence: str = "low"

    mq = _QUOTED_THEN_PRONOUN_SPEECH_RE.match(t)
    if not mq:
        mq = _QUOTED_THEN_PRONOUN_BEAT_RE.match(t)
    if mq:
        raw = str(mq.group(1) or "").strip()
        low = raw.lower()
        speaker_label = raw
        if low and low not in _NON_NAME_ATTRIBUTION_PREFIXES:
            speaker_name = raw
            is_explicit = True
            confidence = "high"
        elif raw:
            confidence = "medium"
        intr = bool(interruption_cue_present_in_text(t) or has_explicit_interruption_shape(t))
        return {
            "speaker_name": speaker_name,
            "speaker_label": speaker_label,
            "is_explicitly_attributed": is_explicit,
            "is_generic_fallback_label": _is_generic_fallback_label(speaker_label),
            "has_interruption_framing": intr,
            "confidence": confidence,
        }

    m = _SPEECH_VERB_ATTRIBUTION_RE.match(t)
    if not m:
        m = _BEAT_ATTRIBUTION_RE.match(t)
    if m:
        raw = str(m.group(1) or "").strip()
        low = raw.lower()
        if raw and low not in _NON_NAME_ATTRIBUTION_PREFIXES and not low.startswith(
            tuple(p + " " for p in _NON_NAME_ATTRIBUTION_PREFIXES)
        ):
            speaker_label = raw
            speaker_name = raw
            is_explicit = True
            confidence = "high"
        elif raw:
            speaker_label = raw
            confidence = "medium"

    intr = bool(interruption_cue_present_in_text(t) or has_explicit_interruption_shape(t))

    return {
        "speaker_name": speaker_name,
        "speaker_label": speaker_label,
        "is_explicitly_attributed": is_explicit,
        "is_generic_fallback_label": _is_generic_fallback_label(speaker_label),
        "has_interruption_framing": intr,
        "confidence": confidence,
    }
