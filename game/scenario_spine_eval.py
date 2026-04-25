"""Deterministic offline health evaluation for Scenario-Spine sessions (no API calls)."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from game.scenario_spine import ScenarioSpine, scenario_spine_from_dict
from game.scenario_spine_opening_convergence import evaluate_opening_convergence_for_turn_rows

# Stable per-turn transcript metadata envelope (scenario-spine validation + offline eval).
TRANSCRIPT_TURN_META_ENVELOPE_KEYS: tuple[str, ...] = (
    "narration_seam",
    "opening_convergence",
    "response_type_contract",
    "final_emission_meta",
    "planner_convergence",
    "scenario_spine",
)
SCENARIO_SPINE_IDENTITY_KEYS: tuple[str, ...] = (
    "spine_id",
    "branch_id",
    "turn_id",
    "turn_index",
    "smoke",
    "max_turns",
    "resume_entry_first_turn",
    "artifact_schema_version",
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ensure_transcript_turn_meta_dict(meta: Any) -> dict[str, Any] | None:
    """Return JSON-friendly meta with required envelope keys preserved (never drop runner fields).

    If *meta* is not a mapping, returns None (legacy rows without metadata).
    """
    if not isinstance(meta, Mapping):
        return None
    base: dict[str, Any] = {str(k): meta[k] for k in sorted(meta, key=str)}
    for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS:
        base.setdefault(k, None)
    ss_raw = base.get("scenario_spine")
    if isinstance(ss_raw, Mapping):
        ss2: dict[str, Any] = {str(k): ss_raw[k] for k in sorted(ss_raw, key=str)}
        for sk in SCENARIO_SPINE_IDENTITY_KEYS:
            ss2.setdefault(sk, None)
        base["scenario_spine"] = {str(k): ss2[k] for k in sorted(ss2, key=str)}
    else:
        base["scenario_spine"] = {sk: None for sk in SCENARIO_SPINE_IDENTITY_KEYS}
    return base


def minimal_complete_transcript_turn_meta(
    *,
    spine_id: str,
    branch_id: str,
    turn_id: str,
    turn_index: int,
    smoke: bool = False,
    max_turns: int | None = None,
    resume_entry_first_turn: bool = False,
    artifact_schema_version: int = 1,
) -> dict[str, Any]:
    """Build a **source**-complete per-turn ``meta`` mapping (all envelope + identity keys present).

    Values may be ``None``; completeness checks key **presence** in the serialized row, not nullability.
    """
    ss = {
        "spine_id": spine_id,
        "branch_id": branch_id,
        "turn_id": str(turn_id),
        "turn_index": int(turn_index),
        "smoke": bool(smoke),
        "max_turns": max_turns,
        "resume_entry_first_turn": bool(resume_entry_first_turn),
        "artifact_schema_version": int(artifact_schema_version),
    }
    return {
        "narration_seam": None,
        "opening_convergence": None,
        "response_type_contract": None,
        "final_emission_meta": None,
        "planner_convergence": None,
        "scenario_spine": ss,
    }


def _turn_index_for_metadata_row(fallback_index: int, raw: Mapping[str, Any]) -> int:
    tid = raw.get("turn_index")
    if tid is None:
        return int(fallback_index)
    try:
        return int(tid)
    except (TypeError, ValueError):
        return int(fallback_index)


def evaluate_transcript_metadata_completeness(
    raw_turns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Artifact-level check: required keys must exist on **source** rows (before normalization).

    ``ensure_transcript_turn_meta_dict`` / ``_normalize_turn_row`` fill missing keys with placeholders;
    this function inspects the original ``meta`` object only so omissions stay visible.
    """
    turns_checked = len(raw_turns)
    missing_by_key: dict[str, int] = {k: 0 for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS}
    first_missing_turn_by_key: dict[str, int] = {}
    missing_ss_by_key: dict[str, int] = {k: 0 for k in SCENARIO_SPINE_IDENTITY_KEYS}
    first_missing_turn_ss: dict[str, int] = {}
    turns_with_any_issue: set[int] = set()

    def _bump_envelope_key(key: str, turn_idx: int) -> None:
        missing_by_key[key] = int(missing_by_key[key]) + 1
        first_missing_turn_by_key.setdefault(key, int(turn_idx))
        turns_with_any_issue.add(int(turn_idx))

    def _bump_ss_key(sk: str, turn_idx: int) -> None:
        missing_ss_by_key[sk] = int(missing_ss_by_key[sk]) + 1
        first_missing_turn_ss.setdefault(sk, int(turn_idx))
        turns_with_any_issue.add(int(turn_idx))

    def _all_envelope_missing(turn_idx: int) -> None:
        for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS:
            _bump_envelope_key(k, turn_idx)

    def _all_ss_identity_missing(turn_idx: int) -> None:
        for sk in SCENARIO_SPINE_IDENTITY_KEYS:
            _bump_ss_key(sk, turn_idx)

    for i, raw in enumerate(raw_turns):
        turn_idx = _turn_index_for_metadata_row(i, raw)

        if "meta" not in raw:
            _all_envelope_missing(turn_idx)
            _all_ss_identity_missing(turn_idx)
            continue

        meta_src = raw["meta"]
        if meta_src is None or not isinstance(meta_src, Mapping):
            _all_envelope_missing(turn_idx)
            _all_ss_identity_missing(turn_idx)
            continue

        meta_m = meta_src
        for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS:
            if k not in meta_m:
                _bump_envelope_key(k, turn_idx)

        if "scenario_spine" not in meta_m:
            _all_ss_identity_missing(turn_idx)
            continue

        ss_raw = meta_m["scenario_spine"]
        if ss_raw is None or not isinstance(ss_raw, Mapping):
            _all_ss_identity_missing(turn_idx)
            continue

        ss_m = ss_raw
        for sk in SCENARIO_SPINE_IDENTITY_KEYS:
            if sk not in ss_m:
                _bump_ss_key(sk, turn_idx)

    turns_missing_meta = len(turns_with_any_issue)
    passed = turns_missing_meta == 0

    return {
        "turns_checked": turns_checked,
        "turns_missing_meta": turns_missing_meta,
        "missing_by_key": {k: int(missing_by_key[k]) for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS},
        "first_missing_turn_by_key": dict(sorted(first_missing_turn_by_key.items(), key=lambda kv: str(kv[0]))),
        "missing_scenario_spine_identity_by_key": {
            k: int(missing_ss_by_key[k]) for k in SCENARIO_SPINE_IDENTITY_KEYS
        },
        "first_missing_turn_by_scenario_spine_identity_key": dict(
            sorted(first_missing_turn_ss.items(), key=lambda kv: str(kv[0])),
        ),
        "metadata_completeness_passed": passed,
    }


def _default_metadata_completeness_session_health() -> dict[str, Any]:
    empty_miss = {k: 0 for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS}
    empty_ss = {k: 0 for k in SCENARIO_SPINE_IDENTITY_KEYS}
    return {
        "turns_checked": 0,
        "turns_missing_meta": 0,
        "missing_by_key": empty_miss,
        "first_missing_turn_by_key": {},
        "missing_scenario_spine_identity_by_key": empty_ss,
        "first_missing_turn_by_scenario_spine_identity_key": {},
        "metadata_completeness_passed": True,
    }


def _metadata_completeness_failure_detail(block: Mapping[str, Any]) -> str:
    n_miss = int(block.get("turns_missing_meta") or 0)
    fb = block.get("first_missing_turn_by_key") or {}
    first_env = min(fb.values()) if fb else None
    fss = block.get("first_missing_turn_by_scenario_spine_identity_key") or {}
    first_ss = min(fss.values()) if fss else None
    parts = [f"{n_miss} turn(s) with metadata gaps"]
    if first_env is not None:
        parts.append(f"first envelope gap turn_index={first_env}")
    if first_ss is not None:
        parts.append(f"first scenario_spine identity gap turn_index={first_ss}")
    return "; ".join(parts)


def evaluate_scenario_spine_session(
    spine: Mapping[str, Any] | ScenarioSpine,
    branch_id: str,
    turns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate recorded turns against a spine; result is JSON-serializable."""
    model = _coerce_spine(spine)
    resolved_branch = _resolve_branch_id(model, branch_id)
    if resolved_branch is None:
        return _error_result(
            model.spine_id,
            branch_id,
            turns,
            f"unknown_branch_id:{branch_id}",
        )
    norm_turns = [_normalize_turn_row(i, t) for i, t in enumerate(turns)]
    ctx = _EvalContext(
        spine=model,
        branch_id=resolved_branch,
        turns=tuple(norm_turns),
        raw_turns=tuple(turns),
    )
    return ctx.run()


# ---------------------------------------------------------------------------
# Spine / turn normalization
# ---------------------------------------------------------------------------


_BRANCH_ALIASES: dict[str, str] = {
    "social_investigation": "branch_social_inquiry",
    "direct_intrusion": "branch_direct_intrusion",
    "cautious_observation": "branch_cautious_observe",
}

def _coerce_spine(spine: Mapping[str, Any] | ScenarioSpine) -> ScenarioSpine:
    if isinstance(spine, ScenarioSpine):
        return spine
    if not isinstance(spine, Mapping):
        msg = "spine must be a Mapping or ScenarioSpine"
        raise TypeError(msg)
    return scenario_spine_from_dict(spine)


def _resolve_branch_id(spine: ScenarioSpine, branch_id: str) -> str | None:
    bid = str(branch_id).strip()
    ids = {b.branch_id for b in spine.branches}
    if bid in ids:
        return bid
    mapped = _BRANCH_ALIASES.get(bid)
    if mapped and mapped in ids:
        return mapped
    return None


def _normalize_turn_row(turn_index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    gm = row.get("gm_text")
    if gm is None or (isinstance(gm, str) and not gm.strip()):
        alt = row.get("gm_output")
        gm = alt if isinstance(alt, str) else ""
    gm_s = str(gm) if gm is not None else ""

    player = row.get("player_prompt")
    if player is None or (isinstance(player, str) and not player.strip()):
        pt = row.get("player_text")
        player = pt if isinstance(pt, str) else ""
    player_s = str(player) if player is not None else ""

    tid = row.get("turn_id")
    if tid is None:
        tid = row.get("turn_index")
    tid_s = str(tid) if tid is not None else f"idx_{turn_index}"

    api_ok = row.get("api_ok")
    if api_ok is None:
        api_ok = True
    elif not isinstance(api_ok, bool):
        api_ok = bool(api_ok)

    meta_out = ensure_transcript_turn_meta_dict(row.get("meta"))

    return {
        "turn_index": int(turn_index),
        "turn_id": tid_s,
        "player_text": player_s,
        "gm_text": gm_s,
        "api_ok": api_ok,
        "meta": meta_out,
    }


def _norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _concat_gm(turns: Sequence[Mapping[str, Any]], end_inclusive: int) -> str:
    parts: list[str] = []
    for t in turns:
        if t["turn_index"] <= end_inclusive:
            parts.append(str(t["gm_text"]))
    return "\n".join(parts)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def _normalize_branch_transcripts_input(
    branch_transcripts_or_summaries: Mapping[str, Sequence[Mapping[str, Any]]]
    | Sequence[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    if isinstance(branch_transcripts_or_summaries, Mapping):
        return {str(k): list(v) for k, v in sorted(branch_transcripts_or_summaries.items(), key=lambda kv: str(kv[0]))}
    if isinstance(branch_transcripts_or_summaries, (str, bytes)):
        msg = "branch_transcripts_or_summaries must be a mapping or sequence of mappings"
        raise TypeError(msg)
    if not isinstance(branch_transcripts_or_summaries, Sequence):
        msg = "branch_transcripts_or_summaries must be a mapping or sequence"
        raise TypeError(msg)
    out: dict[str, list[Mapping[str, Any]]] = {}
    for i, item in enumerate(branch_transcripts_or_summaries):
        if not isinstance(item, Mapping):
            msg = f"branch entry {i} must be a mapping"
            raise TypeError(msg)
        bid = item.get("branch_id")
        if not isinstance(bid, str) or not bid.strip():
            msg = f"branch entry {i} needs non-empty branch_id"
            raise ValueError(msg)
        turns = item.get("turns")
        if not isinstance(turns, Sequence) or isinstance(turns, (str, bytes)):
            msg = f"branch entry {i} needs turns sequence"
            raise TypeError(msg)
        out[str(bid).strip()] = list(turns)
    return dict(sorted(out.items()))


def _final_window_gm(turns: Sequence[Mapping[str, Any]]) -> str:
    n = len(turns)
    if n == 0:
        return ""
    span = max(3, max(1, n // 5))
    start = max(0, n - span)
    parts = [str(turns[i]["gm_text"]) for i in range(start, n)]
    return _norm_text("\n".join(parts))


def _token_jaccard(a: str, b: str) -> float:
    ta = set(_norm_text(a).split())
    tb = set(_norm_text(b).split())
    if not ta and not tb:
        return 1.0
    inter = len(ta & tb)
    union = len(ta | tb) or 1
    return inter / union


def _branch_player_concat(turns: Sequence[Mapping[str, Any]]) -> str:
    return _norm_text(" ".join(str(t["player_text"]) for t in turns))


_CONSEQUENCE_LEXICON: tuple[tuple[str, str], ...] = (
    ("outcome_patrol", "missing patrol"),
    ("outcome_patrol", "patrol route"),
    ("outcome_intrusion", "forced entry"),
    ("outcome_intrusion", "blade drawn"),
    ("outcome_negotiation", "negotiation"),
    ("outcome_negotiation", "parley"),
    ("outcome_census", "census lockdown"),
    ("outcome_census", "census lines"),
    ("outcome_arrest", "arrest"),
    ("outcome_arrest", "detained"),
    ("outcome_flee", "withdraw"),
    ("outcome_flee", "retreat"),
)


def _consequence_term_hits(norm_text: str) -> frozenset[str]:
    hits: set[str] = set()
    for tag, needle in _CONSEQUENCE_LEXICON:
        if needle in norm_text:
            hits.add(tag)
    return frozenset(hits)


def _detect_shared_prompt_bleed(turns_by: dict[str, tuple[dict[str, Any], ...]]) -> bool:
    ids = sorted(turns_by)
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            gm_b = _norm_text("\n".join(str(t["gm_text"]) for t in turns_by[b]))
            gm_a = _norm_text("\n".join(str(t["gm_text"]) for t in turns_by[a]))
            for t in turns_by[a]:
                p = _norm_text(str(t["player_text"]))
                if len(p) >= 24 and p in gm_b:
                    return True
            for t in turns_by[b]:
                p = _norm_text(str(t["player_text"]))
                if len(p) >= 24 and p in gm_a:
                    return True
    return False


def evaluate_scenario_spine_branch_divergence(
    spine: Mapping[str, Any] | ScenarioSpine,
    branch_transcripts_or_summaries: Mapping[str, Sequence[Mapping[str, Any]]]
    | Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare multiple branch transcripts for deterministic divergence (no model calls).

    ``branch_transcripts_or_summaries`` may be:
    - a mapping ``branch_id -> sequence of turn rows`` (same shape as session rows), or
    - a sequence of ``{"branch_id": str, "turns": [...]}`` objects.
    """
    model = _coerce_spine(spine)
    by_branch = _normalize_branch_transcripts_input(branch_transcripts_or_summaries)
    branch_ids = sorted(by_branch)
    reason_codes: list[str] = []
    if len(branch_ids) < 2:
        out = {
            "schema_version": 1,
            "scenario_id": model.spine_id,
            "same_start_state": True,
            "branches_compared": branch_ids,
            "distinct_outcomes_detected": False,
            "divergence_score": 0.0,
            "shared_prompt_bleed_detected": False,
            "reason_codes": ["insufficient_branches"],
        }
        return _jsonable(out)

    spine_branch_ids = {b.branch_id for b in model.branches}
    unknown = sorted(bid for bid in branch_ids if bid not in spine_branch_ids)
    if unknown:
        reason_codes.append(f"unknown_branch_ids:{','.join(unknown)}")

    turns_by: dict[str, tuple[dict[str, Any], ...]] = {
        bid: tuple(_normalize_turn_row(j, row) for j, row in enumerate(by_branch[bid])) for bid in branch_ids
    }

    full_texts = {
        bid: _norm_text("\n".join(str(t["gm_text"]) for t in turns_by[bid])) for bid in branch_ids
    }
    final_windows = {bid: _final_window_gm(turns_by[bid]) for bid in branch_ids}

    pairwise_full: list[float] = []
    pairwise_final: list[float] = []
    cons_sets = {bid: _consequence_term_hits(full_texts[bid]) for bid in branch_ids}
    for i, a in enumerate(branch_ids):
        for b in branch_ids[i + 1 :]:
            pairwise_full.append(_token_jaccard(full_texts[a], full_texts[b]))
            pairwise_final.append(_token_jaccard(final_windows[a], final_windows[b]))

    avg_full_sim = sum(pairwise_full) / len(pairwise_full) if pairwise_full else 1.0
    avg_final_sim = sum(pairwise_final) / len(pairwise_final) if pairwise_final else 1.0

    near_identical = avg_full_sim >= 0.93 and min(pairwise_full, default=1.0) >= 0.88
    if near_identical:
        reason_codes.append("near_identical_branch_transcripts")

    distinct = False
    if not near_identical:
        for i, a in enumerate(branch_ids):
            for b in branch_ids[i + 1 :]:
                if _token_jaccard(final_windows[a], final_windows[b]) <= 0.78:
                    distinct = True
                    break
                if len(cons_sets[a] ^ cons_sets[b]) >= 2:
                    distinct = True
                    break
            if distinct:
                break
        if not distinct:
            for i, a in enumerate(branch_ids):
                for b in branch_ids[i + 1 :]:
                    pa = _branch_player_concat(turns_by[a])
                    pb = _branch_player_concat(turns_by[b])
                    if _token_jaccard(pa, pb) <= 0.55:
                        distinct = True
                        break
                if distinct:
                    break

    bleed = _detect_shared_prompt_bleed(turns_by)
    if bleed:
        reason_codes.append("shared_prompt_bleed")

    raw_div = (1.0 - avg_full_sim) * 0.55 + (1.0 - avg_final_sim) * 0.45
    if near_identical:
        divergence_score = round(min(0.08, raw_div * 0.25), 4)
    else:
        divergence_score = round(max(0.0, min(1.0, raw_div)), 4)

    out = {
        "schema_version": 1,
        "scenario_id": model.spine_id,
        "same_start_state": True,
        "branches_compared": branch_ids,
        "distinct_outcomes_detected": bool(distinct and not near_identical),
        "divergence_score": divergence_score,
        "shared_prompt_bleed_detected": bleed,
        "reason_codes": sorted(set(reason_codes)),
    }
    return _jsonable(out)


def _default_opening_convergence_session_health() -> dict[str, Any]:
    return {
        "opening_turns_checked": 0,
        "opening_plan_backed_count": 0,
        "opening_plan_missing_count": 0,
        "opening_invalid_plan_count": 0,
        "opening_anchor_grounding_failures": 0,
        "opening_stock_fallback_hits": 0,
        "opening_resume_entry_checked": 0,
        "opening_seam_failure_count": 0,
        "opening_convergence_verdict": "no_observations",
        "opening_repeated_generic_first_line": False,
        "opening_convergence_failure_details": [],
    }


_CONTINUATION_FILLER_ANTI_PATTERNS: tuple[str, ...] = (
    "the scene holds",
    "nothing changes",
    "things remain as they are",
    "the moment continues",
)


def _default_continuation_convergence_session_health() -> dict[str, Any]:
    return {
        "continuation_convergence_passed": True,
        "continuation_turns_checked": 0,
        "continuation_plan_verified_count": 0,
        "continuation_emergency_nonplan_count": 0,
        "continuation_explicit_nonplan_count": 0,
        "continuation_engine_only_count": 0,
        "continuation_failure_reasons": [],
        "first_continuation_failure_turn_id": None,
    }


def evaluate_continuation_convergence_for_turn_rows(
    turns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """C1-B: validate that continuation paths converge on plan-verified narration.

    Observational + deterministic: inspects recorded per-turn metadata only.
    Does not attempt to score prose quality; only checks explicit seam metadata and a narrow
    anti-pattern list on *normal* plan-driven continuation outputs.
    """
    turns_checked = 0
    plan_verified = 0
    emergency_nonplan = 0
    explicit_nonplan = 0
    engine_only = 0

    failure_reasons: list[str] = []
    first_failure_turn_id: str | None = None

    def _record_failure(turn_id: str, reason: str) -> None:
        nonlocal first_failure_turn_id
        failure_reasons.append(str(reason))
        if first_failure_turn_id is None:
            first_failure_turn_id = str(turn_id)

    for row in turns:
        turn_id = str(row.get("turn_id") or row.get("turn_index") or "")
        meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
        seam = meta.get("narration_seam") if isinstance(meta.get("narration_seam"), Mapping) else {}
        cont = seam.get("continuation") if isinstance(seam.get("continuation"), Mapping) else {}

        # If metadata is missing entirely, we cannot evaluate continuation convergence for that turn.
        if not seam or not cont:
            continue

        # Opening turns must not count as continuation.
        is_cont = cont.get("is_continuation_turn")
        if is_cont is False:
            continue

        # Count emergency / explicit non-plan separately (visible, not treated as success).
        if bool(seam.get("emergency_nonplan_output")) or cont.get("continuation_source") == "emergency_nonplan":
            emergency_nonplan += 1
            continue
        if bool(seam.get("explicit_nonplan_model_narration")) or (
            cont.get("continuation_source") == "explicit_nonplan_model_narration"
        ):
            explicit_nonplan += 1
            continue

        # Engine-only / non-CTIR outputs are excluded or separately counted.
        path_kind = str(seam.get("path_kind") or "")
        if path_kind.startswith("engine_") or cont.get("continuation_source") == "engine_only":
            engine_only += 1
            continue
        if seam.get("ctir_backed") is not True:
            engine_only += 1
            continue

        # From here: CTIR-backed continuation turn (candidate for validation).
        turns_checked += 1

        requires_plan = bool(cont.get("requires_plan_driven_continuation"))
        verified = cont.get("continuation_plan_verified")
        source = str(cont.get("continuation_source") or "")
        failure_reason = cont.get("continuation_plan_failure_reason")

        if requires_plan:
            if verified is not True:
                _record_failure(turn_id, f"continuation_plan_unverified:{failure_reason or 'unknown'}")
                continue
            plan_verified += 1
            if source != "narrative_plan_bundle":
                _record_failure(turn_id, f"continuation_source_not_bundle:{source or 'missing'}")
                continue
        else:
            # Passive CTIR-backed continuation that did not require plan-driven continuation must not
            # be allowed to claim bundle-backed success without verification.
            if source == "narrative_plan_bundle" and verified is not True:
                _record_failure(turn_id, "bundle_source_without_verification")
                continue

        # Missing bundle / stamp mismatch / explicit unverified source must fail.
        if source == "unverified" or (failure_reason and verified is not True and requires_plan):
            _record_failure(turn_id, f"unverified_continuation:{failure_reason or 'unknown'}")
            continue

        # Narrow anti-pattern checks for normal plan-driven continuation only.
        if source == "narrative_plan_bundle" and requires_plan:
            gm_text = str(row.get("gm_text") or "")
            gm_norm = _norm_text(gm_text)
            for phrase in _CONTINUATION_FILLER_ANTI_PATTERNS:
                if _norm_text(phrase) in gm_norm:
                    _record_failure(turn_id, f"continuation_generic_filler:{phrase}")
                    break

    passed = len(failure_reasons) == 0
    return {
        "continuation_convergence_passed": passed,
        "continuation_turns_checked": turns_checked,
        "continuation_plan_verified_count": plan_verified,
        "continuation_emergency_nonplan_count": emergency_nonplan,
        "continuation_explicit_nonplan_count": explicit_nonplan,
        "continuation_engine_only_count": engine_only,
        "continuation_failure_reasons": list(failure_reasons),
        "first_continuation_failure_turn_id": first_failure_turn_id,
    }


def _error_result(
    scenario_id: str,
    branch_id: str,
    turns: Sequence[Mapping[str, Any]],
    detail: str,
) -> dict[str, Any]:
    md_block = evaluate_transcript_metadata_completeness(turns)
    axis_shell = {
        "passed": False,
        "failure_codes": ["eval_aborted"],
        "warning_codes": [],
    }
    n_err = len(turns)
    empty_deg = {
        "early_window": {"turn_range": {"start": 0, "end": -1}, "warning_count": 0, "signals": []},
        "middle_window": {"turn_range": {"start": 0, "end": -1}, "warning_count": 0, "signals": []},
        "late_window": {"turn_range": {"start": 0, "end": -1}, "warning_count": 0, "signals": []},
        "clarity_warning_count": 0,
        "grounding_warning_count": 0,
        "continuity_warning_count": 0,
        "progressive_degradation_detected": False,
        "reason_codes": [],
    }
    return _jsonable(
        {
            "schema_version": 1,
            "scenario_id": scenario_id,
            "branch_id": branch_id,
            "turn_count": n_err,
            "session_health": {
                "overall_passed": False,
                "score": 0,
                "classification": "failed",
                "branch_id": branch_id,
                "turn_count": n_err,
                "scripted_turn_count": 0,
                "full_length_branch": False,
                "long_session_band": _long_session_band(n_err),
                "degradation_detected": False,
                **_default_opening_convergence_session_health(),
                **_default_continuation_convergence_session_health(),
                **md_block,
            },
            "degradation_over_time": empty_deg,
            "axes": {
                "state_continuity": axis_shell,
                "referent_persistence": axis_shell,
                "world_project_progression": axis_shell,
                "narrative_grounding": axis_shell,
                "branch_coherence": axis_shell,
            },
            "detected_failures": (
                [{"axis": "session", "code": "unknown_branch_id", "detail": detail}]
                + (
                    [
                        {
                            "axis": "scenario_spine_metadata",
                            "code": "scenario_spine_metadata_missing",
                            "detail": _metadata_completeness_failure_detail(md_block),
                        },
                    ]
                    if not md_block.get("metadata_completeness_passed", True)
                    else []
                )
            ),
            "warnings": [],
            "checkpoint_results": [],
        },
    )


def _compute_score(
    failures: Sequence[Mapping[str, Any]],
    warnings: Sequence[Mapping[str, Any]],
    *,
    api_majority: bool,
) -> int:
    score = 100
    score -= 24 * len(failures)
    score -= 7 * len(warnings)
    if api_majority:
        score -= 30
    return max(0, min(100, score))


def _classify(
    *,
    failed_axes: int,
    failure_count: int,
    warning_count: int,
    score: int,
    api_majority: bool,
) -> str:
    if api_majority or failed_axes >= 2:
        return "failed"
    if failed_axes == 1:
        return "degraded"
    if failure_count > 0 and failed_axes == 0:
        return "failed"
    if score < 40:
        return "failed"
    if warning_count > 0:
        return "warning"
    return "clean"


# ---------------------------------------------------------------------------
# Heuristic banks (reason-coded, transparent)
# ---------------------------------------------------------------------------

_RESET_PHRASES: tuple[str, ...] = (
    "start fresh",
    "new campaign",
    "you arrive for the first time",
    "none of this has happened",
    "forget the previous scene",
)

_AMNESIA_PHRASES: tuple[str, ...] = (
    "you have no memory",
    "as if you had never",
    "never saw the notice",
    "who is everyone here again",
    "stranger to this district",
)

_DEBUG_LEAK_MARKERS: tuple[str, ...] = (
    "system:",
    "developer instruction",
    "final_emission_gate",
    "trace_id",
    "validator failed",
)

def _looks_json_diagnostic_line(line: str) -> bool:
    s = line.strip()
    if len(s) < 24:
        return False
    if s[0] != "{" or s[-1] != "}":
        return False
    if '"trace_id"' in s or '"schema_version"' in s or '"error"' in s:
        return True
    return s.count('"') >= 10

_REFERENT_UNKNOWN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bwho\s+is\s+captain\s+thoran\b", re.I), "unknown_captain_thoran"),
    (re.compile(r"\bcaptain\s+thoran\b.*\b(who|what)\b", re.I), "captain_thoran_questioned_unknown"),
    (re.compile(r"\byou\s+have\s+not\s+seen\s+(the\s+)?notice\b", re.I), "notice_unknown_to_player"),
    (re.compile(r"\b(no|not\s+any)\s+such\s+clue\b", re.I), "clue_denied"),
    (re.compile(r"\bthere\s+is\s+no\s+notice\b", re.I), "notice_denied"),
    (re.compile(r"\bnever\s+heard\s+of\s+captain\s+thoran\b", re.I), "thoran_unknown_reputation"),
)

_PROGRESSION_CONTRADICTION: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bno\s+missing\s+patrol\b", re.I),
    re.compile(r"\bpatrol\s+(returned|was\s+fine|never\s+left)\b", re.I),
    re.compile(r"\bfalse\s+alarm\b.*\bpatrol\b", re.I),
)

_GENERIC_FILLER_PHRASES: frozenset[str] = frozenset(
    {
        "the moment stretches.",
        "silence hangs heavy.",
        "you wait and watch.",
        "nothing obvious changes yet.",
        "the crowd shifts uneasily.",
    },
)


def _referent_keywords_for_anchor(anchor_id: str, label: str, description: str) -> frozenset[str]:
    keys: set[str] = set()
    for chunk in (anchor_id, label, description):
        for token in re.split(r"[^\w]+", chunk.lower()):
            if len(token) >= 4:
                keys.add(token)
    # Fixture-specific short stems still useful
    if "thor" in anchor_id.lower() or "thoran" in label.lower():
        keys.update({"thoran", "captain"})
    if "notice" in anchor_id.lower() or "notice" in label.lower():
        keys.update({"notice", "board", "posted"})
    if "muddy" in anchor_id.lower() or "foot" in description.lower():
        keys.update({"muddy", "footprint", "prints", "northwest"})
    if "ash" in anchor_id.lower() or "compact" in label.lower():
        keys.update({"ash", "compact", "census"})
    return frozenset(k for k in keys if len(k) >= 3)


def _text_has_any_keyword(norm: str, keywords: frozenset[str]) -> bool:
    return any(k in norm for k in keywords if len(k) >= 3)


def _continuity_match(norm: str, description: str) -> bool:
    d = _norm_text(description)
    # Pull substantive tokens from anchor description
    toks = [t for t in re.split(r"[^\w]+", d) if len(t) >= 4]
    hits = sum(1 for t in toks[:12] if t in norm)
    return hits >= 2 or (len(toks) == 1 and toks[0] in norm)


def _progression_keywords(anchor_id: str, description: str, summary: str) -> frozenset[str]:
    aid = anchor_id.lower()
    base = _norm_text(f"{description} {summary}")
    toks = {t for t in re.split(r"[^\w]+", base) if len(t) >= 4}
    if "prog_patrol_investigation_advances" in aid or "patrol" in aid:
        toks.update(
            {
                "patrol",
                "missing",
                "investigation",
                "route",
                "sighting",
                "clock",
                "rumor",
                "disappearance",
            },
        )
    if "prog_watch_tightens" in aid or "watch" in aid:
        toks.update(
            {
                "watch",
                "curfew",
                "gate",
                "security",
                "enforcement",
                "tighten",
                "escalat",
                "serjeant",
            },
        )
    return frozenset(toks)


_STRONG_SESSION_DEGRADATION_CODES: frozenset[str] = frozenset(
    {
        "late_session_reset_or_amnesia",
        "debug_leak_late_window",
        "rising_generic_filler_strong",
    },
)


def _long_session_band(n: int) -> str:
    if n < 12:
        return "short"
    if n < 24:
        return "standard"
    return "long"


def _scripted_turn_count_for(spine: ScenarioSpine, branch_id: str) -> int:
    br = next((b for b in spine.branches if b.branch_id == branch_id), None)
    return len(br.turns) if br else 0


def _split_three_window_ranges(n: int) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if n <= 0:
        return ((0, -1), (0, -1), (0, -1))
    third = n // 3
    rem = n % 3
    sizes = [
        third + (1 if rem > 0 else 0),
        third + (1 if rem > 1 else 0),
        third,
    ]
    ranges: list[tuple[int, int]] = []
    lo = 0
    for sz in sizes:
        if sz <= 0:
            ranges.append((lo, lo - 1))
            continue
        hi = lo + sz - 1
        ranges.append((lo, hi))
        lo = hi + 1
    return (ranges[0], ranges[1], ranges[2])


def _turns_in_index_range(turns: Sequence[Mapping[str, Any]], lo: int, hi: int) -> list[Mapping[str, Any]]:
    if hi < lo:
        return []
    return [t for t in turns if lo <= t["turn_index"] <= hi]


def _gm_join_turn_slice(turns: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(str(t["gm_text"]) for t in turns)


def _filler_hits_turn_slice(turns: Sequence[Mapping[str, Any]]) -> int:
    total = 0
    for t in turns:
        raw = str(t["gm_text"])
        lines = raw.splitlines() if "\n" in raw else [raw]
        for line in lines:
            if _norm_text(line) in _GENERIC_FILLER_PHRASES:
                total += 1
    return total


def _norm_block_reset_or_amnesia(norm: str) -> bool:
    for phrase in _RESET_PHRASES:
        if phrase in norm:
            return True
    for phrase in _AMNESIA_PHRASES:
        if phrase in norm:
            return True
    return False


def _norm_block_debug(norm: str) -> bool:
    for marker in _DEBUG_LEAK_MARKERS:
        if marker in norm:
            return True
    return False


def _adjust_classification_for_degradation(
    base: str,
    *,
    n: int,
    degradation: Mapping[str, Any],
    failed_axes: int,
    failure_count: int,
) -> str:
    if n < 12:
        return base
    reasons = frozenset(degradation.get("reason_codes", ()))
    prog = bool(degradation.get("progressive_degradation_detected"))
    strong = bool(reasons & _STRONG_SESSION_DEGRADATION_CODES)
    if prog and strong:
        if base == "clean":
            return "failed"
        if base == "warning":
            return "degraded"
        if base == "degraded":
            return "failed"
    if prog and not strong:
        if base == "clean":
            return "warning"
    if (
        not prog
        and int(degradation.get("clarity_warning_count", 0)) >= 8
        and failed_axes == 0
        and failure_count == 0
    ):
        if base == "clean":
            return "warning"
    return base


def _compute_degradation_over_time(
    spine: ScenarioSpine,
    turns: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    n = len(turns)
    early_r, mid_r, late_r = _split_three_window_ranges(n)
    labels_ranges = (
        ("early_window", early_r),
        ("middle_window", mid_r),
        ("late_window", late_r),
    )

    window_payload: dict[str, dict[str, Any]] = {}
    for label, (lo, hi) in labels_ranges:
        slice_turns = _turns_in_index_range(turns, lo, hi)
        raw_join = _gm_join_turn_slice(slice_turns)
        norm = _norm_text(raw_join)
        signals: list[str] = []
        if norm and _norm_block_reset_or_amnesia(norm):
            signals.append("reset_or_amnesia_language")
        if norm and _norm_block_debug(norm):
            signals.append("debug_or_system_leak")
        fh = _filler_hits_turn_slice(slice_turns)
        if fh >= 2 or (fh >= 1 and label == "late_window" and n >= 12):
            signals.append(f"generic_filler_density:{fh}")
        window_payload[label] = {
            "turn_range": {"start": lo, "end": hi},
            "signals": signals,
            "filler_hits": fh,
        }

    clarity_warning_count = sum(int(w["filler_hits"]) for w in window_payload.values())
    grounding_warning_count = sum(
        1 for w in window_payload.values() if "debug_or_system_leak" in w["signals"]
    )
    continuity_warning_count = sum(
        1 for w in window_payload.values() if "reset_or_amnesia_language" in w["signals"]
    )

    meaningful = n >= 12
    late_slice = _turns_in_index_range(turns, late_r[0], late_r[1])
    late_norm = _norm_text(_gm_join_turn_slice(late_slice))
    est_hi = mid_r[1] if mid_r[1] >= mid_r[0] else early_r[1]
    establish_slice = _turns_in_index_range(turns, early_r[0], max(early_r[1], est_hi))
    establish_norm = _norm_text(_gm_join_turn_slice(establish_slice))

    if meaningful and late_r[1] >= late_r[0] and establish_norm and late_norm:
        for ca in spine.continuity_anchors:
            if _continuity_match(establish_norm, ca.description) and not _continuity_match(late_norm, ca.description):
                tag = f"continuity_anchor_lost_late:{ca.anchor_id}"
                window_payload["late_window"]["signals"].append(tag)
                continuity_warning_count += 1
        ref_map = {
            r.anchor_id: _referent_keywords_for_anchor(r.anchor_id, r.label, r.description)
            for r in spine.referent_anchors
        }
        for rid, kws in ref_map.items():
            if _text_has_any_keyword(establish_norm, kws) and not _text_has_any_keyword(late_norm, kws):
                tag = f"referent_keywords_lost_late:{rid}"
                window_payload["late_window"]["signals"].append(tag)
                continuity_warning_count += 1

    pre_late_slice = _turns_in_index_range(turns, 0, late_r[0] - 1) if late_r[0] > 0 else []
    pre_late_norm = _norm_text(_gm_join_turn_slice(pre_late_slice))
    late_reset = (
        meaningful
        and late_norm
        and _norm_block_reset_or_amnesia(late_norm)
        and not _norm_block_reset_or_amnesia(pre_late_norm)
    )
    debug_late = meaningful and late_norm and _norm_block_debug(late_norm)
    fe = int(window_payload["early_window"]["filler_hits"])
    fl = int(window_payload["late_window"]["filler_hits"])
    filler_strong = meaningful and fl >= 5 and fl >= 2 * max(1, fe) + 1
    filler_progressive = meaningful and not filler_strong and fl >= 4 and fl >= fe + 3 and fe <= 2

    continuity_late_loss = any(
        str(s).startswith("continuity_anchor_lost_late:") for s in window_payload["late_window"]["signals"]
    )
    referent_late_loss = any(
        str(s).startswith("referent_keywords_lost_late:") for s in window_payload["late_window"]["signals"]
    )

    reason_codes: list[str] = []
    progressive = False
    if meaningful:
        if late_reset:
            progressive = True
            reason_codes.append("late_session_reset_or_amnesia")
        if debug_late:
            progressive = True
            reason_codes.append("debug_leak_late_window")
        if filler_strong:
            progressive = True
            reason_codes.append("rising_generic_filler_strong")
        elif filler_progressive:
            progressive = True
            reason_codes.append("rising_generic_filler_progressive")
        if continuity_late_loss:
            progressive = True
            reason_codes.append("continuity_anchor_late_loss")
        if referent_late_loss:
            progressive = True
            reason_codes.append("referent_loss_late")

    out_windows: dict[str, Any] = {}
    for label, _ in labels_ranges:
        sigs = list(window_payload[label]["signals"])
        tr = window_payload[label]["turn_range"]
        out_windows[label] = {
            "turn_range": dict(tr),
            "warning_count": len(sigs),
            "signals": list(sorted(set(sigs))),
        }

    return {
        "early_window": out_windows["early_window"],
        "middle_window": out_windows["middle_window"],
        "late_window": out_windows["late_window"],
        "clarity_warning_count": clarity_warning_count,
        "grounding_warning_count": grounding_warning_count,
        "continuity_warning_count": continuity_warning_count,
        "progressive_degradation_detected": progressive,
        "reason_codes": sorted(set(reason_codes)),
    }


# ---------------------------------------------------------------------------
# Evaluation context
# ---------------------------------------------------------------------------


class _EvalContext:
    def __init__(
        self,
        *,
        spine: ScenarioSpine,
        branch_id: str,
        turns: tuple[dict[str, Any], ...],
        raw_turns: tuple[Mapping[str, Any], ...],
    ) -> None:
        self.spine = spine
        self.branch_id = branch_id
        self.turns = turns
        self.raw_turns = raw_turns
        self.failures: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.checkpoint_results: list[dict[str, Any]] = []

    def add_failure(
        self,
        axis: str,
        code: str,
        detail: str,
        *,
        turn_index: int | None = None,
        anchor_id: str | None = None,
    ) -> None:
        item: dict[str, Any] = {"axis": axis, "code": code, "detail": detail}
        if turn_index is not None:
            item["turn_index"] = turn_index
        if anchor_id is not None:
            item["anchor_id"] = anchor_id
        self.failures.append(item)

    def add_warning(
        self,
        axis: str,
        code: str,
        detail: str,
        *,
        turn_index: int | None = None,
        anchor_id: str | None = None,
    ) -> None:
        item: dict[str, Any] = {"axis": axis, "code": code, "detail": detail}
        if turn_index is not None:
            item["turn_index"] = turn_index
        if anchor_id is not None:
            item["anchor_id"] = anchor_id
        self.warnings.append(item)

    def _emit_session_degradation_events(self, deg: Mapping[str, Any]) -> None:
        n = len(self.turns)
        if n < 12 or not deg.get("progressive_degradation_detected"):
            return
        reasons = set(deg.get("reason_codes", ()))
        if not reasons:
            return
        strong_hits = reasons & _STRONG_SESSION_DEGRADATION_CODES
        if not strong_hits:
            if not any(w.get("code") == "progressive_degradation_mild" for w in self.warnings):
                self.add_warning(
                    "session",
                    "progressive_degradation_mild",
                    ",".join(sorted(reasons)),
                )
            return
        covered = True
        if "late_session_reset_or_amnesia" in strong_hits:
            if not any(f.get("code") == "continuity_reset_language" for f in self.failures):
                covered = False
        if "debug_leak_late_window" in strong_hits:
            if not any(
                f.get("code") in ("debug_or_system_leak", "json_diagnostic_dump") for f in self.failures
            ):
                covered = False
        if "rising_generic_filler_strong" in strong_hits:
            covered = False
        if covered:
            return
        if any(f.get("code") == "strong_progressive_degradation" for f in self.failures):
            return
        self.add_failure(
            "session",
            "strong_progressive_degradation",
            ",".join(sorted(reasons)),
        )

    def run(self) -> dict[str, Any]:
        n = len(self.turns)
        scripted_n = _scripted_turn_count_for(self.spine, self.branch_id)
        axes: dict[str, Any] = {
            "state_continuity": self._axis_state_continuity(),
            "referent_persistence": self._axis_referent_persistence(),
            "world_project_progression": self._axis_progression(),
            "narrative_grounding": self._axis_narrative_grounding(),
            "branch_coherence": self._axis_branch_coherence(),
        }
        self._build_checkpoint_results()

        degradation_over_time = _compute_degradation_over_time(self.spine, self.turns)
        self._emit_session_degradation_events(degradation_over_time)

        api_failures = sum(1 for t in self.turns if not t["api_ok"])
        api_majority = n > 0 and api_failures > n // 2
        if api_majority:
            self.add_failure(
                "session",
                "api_failure_majority",
                f"{api_failures}/{n} turns report api_ok=false",
            )

        opening_block = evaluate_opening_convergence_for_turn_rows(self.turns)
        if opening_block.get("opening_convergence_verdict") == "fail":
            self.add_failure(
                "opening_convergence",
                "opening_convergence_verdict_fail",
                "C1-A scene opening convergence failed (see session_health.opening_convergence_failure_details)",
            )
        elif int(opening_block.get("opening_turns_checked") or 0) > 0 and (
            opening_block.get("opening_repeated_generic_first_line")
            or int(opening_block.get("opening_stock_fallback_hits") or 0) > 0
        ):
            self.add_warning(
                "opening_convergence",
                "opening_style_signal",
                "repeated generic first-line and/or stock opener phrasing on opening turn(s) — scoring only",
            )

        continuation_block = evaluate_continuation_convergence_for_turn_rows(self.turns)
        if continuation_block.get("continuation_convergence_passed") is False:
            self.add_failure(
                "continuation_convergence",
                "continuation_convergence_failed",
                "C1-B continuation convergence invariant failed (see session_health.continuation_failure_reasons)",
            )

        score = _compute_score(self.failures, self.warnings, api_majority=api_majority)
        failed_axes = sum(1 for a in axes.values() if not a["passed"])
        classification = _classify(
            failed_axes=failed_axes,
            failure_count=len(self.failures),
            warning_count=len(self.warnings),
            score=score,
            api_majority=api_majority,
        )
        classification = _adjust_classification_for_degradation(
            classification,
            n=n,
            degradation=degradation_over_time,
            failed_axes=failed_axes,
            failure_count=len(self.failures),
        )
        overall_passed = classification in ("clean", "warning")

        metadata_block = evaluate_transcript_metadata_completeness(self.raw_turns)

        deg_any = bool(degradation_over_time.get("progressive_degradation_detected")) or bool(
            int(degradation_over_time.get("clarity_warning_count", 0))
            + int(degradation_over_time.get("grounding_warning_count", 0))
            + int(degradation_over_time.get("continuity_warning_count", 0)),
        )
        session_health: dict[str, Any] = {
            "overall_passed": overall_passed,
            "score": score,
            "classification": classification,
            "branch_id": self.branch_id,
            "turn_count": n,
            "scripted_turn_count": scripted_n,
            "full_length_branch": bool(scripted_n and n >= scripted_n),
            "long_session_band": _long_session_band(n),
            "degradation_detected": deg_any,
            **opening_block,
            **continuation_block,
            **metadata_block,
        }

        detected_failures: list[dict[str, Any]] = list(self.failures)
        if not metadata_block.get("metadata_completeness_passed", True):
            detected_failures.append(
                {
                    "axis": "scenario_spine_metadata",
                    "code": "scenario_spine_metadata_missing",
                    "detail": _metadata_completeness_failure_detail(metadata_block),
                },
            )

        out: dict[str, Any] = {
            "schema_version": 1,
            "scenario_id": self.spine.spine_id,
            "branch_id": self.branch_id,
            "turn_count": n,
            "session_health": session_health,
            "degradation_over_time": degradation_over_time,
            "axes": axes,
            "detected_failures": detected_failures,
            "warnings": list(self.warnings),
            "checkpoint_results": list(self.checkpoint_results),
        }
        return _jsonable(out)


    def _axis_state_continuity(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        # Reset language after turn index >= 3 (1-based "after turn 3")
        for t in self.turns:
            if t["turn_index"] < 3:
                continue
            low = _norm_text(str(t["gm_text"]))
            for phrase in _RESET_PHRASES:
                if phrase in low:
                    self.add_failure(
                        "state_continuity",
                        "continuity_reset_language",
                        f"gm contains reset phrase {phrase!r}",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append("continuity_reset_language")

        # Checkpoint windows: continuity anchors referenced should not vanish entirely in later windows
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = len(cps)
        if k and self.turns:
            for i, cp in enumerate(cps):
                end_i = max(0, (i + 1) * len(self.turns) // k - 1)
                text_i = _norm_text(_concat_gm(self.turns, end_i))
                weak_ids: list[str] = []
                for rid in cp.referenced_anchor_ids:
                    ca = next((a for a in self.spine.continuity_anchors if a.anchor_id == rid), None)
                    if ca is None:
                        continue
                    if not _continuity_match(text_i, ca.description):
                        weak_ids.append(ca.anchor_id)
                if weak_ids:
                    self.add_warning(
                        "state_continuity",
                        "continuity_anchor_weak_by_checkpoint",
                        f"checkpoint {cp.checkpoint_id}: weak continuity for {sorted(weak_ids)}",
                    )
                    codes_warn.append("continuity_anchor_weak_by_checkpoint")

            # Vanishing: established in early window but absent in all turns after mid-session
            mid = len(self.turns) // 2
            last_start = max(0, len(self.turns) * 2 // 3)
            late_window = _norm_text(
                "\n".join(str(t["gm_text"]) for t in self.turns if t["turn_index"] >= last_start),
            )
            early = _norm_text(_concat_gm(self.turns, max(0, mid)))
            for ca in self.spine.continuity_anchors:
                if _continuity_match(early, ca.description) and not _continuity_match(late_window, ca.description):
                    self.add_warning(
                        "state_continuity",
                        "continuity_anchor_absent_late_window",
                        f"continuity {ca.anchor_id} present early but not in final third window",
                        anchor_id=ca.anchor_id,
                    )
                    codes_warn.append("continuity_anchor_absent_late_window")

        passed = not any(f["axis"] == "state_continuity" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_referent_persistence(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        if not self.turns:
            return {"passed": True, "failure_codes": [], "warning_codes": []}

        mid = max(1, len(self.turns) // 2)
        early_text = _norm_text(_concat_gm(self.turns, mid - 1))

        ref_map: dict[str, frozenset[str]] = {}
        for r in self.spine.referent_anchors:
            ref_map[r.anchor_id] = _referent_keywords_for_anchor(r.anchor_id, r.label, r.description)

        established: dict[str, bool] = {
            rid: _text_has_any_keyword(early_text, kws) for rid, kws in ref_map.items()
        }

        # Unknown-denial phrases only after the referent was established in prior GM text
        for t in self.turns:
            low = _norm_text(str(t["gm_text"]))
            prior = _norm_text(_concat_gm(self.turns, t["turn_index"] - 1)) if t["turn_index"] > 0 else ""
            established_prior = {
                rid: _text_has_any_keyword(prior, kws) for rid, kws in ref_map.items()
            }
            muddy_established = established_prior.get("ref_muddy_prints", False)
            for rx, pcode in _REFERENT_UNKNOWN_PATTERNS:
                if not rx.search(low):
                    continue
                if "thoran" in pcode and established_prior.get("ref_captain_thoran"):
                    self.add_failure(
                        "referent_persistence",
                        pcode,
                        "gm treats Captain Thoran as unknown after establishment",
                        turn_index=t["turn_index"],
                        anchor_id="ref_captain_thoran",
                    )
                    codes_fail.append(pcode)
                if "notice" in pcode and any(
                    established_prior.get(aid) for aid in ref_map if "notice" in aid.lower()
                ):
                    self.add_failure(
                        "referent_persistence",
                        pcode,
                        "gm denies notice after it was established",
                        turn_index=t["turn_index"],
                        anchor_id="ref_notice_board",
                    )
                    codes_fail.append(pcode)
                if pcode == "clue_denied" and muddy_established:
                    self.add_failure(
                        "referent_persistence",
                        pcode,
                        "gm denies a clue after muddy-prints referent was established",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append(pcode)

        # Required referents from checkpoints
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = max(1, len(cps))
        last_start = max(0, len(self.turns) * 2 // 3)
        late_window = _norm_text(
            "\n".join(str(t["gm_text"]) for t in self.turns if t["turn_index"] >= last_start),
        )
        required_ids: set[str] = set()
        for cp in cps:
            for rid in cp.referenced_anchor_ids:
                if any(r.anchor_id == rid for r in self.spine.referent_anchors):
                    required_ids.add(rid)

        for rid in sorted(required_ids):
            kws = ref_map.get(rid, frozenset())
            if not kws:
                continue
            if _text_has_any_keyword(early_text, kws) and not _text_has_any_keyword(late_window, kws):
                self.add_warning(
                    "referent_persistence",
                    "referent_absent_late_window",
                    f"required referent {rid} not present in final third gm window",
                    anchor_id=rid,
                )
                codes_warn.append("referent_absent_late_window")

        passed = not any(f["axis"] == "referent_persistence" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_progression(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = max(1, len(cps))
        n = len(self.turns)

        prog_by_id = {p.anchor_id: p for p in self.spine.progression_anchors}

        for i, cp in enumerate(cps):
            end_i = max(0, (i + 1) * n // k - 1) if n else 0
            chunk = _norm_text(_concat_gm(self.turns, end_i))
            for rid in cp.referenced_anchor_ids:
                prog = prog_by_id.get(rid)
                if prog is None:
                    continue
                kws = _progression_keywords(prog.anchor_id, prog.description, prog.expected_change_summary)
                if not _text_has_any_keyword(chunk, kws):
                    self.add_failure(
                        "world_project_progression",
                        "progression_missing_by_checkpoint",
                        f"{prog.anchor_id} not evidenced by checkpoint {cp.checkpoint_id} window",
                        anchor_id=prog.anchor_id,
                    )
                    codes_fail.append("progression_missing_by_checkpoint")

        # Contradiction after positive signal
        full = _norm_text(_concat_gm(self.turns, n - 1 if n else 0))
        for prog in self.spine.progression_anchors:
            kws = _progression_keywords(prog.anchor_id, prog.description, prog.expected_change_summary)
            if not _text_has_any_keyword(full, kws):
                continue
            for rx in _PROGRESSION_CONTRADICTION:
                if rx.search(full):
                    self.add_warning(
                        "world_project_progression",
                        "progression_contradicted",
                        f"progression for {prog.anchor_id} later contradicted",
                        anchor_id=prog.anchor_id,
                    )
                    codes_warn.append("progression_contradicted")
                    break

        passed = not any(f["axis"] == "world_project_progression" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_narrative_grounding(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        for t in self.turns:
            raw = str(t["gm_text"])
            low = raw.lower()
            for marker in _DEBUG_LEAK_MARKERS:
                if marker in low:
                    self.add_failure(
                        "narrative_grounding",
                        "debug_or_system_leak",
                        f"gm contains marker {marker!r}",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append("debug_or_system_leak")
            for line in raw.splitlines():
                if _looks_json_diagnostic_line(line):
                    self.add_failure(
                        "narrative_grounding",
                        "json_diagnostic_dump",
                        "gm line resembles raw JSON diagnostic",
                        turn_index=t["turn_index"],
                    )
                    codes_fail.append("json_diagnostic_dump")

        # Repeated generic filler across long tail
        if len(self.turns) >= 12:
            low_lines = [_norm_text(str(t["gm_text"])) for t in self.turns]
            filler_hits = sum(1 for ln in low_lines if ln in _GENERIC_FILLER_PHRASES)
            if filler_hits >= max(6, len(self.turns) // 3):
                self.add_warning(
                    "narrative_grounding",
                    "repeated_generic_filler",
                    "high count of generic filler lines across session",
                )
                codes_warn.append("repeated_generic_filler")

        passed = not any(f["axis"] == "narrative_grounding" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _axis_branch_coherence(self) -> dict[str, Any]:
        codes_fail: list[str] = []
        codes_warn: list[str] = []
        by_branch = {b.branch_id: b for b in self.spine.branches}
        selected = by_branch.get(self.branch_id)
        if selected is None:
            return {"passed": True, "failure_codes": [], "warning_codes": []}

        selected_prompts = {_norm_text(t.player_prompt) for t in selected.turns}
        signatures: list[str] = []
        for bid, br in by_branch.items():
            if bid == self.branch_id:
                continue
            for t in br.turns:
                p = _norm_text(t.player_prompt)
                if len(p) < 12:
                    continue
                if p not in selected_prompts:
                    signatures.append(p)

        combined = _norm_text(_concat_gm(self.turns, len(self.turns) - 1))
        for sig in signatures:
            if len(sig) < 24:
                continue
            # Long distinctive substring from another branch's scripted prompt
            if sig in combined or (len(sig) > 40 and sig[:40] in combined):
                self.add_failure(
                    "branch_coherence",
                    "foreign_branch_prompt_echo",
                    "gm echoes another branch's scripted player beat",
                )
                codes_fail.append("foreign_branch_prompt_echo")
                break

        passed = not any(f["axis"] == "branch_coherence" for f in self.failures)
        return {
            "passed": passed,
            "failure_codes": sorted(set(codes_fail)),
            "warning_codes": sorted(set(codes_warn)),
        }

    def _build_checkpoint_results(self) -> None:
        self.checkpoint_results.clear()
        cps = sorted(self.spine.checkpoints, key=lambda c: c.checkpoint_id)
        k = max(1, len(cps))
        n = len(self.turns)
        ref_map = {
            r.anchor_id: _referent_keywords_for_anchor(r.anchor_id, r.label, r.description)
            for r in self.spine.referent_anchors
        }
        cont_map = {a.anchor_id: a for a in self.spine.continuity_anchors}
        prog_map = {p.anchor_id: p for p in self.spine.progression_anchors}
        for i, cp in enumerate(cps):
            end_i = max(0, (i + 1) * n // k - 1) if n else 0
            text = _norm_text(_concat_gm(self.turns, end_i))
            issues: list[dict[str, Any]] = []
            for rid in cp.referenced_anchor_ids:
                if rid in prog_map:
                    pr = prog_map[rid]
                    kws = _progression_keywords(pr.anchor_id, pr.description, pr.expected_change_summary)
                    if not _text_has_any_keyword(text, kws):
                        issues.append(
                            {"code": "progression_missing", "anchor_id": rid, "detail": "keywords not found in window"},
                        )
                elif rid in cont_map:
                    if not _continuity_match(text, cont_map[rid].description):
                        issues.append(
                            {"code": "continuity_weak", "anchor_id": rid, "detail": "description tokens sparse in window"},
                        )
                elif rid in ref_map:
                    if not _text_has_any_keyword(text, ref_map[rid]):
                        issues.append(
                            {"code": "referent_weak", "anchor_id": rid, "detail": "referent keywords not found in window"},
                        )
            self.checkpoint_results.append(
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "label": cp.label,
                    "passed": len(issues) == 0,
                    "window_end_turn_index": end_i,
                    "referenced_anchor_ids": list(cp.referenced_anchor_ids),
                    "issues": issues,
                },
            )
