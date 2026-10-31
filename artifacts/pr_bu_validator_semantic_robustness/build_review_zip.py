"""Refresh handoff/CURRENT_REVIEW.zip for PR-BU. No model calls."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"
MANIFEST_PATH = ROOT / "handoff" / "REVIEW_MANIFEST.json"
EVIDENCE = ROOT / "artifacts" / "pr_bt_selective_epistemic_restoration_final_micro_live" / "evidence"

ROOT_FILES = [
    "handoff/CURRENT_REVIEW.md",
    "PR-BU_qualified_inference_complement_authorization.md",
    "PR-BU_qualified_inference_control_flow_after.md",
    "PR-BU_narration_claim_composition_repair.md",
    "PR-BU_validator_semantic_robustness_discovery.md",
    "PR-BU_validator_semantic_matrix.json",
    "PR-BU_validator_semantic_matrix_after.json",
    "PR-BU_validator_semantic_matrix_complement_after.json",
    "PR-BU_narration_validator_control_flow.md",
    "PR-BU_narration_validator_control_flow_after.md",
    "artifacts/pr_bu_validator_semantic_robustness/regression_evidence.txt",
    "artifacts/pr_bu_validator_semantic_robustness/build_complement_matrix.py",
    "artifacts/pr_bu_validator_semantic_robustness/build_after_matrix.py",
    "game/gm_resolution_decision.py",
    "tests/test_pr_bu_narration_claim_composition.py",
    "tests/test_pr_br_structured_chat_path.py",
    "tests/test_pr_br_continuation18_immutable_boundary.py",
]

EVIDENCE_FILES = [
    "P1/resolution_contract.json",
    "P1/gm_resolution_decision.json",
    "P1/decision_facing_answer_recipe.json",
    "P1/validation.json",
    "P1/digest.json",
    "P1/state_after.json",
    "P1/raw_generation_attempt_1.json",
    "P3/resolution_contract.json",
    "P3/gm_resolution_decision.json",
    "P3/decision_facing_answer_recipe.json",
    "P3/validation.json",
    "P3/digest.json",
    "P3/state_after.json",
    "P3/raw_generation_attempt_1.json",
    "P3/raw_generation_attempt_2.json",
]


def main() -> None:
    files = [ROOT / item for item in ROOT_FILES]
    files.extend(EVIDENCE / item for item in EVIDENCE_FILES)
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    manifest = []
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            data = path.read_bytes()
            if path.name == "CURRENT_REVIEW.md":
                arc = "CURRENT_REVIEW.md"
            else:
                arc = path.relative_to(ROOT).as_posix()
            archive.writestr(arc, data)
            manifest.append({"path": arc, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        body = {
            "review": "PR-BU qualified-inference complement authorization",
            "mode": "QUALIFIED-INFERENCE COMPLEMENT AUTHORIZATION",
            "model_api_calls": 0,
            "production_modified": True,
            "decision": "A - PR-BU DETERMINISTIC REPAIR COMPLETE; READY FOR MICRO LIVE",
            "c04": "fixed unauthorized_inference_complement",
            "control_a": "preserved",
            "open_debt": "cannot establish without be still returns before complement append",
            "architecture": "PR-BR REMAINS CLOSED",
            "pr_bt": "PAUSED",
            "retry": "UNCHANGED",
            "prompts_changed": False,
            "authority_changed": False,
            "p1_status": "fixed unauthorized_causal_relation",
            "p3_status": "fixed uncertain/unclear parity; motive still rejected",
            "matrix_cases": 41,
            "matrix_score": "41/41",
            "discovery_false_accepts": 9,
            "discovery_false_rejects": 5,
            "post_composition_false_accepts": 1,
            "post_composition_false_rejects": 0,
            "post_complement_false_accepts": 0,
            "post_complement_false_rejects": 0,
            "correct_accepts": 18,
            "correct_rejects": 23,
            "tests_passed": 313,
            "tests_failed_outside_repair": 1,
            "tests_xfailed": 0,
            "c18": "passed accepted == sealed == emitted",
            "micro_live": "ready; not run",
            "files": manifest,
        }
        encoded = json.dumps(body, indent=2).encode("utf-8")
        archive.writestr("REVIEW_MANIFEST.json", encoded)
    MANIFEST_PATH.write_bytes(encoded)
    print(f"wrote {ZIP_PATH} files={len(manifest) + 1} bytes={ZIP_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
