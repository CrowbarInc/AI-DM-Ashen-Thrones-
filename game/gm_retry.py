from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import copy
import json
import re

from game.prompt_context import (
    NO_VALIDATOR_VOICE_RULE,
    RESPONSE_RULE_PRIORITY,
    RULE_PRIORITY_COMPACT_INSTRUCTION,
    canonical_interaction_target_npc_id,
)
from game.social import (
    select_best_social_answer_candidate,
    sync_strategy_forced_to_answer_for_valid_followup_alignment,
)
from game.storage import load_scene, get_scene_runtime
from game.interaction_context import (
    evaluate_world_action_social_continuity_break,
    inspect as inspect_interaction_context,
    world_action_turn_suppresses_npc_answer_fallback,
)
from game.anti_reset_emission_guard import (
    anti_reset_suppresses_intro_style_fallbacks,
    local_exchange_continuation_fallback_line,
    text_matches_observe_opener_templates,
    text_overlaps_known_scene_intro_sources,
)
from game.diegetic_fallback_narration import (
    render_nonsocial_terminal_anchor_line,
    render_observe_perception_fallback_line,
    render_travel_arrival_fallback_line,
)
from game.fallback_provenance_debug import preserve_fallback_provenance_metadata
from game.stage_diff_telemetry import (
    record_stage_snapshot,
    record_stage_transition,
    resolve_gate_turn_packet,
    snapshot_turn_stage,
)
from game.turn_packet import get_turn_packet, resolve_turn_packet_contract

from game.gm import (
    _apply_uncertainty_to_gm,
    _clean_scene_detail,
    _ensure_terminal_punctuation,
    _extract_scene_momentum_kind,
    _first_sentence,
    _is_direct_player_question,
    _opening_sentence_should_skip_echo_check,
    _resolve_scene_id,
    _resolve_scene_location,
    _scene_momentum_due,
    _scene_visible_facts,
    _session_social_authority,
    _topic_pressure_snapshot_for_reply,
    classify_player_intent,
    classify_uncertainty,
    detect_forbidden_generic_phrases,
    detect_stock_warning_filler_repetition,
    detect_validator_voice,
    followup_soft_repetition_check,
    npc_response_contract_check,
    opening_sentence_echoes_player_input,
    opening_sentence_overlaps_player_quote,
    question_resolution_rule_check,
    render_uncertainty_response,
    resolve_known_fact_before_uncertainty,
    _is_valid_player_facing_fallback_answer,
)


def _retry_resolve_turn_packet(
    gm_output: Optional[Dict[str, Any]],
    response_policy: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Prefer :func:`resolve_gate_turn_packet` on *gm_output*, then :func:`get_turn_packet` with *response_policy*."""
    if isinstance(gm_output, dict):
        cached = resolve_gate_turn_packet(gm_output)
        if isinstance(cached, dict):
            return cached
    return get_turn_packet(gm_output or {}, response_policy)


def _gm_binding():
    import game.gm as gm

    return gm


RETRY_FAILURE_PRIORITY: dict[str, int] = {
    "unresolved_question": 10,
    "validator_voice": 20,
    "npc_contract_failure": 30,
    "topic_pressure_escalation": 33,
    "followup_soft_repetition": 35,
    # Just below scene_stall: when a stored social answer exists, prefer stating it over stall/echo retries.
    "answer": 39,
    "scene_stall": 40,
    "echo_or_repetition": 50,
    "forbidden_generic_phrase": 60,
}

# Candidate kinds that justify suppressing scene_stall / echo_or_repetition in favor of an answer retry.
_SOCIAL_FORCE_ANSWER_CANDIDATE_KINDS: frozenset[str] = frozenset(
    {"structured_fact", "reconciled_fact", "partial_answer"}
)
MAX_TARGETED_RETRY_ATTEMPTS = 2

_PERCEPTION_FALLBACK_RESOLUTION_KINDS: frozenset[str] = frozenset(
    {
        "observe",
        "investigate",
        "search",
        "already_searched",
        "discover_clue",
        "interact",
        "scene_opening",
    }
)


def _resolution_implies_destination_arrival(resolution: Dict[str, Any] | None) -> bool:
    if not isinstance(resolution, dict):
        return False
    k = str(resolution.get("kind") or "").strip().lower()
    if k not in {"scene_transition", "travel"}:
        return False
    if resolution.get("resolved_transition") is True:
        return True
    sc = resolution.get("state_changes")
    if isinstance(sc, dict):
        if sc.get("scene_transition_occurred") or sc.get("scene_changed") or sc.get("arrived_at_scene"):
            return True
    return False


def resolution_is_open_crowd_social(resolution: Dict[str, Any] | None) -> bool:
    """True for broadcast / open-call turns (no single addressee, reaction-shaped contract)."""
    if not isinstance(resolution, dict):
        return False
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if str(soc.get("social_intent_class") or "").strip().lower() == "open_call":
        return True
    return bool(soc.get("open_social_solicitation") and soc.get("npc_reply_expected") is not True)


def _is_usable_retry_tone_escalation_contract(candidate: Any) -> bool:
    """True for shipped tone contracts or prompt_debug mirrors that carry allow_* flags."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict):
        return True
    jf = candidate.get("justification_flags")
    if isinstance(jf, dict) and candidate.get("max_allowed_tone") is not None:
        return True
    if (
        "allow_explicit_threat" in candidate
        and "allow_physical_hostility" in candidate
        and "allow_combat_initiation" in candidate
    ):
        return True
    return False


def _resolve_retry_tone_escalation_contract(
    gm_output: Optional[Dict[str, Any]],
    response_policy: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Read tone_escalation from response_policy / gm_output only (no contract rebuild)."""
    pkt = _retry_resolve_turn_packet(gm_output, response_policy)
    if isinstance(pkt, dict):
        te = resolve_turn_packet_contract(pkt, "tone_escalation")
        if _is_usable_retry_tone_escalation_contract(te):
            return te
    candidates: List[Any] = []
    if isinstance(response_policy, dict):
        candidates.append(response_policy.get("tone_escalation"))
    if isinstance(gm_output, dict):
        pol = gm_output.get("response_policy")
        if isinstance(pol, dict):
            candidates.append(pol.get("tone_escalation"))
        for key in ("narration_payload", "prompt_payload", "_narration_payload"):
            pl = gm_output.get(key)
            if not isinstance(pl, dict):
                continue
            candidates.append(pl.get("tone_escalation"))
            rp = pl.get("response_policy")
            if isinstance(rp, dict):
                candidates.append(rp.get("tone_escalation"))
        md = gm_output.get("metadata")
        if isinstance(md, dict):
            candidates.append(md.get("tone_escalation"))
            rp = md.get("response_policy")
            if isinstance(rp, dict):
                candidates.append(rp.get("tone_escalation"))
        tr = gm_output.get("trace")
        if isinstance(tr, dict):
            candidates.append(tr.get("tone_escalation"))
            rp = tr.get("response_policy")
            if isinstance(rp, dict):
                candidates.append(rp.get("tone_escalation"))
    for item in candidates:
        if _is_usable_retry_tone_escalation_contract(item):
            return item
    return None


def _retry_allows_hostile_escalation(
    gm_output: Optional[Dict[str, Any]] = None,
    *,
    response_policy: Optional[Dict[str, Any]] = None,
) -> bool:
    """True only when shipped policy explicitly allows threat / physical harm / combat initiation."""
    te = _resolve_retry_tone_escalation_contract(gm_output, response_policy)
    if te is None:
        return False
    if te.get("enabled") is False:
        return False
    return bool(te.get("allow_explicit_threat")) or bool(te.get("allow_physical_hostility")) or bool(
        te.get("allow_combat_initiation")
    )


def _is_shipped_full_anti_railroading_contract(candidate: Any) -> bool:
    """True for ``build_anti_railroading_contract`` / ``prompt_context`` payloads."""
    if not isinstance(candidate, dict):
        return False
    return "forbid_player_decision_override" in candidate and "enabled" in candidate


def _coerce_anti_railroading_contract_dict(maybe: Any) -> Optional[Dict[str, Any]]:
    if _is_shipped_full_anti_railroading_contract(maybe):
        return maybe
    return None


def _resolve_anti_railroading_contract_for_retry(
    response_policy: Optional[Dict[str, Any]],
    gm_output: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Prefer policy/contract already attached to narration (aligns with final_emission_gate resolution)."""
    pkt = _retry_resolve_turn_packet(gm_output, response_policy)
    if isinstance(pkt, dict):
        arc = resolve_turn_packet_contract(pkt, "anti_railroading")
        hit_pkt = _coerce_anti_railroading_contract_dict(arc)
        if hit_pkt:
            return hit_pkt
    candidates: List[Any] = []
    if isinstance(response_policy, dict):
        candidates.append(response_policy.get("anti_railroading"))
    if isinstance(gm_output, dict):
        candidates.append(gm_output.get("anti_railroading_contract"))
        pol = gm_output.get("response_policy")
        if isinstance(pol, dict):
            candidates.append(pol.get("anti_railroading"))
        pc = gm_output.get("prompt_context")
        if isinstance(pc, dict):
            candidates.append(pc.get("anti_railroading_contract"))
            pol2 = pc.get("response_policy")
            if isinstance(pol2, dict):
                candidates.append(pol2.get("anti_railroading"))
        for key in ("narration_payload", "prompt_payload", "_narration_payload"):
            pl = gm_output.get(key)
            if not isinstance(pl, dict):
                continue
            candidates.append(pl.get("anti_railroading_contract"))
            candidates.append(pl.get("anti_railroading"))
            rp = pl.get("response_policy")
            if isinstance(rp, dict):
                candidates.append(rp.get("anti_railroading"))
        md = gm_output.get("metadata")
        if isinstance(md, dict):
            candidates.append(md.get("anti_railroading_contract"))
            rp = md.get("response_policy")
            if isinstance(rp, dict):
                candidates.append(rp.get("anti_railroading"))
        tr = gm_output.get("trace")
        if isinstance(tr, dict):
            candidates.append(tr.get("anti_railroading_contract"))
            rp = tr.get("response_policy")
            if isinstance(rp, dict):
                candidates.append(rp.get("anti_railroading"))
    for item in candidates:
        hit = _coerce_anti_railroading_contract_dict(item)
        if hit:
            return hit
    return None


def _format_anti_railroading_retry_guidance(arc: Optional[Dict[str, Any]]) -> str:
    """Compact retry-only instructions; uses shipped contract flags when present (see prompt_context / gate)."""
    base = (
        "RETRY AGENCY (ANTI-RAILROADING): Energetic forward motion through more hooks, consequences, tension, "
        "and concrete world or NPC response—without choosing for the player. Advance using one or more of: "
        "actionable options, a new clue, a new opening, a consequence, a reaction, social or procedural pressure, "
        "a bounded refusal, or a clarified hard constraint. "
        "Do not narrate the PC moving, traveling, deciding, committing, or concluding unless authoritative state "
        "already settled it or the player explicitly did. "
        "Avoid auto-travel, auto-commitment, meta-story gravity (e.g. the story wants/pulls/sends you), forced "
        "conclusions (e.g. it's obvious you must), and momentum language that collapses agency. "
        "A salient lead may be highlighted as optional; do not convert leads into the only real path unless "
        "allow_exclusivity_from_authoritative_resolution applies. "
        "Prefer phrasing like 'one option,' 'another path,' 'two immediate openings,' "
        "'the obstacle rules out X but leaves Y or Z' over 'you go,' 'you decide,' 'you must,' or 'the only way.' "
    )
    if not isinstance(arc, dict) or arc.get("enabled") is False:
        return base

    extras: List[str] = []
    if arc.get("allow_directional_language_from_resolved_transition"):
        extras.append(
            "If a transition is already resolved in authoritative state, arrival or continuation language may match "
            "that settled movement (do not reopen it)."
        )
    if arc.get("allow_exclusivity_from_authoritative_resolution"):
        extras.append(
            "When authoritative state truly collapses alternatives, exclusivity may match that resolution."
        )
    if arc.get("allow_commitment_language_when_player_explicitly_committed"):
        extras.append(
            "You may echo explicit player-stated commitment; do not invent new PC commitment or decisive action."
        )
    ids = arc.get("surfaced_lead_ids") if isinstance(arc.get("surfaced_lead_ids"), list) else []
    if len(ids) > 1:
        extras.append(
            "Multiple leads are in play; keep them salient but optional unless exclusivity is justified."
        )
    if extras:
        return base + "Contract tail: " + " ".join(extras) + " "
    return base


# --- Context separation (shipped contract + retry steer; no validation/repair here) -----------------


def _is_shipped_context_separation_contract(candidate: Any) -> bool:
    """True for ``build_context_separation_contract`` payloads (aligned with final_emission_gate)."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict) and "forbid_topic_hijack" in candidate:
        return True
    if "forbid_topic_hijack" in candidate and "max_pressure_sentences_without_player_prompt" in candidate:
        return True
    return False


def _coerce_context_separation_contract_dict(maybe: Any) -> Optional[Dict[str, Any]]:
    if _is_shipped_context_separation_contract(maybe):
        return maybe
    return None


def _context_separation_contract_from_emission_debug(em: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(em, dict):
        return None
    for ck in ("context_separation_contract", "context_separation"):
        hit = _coerce_context_separation_contract_dict(em.get(ck))
        if hit:
            return hit
    return None


def _resolve_context_separation_contract_for_retry(
    gm_output: Optional[Dict[str, Any]],
    response_policy: Optional[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Prefer the already-built contract from policy / narration mirrors (same order as final_emission_gate)."""
    pkt = _retry_resolve_turn_packet(gm_output, response_policy)
    if isinstance(pkt, dict):
        csp = resolve_turn_packet_contract(pkt, "context_separation")
        hit_pkt = _coerce_context_separation_contract_dict(csp)
        if hit_pkt:
            return hit_pkt, "turn_packet.contracts.context_separation"
    if isinstance(response_policy, dict):
        for key in ("context_separation_contract", "context_separation"):
            hit = _coerce_context_separation_contract_dict(response_policy.get(key))
            if hit:
                return hit, f"response_policy.{key}"
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
        hit_ed = _context_separation_contract_from_emission_debug(pl.get("emission_debug"))
        if hit_ed:
            return hit_ed, f"{key}.emission_debug"
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
        hit_ed = _context_separation_contract_from_emission_debug(md.get("emission_debug"))
        if hit_ed:
            return hit_ed, "metadata.emission_debug"
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
        hit_ed = _context_separation_contract_from_emission_debug(tr.get("emission_debug"))
        if hit_ed:
            return hit_ed, "trace.emission_debug"
    hit_ed = _context_separation_contract_from_emission_debug(gm_output.get("emission_debug"))
    if hit_ed:
        return hit_ed, "emission_debug"
    return None, None


def _pressure_focus_allowed_from_contract(contract: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(contract, dict):
        return False
    df = contract.get("debug_flags")
    if isinstance(df, dict) and "pressure_focus_allowed" in df:
        return bool(df.get("pressure_focus_allowed"))
    return False


def _debug_marker_has_nonempty_violations(marker: str) -> bool:
    if "cs_violations=" not in marker:
        return False
    tail = marker.split("cs_violations=", 1)[1]
    blob = tail.split(";", 1)[0].strip()
    return bool(blob) and blob != "none"


def _scan_dict_for_context_separation_trouble(d: Any, prefix: str, sink: List[str]) -> None:
    if not isinstance(d, dict):
        return
    if d.get("context_separation_failed") is True:
        sink.append(f"{prefix}:context_separation_failed")
    if d.get("context_separation_repaired") is True:
        sink.append(f"{prefix}:context_separation_repaired")
    fr = d.get("context_separation_failure_reasons")
    if isinstance(fr, list) and any(isinstance(x, str) and x.strip() for x in fr):
        sink.append(f"{prefix}:context_separation_failure_reasons")
    mr = d.get("context_separation_debug_reason_marker")
    if isinstance(mr, str) and mr.strip():
        if _debug_marker_has_nonempty_violations(mr):
            sink.append(f"{prefix}:context_separation_debug_reason_marker_violations")
        if "repair_applied=True" in mr:
            sink.append(f"{prefix}:repair_applied_true")
    em = d.get("emission_debug")
    if isinstance(em, dict):
        nested = em.get("context_separation")
        if isinstance(nested, dict):
            val = nested.get("validation") if isinstance(nested.get("validation"), dict) else {}
            if val.get("passed") is False:
                sink.append(f"{prefix}.emission_debug.context_separation:validation_failed")
            frn = nested.get("failure_reasons")
            if isinstance(frn, list) and any(isinstance(x, str) and x.strip() for x in frn):
                sink.append(f"{prefix}.emission_debug.context_separation:failure_reasons")
        for fk in (
            "context_separation_failed",
            "context_separation_repaired",
        ):
            if em.get(fk) is True:
                sink.append(f"{prefix}.emission_debug:{fk}")


def prior_context_separation_trouble_signals(gm_output: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """True when prior attempt metadata/trace suggests context separation failure or repair (retry bias)."""
    if not isinstance(gm_output, dict):
        return False, []
    raw: List[str] = []
    for blob, prefix in (
        (gm_output.get("_final_emission_meta"), "_final_emission_meta"),
        (gm_output.get("metadata"), "metadata"),
        (gm_output.get("trace"), "trace"),
        (gm_output, "gm_root"),
    ):
        _scan_dict_for_context_separation_trouble(blob, prefix, raw)
    ordered = list(dict.fromkeys(raw))
    return (bool(ordered), ordered)


def _format_context_separation_retry_guidance(
    contract: Optional[Dict[str, Any]],
    *,
    local_first_recovery: bool,
    pressure_focus_allowed: bool,
) -> str:
    """Compact retry-only steer; does not restate the full contract or perform gate-style repair."""
    tone_guard = (
        "Do not escalate harshness, threats, or interpersonal hostility based only on ambient danger or background tension; "
        "tone caps from the tone contract still apply. "
    )
    if pressure_focus_allowed:
        core = (
            "CONTEXT SEPARATION (RETRY STEER): Keep the response concrete and interaction-linked. "
            "Broader pressure may stay central because this turn allows pressure focus under the shipped contract—"
            "but avoid abstract monologue, generic doom narration, or vagueness in place of actionable local substance. "
            + tone_guard
        )
        if local_first_recovery:
            core += (
                "Still open with substantive payoff tied to the present exchange (answer, reaction, or scene-tied consequence)—"
                "not a detached atmosphere paragraph. "
            )
        return core

    if isinstance(contract, dict):
        scope = (
            "Broader ambient pressure may dominate only when the shipped contract marks it as locally relevant for this exchange. "
        )
    else:
        scope = "If wider pressure is not clearly grounded in the present interaction, keep it subordinate. "

    base = (
        "CONTEXT SEPARATION (RETRY STEER): Keep the local exchange primary; answer or react to the immediate interaction first. "
        "Ambient pressure may briefly color the reply but must not replace it. "
        "Do not harden tone from background tension alone. "
        + scope
        + tone_guard
    )
    if local_first_recovery:
        base += (
            "LOCAL-FIRST RECOVERY: Open with the answer, reaction, or concrete NPC beat—do not open with atmosphere, city-scale mood, "
            "or 'the city is tense' style filler. Suppress broad unrest/war/faction exposition as a substitute for substance. "
            "Use at most one short ambient-pressure clause after local payoff unless the contract explicitly allows pressure focus. "
        )
    else:
        base += (
            "Bias toward direct local answers, concrete NPC responses, immediate consequences of the player's present action, "
            "and present-scene sensory detail; keep ambient coloring contract-compatible and subordinate. "
            "Avoid vague ominous paragraphs and escalation in harshness funded only by ambient pressure. "
        )
    return base


def _context_separation_local_first_supplement(failure_class: str) -> str:
    """Extra one-line steer for specific failure classes when recovering from CS trouble (generation bias only)."""
    fc = str(failure_class or "").strip()
    if fc == "topic_pressure_escalation":
        return (
            " Add concrete escalation through immediate on-screen handles (named detail, procedure, time cost, witness)—"
            "not a broader war/unrest monologue. "
        )
    if fc == "scene_stall":
        return " Advance the scene with a local beat (visible object, NPC line, sound, constraint) before wide political weather. "
    if fc == "echo_or_repetition":
        return " Vary prose with new local information; do not substitute a fresh ambient-threat paragraph for substance. "
    if fc in ("followup_soft_repetition",):
        return " Add new local specifics; avoid restating city-scale tension as the escalation. "
    if fc in ("npc_contract_failure",):
        return " Ground the NPC reply in immediate interaction stakes before any ambient color. "
    if fc in ("unresolved_question", "answer"):
        return " Put the bounded answer in sentence one; do not lead with ambient pressure. "
    if fc == "forbidden_generic_phrase":
        return " Replace generics with scene-tied specifics, not with vague tension filler. "
    return ""


def _fill_context_separation_retry_debug_sink(
    sink: Dict[str, Any],
    *,
    contract: Optional[Dict[str, Any]],
    contract_source: Optional[str],
    trouble: bool,
    signals: List[str],
    local_first_recovery: bool,
    pressure_focus_allowed: bool,
    guidance_preview: str,
) -> None:
    sink["retry_context_separation_contract_resolved"] = contract is not None
    sink["retry_context_separation_contract_source"] = contract_source
    sink["retry_context_separation_prior_trouble"] = trouble
    sink["retry_context_separation_prior_signals"] = list(signals)
    sink["retry_context_separation_local_first_recovery"] = local_first_recovery
    sink["retry_context_separation_pressure_focus_allowed"] = pressure_focus_allowed
    sink["retry_context_separation_guidance"] = guidance_preview.strip()


def _fill_fallback_behavior_retry_debug_sink(
    sink: Dict[str, Any],
    *,
    response_policy: Dict[str, Any] | None,
    gm_output: Dict[str, Any] | None,
) -> None:
    policy = response_policy if isinstance(response_policy, dict) else {}
    gm_d = gm_output if isinstance(gm_output, dict) else {}
    fb_contract = policy.get("fallback_behavior")
    if not isinstance(fb_contract, dict):
        rp = gm_d.get("response_policy")
        if isinstance(rp, dict) and isinstance(rp.get("fallback_behavior"), dict):
            fb_contract = rp.get("fallback_behavior")
    sink["retry_fallback_behavior_contract_present"] = isinstance(fb_contract, dict)
    if isinstance(fb_contract, dict):
        sink["retry_fallback_behavior_uncertainty_active"] = bool(fb_contract.get("uncertainty_active"))
        sink["retry_fallback_behavior_uncertainty_mode"] = fb_contract.get("uncertainty_mode")
        sink["retry_fallback_behavior_prefer_partial"] = bool(fb_contract.get("prefer_partial_over_question"))

    meta = gm_d.get("_final_emission_meta") if isinstance(gm_d.get("_final_emission_meta"), dict) else {}
    sink["retry_fallback_behavior_checked"] = bool(meta.get("fallback_behavior_checked"))
    sink["retry_fallback_behavior_failed"] = bool(meta.get("fallback_behavior_failed"))
    sink["retry_fallback_behavior_repaired"] = bool(meta.get("fallback_behavior_repaired"))
    sink["retry_fallback_behavior_skip_reason"] = meta.get("fallback_behavior_skip_reason")
    sink["retry_fallback_behavior_failure_reasons"] = list(meta.get("fallback_behavior_failure_reasons") or [])


def build_retry_prompt_for_failure(
    failure: Dict[str, Any],
    *,
    response_policy: Dict[str, Any] | None = None,
    gm_output: Dict[str, Any] | None = None,
    retry_debug_sink: Dict[str, Any] | None = None,
    player_text: str = "",
) -> str:
    """Build a narrowly scoped retry instruction for one failure class only."""
    failure_class = str((failure or {}).get("failure_class") or "").strip()
    reasons = [str(r).strip() for r in ((failure or {}).get("reasons") or []) if isinstance(r, str) and str(r).strip()]
    priority_order = (
        list((response_policy or {}).get("rule_priority_order") or [])
        if isinstance((response_policy or {}).get("rule_priority_order"), list)
        else [label for _, label in RESPONSE_RULE_PRIORITY]
    )
    ar_guidance = _format_anti_railroading_retry_guidance(
        _resolve_anti_railroading_contract_for_retry(response_policy, gm_output)
    )
    cs_contract, cs_src = _resolve_context_separation_contract_for_retry(gm_output, response_policy)
    cs_trouble, cs_signals = prior_context_separation_trouble_signals(gm_output)
    pf_allowed = _pressure_focus_allowed_from_contract(cs_contract)
    local_first_recovery = bool(cs_trouble)
    cs_guidance = _format_context_separation_retry_guidance(
        cs_contract,
        local_first_recovery=local_first_recovery,
        pressure_focus_allowed=pf_allowed,
    )
    cs_supplement = _context_separation_local_first_supplement(failure_class) if local_first_recovery else ""
    if retry_debug_sink is not None:
        _fill_context_separation_retry_debug_sink(
            retry_debug_sink,
            contract=cs_contract,
            contract_source=cs_src,
            trouble=cs_trouble,
            signals=cs_signals,
            local_first_recovery=local_first_recovery,
            pressure_focus_allowed=pf_allowed,
            guidance_preview=cs_guidance + cs_supplement,
        )
        _fill_fallback_behavior_retry_debug_sink(
            retry_debug_sink,
            response_policy=response_policy,
            gm_output=gm_output,
        )
    shared = (
        f"Rule Priority Hierarchy: {priority_order}. "
        f"{RULE_PRIORITY_COMPACT_INSTRUCTION} "
        f"{ar_guidance}"
        f"{cs_guidance}"
        f"Retry target: {failure_class}. Correct only this failure class. Return the same JSON shape."
    )

    if failure_class == "validator_voice":
        return (
            f"{shared} Rewrite the reply into diegetic, world-facing phrasing only. "
            f"{NO_VALIDATOR_VOICE_RULE} "
            "Remove validator, system, limitation, tool-access, model-identity, and rules-explanation language from standard narration."
            f"{cs_supplement}"
        )

    if failure_class == "answer":
        patched = dict(failure or {})
        patched["failure_class"] = "unresolved_question"
        return build_retry_prompt_for_failure(
            patched,
            response_policy=response_policy,
            gm_output=gm_output,
            retry_debug_sink=retry_debug_sink,
            player_text=player_text,
        )

    allow_hostile = _retry_allows_hostile_escalation(gm_output, response_policy=response_policy)

    if failure_class == "unresolved_question":
        known_fact_context = (failure or {}).get("known_fact_context") if isinstance((failure or {}).get("known_fact_context"), dict) else {}
        known_answer = str(known_fact_context.get("answer") or "").strip()
        reasons_low = [
            str(r).strip().lower()
            for r in reasons
            if isinstance(r, str) and str(r).strip()
        ]
        first_sentence_failed = any(
            ("first_sentence_not_explicit_answer" in reason)
            or reason.startswith("question_rule:social_exchange_first_sentence_")
            for reason in reasons_low
        )
        social_exchange_first_sentence_failed = any(
            reason.startswith("question_rule:social_exchange_first_sentence_")
            for reason in reasons_low
        )
        val_fc = (
            "answer"
            if any(isinstance(r, str) and r.startswith("social_answer_candidate:") for r in reasons)
            else "unresolved_question"
        )
        if known_answer and not _is_valid_player_facing_fallback_answer(
            known_answer,
            player_text=str(player_text or ""),
            known_fact={
                "source": str(known_fact_context.get("source") or ""),
                "subject": str(known_fact_context.get("subject") or ""),
                "position": str(known_fact_context.get("position") or ""),
            },
            failure_class=val_fc,
        ):
            known_answer = ""

        if known_answer:
            known_source = str(known_fact_context.get("source") or "").strip()
            source_hint = f" Established source: {known_source}." if known_source else ""
            social_shape_hint = (
                " Social exchange contract: sentence one must be speaker-grounded and substantive "
                "(usable information: warnings, directions, names, concrete facts, bounded uncertainty, refusal, or pressure—"
                "not cinematic stall or scene-padding)."
                if social_exchange_first_sentence_failed
                else ""
            )
            return (
                f"{shared} A direct answer is already established in current scene state or dialogue continuity. "
                f"Use this answer or a close paraphrase in the first sentence: {known_answer}.{source_hint} "
                "First sentence contract: answer the asked question directly in sentence one. "
                "Do not open with scene summary, atmosphere, or setup. "
                "No advisory phrasing (do not use: 'you should', 'you could', 'best lead', 'try', 'consider'). "
                "Do not reroute it into uncertainty, refusal, or generic fallback language. "
                "Do not narrate the player acting on, accepting, or committing to the answer unless they already did."
                f"{social_shape_hint}{cs_supplement}"
            )
        uncertainty_category = str((failure or {}).get("uncertainty_category") or "").strip()
        uncertainty_context = (failure or {}).get("uncertainty_context") if isinstance((failure or {}).get("uncertainty_context"), dict) else {}
        speaker = uncertainty_context.get("speaker") if isinstance(uncertainty_context.get("speaker"), dict) else {}
        scene_snapshot = uncertainty_context.get("scene_snapshot") if isinstance(uncertainty_context.get("scene_snapshot"), dict) else {}
        speaker_name = str(speaker.get("name") or "").strip()
        speaker_role = str(speaker.get("role") or "").strip().lower()
        location = str(scene_snapshot.get("location") or "").strip()
        first_visible = str(scene_snapshot.get("first_visible_detail") or "").strip()
        context_parts: List[str] = []
        if speaker_role == "npc" and speaker_name:
            context_parts.append(f"Answer from {speaker_name}'s plausible local perspective.")
        elif location:
            context_parts.append(f"Anchor the reply in visible details from {location}.")
        if first_visible:
            context_parts.append(f"Use scene specifics like: {first_visible}.")
        category_hint = f" Uncertainty category: {uncertainty_category}." if uncertainty_category else ""
        context_hint = (" " + " ".join(context_parts)) if context_parts else ""
        first_sentence_hint = (
            " First sentence failed previously: sentence one MUST be an explicit answer with no scene-preface."
            if first_sentence_failed
            else ""
        )
        speaker_hint = (
            f" NPC-directed answer contract: sentence one must be explicitly grounded to {speaker_name}'s viewpoint."
            if speaker_role == "npc" and speaker_name
            else ""
        )
        social_shape_hint = (
            " Social exchange contract: sentence one must be speaker-grounded and substantive "
            "(usable information: warnings, directions, concrete facts, bounded uncertainty, refusal, or pressure—"
            "not cinematic stall or scene-padding)."
            if social_exchange_first_sentence_failed
            else ""
        )
        return (
            f"{shared} The player's direct question still lacks a bounded answer. "
            "Single-purpose rewrite: fix answer shape only. "
            "Sentence one MUST directly answer the exact player question. "
            "Do not begin with atmosphere, scene summary, or recap. "
            "Do not ask a question back. Do not refuse, deflect, or explain limitations. "
            "No advisory phrasing (avoid: 'you should', 'you could', 'best lead', 'try', 'consider'). "
            "If certainty is incomplete, keep uncertainty concrete and bounded to speaker evidence or scene facts. "
            "While fixing answer shape, do not narrate the PC's travel, commitment, or decisive action."
            f"{category_hint}{context_hint}{first_sentence_hint}{speaker_hint}{social_shape_hint}{cs_supplement}"
        )

    if failure_class == "echo_or_repetition":
        return (
            f"{shared} Semantically rewrite the reply so it does not echo the player's wording or quoted speech. "
            "Change sentence structure and phrasing, and react with new information or consequence instead of restating the input. "
            "Keep agency intact: do not slip into narrating the PC's decision, travel, or commitment as you vary the prose."
            f"{cs_supplement}"
        )

    if failure_class == "followup_soft_repetition":
        ctx = (failure or {}).get("followup_context") if isinstance((failure or {}).get("followup_context"), dict) else {}
        prev_player = str(ctx.get("previous_player_input") or "").strip()
        prev_answer = str(ctx.get("previous_answer_snippet") or "").strip()
        topic_tokens = ctx.get("topic_tokens") if isinstance(ctx.get("topic_tokens"), list) else []
        topic_hint = f" Topic tokens: {topic_tokens}." if topic_tokens else ""
        prev_player_hint = f" Previous player press: {prev_player}." if prev_player else ""
        prev_answer_hint = f" Previous answer snippet (do not recycle): {prev_answer}." if prev_answer else ""
        hostile_guard = (
            ""
            if allow_hostile
            else (
                " Do not move to threats, violence, weapons, brandished steel, or hostile interruption—"
                "topic pressure alone is not justification."
            )
        )
        grounded_hostile = (
            " If the tone contract allows explicit threat or physical hostility, you may add a grounded confrontation beat "
            "only when it fits established scene tension or visible authority roles—never arbitrary aggression."
            if allow_hostile
            else ""
        )
        return (
            f"{shared} The player is pressing the same topic again, and your reply repeated the prior answer without escalation."
            f"{topic_hint}{prev_player_hint}{prev_answer_hint} "
            "Do NOT restate the same underlying lead. Escalate with new content: add one concrete detail AND one of "
            "(a) a named person/place/faction/witness (with an in-world source), or (b) a narrowed unknown boundary (time window, location bracket, condition, count). "
            "End with a sharper player-facing opening that uses the new detail (options, leverage, or cost)—without "
            "narrating the PC's decision, destination, or commitment, and without upgrading one lead into the only real path. "
            "Preserve speaker grounding and diegetic voice."
            f"{hostile_guard}{grounded_hostile}{cs_supplement}"
        )

    if failure_class == "npc_contract_failure":
        missing = [str(x).strip() for x in ((failure or {}).get("missing") or []) if isinstance(x, str) and str(x).strip()]
        missing_hint = f" Missing contract elements: {missing}." if missing else ""
        return (
            f"{shared} Produce a direct NPC answer, reaction, or refusal consistent with the current target. "
            "Include at least one concrete person, place, faction, next step, or directly usable condition, time, or location. "
            "Deliver NPC-side substance the player can react to; do not narrate the PC deciding, moving, or committing."
            f"{missing_hint}{cs_supplement}"
        )

    if failure_class == "topic_pressure_escalation":
        ctx = (failure or {}).get("topic_context") if isinstance((failure or {}).get("topic_context"), dict) else {}
        topic_key = str(ctx.get("topic_key") or "").strip()
        prev_answer = str(ctx.get("previous_answer_snippet") or "").strip()
        repeat_count = int(ctx.get("repeat_count", 0) or 0)
        topic_hint = f" Topic key: {topic_key}." if topic_key else ""
        prev_answer_hint = f" Prior low-gain answer (do not paraphrase): {prev_answer}." if prev_answer else ""
        if allow_hostile:
            escalation_menu = (
                "You MUST escalate now with diegetic motion. Prefer one of: concrete clue tied to an on-screen detail; "
                "bounded refusal that changes what is at stake; tightened scrutiny or procedural questioning; authority or policy pressure; "
                "deadline or time cost; environmental shift others notice; social or reputation consequence; narrowing opportunity window; "
                "or a named lead (NPC, faction, or place) the speaker can credibly cite. "
                "Only if the tone contract already allows threat or physical hostility—and the scene has established grounds—"
                "you may add a calibrated confrontation, conditional threat, or physical beat that fits that contract. "
                "Do not invent random aggression."
            )
        else:
            escalation_menu = (
                "You MUST escalate now with diegetic motion without threats, violence, weapons, hostile interruption, or physical pressure—"
                "topic pressure alone does not unlock hostility. "
                "Choose one: concrete clue tied to an on-screen detail; bounded refusal that changes what is at stake; "
                "tightened scrutiny or procedural questioning; authority or policy pressure; deadline or time cost; "
                "environmental shift others notice; social or reputation consequence; narrowing opportunity window; "
                "or a named lead (NPC, faction, or place) the speaker can credibly cite."
            )
        return (
            f"{shared} The player has pressed this unresolved topic repeatedly without meaningful progress."
            f"{topic_hint}{prev_answer_hint} Repetition count: {repeat_count}. "
            f"{escalation_menu} "
            "Urgency sharpens salience; it does not justify narrating the PC's chosen route or forced pathing. "
            "Include exactly one scene momentum tag and end with concrete player-facing openings, stakes, or time "
            "pressure the player can respond to (do not narrate the PC's move or commitment)."
            f"{cs_supplement}"
        )

    if failure_class == "scene_stall":
        hostile_tail = (
            " If the tone contract allows, you may add a grounded confrontation beat that fits visible tension or authority roles."
            if allow_hostile
            else " Do not introduce threats, hostile interruption, violence, or weapons."
        )
        return (
            f"{shared} Scene stall / low progress: advance now with one concrete development—still without choosing for the player. "
            "Prefer new information plus a player-facing opening, or pressure plus a surfaced choice, or a consequence "
            "with visible next opportunities, or a bounded refusal with an alternative handle, or a clarified hard "
            "constraint that removes one avenue while leaving others open. "
            "Do not auto-travel, auto-commit, or collapse multiple leads into one mandatory path. "
            f"{hostile_tail} "
            "Include exactly one matching scene momentum tag in tags: scene_momentum:<kind>."
            f"{cs_supplement}"
        )

    if failure_class == "forbidden_generic_phrase":
        return (
            f"{shared} Rewrite only the offending generic phrase or sentence into scene-anchored specifics. "
            "Keep the rest of the reply intact where possible and avoid flattening the whole response."
            f"{cs_supplement}"
        )

    reason_text = f" Reasons: {reasons}." if reasons else ""
    return f"{shared} Rewrite narrowly to resolve this failure.{reason_text}{cs_supplement}"


def prioritize_retry_failures_for_social_answer_candidate(
    failures: List[Dict[str, Any]],
    *,
    player_text: str,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    world: Dict[str, Any] | None = None,
    segmented_turn: Dict[str, Any] | None = None,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """When a structured/reconciled/partial answer exists, drop stall/echo failures and inject an answer retry.

    Mutates ``resolution["social"]`` with debug fields when this is a social_exchange turn.
    """
    debug: Dict[str, Any] = {
        "strategy_forced_to_answer": False,
        "suppressed_fallback_strategies": [],
    }
    if not isinstance(resolution, dict):
        return list(failures or []), debug
    soc = resolution.get("social")
    if not isinstance(soc, dict):
        return list(failures or []), debug
    if str(soc.get("social_intent_class") or "").strip().lower() != "social_exchange":
        return list(failures or []), debug

    if not _social_answer_fallback_in_scope(
        player_text=str(player_text or ""),
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else {},
        session=session if isinstance(session, dict) else {},
        world=world if isinstance(world, dict) else {},
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
    ):
        debug["retry_social_answer_priority_skipped"] = "block1_world_action_signal"
        return list(failures or []), debug

    scene_id = _resolve_scene_id(scene_envelope)
    npc_id = str(soc.get("npc_id") or "").strip() or None
    best = select_best_social_answer_candidate(
        session=session,
        scene_id=scene_id,
        npc_id=npc_id,
        topic_key=None,
        player_text=str(player_text or ""),
        resolution=resolution,
    )
    kind = str(best.get("answer_kind") or "").strip()
    text = str(best.get("text") or "").strip()

    soc["strategy_forced_to_answer"] = False
    soc["suppressed_fallback_strategies"] = []

    def _merge_valid_followup_strategy_into_debug() -> None:
        sync_strategy_forced_to_answer_for_valid_followup_alignment(soc)
        if soc.get("strategy_forced_to_answer"):
            debug["strategy_forced_to_answer"] = True
        fr = soc.get("forced_answer_reason")
        if isinstance(fr, str) and fr.strip():
            debug["forced_answer_reason"] = fr.strip()

    if kind not in _SOCIAL_FORCE_ANSWER_CANDIDATE_KINDS or not text:
        _merge_valid_followup_strategy_into_debug()
        return list(failures or []), debug

    soc["social_answer_retry_candidate_kind"] = kind
    soc["social_answer_retry_anchor_text"] = text
    soc["social_answer_retry_candidate_source"] = str(best.get("source") or "")

    suppressed: List[str] = []
    filtered: List[Dict[str, Any]] = []
    for failure in failures or []:
        if not isinstance(failure, dict):
            continue
        fc = str(failure.get("failure_class") or "").strip()
        if fc in ("scene_stall", "echo_or_repetition"):
            if fc not in suppressed:
                suppressed.append(fc)
            continue
        filtered.append(failure)

    if not suppressed:
        _merge_valid_followup_strategy_into_debug()
        return list(failures or []), debug

    debug["strategy_forced_to_answer"] = True
    debug["suppressed_fallback_strategies"] = list(suppressed)
    soc["strategy_forced_to_answer"] = True
    soc["suppressed_fallback_strategies"] = list(suppressed)

    synthetic: Dict[str, Any] = {
        "failure_class": "answer",
        "priority": RETRY_FAILURE_PRIORITY["answer"],
        "reasons": [f"social_answer_candidate:{kind}"],
    }
    if _is_valid_player_facing_fallback_answer(
        text,
        player_text=str(player_text or ""),
        known_fact={
            "source": str(best.get("source") or "").strip(),
            "subject": "",
            "position": "",
        },
        failure_class="answer",
    ):
        synthetic["known_fact_context"] = {
            "answer": text,
            "source": str(best.get("source") or "").strip(),
            "subject": "",
            "position": "",
        }
    _merge_valid_followup_strategy_into_debug()
    return [synthetic] + filtered, debug


def choose_retry_strategy(failures: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """Pick the highest-priority retry target from inspectable failures."""
    ranked: List[Dict[str, Any]] = []
    for failure in failures or []:
        if not isinstance(failure, dict):
            continue
        failure_class = str(failure.get("failure_class") or "").strip()
        if not failure_class:
            continue
        ranked.append(
            {
                **failure,
                "failure_class": failure_class,
                "priority": int(failure.get("priority") or RETRY_FAILURE_PRIORITY.get(failure_class, 999)),
            }
        )
    if not ranked:
        return None
    ranked.sort(key=lambda item: (int(item.get("priority", 999)), str(item.get("failure_class") or "")))
    return ranked[0]


def scene_stall_check(
    *,
    gm_reply: Dict[str, Any],
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """Detect when scene momentum is due but the reply leaves the scene static."""
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return {"applies": False, "ok": True, "reasons": []}
    if not _scene_momentum_due(session, scene_id):
        return {"applies": False, "ok": True, "reasons": []}
    if _extract_scene_momentum_kind(gm_reply):
        return {"applies": True, "ok": True, "reasons": []}
    return {
        "applies": True,
        "ok": False,
        "reasons": ["scene_stall:momentum_due_without_progress"],
    }


def _strip_double_quoted_spans_for_generic_scan(text: str) -> str:
    """Remove ``"..."`` spans so forbidden-generic detection ignores in-character quoted stock lines."""
    if not isinstance(text, str):
        return ""
    return re.sub(r'"[^"]*"', " ", str(text))


def _strict_social_speaker_led_opening_for_retry(
    reply_text: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    """True when the opening is clearly NPC-attributed (strict-social retry relax, not narrator sludge)."""
    if not isinstance(resolution, dict):
        return False
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    first = _first_sentence(reply_text)
    if not first.strip():
        return False
    low = first.lower()
    if name and name.lower() in low[: min(len(name) + 96, 200)]:
        return True
    return _opening_sentence_should_skip_echo_check(first)


def inspect_retry_social_answer_fallback_scope(
    *,
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    segmented_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Block #3: scope for deterministic NPC/social-shaped retry fallbacks (Block #1 text signals)."""
    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    sess = session if isinstance(session, dict) else None
    w = world if isinstance(world, dict) else None
    block1_signal = False
    canonical_break = False
    if sess is not None and w is not None:
        block1_signal = world_action_turn_suppresses_npc_answer_fallback(
            session=sess,
            scene=env,
            world=w,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=str(player_text or ""),
        )
        canonical_break = evaluate_world_action_social_continuity_break(
            session=sess,
            scene=env,
            world=w,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=str(player_text or ""),
        )
    return {
        "retry_social_fallback_considered": True,
        "block1_world_action_signal": block1_signal,
        "block1_canonical_continuity_break": canonical_break,
        "social_shaped_fallback_in_scope": not block1_signal,
    }


def _social_answer_fallback_in_scope(
    *,
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    segmented_turn: Dict[str, Any] | None = None,
) -> bool:
    return bool(
        inspect_retry_social_answer_fallback_scope(
            player_text=player_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            segmented_turn=segmented_turn,
        ).get("social_shaped_fallback_in_scope")
    )


def _retry_known_fact_is_suppressed_social_shape(
    known_fact: Dict[str, Any],
    *,
    world_action_signal: bool,
) -> bool:
    """When Block #1 signals world-action, drop social/dialogue-shaped known facts from retry carry."""
    if not world_action_signal or not isinstance(known_fact, dict):
        return False
    src = str(known_fact.get("source") or "").strip()
    if src in {"social_answer_candidate", "recent_dialogue_continuity"}:
        return True
    sp = dict(known_fact.get("speaker") or {}) if isinstance(known_fact.get("speaker"), dict) else {}
    if str(sp.get("role") or "").strip().lower() == "npc":
        return True
    return False


def _append_retry_social_scope_debug(gm_or_out: Dict[str, Any], scope: Dict[str, Any]) -> None:
    if not isinstance(gm_or_out, dict) or not isinstance(scope, dict):
        return
    dbg = gm_or_out.get("debug_notes") if isinstance(gm_or_out.get("debug_notes"), str) else ""
    tail = (
        f"retry_social_fallback_scope:block1_signal={scope.get('block1_world_action_signal')}"
        f":canonical_continuity_break={scope.get('block1_canonical_continuity_break')}"
        f":social_shaped_in_scope={scope.get('social_shaped_fallback_in_scope')}"
    )
    gm_or_out["debug_notes"] = (dbg + " | " if dbg else "") + tail


def detect_retry_failures(
    *,
    player_text: str,
    gm_reply: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    segmented_turn: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Collect inspectable retry failures before deterministic enforcement."""
    if not isinstance(gm_reply, dict):
        return []
    reply_text = gm_reply.get("player_facing_text") if isinstance(gm_reply.get("player_facing_text"), str) else ""
    failures: List[Dict[str, Any]] = []
    scene_id = _resolve_scene_id(scene_envelope)
    strict_social = _gm_binding().strict_social_emission_will_apply(resolution, session, world, scene_id)

    validator_hits = detect_validator_voice(reply_text)
    if validator_hits:
        failures.append(
            {
                "failure_class": "validator_voice",
                "priority": RETRY_FAILURE_PRIORITY["validator_voice"],
                "reasons": validator_hits,
            }
        )

    question_rule = question_resolution_rule_check(
        player_text=player_text,
        gm_reply_text=reply_text,
        resolution=resolution,
    )
    if (
        strict_social
        and question_rule.get("applies")
        and not question_rule.get("ok")
        and _strict_social_speaker_led_opening_for_retry(reply_text, resolution)
    ):
        q_reasons = [str(r) for r in (question_rule.get("reasons") or [])]
        relax_ok = bool(q_reasons) and all(
            isinstance(r, str)
            and r.startswith("question_rule:")
            and "asked_question_before_answer" not in r
            and "empty_reply" not in r
            and "refusal_or_meta_disallowed" not in r
            for r in q_reasons
        )
        if relax_ok:
            question_rule = {"applies": True, "ok": True, "reasons": []}

    if question_rule.get("applies") and not question_rule.get("ok"):
        tags_r = gm_reply.get("tags") if isinstance(gm_reply.get("tags"), list) else []
        tag_list_q = [str(t) for t in tags_r if isinstance(t, str)]
        deterministic_known_retry = "question_retry_fallback" in tag_list_q and (
            "known_fact_guard" in tag_list_q
            or "social_answer_retry" in tag_list_q
        )
        if not deterministic_known_retry:
            block1_signal = world_action_turn_suppresses_npc_answer_fallback(
                session=session if isinstance(session, dict) else {},
                scene=scene_envelope if isinstance(scene_envelope, dict) else {},
                world=world if isinstance(world, dict) else {},
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                raw_text=str(player_text or ""),
            )
            known_fact = resolve_known_fact_before_uncertainty(
                player_text,
                scene_envelope=scene_envelope,
                session=session,
                world=world,
                resolution=resolution,
            )
            suppressed_kf_carry = False
            if isinstance(known_fact, dict) and _retry_known_fact_is_suppressed_social_shape(
                known_fact,
                world_action_signal=block1_signal,
            ):
                known_fact = None
                suppressed_kf_carry = block1_signal
            failure_payload = {
                "failure_class": "unresolved_question",
                "priority": RETRY_FAILURE_PRIORITY["unresolved_question"],
                "reasons": list(question_rule.get("reasons") or []),
            }
            if suppressed_kf_carry:
                failure_payload["retry_social_known_fact_carry_suppressed"] = "block1_world_action_signal"
            if known_fact:
                ktxt = str(known_fact.get("text") or "").strip()
                if ktxt and _is_valid_player_facing_fallback_answer(
                    ktxt,
                    player_text=player_text,
                    known_fact=known_fact if isinstance(known_fact, dict) else None,
                    failure_class="unresolved_question",
                ):
                    failure_payload["known_fact_context"] = {
                        "answer": ktxt,
                        "source": str(known_fact.get("source") or "").strip(),
                        "subject": str(known_fact.get("subject") or "").strip(),
                        "position": str(known_fact.get("position") or "").strip(),
                    }
            if "known_fact_context" not in failure_payload:
                uncertainty_hint = classify_uncertainty(
                    player_text,
                    scene_envelope=scene_envelope,
                    session=session,
                    world=world,
                    resolution=resolution,
                )
                failure_payload["uncertainty_category"] = str(uncertainty_hint.get("category") or "").strip()
                failure_payload["uncertainty_context"] = {
                    "speaker": dict(uncertainty_hint.get("speaker") or {}),
                    "scene_snapshot": dict(uncertainty_hint.get("scene_snapshot") or {}),
                }
            failures.append(failure_payload)

    echo_reasons: List[str] = []
    if opening_sentence_echoes_player_input(reply_text, player_text):
        if not (strict_social and _strict_social_speaker_led_opening_for_retry(reply_text, resolution)):
            echo_reasons.append("echo_or_repetition:opening_overlap")
    if opening_sentence_overlaps_player_quote(reply_text, player_text):
        echo_reasons.append("echo_or_repetition:quoted_speech_overlap")
    echo_reasons.extend(detect_stock_warning_filler_repetition(reply_text))
    if echo_reasons:
        failures.append(
            {
                "failure_class": "echo_or_repetition",
                "priority": RETRY_FAILURE_PRIORITY["echo_or_repetition"],
                "reasons": echo_reasons,
            }
        )

    npc_contract = npc_response_contract_check(
        player_text=player_text,
        npc_reply_text=reply_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    if npc_contract.get("applies") and not npc_contract.get("ok"):
        failures.append(
            {
                "failure_class": "npc_contract_failure",
                "priority": RETRY_FAILURE_PRIORITY["npc_contract_failure"],
                "reasons": list(npc_contract.get("reasons") or []),
                "missing": list(npc_contract.get("missing") or []),
            }
        )

    topic_pressure = _topic_pressure_snapshot_for_reply(
        session=session,
        scene_envelope=scene_envelope,
        reply_text=reply_text,
    )
    if topic_pressure.get("applies") and not topic_pressure.get("ok"):
        failures.append(
            {
                "failure_class": "topic_pressure_escalation",
                "priority": RETRY_FAILURE_PRIORITY["topic_pressure_escalation"],
                "reasons": list(topic_pressure.get("reasons") or []),
                "topic_context": (
                    topic_pressure.get("topic_context")
                    if isinstance(topic_pressure.get("topic_context"), dict)
                    else {}
                ),
            }
        )

    followup_rep = followup_soft_repetition_check(player_text=player_text, reply_text=reply_text, session=session)
    if followup_rep.get("applies") and not followup_rep.get("ok"):
        failures.append(
            {
                "failure_class": "followup_soft_repetition",
                "priority": RETRY_FAILURE_PRIORITY["followup_soft_repetition"],
                "reasons": list(followup_rep.get("reasons") or []),
                "followup_context": (
                    followup_rep.get("followup_context")
                    if isinstance(followup_rep.get("followup_context"), dict)
                    else {}
                ),
            }
        )

    scene_stall = scene_stall_check(gm_reply=gm_reply, session=session, scene_envelope=scene_envelope)
    if scene_stall.get("applies") and not scene_stall.get("ok"):
        failures.append(
            {
                "failure_class": "scene_stall",
                "priority": RETRY_FAILURE_PRIORITY["scene_stall"],
                "reasons": list(scene_stall.get("reasons") or []),
            }
        )

    forbidden_generic_hits = detect_forbidden_generic_phrases(reply_text)
    if strict_social:
        forbidden_generic_hits = detect_forbidden_generic_phrases(
            _strip_double_quoted_spans_for_generic_scan(reply_text)
        )
        if forbidden_generic_hits and _strict_social_speaker_led_opening_for_retry(reply_text, resolution):
            forbidden_generic_hits = []
    if forbidden_generic_hits:
        failures.append(
            {
                "failure_class": "forbidden_generic_phrase",
                "priority": RETRY_FAILURE_PRIORITY["forbidden_generic_phrase"],
                "reasons": forbidden_generic_hits,
            }
        )

    return failures


def apply_deterministic_retry_fallback(
    gm: Dict[str, Any],
    *,
    failure: Dict[str, Any],
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    segmented_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Apply deterministic fallback when targeted retry still fails."""
    if not isinstance(gm, dict):
        return gm
    failure_class = str((failure or {}).get("failure_class") or "").strip()
    if failure_class not in ("unresolved_question", "answer"):
        return gm

    snap_pre_det = snapshot_turn_stage(gm, "retry_pre_deterministic_fallback")
    record_stage_snapshot(gm, "retry_pre_deterministic_fallback", snapshot=snap_pre_det)

    def _emit_deterministic_retry_result(out_obj: Dict[str, Any]) -> None:
        snap_post = snapshot_turn_stage(out_obj, "retry_deterministic_fallback_applied", failure_class=failure_class)
        record_stage_snapshot(out_obj, "retry_deterministic_fallback_applied", snapshot=snap_post)
        record_stage_transition(
            out_obj,
            "retry_pre_deterministic_fallback",
            "retry_deterministic_fallback_applied",
            snap_pre_det,
            snap_post,
        )

    scene_id = str((scene_envelope.get("scene") or {}).get("id") or "").strip()
    eff_res, strict_route, _ = _gm_binding().effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        scene_id,
    )
    scope = inspect_retry_social_answer_fallback_scope(
        player_text=str(player_text or ""),
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else {},
        session=session if isinstance(session, dict) else {},
        world=world if isinstance(world, dict) else {},
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
    )
    soc_in_scope = bool(scope.get("social_shaped_fallback_in_scope"))
    block1_signal = bool(scope.get("block1_world_action_signal"))

    def _tag_retry_scope(out_d: Dict[str, Any]) -> Dict[str, Any]:
        _append_retry_social_scope_debug(out_d, scope)
        return out_d

    known_fact_ctx = (failure or {}).get("known_fact_context") if isinstance((failure or {}).get("known_fact_context"), dict) else {}
    ans_ctx = str(known_fact_ctx.get("answer") or "").strip()
    if failure_class == "answer" and ans_ctx and soc_in_scope:
        kf_for_val: Dict[str, Any] = {
            "source": str(known_fact_ctx.get("source") or ""),
            "subject": str(known_fact_ctx.get("subject") or ""),
            "position": str(known_fact_ctx.get("position") or ""),
        }
        if _is_valid_player_facing_fallback_answer(
            ans_ctx,
            player_text=player_text,
            known_fact=kf_for_val,
            failure_class="answer",
        ):
            out = dict(gm)
            out["player_facing_text"] = _ensure_terminal_punctuation(ans_ctx)
            tags = out.get("tags") if isinstance(out.get("tags"), list) else []
            out["tags"] = list(tags) + ["question_retry_fallback", "known_fact_guard", "social_answer_retry"]
            dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
            source = str(known_fact_ctx.get("source") or "social_answer_candidate").strip()
            out["debug_notes"] = (
                (dbg + " | " if dbg else "")
                + f"retry_fallback:answer:known_fact_guard:{source}"
            )
            _emit_deterministic_retry_result(out)
            return _tag_retry_scope(out)

    known_fact = resolve_known_fact_before_uncertainty(
        player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    if isinstance(known_fact, dict) and _retry_known_fact_is_suppressed_social_shape(
        known_fact,
        world_action_signal=block1_signal,
    ):
        known_fact = None
    out = dict(gm)
    ktxt = str((known_fact or {}).get("text") or "").strip() if isinstance(known_fact, dict) else ""
    if isinstance(known_fact, dict) and ktxt:
        src_nf = str(known_fact.get("source") or "").strip()
        vfc = "answer" if src_nf == "social_answer_candidate" else "unresolved_question"
        if _is_valid_player_facing_fallback_answer(
            ktxt,
            player_text=player_text,
            known_fact=known_fact,
            failure_class=vfc,
        ):
            sp = dict(known_fact.get("speaker") or {}) if isinstance(known_fact.get("speaker"), dict) else {}
            role = str(sp.get("role") or "").strip().lower()
            narrator_kf = role in {"", "narrator"}
            soc_chk: Dict[str, Any] = {}
            if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict):
                soc_chk = resolution.get("social") or {}
            open_social_solicit = bool(soc_chk.get("open_social_solicitation"))
            block1_out = not soc_in_scope
            allow_kf = False
            if block1_out:
                allow_kf = not _retry_known_fact_is_suppressed_social_shape(
                    known_fact,
                    world_action_signal=True,
                )
            else:
                allow_kf = (not (strict_route and narrator_kf)) or open_social_solicit
            if allow_kf:
                out["player_facing_text"] = _ensure_terminal_punctuation(ktxt)
                tags = out.get("tags") if isinstance(out.get("tags"), list) else []
                out["tags"] = list(tags) + ["question_retry_fallback", "known_fact_guard"]
                dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
                source = str(known_fact.get("source") or "known_fact").strip()
                won = "narrator_kf_won_before_strict_social" if block1_out and narrator_kf else "known_fact_guard"
                out["debug_notes"] = (
                    (dbg + " | " if dbg else "")
                    + f"retry_fallback:unresolved_question:known_fact_guard:{source}|retry_fallback:{won}"
                )
                _emit_deterministic_retry_result(out)
                return _tag_retry_scope(out)

    res_open = resolution if isinstance(resolution, dict) else None
    soc_open = (
        res_open.get("social")
        if isinstance(res_open, dict) and isinstance(res_open.get("social"), dict)
        else {}
    )
    if isinstance(soc_open, dict) and soc_open.get("open_social_solicitation"):
        from game.social_exchange_emission import (
            build_open_social_solicitation_recovery,
            _merge_open_social_recovery_emission_debug,
        )

        rec_fb = build_open_social_solicitation_recovery(
            resolution=res_open,
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=scene_id,
            scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
            player_text=player_text,
        )
        if rec_fb.get("used") and isinstance(rec_fb.get("text"), str) and str(rec_fb.get("text") or "").strip():
            out = dict(gm)
            out["player_facing_text"] = _ensure_terminal_punctuation(str(rec_fb.get("text") or "").strip())
            tags = out.get("tags") if isinstance(out.get("tags"), list) else []
            tag_list = [str(t) for t in tags if isinstance(t, str)]
            out["tags"] = tag_list + [
                "question_retry_fallback",
                "open_social_solicitation_recovery",
                "open_social_recovery",
            ]
            dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
            out["debug_notes"] = (
                (dbg + " | " if dbg else "")
                + f"retry_fallback:open_social_recovery:{rec_fb.get('mode')}|retry_fallback:suppressed:uncertainty_pool"
            )
            _merge_open_social_recovery_emission_debug(out, rec_fb)
            _emit_deterministic_retry_result(out)
            return _tag_retry_scope(out)
    if strict_route and isinstance(eff_res, dict) and soc_in_scope:
        inner = _gm_binding().apply_social_exchange_retry_fallback_gm(
            out,
            player_text=player_text,
            session=session,
            world=world,
            resolution=eff_res,
            scene_id=scene_id,
        )
        _emit_deterministic_retry_result(inner)
        return _tag_retry_scope(inner)

    uncertainty = classify_uncertainty(
        player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    out = _apply_uncertainty_to_gm(
        out,
        uncertainty=uncertainty,
        reason="retry_fallback:unresolved_question",
        replace_text=True,
        player_text=player_text,
    )
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = list(tags) + ["question_retry_fallback"]
    dbg_u = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    if not soc_in_scope:
        out["debug_notes"] = (
            (dbg_u + " | " if dbg_u else "")
            + "retry_fallback_chosen:nonsocial_uncertainty_pool_after_block1_social_out_of_scope"
        )
    _emit_deterministic_retry_result(out)
    return _tag_retry_scope(out)


def _stable_u32_from_seed(seed: str) -> int:
    acc = 2166136261
    for ch in str(seed or ""):
        acc = (acc ^ ord(ch)) * 16777619
        acc &= 0xFFFFFFFF
    return int(acc)


def _nonsocial_forced_retry_progress_line(
    player_text: str,
    *,
    scene_envelope: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
) -> str:
    """Short narrator fallback after retries: answer-shape first when possible; diegetic scene anchors only."""
    pt = str(player_text or "").strip()
    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    sess = session if isinstance(session, dict) else {}
    w = world if isinstance(world, dict) else {}
    res = resolution if isinstance(resolution, dict) else None
    sid = _resolve_scene_id(env)
    seed = f"{sid}|{pt[:200]}"

    res_kind = str((res or {}).get("kind") or "").strip().lower()
    suppress_intro = anti_reset_suppresses_intro_style_fallbacks(
        sess if isinstance(sess, dict) else None,
        env,
        w,
        sid,
        res,
    )
    if res_kind in _PERCEPTION_FALLBACK_RESOLUTION_KINDS and not suppress_intro:
        obs_line = render_observe_perception_fallback_line(
            env, seed_key=seed, player_text=pt, resolution=res
        )
        if isinstance(obs_line, str) and obs_line.strip():
            return _ensure_terminal_punctuation(obs_line.strip())

    if _resolution_implies_destination_arrival(res):
        arr_line = render_travel_arrival_fallback_line(env, seed_key=seed)
        if isinstance(arr_line, str) and arr_line.strip():
            return _ensure_terminal_punctuation(arr_line.strip())

    if _is_direct_player_question(pt):
        known_fact = resolve_known_fact_before_uncertainty(
            pt,
            scene_envelope=env,
            session=sess,
            world=w,
            resolution=resolution,
        )
        ktxt = str(known_fact.get("text") or "").strip() if isinstance(known_fact, dict) else ""
        if ktxt and _is_valid_player_facing_fallback_answer(
            ktxt,
            player_text=pt,
            known_fact=known_fact if isinstance(known_fact, dict) else None,
            failure_class="unresolved_question",
        ):
            return _ensure_terminal_punctuation(ktxt)
        uncertainty = classify_uncertainty(
            pt,
            scene_envelope=env,
            session=sess,
            world=w,
            resolution=resolution,
        )
        line = render_uncertainty_response(uncertainty)
        if isinstance(line, str) and line.strip():
            return _ensure_terminal_punctuation(line.strip())

    anchor = render_nonsocial_terminal_anchor_line(env, seed_key=seed, player_text=pt)
    if isinstance(anchor, str) and anchor.strip():
        line_out = anchor.strip()
        if suppress_intro and (
            text_matches_observe_opener_templates(line_out)
            or text_overlaps_known_scene_intro_sources(line_out, env)
        ):
            line_out = local_exchange_continuation_fallback_line(
                session=sess if isinstance(sess, dict) else None,
                world=w,
                scene_id=sid,
                resolution=res,
            )
        return _ensure_terminal_punctuation(line_out)

    return _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())


_SOCIAL_EMPTY_REPAIR_HARD_LINE = "They answer cautiously, keeping it brief."

_NONSOCIAL_EMPTY_REPAIR_HARD_LINE = "Something shifts in the scene, drawing your attention forward."

_NON_SOCIAL_TERMINAL_FINAL_ROUTES: frozenset[str] = frozenset({"forced_retry_fallback"})

_SOCIAL_EXCLUSIVE_FINAL_ROUTES_FOR_NONSOCIAL_REPAIR: frozenset[str] = frozenset({"social_fallback_minimal"})

_PLACEHOLDER_LITERAL_PLAYER_TEXT: frozenset[str] = frozenset(
    {"{}", "[]", "()", "null", "none", "n/a", "na", "...", "…", "tbd", "todo"}
)


def _is_placeholder_only_player_facing_text(t: str) -> bool:
    s = str(t or "").strip()
    if not s:
        return True
    low = s.lower()
    if low in _PLACEHOLDER_LITERAL_PLAYER_TEXT or s in _PLACEHOLDER_LITERAL_PLAYER_TEXT:
        return True
    if re.fullmatch(r"[\s.…]{1,40}", s):
        return True
    if re.fullmatch(r"[\W_]+", s, flags=re.UNICODE):
        return True
    return False


def _gm_has_usable_player_facing_text(gm: Dict[str, Any] | None) -> bool:
    """True when gm carries non-empty, route-legal player-facing narration text."""
    if not isinstance(gm, dict):
        return False
    t = gm.get("player_facing_text")
    if not isinstance(t, str) or not t.strip():
        return False
    if _gm_binding().is_route_illegal_global_or_sanitizer_fallback_text(t):
        return False
    if _is_placeholder_only_player_facing_text(t):
        return False
    return True


_WEAK_REPAIR_STALL_PHRASES: frozenset[str] = frozenset({
    "something shifts",
    "they answer cautiously",
    "after a pause",
    "for a moment",
})


def _repair_prose_has_weak_stall_wording(text: str) -> bool:
    low = str(text or "").lower()
    return any(p in low for p in _WEAK_REPAIR_STALL_PHRASES)


def _player_facing_text_same_line(a: str, b: str) -> bool:
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", str(s or "").strip().lower().rstrip(".!?"))

    return _norm(a) == _norm(b)


def _minimal_repair_context(
    *,
    gm: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Gather only safe, already-established context for repair phrasing.
    No new facts. No inference beyond what is already in session/gm/scene.
    """
    sess = session if isinstance(session, dict) else {}
    gm_d = gm if isinstance(gm, dict) else {}
    sid = str(sess.get("active_scene_id") or "").strip()
    env: Dict[str, Any] = {}
    if sid:
        try:
            env = load_scene(sid)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            env = {}
    if not isinstance(env, dict):
        env = {}
    visible = _scene_visible_facts(env)
    raw_first = visible[0] if visible else ""
    first_visible = _clean_scene_detail(raw_first) if raw_first else ""

    meta = gm_d.get("_final_emission_meta") if isinstance(gm_d.get("_final_emission_meta"), dict) else {}
    ic = inspect_interaction_context(sess) if sess else {}
    interlocutor_raw = str(
        meta.get("active_interlocutor_id")
        or meta.get("npc_id")
        or ic.get("active_interaction_target_id")
        or ""
    ).strip()
    interlocutor_id = canonical_interaction_target_npc_id(sess, interlocutor_raw) if interlocutor_raw else ""

    last_text = str(sess.get("player_input") or "").strip()
    topic_pressure_current: Dict[str, Any] = {}
    if sid:
        rt = get_scene_runtime(sess, sid)
        if isinstance(rt, dict):
            if not last_text:
                last_text = str(rt.get("last_player_action_text") or "").strip()
            tpc = rt.get("topic_pressure_current")
            if isinstance(tpc, dict):
                topic_pressure_current = tpc
                if not last_text:
                    last_text = str(tpc.get("player_text") or "").strip()

    direct_question = _is_direct_player_question(last_text)
    social_authority = _session_social_authority(sess)
    strict_social_active = bool(meta.get("strict_social_active")) if meta else False

    intent_labels: List[str] = []
    last_intent_class = "general"
    if last_text:
        intent_info = classify_player_intent(last_text)
        if isinstance(intent_info, dict):
            raw_lbl = intent_info.get("labels") or []
            intent_labels = [str(x) for x in raw_lbl if isinstance(x, str)]
            last_intent_class = str(intent_labels[0]).strip().lower() if intent_labels else "general"

    canonical_speaker = str(topic_pressure_current.get("npc_name") or "").strip()
    w = world if isinstance(world, dict) else None
    if interlocutor_id and w is not None:
        from game.world import get_world_npc_by_id

        wrow = get_world_npc_by_id(w, interlocutor_id)
        if isinstance(wrow, dict):
            wn = str(wrow.get("name") or "").strip()
            if wn:
                canonical_speaker = wn

    return {
        "active_scene_id": sid,
        "first_visible_fact_detail": first_visible,
        "active_interlocutor_id": interlocutor_id,
        "direct_question": direct_question,
        "session_social_authority": social_authority,
        "strict_social_active": strict_social_active,
        "last_player_text": last_text[:260],
        "intent_labels": intent_labels,
        "last_intent_class": last_intent_class,
        "canonical_speaker_label": canonical_speaker,
    }


def _contextual_social_repair_line(
    *,
    gm: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None = None,
) -> Tuple[str, str]:
    ctx = _minimal_repair_context(gm=gm, session=session, world=world)
    interlocutor = str(ctx.get("active_interlocutor_id") or "").strip()
    dq = bool(ctx.get("direct_question"))
    detail = str(ctx.get("first_visible_fact_detail") or "").strip()
    speaker = str(ctx.get("canonical_speaker_label") or "").strip()
    sid = str(ctx.get("active_scene_id") or "").strip()

    def pick(seed: str, options: Tuple[str, ...]) -> str:
        if not options:
            return ""
        idx = _stable_u32_from_seed(seed) % len(options)
        return options[idx]

    if dq and interlocutor:
        seed = f"soc_ctx|q|{interlocutor}|{speaker}|{detail[:40]}|{sid}"
        if speaker:
            opts: Tuple[str, ...] = (
                f"{speaker} answers with visible caution.",
                f"{speaker} offers a tight, careful reply.",
            )
        else:
            opts = (
                "The reply comes back clipped and immediate.",
                "The answer arrives low and controlled.",
            )
        cand = pick(seed, opts)
        line = _ensure_terminal_punctuation(str(cand).strip())
        if _gm_has_usable_player_facing_text({"player_facing_text": line}) and not _repair_prose_has_weak_stall_wording(line):
            return line, "question_ack"

    if detail:
        seed = f"soc_ctx|scene|{sid}|{detail[:80]}"
        lead = detail[0].upper() + (detail[1:] if len(detail) > 1 else "")
        opts2: Tuple[str, ...] = (
            f"{lead} still frames what you hear—the reply stays careful and brief.",
            f"You still mark {lead.lower()} while the answer lands, short and measured.",
        )
        cand2 = pick(seed, opts2)
        line2 = _ensure_terminal_punctuation(str(cand2).strip())
        if _gm_has_usable_player_facing_text({"player_facing_text": line2}) and not _repair_prose_has_weak_stall_wording(line2):
            return line2, "scene_anchor"

    hl = _ensure_terminal_punctuation(str(_SOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
    return hl, "hard_fallback"


def _contextual_nonsocial_repair_line(
    *,
    gm: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Tuple[str, str]:
    ctx = _minimal_repair_context(gm=gm, session=session, world=None)
    detail = str(ctx.get("first_visible_fact_detail") or "").strip()
    labels_raw = ctx.get("intent_labels") or []
    labels = [str(x).lower() for x in labels_raw if isinstance(x, str)]
    label_set = frozenset(labels)
    last_text = str(ctx.get("last_player_text") or "").strip()
    sid = str(ctx.get("active_scene_id") or "").strip()

    pressure_labels = frozenset({"combat", "travel", "investigation", "social_probe"})
    has_pressure = bool(pressure_labels.intersection(label_set))

    def pick(seed: str, options: Tuple[str, ...]) -> str:
        idx = _stable_u32_from_seed(seed) % len(options)
        return options[idx]

    if detail:
        seed = f"ns_ctx|sc|{sid}|{detail[:80]}"
        lead = detail[0].upper() + (detail[1:] if len(detail) > 1 else "")
        opts: Tuple[str, ...] = (
            f"{lead} catches your eye again as the moment turns toward what happens next.",
            f"{lead} still frames the room while pressure keeps moving through the crowd.",
        )
        cand = pick(seed, opts)
        line = _ensure_terminal_punctuation(str(cand).strip())
        if _gm_has_usable_player_facing_text({"player_facing_text": line}) and not _repair_prose_has_weak_stall_wording(line):
            return line, "scene_anchor"

    if has_pressure and last_text:
        seed = f"ns_ctx|pr|{last_text[:120]}|{sid}"
        opts2: Tuple[str, ...] = (
            "The moment sharpens, demanding an answer.",
            "The scene presses forward before the pause can settle.",
        )
        cand2 = pick(seed, opts2)
        line2 = _ensure_terminal_punctuation(str(cand2).strip())
        if _gm_has_usable_player_facing_text({"player_facing_text": line2}) and not _repair_prose_has_weak_stall_wording(line2):
            return line2, "pressure_forward"

    hl = _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
    return hl, "hard_fallback"


_FINAL_EMISSION_META_CONTINUITY_KEYS: frozenset[str] = frozenset({
    "active_interlocutor_id",
    "npc_id",
    "reply_kind",
    "strict_social_active",
    "coercion_used",
    "coercion_reason",
})


def _is_social_continuity_slot_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, dict) and len(value) == 0:
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def _preserve_social_continuity_fields(
    dst: Dict[str, Any],
    sources: List[Dict[str, Any] | None],
    session: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    *,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> None:
    """Copy only speaker/interlocutor/lane fields into *dst* without reintroducing rejected prose or clue junk.

    Sources are scanned in order; first non-empty continuity value wins. Session/resolution fill any
    remaining gaps for authoritative ids (aligned with :func:`effective_strict_social_resolution_for_emission`).
    """
    if not isinstance(dst, dict):
        return
    lane_social = _session_social_authority(session) or _gm_binding().strict_social_emission_will_apply(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    if not lane_social:
        return

    preserved: List[str] = []
    merged: Dict[str, Any] = {}
    cur = dst.get("_final_emission_meta")
    if isinstance(cur, dict):
        merged = dict(cur)

    for src in sources:
        if not isinstance(src, dict):
            continue
        sm = src.get("_final_emission_meta")
        if not isinstance(sm, dict):
            continue
        for key in _FINAL_EMISSION_META_CONTINUITY_KEYS:
            if key not in sm:
                continue
            val = sm[key]
            if _is_social_continuity_slot_empty(val):
                continue
            if not _is_social_continuity_slot_empty(merged.get(key)):
                continue
            merged[key] = val
            preserved.append(f"_final_emission_meta.{key}")

    eff_res, strict_route, coercion_reason = _gm_binding().effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    soc = (
        eff_res.get("social")
        if isinstance(eff_res, dict) and isinstance(eff_res.get("social"), dict)
        else {}
    )
    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    active_ic = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    soc_nid = str(soc.get("npc_id") or "").strip()
    sess = session if isinstance(session, dict) else None
    npc_res_raw = soc_nid or active_ic
    npc_res = canonical_interaction_target_npc_id(sess, npc_res_raw) if npc_res_raw else ""
    interlocutor_raw = active_ic or soc_nid
    interlocutor_canon = canonical_interaction_target_npc_id(sess, interlocutor_raw) if interlocutor_raw else ""
    reply_kind = str(soc.get("reply_kind") or "").strip()

    cr = str(coercion_reason or "").strip()
    coercion_used = "|" in cr or "synthetic" in cr or "npc_directed_guard" in cr

    if _is_social_continuity_slot_empty(merged.get("active_interlocutor_id")) and interlocutor_canon:
        merged["active_interlocutor_id"] = interlocutor_canon
        preserved.append("_final_emission_meta.active_interlocutor_id")
    if _is_social_continuity_slot_empty(merged.get("npc_id")) and npc_res:
        merged["npc_id"] = npc_res
        preserved.append("_final_emission_meta.npc_id")
    if _is_social_continuity_slot_empty(merged.get("reply_kind")) and reply_kind:
        merged["reply_kind"] = reply_kind
        preserved.append("_final_emission_meta.reply_kind")
    if _is_social_continuity_slot_empty(merged.get("strict_social_active")):
        ss = strict_route or _gm_binding().strict_social_emission_will_apply(
            resolution if isinstance(resolution, dict) else None,
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            str(scene_id or "").strip(),
        )
        merged["strict_social_active"] = bool(ss)
        preserved.append("_final_emission_meta.strict_social_active")
    if _is_social_continuity_slot_empty(merged.get("coercion_reason")) and cr:
        merged["coercion_reason"] = cr
        preserved.append("_final_emission_meta.coercion_reason")
    if _is_social_continuity_slot_empty(merged.get("coercion_used")):
        merged["coercion_used"] = coercion_used
        preserved.append("_final_emission_meta.coercion_used")

    if merged:
        dst["_final_emission_meta"] = merged
    if preserved:
        dst["preserved_social_continuity_fields"] = preserved


def ensure_minimal_social_resolution(
    *,
    gm: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    reason: str = "",
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
    scene_envelope: Dict[str, Any] | None = None,
    player_text: str = "",
    segmented_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Return a minimally valid social-resolution-shaped GM payload.
    Used when a social retry/fallback path produced empty or structurally insufficient output.
    """
    out: Dict[str, Any] = copy.deepcopy(gm) if isinstance(gm, dict) else {}
    sess = session if isinstance(session, dict) else None
    w = world if isinstance(world, dict) else None
    res_in = resolution if isinstance(resolution, dict) else None
    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    scene_id = _resolve_scene_id(env)

    eff_res, _strict_route, _ = _gm_binding().effective_strict_social_resolution_for_emission(
        res_in,
        sess,
        w,
        scene_id,
    )
    res_for_line = eff_res if isinstance(eff_res, dict) else res_in

    src_for_preserve = gm if isinstance(gm, dict) else None
    _preserve_social_continuity_fields(
        out,
        [src_for_preserve, out],
        sess,
        res_in,
        world=w,
        scene_id=scene_id,
    )

    pt_min = str(player_text or "").strip()
    if not pt_min and isinstance(sess, dict):
        pt_min = str(sess.get("player_input") or "").strip()
    block1_terminal_social = bool(
        isinstance(env, dict)
        and isinstance(sess, dict)
        and isinstance(w, dict)
        and world_action_turn_suppresses_npc_answer_fallback(
            session=sess,
            scene=env,
            world=w,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            raw_text=pt_min,
        )
    )

    ctx_mode_social = ""
    if not _gm_has_usable_player_facing_text(out):
        line = ""
        if block1_terminal_social:
            line = _nonsocial_forced_retry_progress_line(
                pt_min,
                scene_envelope=env,
                session=sess,
                world=w,
                resolution=res_in,
            )
            ctx_mode_social = "nonsocial_progress_after_block1_signal"
        if not str(line or "").strip():
            line = _gm_binding().minimal_social_emergency_fallback_line(
                res_for_line if isinstance(res_for_line, dict) else None
            )
        if (
            not isinstance(line, str)
            or not line.strip()
            or _gm_binding().is_route_illegal_global_or_sanitizer_fallback_text(line)
            or _is_placeholder_only_player_facing_text(line)
        ):
            if block1_terminal_social:
                c_line, ctx_mode_social = _contextual_nonsocial_repair_line(gm=out, session=sess)
            else:
                c_line, ctx_mode_social = _contextual_social_repair_line(gm=out, session=sess, world=w)
            if _gm_has_usable_player_facing_text({"player_facing_text": c_line}):
                line = c_line
            else:
                line = (
                    _NONSOCIAL_EMPTY_REPAIR_HARD_LINE if block1_terminal_social else _SOCIAL_EMPTY_REPAIR_HARD_LINE
                )
                ctx_mode_social = "hard_fallback"
        out["player_facing_text"] = _ensure_terminal_punctuation(str(line).strip())

    if not _gm_has_usable_player_facing_text(out):
        out["player_facing_text"] = _ensure_terminal_punctuation(_SOCIAL_EMPTY_REPAIR_HARD_LINE.strip())
        ctx_mode_social = "hard_fallback"

    if not block1_terminal_social and isinstance(res_for_line, dict) and _gm_has_usable_player_facing_text(out):
        pft_soc = str(out.get("player_facing_text") or "")
        repaired_soc, did_soc = _gm_binding().repair_strict_social_terminal_dialogue_fallback_if_needed(
            pft_soc,
            resolution=res_for_line,
            base_gm=out,
            session=sess,
            world=w,
            scene_id=scene_id,
            retry_terminal=True,
        )
        if did_soc:
            out["player_facing_text"] = _ensure_terminal_punctuation(repaired_soc.strip())
            if ctx_mode_social and ctx_mode_social != "hard_fallback":
                ctx_mode_social = f"{ctx_mode_social}|strict_social_dialogue_terminal_repair"
            elif not ctx_mode_social:
                ctx_mode_social = "strict_social_dialogue_terminal_repair"

    existing_route = str(out.get("final_route") or "").strip()
    if existing_route and existing_route not in _NON_SOCIAL_TERMINAL_FINAL_ROUTES:
        out["final_route"] = existing_route
    else:
        out["final_route"] = "social_fallback_minimal"
    out["fallback_kind"] = "social_empty_resolution_repair"
    out["accepted_via"] = "social_resolution_repair"
    out["targeted_retry_terminal"] = True
    out["retry_exhausted"] = True

    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    for extra in ("social_empty_resolution_repair", "retry_exhausted"):
        if extra not in tag_list:
            tag_list.append(extra)
    out["tags"] = tag_list

    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    repair_note = "social_empty_resolution_repair:terminal social resolution repair"
    suffix = f"{repair_note}|{reason}" if reason else repair_note
    if ctx_mode_social:
        suffix = f"{suffix}|social_contextual_repair:{ctx_mode_social}"
    if block1_terminal_social:
        suffix = f"{suffix}|retry_social_minimal_repair:block1_world_action_signal"
    out["debug_notes"] = (dbg + " | " if dbg else "") + suffix
    return out


def _nonsocial_minimal_resolution_line(*, session: Dict[str, Any] | None) -> str:
    """Conservative forward beat for empty non-social GM text; may anchor to on-disk scene visible_facts only."""
    sess = session if isinstance(session, dict) else None
    if not sess:
        return _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
    sid = str(sess.get("active_scene_id") or "").strip()
    if not sid:
        return _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
    try:
        env = load_scene(sid)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        env = {}
    if not isinstance(env, dict):
        env = {}
    visible = _scene_visible_facts(env)
    if visible:
        detail = _clean_scene_detail(visible[0])
        if detail:
            lead = detail[0].upper() + (detail[1:] if len(detail) > 1 else "")
            return _ensure_terminal_punctuation(
                f"{lead} still frames what you can see; the moment invites your next move."
            )
    seed = f"{sid}|nonsocial_empty_resolution_repair"
    idx = _stable_u32_from_seed(seed) % 2
    alts = (
        str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip(),
        "The air settles into a clear beat—time to commit to your next step.",
    )
    return _ensure_terminal_punctuation(alts[idx])


def ensure_minimal_nonsocial_resolution(
    *,
    gm: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """
    Return a minimally valid non-social GM payload when narration is empty or structurally unusable.
    Does not invent NPCs or clues; may reference visible_facts from the active scene template only.
    """
    out: Dict[str, Any] = copy.deepcopy(gm) if isinstance(gm, dict) else {}
    hard_line = _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
    ctx_mode_ns = ""
    if not _gm_has_usable_player_facing_text(out):
        line = _gm_binding()._nonsocial_minimal_resolution_line(session=session)
        bad = (
            not isinstance(line, str)
            or not line.strip()
            or _gm_binding().is_route_illegal_global_or_sanitizer_fallback_text(line)
            or _is_placeholder_only_player_facing_text(line)
        )
        need_ctx = bad or _player_facing_text_same_line(line, hard_line)
        if need_ctx:
            c_line, ctx_mode_ns = _contextual_nonsocial_repair_line(gm=out, session=session)
            if _gm_has_usable_player_facing_text({"player_facing_text": c_line}):
                line = c_line
            else:
                line = hard_line
                ctx_mode_ns = "hard_fallback"
        out["player_facing_text"] = line
    if not _gm_has_usable_player_facing_text(out):
        out["player_facing_text"] = hard_line
        ctx_mode_ns = "hard_fallback"

    existing_route = str(out.get("final_route") or "").strip()
    if existing_route and existing_route not in _SOCIAL_EXCLUSIVE_FINAL_ROUTES_FOR_NONSOCIAL_REPAIR:
        out["final_route"] = existing_route
    else:
        out["final_route"] = "nonsocial_fallback_minimal"
    out["fallback_kind"] = "nonsocial_empty_resolution_repair"
    out["accepted_via"] = "nonsocial_resolution_repair"
    out["targeted_retry_terminal"] = True
    out["retry_exhausted"] = True

    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    for extra in ("nonsocial_empty_resolution_repair", "retry_exhausted"):
        if extra not in tag_list:
            tag_list.append(extra)
    out["tags"] = tag_list

    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    repair_note = "nonsocial_empty_resolution_repair:terminal non-social resolution repair"
    dbg_suffix = repair_note
    if ctx_mode_ns:
        dbg_suffix = f"{repair_note}|nonsocial_contextual_repair:{ctx_mode_ns}"
    out["debug_notes"] = (dbg + " | " if dbg else "") + dbg_suffix
    return out


def force_terminal_retry_fallback(
    *,
    session: Dict[str, Any] | None,
    original_text: str,
    failure: Dict[str, Any] | None,
    retry_failures: List[Dict[str, Any]] | None = None,
    player_text: str = "",
    scene_envelope: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
    base_gm: Dict[str, Any] | None = None,
    segmented_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Produce a terminal fallback payload after targeted retries are exhausted.
    Must be deterministic enough to break loops and conservative enough to avoid scene pollution.
    """
    fail = failure if isinstance(failure, dict) else {}
    failure_class = str(fail.get("failure_class") or "").strip()
    reason_list = [str(r) for r in (fail.get("reasons") or []) if isinstance(r, str)]
    out = dict(base_gm) if isinstance(base_gm, dict) else {}
    snap_terminal_entry = snapshot_turn_stage(out, "retry_terminal_fallback_entry")
    record_stage_snapshot(out, "retry_terminal_fallback_entry", snapshot=snap_terminal_entry)

    def _emit_terminal_retry_result(out_obj: Dict[str, Any]) -> None:
        snap_post = snapshot_turn_stage(out_obj, "retry_terminal_fallback_result")
        record_stage_snapshot(out_obj, "retry_terminal_fallback_result", snapshot=snap_post)
        record_stage_transition(
            out_obj,
            "retry_terminal_fallback_entry",
            "retry_terminal_fallback_result",
            snap_terminal_entry,
            snap_post,
        )

    sess = session if isinstance(session, dict) else None
    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    w = world if isinstance(world, dict) else None
    res = resolution if isinstance(resolution, dict) else None
    scene_id = _resolve_scene_id(env)

    soc_terminal_in_scope = bool(
        w is not None
        and _social_answer_fallback_in_scope(
            player_text=str(player_text or ""),
            scene_envelope=env,
            session=sess if isinstance(sess, dict) else {},
            world=w,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        )
    )
    use_social_terminal = bool(_session_social_authority(sess) and soc_terminal_in_scope)

    line = ""
    gm_work: Dict[str, Any] | None = None
    if use_social_terminal:
        eff_res, _, _ = _gm_binding().effective_strict_social_resolution_for_emission(
            res,
            sess,
            w,
            scene_id,
        )
        res_for_social = eff_res if isinstance(eff_res, dict) else res
        gm_work = dict(out)
        if isinstance(res_for_social, dict):
            gm_work = _gm_binding().apply_social_exchange_retry_fallback_gm(
                gm_work,
                player_text=str(player_text or ""),
                session=sess if isinstance(sess, dict) else {},
                world=w if isinstance(w, dict) else {},
                resolution=res_for_social,
                scene_id=scene_id,
            )
        candidate = str(gm_work.get("player_facing_text") or "").strip()
        if not isinstance(res_for_social, dict):
            candidate = ""
        if (
            not candidate
            or _gm_binding().is_route_illegal_global_or_sanitizer_fallback_text(candidate)
        ):
            candidate = _gm_binding().minimal_social_emergency_fallback_line(
                res_for_social if isinstance(res_for_social, dict) else None
            )
        line_raw = str(candidate).strip()
        line = _ensure_terminal_punctuation(line_raw) if line_raw else ""
        gm_work["player_facing_text"] = line
        if not _gm_has_usable_player_facing_text(gm_work):
            out = ensure_minimal_social_resolution(
                gm=gm_work,
                session=sess,
                reason="force_terminal_retry_fallback",
                world=w,
                resolution=res_for_social if isinstance(res_for_social, dict) else None,
                scene_envelope=env,
                player_text=str(player_text or ""),
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            )
            out["retry_failure_class"] = failure_class or None
            out["retry_failure_reasons"] = list(reason_list)
            if retry_failures is not None:
                out["retry_failures_snapshot"] = list(retry_failures)
            rtags = out.get("tags") if isinstance(out.get("tags"), list) else []
            rt = [str(t) for t in rtags if isinstance(t, str)]
            if "retry_escape_hatch" not in rt:
                rt.append("retry_escape_hatch")
            out["tags"] = rt
            _preserve_social_continuity_fields(
                out,
                [base_gm, gm_work],
                sess,
                res,
                world=w,
                scene_id=scene_id,
            )
            if not _gm_has_usable_player_facing_text(out):
                out = ensure_minimal_social_resolution(
                    gm=out,
                    session=sess,
                    reason="force_terminal_retry_fallback_social_repair_chain",
                    world=w,
                    resolution=res_for_social if isinstance(res_for_social, dict) else None,
                    scene_envelope=env,
                    player_text=str(player_text or ""),
                    segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                )
                out["retry_failure_class"] = failure_class or None
                out["retry_failure_reasons"] = list(reason_list)
                if retry_failures is not None:
                    out["retry_failures_snapshot"] = list(retry_failures)
                rtags2 = out.get("tags") if isinstance(out.get("tags"), list) else []
                rt2 = [str(t) for t in rtags2 if isinstance(t, str)]
                if "retry_escape_hatch" not in rt2:
                    rt2.append("retry_escape_hatch")
                out["tags"] = rt2
                _preserve_social_continuity_fields(
                    out,
                    [base_gm, gm_work],
                    sess,
                    res,
                    world=w,
                    scene_id=scene_id,
                )
            preserve_fallback_provenance_metadata(out, base_gm, gm_work)
            _emit_terminal_retry_result(out)
            return out
        line = str(gm_work.get("player_facing_text") or "").strip()
    else:
        line = _nonsocial_forced_retry_progress_line(
            str(player_text or ""),
            scene_envelope=env,
            session=sess,
            world=w,
            resolution=res,
        )

    if not str(line or "").strip():
        anchor_dead = render_nonsocial_terminal_anchor_line(
            env,
            seed_key=f"term|{scene_id}|{player_text[:120]}",
            player_text=str(player_text or ""),
        )
        if isinstance(anchor_dead, str) and anchor_dead.strip():
            line = _ensure_terminal_punctuation(anchor_dead.strip())
            sup_ar = anti_reset_suppresses_intro_style_fallbacks(
                sess,
                env,
                w,
                scene_id,
                res,
            )
            if sup_ar and (
                text_matches_observe_opener_templates(line)
                or text_overlaps_known_scene_intro_sources(line, env)
            ):
                line = _ensure_terminal_punctuation(
                    local_exchange_continuation_fallback_line(
                        session=sess,
                        world=w,
                        scene_id=scene_id,
                        resolution=res,
                    ).strip()
                )
        else:
            line = _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())

    out["player_facing_text"] = _ensure_terminal_punctuation(str(line).strip())
    out["final_route"] = "forced_retry_fallback"
    out["fallback_kind"] = "retry_escape_hatch"
    out["accepted_via"] = "forced_fallback"
    out["retry_exhausted"] = True
    out["targeted_retry_terminal"] = True
    out["retry_failure_class"] = failure_class or None
    out["retry_failure_reasons"] = list(reason_list)
    if retry_failures is not None:
        out["retry_failures_snapshot"] = list(retry_failures)

    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = list(tags) + ["retry_escape_hatch", "forced_retry_fallback", "retry_exhausted"]
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    esc_tail = f"retry_escape_hatch:class={failure_class or 'unknown'}:reasons={','.join(reason_list[:6])}"
    if _session_social_authority(sess) and not soc_terminal_in_scope:
        esc_tail += "|retry_terminal_skipped_social_terminal:block1_world_action_signal"
    out["debug_notes"] = (dbg + " | " if dbg else "") + esc_tail
    if gm_work is not None:
        _preserve_social_continuity_fields(
            out,
            [base_gm, gm_work],
            sess,
            res,
            world=w,
            scene_id=scene_id,
        )
    else:
        _preserve_social_continuity_fields(
            out,
            [base_gm],
            sess,
            res,
            world=w,
            scene_id=scene_id,
        )

    lane_social = _session_social_authority(sess) or _gm_binding().strict_social_emission_will_apply(
        res, sess, w, scene_id
    )
    if lane_social and not _gm_has_usable_player_facing_text(out):
        out = ensure_minimal_social_resolution(
            gm=out,
            session=sess,
            reason="force_terminal_retry_fallback_lane_sweep",
            world=w,
            resolution=res,
            scene_envelope=env,
            player_text=str(player_text or ""),
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        )
        rtags_sweep = out.get("tags") if isinstance(out.get("tags"), list) else []
        rt_sweep = [str(t) for t in rtags_sweep if isinstance(t, str)]
        for extra in ("retry_escape_hatch", "forced_retry_fallback", "retry_exhausted"):
            if extra not in rt_sweep:
                rt_sweep.append(extra)
        out["tags"] = rt_sweep
        out["retry_failure_class"] = failure_class or None
        out["retry_failure_reasons"] = list(reason_list)
        if retry_failures is not None:
            out["retry_failures_snapshot"] = list(retry_failures)
        sweep_sources: List[Dict[str, Any] | None] = [base_gm, gm_work] if gm_work is not None else [base_gm]
        _preserve_social_continuity_fields(
            out,
            sweep_sources,
            sess,
            res,
            world=w,
            scene_id=scene_id,
        )
    if lane_social and not _gm_has_usable_player_facing_text(out):
        out["player_facing_text"] = _ensure_terminal_punctuation(_SOCIAL_EMPTY_REPAIR_HARD_LINE.strip())
        out["fallback_kind"] = "social_empty_resolution_repair"
        out["accepted_via"] = "social_resolution_repair"
        out["retry_exhausted"] = True
        out["targeted_retry_terminal"] = True
        dbg_sw = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        out["debug_notes"] = (
            (dbg_sw + " | " if dbg_sw else "")
            + "social_empty_resolution_repair:lane_sweep_hard_line"
        )
        sweep_sources2: List[Dict[str, Any] | None] = [base_gm, gm_work] if gm_work is not None else [base_gm]
        _preserve_social_continuity_fields(
            out,
            sweep_sources2,
            sess,
            res,
            world=w,
            scene_id=scene_id,
        )

    preserve_fallback_provenance_metadata(out, base_gm, gm_work)

    if use_social_terminal:
        eff_res_final, _, _ = _gm_binding().effective_strict_social_resolution_for_emission(
            res,
            sess,
            w,
            scene_id,
        )
        res_for_repair = eff_res_final if isinstance(eff_res_final, dict) else res
        if isinstance(res_for_repair, dict) and _gm_has_usable_player_facing_text(out):
            pft_end = str(out.get("player_facing_text") or "")
            repaired_end, did_end = _gm_binding().repair_strict_social_terminal_dialogue_fallback_if_needed(
                pft_end,
                resolution=res_for_repair,
                base_gm=out,
                session=sess,
                world=w,
                scene_id=scene_id,
                retry_terminal=True,
            )
            if did_end:
                out["player_facing_text"] = _ensure_terminal_punctuation(repaired_end.strip())

    _emit_terminal_retry_result(out)
    return out
