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
legality verdicts. Transitional overlap in import sites does not make this file the orchestration owner.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping

from game.state_channels import project_debug_payload

# ``accepted_via`` values that can carry ``retry_exhausted`` / terminal flags from legitimate
# deterministic repairs without implying an upstream API / infra failure by themselves.
_LEGITIMATE_RESOLUTION_REPAIR_ACCEPTED_VIA: frozenset[str] = frozenset(
    {"social_resolution_repair", "nonsocial_resolution_repair"}
)

# Keys merged from NA layer debug into ``gm_output['_final_emission_meta']`` (contract-driven, stable names).
# Distinct from ``response_delta_*`` legality keys (gate delta layer) and from offline ``narrative_authenticity_eval``.
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
    internal = gm_output.get("internal_state")
    if isinstance(internal, Mapping):
        lane = internal.get("emission_debug_lane")
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
    nested = lane.get("_final_emission_meta")
    if isinstance(nested, Mapping):
        return dict(nested)
    fem = gm_output.get("_final_emission_meta")
    return dict(fem) if isinstance(fem, Mapping) else {}


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
