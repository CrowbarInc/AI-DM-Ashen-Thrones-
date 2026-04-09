"""Writer contract resolution for the emission gate: ``response_type_contract`` + last player input.

Reads ``response_policy`` / resolution metadata / debug fallbacks to learn what the model was
asked to produce. **Not** validators (:mod:`game.final_emission_validators`), repairs
(:mod:`game.final_emission_repairs`), or strict-social enforcement
(:mod:`game.social_exchange_emission`).
"""
from __future__ import annotations

from typing import Any, Dict, List

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
