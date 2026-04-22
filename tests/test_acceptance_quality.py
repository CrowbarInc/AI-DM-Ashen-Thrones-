"""Unit coverage for :mod:`game.acceptance_quality` (Objective N4 — Acceptance Quality floor).

Gate orchestration and FEM merge are tested in ``tests/test_final_emission_gate.py``; here we keep
pure contract / validator edges (e.g. unresolved trailer pattern version observability).
"""

from __future__ import annotations

import pytest

from game.acceptance_quality import (
    ACCEPTANCE_QUALITY_VERSION,
    build_acceptance_quality_contract,
    validate_acceptance_quality,
)

pytestmark = pytest.mark.unit


def test_trailer_patterns_unknown_version_records_unresolved_not_v1_table() -> None:
    contract = build_acceptance_quality_contract(
        overrides={"enabled": True, "trailer_phrase_patterns_version": 999},
    )
    assert contract.get("trailer_phrase_patterns_version") == 999
    text = "Nothing will ever be the same."
    v = validate_acceptance_quality(text, contract)
    ev = v.get("evidence") or {}
    assert ev.get("trailer_phrase_patterns_version_unresolved") == 999
    assert "trailer_phrase_patterns_version" not in ev


def test_build_contract_accepts_shipped_trailer_version_without_coercion() -> None:
    c = build_acceptance_quality_contract(overrides={"trailer_phrase_patterns_version": 42})
    assert c["trailer_phrase_patterns_version"] == 42
    assert c["version"] == ACCEPTANCE_QUALITY_VERSION
