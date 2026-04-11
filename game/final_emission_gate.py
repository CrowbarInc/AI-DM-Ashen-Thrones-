"""Final player-facing emission: orchestration, policy layers, and compatibility imports.

**Orchestration home:** :func:`apply_final_emission_gate` sequences sanitizer integration,
strict-social coordination (via :mod:`game.social_exchange_emission`), shipped contracts
(tone, narrative authority, anti-railroading, context separation, scene anchor, speaker
selection), logging, and metadata merges.

**Not the ownership home for:** deterministic validators (:mod:`game.final_emission_validators`),
repair/layer wiring (:mod:`game.final_emission_repairs`), shared text/normalization patterns
(:mod:`game.final_emission_text`), or ``response_type`` contract resolution
(:mod:`game.response_policy_contracts`). Those modules are imported here; some private
symbols remain importable from this package for historical tests (prefer importing from
their real module for new code).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from game.exploration import NPC_PURSUIT_CONTACT_SESSION_KEY
from game.interaction_context import inspect as inspect_interaction_context
from game.narrative_authority import (
    narrative_authority_prefers_roll_prompt,
    narrative_authority_repair_hints,
    validate_narrative_authority,
    _BRANCH_FRAMING_RE,
    _HIDDEN_FACT_CERTAINTY_RE,
    _INTENT_CERTAINTY_RE,
    _ROLL_PROMPT_RE,
    _mask_dialogue_spans,
    _outcome_assertion_hits,
    _player_asks_intent_or_read,
    _sentence_has_hedge,
    _split_sentences,
    _STRONG_OUTCOME_ASSERTION_RE,
)
from game.narration_visibility import (
    build_narration_visibility_contract,
    validate_player_facing_first_mentions,
    validate_player_facing_referential_clarity,
    validate_player_facing_visibility,
    _split_visibility_sentences,
)
from game.output_sanitizer import sanitize_player_facing_output
from game.social import (
    SOCIAL_KINDS,
    SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS,
    neutral_reply_speaker_grounding_bridge_line,
)
from game.social_exchange_emission import (
    _active_interlocutor_matches_resolution_social_npc,
    _has_explicit_interruption_shape,
    build_final_strict_social_response,
    effective_strict_social_resolution_for_emission,
    interruption_cue_present_in_text,
    is_route_illegal_global_or_sanitizer_fallback_text,
    log_final_emission_decision,
    log_final_emission_trace,
    merged_player_prompt_for_gate,
    minimal_social_emergency_fallback_line,
    replacement_is_route_legal_social,
    strict_social_emission_will_apply,
    strict_social_ownership_terminal_fallback,
    strict_social_suppress_non_native_coercion_for_narration_beat,
    _npc_display_name_for_emission,
    _speaker_label,
)
from game.storage import get_scene_runtime
from game.anti_reset_emission_guard import (
    anti_reset_suppresses_intro_style_fallbacks,
    local_exchange_continuation_fallback_line,
    should_replace_candidate_intro_fallback,
)
from game.leads import get_lead, normalize_lead
from game.prompt_context import canonical_interaction_target_npc_id
from game.anti_railroading import anti_railroading_repair_hints, build_anti_railroading_contract, validate_anti_railroading
from game.context_separation import context_separation_repair_hints, validate_context_separation
from game.player_facing_narration_purity import (
    minimal_repair_player_facing_narration_purity,
    player_facing_narration_purity_repair_hints,
    validate_player_facing_narration_purity,
)
from game.scene_state_anchoring import validate_scene_state_anchoring
from game.tone_escalation import tone_escalation_repair_hints, validate_tone_escalation

from game.fallback_provenance_debug import (
    realign_fallback_provenance_selector_to_current_text,
    METADATA_KEY,
    fingerprint_player_facing,
    record_final_emission_gate_entry,
    record_final_emission_gate_exit,
)
from game.final_emission_text import (
    _ACTION_RESULT_PATTERNS,
    _AGENCY_SUBSTITUTE_PATTERNS,
    _ANSWER_DIRECT_PATTERNS,
    _ANSWER_FILLER_PATTERNS,
    _RESPONSE_TYPE_VALUES,
    _capitalize_sentence_fragment,
    _global_narrative_fallback_stock_line,
    _has_terminal_punctuation,
    _normalize_terminal_punctuation,
    _normalize_text,
    _normalize_text_preserve_paragraphs,
    _sanitize_output_text,
)
from game.interaction_continuity import repair_interaction_continuity, validate_interaction_continuity
from game.response_policy_contracts import (
    _last_player_input,
    _resolve_response_type_contract,
    _valid_response_type_contract,
    resolve_interaction_continuity_contract,
)


from game.final_emission_repairs import (
    _apply_answer_completeness_layer,
    _apply_fallback_behavior_layer,
    _apply_response_delta_layer,
    _apply_social_response_structure_layer,
    _default_fallback_behavior_meta,
    _default_response_delta_meta,
    _default_social_response_structure_meta,
    _gm_probe_for_answer_pressure_contracts,
    _merge_answer_completeness_meta,
    _merge_fallback_behavior_meta,
    _merge_response_delta_meta,
    _merge_social_response_structure_meta,
    _minimal_action_outcome_contract_repair,
    _minimal_answer_contract_repair,
    _skip_answer_completeness_layer,
    _skip_response_delta_layer,
    _social_fallback_resolution,
    apply_spoken_state_refinement_cash_out,
    _strict_social_answer_pressure_ac_contract_active,
    _strict_social_answer_pressure_rd_contract_active,
)
from game.final_emission_validators import (
    _content_tokens,
    _split_sentences_answer_complete,
    candidate_satisfies_action_outcome_contract,
    candidate_satisfies_answer_contract,
    candidate_satisfies_dialogue_contract,
    inspect_answer_completeness_failure,
    inspect_response_delta_failure,
    validate_answer_completeness,
    validate_response_delta,
)

# --- Policy layers & helpers (large clusters live here; validators/repairs are extracted) ---


def _default_response_type_debug(contract: Dict[str, Any] | None, source: str | None) -> Dict[str, Any]:
    return {
        "response_type_required": str((contract or {}).get("required_response_type") or "") or None,
        "response_type_contract_source": source,
        "response_type_candidate_ok": None if not contract else True,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
    }


def _merge_response_type_meta(meta: Dict[str, Any], debug: Dict[str, Any]) -> None:
    meta.update(
        {
            "response_type_required": debug.get("response_type_required"),
            "response_type_contract_source": debug.get("response_type_contract_source"),
            "response_type_candidate_ok": debug.get("response_type_candidate_ok"),
            "response_type_repair_used": debug.get("response_type_repair_used"),
            "response_type_repair_kind": debug.get("response_type_repair_kind"),
            "response_type_rejection_reasons": list(debug.get("response_type_rejection_reasons") or []),
            "non_hostile_escalation_blocked": bool(debug.get("non_hostile_escalation_blocked")),
        }
    )


def _response_type_decision_payload(debug: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "response_type_required": debug.get("response_type_required"),
        "response_type_contract_source": debug.get("response_type_contract_source"),
        "response_type_candidate_ok": debug.get("response_type_candidate_ok"),
        "response_type_repair_used": debug.get("response_type_repair_used"),
        "response_type_repair_kind": debug.get("response_type_repair_kind"),
        "response_type_rejection_reasons": list(debug.get("response_type_rejection_reasons") or []),
        "non_hostile_escalation_blocked": bool(debug.get("non_hostile_escalation_blocked")),
    }


def _default_narration_constraint_debug() -> Dict[str, Any]:
    """Compact, sanitized narration-constraint diagnostics; not a full trace log."""
    return {
        "response_type": {
            "required": None,
            "contract_source": None,
            "candidate_ok": None,
            "repair_used": False,
            "repair_kind": None,
        },
        "visibility": {
            "contract_present": False,
            "decision_mode": None,
            "visible_entity_count": None,
            "withheld_fact_count": None,
            "reason_codes": [],
        },
        "speaker_selection": {
            "speaker_id": None,
            "speaker_name": None,
            "selection_source": None,
            "reason_code": None,
            "binding_confident": None,
        },
    }


def _narration_constraint_small_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    clean = value.strip()
    if not clean or len(clean) > 64 or any(ch in clean for ch in "\r\n\t"):
        return None
    return clean


_NARRATION_CONSTRAINT_CODE_RE = re.compile(r"^[A-Za-z0-9_.:/-]+$")


def _narration_constraint_small_code(value: Any) -> str | None:
    clean = _narration_constraint_small_str(value)
    if clean is None or _NARRATION_CONSTRAINT_CODE_RE.fullmatch(clean) is None:
        return None
    return clean


def _narration_constraint_small_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _narration_constraint_reason_codes(*sources: Any, limit: int = 5) -> List[str]:
    """Keep only small stable codes; never surface raw hidden text or prompt fragments."""
    out: List[str] = []

    def _push(raw: Any) -> None:
        if len(out) >= limit:
            return
        if isinstance(raw, str):
            clean = _narration_constraint_small_code(raw)
            if clean and clean not in out:
                out.append(clean)
            return
        if isinstance(raw, dict):
            _push(raw.get("reason_code"))
            _push(raw.get("reason_codes"))
            kind = raw.get("kind")
            if isinstance(kind, str):
                _push(kind)
            return
        if isinstance(raw, (list, tuple)):
            for item in raw:
                if len(out) >= limit:
                    break
                _push(item)

    for source in sources:
        _push(source)
        if len(out) >= limit:
            break
    return out[:limit]


def _narration_constraint_visibility_mode(
    visibility_meta: Mapping[str, Any] | None,
    visibility_validation: Mapping[str, Any] | None,
) -> str | None:
    vm = visibility_meta if isinstance(visibility_meta, dict) else {}
    vv = visibility_validation if isinstance(visibility_validation, dict) else {}
    if vm.get("visibility_replacement_applied") is True:
        return "replaced"
    if vm.get("visibility_continuity_lead_exemption") is True:
        return "continuity_lead_exemption"
    if vm.get("visibility_validation_passed") is True:
        return "validated"
    if vm.get("visibility_validation_passed") is False:
        return "validation_failed"
    if isinstance(vv.get("ok"), bool):
        return "validated" if vv.get("ok") is True else "validation_failed"
    return None


def _narration_constraint_binding_confident(
    speaker_selection_contract: Mapping[str, Any] | None,
    speaker_contract_enforcement: Mapping[str, Any] | None,
    speaker_binding_bridge: Mapping[str, Any] | None,
) -> bool | None:
    ssc = speaker_selection_contract if isinstance(speaker_selection_contract, dict) else {}
    sce = speaker_contract_enforcement if isinstance(speaker_contract_enforcement, dict) else {}
    bridge = speaker_binding_bridge if isinstance(speaker_binding_bridge, dict) else {}
    if bridge.get("malformed_attribution_detected") is True:
        return False

    candidate = sce.get("post_validation")
    if not isinstance(candidate, dict):
        candidate = sce.get("validation")
    details = candidate.get("details") if isinstance(candidate, dict) else {}
    signature = details.get("signature") if isinstance(details, dict) else {}
    confidence = _narration_constraint_small_code(signature.get("confidence")) if isinstance(signature, dict) else None
    if confidence == "high":
        return True
    if confidence == "low":
        return False
    if ssc.get("continuity_locked") is True:
        return True
    if ssc.get("speaker_switch_allowed") is False and _narration_constraint_small_str(ssc.get("primary_speaker_id")):
        return True
    return None


def _narration_constraint_speaker_reason_code(
    speaker_selection_contract: Mapping[str, Any] | None,
    speaker_contract_enforcement: Mapping[str, Any] | None,
    speaker_binding_bridge: Mapping[str, Any] | None,
) -> str | None:
    ssc = speaker_selection_contract if isinstance(speaker_selection_contract, dict) else {}
    sce = speaker_contract_enforcement if isinstance(speaker_contract_enforcement, dict) else {}
    bridge = speaker_binding_bridge if isinstance(speaker_binding_bridge, dict) else {}
    candidate = sce.get("post_validation")
    if not isinstance(candidate, dict):
        candidate = sce.get("validation")
    ssc_debug = ssc.get("debug") if isinstance(ssc.get("debug"), dict) else {}
    grounded = (
        _narration_constraint_small_code(sce.get("final_reason_code"))
        or _narration_constraint_small_code(candidate.get("reason_code") if isinstance(candidate, dict) else None)
        or _narration_constraint_small_code(bridge.get("speaker_reason_code"))
        or _narration_constraint_small_code(ssc_debug.get("grounding_reason_code"))
        or _narration_constraint_small_code(ssc.get("continuity_lock_reason"))
        or _narration_constraint_small_code(ssc.get("speaker_switch_reason"))
    )
    if grounded:
        return grounded

    selection_source = _narration_constraint_small_code(ssc.get("primary_speaker_source")) or _narration_constraint_small_code(
        ssc_debug.get("authoritative_source")
    )
    if selection_source in {"explicit_target", "declared_action", "spoken_vocative", "vocative"}:
        return "speaker_from_explicit_target"
    if selection_source == "continuity":
        return "speaker_from_continuity"
    if not _narration_constraint_small_str(ssc.get("primary_speaker_id")):
        return "speaker_unresolved"
    return None


def _build_narration_constraint_debug(
    *,
    response_type_debug: Mapping[str, Any] | None = None,
    response_type_contract: Mapping[str, Any] | None = None,
    response_type_contract_source: str | None = None,
    narration_visibility: Mapping[str, Any] | None = None,
    visibility_meta: Mapping[str, Any] | None = None,
    visibility_validation: Mapping[str, Any] | None = None,
    speaker_selection_contract: Mapping[str, Any] | None = None,
    speaker_contract_enforcement: Mapping[str, Any] | None = None,
    speaker_binding_bridge: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a lightweight diagnostic surface; keep it compact, stable, and sanitized."""
    payload = _default_narration_constraint_debug()

    rt_dbg = response_type_debug if isinstance(response_type_debug, dict) else {}
    rt_contract = response_type_contract if isinstance(response_type_contract, dict) else {}
    vis_contract = narration_visibility if isinstance(narration_visibility, dict) else {}
    vis_meta = visibility_meta if isinstance(visibility_meta, dict) else {}
    vis_validation_map = visibility_validation if isinstance(visibility_validation, dict) else {}
    ssc = speaker_selection_contract if isinstance(speaker_selection_contract, dict) else {}
    sce = speaker_contract_enforcement if isinstance(speaker_contract_enforcement, dict) else {}
    bridge = speaker_binding_bridge if isinstance(speaker_binding_bridge, dict) else {}

    rt_out = payload["response_type"]
    rt_out["required"] = _narration_constraint_small_code(rt_dbg.get("response_type_required")) or _narration_constraint_small_code(
        rt_contract.get("required_response_type")
    )
    rt_out["contract_source"] = _narration_constraint_small_code(rt_dbg.get("response_type_contract_source")) or _narration_constraint_small_code(
        response_type_contract_source
    )
    candidate_ok = rt_dbg.get("response_type_candidate_ok")
    rt_out["candidate_ok"] = candidate_ok if isinstance(candidate_ok, bool) else None
    rt_out["repair_used"] = bool(rt_dbg.get("response_type_repair_used"))
    rt_out["repair_kind"] = _narration_constraint_small_code(rt_dbg.get("response_type_repair_kind"))

    vis_out = payload["visibility"]
    vis_out["contract_present"] = bool(vis_contract)
    vis_out["decision_mode"] = _narration_constraint_visibility_mode(vis_meta, vis_validation_map)
    vis_out["visible_entity_count"] = (
        len(vis_contract.get("visible_entity_ids"))
        if isinstance(vis_contract.get("visible_entity_ids"), list)
        else None
    )
    vis_out["withheld_fact_count"] = (
        len(vis_contract.get("hidden_fact_strings"))
        if isinstance(vis_contract.get("hidden_fact_strings"), list)
        else None
    )
    vis_reasons: List[str] = []
    if vis_meta.get("visibility_continuity_lead_exemption") is True:
        vis_reasons.append("continuity_lead_exemption")
    vis_reasons.extend(
        _narration_constraint_reason_codes(
            vis_meta.get("visibility_violation_kinds"),
            vis_validation_map.get("reason_codes"),
            vis_validation_map.get("violations"),
            limit=5,
        )
    )
    vis_out["reason_codes"] = _narration_constraint_reason_codes(vis_reasons, limit=5)

    sp_out = payload["speaker_selection"]
    candidate = sce.get("post_validation")
    if not isinstance(candidate, dict):
        candidate = sce.get("validation")
    sp_out["speaker_id"] = _narration_constraint_small_str(ssc.get("primary_speaker_id")) or _narration_constraint_small_str(
        candidate.get("canonical_speaker_id") if isinstance(candidate, dict) else None
    )
    sp_out["speaker_name"] = _narration_constraint_small_str(ssc.get("primary_speaker_name")) or _narration_constraint_small_str(
        candidate.get("canonical_speaker_name") if isinstance(candidate, dict) else None
    )
    ssc_debug = ssc.get("debug") if isinstance(ssc.get("debug"), dict) else {}
    sp_out["selection_source"] = _narration_constraint_small_code(ssc.get("primary_speaker_source")) or _narration_constraint_small_code(
        ssc_debug.get("authoritative_source")
    )
    sp_out["reason_code"] = _narration_constraint_speaker_reason_code(ssc, sce, bridge)
    sp_out["binding_confident"] = _narration_constraint_binding_confident(ssc, sce, bridge)

    return payload


def _merge_narration_constraint_debug_meta(
    metadata: Dict[str, Any],
    debug_payload: Mapping[str, Any] | None,
) -> None:
    """Merge the compact narration diagnostics without disturbing unrelated metadata."""
    if not isinstance(metadata, dict):
        return
    if not isinstance(debug_payload, dict):
        debug_payload = {}

    emission_debug = metadata.setdefault("emission_debug", {})
    if not isinstance(emission_debug, dict):
        return

    # Keep this surface stable and sanitized; it is a summary view, not a full trace.
    merged = _default_narration_constraint_debug()
    existing = emission_debug.get("narration_constraint_debug")
    existing_map = existing if isinstance(existing, dict) else {}
    for section_name, section_default in merged.items():
        existing_section = existing_map.get(section_name)
        payload_section = debug_payload.get(section_name)
        section = dict(section_default)
        if isinstance(existing_section, dict):
            section.update(existing_section)
        if isinstance(payload_section, dict):
            section.update(payload_section)
        merged[section_name] = section
    for extra_key, extra_value in existing_map.items():
        if extra_key not in merged:
            merged[extra_key] = extra_value
    for extra_key, extra_value in debug_payload.items():
        if extra_key not in merged:
            merged[extra_key] = extra_value
    emission_debug["narration_constraint_debug"] = merged


def _resolve_narration_constraint_debug_visibility_contract(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    try:
        contract = build_narration_visibility_contract(
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
    except Exception:
        return {}
    return contract if isinstance(contract, dict) else {}


def _current_speaker_binding_bridge(out: Dict[str, Any]) -> Dict[str, Any]:
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    em = md.get("emission_debug") if isinstance(md.get("emission_debug"), dict) else {}
    bridge = em.get("interaction_continuity_speaker_binding_bridge")
    return bridge if isinstance(bridge, dict) else {}


def _merge_narration_constraint_debug_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    response_type_debug: Mapping[str, Any] | None,
    speaker_contract_enforcement: Mapping[str, Any] | None = None,
) -> None:
    md_out = out.setdefault("metadata", {})
    if not isinstance(md_out, dict):
        return

    visibility_meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    speaker_selection_contract = get_speaker_selection_contract(
        eff_resolution if isinstance(eff_resolution, dict) else resolution,
        metadata=md_out,
        trace=out.get("trace") if isinstance(out.get("trace"), dict) else None,
    )
    payload = _build_narration_constraint_debug(
        response_type_debug=response_type_debug,
        narration_visibility=_resolve_narration_constraint_debug_visibility_contract(
            session=session,
            scene=scene,
            world=world,
        ),
        visibility_meta=visibility_meta,
        speaker_selection_contract=speaker_selection_contract,
        speaker_contract_enforcement=speaker_contract_enforcement,
        speaker_binding_bridge=_current_speaker_binding_bridge(out),
    )
    _merge_narration_constraint_debug_meta(md_out, payload)

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _merge_narration_constraint_debug_meta(md_r, payload)

    if eff_resolution is not None and eff_resolution is not resolution:
        md_eff = eff_resolution.setdefault("metadata", {})
        if isinstance(md_eff, dict):
            _merge_narration_constraint_debug_meta(md_eff, payload)


# --- Tone escalation (response_policy.tone_escalation shipped contract) -----------------------


def _is_shipped_full_tone_escalation_contract(candidate: Any) -> bool:
    """True for ``build_tone_escalation_contract`` payloads, not prompt_debug slim summaries."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict):
        return True
    jf = candidate.get("justification_flags")
    if isinstance(jf, dict) and candidate.get("max_allowed_tone") is not None:
        return True
    return False


def _coerce_tone_escalation_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if _is_shipped_full_tone_escalation_contract(maybe):
        return maybe
    return None


def _resolve_tone_escalation_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Prefer the full shipped policy path; never substitute prompt_debug for validation."""
    if not isinstance(gm_output, dict):
        return None
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = _coerce_tone_escalation_contract_dict(pol.get("tone_escalation"))
        if hit:
            return hit
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = _coerce_tone_escalation_contract_dict(pl.get("tone_escalation"))
        if hit:
            return hit
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_tone_escalation_contract_dict(rp.get("tone_escalation"))
            if hit:
                return hit
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = _coerce_tone_escalation_contract_dict(md.get("tone_escalation"))
        if hit:
            return hit
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_tone_escalation_contract_dict(rp.get("tone_escalation"))
            if hit:
                return hit
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = _coerce_tone_escalation_contract_dict(tr.get("tone_escalation"))
        if hit:
            return hit
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_tone_escalation_contract_dict(rp.get("tone_escalation"))
            if hit:
                return hit
    return None


def _default_tone_escalation_disabled_contract() -> Dict[str, Any]:
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


def _default_tone_escalation_contract_strict_fallback() -> Dict[str, Any]:
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


def _effective_tone_escalation_contract_for_gate(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> tuple[Dict[str, Any], str]:
    """Contract used for final-gate tone validation + repair (shipped policy only)."""
    shipped = _resolve_tone_escalation_contract(gm_output)
    if shipped is not None:
        return shipped, "shipped_response_policy"
    return _default_tone_escalation_disabled_contract(), "no_shipped_contract_pipeline_skipped"


def _pregate_tone_escalation_audit_contract(
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
        return _default_tone_escalation_disabled_contract()
    return _default_tone_escalation_contract_strict_fallback()


def _tone_escalation_contract_summary(contract: Mapping[str, Any]) -> Dict[str, Any]:
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


def _default_tone_escalation_meta() -> Dict[str, Any]:
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


def _merge_tone_escalation_meta(meta: Dict[str, Any], te_dbg: Dict[str, Any]) -> None:
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


def _tone_escalation_prompt_debug_mirror(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
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


def _merge_tone_escalation_into_emission_debug(
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
    mirror = _tone_escalation_prompt_debug_mirror(gm_output)
    full = _resolve_tone_escalation_contract(gm_output if isinstance(gm_output, dict) else None)
    mirror_box: Dict[str, Any] = {}
    if isinstance(mirror, dict) and mirror:
        mirror_box["prompt_debug_mirror_present"] = True
        if isinstance(full, dict) and _is_shipped_full_tone_escalation_contract(full):
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


def _repair_tone_escalation_narrow(
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


def _skip_tone_escalation_layer(response_type_debug: Dict[str, Any] | None) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    return None


def _apply_tone_escalation_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    response_type_debug: Dict[str, Any],
) -> tuple[str, Dict[str, Any], List[str]]:
    meta = _default_tone_escalation_meta()
    skip = _skip_tone_escalation_layer(response_type_debug)
    if skip:
        meta["tone_escalation_contract_summary"] = {}
        return text, meta, []

    ctr, src = _effective_tone_escalation_contract_for_gate(
        gm_output if isinstance(gm_output, dict) else None,
        resolution=resolution,
        session=session,
    )
    meta["tone_escalation_contract_resolution_source"] = src
    meta["tone_escalation_contract_summary"] = _tone_escalation_contract_summary(ctr)

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
    repaired, mode = _repair_tone_escalation_narrow(text, contract=ctr, validation=v0)
    if repaired:
        v1 = validate_tone_escalation(repaired, contract=ctr)
        meta["tone_escalation_checked"] = bool(v1.get("checked"))
        meta["tone_escalation_ok"] = bool(v1.get("ok"))
        d1 = v1.get("detected_assertion_flags")
        meta["tone_escalation_detected_flags"] = dict(d1) if isinstance(d1, dict) else {}
        meta["tone_escalation_matched_tone_level"] = v1.get("matched_tone_level")
        meta["tone_escalation_failure_reasons"] = list(v1.get("failure_reasons") or [])
        if v1.get("ok"):
            meta["tone_escalation_repaired"] = True
            meta["tone_escalation_repair_mode"] = mode
            meta["tone_escalation_failed"] = False
            return repaired, meta, []

    meta["tone_escalation_failed"] = True
    return text, meta, ["tone_escalation_unsatisfied_after_repair"]


def _flag_non_hostile_escalation_from_writer_pregate(
    pre_gate_text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
) -> None:
    """If the writer's pre-gate text overshoots the audit contract, set legacy debug flag."""
    ctr = _pregate_tone_escalation_audit_contract(
        gm_output,
        resolution=resolution,
        session=session,
    )
    if not ctr.get("enabled"):
        return
    pv = validate_tone_escalation(pre_gate_text, contract=ctr)
    if pv.get("checked") and not pv.get("ok"):
        response_type_debug["non_hostile_escalation_blocked"] = True


# --- Narrative authority (response_policy.narrative_authority shipped contract) -----------------


def _is_shipped_full_narrative_authority_contract(candidate: Any) -> bool:
    """True for ``build_narrative_authority_contract`` payloads, not prompt_debug slim summaries."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict):
        return True
    if isinstance(candidate.get("debug_flags"), dict) and isinstance(candidate.get("allowed_deferrals"), list):
        return True
    return False


def _coerce_narrative_authority_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if _is_shipped_full_narrative_authority_contract(maybe):
        return maybe
    return None


def _resolve_narrative_authority_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Prefer the full narration payload path; never substitute prompt_debug for validation."""
    if not isinstance(gm_output, dict):
        return None
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = _coerce_narrative_authority_contract_dict(pol.get("narrative_authority"))
        if hit:
            return hit
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = _coerce_narrative_authority_contract_dict(pl.get("narrative_authority"))
        if hit:
            return hit
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = _coerce_narrative_authority_contract_dict(md.get("narrative_authority"))
        if hit:
            return hit
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = _coerce_narrative_authority_contract_dict(tr.get("narrative_authority"))
        if hit:
            return hit
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    return None


def _narrative_authority_prompt_debug_mirror(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Compact upstream summary only (not valid as a shipped contract)."""
    if not isinstance(gm_output, dict):
        return None
    pd = gm_output.get("prompt_debug")
    if isinstance(pd, dict):
        sl = pd.get("narrative_authority")
        if isinstance(sl, dict):
            return sl
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            sl = em.get("narrative_authority_prompt_debug")
            if isinstance(sl, dict):
                return sl
    return None


def _narrative_authority_policy_disabled(gm_output: Dict[str, Any] | None) -> bool:
    if not isinstance(gm_output, dict):
        return False
    pol = gm_output.get("response_policy")
    if not isinstance(pol, dict):
        return False
    if pol.get("forbid_unjustified_narrative_authority") is False:
        return True
    return False


def _default_narrative_authority_meta() -> Dict[str, Any]:
    return {
        "narrative_authority_checked": False,
        "narrative_authority_failed": False,
        "narrative_authority_failure_reasons": [],
        "narrative_authority_repaired": False,
        "narrative_authority_repair_mode": None,
        "narrative_authority_skip_reason": None,
        "narrative_authority_deferral_mode": None,
        "narrative_authority_assertion_flags": {},
    }


def _merge_narrative_authority_meta(meta: Dict[str, Any], na_dbg: Dict[str, Any]) -> None:
    if not na_dbg:
        return
    keys = (
        "narrative_authority_checked",
        "narrative_authority_failed",
        "narrative_authority_failure_reasons",
        "narrative_authority_repaired",
        "narrative_authority_repair_mode",
        "narrative_authority_skip_reason",
        "narrative_authority_deferral_mode",
        "narrative_authority_assertion_flags",
    )
    for k in keys:
        if k in na_dbg:
            meta[k] = na_dbg[k]


def _merge_narrative_authority_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("narrative_authority_"):
            continue
        flat[k] = v
    mirror = _narrative_authority_prompt_debug_mirror(gm_output)
    full = _resolve_narrative_authority_contract(gm_output)
    mirror_box: Dict[str, Any] = {}
    if isinstance(mirror, dict) and mirror:
        mirror_box["prompt_debug_mirror_present"] = True
        if isinstance(full, dict) and _is_shipped_full_narrative_authority_contract(full):
            keys = (
                "enabled",
                "authoritative_outcome_available",
                "forbid_unresolved_outcome_assertions",
                "forbid_hidden_fact_assertions",
                "forbid_npc_intent_assertions_without_basis",
            )
            mismatch = any(mirror.get(k) != full.get(k) for k in keys)
            mirror_box["prompt_debug_mirror_mismatch_vs_shipped"] = bool(mismatch)

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        if mirror_box:
            base = em.get("narrative_authority")
            if isinstance(base, dict):
                em["narrative_authority"] = {**base, **mirror_box}
            else:
                em["narrative_authority"] = dict(mirror_box)
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


def _skip_narrative_authority_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if _narrative_authority_policy_disabled(gm_output):
        return "narrative_authority_policy_disabled"
    if not isinstance(contract, dict):
        return "no_full_contract"
    if not contract.get("enabled"):
        return "contract_disabled"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    return None


def _na_outcome_sentence_span(raw: str) -> tuple[int, int, str] | None:
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        if not str(msent).strip():
            continue
        if _sentence_has_hedge(sent):
            continue
        if _outcome_assertion_hits(sent, msent):
            return start, end, sent
    return None


def _na_hidden_fact_sentence_span(raw: str) -> tuple[int, int, str] | None:
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        if _sentence_has_hedge(sent):
            continue
        if _HIDDEN_FACT_CERTAINTY_RE.search(msent.lower()):
            return start, end, sent
    return None


def _na_intent_sentence_span(
    raw: str,
    *,
    player_text: str | None,
    resolution: Dict[str, Any] | None,
) -> tuple[int, int, str] | None:
    res_prompt = (
        str((resolution or {}).get("prompt") or "").strip() if isinstance(resolution, dict) else ""
    )
    player_seeks = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(res_prompt)
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        low = msent.lower()
        if player_seeks and _sentence_has_hedge(sent):
            continue
        if player_seeks and _ROLL_PROMPT_RE.search(low):
            continue
        if _INTENT_CERTAINTY_RE.search(low):
            if player_seeks and (_sentence_has_hedge(sent) or _ROLL_PROMPT_RE.search(low)):
                continue
            return start, end, sent
    return None


def _na_replace_sentence(raw: str, start: int, end: int, replacement: str) -> str:
    rep = str(replacement or "").strip()
    before = raw[:start].rstrip()
    after = raw[end:].lstrip()
    parts = [p for p in (before, rep, after) if p]
    return _normalize_text(" ".join(parts))


def _repair_narrative_authority_narrow(
    text: str,
    validation: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None,
    player_text: str | None,
) -> tuple[str | None, str | None]:
    flags = validation.get("assertion_flags") if isinstance(validation.get("assertion_flags"), dict) else {}
    if not flags or validation.get("passed") is True:
        return None, None

    narrative_authority_repair_hints(validation)

    repaired = str(text or "")
    modes: List[str] = []

    if flags.get("invented_outcome"):
        low_full = repaired.lower()
        if narrative_authority_prefers_roll_prompt(player_text, resolution) and not _ROLL_PROMPT_RE.search(
            low_full
        ):
            repaired = _normalize_text(
                repaired.rstrip()
                + " Make a skill check to see how that resolves before you treat the outcome as settled."
            )
            modes.append("invented_outcome_roll_prompt")
        elif _BRANCH_FRAMING_RE.search(low_full):
            span = _na_outcome_sentence_span(repaired)
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "Until the check resolves, leave that beat open rather than stating a result.",
                )
                modes.append("invented_outcome_branch_soften")
        else:
            span = _na_outcome_sentence_span(repaired)
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "You attempt it, but the outcome is not settled yet.",
                )
                modes.append("invented_outcome_uncertainty_replace")
            else:
                strong = _STRONG_OUTCOME_ASSERTION_RE.search(repaired)
                if strong:
                    repaired = (
                        repaired[: strong.start()]
                        + "You attempt it, but the outcome is not settled yet."
                        + repaired[strong.end() :]
                    )
                    repaired = _normalize_text(repaired)
                    modes.append("invented_outcome_span_soften")

    if flags.get("invented_hidden_fact"):
        span = _na_hidden_fact_sentence_span(repaired)
        if span:
            start, end, _sent = span
            repaired = _na_replace_sentence(
                repaired,
                start,
                end,
                "From what you can see, you can't pin the hidden cause down yet.",
            )
            modes.append("invented_hidden_fact_downgrade")

    if flags.get("invented_intent"):
        seek = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(
            str((resolution or {}).get("prompt") or "").strip() if isinstance(resolution, Mapping) else ""
        )
        prefers = narrative_authority_prefers_roll_prompt(player_text, resolution)
        low_full = repaired.lower()
        if seek and prefers and not _ROLL_PROMPT_RE.search(low_full):
            repaired = _normalize_text(
                repaired.rstrip()
                + " Make an Insight check if you want a clearer read on motive—not as a hidden fact."
            )
            modes.append("invented_intent_insight_prompt")
        else:
            span = _na_intent_sentence_span(
                repaired,
                player_text=player_text,
                resolution=resolution if isinstance(resolution, dict) else None,
            )
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "You notice timing, posture, and wording—you can't treat that as proof of motive yet.",
                )
                modes.append("invented_intent_observable_cues")

    if not modes:
        return None, None
    return repaired, "|".join(modes)


def _apply_narrative_authority_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> tuple[str, Dict[str, Any], List[str]]:
    _ = answer_completeness_meta
    strict_social_path = strict_social_details is not None
    contract = _resolve_narrative_authority_contract(gm_output if isinstance(gm_output, dict) else None)

    meta = _default_narrative_authority_meta()

    skip = _skip_narrative_authority_layer(
        text,
        contract,
        gm_output=gm_output if isinstance(gm_output, dict) else None,
        response_type_debug=response_type_debug,
    )
    meta["narrative_authority_skip_reason"] = skip
    if skip:
        return text, meta, []

    assert contract is not None
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

    v0 = validate_narrative_authority(
        text,
        contract,
        resolution=resolution if isinstance(resolution, Mapping) else None,
        player_text=player_text,
    )
    meta["narrative_authority_checked"] = bool(v0.get("checked"))
    meta["narrative_authority_deferral_mode"] = v0.get("matched_deferral_mode")
    af = v0.get("assertion_flags")
    meta["narrative_authority_assertion_flags"] = dict(af) if isinstance(af, dict) else {}

    if not v0.get("checked") or v0.get("passed"):
        return text, meta, []

    meta["narrative_authority_failed"] = True
    meta["narrative_authority_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired, mode = _repair_narrative_authority_narrow(
        text,
        v0,
        resolution=resolution if isinstance(resolution, Mapping) else None,
        player_text=player_text,
    )
    if repaired:
        v1 = validate_narrative_authority(
            repaired,
            contract,
            resolution=resolution if isinstance(resolution, Mapping) else None,
            player_text=player_text,
        )
        if v1.get("passed"):
            meta["narrative_authority_repaired"] = True
            meta["narrative_authority_repair_mode"] = mode
            meta["narrative_authority_failed"] = False
            meta["narrative_authority_failure_reasons"] = []
            meta["narrative_authority_deferral_mode"] = v1.get("matched_deferral_mode")
            af1 = v1.get("assertion_flags")
            meta["narrative_authority_assertion_flags"] = dict(af1) if isinstance(af1, dict) else {}
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("narrative_authority_unsatisfied_after_repair")
    meta["narrative_authority_failed"] = True
    return text, meta, extra


# --- Anti-railroading (anti_railroading_contract + validate_anti_railroading) -------------------


def _is_shipped_full_anti_railroading_contract(candidate: Any) -> bool:
    """True for ``build_anti_railroading_contract`` payloads."""
    if not isinstance(candidate, dict):
        return False
    return "forbid_player_decision_override" in candidate and "enabled" in candidate


def _coerce_anti_railroading_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if _is_shipped_full_anti_railroading_contract(maybe):
        return maybe
    return None


def _resolve_anti_railroading_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Prefer shipped narration / prompt_context mirrors; never substitute prompt_debug alone."""
    if not isinstance(gm_output, dict):
        return None
    direct = gm_output.get("anti_railroading_contract")
    if isinstance(direct, dict):
        hit = _coerce_anti_railroading_contract_dict(direct)
        if hit:
            return hit
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = _coerce_anti_railroading_contract_dict(pol.get("anti_railroading"))
        if hit:
            return hit
    pc = gm_output.get("prompt_context")
    if isinstance(pc, dict):
        hit = _coerce_anti_railroading_contract_dict(pc.get("anti_railroading_contract"))
        if hit:
            return hit
        pol2 = pc.get("response_policy")
        if isinstance(pol2, dict):
            hit = _coerce_anti_railroading_contract_dict(pol2.get("anti_railroading"))
            if hit:
                return hit
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = _coerce_anti_railroading_contract_dict(pl.get("anti_railroading_contract"))
        if hit:
            return hit
        hit = _coerce_anti_railroading_contract_dict(pl.get("anti_railroading"))
        if hit:
            return hit
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_anti_railroading_contract_dict(rp.get("anti_railroading"))
            if hit:
                return hit
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = _coerce_anti_railroading_contract_dict(md.get("anti_railroading_contract"))
        if hit:
            return hit
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_anti_railroading_contract_dict(rp.get("anti_railroading"))
            if hit:
                return hit
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = _coerce_anti_railroading_contract_dict(tr.get("anti_railroading_contract"))
        if hit:
            return hit
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_anti_railroading_contract_dict(rp.get("anti_railroading"))
            if hit:
                return hit
    return None


def _fallback_build_anti_railroading_contract(
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
    nac = _resolve_narrative_authority_contract(gm_output if isinstance(gm_output, dict) else None)
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


def _effective_anti_railroading_contract_for_gate(
    gm_output: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> tuple[Dict[str, Any], str]:
    shipped = _resolve_anti_railroading_contract(gm_output if isinstance(gm_output, dict) else None)
    if shipped is not None:
        return shipped, "shipped"
    built = _fallback_build_anti_railroading_contract(gm_output, resolution, session, scene_id)
    return built, "fallback_build"


def _default_anti_railroading_meta() -> Dict[str, Any]:
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


def _merge_anti_railroading_meta(meta: Dict[str, Any], ar_dbg: Dict[str, Any]) -> None:
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


def _merge_anti_railroading_into_emission_debug(
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


def _repair_anti_railroading_narrow(
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


def _skip_anti_railroading_layer(
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


def _apply_anti_railroading_layer(
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
    meta = _default_anti_railroading_meta()
    ctr, src = _effective_anti_railroading_contract_for_gate(
        gm_output if isinstance(gm_output, dict) else None,
        resolution,
        session,
        str(scene_id or "").strip(),
    )
    meta["anti_railroading_contract_resolution_source"] = src

    skip = _skip_anti_railroading_layer(text, ctr, response_type_debug=response_type_debug)
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
    repaired, mode = _repair_anti_railroading_narrow(
        text,
        v0,
        contract=ctr,
        player_text=player_text,
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    if repaired:
        v1 = validate_anti_railroading(
            repaired,
            ctr,
            player_text=player_text,
            resolution=resolution if isinstance(resolution, Mapping) else None,
        )
        meta["anti_railroading_checked"] = bool(v1.get("checked"))
        meta["anti_railroading_ok"] = bool(v1.get("passed"))
        meta["anti_railroading_failure_reasons"] = list(v1.get("failure_reasons") or [])
        af1 = v1.get("assertion_flags")
        meta["anti_railroading_assertion_flags"] = dict(af1) if isinstance(af1, dict) else {}
        meta["anti_railroading_repair_hints"] = anti_railroading_repair_hints(v1)
        if v1.get("passed"):
            meta["anti_railroading_repaired"] = True
            meta["anti_railroading_repair_mode"] = mode
            meta["anti_railroading_failed"] = False
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("anti_railroading_unsatisfied_after_repair")
    meta["anti_railroading_failed"] = True
    meta["anti_railroading_ok"] = False
    return text, meta, extra


# --- Context separation (shipped context_separation_contract + validate_context_separation) -----


def _is_shipped_full_context_separation_contract(candidate: Any) -> bool:
    """True for ``build_context_separation_contract`` payloads, not ad-hoc dicts."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict) and "forbid_topic_hijack" in candidate:
        return True
    if "forbid_topic_hijack" in candidate and "max_pressure_sentences_without_player_prompt" in candidate:
        return True
    return False


def _coerce_context_separation_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if _is_shipped_full_context_separation_contract(maybe):
        return maybe
    return None


def _resolve_context_separation_contract(
    gm_output: Dict[str, Any] | None,
) -> tuple[Dict[str, Any] | None, str | None]:
    """Read the shipped contract from *gm_output* / narration / policy mirrors (no rebuild)."""
    if not isinstance(gm_output, dict):
        return None, None
    direct = gm_output.get("context_separation_contract")
    if isinstance(direct, dict):
        hit = _coerce_context_separation_contract_dict(direct)
        if hit:
            return hit, "context_separation_contract"
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        for key in ("context_separation_contract", "context_separation"):
            hit = _coerce_context_separation_contract_dict(pol.get(key))
            if hit:
                return hit, "response_policy"
    pc = gm_output.get("prompt_context")
    if isinstance(pc, dict):
        hit = _coerce_context_separation_contract_dict(pc.get("context_separation_contract"))
        if hit:
            return hit, "prompt_context"
        pol2 = pc.get("response_policy")
        if isinstance(pol2, dict):
            for key in ("context_separation_contract", "context_separation"):
                hit = _coerce_context_separation_contract_dict(pol2.get(key))
                if hit:
                    return hit, "prompt_context.response_policy"
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        for ck in ("context_separation_contract", "context_separation"):
            hit = _coerce_context_separation_contract_dict(pl.get(ck))
            if hit:
                return hit, f"{key}"
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            for ck in ("context_separation_contract", "context_separation"):
                hit = _coerce_context_separation_contract_dict(rp.get(ck))
                if hit:
                    return hit, f"{key}.response_policy"
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = _coerce_context_separation_contract_dict(md.get("context_separation_contract"))
        if hit:
            return hit, "metadata"
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            for ck in ("context_separation_contract", "context_separation"):
                hit = _coerce_context_separation_contract_dict(rp.get(ck))
                if hit:
                    return hit, "metadata.response_policy"
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = _coerce_context_separation_contract_dict(tr.get("context_separation_contract"))
        if hit:
            return hit, "trace"
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            for ck in ("context_separation_contract", "context_separation"):
                hit = _coerce_context_separation_contract_dict(rp.get(ck))
                if hit:
                    return hit, "trace.response_policy"
    return None, None


def _default_context_separation_meta() -> Dict[str, Any]:
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


def _merge_context_separation_meta(meta: Dict[str, Any], cs_dbg: Dict[str, Any]) -> None:
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


def _merge_context_separation_into_emission_debug(
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


def _context_separation_debug_reason_marker(
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


def _repair_context_separation_narrow(
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


def _skip_context_separation_layer(
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


def _apply_context_separation_layer(
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
    meta = _default_context_separation_meta()
    ctr, src = _resolve_context_separation_contract(gm_output if isinstance(gm_output, dict) else None)
    meta["context_separation_contract_resolution_source"] = src

    skip = _skip_context_separation_layer(text, ctr, response_type_debug=response_type_debug)
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
        meta["context_separation_debug_reason_marker"] = _context_separation_debug_reason_marker(
            before,
            before,
            violations=[],
            repair_applied=False,
            passed_after=None,
        )
        return text, meta, []

    repaired, mode = _repair_context_separation_narrow(
        before,
        ctr,
        player_text=pt,
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    if repaired:
        v1 = validate_context_separation(
            repaired,
            ctr,
            player_text=pt,
            resolution=resolution if isinstance(resolution, Mapping) else None,
        )
        meta["context_separation_checked"] = bool(v1.get("checked"))
        meta["context_separation_ok"] = bool(v1.get("passed"))
        af1 = v1.get("assertion_flags")
        meta["context_separation_assertion_flags"] = dict(af1) if isinstance(af1, dict) else {}
        meta["context_separation_failure_reasons"] = [str(x) for x in (v1.get("failure_reasons") or []) if isinstance(x, str)]
        passed_after = bool(v1.get("passed"))
        meta["context_separation_passed_after_repair"] = passed_after
        if v1.get("passed"):
            meta["context_separation_repaired"] = True
            meta["context_separation_repair_mode"] = mode
            meta["context_separation_failed"] = False
            meta["context_separation_debug_reason_marker"] = _context_separation_debug_reason_marker(
                before,
                repaired,
                violations=fails0,
                repair_applied=True,
                passed_after=True,
            )
            return repaired, meta, []
        meta["context_separation_failed"] = True
        meta["context_separation_debug_reason_marker"] = _context_separation_debug_reason_marker(
            before,
            repaired,
            violations=fails0,
            repair_applied=True,
            passed_after=False,
        )
    else:
        meta["context_separation_failed"] = True
        meta["context_separation_passed_after_repair"] = None
        meta["context_separation_debug_reason_marker"] = _context_separation_debug_reason_marker(
            before,
            before,
            violations=fails0,
            repair_applied=False,
            passed_after=False,
        )

    extra: List[str] = []
    if not strict_social_path:
        extra.append("context_separation_unsatisfied_after_repair")
    meta["context_separation_ok"] = False
    return text, meta, extra


# --- Player-facing narration purity (shipped contract; before scene state anchor) ---------------

_ASP_PRESSURE_LEX_RE = re.compile(
    r"\b(?:tension|confrontation|crackdown|border\s+war|the\s+war\b|unrest|factions|politics|"
    r"stakes|consequences|pressure|looms|mounts|swallows|brittle|tear\s+at|invasion|rumors?\s+outrun|"
    r"everyone\s+on\s+edge|nothing\s+feels\s+clean|the\s+city\s+watches|choose\s+your\s+next)\b",
    re.IGNORECASE,
)
_ASP_OBSERVE_PAYLOAD_RE = re.compile(
    r"\b(?:see|hear|notice|spot|smell|taste|feel|watch|scan|survey|glimpse|make\s+out)\b",
    re.IGNORECASE,
)
_ASP_SPATIAL_OR_EXISTENTIAL_RE = re.compile(
    r"\b(?:there\s+is|there\s+are|ahead|behind|above|below|to\s+your\s+(?:left|right)|"
    r"at\s+the|under\s+the|over\s+the|along\s+the)\b",
    re.IGNORECASE,
)
_ASP_ARRIVAL_RE = re.compile(
    r"\b(?:step|steps|arrive|arriving|enter|entering|cross|crossing|reach|reaching|pass|passing|emerge)\b",
    re.IGNORECASE,
)
_ASP_SCENE_TEXTURE_RE = re.compile(
    r"\b(?:rain|mud|cobble|torchlight|torch|smoke|arch|door|cart|boots|slate|roof|gutter|bell|hammer|iron)\b",
    re.IGNORECASE,
)
_ASP_AMBIENT_STATE_RE = re.compile(
    r"\b(?:silence|stillness|quiet|hush|calm|pause)\b",
    re.IGNORECASE,
)
_ASP_INFORMATIVE_DETAIL_RE = re.compile(
    r"\b(?:lead|leads|clue|clues|keeper|office|lighthouse|warehouse|checkpoint|register|captain|sergeant|"
    r"customs|harbor|quay|stall|merchant|barracks|alley|roofline|bridge|fold|archive|priest|cellar)\b",
    re.IGNORECASE,
)

_ANSWER_SHAPE_PRIMACY_RESOLUTION_KINDS = frozenset(
    {
        "observe",
        "investigate",
        "interact",
        "travel",
        "scene_transition",
        "discover_clue",
        "already_searched",
        "search",
        "scene_opening",
    }
)


def _is_shipped_player_facing_narration_purity_contract(candidate: Any) -> bool:
    if not isinstance(candidate, dict):
        return False
    if "forbid_scaffold_headers" in candidate and "diegetic_only" in candidate:
        return True
    dr = str(candidate.get("debug_reason") or "")
    return "player_facing_narration_purity" in dr


def _coerce_player_facing_narration_purity_contract(maybe: Any) -> Dict[str, Any] | None:
    if _is_shipped_player_facing_narration_purity_contract(maybe):
        return maybe
    return None


def _resolve_player_facing_narration_purity_contract(
    gm_output: Dict[str, Any] | None,
) -> tuple[Dict[str, Any] | None, str | None]:
    """Read shipped narration-purity policy from gm_output mirrors (no rebuild)."""
    if not isinstance(gm_output, dict):
        return None, None
    direct = gm_output.get("player_facing_narration_purity_contract")
    if isinstance(direct, dict):
        hit = _coerce_player_facing_narration_purity_contract(direct)
        if hit:
            return hit, "player_facing_narration_purity_contract"
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = _coerce_player_facing_narration_purity_contract(pol.get("player_facing_narration_purity"))
        if hit:
            return hit, "response_policy"
    pc = gm_output.get("prompt_context")
    if isinstance(pc, dict):
        hit = _coerce_player_facing_narration_purity_contract(
            pc.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, "prompt_context"
        pol2 = pc.get("response_policy")
        if isinstance(pol2, dict):
            hit = _coerce_player_facing_narration_purity_contract(
                pol2.get("player_facing_narration_purity")
            )
            if hit:
                return hit, "prompt_context.response_policy"
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = _coerce_player_facing_narration_purity_contract(
            pl.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, key
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_player_facing_narration_purity_contract(
                rp.get("player_facing_narration_purity")
            )
            if hit:
                return hit, f"{key}.response_policy"
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = _coerce_player_facing_narration_purity_contract(
            md.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, "metadata"
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_player_facing_narration_purity_contract(
                rp.get("player_facing_narration_purity")
            )
            if hit:
                return hit, "metadata.response_policy"
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = _coerce_player_facing_narration_purity_contract(
            tr.get("player_facing_narration_purity_contract")
        )
        if hit:
            return hit, "trace"
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = _coerce_player_facing_narration_purity_contract(
                rp.get("player_facing_narration_purity")
            )
            if hit:
                return hit, "trace.response_policy"
    return None, None


def _default_player_facing_narration_purity_meta() -> Dict[str, Any]:
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


def _merge_player_facing_narration_purity_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    if not dbg:
        return
    for k, v in dbg.items():
        if str(k).startswith("player_facing_narration_purity_"):
            meta[k] = v


def _merge_player_facing_narration_purity_into_emission_debug(
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


def _gate_text_preview(text: str, limit: int = 96) -> str:
    t = str(text or "")
    return (t[:limit] + "…") if len(t) > limit else t


def _skip_player_facing_narration_purity_layer(
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


def _apply_player_facing_narration_purity_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> tuple[str, Dict[str, Any], List[str]]:
    meta = _default_player_facing_narration_purity_meta()
    ctr, src = _resolve_player_facing_narration_purity_contract(
        gm_output if isinstance(gm_output, dict) else None
    )
    meta["player_facing_narration_purity_contract_resolution_source"] = src
    skip = _skip_player_facing_narration_purity_layer(text, ctr, response_type_debug=response_type_debug)
    meta["player_facing_narration_purity_skip_reason"] = skip
    if skip:
        return text, meta, []

    assert ctr is not None
    before = str(text or "")
    meta["player_facing_narration_purity_preview_before"] = _gate_text_preview(before)
    v0 = validate_player_facing_narration_purity(
        before,
        ctr,
        player_text="",
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    if not v0.get("checked"):
        meta["player_facing_narration_purity_checked"] = False
        meta["player_facing_narration_purity_failed"] = False
        meta["player_facing_narration_purity_preview_after"] = _gate_text_preview(before)
        return text, meta, []

    meta["player_facing_narration_purity_checked"] = True
    fails = [str(x) for x in (v0.get("failure_reasons") or []) if isinstance(x, str)]
    meta["player_facing_narration_purity_violation_keys"] = list(dict.fromkeys(fails))
    hints = player_facing_narration_purity_repair_hints(fails, contract=ctr)
    meta["player_facing_narration_purity_repair_hints_used"] = hints

    if v0.get("passed"):
        meta["player_facing_narration_purity_failed"] = False
        meta["player_facing_narration_purity_preview_after"] = _gate_text_preview(before)
        return text, meta, []

    repaired, rdbg = minimal_repair_player_facing_narration_purity(before, ctr)
    modes = list(rdbg.get("modes") or [])
    meta["player_facing_narration_purity_repair_modes"] = modes
    if rdbg.get("repaired"):
        meta["player_facing_narration_purity_repaired"] = True
    meta["player_facing_narration_purity_collapsed_to_diegetic_core"] = bool(rdbg.get("collapsed_to_core"))

    v1 = validate_player_facing_narration_purity(
        repaired,
        ctr,
        resolution=resolution if isinstance(resolution, Mapping) else None,
    )
    meta["player_facing_narration_purity_preview_after"] = _gate_text_preview(repaired)
    if v1.get("passed"):
        meta["player_facing_narration_purity_failed"] = False
        extra: List[str] = []
        return repaired, meta, extra

    meta["player_facing_narration_purity_failed"] = True
    fails2 = [str(x) for x in (v1.get("failure_reasons") or []) if isinstance(x, str)]
    meta["player_facing_narration_purity_violation_keys"] = list(dict.fromkeys(fails2))
    meta["player_facing_narration_purity_repair_hints_used"] = player_facing_narration_purity_repair_hints(
        fails2, contract=ctr
    )
    extra2: List[str] = []
    extra2.append("player_facing_narration_purity_unrecoverable")
    return repaired, meta, extra2


def _default_answer_shape_primacy_meta() -> Dict[str, Any]:
    return {
        "answer_shape_primacy_skip_reason": None,
        "answer_shape_primacy_checked": False,
        "answer_shape_primacy_failed": False,
        "answer_shape_primacy_repaired": False,
        "answer_shape_primacy_repair_mode": None,
        "answer_shape_primacy_failure_reasons": [],
        "answer_shape_primacy_preview_before": None,
        "answer_shape_primacy_preview_after": None,
    }


def _merge_answer_shape_primacy_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    if not dbg:
        return
    for k, v in dbg.items():
        if str(k).startswith("answer_shape_primacy_"):
            meta[k] = v


def _merge_answer_shape_primacy_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if str(k).startswith("answer_shape_primacy_"):
            flat[k] = v
    nested: Dict[str, Any] = {
        "checked": bool(gate_meta.get("answer_shape_primacy_checked")),
        "passed": not bool(gate_meta.get("answer_shape_primacy_failed")),
        "failure_reasons": list(gate_meta.get("answer_shape_primacy_failure_reasons") or []),
    }
    sr = gate_meta.get("answer_shape_primacy_skip_reason")
    if sr:
        nested["skip_reason"] = sr

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        em["answer_shape_primacy"] = nested
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


def _merge_fallback_behavior_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if str(k).startswith("fallback_behavior_"):
            flat[k] = v
    nested: Dict[str, Any] = {
        "validation": {
            "contract_present": bool(gate_meta.get("fallback_behavior_contract_present")),
            "checked": bool(gate_meta.get("fallback_behavior_checked")),
            "passed": not bool(gate_meta.get("fallback_behavior_failed")),
            "uncertainty_active": bool(gate_meta.get("fallback_behavior_uncertainty_active")),
        },
        "failure_reasons": list(gate_meta.get("fallback_behavior_failure_reasons") or []),
        "repair_mode": gate_meta.get("fallback_behavior_repair_mode"),
    }
    sr = gate_meta.get("fallback_behavior_skip_reason")
    if sr:
        nested["skip_reason"] = sr

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        em["fallback_behavior"] = nested
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


def _merge_conversational_memory_inspection_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
) -> None:
    """Pass-through Objective #15 (conversational memory window + selection counts); no validation."""
    cmw = out.get("conversational_memory_window")
    if not isinstance(cmw, dict):
        pol = out.get("response_policy")
        if isinstance(pol, dict):
            maybe = pol.get("conversational_memory_window")
            cmw = maybe if isinstance(maybe, dict) else None
    scm = out.get("selected_conversational_memory") if isinstance(out.get("selected_conversational_memory"), list) else None
    pd = out.get("prompt_debug")
    cm_counts = pd.get("conversational_memory") if isinstance(pd, dict) else None
    if not isinstance(cm_counts, dict):
        cm_counts = None

    if not isinstance(cmw, dict) and scm is None and cm_counts is None:
        return

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        if isinstance(cmw, dict):
            em["conversational_memory_window"] = dict(cmw)
        if scm is not None:
            em["selected_conversational_memory"] = list(scm)
        if isinstance(cm_counts, dict):
            em["conversational_memory"] = dict(cm_counts)

    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        _patch_em(md_out.setdefault("emission_debug", {}))
    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _patch_em(md_r.setdefault("emission_debug", {}))
    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        _patch_em(eff_resolution["metadata"].setdefault("emission_debug", {}))


def _answer_shape_primacy_applies(
    *,
    resolution: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
) -> bool:
    if strict_social_details is not None:
        return False
    rtr = str((response_type_debug or {}).get("response_type_required") or "").strip().lower()
    if rtr in {"action_outcome", "neutral_narration"}:
        return True
    if not isinstance(resolution, dict):
        return False
    kind = str(resolution.get("kind") or "").strip().lower()
    return kind in _ANSWER_SHAPE_PRIMACY_RESOLUTION_KINDS


def _asp_sentence_has_payload(
    sentence: str,
    *,
    player_tokens: set[str],
    res_kind: str,
    required_rt: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    s = str(sentence or "").strip()
    if not s:
        return False
    if len(_content_tokens(s) & player_tokens) >= 2:
        return True
    if any(p.search(s) for p in _ACTION_RESULT_PATTERNS):
        return True
    if _ASP_OBSERVE_PAYLOAD_RE.search(s):
        return True
    if _ASP_SPATIAL_OR_EXISTENTIAL_RE.search(s):
        return True
    if _ASP_SCENE_TEXTURE_RE.search(s):
        return True
    if _ASP_AMBIENT_STATE_RE.search(s):
        return True
    if _ASP_INFORMATIVE_DETAIL_RE.search(s):
        return True
    if re.search(r'["“”]', s) and len(s) >= 20:
        return True
    if required_rt == "action_outcome" and re.search(r"\b(?:you|your)\b", s, re.IGNORECASE):
        if any(p.search(s) for p in _ACTION_RESULT_PATTERNS):
            return True
        if re.search(
            r"\b(?:latch|door|lock|hinge|snap|give|gives|hold|holds|refuse|refuses)\b",
            s,
            re.IGNORECASE,
        ):
            return True
    st = resolution.get("state_changes") if isinstance(resolution, dict) and isinstance(resolution.get("state_changes"), dict) else {}
    travelish = bool(
        isinstance(resolution, dict)
        and (
            bool(resolution.get("resolved_transition"))
            or bool(st.get("scene_transition_occurred"))
            or bool(st.get("arrived_at_scene"))
        )
    )
    if res_kind in {"travel", "scene_transition"} and travelish and _ASP_ARRIVAL_RE.search(s):
        return True
    return False


def _asp_sentence_is_pressure_only(
    sentence: str,
    *,
    player_tokens: set[str],
    res_kind: str,
    required_rt: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    s = str(sentence or "").strip()
    if not s:
        return False
    if _asp_sentence_has_payload(s, player_tokens=player_tokens, res_kind=res_kind, required_rt=required_rt, resolution=resolution):
        return False
    return bool(_ASP_PRESSURE_LEX_RE.search(s))


def _validate_answer_shape_primacy(
    text: str,
    *,
    player_input: str,
    resolution: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {"passed": True, "failure_reasons": [], "repairable_pressure_lead": False}
    res = resolution if isinstance(resolution, dict) else None
    res_kind = str((res or {}).get("kind") or "").strip().lower()
    required_rt = str((response_type_debug or {}).get("response_type_required") or "").strip().lower()
    player_tokens = _content_tokens(player_input)
    sentences = _split_sentences_answer_complete(str(text or ""))
    if not sentences:
        out["passed"] = False
        out["failure_reasons"].append("empty_text")
        return out

    payload_hits = [
        _asp_sentence_has_payload(
            sent,
            player_tokens=player_tokens,
            res_kind=res_kind,
            required_rt=required_rt,
            resolution=res,
        )
        for sent in sentences
    ]
    if not any(payload_hits):
        wc = len(_normalize_text(text).split())
        any_pressure = any(
            _asp_sentence_is_pressure_only(
                sent,
                player_tokens=player_tokens,
                res_kind=res_kind,
                required_rt=required_rt,
                resolution=res,
            )
            for sent in sentences
        )
        if wc <= 8 and not any_pressure:
            return out
        low = _normalize_text(text).lower()
        if "for a breath" in low and "voices shift" in low:
            out["passed"] = False
            out["failure_reasons"].append("missing_observation_or_result_payload")
            return out
        if _ASP_INFORMATIVE_DETAIL_RE.search(text) or any(p.search(text) for p in _ANSWER_DIRECT_PATTERNS):
            return out
        if wc >= 10 and not any_pressure:
            return out
        out["passed"] = False
        out["failure_reasons"].append("missing_observation_or_result_payload")
        return out

    opener = sentences[0]
    opener_payload = payload_hits[0]
    if not opener_payload and _asp_sentence_is_pressure_only(
        opener,
        player_tokens=player_tokens,
        res_kind=res_kind,
        required_rt=required_rt,
        resolution=res,
    ):
        out["passed"] = False
        out["failure_reasons"].append("pressure_or_consequence_before_payload")
        if any(payload_hits[1:]):
            out["repairable_pressure_lead"] = True
        return out

    return out


def _repair_answer_shape_primacy_leading_pressure(
    text: str,
    *,
    player_input: str,
    resolution: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> tuple[str | None, str | None]:
    res = resolution if isinstance(resolution, dict) else None
    res_kind = str((res or {}).get("kind") or "").strip().lower()
    required_rt = str((response_type_debug or {}).get("response_type_required") or "").strip().lower()
    player_tokens = _content_tokens(player_input)
    sentences = _split_sentences_answer_complete(str(text or ""))
    if len(sentences) < 2:
        return None, None
    i = 0
    while i < len(sentences):
        s = sentences[i]
        has_pl = _asp_sentence_has_payload(
            s,
            player_tokens=player_tokens,
            res_kind=res_kind,
            required_rt=required_rt,
            resolution=res,
        )
        if has_pl:
            break
        if not _asp_sentence_is_pressure_only(
            s,
            player_tokens=player_tokens,
            res_kind=res_kind,
            required_rt=required_rt,
            resolution=res,
        ):
            break
        i += 1
    if i <= 0:
        return None, None
    rest = " ".join(sentences[i:]).strip()
    if not rest:
        return None, None
    return rest, f"strip_leading_pressure_sentences:{i}"


def _apply_answer_shape_primacy_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    response_type_debug: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
) -> tuple[str, Dict[str, Any], List[str]]:
    meta = _default_answer_shape_primacy_meta()
    if not _answer_shape_primacy_applies(
        resolution=resolution,
        response_type_debug=response_type_debug,
        strict_social_details=strict_social_details,
    ):
        meta["answer_shape_primacy_skip_reason"] = "turn_not_in_scope"
        return text, meta, []

    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        meta["answer_shape_primacy_skip_reason"] = "response_type_contract_failed"
        return text, meta, []

    sid = str(scene_id or "").strip()
    player_input = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    if not str(player_input or "").strip():
        player_input = _last_player_input(
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )

    before = str(text or "")
    meta["answer_shape_primacy_preview_before"] = _gate_text_preview(before)
    meta["answer_shape_primacy_checked"] = True

    v0 = _validate_answer_shape_primacy(
        before,
        player_input=player_input,
        resolution=resolution,
        response_type_debug=response_type_debug,
    )
    if v0.get("passed"):
        meta["answer_shape_primacy_failed"] = False
        meta["answer_shape_primacy_preview_after"] = _gate_text_preview(before)
        return text, meta, []

    if v0.get("repairable_pressure_lead"):
        repaired, mode = _repair_answer_shape_primacy_leading_pressure(
            before,
            player_input=player_input,
            resolution=resolution,
            response_type_debug=response_type_debug,
        )
        if repaired:
            v1 = _validate_answer_shape_primacy(
                repaired,
                player_input=player_input,
                resolution=resolution,
                response_type_debug=response_type_debug,
            )
            if v1.get("passed"):
                meta["answer_shape_primacy_repaired"] = True
                meta["answer_shape_primacy_repair_mode"] = mode
                meta["answer_shape_primacy_failed"] = False
                meta["answer_shape_primacy_preview_after"] = _gate_text_preview(repaired)
                return repaired, meta, []

    meta["answer_shape_primacy_failed"] = True
    meta["answer_shape_primacy_failure_reasons"] = list(v0.get("failure_reasons") or [])
    meta["answer_shape_primacy_preview_after"] = _gate_text_preview(before)
    extra: List[str] = ["answer_shape_primacy_violation"]
    return text, meta, extra


# --- Scene state anchor (scene_state_anchor_contract + validate_scene_state_anchoring) ----------


def _resolve_scene_state_anchor_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Read the shipped contract from *gm_output* / narration payload copies only (no rebuild)."""
    if not isinstance(gm_output, dict):
        return None
    direct = gm_output.get("scene_state_anchor_contract")
    if isinstance(direct, dict):
        return direct
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if isinstance(pl, dict):
            sac = pl.get("scene_state_anchor_contract")
            if isinstance(sac, dict):
                return sac
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        sac = md.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            return sac
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        sac = tr.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            return sac
    return None


def _resolve_scene_state_anchor_debug(gm_output: Dict[str, Any] | None) -> Dict[str, Any]:
    """Compact upstream summary (e.g. gm emission_debug.scene_state_anchor) for metadata merge."""
    if not isinstance(gm_output, dict):
        return {}
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            dbg = em.get("scene_state_anchor")
            if isinstance(dbg, dict):
                return dict(dbg)
    return {}


def _default_scene_state_anchor_meta(
    skip: str | None,
    upstream_debug: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "scene_state_anchor_checked": False,
        "scene_state_anchor_passed": False,
        "scene_state_anchor_failed": False,
        "scene_state_anchor_skip_reason": skip,
        "scene_state_anchor_matched_kinds": [],
        "scene_state_anchor_failure_reasons": [],
        "scene_state_anchor_repaired": False,
        "scene_state_anchor_repair_mode": None,
        "scene_state_anchor_upstream_debug": dict(upstream_debug),
    }


def _merge_scene_state_anchor_meta(meta: Dict[str, Any], ssa_dbg: Dict[str, Any]) -> None:
    if not ssa_dbg:
        return
    keys = (
        "scene_state_anchor_checked",
        "scene_state_anchor_passed",
        "scene_state_anchor_failed",
        "scene_state_anchor_skip_reason",
        "scene_state_anchor_matched_kinds",
        "scene_state_anchor_failure_reasons",
        "scene_state_anchor_repaired",
        "scene_state_anchor_repair_mode",
        "scene_state_anchor_upstream_debug",
    )
    for k in keys:
        if k in ssa_dbg:
            meta[k] = ssa_dbg[k]


def _merge_scene_state_anchor_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
) -> None:
    """Attach gate fields and preserve/merge compact upstream ``scene_state_anchor`` summaries."""
    upstream: Any = None
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("scene_state_anchor_"):
            continue
        if k == "scene_state_anchor_upstream_debug":
            upstream = v
            continue
        flat[k] = v
    if not flat and not (isinstance(upstream, dict) and upstream):
        return

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        base = em.get("scene_state_anchor")
        if isinstance(upstream, dict) and upstream:
            if isinstance(base, dict):
                merged = {**upstream, **base}
            else:
                merged = dict(upstream)
            em["scene_state_anchor"] = merged
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


def _skip_scene_state_anchor_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None = None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not isinstance(contract, dict):
        return "missing_contract"
    if not contract.get("enabled"):
        return "contract_disabled"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    if strict_social_details:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            return "strict_social_structured_or_bridge_source"
    return None


def _title_case_anchor_phrase(phrase: str) -> str:
    parts = [p for p in str(phrase or "").strip().split() if p]
    if not parts:
        return ""
    out: List[str] = []
    for w in parts:
        if not w:
            continue
        out.append(w[:1].upper() + w[1:].lower() if len(w) > 1 else w.upper())
    return " ".join(out)


def _opening_has_token_hint(text: str, token_lower: str) -> bool:
    if not token_lower or not str(text or "").strip():
        return False
    low = str(text).lower()
    head = low[: min(len(low), 280)]
    if " " in token_lower:
        return token_lower in head
    return bool(re.search(rf"(?<!\w){re.escape(token_lower)}(?!\w)", head))


def _pick_actor_token(actor_tokens: Sequence[Any]) -> str | None:
    for raw in actor_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 3 and not s.isdigit():
            return s
    return None


def _pick_action_tether_token(player_action_tokens: Sequence[Any]) -> str | None:
    for raw in player_action_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if " " in s and 5 <= len(s) <= 96:
            return s
    skip_one = frozenset({"question", "answer", "observe", "investigate", "action", "kind"})
    for raw in player_action_tokens or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 4 and s not in skip_one:
            return s
    return None


def _pick_location_phrase(contract: Mapping[str, Any]) -> str | None:
    lab = str(contract.get("scene_location_label") or "").strip()
    if lab and len(lab) >= 2:
        return lab.lower()
    for raw in contract.get("location_tokens") or []:
        if not isinstance(raw, str):
            continue
        s = raw.strip().lower()
        if len(s) >= 3:
            return s
    return None


def _repair_actor_opening(text: str, actor_tokens: Sequence[Any]) -> tuple[str | None, str | None]:
    tok = _pick_actor_token(actor_tokens)
    if not tok:
        return None, None
    if _opening_has_token_hint(text, tok):
        return None, None
    display = _title_case_anchor_phrase(tok)
    if not display:
        return None, None
    return _normalize_text(f"{display} {text}"), "actor_rebind"


def _repair_action_tether(text: str, player_action_tokens: Sequence[Any]) -> tuple[str | None, str | None]:
    tok = _pick_action_tether_token(player_action_tokens)
    if not tok:
        return None, None
    if _opening_has_token_hint(text, tok):
        return None, None
    lead = _title_case_anchor_phrase(tok) if " " in tok else tok.capitalize()
    return _normalize_text(f"{lead} — {text}"), "action_rebind"


def _repair_location_opening(text: str, contract: Mapping[str, Any]) -> tuple[str | None, str | None]:
    phrase = _pick_location_phrase(contract)
    if not phrase:
        return None, None
    if _opening_has_token_hint(text, phrase):
        return None, None
    disp = _title_case_anchor_phrase(phrase)
    if not disp:
        return None, None
    return _normalize_text(f"At {disp}, {text}"), "location_rebind"


def _repair_narrator_neutral_location(text: str, contract: Mapping[str, Any]) -> tuple[str | None, str | None]:
    phrase = _pick_location_phrase(contract)
    if not phrase:
        return None, None
    if _opening_has_token_hint(text, phrase):
        return None, None
    disp = _title_case_anchor_phrase(phrase)
    if not disp:
        return None, None
    return _normalize_text(f"Here at {disp}, {text}"), "narrator_neutral_scene_rebind"


def _repair_scene_state_anchor_minimal(
    text: str,
    contract: Mapping[str, Any],
    *,
    gm_output: Dict[str, Any] | None = None,
    strict_social_details: Dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    """Opening-tether repairs only; uses contract token buckets (no new facts)."""
    tags_ssa = [str(t) for t in ((gm_output or {}).get("tags") or []) if isinstance(t, str)]
    fast_fallback_neutral = (
        not strict_social_details
        and any(tag in tags_ssa for tag in ("upstream_api_fast_fallback", "forced_retry_fallback", "retry_escape_hatch"))
    )
    actors = list(contract.get("actor_tokens") or [])
    actions = list(contract.get("player_action_tokens") or [])
    if not fast_fallback_neutral:
        # Repair ladder: A actor → B action → C location → D narrator-neutral + location.
        r, mode = _repair_actor_opening(text, actors)
        if r:
            return r, mode
        r, mode = _repair_action_tether(text, actions)
        if r:
            return r, mode
    r, mode = _repair_location_opening(text, contract)
    if r:
        return r, mode
    r, mode = _repair_narrator_neutral_location(text, contract)
    if r:
        return r, mode
    return None, None


def _apply_scene_state_anchor_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None = None,
) -> tuple[str, Dict[str, Any]]:
    contract = _resolve_scene_state_anchor_contract(gm_output)
    upstream = _resolve_scene_state_anchor_debug(gm_output)
    norm = _normalize_text(text).strip()
    tags_ssa = [str(t) for t in (gm_output.get("tags") or []) if isinstance(t, str)]
    dbg_ssa = str(gm_output.get("debug_notes") or "")
    if norm and re.fullmatch(r"\[[^\]]{1,120}\]", norm):
        meta = _default_scene_state_anchor_meta("bracketed_production_stub", upstream)
        meta["scene_state_anchor_checked"] = False
        meta["scene_state_anchor_passed"] = True
        meta["scene_state_anchor_skip_reason"] = "bracketed_production_stub"
        return text, meta
    if "known_fact_guard" in tags_ssa and "recent_dialogue_continuity" in dbg_ssa:
        meta = _default_scene_state_anchor_meta("known_fact_recent_dialogue_continuity", upstream)
        meta["scene_state_anchor_checked"] = False
        meta["scene_state_anchor_passed"] = True
        meta["scene_state_anchor_skip_reason"] = "known_fact_recent_dialogue_continuity"
        return text, meta
    skip = _skip_scene_state_anchor_layer(
        text,
        contract,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
    )
    meta = _default_scene_state_anchor_meta(skip, upstream)
    if skip:
        return text, meta

    assert contract is not None
    v0 = validate_scene_state_anchoring(text, contract)
    meta["scene_state_anchor_checked"] = bool(v0.get("checked"))
    meta["scene_state_anchor_passed"] = bool(v0.get("passed"))
    meta["scene_state_anchor_matched_kinds"] = list(v0.get("matched_anchor_kinds") or [])
    meta["scene_state_anchor_failure_reasons"] = list(v0.get("failure_reasons") or [])
    if v0.get("passed"):
        return text, meta

    repaired, mode = _repair_scene_state_anchor_minimal(
        text,
        contract,
        gm_output=gm_output,
        strict_social_details=strict_social_details,
    )
    if repaired:
        v1 = validate_scene_state_anchoring(repaired, contract)
        meta["scene_state_anchor_checked"] = bool(v1.get("checked"))
        meta["scene_state_anchor_passed"] = bool(v1.get("passed"))
        meta["scene_state_anchor_matched_kinds"] = list(v1.get("matched_anchor_kinds") or [])
        meta["scene_state_anchor_failure_reasons"] = list(v1.get("failure_reasons") or [])
        if v1.get("passed"):
            meta["scene_state_anchor_repaired"] = True
            meta["scene_state_anchor_repair_mode"] = mode
            meta["scene_state_anchor_failed"] = False
            return repaired, meta

    meta["scene_state_anchor_failed"] = True
    meta["scene_state_anchor_repaired"] = False
    meta["scene_state_anchor_repair_mode"] = None
    return text, meta


def _enforce_response_type_contract(
    candidate_text: str,
    *,
    gm_output: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
    strict_social_turn: bool,
    strict_social_suppressed_non_social_turn: bool,
    active_interlocutor: str,
) -> tuple[str, Dict[str, Any]]:
    contract, source = _resolve_response_type_contract(
        gm_output if isinstance(gm_output, dict) else None,
        resolution=resolution,
        session=session,
    )
    debug = _default_response_type_debug(contract, source)
    if not contract:
        return candidate_text, debug

    required = str(contract.get("required_response_type") or "").strip().lower()
    _norm = (
        _normalize_text_preserve_paragraphs
        if strict_social_turn and required == "dialogue"
        else _normalize_text
    )
    player_input = _last_player_input(
        resolution=resolution,
        session=session,
        scene_id=scene_id,
    )
    current = _norm(candidate_text)
    reasons: List[str] = []

    validator_ok = True
    validator_reasons: List[str] = []
    if required == "dialogue":
        if strict_social_suppressed_non_social_turn:
            debug["response_type_candidate_ok"] = None
            debug["response_type_repair_kind"] = "dialogue_enforcement_skipped_due_to_social_suppression"
            return current, debug
        validator_ok, validator_reasons = candidate_satisfies_dialogue_contract(
            current,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
            world=world,
        )
    elif required == "answer":
        validator_ok, validator_reasons = candidate_satisfies_answer_contract(current)
    elif required == "action_outcome":
        validator_ok, validator_reasons = candidate_satisfies_action_outcome_contract(
            current,
            player_input=player_input,
        )
    reasons.extend(validator_reasons)

    if validator_ok and not reasons:
        debug["response_type_candidate_ok"] = True
        return current, debug

    repaired: str | None = None
    repair_kind: str | None = None
    if required == "dialogue":
        social_resolution = _social_fallback_resolution(
            resolution=resolution,
            active_interlocutor=active_interlocutor,
            world=world,
            scene_id=scene_id,
        )
        if strict_social_turn and isinstance(social_resolution, dict):
            repaired = strict_social_ownership_terminal_fallback(social_resolution)
            repair_kind = "strict_social_dialogue_repair"
        elif isinstance(social_resolution, dict):
            repaired = minimal_social_emergency_fallback_line(social_resolution)
            repair_kind = "dialogue_minimal_repair"
    elif required == "answer":
        repaired = _minimal_answer_contract_repair(
            resolution=resolution,
            active_interlocutor=active_interlocutor,
            world=world,
            scene_id=scene_id,
        )
        if repaired:
            repair_kind = "answer_minimal_repair"
    elif required == "action_outcome":
        repaired = _minimal_action_outcome_contract_repair(
            player_input=player_input,
            resolution=resolution,
        )
        repair_kind = "action_outcome_minimal_repair"

    if repaired:
        repaired = _norm(repaired)
        repaired_reasons: List[str] = []
        if required == "dialogue":
            repaired_ok, validator_reasons = candidate_satisfies_dialogue_contract(
                repaired,
                resolution=resolution,
                session=session,
                scene_id=scene_id,
                world=world,
            )
        elif required == "answer":
            repaired_ok, validator_reasons = candidate_satisfies_answer_contract(repaired)
        elif required == "action_outcome":
            repaired_ok, validator_reasons = candidate_satisfies_action_outcome_contract(
                repaired,
                player_input=player_input,
            )
        else:
            repaired_ok, validator_reasons = (True, [])
        repaired_reasons.extend(validator_reasons)
        if repaired_ok and not repaired_reasons:
            debug["response_type_candidate_ok"] = True
            debug["response_type_repair_used"] = True
            debug["response_type_repair_kind"] = repair_kind
            debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
            return repaired, debug

    debug["response_type_candidate_ok"] = False
    debug["response_type_repair_kind"] = repair_kind
    debug["response_type_rejection_reasons"] = list(dict.fromkeys(str(r) for r in reasons if r))
    return current, debug


_PARTICIPIAL_BASE_VERBS: Dict[str, str] = {
    "intertwining": "intertwine",
    "drawing": "draw",
    "hinting": "hint",
    "suggesting": "suggest",
    "making": "make",
    "indicating": "indicate",
    "offering": "offer",
    "creating": "create",
    "revealing": "reveal",
    "urging": "urge",
    "watching": "watch",
    "cutting": "cut",
}
_PARTICIPIAL_THIRD_PERSON: Dict[str, str] = {
    "intertwining": "intertwines",
    "drawing": "draws",
    "hinting": "hints",
    "suggesting": "suggests",
    "making": "makes",
    "indicating": "indicates",
    "offering": "offers",
    "creating": "creates",
    "revealing": "reveals",
    "urging": "urges",
    "watching": "watches",
    "cutting": "cuts",
}
_IMPLICATION_PARTICIPLES = {"hinting", "indicating", "revealing"}
_MICRO_SMOOTH_MAX_COMBINED_LEN = 140
_MICRO_SMOOTH_SHORT_SENTENCE_LEN = 85
_MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS = (
    ";",
    ":",
    " while ",
    " because ",
    " although ",
    " though ",
    " which ",
    " that ",
    " who ",
)
_MICRO_SMOOTH_BANNED_TAIL_PHRASES = (
    "hinting at",
    "suggesting",
    "implying",
    "revealing",
    "indicating",
)
_MICRO_SMOOTH_COMBAT_MECHANICAL_MARKERS = (
    "initiative",
    "attack roll",
    "damage",
    "hit points",
    "armor class",
    "saving throw",
    "spell slot",
    "dc ",
    "roll ",
    "check ",
    "hp",
    "ac",
)
_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[\"“”'‘’]"),
    re.compile(
        r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|"
        r"blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|"
        r"orders?|interrupts?|thrusts?|hands?|points?)\b",
        re.IGNORECASE,
    ),
)
# Dialogue tag with singular they: "… out loud," they murmur (comma before closing quote) or "…", they say.
_DIALOGUE_ATTRIBUTION_THEY_SPEECH_TAG = re.compile(
    r"(?:"
    r'[""“](.+?),\s*[""”]\s+\b(?:they|them)\b'
    r"|"
    r'[""“](.+?)[""”]\s*,\s+\b(?:they|them)\b'
    r")"
    r"[^.!?\n]{0,200}\b(?:"
    r"murmur|mutters|muttered|say|says|said|asks?|asked|whisper|whispers|whispered|"
    r"reply|replies|replied|add|adds|added"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_THIRD_PERSON_TO_PARTICIPLE: Dict[str, str] = {
    "cuts": "cutting",
    "draws": "drawing",
    "hints": "hinting",
    "suggests": "suggesting",
    "makes": "making",
    "indicates": "indicating",
    "offers": "offering",
    "creates": "creating",
    "reveals": "revealing",
    "urges": "urging",
    "watches": "watching",
    "calls": "calling",
    "shouts": "shouting",
    "scans": "scanning",
    "studies": "studying",
    "gestures": "gesturing",
    "lingers": "lingering",
    "waits": "waiting",
    "stands": "standing",
    "speaks": "speaking",
    "says": "saying",
    "holds": "holding",
    "keeps": "keeping",
    "looks": "looking",
    "glances": "glancing",
    "murmurs": "murmuring",
    "whispers": "whispering",
    "observes": "observing",
    "surveys": "surveying",
    "exchanges": "exchanging",
}


def _looks_like_participial_fragment(text: str) -> bool:
    clean = _normalize_text(text).strip()
    if not clean:
        return False
    core = clean.rstrip(".!?").strip(" ,;")
    if not core:
        return False

    words = re.findall(r"[A-Za-z][A-Za-z'-]*", core)
    if len(words) < 3 or len(words) > 22:
        return False

    first = words[0].lower()
    if not first.endswith("ing"):
        return False
    if first not in _PARTICIPIAL_BASE_VERBS:
        return False

    # Avoid touching already-complete short clauses.
    early = " ".join(words[:7]).lower()
    finite_markers = (
        " is ",
        " are ",
        " was ",
        " were ",
        " has ",
        " have ",
        " had ",
        " does ",
        " do ",
        " did ",
        " will ",
        " can ",
        " could ",
        " should ",
        " would ",
        " must ",
    )
    early_padded = f" {early} "
    if any(marker in early_padded for marker in finite_markers):
        return False

    if re.match(r"^(?:as|because|if|when|while|although)\b", core, flags=re.IGNORECASE):
        return False
    return True


def _has_single_actor_anchor(previous_sentence: str) -> bool:
    prev = _normalize_text(previous_sentence).rstrip(".!?")
    if not prev:
        return False
    lowered = prev.lower()

    if any(token in lowered for token in (" and ", " both ", " together ", " alongside ", " two ", " several ")):
        return False
    if any(token in lowered for token in (" they ", " we ", " them ", " their ", " voices ")):
        return False

    singular_signal = re.search(
        r"\b(?:is|was|calls|shouts|offers|watches|studies|lingers|gestures|waits|leans|stands|speaks|says)\b",
        lowered,
    )
    plural_signal = re.search(r"\b(?:are|were|call|shout|offer|watch|study|linger|gesture|wait|speak|say)\b", lowered)
    if plural_signal and not singular_signal:
        return False
    return singular_signal is not None


def _departicipialize_clause(fragment_clause: str, *, subject: str, third_person: bool = False) -> str:
    clause = _normalize_text(fragment_clause).strip(" ,;")
    match = re.match(r"^([A-Za-z][A-Za-z'-]*ing)\b(.*)$", clause, flags=re.IGNORECASE)
    if not match:
        return ""
    participle = match.group(1).lower()
    remainder = _normalize_text(match.group(2))
    verb = _PARTICIPIAL_THIRD_PERSON.get(participle) if third_person else _PARTICIPIAL_BASE_VERBS.get(participle)
    if not verb:
        return ""
    if remainder:
        return _normalize_terminal_punctuation(f"{subject} {verb}{(' ' + remainder) if not remainder.startswith(',') else remainder}")
    return _normalize_terminal_punctuation(f"{subject} {verb}")


def _repair_participial_fragment(previous_sentence: str, fragment: str) -> str | None:
    clean_fragment = _normalize_text(fragment)
    if not _looks_like_participial_fragment(clean_fragment):
        return None

    core = clean_fragment.rstrip(".!?").strip(" ,;")
    if not core:
        return None
    if re.search(r"\b(he|she|him|his)\b", core, flags=re.IGNORECASE):
        return None
    parts = [part.strip(" ,;") for part in core.split(",", 1)]
    head = parts[0] if parts else ""
    tail = parts[1] if len(parts) > 1 else ""
    if not head:
        return None

    if _has_single_actor_anchor(previous_sentence):
        repaired_head = _departicipialize_clause(head, subject="They", third_person=False)
        if not repaired_head:
            return None
        if not tail:
            return repaired_head
        possessive_tail = re.match(
            r"^(their|his|her)\s+([A-Za-z][A-Za-z' -]{0,40})\s+([A-Za-z][A-Za-z'-]*ing)\b(.*)$",
            tail,
            flags=re.IGNORECASE,
        )
        if not possessive_tail:
            return repaired_head
        possessive = possessive_tail.group(1).lower()
        noun_phrase = _normalize_text(possessive_tail.group(2))
        participle = possessive_tail.group(3).lower()
        remainder = _normalize_text(possessive_tail.group(4))
        finite_verb = _PARTICIPIAL_THIRD_PERSON.get(participle)
        if not finite_verb:
            return repaired_head
        subject_phrase = f"{possessive.capitalize()} {noun_phrase}"
        second = (
            _normalize_terminal_punctuation(f"{subject_phrase} {finite_verb}{(' ' + remainder) if remainder else ''}")
            if noun_phrase
            else ""
        )
        if second:
            return _normalize_text(f"{repaired_head} {second}")
        return repaired_head

    head_match = re.match(r"^([A-Za-z][A-Za-z'-]*ing)\b(.*)$", head, flags=re.IGNORECASE)
    if not head_match:
        return None
    head_participle = head_match.group(1).lower()
    if head_participle not in _IMPLICATION_PARTICIPLES:
        return None
    if re.search(r"\b(he|she|they|his|her|their)\b", core, flags=re.IGNORECASE):
        return None
    repaired = _departicipialize_clause(head, subject="It", third_person=True)
    return repaired or None


def _repair_fragmentary_participial_splits(text: str) -> tuple[str, bool]:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text, False
    sentence_parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean_text) if part.strip()]
    if len(sentence_parts) < 2:
        return clean_text, False

    repaired_any = False
    rewritten_parts: List[str] = [sentence_parts[0]]
    for index in range(1, len(sentence_parts)):
        previous = rewritten_parts[-1]
        current = sentence_parts[index]
        if _has_terminal_punctuation(previous) and _looks_like_participial_fragment(current):
            repaired = _repair_participial_fragment(previous, current)
            if repaired and _normalize_text(repaired) != _normalize_text(current):
                rewritten_parts.append(repaired)
                repaired_any = True
                continue
        rewritten_parts.append(current)
    return _normalize_text(" ".join(rewritten_parts)), repaired_any


def _sentence_has_dialogue_or_mechanics(sentence: str) -> bool:
    clean = _normalize_text(sentence)
    if not clean:
        return True
    lowered = clean.lower()
    if any(ch in clean for ch in ('"', "“", "”")):
        return True
    if re.search(r"(^|[\s(])'[^']{1,120}'", clean):
        return True
    if clean.startswith("- ") or clean.startswith("—"):
        return True
    return any(marker in lowered for marker in _MICRO_SMOOTH_COMBAT_MECHANICAL_MARKERS)


def _can_micro_merge_sentence_pair(first: str, second: str) -> bool:
    first_clean = _normalize_text(first)
    second_clean = _normalize_text(second)
    if not first_clean or not second_clean:
        return False
    if _sentence_has_dialogue_or_mechanics(first_clean) or _sentence_has_dialogue_or_mechanics(second_clean):
        return False

    first_core = first_clean.rstrip(".!?").strip()
    second_core = second_clean.rstrip(".!?").strip()
    if not first_core or not second_core:
        return False
    if len(first_core) > _MICRO_SMOOTH_SHORT_SENTENCE_LEN or len(second_core) > _MICRO_SMOOTH_SHORT_SENTENCE_LEN:
        return False

    first_low = f" {first_core.lower()} "
    second_low = f" {second_core.lower()} "
    if any(marker in first_low for marker in _MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS):
        return False
    if any(marker in second_low for marker in _MICRO_SMOOTH_CLAUSE_HEAVY_MARKERS):
        return False
    if any(phrase in second_low for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
        return False
    if re.search(r"\b(he|she|it|you|we|i|him|her|them|our|your|my)\b", second_core, flags=re.IGNORECASE):
        return False
    if not (
        re.match(r"^they\b", first_core, flags=re.IGNORECASE)
        and (
            re.match(r"^they\b", second_core, flags=re.IGNORECASE)
            or re.match(r"^their\s+[A-Za-z][A-Za-z' -]{0,40}\s+[A-Za-z][A-Za-z'-]+\b", second_core, flags=re.IGNORECASE)
        )
    ):
        return False
    return True


def _merge_short_same_anchor_sentences(first: str, second: str) -> str | None:
    if not _can_micro_merge_sentence_pair(first, second):
        return None
    first_core = _normalize_text(first).rstrip(".!?").strip()
    second_core = _normalize_text(second).rstrip(".!?").strip()

    first_they = re.match(r"^(They)\s+(.+)$", first_core, flags=re.IGNORECASE)
    if not first_they:
        return None
    first_subject = first_they.group(1)
    first_predicate = first_they.group(2).strip()
    if not first_predicate:
        return None

    second_they = re.match(r"^(They)\s+(.+)$", second_core, flags=re.IGNORECASE)
    if second_they:
        second_predicate = second_they.group(2).strip()
        if not second_predicate:
            return None
        merged = f"{first_subject} {first_predicate}, then {second_predicate}"
        normalized = _normalize_terminal_punctuation(merged)
        if len(normalized.rstrip(".!?")) > _MICRO_SMOOTH_MAX_COMBINED_LEN:
            return None
        if any(phrase in normalized.lower() for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
            return None
        return normalized

    second_possessive = re.match(
        r"^Their\s+([A-Za-z][A-Za-z' -]{0,40})\s+([A-Za-z][A-Za-z'-]*)\b(.*)$",
        second_core,
        flags=re.IGNORECASE,
    )
    if not second_possessive:
        return None
    noun_phrase = _normalize_text(second_possessive.group(1))
    finite_verb = second_possessive.group(2).lower()
    remainder = _normalize_text(second_possessive.group(3))
    participle = _THIRD_PERSON_TO_PARTICIPLE.get(finite_verb)
    if not noun_phrase or not participle:
        return None

    tail = f"their {noun_phrase} {participle}{(' ' + remainder) if remainder else ''}"
    if any(phrase in tail.lower() for phrase in _MICRO_SMOOTH_BANNED_TAIL_PHRASES):
        return None
    merged = _normalize_terminal_punctuation(f"{first_subject} {first_predicate}, {tail}")
    if len(merged.rstrip(".!?")) > _MICRO_SMOOTH_MAX_COMBINED_LEN:
        return None
    return merged


def _micro_smooth_post_repair_sentences(text: str) -> tuple[str, bool]:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text, False
    sentence_parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean_text) if part.strip()]
    if len(sentence_parts) < 2:
        return clean_text, False

    merged_any = False
    rewritten_parts: List[str] = []
    idx = 0
    while idx < len(sentence_parts):
        current = sentence_parts[idx]
        if merged_any or idx >= len(sentence_parts) - 1:
            rewritten_parts.append(current)
            idx += 1
            continue
        nxt = sentence_parts[idx + 1]
        merged = _merge_short_same_anchor_sentences(current, nxt)
        if not merged:
            rewritten_parts.append(current)
            idx += 1
            continue
        rewritten_parts.append(merged)
        merged_any = True
        idx += 2

    return _normalize_text(" ".join(rewritten_parts)), merged_any


def _decompress_overpacked_sentences(text: str) -> str:
    clean_text = str(text or "").strip()
    if not clean_text:
        return clean_text
    if not any(marker in clean_text for marker in (",", ";", " hinting at ", " suggesting ", " which could ", " that could ")):
        return clean_text

    participles = (
        "intertwining",
        "drawing",
        "hinting",
        "suggesting",
        "making",
        "indicating",
        "offering",
        "creating",
        "revealing",
        "urging",
        "watching",
    )
    implication_phrases = (
        "hinting at",
        "suggesting",
        "making a tempting opportunity",
        "which could",
        "that could hold vital implications",
    )
    clause_markers = (" while ", " and ", " but ", ";", ":")
    sentence_parts = re.split(r"(?<=[.!?])\s+", clean_text)
    rewritten_parts: List[str] = []

    for raw_sentence in sentence_parts:
        sentence = raw_sentence.strip()
        if not sentence:
            continue
        core = sentence.rstrip(".!?").strip()
        if not core:
            rewritten_parts.append(sentence)
            continue

        rewritten = False
        punct = sentence[-1] if sentence[-1] in ".!?" else "."

        # Pattern B: semicolon-based explicit alternatives.
        if ";" in core:
            left, right = core.split(";", 1)
            left_clean = _normalize_terminal_punctuation(left)
            right_clean = _normalize_text(right)
            if (
                left_clean
                and right_clean
                and (
                    re.search(r"\bone\s+is\b", right_clean, flags=re.IGNORECASE)
                    or re.search(r"\bone\b[^.]{0,120}\bthe other\b", right_clean, flags=re.IGNORECASE)
                )
            ):
                alternatives = re.split(r",\s*(?=(?:the other|another)\b)", right_clean, maxsplit=1, flags=re.IGNORECASE)
                if len(alternatives) == 2:
                    first_alt = _normalize_terminal_punctuation(_capitalize_sentence_fragment(alternatives[0]))
                    second_alt = _normalize_terminal_punctuation(_capitalize_sentence_fragment(alternatives[1]))
                    if first_alt and second_alt:
                        rewritten_parts.extend([left_clean, first_alt, second_alt])
                        rewritten = True
                else:
                    right_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(right_clean))
                    if right_sentence:
                        rewritten_parts.extend([left_clean, right_sentence])
                        rewritten = True

        if rewritten:
            continue

        # Pattern A: overpacked participial tail after comma.
        participle_match = re.search(
            rf",\s*((?:{'|'.join(re.escape(p) for p in participles)})\b[^.!?]*)$",
            core,
            flags=re.IGNORECASE,
        )
        if participle_match:
            prefix = core[: participle_match.start()].strip(" ,;")
            tail = participle_match.group(1).strip(" ,;")
            long_or_multi_clause = len(core) > 140 or any(marker in core.lower() for marker in clause_markers)
            if prefix and tail and long_or_multi_clause:
                first_sentence = _normalize_terminal_punctuation(prefix)
                second_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(tail))
                if first_sentence and second_sentence:
                    rewritten_parts.extend([first_sentence, second_sentence])
                    rewritten = True

        if rewritten:
            continue

        # Pattern C: implication phrase appended to a physical/scene clause.
        lowered_core = core.lower()
        implication_pos = -1
        implication_phrase = ""
        for phrase in implication_phrases:
            token = f" {phrase} "
            idx = lowered_core.find(token)
            if idx == -1:
                idx = lowered_core.find(f", {phrase} ")
            if idx != -1:
                implication_pos = idx + (2 if lowered_core[idx : idx + 2] == ", " else 1)
                implication_phrase = phrase
                break
        if implication_pos > 0 and len(core) > 120:
            prefix = core[:implication_pos].rstrip(" ,;")
            tail = core[implication_pos:].lstrip(" ,;")
            if implication_phrase and prefix and tail:
                first_sentence = _normalize_terminal_punctuation(prefix)
                second_sentence = _normalize_terminal_punctuation(_capitalize_sentence_fragment(tail))
                if first_sentence and second_sentence:
                    rewritten_parts.extend([first_sentence, second_sentence])
                    rewritten = True

        if not rewritten:
            rewritten_parts.append(sentence if _has_terminal_punctuation(sentence) else f"{core}{punct}")

    return _normalize_text(" ".join(rewritten_parts))


def _final_emission_fast_path_eligible(out: Dict[str, Any]) -> bool:
    if not isinstance(out, dict):
        return False
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    if meta.get("final_route") != "accept_candidate":
        return False
    if meta.get("response_type_candidate_ok") is False:
        return False
    if meta.get("answer_completeness_failed") or meta.get("narrative_authority_failed"):
        return False
    if meta.get("fallback_behavior_failed") or meta.get("fallback_behavior_repaired"):
        return False
    if meta.get("fallback_behavior_uncertainty_active"):
        return False
    if meta.get("response_type_repair_used"):
        return False
    if any(
        meta.get(key)
        for key in (
            "answer_completeness_repaired",
            "response_delta_repaired",
            "social_response_structure_repair_applied",
            "tone_escalation_repaired",
            "anti_railroading_repaired",
            "context_separation_repaired",
            "player_facing_narration_purity_repaired",
            "answer_shape_primacy_repaired",
            "candidate_quality_degraded",
        )
    ):
        return False
    if str(meta.get("speaker_contract_enforcement_reason") or "").strip():
        return False
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    if any(
        ("fallback" in tag) or ("retry" in tag)
        for tag in tags
    ):
        return False
    icv = meta.get("interaction_continuity_validation")
    if not isinstance(icv, dict):
        md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
        em = md.get("emission_debug") if isinstance(md.get("emission_debug"), dict) else {}
        icv = em.get("interaction_continuity_validation")
    if isinstance(icv, dict) and icv.get("ok") is False:
        return False
    return True


_FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN: frozenset[str] = frozenset(
    {
        "mutation_before_or_during_gate_entry",
        "mutation_inside_gate_or_finalize",
        "mutation_unknown",
    }
)


def _upstream_fallback_canonical_provenance(out: Dict[str, Any]) -> Dict[str, Any] | None:
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov = md.get(METADATA_KEY)
    if isinstance(prov, dict) and str(prov.get("source") or "") == "fallback":
        return prov
    return None


def _apply_upstream_fallback_pregate_containment(out: Dict[str, Any]) -> bool:
    """When canonical provenance shows gate-entry drift vs selector, restore selector text (Block I)."""
    prov = _upstream_fallback_canonical_provenance(out)
    if not prov:
        return False
    original_fp = str(prov.get("content_fingerprint") or "")
    if not original_fp or prov.get("gate_entry_vs_selector_match") is not False:
        return False
    snap = str(prov.get("selector_player_facing_text") or "")
    if not snap or fingerprint_player_facing(snap) != original_fp:
        return False
    out["player_facing_text"] = snap
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov2 = dict(md.get(METADATA_KEY) or prov)
    prov2["overwrite_containment_applied"] = "pre_gate"
    out["metadata"] = {**md, METADATA_KEY: prov2}
    print("FALLBACK OVERWRITE CONTAINED: pre-gate")
    record_final_emission_gate_entry(out)
    return True


def _finalize_upstream_fallback_overwrite_containment(
    out: Dict[str, Any],
    *,
    pre_gate_normalized: str,
) -> bool:
    """When exit trace proves post-selector divergence, revert to selector snapshot with sanitizer-only cleanup."""
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov = md.get(METADATA_KEY)
    if not isinstance(prov, dict) or str(prov.get("source") or "") != "fallback":
        return False
    if not prov.get("mismatch_detected"):
        return False
    hint = str(prov.get("mutation_hint") or "")
    if hint not in _FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN:
        return False
    snap = str(prov.get("selector_player_facing_text") or "")
    original_fp = str(prov.get("content_fingerprint") or "")
    if not snap or not original_fp or fingerprint_player_facing(snap) != original_fp:
        return False
    snap_san = _sanitize_output_text(snap)
    if fingerprint_player_facing(snap_san) == original_fp:
        chosen = snap_san
    elif fingerprint_player_facing(snap) == original_fp:
        chosen = snap
    else:
        chosen = snap_san
    out["player_facing_text"] = chosen
    gate_norm = _normalize_text(chosen)
    fem = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    contained_kind = (
        "in_gate_finalize"
        if hint in ("mutation_inside_gate_or_finalize", "mutation_unknown")
        else "pre_gate"
    )
    out["_final_emission_meta"] = {
        **fem,
        "fallback_overwrite_contained": contained_kind,
        "fallback_overwrite_finalize_containment": True,
        "post_gate_mutation_detected": pre_gate_normalized != gate_norm,
        "final_text_preview": (gate_norm[:120] + "…") if len(gate_norm) > 120 else gate_norm,
    }
    print(
        "FALLBACK OVERWRITE CONTAINED: in-gate/finalize"
        if contained_kind == "in_gate_finalize"
        else "FALLBACK OVERWRITE CONTAINED: pre-gate"
    )
    record_final_emission_gate_exit(out, final_normalized_text=gate_norm)
    md2 = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    prov3 = dict(md2.get(METADATA_KEY) or {})
    prov3["overwrite_containment_applied"] = contained_kind
    out["metadata"] = {**md2, METADATA_KEY: prov3}
    return True


def _finalize_emission_output(
    out: Dict[str, Any],
    *,
    pre_gate_text: str,
    fast_path: bool = False,
) -> Dict[str, Any]:
    final_text = str(out.get("player_facing_text") or "")
    sanitized_text = _sanitize_output_text(final_text)
    if fast_path:
        smoothed_text = sanitized_text
        fragment_repair_applied = False
        sentence_decompression_applied = False
        sentence_micro_smoothing_applied = False
    else:
        decompressed_text = _decompress_overpacked_sentences(sanitized_text)
        repaired_text = decompressed_text
        fragment_repair_applied = False
        if decompressed_text != sanitized_text:
            repaired_text, fragment_repair_applied = _repair_fragmentary_participial_splits(decompressed_text)
        smoothed_text, sentence_micro_smoothing_applied = _micro_smooth_post_repair_sentences(repaired_text)
        sentence_decompression_applied = decompressed_text != sanitized_text
    sanitization_applied = sanitized_text != final_text
    out["player_facing_text"] = smoothed_text

    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    meta["final_emission_fast_path_used"] = bool(fast_path)
    meta["output_sanitization_applied"] = sanitization_applied
    meta["sentence_decompression_applied"] = sentence_decompression_applied
    meta["sentence_fragment_repair_applied"] = fragment_repair_applied
    meta["sentence_micro_smoothing_applied"] = sentence_micro_smoothing_applied
    gate_out_text = _normalize_text(smoothed_text)
    meta["post_gate_mutation_detected"] = pre_gate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    out["_final_emission_meta"] = meta
    record_final_emission_gate_exit(out, final_normalized_text=gate_out_text)
    _finalize_upstream_fallback_overwrite_containment(out, pre_gate_normalized=pre_gate_text)
    return out


def _question_prompt_for_resolution(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    return str(
        resolution.get("prompt")
        or resolution.get("label")
        or ((resolution.get("metadata") or {}).get("player_input") if isinstance(resolution.get("metadata"), dict) else "")
        or ""
    ).strip()


def _speaker_label(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "The guard"
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    if name:
        return name
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        return npc_id.replace("_", " ").replace("-", " ").title()
    return "The guard"


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if not isinstance(item, str) or not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scene_inner(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, dict):
        return inner
    return scene


def _output_sentence(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def _lowercase_leading_alpha(text: str) -> str:
    if not text:
        return ""
    chars = list(text)
    for idx, ch in enumerate(chars):
        if ch.isalpha():
            chars[idx] = ch.lower()
            break
    return "".join(chars)


def _join_entity_clauses(first_clause: str, second_clause: str) -> str:
    first = _normalize_text(first_clause)
    second = _normalize_text(second_clause)
    if not first:
        return second
    if not second:
        return first

    # If first clause already contains "while", avoid stacking it
    if " while " in first.lower():
        return f"{first}, and {second}"
    return f"{first}, while {second}"


def _opening_scene_preference_active(session: Dict[str, Any] | None) -> bool:
    if not isinstance(session, dict):
        return False
    turn_counter = int(session.get("turn_counter", 0) or 0)
    visited_scene_ids = session.get("visited_scene_ids") if isinstance(session.get("visited_scene_ids"), list) else []
    return turn_counter <= 1 or (turn_counter == 0 and len(visited_scene_ids) <= 1)


_FAST_FALLBACK_NEUTRAL_BAD_JOIN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bholds;\s+beside it\b", flags=re.IGNORECASE),
    re.compile(r"\bholds;\s+beside them\b", flags=re.IGNORECASE),
    re.compile(r"\bholds;\s+beside\b", flags=re.IGNORECASE),
)

_FAST_FALLBACK_NEUTRAL_SUBJECT_VERB_RE = re.compile(
    r"^(?:"
    r"is|was|stands?|keeps?|watches?|glances?|lingers?|waits?|looks?|holds?|moves?|speaks?|says?|"
    r"turns?|steps?|calls?|shouts?|scans?|studies?|gestures?|rests?|leans?|hangs?|offers?|questions?"
    r")\b",
    flags=re.IGNORECASE,
)


def _default_fast_fallback_neutral_composition_meta() -> Dict[str, Any]:
    return {
        "fast_fallback_neutral_composition_checked": False,
        "fast_fallback_neutral_composition_applicable": False,
        "fast_fallback_neutral_composition_malformed_detected": False,
        "fast_fallback_neutral_composition_failure_reasons": [],
        "fast_fallback_neutral_composition_repaired": False,
        "fast_fallback_neutral_composition_repair_mode": None,
    }


def _merge_fast_fallback_neutral_composition_meta(meta: Dict[str, Any], dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "fast_fallback_neutral_composition_checked": bool(
                dbg.get("fast_fallback_neutral_composition_checked")
            ),
            "fast_fallback_neutral_composition_applicable": bool(
                dbg.get("fast_fallback_neutral_composition_applicable")
            ),
            "fast_fallback_neutral_composition_malformed_detected": bool(
                dbg.get("fast_fallback_neutral_composition_malformed_detected")
            ),
            "fast_fallback_neutral_composition_failure_reasons": list(
                dbg.get("fast_fallback_neutral_composition_failure_reasons") or []
            ),
            "fast_fallback_neutral_composition_repaired": bool(
                dbg.get("fast_fallback_neutral_composition_repaired")
            ),
            "fast_fallback_neutral_composition_repair_mode": dbg.get(
                "fast_fallback_neutral_composition_repair_mode"
            ),
        }
    )


def _fast_fallback_neutral_composition_applicable(
    gm_output: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    strict_social_active: bool,
) -> bool:
    if strict_social_active or not _opening_scene_preference_active(session):
        return False
    tags = [str(t) for t in ((gm_output or {}).get("tags") or []) if isinstance(t, str)]
    return any(tag in tags for tag in ("upstream_api_fast_fallback", "forced_retry_fallback", "retry_escape_hatch"))


def _fast_fallback_bare_actor_header_detected(text: str, actor_tokens: List[str]) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    lowered = clean.lower()
    for raw in actor_tokens:
        token = str(raw or "").strip().lower()
        if len(token) < 3:
            continue
        display = _title_case_anchor_phrase(token)
        if not display:
            continue
        prefix = f"{display.lower()} "
        if not lowered.startswith(prefix):
            continue
        remainder = clean[len(display) :].lstrip(" ,;:-")
        if not remainder:
            return True
        if _FAST_FALLBACK_NEUTRAL_SUBJECT_VERB_RE.match(remainder):
            return False
        if remainder[:1].islower():
            return False
        return True
    return False


def _fast_fallback_neutral_composition_failure_reasons(
    text: str,
    *,
    gm_output: Dict[str, Any] | None,
) -> List[str]:
    reasons: List[str] = []
    clean = _normalize_text(text)
    if not clean:
        return reasons
    contract = _resolve_scene_state_anchor_contract(gm_output)
    actor_tokens = [str(tok) for tok in ((contract or {}).get("actor_tokens") or []) if isinstance(tok, str)]
    if actor_tokens and _fast_fallback_bare_actor_header_detected(clean, actor_tokens):
        reasons.append("bare_actor_header")
    if any(pattern.search(clean) for pattern in _FAST_FALLBACK_NEUTRAL_BAD_JOIN_PATTERNS):
        reasons.append("fact_fragment_collision")
    return _dedupe_preserve_order(reasons)


def _fast_fallback_opening_clean_scene_summary(scene: Dict[str, Any] | None) -> str:
    inner = _scene_inner(scene)
    summary = _normalize_text(str(inner.get("summary") or ""))
    if not summary:
        return ""
    first = re.split(r"(?<=[.!?])\s+", summary, maxsplit=1)[0].strip()
    if not first:
        return ""
    if ";" in first:
        first = first.split(";", 1)[0].strip(" ,;:-")
    return _output_sentence(first)


def _fast_fallback_opening_detail_candidates(
    scene: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None,
) -> List[str]:
    contract = _resolve_scene_state_anchor_contract(gm_output)
    actor_tokens = [str(tok) for tok in ((contract or {}).get("actor_tokens") or []) if isinstance(tok, str)]
    details: List[str] = []
    for fact in _scene_visible_facts(scene):
        clean = _output_sentence(fact)
        if not clean:
            continue
        if any(pattern.search(clean) for pattern in _FAST_FALLBACK_NEUTRAL_BAD_JOIN_PATTERNS):
            continue
        if actor_tokens and _fast_fallback_bare_actor_header_detected(clean, actor_tokens):
            continue
        details.append(clean)
    return _dedupe_preserve_order(details)


def _build_fast_fallback_opening_scene_template(
    scene: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None,
    scene_id: str,
) -> str:
    lead = _fast_fallback_opening_clean_scene_summary(scene)
    details = _fast_fallback_opening_detail_candidates(scene, gm_output=gm_output)
    parts: List[str] = []
    if lead:
        parts.append(lead)
    if details:
        for detail in details:
            if lead and _normalize_text(detail).lower() == _normalize_text(lead).lower():
                continue
            parts.append(detail)
            break
    if parts:
        return _normalize_text(" ".join(parts[:2]))
    return _normalize_text(
        _global_narrative_fallback_stock_line(scene if isinstance(scene, dict) else None, scene_id=scene_id)
    )


def _apply_fast_fallback_neutral_composition_layer(
    text: str,
    *,
    gm_output: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
    strict_social_active: bool,
) -> tuple[str, Dict[str, Any]]:
    meta = _default_fast_fallback_neutral_composition_meta()
    if not _fast_fallback_neutral_composition_applicable(
        gm_output,
        session=session,
        strict_social_active=strict_social_active,
    ):
        return text, meta
    meta["fast_fallback_neutral_composition_checked"] = True
    meta["fast_fallback_neutral_composition_applicable"] = True
    reasons = _fast_fallback_neutral_composition_failure_reasons(text, gm_output=gm_output)
    if not reasons:
        return text, meta
    meta["fast_fallback_neutral_composition_malformed_detected"] = True
    meta["fast_fallback_neutral_composition_failure_reasons"] = reasons
    repaired = _build_fast_fallback_opening_scene_template(
        scene,
        gm_output=gm_output,
        scene_id=scene_id,
    )
    if repaired and _normalize_text(repaired) != _normalize_text(text):
        meta["fast_fallback_neutral_composition_repaired"] = True
        meta["fast_fallback_neutral_composition_repair_mode"] = "opening_scene_template"
        return repaired, meta
    return text, meta


def _scene_visible_facts(scene: Dict[str, Any] | None) -> List[str]:
    inner = _scene_inner(scene)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            out.append(clean)
    return _dedupe_preserve_order(out)


def _augment_scene_with_runtime_visible_leads(
    scene: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any] | None:
    if not isinstance(scene, dict):
        return scene
    if not isinstance(session, dict):
        return scene
    sid = str(scene_id or "").strip()
    if not sid:
        return scene
    runtime = get_scene_runtime(session, sid)
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if not isinstance(recent, list) or not recent:
        return scene

    extra_facts: List[str] = []
    for lead in recent[-4:]:
        if not isinstance(lead, dict):
            continue
        kind = str(lead.get("kind") or "").strip()
        if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
            continue
        subject = _normalize_text(lead.get("subject"))
        position = _normalize_text(lead.get("position"))
        if not subject:
            continue
        fact = f"{subject} lingers {position}" if position else f"{subject} lingers nearby"
        extra_facts.append(_output_sentence(fact))

    if not extra_facts:
        return scene

    if isinstance(scene.get("scene"), dict):
        outer = dict(scene)
        inner = dict(scene.get("scene") or {})
        existing = _scene_visible_facts(scene)
        inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
        outer["scene"] = inner
        return outer

    inner = dict(scene)
    existing = _scene_visible_facts(scene)
    inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
    return inner


def _passive_scene_pressure_due_for_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    if not isinstance(session, dict):
        return False
    sid = str(scene_id or "").strip()
    if not sid:
        return False
    runtime = get_scene_runtime(session, sid)
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    last_player_action_passive = bool(runtime.get("last_player_action_passive")) if isinstance(runtime, dict) else False
    if not last_player_action_passive and passive_streak <= 0:
        return False
    visible_low = " ".join(fact.lower() for fact in _scene_visible_facts(scene))
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    return bool(
        passive_streak >= 2
        or isinstance(recent, list)
        and any(isinstance(item, dict) for item in recent)
        or "guard" in visible_low
        or "watch" in visible_low
        or "missing patrol" in visible_low
        or "rumor" in visible_low
        or "rumour" in visible_low
    )


def _reply_already_has_concrete_interaction(text: str) -> bool:
    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)


def _passive_scene_pressure_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> List[tuple[str, str, str, str, str, str, Dict[str, Any]]]:
    if not _passive_scene_pressure_due_for_fallback(session=session, scene=scene, scene_id=scene_id):
        return []

    sid = str(scene_id or "").strip()
    runtime = get_scene_runtime(session, sid) if isinstance(session, dict) and sid else {}
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if isinstance(recent, list):
        for lead in reversed(recent[-4:]):
            if not isinstance(lead, dict):
                continue
            kind = str(lead.get("kind") or "").strip()
            if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
                continue
            subject = _normalize_text(lead.get("subject"))
            position = _normalize_text(lead.get("position"))
            if not subject:
                continue
            move_from = f" leaves {position} and" if position else ""
            if passive_streak >= 2:
                return [
                    (
                        _output_sentence(
                            f'{subject}{move_from} comes straight to you before the pause can settle. "Enough watching," they say. "Ask me now, or lose the trail."'
                        ),
                        "passive_scene_pressure",
                        "passive_scene_pressure_lead_figure",
                        "passive_scene_pressure_fallback",
                        "passive_scene_pressure_fallback",
                        "passive_scene_pressure:lead_figure",
                        _first_mention_composition_meta(),
                    )
                ]
            return [
                (
                    _output_sentence(
                        f'{subject}{move_from} cuts through the crowd and stops at your shoulder. "You\'re asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."'
                    ),
                    "passive_scene_pressure",
                    "passive_scene_pressure_lead_figure",
                    "passive_scene_pressure_fallback",
                    "passive_scene_pressure_fallback",
                    "passive_scene_pressure:lead_figure",
                    _first_mention_composition_meta(),
                )
            ]

    visible_facts = _scene_visible_facts(scene)
    visible_low = " ".join(fact.lower() for fact in visible_facts)
    if "guard" in visible_low and "missing patrol" in visible_low:
        if passive_streak >= 2:
            text = (
                'The same guard does not let the silence stand a second time. "No more watching," he says, '
                "closing the distance and jabbing a finger at the east-road line on the notice. "
                '"Either tell me who sent you, or get moving before that trail cools for good."'
            )
        else:
            text = (
                'A guard peels away from the notice board and squares up to you. "Standing still won\'t help that patrol," '
                'he says, stabbing two fingers at the posting. "Tell me what you know, or get on the east-road trail before it dies."'
            )
        return [
            (
                _output_sentence(text),
                "passive_scene_pressure",
                "passive_scene_pressure_guard_rumor",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure:guard_rumor",
                _first_mention_composition_meta(),
            )
        ]
    if "guard" in visible_low:
        text = (
            'A guard notices you lingering and comes over at once. "If you\'re waiting on trouble, it already passed the checkpoint," '
            'he says. "Take the east-road report or get clear."'
        )
        return [
            (
                _output_sentence(text),
                "passive_scene_pressure",
                "passive_scene_pressure_visible_figure",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure_fallback",
                "passive_scene_pressure:visible_figure",
                _first_mention_composition_meta(),
            )
        ]
    return [
        (
            _output_sentence(
                'The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. '
                '"Board, runner, or road," he says. "Pick one before the gate swallows the trail."'
            ),
            "passive_scene_pressure",
            "passive_scene_pressure_generic",
            "passive_scene_pressure_fallback",
            "passive_scene_pressure_fallback",
            "passive_scene_pressure:fallback",
            _first_mention_composition_meta(),
        )
    ]


def _visible_entity_catalog(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_ids = {
        str(item).strip()
        for item in (contract.get("visible_entity_ids") or [])
        if isinstance(item, str) and str(item).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    inner = _scene_inner(scene)
    addressables = inner.get("addressables") if isinstance(inner.get("addressables"), list) else []
    world_npcs = world.get("npcs") if isinstance(world, dict) and isinstance(world.get("npcs"), list) else []
    world_npc_map = {
        str(row.get("id") or "").strip(): row
        for row in world_npcs
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }

    ordered_rows: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _append_row(entity_id: str, row: Dict[str, Any] | None) -> None:
        if not entity_id or entity_id in seen or entity_id not in visible_ids:
            return
        seen.add(entity_id)
        base = row if isinstance(row, dict) else {}
        display_name = str(base.get("name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (base.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        normalized_aliases = alias_map.get(entity_id) if isinstance(alias_map.get(entity_id), list) else []
        ordered_aliases = _dedupe_preserve_order(
            [display_name]
            + aliases
            + [str(alias).strip() for alias in normalized_aliases if isinstance(alias, str) and str(alias).strip()]
        )
        if not display_name and ordered_aliases:
            display_name = ordered_aliases[0].title()
        role_hints = [
            str(role).strip()
            for role in (base.get("address_roles") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        world_row = world_npc_map.get(entity_id)
        if isinstance(world_row, dict):
            world_role = str(world_row.get("role") or "").strip()
            if world_role:
                role_hints.append(world_role)
        ordered_rows.append(
            {
                "entity_id": entity_id,
                "display_name": display_name or entity_id.replace("_", " ").title(),
                "aliases": ordered_aliases,
                "role_hints": _dedupe_preserve_order(role_hints),
            }
        )

    for row in addressables:
        if not isinstance(row, dict):
            continue
        _append_row(str(row.get("id") or "").strip(), row)

    for entity_id in sorted(visible_ids):
        _append_row(entity_id, world_npc_map.get(entity_id))

    return ordered_rows


def _rewrite_visible_fact_as_explicit_intro(display_name: str, fact_text: str, phrases: List[str]) -> str:
    fact = _output_sentence(fact_text)
    if not fact:
        return ""
    if fact.lower().startswith(display_name.lower()):
        return fact
    for phrase in phrases:
        clean_phrase = _normalize_text(phrase).lower()
        if not clean_phrase:
            continue
        for pattern in (
            rf"^(?:A|An|The)\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
            rf"^One\s+{re.escape(clean_phrase)}\b[\s,;:-]*(.*)$",
        ):
            match = re.match(pattern, fact, flags=re.IGNORECASE)
            if not match:
                continue
            remainder = (match.group(1) or "").strip()
            if not remainder:
                return _output_sentence(display_name)
            return _output_sentence(f"{display_name} {remainder}")
    return ""


def _scene_grounding_clause(visible_facts: List[str], blocked_phrases: List[str]) -> str:
    blocked = [phrase.lower() for phrase in blocked_phrases if phrase]
    for fact in visible_facts:
        if not fact:
            continue
        lowered = fact.lower()
        if any(phrase in lowered for phrase in blocked):
            continue
        return _lowercase_leading_alpha(fact.rstrip(".!?"))
    return ""


def _default_first_mention_composition_layers() -> Dict[str, Any]:
    return {"environment": None, "motion": None, "entities": []}


def _first_mention_composition_meta(
    *,
    used: bool = False,
    environment: str | None = None,
    motion: str | None = None,
    entities: List[str] | None = None,
) -> Dict[str, Any]:
    layers = _default_first_mention_composition_layers()
    if environment:
        layers["environment"] = environment
    if motion:
        layers["motion"] = motion
    if isinstance(entities, list):
        layers["entities"] = [str(entity).strip() for entity in entities if isinstance(entity, str) and str(entity).strip()]
    return {
        "first_mention_composition_used": used,
        "first_mention_composition_layers": layers,
    }


def _fact_matches_keywords(fact: str, keywords: tuple[str, ...]) -> bool:
    lowered = fact.lower()
    return any(keyword in lowered for keyword in keywords)


def _first_fact_matching_keywords(
    visible_facts: List[str],
    keywords: tuple[str, ...],
    *,
    excluded: set[str] | None = None,
) -> str:
    blocked = excluded or set()
    for fact in visible_facts:
        if not fact or fact in blocked:
            continue
        for segment in _fact_segments(fact):
            if segment in blocked:
                continue
            if _fact_matches_keywords(segment, keywords):
                return _output_sentence(segment)
        if _fact_matches_keywords(fact, keywords):
            return fact
    return ""


_ENTITY_COMPOSITION_PREDICATE_STARTS: tuple[tuple[str, str], ...] = (
    ("hangs back", "hangs back"),
    ("calls out", "calls"),
    ("is shouting", "shouts"),
    ("are shouting", "shouts"),
    ("is calling", "calls"),
    ("are calling", "calls"),
    ("is offering", "offers"),
    ("are offering", "offers"),
    ("is watching", "watches"),
    ("are watching", "watches"),
    ("is scanning", "scans"),
    ("are scanning", "scans"),
    ("is studying", "studies"),
    ("are studying", "studies"),
    ("is gesturing", "gestures"),
    ("are gesturing", "gestures"),
    ("is lingering", "lingers"),
    ("are lingering", "lingers"),
    ("is waiting", "waits"),
    ("are waiting", "waits"),
    ("is observing", "observes"),
    ("are observing", "observes"),
    ("is surveying", "surveys"),
    ("are surveying", "surveys"),
    ("is exchanging", "exchanges"),
    ("are exchanging", "exchanges"),
    ("holds", "holds"),
    ("hold", "holds"),
    ("watches", "watches"),
    ("watch", "watches"),
    ("scans", "scans"),
    ("scan", "scans"),
    ("studies", "studies"),
    ("study", "studies"),
    ("shouts", "shouts"),
    ("shout", "shouts"),
    ("calls", "calls"),
    ("call", "calls"),
    ("offers", "offers"),
    ("offer", "offers"),
    ("gestures", "gestures"),
    ("gesture", "gestures"),
    ("lingers", "lingers"),
    ("linger", "lingers"),
    ("waits", "waits"),
    ("wait", "waits"),
    ("observes", "observes"),
    ("observe", "observes"),
    ("surveys", "surveys"),
    ("survey", "surveys"),
    ("exchanges", "exchanges"),
    ("exchange", "exchanges"),
    ("stands", "stands"),
    ("stand", "stands"),
    ("keeps", "keeps"),
    ("keep", "keeps"),
    ("looks", "looks"),
    ("look", "looks"),
    ("glances", "glances"),
    ("glance", "glances"),
    ("murmurs", "murmurs"),
    ("murmur", "murmurs"),
    ("whispers", "whispers"),
    ("whisper", "whispers"),
)
_LOW_INFO_ENTITY_PREDICATE_RE = re.compile(
    r"^(stands|shouts|watches|lingers|waits|scans|gestures)(?:\s+(nearby|there|quietly|silently|still|alone))?$",
    flags=re.IGNORECASE,
)
_ENTITY_DESCRIPTOR_STOPWORDS = {
    "captain",
    "guard",
    "runner",
    "informant",
    "watcher",
    "stranger",
    "refugee",
    "figure",
    "nearby",
    "still",
}
_ENTITY_ROLE_DETAIL_PHRASE_MAP: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("choke", "gate"), "holds the choke at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("line", "gate"), "holds the line at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("crowd",), "scans the crowd at the gate"),
    (("guard", "watchman", "sentry", "guardsman", "captain"), ("gate",), "watches the gate"),
    (("runner", "informant"), ("stew", "rumor"), "calls over the noise with offers of hot stew and rumor"),
    (("runner", "informant"), ("stew",), "calls over the noise with offers of hot stew"),
    (("runner", "informant"), ("crowd",), "calls over the crowd"),
    (("watcher",), ("crowd",), "lingers at the edge of the crowd"),
    (("stranger", "refugee"), ("refugee", "crowd"), "hangs back from the press of refugees"),
    (("stranger", "refugee"), ("crowd",), "hangs back from the crowd"),
)


def _phrase_present(text: str, phrase: str) -> bool:
    clean_text = _normalize_text(text).lower()
    clean_phrase = _normalize_text(phrase).lower()
    if not clean_text or not clean_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(clean_phrase)}(?!\w)", clean_text))


def _entity_descriptor_tokens(display_name: str, aliases: List[str]) -> List[str]:
    tokens: List[str] = []
    for raw in [display_name] + list(aliases):
        for token in re.findall(r"[a-zA-Z][a-zA-Z'-]+", raw.lower()):
            if len(token) < 5 or token in _ENTITY_DESCRIPTOR_STOPWORDS:
                continue
            tokens.append(token)
    return _dedupe_preserve_order(tokens)


def _role_forms(role: str) -> List[str]:
    clean = _normalize_text(role).lower()
    if not clean:
        return []
    forms = [clean]
    if clean.endswith("y") and len(clean) > 1:
        forms.append(f"{clean[:-1]}ies")
    elif clean.endswith(("s", "x", "z", "ch", "sh")):
        forms.append(f"{clean}es")
    else:
        forms.append(f"{clean}s")
    return _dedupe_preserve_order(forms)


def _fact_segments(fact_text: str) -> List[str]:
    clean = _output_sentence(fact_text).rstrip(".!?")
    if not clean:
        return []
    segments = re.split(r"[;:]|(?<=[.!?])\s+", clean)
    return [segment.strip(" ,") for segment in segments if segment.strip(" ,")]


def _extract_leading_subject_and_predicate(segment: str) -> tuple[str, str]:
    clean = _normalize_text(segment)
    if not clean:
        return "", ""
    lowered = clean.lower()
    for predicate_start, _canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        match = re.search(rf"\b{re.escape(predicate_start)}\b", lowered)
        if not match:
            continue
        subject = clean[: match.start()].strip(" ,")
        predicate = clean[match.start() :].strip(" ,")
        if not subject or not predicate:
            continue
        if len(subject.split()) > 9:
            continue
        return subject, predicate
    return "", ""


def _subject_matches_entity(
    subject: str,
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    descriptor_tokens: List[str],
) -> bool:
    lowered_subject = _normalize_text(subject).lower()
    if not lowered_subject:
        return False
    for phrase in _dedupe_preserve_order([display_name] + aliases):
        if _phrase_present(lowered_subject, phrase):
            return True
    for role in role_hints:
        for form in _role_forms(role):
            if _phrase_present(lowered_subject, form):
                return True
    return any(token in lowered_subject for token in descriptor_tokens)


def _singularize_entity_predicate(predicate: str) -> str:
    clean = _normalize_text(predicate)
    if not clean:
        return ""
    lowered = clean.lower()
    replacements = (
        ("are now ", "is now "),
        ("are ", "is "),
        ("hang back", "hangs back"),
        ("hold ", "holds "),
        ("watch ", "watches "),
        ("scan ", "scans "),
        ("study ", "studies "),
        ("shout ", "shouts "),
        ("call ", "calls "),
        ("offer ", "offers "),
        ("gesture ", "gestures "),
        ("linger ", "lingers "),
        ("wait ", "waits "),
        ("observe ", "observes "),
        ("survey ", "surveys "),
        ("exchange ", "exchanges "),
        ("stand ", "stands "),
        ("keep ", "keeps "),
        ("look ", "looks "),
        ("glance ", "glances "),
        ("murmur ", "murmurs "),
        ("whisper ", "whispers "),
    )
    for old, new in replacements:
        if lowered == old.strip():
            return new.strip()
        if lowered.startswith(old):
            return f"{new}{clean[len(old):]}".strip()
    return clean


def _predicate_after_display_name(display_name: str, sentence: str) -> str:
    clean = _output_sentence(sentence).rstrip(".!?")
    if not clean:
        return ""
    lowered_clean = clean.lower()
    lowered_name = display_name.lower()
    if not lowered_clean.startswith(lowered_name):
        return ""
    return clean[len(display_name) :].strip(" ,;:-")


def _entity_predicate_signature(predicate: str) -> tuple[str, bool]:
    clean = _normalize_text(predicate).lower()
    if not clean:
        return "", True
    for predicate_start, canonical in _ENTITY_COMPOSITION_PREDICATE_STARTS:
        if clean == predicate_start or clean.startswith(f"{predicate_start} "):
            return canonical, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))
    first_token = clean.split()[0]
    return first_token, bool(_LOW_INFO_ENTITY_PREDICATE_RE.match(clean))


def _composition_candidate(
    *,
    display_name: str,
    predicate: str,
    source_rank: int,
    source_index: int,
    fact_backed: bool,
) -> Dict[str, Any] | None:
    clean_predicate = _normalize_text(predicate).rstrip(".!?")
    if not clean_predicate:
        return None
    verb_key, low_info = _entity_predicate_signature(clean_predicate)
    detail_bonus = 0 if low_info else min(len(clean_predicate.split()), 8)
    return {
        "clause": f"{display_name} {clean_predicate}",
        "verb_key": verb_key,
        "low_info": low_info,
        "fact_backed": fact_backed,
        "score": (source_rank * 100) + detail_bonus,
        "source_index": source_index,
    }


def _generic_entity_intro_predicate(
    *,
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> str:
    signal_text = " ".join(fact.lower() for fact in composition_facts if isinstance(fact, str))
    role_set = {role.lower() for role in role_hints if isinstance(role, str) and role}
    for required_roles, required_tokens, predicate in _ENTITY_ROLE_DETAIL_PHRASE_MAP:
        if role_set.isdisjoint(required_roles):
            continue
        if all(token in signal_text for token in required_tokens):
            return predicate
    if "crowd" in signal_text:
        return "watches the crowd" if slot_index == 0 else "lingers at the edge of the crowd"
    if "gate" in signal_text:
        return "stands at the gate"
    return "watches nearby" if slot_index == 0 else "lingers nearby"


def _entity_clause_candidates(
    *,
    display_name: str,
    aliases: List[str],
    role_hints: List[str],
    composition_facts: List[str],
    slot_index: int,
) -> List[Dict[str, Any]]:
    explicit_phrases = _dedupe_preserve_order([display_name] + aliases + role_hints)
    descriptor_tokens = _entity_descriptor_tokens(display_name, aliases)
    candidates: List[Dict[str, Any]] = []
    seen_clauses: set[str] = set()

    for fact_index, fact in enumerate(composition_facts):
        explicit_sentence = ""
        if fact.lower().startswith(display_name.lower()):
            explicit_sentence = fact
        else:
            explicit_sentence = _rewrite_visible_fact_as_explicit_intro(display_name, fact, explicit_phrases)
        if explicit_sentence:
            predicate = _predicate_after_display_name(display_name, explicit_sentence)
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=predicate,
                source_rank=3,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)
        for segment in _fact_segments(fact):
            subject, predicate = _extract_leading_subject_and_predicate(segment)
            if not subject or not predicate:
                continue
            if not _subject_matches_entity(
                subject,
                display_name=display_name,
                aliases=aliases,
                role_hints=role_hints,
                descriptor_tokens=descriptor_tokens,
            ):
                continue
            candidate = _composition_candidate(
                display_name=display_name,
                predicate=_singularize_entity_predicate(predicate),
                source_rank=2,
                source_index=fact_index,
                fact_backed=True,
            )
            if candidate and candidate["clause"] not in seen_clauses:
                seen_clauses.add(candidate["clause"])
                candidates.append(candidate)

    generic_candidate = _composition_candidate(
        display_name=display_name,
        predicate=_generic_entity_intro_predicate(
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=slot_index,
        ),
        source_rank=1,
        source_index=len(composition_facts),
        fact_backed=False,
    )
    if generic_candidate and generic_candidate["clause"] not in seen_clauses:
        candidates.append(generic_candidate)

    candidates.sort(
        key=lambda item: (
            -int(item.get("score", 0)),
            int(item.get("source_index", 10**6)),
            len(str(item.get("clause") or "")),
        )
    )
    return candidates


def _visible_safe_scene_composition_facts(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[str]:
    inner = _scene_inner(scene)
    raw_candidates: List[str] = list(_scene_visible_facts(scene))
    summary = _output_sentence(str(inner.get("summary") or ""))
    if summary:
        raw_candidates.append(summary)
    raw_journal_seed_facts = inner.get("journal_seed_facts") if isinstance(inner.get("journal_seed_facts"), list) else []
    for item in raw_journal_seed_facts:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            raw_candidates.append(clean)

    visible_safe_facts: List[str] = []
    for candidate in _dedupe_preserve_order(raw_candidates):
        validation = validate_player_facing_visibility(
            candidate,
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            visible_safe_facts.append(candidate)
    return visible_safe_facts


def _build_composed_scene_intro(
    narration_visibility: Dict[str, Any],
    visible_entities: List[str],
    composition_facts: List[str],
    scene_context: Dict[str, Any],
) -> str | None:
    scene_context["composition_layers"] = _default_first_mention_composition_layers()
    if not isinstance(narration_visibility, dict) or not composition_facts or not visible_entities:
        return None

    environment = _first_fact_matching_keywords(
        composition_facts,
        (
            "rain",
            "snow",
            "wind",
            "fog",
            "mist",
            "smoke",
            "ash",
            "mud",
            "muddy",
            "stone",
            "gate",
            "wall",
            "square",
            "yard",
            "district",
            "alley",
            "alleyway",
            "tavern",
            "banner",
            "banners",
            "ground",
            "earth",
            "puddle",
            "puddles",
            "crate",
            "crates",
            "path",
            "thicket",
            "milestone",
            "millstone",
            "underbrush",
            "breeze",
        ),
    )
    if not environment:
        return None

    motion = _first_fact_matching_keywords(
        composition_facts,
        (
            "crowd",
            "refugee",
            "refugees",
            "wagon",
            "wagons",
            "traffic",
            "patron",
            "patrons",
            "townsfolk",
            "onlookers",
            "voices",
            "whisper",
            "whispers",
            "murmur",
            "murmurs",
            "shout",
            "shouts",
            "queue",
            "presses",
            "press in",
            "pushes",
            "scan",
            "scans",
            "glance",
            "glances",
            "watch newcomers",
            "tension",
            "tense",
            "agitation",
            "unrest",
            "shift uneasily",
        ),
        excluded={environment},
    )

    entity_rows_by_display_name = (
        scene_context.get("entity_rows_by_display_name")
        if isinstance(scene_context.get("entity_rows_by_display_name"), dict)
        else {}
    )
    visible_entity_ids = {
        str(entity_id).strip()
        for entity_id in (narration_visibility.get("visible_entity_ids") or [])
        if isinstance(entity_id, str) and str(entity_id).strip()
    }
    selected_entity_names: List[str] = []
    for entity_name in visible_entities:
        clean_name = _normalize_text(entity_name)
        if not clean_name or clean_name in selected_entity_names:
            continue
        row = entity_rows_by_display_name.get(clean_name) if isinstance(entity_rows_by_display_name, dict) else None
        entity_id = str((row or {}).get("entity_id") or "").strip() if isinstance(row, dict) else ""
        if visible_entity_ids and entity_id and entity_id not in visible_entity_ids:
            continue
        selected_entity_names.append(clean_name)
    if not selected_entity_names:
        return None

    selected_entity_clauses: List[Dict[str, Any]] = []
    used_verb_keys: set[str] = set()
    for index, entity_name in enumerate(selected_entity_names):
        row = entity_rows_by_display_name.get(entity_name) if isinstance(entity_rows_by_display_name, dict) else {}
        aliases = [
            str(alias).strip()
            for alias in ((row or {}).get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in ((row or {}).get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        clause_candidates = _entity_clause_candidates(
            display_name=entity_name,
            aliases=aliases,
            role_hints=role_hints,
            composition_facts=composition_facts,
            slot_index=index,
        )
        chosen_candidate: Dict[str, Any] | None = None
        for candidate in clause_candidates:
            verb_key = str(candidate.get("verb_key") or "")
            if not selected_entity_clauses:
                chosen_candidate = candidate
                break
            if verb_key and verb_key in used_verb_keys and bool(candidate.get("low_info")):
                continue
            if len(selected_entity_clauses) >= 1 and not bool(candidate.get("fact_backed")):
                continue
            chosen_candidate = candidate
            break
        if not chosen_candidate:
            continue
        selected_entity_clauses.append(
            {
                "entity_name": entity_name,
                "clause": str(chosen_candidate.get("clause") or ""),
                "verb_key": str(chosen_candidate.get("verb_key") or ""),
                "fact_backed": bool(chosen_candidate.get("fact_backed")),
                "low_info": bool(chosen_candidate.get("low_info")),
            }
        )
        verb_key = str(chosen_candidate.get("verb_key") or "")
        if verb_key:
            used_verb_keys.add(verb_key)
        if len(selected_entity_clauses) >= 2:
            break
    if not selected_entity_clauses:
        return None

    entity_sentence = selected_entity_clauses[0]["clause"]
    if len(selected_entity_clauses) > 1:
        first_clause = selected_entity_clauses[0]
        second_clause = selected_entity_clauses[1]
        if (
            first_clause["verb_key"]
            and second_clause["verb_key"]
            and first_clause["verb_key"] != second_clause["verb_key"]
            and not second_clause["low_info"]
        ):
            entity_sentence = _join_entity_clauses(
                first_clause["clause"],
                second_clause["clause"],
            )

    scene_sentence = environment.rstrip(".!?")
    if motion:
        scene_sentence = f"{scene_sentence} while {_lowercase_leading_alpha(motion.rstrip('.!?'))}"

    scene_context["composition_layers"] = {
        "environment": environment,
        "motion": motion or None,
        "entities": [str(item.get("entity_name") or "") for item in selected_entity_clauses if str(item.get("entity_name") or "")],
    }
    return f"{_output_sentence(scene_sentence)} {_output_sentence(entity_sentence)}".strip()


def _grounded_scene_intro_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    active_interlocutor: str,
) -> List[tuple[str, str, str, str, str, str, Dict[str, Any]]]:
    visible_facts = _scene_visible_facts(scene)
    composition_facts = _visible_safe_scene_composition_facts(session=session, scene=scene, world=world)
    entity_rows = _visible_entity_catalog(session=session, scene=scene, world=world)
    if not entity_rows and not composition_facts and not visible_facts:
        return []

    narration_visibility = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    inner = _scene_inner(scene)
    scene_location = str(inner.get("location") or inner.get("id") or "").strip()
    prioritized_entities: List[Dict[str, Any]] = []
    if active_interlocutor:
        for row in entity_rows:
            if str(row.get("entity_id") or "").strip() == active_interlocutor:
                prioritized_entities.append(row)
                break
    for row in entity_rows:
        if row not in prioritized_entities:
            prioritized_entities.append(row)

    fallback_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []
    composed_scene_context: Dict[str, Any] = {
        "scene_location": scene_location,
        "entity_rows_by_display_name": {
            str(row.get("display_name") or "").strip(): row
            for row in prioritized_entities
            if isinstance(row, dict) and str(row.get("display_name") or "").strip()
        },
    }
    composed_scene_intro = _build_composed_scene_intro(
        narration_visibility,
        [str(row.get("display_name") or "").strip() for row in prioritized_entities if str(row.get("display_name") or "").strip()],
        composition_facts,
        composed_scene_context,
    )
    composed_layers = composed_scene_context.get("composition_layers")
    if composed_scene_intro and isinstance(composed_layers, dict):
        fallback_candidates.append(
            (
                composed_scene_intro,
                "visible_scene_composed_intro",
                "first_mention_composed_scene_intro",
                "composed_visible_scene_intro",
                "composed_visible_scene_intro",
                "visible_scene_composed_intro",
                _first_mention_composition_meta(
                    used=True,
                    environment=str(composed_layers.get("environment") or "") or None,
                    motion=str(composed_layers.get("motion") or "") or None,
                    entities=composed_layers.get("entities") if isinstance(composed_layers.get("entities"), list) else [],
                ),
            )
        )

    for row in prioritized_entities:
        entity_id = str(row.get("entity_id") or "").strip()
        display_name = str(row.get("display_name") or "").strip()
        aliases = [
            str(alias).strip()
            for alias in (row.get("aliases") or [])
            if isinstance(alias, str) and str(alias).strip()
        ]
        role_hints = [
            str(role).strip()
            for role in (row.get("role_hints") or [])
            if isinstance(role, str) and str(role).strip()
        ]
        subject_phrases = _dedupe_preserve_order(aliases + role_hints)

        explicit_fact_intro = ""
        for fact in visible_facts:
            explicit_fact_intro = _rewrite_visible_fact_as_explicit_intro(display_name, fact, subject_phrases)
            if explicit_fact_intro:
                break
        if explicit_fact_intro:
            fallback_candidates.append(
                (
                    explicit_fact_intro,
                    "visible_scene_explicit_intro",
                    "first_mention_explicit_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    "explicit_visible_entity_scene_intro",
                    f"visible_entity:{entity_id}",
                    _first_mention_composition_meta(),
                )
            )

        grounding_clause = _scene_grounding_clause(visible_facts, subject_phrases)
        if scene_location and grounding_clause:
            generic_intro = f"{display_name} stands in {scene_location} while {grounding_clause}."
        elif scene_location:
            generic_intro = f"{display_name} stands in {scene_location}."
        elif grounding_clause:
            generic_intro = f"{display_name} stands nearby while {grounding_clause}."
        else:
            generic_intro = f"{display_name} stands nearby."
        fallback_candidates.append(
            (
                _output_sentence(generic_intro),
                "visible_scene_explicit_intro",
                "first_mention_explicit_scene_intro",
                "explicit_visible_entity_scene_intro",
                "explicit_visible_entity_scene_intro",
                f"visible_entity:{entity_id}",
                _first_mention_composition_meta(),
            )
        )

    for index, fact in enumerate(visible_facts):
        fallback_candidates.append(
            (
                fact,
                "visible_scene_fact_intro",
                "first_mention_visible_fact_intro",
                "visible_fact_scene_intro",
                "visible_fact_scene_intro",
                f"visible_fact:{index}",
                _first_mention_composition_meta(),
            )
        )

    deduped_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []
    seen_candidates = set()
    for candidate in fallback_candidates:
        candidate_key = candidate[:6]
        if candidate_key in seen_candidates:
            continue
        seen_candidates.add(candidate_key)
        deduped_candidates.append(candidate)
    return deduped_candidates


def _build_visibility_violation_sample(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sample: List[Dict[str, Any]] = []
    for violation in violations[:3]:
        if not isinstance(violation, dict):
            continue
        sample.append(
            {
                "kind": str(violation.get("kind") or ""),
                "token": str(violation.get("token") or ""),
                "matched_entity_id": violation.get("matched_entity_id"),
                "matched_fact": violation.get("matched_fact"),
            }
        )
    return sample


def _build_referential_clarity_violation_sample(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sample: List[Dict[str, Any]] = []
    for violation in violations[:3]:
        if not isinstance(violation, dict):
            continue
        sample.append(
            {
                "kind": str(violation.get("kind") or ""),
                "token": str(violation.get("token") or ""),
                "candidate_entity_ids": list(violation.get("candidate_entity_ids") or []),
                "candidate_aliases": list(violation.get("candidate_aliases") or []),
                "sentence_text": str(violation.get("sentence_text") or ""),
                "offset": violation.get("offset"),
            }
        )
    return sample


_LOCAL_STRICT_SOCIAL_PRONOUN_SUBSTITUTION_TOKENS = frozenset(
    {"he", "she", "they", "him", "her", "them"}
)
_REF_REPAIR_PERSON_LIKE_KINDS = frozenset({"npc", "scene_actor", "creature", "humanoid", "person"})


def _strict_social_answer_payload_signals(clean: str) -> bool:
    """True when dialogue carries bounded answer, refusal-with-reason, clue, or concrete direction."""
    if candidate_satisfies_answer_contract(clean)[0]:
        return True
    if any(p.search(clean) for p in _ANSWER_DIRECT_PATTERNS):
        return True
    low = clean.lower()
    if re.search(
        r"\b(?:can'?t|cannot|won'?t|not (?:here|safe)|no names|won'?t name|too risky|wrong place)\b",
        low,
    ):
        return True
    if re.search(
        r"\b(?:east|west|north|south|gate|road|lane|checkpoint|pier|market|dock|wharf)\b",
        low,
    ):
        return True
    if re.search(r"\b(?:if you (?:want|need)|check (?:the|with)|ask (?:at|about))\b", low):
        return True
    if re.search(r"\b(?:patrol|watch(?:ers)?|sentries|crowd|ears (?:are )?open|listening)\b", low):
        return True
    if re.search(r"\b(?:note|letter|slips? you|hands? you)\b", low):
        return True
    return False


def _strict_social_dialogue_substantive_for_local_ref_repair(text: str) -> bool:
    """Conservative gate: repair only when the line already carries a useful answer payload."""
    clean = _normalize_text(text)
    if len(clean) < 28:
        return False
    if re.search(r"\bstarts to answer\b", clean, re.IGNORECASE):
        return False
    if is_route_illegal_global_or_sanitizer_fallback_text(clean):
        return False
    return _strict_social_answer_payload_signals(clean)


def _strict_social_eff_npc_id_matches_interlocutor(
    eff_resolution: Dict[str, Any] | None, active_interlocutor: str
) -> bool:
    aid = str(active_interlocutor or "").strip()
    if not aid:
        return False
    if not isinstance(eff_resolution, dict):
        return False
    soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
    nid = str(soc.get("npc_id") or "").strip()
    if nid and nid != aid:
        return False
    return True


def _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id(
    gm_output: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
) -> str | None:
    """When strict-social terminal dialogue preconditions hold, treat the grounded NPC as first-mention-grounded."""
    if not strict_social_active or not isinstance(eff_resolution, dict):
        return None
    contract, _src = _resolve_response_type_contract(
        gm_output if isinstance(gm_output, dict) else None,
        resolution=eff_resolution,
        session=session if isinstance(session, dict) else None,
    )
    if str((contract or {}).get("required_response_type") or "").strip().lower() != "dialogue":
        return None
    sid = str(scene_id or "").strip()
    if not strict_social_emission_will_apply(
        eff_resolution,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
    ):
        return None
    if not _active_interlocutor_matches_resolution_social_npc(session, eff_resolution):
        return None
    if not _strict_social_eff_npc_id_matches_interlocutor(eff_resolution, active_interlocutor):
        return None
    if not _active_interlocutor_visible_person_like(
        active_interlocutor, session=session, scene=scene, world=world
    ):
        return None
    soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
    npc_raw = str(soc.get("npc_id") or "").strip()
    if not npc_raw:
        return None
    sess = session if isinstance(session, dict) else None
    if not isinstance(sess, dict):
        return None
    canon_npc = canonical_interaction_target_npc_id(sess, npc_raw)
    canon_active = canonical_interaction_target_npc_id(sess, active_interlocutor)
    if not canon_npc or canon_npc != canon_active:
        return None
    return canon_active


def _active_interlocutor_visible_person_like(
    active_interlocutor: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> bool:
    aid = str(active_interlocutor or "").strip()
    if not aid:
        return False
    contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    visible_ids = [
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    if aid not in visible_ids:
        return False
    kinds = contract.get("visible_entity_kinds") if isinstance(contract.get("visible_entity_kinds"), dict) else {}
    kind = str(kinds.get(aid) or "").strip().lower()
    return kind in _REF_REPAIR_PERSON_LIKE_KINDS


def _grounded_speaker_phrase_for_pronoun_substitution(
    *,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
    pronoun_surface: str,
) -> str:
    label = (
        _speaker_label(eff_resolution)
        if isinstance(eff_resolution, dict)
        else _npc_display_name_for_emission(world, scene_id, active_interlocutor)
    )
    base = str(label or "").strip()
    if not base:
        base = _npc_display_name_for_emission(world, scene_id, active_interlocutor)
    core = base
    low = core.lower()
    if low.startswith("the "):
        core = core[4:].lstrip()
    phrase = f"the {core}".strip()
    if pronoun_surface[:1].isupper():
        return phrase[:1].upper() + phrase[1:]
    return phrase


def _violations_eligible_for_strict_social_local_pronoun_repair(violations: List[Dict[str, Any]]) -> bool:
    if len(violations) != 1:
        return False
    v = violations[0]
    if not isinstance(v, dict):
        return False
    if str(v.get("kind") or "").strip() != "ambiguous_entity_reference":
        return False
    cids = v.get("candidate_entity_ids")
    if isinstance(cids, list) and len(cids) > 1:
        return False
    return True


def _pronoun_violation_candidate_ids_align_with_interlocutor(
    violation: Dict[str, Any], active_interlocutor: str
) -> bool:
    aid = str(active_interlocutor or "").strip()
    cids = violation.get("candidate_entity_ids")
    if not isinstance(cids, list) or len(cids) == 0:
        return True
    if len(cids) == 1:
        return str(cids[0]).strip() == aid
    return False


def _try_strict_social_local_pronoun_substitution_repair(
    candidate_text: str,
    *,
    violations: List[Dict[str, Any]],
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
) -> tuple[str | None, Dict[str, Any]]:
    """Replace one ambiguous pronoun with the grounded interlocutor label; no clause moves or paraphrase."""
    dbg: Dict[str, Any] = {
        "referential_clarity_local_substitution_attempted": False,
        "referential_clarity_local_substitution_applied": False,
        "referential_clarity_local_substitution_token": None,
        "referential_clarity_local_substitution_replacement": None,
        "referential_clarity_fallback_avoided": False,
        "referential_clarity_fallback_after_failed_local_repair": False,
    }
    if not candidate_text.strip():
        return None, dbg
    if not _violations_eligible_for_strict_social_local_pronoun_repair(violations):
        return None, dbg
    v0 = violations[0]
    if not _pronoun_violation_candidate_ids_align_with_interlocutor(v0, active_interlocutor):
        return None, dbg
    token = str(v0.get("token") or "").strip().lower()
    if token not in _LOCAL_STRICT_SOCIAL_PRONOUN_SUBSTITUTION_TOKENS:
        return None, dbg
    sens = _split_visibility_sentences(candidate_text)
    if len(sens) != 1:
        return None, dbg
    try:
        pat = re.compile(rf"(?<!\w){re.escape(token)}(?!\w)", re.IGNORECASE)
    except re.error:
        return None, dbg
    matches = list(pat.finditer(candidate_text))
    if len(matches) != 1:
        return None, dbg
    m = matches[0]
    if not _strict_social_eff_npc_id_matches_interlocutor(eff_resolution, active_interlocutor):
        return None, dbg
    if not _active_interlocutor_visible_person_like(
        active_interlocutor, session=session, scene=scene, world=world
    ):
        return None, dbg
    if not _strict_social_dialogue_substantive_for_local_ref_repair(candidate_text):
        return None, dbg
    replacement = _grounded_speaker_phrase_for_pronoun_substitution(
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
        pronoun_surface=m.group(0),
    )
    repaired = pat.sub(replacement, candidate_text, count=1)
    if repaired == candidate_text:
        return None, dbg
    dbg["referential_clarity_local_substitution_attempted"] = True
    dbg["referential_clarity_local_substitution_token"] = m.group(0)
    dbg["referential_clarity_local_substitution_replacement"] = replacement
    sess = session if isinstance(session, dict) else None
    sc = scene if isinstance(scene, dict) else None
    w = world if isinstance(world, dict) else None
    ref2 = validate_player_facing_referential_clarity(repaired, session=sess, scene=sc, world=w)
    if ref2.get("ok") is not True:
        dbg["referential_clarity_fallback_after_failed_local_repair"] = True
        return None, dbg
    fm2 = validate_player_facing_first_mentions(
        repaired,
        session=sess,
        scene=sc,
        world=w,
        grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
    )
    if fm2.get("ok") is not True:
        dbg["referential_clarity_fallback_after_failed_local_repair"] = True
        return None, dbg
    vis2 = validate_player_facing_visibility(repaired, session=sess, scene=sc, world=w)
    if vis2.get("ok") is not True:
        dbg["referential_clarity_fallback_after_failed_local_repair"] = True
        return None, dbg
    dbg["referential_clarity_local_substitution_applied"] = True
    dbg["referential_clarity_fallback_avoided"] = True
    return repaired, dbg


def _apply_default_referential_clarity_meta(meta: Dict[str, Any], *, passed: bool | None) -> None:
    meta["referential_clarity_validation_passed"] = passed
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = []
    meta["referential_clarity_checked_entities"] = []
    meta["referential_clarity_violation_sample"] = []
    meta["referential_clarity_local_substitution_attempted"] = False
    meta["referential_clarity_local_substitution_applied"] = False
    meta["referential_clarity_local_substitution_token"] = None
    meta["referential_clarity_local_substitution_replacement"] = None
    meta["referential_clarity_fallback_avoided"] = False
    meta["referential_clarity_fallback_after_failed_local_repair"] = False


def _standard_visibility_safe_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    enforce_first_mentions: bool = False,
    enforce_referential_clarity: bool = False,
    prefer_grounded_scene_intro: bool = False,
) -> tuple[str, str, str, str, str, str, Dict[str, Any]]:
    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    validation_scene = _augment_scene_with_runtime_visible_leads(
        scene,
        session=session if isinstance(session, dict) else None,
        scene_id=scene_id,
    )
    suppress_intro = anti_reset_suppresses_intro_style_fallbacks(
        session,
        validation_scene if isinstance(validation_scene, dict) else scene,
        world,
        scene_id,
        eff_resolution,
    )
    fallback_candidates: List[tuple[str, str, str, str, str, str, Dict[str, Any]]] = []

    if strict_social_active and isinstance(eff_resolution, dict):
        social_fallback = minimal_social_emergency_fallback_line(eff_resolution)
        fallback_candidates.append(
            (
                social_fallback,
                "strict_social_visibility_minimal",
                "visibility_minimal_social_fallback",
                "minimal_social_emergency_fallback",
                "standard_safe_fallback",
                "minimal_social_emergency_fallback",
                _first_mention_composition_meta(),
            )
        )
    else:
        fallback_candidates.extend(
            _passive_scene_pressure_fallback_candidates(
                session=session if isinstance(session, dict) else None,
                scene=scene,
                scene_id=scene_id,
            )
        )
        if prefer_grounded_scene_intro and not suppress_intro:
            fallback_candidates.extend(
                _grounded_scene_intro_fallback_candidates(
                    session=session,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene,
                    world=world,
                    active_interlocutor=active_interlocutor,
                )
            )

    sid = str(scene_id or "").strip()
    if (
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
        and not strict_social_active
    ):
        mini_res: Dict[str, Any] = {
            "kind": "question",
            "social": {
                "npc_id": active_interlocutor,
                "npc_name": _npc_display_name_for_emission(world, sid, active_interlocutor),
                "social_intent_class": "social_exchange",
            },
        }
        fallback_candidates.append(
            (
                minimal_social_emergency_fallback_line(mini_res),
                "social_active_interlocutor_minimal",
                "social_interlocutor_fallback",
                "social_interlocutor_minimal_fallback",
                "standard_safe_fallback",
                "social_interlocutor_minimal_fallback",
                _first_mention_composition_meta(),
            )
        )

    if _should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution):
        fallback_candidates.append(
            (
                "Nothing confirms progress toward that lead yet—the moment stays unresolved.",
                "npc_pursuit_fail_closed_neutral",
                "npc_pursuit_neutral_nonprogress",
                "npc_pursuit_neutral_fallback",
                "standard_safe_fallback",
                "npc_pursuit_neutral_fallback",
                _first_mention_composition_meta(),
            )
        )
    elif not strict_social_active and not _passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    ):
        if suppress_intro:
            fallback_candidates.append(
                (
                    local_exchange_continuation_fallback_line(
                        session=session if isinstance(session, dict) else None,
                        world=world if isinstance(world, dict) else None,
                        scene_id=scene_id,
                        resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                    ),
                    "anti_reset_local_continuation",
                    "anti_reset_continuation_fallback",
                    "anti_reset_local_continuation_fallback",
                    "standard_safe_fallback",
                    "anti_reset_local_continuation_fallback",
                    _first_mention_composition_meta(),
                )
            )
        else:
            fallback_candidates.append(
                (
                    _global_narrative_fallback_stock_line(scene if isinstance(scene, dict) else None, scene_id=scene_id),
                    "global_scene_narrative",
                    "narrative_safe_fallback",
                    "global_scene_fallback",
                    "standard_safe_fallback",
                    "global_scene_fallback",
                    _first_mention_composition_meta(),
                )
            )

    for (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        fallback_strategy,
        fallback_candidate_source,
        composition_meta,
    ) in fallback_candidates:
        if not _normalize_text(fallback_text):
            continue
        if suppress_intro and should_replace_candidate_intro_fallback(
            fallback_text,
            scene_envelope=validation_scene if isinstance(validation_scene, dict) else scene,
            emitter_source=final_emitted_source,
            suppress_intro=True,
        ):
            continue
        validation = validate_player_facing_visibility(
            fallback_text,
            session=session if isinstance(session, dict) else None,
            scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
        )
        if validation.get("ok") is True:
            if enforce_first_mentions:
                first_mention_validation = validate_player_facing_first_mentions(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if first_mention_validation.get("ok") is not True:
                    continue
            if enforce_referential_clarity:
                referential_clarity_validation = validate_player_facing_referential_clarity(
                    fallback_text,
                    session=session if isinstance(session, dict) else None,
                    scene=validation_scene if isinstance(validation_scene, dict) else scene if isinstance(scene, dict) else None,
                    world=world if isinstance(world, dict) else None,
                )
                if referential_clarity_validation.get("ok") is not True:
                    continue
            return (
                fallback_text,
                fallback_pool,
                fallback_kind,
                final_emitted_source,
                fallback_strategy,
                fallback_candidate_source,
                composition_meta,
            )

    if strict_social_active and isinstance(eff_resolution, dict):
        return (
            minimal_social_emergency_fallback_line(eff_resolution),
            "strict_social_visibility_minimal",
            "visibility_minimal_social_fallback",
            "minimal_social_emergency_fallback",
            "standard_safe_fallback",
            "minimal_social_emergency_fallback",
            _first_mention_composition_meta(),
        )

    passive_candidates = _passive_scene_pressure_fallback_candidates(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=scene_id,
    )
    if passive_candidates:
        fallback_text, fallback_pool, fallback_kind, final_emitted_source, fallback_strategy, fallback_candidate_source, composition_meta = passive_candidates[0]
        return (
            fallback_text,
            fallback_pool,
            fallback_kind,
            final_emitted_source,
            fallback_strategy,
            fallback_candidate_source,
            composition_meta,
        )

    if suppress_intro:
        return (
            local_exchange_continuation_fallback_line(
                session=session if isinstance(session, dict) else None,
                world=world if isinstance(world, dict) else None,
                scene_id=scene_id,
                resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            ),
            "anti_reset_local_continuation",
            "anti_reset_continuation_fallback",
            "anti_reset_local_continuation_fallback",
            "standard_safe_fallback",
            "anti_reset_local_continuation_fallback",
            _first_mention_composition_meta(),
        )
    return (
        _global_narrative_fallback_stock_line(scene if isinstance(scene, dict) else None, scene_id=scene_id),
        "global_scene_narrative",
        "narrative_safe_fallback",
        "global_scene_fallback",
        "standard_safe_fallback",
        "global_scene_fallback",
        _first_mention_composition_meta(),
    )


def _apply_first_mention_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_first_mentions(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    leading_pronoun_detected = bool(validation.get("leading_pronoun_detected"))
    first_explicit_entity_offset = validation.get("first_explicit_entity_offset")
    if not isinstance(first_explicit_entity_offset, int):
        first_explicit_entity_offset = None

    meta["first_mention_validation_passed"] = validation.get("ok") is True
    meta["first_mention_replacement_applied"] = False
    meta["first_mention_violation_kinds"] = violation_kinds
    meta["first_mention_checked_entities"] = checked_entities
    meta["first_mention_leading_pronoun_detected"] = leading_pronoun_detected
    meta["first_mention_first_explicit_entity_offset"] = first_explicit_entity_offset
    meta["first_mention_fallback_strategy"] = None
    meta["first_mention_fallback_candidate_source"] = None
    meta["opening_scene_first_mention_preference_used"] = False
    meta["first_mention_composition_used"] = False
    meta["first_mention_composition_layers"] = _default_first_mention_composition_layers()
    meta["first_mention_strict_social_grounded_speaker_exemption_entity_id"] = (
        grounded_speaker_first_mention_exemption_entity_id
    )
    _apply_default_referential_clarity_meta(meta, passed=None)
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return _apply_referential_clarity_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        )

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        meta["first_mention_validation_passed"] = None
        out["_final_emission_meta"] = meta
        return out

    opening_scene_preference_used = _opening_scene_preference_active(session)
    suppress_intro = anti_reset_suppresses_intro_style_fallbacks(
        session,
        scene,
        world,
        scene_id,
        eff_resolution,
    )
    prefer_grounded_scene_intro = not suppress_intro

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        fallback_strategy,
        fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
        prefer_grounded_scene_intro=prefer_grounded_scene_intro,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "first_mention_enforcement_replaced"]
        + [f"first_mention_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:first_mention_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["first_mention_validation_passed"] = False
    meta["first_mention_replacement_applied"] = True
    meta["first_mention_fallback_strategy"] = fallback_strategy
    meta["first_mention_fallback_candidate_source"] = fallback_candidate_source
    meta["opening_scene_first_mention_preference_used"] = opening_scene_preference_used
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_first_mention",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_first_mention_replace"})
    return _apply_referential_clarity_enforcement(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
    )


def _referential_clarity_violations_have_multi_entity_candidates(violations: List[Dict[str, Any]]) -> bool:
    for v in violations:
        if not isinstance(v, dict):
            continue
        cids = v.get("candidate_entity_ids")
        if isinstance(cids, list) and len(cids) > 1:
            return True
    return False


def _referential_clarity_violations_only_dialogue_attribution_they(violations: List[Dict[str, Any]]) -> bool:
    if not violations:
        return False
    for v in violations:
        if not isinstance(v, dict):
            return False
        if str(v.get("kind") or "").strip() != "ambiguous_entity_reference":
            return False
        st = str(v.get("sentence_text") or "").strip()
        if not st or not _DIALOGUE_ATTRIBUTION_THEY_SPEECH_TAG.search(st):
            return False
    return True


def _apply_referential_clarity_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_referential_clarity(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = validation.get("checked_entities") if isinstance(validation.get("checked_entities"), list) else []
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )
    meta["referential_clarity_validation_passed"] = validation.get("ok") is True
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = violation_kinds
    meta["referential_clarity_checked_entities"] = checked_entities
    meta["referential_clarity_violation_sample"] = _build_referential_clarity_violation_sample(violations)
    meta["referential_clarity_local_substitution_attempted"] = False
    meta["referential_clarity_local_substitution_applied"] = False
    meta["referential_clarity_local_substitution_token"] = None
    meta["referential_clarity_local_substitution_replacement"] = None
    meta["referential_clarity_fallback_avoided"] = False
    meta["referential_clarity_fallback_after_failed_local_repair"] = False
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return out

    if not checked_entities and _reply_already_has_concrete_interaction(candidate_text):
        if not violations:
            meta["referential_clarity_validation_passed"] = None
            out["_final_emission_meta"] = meta
            return out
        if not _referential_clarity_violations_have_multi_entity_candidates(violations) and (
            _referential_clarity_violations_only_dialogue_attribution_they(violations)
        ):
            meta["referential_clarity_validation_passed"] = True
            meta["referential_clarity_replacement_applied"] = False
            meta["referential_clarity_violation_kinds"] = []
            meta["referential_clarity_violation_sample"] = []
            out["_final_emission_meta"] = meta
            return out

    response_type_req = str(meta.get("response_type_required") or "").strip().lower()
    if (
        strict_social_active
        and response_type_req == "dialogue"
        and not strict_social_suppressed_non_social_turn
    ):
        repaired, subst_dbg = _try_strict_social_local_pronoun_substitution_repair(
            candidate_text,
            violations=[v for v in violations if isinstance(v, dict)],
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        )
        for k, val in subst_dbg.items():
            meta[k] = val
        if repaired is not None:
            out["player_facing_text"] = repaired
            meta["referential_clarity_validation_passed"] = True
            meta["referential_clarity_replacement_applied"] = False
            meta["referential_clarity_violation_kinds"] = []
            meta["referential_clarity_violation_sample"] = []
            tags = out.get("tags") if isinstance(out.get("tags"), list) else []
            out["tags"] = _dedupe_preserve_order(
                [str(t) for t in tags if isinstance(t, str)] + ["referential_clarity_local_substitution"]
            )
            gate_out_text = _normalize_text(out.get("player_facing_text"))
            meta["post_gate_mutation_detected"] = bool(meta.get("post_gate_mutation_detected")) or (
                candidate_text != gate_out_text
            )
            meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
            out["_final_emission_meta"] = meta
            log_final_emission_decision(
                {
                    "stage": "final_emission_gate_referential_clarity",
                    "social_route": strict_social_active,
                    "candidate_ok": True,
                    "rejection_reasons": [],
                    "fallback_pool": "referential_clarity_local_substitution",
                    "fallback_kind": "none",
                    "active_interlocutor": active_interlocutor or None,
                }
            )
            log_final_emission_trace(
                {**meta, "stage": "final_emission_gate_referential_clarity_local_substitution"}
            )
            return out

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        _fallback_strategy,
        _fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        enforce_first_mentions=True,
        enforce_referential_clarity=True,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "referential_clarity_enforcement_replaced"]
        + [f"referential_clarity_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:referential_clarity_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["referential_clarity_validation_passed"] = False
    meta["referential_clarity_replacement_applied"] = True
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_referential_clarity",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
            "referential_clarity_fallback_after_failed_local_repair": bool(
                meta.get("referential_clarity_fallback_after_failed_local_repair")
            ),
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_referential_clarity_replace"})
    return out


def _apply_visibility_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    strict_social_active: bool,
    strict_social_suppressed_non_social_turn: bool,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
) -> Dict[str, Any]:
    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_visibility(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    checked_entities = (
        validation.get("visibility_checked_entities")
        if isinstance(validation.get("visibility_checked_entities"), list)
        else []
    )
    checked_facts = (
        validation.get("visibility_checked_facts")
        if isinstance(validation.get("visibility_checked_facts"), list)
        else []
    )
    violation_kinds = _dedupe_preserve_order(
        [str(v.get("kind") or "") for v in violations if isinstance(v, dict) and str(v.get("kind") or "").strip()]
    )

    meta["first_mention_validation_passed"] = None
    meta["first_mention_replacement_applied"] = False
    meta["first_mention_violation_kinds"] = []
    meta["first_mention_checked_entities"] = []
    meta["first_mention_leading_pronoun_detected"] = False
    meta["first_mention_first_explicit_entity_offset"] = None
    meta["first_mention_fallback_strategy"] = None
    meta["first_mention_fallback_candidate_source"] = None
    meta["opening_scene_first_mention_preference_used"] = False
    meta["first_mention_composition_used"] = False
    meta["first_mention_composition_layers"] = _default_first_mention_composition_layers()
    _apply_default_referential_clarity_meta(meta, passed=None)
    meta["visibility_validation_passed"] = validation.get("ok") is True
    meta["visibility_replacement_applied"] = False
    meta["visibility_violation_kinds"] = violation_kinds
    meta["visibility_violation_sample"] = _build_visibility_violation_sample(violations)
    meta["visibility_checked_entities"] = checked_entities
    meta["visibility_checked_facts"] = checked_facts
    out["_final_emission_meta"] = meta

    if validation.get("ok") is True:
        return _apply_first_mention_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        )

    tag_list_gate = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    dbg_gate = str(out.get("debug_notes") or "")
    if (
        "known_fact_guard" in tag_list_gate
        and "recent_dialogue_continuity" in dbg_gate
        and violation_kinds == ["unseen_entity_reference"]
    ):
        meta["visibility_validation_passed"] = True
        meta["visibility_replacement_applied"] = False
        meta["visibility_continuity_lead_exemption"] = True
        out["_final_emission_meta"] = meta
        return _apply_first_mention_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        )

    if not checked_entities and not checked_facts and _reply_already_has_concrete_interaction(candidate_text):
        meta["visibility_validation_passed"] = None
        out["_final_emission_meta"] = meta
        return out

    (
        fallback_text,
        fallback_pool,
        fallback_kind,
        final_emitted_source,
        _fallback_strategy,
        _fallback_candidate_source,
        composition_meta,
    ) = _standard_visibility_safe_fallback(
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
    )
    out["player_facing_text"] = fallback_text
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = _dedupe_preserve_order(
        [str(t) for t in tags if isinstance(t, str)]
        + ["final_emission_gate_replaced", "visibility_enforcement_replaced"]
        + [f"visibility_violation:{kind}" for kind in violation_kinds]
    )
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:visibility_replaced:"
        + ",".join(violation_kinds[:8])
    )

    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["final_route"] = "replaced"
    meta["final_emitted_source"] = final_emitted_source
    meta["post_gate_mutation_detected"] = candidate_text != gate_out_text
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    meta["visibility_validation_passed"] = False
    meta["visibility_replacement_applied"] = True
    meta["visibility_fallback_pool"] = fallback_pool
    meta["visibility_fallback_kind"] = fallback_kind
    meta["first_mention_composition_used"] = bool(composition_meta.get("first_mention_composition_used"))
    meta["first_mention_composition_layers"] = composition_meta.get(
        "first_mention_composition_layers",
        _default_first_mention_composition_layers(),
    )
    out["_final_emission_meta"] = meta

    log_final_emission_decision(
        {
            "stage": "final_emission_gate_visibility",
            "social_route": strict_social_active,
            "candidate_ok": False,
            "rejection_reasons": violation_kinds[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            "active_interlocutor": active_interlocutor or None,
        }
    )
    log_final_emission_trace({**meta, "stage": "final_emission_gate_visibility_replace"})
    return out


def _should_use_neutral_nonprogress_fallback_instead_of_global_stock(
    session: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
) -> bool:
    """Parser-built NPC-target pursuit turns without grounded contact must not get the stock 'voices shift' line."""
    if not isinstance(session, dict):
        return False
    ctx = session.get(NPC_PURSUIT_CONTACT_SESSION_KEY)
    if not isinstance(ctx, dict):
        return False
    if str(ctx.get("commitment_source") or "").strip() != "explicit_player_pursuit":
        return False
    if not isinstance(eff_resolution, dict):
        return False
    rk = str(eff_resolution.get("kind") or "").strip().lower()
    if rk not in SOCIAL_KINDS:
        return False
    target = str(ctx.get("target_npc_id") or "").strip()
    if not target:
        return False
    soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
    if soc.get("offscene_target"):
        return True
    gs = str(soc.get("grounded_speaker_id") or "").strip()
    if gs and gs == target:
        return False
    if soc.get("target_resolved") is True and str(soc.get("npc_id") or "").strip() == target:
        return False
    return True


# --- Speaker selection contract (Block 1 authority) — validation + repair at final emission ---

_SPEAKER_REASON_SPEAKER_CONTRACT_MATCH = "speaker_contract_match"
_SPEAKER_REASON_SPEAKER_BINDING_MISMATCH = "speaker_binding_mismatch"
_SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER = "forbidden_generic_fallback_speaker"
_SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH = "unjustified_speaker_switch"
_SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT = "interruption_without_contract_support"
_SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH = "interruption_justified_switch"
_SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR = "continuity_locked_speaker_repair"
_SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE = "canonical_speaker_rewrite"
_SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER = "narrator_neutral_no_allowed_speaker"

SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES: tuple[str, ...] = (
    _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
    _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH,
    _SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER,
    _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
    _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
    _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
    _SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR,
    _SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE,
    _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER,
)

_SPEECH_VERB_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|asks|asked|adds|added)\b",
    re.IGNORECASE,
)
_BEAT_ATTRIBUTION_RE = re.compile(
    r"^\s*([^\n]+?)\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
# Leading "…" dialogue + pronoun + attribution verb: label is the pronoun only (not the quoted span).
_QUOTED_THEN_PRONOUN_SPEECH_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:says|said|replies|replied|answers|answered|mutters|muttered|whispers|whispered|"
    r"asks|asked|adds|added|insists|insisted)\b",
    re.IGNORECASE,
)
_QUOTED_THEN_PRONOUN_BEAT_RE = re.compile(
    r'^\s*"[^"]*"\s+'
    r"\b(he|she|they|him|her|them)\b\s+"
    r"(?:shakes|frowns|nods|grimaces|shrugs|lowers|raises|opens|starts|spreads|tightens|leans|glances)\b",
    re.IGNORECASE,
)
_NON_NAME_ATTRIBUTION_PREFIXES = frozenset(
    {
        "he",
        "she",
        "they",
        "it",
        "someone",
        "a voice",
        "the voice",
        "another voice",
    }
)


def _empty_speaker_selection_contract() -> Dict[str, Any]:
    return {
        "primary_speaker_id": None,
        "primary_speaker_name": None,
        "allowed_speaker_ids": [],
        "continuity_locked": False,
        "continuity_lock_reason": None,
        "speaker_switch_allowed": True,
        "speaker_switch_reason": None,
        "interruption_allowed": True,
        "interruption_requires_scene_event": False,
        "generic_fallback_forbidden": False,
        "forbidden_fallback_labels": list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS),
        "offscene_speakers_forbidden": True,
        "debug": {"contract_missing": True},
    }


def get_speaker_selection_contract(
    resolution: Dict[str, Any] | None,
    metadata: Dict[str, Any] | None = None,
    trace: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Load Block 1 speaker contract: metadata emission_debug first, then resolution/trace copies."""
    empty = _empty_speaker_selection_contract()

    def _from_emission_debug(em: Any) -> Dict[str, Any] | None:
        if not isinstance(em, dict):
            return None
        c = em.get("speaker_selection_contract")
        return c if isinstance(c, dict) and c else None

    if isinstance(metadata, dict):
        hit = _from_emission_debug(metadata.get("emission_debug"))
        if hit is not None:
            return hit

    if isinstance(resolution, dict):
        md = resolution.get("metadata")
        if isinstance(md, dict):
            hit = _from_emission_debug(md.get("emission_debug"))
            if hit is not None:
                return hit

    if isinstance(trace, dict):
        tc = trace.get("speaker_selection_contract")
        if isinstance(tc, dict) and tc:
            return tc
        hit = _from_emission_debug(trace.get("emission_debug"))
        if hit is not None:
            return hit

    return empty


def detect_emitted_speaker_signature(
    text: str,
    resolution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Infer opening attribution / dialogue-ownership cues from emitted text."""
    t = _normalize_text(text)
    speaker_label: str | None = None
    speaker_name: str | None = None
    is_explicit = False
    confidence: str = "low"

    mq = _QUOTED_THEN_PRONOUN_SPEECH_RE.match(t)
    if not mq:
        mq = _QUOTED_THEN_PRONOUN_BEAT_RE.match(t)
    if mq:
        raw = str(mq.group(1) or "").strip()
        low = raw.lower()
        speaker_label = raw
        if low and low not in _NON_NAME_ATTRIBUTION_PREFIXES:
            speaker_name = raw
            is_explicit = True
            confidence = "high"
        elif raw:
            confidence = "medium"
        forbidden = list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
        is_generic_fb = False
        if speaker_label:
            sl = speaker_label.strip().lower()
            for fb in forbidden:
                fbl = str(fb or "").strip().lower()
                if fbl and (fbl == sl or fbl in sl or sl in fbl):
                    is_generic_fb = True
                    break
        intr = bool(interruption_cue_present_in_text(t) or _has_explicit_interruption_shape(t))
        return {
            "speaker_name": speaker_name,
            "speaker_label": speaker_label,
            "is_explicitly_attributed": is_explicit,
            "is_generic_fallback_label": is_generic_fb,
            "has_interruption_framing": intr,
            "confidence": confidence,
        }

    m = _SPEECH_VERB_ATTRIBUTION_RE.match(t)
    if not m:
        m = _BEAT_ATTRIBUTION_RE.match(t)
    if m:
        raw = str(m.group(1) or "").strip()
        low = raw.lower()
        if raw and low not in _NON_NAME_ATTRIBUTION_PREFIXES and not low.startswith(
            tuple(p + " " for p in _NON_NAME_ATTRIBUTION_PREFIXES)
        ):
            speaker_label = raw
            speaker_name = raw
            is_explicit = True
            confidence = "high"
        elif raw:
            speaker_label = raw
            confidence = "medium"

    forbidden = list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
    is_generic_fb = False
    if speaker_label:
        sl = speaker_label.strip().lower()
        for fb in forbidden:
            fbl = fb.strip().lower()
            if fbl == sl or fbl in sl or sl in fbl:
                is_generic_fb = True
                break

    intr = bool(interruption_cue_present_in_text(t) or _has_explicit_interruption_shape(t))

    return {
        "speaker_name": speaker_name,
        "speaker_label": speaker_label,
        "is_explicitly_attributed": is_explicit,
        "is_generic_fallback_label": is_generic_fb,
        "has_interruption_framing": intr,
        "confidence": confidence,
    }


def _display_from_npc_id(npc_id: str | None) -> str:
    s = str(npc_id or "").strip()
    if not s:
        return ""
    return s.replace("_", " ").replace("-", " ").title()


def _label_matches_primary_speaker(label: str, contract: Dict[str, Any], resolution: Dict[str, Any] | None) -> bool:
    if not str(label or "").strip():
        return False
    low = label.strip().lower()
    pn = str(contract.get("primary_speaker_name") or "").strip().lower()
    pid = str(contract.get("primary_speaker_id") or "").strip()
    pid_disp = _display_from_npc_id(pid).lower()
    if pn and low == pn:
        return True
    if pid_disp and low == pid_disp:
        return True
    if isinstance(resolution, dict):
        soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
        rn = str(soc.get("npc_name") or "").strip().lower()
        rid = _display_from_npc_id(str(soc.get("npc_id") or "")).lower()
        if rn and low == rn:
            return True
        if rid and low == rid:
            return True
    return False


def _label_in_allowed_speaker_ids(label: str, contract: Dict[str, Any], resolution: Dict[str, Any] | None) -> bool:
    allowed = contract.get("allowed_speaker_ids")
    if not isinstance(allowed, list) or not allowed:
        return False
    low = label.strip().lower()
    for aid in allowed:
        disp = _display_from_npc_id(str(aid or "").strip()).lower()
        if disp and low == disp:
            return True
    pid = str(contract.get("primary_speaker_id") or "").strip()
    if pid in allowed and _label_matches_primary_speaker(label, contract, resolution):
        return True
    return False


def _emitted_invents_dialogue_ownership(text: str) -> bool:
    t = _normalize_text(text)
    if not t:
        return False
    if '"' in t:
        return True
    return bool(
        re.search(
            r"\b(?:says|replies|answers|mutters|whispers|asks|shakes|shrugs|frowns|grimaces)\b",
            t,
            re.IGNORECASE,
        )
    )


def _explicit_interruption_scene_event_framing(text: str) -> bool:
    return bool(_has_explicit_interruption_shape(_normalize_text(text)))


def validate_emitted_speaker_against_contract(
    text: str,
    speaker_selection: Dict[str, Any],
    resolution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Contract-first validation of final text vs Block 1 speaker_selection_contract."""
    c = speaker_selection if isinstance(speaker_selection, dict) else {}
    res = resolution if isinstance(resolution, dict) else None
    details: Dict[str, Any] = {"signature": detect_emitted_speaker_signature(text, res)}

    if isinstance(c.get("debug"), dict) and c["debug"].get("contract_missing"):
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
            "canonical_speaker_id": c.get("primary_speaker_id"),
            "canonical_speaker_name": c.get("primary_speaker_name"),
            "repair_mode": "none",
            "details": {**details, "skipped": "no_contract"},
        }

    allowed = [str(x).strip() for x in (c.get("allowed_speaker_ids") or []) if str(x).strip()]
    primary_id = str(c.get("primary_speaker_id") or "").strip() or None
    primary_name = str(c.get("primary_speaker_name") or "").strip() or None
    continuity_locked = bool(c.get("continuity_locked"))
    gen_ff = bool(c.get("generic_fallback_forbidden"))
    sw_ok = bool(c.get("speaker_switch_allowed"))
    intr_ok = bool(c.get("interruption_allowed"))
    intr_scene = bool(c.get("interruption_requires_scene_event"))
    offscene_forbid = bool(c.get("offscene_speakers_forbidden"))

    sig = details["signature"]
    label = str(sig.get("speaker_label") or "").strip()
    explicit = bool(sig.get("is_explicitly_attributed"))
    intr = bool(sig.get("has_interruption_framing"))
    explicit_scene = _explicit_interruption_scene_event_framing(text)

    canonical_id = primary_id
    canonical_name = primary_name
    if not canonical_name and res is not None:
        soc0 = res.get("social") if isinstance(res.get("social"), dict) else {}
        canonical_name = str(soc0.get("npc_name") or "").strip() or None
    if not canonical_name and primary_id:
        canonical_name = _display_from_npc_id(primary_id)

    # (b) Generic fallback speaker
    if gen_ff:
        flist = (
            c.get("forbidden_fallback_labels")
            if isinstance(c.get("forbidden_fallback_labels"), list)
            else list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS)
        )
        low_lab = label.lower() if label else ""
        hit = bool(sig.get("is_generic_fallback_label"))
        if explicit and low_lab and not hit:
            for fb in flist:
                fbs = str(fb or "").strip().lower()
                if fbs and (fbs == low_lab or fbs in low_lab or low_lab in fbs):
                    hit = True
                    break
        if hit:
            rm = "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral"
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_FORBIDDEN_GENERIC_FALLBACK_SPEAKER,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": rm,
                "details": {**details, "rule": "generic_fallback_forbidden"},
            }

    # Interruption policy (third-party / scene break)
    if intr:
        if not (sw_ok and intr_ok):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral",
                "details": {**details, "rule": "interruption_not_permitted"},
            }
        # Continuity-locked strict-social: require explicit join only when dialogue ownership
        # is present (quoted speech or clear attribution), matching mixed-blob rejection policy.
        tnorm = _normalize_text(text)
        if intr_scene and not explicit_scene and ('"' in tnorm or explicit):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_WITHOUT_CONTRACT_SUPPORT,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if (primary_id or allowed) else "narrator_neutral",
                "details": {**details, "rule": "interruption_requires_scene_event"},
            }

    # (e) No speaker allowed but dialogue ownership invented
    if not allowed:
        if _emitted_invents_dialogue_ownership(text):
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER,
                "canonical_speaker_id": None,
                "canonical_speaker_name": None,
                "repair_mode": "narrator_neutral",
                "details": {**details, "rule": "no_allowed_speaker_dialogue"},
            }
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "none",
            "details": details,
        }

    # (a) Continuity locked + wrong explicit speaker
    if continuity_locked and explicit and label:
        if not _label_in_allowed_speaker_ids(label, c, res):
            if intr and sw_ok and intr_ok and (not intr_scene or explicit_scene):
                return {
                    "ok": True,
                    "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
                    "canonical_speaker_id": canonical_id,
                    "canonical_speaker_name": canonical_name,
                    "repair_mode": "none",
                    "details": {**details, "rule": "interruption_overrides_explicit_mismatch"},
                }
            salvage = bool(re.search(r"\"[^\"]{2,}\"", _normalize_text(text)))
            rm = "local_rebind" if (canonical_name and salvage) else ("canonical_rewrite" if canonical_id else "narrator_neutral")
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": rm,
                "details": {**details, "rule": "continuity_locked_explicit_mismatch"},
            }

    # (c) New speaker not permitted
    if explicit and label and not _label_in_allowed_speaker_ids(label, c, res):
        if intr and sw_ok and intr_ok and (not intr_scene or explicit_scene):
            return {
                "ok": True,
                "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "none",
                "details": {**details, "rule": "switch_permitted_interruption"},
            }
        if not sw_ok:
            return {
                "ok": False,
                "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
                "canonical_speaker_id": canonical_id,
                "canonical_speaker_name": canonical_name,
                "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
                "details": {**details, "rule": "speaker_switch_disallowed"},
            }
        return {
            "ok": False,
            "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
            "details": {**details, "rule": "unlisted_explicit_speaker"},
        }

    if offscene_forbid and explicit and label and not _label_in_allowed_speaker_ids(label, c, res) and not intr:
        return {
            "ok": False,
            "reason_code": _SPEAKER_REASON_UNJUSTIFIED_SPEAKER_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "canonical_rewrite" if canonical_id else "narrator_neutral",
            "details": {**details, "rule": "offscene_speakers_forbidden"},
        }

    if intr:
        return {
            "ok": True,
            "reason_code": _SPEAKER_REASON_INTERRUPTION_JUSTIFIED_SWITCH,
            "canonical_speaker_id": canonical_id,
            "canonical_speaker_name": canonical_name,
            "repair_mode": "none",
            "details": details,
        }

    return {
        "ok": True,
        "reason_code": _SPEAKER_REASON_SPEAKER_CONTRACT_MATCH,
        "canonical_speaker_id": canonical_id,
        "canonical_speaker_name": canonical_name,
        "repair_mode": "none",
        "details": details,
    }


def _try_local_rebind_opening_speaker(text: str, *, wrong_label: str, canonical_name: str) -> str | None:
    t = _normalize_text(text)
    w = str(wrong_label or "").strip()
    if not w or not canonical_name:
        return None
    if '"' in w or "“" in w or "”" in w:
        return None
    low_t = t.lower()
    low_w = w.lower()
    if low_t.startswith(low_w + " ") or low_t.startswith(low_w + ","):
        rest = t[len(w) :].lstrip()
        return _normalize_text(f"{canonical_name} {rest}")
    return None


def _apply_speaker_contract_repairs(
    text: str,
    validation: Dict[str, Any],
    *,
    contract: Dict[str, Any],
    eff_resolution: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None,
) -> tuple[str, str, Dict[str, Any]]:
    """Returns (new_text, final_reason_code, repair_debug)."""
    dbg: Dict[str, Any] = {"initial_repair_mode": validation.get("repair_mode")}
    mode = str(validation.get("repair_mode") or "none")
    reason = str(validation.get("reason_code") or "")
    cid = validation.get("canonical_speaker_id")
    cname = str(validation.get("canonical_speaker_name") or "").strip()

    if mode == "local_rebind" and eff_resolution is not None:
        sig = (validation.get("details") or {}).get("signature") or {}
        wl = str(sig.get("speaker_label") or "").strip()
        if wl and cname:
            attempt = _try_local_rebind_opening_speaker(text, wrong_label=wl, canonical_name=cname)
            if attempt:
                dbg["local_rebind_applied"] = True
                if isinstance(eff_resolution.get("social"), dict):
                    soc = eff_resolution["social"]
                    if cid:
                        soc["npc_id"] = str(cid).strip()
                    soc["npc_name"] = cname
                return attempt, _SPEAKER_REASON_CONTINUITY_LOCKED_SPEAKER_REPAIR, dbg

    if mode == "canonical_rewrite":
        if eff_resolution is not None and isinstance(eff_resolution.get("social"), dict):
            soc = dict(eff_resolution["social"])
            if cid:
                soc["npc_id"] = str(cid).strip()
            if cname:
                soc["npc_name"] = cname
            elif cid:
                soc["npc_name"] = _npc_display_name_for_emission(
                    world if isinstance(world, dict) else {},
                    str(scene_id or "").strip(),
                    str(cid).strip(),
                )
            soc.pop("reply_speaker_grounding_neutral_bridge", None)
            eff_resolution["social"] = soc
            line = strict_social_ownership_terminal_fallback(eff_resolution)
            dbg["canonical_rewrite_applied"] = True
            return line, _SPEAKER_REASON_CANONICAL_SPEAKER_REWRITE, dbg
        line = _normalize_text(text)
        dbg["canonical_rewrite_failed_resolution"] = True
        return line, reason, dbg

    if mode == "narrator_neutral":
        seed = f"{scene_id}|{cid or ''}|{hash(_normalize_text(text)) % 10000}"
        line = neutral_reply_speaker_grounding_bridge_line(seed=seed)
        dbg["narrator_neutral_applied"] = True
        if eff_resolution is not None and isinstance(eff_resolution.get("social"), dict):
            soc = eff_resolution["social"]
            soc["reply_speaker_grounding_neutral_bridge"] = True
            soc.pop("npc_id", None)
            soc.pop("npc_name", None)
        return line, _SPEAKER_REASON_NARRATOR_NEUTRAL_NO_ALLOWED_SPEAKER, dbg

    return text, reason, dbg


def _sync_eff_social_to_resolution(
    eff_resolution: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
) -> None:
    """Copy speaker fields from effective resolution back to the caller's resolution dict when distinct."""
    if not isinstance(eff_resolution, dict) or not isinstance(resolution, dict):
        return
    if resolution is eff_resolution:
        return
    src = eff_resolution.get("social")
    if not isinstance(src, dict):
        return
    dst = resolution.get("social")
    if not isinstance(dst, dict):
        resolution["social"] = {}
        dst = resolution["social"]
    if src.get("reply_speaker_grounding_neutral_bridge"):
        dst["reply_speaker_grounding_neutral_bridge"] = True
        dst.pop("npc_id", None)
        dst.pop("npc_name", None)
        return
    if "npc_id" in src:
        dst["npc_id"] = src.get("npc_id")
    if "npc_name" in src:
        dst["npc_name"] = src.get("npc_name")


def _merge_interaction_continuity_validation_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    validation_payload: Dict[str, Any],
) -> None:
    """Metadata-only: attach continuity validator output (no gating, no text mutation)."""
    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        em = md_out.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em["interaction_continuity_validation"] = validation_payload

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            emr = md_r.setdefault("emission_debug", {})
            if isinstance(emr, dict):
                emr["interaction_continuity_validation"] = validation_payload

    if (
        eff_resolution is not None
        and eff_resolution is not resolution
        and isinstance(eff_resolution.get("metadata"), dict)
    ):
        eme = eff_resolution["metadata"].setdefault("emission_debug", {})
        if isinstance(eme, dict):
            eme["interaction_continuity_validation"] = validation_payload

    fem = out.get("_final_emission_meta")
    if isinstance(fem, dict):
        fem["interaction_continuity_validation"] = validation_payload


def _merge_interaction_continuity_repair_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    repair_payload: Dict[str, Any],
) -> None:
    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        em = md_out.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em["interaction_continuity_repair"] = repair_payload

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            emr = md_r.setdefault("emission_debug", {})
            if isinstance(emr, dict):
                emr["interaction_continuity_repair"] = repair_payload

    if (
        eff_resolution is not None
        and eff_resolution is not resolution
        and isinstance(eff_resolution.get("metadata"), dict)
    ):
        eme = eff_resolution["metadata"].setdefault("emission_debug", {})
        if isinstance(eme, dict):
            eme["interaction_continuity_repair"] = repair_payload

    fem = out.get("_final_emission_meta")
    if isinstance(fem, dict):
        fem["interaction_continuity_repair"] = repair_payload


def _merge_interaction_continuity_enforced_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    enforced: bool,
) -> None:
    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        em = md_out.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em["interaction_continuity_enforced"] = enforced

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            emr = md_r.setdefault("emission_debug", {})
            if isinstance(emr, dict):
                emr["interaction_continuity_enforced"] = enforced

    if (
        eff_resolution is not None
        and eff_resolution is not resolution
        and isinstance(eff_resolution.get("metadata"), dict)
    ):
        eme = eff_resolution["metadata"].setdefault("emission_debug", {})
        if isinstance(eme, dict):
            eme["interaction_continuity_enforced"] = enforced

    fem = out.get("_final_emission_meta")
    if isinstance(fem, dict):
        fem["interaction_continuity_enforced"] = enforced


def _merge_interaction_continuity_speaker_bridge_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    bridge_payload: Dict[str, Any],
) -> None:
    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        em = md_out.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em["interaction_continuity_speaker_binding_bridge"] = bridge_payload

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            emr = md_r.setdefault("emission_debug", {})
            if isinstance(emr, dict):
                emr["interaction_continuity_speaker_binding_bridge"] = bridge_payload

    if (
        eff_resolution is not None
        and eff_resolution is not resolution
        and isinstance(eff_resolution.get("metadata"), dict)
    ):
        eme = eff_resolution["metadata"].setdefault("emission_debug", {})
        if isinstance(eme, dict):
            eme["interaction_continuity_speaker_binding_bridge"] = bridge_payload

    fem = out.get("_final_emission_meta")
    if isinstance(fem, dict):
        fem["interaction_continuity_speaker_binding_bridge"] = bridge_payload


def _ic_build_validation_payload(
    out: Dict[str, Any],
    final_text: str,
    *,
    resolution_for_contracts: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> tuple[Dict[str, Any], Dict[str, Any] | None]:
    ic_contract, _src = resolve_interaction_continuity_contract(
        out, resolution=resolution_for_contracts, session=session
    )
    rtc, _rtc_src = _resolve_response_type_contract(
        out, resolution=resolution_for_contracts, session=session
    )
    nested_ssc = None
    if isinstance(ic_contract, dict):
        ssc = ic_contract.get("speaker_selection_contract")
        if isinstance(ssc, dict):
            nested_ssc = ssc
    payload = validate_interaction_continuity(
        final_text,
        interaction_continuity_contract=ic_contract,
        speaker_selection_contract=nested_ssc,
        response_type_contract=rtc,
    )
    return payload, ic_contract


def _ssc_continuity_locked_or_single_speaker_constrained(ssc: Any) -> bool:
    if not isinstance(ssc, dict):
        return False
    if bool(ssc.get("continuity_locked")):
        return True
    if ssc.get("speaker_switch_allowed") is False:
        return True
    allowed = ssc.get("allowed_speaker_ids")
    if isinstance(allowed, list) and len(allowed) == 1:
        return True
    return False


def _speaker_enforcement_outcome_for_bridge(
    speaker_contract_enforcement: Dict[str, Any] | None,
) -> tuple[bool | None, str, Dict[str, Any]]:
    """Prefer post_validation when present (speaker layer already ran). Returns (ok, reason_code, signature)."""
    if not isinstance(speaker_contract_enforcement, dict):
        return None, "", {}

    def _sig_from(val: Any) -> Dict[str, Any]:
        if not isinstance(val, dict):
            return {}
        det = val.get("details")
        if not isinstance(det, dict):
            return {}
        s = det.get("signature")
        return s if isinstance(s, dict) else {}

    pv = speaker_contract_enforcement.get("post_validation")
    v = speaker_contract_enforcement.get("validation")
    if isinstance(pv, dict):
        return bool(pv.get("ok")), str(pv.get("reason_code") or ""), _sig_from(pv)
    if isinstance(v, dict):
        return bool(v.get("ok")), str(v.get("reason_code") or ""), _sig_from(v)
    return None, "", {}


def _canonical_speaker_display_from_ic_contract(ic_contract: Dict[str, Any] | None) -> str:
    if not isinstance(ic_contract, dict):
        return ""
    ssc = ic_contract.get("speaker_selection_contract")
    if isinstance(ssc, dict):
        name = str(ssc.get("primary_speaker_name") or "").strip()
        if name:
            return name
    return ""


def _looks_like_malformed_explicit_speaker_attribution(
    text: str | None,
    speaker_contract_enforcement: Dict[str, Any] | None,
) -> bool:
    """Narrow, deterministic cues for corrupted explicit attribution (fallback dialogue family)."""
    if not isinstance(text, str):
        return False
    t = text.strip()
    if not t:
        return False

    if re.search(r'\."\s+[A-Z]', t):
        return True

    if t[0].isalpha() and t[0].islower() and ('"' in t or "\u201c" in t or "\u201d" in t):
        return True

    dq = t.count('"')
    if dq % 2 == 1 and dq >= 1 and (re.search(r'[.!?]\s*"', t) or re.search(r'"\s*[A-Za-z]', t)):
        return True

    _ok, _rc, sig = _speaker_enforcement_outcome_for_bridge(speaker_contract_enforcement)
    lab = str(sig.get("speaker_label") or "").strip()
    if lab and ('"' in lab or ".\" " in lab or '.\"' in lab):
        return True
    sname = str(sig.get("speaker_name") or "").strip()
    if sname and ('"' in sname or ".\"" in sname):
        return True

    cn = ""
    if isinstance(speaker_contract_enforcement, dict):
        pv = speaker_contract_enforcement.get("post_validation")
        v = speaker_contract_enforcement.get("validation")
        cand = pv if isinstance(pv, dict) else v
        if isinstance(cand, dict):
            cn = str(cand.get("canonical_speaker_name") or "").strip()
    if (
        cn
        and bool(sig.get("is_explicitly_attributed"))
        and sname
        and sname.lower() != cn.lower()
        and (("." in sname) or ('"' in sname) or len(sname.split()) >= 4)
    ):
        return True

    return False


def _interaction_continuity_should_fail_from_speaker_binding(
    *,
    interaction_continuity_contract: Dict[str, Any] | None,
    interaction_continuity_validation: Dict[str, Any] | None,
    speaker_contract_enforcement: Dict[str, Any] | None,
    text: str,
) -> Dict[str, Any]:
    debug: Dict[str, Any] = {"malformed_attribution_detected": False}
    base: Dict[str, Any] = {
        "should_fail": False,
        "failure_reason": None,
        "synthetic_violation": None,
        "extra_violations": [],
        "debug": debug,
    }

    contract = interaction_continuity_contract if isinstance(interaction_continuity_contract, dict) else None
    if not contract or not contract.get("enabled"):
        debug["skipped"] = "contract_disabled"
        base["debug"] = debug
        return base
    if str(contract.get("continuity_strength") or "").strip().lower() != "strong":
        debug["skipped"] = "not_strong_continuity"
        base["debug"] = debug
        return base
    anchored = str(contract.get("anchored_interlocutor_id") or "").strip()
    if not anchored:
        debug["skipped"] = "no_anchor"
        base["debug"] = debug
        return base

    ssc = contract.get("speaker_selection_contract")
    if not _ssc_continuity_locked_or_single_speaker_constrained(ssc):
        debug["skipped"] = "speaker_contract_not_continuity_locked_or_single_speaker"
        base["debug"] = debug
        return base

    sp_ok, reason_code, _sig = _speaker_enforcement_outcome_for_bridge(speaker_contract_enforcement)
    if sp_ok is None:
        debug["skipped"] = "no_speaker_contract_enforcement"
        base["debug"] = debug
        return base
    if sp_ok is True:
        debug["skipped"] = "speaker_contract_ok"
        base["debug"] = debug
        return base
    if reason_code != _SPEAKER_REASON_SPEAKER_BINDING_MISMATCH:
        debug["skipped"] = "speaker_reason_not_binding_mismatch"
        debug["speaker_reason_code"] = reason_code
        base["debug"] = debug
        return base

    if not _looks_like_malformed_explicit_speaker_attribution(text, speaker_contract_enforcement):
        debug["skipped"] = "malformed_attribution_heuristic_negative"
        debug["speaker_reason_code"] = reason_code
        base["debug"] = debug
        return base

    debug["malformed_attribution_detected"] = True
    debug["speaker_reason_code"] = reason_code

    extra: List[str] = []
    cn = _canonical_speaker_display_from_ic_contract(contract)
    if cn and cn.lower() not in str(text).lower():
        extra.append("anchored_interlocutor_dropped")

    base.update(
        {
            "should_fail": True,
            "failure_reason": "speaker_binding_mismatch_under_strong_continuity",
            "synthetic_violation": "malformed_speaker_attribution_under_continuity",
            "extra_violations": extra,
            "debug": debug,
        }
    )
    return base


def _augment_ic_validation_with_speaker_bridge(
    payload: Dict[str, Any],
    bridge_result: Dict[str, Any],
) -> Dict[str, Any]:
    out = dict(payload)
    viol = list(out.get("violations") or [])
    sv = bridge_result.get("synthetic_violation")
    if isinstance(sv, str) and sv and sv not in viol:
        viol.append(sv)
    for x in bridge_result.get("extra_violations") or []:
        if isinstance(x, str) and x and x not in viol:
            viol.append(x)
    out["violations"] = viol
    out["ok"] = False
    dbg = dict(out.get("debug") or {})
    rp = list(dbg.get("reason_path") or [])
    if "speaker_binding_bridge" not in rp:
        rp.append("speaker_binding_bridge")
    dbg["reason_path"] = rp
    br_dbg = bridge_result.get("debug")
    if isinstance(br_dbg, dict) and br_dbg.get("speaker_reason_code"):
        dbg["speaker_binding_reason_code"] = br_dbg.get("speaker_reason_code")
    out["debug"] = dbg
    return out


def _maybe_apply_speaker_binding_bridge_to_payload(
    out: Dict[str, Any],
    norm: str,
    payload: Dict[str, Any],
    ic_contract: Dict[str, Any] | None,
    *,
    resolution_for_contracts: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    apply_bridge: bool,
) -> tuple[Dict[str, Any], Dict[str, Any] | None]:
    if not apply_bridge:
        return payload, None
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    em = md.get("emission_debug") if isinstance(md.get("emission_debug"), dict) else {}
    enc = em.get("speaker_contract_enforcement")
    enc_d = enc if isinstance(enc, dict) else None
    br = _interaction_continuity_should_fail_from_speaker_binding(
        interaction_continuity_contract=ic_contract,
        interaction_continuity_validation=payload,
        speaker_contract_enforcement=enc_d,
        text=norm,
    )
    if not br.get("should_fail"):
        return payload, None
    aug = _augment_ic_validation_with_speaker_bridge(payload, br)
    meta = {
        "applied": True,
        "failure_reason": br.get("failure_reason"),
        "synthetic_violation": br.get("synthetic_violation"),
        "speaker_reason_code": (br.get("debug") or {}).get("speaker_reason_code"),
        "malformed_attribution_detected": bool((br.get("debug") or {}).get("malformed_attribution_detected")),
    }
    _merge_interaction_continuity_speaker_bridge_into_outputs(
        out,
        resolution_for_contracts,
        eff_resolution,
        bridge_payload=meta,
    )
    return aug, br


def _apply_interaction_continuity_emission_step(
    out: Dict[str, Any],
    *,
    text: str,
    resolution_for_contracts: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    validate_only: bool,
    strict_social_path: bool,
    strict_fallback_resolution: Dict[str, Any] | None = None,
    apply_speaker_binding_bridge: bool = True,
) -> tuple[str, List[str], bool]:
    """Validate; optionally repair and enforce. Returns (text, extra_reasons, strict_continuity_fallback)."""
    norm = _normalize_text(text)
    payload, ic_contract = _ic_build_validation_payload(
        out,
        norm,
        resolution_for_contracts=resolution_for_contracts,
        session=session,
    )
    payload, _bridge_used = _maybe_apply_speaker_binding_bridge_to_payload(
        out,
        norm,
        payload,
        ic_contract,
        resolution_for_contracts=resolution_for_contracts,
        eff_resolution=eff_resolution,
        apply_bridge=apply_speaker_binding_bridge,
    )
    _merge_interaction_continuity_validation_into_outputs(
        out,
        resolution_for_contracts,
        eff_resolution,
        validation_payload=payload,
    )

    if validate_only:
        return norm, [], False

    if not isinstance(payload, dict) or not payload.get("enabled") or payload.get("ok") is True:
        return norm, [], False

    repair_result = repair_interaction_continuity(
        norm,
        validation=payload,
        interaction_continuity_contract=ic_contract,
    )
    pre_violations = list(payload.get("violations") or [])

    if repair_result.get("applied") is True:
        repaired = _normalize_text(str(repair_result.get("repaired_text") or norm))
        strat = list(repair_result.get("strategy_notes") or [])
        if (payload.get("debug") or {}).get("speaker_binding_reason_code"):
            bn = "speaker binding mismatch converted into continuity failure"
            if bn not in strat:
                strat = [bn] + strat
        _merge_interaction_continuity_repair_into_outputs(
            out,
            resolution_for_contracts,
            eff_resolution,
            repair_payload={
                "applied": True,
                "repair_type": repair_result.get("repair_type"),
                "violations": pre_violations,
                "strategy_notes": strat,
            },
        )
        payload2, _ = _ic_build_validation_payload(
            out,
            repaired,
            resolution_for_contracts=resolution_for_contracts,
            session=session,
        )
        payload2, _ = _maybe_apply_speaker_binding_bridge_to_payload(
            out,
            repaired,
            payload2,
            ic_contract,
            resolution_for_contracts=resolution_for_contracts,
            eff_resolution=eff_resolution,
            apply_bridge=False,
        )
        _merge_interaction_continuity_validation_into_outputs(
            out,
            resolution_for_contracts,
            eff_resolution,
            validation_payload=payload2,
        )
        return repaired, [], False

    strength = str(payload.get("continuity_strength") or "none").strip().lower()
    if strength == "soft":
        return norm, [], False

    _merge_interaction_continuity_enforced_into_outputs(
        out,
        resolution_for_contracts,
        eff_resolution,
        enforced=True,
    )
    if strict_social_path and isinstance(strict_fallback_resolution, dict):
        fb = minimal_social_emergency_fallback_line(strict_fallback_resolution)
        return _normalize_text(fb), [], True
    return norm, ["interaction_continuity_enforced"], False


def _attach_interaction_continuity_validation(
    out: Dict[str, Any],
    *,
    resolution_for_contracts: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    preserve_existing_validation: bool = False,
) -> None:
    if preserve_existing_validation:
        md_out = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
        em = md_out.get("emission_debug") if isinstance(md_out.get("emission_debug"), dict) else {}
        icv = em.get("interaction_continuity_validation")
        if isinstance(icv, dict):
            fem = out.setdefault("_final_emission_meta", {})
            if isinstance(fem, dict):
                fem["interaction_continuity_validation"] = icv
        return
    final_text = _normalize_text(out.get("player_facing_text"))
    _apply_interaction_continuity_emission_step(
        out,
        text=final_text,
        resolution_for_contracts=resolution_for_contracts,
        eff_resolution=eff_resolution,
        session=session,
        validate_only=True,
        strict_social_path=False,
    )


def _merge_speaker_enforcement_into_outputs(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    enforcement_payload: Dict[str, Any],
) -> None:
    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        em = md_out.setdefault("emission_debug", {})
        if isinstance(em, dict):
            em["speaker_contract_enforcement"] = enforcement_payload

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            emr = md_r.setdefault("emission_debug", {})
            if isinstance(emr, dict):
                emr["speaker_contract_enforcement"] = enforcement_payload

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        eme = eff_resolution["metadata"].setdefault("emission_debug", {})
        if isinstance(eme, dict):
            eme["speaker_contract_enforcement"] = enforcement_payload


def enforce_emitted_speaker_with_contract(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> tuple[str, Dict[str, Any]]:
    """Validate *text* against stored contract; repair if needed. Mutates *eff_resolution* social on repair paths."""
    trace = gm_output.get("trace") if isinstance(gm_output.get("trace"), dict) else None
    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else None
    contract = get_speaker_selection_contract(
        eff_resolution if isinstance(eff_resolution, dict) else None,
        metadata=md,
        trace=trace,
    )
    val = validate_emitted_speaker_against_contract(
        text,
        contract,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else resolution,
    )
    payload: Dict[str, Any] = {
        "contract_present": not (
            isinstance(contract.get("debug"), dict) and contract["debug"].get("contract_missing")
        ),
        "validation": val,
    }

    if val.get("ok") is True:
        payload["final_reason_code"] = val.get("reason_code")
        _merge_speaker_enforcement_into_outputs(gm_output, resolution, eff_resolution, enforcement_payload=payload)
        return text, payload

    repaired, final_rc, rdbg = _apply_speaker_contract_repairs(
        text,
        val,
        contract=contract,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        scene_id=scene_id,
        world=world,
    )
    payload["repair"] = rdbg
    payload["final_reason_code"] = final_rc
    payload["post_validation"] = validate_emitted_speaker_against_contract(
        repaired,
        contract,
        resolution=eff_resolution if isinstance(eff_resolution, dict) else resolution,
    )
    _merge_speaker_enforcement_into_outputs(gm_output, resolution, eff_resolution, enforcement_payload=payload)
    return repaired, payload


def _reply_kind(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    sp = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(sp.get("reply_kind") or "").strip().lower()


# --- Main entry: wires extracted validators/repairs + remaining in-module policy layers ---


def apply_final_emission_gate(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    scene: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Hard legal-state gate for the final emitted text.

    Orchestrates in-module policy layers with :mod:`game.final_emission_validators`,
    :mod:`game.final_emission_repairs`, and sanitizer/strict-social integration; see module
    docstring for ownership boundaries.
    """
    if not isinstance(gm_output, dict):
        return gm_output
    out = dict(gm_output)
    out = _gm_probe_for_answer_pressure_contracts(out, session if isinstance(session, dict) else None)
    pre_gate_text = _normalize_text(out.get("player_facing_text"))
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]

    eff_resolution, _effective_social_route, coercion_reason = effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    sid = str(scene_id or "").strip()
    strict_social_turn = strict_social_emission_will_apply(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
    )
    merged_for_suppress = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    strict_social_suppressed_non_social_turn = False
    strict_social_suppression_reason: str | None = None
    original_coercion_reason = coercion_reason
    if strict_social_turn:
        do_suppress, sup_reason = strict_social_suppress_non_native_coercion_for_narration_beat(
            resolution if isinstance(resolution, dict) else None,
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            sid,
            coercion_reason=coercion_reason,
            merged_player_prompt=merged_for_suppress,
        )
        if do_suppress:
            strict_social_suppressed_non_social_turn = True
            strict_social_suppression_reason = sup_reason
            strict_social_turn = False
            pre_gate_text = _normalize_text(
                sanitize_player_facing_output(
                    pre_gate_text,
                    {
                        "resolution": resolution if isinstance(resolution, dict) else None,
                        "include_resolution": True,
                        "session": session if isinstance(session, dict) else None,
                        "scene_id": sid,
                        "world": world if isinstance(world, dict) else None,
                        "tags": tag_list,
                    },
                )
            )
            eff_resolution = resolution if isinstance(resolution, dict) else None
            coercion_reason = f"{original_coercion_reason}|suppressed_non_social_narration:{sup_reason}"
            out["player_facing_text"] = pre_gate_text

    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    active_interlocutor = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    npc_id_for_meta = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        npc_id_for_meta = str(sp.get("npc_id") or "").strip()

    res_kind = str((eff_resolution or {}).get("kind") or "").strip().lower() if isinstance(eff_resolution, dict) else ""
    social_ic = ""
    if isinstance(eff_resolution, dict):
        sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        social_ic = str(sp.get("social_intent_class") or "").strip().lower()

    reasons: List[str] = []
    normalization_ran = False
    record_final_emission_gate_entry(out)
    if _apply_upstream_fallback_pregate_containment(out):
        pre_gate_text = _normalize_text(out.get("player_facing_text"))
    text = _normalize_text(out.get("player_facing_text"))
    response_type_debug = _default_response_type_debug(None, None)
    ac_layer_meta: Dict[str, Any] = {}
    rd_layer_meta: Dict[str, Any] = _default_response_delta_meta()
    srs_layer_meta: Dict[str, Any] = _default_social_response_structure_meta()
    fb_layer_meta: Dict[str, Any] = _default_fallback_behavior_meta()
    na_layer_meta: Dict[str, Any] = _default_narrative_authority_meta()
    te_layer_meta: Dict[str, Any] = _default_tone_escalation_meta()
    ar_layer_meta: Dict[str, Any] = _default_anti_railroading_meta()
    cs_layer_meta: Dict[str, Any] = _default_context_separation_meta()
    purity_layer_meta: Dict[str, Any] = _default_player_facing_narration_purity_meta()
    asp_layer_meta: Dict[str, Any] = _default_answer_shape_primacy_meta()
    ssa_layer_meta: Dict[str, Any] = {}
    ffnc_layer_meta: Dict[str, Any] = _default_fast_fallback_neutral_composition_meta()

    strict_social_active = bool(strict_social_turn)
    coercion_used = (
        "|" in original_coercion_reason
        or "synthetic" in original_coercion_reason
        or "npc_directed_guard" in original_coercion_reason
    )
    retry_output = any(
        isinstance(t, str) and ("question_retry_fallback" in t or "social_exchange_retry_fallback" in t)
        for t in tag_list
    )

    if strict_social_turn:
        normalization_ran = True
        text, details = build_final_strict_social_response(
            pre_gate_text,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            tags=tag_list,
            session=session if isinstance(session, dict) else None,
            scene_id=str(scene_id or "").strip(),
            world=world if isinstance(world, dict) else None,
        )
        text, response_type_debug = _enforce_response_type_contract(
            text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
            world=world if isinstance(world, dict) else None,
            strict_social_turn=True,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            active_interlocutor=active_interlocutor,
        )
        if response_type_debug.get("response_type_candidate_ok") is False and isinstance(eff_resolution, dict):
            text = minimal_social_emergency_fallback_line(eff_resolution)
            text, response_type_debug = _enforce_response_type_contract(
                text,
                gm_output=out,
                resolution=eff_resolution,
                session=session if isinstance(session, dict) else None,
                scene_id=sid,
                world=world if isinstance(world, dict) else None,
                strict_social_turn=True,
                strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
                active_interlocutor=active_interlocutor,
            )
            details = {
                **details,
                "used_internal_fallback": True,
                "fallback_kind": "response_type_contract_social_emergency",
                "fallback_pool": "response_type_contract",
                "final_emitted_source": "minimal_social_emergency_fallback",
                "rejection_reasons": list(details.get("rejection_reasons") or [])
                + list(response_type_debug.get("response_type_rejection_reasons") or []),
            }
        text, ac_layer_meta, _ = _apply_answer_completeness_layer(
            text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            strict_social_details=details,
            response_type_debug=response_type_debug,
            strict_social_path=True,
        )
        text, rd_layer_meta, _ = _apply_response_delta_layer(
            text,
            gm_output=out,
            strict_social_details=details,
            response_type_debug=response_type_debug,
            answer_completeness_meta=ac_layer_meta,
            strict_social_path=True,
        )
        text, srs_layer_meta, _ = _apply_social_response_structure_layer(
            text,
            gm_output=out,
            strict_social_details=details,
            response_type_debug=response_type_debug,
            answer_completeness_meta=ac_layer_meta,
            strict_social_path=True,
        )
        out["player_facing_text"] = text
        text, te_layer_meta, _ = _apply_tone_escalation_layer(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
            response_type_debug=response_type_debug,
        )
        if te_layer_meta.get("tone_escalation_violation_before_repair"):
            response_type_debug["non_hostile_escalation_blocked"] = True
        out["player_facing_text"] = text
        text, na_layer_meta, _ = _apply_narrative_authority_layer(
            text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            strict_social_details=details,
            response_type_debug=response_type_debug,
            answer_completeness_meta=ac_layer_meta,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )
        out["player_facing_text"] = text
        text, _speaker_contract_payload = enforce_emitted_speaker_with_contract(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            resolution=resolution if isinstance(resolution, dict) else None,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=sid,
        )
        _sync_eff_social_to_resolution(
            eff_resolution if isinstance(eff_resolution, dict) else None,
            resolution if isinstance(resolution, dict) else None,
        )
        out["player_facing_text"] = text
        text, ar_layer_meta, _ = _apply_anti_railroading_layer(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
            response_type_debug=response_type_debug,
            strict_social_details=details,
        )
        out["player_facing_text"] = text
        text, cs_layer_meta, _ = _apply_context_separation_layer(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
            response_type_debug=response_type_debug,
            strict_social_details=details,
        )
        out["player_facing_text"] = text
        text, purity_layer_meta, _ = _apply_player_facing_narration_purity_layer(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            response_type_debug=response_type_debug,
        )
        out["player_facing_text"] = text
        text, asp_layer_meta, _ = _apply_answer_shape_primacy_layer(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
            response_type_debug=response_type_debug,
            strict_social_details=details,
        )
        out["player_facing_text"] = text
        text, ssa_layer_meta = _apply_scene_state_anchor_layer(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            strict_social_details=details,
            response_type_debug=response_type_debug,
        )
        out["player_facing_text"] = text
        text, ffnc_layer_meta = _apply_fast_fallback_neutral_composition_layer(
            _normalize_text_preserve_paragraphs(text),
            gm_output=out,
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            scene_id=sid,
            strict_social_active=strict_social_active,
        )
        out["player_facing_text"] = text
        if ffnc_layer_meta.get("fast_fallback_neutral_composition_repaired"):
            realign_fallback_provenance_selector_to_current_text(
                out,
                text=str(text or ""),
                reason="fast_fallback_neutral_composition",
            )
        _merge_scene_state_anchor_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=ssa_layer_meta,
        )
        _merge_tone_escalation_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=te_layer_meta,
            gm_output=out,
        )
        _merge_narrative_authority_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=na_layer_meta,
            gm_output=out,
        )
        _merge_anti_railroading_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=ar_layer_meta,
            gm_output=out,
        )
        _merge_context_separation_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=cs_layer_meta,
        )
        _merge_player_facing_narration_purity_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=purity_layer_meta,
        )
        _merge_answer_shape_primacy_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=asp_layer_meta,
        )
        _merge_conversational_memory_inspection_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
        )
        if isinstance(eff_resolution, dict):
            sp = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
            npc_id_for_meta = str(sp.get("npc_id") or "").strip()
        final_emitted_source = str(details.get("final_emitted_source") or "unknown_post_gate_writer")
        if response_type_debug.get("response_type_repair_used"):
            final_emitted_source = str(
                response_type_debug.get("response_type_repair_kind") or "response_type_contract_repair"
            )
        if retry_output:
            final_emitted_source = "retry_output"
        if ac_layer_meta.get("answer_completeness_repaired"):
            final_emitted_source = str(
                ac_layer_meta.get("answer_completeness_repair_mode") or "answer_completeness_repair"
            )
        if rd_layer_meta.get("response_delta_repaired"):
            final_emitted_source = str(
                rd_layer_meta.get("response_delta_repair_mode") or "response_delta_repair"
            )
        if srs_layer_meta.get("social_response_structure_repair_applied") and srs_layer_meta.get(
            "social_response_structure_passed"
        ):
            final_emitted_source = str(
                srs_layer_meta.get("social_response_structure_repair_mode")
                or "social_response_structure_repair"
            )
        if na_layer_meta.get("narrative_authority_repaired"):
            final_emitted_source = str(
                na_layer_meta.get("narrative_authority_repair_mode") or "narrative_authority_repair"
            )
        if te_layer_meta.get("tone_escalation_repaired"):
            final_emitted_source = str(
                te_layer_meta.get("tone_escalation_repair_mode") or "tone_escalation_repair"
            )
        if ar_layer_meta.get("anti_railroading_repaired"):
            final_emitted_source = str(
                ar_layer_meta.get("anti_railroading_repair_mode") or "anti_railroading_repair"
            )
        if cs_layer_meta.get("context_separation_repaired"):
            final_emitted_source = str(
                cs_layer_meta.get("context_separation_repair_mode") or "context_separation_repair"
            )
        if fb_layer_meta.get("fallback_behavior_repaired"):
            final_emitted_source = str(
                fb_layer_meta.get("fallback_behavior_repair_mode") or "fallback_behavior_repair"
            )
        if purity_layer_meta.get("player_facing_narration_purity_repaired"):
            final_emitted_source = "player_facing_narration_purity_repair"
        if asp_layer_meta.get("answer_shape_primacy_repaired"):
            final_emitted_source = str(
                asp_layer_meta.get("answer_shape_primacy_repair_mode") or "answer_shape_primacy_repair"
            )
        if ffnc_layer_meta.get("fast_fallback_neutral_composition_repaired"):
            final_emitted_source = str(
                ffnc_layer_meta.get("fast_fallback_neutral_composition_repair_mode")
                or "fast_fallback_neutral_composition_repair"
            )
        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        if not details.get("used_internal_fallback"):
            log_final_emission_decision(
                {
                    "stage": "final_emission_gate",
                    "social_route": strict_social_turn,
                    "coercion_reason": coercion_reason,
                    "resolution_kind": res_kind,
                    "social_intent_class": social_ic,
                    "active_interlocutor": active_interlocutor or None,
                    "candidate_ok": True,
                    "rejection_reasons": [],
                    "fallback_pool": str(details.get("fallback_pool") or "none"),
                    "fallback_kind": str(details.get("fallback_kind") or "none"),
                    **_response_type_decision_payload(response_type_debug),
                }
            )
            out["_final_emission_meta"] = {
                "final_route": "accept_candidate",
                "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
                "strict_social_active": strict_social_active,
                "coercion_used": coercion_used,
                "active_interlocutor_id": active_interlocutor or None,
                "npc_id": npc_id_for_meta or None,
                "normalization_ran": normalization_ran,
                "candidate_validation_passed": True,
                "deterministic_social_fallback_attempted": bool(details.get("deterministic_attempted")),
                "deterministic_social_fallback_passed": bool(details.get("deterministic_passed")),
                "final_emitted_source": final_emitted_source,
                "post_gate_mutation_detected": post_gate_mutation_detected,
                "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
                "coercion_reason": coercion_reason,
                "candidate_quality_degraded": bool(details.get("candidate_quality_degraded")),
                "resolved_answer_preferred": bool(details.get("resolved_answer_preferred")),
                "resolved_answer_source": details.get("resolved_answer_source"),
                "resolved_answer_preference_reason": details.get("resolved_answer_preference_reason"),
                "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
                "strict_social_suppression_reason": strict_social_suppression_reason,
                "social_emission_integrity_replaced": bool(details.get("social_emission_integrity_replaced")),
                "social_emission_integrity_reasons": details.get("social_emission_integrity_reasons"),
                "social_emission_integrity_fallback_kind": details.get("social_emission_integrity_fallback_kind"),
                "speaker_contract_enforcement_reason": _speaker_contract_payload.get("final_reason_code"),
            }
            _flag_non_hostile_escalation_from_writer_pregate(
                pre_gate_text,
                gm_output=out,
                resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                session=session if isinstance(session, dict) else None,
                response_type_debug=response_type_debug,
            )
            _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
            _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
            _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
            _merge_social_response_structure_meta(out["_final_emission_meta"], srs_layer_meta)
            _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
            _merge_tone_escalation_meta(out["_final_emission_meta"], te_layer_meta)
            _merge_anti_railroading_meta(out["_final_emission_meta"], ar_layer_meta)
            _merge_context_separation_meta(out["_final_emission_meta"], cs_layer_meta)
            _merge_player_facing_narration_purity_meta(out["_final_emission_meta"], purity_layer_meta)
            _merge_answer_shape_primacy_meta(out["_final_emission_meta"], asp_layer_meta)
            _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
            _merge_fallback_behavior_meta(out["_final_emission_meta"], fb_layer_meta)
            _merge_fast_fallback_neutral_composition_meta(out["_final_emission_meta"], ffnc_layer_meta)
            grounded_fm_exempt = _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id(
                out,
                session=session,
                scene=scene,
                world=world,
                scene_id=sid,
                eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                active_interlocutor=active_interlocutor,
                strict_social_active=strict_social_active,
            )
            out = _apply_visibility_enforcement(
                out,
                session=session,
                scene=scene,
                world=world,
                scene_id=sid,
                eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                active_interlocutor=active_interlocutor,
                strict_social_active=strict_social_active,
                strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
                grounded_speaker_first_mention_exemption_entity_id=grounded_fm_exempt,
            )
            ic_strict_text, _, ic_strict_fb = _apply_interaction_continuity_emission_step(
                out,
                text=_normalize_text(out.get("player_facing_text")),
                resolution_for_contracts=eff_resolution if isinstance(eff_resolution, dict) else None,
                eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                session=session if isinstance(session, dict) else None,
                validate_only=False,
                strict_social_path=True,
                strict_fallback_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            )
            out["player_facing_text"] = ic_strict_text
            if ic_strict_fb:
                out["tags"] = list(out.get("tags") or []) + [
                    "final_emission_gate_replaced",
                    "final_emission_gate:interaction_continuity",
                ]
                fem_patch = out.get("_final_emission_meta")
                if isinstance(fem_patch, dict):
                    fem_patch["final_emitted_source"] = "minimal_social_emergency_fallback"
                    gtxt = _normalize_text(ic_strict_text)
                    fem_patch["final_text_preview"] = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
                    fem_patch["post_gate_mutation_detected"] = pre_gate_text != gtxt
            fb_text, fb_layer_meta, _ = _apply_fallback_behavior_layer(
                _normalize_text(out.get("player_facing_text")),
                gm_output=out,
                resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                strict_social_path=True,
                session=session if isinstance(session, dict) else None,
                scene_id=sid,
            )
            out["player_facing_text"] = fb_text
            _merge_fallback_behavior_into_emission_debug(
                out,
                resolution if isinstance(resolution, dict) else None,
                eff_resolution if isinstance(eff_resolution, dict) else None,
                gate_meta=fb_layer_meta,
            )
            fem_patch = out.get("_final_emission_meta")
            if isinstance(fem_patch, dict):
                _merge_fallback_behavior_meta(fem_patch, fb_layer_meta)
                gtxt = _normalize_text(fb_text)
                fem_patch["final_text_preview"] = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
                fem_patch["post_gate_mutation_detected"] = pre_gate_text != gtxt
                if fb_layer_meta.get("fallback_behavior_repaired"):
                    fem_patch["final_emitted_source"] = str(
                        fb_layer_meta.get("fallback_behavior_repair_mode") or "fallback_behavior_repair"
                    )
            _attach_interaction_continuity_validation(
                out,
                resolution_for_contracts=eff_resolution if isinstance(eff_resolution, dict) else None,
                eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                session=session if isinstance(session, dict) else None,
                preserve_existing_validation=True,
            )
            _merge_narration_constraint_debug_into_outputs(
                out,
                resolution if isinstance(resolution, dict) else None,
                eff_resolution if isinstance(eff_resolution, dict) else None,
                session=session if isinstance(session, dict) else None,
                scene=scene if isinstance(scene, dict) else None,
                world=world if isinstance(world, dict) else None,
                response_type_debug=response_type_debug,
                speaker_contract_enforcement=_speaker_contract_payload,
            )
            log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
            return _finalize_emission_output(
                out,
                pre_gate_text=pre_gate_text,
                fast_path=_final_emission_fast_path_eligible(out),
            )

        fb_kind = str(details.get("fallback_kind") or "none")
        deterministic_attempted = bool(details.get("deterministic_attempted"))
        deterministic_passed = bool(details.get("deterministic_passed"))
        fallback_pool = str(details.get("fallback_pool") or "social_deterministic")
        candidate_ok = False
        rejection_reasons = details.get("rejection_reasons") if isinstance(details.get("rejection_reasons"), list) else []
        rejection_reasons = list(rejection_reasons) + list(response_type_debug.get("response_type_rejection_reasons") or [])

        out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fb_kind}"]
        if final_emitted_source == "minimal_social_emergency_fallback":
            out["tags"] = list(out["tags"]) + ["terminal_strict_social_emission", "strict_social_terminal_safe"]

        if details.get("route_illegal_intercepted"):
            dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
            preview = str(details.get("intercepted_preview") or "")
            out["debug_notes"] = (
                (dbg + " | " if dbg else "")
                + f"final_emission_gate:route_illegal_writer_intercepted:{preview[:80]}"
            )

        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + "final_emission_gate:replaced:"
            + ",".join([str(r) for r in rejection_reasons[:8] if isinstance(r, str)])
        )
        log_final_emission_decision(
            {
                "stage": "final_emission_gate",
                "social_route": strict_social_turn,
                "coercion_reason": coercion_reason,
                "resolution_kind": res_kind,
                "social_intent_class": social_ic,
                "active_interlocutor": active_interlocutor or None,
                "candidate_ok": candidate_ok,
                "rejection_reasons": [str(r) for r in rejection_reasons[:12] if isinstance(r, str)],
                "fallback_pool": fallback_pool,
                "fallback_kind": fb_kind,
                **_response_type_decision_payload(response_type_debug),
            }
        )
        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        out["_final_emission_meta"] = {
            "final_route": "replaced",
            "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
            "strict_social_active": strict_social_active,
            "coercion_used": coercion_used,
            "active_interlocutor_id": active_interlocutor or None,
            "npc_id": npc_id_for_meta or None,
            "normalization_ran": normalization_ran,
            "candidate_validation_passed": False,
            "deterministic_social_fallback_attempted": deterministic_attempted,
            "deterministic_social_fallback_passed": deterministic_passed,
            "final_emitted_source": final_emitted_source,
            "post_gate_mutation_detected": post_gate_mutation_detected,
            "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
            "coercion_reason": coercion_reason,
            "rejection_reasons_sample": [str(r) for r in rejection_reasons[:8] if isinstance(r, str)],
            "candidate_quality_degraded": bool(details.get("candidate_quality_degraded")),
            "resolved_answer_preferred": bool(details.get("resolved_answer_preferred")),
            "resolved_answer_source": details.get("resolved_answer_source"),
            "resolved_answer_preference_reason": details.get("resolved_answer_preference_reason"),
            "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
            "strict_social_suppression_reason": strict_social_suppression_reason,
            "speaker_contract_enforcement_reason": _speaker_contract_payload.get("final_reason_code"),
        }
        _flag_non_hostile_escalation_from_writer_pregate(
            pre_gate_text,
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            response_type_debug=response_type_debug,
        )
        _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
        _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
        _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
        _merge_social_response_structure_meta(out["_final_emission_meta"], srs_layer_meta)
        _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
        _merge_tone_escalation_meta(out["_final_emission_meta"], te_layer_meta)
        _merge_anti_railroading_meta(out["_final_emission_meta"], ar_layer_meta)
        _merge_context_separation_meta(out["_final_emission_meta"], cs_layer_meta)
        _merge_player_facing_narration_purity_meta(out["_final_emission_meta"], purity_layer_meta)
        _merge_answer_shape_primacy_meta(out["_final_emission_meta"], asp_layer_meta)
        _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
        _merge_fallback_behavior_meta(out["_final_emission_meta"], fb_layer_meta)
        _merge_fast_fallback_neutral_composition_meta(out["_final_emission_meta"], ffnc_layer_meta)
        grounded_fm_exempt = _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
        )
        out = _apply_visibility_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            grounded_speaker_first_mention_exemption_entity_id=grounded_fm_exempt,
        )
        fb_text, fb_layer_meta, _ = _apply_fallback_behavior_layer(
            _normalize_text(out.get("player_facing_text")),
            gm_output=out,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            strict_social_path=True,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )
        out["player_facing_text"] = fb_text
        _merge_fallback_behavior_into_emission_debug(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            gate_meta=fb_layer_meta,
        )
        fem_patch = out.get("_final_emission_meta")
        if isinstance(fem_patch, dict):
            _merge_fallback_behavior_meta(fem_patch, fb_layer_meta)
            gtxt = _normalize_text(fb_text)
            fem_patch["final_text_preview"] = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
            fem_patch["post_gate_mutation_detected"] = pre_gate_text != gtxt
            if fb_layer_meta.get("fallback_behavior_repaired"):
                fem_patch["final_emitted_source"] = str(
                    fb_layer_meta.get("fallback_behavior_repair_mode") or "fallback_behavior_repair"
                )
        _attach_interaction_continuity_validation(
            out,
            resolution_for_contracts=eff_resolution if isinstance(eff_resolution, dict) else None,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
        )
        _merge_narration_constraint_debug_into_outputs(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
            response_type_debug=response_type_debug,
            speaker_contract_enforcement=_speaker_contract_payload,
        )
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
        return _finalize_emission_output(
            out,
            pre_gate_text=pre_gate_text,
            fast_path=_final_emission_fast_path_eligible(out),
        )

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")
    if _passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene,
        scene_id=sid,
    ) and not _reply_already_has_concrete_interaction(text):
        reasons.append("passive_scene_pressure_missing_concrete_beat")

    text, response_type_debug = _enforce_response_type_contract(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        world=world if isinstance(world, dict) else None,
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        active_interlocutor=active_interlocutor,
    )
    if response_type_debug.get("response_type_candidate_ok") is False:
        reasons.extend(
            [str(r) for r in (response_type_debug.get("response_type_rejection_reasons") or []) if isinstance(r, str)]
        )

    text, ac_layer_meta, ac_reasons = _apply_answer_completeness_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        strict_social_path=False,
    )
    reasons.extend(ac_reasons)

    text, rd_layer_meta, rd_reasons = _apply_response_delta_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        strict_social_path=False,
    )
    reasons.extend(rd_reasons)

    text, srs_layer_meta, srs_reasons = _apply_social_response_structure_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        strict_social_path=False,
    )
    reasons.extend(srs_reasons)

    text, te_layer_meta, te_reasons = _apply_tone_escalation_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
    )
    if te_layer_meta.get("tone_escalation_violation_before_repair"):
        response_type_debug["non_hostile_escalation_blocked"] = True
    reasons.extend(te_reasons)

    text, na_layer_meta, na_reasons = _apply_narrative_authority_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        strict_social_details=None,
        response_type_debug=response_type_debug,
        answer_completeness_meta=ac_layer_meta,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
    )
    reasons.extend(na_reasons)

    text, ar_layer_meta, ar_reasons = _apply_anti_railroading_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=None,
    )
    reasons.extend(ar_reasons)

    text, cs_layer_meta, cs_reasons = _apply_context_separation_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=None,
    )
    reasons.extend(cs_reasons)

    text, purity_layer_meta, purity_extra = _apply_player_facing_narration_purity_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        response_type_debug=response_type_debug,
    )
    reasons.extend(purity_extra)

    text, asp_layer_meta, asp_extra = _apply_answer_shape_primacy_layer(
        text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
        response_type_debug=response_type_debug,
        strict_social_details=None,
    )
    reasons.extend(asp_extra)

    text, ssa_layer_meta = _apply_scene_state_anchor_layer(
        text,
        gm_output=out,
        strict_social_details=None,
        response_type_debug=response_type_debug,
    )
    out["player_facing_text"] = _normalize_text(text)
    text, ffnc_layer_meta = _apply_fast_fallback_neutral_composition_layer(
        _normalize_text(text),
        gm_output=out,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
        strict_social_active=strict_social_active,
    )
    out["player_facing_text"] = _normalize_text(text)
    if ffnc_layer_meta.get("fast_fallback_neutral_composition_repaired"):
        realign_fallback_provenance_selector_to_current_text(
            out,
            text=str(out.get("player_facing_text") or ""),
            reason="fast_fallback_neutral_composition",
        )
    _merge_scene_state_anchor_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=ssa_layer_meta,
    )
    _merge_tone_escalation_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=te_layer_meta,
        gm_output=out,
    )
    _merge_narrative_authority_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=na_layer_meta,
        gm_output=out,
    )
    _merge_anti_railroading_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=ar_layer_meta,
        gm_output=out,
    )
    _merge_context_separation_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=cs_layer_meta,
    )
    _merge_player_facing_narration_purity_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=purity_layer_meta,
    )
    _merge_answer_shape_primacy_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=asp_layer_meta,
    )
    _merge_conversational_memory_inspection_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
    )

    ic_text, ic_extra_reasons, _ic_strict_fb = _apply_interaction_continuity_emission_step(
        out,
        text=_normalize_text(text),
        resolution_for_contracts=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        validate_only=False,
        strict_social_path=False,
    )
    reasons.extend(ic_extra_reasons)
    text = ic_text
    out["player_facing_text"] = _normalize_text(text)
    text, fb_layer_meta, fb_extra = _apply_fallback_behavior_layer(
        _normalize_text(text),
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        strict_social_path=False,
        session=session if isinstance(session, dict) else None,
        scene_id=sid,
    )
    reasons.extend(fb_extra)
    out["player_facing_text"] = _normalize_text(text)
    _merge_fallback_behavior_into_emission_debug(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        gate_meta=fb_layer_meta,
    )

    candidate_ok = not bool(reasons)
    fallback_pool = "none"
    fallback_kind = "none"
    deterministic_attempted = False
    deterministic_passed = False
    final_emitted_source = "unknown_post_gate_writer"

    if not reasons:
        out["player_facing_text"] = text
        final_emitted_source = "generated_candidate"
        if response_type_debug.get("response_type_repair_used"):
            final_emitted_source = str(
                response_type_debug.get("response_type_repair_kind") or "response_type_contract_repair"
            )
        if retry_output:
            final_emitted_source = "retry_output"
        if ac_layer_meta.get("answer_completeness_repaired"):
            final_emitted_source = str(
                ac_layer_meta.get("answer_completeness_repair_mode") or "answer_completeness_repair"
            )
        if rd_layer_meta.get("response_delta_repaired"):
            final_emitted_source = str(
                rd_layer_meta.get("response_delta_repair_mode") or "response_delta_repair"
            )
        if srs_layer_meta.get("social_response_structure_repair_applied") and srs_layer_meta.get(
            "social_response_structure_passed"
        ):
            final_emitted_source = str(
                srs_layer_meta.get("social_response_structure_repair_mode")
                or "social_response_structure_repair"
            )
        if na_layer_meta.get("narrative_authority_repaired"):
            final_emitted_source = str(
                na_layer_meta.get("narrative_authority_repair_mode") or "narrative_authority_repair"
            )
        if te_layer_meta.get("tone_escalation_repaired"):
            final_emitted_source = str(
                te_layer_meta.get("tone_escalation_repair_mode") or "tone_escalation_repair"
            )
        if ar_layer_meta.get("anti_railroading_repaired"):
            final_emitted_source = str(
                ar_layer_meta.get("anti_railroading_repair_mode") or "anti_railroading_repair"
            )
        if cs_layer_meta.get("context_separation_repaired"):
            final_emitted_source = str(
                cs_layer_meta.get("context_separation_repair_mode") or "context_separation_repair"
            )
        if fb_layer_meta.get("fallback_behavior_repaired"):
            final_emitted_source = str(
                fb_layer_meta.get("fallback_behavior_repair_mode") or "fallback_behavior_repair"
            )
        if purity_layer_meta.get("player_facing_narration_purity_repaired"):
            final_emitted_source = "player_facing_narration_purity_repair"
        if asp_layer_meta.get("answer_shape_primacy_repaired"):
            final_emitted_source = str(
                asp_layer_meta.get("answer_shape_primacy_repair_mode") or "answer_shape_primacy_repair"
            )
        if ffnc_layer_meta.get("fast_fallback_neutral_composition_repaired"):
            final_emitted_source = str(
                ffnc_layer_meta.get("fast_fallback_neutral_composition_repair_mode")
                or "fast_fallback_neutral_composition_repair"
            )

        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        log_final_emission_decision(
            {
                "stage": "final_emission_gate",
                "social_route": strict_social_turn,
                "coercion_reason": coercion_reason,
                "resolution_kind": res_kind,
                "social_intent_class": social_ic,
                "active_interlocutor": active_interlocutor or None,
                "candidate_ok": True,
                "rejection_reasons": [],
                "fallback_pool": fallback_pool,
                "fallback_kind": fallback_kind,
                **_response_type_decision_payload(response_type_debug),
            }
        )
        out["_final_emission_meta"] = {
            "final_route": "accept_candidate",
            "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
            "strict_social_active": strict_social_active,
            "coercion_used": coercion_used,
            "active_interlocutor_id": active_interlocutor or None,
            "npc_id": npc_id_for_meta or None,
            "normalization_ran": normalization_ran,
            "candidate_validation_passed": True,
            "deterministic_social_fallback_attempted": False,
            "deterministic_social_fallback_passed": False,
            "final_emitted_source": final_emitted_source,
            "post_gate_mutation_detected": post_gate_mutation_detected,
            "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
            "coercion_reason": coercion_reason,
            "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
            "strict_social_suppression_reason": strict_social_suppression_reason,
        }
        _flag_non_hostile_escalation_from_writer_pregate(
            pre_gate_text,
            gm_output=out,
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            response_type_debug=response_type_debug,
        )
        _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
        _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
        _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
        _merge_social_response_structure_meta(out["_final_emission_meta"], srs_layer_meta)
        _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
        _merge_tone_escalation_meta(out["_final_emission_meta"], te_layer_meta)
        _merge_anti_railroading_meta(out["_final_emission_meta"], ar_layer_meta)
        _merge_context_separation_meta(out["_final_emission_meta"], cs_layer_meta)
        _merge_player_facing_narration_purity_meta(out["_final_emission_meta"], purity_layer_meta)
        _merge_answer_shape_primacy_meta(out["_final_emission_meta"], asp_layer_meta)
        _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
        _merge_fallback_behavior_meta(out["_final_emission_meta"], fb_layer_meta)
        _merge_fast_fallback_neutral_composition_meta(out["_final_emission_meta"], ffnc_layer_meta)
        grounded_fm_exempt = _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
        )
        out = _apply_visibility_enforcement(
            out,
            session=session,
            scene=scene,
            world=world,
            scene_id=sid,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            active_interlocutor=active_interlocutor,
            strict_social_active=strict_social_active,
            strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
            grounded_speaker_first_mention_exemption_entity_id=grounded_fm_exempt,
        )
        _attach_interaction_continuity_validation(
            out,
            resolution_for_contracts=resolution if isinstance(resolution, dict) else None,
            eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
        )
        _merge_narration_constraint_debug_into_outputs(
            out,
            resolution if isinstance(resolution, dict) else None,
            eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
            response_type_debug=response_type_debug,
        )
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
        return _finalize_emission_output(
            out,
            pre_gate_text=pre_gate_text,
            fast_path=_final_emission_fast_path_eligible(out),
        )

    # Non-social replace path only (strict-social replacement is handled in build_final_strict_social_response).
    suppress_intro_replace = anti_reset_suppresses_intro_style_fallbacks(
        session if isinstance(session, dict) else None,
        scene if isinstance(scene, dict) else None,
        world if isinstance(world, dict) else None,
        sid,
        resolution if isinstance(resolution, dict) else None,
    )
    mode = str((inspected or {}).get("interaction_mode") or "").strip().lower()
    if (
        active_interlocutor
        and mode == "social"
        and isinstance(world, dict)
        and not strict_social_suppressed_non_social_turn
    ):
        mini_res: Dict[str, Any] = {
            "kind": "question",
            "social": {
                "npc_id": active_interlocutor,
                "npc_name": _npc_display_name_for_emission(world, sid, active_interlocutor),
                "social_intent_class": "social_exchange",
            },
        }
        fallback_pool = "social_active_interlocutor_minimal"
        fallback_text = minimal_social_emergency_fallback_line(mini_res)
        fallback_kind = "social_interlocutor_fallback"
        final_emitted_source = "social_interlocutor_minimal_fallback"
    else:
        passive_candidates = _passive_scene_pressure_fallback_candidates(
            session=session if isinstance(session, dict) else None,
            scene=scene,
            scene_id=sid,
        )
        if passive_candidates:
            (
                fallback_text,
                fallback_pool,
                fallback_kind,
                final_emitted_source,
                _fallback_strategy,
                _fallback_candidate_source,
                _composition_meta,
            ) = passive_candidates[0]
        elif _should_use_neutral_nonprogress_fallback_instead_of_global_stock(session, eff_resolution):
            fallback_pool = "npc_pursuit_fail_closed_neutral"
            fallback_text = "Nothing confirms progress toward that lead yet—the moment stays unresolved."
            fallback_kind = "npc_pursuit_neutral_nonprogress"
            final_emitted_source = "npc_pursuit_neutral_fallback"
        elif suppress_intro_replace:
            fallback_pool = "anti_reset_local_continuation"
            fallback_text = local_exchange_continuation_fallback_line(
                session=session if isinstance(session, dict) else None,
                world=world if isinstance(world, dict) else None,
                scene_id=sid,
                resolution=resolution if isinstance(resolution, dict) else None,
            )
            fallback_kind = "anti_reset_continuation_fallback"
            final_emitted_source = "anti_reset_local_continuation_fallback"
        else:
            fallback_pool = "global_scene_narrative"
            fallback_text = _global_narrative_fallback_stock_line(scene if isinstance(scene, dict) else None, scene_id=sid)
            fallback_kind = "narrative_safe_fallback"
            final_emitted_source = "global_scene_fallback"
    deterministic_attempted = False
    deterministic_passed = False

    out["player_facing_text"] = fallback_text
    out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fallback_kind}"]

    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:replaced:"
        + ",".join(reasons[:8])
    )
    log_final_emission_decision(
        {
            "stage": "final_emission_gate",
            "social_route": strict_social_turn,
            "coercion_reason": coercion_reason,
            "resolution_kind": res_kind,
            "social_intent_class": social_ic,
            "active_interlocutor": active_interlocutor or None,
            "candidate_ok": candidate_ok,
            "rejection_reasons": reasons[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
            **_response_type_decision_payload(response_type_debug),
        }
    )
    gate_out_text = _normalize_text(out.get("player_facing_text"))
    post_gate_mutation_detected = pre_gate_text != gate_out_text

    out["_final_emission_meta"] = {
        "final_route": "replaced",
        "reply_kind": _reply_kind(eff_resolution if isinstance(eff_resolution, dict) else None),
        "strict_social_active": strict_social_active,
        "coercion_used": coercion_used,
        "active_interlocutor_id": active_interlocutor or None,
        "npc_id": npc_id_for_meta or None,
        "normalization_ran": normalization_ran,
        "candidate_validation_passed": False,
        "deterministic_social_fallback_attempted": deterministic_attempted,
        "deterministic_social_fallback_passed": deterministic_passed,
        "final_emitted_source": final_emitted_source,
        "post_gate_mutation_detected": post_gate_mutation_detected,
        "final_text_preview": (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text,
        "coercion_reason": coercion_reason,
        "rejection_reasons_sample": reasons[:8],
        "strict_social_suppressed_non_social_turn": strict_social_suppressed_non_social_turn,
        "strict_social_suppression_reason": strict_social_suppression_reason,
        "anti_reset_intro_suppressed": bool(suppress_intro_replace),
    }
    _flag_non_hostile_escalation_from_writer_pregate(
        pre_gate_text,
        gm_output=out,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        response_type_debug=response_type_debug,
    )
    _merge_response_type_meta(out["_final_emission_meta"], response_type_debug)
    _merge_answer_completeness_meta(out["_final_emission_meta"], ac_layer_meta)
    _merge_response_delta_meta(out["_final_emission_meta"], rd_layer_meta)
    _merge_social_response_structure_meta(out["_final_emission_meta"], srs_layer_meta)
    _merge_narrative_authority_meta(out["_final_emission_meta"], na_layer_meta)
    _merge_tone_escalation_meta(out["_final_emission_meta"], te_layer_meta)
    _merge_anti_railroading_meta(out["_final_emission_meta"], ar_layer_meta)
    _merge_context_separation_meta(out["_final_emission_meta"], cs_layer_meta)
    _merge_player_facing_narration_purity_meta(out["_final_emission_meta"], purity_layer_meta)
    _merge_answer_shape_primacy_meta(out["_final_emission_meta"], asp_layer_meta)
    _merge_scene_state_anchor_meta(out["_final_emission_meta"], ssa_layer_meta)
    _merge_fallback_behavior_meta(out["_final_emission_meta"], fb_layer_meta)
    grounded_fm_exempt = _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
    )
    out = _apply_visibility_enforcement(
        out,
        session=session,
        scene=scene,
        world=world,
        scene_id=sid,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        strict_social_active=strict_social_active,
        strict_social_suppressed_non_social_turn=strict_social_suppressed_non_social_turn,
        grounded_speaker_first_mention_exemption_entity_id=grounded_fm_exempt,
    )
    _attach_interaction_continuity_validation(
        out,
        resolution_for_contracts=resolution if isinstance(resolution, dict) else None,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    _merge_narration_constraint_debug_into_outputs(
        out,
        resolution if isinstance(resolution, dict) else None,
        eff_resolution if isinstance(eff_resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        response_type_debug=response_type_debug,
    )
    log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
    return _finalize_emission_output(
        out,
        pre_gate_text=pre_gate_text,
        fast_path=_final_emission_fast_path_eligible(out),
    )
