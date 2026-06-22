"""BX2 — Final-emission canonical speaker observation stamp.

Builds and attaches ``metadata.emission_debug.final_speaker_observation`` at the last
safe finalize boundary after terminal text mutation. Scene-roster-bounded only; does
not introduce global alias tables.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Mapping, MutableMapping, Optional

from game.emitted_speaker_signature import detect_emitted_speaker_signature
from game.interaction_context import (
    _all_npc_ids_matching_vocative_raw,
    _collect_embedded_direct_address_phrase_candidates,
    _last_spoken_generic_role_slug,
    _npc_matches_normalized_generic_role,
    canonical_scene_addressable_roster,
    match_generic_role_address,
    resolve_authoritative_social_target,
    scene_addressable_actor_ids,
)
from game.social_exchange_policy import merged_player_prompt_for_gate
from game.speaker_contract_enforcement import get_speaker_selection_contract

FinalSpeakerStatus = Literal["resolved", "neutral", "unattributed", "ambiguous", "unresolved"]

FINAL_SPEAKER_OBSERVATION_KEY = "final_speaker_observation"


def _clean_id(value: Any) -> str | None:
    s = str(value or "").strip()
    return s or None


def _normalize_label(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _label_matches_speaker_id(label: str | None, speaker_id: str | None, speaker_name: str | None) -> bool:
    if not label or not speaker_id:
        return False
    low = _normalize_label(label)
    if speaker_name and _normalize_label(speaker_name) == low:
        return True
    disp = _normalize_label(speaker_id.replace("_", " ").replace("-", " "))
    return low == disp or low in disp or disp in low


def _roster_generic_role_candidate_ids(
    *,
    player_text: str,
    world: Mapping[str, Any] | None,
    scene_id: str,
    scene_envelope: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None,
) -> list[str]:
    """Scene-roster matches for embedded vocative/role tokens (e.g. bare ``guard``)."""
    roster = canonical_scene_addressable_roster(
        dict(world) if isinstance(world, Mapping) else None,
        scene_id,
        scene_envelope=dict(scene_envelope) if isinstance(scene_envelope, Mapping) else None,
        session=dict(session) if isinstance(session, Mapping) else None,
    )
    if not roster:
        return []
    addr_ids = scene_addressable_actor_ids(
        dict(world) if isinstance(world, Mapping) else None,
        scene_id,
        scene_envelope=dict(scene_envelope) if isinstance(scene_envelope, Mapping) else None,
        session=dict(session) if isinstance(session, Mapping) else None,
    )
    low = str(player_text or "").strip().lower()
    tokens: list[str] = []
    tokens.extend(_collect_embedded_direct_address_phrase_candidates(low))
    role_slug = _last_spoken_generic_role_slug(low)
    if role_slug:
        tokens.append(role_slug)
    gr = match_generic_role_address(low, roster)
    if gr.get("matched_role"):
        tokens.append(str(gr.get("matched_role")))
    candidates: list[str] = []
    for token in tokens:
        for nid in _all_npc_ids_matching_vocative_raw(token, roster, addr_ids=addr_ids):
            if nid not in candidates:
                candidates.append(nid)
        norm = _normalize_label(token).replace(" ", "_")
        if norm:
            for row in roster:
                if not isinstance(row, dict):
                    continue
                nid = _clean_id(row.get("id"))
                if not nid or nid not in addr_ids:
                    continue
                if _npc_matches_normalized_generic_role(row, norm) and nid not in candidates:
                    candidates.append(nid)
    return sorted(candidates)


def _conservative_authoritative_routing(
    *,
    session: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    scene_id: str,
    scene_envelope: Mapping[str, Any] | None,
    player_text: str,
    resolution: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not scene_id or not str(player_text or "").strip():
        return {"target_resolved": False, "npc_id": None, "source": "none"}
    na = None
    if isinstance(resolution, Mapping):
        md = resolution.get("metadata")
        if isinstance(md, Mapping):
            na = md.get("normalized_action")
    return resolve_authoritative_social_target(
        dict(session) if isinstance(session, Mapping) else None,
        dict(world) if isinstance(world, Mapping) else None,
        scene_id,
        player_text=player_text,
        normalized_action=dict(na) if isinstance(na, Mapping) else None,
        merged_player_prompt=player_text,
        scene_envelope=dict(scene_envelope) if isinstance(scene_envelope, Mapping) else None,
        allow_first_roster_fallback=False,
    )


def build_final_speaker_observation(
    *,
    final_text: str,
    gm_output: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    eff_resolution: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    scene_envelope: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
) -> Dict[str, Any]:
    """Derive provenance-bearing final speaker observation from finalized text and gate metadata."""
    out = gm_output if isinstance(gm_output, Mapping) else {}
    md = out.get("metadata") if isinstance(out.get("metadata"), Mapping) else {}
    em_dbg = md.get("emission_debug") if isinstance(md.get("emission_debug"), Mapping) else {}
    trace = out.get("trace") if isinstance(out.get("trace"), Mapping) else None

    res = eff_resolution if isinstance(eff_resolution, Mapping) else resolution
    contract = get_speaker_selection_contract(
        dict(res) if isinstance(res, Mapping) else None,
        metadata=dict(md) if isinstance(md, Mapping) else None,
        trace=dict(trace) if isinstance(trace, Mapping) else None,
    )
    contract_primary = _clean_id(contract.get("primary_speaker_id"))
    contract_name = _clean_id(contract.get("primary_speaker_name"))
    contract_source = _clean_id(contract.get("primary_speaker_source"))

    sce = em_dbg.get("speaker_contract_enforcement") if isinstance(em_dbg.get("speaker_contract_enforcement"), Mapping) else {}
    enforcement_reason = _clean_id(sce.get("final_reason_code"))

    soc = {}
    if isinstance(res, Mapping):
        raw_soc = res.get("social")
        if isinstance(raw_soc, Mapping):
            soc = dict(raw_soc)
    reconcile_speaker_id = _clean_id(soc.get("npc_id"))

    sid = _clean_id(scene_id) or ""
    merged_prompt = merged_player_prompt_for_gate(
        dict(resolution) if isinstance(resolution, Mapping) else None,
        dict(session) if isinstance(session, Mapping) else None,
        sid,
    )
    if not merged_prompt and isinstance(contract.get("debug"), Mapping):
        preview = str(contract["debug"].get("merged_player_prompt_preview") or "").rstrip("…").strip()
        merged_prompt = preview or merged_prompt

    signature = dict(detect_emitted_speaker_signature(str(final_text or ""), dict(res) if isinstance(res, Mapping) else None))
    emitted_label = _clean_id(signature.get("speaker_label") or signature.get("speaker_name"))
    confidence = _clean_id(signature.get("confidence")) or "low"

    notes: list[str] = []
    candidates: list[str] = []

    routing_auth: dict[str, Any] = {}
    routing_speaker_id: str | None = None
    routing_resolved = False
    routing_checked = False
    if sid and merged_prompt:
        routing_checked = True
        routing_auth = _conservative_authoritative_routing(
            session=session,
            world=world,
            scene_id=sid,
            scene_envelope=scene_envelope,
            player_text=merged_prompt,
            resolution=resolution if isinstance(resolution, Mapping) else res,
        )
        routing_resolved = bool(routing_auth.get("target_resolved"))
        routing_speaker_id = _clean_id(routing_auth.get("npc_id")) if routing_resolved else None

        role_candidates = _roster_generic_role_candidate_ids(
            player_text=merged_prompt,
            world=world,
            scene_id=sid,
            scene_envelope=scene_envelope,
            session=session,
        )
        if len(role_candidates) > 1:
            candidates = role_candidates
            notes.append("multiple_scene_roster_rows_match_generic_role")

    if reconcile_speaker_id and reconcile_speaker_id not in candidates:
        if contract_primary and reconcile_speaker_id != routing_speaker_id:
            if reconcile_speaker_id not in candidates:
                candidates = sorted(dict.fromkeys([*candidates, reconcile_speaker_id]))

    status: FinalSpeakerStatus
    canonical_speaker_id: str | None = None
    resolution_source: str | None = None

    if enforcement_reason == "narrator_neutral_no_allowed_speaker":
        status = "neutral"
        resolution_source = enforcement_reason
        notes.append("enforcement_narrator_neutral")
    elif not emitted_label and not signature.get("is_explicitly_attributed"):
        status = "unattributed"
        notes.append("no_emitted_speaker_label")
    elif signature.get("is_generic_fallback_label"):
        status = "ambiguous"
        notes.append("emitted_generic_fallback_label")
        if contract_primary:
            notes.append("contract_primary_present")
    elif routing_checked and not routing_resolved and contract_primary:
        status = "ambiguous"
        notes.append("routing_unresolved_contract_primary_present")
        if reconcile_speaker_id and reconcile_speaker_id != routing_speaker_id:
            notes.append("reconcile_candidate_disagrees_with_routing")
        resolution_source = contract_source or _clean_id(routing_auth.get("source")) or "routing_unresolved"
    elif routing_checked and len(candidates) > 1 and not routing_resolved:
        status = "ambiguous"
        notes.append("multiple_roster_candidates_unresolved_routing")
    elif len(candidates) > 1 and (
        not routing_checked
        or not routing_resolved
        or (routing_speaker_id and routing_speaker_id not in candidates)
    ):
        status = "ambiguous"
        notes.append("multiple_roster_candidates")
    elif contract_primary and emitted_label and not _label_matches_speaker_id(emitted_label, contract_primary, contract_name):
        status = "unresolved"
        notes.append("emitted_label_does_not_match_contract_primary")
    elif routing_checked and routing_resolved and contract_primary and routing_speaker_id == contract_primary:
        if emitted_label and _label_matches_speaker_id(emitted_label, contract_primary, contract_name):
            status = "resolved"
            canonical_speaker_id = contract_primary
            resolution_source = contract_source or _clean_id(routing_auth.get("source"))
        elif signature.get("is_explicitly_attributed"):
            status = "unresolved"
            notes.append("emitted_label_does_not_match_contract_primary")
        else:
            status = "unattributed"
    elif routing_checked and routing_resolved and routing_speaker_id:
        if emitted_label and _label_matches_speaker_id(emitted_label, routing_speaker_id, contract_name):
            status = "resolved"
            canonical_speaker_id = routing_speaker_id
            resolution_source = _clean_id(routing_auth.get("source"))
        else:
            status = "unresolved"
            notes.append("routing_resolved_emitted_label_unmatched")
    elif contract_primary and emitted_label and _label_matches_speaker_id(emitted_label, contract_primary, contract_name):
        status = "resolved"
        canonical_speaker_id = contract_primary
        resolution_source = contract_source or "contract.primary_speaker_id"
    elif contract_primary or reconcile_speaker_id:
        status = "unresolved"
        notes.append("speaker_identity_not_fully_joined")
    else:
        status = "unattributed"

    if (
        status == "resolved"
        and routing_checked
        and routing_resolved
        and contract_primary
        and routing_speaker_id
        and routing_speaker_id != contract_primary
    ):
        status = "ambiguous"
        canonical_speaker_id = None
        notes.append("routing_contract_id_mismatch")

    return {
        "status": status,
        "canonical_speaker_id": canonical_speaker_id,
        "emitted_label": emitted_label,
        "resolution_source": resolution_source,
        "confidence": confidence,
        "candidates": candidates,
        "routing_speaker_id": routing_speaker_id,
        "contract_primary_speaker_id": contract_primary,
        "reconcile_speaker_id": reconcile_speaker_id,
        "notes": notes,
    }


def stamp_final_speaker_observation(
    out: MutableMapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
    eff_resolution: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    scene_envelope: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
) -> Dict[str, Any]:
    """Attach final speaker observation to ``metadata.emission_debug`` on *out*."""
    final_text = str(out.get("player_facing_text") or "")
    observation = build_final_speaker_observation(
        final_text=final_text,
        gm_output=out,
        resolution=resolution,
        eff_resolution=eff_resolution,
        session=session,
        world=world,
        scene_envelope=scene_envelope,
        scene_id=scene_id,
    )
    md = out.get("metadata")
    if not isinstance(md, dict):
        md = {}
        out["metadata"] = md
    em_dbg = md.get("emission_debug")
    if not isinstance(em_dbg, dict):
        em_dbg = {}
        md["emission_debug"] = em_dbg
    em_dbg[FINAL_SPEAKER_OBSERVATION_KEY] = observation
    return observation


def read_final_speaker_observation(gm_output: Mapping[str, Any] | None) -> Dict[str, Any] | None:
    """Read stamped observation from gate output metadata."""
    if not isinstance(gm_output, Mapping):
        return None
    md = gm_output.get("metadata")
    if not isinstance(md, Mapping):
        return None
    em_dbg = md.get("emission_debug")
    if not isinstance(em_dbg, Mapping):
        return None
    obs = em_dbg.get(FINAL_SPEAKER_OBSERVATION_KEY)
    return dict(obs) if isinstance(obs, Mapping) else None
