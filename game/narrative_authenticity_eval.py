"""Deterministic proof-layer scoring from shipped narrative authenticity telemetry.

Reads ``_final_emission_meta`` / NA merge fields produced by the emission pipeline.
Does **not** re-run :func:`game.narrative_authenticity.validate_narrative_authenticity` and does not call an LLM.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence, Set

from game.final_emission_meta import (
    NARRATIVE_AUTHENTICITY_FEM_KEYS,
    normalize_merged_na_telemetry_for_eval,
    read_dead_turn_from_gm_output,
    read_final_emission_meta_dict,
    summarize_gameplay_validation_for_turn,
)

_NA_KEYS = NARRATIVE_AUTHENTICITY_FEM_KEYS


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_float(x: Any) -> float | None:
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    return None


def _as_int(x: Any) -> int | None:
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(round(x))
    return None


def _reason_codes_from_meta(meta: Mapping[str, Any]) -> Set[str]:
    out: Set[str] = set()
    for key in ("narrative_authenticity_reason_codes", "narrative_authenticity_failure_reasons"):
        seq = meta.get(key)
        if isinstance(seq, Sequence) and not isinstance(seq, (str, bytes)):
            for x in seq:
                s = str(x).strip()
                if s:
                    out.add(s)
    return out


def _extract_final_emission_meta(response: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        return {}
    dbg = response.get("gm_output_debug")
    if isinstance(dbg, Mapping):
        lane = dbg.get("emission_debug_lane")
        if isinstance(lane, Mapping):
            fem = lane.get("_final_emission_meta")
            if isinstance(fem, Mapping):
                return dict(fem)
    gm = response.get("gm_output")
    if not isinstance(gm, Mapping):
        gm = response
    return read_final_emission_meta_dict(gm if isinstance(gm, Mapping) else None)


def _finalize_na_eval_with_dead_turn_policy(
    out: dict[str, Any],
    response: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Attach DTD1 gameplay_validation; strip positive NA scores when ``validation_playable`` is false."""
    dt = read_dead_turn_from_gm_output(response.get("gm_output") if isinstance(response, Mapping) else None)
    gv = summarize_gameplay_validation_for_turn(dt)
    if gv["excluded_from_scoring"]:
        gv = {
            **gv,
            "diagnostic_scores": dict(out.get("scores") or {}) if isinstance(out.get("scores"), dict) else {},
            "diagnostic_rumor_realism_axes": dict(out.get("rumor_realism_axes") or {})
            if isinstance(out.get("rumor_realism_axes"), dict)
            else {},
        }
        if isinstance(out.get("scores"), dict):
            for k in list(out["scores"].keys()):
                out["scores"][k] = 0
        if isinstance(out.get("rumor_realism_axes"), dict):
            for k in list(out["rumor_realism_axes"].keys()):
                out["rumor_realism_axes"][k] = 0
        if isinstance(out.get("rumor_realism_axis_reasons"), dict):
            for k, v in list(out["rumor_realism_axis_reasons"].items()):
                base = list(v) if isinstance(v, list) else []
                base.append("gameplay_excluded_non_playable_turn")
                out["rumor_realism_axis_reasons"][k] = list(dict.fromkeys(str(x) for x in base if str(x).strip()))
        out["passed"] = False
        merged_reasons = list(out.get("reasons") or [])
        merged_reasons.append("gameplay_excluded_non_playable_turn")
        out["reasons"] = list(dict.fromkeys(str(x) for x in merged_reasons if str(x).strip()))
        out["narrative_authenticity_verdict"] = "excluded_from_scoring"
    out["gameplay_validation"] = gv
    return out


def _merge_na_meta(
    *,
    meta: Mapping[str, Any] | None,
    response: Mapping[str, Any] | None,
) -> dict[str, Any]:
    fem = _extract_final_emission_meta(response)
    merged: dict[str, Any] = {k: fem[k] for k in _NA_KEYS if k in fem}
    if isinstance(meta, Mapping):
        for k, v in meta.items():
            if v is not None:
                merged[str(k)] = v
    return merged


def _gm_text(response: Mapping[str, Any] | None) -> str:
    if not isinstance(response, Mapping):
        return ""
    gm = response.get("gm_output")
    if isinstance(gm, Mapping):
        t = gm.get("player_facing_text")
        if isinstance(t, str):
            return t.strip()
    t2 = response.get("player_facing_text") or response.get("gm_text")
    return str(t2).strip() if isinstance(t2, str) else ""


def _clip_int(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def _supporting_metrics(meta: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in sorted(_NA_KEYS):
        if k not in meta:
            continue
        v = meta.get(k)
        if k == "narrative_authenticity_metrics" and isinstance(v, Mapping):
            out[k] = {str(k2): v[k2] for k2 in sorted(v.keys())[:24]}
        elif k == "narrative_authenticity_evidence" and isinstance(v, Mapping):
            out[k] = {str(k2): v[k2] for k2 in sorted(v.keys())[:16]}
        elif k == "narrative_authenticity_trace" and isinstance(v, Mapping):
            out[k] = {str(k2): v[k2] for k2 in sorted(v.keys())[:12]}
        elif k == "narrative_authenticity_relaxation_flags" and isinstance(v, Mapping):
            out[k] = {str(k2): v[k2] for k2 in sorted(v.keys())[:12]}
        else:
            out[k] = v
    return out


def _text_npc_grounding_signals(text: str) -> dict[str, Any]:
    low = text.lower()
    return {
        "has_quoted_dialogue": bool(re.search(r'["“][^"”]{4,}["”]', text)),
        "scene_anchor_hits": sum(
            1
            for pat in (
                re.compile(r"\b(captain|sergeant|guard|clerk|merchant|watch)\b", re.I),
                re.compile(r"\b(gate|yard|dock|lane|market|ledger|patrol)\b", re.I),
            )
            if pat.search(low)
        ),
    }


_RUMOR_ECHO_REASON_CODES: frozenset[str] = frozenset(
    {
        "rumor_repeats_recent_narration",
        "rumor_restates_scene_description",
        "rumor_uses_identical_phrasing_for_known_fact",
    }
)
_RUMOR_REALISM_REASON_CODES: frozenset[str] = frozenset(
    {
        "rumor_adds_no_new_signal",
        "secondhand_info_lacks_source_limitation",
        "secondhand_info_lacks_uncertainty_or_bias",
    }
)


def _classify_narrative_authenticity_verdict(
    merged: Mapping[str, Any],
    *,
    checked: bool,
    failed: bool,
    repaired: bool,
) -> str:
    """Explicit terminal / skip label for reporting (does not replace gate booleans)."""
    skip = merged.get("narrative_authenticity_skip_reason")
    if not checked:
        if isinstance(skip, str) and skip.strip():
            return "unchecked"
        return "unchecked"
    st_raw = merged.get("narrative_authenticity_status")
    st = str(st_raw).strip().lower() if isinstance(st_raw, str) else ""
    if st == "fail":
        return "fail"
    if st == "repaired":
        return "repaired_pass"
    if st == "relaxed":
        return "relaxed_pass"
    if st == "pass":
        return "clean_pass"
    if failed and not repaired:
        return "fail"
    if repaired:
        return "repaired_pass"
    if not failed and merged.get("narrative_authenticity_rumor_relaxed_low_signal") is True:
        return "relaxed_pass"
    if not failed:
        return "clean_pass"
    return "unchecked"


def _score_rumor_echo_control(
    *,
    verdict: str,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    metrics: Mapping[str, Any],
    na_trace: Mapping[str, Any],
) -> tuple[int, List[str]]:
    reasons: List[str] = []
    if verdict == "unchecked":
        return 3, ["na_eval_unchecked_neutral_rumor_echo_control"]
    if not checked:
        return 3, ["na_eval_not_checked_neutral_rumor_echo_control"]
    rumor_turn = bool(metrics.get("rumor_turn_active")) or bool(na_trace.get("rumor_turn_active"))
    if not rumor_turn:
        return 4, ["na_eval_no_rumor_turn_echo_axis_lenient"]
    echo_codes = codes & _RUMOR_ECHO_REASON_CODES
    if failed and not repaired and echo_codes:
        return 0, [f"na_eval_rumor_echo_unrepaired:{sorted(echo_codes)[0]}"]
    jo = _as_float(metrics.get("rumor_overlap_jaccard"))
    tg = _as_float(metrics.get("rumor_overlap_trigram"))
    score = 5
    if jo is not None and jo >= 0.62:
        score -= 2
        reasons.append("rumor_overlap_jaccard_elevated")
    elif jo is not None and jo >= 0.48:
        score -= 1
        reasons.append("rumor_overlap_jaccard_moderate")
    if tg is not None and tg >= 0.48:
        score -= 1
        reasons.append("rumor_overlap_trigram_elevated")
    if repaired and echo_codes:
        reasons.append("na_eval_repaired_rumor_echo_class")
    return _clip_int(score, 0, 5), reasons


def _score_secondhand_realism(
    *,
    verdict: str,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    metrics: Mapping[str, Any],
    evidence: Mapping[str, Any],
    na_trace: Mapping[str, Any],
) -> tuple[int, List[str]]:
    reasons: List[str] = []
    if verdict == "unchecked":
        return 3, ["na_eval_unchecked_neutral_secondhand_realism"]
    if not checked:
        return 3, ["na_eval_not_checked_neutral_secondhand_realism"]
    rumor_turn = bool(metrics.get("rumor_turn_active")) or bool(na_trace.get("rumor_turn_active"))
    if not rumor_turn:
        return 4, ["na_eval_no_rumor_turn_secondhand_axis_lenient"]
    rr_codes = codes & _RUMOR_REALISM_REASON_CODES
    if failed and not repaired and rr_codes:
        return 0, [f"na_eval_secondhand_unrepaired:{sorted(rr_codes)[0]}"]
    sig = _as_int(metrics.get("rumor_signal_count"))
    if sig is None:
        return 3, ["na_eval_rumor_signal_count_absent"]
    if sig >= 2:
        reasons.append("rumor_signal_count_ge_2")
        return 5, reasons
    if sig == 1:
        missing = evidence.get("rumor_missing_realism_categories")
        if isinstance(missing, list) and missing:
            reasons.append("rumor_missing_realism_categories_present")
        return 4, reasons
    reasons.append("rumor_signal_count_zero")
    return 2, reasons


def _score_rumor_repair_success(
    *,
    verdict: str,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    merged: Mapping[str, Any],
) -> tuple[int, List[str]]:
    reasons: List[str] = []
    if verdict == "unchecked":
        return 3, ["na_eval_unchecked_neutral_rumor_repair_success"]
    if not checked:
        return 3, ["na_eval_not_checked_neutral_rumor_repair_success"]
    mode = merged.get("narrative_authenticity_repair_mode")
    modes = merged.get("narrative_authenticity_repair_modes")
    if verdict == "repaired_pass":
        if isinstance(mode, str) and mode.strip():
            reasons.append(f"na_eval_repair_mode:{mode.strip()}")
        elif isinstance(modes, Sequence) and not isinstance(modes, (str, bytes)) and modes:
            reasons.append(f"na_eval_repair_modes:{modes[0]}")
        return 5, reasons
    if verdict == "fail":
        return 0, ["na_eval_fail_terminal_rumor_repair_success"]
    rumor_hits = bool(codes & (_RUMOR_ECHO_REASON_CODES | _RUMOR_REALISM_REASON_CODES))
    if rumor_hits and failed and repaired:
        return 4, ["na_eval_repaired_other_axes_rumor_context"]
    return 5, reasons


def _score_rumor_relaxation_correctness(
    *,
    verdict: str,
    checked: bool,
    failed: bool,
    merged: Mapping[str, Any],
    na_trace: Mapping[str, Any],
) -> tuple[int, List[str]]:
    reasons: List[str] = []
    if verdict == "unchecked":
        return 3, ["na_eval_unchecked_neutral_rumor_relaxation_correctness"]
    if not checked:
        return 3, ["na_eval_not_checked_neutral_rumor_relaxation_correctness"]
    relaxed_meta = merged.get("narrative_authenticity_rumor_relaxed_low_signal")
    top_flags = merged.get("narrative_authenticity_relaxation_flags")
    nested_flags = na_trace.get("rumor_relaxation_flags")
    has_flags = (isinstance(top_flags, Mapping) and any(top_flags.values())) or (
        isinstance(nested_flags, Mapping) and any(nested_flags.values())
    )
    if verdict == "relaxed_pass":
        if relaxed_meta is not True:
            reasons.append("na_eval_relaxed_pass_missing_rumor_relaxed_low_signal_flag")
            return 3, reasons
        if not has_flags:
            reasons.append("na_eval_relaxed_pass_missing_relaxation_flags")
            return 3, reasons
        return 5, reasons
    if verdict == "fail" and has_flags:
        reasons.append("na_eval_relaxation_flags_present_under_fail_terminal")
        return 3, reasons
    if verdict == "clean_pass" and relaxed_meta is True:
        reasons.append("na_eval_clean_pass_with_rumor_relaxed_low_signal_inconsistent")
        return 2, reasons
    if has_flags and relaxed_meta is not True and verdict == "clean_pass":
        reasons.append("na_eval_relaxation_flags_without_relaxed_terminal_or_meta")
        return 3, reasons
    return 5, reasons


def _score_rumor_state_hygiene(
    *,
    verdict: str,
    checked: bool,
    merged: Mapping[str, Any],
    metrics: Mapping[str, Any],
    na_trace: Mapping[str, Any],
) -> tuple[int, List[str]]:
    reasons: List[str] = []
    if verdict == "unchecked":
        skip = merged.get("narrative_authenticity_skip_reason")
        if isinstance(skip, str) and skip.strip():
            reasons.append(f"na_eval_skip_reason_recorded:{skip.strip()}")
            return 4, reasons
        return 2, ["na_eval_unchecked_without_skip_reason"]
    if not checked:
        return 3, ["na_eval_not_checked_neutral_rumor_state_hygiene"]
    m_rt = metrics.get("rumor_turn_active")
    t_rt = na_trace.get("rumor_turn_active")
    if m_rt is True and t_rt is not True:
        reasons.append("na_eval_rumor_turn_active_true_in_metrics_but_absent_in_trace")
        return 2, reasons
    if t_rt is True and m_rt is not True:
        reasons.append("na_eval_rumor_turn_active_true_in_trace_but_absent_or_false_in_metrics")
        return 2, reasons
    if verdict in {"clean_pass", "relaxed_pass", "repaired_pass"}:
        return 5, reasons
    if verdict == "fail":
        return 1, ["na_eval_fail_terminal_rumor_state_hygiene"]
    return 3, reasons


def _score_signal_gain(
    *,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    metrics: Mapping[str, Any],
    text_signals: Mapping[str, Any],
) -> tuple[int, List[str]]:
    reasons: List[str] = []
    if not checked:
        return 3, ["narrative_authenticity_not_checked_neutral_signal_gain"]
    gfs = _as_float(metrics.get("generic_filler_score"))
    sm = _as_int(metrics.get("signal_markers_detected")) or 0
    if failed and not repaired:
        if "follow_up_missing_signal_shadow_response_delta" in codes:
            return 1, ["na_reason_follow_up_missing_signal_shadow_response_delta"]
        if "low_signal_generic_reply" in codes:
            return 0, ["na_reason_low_signal_generic_reply"]
        return 1, ["na_gate_failed_signal_gain"]
    score = 5
    if gfs is not None:
        if gfs >= 0.52:
            score -= 3
            reasons.append("generic_filler_score_ge_0_52")
        elif gfs >= 0.38:
            score -= 2
            reasons.append("generic_filler_score_ge_0_38")
        elif gfs >= 0.25:
            score -= 1
            reasons.append("generic_filler_score_ge_0_25")
    if sm >= 2:
        score = 5
        reasons.append("signal_markers_detected_ge_2")
    elif sm == 1 and (gfs is None or gfs < 0.32):
        score = max(score, 4)
        reasons.append("signal_markers_detected_eq_1_low_filler")
    if repaired:
        reasons.append("narrative_authenticity_repaired_signal_context")
    if bool(text_signals.get("has_digit")) and score < 5:
        score += 1
    return _clip_int(score, 0, 5), reasons


def _score_anti_echoing(
    *,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    metrics: Mapping[str, Any],
) -> tuple[int, List[str]]:
    if not checked:
        return 3, ["narrative_authenticity_not_checked_neutral_anti_echoing"]
    if failed and not repaired and "dialogue_echoes_prior_narration" in codes:
        return 0, ["na_reason_dialogue_echoes_prior_narration"]
    if failed and not repaired and "adjacent_phrase_reuse" in codes:
        return 1, ["na_reason_adjacent_phrase_reuse"]
    qov = _as_float(metrics.get("quote_narration_overlap"))
    qtg = _as_float(metrics.get("quote_narration_trigram_overlap"))
    adj = _as_float(metrics.get("adjacent_phrase_overlap"))
    ap = _as_int(metrics.get("adjacent_structural_pairs"))
    score = 5
    reasons: List[str] = []
    if qov is not None and qov >= 0.5:
        score -= 2
        reasons.append("quote_narration_overlap_high")
    if qtg is not None and qtg >= 0.4:
        score -= 1
        reasons.append("quote_narration_trigram_overlap_elevated")
    if adj is not None and adj >= 0.34:
        score -= 2
        reasons.append("adjacent_phrase_overlap_elevated")
    elif ap is not None and ap >= 2:
        score -= 1
        reasons.append("adjacent_structural_pairs_ge_2")
    if repaired and (
        "dialogue_echoes_prior_narration" in codes or "adjacent_phrase_reuse" in codes
    ):
        reasons.append("narrative_authenticity_repaired_echo_class")
    return _clip_int(score, 0, 5), reasons


def _score_followup_evolution(
    *,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    metrics: Mapping[str, Any],
    turn_packet: Mapping[str, Any] | None,
) -> tuple[int, List[str]]:
    prior_gm = ""
    if isinstance(turn_packet, Mapping):
        prior_gm = str(turn_packet.get("prior_gm_text") or "").strip()
    if not checked:
        return 3, ["narrative_authenticity_not_checked_neutral_followup"]
    if failed and not repaired and "follow_up_stale_restatement" in codes:
        return 0, ["na_reason_follow_up_stale_restatement"]
    if failed and not repaired and "follow_up_missing_signal_shadow_response_delta" in codes:
        return 1, ["na_reason_follow_up_missing_signal_shadow_response_delta"]
    fo = _as_float(metrics.get("followup_overlap"))
    sm = _as_int(metrics.get("signal_markers_detected")) or 0
    if not prior_gm:
        return 4, ["no_prior_gm_followup_axis_lenient"]
    score = 5
    reasons: List[str] = []
    if fo is not None:
        if fo >= 0.68:
            score -= 3
            reasons.append("followup_overlap_ge_0_68")
        elif fo >= 0.55:
            score -= 1
            reasons.append("followup_overlap_ge_0_55")
    if sm >= 1:
        score = min(5, score + 1)
        reasons.append("followup_signal_markers_present")
    if repaired:
        reasons.append("narrative_authenticity_repaired_followup_context")
    return _clip_int(score, 0, 5), reasons


def _score_non_generic_specificity(
    *,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    metrics: Mapping[str, Any],
    text: str,
) -> tuple[int, List[str]]:
    if not checked:
        return 3, ["narrative_authenticity_not_checked_neutral_specificity"]
    if failed and not repaired and "low_signal_generic_reply" in codes:
        return 0, ["na_reason_low_signal_generic_reply"]
    gfs = _as_float(metrics.get("generic_filler_score"))
    wc = len(re.findall(r"[A-Za-z']+", text))
    score = 5
    reasons: List[str] = []
    if gfs is not None:
        if gfs >= 0.52:
            score = min(score, 1)
            reasons.append("generic_filler_score_ge_0_52")
        elif gfs >= 0.38:
            score = min(score, 3)
            reasons.append("generic_filler_score_ge_0_38")
        elif gfs >= 0.25:
            score = min(score, 4)
            reasons.append("generic_filler_score_ge_0_25")
    if wc >= 28 and gfs is not None and gfs < 0.35:
        score = max(score, 4)
        reasons.append("substantive_word_count")
    if '"' in text or "“" in text:
        score = max(score, 4)
        reasons.append("quoted_material_present")
    if repaired:
        reasons.append("narrative_authenticity_repaired_specificity_context")
    return _clip_int(score, 0, 5), reasons


def _score_npc_voice_grounding(
    *,
    checked: bool,
    failed: bool,
    repaired: bool,
    codes: Set[str],
    text: str,
    text_signals: Mapping[str, Any],
) -> tuple[int, List[str]]:
    if not checked:
        return 3, ["narrative_authenticity_not_checked_neutral_voice"]
    if failed and not repaired and "non_diegetic_meta_voice" in codes:
        return 0, ["na_reason_non_diegetic_meta_voice"]
    sig = _text_npc_grounding_signals(text)
    score = 3
    reasons: List[str] = []
    if sig["has_quoted_dialogue"]:
        score += 2
        reasons.append("quoted_dialogue_detected")
    if int(sig.get("scene_anchor_hits") or 0) >= 1:
        score += 1
        reasons.append("scene_or_role_anchor")
    if bool(text_signals.get("has_lead_snippet")):
        score = min(5, score + 1)
        reasons.append("next_lead_snippet_heuristic")
    if repaired:
        reasons.append("narrative_authenticity_repaired_voice_context")
    return _clip_int(score, 0, 5), reasons


def evaluate_narrative_authenticity(
    turn_packet: Mapping[str, Any] | None,
    response: Mapping[str, Any] | None,
    meta: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Score one turn using NA telemetry (and light text flags). Stable, deterministic schema.

    ``meta`` may be partial; missing NA keys are filled from ``response['gm_output']['_final_emission_meta']``.
    ``turn_packet`` may include ``prior_gm_text`` / ``prior_player_prompt`` for lenient follow-up axis context.
    """
    merged = normalize_merged_na_telemetry_for_eval(_merge_na_meta(meta=meta, response=response))
    text = _gm_text(response)
    metrics = merged.get("narrative_authenticity_metrics")
    metrics_d = _safe_mapping(metrics)

    checked = bool(merged.get("narrative_authenticity_checked"))
    failed = bool(merged.get("narrative_authenticity_failed"))
    repaired = bool(merged.get("narrative_authenticity_repaired") or merged.get("narrative_authenticity_repair_applied"))
    codes = _reason_codes_from_meta(merged)

    has_fem_key = bool(_extract_final_emission_meta(response))
    has_na_in_meta = bool(meta and any(k in meta for k in _NA_KEYS))
    if not has_fem_key and not has_na_in_meta:
        return _finalize_na_eval_with_dead_turn_policy(
            {
                "passed": False,
                "narrative_authenticity_verdict": "missing_telemetry",
                "scores": {
                    "signal_gain": 0,
                    "anti_echoing": 0,
                    "followup_evolution": 0,
                    "non_generic_specificity": 0,
                    "npc_voice_grounding": 0,
                },
                "rumor_realism_axes": {
                    "rumor_echo_control": 0,
                    "secondhand_realism": 0,
                    "rumor_repair_success": 0,
                    "rumor_relaxation_correctness": 0,
                    "rumor_state_hygiene": 0,
                },
                "rumor_realism_axis_reasons": {
                    "rumor_echo_control": ["missing_narrative_authenticity_telemetry"],
                    "secondhand_realism": ["missing_narrative_authenticity_telemetry"],
                    "rumor_repair_success": ["missing_narrative_authenticity_telemetry"],
                    "rumor_relaxation_correctness": ["missing_narrative_authenticity_telemetry"],
                    "rumor_state_hygiene": ["missing_narrative_authenticity_telemetry"],
                },
                "reasons": ["missing_narrative_authenticity_telemetry"],
                "supporting_metrics": {},
            },
            response,
        )

    text_signals: dict[str, Any] = {
        "has_digit": bool(re.search(r"\b\d+\b", text)),
        "has_lead_snippet": bool(
            re.search(
                r"\b(try|ask|check|go to|head to|visit|east|west|north|south)\b",
                text,
                re.IGNORECASE,
            )
        ),
    }

    s1, r1 = _score_signal_gain(
        checked=checked, failed=failed, repaired=repaired, codes=codes, metrics=metrics_d, text_signals=text_signals
    )
    s2, r2 = _score_anti_echoing(
        checked=checked, failed=failed, repaired=repaired, codes=codes, metrics=metrics_d
    )
    s3, r3 = _score_followup_evolution(
        checked=checked,
        failed=failed,
        repaired=repaired,
        codes=codes,
        metrics=metrics_d,
        turn_packet=turn_packet,
    )
    s4, r4 = _score_non_generic_specificity(
        checked=checked, failed=failed, repaired=repaired, codes=codes, metrics=metrics_d, text=text
    )
    s5, r5 = _score_npc_voice_grounding(
        checked=checked, failed=failed, repaired=repaired, codes=codes, text=text, text_signals=text_signals
    )

    scores = {
        "signal_gain": s1,
        "anti_echoing": s2,
        "followup_evolution": s3,
        "non_generic_specificity": s4,
        "npc_voice_grounding": s5,
    }
    reasons = [*r1, *r2, *r3, *r4, *r5]
    if checked and failed and not repaired:
        reasons.insert(0, "narrative_authenticity_gate_failed_unrepaired")
    skip = merged.get("narrative_authenticity_skip_reason")
    if isinstance(skip, str) and skip.strip() and not checked:
        reasons.append(f"narrative_authenticity_skip_reason:{skip.strip()}")

    avg = sum(scores.values()) / 5.0
    passed = (not (checked and failed and not repaired)) and avg >= 3.0 and min(scores.values()) >= 2

    verdict = _classify_narrative_authenticity_verdict(merged, checked=checked, failed=failed, repaired=repaired)
    na_trace_d = _safe_mapping(merged.get("narrative_authenticity_trace"))
    evidence_d = _safe_mapping(merged.get("narrative_authenticity_evidence"))

    rx1, z1 = _score_rumor_echo_control(
        verdict=verdict,
        checked=checked,
        failed=failed,
        repaired=repaired,
        codes=codes,
        metrics=metrics_d,
        na_trace=na_trace_d,
    )
    rx2, z2 = _score_secondhand_realism(
        verdict=verdict,
        checked=checked,
        failed=failed,
        repaired=repaired,
        codes=codes,
        metrics=metrics_d,
        evidence=evidence_d,
        na_trace=na_trace_d,
    )
    rx3, z3 = _score_rumor_repair_success(
        verdict=verdict,
        checked=checked,
        failed=failed,
        repaired=repaired,
        codes=codes,
        merged=merged,
    )
    rx4, z4 = _score_rumor_relaxation_correctness(
        verdict=verdict,
        checked=checked,
        failed=failed,
        merged=merged,
        na_trace=na_trace_d,
    )
    rx5, z5 = _score_rumor_state_hygiene(
        verdict=verdict,
        checked=checked,
        merged=merged,
        metrics=metrics_d,
        na_trace=na_trace_d,
    )
    rumor_axes = {
        "rumor_echo_control": rx1,
        "secondhand_realism": rx2,
        "rumor_repair_success": rx3,
        "rumor_relaxation_correctness": rx4,
        "rumor_state_hygiene": rx5,
    }
    rumor_axis_reasons = {
        "rumor_echo_control": z1,
        "secondhand_realism": z2,
        "rumor_repair_success": z3,
        "rumor_relaxation_correctness": z4,
        "rumor_state_hygiene": z5,
    }

    out: dict[str, Any] = {
        "passed": bool(passed),
        "narrative_authenticity_verdict": verdict,
        "scores": scores,
        "rumor_realism_axes": rumor_axes,
        "rumor_realism_axis_reasons": rumor_axis_reasons,
        "reasons": list(dict.fromkeys(str(x) for x in reasons if str(x).strip())),
        "supporting_metrics": _supporting_metrics(merged),
    }
    return _finalize_na_eval_with_dead_turn_policy(out, response)
