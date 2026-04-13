"""Interaction continuity contract, validation, and minimal deterministic repair.

Reads authoritative interaction and scene state from :mod:`game.interaction_context` and
:mod:`game.storage` when *building* contracts. ``validate_interaction_continuity`` and
``repair_interaction_continuity`` are pure checks/repairs on candidate text plus resolved
contract / validator payloads (repair must not re-read session state).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Tuple

from game.final_emission_text import _RESPONSE_TYPE_VALUES, _normalize_text
from game.interaction_context import (
    assert_valid_speaker,
    build_speaker_selection_contract,
    inspect,
)
from game.storage import get_scene_state

CONTINUITY_STRENGTH_VALUES = frozenset({"none", "soft", "strong"})


def _clean_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    s = value.strip()
    return s


def _normalize_response_type_contract(raw: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    required = str(raw.get("required_response_type") or "").strip().lower()
    if required not in _RESPONSE_TYPE_VALUES:
        return None
    out = dict(raw)
    out["required_response_type"] = required
    return out


def _effective_scene_id(
    scene_id: str | None,
    scene_envelope: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> str:
    sid = _clean_string(scene_id)
    if sid:
        return sid
    if isinstance(scene_envelope, dict):
        sc = scene_envelope.get("scene")
        if isinstance(sc, dict):
            inner = _clean_string(sc.get("id"))
            if inner:
                return inner
    if isinstance(session, dict):
        st = get_scene_state(session)
        return _clean_string(st.get("active_scene_id")) or _clean_string(session.get("active_scene_id"))
    return ""


def _scene_scope_validated(
    session: Dict[str, Any] | None,
    *,
    effective_scene_id: str,
) -> bool:
    if not isinstance(session, dict):
        return False
    stored = _clean_string(get_scene_state(session).get("active_scene_id"))
    eff = _clean_string(effective_scene_id)
    if not eff or not stored:
        return False
    return eff == stored


def _resolve_continuity_anchor(
    session: Dict[str, Any],
    *,
    scene_envelope: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Tuple[str, str]:
    """Return (anchored_interlocutor_id, source_of_anchor)."""
    ctx = inspect(session)
    raw_target = _clean_string(ctx.get("active_interaction_target_id"))
    st = get_scene_state(session)
    raw_interloc = _clean_string(st.get("current_interlocutor"))

    if raw_target and assert_valid_speaker(
        raw_target, session, scene_envelope=scene_envelope, world=world
    ):
        return raw_target, "active_interaction_target_id"

    if raw_interloc and assert_valid_speaker(
        raw_interloc, session, scene_envelope=scene_envelope, world=world
    ):
        return raw_interloc, "current_interlocutor"

    return "", "none"


def _continuity_strength_for(
    *,
    interaction_mode: str,
    anchored_id: str,
    rtc_dialogue: bool,
) -> str:
    if interaction_mode == "social" and bool(anchored_id):
        return "strong"
    if rtc_dialogue and not anchored_id:
        return "soft"
    return "none"


def _append_reason(out: List[str], label: str) -> None:
    if label and label not in out:
        out.append(label)


def _continuity_reason_list(
    *,
    interaction_mode: str,
    anchor_source: str,
    anchored_id: str,
    rtc_dialogue: bool,
    strength: str,
    stale_anchor_attempt: bool,
) -> List[str]:
    reasons: List[str] = []
    if interaction_mode == "social":
        _append_reason(reasons, "social_mode_active")
    if anchor_source == "active_interaction_target_id" and anchored_id:
        _append_reason(reasons, "anchored_to_active_target")
    elif anchor_source == "current_interlocutor" and anchored_id:
        _append_reason(reasons, "anchored_to_scene_interlocutor")
    if strength == "soft" and rtc_dialogue:
        _append_reason(reasons, "dialogue_response_type_without_hard_anchor")
    if stale_anchor_attempt:
        _append_reason(reasons, "no_valid_continuity_anchor")
    return reasons


def build_interaction_continuity_contract(
    session: Dict[str, Any] | None,
    *,
    scene_id: str | None = None,
    scene_envelope: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    response_type_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic, machine-readable continuity snapshot for prompts and downstream gates."""
    rtc = _normalize_response_type_contract(
        response_type_contract if isinstance(response_type_contract, dict) else None
    )
    rtc_dialogue = bool(rtc and rtc.get("required_response_type") == "dialogue")
    response_type_required = str((rtc or {}).get("required_response_type") or "")

    if not isinstance(session, dict):
        return {
            "enabled": False,
            "continuity_strength": "none",
            "preserve_conversational_thread": False,
            "preserve_context_continuity": False,
            "drop_interlocutor_requires_explicit_break": False,
            "speaker_switch_requires_explicit_cue": False,
            "allow_narrator_bridge": True,
            "interaction_mode": "none",
            "interaction_kind": "",
            "active_interaction_target_id": "",
            "current_interlocutor": "",
            "anchored_interlocutor_id": "",
            "conversation_privacy": "",
            "engagement_level": "",
            "speaker_selection_contract": None,
            "continuity_reasons": [],
            "break_signals_present": [],
            "debug": {
                "source_of_anchor": "none",
                "scene_scope_validated": False,
                "response_type_required": response_type_required,
            },
        }

    ctx = inspect(session)
    st = get_scene_state(session)
    eff_sid = _effective_scene_id(scene_id, scene_envelope, session)
    scope_ok = _scene_scope_validated(session, effective_scene_id=eff_sid)

    raw_target = _clean_string(ctx.get("active_interaction_target_id"))
    raw_interloc = _clean_string(st.get("current_interlocutor"))
    anchored_id, anchor_source = _resolve_continuity_anchor(
        session, scene_envelope=scene_envelope, world=world
    )
    stale_anchor_attempt = bool(
        (raw_target or raw_interloc) and not anchored_id
    )

    interaction_mode = _clean_string(ctx.get("interaction_mode")) or "none"
    interaction_kind = _clean_string(ctx.get("active_interaction_kind"))
    conversation_privacy = _clean_string(ctx.get("conversation_privacy"))
    engagement_level = _clean_string(ctx.get("engagement_level")) or "none"

    strength = _continuity_strength_for(
        interaction_mode=interaction_mode,
        anchored_id=anchored_id,
        rtc_dialogue=rtc_dialogue,
    )
    enabled = strength != "none"

    reasons = _continuity_reason_list(
        interaction_mode=interaction_mode,
        anchor_source=anchor_source,
        anchored_id=anchored_id,
        rtc_dialogue=rtc_dialogue,
        strength=strength,
        stale_anchor_attempt=stale_anchor_attempt,
    )

    w = world if isinstance(world, dict) else None
    speaker_selection: Dict[str, Any] | None = None
    if eff_sid:
        speaker_selection = build_speaker_selection_contract(
            session,
            w,
            eff_sid,
            scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
            resolution=None,
        )
    else:
        speaker_selection = None

    return {
        "enabled": enabled,
        "continuity_strength": strength,
        "preserve_conversational_thread": enabled,
        "preserve_context_continuity": enabled,
        "drop_interlocutor_requires_explicit_break": strength == "strong",
        "speaker_switch_requires_explicit_cue": enabled,
        "allow_narrator_bridge": True,
        "interaction_mode": interaction_mode,
        "interaction_kind": interaction_kind,
        "active_interaction_target_id": raw_target,
        "current_interlocutor": raw_interloc,
        "anchored_interlocutor_id": anchored_id,
        "conversation_privacy": conversation_privacy,
        "engagement_level": engagement_level,
        "speaker_selection_contract": speaker_selection,
        "continuity_reasons": reasons,
        "break_signals_present": [],
        "debug": {
            "source_of_anchor": anchor_source,
            "scene_scope_validated": scope_ok,
            "response_type_required": response_type_required,
        },
    }


# --- Deterministic interaction continuity validation (candidate text vs contract) ---

_QUOTE_CLASS = r'["\u201c\u201d\u2018\u2019]'
_SPEECH_TAG_RE = re.compile(
    r"\b(?:says|replies|asks|mutters|whispers|calls\s+out|shouts|adds|snaps|answers|responds)\b",
    re.IGNORECASE,
)
_EXPLICIT_CUE_RES: List[Tuple[str, re.Pattern[str]]] = [
    ("before_speaker_can_answer", re.compile(r"\bbefore\s+\w+\s+can\s+(?:answer|speak|reply)\b", re.I)),
    ("voice_from_crowd", re.compile(r"\b(?:a\s+)?voice\s+from\s+the\s+crowd\b", re.I)),
    ("someone_behind_you", re.compile(r"\bsomeone\s+behind\s+you\b", re.I)),
    ("another_voice", re.compile(r"\banother\s+voice\b", re.I)),
    ("another_speaker", re.compile(r"\banother\s+speaker\b", re.I)),
    ("a_bystander", re.compile(r"\ba\s+bystander\b", re.I)),
    ("guard_nearby", re.compile(r"\ba\s+guard\s+nearby\b", re.I)),
    ("cuts_in", re.compile(r"\bcuts\s+in\b", re.I)),
    ("interrupts", re.compile(r"\binterrupts\b", re.I)),
    ("pipes_up", re.compile(r"\bpipes\s+up\b", re.I)),
    ("glances_aside_then", re.compile(r"\bglances\s+aside\b", re.I)),
    ("then_another_speaker", re.compile(r"\bthen\s+another\s+speaker\b", re.I)),
    ("scene_transition_interruption", re.compile(r"\bthe\s+guard\s+glances\s+aside\b", re.I)),
]
_CROWD_OR_UNCUE_SECOND_VOICE_RE = re.compile(
    r"\b(?:someone|another\s+voice|from\s+the\s+crowd|a\s+bystander|a\s+guard\s+nearby|"
    r"cuts\s+in|interrupts|calls\s+out|shouts|pipes\s+up)\b",
    re.IGNORECASE,
)
_NARRATOR_BRIDGE_RES: List[Tuple[str, re.Pattern[str]]] = [
    ("nearby_beat", re.compile(r"\bnearby\b", re.I)),
    ("around_you", re.compile(r"\baround\s+you\b", re.I)),
    ("for_a_moment", re.compile(r"\bfor\s+a\s+(?:moment|breath)\b", re.I)),
    ("the_crowd", re.compile(r"\bthe\s+crowd\b", re.I)),
    ("before_beat", re.compile(r"\bbefore\s+\w+", re.I)),
]
_SPEAKER_LABEL_LINE_RE = re.compile(
    r"(?m)^\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*:\s*",
)
_SPEAKER_LABEL_AFTER_CLOSE_QUOTE_RE = re.compile(
    r'(?:["\u201d\u2019])\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*:\s*',
)
_ATTRIBUTED_NAME_RE = re.compile(
    r'(?:["\u201c])([^\n"\u201c\u201d]{1,400})(?:["\u201d])\s*,\s*([A-Z][a-z]+)\s+'
    r"(?:says|asks|replies|mutters|whispers|adds|snaps)\b"
)


def _coerce_interaction_continuity_contract(raw: Any) -> Dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    strength = str(raw.get("continuity_strength") or "").strip().lower()
    if strength not in CONTINUITY_STRENGTH_VALUES:
        return None
    if not isinstance(raw.get("enabled"), bool):
        return None
    return raw


def _ic_normalize_text(text: str | None) -> str:
    """Normalize whitespace per line; keep newlines so colon-label turns stay detectable."""
    raw = str(text or "").strip()
    if not raw:
        return ""
    return "\n".join(" ".join(part.split()) for part in raw.split("\n"))


def _has_dialogue_presence(text: str) -> bool:
    if not text.strip():
        return False
    if re.search(_QUOTE_CLASS, text):
        return True
    if _SPEECH_TAG_RE.search(text):
        return True
    if re.search(r"(?:^|[\n])\s*[\u2014—]\s*\w", text):
        return True
    return False


def _speaker_label_colon_matches(text: str) -> List[Any]:
    hits: List[Any] = []
    for m in _SPEAKER_LABEL_LINE_RE.finditer(text):
        hits.append(m)
    for m in _SPEAKER_LABEL_AFTER_CLOSE_QUOTE_RE.finditer(text):
        hits.append(m)
    hits.sort(key=lambda m: m.start())
    out: List[Any] = []
    last_start = -1
    for m in hits:
        if m.start() == last_start:
            continue
        last_start = m.start()
        out.append(m)
    return out


def _extract_simple_speaker_labels(text: str) -> List[str]:
    labels: List[str] = []
    for m in _speaker_label_colon_matches(text):
        labels.append(m.group(1).strip())
    for m in _ATTRIBUTED_NAME_RE.finditer(text):
        labels.append(m.group(2).strip())
    seen: set[str] = set()
    out: List[str] = []
    for lab in labels:
        k = lab.lower()
        if k not in seen:
            seen.add(k)
            out.append(lab)
    return out


def _has_explicit_speaker_switch_cue(text: str) -> tuple[bool, List[str]]:
    hits: List[str] = []
    for label, pat in _EXPLICIT_CUE_RES:
        if pat.search(text):
            hits.append(label)
    return (bool(hits), hits)


def _has_narrator_bridge(text: str) -> tuple[bool, List[str]]:
    hits: List[str] = []
    for label, pat in _NARRATOR_BRIDGE_RES:
        if pat.search(text):
            hits.append(label)
    return (bool(hits), hits)


_QUOTED_PAIR_RE = re.compile(
    r'(?:["\u201c\u2018])([^\n"\u201c\u201d\u2018\u2019]{2,400})(?:["\u201d\u2019])'
)
_QUOTED_ANY_RE = re.compile(
    r'(?:["\u201c\u2018])([^\n"\u201c\u201d\u2018\u2019]{1,400})(?:["\u201d\u2019])'
)

_SHORT_FIRST_LABELED_SEGMENT_CHARS = 15
_VERY_SHORT_QUOTE_INNER_CHARS = 14

BRIDGE_TEMPLATES = [
    "Before they can finish, a voice cuts in. ",
    "Before the reply comes, another voice interrupts. ",
    "Just as they speak, someone else cuts in. ",
]

_NARRATION_WRAP_ACTION_VERBS_RE = re.compile(
    r"\b(?:"
    r"walks?|walking|look(?:s|ed|ing)?|turn(?:s|ed|ing)?|steps?|stepped|reaches?|reached|"
    r"nods?|nodded|gestures?|gestured|glances?|glanced|moves?|moved|rushes?|rushed|"
    r"approaches?|approached|draws?|drew|raises?|raised"
    r")\b",
    re.IGNORECASE,
)


def _pick_bridge_template(text: str, *, variation_salt: str = "") -> str:
    salt = f"{text}\n{str(variation_salt or '').strip()}"
    h = int(hashlib.md5(salt.encode("utf-8"), usedforsecurity=False).hexdigest(), 16)
    return BRIDGE_TEMPLATES[h % len(BRIDGE_TEMPLATES)]


def _is_same_speaker_continuation(text_parts: List[str]) -> bool:
    """True when multi-part text has no uncued second-voice line and no new colon-label speaker."""
    nonempty = [p.strip() for p in text_parts if p.strip()]
    if len(nonempty) < 2:
        return False
    for s in nonempty[1:]:
        if _CROWD_OR_UNCUE_SECOND_VOICE_RE.search(s):
            return False

    def leading_label(s: str) -> str:
        m = _SPEAKER_LABEL_LINE_RE.match(s)
        return m.group(1).strip().lower() if m else ""

    labs = [leading_label(s) for s in nonempty]
    first_lab = next((L for L in labs if L), "")
    if not first_lab:
        return True
    for L in labs[1:]:
        if L and L != first_lab:
            return False
    return True


def _select_primary_dialogue_span(
    text: str,
    *,
    anchor_display_name: str,
) -> Any:
    """Pick the quote span to keep: anchor-tied when possible; upgrade very short first quotes."""
    ms = list(_QUOTED_PAIR_RE.finditer(text))
    if not ms:
        return None
    anchor = (anchor_display_name or "").strip()
    primary_idx = 0
    if anchor and anchor.lower() != "they":
        al = anchor.lower()
        for i, m in enumerate(ms):
            window = text[max(0, m.start() - 120) : m.start()].lower()
            if al in window:
                primary_idx = i
                break
    chosen = ms[primary_idx]
    inner0 = (chosen.group(1) or "").strip()
    if primary_idx + 1 < len(ms):
        inner1 = (ms[primary_idx + 1].group(1) or "").strip()
        if (
            len(inner0) <= _VERY_SHORT_QUOTE_INNER_CHARS
            and len(inner1) > len(inner0) + 8
        ):
            return ms[primary_idx + 1]
    return chosen


def _quoted_segment_count(text: str) -> int:
    return len(_QUOTED_PAIR_RE.findall(text))


def _unique_speaker_label_keys(speaker_labels: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for lab in speaker_labels:
        k = lab.strip().lower()
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _looks_like_multi_speaker_interruption(text: str, speaker_labels: List[str]) -> bool:
    """Multi-speaker pattern: require dialogue/speech signals plus a second-voice signal.

    Avoids flagging pure narration that merely mentions crowds or other actors.
    Same speaker repeating a colon-label (or two quotes under one labeled voice) is not a switch.
    """
    dialogue = _has_dialogue_presence(text)
    if not dialogue:
        return False
    distinct_labels = _unique_speaker_label_keys(speaker_labels)
    if len(distinct_labels) >= 2:
        return True
    if _quoted_segment_count(text) >= 2:
        colon_matches = _speaker_label_colon_matches(text)
        if len(colon_matches) >= 2:
            names = [m.group(1).strip().lower() for m in colon_matches]
            if len(_unique_speaker_label_keys(names)) == 1:
                return False
        return True
    if _CROWD_OR_UNCUE_SECOND_VOICE_RE.search(text):
        return True
    return False


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+", text))


def _detect_thread_drop(
    *,
    strength: str,
    dialogue_presence: bool,
    text: str,
    narrator_bridge: bool,
    explicit_cue: bool,
) -> bool:
    if dialogue_presence or narrator_bridge or explicit_cue:
        return False
    wc = _word_count(text)
    if strength == "strong":
        return wc >= 12
    if strength == "soft":
        return wc >= 18
    return False


def _rtc_requires_dialogue(response_type_contract: Dict[str, Any] | None) -> bool:
    rtc = _normalize_response_type_contract(
        response_type_contract if isinstance(response_type_contract, dict) else None
    )
    return bool(rtc and rtc.get("required_response_type") == "dialogue")


def _append_violation(out: List[str], label: str) -> None:
    if label and label not in out:
        out.append(label)


def _append_warning(out: List[str], label: str) -> None:
    if label and label not in out:
        out.append(label)


def _speaker_contract_debug_notes(
    speaker_selection_contract: Dict[str, Any] | None,
    *,
    multi_speaker_pattern_present: bool,
    explicit_switch_cue_present: bool,
    reason_path: List[str],
) -> None:
    if not isinstance(speaker_selection_contract, dict):
        return
    primary = _clean_string(speaker_selection_contract.get("primary_speaker_id"))
    if (
        primary
        and multi_speaker_pattern_present
        and not explicit_switch_cue_present
    ):
        _append_reason(reason_path, "speaker_contract_primary_id_vs_multi_speaker_pattern")


def validate_interaction_continuity(
    text: str | None,
    *,
    interaction_continuity_contract: Dict[str, Any] | None,
    speaker_selection_contract: Dict[str, Any] | None = None,
    response_type_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Pure validator: compare final candidate *text* to a resolved interaction continuity contract.

    Missing/invalid contracts are inert (``ok=True``, ``enabled=False``, no violations).
    """
    inert: Dict[str, Any] = {
        "ok": True,
        "enabled": False,
        "continuity_strength": "none",
        "violations": [],
        "warnings": [],
        "facts": {
            "anchored_interlocutor_id": "",
            "anchor_required": False,
            "speaker_switch_detected": False,
            "explicit_switch_cue_present": False,
            "thread_drop_detected": False,
            "narrator_bridge_present": False,
            "multi_speaker_pattern_present": False,
            "dialogue_presence": False,
        },
        "debug": {
            "speaker_labels_detected": [],
            "cue_labels": [],
            "reason_path": ["contract_missing_or_invalid"],
        },
    }

    contract = _coerce_interaction_continuity_contract(interaction_continuity_contract)
    if contract is None:
        return inert

    strength = str(contract.get("continuity_strength") or "none").strip().lower()
    enabled = bool(contract.get("enabled"))
    if not enabled or strength == "none":
        out_inert = dict(inert)
        out_inert["debug"] = {
            "speaker_labels_detected": [],
            "cue_labels": [],
            "reason_path": ["contract_disabled_or_strength_none"],
        }
        return out_inert

    norm = _ic_normalize_text(text)
    anchored_id = _clean_string(contract.get("anchored_interlocutor_id"))
    anchor_required = strength == "strong" and bool(anchored_id)

    dialogue_presence = _has_dialogue_presence(norm)
    speaker_labels = _extract_simple_speaker_labels(norm)
    explicit_cue, cue_labels = _has_explicit_speaker_switch_cue(norm)
    bridge_present, _bridge_hits = _has_narrator_bridge(norm)
    multi_speaker = _looks_like_multi_speaker_interruption(norm, speaker_labels)
    speaker_switch_detected = bool(
        multi_speaker or len(_unique_speaker_label_keys(speaker_labels)) >= 2
    )

    rtc_dialogue = _rtc_requires_dialogue(response_type_contract)
    require_dialogue_shape = rtc_dialogue or strength in {"soft", "strong"}

    reason_path: List[str] = ["contract_active"]
    if require_dialogue_shape:
        _append_reason(reason_path, "dialogue_shape_expected")

    thread_drop = _detect_thread_drop(
        strength=strength,
        dialogue_presence=dialogue_presence,
        text=norm,
        narrator_bridge=bridge_present,
        explicit_cue=explicit_cue,
    )

    violations: List[str] = []
    warnings: List[str] = []

    nested_ssc = contract.get("speaker_selection_contract")
    ssc: Dict[str, Any] | None = None
    if isinstance(speaker_selection_contract, dict):
        ssc = speaker_selection_contract
    elif isinstance(nested_ssc, dict):
        ssc = nested_ssc

    _speaker_contract_debug_notes(
        ssc,
        multi_speaker_pattern_present=multi_speaker,
        explicit_switch_cue_present=explicit_cue,
        reason_path=reason_path,
    )

    if require_dialogue_shape and not dialogue_presence:
        _append_violation(violations, "dialogue_absent_under_continuity")

    if strength == "strong":
        if anchor_required and not dialogue_presence and _word_count(norm) >= 8:
            _append_violation(violations, "anchored_interlocutor_dropped")
        if thread_drop:
            _append_violation(violations, "conversational_thread_dropped")
        if multi_speaker and not explicit_cue:
            _append_violation(violations, "multi_speaker_interruption_under_continuity")
            _append_violation(violations, "speaker_switch_without_explicit_cue")

    elif strength == "soft":
        if require_dialogue_shape and not dialogue_presence and _word_count(norm) >= 12:
            _append_violation(violations, "context_continuity_missing")
        if thread_drop:
            _append_violation(violations, "conversational_thread_dropped")
        if bridge_present and dialogue_presence:
            _append_warning(warnings, "narrator_bridge_used")
        short_quote = False
        for m in _QUOTED_ANY_RE.finditer(norm):
            inner = (m.group(1) or "").strip()
            if inner and len(inner.split()) < 3:
                short_quote = True
                break
        if dialogue_presence and short_quote and _word_count(norm) > 25:
            _append_warning(warnings, "soft_continuity_weak_dialogue_shape")

    ok = len(violations) == 0

    return {
        "ok": ok,
        "enabled": True,
        "continuity_strength": strength,
        "violations": violations,
        "warnings": warnings,
        "facts": {
            "anchored_interlocutor_id": anchored_id,
            "anchor_required": anchor_required,
            "speaker_switch_detected": speaker_switch_detected,
            "explicit_switch_cue_present": explicit_cue,
            "thread_drop_detected": thread_drop,
            "narrator_bridge_present": bridge_present,
            "multi_speaker_pattern_present": multi_speaker,
            "dialogue_presence": dialogue_presence,
        },
        "debug": {
            "speaker_labels_detected": list(speaker_labels),
            "cue_labels": list(cue_labels),
            "reason_path": reason_path,
        },
    }


# --- Minimal deterministic repair (consumes Block #2 validator output only) ---

_NARRATION_WRAP_DISALLOW = re.compile(
    r"\b(while|although|though|because|which\s+\w+|gathered|shifted|marked|recorded|"
    r"indifferent|depends|economy|ledgers)\b",
    re.I,
)
_ATTR_TAIL_AFTER_QUOTE_RE = re.compile(
    r"\s*,\s*[A-Z][a-zA-Z]+\s+(?:says|asks|replies|mutters|whispers|adds|snaps)\b[^.\n]*\.?",
)


def _dialogue_attribution_label(interaction_continuity_contract: Dict[str, Any] | None) -> str:
    if not isinstance(interaction_continuity_contract, dict):
        return "They"
    ssc = interaction_continuity_contract.get("speaker_selection_contract")
    if isinstance(ssc, dict):
        name = _clean_string(ssc.get("primary_speaker_name"))
        if name:
            return name
    return "They"


def _try_strip_uncued_interruption(
    text: str,
    *,
    interaction_continuity_contract: Dict[str, Any] | None = None,
) -> tuple[str, bool, List[str]]:
    """Remove secondary-voice material; keep first labeled block, first paragraph, or chosen quote."""
    notes: List[str] = []
    if not (text and text.strip()):
        return text, False, notes

    matches = _speaker_label_colon_matches(text)
    if len(matches) >= 2:
        sp1 = matches[0].group(1).strip().lower()
        sp2 = matches[1].group(1).strip().lower()
        if sp1 == sp2:
            notes.append("skipped_strip_same_speaker_label_continuation")
            return text, False, notes
        seg_before = text[: matches[1].start()].rstrip()
        seg_from_second = text[matches[1].start() :].strip()
        if (
            len(seg_before) < _SHORT_FIRST_LABELED_SEGMENT_CHARS
            and _has_dialogue_presence(seg_from_second)
        ):
            notes.append("preferred_second_labeled_segment_over_very_short_first")
            return seg_from_second, True, notes
        cut = seg_before
        if cut:
            notes.append("kept_first_speaker_label_segment")
            return cut, True, notes

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if not _CROWD_OR_UNCUE_SECOND_VOICE_RE.search(line):
            continue
        if _is_same_speaker_continuation(lines[: i + 1]):
            continue
        cut = "\n".join(lines[:i]).rstrip()
        if cut:
            notes.append("dropped_lines_from_first_uncued_crowd_marker_line")
            return cut, True, notes

    qm = list(_QUOTED_PAIR_RE.finditer(text))
    if len(qm) >= 2:
        anchor_name = _dialogue_attribution_label(interaction_continuity_contract)
        primary = _select_primary_dialogue_span(text, anchor_display_name=anchor_name)
        if primary is None:
            primary = qm[0]
        end_keep = primary.end()
        cut = text[:end_keep]
        tail = text[end_keep:]
        m_attr = _ATTR_TAIL_AFTER_QUOTE_RE.match(tail)
        if m_attr:
            cut += m_attr.group(0)
        cut = cut.rstrip()
        if cut:
            notes.append("kept_primary_quoted_utterance_span")
            return cut, True, notes

    return text, False, notes


def _strip_would_destroy_meaning(original: str, stripped: str) -> bool:
    if not stripped.strip():
        return True
    if _has_dialogue_presence(stripped):
        if _word_count(stripped) < 1:
            return True
    elif _word_count(stripped) < 3:
        return True
    if _has_dialogue_presence(original) and not _has_dialogue_presence(stripped):
        return True
    if (
        not _has_dialogue_presence(stripped)
        and _word_count(original) >= 8
        and _word_count(stripped) < 5
    ):
        return True
    if (
        _has_dialogue_presence(original)
        and _has_dialogue_presence(stripped)
        and _word_count(stripped) < 2
        and _quoted_segment_count(stripped) == 0
    ):
        return True
    return False


def _is_short_answer_like_for_dialogue_wrap(text: str) -> bool:
    t = text.strip()
    if not t or "\n" in t:
        return False
    if len(t) > 120:
        return False
    if len(re.findall(r"\.(?:\s+|$)", t)) > 1:
        return False
    if _NARRATION_WRAP_ACTION_VERBS_RE.search(t):
        return False
    if _word_count(t) > 12:
        return False
    if _NARRATION_WRAP_DISALLOW.search(t):
        return False
    if _has_dialogue_presence(t):
        return False
    if not re.search(r"[.!?][\"'”’]?\s*$", t):
        return False
    return True


def _try_narration_to_dialogue(
    text: str,
    *,
    interaction_continuity_contract: Dict[str, Any] | None,
) -> tuple[str, bool, List[str]]:
    notes: List[str] = []
    if not _is_short_answer_like_for_dialogue_wrap(text):
        return text, False, notes
    inner = text.strip()
    inner_esc = inner.replace('"', "'")
    label = _dialogue_attribution_label(interaction_continuity_contract)
    repaired = f'{label} says, "{inner_esc}"'
    notes.append("wrapped_plain_line_as_attributed_dialogue")
    return repaired, True, notes


def _try_insert_explicit_bridge(
    text: str,
    *,
    interaction_continuity_contract: Dict[str, Any] | None = None,
    variation_salt: str = "",
) -> tuple[str, bool, List[str]]:
    """Explicit narrator cue (validator-visible) + primary quoted utterance."""
    notes: List[str] = []
    anchor_name = _dialogue_attribution_label(interaction_continuity_contract)
    primary = _select_primary_dialogue_span(text, anchor_display_name=anchor_name)
    if primary is None:
        primary = _QUOTED_PAIR_RE.search(text)
    if primary is None:
        return text, False, notes
    frag = (primary.group(0) or "").strip()
    if not frag:
        return text, False, notes
    cue = _pick_bridge_template(text, variation_salt=variation_salt)
    notes.append("prepended_explicit_cue_with_primary_quote")
    return cue + frag, True, notes


def _try_repair_malformed_speaker_attribution(
    text: str,
    *,
    interaction_continuity_contract: Dict[str, Any] | None,
) -> tuple[str, bool, List[str]]:
    """Reorder two dialogue fragments around an existing attribution beat (no new facts)."""
    notes: List[str] = []
    raw = str(text or "").strip()
    if not raw or raw.count('"') != 2:
        return text, False, notes

    canonical = _dialogue_attribution_label(interaction_continuity_contract)
    if not canonical or canonical.strip() == "They":
        return text, False, notes

    parts = raw.split('"')
    if len(parts) != 3:
        return text, False, notes

    frag1 = parts[0].strip()
    middle = parts[1].strip()
    frag2 = parts[2].strip()
    if not frag1 or not frag2 or not middle:
        return text, False, notes

    if canonical.lower() not in middle.lower():
        return text, False, notes

    if not _NARRATION_WRAP_ACTION_VERBS_RE.search(middle):
        return text, False, notes

    inner = f"{frag2} {frag1}".strip()
    inner = " ".join(inner.split())
    if not inner:
        return text, False, notes

    repaired = f'{middle} "{inner}"'
    notes.append("reordered_split_quote_fragments_around_existing_beat")
    return repaired, True, notes


_STRATEGY_NOTE_BY_CODE: Dict[str, str] = {
    "reordered_split_quote_fragments_around_existing_beat": (
        "malformed explicit attribution salvaged into canonical single-speaker dialogue"
    ),
    "skipped_strip_same_speaker_label_continuation": (
        "second segment identified as same-speaker continuation; strip skipped"
    ),
    "preferred_second_labeled_segment_over_very_short_first": (
        "very short first labeled segment skipped; retained substantive following dialogue"
    ),
    "kept_first_speaker_label_segment": (
        "second segment identified as uncued interruption; retained first labeled speaker"
    ),
    "dropped_lines_from_first_uncued_crowd_marker_line": (
        "second segment identified as uncued interruption; dropped interrupt tail from line break"
    ),
    "kept_primary_quoted_utterance_span": (
        "primary quoted span retained (anchor-tied or upgraded from very short lead quote)"
    ),
    "prepended_explicit_cue_with_primary_quote": (
        "bridge inserted to preserve multi-speaker meaning"
    ),
    "wrapped_plain_line_as_attributed_dialogue": (
        "short narration upgraded to anchored speaker dialogue"
    ),
}


def _strategy_notes_for_repair(raw_notes: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    mapped: set[str] = set()
    for n in raw_notes:
        h = _STRATEGY_NOTE_BY_CODE.get(n)
        if h:
            mapped.add(n)
            if h not in seen:
                seen.add(h)
                out.append(h)
    for n in raw_notes:
        if n in mapped:
            continue
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def repair_interaction_continuity(
    text: str,
    *,
    validation: Dict[str, Any],
    interaction_continuity_contract: Dict[str, Any] | None,
    variation_salt: str = "",
) -> Dict[str, Any]:
    """Deterministic, minimal repair using only ``validation`` (+ optional contract for labels).

    Does not invent speakers, events, or facts beyond trivial framing allowed below.
    """
    notes: List[str] = []
    if not isinstance(validation, dict) or not validation.get("enabled"):
        return {
            "repaired_text": text,
            "applied": False,
            "repair_type": None,
            "notes": [],
            "strategy_notes": [],
        }
    if validation.get("ok") is True:
        return {
            "repaired_text": text,
            "applied": False,
            "repair_type": None,
            "notes": [],
            "strategy_notes": [],
        }

    violations = set(str(v) for v in (validation.get("violations") or []) if isinstance(v, str))
    strength = str(validation.get("continuity_strength") or "none").strip().lower()

    v_malformed_attr = "malformed_speaker_attribution_under_continuity" in violations
    v_multi = "multi_speaker_interruption_under_continuity" in violations
    v_switch = "speaker_switch_without_explicit_cue" in violations
    v_dialogue_absent = "dialogue_absent_under_continuity" in violations

    if v_malformed_attr:
        fixed, did_mal, mn = _try_repair_malformed_speaker_attribution(
            text, interaction_continuity_contract=interaction_continuity_contract
        )
        notes.extend(mn)
        destroy_m = _strip_would_destroy_meaning(text, fixed) if did_mal else True
        if did_mal and not destroy_m:
            sn = _strategy_notes_for_repair(notes)
            if (validation.get("debug") or {}).get("speaker_binding_reason_code"):
                bn = "speaker binding mismatch converted into continuity failure"
                if bn not in sn:
                    sn = [bn] + sn
            return {
                "repaired_text": fixed,
                "applied": True,
                "repair_type": "repair_malformed_speaker_attribution",
                "notes": notes,
                "strategy_notes": sn,
            }

    # 1) Strip uncued interruption (primary)
    if v_multi or v_switch:
        stripped, did_strip, sn = _try_strip_uncued_interruption(
            text, interaction_continuity_contract=interaction_continuity_contract
        )
        notes.extend(sn)
        destroy = _strip_would_destroy_meaning(text, stripped) if did_strip else True
        if did_strip and not destroy:
            return {
                "repaired_text": stripped,
                "applied": True,
                "repair_type": "strip_uncued_interruption",
                "notes": notes,
                "strategy_notes": _strategy_notes_for_repair(notes),
            }
        if (v_multi or v_switch) and destroy:
            bridged, did_bridge, bn = _try_insert_explicit_bridge(
                text,
                interaction_continuity_contract=interaction_continuity_contract,
                variation_salt=variation_salt,
            )
            notes.extend(bn)
            if did_bridge:
                return {
                    "repaired_text": bridged,
                    "applied": True,
                    "repair_type": "insert_explicit_bridge",
                    "notes": notes,
                    "strategy_notes": _strategy_notes_for_repair(notes),
                }

    # 2) Narration → dialogue (strong only, trivial lines)
    if v_dialogue_absent and strength == "strong":
        wrapped, did_wrap, wn = _try_narration_to_dialogue(
            text, interaction_continuity_contract=interaction_continuity_contract
        )
        notes.extend(wn)
        if did_wrap:
            return {
                "repaired_text": wrapped,
                "applied": True,
                "repair_type": "narration_to_dialogue",
                "notes": notes,
                "strategy_notes": _strategy_notes_for_repair(notes),
            }

    return {
        "repaired_text": text,
        "applied": False,
        "repair_type": None,
        "notes": notes,
        "strategy_notes": _strategy_notes_for_repair(notes) if notes else [],
    }
