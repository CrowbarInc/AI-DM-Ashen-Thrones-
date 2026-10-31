"""Write PR-BU_validator_semantic_matrix_complement_after.json. No model calls."""
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
COMPOSITION = json.loads((ROOT / "PR-BU_validator_semantic_matrix_after.json").read_text(encoding="utf-8"))


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


def _accepted(label: str) -> bool:
    return label in {"accept", "accept_by_omission"}


def main() -> None:
    decisions = _decisions()
    composition = {row["case_id"]: row for row in COMPOSITION["cases"]}
    rows = []
    for case in ORIGINAL["cases"]:
        decision = decisions[case["authority_setup"]]
        got = diag._classify(case["text"], decision, diag.CORPUS, case["text"])
        after = "accept_by_omission" if got["actual"] == "no_claim" else got["actual"]
        expected = case["expected_classification"]
        discovery = case["actual_classification"]
        composed = composition[case["case_id"]]["post_repair_classification"]
        false_accept = expected == "reject" and _accepted(after)
        false_reject = expected == "accept" and after == "reject"
        codes = got["fact_reasons"] or got["reason_codes"]
        if "unauthorized_inference_complement" in codes:
            path = "qualified_inference_operator_plus_unauthorized_complement"
        elif "authorized_qualified_inference" in codes and _accepted(after):
            path = "qualified_inference_operator_plus_authorized_complement"
        elif "unauthorized_causal_relation" in codes:
            path = "causal_residual"
        elif "unsupported_narrator_lead" in codes:
            path = "ungrounded_lead"
        elif "unauthorized_certainty_upgrade" in codes:
            path = "certainty_residual"
        elif "unauthorized_actor_attribution" in codes:
            path = "actor_residual"
        elif "unauthorized_history_assertion" in codes:
            path = "history_residual"
        elif _accepted(after) and not codes:
            path = "accept_by_omission"
        else:
            path = "existing_residual_or_authorized_claim"
        rows.append(
            {
                "case_id": case["case_id"],
                "text": case["text"],
                "semantic_category": case["semantic_category"],
                "expected_classification": expected,
                "discovery_classification": discovery,
                "post_composition_classification": composed,
                "post_complement_classification": after,
                "pass": not false_accept and not false_reject,
                "false_accept": false_accept,
                "false_reject": false_reject,
                "false_accept_discovery": bool(case["false_accept"]),
                "false_reject_discovery": bool(case["false_reject"]),
                "false_accept_post_composition": bool(composition[case["case_id"]]["false_accept_after"]),
                "false_reject_post_composition": bool(composition[case["case_id"]]["false_reject_after"]),
                "relevant_authorization_path": path,
                "reason_codes": codes,
                "notes": case["notes"],
            }
        )
    counts = {
        "cases": len(rows),
        "discovery_false_accepts": sum(1 for row in rows if row["false_accept_discovery"]),
        "discovery_false_rejects": sum(1 for row in rows if row["false_reject_discovery"]),
        "post_composition_false_accepts": sum(1 for row in rows if row["false_accept_post_composition"]),
        "post_composition_false_rejects": sum(1 for row in rows if row["false_reject_post_composition"]),
        "post_complement_false_accepts": sum(1 for row in rows if row["false_accept"]),
        "post_complement_false_rejects": sum(1 for row in rows if row["false_reject"]),
        "expected_outcomes_matched": sum(1 for row in rows if row["pass"]),
        "correct_accepts": sum(
            1 for row in rows if row["expected_classification"] == "accept" and _accepted(row["post_complement_classification"])
        ),
        "correct_rejects": sum(
            1 for row in rows if row["expected_classification"] == "reject" and row["post_complement_classification"] == "reject"
        ),
    }
    payload = {
        "schema": "pr_bu_validator_semantic_matrix_complement_after_v1",
        "model_calls": 0,
        "case_count": 41,
        "counts": counts,
        "scoring": "accept_by_omission counts as an acceptance, matching the original matrix.",
        "stages": ["discovery", "post_composition", "post_complement"],
        "cases": rows,
    }
    out = ROOT / "PR-BU_validator_semantic_matrix_complement_after.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
