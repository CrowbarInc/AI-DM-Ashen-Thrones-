from __future__ import annotations

from typing import Any, Dict, List

from game.interaction_context import inspect as inspect_interaction_context
from game.output_sanitizer import sanitize_player_facing_output
from game.social_exchange_emission import (
    build_final_strict_social_response,
    effective_strict_social_resolution_for_emission,
    log_final_emission_decision,
    log_final_emission_trace,
    merged_player_prompt_for_gate,
    minimal_social_emergency_fallback_line,
    strict_social_emission_will_apply,
    strict_social_suppress_non_native_coercion_for_narration_beat,
    _npc_display_name_for_emission,
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
    text = pre_gate_text

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
        out["player_facing_text"] = text
        final_emitted_source = str(details.get("final_emitted_source") or "unknown_post_gate_writer")
        if retry_output:
            final_emitted_source = "retry_output"
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
            }
            log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
            return out

        fb_kind = str(details.get("fallback_kind") or "none")
        deterministic_attempted = bool(details.get("deterministic_attempted"))
        deterministic_passed = bool(details.get("deterministic_passed"))
        fallback_pool = str(details.get("fallback_pool") or "social_deterministic")
        candidate_ok = False
        rejection_reasons = details.get("rejection_reasons") if isinstance(details.get("rejection_reasons"), list) else []

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
        }
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
        return out

    low = text.lower()
    banned_any_route = (
        "from here, no certain answer presents itself",
        "the truth is still buried beneath rumor and rain",
    )
    if any(phrase in low for phrase in banned_any_route):
        reasons.append("banned_stock_phrase")

    candidate_ok = not bool(reasons)
    fallback_pool = "none"
    fallback_kind = "none"
    deterministic_attempted = False
    deterministic_passed = False
    final_emitted_source = "unknown_post_gate_writer"

    if not reasons:
        out["player_facing_text"] = text
        final_emitted_source = "generated_candidate"
        if retry_output:
            final_emitted_source = "retry_output"

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
        log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_accept"})
        return out

    # Non-social replace path only (strict-social replacement is handled in build_final_strict_social_response).
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
        fallback_pool = "global_scene_narrative"
        fallback_text = "For a breath, the scene holds while voices shift around you."
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
    }
    log_final_emission_trace({**out["_final_emission_meta"], "stage": "final_emission_gate_replace"})
    return out
