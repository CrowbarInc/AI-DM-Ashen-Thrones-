"""Replay and FEM read bridge for downstream integration tests (Cycle BV7A / BV12A).

Thin compatibility barrel re-exporting ``tests.helpers.replay_fem_read_smoke``.
New consumers should import the domain facade directly.

Golden-replay classifier bucket projection remains in ``golden_replay_projection``.
Route/phrase smoke helpers remain in ``emission_smoke_assertions``.

Registry reference: ``tests/test_gate_boundary_governance.py`` (Cycle AL4 / BV7A / BV12A / BV12C).
Compat barrel FI capped at 2; import guard blocks non-delegate consumers.
"""
from __future__ import annotations

from tests.helpers.replay_fem_read_smoke import (
    final_emission_meta_from_output,
    read_turn_debug_notes,
)

__all__ = (
    "final_emission_meta_from_output",
    "read_turn_debug_notes",
)
