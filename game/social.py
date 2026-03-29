"""Deterministic social action resolution: engine-first before GPT narration.

Supported kinds: question, persuade, intimidate, deceive, barter, recruit, social_probe.

Skill mapping (canonical, conservative):
- question / social_probe: no hard skill check unless explicitly configured
- persuade: Diplomacy
- intimidate: Intimidate
- deceive: Bluff if present; else skip check (fallback cleanly, no crash)
- barter: Diplomacy (canonical; appraise not used—see docstring)
- recruit: Diplomacy with stricter DC (+3)
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from game.models import SocialEngineResult, make_check_request, social_result_to_dict
from game.utils import slugify
from game.npc_promotion import promote_scene_actor_to_npc, should_promote_scene_actor
from game.storage import get_npc_runtime, get_scene_runtime, get_scene_state
from game.interaction_context import (
    apply_turn_input_implied_context,
    canonical_scene_addressable_roster,
    is_actor_addressable_in_current_scene,
    npc_dict_by_id,
    resolve_authoritative_social_target,
    scene_addressable_actor_ids,
    set_non_social_activity,
    set_social_target,
    synchronize_scene_addressability,
)
from game.skill_checks import should_trigger_check

# Skill mapping: action_kind -> (skill_id, dc_modifier)
# dc_modifier: added to base DC 10. recruit uses +3.
SOCIAL_SKILL_MAP = {
    "question": None,  # No check by default
    "social_probe": None,
    "persuade": ("diplomacy", 0),
    "intimidate": ("intimidate", 0),
    "deceive": ("bluff", 0),  # fallback: diplomacy if bluff absent
    "barter": ("diplomacy", 0),  # Canonical: Diplomacy for barter. Appraise not used.
    "recruit": ("diplomacy", 3),  # Stricter threshold
}

SOCIAL_KINDS = tuple(SOCIAL_SKILL_MAP.keys())
SOCIAL_EXCHANGE_KINDS = ("question", "social_probe")
SOCIAL_MANEUVER_KINDS = ("persuade", "intimidate", "deceive", "barter", "recruit")

# Sources that count as stable explicit in-scene address for promotion triggers (not ambient fallbacks).
_STABLE_SOCIAL_ADDRESS_SOURCES = frozenset(
    {
        "explicit_target",
        "declared_action",
        "spoken_vocative",
        "vocative",
        "generic_role",
        "substring",
    }
)


def _topic_pressure_speaker_has_prior_answer(
    session: Dict[str, Any],
    scene_id: str,
    actor_id: str,
) -> bool:
    """True when topic_pressure names this speaker and has a stored last_answer (engine-owned)."""
    sid = str(scene_id or "").strip()
    aid = str(actor_id or "").strip()
    if not sid or not aid or not isinstance(session, dict):
        return False
    rt = get_scene_runtime(session, sid)
    tcur = rt.get("topic_pressure_current") if isinstance(rt.get("topic_pressure_current"), dict) else {}
    speaker_key = str(tcur.get("speaker_key") or "").strip()
    if not speaker_key:
        return False
    a, b = speaker_key.lower(), aid.lower()
    if not (a == b or a in b or b in a):
        return False
    tk = str(tcur.get("topic_key") or "").strip()
    pressure = rt.get("topic_pressure") if isinstance(rt.get("topic_pressure"), dict) else {}
    entry = pressure.get(tk) if tk and isinstance(pressure.get(tk), dict) else {}
    if str(entry.get("last_answer") or "").strip():
        return True
    targets = entry.get("speaker_targets") if isinstance(entry.get("speaker_targets"), dict) else {}
    st = targets.get(speaker_key) if isinstance(targets.get(speaker_key), dict) else {}
    st = st or targets.get(aid) if isinstance(targets.get(aid), dict) else {}
    return int(st.get("repeat_count") or 0) >= 1


_CONSEQUENTIAL_SPEECH_ACT_RE = re.compile(
    r"\b(threaten|threatens|threatening|bribe|bribes|bribing|blackmail|blackmails|blackmailing)\b",
    re.IGNORECASE,
)


def should_auto_promote_scene_actor_for_social(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    actor_id: str,
    *,
    auth_source: str,
    action_type: str,
    turn_counter: int,
    roster_row: Optional[Dict[str, Any]] = None,
    raw_player_text: Optional[str] = None,
) -> Tuple[bool, str]:
    """Deterministic policy: promote roster-only actors only when engine facts justify it.

    Returns (should_promote, reason_code).
    """
    if not isinstance(session, dict) or not isinstance(world, dict):
        return False, "invalid_session_or_world"
    aid = str(actor_id or "").strip()
    sid = str(scene_id or "").strip()
    if not aid or not sid:
        return False, "empty_actor_or_scene"
    if not should_promote_scene_actor(session, world, sid, aid):
        return False, "not_promotable_or_already_bound"
    src = str(auth_source or "").strip().lower()
    at = str(action_type or "").strip().lower()
    if at in SOCIAL_MANEUVER_KINDS:
        return True, "consequential_social_maneuver"
    if raw_player_text and _CONSEQUENTIAL_SPEECH_ACT_RE.search(str(raw_player_text)):
        return True, "consequential_speech_act_in_player_text"
    if src == "first_roster":
        return False, "first_roster_ambient_fallback"
    if src in _STABLE_SOCIAL_ADDRESS_SOURCES:
        return True, "stable_explicit_address"
    rt = get_npc_runtime(session, aid)
    revealed = rt.get("revealed_topics") or []
    if isinstance(revealed, list) and any(str(x).strip() for x in revealed):
        return True, "prior_engine_topic_reveal"
    row = roster_row if isinstance(roster_row, dict) else {}
    if row and _next_topic_to_reveal(row, rt, None) is not None:
        return True, "pending_engine_topic_for_target"
    if _topic_pressure_speaker_has_prior_answer(session, sid, aid):
        return True, "topic_pressure_prior_answer_as_speaker"
    lit = rt.get("last_interaction_turn")
    if isinstance(lit, int) and lit < int(turn_counter or 0):
        return True, "prior_substantive_interaction_turn"
    return False, "no_promotion_trigger"


def compute_social_target_profile_hints(npc: Optional[Dict[str, Any]], scene_id: str) -> Dict[str, Any]:
    """Structured, deterministic hints from long-term NPC social fields (no freeform)."""
    sid = str(scene_id or "").strip()
    if not isinstance(npc, dict):
        return {
            "guardedness": "medium",
            "answer_reliability_tier": "medium",
            "speaks_authoritatively_for_scene": False,
        }
    stance = str(npc.get("stance_toward_player") or "").strip().lower()
    if stance in ("hostile", "wary"):
        guardedness = "high"
    elif stance == "favorable":
        guardedness = "low"
    else:
        guardedness = "medium"
    rel = str(npc.get("information_reliability") or "").strip().lower()
    if rel == "truthful":
        tier = "high"
    elif rel == "misleading":
        tier = "low"
    else:
        tier = "medium"
    scopes = npc.get("knowledge_scope") or []
    auth_scene = False
    if sid and isinstance(scopes, list):
        needle = f"scene:{sid}"
        for x in scopes:
            if isinstance(x, str) and needle == x.strip().lower():
                auth_scene = True
                break
    return {
        "guardedness": guardedness,
        "answer_reliability_tier": tier,
        "speaks_authoritatively_for_scene": bool(auth_scene or (isinstance(scopes, list) and len(scopes) >= 2)),
    }


def finalize_social_target_with_promotion(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    auth: Dict[str, Any],
    *,
    action_type: str,
    turn_counter: int,
    scene_envelope: Optional[Dict[str, Any]] = None,
    raw_player_text: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Apply promoted_actor_npc_map lookup and conditional auto-promotion; return (auth, binding, profile_hints)."""
    empty_binding: Dict[str, Any] = {}
    empty_hints: Dict[str, Any] = {}
    if not isinstance(auth, dict):
        return {}, empty_binding, empty_hints
    out = dict(auth)
    sid = str(scene_id or "").strip()
    w = world if isinstance(world, dict) else {}
    if not sid or not isinstance(session, dict):
        return out, empty_binding, empty_hints
    if not out.get("target_resolved") or out.get("offscene_target"):
        return out, empty_binding, empty_hints

    resolved = str(out.get("npc_id") or "").strip()
    if not resolved:
        return out, empty_binding, empty_hints

    st = get_scene_state(session)
    pmap_raw = st.get("promoted_actor_npc_map")
    pmap = pmap_raw if isinstance(pmap_raw, dict) else {}

    auth_source = str(out.get("source") or "").strip()
    tc = int(turn_counter or 0)

    roster: List[Dict[str, Any]] = canonical_scene_addressable_roster(
        w,
        sid,
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
        session=session,
    )
    roster_row = next((x for x in roster if isinstance(x, dict) and str(x.get("id") or "").strip() == resolved), None)

    origin_actor: Optional[str] = None
    promoted_this_turn = False
    promo_reason = ""

    wnpc_check = npc_dict_by_id(w, resolved)
    # (a) Native world NPC: already backed by world row and not a promotable orphan scene actor.
    if isinstance(wnpc_check, dict) and not should_promote_scene_actor(session, w, sid, resolved):
        src_pf = "native_npc"
        if str(wnpc_check.get("promoted_from_actor_id") or "").strip():
            src_pf = "promoted_actor"
        binding = {
            "final_target_kind": "npc",
            "npc_id": resolved,
            "target_source": src_pf,
            "origin_actor_id": None,
            "promoted_this_turn": False,
        }
        return out, binding, compute_social_target_profile_hints(wnpc_check, sid)

    # (b) Session promotion map (follow-up turns bind to canonical npc_id).
    if resolved in pmap:
        canon = str(pmap[resolved]).strip()
        if canon and canon != resolved:
            origin_actor = resolved
        if canon:
            out["npc_id"] = canon
            wnpc2 = npc_dict_by_id(w, canon)
            if isinstance(wnpc2, dict):
                nm = str(wnpc2.get("name") or "").strip()
                if nm:
                    out["npc_name"] = nm
            binding = {
                "final_target_kind": "npc",
                "npc_id": canon,
                "target_source": "promoted_actor",
                "origin_actor_id": origin_actor,
                "promoted_this_turn": False,
            }
            return out, binding, compute_social_target_profile_hints(
                wnpc2 if isinstance(wnpc2, dict) else None, sid
            )

    # (c) Auto-promote when policy matches.
    do_promo, promo_reason = should_auto_promote_scene_actor_for_social(
        session,
        w,
        sid,
        resolved,
        auth_source=auth_source,
        action_type=action_type,
        turn_counter=tc,
        roster_row=roster_row,
        raw_player_text=raw_player_text,
    )
    if do_promo:
        pr = promote_scene_actor_to_npc(
            session,
            w,
            sid,
            resolved,
            reason=f"social_auto:{promo_reason}",
            turn_counter=tc,
        )
        if isinstance(pr, dict) and pr.get("ok"):
            nid = str(pr.get("npc_id") or "").strip()
            promoted_this_turn = not bool(pr.get("already_promoted"))
            if nid:
                out["npc_id"] = nid
                npc_ob = pr.get("npc") if isinstance(pr.get("npc"), dict) else npc_dict_by_id(w, nid)
                if isinstance(npc_ob, dict):
                    nm = str(npc_ob.get("name") or "").strip()
                    if nm:
                        out["npc_name"] = nm
                binding = {
                    "final_target_kind": "npc",
                    "npc_id": nid,
                    "target_source": "promoted_actor",
                    "origin_actor_id": resolved if nid != resolved else None,
                    "promoted_this_turn": promoted_this_turn,
                }
                return out, binding, compute_social_target_profile_hints(
                    npc_ob if isinstance(npc_ob, dict) else None, sid
                )

    # (d) Fallback: keep authoritative resolver output; binding only if world backs id.
    wnpc3 = npc_dict_by_id(w, resolved)
    if isinstance(wnpc3, dict):
        src_pf = "native_npc"
        if str(wnpc3.get("promoted_from_actor_id") or "").strip():
            src_pf = "promoted_actor"
        binding = {
            "final_target_kind": "npc",
            "npc_id": resolved,
            "target_source": src_pf,
            "origin_actor_id": None,
            "promoted_this_turn": False,
        }
        return out, binding, compute_social_target_profile_hints(wnpc3, sid)

    return out, empty_binding, empty_hints

_DIRECT_QUESTION_WORDS = ("who", "what", "where", "when", "why", "how", "which")
_NAME_REQUEST_TOKENS = ("your name", "their name", "his name", "her name", "called", "who are you")
_DESTINATION_REQUEST_TOKENS = ("where to", "where can i find", "where can we find", "destination", "headed", "going")
_EXPLANATION_REQUEST_TOKENS = ("explain", "why", "how", "what happened", "tell me about", "go on", "continue")
_TERMS_REQUEST_TOKENS = ("terms", "price", "cost", "deal", "conditions", "arrangement")
_LISTENING_INVITE_TOKENS = (
    "i'm listening",
    "im listening",
    "i am listening",
    "go on",
    "continue",
    "tell me more",
    "please continue",
    "what happened next",
    "go ahead",
)

_SOCIAL_PROBE_TRANSACTIONAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:pay|paying|paid|pays|payment|coin|coins|coppers|copper|silver|gold|tip|bribe|"
        r"offering|offer\s+(?:you|them|him|her)|toss(?:es)?\s+(?:him|her|them)?\s*(?:a\s+)?(?:coin|coins))\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bstew\b.*\bstor(?:y|ies)\b|\bstor(?:y|ies)\b.*\bstew\b", re.IGNORECASE),
    re.compile(r"\b(?:for|with)\s+(?:the\s+)?stew\b", re.IGNORECASE),
)
_SOCIAL_PROBE_CHALLENGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:haven't|have\s+not|hadn't|had\s+not)\s+(?:told|said|given)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:nothing|anything)\s+at\s+all\b|\byou\s+(?:haven't|have\s+not)\s+told\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:that|this)\s+(?:isn't|is\s+not|wasn't|was\s+not)\s+(?:an\s+)?answer\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:don't|do\s+not)\s+hedge\b|\bstop\s+(?:hedging|dodging)\b|\b(?:quit|enough)\s+dodging\b",
        re.IGNORECASE,
    ),
)
_SOCIAL_PROBE_DIRECTIONAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhere\s+(?:do|should)\s+i\s+(?:go|start|begin|head)\b", re.IGNORECASE),
    re.compile(r"\bwho\s+should\s+i\s+(?:ask|talk\s+to|speak\s+to|see)\b", re.IGNORECASE),
    re.compile(r"\bwhere\s+can\s+i\s+(?:go|start|begin)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+should\s+i\s+do\s+next\b", re.IGNORECASE),
    re.compile(r"\bwhere\s+to\s+(?:go|start)\b", re.IGNORECASE),
)
_SOCIAL_PROBE_FOLLOWUP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\btell\s+me\s+more\b", re.IGNORECASE),
    re.compile(r"\bgo\s+on\b|\bgo\s+ahead\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+happened\s+(?:then|next)\b", re.IGNORECASE),
    re.compile(r"\bplease\s+continue\b", re.IGNORECASE),
    re.compile(r"\belaborate\b", re.IGNORECASE),
    re.compile(r"\band\?\b", re.IGNORECASE),
    re.compile(r"\b(?:and\s+then|then\s+what)\b", re.IGNORECASE),
)

_VALID_SOCIAL_FOLLOWUP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhy\s+is\s+that\b", re.IGNORECASE),
    re.compile(r"\bwho\s+is\s+that\b", re.IGNORECASE),
    re.compile(r"\bwhere\s*\?"),
    re.compile(r"\bwhere\s+exactly\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s|s|\s+is)\s+going\s+on\b", re.IGNORECASE),
    re.compile(r"\banyone\s+i\s+should\s+steer\s+clear\b", re.IGNORECASE),
    re.compile(r"\bwho\s+should\s+i\s+avoid\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+do\s+you\s+mean\b", re.IGNORECASE),
    re.compile(r"\bfor\s+sure\b", re.IGNORECASE),
    re.compile(r"\bhow\s+come\b", re.IGNORECASE),
)


def is_valid_followup_question(player_text: str) -> bool:
    """Deterministic short list of legitimate follow-up shapes (same conversation thread)."""
    low = str(player_text or "").strip().lower()
    if not low:
        return False
    return any(p.search(low) for p in _VALID_SOCIAL_FOLLOWUP_PATTERNS)


def classify_social_followup_dimension(player_text: str) -> str:
    """Minimal deterministic axis for topic-pressure / exhaustion (not a full ontology)."""
    low = " ".join(str(player_text or "").strip().lower().split())
    if not low:
        return "general"
    # Avoidance/danger before clarification so phrases like "steer clear ... for sure?" stay avoidance.
    if re.search(
        r"\b(steer\s+clear|stay\s+away|keep\s+(?:away|clear)|who\s+should\s+i\s+avoid|"
        r"anyone\s+i\s+should\s+avoid|people\s+(?:to\s+)?avoid|watch\s+out\s+for)\b",
        low,
    ):
        return "avoidance"
    if re.search(r"\b(dangerous|danger\b|peril(?:ous)?|risky|\brisk\b|unsafe|threat(?:en)?|sketchy)\b", low):
        return "danger"
    if re.search(
        r"\b(what\s+do\s+you\s+mean|what(?:'s|s|\s+is)\s+going\s+on|why\s+is\s+that|how\s+come|for\s+sure)\b",
        low,
    ):
        return "clarification"
    if re.search(
        r"\b(where\s+(?:should|do)\s+i|what\s+should\s+i\s+do\s+next|who\s+should\s+i\s+(?:ask|talk|speak|see))\b",
        low,
    ):
        return "next_step"
    if re.search(r"\b(who|whose)\b", low):
        return "identity"
    if re.search(r"\b(where\b|last\s+seen|seen\s+(?:him|her|them))\b", low):
        return "location"
    if re.search(
        r"\b(tied\s+to|affiliated|faction|who\s+does\s+(?:he|she|they)\s+work|serve\s+house|house\s+\w+)\b",
        low,
    ):
        return "affiliation"
    return "general"


def _merge_player_text_with_segmented_turn(
    player_text: Optional[str],
    segmented_turn: Optional[Dict[str, Any]],
) -> str:
    """Rejoin turn segments for probe classification (mirrors api dialogue merge, without importing api)."""
    if not isinstance(segmented_turn, dict):
        return str(player_text or "").strip()
    ordered_keys = (
        "declared_action_text",
        "spoken_text",
        "adjudication_question_text",
        "observation_intent_text",
    )
    parts: List[str] = []
    seen: set[str] = set()
    for key in ordered_keys:
        raw = segmented_turn.get(key)
        if not isinstance(raw, str):
            continue
        s = raw.strip()
        if not s or s in seen:
            continue
        parts.append(s)
        seen.add(s)
    return " ".join(parts) if parts else str(player_text or "").strip()


def classify_social_probe_move(
    *,
    player_text: str,
    segmented_turn: dict | None,
    current_target_id: str | None,
    current_topic_key: str | None,
) -> Dict[str, str]:
    """Classify a small set of conversational probe families for deterministic engine contracts.

    ``current_target_id`` / ``current_topic_key`` are optional; they only enrich the ``reason`` string.
    """
    merged = _merge_player_text_with_segmented_turn(player_text, segmented_turn)
    low = merged.strip().lower()
    if not low:
        return {"probe_move": "none", "reason": "empty_text"}
    scope_bits: List[str] = []
    tid = str(current_target_id or "").strip()
    if tid:
        scope_bits.append(f"target={tid}")
    tk = str(current_topic_key or "").strip()
    if tk:
        scope_bits.append(f"topic_key={tk}")
    scope = ("; " + ", ".join(scope_bits)) if scope_bits else ""

    for i, pat in enumerate(_SOCIAL_PROBE_TRANSACTIONAL_PATTERNS):
        if pat.search(merged):
            return {"probe_move": "transactional", "reason": f"matched_transactional_pattern[{i}]{scope}"}
    for i, pat in enumerate(_SOCIAL_PROBE_CHALLENGE_PATTERNS):
        if pat.search(merged):
            return {"probe_move": "challenge", "reason": f"matched_challenge_pattern[{i}]{scope}"}
    for i, pat in enumerate(_SOCIAL_PROBE_DIRECTIONAL_PATTERNS):
        if pat.search(merged):
            return {"probe_move": "directional", "reason": f"matched_directional_pattern[{i}]{scope}"}
    for i, pat in enumerate(_SOCIAL_PROBE_FOLLOWUP_PATTERNS):
        if pat.search(merged):
            return {"probe_move": "followup", "reason": f"matched_followup_pattern[{i}]{scope}"}

    return {"probe_move": "none", "reason": "no_probe_family_matched" + scope}


def _social_probe_deterministic_contract(
    *,
    probe_move: str,
    npc_name: str,
    exhausted: bool,
    prior_reveal: bool,
) -> Dict[str, Any]:
    """Build reply contract + hint for a classified social_probe when no topic row fires."""
    nm = npc_name.strip() or "the NPC"
    move = (probe_move or "none").strip().lower()

    if move == "transactional":
        if exhausted:
            return {
                "success": True,
                "npc_reply_expected": True,
                "reply_kind": "explanation",
                "probe_outcome": "actionable_redirect",
                "probe_outcome_reason": "engine_topics_exhausted_trade_seeks_next_step",
                "hint": (
                    f"{nm} should treat this as a concrete offer (coin, meal, favor) and answer with either "
                    "a partial honest detail they are willing to sell *or* a sharp redirect (who to ask / where "
                    "to go) grounded in what they can credibly know—no dead-air shrug."
                ),
                "deltas": None,
            }
        return {
            "success": True,
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "probe_outcome": "partial_or_trade",
            "probe_outcome_reason": "trade_pressure_with_remaining_engine_topics",
            "hint": (
                f"{nm} should accept or haggle the trade and supply a partial, concrete detail—still bounded "
                "to established facts and scene knowledge."
            ),
            "deltas": None,
        }

    if move == "followup":
        return {
            "success": True,
            "npc_reply_expected": True,
            "reply_kind": "explanation",
            "probe_outcome": "guarded_continuation" if exhausted else "partial_or_clarify",
            "probe_outcome_reason": "followup_after_exhaustion" if exhausted else "followup_extends_thread",
            "hint": (
                f"{nm} should answer the follow-up with an explicit stance: extend with a guarded detail, "
                "tighten wording on what they already said, or—if they are tapped out—say so plainly and name "
                "a next person, place, or practice to try. No empty nodding."
            ),
            "deltas": None,
        }

    if move == "challenge":
        deltas: Optional[Dict[str, int]] = {"suspicion": 1} if prior_reveal else None
        if not prior_reveal:
            return {
                "success": False,
                "npc_reply_expected": True,
                "reply_kind": "refusal",
                "probe_outcome": "pushback_rebuke",
                "probe_outcome_reason": "challenge_without_prior_engine_reveal",
                "hint": (
                    f"{nm} should push back: the accusation is unfair or premature, keep it short, and set a "
                    "boundary—without granting new intel they have not offered yet."
                ),
                "deltas": None,
            }
        if exhausted:
            return {
                "success": True,
                "npc_reply_expected": True,
                "reply_kind": "explanation",
                "probe_outcome": "friction_or_explicit_limit",
                "probe_outcome_reason": "challenge_after_prior_with_no_further_topics",
                "hint": (
                    f"{nm} already gave something; now they should clarify the earlier point, sharpen a warning, "
                    "say plainly that is all they know, or show irritation/suspicion—include a visible cost "
                    "(tone, impatience, conditions) and, when honest, a redirect for where to learn more."
                ),
                "deltas": deltas,
            }
        return {
            "success": True,
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "probe_outcome": "clarify_or_sharpen_prior",
            "probe_outcome_reason": "challenge_with_remaining_topics_but_no_row_fired",
            "hint": (
                f"{nm} should refine or stress-test what they already revealed—tighter detail, caveat, or "
                "warning—without pretending they said nothing."
            ),
            "deltas": deltas,
        }

    if move == "directional":
        return {
            "success": True,
            "npc_reply_expected": True,
            "reply_kind": "explanation",
            "probe_outcome": "actionable_lead_or_redirect",
            "probe_outcome_reason": "directional_request_defaults_to_concrete_next_step",
            "hint": (
                f"{nm} must answer with at least one actionable thread: a named role to speak with, a place to "
                "check, or a repeatable crowd practice—tight and playable, not vague reassurance."
            ),
            "deltas": None,
        }

    return {
        "success": None,
        "npc_reply_expected": False,
        "reply_kind": "reaction",
        "probe_outcome": "none",
        "probe_outcome_reason": "unclassified_probe",
        "hint": "",
        "deltas": None,
    }


def social_intent_class(kind: str) -> str:
    """Classify social action kind into exchange vs maneuver."""
    k = (kind or "").strip().lower()
    if k in SOCIAL_MANEUVER_KINDS:
        return "social_maneuver"
    return "social_exchange"

# Verb patterns for parse_social_intent: (pattern, action_type, extracts_target)
SOCIAL_PATTERNS = [
    (r"\bpersuade\s+(?:the\s+)?(.+?)(?:\s+to\s+|\s+that\s+)?\.?$", "persuade", True),
    (r"\bpersuade\s+(?:the\s+)?(.+?)\b", "persuade", True),
    (r"\bintimidate\s+(?:the\s+)?(.+?)(?:\s+into\s+|\s+to\s+)?\.?$", "intimidate", True),
    (r"\bintimidate\s+(?:the\s+)?(.+?)\b", "intimidate", True),
    (r"\bdeceive\s+(?:the\s+)?(.+?)(?:\s+into\s+|\s+about\s+)?\.?$", "deceive", True),
    (r"\bdeceive\s+(?:the\s+)?(.+?)\b", "deceive", True),
    (r"\bbarter\s+(?:with\s+)?(?:the\s+)?(.+?)(?:\s+for\s+)?\.?$", "barter", True),
    (r"\bbarter\s+(?:with\s+)?(?:the\s+)?(.+?)\b", "barter", True),
    (r"\brecruit\s+(?:the\s+)?(.+?)(?:\s+to\s+|\s+for\s+)?\.?$", "recruit", True),
    (r"\brecruit\s+(?:the\s+)?(.+?)\b", "recruit", True),
    (r"\b(?:ask|question|query)\s+(?:the\s+)?(.+?)(?:\s+about\s+)?\.?$", "question", True),
    (r"\b(?:talk\s+to|talk\s+with|speak\s+to|speak\s+with|chat\s+with|greet)\s+(?:the\s+)?(.+?)(?:\s+about\s+)?\.?$", "question", True),
    (r"\b(gauge|approach)\s+(?:the\s+)?(.+?)\.?$", "social_probe", True),
]


def parse_social_intent(
    text: str,
    scene_envelope: Optional[Dict[str, Any]] = None,
    world: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Parse freeform player input into a structured social action.

    Returns structured action with id, label, type (question|persuade|intimidate|etc.),
    prompt, target_id. Returns None when no social pattern matches or when world has no npcs.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.strip()
    if not t:
        return None
    low = t.lower()

    npcs = (world or {}).get("npcs") or []
    if not isinstance(npcs, list) or len(npcs) == 0:
        return None

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()

    for pattern, action_type, extracts in SOCIAL_PATTERNS:
        m = re.search(pattern, low, re.IGNORECASE)
        if not m:
            continue
        target = None
        if extracts and m.lastindex and m.lastindex >= 2:
            target = m.group(2).strip()
        elif extracts and m.lastindex:
            target = m.group(1).strip()
        if target and len(target) > 50:
            target = target[:50]
        target_slug = slugify(target) if target else None
        for npc in npcs:
            if not isinstance(npc, dict):
                continue
            nid = str(npc.get("id") or "").strip()
            name = str(npc.get("name") or "").strip()
            loc = npc.get("location") or npc.get("scene_id") or ""
            loc = str(loc).strip() if loc else ""
            if not nid or loc != scene_id:
                continue
            if target_slug and (slugify(nid) == target_slug or slugify(name) == target_slug or target_slug in slugify(nid) or target_slug in slugify(name)):
                return {
                    "id": slugify(f"{action_type}-{nid}") or "social",
                    "label": t,
                    "type": action_type,
                    "social_intent_class": social_intent_class(action_type),
                    "prompt": t,
                    "target_id": nid,
                    "targetEntityId": nid,
                }
        if target:
            return {
                "id": slugify(f"{action_type}-{target}")[:40] or "social",
                "label": t,
                "type": action_type,
                "social_intent_class": social_intent_class(action_type),
                "prompt": t,
                "target_id": target,
                "targetEntityId": target,
            }
    return None


def _get_skill_modifier(character: Dict[str, Any], skill_id: str) -> int:
    """Return character's skill modifier; 0 if skill not present."""
    if not character or not isinstance(character.get("skills"), dict):
        return 0
    v = character["skills"].get(skill_id)
    if v is None:
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _resolve_skill_for_kind(kind: str, character: Dict[str, Any]) -> Optional[str]:
    """Return effective skill_id for social kind. Deceive falls back to diplomacy if bluff absent."""
    entry = SOCIAL_SKILL_MAP.get(kind)
    if entry is None:
        return None
    skill_id, _ = entry
    if skill_id == "bluff":
        skills = character.get("skills") or {}
        if "bluff" in skills and skills.get("bluff") is not None:
            return "bluff"
        return "diplomacy"  # Fallback: no crash
    return skill_id


def find_npc_by_target(
    world: Dict[str, Any],
    target_hint: str,
    scene_id: str,
) -> Optional[Dict[str, Any]]:
    """Find NPC by target id or approximate name. Must be in scene (scene_id or location).

    Returns NPC dict or None if not found/unreachable.
    """
    if not target_hint or not isinstance(target_hint, str):
        return None
    hint = target_hint.strip()
    if not hint:
        return None
    hint_slug = slugify(hint)

    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return None

    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        name = str(npc.get("name") or "").strip()
        loc = npc.get("location") or npc.get("scene_id") or ""
        loc = str(loc).strip() if loc else ""

        if not nid:
            continue
        # Must be in current scene; unknown location does not count as in-scene.
        if loc != scene_id:
            continue

        if nid == hint or nid.lower() == hint.lower():
            return npc
        if slugify(nid) == hint_slug or hint_slug in slugify(nid):
            return npc
        if name and (name.lower() == hint.lower() or slugify(name) == hint_slug or hint_slug in slugify(name)):
            return npc
    return None


def _find_world_npc_by_target(world: Dict[str, Any], target_hint: str) -> Optional[Dict[str, Any]]:
    if not target_hint or not isinstance(target_hint, str):
        return None
    hint = target_hint.strip()
    if not hint:
        return None
    hint_slug = slugify(hint)
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return None
    for npc in npcs:
        if not isinstance(npc, dict):
            continue
        nid = str(npc.get("id") or "").strip()
        name = str(npc.get("name") or "").strip()
        if not nid:
            continue
        if nid == hint or nid.lower() == hint.lower():
            return npc
        if slugify(nid) == hint_slug or hint_slug in slugify(nid):
            return npc
        if name and (name.lower() == hint.lower() or slugify(name) == hint_slug or hint_slug in slugify(name)):
            return npc
    return None


def set_active_interaction_target(
    session: Dict[str, Any],
    npc_id: Optional[str],
    *,
    kind: Optional[str] = "social",
) -> Dict[str, Any]:
    """Compatibility wrapper; owner API now lives in interaction_context."""
    if isinstance(kind, str) and kind.strip().lower() != "social":
        return update_interaction_context_for_non_social(session, kind)
    return set_social_target(session, npc_id)


def update_interaction_context_for_non_social(
    session: Dict[str, Any],
    kind: Optional[str],
) -> Dict[str, Any]:
    """Compatibility wrapper; owner API now lives in interaction_context."""
    return set_non_social_activity(session, kind)


def apply_interaction_implied_heuristics(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    text: Optional[str],
) -> Dict[str, Any]:
    """Compatibility wrapper for interaction-context owned implied-input handling."""
    return apply_turn_input_implied_context(session, world, scene_id, text)


def get_npc_dc_modifier(npc: Dict[str, Any], kind: str) -> int:
    """NPC-specific DC modifier from skill_check_modifier or per-kind override."""
    mod = 0
    m = npc.get("skill_check_modifier")
    if isinstance(m, (int, float)):
        mod += int(m)
    overrides = npc.get("skill_check_overrides") or {}
    if isinstance(overrides, dict) and kind in overrides:
        v = overrides[kind]
        if isinstance(v, (int, float)):
            mod += int(v)
    return mod


def _next_topic_to_reveal(
    npc: Dict[str, Any],
    runtime: Dict[str, Any],
    topic_hint: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return next unrevealed topic that matches hint (if any). Topic: {id, text, clue_id?, clue_text?}."""
    topics = npc.get("topics") or npc.get("knowledge") or []
    if not isinstance(topics, list):
        return None
    revealed = set(runtime.get("revealed_topics") or [])
    hint_slug = slugify(topic_hint) if topic_hint else None

    for t in topics:
        if not isinstance(t, dict):
            rec = {"id": str(t)[:40], "text": str(t)} if t else None
            if not rec:
                continue
        else:
            rec = t
        tid = str(rec.get("id") or "").strip()
        if not tid:
            tid = slugify(rec.get("text", ""))[:40] or "topic"
        if tid in revealed:
            continue
        if hint_slug and hint_slug not in slugify(tid) and hint_slug not in slugify(rec.get("text", "")):
            continue
        out: Dict[str, Any] = {
            "id": tid,
            "text": str(rec.get("text") or rec.get("label") or "").strip() or "Unknown.",
            "clue_id": rec.get("clue_id") or rec.get("reveals_clue"),
            "clue_text": rec.get("clue_text"),
        }
        for key in ("leads_to_scene", "leads_to_npc", "leads_to_rumor"):
            v = rec.get(key)
            if isinstance(v, str) and v.strip():
                out[key] = v.strip()
        return out
    return None


def npc_social_knowledge_exhausted(
    world: Dict[str, Any],
    session: Dict[str, Any],
    npc_id: str,
) -> bool:
    """True when the engine has no further topic rows to reveal for this NPC (legitimate ignorance).

    Does not guess about hidden world facts; only mirrors structured ``topics`` / ``knowledge`` vs runtime.
    """
    nid = str(npc_id or "").strip()
    if not nid:
        return True
    npc = npc_dict_by_id(world, nid)
    if not isinstance(npc, dict):
        return True
    runtime = get_npc_runtime(session, nid)
    return _next_topic_to_reveal(npc, runtime, None) is None


def _neutral_social_escalation_outcome() -> Dict[str, Any]:
    return {
        "escalation_level": 0,
        "escalation_reason": "inactive",
        "escalation_effect": "none",
        "force_partial_answer": False,
        "force_actionable_lead": False,
        "add_suspicion": False,
        "trigger_scene_momentum": False,
        "convert_refusal_to_conditioned_offer": False,
        "topic_exhausted": False,
        "effective_reply_kind": None,
        "social_question_dimension": None,
        "topic_exhausted_for_dimension": False,
        "valid_followup_detected": False,
        "prior_same_dimension_answer_exists": False,
    }


def determine_social_escalation_outcome(
    *,
    session: dict,
    scene_id: str,
    npc_id: str | None,
    topic_key: str | None,
    reply_kind: str | None,
    progress_signals: dict | None,
    player_text: str | None = None,
) -> Dict[str, Any]:
    """Deterministic ladder for repeated social probing on the same tracked topic.

    Uses per-scene ``topic_pressure`` / ``topic_pressure_current`` (see :func:`game.gm.register_topic_probe`).
    When the NPC has no engine topics left, escalation demands redirects (ask X / go to Y), not invented facts.

    Returns flags for the narration contract, plus ``effective_reply_kind`` when ``reply_kind`` should advance
    (e.g. refusal -> answer). ``effective_reply_kind`` is for callers to merge into resolution.social.
    """
    sid = str(scene_id or "").strip()
    if not sid or not isinstance(session, dict):
        return _neutral_social_escalation_outcome()

    runtime = get_scene_runtime(session, sid)
    current = runtime.get("topic_pressure_current") if isinstance(runtime.get("topic_pressure_current"), dict) else {}
    tk = str(topic_key or "").strip() or str(current.get("topic_key") or "").strip()
    if not tk:
        return _neutral_social_escalation_outcome()

    speaker_key = str(npc_id or "").strip() or str(current.get("speaker_key") or "").strip() or "__scene__"
    pressure = runtime.get("topic_pressure") if isinstance(runtime.get("topic_pressure"), dict) else {}
    entry = pressure.get(tk) if isinstance(pressure.get(tk), dict) else {}
    targets = entry.get("speaker_targets") if isinstance(entry.get("speaker_targets"), dict) else {}
    s_entry = targets.get(speaker_key) if isinstance(targets.get(speaker_key), dict) else {}
    # Prefer per-speaker repeats; fall back to aggregate topic repeats when targets desynced.
    rc_s = int(s_entry.get("repeat_count") or 0) if isinstance(s_entry, dict) else 0
    rc_agg = int(entry.get("repeat_count") or 0) if isinstance(entry, dict) else 0
    rc = rc_s if rc_s >= 1 else rc_agg
    if rc < 1:
        return _neutral_social_escalation_outcome()

    sig = progress_signals if isinstance(progress_signals, dict) else {}
    knowledge_exhausted = bool(sig.get("npc_knowledge_exhausted"))

    rk = str(reply_kind or "").strip().lower() or None
    pt = str(player_text or current.get("player_text") or "").strip()
    current_dim = classify_social_followup_dimension(pt)
    valid_fu = is_valid_followup_question(pt)
    last_ans = str(entry.get("last_answer") or "").strip()
    prev_probe_dim = str(entry.get("previous_probe_dimension") or "").strip()
    prior_same = bool(
        last_ans
        and _stored_text_supports_dimension(last_ans, current_dim)
        and _player_question_covers_stored_thread(pt, last_ans)
    )
    dim_changed = bool(prev_probe_dim and current_dim != prev_probe_dim)
    topic_exhausted_for_dimension = bool(knowledge_exhausted and prior_same)

    if not knowledge_exhausted:
        topic_exhausted = False
    elif rc == 1:
        topic_exhausted = prior_same
    elif valid_fu and rc == 2:
        topic_exhausted = False
    elif dim_changed:
        topic_exhausted = False
    else:
        topic_exhausted = True

    out = _neutral_social_escalation_outcome()
    out["topic_exhausted"] = topic_exhausted
    out["social_question_dimension"] = current_dim
    out["topic_exhausted_for_dimension"] = topic_exhausted_for_dimension
    out["valid_followup_detected"] = valid_fu
    out["prior_same_dimension_answer_exists"] = prior_same
    out["escalation_level"] = min(rc, 6)
    out["escalation_reason"] = "same_topic_social_probe"
    out["escalation_effect"] = "allow_guarded_or_vague"

    if rc == 1:
        out["escalation_reason"] = "first_attempt_same_topic"
        out["escalation_effect"] = "vague_or_guarded_answer_allowed"
        if rk == "refusal" and valid_fu:
            out["effective_reply_kind"] = "explanation" if current_dim == "clarification" else "answer"
        return out

    if rc == 2:
        out["escalation_reason"] = "second_attempt_same_topic"
        if knowledge_exhausted:
            out["force_actionable_lead"] = True
            out["escalation_effect"] = "redirect_only_no_new_npc_facts"
        else:
            out["force_partial_answer"] = True
            out["escalation_effect"] = "partial_factual_detail_or_redirected_lead"
    elif rc == 3:
        out["force_actionable_lead"] = True
        out["escalation_reason"] = "third_attempt_same_topic"
        if rk == "refusal":
            out["convert_refusal_to_conditioned_offer"] = True
        if knowledge_exhausted:
            out["escalation_effect"] = "explicit_exhaustion_plus_where_to_next"
        else:
            out["force_partial_answer"] = True
            out["escalation_effect"] = "actionable_lead_or_explicit_condition"
    else:
        out["force_actionable_lead"] = True
        out["add_suspicion"] = True
        out["trigger_scene_momentum"] = True
        out["escalation_reason"] = "four_plus_attempts_same_topic"
        if rk == "refusal":
            out["convert_refusal_to_conditioned_offer"] = True
        if knowledge_exhausted:
            out["escalation_effect"] = "visible_friction_with_exhausted_topic_redirect"
        else:
            out["force_partial_answer"] = True
            out["escalation_effect"] = "suspicion_cost_or_scene_event_plus_progress"

    if rk == "refusal" and (rc >= 2 or valid_fu):
        out["effective_reply_kind"] = "explanation" if current_dim == "clarification" else "answer"

    return out


def classify_social_question_dimension(player_text: str) -> str:
    """Deterministic question axis for matching stored factual answers (topic pressure / clues)."""
    return classify_social_followup_dimension(player_text)


def _extract_double_quoted_spans(text: str) -> List[str]:
    return re.findall(r"\"([^\"]{6,520})\"", str(text or ""))


_THREAD_MATCH_STOPWORDS = frozenset(
    {
        "what",
        "about",
        "does",
        "this",
        "that",
        "have",
        "been",
        "with",
        "from",
        "your",
        "here",
        "there",
        "when",
        "where",
        "which",
        "would",
        "could",
        "should",
        "them",
        "they",
        "their",
        "those",
        "these",
        "who",
        "whom",
        "whose",
        "into",
        "onto",
        "upon",
        "some",
        "many",
        "much",
        "very",
        "just",
        "only",
        "even",
        "still",
        "also",
        "then",
        "than",
        "such",
    }
)


def _player_question_covers_stored_thread(player_text: str, stored: str) -> bool:
    """Avoid surfacing unrelated topic_pressure answers on a fresh 'who/what/where' question."""
    pl = str(player_text or "").strip().lower()
    st = str(stored or "").strip().lower()
    if not pl or not st:
        return False
    if re.search(
        r"\b(he|she|him|her|referring|you mean|the one|that guy|that woman|that man)\b",
        pl,
    ):
        return True
    toks = [t for t in re.findall(r"[a-z]{4,}", pl) if t not in _THREAD_MATCH_STOPWORDS]
    return any(t in st for t in toks[:18])


def _trim_utterance(s: str, max_len: int = 280) -> str:
    u = " ".join(str(s or "").strip().split())
    if len(u) <= max_len:
        return u
    return u[: max_len - 1].rstrip(" ,;:") + "…"


def _stored_text_supports_dimension(stored: str, dimension: str) -> bool:
    if not str(stored or "").strip():
        return False
    t = str(stored)
    low = t.lower()
    if dimension == "identity":
        if re.search(r"\b(?:known\s+as|called|name(?:'s| is)|they\s+call\s+(?:him|her|them))\s+[A-Za-z]", t):
            return True
        for q in _extract_double_quoted_spans(t):
            words = re.findall(r"\b[A-Z][a-z]{2,}\b", q)
            skip = {"The", "He", "She", "They", "But", "And", "You", "House", "Tavern"}
            if any(w not in skip for w in words):
                return True
        return False
    if dimension == "location":
        return bool(
            re.search(
                r"\b(?:near|at|by|toward|towards|east|west|north|south|road|gate|milestone|square|market|lane)\b",
                low,
            )
        )
    if dimension == "affiliation":
        return bool(re.search(r"\b(?:house|tied\s+to|works\s+for|faction|retainer|verevin)\b", low))
    if dimension == "next_step":
        return bool(re.search(r"\b(?:speak\s+to|talk\s+to|go\s+to|head\s+to|try|ask|find|check)\b", low))
    if dimension == "danger":
        return bool(
            re.search(
                r"\b(?:danger|dangerous|risk|peril|threat|unsafe|trouble|hurt|harm|attack|violence|sketchy)\b",
                low,
            )
        )
    if dimension == "avoidance":
        return bool(
            re.search(
                r"\b(?:avoid|steer|clear|away|watch\s+(?:your|out)|unfriendly|thug|enem(?:y|ies)|threat|coin|your\s+back|disappear)\b",
                low,
            )
        )
    if dimension == "clarification":
        return len(low.strip()) >= 24
    return bool(
        re.search(
            r"\b(?:saw|seen|heard|named|called|patrol|road|gate|milestone|house|tied)\b",
            low,
        )
    )


def _pick_utterance_from_stored(stored: str, dimension: str) -> str:
    """Prefer the shortest quote fragment that still matches *dimension* (avoids mixed-form strict-social drops)."""
    best = ""
    for q in _extract_double_quoted_spans(stored):
        parts = re.split(r"(?<=[.!?])\s+", q.strip())
        candidates: List[str] = []
        for p in parts:
            ps = p.strip()
            if not ps:
                continue
            if _stored_text_supports_dimension(ps, dimension):
                candidates.append(_trim_utterance(ps))
        if _stored_text_supports_dimension(q, dimension) or dimension == "general":
            candidates.append(_trim_utterance(q))
        for c in candidates:
            if c and (not best or len(c) < len(best)):
                best = c
        if best and dimension != "general":
            break
    if best:
        return best
    if _stored_text_supports_dimension(stored, dimension):
        return _trim_utterance(stored)
    return ""


def format_structured_fact_social_line(resolution: Dict[str, Any] | None, fact_text: str) -> str:
    """Single-sentence NPC line for strict-social emission (passes first-sentence contract scope)."""
    social = (resolution or {}).get("social") if isinstance((resolution or {}).get("social"), dict) else {}
    name = str((social or {}).get("npc_name") or "").strip()
    npc_id = str((social or {}).get("npc_id") or "").strip()
    speaker = name or (npc_id.replace("_", " ").replace("-", " ").title() if npc_id else "The guard")
    inner = str(fact_text or "").strip().strip('"').strip()
    if not inner:
        return ""
    low_i = inner.lower()
    # Ensure GM question-resolution contract sees an explicit social-answer shape (word is / they say / heard).
    if not re.search(
        r"\b(they\s+say|word\s+is|i\s+heard|i've\s+heard|i\s+have\s+heard|people\s+say|rumor\s+is)\b",
        low_i,
    ):
        inner = f"Word is, {inner[0].lower()}{inner[1:]}" if len(inner) > 1 else f"Word is, {inner}"
    if not re.search(r"[.!?…]$", inner):
        inner += "."
    return f'{speaker} mutters, "{inner}"'


def select_best_social_answer_candidate(
    *,
    session: dict,
    scene_id: str,
    npc_id: str | None,
    topic_key: str | None,
    player_text: str,
    resolution: dict | None,
) -> dict:
    """Choose the strongest deterministic social answer source for this turn (precedence A→D)."""
    sid = str(scene_id or "").strip()
    text_in = " ".join(str(player_text or "").strip().split())
    dimension = classify_social_question_dimension(text_in)

    def _refusal(conf: float = 0.0) -> dict:
        return {
            "answer_kind": "refusal",
            "text": None,
            "source": "none",
            "confidence": conf,
        }

    if not sid or not isinstance(session, dict):
        return _refusal()

    rt = get_scene_runtime(session, sid)
    tcur = rt.get("topic_pressure_current") if isinstance(rt.get("topic_pressure_current"), dict) else {}
    tk = str(topic_key or "").strip() or str(tcur.get("topic_key") or "").strip()
    speaker_key = str(tcur.get("speaker_key") or "").strip()
    nid = str(npc_id or "").strip()

    def _speaker_aligned() -> bool:
        if not nid or not speaker_key:
            return True
        a, b = speaker_key.lower(), nid.lower()
        return a == b or a in b or b in a

    pressure = rt.get("topic_pressure") if isinstance(rt.get("topic_pressure"), dict) else {}

    # --- A: structured topic payload on resolution, then topic pressure last_answer ---
    res_soc = (resolution or {}).get("social") if isinstance((resolution or {}).get("social"), dict) else {}
    topic_rev = res_soc.get("topic_revealed") if isinstance(res_soc.get("topic_revealed"), dict) else None
    if isinstance(topic_rev, dict):
        clue = str(topic_rev.get("clue_text") or topic_rev.get("text") or "").strip()
        if clue and _stored_text_supports_dimension(clue, dimension):
            utt = _pick_utterance_from_stored(clue, dimension) or _trim_utterance(clue)
            if utt:
                return {
                    "answer_kind": "structured_fact",
                    "text": utt,
                    "source": "resolution:topic_revealed",
                    "confidence": 0.95,
                }

    if tk and isinstance(pressure.get(tk), dict):
        entry = pressure[tk]
        last_ans = str(entry.get("last_answer") or "").strip()
        if (
            last_ans
            and _speaker_aligned()
            and _stored_text_supports_dimension(last_ans, dimension)
            and _player_question_covers_stored_thread(text_in, last_ans)
        ):
            utt = _pick_utterance_from_stored(last_ans, dimension)
            if utt:
                return {
                    "answer_kind": "structured_fact",
                    "text": utt,
                    "source": "topic_pressure:last_answer",
                    "confidence": 0.92,
                }

    # --- B: reconciled clues landed for this scene (session clue_knowledge) ---
    ck = session.get("clue_knowledge") if isinstance(session.get("clue_knowledge"), dict) else {}
    best_txt = ""
    best_src = ""
    best_score = 0.0
    for cid, rec in ck.items():
        if not isinstance(rec, dict):
            continue
        if str(rec.get("source_scene") or "").strip() != sid:
            continue
        clue_line = str(rec.get("text") or "").strip()
        if len(clue_line) < 8:
            continue
        if not _stored_text_supports_dimension(clue_line, dimension):
            continue
        if not _player_question_covers_stored_thread(text_in, clue_line):
            continue
        sc = 0.75
        pres = str(rec.get("presentation") or "").strip().lower()
        if pres == "actionable":
            sc = 0.88
        if sc > best_score:
            best_score = sc
            best_txt = clue_line
            best_src = f"clue_knowledge:{cid}"

    if best_txt:
        utt2 = _pick_utterance_from_stored(best_txt, dimension) or _trim_utterance(best_txt)
        if utt2:
            return {
                "answer_kind": "reconciled_fact",
                "text": utt2,
                "source": best_src,
                "confidence": best_score,
            }

    # --- C: explicit redirect lead in last_answer (same topic) without full factual match ---
    if tk and isinstance(pressure.get(tk), dict):
        entry2 = pressure[tk]
        la2 = str(entry2.get("last_answer") or "").strip()
        if (
            la2
            and _speaker_aligned()
            and not _stored_text_supports_dimension(la2, dimension)
            and _player_question_covers_stored_thread(text_in, la2)
        ):
            low2 = la2.lower()
            if re.search(r"\b(?:speak\s+to|talk\s+to|go\s+to|head\s+to|try\s+the|ask\s+at)\b", low2):
                partial = _pick_utterance_from_stored(la2, "next_step") or _trim_utterance(la2, 220)
                if partial and len(partial) >= 16:
                    return {
                        "answer_kind": "partial_answer",
                        "text": partial,
                        "source": "topic_pressure:last_answer:redirect",
                        "confidence": 0.42,
                    }

    return _refusal(0.1)


def sync_strategy_forced_to_answer_for_valid_followup_alignment(soc: Dict[str, Any]) -> None:
    """If answer-mode already applies and a valid follow-up was detected, align ``strategy_forced_to_answer``.

    Does not choose whether to answer; only synchronizes internal flags with decisions already reflected
    in ``reply_kind`` and escalation metadata.
    """
    if not isinstance(soc, dict):
        return
    if str(soc.get("social_intent_class") or "").strip().lower() != "social_exchange":
        return
    rk = str(soc.get("reply_kind") or "").strip().lower()
    if rk not in ("answer", "explanation", "partial_answer"):
        return
    if soc.get("npc_reply_expected") is not True:
        return
    if soc.get("target_resolved") is not True:
        return
    if soc.get("actor_addressable") is not True:
        return
    if soc.get("valid_followup_detected") is not True:
        return
    if soc.get("topic_exhausted_for_dimension") is not False:
        return
    soc["strategy_forced_to_answer"] = True
    soc["forced_answer_reason"] = "valid_followup_alignment"


def apply_structured_social_answer_candidate_to_resolution(
    *,
    session: dict,
    scene_id: str,
    player_text: str,
    resolution: dict,
) -> None:
    """Upgrade engine social resolution when stored facts already answer the current question."""
    if not isinstance(resolution, dict):
        return
    soc = resolution.get("social")
    if not isinstance(soc, dict):
        return
    if str(soc.get("social_intent_class") or "").strip().lower() != "social_exchange":
        return

    sid = str(scene_id or "").strip()
    nid = str(soc.get("npc_id") or "").strip() or None
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id=sid,
        npc_id=nid,
        topic_key=None,
        player_text=str(player_text or ""),
        resolution=resolution,
    )
    dim = classify_social_question_dimension(str(player_text or ""))
    soc["answer_candidate_selected"] = str(cand.get("answer_kind") or "refusal")
    soc["answer_candidate_source"] = str(cand.get("source") or "none")
    soc["answer_candidate_dimension"] = dim

    rk = str(soc.get("reply_kind") or "").strip().lower()
    succ = resolution.get("success")

    if str(cand.get("answer_kind") or "") not in ("structured_fact", "reconciled_fact", "partial_answer"):
        soc["refusal_suppressed_by_structured_fact"] = False
        return

    # Do not mutate success/reply_kind here: narration/state repair uses refusal vs empty payload to
    # reconcile GM hooks with structured state. Final strict-social emission still applies facts.
    soc["refusal_suppressed_by_structured_fact"] = bool(rk == "refusal" or succ is not True)

    if rk == "refusal" or succ is not True:
        nm = str(soc.get("npc_name") or "the NPC").strip()
        snippet = str(cand.get("text") or "").strip()
        preview = (snippet[:120] + "…") if len(snippet) > 120 else snippet
        resolution["hint"] = (
            f"Stored thread facts already cover this question ({preview}). "
            f"Have {nm} state that information plainly in-character—do not refuse or claim nothing was revealed."
        )


def apply_social_topic_escalation_to_resolution(
    *,
    world: Dict[str, Any],
    session: Dict[str, Any],
    scene: Dict[str, Any],
    user_text: str,
    resolution: Dict[str, Any],
) -> None:
    """After :func:`game.gm.register_topic_probe`, attach escalation metadata and narration contract flags.

    Mutates ``resolution["social"]`` in place. Idempotent for a given turn if topic pressure is unchanged.
    """
    if not isinstance(resolution, dict):
        return
    soc = resolution.get("social")
    if not isinstance(soc, dict):
        return
    if str(soc.get("social_intent_class") or "").strip().lower() != "social_exchange":
        return
    try:
        from game.gm import _is_direct_player_question
    except ImportError:
        return
    if not _is_direct_player_question(str(user_text or "")):
        return
    sc_inner = scene.get("scene") if isinstance(scene.get("scene"), dict) else {}
    sid = str(sc_inner.get("id") or "").strip()
    nid = str(soc.get("npc_id") or "").strip() or None
    if not sid or not nid:
        return
    rk = str(soc.get("reply_kind") or "").strip() or None
    exhausted = npc_social_knowledge_exhausted(world, session, nid)
    esc = determine_social_escalation_outcome(
        session=session,
        scene_id=sid,
        npc_id=nid,
        topic_key=None,
        reply_kind=rk,
        progress_signals={"npc_knowledge_exhausted": exhausted},
        player_text=str(user_text or ""),
    )
    if int(esc.get("escalation_level") or 0) <= 0:
        return
    soc["social_escalation"] = dict(esc)
    for _dk in (
        "social_question_dimension",
        "topic_exhausted_for_dimension",
        "valid_followup_detected",
        "prior_same_dimension_answer_exists",
    ):
        if _dk in esc:
            soc[_dk] = esc[_dk]
    eff = esc.get("effective_reply_kind")
    if isinstance(eff, str) and eff.strip():
        soc["reply_kind"] = eff.strip().lower()
    if esc.get("add_suspicion"):
        tc = int(session.get("turn_counter", 0) or 0)
        apply_npc_runtime_deltas(session, nid, "social_probe", None, tc, deltas={"suspicion": 1})
    sync_strategy_forced_to_answer_for_valid_followup_alignment(soc)


def _infer_reply_expectation(
    action_type: str,
    *,
    prompt: str,
    raw_player_text: Optional[str],
    topic_revealed: bool,
    requires_check: bool,
) -> Tuple[bool, str]:
    """Infer whether the active NPC is expected to deliver a substantive reply now."""
    if requires_check:
        return False, "reaction"

    low = f"{raw_player_text or ''} {prompt or ''}".strip().lower()
    has_question_mark = "?" in low
    has_question_word = bool(re.search(r"\b(" + "|".join(_DIRECT_QUESTION_WORDS) + r")\b", low))
    has_direct_question = bool(has_question_mark or has_question_word)
    asks_name = any(tok in low for tok in _NAME_REQUEST_TOKENS)
    asks_destination = any(tok in low for tok in _DESTINATION_REQUEST_TOKENS)
    asks_explanation = any(tok in low for tok in _EXPLANATION_REQUEST_TOKENS)
    asks_terms = any(tok in low for tok in _TERMS_REQUEST_TOKENS)
    invites_continue = any(tok in low for tok in _LISTENING_INVITE_TOKENS)
    explicit_info_request = bool(asks_name or asks_destination or asks_explanation or asks_terms)

    if action_type in SOCIAL_MANEUVER_KINDS:
        return True, "reaction"

    if invites_continue:
        return True, "explanation"

    if action_type == "question" or has_direct_question or explicit_info_request:
        if not topic_revealed and (has_direct_question or explicit_info_request):
            return True, "refusal"
        if asks_explanation:
            return True, "explanation"
        return True, "answer"

    if action_type == "social_probe":
        if has_direct_question or explicit_info_request:
            if not topic_revealed:
                return True, "refusal"
            if asks_explanation:
                return True, "explanation"
            return True, "answer"
        return False, "reaction"

    return False, "reaction"


def _social_payload_with_reply_expectation(
    payload: Dict[str, Any],
    *,
    action_type: str,
    prompt: str,
    raw_player_text: Optional[str],
    topic_revealed: bool,
    requires_check: bool,
    debug_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    expected, reply_kind = _infer_reply_expectation(
        action_type,
        prompt=prompt,
        raw_player_text=raw_player_text,
        topic_revealed=topic_revealed,
        requires_check=requires_check,
    )
    out = dict(payload)
    out["npc_reply_expected"] = bool(expected)
    out["reply_kind"] = reply_kind
    if isinstance(debug_fields, dict) and debug_fields:
        out.update(debug_fields)
    return out


def _social_target_debug_fields(
    session: Dict[str, Any],
    world: Dict[str, Any],
    scene_id: str,
    scene_envelope: Dict[str, Any],
    normalized_action: Dict[str, Any],
    auth: Dict[str, Any],
    *,
    sync_meta: Optional[Dict[str, Any]] = None,
    target_binding: Optional[Dict[str, Any]] = None,
    target_profile_hints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    na = normalized_action if isinstance(normalized_action, dict) else {}
    cand_raw = na.get("target_id") or na.get("targetEntityId")
    cand = str(cand_raw).strip() if cand_raw is not None and str(cand_raw).strip() else None
    ids = scene_addressable_actor_ids(
        world,
        scene_id,
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    out: Dict[str, Any] = {
        "target_source": auth.get("source"),
        "target_reason": auth.get("reason"),
        "target_candidate_id": cand,
        "target_candidate_valid": bool(cand and cand in ids),
    }
    grb = auth.get("generic_role_rebind")
    if isinstance(grb, dict):
        out["generic_role_rebind"] = grb
    sm = sync_meta if isinstance(sync_meta, dict) else {}
    out["stale_interlocutor_cleared"] = bool(sm.get("stale_interlocutor_cleared"))
    ac = sm.get("addressability_checked_against")
    if isinstance(ac, list) and ac:
        out["addressability_checked_against"] = list(ac)
    resolved_id = str(auth.get("npc_id") or "").strip()
    for dk in (
        "declared_switch_detected",
        "declared_switch_target_actor_id",
        "continuity_overridden_by_declared_switch",
        "spoken_vocative_detected",
        "spoken_vocative_target_actor_id",
        "continuity_overridden_by_spoken_vocative",
    ):
        if dk in auth:
            out[dk] = auth.get(dk)
    if resolved_id:
        ad: Dict[str, Any] = {}
        is_actor_addressable_in_current_scene(
            session, scene_envelope if isinstance(scene_envelope, dict) else None, resolved_id, world=world, debug=ad
        )
        if "actor_addressable" in ad:
            out["actor_addressable"] = ad.get("actor_addressable")
        if "addressability_checked_against" in ad and not out.get("addressability_checked_against"):
            out["addressability_checked_against"] = ad.get("addressability_checked_against")
    elif cand:
        ad2: Dict[str, Any] = {}
        is_actor_addressable_in_current_scene(
            session, scene_envelope if isinstance(scene_envelope, dict) else None, cand, world=world, debug=ad2
        )
        if "actor_addressable" in ad2:
            out["actor_addressable"] = ad2.get("actor_addressable")
    tb = target_binding if isinstance(target_binding, dict) else {}
    if tb:
        out["target_binding"] = dict(tb)
    tph = target_profile_hints if isinstance(target_profile_hints, dict) else {}
    if tph:
        out["target_profile_hints"] = dict(tph)
    return out


def apply_npc_runtime_deltas(
    session: Dict[str, Any],
    npc_id: str,
    kind: str,
    success: Optional[bool],
    turn_counter: int,
    deltas: Optional[Dict[str, int]] = None,
) -> None:
    """Apply attitude/trust/fear/suspicion deltas to NPC runtime. Mutates session."""
    rt = get_npc_runtime(session, npc_id)
    rt["last_interaction_turn"] = turn_counter

    if deltas:
        for key in ("attitude", "trust", "fear", "suspicion"):
            if key in deltas and isinstance(deltas[key], (int, float)):
                current = int(rt.get(key, 0) or 0)
                rt[key] = max(-5, min(5, current + int(deltas[key])))

    if success is True:
        if kind in ("persuade", "question", "social_probe", "barter"):
            rt["trust"] = min(5, int(rt.get("trust", 0) or 0) + 1)
        if kind == "intimidate":
            rt["fear"] = min(5, int(rt.get("fear", 0) or 0) + 1)
        if kind == "deceive":
            rt["suspicion"] = min(5, int(rt.get("suspicion", 0) or 0) + 1)
    elif success is False:
        if kind == "intimidate":
            rt["attitude"] = max(-5, int(rt.get("attitude", 0) or 0) - 1)


def _social_result_dict_with_incoming_metadata(
    result: SocialEngineResult, incoming_meta: Dict[str, Any]
) -> Dict[str, Any]:
    out = result.to_dict()
    if incoming_meta:
        merged = dict(incoming_meta)
        prev = out.get("metadata")
        if isinstance(prev, dict):
            merged = {**prev, **merged}
        out["metadata"] = merged
    return out


def resolve_social_action(
    scene_envelope: Dict[str, Any],
    session: Dict[str, Any],
    world: Dict[str, Any],
    normalized_action: Dict[str, Any],
    raw_player_text: Optional[str] = None,
    character: Optional[Dict[str, Any]] = None,
    turn_counter: int = 0,
) -> Dict[str, Any]:
    """Produce a structured SocialEngineResult for the GM prompt. Deterministic, engine-first.

    Mutates session.npc_runtime (deltas, revealed_topics) when an NPC is found and resolved.

    Returns:
        kind, action_id, label, prompt, success, hint, social {npc_id, npc_name, skill_check?, topic_revealed?, ...}
    """
    incoming_action_meta = (
        dict(normalized_action["metadata"]) if isinstance(normalized_action.get("metadata"), dict) else {}
    )

    scene = (scene_envelope or {}).get("scene", {}) if isinstance(scene_envelope, dict) else {}
    scene_id = str(scene.get("id") or "").strip()

    action_type = (normalized_action.get("type") or "social_probe").strip().lower()
    if action_type not in SOCIAL_KINDS:
        action_type = "social_probe"
    intent_class = social_intent_class(action_type)

    label = str(normalized_action.get("label") or "").strip() or "Social action"
    prompt = str(normalized_action.get("prompt") or raw_player_text or label).strip() or label
    action_id = str(normalized_action.get("id") or "").strip() or "social"
    target_id = normalized_action.get("target_id") or normalized_action.get("targetEntityId") or raw_player_text

    sync_meta = synchronize_scene_addressability(
        session, scene_envelope if isinstance(scene_envelope, dict) else None, world
    )

    # Authoritative social target selection happens here. After this point, emission/validation may reject
    # output text, but may not null the selected target unless it is invalidated by scene scope.
    seg_for_auth: Dict[str, Any] | None = None
    if isinstance(normalized_action, dict):
        md_na = normalized_action.get("metadata")
        if isinstance(md_na, dict):
            raw_seg = md_na.get("segmented_turn")
            if isinstance(raw_seg, dict):
                seg_for_auth = raw_seg

    auth = resolve_authoritative_social_target(
        session,
        world,
        scene_id,
        player_text=raw_player_text,
        normalized_action=normalized_action,
        scene_envelope=scene_envelope,
        allow_first_roster_fallback=False,
        segmented_turn=seg_for_auth,
    )
    na = normalized_action if isinstance(normalized_action, dict) else {}
    explicit_norm = str(na.get("target_id") or na.get("targetEntityId") or "").strip()
    if explicit_norm and not (auth.get("target_resolved") and auth.get("npc_id")):
        inv_dbg: Dict[str, Any] = {}
        if is_actor_addressable_in_current_scene(
            session,
            scene_envelope if isinstance(scene_envelope, dict) else None,
            explicit_norm,
            world=world,
            debug=inv_dbg,
        ):
            npc_hint = npc_dict_by_id(world, explicit_norm)
            nm = (
                str((npc_hint or {}).get("name") or "").strip()
                if isinstance(npc_hint, dict)
                else ""
            ) or explicit_norm.replace("_", " ").replace("-", " ").title()
            auth = {
                "npc_id": explicit_norm,
                "npc_name": nm,
                "target_resolved": True,
                "offscene_target": False,
                "source": "explicit_target",
                "reason": "addressability invariant: normalized target is canonically present in scene",
            }

    auth, target_binding, target_profile_hints = finalize_social_target_with_promotion(
        session,
        world,
        scene_id,
        auth,
        action_type=action_type,
        turn_counter=turn_counter,
        scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
        raw_player_text=raw_player_text,
    )

    dbg = _social_target_debug_fields(
        session,
        world,
        scene_id,
        scene_envelope,
        normalized_action,
        auth,
        sync_meta=sync_meta,
        target_binding=target_binding or None,
        target_profile_hints=target_profile_hints or None,
    )

    if auth.get("offscene_target") and auth.get("npc_id"):
        known_target_id = str(auth.get("npc_id") or "").strip()
        known_target_name = str(auth.get("npc_name") or "").strip()
        hint = (
            f"{known_target_name or 'That person'} is no longer here to answer. "
            "Narrate that naturally from the current scene instead of attributing the reply to them."
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=False,
            hint=hint,
            social={
                "social_intent_class": intent_class,
                "npc_id": known_target_id or None,
                "npc_name": known_target_name or None,
                "target_resolved": False,
                "skill_check": None,
                "npc_reply_expected": False,
                "reply_kind": "reaction",
                "offscene_target": True,
                **dbg,
            },
            requires_check=False,
        )
        return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

    if not (auth.get("target_resolved") and auth.get("npc_id")):
        known_target = _find_world_npc_by_target(world, str(target_id or "")) if target_id else None
        known_target_id = str((known_target or {}).get("id") or "").strip()
        known_target_name = str((known_target or {}).get("name") or "").strip()
        known_target_loc = str((known_target or {}).get("location") or (known_target or {}).get("scene_id") or "").strip()
        is_offscene_target = bool(known_target_id and known_target_loc and known_target_loc != scene_id)
        if is_offscene_target:
            hint = (
                f"{known_target_name or 'That person'} is no longer here to answer. "
                "Narrate that naturally from the current scene instead of attributing the reply to them."
            )
        else:
            hint = "No matching NPC found in this scene. Narrate that the player's social attempt has no clear target or the intended person is not present."
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=False,
            hint=hint,
            social={
                "social_intent_class": intent_class,
                "npc_id": known_target_id or None,
                "npc_name": known_target_name or None,
                "target_resolved": False,
                "skill_check": None,
                "npc_reply_expected": False,
                "reply_kind": "reaction",
                "offscene_target": is_offscene_target,
                **dbg,
            },
            requires_check=False,
        )
        return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

    npc_id = str(auth.get("npc_id") or "").strip()
    npc = npc_dict_by_id(world, npc_id)
    if npc is None:
        roster = canonical_scene_addressable_roster(
            world,
            scene_id,
            scene_envelope=scene_envelope if isinstance(scene_envelope, dict) else None,
            session=session if isinstance(session, dict) else None,
        )
        npc = next((x for x in roster if isinstance(x, dict) and str(x.get("id") or "").strip() == npc_id), None)
    if not isinstance(npc, dict):
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=False,
            hint="No matching NPC found in this scene. Narrate that the player's social attempt has no clear target or the intended person is not present.",
            social={
                "social_intent_class": intent_class,
                "npc_id": None,
                "npc_name": None,
                "target_resolved": False,
                "skill_check": None,
                "npc_reply_expected": False,
                "reply_kind": "reaction",
                "offscene_target": False,
                **dbg,
            },
            requires_check=False,
        )
        return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

    npc_name = str(npc.get("name") or auth.get("npc_name") or "the NPC").strip()

    runtime = get_npc_runtime(session, npc_id)
    set_active_interaction_target(session, npc_id, kind="social")

    # Initialize from NPC baseline
    base_attitude = npc.get("disposition") or npc.get("attitude") or "neutral"
    if isinstance(base_attitude, str):
        attitude_map = {"friendly": 2, "helpful": 1, "neutral": 0, "unfriendly": -1, "hostile": -2}
        runtime.setdefault("attitude", attitude_map.get(base_attitude.lower(), 0))
    runtime.setdefault("trust", 0)
    runtime.setdefault("fear", 0)
    runtime.setdefault("suspicion", 0)
    runtime.setdefault("known_topics", [])
    runtime.setdefault("revealed_topics", [])

    # Question/social_probe: no skill check by default; may reveal topic
    if action_type in ("question", "social_probe"):
        # Only use topic hint when explicitly provided; otherwise reveal first available topic
        topic_hint = normalized_action.get("topic") if normalized_action.get("topic") else None
        topic_rec = _next_topic_to_reveal(npc, runtime, topic_hint)

        if topic_rec:
            revealed_ids = runtime.get("revealed_topics") or []
            if topic_rec["id"] not in revealed_ids:
                revealed_ids.append(topic_rec["id"])
                runtime["revealed_topics"] = revealed_ids

            clue_text = topic_rec.get("clue_text") or topic_rec.get("text")
            clue_id = topic_rec.get("clue_id")
            discovered = [clue_text] if clue_text else []

            apply_npc_runtime_deltas(session, npc_id, action_type, True, turn_counter)
            social_payload = _social_payload_with_reply_expectation(
                {
                    "social_intent_class": intent_class,
                    "npc_id": npc_id,
                    "npc_name": npc_name,
                    "target_resolved": True,
                    "topic_revealed": topic_rec,
                    "skill_check": None,
                },
                action_type=action_type,
                prompt=prompt,
                raw_player_text=raw_player_text,
                topic_revealed=True,
                requires_check=False,
                debug_fields=dbg,
            )

            result = SocialEngineResult(
                kind=action_type,
                action_id=action_id,
                label=label,
                prompt=prompt,
                success=True,
                clue_id=clue_id,
                discovered_clues=discovered,
                state_changes={"topic_revealed": True, "npc_id": npc_id},
                hint=f"Player questioned {npc_name} and learned: {topic_rec['text'][:100]}. Narrate the revelation.",
                social=social_payload,
                requires_check=False,
            )
            return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

        if action_type == "social_probe":
            seg_probe: Dict[str, Any] | None = None
            md_na = normalized_action.get("metadata")
            if isinstance(md_na, dict):
                raw_seg = md_na.get("segmented_turn")
                if isinstance(raw_seg, dict):
                    seg_probe = raw_seg
            exhausted = npc_social_knowledge_exhausted(world, session, npc_id)
            revealed_list = runtime.get("revealed_topics") or []
            prior_reveal = bool(
                isinstance(revealed_list, list) and any(str(x).strip() for x in revealed_list)
            )
            sr = get_scene_runtime(session, scene_id) if scene_id else {}
            tcur = sr.get("topic_pressure_current") if isinstance(sr.get("topic_pressure_current"), dict) else {}
            topic_key_ctx = str(tcur.get("topic_key") or "").strip() or None
            cls = classify_social_probe_move(
                player_text=str(raw_player_text or prompt or ""),
                segmented_turn=seg_probe,
                current_target_id=npc_id,
                current_topic_key=topic_key_ctx,
            )
            pmove = str(cls.get("probe_move") or "none").strip().lower()
            if pmove != "none":
                contract = _social_probe_deterministic_contract(
                    probe_move=pmove,
                    npc_name=npc_name,
                    exhausted=exhausted,
                    prior_reveal=prior_reveal,
                )
                apply_npc_runtime_deltas(
                    session,
                    npc_id,
                    action_type,
                    contract["success"],
                    turn_counter,
                    deltas=contract.get("deltas"),
                )
                social_payload = {
                    "social_intent_class": intent_class,
                    "npc_id": npc_id,
                    "npc_name": npc_name,
                    "target_resolved": True,
                    "topic_revealed": None,
                    "skill_check": None,
                    "npc_reply_expected": contract["npc_reply_expected"],
                    "reply_kind": contract["reply_kind"],
                    "social_probe_move": pmove,
                    "probe_move_reason": str(cls.get("reason") or ""),
                    "probe_outcome": contract["probe_outcome"],
                    "probe_outcome_reason": contract["probe_outcome_reason"],
                    "social_probe_engine_contract": True,
                    **dbg,
                }
                result = SocialEngineResult(
                    kind=action_type,
                    action_id=action_id,
                    label=label,
                    prompt=prompt,
                    success=contract["success"],
                    hint=str(contract["hint"] or ""),
                    social=social_payload,
                    requires_check=False,
                )
                return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        revealed_list = runtime.get("revealed_topics") or []
        prior_thread = bool(
            isinstance(revealed_list, list) and any(str(x).strip() for x in revealed_list)
        )
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
                "topic_revealed": None,
                "skill_check": None,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=prior_thread,
            requires_check=False,
            debug_fields=dbg,
        )
        fallback_hint = (
            f"Player spoke with {npc_name}. No new information was revealed. "
            "Narrate a substantive in-turn response (answer, refusal, evasion, or inability), not dead-air stalling."
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=fallback_hint,
            social=social_payload,
            requires_check=False,
        )
        return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

    # Skill-check kinds: persuade, intimidate, deceive, barter, recruit
    skill_entry = SOCIAL_SKILL_MAP.get(action_type)
    if not skill_entry:
        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=False,
            requires_check=False,
            debug_fields=dbg,
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=f"Player attempted a social action toward {npc_name}. Narrate the outcome.",
            social=social_payload,
            requires_check=False,
        )
        return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

    skill_id, dc_mod = skill_entry
    effective_skill = _resolve_skill_for_kind(action_type, character or {})
    if not effective_skill:
        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=False,
            requires_check=False,
            debug_fields=dbg,
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=f"Player attempted {action_type} toward {npc_name}. Narrate the outcome.",
            social=social_payload,
            requires_check=False,
        )
        return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

    # Skill check authority: engine decides when to roll
    ctx = {
        "engine": "social",
        "action": normalized_action,
        "npc": npc,
        "session": session,
        "turn_counter": turn_counter,
        "scene_id": scene_id,
        "action_id": action_id,
        "character_id": (character or {}).get("id", ""),
        "seed_parts": [turn_counter, scene_id, action_id, npc_id, "social"],
    }
    decision = should_trigger_check(normalized_action, ctx)
    if not decision.get("requires_check") or decision.get("skill") is None or decision.get("difficulty") is None:
        apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
        social_payload = _social_payload_with_reply_expectation(
            {
                "social_intent_class": intent_class,
                "npc_id": npc_id,
                "npc_name": npc_name,
                "target_resolved": True,
            },
            action_type=action_type,
            prompt=prompt,
            raw_player_text=raw_player_text,
            topic_revealed=False,
            requires_check=False,
            debug_fields=dbg,
        )
        result = SocialEngineResult(
            kind=action_type,
            action_id=action_id,
            label=label,
            prompt=prompt,
            success=None,
            hint=f"Player attempted {action_type} toward {npc_name}. Narrate the outcome.",
            social=social_payload,
            requires_check=False,
        )
        return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)

    effective_skill = _resolve_skill_for_kind(action_type, character or {}) or decision["skill"]
    dc = int(decision["difficulty"])
    roll_prompt = (
        f"Roll {effective_skill.title()} (DC {dc}) to resolve this {action_type} attempt with {npc_name}."
    )
    check_request = make_check_request(
        requires_check=True,
        check_type=effective_skill,
        skill=effective_skill,
        difficulty=dc,
        reason=str(decision.get("reason") or f"{action_type}_attempt"),
        player_prompt=roll_prompt,
    )

    apply_npc_runtime_deltas(session, npc_id, action_type, None, turn_counter)
    social_payload = _social_payload_with_reply_expectation(
        {
            "social_intent_class": intent_class,
            "npc_id": npc_id,
            "npc_name": npc_name,
            "target_resolved": True,
            "skill_check": None,
            "check_request": check_request,
        },
        action_type=action_type,
        prompt=prompt,
        raw_player_text=raw_player_text,
        topic_revealed=False,
        requires_check=True,
        debug_fields=dbg,
    )

    result = SocialEngineResult(
        kind=action_type,
        action_id=action_id,
        label=label,
        prompt=prompt,
        success=None,
        clue_id=None,
        discovered_clues=[],
        state_changes={"npc_id": npc_id},
        hint=roll_prompt,
        social=social_payload,
        requires_check=True,
        check_request=check_request,
    )
    return _social_result_dict_with_incoming_metadata(result, incoming_action_meta)
