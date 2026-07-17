"""Response-type consumer smoke bridge for downstream integration tests (Cycle BV7B).

Owns weak downstream ``response_type_contract`` scaffolds and response-type FEM
surface checks. Delegates enforcement to ``game.final_emission_response_type``.

Compatibility re-export: ``tests.helpers.emission_smoke_assertions``.

Registry reference: ``tests/test_gate_boundary_governance.py`` (Cycle BV7B).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def response_type_contract(required: str) -> dict:
    """Minimal response-type contract scaffold for downstream smoke and integration tests."""
    return {
        "required_response_type": required,
        "action_must_preserve_agency": required == "action_outcome",
    }


def enforce_response_type_contract_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any]]:
    """Consumer-owned response-type enforcement seam (delegates to response_type owner)."""
    from game.final_emission_response_type import enforce_response_type_contract as _fn

    return _fn(*args, **kwargs)


def assert_response_type_meta(
    meta: Mapping[str, Any],
    *,
    required: Any = None,
    candidate_ok: Any = None,
    repair_used: Any = None,
    repair_kinds: Sequence[str] | None = None,
) -> None:
    """Smoke-check selected response-type FEM fields when provided."""
    if required is not None:
        assert meta.get("response_type_required") == required
    if candidate_ok is not None:
        assert meta.get("response_type_candidate_ok") is candidate_ok
    if repair_used is not None:
        assert meta.get("response_type_repair_used") is repair_used
    if repair_kinds is not None:
        assert meta.get("response_type_repair_kind") in set(repair_kinds)


def assert_response_type_contract_surfaces(
    *,
    required: str,
    debug: Mapping[str, Any] | None = None,
    trace: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
) -> None:
    """HTTP smoke: ``response_type_contract`` threaded through named debug surfaces."""
    for surface_name, contract in (
        ("debug", debug),
        ("trace", trace),
        ("resolution", resolution),
    ):
        if contract is None:
            continue
        actual = contract.get("required_response_type")
        assert actual == required, (
            f"{surface_name} response_type_contract.required_response_type: "
            f"expected {required!r}, got {actual!r}"
        )
