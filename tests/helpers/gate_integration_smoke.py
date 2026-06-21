"""Gate integration bridge for downstream consumer integration tests (Cycle BV7A / BV12A).

Thin compatibility barrel re-exporting ``tests.helpers.gate_orchestration_smoke``.
New consumers should import the domain facade directly.

Compatibility re-export: ``tests.helpers.emission_smoke_assertions``.

Registry reference: ``tests/test_ownership_registry.py`` (Cycle AS2 / BN1 / BV7A / BV12A / BV12C).
Compat barrel FI capped at 2; import guard blocks non-delegate consumers.
"""
from __future__ import annotations

from tests.helpers.gate_orchestration_smoke import (
    apply_final_emission_gate_consumer,
    gm_response_stub,
)

__all__ = (
    "apply_final_emission_gate_consumer",
    "gm_response_stub",
)
