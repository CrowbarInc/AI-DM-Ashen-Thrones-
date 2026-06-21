"""Runtime owner for post-GPT response policy enforcement orchestration.

Orchestration, manifest contract helpers, applied-marker semantics, and
validation/metadata-only helpers live here. Question-resolution and
validator-voice enforcement are owned here; broader uncertainty rendering
helpers remain in ``game.gm`` until a later extraction block.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from game.prompt_context import RESPONSE_RULE_PRIORITY
from game.social_exchange_policy import strict_social_emission_will_apply
from game.utils import slugify

# ``gm["metadata"][GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED]`` is set by
# :func:`apply_response_policy_enforcement`. Post-GM adoption checks this for a
# defense-in-depth signal that semantic policy already ran (not a replacement for
# branch shape validators / typed effects).
GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED = "response_policy_enforcement_applied"

_VALIDATOR_VOICE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bi can(?:not|'t)\s+answer that\b", re.IGNORECASE), "cant_answer_that"),
    (re.compile(r"\bbased on what(?:'s| is)\s+established\b", re.IGNORECASE), "based_on_established"),
    (re.compile(r"\bwe can determine\b", re.IGNORECASE), "we_can_determine"),
    (re.compile(r"\bas an ai\b", re.IGNORECASE), "as_an_ai"),
    (re.compile(r"\bas (?:a )?(?:language )?model\b", re.IGNORECASE), "model_identity"),
    (re.compile(r"\bi (?:can(?:not|'t)|do not|don't)\s+(?:access|see|know|verify|check|look up)\b", re.IGNORECASE), "system_limitation"),
    (re.compile(r"\bi (?:do not|don't|can(?:not|'t))\s+have access\b", re.IGNORECASE), "tool_access"),
    (re.compile(r"\bmy (?:system|training data|tools?)\b", re.IGNORECASE), "system_reference"),
    (re.compile(r"\b(?:the evidence|available evidence|the record|canon)\s+(?:suggests|indicates|shows)\b", re.IGNORECASE), "evidence_review"),
    (re.compile(r"\b(?:under|by)\s+the\s+rules\b", re.IGNORECASE), "rules_explanation"),
    (re.compile(r"\b(?:this|that|it)\s+(?:would|will)\s+require\s+(?:a\s+)?(?:roll|check)\b", re.IGNORECASE), "rules_explanation"),
)


def detect_validator_voice(player_facing_text: str) -> List[str]:
    """Detect system/validator tone that breaks in-world narration."""
    if not isinstance(player_facing_text, str):
        return []
    txt = " ".join(player_facing_text.split())
    if not txt:
        return []
    hits: List[str] = []
    for pattern, label in _VALIDATOR_VOICE_PATTERNS:
        if pattern.search(txt):
            hits.append(f"validator_voice:{label}")
    return hits


def _normalize_response_policy_input(response_policy: Any) -> Dict[str, Any]:
    """Return a dict view of ``response_policy`` for enforcement (metadata/validation only)."""
    return response_policy if isinstance(response_policy, dict) else {}


def _scene_id_from_scene_envelope(scene_envelope: Dict[str, Any]) -> str:
    """Extract ``scene.id`` for strict-social detection (metadata-only)."""
    scene_id = ""
    if isinstance(scene_envelope, dict):
        sc = scene_envelope.get("scene")
        if isinstance(sc, dict):
            scene_id = str(sc.get("id") or "").strip()
    return scene_id


def _init_response_policy_enforcement_state(
    gm: Dict[str, Any],
    response_policy: Any,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> tuple[Dict[str, Any], Dict[str, Any], bool]:
    """Copy the GM dict, normalize policy, and compute strict-social bypass (no text mutation)."""
    out = dict(gm)
    policy = _normalize_response_policy_input(response_policy)
    scene_id = _scene_id_from_scene_envelope(scene_envelope)
    strict_social_turn = strict_social_emission_will_apply(resolution, session, world, scene_id)
    return out, policy, strict_social_turn


def validate_gm_state_update(
    gm: Dict[str, Any],
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate and normalize GM-proposed state updates.

    - Enforces allowlisted keys for scene_update/world_updates/new_scene_draft.
    - Clamps text lengths.
    - Prevents hidden facts from being promoted into visible_facts.
    """
    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)

    scene = (scene_envelope or {}).get('scene', {}) if isinstance(scene_envelope, dict) else {}
    existing_hidden = {
        str(h).strip()
        for h in scene.get('hidden_facts', [])
        if isinstance(h, str) and h.strip()
    }

    def _norm_str_list(val: Any, max_len: int = 500, max_items: int = 16) -> List[str]:
        out: List[str] = []
        if isinstance(val, list):
            for item in val:
                if not isinstance(item, str):
                    continue
                s = item.strip()
                if not s:
                    continue
                if len(s) > max_len:
                    s = s[:max_len]
                if s not in out:
                    out.append(s)
                if len(out) >= max_items:
                    break
        return out

    debug_reasons: List[str] = []

    su = gm.get('scene_update')
    if isinstance(su, dict):
        cleaned: Dict[str, Any] = {}
        vis_add = _norm_str_list(su.get('visible_facts_add'))
        # Block promotion: do not allow exact hidden facts to become visible via update.
        filtered_vis = []
        for v in vis_add:
            if v in existing_hidden:
                debug_reasons.append('validator:hidden_fact_promotion_blocked')
                continue
            filtered_vis.append(v)
        if filtered_vis:
            cleaned['visible_facts_add'] = filtered_vis

        disc_add = _norm_str_list(su.get('discoverable_clues_add'))
        if disc_add:
            cleaned['discoverable_clues_add'] = disc_add

        hid_add = _norm_str_list(su.get('hidden_facts_add'))
        if hid_add:
            cleaned['hidden_facts_add'] = hid_add

        mode = su.get('mode')
        if isinstance(mode, str) and mode in {'exploration', 'combat', 'social', 'travel'}:
            cleaned['mode'] = mode

        gm['scene_update'] = cleaned or None

    wu = gm.get('world_updates')
    if isinstance(wu, dict):
        from game.models import canonical_world_update_is_effectively_empty, normalize_runtime_world_updates

        norm = normalize_runtime_world_updates(wu)
        gm['world_updates'] = None if canonical_world_update_is_effectively_empty(norm) else norm

    nd = gm.get('new_scene_draft')
    if isinstance(nd, dict):
        # Normalize minimal allowed shape.
        draft = {
            'id': nd.get('id'),
            'location': str(nd.get('location', '') or '').strip()[:200],
            'summary': str(nd.get('summary', '') or '').strip()[:800],
            'mode': nd.get('mode', 'exploration'),
            'visible_facts': _norm_str_list(nd.get('visible_facts')),
            'discoverable_clues': _norm_str_list(nd.get('discoverable_clues')),
            'hidden_facts': _norm_str_list(nd.get('hidden_facts')),
            'exits': nd.get('exits') if isinstance(nd.get('exits'), list) else [],
            'enemies': nd.get('enemies') if isinstance(nd.get('enemies'), list) else [],
        }
        # Sanitize/derive id.
        draft['id'] = draft['id'] or slugify(draft['location'] or 'new_scene')
        gm['new_scene_draft'] = draft

    if debug_reasons:
        dbg = gm.get('debug_notes')
        if not isinstance(dbg, str):
            dbg = ''
        reason_text = ','.join(debug_reasons)
        gm['debug_notes'] = (dbg + ' | ' if dbg else '') + reason_text

    return gm


def _apply_forbid_state_invention_validation(
    gm_dict: Dict[str, Any],
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """Validation-only branch for ``forbid_state_invention`` (no player-facing prose)."""
    return validate_gm_state_update(gm_dict, session, scene_envelope)


def _project_fallback_behavior_contract_metadata(
    out: Dict[str, Any],
    fallback_behavior: Dict[str, Any],
) -> None:
    """Project ``fallback_behavior`` into ``metadata.emission_debug`` (metadata-only)."""
    md = out.setdefault("metadata", {})
    if not isinstance(md, dict):
        return
    em = md.setdefault("emission_debug", {})
    if not isinstance(em, dict):
        return
    fb = fallback_behavior
    em["fallback_behavior_contract"] = {
        "enabled": bool(fb.get("enabled")),
        "uncertainty_active": bool(fb.get("uncertainty_active")),
        "uncertainty_mode": fb.get("uncertainty_mode"),
        "uncertainty_sources": list(fb.get("uncertainty_sources") or []),
        "allowed_behaviors": dict(fb.get("allowed_behaviors") or {}),
        "prefer_partial_over_question": bool(fb.get("prefer_partial_over_question")),
    }


def _snapshot_response_policy_and_project_fallback_contract(
    out: Dict[str, Any],
    policy: Dict[str, Any],
) -> None:
    """Store ``response_policy`` on ``out`` and project fallback contract metadata (no prose changes)."""
    out["response_policy"] = dict(policy)
    fb = policy.get("fallback_behavior")
    if isinstance(fb, dict):
        _project_fallback_behavior_contract_metadata(out, fb)


def _mark_response_policy_enforcement_applied(out: Dict[str, Any]) -> None:
    """Set the defense-in-depth marker on metadata (metadata-only)."""
    md = out.setdefault("metadata", {})
    if isinstance(md, dict):
        md[GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED] = True


def _apply_must_answer_question_resolution_enforcement(
    out: Dict[str, Any],
    *,
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """``must_answer`` / question-resolution completeness pass (deterministic; snapshot-covered)."""
    return enforce_question_resolution_rule(
        out,
        player_text=player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )


def enforce_question_resolution_rule(
    gm: Dict[str, Any],
    *,
    player_text: str,
    scene_envelope: Dict[str, Any] | None = None,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Last-resort deterministic compliance with Question Resolution Rule.

    If the player asked a direct question and the reply doesn't start with an explicit
    answer, prepend a grounded uncertain answer plus a concrete next step.
    """
    from game.gm import (
        _apply_uncertainty_to_gm,
        classify_uncertainty,
        question_resolution_rule_check,
    )

    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    reply = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    chk = question_resolution_rule_check(
        player_text=player_text,
        gm_reply_text=reply,
        resolution=resolution,
    )
    if not chk.get("applies") or chk.get("ok"):
        return gm

    out = _apply_uncertainty_to_gm(
        gm,
        uncertainty=classify_uncertainty(
            player_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        ),
        reason=f"question_resolution_rule:enforced:{chk.get('reasons')}",
        replace_text=False,
        player_text=player_text,
    )
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    out["tags"] = list(tags) + ["question_resolution_rule"]
    return out


def enforce_no_validator_voice(
    gm: Dict[str, Any],
    *,
    scene_envelope: Dict[str, Any],
    player_text: str,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministically remove system/validator wording from player-facing text.

    Uses :func:`detect_validator_voice` as the single policy registry for this class of violations.
    Final scaffold/procedural/analytical phrase cleanup belongs to ``game.output_sanitizer`` after
    the emission pipeline; this pass runs inside :func:`apply_response_policy_enforcement`.
    """
    from game.gm import (
        _apply_uncertainty_to_gm,
        _is_direct_player_question,
        _split_reply_sentences,
        _validator_voice_world_fallback,
        classify_uncertainty,
    )

    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    txt = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    if not txt.strip():
        return gm

    hits = detect_validator_voice(txt)
    if not hits:
        return gm

    if _is_direct_player_question(player_text):
        gm = _apply_uncertainty_to_gm(
            gm,
            uncertainty=classify_uncertainty(
                player_text,
                scene_envelope=scene_envelope,
                session=session,
                world=world,
                resolution=resolution,
            ),
            reason=f"validator_voice_rewrite:{hits}",
            replace_text=True,
            player_text=player_text,
        )
        tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
        gm["tags"] = list(tags) + ["validator_voice_rewrite"]
        return gm

    clean_sentences = [
        sentence for sentence in _split_reply_sentences(txt)
        if not detect_validator_voice(sentence)
    ]
    rewritten = " ".join(clean_sentences).strip()
    if not rewritten or detect_validator_voice(rewritten):
        rewritten = _validator_voice_world_fallback(
            scene_envelope=scene_envelope,
            player_text=player_text,
            session=session,
            world=world,
            resolution=resolution,
        )

    gm["player_facing_text"] = rewritten.strip()
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    gm["tags"] = list(tags) + ["validator_voice_rewrite"]
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    gm["debug_notes"] = (dbg + " | " if dbg else "") + f"validator_voice_rewrite:{hits}"
    return gm


def _apply_diegetic_validator_voice_enforcement(
    out: Dict[str, Any],
    *,
    scene_envelope: Dict[str, Any],
    player_text: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """``diegetic_only`` validator-voice removal (snapshot-covered; internal fallback unchanged)."""
    return enforce_no_validator_voice(
        out,
        scene_envelope=scene_envelope,
        player_text=player_text,
        session=session,
        world=world,
        resolution=resolution,
    )


_FORBIDDEN_GENERIC_PHRASE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bin this city\b", re.IGNORECASE), "in_this_city"),
    (re.compile(r"\btimes are tough\b", re.IGNORECASE), "times_are_tough"),
    (re.compile(r"\btrust is hard to come by\b", re.IGNORECASE), "trust_is_hard_to_come_by"),
(re.compile(r"\byou[’']ll need to prove yourself\b", re.IGNORECASE), "prove_yourself"),
)


def detect_forbidden_generic_phrases(player_facing_text: str) -> List[str]:
    """Detect forbidden stock RPG phrases that must be rewritten when present.

    Unlike detect_stock_warning_filler_repetition(), this triggers on a single
    occurrence because these phrases are considered hard failures.
    """
    if not isinstance(player_facing_text, str):
        return []
    txt = " ".join(player_facing_text.split())
    if not txt:
        return []
    hits: List[str] = []
    for pattern, label in _FORBIDDEN_GENERIC_PHRASE_PATTERNS:
        if pattern.search(txt):
            hits.append(f"forbidden_generic:{label}")
    return hits


def npc_response_contract_check(
    *,
    player_text: str,
    npc_reply_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Check the NPC response contract for direct questions to an NPC.

    Returns:
      {applies: bool, ok: bool, reasons: [str], missing: [str]}
    """
    from game.gm import (
        _NPC_CONTRACT_ACTION_TOKENS,
        _NPC_CONTRACT_REQUIREMENT_TOKENS,
        _NPC_CONTRACT_TIME_TOKENS,
        _QUESTION_WORDS,
        _active_interaction_target_id,
        _in_scene_npc_names,
        _resolve_npc_name,
        _resolve_scene_id,
        _resolve_scene_location,
        _world_faction_names,
    )

    player = str(player_text or "").strip()
    reply = str(npc_reply_text or "").strip()
    low_player = player.lower()
    low_reply = reply.lower()

    scene_id = _resolve_scene_id(scene_envelope)
    location = _resolve_scene_location(scene_envelope)

    res = resolution if isinstance(resolution, dict) else {}
    social = res.get("social") if isinstance(res.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    if not npc_id:
        npc_id = _active_interaction_target_id(session)
    has_npc_target = bool(npc_id)

    # "Asked a question" heuristic: direct question mark or leading question word.
    first_word = (low_player.replace('"', ' ').replace("'", " ").split() or [""])[0]
    is_question = ("?" in low_player) or (first_word in _QUESTION_WORDS)

    applies = bool(has_npc_target and is_question)
    if not applies:
        return {"applies": False, "ok": True, "reasons": [], "missing": []}

    npc_name = str(social.get("npc_name") or "").strip() or _resolve_npc_name(world, npc_id, scene_id)
    faction_names = _world_faction_names(world)
    other_npc_names = _in_scene_npc_names(world, scene_id)

    specific_tokens: List[str] = []
    if npc_name:
        specific_tokens.append(npc_name)
    if location:
        specific_tokens.append(location)
    specific_tokens.extend(faction_names)
    specific_tokens.extend(other_npc_names)
    specific_tokens = [t for t in specific_tokens if isinstance(t, str) and t.strip()]

    has_specific = any(t.lower() in low_reply for t in specific_tokens if len(t) >= 4)
    has_next_step = any(tok in low_reply for tok in _NPC_CONTRACT_ACTION_TOKENS)
    has_requirement = any(tok in low_reply for tok in _NPC_CONTRACT_REQUIREMENT_TOKENS)
    has_time = any(tok in low_reply for tok in _NPC_CONTRACT_TIME_TOKENS) or bool(re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", low_reply))
    has_usable_info = bool(has_requirement or has_time or (" at " in low_reply and len(low_reply) >= 30))

    ok = bool(has_specific or has_next_step or has_usable_info)

    missing: List[str] = []
    if not has_specific:
        missing.append("specific_person_place_or_faction")
    if not has_next_step:
        missing.append("concrete_next_step")
    if not has_usable_info:
        missing.append("usable_info")

    reasons: List[str] = []
    if not reply:
        reasons.append("npc_contract:empty_reply")
    if not ok:
        reasons.append("npc_contract:missing_required_specificity")
    return {"applies": True, "ok": ok, "reasons": reasons, "missing": missing}


def _contract_fallback_next_step(scene_envelope: Dict[str, Any], *, npc_name: str, location: str) -> str:
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    visible = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    visible_low = " ".join(str(v).lower() for v in visible if isinstance(v, str))

    if "notice board" in visible_low or "noticeboard" in visible_low:
        loc_phrase = f" in {location}" if location else ""
        return f"Next step: check the notice board{loc_phrase} for the posted names, times, and requirements."
    if exits and isinstance(exits[0], dict) and str(exits[0].get("label") or "").strip():
        label = str(exits[0].get("label") or "").strip()
        return f"Next step: take the exit labeled “{label}” and follow up there."
    if npc_name:
        loc_phrase = f" here in {location}" if location else " here"
        return f"Next step: press {npc_name}{loc_phrase} for a name, a place, or a condition—something you can act on immediately."
    if location:
        return f"Next step: pick a concrete lead in {location} (a posted notice, a guard post, or a shopfront) and ask one targeted question."
    return "Next step: ask a targeted follow-up question that names a person or place, or seek a specific posted notice."


def enforce_npc_response_contract(
    gm: Dict[str, Any],
    *,
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Ensure NPC replies to questions contain concrete specificity.

    This is a last-resort, deterministic patch: it never adds hidden facts.
    """
    from game.gm import (
        _active_interaction_target_id,
        _resolve_npc_name,
        _resolve_scene_id,
        _resolve_scene_location,
    )

    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    reply = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    chk = npc_response_contract_check(
        player_text=player_text,
        npc_reply_text=reply,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    if not chk.get("applies") or chk.get("ok"):
        return gm

    scene_id = _resolve_scene_id(scene_envelope)
    location = _resolve_scene_location(scene_envelope)
    res = resolution if isinstance(resolution, dict) else {}
    social = res.get("social") if isinstance(res.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip() or _active_interaction_target_id(session)
    npc_name = str(social.get("npc_name") or "").strip() or _resolve_npc_name(world, npc_id, scene_id)
    addition = _contract_fallback_next_step(scene_envelope, npc_name=npc_name, location=location)

    txt = reply.strip()
    if txt and not txt.endswith((".", "!", "?", "…")):
        txt += "."
    txt = (txt + ("\n\n" if txt else "") + addition).strip()
    gm["player_facing_text"] = txt

    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    gm["tags"] = list(tags) + ["npc_response_contract"]
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    gm["debug_notes"] = (dbg + " | " if dbg else "") + f"npc_response_contract:enforced:{chk.get('missing')}"
    return gm


def _generic_phrase_replacement_sentence(
    *,
    label: str,
    location: str,
    npc_name: str,
    scene_visible_facts: List[str],
) -> str:
    loc = (location or "").strip()
    npc = (npc_name or "").strip()
    who = npc or "The local voice"
    loc_phrase = f" in {loc}" if loc else ""

    visible_low = " ".join(str(v).lower() for v in (scene_visible_facts or []) if isinstance(v, str))
    has_notice = ("notice board" in visible_low) or ("noticeboard" in visible_low)
    has_missing_patrol = "missing patrol" in visible_low
    has_tavern_runner = (
        ("tavern runner" in visible_low)
        or ("tavern" in visible_low and "runner" in visible_low)
        or ("rumor" in visible_low)
        or ("rumour" in visible_low)
    )
    has_refugees = "refugee" in visible_low

    if label == "in_this_city":
        if has_notice and has_missing_patrol:
            return f"{who}{loc_phrase} gestures to the notice board: taxes, curfews, and the missing patrol posting are the only things anyone is taking seriously."
        if has_notice:
            return f"{who}{loc_phrase} points you at the notice board—the posted taxes and curfews are the rules that actually matter here."
        return f"{who}{loc_phrase} keeps it specific: names, postings, and witnesses decide what happens next—not vague warnings."

    if label == "times_are_tough":
        if has_notice:
            return f"{who}{loc_phrase} doesn’t bother with platitudes—new taxes and curfews are posted, and enforcement is immediate."
        return f"{who}{loc_phrase} skips the sermon and looks for something actionable: a name, a place, or a consequence."

    if label == "trust_is_hard_to_come_by":
        leads: List[str] = []
        if has_notice:
            leads.append("a name off the notice board")
        if has_refugees:
            leads.append("a witness from the refugee line")
        if has_tavern_runner:
            leads.append("one specific rumor bought from the tavern runner")
        lead_phrase = "; or ".join(leads[:2]) if leads else "a named person or posted notice"
        return f"{who}{loc_phrase} makes it procedural, not moral: bring {lead_phrase}, and they can act without guessing."

    if label == "prove_yourself":
        leads2: List[str] = []
        if has_notice:
            leads2.append("a name off the notice board")
        if has_missing_patrol:
            leads2.append("a concrete detail tied to the missing patrol notice")
        if has_tavern_runner:
            leads2.append("one rumor with a source")
        if has_refugees:
            leads2.append("a witness who’ll say it out loud")
        lead_phrase2 = "; or ".join(leads2[:2]) if leads2 else "a concrete lead with a name and place"
        return f"{who}{loc_phrase} sets a clear bar: return with {lead_phrase2}, and the conversation changes immediately."

    # Fallback (should not happen).
    return f"{who}{loc_phrase} replaces the vague line with something concrete the player can act on right now."


def enforce_forbidden_generic_phrases(
    gm: Dict[str, Any],
    *,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
) -> Dict[str, Any]:
    """Deterministically rewrite forbidden generic phrases into scene-anchored specificity.

    This pass rewrites only sentences that contain forbidden phrases, using
    existing visible facts + known NPC names. It never introduces hidden facts.
    """
    from game.gm import (
        _active_interaction_target_id,
        _resolve_npc_name,
        _resolve_scene_id,
        _resolve_scene_location,
    )

    if not isinstance(gm, dict):
        return gm
    gm = dict(gm)
    txt = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    hits = detect_forbidden_generic_phrases(txt)
    if not hits:
        return gm

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    visible = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
    scene_id = _resolve_scene_id(scene_envelope)
    location = _resolve_scene_location(scene_envelope)
    npc_id = _active_interaction_target_id(session)
    npc_name = _resolve_npc_name(world, npc_id, scene_id)

    # Rewrite at sentence granularity to avoid awkward partial substitutions.
    paragraphs = [p for p in str(txt or "").split("\n\n")]
    rewritten_paras: List[str] = []
    for para in paragraphs:
        sents = [s for s in re.split(r"(?<=[.!?])\s+", para.strip()) if s]
        out_sents: List[str] = []
        for s in sents:
            matched_labels: List[str] = []
            for pattern, label in _FORBIDDEN_GENERIC_PHRASE_PATTERNS:
                if pattern.search(s):
                    matched_labels.append(label)
            if not matched_labels:
                out_sents.append(s)
                continue
            rep = _generic_phrase_replacement_sentence(
                label=matched_labels[0],
                location=location,
                npc_name=npc_name,
                scene_visible_facts=[str(v) for v in visible if isinstance(v, str)],
            )
            if rep and not rep.endswith((".", "!", "?", "…")):
                rep += "."
            out_sents.append(rep)
        rewritten_paras.append(" ".join(out_sents).strip())
    new_txt = "\n\n".join([p for p in rewritten_paras if p]).strip()

    if new_txt and new_txt != txt:
        gm["player_facing_text"] = new_txt
        tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
        gm["tags"] = list(tags) + ["forbidden_generic_rewrite"]
        dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
        gm["debug_notes"] = (dbg + " | " if dbg else "") + f"forbidden_generic_rewrite:{hits}"
    return gm


def _apply_prefer_specificity_text_enforcement(
    out: Dict[str, Any],
    *,
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """NPC contract enforcement then forbidden-generic rewrite (fixed pair order; snapshot-covered)."""
    out = enforce_npc_response_contract(
        out,
        player_text=player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    out = enforce_forbidden_generic_phrases(
        out,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
    )
    return out


def sanitize_player_facing_text(
    player_text: str,
    scene_envelope: Dict[str, Any],
    user_text: str,
    discovered_clues: List[str] | None = None,
    *,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Deterministic leak guard against obvious hidden-fact disclosure.

    This is intentionally simple: it catches exact/near-exact reuse of distinctive
    hidden-fact phrasing and a few high-signal keywords.
    """
    from game.gm import (
        _bounded_spoiler_safe_text,
        _is_direct_player_question,
        _scene_layers,
        _session_social_authority,
        classify_player_intent,
        classify_uncertainty,
        normalize_clue_record,
    )
    from game.social_exchange_fallback_catalog import minimal_social_emergency_fallback_line
    from game.social_exchange_policy import effective_strict_social_resolution_for_emission

    public_scene, discoverable, hidden = _scene_layers(scene_envelope)
    _ = public_scene  # kept for future extensions; not used yet

    txt = player_text or ''
    low = txt.lower()

    intent = classify_player_intent(user_text)
    allow_disc = bool(intent.get('allow_discoverable_clues'))
    discovered_set = {s.lower().strip() for s in (discovered_clues or []) if isinstance(s, str)}

    # Hidden fact phrase reuse (exact / near-exact tokens).
    hit_reasons: List[str] = []
    for hf in hidden:
        if not isinstance(hf, str) or not hf.strip():
            continue
        hf_low = hf.lower().strip()
        # If the model repeats most of a hidden fact verbatim, treat as a leak.
        if hf_low in low:
            hit_reasons.append('spoiler_guard:hidden_fact_exact')
            break

    # High-signal frontier_gate regression keywords (and general obvious leaks).
    keyword_leaks = ('noble house', 'smuggler', 'magical talent')
    if any(k in low for k in keyword_leaks):
        hit_reasons.append('spoiler_guard:hidden_fact_keyword')

    # Discoverable clues must not appear unless player justified investigation,
    # except if they were already discovered previously.
    if discoverable:
        for raw_clue in discoverable:
            rec = normalize_clue_record(raw_clue)
            clue_low = rec['text'].lower().strip()
            if not clue_low:
                continue
            if clue_low in low:
                if clue_low in discovered_set:
                    # Already discovered: always allowed.
                    continue
                if not allow_disc:
                    hit_reasons.append('spoiler_guard:undiscovered_clue_without_investigation')
                    break

    if not hit_reasons:
        return {'text': txt, 'did_sanitize': False, 'reasons': []}

    scene_id = ""
    if isinstance(scene_envelope, dict):
        sc = scene_envelope.get("scene")
        if isinstance(sc, dict):
            scene_id = str(sc.get("id") or "").strip()
    eff_res, strict_route, _ = effective_strict_social_resolution_for_emission(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        scene_id,
    )
    if strict_route and isinstance(eff_res, dict):
        safe = minimal_social_emergency_fallback_line(eff_res)
        return {'text': safe, 'did_sanitize': True, 'reasons': hit_reasons, 'uncertainty': None}

    if _session_social_authority(session):
        safe = _bounded_spoiler_safe_text(
            user_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        )
        return {'text': safe, 'did_sanitize': True, 'reasons': hit_reasons, 'uncertainty': None}

    uncertainty = (
        classify_uncertainty(
            user_text,
            scene_envelope=scene_envelope,
            session=session,
            world=world,
            resolution=resolution,
        )
        if _is_direct_player_question(user_text)
        else None
    )
    safe = _bounded_spoiler_safe_text(
        user_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    return {'text': safe, 'did_sanitize': True, 'reasons': hit_reasons, 'uncertainty': uncertainty}


def guard_gm_output(
    gm: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    user_text: str,
    discovered_clues: List[str] | None = None,
    *,
    session: Dict[str, Any] | None = None,
    world: Dict[str, Any] | None = None,
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Apply leak guard and annotate debug_notes/tags without breaking schema."""
    if not isinstance(gm, dict):
        return gm
    # Avoid mutating caller-owned dicts (easier to test and safer for reuse).
    gm = dict(gm)
    pft = gm.get('player_facing_text') if isinstance(gm.get('player_facing_text'), str) else ''
    res = sanitize_player_facing_text(
        pft,
        scene_envelope,
        user_text,
        discovered_clues,
        session=session,
        world=world,
        resolution=resolution,
    )
    if not res['did_sanitize']:
        return gm

    tags = gm.get('tags') if isinstance(gm.get('tags'), list) else []
    uncertainty = res.get('uncertainty') if isinstance(res.get('uncertainty'), dict) else {}
    known_fact = uncertainty.get("known_fact") if isinstance(uncertainty.get("known_fact"), dict) else {}
    category = str(uncertainty.get('category') or '').strip()
    if known_fact:
        gm['tags'] = list(tags) + ['spoiler_guard', 'known_fact_guard']
    else:
        uncertainty_tags = [f'uncertainty:{category}'] if category else []
        gm['tags'] = list(tags) + ['spoiler_guard'] + uncertainty_tags
    gm['player_facing_text'] = res['text']
    dbg = gm.get('debug_notes') if isinstance(gm.get('debug_notes'), str) else ''
    if known_fact:
        source = str(known_fact.get("source") or "known_fact").strip()
        gm['debug_notes'] = (dbg + ' | ' if dbg else '') + f'spoiler_guard: {res["reasons"]} | known_fact_guard:{source}'
    else:
        gm['debug_notes'] = (dbg + ' | ' if dbg else '') + f'spoiler_guard: {res["reasons"]}'
    return gm


def _apply_forbid_secret_leak_guard(
    out: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    player_text: str,
    discovered_clues: List[str] | None,
    *,
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """``forbid_secret_leak`` branch — ``guard_gm_output`` (snapshot-covered)."""
    return guard_gm_output(
        out,
        scene_envelope,
        player_text,
        discovered_clues,
        session=session,
        world=world,
        resolution=resolution,
    )

_TOPIC_SOCIAL_ESCALATION_STANCES: tuple[str, ...] = (
    "irritation",
    "guarded_refusal",
    "contradiction",
    "partial_reveal",
    "urgent_redirect",
    "end_conversation_threat",
    "suspicious_evasion",
    "withdrawal",
)

def _reply_has_escalation_motion(gm_reply: Dict[str, Any]) -> bool:
    from game.gm import _TOPIC_ESCALATION_CUES, _extract_scene_momentum_kind

    if _extract_scene_momentum_kind(gm_reply):
        return True
    text = str((gm_reply or {}).get("player_facing_text") or "")
    if not text.strip():
        return False
    return any(pattern.search(text) for pattern in _TOPIC_ESCALATION_CUES)

def _pressure_first_sentence_answer(player_text: str) -> str:
    low = " ".join(str(player_text or "").strip().lower().split())
    if low.startswith("who ") or low.startswith("who's ") or low.startswith("who is "):
        return "No, I do not have a name for you."
    if low.startswith("where "):
        return "No, I cannot point you to a confirmed location."
    if low.startswith("when "):
        return "No, I do not have a time I trust enough to give you."
    if low.startswith("why "):
        return "No, I do not know their motive well enough to name it."
    if low.startswith("how "):
        return "No, I do not know the method and I will not invent one."
    if low.startswith("what "):
        return "No, I cannot give you a clean account yet."
    return "No, I do not have a reliable answer I can stand behind."

def _is_social_topic_route(topic_context: Dict[str, Any]) -> bool:
    social_intent_class = str(topic_context.get("social_intent_class") or "").strip().lower()
    interaction_kind = str(topic_context.get("interaction_kind") or "").strip().lower()
    interaction_mode = str(topic_context.get("interaction_mode") or "").strip().lower()
    return social_intent_class == "social_exchange" or interaction_kind == "social" or interaction_mode == "social"

def _social_escalation_stance(topic_key: str, speaker_key: str, speaker_repeat_count: int) -> str:
    base = max(0, int(speaker_repeat_count or 0) - 3)
    seed = sum(ord(ch) for ch in f"{topic_key}:{speaker_key}")
    idx = (seed + base) % len(_TOPIC_SOCIAL_ESCALATION_STANCES)
    return _TOPIC_SOCIAL_ESCALATION_STANCES[idx]

def _render_topic_pressure_escalation(
    *,
    player_text: str,
    topic_key: str,
    speaker_key: str,
    topic_context: Dict[str, Any] | None = None,
) -> tuple[str, str]:
    topic_ctx = topic_context if isinstance(topic_context, dict) else {}
    if _is_social_topic_route(topic_ctx):
        speaker_label = str(topic_ctx.get("npc_name") or "").strip() or speaker_key.replace("_", " ").strip() or "The speaker"
        speaker_repeat_count = int(topic_ctx.get("speaker_repeat_count", 0) or 0)
        stance = _social_escalation_stance(topic_key, speaker_key, speaker_repeat_count)
        first_sentence = _pressure_first_sentence_answer(player_text)
        if stance == "irritation":
            return (
                "consequence_or_opportunity",
                f"{speaker_label} snaps back, \"{first_sentence} Stop grinding the same point and bring me something I can use.\"",
            )
        if stance == "guarded_refusal":
            return (
                "consequence_or_opportunity",
                f"{speaker_label} says, \"{first_sentence} I am not discussing names in the open.\" They lower their voice and add, \"Meet me by the north brazier after dusk if you want more.\"",
            )
        if stance == "contradiction":
            return (
                "new_information",
                f"{speaker_label} cuts in, \"{first_sentence} You are pressing the wrong angle: the trail broke east of the crossroads marker, not in the square.\"",
            )
        if stance == "partial_reveal":
            return (
                "new_information",
                f"{speaker_label} says, \"{first_sentence}\" Then they glance over your shoulder. \"All I can give you is this: the pay chit carried a black ash-wax seal.\"",
            )
        if stance == "urgent_redirect":
            return (
                "time_pressure",
                f"{speaker_label} says, \"{first_sentence}\" They lean in. \"If you want the next piece, get to the mill yard before dawn and question the night carter.\"",
            )
        if stance == "end_conversation_threat":
            return (
                "consequence_or_opportunity",
                f"{speaker_label} hardens and says, \"{first_sentence} Press me on this one more time and this conversation is over.\"",
            )
        if stance == "suspicious_evasion":
            return (
                "consequence_or_opportunity",
                f"{speaker_label}'s expression turns flat as they answer, \"{first_sentence} There was no 'mastermind' here worth naming, so drop it.\"",
            )
        return (
            "environmental_change",
            f"{speaker_label} says, \"{first_sentence}\" They step back, break eye contact, and withdraw into the crowd before you can press further.",
        )

    speaker_text = "The speaker"
    if speaker_key and speaker_key not in {"__scene__", "none"}:
        speaker_text = speaker_key.replace("_", " ")
    if topic_key == "missing_patrol":
        return (
            "new_information",
            "A mud-streaked runner shoulders through the crowd and thrusts a torn patrol strip into your hand: "
            "\"East road marker, less than an hour old.\" The rumor stops being abstract.",
        )
    if topic_key == "shadowy_figures":
        return (
            "new_actor_entering",
            "A dockhand cuts in, voice low: \"I saw two hooded figures break from the crossroads toward the shuttered bathhouse.\" "
            "A witness is now on the table.",
        )
    if topic_key == "crossroads_incident":
        return (
            "environmental_change",
            "A cart wheel snaps outside and people shout; guards surge toward the crossroads lane, forcing a decision now.",
        )
    return (
        "consequence_or_opportunity",
        f"{speaker_text.capitalize()} goes hard-evasive and shuts down further circular questions. "
        "They give one actionable redirect instead: move now to the nearest witness, trail, or notice before it goes cold.",
    )

def enforce_topic_pressure_escalation(
    gm: Dict[str, Any],
    *,
    player_text: str,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """Force diegetic scene motion when a topic has been pressed repeatedly with low progress."""
    from game.gm import (
        _extract_scene_momentum_kind,
        _is_direct_player_question,
        _topic_pressure_snapshot_for_reply,
    )
    from game.storage import SCENE_MOMENTUM_TAG_PREFIX

    if not isinstance(gm, dict):
        return gm
    if not _is_direct_player_question(player_text):
        return gm
    pressure = _topic_pressure_snapshot_for_reply(
        session=session,
        scene_envelope=scene_envelope,
        reply_text=str(gm.get("player_facing_text") or ""),
    )
    if not pressure.get("applies") or pressure.get("ok"):
        return gm
    if _reply_has_escalation_motion(gm):
        return gm
    topic_ctx = pressure.get("topic_context") if isinstance(pressure.get("topic_context"), dict) else {}
    topic_key = str(topic_ctx.get("topic_key") or "").strip() or "topic:unknown"
    speaker_key = str(topic_ctx.get("speaker_key") or "__scene__").strip() or "__scene__"
    kind, beat = _render_topic_pressure_escalation(
        player_text=player_text,
        topic_key=topic_key,
        speaker_key=speaker_key,
        topic_context=topic_ctx,
    )
    out = dict(gm)
    text = str(out.get("player_facing_text") or "").strip()
    if _is_social_topic_route(topic_ctx):
        out["player_facing_text"] = beat.strip()
    else:
        out["player_facing_text"] = (text + ("\n\n" if text else "") + beat).strip()
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    next_tags = list(tags)
    if not _extract_scene_momentum_kind(out):
        next_tags.append(f"{SCENE_MOMENTUM_TAG_PREFIX}{kind}")
    if "topic_pressure_escalation" not in next_tags:
        next_tags.append("topic_pressure_escalation")
    out["tags"] = next_tags
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + f"topic_pressure_escalation:topic={topic_key}:repeat={topic_ctx.get('repeat_count')}:progress={topic_ctx.get('progress_score')}"
    )
    return out

def _apply_topic_pressure_escalation_enforcement(
    out: Dict[str, Any],
    *,
    player_text: str,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """First step of ``prefer_scene_momentum`` — topic-pressure escalation."""
    return enforce_topic_pressure_escalation(
        out,
        player_text=player_text,
        session=session,
        scene_envelope=scene_envelope,
    )

def _reply_already_has_concrete_interaction(text: str) -> bool:
    from game.gm import _CONCRETE_INTERACTION_PATTERNS

    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)

def _scene_snapshot_has_tension(
    scene_snapshot: Dict[str, Any],
    runtime: Dict[str, Any],
    session: Dict[str, Any] | None = None,
) -> bool:
    from game.gm import _SCENE_TENSION_PATTERNS
    from game.leads import filter_pending_leads_for_active_follow_surface

    visible_text = " ".join(
        str(item)
        for item in (scene_snapshot.get("visible_facts") or [])
        if isinstance(item, str)
    )
    if any(pattern.search(visible_text) for pattern in _SCENE_TENSION_PATTERNS):
        return True
    if scene_snapshot.get("has_missing_patrol") or scene_snapshot.get("has_notice_board"):
        return True
    if scene_snapshot.get("has_refugees") or scene_snapshot.get("has_tax_or_curfew"):
        return True
    pending_raw = runtime.get("pending_leads") or []
    pending_active = (
        filter_pending_leads_for_active_follow_surface(session, pending_raw)
        if isinstance(session, dict)
        else bool(pending_raw)
    )
    if pending_active or runtime.get("suspicion_flags"):
        return True
    recent = scene_snapshot.get("recent_contextual_leads")
    return bool(recent)

def _pick_passive_pressure_source(
    scene_snapshot: Dict[str, Any],
    speaker: Dict[str, Any],
) -> Dict[str, Any]:
    from game.gm import _extract_visible_figure_candidate

    recent_leads = scene_snapshot.get("recent_contextual_leads")
    if isinstance(recent_leads, list):
        for lead in reversed(recent_leads[-4:]):
            if not isinstance(lead, dict):
                continue
            kind = str(lead.get("kind") or "").strip()
            if kind in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
                return {
                    "source": "lead_figure",
                    "subject": str(lead.get("subject") or "").strip(),
                    "position": str(lead.get("position") or "").strip(),
                    "kind": kind,
                }

    pending = scene_snapshot.get("pending_leads")
    if isinstance(pending, list):
        for lead in pending[:3]:
            if not isinstance(lead, dict):
                continue
            subject = str(
                lead.get("leads_to_npc")
                or lead.get("leads_to_rumor")
                or lead.get("text")
                or lead.get("leads_to_scene")
                or ""
            ).strip()
            if subject:
                return {
                    "source": "pending_lead",
                    "subject": subject,
                    "position": "",
                    "kind": "pending_clue",
                }

    visible_facts = scene_snapshot.get("visible_facts")
    if isinstance(visible_facts, list):
        for fact in visible_facts[:8]:
            candidate = _extract_visible_figure_candidate(str(fact))
            if candidate and str(candidate.get("subject") or "").strip():
                return {
                    "source": "visible_figure",
                    "subject": str(candidate.get("subject") or "").strip(),
                    "position": str(candidate.get("position") or "").strip(),
                    "kind": str(candidate.get("kind") or "visible_figure"),
                }

    if scene_snapshot.get("has_missing_patrol"):
        return {
            "source": "guard_rumor",
            "subject": "the missing patrol notice",
            "position": "",
            "kind": "active_event",
        }

    speaker_name = str(speaker.get("name") or "").strip()
    if str(speaker.get("role") or "").strip().lower() == "npc" and speaker_name:
        return {
            "source": "engaged_npc",
            "subject": speaker_name,
            "position": "",
            "kind": "engaged_npc",
        }

    for name in (scene_snapshot.get("other_npc_names") or [])[:2]:
        clean = str(name).strip()
        if clean:
            return {
                "source": "scene_npc",
                "subject": clean,
                "position": "",
                "kind": "scene_npc",
            }

    return {
        "source": "fallback",
        "subject": str(scene_snapshot.get("location") or "the gate").strip() or "the scene",
        "position": "",
        "kind": "fallback",
    }

def _render_passive_pressure_beat(
    *,
    source: Dict[str, Any],
    scene_snapshot: Dict[str, Any],
    passive_streak: int,
) -> tuple[str, str]:
    subject = str(source.get("subject") or "").strip() or "someone"
    position = str(source.get("position") or "").strip()
    source_key = str(source.get("source") or "").strip()
    move_from = f" leaves {position} and" if position else ""
    if source_key == "lead_figure":
        if passive_streak >= 2:
            text = (
                f"{subject}{move_from} comes straight to you before the pause can settle. "
                f"\"Enough watching,\" they say. \"Ask me now, or lose the trail.\""
            )
            return "consequence_or_opportunity", text
        text = (
            f"{subject}{move_from} cuts through the crowd and stops at your shoulder. "
            f"\"You're asking the wrong questions out loud,\" they murmur. \"Walk with me if you want the next name.\""
        )
        return "new_actor_entering", text
    if source_key == "pending_lead":
        text = (
            f"The lull breaks when a runner shoulders through the press with news tied to {subject}. "
            f"\"If you're moving on this, move now,\" they snap. \"The lead is still warm.\""
        )
        return "new_information", text
    if source_key == "visible_figure":
        if "guard" in subject.lower():
            if passive_streak >= 2:
                text = (
                    f"{subject.capitalize()} pushes off the wall and closes the gap before you can settle back into stillness. "
                    "\"No more staring,\" he says. \"State your business, or start with the road report now.\""
                )
                return "consequence_or_opportunity", text
            text = (
                f"{subject.capitalize()} notices you lingering and comes over at once. "
                "\"If you're waiting on trouble, it already passed the checkpoint,\" he says. \"Take the east-road report or get clear.\""
            )
            return "new_actor_entering", text
        if passive_streak >= 2:
            text = (
                f"{subject.capitalize()} finally breaks from watching and comes straight toward you. "
                "\"You can keep holding still, or you can ask the next useful question,\" they say."
            )
            return "consequence_or_opportunity", text
        text = (
            f"{subject.capitalize()} notices your attention and crosses the space between you. "
            "\"If you're looking for something, say it before the trail shifts,\" they say."
        )
        return "new_actor_entering", text
    if source_key == "guard_rumor":
        if passive_streak >= 2:
            text = (
                "The same guard does not let the silence stand a second time. "
                "\"No more watching,\" he says, closing the distance and jabbing a finger at the east-road line on the notice. "
                "\"Either tell me who sent you, or get moving before that trail cools for good.\""
            )
            return "consequence_or_opportunity", text
        text = (
            "A guard peels away from the notice board and squares up to you. "
            "\"Standing still won't help that patrol,\" he says, stabbing two fingers at the posting. "
            "\"Tell me what you know, or get on the east-road trail before it dies.\""
        )
        return "consequence_or_opportunity", text
    if source_key in {"engaged_npc", "scene_npc"}:
        text = (
            f"{subject} breaks the silence first. "
            f"\"Waiting won't sharpen this,\" they say. \"Question the runner, work the notice, or follow the road report now.\""
        )
        return "consequence_or_opportunity", text
    if scene_snapshot.get("has_notice_board"):
        text = (
            "Fresh ink draws a curse from the guards at the notice board. "
            "Someone has added a half-hour-old sighting to the missing patrol posting, and every eye nearby shifts toward the east road."
        )
        return "new_information", text
    text = (
        "The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "
        "\"Board, runner, or road,\" he says. \"Pick one before the gate swallows the trail.\""
    )
    return "consequence_or_opportunity", text

def escalate_passive_scene(
    gm: Dict[str, Any],
    *,
    player_text: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    resolution: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Turn passive pauses into direct scene pressure when the moment is stalling."""
    from game.gm import (
        _ensure_terminal_punctuation,
        _extract_scene_momentum_kind,
        build_uncertainty_render_context,
        classify_player_intent,
    )
    from game.storage import SCENE_MOMENTUM_TAG_PREFIX, get_scene_runtime

    if not isinstance(gm, dict):
        return gm
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return gm
    runtime = get_scene_runtime(session, scene_id)
    intent = classify_player_intent(player_text)
    labels = intent.get("labels") if isinstance(intent.get("labels"), list) else []
    current_passive = bool(runtime.get("last_player_action_passive")) or ("passive_pause" in labels)
    if not current_passive:
        return gm
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0)
    context = build_uncertainty_render_context(
        player_text,
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
    )
    scene_snapshot = context.get("scene_snapshot") if isinstance(context.get("scene_snapshot"), dict) else {}
    if passive_streak < 2 and not _scene_snapshot_has_tension(scene_snapshot, runtime, session):
        return gm
    text = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    if _reply_already_has_concrete_interaction(text):
        return gm
    source = _pick_passive_pressure_source(
        scene_snapshot,
        context.get("speaker") if isinstance(context.get("speaker"), dict) else {},
    )
    momentum_kind, beat = _render_passive_pressure_beat(
        source=source,
        scene_snapshot=scene_snapshot,
        passive_streak=passive_streak,
    )
    out = dict(gm)
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    new_tags = list(tags)
    if not _extract_scene_momentum_kind(out):
        new_tags.append(f"{SCENE_MOMENTUM_TAG_PREFIX}{momentum_kind}")
    if "passive_scene_pressure" not in new_tags:
        new_tags.append("passive_scene_pressure")
    out["tags"] = new_tags
    out["player_facing_text"] = (text.strip() + ("\n\n" if text.strip() else "") + _ensure_terminal_punctuation(beat)).strip()
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (dbg + " | " if dbg else "") + f"passive_scene_pressure:{source.get('source')}:streak={passive_streak}"
    return out

def _apply_escalate_passive_scene_enforcement(
    out: Dict[str, Any],
    *,
    player_text: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    resolution: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Second step of ``prefer_scene_momentum`` — passive stall pressure."""
    return escalate_passive_scene(
        out,
        player_text=player_text,
        session=session,
        world=world,
        scene_envelope=scene_envelope,
        resolution=resolution,
    )

def enforce_scene_momentum(gm: Dict[str, Any], *, session: Dict[str, Any], scene_envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic enforcement of the Scene Momentum Rule.

    If a momentum beat is due but the model did not tag it, append a safe
    consequence/opportunity beat grounded in existing visible facts/exits.
    """
    from game.diegetic_fallback_narration import render_scene_momentum_diegetic_append
    from game.gm import _extract_scene_momentum_kind, _scene_momentum_due
    from game.storage import SCENE_MOMENTUM_TAG_PREFIX

    if not isinstance(gm, dict):
        return gm
    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()
    if not scene_id:
        return gm

    if not _scene_momentum_due(session, scene_id):
        return gm

    if _extract_scene_momentum_kind(gm):
        return gm

    gm = dict(gm)
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    kind = "consequence_or_opportunity"
    gm["tags"] = list(tags) + [f"{SCENE_MOMENTUM_TAG_PREFIX}{kind}"]

    envelope = scene_envelope if isinstance(scene_envelope, dict) else {"scene": scene}
    opportunity = render_scene_momentum_diegetic_append(envelope, seed_key=scene_id or "momentum")
    txt = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    gm["player_facing_text"] = (txt.strip() + ("\n\n" if txt.strip() else "") + opportunity).strip()

    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    gm["debug_notes"] = (dbg + " | " if dbg else "") + "scene_momentum:enforced_fallback"
    return gm

def _apply_scene_momentum_enforcement(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
) -> Dict[str, Any]:
    """Third step of ``prefer_scene_momentum`` — momentum beat enforcement."""
    return enforce_scene_momentum(out, session=session, scene_envelope=scene_envelope)

def _commit_topic_progress(
    *,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    reply_text: str,
) -> None:
    from game.gm import _get_topic_pressure_context, _topic_progress_score

    ctx = _get_topic_pressure_context(session=session, scene_envelope=scene_envelope)
    if not ctx:
        return
    entry = ctx["entry"]
    speaker_entry = ctx["speaker_entry"] if isinstance(ctx.get("speaker_entry"), dict) else None
    score = _topic_progress_score(reply_text, str(entry.get("last_answer") or ""))
    entry["progress_score_total"] = float(entry.get("progress_score_total", 0.0) or 0.0) + score
    if score < 1.0:
        entry["low_progress_streak"] = int(entry.get("low_progress_streak", 0) or 0) + 1
    else:
        entry["low_progress_streak"] = max(0, int(entry.get("low_progress_streak", 0) or 0) - 1)
    if isinstance(speaker_entry, dict):
        if score < 1.0:
            speaker_entry["low_progress_streak"] = int(speaker_entry.get("low_progress_streak", 0) or 0) + 1
            speaker_entry["patience"] = max(0, int(speaker_entry.get("patience", 3) or 3) - 1)
        else:
            speaker_entry["low_progress_streak"] = max(0, int(speaker_entry.get("low_progress_streak", 0) or 0) - 1)
            speaker_entry["patience"] = min(3, int(speaker_entry.get("patience", 3) or 3) + 1)
    entry["last_answer"] = str(reply_text or "").strip()[:480]

def _commit_topic_progress_after_enforcement(
    *,
    session: Dict[str, Any],
    scene_envelope: Dict[str, Any],
    reply_text: str,
) -> None:
    """Post-loop topic bookkeeping from enforced reply text (ordering-sensitive)."""
    _commit_topic_progress(
        session=session,
        scene_envelope=scene_envelope,
        reply_text=reply_text,
    )

def apply_response_policy_enforcement(
    gm: Dict[str, Any],
    *,
    response_policy: Dict[str, Any],
    player_text: str,
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    discovered_clues: List[str] | None = None,
) -> Dict[str, Any]:
    """Apply deterministic post-generation enforcement in documented priority order.

    This is guard/policy on the GM dict before final emission. Player-visible phrase legality for
    LLM slop (scaffold tokens, procedural imperatives, analytical templates, etc.) is enforced again
    in ``sanitize_player_facing_output``; tests split accordingly.
    """
    if not isinstance(gm, dict):
        return gm

    out, policy, strict_social_turn = _init_response_policy_enforcement_state(
        gm,
        response_policy,
        scene_envelope,
        session,
        world,
        resolution,
    )

    for policy_key, _rule_name in RESPONSE_RULE_PRIORITY:
        if policy_key == "must_answer" and policy.get(policy_key, True):
            if not strict_social_turn:
                out = _apply_must_answer_question_resolution_enforcement(
                    out,
                    player_text=player_text,
                    scene_envelope=scene_envelope,
                    session=session,
                    world=world,
                    resolution=resolution,
                )
            continue

        if policy_key == "forbid_state_invention" and policy.get(policy_key, True):
            out = _apply_forbid_state_invention_validation(out, session, scene_envelope)
            continue

        if policy_key == "forbid_secret_leak" and policy.get(policy_key, True):
            if not strict_social_turn:
                out = _apply_forbid_secret_leak_guard(
                    out,
                    scene_envelope,
                    player_text,
                    discovered_clues,
                    session=session,
                    world=world,
                    resolution=resolution,
                )
            continue

        if policy_key == "allow_partial_answer":
            continue

        if (
            policy_key == "diegetic_only"
            and policy.get(policy_key, True)
            and bool((policy.get("no_validator_voice") or {}).get("enabled", True))
        ):
            if not strict_social_turn:
                out = _apply_diegetic_validator_voice_enforcement(
                    out,
                    scene_envelope=scene_envelope,
                    player_text=player_text,
                    session=session,
                    world=world,
                    resolution=resolution,
                )
            continue

        if policy_key == "prefer_scene_momentum" and policy.get(policy_key, True):
            if not strict_social_turn:
                out = _apply_topic_pressure_escalation_enforcement(
                    out,
                    player_text=player_text,
                    session=session,
                    scene_envelope=scene_envelope,
                )
                out = _apply_escalate_passive_scene_enforcement(
                    out,
                    player_text=player_text,
                    session=session,
                    world=world,
                    scene_envelope=scene_envelope,
                    resolution=resolution,
                )
                out = _apply_scene_momentum_enforcement(
                    out,
                    session=session,
                    scene_envelope=scene_envelope,
                )
            continue

        if policy_key == "prefer_specificity" and policy.get(policy_key, True):
            if not strict_social_turn:
                out = _apply_prefer_specificity_text_enforcement(
                    out,
                    player_text=player_text,
                    scene_envelope=scene_envelope,
                    session=session,
                    world=world,
                    resolution=resolution,
                )

    _commit_topic_progress_after_enforcement(
        session=session,
        scene_envelope=scene_envelope,
        reply_text=str(out.get("player_facing_text") or ""),
    )
    if isinstance(policy, dict):
        _snapshot_response_policy_and_project_fallback_contract(out, policy)
    _mark_response_policy_enforcement_applied(out)
    return out
