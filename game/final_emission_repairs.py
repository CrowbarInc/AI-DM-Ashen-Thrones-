"""Repair and layer wiring for final emission: ``apply_*`` / ``merge_*`` / skip helpers.

Owns skip/repair orchestration for the ``response_policy`` answer-completeness and
response-delta layers (extracted from :mod:`game.final_emission_gate`). Validators live in
:mod:`game.final_emission_validators`; the gate imports these symbols and may re-expose them
for compatibility.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.final_emission_text import (
    _capitalize_sentence_fragment,
    _normalize_terminal_punctuation,
    _normalize_text,
)
from game.final_emission_validators import (
    _concrete_payload_for_kinds,
    _content_tokens,
    _contract_bool,
    _NEXT_LEAD_SNIPPET,
    _opening_carries_allowed_delta,
    _opening_segment,
    _partial_reason_in_text,
    _resolve_answer_completeness_contract,
    _resolve_response_delta_contract,
    _response_delta_snippet_substantive,
    _response_delta_token_overlap_ratio,
    _response_delta_tokens,
    _sentence_carries_response_delta,
    _sentence_substantive_for_frontload,
    _split_sentences_answer_complete,
    validate_answer_completeness,
    validate_response_delta,
)
from game.leads import get_lead, normalize_lead
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
    contract = _resolve_answer_completeness_contract(gm_output)
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
    ac = _resolve_answer_completeness_contract(gm_output)
    if not isinstance(ac, dict):
        return False
    if not _contract_bool(ac, "enabled") or not _contract_bool(ac, "answer_required"):
        return False
    trace = ac.get("trace") if isinstance(ac.get("trace"), dict) else {}
    return bool(trace.get("strict_social_answer_seek_override"))


def _strict_social_answer_pressure_rd_contract_active(gm_output: Dict[str, Any] | None) -> bool:
    """True when response_delta is enabled with strict_social_answer_pressure trigger (Block 1)."""
    rd = _resolve_response_delta_contract(gm_output)
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


def _gm_probe_for_answer_pressure_contracts(
    gm_output: Dict[str, Any],
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Merge ``session["last_turn_response_policy"]`` when ``gm_output`` lacks a non-empty ``response_policy``.

    The narration pipeline stores the shipped bundle on the session; retry helpers also receive
    ``response_policy`` explicitly. :func:`apply_final_emission_gate` uses this so layered contract
    resolution (context separation, tone escalation, etc.) matches the shipped bundle on fallback paths.
    """
    pol = gm_output.get("response_policy") if isinstance(gm_output.get("response_policy"), dict) else None
    if isinstance(pol, dict) and pol:
        return gm_output
    if isinstance(session, dict):
        lp = session.get("last_turn_response_policy")
        if isinstance(lp, dict) and lp:
            merged = dict(gm_output)
            merged["response_policy"] = lp
            return merged
    return gm_output


def apply_spoken_state_refinement_cash_out(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """After state promotes a lead/clue, ensure spoken dialogue surfaces that refinement on answer-pressure turns.

    Uses ``response_policy`` on ``gm_output`` when present; otherwise ``session["last_turn_response_policy"]``
    from the narration pipeline (see :func:`game.api._build_gpt_narration_from_authoritative_state`).
    """
    if not isinstance(gm_output, dict) or not isinstance(session, dict):
        return gm_output
    sid = str(scene_id or "").strip()
    if not sid:
        return gm_output
    if not strict_social_emission_will_apply(resolution, session, world, sid):
        return gm_output
    probe = _gm_probe_for_answer_pressure_contracts(gm_output, session)
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
    contract = _resolve_response_delta_contract(gm_output)
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
