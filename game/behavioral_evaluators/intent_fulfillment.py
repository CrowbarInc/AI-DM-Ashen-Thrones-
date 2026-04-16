"""Deterministic intent-fulfillment scoring (no LLM, advisory only).

Evaluates whether *final_output* plausibly fulfills *player_input* intent using
fixed lexical and pattern rules. Intended for tests, gauntlets, and optional
session debug — never for altering player-facing narration.
"""

from __future__ import annotations

import os
import re
from typing import Any, Mapping

# --- Input normalization -----------------------------------------------------

_STOPWORDS = frozenset(
    """
    the a an and or but if to of in on for with you your my our their we i me
    it is was are were be been being do does did have has had can could would
    should may might will shall this that these those there here just very
    about into from at by not no yes so as then than too also only even
    does did doing done want try attempt tell ask know please could would
    """.split()
)


def _as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def _extract_eval_fields(turn_packet: Mapping[str, Any] | None) -> tuple[str, str, Any]:
    """Resolve player text, final text, and optional response_type from a loose packet dict."""
    if not isinstance(turn_packet, Mapping):
        return "", "", None
    tp = turn_packet
    player = _as_str(tp.get("player_input") or tp.get("player_text"))
    final = _as_str(tp.get("final_output") or tp.get("player_facing_text"))
    rt = tp.get("response_type")
    if rt is None:
        contracts = tp.get("contracts")
        if isinstance(contracts, Mapping):
            rt = contracts.get("response_type")
    if rt is None:
        rp = tp.get("response_policy")
        if isinstance(rp, Mapping):
            rt = rp.get("response_type")
    return player, final, rt


# --- Intent detectors --------------------------------------------------------

_QUESTION_LEAD = re.compile(
    r"^\s*("
    r"what|who|whom|whose|where|when|why|how|which|"
    r"can you|could you|do you|did you|may i|can i|could i|would i|should i|"
    r"is it|are they|was it|were they|is there|are there|"
    r"is it possible|would it be possible|could it be|"
    r"tell me|explain|describe\b)",
    re.I,
)

_WH_WORD = re.compile(
    r"\b(what|who|whom|whose|where|when|why|how|which)\b",
    re.I,
)

_ACTION_LEAD = re.compile(
    r"^\s*("
    r"i\s+(try|attempt|want|need|will|shall|ought|mean|plan|intend|am\s+going|"
    r"would\s+like|am\s+trying|keep|continue|start|begin|go|head|"
    r"look|listen|search|open|close|draw|sheath|attack|cast|speak|say|ask|tell|"
    r"push|pull|lift|drop|throw|climb|jump|run|walk|sneak|hide|read|use|do|"
    r"offer|pay|give|take|grab|examine|inspect|investigate)\b)",
    re.I,
)

_ACTION_INLINE = re.compile(
    r"\b(i\s+(try|attempt|want|need|will|cast|do|open|search|attack|ask|tell|examine|"
    r"go|head|look|listen|speak|use|push|pull|climb|jump|run|walk|sneak))\b",
    re.I,
)


def _detect_question_intent(player: str) -> bool:
    p = player.strip()
    if not p:
        return False
    if "?" in p:
        return True
    if _QUESTION_LEAD.match(p):
        return True
    if re.search(r"\bis it possible\b", p, re.I):
        return True
    if re.search(r"\bwould it be possible\b", p, re.I):
        return True
    return bool(_WH_WORD.search(p))


def _detect_action_intent(player: str) -> bool:
    p = player.strip()
    if not p:
        return False
    if _ACTION_LEAD.match(p) or _ACTION_INLINE.search(p):
        return True
    # Imperative-style first person without leading "I " still common in TTRPG logs
    if re.match(r"^\s*i\s+['\w]", p, re.I) and not _detect_question_intent(p):
        return True
    return False


def _meaningful_tokens(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z0-9']+", text.lower())
        if len(t) > 2 and t not in _STOPWORDS
    }


# --- Direct answer / resolution heuristics ------------------------------------

# Phrases that usually carry an explicit informational answer (not pure mood).
_DIRECT_ANSWER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(yes|no|yep|nope|indeed|correct|incorrect|true|false)\b[.!,:]?", re.I),
    re.compile(
        r"\b(you can|you cannot|you can't|you may|you may not|you must not|you should|you shouldn't|"
        r"you could|you couldn't|you will|you won't|you do not|you don't|you did not|you didn't)\b",
        re.I,
    ),
    re.compile(
        r"\b(it is|it isn't|it's not|it was|it wasn't|they are|they aren't|there is|there are|"
        r"there isn't|there aren't|this is|that is|these are|those are)\b",
        re.I,
    ),
    re.compile(r"\b(the answer is|in short|simply put|to be clear|because|therefore|so:|note that)\b", re.I),
    re.compile(
        r"\b(located (at|in|on|near)|you('ll| will) find (it|them|him|her)|you can find|"
        r"lies (to the|just|about)|stands (on|at|by|near)|two (streets|blocks)|"
        r"three (streets|blocks)|\d+\s*(blocks?|streets?|yards?|feet|miles|minutes))\b",
        re.I,
    ),
    re.compile(r"\b(north of|south of|east of|west of|next to|opposite|adjacent to|around the corner)\b", re.I),
)

_RESOLUTION_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(you succeed|you fail|succeeds|fails|succeeded|failed|hits|misses|critical|"
        r"rolls? a|rolled a|natural 20|natural 1|damage|healing|heals|opens?|opened|closed|"
        r"refuses|gives way|gave way|holds firm|nothing happens|no effect|the lock|the door|"
        r"manages to|fails to|unable to|can't quite|could not|cannot)\b",
        re.I,
    ),
    re.compile(r"\b\d+\s*(points? of )?(damage|hp|hit points?)\b", re.I),
)


def _has_direct_answer_signals(fragment: str) -> bool:
    if not fragment.strip():
        return False
    for pat in _DIRECT_ANSWER_PATTERNS:
        if pat.search(fragment):
            return True
    # Copular / definitional lead common for GM answers ("The inn is …", "Kessa is …").
    if re.search(r"\b(is|was|are|were|'s)\s+[a-z0-9].{8,}", fragment, re.I):
        return True
    return False


def _weak_question_topic_coverage(player: str, output: str) -> bool:
    """Non-authoritative: overlap of salient player tokens with output (fallback signal)."""
    pt = _meaningful_tokens(player)
    ot = _meaningful_tokens(output)
    # Drop wh-words from "topic" requirement
    pt -= {"what", "where", "when", "why", "how", "which", "who", "whom", "whose", "does", "did"}
    if len(pt) < 1:
        return False
    hit = pt & ot
    return len(hit) >= 1 and len(output.strip()) >= 35


def _atmospheric_only_heuristic(output: str) -> bool:
    """Rough filter: sensory-heavy short prose without informational anchors."""
    o = output.strip().lower()
    if len(o) < 24:
        return False
    sensory_hits = len(
        re.findall(
            r"\b(wind|rain|thunder|moonlight|shadow|shadows|chill|mist|fog|dusk|dawn|"
            r"silence|distant|echo|creak|torchlight|candle|smell|taste|air hangs)\b",
            o,
        )
    )
    tokens = _meaningful_tokens(o)
    if not tokens:
        return False
    ratio = sensory_hits / max(1, len(tokens))
    return ratio >= 0.22 and not _has_direct_answer_signals(o)


def _has_action_resolution(output: str, player: str) -> bool:
    if not output.strip():
        return False
    for pat in _RESOLUTION_MARKERS:
        if pat.search(output):
            return True
    # Skill / check narration often states outcome plainly.
    if re.search(r"\b(you (notice|realize|see|hear|find|spot|discover))\b.{12,}", output, re.I | re.S):
        return True
    pt, ot = _meaningful_tokens(player), _meaningful_tokens(output)
    overlap = pt & ot
    # Action object overlap plus a bounded outcome clause
    if overlap and re.search(r"\b(you|your)\b.{0,120}\b(open|close|find|see|feel|reach|move)\b", output, re.I):
        return True
    return False


def _split_intent_parts(player: str) -> list[str]:
    """Split on coordinators / semicolons; keep segments with substance."""
    raw = re.split(r"\s+(?:and|but|also)\s+|;\s*", player, flags=re.I)
    parts: list[str] = []
    for chunk in raw:
        sub = [s.strip() for s in re.split(r",\s+", chunk) if s.strip()]
        for s in sub:
            if len(s) >= 14:
                parts.append(s)
    # De-duplicate while preserving order
    out: list[str] = []
    for p in parts:
        if p not in out:
            out.append(p)
    return out


def _multi_part_intent(player: str) -> bool:
    parts = _split_intent_parts(player)
    return len(parts) >= 2


def _token_in_text(token: str, text_lower: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", text_lower))


def _parts_addressed(player: str, output: str) -> tuple[int, int]:
    parts = _split_intent_parts(player)
    if len(parts) < 2:
        return 0, 0
    ot = output.lower()
    n_ok = 0
    for p in parts:
        toks = _meaningful_tokens(p)
        toks -= {"also", "then"}
        if not toks:
            continue
        hits = sum(1 for t in toks if _token_in_text(t, ot))
        if hits >= 1 and (hits >= 2 or len(toks) == 1):
            n_ok += 1
        elif any(_token_in_text(g, ot) for g in ("yes", "no", "indeed")) and _has_direct_answer_signals(output):
            n_ok += 1
    return n_ok, len(parts)


def _long_narrative_opportunity(output: str) -> bool:
    o = output.strip()
    if len(o) >= 260:
        return True
    if o.count("\n\n") >= 1 and len(o) >= 120:
        return True
    return False


def _answer_before_narrative(player: str, output: str) -> bool:
    """If question + long narrative, direct signals should appear early."""
    if not (_detect_question_intent(player) and _long_narrative_opportunity(output)):
        return True
    lead = output[: min(280, len(output))]
    if _has_direct_answer_signals(lead):
        return True
    if _weak_question_topic_coverage(player, lead):
        return True
    return False


def evaluate_intent_fulfillment(turn_packet: Mapping[str, Any] | None) -> dict[str, Any]:
    """Score how well *final_output* fulfills *player_input* (deterministic).

    *turn_packet* may include ``player_input`` / ``player_text``, ``final_output`` /
    ``player_facing_text``, and optional ``response_type`` (top-level, or under
    ``contracts`` / ``response_policy`` for turn-packet-shaped dicts).

    Returns a dict with boolean flags ``fulfilled``, ``partial``, ``missed``,
    ``notes`` (str list), and ``score`` in ``{0.0, 0.5, 1.0}``.
    """
    player, output, response_type = _extract_eval_fields(turn_packet)
    notes: list[str] = []

    if response_type is not None:
        notes.append(f"response_type:{response_type!r}")

    if not player and not output:
        notes.append("empty_packet")
        return {
            "fulfilled": True,
            "partial": False,
            "missed": False,
            "notes": notes,
            "score": 1.0,
        }

    q = _detect_question_intent(player)
    a = _detect_action_intent(player)
    m = _multi_part_intent(player)

    if q:
        notes.append("intent:question")
    if a:
        notes.append("intent:action")
    if m:
        notes.append("intent:multi_part")

    question_hard_fail = False
    question_soft_fail = False

    if q:
        strong = _has_direct_answer_signals(output)
        weak = _weak_question_topic_coverage(player, output)
        atmospheric = _atmospheric_only_heuristic(output)
        if atmospheric and not strong:
            notes.append("heuristic:atmospheric_only")
        if not strong and not weak:
            question_hard_fail = True
            notes.append("rule:question_expects_direct_answer")
        elif not strong and weak:
            question_soft_fail = True
            notes.append("rule:question_answered_topic_only")
        if not _answer_before_narrative(player, output):
            question_soft_fail = True
            notes.append("rule:answer_should_precede_long_narrative")

    action_fail = False
    if a and not _has_action_resolution(output, player):
        action_fail = True
        notes.append("rule:action_expects_resolution")

    multi_hard = False
    multi_soft = False
    if m:
        ok, total = _parts_addressed(player, output)
        notes.append(f"multi_part:{ok}/{total}")
        if ok == 0:
            multi_hard = True
            notes.append("rule:multi_part_unaddressed")
        elif ok < total:
            multi_soft = True
            notes.append("rule:multi_part_partial")

    missed = question_hard_fail or action_fail or multi_hard
    partial = (not missed) and (question_soft_fail or multi_soft)
    fulfilled = (not missed) and (not partial)

    if missed:
        score = 0.0
    elif partial:
        score = 0.5
    else:
        score = 1.0

    return {
        "fulfilled": fulfilled,
        "partial": partial,
        "missed": missed,
        "notes": notes,
        "score": score,
    }


def _truthy_env(name: str) -> bool:
    v = os.getenv(name)
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "on")


def maybe_attach_intent_fulfillment_eval(
    session: Mapping[str, Any] | None,
    *,
    player_input: str,
    final_output: str,
    response_type: Any = None,
) -> dict[str, Any] | None:
    """If ``ASGM_RECORD_INTENT_FULFILLMENT_EVAL`` is set, attach eval to ``session['last_action_debug']``.

    No-op when disabled or *session* lacks a mutable ``last_action_debug`` dict.
    Does not change player-facing text. Returns the eval dict when recorded.
    """
    if not _truthy_env("ASGM_RECORD_INTENT_FULFILLMENT_EVAL"):
        return None
    if not isinstance(session, dict):
        return None
    lad = session.get("last_action_debug")
    if not isinstance(lad, dict):
        return None
    payload = evaluate_intent_fulfillment(
        {
            "player_input": player_input,
            "final_output": final_output,
            "response_type": response_type,
        }
    )
    lad["intent_fulfillment_eval"] = payload
    return payload
