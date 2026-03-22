from __future__ import annotations

from typing import Any, Dict, List

from game.interaction_context import inspect as inspect_interaction_context
from game.social_exchange_emission import (
    coerce_resolution_for_strict_social_emission,
    deterministic_social_fallback_line,
    emission_gate_interruption_active,
    emission_gate_pressure_active,
    emission_gate_uncertainty_source,
    hard_reject_social_exchange_text,
    is_route_illegal_global_or_sanitizer_fallback_text,
    log_final_emission_decision,
    log_final_emission_trace,
    merged_player_prompt_for_gate,
    minimal_social_emergency_fallback_line,
    minimal_social_resolution_for_directed_question_guard,
    apply_strict_social_sentence_ownership_filter,
    replacement_is_route_legal_social,
)


def _normalize_text(text: str | None) -> str:
    return " ".join(str(text or "").strip().split())


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


def _reply_kind(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    sp = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(sp.get("reply_kind") or "").strip().lower()


def apply_final_emission_gate(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
    world: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Hard legal-state gate for the final emitted text."""
    if not isinstance(gm_output, dict):
        return gm_output
    out = dict(gm_output)
    pre_gate_text = _normalize_text(out.get("player_facing_text"))
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]

    eff_resolution, social_route, coercion_reason = coerce_resolution_for_strict_social_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    )
    merged_prompt = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        str(scene_id or "").strip(),
    )
    if not social_route:
        guard_res = minimal_social_resolution_for_directed_question_guard(
            session if isinstance(session, dict) else None,
            world if isinstance(world, dict) else None,
            str(scene_id or "").strip(),
            merged_player_prompt=merged_prompt,
            resolution=resolution if isinstance(resolution, dict) else None,
        )
        if isinstance(guard_res, dict):
            eff_resolution = guard_res
            social_route = True
            coercion_reason = f"{coercion_reason}|npc_directed_guard"

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
    text = pre_gate_text

    if social_route:
        normalization_ran = True
        text = _normalize_text(
            apply_strict_social_sentence_ownership_filter(
                text,
                resolution=eff_resolution,
                tags=tag_list,
                session=session if isinstance(session, dict) else None,
                scene_id=str(scene_id or "").strip(),
            )
        )

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")

    if social_route:
        reasons.extend(
            hard_reject_social_exchange_text(
                text,
                resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
                session=session if isinstance(session, dict) else None,
            )
        )

    candidate_ok = not bool(reasons)
    fallback_pool = "none"
    fallback_kind = "none"
    deterministic_attempted = False
    deterministic_passed = False
    final_emitted_source = "unknown_post_gate_writer"
    strict_social_active = bool(social_route)
    coercion_used = "|" in coercion_reason or "synthetic" in coercion_reason or "npc_directed_guard" in coercion_reason

    retry_output = any(
        isinstance(t, str) and ("question_retry_fallback" in t or "social_exchange_retry_fallback" in t)
        for t in tag_list
    )

    if not reasons:
        out["player_facing_text"] = text
        if social_route:
            final_emitted_source = (
                "generated_candidate" if pre_gate_text.strip() == text.strip() else "normalized_social_candidate"
            )
        else:
            final_emitted_source = "generated_candidate"
        if retry_output:
            final_emitted_source = "retry_output"

        gate_out_text = _normalize_text(out.get("player_facing_text"))
        post_gate_mutation_detected = pre_gate_text != gate_out_text

        log_final_emission_decision(
            {
                "stage": "final_emission_gate",
                "social_route": social_route,
                "coercion_reason": coercion_reason,
                "resolution_kind": res_kind,
                "social_intent_class": social_ic,
                "active_interlocutor": active_interlocutor or None,
                "candidate_ok": True,
                "rejection_reasons": [],
                "fallback_pool": fallback_pool,
                "fallback_kind": fallback_kind,
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
        }
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
        return out

    uncertainty_source = emission_gate_uncertainty_source(tag_list, text)
    pressure_active = emission_gate_pressure_active(tag_list, session, scene_id)
    interruption_active = emission_gate_interruption_active(tag_list, text)
    seed = (
        f"{scene_id}|{_speaker_label(eff_resolution)}|{_question_prompt_for_resolution(eff_resolution)}|"
        f"{uncertainty_source}|{pressure_active}|{interruption_active}|{'|'.join(sorted(set(tag_list)))}"
    )

    if social_route:
        fallback_pool = "social_deterministic"
        deterministic_attempted = True
        fallback_text, fallback_kind = deterministic_social_fallback_line(
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            uncertainty_source=uncertainty_source,
            pressure_active=pressure_active,
            interruption_active=interruption_active,
            seed=seed,
        )
        deterministic_passed = replacement_is_route_legal_social(
            fallback_text,
            resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
        )
        if not deterministic_passed:
            fallback_text = minimal_social_emergency_fallback_line(
                eff_resolution if isinstance(eff_resolution, dict) else None
            )
            fallback_kind = "emergency_social_minimal"
            final_emitted_source = "minimal_social_emergency_fallback"
        else:
            final_emitted_source = "deterministic_social_fallback"
    else:
        fallback_pool = "global_scene_narrative"
        fallback_text = "For a breath, the scene holds while voices shift around you."
        fallback_kind = "narrative_safe_fallback"
        final_emitted_source = "global_scene_fallback"

    if strict_social_active and is_route_illegal_global_or_sanitizer_fallback_text(fallback_text):
        fb0 = fallback_text
        fallback_text = minimal_social_emergency_fallback_line(
            eff_resolution if isinstance(eff_resolution, dict) else None
        )
        fallback_kind = "emergency_social_minimal"
        final_emitted_source = "minimal_social_emergency_fallback"
        deterministic_passed = False
        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + f"final_emission_gate:route_illegal_writer_intercepted:{fb0[:80]}"
        )

    out["player_facing_text"] = fallback_text
    out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fallback_kind}"]
    if strict_social_active and final_emitted_source == "minimal_social_emergency_fallback":
        out["tags"] = list(out["tags"]) + ["terminal_strict_social_emission", "strict_social_terminal_safe"]

    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:replaced:"
        + ",".join(reasons[:8])
    )
    log_final_emission_decision(
        {
            "stage": "final_emission_gate",
            "social_route": social_route,
            "coercion_reason": coercion_reason,
            "resolution_kind": res_kind,
            "social_intent_class": social_ic,
            "active_interlocutor": active_interlocutor or None,
            "candidate_ok": candidate_ok,
            "rejection_reasons": reasons[:12],
            "fallback_pool": fallback_pool,
            "fallback_kind": fallback_kind,
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
    }
    log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
    return out
