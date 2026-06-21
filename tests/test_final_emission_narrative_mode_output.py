"""Owner tests for narrative mode output validation helpers.

Direct owner for ``game.final_emission_narrative_mode_output``. Gate orchestration
timing and hard-replace policy remain in ``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

import game.final_emission_narrative_mode_output as narrative_mode_output
from game.observability_attribution_read import FINAL_EMISSION_META_KEY
from game.narrative_mode_contract import build_narrative_mode_contract


def test_shipped_narrative_mode_contract_reads_prompt_context_plan() -> None:
    contract = {"mode": "opening", "enabled": True}
    gm_output = {
        "prompt_context": {
            "narrative_plan": {
                "narrative_mode_contract": contract,
            },
        },
    }
    assert narrative_mode_output._shipped_narrative_mode_contract_from_gm_output(gm_output) == contract


def test_narrative_mode_output_legality_assessment_absent_contract_skips() -> None:
    result = narrative_mode_output._narrative_mode_output_legality_assessment(
        "Some text.",
        {},
        resolution_for_nmo=None,
        strict_social_details_flag=None,
    )
    assert result["trace"]["narrative_mode_output_skip_reason"] == "narrative_mode_contract_absent"
    assert result["non_strict_gate_reasons"] == []
    assert result["nmo_enforcement_fail"] is False


def test_narrative_mode_output_legality_assessment_disabled_contract() -> None:
    gm_output = {
        "prompt_context": {
            "narrative_plan": {
                "narrative_mode_contract": build_narrative_mode_contract(enabled=False),
            },
        },
    }
    result = narrative_mode_output._narrative_mode_output_legality_assessment(
        "Some text.",
        gm_output,
        resolution_for_nmo=None,
        strict_social_details_flag=None,
    )
    assert result["trace"]["narrative_mode_output_skip_reason"] == "narrative_mode_contract_disabled"


def test_merge_narrative_mode_output_trace_into_gate_fem() -> None:
    out: dict = {}
    trace = {
        "narrative_mode_output_checked": True,
        "narrative_mode_output_passed": True,
        "narrative_mode_contract_mode": "opening",
    }
    narrative_mode_output._merge_narrative_mode_output_trace_into_gate_fem(out, trace)
    fem = out[FINAL_EMISSION_META_KEY]
    assert fem["narrative_mode_output_checked"] is True
    assert fem["narrative_mode_contract_mode"] == "opening"
