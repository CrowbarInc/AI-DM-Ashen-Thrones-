"""Answer-completeness (AC) consumer smoke bridge for downstream integration tests (Cycle BV7B).

Owns consumer-layer AC validator and repair seams. Delegates to
``game.final_emission_validators`` / ``game.final_emission_repairs``.

Compatibility re-export: ``tests.helpers.emission_smoke_assertions``.

Registry reference: ``tests/test_gate_boundary_governance.py`` (Cycle BV7B).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def validate_answer_completeness(text: str, contract: Mapping[str, Any], *, resolution: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Consumer-owned answer-completeness validator seam (delegates to validator owner)."""
    from game.final_emission_validators import validate_answer_completeness as _fn

    return _fn(text, dict(contract), resolution=dict(resolution) if isinstance(resolution, Mapping) else resolution)


def apply_answer_completeness_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    """Consumer-owned answer-completeness layer seam (delegates to repair owner)."""
    from game.final_emission_repairs import _apply_answer_completeness_layer as _fn

    return _fn(*args, **kwargs)


def skip_answer_completeness_layer(*args: Any, **kwargs: Any) -> bool:
    from game.final_emission_repairs import _skip_answer_completeness_layer as _fn

    return _fn(*args, **kwargs)
