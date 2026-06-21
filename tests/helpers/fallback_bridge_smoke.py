"""Fallback dual-bridge facade for downstream fallback integration tests (Cycle BV12A).

Re-exports gate orchestration and FEM read helpers for fallback suites that run
full gate orchestration and assert on normalized FEM. Replay and gate responsibilities
remain in their domain facades; this module is a **combined import surface only**.

Target Phase-2 consumers (fallback testing domain): dual-bridge fallback suites
identified in BV12 discovery.

Compatibility: consumers may continue importing ``replay_smoke_assertions`` and
``gate_integration_smoke`` until Phase 2 migration.

Registry reference: ``tests/test_ownership_registry.py`` (Cycle BV12A).
"""
from __future__ import annotations

from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output

__all__ = (
    "apply_final_emission_gate_consumer",
    "final_emission_meta_from_output",
)


def fallback_bridge_smoke_surface() -> dict[str, object]:
    """Diagnostic registry surface for ownership governance (read-only)."""
    return {
        "facade": "tests.helpers.fallback_bridge_smoke",
        "symbols": __all__,
        "gate_facade": "tests.helpers.gate_orchestration_smoke",
        "replay_facade": "tests.helpers.replay_fem_read_smoke",
    }
