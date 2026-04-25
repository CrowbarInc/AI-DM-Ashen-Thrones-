"""Offline observational C1-A scene-opening convergence metrics for scenario-spine evaluation.

Does **not** import ``infer_scene_opening_reason`` or ``validate_scene_opening`` (C1-A audit).
Structural checks mirror the public plan shape only; runtime truth is whatever the harness
records under each turn's ``meta["opening_convergence"]`` (see
``capture_opening_convergence_meta_from_chat_payload``).
"""

from __future__ import annotations

import copy
import re
from collections import Counter
from typing import Any, Mapping, Sequence

# Mirror ``game.narrative_planning`` contract keys (observation-only; keep aligned in review).
_SCENE_OPENING_ALLOWED_TOP_KEYS: frozenset[str] = frozenset(
    {
        "opening_required",
        "opening_reason",
        "scene_id",
        "location_anchors",
        "actor_anchors",
        "active_pressures",
        "visible_fact_categories",
        "visible_fact_anchor_ids",
        "prohibited_content_codes",
        "derivation_codes",
        "validator",
    },
)
_SCENE_OPENING_REASONS: frozenset[str] = frozenset(
    {"campaign_start", "scene_entry", "post_transition", "resume_entry", "none"},
)
_SCENE_OPENING_PROSEISH_KEY_SUBSTRINGS: frozenset[str] = frozenset(
    {
        "narration",
        "opener_line",
        "cinematic",
        "neutral_opener",
        "fallback_opener",
        "fallback",
        "template",
        "paragraph",
        "prose",
    },
)

_STOCK_FALLBACK_PHRASES: tuple[str, ...] = (
    "you wake in darkness",
    "darkness recedes",
    "the world swims into focus",
    "you find yourself in",
    "as if waking from a dream",
    "inventory is empty",
    "stranger in a strange land",
    "neutral establishing shot",
    "cinematic wide shot",
    "fallback narration",
    "template opening",
)

_OPENING_CONVERGENCE_META_KEY = "opening_convergence"


def capture_opening_convergence_meta_from_chat_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build JSON-serializable ``meta.opening_convergence`` from a ``POST /api/chat`` style payload."""
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    bundle = session.get("_runtime_narration_plan_bundle_v1")
    bundle_present = isinstance(bundle, dict)
    plan = bundle.get("narrative_plan") if bundle_present else None
    narrative_plan_present = isinstance(plan, dict)
    pm = bundle.get("plan_metadata") if bundle_present and isinstance(bundle.get("plan_metadata"), dict) else {}
    psi = pm.get("planning_session_interaction") if isinstance(pm.get("planning_session_interaction"), dict) else {}
    so_raw = plan.get("scene_opening") if narrative_plan_present else None
    so_dict = copy.deepcopy(so_raw) if isinstance(so_raw, dict) else None

    traces = session.get("debug_traces") if isinstance(session.get("debug_traces"), list) else []
    seam_trace = _pick_last_semantic_bypass_trace(traces)

    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    narration_seam = md.get("narration_seam") if isinstance(md.get("narration_seam"), dict) else {}
    seam_compact = {
        k: narration_seam[k]
        for k in ("path_kind", "plan_driven", "bundle_required", "emergency_nonplan_output")
        if k in narration_seam
    }
    extra = narration_seam.get("extra") if isinstance(narration_seam.get("extra"), dict) else {}
    if extra:
        seam_compact["extra_bundle_seam_failed"] = bool(extra.get("bundle_seam_requirement_failed"))

    out: dict[str, Any] = {
        "bundle_present": bundle_present,
        "narrative_plan_present": narrative_plan_present,
        "planning_session_interaction": dict(psi),
        "scene_opening": so_dict,
        "seam_trace": seam_trace,
        "narration_seam": seam_compact,
        "api_error": payload.get("error"),
    }
    return out


def _pick_last_semantic_bypass_trace(traces: Sequence[Any]) -> dict[str, Any] | None:
    for t in reversed(list(traces)):
        if not isinstance(t, dict):
            continue
        if str(t.get("operation") or "") != "semantic_bypass_blocked":
            continue
        ex = t.get("extra") if isinstance(t.get("extra"), dict) else {}
        return {
            "reason": str(t.get("reason") or ""),
            "opening_required": ex.get("opening_required"),
            "opening_reason_inferred": ex.get("opening_reason_inferred"),
            "validate_scene_opening": ex.get("validate_scene_opening"),
        }
    return None


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _scene_opening_proseish_key_hit(so: Mapping[str, Any]) -> str | None:
    for k in so.keys():
        ks = str(k).lower()
        if ks in _SCENE_OPENING_PROSEISH_KEY_SUBSTRINGS:
            return str(k)
        for frag in _SCENE_OPENING_PROSEISH_KEY_SUBSTRINGS:
            if frag in ks:
                return str(k)
    return None


def _unknown_top_level_keys(so: Mapping[str, Any]) -> frozenset[str]:
    keys = {str(k) for k in so if isinstance(k, str)}
    return frozenset(keys - _SCENE_OPENING_ALLOWED_TOP_KEYS)


def observational_scene_opening_issues(
    scene_opening: Mapping[str, Any] | None,
    *,
    planning_session_interaction: Mapping[str, Any] | None,
) -> list[str]:
    """Return human-readable issue codes; empty means structurally acceptable for recorded openings."""
    issues: list[str] = []
    if scene_opening is None:
        return ["scene_opening_absent"]
    if not isinstance(scene_opening, Mapping):
        return ["scene_opening_not_mapping"]
    so = scene_opening
    bad_top = _unknown_top_level_keys(so)
    if bad_top:
        issues.append(f"scene_opening_unknown_keys:{','.join(sorted(bad_top))}")
    prose = _scene_opening_proseish_key_hit(so)
    if prose:
        issues.append(f"scene_opening_proseish_key:{prose}")
    reason = so.get("opening_reason")
    rs = str(reason).strip() if reason is not None else ""
    if rs not in _SCENE_OPENING_REASONS:
        issues.append(f"scene_opening_bad_reason:{rs!r}")
    req = so.get("opening_required")
    if rs != "none":
        if req is not True:
            issues.append("scene_opening_opening_required_not_true_for_reason")
    else:
        if req is True:
            issues.append("scene_opening_reason_none_but_required_true")
    if rs != "none":
        sid = str(so.get("scene_id") or "").strip()
        if not sid:
            issues.append("scene_opening_missing_scene_id")
        loc = so.get("location_anchors")
        if isinstance(loc, list) and len(loc) > 0:
            if not any(isinstance(x, str) and x.strip() for x in loc):
                issues.append("scene_opening_location_anchors_empty_strings")
        act = so.get("actor_anchors")
        if isinstance(act, list) and len(act) > 0:
            for i, row in enumerate(act):
                if not isinstance(row, Mapping):
                    issues.append(f"scene_opening_actor_anchor_not_mapping:{i}")
                    break
    psi = planning_session_interaction or {}
    if bool(psi.get("resume_entry")) and rs not in ("", "resume_entry"):
        issues.append("scene_opening_resume_mismatch_planning_session_interaction")
    return issues


def _turn_is_opening_candidate(meta: Mapping[str, Any] | None) -> bool:
    if not isinstance(meta, Mapping):
        return False
    oc = meta.get(_OPENING_CONVERGENCE_META_KEY)
    if not isinstance(oc, Mapping):
        return False
    if oc.get("skip_opening_evaluation") is True:
        return False
    if oc.get("is_opening_turn") is True:
        return True
    so = oc.get("scene_opening")
    if isinstance(so, dict):
        rs = str(so.get("opening_reason") or "").strip()
        if so.get("opening_required") is True or (rs and rs != "none"):
            return True
    st = oc.get("seam_trace") if isinstance(oc.get("seam_trace"), dict) else {}
    if str(st.get("reason") or "") == "scene_opening_seam_invalid":
        return True
    return False


def _anchor_grounding_category(
    gm_text: str,
    scene_opening: Mapping[str, Any] | None,
) -> str | None:
    """Return a short category when structural anchors exist but GM text ignores them."""
    if not isinstance(scene_opening, Mapping):
        return None
    norm = _norm(gm_text)
    if not norm:
        return "empty_gm_text"
    loc = scene_opening.get("location_anchors")
    loc_hits = 0
    if isinstance(loc, list):
        for x in loc:
            if not isinstance(x, str):
                continue
            tok = _norm(x)
            if len(tok) >= 3 and tok in norm:
                loc_hits += 1
    need_loc = isinstance(loc, list) and len(loc) > 0
    if need_loc and loc_hits == 0:
        return "location_anchor_not_grounded"

    act = scene_opening.get("actor_anchors")
    act_hits = 0
    if isinstance(act, list):
        for row in act:
            if not isinstance(row, Mapping):
                continue
            eid = str(row.get("entity_id") or "").strip().lower()
            if len(eid) >= 3 and eid in norm:
                act_hits += 1
                continue
            for piece in eid.split("_"):
                if len(piece) >= 4 and piece in norm:
                    act_hits += 1
                    break
    need_act = isinstance(act, list) and len(act) > 0
    if need_act and act_hits == 0:
        return "actor_anchor_not_grounded"
    return None


def _stock_fallback_hit(gm_text: str) -> str | None:
    low = _norm(gm_text)
    for phrase in _STOCK_FALLBACK_PHRASES:
        if phrase in low:
            return phrase
    return None


def evaluate_opening_convergence_for_turn_rows(
    turns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compute C1-A opening observability counters and verdict from normalized spine turn rows."""
    opening_turns_checked = 0
    opening_plan_backed_count = 0
    opening_plan_missing_count = 0
    opening_invalid_plan_count = 0
    opening_anchor_grounding_failures = 0
    opening_stock_fallback_hits = 0
    opening_resume_entry_checked = 0
    opening_seam_failure_count = 0
    failure_details: list[dict[str, Any]] = []
    opening_gm_first_lines: list[str] = []

    for t in turns:
        meta = t.get("meta")
        if not _turn_is_opening_candidate(meta):
            continue
        oc = meta.get(_OPENING_CONVERGENCE_META_KEY) if isinstance(meta, Mapping) else None
        oc = oc if isinstance(oc, Mapping) else {}
        opening_turns_checked += 1
        turn_index = int(t.get("turn_index", -1))
        gm_text = str(t.get("gm_text") or "")
        psi = oc.get("planning_session_interaction") if isinstance(oc.get("planning_session_interaction"), dict) else {}
        st = oc.get("seam_trace") if isinstance(oc.get("seam_trace"), dict) else {}
        seam_reason = str(st.get("reason") or "")
        if seam_reason == "scene_opening_seam_invalid":
            opening_seam_failure_count += 1
            inferred = str(st.get("opening_reason_inferred") or "")
            failure_details.append(
                {
                    "turn_index": turn_index,
                    "opening_reason": inferred or "(unknown)",
                    "scene_id": None,
                    "marker": "scene_opening_seam_invalid",
                    "seam_failure_reason": str(st.get("validate_scene_opening") or ""),
                    "anchor_grounding_category": None,
                    "suspected_source": "seam_guard",
                },
            )
            continue

        bundle_ok = oc.get("bundle_present") is True
        plan_ok = oc.get("narrative_plan_present") is True
        so = oc.get("scene_opening") if isinstance(oc.get("scene_opening"), dict) else None

        if not bundle_ok or not plan_ok or so is None:
            opening_plan_missing_count += 1
            failure_details.append(
                {
                    "turn_index": turn_index,
                    "opening_reason": str(so.get("opening_reason") or "") if isinstance(so, dict) else "(n/a)",
                    "scene_id": (str(so.get("scene_id") or "").strip() or None) if isinstance(so, dict) else None,
                    "marker": "plan_or_scene_opening_missing",
                    "seam_failure_reason": None,
                    "anchor_grounding_category": None,
                    "suspected_source": "CTIR" if not bundle_ok else "Narrative Plan",
                },
            )
            continue

        issues = observational_scene_opening_issues(so, planning_session_interaction=psi)
        if issues:
            opening_invalid_plan_count += 1
            failure_details.append(
                {
                    "turn_index": turn_index,
                    "opening_reason": str(so.get("opening_reason") or ""),
                    "scene_id": str(so.get("scene_id") or "").strip() or None,
                    "marker": f"invalid_plan:{issues[0]}",
                    "seam_failure_reason": None,
                    "anchor_grounding_category": None,
                    "suspected_source": "Narrative Plan",
                },
            )
            continue

        opening_plan_backed_count += 1
        reason_s = str(so.get("opening_reason") or "").strip()
        if reason_s == "resume_entry":
            opening_resume_entry_checked += 1

        ag = _anchor_grounding_category(gm_text, so)
        if ag and ag != "empty_gm_text":
            opening_anchor_grounding_failures += 1
            failure_details.append(
                {
                    "turn_index": turn_index,
                    "opening_reason": reason_s,
                    "scene_id": str(so.get("scene_id") or "").strip() or None,
                    "marker": "anchor_grounding",
                    "seam_failure_reason": None,
                    "anchor_grounding_category": ag,
                    "suspected_source": "prompt/output",
                },
            )

        stock = _stock_fallback_hit(gm_text)
        if stock:
            opening_stock_fallback_hits += 1

        first_ln = _norm(gm_text.split("\n", 1)[0] if gm_text else "")
        if first_ln:
            opening_gm_first_lines.append(first_ln)

    # Same normalized first line repeated on ≥3 opening turns → style warning (not a hard fail).
    repeated_generic_opening = False
    if len(opening_gm_first_lines) >= 3:
        cnt = Counter(opening_gm_first_lines)
        top_line, top_freq = cnt.most_common(1)[0]
        repeated_generic_opening = top_freq >= 3 and len(top_line) >= 16

    hard_fail = (
        opening_plan_missing_count + opening_invalid_plan_count + opening_seam_failure_count + opening_anchor_grounding_failures
        > 0
    )
    if opening_turns_checked == 0:
        verdict = "no_observations"
    elif hard_fail:
        verdict = "fail"
    else:
        verdict = "pass"

    return {
        "opening_turns_checked": opening_turns_checked,
        "opening_plan_backed_count": opening_plan_backed_count,
        "opening_plan_missing_count": opening_plan_missing_count,
        "opening_invalid_plan_count": opening_invalid_plan_count,
        "opening_anchor_grounding_failures": opening_anchor_grounding_failures,
        "opening_stock_fallback_hits": opening_stock_fallback_hits,
        "opening_resume_entry_checked": opening_resume_entry_checked,
        "opening_seam_failure_count": opening_seam_failure_count,
        "opening_convergence_verdict": verdict,
        "opening_repeated_generic_first_line": repeated_generic_opening,
        "opening_convergence_failure_details": failure_details,
    }
