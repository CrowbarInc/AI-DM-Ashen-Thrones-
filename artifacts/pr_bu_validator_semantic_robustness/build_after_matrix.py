"""Write PR-BU_validator_semantic_matrix_after.json. No model calls."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAG_PATH = Path(__file__).resolve().parent / "run_diagnostic.py"
spec = importlib.util.spec_from_file_location("pr_bu_diag", DIAG_PATH)
diag = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(diag)

g = diag.g
ORIGINAL = json.loads((ROOT / "PR-BU_validator_semantic_matrix.json").read_text(encoding="utf-8"))


def _decisions():
    p1 = diag._load("P1/gm_resolution_decision.json")
    p3 = diag._load("P3/gm_resolution_decision.json")
    declared = g.validate_declared_claims_against_decision(
        [
            {
                "declaration_id": "inf_1",
                "declaration_mode": "propose",
                "source_claim_id": None,
                "premise_claim_ids": ["rc_db5ec0aa65c3", "rc_b31ecb1fd1c7"],
                "semantic_identity": {},
                "provenance_requested": "gm_inference",
                "epistemic_status": "inferred",
                "modality": "possible",
                "realization_role": "MAY_STATE",
                "relation_kind": "epistemic_status",
                "text": diag.P1_DECLARATION,
            }
        ],
        decision=p1,
    )
    effective = g._decision_with_accepted_declarations(p1, declared.get("accepted_claims"))
    slotted = dict(p1)
    slotted["unresolved_qualifiers"] = ["cause", "actor", "time", "history"]
    return {
        "p1_interpret": p1,
        "p1_interpret_before_declaration_merge": p1,
        "p1_interpret_after_accepted_declaration": effective,
        "p1_interpret_with_unresolved_qualifiers": slotted,
        "p3_perceive": p3,
        "declaration_rejected": declared.get("hard_valid") is False,
    }


def _mechanism(case_id: str, before: str, after: str) -> str:
    if case_id == "C04" and after in {"accept", "accept_by_omission"}:
        return "open_debt_history_noun_without_connective"
    if before == after or (before in {"accept", "accept_by_omission"} and after in {"accept", "accept_by_omission"}):
        if case_id in {"C01", "C01b", "C02", "G01", "G02", "H03"}:
            return "inference_no_longer_terminal_causal_residual_runs"
        return "unchanged_classification"
    mapping = {
        "C01": "declaration_rejected_and_causal_residual_runs",
        "B04": "actor_pattern_includes_cracked",
        "F02": "epistemic_slot_is_clear_is_certainty",
        "F03": "negation_scopes_over_clearly",
        "F04": "inference_no_longer_terminal_certainty_residual_runs",
        "F06": "negated_establishment_is_unresolved_status",
        "D02": "shared_unresolved_status_uncertain_equals_unclear",
        "D05": "shared_unresolved_status_uncertain_equals_unclear",
        "D07": "negated_establishment_is_unresolved_status",
        "H01": "unresolved_status_does_not_exempt_ungrounded_noun",
        "C06": "possibly_from_is_a_cause_connective",
    }
    return mapping.get(case_id, "compositional_residual_after_epistemic_operation")


def main() -> None:
    decisions = _decisions()
    rows = []
    for case in ORIGINAL["cases"]:
        decision = decisions[case["authority_setup"]]
        got = diag._classify(case["text"], decision, diag.CORPUS, case["text"])
        rec = diag._recognizers(case["text"], decision, diag.CORPUS)
        after = "accept_by_omission" if got["actual"] == "no_claim" else got["actual"]
        before = case["actual_classification"]
        expected = case["expected_classification"]
        false_accept_after = expected == "reject" and after in {"accept", "accept_by_omission"}
        false_reject_after = expected == "accept" and after == "reject"
        passed = not false_accept_after and not false_reject_after
        rows.append(
            {
                "case_id": case["case_id"],
                "text": case["text"],
                "semantic_category": case["semantic_category"],
                "expected_classification": expected,
                "pre_repair_classification": before,
                "post_repair_classification": after,
                "relevant_recognizers": {
                    "qualified_inference": rec["qualified_inference"],
                    "uncertainty_frame": rec["uncertain_frame"],
                    "unknown_slot": rec["unknown_slot"],
                    "epistemic_limit": rec["epistemic_limit"],
                    "epistemic_parent": rec["epistemic_parent"],
                    "certainty_upgrade": rec["certainty_upgrade"],
                    "lead": rec["unsupported_narrator_lead"],
                    "ungrounded_definite": rec["ungrounded_definite"],
                    "cause_fill": rec["cause_fill"],
                    "causal_relation": rec["causal_relation"],
                    "post_repair_reason_codes": got["fact_reasons"] or got["reason_codes"],
                },
                "pass": passed,
                "false_accept_before": bool(case["false_accept"]),
                "false_accept_after": false_accept_after,
                "false_reject_before": bool(case["false_reject"]),
                "false_reject_after": false_reject_after,
                "repair_mechanism": _mechanism(case["case_id"], before, after),
                "notes": case["notes"],
            }
        )
    counts = {
        "cases": len(rows),
        "false_accepts_before": sum(1 for row in rows if row["false_accept_before"]),
        "false_rejects_before": sum(1 for row in rows if row["false_reject_before"]),
        "false_accepts_after": sum(1 for row in rows if row["false_accept_after"]),
        "false_rejects_after": sum(1 for row in rows if row["false_reject_after"]),
        "correct_accepts_after": sum(
            1
            for row in rows
            if row["expected_classification"] == "accept" and row["post_repair_classification"] in {"accept", "accept_by_omission"}
        ),
        "correct_rejects_after": sum(
            1 for row in rows if row["expected_classification"] == "reject" and row["post_repair_classification"] == "reject"
        ),
        "declaration_rejected": decisions["declaration_rejected"],
    }
    payload = {
        "schema": "pr_bu_validator_semantic_matrix_after_v1",
        "model_calls": 0,
        "case_count": 41,
        "counts": counts,
        "scoring": "accept_by_omission counts as an acceptance, matching the original matrix.",
        "open_debt": ["C04"],
        "cases": rows,
    }
    out = ROOT / "PR-BU_validator_semantic_matrix_after.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
