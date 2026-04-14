"""Canonical owner for the turn-packet contract boundary.

This module is the **packet contract owner**: compact versioned packet construction,
stable accessors, and gate-side packet resolution. The turn packet is **not**
authoritative engine state and does not replace runtime resolution or validators.
It exists so retry logic, emission gates, and diagnostics can share one lookup path
and avoid seam drift from duplicated mirror scans. It does not own narration policy
or telemetry.

:mod:`game.stage_diff_telemetry` complements this layer with **mutation observability**
(bounded snapshots/transitions under ``metadata["stage_diff_telemetry"]``). Telemetry
is a packet **consumer** that derives its read path from this module; it is not a
parallel packet owner. The gate may use an intentionally ephemeral
``_gate_turn_packet_cache`` populated at entry and removed before finalized output.

Resolution order for consumers should be: (1) canonical packet, (2) direct
authoritative fields on the GM output, (3) legacy mirror / back-compat scans.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

TURN_PACKET_METADATA_KEY = "turn_packet"
_GATE_TURN_PACKET_CACHE_KEY = "_gate_turn_packet_cache"

_PACKET_VERSION = 1


def _looks_like_turn_packet(d: Any) -> bool:
    return isinstance(d, dict) and isinstance(d.get("contracts"), dict) and isinstance(d.get("version"), int)


def _as_str(v: Any) -> str:
    return str(v or "").strip()


def _resolution_kind(resolution: Mapping[str, Any] | None) -> str | None:
    if not isinstance(resolution, dict):
        return None
    k = _as_str(resolution.get("kind"))
    return k or None


def build_turn_packet(
    *,
    response_policy: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
    player_text: str | None = None,
    resolution: Mapping[str, Any] | None = None,
    interaction_continuity: Mapping[str, Any] | None = None,
    narration_obligations: Mapping[str, Any] | None = None,
    turn_id: Any = None,
    strict_social_expected: bool | None = None,
    last_human_adjacent_continuity: Any = None,
    fallback_provenance: Mapping[str, Any] | None = None,
    response_type: Any = None,
    sources_used: List[str] | None = None,
) -> Dict[str, Any]:
    """Assemble a compact, versioned turn packet (snapshot only; not a policy engine)."""
    rp = response_policy if isinstance(response_policy, dict) else {}
    ic = interaction_continuity if isinstance(interaction_continuity, dict) else {}
    ob = narration_obligations if isinstance(narration_obligations, dict) else {}

    ac = rp.get("answer_completeness")
    rd = rp.get("response_delta")
    fb = rp.get("fallback_behavior")
    te = rp.get("tone_escalation")
    ar = rp.get("anti_railroading")
    cs = rp.get("context_separation")
    if cs is None and isinstance(rp.get("context_separation_contract"), dict):
        cs = rp.get("context_separation_contract")
    rt = response_type if response_type is not None else rp.get("response_type")

    contracts: Dict[str, Any] = {
        "answer_completeness": ac if isinstance(ac, dict) else None,
        "response_delta": rd if isinstance(rd, dict) else None,
        "fallback_behavior": fb if isinstance(fb, dict) else None,
        "tone_escalation": te if isinstance(te, dict) else None,
        "anti_railroading": ar if isinstance(ar, dict) else None,
        "context_separation": cs if isinstance(cs, dict) else None,
        "response_type": rt,
    }

    missing: List[str] = []
    for name, val in contracts.items():
        if name == "response_type" and val is None:
            continue
        if val is None:
            missing.append(name)

    route_strict = strict_social_expected
    if route_strict is None and "suppress_non_social_emitters" in ob:
        route_strict = bool(ob.get("suppress_non_social_emitters"))

    packet: Dict[str, Any] = {
        "version": _PACKET_VERSION,
        "turn_id": turn_id,
        "scene_id": _as_str(scene_id) or None,
        "player_text": str(player_text or "") or None,
        "resolution_kind": _resolution_kind(resolution if isinstance(resolution, dict) else None),
        "route": {
            "interaction_mode": ic.get("interaction_mode"),
            "active_target_id": _as_str(ic.get("active_interaction_target_id")) or None,
            "active_reply_kind": ob.get("active_npc_reply_kind"),
            "strict_social_expected": route_strict,
        },
        "response_policy": dict(rp) if rp else {},
        "contracts": contracts,
        "continuity": {
            "last_human_adjacent_continuity": last_human_adjacent_continuity,
        },
        "fallback": {
            "fallback_provenance": dict(fallback_provenance)
            if isinstance(fallback_provenance, dict)
            else None,
        },
        "debug": {
            "sources_used": list(sources_used or ["build_turn_packet"]),
            "missing_contracts": missing,
        },
    }
    return packet


def attach_turn_packet(gm_output: Dict[str, Any], packet: Mapping[str, Any]) -> None:
    """Store *packet* on *gm_output* metadata under :data:`TURN_PACKET_METADATA_KEY` (non-destructive merge)."""
    if not isinstance(gm_output, dict) or not isinstance(packet, Mapping):
        return
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    gm_output["metadata"] = {**md, TURN_PACKET_METADATA_KEY: dict(packet)}


def get_turn_packet(*sources: Any) -> Optional[Dict[str, Any]]:
    """Return the first canonical turn packet found across *sources* (dict roots, metadata, prompt_context)."""
    for src in sources:
        if not isinstance(src, dict):
            continue
        direct = src.get(TURN_PACKET_METADATA_KEY)
        if _looks_like_turn_packet(direct):
            return direct
        md = src.get("metadata")
        if isinstance(md, dict):
            hit = md.get(TURN_PACKET_METADATA_KEY)
            if _looks_like_turn_packet(hit):
                return hit
        pc = src.get("prompt_context")
        if isinstance(pc, dict):
            hit_pc = pc.get(TURN_PACKET_METADATA_KEY)
            if _looks_like_turn_packet(hit_pc):
                return hit_pc
            md2 = pc.get("metadata")
            if isinstance(md2, dict):
                hit2 = md2.get(TURN_PACKET_METADATA_KEY)
                if _looks_like_turn_packet(hit2):
                    return hit2
            if _looks_like_turn_packet(pc.get("turn_packet")):
                return pc["turn_packet"]
    return None


def resolve_turn_packet_for_gate(gm_output: Mapping[str, Any] | None) -> Optional[Dict[str, Any]]:
    """Canonical gate-side packet accessor.

    Packet boundary owner: prefer the ephemeral gate cache when present, otherwise
    fall back to :func:`get_turn_packet`. Telemetry/retry callers derive from this
    accessor; they do not own the packet boundary.
    """
    if not isinstance(gm_output, dict):
        return None
    cached = gm_output.get(_GATE_TURN_PACKET_CACHE_KEY)
    if _looks_like_turn_packet(cached):
        return cached
    hit = get_turn_packet(
        gm_output,
        gm_output.get("response_policy"),
        gm_output.get("prompt_context"),
    )
    return hit if _looks_like_turn_packet(hit) else None


def ensure_turn_packet(gm_output: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """Return an existing packet on *gm_output* or build, attach, and return a new one."""
    existing = get_turn_packet(gm_output)
    if isinstance(existing, dict):
        return existing
    packet = build_turn_packet(**kwargs)
    attach_turn_packet(gm_output, packet)
    attached = get_turn_packet(gm_output)
    return attached if isinstance(attached, dict) else packet


def resolve_turn_packet_contract(packet: Mapping[str, Any] | None, contract_name: str) -> Any:
    """Read a named contract from *packet* ``contracts`` (no coercion; callers validate)."""
    if not isinstance(packet, dict) or not contract_name:
        return None
    c = packet.get("contracts")
    if not isinstance(c, dict):
        return None
    return c.get(contract_name)


def resolve_turn_packet_field(
    packet: Mapping[str, Any] | None, field_name: str, default: Any = None
) -> Any:
    """Resolve a top-level *field_name* or one segment of ``group.field`` on *packet*."""
    if not isinstance(packet, dict) or not field_name:
        return default
    if "." in field_name:
        group, _, sub = field_name.partition(".")
        subd = packet.get(group)
        if isinstance(subd, dict):
            return subd.get(sub, default)
        return default
    return packet.get(field_name, default)
