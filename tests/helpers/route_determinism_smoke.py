"""Response-delta (RD) consumer smoke bridge for downstream integration tests (Cycle BV7B).

Owns consumer-layer RD validator/repair seams and boundary validate-only smoke.
Delegates to ``game.final_emission_validators`` / ``game.final_emission_repairs``.

Compatibility re-export: ``tests.helpers.emission_smoke_assertions``.

Registry reference: ``tests/test_ownership_registry.py`` (Cycle BV7B).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_MISSING = object()


def apply_response_delta_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    """Consumer-owned response-delta layer seam (delegates to repair owner)."""
    from game.final_emission_repairs import _apply_response_delta_layer as _fn

    return _fn(*args, **kwargs)


def skip_response_delta_layer(*args: Any, **kwargs: Any) -> bool:
    from game.final_emission_repairs import _skip_response_delta_layer as _fn

    return _fn(*args, **kwargs)


def strict_social_answer_pressure_rd_contract_active(gm_output: Mapping[str, Any]) -> bool:
    from game.final_emission_repairs import _strict_social_answer_pressure_rd_contract_active as _fn

    return _fn(dict(gm_output))


def validate_response_delta(emitted: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    from game.final_emission_validators import validate_response_delta as _fn

    return _fn(emitted, dict(contract))


def inspect_response_delta_failure(result: Mapping[str, Any]) -> dict[str, Any]:
    from game.final_emission_validators import inspect_response_delta_failure as _fn

    return _fn(dict(result))


def assert_no_boundary_reorder_repair(meta: Mapping[str, Any], reason: str) -> None:
    """Smoke: boundary validate-only reason appears in rejection sample."""
    sample = meta.get("rejection_reasons_sample") or []
    assert reason in sample


def assert_response_delta_boundary_validate_only(
    out: str,
    raw: str,
    meta: Mapping[str, Any],
    extra: Sequence[str],
    *,
    reason: str = "response_delta_unsatisfied_at_boundary_no_reorder",
    repair_mode: Any | object = _MISSING,
) -> None:
    """Smoke: response-delta boundary failed without reorder repair."""
    assert out == raw
    assert meta["response_delta_repaired"] is False
    assert meta["response_delta_failed"] is True
    if repair_mode is not _MISSING:
        assert meta["response_delta_repair_mode"] is repair_mode
    assert list(extra) == [reason]
