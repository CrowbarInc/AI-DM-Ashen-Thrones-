"""Final-emission tone escalation layer (gate contract resolution + boundary apply).

Validator and contract construction remain in :mod:`game.tone_escalation`.
This module owns gate-layer resolution, metadata merge, pregate audit, and
validate-only boundary application for strict-social / generic emission paths.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping

from game.final_emission_text import _normalize_text
from game.response_policy_contracts import _resolve_response_type_contract
from game.tone_escalation import tone_escalation_repair_hints, validate_tone_escalation
from game.turn_packet import resolve_turn_packet_contract, resolve_turn_packet_for_gate


def is_shipped_full_tone_escalation_contract(candidate: Any) -> bool:
    """True for ``build_tone_escalation_contract`` payloads, not prompt_debug slim summaries."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict):
        return True
    jf = candidate.get("justification_flags")
    if isinstance(jf, dict) and candidate.get("max_allowed_tone") is not None:
        return True
    return False


def coerce_tone_escalation_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if is_shipped_full_tone_escalation_contract(maybe):
        return maybe
    return None


def resolve_tone_escalation_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Prefer the full shipped policy path; never substitute prompt_debug for validation."""
    if not isinstance(gm_output, dict):
        return None
    pkt = resolve_turn_packet_for_gate(gm_output)
    if isinstance(pkt, dict):
        hit = resolve_turn_packet_contract(pkt, "tone_escalation")
        hit = coerce_tone_escalation_contract_dict(hit)
        if hit:
            return hit
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = coerce_tone_escalation_contract_dict(pol.get("tone_escalation"))
        if hit:
            return hit
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = coerce_tone_escalation_contract_dict(pl.get("tone_escalation"))
        if hit:
            return hit
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_tone_escalation_contract_dict(rp.get("tone_escalation"))
            if hit:
                return hit
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = coerce_tone_escalation_contract_dict(md.get("tone_escalation"))
        if hit:
            return hit
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_tone_escalation_contract_dict(rp.get("tone_escalation"))
            if hit:
                return hit
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = coerce_tone_escalation_contract_dict(tr.get("tone_escalation"))
        if hit:
            return hit
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_tone_escalation_contract_dict(rp.get("tone_escalation"))
            if hit:
                return hit
    return None


def default_tone_escalation_disabled_contract() -> Dict[str, Any]:
    return {
        "enabled": False,
        "base_tone": "neutral",
        "max_allowed_tone": "neutral",
        "allow_guarded_refusal": False,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
    }


def default_tone_escalation_contract_strict_fallback() -> Dict[str, Any]:
    """Conservative ceiling for writer pre-gate audit when no full contract is shipped."""
    return {
        "enabled": True,
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": ["fallback_missing_shipped_tone_escalation_contract"],
        "preferred_deescalations": [
            "Default to observational tone; keep interpersonal heat optional.",
        ],
    }


def effective_tone_escalation_contract_for_gate(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> tuple[Dict[str, Any], str]:
    """Contract used for final-gate tone validation + repair (shipped policy only)."""
    shipped = resolve_tone_escalation_contract(gm_output)
    if shipped is not None:
        return shipped, "shipped_response_policy"
    return default_tone_escalation_disabled_contract(), "no_shipped_contract_pipeline_skipped"


def pregate_tone_escalation_audit_contract(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Strict audit for writer pre-gate text only (legacy ``non_hostile_escalation_blocked`` meta)."""
    rtc, _ = _resolve_response_type_contract(
        gm_output if isinstance(gm_output, dict) else None,
        resolution=resolution,
        session=session,
    )
    if rtc and bool(rtc.get("allow_escalation")):
        return default_tone_escalation_disabled_contract()
    return default_tone_escalation_contract_strict_fallback()


def tone_escalation_contract_summary(contract: Mapping[str, Any]) -> Dict[str, Any]:
    reasons = contract.get("justification_reasons")
    jr: List[str] = []
    if isinstance(reasons, list):
        jr = [str(x) for x in reasons[:24] if isinstance(x, str)]
    return {
        "enabled": bool(contract.get("enabled")),
        "base_tone": contract.get("base_tone"),
        "max_allowed_tone": contract.get("max_allowed_tone"),
        "allow_verbal_pressure": bool(contract.get("allow_verbal_pressure")),
        "allow_explicit_threat": bool(contract.get("allow_explicit_threat")),
        "allow_physical_hostility": bool(contract.get("allow_physical_hostility")),
        "allow_combat_initiation": bool(contract.get("allow_combat_initiation")),
        "justification_reasons": jr,
    }


def default_tone_escalation_meta() -> Dict[str, Any]:
    return {
        "tone_escalation_checked": False,
        "tone_escalation_ok": True,
        "tone_escalation_failed": False,
        "tone_escalation_failure_reasons": [],
        "tone_escalation_detected_flags": {},
        "tone_escalation_matched_tone_level": None,
        "tone_escalation_repaired": False,
        "tone_escalation_repair_mode": None,
        "tone_escalation_contract_summary": {},
        "tone_escalation_contract_resolution_source": None,
        "tone_escalation_violation_before_repair": False,
    }


def merge_tone_escalation_meta(meta: Dict[str, Any], te_dbg: Dict[str, Any]) -> None:
    if not te_dbg:
        return
    keys = (
        "tone_escalation_checked",
        "tone_escalation_ok",
        "tone_escalation_failed",
        "tone_escalation_failure_reasons",
        "tone_escalation_detected_flags",
        "tone_escalation_matched_tone_level",
        "tone_escalation_repaired",
        "tone_escalation_repair_mode",
        "tone_escalation_contract_summary",
        "tone_escalation_contract_resolution_source",
        "tone_escalation_violation_before_repair",
    )
    for k in keys:
        if k in te_dbg:
            meta[k] = te_dbg[k]


def tone_escalation_prompt_debug_mirror(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(gm_output, dict):
        return None
    pd = gm_output.get("prompt_debug")
    if isinstance(pd, dict):
        sl = pd.get("tone_escalation")
        if isinstance(sl, dict):
            return sl
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            sl = em.get("tone_escalation_prompt_debug")
            if isinstance(sl, dict):
                return sl
    return None


def merge_tone_escalation_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("tone_escalation_"):
            continue
        flat[k] = v
    mirror = tone_escalation_prompt_debug_mirror(gm_output)
    full = resolve_tone_escalation_contract(gm_output if isinstance(gm_output, dict) else None)
    mirror_box: Dict[str, Any] = {}
    if isinstance(mirror, dict) and mirror:
        mirror_box["prompt_debug_mirror_present"] = True
        if isinstance(full, dict) and is_shipped_full_tone_escalation_contract(full):
            keys = (
                "enabled",
                "base_tone",
                "max_allowed_tone",
                "allow_verbal_pressure",
                "allow_explicit_threat",
                "allow_physical_hostility",
                "allow_combat_initiation",
            )
            mismatch = any(mirror.get(k) != full.get(k) for k in keys)
            mirror_box["prompt_debug_mirror_mismatch_vs_shipped"] = bool(mismatch)

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        if mirror_box:
            base = em.get("tone_escalation")
            if isinstance(base, dict):
                em["tone_escalation"] = {**base, **mirror_box}
            else:
                em["tone_escalation"] = dict(mirror_box)
        for fk, fv in flat.items():
            em[fk] = fv

    if not flat and not mirror_box:
        return

    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        _patch_em(md_out.setdefault("emission_debug", {}))

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _patch_em(md_r.setdefault("emission_debug", {}))

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        _patch_em(eff_resolution["metadata"].setdefault("emission_debug", {}))


def repair_tone_escalation_narrow(
    text: str,
    *,
    contract: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    fails_raw = validation.get("failure_reasons") or []
    fails = [str(x) for x in fails_raw if isinstance(x, str)]
    if not fails:
        return None, None
    _ = tone_escalation_repair_hints(contract=contract, validation=validation)
    t = str(text or "")
    modes: List[str] = []

    def _sub(pat: re.Pattern[str], rep: str, mode: str) -> None:
        nonlocal t
        n, counted = pat.subn(rep, t, count=1)
        if counted:
            t = n
            modes.append(mode)

    if "combat_initiation_not_allowed" in fails:
        _sub(
            re.compile(
                r"\b(?:initiative|rolls?\s+initiative|first\s+strike|combat\s+begins|"
                r"attack\s+of\s+opportunity|readied\s+action|surprise\s+round)\b",
                re.IGNORECASE,
            ),
            "posture tightens, but the moment stays verbal",
            "combat_initiation_soften",
        )
    if "physical_hostility_not_allowed" in fails:
        _sub(
            re.compile(r"\b(?:lunge|lunges|lunging)\s+at\s+you\b", re.IGNORECASE),
            "leans in without closing the last step",
            "physical_lunge_check",
        )
        _sub(
            re.compile(
                r"\b(?:grab|grabs|grabbing|shove|shoves|shoving|slam|slams|slamming|"
                r"strike|strikes|striking|punch|punches|kick|kicks|stab|stabs|cut|cuts|"
                r"slash|slashes|shoot|shoots|fire|fires)\b",
                re.IGNORECASE,
            ),
            "checks the motion before it lands",
            "physical_hostility_soften",
        )
    if "weapon_draw_requires_explicit_threat_allowance" in fails or (
        "explicit_threat_not_allowed" in fails and re.search(r"\b(?:draw|draws|drawing|unsheathe)\b", t, re.IGNORECASE)
    ):
        _sub(
            re.compile(
                r"\b(?:draw|draws|drawing|unsheathe|unsheathes|clear|clears)\s+"
                r"(?:a\s+|the\s+|his\s+|her\s+|their\s+)?(?:blade|sword|knife|dagger|axe|mace|weapon|steel|bow)\b",
                re.IGNORECASE,
            ),
            "keeps a hand near the belt without clearing steel",
            "weapon_draw_soften",
        )
        _sub(
            re.compile(r"\b(?:weapon\s+comes\s+free|steel\s+(?:clears|whispers|hisses))\b", re.IGNORECASE),
            "steel stays sheathed",
            "weapon_free_soften",
        )
    if "explicit_threat_not_allowed" in fails:
        _sub(
            re.compile(r"\b(?:or\s+else|or\s+you(?:'ll| will))\b", re.IGNORECASE),
            "but the line holds anyway",
            "explicit_threat_or_else_soften",
        )
        _sub(
            re.compile(r"\b(?:you(?:'ll| will)\s+regret|last\s+chance|try\s+me)\b", re.IGNORECASE),
            "the warning stays implicit in their posture",
            "explicit_threat_ultimatum_soften",
        )
    if "forced_drama_cue_requires_verbal_pressure_allowance" in fails:
        _sub(
            re.compile(
                r"\b(?:out\s+of\s+nowhere|without\s+warning|suddenly,?\s+everything|"
                r"chaos\s+erupts|all\s+hell\s+breaks\s+loose)\b",
                re.IGNORECASE,
            ),
            "attention snaps toward you as patrol eyes clock the exchange",
            "forced_drama_grounded",
        )
        _sub(
            re.compile(r"\b(?:a\s+shadowy\s+figure|the\s+stranger\s+attacks)\b", re.IGNORECASE),
            "a passerby stiffens, watching",
            "forced_drama_stranger_soften",
        )
    if "verbal_pressure_not_allowed" in fails:
        _sub(
            re.compile(r"\b(?:back\s+off|lay\s+off|drop\s+it|leave\s+it)\b", re.IGNORECASE),
            "lets the topic die without a sharp edge",
            "verbal_pressure_soften",
        )
        _sub(
            re.compile(r"\b(?:watch\s+your(?:self)?|careful\s+how)\b", re.IGNORECASE),
            "keeps their tone flat",
            "verbal_pressure_watch_soften",
        )
    if "guarded_tone_not_allowed" in fails:
        _sub(
            re.compile(r"\b(?:refuse|refuses|refusing)\b", re.IGNORECASE),
            "does not answer directly",
            "guarded_refusal_neutralize",
        )

    if modes:
        return _normalize_text(t), "|".join(modes)
    return None, None


def skip_tone_escalation_layer(response_type_debug: Dict[str, Any] | None) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    return None


def apply_tone_escalation_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    response_type_debug: Dict[str, Any],
) -> tuple[str, Dict[str, Any], List[str]]:
    meta = default_tone_escalation_meta()
    skip = skip_tone_escalation_layer(response_type_debug)
    if skip:
        meta["tone_escalation_contract_summary"] = {}
        return text, meta, []

    ctr, src = effective_tone_escalation_contract_for_gate(
        gm_output if isinstance(gm_output, dict) else None,
        resolution=resolution,
        session=session,
    )
    meta["tone_escalation_contract_resolution_source"] = src
    meta["tone_escalation_contract_summary"] = tone_escalation_contract_summary(ctr)

    if not ctr.get("enabled"):
        return text, meta, []

    v0 = validate_tone_escalation(text, contract=ctr)
    meta["tone_escalation_checked"] = bool(v0.get("checked"))
    meta["tone_escalation_ok"] = bool(v0.get("ok"))
    dflags = v0.get("detected_assertion_flags")
    meta["tone_escalation_detected_flags"] = dict(dflags) if isinstance(dflags, dict) else {}
    meta["tone_escalation_matched_tone_level"] = v0.get("matched_tone_level")
    fails0 = list(v0.get("failure_reasons") or [])
    meta["tone_escalation_failure_reasons"] = fails0

    if not v0.get("checked") or v0.get("ok"):
        return text, meta, []

    meta["tone_escalation_violation_before_repair"] = True
    meta["tone_escalation_boundary_semantic_repair_disabled"] = True
    meta["tone_escalation_failed"] = True
    return text, meta, ["tone_escalation_unsatisfied_at_boundary_no_rewrite"]


def flag_non_hostile_escalation_from_writer_pregate(
    pre_gate_text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
) -> None:
    """If the writer's pre-gate text overshoots the audit contract, set legacy debug flag."""
    ctr = pregate_tone_escalation_audit_contract(
        gm_output,
        resolution=resolution,
        session=session,
    )
    if not ctr.get("enabled"):
        return
    pv = validate_tone_escalation(pre_gate_text, contract=ctr)
    if pv.get("checked") and not pv.get("ok"):
        response_type_debug["non_hostile_escalation_blocked"] = True
