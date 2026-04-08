from __future__ import annotations

from typing import Any, Dict, List, Tuple
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
from game.interaction_context import inspect as inspect_interaction_context

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
)


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

def prioritize_retry_failures_for_social_answer_candidate(
    failures: List[Dict[str, Any]],
    *,
    player_text: str,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
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
        "known_fact_context": {
            "answer": text,
            "source": str(best.get("source") or "").strip(),
            "subject": "",
            "position": "",
        },
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


def build_retry_prompt_for_failure(
    failure: Dict[str, Any],
    *,
    response_policy: Dict[str, Any] | None = None,
) -> str:
    """Build a narrowly scoped retry instruction for one failure class only."""
    failure_class = str((failure or {}).get("failure_class") or "").strip()
    reasons = [str(r).strip() for r in ((failure or {}).get("reasons") or []) if isinstance(r, str) and str(r).strip()]
    priority_order = (
        list((response_policy or {}).get("rule_priority_order") or [])
        if isinstance((response_policy or {}).get("rule_priority_order"), list)
        else [label for _, label in RESPONSE_RULE_PRIORITY]
    )
    shared = (
        f"Rule Priority Hierarchy: {priority_order}. "
        f"{RULE_PRIORITY_COMPACT_INSTRUCTION} "
        f"Retry target: {failure_class}. Correct only this failure class. Return the same JSON shape."
    )

    if failure_class == "validator_voice":
        return (
            f"{shared} Rewrite the reply into diegetic, world-facing phrasing only. "
            f"{NO_VALIDATOR_VOICE_RULE} "
            "Remove validator, system, limitation, tool-access, model-identity, and rules-explanation language from standard narration."
        )

    if failure_class == "answer":
        patched = dict(failure or {})
        patched["failure_class"] = "unresolved_question"
        return build_retry_prompt_for_failure(patched, response_policy=response_policy)

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
                "Do not reroute it into uncertainty, refusal, or generic fallback language."
                f"{social_shape_hint}"
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
            "If certainty is incomplete, keep uncertainty concrete and bounded to speaker evidence or scene facts."
            f"{category_hint}{context_hint}{first_sentence_hint}{speaker_hint}{social_shape_hint}"
        )

    if failure_class == "echo_or_repetition":
        return (
            f"{shared} Semantically rewrite the reply so it does not echo the player's wording or quoted speech. "
            "Change sentence structure and phrasing, and react with new information or consequence instead of restating the input."
        )

    if failure_class == "followup_soft_repetition":
        ctx = (failure or {}).get("followup_context") if isinstance((failure or {}).get("followup_context"), dict) else {}
        prev_player = str(ctx.get("previous_player_input") or "").strip()
        prev_answer = str(ctx.get("previous_answer_snippet") or "").strip()
        topic_tokens = ctx.get("topic_tokens") if isinstance(ctx.get("topic_tokens"), list) else []
        topic_hint = f" Topic tokens: {topic_tokens}." if topic_tokens else ""
        prev_player_hint = f" Previous player press: {prev_player}." if prev_player else ""
        prev_answer_hint = f" Previous answer snippet (do not recycle): {prev_answer}." if prev_answer else ""
        return (
            f"{shared} The player is pressing the same topic again, and your reply repeated the prior answer without escalation."
            f"{topic_hint}{prev_player_hint}{prev_answer_hint} "
            "Do NOT restate the same underlying lead. Escalate with new content: add one concrete detail AND one of "
            "(a) a named person/place/faction/witness (with an in-world source), or (b) a narrowed unknown boundary (time window, location bracket, condition, count). "
            "End with a more actionable immediate next step that uses the new detail. Preserve speaker grounding and diegetic voice."
        )

    if failure_class == "npc_contract_failure":
        missing = [str(x).strip() for x in ((failure or {}).get("missing") or []) if isinstance(x, str) and str(x).strip()]
        missing_hint = f" Missing contract elements: {missing}." if missing else ""
        return (
            f"{shared} Produce a direct NPC answer, reaction, or refusal consistent with the current target. "
            "Include at least one concrete person, place, faction, next step, or directly usable condition, time, or location."
            f"{missing_hint}"
        )

    if failure_class == "topic_pressure_escalation":
        ctx = (failure or {}).get("topic_context") if isinstance((failure or {}).get("topic_context"), dict) else {}
        topic_key = str(ctx.get("topic_key") or "").strip()
        prev_answer = str(ctx.get("previous_answer_snippet") or "").strip()
        repeat_count = int(ctx.get("repeat_count", 0) or 0)
        topic_hint = f" Topic key: {topic_key}." if topic_key else ""
        prev_answer_hint = f" Prior low-gain answer (do not paraphrase): {prev_answer}." if prev_answer else ""
        return (
            f"{shared} The player has pressed this unresolved topic repeatedly without meaningful progress."
            f"{topic_hint}{prev_answer_hint} Repetition count: {repeat_count}. "
            "You MUST escalate now with diegetic motion. Choose one: new NPC interruption, refusal that changes the scene, concrete clue, emerging threat, or environmental shift. "
            "Include exactly one scene momentum tag and end with a concrete immediate action the player can take."
        )

    if failure_class == "scene_stall":
        return (
            f"{shared} Advance the scene by one concrete development now. "
            "Introduce one actionable reveal, answer, consequence, opportunity, environmental change, or new pressure so the exchange does not remain static. "
            "Include exactly one matching scene momentum tag in tags: scene_momentum:<kind>."
        )

    if failure_class == "forbidden_generic_phrase":
        return (
            f"{shared} Rewrite only the offending generic phrase or sentence into scene-anchored specifics. "
            "Keep the rest of the reply intact where possible and avoid flattening the whole response."
        )

    reason_text = f" Reasons: {reasons}." if reasons else ""
    return f"{shared} Rewrite narrowly to resolve this failure.{reason_text}"

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


def detect_retry_failures(
    *,
    player_text: str,
    gm_reply: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
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
        known_fact = resolve_known_fact_before_uncertainty(
            player_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        )
        failure_payload = {
            "failure_class": "unresolved_question",
            "priority": RETRY_FAILURE_PRIORITY["unresolved_question"],
            "reasons": list(question_rule.get("reasons") or []),
        }
        if known_fact:
            failure_payload["known_fact_context"] = {
                "answer": str(known_fact.get("text") or "").strip(),
                "source": str(known_fact.get("source") or "").strip(),
                "subject": str(known_fact.get("subject") or "").strip(),
                "position": str(known_fact.get("position") or "").strip(),
            }
        else:
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
) -> Dict[str, Any]:
    """Apply deterministic fallback when targeted retry still fails."""
    if not isinstance(gm, dict):
        return gm
    failure_class = str((failure or {}).get("failure_class") or "").strip()
    if failure_class not in ("unresolved_question", "answer"):
        return gm

    known_fact_ctx = (failure or {}).get("known_fact_context") if isinstance((failure or {}).get("known_fact_context"), dict) else {}
    if failure_class == "answer" and str(known_fact_ctx.get("answer") or "").strip():
        out = dict(gm)
        out["player_facing_text"] = _ensure_terminal_punctuation(str(known_fact_ctx.get("answer") or "").strip())
        tags = out.get("tags") if isinstance(out.get("tags"), list) else []
        out["tags"] = list(tags) + ["question_retry_fallback", "known_fact_guard", "social_answer_retry"]
        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        source = str(known_fact_ctx.get("source") or "social_answer_candidate").strip()
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + f"retry_fallback:answer:known_fact_guard:{source}"
        )
        return out

    known_fact = resolve_known_fact_before_uncertainty(
        player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    out = dict(gm)
    if isinstance(known_fact, dict) and str(known_fact.get("text") or "").strip():
        out["player_facing_text"] = _ensure_terminal_punctuation(str(known_fact.get("text") or "").strip())
        tags = out.get("tags") if isinstance(out.get("tags"), list) else []
        out["tags"] = list(tags) + ["question_retry_fallback", "known_fact_guard"]
        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        source = str(known_fact.get("source") or "known_fact").strip()
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + f"retry_fallback:unresolved_question:known_fact_guard:{source}"
        )
        return out

    scene_id = str((scene_envelope.get("scene") or {}).get("id") or "").strip()
    eff_res, strict_route, _ = _gm_binding().effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        scene_id,
    )
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
            return out
    if strict_route and isinstance(eff_res, dict):
        return _gm_binding().apply_social_exchange_retry_fallback_gm(
            out,
            player_text=player_text,
            session=session,
            world=world,
            resolution=eff_res,
            scene_id=scene_id,
        )

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
    )
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = list(tags) + ["question_retry_fallback"]
    return out


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
    """Short narrator fallback after retries: acknowledge when possible, one concrete forward beat."""
    pt = str(player_text or "").strip()
    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    sess = session if isinstance(session, dict) else {}
    w = world if isinstance(world, dict) else {}
    if _is_direct_player_question(pt):
        known_fact = resolve_known_fact_before_uncertainty(
            pt,
            scene_envelope=env,
            session=sess,
            world=w,
            resolution=resolution,
        )
        if isinstance(known_fact, dict) and str(known_fact.get("text") or "").strip():
            return _ensure_terminal_punctuation(str(known_fact.get("text") or "").strip())
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

    loc = _resolve_scene_location(env)
    visible = _scene_visible_facts(env)
    sid = _resolve_scene_id(env)
    seed = f"{sid}|{pt[:200]}"
    idx = _stable_u32_from_seed(seed) % 3
    loc_bit = f" near {loc}" if loc else ""
    detail = _clean_scene_detail(visible[0]) if visible else ""
    templates: List[str] = [
        (
            f"You weigh what you just tried{loc_bit}; "
            "the next beat is yours—move toward the clearest face in front of you, let the crowd push you a step, or hold still and listen hard."
        ),
        (
            f"The moment doesn't sharpen on its own{loc_bit}, so you choose footing: "
            "step aside for a cleaner sightline, trade a flat look with the nearest watcher, or head for the nearest door you already know."
        ),
    ]
    if detail:
        templates.append(
            f"{detail[:1].upper()}{detail[1:] if len(detail) > 1 else ''} still reads the same{loc_bit}; "
            "you can examine it closer, leave it, or change your angle before anyone decides for you."
        )
    return _ensure_terminal_punctuation(templates[idx % len(templates)])


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
            f"{lead} holds the room while the situation asks for your next move.",
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

    ctx_mode_social = ""
    if not _gm_has_usable_player_facing_text(out):
        line = _gm_binding().minimal_social_emergency_fallback_line(
            res_for_line if isinstance(res_for_line, dict) else None
        )
        if (
            not isinstance(line, str)
            or not line.strip()
            or _gm_binding().is_route_illegal_global_or_sanitizer_fallback_text(line)
            or _is_placeholder_only_player_facing_text(line)
        ):
            c_line, ctx_mode_social = _contextual_social_repair_line(gm=out, session=sess, world=w)
            if _gm_has_usable_player_facing_text({"player_facing_text": c_line}):
                line = c_line
            else:
                line = _SOCIAL_EMPTY_REPAIR_HARD_LINE
                ctx_mode_social = "hard_fallback"
        out["player_facing_text"] = _ensure_terminal_punctuation(str(line).strip())

    if not _gm_has_usable_player_facing_text(out):
        out["player_facing_text"] = _ensure_terminal_punctuation(_SOCIAL_EMPTY_REPAIR_HARD_LINE.strip())
        ctx_mode_social = "hard_fallback"

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
) -> Dict[str, Any]:
    """
    Produce a terminal fallback payload after targeted retries are exhausted.
    Must be deterministic enough to break loops and conservative enough to avoid scene pollution.
    """
    fail = failure if isinstance(failure, dict) else {}
    failure_class = str(fail.get("failure_class") or "").strip()
    reason_list = [str(r) for r in (fail.get("reasons") or []) if isinstance(r, str)]
    out = dict(base_gm) if isinstance(base_gm, dict) else {}
    sess = session if isinstance(session, dict) else None
    env = scene_envelope if isinstance(scene_envelope, dict) else {}
    w = world if isinstance(world, dict) else None
    res = resolution if isinstance(resolution, dict) else None
    scene_id = _resolve_scene_id(env)

    line = ""
    gm_work: Dict[str, Any] | None = None
    if _session_social_authority(sess):
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
        line = _ensure_terminal_punctuation(
            "You hold your ground a breath, then choose your next move: step in, step back, or hold still and watch who reacts first."
        )

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
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + f"retry_escape_hatch:class={failure_class or 'unknown'}:reasons={','.join(reason_list[:6])}"
    )
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

    return out
