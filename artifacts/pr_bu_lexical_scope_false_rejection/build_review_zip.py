"""Refresh handoff/CURRENT_REVIEW.zip for the lexical-scope repair. No model calls."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"
MANIFEST_PATH = ROOT / "handoff" / "REVIEW_MANIFEST.json"

FILES = [
    "handoff/CURRENT_REVIEW.md",
    "PR-BU_final_lexical_scope_false_rejection_repair.md",
    "PR-BU_lexical_scope_control_flow_after.md",
    "PR-BU_validator_semantic_matrix.json",
    "PR-BU_validator_semantic_matrix_lexical_scope_after.json",
    "tests/test_pr_bu_lexical_scope.py",
    "game/gm_resolution_decision.py",
    "artifacts/pr_bu_lexical_scope_false_rejection/regression_evidence.txt",
    "artifacts/pr_bu_lexical_scope_false_rejection/write_matrix_result.py",
    "artifacts/pr_bu_lexical_scope_false_rejection/dump_gates.py",
    "artifacts/pr_bu_lexical_scope_false_rejection/p1_retry_before_after.json",
    "artifacts/pr_bu_lexical_scope_false_rejection/preserved_gate_after.json",
    "artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/P1/validation.json",
    "artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/P2/validation.json",
    "artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/P3/validation.json",
]


def main() -> None:
    paths = [ROOT / item for item in FILES]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    manifest = []
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            data = path.read_bytes()
            arc = "CURRENT_REVIEW.md" if path.name == "CURRENT_REVIEW.md" else path.relative_to(ROOT).as_posix()
            archive.writestr(arc, data)
            manifest.append({"path": arc, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        body = {
            "review": "PR-BU final lexical-scope false-rejection repair",
            "mode": "FINAL LEXICAL-SCOPE FALSE-REJECTION REPAIR",
            "model_api_calls": 0,
            "pr_bu_decision": "A - PR-BU CLOSED",
            "pr_bt_decision": "PAUSED / BT-C",
            "pr_br": "CLOSED",
            "original_matrix": "41/41",
            "new_lexical_scope_controls": "24/24",
            "geography_controls": "11/11",
            "causal_scope_controls": "13/13",
            "p1_retry_before": "hard_valid false",
            "p1_retry_after": "hard_valid true",
            "p1_initial": "rejected",
            "p2_initial": "rejected",
            "p3_initial": "accepted",
            "broader_regression": "341 passed, 1 failed (pre-existing PR-BT prompt-size assertion)",
            "c18": "PASS",
            "prompts_changed": False,
            "retry_changed": False,
            "authority_changed": False,
            "files": manifest,
        }
        encoded = json.dumps(body, indent=2).encode("utf-8")
        archive.writestr("REVIEW_MANIFEST.json", encoded)
        manifest.append({"path": "REVIEW_MANIFEST.json", "sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)})
    MANIFEST_PATH.write_text(json.dumps({"files": manifest, "summary": {k: body[k] for k in body if k != "files"}}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes, {len(manifest)} entries)")


if __name__ == "__main__":
    main()
