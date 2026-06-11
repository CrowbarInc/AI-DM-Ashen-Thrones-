"""Contract tests for ``tests/helpers/emission_smoke_assertions.py`` (Cycle BE Block 1).

This module owns **helper/facade contract tests only** — phrase-ban predicates,
repair-evidence readers, and other downstream smoke helpers defined in the
emission smoke facade.

HTTP/API pipeline smoke that *uses* these helpers lives in
``tests/test_turn_pipeline_shared.py``. Legality matrices remain in owner suites
(``tests/test_output_sanitizer.py``, ``tests/test_social_exchange_emission.py``,
``tests/test_final_emission_visibility.py``).
"""
from __future__ import annotations

import pytest

from tests.helpers.emission_smoke_assertions import (
    assert_emission_repair_evidence,
    assert_global_visibility_stock_absent,
    assert_no_advisory_prose,
    assert_procedural_adjudication_smoke,
)

pytestmark = pytest.mark.unit


def test_emission_smoke_helpers_reject_global_visibility_stock():
    with pytest.raises(AssertionError):
        assert_global_visibility_stock_absent(
            "For a breath, the scene holds while voices shift around you."
        )


def test_emission_smoke_helpers_reject_advisory_prose():
    with pytest.raises(AssertionError):
        assert_no_advisory_prose("I'd suggest you ask the captain.")


def test_emission_smoke_helpers_reject_procedural_adjudication_leak():
    with pytest.raises(AssertionError):
        assert_procedural_adjudication_smoke(
            "State exactly what you do; the scene offers no clear answer yet."
        )


def test_emission_smoke_helpers_accept_repair_evidence_from_tags_or_debug():
    assert_emission_repair_evidence(
        {"gm_output": {"tags": ["final_emission_gate_replaced"]}},
    )
    assert_emission_repair_evidence(
        {"debug_notes": "retry_fallback:unresolved_question"},
        debug_notes_reader=lambda payload: str(payload.get("debug_notes") or ""),
    )
