"""Offline recorded-output replay and explicit interpretation substitution."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import pytest
from tests.helpers.live_model_guard import install_live_model_guard
from tests.test_atgb_r1_07_correction_contract import interpret
from game.conversational_orchestration import decision_from_interpretation_record, public_conversation_evidence
from tools.validation_evidence import build_packet, write_packet

out = Path(__file__).parent
rows, examples = [], []
for campaign, trial, filename in [("atgb_r1_05", "L1", "traces.json"), ("atgb_r1_05", "L2", "traces.json"), ("atgb_r1_03", "L3", "trace.json")]:
    source = ROOT / "artifacts/atgb" / campaign / trial
    before = json.loads((source / "before.json").read_text(encoding="utf-8"))
    unchanged = copy.deepcopy(before)
    setup = json.loads((source / "setup.json").read_text(encoding="utf-8"))
    trace = json.loads((source / filename).read_text(encoding="utf-8"))
    original = json.loads(next(r["return"]["text"] for r in trace if r["function"] == "request_interpretation"))
    replacement = copy.deepcopy(original)
    replacement.update(communication_mode="OTHER", interpretation_status="INTERPRETED", action_components=[], clarification_question="", correction={"subject": "REFERENT", "note": "Resolved conversational subject"})
    replacement["communication"].update(recipient="GM", purpose="CORRECTION", evidence_refs=["visible:1", "visible:2", "visible:3"])
    row = {"source": source.relative_to(ROOT).as_posix(), "player_input": setup["player_input"], "prior_context": before["log"], "evidence_candidates": public_conversation_evidence(before["scene"], before["log"]), "arms": {}}
    for arm, payload in [("recorded_output", original), ("substituted_interpretation", replacement)]:
        with pytest.MonkeyPatch.context() as monkeypatch:
            install_live_model_guard(monkeypatch)
            result, captured = interpret(monkeypatch, payload, text=setup["player_input"], **{k: before[k] for k in ("scene", "world", "session", "log")})
            decision = decision_from_interpretation_record(result["record"], player_text=setup["player_input"], **{k: before[k] for k in ("scene", "world", "session")})
        row["arms"][arm] = {"generated_request": captured, "interpretation_result": result, "decision": decision.__dict__}
        assert not decision.requires_authoritative_execution
        assert decision.context_update is None
        examples.append({"example_id": f"{campaign}_{trial}_{arm}", "scenario_run_id": f"{campaign}/{trial}/{arm}", "turn_index": 2,
            "player_input": setup["player_input"], "player_input_classification": ["synthetic_positive_control" if arm == "substituted_interpretation" else "synthetic_negative_control", "boundary_case"],
            "simulated_player_rationale": "Preserved failure input; controlled interpretation, no simulated player.", "prior_visible_context": setup.get("prior_gm", before["log"]),
            "exact_gm_output": decision.player_facing_text, "historical_result": "Recorded model output gave redundant clarification; substitution is not a new model result.",
            "semantic_result": "NOT_EVALUATED", "mandatory_gates": {"authority": {"status": "PASS"}},
            "diagnostic_result": {"host_contract": "PASS"}, "automated_evaluation": {"host_only": True}, "runtime_validity": "VALID_OFFLINE_HOST_PATH",
            "final_emission_metadata": "Decision text only; direct API final delivery tested separately in test_direct_chat_delivery_and_state_integrity.",
            "continuation_action_or_termination_reason": "Stop after offline decision", "source_artifact_path": "artifacts/atgb/atgb_r1_07/offline_replay.json",
            "human_review": {"status": "UNREVIEWED", "rationale": "Await external review; no authenticated scoring."}, "evaluator_disagreement": {"present": False}})
    assert before == unchanged
    row["input_state_unchanged"] = True
    rows.append(row)
(out / "offline_replay.json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
packet = build_packet(campaign={"campaign_id": "atgb_r1_07", "what_was_tested": "Recorded and substituted interpretations across three preserved failures; host structural contract only.",
    "runtime_path": "Production request construction -> stub wire -> adapter -> conversational decision", "gm_boundary": "No model/provider calls; explicit counterfactuals",
    "player_input_mode": "Preserved text, synthetic controls", "run_count": 6, "turn_count": 6, "automated_conclusion": "Host contract assertions passed; live selection unproven."},
    claim_types=["structural_evidence", "runtime_evidence"], examples=examples, missing_concepts=[],
    limitations=["No new live result, semantic evaluator, human review, benchmark performance or independent generalization.", "Six offline arms over three historical inputs; recorded-output arms remain redundant clarification."], evidence_scope="structural_only")
write_packet(ROOT / "artifacts/validation_evidence/atgb_r1_07", packet)
print("Six offline arms, zero live calls; packet validated.")
