"""Narrative authority contract: what narration may assert vs defer (read-only).

Distinguishes:
- **Visible observation**: sensory / bodily cues players could witness (hesitation, a glance).
- **Bounded inference**: impression language or explicit uncertainty (might, seems, could be).
- **Hidden-fact assertion**: causal or backstage truth stated as settled fact (planted, sabotage).
- **Adjudicated outcome**: engine-resolved success/fail/mechanical result the model may state as true.

This module does **not** re-derive visibility rules; consume ``narration_visibility`` contracts for
fact/entity visibility. It adds a separate layer for unjustified authority over outcomes, hidden
causes, and NPC internal states.
"""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Mapping, Optional, Tuple

# ---------------------------------------------------------------------------
# Public vocab / constants
# ---------------------------------------------------------------------------

NARRATIVE_AUTHORITY_UNCERTAINTY_REASONS: Tuple[str, ...] = (
    "unresolved_action",
    "unknown_intent",
    "unknown_hidden_fact",
    "insufficient_basis",
)

NARRATIVE_AUTHORITY_ALLOWED_DEFERRALS: Tuple[str, ...] = (
    "ask_for_roll",
    "bounded_uncertainty",
    "branch_outcome",
)

NARRATIVE_AUTHORITY_FORBIDDEN_ASSERTION_KINDS: Tuple[str, ...] = (
    "invented_outcome",
    "invented_hidden_fact",
    "invented_intent",
)

# Risky / mechanics-facing resolution kinds (conservative roll-first deferral ordering).
_MECHANICAL_SOCIAL_KINDS = frozenset(
    {"persuade", "intimidate", "deceive", "barter", "recruit", "social_probe"}
)
_MECHANICAL_EXPLORATION_KINDS = frozenset({"interact", "investigate", "discover_clue"})
_COMBAT_KINDS = frozenset(
    {
        "initiative",
        "attack",
        "spell",
        "skill_check",
        "enemy_attack",
        "enemy_turn_skipped",
        "end_turn",
    }
)

_DIALOGUE_SPAN_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r'"[^"\n]*"'),
    re.compile(r"“[^”\n]*”"),
    re.compile(r"‘[^’\n]*’"),
    re.compile(r"(?<!\w)'[^'\n]*'(?!\w)"),
)


def _clean_str(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _normalize_authority_text(value: str) -> str:
    """Lowercase, collapse whitespace, trim edge punctuation (deterministic, inspectable)."""
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
    """Return (start, end, text) sentences aligned to *original_text* via *masked_text* boundaries."""
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


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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
    """True only when *res* carries a settled mechanical or structured outcome (not attempt-only)."""
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


def _mechanical_result_available(res: Mapping[str, Any]) -> bool:
    sc = res.get("skill_check")
    if isinstance(sc, Mapping) and any(
        k in sc for k in ("roll", "total", "modifier", "difficulty", "dc")
    ):
        return True
    combat = res.get("combat")
    if isinstance(combat, Mapping) and combat:
        return True
    return False


def _success_state_available(res: Mapping[str, Any]) -> bool:
    if isinstance(res.get("success"), bool):
        return True
    sc = res.get("skill_check")
    if isinstance(sc, Mapping) and _bool_from_skill_check(sc) is not None:
        return True
    return False


def _normalize_resolution_kind(res: Mapping[str, Any] | None) -> Optional[str]:
    if not res:
        return None
    kind = _clean_str(res.get("kind")).lower()
    return kind or None


def build_narrative_authority_contract(
    *,
    resolution: Mapping[str, Any] | None,
    narration_visibility: Mapping[str, Any] | None,
    scene_state_anchor_contract: Mapping[str, Any] | None,
    speaker_selection_contract: Mapping[str, Any] | None,
    session_view: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Assemble an inspectable contract for narrative authority (no world mutation).

    Separates **visible observation** (what could be seen) from **bounded inference**
    (hedged impressions), **hidden-fact assertions** (backstage causality stated as fact),
    and **adjudicated outcomes** (engine-resolved mechanical results). The contract never
    reads hidden layers beyond the slices already published in ``narration_visibility``.
    """
    res = _mapping_or_empty(resolution)
    vis = _mapping_or_empty(narration_visibility)
    sp = _mapping_or_empty(speaker_selection_contract)
    sess = _mapping_or_empty(session_view)

    vis_facts_raw = vis.get("visible_fact_strings")
    visible_fact_strings: List[str] = []
    if isinstance(vis_facts_raw, list):
        for item in vis_facts_raw:
            if not isinstance(item, str):
                continue
            n = _normalize_authority_text(item)
            if n:
                visible_fact_strings.append(n)

    hidden_raw = vis.get("hidden_fact_strings")
    hidden_fact_strings_present = bool(
        isinstance(hidden_raw, list)
        and any(isinstance(x, str) and _normalize_authority_text(x) for x in hidden_raw)
    )

    disc_raw = vis.get("discoverable_fact_strings")
    discoverable_hinting_allowed = bool(
        isinstance(disc_raw, list)
        and any(isinstance(x, str) and _normalize_authority_text(x) for x in disc_raw)
    )

    resolution_kind = _normalize_resolution_kind(res if isinstance(resolution, Mapping) else None)
    authoritative_outcome_available = (
        _resolution_has_authoritative_outcome(res) if isinstance(resolution, Mapping) else False
    )
    mechanical_result_available = (
        _mechanical_result_available(res) if isinstance(resolution, Mapping) else False
    )
    success_state_available = (
        _success_state_available(res) if isinstance(resolution, Mapping) else False
    )

    active_speaker_id = _clean_str(sp.get("primary_speaker_id")) or None
    active_target_id = _clean_str(sess.get("active_interaction_target_id")) or _clean_str(
        vis.get("active_interlocutor_id")
    )
    active_target_id = active_target_id or None

    forbid_unresolved_outcome_assertions = not authoritative_outcome_available
    forbid_hidden_fact_assertions = True
    forbid_npc_intent_assertions_without_basis = True

    # Contract flag: builder has no player text; validator refines with ``player_text``.
    allow_bounded_intent_reading_only_when_player_asked = False

    mechanical_risky = False
    if isinstance(resolution, Mapping):
        if resolution_kind in _COMBAT_KINDS or resolution_kind in _MECHANICAL_EXPLORATION_KINDS:
            mechanical_risky = True
        if resolution_kind in _MECHANICAL_SOCIAL_KINDS:
            mechanical_risky = True
        if res.get("requires_check"):
            mechanical_risky = True
        p = _normalize_authority_text(_clean_str(res.get("prompt")))
        for token in (
            "sneak",
            "stealth",
            "hide",
            "lockpick",
            "pick the lock",
            "disable device",
            "bluff",
            "lie",
            "deceive",
            "sense motive",
            "perception",
            "climb",
            "search",
        ):
            if token in p:
                mechanical_risky = True
                break

    if not authoritative_outcome_available and mechanical_risky:
        preferred_deferral_order: List[str] = [
            "ask_for_roll",
            "branch_outcome",
            "bounded_uncertainty",
        ]
    else:
        preferred_deferral_order = ["bounded_uncertainty", "branch_outcome", "ask_for_roll"]

    anchor_on = bool(
        isinstance(scene_state_anchor_contract, Mapping) and scene_state_anchor_contract.get("enabled")
    )
    enabled = True

    debug_flags = {
        "mechanical_risky": mechanical_risky,
        "pending_player_roll": isinstance(resolution, Mapping) and _resolution_pending_player_roll(res),
        "anchor_contract_enabled": anchor_on,
    }
    debug_inputs = {
        "has_resolution": isinstance(resolution, Mapping),
        "has_narration_visibility": bool(vis),
        "has_scene_state_anchor_contract": isinstance(scene_state_anchor_contract, Mapping),
        "has_speaker_selection_contract": bool(sp),
        "has_session_view": bool(sess),
    }
    debug_reason = (
        f"narrative_authority: authoritative_outcome={authoritative_outcome_available} "
        f"kind={resolution_kind!r} mechanical_risky={mechanical_risky}"
    )

    return {
        "enabled": enabled,
        "authoritative_outcome_available": authoritative_outcome_available,
        "resolution_kind": resolution_kind,
        "success_state_available": success_state_available,
        "mechanical_result_available": mechanical_result_available,
        "active_speaker_id": active_speaker_id,
        "active_target_id": active_target_id,
        "visible_fact_strings": list(visible_fact_strings),
        "hidden_fact_strings_present": hidden_fact_strings_present,
        "discoverable_hinting_allowed": discoverable_hinting_allowed,
        "forbid_unresolved_outcome_assertions": forbid_unresolved_outcome_assertions,
        "forbid_hidden_fact_assertions": forbid_hidden_fact_assertions,
        "forbid_npc_intent_assertions_without_basis": forbid_npc_intent_assertions_without_basis,
        "allow_bounded_intent_reading_only_when_player_asked": allow_bounded_intent_reading_only_when_player_asked,
        "allowed_deferrals": list(NARRATIVE_AUTHORITY_ALLOWED_DEFERRALS),
        "preferred_deferral_order": preferred_deferral_order,
        "debug_reason": debug_reason,
        "debug_inputs": debug_inputs,
        "debug_flags": debug_flags,
    }


# --- Detection helpers (deterministic regex; conservative false negatives) ---

_SAFE_UNCERTAINTY_HEDGE_RE = re.compile(
    r"(?<!\w)(?:"
    r"could be|might be|may be|perhaps|maybe|possibly|"
    r"one possibility is|it's possible|it is possible|"
    r"you can't tell yet|you cannot tell yet|hard to tell|difficult to tell|"
    r"unclear if|unclear whether|not sure if|not sure whether|"
    r"it looks like|it seems|seems to|appears to|as if|"
    r"for all you know|from what you can see"
    r")(?!\w)"
)

_ROLL_PROMPT_RE = re.compile(
    r"(?<!\w)(?:"
    r"give me (?:a |an )?(?:dice )?(?:roll|check)|"
    r"roll (?:a |an )?(?:d20|die|dice)?|"
    r"make (?:a |an )?(?:[\w\-]+ )?(?:check|roll)|"
    r"(?:ability|skill) check|"
    r"\bdc\b|difficulty class|"
    r"(?:disable device|sleight of hand|stealth|perception|insight|deception|persuasion|"
    r"intimidation|investigation|athletics|acrobatics)\s+(?:check|roll)"
    r")",
    re.IGNORECASE,
)

_BRANCH_FRAMING_RE = re.compile(
    r"(?<!\w)(?:"
    r"if you (?:succeed|fail|make it|don't make it|miss)|"
    r"if that succeeds|if that fails|on a success|on a failure|"
    r"on a good read|on a bad read|on a high roll|on a low roll|"
    r"whether you (?:succeed|fail)|"
    r"depending on (?:the roll|your roll|the check)|"
    r"two outcomes|either you"
    r")(?!\w)",
    re.IGNORECASE,
)

_STRONG_OUTCOME_ASSERTION_RE = re.compile(
    r"(?<!\w)(?:"
    r"the lock (?:clicks|snaps) open|the lock opens|the door opens|"
    r"(?:spring|springs) unlocked|"
    r"(?:you|your) (?:slip|sneak|pass)(?:\s+\w+){0,3}\s+unseen|get (?:past|by) (?:him|her|them)\s+unseen|"
    r"(?:your )?bluff works|the bluff works|(?:your )?lie lands|they buy it|the guard believes you|"
    r"they believe you|(?:you|she|he|they) (?:believes?|believe) you\b|"
    r"\byou miss\b|the blow lands|lands cleanly|strikes true|a (?:solid )?hit|"
    r"\byou succeed\b|\byou success\b|you are successful|you manage to|you fail|you've failed|you have failed|"
    r"it works perfectly|that works|nothing happens — you fail|you don't make it"
    r")(?!\w)",
    re.IGNORECASE,
)

_OUTCOME_VERBS_RE = re.compile(
    r"(?<!\w)(?:"
    r"\byou\s+(?:open|unlock|disable|pick|break|force|bash|convince|trick|fool|escape|evade)\b|"
    r"\bit\s+opens\b|swings\s+open|gives way|yields"
    r")",
    re.IGNORECASE,
)

_HIDDEN_FACT_CERTAINTY_RE = re.compile(
    r"(?<!\w)(?:"
    r"(?:this|that|it) was definitely|without a doubt|beyond doubt|"
    r"(?:this|that) was (?:clearly|obviously) sabotage|"
    r"the(?:\s+\w+){0,3} (?:was|were) planted|"
    r"someone moved it recently|moved it recently|"
    r"(?:the )?room was searched by professionals|searched by professionals|"
    r"the poison came from|this was sabotage|this was murder|"
    r"that proves (?:who|that)|"
    r"you know (?:someone|they) (?:did|planted|moved|tampered)"
    r")(?!\w)",
    re.IGNORECASE,
)

_INTENT_CERTAINTY_RE = re.compile(
    r"(?<!\w)(?:"
    r"(?:he|she|they) (?:wants|want) you to\b|"
    r"(?:he|she|they) (?:intends|mean|plan)s? to\b|"
    r"(?:he|she|they) (?:are|is) (?:going to|gonna)\s+(?:betray|flee|run|leave|kill|attack)|"
    r"(?:he|she|they) (?:plan|plans) to (?:betray|flee|stall|trap|ambush|lead)|"
    r"(?:he|she|they) (?:are|is) hiding something from you|"
    r"(?:he|she|they) will betray you|meant to betray"
    r")(?!\w)",
    re.IGNORECASE,
)

_BOUNDED_INTENT_OK_RE = re.compile(
    r"(?<!\w)(?:might|may|could|seems|appears|looks like|as though|if you're reading)"
    r"(?!\w)",
    re.IGNORECASE,
)


def _sentence_has_hedge(sentence: str) -> bool:
    low = sentence.lower()
    if _SAFE_UNCERTAINTY_HEDGE_RE.search(low):
        return True
    if _BOUNDED_INTENT_OK_RE.search(low):
        return True
    if re.search(r"\b(if|whether)\b", low):
        return True
    return False


def narrative_authority_prefers_roll_prompt(
    player_text: str | None,
    resolution: Mapping[str, Any] | None = None,
) -> bool:
    """Return True when deferring with an explicit roll prompt is usually appropriate (conservative)."""
    blob = " ".join(
        [
            _normalize_authority_text(_clean_str(player_text)),
            _normalize_authority_text(_clean_str((resolution or {}).get("prompt"))),
        ]
    ).strip()
    if not blob:
        res = _mapping_or_empty(resolution)
        rk = _normalize_resolution_kind(res if isinstance(resolution, Mapping) else None)
        if rk in _COMBAT_KINDS or rk in _MECHANICAL_EXPLORATION_KINDS or rk in _MECHANICAL_SOCIAL_KINDS:
            return True
        return False

    risky_tokens = (
        " sneak",
        " stealth",
        " hide ",
        " hidden",
        " lockpick",
        " pick the lock",
        " disable device",
        " trap",
        " climb ",
        " jump ",
        " bluff",
        " lie ",
        " lying",
        " deceive",
        " deception",
        " pickpocket",
        " sense motive",
        " read him",
        " read her",
        " perceive",
        " perception",
        " investigate",
        " search ",
        " attack ",
        " strike ",
        " shoot ",
    )
    if any(tok in f" {blob} " for tok in risky_tokens):
        return True
    if isinstance(resolution, Mapping) and resolution.get("requires_check"):
        return True
    rk = _normalize_resolution_kind(resolution if isinstance(resolution, Mapping) else None)
    if rk in _COMBAT_KINDS or rk in _MECHANICAL_EXPLORATION_KINDS:
        return True
    if rk in _MECHANICAL_SOCIAL_KINDS:
        return True
    return False


def _player_asks_intent_or_read(player_text: str | None) -> bool:
    p = _normalize_authority_text(_clean_str(player_text))
    if not p:
        return False
    needles = (
        "what is he thinking",
        "what is she thinking",
        "what are they thinking",
        "sense motive",
        "read him",
        "read her",
        "read them",
        "tell me his intentions",
        "her intentions",
        "their intentions",
        "his motives",
        "her motives",
    )
    return any(n in p for n in needles)


def _detect_deferral_mode(masked_full: str) -> Optional[str]:
    low = masked_full.lower()
    if _ROLL_PROMPT_RE.search(low):
        return "ask_for_roll"
    if _BRANCH_FRAMING_RE.search(low):
        return "branch_outcome"
    if _SAFE_UNCERTAINTY_HEDGE_RE.search(low):
        return "bounded_uncertainty"
    return None


def _outcome_assertion_hits(sentence: str, masked_sentence: str) -> bool:
    if _STRONG_OUTCOME_ASSERTION_RE.search(masked_sentence):
        return True
    # Conservative second lane: "you open / it opens" style without hedges
    if _OUTCOME_VERBS_RE.search(masked_sentence) and not _sentence_has_hedge(sentence):
        return True
    return False


def validate_narrative_authority(
    text: str,
    contract: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
    player_text: str | None = None,
) -> Dict[str, Any]:
    """Validate *text* against a ``build_narrative_authority_contract`` result.

    Flags **invented outcomes** when success/failure/effect language appears without
    ``authoritative_outcome_available``, **invented hidden facts** when causal certainty
    appears without hedges, and **invented intent** when motive/plan is stated as fact.
    Observable cues and properly hedged reads are allowed; roll prompts and branch framing
    count as approved deferrals.
    """
    if not isinstance(contract, Mapping):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": ["invalid_contract"],
            "matched_deferral_mode": None,
            "assertion_flags": {
                "invented_outcome": False,
                "invented_hidden_fact": False,
                "invented_intent": False,
                "overcertain_unresolved_action": False,
            },
            "debug": {"reason": "invalid_contract"},
        }

    if not contract.get("enabled"):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "matched_deferral_mode": None,
            "assertion_flags": {
                "invented_outcome": False,
                "invented_hidden_fact": False,
                "invented_intent": False,
                "overcertain_unresolved_action": False,
            },
            "debug": {"reason": "contract_disabled"},
        }

    raw = str(text or "")
    masked_full = _mask_dialogue_spans(raw)
    norm_full = _normalize_authority_text(raw)
    matched_deferral = _detect_deferral_mode(masked_full)

    forbid_outcome = bool(contract.get("forbid_unresolved_outcome_assertions"))
    forbid_hidden = bool(contract.get("forbid_hidden_fact_assertions"))
    forbid_intent = bool(contract.get("forbid_npc_intent_assertions_without_basis"))
    player_seeks_read = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(
        _clean_str((resolution or {}).get("prompt")) if isinstance(resolution, Mapping) else None
    )

    invented_outcome = False
    invented_hidden_fact = False
    invented_intent = False
    overcertain_unresolved_action = False

    if norm_full and forbid_outcome:
        for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = masked_full[start:end]
            if not msent.strip():
                continue
            if _sentence_has_hedge(sent):
                continue
            if _outcome_assertion_hits(sent, msent):
                invented_outcome = True
                overcertain_unresolved_action = True
                break

    if norm_full and forbid_hidden and not invented_outcome:
        for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = masked_full[start:end]
            if _sentence_has_hedge(sent):
                continue
            if _HIDDEN_FACT_CERTAINTY_RE.search(msent.lower()):
                invented_hidden_fact = True
                break

    if norm_full and forbid_intent:
        for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = masked_full[start:end]
            if player_seeks_read and _sentence_has_hedge(sent):
                continue
            if player_seeks_read and _ROLL_PROMPT_RE.search(msent):
                continue
            if _INTENT_CERTAINTY_RE.search(msent.lower()):
                if player_seeks_read and (
                    _sentence_has_hedge(sent) or _ROLL_PROMPT_RE.search(msent.lower())
                ):
                    continue
                invented_intent = True
                break

    failure_reasons: List[str] = []
    if invented_outcome:
        failure_reasons.append("unresolved_action")
    if invented_hidden_fact:
        failure_reasons.append("unknown_hidden_fact")
    if invented_intent:
        failure_reasons.append("unknown_intent")
    if overcertain_unresolved_action and "unresolved_action" not in failure_reasons:
        failure_reasons.append("insufficient_basis")

    passed = not (invented_outcome or invented_hidden_fact or invented_intent)

    # If narration already defers with an explicit roll prompt and every sentence either hedges
    # or prompts / branches, soften outcome findings (acceptance: "try the lock—give me a check").
    if not passed and invented_outcome and matched_deferral == "ask_for_roll":
        risky_sentence = False
        for _s, _e, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = _mask_dialogue_spans(sent)
            if _outcome_assertion_hits(sent, msent) and not _ROLL_PROMPT_RE.search(msent.lower()):
                risky_sentence = True
                break
        if not risky_sentence:
            invented_outcome = False
            overcertain_unresolved_action = False
            failure_reasons = [r for r in failure_reasons if r != "unresolved_action"]
            passed = not (invented_outcome or invented_hidden_fact or invented_intent)

    return {
        "checked": True,
        "passed": passed,
        "failure_reasons": failure_reasons,
        "matched_deferral_mode": matched_deferral,
        "assertion_flags": {
            "invented_outcome": bool(invented_outcome),
            "invented_hidden_fact": bool(invented_hidden_fact),
            "invented_intent": bool(invented_intent),
            "overcertain_unresolved_action": bool(overcertain_unresolved_action),
        },
        "debug": {
            "forbid_unresolved_outcome_assertions": forbid_outcome,
            "player_seeks_intent_read": player_seeks_read,
            "normalized_nonempty": bool(norm_full),
        },
    }


def narrative_authority_repair_hints(validation: Mapping[str, Any]) -> List[str]:
    """Minimal deterministic repair suggestions from a validation dict."""
    if not isinstance(validation, Mapping) or validation.get("passed") is True:
        return []
    hints: List[str] = []
    flags = validation.get("assertion_flags")
    if isinstance(flags, Mapping):
        if flags.get("invented_outcome"):
            hints.append("Replace settled outcome language with a roll prompt, conditional branches, or hedged uncertainty.")
        if flags.get("invented_hidden_fact"):
            hints.append("Frame backstage causality as uncertain ('could be', 'you can't tell yet') or ask for a check.")
        if flags.get("invented_intent"):
            hints.append("Prefer observable cues or bounded reads; avoid stating NPC plans/motives as fact unless grounded.")
    return hints
