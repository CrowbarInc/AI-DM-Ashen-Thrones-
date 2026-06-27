"""Read-side FEM observability packaging and normalization.

Owns read-side accessors, dead-turn classification reads, normalized FEM views,
observability event projection, and unified telemetry bundles. Does **not** own
write-side FEM stamping, merges, or gate orchestration — those remain in
:mod:`game.final_emission_meta`.
"""
from __future__ import annotations

import importlib
from typing import Any, Dict, Mapping

from game.final_emission_replay_projection import build_fem_runtime_lineage_events
from game.state_channels import project_debug_payload
from game.telemetry_vocab import (
    TELEMETRY_ACTION_OBSERVED,
    TELEMETRY_ACTION_REPAIRED,
    TELEMETRY_ACTION_SKIPPED,
    TELEMETRY_ACTION_UNKNOWN,
    TELEMETRY_PHASE_GATE,
    TELEMETRY_SCOPE_TURN,
    build_telemetry_event,
    normalize_reason_list,
)

# Canonical FEM read keys (same spellings as :mod:`game.final_emission_meta`).
INTERNAL_STATE_KEY: str = "internal_state"
EMISSION_DEBUG_LANE_KEY: str = "emission_debug_lane"
FINAL_EMISSION_META_KEY: str = "_final_emission_meta"
DEBUG_NOTES_KEY: str = "debug_notes"
FEM_DEAD_TURN_KEY: str = "dead_turn"

FEM_RESPONSE_TYPE_KEYS: frozenset[str] = frozenset(
    {
        "response_type_required",
        "response_type_contract_source",
        "response_type_candidate_ok",
        "response_type_repair_used",
        "response_type_repair_kind",
        "response_type_rejection_reasons",
        "non_hostile_escalation_blocked",
        "response_type_upstream_prepared_absent",
        "upstream_prepared_emission_used",
        "upstream_prepared_emission_valid",
        "upstream_prepared_emission_source",
        "upstream_prepared_emission_reject_reason",
        "final_emission_boundary_repair_used",
        "final_emission_boundary_semantic_repair_disabled",
        "opening_validation_failed",
        "opening_failure_reasons",
        "opening_recovered_via_fallback",
        "opening_fallback_authorship_source",
        "sealed_fallback_owner_bucket",
        "fallback_family_used",
        "fallback_temporal_frame",
        "realization_fallback_family",
    }
)

STAGE_DIFF_ALLOWED_NA_PROJECTION_KEYS: frozenset[str] = frozenset(
    {
        "narrative_authenticity_reason_codes",
        "narrative_authenticity_skip_reason",
        "narrative_authenticity_status",
        "narrative_authenticity_rumor_relaxed_low_signal",
        "narrative_authenticity_repair_mode",
    }
)

_LEGITIMATE_RESOLUTION_REPAIR_ACCEPTED_VIA: frozenset[str] = frozenset(
    {"social_resolution_repair", "nonsocial_resolution_repair"}
)

_DEAD_TURN_READ_DEFAULTS: Dict[str, Any] = {
    "is_dead_turn": False,
    "dead_turn_reason_codes": [],
    "dead_turn_class": "none",
    "validation_playable": True,
    "manual_test_valid": True,
}

_FEM_OBS_NA_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "narrative_authenticity_checked",
        "narrative_authenticity_failed",
        "narrative_authenticity_repaired",
        "narrative_authenticity_repair_applied",
        "narrative_authenticity_skip_reason",
        "narrative_authenticity_status",
        "narrative_authenticity_reason_codes",
        "narrative_authenticity_failure_reasons",
        "narrative_authenticity_rumor_relaxed_low_signal",
    }
)

_FEM_OBS_AC_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "answer_completeness_checked",
        "answer_completeness_failed",
        "answer_completeness_repaired",
        "answer_completeness_skip_reason",
        "answer_completeness_failure_reasons",
    }
)

_FEM_OBS_RD_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "response_delta_checked",
        "response_delta_failed",
        "response_delta_repaired",
        "response_delta_skip_reason",
        "response_delta_failure_reasons",
    }
)

_FEM_OBS_FB_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "fallback_behavior_contract_present",
        "fallback_behavior_checked",
        "fallback_behavior_failed",
        "fallback_behavior_repaired",
        "fallback_behavior_skip_reason",
        "fallback_behavior_failure_reasons",
        "fallback_behavior_uncertainty_active",
    }
)


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
    """Read **raw** FEM dict from post-gate sidecar, else legacy top-level ``_final_emission_meta``.

    Returns a shallow copy of whatever the pipeline wrote (stable key names, but no
    coercion of nested subtrees). For **normalized** FEM intended for evaluator-style
    consumers, use :func:`normalize_final_emission_meta_for_observability` on the result.

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
    """Read **raw** FEM from an API envelope or gate-shaped ``gm_output`` (pure read-side).

    Same precedence and legacy fallback as :func:`read_final_emission_meta_dict`; does not
    normalize nested NA or dead-turn defaults — that is a separate observational step.
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

    Input is typically a **raw** merged NA dict (FEM keys + optional harness overrides); output
    keeps the same keys but replaces ``None`` / non-mapping nested payloads with ``{}`` for
    metrics/trace/evidence/relaxation flags. Proof-layer consumers treat absent vs ``None`` nested
    dicts consistently without duplicating guards.
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

    **Reason-list alias collapse (read-side):** FEM may carry both
    ``narrative_authenticity_reason_codes`` and ``narrative_authenticity_failure_reasons``.
    They are the same semantic family as gate ``failure_reasons`` vs packaged ``reason_codes``;
    this projection merges them into a **single** deduped ``narrative_authenticity_reason_codes``
    list so stage snapshots do not double-track codes. Raw FEM keys on disk are unchanged —
    only this bounded read surface collapses duplicates.
    """
    if not isinstance(fem, Mapping):
        return {}
    out: dict[str, Any] = {}
    merged_codes: list[str] = []
    merged_codes.extend(normalize_reason_list(fem.get("narrative_authenticity_reason_codes")))
    merged_codes.extend(normalize_reason_list(fem.get("narrative_authenticity_failure_reasons")))
    merged_codes = list(dict.fromkeys(merged_codes))[:16]

    for k in sorted(STAGE_DIFF_ALLOWED_NA_PROJECTION_KEYS):
        if k == "narrative_authenticity_reason_codes":
            if merged_codes:
                out[k] = [str(x) for x in merged_codes if str(x).strip()]
            continue
        v = fem.get(k)
        if v is None:
            continue
        if isinstance(v, bool):
            out[k] = v
        elif isinstance(v, str):
            out[k] = v
        elif isinstance(v, (int, float)):
            out[k] = v
        else:
            continue
    trace = fem.get("narrative_authenticity_trace")
    if isinstance(trace, Mapping) and "rumor_turn_active" in trace:
        out["rumor_turn_active"] = bool(trace.get("rumor_turn_active"))
    return out


def normalize_final_emission_meta_for_observability(fem: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read-side **normalized** FEM view for observability (observational-only; no policy inference).

    **Raw vs normalized:** :func:`read_final_emission_meta_dict` returns pipeline-shaped FEM;
    this function returns a shallow-normalized copy with stable defaults for nested NA and
    dead-turn subtrees so offline tools need fewer null guards.

    - Pure function.
    - Fills missing nested dict/list fields deterministically for evaluator/debug consumers.
    - Does not broaden payloads with arbitrary pass-through keys; it only coerces known nested subtrees.
    """
    base = dict(fem or {}) if isinstance(fem, Mapping) else {}

    snap = base.get(FEM_DEAD_TURN_KEY)
    if not isinstance(snap, Mapping):
        base[FEM_DEAD_TURN_KEY] = dict(_DEAD_TURN_READ_DEFAULTS)
    else:
        merged = dict(_DEAD_TURN_READ_DEFAULTS)
        merged.update(dict(snap))
        base[FEM_DEAD_TURN_KEY] = merged

    base = normalize_merged_na_telemetry_for_eval(base)

    for lk in ("narrative_authenticity_reason_codes", "narrative_authenticity_failure_reasons"):
        v = base.get(lk)
        if v is None:
            continue
        if not isinstance(v, list):
            base[lk] = []
        else:
            base[lk] = [str(x) for x in v if str(x).strip()]
    return base


def _fem_clip_str(value: Any, *, limit: int = 120) -> str | None:
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)] + "…"


def _fem_na_action(fem: Mapping[str, Any]) -> str:
    skip = fem.get("narrative_authenticity_skip_reason")
    if isinstance(skip, str) and skip.strip() and not bool(fem.get("narrative_authenticity_checked")):
        return TELEMETRY_ACTION_SKIPPED
    if bool(fem.get("narrative_authenticity_repaired")) or bool(fem.get("narrative_authenticity_repair_applied")):
        return TELEMETRY_ACTION_REPAIRED
    if bool(fem.get("narrative_authenticity_checked")):
        return TELEMETRY_ACTION_OBSERVED
    return TELEMETRY_ACTION_UNKNOWN


def _fem_layer_action(
    fem: Mapping[str, Any],
    *,
    checked_key: str,
    skip_key: str,
    repaired_key: str,
) -> str:
    skip = fem.get(skip_key)
    if isinstance(skip, str) and skip.strip() and not bool(fem.get(checked_key)):
        return TELEMETRY_ACTION_SKIPPED
    if bool(fem.get(repaired_key)):
        return TELEMETRY_ACTION_REPAIRED
    if bool(fem.get(checked_key)):
        return TELEMETRY_ACTION_OBSERVED
    return TELEMETRY_ACTION_UNKNOWN


def _fem_response_type_action(fem: Mapping[str, Any]) -> str:
    if bool(fem.get("response_type_repair_used")):
        return TELEMETRY_ACTION_REPAIRED
    if fem.get("response_type_candidate_ok") is False:
        return TELEMETRY_ACTION_SKIPPED
    if fem.get("response_type_required") is not None and str(fem.get("response_type_required") or "").strip():
        return TELEMETRY_ACTION_OBSERVED
    return TELEMETRY_ACTION_UNKNOWN


def build_fem_observability_events(fem: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Project FEM into a bounded list of canonical observational events (:mod:`game.telemetry_vocab`).

    ``phase`` is ``gate`` because FEM carries post-gate validator/repair traces, not because this
    function gates anything. Read-side only: no legality interpretation, no stage-diff/evaluator
    semantic ownership, no arbitrary FEM pass-through in ``data``. NA ``reasons`` merge
    ``narrative_authenticity_failure_reasons`` with ``narrative_authenticity_reason_codes``.
    """
    if not isinstance(fem, Mapping):
        return []

    events: list[dict[str, Any]] = []

    if any(k in fem for k in _FEM_OBS_NA_SIGNAL_KEYS):
        na_reasons = normalize_reason_list(fem.get("narrative_authenticity_failure_reasons")) + normalize_reason_list(
            fem.get("narrative_authenticity_reason_codes")
        )
        na_reasons = list(dict.fromkeys(na_reasons))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="narrative_authenticity",
                action=_fem_na_action(fem),
                reasons=na_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "checked": bool(fem.get("narrative_authenticity_checked")),
                    "failed": bool(fem.get("narrative_authenticity_failed")),
                    "repaired": bool(fem.get("narrative_authenticity_repaired"))
                    or bool(fem.get("narrative_authenticity_repair_applied")),
                    "status": _fem_clip_str(fem.get("narrative_authenticity_status"), limit=24),
                    "skip_reason": _fem_clip_str(fem.get("narrative_authenticity_skip_reason")),
                    "rumor_relaxed_low_signal": bool(fem.get("narrative_authenticity_rumor_relaxed_low_signal")),
                },
            )
        )

    if any(k in fem for k in _FEM_OBS_AC_SIGNAL_KEYS):
        ac_reasons = normalize_reason_list(fem.get("answer_completeness_failure_reasons"))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="answer_completeness",
                action=_fem_layer_action(
                    fem,
                    checked_key="answer_completeness_checked",
                    skip_key="answer_completeness_skip_reason",
                    repaired_key="answer_completeness_repaired",
                ),
                reasons=ac_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "checked": bool(fem.get("answer_completeness_checked")),
                    "failed": bool(fem.get("answer_completeness_failed")),
                    "repaired": bool(fem.get("answer_completeness_repaired")),
                    "repair_mode": _fem_clip_str(fem.get("answer_completeness_repair_mode")),
                    "skip_reason": _fem_clip_str(fem.get("answer_completeness_skip_reason")),
                    "expected_voice": _fem_clip_str(fem.get("answer_completeness_expected_voice")),
                },
            )
        )

    if any(k in fem for k in _FEM_OBS_RD_SIGNAL_KEYS):
        rd_reasons = normalize_reason_list(fem.get("response_delta_failure_reasons"))[:16]
        echo_ratio_raw = fem.get("response_delta_echo_overlap_ratio")
        echo_out: float | None
        if isinstance(echo_ratio_raw, bool) or echo_ratio_raw is None:
            echo_out = None
        elif isinstance(echo_ratio_raw, (int, float)):
            echo_out = float(echo_ratio_raw)
        else:
            echo_out = None
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="response_delta",
                action=_fem_layer_action(
                    fem,
                    checked_key="response_delta_checked",
                    skip_key="response_delta_skip_reason",
                    repaired_key="response_delta_repaired",
                ),
                reasons=rd_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "checked": bool(fem.get("response_delta_checked")),
                    "failed": bool(fem.get("response_delta_failed")),
                    "repaired": bool(fem.get("response_delta_repaired")),
                    "kind_detected": _fem_clip_str(fem.get("response_delta_kind_detected"), limit=48),
                    "echo_overlap_ratio": echo_out,
                    "skip_reason": _fem_clip_str(fem.get("response_delta_skip_reason")),
                    "trigger_source": _fem_clip_str(fem.get("response_delta_trigger_source")),
                },
            )
        )

    if any(k in fem for k in _FEM_OBS_FB_SIGNAL_KEYS):
        fb_reasons = normalize_reason_list(fem.get("fallback_behavior_failure_reasons"))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="fallback_behavior",
                action=_fem_layer_action(
                    fem,
                    checked_key="fallback_behavior_checked",
                    skip_key="fallback_behavior_skip_reason",
                    repaired_key="fallback_behavior_repaired",
                ),
                reasons=fb_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "contract_present": bool(fem.get("fallback_behavior_contract_present")),
                    "checked": bool(fem.get("fallback_behavior_checked")),
                    "failed": bool(fem.get("fallback_behavior_failed")),
                    "repaired": bool(fem.get("fallback_behavior_repaired")),
                    "uncertainty_active": bool(fem.get("fallback_behavior_uncertainty_active")),
                    "repair_mode": _fem_clip_str(str(fem.get("fallback_behavior_repair_mode") or ""), limit=48),
                    "skip_reason": _fem_clip_str(fem.get("fallback_behavior_skip_reason")),
                    "clarifying_question_used": bool(fem.get("fallback_behavior_clarifying_question_used")),
                    "partial_used": bool(fem.get("fallback_behavior_partial_used")),
                },
            )
        )

    if any(k in fem for k in FEM_RESPONSE_TYPE_KEYS):
        rt_reasons = normalize_reason_list(fem.get("response_type_rejection_reasons"))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="response_type",
                action=_fem_response_type_action(fem),
                reasons=rt_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "required": _fem_clip_str(fem.get("response_type_required"), limit=48),
                    "contract_source": _fem_clip_str(fem.get("response_type_contract_source"), limit=64),
                    "candidate_ok": fem.get("response_type_candidate_ok"),
                    "repair_used": bool(fem.get("response_type_repair_used")),
                    "repair_kind": _fem_clip_str(fem.get("response_type_repair_kind"), limit=64),
                    "non_hostile_escalation_blocked": bool(fem.get("non_hostile_escalation_blocked")),
                },
            )
        )

    snap = fem.get(FEM_DEAD_TURN_KEY)
    if isinstance(snap, Mapping):
        rc = normalize_reason_list(snap.get("dead_turn_reason_codes"))[:8]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="dead_turn",
                action=TELEMETRY_ACTION_OBSERVED,
                reasons=rc,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "is_dead_turn": bool(snap.get("is_dead_turn")),
                    "dead_turn_class": _fem_clip_str(snap.get("dead_turn_class"), limit=48) or "none",
                    "validation_playable": bool(snap.get("validation_playable", True)),
                    "manual_test_valid": bool(snap.get("manual_test_valid", True)),
                },
            )
        )

    return events[:6]


def _curated_stage_diff_surface_for_bundle(stage_diff: Mapping[str, Any] | None) -> dict[str, Any]:
    """Shallow-stable copies of bounded stage-diff lists only (no arbitrary metadata pass-through).

    Keys are iterated in sorted order so the returned dict is stable across process runs
    (``frozenset`` iteration order is not guaranteed). ``stage_diff`` itself is owned by
    :mod:`game.stage_diff_telemetry`; this helper only copies the bundle allow-list.
    """
    if not isinstance(stage_diff, Mapping):
        return {}
    sdt = importlib.import_module("game.stage_diff_telemetry")
    bundle_keys = getattr(sdt, "STAGE_DIFF_BUNDLE_SURFACE_KEYS", frozenset())

    out: dict[str, Any] = {}
    for key in sorted(bundle_keys):
        if key not in stage_diff:
            continue
        raw = stage_diff.get(key)
        if not isinstance(raw, list):
            continue
        if key == "snapshots":
            out[key] = [dict(s) if isinstance(s, Mapping) else s for s in raw]
        else:
            out[key] = [dict(t) if isinstance(t, Mapping) else t for t in raw]
    return out


def assemble_unified_observational_telemetry_bundle(
    *,
    fem: Mapping[str, Any] | None = None,
    stage_diff: Mapping[str, Any] | None = None,
    evaluator_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble normalized FEM plus observational event projections from read-side inputs.

    ``final_emission_meta`` / ``fem_observability_events`` are built here. Stage-diff lists and
    events come from :mod:`game.stage_diff_telemetry`; evaluator events from
    :mod:`game.narrative_authenticity_eval` (separate from the evaluator scoring dict).
    ``fem_runtime_lineage_events`` is a sibling H1/H2 projection rather than an element of the
    canonical ``phase``/``action`` envelope.

    Stage-diff and evaluator builders are loaded with :func:`importlib.import_module` to avoid
    static import cycles at module import time (same behavior as eager imports).

    Read-side only; telemetry must not drive gate decisions.
    """
    fem_norm = normalize_final_emission_meta_for_observability(fem if isinstance(fem, Mapping) else None)
    fem_events = build_fem_observability_events(fem_norm)
    fem_runtime_lineage_events = build_fem_runtime_lineage_events(fem_norm)

    sdt = importlib.import_module("game.stage_diff_telemetry")
    build_stage_diff_observability_events = getattr(sdt, "build_stage_diff_observability_events", lambda _: [])

    sd_in = stage_diff if isinstance(stage_diff, Mapping) else None
    sd_events = build_stage_diff_observability_events(sd_in)
    sd_surface = _curated_stage_diff_surface_for_bundle(sd_in)

    nae = importlib.import_module("game.narrative_authenticity_eval")
    build_evaluator_observability_events = getattr(nae, "build_evaluator_observability_events", lambda _: [])

    ev_in = evaluator_result if isinstance(evaluator_result, Mapping) else None
    ev_events = build_evaluator_observability_events(ev_in)

    return {
        "final_emission_meta": fem_norm,
        "fem_observability_events": fem_events,
        "fem_runtime_lineage_events": fem_runtime_lineage_events,
        "stage_diff_observability_events": sd_events,
        "evaluator_observability_events": ev_events,
        "stage_diff_surface": sd_surface,
    }


def normalized_observational_telemetry_bundle(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Produce a normalized, observational-only **payload slice** for evaluator/debug consumers.

    This is **not** :func:`assemble_unified_observational_telemetry_bundle` — it does not attach
    stage-diff or evaluator canonical event lists; it normalizes FEM reads from a turn/API
    envelope plus a few lane-level keys useful for proof tooling.

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
        "emission_debug_lane_keys": sorted(str(k) for k in lane.keys()),
    }
