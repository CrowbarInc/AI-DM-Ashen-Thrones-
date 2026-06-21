"""Route-isolated downstream emission helpers for active social_exchange turns.

Ensures player-facing text is speaker-owned, single-form, and never pulled from
scene/ambient uncertainty pools except as an explicit interruption breakoff.

BV14A: compatibility barrel for strict-social composition authority. Fallback, policy,
validation, and projection symbols are re-exported from canonical domain modules.

BV14C: import guard + FI cap (≤12) lock regrowth; fallback/policy/validation/projection
consumers route to ``social_exchange_fallback_catalog``, ``social_exchange_policy``,
``social_exchange_validation``, and ``social_exchange_projection``.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Literal, MutableMapping, Optional, Tuple

from game.dialogue_targeting import (
    line_opens_with_comma_vocative,
    npc_id_from_vocative_line,
)
from game.exploration import EXPLORATION_KINDS
from game.interaction_context import (
    assert_valid_speaker,
    canonical_scene_addressable_roster,
    clear_social_exchange_interruption_tracker,
    get_social_exchange_interruption_tracker,
    inspect as inspect_interaction_context,
    npc_id_from_explicit_generic_role_address,
    resolve_authoritative_social_target,
    scene_addressable_actor_ids,
    session_allows_implicit_social_reply_authority,
    set_social_exchange_interruption_tracker,
)
from game.response_policy_contracts import response_type_contract_requires_dialogue
from game.social import (
    apply_social_reply_speaker_grounding,
    classify_social_question_dimension,
    format_structured_fact_social_line,
    neutral_reply_speaker_grounding_bridge_line,
    resolve_grounded_social_speaker,
    select_best_social_answer_candidate,
    topic_pressure_speaker_id_for_social_exchange,
)
from game.social import SOCIAL_KINDS
from game.storage import get_scene_runtime
from game.utils import slugify
from game.realization_provenance import (
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    attach_realization_fallback_family,
    normalize_realization_fallback_family,
)

from game.social_exchange_fallback_catalog import (
    StrictSocialEmergencyFallbackSurface,
    _integrity_topic_hook,
    active_interlocutor_matches_resolution_social_npc,
    apply_social_exchange_retry_fallback_gm,
    apply_strict_social_terminal_dialogue_fallback_if_needed,
    build_open_social_solicitation_recovery,
    deterministic_social_fallback_line,
    lawful_strict_social_dialogue_emergency_fallback_line,
    merge_open_social_recovery_emission_debug,
    minimal_social_emergency_fallback_line,
    open_social_recovery_passes_anti_stall,
    repair_strict_social_terminal_dialogue_fallback_if_needed,
    select_strict_social_emergency_fallback_line,
    social_fallback_line_for_sanitizer,
    social_integrity_fallback_line_candidates,
    strict_social_ownership_terminal_fallback,
    strict_social_terminal_dialogue_fallback_valid,
    text_is_strict_social_minimal_emergency_fallback,
)
from game.social_exchange_policy import (
    _auth_after_social_promotion_binding,
    _legacy_strict_basis_from_authoritative,
    _merged_prompt_opens_reflective_or_world_action_beat,
    _normalized_action_from_resolution,
    _question_prompt_for_resolution_early,
    _scene_envelope_for_strict_social,
    _session_turn_counter,
    _speaker_label_for_emission_seed,
    coerce_resolution_for_strict_social_emission,
    coerced_strict_social_allowed_by_merged_prompt,
    effective_scene_npc_roster,
    effective_strict_social_resolution_for_emission,
    is_conversational_npc_dialogue_line,
    is_scene_directed_watch_question,
    is_social_exchange_resolution,
    looks_like_npc_directed_question,
    merged_player_prompt_for_gate,
    minimal_social_resolution_for_directed_question_guard,
    npc_display_name_for_emission,
    player_line_triggers_strict_social_emission,
    reconcile_strict_social_resolution_speaker,
    resolve_strict_social_npc_target_id,
    should_apply_strict_social_exchange_emission,
    speaker_label,
    strict_social_emission_will_apply,
    strict_social_suppress_non_native_coercion_for_narration_beat,
    synthetic_social_exchange_resolution_for_emission,
)
from game.social_exchange_projection import (
    _is_pressure_active,
    emission_gate_interruption_active,
    emission_gate_pressure_active,
    emission_gate_uncertainty_source,
    interruption_cue_present_in_text,
    log_final_emission_decision,
    log_final_emission_trace,
    project_strict_social_replace_realization_family,
    stamp_strict_social_deterministic_fallback_family,
    strict_social_deterministic_fallback_family_token,
)
from game.social_exchange_validation import (
    _collapse_ws,
    _final_paragraph_ends_with_question,
    has_explicit_interruption_shape,
    _INTERRUPTION_PATTERNS,
    _interruption_sentence_index,
    _looks_like_interruption_breakoff_text,
    _normalize_gate_text,
    _PRESSURE_SIGNAL_PATTERNS,
    _REFUSAL_SIGNAL_PATTERNS,
    _IGNORANCE_SIGNAL_PATTERNS,
    _SCENE_CONTAMINATION_PATTERNS,
    _social_line_has_playable_npc_substance,
    _sentence_is_bounded_social_signal,
    _sentence_is_clue_or_analytical_substitute,
    _sentence_is_detached_omniscient_analysis,
    _sentence_is_npc_setup,
    _sentence_is_scene_contaminated,
    _sentence_is_speaker_owned_social,
    _sentence_opens_with_resolved_npc_beat,
    _split_sentences,
    is_route_illegal_global_or_sanitizer_fallback_text,
    replacement_is_route_legal_social,
    social_final_emission_malformed_player_echo,
)

_log = logging.getLogger(__name__)

_EXPLORATION_RESOLUTION_KINDS = frozenset(str(k).strip().lower() for k in EXPLORATION_KINDS)

_log = logging.getLogger(__name__)

def _sentence_form_label(sentence: str) -> str:
    """Single-form label for one sentence (after scene/clue drops)."""
    s = (sentence or "").strip()
    low = s.lower()
    if _looks_like_interruption_breakoff_text(s):
        return "interruption_breakoff"
    if any(p.search(s) for p in _PRESSURE_SIGNAL_PATTERNS):
        return "pressure_escalation"
    if any(p.search(s) for p in _REFUSAL_SIGNAL_PATTERNS):
        return "refusal_evasion"
    if any(p.search(s) for p in _IGNORANCE_SIGNAL_PATTERNS):
        return "bounded_ignorance"
    if '"' in s or re.search(r"\b(?:says|replies|asks|answers|mutters|whispers)\b", low):
        return "direct_answer"
    return "direct_answer"

def _is_flat_idk_without_qualifier(sentence: str) -> bool:
    """Flat 'I don't know' / 'no idea' with no in-sentence who/what/which follow-up."""
    low = str(sentence or "").lower()
    m = re.search(r"\b(?:i\s+don'?t\s+know|i\s+do\s+not\s+know|no\s+idea)\b", low)
    if not m:
        return False
    tail = low[m.end() : m.end() + 100]
    if re.search(r"\b(?:who|what|which|whether)\b", tail):
        return False
    return True

def _contradictory_flat_ignorance_and_concrete_lead(sentences: List[str], labels: List[str]) -> bool:
    """True when one line gives a concrete lead and another is flat ignorance (terminal-fallback case)."""
    if len(sentences) != len(labels) or len(sentences) < 2:
        return False
    concrete_pat = re.compile(
        r'(?:\b(?:east|west|north|south)(?:\s+road|\s+lane)?\b|"[^"]{0,120}(?:east|west|road|lane|mill|gate))',
        re.IGNORECASE,
    )
    has_concrete = any(
        lb == "direct_answer" and concrete_pat.search(sentences[i] or "")
        for i, lb in enumerate(labels)
    )
    has_flat = any(
        lb == "bounded_ignorance" and _is_flat_idk_without_qualifier(sentences[i] or "")
        for i, lb in enumerate(labels)
    )
    return bool(has_concrete and has_flat)

def _dominant_form_from_labels(labels: List[str], *, pressure_tag: bool) -> str | None:
    uniq = {lb for lb in labels if lb}
    if not uniq:
        return None
    if len(uniq) == 1:
        return next(iter(uniq))
    if "interruption_breakoff" in uniq:
        return "interruption_breakoff"
    if pressure_tag and ("pressure_escalation" in uniq or "refusal_evasion" in uniq):
        return "pressure_escalation" if "pressure_escalation" in uniq else "refusal_evasion"
    # Conflicting substantive social claims: refuse to synthesize.
    if "bounded_ignorance" in uniq and "direct_answer" in uniq:
        return "mixed_ignorance_and_direct"
    if "refusal_evasion" in uniq and "direct_answer" in uniq:
        return "refusal_evasion"
    if "pressure_escalation" in uniq and "direct_answer" in uniq:
        return "pressure_escalation"
    if "bounded_ignorance" in uniq and "refusal_evasion" in uniq:
        return "refusal_evasion"
    # Pick highest-priority remaining form.
    best = None
    best_rank = -1
    for lb in uniq:
        try:
            r = _FORM_ORDER.index(lb)
        except ValueError:
            r = 0
        if r >= best_rank:
            best_rank = r
            best = lb
    return best

def _strip_ascii_double_quotes_for_scan(sentence: str) -> str:
    """Replace double-quoted spans so advisory heuristics do not match NPC dialogue."""
    return re.sub(r'"[^"]*"', " ", str(sentence or ""))

def _strict_social_advisory_outside_quotes(sentence: str) -> bool:
    """Advisory / player-directive phrasing outside quoted speech — invalid in strict social."""
    outside = _strip_ascii_double_quotes_for_scan(sentence)
    low = outside.lower()
    patterns = (
        r"\byou\s+should\b",
        r"\byou\s+might\s+want\s+to\b",
        r"\bit\s+might\s+be\s+worth\b",
        r"\bit\s+would\s+be\s+wise\b",
        r"\bconsider\s+(?:asking|looking|investigating)\b",
        r"\bi['']d\s+suggest\b",
        r"\bperhaps\s+you\s+should\b",
        r"\bit\s+might\s+help\s+to\b",
    )
    return any(re.search(p, low) for p in patterns)

def _strict_social_sentence_is_invalid(sentence: str, resolution: Dict[str, Any] | None) -> bool:
    """INVALID: narrator uncertainty, scene placeholders, analysis, clue narration, advisory."""
    s = (sentence or "").strip()
    if not s:
        return True
    if _sentence_is_scene_contaminated(s):
        return True
    if _sentence_is_clue_or_analytical_substitute(s):
        return True
    if _sentence_is_detached_omniscient_analysis(s):
        return True
    if _strict_social_advisory_outside_quotes(s):
        return True
    return False

def _classify_strict_social_ownership_sentence(
    sentence: str,
    resolution: Dict[str, Any] | None,
) -> str:
    """Return 'interruption', 'social', or 'invalid' for strict-social final emission."""
    s = (sentence or "").strip()
    if not s:
        return "invalid"
    if _looks_like_interruption_breakoff_text(s):
        return "interruption"
    if _strict_social_sentence_is_invalid(s, resolution):
        return "invalid"
    if _sentence_is_speaker_owned_social(s, resolution):
        return "social"
    return "invalid"

def _merge_interruption_chunk(sentences: List[str]) -> str | None:
    intr_idx = _interruption_sentence_index(sentences)
    if intr_idx is None:
        return None
    start = intr_idx
    cur = sentences[intr_idx]
    if intr_idx > 0 and _looks_like_interruption_breakoff_text(cur) and not has_explicit_interruption_shape(cur):
        if _sentence_is_npc_setup(sentences[intr_idx - 1]):
            start = intr_idx - 1
    chunk = sentences[start : intr_idx + 1]
    merged = _collapse_ws(" ".join(chunk))
    if _sentence_is_scene_contaminated(merged) or _sentence_is_clue_or_analytical_substitute(merged):
        solo = sentences[intr_idx].strip()
        if solo and not _sentence_is_scene_contaminated(solo):
            return _collapse_ws(solo)
        return None
    return merged

def apply_strict_social_sentence_ownership_filter(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
) -> str:
    """Final strict-social emission: only NPC-owned (SOCIAL) sentences or one INTERRUPTION breakoff.

    Classifies each sentence as SOCIAL | INTERRUPTION | INVALID; drops INVALID; resolves
    conflicts; otherwise returns :func:`strict_social_ownership_terminal_fallback`.
    """
    res = resolution if isinstance(resolution, dict) else None
    raw = _collapse_ws(text)
    if not raw:
        return strict_social_ownership_terminal_fallback(res)
    sentences = _split_sentences(raw)
    if not sentences:
        return strict_social_ownership_terminal_fallback(res)

    tag_list = [str(t) for t in tags if isinstance(t, str)] if isinstance(tags, list) else []
    low_tags = {t.strip().lower() for t in tag_list}
    pressure_tag = "topic_pressure_escalation" in low_tags or _is_pressure_active(
        tag_list, session if isinstance(session, dict) else None, str(scene_id or "").strip()
    )

    # 1) Interruption dominates: one coherent breakoff only (trailing sentences ignored).
    intr_merged = _merge_interruption_chunk(sentences)
    if intr_merged:
        return intr_merged.strip()

    # 2) Drop INVALID everywhere; keep only SOCIAL sentences (prefix contamination removed).
    social_sentences: List[str] = []
    labels: List[str] = []
    for s in sentences:
        cat = _classify_strict_social_ownership_sentence(s, res)
        if cat != "social":
            continue
        social_sentences.append(s)
        labels.append(_sentence_form_label(s))

    if not social_sentences:
        return strict_social_ownership_terminal_fallback(res)

    dominant = _dominant_form_from_labels(labels, pressure_tag=pressure_tag)
    if dominant is None:
        return strict_social_ownership_terminal_fallback(res)

    if dominant == "mixed_ignorance_and_direct":
        if _contradictory_flat_ignorance_and_concrete_lead(social_sentences, labels):
            return strict_social_ownership_terminal_fallback(res)
        selected = list(social_sentences)
    else:
        selected = [s for s, lb in zip(social_sentences, labels) if lb == dominant]
    if not selected:
        return strict_social_ownership_terminal_fallback(res)

    out = _collapse_ws(" ".join(selected))
    if _sentence_is_scene_contaminated(out) or _sentence_is_clue_or_analytical_substitute(out):
        return strict_social_ownership_terminal_fallback(res)

    return out

def apply_strict_social_ownership_enforcement(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
) -> str:
    """Alias for :func:`apply_strict_social_sentence_ownership_filter` (final ownership pass)."""
    return apply_strict_social_sentence_ownership_filter(
        text,
        resolution=resolution,
        tags=tags,
        session=session,
        scene_id=scene_id,
    )

def normalize_social_exchange_candidate(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
) -> str:
    """Backward-compatible alias for :func:`apply_strict_social_sentence_ownership_filter`."""
    return apply_strict_social_sentence_ownership_filter(
        text,
        resolution=resolution,
        tags=tags,
        session=session,
        scene_id=scene_id,
    )

_INTERRUPTION_REPEAT_FORCE_THRESHOLD = 2

_INTERRUPTION_SIGNATURE_STOPWORDS = frozenset(
    {
        "then",
        "past",
        "into",
        "from",
        "with",
        "their",
        "there",
        "your",
        "about",
        "mouth",
        "answer",
        "starts",
        "start",
        "opens",
        "open",
        "glances",
        "glance",
        "flicks",
        "flick",
        "looks",
        "look",
        "breaks",
        "break",
        "breaksout",
        "cuts",
        "across",
        "shout",
        "shouting",
        "commotion",
        "crowd",
        "square",
        "room",
        "tables",
    }
)

def _social_exchange_interruption_exchange_key(
    resolution: Dict[str, Any] | None,
    scene_id: str,
) -> str:
    if not isinstance(resolution, dict):
        return str(scene_id or "").strip()
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    return f"{str(scene_id or '').strip()}|{npc_id}"

def _interrupt_signature_actor_anchor(text: str) -> str:
    low = str(text or "").lower()
    actor_map = (
        (r"\bdrunk(?:ard)?\b", "drunk"),
        (r"\b(?:watchman|watchmen|watch)\b", "watch"),
        (r"\bguard(?:s)?\b", "guard"),
        (r"\bclerk\b", "clerk"),
        (r"\bmerchant(?:s)?\b", "merchant"),
    )
    for pattern, label in actor_map:
        if re.search(pattern, low):
            return label
    return "none"

def _interrupt_signature_place_anchor(text: str) -> str:
    low = str(text or "").lower()
    place_map = (
        (r"\bmain gate\b", "main_gate"),
        (r"\bsouth gate\b", "south_gate"),
        (r"\beast gate\b", "east_gate"),
        (r"\bgate\b", "gate"),
        (r"\bsquare\b", "public_space"),
        (r"\balley\b", "alley"),
        (r"\blane\b", "lane"),
        (r"\bpier\b", "pier"),
        (r"\bwell\b", "well"),
        (r"\broom\b|\btables?\b|\btavern\b|\bcrowd\b|\bmarket\b", "public_space"),
    )
    for pattern, label in place_map:
        if re.search(pattern, low):
            return label
    return "none"

def _interruption_signature_for_text(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
) -> str | None:
    merged = _merge_interruption_chunk(_split_sentences(_collapse_ws(text)))
    if not merged:
        return None
    low = merged.lower()
    tokens: set[str] = set()

    if re.search(
        r"\b(?:starts?\s+to\s+answer|opens?\s+(?:their|his|her)\s+mouth|starts?\s+to\s+speak|begins?\s+to\s+(?:answer|respond))\b",
        low,
    ):
        tokens.add("answer_cutoff")
    if re.search(r"\b(?:shout(?:ing)?|commotion|uproar|alarm|cry(?:ing|ies)?|yell(?:ing)?|noise)\b", low):
        tokens.add("disturbance_noise")
    if re.search(r"\b(?:breaks?\s+off|cuts?\s+across|cut\s+off)\b", low):
        tokens.add("interruption_motion")
    if re.search(
        r"\b(?:glances?|looks?|flicks?)\s+(?:past|toward|to)\b|\bpulls?\s+(?:their|his|her)\s+attention\s+away\b",
        low,
    ):
        tokens.add("interruption_motion")
    if re.search(r"\bback\s+to\s+you\b|\battention\s+returning\b", low):
        tokens.add("interruption_motion")

    actor_anchor = _interrupt_signature_actor_anchor(merged)
    place_anchor = _interrupt_signature_place_anchor(merged)
    if actor_anchor != "none":
        tokens.add(f"actor:{actor_anchor}")
    if place_anchor != "none":
        if place_anchor == "public_space":
            tokens.add("public_space")
        else:
            tokens.add(f"place:{place_anchor}")

    if not tokens:
        return None
    return "|".join(sorted(tokens))

def _forced_interruption_progression_line(
    *,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    tag_list: List[str],
    signature: str,
    repeat_count: int = 0,
) -> tuple[str | None, str | None]:
    sid = str(scene_id or "").strip()
    structured = _try_emit_structured_fact_strict_line(
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
        tag_list=tag_list,
    )
    if structured:
        return structured, "forced_progression_structured_fact"

    merged_pt = merged_player_prompt_for_gate(resolution, session, sid)
    seed = f"{sid}|interrupt_progression|{signature}|{merged_pt}|rc={int(repeat_count)}"
    topic = _integrity_topic_hook(merged_pt) or "that"
    speaker = speaker_label(resolution)
    direct_hint, direct_kind = deterministic_social_fallback_line(
        resolution=resolution,
        uncertainty_source="scene_ambiguity",
        pressure_active=False,
        interruption_active=False,
        seed=seed + "|direct_hint",
    )
    # Prefer scene-grounded progression lines before generic integrity/deterministic uncertainty pools.
    progression_first: List[tuple[str, str]] = [
        (
            f'{speaker} lowers their voice. "That shouting is coming from the main gate. If {topic} still matters, catch the ward clerk before the square locks down."',
            "forced_progression_gate_redirect",
        ),
        (
            f'{speaker} jerks their chin toward the square. "Two watchmen are hauling someone out by the main gate. Stay with me and I will give you the short version on {topic} once they pass."',
            "forced_progression_watch_pressure",
        ),
        (direct_hint, f"forced_progression_{direct_kind}"),
    ]
    integrity_candidates = social_integrity_fallback_line_candidates(
        resolution=resolution,
        player_text=merged_pt,
        session=session,
        scene_id=sid,
        tag_list=tag_list,
        seed=seed,
    )
    candidates = progression_first + list(integrity_candidates)

    for raw_line, kind in candidates:
        filtered = apply_strict_social_sentence_ownership_filter(
            raw_line,
            resolution=resolution,
            tags=tag_list or None,
            session=session,
            scene_id=sid,
        )
        norm = _normalize_gate_text(filtered)
        if not norm:
            continue
        sig_hit = _interruption_signature_for_text(norm, resolution=resolution)
        if sig_hit and int(repeat_count) < 2:
            continue
        if not _social_line_has_playable_npc_substance(norm):
            continue
        if not _strict_social_resolved_line_passes_legality(
            norm,
            resolution=resolution,
            session=session,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
        ):
            continue
        try:
            _assert_all_sentences_strict_social_or_interruption(norm, resolution)
        except AssertionError:
            continue
        return norm, kind

    return None, None

def apply_interruption_repeat_guard(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    tags: List[str],
    source_text: str | None = None,
) -> tuple[str, Dict[str, Any]]:
    meta: Dict[str, Any] = {
        "forced_interruption_progression": False,
        "forced_interruption_progression_kind": None,
        "interruption_repeat_signature": None,
        "interruption_repeat_count": 0,
    }
    if not isinstance(resolution, dict) or not isinstance(session, dict) or not str(scene_id or "").strip():
        return text, meta

    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    if not npc_id:
        clear_social_exchange_interruption_tracker(session)
        return text, meta

    source_signature = _interruption_signature_for_text(source_text or text, resolution=resolution)
    final_signature = _interruption_signature_for_text(text, resolution=resolution)
    signature = source_signature or final_signature
    if not signature:
        # Empty signature is not proof the exchange ended (upstream may have replaced raw text
        # before this guard); keep tracker so interruption repeat / progression can still fire.
        return text, meta

    sid = str(scene_id or "").strip()
    exchange_key = _social_exchange_interruption_exchange_key(resolution, sid)
    tracker = get_social_exchange_interruption_tracker(session)
    same_exchange = (
        str(tracker.get("scene_id") or "").strip() == sid
        and str(tracker.get("npc_id") or "").strip() == npc_id
        and str(tracker.get("exchange_key") or "").strip() == exchange_key
    )
    same_signature = same_exchange and str(tracker.get("interruption_signature") or "").strip() == signature
    prior_repeat_count = 0
    if same_signature:
        try:
            prior_repeat_count = int(tracker.get("repeat_count", 0) or 0)
        except (TypeError, ValueError):
            prior_repeat_count = 0
    repeat_count = prior_repeat_count + 1 if same_signature else 1
    meta["interruption_repeat_signature"] = signature
    meta["interruption_repeat_count"] = repeat_count

    next_tracker: Dict[str, Any] = {
        "scene_id": sid,
        "npc_id": npc_id,
        "exchange_key": exchange_key,
        "interruption_signature": signature,
        "repeat_count": repeat_count,
        "last_turn_index": _session_turn_counter(session),
        "last_emitted_text": text,
    }

    if repeat_count >= _INTERRUPTION_REPEAT_FORCE_THRESHOLD:
        if (
            source_signature
            and not final_signature
            and _social_line_has_playable_npc_substance(text)
            and not text_is_strict_social_minimal_emergency_fallback(text, resolution)
        ):
            next_tracker["last_emitted_text"] = text
            next_tracker["forced_progression_count"] = int(tracker.get("forced_progression_count", 0) or 0) + 1
            set_social_exchange_interruption_tracker(session, next_tracker)
            meta["forced_interruption_progression"] = True
            meta["forced_interruption_progression_kind"] = "existing_progression_output"
            return text, meta
        progressed, kind = _forced_interruption_progression_line(
            resolution=resolution,
            session=session,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tag_list=tags,
            signature=signature,
            repeat_count=repeat_count,
        )
        if progressed and _normalize_gate_text(progressed) != _normalize_gate_text(text):
            next_tracker["last_emitted_text"] = progressed
            next_tracker["forced_progression_count"] = int(tracker.get("forced_progression_count", 0) or 0) + 1
            set_social_exchange_interruption_tracker(session, next_tracker)
            meta["forced_interruption_progression"] = True
            meta["forced_interruption_progression_kind"] = kind
            return progressed, meta

    set_social_exchange_interruption_tracker(session, next_tracker)
    return text, meta

def hard_reject_social_exchange_text(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str = "",
    world: Dict[str, Any] | None = None,
) -> List[str]:
    """Reason codes for illegal final social_exchange emission."""
    from game.gm import question_resolution_rule_check

    reasons: List[str] = []
    t = _collapse_ws(text)
    if not t:
        reasons.append("empty_social_emission")
        return reasons

    res = resolution if isinstance(resolution, dict) else {}
    social = res.get("social") if isinstance(res.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    sid = str(scene_id or "").strip()
    merged = merged_player_prompt_for_gate(resolution if isinstance(resolution, dict) else None, session, sid)
    meta = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
    na = meta.get("normalized_action") if isinstance(meta.get("normalized_action"), dict) else None
    env_hr = _scene_envelope_for_strict_social(session if isinstance(session, dict) else None, sid)
    auth = resolve_authoritative_social_target(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        player_text=merged,
        normalized_action=na,
        merged_player_prompt=merged,
        scene_envelope=env_hr,
        allow_first_roster_fallback=True,
    )
    auth, _, _ = _auth_after_social_promotion_binding(
        session, world, sid, auth, env_hr, merged_player_prompt=merged
    )
    tp_hr = topic_pressure_speaker_id_for_social_exchange(session if isinstance(session, dict) else {}, sid)
    gr_hr = resolve_grounded_social_speaker(
        session if isinstance(session, dict) else {},
        world if isinstance(world, dict) else {},
        sid,
        env_hr,
        auth,
        proposed_reply_speaker_id=npc_id or None,
        topic_pressure_speaker_id=tp_hr,
    )
    if social.get("reply_speaker_grounding_neutral_bridge"):
        pass
    elif npc_id and not gr_hr.get("allowed"):
        reasons.append("reply_speaker_grounding_denied")
    elif npc_id and gr_hr.get("grounded_actor_id") and npc_id != str(gr_hr.get("grounded_actor_id") or "").strip():
        reasons.append("speaker_binding_mismatch")

    player_prompt = merged or _question_prompt_for_resolution(resolution if isinstance(resolution, dict) else None)
    if player_prompt:
        first_sentence_contract = question_resolution_rule_check(
            player_text=player_prompt,
            gm_reply_text=t,
            resolution=resolution if isinstance(resolution, dict) else None,
        )
        if first_sentence_contract.get("applies") and not first_sentence_contract.get("ok"):
            reasons.extend([f"first_sentence_illegal:{r}" for r in list(first_sentence_contract.get("reasons") or [])])

    low = t.lower()
    advisory = (
        r"\bi['’]d suggest you\b",
        r"\byou should\b",
        r"\byou could\b",
        r"\bbest lead\b",
        r"\bconsider\b",
    )
    if any(re.search(p, low) for p in advisory):
        reasons.append("advisory_prose_in_social_exchange")

    if any(p.search(t) for p in _SCENE_CONTAMINATION_PATTERNS):
        reasons.append("scene_or_ambient_contamination")

    banned = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
        "nothing in the scene points to a clear answer yet",
        "the answer has not formed yet",
    )
    if any(b in low for b in banned):
        reasons.append("banned_stock_phrase")

    for seg in _split_sentences(t):
        if _sentence_is_detached_omniscient_analysis(seg):
            reasons.append("detached_omniscient_analysis")
            break

    has_npc_answer = bool(re.search(r"\".+?\"", t, re.DOTALL)) or bool(
        re.search(
            r"\b(?:says|replies|answers|shakes|shrugs|frowns|jaw tightens|starts to answer)\b",
            t,
            re.IGNORECASE,
        )
    )
    has_interrupt = any(p.search(t) for p in _INTERRUPTION_PATTERNS)
    if has_npc_answer and has_interrupt and not has_explicit_interruption_shape(t):
        reasons.append("mixed_npc_answer_and_scene_interrupt_blob")

    if re.search(r"\bthe scene holds\b", low) or re.search(r"\bscene stays still\b", low):
        reasons.append("scene_hold_placeholder")

    return reasons

def _assert_all_sentences_strict_social_or_interruption(
    text: str,
    resolution: Dict[str, Any] | None,
) -> None:
    """Temporary invariant: final strict-social output must be only SOCIAL or INTERRUPTION sentences."""
    res = resolution if isinstance(resolution, dict) else None
    raw = _collapse_ws(text)
    if not raw:
        return
    for sent in _split_sentences(raw):
        s = (sent or "").strip()
        if not s:
            continue
        cat = _classify_strict_social_ownership_sentence(s, res)
        if cat not in ("social", "interruption"):
            raise AssertionError(
                f"strict_social_final_invariant: sentence not SOCIAL or INTERRUPTION: {cat!r}: {s[:120]!r}"
            )

def _looks_like_strict_social_terminal_placeholder(text: str) -> bool:
    """True for ownership-filter terminal ignorance / tight-lipped lines (not substantive NPC answers)."""
    low = str(text or "").strip().lower()
    if not low:
        return True
    if any(p.search(str(text or "")) for p in _SCENE_CONTAMINATION_PATTERNS):
        return True
    if "hard to say" in low and ("whisper" in low or "nobody" in low or "swear" in low):
        return True
    if re.search(
        r"\b(don'?t know|do not know|no names here|won'?t name|cannot name anyone|do not know a name|do not know enough)\b",
        low,
    ) and (
        "shake" in low or "grimace" in low or "mutter" in low or "spread" in low
    ):
        return True
    return False

def _structured_fact_emission_details() -> dict[str, Any]:
    details = {
        "used_internal_fallback": False,
        "fallback_kind": "none",
        "rejection_reasons": [],
        "final_emitted_source": "structured_fact_candidate_emission",
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "structured_fact",
        "route_illegal_intercepted": False,
        "intercepted_preview": "",
        "candidate_quality_degraded": False,
        "resolved_answer_preferred": False,
        "resolved_answer_source": None,
        "resolved_answer_preference_reason": None,
    }
    attach_realization_fallback_family(details, STRICT_SOCIAL_DETERMINISTIC_FALLBACK)
    return details

def select_best_grounded_social_answer_text(
    *,
    session: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Return the strongest engine-owned social answer snippet (no narration pools / lead salience).

    Delegates to :func:`game.social.select_best_social_answer_candidate` with the same precedence
    as structured strict-social fallbacks: ``topic_revealed``, topic-pressure ``last_answer``,
    reconciled ``clue_knowledge``, then redirect-style ``last_answer`` partials.
    """
    sid = str(scene_id or "").strip()
    sess = session if isinstance(session, dict) else None
    res = resolution if isinstance(resolution, dict) else None
    merged = merged_player_prompt_for_gate(res, sess, sid)
    soc: Dict[str, Any] = {}
    if isinstance(res, dict):
        s = res.get("social")
        if isinstance(s, dict):
            soc = s
    nid = str(soc.get("npc_id") or "").strip() or None
    cand = select_best_social_answer_candidate(
        session=sess if sess is not None else {},
        scene_id=sid,
        npc_id=nid,
        topic_key=None,
        player_text=merged,
        resolution=res,
    )
    kind = str(cand.get("answer_kind") or "").strip()
    txt = str(cand.get("text") or "").strip()
    if kind not in ("structured_fact", "reconciled_fact", "partial_answer") or not txt:
        return {"text": None, "source": str(cand.get("source") or "none"), "answer_kind": kind or "refusal"}
    return {"text": txt, "source": str(cand.get("source") or ""), "answer_kind": kind}

_ACTIONABLE_DETAIL_RE = re.compile(
    r"\b(?:east|west|north|south|road|lane|gate|mill|square|market|crossroad|milestone|patrol)\b",
    re.IGNORECASE,
)

def _actionable_hits(text: str) -> set[str]:
    return {m.group(0).lower() for m in _ACTIONABLE_DETAIL_RE.finditer(str(text or ""))}

def _strict_social_bounded_evasion_or_placeholder_candidate(text: str) -> bool:
    """True for refusal / flat ignorance / pressure-only lines that should not beat substantive facts."""
    t = _collapse_ws(str(text or ""))
    if not t:
        return True
    if _looks_like_strict_social_terminal_placeholder(t):
        return True
    sents = _split_sentences(t)
    if not sents:
        return True
    if len(sents) > 1:
        return False
    s0 = sents[0]
    if any(p.search(s0) for p in _REFUSAL_SIGNAL_PATTERNS):
        return True
    if any(p.search(s0) for p in _PRESSURE_SIGNAL_PATTERNS) and '"' not in s0:
        return True
    if _is_flat_idk_without_qualifier(s0):
        return True
    low = s0.lower()
    if re.search(r"\b(?:can'?t|cannot)\s+help\b", low) and '"' not in s0:
        return True
    return False

def _strict_social_elliptical_fragment_candidate(text: str) -> bool:
    t = _collapse_ws(str(text or "")).strip()
    if not t:
        return True
    core = t.rstrip(".!?…").strip()
    if len(core) <= 6 and core.lower() in {"just", "only", "right", "there", "here", "well"}:
        return True
    if re.match(r"^just\s*\.?$", t, re.IGNORECASE):
        return True
    return False

def _strict_social_fragmentary_trailing_clause(text: str) -> bool:
    t = _collapse_ws(str(text or ""))
    low = t.lower()
    if re.search(r"\b(?:though|because|if|when)\s+the\s+\w+\s*$", low):
        return True
    if re.search(r",\s*though\s*$", low) and len(t) < 48:
        return True
    return False

def _grounded_snippet_is_substantive(snippet: str, *, answer_kind: str) -> bool:
    s = _collapse_ws(str(snippet or ""))
    if len(s) < 14:
        return False
    if answer_kind == "partial_answer":
        return len(s) >= 18
    return True

def _normalized_social_candidate_is_degraded_vs_grounded(
    accepted_text: str,
    grounded_snippet: str,
    *,
    answer_kind: str,
) -> tuple[bool, str]:
    """Conservative: True only when the accepted line is clearly worse than engine-grounded text."""
    c = _collapse_ws(str(accepted_text or ""))
    g = _collapse_ws(str(grounded_snippet or ""))
    if not c or not g:
        return False, ""
    if not _grounded_snippet_is_substantive(g, answer_kind=answer_kind):
        return False, ""
    if c.strip() == g.strip():
        return False, ""

    if _strict_social_bounded_evasion_or_placeholder_candidate(c):
        return True, "evasion_or_placeholder_over_substantive_grounded_answer"

    if _strict_social_elliptical_fragment_candidate(c):
        return True, "elliptical_fragment"

    if _strict_social_fragmentary_trailing_clause(c):
        return True, "fragmentary_trailing_clause"

    gl, cl = g.lower(), c.lower()
    if len(g) >= 52 and len(c) < len(g) * 0.5:
        gh = _actionable_hits(g)
        ch = _actionable_hits(c)
        if gh and gh - ch:
            return True, "lost_actionable_detail_vs_grounded_answer"

    if len(g) >= 40 and len(c) + 35 < len(g):
        toks = [t for t in re.findall(r"[a-z]{5,}", gl) if t not in {"their", "there", "where", "which", "would", "could", "about", "mutters", "runner", "guard", "tavern"}]
        hits = sum(1 for t in toks[:10] if t in cl)
        if len(toks) >= 4 and hits <= 1:
            return True, "much_shorter_less_informative_vs_grounded_answer"

    return False, ""

def _strict_social_resolved_line_passes_legality(
    line: str,
    *,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
) -> bool:
    t = _normalize_gate_text(line)
    low = t.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        return False
    return not hard_reject_social_exchange_text(
        t,
        resolution=resolution,
        session=session if isinstance(session, dict) else None,
        scene_id=str(scene_id or "").strip(),
        world=world if isinstance(world, dict) else None,
    )

def _prefer_resolved_social_answer_over_candidate(
    accepted_text: str,
    *,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    tags: List[str],
) -> tuple[str, Dict[str, Any]]:
    """If accepted text is clearly degraded vs engine-grounded facts, emit formatted grounded line instead.

    The replacement must pass the same strict-social ownership filter and
    :func:`hard_reject_social_exchange_text` checks as normal final emission.
    """
    sid = str(scene_id or "").strip()
    base_meta: Dict[str, Any] = {
        "candidate_quality_degraded": False,
        "resolved_answer_preferred": False,
        "resolved_answer_source": None,
        "resolved_answer_preference_reason": None,
    }
    sess = session if isinstance(session, dict) else None
    if not sid or not isinstance(resolution, dict):
        return accepted_text, base_meta

    grounded = select_best_grounded_social_answer_text(
        session=sess,
        scene_id=sid,
        resolution=resolution,
    )
    snippet = grounded.get("text")
    src = str(grounded.get("source") or "")
    akind = str(grounded.get("answer_kind") or "")
    if not isinstance(snippet, str) or not str(snippet).strip():
        return accepted_text, base_meta

    degraded, deg_reason = _normalized_social_candidate_is_degraded_vs_grounded(
        accepted_text,
        str(snippet).strip(),
        answer_kind=akind,
    )
    if not degraded:
        return accepted_text, base_meta

    base_meta["candidate_quality_degraded"] = True
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    synth = format_structured_fact_social_line(resolution, str(snippet).strip())
    synth_f = apply_strict_social_sentence_ownership_filter(
        synth,
        resolution=resolution,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    synth_n = _normalize_gate_text(synth_f)
    if synth_n.strip() == _normalize_gate_text(accepted_text).strip():
        base_meta["candidate_quality_degraded"] = False
        return accepted_text, base_meta

    if not _strict_social_resolved_line_passes_legality(
        synth_n,
        resolution=resolution,
        session=sess,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
    ):
        base_meta["resolved_answer_preference_reason"] = "stronger_answer_failed_strict_legality"
        return accepted_text, base_meta

    base_meta["resolved_answer_preferred"] = True
    base_meta["resolved_answer_source"] = src or None
    base_meta["resolved_answer_preference_reason"] = deg_reason
    _assert_all_sentences_strict_social_or_interruption(synth_n, resolution)
    return synth_n, base_meta

def _try_emit_structured_fact_strict_line(
    *,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    tag_list: List[str],
) -> str | None:
    """If topic pressure / clues hold a factual answer, return route-legal strict-social text."""
    sid = str(scene_id or "").strip()
    sess = session if isinstance(session, dict) else None
    merged_pt = merged_player_prompt_for_gate(resolution, sess, sid)
    soc_pre = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    nid_pre = str(soc_pre.get("npc_id") or "").strip() or None
    cand = select_best_social_answer_candidate(
        session=sess,
        scene_id=sid,
        npc_id=nid_pre,
        topic_key=None,
        player_text=merged_pt,
        resolution=resolution,
    )
    if cand.get("answer_kind") not in ("structured_fact", "reconciled_fact") or not str(cand.get("text") or "").strip():
        return None
    synth = format_structured_fact_social_line(resolution, str(cand.get("text") or ""))
    synth_f = apply_strict_social_sentence_ownership_filter(
        synth,
        resolution=resolution,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    synth_n = _normalize_gate_text(synth_f)
    low_s = synth_n.lower()
    banned_any_route2 = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    reasons2: List[str] = []
    if any(phrase in low_s for phrase in banned_any_route2):
        reasons2.append("banned_stock_phrase")
    reasons2.extend(
        hard_reject_social_exchange_text(
            synth_n,
            resolution=resolution,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
        )
    )
    if reasons2:
        return None
    if isinstance(resolution.get("social"), dict):
        resolution["social"]["answer_candidate_selected"] = str(cand.get("answer_kind") or "")
        resolution["social"]["answer_candidate_source"] = str(cand.get("source") or "")
        resolution["social"]["answer_candidate_dimension"] = classify_social_question_dimension(merged_pt)
        resolution["social"]["refusal_suppressed_by_structured_fact"] = True
    preview = synth_n[:140] + ("…" if len(synth_n) > 140 else "")
    resolution["hint"] = (
        "Final strict-social emission used stored thread facts as the spoken NPC line "
        f"({preview}). This is not a refusal and not an empty-information turn."
    )
    _assert_all_sentences_strict_social_or_interruption(synth_n, resolution)
    return synth_n

def _apply_social_emission_integrity_guard(
    accepted_text: str,
    *,
    player_text: str,
    resolution: Dict[str, Any],
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    tags: List[str],
) -> Tuple[str, Dict[str, Any]]:
    """Replace obviously malformed strict-social lines using structured outcome templates."""
    sid = str(scene_id or "").strip()
    meta: Dict[str, Any] = {
        "social_emission_integrity_replaced": False,
        "social_emission_integrity_reasons": [],
        "social_emission_integrity_fallback_kind": None,
    }
    bad, rsn = social_final_emission_malformed_player_echo(
        player_text=player_text,
        final_text=accepted_text,
        resolution=resolution,
    )
    if not bad:
        return accepted_text, meta
    meta["social_emission_integrity_reasons"] = list(rsn)
    seed = (
        f"{sid}|integrity|{sum(ord(c) for c in str(player_text))}|{sum(ord(c) for c in str(accepted_text))}"
    )
    candidates = social_integrity_fallback_line_candidates(
        resolution=resolution,
        player_text=player_text,
        session=session,
        scene_id=sid,
        tag_list=tags,
        seed=seed,
    )
    for raw_line, fk in candidates:
        filtered = apply_strict_social_sentence_ownership_filter(
            raw_line,
            resolution=resolution,
            tags=tags or None,
            session=session,
            scene_id=sid,
        )
        norm = _normalize_gate_text(filtered)
        low = norm.lower()
        banned_any = (
            "from here, no certain answer presents itself",
            "the truth is still buried beneath rumor and rain",
        )
        if any(b in low for b in banned_any):
            continue
        rej = hard_reject_social_exchange_text(
            norm,
            resolution=resolution,
            session=session,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
        )
        if rej:
            continue
        try:
            _assert_all_sentences_strict_social_or_interruption(norm, resolution)
        except AssertionError:
            continue
        meta["social_emission_integrity_replaced"] = True
        meta["social_emission_integrity_fallback_kind"] = fk
        return norm, meta

    return accepted_text, meta

def build_final_strict_social_response(
    candidate_text: str,
    *,
    resolution: Dict[str, Any] | None,
    tags: Optional[List[str]] = None,
    session: Optional[Dict[str, Any]] = None,
    scene_id: str = "",
    world: Optional[Dict[str, Any]] = None,
) -> tuple[str, dict[str, Any]]:
    """Single final writer for strict-social turns.

    Runs :func:`apply_strict_social_sentence_ownership_filter` on the candidate, then
    :func:`hard_reject_social_exchange_text` (and the same banned-phrase gate as the emission gate).
    If the result is rejected, selects deterministic / emergency fallback and runs the ownership
    filter again on that fallback candidate so no unfiltered line reaches the player.
    """
    tag_list = [str(t) for t in tags if isinstance(t, str)] if isinstance(tags, list) else []
    res = resolution if isinstance(resolution, dict) else None
    sid = str(scene_id or "").strip()
    sess = session if isinstance(session, dict) else None

    soc0 = res.get("social") if isinstance(res, dict) and isinstance(res.get("social"), dict) else {}
    if soc0.get("reply_speaker_grounding_neutral_bridge"):
        clear_social_exchange_interruption_tracker(sess)
        nb = neutral_reply_speaker_grounding_bridge_line(
            seed=f"{sid}|neutral_grounding|{_question_prompt_for_resolution_early(res)}"
        )
        details = {
            "used_internal_fallback": True,
            "fallback_kind": "neutral_speaker_grounding_bridge",
            "rejection_reasons": [],
            "final_emitted_source": "neutral_reply_speaker_grounding_bridge",
            "deterministic_attempted": False,
            "deterministic_passed": False,
            "fallback_pool": "neutral_grounding",
            "route_illegal_intercepted": False,
            "intercepted_preview": "",
            "candidate_quality_degraded": False,
            "resolved_answer_preferred": False,
            "resolved_answer_source": None,
            "resolved_answer_preference_reason": None,
        }
        attach_realization_fallback_family(details, STRICT_SOCIAL_DETERMINISTIC_FALLBACK)
        return nb, details

    cand0 = _normalize_gate_text(candidate_text)
    if is_route_illegal_global_or_sanitizer_fallback_text(cand0):
        st_illegal = _try_emit_structured_fact_strict_line(
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tag_list=tag_list,
        )
        if st_illegal:
            st_illegal, interrupt_meta_illegal = apply_interruption_repeat_guard(
                st_illegal,
                resolution=res,
                session=sess,
                scene_id=sid,
                world=world if isinstance(world, dict) else None,
                tags=tag_list,
                source_text=candidate_text,
            )
            return st_illegal, {
                **_structured_fact_emission_details(),
                **interrupt_meta_illegal,
            }

    filtered = apply_strict_social_sentence_ownership_filter(
        candidate_text,
        resolution=res,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    text = _normalize_gate_text(filtered)

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    reasons: List[str] = []
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")
    reasons.extend(
        hard_reject_social_exchange_text(
            text,
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
        )
    )

    if not reasons:
        soc_ok = res.get("social") if isinstance(res, dict) and isinstance(res.get("social"), dict) else {}
        prefer_structured = bool(
            isinstance(res, dict)
            and (
                str(soc_ok.get("reply_kind") or "").strip().lower() == "refusal"
                or res.get("success") is not True
                or soc_ok.get("refusal_suppressed_by_structured_fact") is True
            )
        )
        if prefer_structured and isinstance(res, dict) and _looks_like_strict_social_terminal_placeholder(text):
            st = _try_emit_structured_fact_strict_line(
                resolution=res,
                session=sess,
                scene_id=sid,
                world=world if isinstance(world, dict) else None,
                tag_list=tag_list,
            )
            if st:
                st, interrupt_meta = apply_interruption_repeat_guard(
                    st,
                    resolution=res,
                    session=sess,
                    scene_id=sid,
                    world=world if isinstance(world, dict) else None,
                    tags=tag_list,
                    source_text=candidate_text,
                )
                return st, {
                    **_structured_fact_emission_details(),
                    **interrupt_meta,
                }
        pref_text, pref_meta = _prefer_resolved_social_answer_over_candidate(
            text,
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tags=tag_list,
        )
        text = pref_text
        merged_pt_ig = merged_player_prompt_for_gate(res, sess, sid)
        text, integ_meta = _apply_social_emission_integrity_guard(
            text,
            player_text=merged_pt_ig,
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tags=tag_list,
        )
        text, interrupt_meta = apply_interruption_repeat_guard(
            text,
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tags=tag_list,
            source_text=candidate_text,
        )
        _assert_all_sentences_strict_social_or_interruption(text, res)
        final_emitted_source = (
            "generated_candidate"
            if _normalize_gate_text(candidate_text).strip() == text.strip()
            else "normalized_social_candidate"
        )
        if pref_meta.get("resolved_answer_preferred"):
            final_emitted_source = "resolved_grounded_social_answer"
        if integ_meta.get("social_emission_integrity_replaced"):
            final_emitted_source = "social_emission_integrity_fallback"
        return text, {
            "used_internal_fallback": False,
            "fallback_kind": "none",
            "rejection_reasons": [],
            "final_emitted_source": final_emitted_source,
            "deterministic_attempted": False,
            "deterministic_passed": False,
            "fallback_pool": "none",
            "route_illegal_intercepted": False,
            "intercepted_preview": "",
            **pref_meta,
            **integ_meta,
            **interrupt_meta,
        }

    if isinstance(res, dict):
        st2 = _try_emit_structured_fact_strict_line(
            resolution=res,
            session=sess,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            tag_list=tag_list,
        )
        if st2:
            st2, interrupt_meta = apply_interruption_repeat_guard(
                st2,
                resolution=res,
                session=sess,
                scene_id=sid,
                world=world if isinstance(world, dict) else None,
                tags=tag_list,
                source_text=candidate_text,
            )
            return st2, {
                **_structured_fact_emission_details(),
                **interrupt_meta,
            }

    uncertainty_source = emission_gate_uncertainty_source(tag_list, text)
    pressure_active = emission_gate_pressure_active(tag_list, session, sid)
    interruption_active = emission_gate_interruption_active(tag_list, text)
    seed = (
        f"{sid}|{_speaker_label_for_emission_seed(res)}|{_question_prompt_for_resolution_early(res)}|"
        f"{uncertainty_source}|{pressure_active}|{interruption_active}|{'|'.join(sorted(set(tag_list)))}"
    )
    fallback_pool = "social_deterministic"
    deterministic_attempted = True
    fallback_text, fallback_kind = deterministic_social_fallback_line(
        resolution=res,
        uncertainty_source=uncertainty_source,
        pressure_active=pressure_active,
        interruption_active=interruption_active,
        seed=seed,
    )
    deterministic_passed = replacement_is_route_legal_social(
        fallback_text,
        resolution=res,
        session=sess,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
    )
    final_emitted_source = "deterministic_social_fallback"
    if not deterministic_passed:
        fallback_text = minimal_social_emergency_fallback_line(res)
        fallback_kind = "emergency_social_minimal"
        final_emitted_source = "minimal_social_emergency_fallback"
        deterministic_passed = False

    route_illegal_intercepted = False
    intercepted_preview = ""
    if is_route_illegal_global_or_sanitizer_fallback_text(fallback_text):
        intercepted_preview = fallback_text[:80]
        fallback_text = minimal_social_emergency_fallback_line(res)
        fallback_kind = "emergency_social_minimal"
        final_emitted_source = "minimal_social_emergency_fallback"
        deterministic_passed = False
        route_illegal_intercepted = True

    fb_filtered = apply_strict_social_sentence_ownership_filter(
        fallback_text,
        resolution=res,
        tags=tag_list or None,
        session=sess,
        scene_id=sid,
    )
    out_text = _normalize_gate_text(fb_filtered)
    out_text, interrupt_meta = apply_interruption_repeat_guard(
        out_text,
        resolution=res,
        session=sess,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
        tags=tag_list,
        source_text=candidate_text,
    )
    _assert_all_sentences_strict_social_or_interruption(out_text, res)

    details = {
        "used_internal_fallback": True,
        "fallback_kind": fallback_kind,
        "rejection_reasons": reasons,
        "final_emitted_source": final_emitted_source,
        "deterministic_attempted": deterministic_attempted,
        "deterministic_passed": deterministic_passed,
        "fallback_pool": fallback_pool,
        "route_illegal_intercepted": route_illegal_intercepted,
        "intercepted_preview": intercepted_preview,
        "candidate_quality_degraded": False,
        "resolved_answer_preferred": False,
        "resolved_answer_source": None,
        "resolved_answer_preference_reason": None,
        **interrupt_meta,
    }
    attach_realization_fallback_family(details, STRICT_SOCIAL_DETERMINISTIC_FALLBACK)
    return out_text, details

# --- BV14A compatibility re-exports (canonical implementations in domain modules) ---
__all__ = [
    "StrictSocialEmergencyFallbackSurface",
    "apply_social_exchange_retry_fallback_gm",
    "apply_strict_social_ownership_enforcement",
    "apply_strict_social_sentence_ownership_filter",
    "apply_strict_social_terminal_dialogue_fallback_if_needed",
    "build_final_strict_social_response",
    "build_open_social_solicitation_recovery",
    "coerce_resolution_for_strict_social_emission",
    "coerced_strict_social_allowed_by_merged_prompt",
    "deterministic_social_fallback_line",
    "effective_scene_npc_roster",
    "effective_strict_social_resolution_for_emission",
    "emission_gate_interruption_active",
    "emission_gate_pressure_active",
    "emission_gate_uncertainty_source",
    "hard_reject_social_exchange_text",
    "interruption_cue_present_in_text",
    "is_conversational_npc_dialogue_line",
    "is_route_illegal_global_or_sanitizer_fallback_text",
    "is_scene_directed_watch_question",
    "is_social_exchange_resolution",
    "lawful_strict_social_dialogue_emergency_fallback_line",
    "log_final_emission_decision",
    "log_final_emission_trace",
    "looks_like_npc_directed_question",
    "merged_player_prompt_for_gate",
    "minimal_social_emergency_fallback_line",
    "minimal_social_resolution_for_directed_question_guard",
    "normalize_social_exchange_candidate",
    "player_line_triggers_strict_social_emission",
    "project_strict_social_replace_realization_family",
    "reconcile_strict_social_resolution_speaker",
    "repair_strict_social_terminal_dialogue_fallback_if_needed",
    "replacement_is_route_legal_social",
    "resolve_strict_social_npc_target_id",
    "select_best_grounded_social_answer_text",
    "select_strict_social_emergency_fallback_line",
    "should_apply_strict_social_exchange_emission",
    "social_fallback_line_for_sanitizer",
    "social_final_emission_malformed_player_echo",
    "stamp_strict_social_deterministic_fallback_family",
    "strict_social_deterministic_fallback_family_token",
    "strict_social_emission_will_apply",
    "strict_social_ownership_terminal_fallback",
    "strict_social_suppress_non_native_coercion_for_narration_beat",
    "strict_social_terminal_dialogue_fallback_valid",
    "synthetic_social_exchange_resolution_for_emission",
]

