"""Owner tests for response-type contract helper module.

Direct owner for ``game.final_emission_response_type``, including
``enforce_response_type_contract``. Gate integration, order pins, and opening
harness paths remain in ``tests/test_final_emission_gate.py`` and
``tests/test_final_emission_opening_fallback.py``.
"""

from __future__ import annotations

import game.final_emission_gate as feg
import game.final_emission_response_type as response_type
from game.upstream_response_repairs import UPSTREAM_PREPARED_EMISSION_KEY
from tests.helpers.emission_smoke_assertions import response_type_contract


def test_upstream_prepared_emission_field_source_prefers_attribution() -> None:
    upstream = {
        "upstream_prepared_emission_attribution": "planner.answer_fallback.v2",
        "prepared_answer_fallback_text": "Answer line.",
    }
    assert response_type._upstream_prepared_emission_field_source(upstream, "prepared_answer_fallback_text") == (
        "planner.answer_fallback.v2"
    )


def test_resolve_upstream_prepared_answer_action_repair_answer_present() -> None:
    upstream = {"prepared_answer_fallback_text": "  Prepared answer.  "}
    resolved = response_type._resolve_upstream_prepared_answer_action_repair("answer", upstream)
    assert resolved.repaired == "Prepared answer."
    assert resolved.repair_kind == "answer_upstream_prepared_repair"
    assert resolved.upstream_absent is False


def test_resolve_upstream_prepared_answer_action_repair_absent_marks_absent() -> None:
    resolved = response_type._resolve_upstream_prepared_answer_action_repair("action_outcome", {})
    assert resolved.repaired is None
    assert resolved.upstream_absent is True
    assert resolved.upstream_src_label == "absent"


def test_response_type_opening_mode_active_scene_opening_or_shipped_mode() -> None:
    assert response_type._response_type_opening_mode_active("scene_opening", None, None) is True
    gm_output = {
        "prompt_context": {
            "narration_obligations": {"is_opening_scene": True},
        },
    }
    assert response_type._response_type_opening_mode_active("dialogue", gm_output, None) is True


def test_merge_opening_upstream_prepare_attach_observability_into_response_type_debug() -> None:
    debug: dict = {}
    gm_output = {
        "metadata": {
            "emission_debug": {
                "opening_upstream_prepare_attach_build_failed": True,
                "opening_upstream_prepare_attach_failure_exc_type": "ValueError",
            },
        },
    }
    response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug(
        gm_output,
        debug,
    )
    assert debug["opening_upstream_prepare_attach_build_failed"] is True
    assert debug["opening_upstream_prepare_attach_failure_exc_type"] == "ValueError"


def test_bj39_enforce_response_type_contract_applies_upstream_answer_prepared_repair() -> None:
    text, dbg = response_type.enforce_response_type_contract(
        "Mist gathers without answering.",
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract("answer")},
            UPSTREAM_PREPARED_EMISSION_KEY: {
                "prepared_answer_fallback_text": "Yes. The east gate is open until dusk.",
                "upstream_prepared_emission_attribution": "unit_upstream_answer",
            },
        },
        resolution={"kind": "question", "prompt": "Is the east gate open?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert text == "Yes. The east gate is open until dusk."
    assert dbg.get("response_type_repair_kind") == "answer_upstream_prepared_repair"
    assert dbg.get("upstream_prepared_emission_used") is True
    assert dbg.get("upstream_prepared_emission_valid") is True


def test_bj39_enforce_response_type_contract_marks_upstream_absent_for_answer() -> None:
    text, dbg = response_type.enforce_response_type_contract(
        "Only mist between the torches.",
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract("answer")},
            UPSTREAM_PREPARED_EMISSION_KEY: {},
        },
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("response_type_upstream_prepared_absent") is True
    assert dbg.get("response_type_candidate_ok") is False
    assert text == "Only mist between the torches."


def test_bj39_gate_delegator_removed() -> None:
    assert not hasattr(feg, "_enforce_response_type_contract")
