from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.build_validation_evidence_packets import (
    HISTORICAL_ROOT,
    REACTIVE_ROOT,
    build_historical_packet,
    build_reactive_packet,
)
from tools.validation_evidence import EVIDENCE_CATEGORIES, build_packet, validate_packet, write_packet


def _by_id(packet: dict, example_id: str) -> dict:
    return next(row for row in packet["examples"] if row["example_id"] == example_id)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_reactive_packet_preserves_exact_interaction_and_policy_evidence() -> None:
    packet = build_reactive_packet()
    example = _by_id(
        packet,
        "reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1",
    )
    source = json.loads((REACTIVE_ROOT / "20260918T021838Z/notice_observation_adversarial_seed1701/run.json").read_text(encoding="utf-8"))
    source_turn = source["turns"][1]

    assert example["player_input"] == source_turn["selected_player_action"]
    assert example["exact_gm_output"] == source_turn["gm_response"]
    assert example["simulated_player_rationale"] == source_turn["selection_reason"]
    assert example["semantic_result"] == source_turn["semantic_result"]
    assert example["mandatory_gates"] == source_turn["mandatory_gates"]
    assert example["runtime_validity"] == source_turn["gameplay_runtime_validity"]


def test_disagreement_and_ambiguous_review_are_distinct_from_automation() -> None:
    packet = build_reactive_packet()
    miss = _by_id(packet, "reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1")
    false_positive = _by_id(
        packet,
        "reactive:20260918T022209Z:patrol_knowledge_adversarial_seed1701:turn_0",
    )
    ambiguous = _by_id(packet, "reactive:20260918T021838Z:notice_observation_reactive_seed1701:turn_0")

    assert (miss["semantic_result"], miss["human_review"]["status"]) == ("PASS", "HUMAN_REJECTED")
    assert miss["evaluator_disagreement"]["present"] is True
    assert (false_positive["semantic_result"], false_positive["human_review"]["status"]) == (
        "FAIL",
        "HUMAN_ACCEPTED",
    )
    assert false_positive["evaluator_disagreement"]["present"] is True
    assert ambiguous["human_review"]["status"] == "HUMAN_AMBIGUOUS"
    assert ambiguous["semantic_result"] == "PASS"


def test_stress_probe_is_not_labeled_representative_behavior() -> None:
    packet = build_reactive_packet()
    example = _by_id(
        packet,
        "reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1",
    )
    assert "stress_probe" in example["player_input_classification"]
    assert "representative_player_behavior" not in example["player_input_classification"]


def test_every_required_category_is_explicit_and_selection_is_repeatable() -> None:
    first = build_reactive_packet()["selected_evidence"]
    second = build_reactive_packet()["selected_evidence"]
    assert first == second
    assert set(first) == set(EVIDENCE_CATEGORIES)
    assert all(row["status"] in {"SELECTED", "NO_EXAMPLE_OBSERVED"} for row in first.values())


def test_missing_category_uses_required_no_example_statement() -> None:
    packet = build_packet(
        campaign={
            "campaign_id": "empty_contract",
            "what_was_tested": "Nothing behavioral.",
            "runtime_path": "None.",
            "gm_boundary": "None.",
            "player_input_mode": "None.",
            "run_count": 0,
            "turn_count": 0,
            "automated_conclusion": "No examples.",
        },
        claim_types=(),
        examples=(),
        missing_concepts=(),
        limitations=("No behavioral claim is made.",),
    )
    assert all(row["status"] == "NO_EXAMPLE_OBSERVED" for row in packet["selected_evidence"].values())
    assert all(
        row["statement"] == "No example observed in this campaign."
        for row in packet["selected_evidence"].values()
    )


def test_historical_results_remain_original_pass_with_later_review_beside_them() -> None:
    packet = build_historical_packet()
    truncated = _by_id(packet, "historical:20260917T221002Z:p3_logical_escalation:turn_1")
    source = json.loads((HISTORICAL_ROOT / "20260917T221002Z_p3_logical_escalation/transcript.json").read_text(encoding="utf-8"))

    assert source["turns"][1]["playability_eval"]["overall"]["passed"] is True
    assert truncated["historical_result"] == "PASS"
    assert truncated["semantic_result"] is None
    assert truncated["human_review"]["status"] == "HUMAN_REJECTED"
    assert truncated["evaluator_disagreement"]["historical_result_rewritten"] is False
    assert truncated["mandatory_gates"]["availability"] == "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2"


def test_retrospective_surface_exposes_mutters_failure_directly(tmp_path: Path) -> None:
    packet = build_historical_packet()
    write_packet(tmp_path, packet)
    summary = (tmp_path / "evidence_summary.md").read_text(encoding="utf-8")

    assert "Tavern Runner mutters," in summary
    assert "Original automated result: `PASS`" in summary
    assert "HUMAN_REJECTED" in summary
    assert "case_003_truncated_output" in summary


def test_structural_only_packet_cannot_claim_semantic_behavior() -> None:
    invalid = {
        "schema_version": "validation_evidence_packet.v1",
        "evidence_scope": "structural_only",
        "claim_types": ["structural_evidence", "semantic_behavioral_evidence"],
        "examples": [],
        "selected_evidence": {category: {} for category in EVIDENCE_CATEGORIES},
    }
    assert "structural-only packet cannot claim semantic behavioral evidence" in validate_packet(invalid)


def test_packet_generation_does_not_mutate_source_artifacts(tmp_path: Path) -> None:
    sources = (
        REACTIVE_ROOT / "20260918T021838Z/notice_observation_adversarial_seed1701/run.json",
        HISTORICAL_ROOT / "20260917T221002Z_p3_logical_escalation/transcript.json",
    )
    before = {path: _digest(path) for path in sources}
    write_packet(tmp_path / "reactive", build_reactive_packet())
    write_packet(tmp_path / "historical", build_historical_packet())
    after = {path: _digest(path) for path in sources}
    assert after == before


def test_manifest_validation_rejects_missing_exact_gm_output() -> None:
    packet = build_reactive_packet()
    del packet["examples"][0]["exact_gm_output"]
    errors = validate_packet(packet)
    assert any("missing exact_gm_output" in error for error in errors)


def test_missing_concepts_are_recorded_without_implementation_claim() -> None:
    packet = build_reactive_packet()
    concepts = {row["name"]: row["status"] for row in packet["missing_concepts_future_capabilities"]}
    assert concepts == {
        "player_to_gm_vs_character_utterance_authority": "RECORDED_NOT_IMPLEMENTED",
        "general_ambiguity_clarification_behavior": "RECORDED_NOT_IMPLEMENTED",
    }


def test_generated_packets_validate() -> None:
    assert validate_packet(build_reactive_packet()) == []
    assert validate_packet(build_historical_packet()) == []

