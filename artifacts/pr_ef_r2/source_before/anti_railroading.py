"""Anti-railroading contract: player agency, optional framing, and lead surfacing (read-only).

Conservative, deterministic checks for narration that **decides for the player**, **collapses**
choices into one mandatory path without basis, or **upgrades surfaced leads** into required plot
gravity. Exceptions apply only from **resolved transitions**, **settled mechanical outcomes**,
**explicit player commitment** in turn text, or **published hard constraints** (world state) that
describe limits without dictating the player's next action.

This module does not mutate world state; it consumes published contract slices only.
"""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Vocab (inspectable)
# ---------------------------------------------------------------------------

ALLOWED_LEAD_ROLES: Tuple[str, ...] = (
    "option",
    "hook",
    "rumor",
    "pressure",
    "opportunity",
    "constraint",
)

FORBIDDEN_LEAD_ROLES: Tuple[str, ...] = (
    "destiny",
    "required_path",
    "main_plot",
    "only_real_way_forward",
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


def _resolved_transition(res: Mapping[str, Any]) -> bool:
    return bool(res.get("resolved_transition"))


# --- Detection (conservative; masked dialogue excluded) ---

_PLAYER_DECISION_OVERRIDE_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\byou\s+(?:decide|decides|deciding)\s+to\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\byou\s+(?:choose|chooses|choosing)\s+to\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\byou\s+can'?t\s+help\s+but\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\byou\s+find\s+yourself\s+going\b",
        re.IGNORECASE,
    ),
)

_FORCED_DIRECTION_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\byou\s+head\s+(?:for|toward|towards|to)\b", re.IGNORECASE),
    re.compile(r"\byou\s+head\s+straight\s+(?:for|toward|towards|to)\b", re.IGNORECASE),
    re.compile(r"\byou\s+make\s+your\s+way\s+(?:to|toward|towards)\b", re.IGNORECASE),
    re.compile(r"\byou\s+have\s+to\s+go\b", re.IGNORECASE),
    re.compile(r"\byou\s+must\s+go\b", re.IGNORECASE),
    re.compile(r"\bso\s+you\s+go\s+there\b", re.IGNORECASE),
)

# Post-transition arrival beats (allowed when transition is engine-resolved).
_ARRIVAL_AFTER_TRANSITION_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\byou\s+(?:arrive|arriving|arrived)\b", re.IGNORECASE),
    re.compile(r"\byou(?:'ve| have)\s+reached\b", re.IGNORECASE),
    re.compile(r"\byou\s+step\s+(?:into|through|onto)\b", re.IGNORECASE),
    re.compile(r"\byou\s+come\s+to\s+a\s+stop\b", re.IGNORECASE),
    re.compile(r"\byou\s+find\s+yourself\s+in\b", re.IGNORECASE),
)

_LEAD_PLOT_GRAVITY_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthe\s+real\s+lead\s+is\b", re.IGNORECASE),
    re.compile(r"\bthe\s+main\s+thing\s+now\s+is\b", re.IGNORECASE),
    re.compile(r"\byour\s+true\s+path\s+is\b", re.IGNORECASE),
    re.compile(r"\bthe\s+obvious\s+next\s+destination\s+is\b", re.IGNORECASE),
    re.compile(r"\bthe\s+story\s+(?:now\s+)?pulls\s+you\s+(?:toward|towards|to)\b", re.IGNORECASE),
    re.compile(r"\bthe\s+story\s+wants\s+you\s+to\s+go\b", re.IGNORECASE),
    re.compile(r"\beverything\s+points\s+to\s+only\s+one\s+place\b", re.IGNORECASE),
    re.compile(r"\bonly\s+real\s+lead\s+is\b", re.IGNORECASE),
)

_EXCLUSIVE_PATH_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthe\s+only\s+way\s+forward\s+is\b", re.IGNORECASE),
    re.compile(r"\bthere\s+is\s+no\s+choice\s+but\b", re.IGNORECASE),
    re.compile(r"\bit\s+becomes\s+clear\s+you\s+must\b", re.IGNORECASE),
    re.compile(r"\bnaturally,?\s+you\s+have\s+to\b", re.IGNORECASE),
    re.compile(r"\bthat\s+settles\s+it\b", re.IGNORECASE),
    re.compile(r"\bso\s+the\s+answer\s+is\s+clearly\b", re.IGNORECASE),
)

_FORCED_CONCLUSION_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthe\s+answer\s+is\s+obvious\b", re.IGNORECASE),
    re.compile(r"\bso\s+the\s+answer\s+is\s+obvious\b", re.IGNORECASE),
    re.compile(r"\bit\s+is\s+clear\s+you\s+must\b", re.IGNORECASE),
    re.compile(r"\bit(?:'s| is)\s+obvious\b.+\byou\s+must\b", re.IGNORECASE),
    re.compile(r"\byou\s+must\s+confront\b", re.IGNORECASE),
)

_MAIN_PLOT_RE = re.compile(
    r"\b(?:this\s+is\s+the\s+main\s+plot|the\s+main\s+plot\s+is)\b",
    re.IGNORECASE,
)

# Hard world constraints: stating the situation, not the player's next move.
_HARD_CONSTRAINT_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthe\s+bridge\s+is\s+out\b", re.IGNORECASE),
    re.compile(r"\bthe\s+gate\s+is\s+locked\b", re.IGNORECASE),
    re.compile(r"\bthe\s+door\s+is\s+barred\b", re.IGNORECASE),
    re.compile(r"\bno\s+other\s+(?:exit|way\s+out)\b", re.IGNORECASE),
)

_OPTION_FRAMING_OK_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bone\s+option\s+is\b", re.IGNORECASE),
    re.compile(r"\byou\s+could\b", re.IGNORECASE),
    re.compile(r"\byou\s+might\b", re.IGNORECASE),
    re.compile(r"\bif\s+you\s+want\b", re.IGNORECASE),
    re.compile(r"\balternatively\b", re.IGNORECASE),
    re.compile(r"\banother\s+(?:path|angle|lead|approach)\b", re.IGNORECASE),
)

_PLAYER_COMMITMENT_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi'?ll\s+(?:go|head|walk|run|follow)\b", re.IGNORECASE),
    re.compile(r"\bi\s+will\s+(?:go|head|walk|run|follow)\b", re.IGNORECASE),
    re.compile(r"\bi\s+am\s+going\s+to\b", re.IGNORECASE),
    re.compile(r"\bi\s+choose\s+to\s+follow\b", re.IGNORECASE),
    re.compile(r"\bwe\s+should\s+(?:go|head)\b", re.IGNORECASE),
    re.compile(r"\bi'?ll\s+follow\b", re.IGNORECASE),
)

_PLAYER_MOVEMENT_INTENT_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:go|head|walk|run|follow|enter|confront|meet|seek|find|visit|approach|track)\b",
        re.IGNORECASE,
    ),
)


def _player_explicit_commitment(player_text: str) -> bool:
    low = _normalize_scan_text(player_text)
    if not low:
        return False
    return any(p.search(low) for p in _PLAYER_COMMITMENT_RES)


def _player_movement_intent(player_text: str) -> bool:
    low = _normalize_scan_text(player_text)
    if not low:
        return False
    return any(p.search(low) for p in _PLAYER_MOVEMENT_INTENT_RES)


def _sentence_hits_any(sentence: str, patterns: Sequence[re.Pattern[str]]) -> bool:
    low = sentence.lower()
    return any(p.search(low) for p in patterns)


def _sentence_is_hard_constraint_only(sentence: str) -> bool:
    low = sentence.lower()
    if not any(p.search(low) for p in _HARD_CONSTRAINT_RES):
        return False
    # If the same sentence also seizes agency or mandates action, do not treat as constraint-only.
    if re.search(r"\byou\s+must\b", low) or re.search(r"\byou\s+have\s+to\b", low):
        return False
    if any(p.search(low) for p in _PLAYER_DECISION_OVERRIDE_RES):
        return False
    if any(p.search(low) for p in _EXCLUSIVE_PATH_RES):
        return False
    if any(p.search(low) for p in _FORCED_CONCLUSION_RES):
        return False
    if _MAIN_PLOT_RE.search(low):
        return False
    if any(p.search(low) for p in _LEAD_PLOT_GRAVITY_RES):
        return False
    return True


def _collect_obligation_hints(nob: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "must_advance_scene": bool(nob.get("must_advance_scene")),
        "scene_momentum_due": bool(nob.get("scene_momentum_due")),
        "is_opening_scene": bool(nob.get("is_opening_scene")),
    }


def _ingest_lead_row(row: Any, ids: List[str], labels: List[str]) -> None:
    if not isinstance(row, Mapping):
        return
    lid = row.get("id") or row.get("lead_id")
    if lid is not None:
        s = str(lid).strip()
        if s:
            ids.append(s)
    for key in ("title", "label", "name", "short_label"):
        v = row.get(key)
        if isinstance(v, str) and v.strip():
            labels.append(v.strip())
            break


def _dedupe_preserve(items: Sequence[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        low = item.strip().lower()
        if not low or low in seen:
            continue
        seen.add(low)
        out.append(item.strip())
    return out


def _collect_surfaced_leads(
    *,
    prompt_leads: Any,
    active_pending_leads: Any,
    session_view: Mapping[str, Any],
    follow_surface: Any,
) -> Tuple[List[str], List[str]]:
    ids: List[str] = []
    labels: List[str] = []

    def walk(bucket: Any) -> None:
        if isinstance(bucket, list):
            for item in bucket:
                _ingest_lead_row(item, ids, labels)
        elif isinstance(bucket, Mapping):
            for v in bucket.values():
                if isinstance(v, Mapping):
                    _ingest_lead_row(v, ids, labels)
                elif isinstance(v, list):
                    walk(v)

    walk(prompt_leads)
    walk(active_pending_leads)

    for key in ("surfaced_leads", "prompt_leads", "active_pending_leads", "leads_for_prompt"):
        walk(session_view.get(key))

    if isinstance(follow_surface, Mapping):
        for key in ("lead_ids", "ids", "surfaced_lead_ids"):
            raw = follow_surface.get(key)
            if isinstance(raw, list):
                for x in raw:
                    if x is not None and str(x).strip():
                        ids.append(str(x).strip())
        for key in ("labels", "titles", "surfaced_lead_labels"):
            raw = follow_surface.get(key)
            if isinstance(raw, list):
                for x in raw:
                    if isinstance(x, str) and x.strip():
                        labels.append(x.strip())

    return _dedupe_preserve(ids), _dedupe_preserve(labels)


def _lead_turned_mandatory_destination(sentence: str, labels: Sequence[str]) -> bool:
    if not labels:
        return False
    low = sentence.lower()
    mandatory = bool(
        re.search(
            r"\b(?:only\s+(?:real\s+)?option|not\s+optional|no\s+choice|must\s+go|"
            r"have\s+to\s+go|required\s+destination|you\s+are\s+going|you'?re\s+going)\b",
            low,
        )
    )
    if not mandatory:
        return False
    for lab in labels:
        fragment = _normalize_scan_text(lab)
        if len(fragment) >= 3 and fragment in low:
            return True
    return False


def build_anti_railroading_contract(
    *,
    resolution: Mapping[str, Any] | None = None,
    narration_obligations: Mapping[str, Any] | None = None,
    session_view: Mapping[str, Any] | None = None,
    scene_state_anchor_contract: Mapping[str, Any] | None = None,
    speaker_selection_contract: Mapping[str, Any] | None = None,
    narrative_authority_contract: Mapping[str, Any] | None = None,
    prompt_leads: Any = None,
    active_pending_leads: Any = None,
    follow_surface: Any = None,
    player_text: str | None = None,
) -> Dict[str, Any]:
    """Assemble inspectable anti-railroading policy from published inputs (no mutation)."""
    res = _mapping_or_empty(resolution)
    nob = _mapping_or_empty(narration_obligations)
    sess = _mapping_or_empty(session_view)
    sac = _mapping_or_empty(scene_state_anchor_contract)
    sp = _mapping_or_empty(speaker_selection_contract)
    nac = _mapping_or_empty(narrative_authority_contract)

    surfaced_lead_ids, surfaced_lead_labels = _collect_surfaced_leads(
        prompt_leads=prompt_leads,
        active_pending_leads=active_pending_leads,
        session_view=sess,
        follow_surface=follow_surface,
    )

    transition_ok = _resolved_transition(res) if isinstance(resolution, Mapping) else False
    authoritative = _resolution_has_authoritative_outcome(res) if isinstance(resolution, Mapping) else False
    commitment = _player_explicit_commitment(_clean_str(player_text))

    obligation_hints = _collect_obligation_hints(nob)

    enabled = True
    forbid_player_decision_override = True
    forbid_forced_direction = True
    forbid_exclusive_path_claims_without_basis = True
    forbid_lead_to_plot_gravity_upgrade = True

    allow_directional_language_from_resolved_transition = transition_ok
    allow_exclusivity_from_authoritative_resolution = authoritative
    allow_commitment_language_when_player_explicitly_committed = commitment

    debug_flags = {
        "resolved_transition": transition_ok,
        "authoritative_resolution_outcome": authoritative,
        "player_commitment_detected": commitment,
        "surfaced_lead_count": len(surfaced_lead_ids),
        "scene_state_anchor_contract_present": bool(sac),
        "narrative_authority_contract_present": bool(nac),
        "speaker_contract_present": bool(sp),
    }
    debug_inputs: Dict[str, Any] = {
        "has_resolution": isinstance(resolution, Mapping),
        "has_narration_obligations": bool(nob),
        "has_session_view": bool(sess),
        "has_scene_state_anchor_contract": bool(sac),
        "has_speaker_selection_contract": bool(sp),
        "has_narrative_authority_contract": bool(nac),
        "has_prompt_leads": prompt_leads is not None,
        "has_active_pending_leads": active_pending_leads is not None,
        "has_follow_surface": follow_surface is not None,
        "player_text_nonempty": bool(_clean_str(player_text)),
        "obligation_hints": obligation_hints,
    }
    debug_reason = (
        f"anti_railroading: transition={transition_ok} authoritative={authoritative} "
        f"commitment={commitment} surfaced_leads={len(surfaced_lead_ids)}"
    )

    return {
        "enabled": enabled,
        "forbid_player_decision_override": forbid_player_decision_override,
        "forbid_forced_direction": forbid_forced_direction,
        "forbid_exclusive_path_claims_without_basis": forbid_exclusive_path_claims_without_basis,
        "forbid_lead_to_plot_gravity_upgrade": forbid_lead_to_plot_gravity_upgrade,
        "allow_directional_language_from_resolved_transition": allow_directional_language_from_resolved_transition,
        "allow_exclusivity_from_authoritative_resolution": allow_exclusivity_from_authoritative_resolution,
        "allow_commitment_language_when_player_explicitly_committed": allow_commitment_language_when_player_explicitly_committed,
        "surfaced_lead_ids": list(surfaced_lead_ids),
        "surfaced_lead_labels": list(surfaced_lead_labels),
        "allowed_lead_roles": list(ALLOWED_LEAD_ROLES),
        "forbidden_lead_roles": list(FORBIDDEN_LEAD_ROLES),
        "debug_reason": debug_reason,
        "debug_inputs": debug_inputs,
        "debug_flags": debug_flags,
    }


def validate_anti_railroading(
    text: str,
    contract: Mapping[str, Any],
    *,
    player_text: str | None = None,
    resolution: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate narration *text* against ``build_anti_railroading_contract`` output."""
    if not isinstance(contract, Mapping):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": ["invalid_contract"],
            "assertion_flags": {
                "player_decision_override": False,
                "forced_direction": False,
                "exclusive_path_claim": False,
                "lead_plot_gravity": False,
                "forced_conclusion": False,
            },
            "debug": {"reason": "invalid_contract"},
        }

    if not contract.get("enabled"):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "assertion_flags": {
                "player_decision_override": False,
                "forced_direction": False,
                "exclusive_path_claim": False,
                "lead_plot_gravity": False,
                "forced_conclusion": False,
            },
            "debug": {"reason": "contract_disabled"},
        }

    res_map = _mapping_or_empty(resolution)

    transition_ok = bool(contract.get("allow_directional_language_from_resolved_transition"))
    if _resolved_transition(res_map):
        transition_ok = True

    authoritative = bool(contract.get("allow_exclusivity_from_authoritative_resolution"))
    if _resolution_has_authoritative_outcome(res_map):
        authoritative = True

    allow_commit = bool(contract.get("allow_commitment_language_when_player_explicitly_committed"))
    pt = _clean_str(player_text)
    if pt:
        allow_commit = _player_explicit_commitment(pt)
    movement_intent = _player_movement_intent(pt) if pt else False

    surfaced_labels = contract.get("surfaced_lead_labels")
    if not isinstance(surfaced_labels, list):
        surfaced_labels = []
    label_strings = [str(x) for x in surfaced_labels if isinstance(x, str) and x.strip()]

    raw = str(text or "")
    masked_full = _mask_dialogue_spans(raw)

    flags = {
        "player_decision_override": False,
        "forced_direction": False,
        "exclusive_path_claim": False,
        "lead_plot_gravity": False,
        "forced_conclusion": False,
    }
    forced_direction_from_surfaced_lead = False

    for start, end, sent in _split_sentences(masked_full, raw):
        msent = masked_full[start:end]
        if not msent.strip():
            continue
        low = msent.lower()

        if _sentence_is_hard_constraint_only(sent):
            continue

        if any(p.search(low) for p in _PLAYER_DECISION_OVERRIDE_RES):
            flags["player_decision_override"] = True

        if any(p.search(low) for p in _FORCED_DIRECTION_RES):
            skip_fd = False
            if transition_ok and any(p.search(low) for p in _ARRIVAL_AFTER_TRANSITION_RES):
                skip_fd = True
            if allow_commit and movement_intent:
                skip_fd = True
            if not skip_fd:
                flags["forced_direction"] = True

        if any(p.search(low) for p in _LEAD_PLOT_GRAVITY_RES) or _MAIN_PLOT_RE.search(low):
            flags["lead_plot_gravity"] = True

        excl_hit = any(p.search(low) for p in _EXCLUSIVE_PATH_RES)
        if excl_hit and not authoritative:
            flags["exclusive_path_claim"] = True

        if any(p.search(low) for p in _FORCED_CONCLUSION_RES):
            flags["forced_conclusion"] = True

        if _lead_turned_mandatory_destination(sent, label_strings):
            flags["forced_direction"] = True
            flags["exclusive_path_claim"] = True
            forced_direction_from_surfaced_lead = True

    # Optional-framing rescue: "you could head to …" does not match _FORCED_DIRECTION_RES; if any
    # sentence matched forced direction but also offers explicit option framing, drop those hits.
    # (Narrow: if the full text has option framing and no mandatory patterns, clear forced_direction
    #  when every hit was in a sentence that also contains option framing.)
    if flags["forced_direction"] and not flags["player_decision_override"]:
        fd_still = False
        for start, end, sent in _split_sentences(masked_full, raw):
            msent = masked_full[start:end]
            low = msent.lower()
            if not msent.strip() or _sentence_is_hard_constraint_only(sent):
                continue
            if not any(p.search(low) for p in _FORCED_DIRECTION_RES):
                continue
            if transition_ok and any(p.search(low) for p in _ARRIVAL_AFTER_TRANSITION_RES):
                continue
            if allow_commit and movement_intent:
                continue
            if _sentence_hits_any(sent, _OPTION_FRAMING_OK_RES):
                continue
            fd_still = True
            break
        if not fd_still and not forced_direction_from_surfaced_lead:
            flags["forced_direction"] = False

    failure_reasons: List[str] = []
    if flags["player_decision_override"]:
        failure_reasons.append("player_decision_override")
    if flags["forced_direction"]:
        failure_reasons.append("forced_direction")
    if flags["exclusive_path_claim"]:
        failure_reasons.append("exclusive_path_claim")
    if flags["lead_plot_gravity"]:
        failure_reasons.append("lead_plot_gravity")
    if flags["forced_conclusion"]:
        failure_reasons.append("forced_conclusion")

    passed = not failure_reasons

    return {
        "checked": True,
        "passed": passed,
        "failure_reasons": list(dict.fromkeys(failure_reasons)),
        "assertion_flags": {k: bool(v) for k, v in flags.items()},
        "debug": {
            "allow_directional_language_from_resolved_transition": transition_ok,
            "allow_exclusivity_from_authoritative_resolution": authoritative,
            "allow_commitment_language_when_player_explicitly_committed": allow_commit,
            "movement_intent_in_player_text": movement_intent,
            "normalized_nonempty": bool(_normalize_scan_text(raw)),
        },
    }


def anti_railroading_repair_hints(validation: Mapping[str, Any]) -> List[str]:
    """Narrow deterministic repair suggestions from a validation dict."""
    if not isinstance(validation, Mapping) or validation.get("passed") is True:
        return []
    if validation.get("checked") is False:
        return []
    af = validation.get("assertion_flags")
    if not isinstance(af, Mapping):
        return []
    hints: List[str] = []
    if af.get("player_decision_override"):
        hints.append(
            "Replace decided-for-the-player phrasing with visible cues and explicit options "
            "(e.g. 'You could…', 'If you pursue…') rather than 'You decide to…'."
        )
    if af.get("forced_direction"):
        hints.append(
            "Reframe mandatory destinations as optional leads or pressures; keep movement in the player's voice "
            "unless a transition is engine-resolved or the player explicitly committed."
        )
    if af.get("exclusive_path_claim"):
        hints.append(
            "Swap 'only way / no choice' for bounded constraints plus any known alternatives; "
            "if truly exclusive, ground it in authoritative resolution or published hard constraints."
        )
    if af.get("lead_plot_gravity"):
        hints.append(
            "Present surfaced leads as hooks, rumors, or pressures—not destiny, main plot, or the 'real' path."
        )
    if af.get("forced_conclusion"):
        hints.append(
            "Replace forced conclusions with open prompts or a short menu of interpretations the table can choose."
        )
    return hints
