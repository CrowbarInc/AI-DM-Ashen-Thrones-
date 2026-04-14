"""Support-only repair owner for final emission.

This module owns deterministic repair logic, skip helpers, and extracted layer wiring
for final emission. It is **not** the canonical owner for response-policy contracts
(:mod:`game.response_policy_contracts`) and **not** the top-level orchestration owner
(:mod:`game.final_emission_gate`).

It remains an extracted helper layer with transitional residue from earlier gate-local
implementations; that residue does not make this module the boundary authority for the
contracts it consumes.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from game.final_emission_meta import (
    build_narrative_authenticity_emission_trace,
    default_narrative_authenticity_layer_meta,
    merge_narrative_authenticity_into_final_emission_meta,
)
from game.final_emission_text import (
    _capitalize_sentence_fragment,
    _normalize_terminal_punctuation,
    _normalize_text,
)
from game.final_emission_validators import (
    _FALLBACK_FABRICATED_AUTHORITY_PATTERNS,
    _FALLBACK_META_VOICE_PATTERNS,
    _FALLBACK_OVERCERTAIN_BY_SOURCE,
    _FALLBACK_OVERCERTAIN_GENERAL_PATTERNS,
    _EXPOSITORY_CONNECTOR_RES,
    _bounded_partial_thin_substance_violation,
    _allowed_hedge_in_text,
    _contains_diegetic_uncertainty_partial,
    _concrete_payload_for_kinds,
    _content_tokens,
    _NEXT_LEAD_SNIPPET,
    _contract_bool,
    _looks_like_single_clarifying_question,
    _opening_carries_allowed_delta,
    _opening_segment,
    _partial_reason_in_text,
    _response_delta_snippet_substantive,
    _response_delta_token_overlap_ratio,
    _response_delta_tokens,
    _sentence_carries_response_delta,
    _sentence_substantive_for_frontload,
    _split_sentences_answer_complete,
    inspect_social_response_structure,
    validate_answer_completeness,
    validate_fallback_behavior,
    validate_response_delta,
    validate_social_response_structure,
)
from game.leads import get_lead, normalize_lead
from game.response_policy_contracts import (
    materialize_response_policy_bundle,
    resolve_answer_completeness_contract,
    resolve_fallback_behavior_contract,
    resolve_response_delta_contract,
)
from game.social_exchange_emission import (
    minimal_social_emergency_fallback_line,
    strict_social_emission_will_apply,
    _npc_display_name_for_emission,
)

def _social_fallback_resolution(
    *,
    resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any] | None:
    if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict):
        return resolution
    if not active_interlocutor or not isinstance(world, dict):
        return None
    return {
        "kind": "question",
        "social": {
            "npc_id": active_interlocutor,
            "npc_name": _npc_display_name_for_emission(world, scene_id, active_interlocutor),
            "social_intent_class": "social_exchange",
        },
    }


def _to_second_person_action_clause(player_input: str, resolution: Dict[str, Any] | None) -> str:
    raw = _normalize_text(player_input or str((resolution or {}).get("prompt") or "")).rstrip(".!?")
    if not raw:
        return "You act"
    low = raw.lower()
    if low.startswith("you "):
        return _capitalize_sentence_fragment(raw)
    if low.startswith("i am "):
        return f"You are {raw[5:]}"
    if low.startswith("i'm "):
        return f"You are {raw[4:]}"
    if low.startswith("i "):
        return f"You {raw[2:]}"
    if re.match(
        r"^(?:go|move|travel|investigate|inspect|search|open|close|take|grab|climb|follow|approach|look|examine|head|ask|speak|draw|attack|strike|cast|use|push|pull|listen|wait)\b",
        low,
    ):
        return f"You {raw}"
    return "You act on that move"


def _action_result_summary(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "the scene answers with an immediate change"
    state_changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
    check_request = resolution.get("check_request") if isinstance(resolution.get("check_request"), dict) else {}
    kind = str(resolution.get("kind") or "").strip().lower()
    if bool(resolution.get("resolved_transition")) or state_changes.get("scene_transition_occurred") or state_changes.get("arrived_at_scene"):
        return "the scene shifts with that movement"
    if state_changes.get("already_searched"):
        if kind in {"investigate", "observe", "search"}:
            return "the search turns up nothing new"
        return "the attempt turns up nothing new"
    if state_changes.get("clue_revealed") or resolution.get("clue_id") or resolution.get("discovered_clues"):
        return "you turn up a concrete clue"
    if state_changes.get("skill_check_failed"):
        return "the attempt catches and fails to land cleanly"
    if bool(resolution.get("requires_check")) or bool(check_request.get("requires_check")):
        return "the attempt now calls for a check"
    if resolution.get("success") is False:
        return "the attempt meets resistance"
    if resolution.get("success") is True:
        return "the attempt produces an immediate result"
    if kind in {"investigate", "observe"}:
        return "you get an immediate read on what is there"
    if kind in {"travel", "scene_transition"}:
        return "your position in the scene changes"
    return "the situation answers that move right away"


def _minimal_answer_contract_repair(
    *,
    resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> str | None:
    social_resolution = _social_fallback_resolution(
        resolution=resolution,
        active_interlocutor=active_interlocutor,
        world=world,
        scene_id=scene_id,
    )
    if isinstance(social_resolution, dict):
        return minimal_social_emergency_fallback_line(social_resolution)
    check_request = resolution.get("check_request") if isinstance(resolution, dict) and isinstance(resolution.get("check_request"), dict) else {}
    prompt = _normalize_terminal_punctuation(str(check_request.get("player_prompt") or "").strip())
    if prompt:
        return prompt
    adjudication = resolution.get("adjudication") if isinstance(resolution, dict) and isinstance(resolution.get("adjudication"), dict) else {}
    answer_type = str(adjudication.get("answer_type") or "").strip().lower()
    if answer_type == "needs_concrete_action":
        return "You need a more concrete in-scene action or target before that can be answered."
    if answer_type == "check_required" or bool((resolution or {}).get("requires_check")):
        return "That cannot be answered cleanly until the required check is resolved."
    return "No direct answer is established from the current state yet."


def _minimal_action_outcome_contract_repair(
    *,
    player_input: str,
    resolution: Dict[str, Any] | None,
) -> str:
    action_clause = _to_second_person_action_clause(player_input, resolution)
    result_clause = _action_result_summary(resolution)
    return _normalize_terminal_punctuation(f"{action_clause}, and {result_clause}")

def _skip_answer_completeness_layer(
    *,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    """Return skip reason, or None when the layer should run."""
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if isinstance(gm_output, dict):
        tags_ac = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
        tl = [str(t) for t in tags_ac if isinstance(t, str)]
        if "question_retry_fallback" in tl and (
            "known_fact_guard" in tl
            or "social_answer_retry" in tl
        ):
            dbg_ac = gm_output.get("debug_notes") if isinstance(gm_output.get("debug_notes"), str) else ""
            if "retry_fallback_chosen:nonsocial_uncertainty_pool_after_block1_social_out_of_scope" in dbg_ac:
                return None
            return "deterministic_known_fact_retry_fallback"
    if not strict_social_details:
        return None
    if strict_social_details.get("used_internal_fallback"):
        return "strict_social_authoritative_internal_fallback"
    if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
        return "strict_social_ownership_terminal_repair"
    fe = str(strict_social_details.get("final_emitted_source") or "")
    if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
        if _strict_social_answer_pressure_ac_contract_active(gm_output):
            return None
        return "strict_social_structured_or_bridge_source"
    return None


def _repair_answer_completeness_minimal(
    text: str,
    validation: Dict[str, Any],
    contract: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
) -> tuple[str | None, str | None]:
    """Reorder or compress existing sentences only; no new facts."""
    sentences = _split_sentences_answer_complete(text)
    exp_shape = str(contract.get("expected_answer_shape") or "").strip().lower()
    exp_voice = str(contract.get("expected_voice") or "").strip().lower()
    soc = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    gate_line = str(soc.get("information_gate") or "").strip()
    partial_now = validation.get("partial_reason_detected")

    if validation.get("direct_answer_found_later") and len(sentences) > 1:
        pick: str | None = None
        pick_idx = -1
        for idx, sent in enumerate(sentences):
            if idx == 0:
                continue
            if _sentence_substantive_for_frontload(sent, contract=contract):
                pick = sent
                pick_idx = idx
                break
        if pick and pick_idx > 0:
            rest = sentences[:pick_idx] + sentences[pick_idx + 1 :]
            merged = _normalize_terminal_punctuation(pick) + " " + " ".join(
                _normalize_terminal_punctuation(s) for s in rest if s
            )
            return _normalize_text(merged), "frontload_direct_answer"

    reason_sents: List[str] = []
    partial_sents: List[str] = []
    lead_sents: List[str] = []
    for sent in sentences:
        if _partial_reason_in_text(sent, list(contract.get("allowed_partial_reasons") or [])):
            reason_sents.append(sent)
        if _concrete_payload_for_kinds(sent, list(contract.get("concrete_payload_any_of") or [])):
            partial_sents.append(sent)
        if _NEXT_LEAD_SNIPPET.search(sent):
            lead_sents.append(sent)

    if exp_shape in {"bounded_partial", "refusal_with_reason"} or partial_now:
        ordered: List[str] = []
        if partial_sents:
            ordered.append(partial_sents[0])
        if reason_sents:
            ordered.append(reason_sents[0])
        if lead_sents:
            ordered.append(lead_sents[0])
        if len(ordered) >= 2:
            tail_pool = [s for s in sentences if s not in ordered]
            body = " ".join(_normalize_terminal_punctuation(s) for s in ordered + tail_pool if s)
            return _normalize_text(body), "normalize_bounded_partial_order"

    if partial_now == "gated_information" or soc.get("gated_information") or gate_line:
        boundary = gate_line
        if not boundary:
            m = re.search(
                r"\b(?:orders|sworn|quiet|here|now|captain|command)\b[^.!?]{0,80}",
                text,
                re.IGNORECASE,
            )
            if m:
                boundary = _normalize_text(m.group(0))
        nucleus = sentences[0] if sentences else text
        if boundary and nucleus and boundary.lower() not in nucleus.lower():
            glue = _normalize_terminal_punctuation(f"{nucleus} ({boundary}).")
            rest = " ".join(sentences[1:] if len(sentences) > 1 else [])
            if rest:
                return _normalize_text(f"{glue} {rest}"), "surface_gated_boundary"
        if gate_line:
            head = sentences[0] if sentences else text
            return _normalize_text(f"{head.rstrip('.!?')}—{gate_line}."), "inject_resolution_gate_phrase"

    if exp_voice == "npc" and partial_now == "lack_of_knowledge":
        lead = next((s for s in lead_sents), "")
        head0 = sentences[0] if sentences else text
        if lead:
            pack = _normalize_terminal_punctuation(head0) + " " + _normalize_terminal_punctuation(lead)
            return _normalize_text(pack), "npc_ignorance_pair_compress"

    return None, None


def _apply_answer_completeness_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    contract = resolve_answer_completeness_contract(gm_output)
    skip = _skip_answer_completeness_layer(
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        gm_output=gm_output,
    )
    meta: Dict[str, Any] = {
        "answer_completeness_checked": False,
        "answer_completeness_failed": False,
        "answer_completeness_failure_reasons": [],
        "answer_completeness_repaired": False,
        "answer_completeness_repair_mode": None,
        "answer_completeness_expected_voice": None,
        "answer_completeness_skip_reason": skip,
    }
    if skip or not isinstance(contract, dict):
        return text, meta, []

    v0 = validate_answer_completeness(text, contract, resolution=resolution)
    meta["answer_completeness_checked"] = bool(v0.get("checked"))
    meta["answer_completeness_expected_voice"] = v0.get("answer_completeness_expected_voice")
    if not v0.get("checked"):
        return text, meta, []

    if v0.get("passed"):
        return text, meta, []

    meta["answer_completeness_failed"] = True
    meta["answer_completeness_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired, mode = _repair_answer_completeness_minimal(
        text,
        v0,
        contract,
        resolution=resolution,
    )
    if repaired:
        v1 = validate_answer_completeness(repaired, contract, resolution=resolution)
        if v1.get("passed"):
            meta["answer_completeness_repaired"] = True
            meta["answer_completeness_repair_mode"] = mode
            meta["answer_completeness_failed"] = False
            meta["answer_completeness_failure_reasons"] = []
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("answer_completeness_unsatisfied_after_repair")
    meta["answer_completeness_failed"] = True
    return text, meta, extra


def _merge_answer_completeness_meta(meta: Dict[str, Any], ac_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "answer_completeness_checked": bool(ac_dbg.get("answer_completeness_checked")),
            "answer_completeness_failed": bool(ac_dbg.get("answer_completeness_failed")),
            "answer_completeness_failure_reasons": list(ac_dbg.get("answer_completeness_failure_reasons") or []),
            "answer_completeness_repaired": bool(ac_dbg.get("answer_completeness_repaired")),
            "answer_completeness_repair_mode": ac_dbg.get("answer_completeness_repair_mode"),
            "answer_completeness_expected_voice": ac_dbg.get("answer_completeness_expected_voice"),
            "answer_completeness_skip_reason": ac_dbg.get("answer_completeness_skip_reason"),
        }
    )
def _default_response_delta_meta() -> Dict[str, Any]:
    return {
        "response_delta_checked": False,
        "response_delta_failed": False,
        "response_delta_failure_reasons": [],
        "response_delta_repaired": False,
        "response_delta_repair_mode": None,
        "response_delta_kind_detected": None,
        "response_delta_echo_overlap_ratio": None,
        "response_delta_skip_reason": None,
        "response_delta_trigger_source": None,
    }


def _strict_social_answer_pressure_ac_contract_active(gm_output: Dict[str, Any] | None) -> bool:
    """True when prompt_context activated answer-completeness for strict-social answer-pressure (Block 1)."""
    ac = resolve_answer_completeness_contract(gm_output)
    if not isinstance(ac, dict):
        return False
    if not _contract_bool(ac, "enabled") or not _contract_bool(ac, "answer_required"):
        return False
    trace = ac.get("trace") if isinstance(ac.get("trace"), dict) else {}
    return bool(trace.get("strict_social_answer_seek_override"))


def _strict_social_answer_pressure_rd_contract_active(gm_output: Dict[str, Any] | None) -> bool:
    """True when response_delta is enabled with strict_social_answer_pressure trigger (Block 1)."""
    rd = resolve_response_delta_contract(gm_output)
    if not isinstance(rd, dict) or not _contract_bool(rd, "enabled"):
        return False
    ts = str(rd.get("trigger_source") or "").strip()
    if ts == "strict_social_answer_pressure":
        return True
    tr = rd.get("trace") if isinstance(rd.get("trace"), dict) else {}
    return str(tr.get("trigger_source") or "").strip() == "strict_social_answer_pressure"


def _clue_text_for_spoken_cash_out(session: Dict[str, Any], clue_id: str | None) -> str:
    if not clue_id or not isinstance(session, dict):
        return ""
    ck = session.get("clue_knowledge") if isinstance(session.get("clue_knowledge"), dict) else {}
    entry = ck.get(str(clue_id).strip())
    if not isinstance(entry, dict):
        return ""
    t = entry.get("text")
    return str(t).strip()[:400] if isinstance(t, str) and t.strip() else ""


def _lead_row_phrase_for_spoken_cash_out(session: Dict[str, Any], lead_id: str | None) -> str:
    if not lead_id:
        return ""
    row = get_lead(session, lead_id)
    if not isinstance(row, dict):
        return ""
    ld = normalize_lead(dict(row))
    for key in ("next_step", "summary", "title"):
        v = str(ld.get(key) or "").strip()
        if len(v) >= 6:
            return v[:400]
    return ""


def _refinement_phrase_for_lead_or_clue_id(session: Dict[str, Any], lead_or_clue_id: str | None) -> str:
    """Non-inventive phrase: prefer clue text, then registry row, then registry row matched by evidence clue id."""
    cid = str(lead_or_clue_id or "").strip()
    if not cid or not isinstance(session, dict):
        return ""
    t = _clue_text_for_spoken_cash_out(session, cid)
    if t:
        return t
    lp = _lead_row_phrase_for_spoken_cash_out(session, cid)
    if lp:
        return lp
    reg = session.get("lead_registry")
    if not isinstance(reg, dict):
        return ""
    for row in reg.values():
        if not isinstance(row, dict):
            continue
        ev = row.get("evidence_clue_ids") if isinstance(row.get("evidence_clue_ids"), list) else []
        evs = {str(x).strip() for x in ev if x}
        if cid not in evs:
            continue
        ld = normalize_lead(dict(row))
        for key in ("title", "summary", "next_step"):
            v = str(ld.get(key) or "").strip()
            if len(v) >= 6:
                return v[:400]
    return ""


def _topic_press_context_tokens(resolution: Dict[str, Any] | None) -> set[str]:
    toks: set[str] = set()
    if not isinstance(resolution, dict):
        return toks
    toks |= _content_tokens(str(resolution.get("prompt") or "").lower())
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    tr = soc.get("topic_revealed") if isinstance(soc.get("topic_revealed"), dict) else {}
    for key in ("title", "summary", "label", "topic_id"):
        toks |= _content_tokens(str(tr.get(key) or "").lower())
    return {t for t in toks if len(t) >= 4}


def _refinement_relevant_to_answer_pressure(
    resolution: Dict[str, Any] | None,
    refinement: str,
    *,
    enforced_source: str | None,
    enforced_lead_id: str | None,
    promoted_ids: List[str],
) -> bool:
    if not str(refinement or "").strip():
        return False
    res = resolution if isinstance(resolution, dict) else {}
    clue_id = str(res.get("clue_id") or "").strip()
    press = _topic_press_context_tokens(res)
    ref_toks = _content_tokens(str(refinement).lower())
    inter = press & ref_toks

    if str(enforced_source or "").strip() == "extracted_social":
        return True
    if clue_id and enforced_lead_id and clue_id == enforced_lead_id:
        return True
    if clue_id and clue_id in promoted_ids:
        return True
    if enforced_lead_id and enforced_lead_id in promoted_ids:
        return True
    if len(inter) >= 2:
        return True
    if len(inter) == 1 and len(ref_toks) <= 4:
        return True
    src = str(enforced_source or "").strip()
    if src in ("discoverable_clue", "exit", "author_exit"):
        return len(inter) >= 1
    if promoted_ids:
        return len(inter) >= 1
    return False


def _emitted_covers_refinement_spoken(emitted: str, refinement: str) -> bool:
    e = _normalize_text(emitted).lower()
    r = _normalize_text(refinement).lower()
    if not r:
        return True
    if r in e:
        return True
    rtoks = _content_tokens(r)
    etoks = _content_tokens(e)
    if not rtoks:
        return True
    hit = len(rtoks & etoks)
    need = min(2, len(rtoks))
    return hit >= need


def _repair_probe_for_answer_pressure_policy(
    gm_output: Dict[str, Any],
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Compatibility residue: canonical bundle read-side helper lives in ``game.response_policy_contracts``."""
    return materialize_response_policy_bundle(gm_output, session)


# Compatibility residue: older repair/gate imports may still use the earlier helper name.
def _gm_probe_for_answer_pressure_contracts(
    gm_output: Dict[str, Any],
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    return _repair_probe_for_answer_pressure_policy(gm_output, session)


def apply_spoken_state_refinement_cash_out(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """After state promotes a lead/clue, ensure spoken dialogue surfaces that refinement on answer-pressure turns.

    Downstream repair consumer only: use the canonical response-policy bundle reader from
    :mod:`game.response_policy_contracts`, which prefers shipped ``gm_output["response_policy"]``
    and falls back to ``session["last_turn_response_policy"]`` only as compatibility residue.
    """
    if not isinstance(gm_output, dict) or not isinstance(session, dict):
        return gm_output
    sid = str(scene_id or "").strip()
    if not sid:
        return gm_output
    if not strict_social_emission_will_apply(resolution, session, world, sid):
        return gm_output
    probe = materialize_response_policy_bundle(gm_output, session)
    if not (
        _strict_social_answer_pressure_ac_contract_active(probe)
        or _strict_social_answer_pressure_rd_contract_active(probe)
    ):
        return gm_output
    if not isinstance(resolution, dict):
        return gm_output

    emitted = str(gm_output.get("player_facing_text") or "")
    if not _normalize_text(emitted):
        return gm_output

    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    mal = meta.get("minimum_actionable_lead") if isinstance(meta.get("minimum_actionable_lead"), dict) else {}
    ll = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}

    enforced = bool(mal.get("minimum_actionable_lead_enforced"))
    enforced_id = str(mal.get("enforced_lead_id") or "").strip() or None
    enforced_src = str(mal.get("enforced_lead_source") or "").strip() or None

    promoted_raw = ll.get("authoritative_promoted_ids") or []
    promoted_ids = [str(x).strip() for x in promoted_raw if isinstance(x, str) and str(x).strip()]

    if not enforced and not promoted_ids:
        return gm_output

    refinement = ""
    source = ""

    if enforced and enforced_id:
        refinement = _refinement_phrase_for_lead_or_clue_id(session, enforced_id)
        source = enforced_src or "minimum_actionable_lead"

    if not refinement.strip() and promoted_ids:
        pick = None
        res_cid = str(resolution.get("clue_id") or "").strip()
        if res_cid and res_cid in promoted_ids:
            pick = res_cid
        else:
            pick = promoted_ids[0]
        refinement = _refinement_phrase_for_lead_or_clue_id(session, pick)
        source = "authoritative_promotion"

    refinement = _normalize_text(refinement).strip()
    if not refinement:
        return gm_output

    if not _refinement_relevant_to_answer_pressure(
        resolution,
        refinement,
        enforced_source=enforced_src,
        enforced_lead_id=enforced_id,
        promoted_ids=promoted_ids,
    ):
        return gm_output

    if _emitted_covers_refinement_spoken(emitted, refinement):
        return gm_output

    templates = (
        "I can only add this: {ref}.",
        "What I can say is: {ref}.",
        "I don't know more than this: {ref}.",
    )
    idx = len(refinement) % 3
    ref_clean = refinement.rstrip().rstrip(".")
    tail = templates[idx].format(ref=ref_clean)
    new_text = _normalize_text(emitted.rstrip() + " " + tail)
    out = dict(gm_output)
    out["player_facing_text"] = new_text
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (dbg + " | " if dbg else "") + f"spoken_state_refinement_cash_out:{source}"
    out["_spoken_refinement_cash_out"] = {
        "applied": True,
        "source": source,
        "refinement_preview": refinement[:160],
    }
    return out

def _skip_response_delta_layer(
    *,
    contract: Dict[str, Any] | None,
    emitted_text: str,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    if not isinstance(contract, dict):
        return "no_response_delta_contract"
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if bool(answer_completeness_meta.get("answer_completeness_failed")):
        return "answer_completeness_failed"
    if not strict_social_details:
        pass
    else:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
            return "strict_social_ownership_terminal_repair"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            if _strict_social_answer_pressure_rd_contract_active(gm_output):
                return None
            return "strict_social_structured_or_bridge_source"
    if not _contract_bool(contract, "enabled"):
        return "response_delta_disabled"
    if not _contract_bool(contract, "delta_required"):
        return "delta_not_required"
    prev = str(contract.get("previous_answer_snippet") or "").strip()
    if not prev or not _response_delta_snippet_substantive(prev):
        return "previous_answer_snippet_unavailable"
    allowed = [str(x) for x in (contract.get("allowed_delta_kinds") or []) if str(x).strip()]
    if not allowed:
        return "allowed_delta_kinds_empty"
    norm = _normalize_text(emitted_text)
    if not norm:
        return "empty_emitted_text"
    return None


def _repair_response_delta_minimal(
    text: str,
    _validation: Dict[str, Any],
    contract: Dict[str, Any],
) -> tuple[str | None, str | None]:
    """Reorder / trim existing sentences only; never invent facts."""
    prev = str(contract.get("previous_answer_snippet") or "").strip()
    prior_token_set = set(_response_delta_tokens(prev))
    allowed_list = [str(x).strip().lower() for x in (contract.get("allowed_delta_kinds") or []) if str(x).strip()]
    allowed = set(allowed_list)
    sentences = _split_sentences_answer_complete(text)
    if len(sentences) < 2:
        return None, None

    # 1) Front-load first later sentence that already carries a valid delta.
    for idx in range(1, len(sentences)):
        if _sentence_carries_response_delta(sentences[idx], prior_token_set, allowed=allowed):
            pick = sentences[idx]
            rest = sentences[:idx] + sentences[idx + 1 :]
            merged = _normalize_terminal_punctuation(pick) + " " + " ".join(
                _normalize_terminal_punctuation(s) for s in rest if s
            )
            candidate = _normalize_text(merged)
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "frontload_delta_sentence"

    # 2) Trim echoed opening when the remainder validates.
    open_ov = _response_delta_token_overlap_ratio(_response_delta_tokens(sentences[0]), list(prior_token_set))
    if open_ov >= 0.5 and not _opening_carries_allowed_delta(sentences[0], prior_token_set, allowed=allowed):
        tail = " ".join(_normalize_terminal_punctuation(s) for s in sentences[1:] if s)
        candidate = _normalize_text(tail)
        v2 = validate_response_delta(candidate, contract)
        if v2.get("passed"):
            return candidate, "trim_echo_opening"

    # 3) Prioritize refinement / delta sentence before uncertainty caveat (swap s0/s1).
    if len(sentences) >= 2:
        s0, s1 = sentences[0], sentences[1]
        if _partial_reason_in_text(s0, ["uncertainty", "lack_of_knowledge"]) and _sentence_carries_response_delta(
            s1, prior_token_set, allowed=allowed
        ):
            merged = _normalize_terminal_punctuation(s1) + " " + _normalize_terminal_punctuation(s0)
            candidate = _normalize_text(merged)
            rest = " ".join(_normalize_terminal_punctuation(s) for s in sentences[2:] if s)
            if rest:
                candidate = _normalize_text(candidate + " " + rest)
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "prioritize_refinement_before_caveat"

    # 4) Compress: drop duplicate partial opener + keep first delta sentence.
    if len(sentences) >= 2:
        dup_ov = _response_delta_token_overlap_ratio(
            _response_delta_tokens(sentences[0]),
            _response_delta_tokens(sentences[1]),
        )
        if dup_ov >= 0.72:
            trimmed = sentences[1:]
            candidate = _normalize_text(
                " ".join(_normalize_terminal_punctuation(s) for s in trimmed if s)
            )
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "drop_duplicate_partial_prefix"

    # 5) Compress echoed opener + substantive later line (two sentences -> delta first, opener shortened).
    if len(sentences) >= 2:
        for idx in range(1, len(sentences)):
            if not _sentence_carries_response_delta(sentences[idx], prior_token_set, allowed=allowed):
                continue
            delta_s = sentences[idx]
            head = sentences[0]
            rest = [s for i, s in enumerate(sentences) if i not in (0, idx)]
            merged = (
                _normalize_terminal_punctuation(delta_s)
                + " "
                + _normalize_terminal_punctuation(head)
                + (" " + " ".join(_normalize_terminal_punctuation(s) for s in rest if s) if rest else "")
            )
            candidate = _normalize_text(merged)
            v2 = validate_response_delta(candidate, contract)
            if v2.get("passed"):
                return candidate, "compress_echo_plus_delta"

    return None, None


def _apply_response_delta_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    contract = resolve_response_delta_contract(gm_output)
    meta = _default_response_delta_meta()
    trace = contract.get("trace") if isinstance(contract, dict) else None
    if isinstance(trace, dict):
        meta["response_delta_trigger_source"] = trace.get("trigger_source")
    if isinstance(contract, dict) and contract.get("trigger_source"):
        meta["response_delta_trigger_source"] = contract.get("trigger_source")

    skip = _skip_response_delta_layer(
        contract=contract if isinstance(contract, dict) else None,
        emitted_text=text,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        answer_completeness_meta=answer_completeness_meta,
        gm_output=gm_output,
    )
    meta["response_delta_skip_reason"] = skip
    if skip:
        return text, meta, []

    v0 = validate_response_delta(text, contract)
    meta["response_delta_checked"] = bool(v0.get("checked"))
    meta["response_delta_kind_detected"] = v0.get("delta_kind_detected")
    meta["response_delta_echo_overlap_ratio"] = v0.get("echo_overlap_ratio")
    if not v0.get("checked") or v0.get("passed"):
        return text, meta, []

    meta["response_delta_failed"] = True
    meta["response_delta_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired, mode = _repair_response_delta_minimal(text, v0, contract)
    if repaired:
        v1 = validate_response_delta(repaired, contract)
        if v1.get("passed"):
            meta["response_delta_repaired"] = True
            meta["response_delta_repair_mode"] = mode
            meta["response_delta_failed"] = False
            meta["response_delta_failure_reasons"] = []
            meta["response_delta_kind_detected"] = v1.get("delta_kind_detected")
            meta["response_delta_echo_overlap_ratio"] = v1.get("echo_overlap_ratio")
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("response_delta_unsatisfied_after_repair")
    meta["response_delta_failed"] = True
    return text, meta, extra


def _merge_response_delta_meta(meta: Dict[str, Any], rd_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "response_delta_checked": bool(rd_dbg.get("response_delta_checked")),
            "response_delta_failed": bool(rd_dbg.get("response_delta_failed")),
            "response_delta_failure_reasons": list(rd_dbg.get("response_delta_failure_reasons") or []),
            "response_delta_repaired": bool(rd_dbg.get("response_delta_repaired")),
            "response_delta_repair_mode": rd_dbg.get("response_delta_repair_mode"),
            "response_delta_kind_detected": rd_dbg.get("response_delta_kind_detected"),
            "response_delta_echo_overlap_ratio": rd_dbg.get("response_delta_echo_overlap_ratio"),
            "response_delta_skip_reason": rd_dbg.get("response_delta_skip_reason"),
            "response_delta_trigger_source": rd_dbg.get("response_delta_trigger_source"),
        }
    )


def _srs_word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z']+", str(text or "")))


def _flatten_list_like_dialogue(text: str) -> str:
    """Strip list/bullet/numbered prefixes and join lines into prose (no new list items)."""
    lines = [ln.strip() for ln in str(text or "").splitlines() if ln.strip()]
    if not lines:
        return _normalize_text(text or "")
    out: List[str] = []
    for ln in lines:
        s = ln
        s = re.sub(r"^\s*[\-\*•◦]\s+", "", s)
        s = re.sub(r"^\s*\d+[\.)]\s+", "", s)
        s = re.sub(r"^\s*[a-z]\)\s+", "", s, flags=re.IGNORECASE)
        if re.match(r"^.{6,120}:\s+\S", s):
            s = re.sub(r"^(.{6,120}):\s+", r"\1 — ", s, count=1)
        out.append(s.strip())
    return _normalize_text(" ".join(out))


def _collapse_multi_speaker_formatting(text: str) -> str:
    """Keep a single quoted reply body when multiple Name: \"...\" blocks appear."""
    pat = re.compile(
        r"(?:^|\n)\s*[A-Z][a-zA-Z]{1,18}\s*:\s*[\"“]([^\"”]{1,1200})[\"”]",
        re.MULTILINE,
    )
    matches = list(pat.finditer(str(text or "")))
    if len(matches) < 2:
        return text
    best = max((m.group(1).strip() for m in matches), key=len)
    return _normalize_text(best) if best else _normalize_text(text or "")


def _merge_substantive_paragraphs(text: str, *, target_max: int = 1) -> str:
    raw = str(text or "").strip()
    if not raw:
        return _normalize_text(text or "")
    parts = [p.strip() for p in re.split(r"\n\s*\n+", raw) if p.strip()]
    if len(parts) <= target_max:
        return text
    merged = " ".join(parts)
    return _normalize_text(merged)


def _trim_leading_expository_connectors(text: str, *, max_passes: int = 2) -> str:
    t = str(text or "").strip()
    if not t:
        return t
    for _ in range(max(1, max_passes)):
        stripped = False
        for pat in _EXPOSITORY_CONNECTOR_RES:
            m = pat.search(t)
            if m and m.start() < 40:
                t = (t[: m.start()] + t[m.end() :]).lstrip()
                t = re.sub(r"^[,:;\-\s]+", "", t)
                stripped = True
                break
        if not stripped:
            break
    return _normalize_text(t)


def _collapse_soft_line_breaks(text: str) -> str:
    """Turn single newlines into spaces; keeps blank-line paragraph boundaries."""
    t = str(text or "")
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)
    return _normalize_text(t)


def _reduce_expository_density(text: str, failure_reasons: List[str]) -> str:
    reasons = set(str(r) for r in failure_reasons if r)
    t = str(text or "")
    if "too_many_contiguous_expository_lines" in reasons:
        t = _collapse_soft_line_breaks(t)
    if "expository_monologue_density" in reasons:
        t = _trim_leading_expository_connectors(t, max_passes=3)
    return _normalize_text(t)


def _normalize_dialogue_cadence(text: str) -> str:
    t = _normalize_text(str(text or ""))
    if not t:
        return t
    sents = _split_sentences_answer_complete(t)
    if len(sents) == 1:
        body = sents[0]
        wc = _srs_word_count(body)
        if wc >= 50 and "; " in body:
            a, b = body.split("; ", 1)
            return _normalize_terminal_punctuation(
                _normalize_text(f"{a.strip()}. {b.strip()}")
            )
        if wc >= 55 and re.search(r",\s+and\s+", body):
            m = re.search(r",\s+and\s+", body)
            if m:
                a, b = body[: m.start()], body[m.end() :]
                return _normalize_terminal_punctuation(_normalize_text(f"{a.strip()}. {b.strip()}"))
        return t
    if len(sents) >= 4:
        merged_pairs: List[str] = []
        i = 0
        while i < len(sents):
            if i + 1 < len(sents) and _srs_word_count(sents[i]) < 14 and _srs_word_count(sents[i + 1]) < 14:
                merged_pairs.append(f"{sents[i].rstrip('.!?')} {sents[i + 1]}")
                i += 2
            else:
                merged_pairs.append(sents[i])
                i += 1
        if len(merged_pairs) < len(sents):
            return _normalize_text(" ".join(_normalize_terminal_punctuation(s) for s in merged_pairs if s))
    return t


def _restore_spoken_opening(text: str) -> str:
    """Prefer first-person spoken lead without changing factual content."""
    t = str(text or "").strip()
    if not t:
        return _normalize_text(t)
    head = t[:160].lower()
    if re.search(r"\b(i|i'?m|i'?ve|i'?ll|we|we'?re|we'?ve)\b", head):
        return _normalize_text(t)
    if re.search(r'[\"“]', t[:220]):
        return _normalize_text(t)
    if re.search(r"\byou\b", head):
        lead = "I'll say it plain: "
    else:
        lead = "Here's what I can tell you: "
    rest = t[0].lower() + t[1:] if len(t) > 1 else t
    return _normalize_terminal_punctuation(_normalize_text(lead + rest))


def apply_social_response_structure_repair(
    text: str,
    *,
    failure_reasons: List[str],
    gm_output: Dict[str, Any] | None = None,
) -> tuple[str, str | None]:
    """Structure-only repairs driven by :func:`validate_social_response_structure` failure codes."""
    reasons = [str(r) for r in (failure_reasons or []) if str(r).strip()]
    if not reasons:
        return text, None
    rset = set(reasons)
    t = str(text or "")
    modes: List[str] = []

    if "list_like_or_bulleted_dialogue" in rset:
        t2 = _flatten_list_like_dialogue(t)
        if t2 != _normalize_text(t):
            t = t2
            modes.append("flatten_list_like_dialogue")

    if "multi_speaker_turn_formatting" in rset:
        t2 = _collapse_multi_speaker_formatting(t)
        if t2 != t:
            t = t2
            modes.append("collapse_multi_speaker_formatting")

    if "too_many_dialogue_paragraphs_without_break" in rset:
        t2 = _merge_substantive_paragraphs(t, target_max=1)
        if t2 != t:
            t = t2
            modes.append("merge_dialogue_paragraphs")

    if "too_many_contiguous_expository_lines" in rset or "expository_monologue_density" in rset:
        t2 = _reduce_expository_density(t, reasons)
        if t2 != t:
            t = t2
            modes.append("reduce_expository_density")

    if "unnatural_monoblob_cadence" in rset or "heavy_expository_sentence_cadence" in rset:
        t2 = _normalize_dialogue_cadence(t)
        if t2 != t:
            t = t2
            modes.append("normalize_dialogue_cadence")

    if "missing_spoken_dialogue_shape" in rset:
        t2 = _restore_spoken_opening(t)
        if t2 != t:
            t = t2
            modes.append("restore_spoken_opening")

    t = _normalize_text(t)
    if not modes:
        return text, None
    return t, "+".join(modes)


def _default_social_response_structure_meta() -> Dict[str, Any]:
    return {
        "social_response_structure_checked": False,
        "social_response_structure_applicable": False,
        "social_response_structure_passed": True,
        "social_response_structure_failure_reasons": [],
        "social_response_structure_repair_applied": False,
        "social_response_structure_repair_changed_text": False,
        "social_response_structure_repair_passed": None,
        "social_response_structure_repair_mode": None,
        "social_response_structure_skip_reason": None,
        "social_response_structure_inspect": None,
    }


def _skip_social_response_structure_layer(
    *,
    emitted_text: str,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    """Orchestration skips only; applicability remains owned by the validator."""
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if bool(answer_completeness_meta.get("answer_completeness_failed")):
        return "answer_completeness_failed"
    if not _normalize_text(emitted_text or ""):
        return "empty_emitted_text"
    if strict_social_details:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
            return "strict_social_ownership_terminal_repair"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            if _strict_social_answer_pressure_rd_contract_active(gm_output):
                return None
            return "strict_social_structured_or_bridge_source"
    return None


def _apply_social_response_structure_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    """Dialogue-shape enforcement: depends on prior contracts (response type, answer completeness, delta).

    Runs before downstream policy layers so terminal fallbacks are not asked to preserve bad social form
    when a minimal structural repair can satisfy ``validate_social_response_structure``.
    """
    meta = _default_social_response_structure_meta()
    skip = _skip_social_response_structure_layer(
        emitted_text=text,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        answer_completeness_meta=answer_completeness_meta,
        gm_output=gm_output,
    )
    meta["social_response_structure_skip_reason"] = skip
    if skip:
        return text, meta, []

    v0 = validate_social_response_structure(text, None, gm_output=gm_output)
    meta["social_response_structure_checked"] = bool(v0.get("checked"))
    meta["social_response_structure_applicable"] = bool(v0.get("applicable"))
    meta["social_response_structure_passed"] = bool(v0.get("passed"))
    meta["social_response_structure_failure_reasons"] = list(v0.get("failure_reasons") or [])

    if not v0.get("checked") or not v0.get("applicable"):
        return text, meta, []

    if v0.get("passed"):
        return text, meta, []

    repaired, mode = apply_social_response_structure_repair(
        text,
        failure_reasons=list(v0.get("failure_reasons") or []),
        gm_output=gm_output,
    )
    changed = repaired != text and bool(_normalize_text(repaired) != _normalize_text(text))
    if repaired and mode:
        meta["social_response_structure_repair_applied"] = True
        meta["social_response_structure_repair_changed_text"] = changed
        meta["social_response_structure_repair_mode"] = mode

    v1 = validate_social_response_structure(repaired, None, gm_output=gm_output)
    meta["social_response_structure_repair_passed"] = bool(v1.get("passed"))
    if v1.get("passed"):
        meta["social_response_structure_passed"] = True
        meta["social_response_structure_failure_reasons"] = []
        return repaired, meta, []

    meta["social_response_structure_passed"] = False
    meta["social_response_structure_failure_reasons"] = list(v1.get("failure_reasons") or v0.get("failure_reasons") or [])
    meta["social_response_structure_inspect"] = inspect_social_response_structure(v1)
    extra: List[str] = []
    if not strict_social_path:
        extra.append("social_response_structure_unsatisfied_after_repair")
    return text, meta, extra


def _merge_social_response_structure_meta(meta: Dict[str, Any], srs_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "social_response_structure_checked": bool(srs_dbg.get("social_response_structure_checked")),
            "social_response_structure_applicable": bool(srs_dbg.get("social_response_structure_applicable")),
            "social_response_structure_passed": bool(srs_dbg.get("social_response_structure_passed")),
            "social_response_structure_failure_reasons": list(srs_dbg.get("social_response_structure_failure_reasons") or []),
            "social_response_structure_repair_applied": bool(srs_dbg.get("social_response_structure_repair_applied")),
            "social_response_structure_repair_changed_text": bool(srs_dbg.get("social_response_structure_repair_changed_text")),
            "social_response_structure_repair_passed": srs_dbg.get("social_response_structure_repair_passed"),
            "social_response_structure_repair_mode": srs_dbg.get("social_response_structure_repair_mode"),
            "social_response_structure_skip_reason": srs_dbg.get("social_response_structure_skip_reason"),
            "social_response_structure_inspect": srs_dbg.get("social_response_structure_inspect"),
        }
    )


def _default_narrative_authenticity_meta() -> Dict[str, Any]:
    """Compatibility residue wrapper derived from :mod:`game.final_emission_meta` defaults."""
    return default_narrative_authenticity_layer_meta()


def _merge_narrative_authenticity_meta(meta: Dict[str, Any], na_dbg: Dict[str, Any]) -> None:
    """Compatibility residue wrapper; metadata schema ownership stays in :mod:`game.final_emission_meta`."""
    merge_narrative_authenticity_into_final_emission_meta(meta, na_dbg)


def _skip_narrative_authenticity_layer(
    *,
    emitted_text: str,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    gm_output: Dict[str, Any] | None = None,
) -> str | None:
    if response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if not _normalize_text(emitted_text or ""):
        return "empty_emitted_text"
    if strict_social_details:
        if strict_social_details.get("used_internal_fallback"):
            return "strict_social_authoritative_internal_fallback"
        if response_type_debug.get("response_type_repair_kind") == "strict_social_dialogue_repair":
            return "strict_social_ownership_terminal_repair"
        fe = str(strict_social_details.get("final_emitted_source") or "")
        if fe in {"neutral_reply_speaker_grounding_bridge", "structured_fact_candidate_emission"}:
            return "strict_social_structured_or_bridge_source"
    if isinstance(gm_output, dict):
        tags = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
        tl = [str(t) for t in tags if isinstance(t, str)]
        if "question_retry_fallback" in tl and ("known_fact_guard" in tl or "social_answer_retry" in tl):
            return "deterministic_known_fact_retry_fallback"
    return None


def _apply_narrative_authenticity_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    strict_social_path: bool,
) -> tuple[str, Dict[str, Any], List[str]]:
    from game.narrative_authenticity import (
        repair_narrative_authenticity_minimal,
        resolve_narrative_authenticity_contract,
        validate_narrative_authenticity,
    )

    contract = resolve_narrative_authenticity_contract(gm_output)
    meta = _default_narrative_authenticity_meta()
    skip = _skip_narrative_authenticity_layer(
        emitted_text=text,
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug,
        gm_output=gm_output,
    )
    meta["narrative_authenticity_skip_reason"] = skip
    if skip:
        meta.update(
            build_narrative_authenticity_emission_trace(
                {"skip_reason": skip, "checked": False, "passed": True},
                contract=contract if isinstance(contract, dict) else None,
            )
        )
        return text, meta, []
    if not isinstance(contract, dict):
        meta["narrative_authenticity_skip_reason"] = "no_contract"
        meta.update(
            build_narrative_authenticity_emission_trace(
                {"skip_reason": "no_contract", "checked": False, "passed": True},
                contract=None,
            )
        )
        return text, meta, []

    v0 = validate_narrative_authenticity(text, contract, gm_output=gm_output)
    meta["narrative_authenticity_checked"] = bool(v0.get("checked"))
    if v0.get("skip_reason"):
        meta["narrative_authenticity_skip_reason"] = v0.get("skip_reason")
    if not v0.get("checked"):
        meta.update(build_narrative_authenticity_emission_trace(v0, contract=contract))
        return text, meta, []

    if v0.get("passed"):
        meta.update(
            build_narrative_authenticity_emission_trace(
                v0, contract=contract, repaired=False, repair_failed=False
            )
        )
        return text, meta, []

    meta["narrative_authenticity_failed"] = True
    meta["narrative_authenticity_failure_reasons"] = list(v0.get("failure_reasons") or [])
    meta.update(
        build_narrative_authenticity_emission_trace(v0, contract=contract, repaired=False, repair_failed=False)
    )

    repaired, mode = repair_narrative_authenticity_minimal(text, v0, contract, gm_output=gm_output)
    if repaired:
        v1 = validate_narrative_authenticity(repaired, contract, gm_output=gm_output)
        if v1.get("passed"):
            meta["narrative_authenticity_repaired"] = True
            meta["narrative_authenticity_repair_applied"] = True
            meta["narrative_authenticity_repair_mode"] = mode
            meta["narrative_authenticity_failed"] = False
            meta["narrative_authenticity_failure_reasons"] = []
            meta.update(
                build_narrative_authenticity_emission_trace(
                    v1, contract=contract, repaired=True, repair_mode=mode, repair_failed=False
                )
            )
            return repaired, meta, []

    extra: List[str] = []
    if not strict_social_path:
        extra.append("narrative_authenticity_unsatisfied_after_repair")
    meta["narrative_authenticity_failed"] = True
    meta.update(
        build_narrative_authenticity_emission_trace(v0, contract=contract, repaired=False, repair_failed=True)
    )
    return text, meta, extra


def _default_fallback_behavior_meta() -> Dict[str, Any]:
    return {
        "fallback_behavior_contract_present": False,
        "fallback_behavior_checked": False,
        "fallback_behavior_skip_reason": None,
        "fallback_behavior_uncertainty_active": False,
        "fallback_behavior_failed": False,
        "fallback_behavior_failure_reasons": [],
        "fallback_behavior_repaired": False,
        "fallback_behavior_repair_mode": "none",
        "fallback_behavior_clarifying_question_used": False,
        "fallback_behavior_partial_used": False,
        "fallback_behavior_known_edge_preserved": False,
        "fallback_behavior_unknown_edge_added": False,
        "fallback_behavior_next_lead_added": False,
        "fallback_behavior_meta_voice_stripped": False,
    }


def _merge_fallback_behavior_meta(meta: Dict[str, Any], fb_dbg: Dict[str, Any]) -> None:
    meta.update(
        {
            "fallback_behavior_contract_present": bool(fb_dbg.get("fallback_behavior_contract_present")),
            "fallback_behavior_checked": bool(fb_dbg.get("fallback_behavior_checked")),
            "fallback_behavior_skip_reason": fb_dbg.get("fallback_behavior_skip_reason"),
            "fallback_behavior_uncertainty_active": bool(fb_dbg.get("fallback_behavior_uncertainty_active")),
            "fallback_behavior_failed": bool(fb_dbg.get("fallback_behavior_failed")),
            "fallback_behavior_failure_reasons": list(fb_dbg.get("fallback_behavior_failure_reasons") or []),
            "fallback_behavior_repaired": bool(fb_dbg.get("fallback_behavior_repaired")),
            "fallback_behavior_repair_mode": fb_dbg.get("fallback_behavior_repair_mode"),
            "fallback_behavior_clarifying_question_used": bool(
                fb_dbg.get("fallback_behavior_clarifying_question_used")
            ),
            "fallback_behavior_partial_used": bool(fb_dbg.get("fallback_behavior_partial_used")),
            "fallback_behavior_known_edge_preserved": bool(
                fb_dbg.get("fallback_behavior_known_edge_preserved")
            ),
            "fallback_behavior_unknown_edge_added": bool(
                fb_dbg.get("fallback_behavior_unknown_edge_added")
            ),
            "fallback_behavior_next_lead_added": bool(fb_dbg.get("fallback_behavior_next_lead_added")),
            "fallback_behavior_meta_voice_stripped": bool(
                fb_dbg.get("fallback_behavior_meta_voice_stripped")
            ),
        }
    )


def _fallback_word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z']+", str(text or "")))


def _fallback_allowed_behaviors(contract: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(contract, dict):
        return {}
    allowed = contract.get("allowed_behaviors")
    return allowed if isinstance(allowed, dict) else {}


def _fallback_sentences(text: str) -> List[str]:
    return [s for s in _split_sentences_answer_complete(text) if str(s).strip()]


_FALLBACK_REPEATED_SUBJECT_RE = re.compile(
    r"^(?P<subject>(?:"
    r"[A-Z][\w'.-]+(?:\s+[A-Z][\w'.-]+){0,2}"
    r"|The\s+[A-Za-z][\w'.-]+(?:\s+[A-Za-z][\w'.-]+){0,2}"
    r"|A few\s+[A-Za-z][\w'.-]+(?:\s+[A-Za-z][\w'.-]+){0,2}"
    r"))\s+(?P<predicate>.+)$"
)


def _fallback_subject_predicate(sentence: str) -> Tuple[str, str] | None:
    trimmed = str(sentence or "").strip().rstrip(".!?")
    if not trimmed:
        return None
    match = _FALLBACK_REPEATED_SUBJECT_RE.match(trimmed)
    if not match:
        return None
    subject = _normalize_text(match.group("subject")).strip()
    predicate = _normalize_text(match.group("predicate")).strip(" ,;:-")
    if not subject or not predicate:
        return None
    return subject, predicate


def _fallback_merge_connector(predicate: str) -> str:
    low = str(predicate or "").strip().lower()
    if re.match(
        r"^(?:does not answer|do not answer|no one answers|none answer|holds (?:his|her|their) tongue|lets the question hang)\b",
        low,
    ):
        return "but"
    return "and"


def _merge_repeated_fallback_subject_pair(first: str, second: str) -> str | None:
    left = _fallback_subject_predicate(first)
    right = _fallback_subject_predicate(second)
    if not left or not right:
        return None
    subject1, predicate1 = left
    subject2, predicate2 = right
    if subject1.lower() != subject2.lower():
        return None
    if _fallback_word_count(first) > 12 or _fallback_word_count(second) > 12:
        return None
    if predicate1.lower() == predicate2.lower():
        return None
    connector = _fallback_merge_connector(predicate2)
    merged = f"{subject1} {predicate1}, {connector} {predicate2}" if connector == "but" else f"{subject1} {predicate1} and {predicate2}"
    return _normalize_terminal_punctuation(_normalize_text(merged))


def _smooth_repaired_fallback_line(text: str) -> str:
    t = _normalize_text(text)
    if not t:
        return t
    t = re.sub(
        r"\b(hesitates|pauses)\s+and\s+does not answer at once\b",
        r"\1, but does not answer at once",
        t,
        flags=re.IGNORECASE,
    )
    sentences = _fallback_sentences(t)
    if len(sentences) < 2:
        return _normalize_text(t)
    smoothed: List[str] = []
    idx = 0
    while idx < len(sentences):
        if idx + 1 < len(sentences):
            merged = _merge_repeated_fallback_subject_pair(sentences[idx], sentences[idx + 1])
            if merged:
                smoothed.append(merged)
                idx += 2
                continue
        smoothed.append(_normalize_terminal_punctuation(sentences[idx]))
        idx += 1
    return _normalize_text(" ".join(smoothed))


def _fallback_unique_join(parts: List[str]) -> str:
    deduped: List[str] = []
    seen: set[str] = set()
    for part in parts:
        norm = _normalize_text(part)
        if not norm:
            continue
        key = norm.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(_normalize_terminal_punctuation(norm))
    return _normalize_text(" ".join(deduped))


def _fallback_known_edge_sentence(text: str) -> str:
    for sentence in _fallback_sentences(text):
        if _concrete_payload_for_kinds(sentence, ["name", "place", "direction", "fact", "condition"]):
            return _normalize_terminal_punctuation(sentence)
    return ""


def _fallback_unknown_edge_sentence(text: str, contract: Dict[str, Any]) -> str:
    for sentence in _fallback_sentences(text):
        if _partial_reason_in_text(sentence, ["uncertainty", "lack_of_knowledge", "gated_information"]):
            return _normalize_terminal_punctuation(sentence)
        if _allowed_hedge_in_text(sentence, contract=contract):
            return _normalize_terminal_punctuation(sentence)
        if _contains_diegetic_uncertainty_partial(sentence):
            return _normalize_terminal_punctuation(sentence)
    return ""


def _fallback_next_lead_sentence(text: str) -> str:
    for sentence in _fallback_sentences(text):
        if _concrete_payload_for_kinds(sentence, ["next_lead"]) or _NEXT_LEAD_SNIPPET.search(sentence):
            return _normalize_terminal_punctuation(sentence)
    return ""


def _fallback_primary_source(contract: Dict[str, Any] | None) -> str:
    if not isinstance(contract, dict):
        return ""
    raw = contract.get("uncertainty_sources")
    if not isinstance(raw, list):
        return ""
    for item in raw:
        if isinstance(item, str) and item.strip():
            return item.strip().lower()
    return ""


def _social_npc_name(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(social.get("npc_name") or "").strip()


def _pick_place_hint(low: str) -> str:
    for w in ("checkpoint", "watchhouse", "dock", "market", "square", "gate", "barracks", "lane", "road", "pier"):
        if w in low:
            return w
    return "road"


def _synthesize_known_edge_phrase(
    contract: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    source_text: str,
) -> str:
    ctr = contract if isinstance(contract, dict) else {}
    source = _fallback_primary_source(ctr)
    prompt = _fallback_resolution_prompt(resolution)
    low = f"{source_text} {prompt}".lower()
    npc = _social_npc_name(resolution)
    place = _pick_place_hint(low)

    if npc:
        if source == "unknown_identity":
            return f"{npc} holds near the {place}, but offers no name you can pin down."
        if source == "unknown_location":
            return f"{npc} taps the map case, but nothing here marks the exact spot."
        if source == "unknown_motive":
            return f"{npc} keeps a flat look; motive does not show at the {place}."
        if source == "unknown_method":
            return f"{npc} shrugs; nothing in plain view here shows how it was done."
        if source == "unknown_quantity":
            return f"{npc} won't pin a count while the {place} churns."
        if source == "unknown_feasibility":
            return f"{npc} hesitates at the {place}, offering no clean yes or no."

    if source == "unknown_identity":
        return f"Noise along the {place} stays loud, but no face here offers a name you can use."
    if source == "unknown_location":
        return f"The {place} stays busy; nothing in sight pins the exact spot."
    if source == "unknown_motive":
        return f"The {place} crowd keeps its counsel; the why of it stays off the tongue."
    if source == "unknown_method":
        return "Tracks and tools look ordinary; nothing in plain view shows how it was done."
    if source == "unknown_quantity":
        return "Headcounts shift with the crowd; no clean tally presents itself here."
    return f"The {place} noise holds; nothing in view settles the question."


def _npc_attribution_for_diegetic_lead(resolution: Dict[str, Any] | None) -> str:
    """Short attribution for synthesized fallback leads (diegetic, not omniscient narrator imperatives)."""
    npc = _social_npc_name(resolution)
    if npc:
        return npc
    subj = _fallback_scene_subject(resolution, "")
    if subj:
        return subj
    return "They"


def _diegetic_next_lead_from_template(inner_quote: str, resolution: Dict[str, Any] | None, verb: str = "says") -> str:
    inner = str(inner_quote or "").strip().rstrip(".!?")
    if not inner:
        return ""
    npc = _npc_attribution_for_diegetic_lead(resolution)
    v = str(verb or "says").strip().lower()
    low_att = npc.strip().lower()
    if low_att in ("they", "them"):
        # Avoid bare "they" attribution (referential-clarity gate flags ambiguous entity references).
        if v == "mutters":
            return f'"{inner}," someone nearby mutters.'
        if v == "adds":
            return f'"{inner}," a lean voice adds.'
        if v == "shrugs":
            return f'"{inner}," someone nearby says with a shrug.'
        return f'"{inner}," someone nearby says.'
    if v in ("mutters", "adds", "shrugs"):
        return f'"{inner}," {npc} {v}.'
    return f'"{inner}," {npc} says.'


def _synthesize_next_lead_phrase(
    contract: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
    source_text: str,
    *,
    variant: int = 0,
) -> str:
    """Diegetic next-step hints voiced as NPC speech (never bare second-person planner imperatives)."""
    ctr = contract if isinstance(contract, dict) else {}
    source = _fallback_primary_source(ctr)
    prompt = _fallback_resolution_prompt(resolution)
    low = f"{source_text} {prompt}".lower()
    v = max(0, int(variant)) % 3

    if "dock" in low or "harbor" in low:
        opts = (
            "If you need which berth was logged last watch, the harbor clerk keeps that—not me.",
            "Word on the water is the harbor clerk's ledger names berths; I don't keep it in my head.",
            "They say the harbor clerk can tell you what was logged last watch—I wouldn't swear to it.",
        )
        return _diegetic_next_lead_from_template(opts[v], resolution, "mutters")

    if source == "unknown_motive":
        opts = (
            "If it's a grudge worth hiding on paper, the duty sergeant hears more of that than I do.",
            "Rumors point at bad blood, but the duty sergeant's the one who sees it written down.",
            "I can't pin a motive from here—the duty sergeant might, if anyone does.",
        )
        return _diegetic_next_lead_from_template(opts[v], resolution)

    if source == "unknown_method":
        opts = (
            "Who was on scene is on the watch roster by the gate—if it's written anywhere, it's there.",
            "I've heard they post who's on roster by the gate; that's the closest thing to a witness list.",
            "If you need names tied to the shift, the gate roster is what people actually read.",
        )
        return _diegetic_next_lead_from_template(opts[v], resolution, "adds")

    if source == "unknown_quantity":
        opts = (
            "A hard count lives in the quartermaster's tally—if you need numbers, that's the paper people mean.",
            "I've heard the quartermaster's clerk keeps the tally sheet; I won't pretend I memorized it.",
            "If you want a clean tally, folks say the quartermaster's clerk is the one who holds it.",
        )
        return _diegetic_next_lead_from_template(opts[v], resolution)

    if source == "unknown_feasibility":
        opts = (
            "What the watch will actually allow on the street—that's the patrol sergeant's say, not mine.",
            "If you want the rule on what's allowed out here, the patrol sergeant posts it in practice.",
            "I won't promise what's permitted—the patrol sergeant is the one who enforces it.",
        )
        return _diegetic_next_lead_from_template(opts[v], resolution, "mutters")

    opts = (
        "If you need a name off the watch side, the duty sergeant or the gate roster is where people look.",
        "Rumor runs through the sergeants and the posted rosters—I'm not your clerk.",
        "I've heard answers get pinned down at the duty desk or on the roster sheet by the gate.",
    )
    return _diegetic_next_lead_from_template(opts[v], resolution)


def _fallback_resolution_prompt(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    return _normalize_text(str(resolution.get("prompt") or ""))


def _fallback_scene_subject(resolution: Dict[str, Any] | None, source_text: str) -> str:
    social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    npc_name = str(social.get("npc_name") or "").strip()
    if npc_name:
        return npc_name
    low = f"{source_text} {_fallback_resolution_prompt(resolution)}".lower()
    if not re.search(r"\b(?:ask|offer|talk|speak|answer|runner|guard|captain|crowd|bystander)\b", low):
        return ""
    if "runner" in low:
        return "The runner"
    if "captain" in low:
        return "The captain"
    if "guard" in low:
        return "The guard"
    return ""


def _looks_like_open_call_turn(resolution: Dict[str, Any] | None, source_text: str) -> bool:
    social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    social_intent = str(social.get("social_intent_class") or "").strip().lower()
    low = f"{source_text} {_fallback_resolution_prompt(resolution)}".lower()
    if social_intent == "open_call":
        return True
    return bool(
        re.search(
            r"\b(?:anyone willing to talk|anybody willing to talk|bystanders?|crowd|call out|calls out|who'll talk|who will talk)\b",
            low,
        )
    )


def _rewrite_meta_fallback_as_diegetic_partial(
    source_text: str,
    *,
    contract: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
) -> str:
    source = _fallback_primary_source(contract)
    prompt = _fallback_resolution_prompt(resolution)
    low = f"{source_text} {prompt}".lower()
    subject = _fallback_scene_subject(resolution, source_text)
    open_call = _looks_like_open_call_turn(resolution, source_text)
    coin_word = "copper" if "copper" in low else "silver" if "silver" in low else "coin" if "coin" in low else ""

    if open_call:
        if coin_word:
            return f"A few heads turn toward the {coin_word}, but no one answers at once."
        return "A few bystanders glance over, but no one answers at once."

    if subject:
        if coin_word:
            return f"{subject} eyes the {coin_word} but does not answer at once."
        if source == "unknown_feasibility" or re.search(r"\b(?:safe|safely|bribe|rush|force|work|can i|could i|would it)\b", low):
            if re.search(r"\b(?:gate|checkpoint|choke point|crowd|patrol|watch)\b", low):
                return f"{subject} keeps attention on the choke point and gives you nothing yet."
            return f"{subject} does not answer at once."
        if re.search(r"\b(?:gate|checkpoint|crowd|patrol|watch)\b", low):
            return f"{subject} starts to answer, then glances past you toward the gate."
        if source == "unknown_motive":
            return f"{subject} gives you nothing but a guarded look."
        return f"{subject} hesitates, but does not answer at once."

    if source == "unknown_location":
        return "Nothing in sight pins the place down."
    if source == "unknown_motive":
        return "They give nothing away about why."
    if source == "unknown_method":
        return "Nothing in plain view shows how it was done."
    if source == "unknown_quantity":
        return "No clean count shows."
    if source == "unknown_feasibility":
        return "No one commits themselves at once."
    if source == "unknown_identity":
        return _fallback_unique_join(
            [
                _synthesize_known_edge_phrase(contract, resolution, source_text=source_text),
                "That name stays unclear; hearsay will not pin anyone yet.",
            ]
        )
    return "The moment yields no answer at once."


def _fallback_unknown_edge_phrase(
    contract: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None = None,
    source_text: str = "",
) -> str:
    mode = str((contract or {}).get("uncertainty_mode") or "").strip().lower()
    source = _fallback_primary_source(contract)
    if source == "unknown_identity":
        return "I don't know the name." if mode == "npc_ignorance" else (
            "That name stays unclear; hearsay will not pin anyone yet."
        )
    if source == "unknown_location":
        return "I don't know where they went." if mode == "npc_ignorance" else "Nothing in sight pins the place down."
    if source == "unknown_motive":
        return "I don't know why." if mode == "npc_ignorance" else _rewrite_meta_fallback_as_diegetic_partial(
            source_text,
            contract=contract,
            resolution=resolution,
        )
    if source == "unknown_method":
        return "I don't know how it was done." if mode == "npc_ignorance" else "Nothing in plain view shows how it was done."
    if source == "unknown_quantity":
        return "I don't know the count." if mode == "npc_ignorance" else "No clean count presents itself."
    if source == "unknown_feasibility" or mode == "procedural_insufficiency":
        return _rewrite_meta_fallback_as_diegetic_partial(source_text, contract=contract, resolution=resolution)
    if mode == "npc_ignorance":
        return "I don't know that part."
    return _rewrite_meta_fallback_as_diegetic_partial(source_text, contract=contract, resolution=resolution)


def _fallback_clarifying_question(contract: Dict[str, Any] | None) -> str:
    source = _fallback_primary_source(contract)
    if source == "unknown_identity":
        return "Which one do you mean?"
    if source == "unknown_location":
        return "Which place are you asking about?"
    if source == "unknown_motive":
        return "Whose motive are you asking after?"
    if source == "unknown_method":
        return "Which part are you pressing on?"
    if source == "unknown_quantity":
        return "Which count are you asking for?"
    if source == "unknown_feasibility":
        return "Which move are you weighing?"
    return "Which part do you want pinned down?"


def _strip_patterns_from_text(
    text: str,
    *,
    patterns: Tuple[re.Pattern[str], ...],
) -> str:
    out: List[str] = []
    for sentence in _fallback_sentences(text):
        candidate = sentence
        for pattern in patterns:
            candidate = pattern.sub("", candidate)
        candidate = re.sub(r"\s+", " ", candidate).strip(" ,;:-")
        candidate = re.sub(r"\s+([,.!?;:])", r"\1", candidate).strip()
        if _fallback_word_count(candidate) >= 2:
            out.append(_normalize_terminal_punctuation(candidate))
    return _normalize_text(" ".join(out))


def _sentence_matches_overcertain_source(sentence: str, contract: Dict[str, Any]) -> bool:
    if any(p.search(sentence) for p in _FALLBACK_OVERCERTAIN_GENERAL_PATTERNS):
        return True
    for source in [
        str(item).strip().lower()
        for item in (contract.get("uncertainty_sources") or [])
        if isinstance(item, str) and str(item).strip()
    ]:
        if any(p.search(sentence) for p in _FALLBACK_OVERCERTAIN_BY_SOURCE.get(source, ())):
            return True
    return False


def _strip_meta_fallback_voice(text: str, *, contract: Dict[str, Any] | None = None) -> str:
    cleaned = _strip_patterns_from_text(text, patterns=_FALLBACK_META_VOICE_PATTERNS)
    forbidden = [
        re.compile(re.escape(str(item).strip()), re.IGNORECASE)
        for item in ((contract or {}).get("forbidden_hedge_forms") or [])
        if isinstance(item, str) and str(item).strip()
    ]
    if forbidden:
        cleaned = _strip_patterns_from_text(cleaned or text, patterns=tuple(forbidden))
    return cleaned


def _remove_fabricated_authority(text: str, *, contract: Dict[str, Any] | None = None) -> str:
    _ = contract
    return _strip_patterns_from_text(text, patterns=_FALLBACK_FABRICATED_AUTHORITY_PATTERNS)


def _downgrade_overcertain_claims(text: str, *, contract: Dict[str, Any] | None = None) -> str:
    ctr = contract if isinstance(contract, dict) else {}
    kept: List[str] = []
    for sentence in _fallback_sentences(text):
        if not _sentence_matches_overcertain_source(sentence, ctr):
            kept.append(_normalize_terminal_punctuation(sentence))
            continue
        trimmed = sentence
        for pattern in _FALLBACK_OVERCERTAIN_GENERAL_PATTERNS:
            trimmed = pattern.sub("", trimmed)
        trimmed = re.sub(r"\bdefinitely\b", "", trimmed, flags=re.IGNORECASE)
        trimmed = re.sub(r"\s+", " ", trimmed).strip(" ,;:-")
        trimmed = re.sub(r"\s+([,.!?;:])", r"\1", trimmed).strip()
        if _concrete_payload_for_kinds(trimmed, ["next_lead"]) and _fallback_word_count(trimmed) >= 3:
            kept.append(_normalize_terminal_punctuation(trimmed))
            continue
        if (
            _concrete_payload_for_kinds(trimmed, ["name", "place", "direction", "fact", "condition"])
            and not _sentence_matches_overcertain_source(trimmed, ctr)
            and _fallback_word_count(trimmed) >= 3
        ):
            kept.append(_normalize_terminal_punctuation(trimmed))
    return _normalize_text(" ".join(kept))


def _ensure_known_unknown_shape(
    text: str,
    *,
    contract: Dict[str, Any] | None,
    validation: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None = None,
) -> Tuple[str, Dict[str, Any]]:
    _ = validation
    ctr = contract if isinstance(contract, dict) else {}
    patch: Dict[str, Any] = {}
    sentences = _fallback_sentences(text)
    known = _fallback_known_edge_sentence(text)
    unknown = _fallback_unknown_edge_sentence(text, ctr)
    if unknown and _bounded_partial_thin_substance_violation(unknown):
        unknown = ""

    pieces: List[str] = []

    if known:
        pieces.append(known)
        patch["fallback_behavior_known_edge_preserved"] = True
    elif _contract_bool(ctr, "require_partial_to_state_known_edge"):
        synth_ke = _synthesize_known_edge_phrase(ctr, resolution, source_text=text)
        if synth_ke:
            pieces.append(synth_ke)
            patch["fallback_behavior_known_edge_synthesized"] = True
    elif sentences:
        pieces.append(_normalize_terminal_punctuation(sentences[0]))

    if _contract_bool(ctr, "require_partial_to_state_unknown_edge"):
        if unknown:
            pieces.append(unknown)
        else:
            pieces.append(_fallback_unknown_edge_phrase(ctr, resolution=resolution, source_text=text))
            patch["fallback_behavior_unknown_edge_added"] = True
    elif unknown:
        pieces.append(unknown)

    if not pieces:
        pieces.append(_fallback_unknown_edge_phrase(ctr, resolution=resolution, source_text=text))
        patch["fallback_behavior_unknown_edge_added"] = True

    return _fallback_unique_join(pieces), patch


def _topic_fingerprint_for_fallback(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "none"
    p = _normalize_text(str(resolution.get("prompt") or ""))[:140]
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    na = meta.get("normalized_action") if isinstance(meta.get("normalized_action"), dict) else {}
    extra = _normalize_text(str(na.get("kind") or na.get("action_kind") or ""))[:40]
    return f"{p}|{extra}"


def _fallback_lead_state_key(scene_id: str, resolution: Dict[str, Any] | None) -> str:
    soc = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    npc_id = str(soc.get("npc_id") or "").strip() or "none"
    sid = str(scene_id or "").strip() or "none"
    return f"{sid}|{npc_id}|{_topic_fingerprint_for_fallback(resolution if isinstance(resolution, dict) else None)}"


def _get_lead_tail_record(session: Dict[str, Any] | None, key: str) -> Dict[str, Any]:
    if not isinstance(session, dict):
        return {}
    root = session.setdefault("_social_fallback_lead_tail_state", {})
    if not isinstance(root, dict):
        root = {}
        session["_social_fallback_lead_tail_state"] = root
    ent = root.get(key)
    if not isinstance(ent, dict):
        ent = {"last_tail": "", "streak": 0}
        root[key] = ent
    return ent


def _fallback_lead_tail_should_block(
    session: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
    proposed: str,
) -> bool:
    if not isinstance(session, dict) or not str(proposed or "").strip():
        return False
    key = _fallback_lead_state_key(scene_id, resolution)
    ent = _get_lead_tail_record(session, key)
    norm = _normalize_text(proposed).lower()
    last = str(ent.get("last_tail") or "").lower()
    streak = int(ent.get("streak") or 0)
    return norm == last and streak >= 2


def _record_fallback_lead_tail(
    session: Dict[str, Any] | None,
    scene_id: str,
    resolution: Dict[str, Any] | None,
    emitted: str,
) -> None:
    if not isinstance(session, dict) or not str(emitted or "").strip():
        return
    key = _fallback_lead_state_key(scene_id, resolution)
    ent = _get_lead_tail_record(session, key)
    norm = _normalize_text(emitted).lower()
    last = str(ent.get("last_tail") or "").lower()
    if norm == last:
        ent["streak"] = int(ent.get("streak") or 0) + 1
    else:
        ent["streak"] = 1
    ent["last_tail"] = norm


_BARE_IMP_LEAD_RE = re.compile(r"^(?:Press|Ask|Check|Consider)\b", re.IGNORECASE)


def _is_bare_imperative_lead_sentence(sentence: str) -> bool:
    t = str(sentence or "").strip()
    if not t or t.startswith('"'):
        return False
    return bool(_BARE_IMP_LEAD_RE.match(t)) and (
        _concrete_payload_for_kinds(t, ["next_lead"]) or _NEXT_LEAD_SNIPPET.search(t) is not None
    )


def _wrap_bare_imperative_lead_for_npc_voice(sentence: str, resolution: Dict[str, Any] | None) -> str:
    inner = str(sentence or "").strip().rstrip(".!?")
    npc = _npc_attribution_for_diegetic_lead(resolution)
    if npc.strip().lower() in ("they", "them"):
        return f'"{inner}," someone nearby says.'
    return f'"{inner}," {npc} says.'


def _voice_extracted_next_lead_sentence(sentence: str, resolution: Dict[str, Any] | None) -> str:
    s = str(sentence or "").strip()
    if not s:
        return ""
    if _is_bare_imperative_lead_sentence(s):
        return _wrap_bare_imperative_lead_for_npc_voice(s, resolution)
    return s


def _apply_social_fallback_leak_guard(text: str, resolution: Dict[str, Any] | None) -> str:
    """Convert bare imperative planner tails in NPC-facing fallback to diegetic quoted speech."""
    if not isinstance(resolution, dict):
        return text
    social = resolution.get("social")
    if not isinstance(social, dict) or not str(social.get("npc_id") or "").strip():
        return text
    parts: List[str] = []
    for sent in _fallback_sentences(text):
        if _is_bare_imperative_lead_sentence(sent):
            parts.append(_wrap_bare_imperative_lead_for_npc_voice(sent, resolution))
        else:
            parts.append(sent)
    return _normalize_text(" ".join(parts))


def _append_next_lead_if_allowed(
    text: str,
    *,
    contract: Dict[str, Any] | None,
    source_text: str,
    resolution: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> Tuple[str, Dict[str, Any]]:
    ctr = contract if isinstance(contract, dict) else {}
    patch: Dict[str, Any] = {}
    if not _contract_bool(ctr, "require_partial_to_offer_next_lead"):
        return text, patch
    existing = _fallback_next_lead_sentence(text)
    if existing:
        return text, patch
    lead = _fallback_next_lead_sentence(source_text)
    if lead:
        lead = _voice_extracted_next_lead_sentence(lead, resolution)
    if not lead:
        for variant in range(3):
            cand = _synthesize_next_lead_phrase(ctr, resolution, source_text, variant=variant)
            if not cand:
                continue
            if _fallback_lead_tail_should_block(session, scene_id, resolution, cand):
                continue
            lead = cand
            break
    if not lead:
        return text, patch
    if _fallback_lead_tail_should_block(session, scene_id, resolution, lead):
        patch["fallback_behavior_next_lead_suppressed_repeat"] = True
        return text, patch
    patch["fallback_behavior_next_lead_added"] = True
    joined = _fallback_unique_join([text, lead])
    _record_fallback_lead_tail(session, scene_id, resolution, lead)
    return joined, patch


def _convert_to_single_diegetic_clarifying_question(contract: Dict[str, Any] | None) -> str:
    return _normalize_terminal_punctuation(_fallback_clarifying_question(contract))


def repair_fallback_behavior(
    emitted_text: str,
    contract: Dict[str, Any] | None,
    validation: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None = None,
    strict_social_path: bool = False,
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> Tuple[str, Dict[str, Any], List[str]]:
    _ = strict_social_path
    meta = _default_fallback_behavior_meta()
    ctr = contract if isinstance(contract, dict) else {}
    val = validation if isinstance(validation, dict) else {}
    original = _normalize_text(emitted_text)
    working = original
    modes: List[str] = []
    failure_reasons = {
        str(item).strip()
        for item in (val.get("failure_reasons") or [])
        if isinstance(item, str) and str(item).strip()
    }

    if val.get("meta_fallback_voice_detected"):
        stripped = _strip_meta_fallback_voice(working, contract=ctr)
        if _normalize_text(stripped) != _normalize_text(working):
            working = stripped
            meta["fallback_behavior_meta_voice_stripped"] = True
            modes.append("strip_meta_voice")
        if not _contains_diegetic_uncertainty_partial(working, resolution=resolution):
            diegetic = _rewrite_meta_fallback_as_diegetic_partial(original or working, contract=ctr, resolution=resolution)
            if diegetic:
                nl_raw = _fallback_next_lead_sentence(working or original)
                nl_voice = _voice_extracted_next_lead_sentence(nl_raw, resolution) if nl_raw else ""
                working = _fallback_unique_join(
                    [
                        diegetic,
                        _fallback_known_edge_sentence(working),
                        nl_voice,
                    ]
                )
                meta["fallback_behavior_meta_voice_stripped"] = True
                modes.append("rewrite_meta_as_diegetic_partial")

    if val.get("fabricated_authority_detected"):
        stripped = _remove_fabricated_authority(working, contract=ctr)
        if _normalize_text(stripped) != _normalize_text(working):
            working = stripped
            modes.append("remove_fabricated_authority")

    if val.get("invented_certainty_detected"):
        stripped = _downgrade_overcertain_claims(working, contract=ctr)
        if _normalize_text(stripped) != _normalize_text(working):
            working = stripped
            modes.append("downgrade_invented_certainty")

    allowed = _fallback_allowed_behaviors(ctr)
    partial_allowed = bool(allowed.get("provide_partial_information"))
    question_allowed = bool(allowed.get("ask_clarifying_question"))
    prefer_partial = bool(ctr.get("prefer_partial_over_question"))
    max_questions = ctr.get("max_clarifying_questions")
    can_question = question_allowed and isinstance(max_questions, int) and max_questions > 0
    preserve_partial = bool(
        _fallback_known_edge_sentence(working)
        or _fallback_next_lead_sentence(working)
        or _fallback_unknown_edge_sentence(working, ctr)
    )
    need_shape = bool(
        failure_reasons
        & {
            "missing_allowed_fallback_shape",
            "question_used_when_partial_preferred",
            "too_many_clarifying_questions",
            "invented_certainty",
            "fabricated_authority",
            "meta_fallback_voice",
            "bounded_partial_insufficient_substance",
        }
    )

    if need_shape and partial_allowed and (prefer_partial or preserve_partial or not can_question):
        shaped, patch = _ensure_known_unknown_shape(
            working or original,
            contract=ctr,
            validation=val,
            resolution=resolution,
        )
        working, patch2 = _append_next_lead_if_allowed(
            shaped,
            contract=ctr,
            source_text=working or original,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
        )
        meta.update(patch)
        meta.update(patch2)
        meta["fallback_behavior_partial_used"] = True
        modes.append("bounded_partial")
    elif need_shape and can_question:
        working = _convert_to_single_diegetic_clarifying_question(ctr)
        meta["fallback_behavior_clarifying_question_used"] = True
        modes.append("clarifying_question")
    elif not working and partial_allowed:
        shaped_empty, patch = _ensure_known_unknown_shape(
            original,
            contract=ctr,
            validation=val,
            resolution=resolution,
        )
        working, patch2 = _append_next_lead_if_allowed(
            shaped_empty,
            contract=ctr,
            source_text=original,
            resolution=resolution,
            session=session,
            scene_id=scene_id,
        )
        meta.update(patch)
        meta.update(patch2)
        meta["fallback_behavior_partial_used"] = True
        modes.append("bounded_partial")

    final_text = _normalize_text(working or original)
    if modes:
        final_text = _smooth_repaired_fallback_line(final_text)
    final_text = _apply_social_fallback_leak_guard(final_text, resolution)
    if _looks_like_single_clarifying_question(final_text):
        meta["fallback_behavior_clarifying_question_used"] = True
    if not meta["fallback_behavior_partial_used"] and not meta["fallback_behavior_clarifying_question_used"]:
        partial_shape = _normalize_text(final_text) != _normalize_text(original) and bool(
            _fallback_known_edge_sentence(final_text) or _fallback_unknown_edge_sentence(final_text, ctr)
        )
        if partial_shape:
            meta["fallback_behavior_partial_used"] = True

    if _normalize_text(final_text) != _normalize_text(original):
        meta["fallback_behavior_repaired"] = True
    if modes:
        meta["fallback_behavior_repair_mode"] = "+".join(dict.fromkeys(modes))
    return final_text, meta, []


def _apply_fallback_behavior_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_path: bool,
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> Tuple[str, Dict[str, Any], List[str]]:
    contract = resolve_fallback_behavior_contract(gm_output)
    meta = _default_fallback_behavior_meta()
    meta["fallback_behavior_contract_present"] = isinstance(contract, dict)

    tags = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
    tag_set = {str(t) for t in tags if isinstance(t, str)}
    if "known_fact_guard" in tag_set and "question_retry_fallback" in tag_set:
        meta["fallback_behavior_skip_reason"] = "deterministic_known_fact_retry_answer"
        return text, meta, []

    v0 = validate_fallback_behavior(text, contract, resolution=resolution)
    meta["fallback_behavior_checked"] = bool(v0.get("checked"))
    meta["fallback_behavior_skip_reason"] = v0.get("skip_reason")
    meta["fallback_behavior_uncertainty_active"] = bool(v0.get("uncertainty_active"))
    if not v0.get("checked"):
        return text, meta, []
    if v0.get("passed"):
        return text, meta, []

    meta["fallback_behavior_failed"] = True
    meta["fallback_behavior_failure_reasons"] = list(v0.get("failure_reasons") or [])

    repaired_text, repair_meta, _ = repair_fallback_behavior(
        text,
        contract,
        v0,
        resolution=resolution,
        strict_social_path=strict_social_path,
        session=session,
        scene_id=scene_id,
    )
    _merge_fallback_behavior_meta(meta, repair_meta)

    candidate = repaired_text if _normalize_text(repaired_text) else text
    v1 = validate_fallback_behavior(candidate, contract, resolution=resolution)
    meta["fallback_behavior_checked"] = bool(v1.get("checked"))
    meta["fallback_behavior_skip_reason"] = v1.get("skip_reason")
    meta["fallback_behavior_uncertainty_active"] = bool(v1.get("uncertainty_active"))
    if v1.get("passed"):
        meta["fallback_behavior_failed"] = False
        meta["fallback_behavior_failure_reasons"] = []
        return candidate, meta, []

    meta["fallback_behavior_failed"] = bool(v1.get("checked") and not v1.get("passed"))
    meta["fallback_behavior_failure_reasons"] = list(v1.get("failure_reasons") or v0.get("failure_reasons") or [])
    if _normalize_text(candidate) != _normalize_text(text):
        return candidate, meta, []
    extra: List[str] = []
    if not strict_social_path:
        extra.append("fallback_behavior_unsatisfied_after_repair")
    return text, meta, extra
