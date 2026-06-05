"""Shared boundary semantic-repair integration scaffolds (Cycle AS5).

Support residue for ``tests/test_final_emission_boundary_no_semantic_repair.py`` and
related convergence checks. Predicate / layer semantics stay in owner suites
(``test_final_emission_repairs.py``, ``test_final_emission_gate.py``).
"""
from __future__ import annotations

from typing import Any, Mapping


FEM_SEMANTIC_REPAIR_FLAG_KEYS: tuple[str, ...] = (
    "narrative_authenticity_repaired",
    "narrative_authenticity_repair_applied",
    "social_response_structure_repair_applied",
    "referent_repaired",
    "referent_repair_applied",
    "acceptance_quality_repaired",
    "acceptance_quality_repair_applied",
    "sentence_micro_smoothing_applied",
)


def assert_fem_has_no_semantic_repair_success_flags(fem: Mapping[str, Any]) -> None:
    for key in FEM_SEMANTIC_REPAIR_FLAG_KEYS:
        assert fem.get(key) is not True, f"unexpected boundary semantic repair flag {key!r} in final emission meta"


def dialogue_policy_with_social_structure() -> dict[str, Any]:
    rtc = {
        "required_response_type": "dialogue",
        "allowed_response_types": ["dialogue"],
        "contract_version": 1,
    }
    srs = {
        "enabled": True,
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": True,
        "discourage_expository_monologue": True,
        "require_natural_cadence": True,
        "forbid_bulleted_or_list_like_dialogue": True,
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": 2,
        "max_dialogue_paragraphs_before_break": 2,
        "prefer_single_speaker_turn": True,
    }
    return {"response_type_contract": rtc, "social_response_structure": srs}
