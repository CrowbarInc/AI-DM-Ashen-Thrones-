"""Narrative authenticity contract: prompt + gate policy for anti-echo, signal density, and diegetic shape.

Orthogonal to ``response_delta`` / ``answer_completeness`` but may read their shipped traces on
``response_policy`` for inspection and light coordination (no duplication of their repair paths).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence

from game.final_emission_meta import build_narrative_authenticity_emission_trace
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

# Player / log cues that this turn is asking for hearsay, gossip, or secondhand street knowledge.
_RUMOR_PLAYER_SIGNAL_RES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "lex_rumor",
        re.compile(
            r"\b(?:rumors?|hearsay|gossip|whispers?|scuttlebutt|grapevine|tittle[\s-]?tattle)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "lex_reports_talk",
        re.compile(
            r"\b(?:reports?|reportedly|people\s+say|folks\s+say|they\s+say|some(?:one|body)\s+says?|"
            r"anyone\s+saying|going\s+around|making\s+the\s+rounds)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "lex_street_word",
        re.compile(
            r"\b(?:word\s+on\s+the\s+street|what(?:'s|\s+is)\s+the\s+(?:word|story|talk)|"
            r"what\s+have\s+you\s+heard|what\s+did\s+you\s+hear|what\s+do\s+people\s+say|"
            r"what\s+do\s+they\s+say|what\s+are\s+people\s+saying|what\s+is\s+going\s+around)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "lex_heard_asking",
        re.compile(
            r"\b(?:heard\s+(?:anything|about|that)|hear\s+anything|pick\s+up\s+anything|"
            r"catch\s+wind|get\s+wind)\b",
            re.IGNORECASE,
        ),
    ),
)

_DEFAULT_RUMOR_REALISM: Dict[str, Any] = {
    "enabled": True,
    "apply_on_secondhand_or_rumor_turns": True,
    "forbid_verbatim_scene_to_rumor_reuse": True,
    "forbid_recent_narration_to_dialogue_reuse": True,
    "require_one_of": [
        "source_limitation",
        "uncertainty_or_distortion",
        "perspective_or_bias",
        "net_new_detail",
    ],
    "allow_partial_fact_overlap": True,
    "forbid_identical_phrasing_even_when_overlap_allowed": True,
    "fallback_compatibility": {
        "allow_brief_bounded_partial_under_uncertainty": True,
        "do_not_fail_for_brevity_alone": True,
        "allow_source_limited_refusal": True,
    },
}

_RUMOR_SOURCE_LIMITATION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:only\s+(?:heard|know|what)|heard\s+(?:it\s+)?from|from\s+a\s+(?:runner|clerk|dockhand|sailor|"
        r"porter|messenger|stranger|soldier|witness|customer|regular)|second[\s-]?hand|third[\s-]?hand|"
        r"not\s+firsthand|wasn'?t\s+there|didn'?t\s+see\s+it|can'?t\s+vouch|couldn'?t\s+swear|"
        r"just\s+what\s+(?:they|people)\s+(?:say|claim)|that'?s\s+only\s+what)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:one\s+(?:runner|clerk|dockhand|sailor)\s+(?:said|claims?|told)|"
        r"(?:dock|gate|market|tavern|yard)\s+(?:talk|rumor)|watch\s+runner\s+said)\b",
        re.IGNORECASE,
    ),
)

_RUMOR_UNCERTAINTY_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:could\s+be\s+(?:drink|wine|ale)\s+talk|might\s+be\s+exaggerated|hard\s+to\s+say|"
        r"depends\s+who\s+you\s+ask|no\s+telling|might\s+be\s+wrong|could\s+be\s+wrong|"
        r"take\s+it\s+with\s+salt|grain\s+of\s+salt|shaky\s+story|thin\s+tale)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:unclear|unconfirmed|unverified|not\s+sure\s+whether|can'?t\s+pin\s+it\s+down|"
        r"if\s+it'?s\s+true|if\s+that'?s\s+true)\b",
        re.IGNORECASE,
    ),
)

_RUMOR_BIAS_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:blame\s+(?:the\s+)?|always\s+blame|would\s+say\s+that|in\s+their\s+interest|"
        r"sailors\s+tell\s+it|clerks\s+tell\s+it|tax\s+(?:men|folk)|customs\s+men|"
        r"one\s+way\s+to\s+hear\s+it|another\s+way\s+to\s+hear\s+it)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:biased|slant|angle\s+on\s+it|spin\s+on)\b", re.IGNORECASE),
)


def classify_rumor_secondhand_turn(
    *,
    player_text: str | None = None,
    response_type_contract: Mapping[str, Any] | None = None,
    recent_log_compact: Sequence[Mapping[str, Any]] | None = None,
    response_delta: Mapping[str, Any] | None = None,
    follow_up_pressure: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic rumor / secondhand-intent classifier (player + light policy context)."""
    _ = response_delta, follow_up_pressure  # reserved for future coordination; avoids unused warnings.
    reason_codes: List[str] = []
    trigger_spans: List[str] = []
    seen_spans: set[str] = set()

    def _consume_text(label: str, raw: str) -> None:
        s = str(raw or "").strip()
        if len(s) < 6:
            return
        low = s.lower()
        for code, pat in _RUMOR_PLAYER_SIGNAL_RES:
            for m in pat.finditer(low):
                span = m.group(0).strip()
                if len(span) >= 4:
                    key = f"{code}:{span[:64]}"
                    if key not in seen_spans:
                        seen_spans.add(key)
                        trigger_spans.append(span[:72])
                        tag = f"{label}:{code}"
                        if tag not in reason_codes:
                            reason_codes.append(tag)

    _consume_text("player_text", str(player_text or ""))
    recent = list(recent_log_compact or [])
    if recent:
        last = recent[-1] if isinstance(recent[-1], Mapping) else {}
        prev_player = str((last or {}).get("player_input") or "").strip()
        if prev_player and prev_player != str(player_text or "").strip():
            _consume_text("recent_log_player_input", prev_player)

    rtc = response_type_contract if isinstance(response_type_contract, Mapping) else {}
    rtype = str(rtc.get("required_response_type") or "").strip().lower()
    if rtype == "dialogue":
        reason_codes.append("response_type:dialogue")
    desc = str(rtc.get("response_type_description") or "").lower()
    if any(k in desc for k in ("hearsay", "rumor", "gossip", "secondhand", "street talk")):
        reason_codes.append("response_type:description_hearsay_hint")
        trigger_spans.append("response_type_description")

    lexical_hits = [x for x in reason_codes if x.startswith(("player_text:", "recent_log_player_input:"))]
    rumor_turn_active = bool(lexical_hits) or "response_type:description_hearsay_hint" in reason_codes
    return {
        "rumor_turn_active": rumor_turn_active,
        "rumor_turn_reason_codes": list(dict.fromkeys(reason_codes)),
        "trigger_spans": list(dict.fromkeys(trigger_spans))[:12],
    }


def _merge_rumor_realism_policy(base_rr: Mapping[str, Any], ov: Mapping[str, Any] | None) -> Dict[str, Any]:
    out = dict(base_rr)
    if not isinstance(ov, Mapping):
        return out
    for k, v in ov.items():
        if k == "fallback_compatibility" and isinstance(v, Mapping) and isinstance(out.get("fallback_compatibility"), dict):
            merged_fb = dict(out["fallback_compatibility"])
            merged_fb.update(dict(v))
            out["fallback_compatibility"] = merged_fb
        else:
            out[str(k)] = v
    return out


def _strip_quoted_regions(text: str) -> str:
    return re.sub(r'["“][^"”]{0,4000}["”]', " ", str(text or ""))


def _rumor_substantive_slice(text: str) -> str:
    spans = _quoted_spans(text)
    if spans:
        return " ".join(s for *_, s in spans if s)
    return str(text or "")


def _rumor_reference_token_bag(prior_gm: str, narration_now: str) -> set[str]:
    bag: set[str] = set()
    for t in _na_tokens(prior_gm) + _na_tokens(narration_now):
        if len(t) >= 4:
            bag.add(t)
    return bag


def _rumor_net_new_detail_count(slice_text: str, ref_bag: set[str]) -> int:
    n = 0
    for t in _na_tokens(slice_text):
        if len(t) < 5:
            continue
        if t in ref_bag or t in _CONTINUITY_LEXEMES:
            continue
        n += 1
    return n


def _rumor_detect_source_limitation(text: str) -> bool:
    if any(p.search(text) for p in _RUMOR_SOURCE_LIMITATION_RES):
        return True
    for p in _REFUSAL_BOUNDARY_MARKERS:
        if p.search(text) and re.search(r"\b(?:only|just|more\s+than|than\s+that)\b", text, re.IGNORECASE):
            return True
    return False


def _rumor_detect_uncertainty(text: str) -> bool:
    if any(p.search(text) for p in _RUMOR_UNCERTAINTY_RES):
        return True
    for p in _FOLLOWUP_NARROW_UNCERTAINTY_MARKERS:
        if p.search(text):
            return True
    if "weak_uncertainty_shell" in _collect_filler_pattern_hits(text):
        low = text.lower()
        if any(h in low for h in ("because", "since", "but", "though", "only from", "from the")):
            return True
    return False


def _rumor_detect_bias(text: str) -> bool:
    return any(p.search(text) for p in _RUMOR_BIAS_RES)


def _rumor_collapsed_substring_hit(a: str, b: str, *, min_chars: int = 38) -> bool:
    ca, cb = _collapse_ws(a), _collapse_ws(b)
    if len(ca) < min_chars or len(cb) < min_chars:
        return False
    short, long = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    return len(short) >= min_chars and short in long


def _rumor_consecutive_word_hit(a: str, b: str, *, k: int = 7) -> bool:
    wa = [w.lower() for w in re.findall(r"[A-Za-z']+", a) if len(w) >= 2]
    wb = [w.lower() for w in re.findall(r"[A-Za-z']+", b) if len(w) >= 2]
    if len(wa) < k or len(wb) < k:
        return False
    needles = {" ".join(wa[i : i + k]) for i in range(0, len(wa) - k + 1)}
    hay = " " + " ".join(wb) + " "
    return any(f" {n} " in hay for n in needles)


def _rumor_relaxed_signal_requirement(
    text: str,
    *,
    wc: int,
    gm_output: Mapping[str, Any] | None,
    rr_fb: Mapping[str, Any],
) -> tuple[bool, Dict[str, bool]]:
    """Return (relaxed_ok, flags) for rumor low-signal / bounded-partial compatibility (policy-owned)."""
    from game.final_emission_validators import _partial_reason_in_text, _resolve_fallback_behavior_contract

    flags: Dict[str, bool] = {}
    if bool(rr_fb.get("do_not_fail_for_brevity_alone")) and wc <= 14:
        flags["brevity_alone"] = True
        return True, flags
    if bool(rr_fb.get("allow_brief_bounded_partial_under_uncertainty")):
        pol = _resolve_fallback_behavior_contract(
            dict(gm_output) if isinstance(gm_output, Mapping) else None
        )
        if bool((pol or {}).get("uncertainty_active")):
            flags["fallback_uncertainty_active"] = True
            return True, flags
    if bool(rr_fb.get("allow_source_limited_refusal")):
        if _rumor_detect_source_limitation(text) or _partial_reason_in_text(
            text, ["uncertainty", "lack_of_knowledge", "gated_information"]
        ):
            flags["source_limited_or_refusal_language"] = True
            return True, flags
        for p in _REFUSAL_BOUNDARY_MARKERS:
            if p.search(text):
                flags["source_limited_or_refusal_language"] = True
                return True, flags
    ac: Dict[str, Any] = {}
    if isinstance(gm_output, Mapping):
        rp = gm_output.get("response_policy")
        if isinstance(rp, Mapping) and isinstance(rp.get("answer_completeness"), Mapping):
            ac = dict(rp["answer_completeness"])
    shape = str(ac.get("expected_answer_shape") or "").strip().lower()
    if shape in {"bounded_partial", "refusal_with_reason"} and bool(rr_fb.get("allow_brief_bounded_partial_under_uncertainty")):
        flags["answer_shape_bounded_partial"] = True
        return True, flags
    return False, flags


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

    rumor_class = classify_rumor_secondhand_turn(
        player_text=str(player_text or ""),
        response_type_contract=rtc,
        recent_log_compact=recent,
        response_delta=rd,
        follow_up_pressure=fup,
    )

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
        "rumor_realism": _merge_rumor_realism_policy(dict(_DEFAULT_RUMOR_REALISM), None),
        "trace": {
            "response_delta_contract_active": rd_active,
            "topic_follow_up_active": topic_follow_up,
            "answer_completeness_required": bool(ac.get("answer_required")),
            "dialogue_shape_expected": dialogue_expected,
            "prior_turn_gm_snippet_for_overlap": prior_gm or None,
            "player_text_len": len(str(player_text or "").strip()),
            "rumor_turn_active": bool(rumor_class.get("rumor_turn_active")),
            "rumor_turn_reason_codes": list(rumor_class.get("rumor_turn_reason_codes") or []),
            "rumor_trigger_spans": list(rumor_class.get("trigger_spans") or []),
        },
    }
    if isinstance(overrides, Mapping):
        ov_rr = overrides.get("rumor_realism")
        if isinstance(ov_rr, Mapping):
            base["rumor_realism"] = _merge_rumor_realism_policy(dict(_DEFAULT_RUMOR_REALISM), ov_rr)
        for k, v in overrides.items():
            if k == "rumor_realism":
                continue
            if k in {"anti_goals", "fallback_compatibility", "trace"} and isinstance(v, Mapping) and isinstance(
                base.get(k), dict
            ):
                merged = dict(base[k])
                merged.update(dict(v))
                base[k] = merged
            else:
                base[str(k)] = v
    return base


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
        "rumor_turn_active": None,
        "rumor_signal_count": None,
        "rumor_overlap_jaccard": None,
        "rumor_overlap_trigram": None,
        "rumor_new_detail_count": None,
        "rumor_source_limitation_present": None,
        "rumor_uncertainty_present": None,
        "rumor_bias_present": None,
    }
    evidence: Dict[str, Any] = {
        "matched_filler_patterns": [],
        "reused_ngrams": [],
        "redundant_opening_span": None,
        "prior_gm_reference_snippet": None,
        "adjacent_reuse_detail": None,
        "rumor_overlapping_spans": [],
        "rumor_missing_realism_categories": [],
        "rumor_net_new_candidate_tokens": [],
        "rumor_recent_comparison_snippet": None,
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
        "rumor_realism_relaxed_low_signal": False,
        "rumor_realism_relaxation_flags": {},
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

    rr_pol = contract.get("rumor_realism") if isinstance(contract.get("rumor_realism"), Mapping) else {}
    rumor_turn = bool(trace.get("rumor_turn_active"))
    metrics["rumor_turn_active"] = rumor_turn
    if bool(rr_pol.get("enabled")) and rumor_turn and bool(rr_pol.get("apply_on_secondhand_or_rumor_turns", True)):
        rr_fb = rr_pol.get("fallback_compatibility") if isinstance(rr_pol.get("fallback_compatibility"), Mapping) else {}
        relaxed, rumor_relax_flags = _rumor_relaxed_signal_requirement(text, wc=wc, gm_output=gm_output, rr_fb=rr_fb)
        has_quotes = bool(_quoted_spans(text))
        narration_now = _normalize_text(_strip_quoted_regions(text)) if has_quotes else ""
        slice_txt = _rumor_substantive_slice(text).strip() or text
        prior = prior_trace
        ref_bag = _rumor_reference_token_bag(prior, narration_now)
        j_prior = _token_jaccard(_na_tokens(slice_txt), _na_tokens(prior)) if prior else 0.0
        tg_prior = _trigram_jaccard(slice_txt, prior) if prior else 0.0
        j_scene = _token_jaccard(_na_tokens(slice_txt), _na_tokens(narration_now)) if narration_now.strip() else 0.0
        tg_scene = _trigram_jaccard(slice_txt, narration_now) if narration_now.strip() else 0.0
        metrics["rumor_overlap_jaccard"] = round(max(j_prior, j_scene), 4)
        metrics["rumor_overlap_trigram"] = round(max(tg_prior, tg_scene), 4)

        src_ok = _rumor_detect_source_limitation(text)
        unc_ok = _rumor_detect_uncertainty(text)
        bias_ok = _rumor_detect_bias(text)
        n_new = _rumor_net_new_detail_count(slice_txt, ref_bag)
        novel_long = any(
            t not in ref_bag and t not in _CONTINUITY_LEXEMES
            for t in _na_tokens(slice_txt)
            if len(t) >= 8
        )
        net_ok = n_new >= 2 or novel_long
        cats_ok = {"source_limitation": src_ok, "uncertainty_or_distortion": unc_ok, "perspective_or_bias": bias_ok, "net_new_detail": net_ok}
        signal_count = sum(1 for v in cats_ok.values() if v)
        metrics["rumor_signal_count"] = signal_count
        metrics["rumor_new_detail_count"] = n_new
        metrics["rumor_source_limitation_present"] = src_ok
        metrics["rumor_uncertainty_present"] = unc_ok
        metrics["rumor_bias_present"] = bias_ok

        missing = [k for k, v in cats_ok.items() if not v]
        evidence["rumor_missing_realism_categories"] = missing
        evidence["rumor_recent_comparison_snippet"] = prior[:220] if prior else None
        novel_toks = [
            t
            for t in _na_tokens(slice_txt)
            if len(t) >= 5 and t not in ref_bag and t not in _CONTINUITY_LEXEMES
        ][:8]
        evidence["rumor_net_new_candidate_tokens"] = novel_toks

        prior_sub = _prior_substantive_for_na(prior) if prior else False
        narr_sub = has_quotes and _word_count(narration_now) >= 8

        id_ph = bool(rr_pol.get("forbid_identical_phrasing_even_when_overlap_allowed", True))
        allow_overlap = bool(rr_pol.get("allow_partial_fact_overlap", True))
        high_sig = allow_overlap and signal_count >= 1

        id_hit_prior = bool(
            prior_sub
            and (
                _rumor_collapsed_substring_hit(slice_txt, prior, min_chars=36)
                or _rumor_consecutive_word_hit(slice_txt, prior, k=7)
            )
        )
        id_hit_scene = bool(
            narr_sub
            and (
                _rumor_collapsed_substring_hit(slice_txt, narration_now, min_chars=34)
                or _rumor_consecutive_word_hit(slice_txt, narration_now, k=7)
            )
        )
        identical_prior = id_ph and id_hit_prior
        identical_scene = id_ph and id_hit_scene
        if identical_prior or identical_scene:
            reasons.append("rumor_uses_identical_phrasing_for_known_fact")
            if identical_prior and prior:
                evidence["rumor_overlapping_spans"].append(
                    {"kind": "prior_gm", "reply_excerpt": slice_txt[:140], "ref_excerpt": prior[:140]}
                )
            if identical_scene and narration_now.strip():
                evidence["rumor_overlapping_spans"].append(
                    {"kind": "same_turn_narration", "reply_excerpt": slice_txt[:140], "ref_excerpt": narration_now[:140]}
                )

        if bool(rr_pol.get("forbid_recent_narration_to_dialogue_reuse", True)) and prior_sub and not identical_prior:
            sub_hit = _rumor_collapsed_substring_hit(slice_txt, prior, min_chars=40)
            heavy = j_prior >= 0.68 and tg_prior >= 0.48 and _word_count(slice_txt) >= 6
            if sub_hit or (heavy and not high_sig):
                reasons.append("rumor_repeats_recent_narration")
                evidence["rumor_overlapping_spans"].append(
                    {"kind": "recent_narration_echo", "reply_excerpt": slice_txt[:160], "ref_excerpt": prior[:160]}
                )

        if bool(rr_pol.get("forbid_verbatim_scene_to_rumor_reuse", True)) and narr_sub and not identical_scene:
            sub_s = _rumor_collapsed_substring_hit(slice_txt, narration_now, min_chars=36)
            heavy_s = j_scene >= 0.62 and tg_scene >= 0.44 and _word_count(slice_txt) >= 5
            if (sub_s or (heavy_s and not high_sig)) and narration_now.strip():
                reasons.append("rumor_restates_scene_description")
                evidence["rumor_overlapping_spans"].append(
                    {"kind": "scene_narration_as_rumor", "reply_excerpt": slice_txt[:160], "ref_excerpt": narration_now[:160]}
                )

        req = list(rr_pol.get("require_one_of") or [])
        req_ok = not req or any(
            (k == "source_limitation" and src_ok)
            or (k == "uncertainty_or_distortion" and unc_ok)
            or (k == "perspective_or_bias" and bias_ok)
            or (k == "net_new_detail" and net_ok)
            for k in req
        )
        if not req_ok and not relaxed:
            reasons.append("rumor_adds_no_new_signal")
            if not src_ok:
                reasons.append("secondhand_info_lacks_source_limitation")
            if not (unc_ok or bias_ok):
                reasons.append("secondhand_info_lacks_uncertainty_or_bias")
        if not req_ok and relaxed:
            out["rumor_realism_relaxed_low_signal"] = True
            out["rumor_realism_relaxation_flags"] = dict(rumor_relax_flags)

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
    return _rewrite_nth_quote_span(text, 0, new_inner)


def _rewrite_nth_quote_span(text: str, span_index: int, new_inner: str) -> str | None:
    spans = _quoted_spans(text)
    if not spans or span_index < 0 or span_index >= len(spans):
        return None
    start, end, _old = spans[span_index]
    q0 = text[start]
    q1 = text[end - 1] if end > start else '"'
    inner = new_inner.strip()
    if not inner:
        return None
    rebuilt = text[:start] + q0 + inner + q1 + text[end:]
    return _normalize_text(re.sub(r"\s+", " ", rebuilt))


# Bounded rumor-realism repair (AER2): subtractive / reorder only; revalidated per candidate.
_RUMOR_NA_REPAIR_REASONS: frozenset[str] = frozenset(
    {
        "rumor_repeats_recent_narration",
        "rumor_restates_scene_description",
        "rumor_uses_identical_phrasing_for_known_fact",
        "rumor_adds_no_new_signal",
        "secondhand_info_lacks_source_limitation",
        "secondhand_info_lacks_uncertainty_or_bias",
    }
)
_RUMOR_LOW_SIGNAL_REPAIR_REASONS: frozenset[str] = frozenset(
    {
        "rumor_adds_no_new_signal",
        "secondhand_info_lacks_source_limitation",
        "secondhand_info_lacks_uncertainty_or_bias",
    }
)
_RUMOR_ECHO_REPAIR_REASONS: frozenset[str] = frozenset(
    {
        "rumor_repeats_recent_narration",
        "rumor_restates_scene_description",
        "rumor_uses_identical_phrasing_for_known_fact",
    }
)

_RUMOR_GENERIC_REPORT_SHELL_RE = re.compile(
    r"^(?:\s*)(?:people\s+say|they\s+say|folks\s+say|word\s+is|word\s+was|rumor\s+is|rumor\s+has\s+it|"
    r"some\s+say|so\s+they\s+say|what\s+they\s+say\s+is|the\s+talk\s+is)\b",
    re.IGNORECASE,
)


def _split_rumor_inner_clauses(inner: str) -> List[str]:
    """Deterministic clause boundaries inside reported speech (subtractive repair only)."""
    s = str(inner or "").strip()
    if not s:
        return []
    parts = re.split(r"\s*;\s*|\s+—\s+", s)
    out: List[str] = []
    for p in parts:
        chunk = str(p or "").strip()
        if not chunk:
            continue
        if _word_count(chunk) > 18:
            sub = re.split(r",\s+", chunk)
            if len(sub) >= 2 and all(_word_count(x.strip()) >= 4 for x in sub):
                out.extend(x.strip() for x in sub if x.strip())
            else:
                out.append(chunk)
        else:
            out.append(chunk)
    deduped: List[str] = []
    seen: set[str] = set()
    for c in out:
        if c in seen:
            continue
        seen.add(c)
        deduped.append(c)
    return deduped


def _join_rumor_clauses(clauses: Sequence[str]) -> str:
    parts = [str(c).strip() for c in clauses if str(c).strip()]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts)


def _clause_echoes_reference(clause: str, ref: str, *, min_sub: int = 30) -> bool:
    ref = str(ref or "").strip()
    if not ref:
        return False
    c = str(clause or "").strip()
    if not c:
        return False
    if _rumor_collapsed_substring_hit(c, ref, min_chars=min_sub):
        return True
    if _rumor_consecutive_word_hit(c, ref, k=6):
        return True
    if _word_count(c) >= 5 and _token_jaccard(_na_tokens(c), _na_tokens(ref)) >= 0.72:
        return True
    return False


def _rumor_clause_generic_shell(clause: str) -> bool:
    return bool(_RUMOR_GENERIC_REPORT_SHELL_RE.match(str(clause or "").strip()))


def _rumor_clause_duplicate_pair(a: str, b: str) -> bool:
    ca, cb = _collapse_ws(a), _collapse_ws(b)
    if not ca or not cb:
        return False
    if ca == cb:
        return True
    short, long = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    return len(short) >= 22 and short in long


def _rumor_clause_signal_tuple(
    clause: str,
    *,
    prior: str,
    narration_now: str,
    ref_bag: set[str],
) -> tuple[int, int, int, int, int, int]:
    """Sort key: higher is better for leading position (source/uncertainty/bias/net_new; lower echo)."""
    c = str(clause or "")
    src = 1 if _rumor_detect_source_limitation(c) else 0
    unc = 1 if _rumor_detect_uncertainty(c) else 0
    bias = 1 if _rumor_detect_bias(c) else 0
    n_new = _rumor_net_new_detail_count(c, ref_bag)
    net = 1 if (n_new >= 1 or any(len(t) >= 8 for t in _na_tokens(c) if t not in ref_bag and t not in _CONTINUITY_LEXEMES)) else 0
    echo_pen = 0
    if prior.strip() and _clause_echoes_reference(c, prior, min_sub=28):
        echo_pen += 2
    if narration_now.strip() and _clause_echoes_reference(c, narration_now, min_sub=26):
        echo_pen += 2
    if _rumor_clause_generic_shell(c):
        echo_pen += 1
    # tuple orders: prefer low echo_pen, high markers, longer non-generic content
    wc = _word_count(c)
    return (-echo_pen, src + unc + bias + net, src, unc + bias, n_new, wc)


def _rumor_evidence_priority_drop_indices(clauses: Sequence[str], evidence: Mapping[str, Any]) -> List[int]:
    spans = evidence.get("rumor_overlapping_spans") if isinstance(evidence, Mapping) else None
    if not isinstance(spans, list) or not spans:
        return []
    excerpts: List[str] = []
    for item in spans:
        if not isinstance(item, Mapping):
            continue
        ex = str(item.get("reply_excerpt") or "").strip()
        if len(ex) >= 12:
            excerpts.append(ex)
    if not excerpts:
        return []
    scored: List[tuple[int, int]] = []
    for i, c in enumerate(clauses):
        col = _collapse_ws(c)
        best = 0
        for ex in excerpts:
            e = _collapse_ws(ex)
            if len(e) >= 12 and e in col:
                best = max(best, len(e))
            elif len(e) >= 12 and len(col) >= 12 and (e[:40] in col or col[: min(60, len(col))] in e):
                best = max(best, 20)
        if best:
            scored.append((best, i))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [i for _, i in scored]


def _rumor_collect_echo_drop_candidates(
    clauses: Sequence[str],
    *,
    reasons: set[str],
    prior: str,
    narration_now: str,
    evidence: Mapping[str, Any],
) -> List[int]:
    n = len(clauses)
    if n < 2:
        return []
    drop: List[int] = []
    for i, c in enumerate(clauses):
        hit_prior = bool(prior.strip()) and (
            "rumor_repeats_recent_narration" in reasons
            or "rumor_uses_identical_phrasing_for_known_fact" in reasons
        )
        hit_scene = bool(narration_now.strip()) and (
            "rumor_restates_scene_description" in reasons or "rumor_uses_identical_phrasing_for_known_fact" in reasons
        )
        echo = False
        if hit_prior and _clause_echoes_reference(c, prior, min_sub=28):
            echo = True
        if hit_scene and _clause_echoes_reference(c, narration_now, min_sub=24):
            echo = True
        if echo:
            drop.append(i)
    if not drop:
        return []
    pri = _rumor_evidence_priority_drop_indices(clauses, evidence)
    drop_set = set(drop)
    ordered: List[int] = []
    seen_i: set[int] = set()
    for i in pri:
        if i in drop_set and i not in seen_i:
            ordered.append(i)
            seen_i.add(i)
    for i in drop:
        if i not in seen_i:
            ordered.append(i)
            seen_i.add(i)
    return [i for i in ordered if 0 <= i < n]


def _rumor_compress_duplicate_clauses(clauses: List[str]) -> List[str] | None:
    if len(clauses) < 2:
        return None
    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            if _rumor_clause_duplicate_pair(clauses[i], clauses[j]):
                scored = [(i, _word_count(clauses[i])), (j, _word_count(clauses[j]))]
                drop_k = min(scored, key=lambda t: t[1])[0]
                kept = [c for k, c in enumerate(clauses) if k != drop_k]
                if len(kept) >= 1 and _word_count(_join_rumor_clauses(kept)) >= 3:
                    return kept
    return None


def _rumor_try_transforms_on_quote(
    text: str,
    span_index: int,
    inner: str,
    contract: Mapping[str, Any],
    gm_output: Mapping[str, Any] | None,
    *,
    reasons: set[str],
    evidence: Mapping[str, Any],
    prior: str,
    narration_now: str,
    ref_bag: set[str],
    allow_low_signal_repair: bool,
) -> tuple[str | None, str | None]:
    """Apply bounded transforms to one quoted span; each candidate is revalidated externally."""
    clauses = _split_rumor_inner_clauses(inner)
    if not clauses:
        return None, None

    def _emit_from(new_clauses: Sequence[str]) -> str | None:
        joined = _join_rumor_clauses(new_clauses)
        if not joined or joined.strip() == inner.strip():
            return None
        return _rewrite_nth_quote_span(text, span_index, joined)

    # 1) Drop echoed clause(s), evidence-guided order
    if len(clauses) >= 2:
        for idx in _rumor_collect_echo_drop_candidates(
            clauses, reasons=reasons, prior=prior, narration_now=narration_now, evidence=evidence
        ):
            kept = [c for k, c in enumerate(clauses) if k != idx]
            cand = _emit_from(kept)
            if cand and bool(validate_narrative_authenticity(cand, contract, gm_output=gm_output).get("passed")):
                return cand, "drop_echoed_rumor_clause"

    # 2) Compress redundant duplicate clauses inside the quote
    compressed = _rumor_compress_duplicate_clauses(list(clauses))
    if compressed is not None:
        cand = _emit_from(compressed)
        if cand and bool(validate_narrative_authenticity(cand, contract, gm_output=gm_output).get("passed")):
            return cand, "compress_redundant_reported_speech"

    # 3) Reorder: higher-signal / less echo first
    if len(clauses) >= 2:
        order = sorted(
            range(len(clauses)),
            key=lambda k: _rumor_clause_signal_tuple(
                clauses[k], prior=prior, narration_now=narration_now, ref_bag=ref_bag
            ),
            reverse=True,
        )
        if order != list(range(len(clauses))):
            reordered = [clauses[k] for k in order]
            cand = _emit_from(reordered)
            if cand and bool(validate_narrative_authenticity(cand, contract, gm_output=gm_output).get("passed")):
                return cand, "reorder_distinct_rumor_clause_first"

    # 4–6) Low-signal compressions (skip under relaxed rumor semantics)
    if allow_low_signal_repair and len(clauses) >= 2:
        generic_idxs = [i for i, c in enumerate(clauses) if _rumor_clause_generic_shell(c)]
        if generic_idxs:
            for drop_i in sorted(generic_idxs, key=lambda i: -_word_count(clauses[i])):
                kept = [c for k, c in enumerate(clauses) if k != drop_i]
                cand = _emit_from(kept)
                if cand and bool(validate_narrative_authenticity(cand, contract, gm_output=gm_output).get("passed")):
                    return cand, "compress_generic_rumor_shell"

        src_idxs = [i for i, c in enumerate(clauses) if _rumor_detect_source_limitation(c)]
        if len(src_idxs) >= 1 and len(clauses) >= 2:
            kept = [clauses[i] for i in src_idxs]
            cand = _emit_from(kept)
            if cand and bool(validate_narrative_authenticity(cand, contract, gm_output=gm_output).get("passed")):
                return cand, "retain_source_limited_clause_only"

        unc_idxs = [i for i, c in enumerate(clauses) if _rumor_detect_uncertainty(c)]
        if len(unc_idxs) >= 1 and len(clauses) >= 2:
            kept = [clauses[i] for i in unc_idxs]
            cand = _emit_from(kept)
            if cand and bool(validate_narrative_authenticity(cand, contract, gm_output=gm_output).get("passed")):
                return cand, "retain_uncertain_clause_only"

        bias_idxs = [i for i, c in enumerate(clauses) if _rumor_detect_bias(c)]
        if len(bias_idxs) >= 1 and len(clauses) >= 2:
            kept = [clauses[i] for i in bias_idxs]
            cand = _emit_from(kept)
            if cand and bool(validate_narrative_authenticity(cand, contract, gm_output=gm_output).get("passed")):
                return cand, "retain_biased_clause_only"

    return None, None


def _repair_rumor_realism_unquoted_sentences(
    text: str,
    contract: Mapping[str, Any],
    gm_output: Mapping[str, Any] | None,
    *,
    reasons: set[str],
    prior: str,
    narration_now: str,
) -> tuple[str | None, str | None]:
    """Drop echoing sentences when there is no quoted slice to clause-split."""
    from game.final_emission_validators import _split_sentences_answer_complete

    prior = str(prior or "").strip()
    narration_now = str(narration_now or "").strip()
    sents = [s.strip() for s in _split_sentences_answer_complete(text) if str(s).strip()]
    if len(sents) < 2:
        return None, None
    for i, s in enumerate(sents):
        hit_prior = bool(prior) and (
            "rumor_repeats_recent_narration" in reasons or "rumor_uses_identical_phrasing_for_known_fact" in reasons
        )
        hit_scene = bool(narration_now) and (
            "rumor_restates_scene_description" in reasons or "rumor_uses_identical_phrasing_for_known_fact" in reasons
        )
        echo = (hit_prior and _clause_echoes_reference(s, prior, min_sub=32)) or (
            hit_scene and _clause_echoes_reference(s, narration_now, min_sub=28)
        )
        if not echo:
            continue
        kept = [x for k, x in enumerate(sents) if k != i]
        merged = _normalize_text(" ".join(_normalize_terminal_punctuation(x) for x in kept if x))
        if not merged.strip():
            continue
        if bool(validate_narrative_authenticity(merged, contract, gm_output=gm_output).get("passed")):
            return merged, "drop_echoed_rumor_clause"
    return None, None


def _repair_rumor_realism_bounded(
    text: str,
    contract: Mapping[str, Any],
    gm_output: Mapping[str, Any] | None,
    *,
    reasons: set[str],
    evidence: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    """Bounded subtractive rumor repairs with full revalidation per accepted candidate."""
    rr_pol = contract.get("rumor_realism") if isinstance(contract.get("rumor_realism"), Mapping) else {}
    if not bool(rr_pol.get("enabled")):
        return None, None
    rumor_hits = reasons & _RUMOR_NA_REPAIR_REASONS
    if not rumor_hits:
        return None, None

    t = _normalize_text(text)
    wc = _word_count(t)
    rr_fb = rr_pol.get("fallback_compatibility") if isinstance(rr_pol.get("fallback_compatibility"), Mapping) else {}
    relaxed_low_signal, _ = _rumor_relaxed_signal_requirement(t, wc=wc, gm_output=gm_output, rr_fb=rr_fb)
    allow_low_signal_repair = bool(rumor_hits & _RUMOR_LOW_SIGNAL_REPAIR_REASONS) and not relaxed_low_signal

    trace = contract.get("trace") if isinstance(contract.get("trace"), Mapping) else {}
    prior = str(trace.get("prior_turn_gm_snippet_for_overlap") or "").strip()
    has_quotes = bool(_quoted_spans(t))
    narration_now = _normalize_text(_strip_quoted_regions(t)) if has_quotes else ""
    ref_bag = _rumor_reference_token_bag(prior, narration_now)

    spans = _quoted_spans(t)
    for si, (_st, _en, inner) in enumerate(spans):
        fixed, mode = _rumor_try_transforms_on_quote(
            t,
            si,
            inner,
            contract,
            gm_output,
            reasons=reasons,
            evidence=evidence,
            prior=prior,
            narration_now=narration_now,
            ref_bag=ref_bag,
            allow_low_signal_repair=allow_low_signal_repair,
        )
        if fixed and mode:
            return fixed, mode

    if rumor_hits & _RUMOR_ECHO_REPAIR_REASONS and not spans:
        return _repair_rumor_realism_unquoted_sentences(
            t, contract, gm_output, reasons=reasons, prior=prior, narration_now=narration_now
        )

    return None, None


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

    rumor_subset = reasons & _RUMOR_NA_REPAIR_REASONS
    if rumor_subset:
        ev_map = val.get("evidence") if isinstance(val.get("evidence"), Mapping) else {}
        fixed_rumor, rumor_mode = _repair_rumor_realism_bounded(
            t, contract, gm_output, reasons=set(reasons), evidence=dict(ev_map)
        )
        if fixed_rumor and rumor_mode:
            return fixed_rumor, rumor_mode

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
