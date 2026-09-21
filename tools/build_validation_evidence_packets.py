#!/usr/bin/env python3
"""Build standardized packets from preserved reactive and historical playability evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validation_evidence import build_packet, write_packet  # noqa: E402

REACTIVE_ROOT = ROOT / "artifacts" / "reactive_adversarial_players"
HISTORICAL_ROOT = ROOT / "artifacts" / "simulated_playtest_observability"
DEFAULT_OUT = ROOT / "artifacts" / "validation_evidence"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _review_index() -> dict[tuple[str, str, int], dict[str, Any]]:
    raw = _load_json(REACTIVE_ROOT / "human_review.json")
    out: dict[tuple[str, str, int], dict[str, Any]] = {}
    status_by_class = {
        "A_KNOWN_EVALUATOR_DETECTED_FAILURE": "HUMAN_REJECTED",
        "B_PROBABLE_GAMEPLAY_FAILURE_EVALUATOR_MISS": "HUMAN_REJECTED",
        "C_PROBABLE_FALSE_POSITIVE": "HUMAN_ACCEPTED",
        "E_AMBIGUOUS_HUMAN_REVIEW_REQUIRED": "HUMAN_AMBIGUOUS",
    }
    for row in raw.get("classifications") or []:
        for turn_index in row.get("turn_indices") or []:
            out[(str(row["campaign_id"]), str(row["run_id"]), int(turn_index))] = {
                "status": status_by_class.get(str(row.get("classification")), "UNREVIEWED"),
                "classification": row.get("classification"),
                "rationale": row.get("summary"),
                "review_date": "2026-09-18",
                "changed_semantic_policy": False,
                "calibration_case_id": None,
            }
    return out


def _unreviewed() -> dict[str, Any]:
    return {
        "status": "UNREVIEWED",
        "classification": None,
        "rationale": "No human judgment recorded for this exact interaction.",
        "review_date": None,
        "changed_semantic_policy": False,
        "calibration_case_id": None,
    }


def _reactive_input_classes(strategy: str, turn_index: int) -> list[str]:
    if turn_index == 0:
        return ["representative_player_behavior", "runtime_discovered"]
    if strategy == "adversarial":
        return ["stress_probe", "runtime_discovered"]
    return ["boundary_case", "runtime_discovered"]


def build_reactive_packet() -> dict[str, Any]:
    campaigns = ("20260918T021838Z", "20260918T022209Z")
    review = _review_index()
    examples: list[dict[str, Any]] = []
    run_count = 0
    turn_count = 0
    for campaign_id in campaigns:
        campaign_dir = REACTIVE_ROOT / campaign_id
        for run_path in sorted(campaign_dir.glob("*/run.json")):
            run_count += 1
            run = _load_json(run_path)
            turns = run.get("turns") or []
            turn_count += len(turns)
            run_id = run_path.parent.name
            for pos, turn in enumerate(turns):
                turn_index = int(turn["turn_index"])
                next_turn = turns[pos + 1] if pos + 1 < len(turns) else None
                human = review.get((campaign_id, run_id, turn_index), _unreviewed())
                automated = turn.get("playability_eval") if isinstance(turn.get("playability_eval"), Mapping) else {}
                disagreement = human["status"] in {"HUMAN_ACCEPTED", "HUMAN_REJECTED"} and (
                    (turn.get("semantic_result") == "PASS" and human["status"] == "HUMAN_REJECTED")
                    or (turn.get("semantic_result") == "FAIL" and human["status"] == "HUMAN_ACCEPTED")
                )
                examples.append(
                    {
                        "example_id": f"reactive:{campaign_id}:{run_id}:turn_{turn_index}",
                        "scenario_run_id": run_id,
                        "campaign_id": campaign_id,
                        "turn_index": turn_index,
                        "player_input": turn.get("selected_player_action"),
                        "player_input_classification": _reactive_input_classes(
                            str(run.get("player_strategy")), turn_index
                        ),
                        "simulated_player_rationale": turn.get("selection_reason"),
                        "relevant_prior_context": turn.get("relevant_prior_context"),
                        "exact_gm_output": turn.get("gm_response"),
                        "semantic_result": turn.get("semantic_result"),
                        "mandatory_gates": turn.get("mandatory_gates"),
                        "diagnostic_result": turn.get("diagnostic_quality"),
                        "automated_evaluation": automated,
                        "runtime_validity": turn.get("gameplay_runtime_validity"),
                        "final_emission_metadata": turn.get("final_emission_meta"),
                        "continuation_decision": (
                            {
                                "continued": True,
                                "next_player_action": next_turn.get("selected_player_action"),
                                "next_selection_reason": next_turn.get("selection_reason"),
                            }
                            if next_turn
                            else {"continued": False, "termination_reason": run.get("termination_reason")}
                        ),
                        "source_artifact_path": _relative(run_path),
                        "human_review": human,
                        "evaluator_disagreement": {
                            "present": disagreement,
                            "original_semantic_result": turn.get("semantic_result"),
                            "human_status": human["status"],
                            "later_evaluator_result": None,
                            "calibration_reference": human.get("calibration_case_id"),
                            "policy_changed": False,
                        },
                        "unexpected_behavior": human["status"] == "HUMAN_AMBIGUOUS",
                    }
                )
    return build_packet(
        campaign={
            "campaign_id": "reactive_adversarial_20260918_evidence",
            "source_campaign_ids": list(campaigns),
            "what_was_tested": "Bounded reactive and adversarial player behavior across watch-command, notice-observation, and patrol-knowledge objectives.",
            "runtime_path": "In-process FastAPI TestClient through POST /api/chat with campaign reset before each run.",
            "gm_boundary": "Configured live AI-GM runtime; outputs are preserved runtime responses, not test-authored GM fixtures.",
            "player_input_mode": "Authored opening actions followed by deterministic reactive/adversarial policy choices; stress probes are labeled separately.",
            "run_count": run_count,
            "turn_count": turn_count,
            "automated_conclusion": "The source campaigns completed valid runtime turns and produced PASS/FAIL semantic results. Human review recorded known failures, one evaluator miss, one probable false positive, and one ambiguous response.",
        },
        claim_types=(
            "runtime_evidence",
            "semantic_behavioral_evidence",
            "human_realism_evidence",
            "stress_test_evidence",
            "human_reviewed_evidence",
        ),
        examples=examples,
        missing_concepts=(
            {
                "name": "player_to_gm_vs_character_utterance_authority",
                "evidence": "The notice-legibility probe can be read as player-to-GM clarification rather than character dialogue.",
                "status": "RECORDED_NOT_IMPLEMENTED",
            },
            {
                "name": "general_ambiguity_clarification_behavior",
                "evidence": "Some confusing or mixed utterances may require clarification rather than confident interpretation.",
                "status": "RECORDED_NOT_IMPLEMENTED",
            },
        ),
        limitations=(
            "These runs do not prove broad gameplay quality, long-session continuity, hidden-fact consistency, or UI usability.",
            "Player openings and probes are authored; adversarial probes are useful QA evidence, not representative-human-play evidence.",
            "The deterministic player does not make the configured AI-GM deterministic.",
            "Human review covers selected interactions, not every PASS in every validation lane.",
        ),
    )


_HISTORICAL_REVIEW: dict[tuple[str, int], dict[str, Any]] = {
    ("p1_direct_answer", 0): {
        "status": "HUMAN_REJECTED",
        "rationale": "The watch-command question was not meaningfully answered.",
        "calibration_case_id": "case_001_unanswered_direct_question",
    },
    ("p1_direct_answer", 1): {
        "status": "HUMAN_REJECTED",
        "rationale": "The reply is a broken refusal/non-answer.",
        "calibration_case_id": "case_002_broken_refusal_non_answer",
    },
    ("p2_respect_intent", 0): {
        "status": "HUMAN_REJECTED",
        "rationale": "The reply is a broken refusal/non-answer.",
        "calibration_case_id": "case_002_broken_refusal_non_answer",
    },
    ("p3_logical_escalation", 1): {
        "status": "HUMAN_REJECTED",
        "rationale": "The output is truncated and does not fulfill the notice observation.",
        "calibration_case_id": "case_003_truncated_output",
    },
    ("p4_immersion", 0): {
        "status": "HUMAN_REJECTED",
        "rationale": "The notice observation is redirected into a menu-like instruction instead of being fulfilled.",
        "calibration_case_id": "case_004_observation_not_fulfilled",
    },
}


def _historical_human_review(scenario_id: str, turn_index: int) -> dict[str, Any]:
    source = _HISTORICAL_REVIEW.get((scenario_id, turn_index))
    if source is None:
        return _unreviewed()
    return {
        "status": source["status"],
        "classification": "RETROSPECTIVE_HUMAN_REVIEW",
        "rationale": source["rationale"],
        "review_date": "2026-09-18",
        "changed_semantic_policy": False,
        "calibration_case_id": source["calibration_case_id"],
    }


def build_historical_packet() -> dict[str, Any]:
    examples: list[dict[str, Any]] = []
    run_count = 0
    turn_count = 0
    for transcript_path in sorted(HISTORICAL_ROOT.glob("20260917T221002Z_*/transcript.json")):
        run_count += 1
        transcript = _load_json(transcript_path)
        scenario_id = str(transcript["scenario_id"])
        turns = transcript.get("turns") or []
        turn_count += len(turns)
        for pos, turn in enumerate(turns):
            turn_index = int(turn["turn_index"])
            evaluation = turn.get("playability_eval") or {}
            overall = evaluation.get("overall") or {}
            human = _historical_human_review(scenario_id, turn_index)
            historical_result = "PASS" if overall.get("passed") else "FAIL"
            disagreement = historical_result == "PASS" and human["status"] == "HUMAN_REJECTED"
            classes = ["runtime_discovered"]
            if turn_index == 0:
                classes.append("representative_player_behavior")
            else:
                classes.append("boundary_case")
            if scenario_id == "p3_logical_escalation" and turn_index == 1:
                classes.append("stress_probe")
            if human["status"] == "UNREVIEWED":
                classes.append("classification_uncertain_human_review")
            next_turn = turns[pos + 1] if pos + 1 < len(turns) else None
            examples.append(
                {
                    "example_id": f"historical:20260917T221002Z:{scenario_id}:turn_{turn_index}",
                    "scenario_run_id": transcript_path.parent.name,
                    "campaign_id": "20260917T221002Z",
                    "turn_index": turn_index,
                    "player_input": turn.get("player_prompt"),
                    "player_input_classification": classes,
                    "simulated_player_rationale": "fixed_script_position; no reactive policy rationale existed",
                    "relevant_prior_context": {
                        "player": turns[pos - 1].get("player_prompt") if pos else "",
                        "gm": turns[pos - 1].get("gm_text") if pos else "",
                    },
                    "exact_gm_output": turn.get("gm_text"),
                    "historical_result": historical_result,
                    "semantic_result": None,
                    "mandatory_gates": {
                        "availability": "NOT_PRESENT_IN_HISTORICAL_EVALUATOR_SCHEMA_V2",
                        "later_calibration_case_id": human.get("calibration_case_id"),
                    },
                    "diagnostic_result": overall,
                    "automated_evaluation": evaluation,
                    "runtime_validity": evaluation.get("gameplay_validation"),
                    "final_emission_metadata": None,
                    "continuation_decision": (
                        {
                            "continued": True,
                            "next_player_action": next_turn.get("player_prompt"),
                            "next_selection_reason": "fixed_script_next_turn",
                        }
                        if next_turn
                        else {"continued": False, "termination_reason": "fixed_script_complete"}
                    ),
                    "source_artifact_path": _relative(transcript_path),
                    "human_review": human,
                    "evaluator_disagreement": {
                        "present": disagreement,
                        "original_semantic_result": None,
                        "original_overall_result": historical_result,
                        "human_status": human["status"],
                        "later_evaluator_result": "FAIL" if human.get("calibration_case_id") else None,
                        "calibration_reference": human.get("calibration_case_id"),
                        "policy_changed_after_source_run": bool(human.get("calibration_case_id")),
                        "historical_result_rewritten": False,
                    },
                    "unexpected_behavior": scenario_id == "p3_logical_escalation" and turn_index == 1,
                }
            )
    return build_packet(
        campaign={
            "campaign_id": "retrospective_playability_20260917T221002Z",
            "source_campaign_ids": ["20260917T221002Z"],
            "what_was_tested": "Four fixed playability scenarios that originally produced overall PASS results despite preserved semantic failures.",
            "runtime_path": "In-process POST /api/chat playability runner with campaign resets.",
            "gm_boundary": "Configured live AI-GM runtime preserved by the original observability campaign.",
            "player_input_mode": "Fixed scripted prompts; no reactive selection. Classification uncertainty is explicit where normality was not reviewed.",
            "run_count": run_count,
            "turn_count": turn_count,
            "automated_conclusion": "Historical evaluator schema v2 marked every preserved turn overall PASS. Later human review rejected five interactions, and four known failure shapes entered the accepted semantic calibration corpus.",
        },
        claim_types=(
            "runtime_evidence",
            "semantic_behavioral_evidence",
            "stress_test_evidence",
            "human_reviewed_evidence",
        ),
        examples=examples,
        missing_concepts=(
            {
                "name": "mandatory_noncompensatory_semantic_gates",
                "evidence": "Historical aggregate PASS compensated for failed intent axes and malformed output. This capability was added later; historical results remain unchanged here.",
                "status": "LATER_CALIBRATED_SEPARATELY",
            },
        ),
        limitations=(
            "This retrospective proves what the preserved transcripts and historical evaluator reported; it does not reproduce the run.",
            "Historical evaluator schema v2 had no semantic_result or mandatory-gate fields, which are reported as unavailable rather than reconstructed.",
            "Current calibration references are annotations beside, not replacements for, historical PASS results.",
            "The fixed prompts do not establish reactive or representative-human behavior.",
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    reactive = build_reactive_packet()
    historical = build_historical_packet()
    write_packet(args.output_dir / "reactive_adversarial", reactive)
    write_packet(args.output_dir / "retrospective_playability", historical)
    print((args.output_dir / "reactive_adversarial" / "evidence_summary.md").resolve())
    print((args.output_dir / "retrospective_playability" / "evidence_summary.md").resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
