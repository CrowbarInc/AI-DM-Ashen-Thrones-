"""Referential clarity violation sampling, metadata defaults, and local pronoun repair.

Pure helper logic for strict-social local pronoun substitution and referential-clarity
metadata shapes. Layer enforcement orchestration lives in
:mod:`game.final_emission_visibility_fallback`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, MutableMapping

from game.final_emission_text_formatting import _normalize_text
from game.final_emission_text_policy import _ANSWER_DIRECT_PATTERNS
from game.final_emission_validators import candidate_satisfies_answer_contract
from game.narration_visibility import (
    build_narration_visibility_contract,
    validate_player_facing_first_mentions,
    validate_player_facing_referential_clarity,
    validate_player_facing_visibility,
    _build_visible_referential_candidates,
    _split_visibility_sentences,
)
from game.prompt_context import canonical_interaction_target_npc_id
from game.response_policy_contracts import _resolve_response_type_contract
from game.social_exchange_fallback_catalog import active_interlocutor_matches_resolution_social_npc
from game.social_exchange_policy import (
    npc_display_name_for_emission,
    speaker_label,
    strict_social_emission_will_apply,
)
from game.social_exchange_validation import is_route_illegal_global_or_sanitizer_fallback_text


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
_DIALOGUE_ATTRIBUTION_HE_SHE_SPEECH_TAG = re.compile(
    r"(?:"
    r'[""“](.+?),\s*[""”]\s+\b(?:he|she|him|her)\b'
    r"|"
    r'[""“](.+?)[""”]\s*,\s+\b(?:he|she|him|her)\b'
    r")"
    r"[^.!?\n]{0,200}\b(?:"
    r"murmur|mutters|muttered|say|says|said|asks?|asked|whisper|whispers|whispered|"
    r"reply|replies|replied|add|adds|added|insist|insists|insisted|warn|warns|warned|"
    r"mutter|call|calls|called|shout|shouts|shouted|growl|growls|growled|hiss|hisses|hissed"
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
_INTRODUCER_DISQUALIFYING_TITLE_TOKENS = frozenset(
    {
        "captain",
        "serjeant",
        "sergeant",
        "commander",
        "lord",
        "lady",
        "king",
        "queen",
        "master",
        "mistress",
        "general",
        "baron",
        "duke",
        "dame",
    }
)
_SINGULAR_INDEFINITE_INTRODUCER_BEFORE_TOKEN_RE = re.compile(
    r"\ba(?:n)?\b[^.!?]{0,96}$",
    re.IGNORECASE,
)


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
    if not active_interlocutor_matches_resolution_social_npc(session, eff_resolution):
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
        speaker_label(eff_resolution)
        if isinstance(eff_resolution, dict)
        else npc_display_name_for_emission(world, scene_id, active_interlocutor)
    )
    base = str(label or "").strip()
    if not base:
        base = npc_display_name_for_emission(world, scene_id, active_interlocutor)
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


def _is_dialogue_attribution_he_she_violation(violation: Mapping[str, Any]) -> bool:
    sentence_text = str(violation.get("sentence_text") or "").strip()
    if not sentence_text:
        return False
    if _DIALOGUE_ATTRIBUTION_HE_SHE_SPEECH_TAG.search(sentence_text):
        return True
    return bool(
        re.search(
            r'[""“][^"""\n]{0,240}[""”]\s*,?\s+\b(?:he|she|him|her)\b'
            r"[^.!?\n]{0,120}\b(?:"
            r"say|says|said|asks?|asked|whisper|whispers|whispered|reply|replies|replied|"
            r"add|adds|added|insist|insists|insisted|warn|warns|warned|mutter|call|calls|called|"
            r"shout|shouts|shouted|growl|growls|growled|hiss|hisses|hissed"
            r")\b",
            sentence_text,
            re.IGNORECASE,
        )
        or re.search(
            r'[^.!?\n]{0,240}[""”]\s*,?\s+\b(?:he|she|him|her)\b'
            r"[^.!?\n]{0,120}\b(?:"
            r"say|says|said|asks?|asked|whisper|whispers|whispered|reply|replies|replied|"
            r"add|adds|added|insist|insists|insisted|warn|warns|warned|mutter|call|calls|called|"
            r"shout|shouts|shouted|growl|growls|growled|hiss|hisses|hissed"
            r")\b",
            sentence_text,
            re.IGNORECASE,
        )
    )


def _entity_id_has_contextual_grounding(
    entity_id: str,
    *,
    active_interlocutor: str,
    eff_resolution: Dict[str, Any] | None,
    violation: Mapping[str, Any],
) -> bool:
    grounded = str(entity_id or "").strip()
    if not grounded:
        return False
    if str(active_interlocutor or "").strip() == grounded:
        return True
    if isinstance(eff_resolution, dict):
        soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        if str(soc.get("npc_id") or "").strip() == grounded:
            return True
    cids = violation.get("candidate_entity_ids")
    if isinstance(cids, list) and len(cids) == 1 and str(cids[0]).strip() == grounded:
        return True
    return False


def _visible_person_like_entity_ids(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> List[str]:
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
    kinds = contract.get("visible_entity_kinds") if isinstance(contract.get("visible_entity_kinds"), dict) else {}
    return [
        entity_id
        for entity_id in visible_ids
        if str(kinds.get(entity_id) or "").strip().lower() in _REF_REPAIR_PERSON_LIKE_KINDS
    ]


def _resolve_grounded_person_entity_for_referential_repair(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    violation: Mapping[str, Any],
    allow_contextual_speaker: bool,
) -> str | None:
    cids = violation.get("candidate_entity_ids")
    if isinstance(cids, list) and len(cids) == 1:
        entity_id = str(cids[0]).strip()
        if entity_id and _active_interlocutor_visible_person_like(
            entity_id, session=session, scene=scene, world=world
        ):
            return entity_id

    if isinstance(eff_resolution, dict):
        soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), dict) else {}
        npc_id = str(soc.get("npc_id") or "").strip()
        if npc_id and _active_interlocutor_visible_person_like(
            npc_id, session=session, scene=scene, world=world
        ):
            return npc_id

    aid = str(active_interlocutor or "").strip()
    if aid and _active_interlocutor_visible_person_like(aid, session=session, scene=scene, world=world):
        return aid

    person_ids = _visible_person_like_entity_ids(session=session, scene=scene, world=world)
    if len(person_ids) == 1:
        return person_ids[0]

    if allow_contextual_speaker:
        return None
    return None


def _referential_candidates_by_id(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Dict[str, Any]]:
    contract = build_narration_visibility_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    return {
        str(candidate.get("entity_id") or "").strip(): candidate
        for candidate in _build_visible_referential_candidates(contract)
        if isinstance(candidate, dict) and str(candidate.get("entity_id") or "").strip()
    }


def _exact_alias_entity_ids_for_token(
    token: str,
    candidate_entity_ids: List[str],
    candidates_by_id: Mapping[str, Mapping[str, Any]],
) -> List[str]:
    token_norm = str(token or "").strip().lower()
    if not token_norm:
        return []
    matched: List[str] = []
    for entity_id in candidate_entity_ids:
        candidate = candidates_by_id.get(str(entity_id).strip())
        if not isinstance(candidate, dict):
            continue
        aliases = [
            str(alias or "").strip().lower()
            for alias in (candidate.get("aliases") or [])
            if str(alias or "").strip()
        ]
        if token_norm in aliases:
            matched.append(str(entity_id).strip())
    return matched


def _introducer_disambiguated_entity_id(
    token: str,
    candidate_entity_ids: List[str],
    candidates_by_id: Mapping[str, Mapping[str, Any]],
    *,
    sentence_text: str,
) -> str | None:
    """Resolve a role alias to one visible entity when introducer context excludes title-bearing names."""
    matched = _exact_alias_entity_ids_for_token(token, candidate_entity_ids, candidates_by_id)
    if not matched:
        return None
    if len(matched) == 1:
        return matched[0]
    sentence_low = str(sentence_text or "").lower()
    filtered: List[str] = []
    for entity_id in matched:
        candidate = candidates_by_id.get(entity_id)
        if not isinstance(candidate, dict):
            continue
        label = str(candidate.get("display_label") or "").lower()
        label_tokens = [part for part in label.split() if part]
        title_tokens = [part for part in label_tokens if part in _INTRODUCER_DISQUALIFYING_TITLE_TOKENS]
        if any(title not in sentence_low for title in title_tokens):
            continue
        filtered.append(entity_id)
    if len(filtered) == 1:
        return filtered[0]
    return None


def _has_singular_indefinite_introducer(*, sentence_text: str, token_offset: int) -> bool:
    prefix = str(sentence_text or "")[: max(0, int(token_offset))]
    if not prefix.strip():
        return False
    return bool(_SINGULAR_INDEFINITE_INTRODUCER_BEFORE_TOKEN_RE.search(prefix))


def _grounded_display_phrase_for_alias_substitution(
    entity_id: str,
    *,
    world: Dict[str, Any] | None,
    scene_id: str,
    surface_token: str,
) -> str:
    label = npc_display_name_for_emission(world, scene_id, entity_id)
    core = str(label or "").strip()
    if core.lower().startswith("the "):
        core = core[4:].lstrip()
    phrase = core.lower()
    if str(surface_token or "")[:1].isupper():
        return phrase[:1].upper() + phrase[1:]
    return phrase


def _bv3e_alias_introducer_violation_candidate(
    violations: List[Dict[str, Any]],
    *,
    candidates_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[Dict[str, Any], str] | None:
    ambiguous = [
        v
        for v in violations
        if isinstance(v, dict) and str(v.get("kind") or "").strip() == "ambiguous_entity_reference"
    ]
    for violation in ambiguous:
        token = str(violation.get("token") or "").strip().lower()
        if token in _LOCAL_STRICT_SOCIAL_PRONOUN_SUBSTITUTION_TOKENS:
            continue
        cids = violation.get("candidate_entity_ids")
        if not isinstance(cids, list) or len(cids) < 2:
            continue
        sentence_text = str(violation.get("sentence_text") or "")
        token_offset = int(violation.get("offset") or 0)
        if not _has_singular_indefinite_introducer(sentence_text=sentence_text, token_offset=token_offset):
            continue
        entity_id = _introducer_disambiguated_entity_id(
            token,
            [str(raw).strip() for raw in cids if str(raw).strip()],
            candidates_by_id,
            sentence_text=sentence_text,
        )
        if entity_id:
            return violation, entity_id
    return None


def _violations_eligible_for_bv3e_exact_alias_introducer_repair(
    violations: List[Dict[str, Any]],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> bool:
    candidates_by_id = _referential_candidates_by_id(session=session, scene=scene, world=world)
    return _bv3e_alias_introducer_violation_candidate(violations, candidates_by_id=candidates_by_id) is not None


def _violations_eligible_for_bv3e_multi_violation_dialogue_speaker_repair(
    violations: List[Dict[str, Any]],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> bool:
    ambiguous = [
        v
        for v in violations
        if isinstance(v, dict) and str(v.get("kind") or "").strip() == "ambiguous_entity_reference"
    ]
    dialogue = [
        v
        for v in ambiguous
        if str(v.get("token") or "").strip().lower() in {"he", "she", "him", "her"}
        and _is_dialogue_attribution_he_she_violation(v)
    ]
    if len(dialogue) != 1 or len(ambiguous) < 2:
        return False
    candidates_by_id = _referential_candidates_by_id(session=session, scene=scene, world=world)
    return _bv3e_alias_introducer_violation_candidate(violations, candidates_by_id=candidates_by_id) is not None


def _violations_eligible_for_non_strict_local_repair(
    violations: List[Dict[str, Any]],
    *,
    session: Dict[str, Any] | None = None,
    scene: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
) -> bool:
    if _violations_eligible_for_non_strict_local_pronoun_repair(violations):
        return True
    if session is None or scene is None or world is None:
        return False
    if _violations_eligible_for_bv3e_exact_alias_introducer_repair(
        violations, session=session, scene=scene, world=world
    ):
        return True
    return _violations_eligible_for_bv3e_multi_violation_dialogue_speaker_repair(
        violations, session=session, scene=scene, world=world
    )


def _try_bv3e_exact_alias_introducer_substitution_repair(
    candidate_text: str,
    *,
    violations: List[Dict[str, Any]],
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
) -> tuple[str | None, Dict[str, Any]]:
    dbg: Dict[str, Any] = {
        "referential_clarity_local_substitution_attempted": False,
        "referential_clarity_local_substitution_applied": False,
        "referential_clarity_local_substitution_token": None,
        "referential_clarity_local_substitution_replacement": None,
        "referential_clarity_repair_entity_id": None,
        "referential_clarity_fallback_avoided": False,
        "referential_clarity_fallback_after_failed_local_repair": False,
        "referential_clarity_bv3e_repair_mode": None,
    }
    candidates_by_id = _referential_candidates_by_id(session=session, scene=scene, world=world)
    picked = _bv3e_alias_introducer_violation_candidate(violations, candidates_by_id=candidates_by_id)
    if picked is None:
        return None, dbg
    violation, entity_id = picked
    token = str(violation.get("token") or "").strip()
    token_low = token.lower()
    try:
        pat = re.compile(rf"(?<!\w){re.escape(token_low)}(?!\w)", re.IGNORECASE)
    except re.error:
        return None, dbg
    matches = list(pat.finditer(candidate_text))
    token_offset = int(violation.get("offset") or -1)
    target_match = None
    if len(matches) == 1:
        target_match = matches[0]
    elif token_offset >= 0:
        for match in matches:
            if match.start() == token_offset:
                target_match = match
                break
    if target_match is None:
        return None, dbg
    replacement = _grounded_display_phrase_for_alias_substitution(
        entity_id,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
        surface_token=target_match.group(0),
    )
    repaired = (
        candidate_text[: target_match.start()]
        + replacement
        + candidate_text[target_match.end() :]
    )
    if repaired == candidate_text:
        return None, dbg

    dbg["referential_clarity_local_substitution_attempted"] = True
    dbg["referential_clarity_local_substitution_token"] = target_match.group(0)
    dbg["referential_clarity_local_substitution_replacement"] = replacement
    dbg["referential_clarity_repair_entity_id"] = entity_id
    dbg["referential_clarity_bv3e_repair_mode"] = "exact_alias_introducer"

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


def _violations_eligible_for_non_strict_local_pronoun_repair(
    violations: List[Dict[str, Any]],
) -> bool:
    ambiguous = [
        v
        for v in violations
        if isinstance(v, dict) and str(v.get("kind") or "").strip() == "ambiguous_entity_reference"
    ]
    if len(ambiguous) != 1:
        return False
    if _referential_clarity_violations_have_multi_entity_candidates(ambiguous):
        return False
    token = str(ambiguous[0].get("token") or "").strip().lower()
    return token in _LOCAL_STRICT_SOCIAL_PRONOUN_SUBSTITUTION_TOKENS


def _try_non_strict_local_pronoun_substitution_repair(
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
    strict_social_active: bool = False,
) -> tuple[str | None, Dict[str, Any]]:
    """Local pronoun substitution for observe/non-strict paths before hard fallback replace."""
    if strict_social_active:
        return _try_strict_social_local_pronoun_substitution_repair(
            candidate_text,
            violations=violations,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            eff_resolution=eff_resolution,
            active_interlocutor=active_interlocutor,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        )

    dbg: Dict[str, Any] = {
        "referential_clarity_local_substitution_attempted": False,
        "referential_clarity_local_substitution_applied": False,
        "referential_clarity_local_substitution_token": None,
        "referential_clarity_local_substitution_replacement": None,
        "referential_clarity_repair_entity_id": None,
        "referential_clarity_fallback_avoided": False,
        "referential_clarity_fallback_after_failed_local_repair": False,
        "referential_clarity_bv3e_repair_mode": None,
    }
    if not candidate_text.strip():
        return None, dbg

    if _violations_eligible_for_bv3e_exact_alias_introducer_repair(
        violations, session=session, scene=scene, world=world
    ):
        repaired, alias_dbg = _try_bv3e_exact_alias_introducer_substitution_repair(
            candidate_text,
            violations=violations,
            session=session,
            scene=scene,
            world=world,
            scene_id=scene_id,
            grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        )
        dbg.update(alias_dbg)
        if repaired is not None:
            return repaired, dbg

    if not _violations_eligible_for_non_strict_local_pronoun_repair(violations):
        return None, dbg

    v0 = next(
        v
        for v in violations
        if isinstance(v, dict) and str(v.get("kind") or "").strip() == "ambiguous_entity_reference"
    )
    token = str(v0.get("token") or "").strip().lower()
    dialogue_attribution = _is_dialogue_attribution_he_she_violation(v0)
    entity_id = _resolve_grounded_person_entity_for_referential_repair(
        session=session,
        scene=scene,
        world=world,
        eff_resolution=eff_resolution,
        active_interlocutor=active_interlocutor,
        violation=v0,
        allow_contextual_speaker=dialogue_attribution,
    )
    if not entity_id:
        return None, dbg

    contextual_grounding = _entity_id_has_contextual_grounding(
        entity_id,
        active_interlocutor=active_interlocutor,
        eff_resolution=eff_resolution,
        violation=v0,
    )
    person_ids = _visible_person_like_entity_ids(session=session, scene=scene, world=world)
    if len(person_ids) > 1 and not contextual_grounding:
        return None, dbg
    if not dialogue_attribution and not contextual_grounding and len(person_ids) != 1:
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

    replacement = _grounded_speaker_phrase_for_pronoun_substitution(
        eff_resolution=eff_resolution,
        active_interlocutor=entity_id,
        world=world if isinstance(world, dict) else None,
        scene_id=str(scene_id or "").strip(),
        pronoun_surface=matches[0].group(0),
    )
    repaired = pat.sub(replacement, candidate_text, count=1)
    if repaired == candidate_text:
        return None, dbg

    dbg["referential_clarity_local_substitution_attempted"] = True
    dbg["referential_clarity_local_substitution_token"] = matches[0].group(0)
    dbg["referential_clarity_local_substitution_replacement"] = replacement
    dbg["referential_clarity_repair_entity_id"] = entity_id

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


def _apply_referential_clarity_local_repair_success_meta(
    out: Dict[str, Any],
    meta: Dict[str, Any],
    *,
    candidate_text: str,
    repaired: str,
    subst_dbg: Mapping[str, Any],
    tags_extra: List[str] | None = None,
) -> None:
    out["player_facing_text"] = repaired
    meta["referential_clarity_validation_passed"] = True
    meta["referential_clarity_replacement_applied"] = False
    meta["referential_clarity_violation_kinds"] = []
    meta["referential_clarity_violation_sample"] = []
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = list(dict.fromkeys([str(t) for t in tags if isinstance(t, str)] + (tags_extra or ["referential_clarity_local_substitution"])))
    gate_out_text = _normalize_text(out.get("player_facing_text"))
    meta["post_gate_mutation_detected"] = bool(meta.get("post_gate_mutation_detected")) or (
        candidate_text != gate_out_text
    )
    meta["final_text_preview"] = (gate_out_text[:120] + "…") if len(gate_out_text) > 120 else gate_out_text
    for key in (
        "referential_clarity_local_substitution_attempted",
        "referential_clarity_local_substitution_applied",
        "referential_clarity_local_substitution_token",
        "referential_clarity_local_substitution_replacement",
        "referential_clarity_repair_entity_id",
        "referential_clarity_fallback_avoided",
        "referential_clarity_fallback_after_failed_local_repair",
        "referential_clarity_bv3e_repair_mode",
    ):
        if key in subst_dbg:
            meta[key] = subst_dbg[key]


def apply_observe_referential_clarity_upstream_repair(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    eff_resolution: Dict[str, Any] | None,
    active_interlocutor: str,
    res_kind: str,
    strict_social_active: bool,
    grounded_speaker_first_mention_exemption_entity_id: str | None = None,
) -> Dict[str, Any]:
    """Observe-route upstream referential-clarity repair before visibility enforcement."""
    from game.final_emission_meta import (
        PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION,
        ensure_final_emission_meta_dict,
        stamp_producer_repair_kind,
    )

    meta = ensure_final_emission_meta_dict(out)
    meta["referential_clarity_upstream_repair_attempted"] = False
    meta["referential_clarity_upstream_repair_applied"] = False
    meta["referential_clarity_upstream_repair_eligible"] = False
    meta["referential_clarity_upstream_repair_entity_id"] = None
    meta["referential_clarity_unrepaired_violation_count"] = 0

    if strict_social_active or str(res_kind or "").strip().lower() != "observe":
        return out

    candidate_text = _normalize_text(out.get("player_facing_text"))
    validation = validate_player_facing_referential_clarity(
        candidate_text,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    if validation.get("ok") is True:
        return out

    violations = validation.get("violations") if isinstance(validation.get("violations"), list) else []
    meta["referential_clarity_upstream_repair_attempted"] = True
    meta["referential_clarity_unrepaired_violation_count"] = len(violations)
    meta["referential_clarity_upstream_repair_eligible"] = _violations_eligible_for_non_strict_local_repair(
        violations,
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )

    repaired, subst_dbg = _try_non_strict_local_pronoun_substitution_repair(
        candidate_text,
        violations=[v for v in violations if isinstance(v, dict)],
        session=session,
        scene=scene,
        world=world,
        scene_id=scene_id,
        eff_resolution=eff_resolution if isinstance(eff_resolution, dict) else None,
        active_interlocutor=active_interlocutor,
        grounded_speaker_first_mention_exemption_entity_id=grounded_speaker_first_mention_exemption_entity_id,
        strict_social_active=False,
    )
    if repaired is None:
        for key, value in subst_dbg.items():
            meta[key] = value
        return out

    _apply_referential_clarity_local_repair_success_meta(
        out,
        meta,
        candidate_text=candidate_text,
        repaired=repaired,
        subst_dbg=subst_dbg,
    )
    meta["referential_clarity_upstream_repair_applied"] = True
    meta["referential_clarity_upstream_repair_entity_id"] = subst_dbg.get("referential_clarity_repair_entity_id")
    meta["referential_clarity_unrepaired_violation_count"] = 0
    meta["referential_clarity_checked_entities"] = validation.get("checked_entities") or []
    stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION)
    return out


def _referential_clarity_repair_meta_snapshot(meta: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "referential_clarity_validation_passed",
        "referential_clarity_replacement_applied",
        "referential_clarity_upstream_repair_attempted",
        "referential_clarity_upstream_repair_applied",
        "referential_clarity_upstream_repair_eligible",
        "referential_clarity_upstream_repair_entity_id",
        "referential_clarity_unrepaired_violation_count",
        "referential_clarity_bv3e_repair_mode",
        "referential_clarity_local_substitution_attempted",
        "referential_clarity_local_substitution_applied",
        "referential_clarity_local_substitution_token",
        "referential_clarity_local_substitution_replacement",
        "referential_clarity_repair_entity_id",
        "referential_clarity_fallback_avoided",
        "referential_clarity_fallback_after_failed_local_repair",
    )
    return {key: meta[key] for key in keys if key in meta}


def _restore_referential_clarity_repair_meta(meta: MutableMapping[str, Any], preserved: Mapping[str, Any]) -> None:
    for key, value in preserved.items():
        meta[key] = value


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
    meta["referential_clarity_repair_entity_id"] = None
    meta["referential_clarity_fallback_avoided"] = False
    meta["referential_clarity_fallback_after_failed_local_repair"] = False
    meta["referential_clarity_upstream_repair_attempted"] = False
    meta["referential_clarity_upstream_repair_applied"] = False
    meta["referential_clarity_upstream_repair_eligible"] = False
    meta["referential_clarity_upstream_repair_entity_id"] = None
    meta["referential_clarity_unrepaired_violation_count"] = 0
    meta["referential_clarity_bv3e_repair_mode"] = None


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
