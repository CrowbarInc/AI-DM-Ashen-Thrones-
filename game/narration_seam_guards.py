"""Block C — narrow runtime guards for the CTIR → narration plan bundle → prompt_context → GPT seam.

Operator/debug consumers read ``gm["metadata"]["narration_seam"]`` and session ``debug_traces`` entries
emitted by :func:`record_planner_bypass_attempt` / :func:`record_emergency_nonplan_output`.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, get_attached_ctir
from game.narration_plan_bundle import (
    get_attached_narration_plan_bundle,
    get_narration_plan_bundle_stamp,
)
from game.narrative_planning import infer_scene_opening_reason, validate_scene_opening
from game.state_authority import PLAYER_VISIBLE_STATE, build_state_mutation_trace
from game.storage import append_debug_trace

# --- Path inventory (Block C matrix; keep in sync with runtime call sites) ---

# Every ``path_kind`` passed to :func:`annotate_narration_path_kind` from player-facing turn code
# should appear here so C1 audits catch orphan classifications (update alongside ``game.api``).
REGISTERED_NARRATION_PATH_KINDS: frozenset[str] = frozenset(
    {
        "manual_play_gpt_budget_exceeded",
        "resolved_turn_ctir_upstream_fast_fallback",
        "resolved_turn_ctir_force_terminal_fallback",
        "resolved_turn_ctir_bundle",
        "resolved_turn_ctir_planner_convergence_seam",
        "non_resolution_model_narration",
        "engine_combat_initiative_message",
        "engine_combat_end_turn_message",
        "engine_offscene_social_target",
        "engine_check_required_prompt",
        "engine_empty_narration_placeholder",
        "engine_adjudication_query",
    }
)

NARRATION_PATH_MATRIX: tuple[dict[str, Any], ...] = (
    {
        "path": "resolved_turn_ctir_bundle (normal GPT after engine resolution)",
        "ctir_backed": True,
        "bundle_required": True,
        "plan_driven": True,
        "emergency_only": False,
        "notes": "_run_resolved_turn_pipeline → _build_gpt_narration_from_authoritative_state",
    },
    {
        "path": "resolved_turn_ctir_planner_convergence_seam",
        "ctir_backed": True,
        "bundle_required": True,
        "plan_driven": False,
        "emergency_only": True,
        "notes": "CTIR/plan/prompt convergence failed; deterministic_terminal_repair-style terminal output",
    },
    {
        "path": "resolved_turn_ctir_upstream_fast_fallback / resolved_turn_ctir_force_terminal_fallback",
        "ctir_backed": True,
        "bundle_required": True,
        "plan_driven": False,
        "emergency_only": True,
        "notes": "Initial prompt used bundle seam; terminal text is repair-layer output",
    },
    {
        "path": "chat procedural freeform (unparsed → GPT, no resolution dict)",
        "ctir_backed": False,
        "bundle_required": False,
        "plan_driven": False,
        "emergency_only": False,
        "notes": "Explicit non-plan model narration; resolution=None",
    },
    {
        "path": "engine check prompt / offscene social / adjudication_query",
        "ctir_backed": False,
        "bundle_required": False,
        "plan_driven": False,
        "emergency_only": False,
        "notes": "Engine-authored player text; no GPT",
    },
    {
        "path": "combat roll_initiative / end_turn app strings",
        "ctir_backed": False,
        "bundle_required": False,
        "plan_driven": False,
        "emergency_only": False,
        "notes": "Mechanical UI narration; no GPT",
    },
    {
        "path": "manual_play GPT budget exceeded (synthetic GM)",
        "ctir_backed": False,
        "bundle_required": False,
        "plan_driven": False,
        "emergency_only": True,
        "notes": "Safety cap; no model call",
    },
    {
        "path": "upstream API fast fallback / force_terminal_retry (post-model repair)",
        "ctir_backed": "partial",
        "bundle_required": False,
        "plan_driven": False,
        "emergency_only": True,
        "notes": "Repair layer; not a fresh plan bundle build",
    },
)


def path_matrix_markdown() -> str:
    """Human-readable matrix for operators (source of truth is NARRATION_PATH_MATRIX + code paths)."""
    lines = ["| path | CTIR-backed | bundle-required | plan-driven | emergency-only |", "|---|---:|---:|---:|---:|"]
    for row in NARRATION_PATH_MATRIX:
        lines.append(
            "| {path} | {ctir} | {br} | {pd} | {eo} |".format(
                path=row["path"],
                ctir=row["ctir_backed"],
                br=row["bundle_required"],
                pd=row["plan_driven"],
                eo=row["emergency_only"],
            )
        )
    return "\n".join(lines)


def annotate_narration_path_kind(
    gm: MutableMapping[str, Any] | None,
    *,
    path_kind: str,
    ctir_backed: bool | str,
    bundle_required: bool,
    plan_driven: bool,
    emergency_nonplan_output: bool = False,
    explicit_nonplan_model_narration: bool = False,
    same_turn_retry_messages_reused: bool | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Attach compact seam metadata for downstream gate / logs (idempotent merge on ``metadata``)."""
    if not isinstance(gm, MutableMapping):
        return
    md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    block: dict[str, Any] = {
        "path_kind": str(path_kind or "").strip() or "unknown",
        "ctir_backed": ctir_backed,
        "bundle_required": bool(bundle_required),
        "plan_driven": bool(plan_driven),
        "emergency_nonplan_output": bool(emergency_nonplan_output),
        "explicit_nonplan_model_narration": bool(explicit_nonplan_model_narration),
    }
    if same_turn_retry_messages_reused is not None:
        block["same_turn_retry_messages_reused"] = bool(same_turn_retry_messages_reused)
    if isinstance(extra, Mapping) and extra:
        block["extra"] = dict(extra)
    prev_seam = md.get("narration_seam")
    base_seam = dict(prev_seam) if isinstance(prev_seam, dict) else {}
    gm["metadata"] = {**md, "narration_seam": {**base_seam, **block}}


def classify_narration_continuation_path(
    *,
    session: MutableMapping[str, Any] | None,
    narration_seam: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Classify the *continuation* status/kind for the current narration output.

    Debug-only: this must never drive orchestration (C1-B inventory only).
    Returns a JSON-safe dict with stable keys + reason codes.
    """
    seam = dict(narration_seam) if isinstance(narration_seam, Mapping) else {}
    path_kind = str(seam.get("path_kind") or "").strip() or "unknown"
    ctir_backed = seam.get("ctir_backed")
    plan_driven = bool(seam.get("plan_driven"))
    emergency = bool(seam.get("emergency_nonplan_output"))
    explicit_nonplan = bool(seam.get("explicit_nonplan_model_narration"))

    reason_codes: list[str] = []

    # --- Opening vs continuation ---
    is_continuation_turn: bool
    opening_reason = "unknown"
    if isinstance(ctir_backed, bool) and ctir_backed and isinstance(session, MutableMapping):
        ctir = get_attached_ctir(session)
        bundle = get_attached_narration_plan_bundle(session)
        if isinstance(ctir, Mapping) and isinstance(bundle, Mapping):
            ri = bundle.get("renderer_inputs") if isinstance(bundle.get("renderer_inputs"), Mapping) else {}
            pm = bundle.get("plan_metadata") if isinstance(bundle.get("plan_metadata"), Mapping) else {}
            narration_obligations = ri.get("narration_obligations") if isinstance(ri.get("narration_obligations"), Mapping) else {}
            session_interaction = (
                pm.get("planning_session_interaction")
                if isinstance(pm.get("planning_session_interaction"), Mapping)
                else {}
            )
            opening_reason = infer_scene_opening_reason(
                ctir,
                narration_obligations=narration_obligations,
                session_interaction=session_interaction,
            )
            is_continuation_turn = opening_reason == "none"
            reason_codes.append(f"opening_reason:{opening_reason}")
        else:
            # CTIR-backed path, but we cannot inspect the bundle/ctir for opening inference.
            is_continuation_turn = True
            reason_codes.append("opening_reason:unknown_missing_ctir_or_bundle")
    else:
        # Non-CTIR paths are never treated as scene openings (openings are CTIR semantics).
        is_continuation_turn = True
        reason_codes.append("opening_reason:non_ctir_path_assumed_continuation")

    # --- Continuation path kind ---
    continuation_path_kind: str | None = None
    requires_plan_driven_continuation = False
    allows_nonplan_output = False

    if not is_continuation_turn:
        continuation_path_kind = None
        requires_plan_driven_continuation = False
        allows_nonplan_output = True
        reason_codes.append("turn_is_scene_opening")
    elif emergency:
        continuation_path_kind = "emergency_nonplan_output"
        allows_nonplan_output = True
        requires_plan_driven_continuation = False
        reason_codes.append("seam_emergency_nonplan_output")
    elif explicit_nonplan or path_kind == "non_resolution_model_narration":
        continuation_path_kind = "explicit_nonplan_model_narration"
        allows_nonplan_output = True
        requires_plan_driven_continuation = False
        reason_codes.append("seam_explicit_nonplan_model_narration")
    elif isinstance(ctir_backed, bool) and ctir_backed:
        # CTIR-backed continuation.
        if plan_driven:
            # Heuristic: pressures present → pressure-driven continuation; otherwise plan-driven.
            pressures_present = False
            if isinstance(session, MutableMapping):
                bundle = get_attached_narration_plan_bundle(session)
                plan = bundle.get("narrative_plan") if isinstance(bundle, Mapping) else None
                ap = plan.get("active_pressures") if isinstance(plan, Mapping) else None
                pressures_present = isinstance(ap, Mapping) and bool(ap)
            continuation_path_kind = "pressure_driven_continuation" if pressures_present else "plan_driven_continuation"
            requires_plan_driven_continuation = True
            allows_nonplan_output = False
            reason_codes.append("ctir_backed_plan_driven")
            if pressures_present:
                reason_codes.append("plan_active_pressures_present")
        else:
            continuation_path_kind = "passive_turn_continuation"
            requires_plan_driven_continuation = False
            allows_nonplan_output = True
            reason_codes.append("ctir_backed_not_plan_driven")
    else:
        # Non-CTIR engine or unknown path.
        if path_kind.startswith("engine_"):
            continuation_path_kind = "non_ctir_engine_output"
            requires_plan_driven_continuation = False
            allows_nonplan_output = True
            reason_codes.append("non_ctir_engine_output")
        else:
            continuation_path_kind = "non_ctir_engine_output"
            requires_plan_driven_continuation = False
            allows_nonplan_output = True
            reason_codes.append("non_ctir_unknown_path_assumed_engine_or_external")

    # --- JSON-safety / stability ---
    out: dict[str, Any] = {
        "is_continuation_turn": bool(is_continuation_turn),
        "continuation_path_kind": continuation_path_kind,
        "requires_plan_driven_continuation": bool(requires_plan_driven_continuation),
        "allows_nonplan_output": bool(allows_nonplan_output),
        "reason_codes": [str(x) for x in reason_codes if isinstance(x, str) and x],
    }
    return out


def annotate_narration_continuation_classification(
    gm: MutableMapping[str, Any] | None,
    *,
    session: MutableMapping[str, Any] | None,
) -> None:
    """Attach continuation classification into ``gm["metadata"]["narration_seam"]``.

    Must be called only as a debug/read-side annotation (no orchestration).
    """
    if not isinstance(gm, MutableMapping):
        return
    md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    prev_seam = md.get("narration_seam")
    base_seam = dict(prev_seam) if isinstance(prev_seam, dict) else {}
    seam = dict(base_seam)
    classified = classify_narration_continuation_path(session=session, narration_seam=seam)
    prev_cont = seam.get("continuation")
    carry = dict(prev_cont) if isinstance(prev_cont, Mapping) else {}
    seam["continuation"] = {**carry, **dict(classified)}
    gm["metadata"] = {**md, "narration_seam": seam}


def enforce_plan_driven_continuation_invariant(
    gm: MutableMapping[str, Any] | None,
    *,
    session: MutableMapping[str, Any] | None,
    bundle_seam_requirement: Mapping[str, Any] | None = None,
    turn_stamp: str | None = None,
) -> dict[str, Any]:
    """Enforce C1-B: CTIR-backed continuation requiring plan-driven continuation must be plan-verified.

    - Must not reclassify independently: consumes existing ``gm.metadata.narration_seam.continuation``
      (created by :func:`annotate_narration_continuation_classification`).
    - Produces enforcement metadata under ``gm["metadata"]["narration_seam"]["continuation"]``.
    - Returns a compact status dict for callers (no player-facing narration mutation).
    """
    if not isinstance(gm, MutableMapping):
        return {"ok": True, "skipped": "no_gm"}
    md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    seam0 = md.get("narration_seam")
    seam: dict[str, Any] = dict(seam0) if isinstance(seam0, dict) else {}
    cont0 = seam.get("continuation")
    cont: dict[str, Any] = dict(cont0) if isinstance(cont0, Mapping) else {}

    # If callers forgot to annotate, do it here (idempotent merge).
    if not cont:
        annotate_narration_continuation_classification(gm, session=session)
        md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
        seam = dict(md.get("narration_seam") or {}) if isinstance(md.get("narration_seam"), dict) else {}
        cont = dict(seam.get("continuation") or {}) if isinstance(seam.get("continuation"), Mapping) else {}

    ctir_backed = seam.get("ctir_backed") is True
    emergency = bool(seam.get("emergency_nonplan_output"))
    explicit_nonplan = bool(seam.get("explicit_nonplan_model_narration"))
    path_kind = str(seam.get("path_kind") or "").strip()
    is_engine_only = path_kind.startswith("engine_")

    is_continuation_turn = bool(cont.get("is_continuation_turn"))
    requires_plan_driven = bool(cont.get("requires_plan_driven_continuation"))
    enforcement_applied = bool(ctir_backed and is_continuation_turn and requires_plan_driven and (not is_engine_only))

    # --- Verification ---
    ts = str(turn_stamp or "").strip()
    bs = dict(bundle_seam_requirement) if isinstance(bundle_seam_requirement, Mapping) else {}
    verified = False
    failure_reason: str | None = None

    if emergency or explicit_nonplan or (not ctir_backed) or is_engine_only:
        verified = False
        # Even when the output is an explicit emergency/nonplan path, preserve the triggering
        # seam-verification failure when available (operators need it traceable).
        if bs and bs.get("ok") is False:
            failure_reason = str(bs.get("error") or bs.get("skipped") or "bundle_seam_requirement_failed")
        else:
            failure_reason = None
    else:
        # If we already have a seam verification result, prefer it (no double-check divergence).
        if bs and bs.get("ok") is True:
            verified = True
        elif bs and bs.get("ok") is False:
            verified = False
            failure_reason = str(bs.get("error") or bs.get("skipped") or "bundle_seam_requirement_failed")
        else:
            # Fallback verification for callers that did not pass ``bundle_seam_requirement``.
            if not isinstance(session, MutableMapping):
                verified = False
                failure_reason = "no_session"
            else:
                ctir = get_attached_ctir(session)
                if not isinstance(ctir, Mapping):
                    verified = False
                    failure_reason = "ctir_absent"
                elif not ts:
                    verified = False
                    failure_reason = "empty_turn_stamp"
                else:
                    cstamp = str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip()
                    if cstamp != ts:
                        verified = False
                        failure_reason = "ctir_stamp_mismatch"
                    else:
                        bundle = get_attached_narration_plan_bundle(session)
                        bstamp = get_narration_plan_bundle_stamp(session)
                        if bstamp != ts:
                            verified = False
                            failure_reason = "narration_plan_bundle_stamp_mismatch"
                        elif not isinstance(bundle, Mapping):
                            verified = False
                            failure_reason = "bundle_absent"
                        else:
                            np = bundle.get("narrative_plan")
                            if not isinstance(np, Mapping) or not np:
                                verified = False
                                failure_reason = "narrative_plan_missing"
                            else:
                                verified = True

    # --- Source labeling ---
    if emergency:
        source = "emergency_nonplan"
    elif explicit_nonplan or cont.get("continuation_path_kind") == "explicit_nonplan_model_narration":
        source = "explicit_nonplan_model_narration"
    elif is_engine_only or cont.get("continuation_path_kind") == "non_ctir_engine_output":
        source = "engine_only"
    elif ctir_backed and verified:
        source = "narrative_plan_bundle"
    elif ctir_backed and requires_plan_driven:
        source = "unverified"
    else:
        source = "engine_only"

    cont_out = dict(cont)
    cont_out["continuation_plan_verified"] = bool(verified)
    cont_out["continuation_plan_failure_reason"] = str(failure_reason) if failure_reason else None
    cont_out["continuation_source"] = source
    cont_out["continuation_enforcement_applied"] = bool(enforcement_applied)

    seam["continuation"] = cont_out
    gm["metadata"] = {**md, "narration_seam": seam}

    return {
        "ok": True,
        "continuation_plan_verified": bool(verified),
        "continuation_plan_failure_reason": str(failure_reason) if failure_reason else None,
        "continuation_source": source,
        "continuation_enforcement_applied": bool(enforcement_applied),
    }


def record_explicit_nonplan_model_narration(
    session: MutableMapping[str, Any] | None,
    *,
    reason: str,
    owner_module: str,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """GPT narration without a resolved engine ``resolution`` dict (no CTIR / bundle seam for that turn)."""
    if not isinstance(session, MutableMapping):
        return
    payload = {"reason": str(reason or "").strip() or "unknown", "explicit_nonplan_model_narration": True}
    if isinstance(extra, Mapping):
        payload.update(dict(extra))
    append_debug_trace(
        session,
        build_state_mutation_trace(
            domain=PLAYER_VISIBLE_STATE,
            owner_module=owner_module,
            operation="explicit_nonplan_model_narration",
            extra=payload,
        ),
    )


def record_planner_bypass_attempt(
    session: MutableMapping[str, Any] | None,
    *,
    reason: str,
    owner_module: str,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Audit signal when CTIR narration expected a stamp-matched bundle but invariant failed."""
    if not isinstance(session, MutableMapping):
        return
    payload = {"reason": str(reason or "").strip() or "unknown"}
    if isinstance(extra, Mapping):
        payload.update(dict(extra))
    append_debug_trace(
        session,
        build_state_mutation_trace(
            domain=PLAYER_VISIBLE_STATE,
            owner_module=owner_module,
            operation="semantic_bypass_blocked",
            extra=payload,
        ),
    )


def record_emergency_nonplan_output(
    session: MutableMapping[str, Any] | None,
    *,
    reason: str,
    owner_module: str,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Rare / abnormal outputs that bypass or exit the normal plan-driven model narration success path."""
    if not isinstance(session, MutableMapping):
        return
    payload = {"reason": str(reason or "").strip() or "unknown", "emergency_nonplan_output": True}
    if isinstance(extra, Mapping):
        payload.update(dict(extra))
    append_debug_trace(
        session,
        build_state_mutation_trace(
            domain=PLAYER_VISIBLE_STATE,
            owner_module=owner_module,
            operation="emergency_nonplan_output",
            extra=payload,
        ),
    )


def require_narration_plan_bundle_for_ctir_turn(
    session: MutableMapping[str, Any] | None,
    *,
    turn_stamp: str,
    owner_module: str,
) -> dict[str, Any]:
    """After ``ensure_narration_plan_bundle_for_turn``, verify bundle + narrative_plan + stamp alignment.

    Returns a small status dict for callers; emits :func:`record_planner_bypass_attempt` on failure.
    """
    if not isinstance(session, MutableMapping):
        return {"ok": True, "skipped": "no_session"}
    ctir = get_attached_ctir(session)
    if ctir is None:
        return {"ok": True, "skipped": "no_ctir"}
    ts = str(turn_stamp or "").strip()
    if not ts:
        record_planner_bypass_attempt(session, reason="empty_turn_stamp", owner_module=owner_module)
        return {"ok": False, "error": "empty_turn_stamp"}
    cstamp = str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip()
    if cstamp != ts:
        record_planner_bypass_attempt(
            session,
            reason="ctir_stamp_mismatch",
            owner_module=owner_module,
            extra={"expected": ts, "session_ctir_stamp": cstamp},
        )
        return {"ok": False, "error": "ctir_stamp_mismatch"}
    bundle = get_attached_narration_plan_bundle(session)
    bstamp = get_narration_plan_bundle_stamp(session)
    if bstamp != ts:
        record_planner_bypass_attempt(
            session,
            reason="narration_plan_bundle_stamp_mismatch",
            owner_module=owner_module,
            extra={"expected": ts, "bundle_stamp": bstamp},
        )
        return {"ok": False, "error": "narration_plan_bundle_stamp_mismatch"}
    if not isinstance(bundle, dict):
        record_planner_bypass_attempt(session, reason="bundle_absent", owner_module=owner_module, extra={"expected_stamp": ts})
        return {"ok": False, "error": "bundle_absent"}
    if not isinstance(bundle.get("narrative_plan"), dict):
        pm = bundle.get("plan_metadata") if isinstance(bundle.get("plan_metadata"), dict) else {}
        record_planner_bypass_attempt(
            session,
            reason="narrative_plan_missing",
            owner_module=owner_module,
            extra={
                "narration_plan_bundle_error": pm.get("narration_plan_bundle_error"),
                "semantic_bypass_blocked": pm.get("semantic_bypass_blocked"),
            },
        )
        return {"ok": False, "error": "narrative_plan_missing"}
    plan = bundle["narrative_plan"]
    pm = bundle.get("plan_metadata") if isinstance(bundle.get("plan_metadata"), dict) else {}
    ri = bundle.get("renderer_inputs") if isinstance(bundle.get("renderer_inputs"), dict) else {}
    no = ri.get("narration_obligations") if isinstance(ri.get("narration_obligations"), dict) else {}
    si = pm.get("planning_session_interaction") if isinstance(pm.get("planning_session_interaction"), dict) else {}
    opening_reason = infer_scene_opening_reason(ctir, narration_obligations=no, session_interaction=si or None)
    opening_required = opening_reason != "none"
    so_err = validate_scene_opening(
        plan.get("scene_opening"),
        ctir=ctir,
        public_scene_slice=None,
        plan_active_pressures=plan.get("active_pressures")
        if isinstance(plan.get("active_pressures"), dict)
        else {},
        scene_anchors=plan.get("scene_anchors") if isinstance(plan.get("scene_anchors"), dict) else {},
        opening_required=opening_required,
    )
    if so_err:
        record_planner_bypass_attempt(
            session,
            reason="scene_opening_seam_invalid",
            owner_module=owner_module,
            extra={
                "validate_scene_opening": so_err,
                "opening_reason_inferred": opening_reason,
                "opening_required": opening_required,
            },
        )
        return {"ok": False, "error": "scene_opening_seam_invalid", "scene_opening_error": so_err}
    return {"ok": True}


def verify_same_turn_narration_stamp_for_retry(
    session: MutableMapping[str, Any] | None,
    *,
    expected_ctir_stamp: str,
    owner_module: str,
    expected_narration_plan_bundle_stamp: str | None = None,
) -> bool:
    """Call before a same-turn GPT retry; logs if CTIR or narration plan bundle stamp drifted."""
    if not isinstance(session, MutableMapping):
        return True
    exp = str(expected_ctir_stamp or "").strip()
    if not exp:
        return True
    cur = str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip()
    if cur != exp:
        record_planner_bypass_attempt(
            session,
            reason="same_turn_retry_ctir_stamp_drift",
            owner_module=owner_module,
            extra={"expected": exp, "current": cur},
        )
        return False
    exp_bundle = str(expected_narration_plan_bundle_stamp or "").strip()
    if not exp_bundle:
        return True
    bstamp = get_narration_plan_bundle_stamp(session)
    if bstamp == exp_bundle:
        return True
    record_planner_bypass_attempt(
        session,
        reason="same_turn_retry_narration_plan_bundle_stamp_drift",
        owner_module=owner_module,
        extra={"expected": exp_bundle, "current": bstamp},
    )
    return False
