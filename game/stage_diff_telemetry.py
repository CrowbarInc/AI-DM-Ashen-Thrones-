"""Bounded **stage-diff telemetry** owner (raw snapshots/transitions + read-side event projection).

Canonical telemetry-only owner.

Writes **compare-ready** dicts under ``metadata["stage_diff_telemetry"]`` during gate/retry work.
That log is observability only — not a second engine truth or legality store.

:func:`build_stage_diff_observability_events` maps the raw structure into **canonical
observational events** from :mod:`game.telemetry_vocab` (aggregates over route/fallback/repair/
retry/NA tail signals). Those events are inspect-only and must not steer orchestration.

Snapshots may include a **curated** NA slice from FEM via
:func:`game.final_emission_meta.stage_diff_narrative_authenticity_projection`; NA semantics
remain FEM/NA-owned — this module only consumes the bounded projection.

Packet fields come from :mod:`game.turn_packet`. ``resolve_gate_turn_packet`` is a thin
compatibility wrapper around :func:`game.turn_packet.resolve_turn_packet_for_gate`.

Merges preserve existing ``stage_diff_telemetry`` keys outside ``snapshots`` / ``transitions``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

from game.final_emission_meta import read_final_emission_meta_dict, stage_diff_narrative_authenticity_projection
from game.telemetry_vocab import (
    TELEMETRY_ACTION_OBSERVED,
    TELEMETRY_ACTION_REPAIRED,
    TELEMETRY_PHASE_GATE,
    TELEMETRY_SCOPE_TURN,
    build_telemetry_event,
    normalize_reason_list,
)
from game.turn_packet import resolve_turn_packet_for_gate

STAGE_DIFF_METADATA_KEY = "stage_diff_telemetry"
# Keys allowed on the read-side bundle ``stage_diff_surface`` (bounded inspectable payload only).
STAGE_DIFF_BUNDLE_SURFACE_KEYS: frozenset[str] = frozenset({"snapshots", "transitions"})
_MAX_SNAPSHOTS = 12
_MAX_TRANSITIONS = 12

_LOG = logging.getLogger(__name__)


def resolve_gate_turn_packet(gm_output: Mapping[str, Any] | None) -> Optional[Dict[str, Any]]:
    """Compatibility residue wrapper around the packet-owner gate accessor."""
    return resolve_turn_packet_for_gate(gm_output)


def compact_text_fingerprint(text: str | None) -> str:
    raw = str(text or "")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def compact_preview(text: str | None, *, limit: int = 120) -> str:
    raw = str(text or "")
    if len(raw) <= limit:
        return raw
    return raw[: max(0, limit - 1)] + "…"


def _repair_flag_list(meta: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(meta, dict):
        return []
    keys = (
        "answer_completeness_repaired",
        "response_delta_repaired",
        "social_response_structure_repair_applied",
        "narrative_authenticity_repaired",
        "tone_escalation_repaired",
        "anti_railroading_repaired",
        "context_separation_repaired",
        "player_facing_narration_purity_repaired",
        "answer_shape_primacy_repaired",
        "fallback_behavior_repaired",
        "narrative_authority_repaired",
    )
    out: List[str] = []
    for k in keys:
        if meta.get(k):
            out.append(str(k))
    return out


def snapshot_turn_stage(
    gm_output: Mapping[str, Any] | None,
    stage: str,
    *,
    timing_ms: float | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Return a compact, compare-ready snapshot dict (does not mutate *gm_output*)."""
    if not isinstance(gm_output, dict):
        return {"stage": stage, "player_facing_fingerprint": None, "player_facing_preview": "", "text_len": 0}
    pft = str(gm_output.get("player_facing_text") or "")
    pkt = resolve_turn_packet_for_gate(gm_output)
    route = pkt.get("route") if isinstance(pkt, dict) else None
    route_d = route if isinstance(route, dict) else {}
    fb = pkt.get("fallback") if isinstance(pkt, dict) else None
    fb_d = fb if isinstance(fb, dict) else {}
    fprov = fb_d.get("fallback_provenance") if isinstance(fb_d.get("fallback_provenance"), dict) else {}
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    md_fb = md.get("fallback_provenance") if isinstance(md.get("fallback_provenance"), dict) else {}
    prov = fprov or md_fb
    fem = read_final_emission_meta_dict(gm_output if isinstance(gm_output, Mapping) else None)
    contracts = pkt.get("contracts") if isinstance(pkt, dict) else None
    c = contracts if isinstance(contracts, dict) else {}
    snap: Dict[str, Any] = {
        "stage": stage,
        "player_facing_fingerprint": compact_text_fingerprint(pft),
        "player_facing_preview": compact_preview(pft),
        "text_len": len(pft),
        "final_route": fem.get("final_route") if fem.get("final_route") is not None else gm_output.get("final_route"),
        "fallback_kind": gm_output.get("fallback_kind"),
        "accepted_via": gm_output.get("accepted_via"),
        "response_type": c.get("response_type"),
        "resolution_kind": pkt.get("resolution_kind") if isinstance(pkt, dict) else None,
        "active_target_id": route_d.get("active_target_id"),
        "reply_kind": route_d.get("active_reply_kind"),
        "fallback_source": prov.get("source"),
        "fallback_stage": prov.get("stage"),
        "repair_flags": _repair_flag_list(fem),
        "retry_flags": {
            "retry_exhausted": bool(gm_output.get("retry_exhausted")),
            "targeted_retry_terminal": bool(gm_output.get("targeted_retry_terminal")),
        },
    }
    na_proj = stage_diff_narrative_authenticity_projection(fem)
    if na_proj:
        na_codes = na_proj.get("narrative_authenticity_reason_codes")
        if isinstance(na_codes, list) and na_codes:
            snap["narrative_authenticity_reason_codes"] = normalize_reason_list(na_codes)[:8]
        na_skip = na_proj.get("narrative_authenticity_skip_reason")
        if isinstance(na_skip, str) and na_skip.strip():
            snap["narrative_authenticity_skip_reason"] = na_skip.strip()[:120]
        na_status = na_proj.get("narrative_authenticity_status")
        if isinstance(na_status, str) and na_status.strip():
            snap["narrative_authenticity_status"] = na_status.strip()[:24]
        if na_proj.get("narrative_authenticity_rumor_relaxed_low_signal"):
            snap["narrative_authenticity_rumor_relaxed_low_signal"] = True
        if na_proj.get("rumor_turn_active") is not None:
            snap["rumor_turn_active"] = bool(na_proj.get("rumor_turn_active"))
    if timing_ms is not None:
        snap["timing_ms"] = float(timing_ms)
    if kwargs:
        for k, v in kwargs.items():
            if k in snap or k in (
                "stage",
                "player_facing_fingerprint",
                "player_facing_preview",
                "text_len",
                "repair_flags",
                "retry_flags",
            ):
                continue
            if v is None:
                continue
            snap[k] = v
    return snap


def diff_turn_stage(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Summarize changes between two snapshots (compact booleans + deltas)."""
    b = before if isinstance(before, dict) else {}
    a = after if isinstance(after, dict) else {}

    def _eq(key: str) -> bool:
        return b.get(key) == a.get(key)

    text_changed = not _eq("player_facing_fingerprint")
    route_changed = not _eq("final_route") or not _eq("active_target_id") or not _eq("reply_kind")
    fb_changed = not _eq("fallback_source") or not _eq("fallback_stage") or not _eq("fallback_kind")
    repair_changed = list(b.get("repair_flags") or []) != list(a.get("repair_flags") or [])
    res_changed = not _eq("resolution_kind")
    retry_changed = (b.get("retry_flags") or {}) != (a.get("retry_flags") or {})
    terminal_activated = (not (b.get("retry_flags") or {}).get("targeted_retry_terminal")) and (
        (a.get("retry_flags") or {}).get("targeted_retry_terminal") is True
    )
    return {
        "text_fingerprint_changed": text_changed,
        "route_changed": route_changed,
        "fallback_changed": fb_changed,
        "repair_flags_changed": repair_changed,
        "resolution_kind_changed": res_changed,
        "retry_flags_changed": retry_changed,
        "terminal_retry_activated": terminal_activated,
    }


def _append_bounded(bucket: List[Any], item: Mapping[str, Any], cap: int) -> None:
    bucket.append(dict(item))
    overflow = len(bucket) - cap
    if overflow > 0:
        del bucket[:overflow]


def _ensure_telemetry_dict(gm_output: MutableMapping[str, Any]) -> Dict[str, Any]:
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    raw = md.get(STAGE_DIFF_METADATA_KEY)
    base: Dict[str, Any] = dict(raw) if isinstance(raw, dict) else {}
    if not isinstance(base.get("snapshots"), list):
        base["snapshots"] = []
    if not isinstance(base.get("transitions"), list):
        base["transitions"] = []
    gm_output["metadata"] = {**md, STAGE_DIFF_METADATA_KEY: base}
    return base


def _annotate_fallback_provenance_with_transition(
    gm_output: MutableMapping[str, Any], from_stage: str, to_stage: str
) -> None:
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    prov = md.get("fallback_provenance")
    if not isinstance(prov, dict):
        return
    prov2 = {
        **prov,
        "stage_diff_last_transition": f"{from_stage}→{to_stage}",
    }
    gm_output["metadata"] = {**md, "fallback_provenance": prov2}


def record_stage_snapshot(
    gm_output: MutableMapping[str, Any],
    stage_name: str,
    *,
    snapshot: Mapping[str, Any] | None = None,
    timing_ms: float | None = None,
    **kwargs: Any,
) -> None:
    """Append a bounded snapshot under ``metadata[STAGE_DIFF_METADATA_KEY]['snapshots']``."""
    if not isinstance(gm_output, dict):
        return
    tel = _ensure_telemetry_dict(gm_output)
    snap = (
        dict(snapshot)
        if isinstance(snapshot, dict)
        else snapshot_turn_stage(gm_output, stage_name, timing_ms=timing_ms, **kwargs)
    )
    snap["stage"] = stage_name
    _append_bounded(tel["snapshots"], snap, _MAX_SNAPSHOTS)


def _meaningful_transition(diff: Mapping[str, Any]) -> bool:
    return bool(
        diff.get("text_fingerprint_changed")
        or diff.get("route_changed")
        or diff.get("fallback_changed")
        or diff.get("terminal_retry_activated")
    )


def record_stage_transition(
    gm_output: MutableMapping[str, Any],
    from_stage: str,
    to_stage: str,
    before_snapshot: Mapping[str, Any] | None,
    after_snapshot: Mapping[str, Any] | None,
) -> None:
    """Append a bounded transition record and optionally log meaningful diffs."""
    if not isinstance(gm_output, dict):
        return
    diff = diff_turn_stage(before_snapshot, after_snapshot)
    tel = _ensure_telemetry_dict(gm_output)
    rec = {
        "from": from_stage,
        "to": to_stage,
        "diff": diff,
    }
    _append_bounded(tel["transitions"], rec, _MAX_TRANSITIONS)
    _annotate_fallback_provenance_with_transition(gm_output, from_stage, to_stage)
    payload = {
        "event": "STAGE_DIFF_MEANINGFUL",
        "from": from_stage,
        "to": to_stage,
        "diff": diff,
    }
    line = json.dumps(payload, default=str, ensure_ascii=False)
    if diff.get("terminal_retry_activated"):
        _LOG.warning("STAGE_DIFF %s", line)
    elif diff.get("route_changed") or diff.get("fallback_changed"):
        _LOG.info("STAGE_DIFF %s", line)
    elif _meaningful_transition(diff):
        _LOG.debug("STAGE_DIFF %s", line)


def _stage_diff_clip(value: Any, *, limit: int = 64) -> str | None:
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)] + "…"


def _last_snapshot_dict(snapshots: Any) -> dict[str, Any]:
    if not isinstance(snapshots, list) or not snapshots:
        return {}
    tail = snapshots[-1]
    return dict(tail) if isinstance(tail, Mapping) else {}


def build_stage_diff_observability_events(stage_diff: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Project **raw** ``stage_diff_telemetry`` into canonical observational events (read-only).

    Input dicts match :func:`record_stage_snapshot` / :func:`record_stage_transition`; outputs use
    :func:`game.telemetry_vocab.build_telemetry_event`. Transition ``repair_flags_changed`` and
    snapshot ``repair_flags`` are different raw signals; the repair cluster event may use both
    without reading FEM repair booleans.

    Aggregates over transitions plus the latest snapshot. Does not mutate *stage_diff*.
    """
    if not isinstance(stage_diff, Mapping):
        return []

    transitions = stage_diff.get("transitions")
    snapshots = stage_diff.get("snapshots")
    t_list = transitions if isinstance(transitions, list) else []
    s_list = snapshots if isinstance(snapshots, list) else []

    any_route = False
    any_fallback = False
    any_repair_delta = False
    any_retry = False
    terminal_retry = False
    for rec in t_list:
        if not isinstance(rec, Mapping):
            continue
        diff = rec.get("diff")
        if not isinstance(diff, Mapping):
            continue
        any_route = any_route or bool(diff.get("route_changed"))
        any_fallback = any_fallback or bool(diff.get("fallback_changed"))
        any_repair_delta = any_repair_delta or bool(diff.get("repair_flags_changed"))
        any_retry = any_retry or bool(diff.get("retry_flags_changed"))
        terminal_retry = terminal_retry or bool(diff.get("terminal_retry_activated"))

    last = _last_snapshot_dict(s_list)
    repair_on_tail = normalize_reason_list(last.get("repair_flags"))[:12]
    rf_tail = last.get("retry_flags") if isinstance(last.get("retry_flags"), Mapping) else {}
    retry_exhausted = bool(rf_tail.get("retry_exhausted"))
    targeted_terminal = bool(rf_tail.get("targeted_retry_terminal"))

    fb_kind = _stage_diff_clip(str(last.get("fallback_kind") or ""), limit=48)
    fb_src = _stage_diff_clip(str(last.get("fallback_source") or ""), limit=48)
    fb_stage = _stage_diff_clip(str(last.get("fallback_stage") or ""), limit=48)
    fallback_signal = bool(fb_kind or fb_src or fb_stage)

    na_status = _stage_diff_clip(str(last.get("narrative_authenticity_status") or ""), limit=24)
    na_skip = _stage_diff_clip(str(last.get("narrative_authenticity_skip_reason") or ""), limit=120)
    na_codes = normalize_reason_list(last.get("narrative_authenticity_reason_codes"))[:8]
    na_rumor_relaxed = last.get("narrative_authenticity_rumor_relaxed_low_signal")
    rumor_turn = last.get("rumor_turn_active")
    na_cluster = bool(na_status or na_skip or na_codes or na_rumor_relaxed is True or rumor_turn is not None)

    owner = "stage_diff_telemetry"
    events: list[dict[str, Any]] = []

    if any_route:
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner=owner,
                action=TELEMETRY_ACTION_OBSERVED,
                reasons=["stage_diff_route_changed"],
                scope=TELEMETRY_SCOPE_TURN,
                data={"route_changed": True},
            )
        )

    if any_fallback or fallback_signal:
        reasons: list[str] = []
        if any_fallback:
            reasons.append("stage_diff_fallback_changed")
        if fallback_signal and not any_fallback:
            reasons.append("stage_diff_fallback_path_present")
        reasons = list(dict.fromkeys(reasons))[:8]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner=owner,
                action=TELEMETRY_ACTION_OBSERVED,
                reasons=reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "transition_fallback_changed": bool(any_fallback),
                    "fallback_kind": fb_kind,
                    "fallback_source": fb_src,
                    "fallback_stage": fb_stage,
                },
            )
        )

    repair_reasons: list[str] = []
    if any_repair_delta:
        repair_reasons.append("stage_diff_repair_flags_changed")
    if repair_on_tail:
        repair_reasons.append("stage_diff_repair_flags_present")
    repair_reasons = list(dict.fromkeys(repair_reasons))[:8]
    if any_repair_delta or repair_on_tail:
        repair_action = TELEMETRY_ACTION_REPAIRED if any_repair_delta else TELEMETRY_ACTION_OBSERVED
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner=owner,
                action=repair_action,
                reasons=repair_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "transition_repair_delta": bool(any_repair_delta),
                    "repair_flags": list(repair_on_tail),
                },
            )
        )

    if any_retry or terminal_retry or retry_exhausted or targeted_terminal:
        r_reasons: list[str] = []
        if terminal_retry:
            r_reasons.append("stage_diff_terminal_retry_activated")
        if any_retry:
            r_reasons.append("stage_diff_retry_flags_changed")
        if retry_exhausted:
            r_reasons.append("stage_diff_retry_exhausted_observed")
        if targeted_terminal:
            r_reasons.append("stage_diff_targeted_retry_terminal_observed")
        r_reasons = list(dict.fromkeys(r_reasons))[:8]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner=owner,
                action=TELEMETRY_ACTION_OBSERVED,
                reasons=r_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "transition_retry_delta": bool(any_retry),
                    "terminal_retry_activated": bool(terminal_retry),
                    "retry_exhausted": retry_exhausted,
                    "targeted_retry_terminal": targeted_terminal,
                },
            )
        )

    if na_cluster:
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner=owner,
                action=TELEMETRY_ACTION_OBSERVED,
                reasons=na_codes,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "narrative_authenticity_status": na_status,
                    "narrative_authenticity_skip_reason": na_skip,
                    "narrative_authenticity_rumor_relaxed_low_signal": bool(na_rumor_relaxed),
                    "rumor_turn_active": (bool(rumor_turn) if rumor_turn is not None else None),
                },
            )
        )

    return events[:6]
