"""Canonical owner for response-policy contract resolution and downstream accessors.

This module is the repo-facing semantic home for deterministic helpers that read
shipped ``response_policy`` data, resolution metadata, or debug fallbacks to
recover what contract the model owed. It is a downstream policy consumer and
read-side accessor home, not the owner of prompt-contract bundling. Prompt
assembly may surface these policies, and validators / repairs may consume them,
but prompt-facing public bundle surfaces should remain anchored in
``game.prompt_context``.

It is **not** the prompt-context bundle owner (:mod:`game.prompt_context`),
**not** the repair owner (:mod:`game.final_emission_repairs`), and **not** the
final-emission orchestration owner (:mod:`game.final_emission_gate`).
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from game.final_emission_text import _RESPONSE_TYPE_VALUES
from game.storage import get_scene_runtime


def _policy_subcontract(
    gm_output: Dict[str, Any] | None,
    *,
    key: str,
    allow_top_level_fallback: bool = False,
) -> Dict[str, Any] | None:
    """Read a shipped response-policy child contract from its canonical bundle."""
    if not isinstance(gm_output, dict):
        return None
    response_policy = gm_output.get("response_policy")
    if isinstance(response_policy, Mapping):
        hit = response_policy.get(key)
        if isinstance(hit, dict):
            return hit
    if allow_top_level_fallback:
        hit = gm_output.get(key)
        if isinstance(hit, dict):
            return hit
    return None


def _valid_response_type_contract(candidate: Any) -> Dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None
    required = str(candidate.get("required_response_type") or "").strip().lower()
    if required not in _RESPONSE_TYPE_VALUES:
        return None
    out = dict(candidate)
    out["required_response_type"] = required
    return out


def _resolve_response_type_contract(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> tuple[Dict[str, Any] | None, str | None]:
    response_policy = (
        gm_output.get("response_policy")
        if isinstance(gm_output, dict) and isinstance(gm_output.get("response_policy"), dict)
        else None
    )
    contract = _valid_response_type_contract((response_policy or {}).get("response_type_contract"))
    if contract:
        return contract, "response_policy"

    metadata = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
    contract = _valid_response_type_contract(metadata.get("response_type_contract"))
    if contract:
        return contract, "resolution.metadata"

    debug_candidates: List[Any] = []
    if isinstance(gm_output, dict):
        debug_payload = gm_output.get("debug") if isinstance(gm_output.get("debug"), dict) else {}
        debug_candidates.append(debug_payload.get("response_type_contract"))
        debug_candidates.append(gm_output.get("response_type_contract"))
    if isinstance(session, dict):
        last_action_debug = session.get("last_action_debug") if isinstance(session.get("last_action_debug"), dict) else {}
        debug_candidates.append(last_action_debug.get("response_type_contract"))

    for candidate in debug_candidates:
        contract = _valid_response_type_contract(candidate)
        if contract:
            return contract, "debug"
    return None, None


def response_type_contract_requires_dialogue(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> bool:
    """Canonical read-side helper for downstream dialogue-contract consumers.

    This module owns response-policy contract reads. Emission / fallback consumers
    may ask whether the current turn requires dialogue, but they should not
    re-home contract semantics or duplicate contract resolution logic.
    """
    contract, _ = _resolve_response_type_contract(
        gm_output,
        resolution=resolution,
        session=session,
    )
    required = str((contract or {}).get("required_response_type") or "").strip().lower()
    return required == "dialogue"


def _last_player_input(
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> str:
    metadata = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
    prompt = str(metadata.get("player_input") or "").strip()
    if prompt:
        return prompt
    prompt = str((resolution or {}).get("prompt") or "").strip()
    if prompt:
        return prompt
    lad = session.get("last_action_debug") if isinstance(session, dict) and isinstance(session.get("last_action_debug"), dict) else {}
    prompt = str(lad.get("player_input") or "").strip()
    if prompt:
        return prompt
    if not isinstance(session, dict):
        return ""
    rt = get_scene_runtime(session, scene_id)
    return str((rt or {}).get("last_player_action_text") or "").strip()


def peek_response_type_contract_from_resolution(resolution: Any) -> Dict[str, Any] | None:
    """Return a validated ``response_type_contract`` from ``resolution.metadata``.

    Prompt-facing callers should prefer ``game.prompt_context`` as the canonical
    public home for this bundle seam. This function remains here as downstream
    policy support and compatibility residue.
    """
    if not isinstance(resolution, dict):
        return None
    metadata = resolution.get("metadata")
    if not isinstance(metadata, dict):
        return None
    return _valid_response_type_contract(metadata.get("response_type_contract"))


def resolve_answer_completeness_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    """Return shipped ``response_policy.answer_completeness`` when present."""
    return _policy_subcontract(gm_output, key="answer_completeness")


def resolve_response_delta_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    """Return shipped ``response_policy.response_delta`` when present."""
    return _policy_subcontract(gm_output, key="response_delta")


def resolve_fallback_behavior_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    """Return shipped ``response_policy.fallback_behavior`` when present.

    Top-level ``gm_output["fallback_behavior"]`` remains supported as compatibility
    residue for older payload shapes.
    """
    return _policy_subcontract(
        gm_output,
        key="fallback_behavior",
        allow_top_level_fallback=True,
    )


def resolve_social_response_structure_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    """Canonical read-side accessor for ``response_policy.social_response_structure``.

    Top-level ``gm_output["social_response_structure_contract"]`` remains supported as
    compatibility residue for older payload shapes.
    """
    contract = _policy_subcontract(gm_output, key="social_response_structure")
    if isinstance(contract, dict):
        return contract
    if not isinstance(gm_output, dict):
        return None
    top = gm_output.get("social_response_structure_contract")
    return top if isinstance(top, dict) else None


def materialize_response_policy_bundle(
    gm_output: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Canonical read-side bundle materializer for downstream consumers.

    Canonical response-policy owner / read-side accessor home:
    prefer shipped ``gm_output["response_policy"]`` and only fall back to
    ``session["last_turn_response_policy"]`` as explicit compatibility residue when
    downstream consumers need the bundle materialized on retry / fallback paths.
    """
    out = dict(gm_output) if isinstance(gm_output, dict) else {}
    pol = out.get("response_policy") if isinstance(out.get("response_policy"), dict) else None
    if isinstance(pol, dict) and pol:
        return out
    if isinstance(session, dict):
        lp = session.get("last_turn_response_policy")
        if isinstance(lp, dict) and lp:
            out["response_policy"] = lp
    return out


# Compatibility residue: older internal imports still reach for the private
# validator-era names. Keep them importable while the canonical accessors live here.
def _resolve_answer_completeness_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    return resolve_answer_completeness_contract(gm_output)


def _resolve_response_delta_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    return resolve_response_delta_contract(gm_output)


def _resolve_fallback_behavior_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    return resolve_fallback_behavior_contract(gm_output)


def _resolve_social_response_structure_contract(
    gm_output: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    return resolve_social_response_structure_contract(gm_output)


def _social_response_structure_disabled(
    *,
    debug_reason: str,
    debug_inputs: Dict[str, Any],
    required_response_type: str | None,
) -> Dict[str, Any]:
    return {
        "enabled": False,
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": False,
        "discourage_expository_monologue": False,
        "require_natural_cadence": False,
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": None,
        "max_dialogue_paragraphs_before_break": None,
        "prefer_single_speaker_turn": False,
        "forbid_bulleted_or_list_like_dialogue": False,
        "required_response_type": required_response_type,
        "debug_reason": debug_reason,
        "debug_inputs": dict(debug_inputs),
    }


def build_social_response_structure_contract(
    response_type_contract: Mapping[str, Any] | None = None,
    *,
    debug_inputs: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Downstream policy helper for dialogue-only social reply shape.

    ``game.prompt_context`` is the canonical prompt-contract owner and public
    bundle home for this surface. Keep prompt-facing ownership cues there; this
    module remains the downstream policy consumer / compatibility implementation.
    Enabled only when ``response_type_contract`` (validated) requires ``dialogue``.
    """
    di: Dict[str, Any] = {}
    if isinstance(debug_inputs, Mapping):
        di = {str(k): v for k, v in debug_inputs.items()}

    rtc: Dict[str, Any] | None = None
    if isinstance(response_type_contract, dict):
        rtc = _valid_response_type_contract(response_type_contract)
    elif isinstance(response_type_contract, Mapping):
        rtc = _valid_response_type_contract(dict(response_type_contract))

    if rtc is None:
        return _social_response_structure_disabled(
            debug_reason="missing_or_invalid_response_type_contract",
            debug_inputs=di,
            required_response_type=None,
        )

    required = str(rtc.get("required_response_type") or "").strip().lower()
    if required != "dialogue":
        return _social_response_structure_disabled(
            debug_reason=f"response_type_not_dialogue:{required or 'empty'}",
            debug_inputs=di,
            required_response_type=required or None,
        )

    return {
        "enabled": True,
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": True,
        "discourage_expository_monologue": True,
        "require_natural_cadence": True,
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": 2,
        "max_dialogue_paragraphs_before_break": 2,
        "prefer_single_speaker_turn": True,
        "forbid_bulleted_or_list_like_dialogue": True,
        "required_response_type": "dialogue",
        "debug_reason": "response_type_contract_requires_dialogue",
        "debug_inputs": di,
    }


def _valid_interaction_continuity_contract(candidate: Any) -> Dict[str, Any] | None:
    from game.interaction_continuity import CONTINUITY_STRENGTH_VALUES

    if not isinstance(candidate, dict):
        return None
    strength = str(candidate.get("continuity_strength") or "").strip().lower()
    if strength not in CONTINUITY_STRENGTH_VALUES:
        return None
    if not isinstance(candidate.get("enabled"), bool):
        return None
    out = dict(candidate)
    out["continuity_strength"] = strength
    return out


def _resolve_interaction_continuity_contract(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    response_policy = (
        gm_output.get("response_policy")
        if isinstance(gm_output, dict) and isinstance(gm_output.get("response_policy"), dict)
        else None
    )
    contract = _valid_interaction_continuity_contract((response_policy or {}).get("interaction_continuity"))
    if contract:
        return contract, "response_policy"

    metadata = (
        resolution.get("metadata")
        if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict)
        else {}
    )
    contract = _valid_interaction_continuity_contract(metadata.get("interaction_continuity_contract"))
    if contract:
        return contract, "resolution.metadata"

    debug_candidates: List[Any] = []
    if isinstance(gm_output, dict):
        debug_payload = gm_output.get("debug") if isinstance(gm_output.get("debug"), dict) else {}
        debug_candidates.append(debug_payload.get("interaction_continuity_contract"))
        debug_candidates.append(gm_output.get("interaction_continuity_contract"))
    if isinstance(session, dict):
        last_action_debug = (
            session.get("last_action_debug") if isinstance(session.get("last_action_debug"), dict) else {}
        )
        debug_candidates.append(last_action_debug.get("interaction_continuity_contract"))

    for cand in debug_candidates:
        contract = _valid_interaction_continuity_contract(cand)
        if contract:
            return contract, "debug"
    return None, None


def resolve_interaction_continuity_contract(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Public wrapper for :func:`_resolve_interaction_continuity_contract` (validators / emission debug)."""
    return _resolve_interaction_continuity_contract(
        gm_output, resolution=resolution, session=session
    )


def _valid_conversational_memory_window_contract(candidate: Any) -> Dict[str, Any] | None:
    """Shape check for :func:`game.conversational_memory_window.build_conversational_memory_window_contract` outputs."""
    if not isinstance(candidate, dict):
        return None
    wv = str(candidate.get("window_version") or "").strip()
    if not wv:
        return None
    if not isinstance(candidate.get("enabled"), bool):
        return None
    out = dict(candidate)
    out["window_version"] = wv
    return out


def _resolve_conversational_memory_window_contract(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Resolve the shipped conversational memory window contract (Objective #15; inspection only)."""
    response_policy = (
        gm_output.get("response_policy")
        if isinstance(gm_output, dict) and isinstance(gm_output.get("response_policy"), dict)
        else None
    )
    contract = _valid_conversational_memory_window_contract((response_policy or {}).get("conversational_memory_window"))
    if contract:
        return contract, "response_policy"

    metadata = (
        resolution.get("metadata")
        if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict)
        else {}
    )
    contract = _valid_conversational_memory_window_contract(metadata.get("conversational_memory_window"))
    if contract:
        return contract, "resolution.metadata"

    debug_candidates: List[Any] = []
    if isinstance(gm_output, dict):
        debug_payload = gm_output.get("debug") if isinstance(gm_output.get("debug"), dict) else {}
        debug_candidates.append(debug_payload.get("conversational_memory_window"))
        debug_candidates.append(gm_output.get("conversational_memory_window"))
    if isinstance(session, dict):
        last_action_debug = (
            session.get("last_action_debug") if isinstance(session.get("last_action_debug"), dict) else {}
        )
        debug_candidates.append(last_action_debug.get("conversational_memory_window"))

    for cand in debug_candidates:
        contract = _valid_conversational_memory_window_contract(cand)
        if contract:
            return contract, "debug"
    return None, None


def resolve_conversational_memory_window_contract(
    gm_output: Dict[str, Any] | None,
    *,
    resolution: Dict[str, Any] | None,
    session: Dict[str, Any] | None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Public wrapper for :func:`_resolve_conversational_memory_window_contract`."""
    return _resolve_conversational_memory_window_contract(
        gm_output, resolution=resolution, session=session
    )
