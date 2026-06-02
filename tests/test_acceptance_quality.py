"""Unit coverage for :mod:`game.acceptance_quality` (Objective N4 — Acceptance Quality floor).

Gate orchestration, FEM merge, and route-decision coverage live in ``tests/test_final_emission_gate.py``.
This suite owns contract resolution, validation/repair semantics, emission-trace shape, and
reason-code / evidence behavior at the canonical seam.
"""

from __future__ import annotations

import pytest

from game.acceptance_quality import (
    ACCEPTANCE_QUALITY_PLOT_TRAILER_TERMINAL,
    ACCEPTANCE_QUALITY_VERSION,
    build_acceptance_quality_contract,
    build_acceptance_quality_emission_trace,
    validate_acceptance_quality,
    validate_and_repair_acceptance_quality,
)
from game.final_emission_text import _normalize_text

pytestmark = pytest.mark.unit

_TRAILER_LINE = "Nothing will ever be the same."
_GROUNDED_LEAD = (
    "You still hold the sergeant's gaze while torchlight picks out wet cobbles on the east lane. "
)
_REPAIRABLE_TWO_SENTENCE = f"{_GROUNDED_LEAD}{_TRAILER_LINE}"


def test_build_contract_defaults_enabled_true() -> None:
    c = build_acceptance_quality_contract()
    assert c["enabled"] is True
    assert c["version"] == ACCEPTANCE_QUALITY_VERSION


def test_build_contract_accepts_shipped_trailer_version_without_coercion() -> None:
    c = build_acceptance_quality_contract(overrides={"trailer_phrase_patterns_version": 42})
    assert c["trailer_phrase_patterns_version"] == 42
    assert c["version"] == ACCEPTANCE_QUALITY_VERSION


def test_disabled_contract_skips_trailer_enforcement() -> None:
    contract = build_acceptance_quality_contract(overrides={"enabled": False})
    v = validate_acceptance_quality(_TRAILER_LINE, contract)
    assert v["passed"] is True
    assert (v.get("evidence") or {}).get("skipped") is True


def test_trailer_patterns_unknown_version_records_unresolved_not_v1_table() -> None:
    contract = build_acceptance_quality_contract(
        overrides={"enabled": True, "trailer_phrase_patterns_version": 999},
    )
    assert contract.get("trailer_phrase_patterns_version") == 999
    v = validate_acceptance_quality(_TRAILER_LINE, contract)
    ev = v.get("evidence") or {}
    assert ev.get("trailer_phrase_patterns_version_unresolved") == 999
    assert "trailer_phrase_patterns_version" not in ev


def test_unknown_trailer_version_leaves_trailer_in_repairable_text() -> None:
    contract = build_acceptance_quality_contract(
        overrides={"enabled": True, "trailer_phrase_patterns_version": 999},
    )
    bundle = validate_and_repair_acceptance_quality(_REPAIRABLE_TWO_SENTENCE, contract)
    assert bundle["validation"]["passed"] is True
    assert "nothing will ever be the same" in str(bundle.get("text") or "").lower()


def test_subtractive_repair_drops_trailer_terminal() -> None:
    contract = build_acceptance_quality_contract(overrides={"enabled": True})
    bundle = validate_and_repair_acceptance_quality(_REPAIRABLE_TWO_SENTENCE, contract)
    assert bundle["validation"]["passed"] is True
    assert bundle["repair"]["repair_applied"] is True
    text = str(bundle.get("text") or "").lower()
    assert "nothing will ever be the same" not in text
    assert "sergeant" in text


def test_trailer_only_candidate_fails_after_repair_budget() -> None:
    contract = build_acceptance_quality_contract(overrides={"enabled": True})
    bundle = validate_and_repair_acceptance_quality(_TRAILER_LINE, contract)
    assert bundle["validation"]["passed"] is False
    assert ACCEPTANCE_QUALITY_PLOT_TRAILER_TERMINAL in list(
        bundle["validation"].get("reason_codes") or []
    )


def test_validate_and_repair_emission_trace_has_stable_keys() -> None:
    contract = build_acceptance_quality_contract(overrides={"enabled": True})
    bundle = validate_and_repair_acceptance_quality(_REPAIRABLE_TWO_SENTENCE, contract)
    trace = bundle.get("acceptance_quality_emission_trace")
    assert isinstance(trace, dict)
    for k in (
        "acceptance_quality_version",
        "acceptance_quality_checked",
        "acceptance_quality_passed",
        "acceptance_quality_reason_codes",
        "acceptance_quality_repair_applied",
        "acceptance_quality_evidence",
    ):
        assert k in trace
    assert isinstance(trace.get("acceptance_quality_reason_codes"), list)
    assert isinstance(trace.get("acceptance_quality_evidence"), dict)
    assert trace.get("acceptance_quality_version") == ACCEPTANCE_QUALITY_VERSION
    assert trace.get("acceptance_quality_passed") is True
    assert trace.get("acceptance_quality_repair_applied") is True


def test_build_emission_trace_aligns_validation_and_repair_meta() -> None:
    contract = build_acceptance_quality_contract(overrides={"enabled": True})
    validation = validate_acceptance_quality(_TRAILER_LINE, contract)
    repair = {"repair_applied": False, "repair_modes": []}
    trace = build_acceptance_quality_emission_trace(contract, validation, repair)
    assert trace["acceptance_quality_checked"] is True
    assert trace["acceptance_quality_passed"] is False
    assert isinstance(trace["acceptance_quality_reason_codes"], list)


def test_repair_does_not_invent_grounding_on_thin_text() -> None:
    contract = build_acceptance_quality_contract(overrides={"enabled": True})
    bundle = validate_and_repair_acceptance_quality("Yes.", contract)
    text = _normalize_text(str(bundle.get("text") or ""))
    assert "sergeant" not in text.lower()
    assert "torchlight" not in text.lower()
    assert bundle["validation"]["passed"] is False


def test_emission_trace_shape_stable_for_enabled_contract() -> None:
    contract = build_acceptance_quality_contract(overrides={"enabled": True})
    for sample in (_REPAIRABLE_TWO_SENTENCE, _TRAILER_LINE):
        bundle = validate_and_repair_acceptance_quality(sample, contract)
        trace = bundle.get("acceptance_quality_emission_trace")
        assert isinstance(trace, dict)
        assert isinstance(trace.get("acceptance_quality_reason_codes"), list)
        assert isinstance(trace.get("acceptance_quality_evidence"), dict)
