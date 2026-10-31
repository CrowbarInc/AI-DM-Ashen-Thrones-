"""Legacy semantic sentence-repair helpers (test-only).

**Not invoked at the C2 packaging-only final-emission boundary.** Retained for
unit tests that assert the repair predicates remain stable. Canonical formatting
primitives live in :mod:`game.final_emission_text_formatting`.

BV13A: isolated from ``game.final_emission_text`` compat barrel.
"""
from __future__ import annotations

import re
from typing import Dict, List

from game.final_emission_text_formatting import (
    _capitalize_sentence_fragment,
    _has_terminal_punctuation,
    _normalize_terminal_punctuation,
    _normalize_text,
)

_PARTICIPIAL_BASE_VERBS: Dict[str, str] = {
    "intertwining": "intertwine",
    "drawing": "draw",
    "hinting": "hint",
    "suggesting": "suggest",
    "making": "make",
    "indicating": "indicate",
    "offering": "offer",
    "creating": "create",
    "revealing": "reveal",
    "urging": "urge",
    "watching": "watch",
    "cutting": "cut",
}
_PARTICIPIAL_THIRD_PERSON: Dict[str, str] = {
    "intertwining": "intertwines",
    "drawing": "draws",
    "hinting": "hints",
    "suggesting": "suggests",
    "making": "makes",
    "indicating": "indicates",
    "offering": "offers",
    "creating": "creates",
    "revealing": "reveals",
    "urging": "urges",
    "watching": "watches",
    "cutting": "cuts",
}
_IMPLICATION_PARTICIPLES = {"hinting", "indicating", "revealing"}


def _looks_like_participial_fragment(text: str) -> bool:
    clean = _normalize_text(text).strip()
    if not clean:
        return False
    core = clean.rstrip(".!?").strip(" ,;")
    if not core:
        return False

    words = re.findall(r"[A-Za-z][A-Za-z'-]*", core)
    if len(words) < 3 or len(words) > 22:
        return False

    first = words[0].lower()
    if not first.endswith("ing"):
        return False
    if first not in _PARTICIPIAL_BASE_VERBS:
        return False

    # Avoid touching already-complete short clauses.
    early = " ".join(words[:7]).lower()
    finite_markers = (
        " is ",
        " are ",
        " was ",
        " were ",
        " has ",
        " have ",
        " had ",
        " does ",
        " do ",
        " did ",
        " will ",
        " can ",
        " could ",
        " should ",
        " would ",
        " must ",
    )
    early_padded = f" {early} "
    if any(marker in early_padded for marker in finite_markers):
        return False

    if re.match(r"^(?:as|because|if|when|while|although)\b", core, flags=re.IGNORECASE):
        return False
    return True


def _has_single_actor_anchor(previous_sentence: str) -> bool:
    prev = _normalize_text(previous_sentence).rstrip(".!?")
    if not prev:
        return False
    lowered = prev.lower()

    if any(token in lowered for token in (" and ", " both ", " together ", " alongside ", " two ", " several ")):
        return False
    if any(token in lowered for token in (" they ", " we ", " them ", " their ", " voices ")):
        return False

    singular_signal = re.search(
        r"\b(?:is|was|calls|shouts|offers|watches|studies|lingers|gestures|waits|leans|stands|speaks|says)\b",
        lowered,
    )
    plural_signal = re.search(r"\b(?:are|were|call|shout|offer|watch|study|linger|gesture|wait|speak|say)\b", lowered)
    if plural_signal and not singular_signal:
        return False
    return singular_signal is not None


def _departicipialize_clause(fragment_clause: str, *, subject: str, third_person: bool = False) -> str:
    clause = _normalize_text(fragment_clause).strip(" ,;")
    match = re.match(r"^([A-Za-z][A-Za-z'-]*ing)\b(.*)$", clause, flags=re.IGNORECASE)
    if not match:
        return ""
    participle = match.group(1).lower()
    remainder = _normalize_text(match.group(2))
    verb = _PARTICIPIAL_THIRD_PERSON.get(participle) if third_person else _PARTICIPIAL_BASE_VERBS.get(participle)
    if not verb:
        return ""
    if remainder:
        return _normalize_terminal_punctuation(f"{subject} {verb}{(' ' + remainder) if not remainder.startswith(',') else remainder}")
    return _normalize_terminal_punctuation(f"{subject} {verb}")


def _repair_participial_fragment(previous_sentence: str, fragment: str) -> str | None:
    clean_fragment = _normalize_text(fragment)
    if not _looks_like_participial_fragment(clean_fragment):
        return None

    core = clean_fragment.rstrip(".!?").strip(" ,;")
    if not core:
        return None
    if re.search(r"\b(he|she|him|his)\b", core, flags=re.IGNORECASE):
        return None
    parts = [part.strip(" ,;") for part in core.split(",", 1)]
    head = parts[0] if parts else ""
    tail = parts[1] if len(parts) > 1 else ""
    if not head:
        return None

    if _has_single_actor_anchor(previous_sentence):
        repaired_head = _departicipialize_clause(head, subject="They", third_person=False)
        if not repaired_head:
            return None
        if not tail:
            return repaired_head
        possessive_tail = re.match(
            r"^(their|his|her)\s+([A-Za-z][A-Za-z' -]{0,40})\s+([A-Za-z][A-Za-z'-]*ing)\b(.*)$",
            tail,
            flags=re.IGNORECASE,
        )
        if not possessive_tail:
            return repaired_head
        possessive = possessive_tail.group(1).lower()
        noun_phrase = _normalize_text(possessive_tail.group(2))
        participle = possessive_tail.group(3).lower()
        remainder = _normalize_text(possessive_tail.group(4))
        finite_verb = _PARTICIPIAL_THIRD_PERSON.get(participle)
        if not finite_verb:
            return repaired_head
        subject_phrase = f"{possessive.capitalize()} {noun_phrase}"
        second = (
            _normalize_terminal_punctuation(f"{subject_phrase} {finite_verb}{(' ' + remainder) if remainder else ''}")
            if noun_phrase
            else ""
        )
        if second:
            return _normalize_text(f"{repaired_head} {second}")
        return repaired_head

    head_match = re.match(r"^([A-Za-z][A-Za-z'-]*ing)\b(.*)$", head, flags=re.IGNORECASE)
    if not head_match:
        return None
    head_participle = head_match.group(1).lower()
    if head_participle not in _IMPLICATION_PARTICIPLES:
        return None
    if re.search(r"\b(he|she|they|his|her|their)\b", core, flags=re.IGNORECASE):
        return None
    repaired = _departicipialize_clause(head, subject="It", third_person=True)
    return repaired or None


def _repair_fragmentary_participial_splits(text: str) -> tuple[str, bool]:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text, False
    sentence_parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean_text) if part.strip()]
    if len(sentence_parts) < 2:
        return clean_text, False

    repaired_any = False
    rewritten_parts: List[str] = [sentence_parts[0]]
    for index in range(1, len(sentence_parts)):
        previous = rewritten_parts[-1]
        current = sentence_parts[index]
        if _has_terminal_punctuation(previous) and _looks_like_participial_fragment(current):
            repaired = _repair_participial_fragment(previous, current)
            if repaired and _normalize_text(repaired) != _normalize_text(current):
                rewritten_parts.append(repaired)
                repaired_any = True
                continue
        rewritten_parts.append(current)
    return _normalize_text(" ".join(rewritten_parts)), repaired_any


def _decompress_overpacked_sentences(text: str) -> str:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text
    if not any(marker in clean_text for marker in (",", ";", " hinting at ", " suggesting ", " which could ", " that could ")):
        return clean_text

    participles = (
        "intertwining",
        "drawing",
        "hinting",
        "suggesting",
        "making",
        "indicating",
        "offering",
        "creating",
        "revealing",
        "urging",
        "watching",
    )
    implication_phrases = (
        "hinting at",
        "suggesting",
        "making a tempting opportunity",
        "which could",
        "that could hold vital implications",
    )
    clause_markers = (" while ", " and ", " but ", ";", ":")
    sentence_parts = re.split(r"(?<=[.!?])\s+", clean_text)
    rewritten_parts: List[str] = []

    for raw_sentence in sentence_parts:
        sentence = raw_sentence.strip()
        if not sentence:
            continue
        core = sentence.rstrip(".!?").strip()
        if not core:
            rewritten_parts.append(sentence)
            continue

        rewritten = False
        punct = sentence[-1] if sentence[-1] in ".!?" else "."

        # Pattern B: semicolon-based explicit alternatives.
        if ";" in core:
            left, right = core.split(";", 1)
            left_clean = _normalize_terminal_punctuation(left)
            right_clean = _normalize_text(right)
            if (
                left_clean
                and right_clean
                and (
                    re.search(r"\bone\s+is\b", right_clean, flags=re.IGNORECASE)
                    or re.search(r"\bone\b[^.]{0,120}\bthe other\b", right_clean, flags=re.IGNORECASE)
                )
            ):
                alternatives = re.split(r",\s*(?=(?:the other|another)\b)", right_clean, maxsplit=1, flags=re.IGNORECASE)
                if len(alternatives) == 2:
                    first_alt = _normalize_terminal_punctuation(_capitalize_sentence_fragment(alternatives[0]))
                    second_alt = _normalize_terminal_punctuation(_capitalize_sentence_fragment(alternatives[1]))
                    if first_alt and second_alt:
                        rewritten_parts.extend([left_clean, first_alt, second_alt])
                        rewritten = True
                else:
                    right_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(right_clean))
                    if right_sentence:
                        rewritten_parts.extend([left_clean, right_sentence])
                        rewritten = True

        if rewritten:
            continue

        # Pattern A: overpacked participial tail after comma.
        participle_match = re.search(
            rf",\s*((?:{'|'.join(re.escape(p) for p in participles)})\b[^.!?]*)$",
            core,
            flags=re.IGNORECASE,
        )
        if participle_match:
            prefix = core[: participle_match.start()].strip(" ,;")
            tail = participle_match.group(1).strip(" ,;")
            long_or_multi_clause = len(core) > 140 or any(marker in core.lower() for marker in clause_markers)
            if prefix and tail and long_or_multi_clause:
                first_sentence = _normalize_terminal_punctuation(prefix)
                second_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(tail))
                if first_sentence and second_sentence:
                    rewritten_parts.extend([first_sentence, second_sentence])
                    rewritten = True

        if rewritten:
            continue

        # Pattern C: implication phrase appended to a physical/scene clause.
        lowered_core = core.lower()
        implication_pos = -1
        implication_phrase = ""
        for phrase in implication_phrases:
            token = f" {phrase} "
            idx = lowered_core.find(token)
            if idx == -1:
                idx = lowered_core.find(f", {phrase} ")
            if idx != -1:
                implication_pos = idx + (2 if lowered_core[idx : idx + 2] == ", " else 1)
                implication_phrase = phrase
                break
        if implication_pos > 0 and len(core) > 120:
            prefix = core[:implication_pos].rstrip(" ,;")
            tail = core[implication_pos:].lstrip(" ,;")
            if implication_phrase and prefix and tail:
                first_sentence = _normalize_terminal_punctuation(prefix)
                second_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(tail))
                if first_sentence and second_sentence:
                    rewritten_parts.extend([first_sentence, second_sentence])
                    rewritten = True

        if not rewritten:
            rewritten_parts.append(sentence if _has_terminal_punctuation(sentence) else f"{core}{punct}")

    return _normalize_text(" ".join(rewritten_parts))
