"""Writer contract resolution for the emission gate: ``response_type_contract`` + last player input.

Reads ``response_policy`` / resolution metadata / debug fallbacks to learn what the model was
asked to produce. **Not** validators (:mod:`game.final_emission_validators`), repairs
(:mod:`game.final_emission_repairs`), or strict-social enforcement
(:mod:`game.social_exchange_emission`).
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from game.final_emission_text import _RESPONSE_TYPE_VALUES
from game.storage import get_scene_runtime


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
    """Return a validated ``response_type_contract`` from ``resolution.metadata`` when present."""
    if not isinstance(resolution, dict):
        return None
    metadata = resolution.get("metadata")
    if not isinstance(metadata, dict):
        return None
    return _valid_response_type_contract(metadata.get("response_type_contract"))


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
    """Inspectable dialogue-only policy for social reply shape (prompt surfacing; gate/repairs elsewhere).

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
