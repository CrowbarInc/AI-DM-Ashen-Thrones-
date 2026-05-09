"""Block S — helpers for asserting strict-social gate phase order (local_rebind relocation harness).

No runtime behavior in production code; tests-only utilities for equivalence proofs.
"""
from __future__ import annotations

from game.final_emission_text import _normalize_text


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
