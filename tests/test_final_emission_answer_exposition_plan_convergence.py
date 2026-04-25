"""Final emission Answer/Exposition convergence enforcement (Objective: anti-fragility branch).

This suite focuses on gate-visible failures and FEM traceability rather than prompt behavior.
"""

from __future__ import annotations

import pytest

from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from game.final_emission_repairs import _apply_answer_exposition_plan_layer

pytestmark = pytest.mark.unit


def _aep_plan(
    *,
    answer_required: bool = True,
    answer_must_come_first: bool = True,
    facts: list[dict] | None = None,
    must_include_fact_ids: list[str] | None = None,
) -> dict:
    if facts is None:
        facts = [
            {
                "id": "ctir_noncombat_fact_1",
                "fact": "The captain is Jonas Hale.",
                "source": "ctir",
                "visibility": "public",
                "certainty": "known",
            }
        ]
    if must_include_fact_ids is None:
        must_include_fact_ids = ["ctir_noncombat_fact_1"] if answer_required else []
    return {
        "enabled": True,
        "answer_required": bool(answer_required),
        "answer_intent": "direct_answer",
        "facts": facts,
        "constraints": {
            "forbid_invention": True,
            "forbid_hidden_truth_leak": True,
            "forbid_prompt_layer_reasoning": True,
            "allowed_partial_reasons": [],
        },
        "voice": {"expected_voice": "either", "delivery_mode": "plain_answer"},
        "delivery": {
            "answer_must_come_first": bool(answer_must_come_first),
            "max_sentences_hint": None,
            "must_include_fact_ids": list(must_include_fact_ids),
            "optional_fact_ids": [],
            "forbidden_moves": [],
        },
        "source": {"derived_from_ctir": True, "ctir_sections": [], "derivation_codes": ["test"]},
        "debug": {"derivation_codes": ["test"]},
    }


def test_valid_direct_answer_passes() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The captain is Jonas Hale.",
            "tags": [],
            "response_policy": {
                "answer_completeness": {
                    "enabled": True,
                    "answer_required": True,
                    "answer_must_come_first": True,
                    "answer_exposition_plan": _aep_plan(),
                }
            },
        },
        resolution={"kind": "narrate", "prompt": "Who is the captain?"},
        session=None,
        scene_id="s1",
        world={},
    )
    fem = read_final_emission_meta_dict(out)
    assert fem.get("answer_exposition_plan_checked") is True
    assert fem.get("answer_exposition_plan_present") is True
    assert fem.get("answer_exposition_plan_valid") is True
    assert fem.get("answer_exposition_plan_passed") is True
    assert fem.get("answer_exposition_plan_failure_reasons") == []


def test_valid_lore_exposition_passes_when_grounded() -> None:
    facts = [
        {
            "id": "ctir_noncombat_fact_1",
            "fact": "Ashen Thrones was founded after the Lantern War.",
            "source": "ctir",
            "visibility": "public",
            "certainty": "known",
        }
    ]
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Ashen Thrones was founded after the Lantern War, and the old charters still bind its wards.",
            "tags": [],
            "response_policy": {
                "answer_completeness": {
                    "enabled": True,
                    "answer_required": True,
                    "answer_must_come_first": True,
                    "answer_exposition_plan": _aep_plan(facts=facts, must_include_fact_ids=["ctir_noncombat_fact_1"]),
                }
            },
        },
        resolution={"kind": "narrate", "prompt": "Tell me the lore."},
        session=None,
        scene_id="s1",
        world={},
    )
    fem = read_final_emission_meta_dict(out)
    assert fem.get("answer_exposition_plan_passed") is True


def test_missing_plan_fails_when_answer_required() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The captain is Jonas Hale.",
            "tags": [],
            "response_policy": {"answer_completeness": {"enabled": True, "answer_required": True}},
        },
        resolution={"kind": "narrate", "prompt": "Who is the captain?"},
        session=None,
        scene_id="s1",
        world={},
    )
    fem = read_final_emission_meta_dict(out)
    assert fem.get("answer_exposition_plan_checked") is True
    assert fem.get("answer_exposition_plan_present") is False
    assert fem.get("answer_exposition_plan_valid") is False
    assert fem.get("answer_exposition_plan_passed") is False
    assert "missing_answer_exposition_plan" in (fem.get("answer_exposition_plan_failure_reasons") or [])


def test_malformed_plan_fails() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The captain is Jonas Hale.",
            "tags": [],
            "response_policy": {
                "answer_completeness": {
                    "enabled": True,
                    "answer_required": True,
                    "answer_exposition_plan": {"enabled": True},  # malformed
                }
            },
        },
        resolution={"kind": "narrate", "prompt": "Who is the captain?"},
        session=None,
        scene_id="s1",
        world={},
    )
    fem = read_final_emission_meta_dict(out)
    assert fem.get("answer_exposition_plan_present") is True
    assert fem.get("answer_exposition_plan_valid") is False
    assert fem.get("answer_exposition_plan_passed") is False
    assert any(str(r).startswith("malformed_plan:") for r in (fem.get("answer_exposition_plan_failure_reasons") or []))


def test_unsupported_lore_invention_fails() -> None:
    gm = {
        "response_policy": {
            "answer_completeness": {
                "enabled": True,
                "answer_required": True,
                "answer_must_come_first": True,
                "answer_exposition_plan": _aep_plan(),
            }
        }
    }
    text = "The captain is Jonas Hale, and he secretly commands a dragon beneath the city."
    _out_text, meta, _ = _apply_answer_exposition_plan_layer(
        text,
        gm_output=gm,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta={"answer_completeness_failed": False},
    )
    assert meta.get("answer_exposition_plan_passed") is False
    assert "unsupported_lore_or_exposition_claims" in (meta.get("answer_exposition_plan_failure_reasons") or [])


def test_bounded_unknown_converted_to_certainty_fails() -> None:
    facts = [
        {
            "id": "ctir_noncombat_fact_1",
            "fact": "The captain might be Jonas Hale.",
            "source": "ctir",
            "visibility": "public",
            "certainty": "bounded",
        }
    ]
    gm = {
        "response_policy": {
            "answer_completeness": {
                "enabled": True,
                "answer_required": True,
                "answer_must_come_first": True,
                "answer_exposition_plan": _aep_plan(facts=facts, must_include_fact_ids=["ctir_noncombat_fact_1"]),
            }
        }
    }
    text = "The captain is Jonas Hale."
    _out_text, meta, _ = _apply_answer_exposition_plan_layer(
        text,
        gm_output=gm,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta={"answer_completeness_failed": False},
    )
    assert meta.get("answer_exposition_plan_passed") is False
    assert any(
        "bounded_unknown_upgraded_to_certainty" in str(r)
        for r in (meta.get("answer_exposition_plan_failure_reasons") or [])
    )


def test_safe_reorder_repair_does_not_invent_and_records_mode() -> None:
    # Isolated layer test: repair is allowed to reorder existing sentences only (no invention).
    gm = {
        "response_policy": {
            "answer_completeness": {
                "enabled": True,
                "answer_required": True,
                "answer_must_come_first": True,
                "answer_exposition_plan": _aep_plan(),
            }
        }
    }
    text = "For a moment, the rain hisses on the cobbles. The captain is Jonas Hale."
    out_text, meta, _ = _apply_answer_exposition_plan_layer(
        text,
        gm_output=gm,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta={"answer_completeness_failed": False},
    )
    assert meta.get("answer_exposition_plan_passed") is True
    assert "safe_sentence_reorder_answer_first" in (meta.get("answer_exposition_plan_repair_modes") or [])
    assert out_text.startswith("The captain is Jonas Hale.")


def test_metadata_identifies_failure_source() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Hard to say. People whisper.",
            "tags": [],
            "response_policy": {
                "answer_completeness": {
                    "enabled": True,
                    "answer_required": True,
                    "answer_must_come_first": True,
                    "answer_exposition_plan": _aep_plan(),
                }
            },
        },
        resolution={"kind": "narrate", "prompt": "Who is the captain?"},
        session=None,
        scene_id="s1",
        world={},
    )
    fem = read_final_emission_meta_dict(out)
    assert fem.get("answer_exposition_plan_checked") is True
    assert fem.get("answer_exposition_plan_passed") is False
    assert fem.get("answer_exposition_plan_failure_reasons")

