"""Refresh handoff/CURRENT_REVIEW.zip for PR-BV. No model calls."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"
MANIFEST_PATH = ROOT / "handoff" / "REVIEW_MANIFEST.json"

FILES = [
    "handoff/CURRENT_REVIEW.md",
    "PR-BV_first_pass_realization_competence_discovery.md",
    "PR-BV_realization_operation_analysis.json",
    "PR-BV_PR-BS_vs_current_behavioral_guidance_diff.md",
    "PR-BV_model_facing_operation_map.md",
    "artifacts/pr_bv_first_pass_realization_competence/extract_operation_signals.py",
    "artifacts/pr_bv_first_pass_realization_competence/measurements.json",
    "artifacts/pr_bv_first_pass_realization_competence/P1_removed_instructions.json",
    "artifacts/pr_bv_first_pass_realization_competence/P1_added_instructions.json",
    "artifacts/pr_bv_first_pass_realization_competence/P2_removed_instructions.json",
    "artifacts/pr_bv_first_pass_realization_competence/P2_added_instructions.json",
    "artifacts/pr_bv_first_pass_realization_competence/P1_system_current.txt",
    "artifacts/pr_bv_first_pass_realization_competence/P1_system_PR-BS.txt",
    "artifacts/pr_bv_first_pass_realization_competence/guidance_excerpts.txt",
]

EVIDENCE_NAMES = [
    "provider_request_attempt_generation_1.json",
    "raw_generation_attempt_1.json",
    "resolution_contract.json",
    "gm_resolution_decision.json",
    "decision_facing_answer_recipe.json",
    "validation.json",
]
RETRY_PROBES = ("P1", "P2")
GATES = {
    "current": "artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence",
    "pr_bs": "artifacts/pr_bs_cooperative_gm_micro_live/evidence",
}


def collect() -> list[Path]:
    paths = [ROOT / item for item in FILES]
    for probe in ("P1", "P2", "P3"):
        for name in EVIDENCE_NAMES:
            paths.append(ROOT / GATES["current"] / probe / name)
            paths.append(ROOT / GATES["pr_bs"] / probe / name)
        for probe_name in RETRY_PROBES:
            if probe != probe_name:
                continue
            paths.append(
                ROOT
                / GATES["current"]
                / probe
                / "provider_request_attempt_generation_2.json"
            )
            paths.append(ROOT / GATES["current"] / probe / "raw_generation_attempt_2.json")
    for probe in ("P1", "P2"):
        paths.append(
            ROOT
            / "artifacts/pr_bt_provider_deduplication_micro_live/evidence"
            / probe
            / "raw_generation_attempt_1.json"
        )
        paths.append(
            ROOT
            / "artifacts/pr_bt_selective_epistemic_restoration_final_micro_live/evidence"
            / probe
            / "raw_generation_attempt_1.json"
        )
    return paths


def main() -> None:
    paths = collect()
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    manifest = []
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            data = path.read_bytes()
            arc = "CURRENT_REVIEW.md" if path.name == "CURRENT_REVIEW.md" else path.relative_to(ROOT).as_posix()
            archive.writestr(arc, data)
            manifest.append({"path": arc, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        body = {
            "review": "PR-BV first-pass realization competence discovery",
            "mode": "FIRST-PASS REALIZATION COMPETENCE DISCOVERY",
            "model_api_calls": 0,
            "implementation": False,
            "pr_br": "CLOSED",
            "pr_bu": "CLOSED",
            "pr_bt": "PAUSED / BT-C",
            "decision": "A - COMPACT OPERATION-SELECTION PROJECTION RECOMMENDED",
            "p1_expected": "O3 bounded interpretation",
            "p1_chosen": "propose/gm_inference plus causal narration",
            "p1_primary": "F",
            "p2_expected": "O2 incidental dialogue",
            "p2_chosen": "realize/authored_world_fact/established",
            "p2_primary": "D",
            "p3": "success, discuss hypothesis without establishing it",
            "shared_cause": "strongly supported, two channels",
            "net_recipe_chars": {"P1": 127, "P2": 99, "P3": 106},
            "files": manifest,
        }
        encoded = json.dumps(body, indent=2).encode("utf-8")
        archive.writestr("REVIEW_MANIFEST.json", encoded)
        manifest.append(
            {"path": "REVIEW_MANIFEST.json", "sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)}
        )
    summary = {key: value for key, value in body.items() if key != "files"}
    MANIFEST_PATH.write_text(
        json.dumps({"files": manifest, "summary": summary}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes, {len(manifest)} entries)")


if __name__ == "__main__":
    main()
