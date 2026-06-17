"""Final-emission player-facing narration purity layer (gate contract resolution + boundary apply).

Validator and contract construction remain in :mod:`game.player_facing_narration_purity`.
This module owns gate-layer resolution, metadata merge, skip/apply helpers, and
validate-only boundary application.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from game.player_facing_narration_purity import (
    player_facing_narration_purity_repair_hints,
    validate_player_facing_narration_purity,
)


def is_shipped_player_facing_narration_purity_contract(candidate: Any) -> bool:
    if not isinstance(candidate, dict):
        return False
    if "forbid_scaffold_headers" in candidate and "diegetic_only" in candidate:
        return True
    dr = str(candidate.get("debug_reason") or "")
    return "player_facing_narration_purity" in dr


def coerce_player_facing_narration_purity_contract(maybe: Any) -> Dict[str, Any] | None:
    if is_shipped_player_facing_narration_purity_contract(maybe):
        return maybe
    return None


def resolve_player_facing_narration_purity_contract(
    gm_output: Dict[str, Any] | None,
) -> tuple[Dict[str, Any] | None, str | None]:
    """Read shipped narration-purity policy from gm_output mirrors (no rebuild)."""
    if not isinstance(gm_output, dict):
        return None, None
    direct = gm_output.get("player_facing_narration_purity_contract")
    if isinstance(direct, dict):
        hit = coerce_player_facing_narration_purity_contract(direct)
        if hit:
            return hit, "player_facing_narration_purity_contract"
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = coerce_player_facing_narration_purity_contract(pol.get("player_facing_narration_purity"))
        if hit:
            return hit, "response_policy"
    pc = gm_output.get("prompt_context")
    if isinstance(pc, dict):
        hit = coerce_player_facing_narration_purity_contract(
            pc.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, "prompt_context"
        pol2 = pc.get("response_policy")
        if isinstance(pol2, dict):
            hit = coerce_player_facing_narration_purity_contract(
                pol2.get("player_facing_narration_purity")
            )
            if hit:
                return hit, "prompt_context.response_policy"
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = coerce_player_facing_narration_purity_contract(
            pl.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, key
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_player_facing_narration_purity_contract(
                rp.get("player_facing_narration_purity")
            )
            if hit:
                return hit, f"{key}.response_policy"
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = coerce_player_facing_narration_purity_contract(
            md.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, "metadata"
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_player_facing_narration_purity_contract(
                rp.get("player_facing_narration_purity")
            )
            if hit:
                return hit, "metadata.response_policy"
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = coerce_player_facing_narration_purity_contract(
            tr.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, "trace"
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_player_facing_narration_purity_contract(
                rp.get("player_facing_narration_purity")
            )
            if hit:
                return hit, "trace.response_policy"
    return None, None


def default_player_facing_narration_purity_meta() -> Dict[str, Any]:
    return {
        "player_facing_narration_purity_contract_resolution_source": None,
        "player_facing_narration_purity_skip_reason": None,
        "player_facing_narration_purity_checked": False,
        "player_facing_narration_purity_failed": False,
        "player_facing_narration_purity_repaired": False,
        "player_facing_narration_purity_repair_modes": [],
        "player_facing_narration_purity_violation_keys": [],
        "player_facing_narration_purity_repair_hints_used": [],
        "player_facing_narration_purity_collapsed_to_diegetic_core": False,
        "player_facing_narration_purity_preview_before": None,
        "player_facing_narration_purity_preview_after": None,
    }


def merge_player_facing_narration_purity_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    if not dbg:
        return
    for k, v in dbg.items():
        if str(k).startswith("player_facing_narration_purity_"):
            meta[k] = v


def merge_player_facing_narration_purity_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if str(k).startswith("player_facing_narration_purity_"):
            flat[k] = v
    nested: Dict[str, Any] = {
        "validation": {
            "checked": bool(gate_meta.get("player_facing_narration_purity_checked")),
            "passed": not bool(gate_meta.get("player_facing_narration_purity_failed")),
        },
        "violation_keys": list(gate_meta.get("player_facing_narration_purity_violation_keys") or []),
        "repair_hints": list(gate_meta.get("player_facing_narration_purity_repair_hints_used") or []),
        "repair_modes": list(gate_meta.get("player_facing_narration_purity_repair_modes") or []),
    }
    sr = gate_meta.get("player_facing_narration_purity_skip_reason")
    if sr:
        nested["skip_reason"] = sr
    pb = gate_meta.get("player_facing_narration_purity_preview_before")
    pa = gate_meta.get("player_facing_narration_purity_preview_after")
    if pb is not None:
        nested["preview_before"] = pb
    if pa is not None:
        nested["preview_after"] = pa

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        em["player_facing_narration_purity"] = nested
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


def gate_text_preview(text: str, limit: int = 96) -> str:
    t = str(text or "")
    return (t[:limit] + "…") if len(t) > limit else t


def skip_player_facing_narration_purity_layer(
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


def apply_player_facing_narration_purity_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> tuple[str, Dict[str, Any], List[str]]:
    meta = default_player_facing_narration_purity_meta()
    ctr, src = resolve_player_facing_narration_purity_contract(
        gm_output if isinstance(gm_output, dict) else None
    )
    meta["player_facing_narration_purity_contract_resolution_source"] = src
    skip = skip_player_facing_narration_purity_layer(text, ctr, response_type_debug=response_type_debug)
    meta["player_facing_narration_purity_skip_reason"] = skip
    if skip:
        return text, meta, []

    assert ctr is not None
    before = str(text or "")
    meta["player_facing_narration_purity_preview_before"] = gate_text_preview(before)
    v0 = validate_player_facing_narration_purity(
        before,
        ctr,
        player_text="",
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    if not v0.get("checked"):
        meta["player_facing_narration_purity_checked"] = False
        meta["player_facing_narration_purity_failed"] = False
        meta["player_facing_narration_purity_preview_after"] = gate_text_preview(before)
        return text, meta, []

    meta["player_facing_narration_purity_checked"] = True
    fails = [str(x) for x in (v0.get("failure_reasons") or []) if isinstance(x, str)]
    meta["player_facing_narration_purity_violation_keys"] = list(dict.fromkeys(fails))
    hints = player_facing_narration_purity_repair_hints(fails, contract=ctr)
    meta["player_facing_narration_purity_repair_hints_used"] = hints

    if v0.get("passed"):
        meta["player_facing_narration_purity_failed"] = False
        meta["player_facing_narration_purity_preview_after"] = gate_text_preview(before)
        return text, meta, []

    meta["player_facing_narration_purity_boundary_semantic_repair_disabled"] = True
    meta["player_facing_narration_purity_failed"] = True
    meta["player_facing_narration_purity_preview_after"] = gate_text_preview(before)
    extra2: List[str] = ["player_facing_narration_purity_unsatisfied_at_boundary_no_minimal_repair"]
    return text, meta, extra2
