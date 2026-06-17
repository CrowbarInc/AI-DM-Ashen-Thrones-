"""Referential clarity violation sampling, metadata defaults, and local pronoun repair.

Pure helper logic for strict-social local pronoun substitution and referential-clarity
metadata shapes. Layer enforcement orchestration lives in
:mod:`game.final_emission_visibility_fallback`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.final_emission_text import _ANSWER_DIRECT_PATTERNS, _normalize_text
from game.final_emission_validators import candidate_satisfies_answer_contract
from game.narration_visibility import (
    build_narration_visibility_contract,
    validate_player_facing_first_mentions,
    validate_player_facing_referential_clarity,
    validate_player_facing_visibility,
    _split_visibility_sentences,
)
from game.prompt_context import canonical_interaction_target_npc_id
from game.response_policy_contracts import _resolve_response_type_contract
from game.social_exchange_emission import (
    _active_interlocutor_matches_resolution_social_npc,
    _npc_display_name_for_emission,
    _speaker_label,
    is_route_illegal_global_or_sanitizer_fallback_text,
    strict_social_emission_will_apply,
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
