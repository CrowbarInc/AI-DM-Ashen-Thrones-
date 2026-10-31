"""Build handoff/CURRENT_REVIEW.zip for the PR-BT differential discovery. No model calls."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"

FILES = [
    "handoff/CURRENT_REVIEW.md",
    "PR-BT_selective_epistemic_guidance_differential_discovery.md",
    "PR-BT_epistemic_guidance_delta.json",
    "PR-BT_policy_instruction_semantic_diff.md",
    "artifacts/pr_bt_epistemic_guidance_differential/validator_recognizer_excerpt.md",
    "artifacts/pr_bt_epistemic_guidance_differential/forensic_validation.json",
    "artifacts/pr_bt_epistemic_guidance_differential/policy_narrative_authority.json",
    "artifacts/pr_bt_epistemic_guidance_differential/policy_uncertainty.json",
    "artifacts/pr_bt_epistemic_guidance_differential/P1_system_BS.txt",
    "artifacts/pr_bt_epistemic_guidance_differential/P1_system_BT.txt",
    "artifacts/pr_bt_epistemic_guidance_differential/P1_system_unified.diff",
    "artifacts/pr_bt_epistemic_guidance_differential/P1_instructions_BS.txt",
    "artifacts/pr_bt_epistemic_guidance_differential/P1_instructions_BT.txt",
    "artifacts/pr_bt_epistemic_guidance_differential/P1_decision_epistemic_slice.json",
    "artifacts/pr_bt_epistemic_guidance_differential/P3_decision_epistemic_slice.json",
]

PROBES = ("P1", "P2", "P3")
BS = "artifacts/pr_bs_cooperative_gm_micro_live/evidence"
BT = "artifacts/pr_bt_provider_deduplication_micro_live/evidence"
COMMON = (
    "digest.json",
    "raw_generation_attempt_1.json",
    "decision_facing_answer_recipe.json",
    "gm_resolution_decision.json",
    "resolution_contract.json",
    "provider_request_attempt_generation_1.json",
    "validation.json",
)
RETRY = (
    "raw_generation_attempt_2.json",
    "provider_request_attempt_generation_2.json",
)


def main():
    paths = list(FILES)
    for probe in PROBES:
        for name in COMMON:
            paths.append(f"{BS}/{probe}/{name}")
            paths.append(f"{BT}/{probe}/{name}")
        if probe in {"P1", "P3"}:
            for name in RETRY:
                paths.append(f"{BT}/{probe}/{name}")
    missing = [item for item in paths if not (ROOT / item).is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))

    manifest = []
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        # Zip-root names: CURRENT_REVIEW.md at top; other files keep repo-relative paths.
        for item in paths:
            source = ROOT / item
            arc = "CURRENT_REVIEW.md" if item == "handoff/CURRENT_REVIEW.md" else item
            data = source.read_bytes()
            archive.writestr(arc, data)
            manifest.append(
                {
                    "path": arc,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                }
            )
        manifest_bytes = json.dumps(
            {
                "review": "PR-BT selective epistemic guidance differential discovery",
                "mode": "DIFFERENTIAL DISCOVERY",
                "model_api_calls": 0,
                "decision": "C - BOTH GUIDANCE AND VALIDATOR NEED ATTENTION",
                "address_first": "selective epistemic linguistic protocol",
                "architecture": "A - PR-BR REMAINS CLOSED",
                "estimated_chars_restored": 651,
                "files": manifest,
            },
            indent=2,
        ).encode("utf-8")
        archive.writestr("REVIEW_MANIFEST.json", manifest_bytes)
    print(f"wrote {ZIP_PATH} files={len(manifest)+1} bytes={ZIP_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
