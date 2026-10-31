"""CTIR planner seam fencing — response-type resolution + guard trace labels.

Centralizes **non-authoritative** trace metadata so phrase-heuristic and legacy
fallback lanes cannot masquerade as CTIR-backed semantic authority.

See :mod:`game.planner_input_manifest` for inventory; this module owns **runtime**
resolution policy for :func:`game.response_type_gating.derive_response_type_contract`
at narration bundle / narrative-plan seams only.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from game.response_policy_contracts import (
    coerce_valid_response_type_contract,
    peek_response_type_contract_from_resolution,
)
from game.response_type_gating import derive_response_type_contract

# --- Trace / guard label keys (inspect-only; safe for prompt_debug-adjacent lanes) ---

TRACE_KEY_RESPONSE_TYPE: Final[str] = "response_type_contract_resolution"

GUARD_LEGACY_NO_CTIR_ONLY: Final[str] = "legacy_no_ctir_only"
GUARD_CTIR_BACKED_BUNDLE_REQUIRED: Final[str] = "ctir_backed_bundle_required"
GUARD_SEMANTIC_BYPASS_BLOCKED: Final[str] = "semantic_bypass_blocked"
GUARD_FALLBACK_VISIBLE_FAILURE: Final[str] = "fallback_visible_failure"
GUARD_NON_CTIR_SEMANTIC_PATH: Final[str] = "non_ctir_semantic_path"
GUARD_PLAYER_TEXT_RTC_FALLBACK: Final[str] = "player_text_rtc_fallback"
GUARD_PHRASE_HEURISTICS_LEGACY_LANE: Final[str] = "phrase_heuristics_legacy_lane"


def merge_planner_seam_trace(response_policy: dict[str, Any], fragment: Mapping[str, Any]) -> None:
    """Shallow-merge *fragment* into ``response_policy['planner_seam_trace']`` (mutates *response_policy*)."""
    base = response_policy.get("planner_seam_trace")
    merged: dict[str, Any] = dict(base) if isinstance(base, dict) else {}
    merged.update(dict(fragment))
    response_policy["planner_seam_trace"] = merged


def resolve_response_type_contract_for_planner_seam(
    *,
    ctir_attached: bool,
    resolution_sem: Mapping[str, Any] | None,
    response_policy: Mapping[str, Any] | None,
    interaction_context: Mapping[str, Any] | None,
    user_text: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Choose ``response_type_contract`` for planner/bundle seams with explicit provenance.

    **Precedence**

    1. Valid ``response_policy["response_type_contract"]`` (pre-injected / tests).
    2. ``resolution.metadata.response_type_contract`` (peek — engine-validated).
    3. If ``ctir_attached``: ``derive_response_type_contract`` with **suppressed** phrase
       heuristics (no raw-player-text regex lane).
    4. Else (legacy no-CTIR): full ``derive_response_type_contract`` including phrase
       heuristics and *user_text*.

    Returns ``(contract_dict, trace_fragment)`` where *trace_fragment* is suitable for
    :func:`merge_planner_seam_trace` under key :data:`TRACE_KEY_RESPONSE_TYPE`.
    """
    rp = response_policy if isinstance(response_policy, dict) else {}
    pre = coerce_valid_response_type_contract(rp.get("response_type_contract"))
    if pre is not None:
        trace = {
            "source": "response_policy_prevalidated",
            GUARD_PLAYER_TEXT_RTC_FALLBACK: False,
            GUARD_PHRASE_HEURISTICS_LEGACY_LANE: False,
            "phrase_heuristics_suppressed": False,
        }
        return dict(pre), trace

    peeked = (
        peek_response_type_contract_from_resolution(resolution_sem)
        if isinstance(resolution_sem, dict)
        else None
    )
    if peeked is not None:
        trace = {
            "source": "resolution_metadata_peek",
            GUARD_PLAYER_TEXT_RTC_FALLBACK: False,
            GUARD_PHRASE_HEURISTICS_LEGACY_LANE: False,
            "phrase_heuristics_suppressed": False,
        }
        return dict(peeked), trace

    res = resolution_sem if isinstance(resolution_sem, dict) else None
    if ctir_attached:
        derived = derive_response_type_contract(
            segmented_turn=None,
            normalized_action=None,
            resolution=res,
            interaction_context=interaction_context if isinstance(interaction_context, dict) else None,
            directed_social_entry=None,
            route_choice=None,
            raw_player_text=user_text,
            suppress_phrase_heuristics=True,
        ).to_dict()
        trace = {
            "source": "resolution_only_derive_ctir_suppressed_phrases",
            GUARD_PLAYER_TEXT_RTC_FALLBACK: False,
            GUARD_PHRASE_HEURISTICS_LEGACY_LANE: False,
            "phrase_heuristics_suppressed": True,
        }
        return derived, trace

    legacy = derive_response_type_contract(
        segmented_turn=None,
        normalized_action=None,
        resolution=res,
        interaction_context=interaction_context if isinstance(interaction_context, dict) else None,
        directed_social_entry=None,
        route_choice=None,
        raw_player_text=user_text,
        suppress_phrase_heuristics=False,
    ).to_dict()
    trace = {
        "source": "legacy_non_ctir_phrase_and_resolution_derive",
        GUARD_PLAYER_TEXT_RTC_FALLBACK: True,
        GUARD_PHRASE_HEURISTICS_LEGACY_LANE: True,
        GUARD_LEGACY_NO_CTIR_ONLY: True,
        GUARD_NON_CTIR_SEMANTIC_PATH: True,
        "phrase_heuristics_suppressed": False,
    }
    return legacy, trace


def attach_response_type_trace_to_policy(response_policy: dict[str, Any], trace_fragment: Mapping[str, Any]) -> None:
    """Store RTC resolution trace under ``planner_seam_trace``."""
    merge_planner_seam_trace(response_policy, {TRACE_KEY_RESPONSE_TYPE: dict(trace_fragment)})


def response_type_seam_already_traced(response_policy: Mapping[str, Any] | None) -> bool:
    """True when :func:`compute_narrative_plan_for_bundle_from_head` (or equivalent) already recorded RTC provenance."""
    if not isinstance(response_policy, dict):
        return False
    pst = response_policy.get("planner_seam_trace")
    if not isinstance(pst, dict):
        return False
    slot = pst.get(TRACE_KEY_RESPONSE_TYPE)
    return isinstance(slot, dict) and bool(slot.get("source"))
