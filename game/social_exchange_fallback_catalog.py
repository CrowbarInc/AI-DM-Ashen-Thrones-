"""Strict-social fallback phrase catalog and selection (BV14A canonical owner)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Tuple

from game.interaction_context import inspect as inspect_interaction_context, resolve_authoritative_social_target
from game.prompt_context import canonical_interaction_target_npc_id
from game.response_policy_contracts import response_type_contract_requires_dialogue
from game.social import (
    apply_social_reply_speaker_grounding,
    resolve_grounded_social_speaker,
    topic_pressure_speaker_id_for_social_exchange,
)
from game.social_exchange_policy import (
    _auth_after_social_promotion_binding,
    _deterministic_index,
    _scene_envelope_for_strict_social,
    speaker_label,
    merged_player_prompt_for_gate,
    strict_social_emission_will_apply,
)
from game.social_exchange_projection import (
    _extract_uncertainty_source_from_tags,
    _is_pressure_active,
    emission_gate_interruption_active,
    emission_gate_pressure_active,
    emission_gate_uncertainty_source,
    interruption_cue_present_in_text,
)
from game.social_exchange_validation import (
    _collapse_ws,
    _looks_like_interruption_breakoff_text,
    _normalize_gate_text,
    _sentence_is_bounded_social_signal,
    _sentence_opens_with_resolved_npc_beat,
    _split_sentences,
    is_route_illegal_global_or_sanitizer_fallback_text,
)


def _integrity_topic_hook(player_text: str) -> str:
    from game.gm import _question_content_tokens

    hooks = _question_content_tokens(str(player_text or ""))
    h = str(hooks[0] or "").strip() if hooks else ""
    return h

def minimal_social_emergency_fallback_line(resolution: Dict[str, Any] | None) -> str:
    """Terminal-safe; deterministic variety; must pass as route-legal social without revalidation loops."""
    social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    speaker = speaker_label(resolution)
    seed = f"{npc_id}|{speaker}"
    idx = _deterministic_index(seed, 3)
    lines = (
        f'{speaker} shakes their head. "I don\'t know."',
        f'{speaker} says, "I do not know enough to answer that."',
        f'{speaker} grimaces. "Not something I can say here."',
    )
    return lines[idx]

def _strict_social_emergency_fallback_npc_dialogue_substantive(
    text: str,
    resolution: Dict[str, Any] | None,
) -> bool:
    """True when terminal fallback is not interruption-bridge dead air and has grounded NPC dialogue presence."""
    t = _collapse_ws(str(text or "")).strip()
    if not t:
        return False
    if _looks_like_interruption_breakoff_text(t):
        return False
    if is_route_illegal_global_or_sanitizer_fallback_text(t):
        return False
    if '"' in t:
        return True
    sentences = _split_sentences(t)
    for s in sentences:
        if _sentence_opens_with_resolved_npc_beat(s, resolution) and _sentence_is_bounded_social_signal(s):
            return True
    return False

def lawful_strict_social_dialogue_emergency_fallback_line(resolution: Dict[str, Any] | None) -> str:
    """Compact NPC reply pool for strict-social terminal fallback application."""
    social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    speaker = speaker_label(resolution)
    seed = f"lawful_dialogue_emergency|{npc_id}|{speaker}"
    idx = _deterministic_index(seed, 4)
    lines = (
        f'{speaker} shakes their head. "I don\'t know."',
        f'{speaker} says, "I do not know enough to answer that."',
        f'{speaker} grimaces. "Not something I can say here."',
        f'{speaker} says, "I cannot answer that from what I know."',
    )
    return lines[idx]

def text_is_strict_social_minimal_emergency_fallback(text: str, resolution: Dict[str, Any] | None) -> bool:
    """True when *text* matches a deterministic strict-social terminal emergency line (not model progression)."""
    if not isinstance(resolution, dict):
        return False
    t = _normalize_gate_text(str(text or "")).strip()
    if not t:
        return False
    for factory in (minimal_social_emergency_fallback_line, lawful_strict_social_dialogue_emergency_fallback_line):
        if _normalize_gate_text(factory(resolution)).strip() == t:
            return True
    return False

def strict_social_terminal_dialogue_fallback_valid(text: str, resolution: Dict[str, Any] | None) -> bool:
    """Public check: strict-social emergency fallback carries continuity-valid NPC dialogue."""
    return _strict_social_emergency_fallback_npc_dialogue_substantive(text, resolution)

def active_interlocutor_matches_resolution_social_npc(
    session: Dict[str, Any] | None,
    resolution: Dict[str, Any] | None,
) -> bool:
    if not isinstance(session, dict) or not isinstance(resolution, dict):
        return False
    inspected = inspect_interaction_context(session)
    active_ic = str(inspected.get("active_interaction_target_id") or "").strip()
    if not active_ic:
        return False
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    npc_id = str(soc.get("npc_id") or "").strip()
    if not npc_id:
        return False
    a = canonical_interaction_target_npc_id(session, active_ic)
    n = canonical_interaction_target_npc_id(session, npc_id)
    return bool(a) and bool(n) and a == n

def apply_strict_social_terminal_dialogue_fallback_if_needed(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    base_gm: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    retry_terminal: bool,
) -> tuple[str, bool]:
    """Apply strict-social terminal dialogue fallback when a dialogue contract is already active.

    This is a downstream emission/application step. Contract resolution stays in
    :mod:`game.response_policy_contracts`; this helper only consumes that verdict.
    """
    if not retry_terminal or not isinstance(resolution, dict):
        return text, False
    if not response_type_contract_requires_dialogue(
        base_gm if isinstance(base_gm, dict) else None,
        resolution=resolution,
        session=session if isinstance(session, dict) else None,
    ):
        return text, False
    if not strict_social_emission_will_apply(
        resolution,
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        str(scene_id or "").strip(),
    ):
        return text, False
    if not active_interlocutor_matches_resolution_social_npc(
        session if isinstance(session, dict) else None,
        resolution,
    ):
        return text, False
    if strict_social_terminal_dialogue_fallback_valid(text, resolution):
        return text, False
    return lawful_strict_social_dialogue_emergency_fallback_line(resolution), True

def repair_strict_social_terminal_dialogue_fallback_if_needed(
    text: str,
    *,
    resolution: Dict[str, Any] | None,
    base_gm: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    retry_terminal: bool,
) -> tuple[str, bool]:
    """Compatibility residue for older repair-shaped imports.

    Prefer :func:`apply_strict_social_terminal_dialogue_fallback_if_needed`.
    Do not add new contract semantics here.
    """
    return apply_strict_social_terminal_dialogue_fallback_if_needed(
        text,
        resolution=resolution,
        base_gm=base_gm,
        session=session,
        world=world,
        scene_id=scene_id,
        retry_terminal=retry_terminal,
    )

def strict_social_ownership_terminal_fallback(resolution: Dict[str, Any] | None) -> str:
    """Hard legal minimum for strict-social ownership: NPC refusal/ignorance lines only.

    Deterministic; intended to bypass further validation loops when no SOCIAL sentences remain.
    """
    social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    speaker = speaker_label(resolution)
    seed = f"ownership_terminal|{npc_id}|{speaker}"
    idx = _deterministic_index(seed, 3)
    lines = (
        f'{speaker} shakes their head. "I don\'t know."',
        f'{speaker} says, "I do not know enough to answer that."',
        f'{speaker} says, "No. I cannot answer that from what I know."',
    )
    return lines[idx]

def deterministic_social_fallback_line(
    *,
    resolution: Dict[str, Any] | None,
    uncertainty_source: str,
    pressure_active: bool,
    interruption_active: bool,
    seed: str,
) -> Tuple[str, str]:
    speaker = speaker_label(resolution)
    direct_answer = (
        f'{speaker} points down the nearest road. "Old crossroads—that way."',
        f'{speaker} nods once. "Old Millstone. South road."',
    )
    interruption = (
        f"{speaker} starts to answer, then glances past you as shouting breaks out in the crowd.",
        f"{speaker} opens their mouth, then breaks off as a shout cuts across the square.",
    )
    pressure_refusal = (
        f'{speaker} tightens their jaw. "I\'ve told you what I know."',
        f'{speaker} shakes their head. "No. I will not say more."',
    )
    ignorance = (
        f'{speaker} shakes their head. "I don\'t know."',
        f'{speaker} spreads their hands. "I\'ve heard talk, but not enough to answer that."',
        f'{speaker} lowers their voice. "I have heard the talk, but I cannot swear to that."',
        f'{speaker} glances away. "I do not know that part for certain."',
        f'{speaker} mutters. "Word is, it was messy—but I won\'t swear to who."',
        f'{speaker} shrugs. "Couldn\'t tell you—only rumors from the road."',
    )
    evasive = (
        f'{speaker} avoids your eyes. "I\'m not naming names."',
        f'{speaker} keeps their voice low. "I won\'t say more here."',
    )
    if interruption_active:
        options, kind = interruption, "interruption"
    elif pressure_active:
        options, kind = pressure_refusal, "pressure_refusal"
    elif uncertainty_source == "procedural_insufficiency":
        options, kind = evasive, "refusal_evasion"
    elif uncertainty_source == "npc_ignorance":
        options, kind = ignorance, "explicit_ignorance"
    else:
        social = resolution.get("social") if isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) else {}
        if bool(social.get("npc_reply_expected")):
            options, kind = ignorance, "explicit_ignorance"
            idx = _deterministic_index(seed, len(options))
            return options[idx], kind
        idx = _deterministic_index(seed + "|direct", len(direct_answer))
        return direct_answer[idx], "direct_answer_hint"
    idx = _deterministic_index(seed, len(options))
    return options[idx], kind

def social_fallback_line_for_sanitizer(
    context: Dict[str, Any] | None,
    *,
    source_text: str = "",
    mode: str | None = None,
) -> str:
    """Single-form social line for sanitizer rescue (never scene pools)."""
    resolution = context.get("resolution") if isinstance(context, dict) else None
    session = context.get("session") if isinstance(context, dict) else None
    scene_id = str((context.get("scene_id") or "")).strip()
    if mode == "narration":
        mode = None
    uncertainty = "npc_ignorance"
    if mode == "npc" or mode == "npc_ignorance":
        uncertainty = "npc_ignorance"
    elif mode == "procedural_insufficiency":
        uncertainty = "procedural_insufficiency"
    text = source_text or ""
    tags: List[str] = []
    seed = _collapse_ws(text) or "sanitizer"
    line, _ = deterministic_social_fallback_line(
        resolution=resolution if isinstance(resolution, dict) else None,
        uncertainty_source=uncertainty,
        pressure_active=_is_pressure_active(tags, session if isinstance(session, dict) else None, scene_id),
        interruption_active=False,
        seed=seed,
    )
    return line

StrictSocialEmergencyFallbackSurface = Literal["visibility", "sanitizer_empty"]

def select_strict_social_emergency_fallback_line(
    *,
    resolution: Dict[str, Any] | None = None,
    context: Dict[str, Any] | None = None,
    source_text: str = "",
    surface: StrictSocialEmergencyFallbackSurface,
) -> str:
    """Canonical strict-social emergency fallback line selection across visibility and sanitizer surfaces."""
    if surface == "visibility":
        return minimal_social_emergency_fallback_line(resolution)
    if surface == "sanitizer_empty":
        return social_fallback_line_for_sanitizer(
            context if isinstance(context, dict) else {},
            source_text=source_text,
        )
    raise ValueError(f"unknown strict-social emergency fallback surface: {surface!r}")

_STALL_OPEN_SOCIAL_FRAGMENT_RE = re.compile(
    r"(?i)^\s*(?:no\s+one\s+answers?|nobody\s+answers?|no\s+one\s+steps\s+forward|nobody\s+steps\s+forward|the\s+moment\s+passes)\.?\s*$"
)

_STALL_OPEN_SOCIAL_ANYWHERE_RE = re.compile(
    r"(?i)\b(?:no\s+one\s+answers?|nobody\s+answers?|no\s+one\s+steps\s+forward|nobody\s+steps\s+forward|the\s+moment\s+passes)\b"
)

def _ensure_sentence_end(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    last = s[-1]
    if last in ".!?":
        return s
    if last in "\"'”’" and len(s) > 1 and s[-2] in ".!?":
        return s
    if last in "…":
        return s
    return f"{s}."

def _open_social_visible_leads_surface(
    scene_envelope: Dict[str, Any] | None,
) -> Tuple[List[str], str]:
    facts: List[str] = []
    afford_key = ""
    if not isinstance(scene_envelope, dict):
        return facts, afford_key
    scene = scene_envelope.get("scene") if isinstance(scene_envelope.get("scene"), dict) else {}
    raw = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
    facts = [str(x).strip() for x in raw if isinstance(x, str) and str(x).strip()]
    for ak in ("social_leads", "leads", "open_threads"):
        block = scene_envelope.get(ak)
        if isinstance(block, list) and block:
            afford_key = ak
            break
        if isinstance(scene.get(ak), list) and scene.get(ak):
            afford_key = ak
            break
    return facts, afford_key

def _open_social_anchor_phrase(world: Dict[str, Any] | None, scene_id: str, npc_id: str) -> str:
    nid = str(npc_id or "").strip()
    if not nid:
        return "A figure near you"
    return f"The {nid.replace('_', ' ').strip()}"

def _open_social_responder_templates(npc_id: str) -> Tuple[str, ...]:
    low = str(npc_id or "").lower()
    guard_cluster = (
        '{anchor} glances over but stays at the choke. "If it\'s about the patrol, ask straight."',
        '{anchor} lifts a hand. "Patrol routes aren\'t idle talk—say what you need."',
    )
    runner_cluster = (
        '{anchor} lifts a hand through the rain. "Depends what you\'re buying—stew, rumor, or both?"',
        '{anchor} hooks a thumb toward the kettle. "Coin buys a bowl; careful questions cost extra."',
    )
    if "guard" in low or "watch" in low or "sentry" in low:
        return guard_cluster
    if "runner" in low or "merchant" in low or "tavern" in low:
        return runner_cluster
    return (
        '{anchor} looks up from the press of bodies. "Speak plain—I\'m not guessing what you want."',
        '{anchor} meets your eyes a beat. "One thing at a time—what are you actually offering?"',
    )

def _open_social_lead_templates() -> Tuple[str, ...]:
    return (
        "No one answers outright, but {anchor} is already working the crowd for coin and rumor a few paces off.",
        "The shout earns only flinches; {anchor} is still the clearest face to put a question to.",
        "Nobody owns the moment—yet {anchor} keeps an open posture, waiting to see if you mean business.",
    )

def open_social_recovery_passes_anti_stall(text: str, anchor_key: str) -> bool:
    t = str(text or "").strip()
    if not t:
        return False
    low = t.lower()
    key = str(anchor_key or "").strip().lower()
    if key and key not in low:
        return False
    if _STALL_OPEN_SOCIAL_FRAGMENT_RE.match(t):
        return False
    frag = _STALL_OPEN_SOCIAL_ANYWHERE_RE.search(low)
    if frag:
        tail = t[frag.end() :].strip(" \t,;—:-")
        if len(tail) < 28:
            return False
    return True

def _shorten_visible_fact_for_lead(fact: str, *, limit: int = 110) -> str:
    s = str(fact or "").strip()
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"

def _open_social_fact_lead_line(visible_facts: List[str], seed: str) -> Tuple[str, str]:
    facts = [f for f in visible_facts if isinstance(f, str) and f.strip()]
    if not facts:
        return "", ""
    pick = facts[_deterministic_index(seed, len(facts))]
    snip = _shorten_visible_fact_for_lead(pick)
    opener = (
        "The noise doesn't thin on its own—still, ",
        "Voices overlap, but ",
        "Crowd-swell aside, ",
    )
    op = opener[_deterministic_index(seed + "|op", len(opener))]
    body = snip[0].lower() + snip[1:] if len(snip) > 1 else snip.lower()
    line = f"{op}{body} stays right in front of you as a next handle."
    return _ensure_sentence_end(line), snip.lower()

def _speaker_contract_allows_candidate(
    contract: Dict[str, Any] | None,
    candidate_id: str,
) -> bool:
    if not isinstance(contract, dict):
        return True
    allowed = [str(x).strip() for x in (contract.get("allowed_speaker_ids") or []) if str(x).strip()]
    if not allowed:
        return True
    return str(candidate_id or "").strip() in allowed

def merge_open_social_recovery_emission_debug(
    out: Dict[str, Any],
    rec: Dict[str, Any],
) -> None:
    md = out.setdefault("metadata", {})
    if not isinstance(md, dict):
        return
    em = md.setdefault("emission_debug", {})
    if not isinstance(em, dict):
        return
    em["open_social_recovery_used"] = bool(rec.get("used"))
    em["open_social_recovery_mode"] = rec.get("mode")
    em["open_social_recovery_candidate_id"] = rec.get("candidate_id")
    em["open_social_recovery_reason"] = rec.get("reason")
    em["open_social_recovery_suppressed_retry_fallback"] = bool(rec.get("used"))

def build_open_social_solicitation_recovery(
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    scene_envelope: Dict[str, Any] | None = None,
    player_text: str = "",
) -> Dict[str, Any]:
    """Deterministic rescue for broad-address (open) social solicitation retry/fallback.

    Uses only ``resolution.social`` open-solicitation metadata (already ranked candidates).
    """
    empty_out: Dict[str, Any] = {
        "used": False,
        "mode": None,
        "candidate_id": None,
        "text": None,
        "reason": "not_applicable",
    }
    sid = str(scene_id or "").strip()
    if not sid or not isinstance(resolution, dict):
        return {**empty_out, "reason": "not_applicable"}
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    if not soc.get("open_social_solicitation"):
        return {**empty_out, "reason": "not_open_social_solicitation"}

    cands_raw = soc.get("candidate_addressable_ids")
    ranked: List[str] = []
    if isinstance(cands_raw, list):
        ranked = [str(x).strip() for x in cands_raw if isinstance(x, str) and str(x).strip()]
    try:
        ccount = int(soc.get("candidate_addressable_count", len(ranked)))
    except (TypeError, ValueError):
        ccount = len(ranked)

    w = world if isinstance(world, dict) else {}
    sess = session if isinstance(session, dict) else None
    env = scene_envelope if isinstance(scene_envelope, dict) else _scene_envelope_for_strict_social(sess, sid)
    facts, afford_tag = _open_social_visible_leads_surface(env if isinstance(env, dict) else None)
    has_surface = bool(ccount > 0 or ranked or facts or afford_tag)
    if not has_surface:
        return {**empty_out, "reason": "no_anchor_surface"}

    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    na = meta.get("normalized_action") if isinstance(meta.get("normalized_action"), dict) else None
    merged = merged_player_prompt_for_gate(resolution, sess, sid)
    prompt_seed = _collapse_ws(f"{sid}|{player_text}|{merged}") or sid

    from game.interaction_context import build_speaker_selection_contract

    contract = build_speaker_selection_contract(
        sess,
        w,
        sid,
        resolution=resolution,
        normalized_action=na,
        scene_envelope=env if isinstance(env, dict) else None,
        merged_player_prompt=str(player_text or "").strip() or merged,
    )

    auth = resolve_authoritative_social_target(
        sess,
        w,
        sid,
        player_text=str(player_text or "").strip() or merged,
        normalized_action=na,
        merged_player_prompt=merged,
        scene_envelope=env if isinstance(env, dict) else None,
        allow_first_roster_fallback=True,
    )
    auth, _, _ = _auth_after_social_promotion_binding(
        sess,
        w,
        sid,
        auth,
        env if isinstance(env, dict) else None,
        merged_player_prompt=merged,
    )
    tp = topic_pressure_speaker_id_for_social_exchange(sess, sid) if sess is not None else None

    chosen: str | None = None
    for cid in ranked:
        if not _speaker_contract_allows_candidate(contract, cid):
            continue
        gr = resolve_grounded_social_speaker(
            sess if sess is not None else {},
            w,
            sid,
            env if isinstance(env, dict) else None,
            auth,
            proposed_reply_speaker_id=cid,
            topic_pressure_speaker_id=tp,
        )
        if gr.get("allowed"):
            chosen = cid
            break

    anchor_key = ""
    text_out = ""
    mode: str | None = None
    reason = ""

    if chosen:
        anchor = _open_social_anchor_phrase(w, sid, chosen)
        anchor_key = anchor.lower()
        tpls = _open_social_responder_templates(chosen)
        tpl = tpls[_deterministic_index(prompt_seed + "|rsp|" + chosen, len(tpls))]
        text_out = tpl.format(anchor=anchor)
        text_out = _ensure_sentence_end(text_out)
        mode = "concrete_responder"
        reason = "concrete_responder"
    elif ranked:
        lead_anchor_id = ranked[0]
        anchor = _open_social_anchor_phrase(w, sid, lead_anchor_id)
        anchor_key = anchor.lower()
        ltpl = _open_social_lead_templates()
        text_out = ltpl[_deterministic_index(prompt_seed + "|lead|" + lead_anchor_id, len(ltpl))].format(anchor=anchor)
        text_out = _ensure_sentence_end(text_out)
        mode = "concrete_lead"
        reason = "concrete_lead_after_speaker_blocked"
        chosen = None
    elif facts or afford_tag:
        text_out, anchor_key = _open_social_fact_lead_line(facts, prompt_seed + "|fact")
        if afford_tag and not text_out:
            text_out = _ensure_sentence_end(
                f"Nothing resolves into a single voice—yet the scene still offers a thread under {afford_tag} worth tightening next."
            )
            anchor_key = afford_tag.lower()
        mode = "concrete_lead"
        reason = "concrete_lead_visible_surface"
        chosen = None

    if not text_out or not open_social_recovery_passes_anti_stall(text_out, anchor_key):
        return {**empty_out, "reason": "anti_stall_or_missing_anchor" if text_out else "empty_recovery_line"}

    cid_meta = chosen
    return {
        "used": True,
        "mode": mode,
        "candidate_id": cid_meta,
        "text": text_out,
        "reason": reason,
    }

def _standard_mode_social_retry_payload_floor(
    line: str,
    *,
    resolution: Dict[str, Any] | None,
    uncertainty_source: str,
    pressure_active: bool,
    interruption_active: bool,
    seed: str,
    session: Dict[str, Any] | None,
) -> str:
    """Under standard response_mode, avoid one-line clipped social retry fallbacks unless pressure/interrupt."""
    if not isinstance(session, dict):
        return line
    if str(session.get("response_mode") or "standard").strip().lower() != "standard":
        return line
    if pressure_active or interruption_active:
        return str(line or "").strip()
    t = _normalize_gate_text(str(line or "")).strip()
    if len(t.split()) >= 18:
        return t
    speaker = speaker_label(resolution)
    extras = (
        f'{speaker} keeps their voice low. "Hard to swear to anything in this crowd."',
        f'{speaker} glances toward the street. "You\'re asking for a line I don\'t own."',
        f'{speaker} hesitates. "I\'ve heard talk, but I won\'t pin that down as truth."',
    )
    idx = _deterministic_index(seed + f"|{uncertainty_source}|stdfloor", len(extras))
    return _ensure_sentence_end(_normalize_gate_text(f"{t} {extras[idx]}"))

def apply_social_exchange_retry_fallback_gm(
    gm: Dict[str, Any],
    *,
    player_text: str,
    session: Dict[str, Any],
    world: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    scene_id: str,
    variation_salt: str = "",
) -> Dict[str, Any]:
    """Replace GM text with a compact social fallback (no uncertainty renderer blob)."""
    if not isinstance(gm, dict):
        return gm
    sid_rf = str(scene_id or "").strip()
    if isinstance(resolution, dict) and isinstance(session, dict) and sid_rf:
        soc_os = resolution.get("social") if isinstance(resolution.get("social"), dict) else None
        if isinstance(soc_os, dict) and soc_os.get("open_social_solicitation"):
            env_os = _scene_envelope_for_strict_social(session, sid_rf)
            rec = build_open_social_solicitation_recovery(
                resolution=resolution,
                session=session,
                world=world if isinstance(world, dict) else None,
                scene_id=sid_rf,
                scene_envelope=env_os if isinstance(env_os, dict) else None,
                player_text=player_text,
            )
            if rec.get("used") and isinstance(rec.get("text"), str) and str(rec.get("text") or "").strip():
                out = dict(gm)
                os_line = _ensure_sentence_end(str(rec.get("text") or "").strip())
                tags_pre = gm.get("tags") if isinstance(gm.get("tags"), list) else []
                tag_list_pre = [str(t) for t in tags_pre if isinstance(t, str)]
                out["player_facing_text"] = _standard_mode_social_retry_payload_floor(
                    os_line,
                    resolution=resolution,
                    uncertainty_source="open_social_recovery",
                    pressure_active=_is_pressure_active(tag_list_pre, session, sid_rf),
                    interruption_active=False,
                    seed=f"{sid_rf}|osrec|{player_text}",
                    session=session,
                )
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
                    + f"retry_fallback:open_social_recovery:{rec.get('mode')}|retry_fallback:suppressed:social_exchange_template"
                )
                merge_open_social_recovery_emission_debug(out, rec)
                return out
    if isinstance(resolution, dict) and isinstance(session, dict) and sid_rf:
        soc_r = resolution.get("social") if isinstance(resolution.get("social"), dict) else None
        if isinstance(soc_r, dict) and soc_r.get("target_resolved") is True and not soc_r.get("offscene_target"):
            env_rf = _scene_envelope_for_strict_social(session, sid_rf)
            merged_rf = merged_player_prompt_for_gate(resolution, session, sid_rf)
            meta_rf = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
            na_rf = meta_rf.get("normalized_action") if isinstance(meta_rf.get("normalized_action"), dict) else None
            auth_rf = resolve_authoritative_social_target(
                session,
                world if isinstance(world, dict) else None,
                sid_rf,
                player_text=merged_rf,
                normalized_action=na_rf,
                merged_player_prompt=merged_rf,
                scene_envelope=env_rf,
                allow_first_roster_fallback=True,
            )
            auth_rf, _, _ = _auth_after_social_promotion_binding(
                session,
                world if isinstance(world, dict) else {},
                sid_rf,
                auth_rf,
                env_rf,
                merged_player_prompt=merged_rf,
            )
            apply_social_reply_speaker_grounding(
                soc_r,
                session,
                world if isinstance(world, dict) else {},
                sid_rf,
                env_rf,
                auth_rf,
            )
    out = dict(gm)
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    prior_text = str(out.get("player_facing_text") or "")
    uncertainty_source = _extract_uncertainty_source_from_tags(tag_list, prior_text)
    pressure = _is_pressure_active(tag_list, session, scene_id)
    interrupt = interruption_cue_present_in_text(prior_text)
    vs = str(variation_salt or "").strip()
    # Follow-up repetition uses ``variation_salt``; do not pin the template to the interruption-only floor.
    if vs:
        interrupt = False
    seed = f"{scene_id}|retry|{player_text}|{uncertainty_source}|{pressure}|{interrupt}|{vs}"
    line, kind = deterministic_social_fallback_line(
        resolution=resolution,
        uncertainty_source=uncertainty_source,
        pressure_active=pressure,
        interruption_active=interrupt,
        seed=seed,
    )
    out["player_facing_text"] = _standard_mode_social_retry_payload_floor(
        line,
        resolution=resolution,
        uncertainty_source=uncertainty_source,
        pressure_active=pressure,
        interruption_active=interrupt,
        seed=seed,
        session=session,
    )
    out["tags"] = tag_list + ["question_retry_fallback", "social_exchange_retry_fallback", f"social_exchange_fallback:{kind}"]
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (dbg + " | " if dbg else "") + f"retry_fallback:unresolved_question|retry_fallback:social_exchange:{kind}"
    return out

def social_integrity_fallback_line_candidates(
    *,
    resolution: Dict[str, Any],
    player_text: str,
    session: Dict[str, Any] | None,
    scene_id: str,
    tag_list: List[str],
    seed: str,
) -> List[Tuple[str, str]]:
    """Deterministic NPC-voiced lines ordered by structured social outcome (inspectable, no LLM)."""
    speaker = speaker_label(resolution if isinstance(resolution, dict) else None)
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    rk = str(soc.get("reply_kind") or "").strip().lower()
    po = str(soc.get("probe_outcome") or "").strip().lower()
    pm = str(soc.get("social_probe_move") or "").strip().lower()
    hook = _integrity_topic_hook(player_text)
    topic = hook if hook else "that"

    out: List[Tuple[str, str]] = []

    def _add_unique(line: str, kind: str) -> None:
        t = _normalize_gate_text(line).strip()
        if not t:
            return
        if any(_normalize_gate_text(a).strip() == t for a, _ in out):
            return
        out.append((line, kind))

    if po in ("actionable_redirect", "actionable_lead_or_redirect"):
        _add_unique(
            f'{speaker} nods once. "Speak to the ward clerk by the main gate if {topic} still matters to you."',
            "integrity_redirect_clerk_gate",
        )
        _add_unique(
            f'{speaker} mutters, "Word is, the night watch leans on the river gate route when {topic} comes up."',
            "integrity_redirect_river_gate_rumor",
        )
    if rk == "refusal":
        _add_unique(
            f'{speaker} shakes their head. "I won\'t answer that about {topic}—not here."',
            "integrity_refusal_boundary",
        )
        _add_unique(
            f'{speaker} tightens their jaw. "No names and no favors on {topic}—not from me."',
            "integrity_refusal_pressure",
        )
    if pm == "transactional":
        _add_unique(
            f'{speaker} pockets the coin without smiling. "Word is, the stable lane stays cheaper than the guild inns—'
            f'that is what I will say on {topic}."',
            "integrity_transactional_partial_rumor",
        )
        _add_unique(
            f'{speaker} glances away. "If {topic} is what you are buying, ask the harbor clerk—they see who actually pays."',
            "integrity_transactional_redirect_clerk",
        )
    if rk == "explanation" and po not in ("actionable_redirect", "actionable_lead_or_redirect"):
        _add_unique(
            f'{speaker} keeps their voice low. "All I know on {topic} is rumor: people say the ledger desk by the '
            f'west pier sees the real traffic."',
            "integrity_explanation_rumor_pier",
        )
        _add_unique(
            f'{speaker} exhales. "I do not keep that answer on {topic}—not from what I know."',
            "integrity_explanation_defer_clerk",
        )

    sid = str(scene_id or "").strip()
    unc = emission_gate_uncertainty_source(tag_list, player_text)
    press = emission_gate_pressure_active(tag_list, session, sid)
    interrupt = interruption_cue_present_in_text(player_text)
    fb, fk = deterministic_social_fallback_line(
        resolution=resolution,
        uncertainty_source=unc,
        pressure_active=press,
        interruption_active=interrupt,
        seed=seed + "|integrity_tail",
    )
    _add_unique(fb, f"integrity_deterministic:{fk}")
    _add_unique(minimal_social_emergency_fallback_line(resolution), "integrity_minimal_emergency")

    return out
