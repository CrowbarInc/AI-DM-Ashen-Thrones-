from __future__ import annotations

import re
from typing import Any, Dict, List

from game.exploration import NPC_PURSUIT_CONTACT_SESSION_KEY
from game.interaction_context import inspect as inspect_interaction_context
from game.narration_visibility import (
    build_narration_visibility_contract,
    validate_player_facing_first_mentions,
    validate_player_facing_referential_clarity,
    validate_player_facing_visibility,
)
from game.output_sanitizer import sanitize_player_facing_output
from game.social import SOCIAL_KINDS
from game.social_exchange_emission import (
    build_final_strict_social_response,
    effective_strict_social_resolution_for_emission,
    log_final_emission_decision,
    log_final_emission_trace,
    merged_player_prompt_for_gate,
    minimal_social_emergency_fallback_line,
    strict_social_emission_will_apply,
    strict_social_suppress_non_native_coercion_for_narration_beat,
    _npc_display_name_for_emission,
)
from game.storage import get_scene_runtime


def _normalize_text(text: str | None) -> str:
    return " ".join(str(text or "").strip().split())


def _sanitize_output_text(text: str) -> str:
    if not text:
        return text

    text = text.replace("<br><br>", "\n\n")
    text = text.replace("<br />", "\n")
    text = text.replace("<br>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_terminal_punctuation(text: str) -> str:
    clean = _normalize_text(text).strip(" ,;")
    if not clean:
        return ""
    if not _has_terminal_punctuation(clean):
        clean += "."
    return clean


def _has_terminal_punctuation(text: str) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    if clean[-1] in ".!?":
        return True
    if clean[-1] in "\"')]}”’" and len(clean) > 1 and clean[-2] in ".!?":
        return True
    return False


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
_MICRO_SMOOTH_MAX_COMBINED_LEN = 140
_MICRO_SMOOTH_SHORT_SENTENCE_LEN = 85
_MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS = (
    ";",
    ":",
    " while ",
    " because ",
    " although ",
    " though ",
    " which ",
    " that ",
    " who ",
)
_MICRO_SMOOTH_BANNED_TAIL_PHRASES = (
    "hinting at",
    "suggesting",
    "implying",
    "revealing",
    "indicating",
)
_MICRO_SMOOTH_COMBAT_MECHANICAL_MARKERS = (
    "initiative",
    "attack roll",
    "damage",
    "hit points",
    "armor class",
    "saving throw",
    "spell slot",
    "dc ",
    "roll ",
    "check ",
    "hp",
    "ac",
)
_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[\"“”'‘’]"),
    re.compile(
        r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|"
        r"blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|"
        r"orders?|interrupts?|thrusts?|hands?|points?)\b",
        re.IGNORECASE,
    ),
)
_THIRD_PERSON_TO_PARTICIPLE: Dict[str, str] = {
    "cuts": "cutting",
    "draws": "drawing",
    "hints": "hinting",
    "suggests": "suggesting",
    "makes": "making",
    "indicates": "indicating",
    "offers": "offering",
    "creates": "creating",
    "reveals": "revealing",
    "urges": "urging",
    "watches": "watching",
    "calls": "calling",
    "shouts": "shouting",
    "scans": "scanning",
    "studies": "studying",
    "gestures": "gesturing",
    "lingers": "lingering",
    "waits": "waiting",
    "stands": "standing",
    "speaks": "speaking",
    "says": "saying",
    "holds": "holding",
    "keeps": "keeping",
    "looks": "looking",
    "glances": "glancing",
    "murmurs": "murmuring",
    "whispers": "whispering",
    "observes": "observing",
    "surveys": "surveying",
    "exchanges": "exchanging",
}


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


def _sentence_has_dialogue_or_mechanics(sentence: str) -> bool:
    clean = _normalize_text(sentence)
    if not clean:
        return True
    lowered = clean.lower()
    if any(ch in clean for ch in ('"', "“", "”")):
        return True
    if re.search(r"(^|[\s(])'[^']{1,120}'", clean):
        return True
    if clean.startswith("- ") or clean.startswith("—"):
        return True
    return any(marker in lowered for marker in _MICRO_SMOOTH_COMBAT_MECHANICAL_MARKERS)


def _can_micro_merge_sentence_pair(first: str, second: str) -> bool:
    first_clean = _normalize_text(first)
    second_clean = _normalize_text(second)
    if not first_clean or not second_clean:
        return False
    if _sentence_has_dialogue_or_mechanics(first_clean) or _sentence_has_dialogue_or_mechanics(second_clean):
        return False

    first_core = first_clean.rstrip(".!?").strip()
    second_core = second_clean.rstrip(".!?").strip()
    if not first_core or not second_core:
        return False
    if len(first_core) > _MICRO_SMOOTH_SHORT_SENTENCE_LEN or len(second_core) > _MICRO_SMOOTH_SHORT_SENTENCE_LEN:
        return False

    first_low = f" {first_core.lower()} "
    second_low = f" {second_core.lower()} "
    if any(marker in first_low for marker in _MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS):
        return False
    if any(marker in second_low for marker in _MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS):
        return False
    if any(phrase in second_low for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
        return False
    if re.search(r"\b(he|she|it|you|we|i|him|her|them|our|your|my)\b", second_core, flags=re.IGNORECASE):
        return False
    if not (
        re.match(r"^they\b", first_core, flags=re.IGNORECASE)
        and (
            re.match(r"^they\b", second_core, flags=re.IGNORECASE)
            or re.match(r"^their\s+[A-Za-z][A-Za-z' -]{0,40}\s+[A-Za-z][A-Za-z'-]+\b", second_core, flags=re.IGNORECASE)
        )
    ):
        return False
    return True


def _merge_short_same_anchor_sentences(first: str, second: str) -> str | None:
    if not _can_micro_merge_sentence_pair(first, second):
        return None
    first_core = _normalize_text(first).rstrip(".!?").strip()
    second_core = _normalize_text(second).rstrip(".!?").strip()

    first_they = re.match(r"^(They)\s+(.+)$", first_core, flags=re.IGNORECASE)
    if not first_they:
        return None
    first_subject = first_they.group(1)
    first_predicate = first_they.group(2).strip()
    if not first_predicate:
        return None

    second_they = re.match(r"^(They)\s+(.+)$", second_core, flags=re.IGNORECASE)
    if second_they:
        second_predicate = second_they.group(2).strip()
        if not second_predicate:
            return None
        merged = f"{first_subject} {first_predicate}, then {second_predicate}"
        normalized = _normalize_terminal_punctuation(merged)
        if len(normalized.rstrip(".!?")) > _MICRO_SMOOTH_MAX_COMBINED_LEN:
            return None
        if any(phrase in normalized.lower() for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
            return None
        return normalized

    second_possessive = re.match(
        r"^Their\s+([A-Za-z][A-Za-z' -]{0,40})\s+([A-Za-z][A-Za-z'-]*)\b(.*)$",
        second_core,
        flags=re.IGNORECASE,
    )
    if not second_possessive:
        return None
    noun_phrase = _normalize_text(second_possessive.group(1))
    finite_verb = second_possessive.group(2).lower()
    remainder = _normalize_text(second_possessive.group(3))
    participle = _THIRD_PERSON_TO_PARTICIPLE.get(finite_verb)
    if not noun_phrase or not participle:
        return None

    tail = f"their {noun_phrase} {participle}{(' ' + remainder) if remainder else ''}"
    if any(phrase in tail.lower() for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
        return None
    merged = _normalize_terminal_punctuation(f"{first_subject} {first_predicate}, {tail}")
    if len(merged.rstrip(".!?")) > _MICRO_SMOOTH_MAX_COMBINED_LEN:
        return None
    return merged


def _micro_smooth_post_repair_sentences(text: str) -> tuple[str, bool]:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text, False
    sentence_parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean_text) if part.strip()]
    if len(sentence_parts) < 2:
        return clean_text, False

    merged_any = False
    rewritten_parts: List[str] = []
    idx = 0
    while idx < len(sentence_parts):
        current = sentence_parts[idx]
        if merged_any or idx >= len(sentence_parts) - 1:
            rewritten_parts.append(current)
            idx += 1
            continue
        nxt = sentence_parts[idx + 1]
        merged = _merge_short_same_anchor_sentences(current, nxt)
        if not merged:
            rewritten_parts.append(current)
            idx += 1
            continue
        rewritten_parts.append(merged)
        merged_any = True
        idx += 2

    return _normalize_text(" ".join(rewritten_parts)), merged_any


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


def _finalize_emission_output(out: Dict[str, Any], *, pre_gate_text: str) -> Dict[str, Any]:
    final_text = str(out.get("player_facing_text") or "")
    sanitized_text = _sanitize_output_text(final_text)
    decompressed_text = _decompress_overpacked_sentences(sanitized_text)
    repaired_text = decompressed_text
    fragment_repair_applied = False
    if decompressed_text != sanitized_text:
        repaired_text, fragment_repair_applied = _repair_fragmentary_participial_splits(decompressed_text)
    smoothed_text, sentence_micro_smoothing_applied = _micro_smooth_post_repair_sentences(repaired_text)
    sanitization_applied = sanitized_text != final_text
    sentence_decompression_applied = decompressed_text != sanitized_text
    out["player_facing_text"] = smoothed_text

    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    meta["output_sanitization_applied"] = sanitization_applied
    meta["sentence_decompression_applied"] = sentence_decompression_applied
    meta["sentence_fragment_repair_applied"] = fragment_repair_applied
    meta["sentence_micro_smoothing_applied"] = sentence_micro_smoothing_applied
    gate_out_text = _normalize_text(smoothed_text)
    meta["post_gate_mutation_detected"] = pre_gate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    out["_final_emission_meta"] = meta
    return out


def _question_prompt_for_resolution(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    return str(
        resolution.get("prompt")
        or resolution.get("label")
        or ((resolution.get("metadata") or {}).get("player_input") if isinstance(resolution.get("metadata"), dict) else "")
        or ""
    ).strip()


def _speaker_label(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "The guard"
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    if name:
        return name
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        return npc_id.replace("_", " ").replace("-", " ").title()
    return "The guard"


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if not isinstance(item, str) or not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scene_inner(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, dict):
        return inner
    return scene


def _output_sentence(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def _lowercase_leading_alpha(text: str) -> str:
    if not text:
        return ""
    chars = list(text)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.lower()
            break
    return "".join(chars)


def _join_entity_clauses(first_clause: str, second_clause: str) -> str:
    first = _normalize_text(first_clause)
    second = _normalize_text(second_clause)
    if not first:
        return second
    if not second:
        return first

    # If first clause already contains "while", avoid stacking it
    if " while " in first.lower():
        return f"{first}, and {second}"
    return f"{first}, while {second}"


def _opening_scene_preference_active(session: Dict[str, Any] | None) -> bool:
    if not isinstance(session, dict):
        return False
    turn_counter = int(session.get("turn_counter", 0) or 0)
    visited_scene_ids = session.get("visited_scene_ids") if isinstance(session.get("visited_scene_ids"), list) else []
    return turn_counter <= 1 or (turn_counter == 0 and len(visited_scene_ids) <= 1)


def _scene_visible_facts(scene: Dict[str, Any] | None) -> List[str]:
    inner = _scene_inner(scene)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            out.append(clean)
    return _dedupe_preserve_order(out)


def _augment_scene_with_runtime_visible_leads(
    scene: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any] | None:
    if not isinstance(scene, dict):
        return scene
    if not isinstance(session, dict):
        return scene
    sid = str(scene_id or "").strip()
    if not sid:
        return scene
    runtime = get_scene_runtime(session, sid)
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if not isinstance(recent, list) or not recent:
        return scene

    extra_facts: List[str] = []
    for lead in recent[-4:]:
        if not isinstance(lead, dict):
            continue
        kind = str(lead.get("kind") or "").strip()
        if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
            continue
        subject = _normalize_text(lead.get("subject"))
        position = _normalize_text(lead.get("position"))
        if not subject:
            continue
        fact = f"{subject} lingers {position}" if position else f"{subject} lingers nearby"
        extra_facts.append(_output_sentence(fact))

    if not extra_facts:
        return scene

    if isinstance(scene.get("scene"), dict):
        outer = dict(scene)
        inner = dict(scene.get("scene") or {})
        existing = _scene_visible_facts(scene)
        inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
        outer["scene"] = inner
        return outer

    inner = dict(scene)
    existing = _scene_visible_facts(scene)
    inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
    return inner


def _passive_scene_pressure_due_for_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    if not isinstance(session, dict):
        return False
    sid = str(scene_id or "").strip()
    if not sid:
        return False
    runtime = get_scene_runtime(session, sid)
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    last_player_action_passive = bool(runtime.get("last_player_action_passive")) if isinstance(runtime, dict) else False
    if not last_player_action_passive and passive_streak <= 0:
        return False
    visible_low = " ".join(fact.lower() for fact in _scene_visible_facts(scene))
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    return bool(
        passive_streak >= 2
        or isinstance(recent, list)
        and any(isinstance(item, dict) for item in recent)
        or "guard" in visible_low
        or "watch" in visible_low
        or "missing patrol" in visible_low
        or "rumor" in visible_low
        or "rumour" in visible_low
    )


def _reply_already_has_concrete_interaction(text: str) -> bool:
    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)


def _passive_scene_pressure_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> List[tuple[str, str, str, str, str, str, Dict[str, Any]]]:
    if not _passive_scene_pressure_due_for_fallback(session=session, scene=scene, scene_id=scene_id):
        return []

    sid = str(scene_id or "").strip()
    runtime = get_scene_runtime(session, sid) if isinstance(session, dict) and sid else {}
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if isinstance(recent, list):
        for lead in reversed(recent[-4:]):
            if not isinstance(lead, dict):
                continue
            kind = str(lead.get("kind") or "").strip()
            if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
                continue
            subject = _normalize_text(lead.get("subject"))
            position = _normalize_text(lead.get("position"))
            if not subject:
                continue
            move_from = f" leaves {position} and" if position else ""
            if passive_streak >= 2:
                return [
                    (
                        _output_sentence(
                            f'{subject}{move_from} comes straight to you before the pause can settle. "Enough watching," they say. "Ask me now, or lose the trail."'
                        ),
                        "passive_scene_pressure",
                        "passive_scene_pressure_lead_figure",
                        "passive_scene_pressure_fallback",
                        "passive_scene_pressure_fallback",
                        "passive_scene_pressure:lead_figure",
                        _first_mention_composition_meta(),
                    )
                ]
            return [
                (
                    _output_sentence(
                        f'{subject}{move_from} cuts through the crowd and stops at your shoulder. "You\'re asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."'
                    ),
                    "passive_scene_pressure",
                    "passive_scene_pressure_lead_figure",
                    "passive_scene_pressure_fallback",
                    "passive_scene_pressure_fallback",
                    "passive_scene_pressure:lead_figure",
                    _first_mention_composition_meta(),
                )
            ]

    visible_facts = _scene_visible_facts(scene)
    visible_low = " ".join(fact.lower() for fact in visible_facts)
    if "guard" in visible_low and "missing patrol" in visible_low:
        if passive_streak >= 2:
            text = (
                'The same guard does not let the silence stand a second time. "No more watching," he says, '
                "closing the distance and jabbing a finger at the east-road line on the notice. "
                '"Either tell me who sent you, or get moving before that trail cools for good."'
            )
        else:
            text = (
                'A guard peels away from the notice board and squares up to you. "Standing still won\'t help that patrol," '
                'he says, stabbing two fingers at the posting. "Tell me what you know, or get on the east-road trail before it dies."'
            )
        return [
            (
                _output_sentence(text),
                "passive_scene_pressure",
                "passive_scene_pressure_guard_rumor",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure:guard_rumor",
                _first_mention_composition_meta(),
            )
        ]
    if "guard" in visible_low:
        text = (
            'A guard notices you lingering and comes over at once. "If you\'re waiting on trouble, it already passed the checkpoint," '
            'he says. "Take the east-road report or get clear."'
        )
        return [
            (
                _output_sentence(text),
                "passive_scene_pressure",
                "passive_scene_pressure_visible_figure",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure:visible_figure",
                _first_mention_composition_meta(),
            )
        ]
    return [
        (
            _output_sentence(
                'The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. '
                '"Board, runner, or road," he says. "Pick one before the gate swallows the trail."'
            ),
            "passive_scene_pressure",
            "passive_scene_pressure_generic",
            "passive_scene_pressure_fallback",
            "passive_scene_pressure_fallback",
            "passive_scene_pressure:fallback",
            _first_mention_composition_meta(),
        )
    ]


def _visible_entity_catalog(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_ids = {
        str(item).strip()
        for item in (contract.get("visible_entity_ids") or [])
        if isinstance(item, str) and str(item).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    inner = _scene_inner(scene)
    addressables = inner.get("addressables") if isinstance(inner.get("addressables"), list) else []
    world_npcs = world.get("npcs") if isinstance(world, dict) and isinstance(world.get("npcs"), list) else []
    world_npc_map = {
        str(row.get("id") or "").strip(): row
        for row in world_npcs
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }

    ordered_rows: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _append_row(entity_id: str, row: Dict[str, Any] | None) -> None:
        if not entity_id or entity_id in seen or entity_id not in visible_ids:
            return
        seen.add(entity_id)
        base = row if isinstance(row, dict) else {}
        display_name = str(base.get("name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (base.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        normalized_aliases = alias_map.get(entity_id) if isinstance(alias_map.get(entity_id), list) else []
        ordered_aliases = _dedupe_preserve_order(
            [display_name]
            + aliases
            + [str(alias).strip() for alias in normalized_aliases if isinstance(alias, str) and str(alias).strip()]
        )
        if not display_name and ordered_aliases:
            display_name = ordered_aliases[0].title()
        role_hints = [
            str(role).strip()
            for role in (base.get("address_roles") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        world_row = world_npc_map.get(entity_id)
        if isinstance(world_row, dict):
            world_role = str(world_row.get("role") or "").strip()
            if world_role:
                role_hints.append(world_role)
        ordered_rows.append(
            {
                "entity_id": entity_id,
                "display_name": display_name or entity_id.replace("_", " ").title(),
                "aliases": ordered_aliases,
                "role_hints": _dedupe_preserve_order(role_hints),
            }
        )

    for row in addressables:
        if not isinstance(row, dict):
            continue
        _append_row(str(row.get("id") or "").strip(), row)

    for entity_id in sorted(visible_ids):
        _append_row(entity_id, world_npc_map.get(entity_id))

    return ordered_rows


def _rewrite_visible_fact_as_explicit_intro(display_name: str, fact_text: str, phrases: List[str]) -> str:
    fact = _output_sentence(fact_text)
    if not fact:
        return ""
    if fact.lower().startswith(display_name.lower()):
        return fact
    for phrase in phrases:
        clean_phrase = _normalize_text(phrase).lower()
        if not clean_phrase:
            continue
        for pattern in (
            rf"^(?:A|An|The)\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
            rf"^One\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
        ):
            match = re.match(pattern, fact, flags=re.IGNORECASE)
            if not match:
                continue
            remainder = (match.group(1) or "").strip()
            if not remainder:
                return _output_sentence(display_name)
            return _output_sentence(f"{display_name} {remainder}")
    return ""


def _scene_grounding_clause(visible_facts: List[str], blocked_phrases: List[str]) -> str:
    blocked = [phrase.lower() for phrase in blocked_phrases if phrase]
    for fact in visible_facts:
        if not fact:
            continue
        lowered = fact.lower()
        if any(phrase in lowered for phrase in blocked):
            continue
        return _lowercase_leading_alpha(fact.rstrip(".!?"))
    return ""


def _default_first_mention_composition_layers() -> Dict[str, Any]:
    return {"environment": None, "motion": None, "entities": []}


def _first_mention_composition_meta(
    *,
    used: bool = False,
    environment: str | None = None,
    motion: str | None = None,
    entities: List[str] | None = None,
) -> Dict[str, Any]:
    layers = _default_first_mention_composition_layers()
    if environment:
        layers["environment"] = environment
    if motion:
        layers["motion"] = motion
    if isinstance(entities, list):
        layers["entities"] = [str(entity).strip() for entity in entities if isinstance(entity, str) and str(entity).strip()]
    return {
        "first_mention_composition_used": used,
        "first_mention_composition_layers": layers,
    }


def _fact_matches_keywords(fact: str, keywords: tuple[str, ...]) -> bool:
    lowered = fact.lower()
    return any(keyword in lowered for keyword in keywords)


def _first_fact_matching_keywords(
    visible_facts: List[str],
    keywords: tuple[str, ...],
    *,
    excluded: set[str] | None = None,
) -> str:
    blocked = excluded or set()
    for fact in visible_facts:
        if not fact or fact in blocked:
            continue
        for segment in _fact_segments(fact):
            if segment in blocked:
                continue
            if _fact_matches_keywords(segment, keywords):
                return _output_sentence(segment)
        if _fact_matches_keywords(fact, keywords):
            return fact
    return ""


_ENTITY_COMPOSITION_PREDICATE_STARTS: tuple[tuple[str, str], ...] = (
    ("hangs back", "hangs back"),
    ("calls out", "calls"),
    ("is shouting", "shouts"),
    ("are shouting", "shouts"),
    ("is calling", "calls"),
    ("are calling", "calls"),
    ("is offering", "offers"),
    ("are offering", "offers"),
    ("is watching", "watches"),
    ("are watching", "watches"),
    ("is scanning", "scans"),
    ("are scanning", "scans"),
    ("is studying", "studies"),
    ("are studying", "studies"),
    ("is gesturing", "gestures"),
    ("are gesturing", "gestures"),
    ("is lingering", "lingers"),
    ("are lingering", "lingers"),
    ("is waiting", "waits"),
    ("are waiting", "waits"),
    ("is observing", "observes"),
    ("are observing", "observes"),
    ("is surveying", "surveys"),
    ("are surveying", "surveys"),
    ("is exchanging", "exchanges"),
    ("are exchanging", "exchanges"),
    ("holds", "holds"),
    ("hold", "holds"),
    ("watches", "watches"),
    ("watch", "watches"),
    ("scans", "scans"),
    ("scan", "scans"),
    ("studies", "studies"),
    ("study", "studies"),
    ("shouts", "shouts"),
    ("shout", "shouts"),
    ("calls", "calls"),
    ("call", "calls"),
    ("offers", "offers"),
    ("offer", "offers"),
    ("gestures", "gestures"),
    ("gesture", "gestures"),
    ("lingers", "lingers"),
    ("linger", "lingers"),
    ("waits", "waits"),
    ("wait", "waits"),
    ("observes", "observes"),
    ("observe", "observes"),
    ("surveys", "surveys"),
    ("survey", "surveys"),
    ("exchanges", "exchanges"),
    ("exchange", "exchanges"),
    ("stands", "stands"),
    ("stand", "stands"),
    ("keeps", "keeps"),
    ("keep", "keeps"),
    ("looks", "looks"),
    ("look", "looks"),
    ("glances", "glances"),
    ("glance", "glances"),
    ("murmurs", "murmurs"),
    ("murmur", "murmurs"),
    ("whispers", "whispers"),
    ("whisper", "whispers"),
)
_LOW_INFO_ENTITY_PREDICATE_RE = re.compile(
    r"^(stands|shouts|watches|lingers|waits|scans|gestures)(?:\s+(nearby|there|quietly|silently|still|alone))?$",
    flags=re.IGNORECASE,
)
_ENTITY_DESCRIPTOR_STOPWORDS = {
    "captain",
    "guard",
    "runner",
    "informant",
    "watcher",
    "stranger",
    "refugee",
    "figure",
    "nearby",
    "still",
}
_ENTITY_ROLE_DETAIL_PHRASE_MAP: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("choke", "gate"), "holds the choke at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("line", "gate"), "holds the line at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("crowd",), "scans the crowd at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("gate",), "watches the gate"),
    (("runner", "informant"), ("stew", "rumor"), "calls over the noise with offers of hot stew and rumor"),
    (("runner", "informant"), ("stew",), "calls over the noise with offers of hot stew"),
    (("runner", "informant"), ("crowd",), "calls over the crowd"),
    (("watcher",), ("crowd",), "lingers at the edge of the crowd"),
    (("stranger", "refugee"), ("refugee", "crowd"), "hangs back from the press of refugees"),
    (("stranger", "refugee"), ("crowd",), "hangs back from the crowd"),
)


def _phrase_present(text: str, phrase: str) -> bool:
    clean_text = _normalize_text(text).lower()
    clean_phrase = _normalize_text(phrase).lower()
    if not clean_text or not clean_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(clean_phrase)}(?!\w)", clean_text))


def _entity_descriptor_tokens(display_name: str, aliases: List[str]) -> List[str]:
    tokens: List[str] = []
    for raw in [display_name] + list(aliases):
        for token in re.findall(r"[a-zA-Z][a-zA-Z'-]+", raw.lower()):
            if len(token) < 5 or token in _ENTITY_DESCRIPTOR_STOPWORDS:
                continue
            tokens.append(token)
    return _dedupe_preserve_order(tokens)


def _role_forms(role: str) -> List[str]:
    clean = _normalize_text(role).lower()
    if not clean:
        return []
    forms = [clean]
    if clean.endswith("y") and len(clean) > 1:
        forms.append(f"{clean[:-1]}ies")
    elif clean.endswith(("s", "x", "z", "ch", "sh")):
        forms.append(f"{clean}es")
    else:
        forms.append(f"{clean}s")
    return _dedupe_preserve_order(forms)


def _fact_segments(fact_text: str) -> List[str]:
    clean = _output_sentence(fact_text).rstrip(".!?")
    if not clean:
        return []
    segments = re.split(r"[;:]|(?<=[.!?])\s+", clean)
    return [segment.strip(" ,") for segment in segments if segment.strip(" ,")]


def _extract_leading_subject_and_predicate(segment: str) -> tuple[str, str]:
    clean = _normalize_text(segment)
    if not clean:
        return "", ""
    lowered = clean.lower()
    for predicate_start, _canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        match = re.search(rf"\b{re.escape(predicate_start)}\b", lowered)
        if not match:
            continue
        subject = clean[: match.start()].strip(" ,")
        predicate = clean[match.start() :].strip(" ,")
        if not subject or not predicate:
            continue
        if len(subject.split()) > 9:
            continue
        return subject, predicate
    return "", ""


def _subject_matches_entity(
    subject: str,
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    descriptor_tokens: List[str],
) -> bool:
    lowered_subject = _normalize_text(subject).lower()
    if not lowered_subject:
        return False
    for phrase in _dedupe_preserve_order([display_name] + aliases):
        if _phrase_present(lowered_subject, phrase):
            return True
    for role in role_hints:
        for form in _role_forms(role):
            if _phrase_present(lowered_subject, form):
                return True
    return any(token in lowered_subject for token in descriptor_tokens)


def _singularize_entity_predicate(predicate: str) -> str:
    clean = _normalize_text(predicate)
    if not clean:
        return ""
    lowered = clean.lower()
    replacements = (
        ("are now ", "is now "),
        ("are ", "is "),
        ("hang back", "hangs back"),
        ("hold ", "holds "),
        ("watch ", "watches "),
        ("scan ", "scans "),
        ("study ", "studies "),
        ("shout ", "shouts "),
        ("call ", "calls "),
        ("offer ", "offers "),
        ("gesture ", "gestures "),
        ("linger ", "lingers "),
        ("wait ", "waits "),
        ("observe ", "observes "),
        ("survey ", "surveys "),
        ("exchange ", "exchanges "),
        ("stand ", "stands "),
        ("keep ", "keeps "),
        ("look ", "looks "),
        ("glance ", "glances "),
        ("murmur ", "murmurs "),
        ("whisper ", "whispers "),
    )
    for old, new in replacements:
        if lowered == old.strip():
            return new.strip()
        if lowered.startswith(old):
            return f"{new}{clean[len(old):]}".strip()
    return clean


def _predicate_after_display_name(display_name: str, sentence: str) -> str:
    clean = _output_sentence(sentence).rstrip(".!?")
    if not clean:
        return ""
    lowered_clean = clean.lower()
    lowered_name = display_name.lower()
    if not lowered_clean.startswith(lowered_name):
        return ""
    return clean[len(display_name) :].strip(" ,;:-")


def _entity_predicate_signature(predicate: str) -> tuple[str, bool]:
    clean = _normalize_text(predicate).lower()
    if not clean:
        return "", True
    for predicate_start, canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        if clean == predicate_start or clean.startswith(f"{predicate_start} "):
            return canonical, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))
    first_token = clean.split()[0]
    return first_token, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))


def _composition_candidate(
    *,
    display_name: str,
    predicate: str,
    source_rank: int,
    source_index: int,
    fact_backed: bool,
) -> Dict[str, Any] | None:
    clean_predicate = _normalize_text(predicate).rstrip(".!?")
    if not clean_predicate:
        return None
    verb_key, low_info = _entity_predicate_signature(clean_predicate)
    detail_bonus = 0 if low_info else min(len(clean_predicate.split()), 8)
    return {
        "clause": f"{display_name} {clean_predicate}",
        "verb_key": verb_key,
        "low_info": low_info,
        "fact_backed": fact_backed,
        "score": (source_rank * 100) + detail_bonus,
        "source_index": source_index,
    }


def _generic_entity_intro_predicate(
    *,
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> str:
    signal_text = " ".join(fact.lower() for fact in composition_facts if isinstance(fact, str))
    role_set = {role.lower() for role in role_hints if isinstance(role, str) and role}
    for required_roles, required_tokens, predicate in _ENTITY_ROLE_DETAIL_PHRASE_MAP:
        if role_set.isdisjoint(required_roles):
            continue
        if all(token in signal_text for token in required_tokens):
            return predicate
    if "crowd" in signal_text:
        return "watches the crowd" if slot_index == 0 else "lingers at the edge of the crowd"
    if "gate" in signal_text:
        return "stands at the gate"
    return "watches nearby" if slot_index == 0 else "lingers nearby"


def _entity_clause_candidates(
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> List[Dict[str, Any]]:
    explicit_phrases = _dedupe_preserve_order([display_name] + aliases + role_hints)
    descriptor_tokens = _entity_descriptor_tokens(display_name, aliases)
    candidates: List[Dict[str, Any]] = []
    seen_clauses: set[str] = set()

    for fact_index, fact in enumerate(composition_facts):
        explicit_sentence = ""
        if fact.lower().startswith(display_name.lower()):
            explicit_sentence = fact
        else:
            explicit_sentence = _rewrite_visible_fact_as_explicit_intro(display_name, fact, explicit_phrases)
        if explicit_sentence:
            predicate = _predicate_after_display_name(display_name, explicit_sentence)
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=predicate,
                source_rank=3,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)
        for segment in _fact_segments(fact):
            subject, predicate = _extract_leading_subject_and_predicate(segment)
            if not subject or not predicate:
                continue
            if not _subject_matches_entity(
                subject,
                display_name=display_name,
                aliases=aliases,
                role_hints=role_hints,
                descriptor_tokens=descriptor_tokens,
            ):
                continue
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=_singularize_entity_predicate(predicate),
                source_rank=2,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)

    generic_candidate = _composition_candidate(
        display_name=display_name,
        predicate=_generic_entity_intro_predicate(
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=slot_index,
        ),
        source_rank=1,
        source_index=len(composition_facts),
        fact_backed=False,
    )
    if generic_candidate and generic_candidate["clause"] not in seen_clauses:
        candidates.append(generic_candidate)

    candidates.sort(
        key=lambda item: (
            -int(item.get("score", 0)),
            int(item.get("source_index", 10**6)),
            len(str(item.get("clause") or "")),
        )
    )
    return candidates


def _visible_safe_scene_composition_facts(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[str]:
    inner = _scene_inner(scene)
    raw_candidates: List[str] = list(_scene_visible_facts(scene))
    summary = _output_sentence(str(inner.get("summary") or ""))
    if summary:
        raw_candidates.append(summary)
    raw_journal_seed_facts = inner.get("journal_seed_facts") if isinstance(inner.get("journal_seed_facts"), list) else []
    for item in raw_journal_seed_facts:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            raw_candidates.append(clean)

    visible_safe_facts: List[str] = []
    for candidate in _dedupe_preserve_order(raw_candidates):
        validation = validate_player_facing_visibility(
            candidate,
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            visible_safe_facts.append(candidate)
    return visible_safe_facts


def _build_composed_scene_intro(
    narration_visibility: Dict[str, Any],
    visible_entities: List[str],
    composition_facts: List[str],
    scene_context: Dict[str, Any],
) -> str | None:
    scene_context["composition_layers"] = _default_first_mention_composition_layers()
    if not isinstance(narration_visibility, dict) or not composition_facts or not visible_entities:
        return None

    environment = _first_fact_matching_keywords(
        composition_facts,
        (
            "rain",
            "snow",
            "wind",
            "fog",
            "mist",
            "smoke",
            "ash",
            "mud",
            "muddy",
            "stone",
            "gate",
            "wall",
            "square",
            "yard",
            "district",
            "alley",
            "alleyway",
            "tavern",
            "banner",
            "banners",
            "ground",
            "earth",
            "puddle",
            "puddles",
            "crate",
            "crates",
            "path",
            "thicket",
            "milestone",
            "millstone",
            "underbrush",
            "breeze",
        ),
    )
    if not environment:
        return None

    motion = _first_fact_matching_keywords(
        composition_facts,
        (
            "crowd",
            "refugee",
            "refugees",
            "wagon",
            "wagons",
            "traffic",
            "patron",
            "patrons",
            "townsfolk",
            "onlookers",
            "voices",
            "whisper",
            "whispers",
            "murmur",
            "murmurs",
            "shout",
            "shouts",
            "queue",
            "presses",
            "press in",
            "pushes",
            "scan",
            "scans",
            "glance",
            "glances",
            "watch newcomers",
            "tension",
            "tense",
            "agitation",
            "unrest",
            "shift uneasily",
        ),
        excluded={environment},
    )

    entity_rows_by_display_name = (
        scene_context.get("entity_rows_by_display_name")
        if isinstance(scene_context.get("entity_rows_by_display_name"), dict)
        else {}
    )
    visible_entity_ids = {
        str(entity_id).strip()
        for entity_id in (narration_visibility.get("visible_entity_ids") or [])
        if isinstance(entity_id, str) and str(entity_id).strip()
    }
    selected_entity_names: List[str] = []
    for entity_name in visible_entities:
        clean_name = _normalize_text(entity_name)
        if not clean_name or clean_name in selected_entity_names:
            continue
        row = entity_rows_by_display_name.get(clean_name) if isinstance(entity_rows_by_display_name, dict) else None
        entity_id = str((row or {}).get("entity_id") or "").strip() if isinstance(row, dict) else ""
        if visible_entity_ids and entity_id and entity_id not in visible_entity_ids:
            continue
        selected_entity_names.append(clean_name)
    if not selected_entity_names:
        return None

    selected_entity_clauses: List[Dict[str, Any]] = []
    used_verb_keys: set[str] = set()
    for index, entity_name in enumerate(selected_entity_names):
        row = entity_rows_by_display_name.get(entity_name) if isinstance(entity_rows_by_display_name, dict) else {}
        aliases = [
            str(alias).strip()
            for alias in ((row or {}).get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in ((row or {}).get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        clause_candidates = _entity_clause_candidates(
            display_name=entity_name,
            aliases=aliases,
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=index,
        )
        chosen_candidate: Dict[str, Any] | None = None
        for candidate in clause_candidates:
            verb_key = str(candidate.get("verb_key") or "")
            if not selected_entity_clauses:
                chosen_candidate = candidate
                break
            if verb_key and verb_key in used_verb_keys and bool(candidate.get("low_info")):
                continue
            if len(selected_entity_clauses) >= 1 and not bool(candidate.get("fact_backed")):
                continue
            chosen_candidate = candidate
            break
        if not chosen_candidate:
            continue
        selected_entity_clauses.append(
            {
                "entity_name": entity_name,
                "clause": str(chosen_candidate.get("clause") or ""),
                "verb_key": str(chosen_candidate.get("verb_key") or ""),
                "fact_backed": bool(chosen_candidate.get("fact_backed")),
                "low_info": bool(chosen_candidate.get("low_info")),
            }
        )
        verb_key = str(chosen_candidate.get("verb_key") or "")
        if verb_key:
            used_verb_keys.add(verb_key)
        if len(selected_entity_clauses) >= 2:
            break
    if not selected_entity_clauses:
        return None

    entity_sentence = selected_entity_clauses[0]["clause"]
    if len(selected_entity_clauses) > 1:
        first_clause = selected_entity_clauses[0]
        second_clause = selected_entity_clauses[1]
        if (
            first_clause["verb_key"]
            and second_clause["verb_key"]
            and first_clause["verb_key"] != second_clause["verb_key"]
            and not second_clause["low_info"]
        ):
            entity_sentence = _join_entity_clauses(
                first_clause["clause"],
                second_clause["clause"],
            )

    scene_sentence = environment.rstrip(".!?")
    if motion:
        scene_sentence = f"{scene_sentence} while {_lowercase_leading_alpha(motion.rstrip('.!?'))}"

    scene_context["composition_layers"] = {
        "environment": environment,
        "motion": motion or None,
        "entities": [str(item.get("entity_name") or "") for item in selected_entity_clauses if str(item.get("entity_name") or "")],
    }
    return f"{_output_sentence(scene_sentence)} {_output_sentence(entity_sentence)}".strip()


def _grounded_scene_intro_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    active_interlocutor: str,
) -> List[tuple[str, str, str, str, str, str, Dict[str, Any]]]:
    visible_facts = _scene_visible_facts(scene)
    composition_facts = _visible_safe_scene_composition_facts(session=session, scene=scene, world=world)
    entity_rows = _visible_entity_catalog(session=session, scene=scene, world=world)
    if not entity_rows and not composition_facts and not visible_facts:
        return []

    narration_visibility = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    inner = _scene_inner(scene)
    scene_location = str(inner.get("location") or inner.get("id") or "").strip()
    prioritized_entities: List[Dict[str, Any]] = []
    if active_interlocutor:
        for row in entity_rows:
            if str(row.get("entity_id") or "").strip() == active_interlocutor:
                prioritized_entities.append(row)
                break
    for row in entity_rows:
        if row not in prioritized_entities:
            prioritized_entities.append(row)

    fallback_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []
    composed_scene_context: Dict[str, Any] = {
        "scene_location": scene_location,
        "entity_rows_by_display_name": {
            str(row.get("display_name") or "").strip(): row
            for row in prioritized_entities
            if isinstance(row, dict) and str(row.get("display_name") or "").strip()
        },
    }
    composed_scene_intro = _build_composed_scene_intro(
        narration_visibility,
        [str(row.get("display_name") or "").strip() for row in prioritized_entities if str(row.get("display_name") or "").strip()],
        composition_facts,
        composed_scene_context,
    )
    composed_layers = composed_scene_context.get("composition_layers")
    if composed_scene_intro and isinstance(composed_layers, dict):
        fallback_candidates.append(
            (
                composed_scene_intro,
                "visible_scene_composed_intro",
                "first_mention_composed_scene_intro",
                "composed_visible_scene_intro",
                "composed_visible_scene_intro",
                "visible_scene_composed_intro",
                _first_mention_composition_meta(
                    used=True,
                    environment=str(composed_layers.get("environment") or "") or None,
                    motion=str(composed_layers.get("motion") or "") or None,
                    entities=composed_layers.get("entities") if isinstance(composed_layers.get("entities"), list) else [],
                ),
            )
        )

    for row in prioritized_entities:
        entity_id = str(row.get("entity_id") or "").strip()
        display_name = str(row.get("display_name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (row.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in (row.get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        subject_phrases = _dedupe_preserve_order(aliases + role_hints)

        explicit_fact_intro = ""
        for fact in visible_facts:
            explicit_fact_intro = _rewrite_visible_fact_as_explicit_intro(display_name, fact, subject_phrases)
            if explicit_fact_intro:
                break
        if explicit_fact_intro:
            fallback_candidates.append(
                (
                    explicit_fact_intro,
                    "visible_scene_explicit_intro",
                    "first_mention_explicit_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    f"visible_entity:{entity_id}",
                    _first_mention_composition_meta(),
                )
            )

        grounding_clause = _scene_grounding_clause(visible_facts, subject_phrases)
        if scene_location and grounding_clause:
            generic_intro = f"{display_name} stands in {scene_location} while {grounding_clause}."
        elif scene_location:
            generic_intro = f"{display_name} stands in {scene_location}."
        elif grounding_clause:
            generic_intro = f"{display_name} stands nearby while {grounding_clause}."
        else:
            generic_intro = f"{display_name} stands nearby."
        fallback_candidates.append(
            (
                _output_sentence(generic_intro),
                "visible_scene_explicit_intro",
                "first_mention_explicit_scene_intro",
                "explicit_visible_entity_scene_intro",
                "explicit_visible_entity_scene_intro",
                f"visible_entity:{entity_id}",
                _first_mention_composition_meta(),
            )
        )

    for index, fact in enumerate(visible_facts):
        fallback_candidates.append(
            (
                fact,
                "visible_scene_fact_intro",
                "first_mention_visible_fact_intro",
                "visible_fact_scene_intro",
                "visible_fact_scene_intro",
                f"visible_fact:{index}",
                _first_mention_composition_meta(),
            )
        )

    deduped_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []
    seen_candidates = set()
    for candidate in fallback_candidates:
        candidate_key = candidate[:6]
        if candidate_key in seen_candidates:
            continue
        seen_candidates.add(candidate_key)
        deduped_candidates.append(candidate)
    return deduped_candidates


def _build_visibility_violation_sample(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sample: List[Dict[str, Any]] = []
    for violation in violations[:3]:
        if not isinstance(violation, dict):
            continue
        sample.append(
            {
                "kind": str(violation.get("kind") or ""),
                "token": str(violation.get("token") or ""),
                "matched_entity_id": violation.get("matched_entity_id"),
                "matched_fact": violation.get("matched_fact"),
            }
        )
    return sample


def _build_referential_clarity_violation_sample(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sample: List[Dict[str, Any]] = []
    for violation in violations[:3]:
        if not isinstance(violation, dict):
            continue
        sample.append(
            {
                "kind": str(violation.get("kind") or ""),
                "token": str(violation.get("token") or ""),
                "candidate_entity_ids": list(violation.get("candidate_entity_ids") or []),
                "candidate_aliases": list(violation.get("candidate_aliases") or []),
                "sentence_text": str(violation.get("sentence_text") or ""),
                "offset": violation.get("offset"),
            }
        )
    return sample


def _apply_default_referential_clarity_meta(meta: Dict[str, Any], *, passed: bool | None) -> None:
    meta["referential_clarity_validation_passed"] = passed
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = []
    meta["referential_clarity_checked_entities"] = []
    meta["referential_clarity_violation_sample"] = []


def _standard_visibility_safe_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    enforce_first_mentions: bool = False,
    enforce_referential_clarity: bool = False,
    prefer_grounded_scene_intro: bool = False,
) -> tuple[str, str, str, str, str, str, Dict[str, Any]]:
    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    validation_scene = _augment_scene_with_runtime_visible_leads(
        scene,
        session=session if isinstance(session, dict) else None,
        scene_id=scene_id,
    )
    fallback_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []

    if strict_social_active and isinstance(eff_resolution, dict):
        social_fallback = minimal_social_emergency_fallback_line(eff_resolution)
        fallback_candidates.append(
            (
                social_fallback,
                "strict_social_visibility_minimal",
                "visibility_minimal_social_fallback",
                "minimal_social_emergency_fallback",
                "standard_safe_fallback",
                "minimal_social_emergency_fallback",
                _first_mention_composition_meta(),
            )
        )
    else:
        fallback_candidates.extend(
            _passive_scene_pressure_fallback_candidates(
                session=session if isinstance(session, dict) else None,
                scene=scene,
                scene_id=scene_id,
            )
        )
        if prefer_grounded_scene_intro:
            fallback_candidates.extend(
                _grounded_scene_intro_fallback_candidates(
                    session=session,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene,
                    world=world,
                    active_interlocutor=active_interlocutor,
                )
            )

    sid = str(scene_id or "").strip()
    if (
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
        and not strict_social_active
    ):
        mini_res: Dict[str, Any] = {
            "kind": "question",
            "social": {
                "npc_id": active_interlocutor,
                "npc_name": _npc_display_name_for_emission(world, sid, active_interlocutor),
                "social_intent_class": "social_exchange",
            },
        }
        fallback_candidates.append(
            (
                minimal_social_emergency_fallback_line(mini_res),
                "social_active_interlocutor_minimal",
                "social_interlocutor_fallback",
                "social_interlocutor_minimal_fallback",
                "standard_safe_fallback",
                "social_interlocutor_minimal_fallback",
                _first_mention_composition_meta(),
            )
        )

    if _should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution):
        fallback_candidates.append(
            (
                "Nothing confirms progress toward that lead yet—the moment stays unresolved.",
                "npc_pursuit_fail_closed_neutral",
                "npc_pursuit_neutral_nonprogress",
                "npc_pursuit_neutral_fallback",
                "standard_safe_fallback",
                "npc_pursuit_neutral_fallback",
                _first_mention_composition_meta(),
            )
        )
    elif not strict_social_active and not _passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    ):
        fallback_candidates.append(
            (
                "For a breath, the scene holds while voices shift around you.",
                "global_scene_narrative",
                "narrative_safe_fallback",
                "global_scene_fallback",
                "standard_safe_fallback",
                "global_scene_fallback",
                _first_mention_composition_meta(),
            )
        )

    for (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        fallback_strategy,
        fallback_candidate_source,
        composition_meta,
    ) in fallback_candidates:
        if not _normalize_text(fallback_text):
            continue
        validation = validate_player_facing_visibility(
            fallback_text,
            session=session if isinstance(session, dict) else None,
            scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            if enforce_first_mentions:
                first_mention_validation = validate_player_facing_first_mentions(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if first_mention_validation.get("ok") is not True:
                    continue
            if enforce_referential_clarity:
                referential_clarity_validation = validate_player_facing_referential_clarity(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if referential_clarity_validation.get("ok") is not True:
                    continue
            return (
                fallback_text,
                fallback_pool,
                fallback_kind,
                final_emitted_source,
                fallback_strategy,
                fallback_candidate_source,
                composition_meta,
            )

    if strict_social_active and isinstance(eff_resolution, dict):
        return (
            minimal_social_emergency_fallback_line(eff_resolution),
            "strict_social_visibility_minimal",
            "visibility_minimal_social_fallback",
            "minimal_social_emergency_fallback",
            "standard_safe_fallback",
            "minimal_social_emergency_fallback",
            _first_mention_composition_meta(),
        )

    passive_candidates = _passive_scene_pressure_fallback_candidates(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    )
    if passive_candidates:
        fallback_text, fallback_pool, fallback_kind, final_emitted_source, fallback_strategy, fallback_candidate_source, composition_meta = passive_candidates[0]
        return (
            fallback_text,
            fallback_pool,
            fallback_kind,
            final_emitted_source,
            fallback_strategy,
            fallback_candidate_source,
            composition_meta,
        )

    return (
        "For a breath, the scene holds while voices shift around you.",
        "global_scene_narrative",
        "narrative_safe_fallback",
        "global_scene_fallback",
        "standard_safe_fallback",
        "global_scene_fallback",
        _first_mention_composition_meta(),
    )


def _apply_first_mention_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_first_mentions(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    leading_pronoun_detected = bool(validation.get("leading_pronoun_detected"))
    first_explicit_entity_offset = validation.get("first_explicit_entity_offset")
    if not isinstance(first_explicit_entity_offset, int):
        first_explicit_entity_offset = None

    meta["first_mention_validation_passed"] = validation.get("ok") is True
    meta["first_mention_replacement_applied"] = False
    meta["first_mention_violation_kinds"] = violation_kinds
    meta["first_mention_checked_entities"] = checked_entities
    meta["first_mention_leading_pronoun_detected"] = leading_pronoun_detected
    meta["first_mention_first_explicit_entity_offset"] = first_explicit_entity_offset
    meta["first_mention_fallback_strategy"] = None
    meta["first_mention_fallback_candidate_source"] = None
    meta["opening_scene_first_mention_preference_used"] = False
    meta["first_mention_composition_used"] = False
    meta["first_mention_composition_layers"] = _default_first_mention_composition_layers()
    _apply_default_referential_clarity_meta(meta, passed=None)
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return _apply_referential_clarity_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        meta["first_mention_validation_passed"] = None
        out["_final_emission_meta"] = meta
        return out

    opening_scene_preference_used = _opening_scene_preference_active(session)
    prefer_grounded_scene_intro = True

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        fallback_strategy,
        fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
        prefer_grounded_scene_intro=prefer_grounded_scene_intro,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "first_mention_enforcement_replaced"]
        + [f"first_mention_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:first_mention_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["first_mention_validation_passed"] = False
    meta["first_mention_replacement_applied"] = True
    meta["first_mention_fallback_strategy"] = fallback_strategy
    meta["first_mention_fallback_candidate_source"] = fallback_candidate_source
    meta["opening_scene_first_mention_preference_used"] = opening_scene_preference_used
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_first_mention",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_first_mention_replace"})
    return _apply_referential_clarity_enforcement(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
    )


def _apply_referential_clarity_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_referential_clarity(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    meta["referential_clarity_validation_passed"] = validation.get("ok") is True
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = violation_kinds
    meta["referential_clarity_checked_entities"] = checked_entities
    meta["referential_clarity_violation_sample"] = _build_referential_clarity_violation_sample(violations)
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return out

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        meta["referential_clarity_validation_passed"] = None
        out["_final_emission_meta"] = meta
        return out

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        _fallback_strategy,
        _fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "referential_clarity_enforcement_replaced"]
        + [f"referential_clarity_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:referential_clarity_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["referential_clarity_validation_passed"] = False
    meta["referential_clarity_replacement_applied"] = True
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_referential_clarity",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_referential_clarity_replace"})
    return out


def _apply_visibility_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_visibility(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = (
        validation.get("visibility_checked_entities")
        if isinstance(validation.get("visibility_checked_entities"), list)
        else []
    )
    checked_facts = (
        validation.get("visibility_checked_facts")
        if isinstance(validation.get("visibility_checked_facts"), list)
        else []
    )
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )

    meta["first_mention_validation_passed"] = None
    meta["first_mention_replacement_applied"] = False
    meta["first_mention_violation_kinds"] = []
    meta["first_mention_checked_entities"] = []
    meta["first_mention_leading_pronoun_detected"] = False
    meta["first_mention_first_explicit_entity_offset"] = None
    meta["first_mention_fallback_strategy"] = None
    meta["first_mention_fallback_candidate_source"] = None
    meta["opening_scene_first_mention_preference_used"] = False
    meta["first_mention_composition_used"] = False
    meta["first_mention_composition_layers"] = _default_first_mention_composition_layers()
    _apply_default_referential_clarity_meta(meta, passed=None)
    meta["visibility_validation_passed"] = validation.get("ok") is True
    meta["visibility_replacement_applied"] = False
    meta["visibility_violation_kinds"] = violation_kinds
    meta["visibility_violation_sample"] = _build_visibility_violation_sample(violations)
    meta["visibility_checked_entities"] = checked_entities
    meta["visibility_checked_facts"] = checked_facts
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return _apply_first_mention_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )

    if not checked_entities and not checked_facts and _reply_already_has_concrete_interaction(candidate_text):
        meta["visibility_validation_passed"] = None
        out["_final_emission_meta"] = meta
        return out

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        _fallback_strategy,
        _fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "visibility_enforcement_replaced"]
        + [f"visibility_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:visibility_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["visibility_validation_passed"] = False
    meta["visibility_replacement_applied"] = True
    meta["visibility_fallback_pool"] = fallback_pool
    meta["visibility_fallback_kind"] = fallback_kind
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_visibility",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_visibility_replace"})
    return out


def _should_use_neutral_nonprogress_fallback_instead_of_global_stock(
    session: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
) -> bool:
    """Parser-built NPC-target pursuit turns without grounded contact must not get the stock 'voices shift' line."""
    if not isinstance(session, dict):
        return False
    ctx = session.get(NPC_PURSUIT_CONTACT_SESSION_KEY)
    if not isinstance(ctx, dict):
        return False
    if str(ctx.get("commitment_source") or "").strip() != "explicit_player_pursuit":
        return False
    if not isinstance(eff_resolution, dict):
        return False
    rk = str(eff_resolution.get("kind") or "").strip().lower()
    if rk not in SOCIAL_KINDS:
        return False
    target = str(ctx.get("target_npc_id") or "").strip()
    if not target:
        return False
    soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
    if soc.get("offscene_target"):
        return True
    gs = str(soc.get("grounded_speaker_id") or "").strip()
    if gs and gs == target:
        return False
    if soc.get("target_resolved") is True and str(soc.get("npc_id") or "").strip() == target:
        return False
    return True


def _reply_kind(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    sp = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(sp.get("reply_kind") or "").strip().lower()


def apply_final_emission_gate(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    scene: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Hard legal-state gate for the final emitted text."""
    if not isinstance(gm_output, dict):
        return gm_output
    out = dict(gm_output)
    pre_gate_text = _normalize_text(out.get("player_facing_text"))
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]

    eff_resolution, _effective_social_route, coercion_reason = effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    sid = str(scene_id or "").strip()
    strict_social_turn = strict_social_emission_will_apply(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
    )
    merged_for_suppress = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    strict_social_suppressed_non_social_turn = False
    strict_social_suppression_reason: str | None = None
    original_coercion_reason = coercion_reason
    if strict_social_turn:
        do_suppress, sup_reason = strict_social_suppress_non_native_coercion_for_narration_beat(
            resolution if isinstance(resolution, dict) else None,
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            sid,
            coercion_reason=coercion_reason,
            merged_player_prompt=merged_for_suppress,
        )
        if do_suppress:
            strict_social_suppressed_non_social_turn = True
            strict_social_suppression_reason = sup_reason
            strict_social_turn = False
            pre_gate_text = _normalize_text(
                sanitize_player_facing_output(
                    pre_gate_text,
                    {
                        "resolution": resolution if isinstance(resolution, dict) else None,
                        "include_resolution": True,
                        "session": session if isinstance(session, dict) else None,
                        "scene_id": sid,
                        "world": world if isinstance(world, dict) else None,
                        "tags": tag_list,
                    },
                )
            )
            eff_resolution = resolution if isinstance(resolution, dict) else None
            coercion_reason = f"{original_coercion_reason}|suppressed_non_social_narration:{sup_reason}"
            out["player_facing_text"] = pre_gate_text

    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    active_interlocutor = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    npc_id_for_meta = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        npc_id_for_meta = str(sp.get("npc_id") or "").strip()

    res_kind = str((eff_resolution or {}).get("kind") or "").strip().lower() if isinstance(eff_resolution, dict) else ""
    social_ic = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        social_ic = str(sp.get("social_intent_class") or "").strip().lower()

    reasons: List[str] = []
    normalization_ran = False
    text = pre_gate_text

    strict_social_active = bool(strict_social_turn)
    coercion_used = (
        "|" in original_coercion_reason
        or "synthetic" in original_coercion_reason
        or "npc_directed_guard" in original_coercion_reason
    )
    retry_output = any(
        isinstance(t, str) and ("question_retry_fallback" in t or "social_exchange_retry_fallback" in t)
        for t in tag_list
    )

    if strict_social_turn:
        normalization_ran = True
        text, details = build_final_strict_social_response(
            pre_gate_text,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            tags=tag_list,
            session=session if isinstance(session, dict) else None,
            scene_id=str(scene_id or "").strip(),
            world=world if isinstance(world, dict) else None,
        )
        out["player_facing_text"] = text
        final_emitted_source = str(details.get("final_emitted_source") or "unknown_post_gate_writer")
        if retry_output:
            final_emitted_source = "retry_output"
        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        if not details.get("used_internal_fallback"):
            log_final_emission_decision(
                {
                    "stage": "final_emission_gate",
                    "social_route": strict_social_turn,
                    "coercion_reason": coercion_reason,
                    "resolution_kind": res_kind,
                    "social_intent_class": social_ic,
                    "active_interlocutor": active_interlocutor or None,
                    "candidate_ok": True,
                    "rejection_reasons": [],
                    "fallback_pool": str(details.get("fallback_pool") or "none"),
                    "fallback_kind": str(details.get("fallback_kind") or "none"),
                }
            )
            out["_final_emission_meta"] = {
                "final_route": "accept_candidate",
                "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
                "strict_social_active": strict_social_active,
                "coercion_used": coercion_used,
                "active_interlocutor_id": active_interlocutor or None,
                "npc_id": npc_id_for_meta or None,
                "normalization_ran": normalization_ran,
                "candidate_validation_passed": True,
                "deterministic_social_fallback_attempted": bool(details.get("deterministic_attempted")),
                "deterministic_social_fallback_passed": bool(details.get("deterministic_passed")),
                "final_emitted_source": final_emitted_source,
                "post_gate_mutation_detected": post_gate_mutation_detected,
                "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
                "coercion_reason": coercion_reason,
                "candidate_quality_degraded": bool(details.get("candidate_quality_degraded")),
                "resolved_answer_preferred": bool(details.get("resolved_answer_preferred")),
                "resolved_answer_source": details.get("resolved_answer_source"),
                "resolved_answer_preference_reason": details.get("resolved_answer_preference_reason"),
                "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
                "strict_social_suppression_reason": strict_social_suppression_reason,
                "social_emission_integrity_replaced": bool(details.get("social_emission_integrity_replaced")),
                "social_emission_integrity_reasons": details.get("social_emission_integrity_reasons"),
                "social_emission_integrity_fallback_kind": details.get("social_emission_integrity_fallback_kind"),
            }
            out = _apply_visibility_enforcement(
                out,
                session=session,
                scene=scene,
                world=world,
                scene_id=sid,
                eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                active_interlocutor=active_interlocutor,
                strict_social_active=strict_social_active,
                strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            )
            log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
            return _finalize_emission_output(out, pre_gate_text=pre_gate_text)

        fb_kind = str(details.get("fallback_kind") or "none")
        deterministic_attempted = bool(details.get("deterministic_attempted"))
        deterministic_passed = bool(details.get("deterministic_passed"))
        fallback_pool = str(details.get("fallback_pool") or "social_deterministic")
        candidate_ok = False
        rejection_reasons = details.get("rejection_reasons") if isinstance(details.get("rejection_reasons"), list) else []

        out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fb_kind}"]
        if final_emitted_source == "minimal_social_emergency_fallback":
            out["tags"] = list(out["tags"]) + ["terminal_strict_social_emission", "strict_social_terminal_safe"]

        if details.get("route_illegal_intercepted"):
            dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
            preview = str(details.get("intercepted_preview") or "")
            out["debug_notes"] = (
                (dbg + " | " if dbg else "")
                + f"final_emission_gate:route_illegal_writer_intercepted:{preview[:80]}"
            )

        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + "final_emission_gate:replaced:"
            + ",".join([str(r) for r in rejection_reasons[:8] if isinstance(r, str)])
        )
        log_final_emission_decision(
            {
                "stage": "final_emission_gate",
                "social_route": strict_social_turn,
                "coercion_reason": coercion_reason,
                "resolution_kind": res_kind,
                "social_intent_class": social_ic,
                "active_interlocutor": active_interlocutor or None,
                "candidate_ok": candidate_ok,
                "rejection_reasons": [str(r) for r in rejection_reasons[:12] if isinstance(r, str)],
                "fallback_pool": fallback_pool,
                "fallback_kind": fb_kind,
            }
        )
        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        out["_final_emission_meta"] = {
            "final_route": "replaced",
            "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
            "strict_social_active": strict_social_active,
            "coercion_used": coercion_used,
            "active_interlocutor_id": active_interlocutor or None,
            "npc_id": npc_id_for_meta or None,
            "normalization_ran": normalization_ran,
            "candidate_validation_passed": False,
            "deterministic_social_fallback_attempted": deterministic_attempted,
            "deterministic_social_fallback_passed": deterministic_passed,
            "final_emitted_source": final_emitted_source,
            "post_gate_mutation_detected": post_gate_mutation_detected,
            "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
            "coercion_reason": coercion_reason,
            "rejection_reasons_sample": [str(r) for r in rejection_reasons[:8] if isinstance(r, str)],
            "candidate_quality_degraded": bool(details.get("candidate_quality_degraded")),
            "resolved_answer_preferred": bool(details.get("resolved_answer_preferred")),
            "resolved_answer_source": details.get("resolved_answer_source"),
            "resolved_answer_preference_reason": details.get("resolved_answer_preference_reason"),
            "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
            "strict_social_suppression_reason": strict_social_suppression_reason,
        }
        out = _apply_visibility_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
        return _finalize_emission_output(out, pre_gate_text=pre_gate_text)

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")
    if _passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=sid,
    ) and not _reply_already_has_concrete_interaction(text):
        reasons.append("passive_scene_pressure_missing_concrete_beat")

    candidate_ok = not bool(reasons)
    fallback_pool = "none"
    fallback_kind = "none"
    deterministic_attempted = False
    deterministic_passed = False
    final_emitted_source = "unknown_post_gate_writer"

    if not reasons:
        out["player_facing_text"] = text
        final_emitted_source = "generated_candidate"
        if retry_output:
            final_emitted_source = "retry_output"

        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        log_final_emission_decision(
            {
                "stage": "final_emission_gate",
                "social_route": strict_social_turn,
                "coercion_reason": coercion_reason,
                "resolution_kind": res_kind,
                "social_intent_class": social_ic,
                "active_interlocutor": active_interlocutor or None,
                "candidate_ok": True,
                "rejection_reasons": [],
                "fallback_pool": fallback_pool,
                "fallback_kind": fallback_kind,
            }
        )
        out["_final_emission_meta"] = {
            "final_route": "accept_candidate",
            "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
            "strict_social_active": strict_social_active,
            "coercion_used": coercion_used,
            "active_interlocutor_id": active_interlocutor or None,
            "npc_id": npc_id_for_meta or None,
            "normalization_ran": normalization_ran,
            "candidate_validation_passed": True,
            "deterministic_social_fallback_attempted": False,
            "deterministic_social_fallback_passed": False,
            "final_emitted_source": final_emitted_source,
            "post_gate_mutation_detected": post_gate_mutation_detected,
            "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
            "coercion_reason": coercion_reason,
            "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
            "strict_social_suppression_reason": strict_social_suppression_reason,
        }
        out = _apply_visibility_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        )
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
        return _finalize_emission_output(out, pre_gate_text=pre_gate_text)

    # Non-social replace path only (strict-social replacement is handled in build_final_strict_social_response).
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    if (
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
    ):
        mini_res: Dict[str, Any] = {
            "kind": "question",
            "social": {
                "npc_id": active_interlocutor,
                "npc_name": _npc_display_name_for_emission(world, sid, active_interlocutor),
                "social_intent_class": "social_exchange",
            },
        }
        fallback_pool = "social_active_interlocutor_minimal"
        fallback_text = minimal_social_emergency_fallback_line(mini_res)
        fallback_kind = "social_interlocutor_fallback"
        final_emitted_source = "social_interlocutor_minimal_fallback"
    else:
        passive_candidates = _passive_scene_pressure_fallback_candidates(
            session=session if isinstance(session, dict) else None,
            scene=scene,
            scene_id=sid,
        )
        if passive_candidates:
            (
                fallback_text,
                fallback_pool,
                fallback_kind,
                final_emitted_source,
                _fallback_strategy,
                _fallback_candidate_source,
                _composition_meta,
            ) = passive_candidates[0]
        elif _should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution):
            fallback_pool = "npc_pursuit_fail_closed_neutral"
            fallback_text = "Nothing confirms progress toward that lead yet—the moment stays unresolved."
            fallback_kind = "npc_pursuit_neutral_nonprogress"
            final_emitted_source = "npc_pursuit_neutral_fallback"
        else:
            fallback_pool = "global_scene_narrative"
            fallback_text = "For a breath, the scene holds while voices shift around you."
            fallback_kind = "narrative_safe_fallback"
            final_emitted_source = "global_scene_fallback"
    deterministic_attempted = False
    deterministic_passed = False

    out["player_facing_text"] = fallback_text
    out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fallback_kind}"]

    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:replaced:"
        + ",".join(reasons[:8])
    )
    log_final_emission_decision(
        {
            "stage": "final_emission_gate",
            "social_route": strict_social_turn,
            "coercion_reason": coercion_reason,
            "resolution_kind": res_kind,
            "social_intent_class": social_ic,
            "active_interlocutor": active_interlocutor or None,
            "candidate_ok": candidate_ok,
            "rejection_reasons": reasons[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
        }
    )
    gate_out_text = _normalize_text(out.get("player_facing_text"))
    post_gate_mutation_detected = pre_gate_text != gate_out_text

    out["_final_emission_meta"] = {
        "final_route": "replaced",
        "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
        "strict_social_active": strict_social_active,
        "coercion_used": coercion_used,
        "active_interlocutor_id": active_interlocutor or None,
        "npc_id": npc_id_for_meta or None,
        "normalization_ran": normalization_ran,
        "candidate_validation_passed": False,
        "deterministic_social_fallback_attempted": deterministic_attempted,
        "deterministic_social_fallback_passed": deterministic_passed,
        "final_emitted_source": final_emitted_source,
        "post_gate_mutation_detected": post_gate_mutation_detected,
        "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
        "coercion_reason": coercion_reason,
        "rejection_reasons_sample": reasons[:8],
        "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
        "strict_social_suppression_reason": strict_social_suppression_reason,
    }
    out = _apply_visibility_enforcement(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
    )
    log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
    return _finalize_emission_output(out, pre_gate_text=pre_gate_text)
