"""Block S/T/U — helpers for strict-social gate phase order and text equivalence (Cycle AS6).

No runtime behavior in production code; tests-only utilities for equivalence proofs.
"""
from __future__ import annotations

from game.final_emission_text import _normalize_text

# Strict-social trunk milestone ids (align with ``apply_final_emission_gate`` ordering).
PHASE_BUILD_SOCIAL = "build_final_strict_social_response"
PHASE_RESPONSE_TYPE = "_enforce_response_type_contract"
PHASE_NARRATIVE_AUTHENTICITY = "_apply_narrative_authenticity_layer"
PHASE_TONE_ESCALATION = "_apply_tone_escalation_layer"
PHASE_NARRATIVE_AUTHORITY = "_apply_narrative_authority_layer"
PHASE_SPEAKER = "enforce_emitted_speaker_with_contract"
PHASE_ANTI_RAILROADING = "_apply_anti_railroading_layer"
PHASE_SCENE_STATE_ANCHOR = "_apply_scene_state_anchor_layer"

CHAIN_SOCIAL_TO_POST_SPEAKER: tuple[str, ...] = (
    PHASE_BUILD_SOCIAL,
    PHASE_RESPONSE_TYPE,
    PHASE_NARRATIVE_AUTHENTICITY,
    PHASE_TONE_ESCALATION,
    PHASE_NARRATIVE_AUTHORITY,
    PHASE_SPEAKER,
    PHASE_ANTI_RAILROADING,
    PHASE_SCENE_STATE_ANCHOR,
)


def assert_phase_subsequence(order_events: list[str], required_chain: tuple[str, ...]) -> None:
    """Every phase in *required_chain* occurs in *order_events* in strictly increasing index order."""
    pos = 0
    for phase in required_chain:
        try:
            idx = order_events.index(phase, pos)
        except ValueError as err:
            raise AssertionError(
                f"missing phase {phase!r} after index {pos}; log={order_events!r}"
            ) from err
        pos = idx + 1


def normalized_player_text_equal(a: str, b: str) -> bool:
    """Compare normalized player-facing strings (future A/B harness for relocation vs Gate baseline)."""
    return _normalize_text(a) == _normalize_text(b)
