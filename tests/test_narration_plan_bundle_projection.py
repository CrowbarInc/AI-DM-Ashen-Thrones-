"""Public projection tests for narration plan bundle prompt surfaces."""

from __future__ import annotations

import copy

import pytest

from game.narration_plan_bundle import public_narrative_plan_projection_for_prompt

pytestmark = pytest.mark.unit


def test_public_projection_includes_answer_exposition_plan_when_present() -> None:
    full = {
        "version": 1,
        "narrative_mode": "standard",
        "answer_exposition_plan": {
            "enabled": True,
            "answer_required": True,
            "answer_intent": "direct_answer",
            "source": {"derived_from_ctir": True, "ctir_sections": [], "derivation_codes": ["x"]},
            "facts": [
                {
                    "id": "fact_1",
                    "fact": "A public fact.",
                    "source": "ctir",
                    "visibility": "public",
                    "certainty": "known",
                }
            ],
            "constraints": {
                "forbid_invention": True,
                "forbid_hidden_truth_leak": True,
                "forbid_prompt_layer_reasoning": True,
                "allowed_partial_reasons": [],
            },
            "voice": {"expected_voice": "either", "delivery_mode": "plain_answer"},
            "delivery": {
                "answer_must_come_first": True,
                "max_sentences_hint": None,
                "must_include_fact_ids": ["fact_1"],
                "optional_fact_ids": [],
                "forbidden_moves": [],
            },
        },
    }
    projected = public_narrative_plan_projection_for_prompt(full)
    assert isinstance(projected, dict)
    assert isinstance(projected.get("answer_exposition_plan"), dict)
    assert projected["answer_exposition_plan"]["facts"][0]["id"] == "fact_1"

    # Projection must deep-copy (transport-only; no mutation leaks).
    before = copy.deepcopy(projected)
    projected["answer_exposition_plan"]["facts"][0]["fact"] = "mutated"
    assert before["answer_exposition_plan"]["facts"][0]["fact"] == "A public fact."

