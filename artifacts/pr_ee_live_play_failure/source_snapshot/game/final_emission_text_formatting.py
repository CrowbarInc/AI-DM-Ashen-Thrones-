"""Canonical formatting primitives for final emission text.

Whitespace normalization, HTML cleanup, and punctuation helpers. Used by
:mod:`game.final_emission_gate`, :mod:`game.final_emission_finalize`,
:mod:`game.final_emission_validators`, and upstream narrative modules.

BV13A: extracted from ``game.final_emission_text`` compat barrel.
"""
from __future__ import annotations

import re


def _normalize_text(text: str | None) -> str:
    return " ".join(str(text or "").strip().split())


def _normalize_text_preserve_paragraphs(text: str | None) -> str:
    """Like ``_normalize_text`` but keeps ``\\n\\n`` paragraph breaks (strict-social dialogue + NA splits)."""
    raw = str(text or "").strip()
    if not raw:
        return ""
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    if not blocks:
        return ""
    return "\n\n".join(" ".join(part.split()) for part in blocks)


def _sanitize_output_text(text: str) -> str:
    if not text:
        return text

    text = text.replace("<br><br>", "\n\n")
    text = text.replace("<br />", "\n")
    text = text.replace("<br>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _has_terminal_punctuation(text: str) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    if clean[-1] in ".!?":
        return True
    if clean[-1] in "\"')]}”’" and len(clean) > 1 and clean[-2] in ".!?":
        return True
    return False


def _normalize_terminal_punctuation(text: str) -> str:
    clean = _normalize_text(text).strip(" ,;")
    if not clean:
        return ""
    if not _has_terminal_punctuation(clean):
        clean += "."
    return clean


def _capitalize_sentence_fragment(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    chars = list(clean)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.upper()
            break
    return "".join(chars)
