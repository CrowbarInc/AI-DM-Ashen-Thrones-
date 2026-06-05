"""Downstream consumer facade for ``game.final_emission_repairs`` layer seams (Cycle AS3).

Repairs legality ownership: ``tests/test_final_emission_repairs.py``.
Non-owner suites must import repair-layer functions through this module, not
``game.final_emission_repairs`` directly.

For gate orchestration integration, prefer ``tests/helpers/emission_smoke_assertions.py``
(``apply_final_emission_gate_consumer``, AC/RD layer seams from AS2).
"""
from __future__ import annotations

from typing import Any


def apply_narrative_authenticity_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    from game.final_emission_repairs import _apply_narrative_authenticity_layer as _fn

    return _fn(*args, **kwargs)


def apply_referent_clarity_emission_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    from game.final_emission_repairs import _apply_referent_clarity_emission_layer as _fn

    return _fn(*args, **kwargs)


def apply_answer_exposition_plan_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    from game.final_emission_repairs import _apply_answer_exposition_plan_layer as _fn

    return _fn(*args, **kwargs)


def repair_fallback_behavior(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    from game.final_emission_repairs import repair_fallback_behavior as _fn

    return _fn(*args, **kwargs)


def apply_response_delta_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    from game.final_emission_repairs import _apply_response_delta_layer as _fn

    return _fn(*args, **kwargs)


def apply_social_response_structure_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    from game.final_emission_repairs import _apply_social_response_structure_layer as _fn

    return _fn(*args, **kwargs)
