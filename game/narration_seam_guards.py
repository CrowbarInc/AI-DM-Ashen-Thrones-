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
