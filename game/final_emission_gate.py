from __future__ import annotations

from typing import Any, Dict, List
import re

from game.gm import question_resolution_rule_check

_BANNED_STOCK_PHRASES: tuple[str, ...] = (
    "from here, no certain answer presents itself",
    "the truth is still buried beneath rumor and rain",
    "the answer has not formed yet",
)
_SOCIAL_ADVISORY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi['’]d suggest you\b", re.IGNORECASE),
    re.compile(r"\byou should\b", re.IGNORECASE),
    re.compile(r"\byou could\b", re.IGNORECASE),
    re.compile(r"\bbest lead\b", re.IGNORECASE),
    re.compile(r"\bconsider\b", re.IGNORECASE),
)
_INTERRUPTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bshouting breaks out\b", re.IGNORECASE),
    re.compile(r"\bshout(?:ing)? breaks out\b", re.IGNORECASE),
    re.compile(r"\bcommotion\b", re.IGNORECASE),
    re.compile(r"\balarm\b", re.IGNORECASE),
    re.compile(r"\bcrowd .*?(?:erupts|breaks|surges)\b", re.IGNORECASE),
    re.compile(r"\brunner .*?(?:cuts through|arrives|rushes)\b", re.IGNORECASE),
)
_NPC_ANSWER_SHAPE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\".+?\"", re.DOTALL),
    re.compile(r"\b(?:says|replies|answers|shakes|shrugs|frowns|jaw tightens|starts to answer)\b", re.IGNORECASE),
)
_EXPLICIT_INTERRUPTION_JOIN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bstarts to answer, then\b", re.IGNORECASE),
    re.compile(r"\bbegins to answer, then\b", re.IGNORECASE),
    re.compile(r"\bbreaks off\b", re.IGNORECASE),
    re.compile(r"\bbefore .*?(?:can|could) .*?(?:answer|finish)\b", re.IGNORECASE),
    re.compile(r"\bas .*?(?:shouting|commotion|alarm) .*?(?:breaks out|erupts)\b", re.IGNORECASE),
)
_UNCERTAINTY_TAG_PREFIX = "uncertainty:"
_MOMENTUM_TAG_PREFIX = "scene_momentum:"


def _normalize_text(text: str | None) -> str:
    return " ".join(str(text or "").strip().split())


def _is_social_exchange_route(resolution: Dict[str, Any] | None) -> bool:
    if not isinstance(resolution, dict):
        return False
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    return str(social.get("social_intent_class") or "").strip().lower() == "social_exchange"


def _question_prompt_for_resolution(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return ""
    return str(
        resolution.get("prompt")
        or resolution.get("label")
        or ((resolution.get("metadata") or {}).get("player_input") if isinstance(resolution.get("metadata"), dict) else "")
        or ""
    ).strip()


def _extract_uncertainty_source(tags: List[str], text: str) -> str:
    lowered = text.lower()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        t = tag.strip().lower()
        if not t.startswith(_UNCERTAINTY_TAG_PREFIX):
            continue
        if "feasibility" in t:
            return "procedural_insufficiency"
        if any(v in t for v in ("identity", "location", "motive", "method", "quantity")):
            return "npc_ignorance"
    if "do not know" in lowered or "don't know" in lowered or "no names" in lowered:
        return "npc_ignorance"
    return "scene_ambiguity"


def _is_pressure_active(tags: List[str], session: Dict[str, Any] | None, scene_id: str) -> bool:
    low_tags = {str(t).strip().lower() for t in tags if isinstance(t, str)}
    if "topic_pressure_escalation" in low_tags:
        return True
    if any(t.startswith(_MOMENTUM_TAG_PREFIX) for t in low_tags):
        return True
    if not isinstance(session, dict) or not scene_id:
        return False
    runtime = ((session.get("scene_runtime") or {}).get(scene_id) if isinstance(session.get("scene_runtime"), dict) else {})
    if not isinstance(runtime, dict):
        return False
    current = runtime.get("topic_pressure_current") if isinstance(runtime.get("topic_pressure_current"), dict) else {}
    repeat_count = int(current.get("repeat_count", 0) or 0)
    return repeat_count >= 3


def _is_interruption_requested(tags: List[str], text: str) -> bool:
    low_tags = {str(t).strip().lower() for t in tags if isinstance(t, str)}
    if any(
        t in low_tags
        for t in (
            "topic_pressure_escalation",
            "scene_momentum:new_actor_entering",
            "scene_momentum:environmental_change",
            "scene_momentum:time_pressure",
            "scene_momentum:consequence_or_opportunity",
        )
    ):
        return True
    return any(pattern.search(text) for pattern in _INTERRUPTION_PATTERNS)


def _speaker_label(resolution: Dict[str, Any] | None) -> str:
    if not isinstance(resolution, dict):
        return "The guard"
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    name = str(social.get("npc_name") or "").strip()
    if name:
        return name
    npc_id = str(social.get("npc_id") or "").strip()
    if npc_id:
        return npc_id.replace("_", " ").replace("-", " ").title()
    return "The guard"


def _deterministic_index(seed: str, size: int) -> int:
    if size <= 1:
        return 0
    return sum(ord(ch) for ch in seed) % size


def _deterministic_social_fallback(
    *,
    resolution: Dict[str, Any] | None,
    uncertainty_source: str,
    pressure_active: bool,
    interruption_active: bool,
    seed: str,
) -> tuple[str, str]:
    speaker = _speaker_label(resolution)
    interruption = (
        f"{speaker} starts to answer, then glances past you as shouting breaks out in the crowd.",
        f"{speaker} opens their mouth, then breaks off as a shout cuts across the square.",
    )
    pressure_refusal = (
        f"{speaker} jaw tightens. \"I've told you what I know.\"",
        f"{speaker} steps back. \"No more questions.\"",
    )
    ignorance = (
        f"{speaker} shakes their head. \"I don't know.\"",
        f"{speaker} frowns. \"No names. Only rumors.\"",
    )
    evasive = (
        f"{speaker} avoids your eyes. \"I'm not naming names.\"",
        f"{speaker} keeps their voice low. \"I won't say more here.\"",
    )
    if interruption_active:
        options = interruption
        kind = "interruption"
    elif pressure_active:
        options = pressure_refusal
        kind = "pressure_refusal"
    elif uncertainty_source == "npc_ignorance":
        options = ignorance
        kind = "explicit_ignorance"
    elif uncertainty_source == "procedural_insufficiency":
        options = evasive
        kind = "refusal_evasion"
    else:
        options = ignorance
        kind = "explicit_ignorance"
    idx = _deterministic_index(seed, len(options))
    return options[idx], kind


def _has_banned_stock_phrase(text: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in _BANNED_STOCK_PHRASES)


def _contains_advisory_social_prose(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SOCIAL_ADVISORY_PATTERNS)


def _contains_mixed_answer_and_interruption_blob(text: str) -> bool:
    has_npc_answer = any(pattern.search(text) for pattern in _NPC_ANSWER_SHAPE_PATTERNS)
    has_interrupt = any(pattern.search(text) for pattern in _INTERRUPTION_PATTERNS)
    if not (has_npc_answer and has_interrupt):
        return False
    explicit_interrupt_shape = any(pattern.search(text) for pattern in _EXPLICIT_INTERRUPTION_JOIN_PATTERNS)
    return not explicit_interrupt_shape


def _validate_social_exchange_emission(
    *,
    text: str,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> List[str]:
    reasons: List[str] = []
    social = resolution.get("social") if isinstance((resolution or {}).get("social"), dict) else {}
    npc_id = str(social.get("npc_id") or "").strip()
    active_target = ""
    if isinstance(session, dict):
        interaction = session.get("interaction_context") if isinstance(session.get("interaction_context"), dict) else {}
        active_target = str(interaction.get("active_interaction_target_id") or "").strip()
    if npc_id and active_target and npc_id != active_target:
        reasons.append("turn_owner_mismatch")

    player_prompt = _question_prompt_for_resolution(resolution)
    if player_prompt:
        first_sentence_contract = question_resolution_rule_check(
            player_text=player_prompt,
            gm_reply_text=text,
            resolution=resolution,
        )
        if first_sentence_contract.get("applies") and not first_sentence_contract.get("ok"):
            reasons.extend(
                [f"first_sentence_illegal:{r}" for r in list(first_sentence_contract.get("reasons") or [])]
            )
    if _contains_advisory_social_prose(text):
        reasons.append("advisory_prose_in_social_exchange")
    if _contains_mixed_answer_and_interruption_blob(text):
        reasons.append("mixed_npc_answer_and_scene_interrupt_blob")
    if _has_banned_stock_phrase(text):
        reasons.append("banned_stock_phrase")
    return reasons


def apply_final_emission_gate(
    gm_output: Dict[str, Any],
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any]:
    """Hard legal-state gate for the final emitted text."""
    if not isinstance(gm_output, dict):
        return gm_output
    out = dict(gm_output)
    text = _normalize_text(out.get("player_facing_text"))
    tags = out.get("tags") if isinstance(out.get("tags"), list) else []
    tag_list = [str(t) for t in tags if isinstance(t, str)]
    social_route = _is_social_exchange_route(resolution)
    reasons: List[str] = []

    if _has_banned_stock_phrase(text):
        reasons.append("banned_stock_phrase")

    if social_route:
        reasons.extend(
            _validate_social_exchange_emission(
                text=text,
                resolution=resolution,
                session=session,
            )
        )

    if not reasons:
        return out

    uncertainty_source = _extract_uncertainty_source(tag_list, text)
    pressure_active = _is_pressure_active(tag_list, session, scene_id)
    interruption_active = _is_interruption_requested(tag_list, text)
    seed = (
        f"{scene_id}|{_speaker_label(resolution)}|{_question_prompt_for_resolution(resolution)}|"
        f"{uncertainty_source}|{pressure_active}|{interruption_active}|{'|'.join(sorted(set(tag_list)))}"
    )

    if social_route:
        fallback_text, fallback_kind = _deterministic_social_fallback(
            resolution=resolution,
            uncertainty_source=uncertainty_source,
            pressure_active=pressure_active,
            interruption_active=interruption_active,
            seed=seed,
        )
    else:
        fallback_text = "For a breath, the scene holds while voices shift around you."
        fallback_kind = "narrative_safe_fallback"

    out["player_facing_text"] = fallback_text
    out["tags"] = tag_list + ["final_emission_gate_replaced", f"final_emission_gate:{fallback_kind}"]
    dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
    out["debug_notes"] = (
        (dbg + " | " if dbg else "")
        + "final_emission_gate:replaced:"
        + ",".join(reasons[:8])
    )
    return out
