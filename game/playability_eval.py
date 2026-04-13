"""Deterministic playability scoring for validation and gauntlets (advisory only).

No LLM calls. Reads dead-turn policy from ``_final_emission_meta['dead_turn']`` via
:mod:`game.final_emission_meta` (DTD1 single source of truth). Tolerates missing/malformed
payload fields and always returns a stable top-level schema.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from game.final_emission_meta import read_dead_turn_from_gm_output, summarize_gameplay_validation_for_turn

SCHEMA_VERSION = 2

_STOPWORDS = frozenset(
    """
    the a an and or but if to of in on for with you your my our their we i me
    it is was are were be been being do does did have has had can could would
    should may might will shall this that these those there here just very
    about into from at by not no yes so as then than too also only even
    """.split()
)


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value).strip()
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _word_set(text: str) -> set[str]:
    return {t for t in _tokens(text) if t not in _STOPWORDS and len(t) > 1}


def _jaccard(a: str, b: str) -> float:
    wa, wb = _word_set(a), _word_set(b)
    if not wa and not wb:
        return 1.0
    if not wa or not wb:
        return 0.0
    inter = len(wa & wb)
    union = len(wa | wb)
    return inter / union if union else 0.0


def _has_player_question(player: str) -> bool:
    p = player.strip()
    if not p:
        return False
    if "?" in p:
        return True
    lead = p[:120].lower()
    return bool(
        re.match(
            r"^\s*(what|who|where|when|why|how|which|whose|whom|can you|could you|"
            r"do you|did you|is it|are they|was it|were they|tell me|explain)\b",
            lead,
        )
    )


_DEFLECTION_RES = (
    re.compile(r"\bas the (dungeon master|dm)\b", re.I),
    re.compile(r"\boutside (of )?the scope\b", re.I),
    re.compile(r"\blet's (just )?move on\b", re.I),
    re.compile(r"\bthat's up to you\b", re.I),
    re.compile(r"\broll (a |for )?(check|dice)\b", re.I),
    re.compile(r"\bwithout more (info|information|context)\b", re.I),
    re.compile(r"\bi (can't|cannot) say\b", re.I),
    re.compile(r"\bno answer\b", re.I),
    re.compile(r"\bnot (going to|gonna) answer\b", re.I),
)

_PROCEDURE_RES = (
    re.compile(r"\baccording to the rules\b", re.I),
    re.compile(r"\bper the system\b", re.I),
    re.compile(r"\bper the rules\b", re.I),
    re.compile(r"\brules as written\b", re.I),
    re.compile(r"\braw says\b", re.I),
)

_THROAT_CLEAR_RE = re.compile(r"^\s*(so|okay|ok|alright|well|sure|right)[,!.:\s]", re.I)

_NARROWING_RES = (
    re.compile(r"\bwho exactly\b", re.I),
    re.compile(r"\bwhere exactly\b", re.I),
    re.compile(r"\bwhich one\b", re.I),
    re.compile(r"\bname the\b", re.I),
    re.compile(r"\bbe specific\b", re.I),
    re.compile(r"\bexactly (who|where|what)\b", re.I),
)

_FORCED_ACTION_RES = (
    re.compile(r"\byou must\b", re.I),
    re.compile(r"\byou have to\b", re.I),
    re.compile(r"\bno choice\b", re.I),
    re.compile(r"\bonly option\b", re.I),
    re.compile(r"\bforces you to\b", re.I),
)

_IMMERSION_LEAK_RES = (
    re.compile(r"\bestablished state\b", re.I),
    re.compile(r"\bvalidator\b", re.I),
    re.compile(r"\brouter\b", re.I),
    re.compile(r"\bplanner\b", re.I),
    re.compile(r"\bsystem prompt\b", re.I),
    re.compile(r"\bdebug trace\b", re.I),
    re.compile(r"\btelemetry\b", re.I),
    re.compile(r"\bas an ai\b", re.I),
    re.compile(r"\bllm\b", re.I),
    re.compile(r"\bschema\b", re.I),
    re.compile(r"\bcontract layer\b", re.I),
)

_MENU_RES = (
    re.compile(r"\boption\s*[a-z0-9]\b", re.I),
    re.compile(r"\bchoose (an )?option\b", re.I),
    re.compile(r"\bclick\b", re.I),
    re.compile(r"\bselect (an )?action\b", re.I),
    re.compile(r"\bui\b", re.I),
)

_SYSTEM_VOICE_RES = (
    re.compile(r"\bthe system\b", re.I),
    re.compile(r"\bthe engine\b", re.I),
    re.compile(r"\bthe module\b", re.I),
)

_BOUNDED_PARTIAL_RES = (
    re.compile(r"\b(unclear|unknown|not certain|can't confirm|cannot confirm)\b", re.I),
    re.compile(r"\bno witness\b", re.I),
    re.compile(r"\bnot sure\b", re.I),
)

_NEXT_LEAD_RES = (
    re.compile(r"\b(try|ask|check|go to|head to|visit)\b", re.I),
    re.compile(r"\b(east|west|north|south|lane|alley|market|yard|gate|dock)\b", re.I),
    re.compile(r"\b(crew|contacts|rumor|rumors)\b", re.I),
)

_ANSWER_MARKERS_RES = (
    re.compile(r"\b(yes|no)\b", re.I),
    re.compile(r"\b(because|since|therefore)\b", re.I),
    re.compile(r"\b(captain|sergeant|lord|lady|sir|ma'am)\b", re.I),
    re.compile(r"\b(is|was|were|are)\s+[a-z]", re.I),
    re.compile(r"\b\d{1,4}\b"),
    re.compile(r"\b[a-z]{2,}\s+(commands|leads|runs|owns|guards)\b", re.I),
)

_SPECIFIC_NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")
_SPECIFIC_PLACE_RE = re.compile(
    r"\b(the\s+)?(east|west|north|south)\s+(lane|gate|yard|dock|market|quarter)\b", re.I
)


def _extract_gm_text(payload: Mapping[str, Any]) -> str:
    gm = _safe_str(payload.get("gm_text"))
    if gm:
        return gm
    go = payload.get("gm_output")
    if isinstance(go, Mapping):
        return _safe_str(
            go.get("player_facing_text") or go.get("text") or go.get("narration") or go.get("content")
        )
    return gm


def _extract_player_text(payload: Mapping[str, Any]) -> str:
    return _safe_str(payload.get("player_prompt"))


def _gm_output_for_dead_turn_read(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    go = payload.get("gm_output")
    if isinstance(go, Mapping):
        return go
    fem = payload.get("_final_emission_meta")
    if isinstance(fem, Mapping) and isinstance(fem.get("dead_turn"), Mapping):
        return {"_final_emission_meta": fem}
    return None


def _extract_prior_pair(payload: Mapping[str, Any]) -> tuple[str, str]:
    return _safe_str(payload.get("prior_player_prompt")), _safe_str(payload.get("prior_gm_text"))


def _count_hits(patterns: tuple[re.Pattern[str], ...], text: str) -> int:
    return sum(1 for pat in patterns if pat.search(text))


def _any_re_match(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pat.search(text) for pat in patterns)


def _score_direct_answer(*, player: str, gm: str) -> tuple[int, bool, list[str], dict[str, Any]]:
    reasons: list[str] = []
    signals: dict[str, Any] = {
        "has_question": _has_player_question(player),
        "deflection_hits": 0,
        "procedure_hits": 0,
        "echo_jaccard": round(_jaccard(gm, player), 3),
        "gm_word_count": len(_tokens(gm)),
        "bounded_partial": False,
        "next_lead": False,
        "answer_markers": 0,
    }

    if not gm:
        reasons.append("Missing GM text; cannot judge directness.")
        return 6, False, reasons, signals

    gm_l = gm.lower()
    signals["deflection_hits"] = _count_hits(_DEFLECTION_RES, gm_l)
    signals["procedure_hits"] = _count_hits(_PROCEDURE_RES, gm_l)
    signals["answer_markers"] = _count_hits(_ANSWER_MARKERS_RES, gm)
    signals["bounded_partial"] = _any_re_match(_BOUNDED_PARTIAL_RES, gm_l) and _any_re_match(_NEXT_LEAD_RES, gm_l)
    signals["next_lead"] = _any_re_match(_NEXT_LEAD_RES, gm_l)

    score = 17
    if not signals["has_question"]:
        score = 20
        reasons.append("No explicit question detected; scored leniently for directness.")
        if len(_tokens(gm)) >= 10:
            score = min(25, score + 3)
        return max(0, min(25, score)), score >= 15, reasons, signals

    if signals["deflection_hits"]:
        score -= 10
        reasons.append("Deflection-style non-answer detected.")
    if signals["procedure_hits"]:
        score -= 8
        reasons.append("Procedural/system-style dodge in a diegetic reply.")

    echo = float(signals["echo_jaccard"])
    if echo >= 0.62 and len(_tokens(gm)) < max(18, len(_tokens(player)) + 2):
        score -= 9
        reasons.append("GM largely restates the player's prompt with little new substance.")

    if _THROAT_CLEAR_RE.search(gm) and len(gm) < 70:
        score -= 5
        reasons.append("Answerless throat-clearing or filler opening.")

    clarify_only = bool(
        re.search(r"\b(need more specifics|be more specific|clarify what you mean)\b", gm_l)
    )
    if clarify_only and signals["answer_markers"] < 2 and not signals["bounded_partial"]:
        score -= 7
        reasons.append("Clarify-only loop without a bounded partial answer.")

    if signals["bounded_partial"] and signals["next_lead"]:
        score += 6
        reasons.append("Bounded partial with a concrete next lead.")

    if signals["answer_markers"] >= 2 and echo < 0.55:
        score += 5
        reasons.append("Concrete answer markers present.")

    if score < 15 and len(_tokens(gm)) >= 14 and signals["answer_markers"] >= 1 and echo < 0.5:
        score += 4
        reasons.append("Substantive reply recovers some directness.")

    score = max(0, min(25, score))
    passed = score >= 15
    return score, passed, reasons, signals


def _player_topic_terms(player: str) -> set[str]:
    return {t for t in _word_set(player) if len(t) >= 4}


def _score_player_intent(
    *, player: str, gm: str, prior_player: str
) -> tuple[int, bool, list[str], dict[str, Any]]:
    reasons: list[str] = []
    narrowing = any(p.search(player) for p in _NARROWING_RES)
    terms = _player_topic_terms(player)
    gm_terms = _word_set(gm)
    overlap = len(terms & gm_terms) if terms else 0
    ratio = overlap / len(terms) if terms else 1.0

    signals: dict[str, Any] = {
        "narrowing": narrowing,
        "topic_overlap_count": overlap,
        "topic_overlap_ratio": round(ratio, 3),
        "forced_action_hits": _count_hits(_FORCED_ACTION_RES, gm.lower()),
        "prior_present": bool(prior_player.strip()),
    }

    if not gm:
        reasons.append("Missing GM text; intent alignment unclear.")
        return 7, False, reasons, signals

    score = 18
    if terms and overlap == 0 and len(terms) >= 2:
        score -= 9
        reasons.append("GM misses obvious player topic anchors.")

    if narrowing:
        has_specificity = bool(_SPECIFIC_NAME_RE.search(gm) or _SPECIFIC_PLACE_RE.search(gm))
        refusal_ok = bool(re.search(r"\b(refuses|won't|will not|cannot name|won't name)\b", gm, re.I))
        if has_specificity or refusal_ok:
            score += 5
            reasons.append("Narrow follow-up receives specific detail or a grounded refusal.")
        else:
            score -= 8
            reasons.append("Narrowing follow-up not matched with specifics.")

    if signals["forced_action_hits"]:
        score -= 7
        reasons.append("Forced-action phrasing risks overriding player agency.")

    # Light drift check vs prior player prompt if current player continues thread
    if prior_player.strip():
        prior_terms = _player_topic_terms(prior_player)
        if prior_terms and terms and len(terms & prior_terms) >= min(2, len(terms)):
            prior_overlap = len(prior_terms & gm_terms)
            if prior_overlap == 0 and overlap <= 1:
                score -= 5
                reasons.append("Possible thread drift from the established player focus.")

    score = max(0, min(25, score))
    passed = score >= 15
    return score, passed, reasons, signals


def _score_logical_escalation(
    *, player: str, gm: str, prior_player: str, prior_gm: str
) -> tuple[int, bool, list[str], dict[str, Any]]:
    reasons: list[str] = []
    prior_gm_s = prior_gm.strip()
    prior_player_s = prior_player.strip()

    sim = round(_jaccard(gm, prior_gm), 3) if prior_gm_s else 0.0
    player_press = prior_player_s and (
        _jaccard(player, prior_player) >= 0.35 or _tokens(player) == _tokens(prior_player)
    )

    signals: dict[str, Any] = {
        "prior_gm_present": bool(prior_gm_s),
        "prior_player_present": bool(prior_player_s),
        "gm_repeat_jaccard": sim,
        "player_presses_thread": bool(player_press),
        "gm_word_count": len(_tokens(gm)),
    }

    if not gm:
        reasons.append("Missing GM text; escalation not evaluable.")
        return 8, False, reasons, signals

    score = 18
    if not prior_gm_s:
        reasons.append("No prior GM text; continuity pressure not observed.")
        score = 19
        return max(0, min(25, score)), score >= 15, reasons, signals

    new_detail = len(_word_set(gm) - _word_set(prior_gm_s))
    signals["net_new_terms"] = new_detail

    if sim >= 0.72 and len(_tokens(gm)) > 6:
        score -= 10
        reasons.append("High overlap with prior GM text suggests stale repetition.")

    if player_press and sim >= 0.62 and new_detail < 4:
        score -= 6
        reasons.append("Follow-up pressure did not unlock net-new detail.")

    if new_detail >= 8 and sim < 0.55:
        score += 5
        reasons.append("Net-new specifics relative to the prior beat.")

    if bool(re.search(r"\b(meanwhile|across town|elsewhere|in another city)\b", gm, re.I)):
        if player_press and sim < 0.45:
            score += 1
            reasons.append("Scene break language may justify continuity reset.")
        elif sim > 0.65:
            score -= 3
            reasons.append("Off-scene beat risks bleeding into a pressured thread.")

    score = max(0, min(25, score))
    passed = score >= 15
    return score, passed, reasons, signals


def _score_immersion(*, gm: str, debug_traces: Any) -> tuple[int, bool, list[str], dict[str, Any]]:
    reasons: list[str] = []
    blob = gm
    if debug_traces is not None and not isinstance(debug_traces, (dict, list)):
        blob = f"{gm}\n{_safe_str(debug_traces)}"
    elif isinstance(debug_traces, str) and debug_traces.strip():
        blob = f"{gm}\n{debug_traces.strip()}"

    gm_l = blob.lower()
    leak_hits = _count_hits(_IMMERSION_LEAK_RES, gm_l)
    menu_hits = _count_hits(_MENU_RES, gm_l)
    sys_hits = _count_hits(_SYSTEM_VOICE_RES, gm_l)

    signals: dict[str, Any] = {
        "leak_hits": leak_hits,
        "menu_hits": menu_hits,
        "system_voice_hits": sys_hits,
        "quoted_dialogue": bool(re.search(r"\"[^\"]{3,}\"", gm)),
        "scene_anchor_hits": _count_hits(
            (
                re.compile(r"\b(cobble|torch|mist|rain|gate|yard|dock|hall|tavern)\b", re.I),
                re.compile(r"\b(guard|captain|sergeant|merchant|crowd)\b", re.I),
            ),
            gm_l,
        ),
    }

    if not gm:
        reasons.append("Missing GM text; immersion defaults neutral.")
        return 14, False, reasons, signals

    score = 22
    if leak_hits:
        score -= min(14, 5 * leak_hits)
        reasons.append("Validator/planner/system scaffolding language leaks into narration.")
    if menu_hits:
        score -= min(10, 4 * menu_hits)
        reasons.append("Menu/UI-like phrasing breaks immersion.")
    if sys_hits:
        score -= min(10, 4 * sys_hits)
        reasons.append("Non-diegetic system voice detected.")

    if signals["quoted_dialogue"] or signals["scene_anchor_hits"] >= 1:
        score += min(3, 1 + signals["scene_anchor_hits"] // 2)
        reasons.append("Diegetic scene grounding or voiced dialogue present.")

    score = max(0, min(25, score))
    passed = score >= 15
    return score, passed, reasons, signals


def _finalize_overall(
    *,
    direct: tuple[int, bool, list[str], dict[str, Any]],
    intent: tuple[int, bool, list[str], dict[str, Any]],
    escalation: tuple[int, bool, list[str], dict[str, Any]],
    immersion: tuple[int, bool, list[str], dict[str, Any]],
) -> dict[str, Any]:
    s1, _, _, _ = direct
    s2, _, _, _ = intent
    s3, _, _, _ = escalation
    s4, _, _, _ = immersion
    total = int(max(0, min(100, s1 + s2 + s3 + s4)))

    if total >= 80:
        rating = "strong"
    elif total >= 55:
        rating = "acceptable"
    else:
        rating = "weak"

    passed = total >= 60 and s4 >= 10
    return {"score": total, "rating": rating, "passed": bool(passed)}


def _summarize(
    axes: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    strengths: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []

    for key, ax in axes.items():
        label = key
        sc = int(ax.get("score", 0))
        ps = bool(ax.get("passed"))
        rsn = ax.get("reasons") if isinstance(ax.get("reasons"), list) else []
        if ps and sc >= 20:
            strengths.append(f"{label}: strong ({sc}/25).")
        elif ps and sc >= 15:
            strengths.append(f"{label}: acceptable ({sc}/25).")
        elif not ps:
            failures.append(f"{label}: weak ({sc}/25).")
            for line in rsn[:2]:
                if isinstance(line, str) and line.strip():
                    failures.append(f"{label}: {line.strip()}")
        else:
            warnings.append(f"{label}: borderline ({sc}/25).")

    return {"strengths": strengths[:8], "failures": failures[:10], "warnings": warnings[:8]}


def evaluate_playability(payload: Any) -> dict[str, Any]:
    """Score a single turn/session slice; always returns ``SCHEMA_VERSION`` output."""
    data = _safe_mapping(payload)
    player = _extract_player_text(data)
    gm = _extract_gm_text(data)
    prior_player, prior_gm = _extract_prior_pair(data)
    dt = read_dead_turn_from_gm_output(_gm_output_for_dead_turn_read(data))

    direct = _score_direct_answer(player=player, gm=gm)
    intent = _score_player_intent(player=player, gm=gm, prior_player=prior_player)
    escalation = _score_logical_escalation(
        player=player, gm=gm, prior_player=prior_player, prior_gm=prior_gm
    )
    immersion = _score_immersion(gm=gm, debug_traces=data.get("debug_traces"))

    axes_out = {
        "direct_answer": {
            "score": direct[0],
            "passed": direct[1],
            "reasons": direct[2],
            "signals": direct[3],
        },
        "player_intent": {
            "score": intent[0],
            "passed": intent[1],
            "reasons": intent[2],
            "signals": intent[3],
        },
        "logical_escalation": {
            "score": escalation[0],
            "passed": escalation[1],
            "reasons": escalation[2],
            "signals": escalation[3],
        },
        "immersion": {
            "score": immersion[0],
            "passed": immersion[1],
            "reasons": immersion[2],
            "signals": immersion[3],
        },
    }

    overall = _finalize_overall(direct=direct, intent=intent, escalation=escalation, immersion=immersion)
    summary = _summarize(axes_out)

    raw_overall = dict(overall)
    gameplay_validation = summarize_gameplay_validation_for_turn(dt)
    gameplay_validation["raw_overall"] = raw_overall
    if gameplay_validation.get("excluded_from_scoring"):
        overall = {"score": 0, "rating": "weak", "passed": False}

    return {
        "version": SCHEMA_VERSION,
        "overall": overall,
        "axes": axes_out,
        "summary": summary,
        "gameplay_validation": gameplay_validation,
    }


def rollup_playability_gameplay_validation(turns_out: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate per-turn ``gameplay_validation`` blocks from ``evaluate_playability`` results."""
    dead_turn_count = 0
    infra_failure_count = 0
    exclusions: list[str] = []
    for row in turns_out:
        pe = row.get("playability_eval") if isinstance(row.get("playability_eval"), Mapping) else {}
        gv = pe.get("gameplay_validation") if isinstance(pe.get("gameplay_validation"), Mapping) else {}
        dead_turn_count += int(gv.get("dead_turn_count") or 0)
        infra_failure_count += int(gv.get("infra_failure_count") or 0)
        if not gv.get("run_valid", True):
            ir = gv.get("invalidation_reason")
            if isinstance(ir, str) and ir.strip():
                exclusions.append(ir.strip())
    all_valid = all(
        bool((t.get("playability_eval") or {}).get("gameplay_validation", {}).get("run_valid", True))
        for t in turns_out
    )
    return {
        "run_valid": bool(all_valid),
        "excluded_from_scoring": not bool(all_valid),
        "invalidation_reason": exclusions[0] if exclusions else None,
        "dead_turn_count": dead_turn_count,
        "infra_failure_count": infra_failure_count,
    }
