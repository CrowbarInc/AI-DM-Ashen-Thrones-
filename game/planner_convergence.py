"""Planner convergence contract (Block A): explicit inventory labels for CTIR → plan → prompt → gate.

Classification (intended invariant **CTIR → Narrative Plan → GPT → Gate** for normal narration):

1. **Plan-backed narration** — ``path_label`` in :data:`ALLOWED_NARRATIVE_PATH_LABELS`, CTIR attached,
   stamp-matched narration plan bundle with a dict ``narrative_plan``, and (when a prompt dict is
   supplied) a dict ``prompt_payload["narrative_plan"]``.
2. **Emergency / non-plan** — explicit ``emergency_nonplan_allowed`` plus a label in
   :data:`ALLOWED_EMERGENCY_FALLBACK_LABELS`; failures from the plan-backed chain are suppressed.
3. **Non-narrative / debug** — ``path_label`` in :data:`NON_NARRATIVE_DEBUG_PATH_LABELS` sets
   ``enabled`` false and skips CTIR/plan enforcement codes (still emits observability fields).
4. **Violation** — any registered narrative path missing the chain (or stamp mismatch, or
   ``narration_seam_audit`` / plan build-error mirrors in the prompt payload without emergency)
   yields entries in ``failure_codes``.

Pure helpers only — no runtime side effects, no GPT. Callers pass session slices, optional
``prompt_payload`` (e.g. ``build_narration_context`` output), and optional ``gm_metadata``
(``gm_output["metadata"]``) for forward-compatible inspection.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, get_attached_ctir
from game.narration_plan_bundle import (
    get_attached_narration_plan_bundle,
    get_narration_plan_bundle_stamp,
)

# --- Path label inventories (Block A) ---

ALLOWED_NARRATIVE_PATH_LABELS: frozenset[str] = frozenset(
    {
        "scene_opening",
        "continuation",
        "action_outcome",
        "dialogue_social",
        "transition",
        "exposition_answer",
    }
)

ALLOWED_EMERGENCY_FALLBACK_LABELS: frozenset[str] = frozenset(
    {
        "upstream_api_fast_fallback",
        "manual_play_gpt_budget_exceeded",
        "deterministic_terminal_repair",
        "non_gpt_error_response",
    }
)

# Explicitly registered outputs that skip CTIR/plan convergence (engine/debug harness).
NON_NARRATIVE_DEBUG_PATH_LABELS: frozenset[str] = frozenset(
    {
        "non_narrative_debug",
    }
)

# --- Failure codes ---

MISSING_CTIR_FOR_NARRATIVE_OUTPUT = "missing_ctir_for_narrative_output"
MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN = "missing_narrative_plan_for_ctir_turn"
NARRATIVE_PLAN_STAMP_MISMATCH = "narrative_plan_stamp_mismatch"
PROMPT_PAYLOAD_MISSING_NARRATIVE_PLAN = "prompt_payload_missing_narrative_plan"
PROMPT_PAYLOAD_USES_RAW_SEMANTIC_SHORTCUT = "prompt_payload_uses_raw_semantic_shortcut"
UNREGISTERED_NARRATION_PATH = "unregistered_narration_path"
NONPLAN_OUTPUT_NOT_EMERGENCY_ALLOWED = "nonplan_output_not_emergency_allowed"

FAILURE_CODES: frozenset[str] = frozenset(
    {
        MISSING_CTIR_FOR_NARRATIVE_OUTPUT,
        MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN,
        NARRATIVE_PLAN_STAMP_MISMATCH,
        PROMPT_PAYLOAD_MISSING_NARRATIVE_PLAN,
        PROMPT_PAYLOAD_USES_RAW_SEMANTIC_SHORTCUT,
        UNREGISTERED_NARRATION_PATH,
        NONPLAN_OUTPUT_NOT_EMERGENCY_ALLOWED,
    }
)


def is_allowed_narrative_path_label(path_label: str) -> bool:
    return str(path_label or "").strip() in ALLOWED_NARRATIVE_PATH_LABELS


def is_allowed_emergency_fallback_label(label: str | None) -> bool:
    return str(label or "").strip() in ALLOWED_EMERGENCY_FALLBACK_LABELS


def is_non_narrative_debug_path_label(path_label: str) -> bool:
    return str(path_label or "").strip() in NON_NARRATIVE_DEBUG_PATH_LABELS


def _session_ctir_stamp(session: Mapping[str, Any] | None) -> str:
    if not isinstance(session, Mapping):
        return ""
    return str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip()


def _bundle_narrative_plan(session: Mapping[str, Any] | None) -> dict[str, Any] | None:
    bundle = get_attached_narration_plan_bundle(
        session if isinstance(session, Mapping) else None  # type: ignore[arg-type]
    )
    if not isinstance(bundle, dict):
        return None
    np = bundle.get("narrative_plan")
    return dict(np) if isinstance(np, dict) else None


def _prompt_has_narrative_plan_dict(prompt_payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(prompt_payload, Mapping):
        return False
    np = prompt_payload.get("narrative_plan")
    return isinstance(np, dict) and bool(np)


def _raw_state_prompt_bypass_detected(prompt_payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(prompt_payload, Mapping):
        return False
    if isinstance(prompt_payload.get("narration_seam_audit"), Mapping):
        return True
    pda = prompt_payload.get("prompt_debug_anchor")
    if isinstance(pda, Mapping):
        npa = pda.get("narrative_plan")
        if isinstance(npa, Mapping) and npa.get("build_error"):
            return True
    return False


def _emergency_contract_ok(
    *,
    emergency_nonplan_allowed: bool,
    emergency_fallback_label: str | None,
) -> bool:
    return emergency_nonplan_allowed and is_allowed_emergency_fallback_label(emergency_fallback_label)


def _sorted_unique(codes: list[str]) -> list[str]:
    return sorted({c for c in codes if c in FAILURE_CODES})


def build_planner_convergence_report(
    *,
    path_label: str,
    owner_module: str,
    session: Mapping[str, Any] | None = None,
    prompt_payload: Mapping[str, Any] | None = None,
    gm_metadata: Mapping[str, Any] | None = None,
    emergency_nonplan_allowed: bool = False,
    emergency_fallback_label: str | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable convergence report for one narration-classified path.

    When ``path_label`` is a Block A narrative label, CTIR + stamp-matched narration plan bundle
    are required unless emergency fallback is explicitly allowed with a registered emergency label.

    Unknown labels (neither narrative nor non-narrative debug) yield ``unregistered_narration_path``.
    Debug labels set ``enabled`` false and skip CTIR/plan enforcement failure codes.

    ``gm_metadata`` is accepted for forward-compatible inspection of ``gm["metadata"]``; v1
    convergence signals are read from ``prompt_payload`` only.
    """
    _ = gm_metadata
    pl = str(path_label or "").strip()
    om = str(owner_module or "").strip() or "unknown"
    narrative_registered = pl in ALLOWED_NARRATIVE_PATH_LABELS
    debug_registered = pl in NON_NARRATIVE_DEBUG_PATH_LABELS
    path_known = narrative_registered or debug_registered

    sess = session if isinstance(session, Mapping) else None
    ctir_obj = get_attached_ctir(sess)
    ctir_present = ctir_obj is not None
    ctir_stamp = _session_ctir_stamp(sess)
    bundle_stamp = get_narration_plan_bundle_stamp(sess)
    plan_dict = _bundle_narrative_plan(sess)
    narrative_plan_present = plan_dict is not None
    stamp_matches = bool(ctir_stamp) and bool(bundle_stamp) and ctir_stamp == bundle_stamp

    prompt_consumes_plan = _prompt_has_narrative_plan_dict(
        prompt_payload if isinstance(prompt_payload, Mapping) else None
    )
    raw_bypass = _raw_state_prompt_bypass_detected(
        prompt_payload if isinstance(prompt_payload, Mapping) else None,
    )
    emergency_ok = _emergency_contract_ok(
        emergency_nonplan_allowed=emergency_nonplan_allowed,
        emergency_fallback_label=emergency_fallback_label,
    )
    out_emergency_allowed = emergency_ok
    enabled = not debug_registered

    failure_codes: list[str] = []

    if not path_known:
        failure_codes.append(UNREGISTERED_NARRATION_PATH)

    if not enabled:
        return {
            "enabled": False,
            "owner_module": om,
            "path_label": pl,
            "ctir_present": ctir_present,
            "ctir_stamp": ctir_stamp,
            "narrative_plan_present": narrative_plan_present,
            "narrative_plan_stamp": bundle_stamp,
            "stamp_matches": stamp_matches,
            "prompt_consumes_plan": prompt_consumes_plan,
            "raw_state_prompt_bypass_detected": raw_bypass,
            "emergency_nonplan_allowed": out_emergency_allowed,
            "failure_codes": _sorted_unique(failure_codes),
        }

    if narrative_registered and not emergency_ok:
        if not ctir_present:
            failure_codes.append(MISSING_CTIR_FOR_NARRATIVE_OUTPUT)
        elif not narrative_plan_present:
            failure_codes.append(MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN)
        elif not stamp_matches:
            failure_codes.append(NARRATIVE_PLAN_STAMP_MISMATCH)

        chain_ok = ctir_present and narrative_plan_present and stamp_matches
        if chain_ok and isinstance(prompt_payload, Mapping) and not prompt_consumes_plan:
            failure_codes.append(PROMPT_PAYLOAD_MISSING_NARRATIVE_PLAN)

        if raw_bypass and not emergency_ok:
            failure_codes.append(PROMPT_PAYLOAD_USES_RAW_SEMANTIC_SHORTCUT)

    return {
        "enabled": True,
        "owner_module": om,
        "path_label": pl,
        "ctir_present": ctir_present,
        "ctir_stamp": ctir_stamp,
        "narrative_plan_present": narrative_plan_present,
        "narrative_plan_stamp": bundle_stamp,
        "stamp_matches": stamp_matches,
        "prompt_consumes_plan": prompt_consumes_plan,
        "raw_state_prompt_bypass_detected": raw_bypass,
        "emergency_nonplan_allowed": out_emergency_allowed,
        "failure_codes": _sorted_unique(failure_codes),
    }


def planner_convergence_ok(report: Mapping[str, Any]) -> bool:
    """True when the report has no failure codes (contract satisfied for evaluated path)."""
    fc = report.get("failure_codes")
    if not isinstance(fc, list):
        return False
    return len(fc) == 0
