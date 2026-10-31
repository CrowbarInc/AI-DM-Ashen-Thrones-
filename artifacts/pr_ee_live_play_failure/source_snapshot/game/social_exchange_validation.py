"""Strict-social route legality and emission validation helpers (BV14A canonical owner)."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.social_exchange_policy import looks_like_npc_directed_question

_SENTENCE_TERMINATORS = ".!?"

_CLOSING_PUNCT_OR_QUOTES = "\"')]}»”’"

_SCENE_CONTAMINATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bfor a breath,?\s+the scene\b", re.IGNORECASE),
    re.compile(r"\bthe scene holds\b", re.IGNORECASE),
    re.compile(r"\bscene stays still\b", re.IGNORECASE),
    re.compile(r"\bvoices shift around you\b", re.IGNORECASE),
    re.compile(r"\bnothing in the scene points\b", re.IGNORECASE),
    re.compile(r"\bnothing visible around\b", re.IGNORECASE),
    re.compile(r"\bnothing around\b.+\bconfirms\b", re.IGNORECASE),
    re.compile(r"\bno certain answer\b", re.IGNORECASE),
    re.compile(r"\bfrom here, no\b", re.IGNORECASE),
    re.compile(r"\bno clear answer\b", re.IGNORECASE),
    re.compile(r"\bthe scene suggests\b", re.IGNORECASE),
    re.compile(r"\bit can be inferred\b", re.IGNORECASE),
    re.compile(r"\bdoes not point to a clear answer\b", re.IGNORECASE),
    re.compile(r"\bnothing resolves into\b", re.IGNORECASE),
    re.compile(r"\baround you, small details sharpen into clues\b", re.IGNORECASE),
    re.compile(r"\btaken together, the marks\b", re.IGNORECASE),
    re.compile(r"\bscuffed mud, broken chalk\b", re.IGNORECASE),
    re.compile(r"\btwo details stand out\b", re.IGNORECASE),
)

_INTERRUPTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bshouting breaks out\b", re.IGNORECASE),
    re.compile(r"\bshout(?:ing)? breaks out\b", re.IGNORECASE),
    re.compile(r"\bshout erupts\b", re.IGNORECASE),
    re.compile(r"\bcommotion\b", re.IGNORECASE),
    re.compile(r"\balarm\b", re.IGNORECASE),
    re.compile(r"\bcrowd .*?(?:erupts|breaks|surges)\b", re.IGNORECASE),
    re.compile(r"\berupts in the crowd\b", re.IGNORECASE),
)

_EXPLICIT_INTERRUPTION_JOIN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bstarts to answer, then\b", re.IGNORECASE),
    re.compile(r"\bbegins to answer, then\b", re.IGNORECASE),
    re.compile(r"\bbreaks off\b", re.IGNORECASE),
    re.compile(r"\bcuts (?:himself|herself|themselves) off\b", re.IGNORECASE),
    re.compile(r"\bbefore .*?(?:can|could) .*?(?:answer|finish)\b", re.IGNORECASE),
    re.compile(r"\bas .*?(?:shouting|commotion|alarm) .*?(?:breaks out|erupts)\b", re.IGNORECASE),
)

_NPC_SETUP_HINTS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:says|said|replies|replied|answers|answered|mutters|whispers|asks)\b", re.IGNORECASE),
    re.compile(r"\bstarts to answer\b", re.IGNORECASE),
    re.compile(r"\bbegins to answer\b", re.IGNORECASE),
    re.compile(r"\"[^\"]{2,}\"", re.IGNORECASE),
)

_DETACHED_OMNISCIENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthe plan behind\b", re.IGNORECASE),
    re.compile(r"\bis likely to\b", re.IGNORECASE),
    re.compile(r"\bthe likely motive\b", re.IGNORECASE),
    re.compile(r"\bthis would benefit\b", re.IGNORECASE),
    re.compile(r"\bwould benefit them\b", re.IGNORECASE),
    re.compile(r"\bdisrupt(?:ting)?\s+local\s+order\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+a\s+tactical\b", re.IGNORECASE),
)

_CLUE_OR_ANALYTICAL_SUBSTITUTE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:two\s+details|scuffed\s+mud|broken\s+chalk|wet\s+footprints)\b", re.IGNORECASE),
    re.compile(r"\baround\s+you,\s+small\s+details\b", re.IGNORECASE),
    re.compile(r"\btaken\s+together,\s+the\s+marks\b", re.IGNORECASE),
    re.compile(r"\bonly\s+fragments\s+of\b", re.IGNORECASE),
    re.compile(r"\bthe\s+notice\s+board\s+is\b", re.IGNORECASE),
)

_REFUSAL_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bnot\s+nam(?:ing|e)\b", re.IGNORECASE),
    re.compile(r"\bwon'?t\s+say\b", re.IGNORECASE),
    re.compile(r"\bI\s+won'?t\s+name\b", re.IGNORECASE),
    re.compile(r"\bno\s+names\s+here\b", re.IGNORECASE),
)

_IGNORANCE_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bdon'?t\s+know\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\s+know\b", re.IGNORECASE),
    re.compile(r"\bcan'?t\s+swear\b", re.IGNORECASE),
    re.compile(r"\bnot\s+the\s+names\b", re.IGNORECASE),
    re.compile(r"\bheard\s+the\s+talk\b", re.IGNORECASE),
    re.compile(r"\bno\s+one\s+here\s+can\s+swear\b", re.IGNORECASE),
)

_PRESSURE_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\btighten(?:s|ed)?\s+(?:their|his|her)\s+jaw\b", re.IGNORECASE),
    re.compile(r"\bI'?ve\s+told\s+you\s+what\s+I\s+know\b", re.IGNORECASE),
    re.compile(r"\bthat'?s\s+all\s+you'?re\s+getting\b", re.IGNORECASE),
    re.compile(r"\bpress\s+me\s+on\s+this\b", re.IGNORECASE),
    re.compile(r"\bconversation\s+is\s+over\b", re.IGNORECASE),
    re.compile(r"\bstop\s+grind(?:ing)?\s+the\s+same\s+point\b", re.IGNORECASE),
)

_EXPLANATION_REALIZATION_RE = re.compile(
    r"\b(?:all i know|rumor|word is|from what i know|what i know on|ledger desk|pier)\b",
    re.IGNORECASE,
)

_ECHO_TOKEN_STOPWORDS: frozenset[str] = frozenset(
    {
        "that",
        "this",
        "with",
        "from",
        "your",
        "have",
        "what",
        "when",
        "where",
        "which",
        "would",
        "could",
        "should",
        "about",
        "there",
        "their",
        "them",
        "they",
        "then",
        "than",
        "here",
        "just",
        "like",
        "some",
        "into",
        "please",
        "tavern",
        "runner",
        "guard",
        "captain",
        "player",
    }
)

def is_route_illegal_global_or_sanitizer_fallback_text(text: str | None) -> bool:
    """True when text matches global scene / empty-sanitizer / procedural sludge families (strict-social guard)."""
    t = _collapse_ws(str(text or ""))
    if not t:
        return True
    low = t.lower()
    if any(p.search(t) for p in _SCENE_CONTAMINATION_PATTERNS):
        return True
    banned = (
        "for a breath",
        "the scene holds",
        "voices shift around you",
        "nothing around the faces",
        "the answer has not formed yet",
        "from here, no certain answer",
        "nothing in the scene points",
        "for a breath, the scene stays still",
    )
    if any(b in low for b in banned):
        return True
    if re.search(r"\b(?:pin down|shadow tavern runner|you should|i'd suggest)\b", low):
        return True
    return False

def replacement_is_route_legal_social(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str = "",
    world: Dict[str, Any] | None = None,
) -> bool:
    """True if text is acceptable final social_exchange output (or intentional interruption path)."""
    from game.social_exchange_emission import hard_reject_social_exchange_text

    return not hard_reject_social_exchange_text(
        text,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=str(scene_id or "").strip(),
        world=world if isinstance(world, dict) else None,
    )

def _collapse_ws(text: str) -> str:
    return " ".join(str(text or "").strip().split())

def _split_sentences(text: str) -> List[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    src = text.replace("\r\n", "\n").replace("\r", "\n")
    sentences: List[str] = []
    buff: List[str] = []
    i = 0
    n = len(src)
    while i < n:
        ch = src[i]
        if ch == "\n":
            if i + 1 < n and src[i + 1] == "\n":
                flushed = _collapse_ws("".join(buff))
                if flushed:
                    sentences.append(flushed)
                buff = []
                while i + 1 < n and src[i + 1] == "\n":
                    i += 1
                i += 1
                continue
            buff.append(" ")
            i += 1
            continue
        buff.append(ch)
        if ch in _SENTENCE_TERMINATORS:
            j = i + 1
            while j < n and src[j] in _CLOSING_PUNCT_OR_QUOTES:
                buff.append(src[j])
                j += 1
            flushed = _collapse_ws("".join(buff))
            if flushed:
                sentences.append(flushed)
            buff = []
            while j < n and src[j].isspace():
                j += 1
            i = j
            continue
        i += 1
    tail = _collapse_ws("".join(buff))
    if tail:
        sentences.append(tail)
    return sentences

def _sentence_is_scene_contaminated(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return True
    low = s.lower()
    if any(p.search(s) for p in _SCENE_CONTAMINATION_PATTERNS):
        return True
    if low.startswith("you notice ") or low.startswith("you can trace"):
        return True
    return False

def _sentence_is_npc_setup(sentence: str) -> bool:
    s = (sentence or "").strip()
    return any(p.search(s) for p in _NPC_SETUP_HINTS)

def has_explicit_interruption_shape(text: str) -> bool:
    return any(p.search(text) for p in _EXPLICIT_INTERRUPTION_JOIN_PATTERNS)

def _looks_like_interruption_breakoff_text(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    if any(p.search(s) for p in _INTERRUPTION_PATTERNS) or has_explicit_interruption_shape(s):
        return True
    low = s.lower()
    has_cutoff = bool(
        re.search(
            r"\b(?:starts?\s+to\s+answer|opens?\s+(?:their|his|her)\s+mouth|begins?\s+to\s+(?:answer|respond)|breaks?\s+off|cuts?\s+across|cut\s+off)\b",
            low,
        )
    )
    has_disturbance = bool(
        re.search(r"\b(?:shout(?:ing)?|commotion|uproar|cry(?:ing|ies)?|yell(?:ing)?|crowd|square|room|tables?)\b", low)
    )
    return has_cutoff and has_disturbance

def _interruption_sentence_index(sentences: List[str]) -> int | None:
    for i, s in enumerate(sentences):
        if _looks_like_interruption_breakoff_text(s):
            return i
    return None

def _sentence_has_speaker_speculation_frame(sentence: str) -> bool:
    """True when speculation is clearly NPC/speaker-bound (not narrator omniscience)."""
    t = (sentence or "").strip()
    if not t:
        return False
    low = t.lower()
    if '"' in t:
        return True
    if any(p.search(t) for p in _NPC_SETUP_HINTS):
        return True
    if re.search(r"\bif i (?:had|have) to guess\b", low):
        return True
    if re.search(r"\b(?:i'?d guess|my guess is)\b", low):
        return True
    if re.search(
        r"\b(?:they|he|she|the\s+(?:guard|runner|merchant|man|woman|captain|soldier|clerk|tender|bartender|sergeant|lieutenant))\s+"
        r"(?:grimaces?|shrugs?|mutters?|lowers?\s+(?:their|his|her)\s+voice|leans?\s+in)\b",
        low,
    ):
        return True
    return False

def _sentence_is_detached_omniscient_analysis(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return True
    if _sentence_has_speaker_speculation_frame(s):
        return False
    return any(p.search(s) for p in _DETACHED_OMNISCIENT_PATTERNS)

def _sentence_is_bounded_social_signal(sentence: str) -> bool:
    """Short ignorance / refusal / pressure lines without explicit dialogue tags."""
    s = (sentence or "").strip()
    if not s:
        return False
    return bool(
        any(p.search(s) for p in _IGNORANCE_SIGNAL_PATTERNS)
        or any(p.search(s) for p in _REFUSAL_SIGNAL_PATTERNS)
        or any(p.search(s) for p in _PRESSURE_SIGNAL_PATTERNS)
    )

def _sentence_is_clue_or_analytical_substitute(sentence: str) -> bool:
    s = (sentence or "").strip()
    if not s:
        return True
    if _sentence_is_scene_contaminated(sentence):
        return True
    if _sentence_is_detached_omniscient_analysis(sentence):
        return True
    if any(p.search(s) for p in _CLUE_OR_ANALYTICAL_SUBSTITUTE_PATTERNS):
        return True
    return False

def _speaker_display_prefixes(resolution: Dict[str, Any] | None) -> List[str]:
    """npc_name and title-cased npc_id — used to treat '<Name> frowns.' as speaker-owned."""
    if not isinstance(resolution, dict):
        return []
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    out: List[str] = []
    if name:
        out.append(name)
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        tid = npc_id.replace("_", " ").replace("-", " ").title()
        if tid and tid not in out:
            out.append(tid)
    return out

def _sentence_opens_with_resolved_npc_beat(sentence: str, resolution: Dict[str, Any] | None) -> bool:
    """Multi-word display names (e.g. 'Tavern Runner frowns.') must count as speaker-owned."""
    s = (sentence or "").strip()
    if not s or not isinstance(resolution, dict):
        return False
    low = s.lower()
    for pref in _speaker_display_prefixes(resolution):
        p = pref.strip()
        if len(p) < 2:
            continue
        if not low.startswith(p.lower()):
            continue
        tail = s[len(p) :].lstrip(" \t,")
        if re.match(
            r"^(?:frowns|grimaces|shrugs|nods|gestures|leans|mutters|spreads|opens|starts|shakes|lowers|raises)\b",
            tail,
            re.IGNORECASE,
        ):
            return True
    return False

def _sentence_is_speaker_owned_social(sentence: str, resolution: Dict[str, Any] | None = None) -> bool:
    """True when the line is plausibly NPC/speaker social (not pure narrator atmosphere)."""
    t = (sentence or "").strip()
    if not t:
        return False
    low = t.lower()
    if resolution is not None and _sentence_opens_with_resolved_npc_beat(t, resolution):
        return True
    if _looks_like_interruption_breakoff_text(t):
        return True
    if _sentence_is_bounded_social_signal(t):
        return True
    if '"' in t:
        return True
    if any(p.search(t) for p in _NPC_SETUP_HINTS):
        return True
    if re.search(
        r"\b(?:they|he|she|the\s+\w+)\s+"
        r"(?:says|replies|asks|mutters|whispers|answers|shakes|shrugs|grimaces|frowns|tightens|glances|opens|starts|breaks|steps|cuts|spreads|lowers|nods|points|avoids)\b",
        low,
    ):
        return True
    if re.search(
        r"\b(?:they|he|she|the\s+(?:guard|runner|merchant|man|woman|captain|soldier|clerk|tender|bartender|sergeant|lieutenant))\s+"
        r"(?:points|gestures|nods|waves|looks?|turns|leans|faces|taps|shrugs?|grimaces?|frowns?)\b",
        low,
    ):
        return True
    return False

def _normalize_gate_text(text: str | None) -> str:
    """Whitespace normalization matching :func:`game.final_emission_gate._normalize_text`."""
    return " ".join(str(text or "").strip().split())

_PLAYER_REQUEST_IN_DIALOGUE_RE = re.compile(
    r"\b(?:could\s+you|would\s+you|can\s+you|will\s+you|do\s+you\s+want|do\s+you\s+need|should\s+i)\b",
    re.IGNORECASE,
)

_REDIRECT_REALIZATION_RE = re.compile(
    r"\b(?:speak|talk)\s+to\b|\bask\s+the\b|\bhead\s+to\b|\btry\s+the\b|\bward\s+clerk\b|\bmain\s+gate\b|"
    r"\briver\s+gate\b|\bwest\s+pier\b|\bnight\s+watch\b|\b(?:north|south|east|west)\s+road\b|\bold\s+\w+\b",
    re.IGNORECASE,
)

_EXPLANATION_REALIZATION_RE = re.compile(
    r"\b(?:word\s+is|rumor\s+is|people\s+say|they\s+say|all\s+i\s+know|all\s+i\s+can|because\b|reason\b|"
    r"honest\b|truth\b|heard\b)\b",
    re.IGNORECASE,
)

def _echo_token_set(text: str) -> set[str]:
    low = str(text or "").lower()
    return {
        t
        for t in re.findall(r"[a-z0-9']+", low)
        if len(t) >= 4 and t not in _ECHO_TOKEN_STOPWORDS
    }

def _player_final_token_overlap_ratio(player_text: str, final_text: str) -> float:
    pt = _echo_token_set(player_text)
    if len(pt) < 3:
        return 0.0
    ft = _echo_token_set(final_text)
    if not ft:
        return 0.0
    return len(pt & ft) / float(len(pt))

def _social_text_shows_refusal_realization(text: str) -> bool:
    s = str(text or "")
    if not s.strip():
        return False
    if any(p.search(s) for p in _REFUSAL_SIGNAL_PATTERNS):
        return True
    if any(p.search(s) for p in _PRESSURE_SIGNAL_PATTERNS):
        return True
    if any(p.search(s) for p in _IGNORANCE_SIGNAL_PATTERNS):
        return True
    low = s.lower()
    if re.search(r"\bwon'?t\s+answer\b", low):
        return True
    if re.search(r"\bnot\s+answering\b", low):
        return True
    if re.search(r"\bnot\s+something\s+i\b", low):
        return True
    if re.search(r"\bdon'?t\s+trade\b", low):
        return True
    if re.search(r"\bnot\s+from\s+me\b", low):
        return True
    if re.search(r"\bnot\s+me\b", low):
        return True
    return False

_ACTIONABLE_DETAIL_RE = re.compile(
    r"\b(?:east|west|north|south|road|lane|gate|mill|square|market|crossroad|milestone|patrol)\b",
    re.IGNORECASE,
)

def _actionable_hits(text: str) -> set[str]:
    return {m.group(0).lower() for m in _ACTIONABLE_DETAIL_RE.finditer(str(text or ""))}

def _social_line_has_playable_npc_substance(final_text: str) -> bool:
    """True when the line already delivers a refusal, redirect, rumor, or concrete place/thread."""
    s = str(final_text or "")
    if not s.strip():
        return False
    if _social_text_shows_refusal_realization(s):
        return True
    if _REDIRECT_REALIZATION_RE.search(s):
        return True
    if _EXPLANATION_REALIZATION_RE.search(s):
        return True
    if _actionable_hits(s):
        return True
    return False

def _social_text_shows_redirect_realization(text: str) -> bool:
    return bool(_REDIRECT_REALIZATION_RE.search(str(text or "")))

def _social_text_shows_explanation_realization(text: str) -> bool:
    s = str(text or "")
    if _EXPLANATION_REALIZATION_RE.search(s):
        return True
    return _social_text_shows_redirect_realization(s)

def _npc_dialogue_has_player_request_framing(final_text: str) -> bool:
    for m in re.finditer(r'"([^"]{5,200})"', str(final_text or "")):
        if _PLAYER_REQUEST_IN_DIALOGUE_RE.search(m.group(1)):
            return True
    return False

def _final_paragraph_ends_with_question(final_text: str) -> bool:
    t = _collapse_ws(str(final_text or "")).strip()
    return bool(t) and t.endswith("?")

def social_final_emission_malformed_player_echo(
    *,
    player_text: str,
    final_text: str,
    resolution: Dict[str, Any] | None,
) -> tuple[bool, List[str]]:
    """Narrow, deterministic checks for NPC lines that echo the player's ask or invert roles.

    Does not judge topic correctness—only final emission integrity vs structured reply hints.
    """
    reasons: List[str] = []
    if not isinstance(resolution, dict):
        return False, reasons
    pt = str(player_text or "").strip()
    ft = str(final_text or "").strip()
    if not pt or not ft:
        return False, reasons

    overlap = _player_final_token_overlap_ratio(pt, ft)
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    rk = str(soc.get("reply_kind") or "").strip().lower()
    po = str(soc.get("probe_outcome") or "").strip().lower()
    pmove = str(soc.get("social_probe_move") or "").strip().lower()

    if overlap >= 0.56 and _echo_token_set(pt) and not _social_line_has_playable_npc_substance(ft):
        reasons.append("high_player_token_overlap")

    if (
        _final_paragraph_ends_with_question(ft)
        and overlap >= 0.38
        and len(_echo_token_set(pt)) >= 3
        and not _social_line_has_playable_npc_substance(ft)
    ):
        reasons.append("terminal_question_with_player_overlap")

    if _npc_dialogue_has_player_request_framing(ft):
        reasons.append("player_request_framing_in_npc_dialogue")

    player_questionish = "?" in pt or looks_like_npc_directed_question(pt)

    if (
        rk == "refusal"
        and player_questionish
        and not _social_text_shows_refusal_realization(ft)
        and overlap >= 0.42
        and len(_echo_token_set(pt)) >= 4
    ):
        reasons.append("refusal_kind_without_refusal_realization")

    if po in ("actionable_redirect", "actionable_lead_or_redirect"):
        weak = not _social_text_shows_redirect_realization(ft)
        if weak and overlap >= 0.46 and not _social_line_has_playable_npc_substance(ft):
            reasons.append("actionable_outcome_without_redirect_realization")
        if (
            weak
            and _final_paragraph_ends_with_question(ft)
            and overlap >= 0.30
            and not _social_line_has_playable_npc_substance(ft)
        ):
            reasons.append("actionable_outcome_question_echo")

    if rk == "explanation" and po not in ("actionable_redirect", "actionable_lead_or_redirect"):
        if (
            not _social_text_shows_explanation_realization(ft)
            and _final_paragraph_ends_with_question(ft)
            and overlap >= 0.40
            and not _social_line_has_playable_npc_substance(ft)
        ):
            reasons.append("explanation_kind_question_without_explanation_realization")

    if (
        pmove == "transactional"
        and _final_paragraph_ends_with_question(ft)
        and overlap >= 0.36
        and not _social_line_has_playable_npc_substance(ft)
    ):
        reasons.append("transactional_terminal_question_overlap")

    return bool(reasons), reasons
