"""Deterministic fallback behavior contract for graceful uncertainty handling.

This is a prompt/policy contract layer only. It does not validate, repair, retry, or
re-interpret prior outputs. The contract activates narrowly when other shipped narration
contracts indicate meaningful uncertainty pressure for the current turn.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping

_UNKNOWN_IDENTITY_RE = re.compile(
    r"\b(who|whose|what(?:'s|\s+is)?\s+(?:the\s+)?name|which\s+(?:one|person|man|woman|guard|runner))\b",
    re.IGNORECASE,
)
_UNKNOWN_LOCATION_RE = re.compile(
    r"\b(where|where(?:'s|\s+is)|which\s+(?:road|street|dock|house|room|way|door|alley|location|place)|direction)\b",
    re.IGNORECASE,
)
_UNKNOWN_MOTIVE_RE = re.compile(
    r"\b(why|motive|motives|intent|intention|intentions|reason|reasons|plan|plans|planning)\b",
    re.IGNORECASE,
)
_UNKNOWN_METHOD_RE = re.compile(
    r"\b(how|how\s+did|by\s+what\s+means|method|means|tamper|poison|sabotage)\b",
    re.IGNORECASE,
)
_UNKNOWN_QUANTITY_RE = re.compile(
    r"\b(how\s+many|how\s+much|number|count|quantity)\b",
    re.IGNORECASE,
)
_UNKNOWN_FEASIBILITY_RE = re.compile(
    r"\b(can|could|would|possible|possibly|feasible|safe|safely|will\s+it\s+work|what\s+happens\s+if)\b",
    re.IGNORECASE,
)
_SHORT_CLARIFY_RE = re.compile(
    r"^\s*(who|where|which\s+one|what\s+about\s+(?:that|him|her|them|it)|and\s+who|and\s+where)\s*\??\s*$",
    re.IGNORECASE,
)

_ALLOWED_HEDGE_FORMS: List[str] = [
    "I can't swear to it, but",
    "From what I saw,",
    "As far as rumor goes,",
    "Looks like",
    "Hard to tell, but",
]
_FORBIDDEN_HEDGE_FORMS: List[str] = [
    "I lack enough information to answer confidently.",
    "The system cannot confirm that.",
    "Canon proves it.",
    "As an AI, I don't know.",
    "There is insufficient context available.",
]
_ALLOWED_AUTHORITY_BASES: List[str] = [
    "direct_observation",
    "established_report",
    "rumor_marked_as_rumor",
    "visible_evidence",
]
_FORBIDDEN_AUTHORITY_BASES: List[str] = [
    "unsupported_named_culprit",
    "unsupported_exact_location",
    "unsupported_motive_as_fact",
    "unsupported_procedural_certainty",
    "system_or_canon_claims",
]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _list_of_dicts(value: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(value, list):
        return out
    for item in value:
        if isinstance(item, dict):
            out.append(item)
    return out


def _question_uncertainty_sources(turn_summary: Mapping[str, Any], recent_log: List[Dict[str, Any]]) -> List[str]:
    raw_player = _clean_text(turn_summary.get("raw_player_input"))
    if not raw_player and recent_log:
        raw_player = _clean_text(recent_log[-1].get("player_input"))
    if not raw_player:
        raw_player = _clean_text(turn_summary.get("resolved_prompt"))
    if not raw_player:
        return []

    sources: List[str] = []
    patterns = (
        (_UNKNOWN_IDENTITY_RE, "unknown_identity"),
        (_UNKNOWN_LOCATION_RE, "unknown_location"),
        (_UNKNOWN_MOTIVE_RE, "unknown_motive"),
        (_UNKNOWN_METHOD_RE, "unknown_method"),
        (_UNKNOWN_QUANTITY_RE, "unknown_quantity"),
        (_UNKNOWN_FEASIBILITY_RE, "unknown_feasibility"),
    )
    for pattern, label in patterns:
        if pattern.search(raw_player) and label not in sources:
            sources.append(label)
    return sources


def _has_grounded_partial_basis(
    *,
    scene: Mapping[str, Any],
    recent_log: List[Dict[str, Any]],
    mechanical_resolution: Mapping[str, Any],
    narrative_authority_contract: Mapping[str, Any],
) -> bool:
    visible_fact_strings = narrative_authority_contract.get("visible_fact_strings")
    if isinstance(visible_fact_strings, list) and any(
        isinstance(item, str) and item.strip() for item in visible_fact_strings
    ):
        return True

    if recent_log and any(
        _clean_text(row.get("gm_snippet")) for row in recent_log if isinstance(row, dict)
    ):
        return True

    if any(
        bool(mechanical_resolution.get(key))
        for key in ("clue_id", "discovered_clues", "resolved_transition", "success", "social")
    ):
        return True

    public_scene = scene.get("public") if isinstance(scene.get("public"), dict) else {}
    if _clean_text(public_scene.get("summary")):
        return True

    inner_scene = scene.get("scene") if isinstance(scene.get("scene"), dict) else {}
    if _clean_text(inner_scene.get("summary")):
        return True

    return False


def _is_procedurally_insufficient(
    mechanical_resolution: Mapping[str, Any],
    narrative_authority_contract: Mapping[str, Any],
) -> bool:
    if not narrative_authority_contract.get("forbid_unresolved_outcome_assertions"):
        return False
    if mechanical_resolution.get("requires_check"):
        return True
    if isinstance(mechanical_resolution.get("check_request"), dict):
        return True
    if narrative_authority_contract.get("authoritative_outcome_available") is False:
        resolution_kind = _clean_text(narrative_authority_contract.get("resolution_kind"))
        if resolution_kind:
            return True
    return False


def _fallback_uncertainty_signals(
    *,
    session: Any = None,
    scene: Any = None,
    recent_log: Any = None,
    turn_summary: Any = None,
    mechanical_resolution: Any = None,
    response_type_contract: Any = None,
    answer_completeness_contract: Any = None,
    narrative_authority_contract: Any = None,
    interaction_continuity_contract: Any = None,
) -> Dict[str, Any]:
    _ = session
    ac = _mapping(answer_completeness_contract)
    na = _mapping(narrative_authority_contract)
    ic = _mapping(interaction_continuity_contract)
    rtc = _mapping(response_type_contract)
    ts = _mapping(turn_summary)
    res = _mapping(mechanical_resolution)
    recent = _list_of_dicts(recent_log)

    answer_required = bool(ac.get("answer_required"))
    expected_shape = _clean_text(ac.get("expected_answer_shape")).lower()
    expected_voice = _clean_text(ac.get("expected_voice")).lower()
    allowed_partial_reasons = [
        str(item).strip().lower()
        for item in (ac.get("allowed_partial_reasons") or [])
        if isinstance(item, str) and str(item).strip()
    ]
    trace = _mapping(ac.get("trace"))
    sources = _question_uncertainty_sources(ts, recent)
    activation_reasons: List[str] = []
    uncertainty_modes: List[str] = []

    if answer_required and expected_shape == "bounded_partial":
        activation_reasons.append("answer_completeness_requires_bounded_partial")

    if answer_required and "uncertainty" in allowed_partial_reasons:
        activation_reasons.append("answer_completeness_allows_uncertainty_partial")

    if answer_required and "lack_of_knowledge" in allowed_partial_reasons:
        activation_reasons.append("answer_completeness_detects_lack_of_knowledge")
        uncertainty_modes.append("npc_ignorance" if expected_voice == "npc" else "scene_ambiguity")

    if answer_required and "gated_information" in allowed_partial_reasons:
        activation_reasons.append("answer_completeness_detects_gated_information")
        uncertainty_modes.append("scene_ambiguity")

    if answer_required and bool(na.get("forbid_hidden_fact_assertions")):
        if any(src in sources for src in ("unknown_identity", "unknown_location", "unknown_method")):
            activation_reasons.append("narrative_authority_blocks_hidden_truth_assertion")
            uncertainty_modes.append("scene_ambiguity")

    if answer_required and bool(na.get("forbid_npc_intent_assertions_without_basis")):
        if "unknown_motive" in sources:
            activation_reasons.append("narrative_authority_blocks_unfounded_intent_assertion")
            uncertainty_modes.append("npc_ignorance" if expected_voice == "npc" else "scene_ambiguity")

    if answer_required and _is_procedurally_insufficient(res, na):
        if "unknown_feasibility" not in sources:
            sources.append("unknown_feasibility")
        activation_reasons.append("narrative_authority_requires_outcome_deferral")
        uncertainty_modes.append("procedural_insufficiency")

    if (
        answer_required
        and bool(trace.get("answer_pressure_followup_detected"))
        and bool(ic.get("enabled"))
        and expected_shape == "bounded_partial"
    ):
        activation_reasons.append("followup_pressure_persists_under_uncertainty")

    if (
        answer_required
        and bool(trace.get("same_interlocutor_followup"))
        and _clean_text(ic.get("continuity_strength")) in {"soft", "strong"}
        and expected_shape == "bounded_partial"
    ):
        activation_reasons.append("same_topic_pressed_without_new_certainty")

    if not sources and activation_reasons:
        if bool(na.get("forbid_npc_intent_assertions_without_basis")):
            sources.append("unknown_motive")
        elif bool(na.get("forbid_hidden_fact_assertions")):
            sources.append("unknown_method")
        elif _is_procedurally_insufficient(res, na):
            sources.append("unknown_feasibility")

    uncertainty_active = bool(activation_reasons)

    mode: str | None = None
    deduped_modes: List[str] = []
    for item in uncertainty_modes:
        if item and item not in deduped_modes:
            deduped_modes.append(item)
    if len(deduped_modes) == 1:
        mode = deduped_modes[0]
    elif len(deduped_modes) > 1:
        mode = "mixed"
    elif uncertainty_active and _clean_text(rtc.get("required_response_type")) == "dialogue":
        mode = "npc_ignorance" if expected_voice == "npc" else "scene_ambiguity"

    return {
        "uncertainty_active": uncertainty_active,
        "uncertainty_sources": sources,
        "uncertainty_mode": mode,
        "activation_reasons": activation_reasons,
    }


def _fallback_allowed_partial_payload(
    *,
    scene: Any = None,
    recent_log: Any = None,
    mechanical_resolution: Any = None,
    answer_completeness_contract: Any = None,
    narrative_authority_contract: Any = None,
) -> bool:
    scene_map = _mapping(scene)
    recent = _list_of_dicts(recent_log)
    res = _mapping(mechanical_resolution)
    ac = _mapping(answer_completeness_contract)
    na = _mapping(narrative_authority_contract)

    if not ac.get("answer_required"):
        return False
    if _clean_text(ac.get("expected_answer_shape")).lower() == "refusal_with_reason":
        return False
    if _clean_text(ac.get("expected_answer_shape")).lower() == "bounded_partial":
        return True
    if not ac.get("require_concrete_payload"):
        return False
    if not _has_grounded_partial_basis(
        scene=scene_map,
        recent_log=recent,
        mechanical_resolution=res,
        narrative_authority_contract=na,
    ):
        return False
    return bool(
        na.get("forbid_hidden_fact_assertions")
        or na.get("forbid_npc_intent_assertions_without_basis")
        or na.get("forbid_unresolved_outcome_assertions")
    )


def _fallback_allowed_clarifying_question(
    *,
    scene: Any = None,
    recent_log: Any = None,
    turn_summary: Any = None,
    mechanical_resolution: Any = None,
    answer_completeness_contract: Any = None,
    narrative_authority_contract: Any = None,
) -> bool:
    scene_map = _mapping(scene)
    recent = _list_of_dicts(recent_log)
    ts = _mapping(turn_summary)
    res = _mapping(mechanical_resolution)
    ac = _mapping(answer_completeness_contract)
    na = _mapping(narrative_authority_contract)
    trace = _mapping(ac.get("trace"))

    if not ac.get("answer_required"):
        return False
    if _clean_text(ac.get("expected_answer_shape")).lower() == "refusal_with_reason":
        return False

    raw_player = _clean_text(ts.get("raw_player_input"))
    materially_underspecified = bool(
        trace.get("recent_reference_clarification_detected")
        or _clean_text(trace.get("clarification_prompt_shape"))
        or _clean_text(trace.get("recent_reference_kind"))
        or (raw_player and _SHORT_CLARIFY_RE.match(raw_player))
    )
    if not materially_underspecified:
        return False

    if _has_grounded_partial_basis(
        scene=scene_map,
        recent_log=recent,
        mechanical_resolution=res,
        narrative_authority_contract=na,
    ):
        return False
    return True


def _fallback_expected_behavior(
    *,
    session: Any = None,
    scene: Any = None,
    recent_log: Any = None,
    turn_summary: Any = None,
    mechanical_resolution: Any = None,
    response_type_contract: Any = None,
    answer_completeness_contract: Any = None,
    narrative_authority_contract: Any = None,
    interaction_continuity_contract: Any = None,
) -> Dict[str, Any]:
    signals = _fallback_uncertainty_signals(
        session=session,
        scene=scene,
        recent_log=recent_log,
        turn_summary=turn_summary,
        mechanical_resolution=mechanical_resolution,
        response_type_contract=response_type_contract,
        answer_completeness_contract=answer_completeness_contract,
        narrative_authority_contract=narrative_authority_contract,
        interaction_continuity_contract=interaction_continuity_contract,
    )
    partial_allowed = _fallback_allowed_partial_payload(
        scene=scene,
        recent_log=recent_log,
        mechanical_resolution=mechanical_resolution,
        answer_completeness_contract=answer_completeness_contract,
        narrative_authority_contract=narrative_authority_contract,
    )
    clarify_allowed = _fallback_allowed_clarifying_question(
        scene=scene,
        recent_log=recent_log,
        turn_summary=turn_summary,
        mechanical_resolution=mechanical_resolution,
        answer_completeness_contract=answer_completeness_contract,
        narrative_authority_contract=narrative_authority_contract,
    )
    grounded_partial = _has_grounded_partial_basis(
        scene=_mapping(scene),
        recent_log=_list_of_dicts(recent_log),
        mechanical_resolution=_mapping(mechanical_resolution),
        narrative_authority_contract=_mapping(narrative_authority_contract),
    )

    prefer_partial = bool(partial_allowed and (grounded_partial or not clarify_allowed))
    if not signals.get("uncertainty_active"):
        prefer_partial = False

    return {
        "allowed_behaviors": {
            "ask_clarifying_question": bool(signals.get("uncertainty_active") and clarify_allowed),
            "hedge_appropriately": bool(signals.get("uncertainty_active")),
            "provide_partial_information": bool(signals.get("uncertainty_active") and partial_allowed),
        },
        "prefer_partial_over_question": prefer_partial,
        "require_partial_to_state_known_edge": bool(signals.get("uncertainty_active") and partial_allowed),
        "require_partial_to_state_unknown_edge": bool(signals.get("uncertainty_active") and partial_allowed),
        "require_partial_to_offer_next_lead": bool(signals.get("uncertainty_active") and partial_allowed),
        "partial_preferred": prefer_partial,
        "clarifying_question_allowed": bool(signals.get("uncertainty_active") and clarify_allowed),
    }


def build_fallback_behavior_contract(
    *,
    session: Any = None,
    scene: Any = None,
    recent_log: Any = None,
    turn_summary: Any = None,
    mechanical_resolution: Any = None,
    response_type_contract: Any = None,
    answer_completeness_contract: Any = None,
    narrative_authority_contract: Any = None,
    interaction_continuity_contract: Any = None,
) -> Dict[str, Any]:
    """Build a deterministic contract for graceful fallback under meaningful uncertainty."""
    enabled = any(
        bool(_mapping(item))
        for item in (
            response_type_contract,
            answer_completeness_contract,
            narrative_authority_contract,
            interaction_continuity_contract,
        )
    )
    signals = _fallback_uncertainty_signals(
        session=session,
        scene=scene,
        recent_log=recent_log,
        turn_summary=turn_summary,
        mechanical_resolution=mechanical_resolution,
        response_type_contract=response_type_contract,
        answer_completeness_contract=answer_completeness_contract,
        narrative_authority_contract=narrative_authority_contract,
        interaction_continuity_contract=interaction_continuity_contract,
    )
    behavior = _fallback_expected_behavior(
        session=session,
        scene=scene,
        recent_log=recent_log,
        turn_summary=turn_summary,
        mechanical_resolution=mechanical_resolution,
        response_type_contract=response_type_contract,
        answer_completeness_contract=answer_completeness_contract,
        narrative_authority_contract=narrative_authority_contract,
        interaction_continuity_contract=interaction_continuity_contract,
    )

    return {
        "enabled": bool(enabled),
        "uncertainty_active": bool(signals.get("uncertainty_active")),
        "uncertainty_sources": list(signals.get("uncertainty_sources") or []),
        "uncertainty_mode": signals.get("uncertainty_mode"),
        "allowed_behaviors": dict(behavior.get("allowed_behaviors") or {}),
        "disallowed_behaviors": {
            "invented_certainty": True,
            "fabricated_authority": True,
            "meta_system_explanations": True,
        },
        "diegetic_only": True,
        "max_clarifying_questions": 1,
        "prefer_partial_over_question": bool(behavior.get("prefer_partial_over_question")),
        "require_partial_to_state_known_edge": bool(behavior.get("require_partial_to_state_known_edge")),
        "require_partial_to_state_unknown_edge": bool(behavior.get("require_partial_to_state_unknown_edge")),
        "require_partial_to_offer_next_lead": bool(behavior.get("require_partial_to_offer_next_lead")),
        "allowed_hedge_forms": list(_ALLOWED_HEDGE_FORMS),
        "forbidden_hedge_forms": list(_FORBIDDEN_HEDGE_FORMS),
        "allowed_authority_bases": list(_ALLOWED_AUTHORITY_BASES),
        "forbidden_authority_bases": list(_FORBIDDEN_AUTHORITY_BASES),
        "debug": {
            "activation_reasons": list(signals.get("activation_reasons") or []),
            "partial_preferred": bool(behavior.get("partial_preferred")),
            "clarifying_question_allowed": bool(behavior.get("clarifying_question_allowed")),
        },
    }
