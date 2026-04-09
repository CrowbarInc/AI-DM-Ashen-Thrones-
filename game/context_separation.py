"""Context separation contract: ambient world pressure vs. local interaction focus (read-only).

Conservative, deterministic checks that **background tension** may color wording or add optional
hooks, but must not **hijack topic**, **substitute for answers**, **force interpersonal tone
shifts**, or **over-weight** ambient commentary relative to the present exchange.

This module does not mutate world state; it consumes published contract slices only.
"""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Shared text utilities (aligned with ``game.anti_railroading``)
# ---------------------------------------------------------------------------

_DIALOGUE_SPAN_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r'"[^"\n]*"'),
    re.compile(r"“[^”\n]*”"),
    re.compile(r"‘[^’\n]*’"),
    re.compile(r"(?<!\w)'[^'\n]*'(?!\w)"),
)

_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "to", "of", "in", "on", "for", "with", "is", "are",
    "was", "were", "be", "been", "being", "it", "this", "that", "these", "those", "you", "your",
    "i", "me", "my", "we", "our", "they", "them", "their", "he", "she", "his", "her", "as", "at",
    "by", "from", "into", "about", "not", "no", "yes", "so", "do", "does", "did", "can", "could",
    "would", "should", "will", "just", "very", "too", "also", "then", "there", "here", "how",
    "what", "when", "where", "why", "who", "which", "than", "out", "up", "down", "over", "again",
})


def _clean_str(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _normalize_scan_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split()).strip().lower()
    if not text:
        return ""
    punct = string.punctuation
    while text and text[0] in punct:
        text = text[1:].lstrip().lower()
        text = " ".join(text.split()).strip()
    while text and text[-1] in punct:
        text = text[:-1].rstrip().lower()
        text = " ".join(text.split()).strip()
    return text


def _mask_dialogue_spans(text: str) -> str:
    if not text:
        return ""
    masked = list(text)
    for pattern in _DIALOGUE_SPAN_PATTERNS:
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                masked[index] = " "
    return "".join(masked)


def _split_sentences(masked_text: str, original_text: str) -> List[Tuple[int, int, str]]:
    if not original_text:
        return []
    sentences: List[Tuple[int, int, str]] = []
    cursor = 0
    for match in re.finditer(r"[.!?\n]+", masked_text):
        raw_segment = original_text[cursor : match.start()]
        stripped = raw_segment.strip()
        if stripped:
            lead = len(raw_segment) - len(raw_segment.lstrip())
            trail = len(raw_segment) - len(raw_segment.rstrip())
            sentences.append((cursor + lead, match.start() - trail, stripped))
        cursor = match.end()
    tail = original_text[cursor:]
    stripped_tail = tail.strip()
    if stripped_tail:
        lead = len(tail) - len(tail.lstrip())
        trail = len(tail) - len(tail.rstrip())
        sentences.append((cursor + lead, len(original_text) - trail, stripped_tail))
    return sentences


def _tokenize_topics(text: str, *, max_tokens: int = 14) -> List[str]:
    low = _normalize_scan_text(text)
    if not low:
        return []
    out: List[str] = []
    for raw in re.split(r"[^\w]+", low):
        w = raw.strip().lower()
        if len(w) < 3 or w in _STOPWORDS:
            continue
        if w not in out:
            out.append(w)
        if len(out) >= max_tokens:
            break
    return out


def _dedupe_preserve(items: Sequence[str]) -> Tuple[str, ...]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        s = _clean_str(item)
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return tuple(out)


# ---------------------------------------------------------------------------
# Resolution helpers (mirror anti-railroading semantics)
# ---------------------------------------------------------------------------

def _bool_from_skill_check(sc: Mapping[str, Any]) -> Optional[bool]:
    if "success" not in sc:
        return None
    v = sc.get("success")
    if isinstance(v, bool):
        return v
    return None


def _resolution_pending_player_roll(res: Mapping[str, Any]) -> bool:
    if not res.get("requires_check"):
        return False
    if res.get("skill_check"):
        return False
    return isinstance(res.get("check_request"), dict)


def _resolution_has_authoritative_outcome(res: Mapping[str, Any]) -> bool:
    if _resolution_pending_player_roll(res):
        return False
    sc = res.get("skill_check")
    if isinstance(sc, Mapping) and _bool_from_skill_check(sc) is not None:
        return True
    success = res.get("success")
    if isinstance(success, bool):
        return True
    combat = res.get("combat")
    if isinstance(combat, Mapping) and isinstance(combat.get("hit"), bool):
        return True
    if bool(res.get("resolved_transition")):
        return True
    clue_id = res.get("clue_id")
    if clue_id is not None and str(clue_id).strip():
        return True
    dc = res.get("discovered_clues")
    if isinstance(dc, list) and any(isinstance(x, str) and x.strip() for x in dc):
        return True
    return False


# ---------------------------------------------------------------------------
# Vocabulary: background pressure, dodge phrases, crisis scene, player intent
# ---------------------------------------------------------------------------

_BACKGROUND_PRESSURE_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:war|wars|wartime|campaign|front\s+lines?|invasion|siege)\b", re.IGNORECASE),
    re.compile(r"\b(?:unrest|uprising|rebellion|revolt|insurgent|faction|factions)\b", re.IGNORECASE),
    re.compile(r"\b(?:politic\w*|throne|crown|succession|treaty|embargo|sanction)\b", re.IGNORECASE),
    re.compile(r"\b(?:empire|border|borders|marshal|occupation|occupying)\b", re.IGNORECASE),
    re.compile(r"\b(?:looming|gathering)\s+(?:storm|threat|armies?|host)\b", re.IGNORECASE),
    re.compile(r"\b(?:rumors?\s+of\s+war|open\s+war|total\s+war)\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+realm|the\s+kingdom|the\s+capital)\s+(?:burn|bleed|tears?\s+itself)\b", re.IGNORECASE),
)

_STRONG_SCENE_PRESSURE_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:riot|riots|raid|raids|crackdown|martial\s+law|purge|curfew)\b", re.IGNORECASE),
    re.compile(r"\b(?:panic|stampede|massacre|battle\s+in\s+the\s+streets)\b", re.IGNORECASE),
    re.compile(r"\b(?:house\s+to\s+house|doors?\s+kicked|arrest\s+waves?)\b", re.IGNORECASE),
)

_PLAYER_SEEKS_WORLD_DANGER_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:danger|dangerous|unsafe|safe|safety)\b", re.IGNORECASE),
    re.compile(r"\b(?:unrest|tension|tense|troops|soldiers|patrol|patrols)\b", re.IGNORECASE),
    re.compile(r"\b(?:war|raid|raids|riot|crackdown|faction|factions)\b", re.IGNORECASE),
    re.compile(r"\b(?:what(?:'s| is)\s+going\s+on|what\s+is\s+happening)\b", re.IGNORECASE),
    re.compile(r"\b(?:should\s+i\s+be\s+worried|how\s+bad\s+is\s+it)\b", re.IGNORECASE),
)

_CRISIS_SCENE_SUMMARY_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:panic|raid|raids|riot|crackdown|martial|purge|battle|siege)\b", re.IGNORECASE),
    re.compile(r"\b(?:house\s+to\s+house|doors?\s+smash|arrests?)\b", re.IGNORECASE),
)

_WORLD_INTERACTION_KINDS: frozenset[str] = frozenset({
    "investigate",
    "discover_clue",
    "travel",
})

_PRESSURE_SUBSTITUTION_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:impossible|hard)\s+to\s+say\b.+\b(?:unrest|tension|chaos|war|times)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:no\s+one\s+can\s+say|who\s+can\s+say)\b.+\b(?:these\s+times|this\s+city|the\s+war)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwith\s+(?:everything|the\s+city|the\s+war)\b.+\b(?:can't|cannot)\b.+\b(?:say|tell|answer)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+answer\s+is\s+lost|any\s+answer\s+is\s+swallowed)\b.+\b(?:instability|chaos|war)\b",
        re.IGNORECASE,
    ),
)

_PRESSURE_SUBSTITUTION_LIGHT_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\btoo\s+(?:tense|volatile)\s+to\s+(?:say|tell|answer)\b", re.IGNORECASE),
    re.compile(r"\bwho\s+could\s+know\b.+\b(?:with|under)\b.+\b(?:war|unrest|occupation)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+(?:the\s+time|a\s+time)\s+for\s+(?:answers|details)\b", re.IGNORECASE),
)

_TONE_SHIFT_VERBAL_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:or\s+else|you(?:'ll| will)\s+regret|last\s+chance|try\s+me)\b", re.IGNORECASE),
    re.compile(r"\b(?:i(?:'ll| will)\s+(?:hurt|kill|break)\s+you)\b", re.IGNORECASE),
)

_TONE_SHIFT_GUARDED_HARSH_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:back\s+off|drop\s+it|enough)\b", re.IGNORECASE),
    re.compile(r"\b(?:watch\s+yourself|careful\s+how\s+you)\b", re.IGNORECASE),
)

_BACKGROUND_JUSTIFICATION_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:the\s+city|the\s+ward|the\s+streets|times\s+like\s+these)\b", re.IGNORECASE),
    re.compile(r"\b(?:with\s+the\s+war|with\s+unrest|with\s+everything\s+going\s+on)\b", re.IGNORECASE),
    re.compile(r"\b(?:tension|nerves|on\s+edge)\b", re.IGNORECASE),
)


def _player_seeks_world_danger_info(player_text: str) -> bool:
    low = _normalize_scan_text(player_text)
    if not low:
        return False
    return any(p.search(low) for p in _PLAYER_SEEKS_WORLD_DANGER_RES)


def _scene_summary_is_crisis(summary: str) -> bool:
    low = _normalize_scan_text(summary)
    if not low:
        return False
    return any(p.search(low) for p in _CRISIS_SCENE_SUMMARY_RES)


def _player_asks_concrete_question(player_text: str) -> bool:
    raw = _clean_str(player_text)
    if "?" not in raw:
        return False
    low = _normalize_scan_text(raw)
    return bool(
        re.search(
            r"\b(?:what|where|when|who|whom|which|how\s+much|how\s+many|how\s+long|price|cost)\b",
            low,
        )
    )


def _ingest_lead_label(row: Any, labels: List[str]) -> None:
    if not isinstance(row, Mapping):
        return
    for key in ("title", "label", "name", "short_label"):
        v = row.get(key)
        if isinstance(v, str) and v.strip():
            labels.append(v.strip())
            break


def _walk_leads(bucket: Any, labels: List[str]) -> None:
    if isinstance(bucket, list):
        for item in bucket:
            _ingest_lead_label(item, labels)
    elif isinstance(bucket, Mapping):
        for v in bucket.values():
            if isinstance(v, Mapping):
                _ingest_lead_label(v, labels)
            elif isinstance(v, list):
                _walk_leads(v, labels)


def _collect_allowed_contextual_labels(
    *,
    prompt_leads: Any,
    active_pending_leads: Any,
    session_view: Mapping[str, Any],
    follow_surface: Any,
) -> Tuple[str, ...]:
    labels: List[str] = []
    _walk_leads(prompt_leads, labels)
    _walk_leads(active_pending_leads, labels)
    for key in ("surfaced_leads", "prompt_leads", "active_pending_leads", "leads_for_prompt"):
        _walk_leads(session_view.get(key), labels)
    if isinstance(follow_surface, Mapping):
        for key in ("labels", "titles", "surfaced_lead_labels"):
            raw = follow_surface.get(key)
            if isinstance(raw, list):
                for x in raw:
                    if isinstance(x, str) and x.strip():
                        labels.append(x.strip())
    return _dedupe_preserve(labels)


def _collect_compressed_pressures(
    compressed_world_pressures: Any,
    session_view: Mapping[str, Any],
) -> Tuple[str, ...]:
    items: List[str] = []
    if isinstance(compressed_world_pressures, (list, tuple)):
        for x in compressed_world_pressures:
            if isinstance(x, str) and x.strip():
                items.append(x.strip())
    for key in ("compressed_world_pressures", "world_pressures", "ambient_pressures", "surfaced_pressures"):
        raw = session_view.get(key)
        if isinstance(raw, list):
            for x in raw:
                if isinstance(x, str) and x.strip():
                    items.append(x.strip())
    return _dedupe_preserve(items)


def _sentence_hits_pressure(sentence: str) -> bool:
    low = sentence.lower()
    return any(p.search(low) for p in _BACKGROUND_PRESSURE_RES)


def _sentence_hits_strong_pressure(sentence: str) -> bool:
    low = sentence.lower()
    if any(p.search(low) for p in _STRONG_SCENE_PRESSURE_RES):
        return True
    return _sentence_hits_pressure(sentence)


def _sentence_topic_overlap(sentence: str, topics: Sequence[str]) -> bool:
    if not topics:
        return False
    low = sentence.lower()
    for t in topics:
        frag = _normalize_scan_text(t)
        if len(frag) >= 3 and frag in low:
            return True
        if len(frag) >= 3 and frag in _normalize_scan_text(sentence):
            return True
    return False


def _opening_sentence(
    masked_full: str,
    raw: str,
) -> str:
    sents = _split_sentences(masked_full, raw)
    if not sents:
        return ""
    return sents[0][2]


def _count_pressure_sentences(masked_full: str, raw: str) -> int:
    n = 0
    for _, _, sent in _split_sentences(masked_full, raw):
        if _sentence_hits_strong_pressure(sent):
            n += 1
    return n


def _pressure_weight_ratio(masked_full: str, raw: str) -> float:
    sents = _split_sentences(masked_full, raw)
    if not sents:
        return 0.0
    heavy = 0
    for _, _, sent in sents:
        if _sentence_hits_strong_pressure(sent):
            heavy += 1
    return heavy / float(len(sents))


def _sentence_unearned_hostile_with_background(sentence: str) -> bool:
    low = sentence.lower()
    has_bg = any(p.search(low) for p in _BACKGROUND_JUSTIFICATION_RES) or _sentence_hits_pressure(sentence)
    if not has_bg:
        return False
    harsh = any(p.search(low) for p in _TONE_SHIFT_VERBAL_RES) or any(
        p.search(low) for p in _TONE_SHIFT_GUARDED_HARSH_RES
    )
    return harsh


def _sentence_pressure_substitution(sentence: str) -> bool:
    low = sentence.lower()
    if any(p.search(low) for p in _PRESSURE_SUBSTITUTION_RES):
        return True
    if any(p.search(low) for p in _PRESSURE_SUBSTITUTION_LIGHT_RES):
        return True
    return False


def build_context_separation_contract(
    *,
    resolution: Mapping[str, Any] | None = None,
    player_text: str | None = None,
    session_view: Mapping[str, Any] | None = None,
    scene_envelope: Mapping[str, Any] | None = None,
    scene_summary: str | None = None,
    turn_summary: str | None = None,
    speaker_selection_contract: Mapping[str, Any] | None = None,
    scene_state_anchor_contract: Mapping[str, Any] | None = None,
    narration_visibility: Mapping[str, Any] | None = None,
    tone_escalation_contract: Mapping[str, Any] | None = None,
    compressed_world_pressures: Sequence[str] | None = None,
    prompt_leads: Any = None,
    active_pending_leads: Any = None,
    follow_surface: Any = None,
) -> Dict[str, Any]:
    """Assemble inspectable context-separation policy from published inputs (no mutation)."""
    res = _mapping_or_empty(resolution)
    sess = _mapping_or_empty(session_view)
    sp = _mapping_or_empty(speaker_selection_contract)
    sac = _mapping_or_empty(scene_state_anchor_contract)
    tec = _mapping_or_empty(tone_escalation_contract)

    pt = _clean_str(player_text)

    summary_bits: List[str] = []
    if scene_summary:
        summary_bits.append(_clean_str(scene_summary))
    if turn_summary:
        summary_bits.append(_clean_str(turn_summary))
    if isinstance(scene_envelope, Mapping):
        inner = scene_envelope.get("scene")
        if isinstance(inner, Mapping):
            s = _clean_str(inner.get("summary"))
            if s:
                summary_bits.append(s)
    scene_focus_summary = " ".join(summary_bits).strip()
    if len(scene_focus_summary) > 360:
        scene_focus_summary = scene_focus_summary[:357].rstrip() + "..."

    interaction_kind = (
        _clean_str(res.get("kind")) or _clean_str(sp.get("interaction_mode")) or "unknown"
    )

    player_intent_summary = pt[:200] if pt else "(no player text)"
    if len(player_intent_summary) > 200:
        player_intent_summary = player_intent_summary[:197].rstrip() + "..."

    anchor_tokens: List[str] = []
    for key in ("location_tokens", "actor_tokens", "player_action_tokens"):
        raw_tok = sac.get(key)
        if isinstance(raw_tok, list):
            for x in raw_tok:
                if isinstance(x, str) and x.strip():
                    anchor_tokens.append(x.strip())

    primary_topics = _dedupe_preserve([*_tokenize_topics(pt), *anchor_tokens])

    allowed_contextual_topics = _collect_allowed_contextual_labels(
        prompt_leads=prompt_leads,
        active_pending_leads=active_pending_leads,
        session_view=sess,
        follow_surface=follow_surface,
    )

    ambient_pressure_topics = _collect_compressed_pressures(compressed_world_pressures, sess)

    player_world_danger = _player_seeks_world_danger_info(pt)
    scene_crisis = _scene_summary_is_crisis(scene_focus_summary)
    interaction_about_world = interaction_kind in _WORLD_INTERACTION_KINDS or _player_seeks_world_danger_info(pt)

    auth_outcome = _resolution_has_authoritative_outcome(res) if res else False
    consequence_now_relevant = auth_outcome or bool(res.get("consequence_id") or res.get("immediate_consequence"))

    pressure_focus_allowed = (
        player_world_danger
        or scene_crisis
        or interaction_about_world
        or consequence_now_relevant
    )

    allow_verbal_from_tone = bool(tec.get("allow_verbal_pressure")) if tec else True
    allow_threat_from_tone = bool(tec.get("allow_explicit_threat")) if tec else True

    enabled = True
    forbid_topic_hijack = True
    forbid_pressure_answer_substitution = True
    forbid_unearned_tone_shift_from_background_pressure = True
    allow_brief_pressure_coloring = True
    allow_optional_consequence_signposting = True
    max_pressure_sentences_without_player_prompt = 2

    debug_inputs: Dict[str, Any] = {
        "has_resolution": isinstance(resolution, Mapping),
        "has_session_view": bool(sess),
        "has_scene_envelope": isinstance(scene_envelope, Mapping),
        "has_scene_summary": bool(_clean_str(scene_summary)),
        "has_turn_summary": bool(_clean_str(turn_summary)),
        "has_speaker_selection_contract": bool(sp),
        "has_scene_state_anchor_contract": bool(sac),
        "has_narration_visibility": narration_visibility is not None,
        "has_tone_escalation_contract": bool(tec),
        "has_compressed_world_pressures": compressed_world_pressures is not None,
        "has_prompt_leads": prompt_leads is not None,
        "has_active_pending_leads": active_pending_leads is not None,
        "has_follow_surface": follow_surface is not None,
        "player_text_nonempty": bool(pt),
        "primary_topic_count": len(primary_topics),
        "ambient_pressure_topic_count": len(ambient_pressure_topics),
    }
    debug_flags = {
        "player_seeks_world_danger_info": player_world_danger,
        "scene_summary_crisis": scene_crisis,
        "interaction_kind_worldish": interaction_about_world,
        "authoritative_or_consequence_relevant": consequence_now_relevant,
        "pressure_focus_allowed": pressure_focus_allowed,
        "tone_allow_verbal_pressure": allow_verbal_from_tone,
        "tone_allow_explicit_threat": allow_threat_from_tone,
    }
    debug_reason = (
        f"context_separation: pressure_focus_allowed={pressure_focus_allowed} "
        f"primary_topics={len(primary_topics)} ambient={len(ambient_pressure_topics)}"
    )

    return {
        "enabled": enabled,
        "scene_focus_summary": scene_focus_summary,
        "interaction_kind": interaction_kind,
        "player_intent_summary": player_intent_summary,
        "primary_topics": primary_topics,
        "allowed_contextual_topics": allowed_contextual_topics,
        "ambient_pressure_topics": ambient_pressure_topics,
        "forbid_topic_hijack": forbid_topic_hijack,
        "forbid_pressure_answer_substitution": forbid_pressure_answer_substitution,
        "forbid_unearned_tone_shift_from_background_pressure": forbid_unearned_tone_shift_from_background_pressure,
        "allow_brief_pressure_coloring": allow_brief_pressure_coloring,
        "allow_optional_consequence_signposting": allow_optional_consequence_signposting,
        "max_pressure_sentences_without_player_prompt": max_pressure_sentences_without_player_prompt,
        "tone_escalation_contract": dict(tec) if tec else {},
        "debug_inputs": debug_inputs,
        "debug_flags": debug_flags,
        "debug_reason": debug_reason,
    }


def validate_context_separation(
    text: str,
    contract: Mapping[str, Any] | None,
    *,
    player_text: str = "",
    resolution: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate narration *text* against ``build_context_separation_contract`` output."""
    if not isinstance(contract, Mapping):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": ["invalid_contract"],
            "assertion_flags": {
                "topic_hijack_background_pressure": False,
                "pressure_answer_substitution": False,
                "ambient_pressure_forced_tone_shift": False,
                "scene_focus_displaced_by_world_pressure": False,
                "pressure_overweighting": False,
            },
            "debug": {"reason": "invalid_contract"},
        }

    if not contract.get("enabled"):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "assertion_flags": {
                "topic_hijack_background_pressure": False,
                "pressure_answer_substitution": False,
                "ambient_pressure_forced_tone_shift": False,
                "scene_focus_displaced_by_world_pressure": False,
                "pressure_overweighting": False,
            },
            "debug": {"reason": "contract_disabled"},
        }

    pt = _clean_str(player_text)
    res_map = _mapping_or_empty(resolution)

    pressure_focus_allowed = bool(contract.get("debug_flags", {}).get("pressure_focus_allowed"))
    if _resolution_has_authoritative_outcome(res_map):
        pressure_focus_allowed = True
    if _player_seeks_world_danger_info(pt):
        pressure_focus_allowed = True

    primary_raw = contract.get("primary_topics")
    primary_topics: Tuple[str, ...] = tuple(primary_raw) if isinstance(primary_raw, tuple) else tuple()

    max_pressure = int(contract.get("max_pressure_sentences_without_player_prompt") or 2)

    raw = str(text or "")
    masked_full = _mask_dialogue_spans(raw)

    flags = {
        "topic_hijack_background_pressure": False,
        "pressure_answer_substitution": False,
        "ambient_pressure_forced_tone_shift": False,
        "scene_focus_displaced_by_world_pressure": False,
        "pressure_overweighting": False,
    }

    if not pressure_focus_allowed and contract.get("forbid_topic_hijack"):
        if _player_asks_concrete_question(pt) and len(raw) > 60:
            opening = _opening_sentence(masked_full, raw)
            if opening:
                op_low = opening.lower()
                strong_opening = _sentence_hits_strong_pressure(opening)
                overlap = _sentence_topic_overlap(opening, primary_topics)
                # Conservative hijack: opening is dominated by strong ambient pressure and ignores local topics.
                if strong_opening and not overlap and len(op_low.split()) > 8:
                    flags["topic_hijack_background_pressure"] = True
                    flags["scene_focus_displaced_by_world_pressure"] = True

    if not pressure_focus_allowed and contract.get("forbid_pressure_answer_substitution"):
        for _, _, sent in _split_sentences(masked_full, raw):
            if _sentence_pressure_substitution(sent):
                flags["pressure_answer_substitution"] = True
                break

    if not pressure_focus_allowed and contract.get("forbid_unearned_tone_shift_from_background_pressure"):
        tec = _mapping_or_empty(contract.get("tone_escalation_contract"))
        allow_v = bool(tec.get("allow_verbal_pressure", True))
        allow_t = bool(tec.get("allow_explicit_threat", True))
        df = contract.get("debug_flags")
        if isinstance(df, Mapping):
            if "tone_allow_verbal_pressure" in df:
                allow_v = bool(df.get("tone_allow_verbal_pressure"))
            if "tone_allow_explicit_threat" in df:
                allow_t = bool(df.get("tone_allow_explicit_threat"))

        for _, _, sent in _split_sentences(masked_full, raw):
            if not _sentence_unearned_hostile_with_background(sent):
                continue
            low = sent.lower()
            explicit = any(p.search(low) for p in _TONE_SHIFT_VERBAL_RES)
            verbal = explicit or any(p.search(low) for p in _TONE_SHIFT_GUARDED_HARSH_RES)
            if explicit and not allow_t:
                flags["ambient_pressure_forced_tone_shift"] = True
            elif verbal and not allow_v:
                flags["ambient_pressure_forced_tone_shift"] = True

    if not pressure_focus_allowed:
        ps = _count_pressure_sentences(masked_full, raw)
        ratio = _pressure_weight_ratio(masked_full, raw)
        sents = _split_sentences(masked_full, raw)
        if (
            len(sents) >= 3
            and ps > max_pressure
            and ratio >= 0.5
            and _player_asks_concrete_question(pt)
        ):
            flags["pressure_overweighting"] = True
        # Displacement: most sentences are pressure-heavy for a local-focused turn.
        if len(sents) >= 4 and ratio >= 0.62 and not _player_seeks_world_danger_info(pt):
            flags["scene_focus_displaced_by_world_pressure"] = True

    failure_reasons: List[str] = []
    if flags["topic_hijack_background_pressure"]:
        failure_reasons.append("topic_hijack_background_pressure")
    if flags["pressure_answer_substitution"]:
        failure_reasons.append("pressure_answer_substitution")
    if flags["ambient_pressure_forced_tone_shift"]:
        failure_reasons.append("ambient_pressure_forced_tone_shift")
    if flags["scene_focus_displaced_by_world_pressure"]:
        failure_reasons.append("scene_focus_displaced_by_world_pressure")
    if flags["pressure_overweighting"]:
        failure_reasons.append("pressure_overweighting")

    passed = not failure_reasons

    return {
        "checked": True,
        "passed": passed,
        "failure_reasons": list(dict.fromkeys(failure_reasons)),
        "assertion_flags": {k: bool(v) for k, v in flags.items()},
        "debug": {
            "pressure_focus_allowed": pressure_focus_allowed,
            "normalized_nonempty": bool(_normalize_scan_text(raw)),
        },
    }


def context_separation_repair_hints(
    violations: Sequence[str],
    contract: Mapping[str, Any] | None = None,
) -> List[str]:
    """Minimal composable repair lines from machine-readable violation keys."""
    _ = contract
    hints: List[str] = []
    vset = {str(x) for x in violations if isinstance(x, str) and x.strip()}
    if "topic_hijack_background_pressure" in vset or "scene_focus_displaced_by_world_pressure" in vset:
        hints.append("Answer the local interaction first; preserve scene focus, active speaker, and immediate action.")
    if "pressure_answer_substitution" in vset:
        hints.append(
            "Give the substantive reply the exchange requires; do not substitute vague background instability for an answer."
        )
    if "ambient_pressure_forced_tone_shift" in vset:
        hints.append(
            "Remove alarmist or hostile escalation not justified by the interaction itself; keep interpersonal tone bounded."
        )
    if "pressure_overweighting" in vset:
        hints.append(
            "Keep ambient pressure to one brief supporting clause; convert broad pressure into optional color or consequence, not the main point."
        )
    return hints
