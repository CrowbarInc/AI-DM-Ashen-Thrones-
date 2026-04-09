"""Deterministic guard: block planner / UI / coaching scaffold leaks in player-facing narration.

Conservative detectors (prefer false negatives over false positives) with strong coverage for
common internal-recovery phrases. Dialogue spans are masked so in-world quoted commands are not
flagged. Explicit non-diegetic engine modes (OC, adjudication, etc.) skip this layer when
configured via contract ``interaction_kind``.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

# Modes where narration may legitimately be non-diegetic (OC blocks, adjudication text, etc.).
_NON_DIEGETIC_INTERACTION_KINDS: frozenset[str] = frozenset(
    {
        "oc",
        "ooc",
        "adjudication",
        "adjudicate",
        "meta",
        "system",
        "gm_note",
        "gm_ooc",
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


def _mask_dialogue_spans(text: str) -> str:
    if not text:
        return ""
    masked = list(text)
    for pattern in _DIALOGUE_SPAN_PATTERNS:
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                masked[index] = " "
    return "".join(masked)


def _lower_compact(text: str) -> str:
    return " ".join(text.lower().split())


# --- Scaffold headers (full text; line-structured labels are not plausible in-world prose) ---

_SCAFFOLD_HEADER_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"consequence\s*/\s*opportunity\s*:", re.IGNORECASE),
    re.compile(r"\bnext\s+beat\s*:", re.IGNORECASE),
    re.compile(r"\bcommit\s+to\s+one\s+concrete\s+move\b", re.IGNORECASE),
)

_OPTIONS_HEADER_RE = re.compile(r"(?m)^\s*options\s*:\s*(\n|$)", re.IGNORECASE)


# --- Coaching / prompting (masked narration) ---

_COACHING_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\byou\s+weigh\s+what\s+you\s+just\s+tried\b", re.IGNORECASE),
    re.compile(r"\bhold\s+still\s+and\s+listen\s+hard\b", re.IGNORECASE),
    # Menu-like coaching, not "choose one path" in ordinary prose.
    re.compile(r"(?m)^\s*choose\s+one\b", re.IGNORECASE),
    re.compile(r"\bchoose\s+one\s+(?:of|from)\b", re.IGNORECASE),
)

_NON_DIEGETIC_PROMPT_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bread\s+the\s+notice\s+board\s+closely\s+for\b", re.IGNORECASE),
)


# --- Engine / meta transition bridges ---

_ENGINE_TRANSITION_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthe\s+next\s+beat\s+is\s+yours\b", re.IGNORECASE),
    re.compile(r"\bnext\s+beat\s+is\s+yours\b", re.IGNORECASE),
)


# --- UI / choice-label phrasing ---

_UI_CHOICE_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bexit\s+labeled\b", re.IGNORECASE),
    re.compile(r"\btake\s+the\s+exit\s+labeled\b", re.IGNORECASE),
    re.compile(r"\bclick\s+(?:here|the|on|to)\b", re.IGNORECASE),
    re.compile(r"\bselect\s+(?:the|this|an\s+option)\b", re.IGNORECASE),
)


# --- Engine choice framing (masked) ---

_ENGINE_CHOICE_FRAMING_RES: Tuple[re.Pattern[str], ...] = (
    re.compile(r"\bpick\s+(?:an\s+)?option\b", re.IGNORECASE),
    re.compile(r"\byour\s+options\s+(?:are|include)\b", re.IGNORECASE),
)


# --- Line-leading coaching imperatives (masked) ---

_LINE_START_MOVE_TOWARD = re.compile(r"(?m)^\s*move\s+towards?\b", re.IGNORECASE)


def _menu_like_option_list(text: str) -> bool:
    """Two or more short bullet/numbered lines typical of surfaced menu options."""
    lines = text.splitlines()
    bullets = 0
    numbered = 0
    for line in lines:
        s = line.strip()
        if re.match(r"^[-*•]\s+\S", s):
            bullets += 1
        elif re.match(r"^\d+\.\s+\S", s):
            numbered += 1
    return bullets >= 2 or numbered >= 2


def build_player_facing_narration_purity_contract(
    *,
    enabled: bool = True,
    diegetic_only: bool = True,
    allow_structured_choice_labels: bool = False,
    allow_explicit_ui_references: bool = False,
    allow_meta_transition_bridges: bool = False,
    forbid_scaffold_headers: bool = True,
    forbid_coaching_language: bool = True,
    forbid_engine_choice_framing: bool = True,
    forbid_non_diegetic_action_prompting: bool = True,
    response_type_required: str | None = None,
    interaction_kind: str | None = None,
    debug_inputs: Mapping[str, Any] | None = None,
    debug_reason: str | None = None,
) -> Dict[str, Any]:
    """Assemble inspectable narration-purity policy (deterministic, no world mutation)."""
    ik = _clean_str(interaction_kind).lower() or None
    rtr = _clean_str(response_type_required) if response_type_required is not None else ""
    di: Dict[str, Any] = {}
    if isinstance(debug_inputs, Mapping):
        di = {str(k): v for k, v in debug_inputs.items()}
    dr = _clean_str(debug_reason) if debug_reason else "player_facing_narration_purity: default_strict_diegetic"
    return {
        "enabled": bool(enabled),
        "diegetic_only": bool(diegetic_only),
        "allow_structured_choice_labels": bool(allow_structured_choice_labels),
        "allow_explicit_ui_references": bool(allow_explicit_ui_references),
        "allow_meta_transition_bridges": bool(allow_meta_transition_bridges),
        "forbid_scaffold_headers": bool(forbid_scaffold_headers),
        "forbid_coaching_language": bool(forbid_coaching_language),
        "forbid_engine_choice_framing": bool(forbid_engine_choice_framing),
        "forbid_non_diegetic_action_prompting": bool(forbid_non_diegetic_action_prompting),
        "response_type_required": rtr or None,
        "interaction_kind": ik,
        "debug_inputs": di,
        "debug_reason": dr,
    }


def _empty_flags() -> Dict[str, bool]:
    return {
        "scaffold_header_leak": False,
        "coaching_language_leak": False,
        "ui_choice_label_leak": False,
        "non_diegetic_prompting_leak": False,
        "engine_transition_scaffold_leak": False,
    }


def validate_player_facing_narration_purity(
    text: str,
    contract: Mapping[str, Any] | None,
    *,
    player_text: str = "",
    resolution: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate narration *text* against ``build_player_facing_narration_purity_contract`` output."""
    _ = _clean_str(player_text)

    if not isinstance(contract, Mapping):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": ["invalid_contract"],
            "violations": ["invalid_contract"],
            "assertion_flags": _empty_flags(),
            "debug": {"reason": "invalid_contract"},
        }

    if not contract.get("enabled", True):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "violations": [],
            "assertion_flags": _empty_flags(),
            "debug": {"reason": "contract_disabled"},
        }

    ik = _clean_str(contract.get("interaction_kind")).lower()
    if ik and ik in _NON_DIEGETIC_INTERACTION_KINDS:
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "violations": [],
            "assertion_flags": _empty_flags(),
            "debug": {"reason": "non_diegetic_interaction_kind", "interaction_kind": ik},
        }

    if not contract.get("diegetic_only", True):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "violations": [],
            "assertion_flags": _empty_flags(),
            "debug": {"reason": "diegetic_only_disabled"},
        }

    raw = str(text or "")
    flags = _empty_flags()

    allow_labels = bool(contract.get("allow_structured_choice_labels"))
    allow_ui = bool(contract.get("allow_explicit_ui_references"))
    allow_meta = bool(contract.get("allow_meta_transition_bridges"))

    scan_full = raw
    scan_masked = _mask_dialogue_spans(raw)

    if contract.get("forbid_scaffold_headers", True):
        for pattern in _SCAFFOLD_HEADER_PATTERNS:
            if pattern.search(scan_full):
                flags["scaffold_header_leak"] = True
                break
        if not flags["scaffold_header_leak"] and not allow_labels and _OPTIONS_HEADER_RE.search(scan_full):
            flags["scaffold_header_leak"] = True

    if contract.get("forbid_coaching_language", True):
        for pattern in _COACHING_PATTERNS:
            if pattern.search(scan_masked):
                flags["coaching_language_leak"] = True
                break

    if not allow_meta and contract.get("forbid_coaching_language", True):
        for pattern in _ENGINE_TRANSITION_RES:
            if pattern.search(scan_masked) or pattern.search(scan_full):
                flags["engine_transition_scaffold_leak"] = True
                break

    if not allow_ui and contract.get("forbid_non_diegetic_action_prompting", True):
        for pattern in _UI_CHOICE_RES:
            if pattern.search(scan_masked) or pattern.search(scan_full):
                flags["ui_choice_label_leak"] = True
                break

    if contract.get("forbid_engine_choice_framing", True) and not allow_labels:
        for pattern in _ENGINE_CHOICE_FRAMING_RES:
            if pattern.search(scan_masked):
                flags["non_diegetic_prompting_leak"] = True
                break

    if contract.get("forbid_non_diegetic_action_prompting", True):
        for pattern in _NON_DIEGETIC_PROMPT_PATTERNS:
            if pattern.search(scan_masked):
                flags["non_diegetic_prompting_leak"] = True
                break
        if not allow_labels and _LINE_START_MOVE_TOWARD.search(scan_masked):
            flags["non_diegetic_prompting_leak"] = True
        if not allow_labels and _menu_like_option_list(raw):
            flags["non_diegetic_prompting_leak"] = True

    failure_reasons: List[str] = []
    for k, v in flags.items():
        if v:
            failure_reasons.append(k)

    passed = not failure_reasons

    return {
        "checked": True,
        "passed": passed,
        "failure_reasons": list(dict.fromkeys(failure_reasons)),
        "violations": list(dict.fromkeys(failure_reasons)),
        "assertion_flags": {k: bool(v) for k, v in flags.items()},
        "debug": {
            "response_type_required": _clean_str(contract.get("response_type_required")) or None,
            "has_resolution": isinstance(resolution, Mapping),
            "normalized_nonempty": bool(_lower_compact(raw)),
            "reason": "scanned",
        },
    }


def _simple_sentence_split(text: str) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    parts = re.split(r"(?<=[.!?])\s+", raw)
    return [p.strip() for p in parts if p.strip()]


def _strip_lines_matching_any(text: str, patterns: Sequence[re.Pattern[str]]) -> str:
    """Drop lines containing a pattern match (scaffold headers, option blocks)."""
    lines = str(text or "").splitlines()
    kept: List[str] = []
    for line in lines:
        if any(p.search(line) for p in patterns):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _strip_inline_patterns(text: str, patterns: Sequence[re.Pattern[str]], *, masked: str) -> str:
    """Remove pattern spans; use *masked* only to decide matches (dialogue preserved)."""
    t = str(text or "")
    m = masked
    if len(m) != len(t):
        m = _mask_dialogue_spans(t)
    out = list(t)
    for pat in patterns:
        for match in pat.finditer(m):
            start, end = match.span()
            for i in range(start, end):
                if i < len(out):
                    out[i] = " "
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()


def _strip_scaffold_header_spans(text: str) -> Tuple[str, bool]:
    """Remove scaffold labels even when the same line continues with diegetic prose (whitespace-normalized gate text)."""
    t = str(text or "")
    changed = False
    for pattern in _SCAFFOLD_HEADER_PATTERNS:
        m = pattern.search(t)
        while m:
            t = (t[: m.start()] + t[m.end() :]).strip()
            changed = True
            m = pattern.search(t)
    return t, changed


def minimal_repair_player_facing_narration_purity(
    text: str,
    contract: Mapping[str, Any] | None,
) -> Tuple[str, Dict[str, Any]]:
    """Strip planner/UI/coaching leaks; optionally collapse to the longest passing suffix (no new facts)."""
    modes: List[str] = []
    raw = str(text or "")
    v0 = validate_player_facing_narration_purity(raw, contract)
    if not v0.get("checked") or v0.get("passed"):
        return raw, {
            "repaired": False,
            "collapsed_to_core": False,
            "modes": [],
            "still_failing": False,
            "post_validation": v0,
        }

    allow_labels = bool(contract and contract.get("allow_structured_choice_labels"))
    allow_ui = bool(contract and contract.get("allow_explicit_ui_references"))
    allow_meta = bool(contract and contract.get("allow_meta_transition_bridges"))

    t = raw
    t0, span_hit = _strip_scaffold_header_spans(t)
    if span_hit:
        modes.append("strip_scaffold_header_spans")
        t = t0

    header_line_patterns: List[re.Pattern[str]] = list(_SCAFFOLD_HEADER_PATTERNS)
    if not allow_labels:
        header_line_patterns.append(_OPTIONS_HEADER_RE)

    t2 = _strip_lines_matching_any(t, tuple(header_line_patterns))
    if t2 != t:
        modes.append("strip_scaffold_header_lines")
        t = t2

    masked = _mask_dialogue_spans(t)
    inline_sets: List[re.Pattern[str]] = []
    if contract and contract.get("forbid_coaching_language", True):
        inline_sets.extend(_COACHING_PATTERNS)
    if not allow_meta and contract and contract.get("forbid_coaching_language", True):
        inline_sets.extend(_ENGINE_TRANSITION_RES)
    if not allow_ui and contract and contract.get("forbid_non_diegetic_action_prompting", True):
        inline_sets.extend(_UI_CHOICE_RES)
    if contract and contract.get("forbid_engine_choice_framing", True) and not allow_labels:
        inline_sets.extend(_ENGINE_CHOICE_FRAMING_RES)
    if contract and contract.get("forbid_non_diegetic_action_prompting", True):
        inline_sets.extend(_NON_DIEGETIC_PROMPT_PATTERNS)
        if not allow_labels and _LINE_START_MOVE_TOWARD.search(masked):
            t = _strip_inline_patterns(t, (_LINE_START_MOVE_TOWARD,), masked=masked)
            modes.append("strip_line_start_move_toward")
            masked = _mask_dialogue_spans(t)

    if inline_sets:
        t3 = _strip_inline_patterns(t, tuple(inline_sets), masked=masked)
        if t3 != t:
            modes.append("strip_coaching_ui_meta_spans")
            t = t3

    if contract and contract.get("forbid_non_diegetic_action_prompting", True) and not allow_labels:
        if _menu_like_option_list(t):
            lines = [ln for ln in t.splitlines() if not re.match(r"^\s*(?:[-*•]|\d+\.)\s+\S", ln.strip())]
            t4 = "\n".join(lines).strip()
            if t4 != t:
                modes.append("strip_menu_like_option_lines")
                t = t4

    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    v1 = validate_player_facing_narration_purity(t, contract)
    if v1.get("passed"):
        return t, {
            "repaired": bool(modes),
            "collapsed_to_core": False,
            "modes": modes,
            "still_failing": False,
            "post_validation": v1,
        }

    sents = _simple_sentence_split(t)
    for i in range(len(sents)):
        suffix = " ".join(sents[i:]).strip()
        if not suffix:
            continue
        v = validate_player_facing_narration_purity(suffix, contract)
        if v.get("passed"):
            collapsed = i > 0 or bool(modes)
            m2 = list(modes)
            if i > 0:
                m2.append("collapse_to_passing_suffix")
            return suffix, {
                "repaired": True,
                "collapsed_to_core": i > 0,
                "modes": m2,
                "still_failing": False,
                "post_validation": v,
            }

    return t, {
        "repaired": bool(modes),
        "collapsed_to_core": False,
        "modes": modes,
        "still_failing": not bool(v1.get("passed")),
        "post_validation": v1,
    }


def player_facing_narration_purity_repair_hints(
    violations: Sequence[str],
    contract: Mapping[str, Any] | None = None,
) -> List[str]:
    """Minimal composable repair lines from machine-readable violation keys."""
    _ = contract
    hints: List[str] = []
    vset = {str(x) for x in violations if isinstance(x, str) and x.strip()}

    if "invalid_contract" in vset:
        hints.append("Provide a valid narration purity contract mapping from build_player_facing_narration_purity_contract.")
    if "scaffold_header_leak" in vset:
        hints.append("Remove labeled scaffold headers (e.g. consequence/opportunity, options); fold cues into diegetic prose.")
    if "coaching_language_leak" in vset:
        hints.append("Drop direct coaching; show pressure, stakes, and sensory detail in-world instead of instructing the player.")
    if "ui_choice_label_leak" in vset:
        hints.append("Replace UI or menu labels with visible scene affordances (doors, signs, NPC gestures) without 'exit labeled' phrasing.")
    if "non_diegetic_prompting_leak" in vset:
        hints.append(
            "Convert menu-like prompts and imperative option lists into in-world consequences, obstacles, or ambient hooks—keep agency implicit."
        )
    if "engine_transition_scaffold_leak" in vset:
        hints.append("Remove meta transition lines ('next beat'); use a concrete narrative handoff or sensory beat instead.")

    if not hints and vset:
        hints.append("Rewrite as third-person present diegetic narration with no planner or UI leakage.")

    return hints
