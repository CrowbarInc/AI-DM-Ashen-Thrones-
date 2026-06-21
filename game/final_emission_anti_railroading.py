"""Final-emission anti-railroading layer (gate contract resolution + boundary apply).

Validator and contract construction remain in :mod:`game.anti_railroading`.
This module owns gate-layer resolution, metadata merge, narrow repair helpers, and
validate-only boundary application.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping

from game.anti_railroading import (
    anti_railroading_repair_hints,
    build_anti_railroading_contract,
    validate_anti_railroading,
)
from game.final_emission_narrative_authority import resolve_narrative_authority_contract
from game.final_emission_scene_state_anchor import _resolve_scene_state_anchor_contract
from game.response_policy_contracts import _last_player_input
from game.social_exchange_policy import merged_player_prompt_for_gate
from game.turn_packet import resolve_turn_packet_contract, resolve_turn_packet_for_gate


def is_shipped_full_anti_railroading_contract(candidate: Any) -> bool:
    """True for ``build_anti_railroading_contract`` payloads."""
    if not isinstance(candidate, dict):
        return False
    return "forbid_player_decision_override" in candidate and "enabled" in candidate


def coerce_anti_railroading_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if is_shipped_full_anti_railroading_contract(maybe):
        return maybe
    return None


def resolve_anti_railroading_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Prefer shipped narration / prompt_context mirrors; never substitute prompt_debug alone."""
    if not isinstance(gm_output, dict):
        return None
    pkt = resolve_turn_packet_for_gate(gm_output)
    if isinstance(pkt, dict):
        hit = resolve_turn_packet_contract(pkt, "anti_railroading")
        hit = coerce_anti_railroading_contract_dict(hit)
        if hit:
            return hit
    direct = gm_output.get("anti_railroading_contract")
    if isinstance(direct, dict):
        hit = coerce_anti_railroading_contract_dict(direct)
        if hit:
            return hit
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = coerce_anti_railroading_contract_dict(pol.get("anti_railroading"))
        if hit:
            return hit
    pc = gm_output.get("prompt_context")
    if isinstance(pc, dict):
        hit = coerce_anti_railroading_contract_dict(pc.get("anti_railroading_contract"))
        if hit:
            return hit
        pol2 = pc.get("response_policy")
        if isinstance(pol2, dict):
            hit = coerce_anti_railroading_contract_dict(pol2.get("anti_railroading"))
            if hit:
                return hit
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = coerce_anti_railroading_contract_dict(pl.get("anti_railroading_contract"))
        if hit:
            return hit
        hit = coerce_anti_railroading_contract_dict(pl.get("anti_railroading"))
        if hit:
            return hit
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_anti_railroading_contract_dict(rp.get("anti_railroading"))
            if hit:
                return hit
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = coerce_anti_railroading_contract_dict(md.get("anti_railroading_contract"))
        if hit:
            return hit
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_anti_railroading_contract_dict(rp.get("anti_railroading"))
            if hit:
                return hit
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = coerce_anti_railroading_contract_dict(tr.get("anti_railroading_contract"))
        if hit:
            return hit
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_anti_railroading_contract_dict(rp.get("anti_railroading"))
            if hit:
                return hit
    return None


def fallback_build_anti_railroading_contract(
    gm_output: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
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
    prompt_leads: Any = None
    active_pending_leads: Any = None
    follow_surface: Any = None
    if isinstance(gm_output, dict):
        prompt_leads = gm_output.get("prompt_leads")
        active_pending_leads = gm_output.get("active_pending_leads")
        for key in ("prompt_payload", "narration_payload", "_narration_payload"):
            pl = gm_output.get(key)
            if not isinstance(pl, dict):
                continue
            if prompt_leads is None and pl.get("prompt_leads") is not None:
                prompt_leads = pl.get("prompt_leads")
            if active_pending_leads is None and pl.get("active_pending_leads") is not None:
                active_pending_leads = pl.get("active_pending_leads")
        pc = gm_output.get("prompt_context")
        if isinstance(pc, dict):
            if prompt_leads is None and pc.get("prompt_leads") is not None:
                prompt_leads = pc.get("prompt_leads")
            if active_pending_leads is None and pc.get("active_pending_leads") is not None:
                active_pending_leads = pc.get("active_pending_leads")
            if isinstance(pc.get("follow_surface"), dict):
                follow_surface = pc.get("follow_surface")
    nac = resolve_narrative_authority_contract(gm_output if isinstance(gm_output, dict) else None)
    sac = _resolve_scene_state_anchor_contract(gm_output if isinstance(gm_output, dict) else None)
    return build_anti_railroading_contract(
        resolution=resolution if isinstance(resolution, Mapping) else None,
        session_view=session if isinstance(session, Mapping) else None,
        narrative_authority_contract=nac if isinstance(nac, Mapping) else None,
        scene_state_anchor_contract=sac if isinstance(sac, Mapping) else None,
        prompt_leads=prompt_leads,
        active_pending_leads=active_pending_leads,
        follow_surface=follow_surface,
        player_text=player_text,
    )


def effective_anti_railroading_contract_for_gate(
    gm_output: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> tuple[Dict[str, Any], str]:
    shipped = resolve_anti_railroading_contract(gm_output if isinstance(gm_output, dict) else None)
    if shipped is not None:
        return shipped, "shipped"
    built = fallback_build_anti_railroading_contract(gm_output, resolution, session, scene_id)
    return built, "fallback_build"


def default_anti_railroading_meta() -> Dict[str, Any]:
    return {
        "anti_railroading_checked": False,
        "anti_railroading_ok": True,
        "anti_railroading_failed": False,
        "anti_railroading_failure_reasons": [],
        "anti_railroading_assertion_flags": {},
        "anti_railroading_repair_hints": [],
        "anti_railroading_repaired": False,
        "anti_railroading_repair_mode": None,
        "anti_railroading_skip_reason": None,
        "anti_railroading_contract_resolution_source": None,
    }


def merge_anti_railroading_meta(meta: Dict[str, Any], ar_dbg: Dict[str, Any]) -> None:
    if not ar_dbg:
        return
    keys = (
        "anti_railroading_checked",
        "anti_railroading_ok",
        "anti_railroading_failed",
        "anti_railroading_failure_reasons",
        "anti_railroading_assertion_flags",
        "anti_railroading_repair_hints",
        "anti_railroading_repaired",
        "anti_railroading_repair_mode",
        "anti_railroading_skip_reason",
        "anti_railroading_contract_resolution_source",
    )
    for k in keys:
        if k in ar_dbg:
            meta[k] = ar_dbg[k]


def merge_anti_railroading_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
) -> None:
    _ = gm_output
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("anti_railroading_"):
            continue
        flat[k] = v
    nested: Dict[str, Any] = {
        "validation": {
            "checked": bool(gate_meta.get("anti_railroading_checked")),
            "passed": bool(gate_meta.get("anti_railroading_ok")),
        },
        "failure_reasons": list(gate_meta.get("anti_railroading_failure_reasons") or []),
        "assertion_flags": dict(gate_meta.get("anti_railroading_assertion_flags") or {}),
        "repair_hints": list(gate_meta.get("anti_railroading_repair_hints") or []),
    }
    sr = gate_meta.get("anti_railroading_skip_reason")
    if sr:
        nested["skip_reason"] = sr

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        em["anti_railroading"] = nested
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


def _repair_head_straight_dest(m: re.Match[str]) -> str:
    dest = m.group(1).strip().rstrip(".!?")
    punct = m.group(2) or "."
    if not dest:
        return m.group(0)
    cap = dest[0].upper() + dest[1:] if len(dest) > 1 else dest.upper()
    return f"{cap} reads as one plausible next step; you could head there, or weigh another lead first{punct}"


def _apply_single_anti_railroading_repair_pass(text: str, af: Mapping[str, Any]) -> tuple[str | None, str | None]:
    if not isinstance(af, Mapping) or not str(text or "").strip():
        return None, None
    if af.get("player_decision_override"):
        t2 = re.sub(
            r"(?is)\b(you\s+decide\s+to\s+)(.+?)([.!?]|$)",
            lambda m: f"You could {m.group(2).strip()}, or choose a different angle{m.group(3) or '.'}",
            text,
            count=1,
        )
        if t2 != text:
            return t2, "player_decision_override_soften"
        t2 = re.sub(
            r"(?is)\b(you\s+chooses?\s+to\s+)(.+?)([.!?]|$)",
            lambda m: f"You could {m.group(2).strip()}, or choose a different angle{m.group(3) or '.'}",
            text,
            count=1,
        )
        if t2 != text:
            return t2, "player_decision_override_soften"
    if af.get("forced_direction"):
        t2 = re.sub(
            r"(?is)\bYou\s+head\s+straight\s+(?:for|toward|towards|to)\s+(.+?)([.!?]|$)",
            _repair_head_straight_dest,
            text,
            count=1,
        )
        if t2 != text:
            return t2, "forced_direction_head_straight"
        t2 = re.sub(
            r"(?is)(.+?),\s*so\s+you\s+go\s+there\s*([.!?]|$)",
            lambda m: m.group(1).rstrip().rstrip(",").strip()
            + " as a strong lead; you could follow that thread, or test a different angle"
            + (m.group(2) or "."),
            text,
            count=1,
        )
        if t2 != text:
            return t2, "forced_direction_so_you_go"
        t2 = re.sub(
            r"(?is)(.+?)\s+isn't\s+optional;\s*you(?:'re| are)\s+going\s+there\s+now\s*([.!?]|$)",
            lambda m: m.group(1).strip()
            + " remains a strong pressure; treat it as one option among several"
            + (m.group(2) or "."),
            text,
            count=1,
        )
        if t2 != text:
            return t2, "forced_direction_surfaced_lead_mandatory"
    if af.get("exclusive_path_claim"):
        t2 = re.sub(
            r"(?is)\bit\s+becomes\s+clear\s+you\s+must\s+(.+?)([.!?]|$)",
            lambda m: f"The situation suggests pressure toward {m.group(1).strip()}, but your next move remains open"
            + (m.group(2) or "."),
            text,
            count=1,
        )
        if t2 != text:
            return t2, "exclusive_path_becomes_clear"
        t2 = re.sub(
            r"(?is)\bthere\s+is\s+no\s+choice\s+but\s+(.+?)([.!?]|$)",
            lambda m: f"One narrow-looking path is {m.group(1).strip()}, if you commit; other costs may still exist"
            + (m.group(2) or "."),
            text,
            count=1,
        )
        if t2 != text:
            return t2, "exclusive_path_no_choice_but"
    if af.get("lead_plot_gravity"):
        t2 = re.sub(
            r"(?i)\bthis\s+is\s+where\s+the\s+story\s+wants\s+you\s+to\s+go\b",
            "This location reads as a strong hook—one option among several",
            text,
            count=1,
        )
        if t2 != text:
            return t2, "lead_plot_gravity_story_wants"
        t2 = re.sub(
            r"(?i)\bthe\s+only\s+real\s+lead\s+is\s+(.+?)([.!?]|$)",
            lambda m: f"One strong lead is {m.group(1).strip()}; other hooks may still compete{m.group(2) or '.'}",
            text,
            count=1,
        )
        if t2 != text:
            return t2, "lead_plot_gravity_only_real_lead"
        t2 = re.sub(
            r"(?i)\bthe\s+story\s+(?:now\s+)?pulls\s+you\s+(?:toward|towards|to)\s+(.+?)([.!?]|$)",
            lambda m: f"A strong hook pulls attention toward {m.group(1).strip()}—treat it as pressure, not the only path"
            + (m.group(2) or "."),
            text,
            count=1,
        )
        if t2 != text:
            return t2, "lead_plot_gravity_story_pulls"
    if af.get("forced_conclusion"):
        t2 = re.sub(
            r"(?is)\bit(?:'s| is)\s+obvious\b.+?\byou\s+must\s+(.+?)([.!?]|$)",
            lambda m: f"It may feel pressing to {m.group(1).strip()}, but your next move is still open"
            + (m.group(2) or "."),
            text,
            count=1,
        )
        if t2 != text:
            return t2, "forced_conclusion_obvious_must"
        t2 = re.sub(
            r"(?i)\bthe\s+answer\s+is\s+obvious\b",
            "Several readings remain plausible; nothing is proven yet",
            text,
            count=1,
        )
        if t2 != text:
            return t2, "forced_conclusion_answer_obvious"
    return None, None


def repair_anti_railroading_narrow(
    text: str,
    validation: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
    player_text: str | None,
    resolution: Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    if validation.get("passed") is True:
        return None, None
    modes: List[str] = []
    t = str(text or "")
    for _ in range(14):
        v = validate_anti_railroading(
            t,
            contract,
            player_text=player_text,
            resolution=resolution if isinstance(resolution, Mapping) else None,
        )
        if v.get("passed") or not v.get("checked"):
            return (t if modes else None, "|".join(modes) if modes else None)
        af = v.get("assertion_flags") if isinstance(v.get("assertion_flags"), Mapping) else {}
        nxt, m = _apply_single_anti_railroading_repair_pass(t, af)
        if not nxt or nxt == t:
            return None, None
        t = nxt
        if m:
            modes.append(m)
    return None, None


def skip_anti_railroading_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    response_type_debug: Dict[str, Any] | None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not isinstance(contract, dict):
        return "no_contract"
    if not contract.get("enabled"):
        return "contract_disabled"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    return None


def apply_anti_railroading_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    response_type_debug: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
) -> tuple[str, Dict[str, Any], List[str]]:
    strict_social_path = strict_social_details is not None
    meta = default_anti_railroading_meta()
    ctr, src = effective_anti_railroading_contract_for_gate(
        gm_output if isinstance(gm_output, dict) else None,
        resolution,
        session,
        str(scene_id or "").strip(),
    )
    meta["anti_railroading_contract_resolution_source"] = src

    skip = skip_anti_railroading_layer(text, ctr, response_type_debug=response_type_debug)
    meta["anti_railroading_skip_reason"] = skip
    if skip:
        return text, meta, []

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

    v0 = validate_anti_railroading(
        text,
        ctr,
        player_text=player_text,
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    meta["anti_railroading_checked"] = bool(v0.get("checked"))
    meta["anti_railroading_ok"] = bool(v0.get("passed"))
    meta["anti_railroading_failure_reasons"] = list(v0.get("failure_reasons") or [])
    af0 = v0.get("assertion_flags")
    meta["anti_railroading_assertion_flags"] = dict(af0) if isinstance(af0, dict) else {}
    meta["anti_railroading_repair_hints"] = anti_railroading_repair_hints(v0)

    if not v0.get("checked") or v0.get("passed"):
        return text, meta, []

    meta["anti_railroading_failed"] = True
    meta["anti_railroading_boundary_semantic_repair_disabled"] = True

    extra: List[str] = []
    if not strict_social_path:
        extra.append("anti_railroading_unsatisfied_at_boundary_no_rewrite")
    meta["anti_railroading_failed"] = True
    meta["anti_railroading_ok"] = False
    return text, meta, extra
