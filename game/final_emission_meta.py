"""Debug / meta packaging for final emission (FEM) and related read-side helpers.

**Canonical boundary (post-OC2):** :func:`game.final_emission_gate.apply_final_emission_gate`
remains the **orchestration owner** for layer order and integration. This module is
**Canonical metadata-only owner**: stable dict shapes for FEM / NA fields, slimming, read-side coercion
for deterministic consumers, and dead-turn packaging for
``_final_emission_meta["dead_turn"]``. It does **not** orchestrate gates, prompts, or API
surfaces—only shapes, merges, and **channel-sidecar** helpers used at the emission exit seam.

After the final emission boundary, observability keys (including ``_final_emission_meta``)
live under ``gm_output["internal_state"]["emission_debug_lane"]`` (see
:func:`package_emission_channel_sidecar`). Use :func:`read_final_emission_meta_dict` /
:func:`read_emission_debug_lane` instead of assuming a top-level ``_final_emission_meta`` key.

Validator implementations and emission repair wiring live in :mod:`game.narrative_authenticity`
and :mod:`game.final_emission_repairs` (canonical ``response_delta_*`` legality keys remain
owned by the gate stack’s delta layer); this file only packages **metadata shapes**, not
legality verdicts. Narrative-mode **output** legality is computed in
:mod:`game.narrative_mode_contract` (``validate_narrative_mode_output``); this module may package
``narrative_mode_output_*`` FEM fields the same way as other contract traces. Transitional overlap
in import sites does not make this file the orchestration owner.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping

from game.state_channels import project_debug_payload

# --- Canonical key registries (telemetry-only; not policy owners) ---

# Post-gate contract: debug/meta observability lives under gm_output["internal_state"] lanes.
INTERNAL_STATE_KEY: str = "internal_state"
EMISSION_DEBUG_LANE_KEY: str = "emission_debug_lane"
EMISSION_AUTHOR_LANE_KEY: str = "emission_author_lane"

# Canonical nested dict name for final-emission metadata (FEM). Legacy top-level fallback is supported
# at read time for mixed dicts/fixtures but is not the intended post-gate storage location.
FINAL_EMISSION_META_KEY: str = "_final_emission_meta"
DEBUG_NOTES_KEY: str = "debug_notes"

# FEM subtrees / well-known nested keys.
FEM_DEAD_TURN_KEY: str = "dead_turn"


def ensure_final_emission_meta_dict(gm_output: MutableMapping[str, Any]) -> Dict[str, Any]:
    """Write-time helper: ensure and return the FEM dict on a gate-shaped ``gm_output`` mapping.

    This centralizes the canonical key spelling (``FINAL_EMISSION_META_KEY``) and avoids ad hoc
    get-or-create patterns scattered across gate/repair instrumentation.
    """
    if not isinstance(gm_output, MutableMapping):
        return {}
    meta = gm_output.get(FINAL_EMISSION_META_KEY)
    if not isinstance(meta, dict):
        meta = {}
        gm_output[FINAL_EMISSION_META_KEY] = meta
    return meta


def patch_final_emission_meta(gm_output: MutableMapping[str, Any], patch: Mapping[str, Any] | None) -> None:
    """Write-time helper: shallow-merge *patch* into ``_final_emission_meta`` (in place)."""
    if not isinstance(gm_output, MutableMapping):
        return
    if not isinstance(patch, Mapping) or not patch:
        return
    meta = ensure_final_emission_meta_dict(gm_output)
    meta.update(dict(patch))

# Response-type debug fields (RTD1) that may be merged into FEM for observability.
FEM_RESPONSE_TYPE_KEYS: frozenset[str] = frozenset(
    {
        "response_type_required",
        "response_type_contract_source",
        "response_type_candidate_ok",
        "response_type_repair_used",
        "response_type_repair_kind",
        "response_type_rejection_reasons",
        "non_hostile_escalation_blocked",
    }
)

# Stage-diff is intentionally bounded; it may project a compact NA subset for observability only.
# This is not a second owner of NA semantics; it is an explicitly-allowed projection surface.
STAGE_DIFF_ALLOWED_NA_PROJECTION_KEYS: frozenset[str] = frozenset(
    {
        "narrative_authenticity_reason_codes",
        "narrative_authenticity_skip_reason",
        "narrative_authenticity_status",
        "narrative_authenticity_rumor_relaxed_low_signal",
        # Optional: repair mode is observational and compact; stage-diff does not consume full evidence/metrics.
        "narrative_authenticity_repair_mode",
    }
)

# Evaluator/debug consumers may want a normalized FEM slice without importing every gate module.
# Prefix-based families are explicit registries (telemetry-only) and do not imply policy ownership here.
EVALUATOR_FEM_KEY_PREFIX_FAMILIES: tuple[str, ...] = (
    "answer_completeness_",
    "response_delta_",
    "social_response_structure_",
    "fallback_behavior_",
    "referent_",
    "narrative_authenticity_",
    "narrative_mode_output_",
    "response_type_",
)

# Explicit non-prefix evaluator keys (nested dicts / stable aliases).
EVALUATOR_FEM_EXPLICIT_KEYS: frozenset[str] = frozenset(
    {
        FEM_DEAD_TURN_KEY,
    }
)

# --- Response-type debug/meta shaping (metadata-only; orchestration decides when to attach) ---


def default_response_type_debug(contract: Dict[str, Any] | None, source: str | None) -> Dict[str, Any]:
    """Metadata-only helper for the canonical response-type debug dict (RTD1).

    This shapes *descriptive* fields used by the gate for observability and FEM merge, but does not
    decide whether the response-type contract should run or what repair is applied.
    """
    return {
        "response_type_required": str((contract or {}).get("required_response_type") or "") or None,
        "response_type_contract_source": source,
        "response_type_candidate_ok": None if not contract else True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
        "response_type_upstream_prepared_absent": False,
    }


def merge_response_type_meta(meta: Dict[str, Any], debug: Dict[str, Any]) -> None:
    """Metadata-only merge of response-type debug fields into ``_final_emission_meta``."""
    meta.update(
        {
            "response_type_required": debug.get("response_type_required"),
            "response_type_contract_source": debug.get("response_type_contract_source"),
            "response_type_candidate_ok": debug.get("response_type_candidate_ok"),
            "response_type_repair_used": debug.get("response_type_repair_used"),
            "response_type_repair_kind": debug.get("response_type_repair_kind"),
            "response_type_rejection_reasons": list(debug.get("response_type_rejection_reasons") or []),
            "non_hostile_escalation_blocked": bool(debug.get("non_hostile_escalation_blocked")),
            "response_type_upstream_prepared_absent": bool(debug.get("response_type_upstream_prepared_absent")),
        }
    )


def response_type_decision_payload(debug: Dict[str, Any]) -> Dict[str, Any]:
    """Metadata-only compact view suitable for logs/telemetry sinks (stable keys)."""
    return {
        "response_type_required": debug.get("response_type_required"),
        "response_type_contract_source": debug.get("response_type_contract_source"),
        "response_type_candidate_ok": debug.get("response_type_candidate_ok"),
        "response_type_repair_used": debug.get("response_type_repair_used"),
        "response_type_repair_kind": debug.get("response_type_repair_kind"),
        "response_type_rejection_reasons": list(debug.get("response_type_rejection_reasons") or []),
        "non_hostile_escalation_blocked": bool(debug.get("non_hostile_escalation_blocked")),
        "response_type_upstream_prepared_absent": bool(debug.get("response_type_upstream_prepared_absent")),
    }

# ``accepted_via`` values that can carry ``retry_exhausted`` / terminal flags from legitimate
# deterministic repairs without implying an upstream API / infra failure by themselves.
_LEGITIMATE_RESOLUTION_REPAIR_ACCEPTED_VIA: frozenset[str] = frozenset(
    {"social_resolution_repair", "nonsocial_resolution_repair"}
)

# Keys merged from NA layer debug into ``gm_output['_final_emission_meta']`` (contract-driven, stable names).
# Distinct from ``response_delta_*`` legality keys (gate delta layer) and from offline ``narrative_authenticity_eval``.
NARRATIVE_MODE_OUTPUT_FEM_KEYS: frozenset[str] = frozenset(
    {
        "narrative_mode_output_validator_version",
        "narrative_mode_output_checked",
        "narrative_mode_output_passed",
        "narrative_mode_output_mode",
        "narrative_mode_output_failure_reasons",
        "narrative_mode_output_repairable",
        "narrative_mode_output_observed_signals",
        "narrative_mode_output_skip_reason",
        "narrative_mode_contract_version",
        "narrative_mode_contract_mode",
    }
)


def default_narrative_mode_output_layer_meta() -> Dict[str, Any]:
    """Metadata-only defaults for C4 narrative-mode output validation (FEM merge)."""
    return {
        "narrative_mode_output_validator_version": None,
        "narrative_mode_output_checked": False,
        "narrative_mode_output_passed": True,
        "narrative_mode_output_mode": None,
        "narrative_mode_output_failure_reasons": [],
        "narrative_mode_output_repairable": False,
        "narrative_mode_output_observed_signals": {},
        "narrative_mode_output_skip_reason": None,
        "narrative_mode_contract_version": None,
        "narrative_mode_contract_mode": None,
    }


def merge_narrative_mode_output_into_final_emission_meta(meta: Dict[str, Any], nmo: Mapping[str, Any]) -> None:
    """Shallow-merge narrative-mode output trace fields into ``_final_emission_meta`` (in place)."""
    if not isinstance(meta, dict) or not isinstance(nmo, Mapping) or not nmo:
        return
    for k in NARRATIVE_MODE_OUTPUT_FEM_KEYS:
        if k not in nmo:
            continue
        v = nmo.get(k)
        if k == "narrative_mode_output_failure_reasons" and isinstance(v, (list, tuple)):
            meta[k] = [str(x) for x in v if str(x).strip()]
        elif k == "narrative_mode_output_observed_signals" and isinstance(v, Mapping):
            meta[k] = {str(k2): bool(v2) for k2, v2 in v.items()}
        elif k == "narrative_mode_output_skip_reason" and v is not None:
            meta[k] = str(v).strip() or None
        else:
            meta[k] = v


NARRATIVE_AUTHENTICITY_FEM_KEYS: frozenset[str] = frozenset(
    {
        "narrative_authenticity_checked",
        "narrative_authenticity_failed",
        "narrative_authenticity_failure_reasons",
        "narrative_authenticity_repaired",
        "narrative_authenticity_repair_applied",
        "narrative_authenticity_repair_mode",
        "narrative_authenticity_repair_modes",
        "narrative_authenticity_skip_reason",
        "narrative_authenticity_reason_codes",
        "narrative_authenticity_metrics",
        "narrative_authenticity_evidence",
        "narrative_authenticity_status",
        "narrative_authenticity_trace",
        "narrative_authenticity_relaxation_flags",
        "narrative_authenticity_rumor_relaxed_low_signal",
    }
)


def default_narrative_authenticity_layer_meta() -> Dict[str, Any]:
    """Metadata-only owner for NA layer write-time defaults before merge/package steps."""
    return {
        "narrative_authenticity_checked": False,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_failure_reasons": [],
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_repair_applied": False,
        "narrative_authenticity_repair_mode": None,
        "narrative_authenticity_repair_modes": [],
        "narrative_authenticity_skip_reason": None,
        "narrative_authenticity_reason_codes": [],
        "narrative_authenticity_metrics": None,
        "narrative_authenticity_evidence": None,
        "narrative_authenticity_status": None,
        "narrative_authenticity_trace": None,
        "narrative_authenticity_relaxation_flags": None,
        "narrative_authenticity_rumor_relaxed_low_signal": False,
    }


def package_emission_channel_sidecar(
    *,
    debug_top_level: Mapping[str, Any] | None,
    author_top_level: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize debug/meta sidecar content stored under ``gm_output['internal_state']`` (author channel).

    Values are shallow copies suitable for deterministic inspection; not a second classifier.
    """
    out: dict[str, Any] = {}
    if isinstance(debug_top_level, Mapping) and debug_top_level:
        out["emission_debug_lane"] = dict(debug_top_level)
    if isinstance(author_top_level, Mapping) and author_top_level:
        out["emission_author_lane"] = dict(author_top_level)
    return out


def read_debug_notes_from_turn_payload(payload: Mapping[str, Any] | None) -> str:
    """Return concatenated ``debug_notes`` from an API envelope or a post-gate ``gm_output`` dict.

    Prefers ``gm_output_debug.emission_debug_lane`` when present (HTTP responses), then legacy
    top-level ``gm_output['debug_notes']``, then the emission debug lane on a gate-shaped dict.
    """
    if not isinstance(payload, Mapping):
        return ""
    dpkg = payload.get("gm_output_debug")
    if isinstance(dpkg, Mapping):
        lane = dpkg.get("emission_debug_lane")
        if isinstance(lane, Mapping):
            s = lane.get("debug_notes")
            if isinstance(s, str) and s.strip():
                return s
    gm = payload.get("gm_output")
    if isinstance(gm, Mapping):
        top = gm.get("debug_notes")
        if isinstance(top, str) and top.strip():
            return top
        lane2 = read_emission_debug_lane(gm)
        s2 = lane2.get("debug_notes")
        if isinstance(s2, str) and s2.strip():
            return s2
    if "player_facing_text" in payload:
        lane3 = read_emission_debug_lane(payload)
        s3 = lane3.get("debug_notes")
        if isinstance(s3, str):
            return str(s3)
    return ""


def read_emission_debug_lane(gm_output: Mapping[str, Any] | None) -> dict[str, Any]:
    """Shallow read of debug-classified top-level keys from a post-gate ``gm_output`` (or legacy mixed dict)."""
    if not isinstance(gm_output, Mapping):
        return {}
    internal = gm_output.get(INTERNAL_STATE_KEY)
    if isinstance(internal, Mapping):
        lane = internal.get(EMISSION_DEBUG_LANE_KEY)
        if isinstance(lane, Mapping):
            return dict(lane)
    return project_debug_payload(gm_output)


def read_final_emission_meta_dict(gm_output: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read FEM dict from post-gate sidecar, else legacy top-level ``_final_emission_meta``.

    Precedence is **sidecar first** to align with the post-finalization contract. Legacy top-level
    FEM is accepted as a compatibility fallback for older/mixed dicts and unit fixtures.
    """
    if not isinstance(gm_output, Mapping):
        return {}
    lane = read_emission_debug_lane(gm_output)
    nested = lane.get(FINAL_EMISSION_META_KEY)
    if isinstance(nested, Mapping):
        return dict(nested)
    fem = gm_output.get(FINAL_EMISSION_META_KEY)
    return dict(fem) if isinstance(fem, Mapping) else {}


def read_emission_debug_lane_from_turn_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read emission debug lane from an API envelope or a gate-shaped ``gm_output`` mapping.

    Ownership boundary:
    - **Write-time packaging** of sidecars is owned by :func:`game.final_emission_gate.apply_final_emission_gate`
      (via :func:`package_emission_channel_sidecar`).
    - **Read-time normalization** is owned here.
    - This function is observational-only and must not drive legality/routing.
    """
    if not isinstance(payload, Mapping):
        return {}
    dbg = payload.get("gm_output_debug")
    if isinstance(dbg, Mapping):
        lane = dbg.get(EMISSION_DEBUG_LANE_KEY)
        if isinstance(lane, Mapping):
            return dict(lane)
    gm = payload.get("gm_output")
    if not isinstance(gm, Mapping):
        gm = payload
    return read_emission_debug_lane(gm if isinstance(gm, Mapping) else None)


def read_final_emission_meta_from_turn_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read FEM dict from an API envelope or from a gate-shaped ``gm_output`` mapping.

    This is a pure, read-side helper that preserves the legacy top-level
    ``_final_emission_meta`` fallback already supported by :func:`read_final_emission_meta_dict`.
    """
    if not isinstance(payload, Mapping):
        return {}
    dbg_lane = read_emission_debug_lane_from_turn_payload(payload)
    nested = dbg_lane.get(FINAL_EMISSION_META_KEY)
    if isinstance(nested, Mapping):
        return dict(nested)
    gm = payload.get("gm_output")
    if not isinstance(gm, Mapping):
        gm = payload
    return read_final_emission_meta_dict(gm if isinstance(gm, Mapping) else None)


def merge_narrative_authenticity_into_final_emission_meta(meta: Dict[str, Any], na_dbg: Dict[str, Any]) -> None:
    """Metadata-only packager for NA fields into ``_final_emission_meta`` (in place)."""
    meta.update(
        {
            "narrative_authenticity_checked": bool(na_dbg.get("narrative_authenticity_checked")),
            "narrative_authenticity_failed": bool(na_dbg.get("narrative_authenticity_failed")),
            "narrative_authenticity_failure_reasons": list(na_dbg.get("narrative_authenticity_failure_reasons") or []),
            "narrative_authenticity_repaired": bool(na_dbg.get("narrative_authenticity_repaired")),
            "narrative_authenticity_repair_applied": bool(na_dbg.get("narrative_authenticity_repair_applied")),
            "narrative_authenticity_repair_mode": na_dbg.get("narrative_authenticity_repair_mode"),
            "narrative_authenticity_repair_modes": list(na_dbg.get("narrative_authenticity_repair_modes") or []),
            "narrative_authenticity_skip_reason": na_dbg.get("narrative_authenticity_skip_reason"),
            "narrative_authenticity_reason_codes": list(na_dbg.get("narrative_authenticity_reason_codes") or []),
            "narrative_authenticity_metrics": na_dbg.get("narrative_authenticity_metrics"),
            "narrative_authenticity_evidence": na_dbg.get("narrative_authenticity_evidence"),
            "narrative_authenticity_status": na_dbg.get("narrative_authenticity_status"),
            "narrative_authenticity_trace": na_dbg.get("narrative_authenticity_trace"),
            "narrative_authenticity_relaxation_flags": na_dbg.get("narrative_authenticity_relaxation_flags"),
            "narrative_authenticity_rumor_relaxed_low_signal": bool(
                na_dbg.get("narrative_authenticity_rumor_relaxed_low_signal")
            ),
        }
    )


def slim_na_metrics(metrics: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(metrics, Mapping):
        return {}
    out: Dict[str, Any] = {}
    for k, v in metrics.items():
        if v is None:
            continue
        if isinstance(v, float):
            out[str(k)] = round(v, 4)
        elif isinstance(v, (int, str, bool)):
            out[str(k)] = v
    return out


def slim_na_evidence(evidence: Mapping[str, Any] | None, *, max_str: int = 120, max_list: int = 6) -> Dict[str, Any]:
    if not isinstance(evidence, Mapping):
        return {}

    def clip(x: Any) -> Any:
        if isinstance(x, str) and len(x) > max_str:
            return x[: max(0, max_str - 1)] + "…"
        if isinstance(x, list):
            return [clip(i) for i in x[:max_list]]
        if isinstance(x, dict):
            return {str(k2): clip(v2) for k2, v2 in list(x.items())[:8]}
        return x

    return {str(k): clip(v) for k, v in evidence.items()}


def resolve_narrative_authenticity_emission_status(
    validation: Mapping[str, Any],
    *,
    repaired: bool,
    repair_failed: bool,
) -> str | None:
    """Terminal status for gate/meta (``pass`` / ``relaxed`` / ``repaired`` / ``fail``); None if unchecked or non-terminal."""
    checked = bool(validation.get("checked"))
    if not checked:
        return None
    if repaired:
        return "repaired"
    if repair_failed:
        return "fail"
    if bool(validation.get("passed")):
        return "relaxed" if bool(validation.get("rumor_realism_relaxed_low_signal")) else "pass"
    # Checked failure before a repair outcome is applied — omit status until the layer finishes.
    return None


def build_narrative_authenticity_trace_slice(
    validation: Mapping[str, Any] | None,
    *,
    contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Nested compact rumor / classifier context (contract trace + validation relaxation signals)."""
    trace_out: Dict[str, Any] = {}
    rumor_turn = False
    if isinstance(contract, Mapping):
        tr = contract.get("trace") if isinstance(contract.get("trace"), Mapping) else {}
        rumor_turn = bool(tr.get("rumor_turn_active"))
        if rumor_turn:
            trace_out["rumor_turn_active"] = True
            rrc = tr.get("rumor_turn_reason_codes")
            if isinstance(rrc, list) and rrc:
                trace_out["rumor_turn_reason_codes"] = [str(x) for x in rrc[:10] if str(x).strip()]
            rts = tr.get("rumor_trigger_spans")
            if isinstance(rts, list) and rts:
                trace_out["rumor_trigger_spans"] = rts[:6]
    if isinstance(validation, Mapping):
        if validation.get("rumor_realism_relaxed_low_signal"):
            trace_out["rumor_realism_relaxed_low_signal"] = True
        vflags = validation.get("rumor_realism_relaxation_flags")
        if isinstance(vflags, Mapping) and any(vflags.values()):
            trace_out["rumor_relaxation_flags"] = {str(k): bool(v) for k, v in vflags.items() if v}
    return trace_out


def build_narrative_authenticity_emission_trace(
    validation: Mapping[str, Any] | None,
    *,
    contract: Mapping[str, Any] | None = None,
    repaired: bool = False,
    repair_mode: str | None = None,
    repair_failed: bool = False,
) -> Dict[str, Any]:
    """Single **canonical write-time** NA telemetry bundle for ``_final_emission_meta`` (and layer debug dict).

    Shapes: contract trace slice, validation summary hooks (skip / reasons), slim metrics/evidence,
    terminal ``narrative_authenticity_status`` when defined, relaxation flags, repair mode list.
    """
    if not isinstance(validation, Mapping):
        return {}
    out: Dict[str, Any] = {}
    sr = validation.get("skip_reason")
    if isinstance(sr, str) and sr.strip():
        out["narrative_authenticity_skip_reason"] = sr.strip()
    checked = bool(validation.get("checked"))
    passed = bool(validation.get("passed"))
    reasons = [str(x) for x in (validation.get("failure_reasons") or []) if str(x).strip()]
    if reasons:
        out["narrative_authenticity_reason_codes"] = reasons
    metrics_obj = validation.get("metrics")
    rumor_turn = bool((metrics_obj or {}).get("rumor_turn_active")) if isinstance(metrics_obj, Mapping) else False
    if checked and (reasons or not passed or rumor_turn):
        out["narrative_authenticity_metrics"] = slim_na_metrics(validation.get("metrics"))
        out["narrative_authenticity_evidence"] = slim_na_evidence(validation.get("evidence"))
    status = resolve_narrative_authenticity_emission_status(
        validation, repaired=repaired, repair_failed=repair_failed
    )
    if status is not None:
        out["narrative_authenticity_status"] = status
    rf = validation.get("rumor_realism_relaxation_flags") if isinstance(validation, Mapping) else None
    if isinstance(rf, Mapping) and any(rf.values()):
        out["narrative_authenticity_relaxation_flags"] = {str(k): bool(v) for k, v in rf.items() if v}
    if bool(validation.get("rumor_realism_relaxed_low_signal")):
        out["narrative_authenticity_rumor_relaxed_low_signal"] = True
    slice_trace = build_narrative_authenticity_trace_slice(validation, contract=contract)
    if slice_trace:
        out["narrative_authenticity_trace"] = slice_trace
    if repair_mode:
        out["narrative_authenticity_repair_mode"] = repair_mode
        out["narrative_authenticity_repair_modes"] = [repair_mode]
    else:
        out["narrative_authenticity_repair_modes"] = []
    return out


def _tag_set(gm_output: Mapping[str, Any]) -> frozenset[str]:
    raw = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
    return frozenset(str(t).strip() for t in raw if isinstance(t, str) and str(t).strip())


def _upstream_api_error(md: Mapping[str, Any]) -> Dict[str, Any] | None:
    err = md.get("upstream_api_error")
    return dict(err) if isinstance(err, dict) and err else None


def _infra_error_tags(tags: frozenset[str]) -> bool:
    if "gpt_api_error_nonretryable" in tags:
        return True
    return any(t.startswith("upstream_api_failure:") for t in tags)


def _fast_fallback_lane(*, md: Mapping[str, Any], tags: frozenset[str]) -> bool:
    if str(md.get("latency_mode") or "").strip() == "fast_fallback":
        return True
    if "upstream_api_fast_fallback" in tags:
        return True
    if "fast_fallback" in tags:
        return True
    return False


def _forced_retry_terminal_route(gm_output: Mapping[str, Any]) -> bool:
    return str(gm_output.get("accepted_via") or "").strip() == "forced_fallback" and str(
        gm_output.get("final_route") or ""
    ).strip() == "forced_retry_fallback"


def _strong_infra_dead_signals(
    *,
    has_upstream: bool,
    fast_fallback_lane: bool,
    forced_terminal: bool,
    tags: frozenset[str],
) -> bool:
    """Explicit infra / API failure bundle (not merely ``retry_exhausted`` on a repair path)."""
    if has_upstream and (fast_fallback_lane or _infra_error_tags(tags) or forced_terminal):
        return True
    return False


def classify_dead_turn(gm_output: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Deterministic classifier: turns that did not run through the intended model path.

    Policy is intentionally narrow: generic ``forced_retry_fallback`` text or tags alone
    never mark a dead turn without explicit upstream / fast-fallback / forced-terminal
    metadata defined in this function.
    """
    base = {
        "is_dead_turn": False,
        "dead_turn_reason_codes": [],
        "dead_turn_class": "none",
        "validation_playable": True,
        "manual_test_valid": True,
    }
    if not isinstance(gm_output, Mapping):
        return dict(base)

    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    tags = _tag_set(gm_output)
    upstream = _upstream_api_error(md)
    has_upstream = upstream is not None
    fast_fb = _fast_fallback_lane(md=md, tags=tags)
    forced_terminal = _forced_retry_terminal_route(gm_output)
    retry_bundle = gm_output.get("retry_exhausted") is True and gm_output.get("targeted_retry_terminal") is True
    malformed = md.get("malformed_emergency_output") is True

    reason_codes: list[str] = []
    if malformed:
        reason_codes.append("malformed_emergency_output")
    if has_upstream:
        reason_codes.append("upstream_api_error")
        fc = str((upstream or {}).get("failure_class") or "").strip()
        if fc:
            reason_codes.append(f"upstream_failure_class:{fc}")
    if fast_fb:
        reason_codes.append("fast_fallback_lane")
    if forced_terminal:
        reason_codes.append("forced_retry_terminal_route")
    if retry_bundle:
        reason_codes.append("retry_exhausted_targeted_retry_terminal")
    if _infra_error_tags(tags):
        reason_codes.append("infra_error_tags")

    if malformed:
        out = dict(base)
        out["is_dead_turn"] = True
        out["dead_turn_reason_codes"] = reason_codes
        out["dead_turn_class"] = "malformed_emergency_output"
        out["validation_playable"] = False
        out["manual_test_valid"] = False
        return out

    accepted = str(gm_output.get("accepted_via") or "").strip()
    if accepted in _LEGITIMATE_RESOLUTION_REPAIR_ACCEPTED_VIA:
        if not _strong_infra_dead_signals(
            has_upstream=has_upstream,
            fast_fallback_lane=fast_fb,
            forced_terminal=forced_terminal,
            tags=tags,
        ):
            return dict(base)

    is_dead = bool(
        has_upstream
        and (
            fast_fb
            or _infra_error_tags(tags)
            or (forced_terminal and retry_bundle)
        )
    )

    if not is_dead:
        return dict(base)

    dead_class = "upstream_api_failure"
    if forced_terminal and retry_bundle and (fast_fb or "retry_escape_hatch" in tags):
        dead_class = "retry_terminal_fallback"
    elif has_upstream and forced_terminal and not (retry_bundle and (fast_fb or "retry_escape_hatch" in tags)):
        dead_class = "forced_fallback_nonplayable"

    out = dict(base)
    out["is_dead_turn"] = True
    out["dead_turn_reason_codes"] = reason_codes
    out["dead_turn_class"] = dead_class
    out["validation_playable"] = False
    out["manual_test_valid"] = False
    return out


def package_dead_turn_snapshot_into_final_emission_meta(gm_output: MutableMapping[str, Any]) -> None:
    """Metadata-only dead-turn packager used by the gate at finalize time."""
    if not isinstance(gm_output, MutableMapping):
        return
    status = classify_dead_turn(gm_output)
    meta = gm_output.get("_final_emission_meta")
    if not isinstance(meta, dict):
        meta = {}
        gm_output["_final_emission_meta"] = meta
    meta["dead_turn"] = status


def merge_dead_turn_classification_into_final_emission_meta(gm_output: MutableMapping[str, Any]) -> None:
    """Compatibility residue alias for older call sites; canonical owner stays in this module."""
    package_dead_turn_snapshot_into_final_emission_meta(gm_output)


_DEAD_TURN_READ_DEFAULTS: Dict[str, Any] = {
    "is_dead_turn": False,
    "dead_turn_reason_codes": [],
    "dead_turn_class": "none",
    "validation_playable": True,
    "manual_test_valid": True,
}


def read_dead_turn_from_gm_output(gm_output: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Read-only view of DTD1 status from FEM ``dead_turn`` (sidecar or legacy top-level).

    Does **not** classify or merge; missing keys yield stable defaults (validation_playable=True).
    """
    out = dict(_DEAD_TURN_READ_DEFAULTS)
    if not isinstance(gm_output, Mapping):
        return out
    fem = read_final_emission_meta_dict(gm_output)
    if not fem:
        return out
    snap = fem.get("dead_turn")
    if not isinstance(snap, Mapping):
        return out
    if "is_dead_turn" in snap:
        out["is_dead_turn"] = bool(snap.get("is_dead_turn"))
    rc = snap.get("dead_turn_reason_codes")
    if isinstance(rc, list):
        out["dead_turn_reason_codes"] = [str(x) for x in rc if str(x).strip()]
    dc = snap.get("dead_turn_class")
    if isinstance(dc, str) and dc.strip():
        out["dead_turn_class"] = dc.strip()
    if "validation_playable" in snap:
        out["validation_playable"] = bool(snap.get("validation_playable"))
    if "manual_test_valid" in snap:
        out["manual_test_valid"] = bool(snap.get("manual_test_valid"))
    return out


def summarize_gameplay_validation_for_turn(dt: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Aggregate evaluation policy fields from a DTD1 ``dead_turn`` snapshot (already read from FEM)."""
    row = dict(dt or _DEAD_TURN_READ_DEFAULTS)
    validation_playable = bool(row.get("validation_playable", True))
    is_dead = bool(row.get("is_dead_turn"))
    excluded = not validation_playable
    dead_turn_count = 1 if is_dead else 0
    infra_failure_count = 1 if is_dead else 0
    invalidation_reason: str | None = None
    if excluded:
        if is_dead:
            cls = str(row.get("dead_turn_class") or "unknown").strip() or "unknown"
            invalidation_reason = f"excluded_from_score:dead_turn:{cls}"
        else:
            invalidation_reason = "excluded_from_score:non_playable_turn"
    return {
        "run_valid": not excluded,
        "excluded_from_scoring": excluded,
        "invalidation_reason": invalidation_reason,
        "dead_turn_count": dead_turn_count,
        "infra_failure_count": infra_failure_count,
        "dead_turn": dict(row),
    }


def normalize_merged_na_telemetry_for_eval(merged: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read-side: shallow copy with stable empty mappings for nested NA telemetry (no policy inference).

    Proof-layer consumers treat absent vs ``None`` nested dicts consistently without duplicating guards.
    """
    out = dict(merged or {})
    for k in (
        "narrative_authenticity_metrics",
        "narrative_authenticity_trace",
        "narrative_authenticity_evidence",
        "narrative_authenticity_relaxation_flags",
    ):
        v = out.get(k)
        if v is None or not isinstance(v, Mapping):
            out[str(k)] = {}
        else:
            out[str(k)] = dict(v)
    return out


def stage_diff_narrative_authenticity_projection(fem: Mapping[str, Any] | None) -> dict[str, Any]:
    """Curated NA projection allowed for bounded stage-diff observability.

    This returns a compact dict with a small, explicit key whitelist. It never returns raw,
    arbitrary pass-through JSON from FEM, and it does not infer legality.
    """
    if not isinstance(fem, Mapping):
        return {}
    out: dict[str, Any] = {}
    for k in STAGE_DIFF_ALLOWED_NA_PROJECTION_KEYS:
        v = fem.get(k)
        if v is None:
            continue
        if k in {"narrative_authenticity_reason_codes", "narrative_authenticity_failure_reasons"}:
            if isinstance(v, list) and v:
                out[k] = [str(x) for x in v if str(x).strip()]
        elif isinstance(v, (str, bool, int, float)) or v is None:
            out[k] = v
        else:
            # Explicitly avoid widening the surface with nested dicts/lists.
            continue
    trace = fem.get("narrative_authenticity_trace")
    if isinstance(trace, Mapping) and "rumor_turn_active" in trace:
        out["rumor_turn_active"] = bool(trace.get("rumor_turn_active"))
    return out


def normalize_final_emission_meta_for_observability(fem: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read-side normalizer for FEM telemetry (observational-only; no policy inference).

    - Pure function.
    - Fills missing nested dict/list fields deterministically for evaluator/debug consumers.
    - Does not broaden payloads with arbitrary pass-through keys; it only coerces known nested subtrees.
    """
    base = dict(fem or {}) if isinstance(fem, Mapping) else {}

    # Dead-turn subtree: fill stable defaults if absent or malformed.
    snap = base.get(FEM_DEAD_TURN_KEY)
    if not isinstance(snap, Mapping):
        base[FEM_DEAD_TURN_KEY] = dict(_DEAD_TURN_READ_DEFAULTS)
    else:
        merged = dict(_DEAD_TURN_READ_DEFAULTS)
        merged.update(dict(snap))
        base[FEM_DEAD_TURN_KEY] = merged

    # NA nested dicts: stable empty mappings (no policy inference).
    base = normalize_merged_na_telemetry_for_eval(base)

    # Ensure common NA lists are stable lists when present-but-nullish.
    for lk in ("narrative_authenticity_reason_codes", "narrative_authenticity_failure_reasons"):
        v = base.get(lk)
        if v is None:
            continue
        if not isinstance(v, list):
            base[lk] = []
        else:
            base[lk] = [str(x) for x in v if str(x).strip()]
    return base


def normalized_observational_telemetry_bundle(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Produce a normalized, observational-only telemetry bundle for evaluator/debug consumers.

    Ownership boundaries:
    - **Write-time packaging** (what gets written into gm_output/internal_state) is owned by the gate.
    - **Read-time normalization** (stable empty subtrees + curated projections) is owned here.
    - This is explicitly **not** a policy/legality surface and must not be used to drive orchestration.
    """
    fem_raw = read_final_emission_meta_from_turn_payload(payload)
    fem = normalize_final_emission_meta_for_observability(fem_raw)
    lane = read_emission_debug_lane_from_turn_payload(payload)
    return {
        "final_emission_meta": fem,
        "dead_turn": dict(fem.get(FEM_DEAD_TURN_KEY) or _DEAD_TURN_READ_DEFAULTS),
        "debug_notes": read_debug_notes_from_turn_payload(payload),
        "stage_diff_na_projection": stage_diff_narrative_authenticity_projection(fem),
        # Keep the lane available for debugging, but never pass through arbitrary nested keys as canonical state.
        "emission_debug_lane_keys": sorted(str(k) for k in lane.keys()),
    }
