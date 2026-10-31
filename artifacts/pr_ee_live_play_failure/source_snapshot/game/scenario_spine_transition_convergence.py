"""Block C — scenario-spine transition convergence checks (offline, observational).

Core invariant:
No emitted/implied/observed transition may occur without a valid Narrative Plan ``transition_node``.

This module is evaluation/reporting only:
- does not mutate narration/state/plan
- does not infer missing anchors
- keeps detection conservative, strict for obvious transition markers
"""

from __future__ import annotations

import copy
import re
from typing import Any, Mapping, Sequence

# Mirror ``game.narrative_planning`` / ``game.prompt_context`` contract keys (observation-only).
_TRANSITION_NODE_ALLOWED_TOP_KEYS: frozenset[str] = frozenset(
    {
        "transition_required",
        "transition_type",
        "before_anchor",
        "after_anchor",
        "continuity_anchor_ids",
        "derivation_codes",
        "source_fields",
    },
)
_ANCHOR_ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "kind",
        "identifier",
        "label",
        "scene_id",
        "location_id",
        "time_id",
    },
)

_TRANSITION_TYPES: frozenset[str] = frozenset(
    {
        "none",
        "location_movement",
        "scene_cut",
        "time_skip",
        "mixed",
        "unknown",
    },
)

_META_KEY = "transition_convergence"


def capture_transition_convergence_meta_from_chat_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build JSON-serializable ``meta.transition_convergence`` from a ``POST /api/chat`` style payload."""
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    bundle = session.get("_runtime_narration_plan_bundle_v1")
    bundle_present = isinstance(bundle, dict)
    plan = bundle.get("narrative_plan") if bundle_present else None
    narrative_plan_present = isinstance(plan, dict)

    tn_raw = plan.get("transition_node") if narrative_plan_present else None
    tn_dict = copy.deepcopy(tn_raw) if isinstance(tn_raw, dict) else None

    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), Mapping) else {}
    resolved_transition = resolution.get("resolved_transition")
    target_scene_id = resolution.get("target_scene_id")
    originating_scene_id = resolution.get("originating_scene_id")
    # When resolution omitted, these will be None / empty.
    state_changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), Mapping) else {}

    sess_scene_after = session.get("active_scene_id")
    scene_after = str(sess_scene_after).strip() if isinstance(sess_scene_after, str) and sess_scene_after.strip() else None
    scene_before = (
        str(originating_scene_id).strip()
        if isinstance(originating_scene_id, str) and str(originating_scene_id).strip()
        else None
    )
    scene_target = (
        str(target_scene_id).strip() if isinstance(target_scene_id, str) and str(target_scene_id).strip() else None
    )

    # Also capture compact seam metadata if present (operators rely on it).
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), Mapping) else {}
    md = gm.get("metadata") if isinstance(gm.get("metadata"), Mapping) else {}
    narration_seam = md.get("narration_seam") if isinstance(md.get("narration_seam"), Mapping) else {}
    seam_compact = {
        k: narration_seam[k]
        for k in (
            "path_kind",
            "ctir_backed",
            "plan_driven",
            "bundle_required",
            "emergency_nonplan_output",
            "explicit_nonplan_model_narration",
        )
        if k in narration_seam
    }

    out: dict[str, Any] = {
        "bundle_present": bundle_present,
        "narrative_plan_present": narrative_plan_present,
        "transition_node": tn_dict,
        "resolution_transition_signal": bool(resolved_transition) if isinstance(resolved_transition, bool) else None,
        "resolution_state_changes": dict(state_changes) if isinstance(state_changes, Mapping) else {},
        "scene_before": scene_before,
        "scene_target": scene_target,
        "scene_after": scene_after,
        "narration_seam": seam_compact,
        "api_error": payload.get("error"),
    }
    return out


def evaluate_transition_convergence_for_turn_rows(turns: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute transition invariants for normalized spine turn rows.

    This is observational: it inspects only turn text and recorded ``meta.transition_convergence``.
    """
    checked = 0
    plan_backed = 0
    plan_missing = 0
    invalid_plan = 0
    hidden_mutation = 0
    divergence = 0
    observed_without_plan = 0
    implied_without_plan = 0

    failure_details: list[dict[str, Any]] = []

    def _fail(turn_index: int, marker: str, *, suspected_source: str, codes: Sequence[str] = ()) -> None:
        failure_details.append(
            {
                "turn_index": int(turn_index),
                "marker": str(marker),
                "suspected_source": str(suspected_source),
                "reason_codes": [str(c) for c in codes if c is not None],
            },
        )

    for t in turns:
        turn_index = int(t.get("turn_index", -1))
        gm_text = str(t.get("gm_text") or "")
        meta = t.get("meta") if isinstance(t.get("meta"), Mapping) else {}
        tc = meta.get(_META_KEY) if isinstance(meta.get(_META_KEY), Mapping) else None
        tc = tc if isinstance(tc, Mapping) else {}

        # If this turn has no transition meta and no detectable transition language, skip (no observations).
        implied_type = _detect_output_transition_type(gm_text)
        implied_transition = implied_type is not None
        observed_transition = _observed_transition_signal(tc)
        plan = tc.get("transition_node") if isinstance(tc.get("transition_node"), Mapping) else None
        plan_requires = _plan_requires_transition(plan)

        if not (implied_transition or observed_transition or plan_requires):
            continue

        checked += 1

        if plan is None:
            if observed_transition:
                observed_without_plan += 1
                _fail(
                    turn_index,
                    "observed_transition_without_transition_node",
                    suspected_source="ctir_or_resolution_missing_signal",
                    codes=["ctir_or_resolution_missing_signal"],
                )
            if implied_transition:
                implied_without_plan += 1
                _fail(
                    turn_index,
                    f"output_implied_transition_without_transition_node:{implied_type}",
                    suspected_source="final_emission_hidden_transition_mutation",
                    codes=["final_emission_hidden_transition_mutation"],
                )
            plan_missing += 1
            continue

        # Plan present: validate structure and required fields.
        plan_issues = observational_transition_node_issues(plan)
        if plan_issues:
            invalid_plan += 1
            _fail(
                turn_index,
                f"invalid_planned_transition:{plan_issues[0]}",
                suspected_source="narrative_planning_missing_or_invalid_transition_node",
                codes=["narrative_planning_missing_or_invalid_transition_node"],
            )
            # Continue evaluating implied/observed vs plan when possible.

        plan_backed += 1

        # Check 1: output-implied transition requires plan-defined required transition w/ anchors.
        if implied_transition:
            if not _plan_meets_required_transition_fields(plan):
                hidden_mutation += 1
                _fail(
                    turn_index,
                    f"output_implied_transition_but_plan_not_required_or_incomplete:{implied_type}",
                    suspected_source="final_emission_hidden_transition_mutation",
                    codes=["final_emission_hidden_transition_mutation"],
                )
            else:
                # Detect rough contradictions: planned type vs implied type (when both are specific).
                planned_type = str(plan.get("transition_type") or "").strip()
                if _types_contradict(planned_type, implied_type):
                    divergence += 1
                    _fail(
                        turn_index,
                        f"plan_output_transition_type_contradiction:plan={planned_type}:output={implied_type}",
                        suspected_source="final_emission_plan_output_divergence",
                        codes=["final_emission_plan_output_divergence"],
                    )

        # Check 2: observed transition requires plan-defined required transition w/ anchors.
        if observed_transition:
            if not _plan_meets_required_transition_fields(plan):
                observed_without_plan += 1
                _fail(
                    turn_index,
                    "state_observed_transition_but_plan_missing_required_fields",
                    suspected_source="narrative_planning_missing_or_invalid_transition_node",
                    codes=["narrative_planning_missing_or_invalid_transition_node"],
                )
            else:
                # Optional correspondence check when scene_before/after exist.
                obs_codes = _anchors_correspond_to_observed_scene(tc, plan)
                if obs_codes:
                    divergence += 1
                    _fail(
                        turn_index,
                        f"planned_anchors_do_not_match_observed:{obs_codes[0]}",
                        suspected_source="final_emission_plan_output_divergence",
                        codes=["final_emission_plan_output_divergence"],
                    )

        # Check 4: plan/output divergence when plan requires transition but output is pure continuation.
        if plan_requires and not implied_transition and not observed_transition:
            divergence += 1
            _fail(
                turn_index,
                "planned_transition_required_but_output_shows_no_transition",
                suspected_source="final_emission_plan_output_divergence",
                codes=["final_emission_plan_output_divergence"],
            )

        # Check 5: hidden transition mutation (output implies transition when plan says none).
        if implied_transition and _plan_says_no_transition(plan):
            hidden_mutation += 1
            _fail(
                turn_index,
                f"hidden_transition_mutation:plan_none_output={implied_type}",
                suspected_source="final_emission_hidden_transition_mutation",
                codes=["final_emission_hidden_transition_mutation"],
            )

    hard_fail = bool(failure_details)
    if checked == 0:
        verdict = "no_observations"
    elif hard_fail:
        verdict = "fail"
    else:
        verdict = "pass"

    return {
        "transition_turns_checked": checked,
        "transition_plan_backed_count": plan_backed,
        "transition_plan_missing_count": plan_missing,
        "transition_invalid_plan_count": invalid_plan,
        "transition_hidden_mutation_count": hidden_mutation,
        "transition_plan_output_divergence_count": divergence,
        "transition_observed_without_plan_count": observed_without_plan,
        "transition_implied_without_plan_count": implied_without_plan,
        "transition_convergence_verdict": verdict,
        "transition_convergence_failure_details": failure_details,
    }


def observational_transition_node_issues(node: Mapping[str, Any] | None) -> list[str]:
    """Return issue codes; empty means structurally acceptable for recorded transition_node."""
    if node is None:
        return ["transition_node_absent"]
    if not isinstance(node, Mapping):
        return ["transition_node_not_mapping"]
    issues: list[str] = []

    keys = {str(k) for k in node.keys() if isinstance(k, str)}
    unknown = sorted(keys - _TRANSITION_NODE_ALLOWED_TOP_KEYS)
    missing = sorted(_TRANSITION_NODE_ALLOWED_TOP_KEYS - keys)
    # Missing is tolerated if optional fields absent; enforce only core required keys.
    core_required = ("transition_required", "transition_type", "before_anchor", "after_anchor", "derivation_codes")
    for k in core_required:
        if k not in node:
            issues.append(f"transition_node_missing_key:{k}")
            break
    if unknown:
        issues.append(f"transition_node_unknown_keys:{','.join(unknown[:16])}")

    req = node.get("transition_required")
    if not isinstance(req, bool):
        issues.append("transition_node_transition_required_not_bool")

    ttype = str(node.get("transition_type") or "").strip()
    if ttype and ttype not in _TRANSITION_TYPES:
        issues.append("transition_node_bad_transition_type")

    deriv = node.get("derivation_codes")
    if deriv is not None and not isinstance(deriv, list):
        issues.append("transition_node_derivation_codes_not_list")
    if isinstance(deriv, list):
        for item in deriv:
            if isinstance(item, str) and item.startswith("validation_error:"):
                issues.append("transition_node_derivation_contains_validation_error")
                break

    # Required transitions must not be missing anchors and must not claim type none.
    if req is True:
        if ttype == "none":
            issues.append("transition_node_required_but_type_none")
        if not _anchor_is_present(node.get("before_anchor")) or not _anchor_is_present(node.get("after_anchor")):
            issues.append("transition_node_missing_anchors_for_required_transition")
        if _anchor_is_present(node.get("before_anchor")) and not _anchor_has_identifier(node.get("before_anchor")):
            issues.append("transition_node_before_anchor_missing_identifier")
        if _anchor_is_present(node.get("after_anchor")) and not _anchor_has_identifier(node.get("after_anchor")):
            issues.append("transition_node_after_anchor_missing_identifier")
    else:
        # Non-required transitions must not include anchors.
        if _anchor_is_present(node.get("before_anchor")) or _anchor_is_present(node.get("after_anchor")):
            # Allow empty dicts, but disallow substantive anchors.
            if bool(node.get("before_anchor")) or bool(node.get("after_anchor")):
                issues.append("transition_node_unexpected_anchors_when_not_required")

    # Anchor key hygiene (only when mapping).
    for which in ("before_anchor", "after_anchor"):
        a = node.get(which)
        if a is None:
            continue
        if not isinstance(a, Mapping):
            issues.append(f"transition_node_{which}_not_mapping")
            continue
        akeys = {str(k) for k in a.keys() if isinstance(k, str)}
        bad = sorted(akeys - _ANCHOR_ALLOWED_KEYS)
        if bad:
            issues.append(f"transition_node_{which}_anchor_unknown_keys:{','.join(bad[:12])}")
            break
    _ = missing  # reserved for future stricter checks; keep stable for now.
    return issues


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


_TIME_SKIP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(later|after\s+some\s+time|after\s+a\s+while|hours\s+later|days\s+later|the\s+next\s+day)\b", re.I),
    re.compile(r"\b(meanwhile|elsewhere|at\s+the\s+same\s+time)\b", re.I),
    re.compile(r"\b(time\s+passes|time\s+slips|time\s+drifts)\b", re.I),
)
_SCENE_CUT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(the\s+scene\s+shifts|scene\s+shifts|the\s+scene\s+cuts|cut\s+to)\b", re.I),
    re.compile(r"\b(back\s+at|across\s+town|in\s+another\s+place)\b", re.I),
)
_LOCATION_MOVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(you\s+arrive|you\s+reach|you\s+depart|you\s+leave)\b", re.I),
    re.compile(r"\b(after\s+travel(?:ing|ling)|after\s+the\s+journey|on\s+the\s+road)\b", re.I),
    re.compile(r"\b(you\s+head\s+to|you\s+make\s+your\s+way\s+to)\b", re.I),
)


def _detect_output_transition_type(gm_text: str) -> str | None:
    """Return a coarse transition type if obvious markers exist; else None (conservative)."""
    raw = str(gm_text or "")
    if not raw.strip():
        return None
    for rx in _LOCATION_MOVE_PATTERNS:
        if rx.search(raw):
            return "location_movement"
    for rx in _SCENE_CUT_PATTERNS:
        if rx.search(raw):
            return "scene_cut"
    for rx in _TIME_SKIP_PATTERNS:
        if rx.search(raw):
            return "time_skip"
    return None


def _anchor_is_present(a: Any) -> bool:
    return isinstance(a, Mapping) and bool(a)


def _anchor_has_identifier(a: Any) -> bool:
    if not isinstance(a, Mapping):
        return False
    ident = a.get("identifier")
    return isinstance(ident, str) and bool(ident.strip())


def _plan_requires_transition(plan: Mapping[str, Any] | None) -> bool:
    if not isinstance(plan, Mapping):
        return False
    return plan.get("transition_required") is True


def _plan_says_no_transition(plan: Mapping[str, Any] | None) -> bool:
    if not isinstance(plan, Mapping):
        return False
    if plan.get("transition_required") is True:
        return False
    return str(plan.get("transition_type") or "").strip() == "none"


def _plan_meets_required_transition_fields(plan: Mapping[str, Any] | None) -> bool:
    if not isinstance(plan, Mapping):
        return False
    if plan.get("transition_required") is not True:
        return False
    if str(plan.get("transition_type") or "").strip() in ("", "none"):
        return False
    if not _anchor_is_present(plan.get("before_anchor")) or not _anchor_is_present(plan.get("after_anchor")):
        return False
    return True


def _observed_transition_signal(tc: Mapping[str, Any]) -> bool:
    """Observed transition: conservative, uses recorded resolution/state fields only."""
    if not isinstance(tc, Mapping):
        return False
    sig = tc.get("resolution_transition_signal")
    if sig is True:
        return True
    # Also treat explicit scene delta from recorded ids as observed (when both available).
    before = tc.get("scene_before")
    after = tc.get("scene_after")
    if isinstance(before, str) and isinstance(after, str) and before.strip() and after.strip():
        if before.strip() != after.strip():
            return True
    target = tc.get("scene_target")
    if isinstance(before, str) and isinstance(target, str) and before.strip() and target.strip():
        if before.strip() != target.strip():
            return True
    # state_changes can carry scene_changed / arrived_at_scene flags.
    sc = tc.get("resolution_state_changes")
    if isinstance(sc, Mapping):
        if sc.get("scene_changed") is True or sc.get("arrived_at_scene") is True:
            return True
    return False


def _anchors_correspond_to_observed_scene(tc: Mapping[str, Any], plan: Mapping[str, Any]) -> list[str]:
    """Best-effort correspondence check; never infers missing anchors."""
    codes: list[str] = []
    before_obs = tc.get("scene_before")
    after_obs = tc.get("scene_after") or tc.get("scene_target")
    ba = plan.get("before_anchor") if isinstance(plan.get("before_anchor"), Mapping) else {}
    aa = plan.get("after_anchor") if isinstance(plan.get("after_anchor"), Mapping) else {}
    ba_scene = ba.get("scene_id") if isinstance(ba.get("scene_id"), str) else None
    aa_scene = aa.get("scene_id") if isinstance(aa.get("scene_id"), str) else None
    if isinstance(before_obs, str) and before_obs.strip() and isinstance(ba_scene, str) and ba_scene.strip():
        if before_obs.strip() != ba_scene.strip():
            codes.append("before_scene_mismatch")
    if isinstance(after_obs, str) and after_obs.strip() and isinstance(aa_scene, str) and aa_scene.strip():
        if after_obs.strip() != aa_scene.strip():
            codes.append("after_scene_mismatch")
    return codes


def _types_contradict(planned: str, implied: str) -> bool:
    p = str(planned or "").strip()
    o = str(implied or "").strip()
    if not p or not o:
        return False
    if p in ("mixed", "unknown") or o in ("mixed", "unknown"):
        return False
    # Treat none as contradiction when implied is present.
    if p == "none" and o != "none":
        return True
    return p != o

