"""Final-emission context-separation layer (gate contract resolution + boundary apply).

Validator and contract construction remain in :mod:`game.context_separation`.
This module owns gate-layer resolution, metadata merge, narrow repair helpers, and
validate-only boundary application.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from game.context_separation import context_separation_repair_hints, validate_context_separation
from game.final_emission_text import _normalize_text_preserve_paragraphs
from game.narrative_authority import _mask_dialogue_spans, _split_sentences
from game.response_policy_contracts import _last_player_input
from game.social_exchange_emission import merged_player_prompt_for_gate
from game.turn_packet import resolve_turn_packet_contract, resolve_turn_packet_for_gate


def is_shipped_full_context_separation_contract(candidate: Any) -> bool:
    """True for ``build_context_separation_contract`` payloads, not ad-hoc dicts."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict) and "forbid_topic_hijack" in candidate:
        return True
    if "forbid_topic_hijack" in candidate and "max_pressure_sentences_without_player_prompt" in candidate:
        return True
    return False


def coerce_context_separation_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if is_shipped_full_context_separation_contract(maybe):
        return maybe
    return None


def resolve_context_separation_contract(
    gm_output: Dict[str, Any] | None,
) -> tuple[Dict[str, Any] | None, str | None]:
    """Read the shipped contract from *gm_output* / narration / policy mirrors (no rebuild)."""
    if not isinstance(gm_output, dict):
        return None, None
    pkt = resolve_turn_packet_for_gate(gm_output)
    if isinstance(pkt, dict):
        hit = resolve_turn_packet_contract(pkt, "context_separation")
        hit = coerce_context_separation_contract_dict(hit)
        if hit:
            return hit, "turn_packet.contracts.context_separation"
    direct = gm_output.get("context_separation_contract")
    if isinstance(direct, dict):
        hit = coerce_context_separation_contract_dict(direct)
        if hit:
            return hit, "context_separation_contract"
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        for key in ("context_separation_contract", "context_separation"):
            hit = coerce_context_separation_contract_dict(pol.get(key))
            if hit:
                return hit, "response_policy"
    pc = gm_output.get("prompt_context")
    if isinstance(pc, dict):
        hit = coerce_context_separation_contract_dict(pc.get("context_separation_contract"))
        if hit:
            return hit, "prompt_context"
        pol2 = pc.get("response_policy")
        if isinstance(pol2, dict):
            for key in ("context_separation_contract", "context_separation"):
                hit = coerce_context_separation_contract_dict(pol2.get(key))
                if hit:
                    return hit, "prompt_context.response_policy"
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        for ck in ("context_separation_contract", "context_separation"):
            hit = coerce_context_separation_contract_dict(pl.get(ck))
            if hit:
                return hit, f"{key}"
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            for ck in ("context_separation_contract", "context_separation"):
                hit = coerce_context_separation_contract_dict(rp.get(ck))
                if hit:
                    return hit, f"{key}.response_policy"
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = coerce_context_separation_contract_dict(md.get("context_separation_contract"))
        if hit:
            return hit, "metadata"
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            for ck in ("context_separation_contract", "context_separation"):
                hit = coerce_context_separation_contract_dict(rp.get(ck))
                if hit:
                    return hit, "metadata.response_policy"
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = coerce_context_separation_contract_dict(tr.get("context_separation_contract"))
        if hit:
            return hit, "trace"
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            for ck in ("context_separation_contract", "context_separation"):
                hit = coerce_context_separation_contract_dict(rp.get(ck))
                if hit:
                    return hit, "trace.response_policy"
    return None, None


def default_context_separation_meta() -> Dict[str, Any]:
    return {
        "context_separation_contract_resolution_source": None,
        "context_separation_skip_reason": None,
        "context_separation_checked": False,
        "context_separation_ok": True,
        "context_separation_failed": False,
        "context_separation_failure_reasons": [],
        "context_separation_assertion_flags": {},
        "context_separation_repair_hints": [],
        "context_separation_repaired": False,
        "context_separation_repair_mode": None,
        "context_separation_debug_reason_marker": None,
        "context_separation_passed_after_repair": None,
    }


def merge_context_separation_meta(meta: Dict[str, Any], cs_dbg: Dict[str, Any]) -> None:
    if not cs_dbg:
        return
    keys = (
        "context_separation_contract_resolution_source",
        "context_separation_skip_reason",
        "context_separation_checked",
        "context_separation_ok",
        "context_separation_failed",
        "context_separation_failure_reasons",
        "context_separation_assertion_flags",
        "context_separation_repair_hints",
        "context_separation_repaired",
        "context_separation_repair_mode",
        "context_separation_debug_reason_marker",
        "context_separation_passed_after_repair",
    )
    for k in keys:
        if k in cs_dbg:
            meta[k] = cs_dbg[k]


def merge_context_separation_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("context_separation_"):
            continue
        flat[k] = v
    nested: Dict[str, Any] = {
        "validation": {
            "checked": bool(gate_meta.get("context_separation_checked")),
            "passed": bool(gate_meta.get("context_separation_ok")),
        },
        "failure_reasons": list(gate_meta.get("context_separation_failure_reasons") or []),
        "assertion_flags": dict(gate_meta.get("context_separation_assertion_flags") or {}),
        "repair_hints": list(gate_meta.get("context_separation_repair_hints") or []),
    }
    sr = gate_meta.get("context_separation_skip_reason")
    if sr:
        nested["skip_reason"] = sr
    mr = gate_meta.get("context_separation_debug_reason_marker")
    if mr:
        nested["debug_reason_marker"] = mr

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        em["context_separation"] = nested
        for fk, fv in flat.items():
            em[fk] = fv

    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        _patch_em(md_out.setdefault("emission_debug", {}))

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _patch_em(md_r.setdefault("emission_debug", {}))

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        _patch_em(eff_resolution["metadata"].setdefault("emission_debug", {}))


def context_separation_debug_reason_marker(
    before: str,
    after: str,
    *,
    violations: Sequence[str],
    repair_applied: bool,
    passed_after: bool | None,
) -> str:
    vkeys = "|".join(str(x) for x in violations if isinstance(x, str) and str(x).strip()) or "none"
    b = (before[:96] + "…") if len(before) > 96 else before
    a = (after[:96] + "…") if len(after) > 96 else after
    return (
        f"cs_violations={vkeys};repair_applied={repair_applied};pass_after={passed_after};"
        f"before_len={len(before)};after_len={len(after)};before_head={b!r};after_head={a!r}"
    )


def repair_context_separation_narrow(
    text: str,
    contract: Mapping[str, Any],
    *,
    player_text: str,
    resolution: Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    """Drop lead sentences (pressure-heavy openers) and re-validate; no invented replacement lines."""
    t = str(text or "")
    modes: List[str] = []
    for i in range(8):
        v = validate_context_separation(
            t,
            contract,
            player_text=player_text,
            resolution=resolution if isinstance(resolution, Mapping) else None,
        )
        if v.get("passed") or not v.get("checked"):
            if modes:
                return t, "|".join(modes)
            return None, None
        masked = _mask_dialogue_spans(t)
        sents = _split_sentences(masked, t)
        if len(sents) <= 1:
            return None, None
        start, end, _s0 = sents[0]
        t = _normalize_text_preserve_paragraphs((t[:start] + t[end:]).strip())
        if not t.strip():
            return None, None
        modes.append(f"drop_lead_{i + 1}")
    return None, None


def skip_context_separation_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    response_type_debug: Dict[str, Any] | None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not isinstance(contract, dict):
        return "no_shipped_contract"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    return None


def apply_context_separation_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    response_type_debug: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
) -> tuple[str, Dict[str, Any], List[str]]:
    strict_social_path = strict_social_details is not None
    meta = default_context_separation_meta()
    ctr, src = resolve_context_separation_contract(gm_output if isinstance(gm_output, dict) else None)
    meta["context_separation_contract_resolution_source"] = src

    skip = skip_context_separation_layer(text, ctr, response_type_debug=response_type_debug)
    meta["context_separation_skip_reason"] = skip
    if skip:
        meta["context_separation_debug_reason_marker"] = f"skip={skip}"
        return text, meta, []

    assert ctr is not None
    sid = str(scene_id or "").strip()
    player_text = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    if not str(player_text or "").strip():
        player_text = _last_player_input(
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )
    pt = str(player_text or "")

    before = str(text or "")
    v0 = validate_context_separation(
        before,
        ctr,
        player_text=pt,
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    meta["context_separation_checked"] = bool(v0.get("checked"))
    meta["context_separation_ok"] = bool(v0.get("passed"))
    af0 = v0.get("assertion_flags")
    meta["context_separation_assertion_flags"] = dict(af0) if isinstance(af0, dict) else {}
    fails0 = [str(x) for x in (v0.get("failure_reasons") or []) if isinstance(x, str)]
    meta["context_separation_failure_reasons"] = fails0
    meta["context_separation_repair_hints"] = context_separation_repair_hints(fails0, contract=ctr)

    if not v0.get("checked") or v0.get("passed"):
        meta["context_separation_debug_reason_marker"] = context_separation_debug_reason_marker(
            before,
            before,
            violations=[],
            repair_applied=False,
            passed_after=None,
        )
        return text, meta, []

    meta["context_separation_boundary_semantic_repair_disabled"] = True
    meta["context_separation_failed"] = True
    meta["context_separation_passed_after_repair"] = None
    meta["context_separation_debug_reason_marker"] = context_separation_debug_reason_marker(
        before,
        before,
        violations=fails0,
        repair_applied=False,
        passed_after=False,
    )

    extra: List[str] = []
    if not strict_social_path:
        extra.append("context_separation_unsatisfied_at_boundary_no_lead_drop")
    meta["context_separation_ok"] = False
    return text, meta, extra
