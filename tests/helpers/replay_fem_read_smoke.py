"""Replay FEM read facade for downstream integration tests (Cycle BV12A).

Owns delegate-only normalized FEM reads from gate output and turn-packet debug notes.
Downstream replay acceptance, projection-adjacent, and observability smoke should
import this module instead of ``tests.helpers.replay_smoke_assertions``.

Compatibility re-export: ``tests.helpers.replay_smoke_assertions``.

Registry reference: ``tests/test_ownership_registry.py`` (Cycle BV12A).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from game.final_emission_meta_read import read_debug_notes_from_turn_payload, read_final_emission_meta_dict


def final_emission_meta_from_output(gm_output: Mapping[str, Any]) -> dict[str, Any]:
    """Read normalized FEM from a gate output dict (downstream wiring smoke)."""
    return read_final_emission_meta_dict(dict(gm_output)) or {}


def read_turn_debug_notes(payload: Mapping[str, Any]) -> str:
    """Read turn-packet debug notes (downstream HTTP/pipeline wiring smoke)."""
    return read_debug_notes_from_turn_payload(payload)


def replay_fem_read_smoke_surface() -> dict[str, object]:
    """Diagnostic registry surface for ownership governance (read-only)."""
    return {
        "facade": "tests.helpers.replay_fem_read_smoke",
        "symbols": (
            "final_emission_meta_from_output",
            "read_turn_debug_notes",
        ),
        "authority": "game.final_emission_meta_read",
    }
