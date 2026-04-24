"""Upstream-owned deterministic response-repair text (pre–final-emission).

Contract-shaped *answer* and *action_outcome* fallback lines, optional sanitizer
empty-fallback stock, strict-social spoken refinement cash-out (moved from final emission in
Block C), and the social-resolution helper used for dialogue repair routing live here so
:mod:`game.final_emission_gate` consumes structured fields instead of minting substitute prose
at the boundary.

See ``docs/final_emission_ownership_convergence.md`` (Objective C2, Block B / Block C).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.final_emission_text import (
    _capitalize_sentence_fragment,
    _normalize_terminal_punctuation,
    _normalize_text,
)
from game.interaction_context import inspect as inspect_interaction_context
from game.leads import get_lead, normalize_lead
from game.final_emission_validators import _contract_bool
from game.response_policy_contracts import (
    _last_player_input,
    materialize_response_policy_bundle,
    resolve_answer_completeness_contract,
    resolve_response_delta_contract,
)
from game.social_exchange_emission import (
    _npc_display_name_for_emission,
    minimal_social_emergency_fallback_line,
    strict_social_emission_will_apply,
)

UPSTREAM_PREPARED_EMISSION_KEY = "upstream_prepared_emission"
SANITIZER_BOUNDARY_STRIP_ONLY = "strip_only"


def build_social_fallback_resolution(
    *,
    resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any] | None:
    """Shape a minimal social resolution dict for dialogue / answer fallback routing."""
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


def build_minimal_answer_contract_repair_text(
    *,
    resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> str | None:
    social_resolution = build_social_fallback_resolution(
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


def build_minimal_action_outcome_contract_repair_text(
    *,
    player_input: str,
    resolution: Dict[str, Any] | None,
) -> str:
    action_clause = _to_second_person_action_clause(player_input, resolution)
    result_clause = _action_result_summary(resolution)
    return _normalize_terminal_punctuation(f"{action_clause}, and {result_clause}")


def build_upstream_prepared_emission_payload(
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """Assemble the canonical ``upstream_prepared_emission`` snapshot for a turn."""
    inspected = inspect_interaction_context(session) if isinstance(session, dict) else {}
    active_interlocutor = str((inspected or {}).get("active_interaction_target_id") or "").strip()
    sid = str(scene_id or "").strip()
    player_input = _last_player_input(resolution=resolution, session=session, scene_id=sid)
    answer = build_minimal_answer_contract_repair_text(
        resolution=resolution if isinstance(resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        world=world if isinstance(world, dict) else None,
        scene_id=sid,
    )
    action = build_minimal_action_outcome_contract_repair_text(
        player_input=player_input,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    return {
        "prepared_answer_fallback_text": answer,
        "prepared_action_fallback_text": action,
        "prepared_sanitizer_empty_fallback_text": "For a breath, the scene stays still.",
        "upstream_prepared_bundle_origin": "upstream_response_repairs.build_upstream_prepared_emission_payload",
    }


def merge_upstream_prepared_emission_into_gm_output(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> None:
    """Merge deterministic upstream repair text onto *gm_output* (idempotent).

    Caller-supplied non-empty values in an existing ``upstream_prepared_emission``
    dict win over regenerated defaults so tests and CTIR can override selectively.
    """
    if not isinstance(gm_output, dict):
        return
    fresh = build_upstream_prepared_emission_payload(
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
    )
    existing = gm_output.get(UPSTREAM_PREPARED_EMISSION_KEY)
    if not isinstance(existing, dict):
        gm_output[UPSTREAM_PREPARED_EMISSION_KEY] = fresh
        return
    merged = dict(fresh)
    for k, v in existing.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        merged[k] = v
    gm_output[UPSTREAM_PREPARED_EMISSION_KEY] = merged


def _strict_social_answer_pressure_ac_contract_active_upstream(gm_output: Dict[str, Any] | None) -> bool:
    ac = resolve_answer_completeness_contract(gm_output)
    if not isinstance(ac, dict):
        return False
    if not _contract_bool(ac, "enabled") or not _contract_bool(ac, "answer_required"):
        return False
    trace = ac.get("trace") if isinstance(ac.get("trace"), dict) else {}
    return bool(trace.get("strict_social_answer_seek_override"))


def _strict_social_answer_pressure_rd_contract_active_upstream(gm_output: Dict[str, Any] | None) -> bool:
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


def _content_tokens_for_spoken(text: str) -> set[str]:
    from game.final_emission_validators import _content_tokens

    return _content_tokens(str(text or "").lower())


def _topic_press_context_tokens(resolution: Dict[str, Any] | None) -> set[str]:
    toks: set[str] = set()
    if not isinstance(resolution, dict):
        return toks
    toks |= _content_tokens_for_spoken(str(resolution.get("prompt") or ""))
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    tr = soc.get("topic_revealed") if isinstance(soc.get("topic_revealed"), dict) else {}
    for key in ("title", "summary", "label", "topic_id"):
        toks |= _content_tokens_for_spoken(str(tr.get(key) or ""))
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
    ref_toks = _content_tokens_for_spoken(str(refinement))
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
    rtoks = _content_tokens_for_spoken(r)
    etoks = _content_tokens_for_spoken(e)
    if not rtoks:
        return True
    hit = len(rtoks & etoks)
    need = min(2, len(rtoks))
    return hit >= need


def apply_spoken_state_refinement_cash_out(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """Pre–final-emission packaging: surface promoted lead/clue text under strict-social answer pressure.

    Objective C2 Block C: moved out of :mod:`game.final_emission_repairs` so final emission does not
    author this narrative cash-out; API / post-GM paths call this before the gate.
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
        _strict_social_answer_pressure_ac_contract_active_upstream(probe)
        or _strict_social_answer_pressure_rd_contract_active_upstream(probe)
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
