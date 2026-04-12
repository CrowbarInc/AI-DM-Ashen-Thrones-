"""Narrative authenticity contract: prompt + gate policy for anti-echo, signal density, and diegetic shape.

Orthogonal to ``response_delta`` / ``answer_completeness`` but may read their shipped traces on
``response_policy`` for inspection and light coordination (no duplication of their repair paths).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence

from game.final_emission_text import _normalize_terminal_punctuation, _normalize_text

NARRATIVE_AUTHENTICITY_VERSION = 1

# Tokens often legitimately repeated across adjacent clauses (continuity / geography / roles).
_CONTINUITY_LEXEMES: frozenset[str] = frozenset(
    {
        "east",
        "west",
        "north",
        "south",
        "gate",
        "road",
        "lane",
        "market",
        "square",
        "harbor",
        "dock",
        "yard",
        "watch",
        "guard",
        "guards",
        "clerk",
        "captain",
        "sergeant",
        "ledger",
        "patrol",
        "patrols",
        "curfew",
        "fold",
        "mill",
        "pier",
        "checkpoint",
        "barracks",
        "watchhouse",
        "counting",
        "room",
        "wharf",
        "quay",
    }
)

# Whole-line / dominant-response padding (matched for evidence, not sole signal).
_GENERIC_FILLER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "considers_words",
        re.compile(
            r"\b(?:considers?|weighs?)\s+(?:your|the)\s+words\b|\bstud(?:y|ies)\s+you\b|\bholds?\s+your\s+gaze\b",
            re.IGNORECASE,
        ),
    ),
    (
        "pause_beat",
        re.compile(
            r"\b(?:pauses?|hesitates?|lets?\s+the\s+silence|waits?\s+a\s+beat|for\s+a\s+breath|for\s+a\s+moment)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "atmospheric_only",
        re.compile(
            r"^(?:the\s+)?(?:mist|rain|dusk|dawn|torchlight|crowd|air|wind|bells?)\b[^.?!]{0,120}\.$",
            re.IGNORECASE,
        ),
    ),
    (
        "weak_uncertainty_shell",
        re.compile(
            r"\b(?:hard\s+to\s+say|difficult\s+to\s+say|tough\s+to\s+say|who\s+can\s+say|"
            r"anyone'?s\s+guess|your\s+guess\s+is\s+as\s+good)\b(?![^?.!]{0,80}\b(?:but|though|still|yet|only|except)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "noncommittal_hedge",
        re.compile(
            r"\b(?:perhaps|maybe|possibly|might\s+be|could\s+be)\b(?![^?.!]{0,96}\b(?:because|since|if\s+you|"
            r"what\s+i|the\s+ledger|the\s+gate|east|west|north|south|patrol|captain|clerk)\b)",
            re.IGNORECASE,
        ),
    ),
)

_FOLLOWUP_REACTION_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:snaps|snarls|sighs|laughs|smiles|frowns|grimaces|pales|tenses|softens|relents)\b", re.IGNORECASE),
    re.compile(r"\b(?:voice|tone)\s+(?:drops|sharpens|tightens|warms|cools)\b", re.IGNORECASE),
    re.compile(r"\b(?:leans?|steps?|shifts?|turns?)\s+(?:closer|away|aside)\b", re.IGNORECASE),
)

_FOLLOWUP_PERSPECTIVE_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:from\s+(?:my|our)\s+angle|on\s+my\s+watch|in\s+my\s+line)\b", re.IGNORECASE),
    re.compile(r"\b(?:what\s+you|what\s+we)\s+(?:need|should|ought)\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+real|the\s+honest)\s+(?:answer|truth)\b", re.IGNORECASE),
)

_FOLLOWUP_NARROW_UNCERTAINTY_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:what\s+i\s+can\s+say|one\s+thing\s+is\s+clear|the\s+part\s+i\s+know)\b", re.IGNORECASE),
    re.compile(r"\b(?:can'?t\s+pin|can'?t\s+swear|not\s+certain\s+whether)\b", re.IGNORECASE),
    re.compile(r"\b(?:if\s+you\s+mean|depending\s+whether)\b", re.IGNORECASE),
)

_REFUSAL_BOUNDARY_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:won'?t|will\s+not|refuse|can'?t)\s+(?:say|tell|speak)\b", re.IGNORECASE),
    re.compile(r"\b(?:not\s+(?:at\s+liberty|here|now)|end\s+of\s+that|that\s+line\s+is\s+closed)\b", re.IGNORECASE),
)

_RHETORICAL_FRAME_RE = re.compile(
    r"^(?:for\s+a\s+(?:moment|breath)|in\s+the\s+(?:same|next)\s+breath|after\s+a\s+beat|"
    r"for\s+now|at\s+least|if\s+you\s+want\s+the\s+truth)\b",
    re.IGNORECASE,
)


def resolve_narrative_authenticity_contract(gm_output: Mapping[str, Any] | None) -> Dict[str, Any] | None:
    """Return ``response_policy.narrative_authenticity`` when present."""
    if not isinstance(gm_output, Mapping):
        return None
    pol = gm_output.get("response_policy")
    if not isinstance(pol, Mapping):
        return None
    hit = pol.get("narrative_authenticity")
    return dict(hit) if isinstance(hit, Mapping) else None


_NA_TOKEN_RE = re.compile(r"[a-z']{4,}")
_NA_STOPWORDS: frozenset[str] = frozenset(
    {
        "that",
        "this",
        "with",
        "from",
        "into",
        "about",
        "there",
        "here",
        "they",
        "them",
        "their",
        "then",
        "than",
        "have",
        "has",
        "had",
        "been",
        "were",
        "was",
        "are",
        "is",
        "not",
        "but",
        "and",
        "for",
        "the",
        "you",
        "your",
    }
)


def _na_tokens(text: str) -> List[str]:
    low = re.sub(r"[^a-z'\s]+", " ", str(text or "").lower())
    return [t for t in _NA_TOKEN_RE.findall(low) if t not in _NA_STOPWORDS]


def _token_jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = len(sa & sb)
    union = len(sa | sb)
    return float(inter) / float(union or 1)


def _quoted_spans(text: str) -> List[tuple[int, int, str]]:
    """Return (start, end, inner) for straight/curly double-quoted spans."""
    raw = str(text or "")
    out: List[tuple[int, int, str]] = []
    for m in re.finditer(r'["“]([^"”]{6,1200})["”]', raw):
        out.append((m.start(), m.end(), m.group(1).strip()))
    return out


def _prose_before_index(text: str, idx: int, *, window: int = 320) -> str:
    head = str(text or "")[: max(0, idx)]
    head = head.strip()
    if len(head) > window:
        head = head[-window:]
    return head


def _fourgram_overlap(s0: str, s1: str) -> bool:
    def grams(s: str) -> set[tuple[str, ...]]:
        words = [w.lower() for w in re.findall(r"[A-Za-z']+", s) if len(w) >= 2]
        return {tuple(words[i : i + 4]) for i in range(0, max(0, len(words) - 3))}

    g0, g1 = grams(s0), grams(s1)
    return bool(g0 & g1)


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z']+", str(text or "")))


def _ordered_trigrams(text: str) -> set[tuple[str, ...]]:
    w = [x.lower() for x in re.findall(r"[A-Za-z']+", str(text or "")) if len(x) >= 2]
    if len(w) < 3:
        return set()
    return {tuple(w[i : i + 3]) for i in range(0, len(w) - 2)}


def _trigram_jaccard(a: str, b: str) -> float:
    ga, gb = _ordered_trigrams(a), _ordered_trigrams(b)
    if not ga or not gb:
        return 0.0
    inter = len(ga & gb)
    union = len(ga | gb)
    return float(inter) / float(union or 1)


def _collapse_ws(s: str) -> str:
    return " ".join(str(s or "").lower().split())


def _quote_echoes_prose_substring(prose: str, inner: str) -> bool:
    p = _collapse_ws(prose)
    inn = _collapse_ws(inner)
    if len(inn) < 22:
        return False
    return inn in p


def _opener_stem_words(sentence: str, *, max_words: int = 6) -> tuple[str, ...]:
    raw = [w for w in re.findall(r"[A-Za-z']+", str(sentence or ""))]
    if not raw:
        return ()
    i = 0
    while i < len(raw) and raw[i].lower() in ("the", "a", "an"):
        i += 1
    chunk = raw[i : i + max_words]
    return tuple(w.lower() for w in chunk)


def _scaffold_token_seq(sentence: str) -> List[str]:
    words = [w.lower() for w in re.findall(r"[A-Za-z']+", str(sentence or "")) if len(w) >= 2]
    return [w for w in words if w not in _CONTINUITY_LEXEMES and len(w) >= 3]


def _shared_scaffold_trigrams(a: str, b: str) -> List[str]:
    ta = _scaffold_token_seq(a)
    tb = _scaffold_token_seq(b)
    if len(ta) < 4 or len(tb) < 4:
        return []
    ga = {tuple(ta[i : i + 3]) for i in range(0, len(ta) - 2)}
    gb = {tuple(tb[i : i + 3]) for i in range(0, len(tb) - 2)}
    shared = ga & gb
    out: List[str] = []
    for g in sorted(shared)[:5]:
        out.append(" ".join(g))
    return out


def _scaffold_trigram_pressure(a: str, b: str) -> tuple[bool, float]:
    ta, tb = _scaffold_token_seq(a), _scaffold_token_seq(b)
    if len(ta) < 5 or len(tb) < 5:
        return False, 0.0
    ga = {tuple(ta[i : i + 3]) for i in range(0, len(ta) - 2)}
    gb = {tuple(tb[i : i + 3]) for i in range(0, len(tb) - 2)}
    if not ga or not gb:
        return False, 0.0
    inter = len(ga & gb)
    denom = min(len(ga), len(gb))
    r = float(inter) / float(denom or 1)
    return (inter >= 2 and r >= 0.34), r


def _shared_rhetorical_framing(a: str, b: str) -> bool:
    sa = str(a or "").strip()
    sb = str(b or "").strip()
    if not _RHETORICAL_FRAME_RE.match(sa) or not _RHETORICAL_FRAME_RE.match(sb):
        return False
    wa = [w.lower() for w in re.findall(r"[A-Za-z']+", sa)[:5]]
    wb = [w.lower() for w in re.findall(r"[A-Za-z']+", sb)[:5]]
    if len(wa) < 3 or len(wb) < 3:
        return False
    return wa[:3] == wb[:3]


def _adjacent_pair_structural_reuse(a: str, b: str) -> tuple[bool, Dict[str, Any]]:
    """Structural reuse beyond continuity anchors; bounded deterministic heuristics."""
    detail: Dict[str, Any] = {"fourgram": False, "opener_stem": False, "scaffold": False, "framing": False}
    if _fourgram_overlap(a, b):
        detail["fourgram"] = True
        return True, detail
    sa, sb = _opener_stem_words(a), _opener_stem_words(b)
    if len(sa) >= 4 and len(sb) >= 4 and sa == sb:
        detail["opener_stem"] = True
        return True, detail
    sc_ok, _sc_r = _scaffold_trigram_pressure(a, b)
    if sc_ok:
        detail["scaffold"] = True
        return True, detail
    if _shared_rhetorical_framing(a, b):
        detail["framing"] = True
        return True, detail
    return False, detail


def _collect_filler_pattern_hits(text: str) -> List[str]:
    hits: List[str] = []
    for name, pat in _GENERIC_FILLER_PATTERNS:
        if pat.search(text):
            hits.append(name)
    return hits


def _unique_token_ratio(text: str) -> float:
    words = [w.lower() for w in re.findall(r"[A-Za-z']+", str(text or ""))]
    if not words:
        return 1.0
    return float(len(set(words))) / float(len(words))


def _generic_filler_score(
    text: str,
    *,
    generic_nonanswer_hit: bool,
    pattern_hits: Sequence[str],
) -> float:
    wc = _word_count(text)
    score = 0.0
    if generic_nonanswer_hit:
        score += 0.28
    score += min(0.55, 0.18 * len(pattern_hits))
    if wc and wc <= 16:
        ur = _unique_token_ratio(text)
        if ur <= 0.52:
            score += 0.22
        elif ur <= 0.62 and wc <= 12:
            score += 0.12
    if wc <= 10 and not ('"' in text or "“" in text):
        score += 0.08
    return min(1.0, score)


def _followup_signal_markers_count(text: str) -> int:
    n = 0
    groups = (
        _FOLLOWUP_REACTION_MARKERS,
        _FOLLOWUP_PERSPECTIVE_MARKERS,
        _FOLLOWUP_NARROW_UNCERTAINTY_MARKERS,
        _REFUSAL_BOUNDARY_MARKERS,
    )
    for grp in groups:
        for p in grp:
            if p.search(text):
                n += 1
                break
    return n


def _meaningful_followup_change_vs_prior(text: str, prior: str) -> bool:
    """Diegetic change signals vs prior snippet (non-``response_delta`` path); avoids forcing new facts."""
    if _followup_signal_markers_count(text):
        return True
    from game.final_emission_validators import _NEXT_LEAD_SNIPPET

    if _NEXT_LEAD_SNIPPET.search(text):
        return True
    if re.search(r"\b\d+\b", text):
        return True
    cur = [t for t in _na_tokens(text) if len(t) >= 5]
    prev = set(_na_tokens(prior))
    novel = [t for t in cur if t not in prev]
    if len(novel) >= 2:
        return True
    if any(len(t) >= 8 for t in novel):
        return True
    if "?" in text and "?" not in prior:
        return True
    return False


def _diegetic_signal_negative_control(text: str) -> bool:
    """Brief refusal / uncertainty / lead / quoted substance should not read as generic filler."""
    from game.final_emission_validators import (
        _NEXT_LEAD_SNIPPET,
        _partial_reason_in_text,
    )

    if _NEXT_LEAD_SNIPPET.search(text):
        return True
    if _partial_reason_in_text(text, ["uncertainty", "lack_of_knowledge", "gated_information"]):
        return True
    for p in _REFUSAL_BOUNDARY_MARKERS:
        if p.search(text):
            return True
    for inner in (m.group(1) for m in re.finditer(r'["“]([^"”]{10,})["”]', str(text or ""))):
        if _word_count(inner) >= 5:
            return True
    return False


def build_narrative_authenticity_contract(
    *,
    response_delta: Mapping[str, Any] | None = None,
    answer_completeness: Mapping[str, Any] | None = None,
    fallback_behavior: Mapping[str, Any] | None = None,
    social_response_structure: Mapping[str, Any] | None = None,
    response_type_contract: Mapping[str, Any] | None = None,
    follow_up_pressure: Mapping[str, Any] | None = None,
    recent_log_compact: Sequence[Mapping[str, Any]] | None = None,
    player_text: str | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic shipped contract for prompts, gate validation, and telemetry."""
    rd = response_delta if isinstance(response_delta, Mapping) else {}
    ac = answer_completeness if isinstance(answer_completeness, Mapping) else {}
    fb = fallback_behavior if isinstance(fallback_behavior, Mapping) else {}
    srs = social_response_structure if isinstance(social_response_structure, Mapping) else {}
    rtc = response_type_contract if isinstance(response_type_contract, Mapping) else {}
    fup = follow_up_pressure if isinstance(follow_up_pressure, Mapping) else {}

    prior_gm = ""
    recent = list(recent_log_compact or [])
    if recent:
        last = recent[-1] if isinstance(recent[-1], Mapping) else {}
        prior_gm = str((last or {}).get("gm_snippet") or "").strip()[:360]

    topic_follow_up = bool(fup.get("pressed")) or bool(fup.get("from_leads"))
    rd_active = bool(rd.get("enabled")) and bool(rd.get("delta_required"))
    dialogue_expected = bool(srs.get("enabled")) or str(rtc.get("required_response_type") or "").strip().lower() == "dialogue"

    base: Dict[str, Any] = {
        "enabled": True,
        "version": NARRATIVE_AUTHENTICITY_VERSION,
        "mode": "advisory_prompt_with_gate_enforcement",
        "allow_restate_for_continuity": True,
        "max_anchor_reuse_clauses": 1,
        "forbid_scene_narration_echo_as_dialogue": True,
        "forbid_low_signal_generic_reply": True,
        "forbid_adjacent_phrase_reuse": True,
        "require_meaningful_change_on_followup": True,
        "signal_sources": [
            "new_information",
            "new_perspective",
            "new_reaction",
            "new_boundary_of_uncertainty",
            "new_actionable_next_step",
        ],
        "anti_goals": {
            "do_not_force_verbosity": True,
            "do_not_invent_facts": True,
            "do_not_override_fallback_correctness": True,
        },
        "fallback_compatibility": {
            "may_be_brief_under_uncertainty": True,
            "may_refuse_or_partially_answer_if_other_contracts_require": True,
            "brevity_alone_is_not_failure": True,
        },
        "trace": {
            "response_delta_contract_active": rd_active,
            "topic_follow_up_active": topic_follow_up,
            "answer_completeness_required": bool(ac.get("answer_required")),
            "dialogue_shape_expected": dialogue_expected,
            "prior_turn_gm_snippet_for_overlap": prior_gm or None,
            "player_text_len": len(str(player_text or "").strip()),
        },
    }
    if isinstance(overrides, Mapping):
        for k, v in overrides.items():
            if k in {"anti_goals", "fallback_compatibility", "trace"} and isinstance(v, Mapping) and isinstance(
                base.get(k), dict
            ):
                merged = dict(base[k])
                merged.update(dict(v))
                base[k] = merged
            else:
                base[str(k)] = v
    return base


def _slim_na_metrics(metrics: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(metrics, Mapping):
        return {}
    out: Dict[str, Any] = {}
    for k, v in metrics.items():
        if v is None:
            continue
        if isinstance(v, float):
            out[str(k)] = round(v, 4)
        elif isinstance(v, (int, str, bool)):
            out[str(k)] = v
    return out


def _slim_na_evidence(evidence: Mapping[str, Any] | None, *, max_str: int = 120, max_list: int = 6) -> Dict[str, Any]:
    if not isinstance(evidence, Mapping):
        return {}

    def clip(x: Any) -> Any:
        if isinstance(x, str) and len(x) > max_str:
            return x[: max(0, max_str - 1)] + "…"
        if isinstance(x, list):
            return [clip(i) for i in x[:max_list]]
        if isinstance(x, dict):
            return {str(k2): clip(v2) for k2, v2 in list(x.items())[:8]}
        return x

    return {str(k): clip(v) for k, v in evidence.items()}


def build_narrative_authenticity_emission_trace(validation: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact, stable fields for ``_final_emission_meta`` (failure, repair, or contract skip)."""
    if not isinstance(validation, Mapping):
        return {}
    out: Dict[str, Any] = {}
    sr = validation.get("skip_reason")
    if isinstance(sr, str) and sr.strip():
        out["narrative_authenticity_skip_reason"] = sr.strip()
    checked = bool(validation.get("checked"))
    passed = bool(validation.get("passed"))
    reasons = [str(x) for x in (validation.get("failure_reasons") or []) if str(x).strip()]
    if reasons:
        out["narrative_authenticity_reason_codes"] = reasons
    if checked and (reasons or not passed):
        out["narrative_authenticity_metrics"] = _slim_na_metrics(validation.get("metrics"))
        out["narrative_authenticity_evidence"] = _slim_na_evidence(validation.get("evidence"))
    return out


def inspect_narrative_authenticity_failure(result: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(result, Mapping) or result.get("passed") is not False:
        return {"failed": False}
    payload: Dict[str, Any] = {
        "failed": True,
        "ok": False,
        "reasons": list(result.get("failure_reasons") or []),
        "failure_reasons": list(result.get("failure_reasons") or []),
        "skip_reason": result.get("skip_reason"),
        "metrics": dict(result.get("metrics") or {}),
        "evidence": dict(result.get("evidence") or {}),
    }
    return payload


def validate_narrative_authenticity(
    emitted_text: str,
    contract: Mapping[str, Any] | None,
    *,
    gm_output: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic checks for ``response_policy.narrative_authenticity`` (no LLM)."""
    from game.final_emission_validators import (
        _GENERIC_NONANSWER_SNIPPET,
        _contains_meta_fallback_voice,
        _resolve_fallback_behavior_contract,
        _split_sentences_answer_complete,
        validate_response_delta,
    )

    metrics: Dict[str, Any] = {
        "quote_narration_overlap": None,
        "quote_narration_trigram_overlap": None,
        "adjacent_phrase_overlap": 0.0,
        "adjacent_structural_pairs": 0,
        "generic_filler_score": 0.0,
        "followup_overlap": None,
        "signal_markers_detected": 0,
    }
    evidence: Dict[str, Any] = {
        "matched_filler_patterns": [],
        "reused_ngrams": [],
        "redundant_opening_span": None,
        "prior_gm_reference_snippet": None,
        "adjacent_reuse_detail": None,
    }

    out: Dict[str, Any] = {
        "checked": False,
        "passed": True,
        "ok": True,
        "failure_reasons": [],
        "reasons": [],
        "skip_reason": None,
        "dialogue_narration_echo_ratio": None,
        "adjacent_reuse_pairs": 0,
        "meta_fallback_voice": False,
        "response_delta_shadow_failed": None,
        "metrics": metrics,
        "evidence": evidence,
    }
    if not isinstance(contract, Mapping) or not bool(contract.get("enabled")):
        out["skip_reason"] = "contract_disabled"
        return out

    fb_pol = _resolve_fallback_behavior_contract(gm_output if isinstance(gm_output, Mapping) else None)
    fb_compat = contract.get("fallback_compatibility") if isinstance(contract.get("fallback_compatibility"), Mapping) else {}
    uncertainty_active = bool((fb_pol or {}).get("uncertainty_active"))
    if uncertainty_active and bool(fb_compat.get("may_be_brief_under_uncertainty")):
        out["skip_reason"] = "fallback_uncertainty_brief_compat"
        out["checked"] = False
        return out

    text = _normalize_text(emitted_text)
    if not text:
        return out

    out["checked"] = True
    reasons: List[str] = []
    trace = contract.get("trace") if isinstance(contract.get("trace"), Mapping) else {}
    prior_trace = str(trace.get("prior_turn_gm_snippet_for_overlap") or "").strip()
    if prior_trace:
        evidence["prior_gm_reference_snippet"] = prior_trace[:220]

    if bool(contract.get("forbid_scene_narration_echo_as_dialogue")):
        for start, _end, inner in _quoted_spans(text):
            prose = _prose_before_index(text, start)
            if _word_count(prose) < 6 or _word_count(inner) < 5:
                continue
            ratio = _token_jaccard(_na_tokens(prose), _na_tokens(inner))
            tg = _trigram_jaccard(prose, inner)
            metrics["quote_narration_overlap"] = round(ratio, 4)
            metrics["quote_narration_trigram_overlap"] = round(tg, 4)
            out["dialogue_narration_echo_ratio"] = round(ratio, 4)
            substring_echo = _quote_echoes_prose_substring(prose, inner)
            if substring_echo or ratio >= 0.58 or (tg >= 0.44 and ratio >= 0.36 and _word_count(inner) >= 6):
                reasons.append("dialogue_echoes_prior_narration")
                span_a = prose[-140:] if len(prose) > 140 else prose
                span_b = inner[:140] if len(inner) > 140 else inner
                evidence["redundant_opening_span"] = {"narration_tail": span_a, "dialogue_head": span_b}
                break

    if bool(contract.get("forbid_adjacent_phrase_reuse")):
        sents = _split_sentences_answer_complete(text)
        max_anchor = int(contract.get("max_anchor_reuse_clauses") or 0)
        max_anchor = max(0, min(max_anchor, 3))
        allow_restate = bool(contract.get("allow_restate_for_continuity"))
        budget = max_anchor if allow_restate else 0
        pairs = 0
        first_detail: Dict[str, Any] | None = None
        first_ngrams: List[str] = []
        for i in range(len(sents) - 1):
            a, b = sents[i], sents[i + 1]
            bad, detail = _adjacent_pair_structural_reuse(a, b)
            if bad:
                pairs += 1
                if first_detail is None:
                    first_detail = {"index_pair": [i, i + 1], **detail}
                    first_ngrams = _shared_scaffold_trigrams(a, b)
        out["adjacent_reuse_pairs"] = pairs
        metrics["adjacent_structural_pairs"] = pairs
        if len(sents) > 1:
            metrics["adjacent_phrase_overlap"] = round(float(pairs) / float(len(sents) - 1), 4)
        if first_detail is not None:
            evidence["adjacent_reuse_detail"] = first_detail
        if first_ngrams:
            evidence["reused_ngrams"] = first_ngrams
        if pairs > budget:
            reasons.append("adjacent_phrase_reuse")

    wc = _word_count(text)
    pattern_hits = _collect_filler_pattern_hits(text)
    generic_nonanswer_hit = bool(_GENERIC_NONANSWER_SNIPPET.search(text))
    gscore = _generic_filler_score(text, generic_nonanswer_hit=generic_nonanswer_hit, pattern_hits=pattern_hits)
    metrics["generic_filler_score"] = round(gscore, 4)
    evidence["matched_filler_patterns"] = list(pattern_hits)

    if bool(contract.get("forbid_low_signal_generic_reply")):
        neg_filler = _diegetic_signal_negative_control(text)
        brevity_ok = bool(fb_compat.get("brevity_alone_is_not_failure")) and wc >= 6 and ('"' in text or "“" in text)
        legacy_generic = generic_nonanswer_hit and wc < 18 and not brevity_ok
        scored_pad = (gscore >= 0.52 and wc <= 22) or (gscore >= 0.45 and wc <= 14)
        thin_atmospheric = ("atmospheric_only" in pattern_hits or "pause_beat" in pattern_hits) and wc <= 14
        if (legacy_generic or scored_pad or thin_atmospheric) and not neg_filler and not brevity_ok:
            reasons.append("low_signal_generic_reply")

    rd_active = bool(trace.get("response_delta_contract_active"))
    if bool(contract.get("require_meaningful_change_on_followup")):
        pol = (gm_output or {}).get("response_policy") if isinstance(gm_output, Mapping) else None
        rd = pol.get("response_delta") if isinstance(pol, Mapping) and isinstance(pol.get("response_delta"), Mapping) else {}
        if rd_active and isinstance(rd, Mapping) and bool(rd.get("enabled")):
            rd_val = validate_response_delta(text, dict(rd))
            rd_checked = bool(rd_val.get("checked"))
            out["response_delta_shadow_failed"] = bool(rd_checked and not rd_val.get("passed"))
            if rd_checked and not rd_val.get("passed"):
                reasons.append("follow_up_missing_signal_shadow_response_delta")
        elif bool(trace.get("topic_follow_up_active")):
            prior = prior_trace
            if prior and _prior_substantive_for_na(prior):
                prev_toks = _na_tokens(prior)
                cur_toks = _na_tokens(text)
                j = _token_jaccard(prev_toks, cur_toks)
                metrics["followup_overlap"] = round(j, 4)
                sig_n = _followup_signal_markers_count(text)
                metrics["signal_markers_detected"] = sig_n
                meaningful = _meaningful_followup_change_vs_prior(text, prior)
                if j >= 0.68 and wc <= 44 and not meaningful:
                    reasons.append("follow_up_stale_restatement")

    meta_hit = _contains_meta_fallback_voice(text)
    out["meta_fallback_voice"] = meta_hit
    if meta_hit:
        reasons.append("non_diegetic_meta_voice")

    if bool(fb_compat.get("may_refuse_or_partially_answer_if_other_contracts_require")):
        ac = {}
        if isinstance(gm_output, Mapping):
            rp = gm_output.get("response_policy")
            if isinstance(rp, Mapping) and isinstance(rp.get("answer_completeness"), Mapping):
                ac = dict(rp["answer_completeness"])
        shape = str(ac.get("expected_answer_shape") or "").strip().lower()
        if shape in {"bounded_partial", "refusal_with_reason"} and reasons == ["low_signal_generic_reply"]:
            reasons.clear()

    out["failure_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
    out["passed"] = not bool(out["failure_reasons"])
    out["ok"] = bool(out["passed"])
    out["reasons"] = list(out["failure_reasons"])
    return out


def _prior_substantive_for_na(snippet: str) -> bool:
    s = " ".join(str(snippet or "").strip().split())
    if len(s) < 14:
        return False
    return _word_count(s) >= 3


def _strip_dialogue_prefix_overlapping_prose(prose: str, inner: str, *, min_overlap_words: int = 4) -> str | None:
    """Remove a leading word-prefix of *inner* that matches a terminal word-suffix of *prose* (non-inventive)."""
    raw_inner = str(inner or "").strip()
    if not raw_inner:
        return None
    pw = [w.lower() for w in re.findall(r"[A-Za-z']+", prose)]
    iw = re.findall(r"[A-Za-z']+", raw_inner)
    if len(pw) < min_overlap_words or len(iw) < min_overlap_words + 1:
        return None
    best = 0
    upper = min(len(pw), len(iw))
    for L in range(upper, min_overlap_words - 1, -1):
        if pw[-L:] == [w.lower() for w in iw[:L]]:
            best = L
            break
    if best < min_overlap_words:
        return None
    cut = 0
    seen = 0
    for m in re.finditer(r"[A-Za-z']+", raw_inner):
        seen += 1
        if seen == best:
            cut = m.end()
            break
    remainder = raw_inner[cut:].lstrip(" \t,;:")
    remainder = re.sub(r"^[\s,;:]+", "", remainder)
    if _word_count(remainder) < 2:
        return None
    return remainder


def _rewrite_first_quote_span(text: str, new_inner: str) -> str | None:
    spans = _quoted_spans(text)
    if not spans:
        return None
    start, end, _old = spans[0]
    q0 = text[start]
    q1 = text[end - 1] if end > start else '"'
    inner = new_inner.strip()
    if not inner:
        return None
    rebuilt = text[:start] + q0 + inner + q1 + text[end:]
    return _normalize_text(re.sub(r"\s+", " ", rebuilt))


def _sentence_pure_atmospheric(sentence: str) -> bool:
    s = str(sentence or "").strip()
    if not s:
        return False
    if "atmospheric_only" not in _collect_filler_pattern_hits(s):
        return False
    return bool(re.match(r"^(?:the\s+)?(?:mist|rain|dusk|dawn|torchlight|crowd|air|wind|bells?)\b", s, re.IGNORECASE))


def _sentence_weak_filler_shell(sentence: str) -> bool:
    s = str(sentence or "").strip()
    if not s:
        return False
    hits = set(_collect_filler_pattern_hits(s))
    if not hits:
        return False
    if _diegetic_signal_negative_control(s):
        return False
    wc = _word_count(s)
    if _sentence_pure_atmospheric(s):
        return True
    if wc <= 14 and hits <= {"pause_beat", "considers_words"}:
        return True
    if wc <= 12 and "weak_uncertainty_shell" in hits and not ("but" in s.lower() or "though" in s.lower()):
        return True
    low = s.lower()
    if (
        wc <= 22
        and "weak_uncertainty_shell" in hits
        and "because" not in low
        and "since" not in low
        and "if you" not in low
        and "ask the" not in low
    ):
        return True
    return False


def _followup_signal_sentence_score(sentence: str) -> int:
    from game.final_emission_validators import _NEXT_LEAD_SNIPPET, _partial_reason_in_text

    s = str(sentence or "")
    score = 0
    if _NEXT_LEAD_SNIPPET.search(s):
        score += 6
    if _partial_reason_in_text(s, ["uncertainty", "lack_of_knowledge", "gated_information"]):
        score += 3
    for grp in (
        _FOLLOWUP_REACTION_MARKERS,
        _FOLLOWUP_PERSPECTIVE_MARKERS,
        _FOLLOWUP_NARROW_UNCERTAINTY_MARKERS,
        _REFUSAL_BOUNDARY_MARKERS,
    ):
        for p in grp:
            if p.search(s):
                score += 2
                break
    if re.search(r"\b\d+\b", s):
        score += 1
    if "?" in s:
        score += 1
    cur = [t for t in _na_tokens(s) if len(t) >= 5]
    if len(cur) >= 2:
        score += 1
    return score


def _repair_adjacent_structural_pairs(
    t: str,
    contract: Mapping[str, Any],
    gm_output: Mapping[str, Any] | None,
    *,
    max_passes: int = 8,
) -> tuple[str | None, str | None]:
    from game.final_emission_validators import _split_sentences_answer_complete

    cur = _normalize_text(t)
    drops = 0
    for _ in range(max(1, max_passes)):
        sents = [s.strip() for s in _split_sentences_answer_complete(cur) if str(s).strip()]
        if len(sents) < 2:
            break
        progressed = False
        for i in range(len(sents) - 1):
            a, b = sents[i], sents[i + 1]
            bad, _det = _adjacent_pair_structural_reuse(a, b)
            if not bad:
                continue
            drop_i = i if _word_count(a) <= _word_count(b) else i + 1
            kept = [s for j, s in enumerate(sents) if j != drop_i]
            merged = _normalize_text(" ".join(_normalize_terminal_punctuation(s) for s in kept if s))
            if not merged:
                continue
            drops += 1
            progressed = True
            cur = merged
            v2 = validate_narrative_authenticity(cur, contract, gm_output=gm_output)
            if v2.get("passed"):
                mode = "drop_adjacent_redundant_sentence_multi" if drops > 1 else "drop_adjacent_redundant_sentence"
                return cur, mode
            break
        if not progressed:
            break
    return None, None


def _repair_followup_framing_and_order(
    t: str,
    contract: Mapping[str, Any],
    gm_output: Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    from game.final_emission_validators import _split_sentences_answer_complete

    trace = contract.get("trace") if isinstance(contract.get("trace"), Mapping) else {}
    prior = str(trace.get("prior_turn_gm_snippet_for_overlap") or "").strip()
    if not prior or not _prior_substantive_for_na(prior):
        return None, None
    sents = [s.strip() for s in _split_sentences_answer_complete(t) if str(s).strip()]
    if len(sents) < 2:
        return None, None
    scores = [_followup_signal_sentence_score(s) for s in sents]
    best_idx = max(range(len(sents)), key=lambda i: (scores[i], -i))
    if best_idx > 0 and scores[best_idx] >= scores[0] + 2:
        pick = sents[best_idx]
        rest = [s for j, s in enumerate(sents) if j != best_idx]
        ordered = [pick, *rest]
        merged = _normalize_text(" ".join(_normalize_terminal_punctuation(x) for x in ordered if x))
        v2 = validate_narrative_authenticity(merged, contract, gm_output=gm_output)
        if v2.get("passed"):
            return merged, "reorder_followup_high_signal_first"
    o0 = _token_jaccard(_na_tokens(sents[0]), _na_tokens(prior))
    if o0 >= 0.62:
        tail = " ".join(_normalize_terminal_punctuation(s) for s in sents[1:] if s)
        tail = _normalize_text(tail)
        if tail:
            v2 = validate_narrative_authenticity(tail, contract, gm_output=gm_output)
            if v2.get("passed"):
                return tail, "drop_stale_followup_framing_sentence"
    return None, None


def _repair_low_signal_filler_compression(
    t: str,
    contract: Mapping[str, Any],
    gm_output: Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    from game.final_emission_validators import _split_sentences_answer_complete

    cur = _normalize_text(t)
    for _ in range(max(1, 8)):
        sents = [s.strip() for s in _split_sentences_answer_complete(cur) if str(s).strip()]
        if len(sents) < 2:
            break
        droppable = [i for i, s in enumerate(sents) if _sentence_weak_filler_shell(s)]
        if not droppable:
            break
        progressed = False
        for idx in sorted(droppable, key=lambda i: (_word_count(sents[i]), i)):
            kept = [s for j, s in enumerate(sents) if j != idx]
            merged = _normalize_text(" ".join(_normalize_terminal_punctuation(s) for s in kept if s))
            if not merged.strip():
                continue
            v2 = validate_narrative_authenticity(merged, contract, gm_output=gm_output)
            if v2.get("passed"):
                return merged, "compress_filler_sentence"
            cur = merged
            progressed = True
            break
        if not progressed:
            break
    return None, None


def _repair_non_diegetic_sentence_drop(
    t: str,
    contract: Mapping[str, Any],
    gm_output: Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    from game.final_emission_validators import _contains_meta_fallback_voice, _split_sentences_answer_complete

    sents = [s.strip() for s in _split_sentences_answer_complete(t) if str(s).strip()]
    if len(sents) < 2:
        return None, None
    bad_idx = [i for i, s in enumerate(sents) if _contains_meta_fallback_voice(s)]
    for idx in sorted(bad_idx, key=lambda i: -_word_count(sents[i])):
        kept = [s for j, s in enumerate(sents) if j != idx]
        merged = _normalize_text(" ".join(_normalize_terminal_punctuation(s) for s in kept if s))
        if not merged.strip():
            continue
        v2 = validate_narrative_authenticity(merged, contract, gm_output=gm_output)
        if v2.get("passed"):
            return merged, "drop_non_diegetic_sentence"
    return None, None


def repair_narrative_authenticity_minimal(
    text: str,
    validation: Mapping[str, Any] | None,
    contract: Mapping[str, Any] | None,
    *,
    gm_output: Mapping[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Subtract/reorder only; never invent facts."""
    from game.final_emission_validators import _split_sentences_answer_complete

    if not isinstance(contract, Mapping) or not bool(contract.get("enabled")):
        return None, None
    val = validation if isinstance(validation, Mapping) else {}
    reasons = {str(x) for x in (val.get("failure_reasons") or []) if str(x).strip()}
    t = _normalize_text(text)
    if not t:
        return None, None

    def _passes(txt: str) -> bool:
        return bool(validate_narrative_authenticity(txt, contract, gm_output=gm_output).get("passed"))

    if "dialogue_echoes_prior_narration" in reasons:
        spans = _quoted_spans(t)
        if spans:
            start, end, inner = spans[0]
            trimmed = (t[:start] + t[end:]).strip()
            trimmed = re.sub(r"\s+", " ", trimmed)
            if trimmed and _passes(trimmed):
                return _normalize_text(trimmed), "drop_redundant_opening_quote"
            prose = _prose_before_index(t, start)
            compressed_inner = _strip_dialogue_prefix_overlapping_prose(prose, inner, min_overlap_words=4)
            if compressed_inner:
                rebuilt = _rewrite_first_quote_span(t, compressed_inner)
                if rebuilt and rebuilt != t and _passes(rebuilt):
                    return rebuilt, "compress_echo_dialogue_tail"

    if "adjacent_phrase_reuse" in reasons:
        sents = _split_sentences_answer_complete(t)
        if len(sents) >= 2:
            a0, b0 = sents[0], sents[1]
            struct_bad, _det = _adjacent_pair_structural_reuse(a0, b0)
            if _fourgram_overlap(a0, b0) or struct_bad:
                shorter_first = _word_count(a0) <= _word_count(b0)
                drop_idx = 0 if shorter_first else 1
                kept = [s for i, s in enumerate(sents) if i != drop_idx]
                merged = _normalize_text(" ".join(s.strip() for s in kept if s.strip()))
                if _passes(merged):
                    return merged, "drop_adjacent_redundant_sentence"
        fixed, mode = _repair_adjacent_structural_pairs(t, contract, gm_output)
        if fixed:
            return fixed, mode or "drop_adjacent_redundant_sentence_multi"

    if "follow_up_stale_restatement" in reasons:
        fixed, mode = _repair_followup_framing_and_order(t, contract, gm_output)
        if fixed and mode:
            return fixed, mode

    if "low_signal_generic_reply" in reasons:
        fixed, mode = _repair_low_signal_filler_compression(t, contract, gm_output)
        if fixed and mode:
            return fixed, mode

    if "non_diegetic_meta_voice" in reasons:
        fixed, mode = _repair_non_diegetic_sentence_drop(t, contract, gm_output)
        if fixed and mode:
            return fixed, mode

    return None, None
