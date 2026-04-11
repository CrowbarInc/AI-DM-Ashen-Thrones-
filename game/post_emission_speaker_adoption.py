"""Post-emission adoption of authoritative in-scene speakers into interaction state.

When final player-facing text shows a grounded, explicit takeover with directed dialogue,
update ``active_interaction_target_id`` / ``current_interlocutor`` so stored state matches
visible output. Narrow by design: no route-parser changes; uses emitted text + roster.

When adoption does not apply (e.g. no takeover cue) but the emitted opening speaker is a
different grounded NPC than the stored interlocutor, :func:`apply_stale_interlocutor_invalidation_after_emission`
clears the stale anchor so the next turn does not auto-bind through continuity.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from game.final_emission_gate import detect_emitted_speaker_signature
from game.interaction_context import (
    canonical_scene_addressable_roster,
    clear_stale_social_interlocutor_continuity,
    extract_npc_reference_tokens,
    inspect as inspect_interaction_context,
    is_actor_addressable_in_current_scene,
    set_social_target,
    _display_name_for_npc_entry,
)
from game.prompt_context import canonical_interaction_target_npc_id
from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS

_NARRATOR_NEUTRAL_REASON = "narrator_neutral_no_allowed_speaker"
_QUOTE_CHARS = frozenset({'"', "\u201c", "\u201d", "\u2018", "\u2019"})


def _player_facing_text_from_gm(gm: Dict[str, Any] | None) -> str:
    if not isinstance(gm, dict):
        return ""
    t = gm.get("player_facing_text")
    return str(t).strip() if isinstance(t, str) else ""


def _final_emission_enforcement_reason(gm: Dict[str, Any] | None) -> str:
    """Return speaker_contract final_reason_code when recorded by :func:`apply_final_emission_gate`."""
    if not isinstance(gm, dict):
        return ""
    fem = gm.get("_final_emission_meta")
    if isinstance(fem, dict):
        r = str(fem.get("speaker_contract_enforcement_reason") or "").strip()
        if r:
            return r
    md = gm.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            sce = em.get("speaker_contract_enforcement")
            if isinstance(sce, dict):
                r2 = str(sce.get("final_reason_code") or "").strip()
                if r2:
                    return r2
    return ""


def _text_has_dialogue_quotation(text: str) -> bool:
    if not text:
        return False
    return any(c in text for c in _QUOTE_CHARS)


def _normalize_speaker_label_for_match(raw: str) -> str:
    s = str(raw or "").strip()
    s = re.sub(r"[.,;:!?]+$", "", s).strip()
    low = s.lower()
    if low.startswith("the "):
        s = s[4:].strip()
    return s.strip()


def _label_matches_npc_entry(label_norm: str, npc: Dict[str, Any]) -> bool:
    if len(label_norm) < 2:
        return False
    nid = str(npc.get("id") or "").strip()
    disp = _display_name_for_npc_entry(npc if isinstance(npc, dict) else None, nid).strip().lower()
    name = str(npc.get("name") or "").strip().lower()
    cand = label_norm.lower().strip()
    if not cand:
        return False
    if name and cand == name:
        return True
    if disp and cand == disp:
        return True
    slug_disp = nid.replace("_", " ").replace("-", " ").strip().lower()
    if slug_disp and cand == slug_disp:
        return True
    for tok in extract_npc_reference_tokens(npc if isinstance(npc, dict) else {}):
        if len(tok) < 3:
            continue
        tl = tok.lower()
        if cand == tl:
            return True
        if len(cand) >= 4 and re.search(rf"\b{re.escape(tl)}\b", cand):
            return True
    return False


def _unique_addressable_npc_id_for_label(
    label: str,
    *,
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    scene_envelope: Dict[str, Any] | None,
) -> Optional[str]:
    label_norm = _normalize_speaker_label_for_match(label)
    if not label_norm:
        return None
    roster = canonical_scene_addressable_roster(
        world,
        scene_id,
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    hits: List[str] = []
    for npc in roster:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        if not nid:
            continue
        if _label_matches_npc_entry(label_norm, npc):
            hits.append(nid)
    if len(hits) != 1:
        return None
    return hits[0]


def _forbidden_generic_label(sig: Dict[str, Any], label: str) -> bool:
    if bool(sig.get("is_generic_fallback_label")):
        return True
    low = label.strip().lower()
    for fb in SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS:
        fbs = str(fb or "").strip().lower()
        if not fbs:
            continue
        if fbs == low or fbs in low or low in fbs:
            return True
    if low in ("a voice", "the voice", "someone", "crowd", "the crowd"):
        return True
    return False


def _takeover_or_player_directed_reply(text: str, sig: Dict[str, Any]) -> bool:
    if bool(sig.get("has_interruption_framing")):
        return True
    t = str(text or "")
    m = re.search(r'"([^"]{0,400})"', t)
    if m and re.search(r"\byou\b", m.group(1) or "", re.IGNORECASE):
        return True
    low = t.lower()
    if any(
        w in low
        for w in (
            "halt",
            "freeze",
            "hands up",
            "step back",
            "papers",
            "confront",
            "blocking your",
            "get back",
            "hold it",
        )
    ):
        return True
    return False


def _likely_secondary_speaker_conflict(text: str, primary_label: str) -> bool:
    """True when a second explicit speech attribution appears (skip ambiguous multi-speaker)."""
    t = str(text or "")
    if t.count('"') < 4:
        return False
    # Two distinct "Name says/asks" openings (very conservative).
    hits = list(
        re.finditer(
            r"(?m)^[^\n\"]{2,120}?\b(?:says|said|asks|asked|replies|replied|adds|added)\b",
            t,
            re.IGNORECASE,
        )
    )
    if len(hits) < 2:
        return False
    prim = _normalize_speaker_label_for_match(primary_label).lower()
    labels: List[str] = []
    for m in hits[:3]:
        frag = t[m.start() : m.end()]
        mm = re.match(r"^\s*(.+?)\s+(?:says|said|asks|asked|replies|replied|adds|added)\b", frag, re.IGNORECASE | re.DOTALL)
        if mm:
            labels.append(_normalize_speaker_label_for_match(mm.group(1)).lower())
    uniq = {x for x in labels if x}
    if len(uniq) <= 1:
        return False
    if prim and prim in uniq and len(uniq) > 1:
        return True
    return len(uniq) > 1


def _resolve_visible_grounded_opening_speaker_canon(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
) -> tuple[Optional[str], str]:
    """Return canonical NPC id for the emitted opening grounded speaker, or (None, reason)."""
    if not isinstance(session, dict) or not isinstance(world, dict) or not isinstance(scene, dict):
        return None, "scene_changed_or_bad_inputs"
    sid = str((scene.get("scene") or {}).get("id") or "").strip()
    if not sid:
        return None, "no_scene_id"

    text = _player_facing_text_from_gm(gm_output)
    if not text:
        return None, "empty_text"

    fer = _final_emission_enforcement_reason(gm_output if isinstance(gm_output, dict) else None)
    if fer == _NARRATOR_NEUTRAL_REASON:
        return None, "narrator_neutral_emission"

    sig = detect_emitted_speaker_signature(text, resolution if isinstance(resolution, dict) else None)
    label = str(sig.get("speaker_label") or "").strip()
    if not label:
        return None, "no_opening_speaker_signature"
    if not bool(sig.get("is_explicitly_attributed")) or not str(sig.get("speaker_name") or "").strip():
        return None, "not_explicit_named_speaker"
    if _forbidden_generic_label(sig, label):
        return None, "generic_or_anonymous_speaker"
    if not _text_has_dialogue_quotation(text):
        return None, "no_dialogue_quotation"
    if _likely_secondary_speaker_conflict(text, label):
        return None, "ambiguous_multi_speaker"

    env = scene if isinstance(scene, dict) else None
    npc_id = _unique_addressable_npc_id_for_label(
        label,
        session=session,
        world=world,
        scene_id=sid,
        scene_envelope=env,
    )
    if not npc_id:
        return None, "label_not_unique_or_unresolved"

    if not is_actor_addressable_in_current_scene(session, env, npc_id, world=world):
        return None, "speaker_not_addressable"

    canon = canonical_interaction_target_npc_id(session, npc_id) or npc_id
    return canon, "resolved"


def apply_stale_interlocutor_invalidation_after_emission(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    scene_changed: bool,
    adoption_debug: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """If visible grounded speech contradicts the stored interlocutor, clear the stale anchor.

    Runs after :func:`apply_post_emission_speaker_adoption`. Narrow: does not clear when adoption
    already updated state, when no grounded alternate speaker is resolved, or when output is
    ambiguous multi-speaker (same guard as adoption).
    """
    dbg: Dict[str, Any] = {"cleared": False, "reason": "skipped"}
    ad = adoption_debug if isinstance(adoption_debug, dict) else {}
    if ad.get("adopted") is True:
        dbg["reason"] = "adoption_resolved_speaker"
        return dbg
    if scene_changed or not isinstance(session, dict) or not isinstance(world, dict):
        dbg["reason"] = "scene_changed_or_bad_inputs"
        return dbg
    if not isinstance(scene, dict):
        dbg["reason"] = "no_scene"
        return dbg

    prior = str((inspect_interaction_context(session).get("active_interaction_target_id") or "")).strip()
    prior_canon = canonical_interaction_target_npc_id(session, prior) if prior else ""

    visible_canon, res = _resolve_visible_grounded_opening_speaker_canon(
        session,
        world,
        scene,
        gm_output,
        resolution=resolution,
    )
    dbg["visible_resolution"] = res
    if not visible_canon:
        dbg["reason"] = res or "no_visible_speaker"
        return dbg
    if not prior_canon or prior_canon == visible_canon:
        dbg["reason"] = "no_stale_mismatch"
        dbg["visible_grounded_speaker_id"] = visible_canon
        return dbg

    clear_stale_social_interlocutor_continuity(session)
    dbg["cleared"] = True
    dbg["reason"] = "visible_speaker_contradicts_stored_interlocutor"
    dbg["prior_interlocutor_id"] = prior_canon
    dbg["visible_grounded_speaker_id"] = visible_canon
    return dbg


def apply_post_emission_speaker_adoption(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None = None,
    scene_changed: bool = False,
) -> Dict[str, Any]:
    """Optionally adopt emitted opening speaker as social interlocutor. Returns debug dict."""
    dbg: Dict[str, Any] = {"adopted": False, "reason": "skipped"}
    if scene_changed or not isinstance(session, dict) or not isinstance(world, dict):
        dbg["reason"] = "scene_changed_or_bad_inputs"
        return dbg
    if not isinstance(scene, dict):
        dbg["reason"] = "no_scene"
        return dbg

    text = _player_facing_text_from_gm(gm_output)
    canon, early = _resolve_visible_grounded_opening_speaker_canon(
        session,
        world,
        scene,
        gm_output,
        resolution=resolution,
    )
    if not canon:
        dbg["reason"] = early
        return dbg

    sig = detect_emitted_speaker_signature(text, resolution if isinstance(resolution, dict) else None)
    prior = str((inspect_interaction_context(session).get("active_interaction_target_id") or "")).strip()
    prior_canon = canonical_interaction_target_npc_id(session, prior) if prior else ""

    if prior_canon and prior_canon == canon:
        dbg["reason"] = "already_current_interlocutor"
        dbg["npc_id"] = canon
        return dbg

    if not _takeover_or_player_directed_reply(text, sig):
        dbg["reason"] = "no_takeover_or_player_directed_cue"
        return dbg

    set_social_target(session, canon)
    dbg["adopted"] = True
    dbg["reason"] = "emitted_authoritative_takeover"
    dbg["npc_id"] = canon
    dbg["prior_active_interaction_target_id"] = prior or None
    return dbg
