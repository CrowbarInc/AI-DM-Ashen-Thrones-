"""Compact, bounded stage-diff telemetry for GM outputs (observability only).

Stage-diff telemetry records **mutation observability** (snapshots and transitions) under
``metadata["stage_diff_telemetry"]``. It does not own engine truth or narration policy.

Snapshots reuse :func:`game.turn_packet.get_turn_packet` and, in the emission gate,
:func:`resolve_gate_turn_packet` so the same canonical **turn packet** accessor layer is
used everywhere — no parallel turn-state authority.

At the gate, :func:`resolve_gate_turn_packet` is the preferred resolver: it prefers the
intentionally ephemeral ``_gate_turn_packet_cache`` (see :mod:`game.final_emission_gate`),
then falls back to :func:`game.turn_packet.get_turn_packet`. The cache must not appear in
finalized player-facing output; callers pop it during finalize.

Appends to telemetry merge with any pre-existing ``stage_diff_telemetry`` dict keys
(beyond ``snapshots`` / ``transitions``) so nested subtrees are not clobbered.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

from game.turn_packet import get_turn_packet

STAGE_DIFF_METADATA_KEY = "stage_diff_telemetry"
_MAX_SNAPSHOTS = 12
_MAX_TRANSITIONS = 12

_LOG = logging.getLogger(__name__)


def _looks_like_packet(d: Any) -> bool:
    return isinstance(d, dict) and isinstance(d.get("contracts"), dict) and isinstance(d.get("version"), int)


def resolve_gate_turn_packet(gm_output: Mapping[str, Any] | None) -> Optional[Dict[str, Any]]:
    """Prefer ``_gate_turn_packet_cache`` when valid, else :func:`get_turn_packet`."""
    if not isinstance(gm_output, dict):
        return None
    cached = gm_output.get("_gate_turn_packet_cache")
    if _looks_like_packet(cached):
        return cached
    hit = get_turn_packet(
        gm_output,
        gm_output.get("response_policy"),
        gm_output.get("prompt_context"),
    )
    return hit if _looks_like_packet(hit) else None


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
    pkt = resolve_gate_turn_packet(gm_output)
    route = pkt.get("route") if isinstance(pkt, dict) else None
    route_d = route if isinstance(route, dict) else {}
    fb = pkt.get("fallback") if isinstance(pkt, dict) else None
    fb_d = fb if isinstance(fb, dict) else {}
    fprov = fb_d.get("fallback_provenance") if isinstance(fb_d.get("fallback_provenance"), dict) else {}
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    md_fb = md.get("fallback_provenance") if isinstance(md.get("fallback_provenance"), dict) else {}
    prov = fprov or md_fb
    fem = gm_output.get("_final_emission_meta") if isinstance(gm_output.get("_final_emission_meta"), dict) else {}
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
    na_codes = fem.get("narrative_authenticity_reason_codes")
    if isinstance(na_codes, list) and na_codes:
        snap["narrative_authenticity_reason_codes"] = [str(x) for x in na_codes[:8] if str(x).strip()]
    na_skip = fem.get("narrative_authenticity_skip_reason")
    if isinstance(na_skip, str) and na_skip.strip():
        snap["narrative_authenticity_skip_reason"] = na_skip.strip()[:120]
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
